"""Movement and turning on the subset implemented so far."""

import pytest

from dataclasses import replace

from ssr_env.entity import Entity, pack_cookdata
from ssr_env.mechanics import UnimplementedMechanic, fork_cell, step, try_move_player
from ssr_env.state import GameState
from ssr_env.types import Action, Coord, Direction, EntType


def flat(width=6, height=6, z=0, player_at=(2, 2), facing=Direction.NORTH, extra=()):
    """A flat plain of solid ground with a player on it."""
    occupied = {(e.pos.x, e.pos.y) for e in extra if e.pos.z == z}
    ents = [
        Entity(pos=Coord(x, y, z), type=EntType.GROUND, id=100 + y * width + x, tileset=1)
        for x in range(width)
        for y in range(height)
        if (x, y) not in occupied
    ]
    ents.append(
        Entity(pos=Coord(player_at[0], player_at[1], z + 1), type=EntType.PLAYER,
               id=1, direction=facing)
    )
    ents.extend(extra)
    return GameState(entities=tuple(ents), tileset=0)


def test_walking_forward_moves_one_cell_north():
    state = flat()
    result = step(state, Direction.NORTH)
    assert result.state.player.pos == Coord(2, 2, 1) + Direction.NORTH.delta


def test_walking_backward_moves_opposite_to_facing():
    state = flat()
    result = step(state, Direction.SOUTH)
    assert result.state.player.pos == Coord(2, 2, 1) + Direction.SOUTH.delta


def test_walking_does_not_change_facing():
    result = step(flat(), Direction.SOUTH)
    assert result.state.player.direction is Direction.NORTH


def test_perpendicular_input_turns_without_moving():
    state = flat()
    result = step(state, Direction.EAST)
    assert result.state.player.direction is Direction.EAST
    assert result.state.player.pos == state.player.pos


def test_turning_then_walking_goes_the_new_way():
    state = step(flat(), Direction.EAST).state
    result = step(state, Direction.EAST)
    assert result.state.player.pos == Coord(3, 2, 1)


def test_fork_sits_one_cell_ahead_of_the_player():
    state = flat(facing=Direction.EAST)
    assert fork_cell(state, state.player) == Coord(3, 2, 1)



def test_walking_into_a_sausage_pushes_it():
    """Player faces North with its fork at (2,3); walking North rolls the
    East-West sausage at (2,4) northward."""
    start = Coord(2, 5, 1)
    spos = shifted(start, Direction.NORTH, Direction.NORTH)
    s = Entity(pos=spos, type=EntType.SAUSAGE, id=50, direction=Direction.EAST)
    state = flat(width=8, height=8, player_at=(start.x, start.y), extra=(s,))
    result = step(state, Direction.NORTH)
    assert result.state.by_id(50).pos == shifted(spos, Direction.NORTH)
    assert result.state.by_id(50).rot == 1


def wall(x, y, z=1, ident=90):
    return Entity(pos=Coord(x, y, z), type=EntType.GROUND, id=ident, tileset=1)


def wedged():
    """A sausage that cannot be pushed: a wall sits where it would slide to.

    Player faces East at (1,2) with its fork over (2,2); the sausage lies
    East-West across (3,2)-(4,2) and a block at (5,2) stops it sliding.
    """
    return flat(
        width=7,
        player_at=(1, 2),
        facing=Direction.EAST,
        extra=(sausage(3, 2, facing=Direction.EAST), wall(5, 2)),
    )


def test_walking_into_an_immovable_sausage_pierces_it():
    """`TryFork` fires exactly where the push failed.

    Its guard is `!ActivelyForced(sausage)` — literally `movement != null` — so
    a sausage the push moved is pushed, and one the push could not move is
    forked. Before this existed the move was simply refused, and Emerson Jetty,
    the first level that needs carrying, was unsolvable.
    """
    result = step(wedged(), Direction.EAST)
    assert result.moved
    assert result.state.player.stuckto == 50
    assert result.state.by_id(50).stuckto == result.state.player.id


def test_a_pushable_sausage_is_pushed_not_pierced():
    state = flat(player_at=(1, 2), facing=Direction.EAST,
                 extra=(sausage(3, 2, facing=Direction.EAST),))
    result = step(state, Direction.EAST)
    assert result.state.player.stuckto == -1


