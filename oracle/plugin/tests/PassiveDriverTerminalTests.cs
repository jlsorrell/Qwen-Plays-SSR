using System;
using System.Collections.Generic;
using System.Threading;

internal static class PassiveDriverTerminalTests
{
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

private static void ErrorFieldPolicyIsExact()
{
    RestartOverridesInputFields();
    PendingAttemptWinsErrorFields();
    MappedAndUnknownOffendersAreExact();
    GenericAndInitialFramesAreExact();
}

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

private static void SinkFailureUsesTraceIoMarker()
{
    RunSinkFailureOwnsBeforeDiagnosticDispose();
    InitialSinkFailureOwnsBeforeDiagnosticDispose();
    AssertTerminalSinkFailure("step");
    AssertTerminalSinkFailure("end");
    AssertTerminalSinkFailure("error");
    AssertTerminalSinkFailure("close");
    OrdinaryErrorCloseFailureDowngradesMarker();
}

private static void RunSinkFailureOwnsBeforeDiagnosticDispose()
{
    DriverFixture fixture = DriverFixture.Unprepared();
    fixture.Sink.RunFailure = new TraceIoException("Run failure");
    fixture.Reporter.DiagnosticObserved = delegate(string message)
    {
        fixture.Driver.Dispose();
    };
    Check.False(
        fixture.Driver.Prepare(ProtocolSamples.Run),
        "Run sink failure rejects Prepare");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "Run sink failure owns before Diagnostic Dispose");
    Check.Equal(1, fixture.Sink.RunCalls, "Run attempted once");
    Check.Equal(1, fixture.Sink.CloseCalls, "Run failure closes once");
    Check.Sequence(
        new string[] { "trace_io_failed" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Run failure sole trace-I/O marker");
    Check.Equal(0, fixture.Sink.InitialRecords.Count, "Run no Initial");
    Check.Equal(0, fixture.Sink.StepRecords.Count, "Run no Step");
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, "Run no Error");
    Check.Equal(0, fixture.Sink.EndRecords.Count, "Run no End");
    Check.Sequence(
        new int[0], fixture.Reporter.ReadyValues.ToArray(),
        "Run no Ready");
    Check.Equal(0, fixture.Reporter.CompleteCalls, "Run no Complete");
}

private static void InitialSinkFailureOwnsBeforeDiagnosticDispose()
{
    DriverFixture fixture = DriverFixture.Active();
    PrepareInitialMatch(fixture);
    fixture.Sink.InitialFailure = new TraceIoException("Initial failure");
    fixture.Reporter.DiagnosticObserved = delegate(string message)
    {
        fixture.Driver.Dispose();
    };
    FinishInitialMatch(fixture);
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "Initial sink failure owns before Diagnostic Dispose");
    Check.Equal(1, fixture.Sink.InitialCalls, "Initial attempted once");
    Check.Equal(1, fixture.Sink.CloseCalls, "Initial failure closes once");
    Check.Sequence(
        new string[] { "trace_io_failed" },
        fixture.Reporter.FailedCodes.ToArray(),
        "Initial failure sole trace-I/O marker");
    Check.Equal(0, fixture.Sink.InitialRecords.Count, "Initial not durable");
    Check.Equal(0, fixture.Sink.StepRecords.Count, "Initial no Step");
    Check.Equal(0, fixture.Sink.ErrorRecords.Count, "Initial no Error");
    Check.Equal(0, fixture.Sink.EndRecords.Count, "Initial no End");
    Check.Sequence(
        new int[0], fixture.Reporter.ReadyValues.ToArray(),
        "Initial no Ready");
    Check.Equal(0, fixture.Reporter.CompleteCalls, "Initial no Complete");
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

private static void CompletionReporterCannotRewriteTrace()
{
    AssertCompleteFailureAfterClosedBytes();
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
    CompleteUpdateFailureOwnsBeforeDiagnosticDispose();
    ReadyFailureOwnsBeforeDiagnosticDispose();
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
        Thread worker = new Thread(delegate()
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
            Check.False(
                fixture.Driver.TryFault("capture_failed"),
                "Ready failure already owns during Diagnostic");
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
                fixture, "observer_exception", null, null, 0,
                "Diagnostic deferred observer fault");
        });
}

