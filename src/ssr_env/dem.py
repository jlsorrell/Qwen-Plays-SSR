"""Parse .dem demonstration files: one token per line.

Format confirmed empirically against the vendored corpus: every non-blank line is
one of North / South / East / West / Undo.
"""

from pathlib import Path

from .types import Action, Direction, Input

_TOKENS: dict[str, Input] = {
    "North": Direction.NORTH,
    "South": Direction.SOUTH,
    "East": Direction.EAST,
    "West": Direction.WEST,
    "Undo": Action.UNDO,
}


def parse_dem(text: str) -> list[Input]:
    inputs: list[Input] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        token = raw.strip()
        if not token:
            continue
        if token not in _TOKENS:
            raise ValueError(f"line {lineno}: unknown token {token!r}")
        inputs.append(_TOKENS[token])
    return inputs


def parse_dem_file(path: Path) -> list[Input]:
    return parse_dem(Path(path).read_text())
