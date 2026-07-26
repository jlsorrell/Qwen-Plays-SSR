# Manual check 007 — the world sausage journey (map corrected)

*The map in the previous version was drawn with a broken renderer that showed
raised ground as water. This one renders the topmost solid surface in each
column and has been verified against a structure of known shape.*

## Starting point

Complete **world 1** — all sixteen levels. A sausage appears at the large
structure with the plaque. Stand **4 tiles west and 1 tile south of it, facing
north**, then play the keys below.

```
0....000010111..0000000
00000011000001.....0011
01..0011000001......011
01.200101100........000
10..00100100...........
.00000000000......0000.
.......000.......000000
.................000000
.....0000000.....000110
.....0.0...000000000100
...0000....1010SS000000
...00000000@00000000000
............0000000000.
..000000000000000000000
......00...00000000.0.0
......00.00000000000000
.....00000000000...000.
......0000000000.000000
......000...000000...00
..000.000...00000..0.00
..000000000000000.0..00
..000..0000000000...00.
.....0000000.0000000000
```

- `@` you, `S` the two tiles of the sausage
- `0` ground level with you, `1` one step higher, `-` one lower, `.` nothing
- north is up

The big block of `0`s around and east of the sausage is the plaque structure's
plaza — it is **flush** with the ground you walk on, not raised. The single `1`
just west of the sausage is a raised block on that plaza.

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

`z` is undo — there are two, at keys 2 and 49.

## Checkpoints

Relative to where the sausage first appeared.

| After key | Sausage should be |
|---|---|
| 8 | 1 east, level |
| 16 | 7 east, level |
| 20 | 7 east, 2 north |
| 63 | 7 east, 3 north |
| 96 | 7 east, 4 north |
| 102 | **falls in the water** |

## Questions

**1. Which checkpoint first disagrees?** Stop there — the rest is meaningless
after a divergence, and knowing which one brackets the error to ten or twenty
moves.

**2. Does the map match now?** If it still looks wrong, that matters more than
the checkpoints, and I would rather know before you play 102 moves.

**3. Where is the sausage going?** If you can see the destination — another
structure, a gap it bridges — that tells me what the journey is for.
