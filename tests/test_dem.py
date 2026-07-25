from pathlib import Path

import pytest

from ssr_env.dem import parse_dem, parse_dem_file
from ssr_env.types import Action, Direction

DEM_DIR = Path(__file__).parent.parent / "data" / "dem"


def test_parses_directions():
    assert parse_dem("North\nSouth\nEast\nWest\n") == [
        Direction.NORTH,
        Direction.SOUTH,
        Direction.EAST,
        Direction.WEST,
    ]


def test_parses_undo():
    assert parse_dem("North\nUndo\n") == [Direction.NORTH, Action.UNDO]


def test_ignores_blank_lines():
    assert parse_dem("North\n\n  \nSouth\n") == [Direction.NORTH, Direction.SOUTH]


def test_rejects_unknown_token():
    with pytest.raises(ValueError, match="Sideways"):
        parse_dem("Sideways\n")


def test_error_reports_line_number():
    with pytest.raises(ValueError, match="line 3"):
        parse_dem("North\nSouth\nWobble\n")


def test_level_1_1_length():
    assert len(parse_dem_file(DEM_DIR / "1-1.dem")) == 76


def test_level_5_1_contains_undo():
    assert Action.UNDO in parse_dem_file(DEM_DIR / "5-1.dem")


def test_direction_deltas_are_opposite_in_pairs():
    assert Direction.NORTH.delta == (-Direction.SOUTH.delta[0], -Direction.SOUTH.delta[1])
    assert Direction.EAST.delta == (-Direction.WEST.delta[0], -Direction.WEST.delta[1])


@pytest.mark.parametrize(
    "path",
    sorted(p for p in DEM_DIR.glob("*.dem") if p.stem != "all"),
    ids=lambda p: p.stem,
)
def test_every_level_dem_parses(path: Path):
    assert len(parse_dem_file(path)) > 0
