# Replay Diagnostics and Regression Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested replay-tracing layer and turn the simulator's confirmed 18-level clean prefix into an automated regression gate without changing game mechanics.

**Architecture:** A new dependency-free `ssr_env.diagnostics` module snapshots dynamic entities, computes immutable step deltas, and serializes traces to JSON-safe primitives. `tools/level_audit.py` remains the corpus runner and CLI; it supplies segment indices, retains bounded failure context, and formats human or JSON output. Integration tests exercise the real continuous `all.dem` replay so confirmed progress cannot silently regress.

**Tech Stack:** Python 3.12, frozen dataclasses, stdlib `argparse`/`collections`/`json`, `uv`, pytest 8.

## Global Constraints

- Do not modify movement, turning, pushing, cooking, gravity, or transition behavior.
- Diagnostics must not mutate either the pre-step or post-step `GameState`.
- Keep the existing `uv run python tools/level_audit.py` invocation valid.
- `--trace none` is the default.
- User-facing move numbers are one-based; `input_index` remains zero-based for indexing parsed inputs.
- JSON must contain only dictionaries, lists, strings, integers, booleans, and nulls.
- `failures` mode retains at most five preceding change events plus the failure event.
- A segment following forced resynchronization is not treated as confirmed.
- Existing 120 standalone replay cases remain `xfail`.

## File Structure

- Create `src/ssr_env/diagnostics.py`: immutable diagnostic types, state snapshots, delta calculation, event creation, primitive serialization.
- Create `tests/test_diagnostics.py`: focused tests for snapshots, deltas, event emission, spawn/removal, and serialization.
- Modify `tools/level_audit.py`: trace modes, exact failure indices, bounded context, CLI filtering, human formatting, JSON conversion.
- Create `tests/test_level_audit.py`: audit bookkeeping, CLI-compatible serialization, filtering, and the 18-level integration gate.
- Modify `README.md`: replace the placeholder with the exact commands for running tests and replay diagnostics.

---

### Task 1: Dynamic entity snapshots and deltas

**Files:**
- Create: `src/ssr_env/diagnostics.py`
- Create: `tests/test_diagnostics.py`

**Interfaces:**
- Consumes: `ssr_env.state.GameState`, `ssr_env.entity.Entity`, and enums from `ssr_env.types`.
- Produces:
  - `EntitySnapshot.from_entity(entity: Entity) -> EntitySnapshot`
  - `snapshot_dynamic(state: GameState) -> dict[int, EntitySnapshot]`
  - `entity_deltas(before: GameState, after: GameState) -> tuple[EntityDelta, ...]`
  - `EntitySnapshot.to_dict() -> dict[str, object]`
  - `EntityDelta.to_dict() -> dict[str, object]`

- [ ] **Step 1: Write failing snapshot and delta tests**

Create `tests/test_diagnostics.py`:

