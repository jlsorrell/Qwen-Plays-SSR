"""Occupancy and solidity queries — the layer movement sits on.

Ports `Entity.Extended`, `Entity.Decoration`, `Utility.Solid` and the
`EntAt`/`SolidEntAt` lookups. Island terrain resolves through the mask decoders
in `level.py`.
"""

from .entity import Entity
from .level import is_solid_mask_value, mask_value_at, resolve_island_mask
from .state import GameState
from .types import Coord, Direction, EntType

#: `Utility.Directional` — types whose `direction` field carries meaning.
DIRECTIONAL_TYPES = frozenset({EntType.PLAYER, EntType.LADDER, EntType.SAUSAGE})

#: `Utility.SubjectToPassiveForces` — types the passive force sweep can move.
PASSIVE_FORCE_TYPES = frozenset({EntType.SAUSAGE, EntType.FORK, EntType.ISLAND})

#: `Utility.NeedsGround` — types that fall when unsupported.
NEEDS_GROUND_TYPES = frozenset({EntType.PLAYER, EntType.SAUSAGE, EntType.FORK})

#: `Utility.CanHatTurn` — types that can be carried and turn with their carrier.
CAN_HAT_TURN_TYPES = frozenset({EntType.SAUSAGE, EntType.FORK})

#: Ground tilesets that make an entity decorative. See `is_decoration`.
_DECOR_TILESETS = frozenset({7, 8, 9})


def is_extended(entity: Entity, state: GameState) -> bool:
    """Whether the entity occupies two cells rather than one.

    Mirrors `Entity.Extended()`: sausages and islands always; the player only
    while the fork is still attached — once the fork detaches into its own
    `EntType.fork` entity, the player becomes a single cell.
    """
    if entity.type in (EntType.SAUSAGE, EntType.ISLAND):
        return True
    if entity.type is EntType.PLAYER:
        return not state.of_type(EntType.FORK)
    return False


def cells_of(entity: Entity, state: GameState) -> tuple[Coord, ...]:
    """Grid cells the entity occupies.

    Islands are excluded — their occupancy comes from the island mask, not from
    a cell list. Use `occupies` for a uniform test.
    """
    if entity.type is EntType.ISLAND:
        return ()
    if is_extended(entity, state) and entity.direction is not Direction.NONE:
        return (entity.pos, entity.pos + entity.direction.delta)
    return (entity.pos,)


def is_decoration(entity: Entity, level_tileset: int) -> bool:
    """Mirrors `Entity.Decoration()`.

    Only ground entities are ever decorative, and it depends on both the
    entity's own `tileset`/`tilenum` and the level-wide tileset — which is why
    neither field can be discarded as cosmetic.
    """
    if entity.type is not EntType.GROUND:
        return False
    if level_tileset == 4:
        if entity.tileset in _DECOR_TILESETS and 4 <= entity.tilenum <= 7:
            return False
        if entity.tileset == 9 and entity.tilenum < 4:
            return False
    if level_tileset == 0 and entity.tileset in (5, 13) and entity.tilenum >= 6:
        return True
    return entity.tileset in _DECOR_TILESETS


def is_solid(entity: Entity, level_tileset: int) -> bool:
    """Mirrors `Utility.Solid`: solid is simply "not a decoration"."""
    return not is_decoration(entity, level_tileset)


def occupies(
    entity: Entity,
    pos: Coord,
    state: GameState,
    masks: dict[str, dict] | None = None,
    level_name: str = "",
) -> bool:
    """Whether `entity` occupies `pos`. Mirrors `Entity.At`.

    Islands resolve through their mask; everything else through `cells_of`.
    """
    if entity.type is EntType.ISLAND:
        if not masks:
            return False
        mask = resolve_island_mask(level_name, entity.dat, masks)
        if mask is None:
            return False
        return is_solid_mask_value(
            mask_value_at(mask, entity.pos, pos), entity.cookdata
        )
    return pos in cells_of(entity, state)


def ent_at(
    state: GameState,
    pos: Coord,
    masks: dict[str, dict] | None = None,
    level_name: str = "",
    ignore_laden_forks: bool = False,
) -> Entity | None:
    """First entity occupying `pos`, dynamic entities before static.

    Mirrors `GameState.EntAt`, which searches the dynamic spatial hash first and
    falls back to `StaticEntAt`. Order matters: a sausage resting on ground must
    be found before the ground.
    """
    from .state import dynamic_entities, static_index_of

    for entity in dynamic_entities(state):
        if ignore_laden_forks and entity.type is EntType.FORK:
            continue
        if occupies(entity, pos, state, masks, level_name):
            return entity

    # Statics, including island-covered cells, come from the cached index.
    return static_index_of(state, masks, level_name).get(pos)


def solid_ent_at(
    state: GameState,
    pos: Coord,
    masks: dict[str, dict] | None = None,
    level_name: str = "",
) -> bool:
    """Mirrors `GameState.SolidEntAt`: `EntAt(pos)?.Solid() ?? false`."""
    entity = ent_at(state, pos, masks, level_name)
    return entity is not None and is_solid(entity, state.tileset)


def floor_under(
    entity: Entity,
    state: GameState,
    masks: dict[str, dict] | None = None,
    level_name: str = "",
) -> Entity | None:
    """The entity directly beneath, which is what an entity stands on."""
    return ent_at(state, entity.pos + Direction.DOWN.delta, masks, level_name)


def border_cells(entity: Entity, state: GameState, direction: Direction) -> tuple[Coord, ...]:
    """Cells through which `entity` pushes when moved in `direction`.

    Mirrors `Entity.Border`. For a one-cell entity it is simply the next cell.
    For an extended entity it depends on how the push relates to its own axis:

    - pushed along its facing: the far end, `pos + 2*d`
    - pushed against its facing: the near end, `pos + d`
    - pushed perpendicular: both cells, `pos + d` and `pos + direction + d`

    Diagonal pushes are not valid here; the game logs an error for them.
    """
    if direction.is_diagonal:
        raise ValueError(f"border is undefined for diagonal {direction.name}")
    if not is_extended(entity, state):
        return (entity.pos + direction.delta,)
    if entity.direction is direction:
        d = direction.delta
        return (Coord(entity.pos.x + 2 * d.x, entity.pos.y + 2 * d.y, entity.pos.z + 2 * d.z),)
    if entity.direction is direction.inverse():
        return (entity.pos + direction.delta,)
    return (
        entity.pos + direction.delta,
        entity.pos + entity.direction.delta + direction.delta,
    )


def under(
    entity: Entity,
    state: GameState,
    masks: dict[str, dict] | None = None,
    level_name: str = "",
) -> list[Entity]:
    """Entities supporting `entity`. Mirrors `GameState.Under`.

    An extended entity is supported at both of its cells; duplicates are dropped.
    """
    found: list[Entity] = []
    floor = ent_at(state, entity.pos + Direction.DOWN.delta, masks, level_name)
    if floor is not None:
        found.append(floor)
    if is_extended(entity, state) and entity.direction is not Direction.NONE:
        other = ent_at(
            state,
            entity.pos + entity.direction.delta + Direction.DOWN.delta,
            masks,
            level_name,
        )
        if other is not None and all(f.id != other.id for f in found):
            found.append(other)
    return found
