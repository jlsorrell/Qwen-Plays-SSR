# Task 6.1 Passive Runtime Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the accepted Unity-free `PassiveDriver` to the installed
game through strict read-only configuration, isolated paths, a single game
adapter, exception-safe Harmony observation hooks, and a typed plugin startup
transaction without launching the game or synthesizing input.

**Architecture:** Core owns configuration, path validation, observation
policy, patch firewalls, logging, startup ordering, and a Unity-free
`OracleController`. `GameAdapter`, `GameContract`, `GameHooks`, and `Plugin`
form a thin net35 boundary over the reviewed game/BepInEx assemblies. The
existing `PassiveDriver` remains the sole writer and lifecycle authority.

**Tech Stack:** C# 7.3; compile-only .NET Framework 3.5; pinned .NET SDK
10.0.300 unit harness; BepInEx 5.4.23.5; Harmony; metadata-only PE inspection;
macOS libc path probes; pytest.

**Spec:** `docs/superpowers/specs/2026-08-15-task-6-runtime-replay-design.md`

## Global Constraints

- The accepted parent is design commit
  `ddd15071960852f176d76d3ac3b3995508f378ba`; authenticate it before editing.
- Task 6.1 accepts exactly `off` and `passive`. `replay` remains a typed
  `invalid_mode` failure until the separate Task 6.2 plan is implemented.
- `off` installs no patches, redirects no path, opens no sink, and preserves
  the current three-method compatibility probe and exact boot marker.
- `passive` observes exactly three attempts and never changes an original
  argument, result, exception, or gameplay transition.
- Core contains no Unity, BepInEx, Harmony, `Game`, `GameState`, `Direction`,
  or filesystem-global static game state.
- `GameAdapter` is the only type that reads game fields or calls `Moving()` and
  `Save(false, false)`; Task 6.1 has no native Undo caller.
- Every Harmony finalizer returns the identical original exception reference.
- No monitor spans a game, sink, reporter, diagnostic, log, or Harmony call.
- Configuration is read once as strict UTF-8 bytes and never rewritten.
- Active paths fail closed; the ordinary save path is never used as fallback.
- The trace target uses the existing `FileMode.CreateNew` sink.
- Production remains C# 7.3/net35 compatible. Unit tests compile under net10.
- All package restores are offline from reviewed local artifacts with
  `NuGetAudit=false`; do not access the network.
- Do not launch the game, deploy a plugin/config, mutate installed files, or
  create a real trace in this task.
- The historical monolithic plan is read-only context, not patch input.
- Preserve every Task 5 source behavior and all 39 accepted tests.
- All Task 6.1 edits remain one reviewed working-tree transaction and become
  one final commit with subject `feat: connect passive oracle runtime`.

## File map

### Dependency-free Core

- Create `oracle/plugin/Core/OracleConfiguration.cs`: strict bytes/config
  grammar, typed failures, immutable passive values, injectable byte/path
  seams.
- Create `oracle/plugin/Core/PhysicalPath.cs`: canonical path identity,
  component containment, macOS no-symlink scans, absent-leaf proof.
- Create `oracle/plugin/Core/GameObservation.cs`: thirteen-gate policy and
  complete capture-value mapping.
- Create `oracle/plugin/Core/OracleRuntimeBoundaries.cs`: adapter, logging,
  patch installation, legacy validation, clock, and startup seams.
- Create `oracle/plugin/Core/PatchBoundary.cs`: postfix/finalizer exception
  firewall.
- Create `oracle/plugin/Core/PassiveReporter.cs`: exact passive markers.
- Create `oracle/plugin/Core/PluginModePolicy.cs`: capability-free Off branch.
- Create `oracle/plugin/Core/PassiveStartup.cs`: ordered active startup and
  idempotent teardown.
- Create `oracle/plugin/Core/OracleController.cs`: Unity-free routing from
  runtime callbacks to `PassiveDriver` and `PassiveUpdateBoundary`.

### Game/plugin boundary

- Create `oracle/plugin/GameContract.cs`: exact ABI/reflection validation.
- Create `oracle/plugin/GameAdapter.cs`: sole game-type mapping and save
  isolation.
- Create `oracle/plugin/GameHooks.cs`: eight Harmony target classes and static
  published-controller firewall.
- Replace `oracle/plugin/Plugin.cs`: typed configuration and composition.
- Modify `oracle/plugin/SsrOracle.Plugin.csproj`: deterministic CLR-v2/net35
  artifact, non-copying reviewed references, no Release PDB.

### Tests and registration

- Create `oracle/plugin/tests/ConfigurationTests.cs` (`config=6`).
- Create `oracle/plugin/tests/PhysicalPathTests.cs` (`path=6`).
- Create `oracle/plugin/tests/GameObservationTests.cs` (`observation=5`).
- Create `oracle/plugin/tests/PatchBoundaryTests.cs` (`boundary=5`).
- Create `oracle/plugin/tests/PassiveStartupTests.cs` (`startup=7`).
- Create `oracle/plugin/tests/PassiveReporterTests.cs` (`reporter=4`).
- Create `oracle/plugin/tests/AssemblySurfaceTests.cs` (`assembly=4`,
  `plugin=6`).
- Modify `oracle/plugin/tests/Program.cs`: register the reserved manifest in
  exact order; final C# count is 82.
- Keep `oracle/plugin/tests/SsrOracle.UnitTests.csproj` unchanged; the pinned
  net10 shared framework supplies the metadata reader.

### Evidence only

- Create ignored `.superpowers/sdd/2026-08-15-task-6-1-runtime-bridge/` for
  command logs, RED/GREEN records, review packages, mutation results, and final
  verification. Never stage it.

---

### Task 0: Authenticate the plan lineage and offline baseline

**Files:**
- Read: all paths in the file map
- Evidence: ignored Task 6.1 evidence root only

**Interfaces:**
- Consumes: approved design commit and installed read-only game/BepInEx
  references.
- Produces: authenticated `plan_commit`, baseline status, and reusable literal
  command variables for later steps.

- [ ] **Step 1: Authenticate the plan commit and working tree**

Run from the Task 6 worktree:

```bash
set -e
test "$(git show -s --format=%s HEAD)" = \
  "docs: plan Task 6.1 passive runtime bridge"
test "$(git rev-parse HEAD^)" = \
  ddd15071960852f176d76d3ac3b3995508f378ba
test "$(git diff-tree --no-commit-id --name-only -r HEAD)" = \
  docs/superpowers/plans/2026-08-15-task-6-1-runtime-bridge.md
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain)"
plan_commit=$(git rev-parse HEAD)
test -n "$plan_commit"
```

- [ ] **Step 2: Prove the reviewed local inputs**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
package_source="$PWD/data/oracle/compat/fetch-acceptance"
test -x "$dotnet_bin"
test -f "$game_managed/Assembly-CSharp.dll"
test -f "$game_managed/UnityEngine.dll"
test -f "$game_managed/UnityEngine.CoreModule.dll"
test -f "$bepinex_core/BepInEx.dll"
test -f "$bepinex_core/0Harmony.dll"
test -f "$package_source/microsoft.netframework.referenceassemblies.1.0.3.nupkg"
test "$(sha256sum "$game_managed/Assembly-CSharp.dll" | cut -d ' ' -f 1)" = \
  886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564
```

- [ ] **Step 3: Seed offline assets only when absent**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
package_source="$PWD/data/oracle/compat/fetch-acceptance"
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
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

These restores may change only ignored `obj` paths. Any network request,
NU1900 audit warning, tracked change, or package outside the local source is a
blocker.

- [ ] **Step 4: Run the exact accepted baseline**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
python -m pytest -q
```

Require zero C# warnings/errors, the exact line
`SSR oracle unit harness ready`, exactly 39 registered C# tests, and the full
Python suite green. Record counts and stdout/stderr separately.

---

### Task 1: Strict configuration and stable physical paths

**Files:**
- Create: `oracle/plugin/Core/OracleConfiguration.cs`
- Create: `oracle/plugin/Core/PhysicalPath.cs`
- Create: `oracle/plugin/tests/ConfigurationTests.cs`
- Create: `oracle/plugin/tests/PhysicalPathTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes: `OracleMode`, `OracleProtocol.ExpectedInputCount`,
  `OracleProtocol.MaxSettleFrames`, and `OracleProtocol.MaxSettleSeconds`.
- Produces: `OracleConfiguration.Load`, `OracleConfiguration.Parse`, immutable
  `PassiveConfiguration`, typed `OracleConfigurationException.Code`,
  `PhysicalPath`, and `PhysicalConfigurationPathResolver.Instance`.
- Later tasks consume only canonical `OutputDirectory`, `TracePath`, and
  `SaveDirectory`; they never reinterpret raw config text.

- [ ] **Step 1: Register the twelve configuration/path REDs**

Create the two test classes with these exact registrations:

```csharp
internal static class ConfigurationTests
{
    internal static void Register(TestRegistry tests, HarnessOptions options)
    {
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
}

internal static class PhysicalPathTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("path", "containment uses component boundary",
            ContainmentUsesComponentBoundary);
        tests.Add("path", "existing paths resolve canonically",
            ExistingPathsResolveCanonically);
        tests.Add("path", "missing suffix is preserved",
            MissingSuffixIsPreserved);
        tests.Add("path", "lexical paths are strict", LexicalPathsAreStrict);
        tests.Add("path", "symlink and nondirectory are rejected",
            SymlinkAndNondirectoryAreRejected);
        tests.Add("path", "two scan drift is rejected",
            TwoScanDriftIsRejected);
    }
