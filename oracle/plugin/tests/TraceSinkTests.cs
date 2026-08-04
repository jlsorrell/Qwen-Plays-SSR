using System;
using System.Collections.Generic;
using System.IO;

internal sealed class FakeTraceOutput : ITraceOutput
{
    internal readonly List<byte> Bytes = new List<byte>();
    internal readonly Queue<int> WriteCounts = new Queue<int>();
    internal readonly List<int> FlushByteCounts = new List<int>();
    internal Exception WriteFailure;
    internal Exception FlushFailure;
    internal Exception CloseFailure;
    internal bool ReturnTooMany;
    internal int FlushCalls;
    internal int CloseCalls;

    public int Write(byte[] buffer, int offset, int count)
    {
        if (WriteFailure != null)
            throw WriteFailure;
        if (ReturnTooMany)
            return count + 1;
        int written = WriteCounts.Count == 0 ? count : WriteCounts.Dequeue();
        if (written < 0 || written > count)
            throw new InvalidOperationException("invalid fake write count");
        for (int index = 0; index < written; index++)
            Bytes.Add(buffer[offset + index]);
        return written;
    }

    public void Flush()
    {
        FlushCalls++;
        FlushByteCounts.Add(Bytes.Count);
        if (FlushFailure != null)
            throw FlushFailure;
    }

    public void Close()
    {
        CloseCalls++;
        if (CloseFailure != null)
            throw CloseFailure;
    }
}

internal sealed class FakeTraceFileFactory : ITraceFileFactory
{
    internal FakeTraceOutput Output = new FakeTraceOutput();
    internal string Path;
    internal FileMode Mode;
    internal FileAccess Access;
    internal FileShare Share;
    internal Exception Failure;

    public ITraceOutput CreateNew(
        string path, FileMode mode, FileAccess access, FileShare share)
    {
        Path = path;
        Mode = mode;
        Access = access;
        Share = share;
        if (Failure != null)
            throw Failure;
        return Output;
    }
}

