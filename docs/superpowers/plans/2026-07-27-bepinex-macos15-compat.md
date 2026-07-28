# BepInEx macOS 15 Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, deploy, verify, and exactly restore a source-patched BepInEx
5.4.23.5 preloader that correctly identifies macOS 15 under SSR's legacy Mono
runtime.

**Architecture:** A dependency-free Python compatibility module validates
Git-tracked trust inputs, the pinned recursive upstream checkout, locked NuGet
packages, canonical provenance, and two independent deterministic builds. The
existing manifest installer gains compatibility-aware status plus transactional
deploy/restore commands. A narrow boot-probe module owns process/log evidence
without modifying `Sausage.app`.

**Tech Stack:** Python 3.12+, pytest 8+, Git, .NET SDK 8.0.419 installed locally
below ignored `data/oracle/compat/`, SDK-style `net35` C# projects, NuGet locked
restore, `System.Reflection.Metadata`.

## Global Constraints

- Work only in
  `/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle` on
  branch `codex/ssr-executable-oracle`.
- Preserve the current uncommitted Task 2 changes in
  `docs/superpowers/plans/2026-07-27-executable-oracle.md` and `oracle/`;
  never stage them in a compatibility-task commit unless that task explicitly
  names the same file.
- Never modify `Sausage.app`, its game assembly, ordinary save data, or the
  Steam launcher.
- Expected game assembly SHA-256:
  `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`.
- Official BepInEx archive SHA-256:
  `01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323`.
- Official `BepInEx.Preloader.dll` SHA-256:
  `309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627`.
- BepInEx source commit:
  `57f1fb859bd4d0264cd2a59074d0e96c6a492a33`.
- Recursive `submodules/BepInEx.Harmony` commit:
  `d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa`.
- Upstream build target:
  `BepInEx.Preloader/BepInEx.Preloader.csproj`, configuration `Release`,
  target framework `net35`.
- Use local .NET SDK 8.0.419. The installed SDK 10.0.300 is not a fallback: two
  inspected dry publishes hung without output and were terminated.
- Build and deploy perform no network access. Package and SDK fetching are
  explicit operator actions into ignored `data/oracle/compat/`.
- Commit only patch, locks, source tooling, tests, and documentation. Never
  commit upstream source, packages, SDK files, build intermediates, DLLs, or
  boot logs.
- Generated/recovery paths use resolved roots, reject symlinks, and use
  exclusive UTC-timestamp-plus-128-bit-random names.
- Each implementation task uses TDD, ends with focused and regression tests,
  receives a requirements review and a code-quality review, and commits only
  its named files.

## File Map

- Create `oracle/compat/bepinex-macos15-platform.patch`: the exact one-hunk
  upstream patch.
- Create `oracle/compat/toolchain.json`: exact SDK, commits, project, framework,
  build properties, and official metadata.
- Create `oracle/compat/dependencies.json`: exact package IDs, versions,
  download sources, filenames, and `.nupkg` SHA-256 values.
- Create `oracle/compat/nuget-lock/**/packages.lock.json`: five locked project
  graphs, kept at upstream-relative paths.
- Create `oracle/compat/trust.json`: hashes of every committed compatibility
  input.
- Create `oracle/compat/inspector/SsrOracle.CompatInspector.csproj` and
  `Program.cs`: emit strict assembly metadata JSON using
  `System.Reflection.Metadata`; do not load the inspected DLL.
- Create `src/ssr_env/oracle_compat.py`: schemas, trust/source/package
  validation, patch application, build orchestration, provenance, and assembly
  inspection.
- Create `tools/build_bepinex_compat.py`: CLI for `fetch-sdk`,
  `fetch-packages`, `lock`, `build`, and `inspect`.
- Modify `src/ssr_env/oracle_install.py`: compatibility status and transactional
  deploy/restore.
- Modify `tools/oracle_install.py`: continue delegating to the installer main.
- Create `src/ssr_env/oracle_boot.py` and `tools/oracle_boot_probe.py`: bounded
  boot process, marker verification, configuration reset, and log evidence.
- Create `tests/test_oracle_compat.py`,
  `tests/test_oracle_install_compat.py`, and `tests/test_oracle_boot.py`.
- Modify `.gitignore` and `oracle/README.md`.

---

### Task 1: Pin the Upstream Patch, Toolchain, and NuGet Graph

**Files:**

- Create: `oracle/compat/bepinex-macos15-platform.patch`
- Create: `oracle/compat/toolchain.json`
- Create:
  `oracle/compat/nuget-lock/BepInEx.Preloader/packages.lock.json`
- Create: `oracle/compat/nuget-lock/BepInEx/packages.lock.json`
- Create:
  `oracle/compat/nuget-lock/submodules/BepInEx.Harmony/HarmonyXInterop/packages.lock.json`
- Create:
  `oracle/compat/nuget-lock/submodules/BepInEx.Harmony/HarmonyX2Interop/packages.lock.json`
- Create:
  `oracle/compat/nuget-lock/submodules/BepInEx.Harmony/BepInEx.Harmony/packages.lock.json`
