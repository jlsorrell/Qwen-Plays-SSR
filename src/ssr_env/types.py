"""Core enums and primitives, mirroring the game's own model.

Enum ordinals match the game's so that serialised level data — which stores
`(int)type` and `(int)direction` — round-trips without a translation table.
"""

from enum import IntEnum
from typing import NamedTuple


class Coord(NamedTuple):
    """Integer grid position. y increases NORTHWARD (see Direction)."""

    x: int
    y: int
    z: int = 0

    def __add__(self, other: "Coord") -> "Coord":  # type: ignore[override]
        return Coord(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Coord") -> "Coord":
        return Coord(self.x - other.x, self.y - other.y, self.z - other.z)


class Direction(IntEnum):
    """Eleven members, ordinals as the game defines them.

    Note the convention: North is +y. This is the opposite of screen coordinates
    and is easy to get backwards.
    """

    NORTH = 0
    SOUTH = 1
    WEST = 2
    EAST = 3
    NORTHEAST = 4
    SOUTHWEST = 5
    NORTHWEST = 6
    SOUTHEAST = 7
    NONE = 8
    DOWN = 9
    UP = 10

    @property
    def delta(self) -> Coord:
        return _DELTAS[self]


_DELTAS: dict[Direction, Coord] = {
    Direction.NORTH: Coord(0, 1, 0),
    Direction.SOUTH: Coord(0, -1, 0),
    Direction.WEST: Coord(-1, 0, 0),
    Direction.EAST: Coord(1, 0, 0),
    Direction.NORTHEAST: Coord(1, 1, 0),
    Direction.SOUTHWEST: Coord(-1, -1, 0),
    Direction.NORTHWEST: Coord(-1, 1, 0),
    Direction.SOUTHEAST: Coord(1, -1, 0),
    Direction.NONE: Coord(0, 0, 0),
    Direction.DOWN: Coord(0, 0, -1),
    Direction.UP: Coord(0, 0, 1),
}

#: The four directions a .dem file can contain.
INPUT_DIRECTIONS: tuple[Direction, ...] = (
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
)


class EntType(IntEnum):
    """Every object in the game is one of these. There is no separate terrain grid."""

    GROUND = 0
    BBQ = 1
    PLAYER = 2
    SAUSAGE = 3
    LADDER = 4
    SPECTRALSAUSAGE = 5
    BARRIER = 6
    FORK = 7
    ISLAND = 8


#: Types that never move. Excluded from the canonical state key.
STATIC_TYPES: frozenset[EntType] = frozenset(
    {EntType.GROUND, EntType.BBQ, EntType.LADDER, EntType.BARRIER, EntType.ISLAND}
)

#: Types that can move or change cook state. These define the state key.
DYNAMIC_TYPES: frozenset[EntType] = frozenset(
    {EntType.PLAYER, EntType.SAUSAGE, EntType.SPECTRALSAUSAGE, EntType.FORK}
)


class Action(IntEnum):
    """Non-directional inputs."""

    UNDO = 100


Input = Direction | Action
