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

**Fraction / FractCoord** (`Fraction.cs`, `FractCoord.cs`) — rational arithmetic
for sub-tick movement.

**Use Python's stdlib `fractions.Fraction`.** The game's version reduces lazily
(only when `den > 10000`, to dodge int overflow) but `operator ==` compares by
cross-multiplication, so equality is value-based and matches the stdlib exactly.
Python's arbitrary-precision ints remove the overflow motivation entirely.

Two quirks in the game's implementation, recorded because they are divergence
risks rather than things to reproduce:

1. **`CompareTo` casts to `float`.** Ordering is therefore approximate, and two
   distinct rationals that are very close could tie or invert. Movement
   denominators are small, so exact and float ordering agree in practice — but
   if a replay ever diverges on ordering, look here first.
2. **`GetHashCode` is `num ^ den`, inconsistent with value equality.** `1/2` and
   `2/4` compare equal but hash differently. Harmless in the game because
   `Fraction` is never a dictionary key; do not imitate it.

### 2.1 Direction algebra — CONFIRMED

`DirectionUtil` is table-driven. The tables are transcribed verbatim into
`types.py` rather than rewritten as arithmetic — the game is the specification,
and a clever reimplementation is a place to be subtly wrong.

| Operation | Rule |
|---|---|
| `Inverse` | pairwise swap; `Up`<->`Down`; `None` fixed |
| `RotClockwise90` | N->E->S->W->N (clockwise from above, North = +y); diagonals cycle likewise; `None`/`Up`/`Down` fixed |
| `FlipH` | mirrors East<->West, fixes North/South |
| `FlipV` | mirrors North<->South, fixes East/West |
| `Ortho(d)` | `d < NorthEast` — the four cardinals |
| `Diagonal(d)` | `NorthEast <= d < None` |
| `Valid(d)` | `d != None` |
| `ParallelTo(a,b)` | `a == b or a.Inverse() == b`, **and both valid** |
| `NormalTo(a,b)` | not parallel, and neither is `None` |

**`LeftOf(a, b)` is a trap.** Despite the name it asks whether `b` is a quarter
turn *clockwise* from `a`: for orthogonal inputs it is `a.RotClockwise90() == b`.
`TryTurnPlayer` passes its result to `TryTurn` as the `left` flag, which selects
between the `StrafeL` and `StrafeR` movement types. For non-orthogonal inputs it
consults `continuerot[to, from]` — note the index order is reversed relative to
the call signature `ContinueRot(from, to)`.

Note `ParallelTo` returns false when either direction is `None`, so `None` is
parallel to nothing, *including itself*. Consequently `parallel` and `normal`
partition every pair of planar directions exactly — asserted as a test invariant.

Source: `DirectionUtil.cs:73-149,181-237`.

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

**No field here is safe to discard as cosmetic.** Twice a field that looked
decorative turned out to be geometry:

- `dat` names the island for `EntType.island` and is the island-mask key (§10.2).
- `tilenum`/`tileset` feed `Entity.Decoration()`, and `Solid()` is
  `!Decoration()`, so they decide whether ground can be stood on (§5.4).

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

### 5.4 Occupancy and solidity — CONFIRMED

`Entity.Extended()` decides whether an entity occupies one cell or two: sausages
and islands always; **the player only while the fork is attached**. Once the fork
detaches into its own `EntType.fork` entity, the player becomes a single cell.
An extended entity occupies `pos` and `pos + direction`.

`Entity.At(pos)` resolves islands through the mask and everything else through
that cell list. `EntAt(pos)` searches dynamic entities before static ones —
order matters, since a sausage resting on ground must be found before the ground.
`SolidEntAt(pos)` is `EntAt(pos)?.Solid() ?? false`.

**`Utility.Solid(e)` is `!e.Decoration()`** — solidity is defined negatively.
`Entity.Decoration()` applies only to `EntType.ground` and reads the entity's
`tileset`/`tilenum` **and** the level-wide tileset:

- level tileset 4: tilesets 7/8/9 with `4 <= tilenum <= 7` are **not** decorative;
  nor is tileset 9 with `tilenum < 4`
- level tileset 0: tilesets 5/13 with `tilenum >= 6` **are** decorative
- otherwise: decorative iff tileset is 7, 8 or 9

