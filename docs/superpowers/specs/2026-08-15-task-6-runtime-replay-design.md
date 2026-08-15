# Task 6 Runtime Bridge and Native Replay Design

**Date:** 2026-08-15
**Status:** Approved conversationally; written-spec review pending

## 1. Purpose

Task 5 completed and verified the Unity-free passive driver, but the installed
plugin is still only a three-method compatibility probe. Task 6 connects that
proven driver to the real game and then adds deterministic replay through the
game's native input path.

This work has two separately reviewed slices:

1. **Task 6.1 — runtime bridge:** strict configuration, save isolation, trace
   startup, the game adapter, observation-only Harmony hooks, and passive-mode
   controller wiring.
2. **Task 6.2 — replay coordinator:** exact `.dem` ingestion, generalized run
   metadata and input cardinality, one-update direction injection, native Undo
   driving, and replay alignment.

Task 6 does not launch the game. The first bounded passive and one-input replay
launch remains Task 7 and requires its own explicit gate.

## 2. Accepted baseline and authority

Work begins from merged `origin/main` commit
`2ba1b328545b4beb8d4d64983d2b7916350c28fe`, which contains the accepted
Task 5 implementation and verification report.

Behavioral authority is applied in this order:

1. this design for Task 6 composition, replay, and the changes it explicitly
   makes to mode and trace cardinality;
2. `docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md` and the
   accepted Task 5 implementation for driver lifecycle, terminal ownership,
   output serialization, and settled Step behavior;
3. `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`
   for the runtime ABI, exact game fields, passive observation, path safety,
   read-only configuration, and failure/restoration rules; and
4. `docs/superpowers/specs/2026-07-27-executable-oracle-design.md` for the
   original native-path replay intent.

The Task 6 body in
`docs/superpowers/plans/2026-07-27-executable-oracle.md` is historical input,
not an executable plan. It assumes `GameHooks` and `OracleController` already
exist, but neither class exists in the accepted baseline. The descendant plan
must regenerate every implementation step from this design and the live tree.

This design commit must be the direct child of the accepted merge, have subject
`docs: design Task 6 runtime replay integration`, and change only this file.

## 3. Decision and alternatives

Task 6 composes a thin runtime bridge and an optional replay coordinator around
the existing `PassiveDriver`:

```text
Plugin startup
    |
    v
strict config + path/save isolation + trace creation
    |
    v
Harmony GameHooks -> OracleController -> PassiveDriver -> NDJSON sink
                         |                    ^
                         v                    |
                    GameAdapter        ReplayCoordinator
                         |                    |
                         +---- game ABI <-----+
```

The driver remains the single owner of Initial/Step/End/Error ordering,
settling, lifecycle balancing, terminal arbitration, and output serialization.
The controller translates runtime callbacks. The coordinator decides only when
a replay token may be presented and whether native traversal matched that
decision.

Two alternatives are rejected:

- **Make `PassiveDriver` a mode-aware Unity controller.** This would mix game
  types, file/configuration policy, and input synthesis into the already proven
  state machine and invalidate its isolation boundary.
- **Build a second replay settling state machine.** This would duplicate the
  hardest Task 5 behavior and allow passive and replay traces to disagree about
  settlement, lifecycle, or failure ordering.

## 4. Scope

### 4.1 In scope

- Read-only, strict `off`, `passive`, and finally `replay` configuration.
- Runtime assembly/reflection validation and exact reviewed hook installation.
- Isolated save-path validation and assignment before active observation.
- A game adapter that is the only production boundary containing game types.
- Passive observation through the accepted Task 5 driver with no input
  synthesis.
- Exact UTF-8 `.dem` byte hashing and strict token parsing.
- Replay directions through `Playerinputstring` and Undo through `DoUndo`.
- Replay-neutral and same-update native-path alignment gates.
- Generalized replay run metadata and expected input count while retaining the
  exact passive three-input contract.
- Unity-free net10 tests, compile-only net35/plugin tests, Python protocol
  tests, mutations, and independent reviews.

### 4.2 Out of scope

