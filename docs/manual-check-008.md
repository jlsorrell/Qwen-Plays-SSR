# Manual check 008 — player checkpoints, keys 1-47

Check 007's checkpoints tracked only the sausage, which does not move between
keys 20 and 63 in my model — so a player divergence in that stretch was
invisible. You found it anyway: key 47 enters a level here, and in my
simulator the player is stuck at an island's edge, 11 tiles from any entrance.

This check tracks **the player**, every five keys.

## Starting point

Complete **world 1**, finishing with **The Anchorage**. The game returns you to
its entrance facing north, with the world sausage at the plaque. The first key
below is the very next input. Do not walk anywhere first.

## Keys (first 47)

```
   1-10    A z A D D D D W W A
  11-20    D D D D D D S D W D
  21-30    A W W W A D D D D D
  31-40    D D D W S A S D D D
  41-47    S W W D D D D
```

`z` is undo — at keys 2 and 49 (only the first falls in this range).

## Player checkpoints

Positions are relative to **where you start** — the Anchorage entrance.
Facing is which way the fork points.

| After key | You should be | Facing |
|---|---|---|
| 5 | 2 east | West |
| 10 | 4 east, 1 north | West |
| 15 | 9 east, 1 north | West |
| 20 | 10 east, 1 north | East |
| 25 | 9 east | West |
| 30 | 12 east | West |
| 35 | 12 east | North |
| 40 | 12 east | East |
| 45 | 12 east | East |

## The sausage, for reference

| After key | Sausage's western tile |
|---|---|
| 8 | 1 east |
| 16 | 7 east |
| 20 | 7 east, 2 north |
| 47 | 7 east, 2 north |

## What I most need

**The first player checkpoint that disagrees.** Stop there. That brackets the
fault to five keys, which is small enough for me to find by inspection.

**And at key 47: which level do you enter?** Its name would tell me directly
which entrance I am failing to place — my model has no entrance within 11 tiles
of where it thinks you are.

## Note on my key 44

My simulator turns you east at key 44 and then refuses keys 45, 46 and 47 —
pressing east into open water. If you are instead walking east there, the
divergence is at or before key 44 and the checkpoints at 40 and 45 will show it.
