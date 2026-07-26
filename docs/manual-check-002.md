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
