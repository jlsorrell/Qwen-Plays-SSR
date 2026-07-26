"""Game state and its canonical identity.

The state key mirrors the game's own `GameState.BakStruct` equality check, which
compares snapshots on exactly `pos`, `direction` and `cookdata` per entity. That
is the identity relation the game uses for undo, so Phase 1's reachable-state
enumeration inherits a ground-truth definition of "same state" rather than a
guessed one.
"""

from dataclasses import dataclass, field, replace

from .entity import Entity
from .types import DYNAMIC_TYPES, Coord, Direction, EntType

#: One dynamic entity's contribution to the canonical state key:
#: (id, pos, direction, cookdata, rot).
EntityKey = tuple[int, Coord, Direction, int, int]

StateKey = tuple[EntityKey, ...]


@dataclass(frozen=True, slots=True)
class GameState:
    entities: tuple[Entity, ...]
    #: Level-wide tileset, from field 3 of the level string. Feeds
    #: `Entity.Decoration()` and therefore solidity.
    tileset: int = 0
    lost_reason: str = ""
    #: Player pose at level load. The win condition requires returning here, so
    #: it must travel with the state rather than being recomputed.
    start_pos: Coord | None = None
    start_direction: Direction | None = None
    #: False once inside a level. Mirrors `GameState.overworld`.
    overworld: bool = True
    #: Name of the level currently entered. Mirrors `pushtargetlevel`.
    pushtargetlevel: str = ""
    #: Levels already completed; they no longer trigger entry.
    completed: frozenset = frozenset()
    #: Where the player must stand, and face, to leave a solved level. Normally
    #: the entry pose — but it rides a sausage if one sits beneath it (§12.16).
    exit_pos: Coord | None = None
    exit_dir: Direction | None = None
    #: `CheckOnLevelExit` requires this. A roll of the carrying sausage flips it.
    exit_up: bool = True
    #: Entity id of the sausage the exit rests on, or None.
    exit_attachment: int | None = None
    #: Lazily built cell -> static entity index, mirroring the game's
    #: `BuildStaticCaches`/`StaticEntAt`. Excluded from equality and the state
    #: key; it is a cache, not state. Needed because the composite overworld has
    #: ~17k entities and a linear scan per lookup does not survive a 16k-move
    #: replay.
    _static_index: dict | None = field(
        default=None, compare=False, repr=False, hash=False
    )
    #: Cached dynamic entities. Mirrors the game's `dynamicentities` list.
    #: Without it every lookup scans all ~17k overworld entities to find ~250.
    _dynamic: tuple | None = field(
        default=None, compare=False, repr=False, hash=False
    )

    def state_key(self) -> StateKey:
        """Canonical identity: (id, pos, direction, cookdata, rot) per dynamic entity.

        Static geometry is excluded because it cannot change.

        **`rot` is included deliberately, against the game's own precedent.**
        `GameState.BakStruct` — the game's undo comparison — checks only pos,
        direction and cookdata. That comparison is *lossy*: `DoCook` selects
        which cook face a grill touches via `e.rot` (rot 0 cooks faces 3 and 0,
        rot 1 cooks faces 2 and 1), so two sausages identical but for `rot`
        present different faces and cook differently. Copying BakStruct would
        collapse genuinely distinct states into one key and corrupt every
        distance-to-goal and dead-state label built on it.

        `turndir` and `pivot` remain excluded. `turndir` is mid-animation
        bookkeeping, and `Entity.Pivot()` folds its effect into `cookdata` by
        reversing the faces, so `pivot` carries no state the key would miss.

        See docs/mechanics.md §7.2.
        """
        return tuple(
            sorted(
                (e.id, e.pos, e.direction, e.cookdata, e.rot)
                for e in self.entities
                if e.type in DYNAMIC_TYPES
            )
        )

    def of_type(self, entity_type: EntType) -> tuple[Entity, ...]:
        """Entities of one type.

        Dynamic types read from the cached dynamic list — `is_extended` calls
        this for every occupancy check, and scanning all entities each time
        dominated overworld replay.
        """
        pool = (
            dynamic_entities(self)
            if entity_type in DYNAMIC_TYPES
            else self.entities
        )
        return tuple(e for e in pool if e.type is entity_type)

    def by_id(self, entity_id: int) -> Entity:
        for e in self.entities:
            if e.id == entity_id:
                return e
        raise KeyError(f"no entity with id {entity_id}")

    @property
    def player(self) -> Entity:
        players = self.of_type(EntType.PLAYER)
        if len(players) != 1:
            raise ValueError(f"expected exactly one player, found {len(players)}")
        return players[0]

    def replace_entity(self, entity: Entity) -> "GameState":
        """Swap one entity, carrying the static index forward where it is valid.

        Islands live in the static index, so moving one invalidates it. Every
        other dynamic entity leaves the index untouched, and rebuilding it each
        step would be prohibitive on the composite overworld.
        """
        updated = replace(
            self,
            entities=tuple(entity if e.id == entity.id else e for e in self.entities),
        )
        if entity.type is EntType.ISLAND:
            object.__setattr__(updated, "_static_index", None)
        if self._dynamic is not None:
            object.__setattr__(
                updated,
                "_dynamic",
                tuple(entity if e.id == entity.id else e for e in self._dynamic),
            )
        return updated

    @property
    def lost(self) -> bool:
        return bool(self.lost_reason)