This is why `tilenum`/`tileset` cannot be discarded as cosmetic — they decide
whether ground can be stood on. Second time a "decorative" field turned out to
be geometry; the first was `dat` (§10.2).

Other type predicates from `Utility.cs`: `Directional` (player, ladder, sausage),
`SubjectToPassiveForces` (sausage, fork, island), `NeedsGround` (player, sausage,
fork), `CanHatTurn` (sausage, fork).

Implemented in `geometry.py`. **Validated end-to-end: 104/104 players in real
levels stand on something solid**, which requires the mask join, mask decoding,
occupancy and solidity all to be simultaneously correct.

Source: `Entity.cs Extended/At/Decoration`, `GameState.cs:5030 SolidEntAt`,
`Utility.cs:60-95`.

### 5.5 Level string metadata — CONFIRMED

The `*`-separated fields after the entity records, per `GameState.LoadDat`:

| Index | Field |
|---|---|
| 0 | entity records |
| 1 | levelcompleted (CSV) |
| 2 | worldsausagesissued (CSV) |
| 3 | **tileset** — feeds `Decoration()`, defaults 0 |
| 4 | **displayname** — the in-game level name |
| 5 | sausagescooked |
| 6 | musicseed |

All 206 extracted levels carry a display name. Many are the names players know
("Cold Gate", "Pressure Points", "Shy Dragon", "Emerson Jetty"); internal chunks
keep their raw names ("bridge1", "fillerisland"). **These are a likely shortcut
for the `.dem`-to-level mapping** (§ replay), since the owner can recognise them
directly.

### 5.6 TryPushEnt — the force recursion's other half — PARTIAL

Rejected outright: static types, entities already moving, and **`barrier`**
(barriers are never pushable). Vertical pushes force zero torsion.

Islands additionally refuse to move when: in the overworld with no pushes
budgeted; when the island is the current push target; or when the player is
standing on it and the push is horizontal (unless `canchangeplayerfooting`).

**Torsion is inherited from below, not computed locally.** `Under(e)` gives the
supporting entities. If the entity cannot roll or has no support, torsion is 0.
Otherwise torsion is taken from the supporters' movements — and **only if every
supporter agrees**; any disagreement collapses it to 0. This is how a sausage
resting on a rolling sausage rolls along with it.

**`TORSIONPLACEHOLDER = -666` is a deferred marker, not a magnitude.** A sausage
pushed *non-parallel* to its own direction gets `-666`; everything else gets 0.
The real torsion is resolved later during movement resolution
(`GameState.cs:4116, 4257`). An earlier note here guessed "0 = slide, 1 = roll";
that was wrong, which is why it was recorded as unconfirmed.

Source: `GameState.cs:2703 TryPushEnt`, `GameState.cs:315`.

### 5.7 Type predicates — CONFIRMED, and counter-intuitive

`Utility.Static` is defined negatively: **not** static = player, sausage,
**barrier**, fork, **island**. Therefore:

| Type | Static? |
|---|---|
| ground, bbq, ladder | yes |
| **spectralsausage** | **yes** — despite the name |
| **barrier**, **island** | **no** — islands are pushed around in world 6 |
| player, sausage, fork | no |

This matters beyond pushing: `state_key()` is built from the dynamic types, so
getting the partition wrong silently drops moving islands out of state identity
— and the oracle's whole notion of "same state" with it. The initial
implementation here had barrier and island as static and spectralsausage as
dynamic; wrong on three of nine types.

`Utility.CanRoll` is sausage only. `Vertical(d)` is `d > None` (Up/Down);
`Horizontal(d)` is `d <= None`, so `None` counts as horizontal.

Source: `Utility.cs:117-133`, `DirectionUtil.cs:156-164`.

### 5.9 Turning — PARTIAL

`TryTurn(e, clockwise, turnspeed=2)`; fails outright if the entity is already
moving.

The target facing is `e.direction.Rot90(clockwise)`. The interesting part is
`RotBetween(old, new)` — the **diagonal** between the two facings — and
`pos = e.pos + that diagonal`. That is the cell the fork sweeps through.

