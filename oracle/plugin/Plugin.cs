using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;

namespace SsrOracle
{
    [BepInPlugin("dev.jlsor.ssr.oracle", "SSR Executable Oracle", "0.3.0")]
    public sealed class Plugin : BaseUnityPlugin
    {
        private OracleController controller;

        private void Awake()
        {
            IPassiveLog log = new BepInExLog(Logger);
            PassiveLogReporter reporter = new PassiveLogReporter(log);
            OracleConfiguration configuration;
            byte[] originalBytes;
            try
            {
                configuration = OracleConfiguration.Load(
                    Path.Combine(Paths.ConfigPath,
                        "dev.jlsor.ssr.oracle.cfg"),
                    out originalBytes);
            }
            catch (OracleConfigurationException error)
            {
                reporter.Failed(error.Code);
                return;
            }

            if (configuration.Mode == OracleMode.Off)
            {
                PluginModePolicy.StartOff(configuration,
                    GameContract.ValidateLegacySurface,
                    delegate { log.Info("SSR oracle boot probe loaded"); });
                return;
            }
            if (configuration.Mode != OracleMode.Passive
                && configuration.Mode != OracleMode.Replay)
            {
                reporter.Failed("invalid_mode");
                return;
            }

            PassiveLogReporter activeReporter = configuration.Mode
                    == OracleMode.Replay
                ? new PassiveLogReporter(log, OracleMode.Replay, 1)
                : reporter;
            try
            {
                Harmony harmony = new Harmony(GameHooks.HarmonyOwner);
                GameAdapter adapter;
                try { adapter = new GameAdapter(); }
                catch (Exception error)
                { throw new PassiveStartupException("invalid_reflection", error); }
                OracleRuntimeHost runtime = new OracleRuntimeHost(harmony);
                if (configuration.Mode == OracleMode.Replay)
                {
                    runtime.ValidateAssemblyAndPassiveContract();
                    ReplayInput input = ReplayInput.Load(
                        configuration.Replay.InputPath,
                        new FileReplayInputBytes());
                    controller = new OracleController(
                        configuration.Replay, input, adapter, runtime, log);
                    controller.Start(new RunRecord(
                        Guid.NewGuid().ToString("N"), OracleMode.Replay,
                        HashLiveGameAssembly(), input.Sha256, input.Count,
                        DateTime.UtcNow));
                }
                else
                {
                    controller = new OracleController(
                        configuration.Passive, adapter, runtime, log);
                    controller.Start(new RunRecord(
                        Guid.NewGuid().ToString("N"), HashLiveGameAssembly(),
                        DateTime.UtcNow));
                }
            }
            catch (OracleConfigurationException error)
            {
                activeReporter.Failed(error.Code);
                activeReporter.Diagnostic(error.InnerException == null
                    ? error.GetType().FullName
                    : error.InnerException.GetType().FullName);
            }
            catch (PassiveStartupException error)
            {
                activeReporter.Failed(error.Code);
                activeReporter.Diagnostic(error.InnerException == null
                    ? error.GetType().FullName
                    : error.InnerException.GetType().FullName);
            }
            catch (Exception error)
            {
                activeReporter.Failed("invalid_reflection");
                activeReporter.Diagnostic(error.GetType().FullName);
            }
        }

        private static string HashLiveGameAssembly()
        {
            try
            {
                string location = typeof(Game).Assembly.Location;
                byte[] digest;
                using (SHA256 hash = SHA256.Create())
                using (FileStream stream = new FileStream(location,
                    FileMode.Open, FileAccess.Read, FileShare.Read))
                    digest = hash.ComputeHash(stream);
                string text = LowerHex(digest);
                if (text != OracleProtocol.ExpectedAssemblySha256)
                    throw new InvalidOperationException(
                        "unexpected Assembly-CSharp SHA-256");
                return text;
            }
            catch (PassiveStartupException) { throw; }
            catch (Exception error)
            { throw new PassiveStartupException("invalid_assembly", error); }
        }

        private static string LowerHex(byte[] value)
        {
            StringBuilder result = new StringBuilder(value.Length * 2);
            for (int index = 0; index < value.Length; index++)
                result.Append(value[index].ToString(
                    "x2", CultureInfo.InvariantCulture));
            return result.ToString();
        }

        private void OnDestroy()
        {
            OracleController value = controller;
            controller = null;
            if (value != null) value.Dispose();
        }

        private sealed class BepInExLog : IPassiveLog
        {
            private readonly ManualLogSource source;
            internal BepInExLog(ManualLogSource source)
            { this.source = source ?? throw new ArgumentNullException("source"); }
            public void Info(string message) { source.LogInfo(message); }
            public void Error(string message) { source.LogError(message); }
            public void Warning(string message) { source.LogWarning(message); }
        }

        private sealed class OracleRuntimeHost : IOracleRuntimeHost
        {
            private readonly Harmony harmony;
            private readonly Stopwatch clock;

            internal OracleRuntimeHost(Harmony harmony)
            {
                this.harmony = harmony
                    ?? throw new ArgumentNullException("harmony");
                clock = Stopwatch.StartNew();
            }

            public void ValidateAssemblyAndPassiveContract()
            {
                try { HashLiveGameAssembly(); }
                catch (PassiveStartupException) { throw; }
                catch (Exception error)
                { throw new PassiveStartupException("invalid_assembly", error); }
                try { GameContract.ValidatePassiveSurface(); }
                catch (Exception error)
                { throw new PassiveStartupException("invalid_reflection", error); }
            }

            public ITraceSink CreateTrace(
                string outputDirectory, string runName)
            { return NdjsonTraceSink.Create(outputDirectory, runName); }

            public void InstallPatches(OracleController value)
            {
                GameHooks.Publish(value);
                try { harmony.PatchAll(); }
                catch
                {
                    try { harmony.UnpatchSelf(); }
                    finally { GameHooks.Clear(value); }
                    throw;
                }
            }

            public void UnpatchSelf(OracleController value)
            {
                harmony.UnpatchSelf();
                GameHooks.Clear(value);
            }

            public double NowSeconds()
            { return clock.ElapsedTicks / (double)Stopwatch.Frequency; }
            public DateTime UtcNow() { return DateTime.UtcNow; }
        }
    }
}
