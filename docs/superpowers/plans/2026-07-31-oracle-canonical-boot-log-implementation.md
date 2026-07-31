# Canonical SSR Oracle Boot-Log Observer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the false-negative preloader-only boot observer with a fail-closed observer that recognizes authentic BepInEx 5.4.23.5 success only from the durable canonical `BepInEx/LogOutput.log` bytes.

**Architecture:** Keep the existing public API, schema-v1 records, descriptor-safe scanner, process-group cleanup, and evidence transaction. Internally classify three monitored log families, pin and revalidate the BepInEx disk-logging contract, attribute success only to a changed canonical log, persist live failure observations through final evidence collection, and reconcile a second authoritative inventory immediately before `Popen`.

**Tech Stack:** Python 3.12+, pytest, POSIX descriptor-relative file operations, BepInEx 5.4.23.5 pinned source behavior, Git worktrees.

## Global Constraints

- The authoritative design is `docs/superpowers/specs/2026-07-30-oracle-canonical-boot-log-design.md`.
- Complete all implementation, tests, and review offline. Do not deploy to, mutate, or launch the installed game.
- Keep `LogFingerprint`, `BootEvidence`, `BootProbeResult`, `fingerprint_preloader_logs(...)`, `collect_boot_evidence(...)`, the CLI arguments, CLI JSON shape, and `probe.json` schema version 1 unchanged.
- Keep the public markers exactly `BepInEx 5.4.23.5`, `Unity v2018.4.25f1`, and `SSR oracle boot probe loaded` in that order.
- Match the public Unity marker only against authentic source text `Detected Unity version: v2018.4.25f1`; reject the invented bare source literal and extended/lookalike versions.
- Monitor only exact game-relative `BepInEx/LogOutput.log`, `BepInEx/LogOutput.log.1` through `.4`, and recursively discovered case-sensitive basenames matching `preloader_*.log`.
- Success markers must all come from the changed/new canonical log. Error literals are graded across every retained monitored log.
- `preloader_*.log` and numbered fallback files are failure evidence whenever new or changed, regardless of their payload.
- Accept absent `BepInEx/config/BepInEx.cfg`, including an absent `BepInEx/config` directory, as pinned defaults. An existing file must have exactly one `[Logging.Disk]` section and exactly one valid `Enabled = true`, `AppendLog = false`, and sufficient `LogLevels` entry.
- Validate `[Logging.Console] LogLevels` because it filters the preloader's buffered `BepInEx 5.4.23.5` marker before the disk listener exists. An absent console section/key uses pinned defaults; a configured key must contain the full required visibility set.
- Required disk and configured console levels are `Fatal`, `Error`, `Warning`, `Message`, and `Info`; `Debug` is optional; the single value `All` is sufficient.
- Reject append mode, disabled logging, missing levels, duplicate relevant definitions within their exact section, invalid UTF-8, NUL, bare CR, inline comments, numeric/unknown/duplicate enum members, case-fold/whitespace lookalikes, unsafe paths, and any guarded config component/identity/content change before launch.
- Recheck and close the BepInEx logging guard before the authoritative inventory and `Popen`; never restore or postflight-check the runtime-owned BepInEx configuration.
- A new canonical log is moved into evidence. A changed pre-existing canonical log is copied and left installed without an ambiguity issue. An unchanged or missing canonical log cannot satisfy the run.
- Those canonical overwrite/current-run semantics require the private validated logging proof; public `collect_boot_evidence(...)` remains conservative because it has no `AppendLog = false` proof.
- `_RetainedBootEvidence` and its pinned file descriptors remain authoritative for final markers and errors before and after fsync.
- Keep structural live failures separate from byte-derived marker/error literals, and collect the union of final deltas with every stable regular or unsafe live-observed failure identity.
- Preserve no-follow/nonblocking opens, bounded log reads, exact config restoration, exact launcher and app guards, process-group cleanup, evidence ownership handoffs, and exclusive JSON publication ordering.
- Use strict TDD: add each behavioral regression, run it against the task base and record the intended RED failure, then make the minimum production change and record GREEN.
- The frozen task-base SHA-256 of `src/ssr_env/oracle_boot.py` is `1dcc2023dcb539aab77beb6087126bd91baf42d8d874d676bc9521e408dfe2ca`.
- The realistic 17-line retained `LogOutput.log` fixture SHA-256 is `de73d88a30498e6e00f5fe4071f5acd757e77256adcd9eab391389f1dc272848`.

---

