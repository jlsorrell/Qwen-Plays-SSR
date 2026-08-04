using System;
using System.Globalization;
using System.IO;
using System.Text;

internal sealed class CanonicalEncodingException : Exception
{
    internal CanonicalEncodingException(string message)
        : base(message)
    {
    }

    internal CanonicalEncodingException(string message, Exception inner)
        : base(message, inner)
    {
    }
}

internal sealed class RecordTooLargeException : Exception
{
    internal RecordTooLargeException()
        : base("encoded trace record exceeded its limit")
    {
    }
}

internal static class CanonicalJson
{
    private static readonly UTF8Encoding StrictUtf8Encoding =
        new UTF8Encoding(false, true);

    internal static byte[] EncodeRun(RunRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"run\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"mode\":\"passive\",\"game_assembly_sha256\":");
            WriteString(output, record.GameAssemblySha256);
            WriteAscii(output, ",\"plugin_version\":");
            WriteString(output, record.PluginVersion);
            WriteAscii(output, ",\"input_sha256\":null,\"expected_input_count\":");
            WriteInt(output, record.ExpectedInputCount);
            WriteAscii(output, ",\"started_at_utc\":");
            WriteTimestamp(output, record.StartedAtUtc);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeInitial(InitialRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"initial\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_index\":null,\"capture\":");
            WriteCapture(output, record.Capture);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeStep(StepRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"step\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_index\":");
            WriteInt(output, record.InputIndex);
            WriteAscii(output, ",\"input\":");
            WriteString(output, record.Input.ToString());
            WriteAscii(output, ",\"accepted\":");
            WriteBool(output, record.Accepted);
            WriteAscii(output, ",\"movement_scheduled\":");
            WriteBool(output, record.MovementScheduled);
            WriteAscii(output, ",\"settle_frames\":");
            WriteInt(output, record.SettleFrames);
            WriteAscii(output, ",\"state_replaced\":false,\"capture\":");
            WriteCapture(output, record.Capture);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeEnd(EndRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"end\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_count\":");
            WriteInt(output, record.InputCount);
            WriteAscii(output, ",\"finished_at_utc\":");
            WriteTimestamp(output, record.FinishedAtUtc);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeError(ErrorRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"error\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_index\":");
            if (record.InputIndex.HasValue)
                WriteInt(output, record.InputIndex.Value);
            else
                WriteAscii(output, "null");
            WriteAscii(output, ",\"input\":");
            if (record.Input.HasValue)
                WriteString(output, record.Input.Value.ToString());
            else
                WriteAscii(output, "null");
            WriteAscii(output, ",\"code\":");
            WriteString(output, record.Code);
            WriteAscii(output, ",\"message\":");
            WriteString(output, record.Message);
            WriteAscii(output, ",\"settle_frames\":");
            WriteInt(output, record.SettleFrames);
            WriteAscii(output, ",\"last_capture\":");
            if (record.LastCapture == null)
                WriteAscii(output, "null");
            else
                WriteCapture(output, record.LastCapture);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static void ValidateRecordSize(byte[] encoded)
    {
        if (encoded == null)
            throw new ArgumentNullException("encoded");
        if ((long)encoded.Length + 1L > 16L * 1024L * 1024L)
            throw new RecordTooLargeException();
    }

    internal static byte[] StrictUtf8(string value)
    {
        if (value == null)
            throw new ArgumentNullException("value");
        for (int index = 0; index < value.Length; index += ScalarLength(value, index))
        {
        }
        try
        {
            return StrictUtf8Encoding.GetBytes(value);
        }
        catch (EncoderFallbackException error)
        {
            throw new CanonicalEncodingException("invalid UTF-16 text", error);
        }
    }

    private static byte[] Finish(MemoryStream output)
    {
        byte[] encoded = output.ToArray();
        ValidateRecordSize(encoded);
        return encoded;
    }

