# Task 4 Report: Build Twice and Inspect the Legacy Preloader

## Status

**COMPLETE.** After preserving and diagnosing the initial 300-second restore
and publish timeouts, two narrow concurrency controls resolved the legacy
project-graph deadlocks without changing the SDK, inputs, offline mode, locked
mode, or timeout. Two complete CLI invocations (four fresh build roots)
produced the same DLL SHA-256, exact legacy metadata, canonical provenance, and
the same hash-addressed result.

## Files and commits

Task 4 implementation files:

- `oracle/compat/inspector/SsrOracle.CompatInspector.csproj`
- `oracle/compat/inspector/Program.cs`
- `src/ssr_env/oracle_compat.py`
- `tests/test_oracle_compat.py`
- `tools/build_bepinex_compat.py`

Commit:

- `0727b687619fab411f703f1b59016e1436b933aa`
  (`feat: build reproducible BepInEx preloader`)

The pre-existing unrelated changes remain unstaged and unmodified by Task 4:
`.DS_Store`, `docs/superpowers/plans/2026-07-27-executable-oracle.md`,
`data/decompiled`, `oracle/README.md`, and `oracle/plugin/`.

## TDD evidence

Initial RED:

```text
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py -k 'inspector or build' -q

ImportError: cannot import name 'AssemblyMetadata' from
'ssr_env.oracle_compat'
```

The first real restore exposed an unsupported `dotnet restore --framework`
switch. A regression test was added and observed RED:

```text
test_build_restore_uses_locked_mode_without_unsupported_framework_switch
FAILED
assert all("--framework" not in command for command in restores)
```

After removing the unsupported switch, focused GREEN was:

```text
.......                                                                  [100%]
7 passed, 35 deselected in 6.85s
```

Fresh final full-file GREEN after the timeout and CLR2 corrections was:

```text
..............................................                           [100%]
46 passed in 14.45s
```

The focused tests cover:

- non-loading inspection of a real synthetic net35 PE;
- rejection of differing second-build bytes;
- rejection of wrong CLR/framework/reference metadata;
- 300-second timeout conversion with captured-log preservation;
- publication only after all checks;
- exact locked restore command construction; and
- CLI build routing.

## Inspector evidence

The net8.0 inspector uses `PEReader` and `MetadataReader`. It does not use
`Assembly.Load`, `Assembly.LoadFrom`, or another assembly-loading API. It
rejects missing CLI metadata, non-assembly metadata, native entry points,
non-IL-only/mixed-mode images, missing or duplicate target-framework
attributes, duplicate assembly references, and malformed attribute blobs with
exit code 2.

Direct output from the built inspector over the test's real net35 PE:

```json
{
  "assembly_name": "BepInEx.Preloader",
  "assembly_version": "5.4.23.5",
  "metadata_version": "v2.0.50727",
  "references": {
    "mscorlib": "2.0.0.0"
  },
  "target_framework": ".NETFramework,Version=v3.5"
}
```

The test PE is a synthetic fixture because no official preloader DLL is
present in the Task 4 workspace and the game was not touched. The installed
official legacy artifact was independently confirmed by the controller to omit
`TargetFrameworkAttribute`, matching the real patched output. The inspector
therefore infers net35 only when metadata version equals `v2.0.50727`,
`mscorlib` equals `2.0.0.0`, and `System.Core` equals `3.5.0.0`; any missing or
mismatched signal remains exit 2. This is the Task 4 plan/spec correction for
the real CLR2 metadata layout; approved design documents were not changed.

## Real offline build commands and logs

CLI invocation:

```text
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py build \
  --source data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  --sdk data/oracle/compat/dotnet-8.0.419/dotnet \
  --feed-dir data/oracle/compat/fetch-acceptance \
  --output-dir data/oracle/compat/builds
```

The inspector restore and publish completed offline. Their exact commands and
captured output are in:

- `data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/inspector/restore.log`
- `data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/inspector/publish.log`
- `data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/sdk-version.log`

The corrected first-root preloader restore command was:

```text
/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/dotnet-8.0.419/dotnet restore /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/build-a/source/BepInEx.Preloader/BepInEx.Preloader.csproj --locked-mode --no-cache --packages /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/build-a/packages --configfile /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/build-a/NuGet.config
```

Its preserved log is:

`data/oracle/compat/builds/.work/ce136466c0644c85bfbc6de4fe6443e2/build-a/restore.log`

Captured output at timeout:

```text
Determining projects to restore...
CSSM_ModuleLoad(): One or more parameters passed to a function were not valid.
```

The preloader publish command was not executed, so no preloader publish log
exists. The orchestrator would have run the exact project with `Release`,
`net35`, `--no-restore`, `--disable-build-servers`,
`Deterministic=true`, `ContinuousIntegrationBuild=true`, and the fresh-root
`PathMap=<source-root>=/_/src` after successful locked restore.

The earlier unsupported-switch diagnostic remains preserved separately at:

`data/oracle/compat/builds/.work/f7fb54efb6044651991790734b0fd593/build-a/restore.log`

### Systematic timeout investigation and correction