def test_the_carried_sausage_travels_with_the_player():
    state = step(wedged(), Direction.EAST).state
    before = state.by_id(50).pos
    after = step(state, Direction.NORTH).state
    assert after.by_id(50).pos == before + Direction.NORTH.delta
    assert after.player.pos == state.player.pos + Direction.NORTH.delta


def test_a_carrying_player_cannot_turn():
    """`ProcessInput`'s laden branch has no `TryTurnPlayer` at all."""
    state = step(wedged(), Direction.EAST).state
    assert state.player.direction is Direction.EAST
    after = step(state, Direction.NORTH).state
    assert after.player.direction is Direction.EAST, "carrying should not turn"


def test_a_carried_sausage_does_not_fall():
    """The fork holds it, so `settle` must leave it alone over a gap."""
    state = step(wedged(), Direction.EAST).state
    z = state.by_id(50).pos.z
    # Walk north onto ground, then confirm the sausage stayed at fork height.
    after = step(state, Direction.NORTH).state
    assert after.by_id(50).pos.z == z


def test_undo_restores_the_previous_state():
    state = flat()
    history: list[GameState] = []
    moved = step(state, Direction.NORTH, history).state
    assert moved.player.pos != state.player.pos
    restored = step(moved, Action.UNDO, history).state
    assert restored.state_key() == state.state_key()


def test_undo_raises_when_history_is_withheld():
    """Spec 7.1: the primary solve-rate metric must be able to withhold undo."""
    with pytest.raises(ValueError, match="undo withheld"):
        step(flat(), Action.UNDO, history=None)


def test_undo_with_empty_history_is_a_no_op():
    result = step(flat(), Action.UNDO, history=[])
    assert not result.moved


def test_moving_pushes_onto_history():
    history: list[GameState] = []
    step(flat(), Direction.NORTH, history)
    assert len(history) == 1


def test_player_out_of_world_rejects_input():
    state = flat()
    sunk = state.replace_entity(
        Entity(pos=Coord(2, 2, -50), type=EntType.PLAYER, id=1, direction=Direction.NORTH)
    )
    result = step(sunk, Direction.NORTH)
    assert not result.moved and result.reason == "player out of world"


def test_walking_is_reversible_on_open_ground():
    """Not a game rule — a consistency check on the translation logic."""
    state = flat()
    there = step(state, Direction.NORTH).state
    back = step(there, Direction.SOUTH).state
    assert back.state_key() == state.state_key()


def sausage(x, y, z=1, ident=50, facing=Direction.EAST):
    return Entity(pos=Coord(x, y, z), type=EntType.SAUSAGE, id=ident, direction=facing)


def shifted(base: Coord, *dirs: Direction) -> Coord:
    """`base` stepped once per direction.

    Fixtures place entities relative to the player this way rather than at
    absolute coordinates. A hardcoded neighbour bakes in an orientation, and
    that is exactly how the north/south inversion stayed hidden for so long.
    """
    for d in dirs:
        base = base + d.delta
    return base


def test_sausage_slides_when_pushed_along_its_axis():
    """Player faces East, sausage lies East-West ahead of it: a parallel push."""
    state = flat(player_at=(1, 2), facing=Direction.EAST,
                 extra=(sausage(2, 2, facing=Direction.EAST),))
    result = step(state, Direction.EAST)
    assert result.state.by_id(50).pos == Coord(3, 2, 1)


def test_sliding_preserves_cook_faces():
    """A slide imparts no roll, so cookdata must be untouched."""
    s = Entity(pos=Coord(2, 2, 1), type=EntType.SAUSAGE, id=50,
               direction=Direction.EAST, cookdata=9)
    state = flat(player_at=(1, 2), facing=Direction.EAST, extra=(s,))
    result = step(state, Direction.EAST)
    assert result.state.by_id(50).cookdata == 9


def test_perpendicular_push_rolls_the_sausage():
    """A roll translates the sausage and toggles rot; cookdata is untouched."""
    start = Coord(3, 5, 1)
    spos = shifted(start, Direction.NORTH, Direction.NORTH)
    state = flat(width=8, height=8, player_at=(start.x, start.y), facing=Direction.NORTH,
                 extra=(Entity(pos=spos, type=EntType.SAUSAGE, id=50,
                               direction=Direction.EAST),))
    before = state.by_id(50)
    after = step(state, Direction.NORTH).state.by_id(50)
    assert after.pos == shifted(spos, Direction.NORTH)
    assert after.rot == 1 - before.rot
    assert after.cookdata == before.cookdata


