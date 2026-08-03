using System;
using System.Globalization;
using System.IO;
using System.Text;

internal static class ProtocolSamples
{
    internal const string RunId = "0123456789abcdef0123456789abcdef";
    internal static readonly CaptureRecord InitialCapture = Capture("initial");
    internal static readonly CaptureRecord MovedCapture = Capture("moved");
    internal static readonly RunRecord Run = new RunRecord(
        RunId, OracleProtocol.ExpectedAssemblySha256,
        new DateTime(2026, 7, 31, 19, 9, 50, DateTimeKind.Utc).AddTicks(3199100));
    internal static readonly InitialRecord Initial =
        new InitialRecord(RunId, InitialCapture);
    internal static readonly StepRecord Step0 =
        new StepRecord(RunId, 0, OracleInput.West, true, true, 2, false, MovedCapture);
    internal static readonly StepRecord Step1 =
        new StepRecord(RunId, 1, OracleInput.North, false, false, 2, false, MovedCapture);
    internal static readonly StepRecord Step2 =
        new StepRecord(RunId, 2, OracleInput.Undo, true, false, 2, false, InitialCapture);
    internal static readonly EndRecord End = new EndRecord(
        RunId, 3, new DateTime(2026, 7, 31, 19, 11, 0, DateTimeKind.Utc));
    internal static readonly ErrorRecord Error = new ErrorRecord(
        RunId, 1, OracleInput.North, "settle_timeout", 600, MovedCapture);

    internal static CaptureRecord Capture(string rawSave)
    {
        return new CaptureRecord(
            rawSave, "17", "", false, false, false, false, "", "", 0, 0, 0);
    }
}

