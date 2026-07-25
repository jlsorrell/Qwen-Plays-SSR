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

#: One dynamic entity's contribution to the canonical state key.
EntityKey = tuple[int, Coord, Direction, int]

StateKey = tuple[EntityKey, ...]


@dataclass(frozen=True, slots=True)
class GameState:
    entities: tuple[Entity, ...]
    #: Level-wide tileset, from field 3 of the level string. Feeds
    #: `Entity.Decoration()` and therefore solidity.
    tileset: int = 0
    lost_reason: str = ""

    def state_key(self) -> StateKey:
        """Canonical identity: dynamic entities by (id, pos, direction, cookdata).

        Static geometry is excluded because it cannot change. Transient fields
        (`rot`, `turndir`, `pivot`) are excluded because they only carry meaning
        part-way through a move's resolution.
        """
        return tuple(
            sorted(
                (e.id, e.pos, e.direction, e.cookdata)
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
