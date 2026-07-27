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


@dataclass(frozen=True, slots=True)
class StepTrace:
    input_index: int
    global_move: int
    segment: str
    segment_index: int
    segment_move: int
    input: Input
    moved: bool
    reason: str | None
    level_before: str
    level_after: str
    completed_level: str | None
    loss: str
    changes: tuple[EntityDelta, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "input_index": self.input_index,
            "global_move": self.global_move,
            "segment": self.segment,
            "segment_index": self.segment_index,
            "segment_move": self.segment_move,
            "input": self.input.name,
            "moved": self.moved,
            "reason": self.reason,
            "level_before": self.level_before or None,
            "level_after": self.level_after or None,
            "completed_level": self.completed_level,
            "loss": self.loss or None,
            "changes": [change.to_dict() for change in self.changes],
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


def trace_step(
    before: GameState,
    after: GameState,
    *,
    input_index: int,
    segment: str,
    segment_index: int,
    action: Input,
    moved: bool,
    reason: str | None,
) -> StepTrace | None:
    changes = entity_deltas(before, after)
    if (
        not changes
        and moved
        and not reason
        and before.pushtargetlevel == after.pushtargetlevel
        and not after.lost_reason
    ):
        return None
    return StepTrace(
        input_index=input_index,
        global_move=input_index + 1,
        segment=segment,
        segment_index=segment_index,
        segment_move=segment_index + 1,
        input=action,
        moved=moved,
        reason=reason,
        level_before=before.pushtargetlevel,
        level_after=after.pushtargetlevel,
        completed_level=(
            before.pushtargetlevel
            if (
                before.pushtargetlevel
                and not after.pushtargetlevel
                and before.pushtargetlevel in after.completed
            )
            else None
        ),
        loss=after.lost_reason,
        changes=changes,
    )
