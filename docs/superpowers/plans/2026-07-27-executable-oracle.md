# Executable Game-State Oracle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reversible BepInEx oracle that records one settled real-game state per `.dem` input and a Python comparator that locates the simulator's first exact divergence.

**Architecture:** A single-file BepInEx 5 plugin enters directions through the game's native `Game.Update`/`DoPlayerInput` path, observes acceptance and undo through Harmony patches, and captures `GameState.Save(false, false)` only after a strict two-sample quiescence gate. Dependency-free Python modules validate the NDJSON protocol, parse the game's save string, normalize oracle and simulator states, and stop at the first field-level mismatch. A manifest-based installer writes only beside `Sausage.app` and can recover every installed path without modifying the app bundle or game assembly.

**Tech Stack:** Python 3.12, pytest 8, C# 7.3, `.NET 3.5` plugin target, .NET SDK 10 test harness, BepInEx 5.4.23.5, bundled HarmonyX/`0Harmony.dll`, Unity 2018.4.25f1 Mono.

## Global Constraints

- Target macOS 15.7.3 on Apple Silicon while the game process itself runs as `x86_64` through Rosetta.
- Target `net35`: the game has no `netstandard.dll`, its `mscorlib.dll` uses CLR `v2.0.50727`, and its embedded Mono is 2.6.5.
- Deployable Release plugin builds must omit revision and debug/PDB metadata: set `IncludeSourceRevisionInInformationalVersion` to `false`, `DebugType` to `none`, and `DebugSymbols` to `false`; Git and artifact hashes remain external provenance and no Release PDB is produced.
- Pin BepInEx to stable `5.4.23.5`; use the release archive's own `BepInEx.dll`, `0Harmony.dll`, and Doorstop rather than separate NuGet runtime packages.
- Treat `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564` as the expected SHA-256 of the installed `Assembly-CSharp.dll`.
- Never modify `Sausage.app`, `Assembly-CSharp.dll`, or the user's normal save directories.
- Install BepInEx in the Steam game root beside `Sausage.app`, as required by the official macOS layout.
- Full generated oracle traces stay under ignored `data/oracle/`; only minimal regression fixtures with provenance may be committed.
- Use no JSON runtime dependency in the plugin; encode NDJSON with a tested C# `StringBuilder` encoder compatible with Mono 2.6.5.
- Avoid framework APIs introduced after .NET 3.5 even when the .NET 10 compiler can resolve them in test builds; the deployable target is the game's legacy runtime.
- Call `GameState.Save(false, false)` only on Unity's main thread and never call `GameState.Lost()` for observation because it can mutate `lostreason`.
- Directional inputs must traverse the native `Game.Update` → `DoPlayerInput` → `ProcessInput` path; do not call `ProcessInput` directly.
- Every attempted direction and undo must produce exactly one step or terminal error record; never skip, retry silently, or continue after an alignment fault.
- Implement behavior test-first and make one focused commit per task.

---

## File map

### Python

- `src/ssr_env/oracle_install.py`: safe archive inspection, installation manifest, deployment, status, and recoverable uninstall.
- `src/ssr_env/oracle_protocol.py`: strict NDJSON run/initial/step/error record types and validation.
- `src/ssr_env/oracle_state.py`: parser for `GameState.Save(false, false)` and normalized oracle state.
- `src/ssr_env/oracle_compare.py`: simulator normalization, field/entity diffing, and replay alignment.
- `src/ssr_env/state.py`: serialized global fields needed for oracle parity.
- `src/ssr_env/level.py`: preserves extracted serialized global fields.
- `tools/extract_levels.py`: delegates save-string parsing to the shared strict parser.
- `tools/oracle_install.py`: command-line wrapper around installer operations.
- `tools/oracle_compare.py`: command-line comparator and human/JSON first-divergence output.
- `tests/test_oracle_install.py`: installer boundary and path-safety tests.
- `tests/test_oracle_protocol.py`: trace schema and sequence tests.
- `tests/test_oracle_state.py`: raw save parsing and normalization tests.
- `tests/test_oracle_compare.py`: alignment and precise mismatch tests.

### C#

- `oracle/plugin/SsrOracle.Plugin.csproj`: deterministic `net35` BepInEx plugin build.
- `oracle/plugin/Plugin.cs`: BepInEx entry point and configuration.
- `oracle/plugin/Core/ReplayToken.cs`: dependency-free `.dem` token parser.
- `oracle/plugin/Core/TraceRecords.cs`: immutable trace DTOs.
- `oracle/plugin/Core/JsonLineEncoder.cs`: Mono-compatible deterministic JSON encoder.
- `oracle/plugin/Core/OracleDriver.cs`: Unity-free input/capture state machine.
- `oracle/plugin/GameCapture.cs`: reads game gates and captures raw/envelope state.
- `oracle/plugin/GameHooks.cs`: Harmony patches and event forwarding.
- `oracle/plugin/OracleController.cs`: Unity adapter connecting hooks, driver, and trace sink.
- `oracle/plugin/NdjsonTraceSink.cs`: append-only, auto-flushed trace file.
- `oracle/plugin/tests/SsrOracle.UnitTests.csproj`: .NET 10 console harness linking production core sources.
- `oracle/plugin/tests/Program.cs`: explicit assertions for parser, encoder, and driver.
- `oracle/README.md`: exact build, configuration, run, validation, and recovery instructions.

---

### Task 1: Manifest-safe BepInEx installer

**Files:**
- Create: `src/ssr_env/oracle_install.py`
- Create: `tools/oracle_install.py`
- Create: `tests/test_oracle_install.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: an explicit game-root `Path`, a local BepInEx ZIP `Path`, and a compiled plugin `Path`.
- Produces:
  - `inspect_game(game_root: Path) -> GameInstall`
  - `inspect_archive(archive: Path) -> tuple[ArchiveMember, ...]`
  - `install_runtime(game_root: Path, archive: Path) -> InstallManifest`
  - `deploy_plugin(game_root: Path, plugin: Path, config_text: str) -> InstallManifest`
  - `recover_install(game_root: Path) -> Path`
  - CLI subcommands `inspect`, `install`, `deploy`, `status`, and `recover`.

- [ ] **Step 1: Write failing path-safety and manifest tests**

```python
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

from ssr_env.oracle_install import (
    EXPECTED_ASSEMBLY_SHA256,
    InstallError,
    inspect_archive,
    install_runtime,
    recover_install,
)


def make_fake_game(root: Path, assembly: bytes) -> Path:
    managed = (
        root
        / "Sausage.app/Contents/Resources/Data/Managed"
    )
    managed.mkdir(parents=True)
    (managed / "Assembly-CSharp.dll").write_bytes(assembly)
    (root / "Sausage.app/Contents/MacOS").mkdir(parents=True)
    (root / "Sausage.app/Contents/MacOS/Sausage").write_bytes(b"mach-o")
    return root


def test_archive_rejects_parent_traversal(tmp_path: Path):
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("../outside", b"no")
    with pytest.raises(InstallError, match="unsafe archive member"):
        inspect_archive(archive)


def test_install_refuses_wrong_game_assembly(tmp_path: Path):
    game = make_fake_game(tmp_path / "game", b"wrong")
    archive = tmp_path / "runtime.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("run_bepinex.sh", 'executable_name=""\n')
        zf.writestr("BepInEx/core/BepInEx.dll", b"core")
        zf.writestr("BepInEx/core/0Harmony.dll", b"harmony")
    with pytest.raises(InstallError, match=EXPECTED_ASSEMBLY_SHA256):
        install_runtime(game, archive)


def test_recover_moves_only_manifest_owned_paths(tmp_path: Path, monkeypatch):
    assembly = b"known"
    monkeypatch.setattr(
        "ssr_env.oracle_install.EXPECTED_ASSEMBLY_SHA256",
        sha256(assembly).hexdigest(),
    )
    game = make_fake_game(tmp_path / "game", assembly)
    archive = tmp_path / "runtime.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("run_bepinex.sh", 'executable_name=""\n')
        zf.writestr("BepInEx/core/BepInEx.dll", b"core")
        zf.writestr("BepInEx/core/0Harmony.dll", b"harmony")
    install_runtime(game, archive)
    unrelated = game / "keep-me.txt"
    unrelated.write_text("user")

    recovery = recover_install(game)

    assert unrelated.read_text() == "user"
    assert (recovery / "run_bepinex.sh").is_file()
    assert not (game / "BepInEx").exists()
