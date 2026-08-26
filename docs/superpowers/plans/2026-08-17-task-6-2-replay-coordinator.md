# Task 6.2 Replay Coordinator and Bounded Live Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add exact-byte replay ingestion and a deterministic coordinator that
drives SSR inputs through the game's native input path, prove the implementation
offline, then—behind two fresh explicit approvals—calibrate and execute one
bounded live replay from an authenticated isolated save.

**Architecture:** The existing `PassiveDriver` remains the sole trace, settling,
and terminal owner. `ReplayInput` authenticates immutable `.dem` bytes;
`ReplayCoordinator` wraps the driver's reporter and decides when one token may
traverse `Playerinputstring` or `DoUndo`. `OracleController` routes plain Core
interfaces to the existing game adapter and Harmony hooks. The operational gate
reuses the transactional installer and protocol reader through a reviewed,
one-use runbook; it adds no installed runner or second installer.

**Tech Stack:** C# 7.3; compile-only .NET Framework 3.5; pinned .NET SDK
10.0.300 unit harness; BepInEx 5.4.23.5; Harmony; Python 3.13/pytest; strict
schema-v1 NDJSON; macOS process groups and no-follow filesystem probes.

**Specs:**

- `docs/superpowers/specs/2026-08-17-task-6-2-replay-gate-design.md`
- `docs/superpowers/specs/2026-08-15-task-6-runtime-replay-design.md`

## Global constraints

- The approved design commit is
  `2cb2ff6d1040fb26b163a52faa65a1d947a18d38`; authenticate it before
  implementation.
- Tasks 0–8 are offline. They may read the pinned installed assemblies and
  wrapper, but may not deploy, edit installed configuration, write a save, or
  launch the game.
- Tasks 9–12 are operational. Task 10 stops for approval one; Task 12 stops for
  approval two. An earlier approval, silence, or approval of this plan does not
  authorize either launch.
- `PassiveDriver` remains the only writer of Run/Initial/Step/End/Error and the
  only owner of Ready/Complete/Failed ordering. The coordinator does not settle
  state or write a record.
- Passive remains exactly three attempts, leaves native input unchanged, and
  never invokes Undo. Replay accepts a positive dynamic token count.
- Cardinal replay overrides only `Game.Playerinputstring`; it never calls
  `GameState.ProcessInput` directly. Undo replay calls only public
  `Game.DoUndo()`.
- Physical input is suppressed for the complete replay run. A real suppressed
  `Playerinputstring` return of native `None` is the only neutral-poll credit.
- A token index changes only in `ReplayCoordinator.Ready(n)` after a durable
  intermediate Step. The final Step completes through `Complete()` without
  `Ready(count)`.
- A cardinal override exists for one owning `Game.Update` only. Missing,
  duplicate, mismatched, or late traversal is `replay_alignment_failed` and is
  never retried.
- `initial_state_mismatch` is selected under the driver's Initial output lease,
  before forwarding Ready(0) or arming token zero.
- Core remains free of Unity, Harmony, BepInEx, concrete game types, and ambient
  filesystem/game state.
- Production remains C# 7.3/net35 compatible. Do not add tuples, records,
  nullable-reference annotations, pattern-switch syntax, `using var`, or
  framework APIs absent from CLR v2.
- All package restores are offline from reviewed local artifacts. Any network
  request or audit fetch is a blocker.
- Preserve the exact Task 6.1 graph and every historical design, plan, report,
  evidence root, local asset cache, and unrelated worktree.
- Implementation remains one reviewed working-tree transaction and one final
  exact-scope commit with subject
  `feat: replay SSR inputs through native game path`. Do not create slice commits.
- The live gate never rewrites that immutable implementation commit and never
  commits `.dem`, traces, saves, binaries, logs, or operational evidence.

### Fresh-gate identity-contract prerequisite

Every future gate root must pass the tracked gate-id contract checker before
its helper hashes, source manifest, runbook, or approval packet are frozen.
Run this from the repository root, replacing `<fresh-gate-root>` with the new
root only:

```bash
/Users/jlsor/Documents/Research/SSR/.venv/bin/python tools/check_replay_gate_id_contract.py <fresh-gate-root>/gate_command_once.py <fresh-gate-root>/gate_live_monitor.py
```

Required output:

```text
gate_id_contract=matched pattern=[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z
```

The recorder's literal `SAFE_ID` regex is canonical for `gate_id`. The fresh
monitor copy must assign that same literal regex to `_SAFE_ID`, including
mixed-case identifiers such as `gate-ztIoOAH2`. A mismatch stops preparation.
Correct only the unfrozen fresh copy, rerun its helper tests and this checker,
then freeze new hashes. Never repair or reuse an older prepared, consumed, or
sealed gate root.

## File map

### Core production

- Create `oracle/plugin/Core/ReplayInput.cs`.
- Create `oracle/plugin/Core/ReplayCoordinator.cs`.
- Modify `oracle/plugin/Core/OracleProtocol.cs`.
- Modify `oracle/plugin/Core/CanonicalJson.cs`.
- Modify `oracle/plugin/Core/OracleConfiguration.cs`.
- Modify `oracle/plugin/Core/PhysicalPath.cs`.
- Modify `oracle/plugin/Core/OracleRuntimeBoundaries.cs`.
- Modify `oracle/plugin/Core/PassiveReporter.cs`.
- Modify `oracle/plugin/Core/PassiveDriver.cs`.

### Runtime boundary

- Modify `oracle/plugin/Core/OracleController.cs`.
- Modify `oracle/plugin/GameAdapter.cs`.
- Modify `oracle/plugin/GameHooks.cs`.
- Modify `oracle/plugin/Plugin.cs`.

`GameContract.cs`, `PassiveDriverInput.cs`, `PassiveDriverCompletion.cs`,
`PassiveDriverLifecycleHooks.cs`, `PassiveStartup.cs`, both project files, and
the eight Harmony target names remain unchanged unless a compile-time exactness
review proves a narrower edit is required.

### C# tests

- Create `oracle/plugin/tests/ReplayInputTests.cs` (`replay-input=6`).
- Create `oracle/plugin/tests/ReplayCoordinatorTests.cs`
  (`replay-coordinator=8`).
- Create `oracle/plugin/tests/ControllerReplayTests.cs`
  (`controller-replay=7`).
- Modify `oracle/plugin/tests/ProtocolTests.cs` (`protocol=6`).
- Modify `oracle/plugin/tests/EncodingTests.cs` (`encoding=6`, including the
  existing two capture-signature registrations).
- Modify `oracle/plugin/tests/ConfigurationTests.cs` (`config=8`).
- Modify `oracle/plugin/tests/PhysicalPathTests.cs` (`path=7`).
- Modify `oracle/plugin/tests/PassiveReporterTests.cs` (`reporter=5`).
- Modify `oracle/plugin/tests/AssemblySurfaceTests.cs` (`assembly=5`,
  `plugin=8`).
- Modify `oracle/plugin/tests/TestSupport.cs` only to append the exact approved
  identities.
- Modify `oracle/plugin/tests/Program.cs` to register the new classes and exact
  manifest. Final C# count: **113**.

### Python and fixture

- Modify `src/ssr_env/oracle_protocol.py`.
- Modify `tests/test_oracle_protocol.py`.
- Create `tests/fixtures/oracle_trace/replay-success.ndjson`.

### Evidence only

- Use ignored `data/oracle/task6-2-replay-gate/` for offline and live evidence.
- Never stage that directory or any ignored build/asset path.

---

### Task 0: Authenticate the plan lineage and offline baseline

**Files:** read-only repository and ignored evidence root.

- [ ] **Step 1: Authenticate the plan commit**

Run from the Task 6.2 worktree:

```bash
set -e
test "$(git show -s --format=%s HEAD)" = \
  "docs: plan Task 6.2 replay coordinator and gate"
test "$(git rev-parse HEAD^)" = \
  2cb2ff6d1040fb26b163a52faa65a1d947a18d38
test "$(git diff-tree --no-commit-id --name-only -r HEAD)" = \
  docs/superpowers/plans/2026-08-17-task-6-2-replay-coordinator.md
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain)"
plan_commit=$(git rev-parse HEAD)
test -n "$plan_commit"
```

- [ ] **Step 2: Pin local tool and artifact inputs**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
python_bin=/Users/jlsor/Documents/Research/SSR/.venv/bin/python
game_root="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
game_managed="$game_root/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="$game_root/BepInEx/core"
package_source="$PWD/data/oracle/compat/fetch-acceptance"
test -x "$dotnet_bin"
test -x "$python_bin"
test -f "$game_managed/Assembly-CSharp.dll"
test -f "$game_managed/UnityEngine.dll"
test -f "$game_managed/UnityEngine.CoreModule.dll"
test -f "$bepinex_core/BepInEx.dll"
test -f "$bepinex_core/0Harmony.dll"
test -x "$game_root/run_bepinex.sh"
test "$(shasum -a 256 "$game_managed/Assembly-CSharp.dll" | cut -d ' ' -f 1)" = \
  886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564
