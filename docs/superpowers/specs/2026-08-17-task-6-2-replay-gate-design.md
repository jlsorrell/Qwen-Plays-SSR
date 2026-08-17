# Task 6.2 Replay Coordinator and Live Gate Design

**Date:** 2026-08-17
**Status:** Approved conversationally; written-spec review pending

## 1. Purpose

Task 6.1 connected the proven passive driver to the real game while leaving
`replay` disabled. Task 6.2 completes the offline replay coordinator and then,
under two explicit user approvals, performs the first bounded live proof:

1. a three-attempt passive calibration against an isolated save; and
2. a one-input replay of the calibrated accepted direction from the restored
   identical starting save.

The milestone is deliberately split into an immutable offline implementation
slice and a separately authorized operational slice. Passing the offline slice
does not authorize an installed-game write or launch. Failing or deferring the
live gate does not invalidate an otherwise accepted implementation; it leaves
the milestone's operational status explicitly pending or failed.

## 2. Authority and baseline

Work begins from local `main` commit
`48d0f08f3f32a1a9e0c59f8a5aef18c2fb77094d`, the reviewed Task 6.1 tip.

Behavioral authority is applied in this order:

1. this addendum for the Task 6.2 milestone split and live-gate workflow;
2. `docs/superpowers/specs/2026-08-15-task-6-runtime-replay-design.md`
   for replay protocol, coordinator, native-path, and runtime behavior;
3. the accepted Task 5 driver designs and implementation for lifecycle,
   settling, terminal ownership, and serialized output; and
4. the accepted passive-capture and executable-oracle designs for ABI, path,
   save-isolation, installation, and trace safety.

This addendum overrides only the earlier Task 6 statements that a launch is
outside the milestone and must wait for Task 7. The offline implementation
slice remains launch-free. All other accepted Task 6 decisions remain in
force.

The historical executable-oracle and passive-probe plans are reference
material, not executable instructions. The descendant implementation plan
must be regenerated from this design, the accepted Task 6 design, and the live
tree.

## 3. Decision and rejected alternatives

### 3.1 Two immutable slices

The milestone contains:

1. **Offline replay implementation.** Implement, test, mutate, review, commit,
   and reauthenticate replay without changing or launching the installed game.
2. **Operational replay gate.** After the implementation is immutable and
   approved, use a reviewed runbook to deploy it transactionally, calibrate a
   passive trace, restore the isolated save, and run one replay token.

The operational slice has two independent go/no-go approvals. Approval one
authorizes only passive calibration. Approval two is requested only after the
calibration, restoration, and pre-replay state all authenticate.

### 3.2 Reviewed runbook, not another subsystem

The gate reuses the existing transactional installer, wrapper, protocol
reader, and ordinary project tools. The implementation does not add a second
installer, a reusable gate-runner state machine, or an automated UI driver.
The implementation plan supplies exact commands, targets, hashes, timeouts,
and rollback checks for the one bounded gate.

Rejected alternatives are:

- postponing the gate to a later milestone;
- automatically chaining calibration into replay without approval two;
- replaying a fixed or guessed token rather than deriving it from the same
  isolated starting state;
- using Undo as the sole live replay proof, because it is more state-dependent
  and does not prove cardinal traversal through `Playerinputstring`;
- expanding the first gate into a longer replay; and
- relying on ad hoc manual deployment or cleanup.

## 4. Offline replay architecture

The existing passive driver remains the single owner of Initial, Step, End,
Error, Close, Ready, Complete, and terminal arbitration. Replay adds a
coordinator around that driver rather than another settling state machine:

```text
strict replay config
    |
    v
read/hash/parse exact .dem bytes once
    |
    v
ReplayCoordinator waits for durable Initial + neutral readiness
    |
    +-- cardinal --> Playerinputstring --> DoPlayerInput --> ProcessInput
    |
    +-- Undo ---------------------------------------------> DoUndo
    |
    v
PassiveDriver settles and durably writes Step
    |
    v
coordinator advances only after Ready(completedInputs)
    |
    v
final Step --> End --> Close --> Complete
```

### 4.1 Components

The expected new Core files are:

