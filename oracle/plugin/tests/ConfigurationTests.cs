using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

internal static class ConfigurationTests
{
    internal static void Register(TestRegistry tests, HarnessOptions options)
    {
        tests.Add("config", "off grammar is exact and read only",
            delegate { OffGrammarIsExactAndReadOnly(options.ModeOffFixturePath); });
        tests.Add("config", "off malformed inputs are rejected",
            OffMalformedInputsAreRejected);
        tests.Add("config", "unsupported modes are typed",
            UnsupportedModesAreTyped);
        tests.Add("config", "passive values are canonical",
            PassiveValuesAreCanonical);
        tests.Add("config", "passive failures are typed",
            PassiveFailuresAreTyped);
        tests.Add("config", "configuration reads are typed",
            ConfigurationReadsAreTyped);
    }

    private static void OffGrammarIsExactAndReadOnly(string fixturePath)
    {
        string[] texts = new string[] {
            "[Oracle]\nMode = off\n",
            "[Oracle]\r\nMode = off\r\nOutputDirectory = /legacy\r\nRunName = old\r\n"
        };
        for (int index = 0; index < texts.Length; index++)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(texts[index]);
            StaticConfigurationBytes source = new StaticConfigurationBytes(bytes);
            FakeConfigurationPathResolver resolver = new FakeConfigurationPathResolver();
            byte[] original;
            OracleConfiguration configuration = OracleConfiguration.Load(
                "/config.ini", source, resolver, out original);
            Check.Equal(OracleMode.Off, configuration.Mode, "off Mode");
            Check.Equal<PassiveConfiguration>(null, configuration.Passive, "off Passive");
            Check.Equal(0, resolver.Calls.Count, "off resolver calls");
            Check.Bytes(bytes, original, "off retained bytes");
            Check.False(Object.ReferenceEquals(bytes, original), "off retained clone");
            Check.Bytes(bytes, source.bytes, "off source remains unchanged");
        }
        if (fixturePath != null)
        {
            byte[] fixture = File.ReadAllBytes(fixturePath);
            byte[] before = (byte[])fixture.Clone();
            byte[] original;
            OracleConfiguration.Load(fixturePath, new StaticConfigurationBytes(fixture),
                new FakeConfigurationPathResolver(), out original);
            Check.Equal("cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d",
                Hex(SHA256.Create().ComputeHash(before)), "fixture before hash");
            Check.Equal(Hex(SHA256.Create().ComputeHash(before)),
                Hex(SHA256.Create().ComputeHash(fixture)), "fixture parser makes no write");
        }
    }

    private static void OffMalformedInputsAreRejected()
    {
        string[] cases = new string[] {
            "Mode=off\n", "[Oracle]\n", "[Oracle]\nMode=off\nMode=off\n",
            "[oracle]\nMode=off\n", "[Oracle]\nmode=off\n",
            "[Oracle]\nMode=off\n[Extra]\n", "[Oracle]\nMode=off\nUnknown=x\n",
            "[Oracle]\nMode=off\nRunName=x\nRunName=y\n",
            "[Oracle]\nMode=off\nrunName=x\n", "[Oracle]\nMode=off\nExpectedPassiveInputs=3\n",
            "[Oracle]\nMode=off\n[Oracle]\n",
            "[Oracle]\nMode off\n", "[Oracle]\nMode=off # no\n",
            "[Oracle]\nMode=off\0\n", "\uFEFF[Oracle]\nMode=off\n",
            "[Oracle]\rMode=off\r"
        };
        for (int index = 0; index < cases.Length; index++)
            AssertConfigCode("invalid_configuration", Encoding.UTF8.GetBytes(cases[index]), new FakeConfigurationPathResolver());
        AssertConfigCode("invalid_configuration", new byte[] { 0xff }, new FakeConfigurationPathResolver());
    }

    private static void UnsupportedModesAreTyped()
    {
        string[] values = new string[] { "", "Passive", "replay", "anything" };
        for (int index = 0; index < values.Length; index++)
            AssertConfigCode("invalid_mode", Bytes("[Oracle]\nMode=" + values[index] + "\n"), new FakeConfigurationPathResolver());
    }

    private static void PassiveValuesAreCanonical()
    {
        FakeConfigurationPathResolver resolver = new FakeConfigurationPathResolver();
        resolver.Resolved.Enqueue("/physical/output");
        resolver.Resolved.Enqueue("/physical/save");
        OracleConfiguration configuration = OracleConfiguration.Parse(Bytes(PassiveText(
            "/asked/output", "run-01", "/asked/save")), resolver);
        PassiveConfiguration passive = configuration.Passive;
        Check.Equal(OracleMode.Passive, configuration.Mode, "passive Mode");
        Check.Equal("/physical/output", passive.OutputDirectory, "canonical output");
        Check.Equal("run-01", passive.RunName, "run name");
        Check.Equal("/physical/output/run-01.ndjson", passive.TracePath, "trace path");
        Check.Equal("/physical/save", passive.SaveDirectory, "canonical save");
        Check.Equal(OracleProtocol.ExpectedInputCount, passive.ExpectedInputCount, "input count");
        Check.Equal(OracleProtocol.MaxSettleFrames, passive.MaxSettleFrames, "settle frames");
        Check.Equal((double)OracleProtocol.MaxSettleSeconds, passive.MaxSettleSeconds, "settle seconds");
        Check.Sequence(new string[] { "directory:/asked/output", "directory:/asked/save", "contains:/physical/output:/physical/save", "contains:/physical/save:/physical/output" }, resolver.Calls, "resolver order");
    }

    private static void PassiveFailuresAreTyped()
    {
        string passive = PassiveText("/out", "run", "/save");
        string[] keys = new string[] { "Mode", "OutputDirectory", "RunName", "SaveDirectory", "ExpectedPassiveInputs", "MaxSettleFrames", "MaxSettleSeconds" };
        string[] missingOrExtra = new string[keys.Length + 1];
        for (int index = 0; index < keys.Length; index++)
        {
            int lineStart = passive.IndexOf("\n" + keys[index] + "=") + 1;
            int lineEnd = passive.IndexOf('\n', lineStart) + 1;
            missingOrExtra[index] = passive.Remove(lineStart, lineEnd - lineStart);
        }
        missingOrExtra[keys.Length] = passive + "Extra=x\n";
        for (int index = 0; index < missingOrExtra.Length; index++)
            AssertConfigCode("invalid_configuration", Bytes(missingOrExtra[index]), new FakeConfigurationPathResolver());
        string[] noncanonical = new string[] {
            PassiveText("/out", "run", "/save").Replace("ExpectedPassiveInputs=3", "ExpectedPassiveInputs=03"),
            PassiveText("/out", "run", "/save").Replace("MaxSettleFrames=600", "MaxSettleFrames=599"),
            PassiveText("/out", "run", "/save").Replace("MaxSettleSeconds=30", "MaxSettleSeconds=30.0"),
            PassiveText("/out", "../run", "/save"), PassiveText("/out", "run.ndjson", "/save")
        };
        for (int index = 0; index < noncanonical.Length; index++)
            AssertConfigCode("invalid_configuration", Bytes(noncanonical[index]), new FakeConfigurationPathResolver());
        FakeConfigurationPathResolver overlap = Resolver("/out", "/save");
        overlap.ContainsResult = true;
        AssertConfigCode("invalid_path", Bytes(PassiveText("/out", "run", "/save")), overlap);
        FakeConfigurationPathResolver failed = new FakeConfigurationPathResolver();
        failed.Failure = new IOException("no path");
        AssertConfigCode("invalid_path", Bytes(PassiveText("/out", "run", "/save")), failed);
    }

    private static void ConfigurationReadsAreTyped()
    {
        AssertReadFailure(new StaticConfigurationBytes(null), null, "null read");
        AssertReadFailure(new ThrowingConfigurationBytes(new FileNotFoundException()), typeof(FileNotFoundException), "missing");
        AssertReadFailure(new ThrowingConfigurationBytes(new UnauthorizedAccessException()), typeof(UnauthorizedAccessException), "denied");
        AssertReadFailure(new ThrowingConfigurationBytes(new InvalidOperationException()), typeof(InvalidOperationException), "unexpected");
    }

    private static void AssertReadFailure(IConfigurationBytes source, Type inner, string label)
    {
        byte[] original;
        OracleConfigurationException error = Check.Throws<OracleConfigurationException>(
            delegate { OracleConfiguration.Load("/x", source, new FakeConfigurationPathResolver(), out original); }, label);
        Check.Equal("invalid_configuration", error.Code, label + " code");
        Check.True(error.InnerException != null, label + " inner");
        if (inner != null) Check.Equal(inner, error.InnerException.GetType(), label + " inner type");
        StaticConfigurationBytes staticSource = source as StaticConfigurationBytes;
        if (staticSource != null) Check.Equal(1, staticSource.ReadCount, label + " one read");
        ThrowingConfigurationBytes throwingSource = source as ThrowingConfigurationBytes;
        if (throwingSource != null) Check.Equal(1, throwingSource.ReadCount, label + " one read");
    }

    private static void AssertConfigCode(string code, byte[] bytes, IConfigurationPathResolver resolver)
    {
        OracleConfigurationException error = Check.Throws<OracleConfigurationException>(
            delegate { OracleConfiguration.Parse(bytes, resolver); }, "configuration failure");
        Check.Equal(code, error.Code, "configuration code");
        FakeConfigurationPathResolver fake = resolver as FakeConfigurationPathResolver;
        if (fake != null && code != "invalid_path") Check.Equal(0, fake.Calls.Count, "resolver uncalled");
    }

    private static FakeConfigurationPathResolver Resolver(string output, string save)
    {
        FakeConfigurationPathResolver resolver = new FakeConfigurationPathResolver();
        resolver.Resolved.Enqueue(output); resolver.Resolved.Enqueue(save); return resolver;
    }
    private static string PassiveText(string output, string run, string save)
    { return "[Oracle]\nMode=passive\nOutputDirectory=" + output + "\nRunName=" + run + "\nSaveDirectory=" + save + "\nExpectedPassiveInputs=3\nMaxSettleFrames=600\nMaxSettleSeconds=30\n"; }
    private static byte[] Bytes(string text) { return Encoding.UTF8.GetBytes(text); }
    private static string Hex(byte[] bytes) { StringBuilder result = new StringBuilder(); for (int i = 0; i < bytes.Length; i++) result.Append(bytes[i].ToString("x2")); return result.ToString(); }
}