- Modify: `.gitignore`

**Interfaces:**

- Consumes: the ignored recursive checkout at
  `data/oracle/compat/upstream/BepInEx-5.4.23.5`.
- Produces: immutable inputs consumed by every later compatibility task.

- [ ] **Step 1: Verify the inspected checkout and record the RED boot**

Run:

```bash
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 rev-parse HEAD
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 submodule status
rg -n 'AccessibilityBundles|libc\.so\.6' \
  data/oracle/compat/upstream/BepInEx-5.4.23.5/BepInEx.Preloader/Platform.cs
rg -n 'DllNotFoundException: libc\.so\.6' \
  data/oracle/boot-probe
```

Expected: exact parent/submodule commits from Global Constraints, one obsolete
probe, one Linux import, and the preserved failed-boot trace.

- [ ] **Step 2: Create the exact one-hunk patch**

The patch must contain this sole semantic replacement in
`BepInEx.Preloader/Platform.cs`:

```diff
-            else if (Is(current, Platform.Unix) && Directory.Exists("/System/Library/AccessibilityBundles"))
+            else if (Is(current, Platform.Unix) && Directory.Exists("/System/Library/CoreServices"))
             {
-                current = Platform.iOS;
+                current = Platform.MacOS;
             }
```

Generate it against the pinned checkout, then verify:

```bash
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  apply --check ../../../../../oracle/compat/bepinex-macos15-platform.patch
git apply --numstat oracle/compat/bepinex-macos15-platform.patch
git apply --summary oracle/compat/bepinex-macos15-platform.patch
```

Expected: one text file, one hunk, two removed lines, two added lines.

- [ ] **Step 3: Install and prove the local SDK**

Fetch the official macOS Arm64 SDK 8.0.419 archive and its Microsoft-published
SHA-512 sidecar into `data/oracle/compat/downloads/`, verify the sidecar, and
extract into `data/oracle/compat/dotnet-8.0.419/`. Do not use a mutable
`dotnet-install.sh`.

Run:

```bash
curl --fail --location --proto '=https' \
  --output data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz \
  https://builds.dotnet.microsoft.com/dotnet/Sdk/8.0.419/dotnet-sdk-8.0.419-osx-arm64.tar.gz
curl --fail --location --proto '=https' \
  --output data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz.sha512 \
  https://builds.dotnet.microsoft.com/dotnet/Sdk/8.0.419/dotnet-sdk-8.0.419-osx-arm64.tar.gz.sha512
shasum -a 512 \
  data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz
sed -n '1p' \
  data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz.sha512
data/oracle/compat/dotnet-8.0.419/dotnet --version
```

Expected: the computed and published SHA-512 strings are identical and the SDK
prints exactly `8.0.419`. Record the verified archive SHA-512 in
`toolchain.json` as `dotnet_sdk_archive_sha512`; do not extract if they differ.

- [ ] **Step 4: Generate the five locked graphs**

In a fresh temporary copy of the recursive checkout, apply the patch and run:

```bash
data/oracle/compat/dotnet-8.0.419/dotnet restore \
  BepInEx.Preloader/BepInEx.Preloader.csproj \
  --use-lock-file --force-evaluate \
  --packages data/oracle/compat/inspection-packages
```

Copy the five generated `packages.lock.json` files into the exact committed
paths listed above. Assert that their union is exactly:

```text
HarmonyX 2.0.6
HarmonyX 2.9.0
Microsoft.NETFramework.ReferenceAssemblies 1.0.3
Microsoft.NETFramework.ReferenceAssemblies.net35 1.0.3
Mono.Cecil 0.10.4
MonoMod.RuntimeDetour 20.5.21.5
MonoMod.RuntimeDetour 22.1.29.1
MonoMod.Utils 20.5.21.5
MonoMod.Utils 22.1.29.1
UnityEngine 5.6.1
```

- [ ] **Step 5: Create the concrete toolchain lock**

Write canonical sorted JSON with schema version 1 and these values:

```json
{
  "build_properties": {
    "Configuration": "Release",
    "ContinuousIntegrationBuild": "true",
    "Deterministic": "true",
    "PathMap": "{source_root}=/_/src"
  },
  "dotnet_sdk_version": "8.0.419",
  "framework": "net35",
  "harmony_submodule_commit": "d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa",
  "official_preloader_sha256": "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627",
  "project": "BepInEx.Preloader/BepInEx.Preloader.csproj",
  "schema_version": 1,
  "source_commit": "57f1fb859bd4d0264cd2a59074d0e96c6a492a33"
}
```

The implementation substitutes the actual temporary root into the command; the
lock stores the literal template `{source_root}=/_/src`. After verifying the
SDK sidecar in Step 3, add `dotnet_sdk_archive_sha512` with the exact computed
lowercase 128-hex value before writing the canonical file. Schema validation
requires that key and format.

- [ ] **Step 6: Ignore all generated compatibility material**

Append:

```gitignore
# Locally fetched/built BepInEx compatibility material; never commit.
data/oracle/compat/
```

