using System;
using System.IO;
using System.Text;

internal static class ReplayInputTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("replay-input", "exact bytes own hash and are immutable",
            ExactBytesOwnHashAndAreImmutable);
        tests.Add("replay-input", "all five tokens preserve file order",
            AllFiveTokensPreserveFileOrder);
        tests.Add("replay-input", "blank ASCII lines do not create tokens",
            BlankAsciiLinesDoNotCreateTokens);
        tests.Add("replay-input", "UTF8 BOM NUL and malformed text are rejected",
            InvalidTextIsRejected);
        tests.Add("replay-input", "unknown and empty streams are rejected",
            UnknownAndEmptyAreRejected);
        tests.Add("replay-input", "input source is read exactly once",
            InputSourceIsReadExactlyOnce);
    }

    private static void ExactBytesOwnHashAndAreImmutable()
    {
        byte[] lfBytes = Encoding.UTF8.GetBytes("West\n");
        ReplayInput lf = ReplayInput.Parse(lfBytes);
        ReplayInput crlf = ReplayInput.Parse(Encoding.UTF8.GetBytes("West\r\n"));

        Check.Equal(1, lf.Count, "LF count");
        Check.Equal(OracleInput.West, lf[0], "LF token");
        Check.Equal(1, crlf.Count, "CRLF count");
        Check.Equal(OracleInput.West, crlf[0], "CRLF token");
        Check.Equal(
            "f8ace91df3cf40e0410cd9da8df1a2859a5a1aba66e423ed4bd951ba3c14ba7a",
            lf.Sha256, "LF exact-byte hash");
        Check.Equal(
            "3c330ceeae55c642522970951e6a68e69526cf2a9cbc4eedcb86e3f342c52eff",
            crlf.Sha256, "CRLF exact-byte hash");
        Check.False(lf.Sha256 == crlf.Sha256, "line endings change identity");

        lfBytes[0] = (byte)'X';
        byte[] returnedBytes = lf.Bytes;
        returnedBytes[0] = (byte)'Y';
        OracleInput[] returnedTokens = lf.Tokens;
        returnedTokens[0] = OracleInput.North;

        Check.Bytes(Encoding.UTF8.GetBytes("West\n"), lf.Bytes,
            "stored bytes remain exact");
        Check.Equal(
            "f8ace91df3cf40e0410cd9da8df1a2859a5a1aba66e423ed4bd951ba3c14ba7a",
            lf.Sha256, "stored hash remains exact");
        Check.Equal(1, lf.Count, "stored count remains exact");
        Check.Equal(OracleInput.West, lf[0], "stored index remains exact");
        Check.Equal(OracleInput.West, lf.Tokens[0],
            "stored token array remains exact");
    }

    private static void AllFiveTokensPreserveFileOrder()
    {
        ReplayInput input = ReplayInput.Parse(Encoding.UTF8.GetBytes(
            "North\n South \n\tWest\t\nEast\nUndo\n"));
        Check.Equal(5, input.Count, "five-token count");
        Check.Sequence(new OracleInput[] {
            OracleInput.North, OracleInput.South, OracleInput.West,
            OracleInput.East, OracleInput.Undo
        }, input.Tokens, "five-token order");
        for (int index = 0; index < input.Count; index++)
            Check.Equal(input.Tokens[index], input[index], "token indexer");
    }

    private static void BlankAsciiLinesDoNotCreateTokens()
    {
        ReplayInput input = ReplayInput.Parse(Encoding.UTF8.GetBytes(
            "\n \t\r\f\v\nWest\n"));
        Check.Equal(1, input.Count, "blank-line count");
        Check.Equal(OracleInput.West, input[0], "blank-line token zero");
    }

    private static void InvalidTextIsRejected()
    {
        byte[][] cases = new byte[][] {
            new byte[] { 0xef, 0xbb, 0xbf, (byte)'W' },
            new byte[] { 0xff },
            Encoding.UTF8.GetBytes("North\0\n"),
            Encoding.UTF8.GetBytes("North\rSouth")
        };
        for (int index = 0; index < cases.Length; index++)
            AssertInvalid(cases[index], "invalid text " + index.ToString());
    }

    private static void UnknownAndEmptyAreRejected()
    {
        string[] cases = new string[] {
            "north\n", "1\n", "None\n", "West # comment\n", "", " \t\r\f\v\n"
        };
        for (int index = 0; index < cases.Length; index++)
            AssertInvalid(Encoding.UTF8.GetBytes(cases[index]),
                "unknown or empty " + index.ToString());
        AssertInvalid(null, "null bytes");
    }

    private static void InputSourceIsReadExactlyOnce()
    {
        StaticReplayInputBytes valid = new StaticReplayInputBytes(
            Encoding.UTF8.GetBytes("East\n"));
        ReplayInput loaded = ReplayInput.Load("/input.dem", valid);
        Check.Equal(1, valid.ReadCount, "valid source read once");
        Check.Equal("/input.dem", valid.LastPath, "valid source path");
        Check.Equal(OracleInput.East, loaded[0], "valid loaded token");

        StaticReplayInputBytes nullSource = new StaticReplayInputBytes(null);
        OracleConfigurationException nullError =
            Check.Throws<OracleConfigurationException>(delegate {
                ReplayInput.Load("/null.dem", nullSource);
            }, "null source result");
        Check.Equal("invalid_configuration", nullError.Code,
            "null source result code");
        Check.True(nullError.InnerException is IOException,
            "null source result cause");
        Check.Equal(1, nullSource.ReadCount, "null source read once");

        IOException cause = new IOException("read failed");
        ThrowingReplayInputBytes throwing = new ThrowingReplayInputBytes(cause);
        OracleConfigurationException thrown =
            Check.Throws<OracleConfigurationException>(delegate {
                ReplayInput.Load("/throw.dem", throwing);
            }, "throwing source");
        Check.Equal("invalid_configuration", thrown.Code,
            "throwing source code");
        Check.Same(cause, thrown.InnerException, "throwing source cause retained");
        Check.Equal(1, throwing.ReadCount, "throwing source read once");

        StaticReplayInputBytes uncalled = new StaticReplayInputBytes(
            Encoding.UTF8.GetBytes("North\n"));
        OracleConfigurationException pathError =
            Check.Throws<OracleConfigurationException>(delegate {
                ReplayInput.Load("", uncalled);
            }, "empty input path");
        Check.Equal("invalid_configuration", pathError.Code,
            "empty input path code");
        Check.Equal(0, uncalled.ReadCount, "invalid path prevents source read");
        Check.Throws<ArgumentNullException>(delegate {
            ReplayInput.Load("/input.dem", null);
        }, "null input source");
    }

    private static void AssertInvalid(byte[] bytes, string label)
    {
        OracleConfigurationException error =
            Check.Throws<OracleConfigurationException>(delegate {
                ReplayInput.Parse(bytes);
            }, label);
        Check.Equal("invalid_configuration", error.Code, label + " code");
        Check.True(error.InnerException != null, label + " cause");
    }
}

internal sealed class StaticReplayInputBytes : IReplayInputBytes
{
    private readonly byte[] bytes;
    internal int ReadCount;
    internal string LastPath;

    internal StaticReplayInputBytes(byte[] bytes)
    {
        this.bytes = bytes;
    }

    public byte[] ReadAllBytes(string inputPath)
    {
        ReadCount++;
        LastPath = inputPath;
        return bytes == null ? null : (byte[])bytes.Clone();
    }
}

internal sealed class ThrowingReplayInputBytes : IReplayInputBytes
{
    private readonly Exception error;
    internal int ReadCount;

    internal ThrowingReplayInputBytes(Exception error)
    {
        this.error = error;
    }

    public byte[] ReadAllBytes(string inputPath)
    {
        ReadCount++;
        throw error;
    }
}