**Turning applies force.** When the entity is extended (fork attached), the game
calls `ApplyForce(pos, direction, 1, 1)` on that swept diagonal cell — so
turning can push a sausage. If the push succeeds, `turnspeed` drops to 1. If it
fails and the entity is the player, the blocked entities are recorded in
`moveattempts`.

Carrying something (`GetHat(e)` non-null) also forces `turnspeed = 1`.

For the player specifically, whatever it is standing on gets a `Fixed` movement
for the duration, provided that floor entity is not static.

Note the parameter here is honestly named `clockwise`, while `TryTurnPlayer`
supplies it from `LeftOf` and `Movement` stores it as `left`. The value is the
same; only the names disagree. See §2.1.

`RotBetween` is a symmetric 4x4 table over the cardinals with -1 for parallel
pairs. Verified as a test invariant: it is defined exactly when the two
directions are perpendicular.

Source: `GameState.cs TryTurn`, `DirectionUtil.cs:65-71,176-179,259-266`.

### 5.10 Movement construction — CONFIRMED

All three constructors set `remaining = Fraction(1, 1 << (speed - 1))`. **Speed
is a power-of-two divisor of duration**: speed 1 lasts 1, speed 2 lasts 1/2,
speed 3 lasts 1/4. Higher speed finishes sooner.

`Movement.Translation(target, direction, torsion, speed, mtype, left)` zeroes
torsion when the push direction is parallel to the target's own direction —
sliding a sausage along its axis imparts no roll. This is a second, independent
place the slide/roll distinction is enforced, after §5.6.

`Movement.Rotation(target, from, to, mtype, speed)` sets `left = to.LeftOf(from)`
— **note the argument order is reversed** relative to `TryTurnPlayer`, which
computes `player.direction.LeftOf(dir)`. Same predicate, opposite operands.

`Movement.Fixed(target, speed)` pins an entity in place for a duration with
`MType.Fixed` and no direction.

Source: `Movement.cs:296-375`.

### 5.11 The tick loop — CONFIRMED

`MovementsTick()` is the resolution step. Per tick:

1. Clear `totrycook`, take `deltaTime = MoveTickLength()`.
2. Walk `movements` **backwards** (so finished entries can be removed in place).
3. `movement.Tick(deltaTime)` decrements `remaining`.
4. When `remaining.num == 0` the movement is finished:
   - A `Fixed` movement whose player is still turning gets its speed refreshed
     rather than resolving — it stays pinned for the duration of the turn.
   - Otherwise `Resolve()` commits the change, the entity's `movement` clears,
     and the entry is removed.
   - If the direction was `Down`, the appropriate landing check fires:
     `CheckSausageLanded` / `CheckForkLanded` / `CheckPlayerLanded`.
   - Sausages are queued into `totrycook`.
   - Moving islands set a recalculation flag.
5. After the loop, `DoCook` runs over `totrycook` (`GameState.cs:1468-1477`).

**Cooking is deferred to the end of the tick**, not applied at the moment of
contact. Ordering therefore matters: a sausage that moves onto a grill and off
again within one tick is a different case from one that settles there.

Source: `GameState.cs:1394 MovementsTick`.

### 5.11a Pivot turns — PARTIAL, and the largest remaining gap

`TryPivotTurn(e, clockwise, pushdir = None)`.

**Precondition — CONFIRMED and implemented.** It returns false immediately
unless `Floor(player)` is an `EntType.island`. Off an island, a collided turn is
an ordinary failed move and no pivot machinery is involved. This alone resolved
most observed cases.

**Structure — transcribed, not implemented.**

```
direction  = e.direction.Rot90(clockwise)          # target facing
direction2 = RotBetween(e.direction, direction)    # the swept diagonal
pushdir    = pushdir or direction.Inverse()
Movement.Pivot(e, pushdir, e.direction, direction2, MType.TurnIn, 1)
ApplyPivotForces1(e, pushdir, e.direction, direction2)
if e is player:
    ApplyForce(e.pos + Down, pushdir, 0, 1, canchangeplayerfooting: true)
ApplyPivotForces2(e, pushdir, e.direction, direction2)
... then recurse into GetHat(e) with the same pushdir
```