### Task 1: Classify monitored logs and map authentic marker text

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:27-45,287-302,564-571,790-1210`
- Modify: `tests/test_oracle_boot.py:24-40,959-1180,1390-1490,5868-5950`
- Create: `tests/fixtures/oracle_boot/BepInEx-LogOutput-5.4.23.5.log`

**Interfaces:**
- Produces: `_boot_log_kind(relative_path: Path) -> str | None`, returning only `"canonical"`, `"fallback"`, `"preloader"`, or `None`.
- Produces: `_ScannedLog.kind: str`; `_LogScan` continues to own every directory handle borrowed by its entries.
- Produces: `_BOOT_MARKER_PATTERNS: dict[str, bytes]`, keyed by the three unchanged public marker identifiers.
- Preserves: `_is_preloader_log(path)` as the recursive basename rule and every public fingerprint/collection signature.
- Consumed by Tasks 3-5 for family-specific observation, transfer, and retained-byte grading.

- [ ] **Step 1: Freeze the task base and install the authentic fixture**

Record the source hash before editing:

```bash
shasum -a 256 src/ssr_env/oracle_boot.py
```

Require exactly:

```text
1dcc2023dcb539aab77beb6087126bd91baf42d8d874d676bc9521e408dfe2ca  src/ssr_env/oracle_boot.py
```

Create the tracked fixture with these exact LF-terminated lines:

```text
[Message:   BepInEx] BepInEx 5.4.23.5 - Sausage (03/28/2026 18:41:22)
[Info   :   BepInEx] Running under Unity vUnknown (post-2017)
[Info   :   BepInEx] CLR runtime version: 2.0.50727.1433
[Info   :   BepInEx] Supports SRE: True
[Info   :   BepInEx] System platform: Bits64, MacOS
[Message:   BepInEx] Preloader started
[Info   :   BepInEx] Loaded 1 patcher method from [BepInEx.Preloader 5.4.23.5]
[Info   :   BepInEx] 1 patcher plugin loaded
[Info   :   BepInEx] Patching [UnityEngine.CoreModule] with [BepInEx.Chainloader]
[Message:   BepInEx] Preloader finished
[Info   :   BepInEx] Detected Unity version: v2018.4.25f1
[Message:   BepInEx] Chainloader ready
[Message:   BepInEx] Chainloader started
[Info   :   BepInEx] 1 plugin to load
[Info   :   BepInEx] Loading [SSR Executable Oracle 0.1.0]
[Info   :SSR Executable Oracle] SSR oracle boot probe loaded
[Message:   BepInEx] Chainloader startup complete
```

Verify its exact provenance hash:

```bash
shasum -a 256 tests/fixtures/oracle_boot/BepInEx-LogOutput-5.4.23.5.log
```

- [ ] **Step 2: Extend the test harness without changing existing defaults**

Extend `_launcher(...)` with:

```python
log_relative: str = "nested/preloader_probe.log",
additional_logs: tuple[tuple[str, str], ...] = (),
```

Construct `log = root / log_relative`, create its parent, and write each additional `(relative, text)` pair through the generated launcher. Extend `_probe_layout(...)` to return:

```python
bepinex=game / "BepInEx"
bepinex_config=game / "BepInEx/config/BepInEx.cfg"
canonical_log=game / "BepInEx/LogOutput.log"
fallback_logs=tuple(game / f"BepInEx/LogOutput.log.{index}" for index in range(1, 5))
```

Create `BepInEx/config` in the layout, but leave `BepInEx.cfg` absent so pinned defaults remain the normal test state. Keep `_launcher`'s old preloader default until Task 5 migrates success tests.

- [ ] **Step 3: Write RED classification and authentic-marker tests**

Add table-driven tests with hand-written expected kinds for these relative paths:

```python
{
    Path("BepInEx/LogOutput.log"): "canonical",
    Path("BepInEx/LogOutput.log.1"): "fallback",
    Path("BepInEx/LogOutput.log.4"): "fallback",
    Path("preloader_root.log"): "preloader",
    Path("nested/preloader_failure.log"): "preloader",
    Path("BepInEx/logoutput.log"): None,
    Path("BepInEx/LogOutput.log.0"): None,
    Path("BepInEx/LogOutput.log.5"): None,
    Path("BepInEx/nested/LogOutput.log"): None,
    Path("preloader_wrong.LOG"): None,
}
```

Extend the recursive fingerprint test so canonical and `.1`/`.4` files appear in the exact sorted fingerprint tuple and lookalikes do not. Extend unsafe-path tests so symlink/FIFO canonical and fallback candidates fail before blocking. Add a crafted canonical `LogFingerprint` to `_validate_baseline(...)` and require acceptance.

Add a marker test that loads the tracked fixture as bytes and expects:

```python
tuple(
    marker
    for marker in REQUIRED_MARKERS
    if oracle_boot._payload_contains_boot_marker(payload, marker)
) == REQUIRED_MARKERS
```

Also require all three of these payloads to reject the public Unity marker:

```python
b"Unity v2018.4.25f1"
b"Detected Unity version: v2018.4.25f10"
b"Detected Unity version: xv2018.4.25f1"
```

- [ ] **Step 4: Run RED and confirm the intended failures**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'boot_log_kind or fingerprint_logs or unsafe_monitored or authentic_unity_marker or realistic_log_framing'
```

