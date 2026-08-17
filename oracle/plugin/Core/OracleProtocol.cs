using System;
using System.Collections.Generic;
using System.Globalization;

internal static class OracleProtocol
{
    internal const int SchemaVersion = 1;
    internal const string PluginVersion = "0.3.0";
    internal const int ExpectedInputCount = 3;
    internal const int MaxSettleFrames = 600;
    internal const int MaxSettleSeconds = 30;
    internal const string ExpectedAssemblySha256 =
        "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564";
}

internal enum OracleMode { Off = 0, Passive = 1 }
internal enum OracleInput
{
    North = 0,
    South = 1,
    West = 2,
    East = 3,
    Undo = 4
}

internal enum PassivePhase
{
    Disabled = 0,
    AwaitGame = 1,
    AwaitInitialNeutral = 2,
    Ready = 3,
    Settling = 4,
    Done = 5,
    Faulted = 6
}

internal static class OracleValidation
{
    internal static string Required(string value, string name)
    {
        if (value == null)
            throw new ArgumentNullException(name);
        return value;
    }

    internal static string RunId(string value)
    {
        Required(value, "runId");
        if (value.Length != 32 || !IsLowerHex(value))
            throw new ArgumentException("run ID must be 32 lowercase hex digits", "value");
        return value;
    }

    internal static string AssemblySha256(string value)
    {
        Required(value, "gameAssemblySha256");
        if (value != OracleProtocol.ExpectedAssemblySha256)
            throw new ArgumentException("unexpected assembly SHA-256", "value");
        return value;
    }

    internal static string StateIdentity(string value)
    {
        Required(value, "stateIdentity");
        int parsed;
        if (!Int32.TryParse(
            value,
            NumberStyles.AllowLeadingSign,
            CultureInfo.InvariantCulture,
            out parsed)
            || parsed.ToString(CultureInfo.InvariantCulture) != value)
        {
            throw new ArgumentException(
                "state identity must be canonical signed Int32 text",
                "value");
        }
        return value;
    }

    internal static int Nonnegative(int value, string name)
    {
        if (value < 0)
            throw new ArgumentOutOfRangeException(name);
        return value;
    }

    internal static int SettleFrames(int value, bool success)
    {
        int minimum = success ? 2 : 0;
        if (value < minimum || value > OracleProtocol.MaxSettleFrames)
            throw new ArgumentOutOfRangeException("settleFrames");
        return value;
    }

    internal static OracleInput Input(OracleInput value)
    {
        switch (value)
        {
            case OracleInput.North:
            case OracleInput.South:
            case OracleInput.West:
            case OracleInput.East:
            case OracleInput.Undo:
                return value;
            default:
                throw new ArgumentOutOfRangeException("value");
        }
    }

    internal static DateTime Utc(DateTime value, string name)
    {
        if (value.Kind != DateTimeKind.Utc)
            throw new ArgumentException("timestamp must be UTC", name);
        return value;
    }

    private static bool IsLowerHex(string value)
    {
        for (int index = 0; index < value.Length; index++)
        {
            char current = value[index];
            if (!((current >= '0' && current <= '9')
                || (current >= 'a' && current <= 'f')))
            {
                return false;
            }
        }
        return true;
    }
}

