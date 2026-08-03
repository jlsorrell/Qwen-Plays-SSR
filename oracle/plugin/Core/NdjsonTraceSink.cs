using System;
using System.IO;
using System.Runtime.InteropServices;

internal interface ITraceSink
{
    void WriteRun(RunRecord record);
    void WriteInitial(InitialRecord record);
    void WriteStep(StepRecord record);
    void WriteEnd(EndRecord record);
    void WriteError(ErrorRecord record);
    void Close();
}

internal sealed class TraceIoException : Exception
{
    internal TraceIoException(string message, Exception inner)
        : base(message, inner)
    {
    }

    internal TraceIoException(string message)
        : base(message)
    {
    }
}

internal sealed class TraceExistsException : Exception
{
    internal TraceExistsException(string path, Exception inner)
        : base("trace target already exists: " + path, inner)
    {
    }
}

internal interface ITraceOutput
{
    int Write(byte[] buffer, int offset, int count);
    void Flush();
    void Close();
}

internal interface ITraceFileFactory
{
    ITraceOutput CreateNew(
        string path, FileMode mode, FileAccess access, FileShare share);
}

internal sealed class NdjsonTraceSink : ITraceSink
{
    private const long DefaultMaxTraceBytes = 128L * 1024L * 1024L;

    private enum SinkState
    {
        Open,
        Failed,
        Closing,
        Closed,
        FailedClosed
    }

    private sealed class FileTraceFactory : ITraceFileFactory
    {
        public ITraceOutput CreateNew(
            string path, FileMode mode, FileAccess access, FileShare share)
        {
            try
            {
                return new FileTraceOutput(
                    new FileStream(path, mode, access, share));
            }
            catch (IOException error)
            {
                int native = Marshal.GetHRForException(error) & 0xffff;
                if (native == 17 || native == 80 || native == 183)
                    throw new TraceExistsException(path, error);
                throw new TraceIoException("trace create-new failed", error);
            }
            catch (Exception error)
            {
                throw new TraceIoException("trace create-new failed", error);
            }
        }
    }

    private sealed class FileTraceOutput : ITraceOutput
    {
        private readonly FileStream stream;

        internal FileTraceOutput(FileStream stream)
        {
            this.stream = stream;
        }

        public int Write(byte[] buffer, int offset, int count)
        {
            stream.Write(buffer, offset, count);
            return count;
        }

        public void Flush()
        {
            stream.Flush();
        }

        public void Close()
        {
            stream.Close();
        }
    }

    private static readonly byte[] LineFeed = new byte[] { (byte)'\n' };
    private readonly ITraceOutput output;
    private readonly long maxTraceBytes;
    private SinkState state;
    private long totalBytes;

    internal NdjsonTraceSink(ITraceOutput output)
        : this(output, DefaultMaxTraceBytes)
    {
    }

    internal NdjsonTraceSink(ITraceOutput output, long maxTraceBytes)
    {
        this.output = output ?? throw new ArgumentNullException("output");
        if (maxTraceBytes <= 0L || maxTraceBytes > DefaultMaxTraceBytes)
            throw new ArgumentOutOfRangeException("maxTraceBytes");
        this.maxTraceBytes = maxTraceBytes;
        state = SinkState.Open;
    }

    internal static NdjsonTraceSink Create(
        string outputDirectory,
        string runName)
    {
        return Create(outputDirectory, runName, new FileTraceFactory());
    }

    internal static NdjsonTraceSink Create(
        string outputDirectory,
        string runName,
        ITraceFileFactory factory)
    {
        if (outputDirectory == null)
            throw new ArgumentNullException("outputDirectory");
        if (runName == null)
            throw new ArgumentNullException("runName");
        if (factory == null)
            throw new ArgumentNullException("factory");
        string path = Path.Combine(outputDirectory, runName + ".ndjson");
        ITraceOutput created = factory.CreateNew(
            path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        if (created == null)
            throw new TraceIoException("trace factory returned null");
        return new NdjsonTraceSink(created);
    }

    public void WriteRun(RunRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeRun(record));
    }

    public void WriteInitial(InitialRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeInitial(record));
    }

    public void WriteStep(StepRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeStep(record));
    }

    public void WriteEnd(EndRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeEnd(record));
    }

    public void WriteError(ErrorRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeError(record));
    }

    public void Close()
    {
        if (state != SinkState.Open && state != SinkState.Failed)
            throw new InvalidOperationException("trace close already attempted");
        bool alreadyFailed = state == SinkState.Failed;
        state = SinkState.Closing;
        try
        {
            output.Close();
        }
        catch (Exception error)
        {
            state = SinkState.FailedClosed;
            throw new TraceIoException("trace close failed", error);
        }
        state = alreadyFailed ? SinkState.FailedClosed : SinkState.Closed;
    }

    private void WriteEncoded(byte[] encoded)
    {
        CanonicalJson.ValidateRecordSize(encoded);
        long lineBytes = (long)encoded.Length + 1L;
        if (totalBytes > maxTraceBytes - lineBytes)
        {
            Fail();
            throw new TraceIoException("trace file budget exceeded");
        }
        WriteAll(encoded);
        WriteAll(LineFeed);
        try
        {
            output.Flush();
        }
        catch (Exception error)
        {
            Fail();
            throw new TraceIoException("trace flush failed", error);
        }
        totalBytes += lineBytes;
    }

    private void WriteAll(byte[] buffer)
    {
        int offset = 0;
        while (offset < buffer.Length)
        {
            int written;
            try
            {
                written = output.Write(buffer, offset, buffer.Length - offset);
            }
            catch (Exception error)
            {
                Fail();
                throw new TraceIoException("trace write failed", error);
            }
            if (written <= 0 || written > buffer.Length - offset)
            {
                Fail();
                throw new TraceIoException(
                    "trace output made invalid progress");
            }
            offset += written;
        }
    }

    private void EnsureWritable()
    {
        if (state != SinkState.Open)
            throw new TraceIoException("trace sink is not writable");
    }

    private void Fail()
    {
        state = SinkState.Failed;
    }
}
