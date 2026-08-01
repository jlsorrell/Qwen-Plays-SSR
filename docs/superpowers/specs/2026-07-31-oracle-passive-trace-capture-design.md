# Passive Settled-State Trace Capture Design

**Date:** 2026-07-31

**Status:** Written specification and offline implementation plans approved; implementation pending

## 1. Context

The executable-oracle pipeline has passed its first corrected end-to-end
runtime checkpoint on macOS Tahoe 26.6. The reviewed BepInEx compatibility
preloader, reproducible plugin, canonical `BepInEx/LogOutput.log` observer,
bounded process cleanup, retained evidence, and official-preloader restoration
all worked together. The retained canonical log authenticated these exact
markers:

```text
BepInEx 5.4.23.5
Unity v2018.4.25f1
SSR oracle boot probe loaded
```

The installed game returned to healthy `official` preloader state after that
single approved launch. `Assembly-CSharp.dll` remained at
`886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`.

The plugin at the merged checkpoint is deliberately minimal. It validates
three reflected game methods and writes one load marker, but it does not patch
the game, serialize state, write traces, observe inputs, or compare the game
against the Python simulator. The next trustworthy milestone is therefore a
small passive vertical slice: observe three manual inputs and record the
game's own settled serialized state without synthesizing any input.

## 2. Decision and alternatives

This milestone uses a **thin passive vertical slice**. It defines the minimum
trace protocol, a Unity-free settling driver, passive Harmony adapters, a
create-new trace sink, a strict Python trace validator, and one bounded
real-game integration gate.

Two alternatives were rejected:

1. Building the complete parser, normalization layer, identity bridge, and
   simulator comparator before another runtime capture would defer feedback
   and risk encoding incorrect assumptions about the real save or settling
   boundary.
2. Adding automated replay immediately would couple input injection, native
   input gating, undo semantics, quiescence, serialization, and trace
   alignment in one change. A failure would again be ambiguous.

Passive capture proves observation before injection. Automated replay and
semantic simulator comparison remain separate later milestones.

## 3. Goals

The milestone must:

1. preserve the current Mode-off compatibility-probe behavior;
2. redirect all game saves to an explicit isolated local directory before a
   `Game` instance is accepted, and prove the original save tree unchanged;
3. observe, without modifying, one accepted direction, one refused direction,
   and one accepted Undo;
4. capture the initial state and exactly one terminal state per attempted
   input using `GameState.Save(false, false)` on Unity's main thread;
5. declare a state settled only after the complete quiescence contract holds,
   a neutral physical-input poll has occurred, and two consecutive complete
   capture signatures match;
6. emit a deterministic, append-only, versioned NDJSON trace whose complete
   records are flushed independently;
7. validate the trace structurally and validate the three-step relational
   contract without yet interpreting the raw save;
8. retain the trace, canonical boot log, probe metadata, and recovery evidence
   from exactly one separately approved bounded launch; and
9. return the installed config to exact Mode-off bytes and the preloader to a
   verified healthy `official` state.

## 4. Non-goals

This milestone does not:

- inject, replay, suppress, replace, or retry player input;
- actively invoke `GameState.ProcessInput`, `Game.DoPlayerInput`, `Game.DoUndo`,
  `Game.RestorePrevState`, or any other gameplay method;
- parse the raw save into Python entities;
- compare numeric entity IDs across runtimes;
- normalize oracle and simulator states;
- identify or fix a simulator mechanics divergence;
- capture transient render frames, animation, audio, particles, or camera
  state;
- write inside `Sausage.app`, alter `Assembly-CSharp.dll`, use the user's
  normal save directory, or launch through Steam;
- retry a failed runtime gate or perform a second launch under the first
  approval; or
- commit real traces, save data, recovery trees, or user-specific paths to
  Git.

## 5. Architecture and boundaries

The implementation has five components with one-way dependencies:

```text
Harmony/game observations
        |
        v
Unity-free settling driver
        |
        v
deterministic NDJSON sink
        |
        v
strict Python validator

bounded passive probe ---- retains log, trace, metadata, and cleanup evidence
```

### 5.1 Game adapter

The game adapter contains Harmony patches and the only references to game or
Unity types. It maps native events to plain driver inputs, samples read-only
gate fields, and calls `GameState.Save(false, false)`. It never calls a
gameplay transition method and never changes a method argument or result.
In the pinned decompilation, this argument pair does not call
`NormalizeState`; it only rebuilds the serializer's private string buffer. The
adapter invokes it only from the Unity main-thread update postfix.

### 5.2 Settling driver

The driver contains no Unity, BepInEx, Harmony, or game-assembly types. It is a
deterministic state machine over plain records. Tests can therefore exercise
all phases, samples, errors, and record cardinality without launching Unity.

### 5.3 Trace sink

The sink creates one new UTF-8-without-BOM NDJSON file using
`FileMode.CreateNew` at exactly
`Path.Combine(OutputDirectory, RunName + ".ndjson")`, writes LF-terminated
complete JSON objects, and flushes after every record. It never overwrites or
appends to an existing path.

### 5.4 Python validator

`ssr_env.oracle_protocol` parses the exact schema and distinguishes a
well-formed successful trace from a well-formed terminal-error trace. A
separate success validator enforces the passive three-step sequence and
relations. `tools/oracle_trace_check.py` exposes both operations and treats
`raw_save` as an opaque string in this milestone.

### 5.5 Bounded passive probe

A new passive-probe entry point reuses the canonical boot observer's hardened
path, process-group, installer snapshot, code-signature, BepInEx logging,
canonical-log, evidence-publication, and config-identity primitives. It does
not weaken or silently broaden `run_boot_probe` or its schema-v1 public marker
contract. Shared internals may be extracted only where both probes retain the
same semantics.

## 6. Runtime modes and configuration

The plugin accepts exactly two modes in this milestone:

- `off`: validate the compatibility methods and emit the existing load marker;
  install no Harmony patches and open no trace.
- `passive`: require the complete passive configuration, redirect saves,
  install observation-only patches, and capture exactly three input attempts.

The string `replay` and every other value are rejected. Replay must not be
accepted as a dormant or partially implemented mode.

