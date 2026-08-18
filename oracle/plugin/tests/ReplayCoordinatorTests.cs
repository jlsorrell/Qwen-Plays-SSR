using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;

internal sealed class FakeReplayDriver : IReplayDriver
{
    internal readonly List<object> ReadyStates = new List<object>();
    internal readonly List<int> ReadyCounts = new List<int>();
    internal readonly List<string> FaultCodes = new List<string>();
    internal bool ReadyResult = true;
    internal bool FaultResult = true;
    internal Action<object, int> ReadyObserved;
    internal Action<string> FaultObserved;

    public bool IsReadyForReplay(
        object stateReference, int completedInputs)
    {
        ReadyStates.Add(stateReference);
        ReadyCounts.Add(completedInputs);
        if (ReadyObserved != null)
            ReadyObserved(stateReference, completedInputs);
        return ReadyResult;
    }

    public bool TryFault(string code)
    {
        FaultCodes.Add(code);
        if (FaultObserved != null)
            FaultObserved(code);
        return FaultResult;
    }
}

internal sealed class FakeReplayUpdateAccess : IReplayUpdateAccess
{
    internal object StateReference;
    internal bool StateAvailable = true;
    internal bool SavePathMatches = true;
    internal bool Quiescent = true;
    internal Exception StateFailure;
    internal Exception QuiescenceFailure;
    internal Exception UndoFailure;
    internal Action<object> StateObserved;
    internal Action<object> UndoObserved;
    internal readonly List<string> Events = new List<string>();
    internal int StateCalls;
    internal int PathCalls;
    internal int QuiescenceCalls;
    internal int UndoCalls;
    internal object LastGame;
    internal object LastQuiescentState;

    public bool TryGetState(object game, out object stateReference)
    {
        StateCalls++;
        LastGame = game;
        Events.Add("access:state");
        stateReference = StateReference;
        if (StateObserved != null) StateObserved(game);
        if (StateFailure != null) throw StateFailure;
        return StateAvailable;
    }

    public bool VerifySavePath()
    {
        PathCalls++;
        Events.Add("access:path");
        return SavePathMatches;
    }

    public bool IsQuiescent(object game, object stateReference)
    {
        QuiescenceCalls++;
        LastGame = game;
        LastQuiescentState = stateReference;
        Events.Add("access:quiescent");
        if (QuiescenceFailure != null) throw QuiescenceFailure;
        return Quiescent;
    }

    public void InvokeUndo(object game)
    {
        UndoCalls++;
        LastGame = game;
        Events.Add("access:undo");
        if (UndoObserved != null) UndoObserved(game);
        if (UndoFailure != null) throw UndoFailure;
    }
}

internal sealed class ReplayRecordingReporter : IPassiveReporter
{
    internal readonly List<int> ReadyValues = new List<int>();
    internal readonly List<string> FailedCodes = new List<string>();
    internal readonly List<string> Diagnostics = new List<string>();
    internal readonly List<string> Events = new List<string>();
    internal Action<string> DiagnosticObserved;
    internal int CompleteCalls;

    internal int EventCount
    {
        get { return Events.Count; }
    }

    public void Ready(int completedInputs)
    {
        ReadyValues.Add(completedInputs);
        Events.Add("ready:" + completedInputs.ToString());
    }

    public void Complete()
    {
        CompleteCalls++;
        Events.Add("complete");
    }

    public void Failed(string code)
    {
        FailedCodes.Add(code);
        Events.Add("failed:" + code);
    }

    public void Diagnostic(string message)
    {
        Diagnostics.Add(message);
        Events.Add("diagnostic:" + message);
        if (DiagnosticObserved != null) DiagnosticObserved(message);
    }
}

internal sealed class ReplayCoordinatorFixture
{
    internal readonly object Game = new object();
    internal readonly object State = new object();
    internal readonly object OtherState = new object();
    internal readonly FakeReplayDriver Driver = new FakeReplayDriver();
    internal readonly FakeReplayUpdateAccess Access =
        new FakeReplayUpdateAccess();
    internal readonly ReplayRecordingReporter Reporter =
        new ReplayRecordingReporter();
    internal readonly ReplayCoordinator Coordinator;

    internal ReplayCoordinatorFixture(string tokens)
        : this(tokens, "")
    {
    }

    internal ReplayCoordinatorFixture(
        string tokens, string expectedInitialSha256)
    {
        Access.StateReference = State;
        Coordinator = new ReplayCoordinator(
            ReplayInput.Parse(Encoding.UTF8.GetBytes(tokens)),
            expectedInitialSha256,
            Reporter);
        Coordinator.AttachDriver(Driver);
    }

