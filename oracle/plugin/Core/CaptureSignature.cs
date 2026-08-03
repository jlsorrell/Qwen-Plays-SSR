using System;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;

internal static class CaptureSignature
{
    private static readonly Encoding Ascii = Encoding.ASCII;

    internal static byte[] Compute(CaptureRecord capture)
    {
        if (capture == null)
            throw new ArgumentNullException("capture");
        using (SHA256 hash = SHA256.Create())
        {
            Feed(hash, CanonicalJson.StrictUtf8(capture.RawSave));
            Feed(hash, CanonicalJson.StrictUtf8(capture.StateIdentity));
            Feed(hash, CanonicalJson.StrictUtf8(capture.Level));
            Feed(hash, Boolean(capture.Overworld));
            Feed(hash, Boolean(capture.Won));
            Feed(hash, Boolean(capture.Returning));
            Feed(hash, Boolean(capture.HaveEverCookedAll));
            Feed(hash, CanonicalJson.StrictUtf8(capture.LostReason));
            Feed(hash, CanonicalJson.StrictUtf8(capture.DisplayName));
            Feed(hash, Integer(capture.SausagesCooked));
            Feed(hash, Integer(capture.MovementCount));
            Feed(hash, Integer(capture.PushesToTry));
            hash.TransformFinalBlock(new byte[0], 0, 0);
            return (byte[])hash.Hash.Clone();
        }
    }

    private static byte[] Boolean(bool value)
    {
        return Ascii.GetBytes(value ? "true" : "false");
    }

    private static byte[] Integer(int value)
    {
        return Ascii.GetBytes(value.ToString(CultureInfo.InvariantCulture));
    }

    private static void Feed(SHA256 hash, byte[] value)
    {
        int length = value.Length;
        byte[] prefix = new byte[4];
        prefix[0] = (byte)((length >> 24) & 0xff);
        prefix[1] = (byte)((length >> 16) & 0xff);
        prefix[2] = (byte)((length >> 8) & 0xff);
        prefix[3] = (byte)(length & 0xff);
        hash.TransformBlock(prefix, 0, prefix.Length, prefix, 0);
        if (value.Length != 0)
            hash.TransformBlock(value, 0, value.Length, value, 0);
    }
}
