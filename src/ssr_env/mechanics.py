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

from .entity import Entity, pack_cookdata
from .geometry import (
    NEEDS_GROUND_TYPES,
    border_cells,
    cells_of,
    ent_at,
    is_extended,
    floor_under,
    is_solid,
    occupies,
    solid_ent_at,
    under,
)
from .level import (
    bbq_direction_from_mask,
    ladder_direction_from_mask,
    mask_value_at,
    resolve_island_mask,
)
from .state import GameState, with_entities
from .types import (
    Coord,
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
    state: GameState,
    cell,
    direction: Direction,
    masks,
    level_name: str,
    can_change_player_footing: bool = False,
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
    return try_push(
        state,
        target,
        direction,
        masks,
        level_name,
        can_change_player_footing=can_change_player_footing,
    )


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

    entry = state
    state = apply_pivot_forces_1(
        state, player, pushdir, player.direction, diagonal, masks, level_name
    )
    # The player braces against its own footing — the one place the game passes
    # canchangeplayerfooting, because a pivot moves the island underneath.
    state = _force_at(
        state,
        player.pos + Direction.DOWN.delta,
        pushdir,
        masks,
        level_name,
        can_change_player_footing=True,
    )

    # **The pivot only happens if the floor actually moved.** The game keeps that
    # result and refuses on it:
    #
    #     flag = ApplyForce(e.pos + Coord.Down, pushdir, 0, 1, ...);
    #     if (!flag || e.Collides()) { RestoreEntities(); return false; }
    #
    # Discarding it made every blocked turn pivot, walking the player a cell
    # backwards and completing a turn the game refuses outright. Inside a level
    # this is not an edge case but the norm: the floor is the level's own
    # island, and `TryPushEnt` rejects it (`pushtargetlevel == e.dat`), so a
    # pivot turn can never succeed there. Confirmed by play at key 80 of
    # Emerson Jetty — see docs/mechanics.md §12.34.
    if state.by_id(footing.id).pos == footing.pos:
        return StepResult(
            state=entry,
            moved=False,
            reason="turn blocked (pivot needs the footing to move)",
        )

    player = state.player
    state = apply_pivot_forces_2(
        state, player, pushdir, player.direction, diagonal, masks, level_name
    )

    player = state.player
    landing = player.pos + pushdir.delta
    # A pivot displaces the player, so it is subject to the same rule as walking:
    # you cannot end up over void. Without this the player pivots off the island
    # and drowns, which is not something the real game permits.
    if not solid_ent_at(state, landing + Direction.DOWN.delta, masks, level_name):
        return StepResult(
            state=state, moved=False, reason=f"no ground to pivot onto at {tuple(landing)}"
        )
    pivoted = replace(player, pos=landing, direction=target_facing)
    return StepResult(state=state.replace_entity(pivoted))


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
        # No collision test here. `TryTurn` applies force through the swept
        # cell and then checks `Collides()` on the *rotated entity* — i.e. the
        # fork's destination. Refusing the turn because the diagonal is occupied
        # made every turn beside overworld rock pivot instead, walking the
        # player backwards.

    # Phase 2 (TurnOut): complete to the target cardinal.
    turned = replace(player, direction=direction)
    candidate = state.replace_entity(turned)
    # A rotating extended entity occupies the body, the fork's old cell, and
    # `pos + movement.to` (§12.8) — and `movement.to` is the swept **diagonal**,
    # since `TryTurn` passes `RotBetween` as `to`. The fork's final cardinal cell
    # is never part of a rotation's occupancy, so it must not be tested here.
    collide_cell = (
        player.pos + diagonal.delta
        if diagonal is not None and is_extended(player, state)
        else turned.pos + direction.delta
    )
    if _blocked_for(candidate, turned, collide_cell, masks, level_name):
        return try_pivot_turn(state, direction, masks, level_name)

    # Phase 2 (TurnOut). The fork travels from the diagonal to its final
    # cardinal cell, so *that* cell is this phase's entering cell — and whatever
    # occupies it is pushed, in direction `ContinueRot(turndir, diagonal).Inverse()`.
    # Modelling only phase 1 meant the fork swung onto sausages without moving
    # them (§12.10).
    if diagonal is not None and is_extended(player, state):
        cardinal = player.pos + direction.delta
        # Look past the player: in `candidate` it has already turned, so it
        # occupies the cardinal cell itself and would otherwise mask whatever is
        # actually standing there.
        occupant = next(
            (
                e
                for e in candidate.entities
                if e.id != turned.id
                and is_solid(e, candidate.tileset)
                and occupies(e, cardinal, candidate, masks, level_name)
            ),
            None,
        )
        if occupant is not None:
            # `ContinueRot(turndir, direction)`: target cardinal first,
            # current (diagonal) facing second. Order matters — see §2.1.
            push_dir = _continue(direction, diagonal).inverse()
            if push_dir.is_valid:
                pushed = try_push(candidate, occupant, push_dir, masks, level_name)
                if pushed is candidate:
                    return try_pivot_turn(state, direction, masks, level_name)
                candidate = pushed

    return StepResult(state=candidate)


def _settle_and_cook(
    before: GameState, after: GameState, masks, level_name: str
) -> GameState:
    """Settle gravity, then cook whatever sausage actually moved.

    `MovementsTick` gathers sausages into `totrycook` as their movements
    resolve, so only sausages that changed this step are cooked. Comparing
    before and after reproduces that without modelling the movement list.
    """
    settled = settle(after, masks, level_name)
    prior = {
        e.id: (e.pos, e.direction, e.rot)
        for e in before.entities
        if e.type is EntType.SAUSAGE
    }
    moved = [
        e.id
        for e in settled.entities
        if e.type is EntType.SAUSAGE
        and prior.get(e.id) != (e.pos, e.direction, e.rot)
    ]
    return cook(settled, moved, masks, level_name) if moved else settled


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
    fell: set[int] = set()
    for _ in range(_MAX_SETTLE_STEPS):
        falling = [
            e
            for e in state.entities
            if e.type in NEEDS_GROUND_TYPES
            and e.stuckto < 0  # a forked sausage hangs from the fork, not the floor
            and not under(e, state, masks, level_name)
            and e.pos.z >= -10
        ]
        if not falling:
            break
        for entity in falling:
            fell.add(entity.id)
            state = state.replace_entity(
                replace(entity, pos=entity.pos + Direction.DOWN.delta)
            )
            # `CanFall_Liberal` defers a laden entity's fall to whatever it is
            # stuck to, so a carried sausage descends with the player.
            if entity.type is EntType.PLAYER and entity.stuckto >= 0:
                carried = state.by_id(entity.stuckto)
                state = state.replace_entity(
                    replace(carried, pos=carried.pos + Direction.DOWN.delta)
                )
    else:
        raise UnimplementedMechanic("settle-loop", "gravity did not reach quiescence")

    # A sausage is only lost if it *fell* there. The game marks it inside the
    # movement loop, on `movement.target` — an entity that just moved:
    #
    #     if (movement.target.type == sausage && movement.target.pos.z < -2
    #         && pushestotry == 0
    #         && (dat.Length == 0 || dat[0] == 'M')) { pos.z = -100; dat = 'L'... }
    #
    # Marking on depth alone drowned sausages that were merely *parked* deep —
    # the world sausage rides the overworld down twenty cells whenever a level
    # is entered, and was being declared lost every step thereafter (§12.35).
    # The `dat[0] == 'M'` test also means an already-lost or spectral sausage is
    # never re-marked.
    for entity in state.entities:
        if entity.pos.z >= OUT_OF_WORLD_Z:
            continue
        if entity.type is EntType.PLAYER:
            return replace(state, lost_reason="Drowned")
        if (
            entity.type is EntType.SAUSAGE
            and entity.id in fell
            and (not entity.dat or entity.dat.startswith("M"))
        ):
            state = state.replace_entity(
                replace(entity, pos=Coord(entity.pos.x, entity.pos.y, -100),
                        dat="L" + entity.dat[1:])
            )
            state = replace(state, lost_reason="SausageLost")
    return state


#: Enough for any real level; a runaway means the fall rules are wrong.
_MAX_SETTLE_STEPS = 64

#: Longest push chain we attempt before treating it as unmodelled.
_MAX_PUSH_DEPTH = 8


def ladder_at(state: GameState, cell, masks, level_name: str = ""):
    """Direction of the ladder at `cell`, or None. Mirrors `GameState.LadderAt`.

    A ladder is either an `EntType.LADDER` entity — whose `direction` is the way
    it faces — or an island mask value in 3..6 (§10.3).
    """
    entity = ent_at(state, cell, masks, level_name)
    if entity is None:
        return None
    if entity.type is EntType.LADDER:
        return entity.direction
    if entity.type is EntType.ISLAND and masks:
        mask = resolve_island_mask(level_name, entity.dat, masks)
        if mask is not None:
            return ladder_direction_from_mask(mask_value_at(mask, entity.pos, cell))
    return None


def ladder_up_in_dir(state: GameState, direction: Direction, masks, level_name="") -> bool:
    """Mirrors `LadderUpInDir`: `LadderAt(pos + dir) == dir.Inverse()`.

    The ladder must *face back toward* the player — you climb a ladder you are
    standing in front of, not one facing away.
    """
    found = ladder_at(state, state.player.pos + direction.delta, masks, level_name)
    return found is not None and found is direction.inverse()


def ladder_down_in_dir(state: GameState, direction: Direction, masks, level_name="") -> bool:
    """Mirrors `LadderDownInDir`: `LadderAt(pos + Down) == dir`."""
    found = ladder_at(
        state, state.player.pos + Direction.DOWN.delta, masks, level_name
    )
    return found is not None and found is direction


#: A ladder taller than this means the climb rules are wrong, not the level.
_MAX_CLIMB = 32


def try_climb_up(
    state: GameState, direction: Direction, masks=None, level_name: str = ""
) -> StepResult:
    """Climb a ladder to its top. Mirrors `TryClimbUp`, resolved to rest.

    The game climbs one level per tick, choosing `ClimbUp_Init` while another
    ladder continues above and `ClimbUp_End1` on the last rung. This simulator
    is settle-driven (§1), so the whole ascent resolves inside one `step`: rise
    while the ladder continues and the cell above is clear, then step forward
    onto the top.

    Resolving to rest matters. An earlier version moved the player up a single
    level and returned, whereupon `settle` — which asks only for solid ground —
    found nothing beneath a player standing on a ladder and dropped it straight
    back. A climb must end somewhere it can stand.
    """
    player = state.player
    pos = player.pos

    rungs = 0
    while rungs < _MAX_CLIMB:
        above = pos + Direction.UP.delta
        if solid_ent_at(state, above, masks, level_name):
            break
        pos = above
        rungs += 1
        # Keep rising only while the ladder continues at the new height.
        if ladder_at(state, pos + direction.delta, masks, level_name) is not direction.inverse():
            break

    if rungs == 0:
        return StepResult(state=state, moved=False, reason="ladder blocked above")

    # Step off the top, onto the tile the ladder was mounted against.
    landing = pos + direction.delta
    if not solid_ent_at(state, landing, masks, level_name) and solid_ent_at(
        state, landing + Direction.DOWN.delta, masks, level_name
    ):
        pos = landing

    climbed = replace(player, pos=pos, dat=str(int(direction)))
    return StepResult(state=state.replace_entity(climbed))


def try_climb_down(
    state: GameState, direction: Direction, masks=None, level_name: str = ""
) -> StepResult:
    """Descend a ladder mounted on the block underfoot. Mirrors `TryClimbDown`.

    `TryClimbDown` is a single horizontal translation by `dir` — the player
    steps off the top of the block and onto the ladder on its face; the
    `ClimbDown_*` movement types then lower it. Here the descent is left to
    `settle`, which already drops anything unsupported to the first solid cell
    beneath it. That is the same resting place, reached in one step (§12.31).
    """
    player = state.player
    destination = player.pos + direction.delta
    if solid_ent_at(state, destination, masks, level_name):
        return StepResult(state=state, moved=False, reason="ladder blocked ahead")
    stepped = replace(player, pos=destination, dat=str(-1 - int(direction)))
    return StepResult(state=state.replace_entity(stepped))


def bbqs_on(state: GameState) -> bool:
    """Whether grills are hot. Mirrors `GameState.bbqsOn`.

    `(pushestotry == 0 && !overworld) || returning`. The `pushestotry` term
    counts down the island-sinking animation, which this simulator settles
    instantly (§1), so it reduces to "inside a level".

    Two things depend on it, and both were missing:

    - `DoCook` returns immediately when grills are off, so **cooking only
      happens inside a level**.
    - Hot grills repel the player (§12.18); cold ones can be stood on, which is
      why walking over grills in the overworld is fine.
    """
    return not state.overworld


def grill_identity_at(state: GameState, cell, masks, level_name: str) -> str:
    """Stable identifier for the grill at a cell, or "" if none.

    Mirrors the `bbqdatstring` that `BBQAtDir` yields: a bbq entity's id, or for
    a mask grill the island's dat plus the local mask coordinate. `DoCook`
    compares this against what the sausage recorded last time to avoid cooking
    the same face on the same grill twice.
    """
    entity = ent_at(state, cell, masks, level_name)
    if entity is None:
        return ""
    if entity.type is EntType.BBQ:
        return str(entity.id)
    if entity.type is EntType.ISLAND and masks:
        mask = resolve_island_mask(level_name, entity.dat, masks)
        # `is not None`, never truthiness: Direction.NORTH is IntEnum value 0
        # and therefore falsy, so a truthiness test silently ignores every
        # north-facing grill.
        if mask is not None and bbq_direction_from_mask(
            mask_value_at(mask, entity.pos, cell)
        ) is not None:
            ox, oy, oz = mask["offset"]
            return (
                f"{entity.dat}.{cell.x - entity.pos.x - ox}"
                f".{cell.y - entity.pos.y - oy}.{cell.z - entity.pos.z - oz}"
            )
    return ""


def grill_direction_at(state: GameState, cell, masks, level_name: str):
    """Grill facing at a cell, or None. Mirrors `GameState.BBQAtDir`.

    Grills come from two sources: `EntType.BBQ` entities carry their own
    direction, and island mask values 2 and 20 encode East and North (§10.3).
    """
    entity = ent_at(state, cell, masks, level_name)
    if entity is None:
        return None
    if entity.type is EntType.BBQ:
        return entity.direction
    if entity.type is EntType.ISLAND and masks:
        mask = resolve_island_mask(level_name, entity.dat, masks)
        if mask is not None:
            return bbq_direction_from_mask(
                mask_value_at(mask, entity.pos, cell)
            )
    return None


#: Which cook face a grill touches, per `DoCook`. Indexed [rot][half], where
#: half 0 is the cell at `pos` and half 1 is the cell at `pos + direction`.
_COOK_FACE = ((3, 0), (2, 1))


def cook(
    state: GameState, sausage_ids, masks=None, level_name: str = ""
) -> GameState:
    """Cook the sausages that just moved. Mirrors `DoCook`. See §9.1.

    Only sausages collected during the tick are cooked — the game gathers them
    into `totrycook` as their movements resolve — so a sausage resting on a
    grill is not re-cooked every turn.

    A raw face (0) becomes 1 or 2 depending on whether the grill runs parallel
    to the sausage; an already-cooked face becomes 3, which is burnt and fatal.
    """
    for sausage_id in sausage_ids:
        try:
            entity = state.by_id(sausage_id)
        except KeyError:
            continue
        if entity.type is not EntType.SAUSAGE or entity.pos.z < OUT_OF_WORLD_Z:
            continue
        faces = list(entity.faces)
        halves = (entity.pos, entity.pos + entity.direction.delta)
        # dat records which grill last cooked each half, as "<flag>;<a>;<b>".
        parts = entity.dat.split(";")
        last = (parts[1], parts[2]) if len(parts) >= 3 else ("", "")
        seen = list(last)
        burnt = False
        for half, cell in enumerate(halves):
            below = cell + Direction.DOWN.delta
            grill = grill_direction_at(state, below, masks, level_name)
            if grill is None:
                seen[half] = ""
                continue
            identity = grill_identity_at(state, below, masks, level_name)
            seen[half] = identity
            if identity and identity == last[half]:
                continue  # same grill as last time; the game does not re-cook
            index = _COOK_FACE[entity.rot][half]
            if faces[index] == 0:
                faces[index] = 2 if grill.parallel_to(entity.direction) else 1
            else:
                faces[index] = 3
                burnt = True
        flag = "B" if burnt else (parts[0] if parts and parts[0] else "M")
        updated = replace(
            entity,
            cookdata=pack_cookdata(tuple(faces)),
            dat=f"{flag};{seen[0]};{seen[1]}",
        )
        state = state.replace_entity(updated)
        if burnt:
            state = replace(state, lost_reason="Burned")
    return state


def try_push(
    state: GameState,
    entity: Entity,
    direction: Direction,
    masks=None,
    level_name: str = "",
    depth: int = 0,
    can_change_player_footing: bool = False,
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
        if (
            not can_change_player_footing
            and not direction.is_vertical
            and footing is not None
            and footing.id == entity.id
        ):
            return state
        # `pushtargetlevel == e.dat` — the island of the level you are inside is
        # never pushable, and unlike the footing guard above, this one is *not*
        # bypassed by `canchangeplayerfooting`. That asymmetry is what makes a
        # pivot turn impossible inside a level: the pivot must shove its own
        # floor, and inside a level the floor is precisely this island (§12.34).
        if state.pushtargetlevel and state.pushtargetlevel == entity.dat:
            return state
        # Otherwise `TryPushEnt` builds an ordinary translation: an island is a
        # movable terrain chunk (the world-6 mechanic). Its mask is indexed
        # relative to `entity.pos`, so moving the entity carries the terrain.
        #
        # `overworld && pushestotry == 0` is still not modelled; that state is
        # not represented here.

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
    # If this sausage carries the exit, the exit travels with it. A roll (torsion
    # non-zero) additionally flips `exit_up`, and inverts `exit_dir` when the
    # exit faces orthogonally to the sausage. Mirrors `Movement.Resolve`'s
    # Translation branch. See §12.16.
    after = state.replace_entity(moved)
    if state.exit_attachment == entity.id and state.exit_pos is not None:
        updated = {"exit_pos": state.exit_pos + direction.delta}
        if rolls:
            updated["exit_up"] = not state.exit_up
            if state.exit_dir is not None and state.exit_dir.ortho_to(entity.direction):
                updated["exit_dir"] = state.exit_dir.inverse()
        after = replace(after, **updated)

    # A pushed entity left unsupported simply falls; `settle` handles it and
    # marks a drowned sausage lost.
    return settle(after, masks, level_name)


def can_fork(
    state: GameState, target, destination, direction: Direction
) -> bool:
    """`TryFork`'s guards, minus the ones the caller has already established.

    The game requires the player to be extended, to be mid-*translation*, and
    for that translation to run along the way it faces — so a strafe or a
    backward step never pierces, only a forward walk. The target cell is
    `player.TargetPos() + player.direction`, which is the fork's destination.

    Two conditions remain to check here:

    - the player must not already be carrying something (`stuckto >= 0`), since
      one fork holds one sausage;
    - the sausage must not *also* occupy the body's destination. A sausage lying
      along the direction of travel with its far end under the player's own
      target cell cannot be picked up — the player would be standing inside it.
    """
    player = state.player
    if player.stuckto >= 0 or target.type is not EntType.SAUSAGE:
        return False
    if direction is not player.direction:
        return False
    return destination not in cells_of(target, state)


def pierce(state: GameState, target) -> GameState:
    """Fork the sausage: `stuckto` points both ways, as `TryFork` sets it.

    `Entity.Collides` skips any entity whose `stuckto` is the player's id, which
    is what lets the fork share a cell with the sausage it has gone into.
    """
    state = state.replace_entity(replace(state.player, stuckto=target.id))
    return state.replace_entity(replace(target, stuckto=state.player.id))


def try_move_player(
    state: GameState,
    direction: Direction,
    masks=None,
    level_name: str = "",
    unfork: bool = False,
) -> StepResult:
    """Walk forward or backward. See docs/mechanics.md §5.1-5.3.

    Only the simple case: flat ground, nothing to push, nothing to fall into.
    """
    player = state.player
    destination = player.pos + direction.delta

    # A carried sausage travels with the player: `TryMovePlayer` gives it its own
    # `Movement.Translation` in the same direction. With `unfork` it gets none,
    # which is how the player pulls the fork back out of it.
    carried = (
        state.by_id(player.stuckto)
        if player.stuckto >= 0 and not unfork
        else None
    )
    carried_cells = frozenset(cells_of(carried, state)) if carried else frozenset()

    # The fork's destination matters too. Moving forward pushes the fork into
    # the cell beyond it; moving backward vacates the body's own cell.
    fork_destination = (
        destination + player.direction.delta if is_extended(player, state) else None
    )
    cells_needed = [destination]
    if fork_destination is not None:
        cells_needed.append(fork_destination)

    for cell in cells_needed:
        if cell == player.pos or cell == fork_cell(state, player):
            continue  # the player is vacating this cell as part of the move
        if cell in carried_cells:
            continue  # the fork is inside this sausage and moving with it
        blocker = ent_at(state, cell, masks, level_name)
        if blocker is None or not solid_ent_at(state, cell, masks, level_name):
            continue
        state = try_push(state, blocker, direction, masks, level_name)
        if not solid_ent_at(state, cell, masks, level_name):
            player = state.player
            continue

        # Nothing shifted. `TryFork` runs at exactly this point in
        # `TryMovePlayer`, and its `!ActivelyForced(sausage)` test — literally
        # `movement != null` — is this same distinction: a sausage the push
        # moved is carried along, a sausage the push could not move is pierced.
        if cell == fork_destination and can_fork(state, blocker, destination, direction):
            state = pierce(state, blocker)
            player = state.player
            continue

        return StepResult(
            state=state, moved=False, reason=f"blocked at {tuple(cell)}"
        )

    # You cannot walk off the island. The move is refused outright rather than
    # permitted and then resolved by gravity.
    #
    # Confirmed by observation: standing on Southjaunt's westmost panel and
    # pressing west does nothing in the real game. An earlier version allowed it
    # because the player is extended and its fork still rested on the island, so
    # `under()` reported support — but the test is on the **body's** destination,
    # not on the pair.
    if not solid_ent_at(state, destination + Direction.DOWN.delta, masks, level_name):
        return StepResult(
            state=state, moved=False, reason=f"no ground at {tuple(destination)}"
        )

    # A **hot** grill repels: stepping onto one bounces the player back to the
    # tile it came from, though anything it pushed on the way still moved.
    # Cold grills — those in the overworld — can be walked on freely, which is
    # why this must be gated on `bbqs_on` rather than applied everywhere.
    if bbqs_on(state) and grill_direction_at(
        state, destination + Direction.DOWN.delta, masks, level_name
    ) is not None:
        # The player rebounds, but anything it pushed on the way still moved,
        # so this must not short-circuit settling and cooking (see `step`).
        return StepResult(
            state=state, moved=False, reason="hot grill: bounced back"
        )

    if carried is not None:
        vacated = carried_cells | {player.pos, fork_cell(state, player)}
        for cell in (c + direction.delta for c in carried_cells):
            if cell in vacated or cell == destination:
                continue
            if solid_ent_at(state, cell, masks, level_name):
                # `TryMovePlayer` retries with `unfork: true` when a laden move
                # fails going backward — backing away pulls the fork out and
                # leaves the sausage behind. Any other direction simply fails.
                if direction is player.direction.inverse():
                    return try_move_player(
                        state, direction, masks, level_name, unfork=True
                    )
                return StepResult(
                    state=state, moved=False, reason=f"carried sausage hits {tuple(cell)}"
                )

    state = state.replace_entity(replace(player, pos=destination))
    if carried is not None:
        state = state.replace_entity(
            replace(carried, pos=carried.pos + direction.delta)
        )
    elif unfork and player.stuckto >= 0:
        dropped = state.by_id(player.stuckto)
        state = state.replace_entity(replace(state.player, stuckto=-1))
        state = state.replace_entity(replace(dropped, stuckto=-1))
    return StepResult(state=state)


def step(
    state: GameState,
    action: Input | None,
    history: list[GameState] | None = None,
    masks=None,
    level_name: str = "",
    meta: dict | None = None,
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
        # The restored state already carries whatever transitions were applied
        # when it was recorded, so it must not be run through them again.
        return StepResult(state=history.pop())

    if not isinstance(action, Direction):
        raise TypeError(f"unexpected action {action!r}")

    player = state.player
    if player.pos.z < -2:
        return StepResult(state=state, moved=False, reason="player out of world")

    if history is not None:
        history.append(state)

    # Mirrors `ProcessInput`, which branches three ways. The ladder tests appear
    # in each branch with different guards, so they are spelled out rather than
    # factored: what changes is *when* a press climbs instead of walking.
    laden = player.stuckto >= 0
    extended = is_extended(player, state)
    ahead_is_supported = solid_ent_at(
        state, player.pos + action.delta + Direction.DOWN.delta, masks, level_name
    )

    def climbs_up() -> bool:
        return ladder_up_in_dir(state, action, masks, level_name)

    def climbs_down() -> bool:
        # Descending needs a ladder on the block underfoot facing the way the
        # player is going, and nothing to simply walk onto — otherwise it walks.
        return not ahead_is_supported and ladder_down_in_dir(
            state, action, masks, level_name
        )

    if laden:
        # A player carrying a sausage cannot turn: every press moves it. Facing
        # is fixed until the sausage is put down, which is what makes carrying
        # awkward to steer and is the whole difficulty of the levels that use it.
        if action.parallel_to(player.direction):
            result = try_move_player(state, action, masks, level_name)
        elif climbs_up():
            result = try_climb_up(state, action, masks, level_name)
        elif climbs_down():
            result = try_climb_down(state, action, masks, level_name)
        else:
            result = try_move_player(state, action, masks, level_name)
    elif action.parallel_to(player.direction):
        # Head-on, climbing needs the fork stowed.
        if not extended and action is player.direction and climbs_up():
            result = try_climb_up(state, action, masks, level_name)
        elif not extended and action is player.direction.inverse() and climbs_down():
            result = try_climb_down(state, action, masks, level_name)
        else:
            result = try_move_player(state, action, masks, level_name)
    elif extended and climbs_up():
        result = try_climb_up(state, action, masks, level_name)
    elif extended and climbs_down():
        result = try_climb_down(state, action, masks, level_name)
    else:
        result = try_turn_player(state, action, masks, level_name)

    if not result.moved:
        if history is not None:
            history.pop()
        # `moved` says the *player* did not relocate — it does not mean nothing
        # happened. A hot-grill rebound still pushes whatever was in the way,
        # and those pushes must settle and cook. Skip the work only when the
        # state is genuinely untouched.
        if result.state is state:
            return result

    # Settle and cook once, against the state as it was on entry. Doing this
    # inside the handlers would compare against a state whose pushes had already
    # been applied, so nothing would look moved.
    settled = _settle_and_cook(state, result.state, masks, level_name)
    settled = _apply_transitions(settled, meta, masks)
    return replace(
        result,
        state=settled,
        lost=settled.lost,
        reason=settled.lost_reason or result.reason,
    )


def issue_world_sausages(state: GameState, meta: dict, masks=None) -> GameState:
    """Spawn a shrine's sausages once every level in its temple is complete.

    Mirrors `IssueWorldSausages`. A shrine is any key of `templedat`, and
    `ShouldIssueSausage` requires that it has not already been issued and that
    every level the temple lists is completed. The sausages appear **on the
    overworld** at `sausagepositions[shrine]`, offset by the shrine's island, and
    the island's `cookdata` is set to 1.

    This is the only thing that changes the overworld as levels are completed —
    `CompleteLevel` itself just appends to a list. Missing it means the player
    walks up to a shrine expecting a sausage that never appeared.

    These are also the sausages `load_overworld` discards at load: they start
    unsupported because they are not yet in play.
    """
    temples = meta.get("temples", {})
    spawns = meta.get("sausages", {})
    islands = {e.dat: e for e in state.entities if e.type is EntType.ISLAND}
    issued = set(state.issued_shrines)
    new: list[Entity] = []
    next_id = max((e.id for e in state.entities), default=0) + 1

    for shrine, levels in temples.items():
        if shrine in issued or shrine not in islands:
            continue
        if not levels or any(lv not in state.completed for lv in levels):
            continue
        island = islands[shrine]
        for spec in spawns.get(shrine, []):
            new.append(
                Entity(
                    pos=island.pos + Coord(*spec["pos"]),
                    type=EntType.SAUSAGE,
                    id=next_id + len(new),
                    direction=Direction(spec["direction"]),
                    dat="M; ; ",
                )
            )
        issued.add(shrine)
        # `entity.cookdata = 1` on the shrine island. On an island this flags
        # "sausages issued" (§10.5), and it changes terrain: `IslandAt` treats
        # mask value -1 as solid only while cookdata is 0, so the shrine's
        # sausage-footprint placeholders stop blocking once issued.
        state = state.replace_entity(replace(island, cookdata=1))

    if not new:
        return state
    updated = with_entities(state, state.entities + tuple(new))
    updated = replace(updated, issued_shrines=frozenset(issued))
    return updated


def _apply_transitions(state: GameState, meta: dict | None, masks) -> GameState:
    """Level entry and exit, applied inside `step`.

    These **must** happen here rather than in the caller. `history` is recorded
    inside `step`, so transitions applied afterwards are invisible to it — undo
    would then rewind to a state that never entered or left a level.

    Every one of the 103 undos in `all.dem` falls after move 855, which is
    exactly where replay stopped tracking while transitions lived in the caller.
    """
    if meta is None:
        return state
    state = check_level_exit(check_overworld_entry(state, meta, masks), meta, masks)
    return issue_world_sausages(state, meta, masks) if state.overworld else state


def _laden(state: GameState) -> bool:
    """Whether the player is carrying a sausage on the fork.

    Approximated by `stuckto` pointing at the player. `Laden`/`LadenTarget` are
    not yet transcribed — see docs/mechanics.md §4.
    """
    player = state.player
    return any(
        e.type is EntType.SAUSAGE and e.stuckto == player.id for e in state.entities
    )


#: Face values that count as properly cooked. `CheckGameWon` rejects 0 (raw)
#: and 3 (burnt); 1 and 2 are the two cooked variants (§9.1).
COOKED_FACE_VALUES = frozenset({1, 2})


def all_cooked(state: GameState) -> bool:
    """Every face of every sausage cooked. Mirrors `CheckGameWon`'s face loop."""
    sausages = state.of_type(EntType.SAUSAGE)
    if not sausages:
        return False
    return all(face in COOKED_FACE_VALUES for s in sausages for face in s.faces)


def is_solved(state: GameState) -> bool:
    """Whether every sausage is cooked. Mirrors `GameState.Won`.

    Every face of every sausage must be 1 or 2. Face 0 is raw and face 3 is
    burnt; either loses. At least one sausage must count, none may be below
    z = -3, and the state must not already be lost.

    **There is no return-to-start requirement here.** That belongs to
    `CheckOnLevelExit`, which additionally requires the player to stand at the
    level's exit pose — a separate condition for *leaving* a solved level, not
    for solving it. §11 previously conflated the two.

    Sausages above z = 8, or whose `dat` begins 'S', are skipped by the game.
    """
    found = False
    for entity in state.entities:
        if entity.type is not EntType.SAUSAGE:
            continue
        if entity.pos.z > 8 or entity.dat.startswith("S"):
            continue
        if entity.pos.z < -3:
            return False
        found = True
        if any(face in (0, 3) for face in entity.faces):
            return False
    return found and not state.lost


#: How far the surrounding islands sink when a level is entered.
#:
#: The game pushes each non-target island down one cell per tick while
#: `pushestotry` counts from 20, staggered by `id % 3` so they sink in waves.
#: The staggering is animation; the settled outcome is a uniform drop, so this
#: models it as a single displacement. `TryRaiseAll` restores them on exit,
#: raising until `pos.z >= 0` or `Bottom() >= -2` — a symmetric restore, which
#: is what pairing entry and exit gives us here.
ISLAND_SINK_DEPTH = 20


def _shift_islands(state: GameState, target: str, dz: int, masks) -> GameState:
    """Move every island but `target` by `dz`, carrying whatever rides on them.

    `TryLowerAll` and `TryRaiseAll` do not teleport islands — they call
    `TryPushEnt(island, Direction.Down, 0, 1)`, and a push in this engine carries
    everything resting on the pushed entity. Displacing only the island left
    riders hanging: the world sausage standing on the overworld dropped out from
    under itself the moment a level was entered, and `settle` then marked it
    `SausageLost` (§12.35).

    Riders are resolved *before* anything moves, because `floor_under` stops
    reporting an island once that island has been displaced.
    """
    moving = {
        e.id for e in state.entities if e.type is EntType.ISLAND and e.dat != target
    }
    riders = set()
    for entity in state.entities:
        if entity.type is EntType.ISLAND or entity.type not in NEEDS_GROUND_TYPES:
            continue
        floor = floor_under(entity, state, masks, "")
        if floor is not None and floor.id in moving:
            riders.add(entity.id)

    shift = Coord(0, 0, dz)

    def moved(e: Entity) -> Entity:
        e = replace(e, pos=e.pos + shift)
        # A sausage carried below the waterline while the islands are sinking is
        # adjudicated as it passes z = -3 (`Movement`, under `pushestotry > 0`):
        # if an island lies in the ten cells beneath either of its halves it is
        # marked 'S' and survives; otherwise it is marked 'L' and lost. A rider
        # is on an island *by construction* and the island descends with it, so
        # the island is always there — riders take the 'S' branch. The losing
        # branch belongs to sausages that were never riding anything, and those
        # do not move here at all; they fall in `settle`.
        if dz < 0 and e.type is EntType.SAUSAGE and e.pos.z < -2:
            if not e.dat or e.dat.startswith("M"):
                e = replace(e, dat="S" + (e.dat[1:] if e.dat else " ; ; "))
        return e

    return with_entities(
        state,
        tuple(
            moved(e) if e.id in moving or e.id in riders else e
            for e in state.entities
        ),
    )


def sink_other_islands(
    state: GameState, target: str, depth: int = ISLAND_SINK_DEPTH, masks=None
):
    """Lower every island except `target`. Mirrors `TryLowerAll`."""
    return _shift_islands(state, target, -depth, masks)


def raise_other_islands(
    state: GameState, target: str, depth: int = ISLAND_SINK_DEPTH, masks=None
):
    """Restore every island except `target`. Mirrors `TryRaiseAll`."""
    return _shift_islands(state, target, depth, masks)


def check_overworld_entry(
    state: GameState, meta: dict, masks=None
) -> GameState:
    """Enter a level when standing on its start cell facing its start direction.

    Mirrors `GameState.CheckOverworldGhosts`, which is what actually triggers
    `SubworldTransition`: for each level, compare the player's position against
    that level's recorded start pose offset by its island entity, and require the
    facing to match too. Walking onto the cell is not enough — you enter only
    once you turn to the right heading, which is why the observed playthrough
    steps on with the fork east and drops in on the next press.

    On entry: the island's `cookdata` flips to 1 (see §10.5, which stops its
    sausage footprints being solid) and that level's sausages are spawned from
    the recorded spawn table.

    Source: `GameState.cs:458 CheckOverworldGhosts`, `GameState.cs:492
    SubworldTransition`, `GameState.cs SpawnSubworldSausages`.
    """
    if not state.overworld:
        return state
    player = state.player
    islands = {e.dat: e for e in state.entities if e.type is EntType.ISLAND}

    for name, pose in meta.get("player", {}).items():
        island = islands.get(name)
        if island is None or name in state.completed:
            continue
        start = island.pos + Coord(*pose["pos"])
        if player.pos != start or player.direction is not Direction(pose["direction"]):
            continue

        entered = state.replace_entity(replace(island, cookdata=1))
        spawns = meta.get("sausages", {}).get(name, [])
        next_id = max((e.id for e in entered.entities), default=0) + 1
        sausages = tuple(
            Entity(
                pos=island.pos + Coord(*s["pos"]),
                type=EntType.SAUSAGE,
                id=next_id + i,
                direction=Direction(s["direction"]),
                dat="M; ; ",
            )
            for i, s in enumerate(spawns)
        )
        entered = with_entities(
            entered,
            entered.entities + sausages,
            overworld=False,
            pushtargetlevel=name,
        )
        # `SubworldTransition` records the exit pose, and notes whether it rests
        # on a sausage — if so the exit rides that sausage (§12.16).
        below = ent_at(entered, start + Direction.DOWN.delta, masks, level_name="")
        entered = replace(
            entered,
            exit_pos=start,
            exit_dir=Direction(pose["direction"]),
            exit_up=True,
            exit_attachment=below.id
            if below is not None and below.type is EntType.SAUSAGE
            else None,
        )
        # `TryLowerAll`: every other island sinks, so only this level is
        # reachable while you are inside it.
        return sink_other_islands(entered, name, masks=masks)
    return state


def level_pose(state: GameState, name: str, meta: dict):
    """The level's entry pose in world coordinates, or None.

    `GetExitPos` computes the *exit* pose exactly as entry is computed —
    `playerpositions[name] + island.pos` — so a level is entered and left at the
    same cell, facing the same way. This is the grain of truth behind the
    "return to start" folklore: it is the condition for *leaving* a solved
    level, not for solving it (§11.1).
    """
    pose = meta.get("player", {}).get(name)
    if pose is None:
        return None
    island = next(
        (e for e in state.entities if e.type is EntType.ISLAND and e.dat == name), None
    )
    if island is None:
        return None
    return island.pos + Coord(*pose["pos"]), Direction(pose["direction"])


def check_level_exit(state: GameState, meta: dict, masks=None) -> GameState:
    """Leave a solved level when the player returns to its entry pose.

    Mirrors `CheckOnLevelExit`, which fires on
    `!overworld && Won() && !LevelCompleted(name) && player.Extended()
     && player.pos == exitPos && player.direction == exitDir`,
    then calls `SubworldLeave`: despawn the level's sausages, mark it complete,
    and return to the overworld.

    The island's `cookdata` is deliberately left at 1. It means "this level's
    sausages have been issued" (§10.5) and nothing observed so far shows it
    being cleared; leaving it set keeps the level's sausage footprints
    non-solid, which is what a completed level should look like from outside.
    """
    if state.overworld or not state.pushtargetlevel:
        return state
    name = state.pushtargetlevel
    if name in state.completed or not is_solved(state):
        return state
    exit_pos, exit_dir = state.exit_pos, state.exit_dir
    if exit_pos is None or exit_dir is None:
        pose = level_pose(state, name, meta)
        if pose is None:
            return state
        exit_pos, exit_dir = pose
    # `CheckOnLevelExit` requires `exitUp`; a roll of the carrying sausage can
    # switch the exit off, and a second roll switches it back on.
    if not state.exit_up:
        return state
    player = state.player
    if player.pos != exit_pos or player.direction is not exit_dir:
        return state
    if not is_extended(player, state):
        return state

    # `DespawnSubworldSausages` does not clear every sausage. It removes those
    # with `dat` empty or beginning 'M' — the level's own, which explode as it is
    # completed — and converts 'S' back to 'M'. An 'S' sausage is one riding the
    # sunken overworld, i.e. a world sausage the player left outside; deleting it
    # here destroyed it every time a level was solved.
    remaining = tuple(
        replace(e, dat="M" + e.dat[1:])
        if e.type is EntType.SAUSAGE and e.dat.startswith("S")
        else e
        for e in state.entities
        if e.type is not EntType.SAUSAGE or e.dat.startswith("S")
    )
    left = with_entities(
        state,
        remaining,
        overworld=True,
        pushtargetlevel="",
        completed=state.completed | {name},
        exit_pos=None,
        exit_dir=None,
        exit_up=True,
        exit_attachment=None,
    )
    # `SubworldLeave` calls `TryRaiseAll`: the surrounding islands come back up.
    return raise_other_islands(left, name, masks=masks)
