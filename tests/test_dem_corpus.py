from pathlib import Path

import pytest

DEM_DIR = Path(__file__).parent.parent / "data" / "dem"
VALID_TOKENS = {"North", "South", "East", "West", "Undo"}

# all.dem is the concatenation of every level's inputs, used by the SSRDecompile
# injector to drive one continuous session. It is not a level and has no geometry.
AGGREGATE = "all"


def level_dems() -> list[Path]:
    return sorted(p for p in DEM_DIR.glob("*.dem") if p.stem != AGGREGATE)


def test_corpus_present():
    assert len(list(DEM_DIR.glob("*.dem"))) == 121


def test_level_count_excludes_aggregate():
    assert len(level_dems()) == 120


def test_aggregate_is_longer_than_any_level():
    aggregate = len((DEM_DIR / "all.dem").read_text().splitlines())
    longest = max(len(p.read_text().splitlines()) for p in level_dems())
    assert aggregate > longest


@pytest.mark.parametrize("path", level_dems(), ids=lambda p: p.stem)
def test_only_known_tokens(path: Path):
    tokens = {line.strip() for line in path.read_text().splitlines() if line.strip()}
    assert tokens <= VALID_TOKENS, f"unexpected tokens: {tokens - VALID_TOKENS}"


def test_all_six_worlds_present():
    worlds = {p.stem.split("-")[0] for p in level_dems()}
    assert worlds == {"1", "2", "3", "4", "5", "6"}


def test_half_levels_parse_as_stems():
    """World 6 contains levels named e.g. '6-8.5'; Path.stem must keep the '.5'."""
    assert (DEM_DIR / "6-8.5.dem").stem == "6-8.5"
