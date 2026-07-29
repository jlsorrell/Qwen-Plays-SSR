# Executable Game-State Oracle

**Date:** 2026-07-27  
**Status:** Approved for implementation planning

## 1. Purpose

The Python simulator now replays the first 18 levels of the continuous
`all.dem` demonstration without a known divergence. It later loses in
`levelb11` (Cove), currently observed at global move 1241 / segment move 37.
Source comparison shows that the simulator agrees with the decompiled game at
the final burning transition when given the same pre-state, and that Cove's
initial geometry and entity data also agree. The first incorrect transition
must therefore occur earlier than the visible loss.

Manual playthroughs can bracket a divergence, but they do not expose the
game's complete state after every input. Repeating that process across later,
more complicated mechanics would require an increasing amount of manual
verification.

This milestone will make the installed macOS game an automated executable
oracle. A reversible BepInEx plugin will feed the official demonstration
inputs through the game's normal input path, capture the game's own serialized
state after each input settles, and write a deterministic trace. A Python
comparator will replay the same inputs in the simulator and identify the first
field-level mismatch.

The oracle will compare settled input boundaries. It will not attempt to make
the Python simulator reproduce Unity animation frames or the game's internal
fractional movement ticks.

## 2. Success criteria

The milestone succeeds when:

1. The unmodified game launches through the BepInEx wrapper on macOS 15.7.3.
2. The plugin captures an initial state and exactly one terminal record for
   every submitted direction or undo.
3. A short manual sequence proves that accepted, refused, and undo inputs are
   distinguishable and reproducible.
4. The oracle and simulator compare equal throughout the currently confirmed
   18-level prefix.
5. The automated run reports the first exact state mismatch before the
   existing Cove loss.
6. The mismatch can be converted into a focused failing Python regression
   test without another full manual playthrough.
7. Installation and removal leave `Sausage.app`, `Assembly-CSharp.dll`, and
   the user's normal save data unchanged.

## 3. Scope

### 3.1 Included

- A C# BepInEx plugin for the Unity Mono macOS build of Stephen's Sausage Roll.
- A passive capture mode for validating the observation boundary with normal
  keyboard play.
- A replay mode that consumes the repository's `.dem` token format.
- Settled-state capture using the game's own `GameState.Save`.
- Append-only, versioned NDJSON traces.
- A Python parser, normalizer, and first-divergence comparator.
- An idempotent install/deploy workflow and a manifest-based uninstall
  workflow.
- Unit tests that do not require launching the game, plus a separately invoked
  end-to-end oracle check.

### 3.2 Excluded

- Modifying or replacing the game assembly.
- Reading or writing game state through external process memory.
- Modeling transient render frames, audio, particle effects, or camera state.
- Automatically fixing simulator mechanics in the same change as the oracle.
- Treating all 120 level demonstrations as independent level fixtures.
- Committing full locally generated oracle traces to Git.
- Building the model-training pipeline in this milestone.

## 4. Repository layout

The implementation will use the following boundaries:

```text
oracle/
  plugin/                  C# BepInEx plugin project
  README.md                build, install, run, and removal instructions
tools/
  oracle_install.py        manifest-tracked local installation
  oracle_compare.py        trace parsing and first-divergence CLI
src/ssr_env/
  oracle.py                trace schema, normalization, and comparison
tests/
  test_oracle.py           dependency-free Python tests
data/oracle/               local traces; ignored by Git
```

The exact compiled plugin and BepInEx runtime will be deployment artifacts,
not source-controlled binaries unless a later review explicitly chooses to
vendor them.

## 5. Runtime architecture

### 5.1 Integration boundary

The plugin will locate the active public `Game` MonoBehaviour and read its
current public `gamestate` field on every capture. It will not retain a
`GameState` reference across level load, undo, restart, or overworld
transitions.

Directional replay inputs will enter through the same high-level path as
keyboard inputs:

1. A Harmony patch on the private `Game.Playerinputstring` method supplies one
   queued direction for one eligible update.
2. The unmodified `Game.DoPlayerInput` method performs the input gate, undo
   snapshot management, `CalcBBQAshSteps`, `GameState.ProcessInput`, refusal
   bookkeeping, and automatic-tick scheduling.
3. Harmony observation around `GameState.ProcessInput` records whether the
   attempt returned successfully and whether movement was scheduled.

This is intentionally different from calling `GameState.ProcessInput`
directly: `DoPlayerInput` contains behavior that is part of the real game's
input semantics.

An `Undo` token will call the public `Game.DoUndo` method only when the same
game-level input gate is quiescent. The driver will release synthetic input
for at least one update between attempts so the game's repeated/unsuccessful
input guards observe the same neutral boundary as discrete demonstration
tokens.