Run:

```bash
git check-ignore -v data/oracle/compat/upstream/BepInEx-5.4.23.5
git diff --check
```

Expected: ignored upstream path and no whitespace errors.

- [ ] **Step 7: Commit only immutable inputs**

```bash
git add .gitignore oracle/compat/bepinex-macos15-platform.patch \
  oracle/compat/toolchain.json oracle/compat/nuget-lock
git commit -m "build: pin BepInEx compatibility inputs"
```

---

### Task 2: Validate Trust Inputs and Canonical Provenance

**Files:**

- Create: `src/ssr_env/oracle_compat.py`
- Create: `tests/test_oracle_compat.py`
- Create: `oracle/compat/dependencies.json`
- Create: `oracle/compat/trust.json`
- Create: `tools/build_bepinex_compat.py`

**Interfaces:**

- Produces:
  `CompatError`, `CompatTrust`, `ToolchainLock`, `PackagePin`,
  `BuildProvenance`, `load_trust(repo_root: Path) -> CompatTrust`,
  `parse_trust_data(data: object) -> CompatTrust`,
  `load_provenance(path: Path, trust: CompatTrust) -> BuildProvenance`,
  `canonical_json(value: object) -> bytes`, and CLI commands `fetch-packages`
  and `lock`.

- [ ] **Step 1: Write failing exact-schema and Git-trust tests**

Add tests with these names and assertions:

```python
def test_load_trust_requires_exact_schema_and_lowercase_hashes():
    malformed = {
        "schema_version": 1,
        "patch_sha256": "A" * 64,
        "toolchain_sha256": "0" * 64,
        "dependencies_sha256": "1" * 64,
        "nuget_lock_tree_sha256": "2" * 64,
    }
    with pytest.raises(CompatError, match="trust schema"):
        parse_trust_data(malformed)

def test_load_trust_rejects_untracked_or_dirty_named_input(
    committed_compat_repo: Path,
):
    patch = (
        committed_compat_repo
        / "oracle/compat/bepinex-macos15-platform.patch"
    )
    patch.write_text("locally replaced")
    with pytest.raises(CompatError, match="HEAD blob"):
        load_trust(committed_compat_repo)

def test_load_provenance_rejects_unknown_keys_and_hash_mismatch(
    committed_compat_repo: Path,
    valid_provenance: Path,
):
    trust = load_trust(committed_compat_repo)
    decoded = json.loads(valid_provenance.read_text())
    decoded["unexpected"] = True
    valid_provenance.write_bytes(canonical_json(decoded))
    with pytest.raises(CompatError, match="provenance"):
        load_provenance(valid_provenance, trust)

def test_canonical_json_is_sorted_utf8_with_final_newline():
    assert canonical_json({"b": 2, "a": 1}) == b'{\n  "a": 1,\n  "b": 2\n}\n'
```

- [ ] **Step 2: Run the tests to verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py -q
```

Expected: collection fails because `ssr_env.oracle_compat` does not exist.

- [ ] **Step 3: Implement strict immutable dataclasses and parsers**

Use frozen, slotted dataclasses. Reject booleans where integers are expected,
unknown/missing keys, non-lowercase 64-hex hashes, absolute/parent-traversing
paths, strings over 4096 bytes, and non-canonical JSON. Run Git with argument
arrays and `check=True`; never use a shell.

Core shapes:

```python
@dataclass(frozen=True, slots=True)
class CompatTrust:
    schema_version: int
    patch_sha256: str
    toolchain_sha256: str
    dependencies_sha256: str
    nuget_lock_tree_sha256: str

@dataclass(frozen=True, slots=True)
class ToolchainLock:
    schema_version: int
    source_commit: str
    harmony_submodule_commit: str
    dotnet_sdk_version: str
    dotnet_sdk_archive_sha512: str
    project: str
    framework: str
    official_preloader_sha256: str
    build_properties: tuple[tuple[str, str], ...]

@dataclass(frozen=True, slots=True)
class PackagePin:
    package_id: str
    version: str
    source_index: str
    filename: str
    sha256: str
    content_hash: str

@dataclass(frozen=True, slots=True)
class BuildProvenance:
    schema_version: int
    source_commit: str
    patch_sha256: str
    toolchain_lock_sha256: str
    dotnet_sdk_version: str
    dependency_lock_sha256: str
    build_target: str
    official_preloader_sha256: str
    patched_preloader_sha256: str
```

`load_trust` must compare each live trust input to
`git show HEAD:oracle/compat/<name>` and verify that `trust.json` itself is
tracked and
identical to its `HEAD` blob before trusting its hashes.

- [ ] **Step 4: Implement deterministic package fetch and lock commands**

`fetch-packages --feed-dir PATH` downloads only the ten ID/version pairs from
Task 1, saves lowercase NuGet filenames, hashes bytes while streaming, rejects
redirects outside HTTPS, and never overwrites different bytes.

`lock --feed-dir PATH` reads NuGet `contentHash` and `.nupkg` SHA-256 values,
writes `dependencies.json`, computes the sorted
`relative-posix-path + NUL + file-sha256 + LF` lock-tree digest, then writes
`trust.json`. It refuses to run unless patch/toolchain/locks are clean `HEAD`
blobs; after writing new dependency/trust files, the operator stages and
commits them before `load_trust` can succeed.

- [ ] **Step 5: Run focused tests and the CLI lock flow**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py fetch-packages \
  --feed-dir data/oracle/compat/feed
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py lock \
  --feed-dir data/oracle/compat/feed
```