```

Append registrations after `PassiveDriverTests.Register` and extend the
temporary manifest in exact reserved order:

```csharp
ConfigurationTests.Register(tests, options);
PhysicalPathTests.Register(tests);

// Existing seven rows remain unchanged, then:
{ "config", 6 },
{ "path", 6 }
```

Use a shared `AssertConfigCode(code, bytes, resolver)` helper and cover every
row below. Each row is one assertion inside the named registered method; do not
replace the table with representative sampling.

| Registered test | Input/case | Exact assertion |
|---|---|---|
| off grammar | LF and CRLF `[Oracle]`, `Mode = off`, optional legacy keys | Off; no passive value; resolver never called; input and retained bytes identical but not same array |
| off grammar | optional real fixture | SHA-256 `cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d` before/after; parser makes no write |
| off malformed | missing/duplicate/case-changed section or Mode; extra section; unknown/duplicate/case-changed key; `ExpectedPassiveInputs`; malformed line; inline comment; NUL; BOM; invalid UTF-8; bare CR | `invalid_configuration`, resolver uncalled |
| unsupported modes | empty, `Passive`, `replay`, and arbitrary value | `invalid_mode` |
| passive canonical | exact active grammar and fake canonical paths | every immutable property exact; resolver calls output then save; TracePath is canonical output plus safe leaf |
| passive failures | every missing/extra key; noncanonical value; unsafe RunName; same/nested paths; resolver failure | grammar/value -> `invalid_configuration`; topology/filesystem -> `invalid_path` |
| configuration reads | missing, denied, null result, and unexpected source exception | exactly one read; `invalid_configuration`; original exception retained as `InnerException` |
| containment | equal, child, lexical sibling, unrelated, root | `true,true,false,false,true` |
| existing paths | root and nested directory | canonical identity, existing ancestor, empty missing suffix |
| missing suffix | one and multiple missing components | preserved component order; canonical path appends each exact component |
| lexical strictness | relative, empty, NUL, `.`/`..`, duplicate separator, trailing separator except root | `invalid_path` before native operation |
| symlink/nondirectory | symlink at every existing component; file before leaf; missing required directory | `invalid_path` |
| two-scan drift | kind, symlink, canonical spelling, missing suffix, or target existence changes between scans | `invalid_path`; injected between-scan callback runs once |

The test fakes expose calls rather than copying the production algorithm:

```csharp
internal sealed class StaticConfigurationBytes : IConfigurationBytes
{
    private readonly byte[] bytes;
    internal int ReadCount;
    internal string LastPath;

    internal StaticConfigurationBytes(byte[] bytes) { this.bytes = bytes; }
    public byte[] ReadAllBytes(string configPath)
    {
        ReadCount++;
        LastPath = configPath;
        return bytes == null ? null : (byte[])bytes.Clone();
    }
}

internal sealed class FakeConfigurationPathResolver
    : IConfigurationPathResolver
{
    internal readonly Queue<string> Resolved = new Queue<string>();
    internal readonly List<string> Calls = new List<string>();
    internal bool ContainsResult;
    internal Exception Failure;

    public string ResolveExistingDirectory(string requested)
    {
        Calls.Add("directory:" + requested);
        if (Failure != null) throw Failure;
        return Resolved.Dequeue();
    }
    public bool Contains(string parent, string candidate)
    {
        Calls.Add("contains:" + parent + ":" + candidate);
        return ContainsResult;
    }
}
```

- [ ] **Step 2: Run the intended configuration/path RED**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore \
  --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false
```

Require compiler errors naming `OracleConfiguration`,
`IConfigurationBytes`, and `PhysicalPath`. No existing test may fail first.

- [ ] **Step 3: Implement the exact configuration surface**

Create `OracleConfiguration.cs` with these complete public-to-task interfaces:

```csharp
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;

internal interface IConfigurationBytes
{
    byte[] ReadAllBytes(string configPath);
}

internal interface IConfigurationPathResolver
{
    string ResolveExistingDirectory(string requested);
    bool Contains(string parent, string candidate);
}

internal sealed class OracleConfigurationException : Exception
{
    internal OracleConfigurationException(string code, Exception inner)
        : base(code, inner)
    {
        if (code != "invalid_mode" && code != "invalid_configuration"
            && code != "invalid_path")
            throw new ArgumentException("invalid configuration code", "code");
        Code = code;
    }
    internal string Code { get; private set; }
}

internal sealed class PassiveConfiguration
{
    internal PassiveConfiguration(
        string outputDirectory, string runName, string tracePath,
        string saveDirectory)
    {
        OutputDirectory = outputDirectory;
        RunName = runName;
        TracePath = tracePath;
        SaveDirectory = saveDirectory;
        ExpectedInputCount = OracleProtocol.ExpectedInputCount;
        MaxSettleFrames = OracleProtocol.MaxSettleFrames;
        MaxSettleSeconds = OracleProtocol.MaxSettleSeconds;
    }
    internal string OutputDirectory { get; private set; }
    internal string RunName { get; private set; }
    internal string TracePath { get; private set; }
    internal string SaveDirectory { get; private set; }
    internal int ExpectedInputCount { get; private set; }
    internal int MaxSettleFrames { get; private set; }
    internal double MaxSettleSeconds { get; private set; }
}

internal sealed class OracleConfiguration
{
    private static readonly UTF8Encoding StrictUtf8 =
        new UTF8Encoding(false, true);

    private OracleConfiguration(OracleMode mode, PassiveConfiguration passive)
    {
        Mode = mode;
        Passive = passive;
    }

    internal OracleMode Mode { get; private set; }
    internal PassiveConfiguration Passive { get; private set; }

    internal static OracleConfiguration Load(
        string configPath, IConfigurationBytes source,
        IConfigurationPathResolver paths, out byte[] originalBytes)
    {
        if (source == null) throw new ArgumentNullException("source");
        byte[] bytes;
        try { bytes = source.ReadAllBytes(configPath); }
        catch (Exception error)
        {
            throw Failure("invalid_configuration", error);
        }
        if (bytes == null)
            throw Failure("invalid_configuration",
                new IOException("configuration source returned null"));
        originalBytes = (byte[])bytes.Clone();
        return Parse(bytes, paths);
    }

    internal static OracleConfiguration Parse(
        byte[] bytes, IConfigurationPathResolver paths)
    {
        Dictionary<string, string> values = ParseEntries(bytes);
        string mode = Require(values, "Mode");
        if (mode == "off")
        {
            RequireOnly(values, new string[] {
                "Mode", "OutputDirectory", "RunName", "SaveDirectory",
                "InputPath", "MaxSettleFrames", "MaxSettleSeconds",
                "ExpectedInitialSha256" });
            return new OracleConfiguration(OracleMode.Off, null);
        }
        if (mode != "passive")
            throw Failure("invalid_mode",
                new FormatException("unsupported Mode"));
        if (paths == null) throw new ArgumentNullException("paths");
        RequireOnly(values, new string[] {
            "Mode", "OutputDirectory", "RunName", "SaveDirectory",
            "ExpectedPassiveInputs", "MaxSettleFrames", "MaxSettleSeconds" });
        RequireExactKeys(values, new string[] {
            "Mode", "OutputDirectory", "RunName", "SaveDirectory",
            "ExpectedPassiveInputs", "MaxSettleFrames", "MaxSettleSeconds" });
        if (Require(values, "ExpectedPassiveInputs") != "3"
            || Require(values, "MaxSettleFrames") != "600"
            || Require(values, "MaxSettleSeconds") != "30")
            throw Failure("invalid_configuration",
                new FormatException("passive numeric values are not canonical"));
        string runName = Require(values, "RunName");
        RequireSafeRunName(runName);
        try
        {
            string output = paths.ResolveExistingDirectory(
                Require(values, "OutputDirectory"));
            string save = paths.ResolveExistingDirectory(
                Require(values, "SaveDirectory"));
            if (paths.Contains(output, save) || paths.Contains(save, output))
                throw new IOException("active directories overlap");
            string trace = Path.Combine(output, runName + ".ndjson");
            return new OracleConfiguration(OracleMode.Passive,
                new PassiveConfiguration(output, runName, trace, save));
        }
        catch (OracleConfigurationException) { throw; }
        catch (Exception error) { throw Failure("invalid_path", error); }
    }
}
```

The preceding excerpt intentionally stops before the
`OracleConfiguration` closing brace. Place these private helpers next, then
close that class and declare `FileConfigurationBytes`; all parser errors are
typed `invalid_configuration`:

