# Replay Diagnostics and Regression Gate

**Date:** 2026-07-27  
**Status:** Approved for implementation planning

## 1. Purpose

The simulator currently passes 484 unit tests, but all 120 official replay
acceptance cases are marked `xfail`. Separately, `tools/level_audit.py` shows
that the continuous `all.dem` replay cleanly completes the first 18 levels
before diverging in world 2 level 3 (`levelb11`). Those 18 confirmed levels are
not protected by the normal test suite, and the audit records a loss reason
without the exact move that first caused it.

This milestone will turn replay progress into an automated regression gate and
make the first divergence inspectable without repeatedly adding one-off print
statements or asking for broad manual playthroughs.

It will not change simulator mechanics. Mechanics fixes will follow only after
the diagnostics layer is tested and can demonstrate a precise failing
transition.

## 2. Scope

The milestone will:

1. Extract continuous replay observation from the command-line audit into a
   reusable library module.
2. Record global and segment-relative input indices.
3. Record level entry, level completion, refusal, loss, and dynamic entity
   changes.
4. Expose concise human-readable output and stable JSON output.
5. Preserve the existing per-segment audit table.
6. Add an automated acceptance test for the confirmed 18-level clean prefix.
7. Report the first divergence in `levelb11` with its exact input index and
   state changes.

The milestone will not:

- modify movement, turning, pushing, cooking, gravity, or transition rules;
- claim that segments after a forced resynchronization are independently valid;
- derive the remaining `.dem`-to-level mappings;
- reconstruct arbitrary standalone entry states for all 120 demonstrations;
- replace human differential testing where the game is the only available
  authority.

## 3. Architecture

### 3.1 Library boundary

A new module, `src/ssr_env/diagnostics.py`, will contain replay-observation
types and pure comparison helpers. It will not print, parse command-line
arguments, or load files.

The existing `tools/level_audit.py` will remain responsible for:

- loading `all.dem`, overworld metadata, and island masks;
- defining segment boundaries and the current partial resynchronization policy;
- formatting the audit table;
- writing JSON requested by the CLI.

This keeps mechanics execution in `ssr_env.mechanics.step`, diagnostic
interpretation in the package, and user-interface concerns in the tool.

### 3.2 Data flow

For every input:

1. The audit retains the pre-step `GameState`.
2. It calls `step()` exactly once.
3. The diagnostics module compares the pre-step and post-step states.
4. It emits a trace event only when something relevant changed or when the
   input was refused or caused a loss.
5. The audit attaches global and segment-relative indices and stores the event
   on the segment.

No diagnostic code may mutate either state or influence replay behavior.

## 4. Diagnostic model

### 4.1 Entity snapshot

Dynamic snapshots cover players and sausages. Each snapshot contains:

- entity id and type;
- position;
- direction;
- sausage `rot` and four cook-face values;
- `stuckto`;
- sausage status prefix from `dat`.

Static geometry is excluded because it does not change during ordinary level
play. Island movement and level transitions are represented as transition
events rather than by dumping all island entities.

### 4.2 Step trace

Each trace event contains:

- one-based global move number;
- zero-based input index, for direct indexing into parsed input arrays;
- segment name;
- one-based move number within that segment;
- input token;
- whether the player move was accepted;
- refusal or loss reason, when present;
- level before and after the step;
- solved/completed transition, when present;
- changed dynamic entities, each with before and after snapshots.

An entity spawned during entry has `before = null`; an entity removed during
exit has `after = null`.

### 4.3 Segment result

The existing `Segment` result will gain:

- `lost_at`: the first global move that produced `lost_reason`;
- `failure_at`: the first global move associated with an exception,
  unimplemented mechanic, or loss;
- `events`: diagnostic events retained according to the selected trace mode.

`status` remains backward-compatible. The table adds an `at` column rather than
changing existing status strings.

## 5. Command-line interface

The existing command remains valid:

```bash
uv run python tools/level_audit.py
```

New options:

```text
--trace none|failures|changes
--segment NAME
--json PATH
```

- `none` is the default and preserves concise audit behavior.
- `failures` includes the event at the first failure and a small bounded window
  of preceding change events.
- `changes` includes all relevant events for the selected run.
- `--segment` filters displayed and serialized traces to a named `.dem`
  segment. Replay still begins at the start of `all.dem`, because the selected
  segment may depend on prior overworld state.

JSON will use ordinary dictionaries, lists, strings, integers, booleans, and
nulls. Enum values will be serialized by name and coordinates as three-element
lists. This makes output stable and usable without importing the package.

## 6. Failure handling

- `UnimplementedMechanic` remains a named audit error and records its move.
- Unexpected exceptions remain isolated to the current segment and include the
  exception type and message.
- A loss records only its first occurrence; later inputs cannot overwrite the
  root failure location.
- Trace history is bounded in `failures` mode to prevent the 16,567-move corpus
  from producing excessive output.
- JSON writing happens only after replay finishes, so partial files are not
  presented as successful audit output.

## 7. Testing strategy

### 7.1 Unit tests

Tests for `ssr_env.diagnostics` will use small real `GameState` values and
verify:

- unchanged entities do not appear in deltas;
- movement, direction, carrying, rotation, and cook-face changes do appear;
- spawn and removal use null on the absent side;
- serialized coordinates and enums are stable primitives;
- trace objects do not mutate input states.

### 7.2 Audit tests

Tests for the audit will verify:

- segment-relative indices are correct at boundaries;
- the first loss index is retained even if replay continues;
- `failures` mode includes a bounded preceding window;
- filtering changes display/serialization, not replay initialization;
- old invocations without trace options remain valid.

### 7.3 Acceptance gate

One integration test will run the continuous replay far enough to assert:

- the first 18 levels complete in the known order;
- every one has a clean run-up;
- the next level under test is `levelb11`;
- no earlier loss or audit error occurs.

The test will avoid asserting the current buggy burn as desired behavior.
Instead, it brackets the first unconfirmed transition so a future mechanics fix
can move the frontier forward without rewriting the test.

The existing 120 `xfail` replay cases remain until their standalone mapping and
initial-state assumptions are valid. They will not be presented as meaningful
acceptance coverage.

## 8. Acceptance criteria

The milestone is complete when:

1. The existing 484 passing tests still pass.
2. The 18-level continuous prefix is enforced by an automated test.
3. Running the audit identifies the first `levelb11` loss at its exact global
   and segment-relative move.
4. Failure tracing shows the player and sausage changes leading into that loss.
5. JSON output contains the same indices, reasons, transitions, and entity
   deltas as the human-readable trace.
6. No simulator mechanics behavior changes in the milestone diff.