    internal void MakeInitialReady(string rawSave)
    {
        Coordinator.PhysicalPollReturned(8);
        Coordinator.CaptureObserved(ProtocolSamples.Capture(rawSave));
        Coordinator.Ready(0);
    }

    internal int Override()
    {
        int raw;
        Check.True(Coordinator.TryOverridePlayerInput(out raw),
            "replay always owns Playerinputstring");
        return raw;
    }

    internal int ArmCardinal()
    {
        Coordinator.UpdateEntered(Game, Access);
        return Override();
    }

    internal void TraverseCardinal(int rawDirection)
    {
        Coordinator.UpdateEntered(Game, Access);
        Check.Equal(rawDirection, Override(), "armed cardinal raw direction");
        Coordinator.PhysicalPollReturned(rawDirection);
        Coordinator.ProcessInputEntered(State, rawDirection);
        Coordinator.UpdateReturned();
    }
}

internal static class ReplayCoordinatorTests
{
    private const int WorkerTimeoutMilliseconds = 5000;
    private const string RawSaveSha256 =
        "9bf154e5a52a33858d870559c08bda3109dae0c6b702845209e01c19b3b5afa5";

    internal static void Register(TestRegistry tests)
    {
        tests.Add("replay-coordinator",
            "initial signature owns before Ready and arming",
            InitialSignatureOwnsBeforeReadyAndArming);
        tests.Add("replay-coordinator",
            "real neutral poll is required and physical input is suppressed",
            RealNeutralPollIsRequiredAndPhysicalInputIsSuppressed);
        tests.Add("replay-coordinator",
            "cardinal traverses one owning update",
            CardinalTraversesOneOwningUpdate);
        tests.Add("replay-coordinator",
            "missing duplicate and mismatched traversal fault",
            InvalidCardinalTraversalFaults);
        tests.Add("replay-coordinator",
            "Undo invokes once and Restore stays native",
            UndoInvokesOnceAndRestoreStaysNative);
        tests.Add("replay-coordinator",
            "refused cardinal remains one durable token",
            RefusedCardinalRemainsOneDurableToken);
        tests.Add("replay-coordinator",
            "advance waits for Ready and final Complete has no repeat",
            AdvanceWaitsForReadyAndFinalCompleteHasNoRepeat);
        tests.Add("replay-coordinator",
            "fault disable and late callbacks are inert",
            TerminalAndLateCallbacksAreInert);
    }

    private static void InitialSignatureOwnsBeforeReadyAndArming()
    {
        ReplayCoordinatorFixture exact = new ReplayCoordinatorFixture(
            "North\n", RawSaveSha256);
        exact.MakeInitialReady("raw_save");
        Check.Sequence(new int[] { 0 }, exact.Reporter.ReadyValues.ToArray(),
            "exact UTF-8 raw_save hash forwards Ready zero");
        Check.Equal(0, exact.Driver.FaultCodes.Count,
            "exact UTF-8 raw_save hash does not fault");

        ReplayCoordinatorFixture mismatch = new ReplayCoordinatorFixture(
            "North\n", RawSaveSha256);
        mismatch.Driver.FaultObserved = delegate(string code)
        {
            AssertDiagnosticDisposeCannotReplaceOwner(mismatch);
            mismatch.Coordinator.Failed(code);
        };
        mismatch.Coordinator.PhysicalPollReturned(8);
        mismatch.Coordinator.CaptureObserved(
            ProtocolSamples.Capture("raw_save\n"));
        mismatch.Coordinator.Ready(0);

        Check.Sequence(new string[] { "initial_state_mismatch" },
            mismatch.Driver.FaultCodes.ToArray(),
            "exact bytes choose only initial mismatch");
        Check.Sequence(new string[] { "initial_state_mismatch" },
            mismatch.Reporter.FailedCodes.ToArray(),
            "driver owner forwards only initial mismatch");
        Check.Equal(0, mismatch.Reporter.ReadyValues.Count,
            "mismatch precedes downstream Ready");
        mismatch.Coordinator.UpdateEntered(mismatch.Game, mismatch.Access);
        Check.Equal(0, mismatch.Access.StateCalls,
            "mismatch prevents arming access");
        Check.Equal(8, mismatch.Override(),
            "mismatch leaves input suppressed to None");
    }

