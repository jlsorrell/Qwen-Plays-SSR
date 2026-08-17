using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;

internal static class PassiveStartupTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("startup", "off invokes only legacy validation then boot",
            OffCallsAreExact);
        tests.Add("startup", "off preserves legacy failure identity",
            LegacyFailureIdentity);
        tests.Add("startup",
            "run flush precedes patches and activation precedes boot", StartOrder);
        tests.Add("startup", "typed pre-driver failures stay marker only",
            PreDriverFailures);
        tests.Add("startup", "prepare failure is not reported twice",
            PrepareFailure);
        tests.Add("startup", "owned startup failures use driver arbitration",
            OwnedFailures);
        tests.Add("startup", "teardown is ordered and idempotent",
            TeardownIsIdempotent);
    }

    private static void OffCallsAreExact()
    {
        List<string> events = new List<string>();
        PluginModePolicy.StartOff(OffConfiguration(),
            delegate { events.Add("validate"); }, delegate { events.Add("boot"); });
        Check.Sequence(new string[] { "validate", "boot" }, events.ToArray(),
            "off calls are exact");
    }

    private static void LegacyFailureIdentity()
    {
        Exception original = new InvalidOperationException("legacy");
        Exception caught = null;
        try
        {
            PluginModePolicy.StartOff(OffConfiguration(),
                delegate { throw original; }, delegate { throw new Exception("boot"); });
        }
        catch (Exception error) { caught = error; }
        Check.Same(original, caught, "legacy exception identity");
    }

    private static void StartOrder()
    {
        FakePassiveStartupServices services = new FakePassiveStartupServices();
        PassiveStartup startup = new PassiveStartup(services);
        Check.True(startup.Start(ProtocolSamples.Run), "startup success");
        Check.Sequence(new string[] {
            "validate", "redirect", "create-driver", "sink:run",
            "install:Disabled", "boot:AwaitGame" }, services.Events.ToArray(),
            "startup order");
        startup.Dispose();
    }

    private static void PreDriverFailures()
    {
        string[,] cases = new string[,] {
            { "validate", "invalid_configuration" },
            { "validate", "invalid_assembly" },
            { "validate", "invalid_reflection" },
            { "validate", "invalid_path" },
            { "validate", "trace_exists" },
            { "redirect", "save_redirect_failed" },
            { "create-driver", "trace_exists" },
            { "create-driver", "trace_io_failed" }
        };
        for (int index = 0; index < cases.GetLength(0); index++)
        {
            FakePassiveStartupServices services = new FakePassiveStartupServices();
            services.PreDriverStage = cases[index, 0];
            services.PreDriverCode = cases[index, 1];
            PassiveStartup startup = new PassiveStartup(services);
            Check.False(startup.Start(ProtocolSamples.Run), "pre-driver failure " + index);
            Check.Equal(1, Count(services.Events,
                "marker:" + cases[index, 1]), "one marker " + index);
            Check.Equal(0, services.Sink.RunCalls, "no Run " + index);
            Check.Equal(0, services.InstallCalls, "no install " + index);
            Check.Equal(0, services.Reporter.FailedCalls, "no driver failure " + index);
            startup.Dispose();
        }
    }

    private static void PrepareFailure()
    {
        FakePassiveStartupServices services = new FakePassiveStartupServices();
        services.Sink.RunFailure = new IOException("run");
        PassiveStartup startup = new PassiveStartup(services);
        Check.False(startup.Start(ProtocolSamples.Run), "prepare failure");
        Check.Equal(1, services.Reporter.FailedCalls, "one driver failure");
        Check.Sequence(new string[] { "trace_io_failed" },
            services.Reporter.FailedCodes.ToArray(), "driver owns trace IO");
        Check.Equal(0, services.InstallCalls, "no patches after prepare failure");
        startup.Dispose();
    }

    private static void OwnedFailures()
    {
        AssertOwnedFailure("install", "patch_install_failed");
        AssertOwnedFailure("activate", "observer_exception");
        AssertOwnedFailure("boot", "observer_exception");
    }

    private static void AssertOwnedFailure(string stage, string expectedCode)
    {
        FakePassiveStartupServices services = new FakePassiveStartupServices();
        services.OwnedFailureStage = stage;
        PassiveStartup startup = new PassiveStartup(services);
        Check.False(startup.Start(ProtocolSamples.Run), "owned failure " + stage);
        Check.Sequence(new string[] { expectedCode }, services.Reporter.FailedCodes.ToArray(),
            "driver arbitration " + stage);
        AssertDriverDisabled(services.Driver, "owned failure disables " + stage);
        Check.Equal(1, services.UnpatchCalls, "unpatch after " + stage);
        Check.True(services.Diagnostics.Count >= 1, "diagnostic after " + stage);
        startup.Dispose();
        Check.Equal(1, services.UnpatchCalls, "unpatch remains owned " + stage);
    }

    private static void TeardownIsIdempotent()
    {
        FakePassiveStartupServices services = new FakePassiveStartupServices();
        services.ProbeDriverFaultDuringUnpatch = true;
        PassiveStartup startup = new PassiveStartup(services);
        Check.True(startup.Start(ProtocolSamples.Run), "started");
        startup.Dispose();
        startup.Dispose();
        AssertDriverDisabled(services.Driver, "double dispose disables driver");
        Check.False(services.UnpatchFaultWon,
            "driver disabled before unpatch");
        Check.Equal(1, services.UnpatchCalls, "one owner unpatch");
        Check.Equal(1, services.Sink.CloseCalls, "one sink close");
        Check.Equal(0, services.Reporter.FailedCalls, "no fabricated terminal record");
        Check.Equal(0, services.Sink.ErrorCalls, "no fabricated error record");
    }

    private static OracleConfiguration OffConfiguration()
    {
        return OracleConfiguration.Parse(new byte[] {
            (byte)'[', (byte)'O', (byte)'r', (byte)'a', (byte)'c', (byte)'l',
            (byte)'e', (byte)']', (byte)'\n', (byte)'M', (byte)'o', (byte)'d',
            (byte)'e', (byte)'=', (byte)'o', (byte)'f', (byte)'f', (byte)'\n' },
            new FakeConfigurationPathResolver());
    }

    private static int Count(IList<string> values, string expected)
    {
        int count = 0;
        for (int index = 0; index < values.Count; index++)
            if (values[index] == expected) count++;
        return count;
    }

    private static void AssertDriverDisabled(PassiveDriver driver, string message)
    {
        FieldInfo field = typeof(PassiveDriver).GetField("disabled",
            BindingFlags.Instance | BindingFlags.NonPublic);
        Check.True(field != null, message + " field");
        Check.Equal(1, (int)field.GetValue(driver), message);
    }
}

