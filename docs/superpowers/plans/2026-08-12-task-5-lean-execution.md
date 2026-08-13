# Task 5 Lean Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Unity-free passive driver with manual input attribution,
lifecycle balancing, terminal trace completion, serialized output ownership, and
five focused mutation checks.

**Architecture:** Extend `PassiveDriver` through three sequential partial-class
slices. Task 5.1 generalizes the accepted Initial settling pipeline for cardinal
and Undo attempts; Task 5.2 adds Restart and state-set lifecycle bookkeeping;
Task 5.3 adds a logical output lease and shared terminal owner so Step, Error,
End, Close, and reporter handoffs serialize without holding a monitor across
external code. Each slice is test-first, receives pre-commit and immutable
post-commit reviews, and retains its approved commit subject.

**Tech Stack:** C# 7.3; .NET 10 unit executable; compile-only .NET Framework 3.5;
custom C# test registry; offline pytest; Git; local no-hardlink mutation copies.

**Spec:** `docs/superpowers/specs/2026-08-12-task-5-lean-execution-design.md`

**Behavioral spec:**
`docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md`

## Global Constraints

- Execute from `/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-oracle-passive-trace` on branch `codex/oracle-passive-task5-rebase`.
- The exact accepted lean-design commit is `b042eaa72c1def65f1c76f6bbcf01bf2dc3c1ed2`. Commit this plan as its one-file direct child with subject `docs: plan lean Task 5 execution`. Resolve that real plan commit dynamically; it is Task 5.1's exact parent and the base of every implementation-range review. Do not embed a prospective plan-commit hash.
- Preserve the untracked historical file `docs/superpowers/plans/2026-08-10-task-5-bootstrap-recovery.md`, captured launch outputs, candidate bundles, audit roots, review reports, and progress records. They are not edited, deleted, retried, sourced, executed, or extended.
- Do not create a new authority bundle, byte-pinned checker, controller, evidence namespace, prospective commit hash, or one-shot launch.
- Treat the generated patches in older Task 5 plans as naming and test-design context only. Write the implementation from the two controlling specifications and the current tree; do not extract or mechanically apply historical patches.
- Do not modify `PassiveDriverBoundaries.cs`, `HookKind`, `HookToken`, `UpdateDirective`, `GateSample`, protocol DTOs, sink/reporter interfaces, `TestSupport.cs`, either project file, or any Task 4.2 evidence.
- Do not launch the game, modify Unity or BepInEx integration, install the plugin, read or write saves, access the network, or begin Task 6.
- Core remains C# 7.3 and .NET 3.5 compatible: use existing `Interlocked`, `lock`, `List<T>`, explicit types, and existing exception patterns; do not introduce `Task`, tuples, records, nullable-reference syntax, `Volatile`, or newer BCL dependencies.
- Raw direction mapping is exactly `0/1/2/3 -> North/South/West/East`; raw `8` is physical neutral and is not an `OracleInput`.
- All commands are offline. Every `dotnet` invocation uses `--no-restore`; set `PIP_NO_INDEX=1` and `UV_OFFLINE=1`; do not restore, install, fetch, pull, or access the network.
- Preserve the frozen registration order and counts: Task 5.1 adds six `driver-input` tests, Task 5.2 raises that cohort to eight, and Task 5.3 adds six `driver-terminal` tests for a final total of 39 C# tests.
- Only `SetCurrentFramesForDefensiveTest` and the real update authorization probe remain approved special-purpose seams. Do not recreate neutral/candidate manufactured-state helpers.
- Test external callback ordering with deterministic `ManualResetEvent` barriers, never sleeps.
- A sink write/flush is durable before any state or reporter continuation; no driver monitor or output-lease lock may be held while calling sink or reporter code.
- Before each commit, obtain independent specification and quality reviews of the actual diff and verification evidence. After each commit, obtain fresh independent reviews of the immutable predecessor-to-commit range. Resolve findings as the lean design requires.
- A post-commit Critical or Important finding stops execution for user adjudication. Never amend, rebase, squash, or silently replace a reviewed commit.

## Common Offline Verification Commands

Set the environment once in each execution shell:

```bash
export DOTNET_CLI_UI_LANGUAGE=en
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true
export DOTNET_SDK_VULNERABILITY_CHECK_DISABLE=true
export DOTNET_NOLOGO=1
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
export NUGET_XMLDOC_MODE=skip
export PIP_NO_INDEX=1
export UV_OFFLINE=1
```

Use these exact commands throughout the plan:

```bash
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet

"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --configuration Release --no-restore --nologo -warnaserror \
  -t:Rebuild -m:1 -p:UseSharedCompilation=false

"$dotnet_bin" run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --configuration Release --no-restore --no-build -- \
  --cohort driver-boundary

"$dotnet_bin" run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --configuration Release --no-restore --no-build -- \
  --cohort driver-initial

"$dotnet_bin" run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --configuration Release --no-restore --no-build

"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  --configuration Release --no-restore --nologo -warnaserror \
  -t:Rebuild -m:1 -p:UseSharedCompilation=false

PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 PYTHONPATH="$PWD/src" \
  .venv/bin/python -m pytest -q -rX
```

After Task 5.1 exists, add the no-build `driver-input` run; after Task 5.3
exists, also add the no-build `driver-terminal` run:

```bash
"$dotnet_bin" run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --configuration Release --no-restore --no-build -- \
  --cohort driver-input

"$dotnet_bin" run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --configuration Release --no-restore --no-build -- \
  --cohort driver-terminal
```

Every successful C# run prints exactly `SSR oracle unit harness ready` and
leaves stderr empty. Builds must succeed with zero warnings and errors. Record
each command, exit status, and the C#/Python test totals for the final report.

After Task 5.3 reaches GREEN, use this exact 20-run stress script. Set
`results_file` to the Task 0 `results.tsv` path first.

```bash
stress_root="$(mktemp -d /private/tmp/ssr-task5-stress.XXXXXX)"
stress_head_before="$(git rev-parse HEAD)"
stress_index_before="$(git write-tree)"
stress_tracked_before="$(
  git diff --no-ext-diff --binary HEAD |
    shasum -a 256 | awk '{print $1}'
)"
stress_untracked_before="$(
  git ls-files --others --exclude-standard -z |
    xargs -0 shasum -a 256 |
    shasum -a 256 | awk '{print $1}'
)"
stress_status_before="$(git status --porcelain=v1 --untracked-files=all)"
iteration=1
while test "$iteration" -le 20; do
  ordinal="$(printf '%02d' "$iteration")"
  stdout_path="$stress_root/$ordinal.stdout"
  stderr_path="$stress_root/$ordinal.stderr"
  status=0
  "$dotnet_bin" run \
    --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    --configuration Release --no-restore --no-build -- \
    --cohort driver-terminal \
    >"$stdout_path" 2>"$stderr_path" || status=$?
  printf '%s\n' "$status" >"$stress_root/$ordinal.status"
  test "$status" = 0
  printf 'SSR oracle unit harness ready\n' | cmp -s - "$stdout_path"
  test ! -s "$stderr_path"
  printf 'stress-%s\tdotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-terminal\t%s\t6\tGREEN\n' \
    "$ordinal" "$status" >>"$results_file"
  iteration=$((iteration + 1))
done
test "$(find "$stress_root" -name '*.status' -type f | wc -l | tr -d '[:space:]')" = 20
test "$(git rev-parse HEAD)" = "$stress_head_before"
test "$(git write-tree)" = "$stress_index_before"
test "$(git diff --no-ext-diff --binary HEAD | shasum -a 256 | awk '{print $1}')" = \
  "$stress_tracked_before"
test "$(git ls-files --others --exclude-standard -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')" = \
  "$stress_untracked_before"
test "$(git status --porcelain=v1 --untracked-files=all)" = \
  "$stress_status_before"
```

---

### Task 0: Authenticate the Baseline and Run the Clean Matrix

**Files:**
- Read: `docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md`
- Read: `docs/superpowers/specs/2026-08-12-task-5-lean-execution-design.md`
- Read: `oracle/plugin/Core/PassiveDriver.cs`
- Read: `oracle/plugin/tests/PassiveDriverTestSupport.cs`
- Read: `oracle/plugin/tests/Program.cs`
- Preserve: `docs/superpowers/plans/2026-08-10-task-5-bootstrap-recovery.md`

**Interfaces:**
- Consumes: committed plan whose parent is lean-design commit `b042eaa72c1def65f1c76f6bbcf01bf2dc3c1ed2`.
- Produces: a verified baseline and recorded command/results block for later reviews.

- [ ] **Step 1: Authenticate the repository boundary**

```bash
test "$(git branch --show-current)" = codex/oracle-passive-task5-rebase
design_commit=b042eaa72c1def65f1c76f6bbcf01bf2dc3c1ed2
plan_path=docs/superpowers/plans/2026-08-12-task-5-lean-execution.md
plan_commit="$(git rev-parse HEAD)"
test "$(git rev-parse HEAD^)" = "$design_commit"
test "$(git log -1 --format=%s HEAD)" = 'docs: plan lean Task 5 execution'
test "$(git diff-tree --no-commit-id --name-only -r HEAD)" = "$plan_path"
git diff --quiet
git diff --cached --quiet
test "$(git status --short)" = \
  '?? docs/superpowers/plans/2026-08-10-task-5-bootstrap-recovery.md'
test ! -e "$(git rev-parse --git-path index.lock)"
```

Expected: every assertion succeeds; the historical recovery plan is the only
visible change.

- [ ] **Step 2: Confirm tool and project entry points**

```bash
test "$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet --version)" = 10.0.300
test -x .venv/bin/python
test -f oracle/plugin/tests/SsrOracle.UnitTests.csproj
test -f oracle/plugin/tests/SsrOracle.Core.Net35.csproj
```

Expected: all checks succeed without restore or network access.

- [ ] **Step 3: Run the clean baseline matrix**

Run the common net10 build, `driver-boundary`, `driver-initial`, full C# harness,
net35 build, and full Python suite exactly as listed above. Do not run
`driver-input` or `driver-terminal`; those cohorts are not registered yet.

Expected: C# total is 25, every command exits 0, and the repository state is
unchanged afterward.

- [ ] **Step 4: Record baseline results outside the tracked tree**

Create `results.tsv` under a root returned by
`mktemp -d /private/tmp/ssr-task5-lean-results.XXXXXX`. Its first row is exactly:

```text
phase	command	exit	test-total	note
```

Append one row per RED, GREEN, review, stress, and mutation result. The `command`
column contains the executable plus arguments, `exit` is the decimal status,
`test-total` is the verified manifest/Python count or `n/a`, and `note` is a
short first-failure or verdict. Do not create a controller, authority bundle,
hash manifest, or repository artifact. Preserve the note until the final report
is committed.

Append a metadata row whose `note` contains `plan-commit=` followed by the
resolved lowercase commit ID.
All later tasks resolve the same value with:

```bash
plan_commit="$(git log -1 --format=%H -- \
  docs/superpowers/plans/2026-08-12-task-5-lean-execution.md)"
```

### Task 1: Task 5.1 Tests — Manual Attempts and Settled Steps

**Files:**
- Create: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTestSupport.cs:5-88,254-475`
- Modify: `oracle/plugin/tests/Program.cs:10-26`
- Test: `oracle/plugin/tests/PassiveDriverInitialTests.cs`

**Interfaces:**
- Consumes: existing `DriverFixture`, `FakeTraceSink`, `FakePassiveReporter`,
  `PassiveUpdateBoundary`, `HookToken`, and the frozen registration manifest.
- Produces: six `driver-input` registrations; fixture helpers
  `OpenDirection(int,bool,bool,double)`, `OpenUndo(bool,bool,double)`, and
  `SettleCurrent(CaptureRecord,double)`; production expectations for the ten
  Task 5.1 members listed below.

- [ ] **Step 1: Extend the fake sink and fixture using real callbacks**

Add `Exception StepFailure`, make `WriteStep` record
`sink:step:<InputIndex>` before throwing `StepFailure`, and add these fixture
helpers:

```csharp
internal void OpenDirection(
    int rawDirection,
    bool accepted,
    bool movementScheduled,
    double nowSeconds)
{
    HookToken poll = Driver.PlayerPollEntered();
    Driver.PhysicalPollReturned(rawDirection);
    HookToken input = Driver.ProcessInputEntered(
        State, rawDirection, nowSeconds);
    Driver.ProcessInputReturned(
        input, accepted, movementScheduled);
    Driver.PlayerPollReturned(poll);
}

internal void OpenUndo(
    bool restored,
    bool movementScheduled,
    double nowSeconds)
{
    HookToken undo = Driver.UndoEntered(State, nowSeconds);
    if (restored)
        Driver.RestoreObserved();
    Driver.UndoReturned(undo, movementScheduled);
}

internal void SettleCurrent(
    CaptureRecord capture,
    double firstUpdateSeconds)
{
    Neutral();
    Observe(State, State, firstUpdateSeconds, true, capture);
    Observe(State, State, firstUpdateSeconds + 1.0, true, capture);
}

internal static DriverFixture Ready(int maxFrames, double maxSeconds)
{
    DriverFixture fixture = Active(maxFrames, maxSeconds);
    fixture.Observe(
        fixture.State, fixture.State, 1.0, true,
        ProtocolSamples.Capture("ready-a"));
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 2.0, true,
        ProtocolSamples.Capture("ready-pair"));
    fixture.Observe(
        fixture.State, fixture.State, 3.0, true,
        ProtocolSamples.Capture("ready-pair"));
    Check.Equal(PassivePhase.Ready, fixture.Driver.Phase, "ready fixture");
    return fixture;
}
```

Do not add any setter for neutral state, candidate signature, or last capture.

- [ ] **Step 2: Create the six frozen registrations**

Create `PassiveDriverInputTests.cs` with this wrapper, placing every Task 1 and
Task 3 test/helper body below inside it:

```csharp
using System;
using System.Collections.Generic;

internal static class PassiveDriverInputTests
{
    // Task 1 and Task 3 test members.
}
```

Register tests in this exact order:

```csharp
internal static void Register(TestRegistry tests)
{
    tests.Add("driver-input", "all cardinals correlate",
        AllCardinalsCorrelate);
    tests.Add("driver-input", "filtered and zero poll open no attempt",
        FilteredAndZeroPollOpenNoAttempt);
    tests.Add("driver-input", "duplicate mismatch and unknown fault",
        DuplicateMismatchAndUnknownFault);
    tests.Add("driver-input", "unscoped policy follows phase",
        UnscopedPolicyFollowsPhase);
    tests.Add("driver-input", "accepted and refused direction outcomes",
        AcceptedAndRefusedDirectionOutcomes);
    tests.Add("driver-input", "Undo acceptance and restore rules",
        UndoAcceptanceAndRestoreRules);
}
```

Inside those six registered methods, use focused helpers/subcases to cover:

- exact `0/1/2/3` mapping, one physical poll, identical argument, and only the
  first nested manual call;
- zero/filtered polls, duplicate polls, mismatches, unknown raw values, and
  before-Initial/overlapping precedence;
- phase-dependent unscoped `ProcessInput` policy;
- accepted/refused cardinal outcomes and movement sampling;
- exact retained state identity and real-callback neutral/candidate clearing;
- distinct, equal-valued captures; NotInspected before neutral; exact frame/time
  boundary behavior; and populated Error preflight;
- durable Step fields/order, marker-only Step failure, cleared epoch before a
  Ready reporter fault, and Ready values `0,1,2,3`; and
- Undo accepted only after Restore, refused Undo, nested/duplicate Restore,
  before-Initial Undo, and typed returned/threw cleanup.

Use these descriptive private subcase names so review can map behavior to the
spec: `CardinalCorrelationOrderAndFields`, `NestedInputOrderFaults`,
`ScopedInputBeforeInitialFaults`, `OverlappingInputRetainsAttempt`,
`StateIdentityFollowsPhase`, `ValueEqualCapturesSettle`,
`SettlingCandidateBreaksRestartPair`, `SettlingNotInspectedRestartsPair`,
`SettlingNonquiescentRestartsPair`,
`SettlingDeadlineOrderIsExact`, `StepFailureIsTerminal`,
`ReadyFailureFollowsClearedStep`,
`PopulatedErrorPreflightRejectsBoundaryCapture`,
`StepPrecedesIntermediateReady`, `EverySettledStepReportsReady`,
`UndoBeforeInitialFaults`, and `ThrownInputHooksBalance`.

Implement the registered bodies as explicit subcase aggregators:

```csharp
private static void AllCardinalsCorrelate()
{
    int[] raw = new int[] { 0, 1, 2, 3 };
    OracleInput[] mapped = new OracleInput[]
    {
        OracleInput.North, OracleInput.South,
        OracleInput.West, OracleInput.East
    };
    for (int index = 0; index < raw.Length; index++)
    {
        DriverFixture fixture = DriverFixture.Ready();
        HookToken poll = fixture.Driver.PlayerPollEntered();
        fixture.Driver.PhysicalPollReturned(raw[index]);
        HookToken input = fixture.Driver.ProcessInputEntered(
            fixture.State, raw[index], 10.0);
        Check.Equal(
            PassivePhase.Settling, fixture.Driver.Phase,
            "cardinal opens attempt " + index.ToString());
        Check.Equal(
            mapped[index], fixture.Driver.PendingInput,
            "exact cardinal mapping " + index.ToString());
        fixture.Driver.ProcessInputThrew(input);
        fixture.Driver.PlayerPollReturned(poll);
    }
    CardinalCorrelationOrderAndFields();
}

private static void FilteredAndZeroPollOpenNoAttempt()
{
    DriverFixture empty = DriverFixture.Ready();
    HookToken emptyPoll = empty.Driver.PlayerPollEntered();
    empty.Driver.PlayerPollReturned(emptyPoll);
    Check.Equal(PassivePhase.Ready, empty.Driver.Phase, "empty poll Ready");
    Check.Equal(0, empty.Sink.StepRecords.Count, "empty poll no Step");
    Check.Equal(0, empty.Sink.ErrorRecords.Count, "empty poll no Error");

    DriverFixture filtered = DriverFixture.Ready();
    filtered.CardinalOnly(2);
    Check.Equal(
        PassivePhase.Ready, filtered.Driver.Phase,
        "filtered cardinal Ready");
    Check.Equal(0, filtered.Sink.StepRecords.Count, "filtered no Step");
    Check.Equal(0, filtered.Sink.ErrorRecords.Count, "filtered no Error");
}

private static void DuplicateMismatchAndUnknownFault()
{
    DuplicatePhysicalPollFaults();
    MismatchedDirectionFaults();
    NestedInputOrderFaults();
    UnknownNativeDirectionUsesNullInput();
    ScopedInputBeforeInitialFaults();
    OverlappingInputRetainsAttempt();
}

private static void UnscopedPolicyFollowsPhase()
{
    AssertUnscopedIgnored(DriverFixture.Active(), PassivePhase.AwaitGame);
    DriverFixture initial = DriverFixture.Active();
    initial.Observe(
        initial.State, initial.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    AssertUnscopedIgnored(initial, PassivePhase.AwaitInitialNeutral);
    AssertUnscopedFaultsInReady();
    DriverFixture settling = DriverFixture.Ready();
    settling.OpenDirection(2, true, true, 10.0);
    AssertUnscopedIgnored(settling, PassivePhase.Settling);
}

private static void AcceptedAndRefusedDirectionOutcomes()
{
    AssertDirectionOutcome(2, OracleInput.West, true, true);
    AssertDirectionOutcome(0, OracleInput.North, false, false);
    StateIdentityFollowsPhase();
    ValueEqualCapturesSettle();
    SettlingCandidateBreaksRestartPair();
    SettlingNotInspectedRestartsPair();
    SettlingNonquiescentRestartsPair();
    SettlingDeadlineOrderIsExact();
    StepFailureIsTerminal();
    ReadyFailureFollowsClearedStep();
    PopulatedErrorPreflightRejectsBoundaryCapture();
    StepPrecedesIntermediateReady();
    EverySettledStepReportsReady();
}

private static void UndoAcceptanceAndRestoreRules()
{
    AssertUndoOutcome(true, true, true);
    AssertUndoOutcome(false, false, false);
    NestedAndDuplicateRestoreFaults();
    UndoBeforeInitialFaults();
    ThrownInputHooksBalance();
}

private static void AssertUnscopedIgnored(
    DriverFixture fixture, PassivePhase expectedPhase)
{
    fixture.Driver.ProcessInputEntered(fixture.State, 0, 20.0);
    Check.Equal(expectedPhase, fixture.Driver.Phase, "unscoped phase");
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, "unscoped no Error");
}

private static void AssertUnscopedFaultsInReady()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.Driver.ProcessInputEntered(fixture.State, 0, 20.0);
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "Ready one Error");
    ErrorRecord error = fixture.Sink.ErrorRecords[0];
    Check.Equal("unscoped_process_input", error.Code, "Ready code");
    Check.Equal((int?)null, error.InputIndex, "Ready null index");
    Check.Equal((OracleInput?)null, error.Input, "Ready null input");
    Check.Equal(0, error.SettleFrames, "Ready zero frames");
}

private static void AssertDirectionOutcome(
    int raw, OracleInput input, bool accepted, bool movement)
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(raw, accepted, movement, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    Check.Equal(1, fixture.Sink.StepRecords.Count, "one Step");
    StepRecord step = fixture.Sink.StepRecords[0];
    Check.Equal(0, step.InputIndex, "Step index");
    Check.Equal(input, step.Input, "Step input");
    Check.Equal(accepted, step.Accepted, "Step accepted");
    Check.Equal(movement, step.MovementScheduled, "Step movement");
    Check.Equal(2, step.SettleFrames, "Step frames");
    Check.False(step.StateReplaced, "Step state not replaced");
    Check.Sequence(
        new int[] { 0, 1 }, fixture.Reporter.ReadyValues.ToArray(),
        "Ready values after Step");
    Check.True(
        fixture.Events.IndexOf("sink:step:0")
            < fixture.Events.IndexOf("report:ready:1/3"),
        "Step precedes Ready");
}
```

Each named leaf uses a fresh fixture unless it explicitly tests an overlap.
After the action, assert the exact phase, record count and fields, reporter
values, and event suffix from the vector table below; never assert only that an
exception or generic fault occurred.

Use these exact high-level test vectors and primary assertions; subcases may add
more assertions but may not weaken these:

| Registered test | Action | Required oracle |
|---|---|---|
| all cardinals correlate | For four fresh Ready fixtures, poll and return raw `0,1,2,3`, then enter the same ProcessInput | Phase is Settling and `PendingInput` is North, South, West, East respectively |
| filtered and zero poll open no attempt | Return an empty poll; separately return a cardinal poll with no ProcessInput | Phase stays Ready; zero Step and Error records |
| duplicate mismatch and unknown fault | Duplicate physical poll; mismatched ProcessInput; raw `99`; another input during Settling | Exact `hook_order_mismatch`/`unexpected_input` codes; next/offending fields when no attempt; pending index/input/frames win during an attempt |
| unscoped policy follows phase | Call ProcessInput without a poll in AwaitGame, AwaitInitialNeutral, Ready, and Settling | Ignore in AwaitGame/AwaitInitialNeutral/Settling; Ready emits `unscoped_process_input` with null fields and zero frames |
| accepted and refused direction outcomes | Settle West accepted/moving and North refused/not-moving attempts | Step index 0; exact input/outcome; two settle frames; `state_replaced=false`; Step event precedes Ready(1) |
| Undo acceptance and restore rules | Undo with Restore; Undo without Restore; Restore outside Undo | Accepted only with Restore; input Undo; outside Restore faults `hook_order_mismatch`; typed throw cleanup is idempotent |

The settling subcases additionally require a physical neutral before gate
inspection, two fresh equal complete captures, exact boundary success, a broken
candidate after NotInspected/nonquiescent/cardinal activity, marker-only Step
I/O failure, and Ready values `0,1,2,3` across three durable Steps.

Define the remaining called Task 5.1 leaves. `AssertInputError` is the common
exact-field oracle, so none of these helpers merely checks “some fault”:

```csharp
private static ErrorRecord AssertInputError(
    DriverFixture fixture,
    string code,
    int? index,
    OracleInput? input,
    int frames,
    string label)
{
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, label + " Error count");
    ErrorRecord error = fixture.Sink.ErrorRecords[0];
    Check.Equal(code, error.Code, label + " code");
    Check.Equal(index, error.InputIndex, label + " index");
    Check.Equal(input, error.Input, label + " input");
    Check.Equal(frames, error.SettleFrames, label + " frames");
    Check.Equal(0, fixture.Sink.StepRecords.Count, label + " no Step");
    return error;
}