```

Also add named tests for:

```text
test_archive_rejects_absolute_paths
test_archive_requires_bepinex_and_harmony
test_install_refuses_existing_unmanaged_bepinex
test_install_rewrites_only_the_executable_name_assignment
test_install_manifest_records_archive_hash_and_created_roots
test_deploy_refuses_a_non_dll_plugin
test_recover_refuses_manifest_paths_outside_game_root
test_status_detects_changed_manifest_owned_files
```

- [ ] **Step 2: Run the installer tests and confirm import failure**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_install.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'ssr_env.oracle_install'`.

- [ ] **Step 3: Implement explicit game inspection and safe archive extraction**

```python
EXPECTED_ASSEMBLY_SHA256 = (
    "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564"
)
EXPECTED_RUNTIME_ARCHIVE_SHA256 = (
    "01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323"
)
MANIFEST_NAME = ".ssr-oracle-install.json"
ALLOWED_TOP_LEVEL = {
    ".doorstop_version",
    "BepInEx",
    "changelog.txt",
    "libdoorstop.dylib",
    "run_bepinex.sh",
}


@dataclass(frozen=True, slots=True)
class GameInstall:
    root: Path
    app: Path
    managed: Path
    assembly: Path
    assembly_sha256: str


@dataclass(frozen=True, slots=True)
class ArchiveMember:
    name: str
    is_dir: bool
    size: int


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    relative_path: str
    kind: Literal["file", "directory"]
    sha256: str | None


@dataclass(frozen=True, slots=True)
class InstallManifest:
    schema_version: int
    game_assembly_sha256: str
    runtime_archive_sha256: str | None
    entries: tuple[ManifestEntry, ...]


def _inside(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise InstallError(f"path escapes game root: {candidate}")
    return resolved
```

Implementation rules:

```text
inspect_game:
  resolve the explicit root
  require Sausage.app/Contents/MacOS/Sausage
  require Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll
  compute SHA-256 and require EXPECTED_ASSEMBLY_SHA256

inspect_archive:
  normalize every POSIX member path
  reject absolute paths, "..", symlinks, and unknown top-level names
  allow exactly .doorstop_version, changelog.txt, libdoorstop.dylib,
    run_bepinex.sh, and BepInEx/ as top-level roots
  require .doorstop_version, run_bepinex.sh, libdoorstop.dylib,
    BepInEx/core/BepInEx.dll, and BepInEx/core/0Harmony.dll

install_runtime:
  refuse an existing unmanaged BepInEx directory or manifest
  compute the exact archive SHA-256 and require
    01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323
  extract each member through _inside
  change only executable_name="" to executable_name="Sausage.app"
  chmod run_bepinex.sh to 0o755
  atomically write a manifest that records created top-level roots and file hashes

recover_install:
  validate every manifest entry through _inside
  verify no unrelated top-level target is selected
  move owned roots to .ssr-oracle-recovery/YYYYMMDDTHHMMSSZ instead of deleting
  move the manifest into the recovery directory last
```

- [ ] **Step 4: Add the CLI wrapper and ignore generated data**

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "install", "deploy", "status", "recover"):
        command = sub.add_parser(name)
        command.add_argument("--game-root", type=Path, required=True)
        if name == "install":
            command.add_argument("--archive", type=Path, required=True)
        if name == "deploy":
            command.add_argument("--plugin", type=Path, required=True)
            command.add_argument("--config", type=Path, required=True)
    return parser
```

Add to `.gitignore`:

```gitignore
data/oracle/
oracle/plugin/bin/
oracle/plugin/obj/
oracle/plugin/tests/bin/
oracle/plugin/tests/obj/
```

- [ ] **Step 5: Run installer tests and the complete Python suite**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_install.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

Expected: installer tests pass; the existing suite remains green with the existing expected `xfail` cases.

- [ ] **Step 6: Commit**

```bash
git add .gitignore src/ssr_env/oracle_install.py tools/oracle_install.py tests/test_oracle_install.py
git commit -m "feat: add safe SSR oracle installer"
```

---

### Task 2: `net35` plugin build and boot-compatibility spike

**Files:**
- Create: `oracle/plugin/SsrOracle.Plugin.csproj`
- Create: `oracle/plugin/Plugin.cs`
- Create: `oracle/plugin/tests/SsrOracle.UnitTests.csproj`
- Create: `oracle/plugin/tests/Program.cs`
- Create: `oracle/README.md`

**Interfaces:**
- Consumes: `GameManagedDir` and `BepInExCoreDir` MSBuild properties.
- Produces: `oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll`.

- [ ] **Step 1: Create a minimal plugin project with hard build guards**

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
  </PropertyGroup>

  <PropertyGroup Condition="'$(Configuration)' == 'Release'">
    <IncludeSourceRevisionInInformationalVersion>false</IncludeSourceRevisionInInformationalVersion>
    <DebugType>none</DebugType>
    <DebugSymbols>false</DebugSymbols>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.NETFramework.ReferenceAssemblies.net35"
                      Version="1.0.3" PrivateAssets="all" />
    <Reference Include="BepInEx">
      <HintPath>$(BepInExCoreDir)/BepInEx.dll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="0Harmony">
      <HintPath>$(BepInExCoreDir)/0Harmony.dll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="Assembly-CSharp">
      <HintPath>$(GameManagedDir)/Assembly-CSharp.dll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="UnityEngine">
      <HintPath>$(GameManagedDir)/UnityEngine.dll</HintPath>
      <Private>false</Private>
    </Reference>
    <Reference Include="UnityEngine.CoreModule">
      <HintPath>$(GameManagedDir)/UnityEngine.CoreModule.dll</HintPath>
      <Private>false</Private>
    </Reference>
  </ItemGroup>

  <Target Name="ValidateOracleReferences" BeforeTargets="ResolveReferences">
    <Error Condition="'$(GameManagedDir)' == ''" Text="GameManagedDir is required" />
    <Error Condition="'$(BepInExCoreDir)' == ''" Text="BepInExCoreDir is required" />
    <Error Condition="!Exists('$(GameManagedDir)/Assembly-CSharp.dll')"
           Text="Assembly-CSharp.dll not found under GameManagedDir" />
    <Error Condition="!Exists('$(BepInExCoreDir)/BepInEx.dll')"
           Text="BepInEx.dll not found under BepInExCoreDir" />
    <Error Condition="!Exists('$(BepInExCoreDir)/0Harmony.dll')"
           Text="0Harmony.dll not found under BepInExCoreDir" />
  </Target>
</Project>
```

- [ ] **Step 2: Add a minimal load marker and no-op Harmony compatibility probes**

```csharp
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
```

- [ ] **Step 3: Add a dependency-free .NET 10 harness skeleton**

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <LangVersion>7.3</LangVersion>
    <ImplicitUsings>disable</ImplicitUsings>
    <Nullable>disable</Nullable>
  </PropertyGroup>
</Project>
```

```csharp
using System;

internal static class Program
{
    private static int Main()
    {
        Console.WriteLine("SSR oracle unit harness ready");
        return 0;
    }
}
```

- [ ] **Step 4: Download and inspect the pinned runtime archive**

This step requires root-agent approval for network access. Use the official
release asset:

```bash
curl -L \
  https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.5/BepInEx_macos_universal_5.4.23.5.zip \
  -o /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
shasum -a 256 /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
unzip -l /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
```

Expected SHA-256:
`01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323`.
The exact top-level members are `.doorstop_version`, `changelog.txt`,
`libdoorstop.dylib`, `run_bepinex.sh`, and `BepInEx/`.
`.doorstop_version` contains `4.5.0`; there is no `doorstop_config.ini`.
The wrapper script supplies Doorstop configuration through environment
variables. The archive also contains `BepInEx/core/BepInEx.dll` and
`BepInEx/core/0Harmony.dll`. If the official release redirects to a differently
named macOS asset, stop before installation and change only the pinned archive
name/URL after confirming the release tag is still `v5.4.23.5` and re-verifying
the approved archive SHA-256 and exact member layout.

- [ ] **Step 5: Install the runtime with the tested installer**

This step requires root-agent approval because it writes outside the workspace.

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py install \
  --game-root "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll" \
  --archive /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
```

