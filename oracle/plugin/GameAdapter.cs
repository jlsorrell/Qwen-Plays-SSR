using System;
using System.Globalization;
using System.Reflection;
using System.Runtime.CompilerServices;

internal sealed class GameAdapter : IOracleGameAdapter
{
    private readonly FieldInfo leavingField;
    private readonly FieldInfo gameOverField;
    private readonly FieldInfo explodingField;
    private string isolatedCanonicalPath;

    internal GameAdapter()
    {
        leavingField = RequirePrivateBoolean("leaving");
        gameOverField = RequirePrivateBoolean("gameover");
        explodingField = RequirePrivateBoolean("exploding");
    }

    private static FieldInfo RequirePrivateBoolean(string name)
    {
        FieldInfo field = typeof(Game).GetField(
            name, BindingFlags.Instance | BindingFlags.NonPublic);
        if (field == null || field.FieldType != typeof(bool))
            throw new CaptureException("invalid private Game field: " + name);
        return field;
    }

    public void AuthenticateAndRedirectSavePath(string isolatedPath)
    {
        try
        {
            string home = Environment.GetEnvironmentVariable("HOME");
            if (String.IsNullOrEmpty(home) || SaveGame.homePath != home)
                throw new CaptureException("ordinary HOME authentication failed");
            string ordinaryText = home
                + "/Library/Application Support/unity.increpare games/Sausage";
            if (SaveGame.PersistentDataPath != ordinaryText)
                throw new CaptureException("ordinary save path changed");
            PhysicalPathIdentity ordinary =
                PhysicalPath.ResolvePossiblyAbsent(ordinaryText);
            string isolated = PhysicalPath.ResolveExistingDirectory(isolatedPath);
            if (PhysicalPath.Contains(ordinary.CanonicalPath, isolated)
                || PhysicalPath.Contains(isolated, ordinary.CanonicalPath))
                throw new CaptureException("save paths overlap");
            SaveGame.PersistentDataPath = isolated;
            if (SaveGame.PersistentDataPath != isolated)
                throw new CaptureException("save redirect readback failed");
            isolatedCanonicalPath = isolated;
        }
        catch (CaptureException) { throw; }
        catch (Exception error)
        { throw new CaptureException("save redirect failed", error); }
    }

    public bool VerifySavePath()
    {
        if (isolatedCanonicalPath == null
            || SaveGame.PersistentDataPath != isolatedCanonicalPath) return false;
        try
        {
            return PhysicalPath.ResolveExistingDirectory(isolatedCanonicalPath)
                == isolatedCanonicalPath;
        }
        catch (OracleConfigurationException) { return false; }
    }

    public bool TryGetState(object gameValue, out object stateReference)
    {
        stateReference = null;
        try
        {
            Game game = gameValue as Game;
            if (game == null) return false;
            GameState state = game.gamestate;
            if (state == null) return false;
            stateReference = state;
            return true;
        }
        catch (Exception error)
        { throw new CaptureException("state observation failed", error); }
    }

    public bool MovementScheduled(object stateValue)
    {
        GameState state = stateValue as GameState;
        if (state == null) throw new CaptureException("missing game state");
        try { return state.Moving(); }
        catch (Exception error)
        { throw new CaptureException("movement observation failed", error); }
    }

    public bool CurrentMovementScheduled(object gameValue)
    {
        Game game = gameValue as Game;
        if (game == null) throw new CaptureException("missing game");
        try { return MovementScheduled(game.gamestate); }
        catch (CaptureException) { throw; }
        catch (Exception error)
        { throw new CaptureException("state observation failed", error); }
    }

    public bool IsQuiescent(object gameValue, object stateValue)
    {
        try
        {
            Game game = gameValue as Game;
            GameState state = stateValue as GameState;
            if (game == null || state == null) return false;
            if (state.worldsausagespawns == null)
                throw new CaptureException("world sausage list is null");
            return GameObservationPolicy.IsQuiescent(new GameGateValues(
                true,
                state.player != null,
                !MovementScheduled(state),
                state.pushestotry == 0,
                !game.exitSequence,
                !Game.endingsequence,
                !game.bluespawnanim,
                !(bool)leavingField.GetValue(game),
                !(bool)gameOverField.GetValue(game),
                !(bool)explodingField.GetValue(game),
                game.escmenu == null || !game.escmenu.activeSelf,
                GameState.shouldredrawcoffins == Coord.Invalid,
                state.worldsausagespawns.Count == 0));
        }
        catch (CaptureException) { throw; }
        catch (Exception error)
        { throw new CaptureException("quiescence observation failed", error); }
    }

    public CaptureRecord Capture(object stateValue)
    {
        GameState state = stateValue as GameState;
        if (state == null) throw new CaptureException("missing game state");
        try
        {
            if (state.player == null || state.movements == null
                || state.worldsausagespawns == null)
                throw new CaptureException("required capture member is null");
            string rawSave = state.Save(false, false);
            if (rawSave == null) throw new CaptureException("raw save is null");
            return CaptureMapping.Create(new CaptureValues(
                rawSave,
                RuntimeHelpers.GetHashCode(state).ToString(CultureInfo.InvariantCulture),
                state.pushtargetlevel,
                state.overworld,
                state.won,
                state.returning,
                state.haveevercookedall,
                state.lostreason,
                state.displayname,
                state.sausagescooked,
                state.movements.Count,
                state.pushestotry));
        }
        catch (CaptureException) { throw; }
        catch (Exception error)
        { throw new CaptureException("game-state capture failed", error); }
    }
}
