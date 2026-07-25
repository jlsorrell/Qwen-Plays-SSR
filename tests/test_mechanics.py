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


def test_walking_off_the_edge_raises_falling():
    state = flat(player_at=(0, 0), facing=Direction.SOUTH)
    with pytest.raises(UnimplementedMechanic, match="falling"):
        step(state, Direction.SOUTH)


def test_walking_into_a_sausage_raises_push():
    sausage = Entity(pos=Coord(2, 4, 1), type=EntType.SAUSAGE, id=50,
                     direction=Direction.EAST)
    state = flat(extra=(sausage,))
    with pytest.raises(UnimplementedMechanic, match="push"):
        step(state, Direction.NORTH)


def test_unimplemented_mechanic_names_itself():
    state = flat(player_at=(0, 0), facing=Direction.SOUTH)
    try:
        step(state, Direction.SOUTH)
    except UnimplementedMechanic as exc:
        assert exc.mechanic == "falling"


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


def test_perpendicular_push_raises_roll():
    """Rolling needs the face permutation, which is not yet established.

    Player at (2,1) facing North puts its fork at (2,2); moving North sends the
    fork into (2,3), where an East-West sausage takes a perpendicular push.
    """
    state = flat(player_at=(2, 1), facing=Direction.NORTH,
                 extra=(sausage(2, 3, facing=Direction.EAST),))
    with pytest.raises(UnimplementedMechanic, match="roll"):
        step(state, Direction.NORTH)


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


def test_turn_push_perpendicular_raises_roll():
    """A swept sausage lying across the push direction would have to roll."""
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH,
                 extra=(sausage(3, 3, facing=Direction.NORTH),))
    with pytest.raises(UnimplementedMechanic, match="roll"):
        step(state, Direction.EAST)


def test_turn_into_a_blocked_fork_raises_pivot_turn():
    """Blocked turns fall back to TryPivotTurn, which is not transcribed.

    A barrier blocks the fork's destination without being pushable, so this
    reaches the collision check rather than raising `roll` on the way.
    """
    barrier = Entity(pos=Coord(3, 2, 1), type=EntType.BARRIER, id=60)
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH,
                 extra=(barrier,))
    with pytest.raises(UnimplementedMechanic, match="pivot-turn"):
        step(state, Direction.EAST)


def test_turning_with_a_clear_corner_still_works():
    state = flat(width=8, height=8, player_at=(2, 2), facing=Direction.NORTH)
    assert step(state, Direction.EAST).state.player.direction is Direction.EAST
