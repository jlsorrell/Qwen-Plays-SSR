import pytest

from ssr_env.entity import Entity
from ssr_env.state import GameState
from ssr_env.types import Coord, Direction, EntType


def make_state(**overrides) -> GameState:
    entities = (
        Entity(pos=Coord(0, 0), type=EntType.ISLAND, id=0),
        Entity(pos=Coord(1, 1), type=EntType.BBQ, id=1),
        Entity(pos=Coord(2, 2), type=EntType.PLAYER, id=2, direction=Direction.NORTH),
        Entity(pos=Coord(3, 3), type=EntType.SAUSAGE, id=3, direction=Direction.EAST),
    )
    return GameState(entities=entities, **overrides)


def test_state_key_is_hashable():
    hash(make_state().state_key())


def test_identical_states_share_a_key():
    assert make_state().state_key() == make_state().state_key()


def test_transient_rot_does_not_affect_state_key():
    """rot is mid-move bookkeeping; the game's own undo comparison ignores it."""
    base = make_state()
    rotated = base.replace_entity(
        Entity(pos=Coord(3, 3), type=EntType.SAUSAGE, id=3, direction=Direction.EAST, rot=2)
    )
    assert base.state_key() == rotated.state_key()


def test_transient_pivot_and_turndir_do_not_affect_state_key():
    base = make_state()
    fiddled = base.replace_entity(
        Entity(
            pos=Coord(3, 3),
            type=EntType.SAUSAGE,
            id=3,
            direction=Direction.EAST,
            pivot=1,
            turndir=Direction.WEST,
        )
    )
    assert base.state_key() == fiddled.state_key()


def test_cookdata_change_does_affect_state_key():
    base = make_state()
    cooked = base.replace_entity(
        Entity(pos=Coord(3, 3), type=EntType.SAUSAGE, id=3, direction=Direction.EAST, cookdata=1)
    )
    assert base.state_key() != cooked.state_key()


def test_position_change_does_affect_state_key():
    base = make_state()
    moved = base.replace_entity(
        Entity(pos=Coord(4, 3), type=EntType.SAUSAGE, id=3, direction=Direction.EAST)
    )
    assert base.state_key() != moved.state_key()


def test_direction_change_does_affect_state_key():
    base = make_state()
    turned = base.replace_entity(
        Entity(pos=Coord(3, 3), type=EntType.SAUSAGE, id=3, direction=Direction.WEST)
    )
    assert base.state_key() != turned.state_key()


def test_static_entities_are_excluded_from_state_key():
    """Island (id 0) is dynamic per `Utility.Static`; bbq (id 1) is static.

    Islands are pushable in world 6, so they must carry state identity. This
    test previously asserted the opposite and was wrong.
    """
    key = make_state().state_key()
    assert {entry[0] for entry in key} == {0, 2, 3}


def test_moving_an_island_changes_the_state_key():
    base = make_state()
    shifted = base.replace_entity(
        Entity(pos=Coord(1, 0), type=EntType.ISLAND, id=0)
    )
    assert base.state_key() != shifted.state_key()


def test_state_key_is_order_independent():
    base = make_state()
    shuffled = GameState(entities=tuple(reversed(base.entities)))
    assert base.state_key() == shuffled.state_key()


def test_player_accessor():
    assert make_state().player.id == 2


def test_player_accessor_rejects_ambiguity():
    two_players = GameState(
        entities=(
            Entity(pos=Coord(0, 0), type=EntType.PLAYER, id=1),
            Entity(pos=Coord(1, 0), type=EntType.PLAYER, id=2),
        )
    )
    with pytest.raises(ValueError, match="exactly one player"):
        _ = two_players.player


def test_by_id_raises_for_missing():
    with pytest.raises(KeyError):
        make_state().by_id(99)


def test_lost_is_false_by_default():
    assert not make_state().lost


def test_lost_reflects_reason():
    assert make_state(lost_reason="Burned").lost