Mode selection is parsed read-only from the existing plugin config bytes. The
plugin never calls `Config.Bind`, enables autosave, adds defaults, or otherwise
rewrites that file in either mode. In `off`, only one exactly spelled
`[Oracle]` section and one exactly spelled `Mode = off` entry are required;
passive-only keys are not required. The remaining legacy keys in the pinned
Mode-off fixture (`OutputDirectory`, `RunName`, `SaveDirectory`, `InputPath`,
`MaxSettleFrames`, `MaxSettleSeconds`, and `ExpectedInitialSha256`) remain
accepted but unread; only those keys may accompany `Mode`, with no duplicate or
case-variant key and no other non-comment section. Off mode performs the
original three-method compatibility check, emits the unchanged load marker,
opens no sink, redirects no save path, and installs no patch.

The real pinned Mode-off fixture has SHA-256
`cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d`.
A local ignored-fixture regression supplies those exact bytes, proves the file
remains byte-identical after plugin startup/destruction, and confirms that the
new passive-only key `ExpectedPassiveInputs` is unnecessary in `off`. Portable
unit coverage constructs the same legacy grammar in memory without committing
the fixture's user-specific absolute paths.

Passive mode requires this logical configuration:

```ini
[Oracle]
Mode = passive
OutputDirectory = <absolute private run directory>
RunName = passive-trace
SaveDirectory = <absolute isolated save directory>
ExpectedPassiveInputs = 3
MaxSettleFrames = 600
MaxSettleSeconds = 30
```

Passive mode instead requires:

- exactly one exactly spelled `[Oracle]` section, no other non-comment section,
  one exactly spelled value for every listed key, and no additional key;
- absolute output and save paths;
- `Mode == passive` and `RunName == passive-trace`, with the run name also
  satisfying the single-filename-stem, no-separator, no-traversal rule;
- `ExpectedPassiveInputs == 3`, `MaxSettleFrames == 600`, and
  `MaxSettleSeconds == 30` for this gate;
- already-existing output and save directories that are real directories
  rather than symlinks;
- canonicalized output and save directories that are distinct and neither
  contains the other;
- a canonicalized save directory different from the original
  `SaveGame.PersistentDataPath`, with neither save tree containing the other.

The outer probe creates both leaf directories with mode `0700` and proves the
controlled path from its ignored evidence root contains no symlink component.
The plugin independently canonicalizes both paths, requires both leaves to
exist, and refuses to create either directory. The exact target
`OutputDirectory/RunName.ndjson` must not exist before deployment and is
rechecked by the plugin through `FileMode.CreateNew`.

Before accepting any `Game` instance, passive startup sets
`SaveGame.PersistentDataPath` to the isolated directory. Failure to prove the
separation aborts passive startup; there is no fallback to the normal save.
Before assignment, the plugin requires nonempty `SaveGame.homePath` to equal
the process `HOME` value and the original `PersistentDataPath` to equal that
home plus the pinned `/Library/Application Support/unity.increpare games/Sausage`
suffix. The outer probe fingerprints the same path under the exact environment
passed to the wrapper.
Every active `Game.Update` postfix rechecks exact canonical equality before
sampling; drift faults with `save_path_changed` and never redirects back to the
ordinary path. The outer ordinary-save fingerprint remains the acceptance
proof for writes that could precede detection.

The locally generated passive config is ignored by Git and is deployed only
through the transactional installer. The pinned Mode-off config remains the
restoration source.

Passive startup has one exact order: validate the complete configuration,
assembly hash, reflection surface, directory topology, and absent target;
redirect and verify `SaveGame.PersistentDataPath`; create the sink and flush
the run record; install the observation patches; enter `AwaitGame`; then emit
the unchanged `SSR oracle boot probe loaded` marker exactly once. Passive mode
never emits that marker before save isolation and observation startup are
complete, so its canonical authentication safely gates the menu prompt.
Failure before sink creation produces only the exact failure log marker.
Failure after sink creation writes an error record when possible. A partial
patch-install failure first disables the driver, then unpatches only this
plugin's Harmony owner ID; it never unpatches another plugin.

## 7. Trace protocol

Every record is one JSON object with a fixed key order. The writer emits and
the parser requires the exact field set and order for schema version 1;
unknown, missing, duplicated, or reordered fields are rejected. Strings use
JSON escaping for quotes, backslashes, and every U+0000--U+001F character.
Integers use invariant formatting, booleans are unquoted lowercase JSON
values, and null is unquoted. Canonical integer text is `0` or an optional `-`
followed by a nonzero digit and zero or more digits; `-0`, plus signs, and
leading zeroes are rejected.

Valid Unicode outside the required escape set is emitted as literal UTF-8,
not optional `\u` escapes; `/` is likewise literal. The exact escapes are
`\"`, `\\`, `\b`, `\f`, `\n`, `\r`, and `\t`, with every remaining control
encoded as lowercase `\u00xx`. An unpaired UTF-16 surrogate faults capture.
Each encoded line, including its LF, is at most 16 MiB, and the complete trace
is at most 128 MiB. The sink checks the line bound before writing. The parser
requires those canonical escape spellings, reads with the same streaming
bounds, and rejects an oversized line or file rather than allocating it
without limit.

UTC timestamps use .NET's invariant round-trip `O` representation from a UTC
`DateTime`. `run_id` is `Guid.NewGuid().ToString("N")`. Every record repeats
`schema_version` and `run_id` so a detached line cannot be mistaken for part
of another run. The concrete values in the examples illustrate valid encoded
values; `{}` in a `capture` or `last_capture` position abbreviates the complete
capture object from section 7.2 and is never an empty object on disk.

The parser requires `run_id` to be exactly 32 lowercase hexadecimal
characters, the assembly hash to be exactly 64 lowercase hexadecimal
characters and equal the reviewed value, and timestamps to round-trip to UTC
with the exact seven-fractional-digit `O` form shown below. The finish time
must not precede the start time. All schema integers are JSON integers rather
than floats or booleans and must fit signed 32-bit range; counts, indices, and
`settle_frames` are additionally nonnegative within their narrower stated
bounds.

### 7.1 Run record

The first line is:

```json
{
  "kind": "run",
  "schema_version": 1,
  "run_id": "0123456789abcdef0123456789abcdef",
  "mode": "passive",
  "game_assembly_sha256": "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564",
  "plugin_version": "0.2.0",
  "input_sha256": null,
  "expected_input_count": 3,
  "started_at_utc": "2026-07-31T19:09:50.3199100Z"
}
```

The plugin computes the assembly hash from the exact managed assembly before
opening the trace and requires the reviewed game hash. Passive mode has no
input file, so `input_sha256` is present and null; future replay can use the
same versioned field.

### 7.2 Capture object

Initial, step, and error records embed a capture object with exactly:

```json
{
  "raw_save": "opaque-game-save",
  "state_identity": "123456789",
  "level": "",
  "overworld": false,
  "won": false,
  "returning": false,
  "have_ever_cooked_all": false,
  "lost_reason": "",
  "display_name": "",
  "sausages_cooked": 0,
  "movement_count": 0,
  "pushes_to_try": 0
}
```

The adapter maps the fields without inference:

- `raw_save = gamestate.Save(false, false)`;
- `state_identity = RuntimeHelpers.GetHashCode(gamestate)` formatted as
  invariant decimal;
- `level = gamestate.pushtargetlevel ?? ""`;
- `overworld = gamestate.overworld`;
- `won = gamestate.won`;
- `returning = gamestate.returning`;
- `have_ever_cooked_all = gamestate.haveevercookedall`;
- `lost_reason = gamestate.lostreason ?? ""`;
- `display_name = gamestate.displayname ?? ""`;
- `sausages_cooked = gamestate.sausagescooked`;
- `movement_count = gamestate.movements.Count`; and
- `pushes_to_try = gamestate.pushestotry`.

`raw_save`, `gamestate.movements`, and every required object must be non-null;
a null faults capture. The three nullable game strings listed above normalize
to the empty string and no other field has null normalization. Observation
reads `lostreason` directly; it must not call `GameState.Lost()`, which can
mutate that field. The three numeric capture fields must be nonnegative signed
32-bit values; quiescence later narrows `movement_count` and `pushes_to_try` to
zero.

`state_identity` may have a leading minus sign. Its encoded form is `0` or an
optional `-` followed by a nonzero decimal digit and zero or more decimal
digits; plus signs and leading zeroes are rejected, and parsing must round-trip
within signed 32-bit range.

The stability signature is SHA-256 over `raw_save`, `state_identity`, and every
remaining capture field in the listed JSON order. Strings contribute their
unescaped UTF-8 bytes, booleans contribute ASCII `true` or `false`, and
integers contribute invariant ASCII decimal. Each byte string is preceded by
its four-byte unsigned big-endian length; the hash input is the concatenation
of those length/value pairs. Concatenation without lengths or reliance on JSON
object order is not accepted.

### 7.3 Initial record

After two matching initial quiescent samples, the plugin writes:

```json
{
  "kind": "initial",
  "schema_version": 1,
  "run_id": "0123456789abcdef0123456789abcdef",
  "input_index": null,
  "capture": {}
}
```

No correlated `Game` gameplay attempt may have been observed before the initial
record. Such an input faults the run instead of becoming an ungrounded step;
the pre-`Game` title/profile navigation in section 8.3 is outside this rule.

### 7.4 Step record

Each attempted input produces exactly one terminal record:

```json
{
  "kind": "step",
  "schema_version": 1,
  "run_id": "0123456789abcdef0123456789abcdef",
  "input_index": 0,
  "input": "West",
  "accepted": true,
  "movement_scheduled": true,
  "settle_frames": 8,
  "state_replaced": false,
  "capture": {}
}
```

`input_index` is zero-based and contiguous. `input` is exactly `North`,
`South`, `West`, `East`, or `Undo`. `accepted` for a direction is the exact
`GameState.ProcessInput` return. `movement_scheduled` is the immediate
post-return `GameState.Moving()` result. Undo is accepted only when
`RestorePrevState` is observed inside the corresponding `DoUndo` context; its
`movement_scheduled` value is the `GameState.Moving()` result observed at the
top-level `DoUndo` exit. Any other native direction value faults instead of
being coerced into the five-value trace vocabulary.

An unexpected state replacement is an error rather than a successful step,
so every schema-v1 passive step has `state_replaced: false`. The field remains
explicit to keep the record contract aligned with the later replay design.

### 7.5 End record

After the third step has been successfully flushed, the plugin writes and
flushes:

```json
{
  "kind": "end",
  "schema_version": 1,
  "run_id": "0123456789abcdef0123456789abcdef",
  "input_count": 3,
  "finished_at_utc": "2026-07-31T19:11:00.0000000Z"
}
```

The sink must then close successfully. Only after the close does the plugin
log the exact completion marker:

```text
SSR oracle passive trace complete
```

The driver enters `Done` and ignores later observations. It does not quit the
game or change input behavior.

### 7.6 Error record

When recording is still possible, a fault writes and flushes exactly one:

```json
{
  "kind": "error",
  "schema_version": 1,
  "run_id": "0123456789abcdef0123456789abcdef",
  "input_index": 1,
  "input": "North",
  "code": "settle_timeout",
  "message": "input did not settle",
  "settle_frames": 600,
  "last_capture": {}
}
```

Schema-v1 error codes and messages are closed:

| Code | Exact message |
| --- | --- |
| `patch_install_failed` | `observation patch installation failed` |
| `input_before_initial` | `manual input arrived before initial capture` |
| `overlapping_input` | `manual input arrived while settling` |
| `unexpected_input` | `native input was outside the passive vocabulary` |
| `unscoped_process_input` | `manual-looking input occurred outside the native poll scope` |
| `hook_order_mismatch` | `observation hook order mismatch` |
| `game_method_exception` | `observed game method threw` |
| `observer_exception` | `passive observer failed` |
| `capture_failed` | `game-state capture failed` |
| `record_too_large` | `encoded trace record exceeded its limit` |
| `initial_settle_timeout` | `initial capture did not settle` |
| `settle_timeout` | `input did not settle` |
| `state_replaced` | `game state identity changed` |
| `save_path_changed` | `isolated save path changed` |