    private static void AssertDiagnosticDisposeCannotReplaceOwner(
        ReplayCoordinatorFixture fixture)
    {
        Exception workerFailure = null;
        bool joined = false;
        using (ManualResetEvent entered = new ManualResetEvent(false))
        using (ManualResetEvent release = new ManualResetEvent(false))
        {
            fixture.Reporter.DiagnosticObserved = delegate(string message)
            {
                entered.Set();
                if (!release.WaitOne(WorkerTimeoutMilliseconds))
                    throw new TimeoutException("diagnostic was not released");
            };
            Thread worker = new Thread(delegate()
            {
                try { fixture.Coordinator.Diagnostic("fault diagnostic"); }
                catch (Exception error) { workerFailure = error; }
            });
            worker.IsBackground = false;
            try
            {
                worker.Start();
                Check.True(entered.WaitOne(WorkerTimeoutMilliseconds),
                    "diagnostic callback entered");
                fixture.Coordinator.Dispose();
            }
            finally
            {
                release.Set();
                joined = worker.Join(WorkerTimeoutMilliseconds);
            }
        }
        Check.True(joined, "diagnostic worker joins");
        Check.True(workerFailure == null, "diagnostic worker succeeds");
        Check.Sequence(new string[] { "fault diagnostic" },
            fixture.Reporter.Diagnostics.ToArray(),
            "one diagnostic reaches downstream");
    }

    private static void RealNeutralPollIsRequiredAndPhysicalInputIsSuppressed()
    {
        ReplayCoordinatorFixture missingNeutral =
            new ReplayCoordinatorFixture("North\n");
        missingNeutral.Coordinator.CaptureObserved(
            ProtocolSamples.Capture("raw_save"));
        missingNeutral.Coordinator.Ready(0);
        AssertOnlyFault(missingNeutral, "replay_alignment_failed",
            "capture alone is not neutral credit");

        ReplayCoordinatorFixture mismatchedPostfix =
            new ReplayCoordinatorFixture("North\n");
        Check.Equal(8, mismatchedPostfix.Override(),
            "unarmed override suppresses physical input");
        mismatchedPostfix.Coordinator.PhysicalPollReturned(7);
        AssertOnlyFault(mismatchedPostfix, "replay_alignment_failed",
            "non-None postfix cannot credit neutral");

        ReplayCoordinatorFixture fixture =
            new ReplayCoordinatorFixture("North\n");
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Equal(0, fixture.Access.StateCalls,
            "not Ready performs no native access");
        Check.Equal(8, fixture.Override(),
            "pre-Ready input is suppressed");
        fixture.Coordinator.PhysicalPollReturned(8);
        fixture.Coordinator.CaptureObserved(
            ProtocolSamples.Capture("raw_save"));
        fixture.Driver.ReadyResult = false;
        fixture.Coordinator.Ready(0);
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Sequence(new int[] { 0 }, fixture.Driver.ReadyCounts.ToArray(),
            "driver readiness receives token zero");
        Check.Equal(8, fixture.Override(),
            "unready driver leaves physical input suppressed");
        Check.Equal(0, fixture.Access.UndoCalls,
            "unready cardinal invokes no native method");

        fixture.Driver.ReadyResult = true;
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Equal((int)OracleInput.North, fixture.Override(),
            "Ready plus matching neutral plus driver readiness arms");
        Check.Equal(0, fixture.Access.UndoCalls,
            "cardinal does not invoke Undo");

        ReplayCoordinatorFixture unavailable =
            new ReplayCoordinatorFixture("East\n");
        unavailable.MakeInitialReady("raw_save");
        unavailable.Access.StateAvailable = false;
        unavailable.Coordinator.UpdateEntered(
            unavailable.Game, unavailable.Access);
        Check.Equal(1, unavailable.Access.StateCalls,
            "unavailable state queried once");
        Check.Equal(0, unavailable.Access.PathCalls,
            "unavailable state stops before path");
        Check.Equal(8, unavailable.Override(),
            "unavailable state remains suppressed");

        ReplayCoordinatorFixture nonquiescent =
            new ReplayCoordinatorFixture("East\n");
        nonquiescent.MakeInitialReady("raw_save");
        nonquiescent.Access.Quiescent = false;
        nonquiescent.Coordinator.UpdateEntered(
            nonquiescent.Game, nonquiescent.Access);
        Check.Equal(0, nonquiescent.Driver.ReadyCounts.Count,
            "nonquiescent state stops before driver readiness");
        Check.Equal(8, nonquiescent.Override(),
            "nonquiescent state remains suppressed");
    }

