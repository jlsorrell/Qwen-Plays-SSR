"""Per-level audit of the .dem corpus.

The replay harness is a single serial chain: 120 segments of `all.dem` played
end to end. That makes it a poor diagnostic, because the first level this
simulator gets wrong hides every level after it. Emerson Jetty alone masked 102
segments until it was fixed.

This tool breaks the chain. It replays normally, but at each segment boundary it
checks whether that segment's level was completed and, if it was not, **forces a
resynchronisation** — marks the level complete, restores the overworld, and puts
the player at the level's own pose — so the next segment starts from a sane
state and can be judged on its own.

The result is a table of which levels this simulator solves and which it does
not, in one run.

**A resynced segment is not a pass.** Forcing the state discards whatever the
demo actually did, so every segment after a forced one is only as trustworthy as
the resync. Segments are reported with `resynced_before` for exactly this
reason: a failure immediately after a forced resync may be an artefact, whereas
a failure with a clean run-up is real. Treat the first failure in each
contiguous clean stretch as the signal.

**Known limitation: the decoupling is partial.** The resync restores the level
and the overworld, but it cannot restore the player to where the demo believes
it is standing. A segment ends by *walking into* the next level, so those moves
are a route from one entrance to the next; start them from the wrong tile and
the player wanders and never arrives. In practice only a handful of segments
past the first failure still reach a level.

Fixing that needs level identity per segment to be derived independently of the
chain — for instance by trying each candidate level's entry state and keeping
whichever one the segment actually solves. Until then this tool measures the
clean prefix precisely and tells you nothing reliable after the first break.
Its value is that it makes the prefix, and the effect of any fix on it, a single
number instead of a manual trace.

Usage:  uv run python tools/level_audit.py [--limit N] [--json out.json]
"""

import argparse
import json
from collections import deque
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from ssr_env.dem import parse_dem_file
from ssr_env.diagnostics import StepTrace, trace_step
from ssr_env.level import load_island_masks, load_overworld, load_overworld_meta
from ssr_env.mechanics import (
    UnimplementedMechanic,
    level_pose,
    raise_other_islands,
    step,
)
from ssr_env.state import with_entities
from ssr_env.types import EntType

DEM_DIR = Path("data/dem")
TraceMode = Literal["none", "failures", "changes"]
FAILURE_CONTEXT = 5


def segment_order() -> list[str]:
    """Segment names in play order.

    Not the order `sorted()` gives. Each world runs `w-0`, then `w-1`..`w-N`
    numerically, then `w-final`; lexicographic sorting puts `1-10` before `1-2`
    and drops `1-0`/`1-final` out of place, which is how sixteen levels were
    once mistaken for the whole of world 1.
    """
    names: list[str] = []
    for world in range(1, 10):
        candidates = [f"{world}-0"] + [f"{world}-{i}" for i in range(1, 100)]
        candidates.append(f"{world}-final")
        names += [n for n in candidates if (DEM_DIR / f"{n}.dem").exists()]
    return names


@dataclass
class Segment:
    name: str
    start: int
    end: int  # inclusive
    level: str | None = None
    entered_at: int | None = None
    completed_at: int | None = None
    lost: str = ""
    lost_at: int | None = None
    failure_at: int | None = None
    events: list[StepTrace] = field(default_factory=list)
    error: str = ""
    resynced_before: bool = False
    #: True when the level was already active as the segment opened — only then
    #: is the segment responsible for solving it.
    under_test: bool = False

    @property
    def status(self) -> str:
        if self.error:
            return "ERROR"
        if self.level is None:
            return "no-level"  # overworld-only segment, e.g. w-0 and w-final
        if not self.under_test:
            # The segment ends by walking into this level; the next one solves it.
            return "entered"
        if self.completed_at is not None:
            return "ok"
        if self.lost:
            return f"lost:{self.lost}"
        return "unsolved"


def segments() -> list[Segment]:
    out: list[Segment] = []
    cursor = 0
    for name in segment_order():
        length = len(parse_dem_file(DEM_DIR / f"{name}.dem"))
        out.append(Segment(name=name, start=cursor, end=cursor + length - 1))
        cursor += length
    return out


def resync(state, level: str, meta, masks):
    """Force the state to 'level solved, back on the overworld'.

    Deliberately crude. It exists so one bad level does not hide the next
    hundred, not to be faithful — anything downstream of it is suspect.
    """
    kept = tuple(
        e
        for e in state.entities
        if e.type is not EntType.SAUSAGE or e.dat.startswith("S")
    )
    restored = with_entities(
        state,
        kept,
        overworld=True,
        pushtargetlevel="",
        completed=state.completed | {level},
        lost_reason="",
        exit_pos=None,
        exit_dir=None,
        exit_up=True,
        exit_attachment=None,
    )
    if state.pushtargetlevel:
        restored = raise_other_islands(restored, level, masks=masks)
    pose = level_pose(restored, level, meta)
    if pose is not None:
        pos, direction = pose
        player = restored.player
        restored = restored.replace_entity(
            replace(player, pos=pos, direction=direction, stuckto=-1)
        )
    return restored


