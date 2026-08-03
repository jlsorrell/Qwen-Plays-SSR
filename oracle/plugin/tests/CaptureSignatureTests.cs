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

    private static void ExactSignature()
    {
        Check.Bytes(
            Hex("c870e028a5a526efc0e8af5f78bcea1ff89198b29b16a875715c65f78649c6b7"),
            CaptureSignature.Compute(ProtocolSamples.InitialCapture),
            "fixed length-prefixed signature");
        CaptureRecord multibyte = new CaptureRecord(
            "é/雪", "-2147483648", "x", true, false, true, false, "", "z",
            Int32.MaxValue, 0, 0);
        Check.False(
            Convert.ToBase64String(CaptureSignature.Compute(multibyte)) ==
            Convert.ToBase64String(
                CaptureSignature.Compute(ProtocolSamples.InitialCapture)),
            "all fields affect signature");
        CaptureRecord left = new CaptureRecord(
            "ab", "1", "c", false, false, false, false, "", "", 0, 0, 0);
        CaptureRecord right = new CaptureRecord(
            "a", "1", "bc", false, false, false, false, "", "", 0, 0, 0);
        Check.False(
            Convert.ToBase64String(CaptureSignature.Compute(left)) ==
            Convert.ToBase64String(CaptureSignature.Compute(right)),
            "length prefixes prevent concatenation collision");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(ProtocolSamples.Capture("\ud800"));
            },
            "signature rejects an unpaired surrogate");
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
        int low = 0;
        int high = 16 * 1024 * 1024;
        int accepted = -1;
        while (low <= high)
        {
            int middle = low + ((high - low) / 2);
            try
            {
                CanonicalJson.EncodeError(ErrorWithRawSaveLength(middle));
                accepted = middle;
                low = middle + 1;
            }
            catch (RecordTooLargeException)
            {
                high = middle - 1;
            }
        }
        byte[] exact = CanonicalJson.EncodeError(
            ErrorWithRawSaveLength(accepted));
        Check.Equal(
            16 * 1024 * 1024,
            exact.Length + 1,
            "record boundary includes LF");
        Check.Throws<RecordTooLargeException>(
            delegate
            {
                CanonicalJson.EncodeError(
                    ErrorWithRawSaveLength(accepted + 1));
            },
            "one byte beyond record boundary");
    }
}