def build_static_index(state: GameState, masks=None, level_name: str = "") -> dict:
    """Cell -> static entity, including every cell an island mask covers.

    Islands are expanded here rather than probed per lookup. The composite
    overworld has 249 island chunks, and testing each one's mask on every query
    dominated the cost; expanding once turns lookups into a dict hit.
    """
    from .level import mask_value_at, resolve_island_mask
    from .types import STATIC_TYPES

    index: dict = {}
    for entity in state.entities:
        if entity.type in STATIC_TYPES and entity.type is not EntType.ISLAND:
            index.setdefault(entity.pos, entity)

    if not masks:
        return index
    for entity in state.entities:
        if entity.type is not EntType.ISLAND:
            continue
        mask = resolve_island_mask(level_name, entity.dat, masks)
        if mask is None:
            continue
        ox, oy, oz = mask["offset"]
        grid = mask["mask"]
        for lx, plane in enumerate(grid):
            for ly, row in enumerate(plane):
                for lz, value in enumerate(row):
                    if value > 0 or (entity.cookdata == 0 and value == -1):
                        cell = Coord(
                            entity.pos.x + ox + lx,
                            entity.pos.y + oy + ly,
                            entity.pos.z + oz + lz,
                        )
                        index.setdefault(cell, entity)
    return index


def static_index_of(state: GameState, masks=None, level_name: str = "") -> dict:
    """Index for `state`, built once and cached on it."""
    if state._static_index is None:
        object.__setattr__(
            state, "_static_index", build_static_index(state, masks, level_name)
        )
    return state._static_index


def with_entities(state: GameState, entities: tuple, **kw) -> GameState:
    """Replace the whole entity tuple, dropping both caches.

    `replace()` copies `_dynamic` and `_static_index`, which is correct when only
    one entity changes but silently wrong when entities are added or removed —
    spawned sausages stayed invisible to `ent_at` because they were absent from
    a carried-over dynamic list. Any wholesale change must go through here.
    """
    updated = replace(state, entities=entities, **kw)
    object.__setattr__(updated, "_dynamic", None)
    object.__setattr__(updated, "_static_index", None)
    return updated


def dynamic_entities(state: GameState) -> tuple:
    """Dynamic entities, cached. Mirrors the game's `dynamicentities`."""
    if state._dynamic is None:
        object.__setattr__(
            state,
            "_dynamic",
            tuple(e for e in state.entities if e.type in DYNAMIC_TYPES),
        )
    return state._dynamic