```

- [ ] **Step 3: Seed only ignored offline build inputs when absent**

Run these exact offline restores only for a missing assets file:

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_root="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
game_managed="$game_root/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="$game_root/BepInEx/core"
package_source="$PWD/data/oracle/compat/fetch-acceptance"
if test ! -f oracle/plugin/tests/obj/project.assets.json; then
  "$dotnet_bin" restore oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    --source "$package_source" -p:NuGetAudit=false
fi
if test ! -f oracle/plugin/tests/obj/core-net35/project.assets.json; then
  "$dotnet_bin" restore oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
    --source "$package_source" -p:NuGetAudit=false
fi
if test ! -f oracle/plugin/obj/project.assets.json; then
  "$dotnet_bin" restore oracle/plugin/SsrOracle.Plugin.csproj \
    --source "$package_source" -p:NuGetAudit=false \
    -p:GameManagedDir="$game_managed" \
    -p:BepInExCoreDir="$bepinex_core"
fi
```

A restore may change only ignored `obj` paths. If any command requests the
network, reports NU1900, writes a package outside the reviewed source, or
changes a tracked path, stop.

- [ ] **Step 4: Capture the accepted 82-test/Python baseline**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
python_bin=/Users/jlsor/Documents/Research/SSR/.venv/bin/python
game_root="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
game_managed="$game_root/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="$game_root/BepInEx/core"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false \
  -p:GameManagedDir="$game_managed" -p:BepInExCoreDir="$bepinex_core"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- \
  --assembly "$game_managed/Assembly-CSharp.dll" \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll" \
  --mode-off-fixture \
  "$game_root/BepInEx/config/dev.jlsor.ssr.oracle.cfg"
PYTHONPATH="$PWD/src" "$python_bin" -m pytest -q
```

Require zero warnings/errors, exact single stdout line
`SSR oracle unit harness ready`, the old manifest count 82, and the current
Python counts. Capture stdout, stderr, status, source hash, HEAD, index tree,
tracked diff hash, untracked-name/content hash, and porcelain before/after.

---

### Task 1: Generalize schema-v1 Run and dynamic driver cardinality

**Files:**

- Modify `oracle/plugin/Core/OracleProtocol.cs`
- Modify `oracle/plugin/Core/CanonicalJson.cs`
- Modify `oracle/plugin/Core/PassiveDriver.cs`
- Modify `oracle/plugin/tests/ProtocolTests.cs`
- Modify `oracle/plugin/tests/EncodingTests.cs`
- Create `tests/fixtures/oracle_trace/replay-success.ndjson`

**Produces:** replay-aware Run/End records, two new record errors, positive
driver cardinality, and a driver readiness interface used in Task 3.

- [ ] **Step 1: Add the protocol/encoding RED registrations**

Append these exact identities:

```csharp
tests.Add("protocol", "run mode relations are exact", RunModeRelationsAreExact);
tests.Add("protocol", "dynamic driver count is bound to run", DynamicCountIsBoundToRun);
tests.Add("encoding", "replay run golden bytes", ReplayRunGoldenBytes);
```

`RunModeRelationsAreExact` constructs valid passive and replay Run records,
then rejects: Off; replay with null/uppercase/short hash; replay count 0; passive
non-null hash; passive count other than 3; and End count 0. It asserts the old
passive overload remains byte-identical.

`DynamicCountIsBoundToRun` constructs one driver with expected count 1 and a
replay Run count 1, then proves Prepare/Activate succeeds; a fresh driver with
expected count 2 rejects that Run before `WriteRun`. It also proves expected
count 0 is rejected by the constructor and passive still receives exactly 3.

Create `ProtocolSamples.ReplayRun` and `ProtocolSamples.ReplayEnd` with:

```csharp
internal const string ReplayInputSha256 =
    "f8ace91df3cf40e0410cd9da8df1a2859a5a1aba66e423ed4bd951ba3c14ba7a";
internal static readonly RunRecord ReplayRun = new RunRecord(
    RunId, OracleMode.Replay, OracleProtocol.ExpectedAssemblySha256,
    ReplayInputSha256, 1,
    new DateTime(2026, 7, 31, 19, 9, 50, DateTimeKind.Utc)
        .AddTicks(3199100));
internal static readonly EndRecord ReplayEnd = new EndRecord(
    RunId, 1,
    new DateTime(2026, 7, 31, 19, 11, 0, DateTimeKind.Utc));
```

`ReplayRunGoldenBytes` compares `CanonicalJson.EncodeRun(ReplayRun)` and the
four-record replay fixture line-for-line; it also culture-switches to `fr-FR`
and requires identical bytes.

- [ ] **Step 2: Run the focused production-unchanged RED**

Force-rebuild, then run `--cohort protocol` and `--cohort encoding`. Require the
first semantic failures to identify the absent `Replay` enum/constructor and
replay encoder path; record compile failures separately from semantic REDs.

- [ ] **Step 3: Implement exact mode/count relations**

Apply these shapes in `OracleProtocol.cs`:

```csharp
internal enum OracleMode { Off = 0, Passive = 1, Replay = 2 }

internal sealed class RunRecord
{
    internal RunRecord(string runId, string gameAssemblySha256,
        DateTime startedAtUtc)
        : this(runId, OracleMode.Passive, gameAssemblySha256,
            null, OracleProtocol.ExpectedInputCount, startedAtUtc)
    {
    }

    internal RunRecord(string runId, OracleMode mode,
        string gameAssemblySha256, string inputSha256,
        int expectedInputCount, DateTime startedAtUtc)
    {
        if (mode == OracleMode.Passive)
        {
            if (inputSha256 != null
                || expectedInputCount != OracleProtocol.ExpectedInputCount)
                throw new ArgumentException("invalid passive Run relation");
        }
        else if (mode == OracleMode.Replay)
        {
            OracleValidation.Sha256(inputSha256, "inputSha256");
            if (expectedInputCount <= 0)
                throw new ArgumentOutOfRangeException("expectedInputCount");
        }
        else
            throw new ArgumentOutOfRangeException("mode");
        SchemaVersion = OracleProtocol.SchemaVersion;
        RunId = OracleValidation.RunId(runId);
        Mode = mode;
        GameAssemblySha256 =
            OracleValidation.AssemblySha256(gameAssemblySha256);
        PluginVersion = OracleProtocol.PluginVersion;
        InputSha256 = inputSha256;
        ExpectedInputCount = expectedInputCount;
        StartedAtUtc = OracleValidation.Utc(startedAtUtc, "startedAtUtc");
    }

    // Keep the existing read-only properties unchanged.
}
```

Add `OracleValidation.Sha256(string value, string name)` using the existing
64-lowercase-hex predicate. Change `EndRecord` to require `inputCount > 0`.
Append the exact error rows to both the driver's closed array and
`OracleErrors`:

```csharp
new OracleError("initial_state_mismatch",
    "initial replay state did not match the configured signature"),
new OracleError("replay_alignment_failed",
    "replay input did not traverse the native call path")
```

Change the driver constructor check to `expectedInputCount <= 0`. Before
acquiring the output lease in `Prepare`, require
`run.ExpectedInputCount == expectedInputCount`; a mismatch throws
`ArgumentException("Run expected_input_count does not match driver")` and makes
zero sink calls.

- [ ] **Step 4: Encode replay without changing field order**

Replace only the hardcoded Run mode/hash portion in `CanonicalJson.EncodeRun`:

```csharp
WriteAscii(output, ",\"mode\":");
WriteString(output,
    record.Mode == OracleMode.Passive ? "passive" : "replay");
WriteAscii(output, ",\"game_assembly_sha256\":");
WriteString(output, record.GameAssemblySha256);
WriteAscii(output, ",\"plugin_version\":");
WriteString(output, record.PluginVersion);
WriteAscii(output, ",\"input_sha256\":");
if (record.InputSha256 == null)
    WriteAscii(output, "null");
else
    WriteString(output, record.InputSha256);
WriteAscii(output, ",\"expected_input_count\":");
```

All surrounding keys and punctuation remain in their current order.

Create `tests/fixtures/oracle_trace/replay-success.ndjson` through
`apply_patch` as strict UTF-8, no BOM, exactly these four LF-terminated lines:

```text
{"kind":"run","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","mode":"replay","game_assembly_sha256":"886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564","plugin_version":"0.3.0","input_sha256":"f8ace91df3cf40e0410cd9da8df1a2859a5a1aba66e423ed4bd951ba3c14ba7a","expected_input_count":1,"started_at_utc":"2026-07-31T19:09:50.3199100Z"}
{"kind":"initial","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":null,"capture":{"raw_save":"initial","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"step","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_index":0,"input":"West","accepted":true,"movement_scheduled":true,"settle_frames":2,"state_replaced":false,"capture":{"raw_save":"moved","state_identity":"17","level":"","overworld":false,"won":false,"returning":false,"have_ever_cooked_all":false,"lost_reason":"","display_name":"","sausages_cooked":0,"movement_count":0,"pushes_to_try":0}}
{"kind":"end","schema_version":1,"run_id":"0123456789abcdef0123456789abcdef","input_count":1,"finished_at_utc":"2026-07-31T19:11:00.0000000Z"}
```

The encoding test must prove production encoders reproduce every line exactly;
never regenerate the tracked fixture during test execution.

- [ ] **Step 5: Run focused and inherited GREEN**

Force-rebuild; run `protocol`, `encoding`, all four driver cohorts, `sink`, and
the full manifest. Require passive fixture bytes unchanged and no test count
other than the declared final manifest.

---

### Task 2: Parse immutable replay input and strict replay configuration

**Files:**

- Create `oracle/plugin/Core/ReplayInput.cs`
- Modify `oracle/plugin/Core/OracleConfiguration.cs`
- Modify `oracle/plugin/Core/PhysicalPath.cs`
- Modify `oracle/plugin/tests/ReplayInputTests.cs`
- Modify `oracle/plugin/tests/ConfigurationTests.cs`
- Modify `oracle/plugin/tests/PhysicalPathTests.cs`

- [ ] **Step 1: Register the six input, two config, and one path REDs**

```csharp
internal static class ReplayInputTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("replay-input", "exact bytes own hash and are immutable",
            ExactBytesOwnHashAndAreImmutable);
        tests.Add("replay-input", "all five tokens preserve file order",
            AllFiveTokensPreserveFileOrder);
        tests.Add("replay-input", "blank ASCII lines do not create tokens",
            BlankAsciiLinesDoNotCreateTokens);
        tests.Add("replay-input", "UTF8 BOM NUL and malformed text are rejected",
            InvalidTextIsRejected);
        tests.Add("replay-input", "unknown and empty streams are rejected",
            UnknownAndEmptyAreRejected);
        tests.Add("replay-input", "input source is read exactly once",
            InputSourceIsReadExactlyOnce);
    }
}
```

Append:

```csharp
tests.Add("config", "replay values and topology are exact",
    ReplayValuesAndTopologyAreExact);
