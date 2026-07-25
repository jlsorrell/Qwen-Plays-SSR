# Stephen's Sausage Roll — mechanics

The only written specification of SSR's rules that exists anywhere. Phase 1's
Rust port is a translation of *this document*, not of the game.

## How to use this document

Rules are transcribed from the decompiled `Assembly-CSharp.dll` (see
`tools/extract_levels.py` for how to regenerate `data/decompiled/`), then
verified by `.dem` replay. Both halves matter: reading gives the rule, replay
proves we read it right.

**Provenance convention.** Every rule cites its source anchor as
`GameState.cs:1560 ProcessInput`, and — once a replay exercises it — the level
and move index that confirmed it, as `confirmed: 1-3 @ move 47`. A rule with no
confirmation is a hypothesis.

**Never copy decompiled code into this repository.** Read the logic, state the
rule in your own words here, implement independently.

---

## 1. Architecture: the game ticks, the simulator settles

This is the single most important structural decision in the port.

The game is **animation-driven**. `ProcessInput(dir)` does not compute a new
state; it *initiates* a `Movement` on the player, and `MovementsTick` then
advances all live movements by `Fraction` increments across frames, resolving
pushes, collisions, falls and cooking as they occur. `Movement.remaining` is the
animation progress, and `MType` has 28 members — `WalkForward`, `Backpedal`,
`TurnIn`, `TurnOut`, `StrafeL`, `ClimbUp_Init`, `ClimbUp_Loop`, `Fall`,
`PivotIn`, `NoCanDo`, `Surprise_Chasm`, and so on.

The simulator is **settle-driven**: one call to `step()` applies an input and
then ticks to quiescence, returning the settled state.

The `Fraction` timing cannot simply be discarded. It exists to interleave
*simultaneous* movements — the player walking while a sausage rolls while
another falls — and the interleaving order determines collision outcomes. What
can be discarded is the frame rate: we advance by exact rational steps to the
next event boundary rather than by wall-clock.

**Only settled states enter the state key.** `rot`, `pivot`, `turndir` and live
`movement` are mid-animation bookkeeping. See `state.GameState.state_key`.

Source: `GameState.cs:1560 ProcessInput`, `GameState.cs MovementsTick`,
`Movement.cs:6 MType`.

---

## 2. Primitives — CONFIRMED

**Coord** (`Coord.cs`) is an integer `(x, y, z)`.

**North is `+y`.** `Coord.North = (0, 1)`, `South = (0, -1)`, `East = (1, 0)`,
`West = (-1, 0)`, `Up = (0, 0, 1)`, `Down = (0, 0, -1)`. Easy to get backwards;
the renderer prints rows in descending `y` so north appears at the top.

**Direction** (`Direction.cs`) has eleven members in this ordinal order:
`North=0, South=1, West=2, East=3, NorthEast=4, SouthWest=5, NorthWest=6,
SouthEast=7, None=8, Down=9, Up=10`. Serialised level data stores the ordinal,
so the Python enum matches it exactly. `.dem` input uses only the four cardinals.

**Fraction / FractCoord** (`Fraction.cs`, `FractCoord.cs`) — exact rational
arithmetic for sub-tick movement. Not yet transcribed; see §5.

---

## 3. Entity model — CONFIRMED

Everything is an `Entity`. There is no separate terrain grid.

`EntType` (ordinals): `ground=0, bbq=1, player=2, sausage=3, ladder=4,
spectralsausage=5, barrier=6, fork=7, island=8`.

Serialised fields, per `Entity.SaveToString`:

```
x, y, z, type, id, direction, dat, stuckto, rot, <unused 0>, cookdata,
turndir, tilenum, tileset, pivot
```

`tilenum`/`tileset` are cosmetic. `dat` carries the island name for
`EntType.island` and links the overworld to levels.

**`cookdata` packs four faces in base 4**, range 0..255:
`cookdata%4`, `cookdata/4%4`, `cookdata/16%4`, `cookdata/64%4`. Four states per
face, not two. The meaning of each of the four values is **not yet established**
— see §9 and §13.

