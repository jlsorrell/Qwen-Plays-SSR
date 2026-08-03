using System;
using System.Globalization;

internal static class CaptureSignatureTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("encoding", "capture signature is exact", ExactSignature);
        tests.Add("encoding", "record line limit includes LF", ExactLineLimit);
    }

    private static byte[] Hex(string value)
    {
        byte[] bytes = new byte[value.Length / 2];
        for (int index = 0; index < bytes.Length; index++)
        {
            bytes[index] = Byte.Parse(
                value.Substring(index * 2, 2),
                NumberStyles.HexNumber,
                CultureInfo.InvariantCulture);
        }
        return bytes;
    }

    private static bool SameSignature(CaptureRecord left, CaptureRecord right)
    {
        return Convert.ToBase64String(CaptureSignature.Compute(left)) ==
            Convert.ToBase64String(CaptureSignature.Compute(right));
    }

    private static void ExactSignature()
    {
        CaptureRecord left = new CaptureRecord(
            "a", "12", "c", false, false, false, false, "", "", 0, 0, 0);
        CaptureRecord right = new CaptureRecord(
            "a1", "2", "c", false, false, false, false, "", "", 0, 0, 0);
        Check.False(
            SameSignature(left, right),
            "length prefixes prevent concatenation collision");

        CaptureRecord vectorB = new CaptureRecord(
            "r2", "42", "l2", false, true, true, false, "lost2", "display2",
            1, 2, 3);
        CaptureRecord[] variants = new CaptureRecord[]
        {
            new CaptureRecord(
                "r3", "42", "l2", false, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "43", "l2", false, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l3", false, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", true, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, false, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, false, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, true,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost3", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display3", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display2", 4, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display2", 1, 5, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display2", 1, 2, 6)
        };
        string[] fieldMessages = new string[]
        {
            "signature binds raw_save",
            "signature binds state_identity",
            "signature binds level",
            "signature binds overworld",
            "signature binds won",
            "signature binds returning",
            "signature binds have_ever_cooked_all",
            "signature binds lost_reason",
            "signature binds display_name",
            "signature binds sausages_cooked",
            "signature binds movement_count",
            "signature binds pushes_to_try"
        };
        Check.Equal(12, variants.Length, "one variant per capture field");
        Check.Equal(12, fieldMessages.Length, "one message per capture field");
        for (int index = 0; index < variants.Length; index++)
        {
            Check.False(
                SameSignature(vectorB, variants[index]),
                fieldMessages[index]);
        }

        Check.Bytes(
            Hex("c870e028a5a526efc0e8af5f78bcea1ff89198b29b16a875715c65f78649c6b7"),
            CaptureSignature.Compute(ProtocolSamples.InitialCapture),
            "fixed length-prefixed signature");

        CaptureRecord vectorA = new CaptureRecord(
            "é/雪", "-2147483648", "x", true, false, true, false, "", "z",
            Int32.MaxValue, 0, 0);
        Check.Bytes(
            Hex("6e924d4765c53622d9f734126cdf960fd525cc8a491068fe606606fb0833eac6"),
            CaptureSignature.Compute(vectorA),
            "fixed signature vector A");
        Check.Bytes(
            Hex("2ad1bf134d02a71476f3b7c220d817700079c10051607ab2796a2126406dde8d"),
            CaptureSignature.Compute(vectorB),
            "fixed signature vector B");

        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "\ud800", "7", "level", false, false, false, false,
                    "lost", "display", 4, 5, 6));
            },
            "signature rejects raw_save unpaired surrogate");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "raw", "7", "\ud800", false, false, false, false,
                    "lost", "display", 4, 5, 6));
            },
            "signature rejects level unpaired surrogate");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "raw", "7", "level", false, false, false, false,
                    "\ud800", "display", 4, 5, 6));
            },
            "signature rejects lost_reason unpaired surrogate");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "raw", "7", "level", false, false, false, false,
                    "lost", "\ud800", 4, 5, 6));
            },
            "signature rejects display_name unpaired surrogate");
    }

    private static ErrorRecord ErrorWithRawSaveLength(int length)
    {
        return new ErrorRecord(
            ProtocolSamples.RunId,
            1,
            OracleInput.North,
            "settle_timeout",
            600,
            ProtocolSamples.Capture(new string('x', length)));
    }

    private static void ExactLineLimit()
    {
        byte[] zeroLength = CanonicalJson.EncodeError(
            ErrorWithRawSaveLength(0));
        Check.Equal(421, zeroLength.Length, "zero-length boundary record bytes");

        const int AcceptedRawSaveLength = 16776794;
        byte[] exact;
        try
        {
            exact = CanonicalJson.EncodeError(
                ErrorWithRawSaveLength(AcceptedRawSaveLength));
        }
        catch (RecordTooLargeException error)
        {
            throw new InvalidOperationException(
                "exact record boundary is accepted", error);
        }
        Check.Equal(16777215, exact.Length, "exact JSON length before LF");
        Check.Equal(
            16777216,
            exact.Length + 1,
            "record boundary includes LF");
        Check.Throws<RecordTooLargeException>(
            delegate
            {
                CanonicalJson.EncodeError(
                    ErrorWithRawSaveLength(AcceptedRawSaveLength + 1));
            },
            "one byte beyond record boundary");
    }
}