Expected: tests pass; exactly ten `.nupkg` files exist locally; canonical
`dependencies.json` and `trust.json` are produced.

- [ ] **Step 6: Commit trust tooling and catalogs**

```bash
git add src/ssr_env/oracle_compat.py tests/test_oracle_compat.py \
  tools/build_bepinex_compat.py oracle/compat/dependencies.json \
  oracle/compat/trust.json
git commit -m "feat: validate BepInEx compatibility trust"
```

---

### Task 3: Validate and Patch the Recursive Upstream Checkout

**Files:**

- Modify: `src/ssr_env/oracle_compat.py`
- Modify: `tests/test_oracle_compat.py`

**Interfaces:**

- Produces:
  `SourceCheckout`,
  `validate_source_checkout(source: Path, trust: CompatTrust) -> SourceCheckout`,
  and
  `prepare_source(source: SourceCheckout, destination: Path,
  trust: CompatTrust) -> Path`, plus
  `source_differences(source: Path, prepared: Path) -> list[str]`.

- [ ] **Step 1: Write failing source and patch-boundary tests**

```python
def test_prepare_source_changes_only_platform_cs_one_hunk(
    pinned_recursive_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(pinned_recursive_checkout, trust)
    prepared = prepare_source(source, tmp_path / "prepared", trust)
    platform = prepared / "BepInEx.Preloader/Platform.cs"
    assert "AccessibilityBundles" not in platform.read_text(encoding="utf-8-sig")
    assert platform.read_text(encoding="utf-8-sig").count(
        "/System/Library/CoreServices"
    ) == 1
    changed = source_differences(pinned_recursive_checkout, prepared)
    assert changed == ["BepInEx.Preloader/Platform.cs"]
```

The same test module must construct recursive Git fixtures and add explicit
tests named
`test_validate_source_checkout_rejects_wrong_head`,
`test_validate_source_checkout_rejects_dirty_tracked_file`,
`test_validate_source_checkout_rejects_untracked_file`,
`test_validate_source_checkout_requires_exact_harmony_submodule`,
`test_prepare_source_rejects_already_patched_source`, and
`test_prepare_source_rejects_changed_preimage`. Each asserts `CompatError`
with `source commit`, `clean checkout`, `submodule commit`, or `patch preimage`
respectively.

- [ ] **Step 2: Verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py -k 'source or patch' -q
```

Expected: missing interfaces.

- [ ] **Step 3: Implement fail-closed checkout validation**

`validate_source_checkout` requires:

```text
git rev-parse HEAD == 57f1fb859bd4d0264cd2a59074d0e96c6a492a33
git status --porcelain=v1 --untracked-files=all == ""
git submodule status --recursive ==
 d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa submodules/BepInEx.Harmony
```

Reject a leading `-`, `+`, or `U` submodule status. Resolve all paths and reject
symlinked checkout roots or patch targets.

Define:

```python
@dataclass(frozen=True, slots=True)
class SourceCheckout:
    root: Path
    source_commit: str
    harmony_submodule_commit: str
```

- [ ] **Step 4: Implement isolated preparation**

Copy tracked files and initialized submodule files without the source checkout's
Git metadata into a new absent destination. Apply the committed patch with:

```python
subprocess.run(
    ["git", "apply", "--check", str(patch)],
    cwd=destination, check=True, text=True, capture_output=True,
)
subprocess.run(
    ["git", "apply", str(patch)],
    cwd=destination, check=True, text=True, capture_output=True,
)
```

Hash every copied file before and after; permit a difference only at
`BepInEx.Preloader/Platform.cs`. Confirm old probe count zero, new probe count
one, and `Platform.MacOS` occurs in the patched hunk.

- [ ] **Step 5: Run focused and regression tests**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/ssr_env/oracle_compat.py tests/test_oracle_compat.py
git commit -m "feat: prepare pinned BepInEx source"
```

---

### Task 4: Build Twice and Inspect the Legacy Preloader

**Files:**

- Create: `oracle/compat/inspector/SsrOracle.CompatInspector.csproj`
- Create: `oracle/compat/inspector/Program.cs`
- Modify: `src/ssr_env/oracle_compat.py`
- Modify: `tests/test_oracle_compat.py`
- Modify: `tools/build_bepinex_compat.py`

**Interfaces:**

- Produces:
  `AssemblyMetadata`,
  `BuildResult`,
  `inspect_assembly(path: Path, inspector: Path) -> AssemblyMetadata`,
  `build_compat_preloader(source: Path, sdk: Path, feed_dir: Path,
  output_dir: Path, repo_root: Path) -> BuildResult`, and CLI commands
  `inspect` and `build`.

