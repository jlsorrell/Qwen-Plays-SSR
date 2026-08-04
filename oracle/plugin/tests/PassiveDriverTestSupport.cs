using System;
using System.Collections.Generic;
using System.Reflection;

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
    internal Exception ErrorFailure { get; set; }
    internal Exception CloseFailure { get; set; }
    internal int RunCalls;
    internal int InitialCalls;
    internal int StepCalls;
    internal int EndCalls;
    internal int ErrorCalls;
    internal int CloseCalls;

    public void WriteRun(RunRecord record)
    {
        RunCalls++;
        Add("sink:run");
        if (RunFailure != null)
            throw RunFailure;
        RunRecords.Add(record);
    }

    public void WriteInitial(InitialRecord record)
    {
        InitialCalls++;
        Add("sink:initial");
        if (InitialFailure != null)
            throw InitialFailure;
        InitialRecords.Add(record);
    }

    public void WriteStep(StepRecord record)
    {
        StepCalls++;
        Add("sink:step");
        StepRecords.Add(record);
    }

    public void WriteEnd(EndRecord record)
    {
        EndCalls++;
        Add("sink:end");
        EndRecords.Add(record);
    }

    public void WriteError(ErrorRecord record)
    {
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
    internal Exception FailedFailure { get; set; }
    internal Exception DiagnosticFailure { get; set; }
    internal int CompleteCalls;
    internal int FailedCalls;
    internal int DiagnosticCalls;

    public void Ready(int completedInputs)
    {
        ReadyValues.Add(completedInputs);
        Add("report:ready:" + completedInputs.ToString() + "/3");
        if (ReadyFailure != null)
            throw ReadyFailure;
    }

    public void Complete()
    {
        CompleteCalls++;
        Add("report:complete");
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
        if (DiagnosticFailure != null)
            throw DiagnosticFailure;
    }

    private void Add(string value)
    {
        events.Add(value);
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
        DriverFixture fixture = Active();
        fixture.Observe(
            fixture.State,
            true,
            fixture.State,
            true,
            1.0,
            true,
            ProtocolSamples.Capture("ready-a"));
        fixture.Neutral();
        fixture.Observe(
            fixture.State,
            true,
            fixture.State,
            true,
            2.0,
            true,
            ProtocolSamples.Capture("ready-pair"));
        fixture.Observe(
            fixture.State,
            true,
            fixture.State,
            true,
            3.0,
            true,
            ProtocolSamples.Capture("ready-pair"));
        Check.Equal(
            PassivePhase.Ready,
            fixture.Driver.Phase,
            "ready fixture");
        return fixture;
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

    internal void SetNeutralSeenForDefensiveTest(bool value)
    {
        SetPrivateField("neutralSeen", typeof(bool), value);
    }

    internal void AssertCandidateClearedForDefensiveTest(string label)
    {
        FieldInfo field = RequirePrivateField(
            "candidateSignature", typeof(byte[]));
        Check.True(field.GetValue(Driver) == null, label);
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