```python
from dataclasses import replace

from ssr_env.diagnostics import EntitySnapshot, entity_deltas, snapshot_dynamic
from ssr_env.entity import Entity, pack_cookdata
from ssr_env.state import GameState
from ssr_env.types import Coord, Direction, EntType


def dynamic_state(*entities: Entity) -> GameState:
    return GameState(entities=entities)


def player(ident: int = 1) -> Entity:
    return Entity(
        pos=Coord(2, 3, 1),
        type=EntType.PLAYER,
        id=ident,
        direction=Direction.NORTH,
    )


def sausage(ident: int = 2) -> Entity:
    return Entity(
        pos=Coord(4, 5, 1),
        type=EntType.SAUSAGE,
        id=ident,
        direction=Direction.EAST,
        cookdata=pack_cookdata((0, 1, 2, 3)),
        rot=1,
        dat="M;grill-a;",
    )


def test_snapshot_contains_stable_dynamic_state():
    snapshot = EntitySnapshot.from_entity(sausage())
    assert snapshot.to_dict() == {
        "id": 2,
        "type": "SAUSAGE",
        "pos": [4, 5, 1],
        "direction": "EAST",
        "rot": 1,
        "faces": [0, 1, 2, 3],
        "stuckto": -1,
        "status": "M",
    }


def test_snapshot_dynamic_excludes_static_entities():
    ground = Entity(pos=Coord(0, 0, 0), type=EntType.GROUND, id=9)
    snapshots = snapshot_dynamic(dynamic_state(player(), sausage(), ground))
    assert set(snapshots) == {1, 2}


def test_unchanged_entities_do_not_produce_deltas():
    state = dynamic_state(player(), sausage())
    assert entity_deltas(state, state) == ()


def test_entity_delta_reports_before_and_after():
    before = dynamic_state(player(), sausage())
    moved = replace(
        sausage(),
        pos=Coord(5, 5, 1),
        direction=Direction.SOUTH,
        rot=0,
        stuckto=1,
    )
    after = dynamic_state(player(), moved)
    deltas = entity_deltas(before, after)
    assert len(deltas) == 1
    assert deltas[0].entity_id == 2
    assert deltas[0].before.pos == Coord(4, 5, 1)
    assert deltas[0].after.pos == Coord(5, 5, 1)


def test_spawn_and_removal_use_none_for_the_absent_side():
    before = dynamic_state(player())
    after = dynamic_state(sausage())
    deltas = entity_deltas(before, after)
    by_id = {delta.entity_id: delta for delta in deltas}
    assert by_id[1].before is not None and by_id[1].after is None
    assert by_id[2].before is None and by_id[2].after is not None


def test_delta_calculation_does_not_mutate_either_state():
    before = dynamic_state(player(), sausage())
    after = dynamic_state(player(), replace(sausage(), pos=Coord(5, 5, 1)))
    expected_before = before
    expected_after = after
    entity_deltas(before, after)
    assert before == expected_before
    assert after == expected_after
```

- [ ] **Step 2: Run the tests and verify the import failure**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_diagnostics.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'ssr_env.diagnostics'`.

- [ ] **Step 3: Implement immutable snapshots and deltas**

Create `src/ssr_env/diagnostics.py`:

```python
"""Read-only replay diagnostics for settled simulator states."""

from dataclasses import dataclass

from .entity import Entity
from .state import GameState
from .types import Coord, Direction, EntType, Input


@dataclass(frozen=True, slots=True)
class EntitySnapshot:
    id: int
    type: EntType
    pos: Coord
    direction: Direction
    rot: int
    faces: tuple[int, int, int, int]
    stuckto: int
    status: str

    @classmethod
    def from_entity(cls, entity: Entity) -> "EntitySnapshot":
        return cls(
            id=entity.id,
            type=entity.type,
            pos=entity.pos,
            direction=entity.direction,
            rot=entity.rot,
            faces=entity.faces,
            stuckto=entity.stuckto,
            status=entity.dat[:1],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type.name,
            "pos": [self.pos.x, self.pos.y, self.pos.z],
            "direction": self.direction.name,
            "rot": self.rot,
            "faces": list(self.faces),
            "stuckto": self.stuckto,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class EntityDelta:
    entity_id: int
    before: EntitySnapshot | None
    after: EntitySnapshot | None

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_id": self.entity_id,
            "before": self.before.to_dict() if self.before is not None else None,
            "after": self.after.to_dict() if self.after is not None else None,
        }


def snapshot_dynamic(state: GameState) -> dict[int, EntitySnapshot]:
    return {
        entity.id: EntitySnapshot.from_entity(entity)
        for entity in state.entities
        if entity.type in (EntType.PLAYER, EntType.SAUSAGE)
    }


def entity_deltas(before: GameState, after: GameState) -> tuple[EntityDelta, ...]:
    old = snapshot_dynamic(before)
    new = snapshot_dynamic(after)
    return tuple(
        EntityDelta(entity_id, old.get(entity_id), new.get(entity_id))
        for entity_id in sorted(old.keys() | new.keys())
        if old.get(entity_id) != new.get(entity_id)
    )
```

- [ ] **Step 4: Run the focused tests**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_diagnostics.py -q
```

Expected: `6 passed`.

- [ ] **Step 5: Run the existing unit suite**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

Expected: all previously passing tests remain green; the 120 replay cases remain xfailed.