The corrected default restore was reproduced at diagnostic verbosity with a
45-second process-group kill cap. It completed project evaluation in under one
second, then stopped in NuGet `_GenerateRestoreProjectPathWalk` at an `MSBuild`
task with `BuildInParallel=True`. No package directory or assets file had been
created. `MSBUILDUSESERVER=0` ruled out a build-server wait.

One-variable probes, with all offline/locked inputs unchanged:

- global `-m:1`: exit 0, all five projects restored in 214 ms;
- narrower `-p:RestoreBuildInParallel=false`: exit 0, all five projects
  restored in 217 ms.

The narrower property directly controls the observed NuGet target and was
selected. A command-contract test was observed RED before production changed.

The next real run restored build-a in 200 ms but its publish hit the independent
300-second timeout. A 45-second diagnostic publish completed evaluation and
`GetTargetFrameworks`, then stopped in parallel project-reference traversal
before compiler invocation. Microsoft.Common.CurrentVersion.targets binds
those MSBuild tasks to `$(BuildInParallel)`.

One-variable publish probe:

- `-p:BuildInParallel=false`: exit 0 in 3.37 seconds, compiled all referenced
  projects and published `BepInEx.Preloader.dll`.

A second command-contract assertion was observed RED before adding that exact
publish property. No global node-count restriction was adopted.

### Legacy CLR2 metadata layout correction

The first successful two-root compile produced byte-identical DLLs but the
inspector failed closed because CLR2/net35 output intentionally has no
`TargetFrameworkAttribute`. The SDK source at
`Microsoft.Common.CurrentVersion.targets:3676` generates that attribute only
when `TargetingClr2Framework != true`; the controller confirmed the official
preloader has the same layout.

Before changing inspection, the actual patched bytes showed:

- assembly `BepInEx.Preloader`, version `5.4.23.5`;
- metadata `v2.0.50727`;
- `mscorlib` reference `2.0.0.0`; and
- `System.Core` reference `3.5.0.0`.

The inspector now reports net35 without loading the assembly only when all
three exact CLR2 reference signals match. Tests reject missing System.Core,
changed metadata version, changed mscorlib version, and a changed target
framework. The Python publication gate independently requires the same exact
values.

## Double-build, metadata, provenance, and publication

Two final complete CLI invocations used fresh work roots:

- `184402b251654583924999cc9ddcf039`;
- `72ea0c1b15c14167854d4c527f94a3c9`.

Each invocation itself built fresh `build-a` and `build-b` roots. All four DLLs
were byte-identical:

```text
1339f682e66de7d6276d6727b6bd24b0d3975f13a89b358f53914d7fb7dddfd3
```

Published DLL:

`data/oracle/compat/builds/1339f682e66de7d6276d6727b6bd24b0d3975f13a89b358f53914d7fb7dddfd3/BepInEx.Preloader.dll`

Exact final metadata:

```json
{
  "assembly_name": "BepInEx.Preloader",
  "assembly_version": "5.4.23.5",
  "metadata_version": "v2.0.50727",
  "references": {
    "0Harmony": "2.9.0.0",
    "BepInEx": "5.4.23.5",
    "HarmonyXInterop": "1.0.0.0",
    "Mono.Cecil": "0.10.4.0",
    "MonoMod.RuntimeDetour": "22.1.29.1",
    "MonoMod.Utils": "22.1.29.1",
    "System": "2.0.0.0",
    "System.Core": "3.5.0.0",
    "mscorlib": "2.0.0.0"
  },
  "target_framework": ".NETFramework,Version=v3.5"
}
```

Canonical provenance:

```json
{
  "build_target": "BepInEx.Preloader/BepInEx.Preloader.csproj",
  "dependency_lock_sha256": "d58293afdc866819517bd629440b77f93b2d71499bc55676cad8f097f38d2f5b",
  "dotnet_sdk_version": "8.0.419",
  "official_preloader_sha256": "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627",
  "patch_sha256": "5d37abb8711650a7f7584988830bbba8849344e24630a0bc970930e4fa5726da",
  "patched_preloader_sha256": "1339f682e66de7d6276d6727b6bd24b0d3975f13a89b358f53914d7fb7dddfd3",
  "schema_version": 1,
  "source_commit": "57f1fb859bd4d0264cd2a59074d0e96c6a492a33",
  "toolchain_lock_sha256": "dee39ff37de4a90fe1069fb89f12a9cf989467fdcfd9608cb90accabeb989d25"
}
```

Canonical `current.json` points only to that hash-addressed DLL and provenance.
A direct canonical-byte audit passed for both JSON files (`2/2`).

## Generated-file tracking audit

Inspector build intermediates were redirected below the ignored output work
root. Task-created `oracle/compat/inspector/bin` and
`oracle/compat/inspector/obj` were removed, and a fresh focused test run
confirmed those paths remained absent.

`git status --short --untracked-files=all` shows only the two intended
inspector source files under `oracle/compat/inspector/`; it shows no generated
Task 4 `bin`, `obj`, DLL, PDB, assets, provenance, or `current.json` eligible
for accidental staging. All real build work and logs are under ignored
`data/oracle/compat/builds`.

## Self-review