Require failures because canonical/fallback files are not classified, a canonical baseline name is rejected, and the authentic Unity line is not mapped. A fixture-path typo or setup error is not an acceptable RED.

- [ ] **Step 5: Implement the minimal classifier and marker mapping**

Add exact relative constants and classifier:

```python
_CANONICAL_BOOT_LOG = Path("BepInEx/LogOutput.log")
_FALLBACK_BOOT_LOGS = frozenset(
    Path(f"BepInEx/LogOutput.log.{index}") for index in range(1, 5)
)
_BOOT_MARKER_PATTERNS = {
    "BepInEx 5.4.23.5": b"BepInEx 5.4.23.5",
    "Unity v2018.4.25f1": b"Detected Unity version: v2018.4.25f1",
    "SSR oracle boot probe loaded": b"SSR oracle boot probe loaded",
}

def _boot_log_kind(relative_path: Path) -> str | None:
    if relative_path == _CANONICAL_BOOT_LOG:
        return "canonical"
    if relative_path in _FALLBACK_BOOT_LOGS:
        return "fallback"
    if _is_preloader_log(relative_path):
        return "preloader"
    return None
```

Have the recursive scanner derive `relative_path = candidate.relative_to(game)` once, append only classified entries, and store `kind`. Generalize internal error text from “preloader log” to “monitored boot log” where the operation now covers all families. Validate baselines with `_boot_log_kind(path.relative_to(game_root)) is not None`.

Update `_payload_contains_boot_marker(...)` to search `_BOOT_MARKER_PATTERNS[marker]`; keep token-boundary checks for both version identifiers using the matched authentic pattern's start/end.

- [ ] **Step 6: Run GREEN, focused legacy tests, and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'boot_log_kind or fingerprint_logs or unsafe or baseline or extended_version or realistic_log_framing or authentic_unity_marker'
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py \
  tests/fixtures/oracle_boot/BepInEx-LogOutput-5.4.23.5.log
git commit -m "feat: classify canonical oracle boot logs"
```

### Task 2: Pin and revalidate the BepInEx logging contracts

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:180-242,1478-1744,4325-4580`
- Modify: `tests/test_oracle_boot.py:959-1210,5213-5355,6244-6378,6799-7024`

**Interfaces:**
- Produces: `_DiskLoggingConfigGuard(bepinex_path, bepinex, config, path, name, fd, original)` where `bepinex` is the retained BepInEx directory, `config` is an optional retained config-directory handle, and `original: _ConfigSnapshot | None`; absent handles/snapshot record the exact missing component chain.
- Produces: frozen `_ValidatedBootLogContract(canonical_overwrite: bool)`; only `_verify_and_close_bepinex_disk_logging_guard(...)` may return the `canonical_overwrite=True` proof used by controlled collection.
- Produces: `_parse_bepinex_disk_logging(payload: bytes, path: Path) -> None`; valid input returns `None`, all rejected input raises `BootProbeError`.
- Produces: `_open_bepinex_disk_logging_guard(game_root: Path) -> _DiskLoggingConfigGuard` and `_verify_and_close_bepinex_disk_logging_guard(guard) -> _ValidatedBootLogContract`.
- Integrates: `run_boot_probe` owns the guard from before preliminary log fingerprinting through its final prelaunch recheck, then consumes/closes it before the authoritative inventory and `Popen`.
- Preserves: mutable oracle `_ConfigGuard` and its restoration behavior unchanged.

- [ ] **Step 1: Write RED parser acceptance tests**

Use literal payloads and require acceptance for:

```python
b"[Logging.Disk]\nEnabled = true\nAppendLog = false\nLogLevels = Fatal, Error, Warning, Message, Info\n"
b"\xef\xbb\xbf [Logging.Disk] \r\n Enabled = TRUE \r\n AppendLog = False \r\n LogLevels = All \r\n"
b"[Other]\nValue = okay\n[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=debug,info,message,warning,error,fatal\n"
b"[Logging.Console]\nLogLevels = Fatal, Error, Warning, Message, Info\n[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=All\n"
b"[Logging.Console]\nOther = value\n[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=All\n"
```