The **fork is not serialised**. No level file contains an `EntType.fork`; it is
created at runtime attached to the player. Source: extraction histogram over all
205 levels.

---

## 4. Input dispatch — PARTIAL

`ProcessInput(dir)` returns false immediately if a movement is already live, or
if `player.pos.z < -2` (already fallen out of the world).

Dispatch depends on whether the player is **laden** (carrying a sausage on the
fork, `Laden(player)`) and on `dir` relative to `player.direction`:

- **Laden**, `dir` parallel to facing (same or `Inverse()`): `TryMovePlayer(dir)`.
- **Laden**, `dir` perpendicular: ladder up if `LadderUpInDir(dir)`; ladder down
  if `LadderDownInDir(dir)` and nothing solid below; otherwise `TryMovePlayer`.
- **Unladen**, `dir` parallel: ladder climb if applicable and `!player.Extended()`,
  otherwise `TryMovePlayer`.
- **Extended**, `dir` with a ladder up/down: `TryClimbUp` / `TryClimbDown`.
- Otherwise: **`TryTurnPlayer(dir)`**, which is `TryTurn(player, player.direction.LeftOf(dir))`
  — the turn case, parameterised by whether the target direction is to the left.

After dispatch, `PassiveForceSweep()` runs unconditionally. On success
`ProcessPetalStuff()` runs (decorative only — petals and splashes, safe to omit).
On failure the attempt is recorded in `moveattempts[player.id]`.

Source: `GameState.cs:1560 ProcessInput`, `GameState.cs TryTurnPlayer`.

TODO: `TryTurn`, `Direction.LeftOf`, and the meaning of `Extended()`, `Laden()`,
`LadenTarget()`.

---

## 5. Player movement — PARTIAL

### 5.1 Moves are speculative and can be rolled back

`TryMovePlayer` calls `BakEntities()` before doing anything, then either
`DiscardLastBackup()` on success or `RestoreEntities()` when the attempt turns
out not to work. The game *tries* a move, inspects the result, and rewinds if it
doesn't like it.

This is a gift for the Python port. `GameState` is already immutable, so a
"backup" is just holding a reference to the previous value and a "restore" is
returning it — no snapshot machinery needed. Where the game mutates and rewinds,
we build candidate states and discard them.

Source: `GameState.cs:1810 TryMovePlayer`.

### 5.2 Force propagation is the core primitive

Pushing is recursive: `ApplyForce(...)` → `TryPushEnt(...)` → `ApplyForce(...)`.

`ApplyForce` is overloaded four ways (entity, coord, coord-with-`entsfound`,
bounding-box-with-cell-array) but they converge: find the entities occupying the
target cells, filter out ineligible ones, and call `TryPushEnt` on the first
eligible one.

Parameters and what they carry:

| Parameter | Meaning |
|---|---|
| `dir` | push direction |
| `torsion` | rotational component — the roll-versus-slide selector. Confirm 0 = slide, 1 = roll. |
| `speed` | feeds `Movement` timing; interacts with `MaxSpeed` |
| `weakforce` | a weaker push variant; establish where it applies |
| `canchangeplayerfooting` | whether the push may move what the player stands on |
| `recurse` | whether the push chains onward |

Entities are **ineligible** to receive force when any of:
- already moving (`current.movement != null`)
- a decoration (`Decoration()`)
- a laden fork (`type == fork && Laden()`)

And the push **fails outright** if the target's `LadenTarget()` is the player —
you cannot push something that is carrying you.

`Entity.Border(dir)` supplies the pushing cells; `RoughOccupancyBounds_Wide()`
bounds the search.

Source: `GameState.cs:3396-3453 ApplyForce`.

### 5.3 Standing on a sausage

If `Floor(player)` is a sausage and the input is perpendicular to that sausage's
direction (`dir.NormalTo(entity.direction)`), the game applies force at the
player's feet in the **inverse** direction — the sausage rolls out from under
you. It then inspects `movement.torsion` and whether any entity under the
sausage's lower footprint is stationary, and if so **inverts the player's own
movement direction** (`dir = dir.Inverse()`).

