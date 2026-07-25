"""Movement and turning on the subset implemented so far."""

import pytest

from ssr_env.entity import Entity
from ssr_env.mechanics import UnimplementedMechanic, fork_cell, step, try_move_player
from ssr_env.state import GameState
from ssr_env.types import Action, Coord, Direction, EntType


def flat(width=6, height=6, z=0, player_at=(2, 2), facing=Direction.NORTH, extra=()):
    """A flat plain of solid ground with a player on it."""
    ents = [
        Entity(pos=Coord(x, y, z), type=EntType.GROUND, id=100 + y * width + x, tileset=1)
        for x in range(width)
        for y in range(height)
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
    assert result.state.player.pos == Coord(2, 3, 1)


def test_walking_backward_moves_opposite_to_facing():
    state = flat()
    result = step(state, Direction.SOUTH)
    assert result.state.player.pos == Coord(2, 1, 1)


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
    s = Entity(pos=Coord(2, 4, 1), type=EntType.SAUSAGE, id=50,
               direction=Direction.EAST)
    state = flat(width=8, height=8, extra=(s,))
    result = step(state, Direction.NORTH)
    assert result.state.by_id(50).pos == Coord(2, 5, 1)
    assert result.state.by_id(50).rot == 1


def test_unimplemented_mechanic_names_itself():
    """Points at a mechanic that is still genuinely unimplemented."""
    island = Entity(pos=Coord(2, 2, 0), type=EntType.ISLAND, id=70, dat="island0")
    barrier = Entity(pos=Coord(3, 2, 1), type=EntType.BARRIER, id=60)
    player = Entity(pos=Coord(2, 2, 1), type=EntType.PLAYER, id=1,
                    direction=Direction.NORTH)
    masks = {"lvl__island0": {"offset": [0, 0, 0], "mask": [[[1]]]}}
    state = GameState(entities=(island, barrier, player), tileset=0)
    try:
        step(state, Direction.EAST, None, masks, "lvl")
    except UnimplementedMechanic as exc:
        assert exc.mechanic == "pivot-turn"
    else:
        raise AssertionError("expected UnimplementedMechanic")


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
    state = flat(width=8, height=8, player_at=(2, 1), facing=Direction.NORTH,
                 extra=(sausage(2, 3, facing=Direction.EAST),))
    before = state.by_id(50)
    after = step(state, Direction.NORTH).state.by_id(50)
    assert after.pos == Coord(2, 4, 1)
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


def test_pushing_a_sausage_into_a_void_raises():
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
    with pytest.raises(UnimplementedMechanic, match="push-into-fall"):
        try_push(state, s, Direction.EAST)


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
    assert border_cells(p, st, Direction.NORTH) == (Coord(0, 1, 0),)


def test_border_perpendicular_covers_both_cells():
    from ssr_env.geometry import border_cells

    s = sausage(0, 0, z=0, facing=Direction.EAST)
    st = GameState(entities=(s,))
    assert border_cells(s, st, Direction.NORTH) == (Coord(0, 1, 0), Coord(1, 1, 0))


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
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH,
                 extra=(sausage(3, 3, facing=Direction.EAST),))
    result = step(state, Direction.EAST)
    assert result.state.player.direction is Direction.EAST
    assert result.state.by_id(50).pos == Coord(4, 3, 1)


def test_turn_push_can_roll_the_swept_sausage():
    """A swept sausage lying across the push direction rolls."""
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH,
                 extra=(sausage(3, 3, facing=Direction.NORTH),))
    result = step(state, Direction.EAST)
    assert result.state.by_id(50).pos == Coord(4, 3, 1)
    assert result.state.by_id(50).rot == 1


def test_collided_turn_on_an_island_raises_pivot_turn():
    """On an island, a collided turn falls back to TryPivotTurn — untranscribed."""
    island = Entity(pos=Coord(2, 2, 0), type=EntType.ISLAND, id=70, dat="island0")
    barrier = Entity(pos=Coord(3, 2, 1), type=EntType.BARRIER, id=60)
    player = Entity(pos=Coord(2, 2, 1), type=EntType.PLAYER, id=1,
                    direction=Direction.NORTH)
    masks = {"lvl__island0": {"offset": [0, 0, 0], "mask": [[[1]]]}}
    state = GameState(entities=(island, barrier, player), tileset=0)
    with pytest.raises(UnimplementedMechanic, match="pivot-turn"):
        step(state, Direction.EAST, None, masks, "lvl")


def test_turning_with_a_clear_corner_still_works():
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH)
    assert step(state, Direction.EAST).state.player.direction is Direction.EAST


def test_collided_turn_off_an_island_is_a_failed_move_not_a_pivot():
    """TryPivotTurn returns false unless the player stands on an island."""
    barrier = Entity(pos=Coord(3, 2, 1), type=EntType.BARRIER, id=60)
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


def test_walking_off_an_edge_drowns_the_player():
    """Falling below z=-2 is fatal; the threshold matches GameState.Lost()."""
    state = flat(player_at=(0, 0), facing=Direction.SOUTH)
    result = step(state, Direction.SOUTH)
    assert result.lost and result.state.lost_reason == "Drowned"


def test_a_supported_move_does_not_fall():
    result = step(flat(), Direction.NORTH)
    assert not result.lost
    assert result.state.player.pos == Coord(2, 3, 1)


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
