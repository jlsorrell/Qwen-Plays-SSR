"""Transition rules.

NOT YET IMPLEMENTED. Rules are transcribed from the decompiled `GameState` /
`Entity` logic into `docs/mechanics.md`, then implemented here, then verified by
`.dem` replay. See Tasks 9-13 of the Phase 0 plan.
"""

from dataclasses import dataclass

from .state import GameState
from .types import Input


@dataclass(frozen=True, slots=True)
class StepResult:
    state: GameState
    solved: bool = False
    lost: bool = False
    reason: str | None = None


def step(
    state: GameState,
    action: Input | None,
    history: list[GameState] | None = None,
) -> StepResult:
    """Apply one input.

    `action=None` queries terminal status without moving.

    `history` enables undo. Pass `None` to withhold undo entirely — spec §7.1
    requires this be switchable, because unlimited undo makes solve rate
    degenerate while `.dem` replay of world 5+ needs it.
    """
    raise NotImplementedError(
        "mechanics not yet transcribed — see Tasks 9-13 of the Phase 0 plan"
    )
