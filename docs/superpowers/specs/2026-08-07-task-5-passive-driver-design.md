# Task 5 Passive Driver Completion Design

**Status:** Approved section by section on 2026-08-07; written-spec review pending

## 1. Purpose

Task 5 completes the Unity-free passive driver that Task 4.2 left at the
durable Initial/Ready boundary. It adds manual input attribution, lifecycle
balancing, settled Step emission, and ordinary terminal completion without
changing the already accepted passive-capture architecture.

This is one umbrella design with three separately owned and reviewed slices:

1. Task 5.1 attributes direction and Undo attempts, writes every settled Step,
   and reports intermediate Ready markers.
2. Task 5.2 balances Restart, state replacement, and thrown-hook lifecycle.
3. Task 5.3 changes the post-third-Step branch to End, close, and Complete.

The three slices must remain separate TDD commits. Their boundaries interlock,
so the descendant plan requalifies all three together rather than repairing
Task 5.1 in isolation.

## 2. Accepted baseline and authority

The work starts from exact accepted Task 4.2 seal:

```text
S4 f5de26f3dea85f14f25e3540da9f29130e27a09b
└─ P4 6ade9cd2a06548741d104a38b6498f4e5b48af7f
```

The Task 5 design commit is the direct child of S4. The standalone execution
plan will descend from the accepted design commit. This is the meaning of
"starts from exact S4": the new design/plan chain branches at S4; the plan is
not required to omit its approved design parent.

The following S4 files are selected baseline authentication anchors. The
descendant plan must carry the exhaustive seal-bound anchor set described in
section 12.

| Path | SHA-256 |
|---|---|
| `oracle/plugin/Core/PassiveDriver.cs` | `0ab8b9dfb537577fb052e6e5dab2ca744bc08cfb92206e44fd00e4552cee56a6` |
| `oracle/plugin/Core/PassiveDriverBoundaries.cs` | `1a130383302b315f43f8643fab5c13ec8d643727c2095ca21929aac306cdf133` |
| `oracle/plugin/tests/PassiveDriverInitialTests.cs` | `0590e9ae35cc074e012dcffb86fae94e35bdd9d9225446b490bcce19de0c1b85` |
| `oracle/plugin/tests/PassiveDriverTestSupport.cs` | `ee3af9a57cc539262d2bd80e8f163ea60988087d39fe2600cbf3f38169d9edb9` |
| `oracle/plugin/tests/Program.cs` | `9372ea72e23ca9d8a95f2cce1f7146713b603ce7ea733fe2e0756a33c6b25004` |
| authoritative capture design | `33209340e884fcd580f68183c77b1b8ed6142a13eb30b7f7c530800832b8c8ef` |
| Task 4.2 correction plan | `52d899d9c058171f814e09e403f52d00897fad5c4b956fc3fa0930c2ae8eac4c` |
| Task 4.2 seal | `6a6c43466b32628551f473d839689533c1f2ef7e358e926f78594b1a4c767adb` |

The behavioral authority remains
`docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`.
The Task 4.2 correction plan and seal govern ancestry, immutable evidence, and
the requirement for this descendant rebase.

The design commit must have subject
`docs: design Task 5 passive driver completion`, exact S4 as its sole parent,
and exact one-file scope containing only this design path.

The legacy Task 5.1-5.3 bodies embedded in
`docs/superpowers/plans/2026-07-31-oracle-passive-plugin.md` are historical
input only. They are explicitly non-executable. The new plan must restate all
steps and regenerate all patches, hashes, diagnostics, and checkpoints without
delegating to or executing those bodies.

Task 4.2's seal, evidence, ledgers, historical briefs, and legacy monolithic
plan remain byte-identical.

## 3. Scope

### 3.1 In scope

- Manual cardinal-direction attribution through the native poll scope.
- Undo attribution through the Undo/Restore lifecycle.
- Attempt outcomes, stable-state identity, settling, and durable Step records.
- Restart rejection and nested Restart/Undo/Restore balancing.
- Successful and throwing state-assignment lifecycle.
- Expected-input-count storage and validated UTC handoff.
- Terminal End, close, Complete, fault arbitration, and idempotent disposal.
- Unity-free tests, net10 execution, compile-only net35 compatibility, targeted
  mutations, and independent reviews.

### 3.2 Out of scope