The parser requires the exact code/message pairing. Exception details remain
in the private canonical log and do not make trace bytes nondeterministic.
The marker-only startup/sink codes are exactly `invalid_mode`,
`invalid_configuration`, `invalid_assembly`, `invalid_reflection`,
`invalid_path`, `trace_exists`, `save_redirect_failed`, and `trace_io_failed`.
They never appear in a successfully written error record. The canonical-log
monitor accepts a failure marker only when its code belongs to the record-code
table or this marker-only set. A record-code marker is authenticated only
after two stable descriptor-relative reads produce the same structurally valid
closed terminal-error trace and that trace's final `ErrorRecord.code` equals
the marker suffix. Marker-only codes deliberately do not require a valid
trace: startup may precede trace creation, and `trace_io_failed` may leave only
absent, partial, or malformed trace bytes.

Error fields follow one rule for every code. Top-level Restart is the sole
override: it always uses null input fields and reports the active attempt or
initial frame count, or zero when no budget is active. For every other fault,
if an attempt is pending, `input_index` and `input` identify that attempt and
`settle_frames` is its current committed frame count, except that the
pre-capture deadline-overrun rule in section 8.6 reports
`min(next_frames, 600)`. Otherwise an offending in-scope manual input uses the
next index and its mapped input with `settle_frames: 0`; every other fault uses
null input fields and the current initial frame count only while an initial
budget is active, or zero when no budget is active. `last_capture` is the most
recent successfully constructed, size-bounded complete capture in the current
initial/attempt epoch, whether or not it formed a matching pair, and is null
when none exists. When no attempt is pending, an unknown native input uses a
null `input`, because it cannot be represented by the allowed enum; during a
pending attempt, that attempt's input fields retain precedence.

A terminal-error trace has exactly one error record last, has no end record,
and may contain only the successfully flushed initial and contiguous step
prefix that preceded the fault.

After flushing an error record, the plugin attempts to close the sink and then
logs `SSR oracle passive trace failed: <code>`. If writing, flushing, or
closing the sink itself fails, the plugin instead logs
`SSR oracle passive trace failed: trace_io_failed`; the log marker is then the
only authoritative terminal signal and no false error-record claim is made.

The first transition to `Faulted` wins atomically. It owns the sole error
record and sole terminal failure marker. Later callbacks still clear their own
bookkeeping and preserve original game exceptions, but they cannot change the
chosen code/message, append another terminal record, or emit another terminal
marker; any best-effort secondary diagnostic uses ordinary non-terminal
logging.

## 8. Passive observation and settling

The driver phases are:

```text
Disabled -> AwaitGame -> AwaitInitialNeutral -> Ready
Ready -> Settling -> Ready
Ready -> Settling -> Done
any active phase -> Faulted
```

### 8.1 Observation hooks

Passive mode installs observation-only patches for:

- private `Game.Update` postfix and finalizer, to sample after normal frame
  logic and to fault safely if the original update throws;
- private `Game.DoPlayerInput` prefix, postfix, and finalizer, to delimit one
  native player-poll scope;
- private `Game.Playerinputstring` postfix, to observe neutral physical-input
  polls, defined as an observed return value of `Direction.None`, without
  changing the returned direction;
- `GameState.ProcessInput` prefix, postfix, and finalizer, to pair only an
  in-scope manual direction with its exact acceptance result and immediate
  movement state;
- `Game.DoUndo` prefix, postfix, and finalizer;
- private `Game.RestorePrevState` prefix, to prove an undo restored history;
- `Game.DoRestart` prefix, postfix, and finalizer, to reject a top-level restart
  from the trace vocabulary while balancing its nested undo/restore bookkeeping;
  and
- `Game.SetGameState` prefix, postfix, and finalizer, to detect identity
  replacement.

The pinned signatures are exact:

| Type | Visibility and signature |
| --- | --- |
| `Game` | `private instance void Update()` |
| `Game` | `private instance void DoPlayerInput()` |
| `Game` | `private instance Direction Playerinputstring()` |
| `GameState` | `public instance bool ProcessInput(Direction)` |
| `Game` | `public instance void DoUndo()` |
| `Game` | `private instance void RestorePrevState(GameState.BakStruct)` |
| `Game` | `public instance void DoRestart()` |
| `Game` | `public instance void SetGameState(GameState)` |
| `GameState` | `public instance bool Moving()` |
| `GameState` | `public instance string Save(bool, bool)` |

Required fields are also exact: `Game.gamestate: GameState`,
`Game.exitSequence: bool`, `Game.bluespawnanim: bool`, and
`Game.escmenu: GameObject` are public instance fields;
`Game.endingsequence: bool` is public static; `Game.leaving: bool`,
`Game.gameover: bool`, and `Game.exploding: bool` are private instance fields.
The capture/gate uses public instance `GameState` fields
`player: Entity`, `movements: List<Movement>`,
`worldsausagespawns: List<Coord>`, `pushestotry: int`,
`pushtargetlevel: string`, `overworld: bool`, `won: bool`,
`returning: bool`, `haveevercookedall: bool`, `lostreason: string`,
`displayname: string`, and `sausagescooked: int`, plus public static
`GameState.shouldredrawcoffins: Coord`. Save isolation requires public static
`SaveGame.homePath: string` and `SaveGame.PersistentDataPath: string`.

Every prefix/postfix uses balanced depth or token bookkeeping. Missing,
duplicated, nested outside the reviewed pattern, or out-of-order callbacks
fault the trace. Prefixes and postfixes are `void`, never skip the original,
and never modify `ref` arguments or `__result`; a finalizer's sole return is
the identical original exception reference or null.

Every patch entrypoint is an exception firewall: all observer, capture, sink,
and logging exceptions are caught before control returns to the game. The
driver transitions to `Faulted` and reports best-effort without propagating an
observer exception. A finalizer clears only this plugin's outstanding scope;
if the original game method threw while the driver was active, it faults with
`game_method_exception` best-effort. If an earlier fault already won, it emits
at most an ordinary secondary diagnostic. In both cases it returns the
identical exception object unchanged and never suppresses, replaces, or wraps
the game's exception. Tests inject failures at each callback boundary and
prove the original arguments, return result, exception identity, and remaining
normal game path are unchanged.

### 8.2 Exact quiescence gate

