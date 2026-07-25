"""Loader and renderer tests.

Level geometry is gitignored (derived from the owner's install), so these skip
when it has not been extracted locally.
"""

import pytest

from ssr_env.entity import Entity
from ssr_env.level import (
    available_levels,
    load_level_by_name,
    parent_level,
    playable_levels,
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
