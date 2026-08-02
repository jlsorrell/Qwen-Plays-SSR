using System;
using System.Collections.Generic;
using System.IO;

internal sealed class HarnessOptions
{
    internal string Cohort { get; private set; }
    internal string AssemblyPath { get; private set; }
    internal string PluginPath { get; private set; }
    internal string ModeOffFixturePath { get; private set; }

    private HarnessOptions()
    {
    }

    internal static HarnessOptions Parse(string[] args)
    {
        if (args == null)
            throw new ArgumentNullException("args");
        HarnessOptions options = new HarnessOptions();
        for (int index = 0; index < args.Length; index++)
        {
            string name = args[index];
            if (name == "--cohort")
                options.Cohort = SetOnce(
                    options.Cohort, ReadValue(args, ref index), name);
            else if (name == "--assembly")
                options.AssemblyPath = SetOnce(
                    options.AssemblyPath,
                    RequireAbsolute(ReadValue(args, ref index), name),
                    name);
            else if (name == "--plugin")
                options.PluginPath = SetOnce(
                    options.PluginPath,
                    RequireAbsolute(ReadValue(args, ref index), name),
                    name);
            else if (name == "--mode-off-fixture")
                options.ModeOffFixturePath = SetOnce(
                    options.ModeOffFixturePath,
                    RequireAbsolute(ReadValue(args, ref index), name),
                    name);
            else
                throw new ArgumentException("unknown argument: " + name);
        }
        return options;
    }

    private static string ReadValue(string[] args, ref int index)
    {
        index++;
        if (index >= args.Length || String.IsNullOrEmpty(args[index]))
            throw new ArgumentException("missing argument value");
        return args[index];
    }

    private static string SetOnce(string prior, string value, string name)
    {
        if (prior != null)
            throw new ArgumentException("duplicate argument: " + name);
        return value;
    }

    private static string RequireAbsolute(string value, string name)
    {
        if (!Path.IsPathRooted(value))
            throw new ArgumentException("path must be absolute: " + name);
        return value;
    }
}

internal sealed class TestRegistry
{
    private sealed class TestIdentity
    {
        internal readonly string Cohort;
        internal readonly string Name;

        internal TestIdentity(string cohort, string name)
        {
            Cohort = cohort;
            Name = name;
        }

        internal bool Matches(string cohort, string name)
        {
            return String.Equals(Cohort, cohort, StringComparison.Ordinal)
                && String.Equals(Name, name, StringComparison.Ordinal);
        }
    }

    private sealed class TestCase
    {
        internal string Cohort;
        internal string Name;
        internal Action Test;
    }

