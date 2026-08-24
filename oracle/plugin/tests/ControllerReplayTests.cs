using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

internal sealed class ControllerReplayAdapter : IOracleGameAdapter
{
    private readonly IList<string> events;

    internal ControllerReplayAdapter(IList<string> events, object state)
    {
        this.events = events;
        State = state;
    }

    internal object State;
    internal bool StateAvailable = true;
    internal bool SavePathMatches = true;
    internal bool Quiescent = true;
    internal bool Movement = true;
    internal bool CurrentMovement = false;
    internal CaptureRecord CaptureValue = ProtocolSamples.InitialCapture;
    internal Action StateObserved;
    internal Action UndoAction;
    internal int RedirectCalls;
    internal int StateCalls;
    internal int PathCalls;
    internal int GateCalls;
    internal int CaptureCalls;
    internal int MovementCalls;
    internal int CurrentMovementCalls;
    internal int InvokeUndoCalls;

    public void AuthenticateAndRedirectSavePath(string isolatedPath)
    {
        RedirectCalls++;
        events.Add("adapter:redirect");
    }

    public bool VerifySavePath()
    {
        PathCalls++;
        events.Add("adapter:path");
        return SavePathMatches;
    }

    public bool TryGetState(object game, out object stateReference)
    {
        StateCalls++;
        events.Add("adapter:state");
        if (StateObserved != null) StateObserved();
        stateReference = State;
        return StateAvailable;
    }

    public bool IsQuiescent(object game, object verifiedState)
    {
        GateCalls++;
        events.Add("adapter:gate");
        Check.Same(State, verifiedState, "controller gate state");
        return Quiescent;
    }

    public bool MovementScheduled(object stateReference)
    {
        MovementCalls++;
        events.Add("adapter:movement");
        Check.Same(State, stateReference, "controller movement state");
        return Movement;
    }

    public bool CurrentMovementScheduled(object game)
    {
        CurrentMovementCalls++;
        events.Add("adapter:current-movement");
        return CurrentMovement;
    }

    public CaptureRecord Capture(object verifiedState)
    {
        CaptureCalls++;
        events.Add("adapter:capture");
        Check.Same(State, verifiedState, "controller capture state");
        return CaptureValue;
    }

    public void InvokeUndo(object game)
    {
        InvokeUndoCalls++;
        events.Add("adapter:undo");
        if (UndoAction != null) UndoAction();
    }
}

internal sealed class ControllerReplayRuntime : IOracleRuntimeHost
{
    private readonly IList<string> events;
    private readonly ITraceSink sink;

    internal ControllerReplayRuntime(IList<string> events, ITraceSink sink)
    {
        this.events = events;
        this.sink = sink;
        Utc = DriverFixture.UtcFinish;
    }

    internal double Now;
    internal DateTime Utc;
    internal int ValidateCalls;
    internal int TraceCalls;
    internal int PatchCalls;
    internal int UnpatchCalls;

    public void ValidateAssemblyAndPassiveContract()
    {
        ValidateCalls++;
        events.Add("runtime:validate");
    }

    public ITraceSink CreateTrace(string outputDirectory, string runName)
    {
        TraceCalls++;
        events.Add("runtime:trace");
        return sink;
    }

    public void InstallPatches(OracleController controller)
    {
        PatchCalls++;
        events.Add("runtime:patch");
    }

    public void UnpatchSelf(OracleController controller)
    {
        UnpatchCalls++;
        events.Add("runtime:unpatch");
    }

    public double NowSeconds() { return Now; }
    public DateTime UtcNow() { return Utc; }
}

internal sealed class ControllerReplayLog : IPassiveLog
{
    private readonly IList<string> events;

    internal ControllerReplayLog(IList<string> events)
    { this.events = events; }

    public void Info(string message) { events.Add("Info:" + message); }
    public void Error(string message) { events.Add("Error:" + message); }
    public void Warning(string message) { events.Add("Warning:" + message); }
}

internal sealed class ControllerReplayFixture : IDisposable
{
    internal static readonly DateTime StartedUtc =
        new DateTime(2026, 8, 17, 12, 0, 0, DateTimeKind.Utc);

    private readonly string root;
    internal readonly List<string> Events = new List<string>();
    internal readonly object Game = new object();
    internal readonly object State = new object();
    internal readonly FakeTraceSink Sink;
    internal readonly ControllerReplayAdapter Adapter;
    internal readonly ControllerReplayRuntime Runtime;
    internal readonly ControllerReplayLog Log;
    internal readonly ReplayInput Input;
    internal readonly OracleController Controller;

