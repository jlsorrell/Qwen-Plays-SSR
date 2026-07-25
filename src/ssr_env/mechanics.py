"""Transition rules.

**Partial.** Implements the subset transcribed and understood so far: turning,
and walking forward/backward on flat solid ground with nothing in the way.

Everything else raises `UnimplementedMechanic` rather than guessing. That is
deliberate — a partial simulator that silently does something plausible would
produce replays that diverge far from the real cause. A loud failure naming the
mechanic is the useful signal at this stage.

Rules and their provenance live in `docs/mechanics.md`.
"""

from dataclasses import dataclass, replace

from .entity import Entity
from .geometry import (
    NEEDS_GROUND_TYPES,
    border_cells,
    ent_at,
    is_extended,
    floor_under,
    is_solid,
    occupies,
    solid_ent_at,
    under,
)
from .state import GameState
from .types import (
    ROLLABLE_TYPES,
    STATIC_TYPES,
    Action,
    Direction,
    EntType,
    Input,
)


class UnimplementedMechanic(NotImplementedError):
    """A mechanic that has not been transcribed and implemented yet.

    Carries the mechanic name so replay reports say what is missing rather than
    just failing.
    """

    def __init__(self, mechanic: str, detail: str = "") -> None:
        super().__init__(f"{mechanic}{': ' + detail if detail else ''}")
        self.mechanic = mechanic


@dataclass(frozen=True, slots=True)
class StepResult:
    state: GameState
    solved: bool = False
    lost: bool = False
    reason: str | None = None
    #: False when the input was rejected and the state is unchanged. The game
    #: records these in `moveattempts`; a rejected input still consumes a turn.
    moved: bool = True


def fork_cell(state: GameState, player: Entity):
    """Cell occupied by the fork while it is attached to the player."""
    return player.pos + player.direction.delta


def _supported(state: GameState, pos, masks, level_name: str) -> bool:
    return solid_ent_at(state, pos + Direction.DOWN.delta, masks, level_name)


def _free(state: GameState, pos, masks, level_name: str) -> bool:
    return not solid_ent_at(state, pos, masks, level_name)


def try_turn_player(
    state: GameState, direction: Direction, masks=None, level_name: str = ""
) -> StepResult:
    """Rotate in place. See docs/mechanics.md §5.9.

    Turning sweeps the diagonal between old and new facing and applies force
    through it, so a sausage in that corner would be pushed. Not implemented —
    raises if anything solid occupies the swept cell.
    """
    player = state.player
    swept = player.direction.rot_between(direction)

    # The fork sweeps the diagonal between old and new facing and applies force
    # through it, in the direction of the NEW facing — not along the diagonal.
    if swept is not None and is_extended(player, state):
        cell = player.pos + swept.delta
        blocker = ent_at(state, cell, masks, level_name)
        if blocker is not None and solid_ent_at(state, cell, masks, level_name):
            state = try_push(state, blocker, direction, masks, level_name)
            player = state.player

    turned = replace(player, direction=direction)
    candidate = state.replace_entity(turned)

    # `TryTurn` checks `Collides()` after rotating. On a collision the whole
    # speculative turn is rolled back and the player falls back to a *pivot*
    # turn — rotating about the fork rather than the body. `TryPivotTurn` is not
    # transcribed, so this raises rather than silently failing the turn.
    fork_target = turned.pos + direction.delta
    # The turned player occupies its own fork cell, so `ent_at` would return the
    # player itself and mask a real blocker. Scan for any *other* solid occupant.
    if any(
        entity.id != turned.id
        and is_solid(entity, candidate.tileset)
        and occupies(entity, fork_target, candidate, masks, level_name)
        for entity in candidate.entities
    ):
        # `TryPivotTurn` has a hard precondition: it returns false immediately
        # unless the player is standing on an ISLAND. Off an island a collided
        # turn is simply a failed move, not a pivot.
        footing = floor_under(player, state, masks, level_name)
        if footing is None or footing.type is not EntType.ISLAND:
            return StepResult(
                state=state, moved=False, reason="turn blocked (no pivot: not on island)"
            )
        raise UnimplementedMechanic(
            "pivot-turn", "collided turn on an island falls back to TryPivotTurn"
        )
    return StepResult(state=candidate)


