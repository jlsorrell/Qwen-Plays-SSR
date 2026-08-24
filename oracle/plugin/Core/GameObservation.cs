using System;

internal sealed class GameGateValues
{
    internal GameGateValues(
        bool hasGameAndState, bool hasPlayer, bool notMoving,
        bool noPushesToTry, bool noExitSequence, bool noEndingSequence,
        bool noBlueSpawnAnimation, bool notLeaving, bool notGameOver,
        bool notExploding, bool menuInactive, bool coffinsSettled,
        bool noWorldSausageSpawns)
    {
        HasGameAndState = hasGameAndState;
        HasPlayer = hasPlayer;
        NotMoving = notMoving;
        NoPushesToTry = noPushesToTry;
        NoExitSequence = noExitSequence;
        NoEndingSequence = noEndingSequence;
        NoBlueSpawnAnimation = noBlueSpawnAnimation;
        NotLeaving = notLeaving;
        NotGameOver = notGameOver;
        NotExploding = notExploding;
        MenuInactive = menuInactive;
        CoffinsSettled = coffinsSettled;
        NoWorldSausageSpawns = noWorldSausageSpawns;
    }
    internal bool HasGameAndState { get; private set; }
    internal bool HasPlayer { get; private set; }
    internal bool NotMoving { get; private set; }
    internal bool NoPushesToTry { get; private set; }
    internal bool NoExitSequence { get; private set; }
    internal bool NoEndingSequence { get; private set; }
    internal bool NoBlueSpawnAnimation { get; private set; }
    internal bool NotLeaving { get; private set; }
    internal bool NotGameOver { get; private set; }
    internal bool NotExploding { get; private set; }
    internal bool MenuInactive { get; private set; }
    internal bool CoffinsSettled { get; private set; }
    internal bool NoWorldSausageSpawns { get; private set; }
}

internal sealed class CaptureValues
{
    internal CaptureValues(
        string rawSave, string stateIdentity, string level, bool overworld,
        bool won, bool returning, bool haveEverCookedAll, string lostReason,
        string displayName, int sausagesCooked, int movementCount,
        int pushesToTry)
    {
        RawSave = rawSave; StateIdentity = stateIdentity; Level = level;
        Overworld = overworld; Won = won; Returning = returning;
        HaveEverCookedAll = haveEverCookedAll; LostReason = lostReason;
        DisplayName = displayName; SausagesCooked = sausagesCooked;
        MovementCount = movementCount; PushesToTry = pushesToTry;
    }
    internal string RawSave { get; private set; }
    internal string StateIdentity { get; private set; }
    internal string Level { get; private set; }
    internal bool Overworld { get; private set; }
    internal bool Won { get; private set; }
    internal bool Returning { get; private set; }
    internal bool HaveEverCookedAll { get; private set; }
    internal string LostReason { get; private set; }
    internal string DisplayName { get; private set; }
    internal int SausagesCooked { get; private set; }
    internal int MovementCount { get; private set; }
    internal int PushesToTry { get; private set; }
}

internal static class GameObservationPolicy
{
    internal static bool IsQuiescent(GameGateValues value)
    {
        if (value == null) throw new ArgumentNullException("value");
        return value.HasGameAndState && value.HasPlayer && value.NotMoving
            && value.NoPushesToTry && value.NoExitSequence
            && value.NoEndingSequence && value.NoBlueSpawnAnimation
            && value.NotLeaving && value.NotGameOver && value.NotExploding
            && value.MenuInactive && value.CoffinsSettled
            && value.NoWorldSausageSpawns;
    }
}

internal static class CaptureMapping
{
    internal static CaptureRecord Create(CaptureValues value)
    {
        if (value == null) throw new CaptureException("missing capture values");
        if (value.RawSave == null) throw new CaptureException("raw save is null");
        if (value.StateIdentity == null)
            throw new CaptureException("state identity is null");
        try
        {
            return new CaptureRecord(value.RawSave, value.StateIdentity,
                value.Level ?? "", value.Overworld, value.Won,
                value.Returning, value.HaveEverCookedAll,
                value.LostReason ?? "", value.DisplayName ?? "",
                value.SausagesCooked, value.MovementCount, value.PushesToTry);
        }
        catch (Exception error)
        {
            throw new CaptureException("invalid capture values", error);
        }
    }
}