Note the player branch pushes **the island underneath itself** — that is the
whole point of a pivot: the player braces against its own footing, which is why
`canchangeplayerfooting` is true here and false everywhere else.

**`Movement.Pivot` — CONFIRMED.** Structurally identical to `Movement.Rotation`
(§5.10): same `remaining = Fraction(1, 1 << (speed-1))`, same
`left = to.LeftOf(from)`. It differs only in carrying `movetype = Pivot` and a
`direction` (the pushdir), where a rotation has `Direction.None`. Nothing
surprising here.

**`weakforce` — CONFIRMED as a suppression flag.** It is not a different kind of
push. Within `TryPushEnt` it appears in exactly three places: passed down to the
recursive `ApplyForce`, and guarding two special cases that it *disables* —

- a sausage branch gated on `!weakforce && e.type == sausage && !player.Extended()`
- a fork branch gated on `!weakforce && e.type == fork && e.stuckto == -1 && e.direction == dir`

So a weak force is an ordinary push with the sausage-and-fork special cases
skipped. That demystifies the flag; the remaining question is only what those
two branches do when they *are* active.

**`ApplyPivotForces1` — CONFIRMED, complete.** All forces are weak, torsion 1.

```
if fromdir.Ortho():
    if fromdir not parallel to movedir and RotBetween(fromdir, movedir) == todir:
        force at pos+todir, direction fromdir, speed 2
elif todir not parallel to movedir and ContinueRot(todir, fromdir) != movedir:
        force at pos+todir, direction todir,   speed 2
```

**`ApplyPivotForces2` — CONFIRMED, complete.** All weak, torsion 1, speed 1
unless noted. `C = ContinueRot(todir, fromdir)`.

| `fromdir` | condition | forces applied |
|---|---|---|
| ortho | `== movedir` | `pos+movedir+fromdir` and `pos+movedir+todir`, both toward `movedir` |
| ortho | `== movedir.Inverse()` | `pos+movedir` and `pos+movedir+todir`, toward `movedir` |
| ortho | `RotBetween(fromdir,movedir) == todir` | `pos+movedir` and `pos+movedir+todir`, toward `movedir` |
| ortho | otherwise | `pos+movedir` toward `movedir` |
| diagonal | `todir == movedir` | `pos+movedir+fromdir`, `pos+movedir+todir` toward `movedir`; plus `pos+movedir` toward `C.Inverse()` |
| diagonal | `todir == movedir.Inverse()` | `pos+movedir` toward `movedir`; `pos-movedir` toward `C.Inverse()` at speed 2 |
| diagonal | `C == movedir` | `pos+movedir` toward `movedir` |
| diagonal | otherwise | `pos+movedir` and `pos+movedir+todir` toward `movedir` |

**The pivot transformation — CONFIRMED.** `Movement.Resolve`, `MoveType.Pivot`:

```
target.pos       += direction     # direction is the pushdir
target.direction  = to            # `to` is the swept DIAGONAL
```

Plus, for a sausage carrying a fork, the fork rotates 45 degrees (clockwise or
counter- depending on `target.direction.LeftOf(to)`) and repositions to
`target.pos + to + direction`.

### 5.11b Turning is two-phase — CONFIRMED, and §5.9 was incomplete

The pivot resolution sets `direction` to a **diagonal**, not to the target
cardinal. That is not an artefact of pivots; it is how all turning works:

- `TryTurn` builds its rotation toward `direction2 = RotBetween(old, new)` — the
  diagonal — and stores the eventual cardinal in `e.turndir`.
- `Entity.Turning()` is literally `direction.Diagonal()`: an entity is mid-turn
  exactly while it faces a diagonal.
- `MType` carries `TurnIn`, `TurnOut` and `TurnBackout` — the phases.

So a turn is: **TurnIn** to the diagonal, then a second movement to `turndir`
(or `TurnBackout` back the way it came, presumably when the second phase is
blocked). The diagonal is a real intermediate state, and it is where the swept
cell and its collisions are evaluated.

**Consequence for this implementation.** `mechanics.try_turn_player` currently
sets the final cardinal in one step. For *settled* states that is likely
equivalent — no settled state faces a diagonal — but it means we do not model
the intermediate, so any rule that fires during the diagonal phase is invisible
to us. Pivot cannot be implemented correctly without it, because a pivot *is*
the recovery path taken when the diagonal phase collides.

