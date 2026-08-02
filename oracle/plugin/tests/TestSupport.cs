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
    private sealed class TestCase
    {
        internal string Cohort;
        internal string Name;
        internal Action Test;
    }

    private readonly List<TestCase> tests = new List<TestCase>();
    private readonly HashSet<string> identities =
        new HashSet<string>(StringComparer.Ordinal);

    internal void Add(string cohort, string name, Action test)
    {
        if (String.IsNullOrEmpty(cohort))
            throw new ArgumentException("cohort is required", "cohort");
        if (String.IsNullOrEmpty(name))
            throw new ArgumentException("name is required", "name");
        if (test == null)
            throw new ArgumentNullException("test");
        string identity = cohort + "/" + name;
        if (!identities.Add(identity))
            throw new InvalidOperationException("duplicate test: " + identity);
        tests.Add(new TestCase { Cohort = cohort, Name = name, Test = test });
    }

    internal void VerifyManifest(IDictionary<string, int> expected)
    {
        if (expected == null)
            throw new ArgumentNullException("expected");
        Dictionary<string, int> actual =
            new Dictionary<string, int>(StringComparer.Ordinal);
        for (int index = 0; index < tests.Count; index++)
        {
            int count;
            actual.TryGetValue(tests[index].Cohort, out count);
            actual[tests[index].Cohort] = count + 1;
        }
        foreach (KeyValuePair<string, int> pair in expected)
        {
            int count;
            if (!actual.TryGetValue(pair.Key, out count) || count != pair.Value)
            {
                throw new InvalidOperationException(
                    "test manifest mismatch for " + pair.Key + ": expected "
                    + pair.Value.ToString() + ", actual " + count.ToString());
            }
        }
        foreach (KeyValuePair<string, int> pair in actual)
        {
            if (!expected.ContainsKey(pair.Key))
                throw new InvalidOperationException(
                    "unexpected test cohort: " + pair.Key);
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
                    test.Cohort + "/" + test.Name + ": " + error.ToString());
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
