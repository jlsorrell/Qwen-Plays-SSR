using System;
using System.IO;

internal sealed class OracleController :
    IPassiveStartupServices, IDisposable
{
    private readonly OracleMode mode;
    private readonly string outputDirectory;
    private readonly string runName;
    private readonly string tracePath;
    private readonly string saveDirectory;
    private readonly int expectedInputCount;
    private readonly int maxSettleFrames;
    private readonly double maxSettleSeconds;
    private readonly string inputPath;
    private readonly string expectedInitialSha256;
    private readonly ReplayInput replayInput;
    private readonly IOracleGameAdapter adapter;
    private readonly IOracleRuntimeHost runtime;
    private readonly IPassiveLog log;
    private readonly PassiveStartup startup;
    private PassiveLogReporter reporter;
    private ReplayCoordinator replayCoordinator;
    private PassiveDriver driver;
    private PassiveUpdateBoundary updateBoundary;

    internal OracleController(
        PassiveConfiguration configuration,
        IOracleGameAdapter adapter,
        IOracleRuntimeHost runtime,
        IPassiveLog log)
        : this(configuration
            ?? throw new ArgumentNullException("configuration"),
            null, null, adapter, runtime, log)
    { }

    internal OracleController(
        ReplayConfiguration configuration,
        ReplayInput input,
        IOracleGameAdapter adapter,
        IOracleRuntimeHost runtime,
        IPassiveLog log)
        : this(null, configuration
            ?? throw new ArgumentNullException("configuration"),
            input, adapter, runtime, log)
    { }

    private OracleController(
        PassiveConfiguration passive,
        ReplayConfiguration replay,
        ReplayInput input,
        IOracleGameAdapter adapter,
        IOracleRuntimeHost runtime,
        IPassiveLog log)
    {
        if ((passive == null) == (replay == null))
            throw new ArgumentException(
                "exactly one active configuration is required");
        if (replay == null && input != null)
            throw new ArgumentException(
                "passive mode cannot bind replay input", "input");
        if (replay != null && input == null)
            throw new ArgumentNullException("input");
        this.adapter = adapter ?? throw new ArgumentNullException("adapter");
        this.runtime = runtime ?? throw new ArgumentNullException("runtime");
        this.log = log ?? throw new ArgumentNullException("log");
        replayInput = input;
        mode = replay == null ? OracleMode.Passive : OracleMode.Replay;
        if (replay == null)
        {
            outputDirectory = passive.OutputDirectory;
            runName = passive.RunName;
            tracePath = passive.TracePath;
            saveDirectory = passive.SaveDirectory;
            expectedInputCount = passive.ExpectedInputCount;
            maxSettleFrames = passive.MaxSettleFrames;
            maxSettleSeconds = passive.MaxSettleSeconds;
            inputPath = null;
            expectedInitialSha256 = null;
        }
        else
        {
            outputDirectory = replay.OutputDirectory;
            runName = replay.RunName;
            tracePath = replay.TracePath;
            saveDirectory = replay.SaveDirectory;
            expectedInputCount = input.Count;
            maxSettleFrames = replay.MaxSettleFrames;
            maxSettleSeconds = replay.MaxSettleSeconds;
            inputPath = replay.InputPath;
            expectedInitialSha256 = replay.ExpectedInitialSha256;
        }
        startup = new PassiveStartup(this);
    }

    internal bool Start(RunRecord run) { return startup.Start(run); }

    public void Dispose()
    {
        try
        {
            if (replayCoordinator != null) replayCoordinator.Dispose();
        }
        finally { startup.Dispose(); }
    }

    public void ValidateBeforeSink()
    {
        try
        {
            runtime.ValidateAssemblyAndPassiveContract();
            string output = PhysicalPath.ResolveExistingDirectory(
                outputDirectory);
            string save = PhysicalPath.ResolveExistingDirectory(saveDirectory);
            if (output != outputDirectory || save != saveDirectory
                || PhysicalPath.Contains(output, save)
                || PhysicalPath.Contains(save, output))
                throw new IOException("active path identity changed");
            if (mode == OracleMode.Replay)
            {
                string input = PhysicalPath.ResolveExistingFile(inputPath);
                if (input != inputPath
                    || PhysicalPath.Contains(output, input)
                    || PhysicalPath.Contains(save, input))
                    throw new IOException("replay input identity changed");
            }
            PhysicalPathIdentity target =
                PhysicalPath.ResolvePossiblyAbsent(tracePath);
            if (target.Exists)
                throw new PassiveStartupException("trace_exists",
                    new IOException("trace target exists"));
            if (target.CanonicalPath != tracePath
                || target.ExistingAncestor != output
                || target.MissingComponents.Length != 1
                || target.MissingComponents[0] != runName + ".ndjson")
                throw new IOException("trace target identity changed");
        }
        catch (PassiveStartupException) { throw; }
        catch (OracleConfigurationException error)
        { throw new PassiveStartupException(error.Code, error); }
        catch (Exception error)
        { throw new PassiveStartupException("invalid_path", error); }
    }

    public void AuthenticateAndRedirectSave()
    {
        try { adapter.AuthenticateAndRedirectSavePath(saveDirectory); }
        catch (Exception error)
        { throw new PassiveStartupException("save_redirect_failed", error); }
    }

    public PassiveDriver CreateDriver()
    {
        ITraceSink sink;
        try { sink = runtime.CreateTrace(outputDirectory, runName); }
        catch (TraceExistsException error)
        { throw new PassiveStartupException("trace_exists", error); }
        catch (Exception error)
        { throw new PassiveStartupException("trace_io_failed", error); }

        reporter = new PassiveLogReporter(log, mode, expectedInputCount);
        IPassiveReporter driverReporter = reporter;
        if (mode == OracleMode.Replay)
        {
            replayCoordinator = new ReplayCoordinator(
                replayInput, expectedInitialSha256, reporter);
            driverReporter = replayCoordinator;
        }
        driver = new PassiveDriver(sink, driverReporter,
            expectedInputCount, maxSettleFrames, maxSettleSeconds);
        if (replayCoordinator != null)
            replayCoordinator.AttachDriver(driver);
        updateBoundary = new PassiveUpdateBoundary(driver);
        return driver;
    }

    public void InstallPatches() { runtime.InstallPatches(this); }
    public void UnpatchSelf() { runtime.UnpatchSelf(this); }
    public void EmitBootMarker() { log.Info("SSR oracle boot probe loaded"); }
    public void MarkerOnlyFailed(string code) { RequireReporter().Failed(code); }
    public void Diagnostic(string message) { RequireReporter().Diagnostic(message); }

    private PassiveLogReporter RequireReporter()
    {
        PassiveLogReporter value = reporter;
        if (value == null)
            value = new PassiveLogReporter(log, mode, expectedInputCount);
        return value;
    }

    private sealed class AdapterReplayUpdateAccess : IReplayUpdateAccess
    {
        private readonly OracleController owner;

        internal AdapterReplayUpdateAccess(OracleController owner)
        { this.owner = owner; }

        public bool TryGetState(object game, out object stateReference)
        { return owner.adapter.TryGetState(game, out stateReference); }
        public bool VerifySavePath() { return owner.adapter.VerifySavePath(); }
        public bool IsQuiescent(object game, object stateReference)
        { return owner.adapter.IsQuiescent(game, stateReference); }
        public void InvokeUndo(object game) { owner.adapter.InvokeUndo(game); }
    }

    private sealed class AdapterUpdateObservation : IPassiveUpdateObservation
    {
        private readonly OracleController owner;
        private readonly object game;
        internal AdapterUpdateObservation(OracleController owner, object game)
        { this.owner = owner; this.game = game; }
        public bool TryGetState(out object state)
        { return owner.adapter.TryGetState(game, out state); }
        public bool VerifySavePath() { return owner.adapter.VerifySavePath(); }
        public bool IsQuiescent(object state)
        { return owner.adapter.IsQuiescent(game, state); }
        public CaptureRecord Capture(object state)
        {
            CaptureRecord capture = owner.adapter.Capture(state);
            if (owner.replayCoordinator != null)
                owner.replayCoordinator.CaptureObserved(capture);
            return capture;
        }
        public double NowSeconds() { return owner.runtime.NowSeconds(); }
        public DateTime UtcNow() { return owner.runtime.UtcNow(); }
    }

    internal void UpdateEntered(object game)
    {
        if (replayCoordinator != null)
            replayCoordinator.UpdateEntered(
                game, new AdapterReplayUpdateAccess(this));
    }

    internal void ObserveUpdate(object game)
    {
        if (replayCoordinator != null)
            replayCoordinator.UpdateReturned();
        if (updateBoundary != null)
            updateBoundary.Observe(new AdapterUpdateObservation(this, game));
    }

    internal void UpdateThrew()
    {
        try
        {
            if (replayCoordinator != null) replayCoordinator.UpdateThrew();
        }
        finally { driver.TryFault("game_method_exception"); }
    }

    internal bool TryOverridePlayerInput(out int rawDirection)
    {
        if (replayCoordinator == null)
        { rawDirection = 8; return false; }
        return replayCoordinator.TryOverridePlayerInput(out rawDirection);
    }

    internal HookToken PlayerPollEntered() { return driver.PlayerPollEntered(); }

    internal void PhysicalPollReturned(int raw)
    {
        if (replayCoordinator != null)
            replayCoordinator.PhysicalPollReturned(raw);
        driver.PhysicalPollReturned(raw);
    }

    internal void PlayerPollReturned(HookToken token)
    { driver.PlayerPollReturned(token); }
    internal void PlayerPollThrew(HookToken token)
    { driver.PlayerPollThrew(token); }

    internal HookToken ProcessInputEntered(object state, int raw)
    {
        if (replayCoordinator != null)
            replayCoordinator.ProcessInputEntered(state, raw);
        return driver.ProcessInputEntered(state, raw, runtime.NowSeconds());
    }

    internal void ProcessInputReturned(
        HookToken token, bool accepted, object state)
    {
        driver.ProcessInputReturned(
            token, accepted, adapter.MovementScheduled(state));
    }

    internal void ProcessInputThrew(HookToken token)
    { driver.ProcessInputThrew(token); }

    internal HookToken UndoEntered(object game)
    {
        if (replayCoordinator != null) replayCoordinator.UndoEntered();
        object state;
        adapter.TryGetState(game, out state);
        return driver.UndoEntered(state, runtime.NowSeconds());
    }

    internal void RestoreObserved()
    {
        if (replayCoordinator != null) replayCoordinator.RestoreObserved();
        driver.RestoreObserved();
    }

    internal void UndoReturned(HookToken token, object game)
    {
        if (replayCoordinator != null) replayCoordinator.UndoReturned();
        driver.UndoReturned(token, adapter.CurrentMovementScheduled(game));
    }

    internal void UndoThrew(HookToken token) { driver.UndoThrew(token); }

    internal HookToken RestartEntered() { return driver.RestartEntered(); }
    internal void RestartReturned(HookToken token)
    { driver.RestartReturned(token); }
    internal void RestartThrew(HookToken token) { driver.RestartThrew(token); }

    internal HookToken StateSetEntered(object game, object requested)
    {
        object before;
        adapter.TryGetState(game, out before);
        return driver.StateSetEntered(before, requested);
    }

    internal void StateSetReturned(HookToken token, object game)
    {
        object after;
        adapter.TryGetState(game, out after);
        driver.StateSetReturned(token, after, runtime.NowSeconds());
    }

    internal void StateSetThrew(HookToken token)
    { driver.StateSetThrew(token); }
    internal void ClearThrew(HookToken token) { driver.ClearThrew(token); }
    internal void GameMethodFailed()
    { driver.TryFault("game_method_exception"); }
    internal void ObserverFailed() { driver.TryFault("observer_exception"); }
}
