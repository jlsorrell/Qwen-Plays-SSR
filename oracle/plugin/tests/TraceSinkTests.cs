using System;
using System.Collections.Generic;
using System.IO;

internal sealed class FakeTraceOutput : ITraceOutput
{
    internal readonly List<byte> Bytes = new List<byte>();
    internal readonly Queue<int> WriteCounts = new Queue<int>();
    internal Exception WriteFailure;
    internal Exception FlushFailure;
    internal Exception CloseFailure;
    internal int FlushCalls;
    internal int CloseCalls;

    public int Write(byte[] buffer, int offset, int count)
    {
        if (WriteFailure != null)
            throw WriteFailure;
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
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        sink.WriteRun(ProtocolSamples.Run);
        sink.WriteInitial(ProtocolSamples.Initial);
        Check.Equal(2, output.FlushCalls, "flush per record");
        byte[] run = CanonicalJson.EncodeRun(ProtocolSamples.Run);
        for (int index = 0; index < run.Length; index++)
            Check.Equal(run[index], output.Bytes[index], "run byte " + index);
        Check.Equal((byte)'\n', output.Bytes[run.Length], "run LF");
        Check.False(output.Bytes.Count >= 3
            && output.Bytes[0] == 0xef && output.Bytes[1] == 0xbb
            && output.Bytes[2] == 0xbf, "no BOM");
    }

    private static void SessionLimitIncludesLf()
    {
        byte[] run = CanonicalJson.EncodeRun(ProtocolSamples.Run);
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output, run.Length + 1L);
        sink.WriteRun(ProtocolSamples.Run);
        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "second line exceeds injected session limit");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteInitial(ProtocolSamples.Initial); },
            "failed sink rejects later record");
    }

    private static void WriteFailuresAreTerminal()
    {
        SessionLimitIncludesLf();

        FakeTraceOutput shortOutput = new FakeTraceOutput();
        shortOutput.WriteCounts.Enqueue(1);
        shortOutput.WriteCounts.Enqueue(0);
        NdjsonTraceSink shortSink = new NdjsonTraceSink(shortOutput);
        Check.Throws<TraceIoException>(
            delegate { shortSink.WriteRun(ProtocolSamples.Run); },
            "zero write progress");
        Check.Throws<TraceIoException>(
            delegate { shortSink.WriteRun(ProtocolSamples.Run); },
            "short-write failure is terminal");

        FakeTraceOutput writeOutput = new FakeTraceOutput();
        writeOutput.WriteFailure = new IOException("injected write");
        NdjsonTraceSink writeSink = new NdjsonTraceSink(writeOutput);
        Check.Throws<TraceIoException>(
            delegate { writeSink.WriteRun(ProtocolSamples.Run); }, "write failure");

        FakeTraceOutput flushOutput = new FakeTraceOutput();
        flushOutput.FlushFailure = new IOException("injected flush");
        NdjsonTraceSink flushSink = new NdjsonTraceSink(flushOutput);
        Check.Throws<TraceIoException>(
            delegate { flushSink.WriteRun(ProtocolSamples.Run); }, "flush failure");
        Check.Throws<TraceIoException>(
            delegate { flushSink.WriteRun(ProtocolSamples.Run); },
            "flush failure is terminal");
    }

    private static void CloseIsSingleUse()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        sink.Close();
        Check.Equal(1, output.CloseCalls, "one close");
        Check.Throws<InvalidOperationException>(delegate { sink.Close(); },
            "second close");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); }, "write after close");

        FakeTraceOutput failing = new FakeTraceOutput();
        failing.CloseFailure = new IOException("injected close");
        NdjsonTraceSink failingSink = new NdjsonTraceSink(failing);
        Check.Throws<TraceIoException>(delegate { failingSink.Close(); },
            "close failure typed");
        Check.Throws<InvalidOperationException>(delegate { failingSink.Close(); },
            "failed close not retried");
    }
}