```csharp
private static Dictionary<string, string> ParseEntries(byte[] bytes)
{
    try
    {
        if (bytes == null || bytes.Length == 0)
            throw new FormatException("configuration is empty");
        if (bytes.Length >= 3 && bytes[0] == 0xef
            && bytes[1] == 0xbb && bytes[2] == 0xbf)
            throw new FormatException("UTF-8 BOM is forbidden");
        string text = StrictUtf8.GetString(bytes);
        if (text.IndexOf('\0') >= 0)
            throw new FormatException("NUL is forbidden");
        for (int index = 0; index < text.Length; index++)
        {
            if (text[index] == '\r'
                && (index + 1 >= text.Length || text[index + 1] != '\n'))
                throw new FormatException("bare CR is forbidden");
        }
        text = text.Replace("\r\n", "\n");
        Dictionary<string, string> values =
            new Dictionary<string, string>(StringComparer.Ordinal);
        bool sawSection = false;
        string[] lines = text.Split(new char[] { '\n' });
        for (int index = 0; index < lines.Length; index++)
        {
            string line = TrimAscii(lines[index]);
            if (line.Length == 0 || line[0] == '#' || line[0] == ';')
                continue;
            if (line[0] == '[')
            {
                if (line != "[Oracle]" || sawSection)
                    throw new FormatException("invalid section");
                sawSection = true;
                continue;
            }
            if (!sawSection)
                throw new FormatException("entry precedes Oracle section");
            int separator = line.IndexOf('=');
            if (separator <= 0 || separator != line.LastIndexOf('='))
                throw new FormatException("invalid entry");
            string key = TrimAscii(line.Substring(0, separator));
            string value = TrimAscii(line.Substring(separator + 1));
            if (key.Length == 0 || value.IndexOf('#') >= 0
                || value.IndexOf(';') >= 0 || values.ContainsKey(key))
                throw new FormatException("invalid or duplicate entry");
            values.Add(key, value);
        }
        if (!sawSection || !values.ContainsKey("Mode"))
            throw new FormatException("Oracle Mode is required");
        return values;
    }
    catch (OracleConfigurationException) { throw; }
    catch (Exception error)
    { throw Failure("invalid_configuration", error); }
}

private static string TrimAscii(string value)
{
    int first = 0;
    int last = value.Length;
    while (first < last && (value[first] == ' ' || value[first] == '\t'))
        first++;
    while (last > first
        && (value[last - 1] == ' ' || value[last - 1] == '\t'))
        last--;
    return value.Substring(first, last - first);
}

private static string Require(
    IDictionary<string, string> values, string key)
{
    string value;
    if (!values.TryGetValue(key, out value) || value.Length == 0)
        throw Failure("invalid_configuration",
            new FormatException(key + " is required"));
    return value;
}

private static void RequireOnly(
    IDictionary<string, string> values, string[] allowed)
{
    foreach (string key in values.Keys)
    {
        bool found = false;
        for (int index = 0; index < allowed.Length; index++)
            found |= key == allowed[index];
        if (!found)
            throw Failure("invalid_configuration",
                new FormatException("unknown key: " + key));
    }
}

private static void RequireExactKeys(
    IDictionary<string, string> values, string[] required)
{
    for (int index = 0; index < required.Length; index++)
        if (!values.ContainsKey(required[index]))
            throw Failure("invalid_configuration",
                new FormatException("missing key: " + required[index]));
}

private static void RequireSafeRunName(string value)
{
    if (value == "." || value == ".." || value.IndexOf('/') >= 0
        || value.IndexOf('\\') >= 0 || value.IndexOf('\0') >= 0
        || Path.GetFileName(value) != value
        || value.EndsWith(".ndjson", StringComparison.Ordinal))
        throw Failure("invalid_configuration",
            new FormatException("unsafe RunName"));
}

private static OracleConfigurationException Failure(
    string code, Exception error)
{
    return new OracleConfigurationException(code, error);
}

}

internal sealed class FileConfigurationBytes : IConfigurationBytes
{
    public byte[] ReadAllBytes(string configPath)
    { return File.ReadAllBytes(configPath); }
}
```

Use `StringComparer.Ordinal` and invariant conversions only. `Load` returns a
clone in `originalBytes`; it never writes, opens a `FileStream`, or consults
BepInEx.

- [ ] **Step 4: Implement the exact physical-path surface**

Create `PhysicalPath.cs` with this type surface:

```csharp
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;

internal enum PhysicalPathKind { Missing, Directory, File, Symlink, Other }

internal sealed class PhysicalPathIdentity
{
    internal PhysicalPathIdentity(
        string canonicalPath, bool exists, string existingAncestor,
        string[] missingComponents)
    {
        CanonicalPath = canonicalPath;
        Exists = exists;
        ExistingAncestor = existingAncestor;
        MissingComponents = missingComponents;
    }
    internal string CanonicalPath { get; private set; }
    internal bool Exists { get; private set; }
    internal string ExistingAncestor { get; private set; }
    internal string[] MissingComponents { get; private set; }
}

internal interface IPhysicalPathOperations
{
    PhysicalPathKind Classify(string absolutePath);
    string RealPath(string existingPath);
}

internal static class PhysicalPath
{
    internal static string ResolveExistingDirectory(string requested)
    {
        return ResolveExistingDirectory(
            requested, MacPhysicalPathOperations.Instance, null);
    }
    internal static PhysicalPathIdentity ResolvePossiblyAbsent(string requested)
    {
        return ResolvePossiblyAbsent(
            requested, MacPhysicalPathOperations.Instance, null);
    }
    internal static bool Contains(string parent, string candidate)
    {
        if (parent == "/") return candidate.StartsWith("/", StringComparison.Ordinal);
        return candidate == parent || candidate.StartsWith(
            parent + "/", StringComparison.Ordinal);
    }
}

internal sealed class PhysicalConfigurationPathResolver
    : IConfigurationPathResolver
{
    internal static readonly PhysicalConfigurationPathResolver Instance =
        new PhysicalConfigurationPathResolver();
    private PhysicalConfigurationPathResolver() { }
    public string ResolveExistingDirectory(string requested)
    { return PhysicalPath.ResolveExistingDirectory(requested); }
    public bool Contains(string parent, string candidate)
    { return PhysicalPath.Contains(parent, candidate); }
}
```

Implement the injected overloads using one shared `Scan` transaction:

```text
ValidateLexical(requested):
  require absolute POSIX spelling, root or no trailing '/', no empty component,
  no '.'/'..', no NUL, and Path.GetFullPath(requested) ordinal-equal requested

Scan(requested, operations):
  classify '/', then every cumulative component
  reject Symlink/Other immediately and File before the final existing leaf
  stop at first Missing; remaining components are a preserved missing suffix
  realpath the deepest existing directory
  append missing components without normalization
  return PhysicalPathIdentity(canonical, exists, ancestor, suffix)

Resolve*(requested, operations, betweenScans):
  first = Scan(...)
  invoke betweenScans once when nonnull
  second = Scan(...)
  require all identity fields and missing components ordinal-equal
  existing-directory form requires Exists and final Directory
  return the second authenticated value

```

`MacPhysicalPathOperations` uses `lstat`, `readlink`, and `realpath` from
`libc`. A successful `readlink` means symlink; `EINVAL` alone means not a
symlink; `ENOENT` means missing. Every buffer is instance-local, bounded to
`PATH_MAX = 1024`, NUL-terminated explicitly, and decoded with strict UTF-8.
Any other errno or overlong result becomes `OracleConfigurationException(
"invalid_path", inner)` at the public boundary.

Add production overloads to `OracleConfiguration`:

```csharp
internal static OracleConfiguration Parse(byte[] bytes)
{
    return Parse(bytes, PhysicalConfigurationPathResolver.Instance);
}

internal static OracleConfiguration Load(
    string configPath, out byte[] originalBytes)
{
    return Load(configPath, new FileConfigurationBytes(),
        PhysicalConfigurationPathResolver.Instance, out originalBytes);
}
```

`FileConfigurationBytes.ReadAllBytes` performs exactly one
`File.ReadAllBytes(configPath)` call.

- [ ] **Step 5: Run focused and compatibility GREEN**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- --cohort config
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- --cohort path
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
```

Require both cohorts to print exactly one ready line and net35 to report zero
warnings/errors. Do not commit; retain the exact diff and evidence for the
single Task 6.1 review.

---

### Task 2: Observation policy, exact game contract, and sole adapter

**Files:**
- Create: `oracle/plugin/Core/GameObservation.cs`
- Create: `oracle/plugin/Core/OracleRuntimeBoundaries.cs`
- Create: `oracle/plugin/GameContract.cs`
- Create: `oracle/plugin/GameAdapter.cs`
- Create: `oracle/plugin/tests/GameObservationTests.cs`
- Create: `oracle/plugin/tests/AssemblySurfaceTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes: `CaptureRecord`, `CaptureException`, `PhysicalPath`, and canonical
  save directory from Task 1.
- Produces: `GameGateValues`, `CaptureValues`, `CaptureMapping`,
  `IOracleGameAdapter`, `GameContract.ValidateLegacySurface`,
  `GameContract.ValidatePassiveSurface`, and `GameAdapter`.
- Task 3 consumes only the object-typed adapter interface; game types do not
  cross into Core.

- [ ] **Step 1: Add the observation, assembly, and first plugin REDs**

Create exact registrations:

```csharp
internal static class GameObservationTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("observation", "all thirteen gates are required",
            EveryGateRequired);
        tests.Add("observation", "capture maps all twelve fields", MapsAllFields);
        tests.Add("observation", "three nullable strings normalize",
            NullableStringsNormalize);
        tests.Add("observation", "required values reject null",
            RequiredValuesRejectNull);
        tests.Add("observation", "numeric ranges reject negative",
            NegativeNumbersReject);
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
        tests.Add("plugin", "game adapter call surface is passive",
            delegate { AdapterCallSurface(options.PluginPath); });
    }
}
```

Append registrations and rows after `path`:

```csharp
GameObservationTests.Register(tests);
AssemblySurfaceTests.Register(tests, options);

{ "observation", 5 },
{ "assembly", 4 },
{ "plugin", 1 }
```

The observation methods are table-driven but exhaustive:

