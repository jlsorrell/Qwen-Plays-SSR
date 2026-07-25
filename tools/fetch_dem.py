"""Download the .dem solution corpus from SSRDecompile into data/dem/.

Source: https://github.com/jbzdarkid/SSRDecompile (Apache-2.0)

These are recorded winning input sequences for the official levels. They are the
simulator's acceptance suite (spec §5.1). Note they are *demonstrations*, not
optimal solutions — they wander and use Undo — so they validate the simulator but
are not suitable as SFT data.
"""

import json
import urllib.request
from pathlib import Path

TREE = "https://api.github.com/repos/jbzdarkid/SSRDecompile/git/trees/main?recursive=1"
RAW = "https://raw.githubusercontent.com/jbzdarkid/SSRDecompile/main/"
DEST = Path(__file__).parent.parent / "data" / "dem"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(TREE) as resp:
        tree = json.load(resp)["tree"]
    paths = [e["path"] for e in tree if e["path"].endswith(".dem")]
    for path in sorted(paths):
        target = DEST / Path(path).name
        with urllib.request.urlopen(RAW + path) as resp:
            target.write_bytes(resp.read())
        print(f"{target.name}: {len(target.read_text().splitlines())} moves")
    print(f"\n{len(paths)} files -> {DEST}")


if __name__ == "__main__":
    main()