internal static class TraceSinkTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("sink", "factory arguments are exact", FactoryArguments);
        tests.Add("sink", "null factory output is typed", NullFactoryOutputIsTyped);
        tests.Add("sink", "real collision is typed", RealCollisionIsTyped);
        tests.Add("sink", "records use LF and flush", RecordsUseLfAndFlush);
        tests.Add("sink", "bounds and write failures are terminal", WriteFailuresAreTerminal);
        tests.Add("sink", "close ownership is single use", CloseIsSingleUse);
    }

    private static void FactoryArguments()
    {
        FakeTraceFileFactory factory = new FakeTraceFileFactory();
        NdjsonTraceSink sink = NdjsonTraceSink.Create(
            "/private/tmp/output", "passive-trace", factory);
        Check.Equal(
            Path.Combine("/private/tmp/output", "passive-trace.ndjson"),
            factory.Path, "combined target");
        Check.Equal(FileMode.CreateNew, factory.Mode, "create-new mode");
        Check.Equal(FileAccess.Write, factory.Access, "write access");
        Check.Equal(FileShare.None, factory.Share, "exclusive sharing");
        sink.Close();
        Check.Equal(1, factory.Output.CloseCalls, "owned close");
    }

    private static void NullFactoryOutputIsTyped()
    {
        FakeTraceFileFactory factory = new FakeTraceFileFactory();
        factory.Output = null;
        Check.Throws<TraceIoException>(
            delegate
            {
                NdjsonTraceSink.Create(
                    "/private/tmp/output", "passive-trace", factory);
            },
            "null create-new result");

        FakeTraceFileFactory failing = new FakeTraceFileFactory();
        IOException injected = new IOException("injected create");
        failing.Failure = injected;
        IOException observed = Check.Throws<IOException>(
            delegate
            {
                NdjsonTraceSink.Create(
                    "/private/tmp/output", "passive-trace", failing);
            },
            "injected factory failure");
        Check.Same(injected, observed, "factory failure identity");
    }

    private static void RealCollisionIsTyped()
    {
        string directory = Path.Combine(
            Path.GetTempPath(), "ssr-oracle-sink-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        string path = Path.Combine(directory, "passive-trace.ndjson");
        NdjsonTraceSink unexpected = null;
        try
        {
            NdjsonTraceSink sink = NdjsonTraceSink.Create(directory, "passive-trace");
            sink.Close();
            byte[] sentinel = new byte[] { 0x00, 0x7f, 0x80, 0xff };
            File.WriteAllBytes(path, sentinel);
            Check.Bytes(
                sentinel,
                File.ReadAllBytes(path),
                "collision sentinel written");
            Check.Throws<TraceExistsException>(
                delegate
                {
                    unexpected = NdjsonTraceSink.Create(
                        directory, "passive-trace");
                },
                "atomic create-new collision");
            Check.Bytes(
                sentinel,
                File.ReadAllBytes(path),
                "collision preserves bytes");
        }
        finally
        {
            if (unexpected != null)
            {
                try
                {
                    unexpected.Close();
                }
                catch (Exception)
                {
                }
            }
            if (Directory.Exists(directory))
                Directory.Delete(directory, true);
        }
    }

    private static void RecordsUseLfAndFlush()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        output.WriteCounts.Enqueue(1);
        output.WriteCounts.Enqueue(1);
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        List<byte> expected = new List<byte>();

        sink.WriteRun(ProtocolSamples.Run);
        AppendLine(expected, CanonicalJson.EncodeRun(ProtocolSamples.Run));
        Check.Sequence(
            expected, output.Bytes, "records run exact cumulative LF bytes");
        Check.Equal(
            0, output.WriteCounts.Count,
            "records positive partial writes are retried");
        Check.Equal(1, output.FlushCalls, "records run flush count");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[0],
            "records run flush follows LF");

        sink.WriteInitial(ProtocolSamples.Initial);
        AppendLine(expected, CanonicalJson.EncodeInitial(ProtocolSamples.Initial));
        Check.Sequence(
            expected, output.Bytes, "records initial exact cumulative LF bytes");
        Check.Equal(2, output.FlushCalls, "records initial flush count");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[1],
            "records initial flush follows LF");

        sink.WriteStep(ProtocolSamples.Step0);
        AppendLine(expected, CanonicalJson.EncodeStep(ProtocolSamples.Step0));
        Check.Sequence(
            expected, output.Bytes, "records step exact cumulative LF bytes");
        Check.Equal(3, output.FlushCalls, "records step flush count");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[2],
            "records step flush follows LF");

        sink.WriteEnd(ProtocolSamples.End);
        AppendLine(expected, CanonicalJson.EncodeEnd(ProtocolSamples.End));
        Check.Sequence(
            expected, output.Bytes, "records end exact cumulative LF bytes");
        Check.Equal(4, output.FlushCalls, "records end flush count");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[3],
            "records end flush follows LF");

        sink.WriteError(ProtocolSamples.Error);
        AppendLine(expected, CanonicalJson.EncodeError(ProtocolSamples.Error));
        Check.Sequence(
            expected, output.Bytes, "records error exact cumulative LF bytes");
        Check.Equal(5, output.FlushCalls, "records final flush count is five");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[4],
            "records error flush follows LF");
        Check.Equal(
            5,
            output.FlushByteCounts.Count,
            "records have five flush boundary snapshots");
        Check.Sequence(
            expected, output.Bytes, "records final exact five-line stream");
        Check.False(
            output.Bytes.Count >= 3
            && output.Bytes[0] == 0xef
            && output.Bytes[1] == 0xbb
            && output.Bytes[2] == 0xbf,
            "records stream has no UTF-8 BOM");
    }

    private static void WriteFailuresAreTerminal()
    {
        SessionLimitCountsLfAndBecomesTerminal();
        ZeroProgressIsTerminal();
        OverReportedProgressIsTerminal();
        InjectedWriteFailureIsTerminal();
        InjectedFlushFailureIsTerminal();
        EncodingFailureLeavesSinkReusable();
        RecordSizeFailureLeavesSinkReusable();
    }

    private static void SessionLimitCountsLfAndBecomesTerminal()
    {
        byte[] run = CanonicalJson.EncodeRun(ProtocolSamples.Run);
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(
            output, 2L * (long)run.Length);
        List<byte> accepted = new List<byte>();
        AppendLine(accepted, run);
        byte[] end = CanonicalJson.EncodeEnd(ProtocolSamples.End);
        long remainingCapacity = 2L * (long)run.Length - accepted.Count;
        Check.True(
            (long)end.Length + 1L <= remainingCapacity,
            "budget terminal probe fits remaining capacity");

        sink.WriteRun(ProtocolSamples.Run);
        Check.Sequence(
            accepted, output.Bytes, "budget first line exact bytes");
        Check.Equal(1, output.FlushCalls, "budget first line flush count");
        Check.Equal(
            accepted.Count,
            output.FlushByteCounts[0],
            "budget first line flush follows LF");

        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "budget counts LF in cumulative limit");
        Check.Sequence(
            accepted, output.Bytes, "budget rejection is pre-output");
        Check.Equal(
            1, output.FlushCalls, "budget rejection has no flush");
        Check.Equal(
            1,
            output.FlushByteCounts.Count,
            "budget rejection preserves flush snapshots");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "budget failure is terminal with remaining capacity");
        Check.Sequence(
            accepted,
            output.Bytes,
            "budget terminal retry leaves bytes unchanged");
        Check.Equal(
            1,
            output.FlushCalls,
            "budget terminal retry leaves flush count unchanged");

        AssertOneCloseAfterFailure(sink, output, "budget failure");
    }

    private static void ZeroProgressIsTerminal()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        output.WriteCounts.Enqueue(1);
        output.WriteCounts.Enqueue(0);
        NdjsonTraceSink sink = new NdjsonTraceSink(output);

        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "zero progress is typed");
        Check.Equal(1, output.Bytes.Count, "zero progress keeps partial prefix");
        Check.Equal(
            0, output.FlushCalls, "zero progress never flushes incomplete line");
        List<byte> failedBytes = new List<byte>(output.Bytes);
        Check.Throws<TraceIoException>(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "zero progress failure is terminal");
        Check.Sequence(
            failedBytes,
            output.Bytes,
            "zero progress terminal retry leaves bytes unchanged");
        Check.Equal(
            0,
            output.FlushCalls,
            "zero progress terminal retry leaves flush count unchanged");

        AssertOneCloseAfterFailure(sink, output, "zero progress failure");
    }

    private static void OverReportedProgressIsTerminal()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        output.ReturnTooMany = true;
        NdjsonTraceSink sink = new NdjsonTraceSink(output);

        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "over-reported progress is typed");
        Check.Equal(
            0, output.Bytes.Count, "over-reported progress copies no bytes");
        Check.Equal(
            0, output.FlushCalls, "over-reported progress never flushes");
        output.ReturnTooMany = false;
        Check.Throws<TraceIoException>(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "over-reported progress failure is terminal");
        Check.Equal(
            0,
            output.Bytes.Count,
            "over-reported terminal retry leaves bytes unchanged");
        Check.Equal(
            0,
            output.FlushCalls,
            "over-reported terminal retry leaves flush count unchanged");

        AssertOneCloseAfterFailure(
            sink, output, "over-reported progress failure");
    }

    private static void InjectedWriteFailureIsTerminal()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        IOException injected = new IOException("injected write");
        output.WriteFailure = injected;
        NdjsonTraceSink sink = new NdjsonTraceSink(output);

        TraceIoException observed = Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "write failure is typed");
        Check.Same(
            injected,
            observed.InnerException,
            "write failure preserves exception identity");
        List<byte> failedBytes = new List<byte>(output.Bytes);
        List<int> failedFlushes = new List<int>(output.FlushByteCounts);
        int failedFlushCalls = output.FlushCalls;
        output.WriteFailure = null;
        Check.Throws<TraceIoException>(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "write failure is terminal after stimulus clears");
        Check.Sequence(
            failedBytes,
            output.Bytes,
            "write terminal retry leaves bytes unchanged");
        Check.Equal(
            failedFlushCalls,
            output.FlushCalls,
            "write terminal retry leaves flush count unchanged");
        Check.Sequence(
            failedFlushes,
            output.FlushByteCounts,
            "write terminal retry leaves flush snapshots unchanged");

        AssertOneCloseAfterFailure(sink, output, "write failure");
    }

    private static void InjectedFlushFailureIsTerminal()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        IOException injected = new IOException("injected flush");
        output.FlushFailure = injected;
        NdjsonTraceSink sink = new NdjsonTraceSink(output);

        TraceIoException observed = Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "flush failure is typed");
        Check.Same(
            injected,
            observed.InnerException,
            "flush failure preserves exception identity");
        List<byte> failedBytes = new List<byte>(output.Bytes);
        List<int> failedFlushes = new List<int>(output.FlushByteCounts);
        int failedFlushCalls = output.FlushCalls;
        output.FlushFailure = null;
        Check.Throws<TraceIoException>(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "flush failure is terminal after stimulus clears");
        Check.Sequence(
            failedBytes,
            output.Bytes,
            "flush terminal retry leaves bytes unchanged");
        Check.Equal(
            failedFlushCalls,
            output.FlushCalls,
            "flush terminal retry leaves flush count unchanged");
        Check.Sequence(
            failedFlushes,
            output.FlushByteCounts,
            "flush terminal retry leaves flush snapshots unchanged");

        AssertOneCloseAfterFailure(sink, output, "flush failure");
    }

    private static void EncodingFailureLeavesSinkReusable()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        InitialRecord invalid = new InitialRecord(
            ProtocolSamples.RunId, ProtocolSamples.Capture("\ud800"));

        Check.Throws<CanonicalEncodingException>(
            delegate { sink.WriteInitial(invalid); },
            "encoding failure is typed before output");
        Check.Equal(
            0, output.Bytes.Count, "encoding failure emits no bytes");
        Check.Equal(
            0, output.FlushCalls, "encoding failure performs no flush");
        Check.Equal(
            0,
            output.FlushByteCounts.Count,
            "encoding failure records no flush boundary");
        RequireSuccess(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "encoding failure leaves sink reusable");
        List<byte> expected = new List<byte>();
        AppendLine(expected, CanonicalJson.EncodeEnd(ProtocolSamples.End));
        Check.Sequence(
            expected,
            output.Bytes,
            "encoding recovery writes exact valid line");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[0],
            "encoding recovery flush follows LF");
        sink.Close();
        Check.Equal(1, output.CloseCalls, "encoding recovery closes once");
    }

    private static void RecordSizeFailureLeavesSinkReusable()
    {
        const int AcceptedRawSaveLength = 16776794;
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output);

        Check.Throws<RecordTooLargeException>(
            delegate
            {
                sink.WriteError(
                    ErrorWithRawSaveLength(AcceptedRawSaveLength + 1));
            },
            "record-size failure is typed before output");
        Check.Equal(
            0, output.Bytes.Count, "record-size failure emits no bytes");
        Check.Equal(
            0, output.FlushCalls, "record-size failure performs no flush");
        Check.Equal(
            0,
            output.FlushByteCounts.Count,
            "record-size failure records no flush boundary");
        RequireSuccess(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            "record-size failure leaves sink reusable");
        List<byte> expected = new List<byte>();
        AppendLine(expected, CanonicalJson.EncodeEnd(ProtocolSamples.End));
        Check.Sequence(
            expected,
            output.Bytes,
            "record-size recovery writes exact valid line");
        Check.Equal(
            expected.Count,
            output.FlushByteCounts[0],
            "record-size recovery flush follows LF");
        sink.Close();
        Check.Equal(1, output.CloseCalls, "record-size recovery closes once");
    }

    private static void CloseIsSingleUse()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        sink.Close();
        Check.Equal(1, output.CloseCalls, "normal close attempted exactly once");
        Check.Throws<InvalidOperationException>(
            delegate { sink.Close(); },
            "normal second close rejected");
        Check.Equal(
            1, output.CloseCalls, "normal close has no underlying retry");
        AssertAllRecordsRejected(sink, "normal close");

        FakeTraceOutput failing = new FakeTraceOutput();
        IOException injected = new IOException("injected close");
        failing.CloseFailure = injected;
        NdjsonTraceSink failingSink = new NdjsonTraceSink(failing);
        TraceIoException observed = Check.Throws<TraceIoException>(
            delegate { failingSink.Close(); },
            "failed close is typed");
        Check.Same(
            injected,
            observed.InnerException,
            "failed close preserves exception identity");
        Check.Equal(
            1, failing.CloseCalls, "failed close attempted exactly once");
        failing.CloseFailure = null;
        Check.Throws<InvalidOperationException>(
            delegate { failingSink.Close(); },
            "failed close retry rejected after stimulus clears");
        Check.Equal(
            1, failing.CloseCalls, "failed close has no underlying retry");
        AssertAllRecordsRejected(failingSink, "failed close");
    }

    private static void AppendLine(List<byte> target, byte[] encoded)
    {
        for (int index = 0; index < encoded.Length; index++)
            target.Add(encoded[index]);
        target.Add(0x0a);
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

    private static void RequireSuccess(Action action, string message)
    {
        Exception observed = null;
        try
        {
            action();
        }
        catch (Exception error)
        {
            observed = error;
        }
        Check.True(observed == null, message);
    }

    private static void AssertOneCloseAfterFailure(
        NdjsonTraceSink sink,
        FakeTraceOutput output,
        string label)
    {
        Exception observed = null;
        try
        {
            sink.Close();
        }
        catch (Exception error)
        {
            observed = error;
        }
        Check.True(observed == null, label + " first close remains legal");
        Check.Equal(
            1, output.CloseCalls, label + " first close reaches output");
        Check.Throws<InvalidOperationException>(
            delegate { sink.Close(); },
            label + " second close rejected");
        Check.Equal(
            1, output.CloseCalls, label + " has no underlying close retry");
    }

    private static void AssertAllRecordsRejected(
        NdjsonTraceSink sink,
        string label)
    {
        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            label + " rejects Run");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteInitial(ProtocolSamples.Initial); },
            label + " rejects Initial");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteStep(ProtocolSamples.Step0); },
            label + " rejects Step");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteEnd(ProtocolSamples.End); },
            label + " rejects End");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteError(ProtocolSamples.Error); },
            label + " rejects Error");
    }
}