```csharp
private static void EveryGateRequired()
{
    bool[] all = new bool[13];
    for (int index = 0; index < all.Length; index++) all[index] = true;
    Check.True(GameObservationPolicy.IsQuiescent(Gates(all)), "all gates");
    for (int index = 0; index < all.Length; index++)
    {
        bool[] changed = (bool[])all.Clone();
        changed[index] = false;
        Check.False(GameObservationPolicy.IsQuiescent(Gates(changed)),
            "gate " + index.ToString());
    }
}

private static void MapsAllFields()
{
    CaptureRecord value = CaptureMapping.Create(new CaptureValues(
        "raw", "-17", "level", true, false, true, false,
        "lost", "display", Int32.MaxValue, Int32.MaxValue, Int32.MaxValue));
    Check.Equal("raw", value.RawSave, "raw");
    Check.Equal("-17", value.StateIdentity, "identity");
    Check.Equal("level", value.Level, "level");
    Check.True(value.Overworld, "overworld");
    Check.False(value.Won, "won");
    Check.True(value.Returning, "returning");
    Check.False(value.HaveEverCookedAll, "cooked all");
    Check.Equal("lost", value.LostReason, "lost");
    Check.Equal("display", value.DisplayName, "display");
    Check.Equal(Int32.MaxValue, value.SausagesCooked, "cooked");
    Check.Equal(Int32.MaxValue, value.MovementCount, "movement");
    Check.Equal(Int32.MaxValue, value.PushesToTry, "pushes");
}
```

`NullableStringsNormalize` passes null for level/lost/display and requires
three empty strings. `RequiredValuesRejectNull` checks null values, raw save,
and identity. `NegativeNumbersReject` loops `(-1,0,0)`, `(0,-1,0)`, and
`(0,0,-1)` and requires `CaptureException`.

The metadata reader opens files only through `FileStream` + `PEReader`; it
never uses `Assembly.Load`. Its exact characterization tables are:

```text
Methods:
Game private instance void Update()
Game private instance void DoPlayerInput()
Game private instance Direction Playerinputstring()
GameState public instance bool ProcessInput(Direction)
Game public instance void DoUndo()
Game private instance void RestorePrevState(GameState/BakStruct)
Game public instance void DoRestart()
Game public instance void SetGameState(GameState)
GameState public instance bool Moving()
GameState public instance string Save(bool,bool)

Direction literals: North=0, South=1, West=2, East=3, None=8

Fields:
Game public instance GameState gamestate
Game public instance bool exitSequence
Game public instance bool bluespawnanim
Game public instance UnityEngine/GameObject escmenu
Game public static bool endingsequence
Game private instance bool leaving
Game private instance bool gameover
Game private instance bool exploding
GameState public instance Entity player
GameState public instance List<Movement> movements
GameState public instance List<Coord> worldsausagespawns
GameState public instance int32 pushestotry
GameState public instance string pushtargetlevel
GameState public instance bool overworld
GameState public instance bool won
GameState public instance bool returning
GameState public instance bool haveevercookedall
GameState public instance string lostreason
GameState public instance string displayname
GameState public instance int32 sausagescooked
GameState public static Coord shouldredrawcoffins
SaveGame public static string homePath
SaveGame public static string PersistentDataPath
```

`SyntheticMatcherRejectsNearMisses` constructs in-memory `MethodShape` and
`FieldShape` values and proves wrong visibility, static flag, return type,
parameter type, field type, and enum value each fail. `AdapterCallSurface`
inspects the built plugin IL and requires exactly two direct game calls from
`GameAdapter`: `GameState.Moving()` and `GameState.Save(bool,bool)`, with
literal `false,false` before Save. It rejects calls to `ProcessInput`,
`DoPlayerInput`, `DoUndo`, `DoRestart`, `SetGameState`, or another gameplay
method.

- [ ] **Step 2: Capture the intended observation/metadata REDs**

First run the Core build and require missing `GameGateValues`/
`GameObservationPolicy`. Then build the unchanged plugin and run the metadata
cohorts; assembly must pass and plugin must fail specifically because
`GameAdapter` is absent.

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false -p:GameManagedDir="$game_managed" \
  -p:BepInExCoreDir="$bepinex_core"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort assembly \
  --assembly "$game_managed/Assembly-CSharp.dll"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

Because the first Core build is an intentional failure, execute these as four
recorded commands rather than one `set -e` shell in the real run.

- [ ] **Step 3: Implement the complete observation policy**

Create `GameObservation.cs`:

```csharp
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
```

- [ ] **Step 4: Define the object-typed adapter boundary and exact ABI**

Create the first part of `OracleRuntimeBoundaries.cs`:

```csharp
using System;

internal interface IOracleGameAdapter
{
    void AuthenticateAndRedirectSavePath(string isolatedPath);
    bool VerifySavePath();
    bool TryGetState(object game, out object stateReference);
    bool IsQuiescent(object game, object verifiedState);
    bool MovementScheduled(object stateReference);
    bool CurrentMovementScheduled(object game);
    CaptureRecord Capture(object verifiedState);
}
```

Create `GameContract.cs`. `ValidateLegacySurface()` requires only
`Playerinputstring`, `DoPlayerInput`, and `ProcessInput`. `ValidatePassiveSurface()`
first calls the legacy validator, then requires all ten methods, all fields,
and all Direction literals in the tables from Step 1. Use exact helpers:

```csharp
private static MethodInfo RequireMethod(
    Type owner, string name, BindingFlags flags,
    Type returnType, Type[] parameters)
{
    MethodInfo method = owner.GetMethod(name, flags, null, parameters, null);
    if (method == null || method.ReturnType != returnType
        || method.IsStatic != ((flags & BindingFlags.Static) != 0))
        throw new MissingMethodException(owner.FullName, name);
    return method;
}

private static FieldInfo RequireField(
    Type owner, string name, BindingFlags flags, Type fieldType)
{
    FieldInfo field = owner.GetField(name, flags);
    if (field == null || field.FieldType != fieldType
        || field.IsStatic != ((flags & BindingFlags.Static) != 0))
        throw new MissingFieldException(owner.FullName, name);
    return field;
}
```

`Game.RestorePrevState` must use `typeof(GameState.BakStruct)`. Reflection
errors must occur before any Harmony call.

- [ ] **Step 5: Implement the sole game adapter**

Create `GameAdapter.cs` as `internal sealed class GameAdapter :
IOracleGameAdapter`. It owns private reflected `Game.leaving`, `gameover`, and
`exploding` fields and no static mutable state.

```csharp
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

}
```

The method blocks below are placed inside this class before its closing brace;
the shell above shows the exact fields and constructor, not a second class.

The save transaction is exact:

```csharp
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
```

The observation methods use strict casts. Wrap the body of each public method
in `try/catch (CaptureException) { throw; } / catch (Exception error)` and map
to the exact method-specific `CaptureException` message shown below; no raw
game/reflection exception crosses the adapter:

```csharp
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
    return MovementScheduled(game.gamestate);
}
```

`IsQuiescent(gameValue, stateValue)` requires both exact types, a nonnull
`worldsausagespawns`, and constructs `GameGateValues` in this order:

```csharp
new GameGateValues(
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
    state.worldsausagespawns.Count == 0)
```

`Capture(stateValue)` requires `player`, `movements`, and
`worldsausagespawns`, calls `state.Save(false, false)` exactly once, rejects a
null result, and maps:

```csharp
new CaptureValues(
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
    state.pushestotry)
```

Do not call `GameState.Lost`, normalize the state, cache a state across
callbacks, or restore the ordinary save path.

- [ ] **Step 6: Run all Task 2 GREEN gates**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- --cohort observation
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- --cohort assembly \
  --assembly "$game_managed/Assembly-CSharp.dll"
"$dotnet_bin" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false -p:GameManagedDir="$game_managed" \
  -p:BepInExCoreDir="$bepinex_core"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
```

Require observation 5, assembly 4, plugin 1, zero build warnings/errors, and
no game process. Do not commit.

---

### Task 3: Patch firewalls, mode policy, startup ownership, and markers

**Files:**
- Extend: `oracle/plugin/Core/OracleRuntimeBoundaries.cs`
- Create: `oracle/plugin/Core/PatchBoundary.cs`
- Create: `oracle/plugin/Core/PassiveReporter.cs`
- Create: `oracle/plugin/Core/PluginModePolicy.cs`
- Create: `oracle/plugin/Core/PassiveStartup.cs`
- Create: `oracle/plugin/tests/PatchBoundaryTests.cs`
- Create: `oracle/plugin/tests/PassiveStartupTests.cs`
- Create: `oracle/plugin/tests/PassiveReporterTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes: typed config, existing `HookToken`, `PassiveDriver`, and Run model.
- Produces: a callback firewall, capability-free Off path, exact passive log
  reporter, and one ordered/idempotent startup owner.
- Task 4 implements the real service interfaces; these tests use fakes and the
  real driver only.

- [ ] **Step 1: Register all sixteen REDs in reserved order**

```csharp
internal static class PatchBoundaryTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("boundary", "postfix contains observer failures",
            ObserveContainsFailures);
        tests.Add("boundary", "game exception claims before cleanup",
            GameFailurePrecedesCleanup);
        tests.Add("boundary", "successful postfix makes finalizer cleanup inert",
            ConsumedTokenIsInert);
        tests.Add("boundary", "cleanup failure is contained and reported",
            CleanupFailureIsContained);
        tests.Add("boundary", "update finalizer preserves original reference",
            UpdateFinalizerPreservesOriginalException);
    }
}

internal static class PassiveStartupTests
{
    internal static void Register(TestRegistry tests)
    {
        tests.Add("startup", "off invokes only legacy validation then boot",
            OffCallsAreExact);
        tests.Add("startup", "off preserves legacy failure identity",
            LegacyFailureIdentity);
        tests.Add("startup",
            "run flush precedes patches and activation precedes boot", StartOrder);
        tests.Add("startup", "typed pre-driver failures stay marker only",
            PreDriverFailures);
        tests.Add("startup", "prepare failure is not reported twice",
            PrepareFailure);
        tests.Add("startup", "owned startup failures use driver arbitration",
            OwnedFailures);
        tests.Add("startup", "teardown is ordered and idempotent",
            TeardownIsIdempotent);
    }
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
}
```

