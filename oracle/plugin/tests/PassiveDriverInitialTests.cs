using System;
using System.Collections.Generic;

internal static class PassiveDriverInitialTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("driver-initial", "prepare activate separation",
            PrepareActivateSeparation);
        tests.Add("driver-initial", "pre epoch neutral does not leak",
            PreEpochNeutralDoesNotLeak);
        tests.Add("driver-initial", "matching pair writes initial",
            MatchingPairWritesInitial);
        tests.Add("driver-initial", "not inspected breaks pair",
            NotInspectedBreaksPair);
        tests.Add("driver-initial", "nonquiescent breaks pair",
            NonquiescentBreaksPair);
        tests.Add("driver-initial", "cardinal clears candidate",
            CardinalClearsCandidate);
        tests.Add("driver-initial", "replacement rebases same callback",
            ReplacementRebasesSameCallback);
        tests.Add("driver-initial", "exact deadline and pre overrun",
            ExactDeadlineAndPreOverrun);
    }

    private static void PrepareActivateSeparation()
    {
        IList<string> events = new List<string>();
        FakeTraceSink sink = new FakeTraceSink(events);
        FakePassiveReporter reporter = new FakePassiveReporter(events);
        Check.Throws<ArgumentNullException>(
            delegate { new PassiveUpdateBoundary(null); },
            "null boundary driver rejected");
        Check.Throws<ArgumentNullException>(
            delegate
            {
                new PassiveDriver(
                    null,
                    reporter,
                    OracleProtocol.ExpectedInputCount,
                    600,
                    30.0);
            },
            "null sink rejected");
        Check.Throws<ArgumentNullException>(
            delegate
            {
                new PassiveDriver(
                    sink,
                    null,
                    OracleProtocol.ExpectedInputCount,
                    600,
                    30.0);
            },
            "null reporter rejected");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new PassiveDriver(sink, reporter, 2, 600, 30.0);
            },
            "wrong expected count rejected");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new PassiveDriver(
                    sink,
                    reporter,
                    OracleProtocol.ExpectedInputCount,
                    1,
                    30.0);
            },
            "short frame limit rejected");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new PassiveDriver(
                    sink,
                    reporter,
                    OracleProtocol.ExpectedInputCount,
                    OracleProtocol.MaxSettleFrames + 1,
                    30.0);
            },
            "large frame limit rejected");
        AssertBadSeconds(0.0, sink, reporter, "zero seconds");
        AssertBadSeconds(-1.0, sink, reporter, "negative seconds");
        AssertBadSeconds(Double.NaN, sink, reporter, "NaN seconds");
        AssertBadSeconds(
            Double.PositiveInfinity,
            sink,
            reporter,
            "infinite seconds");

        DriverFixture nullRun = DriverFixture.Unprepared();
        Check.Throws<ArgumentNullException>(
            delegate { nullRun.Driver.Prepare(null); },
            "null Run rejected");
        Check.Equal(0, nullRun.Sink.RunCalls,
            "null Run never reaches sink");
        Check.Throws<ArgumentNullException>(
            delegate { nullRun.Boundary.Observe(null); },
            "null observation rejected while inactive");

        DriverFixture fixture = DriverFixture.Unprepared();
        Check.Equal(
            PassivePhase.Disabled,
            fixture.Driver.Phase,
            "constructor phase");
        Check.False(fixture.Driver.Activate(), "activation needs run");
        Check.True(
            fixture.Driver.Prepare(ProtocolSamples.Run),
            "first prepare");
        Check.Same(
            ProtocolSamples.Run,
            fixture.Sink.RunRecords[0],
            "prepared run identity");
        Check.Equal(
            ProtocolSamples.Run.StartedAtUtc,
            fixture.Driver.StartedAtUtc,
            "started timestamp retained after flush");
        Check.Sequence(
            new string[] { "sink:run" },
            fixture.Events.ToArray(),
            "prepare writes before any report");
        Check.False(
            fixture.Driver.Prepare(ProtocolSamples.Run),
            "prepare is one shot");
        Check.True(fixture.Driver.Activate(), "first activate");
        Check.False(fixture.Driver.Activate(), "activate is one shot");
        Check.Equal(
            PassivePhase.AwaitGame,
            fixture.Driver.Phase,
            "activated phase");
        AssertNoStepOrEnd(fixture, "initial lifecycle");

        DriverFixture disabledBeforeActivation =
            DriverFixture.Unprepared();
        Check.True(
            disabledBeforeActivation.Driver.Prepare(ProtocolSamples.Run),
            "prepare before disable");
        disabledBeforeActivation.Driver.Disable();
        Check.False(
            disabledBeforeActivation.Driver.Activate(),
            "disable prevents first activation");

        AssertPrepareFailureIsMarkerOnly();
        AssertDisableDisposeAndLateCallbacks();
    }

    private static void PreEpochNeutralDoesNotLeak()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Neutral();
        FakeUpdateObservation first = fixture.Observe(
            fixture.State,
            fixture.State,
            1.0,
            true,
            ProtocolSamples.Capture("pre-neutral"));
        Check.Equal(0, first.GateCalls, "old neutral skips gate");
        Check.Equal(0, first.CaptureCalls, "old neutral skips capture");
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            2.0,
            true,
            ProtocolSamples.Capture("new-neutral"));
        Check.Equal(
            0,
            fixture.Sink.InitialRecords.Count,
            "one new-epoch sample is not enough");
        fixture.Observe(
            fixture.State,
            fixture.State,
            3.0,
            true,
            ProtocolSamples.Capture("new-neutral"));
        Check.Equal(
            1,
            fixture.Sink.InitialRecords.Count,
            "new epoch neutral enables pair");

        DriverFixture lateUsable = DriverFixture.Active();
        FakeUpdateObservation becameUsable = lateUsable.Observe(
            null,
            false,
            lateUsable.State,
            true,
            4.0,
            true,
            ProtocolSamples.InitialCapture);
        UpdateDirective started = lateUsable.Boundary.LastDirective;
        Check.True(started != null && started.Active,
            "late usable directive active");
        Check.Equal(1, started.SettleFrames,
            "verified usable state starts frame one");
        Check.False(started.InspectGate,
            "new same-callback epoch is not inspected");
        Check.False(started.TimeoutAfterSample,
            "new same-callback epoch has fresh deadline");
        Check.Equal(0, becameUsable.GateCalls,
            "verified usable callback skips gate");
        Check.Equal(
            PassivePhase.AwaitInitialNeutral,
            lateUsable.Driver.Phase,
            "verified usable starts epoch");

        DriverFixture lost = DriverFixture.Active();
        FakeUpdateObservation becameUnusable = lost.Observe(
            lost.State,
            true,
            null,
            false,
            5.0,
            true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            PassivePhase.AwaitGame,
            lost.Driver.Phase,
            "verified unusable returns to AwaitGame");
        Check.Equal(0, lost.Driver.CurrentSettleFrames,
            "unusable reset clears frames");
        Check.Equal(0, becameUnusable.GateCalls,
            "unusable callback skips gate");
        Check.Equal(0, lost.Boundary.LastDirective.SettleFrames,
            "unusable directive rebases to frame zero");

        DriverFixture reset = CandidateFixture("reset-old");
        FakeUpdateObservation resetToAwaitGame = reset.Observe(
            reset.State,
            true,
            null,
            false,
            2.0,
            true,
            ProtocolSamples.Capture("ignored"));
        Check.Equal(0, resetToAwaitGame.GateCalls,
            "verified unusable skips old neutral gate");
        Check.Equal(
            PassivePhase.AwaitGame,
            reset.Driver.Phase,
            "verified unusable clears populated epoch");
        FakeUpdateObservation resetReentry = reset.Observe(
            null,
            false,
            reset.OtherState,
            true,
            29.0,
            true,
            ProtocolSamples.Capture("ignored"));
        Check.Equal(0, resetReentry.GateCalls,
            "reentry does not inherit old neutral");
        Check.Equal(1, reset.Boundary.LastDirective.SettleFrames,
            "reentry begins at frame one");
        FakeUpdateObservation resetFailure = reset.NewObservation(
            reset.OtherState,
            true,
            reset.OtherState,
            true,
            30.0,
            true,
            ProtocolSamples.Capture("ignored"));
        resetFailure.PathFailure =
            new InvalidOperationException("after reset");
        reset.Boundary.Observe(resetFailure);
        AssertFaultCode(
            reset,
            "observer_exception",
            "fault after unusable reset");
        Check.True(
            reset.Sink.ErrorRecords[0].LastCapture == null,
            "unusable reset clears old last_capture");

        DriverFixture nullUsable = DriverFixture.Active();
        nullUsable.Observe(
            null,
            true,
            null,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        AssertFaultCode(
            nullUsable,
            "capture_failed",
            "usable null state faults");

        DriverFixture backwards = DriverFixture.Active();
        backwards.Observe(
            backwards.State,
            backwards.State,
            2.0,
            true,
            ProtocolSamples.InitialCapture);
        FakeUpdateObservation oldTime = backwards.NewObservation(
            backwards.State,
            true,
            backwards.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        backwards.Boundary.Observe(oldTime);
        Check.Equal(0, oldTime.PathCalls,
            "backwards time faults before path");
        AssertFaultCode(
            backwards,
            "observer_exception",
            "backwards monotonic time faults");
    }

    private static void MatchingPairWritesInitial()
    {
        DriverFixture equal = DriverFixture.Active();
        equal.Observe(
            equal.State,
            equal.State,
            0.0,
            true,
            ProtocolSamples.Capture("epoch"));
        equal.Neutral();
        equal.Events.Clear();
        CaptureRecord firstValue = ProtocolSamples.Capture("equal-value");
        CaptureRecord secondValue = ProtocolSamples.Capture("equal-value");
        Check.False(
            Object.ReferenceEquals(firstValue, secondValue),
            "equal captures are distinct objects");
        FakeUpdateObservation firstEqual = equal.Observe(
            equal.State,
            equal.State,
            1.0,
            true,
            firstValue);
        Check.True(firstEqual.GateSawAuthorized,
            "authorization precedes gate inspection");
        Check.Sequence(
            new string[]
            {
                "observer:state:begin",
                "observer:time",
                "observer:path",
                "observer:state:verified",
                "observer:gate",
                "observer:capture",
                "observer:utc"
            },
            equal.Events.ToArray(),
            "authorized sample order");
        equal.Events.Clear();
        equal.Observe(
            equal.State,
            equal.State,
            2.0,
            true,
            secondValue);
        Check.Sequence(
            new string[]
            {
                "observer:state:begin",
                "observer:time",
                "observer:path",
                "observer:state:verified",
                "observer:gate",
                "observer:capture",
                "observer:utc",
                "sink:initial",
                "report:ready:0/3"
            },
            equal.Events.ToArray(),
            "Initial flush precedes Ready");
        Check.Equal(
            PassivePhase.Ready,
            equal.Driver.Phase,
            "equal signatures settle");
        Check.Same(
            secondValue,
            equal.Sink.InitialRecords[0].Capture,
            "second complete capture is emitted");
        AssertNoStepOrEnd(equal, "initial settle");

        DriverFixture unequal = DriverFixture.Active();
        unequal.Observe(
            unequal.State,
            unequal.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        unequal.Neutral();
        unequal.Observe(
            unequal.State,
            unequal.State,
            1.0,
            true,
            ProtocolSamples.Capture("signature-a"));
        unequal.Observe(
            unequal.State,
            unequal.State,
            2.0,
            true,
            ProtocolSamples.Capture("signature-b"));
        Check.Equal(
            0,
            unequal.Sink.InitialRecords.Count,
            "any two captures do not settle");
        unequal.Observe(
            unequal.State,
            unequal.State,
            3.0,
            true,
            ProtocolSamples.Capture("signature-b"));
        Check.Equal(
            1,
            unequal.Sink.InitialRecords.Count,
            "later equal consecutive signatures settle");

        DriverFixture completeSignature = DriverFixture.Active();
        completeSignature.Observe(
            completeSignature.State,
            completeSignature.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        completeSignature.Neutral();
        CaptureRecord oneMovement = new CaptureRecord(
            "same-raw-save", "17", "", false, false, false, false,
            "", "", 0, 1, 0);
        CaptureRecord twoMovements = new CaptureRecord(
            "same-raw-save", "17", "", false, false, false, false,
            "", "", 0, 2, 0);
        CaptureRecord twoMovementsAgain = new CaptureRecord(
            "same-raw-save", "17", "", false, false, false, false,
            "", "", 0, 2, 0);
        completeSignature.Observe(
            completeSignature.State,
            completeSignature.State,
            1.0,
            true,
            oneMovement);
        completeSignature.Observe(
            completeSignature.State,
            completeSignature.State,
            2.0,
            true,
            twoMovements);
        Check.Equal(
            0,
            completeSignature.Sink.InitialRecords.Count,
            "same raw save with unequal complete signature does not settle");
        completeSignature.Observe(
            completeSignature.State,
            completeSignature.State,
            3.0,
            true,
            twoMovementsAgain);
        Check.Equal(
            1,
            completeSignature.Sink.InitialRecords.Count,
            "complete signature equality settles");

        AssertReadyFailureOccursAfterInitial();
    }

    private static void NotInspectedBreaksPair()
    {
        DriverFixture control = CandidateFixture("gap-control");
        control.Observe(
            control.State,
            control.State,
            2.0,
            true,
            ProtocolSamples.Capture("gap-control"));
        Check.Equal(
            1,
            control.Sink.InitialRecords.Count,
            "candidate fixture settles without defensive seed");

        DriverFixture fixture = CandidateFixture("gap-value");
        fixture.SetNeutralSeenForDefensiveTest(false);
        FakeUpdateObservation skipped = fixture.Observe(
            fixture.State,
            fixture.State,
            2.0,
            true,
            ProtocolSamples.Capture("gap-value"));
        Check.Equal(0, skipped.GateCalls,
            "NotInspected does not call gate");
        Check.Equal(0, skipped.CaptureCalls,
            "NotInspected does not capture");
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            3.0,
            true,
            ProtocolSamples.Capture("gap-value"));
        Check.Equal(
            0,
            fixture.Sink.InitialRecords.Count,
            "NotInspected cleared candidate");
        fixture.Observe(
            fixture.State,
            fixture.State,
            4.0,
            true,
            ProtocolSamples.Capture("gap-value"));
        Check.Equal(
            1,
            fixture.Sink.InitialRecords.Count,
            "new pair settles after NotInspected");
    }

    private static void NonquiescentBreaksPair()
    {
        DriverFixture fixture = CandidateFixture("quiet-value");
        FakeUpdateObservation blocked = fixture.Observe(
            fixture.State,
            fixture.State,
            2.0,
            false,
            ProtocolSamples.Capture("quiet-value"));
        Check.Equal(1, blocked.GateCalls,
            "nonquiescent callback inspects gate");
        Check.Equal(0, blocked.CaptureCalls,
            "nonquiescent callback cannot capture");
        fixture.Observe(
            fixture.State,
            fixture.State,
            3.0,
            true,
            ProtocolSamples.Capture("quiet-value"));
        Check.Equal(
            0,
            fixture.Sink.InitialRecords.Count,
            "nonquiescent sample cleared candidate");
        fixture.Observe(
            fixture.State,
            fixture.State,
            4.0,
            true,
            ProtocolSamples.Capture("quiet-value"));
        Check.Equal(
            1,
            fixture.Sink.InitialRecords.Count,
            "new pair settles after nonquiescent sample");

        AssertPathAndAuthorizationOrder();
        AssertBoundaryExceptionFirewall();
    }

    private static void CardinalClearsCandidate()
    {
        DriverFixture fixture = CandidateFixture("cardinal-value");
        fixture.CardinalOnly(3);
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            2.0,
            true,
            ProtocolSamples.Capture("cardinal-value"));
        Check.Equal(
            0,
            fixture.Sink.InitialRecords.Count,
            "cardinal input cleared candidate");
        fixture.Observe(
            fixture.State,
            fixture.State,
            3.0,
            true,
            ProtocolSamples.Capture("cardinal-value"));
        Check.Equal(
            1,
            fixture.Sink.InitialRecords.Count,
            "new pair settles after cardinal input");

        DriverFixture neutralReset = DriverFixture.Active();
        neutralReset.Observe(
            neutralReset.State,
            neutralReset.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        neutralReset.Neutral();
        neutralReset.CardinalOnly(3);
        neutralReset.Observe(
            neutralReset.State,
            neutralReset.State,
            1.0,
            true,
            ProtocolSamples.Capture("neutral-reset"));
        neutralReset.Observe(
            neutralReset.State,
            neutralReset.State,
            2.0,
            true,
            ProtocolSamples.Capture("neutral-reset"));
        Check.Equal(
            0,
            neutralReset.Sink.InitialRecords.Count,
            "cardinal input cleared neutral eligibility");
        neutralReset.Neutral();
        neutralReset.Observe(
            neutralReset.State,
            neutralReset.State,
            3.0,
            true,
            ProtocolSamples.Capture("neutral-reset"));
        neutralReset.Observe(
            neutralReset.State,
            neutralReset.State,
            4.0,
            true,
            ProtocolSamples.Capture("neutral-reset"));
        Check.Equal(
            1,
            neutralReset.Sink.InitialRecords.Count,
            "new pair settles after a fresh neutral");

        AssertDirectiveOwnership();
        AssertPlayerPollScopeRules();
        AssertTerminalOrderingAndFailureFallbacks();
    }

    private static void ReplacementRebasesSameCallback()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State,
            fixture.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        long oldEpoch = fixture.Boundary.LastDirective.Epoch;
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            1.0,
            true,
            ProtocolSamples.Capture("replacement-candidate"));

        FakeUpdateObservation replacement = fixture.Observe(
            fixture.State,
            true,
            fixture.OtherState,
            true,
            29.0,
            true,
            ProtocolSamples.Capture("replacement-candidate"));
        UpdateDirective rebased = fixture.Boundary.LastDirective;
        Check.True(rebased.Epoch > oldEpoch,
            "replacement directive uses new epoch");
        Check.Equal(1, rebased.SettleFrames,
            "replacement callback is frame one");
        Check.False(rebased.InspectGate,
            "replacement clears neutral eligibility");
        Check.False(rebased.TimeoutAfterSample,
            "replacement resets post-sample timeout");
        Check.Equal(0, replacement.GateCalls,
            "replacement callback skips gate");
        Check.Equal(0, replacement.CaptureCalls,
            "replacement callback skips capture");
        Check.Equal(
            PassivePhase.AwaitInitialNeutral,
            fixture.Driver.Phase,
            "replacement starts new initial epoch");
        FakeUpdateObservation noNeutral = fixture.Observe(
            fixture.OtherState,
            fixture.OtherState,
            30.0,
            true,
            ProtocolSamples.Capture("replacement-candidate"));
        Check.Equal(0, noNeutral.GateCalls,
            "replacement neutral does not leak to next callback");
        Check.Equal(0, noNeutral.CaptureCalls,
            "replacement needs a new neutral poll");
        fixture.Neutral();
        fixture.Observe(
            fixture.OtherState,
            fixture.OtherState,
            31.0,
            true,
            ProtocolSamples.Capture("replacement-candidate"));
        Check.Equal(
            0,
            fixture.Sink.InitialRecords.Count,
            "replacement cleared old candidate and old deadline");
        fixture.Observe(
            fixture.OtherState,
            fixture.OtherState,
            32.0,
            true,
            ProtocolSamples.Capture("replacement-candidate"));
        Check.Equal(
            1,
            fixture.Sink.InitialRecords.Count,
            "new epoch pair settles inside reset deadline");

        DriverFixture candidate =
            CandidateFixture("same-after-replacement");
        UpdateDirective candidateReplacement =
            candidate.Driver.BeginUpdate(
                candidate.State, true, 2.0);
        Check.True(
            candidate.Driver.AuthorizeUpdate(
                candidateReplacement,
                candidate.OtherState,
                true,
                true),
            "candidate replacement authorizes");
        candidate.AssertCandidateClearedForDefensiveTest(
            "replacement clears a value-equal old candidate");
        candidate.Driver.CompleteUpdate(
            candidateReplacement,
            GateSample.NotInspected(),
            DriverFixture.UtcFinish);
        candidate.Neutral();
        candidate.Observe(
            candidate.OtherState,
            candidate.OtherState,
            3.0,
            true,
            ProtocolSamples.Capture("same-after-replacement"));
        Check.Equal(
            0,
            candidate.Sink.InitialRecords.Count,
            "replacement candidate starts a fresh pair");
        candidate.Observe(
            candidate.OtherState,
            candidate.OtherState,
            4.0,
            true,
            ProtocolSamples.Capture("same-after-replacement"));
        Check.Equal(
            1,
            candidate.Sink.InitialRecords.Count,
            "fresh replacement pair settles");

        DriverFixture last = CandidateFixture("old-last");
        last.Observe(
            last.State,
            true,
            last.OtherState,
            true,
            2.0,
            true,
            ProtocolSamples.Capture("ignored"));
        FakeUpdateObservation afterReplacement = last.NewObservation(
            last.OtherState,
            true,
            last.OtherState,
            true,
            3.0,
            true,
            ProtocolSamples.Capture("new"));
        afterReplacement.PathFailure =
            new InvalidOperationException("path observer");
        last.Boundary.Observe(afterReplacement);
        AssertFaultCode(
            last,
            "observer_exception",
            "fault after replacement");
        Check.True(
            last.Sink.ErrorRecords[0].LastCapture == null,
            "replacement cleared old last_capture");
    }

    private static void ExactDeadlineAndPreOverrun()
    {
        AssertExactFrameSuccessAndFailure();
        AssertExactTimeSuccessAndFailure();
        AssertPreOverrunsAndFrameCap();
        AssertCaptureRecordFailures();
    }

    private static void AssertBadSeconds(
        double value,
        ITraceSink sink,
        IPassiveReporter reporter,
        string label)
    {
        Check.Throws<ArgumentOutOfRangeException>(
            delegate
            {
                new PassiveDriver(
                    sink,
                    reporter,
                    OracleProtocol.ExpectedInputCount,
                    600,
                    value);
            },
            label);
    }

    private static DriverFixture CandidateFixture(string rawSave)
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State,
            fixture.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            1.0,
            true,
            ProtocolSamples.Capture(rawSave));
        return fixture;
    }

    private static void AssertPrepareFailureIsMarkerOnly()
    {
        DriverFixture fixture = DriverFixture.Unprepared();
        fixture.Sink.RunFailure =
            new TraceIoException("run write failed");
        Check.False(
            fixture.Driver.Prepare(ProtocolSamples.Run),
            "failed prepare returns false");
        Check.Equal(
            PassivePhase.Faulted,
            fixture.Driver.Phase,
            "failed prepare is terminal");
        Check.Equal(0, fixture.Sink.RunRecords.Count,
            "failed Run is not durable");
        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
            "failed Run cannot claim durable Error");
        Check.Equal(default(DateTime), fixture.Driver.StartedAtUtc,
            "failed Run does not publish start time");
        Check.Equal(1, fixture.Sink.CloseCalls,
            "prepare failure closes once");
        Check.Sequence(
            new string[] { "trace_io_failed" },
            fixture.Reporter.FailedCodes.ToArray(),
            "prepare failure marker");
        Check.False(fixture.Driver.Activate(),
            "failed prepare cannot activate");
        Check.False(fixture.Driver.Prepare(ProtocolSamples.Run),
            "failed prepare cannot retry");
        Check.Equal(1, fixture.Sink.RunCalls,
            "failed prepare writes Run at most once");
    }

    private static void AssertDisableDisposeAndLateCallbacks()
    {
        DriverFixture fixture = DriverFixture.Active();
        HookToken pending = fixture.Driver.PlayerPollEntered();
        fixture.Driver.Disable();
        fixture.Driver.Disable();
        FakeUpdateObservation late = fixture.NewObservation(
            fixture.State,
            true,
            fixture.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        fixture.Boundary.Observe(late);
        Check.Equal(0, late.StateCalls,
            "disabled boundary is inert before observer access");
        fixture.Driver.PhysicalPollReturned(8);
        fixture.Driver.PlayerPollReturned(pending);
        fixture.Driver.PlayerPollThrew(pending);
        Check.False(
            fixture.Driver.TryFault("observer_exception"),
            "disabled driver rejects faults");
        fixture.Driver.Dispose();
        fixture.Driver.Dispose();
        Check.Equal(1, fixture.Sink.CloseCalls,
            "Dispose closes at most once");
        Check.Equal(0, fixture.Sink.ErrorCalls,
            "late callbacks write no Error");
        Check.Equal(0, fixture.Reporter.FailedCalls,
            "late callbacks write no marker");

        DriverFixture disposed = DriverFixture.Unprepared();
        disposed.Driver.Dispose();
        Check.False(
            disposed.Driver.Prepare(ProtocolSamples.Run),
            "disposed driver cannot prepare");
        Check.False(disposed.Driver.Activate(),
            "disposed driver cannot activate");
        Check.Equal(1, disposed.Sink.CloseCalls,
            "pre-prepare disposal closes once");
        FakeUpdateObservation afterDispose = disposed.NewObservation(
            disposed.State,
            true,
            disposed.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        disposed.Boundary.Observe(afterDispose);
        Check.Equal(0, afterDispose.StateCalls,
            "disposed boundary is inert before observer access");
        Check.False(disposed.Driver.PlayerPollEntered().Active,
            "disposed poll entry is inert");

        DriverFixture closeFailure = DriverFixture.Active();
        closeFailure.Sink.CloseFailure =
            new TraceIoException("dispose close failed");
        closeFailure.Driver.Dispose();
        closeFailure.Driver.Dispose();
        Check.Equal(1, closeFailure.Sink.CloseCalls,
            "failed Dispose close is not retried");
        Check.Equal(1, closeFailure.Reporter.DiagnosticCalls,
            "Dispose close failure is diagnostic");
        Check.Equal(0, closeFailure.Reporter.FailedCalls,
            "Dispose close failure invents no terminal marker");
    }

    private static void AssertReadyFailureOccursAfterInitial()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Reporter.ReadyFailure =
            new InvalidOperationException("ready failed");
        fixture.Observe(
            fixture.State,
            fixture.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            1.0,
            true,
            ProtocolSamples.Capture("ready-failure"));
        fixture.Events.Clear();
        fixture.Observe(
            fixture.State,
            fixture.State,
            2.0,
            true,
            ProtocolSamples.Capture("ready-failure"));
        Check.Sequence(
            new string[]
            {
                "observer:state:begin",
                "observer:time",
                "observer:path",
                "observer:state:verified",
                "observer:gate",
                "observer:capture",
                "observer:utc",
                "sink:initial",
                "report:ready:0/3",
                "sink:error:observer_exception",
                "sink:close",
                "report:failed:observer_exception"
            },
            fixture.Events.ToArray(),
            "Ready failure follows durable Initial");
        AssertFaultCode(
            fixture,
            "observer_exception",
            "Ready failure classification");
        Check.True(
            fixture.Sink.ErrorRecords[0].LastCapture == null,
            "completed Initial is not error last_capture");
    }

    private static void AssertPathAndAuthorizationOrder()
    {
        DriverFixture path = DriverFixture.Active();
        FakeUpdateObservation changed = path.NewObservation(
            path.State,
            true,
            path.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        changed.SavePathMatches = false;
        path.Boundary.Observe(changed);
        Check.Equal(1, changed.StateCalls,
            "false path skips verified identity");
        Check.Equal(0, changed.GateCalls,
            "false path skips gate");
        Check.Equal(0, changed.CaptureCalls,
            "false path skips capture");
        Check.Sequence(
            new string[]
            {
                "sink:run",
                "observer:state:begin",
                "observer:time",
                "observer:path",
                "sink:error:save_path_changed",
                "sink:close",
                "report:failed:save_path_changed"
            },
            path.Events.ToArray(),
            "path authorization precedes identity and gate");
        AssertFaultCode(path, "save_path_changed", "path mismatch code");
    }

    private static void AssertBoundaryExceptionFirewall()
    {
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.FirstStateFailure =
                    new InvalidOperationException("begin state");
            },
            "observer_exception",
            "begin state exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.NowFailure =
                    new InvalidOperationException("monotonic clock");
            },
            "observer_exception",
            "monotonic clock exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.PathFailure =
                    new InvalidOperationException("path");
            },
            "observer_exception",
            "path exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.PathFailure =
                    new CaptureException("typed path");
            },
            "capture_failed",
            "typed path exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.SecondStateFailure =
                    new InvalidOperationException("verified state");
            },
            "observer_exception",
            "verified state exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.SecondStateFailure =
                    new CaptureException("typed verified state");
            },
            "capture_failed",
            "typed verified-state exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.UtcFailure =
                    new InvalidOperationException("UTC");
            },
            "observer_exception",
            "UTC exception");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.UtcFailure =
                    new CaptureException("typed UTC capture");
            },
            "capture_failed",
            "typed UTC capture exception");
        DriverFixture nonUtc = DriverFixture.Active();
        FakeUpdateObservation invalidUtc = nonUtc.NewObservation(
            nonUtc.State,
            true,
            nonUtc.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        invalidUtc.Utc = DateTime.SpecifyKind(
            DriverFixture.UtcFinish,
            DateTimeKind.Local);
        nonUtc.Boundary.Observe(invalidUtc);
        AssertFaultCode(
            nonUtc,
            "observer_exception",
            "non-UTC boundary value");
        AssertEarlyBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.FirstStateFailure =
                    new CaptureException("capture typed begin");
            },
            "capture_failed",
            "typed capture exception is preserved");

        AssertEligibleBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.GateFailure =
                    new InvalidOperationException("gate");
            },
            "observer_exception",
            "gate exception");
        AssertEligibleBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.CaptureFailure =
                    new CaptureException("capture");
            },
            "capture_failed",
            "capture exception");
        AssertEligibleBoundaryFailure(
            delegate(FakeUpdateObservation observation)
            {
                observation.CaptureFailure =
                    new InvalidOperationException("capture generic");
            },
            "observer_exception",
            "generic capture exception");
    }

    private static void AssertEarlyBoundaryFailure(
        Action<FakeUpdateObservation> configure,
        string expectedCode,
        string label)
    {
        DriverFixture fixture = DriverFixture.Active();
        FakeUpdateObservation observation = fixture.NewObservation(
            fixture.State,
            true,
            fixture.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        configure(observation);
        fixture.Boundary.Observe(observation);
        AssertFaultCode(fixture, expectedCode, label);
    }

    private static void AssertEligibleBoundaryFailure(
        Action<FakeUpdateObservation> configure,
        string expectedCode,
        string label)
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State,
            fixture.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        FakeUpdateObservation observation = fixture.NewObservation(
            fixture.State,
            true,
            fixture.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        configure(observation);
        fixture.Boundary.Observe(observation);
        AssertFaultCode(fixture, expectedCode, label);
    }

    private static void AssertDirectiveOwnership()
    {
        DriverFixture owner = DriverFixture.Active();
        DriverFixture foreignOwner = DriverFixture.Active();
        UpdateDirective owned = owner.Driver.BeginUpdate(
            owner.State, true, 0.0);
        UpdateDirective foreign = foreignOwner.Driver.BeginUpdate(
            foreignOwner.State, true, 0.0);
        Check.Throws<InvalidOperationException>(
            delegate
            {
                owner.Driver.AuthorizeUpdate(
                    foreign,
                    owner.State,
                    true,
                    true);
            },
            "foreign directive cannot authorize");
        Check.True(
            owner.Driver.AuthorizeUpdate(
                owned,
                owner.State,
                true,
                true),
            "owned directive authorizes");
        Check.Throws<InvalidOperationException>(
            delegate
            {
                owner.Driver.AuthorizeUpdate(
                    owned,
                    owner.State,
                    true,
                    true);
            },
            "duplicate authorization rejected");
        owner.Driver.CompleteUpdate(
            owned,
            GateSample.NotInspected(),
            DriverFixture.UtcFinish);
        Check.Throws<InvalidOperationException>(
            delegate
            {
                owner.Driver.CompleteUpdate(
                    owned,
                    GateSample.NotInspected(),
                    DriverFixture.UtcFinish);
            },
            "duplicate completion rejected");
        foreignOwner.Driver.FailUpdate(
            foreign,
            "observer_exception");
        Check.Throws<InvalidOperationException>(
            delegate
            {
                foreignOwner.Driver.FailUpdate(
                    foreign,
                    "observer_exception");
            },
            "duplicate failure rejected");
    }

    private static void AssertPlayerPollScopeRules()
    {
        DriverFixture cleanup = DriverFixture.Active();
        HookToken cleanupToken = cleanup.Driver.PlayerPollEntered();
        Check.True(cleanupToken.Active, "cleanup poll token active");
        cleanup.Driver.PlayerPollThrew(cleanupToken);
        HookToken afterCleanup = cleanup.Driver.PlayerPollEntered();
        Check.True(afterCleanup.Active, "throw cleanup releases poll scope");
        cleanup.Driver.PlayerPollReturned(afterCleanup);

        DriverFixture unscoped = DriverFixture.Active();
        unscoped.Driver.PhysicalPollReturned(8);
        AssertFaultCode(
            unscoped,
            "hook_order_mismatch",
            "unscoped physical poll faults");

        DriverFixture duplicate = DriverFixture.Active();
        HookToken duplicateToken = duplicate.Driver.PlayerPollEntered();
        duplicate.Driver.PhysicalPollReturned(8);
        duplicate.Driver.PhysicalPollReturned(8);
        duplicate.Driver.PlayerPollReturned(duplicateToken);
        AssertFaultCode(
            duplicate,
            "hook_order_mismatch",
            "duplicate physical poll faults");

        DriverFixture nested = DriverFixture.Active();
        HookToken outer = nested.Driver.PlayerPollEntered();
        HookToken inner = nested.Driver.PlayerPollEntered();
        Check.False(inner.Active, "nested poll receives inert token");
        nested.Driver.PlayerPollReturned(outer);
        AssertFaultCode(
            nested,
            "hook_order_mismatch",
            "nested player poll faults");
    }

    private static void AssertTerminalOrderingAndFailureFallbacks()
    {
        DriverFixture observer = DriverFixture.Active();
        observer.Driver.ObserverFailed();
        AssertFaultCode(
            observer,
            "observer_exception",
            "observer failure entrypoint");
        observer.Driver.ObserverFailed();
        Check.Equal(1, observer.Sink.ErrorCalls,
            "repeated observer failure writes one Error");
        Check.Equal(1, observer.Sink.CloseCalls,
            "repeated observer failure closes once");
        Check.Equal(1, observer.Reporter.FailedCalls,
            "repeated observer failure reports once");

        DriverFixture ordered = DriverFixture.Active();
        ordered.Events.Clear();
        Check.True(
            ordered.Driver.TryFault("observer_exception"),
            "first fault wins");
        Check.False(
            ordered.Driver.TryFault("capture_failed"),
            "second fault loses");
        ordered.Driver.Dispose();
        Check.Sequence(
            new string[]
            {
                "sink:error:observer_exception",
                "sink:close",
                "report:failed:observer_exception"
            },
            ordered.Events.ToArray(),
            "Error then close then marker");
        FakeUpdateObservation afterFault = ordered.NewObservation(
            ordered.State,
            true,
            ordered.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        ordered.Boundary.Observe(afterFault);
        Check.Equal(0, afterFault.StateCalls,
            "faulted boundary is inert before observer access");
        Check.False(ordered.Driver.PlayerPollEntered().Active,
            "faulted poll entry is inert");
        Check.Equal(1, ordered.Sink.ErrorCalls,
            "terminal writes one Error");
        Check.Equal(1, ordered.Sink.CloseCalls,
            "terminal closes once");
        Check.Equal(1, ordered.Reporter.FailedCalls,
            "terminal reports once");

        DriverFixture errorWrite = DriverFixture.Active();
        errorWrite.Sink.ErrorFailure =
            new TraceIoException("error write failed");
        errorWrite.Events.Clear();
        errorWrite.Driver.TryFault("observer_exception");
        Check.Equal(0, errorWrite.Sink.ErrorRecords.Count,
            "failed Error write is not durable");
        Check.Equal(1, errorWrite.Sink.ErrorCalls,
            "failed Error write attempted once");
        Check.Equal(1, errorWrite.Sink.CloseCalls,
            "failed Error write still closes");
        Check.Equal(1, errorWrite.Reporter.FailedCalls,
            "failed Error write reports once");
        Check.Equal(1, errorWrite.Reporter.DiagnosticCalls,
            "failed Error write diagnoses once");
        Check.Sequence(
            new string[] { "trace_io_failed" },
            errorWrite.Reporter.FailedCodes.ToArray(),
            "Error write failure uses trace marker");

        DriverFixture close = DriverFixture.Active();
        close.Sink.CloseFailure =
            new TraceIoException("terminal close failed");
        close.Events.Clear();
        close.Driver.TryFault("capture_failed");
        Check.Equal(1, close.Sink.ErrorRecords.Count,
            "Error may remain after close failure");
        Check.Equal(1, close.Sink.ErrorCalls,
            "close failure writes Error once");
        Check.Equal("capture_failed",
            close.Sink.ErrorRecords[0].Code,
            "durable bytes retain original code");
        Check.Equal(1, close.Sink.CloseCalls,
            "failed close is not retried");
        Check.Equal(1, close.Reporter.FailedCalls,
            "close failure reports once");
        Check.Equal(1, close.Reporter.DiagnosticCalls,
            "close failure diagnoses once");
        Check.Sequence(
            new string[] { "trace_io_failed" },
            close.Reporter.FailedCodes.ToArray(),
            "close failure marker is authoritative trace failure");

        DriverFixture reporter = DriverFixture.Active();
        reporter.Reporter.FailedFailure =
            new InvalidOperationException("failed marker");
        reporter.Reporter.DiagnosticFailure =
            new InvalidOperationException("diagnostic marker");
        reporter.Driver.TryFault("observer_exception");
        Check.Equal(1, reporter.Reporter.FailedCalls,
            "failure marker attempted once");
        Check.Equal(1, reporter.Sink.ErrorCalls,
            "reporter failure leaves one Error attempt");
        Check.Equal(1, reporter.Sink.ErrorRecords.Count,
            "reporter failure leaves one durable Error");
        Check.Equal(1, reporter.Reporter.DiagnosticCalls,
            "failure-marker exception gets one diagnostic attempt");
        Check.Equal(1, reporter.Sink.CloseCalls,
            "reporter failures do not disturb close ownership");
    }

    private static void AssertExactFrameSuccessAndFailure()
    {
        DriverFixture success = DriverFixture.Active(4, 30.0);
        success.Observe(
            success.State,
            success.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        success.Neutral();
        FakeUpdateObservation blocked = success.Observe(
            success.State,
            success.State,
            1.0,
            false,
            ProtocolSamples.InitialCapture);
        Check.Equal(0, blocked.CaptureCalls,
            "frame two nonquiescent does not capture");
        success.Observe(
            success.State,
            success.State,
            2.0,
            true,
            ProtocolSamples.Capture("frame-limit"));
        success.Observe(
            success.State,
            success.State,
            3.0,
            true,
            ProtocolSamples.Capture("frame-limit"));
        Check.Equal(
            PassivePhase.Ready,
            success.Driver.Phase,
            "matching pair wins at exact frame limit");

        DriverFixture failure = DriverFixture.Active(3, 30.0);
        failure.Observe(
            failure.State,
            failure.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        failure.Neutral();
        failure.Observe(
            failure.State,
            failure.State,
            1.0,
            true,
            ProtocolSamples.Capture("frame-a"));
        FakeUpdateObservation exact = failure.Observe(
            failure.State,
            failure.State,
            2.0,
            true,
            ProtocolSamples.Capture("frame-b"));
        Check.Equal(1, exact.CaptureCalls,
            "exact frame limit samples before timeout");
        AssertFaultCode(
            failure,
            "initial_settle_timeout",
            "unsuccessful exact frame times out");
        Check.Equal(3,
            failure.Sink.ErrorRecords[0].SettleFrames,
            "exact frame error count");
        Check.Equal(
            "frame-b",
            failure.Sink.ErrorRecords[0].LastCapture.RawSave,
            "exact frame timeout retains newest complete capture");
    }

    private static void AssertExactTimeSuccessAndFailure()
    {
        DriverFixture success = DriverFixture.Active();
        success.Observe(
            success.State,
            success.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        success.Neutral();
        success.Observe(
            success.State,
            success.State,
            29.0,
            true,
            ProtocolSamples.Capture("time-limit"));
        success.Observe(
            success.State,
            success.State,
            30.0,
            true,
            ProtocolSamples.Capture("time-limit"));
        Check.Equal(
            PassivePhase.Ready,
            success.Driver.Phase,
            "matching pair wins at exact time limit");

        DriverFixture failure = DriverFixture.Active();
        failure.Observe(
            failure.State,
            failure.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        failure.Neutral();
        failure.Observe(
            failure.State,
            failure.State,
            29.0,
            true,
            ProtocolSamples.Capture("time-a"));
        FakeUpdateObservation exact = failure.Observe(
            failure.State,
            failure.State,
            30.0,
            true,
            ProtocolSamples.Capture("time-b"));
        Check.Equal(1, exact.CaptureCalls,
            "exact time limit samples before timeout");
        AssertFaultCode(
            failure,
            "initial_settle_timeout",
            "unsuccessful exact time times out");
        Check.Equal(
            "time-b",
            failure.Sink.ErrorRecords[0].LastCapture.RawSave,
            "exact time timeout retains newest complete capture");
    }

    private static void AssertPreOverrunsAndFrameCap()
    {
        DriverFixture time = DriverFixture.Active();
        time.Observe(
            time.State,
            time.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        FakeUpdateObservation late = time.NewObservation(
            time.State,
            true,
            time.State,
            true,
            30.000001,
            true,
            ProtocolSamples.InitialCapture);
        time.Boundary.Observe(late);
        Check.Equal(0, late.PathCalls,
            "time pre-overrun precedes path");
        Check.Equal(0, late.GateCalls,
            "time pre-overrun precedes gate");
        Check.Equal(0, late.CaptureCalls,
            "time pre-overrun precedes capture");
        AssertFaultCode(
            time,
            "initial_settle_timeout",
            "time pre-overrun code");

        DriverFixture frame = DriverFixture.Active(4, 30.0);
        frame.Observe(
            frame.State,
            frame.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        frame.SetCurrentFramesForDefensiveTest(4);
        FakeUpdateObservation over = frame.NewObservation(
            frame.State,
            true,
            frame.State,
            true,
            1.0,
            true,
            ProtocolSamples.InitialCapture);
        frame.Boundary.Observe(over);
        Check.Equal(0, over.PathCalls,
            "frame pre-overrun precedes path");
        Check.Equal(0, over.GateCalls,
            "frame pre-overrun precedes gate");
        Check.Equal(0, over.CaptureCalls,
            "frame pre-overrun precedes capture");
        AssertFaultCode(
            frame,
            "initial_settle_timeout",
            "frame pre-overrun code");
        Check.Equal(4,
            frame.Sink.ErrorRecords[0].SettleFrames,
            "frame pre-overrun is capped");
    }

    private static void AssertCaptureRecordFailures()
    {
        DriverFixture typed = DriverFixture.Active();
        typed.Observe(
            typed.State,
            typed.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        typed.Neutral();
        typed.Observe(
            typed.State,
            typed.State,
            1.0,
            true,
            ProtocolSamples.Capture("valid-last"));
        CaptureRecord invalidScalar =
            ProtocolSamples.Capture("\ud800");
        typed.Observe(
            typed.State,
            typed.State,
            2.0,
            true,
            invalidScalar);
        AssertFaultCode(
            typed,
            "capture_failed",
            "canonical capture failure classification");
        Check.Equal(
            "valid-last",
            typed.Sink.ErrorRecords[0].LastCapture.RawSave,
            "canonical failure retains most recent complete capture");

        DriverFixture large = DriverFixture.Active();
        large.Observe(
            large.State,
            large.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        large.Neutral();
        large.Observe(
            large.State,
            large.State,
            1.0,
            true,
            ProtocolSamples.Capture("bounded-last"));
        CaptureRecord tooLarge = ProtocolSamples.Capture(
            new string('x', 17 * 1024 * 1024));
        large.Observe(
            large.State,
            large.State,
            2.0,
            true,
            tooLarge);
        AssertFaultCode(
            large,
            "record_too_large",
            "record size classification");
        Check.Equal(
            "bounded-last",
            large.Sink.ErrorRecords[0].LastCapture.RawSave,
            "oversize capture does not replace last_capture");

        AssertInitialWriteFailure();
    }

    private static void AssertInitialWriteFailure()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State,
            fixture.State,
            0.0,
            true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            fixture.State,
            1.0,
            true,
            ProtocolSamples.Capture("initial-io"));
        fixture.Sink.InitialFailure =
            new TraceIoException("initial write failed");
        fixture.Observe(
            fixture.State,
            fixture.State,
            2.0,
            true,
            ProtocolSamples.Capture("initial-io"));
        Check.Equal(0, fixture.Sink.InitialRecords.Count,
            "failed Initial is not durable");
        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
            "Initial write failure is terminal");
        Check.Equal(1, fixture.Sink.InitialCalls,
            "Initial write attempted once");
        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
            "Initial trace failure writes no speculative Error");
        Check.Equal(0, fixture.Sink.ErrorCalls,
            "Initial trace failure attempts no Error");
        Check.Equal(1, fixture.Sink.CloseCalls,
            "Initial write failure closes once");
        fixture.Driver.Dispose();
        Check.Equal(1, fixture.Sink.CloseCalls,
            "Initial trace failure retains close ownership after Dispose");
        Check.Sequence(
            new string[] { "trace_io_failed" },
            fixture.Reporter.FailedCodes.ToArray(),
            "Initial write failure marker");
        Check.Equal(1, fixture.Reporter.FailedCalls,
            "Initial write failure marker attempted once");
        Check.Equal(0, fixture.Reporter.ReadyValues.Count,
            "Initial write failure reports no Ready");
        FakeUpdateObservation late = fixture.NewObservation(
            fixture.State,
            true,
            fixture.State,
            true,
            3.0,
            true,
            ProtocolSamples.InitialCapture);
        fixture.Boundary.Observe(late);
        Check.Equal(0, late.StateCalls,
            "Initial failure makes boundary inert");
        Check.False(fixture.Driver.PlayerPollEntered().Active,
            "Initial failure makes poll inert");
    }

    private static void AssertFaultCode(
        DriverFixture fixture,
        string expectedCode,
        string label)
    {
        Check.Equal(
            PassivePhase.Faulted,
            fixture.Driver.Phase,
            label + " phase");
        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
            label + " Error count");
        Check.Equal(expectedCode,
            fixture.Sink.ErrorRecords[0].Code,
            label + " Error code");
        Check.Equal(
            ProtocolSamples.Run.RunId,
            fixture.Sink.ErrorRecords[0].RunId,
            label + " run_id");
        Check.False(
            fixture.Sink.ErrorRecords[0].InputIndex.HasValue,
            label + " input_index null");
        Check.False(
            fixture.Sink.ErrorRecords[0].Input.HasValue,
            label + " input null");
        Check.Equal(
            OracleErrors.ForCode(expectedCode).Message,
            fixture.Sink.ErrorRecords[0].Message,
            label + " message");
        Check.Equal(1, fixture.Sink.CloseCalls,
            label + " close count");
        Check.Sequence(
            new string[] { expectedCode },
            fixture.Reporter.FailedCodes.ToArray(),
            label + " marker code");
    }

    private static void AssertNoStepOrEnd(
        DriverFixture fixture,
        string label)
    {
        Check.Equal(0, fixture.Sink.StepCalls,
            label + " Step calls");
        Check.Equal(0, fixture.Sink.StepRecords.Count,
            label + " Step records");
        Check.Equal(0, fixture.Sink.EndCalls,
            label + " End calls");
        Check.Equal(0, fixture.Sink.EndRecords.Count,
            label + " End records");
        Check.Equal(0, fixture.Reporter.CompleteCalls,
            label + " Complete reports");
    }
}
