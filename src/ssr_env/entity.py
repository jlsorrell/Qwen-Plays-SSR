"""The game's single uniform entity model.

Field set taken from the game's `EntitySkeleton`. Cosmetic fields (`tilenum`,
`tileset`) are dropped. Transient fields (`rot`, `turndir`, `pivot`) are kept
because the simulator needs them mid-move, but they are deliberately excluded
from the canonical state key — see `state.GameState.state_key`.
"""

from dataclasses import dataclass, replace

from .types import Coord, Direction, EntType

#: Number of independently-cookable surfaces on a sausage.
N_FACES = 4

#: Values a single face can take. The game packs four of these per sausage in
#: base 4, so cookdata ranges 0..255.
FACE_STATES = 4

MAX_COOKDATA = FACE_STATES**N_FACES - 1


def unpack_cookdata(cookdata: int) -> tuple[int, int, int, int]:
    """Split packed cookdata into its four per-face values, least-significant first."""
    if not 0 <= cookdata <= MAX_COOKDATA:
        raise ValueError(f"cookdata {cookdata} outside 0..{MAX_COOKDATA}")
    return tuple((cookdata >> (2 * i)) & 3 for i in range(N_FACES))  # type: ignore[return-value]


def pack_cookdata(faces: tuple[int, int, int, int]) -> int:
    """Inverse of `unpack_cookdata`."""
    if len(faces) != N_FACES:
        raise ValueError(f"expected {N_FACES} faces, got {len(faces)}")
    if any(not 0 <= f < FACE_STATES for f in faces):
        raise ValueError(f"face values must be 0..{FACE_STATES - 1}, got {faces}")
    return sum(f << (2 * i) for i, f in enumerate(faces))


@dataclass(frozen=True, slots=True)
class Entity:
    pos: Coord
    type: EntType
    id: int
    direction: Direction = Direction.NONE
    cookdata: int = 0
    stuckto: int = -1
    #: For EntType.ISLAND this is the island's name and the key into the island
    #: mask table — the mask carries the chunk's shape and its ladder encoding,
    #: so this is load-bearing geometry, not decoration.
    dat: str = ""
    #: Not cosmetic despite the names: `Entity.Decoration()` consults both, and
    #: `Solid()` is `!Decoration()`. Dropping them makes ground solidity wrong.
    tilenum: int = 0
    tileset: int = 0
    # Transient within a move's resolution; never part of the state key.
    rot: int = 0
    turndir: Direction = Direction.NONE
    pivot: int = 0

    @property
    def faces(self) -> tuple[int, int, int, int]:
        return unpack_cookdata(self.cookdata)

    def with_faces(self, faces: tuple[int, int, int, int]) -> "Entity":
        return replace(self, cookdata=pack_cookdata(faces))

    def moved_to(self, pos: Coord) -> "Entity":
        return replace(self, pos=pos)

    def facing(self, direction: Direction) -> "Entity":
        return replace(self, direction=direction)