Register after observation and before assembly/plugin:

```csharp
PatchBoundaryTests.Register(tests);
PassiveStartupTests.Register(tests);
PassiveReporterTests.Register(tests);

{ "boundary", 5 },
{ "startup", 7 },
{ "reporter", 4 }
```

The firewall tests use real `HookToken.Issued` values and require:

```csharp
Exception returned = PatchBoundary.Finalize(
    token, original,
    delegate(HookToken value) { events.Add("clear"); value.TryConsume(); },
    delegate { events.Add("game"); },
    delegate { events.Add("observer"); });
Check.Same(original, returned, "original identity");
Check.Sequence(new string[] { "game", "clear" }, events.ToArray(),
    "game failure owns before cleanup");
```

Also require: postfix exception calls `observerFailed` once even when that
callback throws; a consumed token clears zero times; cleanup failure is
reported once and contained; `FinalizeUpdate(null,...)` is inert; and a
non-null update exception is returned by reference.

The startup fake records exact events. `StartOrder` requires:

```text
validate, redirect, create-driver, sink:run,
install:Disabled, boot:AwaitGame
```

`PreDriverFailures` injects these exact stage/code pairs:

```text
validate: invalid_configuration, invalid_assembly, invalid_reflection,
          invalid_path, trace_exists
redirect: save_redirect_failed
create-driver: trace_exists, trace_io_failed
```

Each produces one marker-only failure, no Run, no patch installation, and no
driver failure. `PrepareFailure` injects Run I/O failure and requires only the
driver's `trace_io_failed`. `OwnedFailures` injects install, activation, and
boot failures and requires respectively `patch_install_failed`,
`observer_exception`, and `observer_exception`, followed by disable/unpatch.
`TeardownIsIdempotent` calls Dispose twice and requires one disable, one
owner-only unpatch, one sink close, and no fabricated terminal record.

Reporter assertions are exact:

```text
Info:    SSR oracle passive trace ready: 0/3
         SSR oracle passive trace ready: 1/3
         SSR oracle passive trace ready: 2/3
Info:    SSR oracle passive trace complete
Error:   SSR oracle passive trace failed: <closed code>
Warning: SSR oracle passive diagnostic: <non-null text>
```

Loop every `OracleErrors` record code plus every `OracleMarkerErrors` code and
reject `unknown`; reject Ready `-1` and `3`.

- [ ] **Step 2: Run the intended missing-surface RED**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release --no-restore \
  --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false
```

Require compiler errors naming `PatchBoundary`, `PluginModePolicy`,
`PassiveStartup`, and `PassiveLogReporter` only after all earlier cohorts can
compile.

- [ ] **Step 3: Implement the complete callback firewall**

Create `PatchBoundary.cs`:

```csharp
using System;

internal static class PatchBoundary
{
    internal static void Observe(Action callback, Action observerFailed)
    {
        try
        {
            if (callback == null) throw new ArgumentNullException("callback");
            callback();
        }
        catch (Exception) { Try(observerFailed); }
    }

    internal static Exception Finalize(
        HookToken token, Exception original, Action<HookToken> clear,
        Action gameMethodFailed, Action observerFailed)
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
            catch (Exception) { observerWorkFailed = true; }
        }
        if (token != null && token.Active)
        {
            try
            {
                if (clear == null) throw new ArgumentNullException("clear");
                clear(token);
            }
            catch (Exception) { observerWorkFailed = true; }
        }
        if (observerWorkFailed) Try(observerFailed);
        return original;
    }

    internal static Exception FinalizeUpdate(
        Exception original, Action gameMethodFailed, Action observerFailed)
    {
        if (original != null)
        {
            try
            {
                if (gameMethodFailed == null)
                    throw new ArgumentNullException("gameMethodFailed");
                gameMethodFailed();
            }
            catch (Exception) { Try(observerFailed); }
        }
        return original;
    }

    private static void Try(Action callback)
    {
        try { if (callback != null) callback(); }
        catch (Exception) { }
    }
}
```

- [ ] **Step 4: Implement Off policy and exact reporter**

Add `IPassiveLog` to `OracleRuntimeBoundaries.cs`:

```csharp
internal interface IPassiveLog
{
    void Info(string message);
    void Error(string message);
    void Warning(string message);
}
```

Create `PluginModePolicy.cs`:

```csharp
using System;

internal static class PluginModePolicy
{
    internal static void StartOff(
        OracleConfiguration configuration,
        Action validateLegacySurface,
        Action emitBootMarker)
    {
        if (configuration == null) throw new ArgumentNullException("configuration");
        if (validateLegacySurface == null)
            throw new ArgumentNullException("validateLegacySurface");
        if (emitBootMarker == null) throw new ArgumentNullException("emitBootMarker");
        if (configuration.Mode != OracleMode.Off)
            throw new OracleConfigurationException("invalid_mode",
                new ArgumentException("Off policy requires off mode"));
        validateLegacySurface();
        emitBootMarker();
    }
}
```

Create `PassiveReporter.cs`:

```csharp
using System;
using System.Globalization;

internal sealed class PassiveLogReporter : IPassiveReporter
{
    private readonly IPassiveLog log;
    internal PassiveLogReporter(IPassiveLog log)
    { this.log = log ?? throw new ArgumentNullException("log"); }

    public void Ready(int completedInputs)
    {
        if (completedInputs < 0
            || completedInputs >= OracleProtocol.ExpectedInputCount)
            throw new ArgumentOutOfRangeException("completedInputs");
        log.Info("SSR oracle passive trace ready: "
            + completedInputs.ToString(CultureInfo.InvariantCulture) + "/3");
    }
    public void Complete()
    { log.Info("SSR oracle passive trace complete"); }
    public void Failed(string code)
    {
        if (!OracleErrors.IsRecordCode(code)
            && !OracleMarkerErrors.IsMarkerOnly(code))
            throw new ArgumentException("unknown passive failure code", "code");
        log.Error("SSR oracle passive trace failed: " + code);
    }
    public void Diagnostic(string message)
    {
        if (message == null) throw new ArgumentNullException("message");
        log.Warning("SSR oracle passive diagnostic: " + message);
    }
}
```

- [ ] **Step 5: Implement ordered startup and teardown**

Create `PassiveStartup.cs`:

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
        if (code != "invalid_mode" && code != "invalid_configuration"
            && code != "invalid_assembly" && code != "invalid_reflection"
            && code != "invalid_path" && code != "trace_exists"
            && code != "save_redirect_failed" && code != "trace_io_failed")
            throw new ArgumentException("invalid startup code", "code");
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
    { this.services = services ?? throw new ArgumentNullException("services"); }

    internal bool Start(RunRecord run)
    {
        if (started) throw new InvalidOperationException("startup already attempted");
        if (run == null) throw new ArgumentNullException("run");
        started = true;
        try
        {
            services.ValidateBeforeSink();
            services.AuthenticateAndRedirectSave();
            driver = services.CreateDriver();
            if (driver == null)
                throw new PassiveStartupException("trace_io_failed",
                    new InvalidOperationException("driver factory returned null"));
        }
        catch (PassiveStartupException error)
        {
            SafeMarker(error.Code);
            return false;
        }
        if (!driver.Prepare(run)) return false;
        patchesMayExist = true;
        try { services.InstallPatches(); }
        catch (Exception error)
        {
            SafeDiagnostic(error); OwnedFailure("patch_install_failed"); return false;
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
            SafeDiagnostic(error); OwnedFailure("observer_exception"); return false;
        }
    }

    public void Dispose()
    {
        if (disposed) return;
        disposed = true;
        SafeDisable(); SafeUnpatch();
        if (driver != null)
        {
            try { driver.Dispose(); }
            catch (Exception error) { SafeDiagnostic(error); }
        }
    }

    private void OwnedFailure(string code)
    {
        try { driver.TryFault(code); }
        catch (Exception error) { SafeDiagnostic(error); }
        SafeDisable(); SafeUnpatch();
    }
    private void SafeDisable()
    {
        if (driver == null) return;
        try { driver.Disable(); }
        catch (Exception error) { SafeDiagnostic(error); }
    }
    private void SafeUnpatch()
    {
        if (!patchesMayExist) return;
        patchesMayExist = false;
        try { services.UnpatchSelf(); }
        catch (Exception error) { SafeDiagnostic(error); }
    }
    private void SafeMarker(string code)
    {
        try { services.MarkerOnlyFailed(code); }
        catch (Exception error) { SafeDiagnostic(error); }
    }
    private void SafeDiagnostic(Exception error)
    {
        try { services.Diagnostic(error.GetType().FullName); }
        catch (Exception) { }
    }
}
```

- [ ] **Step 6: Run focused and compatibility GREEN**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
for cohort_name in boundary startup reporter; do
  "$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
    -c Release --no-restore --no-build -- --cohort "$cohort_name"