Implementing pivot therefore means restructuring turning into two phases and
re-verifying the existing turn behaviour, not adding an isolated branch.

Remaining to read: the tail of `TryPivotTurn` after the `GetHat` recursion, the
two `weakforce`-suppressed branches in `TryPushEnt`, `GetHat`, and the
`TurnOut`/`TurnBackout` phase transitions.

### 5.12 Still to transcribe

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

### 7.1 The two rotations — CONFIRMED

There are two distinct sausage rotations, and only one touches `cookdata`.

**`Entity.Pivot()` — the end-over-end tumble.**

```
pos += direction;  direction = direction.Inverse();  pivot = 1 - pivot;
cookdata faces reversed:  [f0,f1,f2,f3] -> [f3,f2,f1,f0]
dat's two bbq fields swap
```

The sausage lands in the *same two cells* (it moves to `pos+direction` then its
inverted direction points back at `pos`) but reversed end-for-end and inverted.
The face reversal swaps the halves and flips up/down within each — exactly a
tumble over one end. This is the base-4 reversal previously noted at
`Entity.cs:341` as an unidentified mirror operation.

**`Entity.TryRotate(rot_dir)` — the sideways roll.**

```
if (!rot_dir.ParallelTo(direction)) { rot = 1 - rot; ... }
```

It toggles `rot` and, if a fork is stuck to the sausage and orthogonal to it,
inverts that fork's direction. **It does not touch `cookdata`.**

So faces are stored in a canonical frame and `rot` selects which is currently
up. A sideways roll changes the exposed face by flipping `rot`, not by
permuting the stored values.

### 7.2 RESOLVED: `rot` IS part of state identity

This is a contradiction that must be settled before Phase 1, because the oracle
rests on it.

- §7.1 shows `rot` determines **which face is exposed**, which makes it
  semantic: two sausages with equal `cookdata` but different `rot` present
  different faces to a grill and will cook differently.
- §12 shows the game's own `BakStruct` equality — its undo comparison — checks
  only `pos`, `direction` and `cookdata`. It **omits `rot` and `pivot`**.
- `state.GameState.state_key` currently follows `BakStruct` and excludes both.

**Answer: `DoCook` indexes by `e.rot`.**

| Half | Cell | `rot == 0` | `rot == 1` |
|---|---|---|---|
| first | `pos` | cooks face 3 | cooks face 2 |
| second | `pos + direction` | cooks face 0 | cooks face 1 |

So `rot` decides which face meets the grill. It is semantic, and **the game's
`BakStruct` comparison is lossy** — two sausages identical but for `rot` will
cook differently while comparing equal under it.

`state_key` now includes `rot`. `pivot` stays excluded: `Entity.Pivot()` folds
its effect into `cookdata` by reversing the faces, so it carries no independent
state.

**Correction to §4.1 of the spec.** The claim that "state identity is not
guessed — the game hands it to us via BakStruct" was wrong. The game's undo
comparison is a reasonable approximation for undo, where a lost `rot` is
invisible to the player within a single step, but it is not a sound basis for
deduplicating a reachable-state graph. Verify borrowed invariants against what
they are used for.

Cooking a face whose value is already non-zero sets it to 3 — burnt. That is the
burn rule: **cooking the same face twice burns it.**

## 8. Falling — PARTIAL

Falls are ordinary movements with `direction == Direction.Down`. When one
finishes, `MovementsTick` dispatches by type to `CheckSausageLanded`,
`CheckForkLanded` or `CheckPlayerLanded`.

**Sausage drowning — CONFIRMED.** When a sausage's fall resolves with
`pos.z < -2`, it is teleported to `z = -100` and its `dat` field is rewritten
with a leading `'L'` (from `'M'`, or from empty to `"L ; ; "`). So **`dat` on a
sausage is a status field**, not decoration — the fifth field in this codebase
that looks cosmetic and is not. The `z < -2` threshold matches the player's
out-of-world test in `Lost()` and `ProcessInput`.

Source: `GameState.cs:1394 MovementsTick`.

### 8.1 Still to transcribe