- Launching or controlling the real game process.
- Installing or removing plugin artifacts, BepInEx, or configuration.
- Relaxing the pinned game-assembly hash or changing the game assembly.
- Writing to the user's ordinary save directory.
- Calling `GameState.ProcessInput` directly.
- Synthesizing input in passive mode.
- Parsing or comparing the game's raw save format.
- Simulator divergence localization or mechanics fixes.
- Committing generated traces, local compatibility fixtures, or game binaries.

## 5. Slice ownership and files

### 5.1 Task 6.1: runtime bridge

The expected production ownership is:

- `oracle/plugin/Core/OracleConfiguration.cs`: dependency-free strict config
  model and parser.
- `oracle/plugin/Core/OracleController.cs`: Unity-free controller, runtime
  callback routing, reporter behavior, and adapter boundary.
- `oracle/plugin/Core/OracleRuntimeBoundaries.cs`: minimal adapter/log/runtime
  interfaces required by the controller.
- `oracle/plugin/GameAdapter.cs`: exact game field reads, quiescence, capture,
  path verification, time, and native Undo call.
- `oracle/plugin/GameHooks.cs`: exact Harmony patches and callback firewall.
- `oracle/plugin/Plugin.cs`: validate, compose, install, dispose, and unpatch.

Tests live in the existing unit harness where no game types are required, plus
a compile/reflection surface that uses the pinned local game and BepInEx
assemblies. Final filenames may be combined when that makes the implementation
smaller, but the dependency boundary must remain unchanged.

Task 6.1 accepts only `off` and `passive`. It must continue to reject `replay`
until Task 6.2 is complete, so no dormant or partially implemented replay mode
can start.

### 5.2 Task 6.2: replay coordinator

The expected production ownership is:

- `oracle/plugin/Core/ReplayInput.cs`: immutable input bytes metadata, strict
  token parser, and SHA-256 identity.
- `oracle/plugin/Core/ReplayCoordinator.cs`: replay readiness, neutral polls,
  one-update arming, native-path alignment, and token advancement.
- narrow extensions to `OracleProtocol`, `PassiveDriver`, configuration,
  controller, hooks, adapter, and plugin composition;
- corresponding generalization of `src/ssr_env/oracle_protocol.py` so schema-v1
  replay traces are structurally validated without weakening passive success;
  and
- new unit registrations for configuration, controller-passive, and
  controller-replay behavior.

The implementation commits retain these subjects:

1. `feat: connect passive oracle runtime`
2. `feat: replay SSR inputs through native game path`

## 6. Runtime configuration and startup

### 6.1 Common grammar

Configuration is parsed from the existing BepInEx config file bytes. The
plugin never calls `Config.Bind`, enables autosave, inserts defaults, or
rewrites the file.

The parser accepts exactly one `[Oracle]` section, exact case-sensitive key
spelling, no duplicate or case-variant key, and no other non-comment section.
Unknown modes, keys, missing active-mode keys, malformed integers/hashes, or
ambiguous paths fail closed.

The accepted modes are:

- `off`: preserve the current three-method compatibility probe, log the
  unchanged load marker, install no patches, redirect no save path, and open no
  trace;
- `passive`: observe exactly three manual attempts and never synthesize input;
  and
- `replay`: consume one nonempty `.dem` file through the native game path.

Legacy active-only keys in the pinned Mode-off fixture remain accepted but
unread in `off`. `off` must remain byte-preserving.

### 6.2 Active-mode keys

Both active modes require:

```ini
[Oracle]
Mode = passive-or-replay
OutputDirectory = <absolute existing private directory>
RunName = <single safe filename stem>
SaveDirectory = <absolute existing isolated directory>
MaxSettleFrames = 600
MaxSettleSeconds = 30
```

`RunName` is nonempty, contains no directory separator or traversal component,
and names the exact create-new target `<OutputDirectory>/<RunName>.ndjson`.
The target must not exist.

Passive additionally requires exactly:

```ini
ExpectedPassiveInputs = 3
```

Replay instead requires exactly:

```ini
InputPath = <absolute existing .dem file>
ExpectedInitialSha256 = <empty or 64 lowercase hexadecimal digits>
```

The mode-specific key set is exact: passive does not accept replay keys and
replay does not accept `ExpectedPassiveInputs`.

