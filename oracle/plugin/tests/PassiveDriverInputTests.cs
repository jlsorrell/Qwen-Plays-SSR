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
    tests.Add("driver-input", "restart depth and null fields",
        RestartDepthAndNullFields);
    tests.Add("driver-input", "state replacement and ClearThrew",
        StateReplacementAndClearThrew);
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
    EveryIntermediateSettledStepReportsReady();
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

private static void EveryIntermediateSettledStepReportsReady()
{
    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    fixture.OpenDirection(0, false, false, 20.0);
    fixture.SettleCurrent(ProtocolSamples.MovedCapture, 21.0);
    Check.Sequence(
        new int[] { 0, 1, 2 },
        fixture.Reporter.ReadyValues.ToArray(),
        "every intermediate Step reports Ready");
}

private static void RestartDepthAndNullFields()
{
    RestartFieldsFollowEveryActivePhase();
    RestartDepthPrecedesFault();
    RestartNestedPathsBalance();
    RestartCleanupIsLifoAndSingleUse();
}

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

private static void StateReplacementAndClearThrew()
{
    StateSetUsesActualReturnedIdentity();
    StateSetContextIdentityIsAuthoritative();
    StateSetBeforeInitialRulesAreExact();
    StateSetAfterInitialRulesAreExact();
    ClearThrewDispatchesAndProtectsOwnership();
    LateHookCleanupIsOutputInert();
}

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

}
