# Manual check 007 — the world sausage journey

## Starting point

Complete **world 1** — all sixteen levels. A sausage then appears at the large
structure (the one with the plaque). Do not move it yet.

**Then position yourself: 4 tiles west and 1 tile south of the sausage, facing
north.** The key sequence begins from there.

```
  #########......##
  ....###.......###
  ..............###
  ..#######.....###
  ..#.#...#########
  ####.....#.#SS###     <- the sausage, lying east-west
  ########@########     <- you, facing north
  .........########
  #################
```

North is up. `@` is you, `SS` is the two tiles of the sausage, `#` is walkable
ground and `.` is water or empty.

That position is simply where the recorded playthrough happens to be standing
when the sausage appears — it walks there while finishing the last level. If
you arrive facing some other way, turn to face north before starting; a turn
costs a move and would shift the whole sequence by one.

## Keys (102 moves)

```
   1-10    A z A D D D D W W A
  11-20    D D D D D D S D W D
  21-30    A W W W A D D D D D
  31-40    D D D W S A S D D D
  41-50    S W W D D D D A z A
  51-60    A S W W W W W W D A
  61-70    A A W S S A A A A A
  71-80    S S A D S D D W W D
  81-90    D W W D D D S S S S
  91-100   A S W W W W D D S A
 101-102   A W
```

`z` is undo. There are a few in this stretch.

## Checkpoints

Positions are given **relative to where the sausage first appeared**, since my
own coordinates will not mean anything to you. "East" and "north" are as they
appear on screen.

| After key | I predict the sausage is |
|---|---|
| 8 | 1 east, level with |
| 16 | 7 east, level with |
| 20 | 7 east, 2 north |
| 30 | 7 east, 2 north |
| 45 | 7 east, 2 north |
| 63 | 7 east, 3 north |
| 96 | 7 east, 4 north |

| 102 | **falls into the water** |

## The questions

**1. Does the sausage ever fall in the water?** My replay says it does, at
key 102. If it never does, the divergence is somewhere before that.

**2. Which checkpoint first disagrees?** That is the most useful single fact —
it brackets the error to a stretch of ten or twenty moves. Stop as soon as one
is wrong; the rest is meaningless after that.

**3. Roughly, where is the sausage going?** If you can see the intended
destination — another structure, a gap to bridge, somewhere it slots in —
that tells me what the journey is *for*, which is worth as much as the
coordinates.

## If the very first checkpoint is already wrong

Then the error is in the first eight moves after the sausage appears, which
would be the easiest possible case. Say so and stop.