def test_two_rolls_restore_the_original_rot():
    """rot is mod 2, so rolling back and forth returns the exposed face."""
    state = flat(width=9, height=9, player_at=(2, 1), facing=Direction.NORTH,
                 extra=(sausage(2, 3, facing=Direction.EAST),))
    once = step(state, Direction.NORTH).state
    twice = step(once, Direction.NORTH).state
    assert twice.by_id(50).rot == state.by_id(50).rot


def test_rolling_changes_state_identity():
    """rot is in the state key, so a roll is a genuinely different state."""
    state = flat(width=8, height=8, player_at=(2, 1), facing=Direction.NORTH,
                 extra=(sausage(2, 3, facing=Direction.EAST),))
    rolled = step(state, Direction.NORTH).state
    assert rolled.state_key() != state.state_key()


def test_sliding_still_leaves_rot_alone():
    """A parallel push is a slide: no rotation, so rot must not change."""
    state = flat(player_at=(1, 2), facing=Direction.EAST,
                 extra=(sausage(2, 2, facing=Direction.EAST),))
    before = state.by_id(50)
    after = step(state, Direction.EAST).state.by_id(50)
    assert after.rot == before.rot


def test_pushing_a_sausage_into_a_void_loses_it():
    """Both of the sausage's cells must lose support before it falls.

    A sausage half over a ledge is still supported, so the void has to be wide
    enough to swallow the whole thing.
    """
    from ssr_env.mechanics import try_push

    ground = [
        Entity(pos=Coord(x, 0, 0), type=EntType.GROUND, id=200 + x, tileset=1)
        for x in range(2)
    ]
    # Occupies (1,0) and (2,0); already half over the edge. Pushing East puts
    # both cells past the ground and it loses support entirely.
    s = Entity(pos=Coord(1, 0, 1), type=EntType.SAUSAGE, id=50, direction=Direction.EAST)
    state = GameState(entities=(*ground, s), tileset=0)
    after = try_push(state, s, Direction.EAST)
    assert after.lost_reason == "SausageLost"
    assert after.by_id(50).dat.startswith("L")


def test_a_sausage_half_over_a_ledge_is_still_supported():
    from ssr_env.geometry import under

    ground = [
        Entity(pos=Coord(x, 0, 0), type=EntType.GROUND, id=200 + x, tileset=1)
        for x in range(2)
    ]
    s = Entity(pos=Coord(1, 0, 1), type=EntType.SAUSAGE, id=50, direction=Direction.EAST)
    state = GameState(entities=(*ground, s), tileset=0)
    assert len(under(s, state)) == 1


def test_border_of_a_one_cell_entity_is_the_next_cell():
    from ssr_env.geometry import border_cells

    p = Entity(pos=Coord(0, 0, 0), type=EntType.BARRIER, id=9)
    st = GameState(entities=(p,))
    assert border_cells(p, st, Direction.NORTH) == (shifted(Coord(0, 0, 0), Direction.NORTH),)


def test_border_perpendicular_covers_both_cells():
    from ssr_env.geometry import border_cells

    s = sausage(0, 0, z=0, facing=Direction.EAST)
    st = GameState(entities=(s,))
    assert border_cells(s, st, Direction.NORTH) == (
        shifted(Coord(0, 0, 0), Direction.NORTH),
        shifted(Coord(1, 0, 0), Direction.NORTH),
    )


def test_border_along_axis_is_the_far_end():
    from ssr_env.geometry import border_cells

    s = sausage(0, 0, z=0, facing=Direction.EAST)
    st = GameState(entities=(s,))
    assert border_cells(s, st, Direction.EAST) == (Coord(2, 0, 0),)


def test_under_finds_support_at_both_cells_of_a_sausage():
    from ssr_env.geometry import under

    state = flat(extra=(sausage(3, 3, facing=Direction.EAST),))
    assert len(under(state.by_id(50), state)) == 2


