"""Human- and LLM-readable text rendering of a game state.

Two panes, because neither suffices alone: a top-down map carries spatial
structure, and an entity list carries cook-face state and facing, which a glyph
grid cannot express. Spec §5.4 requires that a strong human player be able to
solve a level from this text alone.

North is +y, so rows print in descending y — north at the top, as it appears
on screen.
"""

from .state import GameState
from .types import EntType

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
    for y in range(max(ys), min(ys) - 1, -1):
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