- `oracle/plugin/Core/ReplayInput.cs`: immutable exact bytes, lowercase
  SHA-256 identity, strict UTF-8 decoding, and token parsing; and
- `oracle/plugin/Core/ReplayCoordinator.cs`: initial readiness, physical-input
  suppression, real neutral-poll accounting, one-update cardinal arming,
  native-path alignment, Undo initiation, and durable-Step advancement.

Narrow extensions are permitted only where the accepted Task 6 design already
requires them: protocol records, passive-driver cardinality, configuration,
runtime boundaries, controller, hooks, adapter, plugin composition, unit-test
registration, and `src/ssr_env/oracle_protocol.py`.

`Core` remains free of Unity, Harmony, BepInEx, concrete game types, and
filesystem-global state. The plugin remains C# 7.3/.NET 3.5 compatible. The
plugin and Run record version remain `0.3.0`; schema version remains 1.

### 4.2 Replay input and trace relations

The `.dem` file is read once. `input_sha256` covers its exact bytes, including
line endings and surrounding ASCII whitespace. Strict parsing accepts only
`North`, `South`, `West`, `East`, and `Undo` after ASCII trimming and rejects
an empty token stream.

A replay Run has a positive parsed input count and a 64-character lowercase
input hash. Passive remains exactly three attempts with a null input hash.
The Python reader validates both relations without weakening
`require_passive_success`.

`ExpectedInitialSha256` is the lowercase SHA-256 of the exact UTF-8 bytes of
the durable Initial record's `capture.raw_save`. A configured mismatch selects
`initial_state_mismatch` before any replay token is armed.

### 4.3 Native cardinal and Undo transactions

After Initial is durable, token zero requires the driver's stable Ready state,
two equal quiescent observations, and one consumed real neutral
`Playerinputstring` poll. Later tokens additionally require a neutral poll
after the preceding durable Step.

A cardinal is asserted for one eligible `Game.Update` only. The first
`Playerinputstring` call supplies the mapped native direction, and the
unmodified `DoPlayerInput` body owns the game gate, undo snapshot, refusal,
`ProcessInput`, and movement scheduling. The same update must contain exactly
one matching `ProcessInput` traversal. Missing, duplicate, mismatched, or late
traversal selects `replay_alignment_failed`; the token is not retried.

Replay suppresses physical directional input by returning native None whenever
no cardinal is armed. Passive mode never suppresses or synthesizes input.

Undo is initiated once through public `Game.DoUndo()` after the same readiness
gate. Acceptance requires `RestorePrevState` inside that exact Undo context.
No mode calls `GameState.ProcessInput` directly.

The current token index changes only after the driver's durable Step reports
`Ready(n)`. The final durable Step writes End and reports Complete without an
extra Ready or token increment.

## 5. Offline proof and immutable boundary

Implementation uses production-unchanged REDs before each production slice.
The final proof requires:

- forced no-restore net10 and net35 warning-as-error rebuilds;
- every named C# cohort and an exact full harness manifest;
- the complete Python suite;
- deterministic replay/concurrency stress with bounded barriers and no
  sleep-based race assertions;
- lean mutations for exact-byte hashing, initial-signature enforcement,
  physical suppression, one-update arming, native-path alignment, and no
  advancement before durable Step;
- scoped precommit specification and code-quality reviews;
- one exact-scope implementation commit with subject
  `feat: replay SSR inputs through native game path`; and
- immutable postcommit package authentication, reruns, and independent
  re-reviews with a clean repository and index.

No command in this slice may deploy the candidate DLL, alter the installed
manifest or config, write an active save, or launch the game.

Approval one is requested only after all of these checks pass and the exact
reviewed DLL hash is known.

## 6. Operational layout and preflight

The runbook uses one unique ignored gate root with non-nested sibling paths for
live isolated save, baseline save, output, input, backups, logs, and evidence.
The configured input file is not under the output or save directory. Trace
targets use unique safe RunName values and must be absent before deployment.

Before approval one, the runbook must prove and retain:

- the exact Task 6.2 commit, immutable package, reviewed DLL, and clean
  repository/index;
- no running SSR, Unity SSR, or retained wrapper process;
- a healthy oracle installer manifest and exact pinned game assembly, app,
  runtime, wrapper, and installed-file identities;