def test_turning_pushes_a_sausage_out_of_the_swept_corner():
    """The fork sweeps the diagonal and pushes in the direction of the new facing.

    Player at (2,2) facing North turning East sweeps (3,3). A sausage lying
    East-West there takes a push East, which is parallel to its axis: a slide.
    """
    start = Coord(3, 3, 1)
    spos = shifted(start, Direction.NORTHEAST)
    state = flat(width=8, height=8, player_at=(start.x, start.y), facing=Direction.NORTH,
                 extra=(Entity(pos=spos, type=EntType.SAUSAGE, id=50,
                               direction=Direction.EAST),))
    result = step(state, Direction.EAST)
    assert result.state.player.direction is Direction.EAST
    assert result.state.by_id(50).pos == shifted(spos, Direction.EAST)


def test_turn_push_can_roll_the_swept_sausage():
    """A swept sausage lying across the push direction rolls."""
    start = Coord(3, 3, 1)
    spos = shifted(start, Direction.NORTHEAST)
    state = flat(width=8, height=8, player_at=(start.x, start.y), facing=Direction.NORTH,
                 extra=(Entity(pos=spos, type=EntType.SAUSAGE, id=50,
                               direction=Direction.NORTH),))
    result = step(state, Direction.EAST)
    assert result.state.by_id(50).pos == shifted(spos, Direction.EAST)
    assert result.state.by_id(50).rot == 1


#: The cell a player at (2,2,1) facing North sweeps when turning East. A turn
#: collides against the swept diagonal, not the fork's destination (§12.8), so
#: fixtures that want to force a collision must block this cell.
SWEPT_NE = Coord(2, 2, 1) + Direction.NORTHEAST.delta


def island_state(barrier_at=SWEPT_NE, facing=Direction.NORTH):
    """Player on a 3x3 island chunk, optionally with a barrier in the swept cell."""
    island = Entity(pos=Coord(2, 2, 0), type=EntType.ISLAND, id=70, dat="island0")
    player = Entity(pos=Coord(2, 2, 1), type=EntType.PLAYER, id=1, direction=facing)
    ents = [island, player]
    if barrier_at is not None:
        ents.append(Entity(pos=Coord(*barrier_at), type=EntType.BARRIER, id=60))
    masks = {"lvl__island0": {"offset": [-1, -1, 0], "mask": [[[1]] * 3] * 3}}
    return GameState(entities=tuple(ents), tileset=0), masks


def test_collided_turn_on_an_island_pivots():
    """A blocked turn on an island pivots: pos += pushdir, facing the target.

    pushdir is the inverse of the new facing, so turning East shifts West.
    """
    state, masks = island_state()
    result = step(state, Direction.EAST, None, masks, "lvl")
    assert result.state.player.direction is Direction.EAST
    assert result.state.player.pos == Coord(1, 2, 1)


def test_an_unblocked_turn_does_not_pivot():
    state, masks = island_state(barrier_at=None)
    result = step(state, Direction.EAST, None, masks, "lvl")
    assert result.state.player.direction is Direction.EAST
    assert result.state.player.pos == Coord(2, 2, 1)


def test_pivot_is_refused_off_an_island():
    """TryPivotTurn returns false unless Floor(player) is an island."""
    barrier = Entity(pos=SWEPT_NE, type=EntType.BARRIER, id=60)
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH,
                 extra=(barrier,))
    result = step(state, Direction.EAST)
    assert not result.moved and "not on island" in result.reason


def test_turning_with_a_clear_corner_still_works():
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH)
    assert step(state, Direction.EAST).state.player.direction is Direction.EAST


def test_collided_turn_off_an_island_is_a_failed_move_not_a_pivot():
    """TryPivotTurn returns false unless the player stands on an island."""
    barrier = Entity(pos=SWEPT_NE, type=EntType.BARRIER, id=60)
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH,
                 extra=(barrier,))
    result = step(state, Direction.EAST)
    assert not result.moved
    assert "not on island" in result.reason
    assert result.state.player.direction is Direction.NORTH


def test_pushing_static_terrain_is_a_blocked_move_not_a_raise():
    """TryPushEnt returns false for static types; that is a blocked move."""
    from ssr_env.mechanics import try_push

    wall = Entity(pos=Coord(3, 2, 1), type=EntType.GROUND, id=60, tileset=1)
    state = flat(width=8, height=8, player_at=(1, 2), facing=Direction.EAST,
                 extra=(wall,))
    assert try_push(state, wall, Direction.EAST) is state
    result = step(state, Direction.EAST)
    assert not result.moved


