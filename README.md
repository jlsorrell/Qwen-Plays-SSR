# Qwen Plays Stephen's Sausage Roll

Pure-Python reference simulator and replay tooling for research on learned
heuristics in open-weights models trained to solve Stephen's Sausage Roll.

## Test

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

The standalone official replay cases remain xfailed until their independent
initial-state mappings are validated. The continuous replay regression test
protects the confirmed clean prefix.

## Audit the official continuous replay

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py
```

Trace the first failing segment with bounded context:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/level_audit.py \
  --limit 21 --trace failures --segment 2-3
```

Add `--json PATH` for machine-readable output. Move numbers shown in the human
table and trace are one-based. JSON fields ending in `_at` retain their
established stored meanings: `entered_at` and `completed_at` are zero-based
input indices, while `lost_at` and `failure_at` are one-based move numbers.
Trace events likewise include zero-based `input_index` and `segment_index`
alongside one-based `global_move` and `segment_move`.