private static void CardinalCorrelationOrderAndFields()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(3);
    HookToken input = fixture.Driver.ProcessInputEntered(
        fixture.State, 3, 10.0);
    fixture.Driver.ProcessInputReturned(input, true, false);
    fixture.Driver.PlayerPollReturned(poll);
    Check.Equal(OracleInput.East, fixture.Driver.PendingInput, "East input");
    Check.True(fixture.Driver.PendingAccepted, "accepted retained");
    Check.False(
        fixture.Driver.PendingMovementScheduled,
        "movement retained");
}

private static void DuplicatePhysicalPollFaults()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(0);
    fixture.Driver.PhysicalPollReturned(0);
    AssertInputError(
        fixture, "hook_order_mismatch", null, null, 0,
        "duplicate poll");
    fixture.Driver.PlayerPollReturned(poll);
}

private static void MismatchedDirectionFaults()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(0);
    fixture.Driver.ProcessInputEntered(fixture.State, 1, 10.0);
    AssertInputError(
        fixture, "hook_order_mismatch", null, null, 0,
        "mismatched direction");
    fixture.Driver.PlayerPollReturned(poll);
}

private static void NestedInputOrderFaults()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(2);
    fixture.Driver.ProcessInputEntered(fixture.State, 2, 10.0);
    fixture.Driver.ProcessInputEntered(fixture.State, 2, 10.0);
    AssertInputError(
        fixture, "hook_order_mismatch", 0, OracleInput.West, 0,
        "second manual call retains pending fields");
    fixture.Driver.PlayerPollReturned(poll);
}

private static void UnknownNativeDirectionUsesNullInput()
{
    DriverFixture fixture = DriverFixture.Active();
    fixture.Observe(
        fixture.State, fixture.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(99);
    AssertInputError(
        fixture, "unexpected_input", 0, null, 0,
        "unknown offender overrides active Initial frames");
    fixture.Driver.PlayerPollReturned(poll);

    DriverFixture pending = DriverFixture.Ready();
    pending.OpenDirection(2, true, true, 10.0);
    pending.Observe(
        pending.State, pending.State, 11.0, false,
        ProtocolSamples.MovedCapture);
    HookToken pendingPoll = pending.Driver.PlayerPollEntered();
    pending.Driver.PhysicalPollReturned(99);
    AssertInputError(
        pending, "unexpected_input", 0, OracleInput.West, 1,
        "pending attempt wins unknown offender fields");
    pending.Driver.PlayerPollReturned(pendingPoll);
}

private static void ScopedInputBeforeInitialFaults()
{
    DriverFixture fixture = DriverFixture.Active();
    fixture.Observe(
        fixture.State, fixture.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(0);
    fixture.Driver.ProcessInputEntered(fixture.State, 0, 2.0);
    AssertInputError(
        fixture, "input_before_initial", 0, OracleInput.North, 0,
        "mapped offender overrides active Initial frames");
    fixture.Driver.PlayerPollReturned(poll);
}

private static void OverlappingInputRetainsAttempt()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Observe(
        fixture.State, fixture.State, 11.0, false,
        ProtocolSamples.MovedCapture);
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(0);
    fixture.Driver.ProcessInputEntered(fixture.State, 0, 12.0);
    AssertInputError(
        fixture, "overlapping_input", 0, OracleInput.West, 1,
        "overlap pending precedence");
    fixture.Driver.PlayerPollReturned(poll);
}

private static void AssertUndoOutcome(
    bool restore, bool accepted, bool movement)
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenUndo(restore, movement, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    Check.Equal(1, fixture.Sink.StepRecords.Count, "Undo one Step");
    StepRecord step = fixture.Sink.StepRecords[0];
    Check.Equal(OracleInput.Undo, step.Input, "Undo input");
    Check.Equal(accepted, step.Accepted, "Undo accepted");
    Check.Equal(movement, step.MovementScheduled, "Undo movement");
}

private static void NestedAndDuplicateRestoreFaults()
{
    DriverFixture outside = DriverFixture.Ready();
    outside.Driver.RestoreObserved();
    ErrorRecord outsideError = AssertInputError(
        outside, "hook_order_mismatch", null, null, 0,
        "Restore outside Undo");
    Check.True(outsideError.LastCapture == null, "outside Restore no capture");
    Check.Equal(1, outside.Sink.CloseCalls, "outside Restore one Close");
    Check.Sequence(
        new string[] { "hook_order_mismatch" },
        outside.Reporter.FailedCodes.ToArray(),
        "outside Restore one Failed marker");

    DriverFixture duplicate = DriverFixture.Ready();
    HookToken undo = duplicate.Driver.UndoEntered(duplicate.State, 10.0);
    duplicate.Driver.RestoreObserved();
    duplicate.Driver.RestoreObserved();
    AssertInputError(
        duplicate, "hook_order_mismatch", 0, OracleInput.Undo, 0,
        "duplicate Restore");
    duplicate.Driver.UndoThrew(undo);

    DriverFixture nested = DriverFixture.Ready();
    HookToken outer = nested.Driver.UndoEntered(nested.State, 10.0);
    nested.Driver.UndoEntered(nested.State, 10.0);
    AssertInputError(
        nested, "hook_order_mismatch", 0, OracleInput.Undo, 0,
        "nested Undo");
    nested.Driver.UndoThrew(outer);
}

private static void UndoBeforeInitialFaults()
{
    DriverFixture fixture = DriverFixture.Active();
    HookToken token = fixture.Driver.UndoEntered(fixture.State, 1.0);
    AssertInputError(
        fixture, "input_before_initial", 0, OracleInput.Undo, 0,
        "Undo before Initial");
    fixture.Driver.UndoThrew(token);
}

private static void ThrownInputHooksBalance()
{
    DriverFixture process = DriverFixture.Ready();
    HookToken poll = process.Driver.PlayerPollEntered();
    process.Driver.PhysicalPollReturned(0);
    HookToken input = process.Driver.ProcessInputEntered(
        process.State, 0, 10.0);
    process.Driver.ProcessInputThrew(input);
    process.Driver.ProcessInputThrew(input);
    process.Driver.PlayerPollThrew(poll);

    DriverFixture undo = DriverFixture.Ready();
    HookToken undoToken = undo.Driver.UndoEntered(undo.State, 10.0);
    undo.Driver.UndoThrew(undoToken);
    undo.Driver.UndoThrew(undoToken);
    Check.Equal(0, undo.Sink.ErrorRecords.Count, "throw cleanup no Error");
}

private static void StateIdentityFollowsPhase()
{
    DriverFixture attempt = DriverFixture.Ready();
    HookToken poll = attempt.Driver.PlayerPollEntered();
    attempt.Driver.PhysicalPollReturned(0);
    attempt.Driver.ProcessInputEntered(attempt.OtherState, 0, 10.0);
    AssertInputError(
        attempt, "state_replaced", 0, OracleInput.North, 0,
        "attempt exact state identity");
    attempt.Driver.PlayerPollReturned(poll);

    DriverFixture readyUpdate = DriverFixture.Ready();
    FakeUpdateObservation readyMismatch = readyUpdate.Observe(
        readyUpdate.OtherState, readyUpdate.OtherState, 10.0, true,
        ProtocolSamples.MovedCapture);
    AssertInputError(
        readyUpdate, "state_replaced", null, null, 0,
        "Ready update exact state identity");
    Check.Equal(0, readyMismatch.CaptureCalls, "Ready mismatch no capture");

    DriverFixture settlingUpdate = DriverFixture.Ready();
    settlingUpdate.OpenDirection(2, true, true, 10.0);
    FakeUpdateObservation settlingMismatch = settlingUpdate.Observe(
        settlingUpdate.OtherState, settlingUpdate.OtherState, 11.0, true,
        ProtocolSamples.MovedCapture);
    AssertInputError(
        settlingUpdate, "state_replaced", 0, OracleInput.West, 1,
        "Settling update exact state identity");
    Check.Equal(
        0, settlingMismatch.CaptureCalls,
        "Settling mismatch faults before capture");
}

private static void ValueEqualCapturesSettle()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.Capture("same"));
    fixture.Observe(
        fixture.State, fixture.State, 12.0, true,
        ProtocolSamples.Capture("same"));
    Check.Equal(1, fixture.Sink.StepRecords.Count, "value-equal pair Step");
}

private static void SettlingCandidateBreaksRestartPair()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.Capture("pair"));
    fixture.CardinalOnly(0);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 12.0, true,
        ProtocolSamples.Capture("pair"));
    Check.Equal(0, fixture.Sink.StepRecords.Count, "broken pair no Step");
    fixture.Observe(
        fixture.State, fixture.State, 13.0, true,
        ProtocolSamples.Capture("pair"));
    Check.Equal(1, fixture.Sink.StepRecords.Count, "fresh pair settles");
}

private static void SettlingNotInspectedRestartsPair()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.Capture("pre-neutral-skipped"));
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 12.0, true,
        ProtocolSamples.Capture("fresh-pair"));
    Check.Equal(
        0, fixture.Sink.StepRecords.Count,
        "first eligible capture after NotInspected does not settle");
    fixture.Observe(
        fixture.State, fixture.State, 13.0, true,
        ProtocolSamples.Capture("fresh-pair"));
    Check.Equal(
        1, fixture.Sink.StepRecords.Count,
        "second fresh matching capture settles");
}

private static void SettlingNonquiescentRestartsPair()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.Capture("stale-pair"));
    fixture.Observe(
        fixture.State, fixture.State, 12.0, false,
        ProtocolSamples.Capture("stale-pair"));
    fixture.Observe(
        fixture.State, fixture.State, 13.0, true,
        ProtocolSamples.Capture("fresh-after-nonquiescent"));
    Check.Equal(
        0, fixture.Sink.StepRecords.Count,
        "first fresh capture after nonquiescent does not settle");
    fixture.Observe(
        fixture.State, fixture.State, 14.0, true,
        ProtocolSamples.Capture("fresh-after-nonquiescent"));
    Check.Equal(
        1, fixture.Sink.StepRecords.Count,
        "second fresh capture after nonquiescent settles");
}

private static void SettlingDeadlineOrderIsExact()
{
    DriverFixture exact = DriverFixture.Ready(3, 3.0);
    exact.OpenDirection(2, true, true, 10.0);
    exact.Neutral();
    exact.Observe(
        exact.State, exact.State, 11.0, false,
        ProtocolSamples.MovedCapture);
    exact.Observe(
        exact.State, exact.State, 12.0, true,
        ProtocolSamples.MovedCapture);
    exact.Observe(
        exact.State, exact.State, 13.0, true,
        ProtocolSamples.MovedCapture);
    Check.Equal(
        1, exact.Sink.StepRecords.Count,
        "exact frame/time boundary Step wins");

    DriverFixture over = DriverFixture.Ready(3, 3.0);
    over.OpenDirection(2, true, true, 10.0);
    over.Neutral();
    over.Observe(
        over.State, over.State, 14.0, true,
        ProtocolSamples.MovedCapture);
    AssertInputError(
        over, "settle_timeout", 0, OracleInput.West, 1,
        "post-boundary timeout before capture");
}

private static void StepFailureIsTerminal()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.Sink.StepFailure = new TraceIoException("Step failed");
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, "Step failure no Error");
    Check.Sequence(
        new string[] { "trace_io_failed" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Step failure marker");
    Check.Sequence(
        new int[] { 0 }, fixture.Reporter.ReadyValues.ToArray(),
        "Step failure no Ready(1)");
    Check.Equal(1, fixture.Sink.CloseCalls, "Step failure one Close");
}

private static void ReadyFailureFollowsClearedStep()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.Reporter.ReadyFailure =
        new InvalidOperationException("Ready(1) failed");
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    Check.Equal(1, fixture.Sink.StepRecords.Count, "Ready failure Step durable");
    Check.Sequence(
        new int[] { 0, 1 }, fixture.Reporter.ReadyValues.ToArray(),
        "Ready(1) is attempted once");
    Check.Equal(
        1, fixture.Sink.ErrorRecords.Count,
        "Ready failure one ordinary Error");
    ErrorRecord error = fixture.Sink.ErrorRecords[0];
    Check.Equal("observer_exception", error.Code, "Ready failure code");
    Check.Equal((int?)null, error.InputIndex, "Ready failure null index");
    Check.Equal((OracleInput?)null, error.Input, "Ready failure null input");
    Check.Equal(0, error.SettleFrames, "Ready failure zero frames");
    Check.True(error.LastCapture == null, "Ready failure null capture");
    Check.Equal(1, fixture.Sink.CloseCalls, "Ready failure one Close");
    Check.Sequence(
        new string[] { "observer_exception" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Ready failure one Failed marker");
    Check.Sequence(
        new string[]
        {
            "sink:step:0", "report:ready:1/3",
            "report:diagnostic:System.InvalidOperationException",
            "sink:error:observer_exception", "sink:close",
            "report:failed:observer_exception"
        },
        fixture.Events.GetRange(fixture.Events.Count - 6, 6).ToArray(),
        "cleared Step precedes Ready fault terminal suffix");
}

private static void PopulatedErrorPreflightRejectsBoundaryCapture()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    CaptureRecord oversized =
        ProtocolSamples.Capture(new string('x', 16776795));
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true, oversized);
    AssertInputError(
        fixture, "record_too_large", 0, OracleInput.West, 1,
        "populated Error preflight");
}

private static void StepPrecedesIntermediateReady()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    Check.True(
        fixture.Events.IndexOf("sink:step:0")
            < fixture.Events.IndexOf("report:ready:1/3"),
        "Step precedes Ready");
}

private static void EverySettledStepReportsReady()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    fixture.OpenDirection(0, false, false, 20.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 21.0);
    fixture.OpenUndo(true, false, 30.0);
    fixture.SettleCurrent(ProtocolSamples.InitialCapture, 31.0);
    Check.Sequence(
        new int[] { 0, 1, 2, 3 },
        fixture.Reporter.ReadyValues.ToArray(),
        "every checkpoint Step reports Ready");
}
```

- [ ] **Step 3: Register the six-test cohort**

After `PassiveDriverInitialTests.Register(tests)`, add:

```csharp
PassiveDriverInputTests.Register(tests);
```

Append the exact manifest entry:

```csharp
{ "driver-input", 6 }
```

- [ ] **Step 4: Build to verify the expected compile RED**

Run the forced net10 build.

Expected: nonzero exit and missing-member diagnostics only for:

```text
PendingInput
PendingAccepted
PendingMovementScheduled
ProcessInputEntered
ProcessInputReturned
ProcessInputThrew
UndoEntered
RestoreObserved
UndoReturned
UndoThrew
```

Reject fixture, syntax, manifest, restore, SDK, permission, or unrelated
diagnostics. Preserve the concise RED output in the external results note.

### Task 2: Task 5.1 Production — Attribute Attempts and Emit Steps

**Files:**
- Modify: `oracle/plugin/Core/PassiveDriver.cs:4-865`
- Create: `oracle/plugin/Core/PassiveDriverInput.cs`
- Test: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Test: `oracle/plugin/tests/PassiveDriverInitialTests.cs`

**Interfaces:**
- Consumes: the Task 1 test surface and existing token/update/capture APIs.
- Produces:

```csharp
internal OracleInput PendingInput { get; }
internal bool PendingAccepted { get; }
internal bool PendingMovementScheduled { get; }

internal HookToken ProcessInputEntered(
    object stateReference, int rawDirection, double nowSeconds);
internal void ProcessInputReturned(
    HookToken token, bool accepted, bool movementScheduled);
internal void ProcessInputThrew(HookToken token);

internal HookToken UndoEntered(
    object stateReference, double nowSeconds);
internal void RestoreObserved();
internal void UndoReturned(
    HookToken token, bool movementScheduled);
internal void UndoThrew(HookToken token);
```

- [ ] **Step 1: Make the driver partial and add attempt state**

Change the declaration to `internal sealed partial class PassiveDriver`.
Extend `PlayerPollContext` and add attempt state with these exact declarations:

```csharp
private sealed class PlayerPollContext
{
    internal long Id;
    internal bool SawPhysicalPoll;
    internal int RawDirection;
    internal bool SawManualProcessInput;
}

private int completedInputs;
private object stableState;
private bool attemptPending;
private bool attemptOutcomeKnown;
private OracleInput attemptInput;
private bool attemptAccepted;
private bool attemptMovementScheduled;
private object attemptState;
```

Replace the current minimal `FaultRequest` with this
complete Task 5.1 shape:

```csharp
private struct FaultRequest
{
    internal int? FrameOverride;
    internal bool HasOffendingInput;
    internal int OffendingIndex;
    internal OracleInput? OffendingInput;

    internal static FaultRequest Derived()
    {
        return new FaultRequest();
    }

    internal static FaultRequest DerivedWithFrames(int frames)
    {
        FaultRequest value = new FaultRequest();
        value.FrameOverride = frames;
        return value;
    }

internal static FaultRequest Offending(
        int index, OracleInput? input)
    {
        FaultRequest value = new FaultRequest();
        value.HasOffendingInput = true;
        value.OffendingIndex = index;
        value.OffendingInput = input;
        return value;
    }
}
```

Add the three guarded pending properties below. The getters expose test-only
pending state only while an attempt is open:

```csharp
internal OracleInput PendingInput
{
    get
    {
        if (!attemptPending)
            throw new InvalidOperationException("no pending attempt");
        return attemptInput;
    }
}

internal bool PendingAccepted
{
    get
    {
        if (!attemptPending || !attemptOutcomeKnown)
            throw new InvalidOperationException("attempt outcome is pending");
        return attemptAccepted;
    }
}

internal bool PendingMovementScheduled
{
    get
    {
        if (!attemptPending || !attemptOutcomeKnown)
            throw new InvalidOperationException("attempt outcome is pending");
        return attemptMovementScheduled;
    }
}
```

- [ ] **Step 2: Generalize Initial observation to Ready and Settling**

Rename `IsInitialObservationActive` to `IsObservationActive` and allow exactly
AwaitGame, AwaitInitialNeutral, Ready, and Settling. Update Begin/Authorize/
Complete and poll callbacks to use it. Generalize the frame/time budget so
Initial selects `initial_settle_timeout` and Settling selects `settle_timeout`.

On authorization in Ready/Settling, require exact reference identity against
`stableState` or `attemptState` before gate/capture work. Keep the accepted
same-update Initial replacement behavior at frame one.

In `EmitInitial`, after the durable Initial write and before clearing
`epochState`, assign `stableState = epochState`; only then set Ready, clear the
Initial epoch, and invoke Ready(0). This seeds the exact identity used by the
first manual attempt.

The generalized observation branches are closed:

```csharp
private bool IsObservationActive()
{
    return Read(ref prepared) != 0 && Read(ref disabled) == 0
        && Read(ref disposed) == 0 && !TerminalSelected()
        && (phase == PassivePhase.AwaitGame
            || phase == PassivePhase.AwaitInitialNeutral
            || phase == PassivePhase.Ready
            || phase == PassivePhase.Settling);
}

string timeoutCode = phase == PassivePhase.Settling
    ? "settle_timeout" : "initial_settle_timeout";
object expectedState = phase == PassivePhase.Settling
    ? attemptState : stableState;
if ((phase == PassivePhase.Ready || phase == PassivePhase.Settling)
    && (!usableGame || stateReference == null
        || !Object.ReferenceEquals(expectedState, stateReference)))
{
    ConsumeAuthorizedDirective(directive);
    TryFaultInternal("state_replaced", FaultRequest.Derived());
    return false;
}
```

In `CompleteUpdateCore`, AwaitGame and Ready accept only NotInspected.
AwaitInitialNeutral and Settling execute the existing candidate switch
unchanged; the second matching capture calls `EmitInitial` for Initial or
`EmitSettledAttempt` for Settling. After the switch, `TimeoutAfterSample` faults
with `timeoutCode`. This preserves match-before-timeout at the exact boundary.

- [ ] **Step 3: Implement correlation and attempt lifecycle**

Create `PassiveDriverInput.cs` with this wrapper, placing all Task 5.1 input
members below inside it:

```csharp
using System;

internal sealed partial class PassiveDriver
{
    // Task 5.1 members from Steps 3–4.
}
```

Implement exactly the
public surface above around typed `ProcessInputContext` and `UndoContext`.
Use:

```csharp
private sealed class ProcessInputContext
{
    internal long Id;
}

private sealed class UndoContext
{
    internal long Id;
    internal bool RestoreSeen;
}

private ProcessInputContext processInputContext;
private UndoContext undoContext;

private bool HandleManualAttempt(
    OracleInput input,
    object stateReference,
    double nowSeconds);

private static bool TryMapCardinal(
    int rawDirection,
    out OracleInput input);
```

Implement the mapping with this closed switch:

```csharp
switch (rawDirection)
{
    case 0: input = OracleInput.North; return true;
    case 1: input = OracleInput.South; return true;
    case 2: input = OracleInput.West; return true;
    case 3: input = OracleInput.East; return true;
    default: input = OracleInput.North; return false;
}
```

Use this decision body in `HandleManualAttempt`; `FaultRequest.Offending`
retains the supplied next index/input exactly as defined in Step 1:

```csharp
if (phase == PassivePhase.AwaitGame
    || phase == PassivePhase.AwaitInitialNeutral)
{
    TryFaultInternal(
        "input_before_initial",
        FaultRequest.Offending(completedInputs, input));
    return false;
}
if (attemptPending || phase == PassivePhase.Settling)
{
    TryFaultInternal("overlapping_input", FaultRequest.Derived());
    return false;
}
if (phase != PassivePhase.Ready)
    return false;