internal sealed class FakePassiveStartupServices : IPassiveStartupServices
{
    internal readonly List<string> Events = new List<string>();
    internal readonly List<string> Diagnostics = new List<string>();
    internal readonly FakeTraceSink Sink;
    internal readonly FakePassiveReporter Reporter;
    internal PassiveDriver Driver;
    internal string PreDriverStage;
    internal string PreDriverCode;
    internal string OwnedFailureStage;
    internal bool ProbeDriverFaultDuringUnpatch;
    internal bool UnpatchFaultWon;
    internal int InstallCalls;
    internal int UnpatchCalls;

    internal FakePassiveStartupServices()
    {
        Sink = new FakeTraceSink(Events);
        Reporter = new FakePassiveReporter(Events);
    }

    public void ValidateBeforeSink()
    {
        Events.Add("validate");
        ThrowPreDriver("validate");
    }

    public void AuthenticateAndRedirectSave()
    {
        Events.Add("redirect");
        ThrowPreDriver("redirect");
    }

    public PassiveDriver CreateDriver()
    {
        Events.Add("create-driver");
        ThrowPreDriver("create-driver");
        Driver = new PassiveDriver(Sink, Reporter, OracleProtocol.ExpectedInputCount,
            OracleProtocol.MaxSettleFrames, OracleProtocol.MaxSettleSeconds);
        return Driver;
    }

    public void InstallPatches()
    {
        InstallCalls++;
        Events.Add("install:" + Driver.Phase.ToString());
        ThrowOwned("install");
    }

    public void EmitBootMarker()
    {
        Events.Add("boot:" + Driver.Phase.ToString());
        ThrowOwned("boot");
    }

    public void UnpatchSelf()
    {
        UnpatchCalls++;
        Events.Add("unpatch");
        if (ProbeDriverFaultDuringUnpatch)
            UnpatchFaultWon = Driver.TryFault("observer_exception");
    }

    public void MarkerOnlyFailed(string code) { Events.Add("marker:" + code); }
    public void Diagnostic(string message) { Diagnostics.Add(message); Events.Add("diagnostic"); }

    private void ThrowPreDriver(string stage)
    {
        if (PreDriverStage == stage)
            throw new PassiveStartupException(PreDriverCode,
                new InvalidOperationException(stage));
    }

    private void ThrowOwned(string stage)
    {
        if (OwnedFailureStage == stage)
            throw new InvalidOperationException(stage);
        if (OwnedFailureStage == "activate" && stage == "install"
            && !Driver.Activate())
            throw new InvalidOperationException("activation setup");
    }
}