done
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
```

Require counts 5/7/4, exact markers, zero warnings/errors, and no commit.

---

### Task 4: Unity-free controller, exact Harmony hooks, and plugin shell

**Files:**
- Create: `oracle/plugin/Core/OracleController.cs`
- Extend: `oracle/plugin/Core/OracleRuntimeBoundaries.cs`
- Create: `oracle/plugin/GameHooks.cs`
- Replace: `oracle/plugin/Plugin.cs`
- Modify: `oracle/plugin/SsrOracle.Plugin.csproj`
- Modify: `oracle/plugin/Core/OracleProtocol.cs`
- Modify: `oracle/plugin/tests/EncodingTests.cs`
- Modify: `oracle/plugin/tests/AssemblySurfaceTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`
- Modify: `src/ssr_env/oracle_protocol.py`
- Modify: `tests/test_oracle_protocol.py`
- Modify: `tests/fixtures/oracle_trace/passive-success.ndjson`
- Modify: `tests/fixtures/oracle_trace/passive-error.ndjson`

**Interfaces:**
- Consumes: all Task 1-3 Core policies and the accepted driver hook surface.
- Produces: `OracleController`, eight exact patch targets, one typed plugin
  shell, and Task 6 protocol/plugin version `0.3.0`.
- Task 6.2 will extend `Game.Update`/`Playerinputstring` behavior through this
  controller; it must not move game types into Core.

- [ ] **Step 1: Raise the plugin metadata tests to their final six**

Replace only `AssemblySurfaceTests.Register` with:

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

Set the final row `{ "plugin", 6 }`. The full manifest is now exactly 82:

```text
protocol 4, encoding 5, sink 6,
driver-boundary 2, driver-initial 8, driver-input 8, driver-terminal 6,
config 6, path 6, observation 5, boundary 5, startup 7, reporter 4,
assembly 4, plugin 6
```

The five new plugin assertions are exact:

| Test | Required artifact relation |
|---|---|
| controller boundary | `OracleController.ObserveUpdate` constructs `PassiveUpdateBoundary`/`IPassiveUpdateObservation`; calls adapter in `state, now, path, state, gate, capture, utc` order; only ProcessInput/Undo normal returns call movement methods |
| patch contracts | exactly eight `[HarmonyPatch]` types and the callback matrix below; all finalizers return `System.Exception`; only `out HookToken __state` is by-ref |
| PE/references | PE32 AnyCPU, CLR v2 metadata, no PDB, direct refs limited to mscorlib/System/System.Core/BepInEx/0Harmony/Assembly-CSharp/UnityEngine.CoreModule; no copied external DLL |
| plugin identity | GUID `dev.jlsor.ssr.oracle`, name `SSR Executable Oracle`, version `0.3.0` |
| modes/teardown | Off calls only legacy validation + boot; passive owns `dev.jlsor.ssr.oracle.passive`; no replay branch; `OnDestroy` delegates idempotent owner-only teardown |

Patch callback matrix:

```text
Game.Update:
  Prefix(Game __instance)
  Postfix(Game __instance)
  Finalizer(Exception __exception)
Game.DoPlayerInput:
  Prefix(out HookToken __state)
  Postfix(HookToken __state)
  Finalizer(Exception __exception, HookToken __state)
Game.Playerinputstring:
  bool Prefix()
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

The passive `Playerinputstring` Prefix returns `true` and has no by-ref result.
The Update prefix is an observation-safe no-op reserved for Task 6.2.

- [ ] **Step 2: Capture the semantic plugin RED**

Build the Task 3 artifact before creating controller/hooks/shell, then run the
cumulative plugin cohort. Require the first new failure to name absent
`OracleController` or patch contracts; adapter must remain green.

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
"$dotnet_bin" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false -p:GameManagedDir="$game_managed" \
  -p:BepInExCoreDir="$bepinex_core"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
```

- [ ] **Step 3: Complete runtime boundary interfaces**

Append to `OracleRuntimeBoundaries.cs`:

```csharp
internal interface IOracleRuntimeHost
{
    void ValidateAssemblyAndPassiveContract();
    ITraceSink CreateTrace(string outputDirectory, string runName);
    void InstallPatches(OracleController controller);
    void UnpatchSelf(OracleController controller);
    double NowSeconds();
    DateTime UtcNow();
}
```

`ValidateAssemblyAndPassiveContract` hashes the exact live
`typeof(Game).Assembly.Location`, requires
`OracleProtocol.ExpectedAssemblySha256`, then calls
`GameContract.ValidatePassiveSurface`. Its low-level exceptions are translated
by the real host to `PassiveStartupException("invalid_assembly", ...)` or
`("invalid_reflection", ...)` before returning to Core.

- [ ] **Step 4: Implement the Unity-free controller**

Create `OracleController.cs`. It implements `IPassiveStartupServices` and
`IDisposable` with constructor:

```csharp
internal OracleController(
    PassiveConfiguration configuration,
    IOracleGameAdapter adapter,
    IOracleRuntimeHost runtime,
    IPassiveLog log)
```

Construction creates one `PassiveLogReporter` and one `PassiveStartup`; it
does not open a sink or redirect a path. `Start(run)` delegates exactly once
to startup. The service methods are:

```csharp
using System;
using System.IO;

internal sealed class OracleController :
    IPassiveStartupServices, IDisposable
{
    private readonly PassiveConfiguration configuration;
    private readonly IOracleGameAdapter adapter;
    private readonly IOracleRuntimeHost runtime;
    private readonly IPassiveLog log;
    private readonly PassiveLogReporter reporter;
    private readonly PassiveStartup startup;
    private PassiveDriver driver;
    private PassiveUpdateBoundary updateBoundary;

    internal OracleController(
        PassiveConfiguration configuration,
        IOracleGameAdapter adapter,
        IOracleRuntimeHost runtime,
        IPassiveLog log)
    {
        this.configuration = configuration
            ?? throw new ArgumentNullException("configuration");
        this.adapter = adapter ?? throw new ArgumentNullException("adapter");
        this.runtime = runtime ?? throw new ArgumentNullException("runtime");
        this.log = log ?? throw new ArgumentNullException("log");
        reporter = new PassiveLogReporter(log);
        startup = new PassiveStartup(this);
    }

    internal bool Start(RunRecord run) { return startup.Start(run); }
    public void Dispose() { startup.Dispose(); }

}
```

Place the following service, update, and hook method blocks inside this class
before its closing brace; do not create a second partial or wrapper class.

```csharp
public void ValidateBeforeSink()
{
    try
    {
        runtime.ValidateAssemblyAndPassiveContract();
        string output = PhysicalPath.ResolveExistingDirectory(
            configuration.OutputDirectory);
        string save = PhysicalPath.ResolveExistingDirectory(
            configuration.SaveDirectory);
        if (output != configuration.OutputDirectory
            || save != configuration.SaveDirectory
            || PhysicalPath.Contains(output, save)
            || PhysicalPath.Contains(save, output))
            throw new IOException("active path identity changed");
        PhysicalPathIdentity target =
            PhysicalPath.ResolvePossiblyAbsent(configuration.TracePath);
        if (target.Exists)
            throw new PassiveStartupException("trace_exists",
                new IOException("trace target exists"));
        if (target.CanonicalPath != configuration.TracePath
            || target.ExistingAncestor != output
            || target.MissingComponents.Length != 1
            || target.MissingComponents[0]
                != configuration.RunName + ".ndjson")
            throw new IOException("trace target identity changed");
    }
    catch (PassiveStartupException) { throw; }
    catch (OracleConfigurationException error)
    { throw new PassiveStartupException(error.Code, error); }
    catch (Exception error)
    { throw new PassiveStartupException("invalid_path", error); }
}

public void AuthenticateAndRedirectSave()
{
    try { adapter.AuthenticateAndRedirectSavePath(configuration.SaveDirectory); }
    catch (Exception error)
    { throw new PassiveStartupException("save_redirect_failed", error); }
}

public PassiveDriver CreateDriver()
{
    ITraceSink sink;
    try { sink = runtime.CreateTrace(
        configuration.OutputDirectory, configuration.RunName); }
    catch (TraceExistsException error)
    { throw new PassiveStartupException("trace_exists", error); }
    catch (Exception error)
    { throw new PassiveStartupException("trace_io_failed", error); }
    driver = new PassiveDriver(sink, reporter,
        configuration.ExpectedInputCount, configuration.MaxSettleFrames,
        configuration.MaxSettleSeconds);
    updateBoundary = new PassiveUpdateBoundary(driver);
    return driver;
}

public void InstallPatches() { runtime.InstallPatches(this); }
public void UnpatchSelf() { runtime.UnpatchSelf(this); }
public void EmitBootMarker() { log.Info("SSR oracle boot probe loaded"); }
public void MarkerOnlyFailed(string code) { reporter.Failed(code); }
public void Diagnostic(string message) { reporter.Diagnostic(message); }
```

The per-update observation is a private class that calls only the object-typed
adapter:

```csharp
private sealed class AdapterUpdateObservation : IPassiveUpdateObservation
{
    private readonly OracleController owner;
    private readonly object game;
    internal AdapterUpdateObservation(OracleController owner, object game)
    { this.owner = owner; this.game = game; }
    public bool TryGetState(out object state)
    { return owner.adapter.TryGetState(game, out state); }
    public bool VerifySavePath() { return owner.adapter.VerifySavePath(); }
    public bool IsQuiescent(object state)
    { return owner.adapter.IsQuiescent(game, state); }
    public CaptureRecord Capture(object state)
    { return owner.adapter.Capture(state); }
    public double NowSeconds() { return owner.runtime.NowSeconds(); }
    public DateTime UtcNow() { return owner.runtime.UtcNow(); }
}