    private static readonly TestIdentity[] ApprovedManifest =
        new TestIdentity[]
        {
            new TestIdentity("protocol", "registry manifest is exact"),
            new TestIdentity("protocol", "closed error tables"),
            new TestIdentity("protocol", "record constructor boundaries"),
            new TestIdentity("protocol", "capture value equality"),
            new TestIdentity("encoding", "golden fixture bytes"),
            new TestIdentity("encoding", "canonical string scalars"),
            new TestIdentity("encoding", "surrogates are rejected"),
            new TestIdentity("encoding", "capture signature is exact"),
            new TestIdentity("encoding", "record line limit includes LF"),
            new TestIdentity("sink", "factory arguments are exact"),
            new TestIdentity("sink", "null factory output is typed"),
            new TestIdentity("sink", "real collision is typed"),
            new TestIdentity("sink", "records use LF and flush"),
            new TestIdentity("sink", "bounds and write failures are terminal"),
            new TestIdentity("sink", "close ownership is single use"),
            new TestIdentity(
                "driver-boundary",
                "hook token is owner bound and single consume"),
            new TestIdentity(
                "driver-boundary",
                "update directive authorizes rebases and consumes once"),
            new TestIdentity("driver-initial", "prepare activate separation"),
            new TestIdentity(
                "driver-initial", "pre epoch neutral does not leak"),
            new TestIdentity("driver-initial", "matching pair writes initial"),
            new TestIdentity("driver-initial", "not inspected breaks pair"),
            new TestIdentity("driver-initial", "nonquiescent breaks pair"),
            new TestIdentity("driver-initial", "cardinal clears candidate"),
            new TestIdentity(
                "driver-initial", "replacement rebases same callback"),
            new TestIdentity(
                "driver-initial", "exact deadline and pre overrun"),
            new TestIdentity("driver-input", "all cardinals correlate"),
            new TestIdentity(
                "driver-input", "filtered and zero poll open no attempt"),
            new TestIdentity(
                "driver-input", "duplicate mismatch and unknown fault"),
            new TestIdentity(
                "driver-input", "unscoped policy follows phase"),
            new TestIdentity(
                "driver-input", "accepted and refused direction outcomes"),
            new TestIdentity(
                "driver-input", "Undo acceptance and restore rules"),
            new TestIdentity("driver-input", "restart depth and null fields"),
            new TestIdentity(
                "driver-input", "state replacement and ClearThrew"),
            new TestIdentity(
                "driver-terminal", "three steps End Close Complete order"),
            new TestIdentity(
                "driver-terminal", "error field policy is exact"),
            new TestIdentity(
                "driver-terminal", "sink failure uses trace io marker"),
            new TestIdentity(
                "driver-terminal", "completion reporter cannot rewrite trace"),
            new TestIdentity("driver-terminal", "first fault wins race"),
            new TestIdentity(
                "driver-terminal", "Dispose and late callbacks are final"),
            new TestIdentity("config", "off grammar is exact and read only"),
            new TestIdentity(
                "config", "off malformed inputs are rejected"),
            new TestIdentity("config", "unsupported modes are typed"),
            new TestIdentity("config", "passive values are canonical"),
            new TestIdentity("config", "passive failures are typed"),
            new TestIdentity("config", "configuration reads are typed"),
            new TestIdentity("path", "containment uses component boundary"),
            new TestIdentity("path", "existing paths resolve canonically"),
            new TestIdentity("path", "missing suffix is preserved"),
            new TestIdentity("path", "lexical paths are strict"),
            new TestIdentity(
                "path", "symlink and nondirectory are rejected"),
            new TestIdentity("path", "two scan drift is rejected"),
            new TestIdentity(
                "observation", "all thirteen gates are required"),
            new TestIdentity(
                "observation", "capture maps all twelve fields"),
            new TestIdentity(
                "observation", "three nullable strings normalize"),
            new TestIdentity("observation", "required values reject null"),
            new TestIdentity(
                "observation", "numeric ranges reject negative"),
            new TestIdentity(
                "boundary", "postfix contains observer failures"),
            new TestIdentity(
                "boundary", "game exception claims before cleanup"),
            new TestIdentity(
                "boundary", "successful postfix makes finalizer cleanup inert"),
            new TestIdentity(
                "boundary", "cleanup failure is contained and reported"),
            new TestIdentity(
                "boundary", "update finalizer preserves original reference"),
            new TestIdentity(
                "startup", "off invokes only legacy validation then boot"),
            new TestIdentity(
                "startup", "off preserves legacy failure identity"),
            new TestIdentity(
                "startup",
                "run flush precedes patches and activation precedes boot"),
            new TestIdentity(
                "startup", "typed pre-driver failures stay marker only"),
            new TestIdentity(
                "startup", "prepare failure is not reported twice"),
            new TestIdentity(
                "startup", "owned startup failures use driver arbitration"),
            new TestIdentity(
                "startup", "teardown is ordered and idempotent"),
            new TestIdentity("reporter", "ready markers are exact"),
            new TestIdentity("reporter", "completion marker is exact"),
            new TestIdentity("reporter", "failure markers are closed"),
            new TestIdentity("reporter", "diagnostic is nonterminal"),
            new TestIdentity("assembly", "pinned Assembly-CSharp hash"),
            new TestIdentity("assembly", "exact ten observed methods"),
            new TestIdentity("assembly", "exact required game fields"),
            new TestIdentity(
                "assembly", "metadata matcher rejects near misses"),
            new TestIdentity(
                "plugin", "game adapter call surface is passive"),
            new TestIdentity(
                "plugin", "controller crosses authorized update boundary"),
            new TestIdentity(
                "plugin", "eight Harmony patch contracts are exact"),
            new TestIdentity(
                "plugin", "PE CLR and direct references are pinned"),
            new TestIdentity("plugin", "BepInPlugin identity is exact"),
            new TestIdentity(
                "plugin", "typed modes and owner teardown are closed")
        };

    private readonly List<TestCase> tests = new List<TestCase>();

    internal void Add(string cohort, string name, Action test)
    {
        if (String.IsNullOrEmpty(cohort))
            throw new ArgumentException("cohort is required", "cohort");
        if (String.IsNullOrEmpty(name))
            throw new ArgumentException("name is required", "name");
        if (test == null)
            throw new ArgumentNullException("test");
        for (int index = 0; index < tests.Count; index++)
        {
            if (String.Equals(
                    tests[index].Cohort, cohort, StringComparison.Ordinal)
                && String.Equals(
                    tests[index].Name, name, StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "duplicate test cohort '" + cohort + "', name '" + name + "'");
            }
        }
        tests.Add(new TestCase { Cohort = cohort, Name = name, Test = test });
    }