- [ ] **Step 6: Commit the snapshot layer**

```bash
git add src/ssr_env/diagnostics.py tests/test_diagnostics.py
git commit -m "feat: add immutable replay state deltas"
```

---

### Task 2: Step trace events and primitive serialization

**Files:**
- Modify: `src/ssr_env/diagnostics.py`
- Modify: `tests/test_diagnostics.py`

**Interfaces:**
- Consumes: `entity_deltas(before, after)` from Task 1.
- Produces:
  - `StepTrace`
  - `trace_step(before, after, *, input_index, segment, segment_index, action, moved, reason) -> StepTrace | None`
  - `StepTrace.to_dict() -> dict[str, object]`

- [ ] **Step 1: Write failing event tests**

Append to `tests/test_diagnostics.py`:

```python
from ssr_env.diagnostics import trace_step


def test_trace_step_omits_an_unchanged_accepted_step():
    state = dynamic_state(player(), sausage())
    assert trace_step(
        state,
        state,
        input_index=9,
        segment="1-1",
        segment_index=4,
        action=Direction.NORTH,
        moved=True,
        reason=None,
    ) is None


def test_trace_step_keeps_a_refusal_without_entity_changes():
    state = dynamic_state(player(), sausage())
    trace = trace_step(
        state,
        state,
        input_index=9,
        segment="1-1",
        segment_index=4,
        action=Direction.NORTH,
        moved=False,
        reason="blocked",
    )
    assert trace is not None
    assert trace.global_move == 10
    assert trace.segment_move == 5
    assert trace.reason == "blocked"


def test_trace_step_serializes_level_entry_and_loss():
    before = dynamic_state(player(), sausage())
    after = replace(
        dynamic_state(player(), replace(sausage(), dat="B;grill-a;")),
        pushtargetlevel="levelb11",
        lost_reason="Burned",
    )
    trace = trace_step(
        before,
        after,
        input_index=1240,
        segment="2-3",
        segment_index=36,
        action=Direction.NORTH,
        moved=True,
        reason="Burned",
    )
    assert trace.to_dict()["input"] == "NORTH"
    assert trace.to_dict()["level_after"] == "levelb11"
    assert trace.to_dict()["loss"] == "Burned"


def test_trace_step_names_a_completed_level():
    before = replace(
        dynamic_state(player(), sausage()),
        overworld=False,
        pushtargetlevel="level47",
    )
    after = replace(
        dynamic_state(player()),
        completed=frozenset({"level47"}),
    )
    trace = trace_step(
        before,
        after,
        input_index=82,
        segment="1-1",
        segment_index=67,
        action=Direction.SOUTH,
        moved=True,
        reason=None,
    )
    assert trace.to_dict()["completed_level"] == "level47"
```

- [ ] **Step 2: Run the new tests and verify the symbol failure**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_diagnostics.py -q
```

Expected: collection fails because `trace_step` is not defined.

- [ ] **Step 3: Implement trace events**

Add to `src/ssr_env/diagnostics.py`:

```python
@dataclass(frozen=True, slots=True)
class StepTrace:
    input_index: int
    global_move: int
    segment: str
    segment_index: int
    segment_move: int
    input: Input
    moved: bool
    reason: str | None
    level_before: str
    level_after: str
    completed_level: str | None
    loss: str
    changes: tuple[EntityDelta, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "input_index": self.input_index,
            "global_move": self.global_move,
            "segment": self.segment,
            "segment_index": self.segment_index,
            "segment_move": self.segment_move,
            "input": self.input.name,
            "moved": self.moved,
            "reason": self.reason,
            "level_before": self.level_before or None,
            "level_after": self.level_after or None,
            "completed_level": self.completed_level,
            "loss": self.loss or None,
            "changes": [change.to_dict() for change in self.changes],
        }


