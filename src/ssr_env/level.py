"""Load extracted level geometry into a GameState.

Input is the JSON emitted by `tools/extract_levels.py`, one file per level.
Cosmetic fields (`tilenum`, `tileset`, `dat`) are dropped here — they affect
appearance and overworld linkage, not mechanics.
"""

import json
from pathlib import Path

from .entity import Entity
from .state import GameState
from .types import Coord, Direction, EntType

LEVELS_DIR = Path(__file__).parent.parent.parent / "data" / "levels"


def entity_from_raw(raw: dict) -> Entity:
    return Entity(
        pos=Coord(raw["x"], raw["y"], raw["z"]),
        type=EntType(raw["type"]),
        id=raw["id"],
        direction=Direction(raw["direction"]),
        cookdata=raw["cookdata"],
        stuckto=raw["stuckto"],
        rot=raw["rot"],
        turndir=Direction(raw["turndir"]),
        pivot=raw["pivot"],
    )


def load_level(path: Path) -> GameState:
    raw = json.loads(Path(path).read_text())
    return GameState(entities=tuple(entity_from_raw(e) for e in raw["entities"]))


def load_level_by_name(name: str, levels_dir: Path = LEVELS_DIR) -> GameState:
    return load_level(Path(levels_dir) / f"{name}.json")


def available_levels(levels_dir: Path = LEVELS_DIR) -> list[str]:
    """Level names with extracted geometry, excluding the overworld pseudo-level."""
    directory = Path(levels_dir)
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("*.json") if p.stem != "__overworld__")


#: Multi-island levels serialise each island separately as `<parent>__islandN`.
FRAGMENT_MARKER = "__island"


def parent_level(name: str) -> str:
    """`islandshape26y__island2` -> `islandshape26y`; other names unchanged."""
    return name.split(FRAGMENT_MARKER)[0]


def playable_levels(levels_dir: Path = LEVELS_DIR) -> list[str]:
    """Candidate levels for a `.dem` replay, as parent-level names.

    A level is playable if it, or any of its island fragments, contains exactly
    one player. Multi-island levels store the player inside a fragment rather
    than the parent, so fragments are grouped under their parent instead of being
    excluded — 22 of them carry the player.

    A sausage is deliberately *not* required: some levels have theirs issued by
    the overworld on entry (`IssueWorldSausages`) and serialise with none.
    """
    parents: set[str] = set()
    for name in available_levels(levels_dir):
        if len(load_level_by_name(name, levels_dir).of_type(EntType.PLAYER)) == 1:
            parents.add(parent_level(name))
    return sorted(parents)
