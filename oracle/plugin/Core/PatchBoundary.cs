using System;

internal static class PatchBoundary
{
    internal static void Observe(Action callback, Action observerFailed)
    {
        try
        {
            if (callback == null) throw new ArgumentNullException("callback");
            callback();
        }
        catch (Exception) { Try(observerFailed); }
    }

    internal static Exception Finalize(
        HookToken token, Exception original, Action<HookToken> clear,
        Action gameMethodFailed, Action observerFailed)
    {
        bool observerWorkFailed = false;
        if (original != null)
        {
            try
            {
                if (gameMethodFailed == null)
                    throw new ArgumentNullException("gameMethodFailed");
                gameMethodFailed();
            }
            catch (Exception) { observerWorkFailed = true; }
        }
        if (token != null && token.Active)
        {
            try
            {
                if (clear == null) throw new ArgumentNullException("clear");
                clear(token);
            }
            catch (Exception) { observerWorkFailed = true; }
        }
        if (observerWorkFailed) Try(observerFailed);
        return original;
    }

    internal static Exception FinalizeUpdate(
        Exception original, Action gameMethodFailed, Action observerFailed)
    {
        if (original != null)
        {
            try
            {
                if (gameMethodFailed == null)
                    throw new ArgumentNullException("gameMethodFailed");
                gameMethodFailed();
            }
            catch (Exception) { Try(observerFailed); }
        }
        return original;
    }

    private static void Try(Action callback)
    {
        try { if (callback != null) callback(); }
        catch (Exception) { }
    }
}