Passive mode will never synthesize input. It will only observe real keyboard
attempts at the same hook points.

### 5.2 Settled-state boundary

The plugin will create a pending record when an input attempt enters the game.
It will not serialize the resulting state immediately. Capture occurs only
after the game reaches a quiescent boundary:

- `GameState.Moving()` is false;
- `GameState.pushestotry` is zero;
- no oracle input is currently asserted;
- game-level entry, exit, loss, and spawn presentation gates that block normal
  player input are inactive; and
- the current game-state serialization and `GameState` identity are unchanged
  for two consecutive late-update observations.

The two-observation stability rule guards against capturing the frame between
the last movement and a level/overworld state replacement. The implementation
will derive the presentation-gate checks from the decompiled `Game.Update` and
`DoPlayerInput` conditions rather than guessing from elapsed wall time.

A refused direction still produces a record. Because the game suppresses a
held unsuccessful direction, the driver inserts a neutral update before the
next token.

### 5.3 State capture

At a settled boundary, the plugin will call:

```csharp
game.gamestate.Save(dynamiconly: false, normalize: false)
```

Calling the game's serializer avoids reimplementing entity enumeration or
field interpretation inside the plugin. `normalize` remains false so
observation cannot mutate the live game state.

The plugin will also record selected envelope fields that are important to
interpreting the serialized state but are not all present in the save string,
including:

- `overworld`, `won`, `returning`, and the loss reason;
- `pushtargetlevel`, display name, and cooked-sausage count;
- the input result and whether the `GameState` instance changed;
- movement count and `pushestotry` at the capture boundary.

The raw save string remains authoritative. Python normalization is a separate,
testable layer.

## 6. Trace protocol

The trace will be newline-delimited JSON so every completed record can be
flushed independently. The first line is a run header:

```json
{
  "kind": "run",
  "schema_version": 1,
  "run_id": "opaque-id",
  "mode": "passive-or-replay",
  "game_assembly_sha256": "...",
  "plugin_version": "...",
  "input_sha256": "...",
  "expected_input_count": 16567,
  "started_at_utc": "..."
}
```

The plugin then writes an initial snapshot with `input_index: null`. Each
attempted input produces one terminal record:

```json
{
  "kind": "step",
  "schema_version": 1,
  "run_id": "opaque-id",
  "input_index": 1240,
  "input": "West",
  "accepted": true,
  "settle_frames": 8,
  "state_replaced": false,
  "level": "levelb11",
  "overworld": false,
  "won": false,
  "lost_reason": "",
  "raw_save": "..."
}
```

Records use zero-based `input_index`, matching Python list indexing. User-facing
diagnostics also display the one-based global and segment-relative move
numbers. The writer flushes after every complete line. It writes no partial
JSON object and never overwrites an existing run.

A successful replay finishes with an `end` record containing the emitted input
count. Replay-mode run headers also contain the expected input count. Therefore
a trace ending cleanly at a JSON line boundary is still rejected if it was
truncated before all inputs or before the `end` record.

```json
{
  "kind": "end",
  "schema_version": 1,
  "run_id": "opaque-id",
  "input_count": 16567,
  "finished_at_utc": "..."
}
```

If an input does not settle within a configured frame and wall-clock limit,
the plugin writes a terminal `error` record containing the last observed
movement count, `pushestotry`, state identity, and raw save, then stops replay.
It does not skip the input or continue with an untrusted trace.

## 7. Python normalization and comparison

`ssr_env.oracle` will define immutable, versioned trace types and pure
comparison functions. The command-line tool will handle files, replay
selection, and rendering.

For each step, the comparator will:

1. Validate the run header, sequential indices, record count, assembly hash,
   and terminal status.
2. Parse the game save string without discarding the raw value.
3. Normalize the game state and Python `GameState` to a shared representation.
4. Establish and maintain an explicit identity bridge between game and
   simulator entities, then compare global fields and bridged entities.
5. Stop at the first unequal settled boundary.
6. Print the input location, differing fields, relevant entity before/after
   values, and both simulator and oracle state renderings.

The shared representation will cover at least:

- entity id and type;
- integer position and direction;
- sausage rotation, four face-cook values, attachment, and status data;
- player attachment and state data needed by subsequent mechanics;
- current level/overworld state;
- completed levels, issued world sausages, tileset, display name, cooked count,
  and music seed.

The game and simulator do not initially use the same numeric entity ids. The
comparator will not equate those numbers directly or renumber simulator state.
At the initial boundary it will pair uniquely identifiable entities by
semantics: islands by their unique `dat`, unique player/fork/barrier entities by
type and full state, and remaining entities by an unambiguous full-state key.
The mapping persists across moves. Newly spawned entities are paired from the
unmatched sets using type, pose, direction, data, cooking state, and creation
order only when that pairing is unique. Attachments are translated through the
same map. An ambiguous pairing is a comparison error, not a guessed match.

