"""Direction algebra, checked against the game's own lookup tables.

These are total over the enum rather than sampled: the tables are small and
exact, so there is no reason to test them partially.
"""

import pytest

from ssr_env.types import Coord, Direction

CARDINALS = (Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST)
DIAGONALS = (
    Direction.NORTHEAST,
    Direction.SOUTHWEST,
    Direction.NORTHWEST,
    Direction.SOUTHEAST,
)


@pytest.mark.parametrize("d", list(Direction))
def test_inverse_is_an_involution(d: Direction):
    assert d.inverse().inverse() is d


def test_inverse_pairs_match_the_game_table():
    assert Direction.NORTH.inverse() is Direction.SOUTH
    assert Direction.WEST.inverse() is Direction.EAST
    assert Direction.NORTHEAST.inverse() is Direction.SOUTHWEST
    assert Direction.NORTHWEST.inverse() is Direction.SOUTHEAST
    assert Direction.UP.inverse() is Direction.DOWN
    assert Direction.NONE.inverse() is Direction.NONE


@pytest.mark.parametrize("d", CARDINALS + DIAGONALS)
def test_four_clockwise_quarter_turns_return_to_start(d: Direction):
    assert d.rot_clockwise_90().rot_clockwise_90().rot_clockwise_90().rot_clockwise_90() is d


def test_clockwise_cycle_is_north_east_south_west():
    """Clockwise viewed from above, with North = +y."""
    assert Direction.NORTH.rot_clockwise_90() is Direction.EAST
    assert Direction.EAST.rot_clockwise_90() is Direction.SOUTH
    assert Direction.SOUTH.rot_clockwise_90() is Direction.WEST
    assert Direction.WEST.rot_clockwise_90() is Direction.NORTH


def test_two_quarter_turns_equal_inverse():
    for d in CARDINALS + DIAGONALS:
        assert d.rot_clockwise_90().rot_clockwise_90() is d.inverse()


@pytest.mark.parametrize("d", (Direction.NONE, Direction.UP, Direction.DOWN))
def test_rotation_leaves_non_planar_directions_alone(d: Direction):
    assert d.rot_clockwise_90() is d


def test_ortho_is_exactly_the_four_cardinals():
    assert {d for d in Direction if d.is_ortho} == set(CARDINALS)


def test_diagonal_is_exactly_the_four_diagonals():
    assert {d for d in Direction if d.is_diagonal} == set(DIAGONALS)


def test_parallel_to_is_same_or_opposite():
    assert Direction.NORTH.parallel_to(Direction.NORTH)
    assert Direction.NORTH.parallel_to(Direction.SOUTH)
    assert not Direction.NORTH.parallel_to(Direction.EAST)


def test_none_is_parallel_to_nothing_including_itself():
    assert not Direction.NONE.parallel_to(Direction.NONE)
    assert not Direction.NORTH.parallel_to(Direction.NONE)


def test_normal_to_is_perpendicular():
    assert Direction.NORTH.normal_to(Direction.EAST)
    assert Direction.NORTH.normal_to(Direction.WEST)
    assert not Direction.NORTH.normal_to(Direction.SOUTH)


def test_none_is_normal_to_nothing():
    assert not Direction.NONE.normal_to(Direction.NORTH)
    assert not Direction.NORTH.normal_to(Direction.NONE)


def test_parallel_and_normal_partition_valid_direction_pairs():
    planar = CARDINALS + DIAGONALS
    for a in planar:
        for b in planar:
            assert a.parallel_to(b) != a.normal_to(b)


def test_left_of_is_the_clockwise_quarter_turn():
    """LeftOf(a, b) asks whether b is a quarter turn clockwise from a."""
    assert Direction.NORTH.left_of(Direction.EAST)
    assert not Direction.NORTH.left_of(Direction.WEST)
    assert not Direction.NORTH.left_of(Direction.NORTH)
    assert not Direction.NORTH.left_of(Direction.SOUTH)