The BOM fixture must place the BOM immediately before the first textual character; outer whitespace begins after the optional BOM. Test both an absent `BepInEx.cfg` under an existing config directory and an absent `BepInEx/config` directory. The first guard has `config is not None`/`original is None`; the second has `config is None`/`original is None`.

- [ ] **Step 2: Write RED rejection tables**

Parameterize explicit disk payloads for: `Enabled=false`; `AppendLog=true`; only `Message, Info`; missing each required disk key; duplicate disk section; duplicate relevant disk key; lowercase or whitespace-lookalike section/key; unknown/numeric/duplicate level; `None`; `All, Debug`; NUL; invalid UTF-8; a second/embedded BOM; bare CR; inline `#`; malformed non-comment line; and internal section-name whitespace.

Parameterize console payloads for a configured `LogLevels` missing each required level, duplicate console section/key, `None`, `All, Debug`, and case-fold/whitespace lookalikes. Prove that `LogLevels` under exact `[Logging.Console]` is not counted as the required disk key and vice versa; a realistic generated file containing both sections is valid.

Every case must raise `BootProbeError` containing the BepInEx config path. Add no-follow tests for symlink/FIFO config entries and a symlinked config parent.

- [ ] **Step 3: Write RED pre-`Popen` identity tests**

Use a forbidden `Popen` replacement that increments a counter and raises. Cover:

1. accepted existing config content changed to `AppendLog = true` after preliminary preflight;
2. accepted config replaced by a same-byte new inode;
3. initially absent config created with invalid content;
4. initially absent config created with valid content;
5. initially absent config directory created before the boundary;
6. accepted config's directory or BepInEx parent path replaced while retained handles remain open.

Trigger each mutation at the last existing guard verification immediately before `Popen`. Require `Popen` count zero, exact oracle-config bytes/mode restored, no process PID files, and no canonical `probe.json`.

- [ ] **Step 4: Run RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py -k 'bepinex_disk_config'
```

Require parser-symbol failures and forbidden-launch failures because current production ignores `BepInEx.cfg`.

- [ ] **Step 5: Implement the strict parser**

Decode strict UTF-8 after removing at most one leading UTF-8 BOM. Reject NUL and reject any `\r` remaining after replacing `\r\n` with `\n`. For each normalized line:

```python
trimmed = line.strip()
if not trimmed or trimmed.startswith("#"):
    continue
if "#" in trimmed:
    reject_inline_comment()
if trimmed.startswith("[") or trimmed.endswith("]"):
    parse_one_complete_section_line()
else:
    parse_one_key_value_line()
```

Reject incomplete/malformed section syntax and key lines without exactly one nonempty key before the first `=`. Track exact relevant section/key counts. For relevant-name lookalikes, compare `re.sub(r"\s+", "", name).casefold()` with the exact target after trimming; reject a lookalike rather than ignoring it. Ignore unrelated well-formed sections and keys.

For `LogLevels`, split on commas, trim, casefold, require uniqueness, and accept either the singleton `all` or a subset of `{fatal,error,warning,message,info,debug}` containing `{fatal,error,warning,message,info}`. Count disk keys only while the current exact section is `[Logging.Disk]`; count the console key only inside exact `[Logging.Console]`. Require exactly one disk section and all three disk keys. Permit no console section or one console section with zero/one `LogLevels`; absence uses pinned defaults.

- [ ] **Step 6: Implement retained absent/present guard ownership**

Open `game_root / "BepInEx"` with `_open_absolute_directory`. Inspect `config` with `follow_symlinks=False`. If absent, retain only the BepInEx handle and record both downstream components absent. If present, require a directory and retain an `_open_child_directory` handle; then inspect `BepInEx.cfg`. On leaf absence retain both directory handles with `fd = -1`/`original = None`. On presence, require a regular file, open `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, read twice through `_read_config_snapshot`, parse it, and transfer all ownership into the guard. Any error except exact `ENOENT` is not absence.

On recheck, first verify the absolute BepInEx path against its retained handle. If `config` was absent, its name must remain absent. If present, verify both its public name and retained handle identity. An initially absent leaf must still be absent; any appearance is a guarded-state change, even if the new bytes are valid. An initially present leaf must retain the same named and descriptor identity, exact bytes, mode, size, and mtime; parse the reread bytes again.

After successful revalidation, close the file descriptor, config-directory handle, and BepInEx handle independently. Return `_ValidatedBootLogContract(canonical_overwrite=True)` only after every close succeeds; a close failure prevents launch. The guard is consumed and must not be verified, restored, or closed again after `Popen`.

- [ ] **Step 7: Integrate guard lifecycle and run GREEN**