- Changes to `PassiveDriverBoundaries.cs`, `HookKind`, `HookToken`,
  `UpdateDirective`, `GateSample`, protocol DTOs, or sink/reporter interfaces.
- Unity or game-assembly dependencies in Core.
- Adapter patching, configuration, filesystem/path handling, plugin install,
  real-game launch, bounded runtime probing, or training-pipeline work.
- Reopening or extending Task 4.2 evidence.
- A new mutation ledger, controller replay ledger, or tracked seal.

Those operational concerns remain Tasks 6 onward.

## 4. State model and invariants

Task 5 activates the reserved Ready/Settling/Done transitions:

```text
Disabled -> AwaitGame -> AwaitInitialNeutral -> Ready
Ready -> Settling -> Ready
Ready -> Settling -> Done
any active phase -> Faulted
```

The accepted Task 4.2 invariants remain controlling:

- State, time, path, verified state, authorization, gate/capture, UTC, and
  completion preserve their established update order.
- Capture cannot precede authorization.
- A neutral observation and candidate are scoped to one epoch.
- A matching pair requires two distinct complete, bounded captures.
- Exact-boundary success wins; the first post-boundary callback faults before
  capture.
- Game-state identity is `ReferenceEquals` identity, never the diagnostic
  integer alone.
- Disabled, Faulted, Done, and disposed observations are output-inert, while a
  callback that already owns bookkeeping may still clear its own context.
- The first terminal owner wins atomically and the sink is closed at most once.

The constructor's existing expected-input-count validation remains unchanged.
Task 5.3 stores the validated value; it does not broaden the accepted schema.

## 5. Ownership and files

| Slice | Behavior ownership | Production files | Test and registration files |
|---|---|---|---|
| 5.1 | completed-input count; pending attempt/outcome; direction and Undo correlation and typed throw cleanup; stable-state reference; generalized settling; every durable Step; intermediate Ready | modify `PassiveDriver.cs`; create `PassiveDriverInput.cs` | modify `PassiveDriverTestSupport.cs` and `Program.cs`; create `PassiveDriverInputTests.cs` |
| 5.2 | Restart stack/depth; state-set context; state replacement; Restart/StateSet throw cleanup; kind-dispatched `ClearThrew`; lifecycle balancing | extend `PassiveDriver.cs` and `PassiveDriverInput.cs` only where required; create `PassiveDriverLifecycleHooks.cs` | modify `PassiveDriverInputTests.cs` and `Program.cs`; support remains unchanged |
| 5.3 | stored expected count; validated UTC handoff; post-third-Step terminal branch; End/Close/Complete; successful terminal ownership | extend `PassiveDriver.cs` and `PassiveDriverInput.cs`; create `PassiveDriverCompletion.cs` | modify `PassiveDriverTestSupport.cs` and `Program.cs`; create `PassiveDriverTerminalTests.cs` and the `PassiveDriverTests.cs` aggregator; input tests remain unchanged |

The implementation commits retain the approved subjects:

1. `feat: attribute passive input attempts`
2. `feat: balance passive lifecycle hooks`
3. `feat: finalize passive trace capture`

Task 5.1 must not own Restart/state-set behavior or completion. Task 5.2 still
must not store expected count, hand off UTC, or complete. Task 5.3 must not
move lifecycle ownership out of 5.2 or Step-write ownership out of 5.1.

## 6. Task 5.1: attempt attribution and Step emission

### 6.1 Pending-attempt state

One pending attempt retains:

- the next contiguous input index and schema input value;
- whether its native call has supplied an outcome;
- `accepted` and `movement_scheduled`;
- the exact opening `GameState` object;
- monotonic start, committed frame count, and neutral eligibility;
- the matching candidate and most recent bounded complete capture.

Only one attempt may be pending. A second attempt before settlement faults
with `overlapping_input`; it never finalizes or skips the prior attempt.

### 6.2 Direction correlation

`DoPlayerInput` opens exactly one native poll scope. Its nested
`Playerinputstring` postfix records exactly one returned direction. A nested
`ProcessInput` opens a manual attempt only when:

1. the poll returned one cardinal direction;
2. the `ProcessInput` argument is the identical direction; and
3. no earlier manual `ProcessInput` was observed in the scope.

