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

    def inverse(self) -> "Direction":
        """Opposite direction. Mirrors `DirectionUtil.Inverse` (`invrot` table)."""
        return Direction(_INVROT[self])

    def rot_clockwise_90(self) -> "Direction":
        """Quarter turn clockwise viewed from above. Mirrors `RotClockwise90`."""
        return Direction(_ROT_CLOCKWISE[self])

    def flip_h(self) -> "Direction":
        """Mirror across the vertical axis. Mirrors `DirectionUtil.FlipH`."""
        return Direction(_FLIP_H[self])

    def flip_v(self) -> "Direction":
        """Mirror across the horizontal axis. Mirrors `DirectionUtil.FlipV`."""
        return Direction(_FLIP_V[self])

    @property
    def is_ortho(self) -> bool:
        """One of the four cardinals. Mirrors `Ortho()`: `d < NorthEast`."""
        return self < Direction.NORTHEAST

    @property
    def is_diagonal(self) -> bool:
        """Mirrors `Diagonal()`: `NorthEast <= d < None`."""
        return Direction.NORTHEAST <= self < Direction.NONE

    @property
    def is_valid(self) -> bool:
        return self is not Direction.NONE

    def parallel_to(self, other: "Direction") -> bool:
        """Mirrors `ParallelTo`: same or opposite, and both valid."""
        if not self.is_valid or not other.is_valid:
            return False
        return self is other or self.inverse() is other

    def normal_to(self, other: "Direction") -> bool:
        """Mirrors `NormalTo`: not parallel, and neither is None."""
        return (
            not self.parallel_to(other)
            and self is not Direction.NONE
            and other is not Direction.NONE
        )

    def left_of(self, other: "Direction") -> bool:
        """Mirrors `DirectionUtil.LeftOf` — the turn-handedness flag.

        Despite the name this asks whether `other` is a quarter turn *clockwise*
        from `self`. `TryTurnPlayer` passes the result to `TryTurn` as its `left`
        argument, which selects between the `StrafeL`/`StrafeR` movement types.
        """
        if self.is_ortho and other.is_ortho:
            return self.rot_clockwise_90() is other
        return _continue_rot(self, other) is self.rot_clockwise_90()


# Lookup tables transcribed verbatim from DirectionUtil. Indices are Direction
# ordinals. Kept as raw tuples rather than rewritten as arithmetic: the game is
# the specification, and a clever reimplementation would be a place to be subtly
# wrong.
_INVROT = (1, 0, 3, 2, 5, 4, 7, 6, 8, 10, 9)
_ROT_CLOCKWISE = (3, 2, 0, 1, 7, 6, 4, 5, 8, 9, 10)
_ROT_CLOCKWISE_45 = (4, 5, 7, 6, 2, 3, 0, 1, 8, 9, 10)
_FLIP_H = (0, 1, 3, 2, 6, 7, 4, 5, 8, 9, 10)
_FLIP_V = (1, 0, 2, 3, 7, 6, 5, 4, 8, 9, 10)

#: `continuerot[to][from]` — note the index order is reversed relative to the
#: call signature `ContinueRot(from, to)`. Value 8 is Direction.NONE.
_CONTINUE_ROT = (
    (8, 8, 8, 8, 6, 8, 4, 8),
    (8, 8, 8, 8, 8, 7, 8, 5),
    (8, 8, 8, 8, 8, 6, 5, 8),
    (8, 8, 8, 8, 7, 8, 8, 4),
    (3, 8, 8, 0, 8, 8, 8, 8),
    (8, 2, 1, 8, 8, 8, 8, 8),
    (2, 8, 0, 8, 8, 8, 8, 8),
    (8, 3, 8, 1, 8, 8, 8, 8),
)


def _continue_rot(from_dir: "Direction", to_dir: "Direction") -> "Direction":
    """Mirrors `DirectionUtil.ContinueRot(from, to)` = `continuerot[to, from]`.

    Only defined over the eight compass directions; `None`/`Up`/`Down` are out of
    the table's range.
    """
    if from_dir >= Direction.NONE or to_dir >= Direction.NONE:
        return Direction.NONE
    return Direction(_CONTINUE_ROT[to_dir][from_dir])


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
