# Manual check 003 — ANSWERED WITHOUT REPLAYING

Not needed. Computing the predicted move-35 position against `level47`'s own
island surface (rather than the whole walkable area, which is still oversized
because `TryLowerAll` is unimplemented) gives:

```
predicted:  panel (2,1) facing North
reported:   panel (2,1) facing north
```

Exact match, facing included. The island measures 5 x 4 tiles, consistent with
the owner's "4x4 grid of panels" allowing for an edge.

## Moves 1-35 are verified

All three independent observations now agree with the simulator:

| Observation | Owner | Simulator |
|---|---|---|
| Level entry | move 15, Lachrymose Head, facing north | move 15, level47, facing north |
| First sausage contact | move 22 | move 22 |
| Position at move 35 | panel (2,1) facing north | panel (2,1) facing North |

This is the first stretch of the project that is *verified* rather than merely
self-consistent. It exercises the overworld walk, level entry, sausage spawning,
both turn phases, pushing, rolling and gravity.

## Still open

Replay dies at **move 112**, player drowning, roughly 90 moves into the level.
The useful observation there — whenever it is convenient, and only if the level
is reachable from a save — is whether a sausage goes into the water around moves
100-115, and whether the level is solved before then.

Also still unimplemented and now visible: `TryLowerAll` / `TryRaiseAll`. Entering
a level should sink the surrounding islands so the player is confined to the
level's own island. Without it the player can wander off level47 onto
neighbouring terrain, which is a plausible cause of the move-112 drowning.
