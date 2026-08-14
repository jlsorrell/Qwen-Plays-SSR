using System;
using System.Threading;

internal sealed partial class PassiveDriver : IDisposable
{
    private const int NoTerminalOwner = 0;
    private const int FaultTerminalOwner = 1;
    private const int SuccessTerminalOwner = 2;
    private const int DisposeTerminalOwner = 3;

    private enum TerminalWorkKind
    {
        OrdinaryFault,
        TraceIoFailure,
        Dispose
    }

    private enum StepContinuation
    {
        None,
        Ready,
        Complete
    }

    private sealed class TerminalWork
    {
        internal TerminalWorkKind Kind;
        internal string Code;
        internal ErrorRecord Error;

        internal static TerminalWork Ordinary(
            string code, ErrorRecord error)
        {
            return new TerminalWork
            {
                Kind = TerminalWorkKind.OrdinaryFault,
                Code = code,
                Error = error
            };
        }

        internal static TerminalWork TraceIo()
        {
            return new TerminalWork { Kind = TerminalWorkKind.TraceIoFailure };
        }

        internal static TerminalWork DisposeOnly()
        {
            return new TerminalWork { Kind = TerminalWorkKind.Dispose };
        }
    }

    private static readonly string[] RecordErrorCodes =
        new string[]
        {
            "patch_install_failed",
            "input_before_initial",
            "overlapping_input",
            "unexpected_input",
            "unscoped_process_input",
            "hook_order_mismatch",
            "game_method_exception",
            "observer_exception",
            "capture_failed",
            "record_too_large",
            "initial_settle_timeout",
            "settle_timeout",
            "state_replaced",
            "save_path_changed"
        };

    private sealed class PlayerPollContext
    {
        internal long Id;
        internal bool SawPhysicalPoll;
        internal int RawDirection;
        internal bool SawManualProcessInput;
    }

    private struct FaultRequest
    {
        internal int? FrameOverride;
        internal bool HasOffendingInput;
        internal int OffendingIndex;
        internal OracleInput? OffendingInput;
        internal bool ForceNullInputs;

        internal static FaultRequest Derived()
        {
            return new FaultRequest();
        }

        internal static FaultRequest DerivedWithFrames(int frames)
        {
            FaultRequest value = new FaultRequest();
            value.FrameOverride = frames;
            return value;
        }

        internal static FaultRequest Offending(
            int index, OracleInput? input)
        {
            FaultRequest value = new FaultRequest();
            value.HasOffendingInput = true;
            value.OffendingIndex = index;
            value.OffendingInput = input;
            return value;
        }

        internal static FaultRequest Restart()
        {
            FaultRequest value = new FaultRequest();
            value.ForceNullInputs = true;
            return value;
        }
    }

    private readonly ITraceSink sink;
    private readonly IPassiveReporter reporter;
    private readonly int expectedInputCount;
    private readonly int maxSettleFrames;
    private readonly double maxSettleSeconds;

    private PassivePhase phase;
    private int prepareAttempted;
    private int prepared;
    private int activateAttempted;
    private int disabled;
    private int disposed;
    private int sinkCloseAttempted;
    private int terminalOwner;
    private readonly object outputLeaseSync = new object();
    private bool outputLeaseActive;
    private TerminalWork deferredTerminalWork;

    private string runId;
    private DateTime startedAtUtc;
    private long nextHookId;
    private long nextUpdateId;
    private long epoch;
    private UpdateDirective outstandingUpdate;

    private object epochState;
    private double epochStartedAt;
    private int currentFrames;
    private bool neutralSeen;
    private byte[] candidateSignature;
    private CaptureRecord lastCapture;
    private PlayerPollContext playerPoll;
    private int completedInputs;
    private object stableState;
    private bool attemptPending;
    private bool attemptOutcomeKnown;
    private OracleInput attemptInput;
    private bool attemptAccepted;
    private bool attemptMovementScheduled;
    private object attemptState;