#: Below this z an entity has left the world. Matches the player test in
#: `GameState.Lost()` and `ProcessInput`, and the sausage drowning threshold in
#: `MovementsTick`.
OUT_OF_WORLD_Z = -2


def settle(state: GameState, masks=None, level_name: str = "") -> GameState:
    """Apply gravity until nothing is floating. See docs/mechanics.md §8.

    `Floating(c)` is `EntAt(c + Down)?.Decoration() ?? true` — an entity floats
    when nothing solid supports any of its cells, which is `under()` coming back
    empty. Only `NEEDS_GROUND` types fall.

    Falling below `OUT_OF_WORLD_Z` is fatal: the player drowns, and a sausage is
    marked lost via its `dat` prefix.
    """
    for _ in range(_MAX_SETTLE_STEPS):
        falling = [
            e
            for e in state.entities
            if e.type in NEEDS_GROUND_TYPES
            and not under(e, state, masks, level_name)
            and e.pos.z >= -10
        ]
        if not falling:
            break
        for entity in falling:
            state = state.replace_entity(
                replace(entity, pos=entity.pos + Direction.DOWN.delta)
            )
    else:
        raise UnimplementedMechanic("settle-loop", "gravity did not reach quiescence")

    for entity in state.entities:
        if entity.pos.z >= OUT_OF_WORLD_Z:
            continue
        if entity.type is EntType.PLAYER:
            return replace(state, lost_reason="Drowned")
        if entity.type is EntType.SAUSAGE and not entity.dat.startswith("L"):
            state = state.replace_entity(replace(entity, dat="L" + entity.dat[1:]))
            state = replace(state, lost_reason="SausageLost")
    return state


#: Enough for any real level; a runaway means the fall rules are wrong.
_MAX_SETTLE_STEPS = 64


def try_push(
    state: GameState,
    entity: Entity,
    direction: Direction,
    masks=None,
    level_name: str = "",
) -> GameState:
    """Push one entity. Mirrors `GameState.TryPushEnt`, partially.

    Implemented: sliding a sausage along its own axis, and pushing one-cell
    entities. Rolling raises, because the cook-face permutation is still
    unestablished (docs/mechanics.md §7) and a wrong permutation would corrupt
    every cooking transition downstream.
    """
    # `TryPushEnt` returns false immediately for static types and for barriers:
    #   if (e.type.Static() || e.moving || e.type == EntType.barrier) return false;
    # A failed push is a blocked move, not a missing mechanic. Walking into a
    # wall of ground or a bbq is the ordinary case, not something to raise on.
    if entity.type in STATIC_TYPES or entity.type is EntType.BARRIER:
        return state
    if entity.type is EntType.ISLAND:
        # `TryPushEnt` refuses a horizontal push of the island the player is
        # standing on (unless `canchangeplayerfooting`). Players stand *on*
        # island terrain, so the wall they walk into is usually that same
        # entity, and the push simply fails — a blocked move, not a mechanic.
        footing = floor_under(state.player, state, masks, level_name)
        if not direction.is_vertical and footing is not None and footing.id == entity.id:
            return state
        raise UnimplementedMechanic(
            "push-island", "pushing an island the player is not standing on"
        )

    rolls = entity.type in ROLLABLE_TYPES and not direction.parallel_to(entity.direction)

    for cell in border_cells(entity, state, direction):
        if solid_ent_at(state, cell, masks, level_name):
            raise UnimplementedMechanic(
                "push-chain", f"pushed entity blocked at {tuple(cell)}"
            )

    moved = replace(entity, pos=entity.pos + direction.delta)
    if rolls:
        # A perpendicular push translates the sausage and toggles `rot`, which
        # selects which face meets a grill (docs/mechanics.md §7.1, §9.1).
        # `cookdata` is untouched — faces live in a canonical frame.
        moved = replace(moved, rot=1 - moved.rot)
        # An orthogonal fork stuck to the sausage flips with it.
        fork = next(
            (
                e
                for e in state.entities
                if e.type is EntType.FORK
                and e.id == entity.stuckto
                and e.direction.normal_to(entity.direction)
            ),
            None,
        )
        if fork is not None:
            state = state.replace_entity(
                replace(fork, direction=fork.direction.inverse())
            )
    candidate = state.replace_entity(moved)
    if not under(moved, candidate, masks, level_name):
        raise UnimplementedMechanic(
            "push-into-fall", f"entity {entity.id} unsupported after push"
        )
    return candidate


