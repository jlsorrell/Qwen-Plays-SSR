using System;
using System.Reflection;
using BepInEx;
using HarmonyLib;

namespace SsrOracle
{
    [BepInPlugin("dev.jlsor.ssr.oracle", "SSR Executable Oracle", "0.1.0")]
    public sealed class Plugin : BaseUnityPlugin
    {
        private Harmony harmony;

        private void Awake()
        {
            harmony = new Harmony("dev.jlsor.ssr.oracle");
            RequireMethod(typeof(Game), "Playerinputstring");
            RequireMethod(typeof(Game), "DoPlayerInput");
            RequireMethod(typeof(GameState), "ProcessInput");
            Logger.LogInfo("SSR oracle boot probe loaded");
        }

        private static void RequireMethod(System.Type type, string name)
        {
            MethodInfo method = AccessTools.Method(type, name);
            if (method == null)
                throw new MissingMethodException(type.FullName, name);
        }

        private void OnDestroy()
        {
            if (harmony != null)
                harmony.UnpatchSelf();
        }
    }
}