def test_walking_off_an_edge_is_refused_not_fatal():
    """You cannot walk off the island — the move is refused.

    Confirmed against the real game: standing on the westmost panel of a level
    and pressing west does nothing. This suite previously asserted the player
    drowned instead, which let the replay wander off islands.
    """
    edge = 5 if Direction.SOUTH.delta.y > 0 else 0
    state = flat(player_at=(0, edge), facing=Direction.SOUTH)
    result = step(state, Direction.SOUTH)
    assert not result.lost
    assert not result.moved
    assert result.state.player.pos == state.player.pos


def test_an_extended_player_cannot_walk_out_on_its_fork():
    """Support at the fork does not license walking the body into void.

    The check is on the body's destination. The player is extended, so `under()`
    reports support whenever either cell rests on ground — which previously let
    the body step off an edge while the fork still held it up.
    """
    edge = 5 if Direction.SOUTH.delta.y > 0 else 0
    state = flat(player_at=(0, edge), facing=Direction.NORTH)
    result = step(state, Direction.SOUTH)
    assert not result.moved and not result.lost


def test_a_supported_move_does_not_fall():
    result = step(flat(), Direction.NORTH)
    assert not result.lost
    assert result.state.player.pos == Coord(2, 2, 1) + Direction.NORTH.delta


def test_settle_drops_an_unsupported_entity_onto_the_ground():
    from ssr_env.mechanics import settle

    ground = Entity(pos=Coord(0, 0, 0), type=EntType.GROUND, id=9, tileset=1)
    player = Entity(pos=Coord(0, 0, 5), type=EntType.PLAYER, id=1,
                    direction=Direction.NONE)
    settled = settle(GameState(entities=(ground, player), tileset=0))
    assert settled.by_id(1).pos == Coord(0, 0, 1)
    assert not settled.lost


def test_settle_is_idempotent_once_resting():
    from ssr_env.mechanics import settle

    once = settle(flat())
    assert settle(once).state_key() == once.state_key()


def test_push_chain_moves_two_sausages():
    """ApplyForce recurses, so a pushed sausage pushes the next one."""
    a = sausage(2, 2, ident=50, facing=Direction.EAST)
    b = sausage(4, 2, ident=51, facing=Direction.EAST)
    state = flat(width=10, height=6, player_at=(1, 2), facing=Direction.EAST,
                 extra=(a, b))
    result = step(state, Direction.EAST)
    assert result.state.by_id(50).pos == Coord(3, 2, 1)
    assert result.state.by_id(51).pos == Coord(5, 2, 1)


def test_a_refused_chain_blocks_the_whole_push():
    """TryPushEnt returns false rather than partially applying a chain."""
    a = sausage(2, 2, ident=50, facing=Direction.EAST)
    wall = Entity(pos=Coord(4, 2, 1), type=EntType.BARRIER, id=61)
    state = flat(width=10, height=6, player_at=(1, 2), facing=Direction.EAST,
                 extra=(a, wall))
    result = step(state, Direction.EAST)
    assert result.state.by_id(50).pos == Coord(2, 2, 1)
    assert not result.moved


def test_pushing_an_island_carries_its_terrain():
    """An island is a movable chunk; its mask is indexed off entity.pos."""
    from ssr_env.geometry import solid_ent_at
    from ssr_env.mechanics import try_push

    island = Entity(pos=Coord(5, 0, 0), type=EntType.ISLAND, id=70, dat="island0")
    masks = {"lvl__island0": {"offset": [0, 0, 0], "mask": [[[1]]]}}
    state = GameState(entities=(island,), tileset=0)
    assert solid_ent_at(state, Coord(5, 0, 0), masks, "lvl")
    after = try_push(state, island, Direction.EAST, masks, "lvl")
    assert after.by_id(70).pos == Coord(6, 0, 0)
    assert solid_ent_at(after, Coord(6, 0, 0), masks, "lvl")
    assert not solid_ent_at(after, Coord(5, 0, 0), masks, "lvl")


def test_the_island_underfoot_is_not_pushable():
    """TryPushEnt refuses a horizontal push of the player's own footing."""
    from ssr_env.mechanics import try_push

    state, masks = island_state(barrier_at=None)
    island = state.by_id(70)
    assert try_push(state, island, Direction.EAST, masks, "lvl") is state


