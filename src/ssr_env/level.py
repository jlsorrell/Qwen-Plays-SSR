"""Load extracted level geometry into a GameState.

Input is the JSON emitted by `tools/extract_levels.py`, one file per level.
`tilenum` and `tileset` are dropped — they affect appearance only.

`dat` is **kept**. For `EntType.ISLAND` it names the island and is the key into
the island-mask table, and masks carry both the chunk's shape and its ladder
encoding (`GameState.LadderAt` reads mask values 3..6 as ladder directions).
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
        dat=raw.get("dat", ""),
    )


def load_island_masks(levels_dir: Path = LEVELS_DIR) -> dict[str, dict]:
    """Island masks by name: `{"offset": [x,y,z], "mask": [[[int]]]}`.

    Empty when the extractor has not been run. Mask values 3..6 encode ladder
    directions (North/South/West/East); other values are not yet decoded.
    """
    path = Path(levels_dir) / "__islandmasks__.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def island_mask_key(level_name: str, dat: str) -> str:
    """Mask table key for an island entity's `dat` within a given level.

    Island `dat` is level-local (`island0`, `island1`, ...) while the mask table
    is keyed globally. Secondary islands key as `<level>__<dat>`; the primary
    island (`island0`) keys as the level name itself. Verified: this resolves
    248/248 island entities across all playable levels.
    """
    return f"{level_name}__{dat}"


def resolve_island_mask(
    level_name: str, dat: str, masks: dict[str, dict]
) -> dict | None:
    key = island_mask_key(level_name, dat)
    return masks.get(key) or masks.get(level_name)


def mask_value_at(mask: dict, entity_pos: Coord, pos: Coord) -> int:
    """Mask value at a world position, or 0 outside the mask.

    Mirrors `Entity.IslandMaskVal`: the lookup is in island-local coordinates,
    `pos - entity.pos - mask.offset`.
    """
    ox, oy, oz = mask["offset"]
    lx, ly, lz = pos.x - entity_pos.x - ox, pos.y - entity_pos.y - oy, pos.z - entity_pos.z - oz
    grid = mask["mask"]
    if 0 <= lx < len(grid) and 0 <= ly < len(grid[0]) and 0 <= lz < len(grid[0][0]):
        return grid[lx][ly][lz]
    return 0


def ladder_direction_from_mask(value: int) -> Direction | None:
    """Mask values 3..6 encode ladder directions; anything else is not a ladder.

    Mirrors `GameState.LadderAt`, which returns `(Direction)(value - 3)` —
    North, South, West, East in the game's ordinal order.
    """
    return Direction(value - 3) if 3 <= value <= 6 else None


def pedestal_direction_from_mask(value: int) -> Direction | None:
    """Mask values 9..12 encode pedestal directions. Mirrors `GameState.PedastalAt`."""
    return Direction(value - 9) if 9 <= value <= 12 else None


def bbq_direction_from_mask(value: int) -> Direction | None:
    """Mask value 2 is a grill facing East, 20 a grill facing North.

    Mirrors `GameState.BBQAt` (`value == 2 or value == 20`) and `BBQAtDir`.
    """
    if value == 2:
        return Direction.EAST
    if value == 20:
        return Direction.NORTH
    return None


def decoration_type_from_mask(value: int) -> int | None:
    """Mask values <= -10 are decorations of type `-10 - value`.

    Mirrors `GameState.DecorationAt`. Decorations are cosmetic and are excluded
    from force propagation (`ApplyForce` skips `Decoration()` entities).
    """
    return -10 - value if value <= -10 else None


def is_solid_mask_value(value: int, cookdata: int = 0) -> bool:
    """Whether an island mask cell is solid.

    Mirrors `Entity.IslandAt`: positive values are solid. When the island
    entity's `cookdata` is 0 the value -1 also counts as solid — an exception
    whose purpose is not yet established (see §13 of docs/mechanics.md).
    """
    return value > 0 or (cookdata == 0 and value == -1)


def footprint_type_from_mask(value: int) -> int:
    """Surface category used for footstep effects. Mirrors `GameState.FootprintTypeAt`.

    Category 3 is the grill surface, which `CalcBBQAshSteps` keys on.
    """
    if value == 13:
        return 1
    if value == 14:
        return 2
    if value in (2, 20):
        return 3
    return 0


def load_level(path: Path) -> GameState:
    raw = json.loads(Path(path).read_text())
    return GameState(entities=tuple(entity_from_raw(e) for e in raw["entities"]))


def load_level_by_name(name: str, levels_dir: Path = LEVELS_DIR) -> GameState:
    return load_level(Path(levels_dir) / f"{name}.json")


def available_levels(levels_dir: Path = LEVELS_DIR) -> list[str]:
    """Level names with extracted geometry.

    Names wrapped in double underscores are extractor sidecars, not levels:
    `__overworld__` and `__islandmasks__`.
    """
    directory = Path(levels_dir)
    if not directory.is_dir():
        return []
    return sorted(
        p.stem
        for p in directory.glob("*.json")
        if not (p.stem.startswith("__") and p.stem.endswith("__"))
    )


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
