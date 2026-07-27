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

Keys 1-20: `W` `U` `W` `W` `S` `N` `N` `N` `N` `N` `N` `E` `W` `W` `W` `N` `S` `S` `W` `W`

Keys 21-40: `W` `W` `W` `S` `S` `W` `E` `S` `E` `E` `N` `N` `E` `E` `N` `N` `E` `E` `E` `S`

Keys 41-60: `S` `S` `S` `W` `S` `N` `N` `N` `N` `E` `E` `S` `W` `W` `N` `W` `E` `N` `N` `E`

Keys 61-80: `E` `E` `S` `E` `W` `W` `S` `S` `E` `E` `E` `E` `E` `N` `W` `N` `S` `W` `S` `E`

Keys 81-100: `W` `W` `W` `W` `W` `W` `W` `N` `S` `S` `S` `S` `S` `S` `W` `E` `E` `E` `E` `E`

(`W`=north, `S`=south, `A`=west, `D`=east, `U`=undo — whichever bindings you use;
the names above are the compass directions the demo recorded.)

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