def trace_step(
    before: GameState,
    after: GameState,
    *,
    input_index: int,
    segment: str,
    segment_index: int,
    action: Input,
    moved: bool,
    reason: str | None,
) -> StepTrace | None:
    changes = entity_deltas(before, after)
    if (
        not changes
        and moved
        and not reason
        and before.pushtargetlevel == after.pushtargetlevel
        and not after.lost_reason
    ):
        return None
    return StepTrace(
        input_index=input_index,
        global_move=input_index + 1,
        segment=segment,
        segment_index=segment_index,
        segment_move=segment_index + 1,
        input=action,
        moved=moved,
        reason=reason,
        level_before=before.pushtargetlevel,
        level_after=after.pushtargetlevel,
        completed_level=(
            before.pushtargetlevel
            if (
                before.pushtargetlevel
                and not after.pushtargetlevel
                and before.pushtargetlevel in after.completed
            )
            else None
        ),
        loss=after.lost_reason,
        changes=changes,
    )
```

Add `Input` to the existing import from `.types`.

- [ ] **Step 4: Run focused and full tests**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_diagnostics.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

Expected: diagnostics tests pass; the existing suite remains green with 120 xfails.

- [ ] **Step 5: Commit trace events**

```bash
git add src/ssr_env/diagnostics.py tests/test_diagnostics.py
git commit -m "feat: describe replay steps as serializable traces"
```

---

### Task 3: Exact audit failure locations and bounded trace retention

**Files:**
- Modify: `tools/level_audit.py`
- Create: `tests/test_level_audit.py`

**Interfaces:**
- Consumes: `trace_step(...) -> StepTrace | None` from Task 2.
- Produces:
  - `audit(limit: int | None = None, trace_mode: str = "none", segment_filter: str | None = None) -> list[Segment]`
  - `Segment.lost_at: int | None`
  - `Segment.failure_at: int | None`
  - `Segment.events: list[StepTrace]`
  - `segment_to_dict(segment: Segment) -> dict[str, object]`

- [ ] **Step 1: Write failing audit bookkeeping tests**

Create `tests/test_level_audit.py`:

```python
import json

from tools.level_audit import audit, segment_to_dict


def test_first_levelb11_loss_has_an_exact_location():
    segments = audit(limit=21, trace_mode="failures")
    failing = next(segment for segment in segments if segment.level == "levelb11")
    assert failing.lost
    assert failing.lost_at is not None
    assert failing.failure_at == failing.lost_at
    assert failing.events[-1].global_move == failing.lost_at
    assert failing.events[-1].loss


def test_failure_trace_retains_at_most_five_preceding_events():
    segments = audit(limit=21, trace_mode="failures")
    failing = next(segment for segment in segments if segment.level == "levelb11")
    assert 1 <= len(failing.events) <= 6
    assert failing.events == sorted(
        failing.events, key=lambda event: event.input_index
    )


def test_segment_json_uses_only_json_primitives():
    segments = audit(limit=21, trace_mode="failures")
    failing = next(segment for segment in segments if segment.level == "levelb11")
    encoded = json.dumps(segment_to_dict(failing))
    decoded = json.loads(encoded)
    assert decoded["level"] == "levelb11"
    assert decoded["lost_at"] == failing.lost_at
```

- [ ] **Step 2: Run the tests and verify the signature failure**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_level_audit.py -q
```

Expected: collection or call failure because `segment_to_dict`, `trace_mode`, and the new fields do not exist.

- [ ] **Step 3: Add audit fields and trace configuration**

In `tools/level_audit.py`:

```python
from collections import deque
from typing import Literal

from ssr_env.diagnostics import StepTrace, trace_step

TraceMode = Literal["none", "failures", "changes"]
FAILURE_CONTEXT = 5
```

Extend `Segment`:

```python
    lost_at: int | None = None
    failure_at: int | None = None
    events: list[StepTrace] = field(default_factory=list)
```

Change the dataclass import to `from dataclasses import dataclass, field, replace`.

Change the audit signature:

```python
def audit(
    limit: int | None = None,
    trace_mode: TraceMode = "none",
    segment_filter: str | None = None,
) -> list[Segment]:
```

At the start of each segment, create:

```python
        recent: deque[StepTrace] = deque(maxlen=FAILURE_CONTEXT)
```

After each successful `step()` call and before rebinding `state`, create the event:

```python
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
```

Record exceptions with one-based move numbers:

```python
                seg.failure_at = k + 1
```