def try_move_player(
    state: GameState, direction: Direction, masks=None, level_name: str = ""
) -> StepResult:
    """Walk forward or backward. See docs/mechanics.md §5.1-5.3.

    Only the simple case: flat ground, nothing to push, nothing to fall into.
    """
    player = state.player
    destination = player.pos + direction.delta

    # The fork's destination matters too. Moving forward pushes the fork into
    # the cell beyond it; moving backward vacates the body's own cell.
    cells_needed = [destination]
    if is_extended(player, state):
        cells_needed.append(destination + player.direction.delta)

    for cell in cells_needed:
        if cell == player.pos or cell == fork_cell(state, player):
            continue  # the player is vacating this cell as part of the move
        blocker = ent_at(state, cell, masks, level_name)
        if blocker is not None and solid_ent_at(state, cell, masks, level_name):
            state = try_push(state, blocker, direction, masks, level_name)
            if solid_ent_at(state, cell, masks, level_name):
                return StepResult(
                    state=state, moved=False, reason=f"blocked at {tuple(cell)}"
                )
            player = state.player

    moved_state = state.replace_entity(replace(player, pos=destination))
    settled = settle(moved_state, masks, level_name)
    return StepResult(
        state=settled, lost=settled.lost, reason=settled.lost_reason or None
    )


def step(
    state: GameState,
    action: Input | None,
    history: list[GameState] | None = None,
    masks=None,
    level_name: str = "",
) -> StepResult:
    """Apply one input and settle.

    `action=None` queries terminal status without moving.

    `history` enables undo. Pass `None` to withhold undo entirely — spec §7.1
    requires this be switchable, because unlimited undo makes solve rate
    degenerate while `.dem` replay of world 5+ needs it.
    """
    if action is None:
        return StepResult(state=state, solved=is_solved(state), lost=state.lost)

    if action is Action.UNDO:
        if history is None:
            raise ValueError("undo requested but history is None (undo withheld)")
        if not history:
            return StepResult(state=state, moved=False, reason="nothing to undo")
        return StepResult(state=history.pop())

    if not isinstance(action, Direction):
        raise TypeError(f"unexpected action {action!r}")

    player = state.player
    if player.pos.z < -2:
        return StepResult(state=state, moved=False, reason="player out of world")

    if _laden(state):
        raise UnimplementedMechanic("laden movement", "player is carrying a sausage")

    if history is not None:
        history.append(state)

    if action.parallel_to(player.direction):
        result = try_move_player(state, action, masks, level_name)
    else:
        result = try_turn_player(state, action, masks, level_name)

    if not result.moved and history is not None:
        history.pop()
    return result


def _laden(state: GameState) -> bool:
    """Whether the player is carrying a sausage on the fork.

    Approximated by `stuckto` pointing at the player. `Laden`/`LadenTarget` are
    not yet transcribed — see docs/mechanics.md §4.
    """
    player = state.player
    return any(
        e.type is EntType.SAUSAGE and e.stuckto == player.id for e in state.entities
    )


def is_solved(state: GameState) -> bool:
    """All sausages cooked on all four faces, and the player back at start.

    Not yet transcribed — `AllCooked`, `CheckGameWon` and the return-to-start
    condition are §11 of docs/mechanics.md.
    """
    raise UnimplementedMechanic("win condition", "AllCooked/CheckGameWon not transcribed")