Open the logging guard after the oracle `_ConfigGuard` and before preliminary boot-log fingerprinting. Recheck and consume it after ordinary preflight plus launcher/oracle-config guard checks, then close it before the authoritative boot-log snapshot and `Popen`. If an earlier path returns or raises, close the still-owned guard in `finally`; never restore its bytes and never perform a post-launch BepInEx-config check.

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py -k 'bepinex_disk_config or guard_opener or launches_exact_argv or initial_non_off_config'
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "feat: pin BepInEx disk logging config"
```

### Task 3: Make live observation family-specific and persistent

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:189-205,1025-1158`
- Modify: `tests/test_oracle_boot.py:1328-1390,5472-5950,8158-8207`

**Interfaces:**
- Produces: `_ObservedFailureLog(relative_path: Path, kind: str, device: int, inode: int, mode: int)` for stable regular and unsafe `preloader`/`fallback` observations.
- Extends: private `_MonitorOutcome` with `issues: tuple[str, ...]` and `observed_failures: tuple[_ObservedFailureLog, ...]`; `errors` remains byte-literal observations that final retained bytes replace.
- Changes: `_observe_boot_logs(...) -> tuple[markers, errors, issues, observed_failures]` using tuples in each position.
- Changes: `_wait_for_markers(...)` accumulates the first stable identity of every observed failure/fallback path and includes it in every return state.
- Consumed by Task 4's collector and Task 5's `run_boot_probe` integration.

- [ ] **Step 1: Write RED canonical-only live-marker tests**

Create controlled scans where:

- the canonical log contains the tracked fixture and produces all three public markers;
- three preloader/fallback payloads split the three markers and produce no success markers;
- a changed canonical log contains one marker while a preloader log contains the other two, producing only the canonical marker;
- an unchanged pre-existing canonical log containing all markers produces no markers;
- canonical error text is reported even before all markers arrive.

Use real temporary files and production scanning; mock only time/process polling where a bounded wait is required.

- [ ] **Step 2: Write RED observed-failure tests**

Require any new or changed `preloader_*.log` and any numbered fallback to return monitor state `error` without needing an error literal. Assert its stable relative path/kind/device/inode/mode appears in `outcome.observed_failures` and its family-level reason appears in `outcome.issues`, not as an invented byte error.

Add a wait test where a stable failure is observed and then removed or inode-replaced during process cleanup; the returned outcome must retain the first observation. Add stable symlink/FIFO/special observations and require records without opening them. Add a transient-read test proving an unstable regular-file scan is retried and never recorded as stable evidence.

- [ ] **Step 3: Run RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'canonical_live_marker or markers_same_canonical or observed_failure or fallback_log_monitor or monitor_error'
```

Require failures because current monitoring merges markers across all changed preloader payloads and has no persistent failure record.

- [ ] **Step 4: Implement canonical-only observation**

Build the baseline by path. For each stable new/changed regular entry:

- `canonical`: read its bytes, derive markers from that payload only, and search it for error literals;
- `fallback` or `preloader`: read for error literals, add a family-specific structural issue unconditionally, and emit the complete relative-path/kind/lstat identity record;
- unsafe classified `fallback`/`preloader` entries: add a family/type structural issue and emit the same complete identity record without opening it;
- unsafe canonical entries: add a structural canonical/type issue without treating them as success or failure-family evidence.

Return markers in `_REQUIRED_BOOT_MARKERS` order, byte-derived errors in configured-literal order, structural issues in deterministic path/family order, and observed records sorted by game-relative path.

- [ ] **Step 5: Accumulate exact stable identities in `_wait_for_markers`**

Maintain `observed_by_path: dict[Path, _ObservedFailureLog]`. On the first record for a relative path, retain it. If a later stable observation for that path has another kind/device/inode/mode, add `observed failure log identity changed during monitoring: PATH` to structural issues and retain the first identity. Preserve the accumulated tuple and structural issues through `markers`, `error`, `timeout`, and `early_exit` returns, including final retry-at-exit/deadline paths.

Update direct `_MonitorOutcome(...)` test fixtures with `issues=()` and `observed_failures=()`; do not alter any public dataclass test. Final run integration may replace live markers/literal errors from retained bytes, but it must never discard structural issues.

- [ ] **Step 6: Run GREEN and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'canonical_live_marker or markers_same_canonical or observed_failure or fallback_log_monitor or monitor_error or marker_error_and_exit'
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "feat: observe canonical boot log failures"
```