`CanFall`, `CanFall_Liberal`, `CheckSausageLanded`, `CheckForkLanded`,
`CheckPlayerLanded`, `GetSurfaceType`, `OverWaterMovements`,
`OnlySubmergedMovements`.

Two fall predicates exist, one stricter than the other; establish where each
applies. TODO.

## 9. Cooking and burning — PARTIAL

### 9.1 The four per-face values — CONFIRMED

`DoCook` (`GameState.cs:~3200-3280`) writes faces back with
`cookdata = a0 + 4*a1 + 16*a2 + 64*a3`, matching the base-4 packing in §3.
The per-face values are:

| Value | Meaning |
|---|---|
| 0 | raw |
| 1 | cooked (grill perpendicular to the sausage's axis) |
| 2 | cooked (grill parallel to the sausage's axis) |
| 3 | **burnt** |

The 1-versus-2 split comes from `direction2.ParallelTo(e.direction)` — the grill
direction relative to the sausage — so both are cooked states differing only in
how the sausage met the grill. Values below 3 emit sparks; 3 emits smoke.

**This resolves open question 1.** The face alphabet is four wide because
"cooked" is recorded two ways, not because there is an ash state.

### 9.2 Burnt marks the sausage's `dat` — CONFIRMED

When any face reaches 3, `dat` becomes `"B;<bbqdat>;<bbqdat2>"`. Together with
the drowning marker from §8 (`'L'` prefix), **`dat` on a sausage is a status
field** carrying its failure mode.

### 9.3 Still to transcribe

The `totrycook` collection path, when a face is selected for cooking, and how
`AllCooked` reads these values for the win condition.

## 9.4 Old notes — NOT TRANSCRIBED

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

## 12.5 Implementation status (2026-07-24)

`step()` runs real `.dem` inputs against real extracted geometry. Implemented:
turning, walking forward/backward, sausage **sliding** along its own axis,
one-cell pushes, undo, out-of-world rejection.

Everything else raises `UnimplementedMechanic` naming itself, so a partial
simulator fails loudly rather than plausibly.

Measured blocker distribution, replaying `1-1.dem` against all 124 candidate
levels — this is the work queue, ordered by what actually blocks progress:

| Blocker | 1-0.dem | 1-1.dem |
|---|---|---|
| `falling` | 71 | 65 |
| `pivot-turn` | 20 | 39 |
| `push-island` | 12 | 11 |
| `push-static` | 10 | 4 |
| `push-chain` | 3 | 3 |
| ran to completion | 5 | 1 |

`falling` dominates because most pairings are *wrong* levels where the player
walks off an edge; it is not the most valuable next target. `pivot-turn` is.

**Unresolved in the roll implementation.** `CalculateTorsions` resolves the
`-666` placeholder and only calls `TryRotate` when the resolved torsion is
non-zero. A zero resolution is a *drag* rather than a roll (`anydrags` versus
`anyrolls` in `GameState.cs:4265-4272`). We currently roll unconditionally on a
perpendicular push. `CalculateTorsion` is untranscribed, so the drag case is
unimplemented — the replay gate will surface it as a divergence.

**`push-island` is probably over-eager on our side.** Walking into a wall of
island terrain currently attempts a push and raises. In the game islands *are*
pushable (world 6), but `TryPushEnt` refuses when the player stands on the
island, when it is the push target, or in the overworld without a push budget —
so the ordinary case is a blocked move, not a push. Establish those conditions
before implementing; treating every island contact as a push is wrong.

**`pivot-turn` is a real mechanic, not an error path.** When a turn collides the
game rolls back and calls `TryPivotTurn` — the player rotates about the fork
rather than the body. Untranscribed.

Note `falling` dominates because most of these are *wrong* level pairings where
the player simply walks off an edge; it is not necessarily the most valuable
mechanic to implement next. `turn-push` is, since it blocks levels that are
otherwise running deep.

**The `.dem` files are not level-local — MEASURED.** The 120 level files sum to
**16,565** input lines; `all.dem` is **16,567**. They are a partition of a single
continuous playthrough, differing by two lines, not 120 independent solutions.

Each `X-Y.dem` therefore begins wherever the previous one ended, and the inputs
spent walking the **overworld** between temples are inside these files too. A
`.dem` replayed from a level's start state will diverge almost immediately,
regardless of how faithful the simulator is — which is exactly what we observe
(median depth 5-19 moves, zero wins across 20 dems x 124 levels).

**This invalidates `replay.find_matching_level` as designed.** Matching a `.dem`
against a level in isolation cannot work. Options, none yet chosen:

1. **Simulate the overworld too** and replay `all.dem` end to end. Most faithful
   and it recovers every level boundary for free, but it needs the overworld
   layer: island entities as levels, `SubworldTransition`, `IssueWorldSausages`,
   level entry and exit. Substantially more scope than the level simulator.
2. **Use the extracted `playerpositions` / `sausagepositions` tables.**
   `merged_binary` carries per-level player and sausage start poses, which the
   current extractor skips. These give trustworthy level start states without
   the overworld — but the `.dem` inputs still contain overworld travel, so they
   would need trimming to the in-level segment, and the trim points are unknown.
3. **Drop `.dem` replay as the acceptance gate** and validate against
   human differential testing (spec §5.2) plus the exact solver instead.

Option 1 is the only one that preserves the original validation plan intact.
Whichever is chosen, this is a Phase 0 planning decision, not an implementation
detail — the replay suite is the exit gate for the whole phase.

---

## 12.6 Overworld replay — the new acceptance path

**PARTLY WRONG — see `docs/differential-test-001-results.md`.** One coordinate
space, but not one play space: sausages are issued on level entry and levels are
subworlds you drop into. The geometry below is right; the state model is not.

**The overworld is not a separate scene.** Every level's island chunk sits at
its offset in one connected space; `merged_binary`'s `offsets` table is that
layout. `level.load_overworld` builds it: 17,154 entities spanning x -107..172,
y -85..67, with the single player taken from the level named `start` (per
`MetaGameState.LoadBinary`'s closing lines) at world position (-4, -1, -1).

This is why the `.dem` corpus is one continuous playthrough (§ corpus), and it
makes `all.dem` the natural acceptance test: one 16,567-input replay over the
whole game.

**Status: reaches move 33 of 16,567.**

The failure at move 33 is a sausage burning. Traced: sausage 4521 is
north-south oriented, rolls east twice over grills at moves 4-5 (cooking faces
2 and 3), then at move 33 *slides north* one cell, which puts its already-cooked
face 3 over a fresh grill cell and burns it.

Sliding along a grill genuinely does burn a sausage in SSR, so the fault is
probably **upstream** — the sausage should not be in that position by move 33.
**Ladders are NOT the cause — measured.** Probing every cell adjacent to the
player (and one above and below each) across the first 34 moves finds **zero**
ladders. The climb branches are never reached. This was the leading hypothesis
and it is wrong; do not spend time on ladders for this divergence.

**Two apparent anomalies, both investigated:**

- *Move 9: a sausage moves that nothing seems to push.* Explained and correct.
  Sausage 4505 sits at (0,-4) east-west oriented, so it also occupies (1,-4) —
  the player's destination. The push is legitimate, and the roll direction and
  `rot` toggle are both right.
- *Moves 10-13: four consecutive EAST inputs produce no turn.* The player stands
  at (1,-4) facing North with sausage 4514 at the fork's destination (2,-4). The
  swept diagonal (2,-3) is empty, so the turn-push finds nothing; the fork then
  collides and `TryPivotTurn` refuses because the footing is `ground`, not
  island. **This may well be correct** — `all.dem` is a recorded session and
  repeated ineffective inputs are plausible. It is not established either way.

**Remaining unexplained:** the burn at move 33. Every cheap hypothesis has been
tested and eliminated, and further progress by inspection is guesswork.

**The right next step is human differential testing (spec §5.2), not more
reading.** The owner has the game. Playing the first ~35 inputs of `all.dem`
and reporting where sausage 4521 ends up, and whether it burns, would settle in
one observation what static analysis has not.

**Two guards are implemented and were not the cause.** Cooking is gated both on
the sausage having moved (mirroring `totrycook`) and on the grill's identity
differing from what the sausage recorded in `dat` (mirroring `DoCook`'s
`array2[1] != bbqdatstring` test). Neither prevents this burn, correctly.

## 10.5 `cookdata` on an island is the "sausages issued" flag — CONFIRMED

This resolves the `-1` exception in `Entity.IslandAt` and one standing open
question.

`IslandAt` has three solidity rules:

| Case | Rule |
|---|---|
| `weak` | `value != 0` |
| `cookdata == 0` | `value > 0` **or** `value == -1` |
| otherwise | `value > 0` |

**`-1` marks a sausage footprint carved into the island mask.** Measured across
the corpus: 440 `-1` cells against 220 sausages — exactly two each — always in
pairs, present in 116 of 205 levels, in counts of 2, 4, 6, 10, 14 and 16.

**`cookdata` on an `EntType.island` entity is not cook state at all.** It is set
to 1 in exactly two places:

- `SubworldTransition(levelname)`, on the island being entered
- the tail of `IssueWorldSausages`, after that level's sausages are spawned

So the flag means *"this level's sausages now exist as real entities"*. Before
that, the sausages are not in the world and their footprints stand in as solid
blocks — you cannot walk through the space a sausage will occupy. Afterwards the
footprints stop being solid because actual sausage entities occupy those cells.

**Consequence for the overworld:** an unentered level's sausage cells are
genuine obstacles. A replay blocked by one is behaving correctly, not buggy.

Source: `Entity.cs IslandAt`, `GameState.cs:492 SubworldTransition`,
`GameState.cs:650 IssueWorldSausages`.

## 12.7 Level entry — IMPLEMENTED

`CheckOverworldGhosts` is what triggers `SubworldTransition`. For each level it
compares the player's pose against that level's recorded start pose, offset by
its island entity:

```
player.pos == playerpositions[name].pos + island.pos
&& player.direction == playerpositions[name].direction
&& fork == null && !LevelCompleted(name)
    -> SubworldTransition(name)
```

**Both position and facing must match.** Standing on the cell is not enough,
which is exactly what the owner observed: the player steps onto the entry cell
with the fork east, nothing happens, and the next press turns them to the
correct heading and drops them in.

`SubworldTransition` then sets the island's `cookdata` to 1 (§10.5, which stops
its sausage footprints being solid), spawns that level's sausages from the
recorded spawn table, and calls `TryLowerAll` — the terrain sinking that reads
on screen as dropping into the level. `SubworldLeave` is the mirror image:
despawn, `CompleteLevel`, `TryRaiseAll`.

Implemented in `mechanics.check_overworld_entry`, using the `player` and
`sausages` tables now captured by the extractor. 86 levels have entry poses.

## 12.8 `Collides()` is the remaining blocker — NOT TRANSCRIBED

Replay currently stops **one cell short** of `level49`'s entry at (1,-3,-1). The
player is pushed off it by a spurious pivot at move 11: turning east, the fork's
destination is a `-1` sausage footprint, which §10.5 confirms is genuinely
solid, so my collision stand-in refuses the turn and pivots instead.

**The stand-in is the problem.** `Entity.Collides()` is not a single-cell
solidity test. It walks neighbouring entities within a `RoughOccupancyBounds`
box and tests real overlap via `Occupancy()`, skipping entities that are stuck
to it, decorative, or translating in lockstep with it. Island-vs-island pairs go
through the `projectioncompatibilities` table — which the extractor currently
reads past and discards.

To finish this: transcribe `Entity.Occupancy()`, `RoughOccupancyBounds`,
`CalcBoxNeighbours`, and capture `projectioncompatibilities` in the extractor.
`Occupancy()` matters most, since a turning entity's footprint covers the swept
arc rather than just its destination — which is very likely why the real game
allows a turn my simulator refuses.

## 13. Open questions

1. ~~What do the four per-face `cookdata` values mean?~~ **Answered in §9.1**:
   0 raw, 1 cooked-perpendicular, 2 cooked-parallel, 3 burnt.
2. Which operation triggers the base-4 face reversal at `Entity.cs:341`?
3. When do the `Automatic*` player actions fire without input?
4. What is `stuckto`? Suspected: sausage skewered on the fork.
5. Full enumeration of `lostreason` strings.
6. Does `spectralsausage` follow sausage rules with an exception, or its own set?