    internal PassiveDriver(
        ITraceSink sink,
        IPassiveReporter reporter,
        int expectedInputCount,
        int maxSettleFrames,
        double maxSettleSeconds)
    {
        if (sink == null)
            throw new ArgumentNullException("sink");
        if (reporter == null)
            throw new ArgumentNullException("reporter");
        if (expectedInputCount != OracleProtocol.ExpectedInputCount)
            throw new ArgumentOutOfRangeException("expectedInputCount");
        if (maxSettleFrames < 2
            || maxSettleFrames > OracleProtocol.MaxSettleFrames)
        {
            throw new ArgumentOutOfRangeException("maxSettleFrames");
        }
        if (maxSettleSeconds <= 0.0
            || Double.IsNaN(maxSettleSeconds)
            || Double.IsInfinity(maxSettleSeconds))
        {
            throw new ArgumentOutOfRangeException("maxSettleSeconds");
        }
        this.sink = sink;
        this.reporter = reporter;
        this.expectedInputCount = expectedInputCount;
        this.maxSettleFrames = maxSettleFrames;
        this.maxSettleSeconds = maxSettleSeconds;
        phase = PassivePhase.Disabled;
    }

    internal PassivePhase Phase
    {
        get { return phase; }
    }

    internal int CurrentSettleFrames
    {
        get { return currentFrames; }
    }

    internal DateTime StartedAtUtc
    {
        get { return startedAtUtc; }
    }

    internal bool UpdateObservationActive
    {
        get { return IsObservationActive(); }
    }

    internal OracleInput PendingInput
    {
        get
        {
            if (!attemptPending)
                throw new InvalidOperationException("no pending attempt");
            return attemptInput;
        }
    }

    internal bool PendingAccepted
    {
        get
        {
            if (!attemptPending || !attemptOutcomeKnown)
                throw new InvalidOperationException("attempt outcome is pending");
            return attemptAccepted;
        }
    }

    internal bool PendingMovementScheduled
    {
        get
        {
            if (!attemptPending || !attemptOutcomeKnown)
                throw new InvalidOperationException("attempt outcome is pending");
            return attemptMovementScheduled;
        }
    }

    internal bool Prepare(RunRecord run)
    {
        if (run == null)
            throw new ArgumentNullException("run");
        if (Interlocked.CompareExchange(
            ref prepareAttempted, 1, 0) != 0)
        {
            return false;
        }
        if (Read(ref disposed) != 0 || Read(ref disabled) != 0)
            return false;
        if (!TryAcquireOutputLease())
            return false;
        bool runTraceIoFailure = false;
        bool runPrepared = false;
        try
        {
            try { sink.WriteRun(run); }
            catch (Exception error)
            {
                runTraceIoFailure = true;
                SelectTraceIoFailure();
                SafeDiagnostic(error);
                return false;
            }
            lock (outputLeaseSync)
            {
                if (TerminalSelected() || Read(ref disposed) != 0
                    || Read(ref disabled) != 0)
                    return false;
                runId = run.RunId;
                startedAtUtc = run.StartedAtUtc;
                Interlocked.Exchange(ref prepared, 1);
                runPrepared = true;
            }
            return true;
        }
        finally
        {
            ReleaseOutputLease(runTraceIoFailure);
            if (!runPrepared)
                Interlocked.Exchange(ref prepared, 0);
        }
    }

    internal bool Activate()
    {
        if (Read(ref prepared) == 0
            || Read(ref disposed) != 0
            || Read(ref disabled) != 0
            || phase != PassivePhase.Disabled
            || TerminalSelected())
        {
            return false;
        }
        if (Interlocked.CompareExchange(
            ref activateAttempted, 1, 0) != 0)
        {
            return false;
        }
        phase = PassivePhase.AwaitGame;
        return true;
    }