### Task 4: Grade and preserve family-specific durable evidence

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:1206-1273,2183-3077`
- Modify: `tests/test_oracle_boot.py:1491-2420,3915-4310,5524-6133,7441-8170,8528-8597`

**Interfaces:**
- Produces: `_BootLogInventoryEntry(path, relative_path, kind, file_type, device, inode, mode, size, mtime_ns, fingerprint)` where `fingerprint` is present only for a stable regular file, plus `_BootLogInventory(entries)` with a deterministic `regular_fingerprints` tuple.
- Produces: `_capture_boot_log_inventory(game_root: Path) -> _BootLogInventory`; it lstat-records unsafe classified entries without opening them and fingerprints regular entries with the existing stable descriptor routine.
- Extends private collector:

```python
_collect_boot_evidence_retained(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_root: Path,
    *,
    expected_inventory: _BootLogInventory | None,
    run_contract: _ValidatedBootLogContract | None = None,
    observed_failures: tuple[_ObservedFailureLog, ...] = (),
) -> _RetainedBootEvidence
```

- Preserves public `collect_boot_evidence(before, game_root, evidence_root) -> BootEvidence` exactly and delegates with `expected_inventory=None`, `run_contract=None`, and `observed_failures=()`.
- Produces retained `_EvidenceDecision` whose markers come only from retained `BepInEx/LogOutput.log` bytes and whose errors span every retained monitored file.
- Consumed by Task 5's run integration.

- [ ] **Step 1: Write RED family-specific transfer tests**

Obtain `run_contract` through a real successful
`_verify_and_close_bepinex_disk_logging_guard(...)` call against pinned-default
or valid explicit configuration, then cover these literal outcomes:

| Baseline → final | Transfer | Installed path | Required issue |
|---|---|---|---|
| canonical absent → new | move | absent | none from change itself |
| canonical present → changed | copy | present | none from change itself |
| canonical present → unchanged | none | present | `current canonical boot log is missing or unchanged` |
| preloader/fallback absent → new | move | absent | family-specific failure |
| preloader/fallback present → changed | copy | present | family-specific failure |
| preloader/fallback present → unchanged | none | present | none from baseline history |

Use exact relative evidence paths. Require a changed canonical log not to receive `pre-existing preloader log changed` or any replacement ambiguity wording.

Add a public-collector regression with the same changed canonical path but no private run contract. Require the existing conservative changed-log issue and no `current canonical` requirement; the public helper has no overwrite proof.

- [ ] **Step 2: Write RED retained-byte decision tests**

Create retained evidence containing:

1. the authentic canonical fixture: all three unchanged public markers;
2. split markers across canonical and failure logs: only canonical-contained markers;
3. error literals appended to canonical during shutdown: error returned from final retained bytes;
4. marker-bearing fallback without canonical: zero success markers plus fallback issue;
5. extended authentic-looking versions: rejected.

Mutate retained evidence between decision capture and fsync using existing descriptor-pressure helpers and require the existing fail-closed verification errors.

- [ ] **Step 3: Write RED unpreservable-observation tests**

Pass an `_ObservedFailureLog` captured before final collection, then separately remove it, replace its inode, substitute a symlink/FIFO, begin with a stably observed unsafe entry, and leave a regular same inode with later bytes. The unsafe/unavailable cases must add:

```text
observed failure log could not be preserved: PATH
```

The same-inode later-byte case must preserve and grade the exact final bytes rather than rejecting harmless completion of the already observed file. Add a changed pre-existing failure log that is observed and then restored to the baseline bytes/metadata on the same inode; collection must still copy its final bytes and retain the live family-level failure.

- [ ] **Step 4: Run RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'canonical_log_collection or canonical_retained_decision or observed_failure_preservation or fallback_log_collection'
```

- [ ] **Step 5: Implement family-specific collection**

Generalize baseline and inventory wording to “monitored boot log.” Capture every final classified lstat entry in `_BootLogInventory`, opening only regular files. If `expected_inventory` is supplied, re-scan and compare the complete path/kind/type/identity set plus every regular fingerprint before any transfer.

Classify every final entry by `entry.kind`. Compute new/changed paths and union them with every same-identity live-observed regular failure path, then:

- transfer new paths with the existing exclusive move helper;
- transfer changed paths with the existing exclusive copy helper;
- add failure issues for every new/changed `preloader` or `fallback` path;
- record a `canonical_current` flag only for a successfully fingerprinted new/changed canonical path under a non-`None` validated run contract;
- add the exact missing/unchanged canonical issue when `canonical_current` is false only under that validated run contract;
- keep missing/unsafe baseline and post-shutdown inventory mismatches fail-closed.

Validate each `observed_failures` record as game-relative, normalized, uniquely pathed, and classified exactly as its recorded `preloader`/`fallback` kind. Compare its kind/device/inode/mode with the final inventory. If absent, unsafe, replaced, or unretainable, append the unpreservable issue. Do not require size/mtime/hash equality for a still-regular matching inode. Force a same-identity observed regular path into move/copy selection even when its final fingerprint equals the baseline.

