using System;
using System.Collections.Generic;

internal static class PassiveReporterTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("reporter", "ready markers are exact", ReadyMarkers);
        tests.Add("reporter", "completion marker is exact", CompletionMarker);
        tests.Add("reporter", "failure markers are closed", FailureMarkers);
        tests.Add("reporter", "diagnostic is nonterminal", DiagnosticMarker);
    }

    private static void ReadyMarkers()
    {
        FakePassiveLog log = new FakePassiveLog();
        PassiveLogReporter reporter = new PassiveLogReporter(log);
        for (int value = 0; value < OracleProtocol.ExpectedInputCount; value++)
            reporter.Ready(value);
        Check.Sequence(new string[] {
            "Info:SSR oracle passive trace ready: 0/3",
            "Info:SSR oracle passive trace ready: 1/3",
            "Info:SSR oracle passive trace ready: 2/3" }, log.Events.ToArray(),
            "ready markers");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { reporter.Ready(-1); }, "negative ready rejected");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { reporter.Ready(3); }, "complete ready rejected");
    }

    private static void CompletionMarker()
    {
        FakePassiveLog log = new FakePassiveLog();
        new PassiveLogReporter(log).Complete();
        Check.Sequence(new string[] { "Info:SSR oracle passive trace complete" },
            log.Events.ToArray(), "complete marker");
    }

    private static void FailureMarkers()
    {
        FakePassiveLog log = new FakePassiveLog();
        PassiveLogReporter reporter = new PassiveLogReporter(log);
        string[] recordCodes = new string[] {
            "patch_install_failed", "input_before_initial", "overlapping_input",
            "unexpected_input", "unscoped_process_input", "hook_order_mismatch",
            "game_method_exception", "observer_exception", "capture_failed",
            "record_too_large", "initial_settle_timeout", "settle_timeout",
            "state_replaced", "save_path_changed" };
        string[] markerCodes = new string[] {
            "invalid_mode", "invalid_configuration", "invalid_assembly",
            "invalid_reflection", "invalid_path", "trace_exists",
            "save_redirect_failed", "trace_io_failed" };
        ReportCodes(reporter, recordCodes);
        ReportCodes(reporter, markerCodes);
        Check.Equal(recordCodes.Length + markerCodes.Length, log.Events.Count,
            "all known failure markers logged");
        for (int index = 0; index < log.Events.Count; index++)
            Check.True(log.Events[index].StartsWith("Error:SSR oracle passive trace failed: "),
                "closed error marker " + index.ToString());
        Check.Throws<ArgumentException>(delegate { reporter.Failed("unknown"); },
            "unknown failure rejected");
    }

    private static void ReportCodes(PassiveLogReporter reporter, string[] codes)
    {
        for (int index = 0; index < codes.Length; index++) reporter.Failed(codes[index]);
    }

    private static void DiagnosticMarker()
    {
        FakePassiveLog log = new FakePassiveLog();
        PassiveLogReporter reporter = new PassiveLogReporter(log);
        reporter.Diagnostic("detail");
        Check.Sequence(new string[] { "Warning:SSR oracle passive diagnostic: detail" },
            log.Events.ToArray(), "diagnostic marker");
        Check.Throws<ArgumentNullException>(delegate { reporter.Diagnostic(null); },
            "null diagnostic rejected");
    }
}

internal sealed class FakePassiveLog : IPassiveLog
{
    internal readonly List<string> Events = new List<string>();
    public void Info(string message) { Events.Add("Info:" + message); }
    public void Error(string message) { Events.Add("Error:" + message); }
    public void Warning(string message) { Events.Add("Warning:" + message); }
}
