using System;
using System.IO;

internal sealed class OracleController :
    IPassiveStartupServices, IDisposable
{
    private readonly PassiveConfiguration configuration;
    private readonly IOracleGameAdapter adapter;
    private readonly IOracleRuntimeHost runtime;
    private readonly IPassiveLog log;
    private readonly PassiveLogReporter reporter;
    private readonly PassiveStartup startup;
    private PassiveDriver driver;
    private PassiveUpdateBoundary updateBoundary;

    internal OracleController(
        PassiveConfiguration configuration,
        IOracleGameAdapter adapter,
        IOracleRuntimeHost runtime,
        IPassiveLog log)
    {
        this.configuration = configuration
            ?? throw new ArgumentNullException("configuration");
        this.adapter = adapter ?? throw new ArgumentNullException("adapter");
        this.runtime = runtime ?? throw new ArgumentNullException("runtime");
        this.log = log ?? throw new ArgumentNullException("log");
        reporter = new PassiveLogReporter(log);
        startup = new PassiveStartup(this);
    }

    internal bool Start(RunRecord run) { return startup.Start(run); }
    public void Dispose() { startup.Dispose(); }

    public void ValidateBeforeSink()
    {
        try
        {
            runtime.ValidateAssemblyAndPassiveContract();
            string output = PhysicalPath.ResolveExistingDirectory(
                configuration.OutputDirectory);
            string save = PhysicalPath.ResolveExistingDirectory(
                configuration.SaveDirectory);
            if (output != configuration.OutputDirectory
                || save != configuration.SaveDirectory
                || PhysicalPath.Contains(output, save)
                || PhysicalPath.Contains(save, output))
                throw new IOException("active path identity changed");
            PhysicalPathIdentity target =
                PhysicalPath.ResolvePossiblyAbsent(configuration.TracePath);
            if (target.Exists)
                throw new PassiveStartupException("trace_exists",
                    new IOException("trace target exists"));
            if (target.CanonicalPath != configuration.TracePath
                || target.ExistingAncestor != output
                || target.MissingComponents.Length != 1
                || target.MissingComponents[0]
                    != configuration.RunName + ".ndjson")
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
        try { adapter.AuthenticateAndRedirectSavePath(configuration.SaveDirectory); }
        catch (Exception error)
        { throw new PassiveStartupException("save_redirect_failed", error); }
    }

    public PassiveDriver CreateDriver()
    {
        ITraceSink sink;
        try
        {
            sink = runtime.CreateTrace(
                configuration.OutputDirectory, configuration.RunName);
        }
        catch (TraceExistsException error)
        { throw new PassiveStartupException("trace_exists", error); }
        catch (Exception error)
        { throw new PassiveStartupException("trace_io_failed", error); }
        driver = new PassiveDriver(sink, reporter,
            configuration.ExpectedInputCount, configuration.MaxSettleFrames,
            configuration.MaxSettleSeconds);
        updateBoundary = new PassiveUpdateBoundary(driver);
        return driver;
    }

    public void InstallPatches() { runtime.InstallPatches(this); }
    public void UnpatchSelf() { runtime.UnpatchSelf(this); }
    public void EmitBootMarker() { log.Info("SSR oracle boot probe loaded"); }
    public void MarkerOnlyFailed(string code) { reporter.Failed(code); }
    public void Diagnostic(string message) { reporter.Diagnostic(message); }

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
        { return owner.adapter.Capture(state); }
        public double NowSeconds() { return owner.runtime.NowSeconds(); }
        public DateTime UtcNow() { return owner.runtime.UtcNow(); }
    }

    internal void UpdateEntered(object game) { }
    internal void ObserveUpdate(object game)
    {
        if (updateBoundary != null)
            updateBoundary.Observe(new AdapterUpdateObservation(this, game));
    }

    internal HookToken PlayerPollEntered() { return driver.PlayerPollEntered(); }
    internal void PhysicalPollReturned(int raw)
    { driver.PhysicalPollReturned(raw); }
    internal void PlayerPollReturned(HookToken token)
    { driver.PlayerPollReturned(token); }
    internal void PlayerPollThrew(HookToken token)
    { driver.PlayerPollThrew(token); }

    internal HookToken ProcessInputEntered(object state, int raw)
    {
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
        object state;
        adapter.TryGetState(game, out state);
        return driver.UndoEntered(state, runtime.NowSeconds());
    }
    internal void RestoreObserved() { driver.RestoreObserved(); }
    internal void UndoReturned(HookToken token, object game)
    {
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