tests.Add("config", "replay failures are typed before input read",
    ReplayFailuresAreTypedBeforeInputRead);
tests.Add("path", "existing regular files resolve canonically",
    ExistingFilesResolveCanonically);
```

The exact input matrix is:

| Case | Bytes | Result |
|---|---|---|
| Exact identity | `West\n` versus `West\r\n` | same token, different SHA-256 |
| Five names | `North\n South \n\tWest\t\nEast\nUndo\n` | five enum values in file order |
| Blank lines | `\n \t\r\f\v\nWest\n` | one token, index 0 |
| Invalid | UTF-8 BOM; `0xff`; embedded NUL; `North\rSouth` | `invalid_configuration` |
| Vocabulary | lowercase, numeric, `None`, trailing comment | `invalid_configuration` |
| Empty | empty bytes or whitespace-only | `invalid_configuration` |
| Source | null result or thrown read | one call; typed `invalid_configuration` retaining cause |

Mutating either the source array or a returned `Bytes`/`Tokens` copy must not
change stored bytes, hash, count, or token values.

- [ ] **Step 2: Capture the input/config RED**

Force-rebuild and run `replay-input`, `config`, and `path`. Require absent
`ReplayInput`, replay config rejection, and absent regular-file resolver as the
only new failures.

- [ ] **Step 3: Create `ReplayInput.cs` with this complete public shape**

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

internal interface IReplayInputBytes
{
    byte[] ReadAllBytes(string inputPath);
}

internal sealed class ReplayInput
{
    private static readonly UTF8Encoding StrictUtf8 =
        new UTF8Encoding(false, true);
    private readonly byte[] bytes;
    private readonly OracleInput[] tokens;

    private ReplayInput(byte[] exactBytes, OracleInput[] parsedTokens,
        string sha256)
    {
        bytes = exactBytes;
        tokens = parsedTokens;
        Sha256 = sha256;
    }

    internal int Count { get { return tokens.Length; } }
    internal string Sha256 { get; private set; }
    internal byte[] Bytes { get { return (byte[])bytes.Clone(); } }
    internal OracleInput this[int index] { get { return tokens[index]; } }
    internal OracleInput[] Tokens { get { return (OracleInput[])tokens.Clone(); } }

    internal static ReplayInput Load(string inputPath, IReplayInputBytes source)
    {
        if (String.IsNullOrEmpty(inputPath))
            throw Failure(new ArgumentException("inputPath is required"));
        if (source == null) throw new ArgumentNullException("source");
        byte[] value;
        try { value = source.ReadAllBytes(inputPath); }
        catch (Exception error) { throw Failure(error); }
        if (value == null)
            throw Failure(new IOException("input source returned null"));
        return Parse(value);
    }

    internal static ReplayInput Parse(byte[] sourceBytes)
    {
        try
        {
            if (sourceBytes == null)
                throw new ArgumentNullException("sourceBytes");
            byte[] exact = (byte[])sourceBytes.Clone();
            if (exact.Length >= 3 && exact[0] == 0xef
                && exact[1] == 0xbb && exact[2] == 0xbf)
                throw new FormatException("UTF-8 BOM is forbidden");
            string text = StrictUtf8.GetString(exact);
            if (text.IndexOf('\0') >= 0)
                throw new FormatException("NUL is forbidden");
            List<OracleInput> parsed = new List<OracleInput>();
            string[] lines = text.Split(new char[] { '\n' });
            for (int index = 0; index < lines.Length; index++)
            {
                string token = TrimAscii(lines[index]);
                if (token.Length == 0) continue;
                OracleInput input;
                if (!TryParseToken(token, out input))
                    throw new FormatException("unknown replay token");
                parsed.Add(input);
            }
            if (parsed.Count == 0)
                throw new FormatException("replay token stream is empty");
            return new ReplayInput(exact, parsed.ToArray(), Hash(exact));
        }
        catch (OracleConfigurationException) { throw; }
        catch (Exception error) { throw Failure(error); }
    }

    private static bool TryParseToken(string value, out OracleInput input)
    {
        if (value == "North") { input = OracleInput.North; return true; }
        if (value == "South") { input = OracleInput.South; return true; }
        if (value == "West") { input = OracleInput.West; return true; }
        if (value == "East") { input = OracleInput.East; return true; }
        if (value == "Undo") { input = OracleInput.Undo; return true; }
        input = OracleInput.North;
        return false;
    }

    private static string TrimAscii(string value)
    {
        int first = 0;
        int last = value.Length;
        while (first < last && IsAsciiWhitespace(value[first])) first++;
        while (last > first && IsAsciiWhitespace(value[last - 1])) last--;
        return value.Substring(first, last - first);
    }

    private static bool IsAsciiWhitespace(char value)
    {
        return value == ' ' || value == '\t' || value == '\r'
            || value == '\f' || value == '\v';
    }

    private static string Hash(byte[] value)
    {
        byte[] digest;
        using (SHA256 hash = SHA256.Create()) digest = hash.ComputeHash(value);
        StringBuilder text = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
            text.Append(digest[index].ToString("x2", CultureInfo.InvariantCulture));
        return text.ToString();
    }

    private static OracleConfigurationException Failure(Exception error)
    {
        return new OracleConfigurationException("invalid_configuration", error);
    }
}

internal sealed class FileReplayInputBytes : IReplayInputBytes
{
    public byte[] ReadAllBytes(string inputPath)
    {
        return File.ReadAllBytes(inputPath);
    }
}
```

- [ ] **Step 4: Add exact regular-file and replay config paths**

Add `ResolveExistingFile` beside `ResolveExistingDirectory`; it calls the same
two-scan `Resolve` and requires `Identity.Exists` and final kind `File`. Extend
`IConfigurationPathResolver` and `PhysicalConfigurationPathResolver` with
`ResolveExistingFile`.

Add immutable `ReplayConfiguration` with the same common active values plus
`InputPath` and `ExpectedInitialSha256`. `OracleConfiguration` gains nullable
`Replay` and constructor `(mode, passive, replay)`. Off sets both null; passive
sets Replay null.

The replay parser requires exactly:

```text
Mode
OutputDirectory
RunName
SaveDirectory
InputPath
MaxSettleFrames
MaxSettleSeconds
ExpectedInitialSha256
```

It requires `MaxSettleFrames=600`, `MaxSettleSeconds=30`, a safe RunName, and
ExpectedInitialSha256 either empty or exactly 64 lowercase hex digits. Resolve
in order: output directory, save directory, input file. Reject output/save
nesting, input equal to or beneath output, and input equal to or beneath save.
Return canonical `TracePath = Path.Combine(output, runName + ".ndjson")`.
Passive and Off key sets remain byte-for-byte compatible; replay keys are
rejected in passive.

- [ ] **Step 5: Run focused GREEN and full inherited config/path matrix**

Force-rebuild; run `replay-input`, `config`, `path`, `protocol`, `encoding`, and
full harness. Run net35 Core rebuild. Require no filesystem read from
`ReplayInput` during config parsing—the plugin owns the one later read.

---

### Task 3: Add the replay coordinator and deterministic state-machine tests

**Files:**

- Create `oracle/plugin/Core/ReplayCoordinator.cs`
- Create `oracle/plugin/tests/ReplayCoordinatorTests.cs`

**Interfaces:** `ReplayCoordinator` implements `IPassiveReporter`; it wraps the
mode-aware log reporter and attaches once to the one `PassiveDriver` through
`IReplayDriver`.

- [ ] **Step 1: Register the eight coordinator REDs**

```csharp
internal static class ReplayCoordinatorTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("replay-coordinator",
            "initial signature owns before Ready and arming",
            InitialSignatureOwnsBeforeReadyAndArming);
        tests.Add("replay-coordinator",
            "real neutral poll is required and physical input is suppressed",
            RealNeutralPollIsRequiredAndPhysicalInputIsSuppressed);
        tests.Add("replay-coordinator",
            "cardinal traverses one owning update",
            CardinalTraversesOneOwningUpdate);
        tests.Add("replay-coordinator",
            "missing duplicate and mismatched traversal fault",
            InvalidCardinalTraversalFaults);
        tests.Add("replay-coordinator",
            "Undo invokes once and Restore stays native",
            UndoInvokesOnceAndRestoreStaysNative);
        tests.Add("replay-coordinator",
            "refused cardinal remains one durable token",
            RefusedCardinalRemainsOneDurableToken);
        tests.Add("replay-coordinator",
            "advance waits for Ready and final Complete has no repeat",
            AdvanceWaitsForReadyAndFinalCompleteHasNoRepeat);
        tests.Add("replay-coordinator",
            "fault disable and late callbacks are inert",
            TerminalAndLateCallbacksAreInert);
    }
}
```

