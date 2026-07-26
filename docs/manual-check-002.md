# Manual check 002 — the entry cell contradiction

Level `level49`, in-game name **Infant's Break** — the first level you enter.

## What I believe

- Entry cell: my coords `(1, -3, -1)`, entered facing **WEST**
- You observed the player reaching this cell **with the fork pointing east**
- A player there facing east puts its fork at `(2, -3, -1)`

My model says that fork cell contains a **sausage footprint** (mask value -1)
and that such cells are *solid* until the level is entered. If so, the player
could not stand there facing east — so one of those two beliefs is wrong.

## My map of the entry area

Top-down at the player's height. `E` = entry cell, `-1` = suspected sausage
footprint, `#` = other solid, `.` = open air.

```
y=0     .  .  . -1  .  . -1 -1 -1 -1
y=-1    .  .  .  .  .  .  .  .  .  .
y=-2    .  .  .  .  .  .  .  .  .  .
y=-3    .  .  .  .  E -1  .  .  .  .
y=-4    .  .  . -1 -1 -1  .  .  .  .
y=-5    . 11  .  .  .  .  .  .  .  .
y=-6    .  .  .  .  .  .  .  .  .  .
      -3 -2 -1  0  1  2  3  4  5  6
```

## The questions

**1. Stand on the first level's entry cell facing east (as in your earlier
run). Is there anything solid directly in front of the fork — a block, a
raised tile, anything the fork is resting against or inside?** Or is the fork
simply over open ground?

**2. Before you enter the level, can you see where the sausages will be?**
My model says unentered levels have solid placeholder blocks sitting exactly
where their sausages will appear. If the ground there looks ordinary and
walkable from the overworld, that belief is wrong.

**3. Does the shape above match what you see?** Especially whether the entry
cell sits at the *edge* of the island or has open ground east of it.

**4. Which way is the character facing at the instant the level starts?**

You wrote that `W` turns the player **north** and that drops them in. But my
extracted data says `level49` is entered facing **west**, and no level near
there is entered facing north. That is a plain disagreement about data I read
straight out of the game files, so it is worth pinning down.

If you are definitely facing north on entry, then either my island offsets are
wrong (which would shift every cell and could explain the contradiction on its
own), or the level you drop into is not the one I think it is.

## Which question matters most

**Question 2 is decisive for the contradiction.** If unentered levels show no
placeholder blocks where their sausages will be, then mask value `-1` marks
sausage positions without making them solid, and I have over-read the
`IslandAt` branch.

**Question 4 is decisive for everything else.** A facing mismatch would mean my
overworld coordinates are off, and every conclusion built on them — including
the map above — needs rechecking before anything else is worth debugging.

## Supporting evidence for the footprint reading

The four `-1` cells near the entry sit as two pairs: `(0,-4)-(1,-4)` and
`(2,-4)-(2,-3)`. `level49` has exactly two sausages, and the spawn table places
them at those same coordinates. So `-1` marking sausage positions is well
supported; only its *solidity* is in question.
