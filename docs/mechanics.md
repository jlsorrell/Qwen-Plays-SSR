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
- **Unladen**, `dir` perpendicular: *to be transcribed* — this is the turn case.

Source: `GameState.cs:1560 ProcessInput`.

TODO: transcribe the perpendicular/unladen branch and the meaning of
`Extended()`, `Laden()`, `LadenTarget()`.

---

## 5. Player movement — NOT TRANSCRIBED

Entry: `TryMovePlayer`, `TryFork`.
Movement construction: `AddTranslation`, `AddTranslationOK`, `AddRotation`,
`AddPivot`.
Resolution: `MovementsTick`, `MoveTickLength`, `MaxSpeed`, `SortDynamicEnts`,
`InsertionSort`.

TODO.

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

## 10. Ladders — NOT TRANSCRIBED

`LadderAt`, `LadderUpInDir`, `LadderDownInDir`, `TryClimbUp`, `TryClimbDown`,
`AutomaticClimbUp`, `AutomaticClimbDown`, `AutomaticTurn`, `AutomaticPlayerTick`,
`RotateBack`, `GetHat`.

The `Automatic*` family suggests the player takes actions without input under
some conditions. Establish when. TODO.

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
