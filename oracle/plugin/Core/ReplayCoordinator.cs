using System;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

internal interface IReplayUpdateAccess
{
    bool TryGetState(object game, out object stateReference);
    bool VerifySavePath();
    bool IsQuiescent(object game, object stateReference);
    void InvokeUndo(object game);
}

internal sealed class ReplayCoordinator : IPassiveReporter, IDisposable
{
    private const int ActiveState = 0;
    private const int StoppedState = 1;
    private const int DiagnosticForwardingState = 2;

    private static readonly UTF8Encoding StrictUtf8 =
        new UTF8Encoding(false, true);
    private readonly ReplayInput input;
    private readonly string expectedInitialSha256;
    private readonly IPassiveReporter downstream;
    private IReplayDriver driver;
    private CaptureRecord lastCapture;
    private bool initialReady;
    private bool initialNeutralProven;
    private bool ready;
    private bool neutralSinceStep;
    private bool updateActive;
    private bool awaitingDurableStep;
    private object updateClaim;
    private int tokenIndex;
    private OracleInput armedInput;
    private object armedState;
    private bool overrideIssued;
    private bool physicalReturned;
    private int processCalls;
    private int undoCalls;
    private bool undoReturned;
    private bool restoreObserved;
    private int stopped;

    internal ReplayCoordinator(ReplayInput input,
        string expectedInitialSha256, IPassiveReporter downstream)
    {
        this.input = input ?? throw new ArgumentNullException("input");
        this.expectedInitialSha256 = expectedInitialSha256
            ?? throw new ArgumentNullException("expectedInitialSha256");
        this.downstream = downstream
            ?? throw new ArgumentNullException("downstream");
    }

    internal void AttachDriver(IReplayDriver value)
    {
        if (value == null) throw new ArgumentNullException("value");
        if (Interlocked.CompareExchange(ref driver, value, null) != null)
            throw new InvalidOperationException(
                "replay driver already attached");
    }

    internal void CaptureObserved(CaptureRecord capture)
    {
        if (Stopped) return;
        lastCapture = capture ?? throw new ArgumentNullException("capture");
        if (!initialReady && neutralSinceStep)
            initialNeutralProven = true;
    }

    internal void UpdateEntered(object game, IReplayUpdateAccess access)
    {
        if (Stopped || !ready || !neutralSinceStep || updateActive
            || awaitingDurableStep || tokenIndex >= input.Count)
        {
            return;
        }
        object claim = TryClaimUpdate();
        if (claim == null) return;
        if (access == null)
        {
            ReleaseUpdateClaim(claim);
            throw new ArgumentNullException("access");
        }
        if (!CanContinueUpdate(claim)) return;

        object state;
        bool stateAvailable;
        try
        {
            stateAvailable = access.TryGetState(game, out state);
        }
        catch (CaptureException)
        {
            FaultIfClaimOwned(claim, "capture_failed");
            return;
        }
        catch (Exception)
        {
            FaultIfClaimOwned(claim, "observer_exception");
            return;
        }
        if (!CanContinueUpdate(claim)) return;
        if (!stateAvailable || state == null)
        {
            ReleaseUpdateClaim(claim);
            return;
        }

        bool savePathMatches;
        try
        {
            savePathMatches = access.VerifySavePath();
        }
        catch (CaptureException)
        {
            FaultIfClaimOwned(claim, "capture_failed");
            return;
        }
        catch (Exception)
        {
            FaultIfClaimOwned(claim, "observer_exception");
            return;
        }
        if (!CanContinueUpdate(claim)) return;
        if (!savePathMatches)
        {
            FaultIfClaimOwned(claim, "save_path_changed");
            return;
        }

        bool quiescent;
        try
        {
            quiescent = access.IsQuiescent(game, state);
        }
        catch (CaptureException)
        {
            FaultIfClaimOwned(claim, "capture_failed");
            return;
        }
        catch (Exception)
        {
            FaultIfClaimOwned(claim, "observer_exception");
            return;
        }
        if (!CanContinueUpdate(claim)) return;
        if (!quiescent)
        {
            ReleaseUpdateClaim(claim);
            return;
        }

        IReplayDriver value;
        bool driverReady;
        try
        {
            value = RequireDriver();
            driverReady = value.IsReadyForReplay(state, tokenIndex);
        }
        catch
        {
            ReleaseUpdateClaim(claim);
            throw;
        }
        if (!CanContinueUpdate(claim)) return;
        if (!driverReady)
        {
            ReleaseUpdateClaim(claim);
            return;
        }
        if (!CanContinueUpdate(claim)) return;

        armedInput = input[tokenIndex];
        armedState = state;
        ready = false;
        neutralSinceStep = false;
        overrideIssued = false;
        physicalReturned = false;
        processCalls = 0;
        undoCalls = 0;
        undoReturned = false;
        restoreObserved = false;
        updateActive = true;
        if (!CanContinueUpdate(claim))
        {
            ClearActiveUpdate();
            return;
        }
        if (armedInput == OracleInput.Undo)
        {
            try
            {
                access.InvokeUndo(game);
            }
            catch
            {
                ClearActiveUpdate();
                throw;
            }
            if (!CanContinueUpdate(claim)) return;
        }
    }

