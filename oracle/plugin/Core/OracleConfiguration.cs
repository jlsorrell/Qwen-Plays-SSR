using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

internal interface IConfigurationBytes
{
    byte[] ReadAllBytes(string configPath);
}

internal interface IConfigurationPathResolver
{
    string ResolveExistingDirectory(string requested);
    bool Contains(string parent, string candidate);
}

internal sealed class OracleConfigurationException : Exception
{
    internal OracleConfigurationException(string code, Exception inner)
        : base(code, inner)
    {
        if (code != "invalid_mode" && code != "invalid_configuration"
            && code != "invalid_path")
            throw new ArgumentException("invalid configuration code", "code");
        Code = code;
    }
    internal string Code { get; private set; }
}

internal sealed class PassiveConfiguration
{
    internal PassiveConfiguration(string outputDirectory, string runName,
        string tracePath, string saveDirectory)
    {
        OutputDirectory = outputDirectory;
        RunName = runName;
        TracePath = tracePath;
        SaveDirectory = saveDirectory;
        ExpectedInputCount = OracleProtocol.ExpectedInputCount;
        MaxSettleFrames = OracleProtocol.MaxSettleFrames;
        MaxSettleSeconds = OracleProtocol.MaxSettleSeconds;
    }
    internal string OutputDirectory { get; private set; }
    internal string RunName { get; private set; }
    internal string TracePath { get; private set; }
    internal string SaveDirectory { get; private set; }
    internal int ExpectedInputCount { get; private set; }
    internal int MaxSettleFrames { get; private set; }
    internal double MaxSettleSeconds { get; private set; }
}

internal sealed class OracleConfiguration
{
    private static readonly UTF8Encoding StrictUtf8 = new UTF8Encoding(false, true);
    private OracleConfiguration(OracleMode mode, PassiveConfiguration passive)
    { Mode = mode; Passive = passive; }
    internal OracleMode Mode { get; private set; }
    internal PassiveConfiguration Passive { get; private set; }

    internal static OracleConfiguration Load(string configPath,
        IConfigurationBytes source, IConfigurationPathResolver paths,
        out byte[] originalBytes)
    {
        if (source == null) throw new ArgumentNullException("source");
        byte[] bytes;
        try { bytes = source.ReadAllBytes(configPath); }
        catch (Exception error) { throw Failure("invalid_configuration", error); }
        if (bytes == null) throw Failure("invalid_configuration",
            new IOException("configuration source returned null"));
        originalBytes = (byte[])bytes.Clone();
        return Parse(bytes, paths);
    }

    internal static OracleConfiguration Load(string configPath, out byte[] originalBytes)
    { return Load(configPath, new FileConfigurationBytes(), PhysicalConfigurationPathResolver.Instance, out originalBytes); }

    internal static OracleConfiguration Parse(byte[] bytes)
    { return Parse(bytes, PhysicalConfigurationPathResolver.Instance); }

    internal static OracleConfiguration Parse(byte[] bytes, IConfigurationPathResolver paths)
    {
        Dictionary<string, string> values = ParseEntries(bytes);
        string mode = values["Mode"];
        if (mode == "off")
        {
            RequireOnly(values, new string[] { "Mode", "OutputDirectory", "RunName", "SaveDirectory", "InputPath", "MaxSettleFrames", "MaxSettleSeconds", "ExpectedInitialSha256" });
            return new OracleConfiguration(OracleMode.Off, null);
        }
        if (mode != "passive") throw Failure("invalid_mode", new FormatException("unsupported Mode"));
        if (paths == null) throw new ArgumentNullException("paths");
        RequireOnly(values, new string[] { "Mode", "OutputDirectory", "RunName", "SaveDirectory", "ExpectedPassiveInputs", "MaxSettleFrames", "MaxSettleSeconds" });
        RequireExactKeys(values, new string[] { "Mode", "OutputDirectory", "RunName", "SaveDirectory", "ExpectedPassiveInputs", "MaxSettleFrames", "MaxSettleSeconds" });
        if (Require(values, "ExpectedPassiveInputs") != "3" || Require(values, "MaxSettleFrames") != "600" || Require(values, "MaxSettleSeconds") != "30")
            throw Failure("invalid_configuration", new FormatException("passive numeric values are not canonical"));
        string runName = Require(values, "RunName");
        RequireSafeRunName(runName);
        try
        {
            string output = paths.ResolveExistingDirectory(Require(values, "OutputDirectory"));
            string save = paths.ResolveExistingDirectory(Require(values, "SaveDirectory"));
            if (paths.Contains(output, save) || paths.Contains(save, output))
                throw new IOException("active directories overlap");
            string trace = Path.Combine(output, runName + ".ndjson");
            return new OracleConfiguration(OracleMode.Passive, new PassiveConfiguration(output, runName, trace, save));
        }
        catch (OracleConfigurationException) { throw; }
        catch (Exception error) { throw Failure("invalid_path", error); }
    }

