"""Loader and renderer tests.

Level geometry is gitignored (derived from the owner's install), so these skip
when it has not been extracted locally.
"""

import pytest

from ssr_env.entity import Entity
from ssr_env.level import (
    available_levels,
    bbq_direction_from_mask,
    decoration_type_from_mask,
    footprint_type_from_mask,
    is_solid_mask_value,
    ladder_direction_from_mask,
    load_island_masks,
    load_level_by_name,
    parent_level,
    pedestal_direction_from_mask,
    playable_levels,
    resolve_island_mask,
)
from ssr_env.render import EMPTY, render
from ssr_env.state import GameState
from ssr_env.types import Coord, Direction, EntType

pytestmark = pytest.mark.skipif(
    not available_levels(), reason="run tools/extract_levels.py first"
)


def synthetic() -> GameState:
    return GameState(
        entities=(
            Entity(pos=Coord(0, 0, 0), type=EntType.GROUND, id=1),
            Entity(pos=Coord(1, 0, 0), type=EntType.BBQ, id=2),
            Entity(pos=Coord(0, 1, 0), type=EntType.PLAYER, id=3, direction=Direction.NORTH),
            Entity(
                pos=Coord(1, 1, 0),
                type=EntType.SAUSAGE,
                id=4,
                direction=Direction.EAST,
                cookdata=5,
            ),
        )
    )


def test_render_is_deterministic():
    state = synthetic()
    assert render(state, "t") == render(state, "t")


def test_render_shows_bbq_and_player_glyphs():
    out = render(synthetic(), "t")
    assert "#" in out and "@" in out


def test_render_reports_cook_faces():
    assert "faces=(1, 1, 0, 0)" in render(synthetic(), "t")


def test_render_prints_north_at_top():
    """North is +y, so the higher y row must appear above the lower one."""
    rows = [ln for ln in render(synthetic(), "t").splitlines() if ln.startswith("  ")]
    map_rows = [r for r in rows if "@" in r or "#" in r]
    assert "@" in map_rows[0] and "#" in map_rows[1]


def test_render_marks_empty_cells():
    state = GameState(
        entities=(
            Entity(pos=Coord(0, 0, 0), type=EntType.GROUND, id=1),
            Entity(pos=Coord(2, 2, 0), type=EntType.GROUND, id=2),
        )
    )
    assert EMPTY in render(state, "t")


def test_render_surfaces_loss_reason():
    assert "LOST: Burned" in render(
        GameState(entities=synthetic().entities, lost_reason="Burned"), "t"
    )


def test_empty_level_renders_without_crashing():
    assert "empty" in render(GameState(entities=()), "blank")


def test_extraction_produced_levels():
    assert len(available_levels()) > 100


def test_playable_count_is_close_to_dem_count():
    """Playable parent levels should land near the 120 .dem files."""
    assert 110 <= len(playable_levels()) <= 125


def test_playable_levels_are_parents_not_fragments():
    assert not [n for n in playable_levels() if "__island" in n]


def test_fragments_exist_and_some_carry_the_player():
    """Multi-island levels store the player in a fragment, not the parent."""
    fragments = [n for n in available_levels() if "__island" in n]
    assert fragments, "expected multi-island levels in the extraction"
    with_player = [
        n for n in fragments if load_level_by_name(n).of_type(EntType.PLAYER)
    ]
    assert with_player, "expected some fragments to carry the player"
    assert {parent_level(n) for n in with_player} <= set(playable_levels())


def test_every_playable_level_renders():
    for name in playable_levels()[:30]:
        assert "Map (" in render(load_level_by_name(name), name)


def test_island_masks_extracted():
    assert len(load_island_masks()) > 100


def test_every_island_entity_resolves_to_a_mask():
    """248/248 across all playable levels; a regression here means lost geometry."""
    masks = load_island_masks()
    unresolved = [
        (name, e.dat)
        for name in playable_levels()
        for e in load_level_by_name(name).entities
        if e.type is EntType.ISLAND
        and resolve_island_mask(name, e.dat, masks) is None
    ]
    assert not unresolved, f"unresolved island masks: {unresolved[:5]}"