def audit(
    limit: int | None = None,
    trace_mode: TraceMode = "none",
    segment_filter: str | None = None,
) -> list[Segment]:
    masks = load_island_masks()
    meta = load_overworld_meta()
    state = load_overworld()
    inputs = parse_dem_file(DEM_DIR / "all.dem")

    segs = segments()
    if limit:
        segs = segs[:limit]
    history: list = []
    forced_previous = False

    for seg in segs:
        recent: deque[StepTrace] = deque(maxlen=FAILURE_CONTEXT)
        seg.resynced_before = forced_previous
        # Segment boundaries fall at level *entry*, not exit: a segment ends by
        # walking into the next level, which is then solved during the segment
        # that follows. So the level under test is whichever one is already
        # active when the segment opens.
        under_test = state.pushtargetlevel or None
        seg.level = under_test
        seg.under_test = under_test is not None
        for k in range(seg.start, min(seg.end + 1, len(inputs))):
            try:
                result = step(state, inputs[k], history, masks, "", meta)
            except UnimplementedMechanic as exc:
                seg.error = f"unimplemented: {exc}"
                seg.failure_at = k + 1
                break
            except Exception as exc:  # noqa: BLE001 - the audit must not stop
                seg.error = f"{type(exc).__name__}: {exc}"
                seg.failure_at = k + 1
                break
            event = trace_step(
                state,
                result.state,
                input_index=k,
                segment=seg.name,
                segment_index=k - seg.start,
                action=inputs[k],
                moved=result.moved,
                reason=result.reason,
            )
            keep_trace = segment_filter is None or segment_filter == seg.name
            first_loss = bool(result.state.lost_reason) and seg.lost_at is None
            if event is not None and keep_trace:
                if trace_mode == "changes":
                    seg.events.append(event)
                elif trace_mode == "failures" and first_loss:
                    seg.events = [*recent, event]
                elif trace_mode == "failures":
                    recent.append(event)
            before_level = state.pushtargetlevel
            state = result.state
            if state.pushtargetlevel and seg.entered_at is None:
                seg.entered_at = k
                if seg.level is None:
                    seg.level = state.pushtargetlevel
            if before_level == under_test and not state.pushtargetlevel:
                seg.completed_at = k
            if state.lost_reason and seg.lost_at is None:
                seg.lost = state.lost_reason
                seg.lost_at = k + 1
                seg.failure_at = k + 1

        # Only force a resync for a level that was under test and did not
        # finish. A segment that merely walks into the next level is fine.
        if (
            under_test is not None
            and seg.completed_at is None
            and state.pushtargetlevel == under_test
        ):
            state = resync(state, seg.level, meta, masks)
            history.clear()
            forced_previous = True
        else:
            forced_previous = False
    return segs


def segment_to_dict(segment: Segment) -> dict[str, object]:
    return {
        "name": segment.name,
        "start": segment.start,
        "end": segment.end,
        "level": segment.level,
        "entered_at": segment.entered_at,
        "completed_at": segment.completed_at,
        "lost": segment.lost or None,
        "lost_at": segment.lost_at,
        "failure_at": segment.failure_at,
        "error": segment.error or None,
        "resynced_before": segment.resynced_before,
        "under_test": segment.under_test,
        "status": segment.status,
        "events": [event.to_dict() for event in segment.events],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    segs = audit(args.limit)
    with_level = [s for s in segs if s.under_test]
    ok = [s for s in with_level if s.status == "ok"]
    clean = [s for s in with_level if not s.resynced_before]
    clean_ok = [s for s in clean if s.status == "ok"]

    print(f"{'segment':<10} {'level':<16} {'status':<16} {'entered':>8} {'done':>8}  run-up")
    for s in with_level:
        print(
            f"{s.name:<10} {(s.level or ''):<16} {s.status:<16} "
            f"{s.entered_at if s.entered_at is not None else '':>8} "
            f"{s.completed_at if s.completed_at is not None else '':>8}"
            f"  {'after-resync' if s.resynced_before else 'clean'}"
        )

    print(f"\nsegments carrying a level: {len(with_level)}")
    print(f"  solved:                  {len(ok)}")
    print(f"  solved with a clean run-up: {len(clean_ok)}/{len(clean)}")
    reasons: dict[str, int] = {}
    for s in with_level:
        if s.status != "ok":
            reasons[s.status.split(":")[0]] = reasons.get(s.status.split(":")[0], 0) + 1
    if reasons:
        print("  failure kinds:", ", ".join(f"{k}={v}" for k, v in sorted(reasons.items())))

    if args.json:
        args.json.write_text(
            json.dumps([segment_to_dict(segment) for segment in segs], indent=2)
        )
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
