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

    private readonly ITraceOutput output;
    private bool closeAttempted;

    internal NdjsonTraceSink(ITraceOutput output)
        : this(output, 128L * 1024L * 1024L)
    {
    }

    internal NdjsonTraceSink(ITraceOutput output, long maxTraceBytes)
    {
        if (output == null)
            throw new ArgumentNullException("output");
        if (maxTraceBytes <= 0L || maxTraceBytes > 128L * 1024L * 1024L)
            throw new ArgumentOutOfRangeException("maxTraceBytes");
        this.output = output;
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
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteInitial(InitialRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteStep(StepRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteEnd(EndRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteError(ErrorRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void Close()
    {
        if (closeAttempted)
            throw new InvalidOperationException("trace close already attempted");
        closeAttempted = true;
        try
        {
            output.Close();
        }
        catch (Exception error)
        {
            throw new TraceIoException("trace close failed", error);
        }
    }
}