Without a run contract, retain the existing conservative changed-log issue for any changed pre-existing monitored file and do not require a canonical current-run log. With the validated overwrite proof, suppress that generic issue only for changed canonical and apply the family-specific/current-canonical rules above.

- [ ] **Step 6: Grade exact retained families**

In `_capture_retained_evidence_decision`, map each retained file's `relative_path` through `_boot_log_kind`. Derive all success markers from the single canonical payload only. Derive `_BOOT_ERROR_MARKERS` across every retained payload. Reject an impossible retained path kind as `BootProbeError` rather than silently grading it.

Keep the before-fsync and after-fsync decision comparisons unchanged so path, bytes, fingerprints, markers, and errors remain pinned.

- [ ] **Step 7: Run GREEN, legacy evidence tests, and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'collect or retained_evidence or evidence_inventory or canonical_log or fallback_log or observed_failure_preservation'
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "feat: retain canonical oracle boot evidence"
```

### Task 5: Reconcile the launch baseline and migrate end-to-end probe tests

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:4197-4580`
- Modify: `tests/test_oracle_boot.py:959-1210,5213-6133,6244-8398,8598-9338`

**Interfaces:**
- Consumes: Tasks 1-4 classifiers, logging guard, observed failure ledger, and collector keyword.
- Preserves: `run_boot_probe(game_root, launcher, config, evidence_root, timeout_seconds)` and all CLI/schema-v1 outputs.
- Produces: the second complete fingerprint immediately before `Popen` as the authoritative `before_logs`, live-monitor baseline, collector baseline, and serialized baseline; config/inventory boundary rejection raises `BootProbeError` before evidence allocation.

- [ ] **Step 1: Write RED immediate-baseline reconciliation tests**

After the preliminary fingerprint but before the final launch boundary, separately add, modify, remove, and inode-replace a canonical/fallback/preloader file. Require zero `Popen` calls and `BootProbeError` text containing:

```text
monitored boot log inventory changed during preflight
```

Require exact oracle-config restoration, no evidence directory allocation/transfer, and no canonical success JSON. Add the CLI boundary case and require its existing probe-error exit/status behavior without stdout JSON. Also prove identical preliminary/second inventories launch normally and that the second tuple—not a recomputed third baseline—is passed to `_wait_for_markers`, collector, and `probe.json.before_logs`.

- [ ] **Step 2: Migrate success-oriented launcher tests to authentic canonical output**

Change `_launcher`'s default `log_relative` to `"BepInEx/LogOutput.log"`. For tests whose purpose is a preloader/fallback failure, pass an explicit family path. Update expected moved/copied paths in success tests to `BepInEx/LogOutput.log` and load the realistic fixture for ordinary successful launch payloads.

Do not mechanically replace low-level transfer tests: those that explicitly exercise preloader failure behavior must retain their preloader fixtures.

- [ ] **Step 3: Add end-to-end authentic success and stale-log regressions**

Run `run_boot_probe` with the tracked fixture written to a new canonical log and require success, exact public markers, canonical moved evidence, healthy cleanup, config restoration, and schema version 1.

Run with a pre-existing canonical file and overwrite it during launch; require copy evidence, the installed final file preserved, and success without ambiguity issue. Run with an unchanged stale marker-bearing canonical file and require failure. Run with `AppendLog = true` plus stale markers and require zero launch.

- [ ] **Step 4: Wire the production sequence**

Use these names and ordering in `run_boot_probe`:

```python
preliminary_logs = fingerprint_preloader_logs(game)
preflight = _capture_boot_snapshot(game)
# existing snapshot issues and retained guard checks
run_contract = _verify_and_close_bepinex_disk_logging_guard(
    disk_logging_guard
)
disk_logging_guard = None
before_logs = fingerprint_preloader_logs(game)
if before_logs != preliminary_logs:
    raise BootProbeError(
        "monitored boot log inventory changed during preflight"
    )
process = subprocess.Popen(...)
monitor_outcome = _wait_for_markers(process, game, before_logs, timeout)
```

After cleanup, capture `after_inventory = _capture_boot_log_inventory(game)` and serialize only `after_inventory.regular_fingerprints` as `after_logs`. Pass `before_logs`, the complete `after_inventory`, `run_contract`, and `monitor_outcome.observed_failures` into `_collect_boot_evidence_retained`.

Construct the final outcome using markers and literal errors from `retained.decision`, structural issues from the live monitor plus `BootEvidence.issues`, and the live outcome state/exit code. Deduplicate identical structural strings without reordering first occurrence. A failure-family/unsafe/identity issue must prevent success even when live payload bytes disappear; do not replace it with the vague unspecified-error fallback.

