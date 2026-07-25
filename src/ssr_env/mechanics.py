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
    _continue_rot as _continue,
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


def _force_at(
    state: GameState, cell, direction: Direction, masks, level_name: str
) -> GameState:
    """Apply a force at one cell. Mirrors `ApplyForce(pos, dir, ...)`.

    All pivot forces are *weak*, which per §5.11a only suppresses two special
    cases inside `TryPushEnt` that this simulator does not implement yet — so
    weak and strong are currently identical here. Recorded so the distinction is
    not lost when those branches land.
    """
    target = ent_at(state, cell, masks, level_name)
    if target is None or not is_solid(target, state.tileset):
        return state
    return try_push(state, target, direction, masks, level_name)


def apply_pivot_forces_1(
    state: GameState, entity: Entity, movedir, fromdir, todir, masks, level_name
) -> GameState:
    """Mirrors `ApplyPivotForces1`. See docs/mechanics.md §5.11a."""
    if fromdir.is_ortho:
        if not fromdir.parallel_to(movedir) and fromdir.rot_between(movedir) is todir:
            return _force_at(state, entity.pos + todir.delta, fromdir, masks, level_name)
    elif not todir.parallel_to(movedir) and _continue(todir, fromdir) is not movedir:
        return _force_at(state, entity.pos + todir.delta, todir, masks, level_name)
    return state


def apply_pivot_forces_2(
    state: GameState, entity: Entity, movedir, fromdir, todir, masks, level_name
) -> GameState:
    """Mirrors `ApplyPivotForces2`. See the table in docs/mechanics.md §5.11a."""
    p = entity.pos
    m, td = movedir.delta, todir.delta
    cont = _continue(todir, fromdir)

    if fromdir.is_ortho:
        if fromdir is movedir:
            cells = [(p + m + fromdir.delta, movedir), (p + m + td, movedir)]
        elif fromdir is movedir.inverse() or fromdir.rot_between(movedir) is todir:
            cells = [(p + m, movedir), (p + m + td, movedir)]
        else:
            cells = [(p + m, movedir)]
    else:
        if todir is movedir:
            cells = [
                (p + m + fromdir.delta, movedir),
                (p + m + td, movedir),
                (p + m, cont.inverse()),
            ]
        elif todir is movedir.inverse():
            cells = [(p + m, movedir), (p - m, cont.inverse())]
        elif cont is movedir:
            cells = [(p + m, movedir)]
        else:
            cells = [(p + m, movedir), (p + m + td, movedir)]

    for cell, direction in cells:
        state = _force_at(state, cell, direction, masks, level_name)
    return state


def try_pivot_turn(
    state: GameState, target_facing: Direction, masks=None, level_name: str = ""
) -> StepResult:
    """Recovery path when a turn's diagonal phase collides. See §5.11a-b.

    Precondition: the player must be standing on an island. Off one,
    `TryPivotTurn` returns false immediately and the turn is simply refused.

    The transformation is `pos += pushdir; direction = <swept diagonal>`, with
    the second turn phase then carrying the facing to the target cardinal.
    """
    player = state.player
    footing = floor_under(player, state, masks, level_name)
    if footing is None or footing.type is not EntType.ISLAND:
        return StepResult(
            state=state, moved=False, reason="turn blocked (no pivot: not on island)"
        )

    diagonal = player.direction.rot_between(target_facing)
    if diagonal is None:
        return StepResult(state=state, moved=False, reason="no diagonal to pivot through")
    pushdir = target_facing.inverse()

    state = apply_pivot_forces_1(
        state, player, pushdir, player.direction, diagonal, masks, level_name
    )
    # The player braces against its own footing — the one place the game passes
    # canchangeplayerfooting, because a pivot moves the island underneath.
    state = _force_at(
        state, player.pos + Direction.DOWN.delta, pushdir, masks, level_name
    )
    player = state.player
    state = apply_pivot_forces_2(
        state, player, pushdir, player.direction, diagonal, masks, level_name
    )

    player = state.player
    pivoted = replace(player, pos=player.pos + pushdir.delta, direction=target_facing)
    settled = settle(state.replace_entity(pivoted), masks, level_name)
    return StepResult(
        state=settled, lost=settled.lost, reason=settled.lost_reason or None
    )