internal sealed class CaptureRecord : IEquatable<CaptureRecord>
{
    internal CaptureRecord(
        string rawSave,
        string stateIdentity,
        string level,
        bool overworld,
        bool won,
        bool returning,
        bool haveEverCookedAll,
        string lostReason,
        string displayName,
        int sausagesCooked,
        int movementCount,
        int pushesToTry)
    {
        RawSave = OracleValidation.Required(rawSave, "rawSave");
        StateIdentity = OracleValidation.StateIdentity(stateIdentity);
        Level = OracleValidation.Required(level, "level");
        Overworld = overworld;
        Won = won;
        Returning = returning;
        HaveEverCookedAll = haveEverCookedAll;
        LostReason = OracleValidation.Required(lostReason, "lostReason");
        DisplayName = OracleValidation.Required(displayName, "displayName");
        SausagesCooked = OracleValidation.Nonnegative(
            sausagesCooked, "sausagesCooked");
        MovementCount = OracleValidation.Nonnegative(
            movementCount, "movementCount");
        PushesToTry = OracleValidation.Nonnegative(pushesToTry, "pushesToTry");
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

    public bool Equals(CaptureRecord other)
    {
        return other != null
            && RawSave == other.RawSave
            && StateIdentity == other.StateIdentity
            && Level == other.Level
            && Overworld == other.Overworld
            && Won == other.Won
            && Returning == other.Returning
            && HaveEverCookedAll == other.HaveEverCookedAll
            && LostReason == other.LostReason
            && DisplayName == other.DisplayName
            && SausagesCooked == other.SausagesCooked
            && MovementCount == other.MovementCount
            && PushesToTry == other.PushesToTry;
    }

    public override bool Equals(object value)
    {
        return Equals(value as CaptureRecord);
    }

    public override int GetHashCode()
    {
        unchecked
        {
            int hash = 17;
            hash = hash * 31 + RawSave.GetHashCode();
            hash = hash * 31 + StateIdentity.GetHashCode();
            hash = hash * 31 + Level.GetHashCode();
            hash = hash * 31 + Overworld.GetHashCode();
            hash = hash * 31 + Won.GetHashCode();
            hash = hash * 31 + Returning.GetHashCode();
            hash = hash * 31 + HaveEverCookedAll.GetHashCode();
            hash = hash * 31 + LostReason.GetHashCode();
            hash = hash * 31 + DisplayName.GetHashCode();
            hash = hash * 31 + SausagesCooked;
            hash = hash * 31 + MovementCount;
            hash = hash * 31 + PushesToTry;
            return hash;
        }
    }
}

internal sealed class RunRecord
{
    internal RunRecord(
        string runId,
        string gameAssemblySha256,
        DateTime startedAtUtc)
    {
        SchemaVersion = OracleProtocol.SchemaVersion;
        RunId = OracleValidation.RunId(runId);
        Mode = OracleMode.Passive;
        GameAssemblySha256 = OracleValidation.AssemblySha256(
            gameAssemblySha256);
        PluginVersion = OracleProtocol.PluginVersion;
        InputSha256 = null;
        ExpectedInputCount = OracleProtocol.ExpectedInputCount;
        StartedAtUtc = OracleValidation.Utc(startedAtUtc, "startedAtUtc");
    }

    internal int SchemaVersion { get; private set; }
    internal string RunId { get; private set; }
    internal OracleMode Mode { get; private set; }
    internal string GameAssemblySha256 { get; private set; }
    internal string PluginVersion { get; private set; }
    internal string InputSha256 { get; private set; }
    internal int ExpectedInputCount { get; private set; }
    internal DateTime StartedAtUtc { get; private set; }
}

internal sealed class InitialRecord
{
    internal InitialRecord(string runId, CaptureRecord capture)
    {
        SchemaVersion = OracleProtocol.SchemaVersion;
        RunId = OracleValidation.RunId(runId);
        InputIndex = null;
        Capture = capture ?? throw new ArgumentNullException("capture");
    }

    internal int SchemaVersion { get; private set; }
    internal string RunId { get; private set; }
    internal int? InputIndex { get; private set; }
    internal CaptureRecord Capture { get; private set; }
}

internal sealed class StepRecord
{
    internal StepRecord(
        string runId,
        int inputIndex,
        OracleInput input,
        bool accepted,
        bool movementScheduled,
        int settleFrames,
        bool stateReplaced,
        CaptureRecord capture)
    {
        if (stateReplaced)
            throw new ArgumentException(
                "schema-v1 step cannot replace state", "stateReplaced");
        SchemaVersion = OracleProtocol.SchemaVersion;
        RunId = OracleValidation.RunId(runId);
        InputIndex = OracleValidation.Nonnegative(inputIndex, "inputIndex");
        Input = OracleValidation.Input(input);
        Accepted = accepted;
        MovementScheduled = movementScheduled;
        SettleFrames = OracleValidation.SettleFrames(settleFrames, true);
        StateReplaced = false;
        Capture = capture ?? throw new ArgumentNullException("capture");
    }

    internal int SchemaVersion { get; private set; }
    internal string RunId { get; private set; }
    internal int InputIndex { get; private set; }
    internal OracleInput Input { get; private set; }
    internal bool Accepted { get; private set; }
    internal bool MovementScheduled { get; private set; }
    internal int SettleFrames { get; private set; }
    internal bool StateReplaced { get; private set; }
    internal CaptureRecord Capture { get; private set; }
}

internal sealed class EndRecord
{
    internal EndRecord(string runId, int inputCount, DateTime finishedAtUtc)
    {
        if (inputCount != OracleProtocol.ExpectedInputCount)
            throw new ArgumentOutOfRangeException("inputCount");
        SchemaVersion = OracleProtocol.SchemaVersion;
        RunId = OracleValidation.RunId(runId);
        InputCount = inputCount;
        FinishedAtUtc = OracleValidation.Utc(finishedAtUtc, "finishedAtUtc");
    }

