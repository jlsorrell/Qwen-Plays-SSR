using System;
using System.Reflection;
using System.Threading;
using HarmonyLib;

internal static class GameHooks
{
    internal const string HarmonyOwner = "dev.jlsor.ssr.oracle.passive";
    private static OracleController controller;

    internal static void Publish(OracleController value)
    {
        if (value == null) throw new ArgumentNullException("value");
        if (Interlocked.CompareExchange(ref controller, value, null) != null)
            throw new InvalidOperationException("controller already published");
    }

    internal static void Clear(OracleController value)
    {
        if (value == null) return;
        if (!Object.ReferenceEquals(
            Interlocked.CompareExchange(ref controller, null, value), value))
            throw new InvalidOperationException("controller clear mismatch");
    }

    private static OracleController ReadController()
    {
        return Interlocked.CompareExchange(
            ref controller, null, null);
    }

    internal static void Observe(Action<OracleController> callback)
    {
        OracleController value = ReadController();
        if (value == null) return;
        PatchBoundary.Observe(
            delegate { callback(value); }, value.ObserverFailed);
    }

    internal static bool TryOverridePlayerInput(out int rawDirection)
    {
        rawDirection = 8;
        OracleController value = ReadController();
        if (value == null) return false;
        try { return value.TryOverridePlayerInput(out rawDirection); }
        catch
        {
            rawDirection = 8;
            value.ObserverFailed();
            return true;
        }
    }

    internal static Exception Finalize(HookToken token, Exception original)
    {
        OracleController value = ReadController();
        if (value == null) return original;
        return PatchBoundary.Finalize(token, original,
            value.ClearThrew, value.GameMethodFailed, value.ObserverFailed);
    }

    internal static Exception FinalizeUpdate(Exception original)
    {
        OracleController value = ReadController();
        if (value == null) return original;
        return PatchBoundary.FinalizeUpdate(
            original, value.UpdateThrew, value.ObserverFailed);
    }
}

internal static class PatchTarget
{
    internal static MethodBase Require(Type owner, string name,
        BindingFlags flags, Type returnType, Type[] parameters)
    {
        MethodInfo method = owner.GetMethod(name, flags, null, parameters, null);
        if (method == null || method.ReturnType != returnType
            || method.IsStatic != ((flags & BindingFlags.Static) != 0))
            throw new MissingMethodException(owner.FullName, name);
        return method;
    }
}

[HarmonyPatch]
internal static class GameUpdatePatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "Update",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[0]);
    }
    private static void Prefix(Game __instance)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.UpdateEntered(__instance); });
    }
    private static void Postfix(Game __instance)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.ObserveUpdate(__instance); });
    }
    private static Exception Finalizer(Exception __exception)
    { return GameHooks.FinalizeUpdate(__exception); }
}

[HarmonyPatch]
internal static class GameDoPlayerInputPatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "DoPlayerInput",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[0]);
    }
    private static void Prefix(out HookToken __state)
    {
        HookToken token = HookToken.Inert(HookKind.PlayerPoll);
        GameHooks.Observe(delegate(OracleController value)
        { token = value.PlayerPollEntered(); });
        __state = token;
    }
    private static void Postfix(HookToken __state)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.PlayerPollReturned(__state); });
    }
    private static Exception Finalizer(
        Exception __exception, HookToken __state)
    { return GameHooks.Finalize(__state, __exception); }
}

[HarmonyPatch]
internal static class GamePlayerinputstringPatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "Playerinputstring",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(Direction), new Type[0]);
    }
    private static bool Prefix(ref Direction __result)
    {
        int rawDirection;
        if (!GameHooks.TryOverridePlayerInput(out rawDirection)) return true;
        __result = (Direction)rawDirection;
        return false;
    }
    private static void Postfix(Direction __result)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.PhysicalPollReturned((int)__result); });
    }
}

[HarmonyPatch]
internal static class GameStateProcessInputPatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(GameState), "ProcessInput",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(bool), new Type[] { typeof(Direction) });
    }
    private static void Prefix(
        GameState __instance, Direction __0, out HookToken __state)
    {
        HookToken token = HookToken.Inert(HookKind.ProcessInput);
        GameHooks.Observe(delegate(OracleController value)
        { token = value.ProcessInputEntered(__instance, (int)__0); });
        __state = token;
    }
    private static void Postfix(
        GameState __instance, bool __result, HookToken __state)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.ProcessInputReturned(__state, __result, __instance); });
    }
    private static Exception Finalizer(
        Exception __exception, HookToken __state)
    { return GameHooks.Finalize(__state, __exception); }
}

[HarmonyPatch]
internal static class GameDoUndoPatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "DoUndo",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[0]);
    }
    private static void Prefix(Game __instance, out HookToken __state)
    {
        HookToken token = HookToken.Inert(HookKind.Undo);
        GameHooks.Observe(delegate(OracleController value)
        { token = value.UndoEntered(__instance); });
        __state = token;
    }
    private static void Postfix(Game __instance, HookToken __state)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.UndoReturned(__state, __instance); });
    }
    private static Exception Finalizer(
        Exception __exception, HookToken __state)
    { return GameHooks.Finalize(__state, __exception); }
}

[HarmonyPatch]
internal static class GameRestorePrevStatePatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "RestorePrevState",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[] { typeof(GameState.BakStruct) });
    }
    private static void Prefix(GameState.BakStruct __0)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.RestoreObserved(); });
    }
}

[HarmonyPatch]
internal static class GameDoRestartPatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "DoRestart",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[0]);
    }
    private static void Prefix(out HookToken __state)
    {
        HookToken token = HookToken.Inert(HookKind.Restart);
        GameHooks.Observe(delegate(OracleController value)
        { token = value.RestartEntered(); });
        __state = token;
    }
    private static void Postfix(HookToken __state)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.RestartReturned(__state); });
    }
    private static Exception Finalizer(
        Exception __exception, HookToken __state)
    { return GameHooks.Finalize(__state, __exception); }
}

[HarmonyPatch]
internal static class GameSetGameStatePatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "SetGameState",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[] { typeof(GameState) });
    }
    private static void Prefix(
        Game __instance, GameState __0, out HookToken __state)
    {
        HookToken token = HookToken.Inert(HookKind.StateSet);
        GameHooks.Observe(delegate(OracleController value)
        { token = value.StateSetEntered(__instance, __0); });
        __state = token;
    }
    private static void Postfix(Game __instance, HookToken __state)
    {
        GameHooks.Observe(delegate(OracleController value)
        { value.StateSetReturned(__state, __instance); });
    }
    private static Exception Finalizer(
        Exception __exception, HookToken __state)
    { return GameHooks.Finalize(__state, __exception); }
}
