# Phase 0: SSR Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python reference implementation of Stephen's Sausage Roll that replays all 121 official `.dem` solution files to a winning state, plus the tooling to hunt divergences against the real game.

**Architecture:** Pure-Python, dependency-light, immutable hashable state. Correctness is established empirically: the `.dem` corpus supplies 121 known-winning input sequences, and because SSR introduces mechanics gradually across worlds, replaying levels *in game order* turns the corpus into a natural development curriculum — the first failing replay tells you which mechanic to implement next. Rules are **derived from observed divergence**, not transcribed from a spec, because no authoritative machine-readable spec exists.

**Tech Stack:** Python 3.12, `uv`, `pytest`, stdlib only for the core simulator. No numpy in `ssr_env` — Phase 1's Rust port is where speed comes from.

---

## Prerequisite reading

- Spec: `docs/superpowers/specs/2026-07-24-ssr-learned-heuristics-design.md`, especially §5 (validation strategy) and §7.1 (why undo must be switchable).

## A note on the mechanics tasks

Tasks 9–13 cannot ship pre-written rule implementations, and a plan that pretended otherwise would be actively harmful — confidently wrong mechanics are worse than absent ones. Those tasks specify the **test**, the **signatures**, and the **divergence loop** used to derive each rule. The loop is rigorous: for each level you have exact geometry plus an exact winning input sequence, so a mismatch localises to a single move, and the project owner (who plays the game) can adjudicate that move directly.

## File structure

```
src/ssr_env/
  __init__.py       Public API re-exports
  types.py          Enums: Direction, Tile, CookState, Orientation
  level.py          Level geometry: grid, heights, grills, spawn
  state.py          GameState, PlayerState, Sausage — immutable, hashable
  mechanics.py      step(); the derived rules
  dem.py            .dem parsing
  render.py         ASCII rendering
  errors.py         Typed failures
tools/
  fetch_dem.py      Vendor the .dem corpus
  extract_levels.py Unity asset extraction
  divergence.py     Human differential-testing harness
tests/
  test_dem.py  test_level.py  test_state.py
  test_render.py  test_mechanics.py  test_replay.py
data/
  dem/              121 vendored .dem files
  levels/           Extracted level JSON
```

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`, `src/ssr_env/__init__.py`, `tests/test_smoke.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "ssr-env"
version = "0.1.0"
description = "Stephen's Sausage Roll simulator"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Also create `tests/__init__.py` (empty). Later tasks import shared fixtures via
`from tests.test_level import RAW`, which requires `tests` to be a real package:

```bash
touch tests/__init__.py
```

- [ ] **Step 2: Create the package entry point**

```python
# src/ssr_env/__init__.py
"""Stephen's Sausage Roll simulator — reference implementation."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Write a smoke test**

```python
# tests/test_smoke.py
import ssr_env


def test_package_imports():
    assert ssr_env.__version__ == "0.1.0"
```

- [ ] **Step 4: Install and run**

```bash
uv sync --extra dev && uv run pytest tests/test_smoke.py -v
```

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src tests && git commit -m "feat: scaffold ssr_env package"
```

---

### Task 2: Vendor the `.dem` corpus

The corpus is the acceptance suite. Vendor it so tests never depend on network access.

**Files:**
- Create: `tools/fetch_dem.py`, `tests/test_dem_corpus.py`

- [ ] **Step 1: Write the fetch script**