if (!IsValidMonotonic(nowSeconds))
{
    TryFaultInternal(
        "observer_exception",
        FaultRequest.Offending(completedInputs, input));
    return false;
}
if (stateReference == null
    || !Object.ReferenceEquals(stableState, stateReference))
{
    TryFaultInternal(
        "state_replaced",
        FaultRequest.Offending(completedInputs, input));
    return false;
}
attemptPending = true;
attemptOutcomeKnown = false;
attemptInput = input;
attemptState = stateReference;
epoch++;
phase = PassivePhase.Settling;
epochState = stateReference;
epochStartedAt = nowSeconds;
currentFrames = 0;
neutralSeen = false;
candidateSignature = null;
lastCapture = null;
return true;
```

Use this exact correlation order:

```csharp
internal HookToken ProcessInputEntered(
    object stateReference, int rawDirection, double nowSeconds)
{
    if (!IsObservationActive())
        return HookToken.Inert(HookKind.ProcessInput);
    if (playerPoll == null)
    {
        if (phase == PassivePhase.Ready)
            TryFaultInternal(
                "unscoped_process_input", FaultRequest.Derived());
        return HookToken.Inert(HookKind.ProcessInput);
    }
    if (!playerPoll.SawPhysicalPoll || playerPoll.SawManualProcessInput)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return HookToken.Inert(HookKind.ProcessInput);
    }
    playerPoll.SawManualProcessInput = true;
    OracleInput input;
    if (!TryMapCardinal(playerPoll.RawDirection, out input))
    {
        TryFaultInternal(
            "unexpected_input",
            FaultRequest.Offending(completedInputs, null));
        return HookToken.Inert(HookKind.ProcessInput);
    }
    if (playerPoll.RawDirection != rawDirection)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return HookToken.Inert(HookKind.ProcessInput);
    }
    HookToken token = NewToken(HookKind.ProcessInput);
    if (!token.Active)
        return token;
    processInputContext = new ProcessInputContext { Id = token.Id };
    HandleManualAttempt(input, stateReference, nowSeconds);
    return token;
}
```

`PhysicalPollReturned` stores the raw value once, marks neutral only for raw 8,
clears neutral/candidate on any cardinal while Initial/Settling, and faults an
unknown raw with `unexpected_input` plus next index/null input. Returned
callbacks consume only the matching typed context, store outcome/movement only
for a live attempt, and always clear their context; threw callbacks consume and
clear without storing an outcome.

```csharp
internal void PhysicalPollReturned(int rawDirection)
{
    if (!IsObservationActive())
        return;
    if (playerPoll == null || playerPoll.SawPhysicalPoll)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    playerPoll.SawPhysicalPoll = true;
    playerPoll.RawDirection = rawDirection;
    if (rawDirection == 8)
    {
        if (phase == PassivePhase.AwaitInitialNeutral
            || phase == PassivePhase.Settling)
            neutralSeen = true;
        return;
    }
    if (phase == PassivePhase.AwaitInitialNeutral
        || phase == PassivePhase.Settling)
    {
        neutralSeen = false;
        candidateSignature = null;
    }
    OracleInput ignored;
    if (!TryMapCardinal(rawDirection, out ignored))
        TryFaultInternal(
            "unexpected_input",
            FaultRequest.Offending(completedInputs, null));
}

internal void ProcessInputReturned(
    HookToken token, bool accepted, bool movementScheduled)
{
    if (!ConsumeOrdinaryToken(token, HookKind.ProcessInput))
        return;
    if (processInputContext == null
        || processInputContext.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    processInputContext = null;
    if (!attemptPending || !IsObservationActive())
        return;
    attemptAccepted = accepted;
    attemptMovementScheduled = movementScheduled;
    attemptOutcomeKnown = true;
}

internal void ProcessInputThrew(HookToken token)
{
    if (!ConsumeCleanupToken(token, HookKind.ProcessInput))
        return;
    if (processInputContext == null
        || processInputContext.Id != token.Id)
        throw new InvalidOperationException("ProcessInput token mismatch");
    processInputContext = null;
}

internal HookToken UndoEntered(object stateReference, double nowSeconds)
{
    if (!IsObservationActive())
        return HookToken.Inert(HookKind.Undo);
    if (undoContext != null)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return HookToken.Inert(HookKind.Undo);
    }
    HookToken token = NewToken(HookKind.Undo);
    if (!token.Active)
        return token;
    undoContext = new UndoContext { Id = token.Id };
    HandleManualAttempt(OracleInput.Undo, stateReference, nowSeconds);
    return token;
}

internal void RestoreObserved()
{
    if (!IsObservationActive())
        return;
    if (undoContext == null || undoContext.RestoreSeen)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    undoContext.RestoreSeen = true;
}

internal void UndoReturned(HookToken token, bool movementScheduled)
{
    if (!ConsumeOrdinaryToken(token, HookKind.Undo))
        return;
    if (undoContext == null || undoContext.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    bool accepted = undoContext.RestoreSeen;
    undoContext = null;
    if (!attemptPending || !IsObservationActive())
        return;
    attemptAccepted = accepted;
    attemptMovementScheduled = movementScheduled;
    attemptOutcomeKnown = true;
}

internal void UndoThrew(HookToken token)
{
    if (!ConsumeCleanupToken(token, HookKind.Undo))
        return;
    if (undoContext == null || undoContext.Id != token.Id)
        throw new InvalidOperationException("Undo token mismatch");
    undoContext = null;
}
```

`HandleManualAttempt` faults before Initial, preserves pending-attempt
precedence, opens a fresh Settling epoch from exact Ready state, and rejects an
overlap. `ProcessInputEntered` requires an active poll, one returned physical
cardinal, identical direction, and no earlier manual call. Undo acceptance is
exactly `RestoreSeen`; returned ProcessInput/Undo records outcome and movement;
threw paths clear only their typed context.

- [ ] **Step 4: Implement settled Step emission and Error precedence**

In `CompleteUpdateCore`, share the two-capture algorithm between Initial and
Settling. Add:

```csharp
private void EmitSettledAttempt(
    CaptureRecord capture,
    int settleFrames);
```

Write `StepRecord(runId, completedInputs, attemptInput, attemptAccepted,
attemptMovementScheduled, settleFrames, false, capture)` first. Only after a
durable Step, retain the stable state, clear attempt/candidate/last-capture
state, increment `completedInputs`, return to Ready, then call
`reporter.Ready(completedInputs)` once.

Update `BuildErrorRecord` precedence to pending attempt, offending mapped input,
unknown native input, then generic fields. Preflight the worst-case populated
Error around each accepted capture. Step write/flush failure must choose
marker-only `trace_io_failed`, Close once, and emit neither Error nor Ready.

For Task 5.1 the successful post-write body is exactly:

```csharp
sink.WriteStep(new StepRecord(
    runId, completedInputs, attemptInput, attemptAccepted,
    attemptMovementScheduled, settleFrames, false, capture));
stableState = attemptState;
attemptPending = false;
attemptOutcomeKnown = false;
attemptState = null;
candidateSignature = null;
lastCapture = null;
currentFrames = 0;
completedInputs++;
phase = PassivePhase.Ready;
try
{
    reporter.Ready(completedInputs);
}
catch (Exception error)
{
    SafeDiagnostic(error);
    TryFaultInternal("observer_exception", FaultRequest.Derived());
}
```

Wrap only the sink call in the existing trace-I/O conversion boundary. Do not
clear state or report Ready if that call throws. In Task 5.1,
`BuildErrorRecord` chooses fields in this code order: pending attempt; explicit
offending input (including nullable input); generic active Initial frames; all
null/zero. Task 5.2 inserts `ForceNullInputs` ahead of that order. It always
uses the current epoch's `lastCapture`.

Use this exact Task 5.1 `BuildErrorRecord` body:

```csharp
private ErrorRecord BuildErrorRecord(
    string code, FaultRequest request, PassivePhase faultPhase)
{
    int activeFrames = (faultPhase == PassivePhase.AwaitInitialNeutral
        || faultPhase == PassivePhase.Settling) ? currentFrames : 0;
    int frames;
    int? inputIndex = null;
    OracleInput? input = null;
    if (attemptPending)
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : activeFrames;
        inputIndex = completedInputs;
        input = attemptInput;
    }
    else if (request.HasOffendingInput)
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : 0;
        inputIndex = request.OffendingIndex;
        input = request.OffendingInput;
    }
    else
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : activeFrames;
    }
    return new ErrorRecord(
        runId, inputIndex, input, code, frames, lastCapture);
}
```

Before assigning a candidate to `lastCapture`, execute this populated preflight
for every closed error code; only assign after all encodings succeed:

```csharp
for (int index = 0; index < RecordErrorCodes.Length; index++)
{
    CanonicalJson.EncodeError(new ErrorRecord(
        runId,
        Int32.MaxValue,
        OracleInput.North,
        RecordErrorCodes[index],
        OracleProtocol.MaxSettleFrames,
        capture));
}
byte[] signature = CaptureSignature.Compute(capture);
lastCapture = capture;
return signature;
```

- [ ] **Step 5: Run Task 5.1 focused GREEN and the full matrix**

Run the forced net10 build; `driver-boundary`; `driver-initial`; `driver-input`;
full C# harness; forced net35 build; and full Python suite.

Expected: 31 C# tests, six input registrations, no regression in all eight
Initial tests, and every command exits 0.

- [ ] **Step 6: Run pre-commit specification and quality reviews**

Give two fresh independent reviewers the controlling specs, actual working-tree
diff, Task 1 RED, and Task 2 GREEN results. Require explicit verdicts and
severity counts. Fix every Critical/Important and every accepted Minor finding,
rerun affected commands plus the full matrix, and obtain fresh approvals.

- [ ] **Step 7: Commit the exact reviewed Task 5.1 tree**

```bash
plan_commit="$(git log -1 --format=%H -- \
  docs/superpowers/plans/2026-08-12-task-5-lean-execution.md)"
test "$(git rev-parse HEAD)" = "$plan_commit"
git add -- \
  oracle/plugin/Core/PassiveDriver.cs \
  oracle/plugin/Core/PassiveDriverInput.cs \
  oracle/plugin/tests/PassiveDriverInputTests.cs \
  oracle/plugin/tests/PassiveDriverTestSupport.cs \
  oracle/plugin/tests/Program.cs
git diff --cached --check
git commit -m "feat: attribute passive input attempts"
```

Expected: exact five-file scope and the dynamically resolved plan commit as
sole parent.

- [ ] **Step 8: Review the immutable Task 5.1 commit**

Authenticate subject, parent, scope, tree, clean tracked/index state, and the
sole historical untracked plan. Dispatch fresh specification and quality
reviewers over `"$plan_commit"..HEAD` plus RED/GREEN evidence. Do not begin Task 5.2
until both approve with zero Critical and Important findings.

### Task 3: Task 5.2 Tests — Restart and State Replacement

**Files:**
- Modify: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`
- Test: `oracle/plugin/tests/PassiveDriverTestSupport.cs`

**Interfaces:**
- Consumes: immutable approved Task 5.1 and its six input registrations.
- Produces: registrations 7–8 and production expectations for Restart,
  StateSet, and generic throw cleanup.

- [ ] **Step 1: Append the two frozen registrations**

```csharp
tests.Add("driver-input", "restart depth and null fields",
    RestartDepthAndNullFields);
tests.Add("driver-input", "state replacement and ClearThrew",
    StateReplacementAndClearThrew);
```

Change only the manifest count to `{ "driver-input", 8 }`.

- [ ] **Step 2: Add Restart coverage**

Cover every active phase, null input-field override, depth established before
fault selection, recursive Restart, nested Undo/Restore suppression, returned
and throwing paths, LIFO cleanup, duplicate/stale token rejection, and single
consumption. Use a local `ReentrantErrorTraceSink : ITraceSink` whose
`WriteError` callback reenters Restart/Undo/Restore, proving outer depth is
visible before the first fault emits output.

Use private subcases `RestartFieldsFollowEveryActivePhase`,
`RestartDepthPrecedesFault`, `RestartNestedPathsBalance`,
`RestartCleanupIsLifoAndSingleUse`, and `AssertRestartError`.

The registered body is:

```csharp
private static void RestartDepthAndNullFields()
{
    RestartFieldsFollowEveryActivePhase();
    RestartDepthPrecedesFault();
    RestartNestedPathsBalance();
    RestartCleanupIsLifoAndSingleUse();
}
```

`RestartFieldsFollowEveryActivePhase` creates the four fresh fixtures in the
table and passes their one Error to `AssertRestartError(expectedFrames)`, which
asserts code `unexpected_input`, null index/input, the exact frame value, null
End, one Close, and one Failed marker. `RestartDepthPrecedesFault` installs the
reentrant sink, enters the outer Restart, and inside `WriteError` enters/returns
a nested Restart plus Undo/Restore; after the callback it asserts one Error,
zero Steps, and that the outer returned/threw cleanup is single-use.

The primary Restart vectors are:

| Starting phase | Setup | Required Error |
|---|---|---|
| AwaitGame | Active fixture, no observed state | `unexpected_input`, null index/input, zero frames |
| AwaitInitialNeutral | One committed Initial-settle frame | `unexpected_input`, null index/input, one frame |
| Ready | Durable Initial | `unexpected_input`, null index/input, zero frames |
| Settling | Pending West attempt with one committed frame | `unexpected_input`, null index/input, one frame despite pending input |

For the reentrant sink, require nested Restart/Undo/Restore callbacks to balance
without a second Error or Step and require outer return/throw to restore depth to
zero. Out-of-order LIFO pop throws `InvalidOperationException`; duplicate cleanup
is inert after the token is consumed.

Define every called Restart leaf and its local sink:

```csharp
private static void RestartFieldsFollowEveryActivePhase()
{
    AssertRestartError(DriverFixture.Active(), 0, "AwaitGame");

    DriverFixture initial = DriverFixture.Active();
    initial.Observe(
        initial.State, initial.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    AssertRestartError(initial, 1, "AwaitInitialNeutral");

    AssertRestartError(DriverFixture.Ready(), 0, "Ready");

    DriverFixture settling = DriverFixture.Ready();
    settling.OpenDirection(2, true, true, 10.0);
    settling.Observe(
        settling.State, settling.State, 11.0, false,
        ProtocolSamples.MovedCapture);
    AssertRestartError(settling, 1, "Settling");
}

private static void AssertRestartError(
    DriverFixture fixture, int frames, string label)
{
    HookToken token = fixture.Driver.RestartEntered();
    ErrorRecord error = AssertInputError(
        fixture, "unexpected_input", null, null, frames,
        label + " Restart");
    Check.True(error.LastCapture == null, label + " null capture");
    Check.Equal(1, fixture.Sink.CloseCalls, label + " one Close");
    Check.Sequence(
        new string[] { "unexpected_input" },
        fixture.Reporter.FailedCodes.ToArray(),
        label + " Failed marker");
    fixture.Driver.RestartReturned(token);
}

private static void RestartDepthPrecedesFault()
{
    List<string> events = new List<string>();
    ReentrantErrorTraceSink sink = new ReentrantErrorTraceSink(events);
    FakePassiveReporter reporter = new FakePassiveReporter(events);
    PassiveDriver driver = new PassiveDriver(
        sink, reporter, OracleProtocol.ExpectedInputCount, 600, 30.0);
    sink.Driver = driver;
    Check.True(driver.Prepare(ProtocolSamples.Run), "reentrant prepare");
    Check.True(driver.Activate(), "reentrant activate");
    HookToken outer = driver.RestartEntered();
    driver.RestartReturned(outer);
    Check.Equal(1, sink.ErrorRecords.Count, "one reentrant Error");
    Check.Equal(0, sink.StepRecords.Count, "no reentrant Step");
    Check.True(sink.Reentered, "Error callback reentered hooks");
    Check.True(
        sink.NestedRestartActive,
        "Restart depth is established before Error reentry");
    Check.True(
        sink.SuppressedUndoActive,
        "nested Restart keeps suppressed Undo bookkeeping active");
    Check.True(
        sink.NestedCleanupBalanced,
        "reentrant Restart and Undo cleanup balances");
    Check.Sequence(
        new string[] { "unexpected_input" },
        reporter.FailedCodes.ToArray(),
        "outer Restart remains sole marker");
}

private static void RestartNestedPathsBalance()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken outer = fixture.Driver.RestartEntered();
    HookToken inner = fixture.Driver.RestartEntered();
    HookToken undo = fixture.Driver.UndoEntered(fixture.State, 10.0);
    fixture.Driver.RestoreObserved();
    fixture.Driver.UndoReturned(undo, false);
    fixture.Driver.RestartThrew(inner);
    fixture.Driver.RestartReturned(outer);
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "nested one Error");
    Check.Equal(0, fixture.Sink.StepRecords.Count, "nested no Step");
}

private static void RestartCleanupIsLifoAndSingleUse()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken outer = fixture.Driver.RestartEntered();
    HookToken inner = fixture.Driver.RestartEntered();
    Check.Throws<InvalidOperationException>(
        delegate { fixture.Driver.RestartReturned(outer); },
        "outer cannot pop before inner");
    fixture.Driver.RestartReturned(inner);
    fixture.Driver.RestartReturned(outer);
    fixture.Driver.RestartReturned(outer);
    fixture.Driver.RestartThrew(inner);
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "cleanup one Error");
}

private sealed class ReentrantErrorTraceSink : ITraceSink
{
    private readonly IList<string> events;
    internal readonly List<ErrorRecord> ErrorRecords =
        new List<ErrorRecord>();
    internal readonly List<StepRecord> StepRecords =
        new List<StepRecord>();
    internal PassiveDriver Driver;
    internal bool Reentered;
    internal bool NestedRestartActive;
    internal bool SuppressedUndoActive;
    internal bool NestedCleanupBalanced;

    internal ReentrantErrorTraceSink(IList<string> eventsValue)
    {
        events = eventsValue;
    }

    public void WriteRun(RunRecord record) { events.Add("sink:run"); }
    public void WriteInitial(InitialRecord record)
    {
        events.Add("sink:initial");
    }
    public void WriteStep(StepRecord record)
    {
        StepRecords.Add(record);
        events.Add("sink:step:" + record.InputIndex.ToString());
    }
    public void WriteEnd(EndRecord record) { events.Add("sink:end"); }
    public void WriteError(ErrorRecord record)
    {
        events.Add("sink:error:" + record.Code);
        if (!Reentered)
        {
            Reentered = true;
            HookToken nested = Driver.RestartEntered();
            HookToken undo = Driver.UndoEntered(new object(), 1.0);
            NestedRestartActive = nested.Active;
            SuppressedUndoActive = undo.Active;
            Driver.RestoreObserved();
            Driver.UndoReturned(undo, false);
            Driver.RestartReturned(nested);
            NestedCleanupBalanced = true;
        }
        ErrorRecords.Add(record);
    }
    public void Close() { events.Add("sink:close"); }
}
```

- [ ] **Step 3: Add StateSet and late-cleanup coverage**

Cover actual returned identity rather than the requested argument, exact entry
context identity, pre-Initial null/same/replacement rules, post-Initial
`state_replaced`, pending-attempt Error precedence, frame-zero explicit
replacement, kind/owner protection in `ClearThrew`, and output-inert late
callbacks after Disabled/Faulted/disposal. Keep the production Done branch
output-inert, but defer its reachable callback oracle to Task 5.3, where Done
exists; do not manufacture Done in this slice.

Use private subcases `StateSetUsesActualReturnedIdentity`,
`StateSetContextIdentityIsAuthoritative`, `StateSetBeforeInitialRulesAreExact`,
`StateSetAfterInitialRulesAreExact`, `ClearThrewDispatchesAndProtectsOwnership`,
and `LateHookCleanupIsOutputInert`.

The second registered body is:

```csharp
private static void StateReplacementAndClearThrew()
{
    StateSetUsesActualReturnedIdentity();
    StateSetContextIdentityIsAuthoritative();
    StateSetBeforeInitialRulesAreExact();
    StateSetAfterInitialRulesAreExact();
    ClearThrewDispatchesAndProtectsOwnership();
    LateHookCleanupIsOutputInert();
}
```

Each StateSet leaf enters with `(before, requested)`, returns the table's
`actual after`, and asserts exact reference identity, phase, frame count, and
record/reporter delta. `ClearThrewDispatchesAndProtectsOwnership` exercises
matching dispatch and duplicate cleanup for every HookKind. Its paired-context
subcases clear one live kind and then successfully clear the other, proving
that independent contexts are not cross-cleared; its foreign-owner subcase
proves rejection without consuming the local context. The late leaf
captures event/record/counter snapshots before return/throw and asserts they are
byte-for-byte/count-for-count unchanged afterward.

The primary StateSet vectors are:

| Phase | Before / requested / actual after | Required outcome |
|---|---|---|
| AwaitInitialNeutral | state A / requested B / null | AwaitGame; frames zero; candidate and last capture cleared |
| AwaitInitialNeutral | state A / requested B / same reference A | No replacement; requested argument has no effect |
| AwaitInitialNeutral | state A / A / different non-null B | Fresh AwaitInitialNeutral epoch at frame zero |
| Ready | state A / requested B / same reference A | Ready; no Error or Step |
| Ready | state A / A / different non-null B | `state_replaced`, null input fields, no Step |
| Settling | state A / requested B / different non-null B | `state_replaced` with the pending attempt index/input/frames |

For every hook kind, `ClearThrew` consumes only that token's matching owned
context. Clearing another live kind does not cross-clear it, and a foreign
owner cannot consume local state. A matching callback that
returns after Disable, fault selection, or disposal clears its own context and
produces no sink/reporter event.

Define every called StateSet/cleanup leaf:

```csharp
private static void StateSetUsesActualReturnedIdentity()
{
    DriverFixture same = DriverFixture.Ready();
    HookToken sameToken = same.Driver.StateSetEntered(
        same.State, same.OtherState);
    same.Driver.StateSetReturned(sameToken, same.State, 10.0);
    Check.Equal(PassivePhase.Ready, same.Driver.Phase, "actual same wins");
    Check.Equal(0, same.Sink.ErrorRecords.Count, "requested ignored");

    DriverFixture different = DriverFixture.Ready();
    HookToken differentToken = different.Driver.StateSetEntered(
        different.State, different.State);
    different.Driver.StateSetReturned(
        differentToken, different.OtherState, 10.0);
    AssertInputError(
        different, "state_replaced", null, null, 0,
        "actual different wins");
}

private static void StateSetContextIdentityIsAuthoritative()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken token = fixture.Driver.StateSetEntered(
        fixture.State, fixture.OtherState);
    fixture.Driver.StateSetReturned(token, fixture.State, 10.0);
    Check.Equal(PassivePhase.Ready, fixture.Driver.Phase, "entry identity");
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, "no diagnostic equality");
}

private static void StateSetBeforeInitialRulesAreExact()
{
    DriverFixture toNull = DriverFixture.Active();
    toNull.Observe(
        toNull.State, toNull.State, 1.0, true,
        ProtocolSamples.Capture("null-stale"));
    toNull.Neutral();
    toNull.Observe(
        toNull.State, toNull.State, 2.0, true,
        ProtocolSamples.Capture("null-stale"));
    HookToken nullToken = toNull.Driver.StateSetEntered(
        toNull.State, toNull.OtherState);
    toNull.Driver.StateSetReturned(nullToken, null, 3.0);
    Check.Equal(PassivePhase.AwaitGame, toNull.Driver.Phase, "null AwaitGame");
    Check.Equal(0, toNull.Driver.CurrentSettleFrames, "null clears frames");

    DriverFixture nullFault = DriverFixture.Active();
    nullFault.Observe(
        nullFault.State, nullFault.State, 1.0, true,
        ProtocolSamples.Capture("null-capture"));
    nullFault.Neutral();
    nullFault.Observe(
        nullFault.State, nullFault.State, 2.0, true,
        ProtocolSamples.Capture("null-capture"));
    HookToken nullFaultToken = nullFault.Driver.StateSetEntered(
        nullFault.State, nullFault.OtherState);
    nullFault.Driver.StateSetReturned(nullFaultToken, null, 3.0);
    Check.True(
        nullFault.Driver.TryFault("capture_failed"),
        "post-null generic fault claims");
    Check.True(
        nullFault.Sink.ErrorRecords[0].LastCapture == null,
        "null reset clears last capture");

    DriverFixture same = DriverFixture.Active();
    same.Observe(
        same.State, same.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    HookToken sameToken = same.Driver.StateSetEntered(
        same.State, same.OtherState);
    same.Driver.StateSetReturned(sameToken, same.State, 2.0);
    Check.Equal(
        PassivePhase.AwaitInitialNeutral, same.Driver.Phase,
        "same reference retains Initial");

    DriverFixture replaced = DriverFixture.Active();
    replaced.Observe(
        replaced.State, replaced.State, 1.0, true,
        ProtocolSamples.Capture("replacement-stale"));
    replaced.Neutral();
    replaced.Observe(
        replaced.State, replaced.State, 2.0, true,
        ProtocolSamples.Capture("replacement-stale"));
    HookToken replacedToken = replaced.Driver.StateSetEntered(
        replaced.State, replaced.State);
    replaced.Driver.StateSetReturned(
        replacedToken, replaced.OtherState, 3.0);
    Check.Equal(
        PassivePhase.AwaitInitialNeutral, replaced.Driver.Phase,
        "replacement restarts Initial");
    Check.Equal(0, replaced.Driver.CurrentSettleFrames, "replacement frame zero");
    replaced.Neutral();
    replaced.Observe(
        replaced.OtherState, replaced.OtherState, 4.0, true,
        ProtocolSamples.Capture("replacement-fresh"));
    Check.Equal(
        0, replaced.Sink.InitialRecords.Count,
        "replacement requires first fresh capture");
    replaced.Observe(
        replaced.OtherState, replaced.OtherState, 5.0, true,
        ProtocolSamples.Capture("replacement-fresh"));
    Check.Equal(
        1, replaced.Sink.InitialRecords.Count,
        "replacement settles only a fresh pair");
}

private static void StateSetAfterInitialRulesAreExact()
{
    DriverFixture ready = DriverFixture.Ready();
    HookToken same = ready.Driver.StateSetEntered(
        ready.State, ready.OtherState);
    ready.Driver.StateSetReturned(same, ready.State, 10.0);
    Check.Equal(0, ready.Sink.ErrorRecords.Count, "Ready same no Error");

    DriverFixture replaced = DriverFixture.Ready();
    HookToken different = replaced.Driver.StateSetEntered(
        replaced.State, replaced.State);
    replaced.Driver.StateSetReturned(
        different, replaced.OtherState, 10.0);
    AssertInputError(
        replaced, "state_replaced", null, null, 0,
        "Ready replacement");

    DriverFixture settling = DriverFixture.Ready();
    settling.OpenDirection(2, true, true, 10.0);
    settling.Observe(
        settling.State, settling.State, 11.0, false,
        ProtocolSamples.MovedCapture);
    HookToken pending = settling.Driver.StateSetEntered(
        settling.State, settling.State);
    settling.Driver.StateSetReturned(
        pending, settling.OtherState, 12.0);
    AssertInputError(
        settling, "state_replaced", 0, OracleInput.West, 1,
        "Settling replacement");
}

private static void ClearThrewDispatchesAndProtectsOwnership()
{
    DriverFixture dispatchPoll = DriverFixture.Ready();
    HookToken directPoll = dispatchPoll.Driver.PlayerPollEntered();
    dispatchPoll.Driver.ClearThrew(directPoll);
    dispatchPoll.Driver.PhysicalPollReturned(8);
    dispatchPoll.Driver.ClearThrew(directPoll);

    DriverFixture dispatchProcess = DriverFixture.Ready();
    HookToken directProcessPoll = dispatchProcess.Driver.PlayerPollEntered();
    dispatchProcess.Driver.PhysicalPollReturned(2);
    HookToken directProcess = dispatchProcess.Driver.ProcessInputEntered(
        dispatchProcess.State, 2, 10.0);
    dispatchProcess.Driver.ClearThrew(directProcess);
    dispatchProcess.Driver.ProcessInputReturned(
        directProcess, true, false);
    Check.Throws<InvalidOperationException>(
        delegate
        {
            Check.True(
                dispatchProcess.Driver.PendingAccepted,
                "cleared ProcessInput getter unexpectedly returned");
        },
        "cleared ProcessInput cannot publish an outcome");
    dispatchProcess.Driver.ClearThrew(directProcess);
    dispatchProcess.Driver.ClearThrew(directProcessPoll);

    DriverFixture dispatchUndo = DriverFixture.Ready();
    HookToken directUndo = dispatchUndo.Driver.UndoEntered(
        dispatchUndo.State, 10.0);
    dispatchUndo.Driver.ClearThrew(directUndo);
    dispatchUndo.Driver.RestoreObserved();
    dispatchUndo.Driver.ClearThrew(directUndo);

    DriverFixture dispatchRestart = DriverFixture.Ready();
    HookToken directRestart = dispatchRestart.Driver.RestartEntered();
    dispatchRestart.Driver.ClearThrew(directRestart);
    HookToken postClearRestart = dispatchRestart.Driver.RestartEntered();
    Check.False(
        postClearRestart.Active,
        "cleared Restart leaves no nested depth after terminal selection");
    dispatchRestart.Driver.ClearThrew(directRestart);

    DriverFixture dispatchStateSet = DriverFixture.Ready();
    HookToken directStateSet = dispatchStateSet.Driver.StateSetEntered(
        dispatchStateSet.State, dispatchStateSet.OtherState);
    dispatchStateSet.Driver.ClearThrew(directStateSet);
    dispatchStateSet.Driver.StateSetReturned(
        directStateSet, dispatchStateSet.OtherState, 10.0);
    dispatchStateSet.Driver.ClearThrew(directStateSet);

    Check.Equal(
        1, dispatchPoll.Sink.ErrorRecords.Count,
        "cleared PlayerPoll rejects later physical return");
    AssertInputError(
        dispatchProcess, "hook_order_mismatch", 0, OracleInput.West, 0,
        "cleared ProcessInput rejects consumed-token return");
    Check.Equal(
        1, dispatchUndo.Sink.ErrorRecords.Count,
        "cleared Undo rejects later Restore");
    Check.Equal(
        1, dispatchRestart.Sink.ErrorRecords.Count,
        "Restart direct ClearThrew adds no second Error");
    AssertInputError(
        dispatchStateSet, "hook_order_mismatch", null, null, 0,
        "cleared StateSet rejects consumed-token return");

    DriverFixture pollFixture = DriverFixture.Ready();
    HookToken poll = pollFixture.Driver.PlayerPollEntered();
    HookToken pollUnrelated = pollFixture.Driver.StateSetEntered(
        pollFixture.State, pollFixture.OtherState);
    List<string> pollBefore = new List<string>(pollFixture.Events);
    pollFixture.Driver.ClearThrew(pollUnrelated);
    pollFixture.Driver.PhysicalPollReturned(8);
    pollFixture.Driver.PlayerPollReturned(poll);
    pollFixture.Driver.ClearThrew(poll);
    Check.Sequence(
        pollBefore, pollFixture.Events,
        "StateSet cleanup preserves PlayerPoll until matching cleanup");

    DriverFixture processFixture = DriverFixture.Ready();
    HookToken processPoll = processFixture.Driver.PlayerPollEntered();
    processFixture.Driver.PhysicalPollReturned(2);
    HookToken process = processFixture.Driver.ProcessInputEntered(
        processFixture.State, 2, 10.0);
    HookToken processUnrelated = processFixture.Driver.StateSetEntered(
        processFixture.State, processFixture.OtherState);
    List<string> processBefore = new List<string>(processFixture.Events);
    processFixture.Driver.ClearThrew(processUnrelated);
    processFixture.Driver.ProcessInputReturned(process, true, false);
    Check.True(
        processFixture.Driver.PendingAccepted,
        "ProcessInput remains live after StateSet cleanup");
    processFixture.Driver.ClearThrew(process);
    processFixture.Driver.ClearThrew(processPoll);
    Check.Sequence(
        processBefore, processFixture.Events,
        "StateSet cleanup preserves ProcessInput until matching cleanup");

    DriverFixture undoFixture = DriverFixture.Ready();
    HookToken undo = undoFixture.Driver.UndoEntered(
        undoFixture.State, 10.0);
    HookToken undoUnrelated = undoFixture.Driver.StateSetEntered(
        undoFixture.State, undoFixture.OtherState);
    List<string> undoBefore = new List<string>(undoFixture.Events);
    undoFixture.Driver.ClearThrew(undoUnrelated);
    undoFixture.Driver.RestoreObserved();
    undoFixture.Driver.UndoReturned(undo, false);
    Check.True(
        undoFixture.Driver.PendingAccepted,
        "Undo remains live after StateSet cleanup");
    undoFixture.Driver.ClearThrew(undo);
    Check.Sequence(
        undoBefore, undoFixture.Events,
        "StateSet cleanup preserves Undo until matching cleanup");

    DriverFixture restartFixture = DriverFixture.Ready();
    HookToken restartUnrelated = restartFixture.Driver.StateSetEntered(
        restartFixture.State, restartFixture.OtherState);
    HookToken restart = restartFixture.Driver.RestartEntered();
    List<string> restartBefore = new List<string>(restartFixture.Events);
    restartFixture.Driver.ClearThrew(restartUnrelated);
    HookToken nestedRestart = restartFixture.Driver.RestartEntered();
    Check.True(
        nestedRestart.Active,
        "Restart depth remains live after StateSet cleanup");
    restartFixture.Driver.RestartReturned(nestedRestart);
    restartFixture.Driver.RestartReturned(restart);
    restartFixture.Driver.ClearThrew(restart);
    Check.Sequence(
        restartBefore, restartFixture.Events,
        "StateSet cleanup preserves Restart until matching cleanup");

    DriverFixture stateSetFixture = DriverFixture.Ready();
    HookToken stateSet = stateSetFixture.Driver.StateSetEntered(
        stateSetFixture.State, stateSetFixture.OtherState);
    HookToken stateSetUnrelated =
        stateSetFixture.Driver.PlayerPollEntered();
    List<string> stateSetBefore = new List<string>(stateSetFixture.Events);
    stateSetFixture.Driver.ClearThrew(stateSetUnrelated);
    stateSetFixture.Driver.StateSetReturned(
        stateSet, stateSetFixture.State, 10.0);
    stateSetFixture.Driver.ClearThrew(stateSet);
    Check.Sequence(
        stateSetBefore, stateSetFixture.Events,
        "PlayerPoll cleanup preserves StateSet until matching cleanup");

    DriverFixture owner = DriverFixture.Ready();
    HookToken ownerPoll = owner.Driver.PlayerPollEntered();
    DriverFixture foreign = DriverFixture.Ready();
    HookToken foreignPoll = foreign.Driver.PlayerPollEntered();
    List<string> ownerBefore = new List<string>(owner.Events);
    Check.Throws<InvalidOperationException>(
        delegate { owner.Driver.ClearThrew(foreignPoll); },
        "foreign cleanup rejected");
    owner.Driver.PhysicalPollReturned(8);
    owner.Driver.PlayerPollReturned(ownerPoll);
    owner.Driver.ClearThrew(ownerPoll);
    foreign.Driver.ClearThrew(foreignPoll);
    Check.Sequence(
        ownerBefore, owner.Events,
        "foreign cleanup cannot clear the owned PlayerPoll");

    Check.Equal(0, pollFixture.Sink.ErrorRecords.Count, "poll cleanup no Error");
    Check.Equal(
        0, processFixture.Sink.ErrorRecords.Count,
        "ProcessInput cleanup no Error");
    Check.Equal(0, undoFixture.Sink.ErrorRecords.Count, "Undo cleanup no Error");
    Check.Equal(
        1, restartFixture.Sink.ErrorRecords.Count,
        "Restart entry retains its sole terminal Error");
    Check.Equal(
        0, stateSetFixture.Sink.ErrorRecords.Count,
        "StateSet cleanup no Error");
}

private static void LateHookCleanupIsOutputInert()
{
    DriverFixture faulted = DriverFixture.Ready();
    HookToken poll = faulted.Driver.PlayerPollEntered();
    Check.True(faulted.Driver.TryFault("capture_failed"), "fault wins");
    List<string> faultedBefore = new List<string>(faulted.Events);
    faulted.Driver.PlayerPollReturned(poll);
    faulted.Driver.PlayerPollThrew(poll);
    Check.Sequence(
        faultedBefore, faulted.Events,
        "late faulted PlayerPoll is output-inert");

    DriverFixture disabled = DriverFixture.Ready();
    HookToken disabledStateSet = disabled.Driver.StateSetEntered(
        disabled.State, disabled.OtherState);
    disabled.Driver.Disable();
    List<string> disabledBefore = new List<string>(disabled.Events);
    disabled.Driver.StateSetReturned(
        disabledStateSet, disabled.OtherState, 10.0);
    disabled.Driver.StateSetThrew(disabledStateSet);
    Check.Sequence(
        disabledBefore, disabled.Events,
        "late Disabled StateSet is output-inert");

    DriverFixture disposedProcess = DriverFixture.Ready();
    HookToken processPoll = disposedProcess.Driver.PlayerPollEntered();
    disposedProcess.Driver.PhysicalPollReturned(2);
    HookToken process = disposedProcess.Driver.ProcessInputEntered(
        disposedProcess.State, 2, 10.0);
    disposedProcess.Driver.Dispose();
    List<string> processBefore = new List<string>(disposedProcess.Events);
    disposedProcess.Driver.ProcessInputReturned(process, true, true);
    disposedProcess.Driver.ProcessInputThrew(process);
    disposedProcess.Driver.PlayerPollReturned(processPoll);
    Check.Sequence(
        processBefore, disposedProcess.Events,
        "late disposed ProcessInput is output-inert");

    DriverFixture disposedUndo = DriverFixture.Ready();
    HookToken undo = disposedUndo.Driver.UndoEntered(
        disposedUndo.State, 10.0);
    disposedUndo.Driver.RestoreObserved();
    disposedUndo.Driver.Dispose();
    List<string> undoBefore = new List<string>(disposedUndo.Events);
    disposedUndo.Driver.UndoReturned(undo, false);
    disposedUndo.Driver.UndoThrew(undo);
    Check.Sequence(
        undoBefore, disposedUndo.Events,
        "late disposed Undo is output-inert");

    Check.Equal(1, faulted.Sink.ErrorRecords.Count, "faulted one Error");
    Check.Equal(
        0, disabled.Sink.ErrorRecords.Count,
        "Disabled StateSet no Error");
    Check.Equal(
        0, disposedProcess.Sink.ErrorRecords.Count,
        "disposed ProcessInput no Error");
    Check.Equal(
        0, disposedUndo.Sink.ErrorRecords.Count,
        "disposed Undo no Error");
}
```

`StateSetContextIdentityIsAuthoritative` deliberately uses only object
reference assertions; the other five leaves cover every distinct branch in the
StateSet table. `ClearThrewDispatchesAndProtectsOwnership` covers the shared
dispatcher and foreign-owner rejection, while Task 5.1's typed throw tests
already cover the remaining PlayerPoll/ProcessInput/Undo matching branches.

- [ ] **Step 4: Build to verify the expected compile RED**

Run the forced net10 build.

Expected: missing-member diagnostics only for:

```text
RestartEntered
RestartReturned
RestartThrew
StateSetEntered
StateSetReturned
StateSetThrew
ClearThrew
```

Reject all unrelated failures and preserve the concise RED output externally.

### Task 4: Task 5.2 Production — Balance Lifecycle Hooks

**Files:**
- Modify: `oracle/plugin/Core/PassiveDriver.cs`
- Modify: `oracle/plugin/Core/PassiveDriverInput.cs`
- Create: `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs`
- Test: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Test: `oracle/plugin/tests/PassiveDriverInitialTests.cs`

**Interfaces:**
- Consumes: approved Task 5.1 attempt/token state.
- Produces:

```csharp
internal HookToken RestartEntered();
internal void RestartReturned(HookToken token);
internal void RestartThrew(HookToken token);

internal HookToken StateSetEntered(
    object beforeState, object requestedState);
internal void StateSetReturned(
    HookToken token, object afterState, double nowSeconds);
internal void StateSetThrew(HookToken token);
internal void ClearThrew(HookToken token);
```

- [ ] **Step 1: Add Restart null-field precedence and late-token ownership**

Add `FaultRequest.ForceNullInputs` and `FaultRequest.Restart()`. Restart must
override pending input fields while retaining the applicable active frame count.
Change `ConsumeLateToken` from `void` to `bool`, returning whether the matching
owned token was consumed, so late callbacks can clear only their exact context.

```csharp
private bool ConsumeLateToken(HookToken token, HookKind expectedKind)
{
    if (token == null || !token.Active)
        return false;
    return token.BelongsTo(this)
        && token.Kind == expectedKind
        && token.TryConsume();
}
```

The exact Task 5.2 additions and final Error builder are:

```csharp
internal bool ForceNullInputs;

internal static FaultRequest Restart()
{
    FaultRequest value = new FaultRequest();
    value.ForceNullInputs = true;
    return value;
}

private ErrorRecord BuildErrorRecord(
    string code, FaultRequest request, PassivePhase faultPhase)
{
    int activeFrames = (faultPhase == PassivePhase.AwaitInitialNeutral
        || faultPhase == PassivePhase.Settling) ? currentFrames : 0;
    int frames;
    int? inputIndex = null;
    OracleInput? input = null;
    if (request.ForceNullInputs)
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : activeFrames;
    }
    else if (attemptPending)
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : activeFrames;
        inputIndex = completedInputs;
        input = attemptInput;
    }
    else if (request.HasOffendingInput)
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : 0;
        inputIndex = request.OffendingIndex;
        input = request.OffendingInput;
    }
    else
    {
        frames = request.FrameOverride.HasValue
            ? request.FrameOverride.Value : activeFrames;
    }
    return new ErrorRecord(
        runId, inputIndex, input, code, frames, lastCapture);
}
```

- [ ] **Step 2: Implement lifecycle contexts in a focused partial file**

Create `PassiveDriverLifecycleHooks.cs` with this wrapper and place every
lifecycle member from this task inside it:

```csharp
using System;
using System.Collections.Generic;

internal sealed partial class PassiveDriver
{

private sealed class StateSetContext
{
    internal long Id;
    internal object Before;
}

private readonly List<long> restartContexts = new List<long>();
private int restartDepth;
private StateSetContext stateSetContext;

// The Restart, StateSet, and ClearThrew members below continue here.
}
```

Implement the seven methods above plus `PopRestart(long id)` and
`ValidateRestartPopOrder(HookToken token)`. In `RestartEntered`, allocate and
push the token and increment depth before the outermost
`TryFaultInternal("unexpected_input", FaultRequest.Restart())`. Nested Restart
only balances. `StateSetEntered` stores `beforeState` and deliberately does not
read `requestedState`; `StateSetReturned` compares that entry reference with
the actual post-return `afterState`.

Before Initial, null resets AwaitGame and a different non-null post-state starts
an Initial epoch at frame zero. After Initial, any different reference faults
with `state_replaced` and emits no Step. `ClearThrew` dispatches only by the
token's existing `HookKind` and never clears an unrelated context.

Implement Restart with this ordering (the ordinary/cleanup token validators are
the existing exact-owner validators from `PassiveDriver.cs`):

```csharp
internal HookToken RestartEntered()
{
    bool nested = restartDepth > 0;
    if (!nested && !IsObservationActive())
        return HookToken.Inert(HookKind.Restart);
    HookToken token = NewToken(HookKind.Restart);
    if (!token.Active)
        return token;
    restartContexts.Add(token.Id);
    restartDepth++;
    if (!nested)
        TryFaultInternal("unexpected_input", FaultRequest.Restart());
    return token;
}

private void PopRestart(long id)
{
    int last = restartContexts.Count - 1;
    if (last < 0 || restartContexts[last] != id)
        throw new InvalidOperationException("restart token mismatch");
    restartContexts.RemoveAt(last);
    restartDepth--;
    if (restartDepth < 0 || restartDepth != restartContexts.Count)
        throw new InvalidOperationException("restart depth imbalance");
}

internal void RestartReturned(HookToken token)
{
    ValidateRestartPopOrder(token);
    if (!ConsumeOrdinaryToken(token, HookKind.Restart))
        return;
    PopRestart(token.Id);
}

internal void RestartThrew(HookToken token)
{
    ValidateRestartPopOrder(token);
    if (!ConsumeCleanupToken(token, HookKind.Restart))
        return;
    PopRestart(token.Id);
}

private void ValidateRestartPopOrder(HookToken token)
{
    if (token == null || !token.Active || !token.BelongsTo(this)
        || token.Kind != HookKind.Restart)
        return;
    int index = restartContexts.IndexOf(token.Id);
    if (index >= 0 && index != restartContexts.Count - 1)
        throw new InvalidOperationException("restart token mismatch");
}
```

`StateSetEntered` issues one typed token, rejects an overlapping context, and
stores only `{ Id = token.Id, Before = beforeState }`. `requestedState` is
deliberately unread. The three complete methods are:

```csharp
internal HookToken StateSetEntered(
    object beforeState, object requestedState)
{
    if (!IsObservationActive())
        return HookToken.Inert(HookKind.StateSet);
    if (stateSetContext != null)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return HookToken.Inert(HookKind.StateSet);
    }
    HookToken token = NewToken(HookKind.StateSet);
    if (!token.Active)
        return token;
    stateSetContext = new StateSetContext
    {
        Id = token.Id,
        Before = beforeState
    };
    return token;
}

internal void StateSetReturned(
    HookToken token, object afterState, double nowSeconds)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.StateSet)
            && stateSetContext != null
            && stateSetContext.Id == token.Id)
            stateSetContext = null;
        return;
    }
    if (!ConsumeOrdinaryToken(token, HookKind.StateSet))
        return;
    if (stateSetContext == null || stateSetContext.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    StateSetContext context = stateSetContext;
    stateSetContext = null;
    if (!IsValidMonotonic(nowSeconds))
    {
        TryFaultInternal("observer_exception", FaultRequest.Derived());
        return;
    }
    bool replaced = !Object.ReferenceEquals(context.Before, afterState);
    if (phase == PassivePhase.AwaitGame
        || phase == PassivePhase.AwaitInitialNeutral)
    {
        if (afterState == null)
            ResetToAwaitGame();
        else if (replaced)
            StartInitialEpoch(afterState, nowSeconds, false);
        return;
    }
    if ((phase == PassivePhase.Ready || phase == PassivePhase.Settling)
        && replaced)
        TryFaultInternal("state_replaced", FaultRequest.Derived());
}

internal void StateSetThrew(HookToken token)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.StateSet)
            && stateSetContext != null
            && stateSetContext.Id == token.Id)
            stateSetContext = null;
        return;
    }
    if (!ConsumeCleanupToken(token, HookKind.StateSet))
        return;
    if (stateSetContext == null || stateSetContext.Id != token.Id)
        throw new InvalidOperationException("StateSet token mismatch");
    stateSetContext = null;
}
```

`ClearThrew` is the closed dispatcher:

```csharp
internal void ClearThrew(HookToken token)
{
if (token == null || !token.Active)
    return;
switch (token.Kind)
{
    case HookKind.PlayerPoll: PlayerPollThrew(token); return;
    case HookKind.ProcessInput: ProcessInputThrew(token); return;
    case HookKind.Undo: UndoThrew(token); return;
    case HookKind.Restart: RestartThrew(token); return;
    case HookKind.StateSet: StateSetThrew(token); return;
    default:
        throw new InvalidOperationException("unknown hook kind");
}
}
```

- [ ] **Step 3: Make ProcessInput and Undo late returns precise**

In `PassiveDriverInput.cs`, suppress Undo/Restore when `restartDepth > 0`.
For ProcessInput and Undo returned callbacks, if the driver became inert after
entry, consume the matching token and clear only its exact context without
records or reporter calls. Keep typed threw cleanup strict and preserve the
original game exception.

A nested Restart Undo still owns balanced bookkeeping but never an attempt:

```csharp
internal HookToken UndoEntered(object stateReference, double nowSeconds)
{
    bool suppressed = restartDepth > 0;
    if (!suppressed && !IsObservationActive())
        return HookToken.Inert(HookKind.Undo);
    if (undoContext != null)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return HookToken.Inert(HookKind.Undo);
    }
    HookToken token = NewToken(HookKind.Undo);
    if (!token.Active)
        return token;
    undoContext = new UndoContext { Id = token.Id };
    if (!suppressed)
        HandleManualAttempt(OracleInput.Undo, stateReference, nowSeconds);
    return token;
}

internal void RestoreObserved()
{
    if (restartDepth > 0)
        return;
    if (!IsObservationActive())
        return;
    if (undoContext == null || undoContext.RestoreSeen)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    undoContext.RestoreSeen = true;
}
```