Output and save directories must be canonical, existing real directories,
not symlink leaves, distinct, and non-nested. The save directory must also be
separate and non-nested with the pinned ordinary save tree. Replay input must
be an existing regular non-symlink file and must not equal or reside beneath
the output or save directory. The implementation plan must preserve the full
home/path provenance checks from the authoritative passive design.

### 6.3 Startup transaction

Active startup performs one ordered transaction:

1. parse the file read-only and validate the complete mode-specific config;
2. validate the pinned assembly hash and the entire exact reflection surface;
3. validate directory topology, ordinary-save provenance, and absent trace;
4. in replay, read the input exactly once, hash the exact bytes before parsing,
   parse the complete file, and reject an empty token stream;
5. redirect and verify `SaveGame.PersistentDataPath` to the isolated path;
6. create the trace with `FileMode.CreateNew` and construct the adapter,
   controller, driver, and optional coordinator;
7. call the driver's `Prepare` transaction to write and flush the Run record;
8. install this plugin's complete Harmony patch set atomically;
9. activate the driver; and
10. log the unchanged boot marker once.

Failure before sink creation emits only one exact marker-only startup failure.
Failure after Run durability selects the driver's appropriate terminal failure
when possible. Partial patch installation first disables the controller, then
unpatches only this plugin's Harmony owner. No failure falls back to the user's
ordinary save path.

## 7. Runtime bridge behavior

### 7.1 Game adapter

`GameAdapter` is the only production type that reads or calls the game ABI. It
implements plain runtime interfaces consumed by the controller and maps the
exact fields and methods retained by the 2026-07-31 passive design.

Capture calls `GameState.Save(false, false)` only from the `Game.Update`
postfix on Unity's main thread. It rebuilds the exact `CaptureRecord` envelope
without retaining a `GameState` across state replacement. It does not mutate
gameplay state.

The sole replay exception is native Undo: when commanded by the replay
coordinator, the adapter calls public `Game.DoUndo()`. Directions still enter
only through the `Playerinputstring` override; neither mode calls
`GameState.ProcessInput` directly.

### 7.2 Harmony surface

The complete reviewed observation surface is:

- `Game.Update`: prefix, postfix, and finalizer;
- `Game.DoPlayerInput`: prefix, postfix, and finalizer;
- `Game.Playerinputstring`: replay-capable prefix plus observation postfix;
- `GameState.ProcessInput(Direction)`: prefix, postfix, and finalizer;
- `Game.DoUndo`: prefix, postfix, and finalizer;
- `Game.RestorePrevState(GameState.BakStruct)`: prefix;
- `Game.DoRestart`: prefix, postfix, and finalizer; and
- `Game.SetGameState(GameState)`: prefix, postfix, and finalizer.

Every target is resolved and its exact static/instance, visibility, return,
parameter, and nested-type shape is validated before the first patch is
installed. A missing or changed target is `invalid_reflection`; installation
failure after Run durability is `patch_install_failed`.

Every patch callback catches observer exceptions, reports them through the
controller, and never changes a game method's original return or exception.
Finalizers return the identical original exception object. Passive
`Playerinputstring` always executes the original method and leaves its result
untouched.

### 7.3 Controller ownership

The controller owns one `PassiveDriver` and routes each typed hook token and
update directive exactly once. It implements the driver's observation and
reporting boundaries using only plain interfaces; Core remains free of Unity,
BepInEx, Harmony, filesystem-global state, and concrete game types.

The driver remains authoritative for output. The controller does not write
Initial, Step, End, or Error records itself and cannot advance a replay token
until the corresponding durable Step causes `Ready(n)` or `Complete()`.

Runtime hooks execute on Unity's main thread. Destruction/disable may race only
through the driver's already proven terminal ownership. No monitor is held
across a game call, sink call, reporter callback, diagnostic, or Harmony
unpatch operation.

## 8. Replay input and protocol

### 8.1 Exact input identity

Replay reads the `.dem` file once as bytes. `input_sha256` is the lowercase
SHA-256 of those exact bytes, including line endings and trailing whitespace.
Only after hashing are the bytes decoded as strict UTF-8 without BOM or invalid
sequences.