    internal UpdateDirective BeginUpdate(
        object stateReference,
        bool usableGame,
        double nowSeconds)
    {
        if (!IsObservationActive())
            return UpdateDirective.Inactive(this);
        if (!IsValidMonotonic(nowSeconds))
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
            return UpdateDirective.Inactive(this);
        }
        if (outstandingUpdate != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return UpdateDirective.Inactive(this);
        }
        if (phase == PassivePhase.AwaitGame && usableGame)
        {
            if (stateReference == null)
            {
                TryFaultInternal(
                    "capture_failed", FaultRequest.Derived());
                return UpdateDirective.Inactive(this);
            }
            StartInitialEpoch(stateReference, nowSeconds, false);
        }

        int settleFrames = 0;
        bool inspectGate = false;
        bool timeoutAfterSample = false;
        if (phase == PassivePhase.AwaitInitialNeutral
            || phase == PassivePhase.Settling)
        {
            string timeoutCode = phase == PassivePhase.Settling
                ? "settle_timeout" : "initial_settle_timeout";
            if (nowSeconds < epochStartedAt)
            {
                TryFaultInternal(
                    "observer_exception", FaultRequest.Derived());
                return UpdateDirective.Inactive(this);
            }
            int nextFrames = currentFrames + 1;
            double elapsed = nowSeconds - epochStartedAt;
            if (nextFrames > maxSettleFrames
                || elapsed > maxSettleSeconds)
            {
                TryFaultInternal(
                    timeoutCode,
                    FaultRequest.DerivedWithFrames(
                        Math.Min(nextFrames, maxSettleFrames)));
                return UpdateDirective.Inactive(this);
            }
            currentFrames = nextFrames;
            settleFrames = currentFrames;
            inspectGate = neutralSeen;
            timeoutAfterSample =
                currentFrames >= maxSettleFrames
                || elapsed >= maxSettleSeconds;
        }