- [ ] **Step 1: Write failing inspector and double-build tests**

```python
def test_inspector_reports_identity_version_clr_and_references(
    official_preloader: Path,
    built_inspector: Path,
):
    metadata = inspect_assembly(official_preloader, built_inspector)
    assert metadata.name == "BepInEx.Preloader"
    assert metadata.target_framework == ".NETFramework,Version=v3.5"
    assert metadata.metadata_version.startswith("v2.0")
    assert dict(metadata.references)["mscorlib"] == "2.0.0.0"
```

Add deterministic fake-runner tests named
`test_build_rejects_nonidentical_second_output`,
`test_build_rejects_wrong_metadata`,
`test_build_timeout_preserves_log`, and
`test_build_publishes_only_after_all_checks`. The final test asserts
`result.dll.parent.name == result.patched_sha256` and that the provenance bytes
equal `canonical_json(asdict(result.provenance_data))`.

- [ ] **Step 2: Verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py -k 'inspector or build' -q
```

- [ ] **Step 3: Implement the non-loading metadata inspector**

The `net8.0` executable accepts one DLL path and emits one canonical JSON object
with exact keys:

```json
{
  "assembly_name": "BepInEx.Preloader",
  "assembly_version": "5.4.23.5",
  "metadata_version": "v2.0.50727",
  "references": {"mscorlib": "2.0.0.0"},
  "target_framework": ".NETFramework,Version=v3.5"
}
```

Use `PEReader` and `MetadataReader`; never call `Assembly.Load*`. Treat missing,
duplicate, malformed, native, or mixed-mode metadata as exit 2.

Python result types are exact:

```python
@dataclass(frozen=True, slots=True)
class AssemblyMetadata:
    name: str
    version: str
    metadata_version: str
    target_framework: str
    references: tuple[tuple[str, str], ...]

@dataclass(frozen=True, slots=True)
class BuildResult:
    dll: Path
    provenance: Path
    patched_sha256: str
    metadata: AssemblyMetadata
    provenance_data: BuildProvenance
```

- [ ] **Step 4: Implement offline locked restore and publish**

For each of two different fresh roots:

1. call `prepare_source`;
2. copy the five committed lock files into upstream-relative paths;
3. validate the ten local-feed `.nupkg` hashes;
4. generate a NuGet config containing `<clear />` and one local source;
5. run SDK 8.0.419 restore with `--locked-mode`, `--no-cache`, a fresh packages
   directory, and that config;
6. run publish with `--no-restore --disable-build-servers`, exact project,
   `Release`, `Deterministic=true`, `ContinuousIntegrationBuild=true`, and
   `PathMap={source_root}=/_/src`;
7. accept only `BepInEx.Preloader.dll`.

Every subprocess uses a 300-second timeout and captured output. A timeout is
`CompatError("BepInEx build timed out")` with the captured log preserved below
the ignored output root.

- [ ] **Step 5: Compare, inspect, and publish**

Require byte equality, then validate exact assembly name, `net35`, CLR v2,
`mscorlib` 2.0, source/patch/lock hashes, version from the toolchain, and the
reviewed accepted patched-preloader SHA-256
`5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816`.
Write DLL and provenance to a new
`<output>/<patched-sha256>/` directory, fsync, then atomically write
`<output>/current.json`. Refuse different existing bytes.

- [ ] **Step 6: Run the real local build twice**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py build \
  --source data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  --sdk data/oracle/compat/dotnet-8.0.419/dotnet \
  --feed-dir data/oracle/compat/feed \
  --output-dir data/oracle/compat/builds
```

Expected: one hash-addressed result, canonical provenance, byte-identical build
marker, CLR v2/net35 metadata, and no tracked generated files. If SDK 8.0.419
cannot complete within 300 seconds, stop this plan at Task 4; do not select a
different SDK without a design amendment.

- [ ] **Step 7: Test and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_compat.py -q
git status --short
git add oracle/compat/inspector src/ssr_env/oracle_compat.py \
  tests/test_oracle_compat.py tools/build_bepinex_compat.py
git commit -m "feat: build reproducible BepInEx preloader"
```

---

### Task 5: Add Fail-Closed Compatibility Status

**Files:**

- Modify: `src/ssr_env/oracle_install.py`
- Create: `tests/test_oracle_install_compat.py`

**Interfaces:**

- Consumes: `load_trust`, `load_provenance`, and assembly inspection from Task
  4.
- Produces:
  `PreloaderCompatibilityStatus`,
  `status_install(game_root: Path, repo_root: Path | None = None)`,
  `official`, `patched`, and `invalid` states.

- [ ] **Step 1: Add failing official/patched/invalid tests**

Create a fake runtime archive containing
`BepInEx/core/BepInEx.Preloader.dll`. Monkeypatch the expected official hash to
the fake bytes.

```python
@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_status_rejects_unmanaged_reserved_path(
    kind: str,
    installed_official_game: Path,
    tmp_path: Path,
):
    reserved = installed_official_game / "BepInEx/.ssr-oracle-compat"
    create_path_of_kind(reserved, kind, tmp_path)
    status = status_install(installed_official_game)
    assert status.preloader_compatibility.state == "invalid"
    assert "unmanaged_reserved_path" in (
        status.preloader_compatibility.issues
    )