Expected: BepInEx is installed beside `Sausage.app`; the app bundle and assembly
hash remain unchanged.

- [ ] **Step 6: Restore and build the plugin**

This step requires network approval for the uncached `.NET 3.5` reference pack.

```bash
dotnet restore oracle/plugin/SsrOracle.Plugin.csproj \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

dotnet build oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
```

Expected artifact:

```text
oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll
```

- [ ] **Step 7: Deploy and perform the boot smoke**

Create a config containing `Mode=off`, deploy through the installer, and launch
the wrapper with approval:

```ini
[Oracle]
Mode = off
OutputDirectory = /Users/jlsor/Documents/Research/SSR/data/oracle
RunName = boot-probe
SaveDirectory = /Users/jlsor/Documents/Research/SSR/data/oracle/save-root
InputPath =
MaxSettleFrames = 600
MaxSettleSeconds = 30
ExpectedInitialSha256 =
```

Expected `BepInEx/LogOutput.log` evidence:

```text
BepInEx 5.4.23.5
Unity v2018.4.25f1
SSR oracle boot probe loaded
```

After quitting, rerun:

```bash
shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
```

Expected:

```text
886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564
```

Also record that `codesign --verify --deep --strict Sausage.app` has a
pre-existing `Foregroundr.bundle` seal failure so later work does not
misattribute it to BepInEx.

- [ ] **Step 8: Commit**

```bash
git add oracle/plugin/SsrOracle.Plugin.csproj oracle/plugin/Plugin.cs \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj oracle/plugin/tests/Program.cs \
  oracle/README.md
git commit -m "build: prove SSR BepInEx plugin compatibility"
```

---

### Task 3: Trace records, deterministic JSON, and append-only sink

**Files:**
- Create: `oracle/plugin/Core/ReplayToken.cs`
- Create: `oracle/plugin/Core/TraceRecords.cs`
- Create: `oracle/plugin/Core/JsonLineEncoder.cs`
- Create: `oracle/plugin/NdjsonTraceSink.cs`
- Modify: `oracle/plugin/SsrOracle.Plugin.csproj`
- Modify: `oracle/plugin/tests/SsrOracle.UnitTests.csproj`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Produces:
  - `ReplayToken.ParseLines(string text) -> ReplayToken[]`
  - `JsonLineEncoder.EncodeRun(RunRecord) -> string`
  - `JsonLineEncoder.EncodeInitial(InitialRecord) -> string`
  - `JsonLineEncoder.EncodeStep(StepRecord) -> string`
  - `JsonLineEncoder.EncodeError(ErrorRecord) -> string`
  - `NdjsonTraceSink.Write*` methods that flush one complete line.

Link the production core sources into the .NET 10 harness rather than copying
them:

```xml
<ItemGroup>
  <Compile Include="../Core/*.cs"
           Link="Core/%(Filename)%(Extension)" />
</ItemGroup>
```

- [ ] **Step 1: Add failing harness cases**

```csharp
private static void TestReplayTokens()
{
    ReplayToken[] tokens = ReplayToken.ParseLines("North\nUndo\nWest\n");
    Equal(3, tokens.Length, "token count");
    Equal(OracleInput.North, tokens[0].Input, "north");
    Equal(OracleInput.Undo, tokens[1].Input, "undo");
    Throws<FormatException>(
        delegate { ReplayToken.ParseLines("Jump\n"); },
        "line 1");
}

private static void TestJsonEscaping()
{
    string encoded = JsonLineEncoder.Quote("Cove\n\"fork\"\\");
    Equal("\"Cove\\n\\\"fork\\\"\\\\\"", encoded, "JSON escaping");
    using (JsonDocument.Parse("{\"value\":" + encoded + "}")) { }
}

private static void TestStepSchema()
{
    StepRecord record = Fixtures.Step(37, "West", false, "blocked");
    string json = JsonLineEncoder.EncodeStep(record);
    using (JsonDocument parsed = JsonDocument.Parse(json))
    {
        Equal("step", parsed.RootElement.GetProperty("kind").GetString(), "kind");
        Equal(37, parsed.RootElement.GetProperty("input_index").GetInt32(), "index");
        Equal(false, parsed.RootElement.GetProperty("accepted").GetBoolean(), "accepted");
    }
}
```

- [ ] **Step 2: Run the harness and confirm compile failure**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
```

Expected: compile failure because `ReplayToken` and trace types do not exist.

- [ ] **Step 3: Implement the exact protocol DTOs**

```csharp
public enum OracleInput { North, South, West, East, Undo }
public enum OracleInputOverride { Native = -1, North, South, West, East, None = 8 }

public sealed class CaptureRecord
{
    public string RawSave;
    public string StateIdentity;
    public bool Overworld;
    public bool Won;
    public bool Returning;
    public bool HaveEverCookedAll;
    public string LostReason;
    public string PushTargetLevel;
    public string DisplayName;
    public int SausagesCooked;
    public int MovementCount;
    public int PushesToTry;
}

public sealed class StepRecord
{
    public const int SchemaVersion = 1;
    public string RunId;
    public int InputIndex;
    public string Input;
    public bool Accepted;
    public bool MovementScheduled;
    public int SettleFrames;
    public bool StateReplaced;
    public CaptureRecord Capture;
}

public sealed class EndRecord
{
    public const int SchemaVersion = 1;
    public string RunId;
    public int InputCount;
    public string FinishedAtUtc;
}
```

`RunRecord` contains `run_id`, `mode`, `game_assembly_sha256`,
`plugin_version`, `input_sha256`, `expected_input_count`, and UTC start time.
`InitialRecord` contains `input_index = null` and one `CaptureRecord`.
`ErrorRecord` contains the current index, input, code, message, settle counters,
and last capture.

- [ ] **Step 4: Implement strict token parsing and deterministic JSON encoding**

```csharp
public static ReplayToken[] ParseLines(string text)
{
    List<ReplayToken> result = new List<ReplayToken>();
    string[] lines = text.Replace("\r\n", "\n").Split('\n');
    for (int i = 0; i < lines.Length; i++)
    {
        string token = lines[i].Trim();
        if (token.Length == 0) continue;
        OracleInput input;
        if (!TryParse(token, out input))
            throw new FormatException(
                "line " + (i + 1).ToString(CultureInfo.InvariantCulture)
                + ": unknown token " + token);
        result.Add(new ReplayToken(result.Count, input));
    }
    return result.ToArray();
}
```

The encoder must:

```text
emit keys in one fixed order
encode booleans as true/false and null without quotes
format integers with CultureInfo.InvariantCulture
escape quote, backslash, control characters, and U+0000..U+001F
return one JSON object without a trailing newline
```

- [ ] **Step 5: Implement an append-only sink**

```csharp
public sealed class NdjsonTraceSink : IDisposable
{
    private readonly StreamWriter writer;

    public NdjsonTraceSink(string path)
    {
        if (File.Exists(path))
            throw new IOException("trace already exists: " + path);
        writer = new StreamWriter(
            new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read),
            new UTF8Encoding(false));
        writer.AutoFlush = true;
    }

    public void WriteStep(StepRecord record)
    {
        writer.WriteLine(JsonLineEncoder.EncodeStep(record));
    }

    public void Dispose()
    {
        writer.Dispose();
    }
}
```

Add equivalent `WriteRun`, `WriteInitial`, `WriteError`, and `WriteEnd`
methods. A successful replay is incomplete until its `EndRecord` is flushed.
The controller requires `RunName` to be a nonempty filename stem:
`Path.GetFileName(runName) == runName`, with no directory separators, and
constructs the output as `Path.Combine(outputDirectory, runName + ".ndjson")`.

- [ ] **Step 6: Run the harness and plugin build**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
dotnet build oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
```

Expected: harness exits 0 and the `net35` plugin builds.