Sampling is quiescent only when all of these hold:

```text
game and gamestate exist
gamestate.player exists
gamestate.Moving() is false
gamestate.pushestotry == 0
game.exitSequence is false
Game.endingsequence is false
game.bluespawnanim is false
private game.leaving is false
private game.gameover is false
private game.exploding is false
game.escmenu == null or game.escmenu.activeSelf is false
GameState.shouldredrawcoffins == Coord.Invalid
gamestate.worldsausagespawns.Count == 0
```

The adapter validates every required method and field at startup. A missing or
type-mismatched member aborts passive mode rather than weakening the gate. The
menu expression uses Unity's overloaded `== null`, so a destroyed-object
pseudo-null counts as absent; it intentionally uses `activeSelf`, not
`activeInHierarchy`.

### 8.3 Initial capture

The launch begins on `TitleScreen`, before a `Game` exists. After the three
canonical boot markers are authenticated, the probe instructs the operator to
press and release `action` once on the default `Start` selection, then press
and release `action` once on default empty Slot 1. The pinned decompilation
shows those actions load `ProfileSelect` and then `WorldExplore`; the newly
empty isolated save makes slot index 0 the default. Title/profile menu input is
outside every patched `Game` method and is neither a trace attempt nor
`input_before_initial`. Save redirection is already active during this phase.

After the second confirmation, the operator releases every control and waits.
Once a usable `Game` exists, any correlated direction or top-level Undo before
the initial record does fault with `input_before_initial`; it is never silently
treated as menu navigation.

The first observation of a usable `Game` opens an initial epoch with frame
count zero, a new monotonic start time, `neutral_seen: false`, and no sample
candidate. A `GameState` replacement before the initial record opens a new
initial epoch with all four values reset. The driver then waits for an observed
neutral `Playerinputstring` poll and two consecutive quiescent update-postfix
samples with identical complete stability signatures.

Within an epoch, a `Direction.None` poll sets `neutral_seen`; a cardinal poll
clears it and clears the sample candidate. Only update-postfix samples observed
after `neutral_seen` in that same epoch can enter the matching pair. Thus a
neutral poll must precede the first eligible sample, and neither a pre-reset
neutral poll nor a pre-reset candidate can leak across state replacement.

The initial budget is 600 update-postfix samples or 30 monotonic seconds;
exhausting either limit faults with `initial_settle_timeout`.

After the initial record is successfully flushed, the driver becomes `Ready`
and the plugin logs exactly once:

```text
SSR oracle passive trace ready: 0/3
```

This marker is the operator boundary: the probe does not request an action and
the operator is instructed not to provide one until the marker is authenticated
in the canonical log. An earlier in-scope input faults rather than being
suppressed. A `GameState` replacement after the initial record emits no step and
faults with error code `state_replaced`; the pending input fields are populated
only when the replacement occurred during an attempt.

### 8.4 Direction capture

`DoPlayerInput` opens one native poll scope. Its nested `Playerinputstring`
postfix records exactly one returned direction. A nested `ProcessInput` opens
a manual attempt only when that poll returned one cardinal direction, the
argument is the identical direction, and no prior manual `ProcessInput` was
seen in the scope. Its postfix supplies `accepted` and
`movement_scheduled`, after which the driver enters `Settling`.

A normal `DoPlayerInput` scope may contain zero polls when the game's own early
gate returns before `Playerinputstring`, or one poll. A poll outside such a
scope or a second poll in one scope is `hook_order_mismatch`. A normal scope
that contains a cardinal poll but no `ProcessInput` is valid filtered input and
opens no attempt.

The pinned game also calls `ProcessInput` from `AutomaticPlayerTick` while
resolving automatic BBQ behavior. A `ProcessInput` call outside the correlated
`DoPlayerInput` scope is therefore an internal consequence, not a new manual
step. It is observed but ignored while awaiting the initial state or settling.
If it occurs while the driver is stably `Ready`, it faults with
`unscoped_process_input`, because the previous settling boundary was
incomplete. A cardinal poll that the game's own `DoPlayerInput` logic filters
before `ProcessInput` is likewise not a trace step; this includes held-key
suppression after a refused direction.

Sampling does not occur in the `ProcessInput` postfix because movements,
automatic ticks, level changes, and redraw work may still be pending. Multiple
polls, mismatched directions, or multiple manual `ProcessInput` calls inside
one native scope fault with `hook_order_mismatch`.

### 8.5 Undo capture

`DoUndo` opens an undo context. `RestorePrevState` marks that context accepted.
At normal top-level `DoUndo` exit, the adapter samples
`game.gamestate.Moving()` for `movement_scheduled`, closes the context, and
starts settling whether the undo was accepted or refused. Undo calls nested
inside `DoRestart` are not passive input attempts. A depth imbalance, a restore
outside an undo context, or a second top-level undo while one is open faults
the run.

An outermost `DoRestart` in any active phase immediately faults with
`unexpected_input` and null input fields because `Restart` is outside the
schema-v1 vocabulary. The observer still calls the original method unchanged.
Its prefix first establishes restart depth, so any recursive `DoRestart`,
nested `DoUndo`, or `RestorePrevState` callback only balances bookkeeping and
cannot open a step or emit a second fault. A refused early-return restart and
an accepted in-place restore therefore have the same trace outcome. In `Done`,
as with every later observation, restart is ignored because the sink is already
closed.

### 8.6 Settled terminal capture

Opening a direction or Undo attempt starts a new attempt epoch and clears
`neutral_seen` and the sample candidate. As during initial capture, a neutral
poll sets the flag, while any later cardinal physical poll clears the flag and
candidate. After an attempt, the driver requires:

1. at least one actually observed neutral physical-input poll after the
   attempt;
2. the exact quiescence gate;
3. two consecutive update-postfix samples with identical complete signatures;
   and
4. `ReferenceEquals` equality with the exact `GameState` object retained when
   the attempt opened, independent of the diagnostic identity integer.

The first matching pair flushes exactly one step. After step 0 or 1 is flushed,
the driver becomes `Ready` and logs exactly one corresponding progress marker:

```text
SSR oracle passive trace ready: 1/3
SSR oracle passive trace ready: 2/3
```

