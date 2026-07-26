"""Derive the `.dem`-to-level mapping from segment arithmetic plus replay.

`all.dem` is the concatenation of the 120 level `.dem` files in world order —
their lengths sum to exactly 16,567. So each file is a contiguous slice of the
continuous playthrough, and the level *solved* during slice N is the level that
file N names.

This recovers the mapping without the brute-force search in
`replay.find_matching_level`: it needs one replay pass rather than 120 per file,
and it is self-checking, since a derived pairing must also solve when replayed
against that level alone.

Coverage is bounded by how far the replay tracks. Everything after that point
needs overworld traversal fixed first (docs/mechanics.md 12.20).
"""

import json
from pathlib import Path

from ssr_env.dem import parse_dem_file
from ssr_env.level import (
    load_island_masks,
    load_overworld,
    load_overworld_meta,
    level_display_name,
)
from ssr_env.mechanics import check_level_exit, check_overworld_entry, step

DEM = Path(__file__).parent.parent / "data" / "dem"
OUT = Path(__file__).parent.parent / "data" / "dem_to_level.json"


def sort_key(name: str):
    world, _, rest = name.partition("-")
    if rest == "0":
        return (int(world), 0.0)
    if rest == "final":
        return (int(world), 999.0)
    return (int(world), float(rest))


def segments():
    """(`.dem` name, start, end) slices of all.dem, in world order."""
    names = sorted((p.stem for p in DEM.glob("*.dem") if p.stem != "all"), key=sort_key)
    out, at = [], 0
    for name in names:
        length = len(parse_dem_file(DEM / f"{name}.dem"))
        out.append((name, at, at + length))
        at += length
    return out


def main() -> None:
    inputs = parse_dem_file(DEM / "all.dem")
    bounds = segments()
    total = bounds[-1][2]
    print(f"120 segments total {total} moves; all.dem is {len(inputs)} — "
          f"{'match' if total == len(inputs) else 'MISMATCH'}")

    masks, meta = load_island_masks(), load_overworld_meta()
    state = load_overworld()
    history, mapping = [], {}
    for i, action in enumerate(inputs):
        result = step(state, action, history, masks)
        if result.lost:
            print(f"replay lost at move {i + 1}: {result.reason}")
            break
        was_in = state.pushtargetlevel
        state = check_level_exit(
            check_overworld_entry(result.state, meta, masks), meta, masks
        )
        if was_in and state.overworld:
            here = next((n for n, a, b in bounds if a <= i < b), None)
            if here and here not in mapping:
                mapping[here] = was_in

    OUT.write_text(json.dumps(mapping, indent=1, sort_keys=True))
    print(f"derived {len(mapping)}/120 pairings -> {OUT}")
    for name, level in sorted(mapping.items(), key=lambda kv: sort_key(kv[0])):
        print(f"  {name:8} {level:11} {level_display_name(level)!r}")


if __name__ == "__main__":
    main()
