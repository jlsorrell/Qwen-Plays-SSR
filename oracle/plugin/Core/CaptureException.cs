using System;

internal sealed class CaptureException : Exception
{
    internal CaptureException(string message)
        : base(message)
    {
    }

    internal CaptureException(string message, Exception inner)
        : base(message, inner)
    {
    }
}