    internal int SchemaVersion { get; private set; }
    internal string RunId { get; private set; }
    internal int InputCount { get; private set; }
    internal DateTime FinishedAtUtc { get; private set; }
}

internal sealed class ErrorRecord
{
    internal ErrorRecord(
        string runId,
        int? inputIndex,
        OracleInput? input,
        string code,
        int settleFrames,
        CaptureRecord lastCapture)
    {
        OracleError error = OracleErrors.ForCode(code);
        if (input.HasValue && !inputIndex.HasValue)
            throw new ArgumentException("input requires input index");
        if (inputIndex.HasValue)
            OracleValidation.Nonnegative(inputIndex.Value, "inputIndex");
        if (input.HasValue)
            OracleValidation.Input(input.Value);
        if (inputIndex.HasValue && !input.HasValue
            && !String.Equals(error.Code, "unexpected_input", StringComparison.Ordinal))
        {
            throw new ArgumentException(
                "only unexpected_input may retain an index without an input");
        }
        SchemaVersion = OracleProtocol.SchemaVersion;
        RunId = OracleValidation.RunId(runId);
        InputIndex = inputIndex;
        Input = input;
        Code = error.Code;
        Message = error.Message;
        SettleFrames = OracleValidation.SettleFrames(settleFrames, false);
        LastCapture = lastCapture;
    }

    internal int SchemaVersion { get; private set; }
    internal string RunId { get; private set; }
    internal int? InputIndex { get; private set; }
    internal OracleInput? Input { get; private set; }
    internal string Code { get; private set; }
    internal string Message { get; private set; }
    internal int SettleFrames { get; private set; }
    internal CaptureRecord LastCapture { get; private set; }
}

internal sealed class OracleError
{
    internal OracleError(string code, string message)
    {
        if (code == null)
            throw new ArgumentNullException("code");
        if (message == null)
            throw new ArgumentNullException("message");
        Code = code;
        Message = message;
    }

    internal string Code { get; private set; }
    internal string Message { get; private set; }
}

internal static class OracleErrors
{
    private static readonly Dictionary<string, OracleError> RecordErrors =
        new Dictionary<string, OracleError>(StringComparer.Ordinal)
        {
            { "patch_install_failed", new OracleError("patch_install_failed", "observation patch installation failed") },
            { "input_before_initial", new OracleError("input_before_initial", "manual input arrived before initial capture") },
            { "overlapping_input", new OracleError("overlapping_input", "manual input arrived while settling") },
            { "unexpected_input", new OracleError("unexpected_input", "native input was outside the passive vocabulary") },
            { "unscoped_process_input", new OracleError("unscoped_process_input", "manual-looking input occurred outside the native poll scope") },
            { "hook_order_mismatch", new OracleError("hook_order_mismatch", "observation hook order mismatch") },
            { "game_method_exception", new OracleError("game_method_exception", "observed game method threw") },
            { "observer_exception", new OracleError("observer_exception", "passive observer failed") },
            { "capture_failed", new OracleError("capture_failed", "game-state capture failed") },
            { "record_too_large", new OracleError("record_too_large", "encoded trace record exceeded its limit") },
            { "initial_settle_timeout", new OracleError("initial_settle_timeout", "initial capture did not settle") },
            { "settle_timeout", new OracleError("settle_timeout", "input did not settle") },
            { "state_replaced", new OracleError("state_replaced", "game state identity changed") },
            { "save_path_changed", new OracleError("save_path_changed", "isolated save path changed") }
        };

    internal static OracleError ForCode(string code)
    {
        OracleError value;
        if (code == null || !RecordErrors.TryGetValue(code, out value))
            throw new ArgumentException("unknown record error code", "code");
        return value;
    }

    internal static bool IsRecordCode(string code)
    {
        return code != null && RecordErrors.ContainsKey(code);
    }
}

internal static class OracleMarkerErrors
{
    private static readonly Dictionary<string, bool> MarkerOnly =
        new Dictionary<string, bool>(StringComparer.Ordinal)
        {
            { "invalid_mode", true },
            { "invalid_configuration", true },
            { "invalid_assembly", true },
            { "invalid_reflection", true },
            { "invalid_path", true },
            { "trace_exists", true },
            { "save_redirect_failed", true },
            { "trace_io_failed", true }
        };

    internal static bool IsMarkerOnly(string code)
    {
        return code != null && MarkerOnly.ContainsKey(code);
    }
}