- [ ] **Step 7: Commit**

```bash
git add oracle/plugin/Core oracle/plugin/NdjsonTraceSink.cs \
  oracle/plugin/SsrOracle.Plugin.csproj oracle/plugin/tests
git commit -m "feat: define SSR oracle trace protocol"
```

---

### Task 4: Unity-free capture driver state machine

**Files:**
- Create: `oracle/plugin/Core/OracleDriver.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Consumes: replay tokens, `GateSample` values, attempt-hook events, neutral-poll events, and monotonic elapsed time.
- Produces:
  - `DriverPhase Phase`
  - `OracleInputOverride OverrideInput`
  - `DriverCommand OnUpdatePrefix()`
  - `DriverCommand OnLateSample(GateSample sample, double nowSeconds)`
  - `void DirectionEntered(OracleInput input)`
  - `void DirectionReturned(bool accepted, bool movementScheduled)`
  - `void UndoEntered()`
  - `void StateRestored()`
  - `void StateReplaced()`
  - terminal `InitialRecord`, `StepRecord`, or `ErrorRecord` commands.

- [ ] **Step 1: Write failing state-machine tests**

```csharp
private static void TestInitialRequiresNeutralAndTwoStableSamples()
{
    OracleDriver driver = Fixtures.ReplayDriver("North\n");
    Equal(DriverPhase.AwaitInitialNeutral, driver.Phase, "initial phase");
    driver.PollConsumed(OracleInputOverride.None);
    driver.OnLateSample(Fixtures.Sample("A", true), 0.1);
    Equal(DriverCommandKind.None, driver.LastCommand.Kind, "one sample");
    driver.OnLateSample(Fixtures.Sample("A", true), 0.2);
    Equal(DriverCommandKind.WriteInitial, driver.LastCommand.Kind, "initial record");
}

private static void TestRefusedDirectionStillWritesOneStep()
{
    OracleDriver driver = Fixtures.ReadyDriver("West\n");
    driver.UpdatePrefix();
    driver.PollConsumed(OracleInputOverride.West);
    driver.DirectionEntered(OracleInput.West);
    driver.DirectionReturned(false, false);
    driver.UpdatePostfix();
    driver.PollConsumed(OracleInputOverride.None);
    driver.OnLateSample(Fixtures.Sample("A", true), 0.1);
    driver.OnLateSample(Fixtures.Sample("A", true), 0.2);
    Equal(DriverCommandKind.WriteStep, driver.LastCommand.Kind, "refusal record");
    Equal(false, driver.LastCommand.Step.Accepted, "refused");
}

private static void TestTimeoutFaultsWithoutAdvancing()
{
    OracleDriver driver = Fixtures.SettlingDriver(
        maxFrames: 3, maxSeconds: 1.0);
    driver.OnLateSample(Fixtures.Sample("moving", false), 0.2);
    driver.OnLateSample(Fixtures.Sample("moving", false), 0.4);
    driver.OnLateSample(Fixtures.Sample("moving", false), 0.6);
    Equal(DriverPhase.Faulted, driver.Phase, "faulted");
    Equal("settle_timeout", driver.LastCommand.Error.Code, "timeout code");
}
```

Also add exact cases:

```text
TestAcceptedDirectionWaitsForConsumedNeutral
TestStableSignatureIncludesStateIdentityAndEnvelope
TestChangedSampleRestartsTwoSampleDebounce
TestConsumedDirectionWithoutProcessInputFaults
TestUndoAcceptedOnlyAfterStateRestored
TestRestartNestedUndoIsIgnored
TestUnexpectedStateReplacementMarksAndFaultsPendingStep
TestPassiveNextAttemptFinalizesPriorStableRefusal
TestDoneDoesNotRequestAnotherOverride
```

- [ ] **Step 2: Run the harness and confirm missing driver types**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
```

Expected: compile failure naming `OracleDriver`.

- [ ] **Step 3: Implement the explicit phases and event guards**

```csharp
public enum DriverPhase
{
    AwaitGame,
    AwaitInitialNeutral,
    AwaitInitialStable,
    Neutralize,
    Ready,
    AssertDirection,
    AwaitAttemptHook,
    Settling,
    AwaitNeutralConsumption,
    AwaitStable,
    Done,
    Faulted
}

public sealed class GateSample
{
    public bool Quiescent;
    public string Signature;
    public CaptureRecord Capture;
}
```

The transition contract is:

```text
replay start -> require one actually consumed None poll
two identical quiescent samples -> write initial
direction -> assert for one Game.Update only
consumed direction + no ProcessInput before Update postfix -> fault
ProcessInput result -> settling
undo -> accepted only if RestorePrevState observed inside its DoUndo context
settling -> require an actually consumed None poll
two identical quiescent samples -> write exactly one step and advance index
timeout -> write error and enter Faulted
all tokens emitted -> Done
Done transition -> write one EndRecord with the emitted input count
```

- [ ] **Step 4: Run the harness**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
```

Expected: all driver cases pass.

- [ ] **Step 5: Commit**

```bash
git add oracle/plugin/Core/OracleDriver.cs oracle/plugin/tests/Program.cs
git commit -m "feat: add deterministic oracle capture driver"
```

---

### Task 5: Game capture adapter and passive Harmony hooks

**Files:**
- Create: `oracle/plugin/GameCapture.cs`
- Create: `oracle/plugin/GameHooks.cs`
- Create: `oracle/plugin/OracleController.cs`
- Modify: `oracle/plugin/Plugin.cs`
- Modify: `oracle/plugin/SsrOracle.Plugin.csproj`

**Interfaces:**
- `GameCapture.Sample(Game game) -> GateSample`
- `GameHooks.Controller: OracleController`
- Passive patches:
  - `GameState.ProcessInput` prefix/postfix
  - `Game.DoUndo` prefix/postfix
  - private `Game.RestorePrevState` prefix
  - `Game.SetGameState` prefix/postfix
  - `Game.DoRestart` prefix/postfix

- [ ] **Step 1: Add startup reflection validation**

```csharp
private static readonly string[] RequiredGameMethods = {
    "Update", "Playerinputstring", "DoPlayerInput", "DoUndo",
    "RestorePrevState", "SetGameState", "DoRestart"
};

private void ValidateHooks()
{
    for (int i = 0; i < RequiredGameMethods.Length; i++)
        if (AccessTools.Method(typeof(Game), RequiredGameMethods[i]) == null)
            throw new MissingMethodException(
                typeof(Game).FullName, RequiredGameMethods[i]);
    if (AccessTools.Method(typeof(GameState), "ProcessInput") == null)
        throw new MissingMethodException(
            typeof(GameState).FullName, "ProcessInput");
}
```

- [ ] **Step 2: Implement the exact quiescence gate**

Cache `AccessTools.FieldRef<Game, bool>` delegates for private `leaving`,
`gameover`, and `exploding`. `Sample` is quiescent only when:

```csharp
GameState gs = game == null ? null : game.gamestate;
bool quiescent =
    gs != null
    && gs.player != null
    && !gs.Moving()
    && gs.pushestotry == 0
    && !game.exitSequence
    && !Game.endingsequence
    && !game.bluespawnanim
    && !leaving(game)
    && !gameover(game)
    && !exploding(game)
    && (game.escmenu == null || !game.escmenu.activeSelf)
    && GameState.shouldredrawcoffins == Coord.Invalid
    && gs.worldsausagespawns.Count == 0;
```

Capture:

```csharp
CaptureRecord capture = new CaptureRecord {
    RawSave = gs.Save(false, false),
    StateIdentity = RuntimeHelpers.GetHashCode(gs).ToString(
        CultureInfo.InvariantCulture),
    Overworld = gs.overworld,
    Won = gs.won,
    Returning = gs.returning,
    HaveEverCookedAll = gs.haveevercookedall,
    LostReason = gs.lostreason ?? "",
    PushTargetLevel = gs.pushtargetlevel ?? "",
    DisplayName = gs.displayname ?? "",
    SausagesCooked = gs.sausagescooked,
    MovementCount = gs.movements.Count,
    PushesToTry = gs.pushestotry
};
```

The stability signature is SHA-256 over state identity, raw save, and every
envelope field above.

- [ ] **Step 3: Implement passive attempt observation**

```csharp
[HarmonyPatch(typeof(GameState), "ProcessInput")]
internal static class ProcessInputPatch
{
    private static void Prefix(Direction dir)
    {
        GameHooks.Controller.DirectionEntered(Map(dir));
    }