- an existing manifest-owned plugin and canonical UTF-8/LF config whose exact
  starting mode is `off`;
- exact pre-gate copies and hashes of the installed plugin and config;
- a stable, bounded, no-follow manifest of the ordinary save tree at
  `$HOME/Library/Application Support/unity.increpare games/Sausage`, or an
  equally authenticated proof that the leaf is absent;
- a stable, bounded, no-follow manifest and retained baseline copy of the
  isolated save tree; and
- absent passive and replay trace targets.

Tree manifests reject symlinks, special files, unstable reads, unsafe relative
names, more than 4,096 descendants, or more than 256 MiB of regular-file data.
They record each relative path, kind, mode, byte count, and file SHA-256 in
canonical byte order. A second scan must match before launch.

The existing `tools/oracle_install.py deploy` transaction is the only publisher
of the candidate DLL and active config. The runbook does not write inside
`Sausage.app`, alter `Assembly-CSharp.dll`, or use the ordinary save as a
fallback.

## 7. Approval one and passive calibration

Approval one authorizes exactly one passive deployment and launch.

The runbook:

1. deploys the reviewed DLL with passive mode, the isolated save, canonical
   settle limits, expected count three, and an absent create-new trace;
2. reauthenticates the installer manifest, published hashes, config bytes,
   paths, ordinary save, isolated baseline, and process absence;
3. launches the BepInEx wrapper in a new retained process group; and
4. monitors bounded logs and the trace while the user interacts with the
   visible game.

The user loads the isolated test state and, waiting for the reported boundary
between each attempt, performs in order:

1. one accepted cardinal that schedules movement;
2. one refused cardinal that schedules no movement; and
3. Undo, which is accepted through Restore and schedules no movement.

The game is then closed. The runbook requires the retained process group and
all identified SSR descendants to be absent.

The passive trace must satisfy `require_passive_success`: exact Run/Initial,
Steps 0-2, End order; contiguous indices; accepted moved cardinal; refused
cardinal with the same settled capture as Step 0; accepted Undo restoring the
Initial capture; End count three; no Error; and the reviewed assembly/plugin
relations.

If the attempt relation is wrong, the trace is incomplete, a timeout occurs,
or any identity changes, the run stops. Recalibration is a new approval-one
transaction with a new trace; it is not silently retried.

## 8. Calibration derivation and restoration checkpoint

After a valid passive run, the runbook derives rather than guesses:

- the replay token from passive Step 0's accepted non-Undo cardinal;
- the replay input bytes as exact UTF-8/ASCII `Token + "\n"`;
- the input SHA-256 from those exact bytes; and
- `ExpectedInitialSha256` from the exact UTF-8 bytes of the passive Initial
  `capture.raw_save`.

It preserves the post-passive isolated save for evidence, reconstructs the
live isolated path from the retained baseline through explicit sibling paths,
and proves the restored tree manifest equals the pre-gate manifest. It then
uses the transactional deployer to restore the exact pre-gate DLL and config,
leaving `Mode=off`.

Before approval two, the runbook reauthenticates the absent process, healthy
installer, exact off bytes, ordinary-save equality, isolated-save equality,
candidate DLL/package identity, passive trace hash and relation, replay input
bytes/hash, initial raw-save hash, and absent replay trace target.

Approval two is not requested unless every checkpoint passes.

## 9. Approval two and one-input replay

Approval two authorizes exactly one replay deployment and launch using the
derived one-token input.

The runbook transactionally deploys the same reviewed DLL with replay mode,
the restored isolated save, unique replay RunName, derived `InputPath`, and
derived `ExpectedInitialSha256`. It reauthenticates the publication and launches
the wrapper in a new retained process group.

The user loads the same isolated test state but provides no physical gameplay
input. The coordinator must authenticate the Initial raw save, consume a real
neutral poll, arm the calibrated cardinal for one update, observe exactly one
matching native `ProcessInput`, and settle one durable Step.

The successful replay trace must contain exactly Run, Initial, Step 0, and End,
with:

- mode `replay`, the derived input hash, and expected count one;
- Initial raw save equal to the passive Initial raw save;
- Step input equal to the calibrated cardinal, accepted true, and movement
  scheduled true;
