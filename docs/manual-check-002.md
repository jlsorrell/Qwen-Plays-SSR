# Manual check 002 — WITHDRAWN

The premise was wrong. The owner corrected that the recorded inputs lead to
**Lachrymose Head** (`level47`), not Infant's Break (`level49`). I had inspected
the wrong island.

## The contradiction does not exist

At `level47`'s entry cell `(4, 2, -1)`:

| Fork direction | Cell | Contents |
|---|---|---|
| East | `(5, 2, -1)` | open air |
| North | `(4, 3, -1)` | open air |

Nothing obstructs the approach. That level's `-1` sausage footprints are all at
y=0 and y=1, south of the entry cell. §10.5 stands unchallenged: footprints are
solid placeholders, and the player can stand on the entry cell facing east and
turn north to enter.

## What this confirms

`level47` is entered **facing NORTH**, matching the owner's description exactly.
So the extracted overworld data — offsets, entry poses, spawn tables — is
**correct**. The earlier suspicion that island offsets might be wrong is
discharged.

## What is actually wrong

The simulated player's **path**, not the geometry. After 16 moves it sits at
`(0, -3, -1)`; the real player is heading to `(4, 2, -1)`.

One suggestive detail: with the diagonal collision rule, the simulated player
reaches `x = 4` at move 14 — **the correct x** — but at `y = -3` instead of
`y = 2`. The x-axis tracks and the y-axis is off by 5, which looks systematic
rather than like accumulated drift.

Worth investigating before anything else: whether the north/south sense of
movement is inverted somewhere between input and displacement. `Coord.North` is
`(0, +1)` and `.dem` `North` maps to `w`, both verified — so if there is a sign
error it is in how facing combines with forward/backward movement, not in the
primitives.


## Follow-up: the displacement is a constant, not drift

Hand-simulating the 15 inputs with pure SSR semantics (perpendicular = turn in
place, parallel = move one cell) on unobstructed ground:

```
lands at (4, -4, -1) facing NORTH
level47 entry is (4,  2, -1) facing NORTH
```

**x matches exactly. Facing matches exactly. y is off by exactly 6.**

So the movement rules and the input semantics are right, and the path shape is
right. Something in the y-frame is displaced by a constant. Since the sequence
reaches the correct x from the recorded start x, the start x is right too — it
is specifically the start y, or the y-frame of the entry table, that is wrong.

The start pose comes from a different code path than every other level: `start`
has no `playerpositions` entry, so it is read from the level file and offset by
`offsets["start"]`, per `MetaGameState.LoadBinary`'s closing lines. Every other
level's pose is cross-checked between two sources and they agree. The start pose
has no such cross-check — which makes it the prime suspect.

Working hypothesis: the true start is `(-4, 5, -1)`, six north of what is
computed. That value is not derived from anything, it is what the arithmetic
requires, so it must be verified rather than adopted.

## What would settle it, requiring no progress in the game

The landing area is the first thing in the game, so this needs no unlocking:

**From where the character first appears, how many tiles can you walk north
before running out of ground, and how many south?** Rough is fine.

That pins the y-frame directly against my map of the same area, and it does not
depend on any of the mechanics still in doubt.