Parsing accepts blank/ASCII-whitespace-only lines and exactly the five tokens
`North`, `South`, `West`, `East`, and `Undo` after trimming ASCII whitespace.
Every other token, embedded NUL, invalid UTF-8 sequence, or empty resulting
token list fails startup. The immutable parsed array assigns contiguous
zero-based indices in file order.

### 8.2 Schema-v1 generalization

`OracleMode` gains `Replay`; `off` remains unable to create a Run record.
The Task 6 plugin and Run-record version are both `0.3.0`; the BepInEx
attribute, `OracleProtocol.PluginVersion`, canonical encoder tests, and Python
reader must agree. The trace schema itself remains version 1.

A Run record is valid only when:

- passive: `mode == passive`, `input_sha256 == null`, and
  `expected_input_count == 3`; or
- replay: `mode == replay`, `input_sha256` is 64 lowercase hexadecimal digits,
  and `expected_input_count` equals the positive parsed token count.

The existing passive Run constructor remains as a compatibility overload.
`PassiveDriver` accepts any positive expected count but receives exactly three
in passive mode. `EndRecord` accepts a positive count; the driver still proves
that End count equals the Run expectation and the number of durable Steps.

The Python reader retains mode, input hash, and expected count in `RunHeader`,
uses that count for structural sequence validation, and accepts only the two
relations above. `require_passive_success` remains an exact three-step
direction/refusal/Undo oracle. Replay success validation additionally proves
that Step inputs and indices exactly match the parsed input file and that its
exact-byte SHA-256 equals the header.

No record order, field order, canonical JSON rule, flush rule, or schema version
changes.

## 9. Replay coordinator

### 9.1 Readiness and neutral boundary

The coordinator never settles state itself. It observes driver progress and
may arm a token only when:

- Initial is durable and any expected initial signature has passed;
- the driver is stably Ready;
- the exact current `GameState` is present and the accepted game-level input
  gate is quiescent;
- no native call or prior replay token is active; and
- after the first attempt, at least one actual `Playerinputstring` poll has
  returned synthetic `None` since the prior Step.

The neutral requirement is satisfied by a real call to the patched polling
method, not by elapsed frames. While no cardinal is armed, replay suppresses
physical input and returns `Direction.None`. This is also how settling receives
the physical-neutral observation already required by `PassiveDriver`.

Before input index zero, one consumed neutral poll plus the driver's two equal
quiescent captures are required. On `Ready(0)`, the coordinator hashes the
exact UTF-8 bytes of `Initial.Capture.RawSave`. A nonempty
`ExpectedInitialSha256` mismatch selects terminal Error
`initial_state_mismatch` before any token is armed.

### 9.2 Cardinal transaction

At an eligible `Game.Update` prefix, a cardinal token is armed for that update
only. The first `Playerinputstring` call returns the mapped native direction
and skips physical polling. The normal `DoPlayerInput` body then owns all game
gates, snapshot behavior, `ProcessInput`, refusal behavior, and automatic
movement scheduling.

The same callbacks are sent through the driver's normal PlayerPoll and
ProcessInput lifecycle. Before the update returns, the coordinator requires
the armed direction to have been polled exactly once and to have reached one
matching `GameState.ProcessInput` call. Missing, duplicate, or mismatched
native traversal selects terminal Error `replay_alignment_failed`; the token
is never retried.

The direction is deasserted at the update boundary even if the original method
throws. Physical directional input is suppressed for the entire replay run.

### 9.3 Undo transaction

An eligible Undo token is initiated once from the Unity main thread at the
start of an update, after the same neutral/readiness gate. The adapter calls
public `Game.DoUndo()` and the existing Undo/Restore hooks provide the driver's
normal acceptance and movement-scheduled observations.

Undo is accepted only if `RestorePrevState` occurs inside that exact Undo
context. Raw-save equality is never used to infer acceptance. A game exception
is balanced through `UndoThrew`, selects `game_method_exception`, and is not
reissued.

### 9.4 Progress and terminal behavior

The coordinator's current token index changes only after the driver's durable
Step and matching `Ready(completedInputs)`. It never pre-increments, skips, or
repeats a token.

Unexpected state replacement during a pending token selects the existing
`state_replaced` Error. Schema-v1 continues to prohibit a successful Step with
`state_replaced: true`. Settle deadlines remain owned by the driver.

