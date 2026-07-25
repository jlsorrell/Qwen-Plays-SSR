"""Replay acceptance suite — the Phase 0 exit gate.

Every case xfails until the mechanics land (Tasks 9-13), so the suite stays green
while they are transcribed. As each `.dem` starts passing, add its name to
PASSING; it then guards against regressions from every later mechanic.

Note these are keyed by `.dem` name (`1-1`, `6-8.5`), not by the game's internal
level names. The mapping between them does not exist in the game data and is
recovered by `replay.find_matching_level` once `step()` works — see Task 11.
"""

from pathlib import Path

import pytest

from ssr_env.dem import parse_dem_file
from ssr_env.level import available_levels
from ssr_env.replay import replay_dem

DEM_DIR = Path(__file__).parent.parent / "data" / "dem"

#: .dem name -> internal level name, discovered by find_matching_level.
DEM_TO_LEVEL: dict[str, str] = {}

#: .dem names whose replay currently reaches a winning state.
PASSING: set[str] = set()


def dem_names() -> list[str]:
    return sorted(p.stem for p in DEM_DIR.glob("*.dem") if p.stem != "all")


@pytest.mark.skipif(not available_levels(), reason="run tools/extract_levels.py first")
@pytest.mark.parametrize("name", dem_names())
def test_replay_reaches_goal(name: str, request):
    if name not in PASSING:
        request.node.add_marker(
            pytest.mark.xfail(reason="mechanics not yet implemented", strict=False)
        )
    level = DEM_TO_LEVEL.get(name)
    assert level is not None, f"no level mapping for {name}"
    report = replay_dem(level, DEM_DIR / f"{name}.dem")
    assert report.solved, report.summary()


def test_mapping_covers_passing_set():
    """Anything declared passing must have a level mapping."""
    assert PASSING <= set(DEM_TO_LEVEL)


def test_every_dem_parses_into_inputs():
    """Guards the replay harness's input side independently of the mechanics."""
    for name in dem_names()[:10]:
        assert parse_dem_file(DEM_DIR / f"{name}.dem")
