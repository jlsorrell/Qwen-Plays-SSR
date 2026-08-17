using System;
using System.Globalization;

internal sealed class PassiveLogReporter : IPassiveReporter
{
    private readonly IPassiveLog log;
    internal PassiveLogReporter(IPassiveLog log)
    { this.log = log ?? throw new ArgumentNullException("log"); }

    public void Ready(int completedInputs)
    {
        if (completedInputs < 0
            || completedInputs >= OracleProtocol.ExpectedInputCount)
            throw new ArgumentOutOfRangeException("completedInputs");
        log.Info("SSR oracle passive trace ready: "
            + completedInputs.ToString(CultureInfo.InvariantCulture) + "/3");
    }
    public void Complete()
    { log.Info("SSR oracle passive trace complete"); }
    public void Failed(string code)
    {
        if (!OracleErrors.IsRecordCode(code)
            && !OracleMarkerErrors.IsMarkerOnly(code))
            throw new ArgumentException("unknown passive failure code", "code");
        log.Error("SSR oracle passive trace failed: " + code);
    }
    public void Diagnostic(string message)
    {
        if (message == null) throw new ArgumentNullException("message");
        log.Warning("SSR oracle passive diagnostic: " + message);
    }
}