The exact raw mapping is `0/1/2/3 -> North/South/West/East` and `8 -> None`.
An unknown native value faults with `unexpected_input`; it uses the next input
index and null input when no attempt is pending, while an existing pending
attempt retains field precedence.

The `ProcessInput` return supplies `accepted`; the immediate post-return
`GameState.Moving()` observation supplies `movement_scheduled`, after which
the attempt settles. A zero-poll early return and a cardinal poll filtered
before `ProcessInput` are valid and open no attempt. Duplicate polls,
mismatched directions, and multiple manual calls in one scope fault with
`hook_order_mismatch`.

A correlated cardinal `ProcessInput` observed before Initial becomes durable
faults with `input_before_initial` using the next input index and mapped input.
Its entered and threw paths own and idempotently clear their typed context in
5.1.

An unscoped `ProcessInput` is an ignored internal consequence while awaiting
Initial or while Settling. While stably Ready it faults with
`unscoped_process_input`, because the prior passive boundary was incomplete.

### 6.3 Undo correlation

Top-level `DoUndo` opens an Undo context. `RestorePrevState` marks that context
accepted. Normal top-level return samples `Moving()` for
`movement_scheduled`, closes the context, and begins settling whether the Undo
was accepted or refused.

A top-level Undo observed before Initial becomes durable faults with
`input_before_initial`, the next input index, and input `Undo`. Task 5.1 owns
the typed `UndoThrew` cleanup as well as the normal return path.

Task 5.2 adds Restart-aware suppression: Undo and Restore nested below a
Restart balance bookkeeping but never open an attempt. Restore outside a
valid Undo context, a depth imbalance, or a second top-level Undo faults.

### 6.4 Settling and emission

The settle budget begins when the native attempt opens. Every observed update
postfix follows the accepted ordering:

1. compute the next frame and monotonic elapsed time;
2. reject a pre-capture overrun, otherwise commit the next frame;
3. verify path and exact retained state reference;
4. when neutral and quiescent, construct a bounded capture and update the
   candidate;
5. emit on the second identical capture; otherwise
6. reject exhaustion after allowing success exactly on the boundary.

At least one physical neutral poll after the attempt is required. A later
cardinal physical poll clears neutral eligibility and the candidate. A
successful Step has `settle_frames` in `2..600`.

Task 5.1 owns every Step write, including Step 2, and every Step records
`state_replaced: false`. The sink write is durable before any progress report.
The driver then clears attempt state and `last_capture`, increments
`completedInputs`, transitions to Ready, and reports the new count exactly
once. At the 5.1 and 5.2 checkpoints this includes `Ready(3)` after Step 2;
Task 5.3 changes only that post-write continuation to terminal completion.

Any Step write or flush failure, including Step 0 or 1, selects marker-only
`trace_io_failed`, attempts Close once, and emits neither Error nor Ready. An
intermediate Ready reporter exception occurs after a durable Step and cleared
epoch; it claims `observer_exception` through the ordinary Error/Close/Failed
path and cannot undo the Step.

### 6.5 Supported-flow correction

Task 4.2 deliberately removed `SetNeutralSeenForDefensiveTest` and
`AssertCandidateClearedForDefensiveTest`. Neither method nor an equivalent
manufactured-state seam may return.

The stale Task 5.1 NotInspected subcase is rewritten through real callbacks:

1. open a real settling attempt;
2. observe a pre-neutral `NotInspected` update callback;
3. observe physical neutral;
4. prove the first fresh eligible capture does not settle; and
5. prove only the second fresh matching capture emits the Step.

The retained defensive `currentFrames` injection and passive observation of
the real directive-stage authorization callback remain the only approved
special-purpose seams.

## 7. Task 5.2: lifecycle balancing and replacement

### 7.1 Restart

An outermost Restart establishes restart depth before any fault. In every
active phase it immediately claims `unexpected_input` with null input fields.
The original game method still executes unchanged.

Recursive Restart, nested Undo, and nested Restore callbacks only balance
bookkeeping. They cannot open a Step or claim another fault. Accepted, refused,
and throwing Restart paths therefore have the same trace-level rejection.

### 7.2 State assignment

A state-set context distinguishes entered, successfully returned, and threw
paths. The observer never reads the requested state argument. On successful
return it rereads the actual current state and decides replacement from that
post-return value.