    internal ControllerReplayFixture(string tokens, string expectedInitialSha256)
    {
        root = Path.Combine("/private/tmp",
            "ssr-controller-replay-" + Guid.NewGuid().ToString("N"));
        string requestedOutput = Path.Combine(root, "output");
        string requestedSave = Path.Combine(root, "save");
        Directory.CreateDirectory(requestedOutput);
        Directory.CreateDirectory(requestedSave);
        byte[] inputBytes = Encoding.UTF8.GetBytes(tokens);
        string requestedInput = Path.Combine(root, "input.dem");
        File.WriteAllBytes(requestedInput, inputBytes);
        string output = PhysicalPath.ResolveExistingDirectory(requestedOutput);
        string save = PhysicalPath.ResolveExistingDirectory(requestedSave);
        string inputPath = PhysicalPath.ResolveExistingFile(requestedInput);
        Input = ReplayInput.Parse(inputBytes);
        Sink = new FakeTraceSink(Events);
        Adapter = new ControllerReplayAdapter(Events, State);
        Runtime = new ControllerReplayRuntime(Events, Sink);
        Runtime.Utc = StartedUtc.AddMinutes(1.0);
        Log = new ControllerReplayLog(Events);
        ReplayConfiguration configuration = new ReplayConfiguration(
            output, "controller-replay", Path.Combine(
                output, "controller-replay.ndjson"), save, inputPath,
            expectedInitialSha256);
        Controller = new OracleController(
            configuration, Input, Adapter, Runtime, Log);
        RunRecord run = new RunRecord(
            ProtocolSamples.RunId, OracleMode.Replay,
            OracleProtocol.ExpectedAssemblySha256, Input.Sha256, Input.Count,
            StartedUtc);
        Check.True(Controller.Start(run), "replay controller start");
    }

    internal static ControllerReplayFixture Create(string tokens)
    { return new ControllerReplayFixture(tokens, ""); }

    internal void ReachReady(string rawSave)
    {
        Observe(ProtocolSamples.Capture("epoch"));
        NeutralPoll();
        CaptureRecord first = ProtocolSamples.Capture(rawSave);
        Observe(first);
        CaptureRecord second = ProtocolSamples.Capture(rawSave);
        Adapter.CaptureValue = second;
        ObserveCurrent();
        Check.Equal(1, Sink.InitialRecords.Count, "controller Initial count");
        Check.Same(second, Sink.InitialRecords[0].Capture,
            "controller returns the captured reference to driver");
    }

    internal void NeutralPoll()
    {
        HookToken poll = Controller.PlayerPollEntered();
        int raw;
        Check.True(Controller.TryOverridePlayerInput(out raw),
            "replay suppresses physical input");
        Check.Equal(8, raw, "replay neutral override");
        Controller.PhysicalPollReturned(raw);
        Controller.PlayerPollReturned(poll);
    }

    internal void ArmCardinal(bool accepted, bool movement)
    {
        Adapter.Movement = movement;
        Controller.UpdateEntered(Game);
        HookToken poll = Controller.PlayerPollEntered();
        int raw;
        Check.True(Controller.TryOverridePlayerInput(out raw),
            "cardinal override is active");
        Check.True(raw >= 0 && raw <= 3, "cardinal raw value");
        Controller.PhysicalPollReturned(raw);
        HookToken input = Controller.ProcessInputEntered(State, raw);
        Controller.ProcessInputReturned(input, accepted, State);
        Controller.PlayerPollReturned(poll);
    }

    internal void ReturnOwningUpdate()
    {
        AdvanceClock();
        Controller.ObserveUpdate(Game);
    }

    internal void Settle(CaptureRecord capture)
    {
        NeutralPoll();
        Observe(capture);
        Observe(capture);
    }

    internal void Observe(CaptureRecord capture)
    {
        Adapter.CaptureValue = capture;
        Controller.UpdateEntered(Game);
        ObserveCurrent();
    }

    internal void ObserveCurrent()
    {
        AdvanceClock();
        Controller.ObserveUpdate(Game);
    }

    private void AdvanceClock()
    {
        Runtime.Now += 1.0;
        Runtime.Utc = Runtime.Utc.AddSeconds(1.0);
    }

    public void Dispose()
    {
        Controller.Dispose();
        if (Directory.Exists(root)) Directory.Delete(root, true);
    }

    internal static string HashRawSave(string value)
    {
        byte[] digest;
        using (SHA256 hash = SHA256.Create())
            digest = hash.ComputeHash(new UTF8Encoding(false, true).GetBytes(value));
        StringBuilder text = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
            text.Append(digest[index].ToString(
                "x2", CultureInfo.InvariantCulture));
        return text.ToString();
    }
}