Record only the first loss:

```python
            if state.lost_reason and seg.lost_at is None:
                seg.lost = state.lost_reason
                seg.lost_at = k + 1
                seg.failure_at = k + 1
```

Remove the old unconditional assignment that overwrites `seg.lost` on every later input.

- [ ] **Step 4: Add primitive segment serialization**

Add:

```python
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
```

Replace the JSON write with:

```python
args.json.write_text(
    json.dumps([segment_to_dict(segment) for segment in segs], indent=2)
)
```

- [ ] **Step 5: Run focused and full tests**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_level_audit.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

Expected: audit bookkeeping tests pass; existing tests remain green.

- [ ] **Step 6: Commit audit tracing**

```bash
git add tools/level_audit.py tests/test_level_audit.py
git commit -m "feat: retain exact replay failure context"
```

---

### Task 4: CLI trace modes, filtering, and human-readable output

**Files:**
- Modify: `tools/level_audit.py`
- Modify: `tests/test_level_audit.py`

**Interfaces:**
- Consumes: `Segment.events` and `StepTrace.to_dict()` from Tasks 2-3.
- Produces:
  - `format_event(event: StepTrace) -> str`
  - CLI options `--trace`, `--segment`, and existing `--json`.

- [ ] **Step 1: Write failing formatting and filtering tests**

Append to `tests/test_level_audit.py`:

```python
from tools.level_audit import format_event


def test_segment_filter_does_not_skip_prior_replay_state():
    unfiltered = audit(limit=21, trace_mode="failures")
    filtered = audit(limit=21, trace_mode="failures", segment_filter="2-3")
    expected = next(segment for segment in unfiltered if segment.name == "2-3")
    actual = next(segment for segment in filtered if segment.name == "2-3")
    assert actual.level == expected.level == "levelb11"
    assert actual.lost_at == expected.lost_at
    assert all(
        not segment.events
        for segment in filtered
        if segment.name != "2-3"
    )


def test_human_trace_includes_both_move_numbering_systems():
    segments = audit(limit=21, trace_mode="failures", segment_filter="2-3")
    failing = next(segment for segment in segments if segment.name == "2-3")
    rendered = format_event(failing.events[-1])
    assert f"global {failing.events[-1].global_move}" in rendered
    assert f"2-3:{failing.events[-1].segment_move}" in rendered
    assert failing.events[-1].input.name in rendered
```

- [ ] **Step 2: Run the focused tests and verify the missing formatter**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_level_audit.py -q
```

Expected: collection fails because `format_event` is not defined.

- [ ] **Step 3: Implement concise event formatting**

Add:

```python
def format_event(event: StepTrace) -> str:
    labels: list[str] = []
    if not event.moved:
        labels.append("refused")
    if event.reason:
        labels.append(event.reason)
    if event.level_before != event.level_after:
        labels.append(
            f"level {event.level_before or '-'} -> {event.level_after or '-'}"
        )
    if event.loss:
        labels.append(f"loss={event.loss}")
    summary = "; ".join(labels) if labels else "changed"
    changed = ", ".join(str(delta.entity_id) for delta in event.changes) or "-"
    return (
        f"global {event.global_move} "
        f"{event.segment}:{event.segment_move} "
        f"{event.input.name}: {summary}; entities={changed}"
    )
```

- [ ] **Step 4: Add CLI arguments and table failure column**

Add arguments:

```python
    ap.add_argument(
        "--trace",
        choices=("none", "failures", "changes"),
        default="none",
    )
    ap.add_argument("--segment", default=None)
```

Call:

```python
    segs = audit(args.limit, args.trace, args.segment)
```

Change the table header to include `at`, and print `failure_at` as a one-based move.
After the summary, print retained events for matching segments:

```python
    for segment in segs:
        if not segment.events:
            continue
        print(f"\ntrace {segment.name}:")
        for event in segment.events:
            print("  " + format_event(event))
```

- [ ] **Step 5: Verify CLI output and JSON**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py --limit 21 --trace failures --segment 2-3
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py --limit 21 --trace failures --segment 2-3 --json /tmp/ssr-level-audit.json
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m json.tool /tmp/ssr-level-audit.json
```