Before Initial is durable, a null post-state returns the driver to AwaitGame.
A same-reference post-state is not a replacement. A different non-null state
returned by the explicit state-set hook opens a fresh initial epoch at frame
zero and clears neutral, candidate, and last-capture state. This differs from
a same-update replacement first discovered by the existing verified-state
boundary: that supported Task 4.2 path rebases the new epoch to frame one.

After Initial is durable, successful replacement emits no Step and faults with
`state_replaced`. During a pending attempt, the attempt's input fields remain
authoritative for the Error. Exact object-reference identity is verified
before authorization can lead to gate or capture work.

### 7.3 Thrown and late-hook cleanup

Task 5.1 already balances typed ProcessInput and Undo contexts on return or
throw. Task 5.2 adds typed Restart and StateSet balancing and `ClearThrew`
kind-dispatch across the complete hook set. It cannot silently clear an
unrelated context. The original game exception remains authoritative.

A callback returning after Disabled, Faulted, Done, or disposal clears only
the matching bookkeeping it already owns. It cannot write a record, emit a
marker, invoke a reporter, or change the first terminal outcome.

## 8. Task 5.3: terminal completion

Task 5.3 stores the already validated `expectedInputCount` and threads the
boundary-validated UTC value through update completion into settled emission.

After the third durable Step, and only after its attempt state is cleared and
the completed count is incremented:

1. validate the final count and UTC relation;
2. atomically claim the shared terminal owner;
3. write End with the final observation UTC;
4. close the sink exactly once;
5. enter Done; and
6. call `Complete` on the reporter.

The required observable order is:

```text
Step 2 -> End -> Close -> Complete
```

No monitor is held across sink or reporter code.

### 8.1 Success-path failures

- A Step 2 write failure (still owned by 5.1), End failure, or terminal close
  failure yields authoritative marker-only `trace_io_failed`. It emits no
  Complete and does not append an Error to a potentially partial or already
  closing trace.
- A Complete reporter exception occurs after the closed success trace. It
  cannot rewrite trace bytes; it changes phase to Faulted and may make the one
  explicit post-success call to `Failed("observer_exception")` despite the
  already claimed success owner.
- Dispose is idempotent, attempts close at most once, and makes future
  observations inert.

## 9. Fault and Error policy

The same atomic owner arbitrates ordinary faults and successful completion.
An ordinary fault winner follows durable Error -> Close -> Failed marker. If
Error write/flush or Close fails, it instead attempts best-effort Close and
uses authoritative marker-only `trace_io_failed`; it never claims a durable
Error it cannot authenticate.

The winner otherwise owns the sole terminal record attempt, close path, and
terminal marker. Later failures may clear local bookkeeping and emit only
ordinary best-effort diagnostics. The sole exception is the post-close
Complete reporter failure in section 8.1: the trace stays immutable, phase
becomes Faulted, and `Failed("observer_exception")` may be attempted without a
record or another Close.

Error fields follow the authoritative precedence:

1. Top-level Restart is the sole override: null input fields and the active
   attempt/initial frame count, or zero with no active budget.
2. Otherwise, a pending attempt supplies its index, input, and committed frame
   count, including when another callback detects replacement or imbalance.
3. Otherwise, a recognized offending in-scope manual input uses the next index
   and mapped input with zero settle frames.
4. Otherwise, an unknown native input uses the next index and null input with
   zero settle frames.
5. Every other fault uses null input fields and only the active initial frame
   count, or zero.

`last_capture` is the most recent successfully constructed, size-bounded
complete capture in the current epoch. Before assigning it, the driver must
preflight the worst-case populated Error shape, not merely the all-null form.

An ordinary error trace ends with exactly one Error and no End. A sink failure
may leave absent, partial, or malformed bytes; only `trace_io_failed` then
claims terminal authority.

## 10. Tests and registrations

The frozen registration order is preserved.

Task 5.1 adds six `driver-input` registrations:

1. `all cardinals correlate`
2. `filtered and zero poll open no attempt`
3. `duplicate mismatch and unknown fault`
4. `unscoped policy follows phase`
5. `accepted and refused direction outcomes`
6. `Undo acceptance and restore rules`

Task 5.2 appends:

7. `restart depth and null fields`
8. `state replacement and ClearThrew`

Task 5.3 adds six `driver-terminal` registrations:

1. `three steps End Close Complete order`
2. `error field policy is exact`
3. `sink failure uses trace io marker`
4. `completion reporter cannot rewrite trace`
5. `first fault wins race`
6. `Dispose and late callbacks are final`

The final aggregator orders boundary, initial, input, then terminal tests.
`Program.cs` retains protocol, encoding, signature, sink, then driver aggregate
ordering.

## 11. Verification and review model

Each slice uses an authenticated offline TDD cycle:

1. authenticate its exact predecessor and expected file set;
2. apply only its tests/support/registration change;
3. for 5.1 and 5.2, require the regenerated exact missing-member compiler RED
   set and reject every additional compiler, fixture, restore, SDK,
   permission, timeout, or unrelated diagnostic; for 5.3, require successful
   compilation followed by the named behavioral RED showing that the 5.2
   driver returns to Ready after Step 2 and emits no End/Close/Complete;
4. apply only that slice's production change;
5. run the focused cohort, complete C# harness, corrected eight-test Task 4.2
   cohort, compile-only net35 project, and full Python suite; and
6. verify hashes, scope, whitespace, and clean repository state before commit.

All package and build commands remain offline and use the established local
toolchain and `--no-restore` gates.

### 11.1 Targeted mutations

Targeted mutation checks cover high-risk semantics without recreating Task
4.2's evidence system:

- exact direction correlation;
- neutral/candidate reset and exact reference identity;
- Step-before-Ready ordering;
- restart depth established before fault;
- replacement and late-callback cleanup;
- third-Step/End/Close/Complete ordering;
- shared terminal ownership;
- sink-failure and reporter-failure asymmetry; and
- correction-critical candidate clearing, capture provenance, and
  authorization-stage behavior inherited from Task 4.2.

Each mutant must make its intended test fail after one successful clean build,
then be completely reverted before a fresh GREEN run. Mutation artifacts use
a Task 5 namespace and never enter the Task 4.2 ledgers.

The descendant plan predeclares each mutation ID with its exact patch body and
hash, predecessor/target file hash, target function and semantic, selected
registration, unique first-failure fragment, forced mutated-tree build, exact
restoration hash, and required fresh focused GREEN. The compact report records
those bindings without introducing a transcript ledger or seal.

### 11.2 Independent review

After each implementation commit, separate subagents review one immutable
`BASE..HEAD` package for specification compliance and code quality and return
separate explicit verdicts. They do not share the implementer's role. Once a
committed artifact or implementation range has entered formal review, it is
never amended, rebased, squashed, or replaced. Critical/Important corrections
use append-only follow-up commits, fresh scoped packages, and fresh affected
reviews rather than being waived through a hash update. The three decimal-task
commits remain distinct.

After Task 5.3, a final cross-slice review and clean verification matrix produce
one compact tracked report containing commands, results, targeted mutation
identities, hashes, and reviewer verdicts. There is no raw transcript ledger,
controller replay ledger, or separate seal commit.

## 12. Descendant implementation-plan contract

The forthcoming standalone plan must:

- authenticate exact S4 ancestry and this approved design;
- pin all seal-bound documents, helpers, production files, Program, corrected
  tests, and the frozen future-test manifest;
- restate complete executable Task 5.1-5.3 steps without citing a legacy body
  as an instruction source;
- regenerate every literal patch against its exact predecessor without fuzz
  or offset acceptance;
- remove or behaviorally rewrite the obsolete private-seam call;
- recompute every RED diagnostic, checkpoint, document, helper, tree, and
  review-package hash affected by the corrected lineage;
- re-authenticate nominally unchanged production patches and complete-file
  creations rather than trusting their historical hashes;
- preserve the three ownership slices, registration order, and commit
  subjects; and
- keep all Task 4.2 tracked and ignored evidence immutable.

No implementation command is authorized until that plan is written, reviewed,
and explicitly approved.

## 13. Completion criteria

Task 5 is complete only when:

- all three separately owned commits exist in order;
- every focused and full offline gate passes under net10 and Core compiles for
  net35;
- corrected Task 4.2 supported-flow behavior remains green;
- every selected mutation is killed by its intended oracle and removed;
- independent per-slice and final reviewers approve exact commit ranges;
- the compact verification report matches the final tree; and
- the branch remains scoped to the approved design, plan, implementation,
  tests, and verification report, with no Task 6+ operational work.