Use a `FakeReplayDriver` recording readiness queries/fault codes and a
`FakeReplayUpdateAccess` recording state/path/quiescence/Undo calls. No sleeps.
Every reentrancy subcase uses a callback and bounded `ManualResetEvent` barrier,
releases in `finally`, and joins every foreground thread within 5 seconds.

The eight bodies must prove these exact oracles:

| Test | Required assertions |
|---|---|
| Initial signature | hash exact UTF-8 `raw_save`; mismatch selects only `initial_state_mismatch`; downstream Ready absent; no arm; a Diagnostic/Dispose reentry cannot replace the owner |
| Neutral/suppression | every unarmed override returns `true`/raw 8; no native method; only matching postfix credits neutral; no arm before Ready + credit + ready driver |
| Cardinal | one update arm; first override raw matches token; one matching physical return and ProcessInput; UpdateReturned deasserts; second override raw 8 |
| Invalid cardinal | separate fixtures for missing poll, duplicate poll, missing ProcessInput, duplicate ProcessInput, mismatched raw, foreign state, and late ProcessInput; each sole code `replay_alignment_failed` |
| Undo | `InvokeUndo` once in UpdateEntered; exactly one UndoEntered/Returned; Restore may occur only inside; no cardinal override; no direct ProcessInput |
| Refused | Update traversal is still valid; no retry before Ready; Ready(1) advances once |
| Durable advancement | arming and UpdateReturned do not change index; Ready(n) changes it; Ready resets neutral credit; Complete on last pending token stops without Ready(count) |
| Terminal | Failed, Complete, failed driver claim, duplicate Ready, Dispose, and all late callbacks suppress override to None and produce no new downstream event |

- [ ] **Step 2: Run coordinator production-unchanged RED**

Force-rebuild and run `--cohort replay-coordinator`. Require missing production
type/member failures only.

- [ ] **Step 3: Create `ReplayCoordinator.cs` with these exact contracts**

```csharp
using System;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

internal interface IReplayDriver
{
    bool IsReadyForReplay(object stateReference, int completedInputs);
    bool TryFault(string code);
}

internal interface IReplayUpdateAccess
{
    bool TryGetState(object game, out object stateReference);
    bool VerifySavePath();
    bool IsQuiescent(object game, object stateReference);
    void InvokeUndo(object game);
}

internal sealed class ReplayCoordinator : IPassiveReporter, IDisposable
{
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
            throw new InvalidOperationException("replay driver already attached");
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
            return;
        if (access == null) throw new ArgumentNullException("access");
        object state;
        try
        {
            if (!access.TryGetState(game, out state) || state == null) return;
            if (!access.VerifySavePath()) { Fault("save_path_changed"); return; }
            if (!access.IsQuiescent(game, state)) return;
        }
        catch (CaptureException) { Fault("capture_failed"); return; }
        catch (Exception) { Fault("observer_exception"); return; }
        IReplayDriver value = RequireDriver();
        if (!value.IsReadyForReplay(state, tokenIndex)) return;

        armedInput = input[tokenIndex];
        armedState = state;
        updateActive = true;
        ready = false;
        neutralSinceStep = false;
        overrideIssued = false;
        physicalReturned = false;
        processCalls = 0;
        undoCalls = 0;
        undoReturned = false;
        restoreObserved = false;
        if (armedInput == OracleInput.Undo)
        {
            try { access.InvokeUndo(game); }
            catch { throw; }
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
            if (rawDirection == 8) neutralSinceStep = true;
            else Fault("replay_alignment_failed");
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

    internal void ProcessInputEntered(object stateReference, int rawDirection)
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
        { Fault("replay_alignment_failed"); return; }
        undoCalls++;
    }

    internal void UndoReturned()
    {
        if (Stopped) return;
        if (!updateActive || armedInput != OracleInput.Undo
            || undoCalls != 1 || undoReturned)
        { Fault("replay_alignment_failed"); return; }
        undoReturned = true;
    }

    internal void RestoreObserved()
    {
        if (Stopped) return;
        if (!updateActive || armedInput != OracleInput.Undo
            || undoCalls != 1 || undoReturned || restoreObserved)
        { Fault("replay_alignment_failed"); return; }
        restoreObserved = true;
    }

    internal void UpdateReturned()
    {
        if (Stopped || !updateActive) return;
        bool aligned = armedInput == OracleInput.Undo
            ? undoCalls == 1 && undoReturned
            : overrideIssued && physicalReturned && processCalls == 1;
        ClearActiveUpdate();
        if (!aligned) { Fault("replay_alignment_failed"); return; }
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
            { Fault("replay_alignment_failed"); return; }
            initialReady = true;
            if (expectedInitialSha256.Length != 0
                && HashRawSave(lastCapture.RawSave) != expectedInitialSha256)
            { Fault("initial_state_mismatch"); return; }
            tokenIndex = 0;
            ready = true;
            // CaptureObserved can prove this credit only after a synthetic
            // None was observed, while the real driver separately prevents
            // pre-epoch neutral state from producing a capture.
            neutralSinceStep = true;
            downstream.Ready(0);
            return;
        }
        if (!awaitingDurableStep || completedInputs != tokenIndex + 1
            || completedInputs >= input.Count)
        { Fault("replay_alignment_failed"); return; }
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
        { Fault("replay_alignment_failed"); return; }
        Stop();
        downstream.Complete();
    }

    public void Failed(string code)
    {
        if (Interlocked.Exchange(ref stopped, 1) != 0) return;
        ClearActiveUpdate();
        downstream.Failed(code);
    }

    public void Diagnostic(string message)
    {
        downstream.Diagnostic(message);
    }

    public void Dispose() { Stop(); }

    private bool Stopped { get { return Interlocked.CompareExchange(
        ref stopped, 0, 0) != 0; } }

    private IReplayDriver RequireDriver()
    {
        return Interlocked.CompareExchange(ref driver, null, null)
            ?? throw new InvalidOperationException("replay driver is not attached");
    }

    private void Fault(string code)
    {
        ClearActiveUpdate();
        IReplayDriver value = RequireDriver();
        if (!value.TryFault(code)) Stop();
    }

    private void Stop()
    {
        Interlocked.Exchange(ref stopped, 1);
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
    }

    private static string HashRawSave(string value)
    {
        if (value == null) throw new ArgumentNullException("value");
        byte[] digest;
        using (SHA256 hash = SHA256.Create())
            digest = hash.ComputeHash(StrictUtf8.GetBytes(value));
        StringBuilder text = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
            text.Append(digest[index].ToString("x2", CultureInfo.InvariantCulture));
        return text.ToString();
    }
}
```

The executor may split private validation helpers, but must preserve every
branch and external-callback boundary above. No monitor encloses access,
driver, downstream, or adapter calls. `Fault` selects ownership before any
Diagnostic.

After creating the interface, change the existing driver declaration to
`internal sealed partial class PassiveDriver : IDisposable, IReplayDriver` and
insert these explicit implementations in `PassiveDriver.cs`:

```csharp
bool IReplayDriver.IsReadyForReplay(
    object stateReference, int expectedCompletedInputs)
{
    lock (outputLeaseSync)
    {
        return IsObservationActive()
            && phase == PassivePhase.Ready
            && completedInputs == expectedCompletedInputs
            && Object.ReferenceEquals(stableState, stateReference)
            && outstandingUpdate == null
            && playerPoll == null
            && processInputContext == null
            && undoContext == null
            && !attemptPending;
    }
}

bool IReplayDriver.TryFault(string code)
{
    return TryFault(code);
}
```

- [ ] **Step 4: Run the coordinator GREEN and 20-run deterministic stress**

Force-rebuild, run the cohort once, then 20 times. Each iteration must exit 0,
write exactly `SSR oracle unit harness ready\n` to stdout, write zero stderr
bytes, and preserve pre-iteration HEAD/index/tracked/untracked/porcelain.

---

### Task 4: Compose replay through controller, hooks, adapter, and plugin

**Files:**

- Modify `oracle/plugin/Core/OracleRuntimeBoundaries.cs`
- Modify `oracle/plugin/Core/PassiveReporter.cs`
- Modify `oracle/plugin/Core/OracleController.cs`
- Modify `oracle/plugin/GameAdapter.cs`
- Modify `oracle/plugin/GameHooks.cs`
- Modify `oracle/plugin/Plugin.cs`
- Create `oracle/plugin/tests/ControllerReplayTests.cs`
- Modify `oracle/plugin/tests/PassiveReporterTests.cs`
- Modify `oracle/plugin/tests/AssemblySurfaceTests.cs`

- [ ] **Step 1: Register seven controller and four generalized surface REDs**