    private static void CardinalTraversesOneOwningUpdate()
    {
        ReplayCoordinatorFixture fixture =
            new ReplayCoordinatorFixture("West\n");
        fixture.MakeInitialReady("raw_save");
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Sequence(new string[] {
            "access:state", "access:path", "access:quiescent"
        }, fixture.Access.Events.ToArray(), "arming access order");
        Check.Same(fixture.State, fixture.Driver.ReadyStates[0],
            "arming driver state identity");
        Check.Sequence(new int[] { 0 }, fixture.Driver.ReadyCounts.ToArray(),
            "arming driver token index");

        int raw = fixture.Override();
        Check.Equal((int)OracleInput.West, raw,
            "first owning override matches token");
        fixture.Coordinator.PhysicalPollReturned(raw);
        fixture.Coordinator.ProcessInputEntered(fixture.State, raw);
        fixture.Coordinator.UpdateReturned();
        Check.Equal(8, fixture.Override(),
            "UpdateReturned deasserts cardinal");
        int accessCalls = fixture.Access.StateCalls;
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Equal(accessCalls, fixture.Access.StateCalls,
            "pending durable Step cannot open another update");
        Check.Equal(0, fixture.Driver.FaultCodes.Count,
            "one owning traversal is aligned");

        ReplayCoordinatorFixture threw =
            new ReplayCoordinatorFixture("East\n");
        threw.MakeInitialReady("raw_save");
        Check.Equal((int)OracleInput.East, threw.ArmCardinal(),
            "throw fixture arms cardinal");
        threw.Coordinator.UpdateThrew();
        Check.Equal(8, threw.Override(),
            "UpdateThrew deasserts cardinal");
        Check.Equal(0, threw.Driver.FaultCodes.Count,
            "UpdateThrew leaves driver exception ownership intact");
    }

    private static void InvalidCardinalTraversalFaults()
    {
        ReplayCoordinatorFixture missingPoll = ArmedCardinalFixture();
        missingPoll.Coordinator.UpdateReturned();
        AssertOnlyAlignmentFault(missingPoll, "missing poll");

        ReplayCoordinatorFixture duplicatePoll = ArmedCardinalFixture();
        duplicatePoll.Coordinator.PhysicalPollReturned((int)OracleInput.North);
        duplicatePoll.Coordinator.PhysicalPollReturned((int)OracleInput.North);
        AssertOnlyAlignmentFault(duplicatePoll, "duplicate poll");

        ReplayCoordinatorFixture missingProcess = ArmedCardinalFixture();
        missingProcess.Coordinator.PhysicalPollReturned((int)OracleInput.North);
        missingProcess.Coordinator.UpdateReturned();
        AssertOnlyAlignmentFault(missingProcess, "missing ProcessInput");

        ReplayCoordinatorFixture duplicateProcess = ArmedCardinalFixture();
        duplicateProcess.Coordinator.PhysicalPollReturned((int)OracleInput.North);
        duplicateProcess.Coordinator.ProcessInputEntered(
            duplicateProcess.State, (int)OracleInput.North);
        duplicateProcess.Coordinator.ProcessInputEntered(
            duplicateProcess.State, (int)OracleInput.North);
        AssertOnlyAlignmentFault(duplicateProcess, "duplicate ProcessInput");

        ReplayCoordinatorFixture mismatchedPoll = ArmedCardinalFixture();
        mismatchedPoll.Coordinator.PhysicalPollReturned((int)OracleInput.South);
        AssertOnlyAlignmentFault(mismatchedPoll, "mismatched poll raw");

        ReplayCoordinatorFixture mismatchedProcess = ArmedCardinalFixture();
        mismatchedProcess.Coordinator.PhysicalPollReturned(
            (int)OracleInput.North);
        mismatchedProcess.Coordinator.ProcessInputEntered(
            mismatchedProcess.State, (int)OracleInput.South);
        AssertOnlyAlignmentFault(mismatchedProcess,
            "mismatched ProcessInput raw");

        ReplayCoordinatorFixture foreignState = ArmedCardinalFixture();
        foreignState.Coordinator.PhysicalPollReturned((int)OracleInput.North);
        foreignState.Coordinator.ProcessInputEntered(
            foreignState.OtherState, (int)OracleInput.North);
        AssertOnlyAlignmentFault(foreignState, "foreign state");

        ReplayCoordinatorFixture lateProcess = ArmedCardinalFixture();
        lateProcess.Coordinator.PhysicalPollReturned((int)OracleInput.North);
        lateProcess.Coordinator.ProcessInputEntered(
            lateProcess.State, (int)OracleInput.North);
        lateProcess.Coordinator.UpdateReturned();
        lateProcess.Coordinator.ProcessInputEntered(
            lateProcess.State, (int)OracleInput.North);
        AssertOnlyAlignmentFault(lateProcess, "late ProcessInput");
    }

    private static ReplayCoordinatorFixture ArmedCardinalFixture()
    {
        ReplayCoordinatorFixture fixture =
            new ReplayCoordinatorFixture("North\n");
        fixture.MakeInitialReady("raw_save");
        Check.Equal((int)OracleInput.North, fixture.ArmCardinal(),
            "invalid fixture arms North");
        return fixture;
    }