def test_left_of_holds_for_exactly_one_perpendicular_per_cardinal():
    for a in CARDINALS:
        assert sum(a.left_of(b) for b in CARDINALS) == 1


def test_flip_h_mirrors_east_west_and_leaves_north_south():
    assert Direction.EAST.flip_h() is Direction.WEST
    assert Direction.NORTH.flip_h() is Direction.NORTH
    assert Direction.NORTHEAST.flip_h() is Direction.NORTHWEST


def test_flip_v_mirrors_north_south_and_leaves_east_west():
    assert Direction.NORTH.flip_v() is Direction.SOUTH
    assert Direction.EAST.flip_v() is Direction.EAST
    assert Direction.NORTHEAST.flip_v() is Direction.SOUTHEAST


@pytest.mark.parametrize("d", list(Direction))
def test_flips_are_involutions(d: Direction):
    assert d.flip_h().flip_h() is d
    assert d.flip_v().flip_v() is d


def test_delta_and_inverse_are_consistent():
    for d in CARDINALS + DIAGONALS + (Direction.UP, Direction.DOWN):
        a, b = d.delta, d.inverse().delta
        assert a == Coord(-b.x, -b.y, -b.z)


def test_diagonal_deltas_are_the_sum_of_their_cardinals():
    """Stated as sums so the assertion survives a change of orientation."""
    for diag, a, b in (
        (Direction.NORTHEAST, Direction.NORTH, Direction.EAST),
        (Direction.SOUTHWEST, Direction.SOUTH, Direction.WEST),
        (Direction.NORTHWEST, Direction.NORTH, Direction.WEST),
        (Direction.SOUTHEAST, Direction.SOUTH, Direction.EAST),
    ):
        assert diag.delta == a.delta + b.delta


def test_vertical_is_exactly_up_and_down():
    assert {d for d in Direction if d.is_vertical} == {Direction.UP, Direction.DOWN}


def test_none_counts_as_horizontal():
    """Mirrors the game: Horizontal is `d <= None`, so NONE is horizontal."""
    assert Direction.NONE.is_horizontal
    assert not Direction.NONE.is_vertical


def test_vertical_and_horizontal_partition_all_directions():
    for d in Direction:
        assert d.is_vertical != d.is_horizontal


def test_rot_90_clockwise_matches_rot_clockwise_90():
    for d in CARDINALS + DIAGONALS:
        assert d.rot_90(clockwise=True) is d.rot_clockwise_90()


def test_rot_90_counter_clockwise_is_the_inverse_turn():
    assert Direction.NORTH.rot_90(clockwise=False) is Direction.WEST
    assert Direction.WEST.rot_90(clockwise=False) is Direction.SOUTH


def test_rot_90_both_ways_returns_to_start():
    for d in CARDINALS + DIAGONALS:
        assert d.rot_90(True).rot_90(False) is d


def test_rot_between_gives_the_diagonal():
    assert Direction.NORTH.rot_between(Direction.EAST) is Direction.NORTHEAST
    assert Direction.NORTH.rot_between(Direction.WEST) is Direction.NORTHWEST
    assert Direction.SOUTH.rot_between(Direction.EAST) is Direction.SOUTHEAST
    assert Direction.SOUTH.rot_between(Direction.WEST) is Direction.SOUTHWEST


def test_rot_between_is_symmetric():
    for a in CARDINALS:
        for b in CARDINALS:
            assert a.rot_between(b) == b.rot_between(a)


def test_rot_between_is_none_for_parallel_pairs():
    assert Direction.NORTH.rot_between(Direction.NORTH) is None
    assert Direction.NORTH.rot_between(Direction.SOUTH) is None


def test_rot_between_is_none_for_non_cardinals():
    assert Direction.NORTHEAST.rot_between(Direction.NORTH) is None
    assert Direction.UP.rot_between(Direction.NORTH) is None


def test_rot_between_is_defined_exactly_for_perpendicular_cardinals():
    for a in CARDINALS:
        for b in CARDINALS:
            assert (a.rot_between(b) is not None) == a.normal_to(b)
