using System;

internal interface IPassiveStartupServices
{
    void ValidateBeforeSink();
    void AuthenticateAndRedirectSave();
    PassiveDriver CreateDriver();
    void InstallPatches();
    void EmitBootMarker();
    void UnpatchSelf();
    void MarkerOnlyFailed(string code);
    void Diagnostic(string message);
}

internal sealed class PassiveStartupException : Exception
{
    internal PassiveStartupException(string code, Exception inner)
        : base(code, inner)
    {
        if (code != "invalid_mode" && code != "invalid_configuration"
            && code != "invalid_assembly" && code != "invalid_reflection"
            && code != "invalid_path" && code != "trace_exists"
            && code != "save_redirect_failed" && code != "trace_io_failed")
            throw new ArgumentException("invalid startup code", "code");
        Code = code;
    }
    internal string Code { get; private set; }
}

internal sealed class PassiveStartup : IDisposable
{
    private readonly IPassiveStartupServices services;
    private PassiveDriver driver;
    private bool started;
    private bool patchesMayExist;
    private bool disposed;

    internal PassiveStartup(IPassiveStartupServices services)
    { this.services = services ?? throw new ArgumentNullException("services"); }

    internal bool Start(RunRecord run)
    {
        if (started) throw new InvalidOperationException("startup already attempted");
        if (run == null) throw new ArgumentNullException("run");
        started = true;
        try
        {
            services.ValidateBeforeSink();
            services.AuthenticateAndRedirectSave();
            driver = services.CreateDriver();
            if (driver == null)
                throw new PassiveStartupException("trace_io_failed",
                    new InvalidOperationException("driver factory returned null"));
        }
        catch (PassiveStartupException error)
        {
            SafeMarker(error.Code);
            return false;
        }
        if (!driver.Prepare(run)) return false;
        patchesMayExist = true;
        try { services.InstallPatches(); }
        catch (Exception error)
        {
            SafeDiagnostic(error); OwnedFailure("patch_install_failed"); return false;
        }
        try
        {
            if (!driver.Activate())
                throw new InvalidOperationException("driver activation failed");
            services.EmitBootMarker();
            return true;
        }
        catch (Exception error)
        {
            SafeDiagnostic(error); OwnedFailure("observer_exception"); return false;
        }
    }

    public void Dispose()
    {
        if (disposed) return;
        disposed = true;
        SafeDisable(); SafeUnpatch();
        if (driver != null)
        {
            try { driver.Dispose(); }
            catch (Exception error) { SafeDiagnostic(error); }
        }
    }

    private void OwnedFailure(string code)
    {
        try { driver.TryFault(code); }
        catch (Exception error) { SafeDiagnostic(error); }
        SafeDisable(); SafeUnpatch();
    }
    private void SafeDisable()
    {
        if (driver == null) return;
        try { driver.Disable(); }
        catch (Exception error) { SafeDiagnostic(error); }
    }
    private void SafeUnpatch()
    {
        if (!patchesMayExist) return;
        patchesMayExist = false;
        try { services.UnpatchSelf(); }
        catch (Exception error) { SafeDiagnostic(error); }
    }
    private void SafeMarker(string code)
    {
        try { services.MarkerOnlyFailed(code); }
        catch (Exception error) { SafeDiagnostic(error); }
    }
    private void SafeDiagnostic(Exception error)
    {
        try { services.Diagnostic(error.GetType().FullName); }
        catch (Exception) { }
    }
}
