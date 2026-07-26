# Manual check 006 — is there ground here?

## Getting there

Complete world 1 (all sixteen levels). A sausage then appears at the big
structure — if that is the one with the plaque reading *"There were once great
people here..."*, that is what my code calls the shrine. Walk to it.

In my replay the character is standing just south-east of that sausage,
having walked up from the south, and is about to try walking **south** three
times in a row.

## What my model has

Top-down. `@` is where my character is standing, `S` is the world sausage,
`#` is ground you can walk on, `.` is water or empty, `?` is **the cell in
dispute** — my model says water, the recording walks into it.

```
##.#############.
##...###...##.#..
#############.#..
#####.#.#######..
#########........
########?........
########@#....###
#########....####
######.##....#.##
...###..##.....##
...#####S.....###
...######.#######
....####..#..####
..........######.
......###########
```

North is **up** in this picture.

## The question

**Standing where `@` is, can you walk south (down in this picture)?**

My model says no — the cell marked `?` is water, and three consecutive
south presses in the recording all do nothing. If in the real game you *can*
walk south from there, my overworld is missing ground at that spot.

If it is easier: just describe the shape of the land immediately south of the
structure. Is it a dead end, or does it continue?

## If the picture does not match at all

That is the more useful answer. It would mean my character is not where I
think it is by this point, and the shape of the land is the fastest way to
tell.