The probe surfaces each instruction only after authenticating its marker, and
the operator waits for it before the next action. Unlike the later
high-throughput replay design, a new native attempt never acts as an early
finalization boundary. If another attempt begins before the two-sample rule is
satisfied, the run faults with `overlapping_input`.

The settle budget begins when the native attempt opens. The frame counter
advances once per observed `Game.Update` postfix while that attempt is pending,
including the postfix of the update in which it opened. Initial epochs use the
same counting rule beginning with the first update postfix at or after epoch
opening. At each postfix the driver performs this exact order:

1. compute `next_frames = current_frames + 1` and read monotonic elapsed time;
2. if `next_frames > 600` or elapsed time is greater than 30 seconds, fault
   before capture; otherwise commit `current_frames = next_frames`;
3. verify save-path and identity invariants;
4. if `neutral_seen` and quiescent, construct a capture and update the matching
   candidate;
5. if that produces the second identical sample, emit the initial or step
   record and succeed for the epoch; otherwise
6. fault when the frame count is at least 600 or elapsed time is at least 30
   seconds.

A matching pair on frame 600 or at exactly 30 seconds wins over timeout; the
first callback after either boundary faults before sampling, so a long Unity
stall cannot become a late success. For a pre-capture overrun,
`settle_frames` is `min(next_frames, 600)`. A successful step requires two
distinct update-postfix samples, so its `settle_frames` lies in `2..600`; an
error's value lies in `0..600`. If Unity stops producing observer callbacks,
the plugin cannot self-report the monotonic deadline; the outer 300-second
process deadline remains the terminal bound. The driver never skips or retries
an input. Time spent `Ready` between manual attempts consumes only that global
budget, not a settling budget.

## 9. Python validation

`read_oracle_trace_stream(stream, *, source=...)` performs lexical, per-record,
and sequence parsing on an already-authenticated binary stream without
reopening its name. `read_oracle_trace(path)` is only a convenience wrapper
that opens the path once and delegates to that stream API. The retained
descriptor-relative runtime probe always uses the stream API. Parsing
requires:

- UTF-8 without BOM, LF-delimited complete JSON objects, and a final LF;
- one run record first;
- identical schema version and run ID across all records;
- exact key order and fields, no duplicate JSON keys, no non-finite numbers,
  and no values of the wrong JSON type or allowed range;
- the reviewed assembly hash, `mode == "passive"`, plugin version `0.2.0`,
  null `input_sha256`, and expected count three; and
- exactly one of these terminal shapes:
  - success: one initial record second, exactly three steps with indices
    `0, 1, 2`, and one end record last with input count three; or
  - failure: either `run, error`, or `run, initial`, zero to three contiguous
    step records, and `error` last, always with no end record.

An error record's non-null `input_index` must equal the length of the flushed
step prefix, and a non-null `input` must belong to the five-value vocabulary.
Agreement with the actual faulting runtime event is a producer invariant from
section 7.6, not something a detached trace can independently prove. The
structural parser returns the terminal outcome and records. It does not present
a well-formed error trace as a successful capture.

`require_passive_success(trace)` rejects the failure shape, then applies the
successful record-count and relational contract below. The command-line tool
uses success validation by default; an explicit `--structural-only` mode may
be used to inspect retained terminal-error traces without reporting the gate
as passed.

The passive integration validator additionally requires:

1. step 0 is a direction with `accepted == true`,
   `movement_scheduled == true`, and its `raw_save` differs from the initial
   `raw_save`;
2. step 1 is a direction with `accepted == false`,
   `movement_scheduled == false`, and its complete capture equals step 0's
   complete settled capture field for field;
3. step 2 is `Undo`, is accepted, has `movement_scheduled == false`, and its
   complete capture equals the initial capture field for field;
4. every initial and step capture has `movement_count == 0` and
   `pushes_to_try == 0`; and
5. every step has `state_replaced == false`.

Complete equality includes `state_identity` and every envelope field, not only
`raw_save`. These stronger relations are valid only for the deliberately
simple no-transition acceptance scenario selected for this milestone. The
pinned `DoUndo -> RestorePrevState` path calls `gamestate.RestoreSave` in place
rather than replacing the `GameState`, so identity equality is an explicit
decompilation-backed expectation.

The validator does not infer mechanics from those relations. A failure means
the capture gate or chosen manual scenario did not satisfy this milestone; it
is not labeled a simulator bug.

## 10. Bounded runtime probe and evidence

The runtime gate remains separately approved and executes exactly one launch.
The controller exposes that complete Tahoe/artifact/log/process/ordinary-save
check as a standalone read-only preflight which allocates no evidence or save
directory, performs no installer operation, and acquires no launcher. The
operational gate runs it freshly before mutation; a successful older preflight
is never treated as authorization or cached proof. The standalone preflight
includes reproducible plugin verification, installed healthy `official`
status, and the ordinary-save proof defined below. After private layout
allocation, the in-run pre-mutation gate separately proves the newly selected
exact trace target absent before any installer operation.

The Tahoe check invokes absolute `/usr/bin/sw_vers -productVersion` with a
fixed `C` locale and a five-second bound, accepts only the exact `26.6` product
version, and retains that value in the standalone preflight result. A missing,
failed, malformed, or different version stops before private allocation,
installer mutation, or launcher acquisition. The same observed version is
carried into the final `passive-probe.json` result on every safely publishable
success or failure path.

The approved operation is:

1. capture a bounded no-follow fingerprint, or retained absence-chain proof,
   for the original `SaveGame.PersistentDataPath` tree;
2. exclusively allocate one new private output/run directory below ignored
   `data/oracle/` and one new, empty, separate isolated-save directory, set both
   to mode `0700`, and prove the exact trace target is absent;
3. generate and hash a passive config pointing its output to that run
   directory and its saves to the isolated-save directory;
4. deploy the reproducible plugin and passive config only through the
   installer;
5. deploy the reviewed patched preloader/provenance and require healthy
   `patched` status;
6. recheck the ordinary-save proof and empty isolated-save directory, then
   launch the BepInEx wrapper once in a new process group;