def grill(x, y, z=0, ident=80, facing=Direction.EAST):
    return Entity(pos=Coord(x, y, z), type=EntType.BBQ, id=ident, direction=facing)


def test_rolling_onto_a_grill_cooks_a_face():
    """Perpendicular grill cooks to 1; rot 0 cooks face 0 of the second half."""
    start = Coord(3, 5, 1)
    spos = shifted(start, Direction.NORTH, Direction.NORTH)
    gpos = shifted(spos, Direction.NORTH)
    s = Entity(pos=spos, type=EntType.SAUSAGE, id=50, direction=Direction.EAST)
    state = flat(width=8, height=8, player_at=(start.x, start.y), facing=Direction.NORTH,
                 extra=(s, grill(gpos.x, gpos.y, facing=Direction.NORTH)))
    after = step(state, Direction.NORTH).state.by_id(50)
    assert after.faces != (0, 0, 0, 0)
    assert 1 in after.faces


def test_a_parallel_grill_cooks_to_two():
    start = Coord(3, 5, 1)
    spos = shifted(start, Direction.NORTH, Direction.NORTH)
    gpos = shifted(spos, Direction.NORTH)
    s = Entity(pos=spos, type=EntType.SAUSAGE, id=50, direction=Direction.EAST)
    state = flat(width=8, height=8, player_at=(start.x, start.y), facing=Direction.NORTH,
                 extra=(s, grill(gpos.x, gpos.y, facing=Direction.EAST)))
    after = step(state, Direction.NORTH).state.by_id(50)
    assert 2 in after.faces


def test_cooking_the_same_face_twice_burns_it():
    """A face that is already non-zero goes to 3, which is fatal."""
    from ssr_env.mechanics import cook

    # rot 0 cooks face 3 of the half at `pos`, so face 3 is the one pre-cooked
    # and the grill must sit directly beneath that half.
    s = Entity(pos=Coord(2, 2, 1), type=EntType.SAUSAGE, id=50,
               direction=Direction.EAST, cookdata=pack_cookdata((0, 0, 0, 1)))
    state = flat(width=8, height=8, extra=(s, grill(2, 2, facing=Direction.NORTH)))
    after = cook(state, [50])
    assert 3 in after.by_id(50).faces
    assert after.lost_reason == "Burned"
    assert after.by_id(50).dat.startswith("B;")


def test_a_stationary_sausage_is_not_recooked():
    """Only sausages that moved enter totrycook, so resting does not burn."""
    s = sausage(4, 4, ident=50, facing=Direction.EAST)
    state = flat(width=8, height=8, extra=(s, grill(4, 3, facing=Direction.NORTH)))
    once = step(state, Direction.NORTH).state
    twice = step(once, Direction.NORTH).state
    assert twice.by_id(50).faces == state.by_id(50).faces


def test_grills_are_read_from_island_masks_too():
    from ssr_env.mechanics import grill_direction_at

    island = Entity(pos=Coord(0, 0, 0), type=EntType.ISLAND, id=70, dat="island0")
    masks = {"lvl__island0": {"offset": [0, 0, 0], "mask": [[[2]]]}}
    state = GameState(entities=(island,), tileset=0)
    assert grill_direction_at(state, Coord(0, 0, 0), masks, "lvl") is Direction.EAST


def test_all_cooked_requires_every_face_in_one_or_two():
    from ssr_env.mechanics import all_cooked

    done = sausage(4, 4, ident=50, facing=Direction.EAST)
    done = replace(done, cookdata=pack_cookdata((1, 2, 1, 2)))
    assert all_cooked(flat(width=8, height=8, extra=(done,)))


def test_a_raw_face_is_not_cooked():
    from ssr_env.mechanics import all_cooked

    s = replace(sausage(4, 4, ident=50), cookdata=pack_cookdata((1, 2, 0, 2)))
    assert not all_cooked(flat(width=8, height=8, extra=(s,)))


def test_a_burnt_face_is_not_cooked():
    """CheckGameWon rejects 3 as firmly as it rejects 0."""
    from ssr_env.mechanics import all_cooked

    s = replace(sausage(4, 4, ident=50), cookdata=pack_cookdata((1, 2, 3, 2)))
    assert not all_cooked(flat(width=8, height=8, extra=(s,)))


