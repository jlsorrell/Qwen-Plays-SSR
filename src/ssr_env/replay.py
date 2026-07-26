"""Replay a .dem input sequence and localise the first divergence.

Two jobs. During Tasks 9-13 this is the debugging instrument: it reports the
exact move index at which the simulator's behaviour stops matching a known-good
solution, and renders the state there.

It is also how the `.dem`-to-level-name mapping gets discovered. The game's
internal level names (`islandshape21e`, `leveltest7`) bear no relation to
SSRDecompile's `1-1` ... `6-28`, and no mapping exists in the game data. But a
correct solution only wins on its own level, so running a `.dem` against every
candidate and keeping the one that solves recovers the pairing — self-validating
in the same way the merged_binary parse was.
"""

from dataclasses import dataclass
from pathlib import Path

from .dem import parse_dem_file
from .level import load_island_masks, load_level_by_name, playable_levels
from .mechanics import StepResult, UnimplementedMechanic, is_solved, step
from .render import render
from .state import GameState
from .types import Input


@dataclass(frozen=True)
class ReplayReport:
    level: str
    solved: bool
    moves_applied: int
    total_moves: int
    failure_index: int | None
    failure_reason: str | None
    final_render: str

    def summary(self) -> str:
        if self.solved:
            return f"{self.level}: SOLVED in {self.moves_applied} moves"
        return (
            f"{self.level}: DIVERGED at move {self.failure_index}"
            f"/{self.total_moves} — {self.failure_reason}\n\n{self.final_render}"
        )


def replay(
    state: GameState, inputs: list[Input], name: str = "", masks=None
) -> ReplayReport:
    if masks is None:
        masks = load_island_masks()
    history: list[GameState] = []
    for i, action in enumerate(inputs):
        try:
            result: StepResult = step(state, action, history, masks, name)
        except UnimplementedMechanic as exc:
            return ReplayReport(
                name, False, i, len(inputs), i,
                f"unimplemented mechanic: {exc}", render(state, name),
            )
        if result.lost:
            return ReplayReport(
                name, False, i, len(inputs), i, result.reason, render(result.state, name)
            )
        state = result.state
    try:
        solved = step(state, None, history).solved
    except UnimplementedMechanic:
        solved = False
    return ReplayReport(
        name,
        solved,
        len(inputs),
        len(inputs),
        None if solved else len(inputs),
        None if solved else "sequence exhausted without reaching goal",
        render(state, name),
    )


def replay_dem(level_name: str, dem_path: Path) -> ReplayReport:
    return replay(load_level_by_name(level_name), parse_dem_file(dem_path), level_name)


def find_matching_level(dem_path: Path, candidates: list[str] | None = None) -> list[str]:
    """Return every candidate level this .dem solves.

    Expected to return exactly one name once the mechanics are correct. Zero
    means the simulator is wrong or the level is absent; more than one would mean
    two levels are genuinely interchangeable under this solution.
    """
    inputs = parse_dem_file(dem_path)
    matches = []
    for name in candidates if candidates is not None else playable_levels():
        try:
            if replay(load_level_by_name(name), inputs, name).solved:
                matches.append(name)
        except NotImplementedError:
            raise
        except Exception:
            continue  # a wrong pairing can fail in arbitrary ways; that is a non-match
    return matches
