"""Extract official level geometry from the owner's game install.

Levels live in the Unity TextAsset `Generated/merged_binary` inside
`resources.assets`. It is a .NET `BinaryWriter` stream whose layout is given by
`MetaGameState.LoadBinary`. This module replays that read sequence.

The parse is self-validating: the level data sits at the very end of the stream,
so if every preceding section is read with the correct layout the reader lands
exactly on EOF. A wrong layout desynchronises and fails loudly rather than
producing plausible garbage.

Requires the `extract` extra:  uv run --extra extract python tools/extract_levels.py
"""

import argparse
import json
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_DATA_DIR = Path(
    "~/Library/Application Support/Steam/steamapps/common/"
    "Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data"
).expanduser()

DEST = Path(__file__).parent.parent / "data" / "levels"


class BinaryReader:
    """Minimal port of .NET BinaryReader for the subset the format uses."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def read_int32(self) -> int:
        (value,) = struct.unpack_from("<i", self.data, self.pos)
        self.pos += 4
        return value

    def read_bytes(self, count: int) -> bytes:
        chunk = self.data[self.pos : self.pos + count]
        if len(chunk) != count:
            raise EOFError(f"wanted {count} bytes at {self.pos}, got {len(chunk)}")
        self.pos += count
        return chunk

    def read_string(self) -> str:
        """.NET writes a 7-bit-encoded-int length prefix, then UTF-8 bytes."""
        length = 0
        shift = 0
        while True:
            byte = self.data[self.pos]
            self.pos += 1
            length |= (byte & 0x7F) << shift
            if not byte & 0x80:
                break
            shift += 7
            if shift > 35:
                raise ValueError(f"malformed string length prefix at {self.pos}")
        return self.read_bytes(length).decode("utf-8")

    def read_coord(self) -> tuple[int, int, int]:
        return (self.read_int32(), self.read_int32(), self.read_int32())

    @property
    def at_eof(self) -> bool:
        return self.pos == len(self.data)


def parse_merged_binary(data: bytes) -> tuple[dict[str, str], dict[str, dict], dict]:
    """Return (levels, island_masks), following MetaGameState.LoadBinary.

    levels maps level name -> state string; island_masks maps island name ->
    {"offset": [x,y,z], "mask": int[a][b][c]}.
    """
    r = BinaryReader(data)
    island_masks: dict[str, dict] = {}
    meta: dict[str, dict] = {"offsets": {}, "sausages": {}, "player": {}, "temples": {}}

    # offsets: name -> coord. This is the overworld layout — where each level's
    # island chunk sits in overworld space.
    for _ in range(r.read_int32()):
        name = r.read_string()
        meta["offsets"][name] = list(r.read_coord())

    # sausagepositions: name -> [(coord, direction)]
    for _ in range(r.read_int32()):
        name = r.read_string()
        meta["sausages"][name] = [
            {"pos": list(r.read_coord()), "direction": r.read_int32()}
            for _ in range(r.read_int32())
        ]

    # playerpositions: name -> (coord, direction)
    for _ in range(r.read_int32()):
        name = r.read_string()
        meta["player"][name] = {
            "pos": list(r.read_coord()),
            "direction": r.read_int32(),
        }

    # templedat: temple name -> [level names], the overworld grouping
    for _ in range(r.read_int32()):
        name = r.read_string()
        meta["temples"][name] = [r.read_string() for _ in range(r.read_int32())]

    # islandmasks: name -> (int[a][b][c], coord offset)
    # Kept: masks carry each island chunk's shape and its ladder encoding
    # (GameState.LadderAt reads values 3..6 as ladder directions).
    for _ in range(r.read_int32()):
        name = r.read_string()
        a, b, c = r.read_int32(), r.read_int32(), r.read_int32()
        flat = struct.unpack_from(f"<{a * b * c}i", r.data, r.pos)
        r.pos += 4 * a * b * c
        mask = [
            [list(flat[(i * b + j) * c : (i * b + j) * c + c]) for j in range(b)]
            for i in range(a)
        ]
        island_masks[name] = {"offset": list(r.read_coord()), "mask": mask}

    # projectioncompatibilities: name -> name -> bool[w, h]
    for _ in range(r.read_int32()):
        r.read_string()
        for _ in range(r.read_int32()):
            r.read_string()
            w, h = r.read_int32(), r.read_int32()
            r.read_bytes(w * h)

    # coastdat and splashdat: name -> int -> [coord]
    for _ in range(2):
        for _ in range(r.read_int32()):
            r.read_string()
            for _ in range(r.read_int32()):
                r.read_int32()
                for _ in range(r.read_int32()):
                    r.read_coord()

    # bbqdat: name -> [coord]
    for _ in range(r.read_int32()):
        r.read_string()
        for _ in range(r.read_int32()):
            r.read_coord()

    # treedat: name -> [(coord, int)]
    for _ in range(r.read_int32()):
        r.read_string()
        for _ in range(r.read_int32()):
            r.read_coord()
            r.read_int32()

    overworld = r.read_string()
    levels: dict[str, str] = {"__overworld__": overworld}
    for _ in range(r.read_int32()):
        name = r.read_string()
        levels[name] = r.read_string()

    if not r.at_eof:
        raise ValueError(
            f"parse desynchronised: {len(r.data) - r.pos} bytes left after "
            f"reading {len(levels) - 1} levels"
        )
    return levels, island_masks, meta


@dataclass(frozen=True)
class RawEntity:
    """One entity as serialised by Entity.SaveToString."""

    x: int
    y: int
    z: int
    type: int
    id: int
    direction: int
    dat: str
    stuckto: int
    rot: int
    cookdata: int
    turndir: int
    tilenum: int
    tileset: int
    pivot: int


def parse_level_metadata(text: str) -> dict:
    """Parse the '*'-separated metadata that follows the entity records.

    Field order, per `GameState.LoadDat`:
        0 entities | 1 levelcompleted | 2 worldsausagesissued | 3 tileset
        4 displayname | 5 sausagescooked | 6 musicseed

    `tileset` is load-bearing: `Entity.Decoration()` consults the level-wide
    tileset alongside each entity's own, and `Solid()` is `!Decoration()`.
    """
    f = text.split("*")
    def field(i: int, default: str = "") -> str:
        return f[i] if len(f) > i and f[i] else default
    return {
        "tileset": int(field(3, "0")),
        "display_name": field(4),
        "music_seed": int(field(6, "0")),
    }


def parse_level_string(text: str) -> list[RawEntity]:
    """Parse a level state string into entities, following `GameState.LoadDat`.

    Only the segment before the first '*' holds entity records; everything after
    is level metadata (see `parse_level_metadata`). Records are '|'-separated.
    A leading record beginning 'F' or 'I' is a flag rather than an entity: 'I'
    carries pushtargetlevel, 'F' is a bare marker. Both are skipped here.

    Field order is `Entity.SaveToString`:
        x,y,z,type,id,direction,dat,stuckto,rot,<unused 0>,cookdata,turndir,
        tilenum,tileset,pivot,|
    """
    entities: list[RawEntity] = []
    records = [r.strip() for r in text.split("*")[0].split("|") if r.strip()]
    if records and records[0][0] in "FI":
        records = records[1:]
    for record in records:
        f = record.split(",")
        if len(f) < 15:
            raise ValueError(f"expected >=15 fields, got {len(f)}: {record!r}")
        entities.append(
            RawEntity(
                x=int(f[0]), y=int(f[1]), z=int(f[2]), type=int(f[3]), id=int(f[4]),
                direction=int(f[5]), dat=f[6], stuckto=int(f[7]), rot=int(f[8]),
                cookdata=int(f[10]), turndir=int(f[11]), tilenum=int(f[12]),
                tileset=int(f[13]), pivot=int(f[14]),
            )
        )
    return entities


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    ap.add_argument("--dest", type=Path, default=DEST)
    ap.add_argument("--dump-raw", action="store_true", help="also write raw level strings")
    args = ap.parse_args()

    import UnityPy

    env = UnityPy.load(str(args.data_dir / "resources.assets"))
    blob = None
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        d = obj.read()
        if (getattr(d, "m_Name", None) or getattr(d, "name", "")) == "merged_binary":
            script = getattr(d, "m_Script", None)
            if script is None:
                script = d.script
            blob = script.encode("utf-8", "surrogateescape") if isinstance(script, str) else bytes(script)
            break
    if blob is None:
        raise SystemExit("merged_binary TextAsset not found in resources.assets")

    print(f"merged_binary: {len(blob):,} bytes")
    levels, island_masks, meta = parse_merged_binary(blob)
    print(
        f"parsed {len(levels) - 1} levels + overworld and "
        f"{len(island_masks)} island masks, landed exactly on EOF"
    )

    args.dest.mkdir(parents=True, exist_ok=True)
    for name, text in levels.items():
        ents = parse_level_string(text)
        payload = {
            "name": name,
            **parse_level_metadata(text),
            "entities": [asdict(e) for e in ents],
        }
        if args.dump_raw:
            payload["raw"] = text
        (args.dest / f"{name}.json").write_text(json.dumps(payload, indent=1))
    (args.dest / "__islandmasks__.json").write_text(json.dumps(island_masks))
    (args.dest / "__overworld_meta__.json").write_text(json.dumps(meta, indent=1))
    print(f"wrote {len(levels)} levels + island masks -> {args.dest}")


if __name__ == "__main__":
    main()
