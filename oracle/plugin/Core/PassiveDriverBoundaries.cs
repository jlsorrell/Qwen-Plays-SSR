using System;
using System.Threading;

internal enum HookKind
{
    PlayerPoll = 0,
    ProcessInput = 1,
    Undo = 2,
    Restart = 3,
    StateSet = 4
}

internal sealed class HookToken
{
    private readonly object owner;
    private int consumed;

    private HookToken(object owner, long id, HookKind kind, bool active)
    {
        this.owner = owner;
        Id = id;
        Kind = kind;
        Active = active;
    }

    internal long Id { get; private set; }
    internal HookKind Kind { get; private set; }
    internal bool Active { get; private set; }

    internal static HookToken Inert(HookKind kind)
    {
        ValidateKind(kind);
        return new HookToken(null, 0L, kind, false);
    }

    internal static HookToken Issued(
        object owner,
        long id,
        HookKind kind)
    {
        if (owner == null)
            throw new ArgumentNullException("owner");
        if (id <= 0L)
            throw new ArgumentOutOfRangeException("id");
        ValidateKind(kind);
        return new HookToken(owner, id, kind, true);
    }

    internal bool BelongsTo(object expectedOwner)
    {
        return Active && Object.ReferenceEquals(owner, expectedOwner);
    }

    internal bool TryConsume()
    {
        return Active
            && Interlocked.Exchange(ref consumed, 1) == 0;
    }

    private static void ValidateKind(HookKind kind)
    {
        switch (kind)
        {
            case HookKind.PlayerPoll:
            case HookKind.ProcessInput:
            case HookKind.Undo:
            case HookKind.Restart:
            case HookKind.StateSet:
                return;
            default:
                throw new ArgumentOutOfRangeException("kind");
        }
    }
}

internal sealed class UpdateDirective
{
    private readonly object owner;
    private int stage;

    private UpdateDirective(
        object owner,
        long id,
        long epoch,
        int settleFrames,
        double nowSeconds,
        bool active,
        bool inspectGate,
        bool timeoutAfterSample)
    {
        this.owner = owner;
        Id = id;
        Epoch = epoch;
        SettleFrames = settleFrames;
        NowSeconds = nowSeconds;
        Active = active;
        InspectGate = inspectGate;
        TimeoutAfterSample = timeoutAfterSample;
        stage = active ? 0 : 2;
    }

    internal long Id { get; private set; }
    internal long Epoch { get; private set; }
    internal int SettleFrames { get; private set; }
    internal double NowSeconds { get; private set; }
    internal bool Active { get; private set; }
    internal bool InspectGate { get; private set; }
    internal bool TimeoutAfterSample { get; private set; }

    internal static UpdateDirective Inactive(object owner)
    {
        if (owner == null)
            throw new ArgumentNullException("owner");
        return new UpdateDirective(
            owner, 0L, 0L, 0, 0.0, false, false, false);
    }

    internal static UpdateDirective Issued(
        object owner,
        long id,
        long epoch,
        int settleFrames,
        double nowSeconds,
        bool inspectGate,
        bool timeoutAfterSample)
    {
        if (owner == null)
            throw new ArgumentNullException("owner");
        if (id <= 0L)
            throw new ArgumentOutOfRangeException("id");
        if (epoch < 0L)
            throw new ArgumentOutOfRangeException("epoch");
        if (settleFrames < 0)
            throw new ArgumentOutOfRangeException("settleFrames");
        if (Double.IsNaN(nowSeconds)
            || Double.IsInfinity(nowSeconds)
            || nowSeconds < 0.0)
        {
            throw new ArgumentOutOfRangeException("nowSeconds");
        }
        return new UpdateDirective(
            owner,
            id,
            epoch,
            settleFrames,
            nowSeconds,
            true,
            inspectGate,
            timeoutAfterSample);
    }

    internal bool BelongsTo(object expectedOwner)
    {
        return Object.ReferenceEquals(owner, expectedOwner);
    }

    internal bool TryAuthorize()
    {
        return Active
            && Interlocked.CompareExchange(ref stage, 1, 0) == 0;
    }

    internal void RebaseInitialEpoch(
        long replacementEpoch,
        int replacementFrames)
    {
        if (Interlocked.CompareExchange(ref stage, 1, 1) != 1)
        {
            throw new InvalidOperationException(
                "only an authorized directive may be rebased");
        }
        if (replacementEpoch < 0L)
            throw new ArgumentOutOfRangeException("replacementEpoch");
        if (replacementFrames < 0)
            throw new ArgumentOutOfRangeException("replacementFrames");
        Epoch = replacementEpoch;
        SettleFrames = replacementFrames;
        InspectGate = false;
        TimeoutAfterSample = false;
    }

