using System;
using System.Collections.Generic;

internal static class PatchBoundaryTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("boundary", "postfix contains observer failures",
            ObserveContainsFailures);
        tests.Add("boundary", "game exception claims before cleanup",
            GameFailurePrecedesCleanup);
        tests.Add("boundary", "successful postfix makes finalizer cleanup inert",
            ConsumedTokenIsInert);
        tests.Add("boundary", "cleanup failure is contained and reported",
            CleanupFailureIsContained);
        tests.Add("boundary", "update finalizer preserves original reference",
            UpdateFinalizerPreservesOriginalException);
    }

    private static void ObserveContainsFailures()
    {
        int failures = 0;
        PatchBoundary.Observe(delegate { throw new InvalidOperationException("observer"); },
            delegate { failures++; throw new InvalidOperationException("reporter"); });
        Check.Equal(1, failures, "observer failure reported once");
    }

    private static void GameFailurePrecedesCleanup()
    {
        List<string> events = new List<string>();
        HookToken token = HookToken.Issued(new object(), 1L, HookKind.PlayerPoll);
        Exception original = new InvalidOperationException("game");
        Exception returned = PatchBoundary.Finalize(
            token, original,
            delegate(HookToken value) { events.Add("clear"); value.TryConsume(); },
            delegate { events.Add("game"); },
            delegate { events.Add("observer"); });
        Check.Same(original, returned, "original identity");
        Check.Sequence(new string[] { "game", "clear" }, events.ToArray(),
            "game failure owns before cleanup");
    }

    private static void ConsumedTokenIsInert()
    {
        HookToken token = HookToken.Issued(new object(), 1L, HookKind.PlayerPoll);
        Check.True(token.TryConsume(), "test token consumed");
        int clears = 0;
        PatchBoundary.Finalize(token, null,
            delegate(HookToken value) { if (value.TryConsume()) clears++; },
            delegate { throw new InvalidOperationException("not called"); },
            delegate { throw new InvalidOperationException("not called"); });
        Check.Equal(0, clears, "consumed token clears zero times");
    }

    private static void CleanupFailureIsContained()
    {
        HookToken token = HookToken.Issued(new object(), 1L, HookKind.PlayerPoll);
        int failures = 0;
        Exception original = new InvalidOperationException("game");
        Exception returned = PatchBoundary.Finalize(token, original,
            delegate(HookToken value) { throw new InvalidOperationException("clear"); },
            delegate { }, delegate { failures++; });
        Check.Same(original, returned, "cleanup keeps game exception");
        Check.Equal(1, failures, "cleanup failure reported once");
    }

    private static void UpdateFinalizerPreservesOriginalException()
    {
        int calls = 0;
        Check.Equal<Exception>(null, PatchBoundary.FinalizeUpdate(null,
            delegate { calls++; }, delegate { calls++; }), "null update inert");
        Check.Equal(0, calls, "null update calls nothing");
        Exception original = new InvalidOperationException("update");
        Exception returned = PatchBoundary.FinalizeUpdate(original,
            delegate { calls++; }, delegate { calls++; });
        Check.Same(original, returned, "update original identity");
        Check.Equal(1, calls, "game observer only");
    }
}