```python
# tools/fetch_dem.py
"""Download the .dem solution corpus from SSRDecompile into data/dem/."""
import json
import urllib.request
from pathlib import Path

TREE = "https://api.github.com/repos/jbzdarkid/SSRDecompile/git/trees/main?recursive=1"
RAW = "https://raw.githubusercontent.com/jbzdarkid/SSRDecompile/main/"
DEST = Path(__file__).parent.parent / "data" / "dem"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(TREE) as resp:
        tree = json.load(resp)["tree"]
    paths = [e["path"] for e in tree if e["path"].endswith(".dem")]
    for path in paths:
        target = DEST / Path(path).name
        with urllib.request.urlopen(RAW + path) as resp:
            target.write_bytes(resp.read())
        print(f"{target.name}: {len(target.read_text().splitlines())} moves")
    print(f"\n{len(paths)} files -> {DEST}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

```bash
uv run python tools/fetch_dem.py
```

Expected: 121 files written to `data/dem/`.

- [ ] **Step 3: Write the corpus invariant test**

```python
# tests/test_dem_corpus.py
from pathlib import Path

import pytest

DEM_DIR = Path(__file__).parent.parent / "data" / "dem"
VALID_TOKENS = {"North", "South", "East", "West", "Undo"}


def test_corpus_present():
    assert len(list(DEM_DIR.glob("*.dem"))) == 121


@pytest.mark.parametrize("path", sorted(DEM_DIR.glob("*.dem")), ids=lambda p: p.stem)
def test_only_known_tokens(path: Path):
    tokens = {line.strip() for line in path.read_text().splitlines() if line.strip()}
    assert tokens <= VALID_TOKENS, f"unexpected tokens: {tokens - VALID_TOKENS}"
```

- [ ] **Step 4: Run**

```bash
uv run pytest tests/test_dem_corpus.py -q
```

Expected: 122 passed. A failure here means the corpus contains a token the parser must handle — investigate before proceeding.

- [ ] **Step 5: Commit**

```bash
git add tools/fetch_dem.py tests/test_dem_corpus.py data/dem && git commit -m "feat: vendor .dem solution corpus"
```

---

### Task 3: `.dem` parser

**Files:**
- Create: `src/ssr_env/types.py`, `src/ssr_env/dem.py`, `tests/test_dem.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dem.py
from pathlib import Path

from ssr_env.dem import parse_dem, parse_dem_file
from ssr_env.types import Action, Direction

DEM_DIR = Path(__file__).parent.parent / "data" / "dem"


def test_parses_directions():
    assert parse_dem("North\nSouth\nEast\nWest\n") == [
        Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST,
    ]


def test_parses_undo():
    assert parse_dem("North\nUndo\n") == [Direction.NORTH, Action.UNDO]


def test_ignores_blank_lines():
    assert parse_dem("North\n\n  \nSouth\n") == [Direction.NORTH, Direction.SOUTH]


def test_rejects_unknown_token():
    try:
        parse_dem("Sideways\n")
    except ValueError as exc:
        assert "Sideways" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_level_1_1_length():
    assert len(parse_dem_file(DEM_DIR / "1-1.dem")) == 76


def test_level_5_1_contains_undo():
    assert Action.UNDO in parse_dem_file(DEM_DIR / "5-1.dem")
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_dem.py -q
```

Expected: collection error, `ModuleNotFoundError: ssr_env.dem`.

- [ ] **Step 3: Implement types**

```python
# src/ssr_env/types.py
from enum import Enum


class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        return self.value


class Action(Enum):
    UNDO = "undo"


Input = Direction | Action
```

- [ ] **Step 4: Implement the parser**

```python
# src/ssr_env/dem.py
"""Parse .dem demonstration files: one token per line."""
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
```

- [ ] **Step 5: Run to verify pass**

```bash
uv run pytest tests/test_dem.py -q
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/ssr_env/types.py src/ssr_env/dem.py tests/test_dem.py && git commit -m "feat: parse .dem demonstration files"
```

---

### Task 4: Level extraction spike — **HARD GATE**

The single largest external risk in Phase 0. `.dem` files are input sequences and are worthless without the level geometry they run against. SSRDecompile ships no geometry. Timebox this to **three days**; if it fails, take the fallback and re-plan.

**Files:**
- Create: `tools/extract_levels.py`, `docs/level-format.md`

- [ ] **Step 1: Locate the game install**

```bash
ls ~/Library/Application\ Support/Steam/steamapps/common/"Stephen's Sausage Roll"
```

Expected: a `.app` bundle (macOS) containing `Contents/Resources/Data/`. On Windows the path is `C:\Program Files (x86)\Steam\steamapps\common\Stephen's Sausage Roll\`.

