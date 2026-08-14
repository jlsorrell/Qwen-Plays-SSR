using System;
using System.Collections.Generic;

internal static class PassiveDriverInputTests
{
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
    DirectionWithoutReturnedOutcomeFaults();
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
    UndoWithoutReturnedOutcomeFaults();
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

private static void DirectionWithoutReturnedOutcomeFaults()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken poll = fixture.Driver.PlayerPollEntered();
    fixture.Driver.PhysicalPollReturned(2);
    HookToken input = fixture.Driver.ProcessInputEntered(
        fixture.State, 2, 10.0);
    fixture.Driver.PlayerPollReturned(poll);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);

    ErrorRecord error = AssertInputError(
        fixture, "observer_exception", 0, OracleInput.West, 2,
        "direction without returned outcome");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "direction without outcome Faulted");
    Check.Equal(0, fixture.Sink.StepCalls, "direction no Step attempt");
    Check.Sequence(
        new int[] { 0 }, fixture.Reporter.ReadyValues.ToArray(),
        "direction no new Ready");
    Check.Sequence(
        new string[] { "observer_exception" },
        fixture.Reporter.FailedCodes.ToArray(),
        "direction ordinary failure marker");
    Check.Equal(1, fixture.Sink.CloseCalls, "direction one Close");
    Check.True(
        Object.ReferenceEquals(error.LastCapture, ProtocolSamples.MovedCapture),
        "direction retains committed capture");
    Check.Sequence(
        new string[]
        {
            "report:diagnostic:System.InvalidOperationException",
            "sink:error:observer_exception", "sink:close",
            "report:failed:observer_exception"
        },
        fixture.Events.GetRange(fixture.Events.Count - 4, 4).ToArray(),
        "direction missing outcome terminal suffix");

    int eventCount = fixture.Events.Count;
    fixture.Driver.ProcessInputThrew(input);
    fixture.Driver.ProcessInputThrew(input);
    Check.Equal(
        eventCount, fixture.Events.Count,
        "late ProcessInput throw leaves terminal result");
    Check.True(
        Object.ReferenceEquals(error, fixture.Sink.ErrorRecords[0]),
        "late ProcessInput throw retains first Error");
}

private static void UndoWithoutReturnedOutcomeFaults()
{
    DriverFixture fixture = DriverFixture.Ready();
    HookToken undo = fixture.Driver.UndoEntered(fixture.State, 10.0);
    fixture.Driver.RestoreObserved();
    fixture.SettleCurrent(ProtocolSamples.InitialCapture, 11.0);

    ErrorRecord error = AssertInputError(
        fixture, "observer_exception", 0, OracleInput.Undo, 2,
        "Undo without returned outcome");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "Undo without outcome Faulted");
    Check.Equal(0, fixture.Sink.StepCalls, "Undo no Step attempt");
    Check.Sequence(
        new int[] { 0 }, fixture.Reporter.ReadyValues.ToArray(),
        "Undo no new Ready");
    Check.Sequence(
        new string[] { "observer_exception" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Undo ordinary failure marker");
    Check.Equal(1, fixture.Sink.CloseCalls, "Undo one Close");
    Check.True(
        Object.ReferenceEquals(error.LastCapture, ProtocolSamples.InitialCapture),
        "Undo retains committed capture");
    Check.Sequence(
        new string[]
        {
            "report:diagnostic:System.InvalidOperationException",
            "sink:error:observer_exception", "sink:close",
            "report:failed:observer_exception"
        },
        fixture.Events.GetRange(fixture.Events.Count - 4, 4).ToArray(),
        "Undo missing outcome terminal suffix");

    int eventCount = fixture.Events.Count;
    fixture.Driver.UndoThrew(undo);
    fixture.Driver.UndoThrew(undo);
    Check.Equal(
        eventCount, fixture.Events.Count,
        "late Undo throw leaves terminal result");
    Check.True(
        Object.ReferenceEquals(error, fixture.Sink.ErrorRecords[0]),
        "late Undo throw retains first Error");
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

}