```csharp
internal static class ControllerReplayTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("controller-replay", "passive preserves native input",
            PassivePreservesNativeInput);
        tests.Add("controller-replay", "replay construction binds dynamic run",
            ReplayConstructionBindsDynamicRun);
        tests.Add("controller-replay", "capture reaches signature before Ready",
            CaptureReachesSignatureBeforeReady);
        tests.Add("controller-replay", "update alignment precedes driver observation",
            UpdateAlignmentPrecedesDriverObservation);
        tests.Add("controller-replay", "cardinal hook lifecycle is routed once",
            CardinalHookLifecycleIsRoutedOnce);
        tests.Add("controller-replay", "Undo uses adapter and existing hooks",
            UndoUsesAdapterAndExistingHooks);
        tests.Add("controller-replay", "failure and teardown never reissue input",
            FailureAndTeardownNeverReissueInput);
    }
}
```

Append:

```csharp
tests.Add("reporter", "mode aware markers are exact", ModeAwareMarkersAreExact);
tests.Add("assembly", "replay native ABI remains exact",
    delegate { ReplayNativeAbiRemainsExact(options.AssemblyPath); });
tests.Add("plugin", "adapter replay call surface is exact",
    delegate { AdapterReplayCallSurfaceIsExact(options.PluginPath); });
tests.Add("plugin", "player input override is replay only",
    delegate { PlayerInputOverrideIsReplayOnly(options.PluginPath); });
```

The controller tests use fake runtime/adapter/sink/reporter objects and the
real driver/coordinator. They drive two equal Initial captures, a real neutral
poll, one update, native hook callbacks, settling, and End. They assert exact
event order; no test calls a private driver state setter or game type.

- [ ] **Step 2: Capture controller/plugin REDs**

Force-build net10 and net35, then run `controller-replay`, `reporter`,
`assembly`, and `plugin`. Require production missing-member/surface failures.

- [ ] **Step 3: Generalize the reporter without changing passive text**

Keep the old constructor and add:

```csharp
internal PassiveLogReporter(IPassiveLog log, OracleMode mode,
    int expectedInputCount)
```

Require mode Passive or Replay, positive count, and passive count exactly 3.
Use lowercase `passive`/`replay` in these exact messages:

```text
SSR oracle <mode> trace ready: n/N
SSR oracle <mode> trace complete
SSR oracle <mode> trace failed: <code>
SSR oracle <mode> diagnostic: <detail>
```

Ready accepts `0 <= n < expectedInputCount`. Append the two new record errors
to the closed reporter test table. The one-argument constructor delegates to
Passive/3 and retains every old byte.

- [ ] **Step 4: Extend plain runtime boundaries and the game adapter**

Add only this method to `IOracleGameAdapter`:

```csharp
void InvokeUndo(object game);
```

Implement in `GameAdapter`:

```csharp
public void InvokeUndo(object gameValue)
{
    Game game = gameValue as Game;
    if (game == null) throw new CaptureException("missing game");
    try { game.DoUndo(); }
    catch (Exception error)
    { throw new CaptureException("native Undo failed", error); }
}
```

The metadata test must find exactly three direct game calls in `GameAdapter`:
`GameState.Moving()`, `GameState.Save(false,false)`, and `Game.DoUndo()`.
It must find zero direct calls to `GameState.ProcessInput` anywhere in the
plugin.

- [ ] **Step 5: Compose passive/replay controller modes**

Retain the existing passive constructor. Add a replay constructor accepting
`ReplayConfiguration`, already-loaded `ReplayInput`, adapter, runtime, and log.
Use one private constructor to set immutable mode/common fields.

In `CreateDriver`:

1. create the sink as today;
2. construct a mode-aware `PassiveLogReporter`;
3. for replay, construct `ReplayCoordinator(input,
   ExpectedInitialSha256, logReporter)` and use it as the driver's reporter;
4. construct `PassiveDriver` with 3 or `input.Count`; and
5. attach the driver once before returning it.

Add nested `AdapterReplayUpdateAccess : IReplayUpdateAccess`, delegating exact
state/path/quiescence calls and `InvokeUndo` to `IOracleGameAdapter`.

Route methods in this exact order:

```csharp
internal void UpdateEntered(object game)
{
    if (replayCoordinator != null)
        replayCoordinator.UpdateEntered(
            game, new AdapterReplayUpdateAccess(this));
}

internal void ObserveUpdate(object game)
{
    if (replayCoordinator != null)
        replayCoordinator.UpdateReturned();
    if (updateBoundary != null)
        updateBoundary.Observe(new AdapterUpdateObservation(this, game));
}

internal void UpdateThrew()
{
    try
    {
        if (replayCoordinator != null) replayCoordinator.UpdateThrew();
    }
    finally { driver.TryFault("game_method_exception"); }
}

internal bool TryOverridePlayerInput(out int rawDirection)
{
    if (replayCoordinator == null)
    { rawDirection = 8; return false; }
    return replayCoordinator.TryOverridePlayerInput(out rawDirection);
}

internal void PhysicalPollReturned(int raw)
{
    if (replayCoordinator != null)
        replayCoordinator.PhysicalPollReturned(raw);
    driver.PhysicalPollReturned(raw);
}

internal HookToken ProcessInputEntered(object state, int raw)
{
    if (replayCoordinator != null)
        replayCoordinator.ProcessInputEntered(state, raw);
    return driver.ProcessInputEntered(state, raw, runtime.NowSeconds());
}
```

`UndoEntered`, `RestoreObserved`, and `UndoReturned` notify the coordinator
first, then call the existing driver method. `ClearThrew` notifies the
coordinator only through `UpdateThrew`; typed Process/Undo cleanup remains the
driver's responsibility. `AdapterUpdateObservation.Capture` obtains one
capture, calls `ReplayCoordinator.CaptureObserved(capture)`, and returns the
same reference to the driver.

- [ ] **Step 6: Make only Playerinputstring replay-capable**

Replace `AllowNativePlayerInput` with an exception-contained getter:

```csharp
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
```

The Harmony prefix becomes:

```csharp
private static bool Prefix(ref Direction __result)
{
    int rawDirection;
    if (!GameHooks.TryOverridePlayerInput(out rawDirection)) return true;
    __result = (Direction)rawDirection;
    return false;
}
```

Postfix remains the sole `PhysicalPollReturned` path. Passive returns false
from the getter, so original method/result/exception remain untouched.

`GameUpdatePatch.Finalizer` must call `OracleController.UpdateThrew` as the
game-failure action; other finalizers continue to use `GameMethodFailed` and
return the identical original exception.

- [ ] **Step 7: Compose replay startup after one exact input read**

In `Plugin.Awake`, keep a bootstrap passive reporter only for unreadable mode.
After config parses:

- Off follows the existing capability-free branch.
- Passive constructs the old controller and old passive Run overload.
- Replay constructs `GameAdapter` and `OracleRuntimeHost`, calls
  `runtime.ValidateAssemblyAndPassiveContract()` before touching the input,
  then reads `ReplayInput.Load(configuration.Replay.InputPath,
  new FileReplayInputBytes())` exactly once. It constructs the replay
  controller and replay Run with the returned hash/count. `Start` performs its
  existing validation again before redirect/sink; the repeated validation is
  read-only and closes the interval between input read and startup mutation.

Replay input failure logs one marker-only `invalid_configuration`; it creates
no controller, sink, Run, patch, save redirect, or fallback. Both active modes
use the same assembly hash, Harmony owner, startup transaction, disposal, and
boot marker.

Once replay config is authenticated but before the input count is known, use
`new PassiveLogReporter(log, OracleMode.Replay, 1)` only for marker/diagnostic
failures. After input succeeds, the controller replaces it with the exact-count
reporter; the provisional reporter never receives Ready or Complete.

- [ ] **Step 8: Run focused GREEN, net35, and plugin surface verification**

Run forced net10/net35/plugin builds; all three new cohorts; `reporter`,
`boundary`, `observation`, `assembly`, `plugin`, all driver cohorts; and full
manifest. Require plugin output contains only `SsrOracle.Plugin.dll` and no PDB
or copied dependency DLL.

---

### Task 5: Generalize the Python reader and replay relational gate

**Files:**

- Modify `src/ssr_env/oracle_protocol.py`
- Modify `tests/test_oracle_protocol.py`
- Consume `tests/fixtures/oracle_trace/replay-success.ndjson`

- [ ] **Step 1: Add production-unchanged Python REDs**

Add tests for:

1. retaining `mode`, `plugin_version`, `input_sha256`, and dynamic count in
   `RunHeader`;
2. accepting the exact replay fixture structurally;
3. rejecting Off/unknown mode and invalid passive/replay Run relations;
4. accepting error traces with 0..count Steps and success only with count Steps;
5. parsing exact replay input bytes with the same UTF-8/BOM/NUL/ASCII trim
   grammar as C#;
6. `require_replay_success(trace, b"West\n")` accepting the fixture;
7. rejecting byte-hash mismatch, token count mismatch, index mismatch, and
   token mismatch;
8. proving `require_passive_success` still rejects replay and retains every old
   three-attempt relation;
9. CLI replay default requiring `--input`, structural-only requiring none, and
   passive CLI output unchanged; and
10. golden replay fixture exact LF/no BOM bytes.

Run only these tests and require the current passive-only decoder/gate failures.

- [ ] **Step 2: Extend immutable Python models and Run decoder**

Use:

```python
ModeName = Literal["passive", "replay"]

@dataclass(frozen=True, slots=True)
class RunHeader:
    run_id: str
    game_assembly_sha256: str
    started_at_utc: str
    mode: ModeName = "passive"
    plugin_version: str = "0.3.0"
    input_sha256: str | None = None
    expected_input_count: int = EXPECTED_INPUT_COUNT
```

`_decode_run` retains all fields and validates:

```python
mode = cast(str, values["mode"])
input_sha256 = cast(str | None, values["input_sha256"])
expected_count = _located(
    reader,
    lambda: _nonnegative(
        cast(int, values["expected_input_count"]),
        field="expected_input_count",
    ),
)
if mode == "passive":
    if input_sha256 is not None or expected_count != EXPECTED_INPUT_COUNT:
        _record_error(reader, "passive Run relation is not canonical")
elif mode == "replay":
    if input_sha256 is None:
        _record_error(reader, "replay input_sha256 is required")
    _located(reader, lambda: _validate_hash(input_sha256, field="input_sha256"))
    if expected_count <= 0:
        _record_error(reader, "replay expected_input_count must be positive")
else:
    _record_error(reader, "mode must be 'passive' or 'replay'")
```

Keep plugin version exactly `0.3.0` and the reviewed assembly hash.

- [ ] **Step 3: Make structural sequence count header-driven**

Replace every structural hardcoded three with
`header.expected_input_count`. Error may appear after any prefix no longer than
that count; End requires exact count in both Steps and `input_count`. Preserve
all run-id, timestamp, contiguous-index, record-size, capture, and Error-index
checks.

- [ ] **Step 4: Add exact input parser and replay gate**

```python
import hashlib

def _parse_replay_input(payload: bytes) -> tuple[InputName, ...]:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise OracleProtocolError("replay input UTF-8 BOM is forbidden")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise OracleProtocolError("replay input is not strict UTF-8") from exc
    if "\x00" in text:
        raise OracleProtocolError("replay input NUL is forbidden")
    tokens: list[InputName] = []
    for line in text.split("\n"):
        token = line.strip(" \t\r\f\v")
        if not token:
            continue
        if token not in INPUT_NAMES:
            raise OracleProtocolError("replay input token is not canonical")
        tokens.append(cast(InputName, token))
    if not tokens:
        raise OracleProtocolError("replay input token stream is empty")
    return tuple(tokens)

def require_replay_success(trace: OracleRun, input_bytes: bytes) -> None:
    if trace.header.mode != "replay":
        raise OracleProtocolError("replay success requires replay mode")
    if trace.outcome != "success" or not isinstance(trace.terminal, EndRecord):
        raise OracleProtocolError("replay success requires an end record")
    if trace.initial is None:
        raise OracleProtocolError("replay success requires an initial record")
    tokens = _parse_replay_input(input_bytes)
    digest = hashlib.sha256(input_bytes).hexdigest()
    if digest != trace.header.input_sha256:
        raise OracleProtocolError("replay input SHA-256 does not match Run")
    if len(tokens) != trace.header.expected_input_count:
        raise OracleProtocolError("replay token count does not match Run")
    if len(trace.steps) != len(tokens):
        raise OracleProtocolError("replay success step count is incomplete")
    if trace.terminal.input_count != len(tokens):
        raise OracleProtocolError("replay end count does not match input")
    for index, (step, token) in enumerate(zip(trace.steps, tokens)):
        if step.input_index != index or step.input != token:
            raise OracleProtocolError("replay Step does not match input token")
        if step.state_replaced:
            raise OracleProtocolError("replay state_replaced must be false")
```

Append these exact Python schema rows before running structural Error tests:

```python
"initial_state_mismatch": (
    "initial replay state did not match the configured signature"
),
"replay_alignment_failed": (
    "replay input did not traverse the native call path"
),
```

At the start of `require_passive_success`, require
`trace.header.mode == "passive"`, null input hash, and expected count 3.

Add `--input Path` to the CLI. For a successful replay trace, default mode
requires `--input`, reads that file once as bytes, and calls
`require_replay_success`; `--structural-only` never opens input. Passive ignores
an absent input and rejects a supplied input as a usage-level protocol error.

- [ ] **Step 5: Run Python focused and complete GREEN**

```bash
set -e
python_bin=/Users/jlsor/Documents/Research/SSR/.venv/bin/python
PYTHONPATH="$PWD/src" "$python_bin" -m pytest \
  tests/test_oracle_protocol.py -q
PYTHONPATH="$PWD/src" "$python_bin" -m pytest -q
```

Record exact pass/xfail/xpass counts and prove passive fixture/CLI output bytes
unchanged.

---

### Task 6: Freeze the exact 113-test manifest and run full offline verification

**Files:**

- Modify `oracle/plugin/tests/TestSupport.cs`
- Modify `oracle/plugin/tests/Program.cs`
- Evidence only thereafter

- [ ] **Step 1: Append exact registry identities**

In `ApprovedManifest`, retain all 82 entries in place. Insert the new identities
at the matching registration positions and append the three new cohorts in this
order: `replay-input`, `replay-coordinator`, `controller-replay`. Do not sort or
rename inherited identities.

Register new classes in `Program` after `PassiveDriverTests` and before
configuration/controller surface tests. Use this exact count map:

```csharp
{ "protocol", 6 },
{ "encoding", 6 },
{ "sink", 6 },
{ "driver-boundary", 2 },
{ "driver-initial", 8 },
{ "driver-input", 8 },
{ "driver-terminal", 6 },
{ "replay-input", 6 },
{ "replay-coordinator", 8 },
{ "controller-replay", 7 },
{ "config", 8 },
{ "path", 7 },
{ "observation", 5 },
{ "boundary", 5 },
{ "startup", 7 },
{ "reporter", 5 },
{ "assembly", 5 },
{ "plugin", 8 }
```

The sum must be 113. `RegistryManifestIsExact` must still kill missing,
reordered, renamed, duplicate, and balanced cohort-swap variants.

- [ ] **Step 2: Run every exact C# cohort**

Force one build, then run all 18 named cohorts one at a time with literal game
assembly/plugin/mode-off fixture options. Each run must emit exactly the ready
line and empty stderr. Run the unfiltered harness and require 113.

- [ ] **Step 3: Run the full offline matrix**

Run forced net10, net35 Core, and net35 plugin rebuilds; full C#; complete
Python. Require W0/E0, exact manifest, green Python counts, no installed writes,
no process launch, no source/index drift, and plugin Release output containing
only the plugin DLL.

- [ ] **Step 4: Stress replay/controller deterministically**

Run each of `replay-coordinator` and `controller-replay` 20 times. Capture each
status/stdout/stderr separately and byte-compare stdout with:

```bash
printf 'SSR oracle unit harness ready\n' | cmp -s - "$stdout_path"
test ! -s "$stderr_path"
```

Snapshot and compare HEAD, `git write-tree`, tracked diff bytes, untracked
names/content, and porcelain around the complete stress.

---

### Task 7: Qualify six lean replay mutations

Use a fresh `git clone --no-hardlinks` for each mutation. Overlay the exact
candidate paths, copy ignored `obj` directories (never hardlink), prove inode
difference, force a primary GREEN immediately before each clone, apply one
mutation, force-build the clone, run one focused cohort, record the first exact
failure, then remove only the validated disposable root. Never reuse a mutant.

| Mutation | Exact edit | Required first RED |
|---|---|---|
| M1 exact bytes | hash strict decoded/normalized token text instead of source bytes | `replay-input/exact bytes own hash and are immutable` |
| M2 initial signature | bypass the nonempty expected hash comparison | `replay-coordinator/initial signature owns before Ready and arming` |
| M3 physical suppression | return false/native when replay is unarmed | `controller-replay/passive preserves native input` or the replay half's exact suppression assertion |
| M4 one-update deassertion | omit `ClearActiveUpdate()` from successful UpdateReturned | `replay-coordinator/cardinal traverses one owning update` |
| M5 alignment | accept a mismatched ProcessInput raw direction | `replay-coordinator/missing duplicate and mismatched traversal fault` |
| M6 durable advancement | increment `tokenIndex` in UpdateEntered before Step/Ready | `replay-coordinator/advance waits for Ready and final Complete has no repeat` |

For M3, the focused oracle must include both passive returning native and replay
returning None; report the replay-specific assertion as the intended kill. A
mutation that fails to compile or dies in an unrelated inherited test is not
qualified.

After all six, require six absent clone roots, fresh primary full GREEN, and
unchanged candidate bytes.

---

### Task 8: Review, commit, and reauthenticate the offline implementation

- [ ] **Step 1: Create a complete review package**

Capture the exact candidate status, path list, hashes, complete binary/full-index
`git diff -U10`, design/plan identities, RED/GREEN logs, 113 manifest, Python
counts, stress, mutation table, no-launch proof, and preservation state in the
ignored evidence root.

- [ ] **Step 2: Obtain two scoped precommit reviews**

One independent specification reviewer traces every design relation, native
path, failure owner, manifest, mutation, and live-gate boundary. One independent
quality reviewer inspects concurrency/reentrancy, C#7.3/net35, callback order,
test sensitivity, Python reader compatibility, and exact scope. Require both
`APPROVE C0/I0/M0`. Correct findings append-only, rerun affected/full matrices,
stress, mutations, and both reviews.

- [ ] **Step 3: Commit exactly once**