    private static void Postfix(
        GameState __instance, bool __result)
    {
        GameHooks.Controller.DirectionReturned(
            __result, __instance.Moving());
    }
}
```

`DoUndo` opens an undo context. `RestorePrevState` marks it accepted. A
`DoRestart` depth counter suppresses its nested undo calls. `SetGameState`
records before/after references; ordinary subworld entry/exit must not set
`state_replaced`.

If a second passive attempt begins while any prior attempt is pending, sample
the current game from the new attempt prefix. If that pre-mutation sample is
quiescent, finalize the prior record from it before opening the new attempt.
Entry into another native attempt is stronger boundary evidence than waiting
for a second late sample and prevents rapid refused inputs from overlapping.

- [ ] **Step 4: Wire BepInEx configuration and lifecycle**

```csharp
mode = Config.Bind("Oracle", "Mode", "off", "off|passive|replay");
outputDirectory = Config.Bind(
    "Oracle", "OutputDirectory", "", "Absolute trace directory");
runName = Config.Bind(
    "Oracle", "RunName", "", "Filename stem; output uses FileMode.CreateNew");
inputPath = Config.Bind(
    "Oracle", "InputPath", "", "Absolute .dem path for replay mode");
saveDirectory = Config.Bind(
    "Oracle", "SaveDirectory", "", "Absolute isolated game-save directory");
maxSettleFrames = Config.Bind("Oracle", "MaxSettleFrames", 600, "");
maxSettleSeconds = Config.Bind("Oracle", "MaxSettleSeconds", 30.0, "");
expectedInitialSha256 = Config.Bind(
    "Oracle", "ExpectedInitialSha256", "", "");
```

`off` installs no Harmony patches. `passive` patches observation only.
`replay` is rejected until Task 6 supplies an input file and override path.
Both active modes require an absolute `SaveDirectory` that differs from
`SaveGame.PersistentDataPath`. During `Awake`, before a `Game` instance is
accepted, set `SaveGame.PersistentDataPath` to that isolated directory and
create it. Refuse startup rather than falling back to the user's normal save
directory.

Before opening a trace, compute SHA-256 for
`Path.Combine(Paths.ManagedPath, "Assembly-CSharp.dll")`, require the global
expected hash, and put the computed value in `RunRecord`. Generate `run_id`
with `Guid.NewGuid().ToString("N")` and take the plugin version from the
`BepInPlugin` constant so logs and records cannot disagree.

- [ ] **Step 5: Build and commit**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
dotnet build oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
git add oracle/plugin
git commit -m "feat: capture passive settled game states"
```

---

### Task 6: Native-path replay injection and undo driving

**Files:**
- Modify: `oracle/plugin/GameHooks.cs`
- Modify: `oracle/plugin/OracleController.cs`
- Modify: `oracle/plugin/Plugin.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**
- Replay patches:
  - private `Game.Update` prefix/postfix
  - private `Game.Playerinputstring` prefix
- `OracleController.UpdatePrefix(Game game)`
- `OracleController.UpdatePostfix(Game game)`
- `OracleController.OverridePlayerInput(ref Direction result) -> bool`

- [ ] **Step 1: Add failing replay-injection state tests**

```csharp
private static void TestDirectionIsAssertedForOneUpdate()
{
    OracleDriver driver = Fixtures.ReadyDriver("East\n");
    DriverCommand prefix = driver.UpdatePrefix();
    Equal(OracleInputOverride.East, prefix.Override, "assert east");
    driver.PollConsumed(OracleInputOverride.East);
    driver.DirectionEntered(OracleInput.East);
    driver.DirectionReturned(true, true);
    DriverCommand postfix = driver.UpdatePostfix();
    Equal(OracleInputOverride.None, postfix.Override, "deassert");
}

private static void TestUndoCallsGameOnlyAtReadyGate()
{
    OracleDriver driver = Fixtures.ReadyDriver("Undo\n");
    DriverCommand command = driver.OnLateSample(
        Fixtures.Sample("A", true), 1.0);
    Equal(DriverCommandKind.CallUndo, command.Kind, "call undo");
    Equal(0, command.InputIndex, "undo index");
}
```

- [ ] **Step 2: Run the harness and verify failure**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
```

Expected: the new state expectations fail.

- [ ] **Step 3: Patch the native polling path**

```csharp
[HarmonyPatch(typeof(Game), "Update")]
internal static class GameUpdatePatch
{
    private static void Prefix(Game __instance)
    {
        GameHooks.Controller.UpdatePrefix(__instance);
    }

    private static void Postfix(Game __instance)
    {
        GameHooks.Controller.UpdatePostfix(__instance);
    }
}

[HarmonyPatch(typeof(Game), "Playerinputstring")]
internal static class PlayerInputStringPatch
{
    private static bool Prefix(ref Direction __result)
    {
        return GameHooks.Controller.OverridePlayerInput(ref __result);
    }
}
```

In passive mode, `OverridePlayerInput` returns `true` and leaves native input
untouched. In replay mode it always returns `false`; it supplies the one armed
cardinal or `Direction.None`. A neutral frame counts only when this prefix is
actually called with `None`, because `DoPlayerInput` returns before polling
while movement or `exitSequence` is active.

- [ ] **Step 4: Drive undo through the public wrapper**

From the ready/quiescent controller state:

```csharp
driver.UndoEntered();
game.DoUndo();
driver.UndoReturned();
```

Acceptance remains false unless the `RestorePrevState` patch fires inside this
context. Never infer undo acceptance from raw-save equality.

- [ ] **Step 5: Enforce initial-state and alignment gates**

Before input index 0:

```text
compute input_sha256 from the exact UTF-8 file bytes before parsing
set expected_input_count to the parsed token count
consume one neutral Playerinputstring poll
capture two identical quiescent samples
emit initial record
if ExpectedInitialSha256 is nonempty, require it to equal the initial signature
```

During replay:

```text
physical directional input is suppressed by the polling override
queued direction consumed without ProcessInput in the same Game.Update -> error
unexpected SetGameState during a pending token -> record state_replaced and fault
settle timeout -> error and stop
end of tokens -> Done without repeating the final token
Done -> append exactly one end record whose input_count equals the header expectation
```

- [ ] **Step 6: Run harness, build, and commit**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
dotnet build oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
git add oracle/plugin
git commit -m "feat: replay SSR inputs through native game path"
```

---

### Task 7: Passive and one-input real-game integration gate

**Files:**
- Modify: `oracle/README.md`
- Create locally, do not commit: `data/oracle/passive-*.ndjson`
- Create locally, do not commit: `data/oracle/one-input.dem`

**Interfaces:**
- Produces the first real trace and the trusted initial-state signature used by replay mode.

- [ ] **Step 1: Deploy the passive plugin**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py deploy \
  --game-root "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll" \
  --plugin oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll \
  --config data/oracle/passive.cfg
```

The passive config sets:

```ini
[Oracle]
Mode = passive
OutputDirectory = /Users/jlsor/Documents/Research/SSR/data/oracle
RunName = passive-validation
SaveDirectory = /Users/jlsor/Documents/Research/SSR/data/oracle/save-root
InputPath =
MaxSettleFrames = 600
MaxSettleSeconds = 30
ExpectedInitialSha256 =
```

- [ ] **Step 2: Launch and perform three bounded manual checks**

With approval, run the BepInEx wrapper. In a fresh or explicitly selected test
slot:

```text
1. perform one accepted direction
2. press a direction that is visibly blocked
3. press Undo once
```

Expected trace:

```text
one run header
one initial record
three step records
accepted=true for the accepted direction
accepted=false for the blocked direction
accepted=true for Undo only when RestorePrevState ran
movement_count=0 and pushestotry=0 in every terminal capture
```

- [ ] **Step 3: Replay one hard-coded direction**

