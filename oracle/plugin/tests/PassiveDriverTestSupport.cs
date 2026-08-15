using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading;

internal sealed class FakeTraceSink : ITraceSink
{
    private readonly IList<string> events;

    internal FakeTraceSink(IList<string> events)
    {
        this.events = events;
    }

    internal readonly List<RunRecord> RunRecords =
        new List<RunRecord>();
    internal readonly List<InitialRecord> InitialRecords =
        new List<InitialRecord>();
    internal readonly List<StepRecord> StepRecords =
        new List<StepRecord>();
    internal readonly List<EndRecord> EndRecords =
        new List<EndRecord>();
    internal readonly List<ErrorRecord> ErrorRecords =
        new List<ErrorRecord>();
    internal Exception RunFailure { get; set; }
    internal Exception InitialFailure { get; set; }
    internal Exception StepFailure { get; set; }
    internal Exception EndFailure { get; set; }
    internal Exception ErrorFailure { get; set; }
    internal Exception CloseFailure { get; set; }
    internal Action<RunRecord> RunEntering { get; set; }
    internal Action<InitialRecord> InitialEntering { get; set; }
    internal Action<StepRecord> StepEntering { get; set; }
    internal Action<StepRecord> StepObserved { get; set; }
    internal Action<EndRecord> EndObserved { get; set; }
    internal Action<ErrorRecord> ErrorEntering { get; set; }
    internal int RunCalls;
    internal int InitialCalls;
    internal int StepCalls;
    internal int EndCalls;
    internal int ErrorCalls;
    internal int CloseCalls;

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

    public void Close()
    {
        CloseCalls++;
        Add("sink:close");
        if (CloseFailure != null)
            throw CloseFailure;
    }

    private void Add(string value)
    {
        events.Add(value);
    }
}

internal sealed class FakePassiveReporter : IPassiveReporter
{
    private readonly IList<string> events;

    internal FakePassiveReporter(IList<string> events)
    {
        this.events = events;
    }

    internal readonly List<int> ReadyValues = new List<int>();
    internal readonly List<string> FailedCodes = new List<string>();
    internal readonly List<string> Diagnostics = new List<string>();
    internal Exception ReadyFailure { get; set; }
    internal Exception CompleteFailure { get; set; }
    internal Exception FailedFailure { get; set; }
    internal Exception DiagnosticFailure { get; set; }
    internal Action<int> ReadyObserved { get; set; }
    internal Action CompleteObserved { get; set; }
    internal Action<string> DiagnosticObserved { get; set; }
    internal int CompleteCalls;
    internal int FailedCalls;
    internal int DiagnosticCalls;

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

    public void Failed(string code)
    {
        FailedCalls++;
        FailedCodes.Add(code);
        Add("report:failed:" + code);
        if (FailedFailure != null)
            throw FailedFailure;
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

    private void Add(string value)
    {
        events.Add(value);
    }
}

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

internal sealed class FakeUpdateObservation :
    IPassiveUpdateObservation
{
    private readonly IList<string> events;

    internal FakeUpdateObservation(IList<string> events)
    {
        this.events = events;
    }

    internal object FirstState;
    internal object SecondState;
    internal bool FirstUsable = true;
    internal bool SecondUsable = true;
    internal bool SavePathMatches = true;
    internal bool Quiescent = true;
    internal CaptureRecord CaptureValue =
        ProtocolSamples.InitialCapture;
    internal double Now;
    internal DateTime Utc = DriverFixture.UtcFinish;
    internal Exception FirstStateFailure { get; set; }
    internal Exception SecondStateFailure { get; set; }
    internal Exception NowFailure { get; set; }
    internal Exception PathFailure { get; set; }
    internal Exception GateFailure { get; set; }
    internal Exception CaptureFailure { get; set; }
    internal Exception UtcFailure { get; set; }
    internal int PathCalls;
    internal int StateCalls;
    internal int GateCalls;
    internal int CaptureCalls;
    internal int NowCalls;
    internal int UtcCalls;
    internal object GateState;
    internal object CaptureState;
    internal Func<bool> AuthorizationProbe;
    internal bool GateSawAuthorized;

    public bool TryGetState(out object stateReference)
    {
        bool first = StateCalls == 0;
        StateCalls++;
        Add(first ? "observer:state:begin" : "observer:state:verified");
        Exception failure = first
            ? FirstStateFailure
            : SecondStateFailure;
        if (failure != null)
            throw failure;
        stateReference = first ? FirstState : SecondState;
        return first ? FirstUsable : SecondUsable;
    }

    public bool VerifySavePath()
    {
        PathCalls++;
        Add("observer:path");
        if (PathFailure != null)
            throw PathFailure;
        return SavePathMatches;
    }

    public bool IsQuiescent(object stateReference)
    {
        GateCalls++;
        GateState = stateReference;
        if (AuthorizationProbe != null)
            GateSawAuthorized = AuthorizationProbe();
        Add("observer:gate");
        if (GateFailure != null)
            throw GateFailure;
        return Quiescent;
    }

    public CaptureRecord Capture(object stateReference)
    {
        CaptureCalls++;
        CaptureState = stateReference;
        Add("observer:capture");
        if (CaptureFailure != null)
            throw CaptureFailure;
        return CaptureValue;
    }

    public double NowSeconds()
    {
        NowCalls++;
        Add("observer:time");
        if (NowFailure != null)
            throw NowFailure;
        return Now;
    }

    public DateTime UtcNow()
    {
        UtcCalls++;
        Add("observer:utc");
        if (UtcFailure != null)
            throw UtcFailure;
        return Utc;
    }

    private void Add(string value)
    {
        events.Add(value);
    }
}

internal sealed partial class DriverFixture
{
    internal static readonly DateTime UtcFinish =
        new DateTime(
            2026, 7, 31, 20, 0, 0, DateTimeKind.Utc);

