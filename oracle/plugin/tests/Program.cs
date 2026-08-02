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
            tests.VerifyManifest(
                new Dictionary<string, int>(StringComparer.Ordinal)
                {
                    { "protocol", 1 }
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
