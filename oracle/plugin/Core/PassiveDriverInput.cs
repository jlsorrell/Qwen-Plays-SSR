using System;

internal sealed partial class PassiveDriver
{
    private sealed class ProcessInputContext
    {
        internal long Id;
    }

    private sealed class UndoContext
    {
        internal long Id;
        internal bool RestoreSeen;
    }

    private ProcessInputContext processInputContext;
    private UndoContext undoContext;

    internal HookToken ProcessInputEntered(
        object stateReference, int rawDirection, double nowSeconds)
    {
        if (!IsObservationActive())
            return HookToken.Inert(HookKind.ProcessInput);
        if (playerPoll == null)
        {
            if (phase == PassivePhase.Ready)
                TryFaultInternal(
                    "unscoped_process_input", FaultRequest.Derived());
            return HookToken.Inert(HookKind.ProcessInput);
        }
        if (!playerPoll.SawPhysicalPoll || playerPoll.SawManualProcessInput)
        {
            TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.ProcessInput);
        }
        playerPoll.SawManualProcessInput = true;
        OracleInput input;
        if (!TryMapCardinal(playerPoll.RawDirection, out input))
        {
            TryFaultInternal(
                "unexpected_input",
                FaultRequest.Offending(completedInputs, null));
            return HookToken.Inert(HookKind.ProcessInput);
        }
        if (playerPoll.RawDirection != rawDirection)
        {
            TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.ProcessInput);
        }
        HookToken token = NewToken(HookKind.ProcessInput);
        if (!token.Active)
            return token;
        processInputContext = new ProcessInputContext { Id = token.Id };
        HandleManualAttempt(input, stateReference, nowSeconds);
        return token;
    }

    internal void ProcessInputReturned(
        HookToken token, bool accepted, bool movementScheduled)
    {
        if (!IsObservationActive())
        {
            if (ConsumeLateToken(token, HookKind.ProcessInput)
                && processInputContext != null
                && processInputContext.Id == token.Id)
                processInputContext = null;
            return;
        }
        if (!ConsumeOrdinaryToken(token, HookKind.ProcessInput))
            return;
        if (processInputContext == null
            || processInputContext.Id != token.Id)
        {
            TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        processInputContext = null;
        if (restartDepth > 0 || !attemptPending)
            return;
        attemptAccepted = accepted;
        attemptMovementScheduled = movementScheduled;
        attemptOutcomeKnown = true;
    }

    internal void ProcessInputThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(token, HookKind.ProcessInput))
            return;
        if (processInputContext == null
            || processInputContext.Id != token.Id)
        {
            throw new InvalidOperationException(
                "ProcessInput token mismatch");
        }
        processInputContext = null;
    }

    internal HookToken UndoEntered(object stateReference, double nowSeconds)
    {
        bool suppressed = restartDepth > 0;
        if (!suppressed && !IsObservationActive())
            return HookToken.Inert(HookKind.Undo);
        if (undoContext != null)
        {
            TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.Undo);
        }
        HookToken token = NewToken(HookKind.Undo);
        if (!token.Active)
            return token;
        undoContext = new UndoContext { Id = token.Id };
        if (!suppressed)
            HandleManualAttempt(OracleInput.Undo, stateReference, nowSeconds);
        return token;
    }

    internal void RestoreObserved()
    {
        if (restartDepth > 0)
            return;
        if (!IsObservationActive())
            return;
        if (undoContext == null || undoContext.RestoreSeen)
        {
            TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        undoContext.RestoreSeen = true;
    }

    internal void UndoReturned(HookToken token, bool movementScheduled)
    {
        if (!IsObservationActive())
        {
            if (ConsumeLateToken(token, HookKind.Undo)
                && undoContext != null && undoContext.Id == token.Id)
                undoContext = null;
            return;
        }
        if (!ConsumeOrdinaryToken(token, HookKind.Undo))
            return;
        if (undoContext == null || undoContext.Id != token.Id)
        {
            TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        bool accepted = undoContext.RestoreSeen;
        undoContext = null;
        if (restartDepth > 0 || !attemptPending)
            return;
        attemptAccepted = accepted;
        attemptMovementScheduled = movementScheduled;
        attemptOutcomeKnown = true;
    }

    internal void UndoThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(token, HookKind.Undo))
            return;
        if (undoContext == null || undoContext.Id != token.Id)
            throw new InvalidOperationException("Undo token mismatch");
        undoContext = null;
    }

    private bool HandleManualAttempt(
        OracleInput input,
        object stateReference,
        double nowSeconds)
    {
        if (phase == PassivePhase.AwaitGame
            || phase == PassivePhase.AwaitInitialNeutral)
        {
            TryFaultInternal(
                "input_before_initial",
                FaultRequest.Offending(completedInputs, input));
            return false;
        }
        if (attemptPending || phase == PassivePhase.Settling)
        {
            TryFaultInternal("overlapping_input", FaultRequest.Derived());
            return false;
        }
        if (phase != PassivePhase.Ready)
            return false;
        if (!IsValidMonotonic(nowSeconds))
        {
            TryFaultInternal(
                "observer_exception",
                FaultRequest.Offending(completedInputs, input));
            return false;
        }
        if (stateReference == null
            || !Object.ReferenceEquals(stableState, stateReference))
        {
            TryFaultInternal(
                "state_replaced",
                FaultRequest.Offending(completedInputs, input));
            return false;
        }
        attemptPending = true;
        attemptOutcomeKnown = false;
        attemptInput = input;
        attemptState = stateReference;
        epoch++;
        phase = PassivePhase.Settling;
        epochState = stateReference;
        epochStartedAt = nowSeconds;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
        return true;
    }

    private static bool TryMapCardinal(
        int rawDirection,
        out OracleInput input)
    {
        switch (rawDirection)
        {
            case 0: input = OracleInput.North; return true;
            case 1: input = OracleInput.South; return true;
            case 2: input = OracleInput.West; return true;
            case 3: input = OracleInput.East; return true;
            default: input = OracleInput.North; return false;
        }
    }

    private void EmitSettledAttempt(
        CaptureRecord capture,
        int settleFrames)
    {
        if (!attemptPending || !attemptOutcomeKnown)
            throw new InvalidOperationException(
                "settled attempt lacks outcome");
        sink.WriteStep(new StepRecord(
            runId, completedInputs, attemptInput, attemptAccepted,
            attemptMovementScheduled, settleFrames, false, capture));
        stableState = attemptState;
        attemptPending = false;
        attemptOutcomeKnown = false;
        attemptState = null;
        candidateSignature = null;
        lastCapture = null;
        currentFrames = 0;
        completedInputs++;
        phase = PassivePhase.Ready;
        try
        {
            reporter.Ready(completedInputs);
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
            TryFaultInternal("observer_exception", FaultRequest.Derived());
        }
    }
}