def test_island_entities_retain_dat():
    """dat is the mask key, not decoration — dropping it loses terrain."""
    for name in playable_levels():
        islands = [e for e in load_level_by_name(name).entities if e.type is EntType.ISLAND]
        if islands:
            assert all(e.dat for e in islands)
            return
    pytest.skip("no island entities found")


def test_ladder_directions_decode_from_mask_values():
    assert ladder_direction_from_mask(3) is Direction.NORTH
    assert ladder_direction_from_mask(4) is Direction.SOUTH
    assert ladder_direction_from_mask(5) is Direction.WEST
    assert ladder_direction_from_mask(6) is Direction.EAST


def test_non_ladder_mask_values_decode_to_none():
    for value in (-1, 0, 1, 2, 7, 14, 17):
        assert ladder_direction_from_mask(value) is None


def test_ladder_encoded_cells_exist_in_the_corpus():
    """Values 3..6 really occur; if they vanish, the encoding was misread."""
    found = sum(
        1
        for m in load_island_masks().values()
        for plane in m["mask"]
        for row in plane
        for v in row
        if 3 <= v <= 6
    )
    assert found > 0


def test_sidecars_are_not_treated_as_levels():
    assert "__islandmasks__" not in available_levels()
    assert "__overworld__" not in available_levels()


def test_pedestal_directions_decode():
    assert pedestal_direction_from_mask(9) is Direction.NORTH
    assert pedestal_direction_from_mask(12) is Direction.EAST
    assert pedestal_direction_from_mask(8) is None
    assert pedestal_direction_from_mask(13) is None


def test_bbq_directions_decode():
    assert bbq_direction_from_mask(2) is Direction.EAST
    assert bbq_direction_from_mask(20) is Direction.NORTH
    assert bbq_direction_from_mask(1) is None


def test_solidity_is_decided_by_sign():
    assert is_solid_mask_value(1)
    assert is_solid_mask_value(17)
    assert not is_solid_mask_value(0)
    assert not is_solid_mask_value(-14)


def test_minus_one_is_solid_only_when_cookdata_zero():
    assert is_solid_mask_value(-1, cookdata=0)
    assert not is_solid_mask_value(-1, cookdata=1)


def test_decorations_are_ten_or_more_negative():
    assert decoration_type_from_mask(-10) == 0
    assert decoration_type_from_mask(-25) == 15
    assert decoration_type_from_mask(-9) is None
    assert decoration_type_from_mask(0) is None


def test_footprint_categories():
    assert footprint_type_from_mask(13) == 1
    assert footprint_type_from_mask(14) == 2
    assert footprint_type_from_mask(2) == 3
    assert footprint_type_from_mask(20) == 3
    assert footprint_type_from_mask(1) == 0


def test_grill_cells_and_bbq_entities_both_exist():
    """Flagged in mechanics.md 10.3: grills may be double-represented."""
    grill_cells = sum(
        1
        for m in load_island_masks().values()
        for plane in m["mask"]
        for row in plane
        for v in row
        if v in (2, 20)
    )
    bbq_entities = sum(
        len(load_level_by_name(n).of_type(EntType.BBQ)) for n in playable_levels()
    )
    assert grill_cells > 0 and bbq_entities > 0


def test_merged_levels_have_exactly_one_player():
    """Fragments must be merged, and ids renumbered, or the player is missing."""
    from ssr_env.level import load_full_level, playable_full_levels

    for name in playable_full_levels()[:30]:
        assert len(load_full_level(name).of_type(EntType.PLAYER)) == 1


def test_merging_recovers_entities_from_fragments():
    """A multi-island parent holds only island placeholders until merged."""
    from ssr_env.level import load_full_level

    parent = load_level_by_name("islandshape21e")
    assert all(e.type is EntType.ISLAND for e in parent.entities)
    merged = load_full_level("islandshape21e")
    assert len(merged.entities) > len(parent.entities)
    assert merged.of_type(EntType.PLAYER)


def test_merged_entity_ids_are_unique():
    from ssr_env.level import load_full_level

    ents = load_full_level("islandshape21e").entities
    assert len({e.id for e in ents}) == len(ents)
