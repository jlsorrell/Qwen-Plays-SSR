"""Game state and its canonical identity.

The state key mirrors the game's own `GameState.BakStruct` equality check, which
compares snapshots on exactly `pos`, `direction` and `cookdata` per entity. That
is the identity relation the game uses for undo, so Phase 1's reachable-state
enumeration inherits a ground-truth definition of "same state" rather than a
guessed one.
"""

from dataclasses import dataclass, replace

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
        return tuple(e for e in self.entities if e.type is entity_type)

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
        return replace(
            self,
            entities=tuple(entity if e.id == entity.id else e for e in self.entities),
        )

    @property
    def lost(self) -> bool:
        return bool(self.lost_reason)
