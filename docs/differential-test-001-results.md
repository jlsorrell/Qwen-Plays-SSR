# Differential test 001 — results

Observed by the project owner against the real game, 2026-07-24.

## Answers

**1. Nothing burns.** My predicted burn at move 33 does not occur. The
divergence is upstream and the burn was only where it surfaced.

**2. Moves 11-14 do something.** The four consecutive `D` presses turn the
player east at the bottom panel of the island, then walk them to the starting
position of the first level with the fork pointing east. Move 15 (`W`) turns the
player north and **drops them into the first level**.

**3. The opening is a 4x4 grid of panels.** Numbering the northwest corner
(1,1), south of it (2,1), east of it (1,2), and the southeast corner (4,4): at
move 35 the player is at panel **(2,1) facing north**.

## The structural finding

> "The player is not in a level with a sausage until move 15, so move 16 is the
> first move in the level, and move 22 is the first move that contacts a sausage."

My simulation pushes a sausage at **move 4** and cooks two of its faces by move
5. The real game does not touch a sausage until **move 22**. That is not a small
drift — it means the opening 15 moves happen somewhere with no sausages at all.

Two things follow, and both contradict `load_overworld` as built:

1. **Sausages are not present in the overworld.** They are *issued* on entering
   a level — the `IssueWorldSausages` / `ShouldIssueSausage` /
   `SpawnSubworldSausages` / `DespawnSubworldSausages` family, which I had noted
   and never wired up. Merging all 220 sausages into one world put them
   underfoot during the overworld walk.

2. **Levels are subworlds you drop into, not contiguous ground you walk across.**
   "Drops them into the first level" is a transition, and the game has
   `SubworldTransition` and `SubworldLeave` for exactly this. The overworld
   terrain *is* built from the island chunks, which is why the offsets place
   everything in one coordinate space — but walking on top of an island and
   being inside its level are different states.

So the §12.6 claim that "the overworld is not a separate scene" is **half
right**: one coordinate space, but not one play space. The composite world is a
correct picture of the geometry and a wrong picture of the state.

## Also confirmed wrong

Moves 11-14 turn and move in the real game; my simulator refuses all four
because a sausage sits where the fork would swing. With no sausages present in
the overworld that blocker does not exist — so this is likely a *symptom* of
finding 1 rather than an independent turn bug. Worth re-checking after sausages
are removed from the overworld, before touching the turn rules.

## What to fix, in order

1. Build the overworld **without** sausages; issue them on level entry.
2. Model the subworld transition, so "drop into the level" is a state change.
3. Re-run and compare against these observations: no sausage contact before
   move 22, level entry at move 15, player at panel (2,1) facing north at 35.
