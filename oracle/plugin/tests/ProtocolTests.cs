using System;
using System.Collections.Generic;

internal static class ProtocolTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("protocol", "registry manifest is exact", RegistryManifestIsExact);
    }

    private static void RegistryManifestIsExact()
    {
        TestRegistry registry = new TestRegistry();
        registry.Add("sample", "one", delegate { });
        registry.VerifyManifest(
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "sample", 1 }
            });
        Check.Throws<InvalidOperationException>(
            delegate { registry.Add("sample", "one", delegate { }); },
            "duplicate test identity");
        Check.Throws<InvalidOperationException>(
            delegate
            {
                registry.VerifyManifest(
                    new Dictionary<string, int>(StringComparer.Ordinal)
                    {
                        { "sample", 2 }
                    });
            },
            "manifest count mismatch");
    }
}
