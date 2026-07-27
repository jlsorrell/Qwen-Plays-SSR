# Manual check 009 — Emerson Jetty, the first 95 keys

**Level:** Emerson Jetty (world 2, level 1 — internal name `improv3`).

**Start:** the level's own start position, i.e. wherever entering Emerson Jetty
puts you. Play it fresh from entering the level; do not carry over any moves.

All positions below are **relative to that start tile**, which is counted as
the origin. "2 east, 1 north" means two tiles east and one tile north of where
you were standing the moment the level began.

## Why

The replay runs the first 90 keys of this level with no refused moves at all, and
then refuses 56 of the remaining 106 — including pressing into the same wall five
times in a row. That pattern means the state drifted silently somewhere in the
first 90 keys and everything after is downstream of it. The checkpoints below
bracket that drift.

This is the first level that uses forking, so the two things most worth watching
are **when the fork first goes into the sausage** (the simulator says key 32) and
**when it comes back out** (the simulator says key 42).

## Key sequence

Five keys per row, with the running key number on the left. **These are compass
directions, not WASD letters** — "West" means walk/turn west, not the W key. An
earlier draft of this sheet abbreviated them to single letters, where `W` meant
west; that was too easy to misread as the up-key, so they are spelled out.

`Undo` is the game's undo.

| Keys | Presses | |
|---|---|---|
|  1-5  | West  Undo  West  West  South |
|  6-10 | North North North North North |  <-- checkpoint at key 10
| 11-15 | North East  West  West  West  |
| 16-20 | North South South West  West  |  <-- checkpoint at key 20
| 21-25 | West  West  West  South South |
| 26-30 | West  East  South East  East  |  <-- checkpoint at key 30
| 31-35 | North North East  East  North |  <-- checkpoint at key 32
| 36-40 | North East  East  East  South |  <-- checkpoint at key 40
| 41-45 | South South South West  South |
| 46-50 | North North North North East  |  <-- checkpoint at key 50
| 51-55 | East  South West  West  North |
| 56-60 | West  East  North North East  |  <-- checkpoint at key 60
| 61-65 | East  East  South East  West  |
| 66-70 | West  South South East  East  |  <-- checkpoint at key 70
| 71-75 | East  East  East  North West  |
| 76-80 | North South West  South East  |  <-- checkpoint at key 80
| 81-85 | West  West  West  West  West  |
| 86-90 | West  West  North South South |  <-- checkpoint at key 90
| 91-95 | South South South South West  |

## Checkpoints — what the simulator predicts

Please report where things **actually** are. Where we disagree is the bug.

| Key | Press | Player | Sausage | Carrying? |
|---|---|---|---|---|
| 10 | `NORTH` | 2 west, 5 north, facing South | 9 west, 3 north, lying East-West | no |
| 20 | `WEST` | 6 west, 4 north, facing West | 9 west, 3 north, lying East-West | no |
| 30 | `EAST` | 7 west, 3 north, facing East | 7 west, 4 north, lying East-West | no |
| 32 | `NORTH` | 7 west, 4 north, facing North | 7 west, 5 north, lying East-West | **yes** |
| 40 | `SOUTH` | 2 west, 5 north, facing North | 2 west, 6 north, lying East-West | **yes** |
| 50 | `EAST` | 2 west, 6 north, facing East | 2 west, 7 north, lying East-West | no |
| 60 | `EAST` | 1 west, 7 north, facing East | 6 north, lying East-West | no |
| 70 | `EAST` | 1 east, 6 north, facing South | 1 east, 5 north, lying East-West | **yes** |
| 80 | `EAST` | 3 east, 6 north, facing East | 6 east, 5 north, lying East-West | no |
| 90 | `SOUTH` | 4 west, 5 north, facing North | 6 east, 5 north, lying East-West | no |

## What to report

Most useful, in order:

1. The **first** checkpoint where the player position disagrees.
2. Whether the fork goes into the sausage at key 32, and if not, at which key.
3. At the first disagreement, what the previous few keys actually did.

If a checkpoint is awkward to read off, skip it — the first disagreement is worth
more than a complete table.