- Step capture equal to passive Step 0 in every stable capture field and raw
  save, ignoring only process-local `state_identity`;
- End count one; and
- no Error, duplicate token, missing traversal, or extra Ready.

The game is closed and the retained process group is proven absent. The
runbook restores the isolated-save baseline and exact pre-gate DLL/config bytes
again, then authenticates final state.

## 10. Failure handling and cleanup

No failure advances to the next approval gate.

For a launch failure, timeout, malformed trace, identity change, or unexpected
runtime result, cleanup:

1. asks the retained process group to terminate gracefully within a fixed
   bound;
2. escalates only against that exact retained group if it does not exit;
3. never uses a broad process-name kill;
4. restores the pre-gate DLL/config through the transactional deployer;
5. restores the isolated-save baseline through explicit authenticated sibling
   paths;
6. rechecks the ordinary save, app/assembly/runtime, installer, processes, and
   repository; and
7. preserves all logs, traces, manifests, command statuses, and backup paths in
   the unique ignored evidence root.

Cleanup never deletes traces, backups, or evidence needed to diagnose a failed
restoration. If either installed-state or save restoration cannot be proven,
the runbook stops, preserves every recoverable artifact, and reports the exact
blocker. It does not attempt a broader repair or claim success.

## 11. Evidence and review

The ignored evidence root retains:

- both approval records and timestamps;
- implementation commit, package, DLL, and review identities;
- every command, exit status, stdout/stderr digest, and bounded timeout;
- pre/deployed/restored installer manifests, plugin/config bytes and hashes;
- app, assembly, runtime, wrapper, and code-signature evidence;
- pre/post ordinary and isolated save manifests;
- the baseline and quarantined post-run isolated saves;
- BepInEx logs and retained process-group lifecycle;
- passive/replay trace bytes, hashes, parsed summaries, and relational checks;
- derived `.dem` bytes/hash and Initial raw-save hash; and
- final Git/index/status and installed-state authentication.

Local traces, `.dem` input, saves, binaries, and operational evidence remain
ignored and uncommitted. No live result is folded into or used to rewrite the
already reviewed implementation commit.

After each live launch, the runbook produces a concise gate report and receives
an independent evidence/specification review before the milestone is called
complete.

## 12. Scope exclusions

This milestone does not:

- replay more than the one derived cardinal;
- compare a long simulator prefix or localize Cove;
- automate UI navigation or synthesize keyboard/mouse events;
- exercise replay Undo live (offline tests still cover it);
- call `GameState.ProcessInput` directly;
- change the game assembly, app bundle, Steam launcher, or ordinary save;
- add an installer or reusable operational runner;
- parse or compare the raw game-save format inside the plugin;
- commit local game assets, traces, saves, input, or evidence; or
- delete a failed gate's forensic artifacts automatically.

## 13. Completion criteria

The offline implementation slice is accepted when:

1. replay input has exact byte identity and positive cardinality;
2. initial readiness, physical suppression, native cardinal/Undo traversal,
   alignment, and durable-Step advancement match the accepted Task 6 design;
3. passive behavior remains exact;
4. net10, net35, complete C#, Python, stress, mutation, and review gates pass;
5. the implementation commit and package are immutable and authenticated; and
6. no game process or installed/user state changed during offline work.

The operational slice passes when:

1. both explicit approval boundaries were honored;
2. passive calibration satisfies the exact three-attempt relation;
3. the isolated save authenticates after each restoration;
4. the one-input replay starts from the calibrated Initial raw save and emits
   one native accepted cardinal Step matching the passive Step 0 stable state;
5. both traces end successfully with exact counts and no Error;
6. the ordinary save is byte-for-byte unchanged, including remaining absent
   when it was absent at preflight;
7. the game app, assembly, runtime, installer ownership, and repository remain
   authenticated; and
8. the exact pre-gate plugin/config state is restored with `Mode=off` and no
   game process remains.

Task 6.2 plus the replay gate is complete only when both slices pass. Otherwise
the final report distinguishes `implementation accepted` from
`operational gate pending` or `operational gate failed` without ambiguity.