7. authenticate the three canonical boot markers, surface the two-confirmation
   menu-navigation instruction, authenticate `ready: 0/3`, surface the
   accepted-direction instruction, authenticate `ready: 1/3`, surface the
   blocked-direction instruction, authenticate `ready: 2/3`, surface the Undo
   instruction, then require the exact completion marker and a fully validated
   closed `passive-trace.ndjson`;
8. terminate and reap the complete process group;
9. stage and validate the canonical log, any bounded stable trace bytes,
   generated-config hash, isolated-save inventory, and four stage-specific
   installer/signature snapshots;
10. recapture the ordinary-save proof and require exact equality with the
    prelaunch proof;
11. transactionally deploy the pinned Mode-off config through the installer;
12. restore the official preloader;
13. verify healthy `official` status, exact Mode-off bytes, unchanged assembly,
    exact reproducible plugin, absent live compatibility roots, no remaining
    game, launcher, child/orphan helper, or other probe process, and an
    unchanged ordinary-save proof; and
14. construct, fsync, and exclusively publish `passive-probe.json` last,
    including the cleanup outcome and every retained secondary error.

The global probe timeout is 300 seconds so the operator can perform the three
manual actions. Each transition still has its independent 600-frame/30-second
settling limit. From launch through termination, the canonical-log monitor
continues watching the canonical file, numbered fallback family, and
`preloader_*.log` failure family. The exact plugin failure marker, a new member
of either failure family, premature process exit, or malformed/missing progress
marker is terminal failure and triggers prompt process-group cleanup rather
than waiting out 300 seconds. The probe never treats terminal stdout as
authoritative; canonical retained files remain authoritative.

The ordinary path is the pinned game's unmodified default,
`~/Library/Application Support/unity.increpare games/Sausage`, expanded from
the current account without following links. An existing tree must contain
only real directories and regular files, with at most 4,096 entries and 256
MiB of regular-file bytes; otherwise preflight refuses the launch. Each sorted
entry, including every directory, records relative path, type, device/inode
identity, mode, actual size, and nanosecond mtime/ctime; regular files also
record SHA-256. The present root carries the same metadata, and an absent-tree
proof gives every existing no-follow ancestor the same metadata before naming
the first missing component. Descriptor-relative no-follow opens and
before/after stat agreement are mandatory. This preserves observable directory
changes even when a file is created and deleted between lifecycle snapshots.
Success requires an identical proof after the process exits and again in final
verification. The isolated save path is canonicalized disjoint from the
ordinary tree in both directions.

Both private directories are mode `0700`. After process termination and before
publication, every retained regular evidence file is verified and secured to
mode `0600`. The trace probe uses its own versioned `passive-probe.json`; it
does not change the existing boot probe's schema-v1 payload or publish any
canonical JSON before restoration and final verification finish.

Each of the four passive lifecycle snapshots wraps the complete unchanged boot
snapshot with the observed installed plugin SHA-256, observed installed config
SHA-256, and the complete installer status/manifest evidence captured at that
stage. The top-level requested artifact hashes never substitute for those
observations. The legacy boot-probe payload remains byte-for-byte unchanged.

After the launched group is reaped, evidence collection treats `passive.cfg`
as required and `passive-trace.ndjson` as optional. If a stable bounded trace
exists, it is secured and retained even when lexical or structural parsing
fails; the private result records its hash, size, parse status, and nullable
terminal outcome/error code. An absent optional trace is valid evidence for a
startup failure. A symlink, special file, oversized file, or unstable identity
still makes publication unsafe rather than being silently omitted.

The process-absence check explicitly excludes the currently executing
controller PID, which must remain alive to publish the final JSON. It requires
no descendant, orphaned helper, launcher, game, or second matching probe
process; the controller exits only after publication and returning its final
result to the caller.

The isolated-save directory is not moved into the published evidence
directory and is never automatically deleted. The probe secures its reachable
regular files to mode `0600` and directories to `0700` through a bounded
descriptor-relative no-follow walk. A symlink or other unsupported type makes
the gate fail but is preserved without traversal. The probe records the exact
save path plus a sorted path/type/mode/size/SHA-256 inventory in
`passive-probe.json`, so a failed run remains diagnosable without treating save
bytes as committed evidence. On a cleanup or restoration failure, the
controller best-effort publishes an explicit failure payload only if the
evidence transaction remains healthy; it never claims final health. If safe
publication is unavailable, the private staging and recovery evidence remain
in place.

Real traces, isolated saves, generated passive configs, and recovery trees
remain ignored. Documentation may record only reviewed hashes, non-sensitive
summary values, exact commands, and the pass/fail result.

## 11. Failure and restoration behavior

Startup faults before hooks or trace creation on an invalid assembly,
reflection surface, mode, configuration cardinality, path, save isolation,
existing trace, or expected count.

Runtime faults include:

- input before the initial record;
- overlapping attempts;
- unscoped or unexpected native input and hook depth/order mismatch;
- unexpected `GameState` replacement;
- save-redirection drift, capture/serialization failure, or contained observer
  exception;
- an original observed game-method exception, preserved unchanged;
- unstable or timed-out settling;
- trace write, flush, or close failure; and
- completion marker without a closed valid end record, or a closed valid end
  record without the marker.

The plugin writes one error record when the sink remains usable, enters
`Faulted`, and never resumes. The outer probe preserves all reachable evidence
and terminates the process group. Ordinary-save proof mismatch is an outer
probe failure even if the plugin trace otherwise passes. The probe performs no
automatic second launch.

After a successful probe or an ordinary plugin/probe failure, cleanup attempts
the approved Mode-off installer deployment and official-preloader restore only
while their documented preconditions remain healthy and exact. If installer
state becomes invalid, config restoration is uncertain, or process cleanup
cannot be proven, the controller preserves evidence and stops. It never copies,
renames, deletes, re-signs, relaunches, or manually edits the installed tree as
an improvised repair. Transaction recovery evidence is never deleted.

## 12. Test strategy

Implementation follows test-driven development.

### 12.1 Unity-free C# tests

The existing dependency-minimal harness covers:

- every driver phase and legal transition;
- two-sample initial and terminal debounce with epoch-scoped neutral resets;
- candidate reset on every intervening active update without an eligible
  quiescent capture;