private static void ReadyFailureOwnsBeforeDiagnosticDispose()
{
    DriverFixture fixture = DriverFixture.Ready();
    PrepareFirstStepMatch(fixture);
    fixture.Reporter.ReadyFailure =
        new InvalidOperationException("Ready(1) failure");
    bool faultedBeforeDiagnosticReentry = false;
    fixture.Reporter.DiagnosticObserved = delegate(string message)
    {
        faultedBeforeDiagnosticReentry =
            fixture.Driver.Phase == PassivePhase.Faulted;
        fixture.Driver.Dispose();
    };

    FinishFirstStepMatch(fixture);

    Check.Equal(1, fixture.Sink.StepRecords.Count, "Ready failure Step durable");
    Check.Equal(
        1, fixture.Reporter.DiagnosticCalls,
        "Ready failure one Diagnostic");
    Check.True(
        faultedBeforeDiagnosticReentry,
        "Ready failure owns before Diagnostic Dispose");
    ErrorRecord error = AssertOnlyError(
        fixture, "observer_exception", null, null, 0,
        "Ready failure Diagnostic Dispose");
    Check.True(error.LastCapture == null, "Ready failure null capture");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "Ready failure remains Faulted after Dispose");
    Check.Sequence(
        new int[] { 0, 1 }, fixture.Reporter.ReadyValues.ToArray(),
        "Ready failure Ready values");
    Check.Sequence(
        new string[]
        {
            "sink:step:0", "report:ready:1/3",
            "report:diagnostic:System.InvalidOperationException",
            "sink:error:observer_exception", "sink:close",
            "report:failed:observer_exception"
        },
        fixture.Events.GetRange(fixture.Events.Count - 6, 6).ToArray(),
        "Ready failure authoritative terminal suffix");
}

private static void CompleteUpdateFailureOwnsBeforeDiagnosticDispose()
{
    DriverFixture fixture = DriverFixture.Ready();
    bool faultedBeforeDiagnosticReentry = false;
    fixture.Reporter.DiagnosticObserved = delegate(string message)
    {
        faultedBeforeDiagnosticReentry =
            fixture.Driver.Phase == PassivePhase.Faulted;
        fixture.Driver.Dispose();
    };
    UpdateDirective directive = fixture.Driver.BeginUpdate(
        fixture.State, true, 10.0);
    Check.True(directive.Active, "generic failure directive active");
    Check.True(
        fixture.Driver.AuthorizeUpdate(
            directive, fixture.State, true, true),
        "generic failure directive authorized");

    fixture.Driver.CompleteUpdate(
        directive,
        GateSample.Captured(ProtocolSamples.MovedCapture),
        DriverFixture.UtcFinish);

    Check.Equal(
        1, fixture.Reporter.DiagnosticCalls,
        "generic failure one Diagnostic");
    Check.True(
        faultedBeforeDiagnosticReentry,
        "generic failure owns before Diagnostic Dispose");
    ErrorRecord error = AssertOnlyError(
        fixture, "observer_exception", null, null, 0,
        "generic failure Diagnostic Dispose");
    Check.True(error.LastCapture == null, "generic failure null capture");
    Check.Equal(
        PassivePhase.Faulted, fixture.Driver.Phase,
        "generic failure remains Faulted after Dispose");
    Check.Sequence(
        new string[]
        {
            "report:diagnostic:System.InvalidOperationException",
            "sink:error:observer_exception", "sink:close",
            "report:failed:observer_exception"
        },
        fixture.Events.GetRange(fixture.Events.Count - 4, 4).ToArray(),
        "generic failure authoritative terminal suffix");
}

private static void FaultFaultRace()
{
    DriverFixture fixture = DriverFixture.Ready();
    bool firstWon = false;
    bool secondWon = false;
    Exception firstError = null;
    Exception secondError = null;
    using (ManualResetEvent gate = new ManualResetEvent(false))
    {
        Thread first = new Thread(delegate()
        {
            try
            {
                if (!gate.WaitOne(5000))
                    throw new TimeoutException("fault gate one");
                firstWon = fixture.Driver.TryFault("capture_failed");
            }
            catch (Exception error) { firstError = error; }
        });
        Thread second = new Thread(delegate()
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
}
