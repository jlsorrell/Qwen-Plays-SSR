# Manual check 004 — moves 100-115

Fresh save, from the game's first move. `W`/`A`/`S`/`D` = North/West/South/East.

This is a long sequence, so there are checkpoints. If a checkpoint disagrees,
**stop there and tell me** — everything after it is meaningless, and the
disagreement itself is the useful information.

## Keys

```
   1-10    A D D D D D W S S S
  11-20    D D D D W A S W A D
  21-30    S D A S A W A D D S
  31-40    D A A W W W D W S D
  41-50    W S D D D D D W A A
  51-60    W A A A A S S D S W
  61-70    A D D A A W W W D S
  71-80    S D D D D W S A A A
  81-90    A W S W W W W D A A
  91-100   A W S A A S S S S A
 101-110   D D D S W W D W W D
 111-112   A A
```

## Checkpoints

Panels use your numbering: NW corner (1,1), south of it (2,1), east of it (1,2).

| After move | I predict the character is on | Facing |
|---|---|---|
| 15 | panel (4,1) | North |
| 22 | panel (3,2) | East |
| 35 | panel (2,1) | North |
| 50 | panel (3,4) | West |
| 70 | panel (1,1) | South |
| 90 | panel (0,-1) | East |
| 100 | panel (3,-2) | West |
| 110 | panel (0,-3) | East |

## What I predict happens

- Level entry at move 15, first sausage contact at move 22 (both already confirmed)
- **Move 112: a sausage or the player goes into the water** — my replay reports `Drowned`

## The questions

**1. Around moves 100-115, does anything fall in the water?** My replay says
yes at move 112. If nothing does, my simulation is diverging before then.

**2. Is Lachrymose Head already solved before move 112?** If the level is
completed earlier, then my replay is running past its end and the drowning is
an artefact of not detecting the win.

**3. Did any checkpoint above disagree?** That is more valuable than the
answers to 1 and 2, because it localises the divergence.

Question 2 is worth answering even if you stop early — if the level ends around
move 90 or 100, questions 1 and 3 stop mattering.
