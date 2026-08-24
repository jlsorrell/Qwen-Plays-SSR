using System;
using System.Collections.Generic;

internal static class Program
{
private static int Main(string[] args)
{
    try
    {
        HarnessOptions options = HarnessOptions.Parse(args);
        TestRegistry tests = new TestRegistry();
        ProtocolTests.Register(tests);
        EncodingTests.Register(tests);
        CaptureSignatureTests.Register(tests);
        TraceSinkTests.Register(tests);
        PassiveDriverTests.Register(tests);
        ReplayInputTests.Register(tests);
        ReplayCoordinatorTests.Register(tests);
        ControllerReplayTests.Register(tests);
        ConfigurationTests.Register(tests, options);
        PhysicalPathTests.Register(tests);
        GameObservationTests.Register(tests);
        PatchBoundaryTests.Register(tests);
        PassiveStartupTests.Register(tests);
        PassiveReporterTests.Register(tests);
        AssemblySurfaceTests.Register(tests, options);
        tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
        {
            { "protocol", 6 },
            { "encoding", 6 },
            { "sink", 6 },
            { "driver-boundary", 2 },
            { "driver-initial", 8 },
            { "driver-input", 8 },
            { "driver-terminal", 6 },
            { "replay-input", 6 },
            { "replay-coordinator", 8 },
            { "controller-replay", 7 },
            { "config", 8 },
            { "path", 7 },
            { "observation", 5 },
            { "boundary", 5 },
            { "startup", 7 },
            { "reporter", 5 },
            { "assembly", 5 },
            { "plugin", 8 }
        });
        int result = tests.Run(options.Cohort);
        if (result != 0)
            return result;
        Console.WriteLine("SSR oracle unit harness ready");
        return 0;
    }
    catch (Exception error)
    {
        Console.Error.WriteLine(error.ToString());
        return 1;
    }
}
}