    internal bool TryComplete()
    {
        return Active
            && Interlocked.CompareExchange(ref stage, 2, 1) == 1;
    }

    internal bool TryFail()
    {
        if (!Active)
            return false;
        while (true)
        {
            int observed =
                Interlocked.CompareExchange(ref stage, 0, 0);
            if (observed == 2)
                return false;
            if (Interlocked.CompareExchange(
                ref stage, 2, observed) == observed)
            {
                return true;
            }
        }
    }
}

internal enum GateSampleKind
{
    NotInspected = 0,
    NonQuiescent = 1,
    Captured = 2
}

internal sealed class GateSample
{
    private GateSample(GateSampleKind kind, CaptureRecord capture)
    {
        Kind = kind;
        Capture = capture;
    }

    internal GateSampleKind Kind { get; private set; }
    internal CaptureRecord Capture { get; private set; }

    internal static GateSample NotInspected()
    {
        return new GateSample(GateSampleKind.NotInspected, null);
    }

    internal static GateSample NonQuiescent()
    {
        return new GateSample(GateSampleKind.NonQuiescent, null);
    }

    internal static GateSample Captured(CaptureRecord capture)
    {
        if (capture == null)
            throw new ArgumentNullException("capture");
        return new GateSample(GateSampleKind.Captured, capture);
    }
}

internal interface IPassiveReporter
{
    void Ready(int completedInputs);
    void Complete();
    void Failed(string code);
    void Diagnostic(string message);
}
internal interface IPassiveUpdateObservation
{
    bool TryGetState(out object stateReference);
    bool VerifySavePath();
    bool IsQuiescent(object stateReference);
    CaptureRecord Capture(object stateReference);
    double NowSeconds();
    DateTime UtcNow();
}

internal sealed class PassiveUpdateBoundary
{
    private readonly PassiveDriver driver;

    internal PassiveUpdateBoundary(PassiveDriver driver)
    {
        this.driver = driver
            ?? throw new ArgumentNullException("driver");
    }

    internal UpdateDirective LastDirective { get; private set; }

    internal void Observe(IPassiveUpdateObservation observation)
    {
        if (observation == null)
            throw new ArgumentNullException("observation");
        LastDirective = null;
        if (!driver.UpdateObservationActive)
            return;

        object beginState;
        bool beginUsable;
        double nowSeconds;
        try
        {
            beginUsable = observation.TryGetState(out beginState);
            nowSeconds = observation.NowSeconds();
        }
        catch (CaptureException)
        {
            driver.TryFault("capture_failed");
            return;
        }
        catch (Exception)
        {
            driver.TryFault("observer_exception");
            return;
        }

        UpdateDirective directive;
        try
        {
            directive = driver.BeginUpdate(
                beginState, beginUsable, nowSeconds);
            LastDirective = directive;
        }
        catch (CaptureException)
        {
            driver.TryFault("capture_failed");
            return;
        }
        catch (Exception)
        {
            driver.TryFault("observer_exception");
            return;
        }
        if (!directive.Active)
            return;

        bool savePathMatches;
        try
        {
            savePathMatches = observation.VerifySavePath();
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }
        if (!savePathMatches)
        {
            SafeFail(directive, "save_path_changed");
            return;
        }

        object verifiedState;
        bool verifiedUsable;
        try
        {
            verifiedUsable =
                observation.TryGetState(out verifiedState);
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }

        bool authorized;
        try
        {
            authorized = driver.AuthorizeUpdate(
                directive,
                verifiedState,
                verifiedUsable,
                savePathMatches);
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }
        if (!authorized)
            return;

        GateSample sample;
        try
        {
            if (!directive.InspectGate)
            {
                sample = GateSample.NotInspected();
            }
            else if (!observation.IsQuiescent(verifiedState))
            {
                sample = GateSample.NonQuiescent();
            }
            else
            {
                sample = GateSample.Captured(
                    observation.Capture(verifiedState));
            }
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }

        try
        {
            driver.CompleteUpdate(
                directive, sample, observation.UtcNow());
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
        }
    }

    private void SafeFail(UpdateDirective directive, string code)
    {
        try
        {
            driver.FailUpdate(directive, code);
        }
        catch (Exception)
        {
            driver.TryFault("observer_exception");
        }
    }
}