internal sealed class StaticConfigurationBytes : IConfigurationBytes
{
    internal readonly byte[] bytes;
    internal int ReadCount;
    internal string LastPath;
    internal StaticConfigurationBytes(byte[] bytes) { this.bytes = bytes; }
    public byte[] ReadAllBytes(string configPath)
    { ReadCount++; LastPath = configPath; return bytes == null ? null : (byte[])bytes.Clone(); }
}

internal sealed class ThrowingConfigurationBytes : IConfigurationBytes
{
    private readonly Exception error; internal int ReadCount;
    internal ThrowingConfigurationBytes(Exception error) { this.error = error; }
    public byte[] ReadAllBytes(string configPath) { ReadCount++; throw error; }
}

internal sealed class FakeConfigurationPathResolver : IConfigurationPathResolver
{
    internal readonly Queue<string> Resolved = new Queue<string>();
    internal readonly List<string> Calls = new List<string>();
    internal bool ContainsResult; internal Exception Failure;
    public string ResolveExistingDirectory(string requested)
    { Calls.Add("directory:" + requested); if (Failure != null) throw Failure; return Resolved.Dequeue(); }
    public bool Contains(string parent, string candidate)
    { Calls.Add("contains:" + parent + ":" + candidate); return ContainsResult; }
}