- [ ] **Step 5: Preserve exact schema-v1 and lifecycle ordering**

Update independent schema fixtures to canonical paths but retain the exact JSON field set and marker values. Preserve ordering:

```text
process cleanup
post-cleanup inventory
evidence transfer and retained-byte decision
postflight
oracle-config restore
all guards close
retained evidence fsync/revalidation
exclusive probe.json publication
```

Extend ordering tests so the disk-logging guard closes exactly once and no launch/evidence publication survives an acquisition-boundary interruption.

- [ ] **Step 6: Run the complete boot module and commit**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "fix: observe canonical BepInEx boot output"
```

### Task 6: Update the reviewed runbook and implementation status

**Files:**
- Modify: `oracle/README.md:12-31,320-380,519-590`
- Modify: `docs/superpowers/plans/2026-07-27-executable-oracle.md:525-555,1280-1320`
- Modify: `docs/superpowers/specs/2026-07-30-oracle-canonical-boot-log-design.md:1-8,430-485`

**Interfaces:**
- Documents only behavior implemented and verified by Tasks 1-5.
- Keeps every deploy/launch command behind separate approval; this task does not make the transactional launch section generally runnable.

- [ ] **Step 1: Update the runbook's observer contract**

Document the exact monitored families, authentic Unity source line versus stable public marker, canonical-only success rule, failure-family behavior, strict `BepInEx.cfg` subset, two-snapshot prelaunch reconciliation, and new-versus-changed canonical evidence treatment.

Replace the obsolete “known-broken observer” stop text with a gate that states the observer is implemented and offline-tested but has not been exercised by a corrected second game launch. Require a fresh read-only preflight, explicit approval, installer-only deployment, exactly one corrected bounded probe, and verified official restore before any command in the mutation section is used.

- [ ] **Step 2: Record implementation status without claiming runtime success**

Mark the canonical observer design as implemented and offline-verified, with corrected launch validation pending. Update the executable-oracle plan's observed Task 2 result to explain that the first boot succeeded at runtime but the old observer missed `BepInEx/LogOutput.log`, and that the implementation now derives public `Unity v2018.4.25f1` from exact authentic source text.

Do not claim a second deployment, game launch, end-to-end pass, or installed plugin change.

- [ ] **Step 3: Run consistency searches and commit**

```bash
rg -n 'known-broken observer|preloader_\*\.log.*success|Unity v2018\.4\.25f1.*literal|second launch.*occurred' \
  oracle/README.md \
  docs/superpowers/plans/2026-07-27-executable-oracle.md \
  docs/superpowers/specs/2026-07-30-oracle-canonical-boot-log-design.md
git diff --check
git add oracle/README.md \
  docs/superpowers/plans/2026-07-27-executable-oracle.md \
  docs/superpowers/specs/2026-07-30-oracle-canonical-boot-log-design.md
git commit -m "docs: describe canonical boot observer rollout"
```

### Task 7: Run offline acceptance verification

**Files:**
- Verify only; no planned production changes.

**Interfaces:**
- Consumes the complete branch.
- Produces exact test, source-scope, fixture-hash, schema, and installed-state evidence for final independent review.

- [ ] **Step 1: Verify the focused observer and adjacent oracle cohorts**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install.py \
  tests/test_oracle_install_compat.py \
  tests/test_oracle_compat.py
```

- [ ] **Step 2: Verify the repository and Python compilation**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q src tools tests
git diff --check origin/main...HEAD
```

Only the already documented practical-model XPASS cases and expected failures are acceptable.

- [ ] **Step 3: Verify fixture, public surface, and tracked scope**

```bash
shasum -a 256 tests/fixtures/oracle_boot/BepInEx-LogOutput-5.4.23.5.log
git diff --name-status origin/main...HEAD
git status --short --branch
```

Require fixture hash `de73d88a30498e6e00f5fe4071f5acd757e77256adcd9eab391389f1dc272848`. The only untracked setup artifact permitted is the worktree-local `data/decompiled` link; ignored `.venv`, `data/levels`, and `data/oracle/compat` fixtures must not enter the branch.

- [ ] **Step 4: Verify installed state read-only**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py status \
  --game-root "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
```

Require healthy `official` preloader state. Do not deploy, repair, restore, or launch.

- [ ] **Step 5: Commit only if verification required a documentation-only correction**

If every command passes without a tracked correction, make no commit. If an exact test/result count in documentation required correction, rerun its covering command, stage only that document, and use:

```bash
git commit -m "docs: record canonical observer verification"
```
