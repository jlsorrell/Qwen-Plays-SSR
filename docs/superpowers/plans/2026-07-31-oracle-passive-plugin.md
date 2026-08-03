# SSR Passive Observation Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `0.1.0` compatibility-only plugin with a reproducible `0.2.0` BepInEx plugin that passively observes exactly three native inputs and writes the game's settled schema-v1 state without modifying game control flow.

**Architecture:** Unity-free protocol, encoder, sink, configuration, state-machine, capture/gate policy, startup policy, and hook-boundary code lives under `oracle/plugin/Core/` and is linked directly into the dependency-minimal test harness. `GameAdapter`, `PassivePatches`, and `PassiveController` form a thin game-facing shell: the adapter alone reads Unity/game state, Harmony callbacks only translate native events into core calls, and the controller owns startup resources and owner-scoped unpatching. `PassiveDriver` is the sole trace-session owner: it writes and closes the sink, arbitrates the first terminal transition, and emits progress/completion/failure through `IPassiveReporter`.

**Tech Stack:** C# 7.3, .NET Framework 3.5 plugin target, .NET 10 dependency-minimal executable test harness, BepInEx 5.4.23.5, HarmonyX 2.9.0, Unity 2018.4.25f1, `System.Reflection.Metadata` for metadata-only assembly checks.

## Global Constraints

- The authoritative design is `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`, especially sections 5-8 and 11-12.
- Complete this plan offline. Do not deploy to, mutate, or launch the installed game.
- Every `uv` invocation in this plan sets `UV_OFFLINE=1`. A cache miss is a
  hard failure; it never authorizes dependency acquisition or network access.
- Execute every multi-command gate in a fail-fast Bash process beginning with
  `set -euo pipefail`, or issue each command separately and check its exit
  status before continuing. A later successful command never masks an earlier
  restore, build, test, or hash failure.
- Preserve Mode-off behavior: read existing config bytes without `Config.Bind` or save, require only the original three compatibility methods, emit exactly `SSR oracle boot probe loaded`, and install no patches, sink, or save redirect.
- The ignored Mode-off fixture must retain SHA-256 `cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d` and remain byte-identical across plugin startup/destruction.
- Passive mode requires the exact seven-key configuration and fixed values from design section 6. Reject `replay` and every other mode.
- The plugin version is exactly `0.2.0`; schema version is `1`; expected input count is `3`; frame/time limits are `600` and `30` seconds; assembly SHA-256 is `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`.
- Never call a gameplay transition method. Observation may call only `GameState.Moving()` and `GameState.Save(false, false)` in the specified contexts.
- Every Harmony prefix/postfix is `void`, never skips an original, never changes a game argument or result, and catches every observer exception. Every finalizer returns the identical original `Exception` reference or null.
- `GameState.Save(false, false)` runs only in the normal `Game.Update` postfix on Unity's main thread and only after the two-stage driver boundary authorizes capture.
- A top-level Restart remains outside the trace vocabulary, faults immediately with null input fields, and then runs unchanged. Recursive Restart, nested Undo, and nested restore only balance bookkeeping.
- The first fault owns exactly one terminal record/marker. A sink write, flush, or close failure produces only `SSR oracle passive trace failed: trace_io_failed`; it cannot claim a durable error record.
- `CaptureException` and `CanonicalEncodingException` map to `capture_failed`;
  an otherwise valid complete record over 16 MiB maps to
  `record_too_large`; write/flush/close/file-budget failures map to the
  marker-only `trace_io_failed`. No game-facing exception crosses a patch
  boundary.
- Compact canonical JSON and the two synthetic fixtures from `docs/superpowers/plans/2026-07-31-oracle-passive-protocol.md` are the cross-language wire contract.
- Keep successful harness stdout exactly `SSR oracle unit harness ready` and write failure details only to stderr.
- Every task that changes `oracle/plugin/Core/` must run both the net10 behavioral
  harness and the compile-only net35 Core project introduced in Task 1. C# 7.3
  syntax under net10 is not evidence that the same source uses only net35 APIs.
- Preserve Release determinism, CLR v2/net35 metadata, no Release PDB, and no copied game/BepInEx dependency set.
- Treat these current compile inputs as reviewed pins and stop rather than
  widening the dependency allowlist if any changes:

```text
19eb836818955e4f86818306aaf2baaee989be566d7da697f835b429ab585149  BepInEx.dll
1a21cc03424fc82c3dd1346905d16494536b9595ae4162228d99fb7c285c1031  0Harmony.dll
f8bc81e00aa5f4372cbebe4951e5be7b21e54ba5f978e21c53ae2e8713ca3ca0  UnityEngine.dll
b9aa7294a63984fc7a86cf68bceba4a92b254f8e140943d402e34c397146edf3  UnityEngine.CoreModule.dll
```

- Use strict TDD and the selected `superpowers:subagent-driven-development`
  workflow for every task. The implementer records RED and GREEN evidence,
  makes exactly the task's named commit, and only then may the controller
  generate an immutable `BASE..HEAD` review package. One fresh independent
  task reviewer returns separate, explicit specification-compliance and
  code-quality verdicts. Critical/Important findings are corrected in
  follow-up fix commits and scoped re-reviews; no task commit is amended after
  review. This post-commit sequence is normative anywhere older wording below
  refers to reviews. The initial branch-base hashes, frozen before Task 1.1,
  are:

```text
8c02cafd15da09ccdc4c3a1ff5d2387baf00aee7543b5406fe8a3695dc40afb9  oracle/plugin/Plugin.cs
566779ae0f171daaaba34477e8e7f878cddd11d1218f79acfcd9d0fc8e63e233  oracle/plugin/SsrOracle.Plugin.csproj
419d0d94d2c73204ec3925c723c829e53eed8997ba287e35c41002ce2aee6a60  oracle/plugin/tests/Program.cs
f048869e73157e88513e6338776411bb64bf4c0f74ec50d9cfc6d77b4870d96d  oracle/plugin/tests/SsrOracle.UnitTests.csproj
```

## File responsibility map and execution topology

The coordinator's ten plugin tracks remain stable, but this document contains
twenty-four executable tasks numbered `1.1` through `10.1`.  A coordinator
instruction to execute plugin “Tasks 1-10” means execute every decimal task in
each corresponding track, in numerical order. Every decimal task has its own
RED, GREEN, net35 gate when Core changes, exact commit, and post-commit task
review with separate specification and code-quality verdicts. No decimal
tasks may be batched into one commit.

| File | Sole responsibility |
| --- | --- |
| `Core/OracleProtocol.cs` | Closed schema-v1 values, DTO validation, record/marker error tables |
| `Core/CanonicalJson.cs` | Canonical record bytes and 16 MiB record bound |
| `Core/CaptureSignature.cs` | Length-prefixed complete-capture SHA-256 |
| `Core/NdjsonTraceSink.cs` | Create-new classification, record flushing, 128 MiB session bound |
| `Core/CaptureException.cs` | Shared typed adapter/observation failure boundary |
| `Core/GameObservation.cs` | Unity-free capture values, quiescence values, and capture mapping |
| `Core/PassiveDriverBoundaries.cs` | Hook tokens, issued/authorized/consumed Update capability, and update observation seam |
| `Core/PassiveDriver.cs` | Preparation, activation, update epochs, two-sample settling, and first-fault ownership |
| `Core/PassiveDriverInput.cs` | Direction/Undo attribution and settled Step emission |
| `Core/PassiveDriverLifecycleHooks.cs` | Restart, restore, state-set, and finalizer bookkeeping |
| `Core/PassiveDriverCompletion.cs` | End/close/completion-marker ordering |
| `Core/PassiveConfiguration.cs` | Strict read-only config decoding and typed configuration errors |
| `Core/PhysicalPath.cs` | Two-scan macOS path/absent-leaf proof with deterministic injected scan hook |
| `Core/PassiveReporter.cs` | Exact progress/completion/failure text over an injected log target |
| `Core/PatchBoundary.cs` | Exception firewalls and original-exception identity preservation |
| `Core/PluginModePolicy.cs` | Off-only separation with no passive dependency |
| `Core/PassiveStartup.cs` | Ordered passive resource ownership and owner-only teardown |
| `GameContract.cs` | Exact runtime reflection validation for the pinned game surface |
| `GameAdapter.cs` | The only Unity/game-field reads, `Moving()`, and `Save(false,false)` calls |
| `PassiveController.cs` | Real services/reporter wiring and invariant-before-capture update orchestration |
| `PassivePatches.cs` | Exactly eight observation-only Harmony target classes |
| `Plugin.cs` | One typed config load and Off/Passive selection |
| `tests/Directory.Build.props` | Early project-conditional Core net35 intermediate/project-extension paths |
| `tests/TestSupport.cs` | Assertion API, exact cohort/name manifest, deterministic harness |
| `tests/*Tests.cs` | One responsibility-aligned behavioral or metadata cohort per file |

The final C# manifest is exact and contains 82 named tests:

```text
protocol=4 encoding=5 sink=6 driver-boundary=2 driver-initial=8 driver-input=8
driver-terminal=6 config=6 path=6 observation=5 boundary=5
startup=7 reporter=4 assembly=4 plugin=6 total=82
```

`TestRegistry.VerifyManifest` in Task 1.1 owns one frozen, ordered structural
catalog of all 82 `(cohort, name)` registrations. Each cumulative cohort count
selects that cohort's approved prefix; comparison then rejects a rename,
mis-cohorting, reorder, missing, duplicate, or extra registration before
executing any selected test. Unknown cohorts and negative or overfull counts
are invalid. The final Python accounting task does not guess the protocol
track's evolving item count: it records the literal collection counts,
compares the complete frozen 120-node XFAIL identity manifest, checks all six
named XPASS identities, and proves by exact arithmetic that every other
collected node passed, with zero failures, errors, or skips.

### Exact 24-task ledger

This ledger is normative. The detailed track sections below supply the
complete source and test bodies; this table supplies the non-batchable
execution boundary.  For every row, first add only the named tests and run the
RED command until a named test fails for the stated missing behavior.  Then add
only that row's product slice, run the GREEN command, run `git diff --check`,
make exactly the listed commit, generate the immutable review package from the
recorded task base to that commit, and require both reviewer verdicts before
starting the next row. `core-gate` means the selected cohort followed by the net35 Core
compile command from Task 1.2; `plugin-gate` means the selected cohort followed
by the real net35 plugin build.  A later task may extend a file created earlier,
but may not weaken or rename an earlier registration.

| Task | RED/GREEN selection | Exact new registrations | Product slice | Commit |
| --- | --- | ---: | --- | --- |
| 1.1 | `--cohort protocol` | 1 | runner duplicate/manifest enforcement | `test: install oracle unit harness` |
| 1.2 | `--cohort protocol`; core-gate | 3 (protocol total 4) | closed protocol DTOs and error tables | `feat: define oracle protocol model` |
| 2.1 | `--cohort encoding`; core-gate | 3 | canonical scalar/string/record encoder | `feat: encode canonical oracle json` |
| 2.2 | `--cohort encoding`; core-gate | 2 (encoding total 5) | complete-capture signature and fixtures | `test: pin oracle wire fixtures` |
| 3.1 | `--cohort sink`; core-gate | 3 | injected create-new factory and typed collision | `feat: open oracle traces atomically` |
| 3.2 | `--cohort sink`; core-gate | 3 (sink total 6) | LF/flush, per-line and session bounds, terminal close | `feat: flush bounded oracle traces` |
| 4.1 | `--cohort driver-boundary`; core-gate | 2 | owner-bound hooks and issued/authorized/consumed Update capability | `feat: define passive driver boundaries` |
| 4.2 | `--cohort driver-initial`; core-gate | 8 | preparation, initial epoch, consecutive settling, exact deadlines | `feat: settle passive initial state` |
| 5.1 | `--cohort driver-input`; core-gate | 6 | tokenless physical-poll correlation, four directions, and Undo | `feat: attribute passive input attempts` |
| 5.2 | `--cohort driver-input`; core-gate | 2 (driver-input total 8) | Restart, state replacement, and balanced token cleanup | `feat: balance passive lifecycle hooks` |
| 5.3 | `--cohort driver-terminal`; core-gate | 6 | first-fault arbitration, three steps, End, close, marker ownership | `feat: finalize passive trace capture` |
| 6.1 | `--cohort config`; core-gate | 6 | strict byte parser, typed read failures, fixed passive values | `feat: parse read-only oracle configuration` |
| 6.2 | `--cohort path`; core-gate | 6 | injected two-scan path, containment, and absent-leaf proof | `feat: validate physical oracle paths` |
| 7.1 | `--cohort observation`; core-gate | 5 | thirteen-gate policy and complete capture mapping | `feat: map passive observations` |
| 7.2 | `--cohort assembly --assembly <absolute>`; plugin-gate | 4 | metadata reader plus exact legacy/passive game contract | `test: pin passive game metadata surface` |
| 7.3 | `--cohort plugin --plugin <absolute>`; plugin-gate | 1 | the sole game/Unity adapter and its metadata/IL call-surface audit | `feat: add passive game adapter` |
| 8.1 | `--cohort boundary`; core-gate | 5 | postfix/finalizer firewall and original-exception identity | `feat: contain passive patch callbacks` |
| 8.2 | `--cohort startup`; core-gate | 2 | Off-only dependency separation | `feat: preserve off-mode startup` |
| 8.3 | `--cohort startup`; core-gate | 5 (startup total 7) | ordered prepare/install/activate/marker teardown | `feat: order passive resource startup` |
| 9.1 | `--cohort reporter`; core-gate | 4 | exact logger text over the injected Core log target | `feat: report passive oracle lifecycle` |
| 9.2 | `--cohort plugin --plugin <absolute>`; plugin-gate | 1 (plugin total 2) | controller with path-before-second-identity-before-gate/capture | `feat: enforce passive capture boundary` |
| 9.3 | `--cohort plugin --plugin <absolute>`; plugin-gate | 1 (plugin total 3) | exactly eight Harmony patches and exact signatures | `feat: install passive observation patches` |
| 9.4 | `--cohort plugin --plugin <absolute>`; plugin-gate | 3 (plugin total 6) | typed one-read plugin shell, csproj, metadata/dependency audit | `feat: wire passive oracle plugin` |
| 10.1 | all 82 plus Python accounting and two clean builds | 0 (manifest remains 82) | README literal DLL digest and reproducibility evidence | `docs: record passive oracle build gate` |

For a row that shares a cohort with a later row, temporarily set that cohort's
manifest count to the row's cumulative count.  The final `Program.cs` shown in
Task 10.1 replaces those temporary counts with the exact 15-row/82-test
manifest.  The test methods themselves remain named and registered from their
first RED onward.

---

### Track 1: Establish the core model and real unit-test harness

**Files:**
- Create: `oracle/plugin/Core/OracleProtocol.cs`
- Create: `oracle/plugin/tests/TestSupport.cs`
- Create: `oracle/plugin/tests/Directory.Build.props`
- Create: `oracle/plugin/tests/ProtocolTests.cs`
- Create: `oracle/plugin/tests/SsrOracle.Core.Net35.csproj`
- Modify: `oracle/plugin/tests/Program.cs`
- Modify: `oracle/plugin/tests/SsrOracle.UnitTests.csproj`

**Interfaces:**
- Produces: `OracleMode`, `OracleInput`, `PassivePhase`, `OracleError`, and immutable `RunRecord`, `CaptureRecord`, `InitialRecord`, `StepRecord`, `EndRecord`, and `ErrorRecord` types.
- Produces: `OracleErrors.ForCode(string code) -> OracleError` and `OracleErrors.IsRecordCode(string code) -> bool`.
- Produces: `HarnessOptions`, a tiny `Check` assertion API, and a deterministic
  `TestRegistry`; the harness returns nonzero on the first failed test and
  prints the one success line only after all selected tests pass.
- Produces: compile-only `SsrOracle.Core.Net35.csproj`, which links the same
  `../Core/**/*.cs` product sources against the pinned net35 reference package
  without Unity, Harmony, BepInEx, or game references.
- Produces: project-conditional `Directory.Build.props`, which sets the Core
  project's intermediate and project-extension paths before the SDK imports
  `Microsoft.Common.props`; the net10 harness retains its default paths.
- Consumed by every later C# task.

#### Task 1.1: Install the exact manifest-driven harness

- [ ] **Step 1: Freeze the post-protocol Python baseline and XFAIL identities**

Because the protocol track runs first, freeze the post-protocol non-strict
baseline before any plugin edit.  This retained evidence is ignored, never
committed, and lets Task 10.1 compare the identities of all 120 XFAIL nodes
rather than merely comparing their count:

```bash
set -euo pipefail
mkdir -p data/oracle/plugin-plan-evidence
UV_OFFLINE=1 UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q -rxX \
  > data/oracle/plugin-plan-evidence/pre-plugin-pytest.txt
sed -n 's/^XFAIL \([^ ]*\).*/\1/p' \
  data/oracle/plugin-plan-evidence/pre-plugin-pytest.txt | LC_ALL=C sort \
  > data/oracle/plugin-plan-evidence/pre-plugin-xfail-nodeids.txt
test "$(wc -l < data/oracle/plugin-plan-evidence/pre-plugin-xfail-nodeids.txt | tr -d ' ')" = 120
git check-ignore data/oracle/plugin-plan-evidence/pre-plugin-pytest.txt \
  data/oracle/plugin-plan-evidence/pre-plugin-xfail-nodeids.txt
shasum -a 256 data/oracle/plugin-plan-evidence/pre-plugin-xfail-nodeids.txt
```

Require the post-protocol baseline `1822 passed, 120 xfailed, 6 xpassed`, no
failures/errors/skips, and record the printed XFAIL-manifest digest in the task
report.  Do not continue from a dirty or differently classified baseline.

- [ ] **Step 2: Write the one-test harness RED**

For RED, replace `Program.cs` with the complete temporary one-cohort file shown
in this step, and create this exact initial `ProtocolTests.cs`:

```csharp
using System;
using System.Collections.Generic;

internal static class ProtocolTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("protocol", "registry manifest is exact", RegistryManifestIsExact);
    }

    private static void RegistryManifestIsExact()
    {
        TestRegistry registry = new TestRegistry();
        registry.Add("protocol", "registry manifest is exact", delegate { });
        registry.VerifyManifest(
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });
        Check.Throws<InvalidOperationException>(
            delegate
            {
                registry.Add(
                    "protocol", "registry manifest is exact", delegate { });
            },
            "duplicate test identity");

        TestRegistry renamed = new TestRegistry();
        renamed.Add("protocol", "registry manifest was renamed", delegate { });
        bool renameRejected = RejectsManifest(
            renamed,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry swapped = new TestRegistry();
        swapped.Add("encoding", "registry manifest is exact", delegate { });
        swapped.Add("protocol", "golden fixture bytes", delegate { });
        bool swapRejected = RejectsManifest(
            swapped,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 },
                { "encoding", 1 }
            });

        TestRegistry reordered = new TestRegistry();
        reordered.Add("protocol", "closed error tables", delegate { });
        reordered.Add("protocol", "registry manifest is exact", delegate { });
        bool reorderRejected = RejectsManifest(
            reordered,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry unknown = new TestRegistry();
        unknown.Add("sample", "one", delegate { });
        bool unknownRejected = RejectsManifest(
            unknown,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "sample", 1 }
            });

        bool negativeRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", -1 }
            });
        bool overfullRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 5 }
            });

        bool missingRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry extra = new TestRegistry();
        extra.Add("protocol", "registry manifest is exact", delegate { });
        extra.Add("encoding", "golden fixture bytes", delegate { });
        bool extraRejected = RejectsManifest(
            extra,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry slashPairs = new TestRegistry();
        bool slashPairsDistinct = true;
        try
        {
            slashPairs.Add("a/b", "c", delegate { });
            slashPairs.Add("a", "b/c", delegate { });
        }
        catch (InvalidOperationException)
        {
            slashPairsDistinct = false;
        }

        Check.True(renameRejected, "same-count rename was accepted");
        Check.True(swapRejected, "balanced cohort swap was accepted");
        Check.True(reorderRejected, "registration reorder was accepted");
        Check.True(unknownRejected, "unknown manifest cohort was accepted");
        Check.True(negativeRejected, "negative manifest count was accepted");
        Check.True(overfullRejected, "overfull manifest count was accepted");
        Check.True(missingRejected, "missing registration was accepted");
        Check.True(extraRejected, "extra registration was accepted");
        Check.True(slashPairsDistinct, "structural identities were aliased");
    }

    private static bool RejectsManifest(
        TestRegistry registry,
        IDictionary<string, int> expected)
    {
        try
        {
            registry.VerifyManifest(expected);
            return false;
        }
        catch (InvalidOperationException)
        {
            return true;
        }
    }
}
```

Replace `Program.cs` with this complete Task 1.1 file. This is deliberately
present before `TestSupport.cs`, so the clean-tree RED names the missing
`TestRegistry`/`HarnessOptions` support instead of running the starting
hard-coded-success program:

```csharp
using System;
using System.Collections.Generic;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            HarnessOptions options = HarnessOptions.Parse(args);
            TestRegistry tests = new TestRegistry();
            ProtocolTests.Register(tests);
            tests.VerifyManifest(
                new Dictionary<string, int>(StringComparer.Ordinal)
                {
                    { "protocol", 1 }
                });
            int result = tests.Run(options.Cohort);
            if (result != 0)
                return result;
            Console.WriteLine("SSR oracle unit harness ready");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.ToString());
            return 1;
        }
    }
}
```

- [ ] **Step 3: Run RED for the missing harness support**

Run the harness and require a compiler RED naming `TestRegistry`; an SDK,
assets, or fixture failure is not the intended RED.

```bash
if test ! -f oracle/plugin/tests/obj/project.assets.json; then
  /opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
    oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    --source "$PWD/data/oracle/compat/feed"
fi
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort protocol
```

- [ ] **Step 4: Implement the dependency-minimal runner and assertion support**

Apply the complete `TestSupport.cs` body below.

Create `TestSupport.cs` with the compile-ready runner below so later tasks do
not invent another test framework:

```csharp
using System;
using System.Collections.Generic;
using System.IO;

internal sealed class HarnessOptions
{
    internal string Cohort { get; private set; }
    internal string AssemblyPath { get; private set; }
    internal string PluginPath { get; private set; }
    internal string ModeOffFixturePath { get; private set; }

    private HarnessOptions()
    {
    }

    internal static HarnessOptions Parse(string[] args)
    {
        if (args == null)
            throw new ArgumentNullException("args");
        HarnessOptions options = new HarnessOptions();
        for (int index = 0; index < args.Length; index++)
        {
            string name = args[index];
            if (name == "--cohort")
                options.Cohort = SetOnce(
                    options.Cohort, ReadValue(args, ref index), name);
            else if (name == "--assembly")
                options.AssemblyPath = SetOnce(
                    options.AssemblyPath,
                    RequireAbsolute(ReadValue(args, ref index), name),
                    name);
            else if (name == "--plugin")
                options.PluginPath = SetOnce(
                    options.PluginPath,
                    RequireAbsolute(ReadValue(args, ref index), name),
                    name);
            else if (name == "--mode-off-fixture")
                options.ModeOffFixturePath = SetOnce(
                    options.ModeOffFixturePath,
                    RequireAbsolute(ReadValue(args, ref index), name),
                    name);
            else
                throw new ArgumentException("unknown argument: " + name);
        }
        return options;
    }

    private static string ReadValue(string[] args, ref int index)
    {
        index++;
        if (index >= args.Length || String.IsNullOrEmpty(args[index]))
            throw new ArgumentException("missing argument value");
        return args[index];
    }

    private static string SetOnce(string prior, string value, string name)
    {
        if (prior != null)
            throw new ArgumentException("duplicate argument: " + name);
        return value;
    }

    private static string RequireAbsolute(string value, string name)
    {
        if (!Path.IsPathRooted(value))
            throw new ArgumentException("path must be absolute: " + name);
        return value;
    }
}

internal sealed class TestRegistry
{
    private sealed class TestIdentity
    {
        internal readonly string Cohort;
        internal readonly string Name;

        internal TestIdentity(string cohort, string name)
        {
            Cohort = cohort;
            Name = name;
        }

        internal bool Matches(string cohort, string name)
        {
            return String.Equals(Cohort, cohort, StringComparison.Ordinal)
                && String.Equals(Name, name, StringComparison.Ordinal);
        }
    }

    private sealed class TestCase
    {
        internal string Cohort;
        internal string Name;
        internal Action Test;
    }

    private static readonly TestIdentity[] ApprovedManifest =
        new TestIdentity[]
        {
            new TestIdentity("protocol", "registry manifest is exact"),
            new TestIdentity("protocol", "closed error tables"),
            new TestIdentity("protocol", "record constructor boundaries"),
            new TestIdentity("protocol", "capture value equality"),
            new TestIdentity("encoding", "golden fixture bytes"),
            new TestIdentity("encoding", "canonical string scalars"),
            new TestIdentity("encoding", "surrogates are rejected"),
            new TestIdentity("encoding", "capture signature is exact"),
            new TestIdentity("encoding", "record line limit includes LF"),
            new TestIdentity("sink", "factory arguments are exact"),
            new TestIdentity("sink", "null factory output is typed"),
            new TestIdentity("sink", "real collision is typed"),
            new TestIdentity("sink", "records use LF and flush"),
            new TestIdentity("sink", "bounds and write failures are terminal"),
            new TestIdentity("sink", "close ownership is single use"),
            new TestIdentity(
                "driver-boundary",
                "hook token is owner bound and single consume"),
            new TestIdentity(
                "driver-boundary",
                "update directive authorizes rebases and consumes once"),
            new TestIdentity("driver-initial", "prepare activate separation"),
            new TestIdentity(
                "driver-initial", "pre epoch neutral does not leak"),
            new TestIdentity("driver-initial", "matching pair writes initial"),
            new TestIdentity("driver-initial", "not inspected breaks pair"),
            new TestIdentity("driver-initial", "nonquiescent breaks pair"),
            new TestIdentity("driver-initial", "cardinal clears candidate"),
            new TestIdentity(
                "driver-initial", "replacement rebases same callback"),
            new TestIdentity(
                "driver-initial", "exact deadline and pre overrun"),
            new TestIdentity("driver-input", "all cardinals correlate"),
            new TestIdentity(
                "driver-input", "filtered and zero poll open no attempt"),
            new TestIdentity(
                "driver-input", "duplicate mismatch and unknown fault"),
            new TestIdentity(
                "driver-input", "unscoped policy follows phase"),
            new TestIdentity(
                "driver-input", "accepted and refused direction outcomes"),
            new TestIdentity(
                "driver-input", "Undo acceptance and restore rules"),
            new TestIdentity("driver-input", "restart depth and null fields"),
            new TestIdentity(
                "driver-input", "state replacement and ClearThrew"),
            new TestIdentity(
                "driver-terminal", "three steps End Close Complete order"),
            new TestIdentity(
                "driver-terminal", "error field policy is exact"),
            new TestIdentity(
                "driver-terminal", "sink failure uses trace io marker"),
            new TestIdentity(
                "driver-terminal", "completion reporter cannot rewrite trace"),
            new TestIdentity("driver-terminal", "first fault wins race"),
            new TestIdentity(
                "driver-terminal", "Dispose and late callbacks are final"),
            new TestIdentity("config", "off grammar is exact and read only"),
            new TestIdentity(
                "config", "off malformed inputs are rejected"),
            new TestIdentity("config", "unsupported modes are typed"),
            new TestIdentity("config", "passive values are canonical"),
            new TestIdentity("config", "passive failures are typed"),
            new TestIdentity("config", "configuration reads are typed"),
            new TestIdentity("path", "containment uses component boundary"),
            new TestIdentity("path", "existing paths resolve canonically"),
            new TestIdentity("path", "missing suffix is preserved"),
            new TestIdentity("path", "lexical paths are strict"),
            new TestIdentity(
                "path", "symlink and nondirectory are rejected"),
            new TestIdentity("path", "two scan drift is rejected"),
            new TestIdentity(
                "observation", "all thirteen gates are required"),
            new TestIdentity(
                "observation", "capture maps all twelve fields"),
            new TestIdentity(
                "observation", "three nullable strings normalize"),
            new TestIdentity("observation", "required values reject null"),
            new TestIdentity(
                "observation", "numeric ranges reject negative"),
            new TestIdentity(
                "boundary", "postfix contains observer failures"),
            new TestIdentity(
                "boundary", "game exception claims before cleanup"),
            new TestIdentity(
                "boundary", "successful postfix makes finalizer cleanup inert"),
            new TestIdentity(
                "boundary", "cleanup failure is contained and reported"),
            new TestIdentity(
                "boundary", "update finalizer preserves original reference"),
            new TestIdentity(
                "startup", "off invokes only legacy validation then boot"),
            new TestIdentity(
                "startup", "off preserves legacy failure identity"),
            new TestIdentity(
                "startup",
                "run flush precedes patches and activation precedes boot"),
            new TestIdentity(
                "startup", "typed pre-driver failures stay marker only"),
            new TestIdentity(
                "startup", "prepare failure is not reported twice"),
            new TestIdentity(
                "startup", "owned startup failures use driver arbitration"),
            new TestIdentity(
                "startup", "teardown is ordered and idempotent"),
            new TestIdentity("reporter", "ready markers are exact"),
            new TestIdentity("reporter", "completion marker is exact"),
            new TestIdentity("reporter", "failure markers are closed"),
            new TestIdentity("reporter", "diagnostic is nonterminal"),
            new TestIdentity("assembly", "pinned Assembly-CSharp hash"),
            new TestIdentity("assembly", "exact ten observed methods"),
            new TestIdentity("assembly", "exact required game fields"),
            new TestIdentity(
                "assembly", "metadata matcher rejects near misses"),
            new TestIdentity(
                "plugin", "game adapter call surface is passive"),
            new TestIdentity(
                "plugin", "controller crosses authorized update boundary"),
            new TestIdentity(
                "plugin", "eight Harmony patch contracts are exact"),
            new TestIdentity(
                "plugin", "PE CLR and direct references are pinned"),
            new TestIdentity("plugin", "BepInPlugin identity is exact"),
            new TestIdentity(
                "plugin", "typed modes and owner teardown are closed")
        };

    private readonly List<TestCase> tests = new List<TestCase>();

    internal void Add(string cohort, string name, Action test)
    {
        if (String.IsNullOrEmpty(cohort))
            throw new ArgumentException("cohort is required", "cohort");
        if (String.IsNullOrEmpty(name))
            throw new ArgumentException("name is required", "name");
        if (test == null)
            throw new ArgumentNullException("test");
        for (int index = 0; index < tests.Count; index++)
        {
            if (String.Equals(
                    tests[index].Cohort, cohort, StringComparison.Ordinal)
                && String.Equals(
                    tests[index].Name, name, StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "duplicate test cohort '" + cohort + "', name '" + name + "'");
            }
        }
        tests.Add(new TestCase { Cohort = cohort, Name = name, Test = test });
    }

    internal void VerifyManifest(IDictionary<string, int> expected)
    {
        if (expected == null)
            throw new ArgumentNullException("expected");
        Dictionary<string, int> approvedCounts =
            new Dictionary<string, int>(StringComparer.Ordinal);
        for (int index = 0; index < ApprovedManifest.Length; index++)
        {
            int count;
            approvedCounts.TryGetValue(ApprovedManifest[index].Cohort, out count);
            approvedCounts[ApprovedManifest[index].Cohort] = count + 1;
        }

        Dictionary<string, int> requestedCounts =
            new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (KeyValuePair<string, int> pair in expected)
        {
            int approvedCount;
            if (pair.Key == null
                || !approvedCounts.TryGetValue(pair.Key, out approvedCount))
            {
                throw new InvalidOperationException(
                    "unknown test cohort: " + pair.Key);
            }
            if (pair.Value < 0)
                throw new InvalidOperationException(
                    "negative test count for " + pair.Key);
            if (pair.Value > approvedCount)
                throw new InvalidOperationException(
                    "test count exceeds approved manifest for " + pair.Key);
            if (requestedCounts.ContainsKey(pair.Key))
                throw new InvalidOperationException(
                    "duplicate manifest cohort: " + pair.Key);
            requestedCounts.Add(pair.Key, pair.Value);
        }

        List<TestIdentity> requested = new List<TestIdentity>();
        Dictionary<string, int> visitedCounts =
            new Dictionary<string, int>(StringComparer.Ordinal);
        for (int index = 0; index < ApprovedManifest.Length; index++)
        {
            TestIdentity identity = ApprovedManifest[index];
            int visited;
            visitedCounts.TryGetValue(identity.Cohort, out visited);
            visitedCounts[identity.Cohort] = visited + 1;
            int requestedCount;
            if (requestedCounts.TryGetValue(identity.Cohort, out requestedCount)
                && visited < requestedCount)
            {
                requested.Add(identity);
            }
        }

        if (tests.Count != requested.Count)
        {
            throw new InvalidOperationException(
                "test manifest size mismatch: expected "
                + requested.Count.ToString() + ", actual "
                + tests.Count.ToString());
        }
        for (int index = 0; index < requested.Count; index++)
        {
            if (!requested[index].Matches(
                    tests[index].Cohort, tests[index].Name))
            {
                throw new InvalidOperationException(
                    "test manifest mismatch at index " + index.ToString()
                    + ": expected cohort '" + requested[index].Cohort
                    + "', name '" + requested[index].Name
                    + "'; actual cohort '" + tests[index].Cohort
                    + "', name '" + tests[index].Name + "'");
            }
        }
    }

    internal int Run(string selectedCohort)
    {
        int selected = 0;
        for (int index = 0; index < tests.Count; index++)
        {
            TestCase test = tests[index];
            if (selectedCohort != null
                && selectedCohort != "all"
                && selectedCohort != test.Cohort)
            {
                continue;
            }
            selected++;
            try
            {
                test.Test();
            }
            catch (Exception error)
            {
                Console.Error.WriteLine(
                    "cohort '" + test.Cohort + "', test '" + test.Name
                    + "': " + error.ToString());
                return 1;
            }
        }
        if (selected == 0)
        {
            Console.Error.WriteLine("no tests selected");
            return 1;
        }
        return 0;
    }
}

internal static class Check
{
    internal static void True(bool value, string message)
    {
        if (!value)
            throw new InvalidOperationException(message);
    }

    internal static void False(bool value, string message)
    {
        True(!value, message);
    }

    internal static void Equal<T>(T expected, T actual, string message)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new InvalidOperationException(message);
    }

    internal static void Same(object expected, object actual, string message)
    {
        if (!Object.ReferenceEquals(expected, actual))
            throw new InvalidOperationException(message);
    }

    internal static void Bytes(byte[] expected, byte[] actual, string message)
    {
        Sequence<byte>(expected, actual, message);
    }

    internal static void Sequence<T>(
        IList<T> expected,
        IList<T> actual,
        string message)
    {
        if (expected == null || actual == null || expected.Count != actual.Count)
            throw new InvalidOperationException(message);
        for (int index = 0; index < expected.Count; index++)
        {
            if (!EqualityComparer<T>.Default.Equals(
                expected[index], actual[index]))
            {
                throw new InvalidOperationException(
                    message + " at index " + index.ToString());
            }
        }
    }

    internal static TException Throws<TException>(Action action, string message)
        where TException : Exception
    {
        if (action == null)
            throw new ArgumentNullException("action");
        try
        {
            action();
        }
        catch (TException error)
        {
            return error;
        }
        catch (Exception error)
        {
            throw new InvalidOperationException(
                message + ": wrong exception " + error.GetType().FullName,
                error);
        }
        throw new InvalidOperationException(message + ": no exception");
    }
}
```

- [ ] **Step 5: Run GREEN and record immutable review evidence**

Run `--cohort protocol`, require the one temporary test and exact success
stdout, and run the diff check. Record the RED/GREEN output in the task report
for the post-commit reviewer:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort protocol
git diff --check
```

- [ ] **Step 6: Commit only the Task 1.1 harness slice**

```bash
git add oracle/plugin/tests/TestSupport.cs oracle/plugin/tests/ProtocolTests.cs \
  oracle/plugin/tests/Program.cs oracle/plugin/tests/SsrOracle.UnitTests.csproj
git commit -m "test: install oracle unit harness"
```

After the commit, the controller generates the Task 1.1 `BASE..HEAD` review
package and requires explicit specification-compliance and code-quality
approval before Task 1.2.

#### Task 1.2: Define and validate the closed protocol model

- [ ] **Step 1: Freeze the current sources and write the three remaining RED protocol tests**

Before changing any Task 1.2 source, verify the reviewed post-Task-1.1 source
state with these task-aware pins. `Plugin.cs`, both project files, and their
pins are unchanged from the initial branch base; `Program.cs` intentionally
uses the reviewed Task 1.1 hash rather than its pre-Task-1.1 hash:

```bash
test "$(shasum -a 256 oracle/plugin/Plugin.cs | awk '{print $1}')" = \
  "8c02cafd15da09ccdc4c3a1ff5d2387baf00aee7543b5406fe8a3695dc40afb9"
test "$(shasum -a 256 oracle/plugin/SsrOracle.Plugin.csproj | awk '{print $1}')" = \
  "566779ae0f171daaaba34477e8e7f878cddd11d1218f79acfcd9d0fc8e63e233"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "8e97b9b7e0f6fee6b7d7198d3465bcaba05f335a09d5e78638ac8830061784d0"
test "$(shasum -a 256 oracle/plugin/tests/SsrOracle.UnitTests.csproj | awk '{print $1}')" = \
  "f048869e73157e88513e6338776411bb64bf4c0f74ec50d9cfc6d77b4870d96d"
```

All four commands must exit zero. Add this exact registration and test to
`ProtocolTests.cs`, then register it from `Program.Main` before the success
line:

```csharp
using System;
using System.Collections.Generic;

internal static class ProtocolTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("protocol", "registry manifest is exact", RegistryManifestIsExact);
        tests.Add("protocol", "closed error tables", ClosedErrorTables);
        tests.Add("protocol", "record constructor boundaries", RecordBoundaries);
        tests.Add("protocol", "capture value equality", CaptureValueEquality);
    }

    private static void ClosedErrorTables()
    {
        string[,] pairs = new string[,]
        {
            { "patch_install_failed", "observation patch installation failed" },
            { "input_before_initial", "manual input arrived before initial capture" },
            { "overlapping_input", "manual input arrived while settling" },
            { "unexpected_input", "native input was outside the passive vocabulary" },
            { "unscoped_process_input", "manual-looking input occurred outside the native poll scope" },
            { "hook_order_mismatch", "observation hook order mismatch" },
            { "game_method_exception", "observed game method threw" },
            { "observer_exception", "passive observer failed" },
            { "capture_failed", "game-state capture failed" },
            { "record_too_large", "encoded trace record exceeded its limit" },
            { "initial_settle_timeout", "initial capture did not settle" },
            { "settle_timeout", "input did not settle" },
            { "state_replaced", "game state identity changed" },
            { "save_path_changed", "isolated save path changed" }
        };
        for (int index = 0; index < pairs.GetLength(0); index++)
        {
            OracleError error = OracleErrors.ForCode(pairs[index, 0]);
            Check.Equal(pairs[index, 0], error.Code, "record code " + index);
            Check.Equal(pairs[index, 1], error.Message, "record message " + index);
            Check.True(OracleErrors.IsRecordCode(pairs[index, 0]), "record membership");
            Check.False(OracleMarkerErrors.IsMarkerOnly(pairs[index, 0]), "record not marker");
        }
        string[] markers = new string[]
        {
            "invalid_mode", "invalid_configuration", "invalid_assembly",
            "invalid_reflection", "invalid_path", "trace_exists",
            "save_redirect_failed", "trace_io_failed"
        };
        for (int index = 0; index < markers.Length; index++)
        {
            Check.True(OracleMarkerErrors.IsMarkerOnly(markers[index]), "marker " + index);
            Check.False(OracleErrors.IsRecordCode(markers[index]), "marker not record");
            string marker = markers[index];
            Check.Throws<ArgumentException>(
                delegate { OracleErrors.ForCode(marker); }, "marker rejected by record table");
        }
        Check.Throws<ArgumentException>(
            delegate { OracleErrors.ForCode("unknown"); }, "unknown record code");
    }

    private static CaptureRecord Capture(string rawSave, string identity)
    {
        return new CaptureRecord(
            rawSave, identity, "", false, false, false, false, "", "",
            0, 0, 0);
    }

    private static void RecordBoundaries()
    {
        string runId = "0123456789abcdef0123456789abcdef";
        DateTime utc = new DateTime(2026, 7, 31, 19, 9, 50, DateTimeKind.Utc);
        CaptureRecord capture = Capture("save", "-2147483648");
        new RunRecord(runId, OracleProtocol.ExpectedAssemblySha256, utc);
        new StepRecord(runId, Int32.MaxValue, OracleInput.Undo, true, false, 2, false, capture);
        new StepRecord(runId, 0, OracleInput.North, false, false, 600, false, capture);
        new ErrorRecord(runId, null, null, "capture_failed", 0, null);
        new ErrorRecord(runId, Int32.MaxValue, OracleInput.East, "settle_timeout", 600, capture);
        Check.Throws<ArgumentException>(
            delegate { new RunRecord(runId.ToUpperInvariant(), OracleProtocol.ExpectedAssemblySha256, utc); },
            "uppercase run ID");
        Check.Throws<ArgumentException>(
            delegate { new RunRecord(runId, OracleProtocol.ExpectedAssemblySha256, utc.ToLocalTime()); },
            "non-UTC start");
        Check.Throws<ArgumentException>(
            delegate { Capture("save", "-0"); }, "negative zero identity");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new StepRecord(runId, 0, OracleInput.North, true, false, 1, false, capture); },
            "step frame one");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new StepRecord(runId, 0, OracleInput.North, true, false, 601, false, capture); },
            "step frame 601");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new ErrorRecord(runId, null, null, "capture_failed", -1, null); },
            "error frame negative");
        Check.Throws<ArgumentOutOfRangeException>(
            delegate { new ErrorRecord(runId, null, null, "capture_failed", 601, null); },
            "error frame 601");
        Check.Throws<ArgumentException>(
            delegate { new StepRecord(runId, 0, OracleInput.North, true, false, 2, true, capture); },
            "state replacement step");
        Check.Throws<ArgumentException>(
            delegate { new ErrorRecord(runId, 0, null, "capture_failed", 0, null); },
            "mismatched nullable input fields");
        ErrorRecord unexpected = new ErrorRecord(
            runId, 0, null, "unexpected_input", 0, null);
        Check.Equal(0, unexpected.InputIndex.Value,
            "unknown native input retains the next input index");
        Check.False(unexpected.Input.HasValue,
            "unknown native input is not fabricated as a schema input");
        Check.Throws<ArgumentException>(
            delegate
            {
                new ErrorRecord(
                    runId, null, OracleInput.North,
                    "unexpected_input", 0, null);
            },
            "input never appears without an input index");
    }

    private static void CaptureValueEquality()
    {
        CaptureRecord left = Capture("save", "17");
        CaptureRecord equal = Capture("save", "17");
        CaptureRecord different = Capture("changed", "17");
        Check.True(left.Equals(equal), "complete capture equality");
        Check.Equal(left.GetHashCode(), equal.GetHashCode(), "equal hash codes");
        Check.False(left.Equals(different), "raw-save inequality");
        Check.False(left.Equals(null), "null inequality");
    }

    private static void RegistryManifestIsExact()
    {
        TestRegistry registry = new TestRegistry();
        registry.Add("protocol", "registry manifest is exact", delegate { });
        registry.VerifyManifest(
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });
        Check.Throws<InvalidOperationException>(
            delegate
            {
                registry.Add(
                    "protocol", "registry manifest is exact", delegate { });
            },
            "duplicate test identity");

        TestRegistry renamed = new TestRegistry();
        renamed.Add("protocol", "registry manifest was renamed", delegate { });
        bool renameRejected = RejectsManifest(
            renamed,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry swapped = new TestRegistry();
        swapped.Add("encoding", "registry manifest is exact", delegate { });
        swapped.Add("protocol", "golden fixture bytes", delegate { });
        bool swapRejected = RejectsManifest(
            swapped,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 },
                { "encoding", 1 }
            });

        TestRegistry reordered = new TestRegistry();
        reordered.Add("protocol", "closed error tables", delegate { });
        reordered.Add("protocol", "registry manifest is exact", delegate { });
        bool reorderRejected = RejectsManifest(
            reordered,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry unknown = new TestRegistry();
        unknown.Add("sample", "one", delegate { });
        bool unknownRejected = RejectsManifest(
            unknown,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "sample", 1 }
            });

        bool negativeRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", -1 }
            });
        bool overfullRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 5 }
            });

        bool missingRejected = RejectsManifest(
            registry,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 2 }
            });

        TestRegistry extra = new TestRegistry();
        extra.Add("protocol", "registry manifest is exact", delegate { });
        extra.Add("encoding", "golden fixture bytes", delegate { });
        bool extraRejected = RejectsManifest(
            extra,
            new Dictionary<string, int>(StringComparer.Ordinal)
            {
                { "protocol", 1 }
            });

        TestRegistry slashPairs = new TestRegistry();
        bool slashPairsDistinct = true;
        try
        {
            slashPairs.Add("a/b", "c", delegate { });
            slashPairs.Add("a", "b/c", delegate { });
        }
        catch (InvalidOperationException)
        {
            slashPairsDistinct = false;
        }

        Check.True(renameRejected, "same-count rename was accepted");
        Check.True(swapRejected, "balanced cohort swap was accepted");
        Check.True(reorderRejected, "registration reorder was accepted");
        Check.True(unknownRejected, "unknown manifest cohort was accepted");
        Check.True(negativeRejected, "negative manifest count was accepted");
        Check.True(overfullRejected, "overfull manifest count was accepted");
        Check.True(missingRejected, "missing registration was accepted");
        Check.True(extraRejected, "extra registration was accepted");
        Check.True(slashPairsDistinct, "structural identities were aliased");
    }

    private static bool RejectsManifest(
        TestRegistry registry,
        IDictionary<string, int> expected)
    {
        try
        {
            registry.VerifyManifest(expected);
            return false;
        }
        catch (InvalidOperationException)
        {
            return true;
        }
    }
}
```

Replace `Program.cs` with this complete file; later tasks add registrations and
manifest rows but do not change its output contract:

```csharp
using System;
using System.Collections.Generic;

internal static class Program
{
private static int Main(string[] args)
{
    try
    {
        HarnessOptions options = HarnessOptions.Parse(args);
        TestRegistry tests = new TestRegistry();
        ProtocolTests.Register(tests);
        tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
        {
            { "protocol", 4 }
        });
        int result = tests.Run(options.Cohort);
        if (result != 0)
            return result;
        Console.WriteLine("SSR oracle unit harness ready");
        return 0;
    }
    catch (Exception error)
    {
        Console.Error.WriteLine(error.ToString());
        return 1;
    }
}
}
```

- [ ] **Step 2: Run RED and require the missing product symbol**

Run exactly:

```bash
if test ! -f oracle/plugin/tests/obj/project.assets.json; then
  /opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
    oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    --source "$PWD/data/oracle/compat/feed"
fi
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore
```

Require nonzero exit and a compiler diagnostic naming `CaptureRecord`,
`OracleError`, or `OracleErrors`. The complete frozen protocol tests resolve
the missing `CaptureRecord` return type before the error-table symbols, so
`CaptureRecord` is an equally valid missing-product-symbol RED. A missing
assets file, fixture, or SDK is not the intended RED.

- [ ] **Step 3: Link the product sources and add the net35 compile-only project**

Add this item group to the test project; do not add a project reference to the BepInEx plugin:

```xml
<ItemGroup>
  <Compile Include="../Core/**/*.cs" LinkBase="Core" />
</ItemGroup>
```

Keep target `net10.0`, language version `7.3`, implicit usings disabled, nullable disabled, and zero package references.

Create `oracle/plugin/tests/Directory.Build.props` with exactly these early,
project-conditional properties. They cannot be assigned inside the SDK project:

```xml
<Project>
  <PropertyGroup Condition="'$(MSBuildProjectName)' == 'SsrOracle.Core.Net35'">
    <BaseIntermediateOutputPath>obj/core-net35/</BaseIntermediateOutputPath>
    <MSBuildProjectExtensionsPath>obj/core-net35/</MSBuildProjectExtensionsPath>
  </PropertyGroup>
</Project>
```

Create `oracle/plugin/tests/SsrOracle.Core.Net35.csproj` with exactly:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net35</TargetFramework>
    <LangVersion>7.3</LangVersion>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>
    <AssemblyName>SsrOracle.Core.CompileOnly</AssemblyName>
    <BaseOutputPath>bin/core-net35/</BaseOutputPath>
  </PropertyGroup>
  <PropertyGroup Condition="'$(Configuration)' == 'Release'">
    <DebugType>none</DebugType>
    <DebugSymbols>false</DebugSymbols>
  </PropertyGroup>
  <ItemGroup>
    <Compile Include="../Core/**/*.cs" LinkBase="Core" />
    <PackageReference Include="Microsoft.NETFramework.ReferenceAssemblies.net35"
                      Version="1.0.3" PrivateAssets="all" />
  </ItemGroup>
</Project>
```

- [ ] **Step 4: Implement the exact model and close the RED test**

Create `OracleProtocol.cs` with the following compile-ready model. The literal
error table shown below contains all fourteen entries and no generated or
fallback message path:

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;

internal static class OracleProtocol
{
    internal const int SchemaVersion = 1;
    internal const string PluginVersion = "0.2.0";
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
```

- [ ] **Step 5: Run GREEN and both target-framework gates**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  --source "$PWD/data/oracle/compat/feed"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Require the four-test protocol manifest and both builds to pass, and retain
their pristine output in the task report for post-commit review.

- [ ] **Step 6: Commit only the Task 1.2 protocol-model slice**

```bash
git add oracle/plugin/Core/OracleProtocol.cs \
  oracle/plugin/tests/TestSupport.cs oracle/plugin/tests/ProtocolTests.cs \
  oracle/plugin/tests/Program.cs oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  oracle/plugin/tests/Directory.Build.props \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj
git commit -m "feat: define oracle protocol model"
```

### Track 2: Encode canonical JSON and capture signatures

**Files:**
- Create: `oracle/plugin/Core/CanonicalJson.cs`
- Create: `oracle/plugin/Core/CaptureSignature.cs`
- Create: `oracle/plugin/tests/EncodingTests.cs`
- Create: `oracle/plugin/tests/CaptureSignatureTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Produces `CanonicalJson.EncodeRun`, `EncodeInitial`, `EncodeStep`,
  `EncodeEnd`, and `EncodeError`, each accepting its matching record type and
  returning one compact UTF-8 object without LF. It also produces
  `ValidateRecordSize(byte[])`.

- Produces: `CanonicalJson.ValidateRecordSize(byte[] encoded) -> void`; 16 MiB includes the sink's LF.
- Produces: `CanonicalEncodingException` for invalid canonical scalar/text
  encoding and `RecordTooLargeException` for a complete otherwise-valid line
  that exceeds the fixed bound. The two types are never interchangeable.
- Produces: `CaptureSignature.Compute(CaptureRecord capture) -> byte[]`, always 32 bytes.
- Consumed by the sink and driver.

#### Task 2.1: Encode canonical scalar and record JSON

- [ ] **Step 1: Add the first three exact RED encoder tests**

Create `EncodingTests.cs` exactly as follows.  Every promised scalar, record,
fixture, size, and signature assertion is executable; there is no prose-only
test matrix.

```csharp
using System;
using System.Globalization;
using System.IO;
using System.Text;

internal static class ProtocolSamples
{
    internal const string RunId = "0123456789abcdef0123456789abcdef";
    internal static readonly CaptureRecord InitialCapture = Capture("initial");
    internal static readonly CaptureRecord MovedCapture = Capture("moved");
    internal static readonly RunRecord Run = new RunRecord(
        RunId, OracleProtocol.ExpectedAssemblySha256,
        new DateTime(2026, 7, 31, 19, 9, 50, DateTimeKind.Utc).AddTicks(3199100));
    internal static readonly InitialRecord Initial =
        new InitialRecord(RunId, InitialCapture);
    internal static readonly StepRecord Step0 =
        new StepRecord(RunId, 0, OracleInput.West, true, true, 2, false, MovedCapture);
    internal static readonly StepRecord Step1 =
        new StepRecord(RunId, 1, OracleInput.North, false, false, 2, false, MovedCapture);
    internal static readonly StepRecord Step2 =
        new StepRecord(RunId, 2, OracleInput.Undo, true, false, 2, false, InitialCapture);
    internal static readonly EndRecord End = new EndRecord(
        RunId, 3, new DateTime(2026, 7, 31, 19, 11, 0, DateTimeKind.Utc));
    internal static readonly ErrorRecord Error = new ErrorRecord(
        RunId, 1, OracleInput.North, "settle_timeout", 600, MovedCapture);

    internal static CaptureRecord Capture(string rawSave)
    {
        return new CaptureRecord(
            rawSave, "17", "", false, false, false, false, "", "", 0, 0, 0);
    }
}

internal static class EncodingTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("encoding", "golden fixture bytes", GoldenFixtures);
        tests.Add("encoding", "canonical string scalars", CanonicalStrings);
        tests.Add("encoding", "surrogates are rejected", RejectsSurrogates);
    }

    private static byte[][] ReadFixtureLines(string path)
    {
        byte[] payload = File.ReadAllBytes(path);
        Check.True(payload.Length > 0, "fixture nonempty");
        Check.Equal((byte)'\n', payload[payload.Length - 1], "fixture final LF");
        string[] pieces = new UTF8Encoding(false, true).GetString(payload)
            .Split(new char[] { '\n' });
        byte[][] lines = new byte[pieces.Length - 1][];
        for (int index = 0; index < lines.Length; index++)
            lines[index] = new UTF8Encoding(false, true).GetBytes(pieces[index]);
        return lines;
    }

    private static void GoldenFixtures()
    {
        byte[][] success = ReadFixtureLines(Path.Combine(
            "tests", "fixtures", "oracle_trace", "passive-success.ndjson"));
        byte[][] error = ReadFixtureLines(Path.Combine(
            "tests", "fixtures", "oracle_trace", "passive-error.ndjson"));
        byte[][] actual = new byte[][]
        {
            CanonicalJson.EncodeRun(ProtocolSamples.Run),
            CanonicalJson.EncodeInitial(ProtocolSamples.Initial),
            CanonicalJson.EncodeStep(ProtocolSamples.Step0),
            CanonicalJson.EncodeStep(ProtocolSamples.Step1),
            CanonicalJson.EncodeStep(ProtocolSamples.Step2),
            CanonicalJson.EncodeEnd(ProtocolSamples.End)
        };
        Check.Equal(6, success.Length, "success fixture lines");
        for (int index = 0; index < actual.Length; index++)
            Check.Bytes(success[index], actual[index], "success line " + index);
        Check.Equal(4, error.Length, "error fixture lines");
        Check.Bytes(error[0], actual[0], "error run line");
        Check.Bytes(error[1], actual[1], "error initial line");
        Check.Bytes(error[2], actual[2], "error step line");
        Check.Bytes(error[3], CanonicalJson.EncodeError(ProtocolSamples.Error),
            "error terminal line");

        Check.Bytes(
            new UTF8Encoding(false, true).GetBytes(
                "{\"kind\":\"error\",\"schema_version\":1,\"run_id\":"
                + "\"0123456789abcdef0123456789abcdef\",\"input_index\":null,"
                + "\"input\":null,\"code\":\"capture_failed\",\"message\":"
                + "\"game-state capture failed\",\"settle_frames\":0,"
                + "\"last_capture\":null}"),
            CanonicalJson.EncodeError(new ErrorRecord(
                ProtocolSamples.RunId, null, null, "capture_failed", 0, null)),
            "fully-null error bytes");
        Check.Bytes(
            new UTF8Encoding(false, true).GetBytes(
                "{\"kind\":\"error\",\"schema_version\":1,\"run_id\":"
                + "\"0123456789abcdef0123456789abcdef\",\"input_index\":2,"
                + "\"input\":null,\"code\":\"unexpected_input\",\"message\":"
                + "\"native input was outside the passive vocabulary\","
                + "\"settle_frames\":0,\"last_capture\":null}"),
            CanonicalJson.EncodeError(new ErrorRecord(
                ProtocolSamples.RunId, 2, null, "unexpected_input", 0, null)),
            "indexed null-input error bytes");

        byte[] south = CanonicalJson.EncodeStep(new StepRecord(
            ProtocolSamples.RunId, 0, OracleInput.South,
            true, true, 2, false, ProtocolSamples.MovedCapture));
        Check.True(ContainsBytes(south,
            new UTF8Encoding(false, true).GetBytes("\"input\":\"South\"")),
            "South exact wire spelling");
        byte[] east = CanonicalJson.EncodeError(new ErrorRecord(
            ProtocolSamples.RunId, 2, OracleInput.East,
            "settle_timeout", 2, ProtocolSamples.MovedCapture));
        Check.True(ContainsBytes(east,
            new UTF8Encoding(false, true).GetBytes("\"input\":\"East\"")),
            "East exact wire spelling");
    }

    private static void CanonicalStrings()
    {
        string[,] cases = new string[,]
        {
            { "plain", "\"raw_save\":\"plain\"" },
            { "\"", "\"raw_save\":\"\\\"\"" },
            { "\\", "\"raw_save\":\"\\\\\"" },
            { "\b\f\n\r\t", "\"raw_save\":\"\\b\\f\\n\\r\\t\"" },
            { "\u0000\u0001\u001f", "\"raw_save\":\"\\u0000\\u0001\\u001f\"" },
            { "é/雪", "\"raw_save\":\"é/雪\"" },
            { "\ud83d\ude00", "\"raw_save\":\"😀\"" }
        };
        for (int index = 0; index < cases.GetLength(0); index++)
        {
            string encoded = new UTF8Encoding(false, true).GetString(
                CanonicalJson.EncodeInitial(new InitialRecord(
                    ProtocolSamples.RunId, ProtocolSamples.Capture(cases[index, 0]))));
            Check.True(encoded.IndexOf(cases[index, 1], StringComparison.Ordinal) >= 0,
                "canonical string " + index);
        }
        byte[] supplementary = CanonicalJson.EncodeInitial(new InitialRecord(
            ProtocolSamples.RunId, ProtocolSamples.Capture("\ud83d\ude00")));
        Check.True(ContainsBytes(supplementary,
            new byte[] { 0xf0, 0x9f, 0x98, 0x80 }),
            "U+1F600 exact UTF-8 bytes");
        CultureInfo prior = CultureInfo.CurrentCulture;
        try
        {
            CultureInfo.CurrentCulture = new CultureInfo("fr-FR");
            Check.Bytes(ReadFixtureLines(Path.Combine(
                "tests", "fixtures", "oracle_trace", "passive-success.ndjson"))[0],
                CanonicalJson.EncodeRun(ProtocolSamples.Run), "culture-invariant run");
        }
        finally
        {
            CultureInfo.CurrentCulture = prior;
        }
    }

    private static bool ContainsBytes(byte[] haystack, byte[] needle)
    {
        for (int start = 0; start <= haystack.Length - needle.Length; start++)
        {
            int offset = 0;
            while (offset < needle.Length
                && haystack[start + offset] == needle[offset])
            {
                offset++;
            }
            if (offset == needle.Length)
                return true;
        }
        return false;
    }

    private static void RejectsSurrogates()
    {
        string[] invalid = new string[] { "\ud800", "\udfff", "x\ud800y" };
        for (int index = 0; index < invalid.Length; index++)
        {
            CaptureRecord capture = ProtocolSamples.Capture(invalid[index]);
            Check.Throws<CanonicalEncodingException>(
                delegate { CanonicalJson.EncodeInitial(
                    new InitialRecord(ProtocolSamples.RunId, capture)); },
                "encoder surrogate " + index);
        }
    }
}
```

Add `EncodingTests.Register(tests)` after `ProtocolTests.Register(tests)` and
replace the Task 1 manifest with this exact current manifest:

```csharp
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 3 }
});
```

- [ ] **Step 2: Run the encoder cohort and confirm RED**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding
```

Require missing encoder symbols, not a missing fixture.

- [ ] **Step 3: Implement canonical scalar emission and exact record order**

Create `CanonicalJson.cs` with this complete implementation. It uses strict
UTF-8, validates every UTF-16 scalar before encoding, emits literal `/`, and
calls the line bound only after a complete object exists:

```csharp
using System;
using System.Globalization;
using System.IO;
using System.Text;

internal sealed class CanonicalEncodingException : Exception
{
    internal CanonicalEncodingException(string message)
        : base(message)
    {
    }

    internal CanonicalEncodingException(string message, Exception inner)
        : base(message, inner)
    {
    }
}

internal sealed class RecordTooLargeException : Exception
{
    internal RecordTooLargeException()
        : base("encoded trace record exceeded its limit")
    {
    }
}

internal static class CanonicalJson
{
    private static readonly UTF8Encoding StrictUtf8Encoding =
        new UTF8Encoding(false, true);

    internal static byte[] EncodeRun(RunRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"run\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"mode\":\"passive\",\"game_assembly_sha256\":");
            WriteString(output, record.GameAssemblySha256);
            WriteAscii(output, ",\"plugin_version\":");
            WriteString(output, record.PluginVersion);
            WriteAscii(output, ",\"input_sha256\":null,\"expected_input_count\":");
            WriteInt(output, record.ExpectedInputCount);
            WriteAscii(output, ",\"started_at_utc\":");
            WriteTimestamp(output, record.StartedAtUtc);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeInitial(InitialRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"initial\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_index\":null,\"capture\":");
            WriteCapture(output, record.Capture);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeStep(StepRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"step\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_index\":");
            WriteInt(output, record.InputIndex);
            WriteAscii(output, ",\"input\":");
            WriteString(output, record.Input.ToString());
            WriteAscii(output, ",\"accepted\":");
            WriteBool(output, record.Accepted);
            WriteAscii(output, ",\"movement_scheduled\":");
            WriteBool(output, record.MovementScheduled);
            WriteAscii(output, ",\"settle_frames\":");
            WriteInt(output, record.SettleFrames);
            WriteAscii(output, ",\"state_replaced\":false,\"capture\":");
            WriteCapture(output, record.Capture);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeEnd(EndRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"end\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_count\":");
            WriteInt(output, record.InputCount);
            WriteAscii(output, ",\"finished_at_utc\":");
            WriteTimestamp(output, record.FinishedAtUtc);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static byte[] EncodeError(ErrorRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        using (MemoryStream output = new MemoryStream())
        {
            WriteAscii(output, "{\"kind\":\"error\",\"schema_version\":1,\"run_id\":");
            WriteString(output, record.RunId);
            WriteAscii(output, ",\"input_index\":");
            if (record.InputIndex.HasValue)
                WriteInt(output, record.InputIndex.Value);
            else
                WriteAscii(output, "null");
            WriteAscii(output, ",\"input\":");
            if (record.Input.HasValue)
                WriteString(output, record.Input.Value.ToString());
            else
                WriteAscii(output, "null");
            WriteAscii(output, ",\"code\":");
            WriteString(output, record.Code);
            WriteAscii(output, ",\"message\":");
            WriteString(output, record.Message);
            WriteAscii(output, ",\"settle_frames\":");
            WriteInt(output, record.SettleFrames);
            WriteAscii(output, ",\"last_capture\":");
            if (record.LastCapture == null)
                WriteAscii(output, "null");
            else
                WriteCapture(output, record.LastCapture);
            WriteAscii(output, "}");
            return Finish(output);
        }
    }

    internal static void ValidateRecordSize(byte[] encoded)
    {
        if (encoded == null)
            throw new ArgumentNullException("encoded");
        if ((long)encoded.Length + 1L > 16L * 1024L * 1024L)
            throw new RecordTooLargeException();
    }

    internal static byte[] StrictUtf8(string value)
    {
        if (value == null)
            throw new ArgumentNullException("value");
        for (int index = 0; index < value.Length; index += ScalarLength(value, index))
        {
        }
        try
        {
            return StrictUtf8Encoding.GetBytes(value);
        }
        catch (EncoderFallbackException error)
        {
            throw new CanonicalEncodingException("invalid UTF-16 text", error);
        }
    }

    private static byte[] Finish(MemoryStream output)
    {
        byte[] encoded = output.ToArray();
        ValidateRecordSize(encoded);
        return encoded;
    }

    private static void WriteCapture(MemoryStream output, CaptureRecord capture)
    {
        WriteAscii(output, "{\"raw_save\":");
        WriteString(output, capture.RawSave);
        WriteAscii(output, ",\"state_identity\":");
        WriteString(output, capture.StateIdentity);
        WriteAscii(output, ",\"level\":");
        WriteString(output, capture.Level);
        WriteAscii(output, ",\"overworld\":");
        WriteBool(output, capture.Overworld);
        WriteAscii(output, ",\"won\":");
        WriteBool(output, capture.Won);
        WriteAscii(output, ",\"returning\":");
        WriteBool(output, capture.Returning);
        WriteAscii(output, ",\"have_ever_cooked_all\":");
        WriteBool(output, capture.HaveEverCookedAll);
        WriteAscii(output, ",\"lost_reason\":");
        WriteString(output, capture.LostReason);
        WriteAscii(output, ",\"display_name\":");
        WriteString(output, capture.DisplayName);
        WriteAscii(output, ",\"sausages_cooked\":");
        WriteInt(output, capture.SausagesCooked);
        WriteAscii(output, ",\"movement_count\":");
        WriteInt(output, capture.MovementCount);
        WriteAscii(output, ",\"pushes_to_try\":");
        WriteInt(output, capture.PushesToTry);
        WriteAscii(output, "}");
    }

    private static void WriteTimestamp(MemoryStream output, DateTime value)
    {
        OracleValidation.Utc(value, "value");
        string text = value.ToString("O", CultureInfo.InvariantCulture);
        if (!IsTimestamp(text))
            throw new CanonicalEncodingException("noncanonical UTC timestamp");
        WriteString(output, text);
    }

    private static bool IsTimestamp(string value)
    {
        if (value.Length != 28
            || value[4] != '-'
            || value[7] != '-'
            || value[10] != 'T'
            || value[13] != ':'
            || value[16] != ':'
            || value[19] != '.'
            || value[27] != 'Z')
        {
            return false;
        }
        for (int index = 0; index < value.Length; index++)
        {
            if (index == 4 || index == 7 || index == 10 || index == 13
                || index == 16 || index == 19 || index == 27)
            {
                continue;
            }
            if (value[index] < '0' || value[index] > '9')
                return false;
        }
        return true;
    }

    private static void WriteString(MemoryStream output, string value)
    {
        if (value == null)
            throw new ArgumentNullException("value");
        WriteAscii(output, "\"");
        int literalStart = 0;
        int index = 0;
        while (index < value.Length)
        {
            char current = value[index];
            if (current == '"' || current == '\\' || current < 0x20)
            {
                WriteUtf8(output, value, literalStart, index - literalStart);
                if (current == '"')
                    WriteAscii(output, "\\\"");
                else if (current == '\\')
                    WriteAscii(output, "\\\\");
                else
                    WriteAscii(output, ControlEscape(current));
                index++;
                literalStart = index;
            }
            else
            {
                index += ScalarLength(value, index);
            }
        }
        WriteUtf8(output, value, literalStart, value.Length - literalStart);
        WriteAscii(output, "\"");
    }

    private static int ScalarLength(string value, int index)
    {
        char current = value[index];
        if (char.IsHighSurrogate(current))
        {
            if (index + 1 >= value.Length
                || !char.IsLowSurrogate(value[index + 1]))
            {
                throw new CanonicalEncodingException(
                    "unpaired UTF-16 surrogate");
            }
            return 2;
        }
        if (char.IsLowSurrogate(current))
            throw new CanonicalEncodingException("unpaired UTF-16 surrogate");
        return 1;
    }

    private static string ControlEscape(char value)
    {
        switch (value)
        {
            case '\b': return "\\b";
            case '\f': return "\\f";
            case '\n': return "\\n";
            case '\r': return "\\r";
            case '\t': return "\\t";
            default:
                const string Hex = "0123456789abcdef";
                return "\\u00" + Hex[(value >> 4) & 15] + Hex[value & 15];
        }
    }

    private static void WriteBool(MemoryStream output, bool value)
    {
        WriteAscii(output, value ? "true" : "false");
    }

    private static void WriteInt(MemoryStream output, int value)
    {
        WriteAscii(output, value.ToString(CultureInfo.InvariantCulture));
    }

    private static void WriteAscii(MemoryStream output, string value)
    {
        for (int index = 0; index < value.Length; index++)
        {
            if (value[index] > 0x7f)
                throw new InvalidOperationException("non-ASCII punctuation");
            output.WriteByte((byte)value[index]);
        }
    }

    private static void WriteUtf8(
        MemoryStream output,
        string value,
        int start,
        int count)
    {
        if (count == 0)
            return;
        byte[] buffer = new byte[StrictUtf8Encoding.GetMaxByteCount(count)];
        int written;
        try
        {
            written = StrictUtf8Encoding.GetBytes(
                value, start, count, buffer, 0);
        }
        catch (EncoderFallbackException error)
        {
            throw new CanonicalEncodingException("invalid UTF-16 text", error);
        }
        output.Write(buffer, 0, written);
    }
}
```

- [ ] **Step 4: Prove the hardened assertions with one controlled mutant at a time**

First require that `CanonicalJson.cs` is byte-for-byte the exact implementation
from Step 3:

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Apply the supplementary-pair mutant with `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-            return 2;
+            throw new CanonicalEncodingException(
+                "paired UTF-16 surrogate");
*** End Patch
```

Run exactly and require the named existing registration to fail:

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "supplementary-pair mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'canonical string scalars'"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`, then require the planned hash:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-            throw new CanonicalEncodingException(
-                "paired UTF-16 surrogate");
+            return 2;
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Apply the nullable-error mutant with `apply_patch`; it changes only the branch
that must retain a non-null index when `input` is null:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-            if (record.InputIndex.HasValue)
+            if (record.Input.HasValue)
                 WriteInt(output, record.InputIndex.Value);
*** End Patch
```

Run exactly and require the independently hand-written error bytes in the
named existing registration to fail:

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "nullable-error mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'golden fixture bytes'"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`, then require the planned hash:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-            if (record.Input.HasValue)
+            if (record.InputIndex.HasValue)
                 WriteInt(output, record.InputIndex.Value);
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Apply the South-only wire-spelling mutant with `apply_patch`; the pre-existing
West, North, and Undo fixtures remain unchanged, so only the new South
assertion can catch it:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-            WriteString(output, record.Input.ToString());
+            WriteString(output, record.Input == OracleInput.South
+                ? "south" : record.Input.ToString());
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "South wire-spelling mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'golden fixture bytes'"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`, then require the planned hash:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-            WriteString(output, record.Input == OracleInput.South
-                ? "south" : record.Input.ToString());
+            WriteString(output, record.Input.ToString());
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Apply the East-only wire-spelling mutant with `apply_patch`; the pre-existing
North error fixture remains unchanged, so only the new East assertion can
catch it:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-                WriteString(output, record.Input.Value.ToString());
+                WriteString(output, record.Input.Value == OracleInput.East
+                    ? "east" : record.Input.Value.ToString());
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "East wire-spelling mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'golden fixture bytes'"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`, require the planned hash once
more, and confirm that no mutant was staged:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-                WriteString(output, record.Input.Value == OracleInput.East
-                    ? "east" : record.Input.Value.ToString());
+                WriteString(output, record.Input.Value.ToString());
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

- [ ] **Step 5: Run final GREEN and the net35 gate**

Run `encoding=3`, then the net35 Core gate. Require exact fixture/scalar/
surrogate behavior, run the diff check, and retain the output for post-commit
review:

```bash
set -euo pipefail
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

- [ ] **Step 6: Commit only the Task 2.1 encoder slice**

```bash
git add oracle/plugin/Core/CanonicalJson.cs \
  oracle/plugin/tests/EncodingTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: encode canonical oracle json"
```

#### Task 2.2: Pin complete-capture signatures and fixture bytes

- [ ] **Step 1: Add the final two RED registrations and boundary tests**

Create `CaptureSignatureTests.cs` exactly as follows and register it after
`EncodingTests`. This complete C# 7.3 two-test increment retains the existing
registration identities and ordering, pins three externally calculated
digests, proves that every capture field affects the signature, exercises all
reachable unrestricted-string surrogate paths, and derives the line limit
directly without a search loop.

```csharp
using System;
using System.Globalization;

internal static class CaptureSignatureTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("encoding", "capture signature is exact", ExactSignature);
        tests.Add("encoding", "record line limit includes LF", ExactLineLimit);
    }

    private static byte[] Hex(string value)
    {
        byte[] bytes = new byte[value.Length / 2];
        for (int index = 0; index < bytes.Length; index++)
        {
            bytes[index] = Byte.Parse(
                value.Substring(index * 2, 2),
                NumberStyles.HexNumber,
                CultureInfo.InvariantCulture);
        }
        return bytes;
    }

    private static bool SameSignature(CaptureRecord left, CaptureRecord right)
    {
        return Convert.ToBase64String(CaptureSignature.Compute(left)) ==
            Convert.ToBase64String(CaptureSignature.Compute(right));
    }

    private static void ExactSignature()
    {
        CaptureRecord left = new CaptureRecord(
            "a", "12", "c", false, false, false, false, "", "", 0, 0, 0);
        CaptureRecord right = new CaptureRecord(
            "a1", "2", "c", false, false, false, false, "", "", 0, 0, 0);
        Check.False(
            SameSignature(left, right),
            "length prefixes prevent concatenation collision");

        CaptureRecord vectorB = new CaptureRecord(
            "r2", "42", "l2", false, true, true, false, "lost2", "display2",
            1, 2, 3);
        CaptureRecord[] variants = new CaptureRecord[]
        {
            new CaptureRecord(
                "r3", "42", "l2", false, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "43", "l2", false, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l3", false, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", true, true, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, false, true, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, false, false,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, true,
                "lost2", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost3", "display2", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display3", 1, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display2", 4, 2, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display2", 1, 5, 3),
            new CaptureRecord(
                "r2", "42", "l2", false, true, true, false,
                "lost2", "display2", 1, 2, 6)
        };
        string[] fieldMessages = new string[]
        {
            "signature binds raw_save",
            "signature binds state_identity",
            "signature binds level",
            "signature binds overworld",
            "signature binds won",
            "signature binds returning",
            "signature binds have_ever_cooked_all",
            "signature binds lost_reason",
            "signature binds display_name",
            "signature binds sausages_cooked",
            "signature binds movement_count",
            "signature binds pushes_to_try"
        };
        Check.Equal(12, variants.Length, "one variant per capture field");
        Check.Equal(12, fieldMessages.Length, "one message per capture field");
        for (int index = 0; index < variants.Length; index++)
        {
            Check.False(
                SameSignature(vectorB, variants[index]),
                fieldMessages[index]);
        }

        Check.Bytes(
            Hex("c870e028a5a526efc0e8af5f78bcea1ff89198b29b16a875715c65f78649c6b7"),
            CaptureSignature.Compute(ProtocolSamples.InitialCapture),
            "fixed length-prefixed signature");

        CaptureRecord vectorA = new CaptureRecord(
            "é/雪", "-2147483648", "x", true, false, true, false, "", "z",
            Int32.MaxValue, 0, 0);
        Check.Bytes(
            Hex("6e924d4765c53622d9f734126cdf960fd525cc8a491068fe606606fb0833eac6"),
            CaptureSignature.Compute(vectorA),
            "fixed signature vector A");
        Check.Bytes(
            Hex("2ad1bf134d02a71476f3b7c220d817700079c10051607ab2796a2126406dde8d"),
            CaptureSignature.Compute(vectorB),
            "fixed signature vector B");

        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "\ud800", "7", "level", false, false, false, false,
                    "lost", "display", 4, 5, 6));
            },
            "signature rejects raw_save unpaired surrogate");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "raw", "7", "\ud800", false, false, false, false,
                    "lost", "display", 4, 5, 6));
            },
            "signature rejects level unpaired surrogate");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "raw", "7", "level", false, false, false, false,
                    "\ud800", "display", 4, 5, 6));
            },
            "signature rejects lost_reason unpaired surrogate");
        Check.Throws<CanonicalEncodingException>(
            delegate
            {
                CaptureSignature.Compute(new CaptureRecord(
                    "raw", "7", "level", false, false, false, false,
                    "lost", "\ud800", 4, 5, 6));
            },
            "signature rejects display_name unpaired surrogate");
    }

    private static ErrorRecord ErrorWithRawSaveLength(int length)
    {
        return new ErrorRecord(
            ProtocolSamples.RunId,
            1,
            OracleInput.North,
            "settle_timeout",
            600,
            ProtocolSamples.Capture(new string('x', length)));
    }

    private static void ExactLineLimit()
    {
        byte[] zeroLength = CanonicalJson.EncodeError(
            ErrorWithRawSaveLength(0));
        Check.Equal(421, zeroLength.Length, "zero-length boundary record bytes");

        const int AcceptedRawSaveLength = 16776794;
        byte[] exact;
        try
        {
            exact = CanonicalJson.EncodeError(
                ErrorWithRawSaveLength(AcceptedRawSaveLength));
        }
        catch (RecordTooLargeException error)
        {
            throw new InvalidOperationException(
                "exact record boundary is accepted", error);
        }
        Check.Equal(16777215, exact.Length, "exact JSON length before LF");
        Check.Equal(
            16777216,
            exact.Length + 1,
            "record boundary includes LF");
        Check.Throws<RecordTooLargeException>(
            delegate
            {
                CanonicalJson.EncodeError(
                    ErrorWithRawSaveLength(AcceptedRawSaveLength + 1));
            },
            "one byte beyond record boundary");
    }
}
```

Add `CaptureSignatureTests.Register(tests)` and update the cumulative manifest
to `protocol=4, encoding=5`.

- [ ] **Step 2: Run RED for the missing capture-signature implementation**

Run `--cohort encoding` and require a compiler diagnostic naming
`CaptureSignature`; do not accept an SDK, asset, or fixture failure.

- [ ] **Step 3: Implement length-prefixed capture hashing and line bounds**

Create `CaptureSignature.cs` with this complete one-hash implementation. Each
logical value is prefixed independently, so concatenation collisions remain
distinct:

```csharp
using System;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;

internal static class CaptureSignature
{
    private static readonly Encoding Ascii = Encoding.ASCII;

    internal static byte[] Compute(CaptureRecord capture)
    {
        if (capture == null)
            throw new ArgumentNullException("capture");
        using (SHA256 hash = SHA256.Create())
        {
            Feed(hash, CanonicalJson.StrictUtf8(capture.RawSave));
            Feed(hash, CanonicalJson.StrictUtf8(capture.StateIdentity));
            Feed(hash, CanonicalJson.StrictUtf8(capture.Level));
            Feed(hash, Boolean(capture.Overworld));
            Feed(hash, Boolean(capture.Won));
            Feed(hash, Boolean(capture.Returning));
            Feed(hash, Boolean(capture.HaveEverCookedAll));
            Feed(hash, CanonicalJson.StrictUtf8(capture.LostReason));
            Feed(hash, CanonicalJson.StrictUtf8(capture.DisplayName));
            Feed(hash, Integer(capture.SausagesCooked));
            Feed(hash, Integer(capture.MovementCount));
            Feed(hash, Integer(capture.PushesToTry));
            hash.TransformFinalBlock(new byte[0], 0, 0);
            return (byte[])hash.Hash.Clone();
        }
    }

    private static byte[] Boolean(bool value)
    {
        return Ascii.GetBytes(value ? "true" : "false");
    }

    private static byte[] Integer(int value)
    {
        return Ascii.GetBytes(value.ToString(CultureInfo.InvariantCulture));
    }

    private static void Feed(SHA256 hash, byte[] value)
    {
        int length = value.Length;
        byte[] prefix = new byte[4];
        prefix[0] = (byte)((length >> 24) & 0xff);
        prefix[1] = (byte)((length >> 16) & 0xff);
        prefix[2] = (byte)((length >> 8) & 0xff);
        prefix[3] = (byte)(length & 0xff);
        hash.TransformBlock(prefix, 0, prefix.Length, prefix, 0);
        if (value.Length != 0)
            hash.TransformBlock(value, 0, value.Length, value, 0);
    }
}
```

- [ ] **Step 4: Prove the hardened assertions with six controlled mutants**

Apply every mutant separately with `apply_patch`, run only the encoding cohort
with `--no-restore`, require nonzero plus the exact test identity and intended
assertion/error text, and immediately apply the exact inverse patch. Never
stage a mutant. After each inverse, the fail-fast pristine gate pins both
production hashes and requires an empty index.

Before applying the first mutant, require the reviewed production hashes and
an empty index in one fail-fast gate:

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Delete the four-byte prefix feed:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
-        hash.TransformBlock(prefix, 0, prefix.Length, prefix, 0);
         if (value.Length != 0)
             hash.TransformBlock(value, 0, value.Length, value, 0);
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "length-prefix mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'capture signature is exact'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"length prefixes prevent concatenation collision"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
+        hash.TransformBlock(prefix, 0, prefix.Length, prefix, 0);
         if (value.Length != 0)
             hash.TransformBlock(value, 0, value.Length, value, 0);
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Delete the `DisplayName` feed:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
-            Feed(hash, CanonicalJson.StrictUtf8(capture.DisplayName));
             Feed(hash, Integer(capture.SausagesCooked));
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "display_name omission mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'capture signature is exact'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"signature binds display_name"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
+            Feed(hash, CanonicalJson.StrictUtf8(capture.DisplayName));
             Feed(hash, Integer(capture.SausagesCooked));
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Swap the `Overworld` and `Returning` feeds. Vector A intentionally remains
unchanged because both values are `true`; vector B must fail its fixed digest:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
-            Feed(hash, Boolean(capture.Overworld));
+            Feed(hash, Boolean(capture.Returning));
             Feed(hash, Boolean(capture.Won));
-            Feed(hash, Boolean(capture.Returning));
+            Feed(hash, Boolean(capture.Overworld));
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "boolean-position swap mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'capture signature is exact'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"fixed signature vector B"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
-            Feed(hash, Boolean(capture.Returning));
+            Feed(hash, Boolean(capture.Overworld));
             Feed(hash, Boolean(capture.Won));
-            Feed(hash, Boolean(capture.Overworld));
+            Feed(hash, Boolean(capture.Returning));
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Replace strict `DisplayName` encoding with permissive framework UTF-8:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
-            Feed(hash, CanonicalJson.StrictUtf8(capture.DisplayName));
+            Feed(hash, Encoding.UTF8.GetBytes(capture.DisplayName));
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "display_name permissive-UTF-8 mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'capture signature is exact'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"signature rejects display_name unpaired surrogate: no exception"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CaptureSignature.cs
@@
-            Feed(hash, Encoding.UTF8.GetBytes(capture.DisplayName));
+            Feed(hash, CanonicalJson.StrictUtf8(capture.DisplayName));
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Make the canonical line bound ignore the final LF:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-        if ((long)encoded.Length + 1L > 16L * 1024L * 1024L)
+        if ((long)encoded.Length > 16L * 1024L * 1024L)
             throw new RecordTooLargeException();
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "LF-omission bound mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'record line limit includes LF'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"one byte beyond record boundary"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-        if ((long)encoded.Length > 16L * 1024L * 1024L)
+        if ((long)encoded.Length + 1L > 16L * 1024L * 1024L)
             throw new RecordTooLargeException();
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

Make the canonical line bound reject equality:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-        if ((long)encoded.Length + 1L > 16L * 1024L * 1024L)
+        if ((long)encoded.Length + 1L >= 16L * 1024L * 1024L)
             throw new RecordTooLargeException();
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding 2>&1)"; then
  printf '%s\n' "inclusive bound mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'encoding', test 'record line limit includes LF'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"exact record boundary is accepted"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/CanonicalJson.cs
@@
-        if ((long)encoded.Length + 1L >= 16L * 1024L * 1024L)
+        if ((long)encoded.Length + 1L > 16L * 1024L * 1024L)
             throw new RecordTooLargeException();
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/CaptureSignature.cs | awk '{print $1}')" = \
  "335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54"
test "$(shasum -a 256 oracle/plugin/Core/CanonicalJson.cs | awk '{print $1}')" = \
  "7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c"
test -z "$(git diff --cached --name-only)"
```

- [ ] **Step 5: Run both framework gates**

```bash
set -euo pipefail
encoding_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort encoding)"
test "$encoding_output" = "SSR oracle unit harness ready"
printf '%s\n' "$encoding_output"
build_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror)"
printf '%s\n' "$build_output"
case "$build_output" in
  *"Build succeeded."*"0 Warning(s)"*"0 Error(s)"*) ;;
  *) exit 1 ;;
esac
git diff --check
```

Require exact stdout `SSR oracle unit harness ready`, net35 `Build succeeded.`
with `0 Warning(s)` and `0 Error(s)`, and an empty `git diff --check` result.
Retain the outputs in the task report for post-commit review.

- [ ] **Step 6: Commit only the Task 2.2 signature slice**

```bash
git add oracle/plugin/Core/CaptureSignature.cs \
  oracle/plugin/tests/CaptureSignatureTests.cs \
  oracle/plugin/tests/Program.cs
git commit -m "test: pin oracle wire fixtures"
```

### Track 3: Add the create-new flushed NDJSON sink

**Files:**
- Create: `oracle/plugin/Core/NdjsonTraceSink.cs`
- Create: `oracle/plugin/tests/TraceSinkTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Produces exactly:

```csharp
using System;
using System.IO;
using System.Runtime.InteropServices;

internal interface ITraceSink
{
    void WriteRun(RunRecord record);
    void WriteInitial(InitialRecord record);
    void WriteStep(StepRecord record);
    void WriteEnd(EndRecord record);
    void WriteError(ErrorRecord record);
    void Close();
}

internal sealed class TraceIoException : Exception
{
    internal TraceIoException(string message, Exception inner)
        : base(message, inner)
    {
    }

    internal TraceIoException(string message)
        : base(message)
    {
    }
}

internal sealed class TraceExistsException : Exception
{
    internal TraceExistsException(string path, Exception inner)
        : base("trace target already exists: " + path, inner)
    {
    }
}
```

- Produces: `NdjsonTraceSink.Create(string outputDirectory, string runName) -> NdjsonTraceSink`.
- Produces: internal `ITraceOutput` seam used only to inject write, flush, short-write, and close failures.
- Consumes `RecordTooLargeException` from Task 2 and produces
  `TraceIoException` for write, flush, close, and cumulative-file-budget
  failures; the driver maps them to the exact terminal policy.

`ITraceOutput` is exactly:

```csharp
internal interface ITraceOutput
{
    int Write(byte[] buffer, int offset, int count);
    void Flush();
    void Close();
}

internal interface ITraceFileFactory
{
    ITraceOutput CreateNew(
        string path, FileMode mode, FileAccess access, FileShare share);
}
```

The production adapter calls `FileStream.Write` once for the requested slice
and returns `count`; injected tests may return a positive short count or zero.
Zero before completion is a `TraceIoException`, preventing an infinite loop.
Schema-v1 per-record flush means legacy-compatible `FileStream.Flush()`; the
outer Python probe performs descriptor fsync after process termination before
registering the retained trace.

#### Task 3.1: Open trace files atomically with typed collisions

Retain the completed platform preflight in the task report: on macOS 26.6,
arm64, .NET 10.0.8, a real existing-file `FileMode.CreateNew` collision raised
`System.IO.IOException` with `HResult` and `Marshal.GetHRForException` both
equal to decimal 17 in 32 of 32 isolated attempts, while preserving the
existing bytes. The exact four-argument `FileStream` constructor and
`FileShare.None` also compiled against the installed net35 reference
assemblies. Do not repeat that separate platform probe during implementation.

- [ ] **Step 1: Add the first three exact RED sink tests**

Create `TraceSinkTests.cs` exactly as follows:

```csharp
using System;
using System.Collections.Generic;
using System.IO;

internal sealed class FakeTraceOutput : ITraceOutput
{
    internal readonly List<byte> Bytes = new List<byte>();
    internal readonly Queue<int> WriteCounts = new Queue<int>();
    internal Exception WriteFailure;
    internal Exception FlushFailure;
    internal Exception CloseFailure;
    internal int FlushCalls;
    internal int CloseCalls;

    public int Write(byte[] buffer, int offset, int count)
    {
        if (WriteFailure != null)
            throw WriteFailure;
        int written = WriteCounts.Count == 0 ? count : WriteCounts.Dequeue();
        if (written < 0 || written > count)
            throw new InvalidOperationException("invalid fake write count");
        for (int index = 0; index < written; index++)
            Bytes.Add(buffer[offset + index]);
        return written;
    }

    public void Flush()
    {
        FlushCalls++;
        if (FlushFailure != null)
            throw FlushFailure;
    }

    public void Close()
    {
        CloseCalls++;
        if (CloseFailure != null)
            throw CloseFailure;
    }
}

internal sealed class FakeTraceFileFactory : ITraceFileFactory
{
    internal FakeTraceOutput Output = new FakeTraceOutput();
    internal string Path;
    internal FileMode Mode;
    internal FileAccess Access;
    internal FileShare Share;
    internal Exception Failure;

    public ITraceOutput CreateNew(
        string path, FileMode mode, FileAccess access, FileShare share)
    {
        Path = path;
        Mode = mode;
        Access = access;
        Share = share;
        if (Failure != null)
            throw Failure;
        return Output;
    }
}

internal static class TraceSinkTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("sink", "factory arguments are exact", FactoryArguments);
        tests.Add("sink", "null factory output is typed", NullFactoryOutputIsTyped);
        tests.Add("sink", "real collision is typed", RealCollisionIsTyped);
    }

    private static void FactoryArguments()
    {
        FakeTraceFileFactory factory = new FakeTraceFileFactory();
        NdjsonTraceSink sink = NdjsonTraceSink.Create(
            "/private/tmp/output", "passive-trace", factory);
        Check.Equal(
            Path.Combine("/private/tmp/output", "passive-trace.ndjson"),
            factory.Path, "combined target");
        Check.Equal(FileMode.CreateNew, factory.Mode, "create-new mode");
        Check.Equal(FileAccess.Write, factory.Access, "write access");
        Check.Equal(FileShare.None, factory.Share, "exclusive sharing");
        sink.Close();
        Check.Equal(1, factory.Output.CloseCalls, "owned close");
    }

    private static void NullFactoryOutputIsTyped()
    {
        FakeTraceFileFactory factory = new FakeTraceFileFactory();
        factory.Output = null;
        Check.Throws<TraceIoException>(
            delegate
            {
                NdjsonTraceSink.Create(
                    "/private/tmp/output", "passive-trace", factory);
            },
            "null create-new result");

        FakeTraceFileFactory failing = new FakeTraceFileFactory();
        IOException injected = new IOException("injected create");
        failing.Failure = injected;
        IOException observed = Check.Throws<IOException>(
            delegate
            {
                NdjsonTraceSink.Create(
                    "/private/tmp/output", "passive-trace", failing);
            },
            "injected factory failure");
        Check.Same(injected, observed, "factory failure identity");
    }

    private static void RealCollisionIsTyped()
    {
        string directory = Path.Combine(
            Path.GetTempPath(), "ssr-oracle-sink-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        string path = Path.Combine(directory, "passive-trace.ndjson");
        NdjsonTraceSink unexpected = null;
        try
        {
            NdjsonTraceSink sink = NdjsonTraceSink.Create(directory, "passive-trace");
            sink.Close();
            byte[] sentinel = new byte[] { 0x00, 0x7f, 0x80, 0xff };
            File.WriteAllBytes(path, sentinel);
            Check.Bytes(
                sentinel,
                File.ReadAllBytes(path),
                "collision sentinel written");
            Check.Throws<TraceExistsException>(
                delegate
                {
                    unexpected = NdjsonTraceSink.Create(
                        directory, "passive-trace");
                },
                "atomic create-new collision");
            Check.Bytes(
                sentinel,
                File.ReadAllBytes(path),
                "collision preserves bytes");
        }
        finally
        {
            if (unexpected != null)
            {
                try
                {
                    unexpected.Close();
                }
                catch (Exception)
                {
                }
            }
            if (Directory.Exists(directory))
                Directory.Delete(directory, true);
        }
    }

    private static void RecordsUseLfAndFlush()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        sink.WriteRun(ProtocolSamples.Run);
        sink.WriteInitial(ProtocolSamples.Initial);
        Check.Equal(2, output.FlushCalls, "flush per record");
        byte[] run = CanonicalJson.EncodeRun(ProtocolSamples.Run);
        for (int index = 0; index < run.Length; index++)
            Check.Equal(run[index], output.Bytes[index], "run byte " + index);
        Check.Equal((byte)'\n', output.Bytes[run.Length], "run LF");
        Check.False(output.Bytes.Count >= 3
            && output.Bytes[0] == 0xef && output.Bytes[1] == 0xbb
            && output.Bytes[2] == 0xbf, "no BOM");
    }

    private static void SessionLimitIncludesLf()
    {
        byte[] run = CanonicalJson.EncodeRun(ProtocolSamples.Run);
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output, run.Length + 1L);
        sink.WriteRun(ProtocolSamples.Run);
        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); },
            "second line exceeds injected session limit");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteInitial(ProtocolSamples.Initial); },
            "failed sink rejects later record");
    }

    private static void WriteFailuresAreTerminal()
    {
        SessionLimitIncludesLf();

        FakeTraceOutput shortOutput = new FakeTraceOutput();
        shortOutput.WriteCounts.Enqueue(1);
        shortOutput.WriteCounts.Enqueue(0);
        NdjsonTraceSink shortSink = new NdjsonTraceSink(shortOutput);
        Check.Throws<TraceIoException>(
            delegate { shortSink.WriteRun(ProtocolSamples.Run); },
            "zero write progress");
        Check.Throws<TraceIoException>(
            delegate { shortSink.WriteRun(ProtocolSamples.Run); },
            "short-write failure is terminal");

        FakeTraceOutput writeOutput = new FakeTraceOutput();
        writeOutput.WriteFailure = new IOException("injected write");
        NdjsonTraceSink writeSink = new NdjsonTraceSink(writeOutput);
        Check.Throws<TraceIoException>(
            delegate { writeSink.WriteRun(ProtocolSamples.Run); }, "write failure");

        FakeTraceOutput flushOutput = new FakeTraceOutput();
        flushOutput.FlushFailure = new IOException("injected flush");
        NdjsonTraceSink flushSink = new NdjsonTraceSink(flushOutput);
        Check.Throws<TraceIoException>(
            delegate { flushSink.WriteRun(ProtocolSamples.Run); }, "flush failure");
        Check.Throws<TraceIoException>(
            delegate { flushSink.WriteRun(ProtocolSamples.Run); },
            "flush failure is terminal");
    }

    private static void CloseIsSingleUse()
    {
        FakeTraceOutput output = new FakeTraceOutput();
        NdjsonTraceSink sink = new NdjsonTraceSink(output);
        sink.Close();
        Check.Equal(1, output.CloseCalls, "one close");
        Check.Throws<InvalidOperationException>(delegate { sink.Close(); },
            "second close");
        Check.Throws<TraceIoException>(
            delegate { sink.WriteRun(ProtocolSamples.Run); }, "write after close");

        FakeTraceOutput failing = new FakeTraceOutput();
        failing.CloseFailure = new IOException("injected close");
        NdjsonTraceSink failingSink = new NdjsonTraceSink(failing);
        Check.Throws<TraceIoException>(delegate { failingSink.Close(); },
            "close failure typed");
        Check.Throws<InvalidOperationException>(delegate { failingSink.Close(); },
            "failed close not retried");
    }
}
```

Register `TraceSinkTests` after `CaptureSignatureTests`, then require the exact
current manifest `protocol=4`, `encoding=5`, `sink=3` with this exact patch:

```diff
*** Begin Patch
*** Update File: oracle/plugin/tests/Program.cs
@@
         EncodingTests.Register(tests);
         CaptureSignatureTests.Register(tests);
+        TraceSinkTests.Register(tests);
         tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
         {
             { "protocol", 4 },
-            { "encoding", 5 }
+            { "encoding", 5 },
+            { "sink", 3 }
         });
*** End Patch
```

- [ ] **Step 2: Run RED**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink
```

Require a compiler RED naming `ITraceOutput` or `NdjsonTraceSink`; a package,
SDK, or filesystem-permission failure is not the intended RED.

- [ ] **Step 3: Implement atomic create-new ownership**

Create `NdjsonTraceSink.cs` exactly as follows. The complete source repeats the
Track 3 imports, interfaces, and typed exceptions so this task's extracted
brief is self-contained. It deliberately supports only atomic creation and
owned close; the three unregistered write-policy methods in the test file
compile against its constructors but remain dormant until Task 3.2.

```csharp
using System;
using System.IO;
using System.Runtime.InteropServices;

internal interface ITraceSink
{
    void WriteRun(RunRecord record);
    void WriteInitial(InitialRecord record);
    void WriteStep(StepRecord record);
    void WriteEnd(EndRecord record);
    void WriteError(ErrorRecord record);
    void Close();
}

internal sealed class TraceIoException : Exception
{
    internal TraceIoException(string message, Exception inner)
        : base(message, inner)
    {
    }

    internal TraceIoException(string message)
        : base(message)
    {
    }
}

internal sealed class TraceExistsException : Exception
{
    internal TraceExistsException(string path, Exception inner)
        : base("trace target already exists: " + path, inner)
    {
    }
}

internal interface ITraceOutput
{
    int Write(byte[] buffer, int offset, int count);
    void Flush();
    void Close();
}

internal interface ITraceFileFactory
{
    ITraceOutput CreateNew(
        string path, FileMode mode, FileAccess access, FileShare share);
}

internal sealed class NdjsonTraceSink : ITraceSink
{
    private sealed class FileTraceFactory : ITraceFileFactory
    {
        public ITraceOutput CreateNew(
            string path, FileMode mode, FileAccess access, FileShare share)
        {
            try
            {
                return new FileTraceOutput(
                    new FileStream(path, mode, access, share));
            }
            catch (IOException error)
            {
                int native = Marshal.GetHRForException(error) & 0xffff;
                if (native == 17 || native == 80 || native == 183)
                    throw new TraceExistsException(path, error);
                throw new TraceIoException("trace create-new failed", error);
            }
            catch (Exception error)
            {
                throw new TraceIoException("trace create-new failed", error);
            }
        }
    }

    private sealed class FileTraceOutput : ITraceOutput
    {
        private readonly FileStream stream;

        internal FileTraceOutput(FileStream stream)
        {
            this.stream = stream;
        }

        public int Write(byte[] buffer, int offset, int count)
        {
            stream.Write(buffer, offset, count);
            return count;
        }

        public void Flush()
        {
            stream.Flush();
        }

        public void Close()
        {
            stream.Close();
        }
    }

    private readonly ITraceOutput output;
    private bool closeAttempted;

    internal NdjsonTraceSink(ITraceOutput output)
        : this(output, 128L * 1024L * 1024L)
    {
    }

    internal NdjsonTraceSink(ITraceOutput output, long maxTraceBytes)
    {
        if (output == null)
            throw new ArgumentNullException("output");
        if (maxTraceBytes <= 0L || maxTraceBytes > 128L * 1024L * 1024L)
            throw new ArgumentOutOfRangeException("maxTraceBytes");
        this.output = output;
    }

    internal static NdjsonTraceSink Create(
        string outputDirectory,
        string runName)
    {
        return Create(outputDirectory, runName, new FileTraceFactory());
    }

    internal static NdjsonTraceSink Create(
        string outputDirectory,
        string runName,
        ITraceFileFactory factory)
    {
        if (outputDirectory == null)
            throw new ArgumentNullException("outputDirectory");
        if (runName == null)
            throw new ArgumentNullException("runName");
        if (factory == null)
            throw new ArgumentNullException("factory");
        string path = Path.Combine(outputDirectory, runName + ".ndjson");
        ITraceOutput created = factory.CreateNew(
            path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        if (created == null)
            throw new TraceIoException("trace factory returned null");
        return new NdjsonTraceSink(created);
    }

    public void WriteRun(RunRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteInitial(InitialRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteStep(StepRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteEnd(EndRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void WriteError(ErrorRecord record)
    {
        throw new NotSupportedException("record writing begins in Task 3.2");
    }

    public void Close()
    {
        if (closeAttempted)
            throw new InvalidOperationException("trace close already attempted");
        closeAttempted = true;
        try
        {
            output.Close();
        }
        catch (Exception error)
        {
            throw new TraceIoException("trace close failed", error);
        }
    }
}
```

- [ ] **Step 4: Run the provisional GREEN and net35 gate**

Run the sink cohort and net35 Core gate in one fail-fast process. Require the
exact harness stdout, zero build warnings and errors, the three planned source
hashes, an empty index, and exactly the intended unstaged Task 3.1 slice:

```bash
set -euo pipefail
sink_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink)"
test "$sink_output" = "SSR oracle unit harness ready"
printf '%s\n' "$sink_output"
build_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror)"
printf '%s\n' "$build_output"
case "$build_output" in
  *"Build succeeded."*"0 Warning(s)"*"0 Error(s)"*) ;;
  *) exit 1 ;;
esac
git diff --check
test "$(shasum -a 256 oracle/plugin/Core/NdjsonTraceSink.cs | awk '{print $1}')" = \
  "bba8919d862c5216b4b03be99eba73178418ccdd4e4e2ade0dd3b32e36c1693f"
test "$(shasum -a 256 oracle/plugin/tests/TraceSinkTests.cs | awk '{print $1}')" = \
  "365be9a4aea65ba08102504cf00605e5ceaf8fc514ea6cf5f5939e7c236d9b59"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "e3a4a01ada6ee6281fc793f379b3feb9a16afc170f3eff27b0f9f274cd941b4c"
test -z "$(git diff --cached --name-only)"
test "$(git status --short)" = "$(printf '%s\n' \
  '?? oracle/plugin/Core/NdjsonTraceSink.cs' \
  ' M oracle/plugin/tests/Program.cs' \
  '?? oracle/plugin/tests/TraceSinkTests.cs')"
```

- [ ] **Step 5: Prove the hardened assertions with three controlled mutants**

Apply every mutant separately with `apply_patch`, run only the sink cohort with
`--no-restore`, require nonzero plus the exact test identity and intended
assertion text, and immediately apply the exact inverse patch. Never stage a
mutant. Before the first mutant and after every inverse, require the three
reviewed source hashes, an empty index, and exactly the intended unstaged Task
3.1 slice.

Run the initial pristine gate:

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/NdjsonTraceSink.cs | awk '{print $1}')" = \
  "bba8919d862c5216b4b03be99eba73178418ccdd4e4e2ade0dd3b32e36c1693f"
test "$(shasum -a 256 oracle/plugin/tests/TraceSinkTests.cs | awk '{print $1}')" = \
  "365be9a4aea65ba08102504cf00605e5ceaf8fc514ea6cf5f5939e7c236d9b59"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "e3a4a01ada6ee6281fc793f379b3feb9a16afc170f3eff27b0f9f274cd941b4c"
test -z "$(git diff --cached --name-only)"
test "$(git status --short)" = "$(printf '%s\n' \
  '?? oracle/plugin/Core/NdjsonTraceSink.cs' \
  ' M oracle/plugin/tests/Program.cs' \
  '?? oracle/plugin/tests/TraceSinkTests.cs')"
```

Delete the owned-output close:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/NdjsonTraceSink.cs
@@
         try
         {
-            output.Close();
         }
         catch (Exception error)
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink 2>&1)"; then
  printf '%s\n' "owned-close mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'sink', test 'factory arguments are exact'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"owned close"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/NdjsonTraceSink.cs
@@
         try
         {
+            output.Close();
         }
         catch (Exception error)
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/NdjsonTraceSink.cs | awk '{print $1}')" = \
  "bba8919d862c5216b4b03be99eba73178418ccdd4e4e2ade0dd3b32e36c1693f"
test "$(shasum -a 256 oracle/plugin/tests/TraceSinkTests.cs | awk '{print $1}')" = \
  "365be9a4aea65ba08102504cf00605e5ceaf8fc514ea6cf5f5939e7c236d9b59"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "e3a4a01ada6ee6281fc793f379b3feb9a16afc170f3eff27b0f9f274cd941b4c"
test -z "$(git diff --cached --name-only)"
test "$(git status --short)" = "$(printf '%s\n' \
  '?? oracle/plugin/Core/NdjsonTraceSink.cs' \
  ' M oracle/plugin/tests/Program.cs' \
  '?? oracle/plugin/tests/TraceSinkTests.cs')"
```

Make only the real file adapter overwrite instead of creating atomically. The
fake factory must still observe `FileMode.CreateNew`, so the first registration
continues to pass and the real-collision registration detects the defect:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/NdjsonTraceSink.cs
@@
                 return new FileTraceOutput(
-                    new FileStream(path, mode, access, share));
+                    new FileStream(path, FileMode.Create, access, share));
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink 2>&1)"; then
  printf '%s\n' "non-atomic create mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'sink', test 'real collision is typed'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"atomic create-new collision: no exception"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/NdjsonTraceSink.cs
@@
                 return new FileTraceOutput(
-                    new FileStream(path, FileMode.Create, access, share));
+                    new FileStream(path, mode, access, share));
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/NdjsonTraceSink.cs | awk '{print $1}')" = \
  "bba8919d862c5216b4b03be99eba73178418ccdd4e4e2ade0dd3b32e36c1693f"
test "$(shasum -a 256 oracle/plugin/tests/TraceSinkTests.cs | awk '{print $1}')" = \
  "365be9a4aea65ba08102504cf00605e5ceaf8fc514ea6cf5f5939e7c236d9b59"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "e3a4a01ada6ee6281fc793f379b3feb9a16afc170f3eff27b0f9f274cd941b4c"
test -z "$(git diff --cached --name-only)"
test "$(git status --short)" = "$(printf '%s\n' \
  '?? oracle/plugin/Core/NdjsonTraceSink.cs' \
  ' M oracle/plugin/tests/Program.cs' \
  '?? oracle/plugin/tests/TraceSinkTests.cs')"
```

Truncate an existing path immediately before the otherwise-correct atomic
open. The second create must still be typed as a collision, after which the
sentinel assertion detects the destructive pre-open write:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/NdjsonTraceSink.cs
@@
         {
             try
             {
+                if (File.Exists(path))
+                    File.WriteAllBytes(path, new byte[0]);
                 return new FileTraceOutput(
*** End Patch
```

```bash
set -euo pipefail
if mutation_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink 2>&1)"; then
  printf '%s\n' "pre-collision truncation mutant unexpectedly passed" >&2
  exit 1
fi
printf '%s\n' "$mutation_output"
case "$mutation_output" in
  *"cohort 'sink', test 'real collision is typed'"*) ;;
  *) exit 1 ;;
esac
case "$mutation_output" in
  *"collision preserves bytes"*) ;;
  *) exit 1 ;;
esac
```

Restore with the exact inverse `apply_patch`:

```diff
*** Begin Patch
*** Update File: oracle/plugin/Core/NdjsonTraceSink.cs
@@
         {
             try
             {
-                if (File.Exists(path))
-                    File.WriteAllBytes(path, new byte[0]);
                 return new FileTraceOutput(
*** End Patch
```

```bash
set -euo pipefail
test "$(shasum -a 256 oracle/plugin/Core/NdjsonTraceSink.cs | awk '{print $1}')" = \
  "bba8919d862c5216b4b03be99eba73178418ccdd4e4e2ade0dd3b32e36c1693f"
test "$(shasum -a 256 oracle/plugin/tests/TraceSinkTests.cs | awk '{print $1}')" = \
  "365be9a4aea65ba08102504cf00605e5ceaf8fc514ea6cf5f5939e7c236d9b59"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "e3a4a01ada6ee6281fc793f379b3feb9a16afc170f3eff27b0f9f274cd941b4c"
test -z "$(git diff --cached --name-only)"
test "$(git status --short)" = "$(printf '%s\n' \
  '?? oracle/plugin/Core/NdjsonTraceSink.cs' \
  ' M oracle/plugin/tests/Program.cs' \
  '?? oracle/plugin/tests/TraceSinkTests.cs')"
```

- [ ] **Step 6: Run the final framework gates**

```bash
set -euo pipefail
sink_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink)"
test "$sink_output" = "SSR oracle unit harness ready"
printf '%s\n' "$sink_output"
build_output="$(/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror)"
printf '%s\n' "$build_output"
case "$build_output" in
  *"Build succeeded."*"0 Warning(s)"*"0 Error(s)"*) ;;
  *) exit 1 ;;
esac
git diff --check
test "$(shasum -a 256 oracle/plugin/Core/NdjsonTraceSink.cs | awk '{print $1}')" = \
  "bba8919d862c5216b4b03be99eba73178418ccdd4e4e2ade0dd3b32e36c1693f"
test "$(shasum -a 256 oracle/plugin/tests/TraceSinkTests.cs | awk '{print $1}')" = \
  "365be9a4aea65ba08102504cf00605e5ceaf8fc514ea6cf5f5939e7c236d9b59"
test "$(shasum -a 256 oracle/plugin/tests/Program.cs | awk '{print $1}')" = \
  "e3a4a01ada6ee6281fc793f379b3feb9a16afc170f3eff27b0f9f274cd941b4c"
test -z "$(git diff --cached --name-only)"
test "$(git status --short)" = "$(printf '%s\n' \
  '?? oracle/plugin/Core/NdjsonTraceSink.cs' \
  ' M oracle/plugin/tests/Program.cs' \
  '?? oracle/plugin/tests/TraceSinkTests.cs')"
```

Require exact stdout `SSR oracle unit harness ready`, net35 `Build succeeded.`
with `0 Warning(s)` and `0 Error(s)`, exact planned source hashes, an empty
index, the exact three-file unstaged slice, and an empty `git diff --check`.
Retain all outputs in the task report for post-commit review.

- [ ] **Step 7: Commit only the Task 3.1 create-new slice**

```bash
git add oracle/plugin/Core/NdjsonTraceSink.cs \
  oracle/plugin/tests/TraceSinkTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: open oracle traces atomically"
```

#### Task 3.2: Flush bounded records and own terminal close

- [ ] **Step 1: Add only the final three RED registrations**

Replace only `TraceSinkTests.Register` with this cumulative block and raise the
temporary manifest from `sink=3` to `sink=6`.  The first failing registration
must be `records use LF and flush`; the Task 3.1 implementation throws before
writing any bytes.

```csharp
internal static void Register(TestRegistry tests)
{
    tests.Add("sink", "factory arguments are exact", FactoryArguments);
    tests.Add("sink", "null factory output is typed", NullFactoryOutputIsTyped);
    tests.Add("sink", "real collision is typed", RealCollisionIsTyped);
    tests.Add("sink", "records use LF and flush", RecordsUseLfAndFlush);
    tests.Add("sink", "bounds and write failures are terminal", WriteFailuresAreTerminal);
    tests.Add("sink", "close ownership is single use", CloseIsSingleUse);
}
```

Run the selected cohort and require that named behavioral RED.

- [ ] **Step 2: Run RED against the staged create-new sink**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink
```

Require `records use LF and flush` to fail from the staged write behavior, not
from a compiler, SDK, asset, or fixture failure.

- [ ] **Step 3: Implement exact write, flush, bound, and close transitions**

Replace the staged Task 3.1 `NdjsonTraceSink` class—leaving its interfaces and
typed exceptions unchanged—with this complete final implementation:

```csharp
internal sealed class NdjsonTraceSink : ITraceSink
{
    private const long DefaultMaxTraceBytes = 128L * 1024L * 1024L;

    private enum SinkState
    {
        Open,
        Failed,
        Closing,
        Closed,
        FailedClosed
    }

    private sealed class FileTraceFactory : ITraceFileFactory
    {
        public ITraceOutput CreateNew(
            string path, FileMode mode, FileAccess access, FileShare share)
        {
            try
            {
                return new FileTraceOutput(
                    new FileStream(path, mode, access, share));
            }
            catch (IOException error)
            {
                int native = Marshal.GetHRForException(error) & 0xffff;
                if (native == 17 || native == 80 || native == 183)
                    throw new TraceExistsException(path, error);
                throw new TraceIoException("trace create-new failed", error);
            }
            catch (Exception error)
            {
                throw new TraceIoException("trace create-new failed", error);
            }
        }
    }

    private sealed class FileTraceOutput : ITraceOutput
    {
        private readonly FileStream stream;

        internal FileTraceOutput(FileStream stream)
        {
            this.stream = stream;
        }

        public int Write(byte[] buffer, int offset, int count)
        {
            stream.Write(buffer, offset, count);
            return count;
        }

        public void Flush()
        {
            stream.Flush();
        }

        public void Close()
        {
            stream.Close();
        }
    }

    private static readonly byte[] LineFeed = new byte[] { (byte)'\n' };
    private readonly ITraceOutput output;
    private readonly long maxTraceBytes;
    private SinkState state;
    private long totalBytes;

    internal NdjsonTraceSink(ITraceOutput output)
        : this(output, DefaultMaxTraceBytes)
    {
    }

    internal NdjsonTraceSink(ITraceOutput output, long maxTraceBytes)
    {
        this.output = output ?? throw new ArgumentNullException("output");
        if (maxTraceBytes <= 0L || maxTraceBytes > DefaultMaxTraceBytes)
            throw new ArgumentOutOfRangeException("maxTraceBytes");
        this.maxTraceBytes = maxTraceBytes;
        state = SinkState.Open;
    }

    internal static NdjsonTraceSink Create(
        string outputDirectory,
        string runName)
    {
        return Create(outputDirectory, runName, new FileTraceFactory());
    }

    internal static NdjsonTraceSink Create(
        string outputDirectory,
        string runName,
        ITraceFileFactory factory)
    {
        if (outputDirectory == null)
            throw new ArgumentNullException("outputDirectory");
        if (runName == null)
            throw new ArgumentNullException("runName");
        if (factory == null)
            throw new ArgumentNullException("factory");
        string path = Path.Combine(outputDirectory, runName + ".ndjson");
        ITraceOutput created = factory.CreateNew(
            path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        if (created == null)
            throw new TraceIoException("trace factory returned null");
        return new NdjsonTraceSink(created);
    }

    public void WriteRun(RunRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeRun(record));
    }

    public void WriteInitial(InitialRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeInitial(record));
    }

    public void WriteStep(StepRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeStep(record));
    }

    public void WriteEnd(EndRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeEnd(record));
    }

    public void WriteError(ErrorRecord record)
    {
        if (record == null)
            throw new ArgumentNullException("record");
        EnsureWritable();
        WriteEncoded(CanonicalJson.EncodeError(record));
    }

    public void Close()
    {
        if (state != SinkState.Open && state != SinkState.Failed)
            throw new InvalidOperationException("trace close already attempted");
        bool alreadyFailed = state == SinkState.Failed;
        state = SinkState.Closing;
        try
        {
            output.Close();
        }
        catch (Exception error)
        {
            state = SinkState.FailedClosed;
            throw new TraceIoException("trace close failed", error);
        }
        state = alreadyFailed ? SinkState.FailedClosed : SinkState.Closed;
    }

    private void WriteEncoded(byte[] encoded)
    {
        CanonicalJson.ValidateRecordSize(encoded);
        long lineBytes = (long)encoded.Length + 1L;
        if (totalBytes > maxTraceBytes - lineBytes)
        {
            Fail();
            throw new TraceIoException("trace file budget exceeded");
        }
        WriteAll(encoded);
        WriteAll(LineFeed);
        try
        {
            output.Flush();
        }
        catch (Exception error)
        {
            Fail();
            throw new TraceIoException("trace flush failed", error);
        }
        totalBytes += lineBytes;
    }

    private void WriteAll(byte[] buffer)
    {
        int offset = 0;
        while (offset < buffer.Length)
        {
            int written;
            try
            {
                written = output.Write(buffer, offset, buffer.Length - offset);
            }
            catch (Exception error)
            {
                Fail();
                throw new TraceIoException("trace write failed", error);
            }
            if (written <= 0 || written > buffer.Length - offset)
            {
                Fail();
                throw new TraceIoException(
                    "trace output made invalid progress");
            }
            offset += written;
        }
    }

    private void EnsureWritable()
    {
        if (state != SinkState.Open)
            throw new TraceIoException("trace sink is not writable");
    }

    private void Fail()
    {
        state = SinkState.Failed;
    }
}
```

`Marshal.GetHRForException(error) & 0xffff` classifies only the
atomic `CreateNew` collision codes `EEXIST (17)`, `ERROR_FILE_EXISTS (80)`,
and `ERROR_ALREADY_EXISTS (183)` as `TraceExistsException`; it performs no
racy `File.Exists` recheck. Because encoding completes
before `WriteEncoded`, `CanonicalEncodingException` and
`RecordTooLargeException` leave the open sink reusable. Every write, flush,
close, invalid-progress, and cumulative-budget failure permanently blocks
later records; one best-effort Close remains legal after a write/flush failure.

- [ ] **Step 4: Run GREEN and the net35 gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort sink
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Require all six sink registrations to pass and retain the pristine output in
the task report for post-commit review.

- [ ] **Step 5: Commit only the Task 3.2 sink slice**

```bash
git add oracle/plugin/Core/NdjsonTraceSink.cs \
  oracle/plugin/tests/TraceSinkTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: flush bounded oracle traces"
```

### Track 4: Stage update authorization and settle the initial state

#### Task 4.1: Add issued-authorized-consumed update and hook boundaries

- [ ] **Step 1: Write the two exact RED token-lifecycle tests**

**Files:**
- Create: oracle/plugin/Core/CaptureException.cs
- Create: oracle/plugin/Core/PassiveDriverBoundaries.cs
- Create: oracle/plugin/tests/PassiveDriverBoundaryTests.cs
- Modify: oracle/plugin/tests/Program.cs

**Interfaces:**
- Produces CaptureException in its own Core/CaptureException.cs file, plus
  HookKind, owner-bound HookToken, staged UpdateDirective, GateSampleKind,
  GateSample, and IPassiveReporter in PassiveDriverBoundaries.cs.
  PatchBoundary remains owned solely by Core/PatchBoundary.cs in Task 8.
- UpdateDirective has the exact lifecycle issued (stage 0), authorized
  (stage 1), consumed (stage 2). Only PassiveDriver may authorize, rebase, or
  consume it. FailUpdate may atomically consume either issued or authorized.
- Task 4.2 adds PassiveUpdateBoundary after PassiveDriver exists. Its required
  order is BeginUpdate, VerifySavePath, reread state identity,
  AuthorizeUpdate, and only then IsQuiescent/Capture. A false path or identity
  result therefore makes Save(false, false) structurally unreachable.
- Product types remain in the global namespace so the net10 linked-source
  harness and the net35 plugin compile the identical names.

Create PassiveDriverBoundaryTests.cs:

~~~csharp
using System;

internal static class PassiveDriverBoundaryTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add(
            "driver-boundary",
            "hook token is owner bound and single consume",
            HookTokenIsOwnerBoundAndSingleConsume);
        tests.Add(
            "driver-boundary",
            "update directive authorizes rebases and consumes once",
            UpdateDirectiveAuthorizesRebasesAndConsumesOnce);
    }

    private static void HookTokenIsOwnerBoundAndSingleConsume()
    {
        object owner = new object();
        HookToken token = HookToken.Issued(owner, 7L, HookKind.Undo);
        Check.True(token.Active, "issued token active");
        Check.True(token.BelongsTo(owner), "owner identity");
        Check.False(token.BelongsTo(new object()), "foreign identity");
        Check.True(token.TryConsume(), "first consume");
        Check.False(token.TryConsume(), "second consume rejected");
        Check.False(
            HookToken.Inert(HookKind.Undo).TryConsume(),
            "inert token cannot consume");
    }

    private static void UpdateDirectiveAuthorizesRebasesAndConsumesOnce()
    {
        InvalidOperationException inner =
            new InvalidOperationException("inner");
        CaptureException plain =
            new CaptureException("plain");
        CaptureException wrapped =
            new CaptureException("wrapped", inner);
        Check.Equal("plain", plain.Message, "plain capture error");
        Check.Same(inner, wrapped.InnerException, "wrapped capture error");

        object owner = new object();
        UpdateDirective directive = UpdateDirective.Issued(
            owner, 9L, 3L, 4, 2.5, true, true);
        Check.True(directive.BelongsTo(owner), "owner identity");
        Check.True(directive.TryAuthorize(), "issued to authorized");
        Check.False(directive.TryAuthorize(), "authorize once");
        directive.RebaseInitialEpoch(4L, 1);
        Check.Equal(4L, directive.Epoch, "rebased epoch");
        Check.Equal(1, directive.SettleFrames, "replacement is frame one");
        Check.False(directive.InspectGate, "replacement not inspected");
        Check.False(
            directive.TimeoutAfterSample,
            "replacement cannot inherit timeout");
        Check.True(directive.TryComplete(), "authorized to consumed");
        Check.False(directive.TryComplete(), "consume once");
    }
}
~~~

Add PassiveDriverBoundaryTests.Register(tests) after
TraceSinkTests.Register(tests).
The cumulative Program manifest at this checkpoint is exactly:

~~~csharp
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 }
});
~~~

- [ ] **Step 2: Run RED**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort driver-boundary
~~~

Require a compiler error naming CaptureException, HookToken, or
UpdateDirective. A fixture, SDK, or assets failure is not the intended RED.

- [ ] **Step 3: Implement the complete boundaries**

Create CaptureException.cs exactly. Task 7 consumes this type and must not
redeclare it in GameObservation.cs:

~~~csharp
using System;

internal sealed class CaptureException : Exception
{
    internal CaptureException(string message)
        : base(message)
    {
    }

    internal CaptureException(string message, Exception inner)
        : base(message, inner)
    {
    }
}
~~~

Create PassiveDriverBoundaries.cs exactly:

~~~csharp
using System;
using System.Threading;

internal enum HookKind
{
    PlayerPoll,
    ProcessInput,
    Undo,
    Restart,
    StateSet
}

internal sealed class HookToken
{
    private readonly object owner;
    private int consumed;

    private HookToken(object owner, long id, HookKind kind, bool active)
    {
        this.owner = owner;
        Id = id;
        Kind = kind;
        Active = active;
    }

    internal long Id { get; private set; }
    internal HookKind Kind { get; private set; }
    internal bool Active { get; private set; }

    internal static HookToken Inert(HookKind kind)
    {
        return new HookToken(null, 0L, kind, false);
    }

    internal static HookToken Issued(
        object owner,
        long id,
        HookKind kind)
    {
        if (owner == null)
            throw new ArgumentNullException("owner");
        if (id <= 0L)
            throw new ArgumentOutOfRangeException("id");
        return new HookToken(owner, id, kind, true);
    }

    internal bool BelongsTo(object expectedOwner)
    {
        return Object.ReferenceEquals(owner, expectedOwner);
    }

    internal bool TryConsume()
    {
        return Active
            && Interlocked.Exchange(ref consumed, 1) == 0;
    }
}

internal sealed class UpdateDirective
{
    private readonly object owner;
    private int stage;

    private UpdateDirective(
        object owner,
        long id,
        long epoch,
        int settleFrames,
        double nowSeconds,
        bool active,
        bool inspectGate,
        bool timeoutAfterSample)
    {
        this.owner = owner;
        Id = id;
        Epoch = epoch;
        SettleFrames = settleFrames;
        NowSeconds = nowSeconds;
        Active = active;
        InspectGate = inspectGate;
        TimeoutAfterSample = timeoutAfterSample;
        stage = active ? 0 : 2;
    }

    internal long Id { get; private set; }
    internal long Epoch { get; private set; }
    internal int SettleFrames { get; private set; }
    internal double NowSeconds { get; private set; }
    internal bool Active { get; private set; }
    internal bool InspectGate { get; private set; }
    internal bool TimeoutAfterSample { get; private set; }

    internal static UpdateDirective Inactive(object owner)
    {
        return new UpdateDirective(
            owner, 0L, 0L, 0, 0.0, false, false, false);
    }

    internal static UpdateDirective Issued(
        object owner,
        long id,
        long epoch,
        int settleFrames,
        double nowSeconds,
        bool inspectGate,
        bool timeoutAfterSample)
    {
        if (owner == null)
            throw new ArgumentNullException("owner");
        if (id <= 0L)
            throw new ArgumentOutOfRangeException("id");
        return new UpdateDirective(
            owner,
            id,
            epoch,
            settleFrames,
            nowSeconds,
            true,
            inspectGate,
            timeoutAfterSample);
    }

    internal bool BelongsTo(object expectedOwner)
    {
        return Object.ReferenceEquals(owner, expectedOwner);
    }

    internal bool TryAuthorize()
    {
        return Active
            && Interlocked.CompareExchange(ref stage, 1, 0) == 0;
    }

    internal void RebaseInitialEpoch(
        long replacementEpoch,
        int replacementFrames)
    {
        if (Interlocked.CompareExchange(ref stage, 1, 1) != 1)
            throw new InvalidOperationException(
                "only an authorized directive may be rebased");
        if (replacementFrames < 0)
            throw new ArgumentOutOfRangeException("replacementFrames");
        Epoch = replacementEpoch;
        SettleFrames = replacementFrames;
        InspectGate = false;
        TimeoutAfterSample = false;
    }

    internal bool TryComplete()
    {
        return Active
            && Interlocked.CompareExchange(ref stage, 2, 1) == 1;
    }

    internal bool TryFail()
    {
        if (!Active)
            return false;
        while (true)
        {
            int observed =
                Interlocked.CompareExchange(ref stage, 0, 0);
            if (observed == 2)
                return false;
            if (Interlocked.CompareExchange(
                ref stage, 2, observed) == observed)
            {
                return true;
            }
        }
    }

    internal bool TryConsume()
    {
        return TryFail();
    }
}

internal enum GateSampleKind
{
    NotInspected,
    NonQuiescent,
    Captured
}

internal sealed class GateSample
{
    private GateSample(GateSampleKind kind, CaptureRecord capture)
    {
        Kind = kind;
        Capture = capture;
    }

    internal GateSampleKind Kind { get; private set; }
    internal CaptureRecord Capture { get; private set; }

    internal static GateSample NotInspected()
    {
        return new GateSample(GateSampleKind.NotInspected, null);
    }

    internal static GateSample NonQuiescent()
    {
        return new GateSample(GateSampleKind.NonQuiescent, null);
    }

    internal static GateSample Captured(CaptureRecord capture)
    {
        if (capture == null)
            throw new ArgumentNullException("capture");
        return new GateSample(GateSampleKind.Captured, capture);
    }
}

internal interface IPassiveReporter
{
    void Ready(int completedInputs);
    void Complete();
    void Failed(string code);
    void Diagnostic(string message);
}

~~~

- [ ] **Step 4: Run GREEN and the net35 gate**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort driver-boundary
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
git diff -- oracle/plugin/Core/CaptureException.cs \
  oracle/plugin/Core/PassiveDriverBoundaries.cs \
  oracle/plugin/tests/PassiveDriverBoundaryTests.cs \
  oracle/plugin/tests/Program.cs
~~~

- [ ] **Step 5: Commit only the Task 4.1 boundary slice**

~~~bash
git add oracle/plugin/Core/CaptureException.cs \
  oracle/plugin/Core/PassiveDriverBoundaries.cs \
  oracle/plugin/tests/PassiveDriverBoundaryTests.cs \
  oracle/plugin/tests/Program.cs
git commit -m "feat: define passive driver boundaries"
~~~

#### Task 4.2: Implement initial epochs, authorization, debounce, and deadlines

- [ ] **Step 1: Add the complete fake boundary and exactly eight RED tests**

**Files:**
- Modify: oracle/plugin/Core/PassiveDriverBoundaries.cs
- Create: oracle/plugin/Core/PassiveDriver.cs
- Create: oracle/plugin/tests/PassiveDriverTestSupport.cs
- Create: oracle/plugin/tests/PassiveDriverInitialTests.cs
- Modify: oracle/plugin/tests/Program.cs

**Interfaces:**
- Produces partial PassiveDriver with constructor
  PassiveDriver(ITraceSink, IPassiveReporter, int, int, double), Prepare,
  Activate, BeginUpdate, AuthorizeUpdate, CompleteUpdate, FailUpdate,
  PlayerPollEntered, tokenless PhysicalPollReturned, PlayerPollReturned,
  PlayerPollThrew, TryFault, ObserverFailed, Disable, and Dispose.
- Observation state is Unity-main-thread-only. Terminal selection, directive
  stages, hook-token consumption, teardown, and sink-close ownership use
  Interlocked. No sink or reporter method is invoked while a monitor is held.
- A pre-initial replacement detected after the path check starts a new epoch
  on that same callback with currentFrames equal to 1, rebases the authorized
  directive, resets neutral/candidate/last-capture state, and completes that
  callback as NotInspected.

Create PassiveDriverTestSupport.cs:

~~~csharp
using System;
using System.Collections.Generic;

internal sealed class FakeTraceSink : ITraceSink
{
    private readonly IList<string> events;

    internal FakeTraceSink(IList<string> events)
    {
        this.events = events;
    }

    internal readonly List<InitialRecord> InitialRecords =
        new List<InitialRecord>();
    internal readonly List<StepRecord> StepRecords =
        new List<StepRecord>();
    internal readonly List<EndRecord> EndRecords =
        new List<EndRecord>();
    internal readonly List<ErrorRecord> ErrorRecords =
        new List<ErrorRecord>();
    internal Exception RunFailure { get; set; }
    internal Exception InitialFailure { get; set; }
    internal Exception StepFailure { get; set; }
    internal Exception EndFailure { get; set; }
    internal Exception ErrorFailure { get; set; }
    internal Exception CloseFailure { get; set; }
    internal int CloseCalls;

    public void WriteRun(RunRecord record)
    {
        if (RunFailure != null)
            throw RunFailure;
        Add("sink:run");
    }

    public void WriteInitial(InitialRecord record)
    {
        if (InitialFailure != null)
            throw InitialFailure;
        InitialRecords.Add(record);
        Add("sink:initial");
    }

    public void WriteStep(StepRecord record)
    {
        if (StepFailure != null)
            throw StepFailure;
        StepRecords.Add(record);
        Add("sink:step:" + record.InputIndex.ToString());
    }

    public void WriteEnd(EndRecord record)
    {
        if (EndFailure != null)
            throw EndFailure;
        EndRecords.Add(record);
        Add("sink:end");
    }

    public void WriteError(ErrorRecord record)
    {
        if (ErrorFailure != null)
            throw ErrorFailure;
        ErrorRecords.Add(record);
        Add("sink:error:" + record.Code);
    }

    public void Close()
    {
        CloseCalls++;
        Add("sink:close");
        if (CloseFailure != null)
            throw CloseFailure;
    }

    private void Add(string value)
    {
        lock (events)
            events.Add(value);
    }
}

internal sealed class FakePassiveReporter : IPassiveReporter
{
    private readonly IList<string> events;

    internal FakePassiveReporter(IList<string> events)
    {
        this.events = events;
    }

    internal Exception ReadyFailure { get; set; }
    internal Exception CompleteFailure { get; set; }
    internal Exception FailedFailure { get; set; }
    internal Exception DiagnosticFailure { get; set; }

    public void Ready(int completedInputs)
    {
        Add("report:ready:" + completedInputs.ToString() + "/3");
        if (ReadyFailure != null)
            throw ReadyFailure;
    }

    public void Complete()
    {
        Add("report:complete");
        if (CompleteFailure != null)
            throw CompleteFailure;
    }

    public void Failed(string code)
    {
        Add("report:failed:" + code);
        if (FailedFailure != null)
            throw FailedFailure;
    }

    public void Diagnostic(string message)
    {
        Add("report:diagnostic:" + message);
        if (DiagnosticFailure != null)
            throw DiagnosticFailure;
    }

    private void Add(string value)
    {
        lock (events)
            events.Add(value);
    }
}

internal sealed class FakeUpdateObservation :
    IPassiveUpdateObservation
{
    internal object FirstState;
    internal object SecondState;
    internal bool FirstUsable = true;
    internal bool SecondUsable = true;
    internal bool SavePathMatches = true;
    internal bool Quiescent = true;
    internal CaptureRecord CaptureValue =
        ProtocolSamples.InitialCapture;
    internal double Now;
    internal DateTime Utc = DriverFixture.UtcFinish;
    internal Exception PathFailure { get; set; }
    internal Exception GateFailure { get; set; }
    internal Exception CaptureFailure { get; set; }
    internal int PathCalls;
    internal int StateCalls;
    internal int GateCalls;
    internal int CaptureCalls;
    internal object GateState;
    internal object CaptureState;

    public bool TryGetState(out object stateReference)
    {
        if (StateCalls++ == 0)
        {
            stateReference = FirstState;
            return FirstUsable;
        }
        stateReference = SecondState;
        return SecondUsable;
    }

    public bool VerifySavePath()
    {
        PathCalls++;
        if (PathFailure != null)
            throw PathFailure;
        return SavePathMatches;
    }

    public bool IsQuiescent(object stateReference)
    {
        GateCalls++;
        GateState = stateReference;
        if (GateFailure != null)
            throw GateFailure;
        return Quiescent;
    }

    public CaptureRecord Capture(object stateReference)
    {
        CaptureCalls++;
        CaptureState = stateReference;
        if (CaptureFailure != null)
            throw CaptureFailure;
        return CaptureValue;
    }

    public double NowSeconds()
    {
        return Now;
    }

    public DateTime UtcNow()
    {
        return Utc;
    }
}

internal sealed partial class DriverFixture
{
    internal static readonly DateTime UtcFinish =
        new DateTime(
            2026, 7, 31, 20, 0, 0, DateTimeKind.Utc);

    internal readonly object State = new object();
    internal readonly object OtherState = new object();
    internal readonly List<string> Events = new List<string>();
    internal readonly FakeTraceSink Sink;
    internal readonly FakePassiveReporter Reporter;
    internal readonly PassiveDriver Driver;
    internal readonly PassiveUpdateBoundary Boundary;

    private DriverFixture(int maxFrames, double maxSeconds)
    {
        Sink = new FakeTraceSink(Events);
        Reporter = new FakePassiveReporter(Events);
        Driver = new PassiveDriver(
            Sink, Reporter, 3, maxFrames, maxSeconds);
        Boundary = new PassiveUpdateBoundary(Driver);
    }

    internal static DriverFixture Active()
    {
        return Active(600, 30.0);
    }

    internal static DriverFixture Active(
        int maxFrames,
        double maxSeconds)
    {
        DriverFixture fixture =
            new DriverFixture(maxFrames, maxSeconds);
        Check.True(
            fixture.Driver.Prepare(ProtocolSamples.Run),
            "prepare");
        Check.True(fixture.Driver.Activate(), "activate");
        return fixture;
    }

    internal static DriverFixture Ready()
    {
        DriverFixture fixture = Active();
        fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        FakeUpdateObservation firstSample = fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        Check.Same(fixture.State, firstSample.GateState,
            "gate receives verified state");
        Check.Same(fixture.State, firstSample.CaptureState,
            "capture receives verified state");
        fixture.Observe(
            fixture.State, fixture.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            PassivePhase.Ready,
            fixture.Driver.Phase,
            "ready fixture");
        return fixture;
    }

    internal FakeUpdateObservation Observe(
        object firstState,
        object secondState,
        double now,
        bool quiescent,
        CaptureRecord capture)
    {
        FakeUpdateObservation observation =
            new FakeUpdateObservation
            {
                FirstState = firstState,
                SecondState = secondState,
                FirstUsable = firstState != null,
                SecondUsable = secondState != null,
                Now = now,
                Quiescent = quiescent,
                CaptureValue = capture,
                Utc = UtcFinish
            };
        Boundary.Observe(observation);
        return observation;
    }

    internal void Neutral()
    {
        HookToken poll = Driver.PlayerPollEntered();
        Driver.PhysicalPollReturned(8);
        Driver.PlayerPollReturned(poll);
    }

    internal void CardinalOnly(int rawDirection)
    {
        HookToken poll = Driver.PlayerPollEntered();
        Driver.PhysicalPollReturned(rawDirection);
        Driver.PlayerPollReturned(poll);
    }
}
~~~

Create PassiveDriverInitialTests.cs with exactly eight registrations and eight
method bodies:

~~~csharp
using System;

internal static class PassiveDriverInitialTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("driver-initial", "prepare activate separation",
            PrepareActivateSeparation);
        tests.Add("driver-initial", "pre epoch neutral does not leak",
            PreEpochNeutralDoesNotLeak);
        tests.Add("driver-initial", "matching pair writes initial",
            MatchingPairWritesInitial);
        tests.Add("driver-initial", "not inspected breaks pair",
            NotInspectedBreaksPair);
        tests.Add("driver-initial", "nonquiescent breaks pair",
            NonquiescentBreaksPair);
        tests.Add("driver-initial", "cardinal clears candidate",
            CardinalClearsCandidate);
        tests.Add("driver-initial", "replacement rebases same callback",
            ReplacementRebasesSameCallback);
        tests.Add("driver-initial", "exact deadline and pre overrun",
            ExactDeadlineAndPreOverrun);
    }

    private static void PrepareActivateSeparation()
    {
        DriverFixture fixture = DriverFixture.Active();
        Check.Sequence(
            new string[] { "sink:run" },
            fixture.Events.ToArray(),
            "prepare precedes all reports");
        Check.Equal(
            PassivePhase.AwaitGame,
            fixture.Driver.Phase,
            "activated phase");
        Check.False(
            fixture.Driver.Prepare(ProtocolSamples.Run),
            "second prepare");
        Check.False(fixture.Driver.Activate(), "second activate");
    }

    private static void PreEpochNeutralDoesNotLeak()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Neutral();
        FakeUpdateObservation first = fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(0, first.CaptureCalls, "old neutral ignored");
        fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            0, fixture.Sink.InitialRecords.Count,
            "no initial without epoch neutral");
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Observe(
            fixture.State, fixture.State, 4.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            1, fixture.Sink.InitialRecords.Count,
            "new neutral enables pair");
    }

    private static void MatchingPairWritesInitial()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            0, fixture.Sink.InitialRecords.Count,
            "one sample is not a pair");
        fixture.Observe(
            fixture.State, fixture.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        Check.Sequence(
            new string[]
            {
                "sink:run",
                "sink:initial",
                "report:ready:0/3"
            },
            fixture.Events.ToArray(),
            "record before progress");
        Check.Equal(
            PassivePhase.Ready,
            fixture.Driver.Phase,
            "ready after flushed pair");

        DriverFixture failedMarker = DriverFixture.Active();
        failedMarker.Reporter.ReadyFailure =
            new InvalidOperationException("ready marker");
        failedMarker.Observe(
            failedMarker.State, failedMarker.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        failedMarker.Neutral();
        failedMarker.Observe(
            failedMarker.State, failedMarker.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        failedMarker.Observe(
            failedMarker.State, failedMarker.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        ErrorRecord markerError = failedMarker.Sink.ErrorRecords[0];
        Check.Equal("observer_exception", markerError.Code,
            "initial Ready failure code");
        Check.True(markerError.LastCapture == null,
            "completed initial epoch is not retained as last_capture");
    }

    private static void NotInspectedBreaksPair()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        fixture.CardinalOnly(0);
        FakeUpdateObservation skipped = fixture.Observe(
            fixture.State, fixture.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(0, skipped.GateCalls, "not inspected");
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 4.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            0, fixture.Sink.InitialRecords.Count,
            "first post-gap sample");
        fixture.Observe(
            fixture.State, fixture.State, 5.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            1, fixture.Sink.InitialRecords.Count,
            "second post-gap sample");
    }

    private static void NonquiescentBreaksPair()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Observe(
            fixture.State, fixture.State, 3.0, false,
            ProtocolSamples.InitialCapture);
        fixture.Observe(
            fixture.State, fixture.State, 4.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            0, fixture.Sink.InitialRecords.Count,
            "nonquiescent broke pair");
        fixture.Observe(
            fixture.State, fixture.State, 5.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            1, fixture.Sink.InitialRecords.Count,
            "new consecutive pair");
    }

    private static void CardinalClearsCandidate()
    {
        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        fixture.CardinalOnly(3);
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            0, fixture.Sink.InitialRecords.Count,
            "cardinal cleared first candidate");
        fixture.Observe(
            fixture.State, fixture.State, 4.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            1, fixture.Sink.InitialRecords.Count,
            "pair after cardinal");
    }

    private static void ReplacementRebasesSameCallback()
    {
        DriverFixture path = DriverFixture.Active();
        FakeUpdateObservation changedPath =
            new FakeUpdateObservation
            {
                FirstState = path.State,
                SecondState = path.State,
                SavePathMatches = false,
                Now = 1.0,
                CaptureValue = ProtocolSamples.InitialCapture
            };
        path.Boundary.Observe(changedPath);
        Check.Equal(1, changedPath.PathCalls, "path checked once");
        Check.Equal(1, changedPath.StateCalls, "false path skips identity reread");
        Check.Equal(0, changedPath.GateCalls, "false path skips gate");
        Check.Equal(0, changedPath.CaptureCalls, "false path skips save");
        Check.Equal(
            "save_path_changed",
            path.Sink.ErrorRecords[0].Code,
            "path failure precedes capture");

        DriverFixture fixture = DriverFixture.Active();
        fixture.Observe(
            fixture.State, fixture.State, 1.0, true,
            ProtocolSamples.InitialCapture);
        fixture.Neutral();
        fixture.Observe(
            fixture.State, fixture.State, 2.0, true,
            ProtocolSamples.InitialCapture);

        FakeUpdateObservation replacement =
            fixture.Observe(
                fixture.State,
                fixture.OtherState,
                3.0,
                true,
                ProtocolSamples.MovedCapture);

        Check.Equal(1, replacement.PathCalls, "path checked");
        Check.Equal(2, replacement.StateCalls, "identity reread once");
        Check.Equal(0, replacement.GateCalls, "neutral reset");
        Check.Equal(0, replacement.CaptureCalls, "no replacement capture");
        Check.Equal(
            1, fixture.Driver.CurrentSettleFrames,
            "replacement callback is frame one");
        Check.Equal(
            PassivePhase.AwaitInitialNeutral,
            fixture.Driver.Phase,
            "new initial epoch");

        fixture.Neutral();
        fixture.Observe(
            fixture.OtherState, fixture.OtherState, 4.0, true,
            ProtocolSamples.MovedCapture);
        fixture.Observe(
            fixture.OtherState, fixture.OtherState, 5.0, true,
            ProtocolSamples.MovedCapture);
        Check.Equal(
            1, fixture.Sink.InitialRecords.Count,
            "new epoch completes");
    }

    private static void ExactDeadlineAndPreOverrun()
    {
        DriverFixture frame = DriverFixture.Active(4, 30.0);
        frame.Observe(
            frame.State, frame.State, 0.0, true,
            ProtocolSamples.InitialCapture);
        frame.Neutral();
        frame.Observe(
            frame.State, frame.State, 1.0, false,
            ProtocolSamples.InitialCapture);
        frame.Observe(
            frame.State, frame.State, 2.0, true,
            ProtocolSamples.InitialCapture);
        frame.Observe(
            frame.State, frame.State, 3.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            PassivePhase.Ready,
            frame.Driver.Phase,
            "pair wins on frame four");

        DriverFixture time = DriverFixture.Active();
        time.Observe(
            time.State, time.State, 0.0, true,
            ProtocolSamples.InitialCapture);
        time.Neutral();
        time.Observe(
            time.State, time.State, 29.0, true,
            ProtocolSamples.InitialCapture);
        time.Observe(
            time.State, time.State, 30.0, true,
            ProtocolSamples.InitialCapture);
        Check.Equal(
            PassivePhase.Ready,
            time.Driver.Phase,
            "pair wins at exactly thirty seconds");

        DriverFixture over = DriverFixture.Active();
        over.Observe(
            over.State, over.State, 0.0, true,
            ProtocolSamples.InitialCapture);
        FakeUpdateObservation late =
            new FakeUpdateObservation
            {
                FirstState = over.State,
                SecondState = over.State,
                Now = 30.000001,
                CaptureValue = ProtocolSamples.InitialCapture
            };
        over.Boundary.Observe(late);
        Check.Equal(0, late.PathCalls, "overrun before path");
        Check.Equal(0, late.GateCalls, "overrun before gate");
        Check.Equal(0, late.CaptureCalls, "overrun before capture");
        Check.Equal(
            "initial_settle_timeout",
            over.Sink.ErrorRecords[0].Code,
            "pre-capture timeout code");
    }
}
~~~

Add PassiveDriverInitialTests.Register(tests) after
PassiveDriverBoundaryTests.Register(tests). The cumulative manifest is:

~~~csharp
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 },
    { "driver-initial", 8 }
});
~~~

- [ ] **Step 2: Run RED**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort driver-initial
~~~

Require a compiler diagnostic naming PassiveDriver. Do not accept a fixture,
SDK, or assets failure.

- [ ] **Step 3: Implement the ordered update boundary and complete initial driver**

Append this code to PassiveDriverBoundaries.cs. CaptureException comes from
the dedicated Task 4.1 file; generic observer failures remain distinct. Most
importantly, VerifySavePath and the identity reread both finish before
AuthorizeUpdate, and IsQuiescent/Capture are unreachable until authorization
succeeds:

~~~csharp
internal interface IPassiveUpdateObservation
{
    bool TryGetState(out object stateReference);
    bool VerifySavePath();
    bool IsQuiescent(object stateReference);
    CaptureRecord Capture(object stateReference);
    double NowSeconds();
    DateTime UtcNow();
}

internal sealed class PassiveUpdateBoundary
{
    private readonly PassiveDriver driver;

    internal PassiveUpdateBoundary(PassiveDriver driver)
    {
        this.driver = driver
            ?? throw new ArgumentNullException("driver");
    }

    internal void Observe(IPassiveUpdateObservation observation)
    {
        if (observation == null)
            throw new ArgumentNullException("observation");

        object beginState;
        bool beginUsable;
        double nowSeconds;
        try
        {
            beginUsable = observation.TryGetState(out beginState);
            nowSeconds = observation.NowSeconds();
        }
        catch (CaptureException)
        {
            driver.TryFault("capture_failed");
            return;
        }
        catch (Exception)
        {
            driver.TryFault("observer_exception");
            return;
        }

        UpdateDirective directive;
        try
        {
            directive = driver.BeginUpdate(
                beginState, beginUsable, nowSeconds);
        }
        catch (Exception)
        {
            driver.TryFault("observer_exception");
            return;
        }
        if (!directive.Active)
            return;

        bool savePathMatches;
        try
        {
            savePathMatches = observation.VerifySavePath();
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }
        if (!savePathMatches)
        {
            SafeFail(directive, "save_path_changed");
            return;
        }

        object verifiedState;
        bool verifiedUsable;
        try
        {
            verifiedUsable =
                observation.TryGetState(out verifiedState);
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }

        bool authorized;
        try
        {
            authorized = driver.AuthorizeUpdate(
                directive,
                verifiedState,
                verifiedUsable,
                savePathMatches);
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }
        if (!authorized)
            return;

        GateSample sample;
        try
        {
            if (!directive.InspectGate)
            {
                sample = GateSample.NotInspected();
            }
            else if (!observation.IsQuiescent(verifiedState))
            {
                sample = GateSample.NonQuiescent();
            }
            else
            {
                sample = GateSample.Captured(
                    observation.Capture(verifiedState));
            }
        }
        catch (CaptureException)
        {
            SafeFail(directive, "capture_failed");
            return;
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
            return;
        }

        try
        {
            driver.CompleteUpdate(
                directive, sample, observation.UtcNow());
        }
        catch (Exception)
        {
            SafeFail(directive, "observer_exception");
        }
    }

    private void SafeFail(UpdateDirective directive, string code)
    {
        try
        {
            driver.FailUpdate(directive, code);
        }
        catch (Exception)
        {
            driver.TryFault("observer_exception");
        }
    }
}
~~~

Create PassiveDriver.cs exactly:

~~~csharp
using System;
using System.Collections.Generic;
using System.Threading;

internal sealed partial class PassiveDriver : IDisposable
{
    private static readonly string[] RecordErrorCodes =
        new string[]
        {
            "patch_install_failed",
            "input_before_initial",
            "overlapping_input",
            "unexpected_input",
            "unscoped_process_input",
            "hook_order_mismatch",
            "game_method_exception",
            "observer_exception",
            "capture_failed",
            "record_too_large",
            "initial_settle_timeout",
            "settle_timeout",
            "state_replaced",
            "save_path_changed"
        };

    private sealed class PlayerPollContext
    {
        internal long Id;
        internal bool SawPhysicalPoll;
        internal int RawDirection { get; set; }
        internal bool SawManualProcessInput { get; set; }
    }

    private struct FaultRequest
    {
        internal bool ForceNullInputs;
        internal bool HasOffendingInput;
        internal int? OffendingIndex;
        internal OracleInput? OffendingInput;
        internal int? FrameOverride;

        internal static FaultRequest Derived()
        {
            return new FaultRequest();
        }

        internal static FaultRequest DerivedWithFrames(int frames)
        {
            FaultRequest value = new FaultRequest();
            value.FrameOverride = frames;
            return value;
        }

        internal static FaultRequest Offending(
            int index,
            OracleInput? input)
        {
            FaultRequest value = new FaultRequest();
            value.HasOffendingInput = true;
            value.OffendingIndex = index;
            value.OffendingInput = input;
            return value;
        }

        internal static FaultRequest Restart()
        {
            FaultRequest value = new FaultRequest();
            value.ForceNullInputs = true;
            return value;
        }
    }

    private readonly ITraceSink sink;
    private readonly IPassiveReporter reporter;
    private readonly int expectedInputCount;
    private readonly int maxSettleFrames;
    private readonly double maxSettleSeconds;

    private PassivePhase phase;
    private int prepareAttempted;
    private int prepared;
    private int activateAttempted;
    private int disabled;
    private int disposed;
    private int sinkCloseAttempted;
    private int terminalOwner;

    private string runId;
    private DateTime startedAtUtc;
    private int completedInputs;
    private long nextHookId;
    private long nextUpdateId;
    private long epoch;
    private UpdateDirective outstandingUpdate;

    private object epochState;
    private object stableState;
    private double epochStartedAt;
    private int currentFrames;
    private bool neutralSeen;
    private byte[] candidateSignature;
    private CaptureRecord lastCapture;

    private bool attemptPending;
    private bool attemptOutcomeKnown;
    private OracleInput attemptInput;
    private bool attemptAccepted;
    private bool attemptMovementScheduled;
    private object attemptState;

    private PlayerPollContext playerPoll;
    partial void EmitSettledAttempt(
        CaptureRecord capture,
        int settleFrames,
        DateTime utcNow,
        ref bool handled);

    partial void FinishExpectedInputCount(
        DateTime finishedAtUtc,
        ref bool handled);

    internal PassiveDriver(
        ITraceSink sink,
        IPassiveReporter reporter,
        int expectedInputCount,
        int maxSettleFrames,
        double maxSettleSeconds)
    {
        if (sink == null)
            throw new ArgumentNullException("sink");
        if (reporter == null)
            throw new ArgumentNullException("reporter");
        if (expectedInputCount != OracleProtocol.ExpectedInputCount)
            throw new ArgumentOutOfRangeException("expectedInputCount");
        if (maxSettleFrames < 2
            || maxSettleFrames > OracleProtocol.MaxSettleFrames)
        {
            throw new ArgumentOutOfRangeException("maxSettleFrames");
        }
        if (maxSettleSeconds <= 0.0
            || Double.IsNaN(maxSettleSeconds)
            || Double.IsInfinity(maxSettleSeconds))
        {
            throw new ArgumentOutOfRangeException("maxSettleSeconds");
        }
        this.sink = sink;
        this.reporter = reporter;
        this.expectedInputCount = expectedInputCount;
        this.maxSettleFrames = maxSettleFrames;
        this.maxSettleSeconds = maxSettleSeconds;
        phase = PassivePhase.Disabled;
    }

    internal PassivePhase Phase
    {
        get { return phase; }
    }

    internal int CurrentSettleFrames
    {
        get { return currentFrames; }
    }

    internal int ExpectedInputCount
    {
        get { return expectedInputCount; }
    }

    internal DateTime StartedAtUtc
    {
        get { return startedAtUtc; }
    }

    internal OracleInput PendingInput
    {
        get
        {
            if (!attemptPending)
                throw new InvalidOperationException("no pending attempt");
            return attemptInput;
        }
    }

    internal bool PendingAccepted
    {
        get
        {
            if (!attemptOutcomeKnown)
                throw new InvalidOperationException(
                    "attempt outcome is unavailable");
            return attemptAccepted;
        }
    }

    internal bool PendingMovementScheduled
    {
        get
        {
            if (!attemptOutcomeKnown)
                throw new InvalidOperationException(
                    "attempt outcome is unavailable");
            return attemptMovementScheduled;
        }
    }

    internal bool Prepare(RunRecord run)
    {
        if (run == null)
            throw new ArgumentNullException("run");
        if (Interlocked.CompareExchange(
            ref prepareAttempted, 1, 0) != 0)
        {
            return false;
        }
        if (Read(ref disposed) != 0)
            return false;
        try
        {
            sink.WriteRun(run);
            runId = run.RunId;
            startedAtUtc = run.StartedAtUtc;
            Interlocked.Exchange(ref prepared, 1);
            return true;
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
            SelectTraceIoFailure();
            return false;
        }
    }

    internal bool Activate()
    {
        if (Read(ref prepared) == 0
            || Read(ref disposed) != 0
            || Read(ref disabled) != 0
            || phase != PassivePhase.Disabled
            || TerminalSelected())
        {
            return false;
        }
        if (Interlocked.CompareExchange(
            ref activateAttempted, 1, 0) != 0)
        {
            return false;
        }
        phase = PassivePhase.AwaitGame;
        return true;
    }

    internal UpdateDirective BeginUpdate(
        object stateReference,
        bool usableGame,
        double nowSeconds)
    {
        if (!IsObservationActive())
            return UpdateDirective.Inactive(this);
        if (!IsValidMonotonic(nowSeconds))
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
            return UpdateDirective.Inactive(this);
        }
        if (outstandingUpdate != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return UpdateDirective.Inactive(this);
        }
        if (phase == PassivePhase.AwaitGame && usableGame)
        {
            if (stateReference == null)
            {
                TryFaultInternal(
                    "capture_failed", FaultRequest.Derived());
                return UpdateDirective.Inactive(this);
            }
            StartInitialEpoch(stateReference, nowSeconds, false);
        }

        int settleFrames = 0;
        bool inspectGate = false;
        bool timeoutAfterSample = false;
        if (phase == PassivePhase.AwaitInitialNeutral
            || phase == PassivePhase.Settling)
        {
            if (nowSeconds < epochStartedAt)
            {
                TryFaultInternal(
                    "observer_exception", FaultRequest.Derived());
                return UpdateDirective.Inactive(this);
            }
            int nextFrames = currentFrames + 1;
            double elapsed = nowSeconds - epochStartedAt;
            if (nextFrames > maxSettleFrames
                || elapsed > maxSettleSeconds)
            {
                string code =
                    phase == PassivePhase.AwaitInitialNeutral
                    ? "initial_settle_timeout"
                    : "settle_timeout";
                TryFaultInternal(
                    code,
                    FaultRequest.DerivedWithFrames(
                        Math.Min(nextFrames, maxSettleFrames)));
                return UpdateDirective.Inactive(this);
            }
            currentFrames = nextFrames;
            settleFrames = currentFrames;
            inspectGate = neutralSeen;
            timeoutAfterSample =
                currentFrames >= maxSettleFrames
                || elapsed >= maxSettleSeconds;
        }

        UpdateDirective directive =
            UpdateDirective.Issued(
                this,
                NextUpdateId(),
                epoch,
                settleFrames,
                nowSeconds,
                inspectGate,
                timeoutAfterSample);
        outstandingUpdate = directive;
        return directive;
    }

    internal bool AuthorizeUpdate(
        UpdateDirective directive,
        object stateReference,
        bool usableGame,
        bool savePathMatches)
    {
        RequireDirective(directive);
        if (!directive.TryAuthorize())
            throw new InvalidOperationException(
                "update directive was not issued");
        if (!Object.ReferenceEquals(outstandingUpdate, directive))
        {
            directive.TryComplete();
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        if (!IsObservationActive())
        {
            ConsumeAuthorizedDirective(directive);
            return false;
        }
        if (directive.Epoch != epoch)
        {
            ConsumeAuthorizedDirective(directive);
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        if (!savePathMatches)
        {
            ConsumeAuthorizedDirective(directive);
            TryFaultInternal(
                "save_path_changed", FaultRequest.Derived());
            return false;
        }

        if (phase == PassivePhase.AwaitGame)
        {
            if (usableGame)
            {
                if (stateReference == null)
                {
                    ConsumeAuthorizedDirective(directive);
                    TryFaultInternal(
                        "capture_failed", FaultRequest.Derived());
                    return false;
                }
                StartInitialEpoch(
                    stateReference, directive.NowSeconds, true);
                directive.RebaseInitialEpoch(epoch, currentFrames);
            }
            return true;
        }

        if (phase == PassivePhase.AwaitInitialNeutral)
        {
            if (!usableGame || stateReference == null)
            {
                ResetToAwaitGame();
                directive.RebaseInitialEpoch(epoch, 0);
                return true;
            }
            if (!Object.ReferenceEquals(epochState, stateReference))
            {
                StartInitialEpoch(
                    stateReference, directive.NowSeconds, true);
                directive.RebaseInitialEpoch(epoch, currentFrames);
            }
            return true;
        }

        object expectedState =
            phase == PassivePhase.Settling
            ? attemptState
            : stableState;
        if (!usableGame
            || stateReference == null
            || !Object.ReferenceEquals(expectedState, stateReference))
        {
            ConsumeAuthorizedDirective(directive);
            TryFaultInternal(
                "state_replaced", FaultRequest.Derived());
            return false;
        }
        return true;
    }

    internal void CompleteUpdate(
        UpdateDirective directive,
        GateSample sample,
        DateTime utcNow)
    {
        RequireDirective(directive);
        if (!directive.TryComplete())
            throw new InvalidOperationException(
                "update directive was not authorized");
        if (!Object.ReferenceEquals(outstandingUpdate, directive))
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            throw new InvalidOperationException(
                "update directive is not outstanding");
        }
        outstandingUpdate = null;
        if (!IsObservationActive())
            return;
        if (directive.Epoch != epoch)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        try
        {
            CompleteUpdateCore(directive, sample, utcNow);
        }
        catch (RecordTooLargeException)
        {
            TryFaultInternal(
                "record_too_large", FaultRequest.Derived());
        }
        catch (CanonicalEncodingException)
        {
            TryFaultInternal(
                "capture_failed", FaultRequest.Derived());
        }
        catch (TraceIoException)
        {
            SelectTraceIoFailure();
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
        }
    }

    internal void FailUpdate(
        UpdateDirective directive,
        string code)
    {
        if (code != "capture_failed"
            && code != "observer_exception"
            && code != "save_path_changed")
        {
            throw new ArgumentException(
                "invalid update failure code", "code");
        }
        RequireDirective(directive);
        if (!directive.TryFail())
            throw new InvalidOperationException(
                "update directive was already consumed");
        if (!Object.ReferenceEquals(outstandingUpdate, directive))
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            throw new InvalidOperationException(
                "update directive is not outstanding");
        }
        outstandingUpdate = null;
        TryFaultInternal(code, FaultRequest.Derived());
    }

    internal HookToken PlayerPollEntered()
    {
        if (!IsObservationActive())
            return HookToken.Inert(HookKind.PlayerPoll);
        if (playerPoll != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.PlayerPoll);
        }
        HookToken token = NewToken(HookKind.PlayerPoll);
        playerPoll = new PlayerPollContext { Id = token.Id };
        return token;
    }

    internal void PhysicalPollReturned(int rawDirection)
    {
        if (!IsObservationActive())
            return;
        if (playerPoll == null || playerPoll.SawPhysicalPoll)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        playerPoll.SawPhysicalPoll = true;
        playerPoll.RawDirection = rawDirection;
        if (rawDirection == 8)
        {
            if (phase == PassivePhase.AwaitInitialNeutral
                || phase == PassivePhase.Settling)
            {
                neutralSeen = true;
            }
            return;
        }
        if (phase == PassivePhase.AwaitInitialNeutral
            || phase == PassivePhase.Settling)
        {
            neutralSeen = false;
            candidateSignature = null;
        }
        OracleInput ignored;
        if (!TryMapCardinal(rawDirection, out ignored))
        {
            TryFaultInternal(
                "unexpected_input",
                FaultRequest.Offending(completedInputs, null));
        }
    }

    internal void PlayerPollReturned(HookToken token)
    {
        if (!ConsumeOrdinaryToken(token, HookKind.PlayerPoll))
            return;
        if (playerPoll == null || playerPoll.Id != token.Id)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        playerPoll = null;
    }

    internal void PlayerPollThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(token, HookKind.PlayerPoll))
            return;
        if (playerPoll == null || playerPoll.Id != token.Id)
            throw new InvalidOperationException(
                "player-poll token mismatch");
        playerPoll = null;
    }

    internal void ObserverFailed()
    {
        TryFault("observer_exception");
    }

    internal bool TryFault(string code)
    {
        if (Read(ref disposed) != 0 || Read(ref disabled) != 0)
            return false;
        return TryFaultInternal(code, FaultRequest.Derived());
    }

    internal void Disable()
    {
        Interlocked.Exchange(ref disabled, 1);
    }

    public void Dispose()
    {
        if (Interlocked.CompareExchange(ref disposed, 1, 0) != 0)
            return;
        Interlocked.Exchange(ref disabled, 1);
        BestEffortClose();
    }

    private void CompleteUpdateCore(
        UpdateDirective directive,
        GateSample sample,
        DateTime utcNow)
    {
        if (sample == null)
            throw new ArgumentNullException("sample");
        if (phase == PassivePhase.AwaitGame
            || phase == PassivePhase.Ready)
        {
            if (sample.Kind != GateSampleKind.NotInspected)
                throw new InvalidOperationException(
                    "gate inspected without an active epoch");
            return;
        }

        if (sample.Kind == GateSampleKind.NotInspected)
        {
            if (directive.InspectGate)
                throw new InvalidOperationException(
                    "eligible update was not inspected");
            candidateSignature = null;
        }
        else if (sample.Kind == GateSampleKind.NonQuiescent)
        {
            if (!directive.InspectGate)
                throw new InvalidOperationException(
                    "ineligible update inspected gate");
            candidateSignature = null;
        }
        else if (sample.Kind == GateSampleKind.Captured)
        {
            if (!directive.InspectGate || sample.Capture == null)
                throw new InvalidOperationException(
                    "capture was not authorized");
            byte[] signature =
                ValidateAndRememberCapture(sample.Capture);
            if (candidateSignature != null
                && SameBytes(candidateSignature, signature))
            {
                if (phase == PassivePhase.AwaitInitialNeutral)
                {
                    EmitInitial(sample.Capture);
                }
                else
                {
                    bool handled = false;
                    EmitSettledAttempt(
                        sample.Capture,
                        directive.SettleFrames,
                        utcNow,
                        ref handled);
                    if (!handled)
                        throw new InvalidOperationException(
                            "settled-attempt extension is unavailable");
                }
                return;
            }
            candidateSignature = signature;
        }
        else
        {
            throw new InvalidOperationException("unknown gate sample");
        }

        if (directive.TimeoutAfterSample)
        {
            TryFaultInternal(
                phase == PassivePhase.AwaitInitialNeutral
                    ? "initial_settle_timeout"
                    : "settle_timeout",
                FaultRequest.Derived());
        }
    }

    private byte[] ValidateAndRememberCapture(CaptureRecord capture)
    {
        for (int index = 0; index < RecordErrorCodes.Length; index++)
        {
            CanonicalJson.EncodeError(
                new ErrorRecord(
                    runId,
                    Int32.MaxValue,
                    OracleInput.North,
                    RecordErrorCodes[index],
                    OracleProtocol.MaxSettleFrames,
                    capture));
        }
        byte[] signature = CaptureSignature.Compute(capture);
        lastCapture = capture;
        return signature;
    }

    private void EmitInitial(CaptureRecord capture)
    {
        sink.WriteInitial(new InitialRecord(runId, capture));
        stableState = epochState;
        phase = PassivePhase.Ready;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
        try
        {
            reporter.Ready(0);
        }
        catch (Exception)
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
        }
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
        if (phase == PassivePhase.Settling)
        {
            TryFaultInternal(
                "overlapping_input", FaultRequest.Derived());
            return false;
        }
        if (phase != PassivePhase.Ready)
            return false;
        if (stateReference == null
            || !Object.ReferenceEquals(stableState, stateReference))
        {
            TryFaultInternal(
                "state_replaced", FaultRequest.Derived());
            return false;
        }
        epoch++;
        phase = PassivePhase.Settling;
        epochState = stateReference;
        epochStartedAt = nowSeconds;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
        attemptPending = true;
        attemptOutcomeKnown = false;
        attemptInput = input;
        attemptAccepted = false;
        attemptMovementScheduled = false;
        attemptState = stateReference;
        return true;
    }

    private void StartInitialEpoch(
        object stateReference,
        double nowSeconds,
        bool countCurrentUpdate)
    {
        epoch++;
        phase = PassivePhase.AwaitInitialNeutral;
        epochState = stateReference;
        epochStartedAt = nowSeconds;
        currentFrames = countCurrentUpdate ? 1 : 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
        ClearAttemptFields();
    }

    private void ResetToAwaitGame()
    {
        epoch++;
        phase = PassivePhase.AwaitGame;
        epochState = null;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        lastCapture = null;
        ClearAttemptFields();
    }

    private void ClearAttemptAfterStep()
    {
        phase = PassivePhase.Ready;
        currentFrames = 0;
        neutralSeen = false;
        candidateSignature = null;
        epochState = stableState;
        ClearAttemptFields();
    }

    private void ClearAttemptFields()
    {
        attemptPending = false;
        attemptOutcomeKnown = false;
        attemptAccepted = false;
        attemptMovementScheduled = false;
        attemptState = null;
    }

    private void ConsumeAuthorizedDirective(UpdateDirective directive)
    {
        if (!directive.TryComplete())
            throw new InvalidOperationException(
                "authorized update could not be consumed");
        outstandingUpdate = null;
    }

    private void RequireDirective(UpdateDirective directive)
    {
        if (directive == null)
            throw new ArgumentNullException("directive");
        if (!directive.Active || !directive.BelongsTo(this))
            throw new InvalidOperationException(
                "foreign or inactive update directive");
    }

    private HookToken NewToken(HookKind kind)
    {
        if (nextHookId == Int64.MaxValue)
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
            return HookToken.Inert(kind);
        }
        nextHookId++;
        return HookToken.Issued(this, nextHookId, kind);
    }

    private long NextUpdateId()
    {
        if (nextUpdateId == Int64.MaxValue)
            throw new InvalidOperationException(
                "update token exhaustion");
        nextUpdateId++;
        return nextUpdateId;
    }

    private bool ConsumeOrdinaryToken(
        HookToken token,
        HookKind expectedKind)
    {
        if (token == null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        if (!token.Active)
            return false;
        if (!token.BelongsTo(this)
            || token.Kind != expectedKind
            || !token.TryConsume())
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return false;
        }
        return true;
    }

    private bool ConsumeCleanupToken(
        HookToken token,
        HookKind expectedKind)
    {
        if (token == null || !token.Active)
            return false;
        if (!token.BelongsTo(this) || token.Kind != expectedKind)
            throw new InvalidOperationException("foreign cleanup token");
        return token.TryConsume();
    }

    private bool TryFaultInternal(
        string code,
        FaultRequest request)
    {
        OracleErrors.ForCode(code);
        if (Interlocked.CompareExchange(
            ref terminalOwner, 1, 0) != 0)
        {
            return false;
        }

        PassivePhase faultPhase = phase;
        phase = PassivePhase.Faulted;
        if (Read(ref prepared) == 0)
        {
            BestEffortClose();
            SafeFailed("trace_io_failed");
            return true;
        }

        bool durable = false;
        try
        {
            sink.WriteError(
                BuildErrorRecord(code, request, faultPhase));
            CloseSink();
            durable = true;
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
            BestEffortClose();
        }
        SafeFailed(durable ? code : "trace_io_failed");
        return true;
    }

    private ErrorRecord BuildErrorRecord(
        string code,
        FaultRequest request,
        PassivePhase faultPhase)
    {
        int? inputIndex;
        OracleInput? input;
        if (request.ForceNullInputs)
        {
            inputIndex = null;
            input = null;
        }
        else if (attemptPending)
        {
            inputIndex = completedInputs;
            input = attemptInput;
        }
        else if (request.HasOffendingInput)
        {
            inputIndex = request.OffendingIndex;
            input = request.OffendingInput;
        }
        else
        {
            inputIndex = null;
            input = null;
        }

        int frames;
        if (request.FrameOverride.HasValue)
            frames = request.FrameOverride.Value;
        else if (attemptPending)
            frames = currentFrames;
        else if (request.HasOffendingInput)
            frames = 0;
        else if (faultPhase == PassivePhase.AwaitInitialNeutral)
            frames = currentFrames;
        else
            frames = 0;

        return new ErrorRecord(
            runId,
            inputIndex,
            input,
            code,
            frames,
            lastCapture);
    }

    private void SelectTraceIoFailure()
    {
        if (Interlocked.CompareExchange(
            ref terminalOwner, 1, 0) != 0)
        {
            return;
        }
        phase = PassivePhase.Faulted;
        BestEffortClose();
        SafeFailed("trace_io_failed");
    }

    private void CloseSink()
    {
        if (Interlocked.CompareExchange(
            ref sinkCloseAttempted, 1, 0) != 0)
        {
            throw new InvalidOperationException(
                "sink close already attempted");
        }
        sink.Close();
    }

    private void BestEffortClose()
    {
        if (Read(ref sinkCloseAttempted) != 0)
            return;
        try
        {
            CloseSink();
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeFailed(string code)
    {
        try
        {
            reporter.Failed(code);
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeDiagnostic(Exception error)
    {
        try
        {
            reporter.Diagnostic(
                error == null
                ? "unknown"
                : error.GetType().FullName);
        }
        catch (Exception)
        {
        }
    }

    private bool IsObservationActive()
    {
        return Read(ref prepared) != 0
            && Read(ref disabled) == 0
            && !TerminalSelected()
            && (phase == PassivePhase.AwaitGame
                || phase == PassivePhase.AwaitInitialNeutral
                || phase == PassivePhase.Ready
                || phase == PassivePhase.Settling);
    }

    private bool TerminalSelected()
    {
        return Read(ref terminalOwner) != 0;
    }

    private static int Read(ref int value)
    {
        return Interlocked.CompareExchange(ref value, 0, 0);
    }

    private static bool IsValidMonotonic(double value)
    {
        return value >= 0.0
            && !Double.IsNaN(value)
            && !Double.IsInfinity(value);
    }

    private static bool TryMapCardinal(
        int rawDirection,
        out OracleInput input)
    {
        switch (rawDirection)
        {
            case 0:
                input = OracleInput.North;
                return true;
            case 1:
                input = OracleInput.South;
                return true;
            case 2:
                input = OracleInput.West;
                return true;
            case 3:
                input = OracleInput.East;
                return true;
            default:
                input = OracleInput.North;
                return false;
        }
    }

    private static bool SameBytes(byte[] left, byte[] right)
    {
        if (left == null
            || right == null
            || left.Length != right.Length)
        {
            return false;
        }
        for (int index = 0; index < left.Length; index++)
        {
            if (left[index] != right[index])
                return false;
        }
        return true;
    }
}
~~~

- [ ] **Step 4: Run GREEN and the net35 gate**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort driver-initial
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
git diff -- oracle/plugin/Core/PassiveDriverBoundaries.cs \
  oracle/plugin/Core/PassiveDriver.cs \
  oracle/plugin/tests/PassiveDriverTestSupport.cs \
  oracle/plugin/tests/PassiveDriverInitialTests.cs \
  oracle/plugin/tests/Program.cs
~~~

- [ ] **Step 5: Commit only the Task 4.2 initial-driver slice**

~~~bash
git add oracle/plugin/Core/PassiveDriverBoundaries.cs \
  oracle/plugin/Core/PassiveDriver.cs \
  oracle/plugin/tests/PassiveDriverTestSupport.cs \
  oracle/plugin/tests/PassiveDriverInitialTests.cs \
  oracle/plugin/tests/Program.cs
git commit -m "feat: settle passive initial state"
~~~

### Track 5: Attribute native inputs and own terminal outcomes

#### Task 5.1: Attribute cardinal directions and Undo

- [ ] **Step 1: Add the complete fixture extensions and six RED tests**

**Files:**
- Create: oracle/plugin/Core/PassiveDriverInput.cs
- Modify: oracle/plugin/tests/PassiveDriverTestSupport.cs
- Create: oracle/plugin/tests/PassiveDriverInputTests.cs
- Modify: oracle/plugin/tests/Program.cs

**Interfaces:**
- Produces ProcessInputEntered(object, int, double),
  ProcessInputReturned(HookToken, bool, bool), ProcessInputThrew(HookToken),
  UndoEntered(object, double), RestoreObserved(),
  UndoReturned(HookToken, bool), and UndoThrew(HookToken).
- A direction becomes an attempt only for the first ProcessInput nested in one
  PlayerPoll context after exactly one physical cardinal result, with an
  identical raw direction. A zero-poll scope and a cardinal scope filtered by
  the game are both valid no-attempt scopes.
- An unscoped ProcessInput is ignored while AwaitGame,
  AwaitInitialNeutral, or Settling and faults with unscoped_process_input only
  while stably Ready. Undo is accepted only when RestoreObserved occurs inside
  its matching top-level context.
- All state observation remains on the Unity main thread. No monitor surrounds
  a sink or reporter call.

Append this partial fixture body to PassiveDriverTestSupport.cs:

~~~csharp
internal sealed partial class DriverFixture
{
    internal void OpenDirection(
        int rawDirection,
        bool accepted,
        bool movementScheduled,
        double nowSeconds)
    {
        HookToken poll = Driver.PlayerPollEntered();
        Driver.PhysicalPollReturned(rawDirection);
        HookToken process = Driver.ProcessInputEntered(
            State, rawDirection, nowSeconds);
        Driver.ProcessInputReturned(
            process, accepted, movementScheduled);
        Driver.PlayerPollReturned(poll);
    }

    internal void OpenUndo(
        bool restored,
        bool movementScheduled,
        double nowSeconds)
    {
        HookToken undo = Driver.UndoEntered(State, nowSeconds);
        if (restored)
            Driver.RestoreObserved();
        Driver.UndoReturned(undo, movementScheduled);
    }

    internal void SettleCurrent(
        CaptureRecord capture,
        double firstUpdateSeconds)
    {
        Neutral();
        Observe(
            State,
            State,
            firstUpdateSeconds,
            true,
            capture);
        Observe(
            State,
            State,
            firstUpdateSeconds + 1.0,
            true,
            capture);
    }
}
~~~

Create PassiveDriverInputTests.cs with exactly these six registrations and six
method bodies:

~~~csharp
using System;

internal static class PassiveDriverInputTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("driver-input", "all cardinals correlate",
            AllCardinalsCorrelate);
        tests.Add("driver-input", "filtered and zero poll open no attempt",
            FilteredAndZeroPollOpenNoAttempt);
        tests.Add("driver-input", "duplicate mismatch and unknown fault",
            DuplicateMismatchAndUnknownFault);
        tests.Add("driver-input", "unscoped policy follows phase",
            UnscopedPolicyFollowsPhase);
        tests.Add("driver-input", "accepted and refused direction outcomes",
            AcceptedAndRefusedDirectionOutcomes);
        tests.Add("driver-input", "Undo acceptance and restore rules",
            UndoAcceptanceAndRestoreRules);
    }

    private static void AllCardinalsCorrelate()
    {
        int[] raw = new int[] { 0, 1, 2, 3 };
        OracleInput[] expected = new OracleInput[]
        {
            OracleInput.North,
            OracleInput.South,
            OracleInput.West,
            OracleInput.East
        };
        for (int index = 0; index < raw.Length; index++)
        {
            DriverFixture fixture = DriverFixture.Ready();
            fixture.OpenDirection(raw[index], true, true, 10.0);
            Check.Equal(
                PassivePhase.Settling,
                fixture.Driver.Phase,
                "cardinal opens attempt " + index.ToString());
            Check.Equal(
                expected[index],
                fixture.Driver.PendingInput,
                "mapped cardinal " + index.ToString());
        }
    }

    private static void FilteredAndZeroPollOpenNoAttempt()
    {
        DriverFixture fixture = DriverFixture.Ready();
        HookToken empty = fixture.Driver.PlayerPollEntered();
        fixture.Driver.PlayerPollReturned(empty);
        Check.Equal(
            PassivePhase.Ready,
            fixture.Driver.Phase,
            "zero-poll early gate");

        fixture.CardinalOnly(2);
        Check.Equal(
            PassivePhase.Ready,
            fixture.Driver.Phase,
            "filtered cardinal");
        Check.Equal(0, fixture.Sink.StepRecords.Count, "no attempt emitted");
        Check.Equal(0, fixture.Sink.ErrorRecords.Count, "no fault emitted");
    }

    private static void DuplicateMismatchAndUnknownFault()
    {
        DriverFixture duplicate = DriverFixture.Ready();
        HookToken duplicatePoll =
            duplicate.Driver.PlayerPollEntered();
        duplicate.Driver.PhysicalPollReturned(0);
        duplicate.Driver.PhysicalPollReturned(0);
        duplicate.Driver.PlayerPollReturned(duplicatePoll);
        Check.Equal(
            "hook_order_mismatch",
            duplicate.Sink.ErrorRecords[0].Code,
            "second physical poll");

        DriverFixture mismatch = DriverFixture.Ready();
        HookToken mismatchPoll =
            mismatch.Driver.PlayerPollEntered();
        mismatch.Driver.PhysicalPollReturned(0);
        mismatch.Driver.ProcessInputEntered(
            mismatch.State, 1, 10.0);
        mismatch.Driver.PlayerPollReturned(mismatchPoll);
        Check.Equal(
            "hook_order_mismatch",
            mismatch.Sink.ErrorRecords[0].Code,
            "argument differs from physical poll");

        DriverFixture unknown = DriverFixture.Ready();
        HookToken unknownPoll = unknown.Driver.PlayerPollEntered();
        unknown.Driver.PhysicalPollReturned(99);
        unknown.Driver.PlayerPollReturned(unknownPoll);
        ErrorRecord error = unknown.Sink.ErrorRecords[0];
        Check.Equal("unexpected_input", error.Code, "unknown direction");
        Check.Equal((int?)0, error.InputIndex, "next input index");
        Check.False(error.Input.HasValue, "unknown has null input");

        DriverFixture duringAttempt = DriverFixture.Ready();
        duringAttempt.OpenDirection(2, true, true, 10.0);
        duringAttempt.Observe(
            duringAttempt.State,
            duringAttempt.State,
            11.0,
            false,
            ProtocolSamples.MovedCapture);
        HookToken settlingPoll =
            duringAttempt.Driver.PlayerPollEntered();
        duringAttempt.Driver.PhysicalPollReturned(99);
        duringAttempt.Driver.PlayerPollReturned(settlingPoll);
        ErrorRecord settling = duringAttempt.Sink.ErrorRecords[0];
        Check.Equal(
            "unexpected_input",
            settling.Code,
            "unknown while settling");
        Check.Equal(
            (int?)0,
            settling.InputIndex,
            "pending attempt retains its index");
        Check.Equal(
            (OracleInput?)OracleInput.West,
            settling.Input,
            "pending attempt outranks unknown offending input");
        Check.Equal(
            1,
            settling.SettleFrames,
            "unknown retains active attempt frame count");
    }

    private static void UnscopedPolicyFollowsPhase()
    {
        DriverFixture preInitial = DriverFixture.Active();
        HookToken ignored = preInitial.Driver.ProcessInputEntered(
            preInitial.State, 0, 1.0);
        preInitial.Driver.ProcessInputReturned(
            ignored, true, true);
        Check.Equal(
            PassivePhase.AwaitGame,
            preInitial.Driver.Phase,
            "unscoped pre-initial ignored");
        Check.Equal(
            0,
            preInitial.Sink.ErrorRecords.Count,
            "pre-initial no fault");

        DriverFixture ready = DriverFixture.Ready();
        ready.Driver.ProcessInputEntered(
            ready.State, 0, 10.0);
        Check.Equal(
            "unscoped_process_input",
            ready.Sink.ErrorRecords[0].Code,
            "ready unscoped fault");

        DriverFixture settling = DriverFixture.Ready();
        settling.OpenDirection(2, true, true, 10.0);
        HookToken automatic = settling.Driver.ProcessInputEntered(
            settling.State, 0, 11.0);
        settling.Driver.ProcessInputReturned(
            automatic, true, true);
        Check.Equal(
            PassivePhase.Settling,
            settling.Driver.Phase,
            "automatic tick ignored while settling");
        Check.Equal(
            0,
            settling.Sink.ErrorRecords.Count,
            "settling unscoped no fault");
    }

    private static void AcceptedAndRefusedDirectionOutcomes()
    {
        DriverFixture accepted = DriverFixture.Ready();
        accepted.OpenDirection(2, true, true, 10.0);
        Check.True(
            accepted.Driver.PendingAccepted,
            "exact ProcessInput result");
        Check.True(
            accepted.Driver.PendingMovementScheduled,
            "immediate Moving result");
        accepted.SettleCurrent(
            ProtocolSamples.MovedCapture, 11.0);
        StepRecord first = accepted.Sink.StepRecords[0];
        Check.Equal(OracleInput.West, first.Input, "west step");
        Check.True(first.Accepted, "accepted step");
        Check.True(first.MovementScheduled, "movement scheduled");
        Check.Equal(2, first.SettleFrames, "two-sample settle");

        DriverFixture refused = DriverFixture.Ready();
        refused.OpenDirection(0, false, false, 10.0);
        Check.False(refused.Driver.PendingAccepted, "refused result");
        Check.False(
            refused.Driver.PendingMovementScheduled,
            "no immediate movement");
        refused.SettleCurrent(
            ProtocolSamples.InitialCapture, 11.0);
        StepRecord second = refused.Sink.StepRecords[0];
        Check.Equal(OracleInput.North, second.Input, "north step");
        Check.False(second.Accepted, "refused step");
        Check.False(second.MovementScheduled, "no scheduled movement");
    }

    private static void UndoAcceptanceAndRestoreRules()
    {
        DriverFixture accepted = DriverFixture.Ready();
        accepted.OpenUndo(true, false, 10.0);
        Check.Equal(
            OracleInput.Undo,
            accepted.Driver.PendingInput,
            "Undo input");
        Check.True(accepted.Driver.PendingAccepted, "restore accepted");
        Check.False(
            accepted.Driver.PendingMovementScheduled,
            "top-level Moving result");

        DriverFixture refused = DriverFixture.Ready();
        refused.OpenUndo(false, false, 10.0);
        Check.False(refused.Driver.PendingAccepted, "no restore refused");

        DriverFixture outside = DriverFixture.Ready();
        outside.Driver.RestoreObserved();
        Check.Equal(
            "hook_order_mismatch",
            outside.Sink.ErrorRecords[0].Code,
            "restore outside Undo");
    }
}
~~~

Register PassiveDriverInputTests after PassiveDriverInitialTests. The
cumulative manifest is exactly:

~~~csharp
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 },
    { "driver-initial", 8 },
    { "driver-input", 6 }
});
~~~

- [ ] **Step 2: Run RED**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore -- --cohort driver-input
~~~

Require a compiler diagnostic naming ProcessInputEntered. Fixture, SDK, and
assets failures are not the intended RED.

- [ ] **Step 3: Implement the complete direction and Undo partial**

Create PassiveDriverInput.cs exactly:

~~~csharp
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

    private ProcessInputContext processInput;
    private UndoContext undoContext;
    private int restartDepth;

    internal HookToken ProcessInputEntered(
        object stateReference,
        int rawDirection,
        double nowSeconds)
    {
        if (!IsObservationActive())
            return HookToken.Inert(HookKind.ProcessInput);

        OracleInput input;
        if (!TryMapCardinal(rawDirection, out input))
        {
            TryFaultInternal(
                "unexpected_input",
                FaultRequest.Offending(completedInputs, null));
            return HookToken.Inert(HookKind.ProcessInput);
        }

        if (playerPoll == null)
        {
            if (phase == PassivePhase.Ready)
            {
                TryFaultInternal(
                    "unscoped_process_input",
                    FaultRequest.Offending(
                        completedInputs, input));
            }
            return HookToken.Inert(HookKind.ProcessInput);
        }

        if (!playerPoll.SawPhysicalPoll
            || playerPoll.SawManualProcessInput
            || playerPoll.RawDirection != rawDirection
            || processInput != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.ProcessInput);
        }
        playerPoll.SawManualProcessInput = true;

        if (!HandleManualAttempt(
            input, stateReference, nowSeconds))
        {
            return HookToken.Inert(HookKind.ProcessInput);
        }

        HookToken token = NewToken(HookKind.ProcessInput);
        if (!token.Active)
            return token;
        processInput =
            new ProcessInputContext { Id = token.Id };
        return token;
    }

    internal void ProcessInputReturned(
        HookToken token,
        bool accepted,
        bool movementScheduled)
    {
        if (!ConsumeOrdinaryToken(
            token, HookKind.ProcessInput))
        {
            return;
        }
        if (processInput == null
            || processInput.Id != token.Id
            || !attemptPending
            || attemptOutcomeKnown)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        processInput = null;
        attemptAccepted = accepted;
        attemptMovementScheduled = movementScheduled;
        attemptOutcomeKnown = true;
    }

    internal void ProcessInputThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(
            token, HookKind.ProcessInput))
        {
            return;
        }
        if (processInput == null
            || processInput.Id != token.Id)
        {
            throw new InvalidOperationException(
                "ProcessInput token mismatch");
        }
        processInput = null;
    }

    internal HookToken UndoEntered(
        object stateReference,
        double nowSeconds)
    {
        if (restartDepth > 0)
            return HookToken.Inert(HookKind.Undo);
        if (!IsObservationActive())
            return HookToken.Inert(HookKind.Undo);
        if (undoContext != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return HookToken.Inert(HookKind.Undo);
        }
        if (!HandleManualAttempt(
            OracleInput.Undo, stateReference, nowSeconds))
        {
            return HookToken.Inert(HookKind.Undo);
        }
        HookToken token = NewToken(HookKind.Undo);
        if (!token.Active)
            return token;
        undoContext = new UndoContext { Id = token.Id };
        return token;
    }

    internal void RestoreObserved()
    {
        if (restartDepth > 0 || !IsObservationActive())
            return;
        if (undoContext == null || undoContext.RestoreSeen)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        undoContext.RestoreSeen = true;
    }

    internal void UndoReturned(
        HookToken token,
        bool movementScheduled)
    {
        if (!ConsumeOrdinaryToken(token, HookKind.Undo))
            return;
        if (undoContext == null
            || undoContext.Id != token.Id
            || !attemptPending
            || attemptOutcomeKnown)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        bool accepted = undoContext.RestoreSeen;
        undoContext = null;
        attemptAccepted = accepted;
        attemptMovementScheduled = movementScheduled;
        attemptOutcomeKnown = true;
    }

    internal void UndoThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(token, HookKind.Undo))
            return;
        if (undoContext == null
            || undoContext.Id != token.Id)
        {
            throw new InvalidOperationException(
                "Undo token mismatch");
        }
        undoContext = null;
    }

    partial void EmitSettledAttempt(
        CaptureRecord capture,
        int settleFrames,
        DateTime utcNow,
        ref bool handled)
    {
        handled = true;
        if (!attemptPending || !attemptOutcomeKnown)
        {
            throw new InvalidOperationException(
                "settled attempt has no complete outcome");
        }

        sink.WriteStep(
            new StepRecord(
                runId,
                completedInputs,
                attemptInput,
                attemptAccepted,
                attemptMovementScheduled,
                settleFrames,
                false,
                capture));
        completedInputs++;
        stableState = attemptState;
        ClearAttemptAfterStep();
        lastCapture = null;

        if (completedInputs == expectedInputCount)
        {
            bool terminalHandled = false;
            FinishExpectedInputCount(
                utcNow, ref terminalHandled);
            if (!terminalHandled)
            {
                throw new InvalidOperationException(
                    "terminal extension is unavailable");
            }
            return;
        }

        try
        {
            reporter.Ready(completedInputs);
        }
        catch (Exception)
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
        }
    }
}
~~~

- [ ] **Step 4: Run GREEN and the net35 gate**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore -- --cohort driver-input
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build oracle/plugin/tests/SsrOracle.Core.Net35.csproj -c Release --no-restore -warnaserror
git diff --check
~~~

- [ ] **Step 5: Inspect the task diff and commit**

Inspect the full diff, retain it with the task report, and then run exactly:

~~~bash
git diff -- oracle/plugin/Core/PassiveDriverInput.cs oracle/plugin/tests/PassiveDriverTestSupport.cs oracle/plugin/tests/PassiveDriverInputTests.cs oracle/plugin/tests/Program.cs
git add oracle/plugin/Core/PassiveDriverInput.cs oracle/plugin/tests/PassiveDriverTestSupport.cs oracle/plugin/tests/PassiveDriverInputTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: attribute passive input attempts"
~~~

#### Task 5.2: Balance restart, state replacement, and thrown hooks

- [ ] **Step 1: Append the final two RED input tests**

**Files:**
- Create: oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
- Modify: oracle/plugin/tests/PassiveDriverInputTests.cs
- Modify: oracle/plugin/tests/Program.cs

**Interfaces:**
- Produces RestartEntered(), RestartReturned(HookToken),
  RestartThrew(HookToken), StateSetEntered(object, object),
  StateSetReturned(HookToken, object, double), StateSetThrew(HookToken), and
  ClearThrew(HookToken).
- An outer Restart establishes depth before atomically selecting
  unexpected_input. Its ErrorRecord always has null input fields. Recursive
  Restart and nested Undo/Restore callbacks balance bookkeeping without a
  second terminal claim.
- State replacement before Initial starts a fresh frame-zero initial epoch.
  Replacement after Initial faults with state_replaced. ClearThrew dispatches
  by HookKind, consumes at most once, and never changes a first-fault winner.

Add these two registrations after UndoAcceptanceAndRestoreRules, bringing the
driver-input registration total to exactly eight:

~~~csharp
tests.Add("driver-input", "restart depth and null fields",
    RestartDepthAndNullFields);
tests.Add("driver-input", "state replacement and ClearThrew",
    StateReplacementAndClearThrew);
~~~

Insert these two method bodies before the final brace of
PassiveDriverInputTests:

~~~csharp
private static void RestartDepthAndNullFields()
{
    DriverFixture beforeInitial = DriverFixture.Active();
    beforeInitial.Observe(
        beforeInitial.State,
        beforeInitial.State,
        1.0,
        true,
        ProtocolSamples.InitialCapture);
    HookToken early = beforeInitial.Driver.RestartEntered();
    ErrorRecord earlyError = beforeInitial.Sink.ErrorRecords[0];
    Check.Equal("unexpected_input", earlyError.Code,
        "pre-initial restart code");
    Check.False(earlyError.InputIndex.HasValue,
        "pre-initial restart index null");
    Check.False(earlyError.Input.HasValue,
        "pre-initial restart input null");
    Check.Equal(1, earlyError.SettleFrames,
        "pre-initial restart keeps initial frame count");
    beforeInitial.Driver.RestartReturned(early);

    DriverFixture fixture = DriverFixture.Ready();
    fixture.OpenDirection(2, true, true, 10.0);
    fixture.Observe(
        fixture.State,
        fixture.State,
        11.0,
        false,
        ProtocolSamples.MovedCapture);

    HookToken outer = fixture.Driver.RestartEntered();
    ErrorRecord error = fixture.Sink.ErrorRecords[0];
    Check.Equal("unexpected_input", error.Code, "restart code");
    Check.False(error.InputIndex.HasValue, "restart index null");
    Check.False(error.Input.HasValue, "restart input null");
    Check.Equal(1, error.SettleFrames, "active attempt frames");

    HookToken recursive = fixture.Driver.RestartEntered();
    HookToken nestedUndo =
        fixture.Driver.UndoEntered(fixture.State, 12.0);
    fixture.Driver.RestoreObserved();
    fixture.Driver.UndoReturned(nestedUndo, false);
    fixture.Driver.RestartReturned(recursive);
    fixture.Driver.RestartReturned(outer);
    Check.Equal(
        1,
        fixture.Sink.ErrorRecords.Count,
        "nested path cannot emit a second Error");
}

private static void StateReplacementAndClearThrew()
{
    DriverFixture preInitial = DriverFixture.Active();
    preInitial.Observe(
        preInitial.State,
        preInitial.State,
        1.0,
        true,
        ProtocolSamples.InitialCapture);
    HookToken replace = preInitial.Driver.StateSetEntered(
        preInitial.State, preInitial.OtherState);
    preInitial.Driver.StateSetReturned(
        replace, preInitial.OtherState, 2.0);
    Check.Equal(
        PassivePhase.AwaitInitialNeutral,
        preInitial.Driver.Phase,
        "replacement starts new initial epoch");
    Check.Equal(
        0,
        preInitial.Driver.CurrentSettleFrames,
        "SetGameState return is not an Update frame");

    DriverFixture ready = DriverFixture.Ready();
    HookToken late = ready.Driver.StateSetEntered(
        ready.State, ready.OtherState);
    ready.Driver.StateSetReturned(
        late, ready.OtherState, 10.0);
    Check.Equal(
        "state_replaced",
        ready.Sink.ErrorRecords[0].Code,
        "post-initial replacement faults");

    DriverFixture player = DriverFixture.Ready();
    HookToken playerToken = player.Driver.PlayerPollEntered();
    player.Driver.ClearThrew(playerToken);
    player.Driver.ClearThrew(playerToken);
    HookToken nextPlayer = player.Driver.PlayerPollEntered();
    Check.True(nextPlayer.Active, "player scope cleared once");
    player.Driver.PlayerPollReturned(nextPlayer);

    DriverFixture process = DriverFixture.Ready();
    HookToken processPoll = process.Driver.PlayerPollEntered();
    process.Driver.PhysicalPollReturned(2);
    HookToken processToken = process.Driver.ProcessInputEntered(
        process.State, 2, 10.0);
    process.Driver.ClearThrew(processToken);
    process.Driver.ClearThrew(processToken);
    process.Driver.PlayerPollReturned(processPoll);

    DriverFixture undo = DriverFixture.Ready();
    HookToken undoToken =
        undo.Driver.UndoEntered(undo.State, 10.0);
    undo.Driver.ClearThrew(undoToken);
    undo.Driver.ClearThrew(undoToken);

    DriverFixture stateSet = DriverFixture.Ready();
    HookToken stateToken = stateSet.Driver.StateSetEntered(
        stateSet.State, stateSet.State);
    stateSet.Driver.ClearThrew(stateToken);
    stateSet.Driver.ClearThrew(stateToken);

    DriverFixture restart = DriverFixture.Ready();
    HookToken restartToken = restart.Driver.RestartEntered();
    restart.Driver.ClearThrew(restartToken);
    restart.Driver.ClearThrew(restartToken);
    Check.Equal(
        1,
        restart.Sink.ErrorRecords.Count,
        "restart cleanup preserves first fault");
}
~~~

Update only the manifest value from driver-input=6 to driver-input=8. The full
cumulative manifest at this checkpoint is:

~~~csharp
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 },
    { "driver-initial", 8 },
    { "driver-input", 8 }
});
~~~

- [ ] **Step 2: Run RED**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore -- --cohort driver-input
~~~

Require compiler diagnostics naming RestartEntered, StateSetEntered, or
ClearThrew.

- [ ] **Step 3: Implement the complete lifecycle-hook partial**

Create PassiveDriverLifecycleHooks.cs exactly:

~~~csharp
using System;
using System.Collections.Generic;

internal sealed partial class PassiveDriver
{
    private sealed class StateSetContext
    {
        internal long Id;
        internal object Before;
    }

    private readonly List<long> restartContexts =
        new List<long>();
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
        {
            TryFaultInternal(
                "unexpected_input", FaultRequest.Restart());
        }
        return token;
    }

    internal void RestartReturned(HookToken token)
    {
        if (!ConsumeOrdinaryToken(token, HookKind.Restart))
            return;
        PopRestart(token.Id);
    }

    internal void RestartThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(token, HookKind.Restart))
            return;
        PopRestart(token.Id);
    }

    internal HookToken StateSetEntered(
        object beforeState,
        object requestedState)
    {
        if (!IsObservationActive())
            return HookToken.Inert(HookKind.StateSet);
        if (stateSetContext != null)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
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
        HookToken token,
        object afterState,
        double nowSeconds)
    {
        if (!ConsumeOrdinaryToken(token, HookKind.StateSet))
            return;
        if (stateSetContext == null
            || stateSetContext.Id != token.Id)
        {
            TryFaultInternal(
                "hook_order_mismatch", FaultRequest.Derived());
            return;
        }
        StateSetContext context = stateSetContext;
        stateSetContext = null;
        if (!IsObservationActive())
            return;
        if (!IsValidMonotonic(nowSeconds))
        {
            TryFaultInternal(
                "observer_exception", FaultRequest.Derived());
            return;
        }

        if (phase == PassivePhase.AwaitGame
            || phase == PassivePhase.AwaitInitialNeutral)
        {
            if (afterState == null)
            {
                ResetToAwaitGame();
            }
            else if (!Object.ReferenceEquals(
                context.Before, afterState)
                || !Object.ReferenceEquals(
                    epochState, afterState))
            {
                StartInitialEpoch(
                    afterState, nowSeconds, false);
            }
            return;
        }

        object expectedState =
            phase == PassivePhase.Settling
            ? attemptState
            : stableState;
        if (afterState == null
            || !Object.ReferenceEquals(
                expectedState, afterState))
        {
            TryFaultInternal(
                "state_replaced", FaultRequest.Derived());
        }
    }

    internal void StateSetThrew(HookToken token)
    {
        if (!ConsumeCleanupToken(token, HookKind.StateSet))
            return;
        if (stateSetContext == null
            || stateSetContext.Id != token.Id)
        {
            throw new InvalidOperationException(
                "SetGameState token mismatch");
        }
        stateSetContext = null;
    }

    internal void ClearThrew(HookToken token)
    {
        if (token == null || !token.Active)
            return;
        switch (token.Kind)
        {
            case HookKind.PlayerPoll:
                PlayerPollThrew(token);
                return;
            case HookKind.ProcessInput:
                ProcessInputThrew(token);
                return;
            case HookKind.Undo:
                UndoThrew(token);
                return;
            case HookKind.Restart:
                RestartThrew(token);
                return;
            case HookKind.StateSet:
                StateSetThrew(token);
                return;
            default:
                throw new InvalidOperationException(
                    "unknown hook token kind");
        }
    }

    private void PopRestart(long id)
    {
        int last = restartContexts.Count - 1;
        if (last < 0 || restartContexts[last] != id)
        {
            throw new InvalidOperationException(
                "Restart token mismatch");
        }
        restartContexts.RemoveAt(last);
        restartDepth--;
        if (restartDepth < 0
            || restartDepth != restartContexts.Count)
        {
            throw new InvalidOperationException(
                "Restart depth imbalance");
        }
    }
}
~~~

The requestedState parameter is deliberately not trusted as proof of a
replacement. The decision uses only the reread afterState identity; retaining
the parameter in the method contract keeps the Core API aligned with the exact
SetGameState patch without dereferencing game types.

- [ ] **Step 4: Run GREEN and the net35 gate**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore -- --cohort driver-input
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build oracle/plugin/tests/SsrOracle.Core.Net35.csproj -c Release --no-restore -warnaserror
git diff --check
~~~

- [ ] **Step 5: Inspect the task diff and commit**

Retain the complete task diff and GREEN evidence, then run exactly:

~~~bash
git diff -- oracle/plugin/Core/PassiveDriverLifecycleHooks.cs oracle/plugin/tests/PassiveDriverInputTests.cs oracle/plugin/tests/Program.cs
git add oracle/plugin/Core/PassiveDriverLifecycleHooks.cs oracle/plugin/tests/PassiveDriverInputTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: balance passive lifecycle hooks"
~~~

#### Task 5.3: Finalize success and make terminal ownership immutable

- [ ] **Step 1: Add the complete terminal fixture and exactly six RED tests**

**Files:**
- Create: oracle/plugin/Core/PassiveDriverCompletion.cs
- Modify: oracle/plugin/tests/PassiveDriverTestSupport.cs
- Create: oracle/plugin/tests/PassiveDriverTerminalTests.cs
- Create: oracle/plugin/tests/PassiveDriverTests.cs
- Modify: oracle/plugin/tests/Program.cs

**Interfaces:**
- Implements FinishExpectedInputCount. The third flushed Step is followed by
  End, Close, and Complete in exactly that order.
- One Interlocked terminal claim owns success or the first fault. Sink failure
  yields only trace_io_failed. A Complete reporter exception cannot rewrite
  the closed trace; it sets the in-memory phase to Faulted and reports
  observer_exception best-effort without Error or another Close.
- Dispose is idempotent, closes at most once, and makes later callbacks inert.
  No terminal path holds a monitor around sink or reporter code.

Append this method in the DriverFixture partial body:

~~~csharp
internal void CompleteThreeSteps()
{
    OpenDirection(2, true, true, 10.0);
    SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
    OpenDirection(0, false, false, 20.0);
    SettleCurrent(ProtocolSamples.MovedCapture, 21.0);
    OpenUndo(true, false, 30.0);
    SettleCurrent(ProtocolSamples.InitialCapture, 31.0);
}
~~~

Create PassiveDriverTerminalTests.cs exactly:

~~~csharp
using System;
using System.Collections.Generic;
using System.Threading;

internal static class PassiveDriverTerminalTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("driver-terminal", "three steps End Close Complete order",
            ThreeStepsEndCloseCompleteOrder);
        tests.Add("driver-terminal", "error field policy is exact",
            ErrorFieldPolicyIsExact);
        tests.Add("driver-terminal", "sink failure uses trace io marker",
            SinkFailureUsesTraceIoMarker);
        tests.Add("driver-terminal", "completion reporter cannot rewrite trace",
            CompletionReporterCannotRewriteTrace);
        tests.Add("driver-terminal", "first fault wins race",
            FirstFaultWinsRace);
        tests.Add("driver-terminal", "Dispose and late callbacks are final",
            DisposeAndLateCallbacksAreFinal);
    }

    private static void ThreeStepsEndCloseCompleteOrder()
    {
        DriverFixture fixture = DriverFixture.Ready();
        fixture.CompleteThreeSteps();
        Check.Equal(PassivePhase.Done, fixture.Driver.Phase, "Done");
        Check.Equal(3, fixture.Sink.StepRecords.Count, "three steps");
        Check.Equal(1, fixture.Sink.EndRecords.Count, "one End");
        Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
        Check.Sequence(
            new string[]
            {
                "sink:run",
                "sink:initial",
                "report:ready:0/3",
                "sink:step:0",
                "report:ready:1/3",
                "sink:step:1",
                "report:ready:2/3",
                "sink:step:2",
                "sink:end",
                "sink:close",
                "report:complete"
            },
            fixture.Events.ToArray(),
            "record and marker order");
    }

    private static void ErrorFieldPolicyIsExact()
    {
        DriverFixture early = DriverFixture.Active();
        HookToken earlyPoll = early.Driver.PlayerPollEntered();
        early.Driver.PhysicalPollReturned(0);
        early.Driver.ProcessInputEntered(early.State, 0, 1.0);
        early.Driver.PlayerPollReturned(earlyPoll);
        ErrorRecord offending = early.Sink.ErrorRecords[0];
        Check.Equal("input_before_initial", offending.Code, "early code");
        Check.Equal((int?)0, offending.InputIndex, "early index");
        Check.Equal((OracleInput?)OracleInput.North, offending.Input,
            "early input");
        Check.Equal(0, offending.SettleFrames, "early frames");

        DriverFixture pending = DriverFixture.Ready();
        pending.OpenDirection(2, true, true, 10.0);
        pending.Neutral();
        pending.Observe(pending.State, pending.State, 11.0, true,
            ProtocolSamples.MovedCapture);
        pending.Driver.TryFault("settle_timeout");
        ErrorRecord during = pending.Sink.ErrorRecords[0];
        Check.Equal((int?)0, during.InputIndex, "pending index");
        Check.Equal((OracleInput?)OracleInput.West, during.Input,
            "pending input");
        Check.Equal(1, during.SettleFrames, "pending frames");
        Check.Same(ProtocolSamples.MovedCapture, during.LastCapture,
            "latest bounded capture");

        DriverFixture failedProgress = DriverFixture.Ready();
        failedProgress.Reporter.ReadyFailure =
            new InvalidOperationException("ready marker");
        failedProgress.OpenDirection(2, true, true, 10.0);
        failedProgress.SettleCurrent(
            ProtocolSamples.MovedCapture, 11.0);
        ErrorRecord progressError = failedProgress.Sink.ErrorRecords[0];
        Check.Equal("observer_exception", progressError.Code,
            "intermediate Ready failure code");
        Check.True(progressError.LastCapture == null,
            "completed step epoch is not retained as last_capture");

        DriverFixture restart = DriverFixture.Ready();
        restart.OpenDirection(2, true, true, 10.0);
        restart.Observe(restart.State, restart.State, 11.0, false,
            ProtocolSamples.MovedCapture);
        restart.Driver.RestartEntered();
        ErrorRecord restarted = restart.Sink.ErrorRecords[0];
        Check.False(restarted.InputIndex.HasValue, "Restart index null");
        Check.False(restarted.Input.HasValue, "Restart input null");
        Check.Equal(1, restarted.SettleFrames, "Restart keeps frames");

        DriverFixture generic = DriverFixture.Ready();
        generic.Driver.TryFault("observer_exception");
        ErrorRecord derived = generic.Sink.ErrorRecords[0];
        Check.False(derived.InputIndex.HasValue, "derived index null");
        Check.False(derived.Input.HasValue, "derived input null");
        Check.Equal(0, derived.SettleFrames, "Ready has zero frames");
    }

    private static void SinkFailureUsesTraceIoMarker()
    {
        List<string> prepareEvents = new List<string>();
        FakeTraceSink prepareSink = new FakeTraceSink(prepareEvents);
        FakePassiveReporter prepareReporter =
            new FakePassiveReporter(prepareEvents);
        prepareSink.RunFailure = new TraceIoException("run");
        PassiveDriver prepareDriver = new PassiveDriver(
            prepareSink, prepareReporter, 3, 600, 30.0);
        Check.False(prepareDriver.Prepare(ProtocolSamples.Run),
            "Run failure");
        Check.Equal(1, prepareSink.CloseCalls, "prepare close");
        Check.True(prepareEvents.Contains(
            "report:failed:trace_io_failed"),
            "prepare trace-io marker");

        DriverFixture write = DriverFixture.Ready();
        write.Sink.ErrorFailure = new TraceIoException("error");
        write.Driver.TryFault("observer_exception");
        Check.Equal(0, write.Sink.ErrorRecords.Count, "no false Error");
        Check.Equal(1, write.Sink.CloseCalls, "write failure close");
        Check.True(write.Events.Contains(
            "report:failed:trace_io_failed"),
            "runtime trace-io marker");

        DriverFixture close = DriverFixture.Ready();
        close.Sink.CloseFailure = new TraceIoException("close");
        close.Driver.TryFault("observer_exception");
        Check.Equal(1, close.Sink.ErrorRecords.Count, "Error flushed");
        Check.Equal(1, close.Sink.CloseCalls, "Close attempted once");
        Check.True(close.Events.Contains(
            "report:failed:trace_io_failed"),
            "close failure marker");
    }

    private static void CompletionReporterCannotRewriteTrace()
    {
        DriverFixture fixture = DriverFixture.Ready();
        fixture.Reporter.CompleteFailure =
            new InvalidOperationException("reporter");
        fixture.CompleteThreeSteps();
        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
            "outer marker gate fails");
        Check.Equal(1, fixture.Sink.EndRecords.Count, "End immutable");
        Check.Equal(0, fixture.Sink.ErrorRecords.Count, "no Error rewrite");
        Check.Equal(1, fixture.Sink.CloseCalls, "no second Close");
        int tail = fixture.Events.Count - 5;
        Check.Sequence(
            new string[]
            {
                "sink:step:2",
                "sink:end",
                "sink:close",
                "report:complete",
                "report:failed:observer_exception"
            },
            fixture.Events.GetRange(tail, 5).ToArray(),
            "closed trace remains immutable");
    }

    private static void FirstFaultWinsRace()
    {
        DriverFixture fixture = DriverFixture.Ready();
        int winners = 0;
        using (ManualResetEvent start = new ManualResetEvent(false))
        {
            Thread first = new Thread(delegate()
            {
                start.WaitOne();
                if (fixture.Driver.TryFault("observer_exception"))
                    Interlocked.Increment(ref winners);
            });
            Thread second = new Thread(delegate()
            {
                start.WaitOne();
                if (fixture.Driver.TryFault("capture_failed"))
                    Interlocked.Increment(ref winners);
            });
            first.Start();
            second.Start();
            start.Set();
            first.Join();
            second.Join();
        }
        Check.Equal(1, winners, "one atomic owner");
        Check.Equal(1, fixture.Sink.ErrorRecords.Count, "one Error");
        Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
        int failureMarkers = 0;
        for (int index = 0; index < fixture.Events.Count; index++)
        {
            if (fixture.Events[index].StartsWith(
                "report:failed:", StringComparison.Ordinal))
            {
                failureMarkers++;
            }
        }
        Check.Equal(1, failureMarkers, "one terminal marker");
    }

    private static void DisposeAndLateCallbacksAreFinal()
    {
        DriverFixture disposed = DriverFixture.Active();
        HookToken open = disposed.Driver.PlayerPollEntered();
        disposed.Driver.Dispose();
        disposed.Driver.Dispose();
        disposed.Driver.ClearThrew(open);
        disposed.Driver.ClearThrew(open);
        Check.Equal(1, disposed.Sink.CloseCalls, "Dispose close once");
        Check.Equal(0, disposed.Sink.EndRecords.Count, "no End");
        Check.Equal(0, disposed.Sink.ErrorRecords.Count, "no Error");
        Check.False(disposed.Driver.TryFault("observer_exception"),
            "disabled late fault ignored");
        FakeUpdateObservation late = new FakeUpdateObservation
        {
            FirstState = disposed.State,
            SecondState = disposed.State,
            Now = 5.0
        };
        disposed.Boundary.Observe(late);
        Check.Equal(0, late.PathCalls, "late update inactive");

        DriverFixture done = DriverFixture.Ready();
        done.CompleteThreeSteps();
        int eventCount = done.Events.Count;
        done.Driver.PlayerPollReturned(
            done.Driver.PlayerPollEntered());
        done.Driver.RestartEntered();
        done.Driver.TryFault("observer_exception");
        done.Driver.Dispose();
        Check.Equal(eventCount, done.Events.Count, "Done is final");
        Check.Equal(1, done.Sink.CloseCalls, "Done close once");
    }
}
~~~

Create `PassiveDriverTests.cs` with the permanent aggregate registration used
by every later task and by the final Program:

~~~csharp
internal static class PassiveDriverTests
{
    internal static void Register(TestRegistry tests)
    {
        PassiveDriverBoundaryTests.Register(tests);
        PassiveDriverInitialTests.Register(tests);
        PassiveDriverInputTests.Register(tests);
        PassiveDriverTerminalTests.Register(tests);
    }
}
~~~

Replace the four individual driver registrations in `Program.cs` with
`PassiveDriverTests.Register(tests)`. The
cumulative Program manifest is exactly:

~~~csharp
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 },
    { "driver-initial", 8 },
    { "driver-input", 8 },
    { "driver-terminal", 6 }
});
~~~

- [ ] **Step 2: Run RED**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore -- --cohort driver-terminal
~~~

Require ThreeStepsEndCloseCompleteOrder to fail because the terminal partial
seam has no implementation. Do not accept a fixture, SDK, or assets failure.

- [ ] **Step 3: Implement the complete terminal partial**

Create PassiveDriverCompletion.cs exactly:

~~~csharp
using System;
using System.Threading;

internal sealed partial class PassiveDriver
{
    partial void FinishExpectedInputCount(
        DateTime finishedAtUtc,
        ref bool handled)
    {
        handled = true;
        FinishSuccess(finishedAtUtc);
    }

    private void FinishSuccess(DateTime finishedAtUtc)
    {
        OracleValidation.Utc(finishedAtUtc, "finishedAtUtc");
        if (finishedAtUtc < startedAtUtc)
            throw new ArgumentOutOfRangeException("finishedAtUtc");
        if (completedInputs != expectedInputCount)
            throw new InvalidOperationException(
                "terminal input count mismatch");
        if (Interlocked.CompareExchange(
            ref terminalOwner, 1, 0) != 0)
        {
            return;
        }

        try
        {
            sink.WriteEnd(new EndRecord(
                runId, expectedInputCount, finishedAtUtc));
            CloseSink();
            phase = PassivePhase.Done;
        }
        catch (Exception)
        {
            phase = PassivePhase.Faulted;
            BestEffortClose();
            SafeFailed("trace_io_failed");
            return;
        }

        try
        {
            reporter.Complete();
        }
        catch (Exception)
        {
            phase = PassivePhase.Faulted;
            SafeFailed("observer_exception");
        }
    }
}
~~~

- [ ] **Step 4: Run GREEN and the net35 gate**

~~~bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore -- --cohort driver-terminal
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build oracle/plugin/tests/SsrOracle.Core.Net35.csproj -c Release --no-restore -warnaserror
git diff --check
~~~

- [ ] **Step 5: Inspect the task diff and commit**

Retain the complete task diff and GREEN evidence, then run exactly:

~~~bash
git diff -- oracle/plugin/Core/PassiveDriverCompletion.cs oracle/plugin/tests/PassiveDriverTestSupport.cs oracle/plugin/tests/PassiveDriverTerminalTests.cs oracle/plugin/tests/PassiveDriverTests.cs oracle/plugin/tests/Program.cs
git add oracle/plugin/Core/PassiveDriverCompletion.cs oracle/plugin/tests/PassiveDriverTestSupport.cs oracle/plugin/tests/PassiveDriverTerminalTests.cs oracle/plugin/tests/PassiveDriverTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: finalize passive trace capture"
~~~

### Track 6: Parse exact read-only configuration and physical paths

#### Task 6.1: Parse strict read-only configuration bytes

- [ ] **Step 1: Write the six failing configuration tests**

**Files:**
- Create: `oracle/plugin/Core/PassiveConfiguration.cs`
- Create: `oracle/plugin/tests/ConfigurationTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes `OracleMode` and the fixed numeric values from `OracleProtocol`.
- Produces `IConfigurationBytes.ReadAllBytes(string path) -> byte[]` and
  `IConfigurationPathResolver.ResolveExistingDirectory(string requested) ->
  string`/`Contains(string parent, string candidate) -> bool`.
- Produces the independently testable seams
  `OracleConfiguration.Parse(byte[] bytes, IConfigurationPathResolver paths)`
  and `OracleConfiguration.Load(string path, IConfigurationBytes source,
  IConfigurationPathResolver paths, out byte[] originalBytes)`.
- Produces `OracleConfigurationException` with exact get-only `Code`.
  Unsupported exactly spelled `Mode` values use `invalid_mode`; byte,
  grammar, cardinality, and fixed-value failures use
  `invalid_configuration`; the path resolver uses only `invalid_path`.
- Produces immutable `OracleConfiguration` and `PassiveConfiguration` values.
  Off carries no passive value and never calls the path resolver. Passive
  stores only canonical paths returned by the resolver.
- Task 6.2 supplies the production physical resolver and the final
  `Parse(byte[])`, `Load(string, out byte[])`, and
  `Load(string, IConfigurationBytes, out byte[])` overloads. Until then,
  callers must explicitly supply the resolver; there is no fallback branch.

Create `oracle/plugin/tests/ConfigurationTests.cs` with this complete body:

```csharp
using System;
using System.Globalization;
using System.IO;
using System.Security;
using System.Security.Cryptography;
using System.Text;

internal static class ConfigurationTests
{
    private const string PinnedModeOffSha256 =
        "cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d";

    internal static void Register(TestRegistry tests, HarnessOptions options)
    {
        if (tests == null)
            throw new ArgumentNullException("tests");
        if (options == null)
            throw new ArgumentNullException("options");
        tests.Add("config", "off grammar is exact and read only",
            delegate { OffGrammarIsExactAndReadOnly(options.ModeOffFixturePath); });
        tests.Add("config", "off malformed inputs are rejected",
            OffMalformedInputsAreRejected);
        tests.Add("config", "unsupported modes are typed",
            UnsupportedModesAreTyped);
        tests.Add("config", "passive values are canonical",
            PassiveValuesAreCanonical);
        tests.Add("config", "passive failures are typed",
            PassiveFailuresAreTyped);
        tests.Add("config", "configuration reads are typed",
            ConfigurationReadsAreTyped);
    }

    private static void OffGrammarIsExactAndReadOnly(string fixturePath)
    {
        byte[] bytes = Utf8(
            "; portable legacy fixture\r\n\r\n"
            + "[Oracle]\r\n"
            + "Mode = off\r\n"
            + "OutputDirectory = relative-and-unread\r\n"
            + "RunName = arbitrary-and-unread\r\n"
            + "SaveDirectory =\r\n"
            + "InputPath =\r\n"
            + "MaxSettleFrames = not-read\r\n"
            + "MaxSettleSeconds = not-read\r\n"
            + "ExpectedInitialSha256 =\r\n");
        byte[] snapshot = (byte[])bytes.Clone();
        StaticConfigurationBytes source = new StaticConfigurationBytes(bytes);
        byte[] retained;
        OracleConfiguration configuration = OracleConfiguration.Load(
            "/private/tmp/portable-off.cfg", source,
            FakeConfigurationPathResolver.Stable(), out retained);

        Check.Equal(OracleMode.Off, configuration.Mode, "off mode");
        Check.True(configuration.Passive == null, "off has no passive values");
        Check.Equal(1, source.ReadCount, "one read");
        Check.Equal("/private/tmp/portable-off.cfg", source.LastPath,
            "read path");
        Check.Bytes(snapshot, source.Bytes, "source bytes unchanged");
        Check.Bytes(snapshot, retained, "retained bytes exact");
        Check.False(Object.ReferenceEquals(source.Bytes, retained),
            "retained bytes cloned");

        OracleConfiguration lf = OracleConfiguration.Parse(
            Utf8("[Oracle]\nMode = off\n"),
            FakeConfigurationPathResolver.NeverCalled());
        Check.Equal(OracleMode.Off, lf.Mode, "LF accepted");

        if (fixturePath == null)
            return;
        byte[] before = File.ReadAllBytes(fixturePath);
        Check.Equal(261, before.Length, "pinned fixture length");
        Check.Equal(PinnedModeOffSha256, Sha256(before),
            "pinned fixture hash before parse");
        byte[] originalBytes;
        OracleConfiguration fixture = OracleConfiguration.Load(
            fixturePath, new FileConfigurationBytes(),
            FakeConfigurationPathResolver.NeverCalled(), out originalBytes);
        byte[] after = File.ReadAllBytes(fixturePath);
        Check.Equal(OracleMode.Off, fixture.Mode, "fixture mode");
        Check.Bytes(before, originalBytes, "fixture retained bytes");
        Check.Bytes(before, after, "fixture byte identity");
        Check.Equal(PinnedModeOffSha256, Sha256(after),
            "pinned fixture hash after parse");
    }

    private static void OffMalformedInputsAreRejected()
    {
        InvalidBytesCase[] cases = new InvalidBytesCase[]
        {
            new InvalidBytesCase("missing section", Utf8("Mode = off\n")),
            new InvalidBytesCase("duplicate section",
                Utf8("[Oracle]\nMode = off\n[Oracle]\n")),
            new InvalidBytesCase("case section",
                Utf8("[oracle]\nMode = off\n")),
            new InvalidBytesCase("missing Mode",
                Utf8("[Oracle]\nOutputDirectory = unused\n")),
            new InvalidBytesCase("duplicate Mode",
                Utf8("[Oracle]\nMode = off\nMode = off\n")),
            new InvalidBytesCase("case Mode",
                Utf8("[Oracle]\nmode = off\n")),
            new InvalidBytesCase("other section",
                Utf8("[Oracle]\nMode = off\n[Other]\n")),
            new InvalidBytesCase("unknown key",
                Utf8("[Oracle]\nMode = off\nUnknown = value\n")),
            new InvalidBytesCase("passive key in off",
                Utf8("[Oracle]\nMode = off\nExpectedPassiveInputs = 3\n")),
            new InvalidBytesCase("malformed line",
                Utf8("[Oracle]\nMode = off\nnot-an-entry\n")),
            new InvalidBytesCase("inline semicolon",
                Utf8("[Oracle]\nMode = off ; comment\n")),
            new InvalidBytesCase("inline hash",
                Utf8("[Oracle]\nMode = off # comment\n")),
            new InvalidBytesCase("NUL",
                Utf8("[Oracle]\nMode = off\0\n")),
            new InvalidBytesCase("invalid UTF-8", new byte[] { 0xff }),
            new InvalidBytesCase("UTF-8 BOM",
                WithBom(Utf8("[Oracle]\nMode = off\n"))),
            new InvalidBytesCase("bare CR",
                Utf8("[Oracle]\rMode = off\n")),
            new InvalidBytesCase("duplicate optional key",
                Utf8("[Oracle]\nMode = off\nOutputDirectory = one\n"
                    + "OutputDirectory = two\n")),
            new InvalidBytesCase("case optional key",
                Utf8("[Oracle]\nMode = off\noutputDirectory = unused\n"))
        };
        for (int index = 0; index < cases.Length; index++)
        {
            AssertCode("invalid_configuration", cases[index].Bytes,
                FakeConfigurationPathResolver.NeverCalled(), cases[index].Name);
        }
    }

    private static void UnsupportedModesAreTyped()
    {
        string[] values = new string[] { "replay", "OFF", "unknown", "" };
        for (int index = 0; index < values.Length; index++)
        {
            AssertCode("invalid_mode",
                Utf8("[Oracle]\nMode = " + values[index] + "\n"),
                FakeConfigurationPathResolver.NeverCalled(),
                "mode " + values[index]);
        }
    }

    private static void PassiveValuesAreCanonical()
    {
        OracleConfiguration configuration = OracleConfiguration.Parse(
            Utf8(PassiveText("/configured-output", "passive-trace",
                "/configured-save", "3", "600", "30")),
            FakeConfigurationPathResolver.Stable());
        Check.Equal(OracleMode.Passive, configuration.Mode, "passive mode");
        Check.Equal("/physical/output", configuration.Passive.OutputDirectory,
            "canonical output");
        Check.Equal("passive-trace", configuration.Passive.RunName, "run name");
        Check.Equal("/physical/save", configuration.Passive.SaveDirectory,
            "canonical save");
        Check.Equal(3, configuration.Passive.ExpectedPassiveInputs,
            "input count");
        Check.Equal(600, configuration.Passive.MaxSettleFrames, "frame limit");
        Check.Equal(30, configuration.Passive.MaxSettleSeconds, "time limit");
    }

    private static void PassiveFailuresAreTyped()
    {
        string valid = PassiveText("/configured-output", "passive-trace",
            "/configured-save", "3", "600", "30");
        PassiveFailureCase[] cases = new PassiveFailureCase[]
        {
            new PassiveFailureCase("missing key",
                valid.Replace("ExpectedPassiveInputs = 3\n", ""),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("additional key", valid + "InputPath = x\n",
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("duplicate key",
                valid.Replace("RunName = passive-trace\n",
                    "RunName = passive-trace\nRunName = passive-trace\n"),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("case key",
                valid.Replace("RunName = passive-trace\n",
                    "runName = passive-trace\n"),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("traversal run name",
                PassiveText("/configured-output", "../passive-trace",
                    "/configured-save", "3", "600", "30"),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("noncanonical input count",
                PassiveText("/configured-output", "passive-trace",
                    "/configured-save", "03", "600", "30"),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("wrong frame limit",
                PassiveText("/configured-output", "passive-trace",
                    "/configured-save", "3", "601", "30"),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("wrong seconds",
                PassiveText("/configured-output", "passive-trace",
                    "/configured-save", "3", "600", "+30"),
                FakeConfigurationPathResolver.Stable(),
                "invalid_configuration"),
            new PassiveFailureCase("resolver path failure", valid,
                FakeConfigurationPathResolver.FailOutput(), "invalid_path"),
            new PassiveFailureCase("same canonical directory", valid,
                FakeConfigurationPathResolver.Topology(
                    "/physical/shared", "/physical/shared", true, false),
                "invalid_path"),
            new PassiveFailureCase("output contains save", valid,
                FakeConfigurationPathResolver.Topology(
                    "/physical/tree", "/physical/tree/save", true, false),
                "invalid_path"),
            new PassiveFailureCase("save contains output", valid,
                FakeConfigurationPathResolver.Topology(
                    "/physical/tree/output", "/physical/tree", false, true),
                "invalid_path")
        };
        for (int index = 0; index < cases.Length; index++)
        {
            AssertCode(cases[index].Code, Utf8(cases[index].Text),
                cases[index].Paths, cases[index].Name);
        }
    }

    private static void ConfigurationReadsAreTyped()
    {
        Exception[] failures = new Exception[]
        {
            new FileNotFoundException("injected"),
            new DirectoryNotFoundException("injected"),
            new IOException("injected"),
            new UnauthorizedAccessException("injected"),
            new SecurityException("injected"),
            new NotSupportedException("injected"),
            new ArgumentException("injected")
        };
        for (int index = 0; index < failures.Length; index++)
        {
            Exception failure = failures[index];
            byte[] retained = new byte[] { 1 };
            OracleConfigurationException error =
                Check.Throws<OracleConfigurationException>(delegate
                {
                    OracleConfiguration.Load("/private/tmp/read-failure.cfg",
                        new ThrowingConfigurationBytes(failure),
                        FakeConfigurationPathResolver.NeverCalled(),
                        out retained);
                }, "typed read " + failure.GetType().FullName);
            Check.Equal("invalid_configuration", error.Code, "read code");
            Check.Same(failure, error.InnerException, "read cause");
            Check.True(retained == null, "no bytes retained on read failure");
        }

        byte[] nullRetained = new byte[] { 1 };
        OracleConfigurationException nullError =
            Check.Throws<OracleConfigurationException>(delegate
            {
                OracleConfiguration.Load("/private/tmp/null.cfg",
                    new NullConfigurationBytes(),
                    FakeConfigurationPathResolver.NeverCalled(),
                    out nullRetained);
            }, "null reader result");
        Check.Equal("invalid_configuration", nullError.Code, "null read code");
        Check.True(nullRetained == null, "null read retains nothing");

        InvalidOperationException unexpected =
            new InvalidOperationException("unexpected");
        byte[] unexpectedRetained = null;
        InvalidOperationException propagated =
            Check.Throws<InvalidOperationException>(delegate
            {
                OracleConfiguration.Load("/private/tmp/unexpected.cfg",
                    new ThrowingConfigurationBytes(unexpected),
                    FakeConfigurationPathResolver.NeverCalled(),
                    out unexpectedRetained);
            }, "unexpected reader exception");
        Check.Same(unexpected, propagated, "unexpected exception identity");

        byte[] malformed = Utf8("[Oracle]\nMode = off\nUnknown = value\n");
        byte[] parsedRetained = null;
        OracleConfigurationException parseError =
            Check.Throws<OracleConfigurationException>(delegate
            {
                OracleConfiguration.Load("/private/tmp/malformed.cfg",
                    new StaticConfigurationBytes(malformed),
                    FakeConfigurationPathResolver.NeverCalled(),
                    out parsedRetained);
            }, "post-read parse failure");
        Check.Equal("invalid_configuration", parseError.Code,
            "post-read parse code");
        Check.Bytes(malformed, parsedRetained, "read bytes retained for parse");
        Check.False(Object.ReferenceEquals(malformed, parsedRetained),
            "post-read bytes cloned");
    }

    private static void AssertCode(string expectedCode, byte[] bytes,
        IConfigurationPathResolver paths, string message)
    {
        OracleConfigurationException error =
            Check.Throws<OracleConfigurationException>(delegate
            {
                OracleConfiguration.Parse(bytes, paths);
            }, message);
        Check.Equal(expectedCode, error.Code, message + " code");
    }

    private static string PassiveText(string output, string runName,
        string save, string inputs, string frames, string seconds)
    {
        return "[Oracle]\nMode = passive\n"
            + "OutputDirectory = " + output + "\n"
            + "RunName = " + runName + "\n"
            + "SaveDirectory = " + save + "\n"
            + "ExpectedPassiveInputs = " + inputs + "\n"
            + "MaxSettleFrames = " + frames + "\n"
            + "MaxSettleSeconds = " + seconds + "\n";
    }

    private static byte[] Utf8(string value)
    {
        return new UTF8Encoding(false, true).GetBytes(value);
    }

    private static byte[] WithBom(byte[] body)
    {
        byte[] result = new byte[body.Length + 3];
        result[0] = 0xef;
        result[1] = 0xbb;
        result[2] = 0xbf;
        Buffer.BlockCopy(body, 0, result, 3, body.Length);
        return result;
    }

    private static string Sha256(byte[] bytes)
    {
        byte[] digest;
        using (SHA256 hash = SHA256.Create())
            digest = hash.ComputeHash(bytes);
        StringBuilder text = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
        {
            text.Append(digest[index].ToString(
                "x2", CultureInfo.InvariantCulture));
        }
        return text.ToString();
    }

    private sealed class InvalidBytesCase
    {
        internal InvalidBytesCase(string name, byte[] bytes)
        {
            Name = name;
            Bytes = bytes;
        }
        internal string Name;
        internal byte[] Bytes;
    }

    private sealed class PassiveFailureCase
    {
        internal PassiveFailureCase(string name, string text,
            IConfigurationPathResolver paths, string code)
        {
            Name = name;
            Text = text;
            Paths = paths;
            Code = code;
        }
        internal string Name;
        internal string Text;
        internal IConfigurationPathResolver Paths;
        internal string Code;
    }

    private sealed class StaticConfigurationBytes : IConfigurationBytes
    {
        internal StaticConfigurationBytes(byte[] bytes) { Bytes = bytes; }
        internal byte[] Bytes;
        internal int ReadCount;
        internal string LastPath;
        public byte[] ReadAllBytes(string path)
        {
            ReadCount++;
            LastPath = path;
            return Bytes;
        }
    }

    private sealed class ThrowingConfigurationBytes : IConfigurationBytes
    {
        private readonly Exception failure;
        internal ThrowingConfigurationBytes(Exception failure)
        {
            this.failure = failure;
        }
        public byte[] ReadAllBytes(string path) { throw failure; }
    }

    private sealed class NullConfigurationBytes : IConfigurationBytes
    {
        public byte[] ReadAllBytes(string path) { return null; }
    }

    private sealed class FakeConfigurationPathResolver
        : IConfigurationPathResolver
    {
        private readonly string output;
        private readonly string save;
        private readonly bool outputContainsSave;
        private readonly bool saveContainsOutput;
        private readonly bool failOutput;
        private readonly bool failIfCalled;

        private FakeConfigurationPathResolver(string output, string save,
            bool outputContainsSave, bool saveContainsOutput,
            bool failOutput, bool failIfCalled)
        {
            this.output = output;
            this.save = save;
            this.outputContainsSave = outputContainsSave;
            this.saveContainsOutput = saveContainsOutput;
            this.failOutput = failOutput;
            this.failIfCalled = failIfCalled;
        }

        internal static FakeConfigurationPathResolver Stable()
        {
            return Topology("/physical/output", "/physical/save", false, false);
        }

        internal static FakeConfigurationPathResolver Topology(string output,
            string save, bool outputContainsSave, bool saveContainsOutput)
        {
            return new FakeConfigurationPathResolver(output, save,
                outputContainsSave, saveContainsOutput, false, false);
        }

        internal static FakeConfigurationPathResolver FailOutput()
        {
            return new FakeConfigurationPathResolver(null, null,
                false, false, true, false);
        }

        internal static FakeConfigurationPathResolver NeverCalled()
        {
            return new FakeConfigurationPathResolver(null, null,
                false, false, false, true);
        }

        public string ResolveExistingDirectory(string requested)
        {
            if (failIfCalled)
                throw new InvalidOperationException("path resolver was called");
            if (requested == "/configured-output")
            {
                if (failOutput)
                    throw InvalidPath("injected output failure");
                return output;
            }
            if (requested == "/configured-save")
                return save;
            throw InvalidPath("unexpected path: " + requested);
        }

        public bool Contains(string parent, string candidate)
        {
            if (parent == output && candidate == save)
                return outputContainsSave;
            if (parent == save && candidate == output)
                return saveContainsOutput;
            throw new InvalidOperationException("unexpected containment pair");
        }

        private static OracleConfigurationException InvalidPath(string message)
        {
            return new OracleConfigurationException(
                "invalid_path", new IOException(message));
        }
    }
}
```

When `data/oracle/boot-probe.cfg` is absent in the implementation worktree,
run this exact ignored-fixture precondition before RED. It hard-links only
after proving the retained source hash and never replaces an existing path:

```bash
SSR_MODE_OFF_SOURCE=/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/boot-probe.cfg
SSR_MODE_OFF_DESTINATION="$PWD/data/oracle/boot-probe.cfg"
test "$(shasum -a 256 "$SSR_MODE_OFF_SOURCE" | awk '{print $1}')" = \
  cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d
if test -e "$SSR_MODE_OFF_DESTINATION"; then
  test "$SSR_MODE_OFF_SOURCE" -ef "$SSR_MODE_OFF_DESTINATION"
else
  mkdir -p "$PWD/data/oracle"
  ln "$SSR_MODE_OFF_SOURCE" "$SSR_MODE_OFF_DESTINATION"
fi
git check-ignore "$SSR_MODE_OFF_DESTINATION"
test "$(shasum -a 256 "$SSR_MODE_OFF_DESTINATION" | awk '{print $1}')" = \
  cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d
```

- [ ] **Step 2: Register the exact cumulative manifest and run RED**

After `PassiveDriverTests.Register(tests)`, add
`ConfigurationTests.Register(tests, options)`. The cumulative registration and
manifest block in `Program.Main` is exactly:

```csharp
ProtocolTests.Register(tests);
EncodingTests.Register(tests);
CaptureSignatureTests.Register(tests);
TraceSinkTests.Register(tests);
PassiveDriverTests.Register(tests);
ConfigurationTests.Register(tests, options);
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 },
    { "driver-initial", 8 },
    { "driver-input", 8 },
    { "driver-terminal", 6 },
    { "config", 6 }
});
```

Run:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort config
```

Expected: nonzero compilation failure naming the missing
`IConfigurationPathResolver`, `IConfigurationBytes`, or
`OracleConfiguration`; a fixture-path or restore failure is not the intended
RED.

- [ ] **Step 3: Implement the complete strict byte parser**

Create `oracle/plugin/Core/PassiveConfiguration.cs` with this complete
C# 7.3/net35 body. It has every required namespace, never writes, and the sole
production configuration-file read remains in `FileConfigurationBytes`:

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security;
using System.Text;

internal interface IConfigurationBytes
{
    byte[] ReadAllBytes(string path);
}

internal interface IConfigurationPathResolver
{
    string ResolveExistingDirectory(string requested);
    bool Contains(string parent, string candidate);
}

internal sealed class FileConfigurationBytes : IConfigurationBytes
{
    public byte[] ReadAllBytes(string path)
    {
        return File.ReadAllBytes(path);
    }
}

internal sealed class OracleConfigurationException : Exception
{
    internal OracleConfigurationException(string code, Exception inner)
        : base(code, inner)
    {
        if (code != "invalid_mode"
            && code != "invalid_configuration"
            && code != "invalid_path")
        {
            throw new ArgumentException(
                "invalid configuration error code", "code");
        }
        Code = code;
    }

    internal string Code { get; private set; }
}

internal sealed class OracleConfiguration
{
    private static readonly UTF8Encoding StrictUtf8 =
        new UTF8Encoding(false, true);

    private static readonly string[] OffKeys = new string[]
    {
        "Mode", "OutputDirectory", "RunName", "SaveDirectory",
        "InputPath", "MaxSettleFrames", "MaxSettleSeconds",
        "ExpectedInitialSha256"
    };

    private static readonly string[] PassiveKeys = new string[]
    {
        "Mode", "OutputDirectory", "RunName", "SaveDirectory",
        "ExpectedPassiveInputs", "MaxSettleFrames", "MaxSettleSeconds"
    };

    internal OracleConfiguration(
        OracleMode mode,
        PassiveConfiguration passive)
    {
        if (mode == OracleMode.Off && passive != null)
            throw new ArgumentException("Off cannot carry passive settings");
        if (mode == OracleMode.Passive && passive == null)
            throw new ArgumentNullException("passive");
        if (mode != OracleMode.Off && mode != OracleMode.Passive)
            throw new ArgumentOutOfRangeException("mode");
        Mode = mode;
        Passive = passive;
    }

    internal OracleMode Mode { get; private set; }
    internal PassiveConfiguration Passive { get; private set; }

    internal static OracleConfiguration Load(
        string path,
        IConfigurationBytes source,
        IConfigurationPathResolver paths,
        out byte[] originalBytes)
    {
        if (source == null)
            throw new ArgumentNullException("source");
        if (paths == null)
            throw new ArgumentNullException("paths");
        originalBytes = null;
        byte[] loaded;
        try
        {
            loaded = source.ReadAllBytes(path);
        }
        catch (Exception error)
        {
            if (!(error is IOException)
                && !(error is UnauthorizedAccessException)
                && !(error is SecurityException)
                && !(error is NotSupportedException)
                && !(error is ArgumentException))
            {
                throw;
            }
            throw new OracleConfigurationException(
                "invalid_configuration", error);
        }
        if (loaded == null)
        {
            throw new OracleConfigurationException(
                "invalid_configuration",
                new IOException("configuration reader returned null"));
        }
        originalBytes = (byte[])loaded.Clone();
        return Parse(loaded, paths);
    }

    internal static OracleConfiguration Parse(
        byte[] bytes,
        IConfigurationPathResolver paths)
    {
        if (paths == null)
            throw new ArgumentNullException("paths");
        string text = Decode(bytes);
        Dictionary<string, string> entries = ParseEntries(text);
        string modeText;
        if (!entries.TryGetValue("Mode", out modeText))
            throw InvalidConfiguration("Mode is required");

        if (String.Equals(modeText, "off", StringComparison.Ordinal))
        {
            RequireExactKeys(entries, OffKeys, new string[] { "Mode" });
            return new OracleConfiguration(OracleMode.Off, null);
        }
        if (!String.Equals(modeText, "passive", StringComparison.Ordinal))
            throw InvalidMode("Mode must be off or passive");

        RequireExactKeys(entries, PassiveKeys, PassiveKeys);
        ValidatePassiveScalars(entries);
        string output = paths.ResolveExistingDirectory(
            entries["OutputDirectory"]);
        string save = paths.ResolveExistingDirectory(
            entries["SaveDirectory"]);
        if (String.IsNullOrEmpty(output) || String.IsNullOrEmpty(save))
            throw InvalidPath("path resolver returned an empty path");
        if (paths.Contains(output, save) || paths.Contains(save, output))
            throw InvalidPath("configured output and save paths overlap");

        return new OracleConfiguration(
            OracleMode.Passive,
            new PassiveConfiguration(
                output, entries["RunName"], save,
                OracleProtocol.ExpectedInputCount,
                OracleProtocol.MaxSettleFrames,
                OracleProtocol.MaxSettleSeconds));
    }

    private static string Decode(byte[] bytes)
    {
        if (bytes == null)
            throw InvalidConfiguration("configuration bytes are required");
        if (bytes.Length >= 3
            && bytes[0] == 0xef
            && bytes[1] == 0xbb
            && bytes[2] == 0xbf)
        {
            throw InvalidConfiguration("UTF-8 BOM is forbidden");
        }
        string text;
        try
        {
            text = StrictUtf8.GetString(bytes);
        }
        catch (DecoderFallbackException error)
        {
            throw new OracleConfigurationException(
                "invalid_configuration", error);
        }
        if (text.IndexOf('\0') >= 0)
            throw InvalidConfiguration("configuration contains NUL");
        return NormalizeNewlines(text);
    }

    private static string NormalizeNewlines(string text)
    {
        StringBuilder normalized = new StringBuilder(text.Length);
        for (int index = 0; index < text.Length; index++)
        {
            char value = text[index];
            if (value != '\r')
            {
                normalized.Append(value);
                continue;
            }
            if (index + 1 >= text.Length || text[index + 1] != '\n')
                throw InvalidConfiguration("bare CR is forbidden");
            normalized.Append('\n');
            index++;
        }
        return normalized.ToString();
    }

    private static Dictionary<string, string> ParseEntries(string text)
    {
        Dictionary<string, string> entries =
            new Dictionary<string, string>(StringComparer.Ordinal);
        string[] lines = text.Split(new char[] { '\n' });
        bool sawOracle = false;
        for (int index = 0; index < lines.Length; index++)
        {
            string line = lines[index].Trim();
            if (line.Length == 0)
                continue;
            if (line[0] == '#' || line[0] == ';')
                continue;
            if (line.IndexOf('#') >= 0 || line.IndexOf(';') >= 0)
            {
                throw InvalidConfiguration(
                    "inline comment at line "
                    + (index + 1).ToString(CultureInfo.InvariantCulture));
            }
            if (line[0] == '[')
            {
                if (line != "[Oracle]" || sawOracle)
                {
                    throw InvalidConfiguration(
                        "exactly one [Oracle] section is required");
                }
                sawOracle = true;
                continue;
            }
            if (!sawOracle)
                throw InvalidConfiguration("entry precedes [Oracle]");
            int separator = line.IndexOf('=');
            if (separator <= 0)
            {
                throw InvalidConfiguration(
                    "malformed entry at line "
                    + (index + 1).ToString(CultureInfo.InvariantCulture));
            }
            string key = line.Substring(0, separator).Trim();
            string value = line.Substring(separator + 1).Trim();
            if (key.Length == 0)
                throw InvalidConfiguration("empty key");
            if (entries.ContainsKey(key))
                throw InvalidConfiguration("duplicate key: " + key);
            entries.Add(key, value);
        }
        if (!sawOracle)
            throw InvalidConfiguration("[Oracle] is required");
        return entries;
    }

    private static void RequireExactKeys(
        Dictionary<string, string> entries,
        string[] allowed,
        string[] required)
    {
        foreach (KeyValuePair<string, string> entry in entries)
        {
            if (!ContainsName(allowed, entry.Key))
            {
                throw InvalidConfiguration(
                    "unknown or mis-cased key: " + entry.Key);
            }
        }
        for (int index = 0; index < required.Length; index++)
        {
            if (!entries.ContainsKey(required[index]))
                throw InvalidConfiguration("missing key: " + required[index]);
        }
    }

    private static bool ContainsName(string[] names, string candidate)
    {
        for (int index = 0; index < names.Length; index++)
        {
            if (String.Equals(names[index], candidate, StringComparison.Ordinal))
                return true;
        }
        return false;
    }

    private static void ValidatePassiveScalars(
        Dictionary<string, string> entries)
    {
        string runName = entries["RunName"];
        if (!IsSingleFilenameStem(runName) || runName != "passive-trace")
            throw InvalidConfiguration("RunName must be passive-trace");
        if (entries["ExpectedPassiveInputs"]
            != OracleProtocol.ExpectedInputCount.ToString(
                CultureInfo.InvariantCulture))
        {
            throw InvalidConfiguration("ExpectedPassiveInputs must be 3");
        }
        if (entries["MaxSettleFrames"]
            != OracleProtocol.MaxSettleFrames.ToString(
                CultureInfo.InvariantCulture))
        {
            throw InvalidConfiguration("MaxSettleFrames must be 600");
        }
        if (entries["MaxSettleSeconds"]
            != OracleProtocol.MaxSettleSeconds.ToString(
                CultureInfo.InvariantCulture))
        {
            throw InvalidConfiguration("MaxSettleSeconds must be 30");
        }
    }

    private static bool IsSingleFilenameStem(string value)
    {
        return !String.IsNullOrEmpty(value)
            && value != "."
            && value != ".."
            && value.IndexOf('/') < 0
            && value.IndexOf('\\') < 0;
    }

    private static OracleConfigurationException InvalidMode(string message)
    {
        return new OracleConfigurationException(
            "invalid_mode", new FormatException(message));
    }

    private static OracleConfigurationException InvalidConfiguration(
        string message)
    {
        return new OracleConfigurationException(
            "invalid_configuration", new FormatException(message));
    }

    private static OracleConfigurationException InvalidPath(string message)
    {
        return new OracleConfigurationException(
            "invalid_path", new IOException(message));
    }
}

internal sealed class PassiveConfiguration
{
    internal PassiveConfiguration(string outputDirectory, string runName,
        string saveDirectory, int expectedPassiveInputs,
        int maxSettleFrames, int maxSettleSeconds)
    {
        if (outputDirectory == null)
            throw new ArgumentNullException("outputDirectory");
        if (runName == null)
            throw new ArgumentNullException("runName");
        if (saveDirectory == null)
            throw new ArgumentNullException("saveDirectory");
        if (expectedPassiveInputs != OracleProtocol.ExpectedInputCount
            || maxSettleFrames != OracleProtocol.MaxSettleFrames
            || maxSettleSeconds != OracleProtocol.MaxSettleSeconds)
        {
            throw new ArgumentException("non-fixed passive limit");
        }
        OutputDirectory = outputDirectory;
        RunName = runName;
        SaveDirectory = saveDirectory;
        ExpectedPassiveInputs = expectedPassiveInputs;
        MaxSettleFrames = maxSettleFrames;
        MaxSettleSeconds = maxSettleSeconds;
    }

    internal string OutputDirectory { get; private set; }
    internal string RunName { get; private set; }
    internal string SaveDirectory { get; private set; }
    internal int ExpectedPassiveInputs { get; private set; }
    internal int MaxSettleFrames { get; private set; }
    internal int MaxSettleSeconds { get; private set; }
}
```

- [ ] **Step 4: Run GREEN and the net35 Core gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort config
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort config \
  --mode-off-fixture "$PWD/data/oracle/boot-probe.cfg"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Expected: all six selected config tests pass in both runs, including the
261-byte pinned fixture in the second run; stdout contains only the harness
success line, stderr is empty, and the net35 build has zero warnings/errors.

- [ ] **Step 5: Freeze Task 6.1 review evidence**

Record the Task 6.1 diff, this task body, design Sections 5.1 and 6, and both
framework outputs in the task report. The post-commit reviewer must return
explicit verdicts for exact Off/passive grammar, typed codes, byte identity,
fixed values, absence of writes, and code quality. Task 6.2 receives its own
fresh reviewer.

- [ ] **Step 6: Make only the Task 6.1 ledger commit**

```bash
git add oracle/plugin/Core/PassiveConfiguration.cs \
  oracle/plugin/tests/ConfigurationTests.cs \
  oracle/plugin/tests/Program.cs
git commit -m "feat: parse read-only oracle configuration"
```

#### Task 6.2: Prove stable physical paths on macOS

- [ ] **Step 1: Write the six failing physical-path tests**

**Files:**
- Create: `oracle/plugin/Core/PhysicalPath.cs`
- Create: `oracle/plugin/tests/PhysicalPathTests.cs`
- Modify: `oracle/plugin/Core/PassiveConfiguration.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes `IConfigurationPathResolver` and
  `OracleConfigurationException("invalid_path", inner)` from Task 6.1.
- Produces `PhysicalPath.ResolveExistingDirectory(string requested) ->
  string`, `ResolvePossiblyAbsent(string requested) -> PhysicalPathIdentity`,
  `RequireAbsentLeaf(string canonicalDirectory, string leafName) -> string`,
  and boundary-aware `Contains(string parent, string candidate) -> bool`.
- Produces injected overloads accepting `IPhysicalPathOperations` and one
  `Action betweenScans`. The hook runs exactly once after a complete first
  classification/`realpath` pass and before the second pass; production calls
  pass `null`.
- Produces `MacPhysicalPathOperations`, whose per-call instance-local one-byte
  buffer probes every existing component with `readlink`; `EINVAL` alone means
  nonsymlink, `ENOENT` means missing, and every other native failure maps to
  `invalid_path` at the `PhysicalPath` boundary.
- Produces `PhysicalConfigurationPathResolver`, which implements the Task 6.1
  seam, and the final exact overloads `OracleConfiguration.Parse(byte[])`,
  `Load(string, out byte[])`, and
  `Load(string, IConfigurationBytes, out byte[])`.
- Does not claim device/inode identity or detection of a real-directory
  replacement preserving the same canonical spelling. The outer probe owns
  that active-race proof.

Create `oracle/plugin/tests/PhysicalPathTests.cs` with this complete body. The
fake changes state only through the injected between-scan hook; it neither
touches the filesystem nor reproduces the production resolver algorithm:

```csharp
using System;

internal static class PhysicalPathTests
{
    internal static void Register(TestRegistry tests)
    {
        if (tests == null)
            throw new ArgumentNullException("tests");
        tests.Add("path", "containment uses component boundary",
            ContainmentUsesComponentBoundary);
        tests.Add("path", "existing paths resolve canonically",
            ExistingPathsResolveCanonically);
        tests.Add("path", "missing suffix is preserved",
            MissingSuffixIsPreserved);
        tests.Add("path", "lexical paths are strict",
            LexicalPathsAreStrict);
        tests.Add("path", "symlink and nondirectory are rejected",
            SymlinkAndNondirectoryAreRejected);
        tests.Add("path", "two scan drift is rejected",
            TwoScanDriftIsRejected);
    }

    private static void ContainmentUsesComponentBoundary()
    {
        ContainmentCase[] cases = new ContainmentCase[]
        {
            new ContainmentCase("/tmp/run", "/tmp/run", true),
            new ContainmentCase("/tmp/run", "/tmp/run/child", true),
            new ContainmentCase("/tmp/run", "/tmp/runner", false),
            new ContainmentCase("/tmp/run", "/tmp/other", false),
            new ContainmentCase("/", "/tmp/run", true)
        };
        for (int index = 0; index < cases.Length; index++)
        {
            Check.Equal(cases[index].Expected,
                PhysicalPath.Contains(cases[index].Parent,
                    cases[index].Candidate),
                "containment " + index.ToString());
        }
    }

    private static void ExistingPathsResolveCanonically()
    {
        ExistingCase[] cases = new ExistingCase[]
        {
            new ExistingCase("/", new string[] { "/" }, "/"),
            new ExistingCase("/root/leaf",
                new string[] { "/", "/root", "/root/leaf" },
                "/physical/leaf")
        };
        for (int index = 0; index < cases.Length; index++)
        {
            ExistingCase item = cases[index];
            FakePhysicalPathOperations operations =
                TestPhysicalOperations.Existing(item.ExistingPaths,
                    item.Requested, item.Canonical);
            Check.Equal(item.Canonical,
                PhysicalPath.ResolveExistingDirectory(
                    item.Requested, operations, null),
                "existing canonical " + item.Requested);
            PhysicalPathIdentity identity =
                PhysicalPath.ResolvePossiblyAbsent(
                    item.Requested, operations, null);
            Check.True(identity.Exists, "existing identity");
            Check.Equal(item.Canonical, identity.CanonicalPath,
                "existing identity canonical");
            Check.Equal(item.Canonical, identity.ExistingAncestor,
                "existing identity ancestor");
            Check.Sequence(new string[0], identity.MissingComponents,
                "existing missing suffix");
        }

        Check.Equal(
            "/tmp/é/雪",
            MacPhysicalPathOperations.DecodeNativePath(new byte[]
            {
                0x2f, 0x74, 0x6d, 0x70, 0x2f,
                0xc3, 0xa9, 0x2f, 0xe9, 0x9b, 0xaa
            }),
            "native path bytes decode as strict UTF-8");
        Check.Throws<System.IO.IOException>(delegate
        {
            MacPhysicalPathOperations.DecodeNativePath(
                new byte[] { 0xff });
        }, "invalid native path UTF-8");
    }

    private static void MissingSuffixIsPreserved()
    {
        MissingCase[] cases = new MissingCase[]
        {
            new MissingCase("/root/missing", "/root/missing", "/root",
                "/physical/root", "/physical/root/missing",
                new string[] { "missing" }),
            new MissingCase("/root/missing/child", "/root/missing", "/root",
                "/physical/root", "/physical/root/missing/child",
                new string[] { "missing", "child" })
        };
        for (int index = 0; index < cases.Length; index++)
        {
            MissingCase item = cases[index];
            PhysicalPathIdentity identity = PhysicalPath.ResolvePossiblyAbsent(
                item.Requested,
                TestPhysicalOperations.Missing(
                    new string[] { "/", "/root" }, item.FirstMissing,
                    item.ExistingLexical, item.CanonicalAncestor),
                null);
            Check.False(identity.Exists, "missing identity");
            Check.Equal(item.Canonical, identity.CanonicalPath,
                "missing canonical");
            Check.Equal(item.CanonicalAncestor, identity.ExistingAncestor,
                "missing ancestor");
            Check.Sequence(item.Missing, identity.MissingComponents,
                "ordered missing suffix");
        }

        FakePhysicalPathOperations absent =
            TestPhysicalOperations.TraceLeaf(
                PhysicalPathComponentKind.Missing,
                PhysicalPathComponentKind.Missing);
        Check.Equal(
            "/physical/output/passive-trace.ndjson",
            PhysicalPath.RequireAbsentLeaf(
                "/physical/output", "passive-trace.ndjson", absent,
                delegate { absent.Advance(); }),
            "stable absent trace leaf");

        FakePhysicalPathOperations occupied =
            TestPhysicalOperations.TraceLeaf(
                PhysicalPathComponentKind.Other,
                PhysicalPathComponentKind.Other);
        Check.Throws<TraceExistsException>(delegate
        {
            PhysicalPath.RequireAbsentLeaf(
                "/physical/output", "passive-trace.ndjson", occupied,
                delegate { occupied.Advance(); });
        }, "occupied trace leaf is typed");

        FakePhysicalPathOperations appeared =
            TestPhysicalOperations.TraceLeaf(
                PhysicalPathComponentKind.Missing,
                PhysicalPathComponentKind.Other);
        Check.Throws<TraceExistsException>(delegate
        {
            PhysicalPath.RequireAbsentLeaf(
                "/physical/output", "passive-trace.ndjson", appeared,
                delegate { appeared.Advance(); });
        }, "trace leaf appearance is typed");
    }

    private static void LexicalPathsAreStrict()
    {
        string[] invalid = new string[]
        {
            null, "", "relative", "//root", "/root//leaf",
            "/root/./leaf", "/root/../leaf", "/root/", "/root/\0leaf"
        };
        for (int index = 0; index < invalid.Length; index++)
        {
            string requested = invalid[index];
            AssertInvalidPath(delegate
            {
                PhysicalPath.ResolvePossiblyAbsent(requested,
                    TestPhysicalOperations.NeverCalled(), null);
            }, "possibly absent lexical " + index.ToString());
            AssertInvalidPath(delegate
            {
                PhysicalPath.ResolveExistingDirectory(requested,
                    TestPhysicalOperations.NeverCalled(), null);
            }, "existing lexical " + index.ToString());
        }
    }

    private static void SymlinkAndNondirectoryAreRejected()
    {
        RejectedKindCase[] cases = new RejectedKindCase[]
        {
            new RejectedKindCase("symlink ancestor", "/root",
                PhysicalPathComponentKind.SymbolicLink),
            new RejectedKindCase("nondirectory ancestor", "/root",
                PhysicalPathComponentKind.Other),
            new RejectedKindCase("symlink leaf", "/root/leaf",
                PhysicalPathComponentKind.SymbolicLink),
            new RejectedKindCase("nondirectory leaf", "/root/leaf",
                PhysicalPathComponentKind.Other)
        };
        for (int index = 0; index < cases.Length; index++)
        {
            RejectedKindCase item = cases[index];
            AssertInvalidPath(delegate
            {
                PhysicalPath.ResolvePossiblyAbsent("/root/leaf",
                    TestPhysicalOperations.RejectAt(item.Path, item.Kind),
                    null);
            }, item.Name);
        }
        AssertInvalidPath(delegate
        {
            PhysicalPath.ResolveExistingDirectory("/root/missing",
                TestPhysicalOperations.Missing(
                    new string[] { "/", "/root" }, "/root/missing",
                    "/root", "/physical/root"), null);
        }, "existing configured leaf required");
    }

    private static void TwoScanDriftIsRejected()
    {
        PathDrift[] cases = new PathDrift[]
        {
            PathDrift.Appearance,
            PathDrift.Disappearance,
            PathDrift.SymlinkStatus,
            PathDrift.CanonicalTarget
        };
        for (int index = 0; index < cases.Length; index++)
        {
            FakePhysicalPathOperations operations =
                TestPhysicalOperations.Drifting(cases[index]);
            AssertInvalidPath(delegate
            {
                PhysicalPath.ResolvePossiblyAbsent("/root/leaf", operations,
                    delegate { operations.Advance(); });
            }, "two-scan drift " + cases[index].ToString());
        }
    }

    private static void AssertInvalidPath(Action action, string message)
    {
        OracleConfigurationException error =
            Check.Throws<OracleConfigurationException>(action, message);
        Check.Equal("invalid_path", error.Code, message + " code");
    }

    private sealed class ContainmentCase
    {
        internal ContainmentCase(string parent, string candidate, bool expected)
        {
            Parent = parent;
            Candidate = candidate;
            Expected = expected;
        }
        internal string Parent;
        internal string Candidate;
        internal bool Expected;
    }

    private sealed class ExistingCase
    {
        internal ExistingCase(string requested, string[] existingPaths,
            string canonical)
        {
            Requested = requested;
            ExistingPaths = existingPaths;
            Canonical = canonical;
        }
        internal string Requested;
        internal string[] ExistingPaths;
        internal string Canonical;
    }

    private sealed class MissingCase
    {
        internal MissingCase(string requested, string firstMissing,
            string existingLexical, string canonicalAncestor,
            string canonical, string[] missing)
        {
            Requested = requested;
            FirstMissing = firstMissing;
            ExistingLexical = existingLexical;
            CanonicalAncestor = canonicalAncestor;
            Canonical = canonical;
            Missing = missing;
        }
        internal string Requested;
        internal string FirstMissing;
        internal string ExistingLexical;
        internal string CanonicalAncestor;
        internal string Canonical;
        internal string[] Missing;
    }

    private sealed class RejectedKindCase
    {
        internal RejectedKindCase(string name, string path,
            PhysicalPathComponentKind kind)
        {
            Name = name;
            Path = path;
            Kind = kind;
        }
        internal string Name;
        internal string Path;
        internal PhysicalPathComponentKind Kind;
    }
}

internal enum PathDrift
{
    Appearance,
    Disappearance,
    SymlinkStatus,
    CanonicalTarget
}

internal sealed class FakePhysicalPathOperations : IPhysicalPathOperations
{
    private readonly Func<int, string, PhysicalPathComponentKind> classify;
    private readonly Func<int, string, string> canonicalize;
    private int pass;

    internal FakePhysicalPathOperations(
        Func<int, string, PhysicalPathComponentKind> classify,
        Func<int, string, string> canonicalize)
    {
        if (classify == null)
            throw new ArgumentNullException("classify");
        if (canonicalize == null)
            throw new ArgumentNullException("canonicalize");
        this.classify = classify;
        this.canonicalize = canonicalize;
    }

    internal void Advance() { pass++; }

    public PhysicalPathComponentKind Classify(string path)
    {
        return classify(pass, path);
    }

    public string RealPath(string path)
    {
        return canonicalize(pass, path);
    }
}

internal static class TestPhysicalOperations
{
    internal static FakePhysicalPathOperations Existing(
        string[] existingPaths, string realPathInput, string canonical)
    {
        return new FakePhysicalPathOperations(delegate(int pass, string path)
        {
            for (int index = 0; index < existingPaths.Length; index++)
            {
                if (existingPaths[index] == path)
                    return PhysicalPathComponentKind.Directory;
            }
            throw new InvalidOperationException(
                "unexpected classification: " + path);
        }, delegate(int pass, string path)
        {
            if (path != realPathInput)
                throw new InvalidOperationException("unexpected realpath: " + path);
            return canonical;
        });
    }

    internal static FakePhysicalPathOperations Missing(
        string[] existingPaths, string firstMissing,
        string realPathInput, string canonicalAncestor)
    {
        return new FakePhysicalPathOperations(delegate(int pass, string path)
        {
            for (int index = 0; index < existingPaths.Length; index++)
            {
                if (existingPaths[index] == path)
                    return PhysicalPathComponentKind.Directory;
            }
            if (path == firstMissing)
                return PhysicalPathComponentKind.Missing;
            throw new InvalidOperationException(
                "scanner continued beyond first missing component: " + path);
        }, delegate(int pass, string path)
        {
            if (path != realPathInput)
                throw new InvalidOperationException("unexpected realpath: " + path);
            return canonicalAncestor;
        });
    }

    internal static FakePhysicalPathOperations RejectAt(string rejectedPath,
        PhysicalPathComponentKind kind)
    {
        return new FakePhysicalPathOperations(delegate(int pass, string path)
        {
            if (path == rejectedPath)
                return kind;
            if (path == "/" || path == "/root" || path == "/root/leaf")
                return PhysicalPathComponentKind.Directory;
            throw new InvalidOperationException(
                "unexpected classification: " + path);
        }, delegate(int pass, string path)
        {
            if (path == "/root/leaf")
                return "/physical/root/leaf";
            if (path == "/root")
                return "/physical/root";
            if (path == "/")
                return "/";
            throw new InvalidOperationException("unexpected realpath: " + path);
        });
    }

    internal static FakePhysicalPathOperations Drifting(PathDrift drift)
    {
        return new FakePhysicalPathOperations(delegate(int pass, string path)
        {
            if (path == "/" || path == "/root")
                return PhysicalPathComponentKind.Directory;
            if (path != "/root/leaf")
                throw new InvalidOperationException(
                    "unexpected classification: " + path);
            if (drift == PathDrift.Appearance)
            {
                return pass == 0
                    ? PhysicalPathComponentKind.Missing
                    : PhysicalPathComponentKind.Directory;
            }
            if (drift == PathDrift.Disappearance)
            {
                return pass == 0
                    ? PhysicalPathComponentKind.Directory
                    : PhysicalPathComponentKind.Missing;
            }
            if (drift == PathDrift.SymlinkStatus && pass != 0)
                return PhysicalPathComponentKind.SymbolicLink;
            return PhysicalPathComponentKind.Directory;
        }, delegate(int pass, string path)
        {
            if (path == "/")
                return "/";
            if (path == "/root")
                return "/physical/root";
            if (path == "/root/leaf")
            {
                if (drift == PathDrift.CanonicalTarget)
                {
                    return pass == 0
                        ? "/physical/first"
                        : "/physical/second";
                }
                return "/physical/root/leaf";
            }
            throw new InvalidOperationException("unexpected realpath: " + path);
        });
    }

    internal static FakePhysicalPathOperations NeverCalled()
    {
        return new FakePhysicalPathOperations(delegate(int pass, string path)
        {
            throw new InvalidOperationException("classification must not run");
        }, delegate(int pass, string path)
        {
            throw new InvalidOperationException("realpath must not run");
        });
    }

    internal static FakePhysicalPathOperations TraceLeaf(
        PhysicalPathComponentKind first,
        PhysicalPathComponentKind second)
    {
        return new FakePhysicalPathOperations(delegate(int pass, string path)
        {
            if (path == "/" || path == "/physical"
                || path == "/physical/output")
            {
                return PhysicalPathComponentKind.Directory;
            }
            if (path == "/physical/output/passive-trace.ndjson")
                return pass == 0 ? first : second;
            throw new InvalidOperationException(
                "unexpected classification: " + path);
        }, delegate(int pass, string path)
        {
            if (path == "/physical/output")
                return "/physical/output";
            throw new InvalidOperationException(
                "unexpected realpath: " + path);
        });
    }
}
```

- [ ] **Step 2: Register the exact cumulative manifest and run RED**

Add `PhysicalPathTests.Register(tests)` immediately after the configuration
registration. The cumulative registration and manifest block is exactly:

```csharp
ProtocolTests.Register(tests);
EncodingTests.Register(tests);
CaptureSignatureTests.Register(tests);
TraceSinkTests.Register(tests);
PassiveDriverTests.Register(tests);
ConfigurationTests.Register(tests, options);
PhysicalPathTests.Register(tests);
tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
{
    { "protocol", 4 },
    { "encoding", 5 },
    { "sink", 6 },
    { "driver-boundary", 2 },
    { "driver-initial", 8 },
    { "driver-input", 8 },
    { "driver-terminal", 6 },
    { "config", 6 },
    { "path", 6 }
});
```

Run:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort path
```

Expected: nonzero compilation failure naming `PhysicalPath`,
`IPhysicalPathOperations`, or `PhysicalPathIdentity`; a test-fixture or restore
failure is not the intended RED.

- [ ] **Step 3: Implement the macOS operations and stable two-pass resolver**

Create `oracle/plugin/Core/PhysicalPath.cs` with this complete C# 7.3/net35
body. The `readlink` probe buffer is instance-local to each call, so concurrent
verification cannot share a native write buffer:

```csharp
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

internal enum PhysicalPathComponentKind
{
    Missing = 0,
    Directory = 1,
    Other = 2,
    SymbolicLink = 3
}

internal interface IPhysicalPathOperations
{
    PhysicalPathComponentKind Classify(string path);
    string RealPath(string path);
}

internal sealed class PhysicalPathIdentity
{
    private readonly string[] missingComponents;

    internal PhysicalPathIdentity(string canonicalPath, bool exists,
        string existingAncestor, string[] missingComponents)
    {
        if (canonicalPath == null)
            throw new ArgumentNullException("canonicalPath");
        if (existingAncestor == null)
            throw new ArgumentNullException("existingAncestor");
        if (missingComponents == null)
            throw new ArgumentNullException("missingComponents");
        if (exists && missingComponents.Length != 0)
        {
            throw new ArgumentException(
                "existing path cannot have missing suffix",
                "missingComponents");
        }
        if (!exists && missingComponents.Length == 0)
        {
            throw new ArgumentException(
                "absent path must have a missing suffix",
                "missingComponents");
        }
        CanonicalPath = canonicalPath;
        Exists = exists;
        ExistingAncestor = existingAncestor;
        this.missingComponents = (string[])missingComponents.Clone();
    }

    internal string CanonicalPath { get; private set; }
    internal bool Exists { get; private set; }
    internal string ExistingAncestor { get; private set; }
    internal string[] MissingComponents
    {
        get { return (string[])missingComponents.Clone(); }
    }
}

internal sealed class PhysicalConfigurationPathResolver
    : IConfigurationPathResolver
{
    internal static readonly PhysicalConfigurationPathResolver Instance =
        new PhysicalConfigurationPathResolver();

    private PhysicalConfigurationPathResolver() { }

    public string ResolveExistingDirectory(string requested)
    {
        return PhysicalPath.ResolveExistingDirectory(requested);
    }

    public bool Contains(string parent, string candidate)
    {
        return PhysicalPath.Contains(parent, candidate);
    }
}

internal sealed class MacPhysicalPathOperations : IPhysicalPathOperations
{
    private const int Enoent = 2;
    private const int Einval = 22;

    internal static readonly MacPhysicalPathOperations Instance =
        new MacPhysicalPathOperations();

    private static readonly UTF8Encoding StrictUtf8 =
        new UTF8Encoding(false, true);

    private MacPhysicalPathOperations() { }

    public PhysicalPathComponentKind Classify(string path)
    {
        byte[] readLinkProbe = new byte[1];
        long result = readlink(path, readLinkProbe,
            new UIntPtr((uint)readLinkProbe.Length)).ToInt64();
        if (result >= 0)
            return PhysicalPathComponentKind.SymbolicLink;
        int errorNumber = Marshal.GetLastWin32Error();
        if (errorNumber == Enoent)
            return PhysicalPathComponentKind.Missing;
        if (errorNumber != Einval)
        {
            throw new IOException("readlink failed for " + path,
                new Win32Exception(errorNumber));
        }
        FileAttributes attributes = File.GetAttributes(path);
        return (attributes & FileAttributes.Directory) != 0
            ? PhysicalPathComponentKind.Directory
            : PhysicalPathComponentKind.Other;
    }

    public string RealPath(string path)
    {
        IntPtr pointer = realpath(path, IntPtr.Zero);
        if (pointer == IntPtr.Zero)
        {
            int errorNumber = Marshal.GetLastWin32Error();
            throw new IOException("realpath failed for " + path,
                new Win32Exception(errorNumber));
        }
        try
        {
            ulong nativeLength = strlen(pointer).ToUInt64();
            if (nativeLength > Int32.MaxValue)
                throw new IOException("realpath returned an oversized path");
            byte[] bytes = new byte[(int)nativeLength];
            if (bytes.Length != 0)
                Marshal.Copy(pointer, bytes, 0, bytes.Length);
            return DecodeNativePath(bytes);
        }
        finally
        {
            free(pointer);
        }
    }

    internal static string DecodeNativePath(byte[] bytes)
    {
        if (bytes == null)
            throw new ArgumentNullException("bytes");
        try
        {
            string value = StrictUtf8.GetString(bytes);
            if (String.IsNullOrEmpty(value) || value.IndexOf('\0') >= 0)
                throw new IOException("realpath returned an invalid path");
            return value;
        }
        catch (DecoderFallbackException error)
        {
            throw new IOException("realpath returned invalid UTF-8", error);
        }
    }

    [DllImport("/usr/lib/libSystem.B.dylib", SetLastError = true,
        CharSet = CharSet.Ansi)]
    private static extern IntPtr realpath(
        string path, IntPtr resolvedPath);

    [DllImport("/usr/lib/libSystem.B.dylib", SetLastError = true,
        CharSet = CharSet.Ansi)]
    private static extern IntPtr readlink(
        string path, byte[] buffer, UIntPtr bufferSize);

    [DllImport("/usr/lib/libSystem.B.dylib")]
    private static extern UIntPtr strlen(IntPtr value);

    [DllImport("/usr/lib/libSystem.B.dylib")]
    private static extern void free(IntPtr pointer);
}

internal static class PhysicalPath
{
    internal static string ResolveExistingDirectory(string requested)
    {
        return ResolveExistingDirectory(requested,
            MacPhysicalPathOperations.Instance, null);
    }

    internal static string ResolveExistingDirectory(string requested,
        IPhysicalPathOperations operations, Action betweenScans)
    {
        PhysicalPathIdentity identity = ResolveStable(
            requested, operations, betweenScans);
        if (!identity.Exists)
            throw InvalidPath("directory does not exist: " + requested, null);
        return identity.CanonicalPath;
    }

    internal static PhysicalPathIdentity ResolvePossiblyAbsent(
        string requested)
    {
        return ResolvePossiblyAbsent(requested,
            MacPhysicalPathOperations.Instance, null);
    }

    internal static PhysicalPathIdentity ResolvePossiblyAbsent(
        string requested,
        IPhysicalPathOperations operations,
        Action betweenScans)
    {
        return ResolveStable(requested, operations, betweenScans);
    }

    internal static string RequireAbsentLeaf(
        string canonicalDirectory,
        string leafName)
    {
        return RequireAbsentLeaf(canonicalDirectory, leafName,
            MacPhysicalPathOperations.Instance, null);
    }

    internal static string RequireAbsentLeaf(
        string canonicalDirectory,
        string leafName,
        IPhysicalPathOperations operations,
        Action betweenScans)
    {
        if (operations == null)
            throw new ArgumentNullException("operations");
        try
        {
            if (String.IsNullOrEmpty(leafName)
                || leafName == "."
                || leafName == ".."
                || leafName.IndexOf('/') >= 0
                || leafName.IndexOf('\\') >= 0
                || leafName.IndexOf('\0') >= 0)
            {
                throw InvalidPath("invalid absent-leaf name", null);
            }

            string[] components = ParseAbsolute(
                canonicalDirectory, "canonical directory");
            ScanSnapshot first = Scan(components, operations);
            string firstTarget = Append(first.CanonicalPath, leafName);
            PhysicalPathComponentKind firstKind =
                operations.Classify(firstTarget);
            if (betweenScans != null)
                betweenScans();
            ScanSnapshot second = Scan(components, operations);
            string secondTarget = Append(second.CanonicalPath, leafName);
            PhysicalPathComponentKind secondKind =
                operations.Classify(secondTarget);

            RequireSameObservation(first, second);
            if (!first.Exists
                || !String.Equals(first.CanonicalPath,
                    canonicalDirectory, StringComparison.Ordinal)
                || !String.Equals(firstTarget,
                    secondTarget, StringComparison.Ordinal))
            {
                throw InvalidPath(
                    "trace parent canonical identity changed", null);
            }
            if (firstKind != PhysicalPathComponentKind.Missing
                || secondKind != PhysicalPathComponentKind.Missing)
            {
                throw new TraceExistsException(
                    firstTarget,
                    new IOException("trace target is already occupied"));
            }
            return firstTarget;
        }
        catch (TraceExistsException)
        {
            throw;
        }
        catch (OracleConfigurationException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw InvalidPath("absent trace target proof failed", error);
        }
    }

    internal static bool Contains(string parent, string candidate)
    {
        if (parent == null)
            throw new ArgumentNullException("parent");
        if (candidate == null)
            throw new ArgumentNullException("candidate");
        if (String.Equals(parent, candidate, StringComparison.Ordinal))
            return true;
        string prefix = parent.EndsWith("/", StringComparison.Ordinal)
            ? parent
            : parent + "/";
        return candidate.StartsWith(prefix, StringComparison.Ordinal);
    }

    private static PhysicalPathIdentity ResolveStable(string requested,
        IPhysicalPathOperations operations, Action betweenScans)
    {
        if (operations == null)
            throw new ArgumentNullException("operations");
        try
        {
            string[] components = ParseAbsolute(requested, "requested path");
            ScanSnapshot first = Scan(components, operations);
            if (betweenScans != null)
                betweenScans();
            ScanSnapshot second = Scan(components, operations);
            RequireSameObservation(first, second);
            return new PhysicalPathIdentity(first.CanonicalPath, first.Exists,
                first.ExistingAncestor, first.MissingComponents);
        }
        catch (OracleConfigurationException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw InvalidPath("physical path proof failed", error);
        }
    }

    private static ScanSnapshot Scan(string[] components,
        IPhysicalPathOperations operations)
    {
        List<PhysicalPathComponentKind> observed =
            new List<PhysicalPathComponentKind>();
        PhysicalPathComponentKind rootKind = operations.Classify("/");
        observed.Add(rootKind);
        RequireDirectory("/", rootKind);

        string existingLexical = "/";
        int firstMissing = -1;
        for (int index = 0; index < components.Length; index++)
        {
            string candidate = Append(existingLexical, components[index]);
            PhysicalPathComponentKind kind = operations.Classify(candidate);
            observed.Add(kind);
            if (kind == PhysicalPathComponentKind.Missing)
            {
                firstMissing = index;
                break;
            }
            RequireDirectory(candidate, kind);
            existingLexical = candidate;
        }

        string canonicalAncestor = operations.RealPath(existingLexical);
        ParseAbsolute(canonicalAncestor, "realpath result");
        string[] missing;
        if (firstMissing < 0)
        {
            missing = new string[0];
        }
        else
        {
            missing = new string[components.Length - firstMissing];
            Array.Copy(components, firstMissing, missing, 0, missing.Length);
        }
        string canonical = canonicalAncestor;
        for (int index = 0; index < missing.Length; index++)
            canonical = Append(canonical, missing[index]);
        return new ScanSnapshot(firstMissing < 0, canonical,
            canonicalAncestor, missing, observed.ToArray());
    }

    private static void RequireDirectory(string path,
        PhysicalPathComponentKind kind)
    {
        if (kind == PhysicalPathComponentKind.Directory)
            return;
        if (kind == PhysicalPathComponentKind.SymbolicLink)
            throw InvalidPath("symbolic-link component: " + path, null);
        if (kind == PhysicalPathComponentKind.Other)
            throw InvalidPath("component is not a directory: " + path, null);
        if (kind == PhysicalPathComponentKind.Missing)
            throw InvalidPath("required component is missing: " + path, null);
        throw InvalidPath("unknown component classification: " + path, null);
    }

    private static void RequireSameObservation(
        ScanSnapshot first, ScanSnapshot second)
    {
        if (first.Exists != second.Exists
            || !String.Equals(first.CanonicalPath, second.CanonicalPath,
                StringComparison.Ordinal)
            || !String.Equals(first.ExistingAncestor,
                second.ExistingAncestor, StringComparison.Ordinal)
            || !Equal(first.MissingComponents, second.MissingComponents)
            || !Equal(first.ObservedKinds, second.ObservedKinds))
        {
            throw InvalidPath("physical path changed between scans", null);
        }
    }

    private static bool Equal(string[] left, string[] right)
    {
        if (left.Length != right.Length)
            return false;
        for (int index = 0; index < left.Length; index++)
        {
            if (!String.Equals(left[index], right[index],
                StringComparison.Ordinal))
            {
                return false;
            }
        }
        return true;
    }

    private static bool Equal(PhysicalPathComponentKind[] left,
        PhysicalPathComponentKind[] right)
    {
        if (left.Length != right.Length)
            return false;
        for (int index = 0; index < left.Length; index++)
        {
            if (left[index] != right[index])
                return false;
        }
        return true;
    }

    private static string[] ParseAbsolute(string path, string description)
    {
        if (path == null)
            throw InvalidPath(description + " is null", null);
        if (path.Length == 0)
            throw InvalidPath(description + " is empty", null);
        if (path.IndexOf('\0') >= 0)
            throw InvalidPath(description + " contains NUL", null);
        if (path[0] != '/')
            throw InvalidPath(description + " is not absolute", null);
        if (path == "/")
            return new string[0];
        string[] components = path.Substring(1).Split(new char[] { '/' });
        for (int index = 0; index < components.Length; index++)
        {
            string component = components[index];
            if (component.Length == 0
                || component == "."
                || component == "..")
            {
                throw InvalidPath(
                    description + " has an invalid component", null);
            }
        }
        return components;
    }

    private static string Append(string parent, string component)
    {
        return parent == "/" ? "/" + component : parent + "/" + component;
    }

    private static OracleConfigurationException InvalidPath(
        string message, Exception inner)
    {
        return new OracleConfigurationException("invalid_path",
            inner ?? new IOException(message));
    }

    private sealed class ScanSnapshot
    {
        internal ScanSnapshot(bool exists, string canonicalPath,
            string existingAncestor, string[] missingComponents,
            PhysicalPathComponentKind[] observedKinds)
        {
            Exists = exists;
            CanonicalPath = canonicalPath;
            ExistingAncestor = existingAncestor;
            MissingComponents = missingComponents;
            ObservedKinds = observedKinds;
        }
        internal bool Exists;
        internal string CanonicalPath;
        internal string ExistingAncestor;
        internal string[] MissingComponents;
        internal PhysicalPathComponentKind[] ObservedKinds;
    }
}
```

Every first pass classifies `/` plus every existing lexical component, stops
at the first `ENOENT`, and canonicalizes only the longest existing directory.
The second pass repeats those exact operations. A changed observed-kind array,
missing suffix, existing canonical ancestor, or complete canonical spelling is
`invalid_path`. An already-invalid first scan fails immediately. No `stat`,
inode, birth-time, or same-spelling replacement claim is added.

- [ ] **Step 4: Add the exact production configuration overloads**

Insert these complete overloads in `OracleConfiguration`; do not change the
Task 6.1 injected methods:

```csharp
internal static OracleConfiguration Load(
    string path,
    out byte[] originalBytes)
{
    return Load(path, new FileConfigurationBytes(),
        PhysicalConfigurationPathResolver.Instance, out originalBytes);
}

internal static OracleConfiguration Load(
    string path,
    IConfigurationBytes source,
    out byte[] originalBytes)
{
    return Load(path, source,
        PhysicalConfigurationPathResolver.Instance, out originalBytes);
}

internal static OracleConfiguration Parse(byte[] bytes)
{
    return Parse(bytes, PhysicalConfigurationPathResolver.Instance);
}
```

These overloads are the only production route. `Plugin` later calls the
two-argument `Load` exactly once; neither it nor another Core file calls
`File.ReadAllBytes`, `Config.Bind`, `Config.Save`, or any config mutation API.

- [ ] **Step 5: Run GREEN and the net35 Core gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort path
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort config
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Expected: all six path tests and all six retained config tests pass; each run
prints only the harness success line with empty stderr, and the net35 build has
zero warnings/errors.

- [ ] **Step 6: Freeze Task 6.2 review evidence**

Record the Task 6.2 diff, this task body, design Section 6, and all three
framework outputs in the task report. The post-commit reviewer must return
explicit verdicts for per-component `readlink`, allocated `realpath` cleanup,
strict UTF-8 native-path decoding, lexical missing-suffix handling, boundary
containment, exact standard config overloads, all four deterministic
between-scan changes, and code quality. Task 6.1 approval is not reusable.

- [ ] **Step 7: Make only the Task 6.2 ledger commit**

```bash
git add oracle/plugin/Core/PhysicalPath.cs \
  oracle/plugin/Core/PassiveConfiguration.cs \
  oracle/plugin/tests/PhysicalPathTests.cs \
  oracle/plugin/tests/Program.cs
git commit -m "feat: validate physical oracle paths"
```

### Track 7: Add the exact game adapter and metadata surface audit

**Files:**
- Create: `oracle/plugin/Core/GameObservation.cs`
- Create: `oracle/plugin/GameContract.cs`
- Create: `oracle/plugin/GameAdapter.cs`
- Create: `oracle/plugin/tests/GameObservationTests.cs`
- Create: `oracle/plugin/tests/AssemblySurfaceTests.cs`
- Modify: `oracle/plugin/tests/SsrOracle.UnitTests.csproj`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Produces: `GameContract.ValidatePassiveSurface() -> void` and preserves
  `GameContract.ValidateLegacySurface() -> void` for Mode-off.
- Pins the native `Direction` constants used by Core attribution exactly:
  `North=0`, `South=1`, `West=2`, `East=3`, and `None=8`, both in the
  external metadata characterization and passive runtime validation.
- Produces Unity-free `GameGateValues`, `CaptureValues`,
  `GameObservationPolicy.IsQuiescent(GameGateValues)`, and
  `CaptureMapping.Create(CaptureValues) -> CaptureRecord`; invalid mapping
  throws `CaptureException`.
- Produces exactly this game-facing method surface:

```text
internal void AuthenticateAndRedirectSavePath(string isolatedPath);
internal bool VerifySavePath();
internal bool TryGetState(Game game, out object stateReference);
internal bool IsQuiescent(Game game, GameState verifiedState);
internal bool MovementScheduled(GameState state);
internal bool CurrentMovementScheduled(Game game);
internal CaptureRecord Capture(GameState verifiedState);
```

  Quiescence and capture consume the exact `GameState` object authorized by
  `PassiveUpdateBoundary`; neither method rereads `game.gamestate`.
  `MovementScheduled(state)` is used only in the normal `ProcessInput` postfix
  and returns the immediate post-original `state.Moving()` result.
  `CurrentMovementScheduled(game)` is used only at the normal top-level
  `DoUndo` exit, rereads `game.gamestate`, and then delegates to
  `MovementScheduled`. Null/member/`Moving()` failures from either are wrapped
  in `CaptureException`.
- `GameAdapter.cs` is the only source file that reads game fields or Unity
  `GameObject` state and the only source that calls `Moving()` or
  `Save(false, false)`.
- Metadata-only harness mode requires `--cohort assembly` and one absolute
  Assembly-CSharp DLL path after `--assembly`.

#### Task 7.1: Prove the thirteen-gate and complete-capture policy

- [ ] **Step 1: Add all five Unity-free policy RED registrations**

Create `GameObservationTests.cs` exactly, register it in `Program.Main`, and
set the temporary manifest row to `observation=5`:

```csharp
using System;

internal static class GameObservationTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("observation", "all thirteen gates are required", EveryGateRequired);
        tests.Add("observation", "capture maps all twelve fields", MapsAllFields);
        tests.Add("observation", "three nullable strings normalize", NullableStringsNormalize);
        tests.Add("observation", "required values reject null", RequiredValuesRejectNull);
        tests.Add("observation", "numeric ranges reject negative", NegativeNumbersReject);
    }

    private static GameGateValues Gates(bool[] values)
    {
        return new GameGateValues(
            values[0], values[1], values[2], values[3], values[4],
            values[5], values[6], values[7], values[8], values[9],
            values[10], values[11], values[12]);
    }

    private static void EveryGateRequired()
    {
        bool[] all = new bool[13];
        for (int index = 0; index < all.Length; index++)
            all[index] = true;
        Check.True(GameObservationPolicy.IsQuiescent(Gates(all)), "all gates");
        for (int index = 0; index < all.Length; index++)
        {
            bool[] oneFalse = (bool[])all.Clone();
            oneFalse[index] = false;
            Check.False(GameObservationPolicy.IsQuiescent(Gates(oneFalse)),
                "false gate " + index);
        }
        Check.Throws<ArgumentNullException>(
            delegate { GameObservationPolicy.IsQuiescent(null); }, "null gates");
    }

    private static CaptureValues Values(
        string rawSave, string identity, string level, string lost, string display,
        int cooked, int movements, int pushes)
    {
        return new CaptureValues(
            rawSave, identity, level, true, false, true, false, lost, display,
            cooked, movements, pushes);
    }

    private static void MapsAllFields()
    {
        CaptureRecord value = CaptureMapping.Create(Values(
            "raw", "-17", "level", "lost", "display",
            Int32.MaxValue, Int32.MaxValue, Int32.MaxValue));
        Check.Equal("raw", value.RawSave, "raw save");
        Check.Equal("-17", value.StateIdentity, "identity");
        Check.Equal("level", value.Level, "level");
        Check.True(value.Overworld, "overworld");
        Check.False(value.Won, "won");
        Check.True(value.Returning, "returning");
        Check.False(value.HaveEverCookedAll, "cooked-all");
        Check.Equal("lost", value.LostReason, "lost reason");
        Check.Equal("display", value.DisplayName, "display name");
        Check.Equal(Int32.MaxValue, value.SausagesCooked, "sausages");
        Check.Equal(Int32.MaxValue, value.MovementCount, "movements");
        Check.Equal(Int32.MaxValue, value.PushesToTry, "pushes");
    }

    private static void NullableStringsNormalize()
    {
        CaptureRecord value = CaptureMapping.Create(Values(
            "raw", "0", null, null, null, 0, 0, 0));
        Check.Equal("", value.Level, "null level");
        Check.Equal("", value.LostReason, "null lost reason");
        Check.Equal("", value.DisplayName, "null display name");
    }

    private static void RequiredValuesRejectNull()
    {
        Check.Throws<CaptureException>(
            delegate { CaptureMapping.Create(null); }, "null values");
        Check.Throws<CaptureException>(
            delegate { CaptureMapping.Create(Values(
                null, "0", "", "", "", 0, 0, 0)); }, "null raw save");
        Check.Throws<CaptureException>(
            delegate { CaptureMapping.Create(Values(
                "raw", null, "", "", "", 0, 0, 0)); }, "null identity");
    }

    private static void NegativeNumbersReject()
    {
        int[,] values = new int[,] { { -1, 0, 0 }, { 0, -1, 0 }, { 0, 0, -1 } };
        for (int index = 0; index < values.GetLength(0); index++)
        {
            int row = index;
            Check.Throws<CaptureException>(
                delegate
                {
                    CaptureMapping.Create(Values(
                        "raw", "0", "", "", "",
                        values[row, 0], values[row, 1], values[row, 2]));
                },
                "negative capture integer " + index);
        }
    }
}
```

Run the selected cohort and require a compiler RED naming
`GameGateValues`, `GameObservationPolicy`, or `CaptureValues`.  A package or
SDK failure is not the intended RED.

- [ ] **Step 2: Run the observation-policy RED**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort observation
```

- [ ] **Step 3: Implement the complete Core-owned observation policy**

Create `Core/GameObservation.cs` with the following complete Core-owned value
and policy types.  The shared `CaptureException` was created in Task 4.1 and is
not redeclared here, so the linked net35 Core project compiles independently
of Unity and the game assembly.

```csharp
using System;

internal sealed class GameGateValues
{
    internal GameGateValues(
        bool hasGameAndState,
        bool hasPlayer,
        bool notMoving,
        bool noPushesToTry,
        bool noExitSequence,
        bool noEndingSequence,
        bool noBlueSpawnAnimation,
        bool notLeaving,
        bool notGameOver,
        bool notExploding,
        bool menuInactive,
        bool coffinsSettled,
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
        RawSave = rawSave;
        StateIdentity = stateIdentity;
        Level = level;
        Overworld = overworld;
        Won = won;
        Returning = returning;
        HaveEverCookedAll = haveEverCookedAll;
        LostReason = lostReason;
        DisplayName = displayName;
        SausagesCooked = sausagesCooked;
        MovementCount = movementCount;
        PushesToTry = pushesToTry;
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
    internal static bool IsQuiescent(GameGateValues values)
    {
        if (values == null)
            throw new ArgumentNullException("values");
        return values.HasGameAndState
            && values.HasPlayer
            && values.NotMoving
            && values.NoPushesToTry
            && values.NoExitSequence
            && values.NoEndingSequence
            && values.NoBlueSpawnAnimation
            && values.NotLeaving
            && values.NotGameOver
            && values.NotExploding
            && values.MenuInactive
            && values.CoffinsSettled
            && values.NoWorldSausageSpawns;
    }
}

internal static class CaptureMapping
{
    internal static CaptureRecord Create(CaptureValues values)
    {
        if (values == null)
            throw new CaptureException("missing capture values");
        if (values.RawSave == null)
            throw new CaptureException("raw save is null");
        if (values.StateIdentity == null)
            throw new CaptureException("state identity is null");
        try
        {
            return new CaptureRecord(
                values.RawSave,
                values.StateIdentity,
                values.Level ?? "",
                values.Overworld,
                values.Won,
                values.Returning,
                values.HaveEverCookedAll,
                values.LostReason ?? "",
                values.DisplayName ?? "",
                values.SausagesCooked,
                values.MovementCount,
                values.PushesToTry);
        }
        catch (Exception error)
        {
            throw new CaptureException("invalid capture values", error);
        }
    }
}
```

- [ ] **Step 4: Run GREEN and the net35 gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort observation
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Require the exact harness success line and a clean net35 build. Retain the
Task 7.1 diff and both outputs in the task report for post-commit review.

- [ ] **Step 5: Commit only the Task 7.1 observation-policy slice**

```bash
git add oracle/plugin/Core/GameObservation.cs \
  oracle/plugin/tests/GameObservationTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: map passive observations"
```

#### Task 7.2: Pin the legacy and passive game metadata contract

- [ ] **Step 1: Register the missing-type metadata RED**

First add `AssemblySurfaceTests.Register(tests, options)` to `Program.Main`
without creating `AssemblySurfaceTests.cs`. Set the cumulative manifest row to
`assembly=4`; it remains four through the rest of the plan.

- [ ] **Step 2: Run RED for the absent metadata test surface**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort assembly \
  --assembly "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
```

Require a compiler error naming `AssemblySurfaceTests`; an SDK, asset, or
external-DLL failure is not the intended RED.

- [ ] **Step 3: Implement the external metadata reader and exact contract**

Create the test file and use `PEReader` and `MetadataReader` from
`System.Reflection.Metadata`; do not load Unity. Verify exact declaring type,
visibility, static/instance flag, return type, and parameter sequence for all
ten methods—`Update`,
`DoPlayerInput`, `Playerinputstring`, `ProcessInput`, `DoUndo`,
`RestorePrevState`, `DoRestart`, `SetGameState`, `Moving`, and `Save`—and every
required field in design section 8.1. Verify the reviewed Assembly-CSharp
SHA-256 first. Include negative synthetic assertions for wrong overload,
static flag, field type, and visibility. `HarnessOptions` requires one value
after `--assembly` and rejects duplicate or unknown arguments.
Create `AssemblySurfaceTests.cs` with the complete body below.  The decoder is
final at this point and is reused by the later plugin-artifact tests; it never
calls `Assembly.Load`, `Type.GetType`, or another executable-load API.  Task
7.2 registers and passes all four `assembly` tests against the reviewed game
DLL.  Task 7.3 adds the first `plugin` registration; Tasks 9.2-9.4 make the
exact cumulative changes shown in those tasks.  The final block has exactly
four `assembly` and six `plugin` registrations, all under this single
`Register(tests, options)` method.

```csharp
using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Security.Cryptography;
using System.Text;

internal sealed class ParameterShape
{
    internal ParameterShape(string type, string name, bool isOut)
    {
        Type = type;
        Name = name;
        IsOut = isOut;
    }

    internal string Type;
    internal string Name;
    internal bool IsOut;
}

internal sealed class MethodShape
{
    internal MethodShape(
        MethodDefinitionHandle handle,
        string owner,
        string name,
        string visibility,
        bool isStatic,
        string returnType,
        ParameterShape[] parameters)
    {
        Handle = handle;
        Owner = owner;
        Name = name;
        Visibility = visibility;
        IsStatic = isStatic;
        ReturnType = returnType;
        Parameters = parameters;
    }

    internal MethodDefinitionHandle Handle;
    internal string Owner;
    internal string Name;
    internal string Visibility;
    internal bool IsStatic;
    internal string ReturnType;
    internal ParameterShape[] Parameters;
}

internal sealed class FieldShape
{
    internal FieldShape(
        string owner,
        string name,
        string visibility,
        bool isStatic,
        string fieldType)
    {
        Owner = owner;
        Name = name;
        Visibility = visibility;
        IsStatic = isStatic;
        FieldType = fieldType;
    }

    internal string Owner;
    internal string Name;
    internal string Visibility;
    internal bool IsStatic;
    internal string FieldType;
}

internal sealed class MethodCall
{
    internal MethodCall(
        int offset,
        string owner,
        string name,
        string returnType,
        string[] parameters)
    {
        Offset = offset;
        Owner = owner;
        Name = name;
        ReturnType = returnType;
        Parameters = parameters;
    }

    internal int Offset;
    internal string Owner;
    internal string Name;
    internal string ReturnType;
    internal string[] Parameters;

    internal string Key
    {
        get
        {
            return Owner + "::" + Name + "("
                + String.Join(",", Parameters) + ")->" + ReturnType;
        }
    }
}

internal sealed class IlInstruction
{
    internal int Offset;
    internal OpCode OpCode;
    internal int Token;
    internal bool HasToken;
    internal int Int32Value;
    internal bool HasInt32;
}

internal sealed class MetadataTypeProvider :
    ISignatureTypeProvider<string, object>,
    ICustomAttributeTypeProvider<string>
{
    public string GetArrayType(string elementType, ArrayShape shape)
    {
        return elementType + "[" + new string(',', shape.Rank - 1) + "]";
    }

    public string GetByReferenceType(string elementType)
    {
        return elementType + "&";
    }

    public string GetFunctionPointerType(MethodSignature<string> signature)
    {
        return "methodptr(" + String.Join(",", signature.ParameterTypes)
            + ")->" + signature.ReturnType;
    }

    public string GetGenericInstantiation(
        string genericType,
        ImmutableArray<string> typeArguments)
    {
        int tick = genericType.LastIndexOf('`');
        if (tick >= 0)
            genericType = genericType.Substring(0, tick);
        return genericType + "<" + String.Join(",", typeArguments) + ">";
    }

    public string GetGenericMethodParameter(object genericContext, int index)
    {
        return "!!" + index.ToString(CultureInfo.InvariantCulture);
    }

    public string GetGenericTypeParameter(object genericContext, int index)
    {
        return "!" + index.ToString(CultureInfo.InvariantCulture);
    }

    public string GetModifiedType(
        string modifier,
        string unmodifiedType,
        bool isRequired)
    {
        return unmodifiedType;
    }

    public string GetPinnedType(string elementType)
    {
        return elementType;
    }

    public string GetPointerType(string elementType)
    {
        return elementType + "*";
    }

    public string GetPrimitiveType(PrimitiveTypeCode typeCode)
    {
        switch (typeCode)
        {
            case PrimitiveTypeCode.Boolean: return "System.Boolean";
            case PrimitiveTypeCode.Byte: return "System.Byte";
            case PrimitiveTypeCode.Char: return "System.Char";
            case PrimitiveTypeCode.Double: return "System.Double";
            case PrimitiveTypeCode.Int16: return "System.Int16";
            case PrimitiveTypeCode.Int32: return "System.Int32";
            case PrimitiveTypeCode.Int64: return "System.Int64";
            case PrimitiveTypeCode.IntPtr: return "System.IntPtr";
            case PrimitiveTypeCode.Object: return "System.Object";
            case PrimitiveTypeCode.SByte: return "System.SByte";
            case PrimitiveTypeCode.Single: return "System.Single";
            case PrimitiveTypeCode.String: return "System.String";
            case PrimitiveTypeCode.TypedReference: return "System.TypedReference";
            case PrimitiveTypeCode.UInt16: return "System.UInt16";
            case PrimitiveTypeCode.UInt32: return "System.UInt32";
            case PrimitiveTypeCode.UInt64: return "System.UInt64";
            case PrimitiveTypeCode.UIntPtr: return "System.UIntPtr";
            case PrimitiveTypeCode.Void: return "System.Void";
            default:
                throw new InvalidOperationException(
                    "unsupported primitive type: " + typeCode.ToString());
        }
    }

    public string GetSZArrayType(string elementType)
    {
        return elementType + "[]";
    }

    public string GetTypeFromDefinition(
        MetadataReader reader,
        TypeDefinitionHandle handle,
        byte rawTypeKind)
    {
        return MetadataImage.DefinitionName(reader, handle);
    }

    public string GetTypeFromReference(
        MetadataReader reader,
        TypeReferenceHandle handle,
        byte rawTypeKind)
    {
        return MetadataImage.ReferenceName(reader, handle);
    }

    public string GetTypeFromSpecification(
        MetadataReader reader,
        object genericContext,
        TypeSpecificationHandle handle,
        byte rawTypeKind)
    {
        return reader.GetTypeSpecification(handle).DecodeSignature(
            this, genericContext);
    }

    public string GetSystemType()
    {
        return "System.Type";
    }

    public bool IsSystemType(string type)
    {
        return type == "System.Type";
    }

    public string GetTypeFromSerializedName(string name)
    {
        return name;
    }

    public PrimitiveTypeCode GetUnderlyingEnumType(string type)
    {
        return PrimitiveTypeCode.Int32;
    }
}

internal sealed class MetadataImage : IDisposable
{
    private static readonly Dictionary<ushort, OpCode> Opcodes = BuildOpcodes();
    private readonly FileStream stream;
    private readonly PEReader pe;
    private readonly MetadataTypeProvider provider = new MetadataTypeProvider();

    private MetadataImage(FileStream stream, PEReader pe)
    {
        this.stream = stream;
        this.pe = pe;
        Reader = pe.GetMetadataReader();
    }

    internal MetadataReader Reader { get; private set; }
    internal PEHeaders Headers { get { return pe.PEHeaders; } }

    internal static MetadataImage Open(string path, string option)
    {
        if (String.IsNullOrEmpty(path))
            throw new ArgumentException(option + " is required");
        if (!Path.IsPathRooted(path))
            throw new ArgumentException(option + " must be absolute");
        FileStream stream = File.OpenRead(path);
        try
        {
            PEReader pe = new PEReader(stream, PEStreamOptions.LeaveOpen);
            if (!pe.HasMetadata)
                throw new BadImageFormatException("managed metadata is required");
            return new MetadataImage(stream, pe);
        }
        catch
        {
            stream.Dispose();
            throw;
        }
    }

    public void Dispose()
    {
        pe.Dispose();
        stream.Dispose();
    }

    internal static string DefinitionName(
        MetadataReader reader,
        TypeDefinitionHandle handle)
    {
        TypeDefinition definition = reader.GetTypeDefinition(handle);
        string name = reader.GetString(definition.Name);
        TypeDefinitionHandle parent = definition.GetDeclaringType();
        if (!parent.IsNil)
            return DefinitionName(reader, parent) + "." + name;
        string typeNamespace = reader.GetString(definition.Namespace);
        return typeNamespace.Length == 0 ? name : typeNamespace + "." + name;
    }

    internal static string ReferenceName(
        MetadataReader reader,
        TypeReferenceHandle handle)
    {
        TypeReference reference = reader.GetTypeReference(handle);
        string name = reader.GetString(reference.Name);
        if (reference.ResolutionScope.Kind == HandleKind.TypeReference)
        {
            return ReferenceName(
                reader, (TypeReferenceHandle)reference.ResolutionScope)
                + "." + name;
        }
        string typeNamespace = reader.GetString(reference.Namespace);
        return typeNamespace.Length == 0 ? name : typeNamespace + "." + name;
    }

    internal string TypeName(EntityHandle handle)
    {
        if (handle.Kind == HandleKind.TypeDefinition)
            return DefinitionName(Reader, (TypeDefinitionHandle)handle);
        if (handle.Kind == HandleKind.TypeReference)
            return ReferenceName(Reader, (TypeReferenceHandle)handle);
        if (handle.Kind == HandleKind.TypeSpecification)
        {
            return Reader.GetTypeSpecification(
                (TypeSpecificationHandle)handle).DecodeSignature(
                    provider, null);
        }
        throw new InvalidOperationException(
            "unsupported type handle: " + handle.Kind.ToString());
    }

    internal TypeDefinitionHandle FindType(string fullName)
    {
        TypeDefinitionHandle found = default(TypeDefinitionHandle);
        foreach (TypeDefinitionHandle handle in Reader.TypeDefinitions)
        {
            if (DefinitionName(Reader, handle) != fullName)
                continue;
            if (!found.IsNil)
                throw new InvalidOperationException("duplicate type: " + fullName);
            found = handle;
        }
        if (found.IsNil)
            throw new InvalidOperationException("missing type: " + fullName);
        return found;
    }

    internal MethodShape[] Methods(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        List<MethodShape> values = new List<MethodShape>();
        foreach (MethodDefinitionHandle handle in definition.GetMethods())
        {
            MethodDefinition method = Reader.GetMethodDefinition(handle);
            if (Reader.GetString(method.Name) != name)
                continue;
            MethodSignature<string> signature = method.DecodeSignature(
                provider, null);
            ParameterShape[] parameters = new ParameterShape[
                signature.ParameterTypes.Length];
            string[] names = new string[parameters.Length];
            bool[] outs = new bool[parameters.Length];
            foreach (ParameterHandle parameterHandle in method.GetParameters())
            {
                Parameter parameter = Reader.GetParameter(parameterHandle);
                int sequence = parameter.SequenceNumber;
                if (sequence <= 0 || sequence > parameters.Length)
                    continue;
                names[sequence - 1] = Reader.GetString(parameter.Name);
                outs[sequence - 1] =
                    (parameter.Attributes & ParameterAttributes.Out) != 0;
            }
            for (int index = 0; index < parameters.Length; index++)
            {
                parameters[index] = new ParameterShape(
                    signature.ParameterTypes[index], names[index] ?? "", outs[index]);
            }
            values.Add(new MethodShape(
                handle,
                owner,
                name,
                MethodVisibility(method.Attributes),
                (method.Attributes & MethodAttributes.Static) != 0,
                signature.ReturnType,
                parameters));
        }
        return values.ToArray();
    }

    internal FieldShape[] Fields(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        List<FieldShape> values = new List<FieldShape>();
        foreach (FieldDefinitionHandle handle in definition.GetFields())
        {
            FieldDefinition field = Reader.GetFieldDefinition(handle);
            if (Reader.GetString(field.Name) != name)
                continue;
            values.Add(new FieldShape(
                owner,
                name,
                FieldVisibility(field.Attributes),
                (field.Attributes & FieldAttributes.Static) != 0,
                field.DecodeSignature(provider, null)));
        }
        return values.ToArray();
    }

    internal MethodShape RequireMethod(
        string owner,
        string name,
        string visibility,
        bool isStatic,
        string returnType,
        ParameterShape[] parameters)
    {
        return AssemblySurfaceTests.RequireMethodShape(
            Methods(owner, name),
            new MethodShape(
                default(MethodDefinitionHandle), owner, name, visibility,
                isStatic, returnType, parameters));
    }

    internal FieldShape RequireField(
        string owner,
        string name,
        string visibility,
        bool isStatic,
        string fieldType)
    {
        return AssemblySurfaceTests.RequireFieldShape(
            Fields(owner, name),
            new FieldShape(owner, name, visibility, isStatic, fieldType));
    }

    internal int RequireInt32EnumConstant(string owner, string name)
    {
        TypeDefinition definition = Reader.GetTypeDefinition(FindType(owner));
        FieldDefinitionHandle found = default(FieldDefinitionHandle);
        foreach (FieldDefinitionHandle handle in definition.GetFields())
        {
            FieldDefinition field = Reader.GetFieldDefinition(handle);
            if (Reader.GetString(field.Name) != name)
                continue;
            if (!found.IsNil)
                throw new InvalidOperationException(
                    "duplicate enum constant: " + owner + "::" + name);
            found = handle;
        }
        if (found.IsNil)
            throw new InvalidOperationException(
                "missing enum constant: " + owner + "::" + name);

        FieldDefinition value = Reader.GetFieldDefinition(found);
        FieldAttributes required = FieldAttributes.Public
            | FieldAttributes.Static
            | FieldAttributes.Literal
            | FieldAttributes.HasDefault;
        if ((value.Attributes & required) != required
            || value.DecodeSignature(provider, null) != owner)
        {
            throw new InvalidOperationException(
                "invalid enum constant shape: " + owner + "::" + name);
        }
        ConstantHandle constantHandle = value.GetDefaultValue();
        if (constantHandle.IsNil)
            throw new InvalidOperationException(
                "missing enum constant value: " + owner + "::" + name);
        Constant constant = Reader.GetConstant(constantHandle);
        if (constant.TypeCode != ConstantTypeCode.Int32)
            throw new InvalidOperationException(
                "enum constant is not Int32: " + owner + "::" + name);
        BlobReader bytes = Reader.GetBlobReader(constant.Value);
        int result = bytes.ReadInt32();
        if (bytes.RemainingBytes != 0)
            throw new BadImageFormatException("trailing enum constant bytes");
        return result;
    }

    internal bool HasCustomAttribute(
        CustomAttributeHandleCollection attributes,
        string expectedType)
    {
        foreach (CustomAttributeHandle handle in attributes)
        {
            if (CustomAttributeType(Reader.GetCustomAttribute(handle))
                == expectedType)
                return true;
        }
        return false;
    }

    internal CustomAttribute RequireCustomAttribute(
        CustomAttributeHandleCollection attributes,
        string expectedType)
    {
        CustomAttributeHandle found = default(CustomAttributeHandle);
        foreach (CustomAttributeHandle handle in attributes)
        {
            if (CustomAttributeType(Reader.GetCustomAttribute(handle))
                != expectedType)
                continue;
            if (!found.IsNil)
                throw new InvalidOperationException(
                    "duplicate attribute: " + expectedType);
            found = handle;
        }
        if (found.IsNil)
            throw new InvalidOperationException("missing attribute: " + expectedType);
        return Reader.GetCustomAttribute(found);
    }

    internal CustomAttributeValue<string> DecodeAttribute(CustomAttribute value)
    {
        return value.DecodeValue(provider);
    }

    private string CustomAttributeType(CustomAttribute attribute)
    {
        EntityHandle constructor = attribute.Constructor;
        if (constructor.Kind == HandleKind.MemberReference)
        {
            MemberReference member = Reader.GetMemberReference(
                (MemberReferenceHandle)constructor);
            return TypeName((EntityHandle)member.Parent);
        }
        if (constructor.Kind == HandleKind.MethodDefinition)
        {
            MethodDefinition method = Reader.GetMethodDefinition(
                (MethodDefinitionHandle)constructor);
            return DefinitionName(Reader, method.GetDeclaringType());
        }
        throw new InvalidOperationException("unsupported attribute constructor");
    }

    internal List<IlInstruction> Instructions(MethodShape method)
    {
        MethodDefinition definition = Reader.GetMethodDefinition(method.Handle);
        if (definition.RelativeVirtualAddress == 0)
            throw new InvalidOperationException("method has no IL: " + method.Name);
        ImmutableArray<byte> bytes = pe.GetMethodBody(
            definition.RelativeVirtualAddress).GetILContent();
        List<IlInstruction> instructions = new List<IlInstruction>();
        int offset = 0;
        while (offset < bytes.Length)
        {
            int instructionOffset = offset;
            ushort value = bytes[offset++];
            if (value == 0xfe)
            {
                RequireBytes(bytes, offset, 1);
                value = (ushort)(0xfe00 | bytes[offset++]);
            }
            OpCode opCode;
            if (!Opcodes.TryGetValue(value, out opCode))
                throw new BadImageFormatException("unknown IL opcode");
            IlInstruction instruction = new IlInstruction
            {
                Offset = instructionOffset,
                OpCode = opCode
            };
            int size = OperandSize(bytes, offset, opCode.OperandType);
            RequireBytes(bytes, offset, size);
            if (opCode.OperandType == OperandType.ShortInlineI)
            {
                instruction.HasInt32 = true;
                instruction.Int32Value = unchecked((sbyte)bytes[offset]);
            }
            else if (opCode.OperandType == OperandType.InlineI)
            {
                instruction.HasInt32 = true;
                instruction.Int32Value = ReadInt32(bytes, offset);
            }
            else if (opCode.OperandType == OperandType.InlineField
                || opCode.OperandType == OperandType.InlineMethod
                || opCode.OperandType == OperandType.InlineSig
                || opCode.OperandType == OperandType.InlineString
                || opCode.OperandType == OperandType.InlineTok
                || opCode.OperandType == OperandType.InlineType)
            {
                instruction.HasToken = true;
                instruction.Token = ReadInt32(bytes, offset);
            }
            instructions.Add(instruction);
            offset += size;
        }
        return instructions;
    }

    internal List<MethodCall> Calls(MethodShape method)
    {
        List<MethodCall> calls = new List<MethodCall>();
        List<IlInstruction> instructions = Instructions(method);
        for (int index = 0; index < instructions.Count; index++)
        {
            IlInstruction instruction = instructions[index];
            short opcode = instruction.OpCode.Value;
            if (!instruction.HasToken
                || (opcode != OpCodes.Call.Value
                    && opcode != OpCodes.Callvirt.Value
                    && opcode != OpCodes.Newobj.Value))
                continue;
            calls.Add(ResolveCall(instruction.Offset, instruction.Token));
        }
        return calls;
    }

    internal string UserString(IlInstruction instruction)
    {
        if (!instruction.HasToken
            || instruction.OpCode.Value != OpCodes.Ldstr.Value)
            throw new ArgumentException("instruction is not ldstr");
        return Reader.GetUserString(
            MetadataTokens.UserStringHandle(instruction.Token & 0x00ffffff));
    }

    internal string TypeToken(IlInstruction instruction)
    {
        if (!instruction.HasToken
            || instruction.OpCode.Value != OpCodes.Ldtoken.Value)
            throw new ArgumentException("instruction is not ldtoken");
        return TypeName(MetadataTokens.EntityHandle(instruction.Token));
    }

    internal bool TryConstant(IlInstruction instruction, out int value)
    {
        value = 0;
        short opcode = instruction.OpCode.Value;
        if (opcode == OpCodes.Ldc_I4_M1.Value) value = -1;
        else if (opcode == OpCodes.Ldc_I4_0.Value) value = 0;
        else if (opcode == OpCodes.Ldc_I4_1.Value) value = 1;
        else if (opcode == OpCodes.Ldc_I4_2.Value) value = 2;
        else if (opcode == OpCodes.Ldc_I4_3.Value) value = 3;
        else if (opcode == OpCodes.Ldc_I4_4.Value) value = 4;
        else if (opcode == OpCodes.Ldc_I4_5.Value) value = 5;
        else if (opcode == OpCodes.Ldc_I4_6.Value) value = 6;
        else if (opcode == OpCodes.Ldc_I4_7.Value) value = 7;
        else if (opcode == OpCodes.Ldc_I4_8.Value) value = 8;
        else if (instruction.HasInt32) value = instruction.Int32Value;
        else return false;
        return true;
    }

    internal bool HasCatch(MethodShape method, string exceptionType)
    {
        MethodDefinition definition = Reader.GetMethodDefinition(method.Handle);
        MethodBodyBlock body = pe.GetMethodBody(definition.RelativeVirtualAddress);
        foreach (ExceptionRegion region in body.ExceptionRegions)
        {
            if (region.Kind == ExceptionRegionKind.Catch
                && TypeName(region.CatchType) == exceptionType)
                return true;
        }
        return false;
    }

    private MethodCall ResolveCall(int offset, int token)
    {
        EntityHandle handle = MetadataTokens.EntityHandle(token);
        if (handle.Kind == HandleKind.MethodSpecification)
        {
            MethodSpecification specification = Reader.GetMethodSpecification(
                (MethodSpecificationHandle)handle);
            return ResolveCall(offset, MetadataTokens.GetToken(specification.Method));
        }
        if (handle.Kind == HandleKind.MethodDefinition)
        {
            MethodDefinition method = Reader.GetMethodDefinition(
                (MethodDefinitionHandle)handle);
            MethodSignature<string> signature = method.DecodeSignature(provider, null);
            return new MethodCall(
                offset,
                DefinitionName(Reader, method.GetDeclaringType()),
                Reader.GetString(method.Name),
                signature.ReturnType,
                Copy(signature.ParameterTypes));
        }
        if (handle.Kind == HandleKind.MemberReference)
        {
            MemberReference member = Reader.GetMemberReference(
                (MemberReferenceHandle)handle);
            MethodSignature<string> signature = member.DecodeMethodSignature(
                provider, null);
            return new MethodCall(
                offset,
                TypeName((EntityHandle)member.Parent),
                Reader.GetString(member.Name),
                signature.ReturnType,
                Copy(signature.ParameterTypes));
        }
        throw new BadImageFormatException("call operand is not a method");
    }

    private static string[] Copy(ImmutableArray<string> values)
    {
        string[] copy = new string[values.Length];
        for (int index = 0; index < values.Length; index++)
            copy[index] = values[index];
        return copy;
    }

    private static string MethodVisibility(MethodAttributes attributes)
    {
        MethodAttributes access = attributes & MethodAttributes.MemberAccessMask;
        if (access == MethodAttributes.Public) return "public";
        if (access == MethodAttributes.Private) return "private";
        if (access == MethodAttributes.Assembly) return "assembly";
        if (access == MethodAttributes.Family) return "family";
        if (access == MethodAttributes.FamORAssem) return "family-or-assembly";
        if (access == MethodAttributes.FamANDAssem) return "family-and-assembly";
        return "private-scope";
    }

    private static string FieldVisibility(FieldAttributes attributes)
    {
        FieldAttributes access = attributes & FieldAttributes.FieldAccessMask;
        if (access == FieldAttributes.Public) return "public";
        if (access == FieldAttributes.Private) return "private";
        if (access == FieldAttributes.Assembly) return "assembly";
        if (access == FieldAttributes.Family) return "family";
        if (access == FieldAttributes.FamORAssem) return "family-or-assembly";
        if (access == FieldAttributes.FamANDAssem) return "family-and-assembly";
        return "private-scope";
    }

    private static Dictionary<ushort, OpCode> BuildOpcodes()
    {
        Dictionary<ushort, OpCode> values = new Dictionary<ushort, OpCode>();
        FieldInfo[] fields = typeof(OpCodes).GetFields(
            BindingFlags.Public | BindingFlags.Static);
        for (int index = 0; index < fields.Length; index++)
        {
            if (fields[index].FieldType != typeof(OpCode))
                continue;
            OpCode opCode = (OpCode)fields[index].GetValue(null);
            values[unchecked((ushort)opCode.Value)] = opCode;
        }
        return values;
    }

    private static int OperandSize(
        ImmutableArray<byte> bytes,
        int offset,
        OperandType operandType)
    {
        switch (operandType)
        {
            case OperandType.InlineNone: return 0;
            case OperandType.ShortInlineBrTarget:
            case OperandType.ShortInlineI:
            case OperandType.ShortInlineVar: return 1;
            case OperandType.InlineVar: return 2;
            case OperandType.InlineBrTarget:
            case OperandType.InlineField:
            case OperandType.InlineI:
            case OperandType.InlineMethod:
            case OperandType.InlineSig:
            case OperandType.InlineString:
            case OperandType.InlineTok:
            case OperandType.InlineType:
            case OperandType.ShortInlineR: return 4;
            case OperandType.InlineI8:
            case OperandType.InlineR: return 8;
            case OperandType.InlineSwitch:
                RequireBytes(bytes, offset, 4);
                int count = ReadInt32(bytes, offset);
                if (count < 0)
                    throw new BadImageFormatException("negative switch size");
                return checked(4 + count * 4);
            default:
                throw new BadImageFormatException(
                    "unsupported IL operand: " + operandType.ToString());
        }
    }

    private static int ReadInt32(ImmutableArray<byte> bytes, int offset)
    {
        RequireBytes(bytes, offset, 4);
        return bytes[offset]
            | (bytes[offset + 1] << 8)
            | (bytes[offset + 2] << 16)
            | (bytes[offset + 3] << 24);
    }

    private static void RequireBytes(
        ImmutableArray<byte> bytes,
        int offset,
        int count)
    {
        if (offset < 0 || count < 0 || offset > bytes.Length - count)
            throw new BadImageFormatException("truncated IL");
    }
}

internal static class AssemblySurfaceTests
{
    internal static void Register(TestRegistry tests, HarnessOptions options)
    {
        tests.Add("assembly", "pinned Assembly-CSharp hash",
            delegate { PinnedHash(options.AssemblyPath); });
        tests.Add("assembly", "exact ten observed methods",
            delegate { ExactObservedMethods(options.AssemblyPath); });
        tests.Add("assembly", "exact required game fields",
            delegate { ExactRequiredFields(options.AssemblyPath); });
        tests.Add("assembly", "metadata matcher rejects near misses",
            SyntheticMatcherRejectsNearMisses);
    }

    private static ParameterShape P(string type)
    {
        return new ParameterShape(type, null, false);
    }

    private static ParameterShape P(string type, string name, bool isOut)
    {
        return new ParameterShape(type, name, isOut);
    }

    private static void PinnedHash(string path)
    {
        if (String.IsNullOrEmpty(path))
            throw new ArgumentException("--assembly is required");
        byte[] digest;
        using (SHA256 hash = SHA256.Create())
        using (FileStream stream = File.OpenRead(path))
            digest = hash.ComputeHash(stream);
        StringBuilder actual = new StringBuilder(64);
        for (int index = 0; index < digest.Length; index++)
        {
            actual.Append(digest[index].ToString(
                "x2", CultureInfo.InvariantCulture));
        }
        Check.Equal(
            OracleProtocol.ExpectedAssemblySha256,
            actual.ToString(),
            "Assembly-CSharp SHA-256");
    }

    private static void ExactObservedMethods(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--assembly"))
        {
            image.RequireMethod("Game", "Update", "private", false,
                "System.Void", new ParameterShape[0]);
            image.RequireMethod("Game", "DoPlayerInput", "private", false,
                "System.Void", new ParameterShape[0]);
            image.RequireMethod("Game", "Playerinputstring", "private", false,
                "Direction", new ParameterShape[0]);
            image.RequireMethod("GameState", "ProcessInput", "public", false,
                "System.Boolean", new ParameterShape[] { P("Direction") });
            image.RequireMethod("Game", "DoUndo", "public", false,
                "System.Void", new ParameterShape[0]);
            image.RequireMethod("Game", "RestorePrevState", "private", false,
                "System.Void", new ParameterShape[] { P("GameState.BakStruct") });
            image.RequireMethod("Game", "DoRestart", "public", false,
                "System.Void", new ParameterShape[0]);
            image.RequireMethod("Game", "SetGameState", "public", false,
                "System.Void", new ParameterShape[] { P("GameState") });
            image.RequireMethod("GameState", "Moving", "public", false,
                "System.Boolean", new ParameterShape[0]);
            image.RequireMethod("GameState", "Save", "public", false,
                "System.String", new ParameterShape[]
                {
                    P("System.Boolean"), P("System.Boolean")
                });
            Check.Equal(0,
                image.RequireInt32EnumConstant("Direction", "North"),
                "Direction.North");
            Check.Equal(1,
                image.RequireInt32EnumConstant("Direction", "South"),
                "Direction.South");
            Check.Equal(2,
                image.RequireInt32EnumConstant("Direction", "West"),
                "Direction.West");
            Check.Equal(3,
                image.RequireInt32EnumConstant("Direction", "East"),
                "Direction.East");
            Check.Equal(8,
                image.RequireInt32EnumConstant("Direction", "None"),
                "Direction.None");
        }
    }

    private static void ExactRequiredFields(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--assembly"))
        {
            RequireField(image, "Game", "gamestate", "public", false, "GameState");
            RequireField(image, "Game", "exitSequence", "public", false, "System.Boolean");
            RequireField(image, "Game", "bluespawnanim", "public", false, "System.Boolean");
            RequireField(image, "Game", "escmenu", "public", false, "UnityEngine.GameObject");
            RequireField(image, "Game", "endingsequence", "public", true, "System.Boolean");
            RequireField(image, "Game", "leaving", "private", false, "System.Boolean");
            RequireField(image, "Game", "gameover", "private", false, "System.Boolean");
            RequireField(image, "Game", "exploding", "private", false, "System.Boolean");
            RequireField(image, "GameState", "player", "public", false, "Entity");
            RequireField(image, "GameState", "movements", "public", false,
                "System.Collections.Generic.List<Movement>");
            RequireField(image, "GameState", "worldsausagespawns", "public", false,
                "System.Collections.Generic.List<Coord>");
            RequireField(image, "GameState", "pushestotry", "public", false, "System.Int32");
            RequireField(image, "GameState", "pushtargetlevel", "public", false, "System.String");
            RequireField(image, "GameState", "overworld", "public", false, "System.Boolean");
            RequireField(image, "GameState", "won", "public", false, "System.Boolean");
            RequireField(image, "GameState", "returning", "public", false, "System.Boolean");
            RequireField(image, "GameState", "haveevercookedall", "public", false, "System.Boolean");
            RequireField(image, "GameState", "lostreason", "public", false, "System.String");
            RequireField(image, "GameState", "displayname", "public", false, "System.String");
            RequireField(image, "GameState", "sausagescooked", "public", false, "System.Int32");
            RequireField(image, "GameState", "shouldredrawcoffins", "public", true, "Coord");
            RequireField(image, "SaveGame", "homePath", "public", true, "System.String");
            RequireField(image, "SaveGame", "PersistentDataPath", "public", true, "System.String");
        }
    }

    private static void RequireField(
        MetadataImage image,
        string owner,
        string name,
        string visibility,
        bool isStatic,
        string fieldType)
    {
        image.RequireField(owner, name, visibility, isStatic, fieldType);
    }

    private static void SyntheticMatcherRejectsNearMisses()
    {
        MethodShape expected = new MethodShape(
            default(MethodDefinitionHandle), "GameState", "ProcessInput",
            "public", false, "System.Boolean",
            new ParameterShape[] { P("Direction") });
        Check.Throws<InvalidOperationException>(
            delegate
            {
                RequireMethodShape(
                    new MethodShape[]
                    {
                        new MethodShape(
                            default(MethodDefinitionHandle), "GameState",
                            "ProcessInput", "public", false, "System.Boolean",
                            new ParameterShape[] { P("System.Int32") })
                    }, expected);
            },
            "wrong overload rejected");
        Check.Throws<InvalidOperationException>(
            delegate
            {
                RequireMethodShape(
                    new MethodShape[]
                    {
                        new MethodShape(
                            default(MethodDefinitionHandle), "GameState",
                            "ProcessInput", "public", true, "System.Boolean",
                            new ParameterShape[] { P("Direction") })
                    }, expected);
            },
            "wrong static flag rejected");
        FieldShape expectedField = new FieldShape(
            "Game", "gamestate", "public", false, "GameState");
        Check.Throws<InvalidOperationException>(
            delegate
            {
                RequireFieldShape(
                    new FieldShape[]
                    {
                        new FieldShape(
                            "Game", "gamestate", "public", false,
                            "System.Object")
                    }, expectedField);
            },
            "wrong field type rejected");
        Check.Throws<InvalidOperationException>(
            delegate
            {
                RequireFieldShape(
                    new FieldShape[]
                    {
                        new FieldShape(
                            "Game", "gamestate", "private", false,
                            "GameState")
                    }, expectedField);
            },
            "wrong visibility rejected");
    }

    internal static MethodShape RequireMethodShape(
        MethodShape[] actual,
        MethodShape expected)
    {
        MethodShape found = null;
        for (int index = 0; index < actual.Length; index++)
        {
            if (!MethodMatches(actual[index], expected))
                continue;
            if (found != null)
                throw new InvalidOperationException(
                    "duplicate method shape: " + expected.Owner + "::" + expected.Name);
            found = actual[index];
        }
        if (found == null)
        {
            throw new InvalidOperationException(
                "missing method shape: " + expected.Owner + "::" + expected.Name);
        }
        return found;
    }

    internal static FieldShape RequireFieldShape(
        FieldShape[] actual,
        FieldShape expected)
    {
        FieldShape found = null;
        for (int index = 0; index < actual.Length; index++)
        {
            FieldShape value = actual[index];
            if (value.Owner != expected.Owner
                || value.Name != expected.Name
                || value.Visibility != expected.Visibility
                || value.IsStatic != expected.IsStatic
                || value.FieldType != expected.FieldType)
                continue;
            if (found != null)
                throw new InvalidOperationException(
                    "duplicate field shape: " + expected.Owner + "::" + expected.Name);
            found = value;
        }
        if (found == null)
        {
            throw new InvalidOperationException(
                "missing field shape: " + expected.Owner + "::" + expected.Name);
        }
        return found;
    }

    private static bool MethodMatches(MethodShape actual, MethodShape expected)
    {
        if (actual.Owner != expected.Owner
            || actual.Name != expected.Name
            || actual.Visibility != expected.Visibility
            || actual.IsStatic != expected.IsStatic
            || actual.ReturnType != expected.ReturnType
            || actual.Parameters.Length != expected.Parameters.Length)
            return false;
        for (int index = 0; index < actual.Parameters.Length; index++)
        {
            if (actual.Parameters[index].Type != expected.Parameters[index].Type)
                return false;
            if (expected.Parameters[index].Name != null
                && actual.Parameters[index].Name != expected.Parameters[index].Name)
                return false;
            if (actual.Parameters[index].IsOut != expected.Parameters[index].IsOut)
                return false;
        }
        return true;
    }

    private static void PluginPeAndReferences(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            PEHeaders headers = image.Headers;
            Check.True(headers.PEHeader != null, "PE header");
            Check.Equal(PEMagic.PE32, headers.PEHeader.Magic, "PE32 image");
            CorHeader cor = headers.CorHeader;
            Check.True(cor != null, "CLR header");
            Check.True((cor.Flags & CorFlags.ILOnly) != 0, "IL-only image");
            Check.Equal(0, cor.EntryPointTokenOrRelativeVirtualAddress,
                "no native or managed entrypoint");
            Check.Equal(0, cor.ManagedNativeHeaderDirectory.Size,
                "no managed-native header");
            Check.Equal("v2.0.50727", image.Reader.MetadataVersion,
                "CLR v2 metadata version");
            AssemblyDefinition assembly = image.Reader.GetAssemblyDefinition();
            Check.Equal("SsrOracle.Plugin", image.Reader.GetString(assembly.Name),
                "assembly name");
            Check.Equal(new Version(1, 0, 0, 0), assembly.Version,
                "assembly version");
            Check.False(
                image.HasCustomAttribute(
                    assembly.GetCustomAttributes(),
                    "System.Runtime.Versioning.TargetFrameworkAttribute"),
                "no target-framework attribute");

            List<string> references = new List<string>();
            foreach (AssemblyReferenceHandle handle in image.Reader.AssemblyReferences)
            {
                AssemblyReference reference = image.Reader.GetAssemblyReference(handle);
                references.Add(image.Reader.GetString(reference.Name)
                    + "=" + reference.Version.ToString());
            }
            references.Sort(StringComparer.Ordinal);
            Check.Sequence(new string[]
            {
                "0Harmony=2.9.0.0",
                "Assembly-CSharp=0.0.0.0",
                "BepInEx=5.4.23.5",
                "System.Core=3.5.0.0",
                "System=2.0.0.0",
                "UnityEngine.CoreModule=0.0.0.0",
                "mscorlib=2.0.0.0"
            }, references.ToArray(), "exact direct AssemblyRef set");
        }
    }

    private static void ExactPatchSurface(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            string[] patchTypes = new string[]
            {
                "DoPlayerInputPatch", "DoRestartPatch", "DoUndoPatch",
                "GameUpdatePatch", "PlayerInputStringPatch", "ProcessInputPatch",
                "RestorePrevStatePatch", "SetGameStatePatch"
            };
            List<string> actualPatchTypes = new List<string>();
            foreach (TypeDefinitionHandle handle in image.Reader.TypeDefinitions)
            {
                TypeDefinition type = image.Reader.GetTypeDefinition(handle);
                if (image.HasCustomAttribute(
                    type.GetCustomAttributes(), "HarmonyLib.HarmonyPatch"))
                    actualPatchTypes.Add(MetadataImage.DefinitionName(image.Reader, handle));
            }
            actualPatchTypes.Sort(StringComparer.Ordinal);
            Check.Sequence(patchTypes, actualPatchTypes.ToArray(),
                "exact eight Harmony patch classes");

            RequirePatch(image, "GameUpdatePatch", "Game", "Update", 36,
                "System.Void", new string[0], new MethodShape[]
                {
                    Callback("Postfix", "System.Void", P("Game", "__instance", false)),
                    Callback("Finalizer", "System.Exception",
                        P("System.Exception", "__exception", false))
                });
            RequirePatch(image, "DoPlayerInputPatch", "Game", "DoPlayerInput", 36,
                "System.Void", new string[0], new MethodShape[]
                {
                    Callback("Prefix", "System.Void", P("HookToken&", "__state", true)),
                    Callback("Postfix", "System.Void", P("HookToken", "__state", false)),
                    Callback("Finalizer", "System.Exception",
                        P("System.Exception", "__exception", false),
                        P("HookToken", "__state", false))
                });
            RequirePatch(image, "PlayerInputStringPatch", "Game",
                "Playerinputstring", 36, "Direction", new string[0],
                new MethodShape[]
                {
                    Callback("Postfix", "System.Void",
                        P("Direction", "__result", false))
                });
            RequirePatch(image, "ProcessInputPatch", "GameState", "ProcessInput", 20,
                "System.Boolean", new string[] { "Direction" }, new MethodShape[]
                {
                    Callback("Prefix", "System.Void",
                        P("GameState", "__instance", false),
                        P("Direction", "__0", false),
                        P("HookToken&", "__state", true)),
                    Callback("Postfix", "System.Void",
                        P("GameState", "__instance", false),
                        P("System.Boolean", "__result", false),
                        P("HookToken", "__state", false)),
                    Callback("Finalizer", "System.Exception",
                        P("System.Exception", "__exception", false),
                        P("HookToken", "__state", false))
                });
            RequirePatch(image, "DoUndoPatch", "Game", "DoUndo", 20,
                "System.Void", new string[0], new MethodShape[]
                {
                    Callback("Prefix", "System.Void",
                        P("Game", "__instance", false),
                        P("HookToken&", "__state", true)),
                    Callback("Postfix", "System.Void",
                        P("Game", "__instance", false),
                        P("HookToken", "__state", false)),
                    Callback("Finalizer", "System.Exception",
                        P("System.Exception", "__exception", false),
                        P("HookToken", "__state", false))
                });
            RequirePatch(image, "RestorePrevStatePatch", "Game",
                "RestorePrevState", 36, "System.Void",
                new string[] { "GameState.BakStruct" }, new MethodShape[]
                {
                    Callback("Prefix", "System.Void",
                        P("GameState.BakStruct", "__0", false))
                });
            RequirePatch(image, "DoRestartPatch", "Game", "DoRestart", 20,
                "System.Void", new string[0], new MethodShape[]
                {
                    Callback("Prefix", "System.Void", P("HookToken&", "__state", true)),
                    Callback("Postfix", "System.Void", P("HookToken", "__state", false)),
                    Callback("Finalizer", "System.Exception",
                        P("System.Exception", "__exception", false),
                        P("HookToken", "__state", false))
                });
            RequirePatch(image, "SetGameStatePatch", "Game", "SetGameState", 20,
                "System.Void", new string[] { "GameState" }, new MethodShape[]
                {
                    Callback("Prefix", "System.Void",
                        P("Game", "__instance", false),
                        P("GameState", "__0", false),
                        P("HookToken&", "__state", true)),
                    Callback("Postfix", "System.Void",
                        P("Game", "__instance", false),
                        P("HookToken", "__state", false)),
                    Callback("Finalizer", "System.Exception",
                        P("System.Exception", "__exception", false),
                        P("HookToken", "__state", false))
                });
        }
    }

    private static MethodShape Callback(
        string name,
        string returnType,
        params ParameterShape[] parameters)
    {
        return new MethodShape(
            default(MethodDefinitionHandle), "", name, "private", true,
            returnType, parameters);
    }

    private static void RequirePatch(
        MetadataImage image,
        string patchType,
        string targetOwner,
        string targetName,
        int bindingFlags,
        string returnType,
        string[] targetParameters,
        MethodShape[] callbacks)
    {
        MethodShape target = image.RequireMethod(
            patchType, "TargetMethod", "private", true,
            "System.Reflection.MethodBase", new ParameterShape[0]);
        RequireString(image, target, targetName);
        RequireTypeToken(image, target, targetOwner);
        RequireTypeToken(image, target, returnType);
        RequireConstant(image, target, bindingFlags);
        for (int index = 0; index < targetParameters.Length; index++)
            RequireTypeToken(image, target, targetParameters[index]);
        RequireCall(image, target, "PatchTarget", "Require");

        for (int index = 0; index < callbacks.Length; index++)
        {
            callbacks[index].Owner = patchType;
            MethodShape callback = image.RequireMethod(
                patchType,
                callbacks[index].Name,
                callbacks[index].Visibility,
                callbacks[index].IsStatic,
                callbacks[index].ReturnType,
                callbacks[index].Parameters);
            if (callbacks[index].Name == "Finalizer")
            {
                RequireCall(
                    image,
                    callback,
                    "PassiveController",
                    patchType == "GameUpdatePatch"
                        ? "FinalizeUpdatePatch"
                        : "FinalizePatch");
            }
            else
            {
                RequireCall(
                    image,
                    callback,
                    "PassiveController",
                    "ObservePatch");
            }
        }
        MethodShape[] all = AllNamedCallbacks(image, patchType);
        Check.Equal(callbacks.Length, all.Length,
            "exact callback count for " + patchType);
        for (int index = 0; index < all.Length; index++)
        {
            for (int parameter = 0; parameter < all[index].Parameters.Length;
                parameter++)
            {
                ParameterShape value = all[index].Parameters[parameter];
                if (value.Type.EndsWith("&", StringComparison.Ordinal))
                {
                    Check.Equal("HookToken&", value.Type,
                        "only HookToken may be by-ref");
                    Check.Equal("__state", value.Name,
                        "only __state may be by-ref");
                    Check.True(value.IsOut, "HookToken __state is out");
                    Check.Equal("Prefix", all[index].Name,
                        "only a prefix emits token state");
                }
            }
        }
    }

    private static MethodShape[] AllNamedCallbacks(
        MetadataImage image,
        string patchType)
    {
        string[] names = new string[] { "Prefix", "Postfix", "Finalizer" };
        List<MethodShape> methods = new List<MethodShape>();
        for (int index = 0; index < names.Length; index++)
        {
            MethodShape[] found = image.Methods(patchType, names[index]);
            for (int item = 0; item < found.Length; item++)
                methods.Add(found[item]);
        }
        return methods.ToArray();
    }

    private static void AdapterCallSurface(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            image.RequireMethod("GameAdapter", "AuthenticateAndRedirectSavePath",
                "assembly", false, "System.Void",
                new ParameterShape[] { P("System.String") });
            image.RequireMethod("GameAdapter", "VerifySavePath",
                "assembly", false, "System.Boolean", new ParameterShape[0]);
            image.RequireMethod("GameAdapter", "TryGetState",
                "assembly", false, "System.Boolean",
                new ParameterShape[]
                {
                    P("Game"),
                    new ParameterShape("System.Object&", null, true)
                });
            image.RequireMethod("GameAdapter", "IsQuiescent",
                "assembly", false, "System.Boolean",
                new ParameterShape[] { P("Game"), P("GameState") });
            image.RequireMethod("GameAdapter", "MovementScheduled",
                "assembly", false, "System.Boolean",
                new ParameterShape[] { P("GameState") });
            image.RequireMethod("GameAdapter", "CurrentMovementScheduled",
                "assembly", false, "System.Boolean",
                new ParameterShape[] { P("Game") });
            MethodShape capture = image.RequireMethod("GameAdapter", "Capture",
                "assembly", false, "CaptureRecord",
                new ParameterShape[] { P("GameState") });
            image.RequireField("GameAdapter", "isolatedCanonicalPath",
                "private", false, "System.String");

            MethodShape gate = image.RequireMethod("GameAdapter", "IsQuiescent",
                "assembly", false, "System.Boolean",
                new ParameterShape[] { P("Game"), P("GameState") });
            RequireCall(image, gate, "UnityEngine.Object", "op_Equality");
            RequireCall(image, gate, "UnityEngine.GameObject", "get_activeSelf");
            RequireCall(image, gate, "Coord", "op_Equality");
            RequireFalseFalseSave(image, capture);
            RequireOnlyExternalCallers(
                image,
                "GameState",
                "Moving",
                new string[] { "GameAdapter::MovementScheduled" });
            RequireOnlyExternalCallers(
                image,
                "GameState",
                "Save",
                new string[] { "GameAdapter::Capture" });
            RequireNoMemberReference(image, "GameState", "Lost");
        }
    }

    private static void ControllerUsesAuthorizedBoundary(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            MethodShape validate = image.RequireMethod(
                "PassiveController", "ValidateBeforeSink", "public", false,
                "System.Void", new ParameterShape[0]);
            RequireCall(
                image, validate, "PhysicalPath", "RequireAbsentLeaf");
            RequireString(image, validate, ".ndjson");
            Check.True(image.HasCatch(validate, "TraceExistsException"),
                "pre-redirect trace collision is typed");
            Check.True(image.HasCatch(
                validate, "OracleConfigurationException"),
                "pre-redirect target path failure is typed");

            MethodShape update = image.RequireMethod(
                "PassiveController", "ObserveUpdate", "assembly", false,
                "System.Void", new ParameterShape[] { P("Game") });
            List<MethodCall> updateCalls = image.Calls(update);
            RequireCall(updateCalls, "PassiveUpdateBoundary", "Observe");
            ForbidCall(updateCalls, "GameAdapter", "IsQuiescent");
            ForbidCall(updateCalls, "GameAdapter", "Capture");
            ForbidCall(updateCalls, "PassiveDriver", "CompleteUpdate");
            ForbidCall(updateCalls, "PassiveDriver", "RejectUpdate");

            MethodShape boundary = image.RequireMethod(
                "PassiveUpdateBoundary", "Observe", "assembly", false,
                "System.Void",
                new ParameterShape[] { P("IPassiveUpdateObservation") });
            RequireCallSequence(image.Calls(boundary), new string[]
            {
                "IPassiveUpdateObservation::TryGetState",
                "IPassiveUpdateObservation::NowSeconds",
                "PassiveDriver::BeginUpdate",
                "IPassiveUpdateObservation::VerifySavePath",
                "IPassiveUpdateObservation::TryGetState",
                "PassiveDriver::AuthorizeUpdate",
                "IPassiveUpdateObservation::IsQuiescent",
                "IPassiveUpdateObservation::Capture",
                "IPassiveUpdateObservation::UtcNow",
                "PassiveDriver::CompleteUpdate"
            });
            Check.Equal(0, image.Methods("PassiveDriver", "RejectUpdate").Length,
                "removed RejectUpdate API");

            MethodShape observedCapture = image.RequireMethod(
                "PassiveController.GameUpdateObservation", "Capture",
                "public", false, "CaptureRecord",
                new ParameterShape[] { P("System.Object") });
            RequireCall(image, observedCapture, "GameAdapter", "Capture");
            MethodShape observedGate = image.RequireMethod(
                "PassiveController.GameUpdateObservation", "IsQuiescent",
                "public", false, "System.Boolean",
                new ParameterShape[] { P("System.Object") });
            RequireCall(image, observedGate, "GameAdapter", "IsQuiescent");
            RequireOnlyExternalCallers(
                image,
                "GameAdapter",
                "Capture",
                new string[]
                {
                    "PassiveController.GameUpdateObservation::Capture"
                });
            RequireOnlyExternalCallers(
                image,
                "GameAdapter",
                "IsQuiescent",
                new string[]
                {
                    "PassiveController.GameUpdateObservation::IsQuiescent"
                });
            RequireOnlyExternalCallers(
                image,
                "GameAdapter",
                "MovementScheduled",
                new string[] { "PassiveController::ProcessInputReturned" });
            RequireOnlyExternalCallers(
                image,
                "GameAdapter",
                "CurrentMovementScheduled",
                new string[] { "PassiveController::UndoReturned" });

            MethodShape processReturned = image.RequireMethod(
                "PassiveController", "ProcessInputReturned", "assembly", false,
                "System.Void", new ParameterShape[]
                {
                    P("GameState"), P("System.Boolean"), P("HookToken")
                });
            RequireCaptureFailureBoundary(
                image, processReturned, "ProcessInputThrew");
            RequireCallSequence(image.Calls(processReturned), new string[]
            {
                "HookToken::get_Active",
                "GameAdapter::MovementScheduled"
            });
            RequireCaptureFailureBoundary(
                image,
                image.RequireMethod(
                    "PassiveController", "UndoEntered", "assembly", false,
                    "HookToken", new ParameterShape[] { P("Game") }),
                null);
            MethodShape undoReturned = image.RequireMethod(
                "PassiveController", "UndoReturned", "assembly", false,
                "System.Void", new ParameterShape[]
                {
                    P("Game"), P("HookToken")
                });
            RequireCaptureFailureBoundary(
                image, undoReturned, "UndoThrew");
            RequireCallSequence(image.Calls(undoReturned), new string[]
            {
                "HookToken::get_Active",
                "GameAdapter::CurrentMovementScheduled"
            });
            RequireCaptureFailureBoundary(
                image,
                image.RequireMethod(
                    "PassiveController", "StateSetEntered", "assembly", false,
                    "HookToken", new ParameterShape[]
                    {
                        P("Game"), P("GameState")
                    }),
                null);
            MethodShape stateSetReturned = image.RequireMethod(
                "PassiveController", "StateSetReturned", "assembly", false,
                "System.Void", new ParameterShape[]
                {
                    P("Game"), P("HookToken")
                });
            RequireCaptureFailureBoundary(
                image, stateSetReturned, "StateSetThrew");
            RequireCallSequence(image.Calls(stateSetReturned), new string[]
            {
                "HookToken::get_Active",
                "GameAdapter::TryGetState"
            });

            MethodShape createDriver = image.RequireMethod(
                "PassiveController", "CreateDriver", "public", false,
                "PassiveDriver", new ParameterShape[0]);
            RequireCall(
                image, createDriver, "PassiveController", "CloseUnownedSink");
            Check.True(image.HasCatch(createDriver, "TraceExistsException"),
                "driver factory classifies trace collision");
            Check.True(image.HasCatch(createDriver, "TraceIoException"),
                "driver factory classifies trace IO");
            Check.True(image.HasCatch(createDriver, "System.Exception"),
                "driver factory contains unexpected construction failure");
            MethodShape closeUnowned = image.RequireMethod(
                "PassiveController", "CloseUnownedSink", "private", true,
                "System.Void", new ParameterShape[] { P("ITraceSink") });
            RequireCall(image, closeUnowned, "ITraceSink", "Close");
        }
    }

    private static void RequireCaptureFailureBoundary(
        MetadataImage image,
        MethodShape method,
        string cleanupMethod)
    {
        Check.True(image.HasCatch(method, "CaptureException"),
            method.Name + " catches CaptureException");
        RequireCall(image, method, "PassiveDriver", "TryFault");
        RequireString(image, method, "capture_failed");
        if (cleanupMethod == null)
            RequireCall(image, method, "HookToken", "Inert");
        else
            RequireCall(image, method, "PassiveDriver", cleanupMethod);
    }

    private static void BepInPluginIdentity(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            TypeDefinition plugin = image.Reader.GetTypeDefinition(
                image.FindType("SsrOracle.Plugin"));
            CustomAttribute attribute = image.RequireCustomAttribute(
                plugin.GetCustomAttributes(), "BepInEx.BepInPlugin");
            CustomAttributeValue<string> value = image.DecodeAttribute(attribute);
            Check.Equal(3, value.FixedArguments.Length,
                "BepInPlugin constructor arity");
            Check.Equal("dev.jlsor.ssr.oracle",
                (string)value.FixedArguments[0].Value, "plugin GUID");
            Check.Equal("SSR Executable Oracle",
                (string)value.FixedArguments[1].Value, "plugin name");
            Check.Equal("0.2.0",
                (string)value.FixedArguments[2].Value, "plugin version");
        }
    }

    private static void TypedModeAndOwnerOnlyTeardown(string path)
    {
        using (MetadataImage image = MetadataImage.Open(path, "--plugin"))
        {
            MethodShape awake = image.RequireMethod(
                "SsrOracle.Plugin", "Awake", "private", false,
                "System.Void", new ParameterShape[0]);
            List<MethodCall> awakeCalls = image.Calls(awake);
            RequireCallSequence(awakeCalls, new string[]
            {
                "System.IO.Path::Combine",
                "OracleConfiguration::Load",
                "OracleConfiguration::get_Mode",
                "PluginModePolicy::StartOff",
                "PassiveController::.ctor",
                "PassiveController::Start"
            });
            Check.Equal(1, CountCalls(
                awakeCalls, "OracleConfiguration", "Load"),
                "one typed configuration read");
            Check.True(image.HasCatch(awake, "OracleConfigurationException"),
                "typed configuration catch");
            RequireString(image, awake, "dev.jlsor.ssr.oracle.cfg");
            ForbidCall(awakeCalls, "System.IO.File", "ReadAllBytes");
            ForbidCall(awakeCalls, "PassiveDriver", ".ctor");
            RequireConditionalBranchBetween(
                image, awake, "OracleConfiguration", "get_Mode",
                "PluginModePolicy", "StartOff");

            ForbidMemberReference(image,
                "BepInEx.Configuration.ConfigFile", "Bind");
            ForbidMemberReference(image,
                "BepInEx.Configuration.ConfigFile", "Save");
            ForbidPluginFileWrites(image);
            ForbidMemberReference(image, "HarmonyLib.Harmony", "UnpatchAll");

            MethodShape unpatch = image.RequireMethod(
                "PassiveController", "UnpatchSelf", "public", false,
                "System.Void", new ParameterShape[0]);
            RequireCall(image, unpatch, "HarmonyLib.Harmony", "UnpatchSelf");
            MethodShape startupDispose = image.RequireMethod(
                "PassiveStartup", "Dispose", "public", false,
                "System.Void", new ParameterShape[0]);
            RequireCallSequence(image.Calls(startupDispose), new string[]
            {
                "PassiveStartup::SafeDisable",
                "PassiveStartup::SafeUnpatch",
                "PassiveDriver::Dispose"
            });
            MethodShape safeDisable = image.RequireMethod(
                "PassiveStartup", "SafeDisable", "private", false,
                "System.Void", new ParameterShape[0]);
            RequireCall(image, safeDisable, "PassiveDriver", "Disable");
            MethodShape safeUnpatch = image.RequireMethod(
                "PassiveStartup", "SafeUnpatch", "private", false,
                "System.Void", new ParameterShape[0]);
            RequireCall(
                image, safeUnpatch, "IPassiveStartupServices", "UnpatchSelf");
            MethodShape controllerDispose = image.RequireMethod(
                "PassiveController", "Dispose", "public", false,
                "System.Void", new ParameterShape[0]);
            RequireCall(image, controllerDispose, "PassiveStartup", "Dispose");
            MethodShape destroy = image.RequireMethod(
                "SsrOracle.Plugin", "OnDestroy", "private", false,
                "System.Void", new ParameterShape[0]);
            RequireCall(image, destroy, "PassiveController", "Dispose");
        }
    }

    private static void RequireFalseFalseSave(
        MetadataImage image,
        MethodShape capture)
    {
        List<IlInstruction> instructions = image.Instructions(capture);
        List<MethodCall> calls = image.Calls(capture);
        MethodCall save = null;
        for (int index = 0; index < calls.Count; index++)
        {
            if (calls[index].Owner == "GameState" && calls[index].Name == "Save")
            {
                if (save != null)
                    throw new InvalidOperationException("duplicate GameState.Save call");
                save = calls[index];
            }
        }
        if (save == null)
            throw new InvalidOperationException("missing GameState.Save call");
        int callIndex = -1;
        for (int index = 0; index < instructions.Count; index++)
        {
            if (instructions[index].Offset == save.Offset)
                callIndex = index;
        }
        Check.True(callIndex >= 2, "Save has two argument instructions");
        int first;
        int second;
        Check.True(image.TryConstant(instructions[callIndex - 2], out first),
            "first Save flag is constant");
        Check.True(image.TryConstant(instructions[callIndex - 1], out second),
            "second Save flag is constant");
        Check.Equal(0, first, "Save first flag false");
        Check.Equal(0, second, "Save second flag false");
    }

    private static void RequireOnlyExternalCallers(
        MetadataImage image,
        string targetOwner,
        string targetName,
        string[] expectedCallers)
    {
        List<string> actual = new List<string>();
        foreach (TypeDefinitionHandle typeHandle in image.Reader.TypeDefinitions)
        {
                string owner = MetadataImage.DefinitionName(image.Reader, typeHandle);
                if (owner == targetOwner)
                    continue;
                TypeDefinition type = image.Reader.GetTypeDefinition(typeHandle);
            foreach (MethodDefinitionHandle methodHandle in type.GetMethods())
            {
                MethodDefinition definition = image.Reader.GetMethodDefinition(methodHandle);
                if (definition.RelativeVirtualAddress == 0)
                    continue;
                string name = image.Reader.GetString(definition.Name);
                MethodShape[] overloads = image.Methods(owner, name);
                for (int candidate = 0; candidate < overloads.Length; candidate++)
                {
                    if (overloads[candidate].Handle != methodHandle)
                        continue;
                    List<MethodCall> calls = image.Calls(overloads[candidate]);
                    for (int call = 0; call < calls.Count; call++)
                    {
                        if (calls[call].Owner == targetOwner
                            && calls[call].Name == targetName)
                            actual.Add(owner + "::" + name);
                    }
                }
            }
        }
        actual.Sort(StringComparer.Ordinal);
        string[] expected = (string[])expectedCallers.Clone();
        Array.Sort(expected, StringComparer.Ordinal);
        Check.Sequence(expected, actual.ToArray(),
            "exact callers of " + targetOwner + "::" + targetName);
    }

    private static void RequireNoMemberReference(
        MetadataImage image,
        string owner,
        string name)
    {
        ForbidMemberReference(image, owner, name);
    }

    private static void ForbidMemberReference(
        MetadataImage image,
        string owner,
        string name)
    {
        foreach (MemberReferenceHandle handle in image.Reader.MemberReferences)
        {
            MemberReference member = image.Reader.GetMemberReference(handle);
            if (image.TypeName((EntityHandle)member.Parent) == owner
                && image.Reader.GetString(member.Name) == name)
            {
                throw new InvalidOperationException(
                    "forbidden member reference: " + owner + "::" + name);
            }
        }
    }

    private static void ForbidPluginFileWrites(MetadataImage image)
    {
        string[] methods = new string[] { "Awake", "OnDestroy", "EmitBootMarker" };
        for (int index = 0; index < methods.Length; index++)
        {
            MethodShape method = image.RequireMethod(
                "SsrOracle.Plugin", methods[index], "private", false,
                "System.Void", new ParameterShape[0]);
            List<MethodCall> calls = image.Calls(method);
            for (int call = 0; call < calls.Count; call++)
            {
                if (calls[call].Owner == "System.IO.File"
                    || calls[call].Owner == "System.IO.FileStream"
                    || calls[call].Owner == "System.IO.StreamWriter")
                {
                    throw new InvalidOperationException(
                        "plugin shell performs file I/O: " + calls[call].Key);
                }
            }
        }
    }

    private static void RequireString(
        MetadataImage image,
        MethodShape method,
        string value)
    {
        List<IlInstruction> instructions = image.Instructions(method);
        for (int index = 0; index < instructions.Count; index++)
        {
            if (instructions[index].OpCode.Value == OpCodes.Ldstr.Value
                && image.UserString(instructions[index]) == value)
                return;
        }
        throw new InvalidOperationException("missing string literal: " + value);
    }

    private static void RequireTypeToken(
        MetadataImage image,
        MethodShape method,
        string value)
    {
        List<IlInstruction> instructions = image.Instructions(method);
        for (int index = 0; index < instructions.Count; index++)
        {
            if (instructions[index].OpCode.Value == OpCodes.Ldtoken.Value
                && image.TypeToken(instructions[index]) == value)
                return;
        }
        throw new InvalidOperationException("missing type token: " + value);
    }

    private static void RequireConstant(
        MetadataImage image,
        MethodShape method,
        int value)
    {
        List<IlInstruction> instructions = image.Instructions(method);
        for (int index = 0; index < instructions.Count; index++)
        {
            int actual;
            if (image.TryConstant(instructions[index], out actual) && actual == value)
                return;
        }
        throw new InvalidOperationException(
            "missing integer constant: " + value.ToString(CultureInfo.InvariantCulture));
    }

    private static void RequireCall(
        MetadataImage image,
        MethodShape method,
        string owner,
        string name)
    {
        RequireCall(image.Calls(method), owner, name);
    }

    private static void RequireCall(
        List<MethodCall> calls,
        string owner,
        string name)
    {
        if (CountCalls(calls, owner, name) == 0)
        {
            throw new InvalidOperationException(
                "missing call: " + owner + "::" + name);
        }
    }

    private static void ForbidCall(
        List<MethodCall> calls,
        string owner,
        string name)
    {
        if (CountCalls(calls, owner, name) != 0)
        {
            throw new InvalidOperationException(
                "forbidden call: " + owner + "::" + name);
        }
    }

    private static int CountCalls(
        List<MethodCall> calls,
        string owner,
        string name)
    {
        int count = 0;
        for (int index = 0; index < calls.Count; index++)
        {
            if (calls[index].Owner == owner && calls[index].Name == name)
                count++;
        }
        return count;
    }

    private static void RequireCallSequence(
        List<MethodCall> calls,
        string[] expected)
    {
        int cursor = -1;
        for (int expectedIndex = 0; expectedIndex < expected.Length;
            expectedIndex++)
        {
            int found = -1;
            for (int call = cursor + 1; call < calls.Count; call++)
            {
                string prefix = calls[call].Owner + "::" + calls[call].Name;
                if (prefix == expected[expectedIndex])
                {
                    found = call;
                    break;
                }
            }
            if (found < 0)
            {
                throw new InvalidOperationException(
                    "missing ordered call: " + expected[expectedIndex]);
            }
            cursor = found;
        }
    }

    private static void RequireConditionalBranchBetween(
        MetadataImage image,
        MethodShape method,
        string firstOwner,
        string firstName,
        string secondOwner,
        string secondName)
    {
        List<MethodCall> calls = image.Calls(method);
        int firstOffset = -1;
        int secondOffset = -1;
        for (int index = 0; index < calls.Count; index++)
        {
            if (calls[index].Owner == firstOwner && calls[index].Name == firstName)
                firstOffset = calls[index].Offset;
            if (calls[index].Owner == secondOwner && calls[index].Name == secondName)
            {
                secondOffset = calls[index].Offset;
                break;
            }
        }
        Check.True(firstOffset >= 0 && secondOffset > firstOffset,
            "typed mode branch endpoints");
        List<IlInstruction> instructions = image.Instructions(method);
        for (int index = 0; index < instructions.Count; index++)
        {
            if (instructions[index].Offset > firstOffset
                && instructions[index].Offset < secondOffset
                && instructions[index].OpCode.FlowControl == FlowControl.Cond_Branch)
                return;
        }
        throw new InvalidOperationException("missing typed mode conditional branch");
    }
}
```

`System.Reflection.Metadata`, `System.Reflection.PortableExecutable`,
`System.Collections.Immutable`, and `System.Reflection.Emit` are all supplied
by the pinned net10 reference pack used by the harness.  Do not add a NuGet or
plugin project reference; keep the existing zero-package test project and the
linked `../Core/**/*.cs` item from Task 1.

Create `GameContract.cs` with this complete runtime validator.  The metadata
cohort independently characterizes the same signatures without loading Unity;
this product validator owns passive startup rejection.

```csharp
using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

internal static class GameContract
{
    internal static void ValidateLegacySurface()
    {
        RequireMethod(typeof(Game), "Playerinputstring",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(Direction), new Type[0]);
        RequireMethod(typeof(Game), "DoPlayerInput",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[0]);
        RequireMethod(typeof(GameState), "ProcessInput",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(bool), new Type[] { typeof(Direction) });
    }

    internal static void ValidatePassiveSurface()
    {
        ValidateLegacySurface();
        RequireDirectionValue("North", 0);
        RequireDirectionValue("South", 1);
        RequireDirectionValue("West", 2);
        RequireDirectionValue("East", 3);
        RequireDirectionValue("None", 8);
        RequireMethod(typeof(Game), "Update",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[0]);
        RequireMethod(typeof(Game), "DoUndo",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[0]);
        RequireMethod(typeof(Game), "RestorePrevState",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[] { typeof(GameState.BakStruct) });
        RequireMethod(typeof(Game), "DoRestart",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[0]);
        RequireMethod(typeof(Game), "SetGameState",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(void), new Type[] { typeof(GameState) });
        RequireMethod(typeof(GameState), "Moving",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(bool), new Type[0]);
        RequireMethod(typeof(GameState), "Save",
            BindingFlags.Instance | BindingFlags.Public,
            typeof(string), new Type[] { typeof(bool), typeof(bool) });

        RequireField(typeof(Game), "gamestate",
            BindingFlags.Instance | BindingFlags.Public, typeof(GameState));
        RequireField(typeof(Game), "exitSequence",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(Game), "bluespawnanim",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(Game), "escmenu",
            BindingFlags.Instance | BindingFlags.Public, typeof(GameObject));
        RequireField(typeof(Game), "endingsequence",
            BindingFlags.Static | BindingFlags.Public, typeof(bool));
        RequireField(typeof(Game), "leaving",
            BindingFlags.Instance | BindingFlags.NonPublic, typeof(bool));
        RequireField(typeof(Game), "gameover",
            BindingFlags.Instance | BindingFlags.NonPublic, typeof(bool));
        RequireField(typeof(Game), "exploding",
            BindingFlags.Instance | BindingFlags.NonPublic, typeof(bool));

        RequireField(typeof(GameState), "player",
            BindingFlags.Instance | BindingFlags.Public, typeof(Entity));
        RequireField(typeof(GameState), "movements",
            BindingFlags.Instance | BindingFlags.Public, typeof(List<Movement>));
        RequireField(typeof(GameState), "worldsausagespawns",
            BindingFlags.Instance | BindingFlags.Public, typeof(List<Coord>));
        RequireField(typeof(GameState), "pushestotry",
            BindingFlags.Instance | BindingFlags.Public, typeof(int));
        RequireField(typeof(GameState), "pushtargetlevel",
            BindingFlags.Instance | BindingFlags.Public, typeof(string));
        RequireField(typeof(GameState), "overworld",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "won",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "returning",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "haveevercookedall",
            BindingFlags.Instance | BindingFlags.Public, typeof(bool));
        RequireField(typeof(GameState), "lostreason",
            BindingFlags.Instance | BindingFlags.Public, typeof(string));
        RequireField(typeof(GameState), "displayname",
            BindingFlags.Instance | BindingFlags.Public, typeof(string));
        RequireField(typeof(GameState), "sausagescooked",
            BindingFlags.Instance | BindingFlags.Public, typeof(int));
        RequireField(typeof(GameState), "shouldredrawcoffins",
            BindingFlags.Static | BindingFlags.Public, typeof(Coord));
        RequireField(typeof(SaveGame), "homePath",
            BindingFlags.Static | BindingFlags.Public, typeof(string));
        RequireField(typeof(SaveGame), "PersistentDataPath",
            BindingFlags.Static | BindingFlags.Public, typeof(string));
    }

    private static void RequireMethod(
        Type type, string name, BindingFlags flags,
        Type returnType, Type[] parameters)
    {
        MethodInfo method = type.GetMethod(name, flags, null, parameters, null);
        if (method == null || method.ReturnType != returnType
            || method.IsStatic != ((flags & BindingFlags.Static) != 0))
            throw new MissingMethodException(type.FullName, name);
    }

    private static void RequireDirectionValue(string name, int expected)
    {
        FieldInfo field = typeof(Direction).GetField(
            name, BindingFlags.Public | BindingFlags.Static);
        if (field == null || !field.IsLiteral
            || field.FieldType != typeof(Direction))
        {
            throw new MissingFieldException(
                typeof(Direction).FullName, name);
        }
        object raw = field.GetRawConstantValue();
        if (raw == null || raw.GetType() != typeof(int)
            || (int)raw != expected)
        {
            throw new InvalidOperationException(
                "unexpected Direction value: " + name);
        }
    }

    private static void RequireField(
        Type type, string name, BindingFlags flags, Type fieldType)
    {
        FieldInfo field = type.GetField(name, flags);
        if (field == null || field.FieldType != fieldType
            || field.IsStatic != ((flags & BindingFlags.Static) != 0))
            throw new MissingFieldException(type.FullName, name);
    }
}
```

- [ ] **Step 4: Run the real-DLL metadata GREEN gate**

Run exactly:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/SsrOracle.Plugin.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort assembly \
  --assembly "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
```

Require the pinned-reference net35 plugin build to pass with zero warnings and
errors, proving the newly created `GameContract.cs` compiles before its Task
7.2 commit. Require the external characterization to pass. A missing
assembly/assets file/metadata reader is not GREEN, and the old name-only plugin
checks are not sufficient. Do not load or launch the plugin.

- [ ] **Step 5: Freeze the pinned-metadata review evidence**

Require the exact harness success line. Retain the Task 7.2-only diff, the
zero-warning pinned plugin compile, and the external characterization output
in the task report for post-commit review, then check the final diff:

```bash
git diff --check
```

- [ ] **Step 6: Commit only the Task 7.2 metadata slice**

```bash
git add oracle/plugin/GameContract.cs \
  oracle/plugin/tests/AssemblySurfaceTests.cs \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  oracle/plugin/tests/Program.cs
git commit -m "test: pin passive game metadata surface"
```

#### Task 7.3: Implement and audit the sole game/Unity adapter

- [ ] **Step 1: Add the adapter call-surface RED registration**

First replace only `AssemblySurfaceTests.Register` with this cumulative block.
The four game-assembly tests stay fixed and the first `plugin` registration
audits only the adapter's own method/field/call surface; controller call-site
exclusivity remains in the Task 9.2 controller test because the controller does
not exist yet.

```csharp
internal static void Register(TestRegistry tests, HarnessOptions options)
{
    tests.Add("assembly", "pinned Assembly-CSharp hash",
        delegate { PinnedHash(options.AssemblyPath); });
    tests.Add("assembly", "exact ten observed methods",
        delegate { ExactObservedMethods(options.AssemblyPath); });
    tests.Add("assembly", "exact required game fields",
        delegate { ExactRequiredFields(options.AssemblyPath); });
    tests.Add("assembly", "metadata matcher rejects near misses",
        SyntheticMatcherRejectsNearMisses);
    tests.Add("plugin", "game adapter call surface is passive",
        delegate { AdapterCallSurface(options.PluginPath); });
}
```

- [ ] **Step 2: Build the pre-adapter artifact and run semantic RED**

Keep `assembly=4`, add the temporary `plugin=1` row, build the Task 7.2
artifact before creating `GameAdapter.cs`, and require the adapter registration
to fail semantically because that type is absent:

```bash
if test ! -f oracle/plugin/obj/project.assets.json; then
  /opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
    oracle/plugin/SsrOracle.Plugin.csproj \
    --source "$PWD/data/oracle/compat/feed" \
    -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
    -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
fi
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

Require a named `plugin/game adapter call surface is passive` RED whose cause
is missing `GameAdapter`; a build, assets, or metadata-reader failure is not
the intended RED.

- [ ] **Step 3: Implement save isolation, movement, gates, and capture mapping**

Before any `Game` is accepted, require nonempty
`Environment.GetEnvironmentVariable("HOME")`, exact equality with
`SaveGame.homePath`, exact original
`PersistentDataPath = HOME + "/Library/Application Support/unity.increpare games/Sausage"`,
and canonical disjointness from the isolated directory. Resolve that expected
ordinary path with `ResolvePossiblyAbsent`, because a fresh HOME may not yet
contain the save tree; resolve the isolated path with
`ResolveExistingDirectory`. Compare canonical paths in both containment
directions. Assign the isolated canonical path, read it back, and require exact
equality. Never restore to the ordinary path during an active process.

`VerifySavePath()` runs after every active `BeginUpdate` and before
quiescence/capture. It returns false on canonical-string, existence, or
observable-topology drift covered by Task 6; it does not claim inode-level
replacement detection.

Use these exact methods and backing field in `GameAdapter`:

```csharp
private string isolatedCanonicalPath;

internal void AuthenticateAndRedirectSavePath(string isolatedPath)
{
    try
    {
        string home = Environment.GetEnvironmentVariable("HOME");
        if (String.IsNullOrEmpty(home) || SaveGame.homePath != home)
            throw new CaptureException("ordinary HOME authentication failed");
        string expectedOrdinary = home
            + "/Library/Application Support/unity.increpare games/Sausage";
        if (SaveGame.PersistentDataPath != expectedOrdinary)
            throw new CaptureException("ordinary save path changed");
        PhysicalPathIdentity ordinary =
            PhysicalPath.ResolvePossiblyAbsent(expectedOrdinary);
        string isolated = PhysicalPath.ResolveExistingDirectory(isolatedPath);
        if (PhysicalPath.Contains(ordinary.CanonicalPath, isolated)
            || PhysicalPath.Contains(isolated, ordinary.CanonicalPath))
        {
            throw new CaptureException("save paths overlap");
        }
        SaveGame.PersistentDataPath = isolated;
        if (SaveGame.PersistentDataPath != isolated)
            throw new CaptureException("save redirect readback failed");
        isolatedCanonicalPath = isolated;
    }
    catch (CaptureException)
    {
        throw;
    }
    catch (Exception error)
    {
        throw new CaptureException("save redirect failed", error);
    }
}

internal bool VerifySavePath()
{
    if (isolatedCanonicalPath == null
        || SaveGame.PersistentDataPath != isolatedCanonicalPath)
    {
        return false;
    }
    try
    {
        return PhysicalPath.ResolveExistingDirectory(
            isolatedCanonicalPath) == isolatedCanonicalPath;
    }
    catch (OracleConfigurationException)
    {
        return false;
    }
}
```

The movement sub-boundary is exact:

Add these two methods to `GameAdapter`; they consume the Core-owned
`CaptureException` defined above:

```csharp
internal bool MovementScheduled(GameState state)
{
    if (state == null)
        throw new CaptureException("missing game state");
    try
    {
        return state.Moving();
    }
    catch (Exception error)
    {
        throw new CaptureException("movement observation failed", error);
    }
}

internal bool CurrentMovementScheduled(Game game)
{
    if (game == null)
        throw new CaptureException("missing game");
    GameState state;
    try
    {
        state = game.gamestate;
    }
    catch (Exception error)
    {
        throw new CaptureException("state observation failed", error);
    }
    return MovementScheduled(state);
}
```

Use the following as the complete `GameAdapter.cs`; it replaces the
incremental snippets above:

Create `GameAdapter.cs` with this complete implementation and use it verbatim
at GREEN:

```csharp
using System;
using System.Globalization;
using System.Reflection;
using System.Runtime.CompilerServices;

internal sealed class GameAdapter
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

    internal void AuthenticateAndRedirectSavePath(string isolatedPath)
    {
        try
        {
            string home = Environment.GetEnvironmentVariable("HOME");
            if (String.IsNullOrEmpty(home) || SaveGame.homePath != home)
                throw new CaptureException("ordinary HOME authentication failed");
            string expectedOrdinary = home
                + "/Library/Application Support/unity.increpare games/Sausage";
            if (SaveGame.PersistentDataPath != expectedOrdinary)
                throw new CaptureException("ordinary save path changed");
            PhysicalPathIdentity ordinary =
                PhysicalPath.ResolvePossiblyAbsent(expectedOrdinary);
            string isolated = PhysicalPath.ResolveExistingDirectory(isolatedPath);
            if (PhysicalPath.Contains(ordinary.CanonicalPath, isolated)
                || PhysicalPath.Contains(isolated, ordinary.CanonicalPath))
                throw new CaptureException("save paths overlap");
            SaveGame.PersistentDataPath = isolated;
            if (SaveGame.PersistentDataPath != isolated)
                throw new CaptureException("save redirect readback failed");
            isolatedCanonicalPath = isolated;
        }
        catch (CaptureException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw new CaptureException("save redirect failed", error);
        }
    }

    internal bool VerifySavePath()
    {
        if (isolatedCanonicalPath == null
            || SaveGame.PersistentDataPath != isolatedCanonicalPath)
            return false;
        try
        {
            return PhysicalPath.ResolveExistingDirectory(
                isolatedCanonicalPath) == isolatedCanonicalPath;
        }
        catch (OracleConfigurationException)
        {
            return false;
        }
    }

    internal bool TryGetState(Game game, out object stateReference)
    {
        stateReference = null;
        if (game == null)
            return false;
        try
        {
            GameState state = game.gamestate;
            if (state == null)
                return false;
            stateReference = state;
            return true;
        }
        catch (Exception error)
        {
            throw new CaptureException("state observation failed", error);
        }
    }

    internal bool MovementScheduled(GameState state)
    {
        if (state == null)
            throw new CaptureException("missing game state");
        try
        {
            return state.Moving();
        }
        catch (Exception error)
        {
            throw new CaptureException("movement observation failed", error);
        }
    }

    internal bool CurrentMovementScheduled(Game game)
    {
        if (game == null)
            throw new CaptureException("missing game");
        GameState state;
        try
        {
            state = game.gamestate;
        }
        catch (Exception error)
        {
            throw new CaptureException("state observation failed", error);
        }
        return MovementScheduled(state);
    }

    internal bool IsQuiescent(Game game, GameState state)
    {
        if (game == null || state == null)
            return false;
        try
        {
            if (state.worldsausagespawns == null)
                throw new CaptureException("world sausage list is null");
            bool menuInactive = game.escmenu == null
                || !game.escmenu.activeSelf;
            GameGateValues values = new GameGateValues(
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
                menuInactive,
                GameState.shouldredrawcoffins == Coord.Invalid,
                state.worldsausagespawns.Count == 0);
            return GameObservationPolicy.IsQuiescent(values);
        }
        catch (CaptureException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw new CaptureException("quiescence observation failed", error);
        }
    }

    internal CaptureRecord Capture(GameState state)
    {
        if (state == null)
            throw new CaptureException("missing game state");
        try
        {
            if (state.player == null
                || state.movements == null || state.worldsausagespawns == null)
                throw new CaptureException("required capture member is null");
            string rawSave = state.Save(false, false);
            if (rawSave == null)
                throw new CaptureException("raw save is null");
            return CaptureMapping.Create(new CaptureValues(
                rawSave,
                RuntimeHelpers.GetHashCode(state).ToString(
                    CultureInfo.InvariantCulture),
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
        catch (CaptureException)
        {
            throw;
        }
        catch (Exception error)
        {
            throw new CaptureException("game-state capture failed", error);
        }
    }
}
```

The Core-only harness does not compile `GameAdapter.cs`; the real net35 plugin
build and first plugin-artifact test below are its compile and semantic gates.
This task proves Unity pseudo-null, `activeSelf`, `Save(false, false)` argument
constants, and absence of `GameState.Lost()`. Task 9.2 adds the two exclusive
controller-to-adapter movement caller checks when that caller exists.

- [ ] **Step 4: Run every GREEN gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort observation
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort assembly \
  --assembly "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
if test ! -f oracle/plugin/obj/project.assets.json; then
  /opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
    oracle/plugin/SsrOracle.Plugin.csproj \
    --source "$PWD/data/oracle/compat/feed" \
    -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
    -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
fi
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

Require the exact success line from all three harness runs and a successful
real plugin build. Retain the Task 7.3-only diff plus all three GREEN outputs
in the task report. Its post-commit review is fresh; Task 7.1 or 7.2 approval
does not carry forward.

- [ ] **Step 5: Commit only the adapter surface**

```bash
git diff --check
git add oracle/plugin/GameAdapter.cs \
  oracle/plugin/tests/AssemblySurfaceTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: add passive game adapter"
```

### Track 8: Implement Unity-free patch firewalls and startup policy

**Files:**
- Create: `oracle/plugin/Core/PatchBoundary.cs`
- Create: `oracle/plugin/Core/PassiveStartup.cs`
- Create: `oracle/plugin/Core/PluginModePolicy.cs`
- Create: `oracle/plugin/tests/PatchBoundaryTests.cs`
- Create: `oracle/plugin/tests/PassiveStartupTests.cs`
- Create: `oracle/plugin/tests/PluginModePolicyTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Produces exactly these `PatchBoundary` methods:

```text
internal static void Observe(Action callback, Action observerFailed);
internal static Exception Finalize(
    HookToken token,
    Exception original,
    Action<HookToken> clear,
    Action gameMethodFailed,
    Action observerFailed);
internal static Exception FinalizeUpdate(
    Exception original,
    Action gameMethodFailed,
    Action observerFailed);
```

- Produces Unity-free `PassiveStartup`, `PassiveStartupException`, and
  `IPassiveStartupServices`. The lifecycle API is
  `new PassiveStartup(IPassiveStartupServices services)`, single-use
  `bool Start(RunRecord run)`, and idempotent `Dispose()`.
- `IPassiveStartupServices` is exactly:

```csharp
internal interface IPassiveStartupServices
{
    void ValidateBeforeSink();
    void AuthenticateAndRedirectSave();
    PassiveDriver CreateDriver();
    void InstallPatches();
    void EmitBootMarker();
    void UnpatchSelf();
    void MarkerOnlyFailed(string code);
    void Diagnostic(string message);
}
```

  A returned driver is owned immediately; a factory failure must close any
  not-yet-returned sink itself. `Start` performs validation, redirect, driver
  acquisition, `driver.Prepare(run)`, patch installation, `driver.Activate()`,
  and boot marker in exactly that order. `Dispose` performs driver disable,
  owner-only unpatch, and driver disposal.

`PassiveStartupException.Code` is restricted to the eight marker-only startup
codes. `ValidateBeforeSink` may report `invalid_configuration`,
`invalid_assembly`, `invalid_reflection`, `invalid_path`, or `trace_exists`;
redirect reports `save_redirect_failed`; driver factory/open reports
`trace_exists` or `trace_io_failed`. These service methods must translate
their low-level failures to the declared typed exception before returning to
Core. Once a driver has returned, patch install maps to the record code
`patch_install_failed` and later unexpected owned-lifecycle/logger failure maps
to `observer_exception`; no marker-only startup code is put in an Error record.
- Produces `PluginModePolicy.StartOff(OracleConfiguration, Action
  validateLegacySurface, Action emitBootMarker)`. It accepts only Off, invokes
  exactly the two callbacks in order, preserves the identical legacy callback
  exception rather than translating it into a passive marker, and has no
  passive-service argument through which it could create a sink, redirect
  saves, or patch.

#### Task 8.1: Contain every patch callback and preserve game exceptions

- [ ] **Step 1: Create the complete five-test RED firewall cohort**

Create `PatchBoundaryTests.cs` exactly as follows, register it, and set the
temporary manifest row to `boundary=5`.  No test or product file in this task
references Unity, Harmony, BepInEx, `Game`, or `GameState`.

```csharp
using System;
using System.Collections.Generic;

internal static class PatchBoundaryTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("boundary", "postfix contains observer failures", ObserveContainsFailures);
        tests.Add("boundary", "game exception claims before cleanup", GameFailurePrecedesCleanup);
        tests.Add("boundary", "successful postfix makes finalizer cleanup inert", ConsumedTokenIsInert);
        tests.Add("boundary", "cleanup failure is contained and reported", CleanupFailureIsContained);
        tests.Add("boundary", "update finalizer preserves original reference", UpdateFinalizerPreservesOriginalException);
    }

    private static void ObserveContainsFailures()
    {
        int failed = 0;
        PatchBoundary.Observe(
            delegate { throw new InvalidOperationException("observer"); },
            delegate { failed++; throw new InvalidOperationException("reporter"); });
        Check.Equal(1, failed, "one contained observer-failure callback");
        PatchBoundary.Observe(delegate { }, delegate { failed++; });
        Check.Equal(1, failed, "successful postfix does not report failure");
    }

    private static void GameFailurePrecedesCleanup()
    {
        object owner = new object();
        HookToken token = HookToken.Issued(owner, 1L, HookKind.Restart);
        Exception original = new InvalidOperationException("game");
        List<string> events = new List<string>();
        Exception returned = PatchBoundary.Finalize(
            token,
            original,
            delegate(HookToken value)
            {
                events.Add("clear");
                Check.True(value.TryConsume(), "active token clears once");
            },
            delegate { events.Add("game"); },
            delegate { events.Add("observer"); });
        Check.Same(original, returned, "original exception identity");
        Check.Sequence(
            new string[] { "game", "clear" },
            events.ToArray(),
            "game fault wins before balancing cleanup");
    }

    private static void ConsumedTokenIsInert()
    {
        HookToken token = HookToken.Issued(
            new object(), 2L, HookKind.ProcessInput);
        Check.True(token.TryConsume(), "ordinary postfix consumes token");
        int clears = 0;
        Exception returned = PatchBoundary.Finalize(
            token,
            null,
            delegate(HookToken value)
            {
                if (value.TryConsume())
                    clears++;
            },
            delegate { throw new InvalidOperationException("not called"); },
            delegate { throw new InvalidOperationException("not called"); });
        Check.True(returned == null, "null original preserved");
        Check.Equal(0, clears, "normal-postfix token is a finalizer no-op");
    }

    private static void CleanupFailureIsContained()
    {
        HookToken token = HookToken.Issued(
            new object(), 3L, HookKind.Undo);
        int reported = 0;
        Exception returned = PatchBoundary.Finalize(
            token,
            null,
            delegate(HookToken value)
            {
                value.TryConsume();
                throw new InvalidOperationException("cleanup");
            },
            delegate { throw new InvalidOperationException("not called"); },
            delegate
            {
                reported++;
                throw new InvalidOperationException("contained reporter");
            });
        Check.True(returned == null, "null original after cleanup failure");
        Check.Equal(1, reported, "one contained cleanup report");
    }

    private static void UpdateFinalizerPreservesOriginalException()
    {
        Exception original = new InvalidOperationException("game failure");
        int gameFailures = 0;
        int observerFailures = 0;
        Exception returned = PatchBoundary.FinalizeUpdate(
            original,
            delegate { gameFailures++; },
            delegate { observerFailures++; });
        Check.Same(original, returned, "identical update exception");
        Check.Equal(1, gameFailures, "game failure callback");
        Check.Equal(0, observerFailures, "no observer failure");
        Check.True(
            PatchBoundary.FinalizeUpdate(
                null,
                delegate { throw new InvalidOperationException("not called"); },
                delegate { throw new InvalidOperationException("not called"); }) == null,
            "normal Update finalizer is inert");
    }
}
```

Run `--cohort boundary` and require RED from missing `PatchBoundary`, never a
missing SDK, package, fixture, or game DLL.

- [ ] **Step 2: Run the firewall RED**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort boundary
```

Require the failure to name the missing `PatchBoundary` product surface.

- [ ] **Step 3: Implement the closed firewall behavior**

Every boundary independently contains exceptions from the observed callback
and from either reporting callback. Reject null callbacks on construction/use
in ordinary Core code; no callback exception escapes a game patch. `Finalize`
treats an inert or already consumed token as a valid no-op and balances an
active token once. This makes both a failed prefix observer and an already
successful postfix finalizer-safe. No boundary writes a trace or logs directly.

Implement `PatchBoundary` with this exact contained control flow:

```csharp
using System;

internal static class PatchBoundary
{
    internal static void Observe(Action callback, Action observerFailed)
    {
        try
        {
            if (callback == null)
                throw new ArgumentNullException("callback");
            callback();
        }
        catch (Exception)
        {
            Try(observerFailed);
        }
    }

    internal static Exception Finalize(
        HookToken token,
        Exception original,
        Action<HookToken> clear,
        Action gameMethodFailed,
        Action observerFailed)
    {
        bool observerWorkFailed = false;
        if (original != null)
        {
            try
            {
                if (gameMethodFailed == null)
                    throw new ArgumentNullException("gameMethodFailed");
                gameMethodFailed();
            }
            catch (Exception)
            {
                observerWorkFailed = true;
            }
        }
        if (token != null && token.Active)
        {
            try
            {
                if (clear == null)
                    throw new ArgumentNullException("clear");
                clear(token);
            }
            catch (Exception)
            {
                observerWorkFailed = true;
            }
        }
        if (observerWorkFailed)
            Try(observerFailed);
        return original;
    }

    internal static Exception FinalizeUpdate(
        Exception original,
        Action gameMethodFailed,
        Action observerFailed)
    {
        if (original != null)
        {
            try
            {
                if (gameMethodFailed == null)
                    throw new ArgumentNullException("gameMethodFailed");
                gameMethodFailed();
            }
            catch (Exception)
            {
                Try(observerFailed);
            }
        }
        return original;
    }

    private static void Try(Action callback)
    {
        try
        {
            if (callback != null)
                callback();
        }
        catch (Exception)
        {
        }
    }
}
```

- [ ] **Step 4: Run GREEN and the net35 gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort boundary
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Require the exact five registrations and retain the pristine output for
post-commit review.

- [ ] **Step 5: Commit only the Task 8.1 firewall slice**

```bash
git add oracle/plugin/Core/PatchBoundary.cs \
  oracle/plugin/tests/PatchBoundaryTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: contain passive patch callbacks"
```

#### Task 8.2: Preserve Off mode without a passive capability

- [ ] **Step 1: Add the complete two-test RED Off-policy cohort**

Create `PluginModePolicyTests.cs` exactly as follows.  Its public surface makes
sink creation, save redirection, patching, and passive teardown impossible to
request from `StartOff`.

```csharp
using System;
using System.Collections.Generic;

internal static class PluginModePolicyTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("startup", "off invokes only legacy validation then boot", OffCallsAreExact);
        tests.Add("startup", "off preserves legacy failure identity", LegacyFailureIdentity);
    }

    private static void OffCallsAreExact()
    {
        OracleConfiguration off = new OracleConfiguration(
            OracleMode.Off, null);
        List<string> events = new List<string>();
        PluginModePolicy.StartOff(
            off,
            delegate { events.Add("legacy"); },
            delegate { events.Add("boot"); });
        Check.Sequence(
            new string[] { "legacy", "boot" },
            events.ToArray(),
            "Off has exactly two ordered effects");

        PassiveConfiguration values = new PassiveConfiguration(
            "/output", "passive-trace", "/save", 3, 600, 30);
        OracleConfiguration passive = new OracleConfiguration(
            OracleMode.Passive, values);
        OracleConfigurationException error =
            Check.Throws<OracleConfigurationException>(
                delegate
                {
                    PluginModePolicy.StartOff(
                        passive, delegate { }, delegate { });
                },
                "passive cannot enter Off policy");
        Check.Equal("invalid_mode", error.Code, "typed mode error");
    }

    private static void LegacyFailureIdentity()
    {
        OracleConfiguration off = new OracleConfiguration(
            OracleMode.Off, null);
        Exception injected = new InvalidOperationException("legacy");
        bool boot = false;
        Exception observed = Check.Throws<InvalidOperationException>(
            delegate
            {
                PluginModePolicy.StartOff(
                    off,
                    delegate { throw injected; },
                    delegate { boot = true; });
            },
            "legacy failure propagates unchanged");
        Check.Same(injected, observed, "legacy failure identity");
        Check.False(boot, "boot is not emitted after failed validation");
    }
}
```

- [ ] **Step 2: Run the Off-policy RED**

Run `--cohort startup` with the temporary manifest `startup=2` and require a
compiler RED naming `PluginModePolicy`; a package, SDK, fixture, or game-DLL
failure is not the intended RED.

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort startup
```

- [ ] **Step 3: Implement the capability-free Off policy**

Create `Core/PluginModePolicy.cs` exactly as follows. It references no
`IPassiveStartupServices`, `PassiveDriver`, Harmony, sink, or save-redirect
type; its only effects are its two supplied callbacks.

```csharp
using System;

internal static class PluginModePolicy
{
    internal static void StartOff(
        OracleConfiguration configuration,
        Action validateLegacySurface,
        Action emitBootMarker)
    {
        if (configuration == null)
            throw new ArgumentNullException("configuration");
        if (validateLegacySurface == null)
            throw new ArgumentNullException("validateLegacySurface");
        if (emitBootMarker == null)
            throw new ArgumentNullException("emitBootMarker");
        if (configuration.Mode != OracleMode.Off)
        {
            throw new OracleConfigurationException(
                "invalid_mode",
                new ArgumentException("Mode-off policy requires off mode"));
        }
        validateLegacySurface();
        emitBootMarker();
    }
}
```

- [ ] **Step 4: Run GREEN and the net35 gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort startup
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Require both tests and retain the pristine output for post-commit review.

- [ ] **Step 5: Commit only the Task 8.2 Off-policy slice**

```bash
git add oracle/plugin/Core/PluginModePolicy.cs \
  oracle/plugin/tests/PluginModePolicyTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: preserve off-mode startup"
```

#### Task 8.3: Order passive ownership from Run flush through teardown

- [ ] **Step 1: Write the complete five-test RED passive-startup cohort**

Create `PassiveStartupTests.cs` with this complete cohort.  The fakes use the
real driver, so the tests prove ownership transfer and marker arbitration
without private-state mutation.

```csharp
using System;
using System.Collections.Generic;

internal static class PassiveStartupTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("startup", "run flush precedes patches and activation precedes boot", StartOrder);
        tests.Add("startup", "typed pre-driver failures stay marker only", PreDriverFailures);
        tests.Add("startup", "prepare failure is not reported twice", PrepareFailure);
        tests.Add("startup", "owned startup failures use driver arbitration", OwnedFailures);
        tests.Add("startup", "teardown is ordered and idempotent", TeardownIsIdempotent);
    }

    private static void StartOrder()
    {
        FakeStartupServices services = new FakeStartupServices();
        PassiveStartup startup = new PassiveStartup(services);
        Check.True(startup.Start(ProtocolSamples.Run), "startup succeeds");
        Check.Sequence(
            new string[]
            {
                "validate", "redirect", "create-driver", "sink:run",
                "install:Disabled", "boot:AwaitGame"
            },
            services.Events.ToArray(),
            "startup order");
        Check.Throws<InvalidOperationException>(
            delegate { startup.Start(ProtocolSamples.Run); },
            "startup is single-use");
    }

    private static void PreDriverFailures()
    {
        StartupFailureCase[] cases = new StartupFailureCase[]
        {
            new StartupFailureCase("validate", "invalid_configuration"),
            new StartupFailureCase("validate", "invalid_assembly"),
            new StartupFailureCase("validate", "invalid_reflection"),
            new StartupFailureCase("validate", "invalid_path"),
            new StartupFailureCase("validate", "trace_exists"),
            new StartupFailureCase("redirect", "save_redirect_failed"),
            new StartupFailureCase("create-driver", "trace_exists"),
            new StartupFailureCase("create-driver", "trace_io_failed")
        };
        for (int index = 0; index < cases.Length; index++)
        {
            FakeStartupServices services = new FakeStartupServices();
            services.FailureStage = cases[index].Stage;
            services.FailureCode = cases[index].Code;
            PassiveStartup startup = new PassiveStartup(services);
            Check.False(startup.Start(ProtocolSamples.Run), "typed failure");
            Check.Equal(0, services.Sink.RunCount, "no Run before ownership");
            Check.Equal(1, services.MarkerFailures.Count, "one marker");
            Check.Equal(cases[index].Code, services.MarkerFailures[0], "exact marker");
            Check.False(services.Events.Contains("install:Disabled"), "no patch install");
            if (cases[index].Stage == "validate")
            {
                Check.False(services.Events.Contains("redirect"),
                    "validation failure precedes save redirect");
                Check.False(services.Events.Contains("create-driver"),
                    "validation failure precedes driver creation");
            }
            Check.Equal(
                cases[index].Stage == "create-driver" ? 1 : 0,
                services.Sink.CloseCount,
                "factory closes only its unreturned sink");
        }
    }

    private static void PrepareFailure()
    {
        FakeStartupServices services = new FakeStartupServices();
        services.Sink.ThrowOnRun = true;
        PassiveStartup startup = new PassiveStartup(services);
        Check.False(startup.Start(ProtocolSamples.Run), "prepare fails");
        Check.Equal(0, services.MarkerFailures.Count, "startup adds no marker");
        Check.Sequence(
            new string[] { "trace_io_failed" },
            services.Reporter.Failures.ToArray(),
            "driver owns sole marker");
        Check.False(services.Events.Contains("install:Disabled"), "no patches");
    }

    private static void OwnedFailures()
    {
        AssertOwnedFailure("install", "patch_install_failed");
        AssertOwnedFailure("activate", "observer_exception");
        AssertOwnedFailure("boot", "observer_exception");
    }

    private static void AssertOwnedFailure(string stage, string code)
    {
        FakeStartupServices services = new FakeStartupServices();
        services.OwnedFailureStage = stage;
        PassiveStartup startup = new PassiveStartup(services);
        Check.False(startup.Start(ProtocolSamples.Run), stage + " fails");
        Check.Equal(1, services.Sink.ErrorCodes.Count, stage + " one Error");
        Check.Equal(code, services.Sink.ErrorCodes[0], stage + " Error code");
        Check.Equal(1, services.Reporter.Failures.Count, stage + " one marker");
        Check.Equal(code, services.Reporter.Failures[0], stage + " marker code");
        Check.Equal(1, Count(services.Events, "unpatch"), stage + " one unpatch");
    }

    private static void TeardownIsIdempotent()
    {
        FakeStartupServices services = new FakeStartupServices();
        PassiveStartup startup = new PassiveStartup(services);
        Check.True(startup.Start(ProtocolSamples.Run), "startup succeeds");
        startup.Dispose();
        startup.Dispose();
        Check.Equal(1, Count(services.Events, "unpatch"), "one owner unpatch");
        Check.Equal(1, services.Sink.CloseCount, "one driver close");
        Check.Equal(0, services.Sink.EndCount, "teardown invents no End");
        Check.Equal(0, services.Sink.ErrorCodes.Count, "teardown invents no Error");
        Check.Equal(0, services.Reporter.Failures.Count, "teardown invents no marker");
    }

    private static int Count(List<string> values, string expected)
    {
        int count = 0;
        for (int index = 0; index < values.Count; index++)
        {
            if (values[index] == expected)
                count++;
        }
        return count;
    }

    private sealed class StartupFailureCase
    {
        internal StartupFailureCase(string stage, string code)
        {
            Stage = stage;
            Code = code;
        }
        internal string Stage;
        internal string Code;
    }

    private sealed class FakeStartupServices : IPassiveStartupServices
    {
        internal readonly List<string> Events = new List<string>();
        internal readonly FakeStartupSink Sink;
        internal readonly FakeStartupReporter Reporter;
        internal readonly PassiveDriver Driver;
        internal readonly List<string> MarkerFailures = new List<string>();
        internal string FailureStage;
        internal string FailureCode;
        internal string OwnedFailureStage;

        internal FakeStartupServices()
        {
            Sink = new FakeStartupSink(Events);
            Reporter = new FakeStartupReporter(Events);
            Driver = new PassiveDriver(Sink, Reporter, 3, 600, 30.0);
        }

        public void ValidateBeforeSink()
        {
            Events.Add("validate");
            ThrowTyped("validate");
        }

        public void AuthenticateAndRedirectSave()
        {
            Events.Add("redirect");
            ThrowTyped("redirect");
        }

        public PassiveDriver CreateDriver()
        {
            Events.Add("create-driver");
            if (FailureStage == "create-driver")
            {
                Driver.Dispose();
                throw new PassiveStartupException(
                    FailureCode,
                    new InvalidOperationException("create-driver"));
            }
            return Driver;
        }

        public void InstallPatches()
        {
            Events.Add("install:" + Driver.Phase.ToString());
            if (OwnedFailureStage == "activate")
            {
                Check.True(Driver.Activate(),
                    "injected early activation succeeds once");
            }
            if (OwnedFailureStage == "install")
                throw new InvalidOperationException("install");
        }

        public void EmitBootMarker()
        {
            Events.Add("boot:" + Driver.Phase.ToString());
            if (OwnedFailureStage == "boot")
                throw new InvalidOperationException("boot");
        }

        public void UnpatchSelf() { Events.Add("unpatch"); }

        public void MarkerOnlyFailed(string code)
        {
            MarkerFailures.Add(code);
            Events.Add("marker:" + code);
        }

        public void Diagnostic(string message)
        {
            Events.Add("diagnostic:" + message);
        }

        private void ThrowTyped(string stage)
        {
            if (FailureStage == stage)
            {
                throw new PassiveStartupException(
                    FailureCode, new InvalidOperationException(stage));
            }
        }
    }

    private sealed class FakeStartupSink : ITraceSink
    {
        private readonly List<string> events;
        internal bool ThrowOnRun;
        internal int RunCount;
        internal int EndCount;
        internal int CloseCount;
        internal readonly List<string> ErrorCodes = new List<string>();

        internal FakeStartupSink(List<string> events) { this.events = events; }

        public void WriteRun(RunRecord record)
        {
            RunCount++;
            events.Add(ThrowOnRun ? "sink:run:throw" : "sink:run");
            if (ThrowOnRun)
                throw new TraceIoException("injected Run failure");
        }
        public void WriteInitial(InitialRecord record) { events.Add("sink:initial"); }
        public void WriteStep(StepRecord record) { events.Add("sink:step"); }
        public void WriteEnd(EndRecord record) { EndCount++; events.Add("sink:end"); }
        public void WriteError(ErrorRecord record)
        {
            ErrorCodes.Add(record.Code);
            events.Add("sink:error:" + record.Code);
        }
        public void Close() { CloseCount++; events.Add("sink:close"); }
    }

    private sealed class FakeStartupReporter : IPassiveReporter
    {
        private readonly List<string> events;
        internal readonly List<string> Failures = new List<string>();
        internal FakeStartupReporter(List<string> events) { this.events = events; }
        public void Ready(int completedInputs) { events.Add("report:ready"); }
        public void Complete() { events.Add("report:complete"); }
        public void Failed(string code)
        {
            Failures.Add(code);
            events.Add("report:failed:" + code);
        }
        public void Diagnostic(string message) { events.Add("diagnostic:" + message); }
    }
}
```

Register `PluginModePolicyTests` followed by `PassiveStartupTests`, update the
temporary manifest to `startup=7`, run the cohort, and require RED from the
missing startup behavior.

- [ ] **Step 2: Run RED for the missing passive-startup lifecycle**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort startup
```

Require a named Task 8.3 startup test to fail for the absent
`PassiveStartup` behavior; the two retained Off-policy tests must pass.

- [ ] **Step 3: Implement passive startup ownership and teardown**

`Start` rejects a second call. Before driver acquisition it catches only the
typed `PassiveStartupException`, calls `MarkerOnlyFailed(error.Code)` once,
and returns false. The service contract forbids an untyped low-level failure;
tests inject every declared typed failure. After ownership transfers, call
`Prepare`; on false return without another marker. Install patches while
`Phase==Disabled`; only then call `Activate`. Patch-install exceptions call
`TryFault("patch_install_failed")`; any unexpected owned-driver activation or
boot callback exception calls `TryFault("observer_exception")`. Cleanup always
disables before owner-only unpatch, and later cleanup/report failures cannot
replace the first terminal winner.

Create the complete `Core/PassiveStartup.cs` file with this exact declaration
order and exact code. The interface is first, followed by the typed exception
and lifecycle; do not prepend or append another declaration to this file:

```csharp
using System;

internal interface IPassiveStartupServices
{
    void ValidateBeforeSink();
    void AuthenticateAndRedirectSave();
    PassiveDriver CreateDriver();
    void InstallPatches();
    void EmitBootMarker();
    void UnpatchSelf();
    void MarkerOnlyFailed(string code);
    void Diagnostic(string message);
}

internal sealed class PassiveStartupException : Exception
{
    internal PassiveStartupException(string code, Exception inner)
        : base(code, inner)
    {
        if (code != "invalid_mode"
            && code != "invalid_configuration"
            && code != "invalid_assembly"
            && code != "invalid_reflection"
            && code != "invalid_path"
            && code != "trace_exists"
            && code != "save_redirect_failed"
            && code != "trace_io_failed")
        {
            throw new ArgumentException("invalid startup code", "code");
        }
        Code = code;
    }

    internal string Code { get; private set; }
}

internal sealed class PassiveStartup : IDisposable
{
    private readonly IPassiveStartupServices services;
    private PassiveDriver driver;
    private bool started;
    private bool patchesMayExist;
    private bool disposed;

    internal PassiveStartup(IPassiveStartupServices services)
    {
        this.services = services
            ?? throw new ArgumentNullException("services");
    }

    internal bool Start(RunRecord run)
    {
        if (started)
            throw new InvalidOperationException("startup already attempted");
        if (run == null)
            throw new ArgumentNullException("run");
        started = true;
        try
        {
            services.ValidateBeforeSink();
            services.AuthenticateAndRedirectSave();
            driver = services.CreateDriver();
            if (driver == null)
            {
                throw new PassiveStartupException(
                    "trace_io_failed",
                    new InvalidOperationException("driver factory returned null"));
            }
        }
        catch (PassiveStartupException error)
        {
            SafeMarker(error.Code);
            return false;
        }

        if (!driver.Prepare(run))
            return false;

        patchesMayExist = true;
        try
        {
            services.InstallPatches();
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
            OwnedFailure("patch_install_failed");
            return false;
        }

        try
        {
            if (!driver.Activate())
                throw new InvalidOperationException("driver activation failed");
            services.EmitBootMarker();
            return true;
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
            OwnedFailure("observer_exception");
            return false;
        }
    }

    public void Dispose()
    {
        if (disposed)
            return;
        disposed = true;
        SafeDisable();
        SafeUnpatch();
        if (driver != null)
        {
            try
            {
                driver.Dispose();
            }
            catch (Exception error)
            {
                SafeDiagnostic(error);
            }
        }
    }

    private void OwnedFailure(string code)
    {
        try
        {
            driver.TryFault(code);
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
        SafeDisable();
        SafeUnpatch();
    }

    private void SafeDisable()
    {
        if (driver == null)
            return;
        try
        {
            driver.Disable();
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeUnpatch()
    {
        if (!patchesMayExist)
            return;
        patchesMayExist = false;
        try
        {
            services.UnpatchSelf();
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeMarker(string code)
    {
        try
        {
            services.MarkerOnlyFailed(code);
        }
        catch (Exception error)
        {
            SafeDiagnostic(error);
        }
    }

    private void SafeDiagnostic(Exception error)
    {
        try
        {
            services.Diagnostic(error.GetType().FullName);
        }
        catch (Exception)
        {
        }
    }
}
```

- [ ] **Step 4: Run GREEN and the net35 gate**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort startup
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

Require `startup=7` and retain the pristine output for post-commit review.

- [ ] **Step 5: Commit only the Task 8.3 startup slice**

```bash
git add oracle/plugin/Core/PassiveStartup.cs \
  oracle/plugin/tests/PassiveStartupTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: order passive resource startup"
```

### Track 9: Wire the thin Harmony, controller, and plugin shell

**Files:**
- Create: `oracle/plugin/Core/PassiveReporter.cs`
- Create: `oracle/plugin/PassivePatches.cs`
- Create: `oracle/plugin/PassiveController.cs`
- Create: `oracle/plugin/tests/PassiveReporterTests.cs`
- Modify: `oracle/plugin/Plugin.cs`
- Modify: `oracle/plugin/SsrOracle.Plugin.csproj`
- Modify: `oracle/plugin/tests/AssemblySurfaceTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Produces Harmony patches for the exact eight observed methods, all owned by
  `dev.jlsor.ssr.oracle.passive`.
- Produces one `PassiveController` that implements `IPassiveStartupServices`
  and `IPassiveReporter`, exposes single-use `bool Start(RunRecord run)`, hook
  forwarding, `TryFault`, `Disable`, and idempotent `Dispose`, and never calls
  an `ITraceSink` method directly. Its shell constructor is exactly
  `PassiveController(PassiveConfiguration configuration,
  BepInEx.Logging.ManualLogSource logger)`.
- `Plugin.Awake` selects Off or Passive from the typed byte load;
  `Plugin.OnDestroy` delegates ordered Core teardown and never invents
  completion.

`PassiveController.ValidateBeforeSink` repeats a two-pass physical proof that
the exact canonical output leaf is absent and maps an occupied leaf to
`trace_exists` before save redirection. `CreateDriver` still uses
`FileMode.CreateNew`; the earlier proof establishes startup ordering and the
later open remains the authoritative atomic ownership transition.

#### Task 9.1: Format the exact passive lifecycle markers

- [ ] **Step 1: Add the exact four-test reporter RED cohort**

Create `PassiveReporterTests.cs` with exactly four registrations: one table
test asserting all three Ready strings and rejecting `-1`/`3`; one completion
test; one table test asserting all fourteen record and eight marker-only
failure strings while rejecting `unknown`; and one diagnostic/null test.  The
complete test body is:

```csharp
using System;
using System.Collections.Generic;

internal sealed class FakePassiveLog : IPassiveLog
{
    internal readonly List<string> Events = new List<string>();
    public void Info(string message) { Events.Add("info:" + message); }
    public void Error(string message) { Events.Add("error:" + message); }
    public void Warning(string message) { Events.Add("warning:" + message); }
}

internal static class PassiveReporterTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("reporter", "ready markers are exact", ReadyMarkers);
        tests.Add("reporter", "completion marker is exact", CompletionMarker);
        tests.Add("reporter", "failure markers are closed", FailureMarkers);
        tests.Add("reporter", "diagnostic is nonterminal", DiagnosticMarker);
    }

    private static void ReadyMarkers()
    {
        FakePassiveLog log = new FakePassiveLog();
        PassiveLogReporter reporter = new PassiveLogReporter(log);
        reporter.Ready(0); reporter.Ready(1); reporter.Ready(2);
        Check.Sequence(new string[]
        {
            "info:SSR oracle passive trace ready: 0/3",
            "info:SSR oracle passive trace ready: 1/3",
            "info:SSR oracle passive trace ready: 2/3"
        }, log.Events.ToArray(), "ready markers");
        Check.Throws<ArgumentOutOfRangeException>(delegate { reporter.Ready(-1); },
            "negative ready");
        Check.Throws<ArgumentOutOfRangeException>(delegate { reporter.Ready(3); },
            "terminal ready belongs to completion");
    }

    private static void CompletionMarker()
    {
        FakePassiveLog log = new FakePassiveLog();
        new PassiveLogReporter(log).Complete();
        Check.Equal("info:SSR oracle passive trace complete", log.Events[0],
            "completion marker");
    }

    private static void FailureMarkers()
    {
        string[] codes = new string[]
        {
            "patch_install_failed", "input_before_initial", "overlapping_input",
            "unexpected_input", "unscoped_process_input", "hook_order_mismatch",
            "game_method_exception", "observer_exception", "capture_failed",
            "record_too_large", "initial_settle_timeout", "settle_timeout",
            "state_replaced", "save_path_changed", "invalid_mode",
            "invalid_configuration", "invalid_assembly", "invalid_reflection",
            "invalid_path", "trace_exists", "save_redirect_failed",
            "trace_io_failed"
        };
        FakePassiveLog log = new FakePassiveLog();
        PassiveLogReporter reporter = new PassiveLogReporter(log);
        for (int index = 0; index < codes.Length; index++)
        {
            reporter.Failed(codes[index]);
            Check.Equal("error:SSR oracle passive trace failed: " + codes[index],
                log.Events[index], "failure marker " + index);
        }
        Check.Throws<ArgumentException>(delegate { reporter.Failed("unknown"); },
            "unknown failure code");
    }

    private static void DiagnosticMarker()
    {
        FakePassiveLog log = new FakePassiveLog();
        PassiveLogReporter reporter = new PassiveLogReporter(log);
        reporter.Diagnostic("System.InvalidOperationException");
        Check.Equal(
            "warning:SSR oracle passive diagnostic: System.InvalidOperationException",
            log.Events[0], "diagnostic marker");
        Check.Throws<ArgumentNullException>(delegate { reporter.Diagnostic(null); },
            "null diagnostic");
    }
}
```

- [ ] **Step 2: Run RED for the missing reporter implementation**

Set the cumulative manifest row to `reporter=4`, register the test class, and
run the selected cohort. Require a compiler RED naming `PassiveLogReporter`.

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort reporter
```

- [ ] **Step 3: Implement the exact Core-owned marker formatter**

Create `Core/PassiveReporter.cs` with the exact real marker formatter below.
The controller's BepInEx adapter implements only `IPassiveLog`; therefore all
marker validation and spelling remain net35-testable Core code.

```csharp
using System;
using System.Globalization;

internal interface IPassiveLog
{
    void Info(string message);
    void Error(string message);
    void Warning(string message);
}

internal sealed class PassiveLogReporter : IPassiveReporter
{
    private readonly IPassiveLog log;

    internal PassiveLogReporter(IPassiveLog log)
    {
        this.log = log ?? throw new ArgumentNullException("log");
    }

    public void Ready(int completedInputs)
    {
        if (completedInputs < 0
            || completedInputs >= OracleProtocol.ExpectedInputCount)
            throw new ArgumentOutOfRangeException("completedInputs");
        log.Info("SSR oracle passive trace ready: "
            + completedInputs.ToString(CultureInfo.InvariantCulture) + "/3");
    }

    public void Complete()
    {
        log.Info("SSR oracle passive trace complete");
    }

    public void Failed(string code)
    {
        if (!OracleErrors.IsRecordCode(code)
            && !OracleMarkerErrors.IsMarkerOnly(code))
            throw new ArgumentException("unknown passive failure code", "code");
        log.Error("SSR oracle passive trace failed: " + code);
    }

    public void Diagnostic(string message)
    {
        if (message == null)
            throw new ArgumentNullException("message");
        log.Warning("SSR oracle passive diagnostic: " + message);
    }
}
```

- [ ] **Step 4: Run GREEN and the net35 gate**

Run `--cohort reporter` plus the net35 Core gate, require all four exact tests,
run the diff check, and retain the output for post-commit review:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort reporter
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
git diff --check
```

- [ ] **Step 5: Commit only the Task 9.1 reporter slice**

```bash
git add oracle/plugin/Core/PassiveReporter.cs \
  oracle/plugin/tests/PassiveReporterTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: report passive oracle lifecycle"
```

#### Task 9.2: Enforce path and identity authorization before capture

- [ ] **Step 1: Add the controller-boundary RED registration**

Replace only `AssemblySurfaceTests.Register` with this cumulative block and
raise the plugin manifest row from `plugin=1` to `plugin=2`.  The adapter test
from Task 7.3 remains a regression; the one new controller test proves the
invariant boundary and the two exclusive controller-to-adapter movement call
sites.

```csharp
internal static void Register(TestRegistry tests, HarnessOptions options)
{
    tests.Add("assembly", "pinned Assembly-CSharp hash",
        delegate { PinnedHash(options.AssemblyPath); });
    tests.Add("assembly", "exact ten observed methods",
        delegate { ExactObservedMethods(options.AssemblyPath); });
    tests.Add("assembly", "exact required game fields",
        delegate { ExactRequiredFields(options.AssemblyPath); });
    tests.Add("assembly", "metadata matcher rejects near misses",
        SyntheticMatcherRejectsNearMisses);
    tests.Add("plugin", "game adapter call surface is passive",
        delegate { AdapterCallSurface(options.PluginPath); });
    tests.Add("plugin", "controller crosses authorized update boundary",
        delegate { ControllerUsesAuthorizedBoundary(options.PluginPath); });
}
```

- [ ] **Step 2: Build the pre-controller artifact and run semantic RED**

Build the Task 9.1 artifact before creating `PassiveController.cs`, then run
the cumulative plugin cohort and require the named controller registration to
fail because `PassiveController` is absent.  The adapter registration must
still pass; a build, asset, or decoder failure is not the intended RED.

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

- [ ] **Step 3: Implement issued-authorized-consumed controller forwarding**

The Core-owned `PassiveUpdateBoundary` is the behavioral seam behind the new
plugin test. Its fake `IPassiveUpdateObservation` proves the ordered calls
`state, now, path, state, gate, capture, utc` through the static call-sequence
check plus per-operation counters: a false path stops at `path`, and a
different second state stops after the second `state`. Both cases assert zero
quiescence and capture calls and the exact driver fault. Implement the
controller's game-backed observation and normal Update body with this exact
control flow:

```csharp
private sealed class GameUpdateObservation : IPassiveUpdateObservation
{
    private readonly PassiveController owner;
    private readonly Game game;

    internal GameUpdateObservation(PassiveController owner, Game game)
    {
        this.owner = owner ?? throw new ArgumentNullException("owner");
        this.game = game;
    }

    public bool TryGetState(out object stateReference)
    {
        return owner.adapter.TryGetState(game, out stateReference);
    }

    public bool VerifySavePath() { return owner.adapter.VerifySavePath(); }
    public bool IsQuiescent(object stateReference)
    {
        GameState state = stateReference as GameState;
        if (state == null)
            throw new CaptureException("verified game state is missing");
        return owner.adapter.IsQuiescent(game, state);
    }
    public CaptureRecord Capture(object stateReference)
    {
        GameState state = stateReference as GameState;
        if (state == null)
            throw new CaptureException("verified game state is missing");
        return owner.adapter.Capture(state);
    }
    public double NowSeconds() { return owner.NowSeconds(); }
    public DateTime UtcNow() { return DateTime.UtcNow; }
}

internal void ObserveUpdate(Game game)
{
    updateBoundary.Observe(new GameUpdateObservation(this, game));
}
```

Thus every active directive follows the issued -> authorized -> consumed state
machine.  `BeginUpdate` performs deadline/frame accounting.  The boundary then
calls `VerifySavePath`, rereads state identity, and calls `AuthorizeUpdate`.
Only an authorized directive may call `IsQuiescent` or `Capture`; only that
same verified state reference is passed into those calls.  The plugin
metadata/IL cohort requires `PassiveUpdateBoundary.Observe` and forbids direct
controller calls to `GameAdapter.IsQuiescent`, `GameAdapter.Capture`,
`PassiveDriver.CompleteUpdate`, or the removed `RejectUpdate` API.

The normal `ProcessInput` postfix calls
`adapter.MovementScheduled(__instance)` immediately only for an active manual
token and then forwards the bool to `driver.ProcessInputReturned`. The normal
top-level Undo postfix similarly calls
`adapter.CurrentMovementScheduled(__instance)` only for an active Undo token
and forwards it to `driver.UndoReturned`. Inert tokens from automatic input,
nested Restart bookkeeping, or an already rejected prefix are forwarded
directly to the driver without an adapter read. On a typed adapter failure,
consume/balance that hook token first, then call
`TryFault("capture_failed")`; do not let a successful original's finalizer
misclassify it as `game_method_exception`. No other file calls either movement
API, `Capture`, or `Save(false, false)`.

Use these exact controller postfix methods:

```csharp
internal void ProcessInputReturned(
    GameState state,
    bool accepted,
    HookToken token)
{
    if (token == null || !token.Active)
    {
        driver.ProcessInputReturned(token, accepted, false);
        return;
    }
    bool movement;
    try
    {
        movement = adapter.MovementScheduled(state);
    }
    catch (CaptureException)
    {
        driver.ProcessInputThrew(token);
        driver.TryFault("capture_failed");
        return;
    }
    driver.ProcessInputReturned(token, accepted, movement);
}

internal void UndoReturned(Game game, HookToken token)
{
    if (token == null || !token.Active)
    {
        driver.UndoReturned(token, false);
        return;
    }
    bool movement;
    try
    {
        movement = adapter.CurrentMovementScheduled(game);
    }
    catch (CaptureException)
    {
        driver.UndoThrew(token);
        driver.TryFault("capture_failed");
        return;
    }
    driver.UndoReturned(token, movement);
}
```

Create `PassiveController.cs` from this complete file; it replaces the three
incremental controller snippets above and supplies every startup-service,
reporter, forwarding, finalizer, and ownership body:

```csharp
using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using BepInEx.Logging;
using HarmonyLib;

internal sealed class PassiveController :
    IPassiveStartupServices, IPassiveReporter, IDisposable
{
    private sealed class BepInExLogTarget : IPassiveLog
    {
        private readonly ManualLogSource logger;
        internal BepInExLogTarget(ManualLogSource logger)
        {
            this.logger = logger ?? throw new ArgumentNullException("logger");
        }
        public void Info(string message) { logger.LogInfo(message); }
        public void Error(string message) { logger.LogError(message); }
        public void Warning(string message) { logger.LogWarning(message); }
    }

    private sealed class GameUpdateObservation : IPassiveUpdateObservation
    {
        private readonly PassiveController owner;
        private readonly Game game;

        internal GameUpdateObservation(PassiveController owner, Game game)
        {
            this.owner = owner ?? throw new ArgumentNullException("owner");
            this.game = game;
        }

        public bool TryGetState(out object stateReference)
        {
            return owner.adapter.TryGetState(game, out stateReference);
        }

        public bool VerifySavePath()
        {
            return owner.adapter.VerifySavePath();
        }

        public bool IsQuiescent(object stateReference)
        {
            GameState state = stateReference as GameState;
            if (state == null)
                throw new CaptureException("verified game state is missing");
            return owner.adapter.IsQuiescent(game, state);
        }

        public CaptureRecord Capture(object stateReference)
        {
            GameState state = stateReference as GameState;
            if (state == null)
                throw new CaptureException("verified game state is missing");
            return owner.adapter.Capture(state);
        }

        public double NowSeconds() { return owner.NowSeconds(); }
        public DateTime UtcNow() { return DateTime.UtcNow; }
    }

    internal const string HarmonyOwner = "dev.jlsor.ssr.oracle.passive";
    private static PassiveController instance;
    private readonly PassiveConfiguration configuration;
    private readonly ManualLogSource logger;
    private readonly PassiveLogReporter reporter;
    private readonly Stopwatch clock;
    private GameAdapter adapter;
    private Harmony harmony;
    private PassiveDriver driver;
    private PassiveUpdateBoundary updateBoundary;
    private PassiveStartup startup;
    private bool startAttempted;
    private bool disposed;

    internal PassiveController(
        PassiveConfiguration configuration,
        ManualLogSource logger)
    {
        this.configuration = configuration
            ?? throw new ArgumentNullException("configuration");
        this.logger = logger ?? throw new ArgumentNullException("logger");
        reporter = new PassiveLogReporter(new BepInExLogTarget(logger));
        clock = Stopwatch.StartNew();
    }

    internal static PassiveController Instance
    {
        get
        {
            if (instance == null)
                throw new InvalidOperationException("passive controller is unavailable");
            return instance;
        }
    }

    internal static void ObservePatch(
        Action<PassiveController> callback)
    {
        if (callback == null)
            return;
        PassiveController current = instance;
        if (current == null)
            return;
        PatchBoundary.Observe(
            delegate { callback(current); },
            current.ObserverFailed);
    }

    internal static Exception FinalizePatch(
        HookToken token,
        Exception original)
    {
        PassiveController current = instance;
        if (current == null)
            return original;
        try
        {
            current.ObserveFinalizer(token, original);
            return original;
        }
        catch (Exception)
        {
            PatchBoundary.Observe(current.ObserverFailed, null);
            return original;
        }
    }

    internal static Exception FinalizeUpdatePatch(Exception original)
    {
        PassiveController current = instance;
        if (current == null)
            return original;
        try
        {
            current.ObserveUpdateFinalizer(original);
            return original;
        }
        catch (Exception)
        {
            PatchBoundary.Observe(current.ObserverFailed, null);
            return original;
        }
    }

    internal bool Start(RunRecord run)
    {
        if (startAttempted)
            throw new InvalidOperationException("controller start already attempted");
        startAttempted = true;
        startup = new PassiveStartup(this);
        return startup.Start(run);
    }

    public void ValidateBeforeSink()
    {
        string assemblyPath = typeof(Game).Assembly.Location;
        string actual;
        try
        {
            using (SHA256 hash = SHA256.Create())
            using (FileStream stream = File.OpenRead(assemblyPath))
            {
                byte[] digest = hash.ComputeHash(stream);
                StringBuilder text = new StringBuilder(64);
                for (int index = 0; index < digest.Length; index++)
                    text.Append(digest[index].ToString("x2", CultureInfo.InvariantCulture));
                actual = text.ToString();
            }
        }
        catch (Exception error)
        {
            throw new PassiveStartupException("invalid_assembly", error);
        }
        if (actual != OracleProtocol.ExpectedAssemblySha256)
        {
            throw new PassiveStartupException(
                "invalid_assembly", new InvalidDataException("assembly hash mismatch"));
        }
        try
        {
            GameContract.ValidatePassiveSurface();
            adapter = new GameAdapter();
        }
        catch (Exception error)
        {
            throw new PassiveStartupException("invalid_reflection", error);
        }
        try
        {
            string leaf = configuration.RunName + ".ndjson";
            string expected = Path.Combine(
                configuration.OutputDirectory, leaf);
            string proved = PhysicalPath.RequireAbsentLeaf(
                configuration.OutputDirectory, leaf);
            if (proved != expected)
            {
                throw new OracleConfigurationException(
                    "invalid_path",
                    new InvalidDataException("trace target spelling mismatch"));
            }
        }
        catch (TraceExistsException error)
        {
            throw new PassiveStartupException("trace_exists", error);
        }
        catch (OracleConfigurationException error)
        {
            throw new PassiveStartupException("invalid_path", error);
        }
        catch (Exception error)
        {
            throw new PassiveStartupException("invalid_path", error);
        }
        // This ordered absence proof precedes save redirection. CreateDriver's
        // FileMode.CreateNew remains the authoritative atomic recheck.
    }

    public void AuthenticateAndRedirectSave()
    {
        try
        {
            adapter.AuthenticateAndRedirectSavePath(configuration.SaveDirectory);
        }
        catch (Exception error)
        {
            throw new PassiveStartupException("save_redirect_failed", error);
        }
    }

    public PassiveDriver CreateDriver()
    {
        ITraceSink sink = null;
        try
        {
            sink = NdjsonTraceSink.Create(
                configuration.OutputDirectory, configuration.RunName);
            PassiveDriver created = new PassiveDriver(
                sink, this, configuration.ExpectedPassiveInputs,
                configuration.MaxSettleFrames,
                (double)configuration.MaxSettleSeconds);
            PassiveUpdateBoundary createdBoundary =
                new PassiveUpdateBoundary(created);
            driver = created;
            updateBoundary = createdBoundary;
            sink = null;
            return created;
        }
        catch (TraceExistsException error)
        {
            CloseUnownedSink(sink);
            throw new PassiveStartupException("trace_exists", error);
        }
        catch (TraceIoException error)
        {
            CloseUnownedSink(sink);
            throw new PassiveStartupException("trace_io_failed", error);
        }
        catch (Exception error)
        {
            CloseUnownedSink(sink);
            throw new PassiveStartupException("trace_io_failed", error);
        }
    }

    private static void CloseUnownedSink(ITraceSink sink)
    {
        if (sink == null)
            return;
        try
        {
            sink.Close();
        }
        catch (Exception)
        {
        }
    }

    public void InstallPatches()
    {
        if (instance != null)
            throw new InvalidOperationException("another passive controller is active");
        instance = this;
        harmony = new Harmony(HarmonyOwner);
        harmony.PatchAll(typeof(PassiveController).Assembly);
    }

    public void EmitBootMarker()
    {
        logger.LogInfo("SSR oracle boot probe loaded");
    }

    public void UnpatchSelf()
    {
        try
        {
            if (harmony != null)
                harmony.UnpatchSelf();
        }
        finally
        {
            harmony = null;
            if (Object.ReferenceEquals(instance, this))
                instance = null;
        }
    }

    public void MarkerOnlyFailed(string code) { reporter.Failed(code); }
    public void Diagnostic(string message) { reporter.Diagnostic(message); }
    public void Ready(int completedInputs) { reporter.Ready(completedInputs); }
    public void Complete() { reporter.Complete(); }
    public void Failed(string code) { reporter.Failed(code); }

    private double NowSeconds()
    {
        return clock.ElapsedTicks / (double)Stopwatch.Frequency;
    }

    internal void ObserveUpdate(Game game)
    {
        updateBoundary.Observe(new GameUpdateObservation(this, game));
    }

    internal HookToken PlayerPollEntered() { return driver.PlayerPollEntered(); }
    internal void PhysicalPollReturned(int rawDirection)
    {
        driver.PhysicalPollReturned(rawDirection);
    }
    internal void PlayerPollReturned(HookToken token)
    {
        driver.PlayerPollReturned(token);
    }

    internal HookToken ProcessInputEntered(GameState state, int rawDirection)
    {
        return driver.ProcessInputEntered(state, rawDirection, NowSeconds());
    }

    internal void ProcessInputReturned(
        GameState state, bool accepted, HookToken token)
    {
        if (token == null || !token.Active)
        {
            driver.ProcessInputReturned(token, accepted, false);
            return;
        }
        bool movement;
        try
        {
            movement = adapter.MovementScheduled(state);
        }
        catch (CaptureException)
        {
            driver.ProcessInputThrew(token);
            driver.TryFault("capture_failed");
            return;
        }
        driver.ProcessInputReturned(token, accepted, movement);
    }

    internal HookToken UndoEntered(Game game)
    {
        try
        {
            object stateReference;
            bool usable = adapter.TryGetState(game, out stateReference);
            return driver.UndoEntered(
                usable ? stateReference : null, NowSeconds());
        }
        catch (CaptureException)
        {
            driver.TryFault("capture_failed");
            return HookToken.Inert(HookKind.Undo);
        }
    }

    internal void RestoreObserved() { driver.RestoreObserved(); }

    internal void UndoReturned(Game game, HookToken token)
    {
        if (token == null || !token.Active)
        {
            driver.UndoReturned(token, false);
            return;
        }
        bool movement;
        try
        {
            movement = adapter.CurrentMovementScheduled(game);
        }
        catch (CaptureException)
        {
            driver.UndoThrew(token);
            driver.TryFault("capture_failed");
            return;
        }
        driver.UndoReturned(token, movement);
    }

    internal HookToken RestartEntered() { return driver.RestartEntered(); }
    internal void RestartReturned(HookToken token) { driver.RestartReturned(token); }

    internal HookToken StateSetEntered(Game game, GameState requested)
    {
        try
        {
            object before;
            bool usable = adapter.TryGetState(game, out before);
            return driver.StateSetEntered(
                usable ? before : null, requested);
        }
        catch (CaptureException)
        {
            driver.TryFault("capture_failed");
            return HookToken.Inert(HookKind.StateSet);
        }
    }

    internal void StateSetReturned(Game game, HookToken token)
    {
        if (token == null || !token.Active)
        {
            driver.StateSetReturned(token, null, 0.0);
            return;
        }
        try
        {
            object after;
            bool usable = adapter.TryGetState(game, out after);
            driver.StateSetReturned(
                token, usable ? after : null, NowSeconds());
        }
        catch (CaptureException)
        {
            driver.StateSetThrew(token);
            driver.TryFault("capture_failed");
        }
    }

    internal Exception ObserveFinalizer(HookToken token, Exception original)
    {
        return PatchBoundary.Finalize(
            token,
            original,
            driver.ClearThrew,
            delegate { driver.TryFault("game_method_exception"); },
            ObserverFailed);
    }

    internal Exception ObserveUpdateFinalizer(Exception original)
    {
        return PatchBoundary.FinalizeUpdate(
            original,
            delegate { driver.TryFault("game_method_exception"); },
            ObserverFailed);
    }

    internal void ObserverFailed()
    {
        if (driver != null)
            driver.TryFault("observer_exception");
    }

    internal bool TryFault(string code)
    {
        return driver != null && driver.TryFault(code);
    }

    internal void Disable()
    {
        if (driver != null)
            driver.Disable();
    }

    public void Dispose()
    {
        if (disposed)
            return;
        disposed = true;
        if (startup != null)
            startup.Dispose();
        else if (Object.ReferenceEquals(instance, this))
            instance = null;
    }
}
```

- [ ] **Step 4: Run the real plugin GREEN gate**

Run the two cumulative plugin tests and real build, then require the
metadata call graph to show `PassiveUpdateBoundary.Observe` and no direct
gate/capture/complete call from `PassiveController.ObserveUpdate`. Retain the
diff and output for post-commit review:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
git diff --check
```

- [ ] **Step 5: Commit only the Task 9.2 controller slice**

```bash
git add oracle/plugin/PassiveController.cs \
  oracle/plugin/tests/AssemblySurfaceTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: enforce passive capture boundary"
```

#### Task 9.3: Install exactly eight observation-only Harmony patches

- [ ] **Step 1: Add the Harmony-surface RED built-plugin metadata/IL test**

Replace only `AssemblySurfaceTests.Register` with this cumulative block.  The
four game-assembly registrations stay fixed, the adapter and controller tests
remain, and the one new Harmony registration raises the manifest to
`plugin=3`.

```csharp
internal static void Register(TestRegistry tests, HarnessOptions options)
{
    tests.Add("assembly", "pinned Assembly-CSharp hash",
        delegate { PinnedHash(options.AssemblyPath); });
    tests.Add("assembly", "exact ten observed methods",
        delegate { ExactObservedMethods(options.AssemblyPath); });
    tests.Add("assembly", "exact required game fields",
        delegate { ExactRequiredFields(options.AssemblyPath); });
    tests.Add("assembly", "metadata matcher rejects near misses",
        SyntheticMatcherRejectsNearMisses);
    tests.Add("plugin", "game adapter call surface is passive",
        delegate { AdapterCallSurface(options.PluginPath); });
    tests.Add("plugin", "controller crosses authorized update boundary",
        delegate { ControllerUsesAuthorizedBoundary(options.PluginPath); });
    tests.Add("plugin", "eight Harmony patch contracts are exact",
        delegate { ExactPatchSurface(options.PluginPath); });
}
```

Reuse the exact `--cohort plugin --plugin <absolute>` parser and metadata-only
decoder already committed. Freeze the eight patch targets, exact callback
parameter names/types, tokenless Update finalizer, and state-bearing finalizer
rules. The only permitted by-ref callback parameter is prefix
`out HookToken __state`; no game argument or result is by-ref.

- [ ] **Step 2: Build the pre-patch artifact and run semantic RED**

Build the Task 9.2 controller artifact before creating `PassivePatches.cs` and
require the named Harmony registration to fail for the missing eight-class
surface; the adapter and controller registrations must pass:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

The second command must exit nonzero for that expected contract mismatch, not a
missing DLL/assets file/metadata reader. If assets are absent, first run the
authenticated local-feed restores in Task 10 Step 1.

- [ ] **Step 3: Implement exact Harmony targets and positional callbacks**

Each patch class supplies `TargetMethod()` with the exact declaring type,
visibility, return type, and parameter array. The callback signature matrix is
fixed:

```text
Game.Update:
  Postfix(Game __instance)
  Finalizer(Exception __exception)
Game.DoPlayerInput:
  Prefix(out HookToken __state)
  Postfix(HookToken __state)
  Finalizer(Exception __exception, HookToken __state)
Game.Playerinputstring:
  Postfix(Direction __result)
GameState.ProcessInput:
  Prefix(GameState __instance, Direction __0, out HookToken __state)
  Postfix(GameState __instance, bool __result, HookToken __state)
  Finalizer(Exception __exception, HookToken __state)
Game.DoUndo:
  Prefix(Game __instance, out HookToken __state)
  Postfix(Game __instance, HookToken __state)
  Finalizer(Exception __exception, HookToken __state)
Game.RestorePrevState:
  Prefix(GameState.BakStruct __0)
Game.DoRestart:
  Prefix(out HookToken __state)
  Postfix(HookToken __state)
  Finalizer(Exception __exception, HookToken __state)
Game.SetGameState:
  Prefix(Game __instance, GameState __0, out HookToken __state)
  Postfix(Game __instance, HookToken __state)
  Finalizer(Exception __exception, HookToken __state)
```

`Direction __0` and `GameState __0` are deliberate Harmony positional
arguments, not source parameter-name guesses. The metadata test asserts the
literal `__0` names. `RestorePrevState` likewise uses positional `__0` even
though observation needs only the fact of entry. All original arguments and
`__result` are by value. Every prefix initializes `__state` to the correct
`HookToken.Inert(kind)` before entering `PassiveController.ObservePatch`.

Use only the complete file below. `PatchTarget.Require` rejects a missing or
wrong-return target before patching. Every ordinary callback enters through
`PassiveController.ObservePatch`; every finalizer enters through
`FinalizePatch` or `FinalizeUpdatePatch`. Those static wrappers tolerate an
unavailable controller, contain all observer/reporting failures, and preserve
the identical original exception reference. The Update finalizer never samples
because a thrown original skips the normal postfix.

Create `PassivePatches.cs` from this one complete authoritative file:

```csharp
using System;
using System.Reflection;
using HarmonyLib;

internal static class PatchTarget
{
    internal static MethodBase Require(
        Type type, string name, BindingFlags flags,
        Type returnType, Type[] parameters)
    {
        MethodInfo method = type.GetMethod(name, flags, null, parameters, null);
        if (method == null || method.ReturnType != returnType)
            throw new MissingMethodException(type.FullName, name);
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

    private static void Postfix(Game __instance)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { controller.ObserveUpdate(__instance); });
    }

    private static Exception Finalizer(Exception __exception)
    {
        return PassiveController.FinalizeUpdatePatch(__exception);
    }
}

[HarmonyPatch]
internal static class DoPlayerInputPatch
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
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { token = controller.PlayerPollEntered(); });
        __state = token;
    }

    private static void Postfix(HookToken __state)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { controller.PlayerPollReturned(__state); });
    }

    private static Exception Finalizer(Exception __exception, HookToken __state)
    {
        return PassiveController.FinalizePatch(__state, __exception);
    }
}

[HarmonyPatch]
internal static class PlayerInputStringPatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "Playerinputstring",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(Direction), new Type[0]);
    }

    private static void Postfix(Direction __result)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller)
            {
                controller.PhysicalPollReturned((int)__result);
            });
    }
}

[HarmonyPatch]
internal static class ProcessInputPatch
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
        PassiveController.ObservePatch(
            delegate(PassiveController controller)
            {
                token = controller.ProcessInputEntered(
                    __instance, (int)__0);
            });
        __state = token;
    }

    private static void Postfix(
        GameState __instance, bool __result, HookToken __state)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller)
            {
                controller.ProcessInputReturned(
                    __instance, __result, __state);
            });
    }

    private static Exception Finalizer(Exception __exception, HookToken __state)
    {
        return PassiveController.FinalizePatch(__state, __exception);
    }
}

[HarmonyPatch]
internal static class DoUndoPatch
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
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { token = controller.UndoEntered(__instance); });
        __state = token;
    }

    private static void Postfix(Game __instance, HookToken __state)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { controller.UndoReturned(__instance, __state); });
    }

    private static Exception Finalizer(Exception __exception, HookToken __state)
    {
        return PassiveController.FinalizePatch(__state, __exception);
    }
}

[HarmonyPatch]
internal static class RestorePrevStatePatch
{
    private static MethodBase TargetMethod()
    {
        return PatchTarget.Require(typeof(Game), "RestorePrevState",
            BindingFlags.Instance | BindingFlags.NonPublic,
            typeof(void), new Type[] { typeof(GameState.BakStruct) });
    }

    private static void Prefix(GameState.BakStruct __0)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { controller.RestoreObserved(); });
    }
}

[HarmonyPatch]
internal static class DoRestartPatch
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
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { token = controller.RestartEntered(); });
        __state = token;
    }

    private static void Postfix(HookToken __state)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { controller.RestartReturned(__state); });
    }

    private static Exception Finalizer(Exception __exception, HookToken __state)
    {
        return PassiveController.FinalizePatch(__state, __exception);
    }
}

[HarmonyPatch]
internal static class SetGameStatePatch
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
        PassiveController.ObservePatch(
            delegate(PassiveController controller)
            {
                token = controller.StateSetEntered(
                    __instance, __0);
            });
        __state = token;
    }

    private static void Postfix(Game __instance, HookToken __state)
    {
        PassiveController.ObservePatch(
            delegate(PassiveController controller) { controller.StateSetReturned(
                __instance, __state); });
    }

    private static Exception Finalizer(Exception __exception, HookToken __state)
    {
        return PassiveController.FinalizePatch(__state, __exception);
    }
}
```

- [ ] **Step 4: Run the real plugin GREEN gate**

Build the real net35 plugin and require all three cumulative plugin tests to
pass. Retain the diff and output for post-commit review:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
git diff --check
```

- [ ] **Step 5: Commit only the Task 9.3 patch slice**

```bash
git add oracle/plugin/PassivePatches.cs \
  oracle/plugin/tests/AssemblySurfaceTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: install passive observation patches"
```

#### Task 9.4: Wire the typed plugin shell and freeze its metadata

- [ ] **Step 1: Add the final three plugin metadata RED registrations**

Replace only `AssemblySurfaceTests.Register` with this final cumulative block
and raise the manifest from `plugin=3` to its final `assembly=4`, `plugin=6`.
The new PE/dependency, plugin identity, and typed-mode/teardown registrations
all remain RED against the Task 9.3 artifact. This is the sole final
registration method: no other metadata-test class or registration path is
permitted.

```csharp
internal static void Register(TestRegistry tests, HarnessOptions options)
{
    tests.Add("assembly", "pinned Assembly-CSharp hash",
        delegate { PinnedHash(options.AssemblyPath); });
    tests.Add("assembly", "exact ten observed methods",
        delegate { ExactObservedMethods(options.AssemblyPath); });
    tests.Add("assembly", "exact required game fields",
        delegate { ExactRequiredFields(options.AssemblyPath); });
    tests.Add("assembly", "metadata matcher rejects near misses",
        SyntheticMatcherRejectsNearMisses);
    tests.Add("plugin", "game adapter call surface is passive",
        delegate { AdapterCallSurface(options.PluginPath); });
    tests.Add("plugin", "controller crosses authorized update boundary",
        delegate { ControllerUsesAuthorizedBoundary(options.PluginPath); });
    tests.Add("plugin", "eight Harmony patch contracts are exact",
        delegate { ExactPatchSurface(options.PluginPath); });
    tests.Add("plugin", "PE CLR and direct references are pinned",
        delegate { PluginPeAndReferences(options.PluginPath); });
    tests.Add("plugin", "BepInPlugin identity is exact",
        delegate { BepInPluginIdentity(options.PluginPath); });
    tests.Add("plugin", "typed modes and owner teardown are closed",
        delegate { TypedModeAndOwnerOnlyTeardown(options.PluginPath); });
}
```

- [ ] **Step 2: Build the pre-shell artifact and run semantic RED**

Build the Task 9.3 artifact before replacing `Plugin.cs` or the project file,
then run the six-test cumulative plugin cohort. Require at least one of the
three new registrations to fail for the old PE/reference, identity, or typed
mode/teardown surface; the three retained plugin tests must pass.

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

- [ ] **Step 3: Wire typed configuration and exact startup inputs**

Set `[BepInPlugin("dev.jlsor.ssr.oracle", "SSR Executable Oracle", "0.2.0")]`.
Build the path with `Path.Combine(Paths.ConfigPath,
"dev.jlsor.ssr.oracle.cfg")` and call
`OracleConfiguration.Load(path, out originalConfigBytes)` exactly once. Do not
call raw `File.ReadAllBytes` in `Plugin`, `Config.Bind`, `Config.Save`, or
mutate an entry. Catch `OracleConfigurationException` before any driver exists
and emit only `SSR oracle passive trace failed: ` plus its exact `Code`;
missing/unreadable maps to `invalid_configuration`, an invalid mode stays
`invalid_mode`, and grammar/path failures retain their typed codes.

Off delegates to `PluginModePolicy.StartOff`, whose callbacks perform only the
preserved three legacy method checks and emit exactly
`SSR oracle boot probe loaded`. Passive constructs the controller and starts
it. Passive validation hashes `typeof(Game).Assembly.Location` before sink
creation and requires the reviewed lowercase SHA-256, creates
`Guid.NewGuid().ToString("N")` plus a UTC start for `RunRecord`, and passes that
record to `PassiveStartup.Start`. Create one `Stopwatch.StartNew()` per
controller and compute monotonic seconds as
`clock.ElapsedTicks / (double)Stopwatch.Frequency` for every driver boundary.

Install with Harmony owner `dev.jlsor.ssr.oracle.passive`. The controller must
become `Instance` before patch installation and remain available until after
owner-only unpatch. Run flush precedes installation, activation follows a
successful install, and only then may the unchanged boot marker be logged.

`OnDestroy` invokes idempotent Core teardown: Disable, owner-only
`UnpatchSelf`, then driver Dispose. If teardown precedes a terminal record,
Dispose closes the sink without fabricating End, Error, completion, or a
second failure marker.

Replace `SsrOracle.Plugin.csproj` with this complete project.  In particular,
the Unity facade remains a non-copying compile input solely to resolve
BepInEx's `MonoBehaviour` base type; plugin IL still has no direct facade
reference. The target-framework attribute is disabled to preserve the
reviewed CLR-v2 surface, every external reference is non-copying, and Release
cannot emit a PDB:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net35</TargetFramework>
    <LangVersion>7.3</LangVersion>
    <PlatformTarget>AnyCPU</PlatformTarget>
    <Deterministic>true</Deterministic>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <AssemblyName>SsrOracle.Plugin</AssemblyName>
    <RootNamespace>SsrOracle</RootNamespace>
    <GenerateTargetFrameworkAttribute>false</GenerateTargetFrameworkAttribute>
  </PropertyGroup>
  <PropertyGroup Condition="'$(Configuration)' == 'Release'">
    <IncludeSourceRevisionInInformationalVersion>false</IncludeSourceRevisionInInformationalVersion>
    <DebugType>none</DebugType>
    <DebugSymbols>false</DebugSymbols>
  </PropertyGroup>
  <ItemGroup>
    <Compile Remove="tests/**/*.cs;obj/**/*.cs;bin/**/*.cs" />
    <PackageReference Include="Microsoft.NETFramework.ReferenceAssemblies.net35"
                      Version="1.0.3" PrivateAssets="all" />
    <Reference Include="BepInEx">
      <HintPath>$(BepInExCoreDir)/BepInEx.dll</HintPath>
      <ExternallyResolved>true</ExternallyResolved>
      <Private>false</Private>
    </Reference>
    <Reference Include="0Harmony">
      <HintPath>$(BepInExCoreDir)/0Harmony.dll</HintPath>
      <ExternallyResolved>true</ExternallyResolved>
      <Private>false</Private>
    </Reference>
    <Reference Include="Assembly-CSharp">
      <HintPath>$(GameManagedDir)/Assembly-CSharp.dll</HintPath>
      <ExternallyResolved>true</ExternallyResolved>
      <Private>false</Private>
    </Reference>
    <Reference Include="UnityEngine">
      <HintPath>$(GameManagedDir)/UnityEngine.dll</HintPath>
      <ExternallyResolved>true</ExternallyResolved>
      <Private>false</Private>
    </Reference>
    <Reference Include="UnityEngine.CoreModule">
      <HintPath>$(GameManagedDir)/UnityEngine.CoreModule.dll</HintPath>
      <ExternallyResolved>true</ExternallyResolved>
      <Private>false</Private>
    </Reference>
  </ItemGroup>
  <Target Name="ValidateOracleReferences" BeforeTargets="ResolveReferences">
    <Error Condition="'$(GameManagedDir)' == ''" Text="GameManagedDir is required" />
    <Error Condition="'$(BepInExCoreDir)' == ''" Text="BepInExCoreDir is required" />
    <Error Condition="!Exists('$(GameManagedDir)/Assembly-CSharp.dll')"
           Text="Assembly-CSharp.dll not found under GameManagedDir" />
    <Error Condition="!Exists('$(GameManagedDir)/UnityEngine.dll')"
           Text="UnityEngine.dll not found under GameManagedDir" />
    <Error Condition="!Exists('$(GameManagedDir)/UnityEngine.CoreModule.dll')"
           Text="UnityEngine.CoreModule.dll not found under GameManagedDir" />
    <Error Condition="!Exists('$(BepInExCoreDir)/BepInEx.dll')"
           Text="BepInEx.dll not found under BepInExCoreDir" />
    <Error Condition="!Exists('$(BepInExCoreDir)/0Harmony.dll')"
           Text="0Harmony.dll not found under BepInExCoreDir" />
  </Target>
</Project>
```

Replace `Plugin.cs` with this complete configuration/lifecycle file;
`originalConfigBytes` is retained solely for Mode-off byte-identity tests:

```csharp
using System;
using System.IO;
using BepInEx;

namespace SsrOracle
{
    [BepInPlugin("dev.jlsor.ssr.oracle", "SSR Executable Oracle", "0.2.0")]
    public sealed class Plugin : BaseUnityPlugin
    {
        private PassiveController controller;
        private byte[] originalConfigBytes;

        private void Awake()
        {
            string path = Path.Combine(
                Paths.ConfigPath, "dev.jlsor.ssr.oracle.cfg");
            OracleConfiguration configuration;
            try
            {
                configuration = OracleConfiguration.Load(
                    path, out originalConfigBytes);
            }
            catch (OracleConfigurationException error)
            {
                Logger.LogError(
                    "SSR oracle passive trace failed: " + error.Code);
                return;
            }

            if (configuration.Mode == OracleMode.Off)
            {
                PluginModePolicy.StartOff(
                    configuration,
                    GameContract.ValidateLegacySurface,
                    EmitBootMarker);
                return;
            }

            controller = new PassiveController(configuration.Passive, Logger);
            RunRecord run = new RunRecord(
                Guid.NewGuid().ToString("N"),
                OracleProtocol.ExpectedAssemblySha256,
                DateTime.UtcNow);
            controller.Start(run);
        }

        private void EmitBootMarker()
        {
            Logger.LogInfo("SSR oracle boot probe loaded");
        }

        private void OnDestroy()
        {
            if (controller != null)
                controller.Dispose();
            GC.KeepAlive(originalConfigBytes);
        }
    }
}
```

- [ ] **Step 4: Build and run the exact GREEN gates**

```bash
if test ! -f oracle/plugin/obj/project.assets.json; then
  /opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
    oracle/plugin/SsrOracle.Plugin.csproj \
    --source "$PWD/data/oracle/compat/feed" \
    -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
    -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
fi
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort assembly \
  --assembly "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

Require both harness runs to print exactly the success line. The plugin
cohort asserts positional `__0` parameters, tokenless Update finalizer,
adapter movement/capture call sites, exact metadata pins, and typed config
load. Retain the diff and every gate output for post-commit review.

- [ ] **Step 5: Commit only the typed plugin and metadata slice**

```bash
git diff --check
git add oracle/plugin/Plugin.cs oracle/plugin/SsrOracle.Plugin.csproj \
  oracle/plugin/tests/AssemblySurfaceTests.cs oracle/plugin/tests/Program.cs
git commit -m "feat: wire passive oracle plugin"
```

The dependency-minimal harness tests only Core policy. Passing this task also
requires the real net35 plugin build; Task 10 inspects that artifact instead of
pretending the Core harness compiled game types.

### Track 10: Prove reproducibility and document the offline plugin gate

#### Task 10.1: Prove the complete offline artifact and record its literal digest

Execute Steps 1-5 sequentially in one fresh, retained Bash process (one PTY or
terminal session), beginning with the `set -euo pipefail` below.  The readonly
package identities and default package root created in Step 1 are deliberately
reused by Steps 2-3; the independent build roots and DLL paths created in Step
3 are deliberately reused by Steps 4-5.  Do not close or replace that shell
between those steps.  If it exits for any reason, retain the failed task
evidence but restart Task 10.1 at Step 1 with new temporary roots rather than
resuming a later step with reconstructed variables.

- [ ] **Step 1: Authenticate the local package and restore into an isolated cache**

**Files:**
- Modify: `oracle/README.md`
- Verify: all plugin and harness files from Tasks 1-9

**Interfaces:**
- Produces a literal reviewed `0.2.0` DLL SHA-256 for the passive-controller and runtime-acceptance plans.
- Produces byte-identical clean Release artifacts from two independent output roots.
- Does not deploy the artifact or claim runtime success.

First run `shasum -a 256` on the four absolute BepInEx/Harmony/Unity compile
inputs and require the Global Constraints values plus the reviewed
Assembly-CSharp hash. Stop on any mismatch.

```bash
set -euo pipefail
shasum -a 256 \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core/BepInEx.dll" \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core/0Harmony.dll" \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/UnityEngine.dll" \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/UnityEngine.CoreModule.dll" \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
test "$(shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core/BepInEx.dll" | awk '{print $1}')" = \
  19eb836818955e4f86818306aaf2baaee989be566d7da697f835b429ab585149
test "$(shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core/0Harmony.dll" | awk '{print $1}')" = \
  1a21cc03424fc82c3dd1346905d16494536b9595ae4162228d99fb7c285c1031
test "$(shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/UnityEngine.dll" | awk '{print $1}')" = \
  f8bc81e00aa5f4372cbebe4951e5be7b21e54ba5f978e21c53ae2e8713ca3ca0
test "$(shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/UnityEngine.CoreModule.dll" | awk '{print $1}')" = \
  b9aa7294a63984fc7a86cf68bceba4a92b254f8e140943d402e34c397146edf3
test "$(shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll" | awk '{print $1}')" = \
  886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564
```

Authenticate the exact package bytes consumed by every net35 restore, then
restore all three projects from only that local feed into one new private
default-build package root. Existing source-tree assets or the user-global
NuGet cache are not accepted as restore evidence:

```bash
SSR_FRAMEWORK_PACKAGE="$PWD/data/oracle/compat/feed/microsoft.netframework.referenceassemblies.1.0.3.nupkg"
SSR_FRAMEWORK_PACKAGE_SHA256="141a093f90c7645d101ccd312e6f727781c965540eb92a52280f95411a698441"
SSR_NET35_PACKAGE="$PWD/data/oracle/compat/feed/microsoft.netframework.referenceassemblies.net35.1.0.3.nupkg"
SSR_NET35_PACKAGE_SHA256="b16156111a88670d91a757fbd465fcb4856e034b1a4d523ae2c41a470f3578f9"
SSR_PLUGIN_DEFAULT_PACKAGES=$(mktemp -d /tmp/ssr-plugin-packages.XXXXXX)
readonly SSR_FRAMEWORK_PACKAGE SSR_FRAMEWORK_PACKAGE_SHA256 \
  SSR_NET35_PACKAGE SSR_NET35_PACKAGE_SHA256 SSR_PLUGIN_DEFAULT_PACKAGES
chmod 700 "$SSR_PLUGIN_DEFAULT_PACKAGES"
test -f "$SSR_FRAMEWORK_PACKAGE" && test -f "$SSR_NET35_PACKAGE"
test "$(shasum -a 256 "$SSR_FRAMEWORK_PACKAGE" | awk '{print $1}')" = \
  "$SSR_FRAMEWORK_PACKAGE_SHA256"
test "$(shasum -a 256 "$SSR_NET35_PACKAGE" | awk '{print $1}')" = \
  "$SSR_NET35_PACKAGE_SHA256"

/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/SsrOracle.Plugin.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_DEFAULT_PACKAGES" --no-http-cache \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_DEFAULT_PACKAGES" --no-http-cache
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_DEFAULT_PACKAGES" --no-http-cache
```

The plugin restore must resolve only the pinned
`Microsoft.NETFramework.ReferenceAssemblies` and
`Microsoft.NETFramework.ReferenceAssemblies.net35` packages from the
authenticated ignored feed and the new isolated package root. No
package-network acquisition or user-global package-cache reuse is part of this
plan. Retain the private package root through the default build and review.

- [ ] **Step 2: Freeze the final 15-cohort/82-test Program and run the complete C# matrix**

Replace the cumulative `Program.cs` manifest with this complete final file.
The unconditional registrations make missing/extra cohorts detectable even
when one cohort is selected; path-dependent tests read their values only when
executed.

```csharp
using System;
using System.Collections.Generic;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            HarnessOptions options = HarnessOptions.Parse(args);
            TestRegistry tests = new TestRegistry();
            ProtocolTests.Register(tests);
            EncodingTests.Register(tests);
            CaptureSignatureTests.Register(tests);
            TraceSinkTests.Register(tests);
            PassiveDriverTests.Register(tests);
            ConfigurationTests.Register(tests, options);
            PhysicalPathTests.Register(tests);
            GameObservationTests.Register(tests);
            PatchBoundaryTests.Register(tests);
            PluginModePolicyTests.Register(tests);
            PassiveStartupTests.Register(tests);
            PassiveReporterTests.Register(tests);
            AssemblySurfaceTests.Register(tests, options);
            tests.VerifyManifest(
                new Dictionary<string, int>(StringComparer.Ordinal)
                {
                    { "protocol", 4 },
                    { "encoding", 5 },
                    { "sink", 6 },
                    { "driver-boundary", 2 },
                    { "driver-initial", 8 },
                    { "driver-input", 8 },
                    { "driver-terminal", 6 },
                    { "config", 6 },
                    { "path", 6 },
                    { "observation", 5 },
                    { "boundary", 5 },
                    { "startup", 7 },
                    { "reporter", 4 },
                    { "assembly", 4 },
                    { "plugin", 6 }
                });
            int result = tests.Run(options.Cohort);
            if (result != 0)
                return result;
            Console.WriteLine("SSR oracle unit harness ready");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.ToString());
            return 1;
        }
    }
}
```

Before running it, mechanically count the literal registrations and manifest
rows; both commands must print nothing and return zero:

```bash
test "$(rg -o 'tests\.Add\(' oracle/plugin/tests/*Tests.cs | wc -l | tr -d ' ')" = 82
test "$(rg -o '^                    \{ "[a-z-]+", [0-9]+ \},?$' oracle/plugin/tests/Program.cs | wc -l | tr -d ' ')" = 15
```

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- \
  --assembly "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll" \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll" \
  --mode-off-fixture "$PWD/data/oracle/boot-probe.cfg"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
```

Require the one exact success line and no stderr.

- [ ] **Step 3: Build twice into independent temporary roots**

Use two `mktemp -d` roots. Restore each root independently with matching
`BaseIntermediateOutputPath` and `MSBuildProjectExtensionsPath`; a restore in
the default `obj` directory cannot support `--no-restore` in a fresh root.
The default Step 2 build must remain in place: do not clean source-tree
`obj/` or `bin/`. First prove that generated C# is present and that the project
has stable explicit exclusions; this makes the independent-root build test the
previously dangerous dirty-source-tree case. Then pass the same two properties
plus distinct `BaseOutputPath` to each Release build and compare the DLLs with
`cmp`:

```bash
test "$(rg --files oracle/plugin/obj -g '*.cs' | wc -l | tr -d ' ')" -gt 0
rg -q '<Compile Remove="tests/\*\*/\*\.cs;obj/\*\*/\*\.cs;bin/\*\*/\*\.cs" />' \
  oracle/plugin/SsrOracle.Plugin.csproj
test "${SSR_PLUGIN_DEFAULT_PACKAGES+x}" = x
test "${SSR_FRAMEWORK_PACKAGE+x}" = x
test "${SSR_FRAMEWORK_PACKAGE_SHA256+x}" = x
test "${SSR_NET35_PACKAGE+x}" = x
test "${SSR_NET35_PACKAGE_SHA256+x}" = x
test -d "$SSR_PLUGIN_DEFAULT_PACKAGES"
SSR_PLUGIN_BUILD_A=$(mktemp -d /tmp/ssr-plugin-build-a.XXXXXX)
SSR_PLUGIN_BUILD_B=$(mktemp -d /tmp/ssr-plugin-build-b.XXXXXX)
readonly SSR_PLUGIN_BUILD_A SSR_PLUGIN_BUILD_B
test "$(shasum -a 256 "$SSR_FRAMEWORK_PACKAGE" | awk '{print $1}')" = \
  "$SSR_FRAMEWORK_PACKAGE_SHA256"
test "$(shasum -a 256 "$SSR_NET35_PACKAGE" | awk '{print $1}')" = \
  "$SSR_NET35_PACKAGE_SHA256"

/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/SsrOracle.Plugin.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_BUILD_A/packages" --no-http-cache \
  -p:BaseIntermediateOutputPath="$SSR_PLUGIN_BUILD_A/obj/" \
  -p:MSBuildProjectExtensionsPath="$SSR_PLUGIN_BUILD_A/obj/" \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:BaseOutputPath="$SSR_PLUGIN_BUILD_A/out/" \
  -p:BaseIntermediateOutputPath="$SSR_PLUGIN_BUILD_A/obj/" \
  -p:MSBuildProjectExtensionsPath="$SSR_PLUGIN_BUILD_A/obj/" \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/SsrOracle.Plugin.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_BUILD_B/packages" --no-http-cache \
  -p:BaseIntermediateOutputPath="$SSR_PLUGIN_BUILD_B/obj/" \
  -p:MSBuildProjectExtensionsPath="$SSR_PLUGIN_BUILD_B/obj/" \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:BaseOutputPath="$SSR_PLUGIN_BUILD_B/out/" \
  -p:BaseIntermediateOutputPath="$SSR_PLUGIN_BUILD_B/obj/" \
  -p:MSBuildProjectExtensionsPath="$SSR_PLUGIN_BUILD_B/obj/" \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

SSR_PLUGIN_DLL_A="$SSR_PLUGIN_BUILD_A/out/Release/net35/SsrOracle.Plugin.dll"
SSR_PLUGIN_DLL_B="$SSR_PLUGIN_BUILD_B/out/Release/net35/SsrOracle.Plugin.dll"
readonly SSR_PLUGIN_DLL_A SSR_PLUGIN_DLL_B
test -f "$SSR_PLUGIN_DLL_A"
test -f "$SSR_PLUGIN_DLL_B"
shasum -a 256 "$SSR_PLUGIN_DLL_A" "$SSR_PLUGIN_DLL_B"
cmp "$SSR_PLUGIN_DLL_A" "$SSR_PLUGIN_DLL_B"
```

Retain both independent build roots and the default-build package root until
hashes and reviewer evidence have been copied into the task report. Cleanup is
a separate explicit generated-artifact step after review; it is not part of
this command block.

Both hashes must be identical. Record that literal hash in `oracle/README.md`; it becomes an input to the passive-probe implementation review and the later runtime-acceptance plan.

- [ ] **Step 4: Verify legacy metadata and dependency closure**

Reuse Task 9's `--cohort plugin --plugin` metadata-only harness mode on both
independent outputs. Require PE32 managed IL-only with no native entrypoint or
managed-native header, metadata version `v2.0.50727`, AssemblyDefinition
`SsrOracle.Plugin` version `1.0.0.0`, no `TargetFrameworkAttribute`, and the
exact `BepInPlugin` constructor values
`dev.jlsor.ssr.oracle`, `SSR Executable Oracle`, `0.2.0`, and exactly this
direct AssemblyRef set—no missing, extra, or version-changed entry:

```text
0Harmony=2.9.0.0
Assembly-CSharp=0.0.0.0
BepInEx=5.4.23.5
System.Core=3.5.0.0
System=2.0.0.0
UnityEngine.CoreModule=0.0.0.0
mscorlib=2.0.0.0
```

`UnityEngine.dll` is an authenticated, non-copying compile input required to
resolve BepInEx's `MonoBehaviour` base, but plugin IL has no direct facade
type/member use, so do not expect `UnityEngine` in this AssemblyRef set. In the
same metadata/IL audit,
require the adapter's call/member-reference surface to include Unity
`Object.op_Equality`, `GameObject.get_activeSelf`, and
`GameState.Save(bool,bool)` with both arguments emitted as false, while no
method references `GameState.Lost`. Require the eight Harmony patch target
factories, tokenless `Game.Update` finalizer, token-bearing finalizers only for
methods with prefixes, and no by-ref game argument or result in any patch
entrypoint. Require literal positional names/types `Direction __0` on
`ProcessInput` and `GameState __0` on `SetGameState`; the only permitted by-ref
parameter is prefix `out HookToken __state`. Require the immediate
`ProcessInput` path to call `GameAdapter.MovementScheduled(GameState)`, the Undo
exit path to call `GameAdapter.CurrentMovementScheduled(Game)`, and no other
movement call site. Audit `Plugin.Awake`/`OnDestroy` call edges so the Off branch reaches
`PluginModePolicy.StartOff` but no passive startup, and the Passive branch
reaches the controller only after parse. Reject references from Plugin code to
`Config.Bind`, `Config.Save`, file-write APIs, or any config mutation path;
require owner-only teardown and no driver construction in the compiled Off
branch. Require `Plugin.Awake` to call `OracleConfiguration.Load` and forbid a
direct `File.ReadAllBytes` call there.

```bash
test "${SSR_PLUGIN_DLL_A+x}" = x
test "${SSR_PLUGIN_DLL_B+x}" = x
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin --plugin "$SSR_PLUGIN_DLL_A"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin --plugin "$SSR_PLUGIN_DLL_B"
find "$SSR_PLUGIN_BUILD_A/out/Release/net35" -maxdepth 1 -type f -print | sort
find "$SSR_PLUGIN_BUILD_B/out/Release/net35" -maxdepth 1 -type f -print | sort
test "$(find "$SSR_PLUGIN_BUILD_A/out/Release/net35" -maxdepth 1 -type f -print)" = "$SSR_PLUGIN_DLL_A"
test "$(find "$SSR_PLUGIN_BUILD_B/out/Release/net35" -maxdepth 1 -type f -print)" = "$SSR_PLUGIN_DLL_B"
```

Each output leaf contains exactly `SsrOracle.Plugin.dll`; reject a PDB or any
copied dependency.

- [ ] **Step 5: Update the runbook without authorizing a launch**

Immediately above the new section, add one evidence bullet whose text begins
`` `SsrOracle.Plugin.dll 0.2.0` SHA-256: `` and ends with the complete literal
common digest printed in Step 3. Then add this exact static block to
`oracle/README.md`:

````markdown
### Passive observation plugin 0.2.0

The passive plugin source is split between Unity-free policy under `oracle/plugin/Core/` and the thin `GameAdapter`, `PassiveController`, `PassivePatches`, and `Plugin` shell under `oracle/plugin/`. Its reviewed DLL SHA-256 is the literal common hash from the two clean Release builds in the artifact evidence bullet immediately above; a label, variable name, or shortened digest is not evidence.

Mode-off remains compatibility-only: it reads the existing config bytes without saving them, validates only `Game.Playerinputstring`, `Game.DoPlayerInput`, and `GameState.ProcessInput`, installs no patches, creates no trace, does not redirect saves, and emits `SSR oracle boot probe loaded`.

Passive mode accepts exactly:

```ini
[Oracle]
Mode = passive
OutputDirectory = /private/tmp/ssr-oracle-output
RunName = passive-trace
SaveDirectory = /private/tmp/ssr-oracle-save
ExpectedPassiveInputs = 3
MaxSettleFrames = 600
MaxSettleSeconds = 30
```

Run the offline gates from the repository root:

```bash
set -euo pipefail
SSR_GAME_MANAGED_DIR="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
SSR_BEPINEX_CORE_DIR="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
SSR_PLUGIN_PACKAGES=$(mktemp -d /tmp/ssr-plugin-readme-packages.XXXXXX)
SSR_MODE_OFF_SOURCE="/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/boot-probe.cfg"
SSR_MODE_OFF_DESTINATION="$PWD/data/oracle/boot-probe.cfg"
readonly SSR_GAME_MANAGED_DIR SSR_BEPINEX_CORE_DIR SSR_PLUGIN_PACKAGES \
  SSR_MODE_OFF_SOURCE SSR_MODE_OFF_DESTINATION
chmod 700 "$SSR_PLUGIN_PACKAGES"
test "$(shasum -a 256 "$SSR_BEPINEX_CORE_DIR/BepInEx.dll" | awk '{print $1}')" = \
  19eb836818955e4f86818306aaf2baaee989be566d7da697f835b429ab585149
test "$(shasum -a 256 "$SSR_BEPINEX_CORE_DIR/0Harmony.dll" | awk '{print $1}')" = \
  1a21cc03424fc82c3dd1346905d16494536b9595ae4162228d99fb7c285c1031
test "$(shasum -a 256 "$SSR_GAME_MANAGED_DIR/UnityEngine.dll" | awk '{print $1}')" = \
  f8bc81e00aa5f4372cbebe4951e5be7b21e54ba5f978e21c53ae2e8713ca3ca0
test "$(shasum -a 256 "$SSR_GAME_MANAGED_DIR/UnityEngine.CoreModule.dll" | awk '{print $1}')" = \
  b9aa7294a63984fc7a86cf68bceba4a92b254f8e140943d402e34c397146edf3
test "$(shasum -a 256 "$SSR_GAME_MANAGED_DIR/Assembly-CSharp.dll" | awk '{print $1}')" = \
  886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564
test "$(shasum -a 256 "$PWD/data/oracle/compat/feed/microsoft.netframework.referenceassemblies.1.0.3.nupkg" | awk '{print $1}')" = \
  141a093f90c7645d101ccd312e6f727781c965540eb92a52280f95411a698441
test "$(shasum -a 256 "$PWD/data/oracle/compat/feed/microsoft.netframework.referenceassemblies.net35.1.0.3.nupkg" | awk '{print $1}')" = \
  b16156111a88670d91a757fbd465fcb4856e034b1a4d523ae2c41a470f3578f9
test "$(shasum -a 256 "$SSR_MODE_OFF_SOURCE" | awk '{print $1}')" = \
  cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d
if test -e "$SSR_MODE_OFF_DESTINATION"; then
  test "$SSR_MODE_OFF_SOURCE" -ef "$SSR_MODE_OFF_DESTINATION"
else
  mkdir -p "$PWD/data/oracle"
  ln "$SSR_MODE_OFF_SOURCE" "$SSR_MODE_OFF_DESTINATION"
fi
git check-ignore "$SSR_MODE_OFF_DESTINATION"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/SsrOracle.Plugin.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_PACKAGES" --no-http-cache \
  -p:GameManagedDir="$SSR_GAME_MANAGED_DIR" \
  -p:BepInExCoreDir="$SSR_BEPINEX_CORE_DIR"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_PACKAGES" --no-http-cache
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  --source "$PWD/data/oracle/compat/feed" \
  --packages "$SSR_PLUGIN_PACKAGES" --no-http-cache
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="$SSR_GAME_MANAGED_DIR" \
  -p:BepInExCoreDir="$SSR_BEPINEX_CORE_DIR"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- \
  --assembly "$SSR_GAME_MANAGED_DIR/Assembly-CSharp.dll" \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll" \
  --mode-off-fixture "$SSR_MODE_OFF_DESTINATION"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore -warnaserror
```

The offline harness must finish with exactly `SSR oracle unit harness ready`. Runtime progress markers are `SSR oracle passive trace ready: 0/3`, `SSR oracle passive trace ready: 1/3`, and `SSR oracle passive trace ready: 2/3`; success is `SSR oracle passive trace complete`; failure begins with `SSR oracle passive trace failed: ` and ends with one exact code from the closed schema-v1 record-code or marker-only tables. Real traces, generated configs, isolated saves, recovery trees, and probe evidence remain ignored below `data/oracle/`.

Status: offline plugin complete; bounded passive controller and real-game gate pending. This offline result does not authorize deployment, launch, save restoration, or a real capture. Those actions require a fresh read-only preflight and separate explicit approval.
````

For the artifact evidence bullet referenced by that block, compute both hashes,
prove equality, and insert that complete literal 64-digit value after the fixed
bullet prefix. Then extract the README value back out and compare it; merely
finding some 64-digit string is not an acceptance gate:

```bash
test "${SSR_PLUGIN_DLL_A+x}" = x
test "${SSR_PLUGIN_DLL_B+x}" = x
SSR_PLUGIN_SHA_A=$(shasum -a 256 "$SSR_PLUGIN_DLL_A" | awk '{print $1}')
SSR_PLUGIN_SHA_B=$(shasum -a 256 "$SSR_PLUGIN_DLL_B" | awk '{print $1}')
test "$SSR_PLUGIN_SHA_A" = "$SSR_PLUGIN_SHA_B"
test "${#SSR_PLUGIN_SHA_A}" = 64
SSR_README_SHA=$(sed -n \
  's/^- `SsrOracle\.Plugin\.dll 0\.2\.0` SHA-256: `\([0-9a-f]\{64\}\)`$/\1/p' \
  oracle/README.md)
test "$(sed -n \
  '/^- `SsrOracle\.Plugin\.dll 0\.2\.0` SHA-256: `[0-9a-f]\{64\}`$/p' \
  oracle/README.md | wc -l | tr -d ' ')" = 1
test "$SSR_README_SHA" = "$SSR_PLUGIN_SHA_A"
rg -n 'Mode = passive|SSR oracle passive trace ready:|SSR oracle passive trace complete|offline plugin complete|real-game gate pending|separate explicit approval' \
  oracle/README.md
```

- [ ] **Step 6: Run complete offline acceptance**

```bash
set -euo pipefail
UV_OFFLINE=1 UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest --collect-only -q \
  tests/test_oracle_protocol.py \
  > data/oracle/plugin-plan-evidence/protocol-collection.txt
rg -q '^240 tests collected in ' \
  data/oracle/plugin-plan-evidence/protocol-collection.txt
UV_OFFLINE=1 UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest --collect-only -q \
  > data/oracle/plugin-plan-evidence/full-collection.txt
rg -q '^1948 tests collected in ' \
  data/oracle/plugin-plan-evidence/full-collection.txt
UV_OFFLINE=1 UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q -rxX \
  > data/oracle/plugin-plan-evidence/post-plugin-pytest.txt
test "$(rg -o '[0-9]+ passed' \
  data/oracle/plugin-plan-evidence/post-plugin-pytest.txt | tail -n 1)" = '1822 passed'
test "$(rg -o '[0-9]+ xfailed' \
  data/oracle/plugin-plan-evidence/post-plugin-pytest.txt | tail -n 1)" = '120 xfailed'
test "$(rg -o '[0-9]+ xpassed' \
  data/oracle/plugin-plan-evidence/post-plugin-pytest.txt | tail -n 1)" = '6 xpassed'
! rg -q '[0-9]+ (failed|errors?|skipped)' \
  data/oracle/plugin-plan-evidence/post-plugin-pytest.txt
sed -n 's/^XFAIL \([^ ]*\).*/\1/p' \
  data/oracle/plugin-plan-evidence/post-plugin-pytest.txt | LC_ALL=C sort \
  > data/oracle/plugin-plan-evidence/post-plugin-xfail-nodeids.txt
cmp data/oracle/plugin-plan-evidence/pre-plugin-xfail-nodeids.txt \
  data/oracle/plugin-plan-evidence/post-plugin-xfail-nodeids.txt
test "$(rg -c '^XPASS ' \
  data/oracle/plugin-plan-evidence/post-plugin-pytest.txt)" = 6
UV_OFFLINE=1 UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q src tools tests
git diff --check
SSR_PLUGIN_BRANCH_BASE=$(git merge-base main HEAD)
readonly SSR_PLUGIN_BRANCH_BASE
git diff --name-status "$SSR_PLUGIN_BRANCH_BASE"
git status --short --branch
```

The exact arithmetic is `1582 + P = 1582 + 240 = 1822` passes and
`1822 + 120 + 6 = 1948` collected terminal outcomes. Require zero failures,
zero errors, zero skips, the byte-identical frozen 120-node XFAIL manifest, and
exactly six non-strict XPASS with these node IDs:

```text
tests/test_oracle_boot.py::test_probe_rejects_evidence_directory_substitution_at_final_json_boundary
tests/test_oracle_boot.py::test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[raise]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[raise]
```

Check each identity mechanically against the retained `-rxX` report:

```bash
for SSR_XPASS_NODE in \
  'tests/test_oracle_boot.py::test_probe_rejects_evidence_directory_substitution_at_final_json_boundary' \
  'tests/test_oracle_boot.py::test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts' \
  'tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[return]' \
  'tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[raise]' \
  'tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[return]' \
  'tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[raise]'
do
  test "$(rg -F -c "XPASS $SSR_XPASS_NODE " \
    data/oracle/plugin-plan-evidence/post-plugin-pytest.txt)" = 1
done
```

Every other collected item must pass. Verify no `bin`, `obj`, real trace,
config, save, decompiled source, or user path fixture is tracked. Retain the
complete Tasks 1-10 diff and all acceptance evidence for Task 10.1's
post-commit review and the separate final whole-branch review.

- [ ] **Step 7: Commit only the literal reviewed runbook evidence**

```bash
git add oracle/README.md
git commit -m "docs: record passive oracle build gate"
```