        UpdateDirective directive =
            UpdateDirective.Issued(
                this,
                NextUpdateId(),
                epoch,
                settleFrames,
                nowSeconds,
                inspectGate,
                timeoutAfterSample);
        outstandingUpdate = directive;
        return directive;
    }

    internal bool AuthorizeUpdate(
        UpdateDirective directive,
        object stateReference,
        bool usableGame,
        bool savePathMatches)
    {
        RequireDirective(directive);
        if (!directive.TryAuthorize())
            throw new InvalidOperationException(
                "update directive was not issued");
        if (!Object.ReferenceEquals(outstandingUpdate, directive))
        {
            directive.TryComplete();
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        if (!IsObservationActive())
        {
            ConsumeAuthorizedDirective(directive);
            return false;
        }
        if (directive.Epoch != epoch)
        {
            ConsumeAuthorizedDirective(directive);
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        if (!savePathMatches)
        {
            ConsumeAuthorizedDirective(directive);
            TryFaultInternal(
                "save_path_changed", FaultRequest.Derived());
            return false;
        }

        if (phase == PassivePhase.AwaitGame)
        {
            if (usableGame)
            {
                if (stateReference == null)
                {
                    ConsumeAuthorizedDirective(directive);
                    TryFaultInternal(
                        "capture_failed", FaultRequest.Derived());
                    return false;
                }
                StartInitialEpoch(
                    stateReference, directive.NowSeconds, true);
                directive.RebaseInitialEpoch(epoch, currentFrames);
            }
            return true;
        }

        if (phase == PassivePhase.AwaitInitialNeutral)
        {
            if (!usableGame || stateReference == null)
            {
                ResetToAwaitGame();
                directive.RebaseInitialEpoch(epoch, 0);
                return true;
            }
            if (!Object.ReferenceEquals(epochState, stateReference))
            {
                StartInitialEpoch(
                    stateReference, directive.NowSeconds, true);
                directive.RebaseInitialEpoch(epoch, currentFrames);
            }
            return true;
        }

        object expectedState = phase == PassivePhase.Settling
            ? attemptState : stableState;
        if ((phase == PassivePhase.Ready || phase == PassivePhase.Settling)
            && (!usableGame || stateReference == null
                || !Object.ReferenceEquals(expectedState, stateReference)))
        {
            ConsumeAuthorizedDirective(directive);
            TryFaultInternal("state_replaced", FaultRequest.Derived());
            return false;
        }
        if (phase == PassivePhase.Ready || phase == PassivePhase.Settling)
            return true;

        ConsumeAuthorizedDirective(directive);
        return false;
    }

    internal void CompleteUpdate(
        UpdateDirective directive,
        GateSample sample,
        DateTime utcNow)
    {
        RequireDirective(directive);
        if (!directive.TryComplete())
            throw new InvalidOperationException(
                "update directive was not authorized");
        if (!Object.ReferenceEquals(outstandingUpdate, directive))
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            throw new InvalidOperationException(
                "update directive is not outstanding");
        }
        outstandingUpdate = null;
        if (!IsObservationActive())
            return;
        if (directive.Epoch != epoch)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        try
        {
            OracleValidation.Utc(utcNow, "utcNow");
            CompleteUpdateCore(directive, sample, utcNow);
        }
        catch (RecordTooLargeException)
        {
            TryFaultInternal(
                "record_too_large", FaultRequest.Derived());
        }
        catch (CanonicalEncodingException)
        {
            TryFaultInternal(
                "capture_failed", FaultRequest.Derived());
        }
        catch (TraceIoException)
        {
            SelectTraceIoFailure();
        }
        catch (Exception error)
        {
            SafeDiagnosticWithOutputLease(error);
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
        }
    }

    internal void FailUpdate(
        UpdateDirective directive,
        string code)
    {
        if (code != "capture_failed"
            && code != "observer_exception"
            && code != "save_path_changed")
        {
            throw new ArgumentException(
                "invalid update failure code", "code");
        }
        RequireDirective(directive);
        if (!directive.TryFail())
            throw new InvalidOperationException(
                "update directive was already consumed");
        if (!Object.ReferenceEquals(outstandingUpdate, directive))
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            throw new InvalidOperationException(
                "update directive is not outstanding");
        }
        outstandingUpdate = null;
        TryFaultInternal(code, FaultRequest.Derived());
    }

    internal HookToken PlayerPollEntered()
    {
        if (!IsObservationActive())
            return HookToken.Inert(HookKind.PlayerPoll);
        if (playerPoll != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.PlayerPoll);
        }
        HookToken token = NewToken(HookKind.PlayerPoll);
        playerPoll = new PlayerPollContext { Id = token.Id };
        return token;
    }

    internal void PhysicalPollReturned(int rawDirection)
    {
        if (!IsObservationActive())
            return;
        if (playerPoll == null || playerPoll.SawPhysicalPoll)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        playerPoll.SawPhysicalPoll = true;
        playerPoll.RawDirection = rawDirection;
        if (rawDirection == 8)
        {
            if (phase == PassivePhase.AwaitInitialNeutral
                || phase == PassivePhase.Settling)
                neutralSeen = true;
            return;
        }
        if (phase == PassivePhase.AwaitInitialNeutral
            || phase == PassivePhase.Settling)
        {
            neutralSeen = false;
            candidateSignature = null;
        }
        OracleInput ignored;
        if (!TryMapCardinal(rawDirection, out ignored))
            TryFaultInternal(
                "unexpected_input",
                FaultRequest.Offending(completedInputs, null));
    }

    internal void PlayerPollReturned(HookToken token)
    {
        if (!IsObservationActive())
        {
            if (ConsumeLateToken(token, HookKind.PlayerPoll)
                && playerPoll != null && playerPoll.Id == token.Id)
                playerPoll = null;
            return;
        }
        if (!ConsumeOrdinaryToken(token, HookKind.PlayerPoll))
            return;
        if (playerPoll == null || playerPoll.Id != token.Id)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        playerPoll = null;
    }

    internal void PlayerPollThrew(HookToken token)
    {
        if (!IsObservationActive())
        {
            if (ConsumeLateToken(token, HookKind.PlayerPoll)
                && playerPoll != null && playerPoll.Id == token.Id)
                playerPoll = null;
            return;
        }
        if (!ConsumeCleanupToken(token, HookKind.PlayerPoll))
            return;
        if (playerPoll == null || playerPoll.Id != token.Id)
            throw new InvalidOperationException(
                "player-poll token mismatch");
        playerPoll = null;
    }

    internal void ObserverFailed()
    {
        TryFault("observer_exception");
    }

    internal bool TryFault(string code)
    {
        if (Read(ref disposed) != 0 || Read(ref disabled) != 0)
            return false;
        return TryFaultInternal(code, FaultRequest.Derived());
    }

    internal void Disable()
    {
        Interlocked.Exchange(ref disabled, 1);
    }

    public void Dispose()
    {
        if (Interlocked.CompareExchange(ref disposed, 1, 0) != 0)
            return;
        Interlocked.Exchange(ref disabled, 1);
        TerminalWork work = null;
        bool execute = false;
        lock (outputLeaseSync)
        {
            if (Interlocked.CompareExchange(
                ref terminalOwner, DisposeTerminalOwner, NoTerminalOwner)
                == NoTerminalOwner)
            {
                work = TerminalWork.DisposeOnly();
                execute = QueueOrAcquireOutputLeaseLocked(work);
            }
        }
        if (execute)
            ExecuteTerminalWorkAndRelease(work);
    }

    private void CompleteUpdateCore(
        UpdateDirective directive,
        GateSample sample,
        DateTime utcNow)
    {
        if (sample == null)
            throw new ArgumentNullException("sample");
        if (phase == PassivePhase.AwaitGame)
        {
            if (sample.Kind != GateSampleKind.NotInspected)
                throw new InvalidOperationException(
                    "gate inspected without an active epoch");
            return;
        }
        if (phase == PassivePhase.Ready)
        {
            if (sample.Kind != GateSampleKind.NotInspected)
                throw new InvalidOperationException(
                    "gate inspected without an active epoch");
            return;
        }
        if (phase != PassivePhase.AwaitInitialNeutral
            && phase != PassivePhase.Settling)
            return;

        string timeoutCode = phase == PassivePhase.Settling
            ? "settle_timeout" : "initial_settle_timeout";

        if (sample.Kind == GateSampleKind.NotInspected)
        {
            if (directive.InspectGate)
                throw new InvalidOperationException(
                    "eligible update was not inspected");
            candidateSignature = null;
        }
        else if (sample.Kind == GateSampleKind.NonQuiescent)
        {
            if (!directive.InspectGate)
                throw new InvalidOperationException(
                    "ineligible update inspected gate");
            candidateSignature = null;
        }
        else if (sample.Kind == GateSampleKind.Captured)
        {
            if (!directive.InspectGate || sample.Capture == null)
                throw new InvalidOperationException(
                    "capture was not authorized");
            byte[] signature =
                ValidateAndRememberCapture(sample.Capture);
            if (candidateSignature != null
                && SameBytes(candidateSignature, signature))
            {
                if (phase == PassivePhase.Settling)
                {
                    EmitSettledAttempt(
                        sample.Capture, directive.SettleFrames, utcNow);
                }
                else
                {
                    EmitInitial(sample.Capture);
                }
                return;
            }
            candidateSignature = signature;
        }
        else
        {
            throw new InvalidOperationException("unknown gate sample");
        }

        if (directive.TimeoutAfterSample)
        {
            TryFaultInternal(
                timeoutCode,
                FaultRequest.Derived());
        }
    }

    private byte[] ValidateAndRememberCapture(CaptureRecord capture)
    {
        for (int index = 0; index < RecordErrorCodes.Length; index++)
        {
            CanonicalJson.EncodeError(
                new ErrorRecord(
                    runId,
                    Int32.MaxValue,
                    OracleInput.North,
                    RecordErrorCodes[index],
                    OracleProtocol.MaxSettleFrames,
                    capture));
        }
        byte[] signature = CaptureSignature.Compute(capture);
        lastCapture = capture;
        return signature;
    }

    private void EmitInitial(CaptureRecord capture)
    {
        if (!TryAcquireOutputLease())
        {
            ClearInitialAfterTerminalReturn();
            return;
        }
        bool traceIoFailure = false;
        try
        {
            try { sink.WriteInitial(new InitialRecord(runId, capture)); }
            catch (Exception error)
            {
                traceIoFailure = true;
                SelectTraceIoFailure();
                SafeDiagnostic(error);
                return;
            }
            bool reportReady;
            lock (outputLeaseSync)
            {
                reportReady = !TerminalSelected()
                    && Read(ref disposed) == 0 && Read(ref disabled) == 0;
                if (reportReady)
                {
                    stableState = epochState;
                    phase = PassivePhase.Ready;
                }
                epochState = null;
                currentFrames = 0;
                neutralSeen = false;
                candidateSignature = null;
                lastCapture = null;
            }
            if (reportReady)
            {
                try { reporter.Ready(0); }
                catch (Exception)
                {
                    TryFaultInternal(
                        "observer_exception", FaultRequest.Derived());
                }
            }
        }
        finally
        {
            ReleaseOutputLease(traceIoFailure);
        }
    }

    private void StartInitialEpoch(
        object stateReference,
        double nowSeconds,
        bool countCurrentUpdate)
    {
        epoch++;
        phase = PassivePhase.AwaitInitialNeutral;
        epochState = stateReference;
        epochStartedAt = nowSeconds;
        currentFrames = countCurrentUpdate ? 1 : 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
    }

    private void ResetToAwaitGame()
    {
        epoch++;
        phase = PassivePhase.AwaitGame;
        epochState = null;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
    }

    private void ConsumeAuthorizedDirective(UpdateDirective directive)
    {
        if (!directive.TryComplete())
            throw new InvalidOperationException(
                "authorized update could not be consumed");
        outstandingUpdate = null;
    }

    private void RequireDirective(UpdateDirective directive)
    {
        if (directive == null)
            throw new ArgumentNullException("directive");
        if (!directive.Active || !directive.BelongsTo(this))
            throw new InvalidOperationException(
                "foreign or inactive update directive");
    }

    private HookToken NewToken(HookKind kind)
    {
        if (nextHookId == Int64.MaxValue)
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
            return HookToken.Inert(kind);
        }
        nextHookId++;
        return HookToken.Issued(this, nextHookId, kind);
    }

    private long NextUpdateId()
    {
        if (nextUpdateId == Int64.MaxValue)
            throw new InvalidOperationException(
                "update token exhaustion");
        nextUpdateId++;
        return nextUpdateId;
    }

    private bool ConsumeOrdinaryToken(
        HookToken token,
        HookKind expectedKind)
    {
        if (token == null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        if (!token.Active)
            return false;
        if (!token.BelongsTo(this)
            || token.Kind != expectedKind
            || !token.TryConsume())
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        return true;
    }

    private bool ConsumeCleanupToken(
        HookToken token,
        HookKind expectedKind)
    {
        if (token == null || !token.Active)
            return false;
        if (!token.BelongsTo(this) || token.Kind != expectedKind)
            throw new InvalidOperationException("foreign cleanup token");
        return token.TryConsume();
    }

    private bool ConsumeLateToken(
        HookToken token,
        HookKind expectedKind)
    {
        if (token == null || !token.Active)
            return false;
        return token.BelongsTo(this)
            && token.Kind == expectedKind
            && token.TryConsume();
    }

    private bool TryFaultInternal(
        string code,
        FaultRequest request)
    {
        OracleErrors.ForCode(code);
        TerminalWork work;
        bool execute;
        lock (outputLeaseSync)
        {
            if (Interlocked.CompareExchange(
                ref terminalOwner, FaultTerminalOwner, NoTerminalOwner)
                != NoTerminalOwner)
                return false;
            PassivePhase faultPhase = phase;
            phase = PassivePhase.Faulted;
            work = Read(ref prepared) == 0
                ? TerminalWork.TraceIo()
                : TerminalWork.Ordinary(
                    code, BuildErrorRecord(code, request, faultPhase));
            execute = QueueOrAcquireOutputLeaseLocked(work);
        }
        if (execute)
            ExecuteTerminalWorkAndRelease(work);
        return true;
    }

    private ErrorRecord BuildErrorRecord(
        string code,
        FaultRequest request,
        PassivePhase faultPhase)
    {
        int activeFrames = (faultPhase == PassivePhase.AwaitInitialNeutral
            || faultPhase == PassivePhase.Settling) ? currentFrames : 0;
        int frames;
        int? inputIndex = null;
        OracleInput? input = null;
        if (request.ForceNullInputs)
        {
            frames = request.FrameOverride.HasValue
                ? request.FrameOverride.Value : activeFrames;
        }
        else if (attemptPending)
        {
            frames = request.FrameOverride.HasValue
                ? request.FrameOverride.Value : activeFrames;
            inputIndex = completedInputs;
            input = attemptInput;
        }
        else if (request.HasOffendingInput)
        {
            frames = request.FrameOverride.HasValue
                ? request.FrameOverride.Value : 0;
            inputIndex = request.OffendingIndex;
            input = request.OffendingInput;
        }
        else
        {
            frames = request.FrameOverride.HasValue
                ? request.FrameOverride.Value : activeFrames;
        }
        return new ErrorRecord(
            runId,
            inputIndex,
            input,
            code,
            frames,
            lastCapture);
    }

    private void SelectTraceIoFailure()
    {
        TerminalWork work = null;
        bool execute = false;
        lock (outputLeaseSync)
        {
            if (Interlocked.CompareExchange(
                ref terminalOwner, FaultTerminalOwner, NoTerminalOwner)
                == NoTerminalOwner)
            {
                phase = PassivePhase.Faulted;
                work = TerminalWork.TraceIo();
                execute = QueueOrAcquireOutputLeaseLocked(work);
            }
        }
        if (execute)
            ExecuteTerminalWorkAndRelease(work);
    }

    private void CloseSink()
    {
        if (Interlocked.CompareExchange(
            ref sinkCloseAttempted, 1, 0) != 0)
        {
            throw new InvalidOperationException(
                "sink close already attempted");
        }
        sink.Close();
    }

    private void BestEffortClose()
    {
        if (Read(ref sinkCloseAttempted) != 0)
            return;
        try
        {
            CloseSink();
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeFailed(string code)
    {
        try
        {
            reporter.Failed(code);
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeDiagnostic(Exception error)
    {
        try
        {
            reporter.Diagnostic(
                error == null
                ? "unknown"
                : error.GetType().FullName);
        }
        catch (Exception)
        {
        }
    }

    private bool IsObservationActive()
    {
        return Read(ref prepared) != 0 && Read(ref disabled) == 0
            && Read(ref disposed) == 0
            && !TerminalSelected()
            && (phase == PassivePhase.AwaitGame
                || phase == PassivePhase.AwaitInitialNeutral
                || phase == PassivePhase.Ready
                || phase == PassivePhase.Settling);
    }

    private bool TerminalSelected()
    {
        return Read(ref terminalOwner) != 0;
    }

    private static int Read(ref int value)
    {
        return Interlocked.CompareExchange(ref value, 0, 0);
    }

    private static bool IsValidMonotonic(double value)
    {
        return value >= 0.0
            && !Double.IsNaN(value)
            && !Double.IsInfinity(value);
    }

    private static bool SameBytes(byte[] left, byte[] right)
    {
        if (left == null
            || right == null
            || left.Length != right.Length)
        {
            return false;
        }
        for (int index = 0; index < left.Length; index++)
        {
            if (left[index] != right[index])
                return false;
        }
        return true;
    }
}
