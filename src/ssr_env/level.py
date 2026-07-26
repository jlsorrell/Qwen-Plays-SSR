"""Load extracted level geometry into a GameState.

Input is the JSON emitted by `tools/extract_levels.py`, one file per level.

Nothing here is dropped as cosmetic, because twice now a field that looked
decorative turned out to be geometry:

- `dat` on `EntType.ISLAND` is the island-mask key, and masks carry the chunk's
  shape and its ladder encoding (`GameState.LadderAt` reads values 3..6).
- `tilenum` and `tileset` feed `Entity.Decoration()`, and `Utility.Solid` is
  `!Decoration()` — so they decide whether ground can be stood on.
- The level-wide `tileset` (field 3 of the level string) feeds the same test.
"""

import json
from dataclasses import replace
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
        tilenum=raw.get("tilenum", 0),
        tileset=raw.get("tileset", 0),
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
    """Mask for an island entity.

    Tries `<level>__<dat>`, then `dat` as an already-qualified global key (the
    composite overworld rewrites island `dat` this way, since its islands come
    from many different levels), then the level name itself for `island0`.
    """
    return (
        masks.get(island_mask_key(level_name, dat))
        or masks.get(dat)
        or masks.get(level_name)
    )


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
    return GameState(
        entities=tuple(entity_from_raw(e) for e in raw["entities"]),
        tileset=raw.get("tileset", 0),
    )


def level_display_name(name: str, levels_dir: Path = LEVELS_DIR) -> str:
    """The level's in-game name, e.g. `leveltest7` -> "Sludge Coast"."""
    raw = json.loads((Path(levels_dir) / f"{name}.json").read_text())
    return raw.get("display_name", "")


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


def load_full_level(name: str, levels_dir: Path = LEVELS_DIR) -> GameState:
    """Load a level with its island fragments merged in.

    A multi-island level stores only positioned `EntType.ISLAND` placeholders in
    the parent file; the entities of each chunk live in `<parent>__<dat>` and are
    expressed in that chunk's own coordinates. Merging translates each fragment's
    entities by its placeholder's position.

    `island0` normally has no fragment file — it is pure mask terrain, and its
    mask is keyed by the parent name. That is the same fallback `resolve_island_mask`
    applies, which is why the join rule works out.

    Entity ids are renumbered across fragments, since each file numbers from its
    own sequence and collisions would break `by_id` and the state key.
    """
    directory = Path(levels_dir)
    parent = load_level(directory / f"{name}.json")
    merged: list[Entity] = list(parent.entities)

    for placeholder in parent.entities:
        if placeholder.type is not EntType.ISLAND:
            continue
        fragment_path = directory / f"{island_mask_key(name, placeholder.dat)}.json"
        if not fragment_path.is_file():
            continue  # pure mask terrain, no entities of its own
        for entity in load_level(fragment_path).entities:
            merged.append(replace(entity, pos=entity.pos + placeholder.pos))

    renumbered = tuple(replace(e, id=i) for i, e in enumerate(merged))
    state = replace(parent, entities=renumbered)
    players = state.of_type(EntType.PLAYER)
    if len(players) == 1:
        state = replace(
            state, start_pos=players[0].pos, start_direction=players[0].direction
        )
    return state


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


def playable_full_levels(levels_dir: Path = LEVELS_DIR) -> list[str]:
    """Playable levels that merge to exactly one player — the replay candidates."""
    return [
        name
        for name in playable_levels(levels_dir)
        if len(load_full_level(name, levels_dir).of_type(EntType.PLAYER)) == 1
    ]


def load_overworld_meta(levels_dir: Path = LEVELS_DIR) -> dict:
    """Overworld layout: island offsets, per-level start poses, temple grouping."""
    path = Path(levels_dir) / "__overworld_meta__.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def load_overworld(levels_dir: Path = LEVELS_DIR) -> GameState:
    """The overworld, built the way `MetaGameState.RegenIslands` builds it.

    The overworld is **not** a merge of every level's contents. `RegenIslands`
    discards and rebuilds it as exactly one `EntType.ISLAND` entity per level,
    positioned at that level's entry in `offsets`, with `dat` set to the level
    name. All walkable terrain comes from the island masks, keyed by that name.

    Two consequences, both confirmed against the real game
    (docs/differential-test-001-results.md):

    - **No sausages in the overworld.** They are issued on entering a level
      (`IssueWorldSausages`) and despawned on leaving.
    - Island entities sit at `offsets[name]` **directly**. An earlier version
      placed each level's own island entity at its level-local position *plus*
      the offset, double-shifting the terrain and leaving holes in the surface.

    The player comes from the level named `start`, offset into overworld space.
    """
    meta = load_overworld_meta(levels_dir)
    offsets = meta.get("offsets", {})
    masks = load_island_masks(levels_dir)

    entities: list[Entity] = [
        Entity(
            pos=Coord(*offsets[name]),
            type=EntType.ISLAND,
            id=i,
            direction=Direction.NONE,
            dat=name,
        )
        for i, name in enumerate(sorted(offsets))
        if name in masks
    ]

    start_path = Path(levels_dir) / "start.json"
    if start_path.is_file() and "start" in offsets:
        shift = Coord(*offsets["start"])
        for e in load_level(start_path).entities:
            if e.type is EntType.PLAYER:
                entities.append(replace(e, id=len(entities), pos=e.pos + shift))
                break

    state = GameState(entities=tuple(entities), tileset=0)
    players = state.of_type(EntType.PLAYER)
    if players:
        state = replace(
            state, start_pos=players[0].pos, start_direction=players[0].direction
        )
    return state
