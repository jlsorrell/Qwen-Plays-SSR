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
        registry.Add("protocol", "registry manifest is exact", delegate { });
        registry.VerifyManifest(
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });
        Check.Throws<InvalidOperationException>(
            delegate
            {
                registry.Add(
                    "protocol", "registry manifest is exact", delegate { });
            },
            "duplicate test identity");

        TestRegistry renamed = new TestRegistry();
        renamed.Add("protocol", "registry manifest was renamed", delegate { });
        bool renameRejected = RejectsManifest(
            renamed,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry swapped = new TestRegistry();
        swapped.Add("encoding", "registry manifest is exact", delegate { });
        swapped.Add("protocol", "golden fixture bytes", delegate { });
        bool swapRejected = RejectsManifest(
            swapped,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 },
                { "encoding", 1 }
            });

        TestRegistry reordered = new TestRegistry();
        reordered.Add("protocol", "closed error tables", delegate { });
        reordered.Add("protocol", "registry manifest is exact", delegate { });
        bool reorderRejected = RejectsManifest(
            reordered,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry unknown = new TestRegistry();
        unknown.Add("sample", "one", delegate { });
        bool unknownRejected = RejectsManifest(
            unknown,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "sample", 1 }
            });

        bool negativeRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", -1 }
            });
        bool overfullRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 5 }
            });

        bool missingRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry extra = new TestRegistry();
        extra.Add("protocol", "registry manifest is exact", delegate { });
        extra.Add("encoding", "golden fixture bytes", delegate { });
        bool extraRejected = RejectsManifest(
            extra,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry slashPairs = new TestRegistry();
        bool slashPairsDistinct = true;
        try
        {
            slashPairs.Add("a/b", "c", delegate { });
            slashPairs.Add("a", "b/c", delegate { });
        }
        catch (InvalidOperationException)
        {
            slashPairsDistinct = false;
        }

        Check.True(renameRejected, "same-count rename was accepted");
        Check.True(swapRejected, "balanced cohort swap was accepted");
        Check.True(reorderRejected, "registration reorder was accepted");
        Check.True(unknownRejected, "unknown manifest cohort was accepted");
        Check.True(negativeRejected, "negative manifest count was accepted");
        Check.True(overfullRejected, "overfull manifest count was accepted");
        Check.True(missingRejected, "missing registration was accepted");
        Check.True(extraRejected, "extra registration was accepted");
        Check.True(slashPairsDistinct, "structural identities were aliased");
    }

    private static bool RejectsManifest(
        TestRegistry registry,
        IDictionary<string, int> expected)
    {
        try
        {
            registry.VerifyManifest(expected);
            return false;
        }
        catch (InvalidOperationException)
        {
            return true;
        }
    }
}