After the final durable Step, the driver writes End, closes, and reports
Complete without `Ready(expectedInputCount)`. End count equals both the header
expectation and parsed token count. Late hooks, updates, physical input, and
disposal remain output-inert.

## 10. Failures, logging, and cleanup

Task 6 adds record errors:

- `initial_state_mismatch`: the durable Initial raw-save signature does not
  match the configured replay expectation; and
- `replay_alignment_failed`: an armed replay token did not traverse the exact
  native call shape in its owning update.

Unreadable or invalid replay input is an `invalid_configuration` startup
failure because no authenticated Run exists yet. Existing record and
marker-only codes retain their accepted meanings.

The first terminal owner still wins. A trace I/O failure remains marker-only
`trace_io_failed`; no later runtime or replay failure may rewrite authenticated
bytes. Controller diagnostics share the driver's serialized callback policy
and cannot win ownership ahead of the failure they describe.

`OnDestroy` disables the controller, disposes the driver/sink, clears the
published hook target, and unpatches only this plugin's Harmony owner. It does
not delete traces, input files, saves, config, compatibility artifacts, or
user data. Ordinary save bytes remain untouched. Process-level Mode-off
restoration and installation removal remain later operational workflows.

## 11. Test and review strategy

### 11.1 Unity-free tests

New deterministic cohorts cover:

- strict off/passive/replay configuration and path relations;
- active startup ordering and rollback at every boundary;
- exact callback/token routing for the complete hook lifecycle;
- passive mode preserving native input and never calling Undo;
- exact-byte replay hashing, UTF-8/token rejection, and dynamic counts;
- initial neutral/signature gating;
- one-update cardinal assertion and deassertion;
- physical suppression and actual neutral-poll accounting;
- same-update missing/duplicate/mismatched `ProcessInput` detection;
- Undo through the adapter with Restore-based acceptance;
- refused directions, state replacement, timeouts, game exceptions, and
  trace/reporter failures;
- no increment before durable Step, no final-token repeat, exact End count;
- disable/dispose/reentrant diagnostic behavior; and
- unchanged passive 39-test behavior unless an explicitly generalized protocol
  assertion is replaced by an equally strict mode-specific assertion.

Barriers use bounded waits and deterministic callbacks; no sleep-based race
test is accepted.

### 11.2 ABI and build gates

The plan must provide an exact reflection/ABI manifest and test it against the
pinned `Assembly-CSharp.dll`. The plugin builds with C# 7.3/net35 against the
pinned Game/BepInEx references. Core and the unit harness build/run under the
pinned net10 SDK. All existing Python tests remain green with new replay
protocol tests added.

The final matrix includes forced no-restore net10 and net35 rebuilds with zero
warnings, every named C# cohort, the exact full harness manifest, and the full
Python suite. Relevant controller/replay races receive repeated stress and
lean mutation qualification.

### 11.3 Review gates

Each slice requires:

1. meaningful production-unchanged RED evidence;
2. focused GREEN and the full affected matrix;
3. a scoped precommit spec review and code-quality review;
4. one exact-scope implementation commit;
5. immutable postcommit reauthentication and re-review; and
6. preservation checks for all historical plans, reports, evidence, local
   fixtures, and unrelated repository paths.

No runtime launch evidence may be claimed in Task 6.

## 12. Completion criteria

Task 6 is complete when:

1. Mode-off remains byte-preserving and patch-free.
2. Passive mode can be composed from strict config through the proven driver
   without synthesizing input.
3. Replay input has an exact byte identity and positive parsed cardinality.
4. Directions traverse native `DoPlayerInput`; Undo traverses native `DoUndo`.
5. Every token advances only after one durable settled Step.
6. The trace protocol structurally validates passive and replay relations
   without weakening passive success.
7. Runtime exceptions cannot escape patches or replace original game
   exceptions.
8. Save and output isolation fail closed.
9. The full net10, net35, C#, and Python verification matrix passes with clean
   repository state.
10. No game process was launched and no installed game or user data was
    changed.

The next milestone is Task 7: transactionally deploy reviewed artifacts, run
the bounded three-input passive gate, restore Mode-off, then run and restore a
one-input replay gate under separate user approval.
