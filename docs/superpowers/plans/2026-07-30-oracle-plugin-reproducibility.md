# SSR Oracle Plugin Reproducibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the deployable Release plugin byte-identical across unrelated
Git commits and checkout paths while preserving the exact hash-gated oracle
workflow.

**Architecture:** Keep debug provenance available only outside the deployable
Release build. The Release project disables SDK-injected revision metadata and
debug/PDB output, while Git commits and the runbook retain external source
provenance. Verification compares real DLL bytes under distinct revision
inputs and then under distinct checkout paths.

**Tech Stack:** .NET SDK 10.0.300, MSBuild, C# 7.3, `net35`, SHA-256, Git
worktrees, Markdown runbook.

## Global Constraints

- Do not launch the game or mutate any installed-game path.
- Keep the plugin target at `net35`, `PlatformTarget=AnyCPU`, and C# 7.3.
- Keep `Deterministic=true` and all existing `ExternallyResolved` reference
  boundaries.
- Release output contains only `SsrOracle.Plugin.dll`; it contains no Git
  revision, Source Link payload, PDB identity, or checkout-local PDB path.
- Debug configuration behavior is unchanged.
- The accepted Release DLL SHA-256 is
  `73003a18348970edf3157fdc3865feb275eb254c8f6fd12ddcfa88b64135754b`.
- Preserve unrelated `.DS_Store` and `data/decompiled` working-tree state.
- Do not stage generated `bin/` or `obj/` output.

---

### Task 1: Make the Release plugin content-stable

**Files:**

- Modify: `oracle/plugin/SsrOracle.Plugin.csproj`
- Modify: `oracle/README.md`
- Modify: `docs/superpowers/plans/2026-07-27-executable-oracle.md`
- Include: `oracle/plugin/Plugin.cs`
- Include: `oracle/plugin/tests/Program.cs`
- Include: `oracle/plugin/tests/SsrOracle.UnitTests.csproj`

**Interfaces:**

- Consumes: pinned game/BepInEx reference directories and the existing
  dependency-free unit harness.
- Produces: a Release-only MSBuild contract and one hash-pinned
  `SsrOracle.Plugin.dll` with no accompanying PDB.

- [ ] **Step 1: Record the failing revision-invariance reproduction**

Build the unchanged project twice, changing only `SourceRevisionId`:

```bash
DOTNET=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
GAME_MANAGED="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed"
BEPINEX_CORE="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

"$DOTNET" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore \
  -p:GameManagedDir="$GAME_MANAGED" \
  -p:BepInExCoreDir="$BEPINEX_CORE" \
  -p:SourceRevisionId=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
shasum -a 256 oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll

"$DOTNET" build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore \
  -p:GameManagedDir="$GAME_MANAGED" \
  -p:BepInExCoreDir="$BEPINEX_CORE" \
  -p:SourceRevisionId=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
shasum -a 256 oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll
```

Expected before the fix: the two DLL hashes differ because the generated
informational version changes. A normal build at `945198b` produced
`ae6da6acfcfc15f1d2e4e668514fc0d426507fa0d8f57ce99279c19b9d0065fe`,
while the installed reviewed build from `cd82644` is
`6d06583d75bfdc5a677668c3c7b0bd88f9eec49be0d169cf6f357ccac4cc7de4`.

- [ ] **Step 2: Add the minimal Release-only build contract**

Add this property group immediately after the existing general
`PropertyGroup`:

```xml
  <PropertyGroup Condition="'$(Configuration)' == 'Release'">
    <IncludeSourceRevisionInInformationalVersion>false</IncludeSourceRevisionInInformationalVersion>
    <DebugType>none</DebugType>
    <DebugSymbols>false</DebugSymbols>
  </PropertyGroup>
```

Do not set or pin `SourceRevisionId`. Do not change the assembly or plugin
version in this correction.

- [ ] **Step 3: Verify revision-invariant Release bytes**

Repeat Step 1. Both builds must succeed with zero warnings and zero errors,
and both hashes must be exactly:

```text
73003a18348970edf3157fdc3865feb275eb254c8f6fd12ddcfa88b64135754b
```

The output directory must contain only:

```text
oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll
```

- [ ] **Step 4: Update the reviewed runbook contract**

In `oracle/README.md`:

- explain that deployable Release builds omit revision and debug/PDB metadata
  so Git and artifact hashes remain external provenance;
- state that no Release PDB is produced;
- replace the required rebuild hash
  `6d06583d75bfdc5a677668c3c7b0bd88f9eec49be0d169cf6f357ccac4cc7de4`
  with
  `73003a18348970edf3157fdc3865feb275eb254c8f6fd12ddcfa88b64135754b`;
- retain
  `6d06583d75bfdc5a677668c3c7b0bd88f9eec49be0d169cf6f357ccac4cc7de4`
  only as the historical currently installed plugin hash.

In `docs/superpowers/plans/2026-07-27-executable-oracle.md`, add the same
Release-only metadata rule to the project example and global constraints.

- [ ] **Step 5: Verify the harness and tracked scope**

Run:

```bash
"$DOTNET" run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore
git diff --check
git status --short
```

Expected harness output:

```text
SSR oracle unit harness ready
```

Only the files listed under **Files** may be staged for this task. Generated
`bin/` and `obj/`, `.DS_Store`, and `data/decompiled` remain unstaged.

- [ ] **Step 6: Commit**

```bash
git add \
  docs/superpowers/plans/2026-07-27-executable-oracle.md \
  oracle/README.md \
  oracle/plugin/Plugin.cs \
  oracle/plugin/SsrOracle.Plugin.csproj \
  oracle/plugin/tests/Program.cs \
  oracle/plugin/tests/SsrOracle.UnitTests.csproj
git commit -m "feat: add reproducible SSR oracle plugin"
```

- [ ] **Step 7: Prove checkout-path and unrelated-commit invariance**

After a later documentation-only commit exists, create two detached temporary
worktrees, one at this task's commit and one at the documentation-only
descendant. In each worktree, restore from the already available package
cache if needed and perform the exact Release build from Step 1 without a
`SourceRevisionId` override.

Both DLLs must hash exactly to
`73003a18348970edf3157fdc3865feb275eb254c8f6fd12ddcfa88b64135754b`.
Preserve the temporary directories until the PR is created; do not delete
them as part of this task.