```bash
git diff --check
git add \
  oracle/plugin/Core/ReplayInput.cs \
  oracle/plugin/Core/ReplayCoordinator.cs \
  oracle/plugin/Core/OracleProtocol.cs \
  oracle/plugin/Core/CanonicalJson.cs \
  oracle/plugin/Core/OracleConfiguration.cs \
  oracle/plugin/Core/PhysicalPath.cs \
  oracle/plugin/Core/OracleRuntimeBoundaries.cs \
  oracle/plugin/Core/PassiveReporter.cs \
  oracle/plugin/Core/PassiveDriver.cs \
  oracle/plugin/Core/OracleController.cs \
  oracle/plugin/GameAdapter.cs \
  oracle/plugin/GameHooks.cs \
  oracle/plugin/Plugin.cs \
  oracle/plugin/tests/ReplayInputTests.cs \
  oracle/plugin/tests/ReplayCoordinatorTests.cs \
  oracle/plugin/tests/ControllerReplayTests.cs \
  oracle/plugin/tests/ProtocolTests.cs \
  oracle/plugin/tests/EncodingTests.cs \
  oracle/plugin/tests/ConfigurationTests.cs \
  oracle/plugin/tests/PhysicalPathTests.cs \
  oracle/plugin/tests/PassiveReporterTests.cs \
  oracle/plugin/tests/AssemblySurfaceTests.cs \
  oracle/plugin/tests/TestSupport.cs \
  oracle/plugin/tests/Program.cs \
  src/ssr_env/oracle_protocol.py \
  tests/test_oracle_protocol.py \
  tests/fixtures/oracle_trace/replay-success.ndjson
git diff --cached --check
git commit -m "feat: replay SSR inputs through native game path"
```

Reject any staged path outside this list. Record the exact committed path list
and blob closure.

- [ ] **Step 4: Build an immutable package and rerun**

Create an ignored immutable full-index/binary package from plan parent through
implementation tip. Prove extracted body byte-equals a fresh diff and all
committed/live blobs match. Rerun full builds, 18 cohorts, full 113 C#, Python,
20x replay stress, and six mutations at immutable tip.

- [ ] **Step 5: Obtain immutable postcommit reviews**

Require two fresh reviews at the immutable commit with `APPROVE C0/I0/M0` and
clean repository/index. Only then may Task 9 perform read-only live preflight.

---

### Task 9: Prepare the reviewed one-use live runbook and preflight

This task is read-only with respect to installed game/plugin/config/save state.
It may copy bytes into the ignored evidence root. It must not deploy or launch.

- [ ] **Step 1: Allocate and validate the unique ignored gate root**

Use `mktemp -d` beneath exact ignored parent
`$PWD/data/oracle/task6-2-replay-gate`. Resolve it, prove it is beneath that
parent, and create non-nested siblings:

```text
approvals/
baseline-save/
post-passive-save/
live-save/
output/
input/
installed-backup/
logs/
manifests/
evidence/
```

Record the literal root and never infer it from a broad glob.

- [ ] **Step 2: Create a reviewed ignored tree-manifest helper**

Create `gate_tree_manifest.py` inside that root (never stage it) with this exact
one-use implementation:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

MAX_DESCENDANTS = 4096
MAX_FILE_BYTES = 256 * 1024 * 1024
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK

class ManifestError(RuntimeError):
    pass

def _identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
    )

def _safe_name(name: str) -> bytes:
    if name in {"", ".", ".."} or "/" in name or "\x00" in name:
        raise ManifestError("unsafe relative name")
    try:
        return name.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ManifestError("relative name is not strict UTF-8") from exc

def _scan_present(root: Path) -> dict[str, object]:
    total = 0
    entries: list[dict[str, object]] = []
    root_fd = os.open(root, DIRECTORY_FLAGS)
    try:
        root_before = os.fstat(root_fd)
        if not stat.S_ISDIR(root_before.st_mode):
            raise ManifestError("root is not a directory")
        entries.append({
            "path": ".",
            "kind": "directory",
            "mode": stat.S_IMODE(root_before.st_mode),
            "byte_count": 0,
            "sha256": None,
        })

        def visit(directory_fd: int, prefix: str) -> None:
            nonlocal total
            directory_before = os.fstat(directory_fd)
            names = os.listdir(directory_fd)
            names.sort(key=_safe_name)
            for name in names:
                _safe_name(name)
                relative = name if prefix == "" else prefix + "/" + name
                if len(entries) - 1 >= MAX_DESCENDANTS:
                    raise ManifestError("tree exceeds descendant bound")
                observed = os.stat(
                    name, dir_fd=directory_fd, follow_symlinks=False
                )
                if stat.S_ISDIR(observed.st_mode):
                    child_fd = os.open(
                        name, DIRECTORY_FLAGS, dir_fd=directory_fd
                    )
                    try:
                        opened = os.fstat(child_fd)
                        if _identity(opened) != _identity(observed):
                            raise ManifestError("directory changed before open")
                        entries.append({
                            "path": relative,
                            "kind": "directory",
                            "mode": stat.S_IMODE(opened.st_mode),
                            "byte_count": 0,
                            "sha256": None,
                        })
                        visit(child_fd, relative)
                        if _identity(os.fstat(child_fd)) != _identity(opened):
                            raise ManifestError("directory changed during scan")
                    finally:
                        os.close(child_fd)
                elif stat.S_ISREG(observed.st_mode):
                    file_fd = os.open(name, FILE_FLAGS, dir_fd=directory_fd)
                    try:
                        opened = os.fstat(file_fd)
                        if _identity(opened) != _identity(observed):
                            raise ManifestError("file changed before open")
                        digest = hashlib.sha256()
                        count = 0
                        while True:
                            chunk = os.read(file_fd, 1024 * 1024)
                            if not chunk:
                                break
                            count += len(chunk)
                            total += len(chunk)
                            if total > MAX_FILE_BYTES:
                                raise ManifestError("tree exceeds byte bound")
                            digest.update(chunk)
                        if count != opened.st_size:
                            raise ManifestError("file size changed while read")
                        if _identity(os.fstat(file_fd)) != _identity(opened):
                            raise ManifestError("file changed during read")
                        entries.append({
                            "path": relative,
                            "kind": "file",
                            "mode": stat.S_IMODE(opened.st_mode),
                            "byte_count": count,
                            "sha256": digest.hexdigest(),
                        })
                    finally:
                        os.close(file_fd)
                else:
                    raise ManifestError("symlink or special file is forbidden")
            if _identity(os.fstat(directory_fd)) != _identity(directory_before):
                raise ManifestError("directory changed during enumeration")

        visit(root_fd, "")
        if _identity(os.fstat(root_fd)) != _identity(root_before):
            raise ManifestError("root changed during scan")
    finally:
        os.close(root_fd)
    entries[1:] = sorted(
        entries[1:], key=lambda row: str(row["path"]).encode("utf-8")
    )
    return {"schema_version": 1, "root_kind": "directory", "entries": entries}

def scan(root: Path) -> dict[str, object]:
    try:
        observed = os.lstat(root)
    except FileNotFoundError:
        return {"schema_version": 1, "root_kind": "absent", "entries": []}
    if stat.S_ISLNK(observed.st_mode):
        raise ManifestError("root symlink is forbidden")
    if not stat.S_ISDIR(observed.st_mode):
        raise ManifestError("root must be a directory or absent")
    return _scan_present(root)

def encoded(value: dict[str, object]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )

def publish(root: Path, output: Path) -> None:
    first = encoded(scan(root))
    second = encoded(scan(root))
    if first != second:
        raise ManifestError("two tree scans differ")
    descriptor = os.open(
        output,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    try:
        written = 0
        while written < len(first):
            written += os.write(descriptor, first[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args(argv)
    if not arguments.root.is_absolute() or not arguments.output.is_absolute():
        raise ManifestError("root and output must be absolute")
    publish(arguments.root, arguments.output)
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
```

Add a separate ignored `test_gate_tree_manifest.py` that imports this file and
uses fresh temporary roots to assert: canonical regular tree; absent leaf;
symlink and FIFO rejection; replacement/mtime instability; 4,097 descendants;
256 MiB plus one byte; and UTF-8 byte ordering. Run it with the pinned Python.
Only after those tests pass, manifest each real save twice into two create-new
paths and require `cmp -s`.

- [ ] **Step 3: Authenticate immutable implementation and installed baseline**

Record and require:

- exact implementation commit/package/review hashes and clean Git/index;
- exact reviewed Release DLL SHA-256;
- installer `status` healthy with zero changed/missing entries;
- pinned app, `Assembly-CSharp.dll`, runtime archive, preloader, BepInEx,
  Harmony, wrapper, manifest, config, and installed plugin identities;
- config is strict UTF-8/LF and parses exact Mode `off`;
- installed plugin/config are manifest-owned regular non-symlink files;
- exact pre-gate copies/hashes in `installed-backup`;
- no SSR/wrapper process identified by executable path or retained PID/PGID;
- passive/replay trace targets absent.

Use:

```bash
PYTHONPATH="$PWD/src" "$python_bin" tools/oracle_install.py status \
  --game-root "$game_root"
```

No unhealthy status authorizes repair.

- [ ] **Step 4: Snapshot ordinary and isolated save baselines**

The ordinary save is the literal path
`/Users/jlsor/Library/Application Support/unity.increpare games/Sausage`.
Record whether the leaf is absent. If present, two scans must byte-match; copy
it no-follow into evidence and scan the copy to the same manifest.

Select the live isolated save only from an explicit user-reviewed source.
Copy it into `baseline-save`, create `live-save` as a separate copy, and prove
all three initial manifests equal. Reject overlap with ordinary save, output,
input, worktree, or installed game. Do not fall back to ordinary save.

- [ ] **Step 5: Freeze exact launch/cleanup commands without running them**

The only publisher is:

```bash
PYTHONPATH="$PWD/src" "$python_bin" tools/oracle_install.py deploy \
  --game-root "$game_root" --plugin "$reviewed_dll" --config "$config_path"
```

The launcher is the exact manifest-owned `$game_root/run_bepinex.sh`. Create
one ignored `gate_launch_once.py` with this body:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--game-root", type=Path, required=True)
parser.add_argument("--record", type=Path, required=True)
parser.add_argument("--stdout", type=Path, required=True)
parser.add_argument("--stderr", type=Path, required=True)
arguments = parser.parse_args()
game_root = arguments.game_root.resolve(strict=True)
wrapper = game_root / "run_bepinex.sh"
observed = os.lstat(wrapper)
if not stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
    raise RuntimeError("wrapper is not an owned regular file")
stdout = arguments.stdout.open("xb", buffering=0)
stderr = arguments.stderr.open("xb", buffering=0)
try:
    process = subprocess.Popen(
        [str(wrapper)],
        cwd=game_root,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        start_new_session=True,
        close_fds=True,
    )
    pgid = os.getpgid(process.pid)
    if pgid != process.pid:
        raise RuntimeError("launcher did not create a new process group")
    payload = {
        "pid": process.pid,
        "pgid": pgid,
        "wrapper": str(wrapper),
        "game_root": str(game_root),
    }
    descriptor = os.open(
        arguments.record,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
    )
    try:
        body = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8") + b"\n"
        os.write(descriptor, body)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
finally:
    stdout.close()
    stderr.close()
```

Invoke it once per approval with four explicit absolute create-new paths. The
recorded PID must equal PGID. Before signaling, read the record once, require
positive integers, query `/bin/ps -axo pid=,pgid=,command=`, and reject any
row with that PGID whose command is not the exact wrapper, Sausage executable,
or a path beneath the authenticated game root. Signal only
`os.killpg(pgid, signal.SIGTERM)`, poll group absence for at most 20 seconds,
then re-run the same membership authentication before optional
`os.killpg(pgid, signal.SIGKILL)`. Never use `pkill`, `killall`, a name-only
target, or a PID/PGID from discovery rather than the create-new record.

Review these literal commands and all resolved paths/hashes before Task 10.

---

### Task 10: Stop for approval one, then run passive calibration once

- [ ] **Step 1: Present the approval-one packet and stop**

Report: immutable commit/package/reviews; reviewed DLL hash; healthy installer;
exact off plugin/config backup hashes; ordinary/isolated manifests; literal
passive config; absent trace; launch command; timeout; exact three user actions;
and cleanup command. Ask:

> Approve exactly one passive calibration deployment and game launch using the
> authenticated isolated save and reviewed cleanup transaction?

Do not continue until the user explicitly approves this packet.

- [ ] **Step 2: Deploy passive config transactionally**

Create the canonical source config with LF-only strict UTF-8:

```ini
[Oracle]
Mode=passive
OutputDirectory=<literal gate output path>
RunName=<literal unique passive stem>
SaveDirectory=<literal live isolated save path>
ExpectedPassiveInputs=3
MaxSettleFrames=600
MaxSettleSeconds=30
```

Use the reviewed deploy command. Immediately require healthy status, candidate
DLL hash, exact config bytes, isolated/ordinary save pre-launch equality,
absent trace, and no process.

- [ ] **Step 3: Launch once and guide the three attempts**

Launch into a new retained process group and record PID/PGID before interacting.
Monitor only bounded canonical BepInEx logs and the unique trace. The user:

1. loads the isolated state;
2. waits for `passive trace ready: 0/3`, performs one accepted cardinal, and
   waits for `1/3`;
3. performs one refused cardinal, waits for `2/3`;
4. performs Undo; and
5. closes the game after Complete.

Do not synthesize keys or silently retry. Timeout or wrong marker invokes exact
cleanup and ends this approval.

- [ ] **Step 4: Validate and preserve passive evidence**

Require retained process group absent. Open the trace once and call
`require_passive_success`. Prove accepted moved Step 0, refused Step 1 with
complete capture equal Step 0, accepted Undo Step 2 equal Initial, exact End 3,
reviewed assembly/plugin relation, no Error, and no extra record. Hash and copy
the trace/logs; copy post-passive live save to `post-passive-save`; do not delete
either.

Obtain an independent evidence/spec review before restoration. A failure marks
the operational gate failed/pending; it does not authorize another launch.

---

### Task 11: Derive replay input and restore the approval-two checkpoint

- [ ] **Step 1: Derive, never guess, exact replay values**

From the authenticated passive trace derive:

- Step 0 token; require accepted, non-Undo, movement scheduled true;
- exact input bytes `Token + "\n"` and SHA-256;
- expected Initial hash from exact UTF-8 bytes of
  `Initial.capture.raw_save`.

Create the `.dem` in the ignored `input` sibling via `apply_patch`, then compare
its bytes/hash with the derivation. Do not normalize the passive trace.

- [ ] **Step 2: Restore isolated save through explicit siblings**

Move the current `live-save` to a unique quarantine sibling. Copy
`baseline-save` to a new create-only `live-save`. Scan twice and require exact
pre-gate manifest equality before any deployment. Never recursively delete a
save or overwrite the quarantine.

- [ ] **Step 3: Restore exact pre-gate plugin/config and Off mode**

Deploy the exact backed-up plugin and config through the installer. Require
healthy status, exact pre-gate bytes/hashes, parsed Mode off, process absence,
ordinary-save equality/absence, restored isolated equality, passive evidence
unchanged, candidate commit/DLL unchanged, and absent replay trace.

- [ ] **Step 4: Produce the approval-two packet**

Include all approval-one evidence/review, restored hashes/manifests, derived
token/input bytes/hash, Initial hash, literal replay config, absent target,
launch/timeout/cleanup, and the instruction that the user supplies no gameplay
input.

---

### Task 12: Stop for approval two, then run one replay and restore final state

- [ ] **Step 1: Ask and stop**

Ask:

> Approve exactly one replay deployment and game launch for the single derived
> cardinal, with no user gameplay input, followed by exact isolated-save and
> Mode-off installed-state restoration?

Do not infer approval from approval one or plan approval.

- [ ] **Step 2: Deploy exact replay config and launch once**

The canonical config is:

```ini
[Oracle]
Mode=replay
OutputDirectory=<literal gate output path>
RunName=<literal unique replay stem>
SaveDirectory=<literal restored live isolated save path>
InputPath=<literal derived .dem path>
MaxSettleFrames=600
MaxSettleSeconds=30
ExpectedInitialSha256=<literal derived lowercase hash>
```

Deploy transactionally; reauthenticate; launch one retained process group. The
user loads the same isolated state and supplies no gameplay input. The plugin
must authenticate Initial, consume a real neutral poll, assert one cardinal for
one update, observe one matching ProcessInput, settle one Step, and Complete.

- [ ] **Step 3: Validate the one-input relation**

Require process group absent and exact Run/Initial/Step0/End only. Call
`require_replay_success(trace, input_bytes)` and additionally prove:

- mode replay, input hash derived, expected/end count 1;
- Initial raw save exactly passive Initial raw save;
- Step input equals calibrated cardinal, accepted true, movement true;
- Step capture equals passive Step 0 for raw save and every stable field,
  excluding only `state_identity`;
- no Error, duplicate token, extra Ready, or trailing bytes.

Obtain an independent evidence/spec review.

- [ ] **Step 4: Restore exact save and installed state**

Quarantine post-replay live save; recreate from baseline; require manifest
equality. Deploy exact pre-gate DLL/config; require healthy Mode off and exact
hashes. Reauthenticate ordinary save equality/absence, app/assembly/runtime,
wrapper, installer ownership, candidate Git/package/DLL, trace/input/log hashes,
clean repository/index, and zero process.

If restoration cannot be proven, stop with all forensic artifacts preserved;
do not attempt a broader repair or claim operational success.

- [ ] **Step 5: Write the final Task 6.2 gate report**

The report must distinguish:

- `implementation accepted`;
- `operational gate passed`, `pending`, or `failed`;
- both approval texts/timestamps;
- immutable implementation/review identities;
- calibration and replay trace relations/hashes;
- final save/installed/process/Git authentication; and
- every deviation, timeout, cleanup, or preserved quarantine path.

Do not commit the report unless a later explicit documentation task defines a
tracked report scope and review gate.

## Plan self-review checklist

- [ ] Every Task 6.2 design section maps to a task above.
- [ ] Every new Core interface has an exact signature and owner.
- [ ] Every new C# cohort has exact registrations, count, and assertions.
- [ ] Final manifest arithmetic is 113 and preserves all 82 inherited entries.
- [ ] Passive wire/log/config/native behavior remains explicitly protected.
- [ ] Replay Run/count/hash relations agree across C#, fixture, and Python.
- [ ] Coordinator advancement occurs only in Ready and final Complete repeats no
  token.
- [ ] Cardinal and Undo use only the accepted native paths.
- [ ] No callback holds a monitor across external code.
- [ ] Offline tasks contain no deployment, save write, or launch.
- [ ] Approval one and approval two are separate terminal stops.
- [ ] Cleanup targets only the retained process group and explicit sibling
  paths; no broad destructive command appears.
- [ ] The implementation commit scope/subject is exact and operational evidence
  remains ignored.
- [ ] No placeholder, TODO, ellipsis-as-instruction, or historical-patch
  dependency remains.
