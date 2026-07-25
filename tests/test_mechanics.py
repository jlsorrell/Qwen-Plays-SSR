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
