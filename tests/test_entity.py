import pytest

from ssr_env.entity import (
    MAX_COOKDATA,
    Entity,
    pack_cookdata,
    unpack_cookdata,
)
from ssr_env.types import (
    DYNAMIC_TYPES,
    INPUT_DIRECTIONS,
    STATIC_TYPES,
    Coord,
    Direction,
    EntType,
)


def test_north_is_positive_y():
    """The game's Coord.North is (0, 1): y increases northward, not southward."""
    assert Direction.NORTH.delta == Coord(0, 1, 0)
    assert Direction.SOUTH.delta == Coord(0, -1, 0)


def test_east_west_deltas():
    assert Direction.EAST.delta == Coord(1, 0, 0)
    assert Direction.WEST.delta == Coord(-1, 0, 0)


def test_vertical_deltas():
    assert Direction.UP.delta == Coord(0, 0, 1)
    assert Direction.DOWN.delta == Coord(0, 0, -1)


def test_direction_has_eleven_members():
    assert len(Direction) == 11


def test_input_directions_are_the_four_cardinals():
    assert set(INPUT_DIRECTIONS) == {
        Direction.NORTH,
        Direction.SOUTH,
        Direction.EAST,
        Direction.WEST,
    }


def test_direction_ordinals_match_the_game():
    assert (Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST) == (0, 1, 2, 3)


def test_enttype_has_nine_members():
    assert len(EntType) == 9


def test_static_and_dynamic_partition_enttype():
    assert STATIC_TYPES | DYNAMIC_TYPES == set(EntType)
    assert not (STATIC_TYPES & DYNAMIC_TYPES)


def test_cookdata_roundtrips_over_full_range():
    for value in range(MAX_COOKDATA + 1):
        assert pack_cookdata(unpack_cookdata(value)) == value


def test_cookdata_is_base_four_little_endian():
    assert unpack_cookdata(0) == (0, 0, 0, 0)
    assert unpack_cookdata(1) == (1, 0, 0, 0)
    assert unpack_cookdata(4) == (0, 1, 0, 0)
    assert unpack_cookdata(64) == (0, 0, 0, 1)
    assert unpack_cookdata(MAX_COOKDATA) == (3, 3, 3, 3)


def test_cookdata_range_is_256_not_16():
    """Guards the spec correction: four states per face, not two."""
    assert MAX_COOKDATA == 255


def test_rejects_out_of_range_cookdata():
    with pytest.raises(ValueError, match="outside"):
        unpack_cookdata(256)


def test_rejects_bad_face_values():
    with pytest.raises(ValueError, match="face values"):
        pack_cookdata((0, 0, 0, 4))


def test_entity_faces_property():
    e = Entity(pos=Coord(0, 0), type=EntType.SAUSAGE, id=1, cookdata=6)
    assert e.faces == (2, 1, 0, 0)


def test_with_faces_is_immutable():
    e = Entity(pos=Coord(0, 0), type=EntType.SAUSAGE, id=1)
    updated = e.with_faces((1, 0, 0, 0))
    assert e.cookdata == 0 and updated.cookdata == 1