Expected:

- the audit table names `levelb11` as the first failing level;
- the `at` column contains the exact loss move;
- the trace shows at most six events and ends at that move;
- `json.tool` exits successfully.

- [ ] **Step 6: Run all tests and commit**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

Then:

```bash
git add tools/level_audit.py tests/test_level_audit.py
git commit -m "feat: expose replay traces through the audit CLI"
```

---

### Task 5: Confirmed-prefix acceptance gate and operator documentation

**Files:**
- Modify: `tests/test_level_audit.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `audit(limit=21)` from Task 3.
- Produces: a regression gate for the first 18 solved levels and documented operator commands.

- [ ] **Step 1: Write the confirmed-prefix acceptance test**

Append to `tests/test_level_audit.py`:

```python
def test_continuous_replay_preserves_the_confirmed_eighteen_level_prefix():
    segments = audit(limit=21)
    under_test = [segment for segment in segments if segment.under_test]
    solved = [segment for segment in under_test if segment.status == "ok"]
    assert [(segment.name, segment.level) for segment in solved] == [
        ("1-1", "level47"),
        ("1-2", "level56"),
        ("1-3", "level49"),
        ("1-4", "level23"),
        ("1-5", "generated1"),
        ("1-6", "level28"),
        ("1-7", "level26"),
        ("1-8", "level16"),
        ("1-9", "level11"),
        ("1-10", "level24"),
        ("1-11", "level46"),
        ("1-12", "level27"),
        ("1-13", "level4"),
        ("1-14", "level9b8"),
        ("1-15", "level41"),
        ("1-16", "level35"),
        ("2-1", "improv3"),
        ("2-2", "levelb4b"),
    ]
    assert all(not segment.resynced_before for segment in solved)
    frontier = under_test[len(solved)]
    assert frontier.name == "2-3"
    assert frontier.level == "levelb11"
    assert not frontier.resynced_before
```

- [ ] **Step 2: Prove the gate detects a regression**

Temporarily change the first expected pair to `("1-1", "wrong-level")`, then run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_level_audit.py::test_continuous_replay_preserves_the_confirmed_eighteen_level_prefix -q
```

Expected: failure showing `level47 != wrong-level`.

Restore `("1-1", "level47")`.

- [ ] **Step 3: Run the real acceptance gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_level_audit.py::test_continuous_replay_preserves_the_confirmed_eighteen_level_prefix -q
```

Expected: `1 passed`.

- [ ] **Step 4: Replace the README placeholder**

Replace `README.md` with:

````markdown
# Qwen Plays Stephen's Sausage Roll

Pure-Python reference simulator and replay tooling for research on learned
heuristics in open-weights models trained to solve Stephen's Sausage Roll.

## Test

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

The standalone official replay cases remain xfailed until their independent
initial-state mappings are validated. The continuous replay regression test
protects the confirmed clean prefix.

## Audit the official continuous replay

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py
```

Trace the first failing segment with bounded context:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py \
  --limit 21 --trace failures --segment 2-3
```

Add `--json PATH` for machine-readable output. Move numbers shown to users are
one-based; JSON also includes the zero-based `input_index`.
````

- [ ] **Step 5: Run final verification**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py --limit 21 --trace failures --segment 2-3
git diff --check
git status --short
```

Expected:

- all unit and integration tests pass;
- 120 standalone replays remain xfailed;
- the audit reports 18 clean solved levels followed by `levelb11`;
- no whitespace errors;
- only planned files are modified.

- [ ] **Step 6: Commit the acceptance gate and documentation**

```bash
git add tests/test_level_audit.py README.md
git commit -m "test: protect the confirmed replay frontier"
```

---

## Completion review

Before claiming the milestone complete:

1. Run `git diff HEAD~5 -- src/ssr_env/mechanics.py` and verify there are no mechanics changes.
2. Run the full verification commands from Task 5.
3. Inspect the final `levelb11` event and confirm its global move, segment-relative move, input, loss reason, and sausage deltas are present in both CLI and JSON output.
4. Record the new test count and exact first-loss location in the handoff.