Replace the two returned paths with these concrete forms:

```csharp
internal void ProcessInputReturned(
    HookToken token, bool accepted, bool movementScheduled)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.ProcessInput)
            && processInputContext != null
            && processInputContext.Id == token.Id)
            processInputContext = null;
        return;
    }
    if (!ConsumeOrdinaryToken(token, HookKind.ProcessInput))
        return;
    if (processInputContext == null
        || processInputContext.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    processInputContext = null;
    if (restartDepth > 0 || !attemptPending)
        return;
    attemptAccepted = accepted;
    attemptMovementScheduled = movementScheduled;
    attemptOutcomeKnown = true;
}

internal void UndoReturned(HookToken token, bool movementScheduled)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.Undo)
            && undoContext != null && undoContext.Id == token.Id)
            undoContext = null;
        return;
    }
    if (!ConsumeOrdinaryToken(token, HookKind.Undo))
        return;
    if (undoContext == null || undoContext.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    bool accepted = undoContext.RestoreSeen;
    undoContext = null;
    if (restartDepth > 0 || !attemptPending)
        return;
    attemptAccepted = accepted;
    attemptMovementScheduled = movementScheduled;
    attemptOutcomeKnown = true;
}
```

Update both PlayerPoll late branches too; this prevents an owned poll context
from surviving a callback that returns after terminal selection:

```csharp
internal void PlayerPollReturned(HookToken token)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.PlayerPoll)
            && playerPoll != null && playerPoll.Id == token.Id)
            playerPoll = null;
        return;
    }
    if (!ConsumeOrdinaryToken(token, HookKind.PlayerPoll))
        return;
    if (playerPoll == null || playerPoll.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    playerPoll = null;
}

internal void PlayerPollThrew(HookToken token)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.PlayerPoll)
            && playerPoll != null && playerPoll.Id == token.Id)
            playerPoll = null;
        return;
    }
    if (!ConsumeCleanupToken(token, HookKind.PlayerPoll))
        return;
    if (playerPoll == null || playerPoll.Id != token.Id)
        throw new InvalidOperationException("player-poll token mismatch");
    playerPoll = null;
}
```

In `LateHookCleanupIsOutputInert`, cover a real PlayerPoll after ordinary fault,
a real ProcessInput after Dispose, and a real Undo after Dispose. Snapshot all
sink/reporter events after terminal output, call each matching return and then
its duplicate cleanup, and require no exception or event/count delta. The
matching ID branches above are the reviewed bookkeeping-clear oracles; do not
expose hook contexts through reflection.

- [ ] **Step 4: Run Task 5.2 focused GREEN and the full matrix**

Run forced net10 build; `driver-boundary`; `driver-initial`; `driver-input`;
full C# harness; forced net35 build; and full Python suite.

Expected: 33 C# tests, exactly eight input registrations, and all commands exit
0 with no tracked/index changes beyond the five Task 5.2 paths.

- [ ] **Step 5: Run pre-commit specification and quality reviews**

Give fresh reviewers the controlling specs, immutable Task 5.1 parent, actual
Task 5.2 diff, compile RED, and complete GREEN evidence. Resolve and re-review
all required findings before commit.

- [ ] **Step 6: Commit the exact reviewed Task 5.2 tree**

```bash
git add -- \
  oracle/plugin/Core/PassiveDriver.cs \
  oracle/plugin/Core/PassiveDriverInput.cs \
  oracle/plugin/Core/PassiveDriverLifecycleHooks.cs \
  oracle/plugin/tests/PassiveDriverInputTests.cs \
  oracle/plugin/tests/Program.cs
git diff --cached --check
git commit -m "feat: balance passive lifecycle hooks"
```

Expected: exact five-file scope and the approved Task 5.1 commit as sole parent.

- [ ] **Step 7: Review the immutable Task 5.2 commit**

Authenticate subject, parent, scope, tree, clean tracked/index state, and the
historical untracked plan. Dispatch fresh reviewers over `HEAD^..HEAD`. Do not
begin Task 5.3 until both independent lanes approve with zero Critical and
Important findings.

### Task 5: Task 5.3 Final Tests — Completion, Serialization, and Rebase

**Files:**
- Create: `oracle/plugin/tests/PassiveDriverTerminalTests.cs`
- Create: `oracle/plugin/tests/PassiveDriverTests.cs`
- Modify: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTestSupport.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes: immutable approved Task 5.2, eight input registrations, real
  `NdjsonTraceSink`, and existing `ITraceOutput`.
- Produces: six terminal registrations, deterministic blocking fixtures, and
  three sequential behavioral RED checkpoints inside one final slice.

- [ ] **Step 1: Move Step 2 continuation ownership to the terminal cohort**

Rename the Task 5.1 helper `EverySettledStepReportsReady` to
`EveryIntermediateSettledStepReportsReady`. Stop after Step 1 and require Ready
values `0,1,2`; the final Step/Ready(3) distinction belongs to Task 5.3.

- [ ] **Step 2: Add terminal failure and barrier support**

Add `using System.IO;` and `using System.Threading;` to
`PassiveDriverTestSupport.cs`; keep its existing imports.

Extend `FakeTraceSink` with `EndFailure`; pre-durability callbacks
`RunEntering`, `InitialEntering`, `StepEntering`, and `ErrorEntering`; and
post-record callbacks `StepObserved` and `EndObserved`. Extend
`FakePassiveReporter` with `CompleteFailure`, `ReadyObserved`, and
`CompleteObserved`.

Declare the callbacks exactly:

```csharp
internal Action<RunRecord> RunEntering { get; set; }
internal Action<InitialRecord> InitialEntering { get; set; }
internal Action<StepRecord> StepEntering { get; set; }
internal Action<StepRecord> StepObserved { get; set; }
internal Action<EndRecord> EndObserved { get; set; }
internal Action<ErrorRecord> ErrorEntering { get; set; }
internal Action<int> ReadyObserved { get; set; }
internal Action CompleteObserved { get; set; }
internal Action<string> DiagnosticObserved { get; set; }
internal Exception EndFailure { get; set; }
internal Exception CompleteFailure { get; set; }
```

Every sink `Entering` callback runs before its call counter, event, failure, or
record mutation. `StepObserved` and `EndObserved` run after the record is added.
Ready/Complete observed callbacks run after their list/counter/event is updated
and before an injected reporter failure.

Use this exact ordering in every modified fake method:

```csharp
public void WriteRun(RunRecord record)
{
    if (RunEntering != null)
        RunEntering(record);
    RunCalls++;
    Add("sink:run");
    if (RunFailure != null)
        throw RunFailure;
    RunRecords.Add(record);
}

public void WriteInitial(InitialRecord record)
{
    if (InitialEntering != null)
        InitialEntering(record);
    InitialCalls++;
    Add("sink:initial");
    if (InitialFailure != null)
        throw InitialFailure;
    InitialRecords.Add(record);
}

public void WriteStep(StepRecord record)
{
    if (StepEntering != null)
        StepEntering(record);
    StepCalls++;
    Add("sink:step:" + record.InputIndex.ToString());
    if (StepFailure != null)
        throw StepFailure;
    StepRecords.Add(record);
    if (StepObserved != null)
        StepObserved(record);
}

public void WriteEnd(EndRecord record)
{
    EndCalls++;
    Add("sink:end");
    if (EndFailure != null)
        throw EndFailure;
    EndRecords.Add(record);
    if (EndObserved != null)
        EndObserved(record);
}

public void WriteError(ErrorRecord record)
{
    if (ErrorEntering != null)
        ErrorEntering(record);
    ErrorCalls++;
    Add("sink:error:" + record.Code);
    if (ErrorFailure != null)
        throw ErrorFailure;
    ErrorRecords.Add(record);
}

public void Ready(int completedInputs)
{
    ReadyValues.Add(completedInputs);
    Add("report:ready:" + completedInputs.ToString() + "/3");
    if (ReadyObserved != null)
        ReadyObserved(completedInputs);
    if (ReadyFailure != null)
        throw ReadyFailure;
}

public void Complete()
{
    CompleteCalls++;
    Add("report:complete");
    if (CompleteObserved != null)
        CompleteObserved();
    if (CompleteFailure != null)
        throw CompleteFailure;
}

public void Diagnostic(string message)
{
    DiagnosticCalls++;
    Diagnostics.Add(message);
    Add("report:diagnostic:" + message);
    if (DiagnosticObserved != null)
        DiagnosticObserved(message);
    if (DiagnosticFailure != null)
        throw DiagnosticFailure;
}
```

Add `BlockingTraceOutput : ITraceOutput` with thread-safe `ByteCount`,
`FlushCalls`, `CloseCalls`, `SnapshotBytes()`, and:

```csharp
internal int ByteCount { get; }
internal int FlushCalls { get; }
internal int CloseCalls { get; }
internal byte[] SnapshotBytes();
internal void BlockNextWrite(
    ManualResetEvent entered,
    ManualResetEvent release);
```

Its write barrier blocks before bytes become durable. Use `lock` only around
fixture-owned fields and never sleep.

`BlockingTraceOutput.Write` consumes an armed barrier under its own lock, waits
outside that lock, then appends bytes under the lock. `Flush` and `Close` mutate
only under that lock:

```csharp
internal sealed class BlockingTraceOutput : ITraceOutput
{
private readonly object sync = new object();
private readonly List<byte> bytes = new List<byte>();
private bool blockNextWrite;
private ManualResetEvent writeEntered;
private ManualResetEvent releaseWrite;
private bool closed;
private int flushCalls;
private int closeCalls;

internal int ByteCount
{
    get { lock (sync) { return bytes.Count; } }
}

internal int FlushCalls
{
    get { lock (sync) { return flushCalls; } }
}

internal int CloseCalls
{
    get { lock (sync) { return closeCalls; } }
}

internal byte[] SnapshotBytes()
{
    lock (sync) { return bytes.ToArray(); }
}

internal void BlockNextWrite(
    ManualResetEvent entered, ManualResetEvent release)
{
    if (entered == null || release == null)
        throw new ArgumentNullException(
            entered == null ? "entered" : "release");
    lock (sync)
    {
        if (blockNextWrite || closed)
            throw new InvalidOperationException("output cannot arm write");
        blockNextWrite = true;
        writeEntered = entered;
        releaseWrite = release;
    }
}

public int Write(byte[] buffer, int offset, int count)
{
    ManualResetEvent entered = null;
    ManualResetEvent release = null;
    lock (sync)
    {
        if (blockNextWrite)
        {
            blockNextWrite = false;
            entered = writeEntered;
            release = releaseWrite;
        }
    }
    if (entered != null)
    {
        entered.Set();
        if (!release.WaitOne(5000))
            throw new TimeoutException("blocked write was not released");
    }
    lock (sync)
    {
        if (closed)
            throw new IOException("write after close");
        for (int index = 0; index < count; index++)
            bytes.Add(buffer[offset + index]);
    }
    return count;
}

public void Flush()
{
    lock (sync)
    {
        if (closed)
            throw new IOException("flush after close");
        flushCalls++;
    }
}

public void Close()
{
    lock (sync)
    {
        closeCalls++;
        if (closed)
            throw new IOException("duplicate close");
        closed = true;
    }
}
}
```

- [ ] **Step 3: Add final-step fixture helpers**

Add `DriverFixture.ReadyWithSink(ITraceSink)`, private `MakeReady`,
`ObserveAtUtc`, `SettleCurrentAtUtc`, `CompleteFirstTwoSteps`, `OpenThirdStep`,
`ObserveThirdCandidate`, `ObserveThirdMatch(DateTime)`,
`CompleteThirdStep(DateTime)`, and `CompleteThreeSteps`.

Use these exact signatures:

```csharp
internal static DriverFixture ReadyWithSink(ITraceSink sink);
private static DriverFixture MakeReady(DriverFixture fixture);
internal FakeUpdateObservation ObserveAtUtc(
    object firstState,
    object secondState,
    double now,
    bool quiescent,
    CaptureRecord capture,
    DateTime utc);
internal void SettleCurrentAtUtc(
    CaptureRecord capture,
    double firstUpdateSeconds,
    DateTime finalUtc);
internal void CompleteFirstTwoSteps();
internal void OpenThirdStep();
internal void ObserveThirdCandidate();
internal void ObserveThirdMatch(DateTime finalUtc);
internal void CompleteThirdStep(DateTime finalUtc);
internal void CompleteThreeSteps();
```

These helpers must drive only real public/internal callbacks; no state
manufacturing seam is allowed.

Refactor the existing `Ready()` construction through these concrete bodies.
The fixture constructor accepts an optional `ITraceSink`; when it is not a
`FakeTraceSink`, the existing `Sink` field is null and tests inspect the supplied
sink/output instead:

```csharp
private DriverFixture(
    int maxFrames, double maxSeconds, ITraceSink selectedSink)
{
    Sink = selectedSink as FakeTraceSink;
    Reporter = new FakePassiveReporter(Events);
    Driver = new PassiveDriver(
        selectedSink, Reporter, OracleProtocol.ExpectedInputCount,
        maxFrames, maxSeconds);
    Boundary = new PassiveUpdateBoundary(Driver);
}

private DriverFixture(int maxFrames, double maxSeconds)
{
    Reporter = new FakePassiveReporter(Events);
    Sink = new FakeTraceSink(Events);
    Driver = new PassiveDriver(
        Sink, Reporter, OracleProtocol.ExpectedInputCount,
        maxFrames, maxSeconds);
    Boundary = new PassiveUpdateBoundary(Driver);
}

internal static DriverFixture ReadyWithSink(ITraceSink sink)
{
    if (sink == null)
        throw new ArgumentNullException("sink");
    return MakeReady(new DriverFixture(600, 30.0, sink));
}

private static DriverFixture MakeReady(DriverFixture fixture)
{
    Check.True(fixture.Driver.Prepare(ProtocolSamples.Run), "prepare");
    Check.True(fixture.Driver.Activate(), "activate");
    fixture.Observe(
        fixture.State, fixture.State, 1.0, true,
        ProtocolSamples.Capture("ready-a"));
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 2.0, true,
        ProtocolSamples.Capture("ready-pair"));
    fixture.Observe(
        fixture.State, fixture.State, 3.0, true,
        ProtocolSamples.Capture("ready-pair"));
    Check.Equal(PassivePhase.Ready, fixture.Driver.Phase, "ready fixture");
    return fixture;
}

internal FakeUpdateObservation ObserveAtUtc(
    object firstState,
    object secondState,
    double now,
    bool quiescent,
    CaptureRecord capture,
    DateTime utc)
{
    FakeUpdateObservation observation = NewObservation(
        firstState, firstState != null,
        secondState, secondState != null,
        now, quiescent, capture);
    observation.Utc = utc;
    Boundary.Observe(observation);
    return observation;
}

internal void SettleCurrentAtUtc(
    CaptureRecord capture, double firstUpdateSeconds, DateTime finalUtc)
{
    Neutral();
    ObserveAtUtc(
        State, State, firstUpdateSeconds, true, capture, finalUtc);
    ObserveAtUtc(
        State, State, firstUpdateSeconds + 1.0, true, capture, finalUtc);
}

internal void CompleteFirstTwoSteps()
{
    OpenDirection(2, true, true, 10.0);
    SettleCurrentAtUtc(ProtocolSamples.MovedCapture, 11.0, UtcFinish);
    OpenDirection(0, false, false, 20.0);
    SettleCurrentAtUtc(ProtocolSamples.MovedCapture, 21.0, UtcFinish);
}

internal void OpenThirdStep()
{
    OpenUndo(true, false, 30.0);
    Neutral();
}

internal void ObserveThirdCandidate()
{
    ObserveAtUtc(
        State, State, 31.0, true,
        ProtocolSamples.InitialCapture, UtcFinish);
}

internal void ObserveThirdMatch(DateTime finalUtc)
{
    ObserveAtUtc(
        State, State, 32.0, true,
        ProtocolSamples.InitialCapture, finalUtc);
}

internal void CompleteThirdStep(DateTime finalUtc)
{
    OpenThirdStep();
    ObserveThirdCandidate();
    ObserveThirdMatch(finalUtc);
}

internal void CompleteThreeSteps()
{
    CompleteFirstTwoSteps();
    CompleteThirdStep(UtcFinish);
}
```

- [ ] **Step 4: Create the six frozen terminal registrations**

Create `PassiveDriverTerminalTests.cs` with this wrapper and place every
terminal registration/test/helper body below inside it:

```csharp
using System;
using System.Collections.Generic;
using System.Threading;

internal static class PassiveDriverTerminalTests
{
    // Task 5 terminal test members.
}
```

```csharp
internal static void Register(TestRegistry tests)
{
    tests.Add("driver-terminal", "three steps End Close Complete order",
        ThreeStepsEndCloseCompleteOrder);
    tests.Add("driver-terminal", "error field policy is exact",
        ErrorFieldPolicyIsExact);
    tests.Add("driver-terminal", "sink failure uses trace io marker",
        SinkFailureUsesTraceIoMarker);
    tests.Add(
        "driver-terminal", "completion reporter cannot rewrite trace",
        CompletionReporterCannotRewriteTrace);
    tests.Add("driver-terminal", "first fault wins race",
        FirstFaultWinsRace);
    tests.Add("driver-terminal", "Dispose and late callbacks are final",
        DisposeAndLateCallbacksAreFinal);
}
```

Cover final UTC validation; `Step 2 -> End -> Close -> Complete`; no Ready(3);
Error precedence; Step/End/Error/Close failures; Complete failure after closed
success bytes; atomic success/fault/dispose ownership; Run/Initial/Ready/Step
output barriers; Dispose during Error/End; and late callback inertia.

Within `FirstFaultWinsRace`, include deterministic subcases
`FaultWaitsForInFlightRun`, `FaultWaitsForInFlightInitial`,
`FaultDuringInitialReadyIsDeferred`, `FaultWaitsForInFlightRealStep`,
`StepFailureOverridesQueuedFault`, `FaultWinsAtIntermediateHandoff`,
`FaultWinsWhileDurableStepIsBlocked`, `FaultDuringReadyIsDeferred`,
`FaultFaultRace`, `SuccessWinsWhileEndIsBlocked`, and
`SuccessWinsWhileCompleteIsBlocked`.

Implement the six registered bodies as explicit aggregators:

```csharp
private static void ThreeStepsEndCloseCompleteOrder()
{
    FinalUtcEqualToStartCompletes();
    FinalUtcBeforeStartFaultsAfterDurableStep();
    InvalidUtcOwnsBeforeErrorDrain();
}

private static void FinalUtcEqualToStartCompletes()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    fixture.CompleteThirdStep(fixture.Driver.StartedAtUtc);
    Check.Equal(3, fixture.Sink.StepRecords.Count, "three Steps");
    Check.Sequence(
        new int[] { 0, 1, 2 }, fixture.Reporter.ReadyValues.ToArray(),
        "no Ready(3)");
    Check.Equal(1, fixture.Sink.EndRecords.Count, "one End");
    Check.Equal(
        fixture.Driver.StartedAtUtc,
        fixture.Sink.EndRecords[0].FinishedAtUtc,
        "equal final UTC retained");
    Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
    Check.Equal(1, fixture.Reporter.CompleteCalls, "one Complete");
    Check.Equal(PassivePhase.Done, fixture.Driver.Phase, "Done");
    Check.Sequence(
        new string[]
        {
            "sink:step:2", "sink:end", "sink:close", "report:complete"
        },
        fixture.Events.GetRange(fixture.Events.Count - 4, 4).ToArray(),
        "terminal order");
}

private static void FinalUtcBeforeStartFaultsAfterDurableStep()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    fixture.CompleteThirdStep(
        fixture.Driver.StartedAtUtc.AddTicks(-1));
    Check.Equal(3, fixture.Sink.StepRecords.Count, "Step 2 durable");
    Check.Equal(0, fixture.Sink.EndRecords.Count, "no End");
    Check.Equal(0, fixture.Reporter.CompleteCalls, "no Complete");
    Check.Sequence(
        new int[] { 0, 1, 2 }, fixture.Reporter.ReadyValues.ToArray(),
        "no Ready(3)");
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "one UTC Error");
    ErrorRecord error = fixture.Sink.ErrorRecords[0];
    Check.Equal("observer_exception", error.Code, "UTC code");
    Check.Equal((int?)null, error.InputIndex, "UTC null index");
    Check.Equal((OracleInput?)null, error.Input, "UTC null input");
    Check.Equal(0, error.SettleFrames, "UTC zero frames");
    Check.True(error.LastCapture == null, "UTC null capture");
}

private static void ErrorFieldPolicyIsExact()
{
    RestartOverridesInputFields();
    PendingAttemptWinsErrorFields();
    MappedAndUnknownOffendersAreExact();
    GenericAndInitialFramesAreExact();
}

private static void SinkFailureUsesTraceIoMarker()
{
    AssertTerminalSinkFailure("step");
    AssertTerminalSinkFailure("end");
    AssertTerminalSinkFailure("error");
    AssertTerminalSinkFailure("close");
    OrdinaryErrorCloseFailureDowngradesMarker();
}

private static void CompletionReporterCannotRewriteTrace()
{
    AssertCompleteFailureAfterClosedBytes();
}

private static void FirstFaultWinsRace()
{
    FaultWaitsForInFlightRun();
    FaultWaitsForInFlightInitial();
    FaultDuringInitialReadyIsDeferred();
    FaultWaitsForInFlightRealStep();
    StepFailureOverridesQueuedFault();
    FaultWinsAtIntermediateHandoff();
    FaultWinsWhileDurableStepIsBlocked();
    FaultDuringReadyIsDeferred();
    FaultDuringDiagnosticIsDeferred();
    FaultFaultRace();
    SuccessWinsWhileEndIsBlocked();
    SuccessWinsWhileCompleteIsBlocked();
}

private static void DisposeAndLateCallbacksAreFinal()
{
    DisposeWaitsForInFlightRun();
    DisposeWaitsForInFlightInitial();
    DisposeWaitsForInFlightStep();
    DisposeDuringErrorLeavesFaultOwner();
    DisposeDuringEndLeavesSuccessOwner();
    MatchingLateStateSetReturnAfterDoneIsInert();
}
```

Every barrier leaf follows the same deterministic body: create `entered` and
`release`; configure the named pre-durability callback or `BlockingTraceOutput`
to set `entered` then require `release.WaitOne(5000)`; start that output on one Thread; require
`entered.WaitOne(5000)`; make the competing terminal claim on the test thread;
assert zero competing Error/End/Close/reporter delta while blocked. A `finally`
block always sets `release` and joins the output thread with a 5000 ms guard,
even if an earlier wait or assertion fails; then assert the exact first-owner suffix.
No barrier leaf may use sleep, use elapsed duration as a behavioral oracle, or
leave a Thread unjoined. A bounded 5000 ms wait/join is only a hang guard.

This is the complete durable-Step transaction; sibling races retain the same
barrier release and exception/join discipline:

```csharp
private static void FaultWinsWhileDurableStepIsBlocked()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Neutral();
    fixture.Observe(fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.MovedCapture);
    Exception stepError = null;
    using (ManualResetEvent entered = new ManualResetEvent(false))
    using (ManualResetEvent release = new ManualResetEvent(false))
    {
        fixture.Sink.StepObserved = delegate(StepRecord record)
        {
            if (record.InputIndex == 0)
            {
                entered.Set();
                if (!release.WaitOne(5000))
                    throw new TimeoutException("Step was not released");
            }
        };
        Thread step = new Thread(delegate()
        {
            try
            {
                fixture.Observe(
                    fixture.State, fixture.State, 12.0, true,
                    ProtocolSamples.MovedCapture);
            }
            catch (Exception error) { stepError = error; }
        });
        bool joined = false;
        try
        {
            step.Start();
            Check.True(entered.WaitOne(5000), "Step barrier entered");
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "fault claims terminal outcome");
            Check.Equal(1, fixture.Sink.StepRecords.Count, "Step durable");
            Check.Equal(0, fixture.Sink.ErrorCalls, "Error waits for Step");
            Check.Equal(0, fixture.Sink.CloseCalls, "Close waits for Step");
            Check.Equal(
                0, fixture.Reporter.FailedCalls,
                "Failed waits for Step");
        }
        finally
        {
            release.Set();
            joined = step.Join(5000);
        }
        Check.True(joined, "Step producer joins");
    }
    Check.True(stepError == null, "Step worker succeeds");
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "one Error");
    ErrorRecord errorRecord = fixture.Sink.ErrorRecords[0];
    Check.Equal("capture_failed", errorRecord.Code, "fault code");
    Check.Equal((int?)null, errorRecord.InputIndex, "rebased index");
    Check.Equal((OracleInput?)null, errorRecord.Input, "rebased input");
    Check.Equal(0, errorRecord.SettleFrames, "rebased frames");
    Check.True(
        errorRecord.LastCapture == null,
        "durable Step clears fault capture");
}
```

The sibling transactions use these closed producer/oracle bindings:

| Subcase | Producer/barrier | Contender | Before release | After release |
|---|---|---|---|---|
| `FaultWaitsForInFlightRun` | Prepare / RunEntering | ordinary fault | no Error/Close/Failed; claim returns | Run durable, Prepare false, Close + `trace_io_failed`; no Error |
| `FaultWaitsForInFlightInitial` | second Initial / InitialEntering | ordinary fault | no Error/Close/Ready | Initial, Error, Close, Failed; no Ready(0) |
| `FaultDuringInitialReadyIsDeferred` | ReadyObserved(0) | ordinary fault | Ready(0), no Error/Close | Error, Close, Failed |
| `FaultWaitsForInFlightRealStep` | blocked NDJSON Step write | ordinary fault | bytes and Close unchanged | Step line, rebased Error line, one Close |
| `StepFailureOverridesQueuedFault` | blocked Step throws after release | ordinary fault | no Error/Close/Failed | no Error; one Close; only `trace_io_failed` |
| `FaultWinsAtIntermediateHandoff` | StepObserved before continuation | ordinary fault | durable Step; no Ready/Error/Close | rebased Error, Close, Failed; no Ready |
| `FaultDuringReadyIsDeferred` | ReadyObserved(1) | ordinary fault | Ready(1), no Error/Close | Error, Close, Failed |
| `FaultDuringDiagnosticIsDeferred` | DiagnosticObserved after Ready(1) throws | ordinary fault | Diagnostic visible, no Error/Close/Failed | contender Error, Close, Failed after Diagnostic returns |
| `SuccessWinsWhileEndIsBlocked` | third Step / EndObserved | ordinary fault | End durable; contender false; no Close/Complete | Close, Complete, Done; no Error |
| `SuccessWinsWhileCompleteIsBlocked` | third Step / CompleteObserved | ordinary fault | End/Close done; contender false | Complete returns, Done; no Error/Failed |
| Dispose during Error or End | ErrorEntering or EndObserved | Dispose | Dispose returns; owner unchanged | original owner finishes; one Close |

`FaultFaultRace` releases two fault Threads from one gate, joins both, requires
exactly one true return, one Error, one Close, and a Failed code equal to the
winning Error code.

`InvalidUtcOwnsBeforeErrorDrain` completes Step 2 with an earlier UTC while
`ErrorEntering` blocks behind a bounded barrier. Once that callback enters,
invoke a second ordinary fault and Dispose; require both to lose/leave the
Fault owner unchanged and require no Close/Failed yet. Always release and join
in `finally`, then assert durable Step 2 followed only by the null-field
`observer_exception`, Close, and Failed. This proves invalid-UTC fault selection
occurred atomically before the Step lease released into Error drain.

```csharp
private static void InvalidUtcOwnsBeforeErrorDrain()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    Exception workerError = null;
    using (ManualResetEvent entered = new ManualResetEvent(false))
    using (ManualResetEvent release = new ManualResetEvent(false))
    {
        fixture.Sink.ErrorEntering = delegate(ErrorRecord record)
        {
            entered.Set();
            if (!release.WaitOne(5000))
                throw new TimeoutException("UTC Error was not released");
        };
        Thread worker = new Thread(delegate()
        {
            try
            {
                fixture.CompleteThirdStep(
                    fixture.Driver.StartedAtUtc.AddTicks(-1));
            }
            catch (Exception error) { workerError = error; }
        });
        bool joined = false;
        try
        {
            worker.Start();
            Check.True(entered.WaitOne(5000), "UTC Error drain entered");
            Check.False(
                fixture.Driver.TryFault("capture_failed"),
                "UTC fault already owns terminal result");
            fixture.Driver.Dispose();
            Check.Equal(0, fixture.Sink.CloseCalls, "Close still blocked");
            Check.Equal(0, fixture.Reporter.FailedCalls, "Failed still blocked");
        }
        finally
        {
            release.Set();
            joined = worker.Join(5000);
        }
        Check.True(joined, "UTC worker joins");
    }
    Check.True(workerError == null, "UTC worker succeeds");
    Check.Equal(3, fixture.Sink.StepRecords.Count, "UTC Step 2 durable");
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "UTC one Error");
    Check.Equal(1, fixture.Sink.CloseCalls, "UTC one Close");
    Check.Sequence(
        new string[] { "observer_exception" },
        fixture.Reporter.FailedCodes.ToArray(),
        "UTC one Failed marker");
}
```

Define the Error-policy and failure leaves plus their shared oracle:

```csharp
private static void RestartOverridesInputFields()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Observe(
        fixture.State, fixture.State, 11.0, false,
        ProtocolSamples.MovedCapture);
    HookToken restart = fixture.Driver.RestartEntered();
    AssertOnlyError(
        fixture, "unexpected_input", null, null, 1,
        "Restart override");
    fixture.Driver.RestartReturned(restart);
}

private static void PendingAttemptWinsErrorFields()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.MovedCapture);
    HookToken stateSet = fixture.Driver.StateSetEntered(
        fixture.State, fixture.OtherState);
    fixture.Driver.StateSetReturned(
        stateSet, fixture.OtherState, 12.0);
    ErrorRecord error = AssertOnlyError(
        fixture, "state_replaced", 0, OracleInput.West, 1,
        "pending attempt");
    Check.Same(
        ProtocolSamples.MovedCapture, error.LastCapture,
        "pending capture retained");
}

private static void MappedAndUnknownOffendersAreExact()
{
    DriverFixture mapped = DriverFixture.Active();
    HookToken mappedPoll = mapped.Driver.PlayerPollEntered();
    mapped.Driver.PhysicalPollReturned(2);
    HookToken mappedInput = mapped.Driver.ProcessInputEntered(
        mapped.State, 2, 1.0);
    AssertOnlyError(
        mapped, "input_before_initial", 0, OracleInput.West, 0,
        "mapped offender");
    mapped.Driver.ProcessInputThrew(mappedInput);
    mapped.Driver.PlayerPollThrew(mappedPoll);

    DriverFixture unknown = DriverFixture.Ready();
    HookToken unknownPoll = unknown.Driver.PlayerPollEntered();
    unknown.Driver.PhysicalPollReturned(99);
    AssertOnlyError(
        unknown, "unexpected_input", 0, null, 0,
        "unknown offender");
    unknown.Driver.PlayerPollThrew(unknownPoll);
}

private static void GenericAndInitialFramesAreExact()
{
    DriverFixture generic = DriverFixture.Active();
    Check.True(
        generic.Driver.TryFault("capture_failed"),
        "generic fault claims");
    AssertOnlyError(
        generic, "capture_failed", null, null, 0,
        "generic fields");

    DriverFixture initial = DriverFixture.Active();
    initial.Observe(
        initial.State, initial.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    Check.True(
        initial.Driver.TryFault("capture_failed"),
        "Initial fault claims");
    AssertOnlyError(
        initial, "capture_failed", null, null, 1,
        "Initial fields");
}

private static ErrorRecord AssertOnlyError(
    DriverFixture fixture,
    string code,
    int? inputIndex,
    OracleInput? input,
    int settleFrames,
    string label)
{
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, label + " one Error");
    ErrorRecord error = fixture.Sink.ErrorRecords[0];
    Check.Equal(code, error.Code, label + " code");
    Check.Equal(inputIndex, error.InputIndex, label + " index");
    Check.Equal(input, error.Input, label + " input");
    Check.Equal(settleFrames, error.SettleFrames, label + " frames");
    Check.Equal(0, fixture.Sink.EndRecords.Count, label + " no End");
    Check.Equal(1, fixture.Sink.CloseCalls, label + " one Close");
    Check.Sequence(
        new string[] { code }, fixture.Reporter.FailedCodes.ToArray(),
        label + " Failed marker");
    return error;
}

private static void AssertTerminalSinkFailure(string point)
{
    DriverFixture fixture = DriverFixture.Ready();
    if (point == "step")
    {
        fixture.CompleteFirstTwoSteps();
        fixture.OpenThirdStep();
        fixture.ObserveThirdCandidate();
        fixture.Sink.StepFailure = new TraceIoException("Step failure");
        fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
    }
    else if (point == "end")
    {
        fixture.CompleteFirstTwoSteps();
        fixture.Sink.EndFailure = new TraceIoException("End failure");
        fixture.CompleteThirdStep(DriverFixture.UtcFinish);
    }
    else if (point == "error")
    {
        fixture.Sink.ErrorFailure = new TraceIoException("Error failure");
        Check.True(
            fixture.Driver.TryFault("capture_failed"),
            "Error failure claims");
    }
    else if (point == "close")
    {
        fixture.CompleteFirstTwoSteps();
        fixture.Sink.CloseFailure = new TraceIoException("Close failure");
        fixture.CompleteThirdStep(DriverFixture.UtcFinish);
    }
    else
        throw new ArgumentOutOfRangeException("point");

    Check.Equal(1, fixture.Sink.CloseCalls, point + " Close once");
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, point + " no Error");
    Check.Equal(
        point == "close" ? 1 : 0,
        fixture.Sink.EndRecords.Count,
        point + " authenticated End count");
    Check.Equal(0, fixture.Reporter.CompleteCalls, point + " no Complete");
    Check.Sequence(
        new string[] { "trace_io_failed" },
        fixture.Reporter.FailedCodes.ToArray(),
        point + " trace-I/O marker");
}

private static void OrdinaryErrorCloseFailureDowngradesMarker()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.Sink.CloseFailure = new TraceIoException("fault Close failure");
    Check.True(
        fixture.Driver.TryFault("capture_failed"),
        "ordinary fault claims before Close failure");
    Check.Equal(1, fixture.Sink.ErrorCalls, "ordinary Error attempted once");
    Check.Equal(
        1, fixture.Sink.ErrorRecords.Count,
        "ordinary Error is durable before Close failure");
    Check.Equal(1, fixture.Sink.CloseCalls, "fault Close attempted once");
    Check.Equal(0, fixture.Sink.EndRecords.Count, "fault Close no End");
    Check.Equal(0, fixture.Reporter.CompleteCalls, "fault Close no Complete");
    Check.Sequence(
        new string[] { "trace_io_failed" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Close failure downgrades authoritative marker");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "fault Close failure remains Faulted");
}

private static void AssertCompleteFailureAfterClosedBytes()
{
    BlockingTraceOutput output = new BlockingTraceOutput();
    DriverFixture fixture = DriverFixture.ReadyWithSink(
        new NdjsonTraceSink(output));
    fixture.CompleteFirstTwoSteps();
    byte[] bytesAtComplete = null;
    fixture.Reporter.CompleteObserved = delegate
    {
        bytesAtComplete = output.SnapshotBytes();
    };
    fixture.Reporter.CompleteFailure =
        new InvalidOperationException("Complete failure");
    fixture.CompleteThirdStep(DriverFixture.UtcFinish);

    Check.True(bytesAtComplete != null, "Complete observed");
    Check.Bytes(
        bytesAtComplete, output.SnapshotBytes(),
        "Complete failure cannot rewrite bytes");
    Check.Equal(1, output.CloseCalls, "Complete failure no reclose");
    Check.Equal(1, fixture.Reporter.CompleteCalls, "Complete once");
    Check.Sequence(
        new string[] { "observer_exception" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Complete failure marker");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "Complete failure phase");
}
```

Use one shared deterministic runner and define every fault/success race leaf:

```csharp
private static void RunBlockedProducer(
    string label,
    Action<ManualResetEvent, ManualResetEvent> arm,
    Action producer,
    Action whileBlocked,
    Action afterRelease)
{
    Exception producerError = null;
    Exception assertionError = null;
    bool joined = false;
    using (ManualResetEvent entered = new ManualResetEvent(false))
    using (ManualResetEvent release = new ManualResetEvent(false))
    {
        arm(entered, release);
        Thread worker = new Thread(delegate
        {
            try { producer(); }
            catch (Exception error) { producerError = error; }
        });
        try
        {
            worker.Start();
            Check.True(entered.WaitOne(5000), label + " entered");
            whileBlocked();
        }
        catch (Exception error) { assertionError = error; }
        finally
        {
            release.Set();
            joined = worker.Join(5000);
        }
    }
    Check.True(joined, label + " producer joined");
    if (assertionError != null)
        throw new InvalidOperationException(
            label + " blocked oracle failed", assertionError);
    if (producerError != null)
        throw new InvalidOperationException(
            label + " producer failed", producerError);
    afterRelease();
}

private static void EnterBarrier(
    ManualResetEvent entered,
    ManualResetEvent release,
    string label)
{
    entered.Set();
    if (!release.WaitOne(5000))
        throw new TimeoutException(label + " was not released");
}

private static void PrepareInitialMatch(DriverFixture fixture)
{
    fixture.Observe(
        fixture.State, fixture.State, 1.0, false,
        ProtocolSamples.InitialCapture);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 2.0, true,
        ProtocolSamples.InitialCapture);
}

private static void FinishInitialMatch(DriverFixture fixture)
{
    fixture.Observe(
        fixture.State, fixture.State, 3.0, true,
        ProtocolSamples.InitialCapture);
}

private static void PrepareFirstStepMatch(DriverFixture fixture)
{
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Neutral();
    fixture.Observe(
        fixture.State, fixture.State, 11.0, true,
        ProtocolSamples.MovedCapture);
}

private static void FinishFirstStepMatch(DriverFixture fixture)
{
    fixture.Observe(
        fixture.State, fixture.State, 12.0, true,
        ProtocolSamples.MovedCapture);
}

private static void AssertTraceIoOnly(
    DriverFixture fixture, string label)
{
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, label + " no Error");
    Check.Equal(0, fixture.Sink.EndRecords.Count, label + " no End");
    Check.Equal(1, fixture.Sink.CloseCalls, label + " one Close");
    Check.Sequence(
        new string[] { "trace_io_failed" },
        fixture.Reporter.FailedCodes.ToArray(),
        label + " trace-I/O marker");
}

private static void FaultWaitsForInFlightRun()
{
    DriverFixture fixture = DriverFixture.Unprepared();
    bool prepared = true;
    RunBlockedProducer(
        "Run/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.RunEntering = delegate(RunRecord record)
            {
                EnterBarrier(entered, release, "Run");
            };
        },
        delegate { prepared = fixture.Driver.Prepare(ProtocolSamples.Run); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "Run contender claims");
            Check.Equal(0, fixture.Sink.ErrorCalls, "Run Error waits");
            Check.Equal(0, fixture.Sink.CloseCalls, "Run Close waits");
            Check.Equal(0, fixture.Reporter.FailedCalls, "Run Failed waits");
        },
        delegate
        {
            Check.False(prepared, "faulted Prepare false");
            Check.Equal(1, fixture.Sink.RunRecords.Count, "Run durable");
            Check.False(fixture.Driver.Activate(), "faulted Run inert");
            AssertTraceIoOnly(fixture, "Run/fault");
        });
}

private static void FaultWaitsForInFlightInitial()
{
    DriverFixture fixture = DriverFixture.Active();
    PrepareInitialMatch(fixture);
    RunBlockedProducer(
        "Initial/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.InitialEntering = delegate(InitialRecord record)
            {
                EnterBarrier(entered, release, "Initial");
            };
        },
        delegate { FinishInitialMatch(fixture); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "Initial contender claims");
            Check.Equal(0, fixture.Sink.ErrorCalls, "Initial Error waits");
            Check.Equal(0, fixture.Sink.CloseCalls, "Initial Close waits");
            Check.Sequence(
                new int[0], fixture.Reporter.ReadyValues.ToArray(),
                "Initial Ready waits");
        },
        delegate
        {
            Check.Equal(1, fixture.Sink.InitialRecords.Count, "Initial durable");
            AssertOnlyError(
                fixture, "capture_failed", null, null, 3,
                "Initial deferred fault");
            Check.Sequence(
                new int[0], fixture.Reporter.ReadyValues.ToArray(),
                "Initial no Ready");
        });
}

private static void FaultDuringInitialReadyIsDeferred()
{
    DriverFixture fixture = DriverFixture.Active();
    RunBlockedProducer(
        "Initial Ready/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Reporter.ReadyObserved = delegate(int value)
            {
                if (value == 0)
                    EnterBarrier(entered, release, "Ready(0)");
            };
        },
        delegate
        {
            PrepareInitialMatch(fixture);
            FinishInitialMatch(fixture);
        },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "Ready(0) contender claims");
            Check.Sequence(
                new int[] { 0 }, fixture.Reporter.ReadyValues.ToArray(),
                "Ready(0) visible");
            Check.Equal(0, fixture.Sink.ErrorCalls, "Ready Error waits");
            Check.Equal(0, fixture.Sink.CloseCalls, "Ready Close waits");
        },
        delegate
        {
            AssertOnlyError(
                fixture, "capture_failed", null, null, 0,
                "Ready(0) deferred fault");
        });
}

private static void FaultWaitsForInFlightRealStep()
{
    BlockingTraceOutput output = new BlockingTraceOutput();
    DriverFixture fixture = DriverFixture.ReadyWithSink(
        new NdjsonTraceSink(output));
    fixture.CompleteFirstTwoSteps();
    fixture.OpenThirdStep();
    fixture.ObserveThirdCandidate();
    int bytesBefore = output.ByteCount;
    RunBlockedProducer(
        "real Step/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            output.BlockNextWrite(entered, release);
        },
        delegate { fixture.ObserveThirdMatch(DriverFixture.UtcFinish); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("observer_exception"),
                "real Step contender claims");
            Check.Equal(bytesBefore, output.ByteCount, "Step bytes wait");
            Check.Equal(0, output.CloseCalls, "Step Close waits");
            Check.Equal(0, fixture.Reporter.FailedCalls, "Step Failed waits");
        },
        delegate
        {
            Check.Equal(1, output.CloseCalls, "real Step one Close");
            Check.Sequence(
                new string[] { "observer_exception" },
                fixture.Reporter.FailedCodes.ToArray(),
                "real Step marker");
            AssertRebasedStepErrorTail(
                output.SnapshotBytes(), "observer_exception");
        });
}

private static void StepFailureOverridesQueuedFault()
{
    DriverFixture fixture = DriverFixture.Ready();
    PrepareFirstStepMatch(fixture);
    fixture.Sink.StepFailure = new TraceIoException("Step failure");
    RunBlockedProducer(
        "Step failure/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.StepEntering = delegate(StepRecord record)
            {
                EnterBarrier(entered, release, "failing Step");
            };
        },
        delegate { FinishFirstStepMatch(fixture); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "ordinary fault queues");
            Check.Equal(0, fixture.Sink.ErrorCalls, "queued Error waits");
            Check.Equal(0, fixture.Sink.CloseCalls, "queued Close waits");
        },
        delegate
        {
            Check.Equal(0, fixture.Sink.StepRecords.Count, "Step not durable");
            AssertTraceIoOnly(fixture, "Step failure override");
        });
}

private static void FaultWinsAtIntermediateHandoff()
{
    DriverFixture fixture = DriverFixture.Ready();
    PrepareFirstStepMatch(fixture);
    RunBlockedProducer(
        "Step handoff/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.StepObserved = delegate(StepRecord record)
            {
                EnterBarrier(entered, release, "Step handoff");
            };
        },
        delegate { FinishFirstStepMatch(fixture); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "handoff fault claims");
            Check.Equal(1, fixture.Sink.StepRecords.Count, "Step durable");
            Check.Equal(0, fixture.Sink.ErrorCalls, "handoff Error waits");
            Check.Sequence(
                new int[] { 0 }, fixture.Reporter.ReadyValues.ToArray(),
                "handoff no Ready(1)");
        },
        delegate
        {
            AssertOnlyError(
                fixture, "capture_failed", null, null, 0,
                "handoff rebased fault");
        });
}

private static void FaultDuringReadyIsDeferred()
{
    DriverFixture fixture = DriverFixture.Ready();
    PrepareFirstStepMatch(fixture);
    RunBlockedProducer(
        "Ready(1)/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Reporter.ReadyObserved = delegate(int value)
            {
                if (value == 1)
                    EnterBarrier(entered, release, "Ready(1)");
            };
        },
        delegate { FinishFirstStepMatch(fixture); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "Ready(1) contender claims");
            Check.Sequence(
                new int[] { 0, 1 }, fixture.Reporter.ReadyValues.ToArray(),
                "Ready(1) visible");
            Check.Equal(0, fixture.Sink.ErrorCalls, "Ready Error waits");
            Check.Equal(0, fixture.Sink.CloseCalls, "Ready Close waits");
        },
        delegate
        {
            AssertOnlyError(
                fixture, "capture_failed", null, null, 0,
                "Ready(1) deferred fault");
        });
}

private static void FaultDuringDiagnosticIsDeferred()
{
    DriverFixture fixture = DriverFixture.Ready();
    PrepareFirstStepMatch(fixture);
    fixture.Reporter.ReadyFailure =
        new InvalidOperationException("Ready(1) failure");
    RunBlockedProducer(
        "Diagnostic/fault",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Reporter.DiagnosticObserved = delegate(string message)
            {
                EnterBarrier(entered, release, "Diagnostic");
            };
        },
        delegate { FinishFirstStepMatch(fixture); },
        delegate
        {
            Check.True(
                fixture.Driver.TryFault("capture_failed"),
                "Diagnostic contender claims");
            Check.Equal(
                1, fixture.Reporter.DiagnosticCalls,
                "Diagnostic is visible before terminal drain");
            Check.Equal(0, fixture.Sink.ErrorCalls, "Diagnostic Error waits");
            Check.Equal(0, fixture.Sink.CloseCalls, "Diagnostic Close waits");
            Check.Equal(
                0, fixture.Reporter.FailedCalls,
                "Diagnostic Failed waits");
        },
        delegate
        {
            AssertOnlyError(
                fixture, "capture_failed", null, null, 0,
                "Diagnostic deferred fault");
        });
}
```

Define the remaining race, Dispose, late-Done, and NDJSON helpers:

```csharp
private static void FaultFaultRace()
{
    DriverFixture fixture = DriverFixture.Ready();
    bool firstWon = false;
    bool secondWon = false;
    Exception firstError = null;
    Exception secondError = null;
    using (ManualResetEvent gate = new ManualResetEvent(false))
    {
        Thread first = new Thread(delegate
        {
            try
            {
                if (!gate.WaitOne(5000))
                    throw new TimeoutException("fault gate one");
                firstWon = fixture.Driver.TryFault("capture_failed");
            }
            catch (Exception error) { firstError = error; }
        });
        Thread second = new Thread(delegate
        {
            try
            {
                if (!gate.WaitOne(5000))
                    throw new TimeoutException("fault gate two");
                secondWon = fixture.Driver.TryFault("observer_exception");
            }
            catch (Exception error) { secondError = error; }
        });
        bool firstJoined = false;
        bool secondJoined = false;
        try
        {
            first.Start();
            second.Start();
            gate.Set();
        }
        finally
        {
            gate.Set();
            firstJoined = first.Join(5000);
            secondJoined = second.Join(5000);
        }
        Check.True(firstJoined, "first fault joins");
        Check.True(secondJoined, "second fault joins");
    }
    Check.True(firstError == null, "first fault succeeds");
    Check.True(secondError == null, "second fault succeeds");
    Check.True(firstWon != secondWon, "exactly one fault wins");
    Check.Equal(1, fixture.Sink.ErrorRecords.Count, "race one Error");
    Check.Equal(1, fixture.Sink.CloseCalls, "race one Close");
    Check.Equal(1, fixture.Reporter.FailedCodes.Count, "race one Failed");
    Check.Equal(
        fixture.Sink.ErrorRecords[0].Code,
        fixture.Reporter.FailedCodes[0],
        "race marker follows winner");
}

private static void SuccessWinsWhileEndIsBlocked()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    RunBlockedProducer(
        "End/success",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.EndObserved = delegate(EndRecord record)
            {
                EnterBarrier(entered, release, "End");
            };
        },
        delegate { fixture.CompleteThirdStep(DriverFixture.UtcFinish); },
        delegate
        {
            Check.False(
                fixture.Driver.TryFault("capture_failed"),
                "success owns at End");
            Check.Equal(1, fixture.Sink.EndRecords.Count, "End durable");
            Check.Equal(0, fixture.Sink.CloseCalls, "End Close waits");
            Check.Equal(0, fixture.Reporter.CompleteCalls, "Complete waits");
        },
        delegate
        {
            Check.Equal(1, fixture.Sink.CloseCalls, "End one Close");
            Check.Equal(1, fixture.Reporter.CompleteCalls, "one Complete");
            Check.Equal(0, fixture.Sink.ErrorRecords.Count, "End no Error");
            Check.Equal(0, fixture.Reporter.FailedCalls, "End no Failed");
            Check.Equal(PassivePhase.Done, fixture.Driver.Phase, "Done");
        });
}

private static void SuccessWinsWhileCompleteIsBlocked()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    RunBlockedProducer(
        "Complete/success",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Reporter.CompleteObserved = delegate
            {
                EnterBarrier(entered, release, "Complete");
            };
        },
        delegate { fixture.CompleteThirdStep(DriverFixture.UtcFinish); },
        delegate
        {
            Check.False(
                fixture.Driver.TryFault("capture_failed"),
                "success owns at Complete");
            Check.Equal(1, fixture.Sink.EndRecords.Count, "End durable");
            Check.Equal(1, fixture.Sink.CloseCalls, "Close durable");
            Check.Equal(1, fixture.Reporter.CompleteCalls, "Complete entered");
            Check.Equal(0, fixture.Sink.ErrorRecords.Count, "no Error");
        },
        delegate
        {
            Check.Equal(PassivePhase.Done, fixture.Driver.Phase, "Done");
            Check.Equal(0, fixture.Reporter.FailedCalls, "no Failed");
        });
}

private static void DisposeWaitsForInFlightRun()
{
    DriverFixture fixture = DriverFixture.Unprepared();
    bool prepared = true;
    RunBlockedProducer(
        "Run/Dispose",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.RunEntering = delegate(RunRecord record)
            {
                EnterBarrier(entered, release, "Run Dispose");
            };
        },
        delegate { prepared = fixture.Driver.Prepare(ProtocolSamples.Run); },
        delegate
        {
            fixture.Driver.Dispose();
            Check.Equal(0, fixture.Sink.CloseCalls, "Dispose Close waits");
        },
        delegate
        {
            Check.False(prepared, "disposed Prepare false");
            Check.Equal(1, fixture.Sink.RunRecords.Count, "Run durable");
            Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
            Check.Equal(0, fixture.Reporter.FailedCalls, "no Failed");
        });
}

private static void DisposeWaitsForInFlightInitial()
{
    DriverFixture fixture = DriverFixture.Active();
    PrepareInitialMatch(fixture);
    RunBlockedProducer(
        "Initial/Dispose",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.InitialEntering = delegate(InitialRecord record)
            {
                EnterBarrier(entered, release, "Initial Dispose");
            };
        },
        delegate { FinishInitialMatch(fixture); },
        delegate
        {
            fixture.Driver.Dispose();
            Check.Equal(0, fixture.Sink.CloseCalls, "Dispose Close waits");
        },
        delegate
        {
            Check.Equal(1, fixture.Sink.InitialRecords.Count, "Initial durable");
            Check.Sequence(
                new int[0], fixture.Reporter.ReadyValues.ToArray(),
                "no Ready");
            Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
            Check.Equal(0, fixture.Reporter.FailedCalls, "no Failed");
        });
}

private static void DisposeWaitsForInFlightStep()
{
    DriverFixture fixture = DriverFixture.Ready();
    PrepareFirstStepMatch(fixture);
    RunBlockedProducer(
        "Step/Dispose",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.StepObserved = delegate(StepRecord record)
            {
                EnterBarrier(entered, release, "Step Dispose");
            };
        },
        delegate { FinishFirstStepMatch(fixture); },
        delegate
        {
            fixture.Driver.Dispose();
            Check.Equal(1, fixture.Sink.StepRecords.Count, "Step durable");
            Check.Equal(0, fixture.Sink.CloseCalls, "Close waits");
        },
        delegate
        {
            Check.Sequence(
                new int[] { 0 }, fixture.Reporter.ReadyValues.ToArray(),
                "no Ready(1)");
            Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
            Check.Equal(0, fixture.Reporter.FailedCalls, "no Failed");
        });
}

private static void DisposeDuringErrorLeavesFaultOwner()
{
    DriverFixture fixture = DriverFixture.Ready();
    bool claimed = false;
    RunBlockedProducer(
        "Error/Dispose",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.ErrorEntering = delegate(ErrorRecord record)
            {
                EnterBarrier(entered, release, "Error Dispose");
            };
        },
        delegate { claimed = fixture.Driver.TryFault("capture_failed"); },
        delegate
        {
            fixture.Driver.Dispose();
            Check.Equal(0, fixture.Sink.CloseCalls, "Close waits");
            Check.Equal(0, fixture.Reporter.FailedCalls, "Failed waits");
        },
        delegate
        {
            Check.True(claimed, "fault owner claimed");
            AssertOnlyError(
                fixture, "capture_failed", null, null, 0,
                "Error survives Dispose");
        });
}

private static void DisposeDuringEndLeavesSuccessOwner()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    RunBlockedProducer(
        "End/Dispose",
        delegate(ManualResetEvent entered, ManualResetEvent release)
        {
            fixture.Sink.EndObserved = delegate(EndRecord record)
            {
                EnterBarrier(entered, release, "End Dispose");
            };
        },
        delegate { fixture.CompleteThirdStep(DriverFixture.UtcFinish); },
        delegate
        {
            fixture.Driver.Dispose();
            Check.Equal(1, fixture.Sink.EndRecords.Count, "End durable");
            Check.Equal(0, fixture.Sink.CloseCalls, "Close waits");
        },
        delegate
        {
            Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
            Check.Equal(1, fixture.Reporter.CompleteCalls, "Complete retained");
            Check.Equal(0, fixture.Sink.ErrorRecords.Count, "no Error");
            Check.Equal(0, fixture.Reporter.FailedCalls, "no Failed");
            Check.Equal(PassivePhase.Done, fixture.Driver.Phase, "Done");
        });
}

private static void MatchingLateStateSetReturnAfterDoneIsInert()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.CompleteFirstTwoSteps();
    HookToken stateSet = fixture.Driver.StateSetEntered(
        fixture.State, fixture.OtherState);
    fixture.CompleteThirdStep(DriverFixture.UtcFinish);
    List<string> before = new List<string>(fixture.Events);
    fixture.Driver.StateSetReturned(stateSet, fixture.State, 40.0);
    fixture.Driver.ClearThrew(stateSet);
    Check.Sequence(before, fixture.Events, "late StateSet inert");
    Check.Equal(1, fixture.Sink.CloseCalls, "no reclose");
    Check.Equal(1, fixture.Reporter.CompleteCalls, "no recomplete");
}

private static void AssertRebasedStepErrorTail(
    byte[] traceBytes, string code)
{
    List<byte[]> lines = NonemptyTraceLines(traceBytes);
    Check.True(lines.Count >= 2, "trace Step/Error tail");
    StepRecord expectedStep = new StepRecord(
        ProtocolSamples.Run.RunId, 2, OracleInput.Undo,
        true, false, 2, false, ProtocolSamples.InitialCapture);
    ErrorRecord expectedError = new ErrorRecord(
        ProtocolSamples.Run.RunId, null, null, code, 0, null);
    Check.Bytes(
        CanonicalJson.EncodeStep(expectedStep),
        lines[lines.Count - 2],
        "real Step line");
    Check.Bytes(
        CanonicalJson.EncodeError(expectedError),
        lines[lines.Count - 1],
        "rebased Error line");
}

private static List<byte[]> NonemptyTraceLines(byte[] bytes)
{
    if (bytes == null)
        throw new ArgumentNullException("bytes");
    List<byte[]> lines = new List<byte[]>();
    int start = 0;
    for (int index = 0; index < bytes.Length; index++)
    {
        if (bytes[index] != (byte)'\n')
            continue;
        if (index > start)
        {
            byte[] line = new byte[index - start];
            Buffer.BlockCopy(bytes, start, line, 0, line.Length);
            lines.Add(line);
        }
        start = index + 1;
    }
    Check.Equal(bytes.Length, start, "trace ends with LF");
    return lines;
}
```

Use `BlockingTraceOutput -> NdjsonTraceSink -> DriverFixture.ReadyWithSink` to
prove a durable Step line precedes a deferred ordinary Error line with null
index/input, zero frames, and null last capture.

The six registered tests use these primary oracles:

| Registered test | Required oracle |
|---|---|
| three steps End Close Complete order | Exactly three Steps indexed 0–2; Ready values `0,1,2`; final events `sink:step:2`, `sink:end`, `sink:close`, `report:complete`; final phase Done; final UTC equal to `StartedAtUtc` is accepted and retained in End |
| error field policy is exact | Restart null override; pending attempt precedence; mapped offending input; unknown input with null schema input; generic and Initial frame rules |
| sink failure uses trace io marker | Step 2, End, Error, and Close failures each Close at most once, report only `trace_io_failed`, and never append an unauthenticated Error/End continuation |
| completion reporter cannot rewrite trace | Complete exception occurs after End/Close, leaves trace bytes unchanged, sets phase Faulted, calls Failed(observer_exception) once, and does not reclose |
| first fault wins race | Exactly one terminal owner; all terminal records/Close/markers wait for active Run/Initial/Ready/Step output; real durable Step precedes rebased Error |
| Dispose and late callbacks are final | Dispose/Error/End races retain the first owner, Close at most once, and all future observations are output-inert while exact owned cleanup remains legal |

For a final UTC earlier than `StartedAtUtc`, require Step 2 to remain durable,
then ordinary `observer_exception` with null index/input, zero frames, and null
last capture, followed by Close and Failed. Require no End, Complete, or
Ready(3).

In `DisposeAndLateCallbacksAreFinal`, enter a real StateSet bookkeeping context
before the final successful Step, reach Done without returning that context,
then return or clear its matching token after Done. Require exact owned cleanup
and no additional sink or reporter event. This is the deferred reachable Done
oracle for Task 5.2's already-implemented inert branch; do not add a state seam.

For the real NDJSON rebase leaf, block the low-level Step write, wait for entry,
call `Driver.TryFault("observer_exception")`, release and join, split
`SnapshotBytes()` on LF, and deserialize/inspect the last two nonempty lines.
Assert line one is the real Step with index 2 and line two is Error with the
same code but null index/input, zero frames, and null capture; assert Error then
Close/Failed is the only terminal continuation.

- [ ] **Step 5: Add the driver aggregator and final manifest**

Create:

```csharp
internal static class PassiveDriverTests
{
    internal static void Register(TestRegistry tests)
    {
        PassiveDriverBoundaryTests.Register(tests);
        PassiveDriverInitialTests.Register(tests);
        PassiveDriverInputTests.Register(tests);
        PassiveDriverTerminalTests.Register(tests);
    }
}
```

Replace the three direct driver registration calls in `Program.cs` with
`PassiveDriverTests.Register(tests)` and add `{ "driver-terminal", 6 }` after
`{ "driver-input", 8 }`.

- [ ] **Step 6: Run the first behavioral RED**

Run the forced net10 build, then the no-build `driver-terminal` cohort.

Expected: build succeeds; cohort exits 1 at `three steps End Close Complete
order` because the Task 5.2 driver emits durable Step 2, returns Ready, and has
no End/Close/Complete continuation.

### Task 6: Task 5.3 Production — One Serialized Terminal Slice

**Files:**
- Modify: `oracle/plugin/Core/PassiveDriver.cs`
- Modify: `oracle/plugin/Core/PassiveDriverInput.cs`
- Create: `oracle/plugin/Core/PassiveDriverCompletion.cs`
- Test: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Test: `oracle/plugin/tests/PassiveDriverTerminalTests.cs`
- Test: `oracle/plugin/tests/PassiveDriverTestSupport.cs`
- Test: `oracle/plugin/tests/PassiveDriverTests.cs`
- Test: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes: all final terminal tests and immutable Task 5.2 behavior.
- Produces: logical output lease, shared terminal owner, final completion, and
  deferred ordinary-fault rebase in the third approved implementation commit.

- [ ] **Step 1: Add basic expected-count completion**

Store the constructor-validated count and define the initial terminal constants
in `PassiveDriver.cs`:

```csharp
private const int NoTerminalOwner = 0;
private const int SuccessTerminalOwner = 2;
private readonly int expectedInputCount;
```

After validating the constructor argument and before the constructor returns,
assign:

```csharp
this.expectedInputCount = expectedInputCount;
```

Thread `utcNow` through
`CompleteUpdateCore(UpdateDirective, GateSample, DateTime)` into
`EmitSettledAttempt(CaptureRecord, int, DateTime)`.

At the basic checkpoint, make these exact signature/call replacements:

```csharp
CompleteUpdateCore(directive, sample, utcNow);

private void CompleteUpdateCore(
    UpdateDirective directive, GateSample sample, DateTime utcNow)

EmitSettledAttempt(sample.Capture, directive.SettleFrames, utcNow);
```

Replace the Task 5.1 two-argument Step method with this complete temporary
three-argument body. Task 6 Step 3 later replaces it with the leased body:

```csharp
private void EmitSettledAttempt(
    CaptureRecord capture, int settleFrames, DateTime utcNow)
{
    if (!attemptPending || !attemptOutcomeKnown)
        throw new InvalidOperationException("settled attempt lacks outcome");
    sink.WriteStep(new StepRecord(
        runId, completedInputs, attemptInput, attemptAccepted,
        attemptMovementScheduled, settleFrames, false, capture));
    stableState = attemptState;
    attemptPending = false;
    attemptOutcomeKnown = false;
    attemptState = null;
    currentFrames = 0;
    neutralSeen = false;
    candidateSignature = null;
    lastCapture = null;
    completedInputs++;
    if (completedInputs == expectedInputCount)
    {
        if (TryClaimExpectedInputCompletion(utcNow))
            FinishExpectedInputCount(utcNow);
        return;
    }
    phase = PassivePhase.Ready;
    try
    {
        reporter.Ready(completedInputs);
    }
    catch (Exception error)
    {
        SafeDiagnostic(error);
        TryFaultInternal(
            "observer_exception", FaultRequest.Derived());
    }
}
```

Create `PassiveDriverCompletion.cs` with this wrapper, placing every completion
member below inside it:

```csharp
using System;
using System.Threading;

internal sealed partial class PassiveDriver
{
    // Task 6 completion members.
}
```

Implement count/UTC validation, an atomic success claim, `EndRecord`, Close,
Done, and Complete. After a durable Step, clear
attempt state, increment count, and choose Ready for intermediate counts or
completion for the expected count. Complete failure occurs only after closed
success bytes and may call `Failed("observer_exception")` without Error or a
second Close.

Validate the final UTC only after Step 2 is durable. A value exactly equal to
the Run record's `StartedAtUtc` is valid and is retained unchanged in End. At
this temporary basic checkpoint, an earlier value throws into CompleteUpdate's
ordinary `observer_exception` catch after Step state is cleared. Task 6 Step 3
replaces that handoff so the final implementation queues the same rebased work
atomically under the active lease. Its Error has null index/input, zero frames,
and null last capture, then Error -> Close -> Failed; it emits no End, Complete,
or Ready(3).

For this basic-completion checkpoint, use the constants above; Task 6 Step 3
names the existing fault value and adds disposal ownership when it unifies all
terminal paths.

Use this temporary claim body for the basic checkpoint; Task 6 Step 3 replaces
it with atomic validation/fault queuing under the new lease lock:

```csharp
private bool TryClaimExpectedInputCompletion(DateTime finishedAtUtc)
{
    OracleValidation.Utc(finishedAtUtc, "finishedAtUtc");
    if (finishedAtUtc < startedAtUtc)
        throw new ArgumentOutOfRangeException("finishedAtUtc");
    if (completedInputs != expectedInputCount)
        throw new InvalidOperationException(
            "completion requires expected input count");
    return Interlocked.CompareExchange(
        ref terminalOwner, SuccessTerminalOwner, NoTerminalOwner)
        == NoTerminalOwner;
}
```

Use this End/Close/Complete body after the durable Step. At the basic checkpoint
it runs directly; after Task 6 Step 3 it runs while the Step lease remains
logically active but outside `outputLeaseSync`:

```csharp
private void FinishExpectedInputCount(DateTime finishedAtUtc)
{
    try
    {
        sink.WriteEnd(new EndRecord(
            runId, expectedInputCount, finishedAtUtc));
        CloseSink();
    }
    catch (Exception error)
    {
        phase = PassivePhase.Faulted;
        SafeDiagnostic(error);
        BestEffortClose();
        SafeFailed("trace_io_failed");
        return;
    }
    phase = PassivePhase.Done;
    try { reporter.Complete(); }
    catch (Exception error)
    {
        phase = PassivePhase.Faulted;
        SafeDiagnostic(error);
        SafeFailed("observer_exception");
    }
}
```

- [ ] **Step 2: Confirm basic completion passes and expose ownership RED**

Run forced net10 build and `driver-terminal`.

Expected: the first two completion/order subcases advance, but the same first
registered test exits 1 in `InvalidUtcOwnsBeforeErrorDrain`: the temporary
invalid-UTC path does not keep selection and Error drain inside one serialized
transaction, so Dispose can Close while `ErrorEntering` is blocked. Preserve
this second RED externally.

- [ ] **Step 3: Add the shared output lease and terminal work queue**

In `PassiveDriver.cs`, add:

```csharp
private const int FaultTerminalOwner = 1;
private const int DisposeTerminalOwner = 3;
```

Add enums:

```csharp
private enum TerminalWorkKind
{
    OrdinaryFault,
    TraceIoFailure,
    Dispose
}

private enum StepContinuation
{
    None,
    Ready,
    Complete
}
```

Add nested `TerminalWork` with fields `Kind`, `Code`, `Error` and exact
factories:

```csharp
private sealed class TerminalWork
{
    internal TerminalWorkKind Kind;
    internal string Code;
    internal ErrorRecord Error;

    internal static TerminalWork Ordinary(
        string code, ErrorRecord error)
    {
        return new TerminalWork
        {
            Kind = TerminalWorkKind.OrdinaryFault,
            Code = code,
            Error = error
        };
    }

    internal static TerminalWork TraceIo()
    {
        return new TerminalWork { Kind = TerminalWorkKind.TraceIoFailure };
    }

    internal static TerminalWork DisposeOnly()
    {
        return new TerminalWork { Kind = TerminalWorkKind.Dispose };
    }
}
```

Add exact fields:

```csharp
private readonly object outputLeaseSync = new object();
private bool outputLeaseActive;
private TerminalWork deferredTerminalWork;
```

Add:

```csharp
private bool TryAcquireOutputLease();
private void SafeDiagnosticWithOutputLease(Exception error);
private bool QueueOrAcquireOutputLeaseLocked(TerminalWork work);
private void ReleaseOutputLease(bool traceIoFailure);
private void ExecuteTerminalWorkAndRelease(TerminalWork work);
private void ClearInitialAfterTerminalReturn();
private void ClearAttemptAfterTerminalReturn();
private bool TryClaimExpectedInputCompletion(DateTime finishedAtUtc);
private void FinishExpectedInputCount(DateTime finishedAtUtc);
private StepContinuation SelectDurableStepContinuation(DateTime utcNow);
```

Implement acquisition, queuing, and draining with these exact lock boundaries.
The lock protects state selection only; logical `outputLeaseActive` remains true
while every external callback runs:

```csharp
private bool TryAcquireOutputLease()
{
    lock (outputLeaseSync)
    {
        if (TerminalSelected() || Read(ref disposed) != 0
            || Read(ref disabled) != 0)
            return false;
        if (outputLeaseActive)
            throw new InvalidOperationException("output lease already active");
        outputLeaseActive = true;
        return true;
    }
}

private void SafeDiagnosticWithOutputLease(Exception error)
{
    if (!TryAcquireOutputLease())
        return;
    try
    {
        SafeDiagnostic(error);
    }
    finally
    {
        ReleaseOutputLease(false);
    }
}

private bool QueueOrAcquireOutputLeaseLocked(TerminalWork work)
{
    if (work == null)
        throw new ArgumentNullException("work");
    if (outputLeaseActive)
    {
        if (deferredTerminalWork != null)
            throw new InvalidOperationException("terminal work already queued");
        deferredTerminalWork = work;
        return false;
    }
    outputLeaseActive = true;
    return true;
}

private void ReleaseOutputLease(bool traceIoFailure)
{
    TerminalWork next = null;
    lock (outputLeaseSync)
    {
        if (!outputLeaseActive)
            throw new InvalidOperationException("output lease is not active");
        if (traceIoFailure && deferredTerminalWork != null
            && deferredTerminalWork.Kind == TerminalWorkKind.OrdinaryFault)
            deferredTerminalWork = TerminalWork.TraceIo();
        if (deferredTerminalWork == null)
            outputLeaseActive = false;
        else
        {
            next = deferredTerminalWork;
            deferredTerminalWork = null;
        }
    }
    if (next != null)
        ExecuteTerminalWorkAndRelease(next);
}

private void ExecuteTerminalWorkAndRelease(TerminalWork work)
{
    try
    {
        if (work.Kind == TerminalWorkKind.OrdinaryFault)
        {
            bool durable = false;
            try
            {
                sink.WriteError(work.Error);
                CloseSink();
                durable = true;
            }
            catch (Exception error)
            {
                SafeDiagnostic(error);
                BestEffortClose();
            }
            SafeFailed(durable ? work.Code : "trace_io_failed");
        }
        else if (work.Kind == TerminalWorkKind.TraceIoFailure)
        {
            phase = PassivePhase.Faulted;
            BestEffortClose();
            SafeFailed("trace_io_failed");
        }
        else
            BestEffortClose();
    }
    finally
    {
        lock (outputLeaseSync)
        {
            outputLeaseActive = false;
        }
    }
}
```

Terminal selection occurs under the same lock and execution occurs after the
lock is released:

```csharp
private bool TryFaultInternal(string code, FaultRequest request)
{
    OracleErrors.ForCode(code);
    TerminalWork work;
    bool execute;
    lock (outputLeaseSync)
    {
        if (Interlocked.CompareExchange(
            ref terminalOwner, FaultTerminalOwner, NoTerminalOwner)
            != NoTerminalOwner)
            return false;
        PassivePhase faultPhase = phase;
        phase = PassivePhase.Faulted;
        work = Read(ref prepared) == 0
            ? TerminalWork.TraceIo()
            : TerminalWork.Ordinary(
                code, BuildErrorRecord(code, request, faultPhase));
        execute = QueueOrAcquireOutputLeaseLocked(work);
    }
    if (execute)
        ExecuteTerminalWorkAndRelease(work);
    return true;
}

public void Dispose()
{
    if (Interlocked.CompareExchange(ref disposed, 1, 0) != 0)
        return;
    Interlocked.Exchange(ref disabled, 1);
    TerminalWork work = null;
    bool execute = false;
    lock (outputLeaseSync)
    {
        if (Interlocked.CompareExchange(
            ref terminalOwner, DisposeTerminalOwner, NoTerminalOwner)
            == NoTerminalOwner)
        {
            work = TerminalWork.DisposeOnly();
            execute = QueueOrAcquireOutputLeaseLocked(work);
        }
    }
    if (execute)
        ExecuteTerminalWorkAndRelease(work);
}
```

Use this trace-I/O selection body. If Fault already owns queued ordinary work,
the active producer's later `ReleaseOutputLease(true)` performs the replacement:

```csharp
private void SelectTraceIoFailure()
{
    TerminalWork work = null;
    bool execute = false;
    lock (outputLeaseSync)
    {
        if (Interlocked.CompareExchange(
            ref terminalOwner, FaultTerminalOwner, NoTerminalOwner)
            == NoTerminalOwner)
        {
            phase = PassivePhase.Faulted;
            work = TerminalWork.TraceIo();
            execute = QueueOrAcquireOutputLeaseLocked(work);
        }
    }
    if (execute)
        ExecuteTerminalWorkAndRelease(work);
}
```

Replace the temporary success-claim method with this final version. It is called
only from `SelectDurableStepContinuation` while `outputLeaseSync` is held and
the Step lease is active. UTC kind was already boundary-validated before
`CompleteUpdateCore`; relation/count arbitration and terminal selection happen
here without an external callback:

```csharp
private bool TryClaimExpectedInputCompletion(DateTime finishedAtUtc)
{
    if (completedInputs != expectedInputCount
        || finishedAtUtc.Kind != DateTimeKind.Utc
        || finishedAtUtc < startedAtUtc)
    {
        if (Interlocked.CompareExchange(
            ref terminalOwner, FaultTerminalOwner, NoTerminalOwner)
            != NoTerminalOwner)
            return false;
        phase = PassivePhase.Faulted;
        TerminalWork work = TerminalWork.Ordinary(
            "observer_exception",
            new ErrorRecord(
                runId, null, null, "observer_exception", 0, null));
        if (QueueOrAcquireOutputLeaseLocked(work))
            throw new InvalidOperationException(
                "completion fault must defer behind Step lease");
        return false;
    }
    return Interlocked.CompareExchange(
        ref terminalOwner, SuccessTerminalOwner, NoTerminalOwner)
        == NoTerminalOwner;
}
```

Thus invalid relation/count work is owned and queued before the Step lease can
be released. `FinishExpectedInputCount` is the only completion method that
performs external callbacks, and it remains outside `outputLeaseSync`.

Replace Prepare's output section with this Run transaction:

```csharp
if (!TryAcquireOutputLease())
    return false;
bool runTraceIoFailure = false;
bool runPrepared = false;
try
{
    try { sink.WriteRun(run); }
    catch (Exception error)
    {
        runTraceIoFailure = true;
        SafeDiagnostic(error);
        SelectTraceIoFailure();
        return false;
    }
    lock (outputLeaseSync)
    {
        if (TerminalSelected() || Read(ref disposed) != 0
            || Read(ref disabled) != 0)
            return false;
        runId = run.RunId;
        startedAtUtc = run.StartedAtUtc;
        Interlocked.Exchange(ref prepared, 1);
        runPrepared = true;
    }
    return true;
}
finally
{
    ReleaseOutputLease(runTraceIoFailure);
    if (!runPrepared)
        Interlocked.Exchange(ref prepared, 0);
}
```

Replace `EmitInitial` with this Initial/Ready transaction:

```csharp
private void EmitInitial(CaptureRecord capture)
{
    if (!TryAcquireOutputLease())
    {
        ClearInitialAfterTerminalReturn();
        return;
    }
    bool traceIoFailure = false;
    try
    {
        try { sink.WriteInitial(new InitialRecord(runId, capture)); }
        catch (Exception error)
        {
            traceIoFailure = true;
            SafeDiagnostic(error);
            SelectTraceIoFailure();
            return;
        }
        bool reportReady;
        lock (outputLeaseSync)
        {
            reportReady = !TerminalSelected()
                && Read(ref disposed) == 0 && Read(ref disabled) == 0;
            if (reportReady)
            {
                stableState = epochState;
                phase = PassivePhase.Ready;
            }
            epochState = null;
            currentFrames = 0;
            neutralSeen = false;
            candidateSignature = null;
            lastCapture = null;
        }
        if (reportReady)
        {
            try { reporter.Ready(0); }
            catch (Exception error)
            {
                SafeDiagnostic(error);
                TryFaultInternal(
                    "observer_exception", FaultRequest.Derived());
            }
        }
    }
    finally
    {
        ReleaseOutputLease(traceIoFailure);
    }
}
```

These bodies make the Run/Initial entry and terminal-return behavior executable:
durability precedes publication, a contender can claim and return while output
is blocked, and queued terminal work drains only from the producer's `finally`.

Run, Initial, Step, Error, End, Close, Ready, Complete, Failed, and Dispose all
use the same logical lease, as does best-effort Diagnostic. No monitor or
`outputLeaseSync` lock encloses sink/reporter code. Calls to `SafeDiagnostic`
from code already holding the logical lease remain direct. Replace the generic
`CompleteUpdate` catch, which runs after any producer `finally` has released
its lease, with:

```csharp
catch (Exception error)
{
    SafeDiagnosticWithOutputLease(error);
    TryFaultInternal(
        "observer_exception", FaultRequest.Derived());
}
```

If another terminal owner wins before this best-effort diagnostic acquires the
lease, suppress the diagnostic; never overlap it with terminal output.

The two terminal-return clear helpers are complete, output-free, and lock their
own mutations because they are called after lease acquisition was refused:

```csharp
private void ClearInitialAfterTerminalReturn()
{
    lock (outputLeaseSync)
    {
        epochState = null;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
    }
}

private void ClearAttemptAfterTerminalReturn()
{
    lock (outputLeaseSync)
    {
        attemptPending = false;
        attemptOutcomeKnown = false;
        attemptState = null;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
    }
}
```

Use this Step path:

```csharp
private void EmitSettledAttempt(
    CaptureRecord capture, int settleFrames, DateTime utcNow)
{
    if (!attemptPending || !attemptOutcomeKnown)
        throw new InvalidOperationException("settled attempt lacks outcome");
    if (!TryAcquireOutputLease())
    {
        ClearAttemptAfterTerminalReturn();
        return;
    }
    bool traceIoFailure = false;
    try
    {
        try
        {
            sink.WriteStep(new StepRecord(
                runId, completedInputs, attemptInput, attemptAccepted,
                attemptMovementScheduled, settleFrames, false, capture));
        }
        catch (TraceIoException)
        {
            traceIoFailure = true;
            SelectTraceIoFailure();
            throw;
        }
        StepContinuation continuation =
            SelectDurableStepContinuation(utcNow);
        if (continuation == StepContinuation.Complete)
            FinishExpectedInputCount(utcNow);
        else if (continuation == StepContinuation.Ready)
        {
            try { reporter.Ready(completedInputs); }
            catch (Exception error)
            {
                SafeDiagnostic(error);
                TryFaultInternal(
                    "observer_exception", FaultRequest.Derived());
            }
        }
    }
    finally
    {
        ReleaseOutputLease(traceIoFailure);
    }
}

private StepContinuation SelectDurableStepContinuation(DateTime utcNow)
{
    lock (outputLeaseSync)
    {
        stableState = attemptState;
        attemptPending = false;
        attemptOutcomeKnown = false;
        attemptState = null;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
        completedInputs++;
        if (TerminalSelected() || Read(ref disposed) != 0
            || Read(ref disabled) != 0)
            return StepContinuation.None;
        if (completedInputs == expectedInputCount)
            return TryClaimExpectedInputCompletion(utcNow)
                ? StepContinuation.Complete : StepContinuation.None;
        phase = PassivePhase.Ready;
        return StepContinuation.Ready;
    }
}
```

Run and Initial follow the same
acquire -> external durable write -> locked state continuation -> external
reporter -> release shape. Prepare publishes `runId`, `startedAtUtc`, and
`prepared` only after durable Run; Initial publishes Ready only after durable
Initial, and suppresses Ready if a queued terminal/dispose claim won.

- [ ] **Step 4: Confirm ownership/serialization passes and expose rebase RED**

Run forced net10 build and `driver-terminal` again.

Expected: invalid-UTC ownership and the earlier barrier races advance, but
`first fault wins race` exits 1 in its real NDJSON subcase because a queued
ordinary Error still carries the just-durable attempt index/input, frames, or
last capture. Preserve this third RED externally.

- [ ] **Step 5: Rebase only deferred ordinary work after a durable Step**

Inside the output-lease lock in `SelectDurableStepContinuation`, after updating
stable state, clearing the attempt/candidate/last-capture state, and incrementing
`completedInputs`, replace only deferred `OrdinaryFault` data with:

```csharp
if (deferredTerminalWork != null
    && deferredTerminalWork.Kind == TerminalWorkKind.OrdinaryFault)
{
    deferredTerminalWork.Error = new ErrorRecord(
        runId,
        null,
        null,
        deferredTerminalWork.Code,
        0,
        null);
}
```

Do not rewrite TraceIo or Dispose work. Keep the original fault code. The final
real trace must contain the durable Step line followed by the rebased Error line.

- [ ] **Step 6: Run Task 5.3 focused GREEN, stress, and full matrix**

Run forced net10 build; `driver-boundary`; `driver-initial`; `driver-input`;
`driver-terminal`; full C# harness; forced net35 build; and full Python suite.
Then set `results_file` and run the exact common 20-run stress script. Every
iteration must exit 0, print exactly the ready line, leave stderr empty, and
leave Git unchanged.

Expected: 39 C# tests and all commands/20 stress iterations pass.

- [ ] **Step 7: Run pre-commit specification and quality reviews**

Review the whole final Task 5.3 working-tree diff once, including all three RED
checkpoints, the full GREEN matrix, the 20-run stress result, the real NDJSON
proof, and the fact that both terminal corrections are folded into this single
slice. Resolve and re-review all required findings.

- [ ] **Step 8: Commit the exact reviewed Task 5.3 tree**

```bash
git add -- \
  oracle/plugin/Core/PassiveDriver.cs \
  oracle/plugin/Core/PassiveDriverInput.cs \
  oracle/plugin/Core/PassiveDriverCompletion.cs \
  oracle/plugin/tests/PassiveDriverInputTests.cs \
  oracle/plugin/tests/PassiveDriverTerminalTests.cs \
  oracle/plugin/tests/PassiveDriverTestSupport.cs \
  oracle/plugin/tests/PassiveDriverTests.cs \
  oracle/plugin/tests/Program.cs
git diff --cached --check
git commit -m "feat: finalize passive trace capture"
```

Expected: exact eight-file scope and the approved Task 5.2 commit as sole parent.

- [ ] **Step 9: Review the immutable Task 5.3 commit**

Authenticate subject, parent, scope, tree, repository state, and preserved
historical plan. Dispatch fresh reviewers over `HEAD^..HEAD`; require both to
approve with zero Critical/Important findings before mutation qualification.

### Task 7: Kill Five Targeted Mutations in Disposable Copies

**Files:**
- Mutate temporarily: `oracle/plugin/Core/PassiveDriverInput.cs` in copy 1
- Mutate temporarily: `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs` in copy 2
- Analyze without editing: `oracle/plugin/Core/PassiveDriverCompletion.cs` in copy 3
- Mutate temporarily: `oracle/plugin/Core/PassiveDriverCompletion.cs` in copies 4 and 5
- Test read-only: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Test read-only: `oracle/plugin/tests/PassiveDriverTerminalTests.cs`
- Preserve: the primary worktree and every commit

**Interfaces:**
- Consumes: immutable approved three-commit implementation tip.
- Produces: five recorded mutation outcomes with no surviving mutation.

- [ ] **Step 1: Create and validate one disposable copy per mutation**

For each mutation, use this shape with a newly resolved clean implementation
tip and a fresh root:

```bash
primary_root=/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-oracle-passive-trace
implementation_tip="$(git -C "$primary_root" rev-parse HEAD)"
mutation_root="$(mktemp -d /private/tmp/ssr-task5-mutation.XXXXXX)"
clone_root="$mutation_root/repo"
git clone --no-hardlinks --local "$primary_root" "$clone_root"
git -C "$clone_root" checkout --detach "$implementation_tip"
test "$(git -C "$clone_root" rev-parse HEAD)" = "$implementation_tip"
test -z "$(git -C "$clone_root" status --short)"
test -f "$primary_root/oracle/plugin/tests/obj/project.assets.json"
/bin/cp -R "$primary_root/oracle/plugin/tests/obj" \
  "$clone_root/oracle/plugin/tests/"
test -f "$clone_root/oracle/plugin/tests/obj/project.assets.json"
test "$(stat -f '%d:%i' \
  "$primary_root/oracle/plugin/tests/obj/project.assets.json")" != \
  "$(stat -f '%d:%i' \
  "$clone_root/oracle/plugin/tests/obj/project.assets.json")"
test -z "$(git -C "$clone_root" status --short)"
```

Before editing, set `target_rel` to that mutation's exact target path and verify
copy isolation:

```bash
test "$(stat -f '%d:%i' "$primary_root/$target_rel")" != \
  "$(stat -f '%d:%i' "$clone_root/$target_rel")"
```

The ignored `obj` copy is trusted offline build metadata: both project files are
frozen and every mutation still uses `--no-restore`. Never use `cp -al`, a
worktree sharing the primary index, or an existing clone.

After applying each non-omitted semantic edit, set `mutant_cohort` to that
step's named cohort and execute the build and test from the clone explicitly:

```bash
(
  cd "$clone_root"
  "$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    --configuration Release --no-restore --nologo -warnaserror \
    -t:Rebuild -m:1 -p:UseSharedCompilation=false
)
mutant_status=0
(
  cd "$clone_root"
  "$dotnet_bin" run \
    --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    --configuration Release --no-restore --no-build -- \
    --cohort "$mutant_cohort"
) || mutant_status=$?
test "$mutant_status" -ne 0
```

The clone build must exit 0; the clone cohort must exit nonzero with the exact
intended first failure. Never invoke the mutant command while the shell remains
in `primary_root`. Run every required primary reauthentication/build/GREEN from
an explicit subshell that first executes `cd "$primary_root"`.

For each transaction, if the planned edit is not one compiling semantic, refine
it before running the cohort. If a compiling narrow mutant survives its intended
test because the semantic is redundant, record `OMITTED-REDUNDANT` with the
evidence and do not count it as killed. In either case, discard the clone and run
the specified fresh primary-tree GREEN before starting the next transaction.

- [ ] **Step 2: Mutation 1 — corrupt exact cardinal correlation**

In the disposable copy only, make `ProcessInputEntered` reject the exact
`playerPoll.RawDirection == rawDirection` match while leaving the surrounding
policy unchanged. Force-build and run `driver-input`.

Replace only this condition:

```csharp
if (playerPoll.RawDirection != rawDirection)
```

with this compiling mutant:

```csharp
if (playerPoll.RawDirection == rawDirection)
```

Expected: build succeeds; `all cardinals correlate` fails because cardinal 0 no
longer opens attempt 0. Record the first failure and discard the entire clone.
Authenticate the primary HEAD/tree/status, force-build it, and run
`driver-input`; require a fresh GREEN before Mutation 2.

- [ ] **Step 3: Mutation 2 — establish Restart depth after fault selection**

In a fresh copy, move the outermost `TryFaultInternal` call before the token is
pushed and `restartDepth` is incremented. Force-build and run `driver-input`.

Replace only:

```csharp
restartContexts.Add(token.Id);
restartDepth++;
if (!nested)
    TryFaultInternal("unexpected_input", FaultRequest.Restart());
```

with:

```csharp
if (!nested)
    TryFaultInternal("unexpected_input", FaultRequest.Restart());
restartContexts.Add(token.Id);
restartDepth++;
```

Expected: `restart depth and null fields` fails at its reentrant Restart-depth
assertion. Record and discard the clone. Authenticate the primary HEAD/tree/
status, force-build it, and run `driver-input`; require a fresh GREEN before
Mutation 3.

- [ ] **Step 4: Mutation 3 — document redundant lease release before Close**

In a fresh authenticated copy, inspect successful `FinishExpectedInputCount`
and the first-owner/output-entry gates without editing either. Releasing only
the private logical lease flag immediately before Close is not externally
observable: the already-claimed success owner independently rejects new Run,
Initial, Step, Error, and disposal ownership, while End/Close/Complete ordering
is unchanged. Detecting that flag directly would require private-state
reflection, which the behavioral spec forbids as a new special-purpose seam.

Expected: record `OMITTED-REDUNDANT` with those two reasons and do not count the
transaction as killed. Discard the untouched clone, authenticate the primary
HEAD/tree/status, force-build it, and run `driver-terminal`; require a fresh
GREEN before Mutation 4. This is the lean design section 7 contingency for a
behaviorally redundant selected mutation.

- [ ] **Step 5: Mutation 4 — retain stale deferred attempt fields**

In a fresh copy, remove only the deferred `OrdinaryFault` rebuild from
`SelectDurableStepContinuation`. Force-build and run `driver-terminal`.

Delete exactly this guarded block and no surrounding state transition:

```csharp
if (deferredTerminalWork != null
    && deferredTerminalWork.Kind == TerminalWorkKind.OrdinaryFault)
{
    deferredTerminalWork.Error = new ErrorRecord(
        runId, null, null, deferredTerminalWork.Code, 0, null);
}
```

Expected: `first fault wins race` fails because the real Step is followed by an
Error with stale attempt fields. Record and discard the clone. Authenticate the
primary HEAD/tree/status, force-build it, and run `driver-terminal`; require a
fresh GREEN before Mutation 5.

- [ ] **Step 6: Mutation 5 — Complete before Close**

In a fresh copy, invoke `reporter.Complete()` before `CloseSink()` inside
successful completion while leaving End first. Force-build and run
`driver-terminal`.

Replace the complete final `FinishExpectedInputCount` body with this compiling
mutant, which changes only the successful callback order while retaining End
first, trace-I/O conversion for End/Close, and observer-exception conversion for
Complete:

```csharp
private void FinishExpectedInputCount(DateTime finishedAtUtc)
{
    try
    {
        sink.WriteEnd(new EndRecord(
            runId, expectedInputCount, finishedAtUtc));
    }
    catch (Exception error)
    {
        phase = PassivePhase.Faulted;
        SafeDiagnostic(error);
        BestEffortClose();
        SafeFailed("trace_io_failed");
        return;
    }
    phase = PassivePhase.Done;
    try
    {
        reporter.Complete();
    }
    catch (Exception error)
    {
        phase = PassivePhase.Faulted;
        SafeDiagnostic(error);
        BestEffortClose();
        SafeFailed("observer_exception");
        return;
    }
    try
    {
        CloseSink();
    }
    catch (Exception error)
    {
        phase = PassivePhase.Faulted;
        SafeDiagnostic(error);
        BestEffortClose();
        SafeFailed("trace_io_failed");
    }
}
```

Expected: `three steps End Close Complete order` fails on exact event order.
Record and discard the clone. Authenticate the primary HEAD/tree/status,
force-build it, and run `driver-terminal`; require a fresh GREEN before the
aggregate primary verification.

- [ ] **Step 7: Reverify the untouched primary implementation**

Confirm primary HEAD/tree/status did not change, every mutation clone is outside
the repository, and no mutation path is staged. Run a fresh forced net10 build,
`driver-boundary`, `driver-input`, and `driver-terminal` from the primary tree;
all must pass.

### Task 8: Final Cross-Slice Review and Verification Report

**Files:**
- Create: `docs/superpowers/reports/2026-08-12-task-5-passive-driver-verification.md`
- Read: three implementation commits and all external lean result notes

**Interfaces:**
- Consumes: approved immutable three-commit range, five completed mutation
  transactions (killed or explicitly omitted under the design rule), and a
  clean complete verification matrix.
- Produces: the compact tracked Task 5 verification report.

- [ ] **Step 1: Run the final clean matrix and 20-run terminal stress**

From exact implementation tip, run forced net10 build; `driver-boundary`;
`driver-initial`; `driver-input`; `driver-terminal`; full C# harness; forced
net35 build; full Python suite; and the exact common 20-iteration terminal
stress script. Confirm exact 39-test registration and unchanged Git state.

- [ ] **Step 2: Obtain fresh cross-slice reviews**

Give independent specification and quality reviewers both controlling specs,
the complete three-commit range from the dynamically resolved `plan_commit`,
all per-slice immutable review
verdicts, final commands/results, stress summary, real NDJSON result, and the
five mutation outcomes. Require explicit verdicts and severity counts.

Any implementation Critical/Important finding stops for user adjudication and
an explicitly approved follow-up commit. Classify every Minor/code finding as
accepted or rejected with evidence; every accepted implementation finding,
regardless of severity, is corrected through normal RED/GREEN work in a
separate append-only follow-up commit approved by the user, never by amending a
reviewed slice. Re-run the affected and full matrices, all five mutations
against the corrected tip, the exact common 20-run terminal stress with fresh
captured evidence, and fresh immutable cross-slice reviews. Resolve
`accepted_implementation_tip` to the resulting correction commit, or to the
Task 5.3 commit when no implementation correction is accepted. Report-only
findings are fixed before the report commit and re-reviewed.

- [ ] **Step 3: Write the compact verification report**

Record:

```markdown
# Task 5 Passive Driver Verification

## Scope and lineage
## Task 5.1 RED, GREEN, reviews, and commit
## Task 5.2 RED, GREEN, reviews, and commit
## Task 5.3 three REDs, GREEN, stress, reviews, and commit
## Final offline verification matrix
## Five targeted mutation outcomes
## Cross-slice reviewer verdicts and findings
## Preserved historical recovery artifacts
## Completion assessment and deviations
```

Keep command text, exit status, test totals, commit IDs, reviewer verdicts, and
mutation first failures. Do not paste full logs, generated patches, old
authority manifests, controller material, or prospective report-commit hashes.

- [ ] **Step 4: Review and commit only the report**

Run `git diff --check`, verify the report against the preserved result notes and
actual commits, and dispatch fresh specification and quality reviews of the
staged report plus immutable implementation range. Fix report-only findings and
re-review.

```bash
git add -- \
  docs/superpowers/reports/2026-08-12-task-5-passive-driver-verification.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs: record Task 5 passive driver verification"
```

Expected: one-file report commit, sole parent equal to
`accepted_implementation_tip` (normally the Task 5.3 commit), clean
tracked/index state, and the historical recovery plan still the only untracked
path.

- [ ] **Step 5: Perform completion verification**

Authenticate the final linear graph from lean design through the required three
implementation commits, any explicitly approved append-only correction
commits, and report; exact subjects/scopes/parents; all review approvals; all
five mutation transactions against the accepted implementation tip recorded,
every non-omitted mutant killed, and no mutation present; final
39-test/net35/Python matrix; no Task 6 changes; and preserved historical
artifacts.