Create `data/oracle/one-input.dem` containing:

```text
West
```

Configure replay mode with the passive initial signature, launch from the same
test initial state, and compare the automated terminal raw save to a passive
manual `West` from that state.

Expected: identical capture signatures and one step record.

- [ ] **Step 4: Document observed runtime details and commit**

Record:

```text
BepInEx archive SHA-256
actual run script invocation
LogOutput path
plugin load marker
initial signature
accepted/refused/undo results
ordinary non-wrapper launch result
unchanged Assembly-CSharp.dll hash
```

Do not commit the initial save, full trace, or user-specific save data.

```bash
git add oracle/README.md
git commit -m "docs: verify passive SSR oracle integration"
```

---

### Task 8: Parse the game's raw save format

**Files:**
- Create: `src/ssr_env/oracle_state.py`
- Create: `tests/test_oracle_state.py`

**Interfaces:**
- Produces:
  - `SerializedEntity`
  - `SerializedGameState`
  - `parse_game_save(raw: str) -> SerializedGameState`

- [ ] **Step 1: Write failing parser tests with a representative save**

```python
RAW = (
    "Ilevelb11|"
    "1,2,0,2,10,3,,-1,0,0,0,8,0,0,0,|"
    "2,2,0,3,208,2,M,-1,1,0,17,8,0,0,0,|"
    "*level47,levelb4b,*temple1d1,*0*Cove*18*196592012"
)


def test_parse_game_save_preserves_all_entity_fields():
    state = parse_game_save(RAW)
    assert state.overworld is False
    assert state.level == "levelb11"
    assert state.entities[1] == SerializedEntity(
        pos=Coord(2, 2, 0),
        type=EntType.SAUSAGE,
        id=208,
        direction=Direction.WEST,
        dat="M",
        stuckto=-1,
        rot_primary=1,
        rot_legacy=0,
        cookdata=17,
        turndir=Direction.NONE,
        tilenum=0,
        tileset=0,
        pivot=0,
    )
    assert state.completed == frozenset({"level47", "levelb4b"})
    assert state.issued_shrines == frozenset({"temple1d1"})
    assert state.display_name == "Cove"
    assert state.sausages_cooked == 18
    assert state.music_seed == 196592012


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("", "empty save"),
        ("Ilevel|1,2,|******", "15 fields"),
        ("Ilevel|0,0,0,99,1,0,,-1,0,0,0,8,0,0,0,|******", "EntType"),
        ("Ilevel|0,0,0,2,1,99,,-1,0,0,0,8,0,0,0,|******", "Direction"),
        ("Ilevel|0,0,0,2,1,0,,-1,2,0,0,8,0,0,0,|******", "rotation"),
    ],
)
def test_parse_game_save_rejects_malformed_data(raw, message):
    with pytest.raises(OracleStateError, match=message):
        parse_game_save(raw)
```

- [ ] **Step 2: Run and verify import failure**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_state.py -q
```

Expected: module import fails.

- [ ] **Step 3: Implement strict parsing**

```python
@dataclass(frozen=True, slots=True)
class SerializedEntity:
    pos: Coord
    type: EntType
    id: int
    direction: Direction
    dat: str
    stuckto: int
    rot_primary: int
    rot_legacy: int
    cookdata: int
    turndir: Direction
    tilenum: int
    tileset: int
    pivot: int

    @property
    def rot(self) -> int:
        return 1 if self.rot_primary == 1 or self.rot_legacy == 1 else 0


@dataclass(frozen=True, slots=True)
class SerializedGameState:
    entities: tuple[SerializedEntity, ...]
    overworld: bool
    level: str
    completed: frozenset[str]
    issued_shrines: frozenset[str]
    tileset: int
    display_name: str
    sausages_cooked: int
    music_seed: int
```

Parsing rules:

```text
split the save into exactly seven "*" sections
read optional leading "I<level>|" as subworld; accept the game's bare "F|"
marker and treat absence of either marker as overworld
split entity records on "|" and ignore only the final empty record
require 15 comma fields plus the trailing empty comma field
map numeric type/direction ordinals through existing IntEnums
require both rotation fields to be 0 or 1 and normalize as their logical OR
reject duplicate entity ids
retain static and dynamic entities
split completed and issued lists on comma, dropping only empty members
```

- [ ] **Step 4: Run tests and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_state.py -q
git add src/ssr_env/oracle_state.py tests/test_oracle_state.py
git commit -m "feat: parse real SSR save states"
```

---

### Task 9: Strict NDJSON protocol reader

**Files:**
- Create: `src/ssr_env/oracle_protocol.py`
- Create: `tests/test_oracle_protocol.py`

**Interfaces:**
- Produces:
  - `RunHeader`, `OracleCapture`, `InitialRecord`, `StepRecord`, `EndRecord`, `ErrorRecord`
  - `OracleRun`
  - `read_oracle_trace(path: Path) -> OracleRun`

- [ ] **Step 1: Write failing protocol tests**

```python
def test_trace_requires_header_then_initial_then_sequential_steps(tmp_path):
    path = write_trace(
        tmp_path,
        header(),
        initial(raw_save=RAW),
        step(0, "West", accepted=False, raw_save=RAW),
        step(1, "Undo", accepted=True, raw_save=RAW),
        end(input_count=2),
    )
    run = read_oracle_trace(path)
    assert run.header.schema_version == 1
    assert run.initial.input_index is None
    assert [record.input_index for record in run.steps] == [0, 1]


@pytest.mark.parametrize(
    ("records", "message"),
    [
        ([initial()], "first record must be run"),
        ([header(), step(0)], "initial"),
        ([header(), initial(), step(1)], "expected input_index 0"),
        ([header(), initial(), step(0), step(0)], "expected input_index 1"),
        ([header(schema_version=2), initial()], "schema_version 2"),
        ([header(), initial(), error(0), step(1)], "records after terminal error"),
        ([header(expected_input_count=1), initial(), step(0)], "missing end"),
        ([header(expected_input_count=1), initial(), step(0), end(0)], "input_count"),
    ],
)
def test_trace_rejects_misalignment(tmp_path, records, message):
    with pytest.raises(OracleProtocolError, match=message):
        read_oracle_trace(write_trace(tmp_path, *records))
```

Also test unknown keys, missing keys, wrong scalar types, malformed JSON,
truncated final lines, mismatched `run_id`, and unexpected assembly hash.

- [ ] **Step 2: Run and verify import failure**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_protocol.py -q
```

- [ ] **Step 3: Implement strict record decoding**

```python
@dataclass(frozen=True, slots=True)
class OracleCapture:
    raw_save: str
    state_identity: str
    overworld: bool
    won: bool
    returning: bool
    have_ever_cooked_all: bool
    lost_reason: str
    push_target_level: str
    display_name: str
    sausages_cooked: int
    movement_count: int
    pushes_to_try: int


@dataclass(frozen=True, slots=True)
class OracleRun:
    header: RunHeader
    initial: InitialRecord
    steps: tuple[StepRecord, ...]
    end: EndRecord | None
    error: ErrorRecord | None
```

Use per-kind exact-key sets and explicit `isinstance` checks; remember that
`bool` is a subclass of `int` in Python and must be rejected where an integer
is required. A successful replay shape is exactly `run`, one `initial`,
sequential steps `0..N-1`, and one `end` whose `input_count` and the header's
`expected_input_count` both equal `N`.

- [ ] **Step 4: Run tests and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_protocol.py -q
git add src/ssr_env/oracle_protocol.py tests/test_oracle_protocol.py
git commit -m "feat: validate SSR oracle traces"
```

---

### Task 10: Shared normalization and precise state diffs

**Files:**
- Create: `src/ssr_env/oracle_compare.py`
- Create: `tests/test_oracle_compare.py`
- Modify: `src/ssr_env/state.py`
- Modify: `src/ssr_env/level.py`
- Modify: `src/ssr_env/mechanics.py`
- Modify: `tools/extract_levels.py`
- Create: `tests/test_extract_levels.py`
- Modify: `tests/test_subworld.py`