    internal bool TryOverridePlayerInput(out int rawDirection)
    {
        rawDirection = 8;
        if (Stopped) return true;
        if (!updateActive || armedInput == OracleInput.Undo) return true;
        if (overrideIssued)
        {
            Fault("replay_alignment_failed");
            return true;
        }
        overrideIssued = true;
        rawDirection = (int)armedInput;
        return true;
    }

    internal void PhysicalPollReturned(int rawDirection)
    {
        if (Stopped) return;
        if (!updateActive)
        {
            if (rawDirection == 8)
                neutralSinceStep = true;
            else
                Fault("replay_alignment_failed");
            return;
        }
        if (armedInput == OracleInput.Undo)
        {
            if (rawDirection != 8) Fault("replay_alignment_failed");
            return;
        }
        if (!overrideIssued || physicalReturned
            || rawDirection != (int)armedInput)
        {
            Fault("replay_alignment_failed");
            return;
        }
        physicalReturned = true;
    }

    internal void ProcessInputEntered(
        object stateReference, int rawDirection)
    {
        if (Stopped) return;
        if (!updateActive || armedInput == OracleInput.Undo
            || !physicalReturned || processCalls != 0
            || rawDirection != (int)armedInput
            || !Object.ReferenceEquals(armedState, stateReference))
        {
            Fault("replay_alignment_failed");
            return;
        }
        processCalls++;
    }

    internal void UndoEntered()
    {
        if (Stopped) return;
        if (!updateActive || armedInput != OracleInput.Undo || undoCalls != 0)
        {
            Fault("replay_alignment_failed");
            return;
        }
        undoCalls++;
    }

    internal void UndoReturned()
    {
        if (Stopped) return;
        if (!updateActive || armedInput != OracleInput.Undo
            || undoCalls != 1 || undoReturned)
        {
            Fault("replay_alignment_failed");
            return;
        }
        undoReturned = true;
    }

    internal void RestoreObserved()
    {
        if (Stopped) return;
        if (!updateActive || armedInput != OracleInput.Undo
            || undoCalls != 1 || undoReturned || restoreObserved)
        {
            Fault("replay_alignment_failed");
            return;
        }
        restoreObserved = true;
    }

    internal void UpdateReturned()
    {
        if (Stopped || !updateActive) return;
        bool aligned = armedInput == OracleInput.Undo
            ? undoCalls == 1 && restoreObserved && undoReturned
            : overrideIssued && physicalReturned && processCalls == 1;
        ClearActiveUpdate();
        if (!aligned)
        {
            Fault("replay_alignment_failed");
            return;
        }
        awaitingDurableStep = true;
    }

    internal void UpdateThrew()
    {
        ClearActiveUpdate();
    }