Comparison policy will be explicit. Fields proved to be presentation-only may
be ignored by name, but no unknown or unparsable field will silently disappear.
Unknown data is either retained as raw data or reported as an unsupported
schema condition.

The existing `ssr_env.diagnostics` snapshots will be reused where their field
definitions agree. Oracle comparison will not change simulator execution.

## 8. Installation and data safety

The install tool will receive explicit game and output paths. It will:

1. Verify the expected app, Unity version, Mono managed directory, and
   `Assembly-CSharp.dll` before writing.
2. Compute and display the assembly hash.
3. Install BepInEx beside the `.app`, not inside the app bundle.
4. Copy the oracle plugin and configuration.
5. Write an installation manifest containing every path it created.
6. Refuse to overwrite unrelated existing files or an unrecognized BepInEx
   installation.

Removal will delete only files listed in a matching manifest and only after
verifying their locations are under the resolved game directory. It will not
use broad recursive deletion.

The original Steam launcher remains available. Oracle runs use the BepInEx
wrapper explicitly. The plugin will use a dedicated test save slot or a copied
test save, selected during implementation after the game's save API and slot
layout are verified. It will never select the user's normal slot by default.

Trace output defaults to the repository's ignored `data/oracle/` directory.
No network service is opened, and traces remain local.

## 9. Validation sequence

Implementation will advance through gates:

### Gate 1: Build and boot

- Build the plugin against the installed game's managed assemblies.
- Launch through the wrapper.
- Confirm the BepInEx and plugin versions in logs.
- Confirm an ordinary non-BepInEx launch still works.

### Gate 2: Passive observation

- Capture the initial state.
- Manually perform one accepted direction, one refused direction, and one undo.
- Confirm one record per attempt and deterministic repeated serialization.
- Confirm the plugin makes no game-state writes in passive mode.

### Gate 3: Short automated replay

- Use a dedicated test save.
- Replay a small known sequence through the normal `Game` input path.
- Compare passive and automated traces for the same sequence.
- Verify timeout, duplicate-index, and interrupted-run handling.

### Gate 4: Confirmed prefix

- Replay `all.dem` from the known initial state.
- Require equality across the 18-level prefix already protected by the Python
  replay acceptance test.
- Treat an earlier mismatch as an oracle/comparator issue until independently
  explained.

### Gate 5: Cove localization

- Continue into `levelb11`.
- Report the first mismatching settled transition.
- Save a minimal local trace window around that transition.
- Write a focused failing Python test before changing mechanics.

The user-facing manual validation budget is expected to be three to five short
checkpoints concentrated in Gates 1–3. Later levels should use the executable
oracle rather than repeated manual playthroughs.

## 10. Testing strategy

### 10.1 C# tests

Where Unity-free extraction is practical, tests will cover:

- `.dem` parsing and token validation;
- record sequencing;
- state-machine transitions from idle to injected to settling to captured;
- stable-state debounce behavior;
- timeout and terminal error generation;
- atomic line construction and schema versioning.

Unity- and game-bound hooks are verified through the staged integration gates,
not mocked as proof that the real game integration works.

### 10.2 Python tests

Tests will cover:

- header and schema validation;
- initial and step record parsing;
- missing, duplicate, and out-of-order indices;
- game-save parsing for real representative strings;
- entity and global-state normalization;
- accepted, refused, and undo records;
- precise field-level divergence reports;
- unknown field and truncated-run failures;
- non-mutation of simulator states during comparison.

### 10.3 Regression policy

Full traces remain local and ignored. After a simulator bug is understood, the
smallest state/transition fixture necessary to reproduce it may be added to
the test suite with its provenance, game assembly hash, and move index.

Mechanics fixes will use those fixtures test-first and rerun both the ordinary
test suite and the oracle prefix before the confirmed frontier advances.

## 11. Failure handling and observability

- Startup errors name the missing or mismatched assembly, plugin dependency,
  configuration, or output path.
- The plugin logs mode changes, run identifiers, input indices, and capture
  completion without logging every Unity frame.
- A replay cannot resume by silently appending to an interrupted run; a new run
  id and file are required.
- The comparator rejects traces from an unexpected assembly hash unless the
  user explicitly acknowledges the mismatch.
- Capture or parse failures retain the last raw save and input index.
- No mismatch is called a simulator bug until record alignment, initial state,
  and comparator normalization have been checked.

## 12. Delivery boundary

This design delivers a trustworthy first-divergence instrument. Once it
identifies Cove's earliest mismatch, simulator repair becomes a separate
test-driven mechanics task. The same cycle can then advance through later
levels without expanding the amount of routine manual verification.
