"""Read-only replay diagnostics for settled simulator states."""

from dataclasses import dataclass

from .entity import Entity
from .state import GameState
from .types import Coord, Direction, EntType, Input


@dataclass(frozen=True, slots=True)
class EntitySnapshot:
    id: int
    type: EntType
    pos: Coord
    direction: Direction
    rot: int
    faces: tuple[int, int, int, int]
    stuckto: int
    status: str

    @classmethod
    def from_entity(cls, entity: Entity) -> "EntitySnapshot":
        return cls(
            id=entity.id,
            type=entity.type,
            pos=entity.pos,
            direction=entity.direction,
            rot=entity.rot,
            faces=entity.faces,
            stuckto=entity.stuckto,
            status=entity.dat[:1],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type.name,
            "pos": [self.pos.x, self.pos.y, self.pos.z],
            "direction": self.direction.name,
            "rot": self.rot,
            "faces": list(self.faces),
            "stuckto": self.stuckto,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class EntityDelta:
    entity_id: int
    before: EntitySnapshot | None
    after: EntitySnapshot | None

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_id": self.entity_id,
            "before": self.before.to_dict() if self.before is not None else None,
            "after": self.after.to_dict() if self.after is not None else None,
        }


def snapshot_dynamic(state: GameState) -> dict[int, EntitySnapshot]:
    return {
        entity.id: EntitySnapshot.from_entity(entity)
        for entity in state.entities
        if entity.type in (EntType.PLAYER, EntType.SAUSAGE)
    }


def entity_deltas(before: GameState, after: GameState) -> tuple[EntityDelta, ...]:
    old = snapshot_dynamic(before)
    new = snapshot_dynamic(after)
    return tuple(
        EntityDelta(entity_id, old.get(entity_id), new.get(entity_id))
        for entity_id in sorted(old.keys() | new.keys())
        if old.get(entity_id) != new.get(entity_id)
    )