internal void UpdateEntered(object game) { }
internal void ObserveUpdate(object game)
{
    if (updateBoundary != null)
        updateBoundary.Observe(new AdapterUpdateObservation(this, game));
}
```

Implement the hook forwarding table literally:

| Controller method | Driver call |
|---|---|
| `PlayerPollEntered()` | `driver.PlayerPollEntered()` |
| `PhysicalPollReturned(int raw)` | `driver.PhysicalPollReturned(raw)` |
| `PlayerPollReturned(token)` | `driver.PlayerPollReturned(token)` |
| `ProcessInputEntered(state,raw)` | `driver.ProcessInputEntered(state,raw,runtime.NowSeconds())` |
| `ProcessInputReturned(token,result,state)` | `driver.ProcessInputReturned(token,result,adapter.MovementScheduled(state))` |
| `UndoEntered(game)` | read state once with adapter, then `driver.UndoEntered(state,runtime.NowSeconds())` |
| `RestoreObserved()` | `driver.RestoreObserved()` |
| `UndoReturned(token,game)` | `driver.UndoReturned(token,adapter.CurrentMovementScheduled(game))` |
| `RestartEntered/Returned` | matching driver methods |
| `StateSetEntered(game,requested)` | read current state once, then driver method |
| `StateSetReturned(token,game)` | read current state once, then driver method with `runtime.NowSeconds()` |
| every typed `Threw` | matching driver cleanup |
| `ClearThrew(token)` | `driver.ClearThrew(token)` |
| `GameMethodFailed()` | `driver.TryFault("game_method_exception")` |
| `ObserverFailed()` | `driver.TryFault("observer_exception")` |

Use these bodies; if state lookup returns false, the out value remains null:

```csharp
internal HookToken PlayerPollEntered() { return driver.PlayerPollEntered(); }
internal void PhysicalPollReturned(int raw)
{ driver.PhysicalPollReturned(raw); }
internal void PlayerPollReturned(HookToken token)
{ driver.PlayerPollReturned(token); }
internal void PlayerPollThrew(HookToken token)
{ driver.PlayerPollThrew(token); }

internal HookToken ProcessInputEntered(object state, int raw)
{
    return driver.ProcessInputEntered(state, raw, runtime.NowSeconds());
}
internal void ProcessInputReturned(
    HookToken token, bool accepted, object state)
{
    driver.ProcessInputReturned(
        token, accepted, adapter.MovementScheduled(state));
}
internal void ProcessInputThrew(HookToken token)
{ driver.ProcessInputThrew(token); }

internal HookToken UndoEntered(object game)
{
    object state;
    adapter.TryGetState(game, out state);
    return driver.UndoEntered(state, runtime.NowSeconds());
}
internal void RestoreObserved() { driver.RestoreObserved(); }
internal void UndoReturned(HookToken token, object game)
{
    driver.UndoReturned(token, adapter.CurrentMovementScheduled(game));
}
internal void UndoThrew(HookToken token) { driver.UndoThrew(token); }

internal HookToken RestartEntered() { return driver.RestartEntered(); }
internal void RestartReturned(HookToken token)
{ driver.RestartReturned(token); }
internal void RestartThrew(HookToken token) { driver.RestartThrew(token); }

internal HookToken StateSetEntered(object game, object requested)
{
    object before;
    adapter.TryGetState(game, out before);
    return driver.StateSetEntered(before, requested);
}
internal void StateSetReturned(HookToken token, object game)
{
    object after;
    adapter.TryGetState(game, out after);
    driver.StateSetReturned(token, after, runtime.NowSeconds());
}
internal void StateSetThrew(HookToken token)
{ driver.StateSetThrew(token); }
internal void ClearThrew(HookToken token) { driver.ClearThrew(token); }
internal void GameMethodFailed() { driver.TryFault("game_method_exception"); }
internal void ObserverFailed() { driver.TryFault("observer_exception"); }
```

No hook method catches exceptions—`GameHooks` owns the firewall. `Dispose`
delegates only to `PassiveStartup.Dispose()`.

- [ ] **Step 5: Implement the exact static hook firewall**

Create `GameHooks.cs` with owner
`dev.jlsor.ssr.oracle.passive`. Publishing uses
`Interlocked.CompareExchange`; clearing requires the identical controller and
occurs only after owner-only unpatch.

```csharp
using System;
using System.Threading;

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

    internal static bool AllowNativePlayerInput() { return true; }

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
            original, value.GameMethodFailed, value.ObserverFailed);
    }
}
```

Every ordinary callback uses:

```csharp
GameHooks.Observe(delegate(OracleController value)
{
    value.PlayerPollReturned(__state);
});
```

Every token finalizer uses:

```csharp
return GameHooks.Finalize(__state, __exception);
```

`GameHooks.Finalize` is exactly:

```csharp
internal static Exception Finalize(HookToken token, Exception original)
{
    OracleController value = ReadController();
    if (value == null) return original;
    return PatchBoundary.Finalize(token, original,
        value.ClearThrew, value.GameMethodFailed, value.ObserverFailed);
}
```

Update finalization uses `PatchBoundary.FinalizeUpdate`. Prefixes initialize
`__state = HookToken.Inert(correctKind)` before calling Observe. Postfixes
consume the matching token. Exact hook mapping:

```text
Update prefix -> UpdateEntered(game)
Update postfix -> ObserveUpdate(game)
DoPlayerInput prefix/postfix -> PlayerPollEntered/Returned
Playerinputstring prefix -> return true
Playerinputstring postfix -> PhysicalPollReturned((int)__result)
ProcessInput prefix -> ProcessInputEntered(__instance,(int)__0)
ProcessInput postfix -> ProcessInputReturned(__state,__result,__instance)
DoUndo prefix/postfix -> UndoEntered/UndoReturned
RestorePrevState prefix -> RestoreObserved
DoRestart prefix/postfix -> RestartEntered/Returned
SetGameState prefix -> StateSetEntered(__instance,__0)
SetGameState postfix -> StateSetReturned(__state,__instance)
```

Each of the eight patch classes has a `TargetMethod()` that calls an exact
`PatchTarget.Require` helper; no name-only `AccessTools.Method` is accepted.
Do not patch another overload or use source parameter names where `__0` is
specified.

- [ ] **Step 6: Wire the plugin and deterministic artifact**

Set both version constants to `0.3.0`:

```csharp
internal const string PluginVersion = "0.3.0";
[BepInPlugin("dev.jlsor.ssr.oracle", "SSR Executable Oracle", "0.3.0")]
```

`Plugin.Awake` uses this exact branch order:

```text
load Paths.ConfigPath/dev.jlsor.ssr.oracle.cfg once into OracleConfiguration
if Off:
  PluginModePolicy.StartOff(config, GameContract.ValidateLegacySurface, Boot)
  return
if not Passive: marker invalid_mode and return
construct Harmony(owner), BepInEx log adapter, GameAdapter, runtime host,
  OracleController
hash typeof(Game).Assembly.Location and require reviewed lowercase digest
construct RunRecord(Guid.NewGuid().ToString("N"), digest, DateTime.UtcNow)
controller.Start(run)
```

Catch `OracleConfigurationException` before mode selection and emit only its
code. In passive construction, translate assembly/reflection/path/startup
failures to exactly one closed marker and one diagnostic. Off legacy
validation exceptions retain their original identity and are not translated
to a passive failure.

The real runtime host:

```text
CreateTrace -> NdjsonTraceSink.Create(outputDirectory,runName)
InstallPatches(controller) -> GameHooks.Publish(controller), harmony.PatchAll()
  on failure: harmony.UnpatchSelf(), GameHooks.Clear(controller), rethrow
UnpatchSelf(controller) -> harmony.UnpatchSelf(), then GameHooks.Clear(controller)
NowSeconds -> Stopwatch.ElapsedTicks / (double)Stopwatch.Frequency
UtcNow -> DateTime.UtcNow
```

`OnDestroy` calls controller.Dispose once when nonnull. It never directly
closes a sink or fabricates terminal output.

In `SsrOracle.Plugin.csproj`, add
`<GenerateTargetFrameworkAttribute>false</GenerateTargetFrameworkAttribute>`;
retain net35/C#7.3/AnyCPU/determinism; retain every external reference with
`Private=false`; keep Release `DebugType=none` and `DebugSymbols=false`.

- [ ] **Step 7: Update the passive version oracles**

Change only the literal plugin version from `0.2.0` to `0.3.0` in C# golden
bytes, the two tracked NDJSON fixtures, the Python strict decoder, and the
corresponding Python expectations. Do not change mode, input hash, count,
record ordering, or any other fixture byte.

Run the focused Python protocol file and require all prior strict mutations to
remain rejected:

```bash
python -m pytest tests/test_oracle_protocol.py -q
```

- [ ] **Step 8: Run the Task 4 GREEN matrix**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false -p:GameManagedDir="$game_managed" \
  -p:BepInExCoreDir="$bepinex_core"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- --cohort plugin \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- --cohort assembly \
  --assembly "$game_managed/Assembly-CSharp.dll"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
python -m pytest tests/test_oracle_protocol.py -q
```

Require plugin 6, assembly 4, zero warnings/errors, and no game launch.

---

### Task 5: Full verification, lean mutations, review, and immutable commit

**Files:**
- Review: the exact 28-path Task 6.1 implementation scope below
- Evidence: ignored Task 6.1 evidence root
- Commit: one implementation commit only

**Interfaces:**
- Consumes: all focused GREEN checkpoints.
- Produces: reviewed commit `feat: connect passive oracle runtime`, immutable
  package, final matrix, and clean branch ready for the separate Task 6.2 plan.

- [ ] **Step 1: Authenticate the exact precommit scope**