internal static class EncodingTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("encoding", "golden fixture bytes", GoldenFixtures);
        tests.Add("encoding", "canonical string scalars", CanonicalStrings);
        tests.Add("encoding", "surrogates are rejected", RejectsSurrogates);
    }

    private static byte[][] ReadFixtureLines(string path)
    {
        byte[] payload = File.ReadAllBytes(path);
        Check.True(payload.Length > 0, "fixture nonempty");
        Check.Equal((byte)'\n', payload[payload.Length - 1], "fixture final LF");
        string[] pieces = new UTF8Encoding(false, true).GetString(payload)
            .Split(new char[] { '\n' });
        byte[][] lines = new byte[pieces.Length - 1][];
        for (int index = 0; index < lines.Length; index++)
            lines[index] = new UTF8Encoding(false, true).GetBytes(pieces[index]);
        return lines;
    }

    private static void GoldenFixtures()
    {
        byte[][] success = ReadFixtureLines(Path.Combine(
            "tests", "fixtures", "oracle_trace", "passive-success.ndjson"));
        byte[][] error = ReadFixtureLines(Path.Combine(
            "tests", "fixtures", "oracle_trace", "passive-error.ndjson"));
        byte[][] actual = new byte[][]
        {
            CanonicalJson.EncodeRun(ProtocolSamples.Run),
            CanonicalJson.EncodeInitial(ProtocolSamples.Initial),
            CanonicalJson.EncodeStep(ProtocolSamples.Step0),
            CanonicalJson.EncodeStep(ProtocolSamples.Step1),
            CanonicalJson.EncodeStep(ProtocolSamples.Step2),
            CanonicalJson.EncodeEnd(ProtocolSamples.End)
        };
        Check.Equal(6, success.Length, "success fixture lines");
        for (int index = 0; index < actual.Length; index++)
            Check.Bytes(success[index], actual[index], "success line " + index);
        Check.Equal(4, error.Length, "error fixture lines");
        Check.Bytes(error[0], actual[0], "error run line");
        Check.Bytes(error[1], actual[1], "error initial line");
        Check.Bytes(error[2], actual[2], "error step line");
        Check.Bytes(error[3], CanonicalJson.EncodeError(ProtocolSamples.Error),
            "error terminal line");

        Check.Bytes(
            new UTF8Encoding(false, true).GetBytes(
                "{\"kind\":\"error\",\"schema_version\":1,\"run_id\":"
                + "\"0123456789abcdef0123456789abcdef\",\"input_index\":null,"
                + "\"input\":null,\"code\":\"capture_failed\",\"message\":"
                + "\"game-state capture failed\",\"settle_frames\":0,"
                + "\"last_capture\":null}"),
            CanonicalJson.EncodeError(new ErrorRecord(
                ProtocolSamples.RunId, null, null, "capture_failed", 0, null)),
            "fully-null error bytes");
        Check.Bytes(
            new UTF8Encoding(false, true).GetBytes(
                "{\"kind\":\"error\",\"schema_version\":1,\"run_id\":"
                + "\"0123456789abcdef0123456789abcdef\",\"input_index\":2,"
                + "\"input\":null,\"code\":\"unexpected_input\",\"message\":"
                + "\"native input was outside the passive vocabulary\","
                + "\"settle_frames\":0,\"last_capture\":null}"),
            CanonicalJson.EncodeError(new ErrorRecord(
                ProtocolSamples.RunId, 2, null, "unexpected_input", 0, null)),
            "indexed null-input error bytes");

        byte[] south = CanonicalJson.EncodeStep(new StepRecord(
            ProtocolSamples.RunId, 0, OracleInput.South,
            true, true, 2, false, ProtocolSamples.MovedCapture));
        Check.True(ContainsBytes(south,
            new UTF8Encoding(false, true).GetBytes("\"input\":\"South\"")),
            "South exact wire spelling");
        byte[] east = CanonicalJson.EncodeError(new ErrorRecord(
            ProtocolSamples.RunId, 2, OracleInput.East,
            "settle_timeout", 2, ProtocolSamples.MovedCapture));
        Check.True(ContainsBytes(east,
            new UTF8Encoding(false, true).GetBytes("\"input\":\"East\"")),
            "East exact wire spelling");
    }

    private static void CanonicalStrings()
    {
        string[,] cases = new string[,]
        {
            { "plain", "\"raw_save\":\"plain\"" },
            { "\"", "\"raw_save\":\"\\\"\"" },
            { "\\", "\"raw_save\":\"\\\\\"" },
            { "\b\f\n\r\t", "\"raw_save\":\"\\b\\f\\n\\r\\t\"" },
            { "\u0000\u0001\u001f", "\"raw_save\":\"\\u0000\\u0001\\u001f\"" },
            { "é/雪", "\"raw_save\":\"é/雪\"" },
            { "\ud83d\ude00", "\"raw_save\":\"😀\"" }
        };
        for (int index = 0; index < cases.GetLength(0); index++)
        {
            string encoded = new UTF8Encoding(false, true).GetString(
                CanonicalJson.EncodeInitial(new InitialRecord(
                    ProtocolSamples.RunId, ProtocolSamples.Capture(cases[index, 0]))));
            Check.True(encoded.IndexOf(cases[index, 1], StringComparison.Ordinal) >= 0,
                "canonical string " + index);
        }
        byte[] supplementary = CanonicalJson.EncodeInitial(new InitialRecord(
            ProtocolSamples.RunId, ProtocolSamples.Capture("\ud83d\ude00")));
        Check.True(ContainsBytes(supplementary,
            new byte[] { 0xf0, 0x9f, 0x98, 0x80 }),
            "U+1F600 exact UTF-8 bytes");
        CultureInfo prior = CultureInfo.CurrentCulture;
        try
        {
            CultureInfo.CurrentCulture = new CultureInfo("fr-FR");
            Check.Bytes(ReadFixtureLines(Path.Combine(
                "tests", "fixtures", "oracle_trace", "passive-success.ndjson"))[0],
                CanonicalJson.EncodeRun(ProtocolSamples.Run), "culture-invariant run");
        }
        finally
        {
            CultureInfo.CurrentCulture = prior;
        }
    }

    private static bool ContainsBytes(byte[] haystack, byte[] needle)
    {
        for (int start = 0; start <= haystack.Length - needle.Length; start++)
        {
            int offset = 0;
            while (offset < needle.Length
                && haystack[start + offset] == needle[offset])
            {
                offset++;
            }
            if (offset == needle.Length)
                return true;
        }
        return false;
    }

    private static void RejectsSurrogates()
    {
        string[] invalid = new string[] { "\ud800", "\udfff", "x\ud800y" };
        for (int index = 0; index < invalid.Length; index++)
        {
            CaptureRecord capture = ProtocolSamples.Capture(invalid[index]);
            Check.Throws<CanonicalEncodingException>(
                delegate { CanonicalJson.EncodeInitial(
                    new InitialRecord(ProtocolSamples.RunId, capture)); },
                "encoder surrogate " + index);
        }
    }
}