    private static void UndoInvokesOnceAndRestoreStaysNative()
    {
        ReplayCoordinatorFixture fixture =
            new ReplayCoordinatorFixture("Undo\n");
        fixture.MakeInitialReady("raw_save");
        int undoEntered = 0;
        int restoreObserved = 0;
        int undoReturned = 0;
        fixture.Access.UndoObserved = delegate(object game)
        {
            Check.Same(fixture.Game, game, "public Undo receives owning game");
            undoEntered++;
            fixture.Coordinator.UndoEntered();
            restoreObserved++;
            fixture.Coordinator.RestoreObserved();
            undoReturned++;
            fixture.Coordinator.UndoReturned();
        };
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Equal(1, fixture.Access.UndoCalls, "public Undo invoked once");
        Check.Equal(1, undoEntered, "one UndoEntered callback");
        Check.Equal(1, restoreObserved, "one native Restore callback");
        Check.Equal(1, undoReturned, "one UndoReturned callback");
        Check.Equal(8, fixture.Override(),
            "Undo never arms a cardinal override");
        fixture.Coordinator.UpdateReturned();
        Check.Equal(0, fixture.Driver.FaultCodes.Count,
            "native Undo traversal is aligned");

        ReplayCoordinatorFixture recursive =
            new ReplayCoordinatorFixture("Undo\n");
        recursive.MakeInitialReady("raw_save");
        int stateCallbacks = 0;
        int undoCallbacks = 0;
        recursive.Access.StateObserved = delegate(object game)
        {
            stateCallbacks++;
            if (stateCallbacks == 1)
            {
                recursive.Coordinator.UpdateEntered(
                    game, recursive.Access);
            }
        };
        recursive.Access.UndoObserved = delegate(object game)
        {
            undoCallbacks++;
            recursive.Coordinator.UpdateEntered(game, recursive.Access);
            recursive.Coordinator.UndoEntered();
            recursive.Coordinator.RestoreObserved();
            recursive.Coordinator.UndoReturned();
        };
        recursive.Coordinator.UpdateEntered(
            recursive.Game, recursive.Access);
        Check.Equal(1, stateCallbacks,
            "recursive access callback cannot claim another update");
        Check.Equal(1, recursive.Access.StateCalls,
            "recursive access performs one state read");
        Check.Equal(1, recursive.Access.PathCalls,
            "recursive access performs one path check");
        Check.Equal(1, recursive.Access.QuiescenceCalls,
            "recursive access performs one quiescence check");
        Check.Equal(1, recursive.Driver.ReadyCounts.Count,
            "recursive access performs one readiness query");
        Check.Equal(1, recursive.Access.UndoCalls,
            "recursive access invokes public Undo once");
        Check.Equal(1, undoCallbacks,
            "InvokeUndo reentry remains inside one owning claim");
        recursive.Coordinator.UpdateReturned();
        Check.Equal(0, recursive.Driver.FaultCodes.Count,
            "recursive Undo remains aligned");

        ReplayCoordinatorFixture missingRestore =
            new ReplayCoordinatorFixture("Undo\n");
        missingRestore.MakeInitialReady("raw_save");
        missingRestore.Access.UndoObserved = delegate(object game)
        {
            missingRestore.Coordinator.UndoEntered();
            missingRestore.Coordinator.UndoReturned();
        };
        missingRestore.Coordinator.UpdateEntered(
            missingRestore.Game, missingRestore.Access);
        missingRestore.Coordinator.UpdateReturned();
        AssertOnlyAlignmentFault(missingRestore,
            "Undo without native Restore");

        ReplayCoordinatorFixture outside =
            new ReplayCoordinatorFixture("Undo\n");
        outside.Coordinator.RestoreObserved();
        AssertOnlyAlignmentFault(outside, "Restore outside Undo");

        ReplayCoordinatorFixture duplicateEnter =
            new ReplayCoordinatorFixture("Undo\n");
        duplicateEnter.MakeInitialReady("raw_save");
        duplicateEnter.Access.UndoObserved = delegate(object game)
        {
            duplicateEnter.Coordinator.UndoEntered();
            duplicateEnter.Coordinator.UndoEntered();
        };
        duplicateEnter.Coordinator.UpdateEntered(
            duplicateEnter.Game, duplicateEnter.Access);
        AssertOnlyAlignmentFault(duplicateEnter, "duplicate UndoEntered");

        ReplayCoordinatorFixture duplicateReturn =
            new ReplayCoordinatorFixture("Undo\n");
        duplicateReturn.MakeInitialReady("raw_save");
        duplicateReturn.Access.UndoObserved = delegate(object game)
        {
            duplicateReturn.Coordinator.UndoEntered();
            duplicateReturn.Coordinator.UndoReturned();
            duplicateReturn.Coordinator.UndoReturned();
        };
        duplicateReturn.Coordinator.UpdateEntered(
            duplicateReturn.Game, duplicateReturn.Access);
        AssertOnlyAlignmentFault(duplicateReturn, "duplicate UndoReturned");

        ReplayCoordinatorFixture lateRestore =
            new ReplayCoordinatorFixture("Undo\n");
        lateRestore.MakeInitialReady("raw_save");
        lateRestore.Access.UndoObserved = delegate(object game)
        {
            lateRestore.Coordinator.UndoEntered();
            lateRestore.Coordinator.UndoReturned();
            lateRestore.Coordinator.RestoreObserved();
        };
        lateRestore.Coordinator.UpdateEntered(
            lateRestore.Game, lateRestore.Access);
        AssertOnlyAlignmentFault(lateRestore, "Restore after UndoReturned");

        ReplayCoordinatorFixture directProcess =
            new ReplayCoordinatorFixture("Undo\n");
        directProcess.MakeInitialReady("raw_save");
        directProcess.Access.UndoObserved = delegate(object game)
        {
            directProcess.Coordinator.UndoEntered();
            directProcess.Coordinator.ProcessInputEntered(
                directProcess.State, (int)OracleInput.North);
        };
        directProcess.Coordinator.UpdateEntered(
            directProcess.Game, directProcess.Access);
        AssertOnlyAlignmentFault(directProcess,
            "Undo cannot traverse ProcessInput");

        ReplayCoordinatorFixture throwing =
            new ReplayCoordinatorFixture("Undo\n");
        throwing.MakeInitialReady("raw_save");
        InvalidOperationException undoFailure =
            new InvalidOperationException("Undo failed");
        throwing.Access.UndoFailure = undoFailure;
        InvalidOperationException observed =
            Check.Throws<InvalidOperationException>(delegate
            {
                throwing.Coordinator.UpdateEntered(
                    throwing.Game, throwing.Access);
            }, "Undo exception escapes to callback firewall");
        Check.Same(undoFailure, observed, "Undo exception identity retained");
        throwing.Coordinator.UpdateThrew();
        Check.Equal(8, throwing.Override(),
            "Undo throw cleanup leaves None override");
        Check.Equal(0, throwing.Driver.FaultCodes.Count,
            "Undo throw keeps driver exception ownership");
    }