def test_status_reports_invalid_stable_issue_codes(
    installed_patched_game: Path,
):
    active = (
        installed_patched_game / "BepInEx/core/BepInEx.Preloader.dll"
    )
    active.write_bytes(b"changed")
    status = status_install(installed_patched_game)
    assert status.preloader_compatibility.issues == (
        "active_hash_mismatch",
    )
```

Also add complete tests
`test_status_reports_official_only_when_reserved_paths_absent` and
`test_status_reports_patched_only_when_all_hashes_agree`; the fixtures create
canonical manifests/provenance using production serializers, not hand-written
permissive JSON.

- [ ] **Step 2: Verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install_compat.py -q
```

- [ ] **Step 3: Extend constants and immutable status types**

Add:

```python
PRELOADER_RELATIVE_PATH = "BepInEx/core/BepInEx.Preloader.dll"
PRELOADER_BACKUP_RELATIVE_PATH = (
    "BepInEx/.ssr-oracle-backup/BepInEx.Preloader.dll"
)
PRELOADER_PROVENANCE_RELATIVE_PATH = (
    "BepInEx/.ssr-oracle-compat/preloader-provenance.json"
)
EXPECTED_OFFICIAL_PRELOADER_SHA256 = (
    "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627"
)
```

`PreloaderCompatibilityStatus` contains `state`, `official_sha256`,
`active_sha256`, `patched_sha256`, and sorted tuple `issues`.

- [ ] **Step 4: Implement read-only classification**

Official requires the official active hash, matching manifest entry, and both
reserved live roots absent by `lstat`. Patched requires valid clean-HEAD trust,
canonical provenance, matching active/backup/manifest hashes, safe regular
files, owned parent directories, and exact agreement with the reviewed accepted
patched-preloader SHA-256. Reserved live directories must contain exactly the
owned expected entries without following symlinks. Every other combination is
invalid and makes `InstallStatus.healthy` false. Status never repairs.

- [ ] **Step 5: Test and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install_compat.py tests/test_oracle_install.py -q
git add src/ssr_env/oracle_install.py tests/test_oracle_install_compat.py
git commit -m "feat: report preloader compatibility status"
```

---

### Task 6: Deploy the Patched Preloader Transactionally

**Files:**

- Modify: `src/ssr_env/oracle_install.py`
- Modify: `tests/test_oracle_install_compat.py`

**Interfaces:**

- Produces:
  `deploy_preloader(game_root: Path, preloader: Path, provenance: Path,
  repo_root: Path | None = None) -> InstallManifest` and CLI
  `deploy-preloader`.

- [ ] **Step 1: Write failing precondition and happy-path tests**

Cover wrong game/archive hash, unhealthy manifest, changed official preloader,
bad provenance, DLL metadata mismatch, unmanaged targets, symlink parents,
idempotent identical deployment, and different-build refusal.

The happy path asserts:

```python
assert active.read_bytes() == patched
assert backup.read_bytes() == official
assert canonical_deployed_provenance == supplied_provenance
assert manifest_hash(active) == sha256(patched).hexdigest()
assert status.preloader_compatibility.state == "patched"
```

- [ ] **Step 2: Verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install_compat.py -k deploy -q
```

- [ ] **Step 3: Implement all-read preflight**

Read and validate every input and destination before creating staging. Require
official status or return the existing manifest for a byte-identical patched
request. Snapshot active DLL, manifest, and modes. Stage backup, canonical
provenance, and patched DLL on the game filesystem.

- [ ] **Step 4: Implement publication and manifest-last rollback**

Publish backup, provenance, and patched DLL with atomic file replacement, then
write the updated manifest last. Retain no-follow directory descriptors from
preflight through publication and use descriptor-relative replacement; pathname
rechecks alone do not satisfy containment. Inject failures independently at
every file write/fsync, replace, parent-directory fsync, manifest atomic-write
sub-boundary, staging cleanup, and recovery movement. On any failure:

On macOS, use descriptor-relative `renameatx_np` with `RENAME_EXCL` for
required-absent destinations and `RENAME_SWAP` plus displaced-inode validation
for active/manifest replacement. Ordinary rename after a leaf check does not
satisfy the concurrent-substitution contract.

1. restore active DLL and manifest bytes/modes;
2. move newly created backup/provenance artifacts into an exclusive
   `.ssr-oracle-recovery/<timestamp>-<token>/compat/`;
3. remove only empty created live directories with `rmdir`;
4. report rollback failures without hiding the original failure.

Inject a failure after each file replace and manifest write. Each test asserts
exact pre-call active/manifest bytes and modes plus preserved recovery bytes.

- [ ] **Step 5: Add the CLI**

Parser arguments are exact:

```text
deploy-preloader --game-root PATH --preloader PATH --provenance PATH
                  [--repo-root PATH]
```

Success prints the canonical manifest JSON and exits 0; validation/mutation
failure prints one `error:` line to stderr and exits 2.

- [ ] **Step 6: Test and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install_compat.py tests/test_oracle_install.py -q
git add src/ssr_env/oracle_install.py tests/test_oracle_install_compat.py
git commit -m "feat: deploy patched BepInEx preloader"
```

---

### Task 7: Restore the Official Preloader Transactionally

**Files:**

- Modify: `src/ssr_env/oracle_install.py`
- Modify: `tests/test_oracle_install_compat.py`

**Interfaces:**

- Produces:
  `restore_preloader(game_root: Path, repo_root: Path | None = None) ->
  tuple[InstallManifest, Path]` and CLI `restore-preloader`.

- [ ] **Step 1: Write failing restore and failure-boundary tests**

Cover official-state refusal, changed active/backup/provenance, trust mismatch,
reserved symlinks, recovery collision retry, success, and failures after:

```text
backup move
provenance move
active replacement
final manifest write
first rmdir
second rmdir
```

Every injected failure must return to byte/mode-identical patched state or
raise a hard rollback error while preserving both copies.

- [ ] **Step 2: Verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install_compat.py -k restore -q
```

- [ ] **Step 3: Implement the exact restore state machine**

After full patched-state validation and snapshots:

1. create exclusive recovery directory;
2. move backup and provenance into it, preserving relative paths/modes;
3. atomically replace active with validated backup bytes;
4. atomically write one final official manifest with compatibility entries
   removed;
5. `rmdir` only the two empty live compatibility directories;
6. re-run status and require `official`.

Rollback reverses each completed step and restores the patched manifest last.
Never recursively delete or overwrite a recovery collision.

- [ ] **Step 4: Add CLI and repeat behavior**

Parser:

```text
restore-preloader --game-root PATH [--repo-root PATH]
```

Success JSON contains `manifest` and absolute `recovery`. Calling restore in
official state exits 2 with `preloader compatibility is not patched`.

- [ ] **Step 5: Test and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_install_compat.py tests/test_oracle_install.py -q
git add src/ssr_env/oracle_install.py tests/test_oracle_install_compat.py
git commit -m "feat: restore official BepInEx preloader"
```

---

### Task 8: Preserve Boot Evidence and Enforce Marker-Based Success

**Files:**

- Create: `src/ssr_env/oracle_boot.py`
- Create: `tools/oracle_boot_probe.py`
- Create: `tests/test_oracle_boot.py`

**Interfaces:**

- Produces:
  `LogFingerprint`,
  `BootEvidence`,
  `BootProbeResult`,
  `fingerprint_preloader_logs(game_root: Path) ->
  tuple[LogFingerprint, ...]`,
  `collect_boot_evidence(before: tuple[LogFingerprint, ...],
  game_root: Path, evidence_root: Path) -> BootEvidence`,
  `run_boot_probe(game_root: Path, launcher: Path, config: Path,
  evidence_root: Path, timeout_seconds: int) -> BootProbeResult`, and CLI main.

- [ ] **Step 1: Write failing log-baseline and process tests**

```python
def test_collect_moves_only_new_regular_logs(tmp_path: Path):
    game = tmp_path / "game"
    game.mkdir()
    old = game / "preloader_old.log"
    old.write_text("keep")
    before = fingerprint_preloader_logs(game)
    new = game / "preloader_new.log"
    new.write_text("BepInEx 5.4.23.5")
    result = collect_boot_evidence(before, game, tmp_path / "evidence")
    assert old.read_text() == "keep"
    assert not new.exists()
    assert [path.name for path in result.moved_logs] == ["preloader_new.log"]
```

Add complete tests named
`test_collect_leaves_changed_preexisting_log_and_copies_evidence`,
`test_collect_rejects_new_symlink_log`,
`test_probe_requires_all_three_markers`,
`test_probe_terminates_only_spawned_process_and_resets_mode`, and
`test_probe_timeout_is_failure_with_evidence`.

- [ ] **Step 2: Verify RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_boot.py -q
```

- [ ] **Step 3: Implement immutable fingerprints and evidence collection**

Fingerprint resolved path, `lstat` type, inode, size, nanosecond mtime, and
SHA-256. After the process exits:

- move only new in-root regular non-symlink logs;
- copy but do not move a changed pre-existing log, and mark failure;
- reject new symlinks or paths escaping the game root;
- use
  `data/oracle/boot-probe/<timestamp>-<128-bit-token>/`;
- write canonical `probe.json` containing pre/post hashes and marker results.

Define:

```python
@dataclass(frozen=True, slots=True)
class LogFingerprint:
    path: Path
    inode: int
    size: int
    mtime_ns: int
    sha256: str

@dataclass(frozen=True, slots=True)
class BootEvidence:
    evidence_dir: Path
    moved_logs: tuple[Path, ...]
    copied_logs: tuple[Path, ...]
    issues: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class BootProbeResult:
    success: bool
    evidence_dir: Path
    moved_logs: tuple[Path, ...]
    copied_logs: tuple[Path, ...]
    markers: tuple[str, ...]
    issues: tuple[str, ...]
    exit_code: int | None
```

