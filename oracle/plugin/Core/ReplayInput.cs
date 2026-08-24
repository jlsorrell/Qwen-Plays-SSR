using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

internal interface IReplayInputBytes
{
    byte[] ReadAllBytes(string inputPath);
}

internal sealed class ReplayInput
{
    private static readonly UTF8Encoding StrictUtf8 =
        new UTF8Encoding(false, true);
    private readonly byte[] bytes;
    private readonly OracleInput[] tokens;

    private ReplayInput(byte[] exactBytes, OracleInput[] parsedTokens,
        string sha256)
    {
        bytes = exactBytes;
        tokens = parsedTokens;
        Sha256 = sha256;
    }

    internal int Count { get { return tokens.Length; } }
    internal string Sha256 { get; private set; }
    internal byte[] Bytes { get { return (byte[])bytes.Clone(); } }
    internal OracleInput this[int index] { get { return tokens[index]; } }
    internal OracleInput[] Tokens { get { return (OracleInput[])tokens.Clone(); } }

    internal static ReplayInput Load(string inputPath, IReplayInputBytes source)
    {
        if (String.IsNullOrEmpty(inputPath))
            throw Failure(new ArgumentException("inputPath is required"));
        if (source == null) throw new ArgumentNullException("source");
        byte[] value;
        try { value = source.ReadAllBytes(inputPath); }
        catch (Exception error) { throw Failure(error); }
        if (value == null)
            throw Failure(new IOException("input source returned null"));
        return Parse(value);
    }

    internal static ReplayInput Parse(byte[] sourceBytes)
    {
        try
        {
            if (sourceBytes == null)
                throw new ArgumentNullException("sourceBytes");
            byte[] exact = (byte[])sourceBytes.Clone();
            if (exact.Length >= 3 && exact[0] == 0xef
                && exact[1] == 0xbb && exact[2] == 0xbf)
                throw new FormatException("UTF-8 BOM is forbidden");
            string text = StrictUtf8.GetString(exact);
            if (text.IndexOf('\0') >= 0)
                throw new FormatException("NUL is forbidden");
            List<OracleInput> parsed = new List<OracleInput>();
            string[] lines = text.Split(new char[] { '\n' });
            for (int index = 0; index < lines.Length; index++)
            {
                string token = TrimAscii(lines[index]);
                if (token.Length == 0) continue;
                OracleInput input;
                if (!TryParseToken(token, out input))
                    throw new FormatException("unknown replay token");
                parsed.Add(input);
            }
            if (parsed.Count == 0)
                throw new FormatException("replay token stream is empty");
            return new ReplayInput(exact, parsed.ToArray(), Hash(exact));
        }
        catch (OracleConfigurationException) { throw; }
        catch (Exception error) { throw Failure(error); }
    }

    private static bool TryParseToken(string value, out OracleInput input)
    {
        if (value == "North") { input = OracleInput.North; return true; }
        if (value == "South") { input = OracleInput.South; return true; }
        if (value == "West") { input = OracleInput.West; return true; }
        if (value == "East") { input = OracleInput.East; return true; }
        if (value == "Undo") { input = OracleInput.Undo; return true; }
        input = OracleInput.North;
        return false;
    }

    private static string TrimAscii(string value)
    {
        int first = 0;
        int last = value.Length;
        while (first < last && IsAsciiWhitespace(value[first])) first++;
        while (last > first && IsAsciiWhitespace(value[last - 1])) last--;
        return value.Substring(first, last - first);
    }

    private static bool IsAsciiWhitespace(char value)
    {
        return value == ' ' || value == '\t' || value == '\r'
            || value == '\f' || value == '\v';
    }

    private static string Hash(byte[] value)
    {
        byte[] digest;
        using (SHA256 hash = SHA256.Create()) digest = hash.ComputeHash(value);
        StringBuilder text = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
            text.Append(digest[index].ToString("x2", CultureInfo.InvariantCulture));
        return text.ToString();
    }

    private static OracleConfigurationException Failure(Exception error)
    {
        return new OracleConfigurationException("invalid_configuration", error);
    }
}

internal sealed class FileReplayInputBytes : IReplayInputBytes
{
    public byte[] ReadAllBytes(string inputPath)
    {
        return File.ReadAllBytes(inputPath);
    }
}