    private static void RefusedCardinalRemainsOneDurableToken()
    {
        ReplayCoordinatorFixture fixture =
            new ReplayCoordinatorFixture("North\nSouth\n");
        fixture.MakeInitialReady("raw_save");
        fixture.TraverseCardinal((int)OracleInput.North);
        int stateCalls = fixture.Access.StateCalls;
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Equal(stateCalls, fixture.Access.StateCalls,
            "refused native traversal is not retried before Ready");
        Check.Equal(8, fixture.Override(),
            "refused pending token is deasserted");

        fixture.Coordinator.Ready(1);
        Check.Sequence(new int[] { 0, 1 },
            fixture.Reporter.ReadyValues.ToArray(),
            "durable refused Step advances once");
        fixture.Coordinator.PhysicalPollReturned(8);
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Sequence(new int[] { 0, 1 },
            fixture.Driver.ReadyCounts.ToArray(),
            "next readiness query uses advanced token index");
        Check.Equal((int)OracleInput.South, fixture.Override(),
            "next durable token is South");
        Check.Equal(0, fixture.Driver.FaultCodes.Count,
            "refused traversal remains valid");
    }

    private static void AdvanceWaitsForReadyAndFinalCompleteHasNoRepeat()
    {
        ReplayCoordinatorFixture fixture =
            new ReplayCoordinatorFixture("North\nEast\n");
        fixture.MakeInitialReady("raw_save");
        fixture.TraverseCardinal((int)OracleInput.North);
        Check.Sequence(new int[] { 0 }, fixture.Driver.ReadyCounts.ToArray(),
            "arming and UpdateReturned retain token zero");
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Sequence(new int[] { 0 }, fixture.Driver.ReadyCounts.ToArray(),
            "pending Step blocks readiness query");

        fixture.Coordinator.Ready(1);
        int stateCalls = fixture.Access.StateCalls;
        fixture.Coordinator.UpdateEntered(fixture.Game, fixture.Access);
        Check.Equal(stateCalls, fixture.Access.StateCalls,
            "Ready resets neutral credit");
        fixture.Coordinator.PhysicalPollReturned(8);
        fixture.TraverseCardinal((int)OracleInput.East);
        Check.Sequence(new int[] { 0, 1 }, fixture.Driver.ReadyCounts.ToArray(),
            "Ready one alone advances token index");
        Check.Sequence(new int[] { 0, 1 },
            fixture.Reporter.ReadyValues.ToArray(),
            "no Ready count before final completion");

        fixture.Coordinator.Complete();
        Check.Equal(1, fixture.Reporter.CompleteCalls,
            "final pending Step completes once");
        Check.Sequence(new int[] { 0, 1 },
            fixture.Reporter.ReadyValues.ToArray(),
            "final Complete has no Ready two");
        int events = fixture.Reporter.EventCount;
        fixture.Coordinator.Complete();
        fixture.Coordinator.Ready(2);
        Check.Equal(events, fixture.Reporter.EventCount,
            "final Complete and late Ready do not repeat");
        Check.Equal(8, fixture.Override(),
            "Complete leaves physical input suppressed");
    }