    internal readonly object State = new object();
    internal readonly object OtherState = new object();
    internal readonly List<string> Events = new List<string>();
    internal readonly FakeTraceSink Sink;
    internal readonly FakePassiveReporter Reporter;
    internal readonly PassiveDriver Driver;
    internal readonly PassiveUpdateBoundary Boundary;

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
        Sink = new FakeTraceSink(Events);
        Reporter = new FakePassiveReporter(Events);
        Driver = new PassiveDriver(
            Sink,
            Reporter,
            OracleProtocol.ExpectedInputCount,
            maxFrames,
            maxSeconds);
        Boundary = new PassiveUpdateBoundary(Driver);
    }

    internal static DriverFixture Unprepared()
    {
        return Unprepared(600, 30.0);
    }

    internal static DriverFixture Unprepared(
        int maxFrames,
        double maxSeconds)
    {
        return new DriverFixture(maxFrames, maxSeconds);
    }

    internal static DriverFixture Active()
    {
        return Active(600, 30.0);
    }

    internal static DriverFixture Active(
        int maxFrames,
        double maxSeconds)
    {
        DriverFixture fixture =
            Unprepared(maxFrames, maxSeconds);
        Check.True(
            fixture.Driver.Prepare(ProtocolSamples.Run),
            "prepare");
        Check.True(fixture.Driver.Activate(), "activate");
        return fixture;
    }

    internal static DriverFixture Ready()
    {
        return Ready(600, 30.0);
    }

    internal static DriverFixture Ready(int maxFrames, double maxSeconds)
    {
        return MakeReady(new DriverFixture(maxFrames, maxSeconds));
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

    internal FakeUpdateObservation Observe(
        object firstState,
        object secondState,
        double now,
        bool quiescent,
        CaptureRecord capture)
    {
        return Observe(
            firstState,
            firstState != null,
            secondState,
            secondState != null,
            now,
            quiescent,
            capture);
    }

    internal FakeUpdateObservation Observe(
        object firstState,
        bool firstUsable,
        object secondState,
        bool secondUsable,
        double now,
        bool quiescent,
        CaptureRecord capture)
    {
        FakeUpdateObservation observation =
            NewObservation(
                firstState,
                firstUsable,
                secondState,
                secondUsable,
                now,
                quiescent,
                capture);
        Boundary.Observe(observation);
        return observation;
    }

    internal FakeUpdateObservation NewObservation(
        object firstState,
        bool firstUsable,
        object secondState,
        bool secondUsable,
        double now,
        bool quiescent,
        CaptureRecord capture)
    {
        FakeUpdateObservation observation =
            new FakeUpdateObservation(Events)
        {
            FirstState = firstState,
            FirstUsable = firstUsable,
            SecondState = secondState,
            SecondUsable = secondUsable,
            Now = now,
            Quiescent = quiescent,
            CaptureValue = capture,
            Utc = UtcFinish
        };
        observation.AuthorizationProbe = delegate
        {
            UpdateDirective directive = Boundary.LastDirective;
            return directive != null
                && ReadUpdateStage(directive) == 1;
        };
        return observation;
    }

    internal void Neutral()
    {
        HookToken poll = Driver.PlayerPollEntered();
        Driver.PhysicalPollReturned(8);
        Driver.PlayerPollReturned(poll);
    }

    internal void CardinalOnly(int rawDirection)
    {
        HookToken poll = Driver.PlayerPollEntered();
        Driver.PhysicalPollReturned(rawDirection);
        Driver.PlayerPollReturned(poll);
    }

    internal void SetCurrentFramesForDefensiveTest(int value)
    {
        SetPrivateField("currentFrames", typeof(int), value);
    }

    private void SetPrivateField(
        string name,
        Type expectedType,
        object value)
    {
        FieldInfo field = RequirePrivateField(name, expectedType);
        field.SetValue(Driver, value);
    }

    private static int ReadUpdateStage(UpdateDirective directive)
    {
        FieldInfo field = typeof(UpdateDirective).GetField(
            "stage",
            BindingFlags.Instance | BindingFlags.NonPublic);
        Check.True(field != null, "directive stage reflection seam");
        Check.Same(
            typeof(UpdateDirective),
            field.DeclaringType,
            "directive stage declaring type");
        Check.Same(typeof(int), field.FieldType,
            "directive stage field type");
        Check.True(field.IsPrivate, "directive stage is private");
        return (int)field.GetValue(directive);
    }

    private static FieldInfo RequirePrivateField(
        string name,
        Type expectedType)
    {
        FieldInfo field = typeof(PassiveDriver).GetField(
            name,
            BindingFlags.Instance | BindingFlags.NonPublic);
        Check.True(field != null, name + " reflection seam");
        Check.Same(
            typeof(PassiveDriver),
            field.DeclaringType,
            name + " declaring type");
        Check.Same(expectedType, field.FieldType, name + " field type");
        Check.True(field.IsPrivate, name + " is private");
        return field;
    }
}
