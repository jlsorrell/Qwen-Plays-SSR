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

Add `--json PATH` for machine-readable output. Move numbers shown to users are
one-based; JSON also includes the zero-based `input_index`.