    private static void TerminalAndLateCallbacksAreInert()
    {
        AssertConstructorAndAttachmentContracts();

        ReplayCoordinatorFixture failed =
            new ReplayCoordinatorFixture("North\n");
        failed.Coordinator.Failed("capture_failed");
        Check.Sequence(new string[] { "capture_failed" },
            failed.Reporter.FailedCodes.ToArray(), "Failed forwards once");
        AssertLateCallbacksInert(failed, "Failed");

        ReplayCoordinatorFixture complete =
            new ReplayCoordinatorFixture("North\n");
        complete.MakeInitialReady("raw_save");
        complete.TraverseCardinal((int)OracleInput.North);
        complete.Coordinator.Complete();
        Check.Equal(1, complete.Reporter.CompleteCalls,
            "Complete forwards once");
        AssertLateCallbacksInert(complete, "Complete");

        ReplayCoordinatorFixture refusedClaim =
            new ReplayCoordinatorFixture("North\n");
        refusedClaim.MakeInitialReady("raw_save");
        refusedClaim.Driver.FaultResult = false;
        refusedClaim.Coordinator.PhysicalPollReturned(7);
        AssertOnlyFault(refusedClaim, "replay_alignment_failed",
            "failed driver claim code");
        AssertLateCallbacksInert(refusedClaim, "failed driver claim");

        ReplayCoordinatorFixture duplicateReady =
            new ReplayCoordinatorFixture("North\n");
        duplicateReady.MakeInitialReady("raw_save");
        duplicateReady.Driver.FaultObserved = delegate(string code)
        {
            duplicateReady.Coordinator.Failed(code);
        };
        duplicateReady.Coordinator.Ready(0);
        AssertOnlyAlignmentFault(duplicateReady, "duplicate Ready");
        Check.Sequence(new string[] { "replay_alignment_failed" },
            duplicateReady.Reporter.FailedCodes.ToArray(),
            "duplicate Ready forwards driver failure");
        AssertLateCallbacksInert(duplicateReady, "duplicate Ready");

        ReplayCoordinatorFixture disposed =
            new ReplayCoordinatorFixture("North\n");
        disposed.Coordinator.Dispose();
        AssertLateCallbacksInert(disposed, "Dispose");

        AssertReadinessTerminalReentry();

        AssertUpdateAccessFaults();
    }

    private static void AssertReadinessTerminalReentry()
    {
        ReplayCoordinatorFixture failed =
            new ReplayCoordinatorFixture("Undo\n");
        failed.MakeInitialReady("raw_save");
        failed.Driver.ReadyObserved = delegate(
            object stateReference, int completedInputs)
        {
            failed.Coordinator.Failed("state_replaced");
        };
        failed.Coordinator.UpdateEntered(failed.Game, failed.Access);
        Check.Sequence(new string[] { "state_replaced" },
            failed.Reporter.FailedCodes.ToArray(),
            "readiness Failed forwards one terminal result");
        Check.Equal(0, failed.Reporter.CompleteCalls,
            "readiness Failed does not Complete");
        Check.Equal(0, failed.Access.UndoCalls,
            "readiness Failed prevents outer Undo publication");
        Check.Equal(8, failed.Override(),
            "readiness Failed leaves None override");
        AssertLateCallbacksInert(failed, "readiness Failed");

        ReplayCoordinatorFixture disposed =
            new ReplayCoordinatorFixture("Undo\n");
        disposed.MakeInitialReady("raw_save");
        int downstreamEvents = disposed.Reporter.EventCount;
        disposed.Driver.ReadyObserved = delegate(
            object stateReference, int completedInputs)
        {
            disposed.Coordinator.Dispose();
        };
        disposed.Coordinator.UpdateEntered(
            disposed.Game, disposed.Access);
        Check.Equal(downstreamEvents, disposed.Reporter.EventCount,
            "readiness Dispose adds no downstream terminal result");
        Check.Equal(0, disposed.Access.UndoCalls,
            "readiness Dispose prevents outer Undo publication");
        Check.Equal(8, disposed.Override(),
            "readiness Dispose leaves None override");
        AssertLateCallbacksInert(disposed, "readiness Dispose");
    }

