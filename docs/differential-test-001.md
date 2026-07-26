# Differential test: first 35 inputs of `all.dem`

Start a **fresh save** and play these from the very first move of the game.
Keys are `W`/`A`/`S`/`D` = North/West/South/East, matching the game's bindings.

## Where this is

Not a single level — the overworld is one connected space, so these inputs walk
you out of the landing area and into the first sausages you meet.

| What | Level | In-game name |
|---|---|---|
| Where you start | `start` | **landing** |
| Sausage 4521 (the one I predict burns) and 4539 | `level56` | **Southjaunt** |
| Sausages 4505 and 4514 | `level49` | **Infant's Break** |
| Sausage 4474 | `level47` | **Lachrymose Head** |

**The sausage that burns at move 33 is Southjaunt's.** If the names on screen
don't match this ordering, that alone is a useful finding — it would mean the
overworld layout is assembled wrongly.

## The keys, in order

```
  1-10   A D D D D D W S S S
 11-20   D D D D W A S W A D
 21-30   S D A S A W A D D S
 31-35   D A A W W
```

## What I predict, and what to check

Coordinates are mine and won't match anything on screen — use them only to
read the shape of the movement. The three questions at the bottom are what
actually matter.

| # | Key | My predicted player pos | Facing | Sausage 4521 | rot | faces |
|---|---|---|---|---|---|---|
| 1 | A | (-4, -1, -1) | WEST | (0, 0, -1) | 0 | (0, 0, 0, 0) |
| 2 | D | (-3, -1, -1) | WEST | (0, 0, -1) | 0 | (0, 0, 0, 0) |
| 3 | D | (-2, -1, -1) | WEST | (0, 0, -1) | 0 | (0, 0, 0, 0) |
| 4 | D | (-1, -1, -1) | WEST | (0, 0, -1) | 0 | (0, 0, 0, 0) |
| 5 | D | (0, -1, -1) | WEST | (1, 0, -1) | 1 | (0, 0, 1, 0) |
| 6 | D | (1, -1, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 7 | W | (1, -1, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 8 | S | (1, -2, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 9 | S | (1, -3, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 10 | S | (1, -4, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 11 | D | (1, -4, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 12 | D | (1, -4, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 13 | D | (1, -4, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 14 | D | (1, -4, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 15 | W | (1, -3, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 16 | A | (1, -3, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 17 | S | (1, -3, -1) | SOUTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 18 | W | (1, -2, -1) | SOUTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 19 | A | (1, -2, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 20 | D | (2, -2, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 21 | S | (2, -2, -1) | SOUTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 22 | D | (2, -2, -1) | EAST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 23 | A | (1, -2, -1) | EAST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 24 | S | (1, -2, -1) | SOUTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 25 | A | (1, -2, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 26 | W | (1, -2, -1) | NORTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 27 | A | (1, -2, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 28 | D | (2, -2, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 29 | D | (3, -2, -1) | WEST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 30 | S | (3, -2, -1) | SOUTH | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 31 | D | (3, -2, -1) | EAST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 32 | A | (2, -2, -1) | EAST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 33 | A | (1, -2, -1) | EAST | (2, 0, -1) | 0 | (0, 0, 1, 1) |
| 34 | W | (1, -2, -1) | NORTH | (2, 1, -1) | 0 | (1, 0, 1, 3)  **<- BURNS HERE** |
| 35 | W | (1, -1, -1) | NORTH | (2, 1, -1) | 0 | (1, 0, 1, 3)  **<- BURNS HERE** |

## The three questions

**1. Does a Southjaunt sausage burn on move 33?**  The one that matters most.
My simulator says the sausage you cook early slides north along a grill at
move 33 and burns a face it already cooked. If nothing burns in the real
game, my divergence is somewhere in moves 1-32.

**2. Do moves 11, 12, 13 and 14 (four `D` presses in a row) do anything?**
I predict the player stands still facing North for all four, because a
sausage blocks where the fork would swing. If the character actually turns
or moves, my turn-blocking rule is wrong.

**3. Roughly where does the character end up by move 35?**  Not exact
coordinates - just whether the path looks like: walk west one, then east
five pushing a sausage, then south four, then a stretch of not much, then
north again. If the *shape* is wrong the divergence is early.

Anything else that looks off is worth telling me, especially a sausage
moving when you didn't expect it to.