internal static class ControllerReplayTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("controller-replay", "passive preserves native input",
            PassivePreservesNativeInput);
        tests.Add("controller-replay", "replay construction binds dynamic run",
            ReplayConstructionBindsDynamicRun);
        tests.Add("controller-replay", "capture reaches signature before Ready",
            CaptureReachesSignatureBeforeReady);
        tests.Add("controller-replay", "update alignment precedes driver observation",
            UpdateAlignmentPrecedesDriverObservation);
        tests.Add("controller-replay", "cardinal hook lifecycle is routed once",
            CardinalHookLifecycleIsRoutedOnce);
        tests.Add("controller-replay", "Undo uses adapter and existing hooks",
            UndoUsesAdapterAndExistingHooks);
        tests.Add("controller-replay", "failure and teardown never reissue input",
            FailureAndTeardownNeverReissueInput);
    }

    private static void PassivePreservesNativeInput()
    {
        string root = Path.Combine("/private/tmp",
            "ssr-controller-passive-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(Path.Combine(root, "output"));
        Directory.CreateDirectory(Path.Combine(root, "save"));
        List<string> events = new List<string>();
        FakeTraceSink sink = new FakeTraceSink(events);
        ControllerReplayAdapter adapter =
            new ControllerReplayAdapter(events, new object());
        ControllerReplayRuntime runtime =
            new ControllerReplayRuntime(events, sink);
        OracleController controller = null;
        try
        {
            string output = PhysicalPath.ResolveExistingDirectory(
                Path.Combine(root, "output"));
            string save = PhysicalPath.ResolveExistingDirectory(
                Path.Combine(root, "save"));
            controller = new OracleController(new PassiveConfiguration(
                output, "controller-passive", Path.Combine(
                    output, "controller-passive.ndjson"), save),
                adapter, runtime, new ControllerReplayLog(events));
            Check.True(controller.Start(ProtocolSamples.Run),
                "passive controller start");
            int raw;
            Check.False(controller.TryOverridePlayerInput(out raw),
                "passive leaves Playerinputstring native");
            Check.Equal(8, raw, "passive nonoverride default");
            controller.UpdateEntered(new object());
            Check.Equal(0, adapter.InvokeUndoCalls,
                "passive never invokes native Undo");
        }
        finally
        {
            if (controller != null) controller.Dispose();
            if (Directory.Exists(root)) Directory.Delete(root, true);
        }
    }

    private static void ReplayConstructionBindsDynamicRun()
    {
        using (ControllerReplayFixture fixture =
            ControllerReplayFixture.Create("North\nSouth\n"))
        {
            Check.Equal(1, fixture.Sink.RunRecords.Count,
                "dynamic replay Run count");
            RunRecord run = fixture.Sink.RunRecords[0];
            Check.Equal(OracleMode.Replay, run.Mode, "dynamic Run mode");
            Check.Equal(fixture.Input.Sha256, run.InputSha256,
                "dynamic Run hash");
            Check.Equal(2, run.ExpectedInputCount, "dynamic Run count");
            fixture.ReachReady("dynamic-ready");
            Check.True(fixture.Events.Contains(
                "Info:SSR oracle replay trace ready: 0/2"),
                "dynamic reporter denominator");
            Check.Equal(1, fixture.Runtime.ValidateCalls,
                "Start revalidates replay contract once");
            Check.Equal(1, fixture.Runtime.TraceCalls,
                "one replay sink factory");
        }
    }

    private static void CaptureReachesSignatureBeforeReady()
    {
        const string rawSave = "signature-before-ready";
        using (ControllerReplayFixture fixture = new ControllerReplayFixture(
            "West\n", ControllerReplayFixture.HashRawSave(rawSave)))
        {
            fixture.ReachReady(rawSave);
            Check.True(fixture.Events.Contains(
                "Info:SSR oracle replay trace ready: 0/1"),
                "signature authorizes Ready");
            Check.Equal(0, fixture.Sink.ErrorRecords.Count,
                "signature path has no Error");
            int initial = fixture.Events.IndexOf("sink:initial");
            int ready = fixture.Events.IndexOf(
                "Info:SSR oracle replay trace ready: 0/1");
            Check.True(initial >= 0 && initial < ready,
                "Initial durability precedes replay Ready marker");
        }
    }

    private static void UpdateAlignmentPrecedesDriverObservation()
    {
        using (ControllerReplayFixture fixture =
            ControllerReplayFixture.Create("North\n"))
        {
            fixture.ReachReady("alignment");
            fixture.ArmCardinal(true, true);
            int probes = 0;
            fixture.Adapter.StateObserved = delegate
            {
                fixture.Adapter.StateObserved = null;
                probes++;
                int raw;
                Check.True(fixture.Controller.TryOverridePlayerInput(out raw),
                    "observation-time replay suppression");
                Check.Equal(8, raw,
                    "owning cardinal is deasserted before observation");
            };
            fixture.ReturnOwningUpdate();
            Check.Equal(1, probes, "one observation-time alignment probe");
            Check.Equal(0, fixture.Sink.ErrorRecords.Count,
                "observation after alignment cannot duplicate override");
        }
    }

    private static void CardinalHookLifecycleIsRoutedOnce()
    {
        using (ControllerReplayFixture fixture =
            ControllerReplayFixture.Create("East\n"))
        {
            fixture.ReachReady("cardinal-initial");
            fixture.ArmCardinal(true, true);
            fixture.ReturnOwningUpdate();
            fixture.Settle(ProtocolSamples.Capture("cardinal-settled"));

            Check.Equal(1, fixture.Adapter.MovementCalls,
                "cardinal movement observed once");
            Check.Equal(1, fixture.Sink.StepRecords.Count,
                "cardinal Step count");
            StepRecord step = fixture.Sink.StepRecords[0];
            Check.Equal(OracleInput.East, step.Input, "cardinal Step input");
            Check.True(step.Accepted, "cardinal Step accepted");
            Check.True(step.MovementScheduled,
                "cardinal Step movement scheduled");
            Check.Equal(1, fixture.Sink.EndRecords.Count,
                "cardinal End count");
            Check.Equal(1, fixture.Sink.CloseCalls,
                "cardinal sink Close count");
            RequireSubsequence(fixture.Events, new string[]
            {
                "sink:run", "runtime:patch",
                "Info:SSR oracle boot probe loaded", "sink:initial",
                "Info:SSR oracle replay trace ready: 0/1", "sink:step:0",
                "sink:end", "sink:close",
                "Info:SSR oracle replay trace complete"
            }, "cardinal controller event order");
        }
    }

    private static void UndoUsesAdapterAndExistingHooks()
    {
        using (ControllerReplayFixture fixture =
            ControllerReplayFixture.Create("Undo\n"))
        {
            fixture.ReachReady("undo-initial");
            fixture.Adapter.UndoAction = delegate
            {
                HookToken token = fixture.Controller.UndoEntered(fixture.Game);
                fixture.Controller.RestoreObserved();
                fixture.Controller.UndoReturned(token, fixture.Game);
            };
            fixture.Controller.UpdateEntered(fixture.Game);
            fixture.ReturnOwningUpdate();
            fixture.Settle(ProtocolSamples.Capture("undo-settled"));

            Check.Equal(1, fixture.Adapter.InvokeUndoCalls,
                "public Undo invoked once");
            Check.Equal(1, fixture.Adapter.CurrentMovementCalls,
                "existing Undo hook movement observed once");
            Check.Equal(0, fixture.Adapter.MovementCalls,
                "Undo never uses cardinal movement callback");
            Check.Equal(1, fixture.Sink.StepRecords.Count, "Undo Step count");
            StepRecord step = fixture.Sink.StepRecords[0];
            Check.Equal(OracleInput.Undo, step.Input, "Undo Step input");
            Check.True(step.Accepted, "Restore accepts Undo");
            Check.False(step.MovementScheduled, "Undo movement false");
        }
    }

    private static void FailureAndTeardownNeverReissueInput()
    {
        using (ControllerReplayFixture fixture =
            ControllerReplayFixture.Create("Undo\n"))
        {
            fixture.ReachReady("terminal-initial");
            fixture.Adapter.UndoAction = delegate
            {
                HookToken token = fixture.Controller.UndoEntered(fixture.Game);
                fixture.Controller.RestoreObserved();
                fixture.Controller.UndoReturned(token, fixture.Game);
            };
            fixture.Controller.UpdateEntered(fixture.Game);
            Check.Equal(1, fixture.Adapter.InvokeUndoCalls,
                "terminal fixture invokes token once");
            fixture.Controller.UpdateThrew();
            fixture.Controller.UpdateEntered(fixture.Game);
            fixture.Controller.UpdateEntered(fixture.Game);
            int raw;
            Check.True(fixture.Controller.TryOverridePlayerInput(out raw),
                "terminal replay remains suppressing");
            Check.Equal(8, raw, "terminal replay returns None");
            fixture.Controller.Dispose();
            fixture.Controller.Dispose();
            fixture.Controller.UpdateEntered(fixture.Game);

            Check.Equal(1, fixture.Adapter.InvokeUndoCalls,
                "failure and teardown never reissue Undo");
            Check.Equal(1, fixture.Sink.ErrorRecords.Count,
                "one terminal Error");
            Check.Equal("game_method_exception",
                fixture.Sink.ErrorRecords[0].Code, "Update throw code");
            Check.Equal(1, fixture.Runtime.UnpatchCalls,
                "teardown unpatches once");
            Check.Equal(1, fixture.Sink.CloseCalls,
                "terminal sink closes once");
        }
    }

    private static void RequireSubsequence(
        IList<string> actual, string[] expected, string message)
    {
        int next = 0;
        for (int index = 0; index < actual.Count && next < expected.Length; index++)
            if (actual[index] == expected[next]) next++;
        Check.Equal(expected.Length, next, message);
    }
}