Require this exact sorted path set and no staged file:

```text
oracle/plugin/Core/GameObservation.cs
oracle/plugin/Core/OracleConfiguration.cs
oracle/plugin/Core/OracleController.cs
oracle/plugin/Core/OracleProtocol.cs
oracle/plugin/Core/OracleRuntimeBoundaries.cs
oracle/plugin/Core/PassiveReporter.cs
oracle/plugin/Core/PassiveStartup.cs
oracle/plugin/Core/PatchBoundary.cs
oracle/plugin/Core/PhysicalPath.cs
oracle/plugin/Core/PluginModePolicy.cs
oracle/plugin/GameAdapter.cs
oracle/plugin/GameContract.cs
oracle/plugin/GameHooks.cs
oracle/plugin/Plugin.cs
oracle/plugin/SsrOracle.Plugin.csproj
oracle/plugin/tests/AssemblySurfaceTests.cs
oracle/plugin/tests/ConfigurationTests.cs
oracle/plugin/tests/EncodingTests.cs
oracle/plugin/tests/GameObservationTests.cs
oracle/plugin/tests/PassiveReporterTests.cs
oracle/plugin/tests/PassiveStartupTests.cs
oracle/plugin/tests/PatchBoundaryTests.cs
oracle/plugin/tests/PhysicalPathTests.cs
oracle/plugin/tests/Program.cs
src/ssr_env/oracle_protocol.py
tests/fixtures/oracle_trace/passive-error.ndjson
tests/fixtures/oracle_trace/passive-success.ndjson
tests/test_oracle_protocol.py
```

```bash
set -e
test -z "$(git diff --cached --name-only)"
git diff --check
git diff --name-only | LC_ALL=C sort > /tmp/task6_1_actual_paths.txt
wc -l /tmp/task6_1_actual_paths.txt
```

Require exactly 28. Any additional path is a scope blocker; do not silently
fold it into the commit.

- [ ] **Step 2: Run the exact full precommit matrix**

```bash
set -e
dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
game_managed="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
bepinex_core="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
plugin_dll="$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
"$dotnet_bin" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false -p:GameManagedDir="$game_managed" \
  -p:BepInExCoreDir="$bepinex_core"
"$dotnet_bin" build oracle/plugin/tests/SsrOracle.Core.Net35.csproj \
  -c Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 \
  -p:UseSharedCompilation=false
for cohort_name in \
  protocol encoding sink driver-boundary driver-initial driver-input \
  driver-terminal config path observation boundary startup reporter \
  assembly plugin; do
  case "$cohort_name" in
    assembly)
      "$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
        -c Release --no-restore --no-build -- --cohort assembly \
        --assembly "$game_managed/Assembly-CSharp.dll" ;;
    plugin)
      "$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
        -c Release --no-restore --no-build -- --cohort plugin \
        --plugin "$plugin_dll" ;;
    *)
      "$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
        -c Release --no-restore --no-build -- --cohort "$cohort_name" ;;
  esac
done
"$dotnet_bin" run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore --no-build -- \
  --assembly "$game_managed/Assembly-CSharp.dll" --plugin "$plugin_dll"
python -m pytest -q
```

Require zero build warnings/errors, every named cohort, exactly 82 C# tests,
one ready line and empty stderr per successful harness command, and the full
Python suite green. Record exact counts; never predict updated Python totals.

- [ ] **Step 3: Run five one-change mutation transactions**

For each mutation, create a fresh disposable clone with `git clone
--no-hardlinks`, overlay the exact 28 candidate files from the primary
worktree, copy the primary ignored `obj` directories without hardlinks, verify
one changed semantic fragment, run the named focused cohort, record the first
failure, and remove the clone only after its evidence is durable. Run a fresh
primary focused GREEN immediately before each clone.

| Mutation | Exact one-change edit | Required kill |
|---|---|---|
| M1 | accept exact `Mode = replay` as Off instead of `invalid_mode` | `config/unsupported modes are typed` |
| M2 | return the first physical scan without comparing the second | `path/two scan drift is rejected` |
| M3 | omit `NoWorldSausageSpawns` from the quiescence conjunction | `observation/all thirteen gates are required` |
| M4 | in `PatchBoundary.Finalize`, clear before `gameMethodFailed` | `boundary/game exception claims before cleanup` |
| M5 | call `EmitBootMarker` before `driver.Activate()` | `startup/run flush precedes patches and activation precedes boot` |

Use `apply_patch` for each clone edit. The mutant must compile; a compile
failure is not a kill. After each focused RED, restore nothing in the primary
worktree and prove its HEAD, index, diff digest, and porcelain are unchanged.

- [ ] **Step 4: Run deterministic repetition**

Run the complete `boundary`, `startup`, and `plugin` sequence ten times. For
each iteration capture status/stdout/stderr independently and require status
zero, byte-exact one-line stdout from each harness invocation, empty stderr,
and unchanged pre/post HEAD, index tree, tracked diff digest, untracked digest,
and porcelain. Do not use sleeps.

- [ ] **Step 5: Request fresh precommit specification and quality reviews**

Create one review package with:

```bash
git diff -U10 > \
  .superpowers/sdd/2026-08-15-task-6-1-runtime-bridge/precommit.patch
sha256sum \
  .superpowers/sdd/2026-08-15-task-6-1-runtime-bridge/precommit.patch
```

The specification review checks every design section through 7 plus Task 6.1
parts of sections 10-12, exact config/path safety, ABI, save isolation,
exception identity, passive-only hooks, marker ownership, and absence of game
launch. The quality review checks Core/game dependency direction, C#7.3,
resource/exception ownership, IL metadata tests, tests/mutations, and unrelated
changes. Both must report `APPROVE C0/I0/M0`; otherwise make the narrow fix,
rerun the affected RED/GREEN, full matrix, mutations, repetition, and both
reviews.

- [ ] **Step 6: Commit the exact reviewed implementation**

```bash
set -e
git diff --check
git add \
  oracle/plugin/Core/GameObservation.cs \
  oracle/plugin/Core/OracleConfiguration.cs \
  oracle/plugin/Core/OracleController.cs \
  oracle/plugin/Core/OracleProtocol.cs \
  oracle/plugin/Core/OracleRuntimeBoundaries.cs \
  oracle/plugin/Core/PassiveReporter.cs \
  oracle/plugin/Core/PassiveStartup.cs \
  oracle/plugin/Core/PatchBoundary.cs \
  oracle/plugin/Core/PhysicalPath.cs \
  oracle/plugin/Core/PluginModePolicy.cs \
  oracle/plugin/GameAdapter.cs oracle/plugin/GameContract.cs \
  oracle/plugin/GameHooks.cs oracle/plugin/Plugin.cs \
  oracle/plugin/SsrOracle.Plugin.csproj \
  oracle/plugin/tests/AssemblySurfaceTests.cs \
  oracle/plugin/tests/ConfigurationTests.cs \
  oracle/plugin/tests/EncodingTests.cs \
  oracle/plugin/tests/GameObservationTests.cs \
  oracle/plugin/tests/PassiveReporterTests.cs \
  oracle/plugin/tests/PassiveStartupTests.cs \
  oracle/plugin/tests/PatchBoundaryTests.cs \
  oracle/plugin/tests/PhysicalPathTests.cs oracle/plugin/tests/Program.cs \
  src/ssr_env/oracle_protocol.py \
  tests/fixtures/oracle_trace/passive-error.ndjson \
  tests/fixtures/oracle_trace/passive-success.ndjson \
  tests/test_oracle_protocol.py
test "$(git diff --cached --name-only | wc -l | tr -d ' ')" = 28
git diff --cached --check
git commit -m "feat: connect passive oracle runtime"
```

- [ ] **Step 7: Authenticate the immutable commit**

```bash
set -e
implementation_commit=$(git rev-parse HEAD)
plan_commit=$(git rev-parse HEAD^)
test "$(git show -s --format=%s HEAD)" = \
  "feat: connect passive oracle runtime"
test "$(git show -s --format=%s "$plan_commit")" = \
  "docs: plan Task 6.1 passive runtime bridge"
test "$(git rev-parse "$plan_commit"^)" = \
  ddd15071960852f176d76d3ac3b3995508f378ba
test "$(git diff-tree --no-commit-id --name-only -r "$plan_commit")" = \
  docs/superpowers/plans/2026-08-15-task-6-1-runtime-bridge.md
test "$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l | tr -d ' ')" = 28
git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain)"
git format-patch --stdout --full-index --binary HEAD^..HEAD > \
  .superpowers/sdd/2026-08-15-task-6-1-runtime-bridge/immutable.patch
sha256sum \
  .superpowers/sdd/2026-08-15-task-6-1-runtime-bridge/immutable.patch
```

- [ ] **Step 8: Re-run immutable verification and reviews**

Repeat the full Task 5 Step 2 matrix, ten-run repetition, and both reviews
against the immutable commit. Reauthenticate every committed blob against the
live file, prove the patch body equals a fresh `git diff -U10 HEAD^ HEAD`, and
prove only ignored evidence exists outside Git. Any correction is a new narrow
append-only implementation commit followed by full requalification; never
amend the reviewed implementation commit.

- [ ] **Step 9: Handoff to the dependent replay plan**

Record the accepted immutable Task 6.1 tip, exact 28-path package hash, final
82-test manifest, Python counts, mutation results, review verdicts, and local
reference identities. Then write the separate Task 6.2 plan from the real
accepted controller/protocol APIs. Do not enable `Mode = replay` or launch the
game during this handoff.