- frame/time boundary ordering, including success on the exact deadline;
- accepted, refused, and undo semantics;
- top-level Restart rejection before initial, while Ready, and while Settling,
  including refused and accepted/nested game paths;
- exact one-record cardinality;
- overlapping/unscoped input, state replacement, timeout, and hook imbalance;
- error-record best effort and Faulted finality;
- first-fault-wins terminal ownership when later callbacks also fail;
- the closed error-code/message table and deterministic error-field policy;
- deterministic JSON ordering and escaping;
- record/file bounds plus create-new, flush, close, partial-write, and
  existing-path behavior; and
- exact record-before-progress-marker and close-before-completion-marker
  ordering, with every marker emitted once.

### 12.2 Adapter and build tests

Tests and build checks cover:

- exact method and field signatures against the pinned game assembly;
- `DoPlayerInput`/`Playerinputstring` correlation and ignored internal
  `AutomaticPlayerTick -> ProcessInput` calls during settling;
- immediate adapter-owned `Moving()` samples after `ProcessInput` and at
  top-level Undo return;
- read-only Harmony callbacks and exception firewalls that preserve original
  arguments, results, exception identity, and game control flow;
- `Game.Update` original-exception handling when its normal postfix is skipped;
- a top-level Restart fault followed by an original Restart exception, proving
  one terminal signal and identical exception propagation;
- restart depth plus recursive-restart, nested-undo, and restore suppression
  without changing the original restart path;
- exact capture-member mapping, null policy, numeric ranges, and
  `GameState.Lost()` non-use;
- stable length-prefixed capture hashing;
- configuration cardinality and path rejection;
- existing trace-target, symlink-component, and overlapping-directory
  rejection;
- original HOME/path authentication and save-directory separation before a
  game instance is used;
- exact Run-flush, patch-install, activation, and boot-marker startup ordering,
  with owner-scoped cleanup after partial patch failure;
- passive load-marker emission only after save isolation and patch startup;
- the pinned Mode-off grammar and local ignored-fixture hash, with no config
  write, passive-key requirement, sink, save redirect, or observation patch;
- missing/unreadable config mapping to one typed pre-sink failure marker;
- an End/close followed by completion-reporter failure remaining immutable and
  failing the outer marker gate without another trace write;
- the existing load marker remaining unchanged;
- two clean plugin builds producing byte-identical DLLs; and
- a net35 compile gate for every Core increment and the reviewed CLR v2/net35
  final reference surface.

### 12.3 Python tests

Synthetic fixtures cover every valid record kind and reject malformed UTF-8,
BOM, CRLF, duplicate/reordered/unknown keys, mixed run IDs, skipped or repeated
indices, malformed hashes/timestamps/Unicode, non-ASCII timestamp digits,
missing initial/end, extra records, wrong counts or ranges, oversized
lines/files, truncated lines, and named-path replacement after a descriptor is
opened. They also cover malformed terminal-error prefixes, error traces
presented as success, and every failed three-step relation including an
envelope-only mismatch.

The full repository suite, Python compilation, diff check, reproducible plugin
build, fixture hashes, and read-only installed-state preflight run before any
runtime request.

### 12.4 Passive-probe tests

Synthetic process/log/filesystem fixtures cover:

- exclusive new empty save allocation and trace-target absence;
- bounded no-follow ordinary-save inventories, absence proofs, and every
  pre/post mismatch, including create-then-delete changes observable only in
  present-root or absent-ancestor directory metadata;
- boot-authenticated menu prompting, all three progress markers, control-release
  guidance, and complete operator-prompt ordering;
- matching closed terminal-error traces for record-code markers, plus absent,
  partial, malformed, and mismatched failure traces;
- prompt termination on plugin, numbered-log, preloader-log, early-exit, and
  global-timeout failures;
- standalone preflight proof that no allocation, installer mutation, or
  launcher acquisition occurs;
- full process-group reaping before installed-tree cleanup;
- staging before restoration and exclusive JSON publication only after final
  verification, with observed plugin/config hashes and full installer status
  in every reached lifecycle snapshot; and
- explicit failure payloads, secondary cleanup errors, and preservation when
  publication is unsafe.

### 12.5 Real-game acceptance

With fresh explicit approval, the operator uses the visible isolated starting
state and performs only the action named by each authenticated instruction:

1. after the authenticated boot/menu prompt, press and release `action` on
   default `Start`, then press and release `action` on default empty Slot 1;
2. after `ready: 0/3`, one direction that visibly succeeds;
3. after `ready: 1/3`, one direction that is visibly blocked; and
4. after `ready: 2/3`, Undo once.

During menu navigation the operator releases `action` and waits for the next
visible menu before the second confirmation. After each traced gameplay input,
the operator releases every control and waits for the next authenticated
marker before acting again.

The gate passes only when the canonical boot and completion evidence, strict
trace validator, process cleanup, Mode-off restoration, and final healthy
`official` installed state all pass, and the ordinary-save proof remains
identical. A runtime failure is retained and diagnosed offline; it is never
retried under the same approval.

## 13. Deliverables

Implementation is expected to add focused files rather than expand the
already-large boot observer indiscriminately:

- C# protocol DTOs, deterministic encoder, sink, Unity-free driver, capture
  adapter, passive hooks, and controller below `oracle/plugin/`;
- C# harness tests below `oracle/plugin/tests/`;
- `src/ssr_env/oracle_protocol.py` and `tools/oracle_trace_check.py`;
- a passive-probe module and CLI that reuse hardened observer primitives;
- Python protocol, probe, and integration-contract tests;
- minimal synthetic committed fixtures only if they add coverage that inline
  builders cannot; and
- runbook updates recording the successful 2026-07-31 canonical boot
  checkpoint and the new passive gate.

## 14. Completion boundary and next milestone

This milestone is complete only after the offline implementation is reviewed,
one separately approved passive runtime gate passes, all evidence is retained,
the ordinary-save proof is unchanged, and the installed tree is verified
healthy `official` with exact Mode-off configuration.

The next design will add raw-save parsing, semantic identity bridging, and
comparison of this trusted passive trace with the Python simulator. Native-path
automated replay remains gated on passive capture success; it is not implicitly
authorized or implemented by this design.