    private static void WriteCapture(MemoryStream output, CaptureRecord capture)
    {
        WriteAscii(output, "{\"raw_save\":");
        WriteString(output, capture.RawSave);
        WriteAscii(output, ",\"state_identity\":");
        WriteString(output, capture.StateIdentity);
        WriteAscii(output, ",\"level\":");
        WriteString(output, capture.Level);
        WriteAscii(output, ",\"overworld\":");
        WriteBool(output, capture.Overworld);
        WriteAscii(output, ",\"won\":");
        WriteBool(output, capture.Won);
        WriteAscii(output, ",\"returning\":");
        WriteBool(output, capture.Returning);
        WriteAscii(output, ",\"have_ever_cooked_all\":");
        WriteBool(output, capture.HaveEverCookedAll);
        WriteAscii(output, ",\"lost_reason\":");
        WriteString(output, capture.LostReason);
        WriteAscii(output, ",\"display_name\":");
        WriteString(output, capture.DisplayName);
        WriteAscii(output, ",\"sausages_cooked\":");
        WriteInt(output, capture.SausagesCooked);
        WriteAscii(output, ",\"movement_count\":");
        WriteInt(output, capture.MovementCount);
        WriteAscii(output, ",\"pushes_to_try\":");
        WriteInt(output, capture.PushesToTry);
        WriteAscii(output, "}");
    }

    private static void WriteTimestamp(MemoryStream output, DateTime value)
    {
        OracleValidation.Utc(value, "value");
        string text = value.ToString("O", CultureInfo.InvariantCulture);
        if (!IsTimestamp(text))
            throw new CanonicalEncodingException("noncanonical UTC timestamp");
        WriteString(output, text);
    }

    private static bool IsTimestamp(string value)
    {
        if (value.Length != 28
            || value[4] != '-'
            || value[7] != '-'
            || value[10] != 'T'
            || value[13] != ':'
            || value[16] != ':'
            || value[19] != '.'
            || value[27] != 'Z')
        {
            return false;
        }
        for (int index = 0; index < value.Length; index++)
        {
            if (index == 4 || index == 7 || index == 10 || index == 13
                || index == 16 || index == 19 || index == 27)
            {
                continue;
            }
            if (value[index] < '0' || value[index] > '9')
                return false;
        }
        return true;
    }

    private static void WriteString(MemoryStream output, string value)
    {
        if (value == null)
            throw new ArgumentNullException("value");
        WriteAscii(output, "\"");
        int literalStart = 0;
        int index = 0;
        while (index < value.Length)
        {
            char current = value[index];
            if (current == '"' || current == '\\' || current < 0x20)
            {
                WriteUtf8(output, value, literalStart, index - literalStart);
                if (current == '"')
                    WriteAscii(output, "\\\"");
                else if (current == '\\')
                    WriteAscii(output, "\\\\");
                else
                    WriteAscii(output, ControlEscape(current));
                index++;
                literalStart = index;
            }
            else
            {
                index += ScalarLength(value, index);
            }
        }
        WriteUtf8(output, value, literalStart, value.Length - literalStart);
        WriteAscii(output, "\"");
    }

    private static int ScalarLength(string value, int index)
    {
        char current = value[index];
        if (char.IsHighSurrogate(current))
        {
            if (index + 1 >= value.Length
                || !char.IsLowSurrogate(value[index + 1]))
            {
                throw new CanonicalEncodingException(
                    "unpaired UTF-16 surrogate");
            }
            return 2;
        }
        if (char.IsLowSurrogate(current))
            throw new CanonicalEncodingException("unpaired UTF-16 surrogate");
        return 1;
    }

    private static string ControlEscape(char value)
    {
        switch (value)
        {
            case '\b': return "\\b";
            case '\f': return "\\f";
            case '\n': return "\\n";
            case '\r': return "\\r";
            case '\t': return "\\t";
            default:
                const string Hex = "0123456789abcdef";
                return "\\u00" + Hex[(value >> 4) & 15] + Hex[value & 15];
        }
    }

    private static void WriteBool(MemoryStream output, bool value)
    {
        WriteAscii(output, value ? "true" : "false");
    }

    private static void WriteInt(MemoryStream output, int value)
    {
        WriteAscii(output, value.ToString(CultureInfo.InvariantCulture));
    }

    private static void WriteAscii(MemoryStream output, string value)
    {
        for (int index = 0; index < value.Length; index++)
        {
            if (value[index] > 0x7f)
                throw new InvalidOperationException("non-ASCII punctuation");
            output.WriteByte((byte)value[index]);
        }
    }

    private static void WriteUtf8(
        MemoryStream output,
        string value,
        int start,
        int count)
    {
        if (count == 0)
            return;
        byte[] buffer = new byte[StrictUtf8Encoding.GetMaxByteCount(count)];
        int written;
        try
        {
            written = StrictUtf8Encoding.GetBytes(
                value, start, count, buffer, 0);
        }
        catch (EncoderFallbackException error)
        {
            throw new CanonicalEncodingException("invalid UTF-16 text", error);
        }
        output.Write(buffer, 0, written);
    }
}