So walking perpendicular while standing on a sausage can move you the opposite
way from the key you pressed. Confirm against replay before trusting it.

Source: `GameState.cs:1810 TryMovePlayer`.

### 5.4 Still to transcribe

`TryPushEnt` (the recursion's other half), `PassiveForceSweep`, `Movement.Translation`
construction, `AddTranslation`, `AddTranslationOK`, `AddRotation`, `AddPivot`,
`MovementsTick`, `MoveTickLength`, `MaxSpeed`, `SortDynamicEnts`, `Floor`,
`Direction.NormalTo`, `Direction.Inverse`.

## 6. The fork — NOT TRANSCRIBED

`TryFork`, `BumpForks`, `ForkFall`, `CheckForkLanded`, `CombinedBorders`,
`PlayerBorder`, `Entity.Extended()`.

The player occupies two cells — body and fork — and later worlds allow them to
separate. TODO.

## 7. Sausage pushing and rolling — NOT TRANSCRIBED

`PassiveForceSweep`, `ApplyPivotForces1`, `CanRoll`, `Entity.Pushable()`,
`Entity.Pivot()`, `Entity.TryRotate()`, `CalcSausagePositions`,
`CheckWallSausageCollisions`.

A sausage occupies two cells. Pushed along its long axis it slides; pushed
perpendicular it rolls, permuting the cook faces. **The exact face permutation is
unestablished** and must be pinned by a unit test asserting that four rolls in
one direction restore the original arrangement.

Note `Entity.cs:341` performs a base-4 *reversal* of `cookdata`
(`f3 + 4*f2 + 16*f1 + 64*f0`), evidence that face order is positional and that
some operation mirrors the sausage. Identify which. TODO.

## 8. Falling — NOT TRANSCRIBED

`CanFall`, `CanFall_Liberal`, `CheckSausageLanded`, `CheckForkLanded`,
`CheckPlayerLanded`, `GetSurfaceType`, `OverWaterMovements`,
`OnlySubmergedMovements`.

Two fall predicates exist, one stricter than the other; establish where each
applies. TODO.

## 9. Cooking and burning — NOT TRANSCRIBED

`DoCook`, the `totrycook` list, `CalcBBQAshSteps`, `sausagescooked`,
`haveevercookedall`.

Known: `lostreason = "Burned"` is set at `GameState.cs:993`. Cooking is deferred
— entities are collected into `totrycook` during movement resolution and cooked
afterwards (`GameState.cs:1396-1477`), which matters for ordering.

Establish the four per-face states and the transitions between them. TODO.

## 10. Ladders — PARTIAL

### 10.1 Ladders come from two places — CONFIRMED

`LadderAt(c)` returns a `Direction`:

1. If the entity at `c` is `EntType.ladder`, its `direction`.
2. **If the entity is `EntType.island`, from the island mask**: value `v` at that
   cell with `3 <= v <= 6` yields `Direction(v - 3)` — North, South, West, East.
3. Otherwise `Direction.None`.

Case 2 means **a large part of the terrain lives in island masks, not in
entities**. An `EntType.island` entity is a whole terrain chunk whose shape and
ladder placement come from a 3D int grid looked up by name.

Source: `GameState.cs LadderAt`, `Entity.cs IslandMaskVal`, `IslandMask.cs`.

### 10.2 Mask lookup — CONFIRMED

`Entity.IslandMaskVal(pos)` indexes `mask[lx][ly][lz]` where
`(lx,ly,lz) = pos - entity.pos - mask.offset`, returning 0 outside the grid.

The mask table is keyed globally while island `dat` is level-local
(`island0`, `island1`, ...). Join rule, verified against all 248 island entities
in the playable corpus: try `<level>__<dat>`, else fall back to `<level>` — the
primary island (`island0`) is keyed by the level name itself.

Implemented in `level.resolve_island_mask` / `level.mask_value_at`.

### 10.3 Mask value semantics — DECODED

Every consumer of `IslandMaskVal` has been read. The encoding is a flat tagged
integer, not a bitfield:

| Value | Meaning | Source |
|---|---|---|
| `> 0` | **solid** | `Entity.IslandAt` |
| `-1` | solid **only when the island entity's `cookdata == 0`** | `Entity.IslandAt` |
| `0` | empty (52,839 cells — the bulk) | |
| `1` | plain solid ground (5,481) | |
| `2` | **grill facing East** (413) | `GameState.BBQAt`, `BBQAtDir` |
| `20` | **grill facing North** (92) | `GameState.BBQAt`, `BBQAtDir` |
| `3..6` | **ladder**, direction `Direction(v - 3)` (365 total) | `GameState.LadderAt` |
| `9..12` | **pedestal**, direction `Direction(v - 9)` | `GameState.PedastalAt` |
| `13` | solid, footprint category 1 | `GameState.FootprintTypeAt` |
| `14` | solid, footprint category 2 | `GameState.FootprintTypeAt` |
| `<= -10` | **decoration** of type `-10 - v` | `GameState.DecorationAt` |

Footprint categories are cosmetic (footstep effects); category 3 is the grill
surface and is what `CalcBBQAshSteps` keys on.

Implemented in `level.py`: `is_solid_mask_value`, `bbq_direction_from_mask`,
`ladder_direction_from_mask`, `pedestal_direction_from_mask`,
`decoration_type_from_mask`, `footprint_type_from_mask`.

**Note the grill count coincidence.** Mask values 2 and 20 total 505 cells, and
the corpus contains exactly 505 `EntType.bbq` entities. Either grills are
represented twice — once as an entity, once in the mask — or this is chance.
Establish which before implementing cooking, since double-counting grills would
corrupt every cook transition.

### 10.4 Still unresolved

Values `15`, `16`, `17`, `18` (297-4,822 cells each) are solid by the `> 0` rule
but hit no decoder — they fall through `FootprintTypeAt` to category 0. Likely
tileset or slope variants that only affect appearance. Value `8` (1 cell) and
`-9` (288 cells) are unexplained; `-9` is notably *not* a decoration, since the
decoration test is `<= -10`.

None of these block movement: solidity is decided by sign alone.

`LadderUpInDir`, `LadderDownInDir`, `TryClimbUp`, `TryClimbDown`,
`AutomaticClimbUp`, `AutomaticClimbDown`, `AutomaticTurn`, `AutomaticPlayerTick`,
`RotateBack`, `GetHat`. The `Automatic*` family suggests the player acts without
input under some conditions. Establish when. TODO.

## 11. Win and loss — PARTIAL

**Loss** (`GameState.cs:969 Lost()`): returns `lostreason` if set; also lost when
`player.pos.z < -2`. Known reason string: `"Burned"`. Enumerate the rest.

**Win**: `AllCooked`, `CheckGameWon`, `LevelCompleted`, `CompleteLevel`.
All sausages cooked on all four faces **and** the player returned to start — the
return-to-start condition needs confirming against the code rather than folklore.

TODO.

## 12. Undo — NOT TRANSCRIBED

`TakeUndoSnapshot`, `RestoreEntities`, `DiscardLastBackup`, `ClearUndos`,
`BakStruct`.

**`BakStruct` equality compares `pos`, `direction`, `cookdata` per entity** — this
is the authoritative definition of state identity and is already implemented in
`state.GameState.state_key`. Confirmed by reading; not yet exercised by replay.

Spec §7.1 requires undo be switchable: replay of world 5+ needs it, the primary
solve-rate metric must withhold it.

---

## 13. Open questions

1. What do the four per-face `cookdata` values mean? Raw / cooked / burnt leaves
   one unaccounted for. `CalcBBQAshSteps` hints at an ash state.
2. Which operation triggers the base-4 face reversal at `Entity.cs:341`?
3. When do the `Automatic*` player actions fire without input?
4. What is `stuckto`? Suspected: sausage skewered on the fork.
5. Full enumeration of `lostreason` strings.
6. Does `spectralsausage` follow sausage rules with an exception, or its own set?
