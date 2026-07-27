# Manual check 006 — is there ground south of the shrine sausage?

*(An earlier version of this map was printed upside-down — north is `-y` and I
was printing rows the wrong way. This one is correct.)*

## Getting there

Complete world 1 — all sixteen levels. A sausage then appears at a large
structure. If that is the one with the plaque reading *"There were once great
people here, but now there is something even greater"*, that is what the code
calls a shrine and what I mean below.

## What my model has

```
......###########
..........######.
....####..#..####
...######.#######
...#####S.....###
...###..##.....##
######.##....#.##
#########....####
########@#....###
########?........
#########........
#####.#.#######..
#############.#..
##...###...##.#..
##.#############.
```

**North is up. South is down.**

- `@` where my character stands
- `S` the world sausage that appeared after world 1
- `#` ground you can stand on, `.` water or empty
- `?` **the cell in dispute** — one step SOUTH of `@`

## The question

**Standing where `@` is, can you walk one step south (down)?**

My model says no: `?` is water. The recording presses south three times in a
row there, which only makes sense if it is walkable. If you can walk south,
my overworld is missing ground at that spot.

## Easier alternative

If lining up with `@` is fiddly, this is just as useful: **stand at the world
sausage and describe the land to its south** — dead end, narrow path,
open area? Any mismatch with the picture tells me what I need.

And if the picture looks nothing like what you see, say so — that would mean
my character is not where I think it is, which is more important than the
ground question.
