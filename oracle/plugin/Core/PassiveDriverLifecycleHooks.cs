using System;
using System.Collections.Generic;

internal sealed partial class PassiveDriver
{

private sealed class StateSetContext
{
    internal long Id;
    internal object Before;
}

private readonly List<long> restartContexts = new List<long>();
private int restartDepth;
private StateSetContext stateSetContext;

internal HookToken RestartEntered()
{
    bool nested = restartDepth > 0;
    if (!nested && !IsObservationActive())
        return HookToken.Inert(HookKind.Restart);
    HookToken token = NewToken(HookKind.Restart);
    if (!token.Active)
        return token;
    restartContexts.Add(token.Id);
    restartDepth++;
    if (!nested)
        TryFaultInternal("unexpected_input", FaultRequest.Restart());
    return token;
}

private void PopRestart(long id)
{
    int last = restartContexts.Count - 1;
    if (last < 0 || restartContexts[last] != id)
        throw new InvalidOperationException("restart token mismatch");
    restartContexts.RemoveAt(last);
    restartDepth--;
    if (restartDepth < 0 || restartDepth != restartContexts.Count)
        throw new InvalidOperationException("restart depth imbalance");
}

internal void RestartReturned(HookToken token)
{
    ValidateRestartPopOrder(token);
    if (!ConsumeOrdinaryToken(token, HookKind.Restart))
        return;
    PopRestart(token.Id);
}

internal void RestartThrew(HookToken token)
{
    ValidateRestartPopOrder(token);
    if (!ConsumeCleanupToken(token, HookKind.Restart))
        return;
    PopRestart(token.Id);
}

private void ValidateRestartPopOrder(HookToken token)
{
    if (token == null || !token.Active || !token.BelongsTo(this)
        || token.Kind != HookKind.Restart)
        return;
    int index = restartContexts.IndexOf(token.Id);
    if (index >= 0 && index != restartContexts.Count - 1)
        throw new InvalidOperationException("restart token mismatch");
}

internal HookToken StateSetEntered(
    object beforeState, object requestedState)
{
    if (!IsObservationActive())
        return HookToken.Inert(HookKind.StateSet);
    if (stateSetContext != null)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return HookToken.Inert(HookKind.StateSet);
    }
    HookToken token = NewToken(HookKind.StateSet);
    if (!token.Active)
        return token;
    stateSetContext = new StateSetContext
    {
        Id = token.Id,
        Before = beforeState
    };
    return token;
}

internal void StateSetReturned(
    HookToken token, object afterState, double nowSeconds)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.StateSet)
            && stateSetContext != null
            && stateSetContext.Id == token.Id)
            stateSetContext = null;
        return;
    }
    if (!ConsumeOrdinaryToken(token, HookKind.StateSet))
        return;
    if (stateSetContext == null || stateSetContext.Id != token.Id)
    {
        TryFaultInternal("hook_order_mismatch", FaultRequest.Derived());
        return;
    }
    StateSetContext context = stateSetContext;
    stateSetContext = null;
    if (!IsValidMonotonic(nowSeconds))
    {
        TryFaultInternal("observer_exception", FaultRequest.Derived());
        return;
    }
    bool replaced = !Object.ReferenceEquals(context.Before, afterState);
    if (phase == PassivePhase.AwaitGame
        || phase == PassivePhase.AwaitInitialNeutral)
    {
        if (afterState == null)
            ResetToAwaitGame();
        else if (replaced)
            StartInitialEpoch(afterState, nowSeconds, false);
        return;
    }
    if ((phase == PassivePhase.Ready || phase == PassivePhase.Settling)
        && replaced)
        TryFaultInternal("state_replaced", FaultRequest.Derived());
}

internal void StateSetThrew(HookToken token)
{
    if (!IsObservationActive())
    {
        if (ConsumeLateToken(token, HookKind.StateSet)
            && stateSetContext != null
            && stateSetContext.Id == token.Id)
            stateSetContext = null;
        return;
    }
    if (!ConsumeCleanupToken(token, HookKind.StateSet))
        return;
    if (stateSetContext == null || stateSetContext.Id != token.Id)
        throw new InvalidOperationException("StateSet token mismatch");
    stateSetContext = null;
}

internal void ClearThrew(HookToken token)
{
if (token == null || !token.Active)
    return;
switch (token.Kind)
{
    case HookKind.PlayerPoll: PlayerPollThrew(token); return;
    case HookKind.ProcessInput: ProcessInputThrew(token); return;
    case HookKind.Undo: UndoThrew(token); return;
    case HookKind.Restart: RestartThrew(token); return;
    case HookKind.StateSet: StateSetThrew(token); return;
    default:
        throw new InvalidOperationException("unknown hook kind");
}
}

}