def try_turn_player(
    state: GameState, direction: Direction, masks=None, level_name: str = ""
) -> StepResult:
    """Turn in place. Two-phase, per docs/mechanics.md §5.11b.

    A turn is `TurnIn` to the diagonal between old and new facing, then a second
    phase to the target cardinal. The diagonal is a real intermediate state —
    `Entity.Turning()` is `direction.Diagonal()` — and it is where the fork
    sweeps and collisions are evaluated. A collision there is what triggers a
    pivot turn.

    Only settled states are returned, and no settled state faces a diagonal, so
    the intermediate never reaches the state key.
    """
    player = state.player
    diagonal = player.direction.rot_between(direction)

    # Phase 1 (TurnIn): the fork sweeps into the diagonal cell, pushing in the
    # direction of the new facing.
    if diagonal is not None and is_extended(player, state):
        swept = player.pos + diagonal.delta
        blocker = ent_at(state, swept, masks, level_name)
        if blocker is not None and is_solid(blocker, state.tileset):
            state = try_push(state, blocker, direction, masks, level_name)
            player = state.player
        if _blocked_for(state, player, swept, masks, level_name):
            return try_pivot_turn(state, direction, masks, level_name)

    # Phase 2 (TurnOut): complete to the target cardinal.
    turned = replace(player, direction=direction)
    candidate = state.replace_entity(turned)
    if _blocked_for(candidate, turned, turned.pos + direction.delta, masks, level_name):
        return try_pivot_turn(state, direction, masks, level_name)

    settled = settle(candidate, masks, level_name)
    return StepResult(
        state=settled, lost=settled.lost, reason=settled.lost_reason or None
    )


def _blocked_for(state: GameState, entity: Entity, cell, masks, level_name: str) -> bool:
    """Whether any entity other than `entity` solidly occupies `cell`."""
    return any(
        e.id != entity.id
        and is_solid(e, state.tileset)
        and occupies(e, cell, state, masks, level_name)
        for e in state.entities
    )


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

#: Longest push chain we attempt before treating it as unmodelled.
_MAX_PUSH_DEPTH = 8


def try_push(
    state: GameState,
    entity: Entity,
    direction: Direction,
    masks=None,
    level_name: str = "",
    depth: int = 0,
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
        players = state.of_type(EntType.PLAYER)
        footing = (
            floor_under(players[0], state, masks, level_name) if players else None
        )
        if not direction.is_vertical and footing is not None and footing.id == entity.id:
            return state
        # Otherwise `TryPushEnt` builds an ordinary translation: an island is a
        # movable terrain chunk (the world-6 mechanic). Its mask is indexed
        # relative to `entity.pos`, so moving the entity carries the terrain.
        #
        # Two further refusals are not modelled because their state is not
        # represented here: `overworld && pushestotry == 0`, and
        # `pushtargetlevel == e.dat`. Neither applies inside a level.

    rolls = entity.type in ROLLABLE_TYPES and not direction.parallel_to(entity.direction)

    # Push chains: `ApplyForce` recurses, so a pushed entity pushes whatever it
    # meets. If the chain fails to clear, the whole push fails and the move is
    # blocked — `TryPushEnt` returns false rather than partially applying.
    for cell in border_cells(entity, state, direction):
        blocker = ent_at(state, cell, masks, level_name)
        if blocker is None or not is_solid(blocker, state.tileset):
            continue
        if blocker.id == entity.id:
            continue
        if depth >= _MAX_PUSH_DEPTH:
            raise UnimplementedMechanic(
                "push-chain", f"chain deeper than {_MAX_PUSH_DEPTH}"
            )
        pushed = try_push(state, blocker, direction, masks, level_name, depth + 1)
        if pushed is state:
            return state  # chain refused; the whole push fails
        state = pushed
        entity = state.by_id(entity.id)

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
    # A pushed entity left unsupported simply falls; `settle` handles it and
    # marks a drowned sausage lost.
    return settle(state.replace_entity(moved), masks, level_name)


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