    internal void VerifyManifest(IDictionary<string, int> expected)
    {
        if (expected == null)
            throw new ArgumentNullException("expected");
        Dictionary<string, int> approvedCounts =
            new Dictionary<string, int>(StringComparer.Ordinal);
        for (int index = 0; index < ApprovedManifest.Length; index++)
        {
            int count;
            approvedCounts.TryGetValue(ApprovedManifest[index].Cohort, out count);
            approvedCounts[ApprovedManifest[index].Cohort] = count + 1;
        }

        Dictionary<string, int> requestedCounts =
            new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (KeyValuePair<string, int> pair in expected)
        {
            int approvedCount;
            if (pair.Key == null
                || !approvedCounts.TryGetValue(pair.Key, out approvedCount))
            {
                throw new InvalidOperationException(
                    "unknown test cohort: " + pair.Key);
            }
            if (pair.Value < 0)
                throw new InvalidOperationException(
                    "negative test count for " + pair.Key);
            if (pair.Value > approvedCount)
                throw new InvalidOperationException(
                    "test count exceeds approved manifest for " + pair.Key);
            if (requestedCounts.ContainsKey(pair.Key))
                throw new InvalidOperationException(
                    "duplicate manifest cohort: " + pair.Key);
            requestedCounts.Add(pair.Key, pair.Value);
        }

        List<TestIdentity> requested = new List<TestIdentity>();
        Dictionary<string, int> visitedCounts =
            new Dictionary<string, int>(StringComparer.Ordinal);
        for (int index = 0; index < ApprovedManifest.Length; index++)
        {
            TestIdentity identity = ApprovedManifest[index];
            int visited;
            visitedCounts.TryGetValue(identity.Cohort, out visited);
            visitedCounts[identity.Cohort] = visited + 1;
            int requestedCount;
            if (requestedCounts.TryGetValue(identity.Cohort, out requestedCount)
                && visited < requestedCount)
            {
                requested.Add(identity);
            }
        }

        if (tests.Count != requested.Count)
        {
            throw new InvalidOperationException(
                "test manifest size mismatch: expected "
                + requested.Count.ToString() + ", actual "
                + tests.Count.ToString());
        }
        for (int index = 0; index < requested.Count; index++)
        {
            if (!requested[index].Matches(
                    tests[index].Cohort, tests[index].Name))
            {
                throw new InvalidOperationException(
                    "test manifest mismatch at index " + index.ToString()
                    + ": expected cohort '" + requested[index].Cohort
                    + "', name '" + requested[index].Name
                    + "'; actual cohort '" + tests[index].Cohort
                    + "', name '" + tests[index].Name + "'");
            }
        }
    }

    internal int Run(string selectedCohort)
    {
        int selected = 0;
        for (int index = 0; index < tests.Count; index++)
        {
            TestCase test = tests[index];
            if (selectedCohort != null
                && selectedCohort != "all"
                && selectedCohort != test.Cohort)
            {
                continue;
            }
            selected++;
            try
            {
                test.Test();
            }
            catch (Exception error)
            {
                Console.Error.WriteLine(
                    "cohort '" + test.Cohort + "', test '" + test.Name
                    + "': " + error.ToString());
                return 1;
            }
        }
        if (selected == 0)
        {
            Console.Error.WriteLine("no tests selected");
            return 1;
        }
        return 0;
    }
}

internal static class Check
{
    internal static void True(bool value, string message)
    {
        if (!value)
            throw new InvalidOperationException(message);
    }

    internal static void False(bool value, string message)
    {
        True(!value, message);
    }

    internal static void Equal<T>(T expected, T actual, string message)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new InvalidOperationException(message);
    }

    internal static void Same(object expected, object actual, string message)
    {
        if (!Object.ReferenceEquals(expected, actual))
            throw new InvalidOperationException(message);
    }

    internal static void Bytes(byte[] expected, byte[] actual, string message)
    {
        Sequence<byte>(expected, actual, message);
    }

    internal static void Sequence<T>(
        IList<T> expected,
        IList<T> actual,
        string message)
    {
        if (expected == null || actual == null || expected.Count != actual.Count)
            throw new InvalidOperationException(message);
        for (int index = 0; index < expected.Count; index++)
        {
            if (!EqualityComparer<T>.Default.Equals(
                expected[index], actual[index]))
            {
                throw new InvalidOperationException(
                    message + " at index " + index.ToString());
            }
        }
    }

    internal static TException Throws<TException>(Action action, string message)
        where TException : Exception
    {
        if (action == null)
            throw new ArgumentNullException("action");
        try
        {
            action();
        }
        catch (TException error)
        {
            return error;
        }
        catch (Exception error)
        {
            throw new InvalidOperationException(
                message + ": wrong exception " + error.GetType().FullName,
                error);
        }
        throw new InvalidOperationException(message + ": no exception");
    }
}