    private static void AssertConstructorAndAttachmentContracts()
    {
        ReplayInput input = ReplayInput.Parse(Encoding.UTF8.GetBytes("North\n"));
        ReplayRecordingReporter reporter = new ReplayRecordingReporter();
        Check.Throws<ArgumentNullException>(delegate
        {
            new ReplayCoordinator(null, "", reporter);
        }, "null replay input");
        Check.Throws<ArgumentNullException>(delegate
        {
            new ReplayCoordinator(input, null, reporter);
        }, "null expected signature");
        Check.Throws<ArgumentNullException>(delegate
        {
            new ReplayCoordinator(input, "", null);
        }, "null downstream reporter");

        ReplayCoordinator coordinator =
            new ReplayCoordinator(input, "", reporter);
        Check.Throws<ArgumentNullException>(delegate
        {
            coordinator.AttachDriver(null);
        }, "null replay driver");
        coordinator.AttachDriver(new FakeReplayDriver());
        Check.Throws<InvalidOperationException>(delegate
        {
            coordinator.AttachDriver(new FakeReplayDriver());
        }, "replay driver attaches once");

        ReplayCoordinator unattached =
            new ReplayCoordinator(input, "", reporter);
        unattached.PhysicalPollReturned(8);
        unattached.CaptureObserved(ProtocolSamples.Capture("raw_save"));
        unattached.Ready(0);
        Check.Throws<InvalidOperationException>(delegate
        {
            unattached.UpdateEntered(new object(),
                new FakeReplayUpdateAccess { StateReference = new object() });
        }, "eligible update requires attached driver");
    }

    private static void AssertUpdateAccessFaults()
    {
        ReplayCoordinatorFixture savePath =
            new ReplayCoordinatorFixture("North\n");
        savePath.MakeInitialReady("raw_save");
        savePath.Access.SavePathMatches = false;
        savePath.Coordinator.UpdateEntered(savePath.Game, savePath.Access);
        AssertOnlyFault(savePath, "save_path_changed", "save path drift");

        ReplayCoordinatorFixture capture =
            new ReplayCoordinatorFixture("North\n");
        capture.MakeInitialReady("raw_save");
        capture.Access.StateFailure = new CaptureException("capture failed");
        capture.Coordinator.UpdateEntered(capture.Game, capture.Access);
        AssertOnlyFault(capture, "capture_failed", "capture access failure");

        ReplayCoordinatorFixture observer =
            new ReplayCoordinatorFixture("North\n");
        observer.MakeInitialReady("raw_save");
        observer.Access.QuiescenceFailure =
            new InvalidOperationException("observer failed");
        observer.Coordinator.UpdateEntered(observer.Game, observer.Access);
        AssertOnlyFault(observer, "observer_exception",
            "ordinary access failure");
    }

    private static void AssertLateCallbacksInert(
        ReplayCoordinatorFixture fixture, string label)
    {
        int events = fixture.Reporter.EventCount;
        int faults = fixture.Driver.FaultCodes.Count;
        int accessCalls = fixture.Access.StateCalls;
        fixture.Coordinator.CaptureObserved(null);
        fixture.Coordinator.UpdateEntered(null, null);
        Check.Equal(8, fixture.Override(), label + " late override is None");
        fixture.Coordinator.PhysicalPollReturned(0);
        fixture.Coordinator.ProcessInputEntered(new object(), 0);
        fixture.Coordinator.UndoEntered();
        fixture.Coordinator.RestoreObserved();
        fixture.Coordinator.UndoReturned();
        fixture.Coordinator.UpdateReturned();
        fixture.Coordinator.UpdateThrew();
        fixture.Coordinator.Ready(99);
        fixture.Coordinator.Complete();
        fixture.Coordinator.Failed("late_failure");
        fixture.Coordinator.Diagnostic("late diagnostic");
        fixture.Coordinator.Dispose();
        Check.Equal(events, fixture.Reporter.EventCount,
            label + " late callbacks add no downstream event");
        Check.Equal(faults, fixture.Driver.FaultCodes.Count,
            label + " late callbacks add no driver fault");
        Check.Equal(accessCalls, fixture.Access.StateCalls,
            label + " late callbacks perform no native access");
    }

    private static void AssertOnlyAlignmentFault(
        ReplayCoordinatorFixture fixture, string label)
    {
        AssertOnlyFault(fixture, "replay_alignment_failed", label);
    }

    private static void AssertOnlyFault(
        ReplayCoordinatorFixture fixture, string code, string label)
    {
        Check.Sequence(new string[] { code },
            fixture.Driver.FaultCodes.ToArray(), label + " sole fault code");
    }
}
