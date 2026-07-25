# Phase 0: SSR Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python reference implementation of Stephen's Sausage Roll that replays all 120 official level `.dem` solution files to a winning state, plus the tooling to hunt divergences against the real game.

**Architecture:** Pure-Python, dependency-light, immutable hashable state. Correctness is established empirically: the `.dem` corpus supplies 120 known-winning input sequences, and because SSR introduces mechanics gradually across worlds, replaying levels *in game order* turns the corpus into a natural development curriculum — the first failing replay tells you which mechanic to implement next. Rules are **derived from observed divergence**, not transcribed from a spec, because no authoritative machine-readable spec exists.

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
  types.py          Enums: Direction (11 members), EntType (9 members), Action
  entity.py         Entity — the game's single uniform entity model
  level.py          Level: the initial entity list, loaded from extracted data
  state.py          GameState + state_key(); immutable, hashable
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
  dem/              121 vendored .dem files (120 levels + all.dem aggregate)
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

Expected: 121 files written (120 levels + all.dem) to `data/dem/`.

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

### Task 5: Entity model and level loading

The game models **everything** as one `Entity` type — ground, island, bbq, ladder,
barrier, player, fork, sausage, spectralsausage. There is no separate terrain grid.
Mirror that; a grid-plus-sausage-list model does not survive contact with world 6.

Semantic fields, taken from `EntitySkeleton`: `pos` (Coord x,y,z), `type`
(EntType), `id`, `direction`, `stuckto`, `cookdata`, plus transient `rot`,
`turndir`, `pivot`. `tilenum`/`tileset` are cosmetic and are dropped.

**Coordinate convention (from the game's `Coord`):** `North = (0, +1)`,
`South = (0, -1)`, `East = (+1, 0)`, `West = (-1, 0)`, `Up = (0, 0, +1)`.
y increases **northward**. `Direction` has eleven members — the four cardinals,
four diagonals, `None`, `Up`, `Down` — of which `.dem` input uses only cardinals.

**Files:**
- Create: `src/ssr_env/entity.py`, `tests/test_entity.py`
- Modify: `src/ssr_env/types.py` (correct Direction deltas; add EntType)

- [ ] **Step 1** Rewrite `Direction` to match the game exactly, including diagonals
      and `None`/`Up`/`Down`. Add `INPUT_DIRECTIONS` for the four `.dem` cardinals.
      Add `EntType` with all nine members.
- [ ] **Step 2** Write failing tests: North delta is `(0, 1)`; `INPUT_DIRECTIONS`
      has exactly four members; `EntType` has exactly nine.
- [ ] **Step 3** Implement. `Entity` is a frozen dataclass; `STATIC_TYPES` and
      `DYNAMIC_TYPES` partition `EntType`.
- [ ] **Step 4** Test that `cookdata` unpacks base-4 into four faces and repacks
      losslessly across the full 0-255 range.
- [ ] **Step 5** Run and commit.

---

### Task 6: Game state and the canonical state key

`GameState.BakStruct` — the game's own undo snapshot — compares states for equality
on exactly `pos`, `direction`, `cookdata` per entity. That is authoritative: it is
the identity relation the game itself uses, so Phase 1's enumeration inherits a
ground-truth definition of "same state" rather than a guessed one. `rot`, `pivot`,
`turndir` and in-flight `movement` are transient within a move's resolution and
must be excluded from the key.

**Files:**
- Create: `src/ssr_env/state.py`, `tests/test_state.py`

- [ ] **Step 1** Write failing tests: two states differing only in `rot` share a
      state key; two differing in `cookdata` do not; the key is hashable and
      stable across reconstruction.
- [ ] **Step 2** Implement `GameState` holding `tuple[Entity, ...]`, with
      `state_key()` returning a hashable tuple of `(id, pos, direction, cookdata)`
      over dynamic entities only — static geometry cannot change.
- [ ] **Step 3** Test that static entities are excluded from the key.
- [ ] **Step 4** Run and commit.

---

### Task 6.5: Configuration-space upper bound

Spec §4.1's tractability estimate is the load-bearing assumption of the whole
project, and it was made before the `cookdata` encoding was known. This task
bounds the risk as early as it can be bounded.

**Scope limit, stated honestly:** the *reachable* state count cannot be measured
without a working `step()`, which does not exist until Task 13. What is computable
from geometry alone is a combinatorial **upper bound** on configuration space. A
small upper bound proves tractability; a large one proves nothing but flags risk.
The true reachable measurement is Task 13.5.

**Files:**
- Create: `tools/state_space.py`, `docs/state-space.md`

- [ ] **Step 1** For each level, compute `product over dynamic entities of
      (walkable cells x directions x reachable cookdata values)`.
- [ ] **Step 2** Report per level, sorted, against world and level number.
- [ ] **Step 3** Write `docs/state-space.md` with the distribution and the
      resulting recommendation for the generator's difficulty ceiling.
- [ ] **Step 4** If world-1 upper bounds already exceed ~10^9, escalate to the
      spec's §8 risk table before proceeding — this is the early warning the task
      exists to produce.
- [ ] **Step 5** Commit.

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
    # all.dem is the injector's concatenated aggregate, not a level — skip it.
    return sorted(
        p.stem
        for p in DEMS.glob("*.dem")
        if p.stem != "all" and (LEVELS / f"{p.stem}.json").exists()
    )


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
- [ ] **Step 5** Repeat until all 120 pass. **This is the Phase 0 exit gate.**

---

### Task 13.5: Measure the true reachable state space

Now that `step()` exists, replace Task 6.5's upper bound with the real number.

- [ ] **Step 1** Enumerate the full reachable component for every world-1 level via
      BFS over `state_key()`, recording state count and wall-clock time.
- [ ] **Step 2** Repeat for worlds 2-3 until enumeration exceeds ten minutes or
      memory, and record where it breaks.
- [ ] **Step 3** Update `docs/state-space.md` and spec §4.1 with measured counts,
      replacing the estimate.
- [ ] **Step 4** Set the generator difficulty ceiling from the measurement. This is
      the number Phase 2 is built on.
- [ ] **Step 5** Commit.

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
- [ ] **Step 4** Run the full suite: `uv run pytest -q`. Expected: 120 replay tests passing, zero xfail.
- [ ] **Step 5** Commit and tag `phase-0-complete`.

---

## Exit criteria

1. All 120 level `.dem` replays reach a winning state.
2. `docs/mechanics.md` records every derived rule with level/move provenance.
3. At least one confirmed-correct dead-state regression test per loss mode (burn, sausage drowned, player drowned).
4. States are hashable and value-equal, ready for Phase 1 enumeration.
5. Undo is switchable and raises when withheld.