- [ ] **Step 4: Implement bounded exact-process control**

Use `subprocess.Popen` with an argument list, record its PID and process group,
and never search by process name. On timeout, send TERM only to that spawned
group, wait 10 seconds, then KILL only that group. A `finally` block restores
the exact config bytes/mode that existed before the probe.

Require literal markers for:

```text
BepInEx 5.4.23.5
Unity v2018.4.25f1
[SsrOracle] ready
```

Also fail on `DllNotFoundException`, `Preloader error`, unexpected exit, or
installer status other than patched.

- [ ] **Step 5: Add CLI and tests**

```text
oracle_boot_probe.py --game-root PATH --launcher PATH --config PATH
                     --evidence-root PATH --timeout 120
```

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest tests/test_oracle_boot.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/ssr_env/oracle_boot.py tools/oracle_boot_probe.py \
  tests/test_oracle_boot.py
git commit -m "feat: add controlled oracle boot probe"
```

---

### Task 9: Document, Deploy, Boot-Test, Restore-Test, and Re-deploy

**Files:**

- Modify: `oracle/README.md`
- Modify:
  `docs/superpowers/plans/2026-07-27-executable-oracle.md` only to record the
  compatibility prerequisite and Task 2 boot result; preserve all other
  existing uncommitted corrections.
- Modify:
  `.superpowers/sdd/2026-07-27-executable-oracle/progress.md` (ignored ledger)

**Interfaces:**

- Consumes: all Tasks 1–8 plus the Task 2 plugin build/harness.
- Produces: operator runbook, real GREEN boot evidence, proven exact restore,
  and a healthy patched state ready to resume executable-oracle Task 2.

- [ ] **Step 1: Document exact fetch/build/deploy/restore commands**

README must identify upstream source/license, both commits, SDK and package
pins, generated ignored locations, trust model, status states, failure
recovery, and the invariant that `Sausage.app` is never modified.

- [ ] **Step 2: Run focused and full verification before touching the game**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest \
  tests/test_oracle_compat.py tests/test_oracle_install_compat.py \
  tests/test_oracle_boot.py tests/test_oracle_install.py -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
dotnet build oracle/plugin/SsrOracle.Plugin.csproj \
  -c Release --no-restore
dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore
git status --short
```

Expected: focused and full Python suites pass; plugin build has zero errors and
warnings; C# harness prints its ready/success marker; only known owner-local and
Task 2 partial changes remain.

- [ ] **Step 3: Record real preflight**

Run installer status, game assembly SHA-256, active preloader SHA-256, and
`codesign --verify --deep --strict` before deployment. Require healthy official
status, expected assembly/preloader hashes, and only the previously recorded
`Foregroundr.bundle` signature failure.

- [ ] **Step 4: Deploy and run the controlled GREEN boot**

Use the hash-addressed build result:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  deploy-preloader --game-root "$SSR_GAME_ROOT" \
  --preloader "$SSR_PATCHED_PRELOADER" \
  --provenance "$SSR_PATCHED_PROVENANCE"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_boot_probe.py \
  --game-root "$SSR_GAME_ROOT" \
  --launcher "$SSR_GAME_ROOT/run_bepinex.sh" \
  --config "$SSR_GAME_ROOT/BepInEx/config/dev.jlsor.ssr.oracle.cfg" \
  --evidence-root data/oracle/boot-probe --timeout 120
```

The operator resolves the three `SSR_*` variables to explicit absolute paths
and prints them before either command. Success requires all three exact markers,
no preloader exception, unchanged game assembly hash, healthy patched status,
mode reset to off, and no new signature difference.

- [ ] **Step 5: Prove exact restore**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  restore-preloader --game-root "$SSR_GAME_ROOT"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  status --game-root "$SSR_GAME_ROOT"
shasum -a 256 "$SSR_GAME_ROOT/BepInEx/core/BepInEx.Preloader.dll"
```

Expected: official status, exact official preloader hash, no live reserved
compatibility roots, and preserved recovery directory.

- [ ] **Step 6: Re-deploy the identical patch and verify readiness**

Re-run deploy and status, but do not launch again. Require healthy patched state,
unchanged assembly hash, and idempotent second identical deploy.

- [ ] **Step 7: Update docs/ledger and commit only documentation**

```bash
git add oracle/README.md \
  docs/superpowers/plans/2026-07-27-executable-oracle.md
git commit -m "docs: record BepInEx compatibility workflow"
```

- [ ] **Step 8: Final review and resumption gate**

Run `superpowers:verification-before-completion`, then
`superpowers:requesting-code-review`. Resume executable-oracle Task 2 only if:

```text
compatibility build reproducible
installer status patched and healthy
GREEN boot evidence preserved
official restore proven byte-for-byte
full Python suite green
legacy plugin build/harness green
Sausage.app and Assembly-CSharp.dll unchanged
```
