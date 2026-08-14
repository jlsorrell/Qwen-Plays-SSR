using System;
using System.Threading;

internal sealed partial class PassiveDriver
{
    private bool TryAcquireOutputLease()
    {
        lock (outputLeaseSync)
        {
            if (TerminalSelected() || Read(ref disposed) != 0
                || Read(ref disabled) != 0)
                return false;
            if (outputLeaseActive)
                throw new InvalidOperationException("output lease already active");
            outputLeaseActive = true;
            return true;
        }
    }

    private void SafeDiagnosticWithOutputLease(Exception error)
    {
        if (!TryAcquireOutputLease())
            return;
        try
        {
            SafeDiagnostic(error);
        }
        finally
        {
            ReleaseOutputLease(false);
        }
    }

    private bool QueueOrAcquireOutputLeaseLocked(TerminalWork work)
    {
        if (work == null)
            throw new ArgumentNullException("work");
        if (outputLeaseActive)
        {
            if (deferredTerminalWork != null)
                throw new InvalidOperationException("terminal work already queued");
            deferredTerminalWork = work;
            return false;
        }
        outputLeaseActive = true;
        return true;
    }

    private void ReleaseOutputLease(bool traceIoFailure)
    {
        TerminalWork next = null;
        lock (outputLeaseSync)
        {
            if (!outputLeaseActive)
                throw new InvalidOperationException("output lease is not active");
            if (traceIoFailure && deferredTerminalWork != null
                && deferredTerminalWork.Kind == TerminalWorkKind.OrdinaryFault)
                deferredTerminalWork = TerminalWork.TraceIo();
            if (deferredTerminalWork == null)
                outputLeaseActive = false;
            else
            {
                next = deferredTerminalWork;
                deferredTerminalWork = null;
            }
        }
        if (next != null)
            ExecuteTerminalWorkAndRelease(next);
    }

    private void ExecuteTerminalWorkAndRelease(TerminalWork work)
    {
        try
        {
            if (work.Kind == TerminalWorkKind.OrdinaryFault)
            {
                bool durable = false;
                try
                {
                    sink.WriteError(work.Error);
                    CloseSink();
                    durable = true;
                }
                catch (Exception error)
                {
                    SafeDiagnostic(error);
                    BestEffortClose();
                }
                SafeFailed(durable ? work.Code : "trace_io_failed");
            }
            else if (work.Kind == TerminalWorkKind.TraceIoFailure)
            {
                phase = PassivePhase.Faulted;
                BestEffortClose();
                SafeFailed("trace_io_failed");
            }
            else
                BestEffortClose();
        }
        finally
        {
            lock (outputLeaseSync)
            {
                outputLeaseActive = false;
            }
        }
    }

    private void ClearInitialAfterTerminalReturn()
    {
        lock (outputLeaseSync)
        {
            epochState = null;
            currentFrames = 0;
            neutralSeen = false;
            candidateSignature = null;
            lastCapture = null;
        }
    }

    private void ClearAttemptAfterTerminalReturn()
    {
        lock (outputLeaseSync)
        {
            attemptPending = false;
            attemptOutcomeKnown = false;
            attemptState = null;
            currentFrames = 0;
            neutralSeen = false;
            candidateSignature = null;
            lastCapture = null;
        }
    }

    private bool TryClaimExpectedInputCompletion(DateTime finishedAtUtc)
    {
        if (completedInputs != expectedInputCount
            || finishedAtUtc.Kind != DateTimeKind.Utc
            || finishedAtUtc < startedAtUtc)
        {
            if (Interlocked.CompareExchange(
                ref terminalOwner, FaultTerminalOwner, NoTerminalOwner)
                != NoTerminalOwner)
                return false;
            phase = PassivePhase.Faulted;
            TerminalWork work = TerminalWork.Ordinary(
                "observer_exception",
                new ErrorRecord(
                    runId, null, null, "observer_exception", 0, null));
            if (QueueOrAcquireOutputLeaseLocked(work))
                throw new InvalidOperationException(
                    "completion fault must defer behind Step lease");
            return false;
        }
        return Interlocked.CompareExchange(
            ref terminalOwner, SuccessTerminalOwner, NoTerminalOwner)
            == NoTerminalOwner;
    }

    private void FinishExpectedInputCount(DateTime finishedAtUtc)
    {
        try
        {
            sink.WriteEnd(new EndRecord(
                runId, expectedInputCount, finishedAtUtc));
            CloseSink();
        }
        catch (Exception error)
        {
            phase = PassivePhase.Faulted;
            SafeDiagnostic(error);
            BestEffortClose();
            SafeFailed("trace_io_failed");
            return;
        }
        phase = PassivePhase.Done;
        try { reporter.Complete(); }
        catch (Exception error)
        {
            phase = PassivePhase.Faulted;
            SafeDiagnostic(error);
            SafeFailed("observer_exception");
        }
    }

    private StepContinuation SelectDurableStepContinuation(DateTime utcNow)
    {
        lock (outputLeaseSync)
        {
            stableState = attemptState;
            attemptPending = false;
            attemptOutcomeKnown = false;
            attemptState = null;
            currentFrames = 0;
            neutralSeen = false;
            candidateSignature = null;
            lastCapture = null;
            completedInputs++;
            if (deferredTerminalWork != null
                && deferredTerminalWork.Kind == TerminalWorkKind.OrdinaryFault)
            {
                deferredTerminalWork.Error = new ErrorRecord(
                    runId,
                    null,
                    null,
                    deferredTerminalWork.Code,
                    0,
                    null);
            }
            if (TerminalSelected() || Read(ref disposed) != 0
                || Read(ref disabled) != 0)
                return StepContinuation.None;
            if (completedInputs == expectedInputCount)
                return TryClaimExpectedInputCompletion(utcNow)
                    ? StepContinuation.Complete : StepContinuation.None;
            phase = PassivePhase.Ready;
            return StepContinuation.Ready;
        }
    }
}