    public void Ready(int completedInputs)
    {
        if (Stopped) return;
        if (!initialReady)
        {
            if (completedInputs != 0 || lastCapture == null
                || !initialNeutralProven)
            {
                Fault("replay_alignment_failed");
                return;
            }
            initialReady = true;
            if (expectedInitialSha256.Length != 0
                && HashRawSave(lastCapture.RawSave)
                    != expectedInitialSha256)
            {
                Fault("initial_state_mismatch");
                return;
            }
            tokenIndex = 0;
            ready = true;
            neutralSinceStep = true;
            downstream.Ready(0);
            return;
        }
        if (!awaitingDurableStep || completedInputs != tokenIndex + 1
            || completedInputs >= input.Count)
        {
            Fault("replay_alignment_failed");
            return;
        }
        tokenIndex = completedInputs;
        awaitingDurableStep = false;
        ready = true;
        neutralSinceStep = false;
        downstream.Ready(completedInputs);
    }

    public void Complete()
    {
        if (Stopped) return;
        if (!initialReady || !awaitingDurableStep
            || tokenIndex != input.Count - 1)
        {
            Fault("replay_alignment_failed");
            return;
        }
        Stop();
        downstream.Complete();
    }

    public void Failed(string code)
    {
        if (Interlocked.Exchange(ref stopped, StoppedState)
            == StoppedState)
        {
            return;
        }
        ClearStoppedState();
        downstream.Failed(code);
    }

    public void Diagnostic(string message)
    {
        if (Interlocked.CompareExchange(
            ref stopped, DiagnosticForwardingState, ActiveState)
            != ActiveState)
        {
            return;
        }
        try
        {
            downstream.Diagnostic(message);
        }
        finally
        {
            Interlocked.CompareExchange(
                ref stopped, ActiveState, DiagnosticForwardingState);
        }
    }

    public void Dispose()
    {
        if (Interlocked.CompareExchange(
            ref stopped, StoppedState, ActiveState) != ActiveState)
        {
            return;
        }
        ClearStoppedState();
    }

    private bool Stopped
    {
        get
        {
            return Interlocked.CompareExchange(
                ref stopped, ActiveState, ActiveState) == StoppedState;
        }
    }

    private IReplayDriver RequireDriver()
    {
        IReplayDriver value =
            Interlocked.CompareExchange(ref driver, null, null);
        if (value == null)
            throw new InvalidOperationException(
                "replay driver is not attached");
        return value;
    }

    private void Fault(string code)
    {
        ready = false;
        ClearActiveUpdate();
        IReplayDriver value = RequireDriver();
        if (!value.TryFault(code)) Stop();
    }

    private void Stop()
    {
        Interlocked.Exchange(ref stopped, StoppedState);
        ClearStoppedState();
    }

    private void ClearStoppedState()
    {
        ready = false;
        awaitingDurableStep = false;
        ClearActiveUpdate();
    }

    private void ClearActiveUpdate()
    {
        updateActive = false;
        armedState = null;
        overrideIssued = false;
        physicalReturned = false;
        processCalls = 0;
        undoCalls = 0;
        undoReturned = false;
        restoreObserved = false;
        Interlocked.Exchange(ref updateClaim, null);
    }

    private object TryClaimUpdate()
    {
        object claim = new object();
        return Interlocked.CompareExchange(
            ref updateClaim, claim, null) == null ? claim : null;
    }

    private bool CanContinueUpdate(object claim)
    {
        if (Stopped)
        {
            ReleaseUpdateClaim(claim);
            return false;
        }
        return Object.ReferenceEquals(
            Interlocked.CompareExchange(ref updateClaim, null, null), claim);
    }

    private void FaultIfClaimOwned(object claim, string code)
    {
        if (CanContinueUpdate(claim))
            Fault(code);
    }

    private void ReleaseUpdateClaim(object claim)
    {
        if (claim == null) return;
        Interlocked.CompareExchange(ref updateClaim, null, claim);
    }

    private static string HashRawSave(string value)
    {
        if (value == null) throw new ArgumentNullException("value");
        byte[] digest;
        using (SHA256 hash = SHA256.Create())
            digest = hash.ComputeHash(StrictUtf8.GetBytes(value));
        StringBuilder text = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
        {
            text.Append(digest[index].ToString(
                "x2", CultureInfo.InvariantCulture));
        }
        return text.ToString();
    }
}