def test_winning_does_not_require_returning_to_the_start():
    """`Won()` checks cooking alone.

    Returning to the start pose is widely described as part of the win
    condition, and this suite previously asserted it. It is not: that belongs
    to `CheckOnLevelExit`, the condition for *leaving* a solved level.
    """
    from ssr_env.mechanics import is_solved

    s = replace(sausage(4, 4, ident=50), cookdata=pack_cookdata((1, 2, 1, 2)))
    state = flat(width=8, height=8, extra=(s,))
    assert is_solved(replace(state, start_pos=state.player.pos))
    assert is_solved(replace(state, start_pos=Coord(7, 7, 1)))


def test_a_raw_or_burnt_face_prevents_the_win():
    from ssr_env.mechanics import is_solved

    base = flat(width=8, height=8)
    for faces, why in (((1, 2, 0, 2), "raw"), ((1, 2, 3, 2), "burnt")):
        s = replace(sausage(4, 4, ident=50), cookdata=pack_cookdata(faces))
        assert not is_solved(flat(width=8, height=8, extra=(s,))), why


def test_both_cooked_face_values_count_as_done():
    """0 raw, 1 and 2 cooked, 3 burnt — real play produces all-1s and all-2s."""
    from ssr_env.mechanics import is_solved

    for faces in ((1, 1, 1, 1), (2, 2, 2, 2), (1, 2, 2, 1)):
        s = replace(sausage(4, 4, ident=50), cookdata=pack_cookdata(faces))
        assert is_solved(flat(width=8, height=8, extra=(s,)))


def test_a_level_with_no_sausages_is_not_solved():
    from ssr_env.mechanics import is_solved

    assert not is_solved(flat(width=8, height=8))


def test_a_lost_state_is_never_solved():
    from ssr_env.mechanics import is_solved

    s = replace(sausage(4, 4, ident=50), cookdata=pack_cookdata((1, 2, 1, 2)))
    state = flat(width=8, height=8, extra=(s,))
    state = replace(state, start_pos=state.player.pos, lost_reason="Burned")
    assert not is_solved(state)


def ladder_world(height=2, facing=Direction.NORTH):
    """A wall `height` tall with a ladder up its south face, player facing it."""
    ents = []
    for x in range(-1, 2):
        for y in range(-1, 2):
            ents.append(Entity(pos=Coord(x, y, 0), type=EntType.GROUND,
                               id=100 + 10 * (y + 1) + x + 1, tileset=1))
    # The wall occupies the north column. Its cells *are* the ladder, so the
    # topmost ladder cell is the top of the wall and the climb steps onto it.
    for z in range(1, height + 1):
        ents.append(Entity(pos=Coord(0, -1, z), type=EntType.LADDER, id=200 + z,
                           direction=Direction.SOUTH))
    ents.append(Entity(pos=Coord(0, 0, 1), type=EntType.PLAYER, id=1, direction=Direction.EAST))
    return GameState(entities=tuple(ents), tileset=0)


def test_climbing_resolves_to_the_top_in_one_step():
    """A climb must end somewhere the player can stand.

    An earlier version rose one level and returned, whereupon settle — which
    asks only for solid ground — found nothing beneath a player on a ladder and
    dropped it back. Nothing appeared to happen at all.
    """
    state = ladder_world(height=2)
    result = step(state, Direction.NORTH, masks={})
    assert result.moved
    assert result.state.player.pos.z > state.player.pos.z, "should have climbed"
    # Ends on top of the wall, not floating in the ladder's column.
    assert result.state.player.pos == Coord(0, -1, 3)


def test_a_climb_is_not_undone_by_gravity():
    state = ladder_world(height=3)
    after = step(state, Direction.NORTH, masks={}).state
    settled = step(after, None, masks={})
    assert settled.state.player.pos == after.player.pos


def test_climbing_needs_the_ladder_to_face_the_player():
    """LadderUpInDir requires LadderAt(pos+dir) == dir.Inverse()."""
    from ssr_env.mechanics import ladder_up_in_dir

    state = ladder_world()
    assert ladder_up_in_dir(state, Direction.NORTH, {})
    assert not ladder_up_in_dir(state, Direction.SOUTH, {})