**Interfaces:**
- Produces:
  - `NormalizedEntity`
  - `NormalizedState`
  - `StateDifference`
  - `IdentityBridge`
  - `normalize_oracle(capture: OracleCapture) -> NormalizedState`
  - `normalize_simulator(state: GameState) -> NormalizedState`
  - `diff_states(expected: NormalizedState, actual: NormalizedState, bridge: IdentityBridge) -> tuple[StateDifference, ...]`

- [ ] **Step 1: Write failing entity/global diff tests**

```python
def test_entity_diff_names_exact_field_after_identity_bridge():
    expected = normalized_state(
        entities={208: normalized_sausage(208, pos=Coord(2, 2, 0), cookdata=17)}
    )
    actual = normalized_state(
        entities={33: normalized_sausage(33, pos=Coord(3, 2, 0), cookdata=21)}
    )
    bridge = IdentityBridge.from_pairs([(208, 33)])
    assert diff_states(expected, actual, bridge) == (
        StateDifference("entities[208->33].pos", [2, 2, 0], [3, 2, 0]),
        StateDifference("entities[208->33].cookdata", 17, 21),
    )


def test_diff_reports_missing_and_extra_entities_in_id_order():
    expected = normalized_state(entities={2: normalized_player(2)})
    actual = normalized_state(entities={3: normalized_player(3)})
    bridge = IdentityBridge.empty()
    assert [diff.path for diff in diff_states(expected, actual, bridge)] == [
        "entities[2]",
        "entities[3]",
    ]


def test_oracle_normalization_rejects_non_quiescent_capture():
    capture = oracle_capture(RAW, movement_count=1)
    with pytest.raises(OracleComparisonError, match="not settled"):
        normalize_oracle(capture)


def test_level_exit_counts_only_removed_level_sausages():
    solved = entered_with((1, 2, 1, 2))
    original = solved.of_type(EntType.SAUSAGE)[0]
    state = with_entities(
        solved,
        tuple(e for e in solved.entities if e.id != original.id)
        + (
            replace(original, id=20, dat="M"),
            replace(original, id=21, dat=""),
            replace(original, id=22, dat="S;world"),
        ),
        sausages_cooked=7,
    )
    left = check_level_exit(state, META, masks={})
    assert left.sausages_cooked == 9
    assert left.by_id(22).dat == "M;world"


def test_extractor_uses_strict_shared_save_parser():
    payload = level_payload("levelb11", RAW)
    assert payload["sausages_cooked"] == 18
    assert payload["entities"][1]["rot_primary"] == 1
    assert payload["entities"][1]["rot_legacy"] == 0
    assert payload["entities"][1]["rot"] == 1
```

Add tests for direction, `dat`, `stuckto`, `rot`, four cook faces, `turndir`,
`tilenum`, `tileset`, `pivot`, level, overworld, completed, issued shrines,
display name, cooked count, music seed, loss envelope, and entity order
independence. Add exact identity tests:

```text
test_initial_bridge_pairs_islands_by_unique_dat
test_initial_bridge_pairs_unique_player_despite_different_ids
test_bridge_translates_stuckto_through_mapped_ids
test_bridge_persists_after_entities_move
test_bridge_pairs_one_new_sausage_by_full_state
test_bridge_rejects_ambiguous_new_entities
test_bridge_reports_removed_entity
```

- [ ] **Step 2: Run and verify import failure**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_compare.py -q
```

- [ ] **Step 3: Implement normalized types and deterministic diffing**

```python
@dataclass(frozen=True, slots=True)
class NormalizedEntity:
    id: int
    type: EntType
    pos: Coord
    direction: Direction
    dat: str
    stuckto: int
    rot: int
    cookdata: int
    turndir: Direction
    tilenum: int
    tileset: int
    pivot: int


@dataclass(frozen=True, slots=True)
class NormalizedState:
    entities: tuple[NormalizedEntity, ...]
    overworld: bool
    level: str
    completed: frozenset[str]
    issued_shrines: frozenset[str]
    tileset: int
    display_name: str
    sausages_cooked: int
    music_seed: int
    won: bool
    returning: bool
    have_ever_cooked_all: bool
    lost_reason: str


@dataclass(frozen=True, slots=True)
class StateDifference:
    path: str
    oracle: object
    simulator: object
```

`normalize_oracle` parses `raw_save`, cross-checks the duplicated envelope
fields, requires `movement_count == 0` and `pushes_to_try == 0`, and sorts
entities by id.

Add immutable serialized global fields to `GameState`:

```python
display_name: str = ""
sausages_cooked: int = 0
music_seed: int = 0
won: bool = False
returning: bool = False
have_ever_cooked_all: bool = False
```

`load_level` and `load_overworld` preserve these values from extracted JSON.
`check_level_exit` increments `sausages_cooked` by exactly the number of removed
sausages whose `dat` is empty or begins with `"M"`, matching
`DespawnSubworldSausages`; `"S"` sausages are retained and do not increment the
count on that exit.

Refactor `tools/extract_levels.py` to expose
`level_payload(name: str, text: str) -> dict` backed by `parse_game_save`, and
emit:

```text
tileset
display_name
music_seed
sausages_cooked
completed
issued_shrines
all 15 serialized entity fields, including both raw rotation slots
normalized rot = 1 when either raw rotation slot equals 1, preserving the
existing entity_from_raw contract
```

Do not compare raw numeric IDs directly. `IdentityBridge` owns two persistent
maps:

```python
oracle_to_simulator: dict[int, int]
simulator_to_oracle: dict[int, int]
```

At the initial state it pairs islands by unique `dat`, then unique entities by
type and complete non-ID state. At later boundaries it retains existing pairs
and pairs only newly unmatched entities using type, position, direction, data,
attachment after mapped-ID translation, rotation, cookdata, and creation-order
ID when the pairing is unique. It raises `IdentityMappingError` if more than one
pairing remains possible. `stuckto` is translated through the bridge before
field comparison. No normalization or comparison function mutates simulator
state.

- [ ] **Step 4: Run focused and full tests**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compare.py tests/test_extract_levels.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

- [ ] **Step 5: Commit**

```bash
git add src/ssr_env/oracle_compare.py src/ssr_env/state.py src/ssr_env/level.py \
  src/ssr_env/mechanics.py tools/extract_levels.py \
  tests/test_oracle_compare.py tests/test_extract_levels.py tests/test_subworld.py
git commit -m "feat: diff oracle and simulator states"
```

---

### Task 11: Replay-aligned first-divergence CLI

**Files:**
- Modify: `src/ssr_env/oracle_compare.py`
- Create: `tools/oracle_compare.py`
- Modify: `tests/test_oracle_compare.py`

**Interfaces:**
- `compare_trace(run: OracleRun, inputs: list[Input], input_sha256: str, initial: GameState, masks, meta) -> ComparisonReport`
- `locate_input(input_index: int) -> InputLocation`
- CLI:

```text
tools/oracle_compare.py TRACE --dem data/dem/all.dem
  [--json PATH] [--allow-assembly-sha256 SHA]
```

- [ ] **Step 1: Write failing alignment and report tests**

```python
def test_compare_trace_stops_at_first_mismatch():
    inputs = [Direction.WEST, Direction.NORTH]
    digest = sha256(b"West\nNorth\n").hexdigest()
    initial = flat()
    oracle = run_for_states(
        input_sha256=digest,
        initial=initial,
        steps=[
            step_capture(step(initial, Direction.WEST, []).state),
            altered_capture(entity_id=initial.player.id, x=99),
        ],
    )
    report = compare_trace(oracle, inputs, digest, initial, masks={})
    assert report.matched_steps == 1
    assert report.input_index == 1
    assert report.input == Direction.NORTH
    assert report.differences[0].path.startswith("entities[")


def test_compare_trace_rejects_input_hash_mismatch():
    oracle = run_with_input_sha256("0" * 64)
    with pytest.raises(OracleComparisonError, match="input_sha256"):
        compare_trace(
            oracle,
            [Direction.WEST],
            sha256(b"West\n").hexdigest(),
            flat(),
            masks={},
        )


def test_known_cove_failure_location_uses_existing_segment_boundaries():
    location = locate_input(1240)
    assert location.global_move == 1241
    assert location.segment == "2-3"
    assert location.segment_index == 36
    assert location.segment_move == 37
