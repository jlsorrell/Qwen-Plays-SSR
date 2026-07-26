# Manual check 007 — the world sausage journey

*Map corrected twice: it now renders the topmost solid **terrain** per column.
Earlier versions drew raised ground as water, and then drew the player's own
fork as a raised tile.*

## Starting point

Complete **world 1**. A sausage appears at the plaque structure. Stand **4 tiles
west and 1 tile south of it, facing north**, then play the keys below.

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
...0000....0010SS000000
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

- `@` you, `S` the sausage's two tiles
- `0` ground level with you, `1` one step up, `-` one down, `.` nothing
- north is up. The `1` two tiles west of the sausage is the plaque pedestal.

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

`z` is undo — two of them, at keys 2 and 49.

## Checkpoints

**What the numbers mean.** The sausage covers two tiles. These track its
**western tile**, and everything is measured from **where that tile first
appeared** — not from you, and not from the structure.

So "1 tile east" means the sausage has been pushed one tile east of where it
materialised. If it has been rolled onto its other axis the western tile is
still the reference; the facing column says which way it is lying.

| After key | The sausage's western tile is | Lying |
|---|---|---|
| 8 | 1 tile east, same row | east-west |
| 16 | 7 tiles east, same row | east-west |
| 20 | 7 tiles east, 2 tiles north | east-west |
| 63 | 7 tiles east, 3 tiles north | east-west |
| 96 | 7 tiles east, 4 tiles north | east-west |
| 102 | **falls in the water** | |

## Questions

**1. Which checkpoint first disagrees?** Stop there.

**2. Where is the sausage going?** The destination tells me what the journey
is for, which is worth as much as the coordinates.
