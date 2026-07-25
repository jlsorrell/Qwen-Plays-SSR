"""Occupancy and solidity."""

import pytest

from ssr_env.entity import Entity
from ssr_env.geometry import (
    cells_of,
    ent_at,
    floor_under,
    is_decoration,
    is_extended,
    is_solid,
    solid_ent_at,
)
from ssr_env.level import available_levels, load_island_masks, load_level_by_name, playable_levels
from ssr_env.state import GameState
from ssr_env.types import Coord, Direction, EntType


def ground(x, y, z=0, ident=1, tileset=0, tilenum=0):
    return Entity(pos=Coord(x, y, z), type=EntType.GROUND, id=ident,
                  tileset=tileset, tilenum=tilenum)


def test_sausage_is_always_extended():
    s = Entity(pos=Coord(0, 0), type=EntType.SAUSAGE, id=1, direction=Direction.EAST)
    assert is_extended(s, GameState(entities=(s,)))


def test_player_is_extended_only_while_the_fork_is_attached():
    p = Entity(pos=Coord(0, 0), type=EntType.PLAYER, id=1, direction=Direction.NORTH)
    assert is_extended(p, GameState(entities=(p,)))
    fork = Entity(pos=Coord(5, 5), type=EntType.FORK, id=2)
    assert not is_extended(p, GameState(entities=(p, fork)))


def test_ground_is_never_extended():
    g = ground(0, 0)
    assert not is_extended(g, GameState(entities=(g,)))


def test_extended_entity_occupies_two_cells():
    s = Entity(pos=Coord(2, 2), type=EntType.SAUSAGE, id=1, direction=Direction.NORTH)
    assert cells_of(s, GameState(entities=(s,))) == (Coord(2, 2), Coord(2, 3, 0))


def test_unextended_entity_occupies_one_cell():
    g = ground(2, 2)
    assert cells_of(g, GameState(entities=(g,))) == (Coord(2, 2),)


def test_islands_have_no_cell_list():
    i = Entity(pos=Coord(0, 0), type=EntType.ISLAND, id=1, dat="island0")
    assert cells_of(i, GameState(entities=(i,))) == ()


def test_non_ground_is_never_decoration():
    s = Entity(pos=Coord(0, 0), type=EntType.SAUSAGE, id=1, tileset=7)
    assert not is_decoration(s, level_tileset=0)


def test_decorative_tilesets_on_ground():
    for ts in (7, 8, 9):
        assert is_decoration(ground(0, 0, tileset=ts), level_tileset=0)
    assert not is_decoration(ground(0, 0, tileset=1), level_tileset=0)


def test_level_tileset_four_rescues_some_decorative_tilesets():
    """Under level tileset 4 these become solid rather than decorative."""
    assert not is_decoration(ground(0, 0, tileset=7, tilenum=5), level_tileset=4)
    assert not is_decoration(ground(0, 0, tileset=9, tilenum=2), level_tileset=4)


def test_level_tileset_zero_makes_some_high_tilenums_decorative():
    assert is_decoration(ground(0, 0, tileset=5, tilenum=6), level_tileset=0)
    assert not is_decoration(ground(0, 0, tileset=5, tilenum=5), level_tileset=0)


def test_solid_is_the_negation_of_decoration():
    for ts in (0, 1, 5, 7, 8, 9, 13):
        for tn in range(0, 9):
            for lvl in (0, 4):
                g = ground(0, 0, tileset=ts, tilenum=tn)
                assert is_solid(g, lvl) is not is_decoration(g, lvl)


def test_ent_at_finds_a_dynamic_entity_before_static():
    g = ground(0, 0, ident=1)
    s = Entity(pos=Coord(0, 0), type=EntType.SAUSAGE, id=2, direction=Direction.EAST)
    found = ent_at(GameState(entities=(g, s)), Coord(0, 0))
    assert found is not None and found.id == 2


def test_ent_at_returns_none_for_empty_cells():
    assert ent_at(GameState(entities=(ground(0, 0),)), Coord(9, 9)) is None


def test_solid_ent_at_is_false_over_decorations():
    g = ground(0, 0, tileset=7)
    assert not solid_ent_at(GameState(entities=(g,), tileset=0), Coord(0, 0))


def test_solid_ent_at_is_true_over_plain_ground():
    g = ground(0, 0, tileset=1)
    assert solid_ent_at(GameState(entities=(g,), tileset=0), Coord(0, 0))


def test_floor_under_finds_the_supporting_entity():
    g = ground(3, 3, z=0, ident=1)
    p = Entity(pos=Coord(3, 3, 1), type=EntType.PLAYER, id=2, direction=Direction.NORTH)
    found = floor_under(p, GameState(entities=(g, p)))
    assert found is not None and found.id == 1


@pytest.mark.skipif(not available_levels(), reason="run tools/extract_levels.py first")
def test_every_player_stands_on_something_in_every_real_level():
    """End-to-end check of the whole geometry stack against real levels.

    Entity parsing, the island-mask join rule, mask value decoding, occupancy and
    solidity all have to be correct simultaneously — any one of them wrong and
    some players float. Measured 104/104, so this asserts exactness rather than a
    threshold: a regression should fail loudly, not degrade quietly.
    """
    masks = load_island_masks()
    unsupported = [
        name
        for name in playable_levels()
        if (state := load_level_by_name(name)).of_type(EntType.PLAYER)
        and floor_under(state.of_type(EntType.PLAYER)[0], state, masks, name) is None
    ]
    assert not unsupported, f"players floating in: {unsupported[:8]}"