- [ ] **Step 2: Extract assets with AssetRipper**

Download AssetRipper (https://github.com/AssetRipper/AssetRipper), point it at the `Data/` directory, export to `data/raw_assets/`.

- [ ] **Step 3: Find level geometry**

Search the exported assets for per-level data. Levels are named by world-stage (`1-1`, `5-12`, `*-final`) matching the `.dem` filenames, so grep exported `.asset`/`.json`/`TextAsset` files for those identifiers:

```bash
grep -rl "1-1" data/raw_assets/ | head -20
```

Record what you find in `docs/level-format.md`: the container format, the coordinate convention, how heights and grills are encoded, and where the player spawn and sausages sit.

- [ ] **Step 4: Write the converter**

Write `tools/extract_levels.py` emitting one JSON per level into `data/levels/` matching the Task 5 schema. The body is format-dependent and cannot be pre-written — Step 3's findings determine it.

- [ ] **Step 5: Verify against a known level**

Extract `1-1` and render it by hand against the real game's opening screen. The owner plays SSR and can confirm the geometry directly.

- [ ] **Step 6: Gate decision**

If extraction works: commit and continue.

If it fails after three days: **fall back** to hand-transcribing levels from the game with the owner, starting with world 1 (~17 levels). This is slower and caps how much of the corpus can validate the simulator, so record the reduced coverage in the spec's risk table and revisit before Phase 1.

- [ ] **Step 7: Commit**

```bash
git add tools/extract_levels.py docs/level-format.md data/levels && git commit -m "feat: extract official level geometry"
```

---

### Task 5: Level data model

**Files:**
- Create: `src/ssr_env/level.py`, `tests/test_level.py`

Schema, chosen to be human-writable so hand-transcription stays viable:

```json
{
  "name": "1-1",
  "width": 5, "height": 5,
  "tiles": [["water","water"], ["ground","grill"]],
  "heights": [[0,0],[0,1]],
  "player": {"x": 1, "y": 1, "z": 0, "facing": "North"},
  "sausages": [{"x": 2, "y": 2, "z": 0, "orientation": "horizontal"}]
}
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test_level.py
import pytest

from ssr_env.level import Level
from ssr_env.types import Direction, Orientation, Tile

RAW = {
    "name": "test", "width": 2, "height": 2,
    "tiles": [["ground", "grill"], ["water", "ground"]],
    "heights": [[0, 1], [0, 0]],
    "player": {"x": 0, "y": 0, "z": 0, "facing": "North"},
    "sausages": [{"x": 1, "y": 1, "z": 0, "orientation": "horizontal"}],
}


def test_loads_dimensions():
    lvl = Level.from_dict(RAW)
    assert (lvl.width, lvl.height) == (2, 2)


def test_tile_lookup_is_xy_indexed():
    lvl = Level.from_dict(RAW)
    assert lvl.tile(0, 0) is Tile.GROUND
    assert lvl.tile(1, 0) is Tile.GRILL
    assert lvl.tile(0, 1) is Tile.WATER


def test_height_lookup():
    assert Level.from_dict(RAW).height_at(1, 0) == 1


def test_out_of_bounds_reads_as_water():
    assert Level.from_dict(RAW).tile(-1, 0) is Tile.WATER


def test_initial_player_and_sausages():
    lvl = Level.from_dict(RAW)
    assert lvl.player_start.facing is Direction.NORTH
    assert lvl.sausage_starts[0].orientation is Orientation.HORIZONTAL


def test_rejects_ragged_grid():
    bad = {**RAW, "tiles": [["ground"], ["water", "ground"]]}
    with pytest.raises(ValueError, match="ragged"):
        Level.from_dict(bad)
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_level.py -q
```

Expected: `ModuleNotFoundError: ssr_env.level`.

- [ ] **Step 3: Extend types**

Append to `src/ssr_env/types.py`:

```python
class Tile(Enum):
    GROUND = "ground"
    WATER = "water"
    GRILL = "grill"


class Orientation(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
```

- [ ] **Step 4: Implement `Level`**

```python
# src/ssr_env/level.py
"""Static level geometry. Immutable; shared across all states of a puzzle."""
from dataclasses import dataclass
from pathlib import Path
import json

from .types import Direction, Orientation, Tile


@dataclass(frozen=True)
class PlayerStart:
    x: int
    y: int
    z: int
    facing: Direction


@dataclass(frozen=True)
class SausageStart:
    x: int
    y: int
    z: int
    orientation: Orientation


@dataclass(frozen=True)
class Level:
    name: str
    width: int
    height: int
    tiles: tuple[tuple[Tile, ...], ...]      # indexed [y][x]
    heights: tuple[tuple[int, ...], ...]     # indexed [y][x]
    player_start: PlayerStart
    sausage_starts: tuple[SausageStart, ...]

    @classmethod
    def from_dict(cls, raw: dict) -> "Level":
        rows = raw["tiles"]
        if any(len(r) != raw["width"] for r in rows) or len(rows) != raw["height"]:
            raise ValueError(f"ragged grid in level {raw['name']!r}")
        p = raw["player"]
        return cls(
            name=raw["name"],
            width=raw["width"],
            height=raw["height"],
            tiles=tuple(tuple(Tile(t) for t in row) for row in rows),
            heights=tuple(tuple(int(h) for h in row) for row in raw["heights"]),
            player_start=PlayerStart(p["x"], p["y"], p["z"], Direction[p["facing"].upper()]),
            sausage_starts=tuple(
                SausageStart(s["x"], s["y"], s["z"], Orientation(s["orientation"]))
                for s in raw["sausages"]
            ),
        )

    @classmethod
    def load(cls, path: Path) -> "Level":
        return cls.from_dict(json.loads(Path(path).read_text()))

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def tile(self, x: int, y: int) -> Tile:
        """Out-of-bounds reads as water: the island is surrounded by sea."""
        return self.tiles[y][x] if self.in_bounds(x, y) else Tile.WATER

    def height_at(self, x: int, y: int) -> int:
        return self.heights[y][x] if self.in_bounds(x, y) else 0
```

- [ ] **Step 5: Run to verify pass**

```bash
uv run pytest tests/test_level.py -q
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/ssr_env/level.py tests/test_level.py && git commit -m "feat: level geometry model"
```

---

### Task 6: Game state — immutable and hashable

Hashability is not cosmetic: Phase 1 enumerates the full reachable state graph and needs states as dict keys.

**Files:**
- Create: `src/ssr_env/state.py`, `tests/test_state.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_state.py
from ssr_env.level import Level
from ssr_env.state import GameState, Sausage
from ssr_env.types import CookState, Direction, Orientation
from tests.test_level import RAW


def test_initial_state_matches_level():
    st = GameState.initial(Level.from_dict(RAW))
    assert st.player.x == 0 and st.player.facing is Direction.NORTH
    assert len(st.sausages) == 1


def test_state_is_hashable_and_value_equal():
    lvl = Level.from_dict(RAW)
    assert hash(GameState.initial(lvl)) == hash(GameState.initial(lvl))
    assert GameState.initial(lvl) == GameState.initial(lvl)


def test_states_differing_in_facing_are_distinct():
    lvl = Level.from_dict(RAW)
    a = GameState.initial(lvl)
    b = a.with_player(a.player.turned(Direction.SOUTH))
    assert a != b and hash(a) != hash(b)


def test_sausage_starts_raw_on_all_four_faces():
    s = GameState.initial(Level.from_dict(RAW)).sausages[0]
    assert s.faces == (CookState.RAW,) * 4


def test_sausage_is_burnt_when_any_face_burnt():
    s = Sausage(1, 1, 0, Orientation.HORIZONTAL,
                (CookState.RAW, CookState.BURNT, CookState.RAW, CookState.RAW))
    assert s.is_burnt


def test_sausage_is_cooked_only_when_all_faces_cooked():
    s = Sausage(1, 1, 0, Orientation.HORIZONTAL, (CookState.COOKED,) * 4)
    assert s.is_cooked
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_state.py -q
```

Expected: `ModuleNotFoundError: ssr_env.state`.

- [ ] **Step 3: Add `CookState` to types**

```python
class CookState(Enum):
    RAW = "raw"
    COOKED = "cooked"
    BURNT = "burnt"
```

- [ ] **Step 4: Implement state**

Face indices `0..3` are the sausage's four cookable surfaces (two halves x two sides). The mapping from index to physical surface, and how rolling permutes it, is derived in Task 10 — the container is defined here, the permutation is not.

```python
# src/ssr_env/state.py
"""Mutable-by-copy game state. Frozen dataclasses so states are hashable."""
from dataclasses import dataclass, replace

from .level import Level
from .types import CookState, Direction, Orientation


@dataclass(frozen=True)
class Player:
    x: int
    y: int
    z: int
    facing: Direction

    def turned(self, facing: Direction) -> "Player":
        return replace(self, facing=facing)

    def moved(self, x: int, y: int, z: int) -> "Player":
        return replace(self, x=x, y=y, z=z)


@dataclass(frozen=True)
class Sausage:
    x: int
    y: int
    z: int
    orientation: Orientation
    faces: tuple[CookState, CookState, CookState, CookState]

    @property
    def is_burnt(self) -> bool:
        return CookState.BURNT in self.faces

    @property
    def is_cooked(self) -> bool:
        return all(f is CookState.COOKED for f in self.faces)

    @property
    def cells(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """The two grid cells this sausage occupies."""
        if self.orientation is Orientation.HORIZONTAL:
            return ((self.x, self.y), (self.x + 1, self.y))
        return ((self.x, self.y), (self.x, self.y + 1))


@dataclass(frozen=True)
class GameState:
    level: Level
    player: Player
    sausages: tuple[Sausage, ...]

    @classmethod
    def initial(cls, level: Level) -> "GameState":
        p = level.player_start
        return cls(
            level=level,
            player=Player(p.x, p.y, p.z, p.facing),
            sausages=tuple(
                Sausage(s.x, s.y, s.z, s.orientation, (CookState.RAW,) * 4)
                for s in level.sausage_starts
            ),
        )

    def with_player(self, player: Player) -> "GameState":
        return replace(self, player=player)

    def with_sausages(self, sausages: tuple[Sausage, ...]) -> "GameState":
        return replace(self, sausages=sausages)
```

- [ ] **Step 5: Run to verify pass**

```bash
uv run pytest tests/test_state.py -q
```

Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/ssr_env/types.py src/ssr_env/state.py tests/test_state.py && git commit -m "feat: hashable game state"
```

---

### Task 7: ASCII renderer

Built before the mechanics because every subsequent task debugs through it, and because spec §5.4 makes the rendering a validated artifact in its own right.

**Files:**
- Create: `src/ssr_env/render.py`, `tests/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_render.py
from ssr_env.level import Level
from ssr_env.render import render
from ssr_env.state import GameState
from tests.test_level import RAW


def test_render_contains_legend_and_grid():
    out = render(GameState.initial(Level.from_dict(RAW)))
    assert "Level test" in out
    assert "Player:" in out
    assert "Sausage A:" in out


def test_render_marks_water_and_grill():
    out = render(GameState.initial(Level.from_dict(RAW)))
    assert "~" in out and "#" in out


def test_render_is_deterministic():
    st = GameState.initial(Level.from_dict(RAW))
    assert render(st) == render(st)
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/test_render.py -q
```

Expected: `ModuleNotFoundError: ssr_env.render`.

- [ ] **Step 3: Implement the renderer**

Terrain grid plus an explicit entity list — the grid alone cannot express cook-face state, and spec §5.4 requires a human to solve from this text alone.

```python
# src/ssr_env/render.py
"""Human- and LLM-readable text rendering of a game state."""
from .state import GameState
from .types import Tile

_GLYPH = {Tile.WATER: "~", Tile.GRILL: "#"}


def render(state: GameState) -> str:
    lvl = state.level
    lines = [f"Level {lvl.name}  ({lvl.width}x{lvl.height})", ""]
    lines.append("Terrain ('~' water, '#' grill, digit = ground height):")
    lines.append("    " + " ".join(str(x) for x in range(lvl.width)))
    for y in range(lvl.height):
        cells = []
        for x in range(lvl.width):
            tile = lvl.tile(x, y)
            cells.append(_GLYPH.get(tile, str(lvl.height_at(x, y))))
        lines.append(f"  {y} " + " ".join(cells))
    lines.append("")

    p = state.player
    lines.append(f"Player: ({p.x},{p.y}) height {p.z}, facing {p.facing.name.title()}")
    for i, s in enumerate(state.sausages):
        label = chr(ord("A") + i)
        a, b = s.cells
        faces = " ".join(f"f{j}={f.value}" for j, f in enumerate(s.faces))
        lines.append(
            f"Sausage {label}: {a}-{b} height {s.z} "
            f"{s.orientation.value}, {faces}"
        )
    return "\n".join(lines)
```

- [ ] **Step 4: Run to verify pass**

```bash
uv run pytest tests/test_render.py -q
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/ssr_env/render.py tests/test_render.py && git commit -m "feat: ASCII state renderer"
```

---

### Task 8: Replay harness and divergence reporter

The instrument for all mechanics work. Its tests fail until Task 9+ land — that is intended, and they are marked `xfail` so the suite stays green while the mechanics are derived.

**Files:**
- Create: `src/ssr_env/replay.py`, `tests/test_replay.py`

- [ ] **Step 1: Write the harness**

```python
# src/ssr_env/replay.py
"""Replay a .dem input sequence and localise the first divergence."""
from dataclasses import dataclass
from pathlib import Path

from .dem import parse_dem_file
from .level import Level
from .mechanics import StepResult, step
from .render import render
from .state import GameState
from .types import Input


@dataclass
class ReplayReport:
    level: str
    solved: bool
    moves_applied: int
    total_moves: int
    failure_index: int | None
    failure_reason: str | None
    final_render: str

    def summary(self) -> str:
        if self.solved:
            return f"{self.level}: SOLVED in {self.moves_applied} moves"
        return (
            f"{self.level}: DIVERGED at move {self.failure_index}"
            f"/{self.total_moves} — {self.failure_reason}\n\n{self.final_render}"
        )


def replay(level: Level, inputs: list[Input]) -> ReplayReport:
    state = GameState.initial(level)
    history: list[GameState] = []
    for i, action in enumerate(inputs):
        result: StepResult = step(state, action, history)
        if result.lost:
            return ReplayReport(
                level.name, False, i, len(inputs), i, result.reason, render(result.state)
            )
        state = result.state
    solved = step(state, None, history).solved
    return ReplayReport(
        level.name, solved, len(inputs), len(inputs),
        None if solved else len(inputs),
        None if solved else "sequence exhausted without reaching goal",
        render(state),
    )


def replay_file(level_path: Path, dem_path: Path) -> ReplayReport:
    return replay(Level.load(level_path), parse_dem_file(dem_path))
```

- [ ] **Step 2: Write the acceptance suite**

```python
# tests/test_replay.py
from pathlib import Path

import pytest

from ssr_env.replay import replay_file

ROOT = Path(__file__).parent.parent
LEVELS, DEMS = ROOT / "data" / "levels", ROOT / "data" / "dem"

# Populated as mechanics land. Move a level here once its replay passes;
# it then guards against regressions for every later mechanic.
PASSING: set[str] = set()


def _cases():
    return sorted(p.stem for p in DEMS.glob("*.dem") if (LEVELS / f"{p.stem}.json").exists())


@pytest.mark.parametrize("name", _cases())
def test_replay_reaches_goal(name: str, request):
    if name not in PASSING:
        request.node.add_marker(pytest.mark.xfail(reason="mechanics not yet derived", strict=False))
    report = replay_file(LEVELS / f"{name}.json", DEMS / f"{name}.dem")
    assert report.solved, report.summary()
```

- [ ] **Step 3: Run — expect xfails, not errors**

```bash
uv run pytest tests/test_replay.py -q
```

Expected: all `xfailed` once `mechanics.py` exists. Until then, collection fails — that is the signal to start Task 9.

- [ ] **Step 4: Commit**

```bash
git add src/ssr_env/replay.py tests/test_replay.py && git commit -m "feat: replay harness with divergence reporting"
```

---

### Task 9: Movement mechanics — player only

**Files:**
- Create: `src/ssr_env/mechanics.py`, `tests/test_mechanics.py`

The player occupies two cells: body and fork. Pressing a direction either **rotates** (turning to face it) or **moves** (translating along the current facing). Which of the two occurs, and how the fork sweeps during rotation, is the first thing to derive.

- [ ] **Step 1: Define the interface**

```python
# src/ssr_env/mechanics.py
"""Transition rules. Derived empirically — see docs/mechanics.md for provenance."""
from dataclasses import dataclass

from .state import GameState
from .types import Action, Direction, Input


@dataclass(frozen=True)
class StepResult:
    state: GameState
    solved: bool = False
    lost: bool = False
    reason: str | None = None


def fork_cell(state: GameState) -> tuple[int, int]:
    """Grid cell occupied by the fork, given body position and facing."""
    dx, dy = state.player.facing.delta
    return (state.player.x + dx, state.player.y + dy)


def step(state: GameState, action: Input | None, history: list[GameState] | None = None) -> StepResult:
    """Apply one input. `action=None` queries terminal status without moving.

    `history` enables undo; pass None to withhold undo (see spec §7.1).
    """
    raise NotImplementedError("derive via Task 9 divergence loop")
```

- [ ] **Step 2: Write movement tests on a sausage-free level**

Build a flat 5x5 level with no sausages and no grills. Assert: rotating changes `facing` without moving the body; moving forward translates the body one cell along facing; walking into water loses; the fork cell tracks facing. Write these as concrete `assert` statements against `step()` using the `RAW`-style dict from Task 5, adapted to 5x5.

- [ ] **Step 3: Derive the rules**

Run `uv run python -c "from ssr_env.replay import replay_file; print(replay_file('data/levels/1-1.json','data/dem/1-1.dem').summary())"`. Implement `step()` to your best understanding, then iterate: the report localises the first divergent move and renders the state there. For each divergence, ask the owner what the real game does at that exact position, and record the answer in `docs/mechanics.md` with the level and move index as provenance.

- [ ] **Step 4: Commit each derived rule separately**

```bash
git add src/ssr_env/mechanics.py docs/mechanics.md tests/test_mechanics.py && git commit -m "feat: player movement and rotation"
```

---

### Task 10: Sausage rolling and pushing

- [ ] **Step 1** Extend `step()` so the fork displaces sausages. A sausage pushed **along its long axis slides**; pushed **perpendicular to it, rolls**, which permutes the four cook faces.
- [ ] **Step 2** Derive the face permutation by rolling a sausage over a grill in the real game and observing which surfaces char. Record the permutation in `docs/mechanics.md`.
- [ ] **Step 3** Add unit tests pinning the permutation: rolling a sausage four times in one direction must return all faces to their starting arrangement.
- [ ] **Step 4** Run `1-1.dem`. When it solves, add `"1-1"` to `PASSING` in `tests/test_replay.py`.
- [ ] **Step 5** Commit.

---

### Task 11: Cooking, burning, and loss conditions

- [ ] **Step 1** A sausage face resting on a grill cooks: `RAW -> COOKED`. Cooking an already-`COOKED` face makes it `BURNT`, which is an irreversible loss.
- [ ] **Step 2** A sausage pushed into water is lost; the player entering water is lost. Confirm against the real game whether either is instant-loss or merely unwinnable — this distinction directly determines Phase 1's dead-state labels, so get it right.
- [ ] **Step 3** Implement the goal test: all sausages cooked on all four faces **and** the player returned to the spawn position.
- [ ] **Step 4** Run the world-1 replays; add each passing level to `PASSING`.
- [ ] **Step 5** Commit.

---

### Task 12: Undo

Required by `5-1.dem` and switchable per spec §7.1.

- [ ] **Step 1** `step()` pushes the pre-move state onto `history` on every non-undo input; `Action.UNDO` pops and restores.
- [ ] **Step 2** Test: any move followed by undo returns to a state equal *and hash-equal* to the original.
- [ ] **Step 3** Test: `step(state, Action.UNDO, history=None)` raises, so the no-undo evaluation mode cannot silently succeed.
- [ ] **Step 4** Commit.

---

### Task 13: The grind — remaining worlds

Worlds 2–5 introduce ladders, standing on sausages, and fork separation. Each is derived by the same loop.

- [ ] **Step 1** Run the full replay suite: `uv run pytest tests/test_replay.py -q`.
- [ ] **Step 2** Take the lowest-numbered failing level. Read its divergence report.
- [ ] **Step 3** Derive the missing rule with the owner; record it in `docs/mechanics.md`.
- [ ] **Step 4** Implement, add a unit test pinning the rule in isolation, add the level to `PASSING`, commit.
- [ ] **Step 5** Repeat until all 121 pass. **This is the Phase 0 exit gate.**

---

### Task 14: Human differential testing harness

Covers the region replays cannot reach: off-solution and dead states (spec §5.2).

**Files:**
- Create: `tools/divergence.py`

- [ ] **Step 1** Write a tool that, given a level, walks random or adversarial input sequences, **preferring sequences the simulator predicts end in a dead or lost state**, and emits: the input sequence as `.dem`-format lines, plus the predicted final state via `render()`.
- [ ] **Step 2** Emit batches of ten cases to `data/divergence/<level>/`.
- [ ] **Step 3** The owner executes each sequence in the real game and flags mismatches.
- [ ] **Step 4** Each confirmed mismatch becomes a regression test in `tests/test_mechanics.py` with the observed correct outcome.
- [ ] **Step 5** Commit.

---

### Task 15: Public API

**Files:**
- Modify: `src/ssr_env/__init__.py`

- [ ] **Step 1** Re-export `Level`, `GameState`, `step`, `StepResult`, `render`, `replay`, `parse_dem`, and the enums.
- [ ] **Step 2** Test that `from ssr_env import Level, GameState, step, render` works.
- [ ] **Step 3** Write `README.md` usage showing: load a level, step it, render it, replay a `.dem`.
- [ ] **Step 4** Run the full suite: `uv run pytest -q`. Expected: 121 replay tests passing, zero xfail.
- [ ] **Step 5** Commit and tag `phase-0-complete`.

---

## Exit criteria

1. All 121 `.dem` replays reach a winning state.
2. `docs/mechanics.md` records every derived rule with level/move provenance.
3. At least one confirmed-correct dead-state regression test per loss mode (burn, sausage drowned, player drowned).
4. States are hashable and value-equal, ready for Phase 1 enumeration.
5. Undo is switchable and raises when withheld.
