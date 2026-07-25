"""Core enums shared across the simulator."""

from enum import Enum


class Direction(Enum):
    """Cardinal directions. Deltas are (dx, dy) with y increasing southward."""

    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        return self.value


class Action(Enum):
    """Non-directional inputs."""

    UNDO = "undo"


Input = Direction | Action