```

Add cases for initial mismatch, input-count mismatch, oracle terminal error,
accepted/refused disagreement, undo history alignment, and first mismatch
global/segment-relative numbering.

- [ ] **Step 2: Run tests and verify failure**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_compare.py -q
```

- [ ] **Step 3: Implement the replay loop**

```python
def compare_trace(
    run: OracleRun,
    inputs: list[Input],
    input_sha256: str,
    initial: GameState,
    masks,
    meta=None,
) -> ComparisonReport:
    validate_input_hash(run.header.input_sha256, input_sha256)
    history: list[GameState] = []
    state = initial
    bridge = IdentityBridge.establish(
        normalize_oracle(run.initial.capture),
        normalize_simulator(state),
    )
    initial_diffs = compare_capture(run.initial.capture, state, bridge)
    if initial_diffs:
        return ComparisonReport.initial(initial_diffs)

    for record, action in zip(run.steps, inputs, strict=False):
        result = step(state, action, history, masks, "", meta)
        bridge.update(
            normalize_oracle(record.capture),
            normalize_simulator(result.state),
        )
        differences = compare_capture(record.capture, result.state, bridge)
        if record.accepted != result.moved:
            differences = (
                StateDifference("accepted", record.accepted, result.moved),
                *differences,
            )
        if differences:
            return ComparisonReport.mismatch(
                record.input_index, action, differences, state, result.state)
        state = result.state
    return ComparisonReport.match(len(run.steps), state)
```

For undo, compare acceptance to whether the history actually restored a prior
state rather than to `StepResult.moved`. Segment names and segment-relative
moves come from the lengths of `data/dem/<segment>.dem` in the existing
`tools/level_audit.py` order.

- [ ] **Step 4: Implement concise text and stable JSON output**

Text begins:

```text
FIRST DIVERGENCE
global move: 1234
input index: 1233
segment: 2-3
segment move: 30
level: levelb11 (Cove)
input: West
```

Then print each difference as:

```text
entities[208].cookdata: oracle=17 simulator=21
```

Include the existing simulator render and a compact oracle entity table. JSON
uses only dictionaries, lists, strings, integers, booleans, and null.
Return process exit code `0` for a complete match, `1` for a validated state
divergence, and `2` for an invalid/incomplete trace, wrong assembly/input hash,
identity ambiguity, or oracle terminal error.

- [ ] **Step 5: Run tests and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_compare.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
git add src/ssr_env/oracle_compare.py tools/oracle_compare.py tests/test_oracle_compare.py
git commit -m "feat: report first real-game divergence"
```

---

### Task 12: Short replay, confirmed prefix, and Cove localization

**Files:**
- Modify: `oracle/README.md`
- Modify only if a minimal regression is extracted: `tests/test_mechanics.py`
- Create only if a minimal regression is extracted: `tests/fixtures/cove-first-divergence.json`
- Create locally, do not commit: `data/oracle/all-*.ndjson`
- Create locally, do not commit: `data/oracle/cove-window-*.ndjson`

**Interfaces:**
- Produces a verified 18-level matching prefix and the first exact Cove mismatch.

- [ ] **Step 1: Run the complete local verification before deployment**

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
dotnet build oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
git diff --check
```

Expected: C# harness and build pass; Python suite remains green with expected
`xfail` cases only; no whitespace errors.

- [ ] **Step 2: Run a short automated replay**

Use the first 35 inputs of `all.dem` in a local file and the trusted initial
signature from Task 7. Set `RunName = short-run`, deploy replay mode, and launch
from the same dedicated test start.

Expected:

```text
35 sequential step records
no duplicate or missing input_index
no error record
all terminal captures quiescent
```

Compare:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_compare.py \
  data/oracle/short-run.ndjson \
  --dem data/oracle/short-input.dem
```

Expected: all 35 steps match.

- [ ] **Step 3: Run through the confirmed 18-level prefix**

Set `RunName = all-run`, deploy replay mode with `data/dem/all.dem`, launch from
the trusted dedicated test start, and compare the resulting trace:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_compare.py \
  data/oracle/all-run.ndjson \
  --dem data/dem/all.dem \
  --json data/oracle/all-run-comparison.json
```

Acceptance gate:

```text
no mismatch before the existing 18-level confirmed frontier
no trace alignment error
no state replacement fault
no unsettled terminal record
```

If an earlier mismatch appears, stop and classify it as one of:

```text
initial-state mismatch
input alignment mismatch
oracle normalization mismatch
simulator mismatch
```

Do not continue to Cove until the classification has evidence.

- [ ] **Step 4: Localize the earliest Cove mismatch**

Continue comparison until the first mismatch in or before `levelb11`. Record:

```text
global move and zero-based input index
segment and segment-relative move
input token
level name and display name
accepted/refused result
all differing global fields
all differing entities and fields
pre-step simulator render
post-step simulator render
oracle entity table
game assembly hash and plugin version
```

Extract only the smallest raw state/transition window necessary to reproduce
the mismatch locally.

- [ ] **Step 5: Add a focused failing mechanics test**

The test name states the discovered rule rather than the symptom. Structure:

```python
def test_cove_first_oracle_divergence_transition():
    fixture_path = (
        Path(__file__).parent / "fixtures" / "cove-first-divergence.json"
    )
    fixture = json.loads(fixture_path.read_text())
    before = GameState(
        entities=tuple(entity_from_raw(raw) for raw in fixture["before"]["entities"]),
        overworld=fixture["before"]["overworld"],
        pushtargetlevel=fixture["before"]["level"],
        completed=frozenset(fixture["before"]["completed"]),
        issued_shrines=frozenset(fixture["before"]["issued_shrines"]),
    )
    action = {
        "North": Direction.NORTH,
        "South": Direction.SOUTH,
        "West": Direction.WEST,
        "East": Direction.EAST,
        "Undo": Action.UNDO,
    }[fixture["input"]]
    result = step(before, action, history=[], masks=fixture["masks"])
    actual = normalize_simulator(result.state)
    envelope = fixture["expected_envelope"]
    expected = normalize_oracle(
        OracleCapture(
            raw_save=fixture["expected_raw_save"],
            state_identity="fixture",
            overworld=envelope["overworld"],
            won=envelope["won"],
            returning=envelope["returning"],
            have_ever_cooked_all=envelope["have_ever_cooked_all"],
            lost_reason=envelope["lost_reason"],
            push_target_level=envelope["push_target_level"],
            display_name=envelope["display_name"],
            sausages_cooked=envelope["sausages_cooked"],
            movement_count=0,
            pushes_to_try=0,
        )
    )
    assert actual == expected
```

Run it and confirm it fails for the exact oracle difference. Do not implement
the mechanics fix in this oracle milestone.

- [ ] **Step 6: Update operator documentation and commit**

Document:

```text
how to prepare the dedicated test start
how to switch off/passive/replay modes
how to identify a completed or faulted run
how to compare a trace
how to recover the BepInEx installation
which three-to-five manual checks established trust
the verified prefix and first Cove mismatch
```

```bash
git add oracle/README.md tests/test_mechanics.py \
  tests/fixtures/cove-first-divergence.json
git commit -m "test: capture first real SSR divergence"
```

If no mechanics test was added because the mismatch was in the comparator or
oracle, commit only the corrected oracle files and documentation with a message
that names that verified root cause.

---

## Final verification

- [ ] Run all C# pure tests:

```bash
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj -c Release
```

- [ ] Build the exact deployable plugin:

```bash
dotnet build oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
```

- [ ] Run the complete Python suite:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

- [ ] Verify source cleanliness:

```bash
git diff --check
git status --short
```

- [ ] Recheck game integrity:

```bash
shasum -a 256 "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
```

Expected:

```text
886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564
```

- [ ] Verify recoverability with installer `status`, without recovering the
active installation unless requested:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py status \
  --game-root "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
```

- [ ] Confirm the final report identifies either:

```text
the first exact simulator mismatch before the Cove loss
```

or, if the oracle itself failed:

```text
the exact oracle gate/protocol failure with no skipped inputs and no simulator claim
```