- Public dataclasses and function signatures match the Task 4 brief.
- The local feed is required to contain exactly the ten dependency-lock
  filenames, and every nupkg SHA-256 is revalidated before a subprocess.
- NuGet config contains `<clear />` and exactly one local feed.
- Each build uses a distinct UUID fresh root, fresh package directory, copied
  committed lock files, and a prepared/patched source copy.
- Every SDK and inspector subprocess has a literal 300-second timeout and
  captured stdout/stderr.
- Publication stages and fsyncs the DLL and canonical provenance, atomically
  installs the hash directory, then atomically replaces `current.json`.
- No game path was read or written.
- `git diff --check` reports no whitespace errors.

## Concerns

1. SDK processes print a non-fatal macOS
   `CSSM_ModuleLoad(): One or more parameters passed to a function were not
   valid.` line. All final restores and publishes exit 0; the line remains in
   captured logs rather than being suppressed.
2. The real CLR2/net35 layout has no `TargetFrameworkAttribute`. The inspector
   uses an exact three-signal inference, with positive and negative integration
   coverage, and the Python publish gate independently rechecks the exact
   result.
3. The legacy recursive project graph deadlocks under parallel traversal in
   this SDK. Restore and publish serialization are narrowly scoped to the
   controlling MSBuild properties and covered by command-contract tests.
4. Deferred Task 2 and Task 3 ledger minors were not changed; they remain
   final-review work as directed.

## Fix Round 1 evidence (2026-07-28)

Implemented the seven findings from
`task-4-fix-round-1-brief.md` without modifying the pinned source, patch,
toolchain, dependency lock, or game installation.

### Focused RED/GREEN evidence

- Compiled patch proof: the new inspector mode locates exactly one
  `BepInEx.Preloader.PlatformUtils.SetPlatform`, decodes its IL operands, and
  requires exactly one CoreServices string token and no AccessibilityBundles
  token. The real installed official preloader is rejected in patch mode, the
  patched DLL is accepted, and the builder rejects bytes equal to the locked
  official hash. Focused result: `3 passed`.
- SDK authentication: symlinked supplied SDK paths and a changed archive fail;
  a successful build executes only `dotnet` from `verified-sdk` below its fresh
  work root. The canonical archive is rehashed with SHA-512 and safely
  re-extracted for every invocation. Focused result: `3 passed`.
- Timeout cleanup: the process starts in a new session; timeout sends SIGTERM
  to the process group, escalates to SIGKILL, drains output, and preserves the
  timeout log. A real child-process survival regression passed: `1 passed`.
- Publication: output-root, output-parent, `.work`, digest-directory, DLL,
  provenance, and `current.json` symlinks are rejected. An existing digest
  directory must contain exactly its two expected regular files and no extra
  entries. Focused result: `8 passed`.
- Legacy metadata: both the missing-TFA inspector inference and the independent
  Python publication gate require the exact identity, version, CLR metadata,
  and complete nine-reference map. Missing, extra, and changed reference maps
  are rejected. Focused result: `5 passed`.
- Provenance: schema 1 retains its exact key set and now requires
  `BepInEx.Preloader/BepInEx.Preloader.csproj@framework=net35`.
- PE hardening: a non-empty managed-native directory is explicitly rejected
  and covered by a mutated PE fixture.

Full compatibility suite:

```text
65 passed in 31.00s
```

### Fresh authenticated real builds

Two complete CLI invocations used distinct fresh output roots:

- `/private/tmp/ssr-task4-real-a.vhw7cu`
- `/private/tmp/ssr-task4-real-b.sGTI5A`

Each invocation safely extracted the verified SDK archive into its own
UUID-named work root and performed independent `build-a` and `build-b`
publishes. All four output DLLs were byte-identical:

```text
5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816
```

Patch-mode inspection of the real result succeeded. Its exact metadata remains:

```json
{
  "assembly_name": "BepInEx.Preloader",
  "assembly_version": "5.4.23.5",
  "metadata_version": "v2.0.50727",
  "references": {
    "0Harmony": "2.9.0.0",
    "BepInEx": "5.4.23.5",
    "HarmonyXInterop": "1.0.0.0",
    "Mono.Cecil": "0.10.4.0",
    "MonoMod.RuntimeDetour": "22.1.29.1",
    "MonoMod.Utils": "22.1.29.1",
    "System": "2.0.0.0",
    "System.Core": "3.5.0.0",
    "mscorlib": "2.0.0.0"
  },
  "target_framework": ".NETFramework,Version=v3.5"
}
```

The two canonical provenance files were byte-identical. The final provenance
uses the framework-bearing target and the new patched hash; both canonical
`current.json` files point only to the matching hash-addressed DLL and
provenance.

### Final audits

- Installed official preloader SHA-256:
  `309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627`.
- Installed game `Assembly-CSharp.dll` SHA-256 remained:
  `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`.
- No Task 4 inspector `bin` or `obj` directory exists in the repository.
- `git status --short --untracked-files=all` shows no generated Task 4 file
  eligible for staging; owner-local `.DS_Store`, plan, decompilation, README,
  and plugin changes remain untouched.
- `git diff --check` passed.
