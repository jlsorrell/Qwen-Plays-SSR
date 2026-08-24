using System;
using System.Globalization;

internal sealed class PassiveLogReporter : IPassiveReporter
{
    private readonly IPassiveLog log;
    private readonly string modeName;
    private readonly int expectedInputCount;

    internal PassiveLogReporter(IPassiveLog log)
        : this(log, OracleMode.Passive, OracleProtocol.ExpectedInputCount)
    { }

    internal PassiveLogReporter(IPassiveLog log, OracleMode mode,
        int expectedInputCount)
    {
        this.log = log ?? throw new ArgumentNullException("log");
        if (mode != OracleMode.Passive && mode != OracleMode.Replay)
            throw new ArgumentOutOfRangeException("mode");
        if (expectedInputCount <= 0
            || (mode == OracleMode.Passive
                && expectedInputCount != OracleProtocol.ExpectedInputCount))
            throw new ArgumentOutOfRangeException("expectedInputCount");
        modeName = mode == OracleMode.Passive ? "passive" : "replay";
        this.expectedInputCount = expectedInputCount;
    }

    public void Ready(int completedInputs)
    {
        if (completedInputs < 0
            || completedInputs >= expectedInputCount)
            throw new ArgumentOutOfRangeException("completedInputs");
        log.Info("SSR oracle " + modeName + " trace ready: "
            + completedInputs.ToString(CultureInfo.InvariantCulture) + "/"
            + expectedInputCount.ToString(CultureInfo.InvariantCulture));
    }
    public void Complete()
    { log.Info("SSR oracle " + modeName + " trace complete"); }
    public void Failed(string code)
    {
        if (!OracleErrors.IsRecordCode(code)
            && !OracleMarkerErrors.IsMarkerOnly(code))
            throw new ArgumentException("unknown passive failure code", "code");
        log.Error("SSR oracle " + modeName + " trace failed: " + code);
    }
    public void Diagnostic(string message)
    {
        if (message == null) throw new ArgumentNullException("message");
        log.Warning("SSR oracle " + modeName + " diagnostic: " + message);
    }
}
