"""Human- and LLM-readable text rendering of a game state.

Two panes, because neither suffices alone: a top-down map carries spatial
structure, and an entity list carries cook-face state and facing, which a glyph
grid cannot express. Spec §5.4 requires that a strong human player be able to
solve a level from this text alone.

North is **-y** (§2), so rows print in *ascending* y to put north at the top,
as it appears on screen. Printing descending y — which is the natural reading of
"north is up" if you forget the sign — silently mirrors the map.
"""

from .state import GameState
from .types import Coord, EntType

GLYPHS: dict[EntType, str] = {
    EntType.GROUND: ".",
    EntType.ISLAND: ".",
    EntType.BBQ: "#",
    EntType.LADDER: "H",
    EntType.BARRIER: "B",
    EntType.PLAYER: "@",
    EntType.FORK: "y",
    EntType.SAUSAGE: "S",
    EntType.SPECTRALSAUSAGE: "s",
}

EMPTY = "~"

#: Drawn last so they sit on top of the terrain they stand on.
_DRAW_ORDER = [
    EntType.GROUND,
    EntType.ISLAND,
    EntType.BBQ,
    EntType.LADDER,
    EntType.BARRIER,
    EntType.SPECTRALSAUSAGE,
    EntType.SAUSAGE,
    EntType.FORK,
    EntType.PLAYER,
]

_LEGEND = "  ".join(
    f"{GLYPHS[t]} {t.name.lower()}" for t in _DRAW_ORDER if t is not EntType.ISLAND
)


def render(state: GameState, name: str = "") -> str:
    if not state.entities:
        return f"Level {name}: empty"

    xs = [e.pos.x for e in state.entities]
    ys = [e.pos.y for e in state.entities]
    zs = [e.pos.z for e in state.entities]

    priority = {t: i for i, t in enumerate(_DRAW_ORDER)}
    top: dict[tuple[int, int], tuple[int, int, str]] = {}
    for e in state.entities:
        cell = (e.pos.x, e.pos.y)
        rank = (e.pos.z, priority.get(e.type, -1))
        if cell not in top or rank > top[cell][:2]:
            top[cell] = (e.pos.z, priority.get(e.type, -1), GLYPHS.get(e.type, "?"))

    header = (
        f"Level {name}  x {min(xs)}..{max(xs)}  y {min(ys)}..{max(ys)}  "
        f"z {min(zs)}..{max(zs)}"
    )
    lines = [header, "", f"Map ({EMPTY} = nothing; north is up):"]

    width = max(len(str(x)) for x in (min(xs), max(xs)))
    lines.append("     " + " ".join(f"{x:>{width}}" for x in range(min(xs), max(xs) + 1)))
    for y in range(min(ys), max(ys) + 1):
        row = [
            top.get((x, y), (0, 0, EMPTY))[2].rjust(width)
            for x in range(min(xs), max(xs) + 1)
        ]
        lines.append(f"  {y:>3}" + " " + " ".join(row))

    lines += ["", f"Legend: {_LEGEND}", ""]

    dynamic = [e for e in state.entities if e.type in (EntType.PLAYER, EntType.FORK)]
    dynamic += [
        e
        for e in state.entities
        if e.type in (EntType.SAUSAGE, EntType.SPECTRALSAUSAGE)
    ]
    if dynamic:
        lines.append("Entities:")
        for e in dynamic:
            detail = (
                f"  {e.type.name.lower()} id={e.id} at ({e.pos.x},{e.pos.y},{e.pos.z}) "
                f"facing {e.direction.name.title()}"
            )
            if e.type in (EntType.SAUSAGE, EntType.SPECTRALSAUSAGE):
                detail += f" faces={e.faces}"
            lines.append(detail)

    if state.lost:
        lines += ["", f"LOST: {state.lost_reason}"]
    return "\n".join(lines)


def surface_map(
    state: GameState,
    masks,
    centre,
    radius: int = 8,
    z_range: tuple[int, int] = (-4, 4),
    marks: dict | None = None,
) -> str:
    """Top-down map showing the **topmost solid surface** in each column.

    Written because the ad-hoc maps used for manual checks tested each cell as
    "solid at z-1 and clear at z". That is right for flat ground and wrong for
    anything raised: a platform whose top surface sits at the sampled height
    fails the "clear above" half and is drawn as water. The shrine platform
    rendered that way, and the owner was asked to compare against a map that
    showed a solid plaza as sea (§12.26).

    Each column is searched from the top of `z_range` down for the first solid
    cell, and its height is drawn relative to `centre.z`:

    - `0` level with the centre, `1`..`9` that many steps higher
    - `-` one step lower, `=` two or more lower
    - `.` nothing solid anywhere in range

    `marks` maps (x, y) to a single character drawn instead of the height, for
    the player, sausages and any cell under discussion.

    **Only terrain counts as surface.** Dynamic entities are skipped: the player
    occupies two cells, so its fork was being drawn as a raised tile one step
    above the ground beside it — which the owner spotted as a phantom step four
    tiles west of the world sausage.
    """
    from .geometry import is_solid, occupies
    from .types import DYNAMIC_TYPES

    def terrain_at(cell) -> bool:
        for entity in state.entities:
            if entity.type in DYNAMIC_TYPES and entity.type is not EntType.ISLAND:
                continue
            if occupies(entity, cell, state, masks, "") and is_solid(
                entity, state.tileset
            ):
                return True
        return False

    marks = marks or {}
    lo, hi = z_range
    lines = []
    # North is -y (§2), so ascending y prints north-first.
    for y in range(centre.y - radius, centre.y + radius + 1):
        row = []
        for x in range(centre.x - radius, centre.x + radius + 1):
            if (x, y) in marks:
                row.append(marks[(x, y)])
                continue
            top = None
            for z in range(centre.z + hi, centre.z + lo - 1, -1):
                if terrain_at(Coord(x, y, z)):
                    top = z
                    break
            if top is None:
                row.append(".")
            else:
                d = top - (centre.z - 1)
                row.append("0" if d == 0 else ("-" if d == -1 else ("=" if d < -1 else str(min(d, 9)))))
        lines.append("".join(row))
    return "\n".join(lines)