    private static Dictionary<string, string> ParseEntries(byte[] bytes)
    {
        try
        {
            if (bytes == null || bytes.Length == 0) throw new FormatException("configuration is empty");
            if (bytes.Length >= 3 && bytes[0] == 0xef && bytes[1] == 0xbb && bytes[2] == 0xbf) throw new FormatException("UTF-8 BOM is forbidden");
            string text = StrictUtf8.GetString(bytes);
            if (text.IndexOf('\0') >= 0) throw new FormatException("NUL is forbidden");
            for (int index = 0; index < text.Length; index++)
                if (text[index] == '\r' && (index + 1 >= text.Length || text[index + 1] != '\n')) throw new FormatException("bare CR is forbidden");
            text = text.Replace("\r\n", "\n");
            Dictionary<string, string> values = new Dictionary<string, string>(StringComparer.Ordinal);
            bool sawSection = false;
            string[] lines = text.Split(new char[] { '\n' });
            for (int index = 0; index < lines.Length; index++)
            {
                string line = TrimAscii(lines[index]);
                if (line.Length == 0 || line[0] == '#' || line[0] == ';') continue;
                if (line[0] == '[')
                {
                    if (line != "[Oracle]" || sawSection) throw new FormatException("invalid section");
                    sawSection = true; continue;
                }
                if (!sawSection) throw new FormatException("entry precedes Oracle section");
                int separator = line.IndexOf('=');
                if (separator <= 0 || separator != line.LastIndexOf('=')) throw new FormatException("invalid entry");
                string key = TrimAscii(line.Substring(0, separator));
                string value = TrimAscii(line.Substring(separator + 1));
                if (key.Length == 0 || value.IndexOf('#') >= 0 || value.IndexOf(';') >= 0 || values.ContainsKey(key)) throw new FormatException("invalid or duplicate entry");
                values.Add(key, value);
            }
            if (!sawSection || !values.ContainsKey("Mode")) throw new FormatException("Oracle Mode is required");
            return values;
        }
        catch (OracleConfigurationException) { throw; }
        catch (Exception error) { throw Failure("invalid_configuration", error); }
    }
    private static string TrimAscii(string value)
    { int first = 0; int last = value.Length; while (first < last && (value[first] == ' ' || value[first] == '\t')) first++; while (last > first && (value[last - 1] == ' ' || value[last - 1] == '\t')) last--; return value.Substring(first, last - first); }
    private static string Require(IDictionary<string, string> values, string key)
    { string value; if (!values.TryGetValue(key, out value) || value.Length == 0) throw Failure("invalid_configuration", new FormatException(key + " is required")); return value; }
    private static void RequireOnly(IDictionary<string, string> values, string[] allowed)
    { foreach (string key in values.Keys) { bool found = false; for (int index = 0; index < allowed.Length; index++) found |= key == allowed[index]; if (!found) throw Failure("invalid_configuration", new FormatException("unknown key: " + key)); } }
    private static void RequireExactKeys(IDictionary<string, string> values, string[] required)
    { for (int index = 0; index < required.Length; index++) if (!values.ContainsKey(required[index])) throw Failure("invalid_configuration", new FormatException("missing key: " + required[index])); }
    private static void RequireSafeRunName(string value)
    { if (value == "." || value == ".." || value.IndexOf('/') >= 0 || value.IndexOf('\\') >= 0 || value.IndexOf('\0') >= 0 || Path.GetFileName(value) != value || value.EndsWith(".ndjson", StringComparison.Ordinal)) throw Failure("invalid_configuration", new FormatException("unsafe RunName")); }
    private static OracleConfigurationException Failure(string code, Exception error)
    { return new OracleConfigurationException(code, error); }
}

internal sealed class FileConfigurationBytes : IConfigurationBytes
{
    public byte[] ReadAllBytes(string configPath) { return File.ReadAllBytes(configPath); }
}
