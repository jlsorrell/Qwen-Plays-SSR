# SSR Oracle Practical Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Task 8 with a controlled SSR boot probe that is fail-closed, reversible, bounded, and reliable on the approved practical local-machine threat model.

**Architecture:** Keep the existing single Python module and public records, but replace the ambient collector handoff with a private retained-evidence transaction used by `run_boot_probe`. The transaction owns the allocated directory and exact collected log descriptors through cleanup and final evidence validation, then transfers the exact directory identity to the staged JSON publisher and closes before the canonical name appears. Existing publication machinery remains responsible for exclusive `probe.json` creation and gains one bounded best-effort quarantine path for reachable post-rename reconciliation failures.

**Tech Stack:** Python 3.12, pytest 8, POSIX descriptor-relative filesystem APIs, macOS `renameatx_np` through the existing `_renameatx` wrapper, `subprocess.Popen(start_new_session=True)`, uv.

## Global Constraints

- The authoritative scope is `docs/superpowers/specs/2026-07-29-oracle-practical-threat-model-design.md`.
- No hostile process concurrently rewrites the Steam game directory, oracle evidence directory, launcher, configuration hierarchy, or repository while a probe is running.
- The operating system and the current user account are trusted.
- Ordinary accidental changes remain in scope: Steam updates, unexpected prior artifacts, symlinks or special files, hung children, identity changes, short I/O, and ordinary I/O failures.
- A single asynchronous interruption is in scope; repeated uncatchable interruption and forced PID/PGID reuse are not.
- Keep `LogFingerprint.file_type`; it is part of the approved safety contract.
- Keep `collect_boot_evidence(before, game_root, evidence_root) -> BootEvidence` public with exactly three arguments.
- Rename the public `run_boot_probe` keywords to `launcher` and `config` without changing positional order.
- Open a file with `O_NOFOLLOW | O_NONBLOCK` before deciding that it is regular.
- Restore and verify the retained original configuration inode before reporting a replacement public path, and never write through the replacement path.
- Derive final boot markers and error literals from the exact bytes retained as evidence.
- Perform one final monitored-log inventory scan after evidence-directory allocation and before transfer; do not add endless rescanning intended to defeat an active writer.
- Retain collected-file descriptors through final validation/fsync, and carry the allocated evidence-directory identity through publication with a duplicated staged-publication handle.
- Immediately before publication, revalidate the exact evidence tree and bytes, fsync collected files, fsync evidence directories child-first, and fsync the evidence root last.
- On a caught post-rename reconciliation failure, quarantine a reachable canonical `probe.json` through the retained directory with mode `0600`; do not promise success against a process racing every rename.
- Launch with an argument vector, `shell=False`, and a distinct session; do not search by process name.
- Retry process cleanup once after the first caught interruption, preserve the first exception, and attach cleanup uncertainty as a note.
- During failure cleanup, if the first configuration-restoration attempt is interrupted by a non-`Exception` `BaseException`, retry restoration exactly once through the still-open retained descriptor, then preserve the first interruption.
- Relative CLI paths, including the evidence root, resolve against the caller's working directory.
- Do not add a supervisor, pidfd emulation, descriptor-native launcher execution, a shell launch, or defenses for deliberate final-syscall path replacement.
- Do not launch the game or mutate the installed game during Task 8.
- Preserve owner-local `.DS_Store`, the modified original executable-oracle plan, `data/decompiled`, `oracle/README.md`, and `oracle/plugin/`.
- Task 8's code boundary is exactly `src/ssr_env/oracle_boot.py`, `tests/test_oracle_boot.py`, and `tools/oracle_boot_probe.py`.
- Keep cohort work unstaged and uncommitted. After final practical-model review, make one Task 8 code commit: `feat: add controlled oracle boot probe`.
- Every missing-behavior regression must be observed failing against the frozen pre-repair source snapshot created in Task 0. CLI path and wrapper-exit tests characterize behavior that is already correct and therefore begin green.

---

## File Map

- `src/ssr_env/oracle_boot.py`: public boot-probe API, safe preflight, config guard, process cleanup, retained log collection, evidence validation, result construction, and exclusive JSON publication.
- `tests/test_oracle_boot.py`: all Task 8 unit, integration, descriptor-lifecycle, process-group, CLI, and publication regressions.
- `tools/oracle_boot_probe.py`: intentionally thin executable wrapper; expected to remain behaviorally unchanged while new subprocess coverage locks its exit propagation.
- `docs/superpowers/specs/2026-07-29-oracle-practical-threat-model-design.md`: approved contract used by every cohort reviewer.
- `docs/superpowers/plans/2026-07-29-oracle-practical-hardening.md`: this execution plan; committed separately before Task 8 implementation.

---

### Task 0: Capture the Frozen Pre-Repair Source

**Files:**
- Read: `src/ssr_env/`
- Create outside the repository: `/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src/ssr_env/`

**Interfaces:**
- Consumes: the reviewed pre-repair `src/ssr_env/oracle_boot.py` whose SHA-256 is `ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f`.
- Produces: a read-only-by-convention import snapshot selected by `PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src`.

- [ ] **Step 1: Verify the frozen source hash before any production edit**

Run:

```bash
shasum -a 256 src/ssr_env/oracle_boot.py
```

Expected:

```text
ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f  src/ssr_env/oracle_boot.py
```

- [ ] **Step 2: Copy the complete package needed by frozen imports**

If the exact destination does not exist, run:

```bash
mkdir -p /private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src
cp -R src/ssr_env /private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src/
```

If it already exists, do not overwrite it; verify Step 3 and stop if the hash differs.

- [ ] **Step 3: Prove later RED commands import the snapshot**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache \
  uv run python -c 'import hashlib, pathlib, ssr_env.oracle_boot as m; p = pathlib.Path(m.__file__); print(p); print(hashlib.sha256(p.read_bytes()).hexdigest())'
```

Expected output ends with:

```text
/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src/ssr_env/oracle_boot.py
ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f
```

Do not edit, stage, or commit the snapshot.

---

### Task 1A: Nonblocking Hashing and Shared Test Helpers

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:387-434`
- Modify: `src/ssr_env/oracle_boot.py:522-547`
- Modify: `tests/test_oracle_boot.py:1-56`
- Modify: `tests/test_oracle_boot.py:830-890`

**Interfaces:**
- Consumes: `_DirectoryHandle`, `_stat_identity`, and the existing test helpers.
- Produces:
  - `_sha256_file(path: Path) -> str` with an `O_NONBLOCK` target open
  - direct test imports from `ssr_env.oracle_boot`, without import-time RED scaffolding
  - `_exception_graph(root: BaseException) -> tuple[BaseException, ...]`
  - `_assert_no_canonical_probe_json(*roots: Path) -> None`

- [ ] **Step 1: Replace obsolete import scaffolding and add exact test helpers**

Use direct imports and one shared exception-graph helper:

```python
from ssr_env import oracle_boot
from ssr_env.oracle_boot import (
    collect_boot_evidence,
    fingerprint_preloader_logs,
    run_boot_probe,
)


def _exception_graph(root: BaseException) -> tuple[BaseException, ...]:
    pending = [root]
    observed: list[BaseException] = []
    while pending:
        current = pending.pop()
        if any(current is candidate for candidate in observed):
            continue
        observed.append(current)
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return tuple(observed)


def _assert_no_canonical_probe_json(*roots: Path) -> None:
    for root in roots:
        if root.exists():
            assert tuple(root.rglob("probe.json")) == ()
```

Replace cleanup/integrity uses of `_assert_no_success_probe_json` with `_assert_no_canonical_probe_json`. Keep ordinary unsuccessful-probe tests that explicitly require a canonical `{"success": false}` payload.

- [ ] **Step 2: Write the failing hash-open regression**

```python
def test_sha256_file_opens_hash_target_nonblocking_before_type_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / "Assembly-CSharp.dll"
    target.write_bytes(b"reviewed bytes")
    original_open = os.open
    matching_flags: list[int] = []

    def checked_open(path, flags, *args, **kwargs):
        if path == target.name and kwargs.get("dir_fd") is not None:
            matching_flags.append(flags)
            assert flags & os.O_NOFOLLOW
            assert flags & os.O_NONBLOCK
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, open=checked_open),
        raising=False,
    )

    assert oracle_boot._sha256_file(target) == hashlib.sha256(
        b"reviewed bytes"
    ).hexdigest()
    assert matching_flags
```

- [ ] **Step 3: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'sha256_file_opens_hash_target_nonblocking_before_type_validation'
```

Expected: the assertion fails because the frozen source omits `O_NONBLOCK`.

- [ ] **Step 4: Implement nonblocking hashing**

```python
descriptor = os.open(
    requested.name,
    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
    dir_fd=parent.fd,
)
```

While working in `_open_absolute_directory`, remove its unused local `current_path`; this is housekeeping, not a correctness gate.

- [ ] **Step 5: Run the hashing cohort gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'sha256_file or preflight'
```

Expected: all selected tests pass. Review this cohort before starting Task 1B. Do not stage or commit.

---

### Task 1B: Descriptor-First Configuration Restoration

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:1205-1439`
- Modify: `tests/test_oracle_boot.py:3172-3457`

**Interfaces:**
- Consumes: `_ConfigGuard`, `_ConfigSnapshot`, `_stat_identity`, and `_verify_current_config_path_identity`.
- Produces: `_read_retained_config_snapshot(descriptor: int, path: Path) -> _ConfigSnapshot`.

- [ ] **Step 1: Write the failing descriptor-first restoration regressions**

Parameterize leaf and parent displacement. Open a real guard, mutate its retained file, displace the public name, install a sentinel replacement, and close only after assertions:

```python
@pytest.mark.parametrize("displacement", ["leaf", "parent"])
def test_restore_config_guard_repairs_retained_inode_before_public_path_error(
    displacement: str,
    tmp_path: Path,
):
    parent = tmp_path / "config"
    parent.mkdir()
    config = parent / "oracle.cfg"
    config.write_bytes(ORIGINAL_CONFIG)
    config.chmod(0o640)
    guard = oracle_boot._open_config_guard(config)
    displaced = tmp_path / f"displaced-{displacement}"
    replacement_payload = b"replacement must remain untouched\n"

    try:
        os.lseek(guard.fd, 0, os.SEEK_SET)
        os.ftruncate(guard.fd, 0)
        os.write(guard.fd, b"mutated retained config\n")
        os.fchmod(guard.fd, 0o600)
        if displacement == "leaf":
            config.rename(displaced)
            config.write_bytes(replacement_payload)
        else:
            parent.rename(displaced)
            parent.mkdir()
            (parent / config.name).write_bytes(replacement_payload)

        with pytest.raises(
            oracle_boot.BootProbeError,
            match="identity changed|parent identity changed",
        ):
            oracle_boot._restore_config_guard(guard)

        retained_path = (
            displaced if displacement == "leaf" else displaced / config.name
        )
        assert retained_path.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(retained_path.stat().st_mode) == 0o640
        assert (parent / config.name).read_bytes() == replacement_payload
    finally:
        guard.close()
```

- [ ] **Step 2: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'restore_config_guard_repairs_retained_inode_before_public_path_error'
```

Expected: both cases show that the retained original is not repaired before the frozen source reports the public-path identity error.

- [ ] **Step 3: Implement descriptor-only reading and restore before path verification**

`_read_retained_config_snapshot` performs the existing two-pass read and retained `fstat` stability checks but never calls `os.stat` on the public name:

```python
def _read_retained_config_snapshot(
    descriptor: int,
    path: Path,
) -> _ConfigSnapshot:
    payloads: list[bytes] = []
    expected_identity: tuple[int, int, int, int, int] | None = None
    for _ in range(2):
        os.lseek(descriptor, 0, os.SEEK_SET)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise BootProbeError(f"config is not a regular file: {path}")
        payload = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload.extend(chunk)
        after = os.fstat(descriptor)
        identity = _stat_identity(before)
        if (
            _stat_identity(after) != identity
            or len(payload) != before.st_size
            or (
                expected_identity is not None
                and identity != expected_identity
            )
        ):
            raise BootProbeError(f"config changed while being read: {path}")
        expected_identity = identity
        payloads.append(bytes(payload))
    if payloads[0] != payloads[1]:
        raise BootProbeError(f"config content was unstable while reading: {path}")
    observed = os.fstat(descriptor)
    if expected_identity is None or _stat_identity(observed) != expected_identity:
        raise BootProbeError(f"config changed after being read: {path}")
    return _ConfigSnapshot(
        payload=payloads[0],
        mode=stat.S_IMODE(observed.st_mode),
        device=observed.st_dev,
        inode=observed.st_ino,
        size=observed.st_size,
    )
```

Keep `_read_config_snapshot` as the public-name-binding wrapper used at open/use time. In `_restore_config_guard`, call the descriptor-only reader, restore bytes/mode, fsync and reread the retained descriptor, fsync `guard.parent.fd`, and only then call `_verify_current_config_path_identity(guard)`.

- [ ] **Step 4: Run the restoration cohort gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'restore_config_guard or config_snapshot or config_guard'
```

Expected: all selected tests pass. Review this cohort before starting Task 1C. Do not stage or commit.

---

### Task 1C: Public API and CLI Boundaries

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:2813-2835`
- Modify: `src/ssr_env/oracle_boot.py:2995-3020`
- Modify: `tests/test_oracle_boot.py:4427-4684`
- Verify only: `tools/oracle_boot_probe.py`

**Interfaces:**
- Consumes: the existing five positional `run_boot_probe` arguments and `main(argv)`.
- Produces: `run_boot_probe(game_root: Path, launcher: Path, config: Path, evidence_root: Path, timeout_seconds: int) -> BootProbeResult`.

- [ ] **Step 1: Write a failing real keyword-call regression**

Exercise Python's actual call binding and stop at the validation boundary:

```python
def test_run_boot_probe_accepts_documented_launcher_and_config_keywords(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    launcher = tmp_path / "launcher"
    config = tmp_path / "config"
    evidence = tmp_path / "evidence"
    captured: list[tuple[Path, Path, Path, Path, int]] = []

    class StopAtValidation(RuntimeError):
        pass

    def capture_validation(
        game_root,
        launcher_argument,
        config_argument,
        evidence_root,
        timeout_seconds,
    ):
        captured.append(
            (
                game_root,
                launcher_argument,
                config_argument,
                evidence_root,
                timeout_seconds,
            )
        )
        raise StopAtValidation("keyword binding reached validation")

    monkeypatch.setattr(
        oracle_boot,
        "_validate_probe_request",
        capture_validation,
    )

    with pytest.raises(
        StopAtValidation,
        match="keyword binding reached validation",
    ):
        run_boot_probe(
            game_root=game,
            launcher=launcher,
            config=config,
            evidence_root=evidence,
            timeout_seconds=7,
        )

    assert captured == [(game, launcher, config, evidence, 7)]
```

- [ ] **Step 2: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'run_boot_probe_accepts_documented_launcher_and_config_keywords'
```

Expected: the frozen source raises `TypeError` for the unexpected `launcher` keyword before validation is reached.

- [ ] **Step 3: Implement the documented public keywords**

```python
def run_boot_probe(
    game_root: Path,
    launcher: Path,
    config: Path,
    evidence_root: Path,
    timeout_seconds: int,
) -> BootProbeResult:
    game, launcher_path, config_path, evidence, timeout = (
        _validate_probe_request(
            game_root,
            launcher,
            config,
            evidence_root,
            timeout_seconds,
        )
    )
```

Use `launcher_path` and `config_path` only as validated local names inside the body. Preserve positional order.

- [ ] **Step 4: Add green characterization coverage for relative CLI resolution and wrapper exit propagation**

```python
def test_boot_main_resolves_relative_evidence_root_from_caller_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    caller = tmp_path / "caller"
    caller.mkdir()
    captured: list[Path] = []
    result = _complete_boot_probe_result(tmp_path, success=False)

    def fake_probe(_game, _launcher, _config, evidence, _timeout):
        captured.append(evidence)
        return result

    monkeypatch.chdir(caller)
    monkeypatch.setattr(oracle_boot, "run_boot_probe", fake_probe)
    exit_code = oracle_boot.main(
        [
            "--game-root", ".",
            "--launcher", "launcher",
            "--config", "config",
            "--evidence-root", "data/oracle/boot-probe",
            "--timeout", "2",
        ]
    )

    assert exit_code == 1
    assert captured == [(caller / "data/oracle/boot-probe").resolve()]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("returned", [1, 2])
def test_oracle_boot_probe_wrapper_propagates_returned_exit_status(
    returned: int,
    tmp_path: Path,
):
    shadow = tmp_path / "shadow/ssr_env"
    shadow.mkdir(parents=True)
    (shadow / "__init__.py").write_text("", encoding="utf-8")
    (shadow / "oracle_boot.py").write_text(
        f"def main():\n    return {returned}\n",
        encoding="utf-8",
    )
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "tools/oracle_boot_probe.py"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(shadow.parent)

    completed = subprocess.run(
        [sys.executable, str(wrapper)],
        cwd=repo_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert completed.returncode == returned
```

These tests characterize behavior that is already correct; they must remain green before and after the API rename.

- [ ] **Step 5: Run the API/CLI cohort gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'run_boot_probe_accepts_documented or boot_main_resolves_relative or wrapper_propagates_returned'
```

Expected: all selected tests pass. Review this cohort before starting Task 2. Do not stage or commit.

---

### Task 2: One-Interruption Process Cleanup

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:1654-1721`
- Modify: `src/ssr_env/oracle_boot.py:3048-3074`
- Modify: `tests/test_oracle_boot.py:2617-3170`
- Modify: `tests/test_oracle_boot.py:4687-4910`

**Interfaces:**
- Consumes:
  - `_stop_unretained_spawned_process(process: subprocess.Popen[bytes]) -> None`
  - `_stop_spawned_process_group(process: subprocess.Popen[bytes], pgid: int) -> int | None`
- Produces:
  - `_cleanup_spawned_process(process: subprocess.Popen[bytes], pgid: int | None) -> int | None`
  - exactly one retry after the first `BaseException`
  - the first exception remains top-level; a failed retry is attached with `_note_later_error`

- [ ] **Step 1: Write the failing single-interruption cleanup regressions**

```python
@pytest.mark.parametrize(
    "pgid",
    [None, 424242],
    ids=["unretained-child", "retained-group"],
)
def test_cleanup_spawned_process_retries_once_and_preserves_interrupt(
    pgid: int | None,
    monkeypatch: pytest.MonkeyPatch,
):
    process = SimpleNamespace(pid=424242)
    calls = 0

    def interrupted_then_stopped(*args):
        nonlocal calls
        assert args == ((process,) if pgid is None else (process, pgid))
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt("single interruption")
        return None

    monkeypatch.setattr(
        oracle_boot,
        (
            "_stop_unretained_spawned_process"
            if pgid is None
            else "_stop_spawned_process_group"
        ),
        interrupted_then_stopped,
    )

    with pytest.raises(KeyboardInterrupt, match="single interruption"):
        oracle_boot._cleanup_spawned_process(process, pgid)
    assert calls == 2


@pytest.mark.parametrize(
    "pgid",
    [None, 424242],
    ids=["unretained-child", "retained-group"],
)
def test_cleanup_spawned_process_notes_retry_uncertainty_on_primary_interrupt(
    pgid: int | None,
    monkeypatch: pytest.MonkeyPatch,
):
    process = SimpleNamespace(pid=424242)
    failures = iter(
        (
            KeyboardInterrupt("primary interruption"),
            oracle_boot.BootProbeError("cleanup remains uncertain"),
        )
    )
    monkeypatch.setattr(
        oracle_boot,
        (
            "_stop_unretained_spawned_process"
            if pgid is None
            else "_stop_spawned_process_group"
        ),
        lambda *_args: (_ for _ in ()).throw(next(failures)),
    )

    with pytest.raises(KeyboardInterrupt) as raised:
        oracle_boot._cleanup_spawned_process(process, pgid)
    assert any(
        "cleanup retry also failed" in note
        and "cleanup remains uncertain" in note
        for note in getattr(raised.value, "__notes__", ())
    )


def test_probe_retries_group_cleanup_after_one_keyboard_interrupt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=b"mutated before interrupted cleanup\n",
    )
    original_stop = oracle_boot._stop_spawned_process_group
    calls = 0

    def interrupt_once_then_stop(process, pgid):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt("single cleanup interruption")
        return original_stop(process, pgid)

    monkeypatch.setattr(
        oracle_boot,
        "_stop_spawned_process_group",
        interrupt_once_then_stop,
    )

    with pytest.raises(KeyboardInterrupt, match="single cleanup interruption"):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    assert calls == 2
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_no_canonical_probe_json(layout.evidence)
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)
```

- [ ] **Step 2: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'cleanup_spawned_process_retries_once or cleanup_spawned_process_notes_retry or retries_group_cleanup_after_one_keyboard_interrupt'
```

Expected: the unit tests fail because `_cleanup_spawned_process` does not exist, and the run-level case makes only one interrupted cleanup attempt on the frozen source.

- [ ] **Step 3: Implement one bounded retry and route `run_boot_probe` through it**

```python
def _cleanup_spawned_process(
    process: subprocess.Popen[bytes],
    pgid: int | None,
) -> int | None:
    def stop() -> int | None:
        if pgid is None:
            _stop_unretained_spawned_process(process)
            return None
        return _stop_spawned_process_group(process, pgid)

    try:
        return stop()
    except BaseException as primary:
        try:
            stop()
        except BaseException as retry_error:
            _note_later_error(
                primary,
                "spawned process cleanup retry also failed",
                retry_error,
            )
        raise
```

Replace the two cleanup branches in the launch `finally` with:

```python
if process is not None:
    cleanup_exit_code = _cleanup_spawned_process(process, spawned_pgid)
```

Do not alter the numeric PGID strategy or add a third attempt.

- [ ] **Step 4: Run the process-control regression gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'cleanup_spawned_process or process_group or distinct_session or exact_child_handle or full_group_grace or term_to_kill'
```

Expected: all selected tests pass and no controlled process group survives fixture teardown. Do not stage or commit.

---

### Task 3: Retained Collector and Final Allocation-Boundary Inventory

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:88-103`
- Modify: `src/ssr_env/oracle_boot.py:137-244`
- Modify: `src/ssr_env/oracle_boot.py:1017-1194`
- Modify: `src/ssr_env/oracle_boot.py:1724-2087`
- Modify: `src/ssr_env/oracle_boot.py:2451-2582`
- Modify: `tests/test_oracle_boot.py:993-1356`
- Modify: `tests/test_oracle_boot.py:3606-3971`

**Interfaces:**
- Consumes: `BootEvidence`, `_DirectoryHandle`, `_ScannedLog`, `LogFingerprint`, `_allocate_evidence_directory`, `_make_evidence_parents`, `_post_shutdown_inventory_mismatches`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class _EvidenceDirectoryIdentity:
    relative_path: Path
    device: int
    inode: int


@dataclass(slots=True)
class _RetainedEvidenceFile:
    relative_path: Path
    descriptor: int
    identity: tuple[int, int, int, int, int]
    fingerprint: LogFingerprint

    def close(self) -> None:
        if self.descriptor >= 0:
            descriptor = self.descriptor
            self.descriptor = -1
            os.close(descriptor)


@dataclass(frozen=True, slots=True)
class _EvidenceDecision:
    markers: tuple[str, ...]
    errors: tuple[str, ...]
    fingerprints: tuple[LogFingerprint, ...]


@dataclass(slots=True)
class _RetainedBootEvidence:
    public: BootEvidence
    directory_handle: _DirectoryHandle
    files: tuple[_RetainedEvidenceFile, ...]
    directories: tuple[_EvidenceDirectoryIdentity, ...]
    decision: _EvidenceDecision | None = None

    def close(self) -> None:
        primary: BaseException | None = None
        for item in reversed(self.files):
            try:
                item.close()
            except BaseException as exc:
                if primary is None:
                    primary = exc
                else:
                    _note_later_error(
                        primary,
                        "retained evidence file close also failed",
                        exc,
                    )
        try:
            self.directory_handle.close()
        except BaseException as exc:
            if primary is None:
                primary = exc
            else:
                _note_later_error(
                    primary,
                    "retained evidence directory close also failed",
                    exc,
                )
        if primary is not None:
            raise primary
```

The remaining exact signatures are:

```text
_duplicate_directory_handle(handle: _DirectoryHandle) -> _DirectoryHandle
_collect_boot_evidence_retained(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_root: Path,
    *,
    expected_inventory: tuple[LogFingerprint, ...] | None,
) -> _RetainedBootEvidence
```

- [ ] **Step 1: Write the failing allocation-boundary inventory regressions**

Inject exactly once after `_allocate_evidence_directory` returns and before transfer:

```python
@pytest.mark.parametrize("mutation", ["added", "changed", "removed"])
def test_probe_rechecks_expected_inventory_after_evidence_allocation(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    baseline = layout.game / "existing/preloader_baseline.log"
    baseline.parent.mkdir()
    baseline.write_bytes(b"stable baseline")
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    original_allocate = oracle_boot._allocate_evidence_directory
    injected = False

    def allocate_then_mutate(*args, **kwargs):
        nonlocal injected
        result = original_allocate(*args, **kwargs)
        assert not injected
        injected = True
        if mutation == "added":
            (layout.game / "preloader_late.log").write_bytes(b"late")
        elif mutation == "changed":
            baseline.write_bytes(b"changed after allocation")
        else:
            baseline.rename(tmp_path / "removed.log")
        return result

    monkeypatch.setattr(
        oracle_boot,
        "_allocate_evidence_directory",
        allocate_then_mutate,
    )

    with pytest.raises(oracle_boot.BootProbeError, match="inventory"):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    assert injected
    _assert_no_canonical_probe_json(layout.evidence)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)
```

- [ ] **Step 2: Write the failing retained ownership regression**

```python
def test_collect_retained_evidence_keeps_exact_files_open_until_close(
    tmp_path: Path,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "nested/preloader_probe.log"
    source.parent.mkdir()
    source.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)

    retained = oracle_boot._collect_boot_evidence_retained(
        (),
        game,
        tmp_path / "evidence",
        expected_inventory=expected,
    )
    descriptors = (
        retained.directory_handle.fd,
        *(item.descriptor for item in retained.files),
    )
    try:
        assert len(retained.files) == 1
        assert retained.files[0].relative_path == Path(
            "nested/preloader_probe.log"
        )
        assert all(os.fstat(descriptor) for descriptor in descriptors)
    finally:
        retained.close()
    for descriptor in descriptors:
        with pytest.raises(OSError) as raised:
            os.fstat(descriptor)
        assert raised.value.errno == errno.EBADF


def test_collect_retained_evidence_closes_partial_transfer_ownership(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    for name in ("preloader_one.log", "preloader_two.log"):
        (game / name).write_text(
            "\n".join(REQUIRED_MARKERS),
            encoding="utf-8",
        )
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    original_allocate = oracle_boot._allocate_evidence_directory
    original_move = oracle_boot._move_regular_exclusive
    allocated_directory_fd = -1
    retained_file_fds: list[int] = []
    move_calls = 0

    class InjectedSecondTransferError(OSError):
        pass

    def capture_allocation(*args, **kwargs):
        nonlocal allocated_directory_fd
        evidence_dir, handle = original_allocate(*args, **kwargs)
        allocated_directory_fd = handle.fd
        return evidence_dir, handle

    def fail_second_transfer(*args, **kwargs):
        nonlocal move_calls
        move_calls += 1
        if move_calls == 2:
            raise InjectedSecondTransferError("second transfer failed")
        retained_file = original_move(*args, **kwargs)
        retained_file_fds.append(retained_file.descriptor)
        return retained_file

    monkeypatch.setattr(
        oracle_boot,
        "_allocate_evidence_directory",
        capture_allocation,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_move_regular_exclusive",
        fail_second_transfer,
    )

    with pytest.raises(
        InjectedSecondTransferError,
        match="second transfer failed",
    ):
        oracle_boot._collect_boot_evidence_retained(
            (),
            game,
            tmp_path / "evidence",
            expected_inventory=expected,
        )

    assert move_calls == 2
    assert len(retained_file_fds) == 1
    assert allocated_directory_fd >= 0
    for descriptor in (*retained_file_fds, allocated_directory_fd):
        with pytest.raises(OSError) as raised:
            os.fstat(descriptor)
        assert raised.value.errno == errno.EBADF
    _assert_no_canonical_probe_json(tmp_path / "evidence")
```

- [ ] **Step 3: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'rechecks_expected_inventory_after_evidence_allocation or collect_retained_evidence'
```

Expected: the run-level cases fail because the frozen source accepts an added or mutated non-transfer log after its only inventory comparison; ownership tests fail because the private retained collector does not exist.

- [ ] **Step 4: Make transfer functions return retained exact files**

Change both signatures:

```text
_copy_regular_exclusive(
    entry: _ScannedLog,
    destination_parent: _DirectoryHandle,
    destination_name: str,
    destination_path: Path,
    expected: LogFingerprint,
) -> _RetainedEvidenceFile

_move_regular_exclusive(
    entry: _ScannedLog,
    destination_parent: _DirectoryHandle,
    destination_name: str,
    destination_path: Path,
    expected: LogFingerprint,
) -> _RetainedEvidenceFile
```

For a copy, initialize `destination_descriptor = -1`, open the exact `O_RDWR` destination, and transfer ownership only after its size/hash/named identity checks pass. For a move, open `source_descriptor` with `O_RDWR | O_NOFOLLOW | O_NONBLOCK` and transfer that exact descriptor after the exclusive rename and moved-name checks pass; the probe never writes through it, but the writable descriptor makes the required final `fsync` well-defined. Each returned record uses a destination-relative path, the descriptor's full `_stat_identity`, and a destination-path `LogFingerprint`.

Both success paths assign the owned descriptor to a local `transferred_descriptor`, set the original local to `-1`, and return the record. Both `finally` blocks use an integer guard:

```python
if destination_descriptor >= 0:
    os.close(destination_descriptor)

if source_descriptor >= 0:
    os.close(source_descriptor)
```

Do not retain the copy path's current `None` sentinel or the move path's unconditional `os.close(source_descriptor)`.

- [ ] **Step 5: Implement the private collector with one final scan after allocation**

The order is fixed:

1. Open `initial_scan = _scan_preloader_logs(game)`, fingerprint its regular entries, record unsafe-entry issues, and close it in `finally`.
2. Allocate `evidence_dir, evidence_handle = _allocate_evidence_directory(evidence, evidence_exists)`.
3. Open `final_scan = _scan_preloader_logs(game)` and rebuild `final_regular`, `final_entries`, `final_paths`, and final unsafe-entry issues from only this scan.
4. When `expected_inventory is not None`, validate it with `_validate_baseline`, call `_post_shutdown_inventory_mismatches(expected, final_regular, final_paths)`, and raise `BootProbeError("; ".join(mismatches))` before the first transfer when nonempty.
5. Classify new and changed logs by comparing `final_regular` to the validated `before` baseline.
6. Pass the matching `_ScannedLog` from `final_entries` to `_move_regular_exclusive` or `_copy_regular_exclusive`.
7. Close `final_scan` in `finally` after every transfer has either completed or raised.

Convert `known_evidence_directories` to sorted `_EvidenceDirectoryIdentity` records relative to `evidence_dir`, representing the root itself as `Path(".")`. On every exception, close all retained file descriptors and the evidence directory, retaining the first error and adding close failures as notes.

At the end, construct:

```python
public = BootEvidence(
    evidence_dir=evidence_dir,
    moved_logs=tuple(moved_logs),
    copied_logs=tuple(copied_logs),
    issues=tuple(issues),
)
retained = _RetainedBootEvidence(
    public=public,
    directory_handle=evidence_handle,
    files=tuple(retained_files),
    directories=directory_identities,
)
return retained
```

`_RetainedBootEvidence` is non-frozen and leaves `decision=None` until Task 4 derives it from retained bytes. Do not use a `ContextVar`.

- [ ] **Step 6: Preserve the public three-argument collector**

```python
def collect_boot_evidence(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_root: Path,
) -> BootEvidence:
    retained = _collect_boot_evidence_retained(
        before,
        game_root,
        evidence_root,
        expected_inventory=None,
    )
    try:
        return retained.public
    finally:
        retained.close()
```

Task 4 adds final decision capture and verification to this wrapper. Remove `_EXPECTED_COLLECTOR_INVENTORY` after `run_boot_probe` switches to the private collector in Task 5.

- [ ] **Step 7: Extend staging to duplicate an already-retained directory**

```python
def _stage_probe_json(
    evidence_dir: Path,
    payload: dict[str, Any],
    *,
    _directory_handle: _DirectoryHandle | None = None,
) -> _StagedProbeJson:
    directory = _requested_path(evidence_dir, "evidence directory")
    if _directory_handle is None:
        directory = _validate_directory(directory, "evidence directory")
        directory_handle = _open_absolute_directory(
            directory,
            "evidence directory",
        )
    else:
        if _directory_handle.path != directory:
            raise BootProbeError(
                f"retained evidence directory does not match {directory}"
            )
        _verify_pinned_directory_path(
            directory,
            _directory_handle,
            "evidence directory before probe JSON staging",
        )
        directory_handle = _duplicate_directory_handle(_directory_handle)
```

Implement exact duplication as:

```python
def _duplicate_directory_handle(
    handle: _DirectoryHandle,
) -> _DirectoryHandle:
    duplicate = _opened_directory(os.dup(handle.fd), handle.path)
    if (duplicate.device, duplicate.inode) != (
        handle.device,
        handle.inode,
    ):
        duplicate.close()
        raise BootProbeError(
            f"retained directory changed while duplicating: {handle.path}"
        )
    return duplicate
```

Keep `_write_probe_json`'s existing `_staged`-only private extension. The retained directory is consumed only by `_stage_probe_json`; the run lifecycle later passes the resulting `_StagedProbeJson` to `_write_probe_json`.

- [ ] **Step 8: Run the collector gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'collect_ or evidence_source_open or inventory_change_after_shutdown'
```

Expected: all selected tests pass; public collector callers still receive `BootEvidence`, and all private ownership tests prove exact close behavior. Do not stage or commit.

---

### Task 4: Preserved-Byte Decision and Evidence Durability

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:718-837`
- Modify: `src/ssr_env/oracle_boot.py:1724-2087`
- Modify: `src/ssr_env/oracle_boot.py:2936-2994`
- Modify: `tests/test_oracle_boot.py:892-1083`
- Modify: `tests/test_oracle_boot.py:2177-2464`
- Modify: `tests/test_oracle_boot.py:3606-3971`

**Interfaces:**
- Consumes: `_RetainedBootEvidence`, `_RetainedEvidenceFile`, `_EvidenceDecision`, `_payload_contains_boot_marker`, `_REQUIRED_BOOT_MARKERS`, `_BOOT_ERROR_MARKERS`, `_MAX_MONITOR_LOG_BYTES`.
- Produces:
  - `_read_retained_evidence_file(retained: _RetainedBootEvidence, item: _RetainedEvidenceFile) -> tuple[bytes, LogFingerprint]`
  - `_capture_retained_evidence_decision(retained: _RetainedBootEvidence) -> _EvidenceDecision`
  - `_open_verified_evidence_directories(retained: _RetainedBootEvidence) -> tuple[_DirectoryHandle, ...]`
  - `_verify_and_sync_retained_evidence(retained: _RetainedBootEvidence) -> None`
  - an exact descriptor-root tree comparison against `retained.files` and `retained.directories`

- [ ] **Step 1: Write the failing preserved-byte grading regression**

Inject an error after the current final path scan but before the current `after_logs` snapshot:

```python
def test_probe_grades_late_error_from_exact_preserved_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    original_fingerprint = oracle_boot._fingerprint_regular_preloader_logs
    injected = False

    def append_error_then_fingerprint(game):
        nonlocal injected
        log = game / "nested/preloader_probe.log"
        if log.exists() and not injected:
            log.write_text(
                log.read_text(encoding="utf-8")
                + "\nDllNotFoundException: after stale scan\n",
                encoding="utf-8",
            )
            injected = True
        return original_fingerprint(game)

    monkeypatch.setattr(
        oracle_boot,
        "_fingerprint_regular_preloader_logs",
        append_error_then_fingerprint,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert injected
    assert result.success is False
    assert any("DllNotFoundException" in issue for issue in result.issues)
    preserved = result.evidence_dir / "nested/preloader_probe.log"
    assert "after stale scan" in preserved.read_text(encoding="utf-8")
```

- [ ] **Step 2: Write failing exact-tree, byte-change, and fsync-order tests**

Use the private collector to obtain a retained transaction, then mutate only before final verification:

```python
@pytest.mark.parametrize(
    "mutation",
    [
        "bytes",
        "extra-entry",
        "missing-name",
        "missing-directory",
        "fifo-leaf",
        "symlink-directory",
    ],
)
def test_verify_retained_evidence_rejects_final_tree_or_byte_change(
    mutation: str,
    tmp_path: Path,
):
    game = tmp_path / "game"
    game.mkdir()
    log = game / "nested/preloader_probe.log"
    log.parent.mkdir()
    log.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    retained = oracle_boot._collect_boot_evidence_retained(
        (),
        game,
        tmp_path / "evidence",
        expected_inventory=expected,
    )
    try:
        preserved = (
            retained.public.evidence_dir
            / retained.files[0].relative_path
        )
        if mutation == "bytes":
            preserved.write_bytes(preserved.read_bytes() + b"\nchanged")
        elif mutation == "extra-entry":
            (retained.public.evidence_dir / "unexpected.keep").write_bytes(
                b"unexpected"
            )
        elif mutation == "missing-name":
            preserved.rename(tmp_path / "missing-name.log")
        elif mutation == "missing-directory":
            preserved.parent.rename(tmp_path / "missing-directory")
        elif mutation == "fifo-leaf":
            preserved.rename(tmp_path / "fifo-original.log")
            os.mkfifo(preserved, 0o600)
        else:
            preserved.parent.rename(tmp_path / "symlink-directory")
            preserved.parent.symlink_to(
                tmp_path / "symlink-directory",
                target_is_directory=True,
            )
        with pytest.raises(oracle_boot.BootProbeError):
            oracle_boot._verify_and_sync_retained_evidence(retained)
    finally:
        retained.close()


def test_verify_retained_evidence_fsyncs_files_before_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    log = game / "nested/preloader_probe.log"
    log.parent.mkdir()
    log.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    retained = oracle_boot._collect_boot_evidence_retained(
        (),
        game,
        tmp_path / "evidence",
        expected_inventory=expected,
    )
    file_identities = {
        (os.fstat(item.descriptor).st_dev, os.fstat(item.descriptor).st_ino)
        for item in retained.files
    }
    directory_identities = {
        (item.device, item.inode): item.relative_path
        for item in retained.directories
    }
    events: list[tuple[str, Path | None]] = []
    original_fsync = os.fsync

    def tracked_fsync(descriptor: int) -> None:
        observed = os.fstat(descriptor)
        identity = (observed.st_dev, observed.st_ino)
        if identity in file_identities:
            events.append(("file", None))
        elif identity in directory_identities:
            events.append(("directory", directory_identities[identity]))
        original_fsync(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=tracked_fsync),
        raising=False,
    )
    try:
        oracle_boot._verify_and_sync_retained_evidence(retained)
    finally:
        retained.close()

    file_indexes = [
        index for index, event in enumerate(events) if event[0] == "file"
    ]
    directory_indexes = [
        index for index, event in enumerate(events)
        if event[0] == "directory"
    ]
    assert file_indexes
    assert directory_indexes
    assert max(file_indexes) < min(directory_indexes)
    assert events[-1] == ("directory", Path("."))


def test_public_collector_preserves_verification_error_over_close_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    log = game / "nested/preloader_probe.log"
    log.parent.mkdir()
    log.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
    retained = oracle_boot._collect_boot_evidence_retained(
        (),
        game,
        tmp_path / "evidence",
        expected_inventory=None,
    )
    descriptors = (
        retained.directory_handle.fd,
        *(item.descriptor for item in retained.files),
    )
    original_close = oracle_boot._RetainedBootEvidence.close

    class PrimaryEvidenceError(OSError):
        pass

    class RetainedCloseError(OSError):
        pass

    def close_then_raise(candidate):
        original_close(candidate)
        raise RetainedCloseError("close failed after releasing descriptors")

    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        lambda *_args, **_kwargs: retained,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_verify_and_sync_retained_evidence",
        lambda *_args: (_ for _ in ()).throw(
            PrimaryEvidenceError("primary verification failure")
        ),
    )
    monkeypatch.setattr(
        oracle_boot._RetainedBootEvidence,
        "close",
        close_then_raise,
    )

    with pytest.raises(
        PrimaryEvidenceError,
        match="primary verification failure",
    ) as raised:
        collect_boot_evidence((), game, tmp_path / "unused")

    assert any(
        "retained boot evidence close also failed" in note
        and "close failed after releasing descriptors" in note
        for note in getattr(raised.value, "__notes__", ())
    )
    for descriptor in descriptors:
        with pytest.raises(OSError) as closed:
            os.fstat(descriptor)
        assert closed.value.errno == errno.EBADF


def test_evidence_inventory_error_survives_scan_handle_close_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    log = game / "nested/preloader_probe.log"
    log.parent.mkdir()
    log.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    retained = oracle_boot._collect_boot_evidence_retained(
        (),
        game,
        tmp_path / "evidence",
        expected_inventory=expected,
    )
    (retained.public.evidence_dir / "unexpected.keep").write_bytes(
        b"unexpected"
    )
    original_close = oracle_boot._DirectoryHandle.close
    closed_child_fd = -1

    class ScanCloseError(OSError):
        pass

    def close_child_then_raise(handle):
        nonlocal closed_child_fd
        is_scanned_child = (
            handle.path
            == retained.public.evidence_dir / "nested"
        )
        descriptor = handle.fd
        original_close(handle)
        if is_scanned_child:
            closed_child_fd = descriptor
            raise ScanCloseError("temporary scan handle close failed")

    monkeypatch.setattr(
        oracle_boot._DirectoryHandle,
        "close",
        close_child_then_raise,
    )
    try:
        with pytest.raises(
            oracle_boot.BootProbeError,
            match="inventory changed",
        ) as raised:
            oracle_boot._verify_and_sync_retained_evidence(retained)

        assert any(
            "tree scan handle close also failed" in note
            and "temporary scan handle close failed" in note
            for note in getattr(raised.value, "__notes__", ())
        )
        assert closed_child_fd >= 0
        with pytest.raises(OSError) as closed:
            os.fstat(closed_child_fd)
        assert closed.value.errno == errno.EBADF
    finally:
        retained.close()
```

- [ ] **Step 3: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'probe_grades_late_error_from_exact_preserved_bytes or verify_retained_evidence or public_collector_preserves_verification_error or evidence_inventory_error_survives_scan_handle_close_failure'
```

Expected: the run-level test incorrectly returns success on the frozen source, and every private retention/verification test fails because those APIs do not exist.

- [ ] **Step 4: Implement descriptor-based evidence reads and decisions**

```python
def _read_retained_evidence_file(
    retained: _RetainedBootEvidence,
    item: _RetainedEvidenceFile,
) -> tuple[bytes, LogFingerprint]:
    path = retained.public.evidence_dir / item.relative_path
    before = os.fstat(item.descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or _stat_identity(before) != item.identity
        or before.st_size > _MAX_MONITOR_LOG_BYTES
    ):
        raise BootProbeError(
            f"retained preloader evidence changed: {path}"
        )
    os.lseek(item.descriptor, 0, os.SEEK_SET)
    payload = bytearray()
    digest = hashlib.sha256()
    while True:
        chunk = os.read(item.descriptor, 1024 * 1024)
        if not chunk:
            break
        payload.extend(chunk)
        if len(payload) > _MAX_MONITOR_LOG_BYTES:
            raise BootProbeError(
                f"retained preloader evidence exceeds byte limit: {path}"
            )
        digest.update(chunk)
    after = os.fstat(item.descriptor)
    if (
        _stat_identity(after) != item.identity
        or len(payload) != before.st_size
    ):
        raise BootProbeError(
            f"retained preloader evidence was unstable: {path}"
        )
    fingerprint = LogFingerprint(
        path=path,
        file_type="regular",
        inode=before.st_ino,
        size=before.st_size,
        mtime_ns=before.st_mtime_ns,
        sha256=digest.hexdigest(),
    )
    if fingerprint != item.fingerprint:
        raise BootProbeError(
            f"retained preloader evidence fingerprint changed: {path}"
        )
    return bytes(payload), fingerprint


def _capture_retained_evidence_decision(
    retained: _RetainedBootEvidence,
) -> _EvidenceDecision:
    payloads: list[bytes] = []
    fingerprints: list[LogFingerprint] = []
    for item in retained.files:
        payload, fingerprint = _read_retained_evidence_file(
            retained,
            item,
        )
        payloads.append(payload)
        fingerprints.append(fingerprint)
    return _EvidenceDecision(
        markers=tuple(
            marker
            for marker in _REQUIRED_BOOT_MARKERS
            if any(
                _payload_contains_boot_marker(payload, marker)
                for payload in payloads
            )
        ),
        errors=tuple(
            marker
            for marker in _BOOT_ERROR_MARKERS
            if any(
                marker.encode("ascii") in payload
                for payload in payloads
            )
        ),
        fingerprints=tuple(fingerprints),
    )
```

- [ ] **Step 5: Store the exact decision and make the public collector verify before close**

At the end of `_collect_boot_evidence_retained`, after all ownership has been assembled:

```python
retained = _RetainedBootEvidence(
    public=public,
    directory_handle=evidence_handle,
    files=tuple(retained_files),
    directories=directory_identities,
)
retained.decision = _capture_retained_evidence_decision(retained)
return retained
```

Update the public collector without allowing close failure to replace a verification failure:

```python
retained = _collect_boot_evidence_retained(
    before,
    game_root,
    evidence_root,
    expected_inventory=None,
)
public = retained.public
primary: BaseException | None = None
try:
    _verify_and_sync_retained_evidence(retained)
except BaseException as exc:
    primary = exc
try:
    retained.close()
except BaseException as close_error:
    if primary is None:
        raise
    _note_later_error(
        primary,
        "retained boot evidence close also failed",
        close_error,
    )
if primary is not None:
    raise primary
return public
```

- [ ] **Step 6: Implement exact evidence-tree verification and durability**

```python
def _open_verified_evidence_directories(
    retained: _RetainedBootEvidence,
) -> tuple[_DirectoryHandle, ...]:
    expected_directories = {
        item.relative_path: (item.device, item.inode)
        for item in retained.directories
    }
    expected_files = {
        item.relative_path: item.identity
        for item in retained.files
    }
    root_observed = os.fstat(retained.directory_handle.fd)
    observed_directories = {
        Path("."): (root_observed.st_dev, root_observed.st_ino)
    }
    observed_files: dict[
        Path,
        tuple[int, int, int, int, int],
    ] = {}
    child_handles: list[_DirectoryHandle] = []

    def visit(
        directory: _DirectoryHandle,
        relative_parent: Path,
    ) -> None:
        with os.scandir(directory.fd) as discovered:
            children = sorted(discovered, key=lambda entry: entry.name)
        for child_entry in children:
            relative = (
                Path(child_entry.name)
                if relative_parent == Path(".")
                else relative_parent / child_entry.name
            )
            path = retained.public.evidence_dir / relative
            observed = os.stat(
                child_entry.name,
                dir_fd=directory.fd,
                follow_symlinks=False,
            )
            if stat.S_ISDIR(observed.st_mode):
                child = _open_child_directory(
                    directory,
                    child_entry.name,
                    path,
                    observed,
                )
                child_handles.append(child)
                observed_directories[relative] = (
                    child.device,
                    child.inode,
                )
                visit(child, relative)
            elif stat.S_ISREG(observed.st_mode):
                observed_files[relative] = _stat_identity(observed)
            else:
                raise BootProbeError(
                    f"unsafe {_file_type(observed.st_mode)} "
                    f"retained evidence entry: {path}"
                )

    try:
        if (
            not stat.S_ISDIR(root_observed.st_mode)
            or observed_directories[Path(".")]
            != (
                retained.directory_handle.device,
                retained.directory_handle.inode,
            )
        ):
            raise BootProbeError(
                f"retained evidence directory changed: "
                f"{retained.public.evidence_dir}"
            )
        visit(retained.directory_handle, Path("."))
        if observed_directories != expected_directories:
            raise BootProbeError(
                f"retained evidence directory inventory changed: "
                f"{retained.public.evidence_dir}"
            )
        if observed_files != expected_files:
            raise BootProbeError(
                f"retained evidence file inventory changed: "
                f"{retained.public.evidence_dir}"
            )
        return tuple(
            sorted(
                child_handles,
                key=lambda handle: len(handle.path.parts),
                reverse=True,
            )
        )
    except BaseException as primary:
        for handle in reversed(child_handles):
            try:
                handle.close()
            except BaseException as close_error:
                _note_later_error(
                    primary,
                    "evidence tree scan handle close also failed",
                    close_error,
                )
        raise


def _verify_and_sync_retained_evidence(
    retained: _RetainedBootEvidence,
) -> None:
    if retained.decision is None:
        raise BootProbeError(
            f"retained evidence decision is missing: "
            f"{retained.public.evidence_dir}"
        )
    child_handles = _open_verified_evidence_directories(retained)
    primary: BaseException | None = None
    try:
        before_sync = _capture_retained_evidence_decision(retained)
        if before_sync != retained.decision:
            raise BootProbeError(
                f"retained evidence changed before fsync: "
                f"{retained.public.evidence_dir}"
            )
        for item in retained.files:
            os.fsync(item.descriptor)
        after_sync = _capture_retained_evidence_decision(retained)
        if after_sync != retained.decision:
            raise BootProbeError(
                f"retained evidence changed during fsync: "
                f"{retained.public.evidence_dir}"
            )
        for directory in child_handles:
            os.fsync(directory.fd)
        os.fsync(retained.directory_handle.fd)
    except BaseException as exc:
        primary = exc
    for handle in child_handles:
        try:
            handle.close()
        except BaseException as close_error:
            if primary is None:
                primary = close_error
            else:
                _note_later_error(
                    primary,
                    "verified evidence directory close also failed",
                    close_error,
                )
    if primary is not None:
        raise primary
```

Do not attempt another tree scan after this final boundary. Every temporary-handle close either becomes the primary error or is attached to the earlier verification/fsync error.

- [ ] **Step 7: Run the evidence-decision gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'probe_grades_late_error or retained_evidence or verify_retained_evidence or public_collector_preserves_verification_error or evidence_inventory_error_survives_scan_handle_close_failure or marker_error_and_exit or exact_markers or shutdown_log'
```

Expected: all selected tests pass and the final error/marker result matches the bytes present in the retained evidence. Do not stage or commit.

---

### Task 5: Run Lifecycle and Descriptor-Pinned Publication

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:2995-3241`
- Modify: `tests/test_oracle_boot.py:1729-3605`
- Modify: `tests/test_oracle_boot.py:3788-3971`

**Interfaces:**
- Consumes:
  - `_collect_boot_evidence_retained(before, game, evidence, expected_inventory=after_logs) -> _RetainedBootEvidence`
  - `retained.decision: _EvidenceDecision`
  - `_verify_and_sync_retained_evidence(retained) -> None`
  - `_stage_probe_json(result.evidence_dir, payload, _directory_handle=retained.directory_handle) -> _StagedProbeJson`
  - `_write_probe_json(result.evidence_dir, payload, _staged=staged_probe) -> None`
  - `_cleanup_spawned_process(process, spawned_pgid) -> int | None`
- Produces:
  - `_restore_config_guard_for_failure_cleanup(guard: _ConfigGuard) -> None`
  - final `BootProbeResult.markers` and log-error issues from `retained.decision`
  - no staged or canonical JSON before config and guard cleanup succeeds
  - final evidence verification/fsync after cleanup and immediately before publication

- [ ] **Step 1: Write the failing allocated-directory identity regression**

Patch `_stage_probe_json`, not `_write_probe_json`, so substitution occurs in the gap rejected by final review:

```python
def test_probe_uses_allocated_evidence_handle_before_json_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(tmp_path, log_text="\n".join(REQUIRED_MARKERS))
    original_stage = oracle_boot._stage_probe_json
    displaced: Path | None = None

    def substitute_before_stage(evidence_dir, payload, *args, **kwargs):
        nonlocal displaced
        displaced = evidence_dir.with_name(f"{evidence_dir.name}-displaced")
        evidence_dir.rename(displaced)
        evidence_dir.mkdir(mode=0o700)
        (evidence_dir / "replacement.keep").write_bytes(b"replacement")
        return original_stage(evidence_dir, payload, *args, **kwargs)

    monkeypatch.setattr(
        oracle_boot,
        "_stage_probe_json",
        substitute_before_stage,
    )

    with pytest.raises(oracle_boot.BootProbeError, match="identity"):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    assert displaced is not None
    assert (
        displaced / "nested/preloader_probe.log"
    ).read_text(encoding="utf-8") == "\n".join(REQUIRED_MARKERS)
    _assert_no_canonical_probe_json(displaced, layout.evidence)
```

The frozen source accepts the replacement at staging and can publish success there; the retained-handle implementation must reject it.

- [ ] **Step 2: Write the failing post-cleanup evidence revalidation regression**

Wrap the first successful config restoration, mutate the already-preserved log, and require publication failure:

```python
def test_probe_revalidates_collected_evidence_after_cleanup_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=b"mutated during probe\n",
    )
    original_restore = oracle_boot._restore_config_guard
    injected = False

    def restore_then_mutate_evidence(guard):
        nonlocal injected
        original_restore(guard)
        if not injected:
            preserved = next(
                layout.evidence.rglob("preloader_probe.log")
            )
            preserved.write_bytes(
                preserved.read_bytes() + b"\nchanged before publication"
            )
            injected = True

    monkeypatch.setattr(
        oracle_boot,
        "_restore_config_guard",
        restore_then_mutate_evidence,
    )

    with pytest.raises(oracle_boot.BootProbeError):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    assert injected
    _assert_no_canonical_probe_json(layout.evidence)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG


def test_probe_preserves_monitor_error_over_process_cleanup_uncertainty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )

    class PrimaryMonitorError(RuntimeError):
        pass

    class CleanupUncertainError(RuntimeError):
        pass

    monkeypatch.setattr(
        oracle_boot,
        "_wait_for_markers",
        lambda *_args: (_ for _ in ()).throw(
            PrimaryMonitorError("primary monitor failure")
        ),
    )
    monkeypatch.setattr(
        oracle_boot,
        "_stop_spawned_process_group",
        lambda *_args: (_ for _ in ()).throw(
            CleanupUncertainError("cleanup remains uncertain")
        ),
    )

    with pytest.raises(PrimaryMonitorError) as raised:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    assert any(
        "cleanup" in note and "cleanup remains uncertain" in note
        for note in getattr(raised.value, "__notes__", ())
    )
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    _assert_no_canonical_probe_json(layout.evidence)


def test_probe_retained_evidence_close_failure_cannot_publish_canonical_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    original_close = oracle_boot._RetainedBootEvidence.close
    close_calls = 0

    class RetainedCloseError(OSError):
        pass

    def close_then_raise(retained):
        nonlocal close_calls
        close_calls += 1
        original_close(retained)
        raise RetainedCloseError("retained evidence close failed")

    monkeypatch.setattr(
        oracle_boot._RetainedBootEvidence,
        "close",
        close_then_raise,
    )

    with pytest.raises(
        RetainedCloseError,
        match="retained evidence close failed",
    ):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    assert close_calls >= 1
    _assert_no_canonical_probe_json(layout.evidence)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG


def test_probe_writer_boundary_failure_closes_staged_descriptors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    staged_descriptors: list[int] = []

    class WriterBoundaryError(KeyboardInterrupt):
        pass

    def fail_before_writer_ownership(
        evidence_dir,
        _payload,
        *,
        _staged=None,
    ):
        assert _staged is not None
        assert evidence_dir == _staged.directory
        staged_descriptors.extend(
            (
                _staged.directory_handle.fd,
                _staged.verifier_fd,
            )
        )
        assert (evidence_dir / _staged.pending_name).exists()
        raise WriterBoundaryError("interrupt at writer call boundary")

    monkeypatch.setattr(
        oracle_boot,
        "_write_probe_json",
        fail_before_writer_ownership,
    )

    with pytest.raises(
        WriterBoundaryError,
        match="interrupt at writer call boundary",
    ):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    assert len(staged_descriptors) == 2
    for descriptor in staged_descriptors:
        with pytest.raises(OSError) as closed:
            os.fstat(descriptor)
        assert closed.value.errno == errno.EBADF
    _assert_no_canonical_probe_json(layout.evidence)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


def test_probe_retries_interrupted_failure_cleanup_config_restoration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=b"mutated before postflight failure\n",
    )
    original_snapshot = oracle_boot._capture_boot_snapshot
    original_restore = oracle_boot._restore_config_guard
    snapshot_calls = 0
    restore_calls = 0
    partial_payload = b"partial interrupted restoration"

    class PrimaryPostflightError(RuntimeError):
        pass

    def fail_postflight(game):
        nonlocal snapshot_calls
        snapshot_calls += 1
        if snapshot_calls == 2:
            raise PrimaryPostflightError("ordinary postflight failure")
        return original_snapshot(game)

    def interrupt_partial_restore_then_finish(guard):
        nonlocal restore_calls
        restore_calls += 1
        if restore_calls == 1:
            os.lseek(guard.fd, 0, os.SEEK_SET)
            os.ftruncate(guard.fd, 0)
            assert os.write(guard.fd, partial_payload) == len(
                partial_payload
            )
            os.fchmod(guard.fd, 0o600)
            raise KeyboardInterrupt(
                "interrupted after partial config restoration"
            )
        return original_restore(guard)

    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        fail_postflight,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_restore_config_guard",
        interrupt_partial_restore_then_finish,
    )

    with pytest.raises(
        PrimaryPostflightError,
        match="ordinary postflight failure",
    ) as raised:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    assert snapshot_calls == 2
    assert restore_calls == 2
    assert any(
        "config restore failed" in note
        and "interrupted after partial config restoration" in note
        for note in getattr(raised.value, "__notes__", ())
    )
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_no_canonical_probe_json(layout.evidence)
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


@pytest.mark.parametrize(
    "target",
    ["file", "child-directory", "root"],
)
def test_probe_final_evidence_fsync_failure_restores_and_closes(
    target: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=b"mutated before final evidence fsync\n",
    )
    original_collect = oracle_boot._collect_boot_evidence_retained
    original_restore = oracle_boot._restore_config_guard
    original_retained_close = oracle_boot._RetainedBootEvidence.close
    original_fsync = os.fsync
    file_identities: set[tuple[int, int]] = set()
    child_identities: set[tuple[int, int]] = set()
    root_identity: tuple[int, int] | None = None
    retained_descriptors: list[int] = []
    cleanup_complete = False
    retained_closed = False
    injected = False

    class EvidenceFsyncError(OSError):
        pass

    def capture_retained(*args, **kwargs):
        nonlocal root_identity
        retained = original_collect(*args, **kwargs)
        root_identity = (
            retained.directory_handle.device,
            retained.directory_handle.inode,
        )
        retained_descriptors.append(retained.directory_handle.fd)
        for item in retained.files:
            observed = os.fstat(item.descriptor)
            file_identities.add((observed.st_dev, observed.st_ino))
            retained_descriptors.append(item.descriptor)
        child_identities.update(
            (item.device, item.inode)
            for item in retained.directories
            if item.relative_path != Path(".")
        )
        assert file_identities
        assert child_identities
        return retained

    def restore_then_open_injection_window(guard):
        nonlocal cleanup_complete
        original_restore(guard)
        cleanup_complete = True

    def close_and_record(retained):
        nonlocal retained_closed
        try:
            original_retained_close(retained)
        finally:
            retained_closed = True

    def fail_selected_fsync(descriptor: int) -> None:
        nonlocal injected
        if cleanup_complete and not injected:
            observed = os.fstat(descriptor)
            identity = (observed.st_dev, observed.st_ino)
            selected = (
                (target == "file" and identity in file_identities)
                or (
                    target == "child-directory"
                    and identity in child_identities
                )
                or (target == "root" and identity == root_identity)
            )
            if selected:
                injected = True
                raise EvidenceFsyncError(
                    f"injected final {target} fsync failure"
                )
        original_fsync(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        capture_retained,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_restore_config_guard",
        restore_then_open_injection_window,
    )
    monkeypatch.setattr(
        oracle_boot._RetainedBootEvidence,
        "close",
        close_and_record,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=fail_selected_fsync),
        raising=False,
    )

    with pytest.raises(
        EvidenceFsyncError,
        match=rf"injected final {target} fsync failure",
    ):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    assert cleanup_complete
    assert injected
    assert retained_closed
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_no_canonical_probe_json(layout.evidence)
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)
    for descriptor in retained_descriptors:
        with pytest.raises(OSError) as closed:
            os.fstat(descriptor)
        assert closed.value.errno == errno.EBADF
```

- [ ] **Step 3: Run the frozen-source RED gate**

First lock the writer-boundary cleanup behavior that is already correct on the frozen source:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'writer_boundary_failure_closes_staged_descriptors'
```

Expected: PASS. This is a green lifecycle-preservation test, not RED evidence.

Then run the missing-behavior regressions:

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'uses_allocated_evidence_handle_before_json_staging or revalidates_collected_evidence_after_cleanup or preserves_monitor_error_over_process_cleanup_uncertainty or retained_evidence_close_failure_cannot_publish or retries_interrupted_failure_cleanup_config_restoration or final_evidence_fsync_failure_restores_and_closes'
```

Expected: the evidence regressions fail by accepting a replaced path or publishing without a final retained-evidence check, the process case exposes cleanup failure instead of the original monitor error, the frozen failure-cleanup path makes only one interrupted restoration attempt and leaves partial config bytes, and the retained-close/fsync cases fail because the retained transaction and final durability boundary do not yet exist.

- [ ] **Step 4: Restructure the successful launch path around retained evidence**

Use the monitor outcome only for its process state and exit status. After cleanup:

```python
after_logs = _fingerprint_regular_preloader_logs(game)
retained = _collect_boot_evidence_retained(
    before,
    game,
    evidence,
    expected_inventory=after_logs,
)
decision = retained.decision
if decision is None:
    raise BootProbeError(
        f"retained evidence decision is missing: "
        f"{retained.public.evidence_dir}"
    )
final_outcome = _MonitorOutcome(
    state=_monitor_outcome.state,
    markers=decision.markers,
    errors=decision.errors,
    exit_code=final_exit_code,
)
```

Build `BootProbeResult` and `_probe_result_payload` from `retained.public`, `decision`, preflight/postflight, `before`, and `after_logs`. Do not union earlier scanned log-error literals into `decision.errors`. A prior monitor `"error"` state with no preserved error remains fail-closed through `_monitor_result_issues`.

- [ ] **Step 5: Update tests that intentionally intercept healthy-path collection**

In `test_probe_json_schema_v1_matches_independent_exact_encoding`, replace the public-collector spy with:

```python
original_collect_retained = oracle_boot._collect_boot_evidence_retained


def capture_after_logs(
    before,
    game_root,
    evidence_root,
    *,
    expected_inventory,
):
    assert expected_inventory is not None
    after_logs.extend(
        _independent_log_fingerprint(fingerprint.path)
        for fingerprint in expected_inventory
    )
    return original_collect_retained(
        before,
        game_root,
        evidence_root,
        expected_inventory=expected_inventory,
    )


monkeypatch.setattr(
    oracle_boot,
    "_collect_boot_evidence_retained",
    capture_after_logs,
)
```

In the `"evidence"` row of `test_probe_restores_exact_config_after_exception_at_every_stage`, patch `_collect_boot_evidence_retained` instead of `collect_boot_evidence`. Keep preflight-rejection tests on the public collector because they intentionally exercise the no-launch path.

- [ ] **Step 6: Move restoration, cleanup, verification, and publication into strict order**

Add one bounded failure-cleanup restoration wrapper. It retries only when the first attempt is interrupted by a non-`Exception` `BaseException`; ordinary restoration errors remain single-attempt and fail closed:

```python
def _restore_config_guard_for_failure_cleanup(
    guard: _ConfigGuard,
) -> None:
    try:
        _restore_config_guard(guard)
    except BaseException as primary:
        if isinstance(primary, Exception):
            raise
        try:
            _restore_config_guard(guard)
        except BaseException as retry_error:
            _note_later_error(
                primary,
                "config restoration retry also failed",
                retry_error,
            )
        raise
```

Use it for every outer failure-cleanup restoration while `config_guard.fd` is still open:

```python
if restore_required:
    try:
        _restore_config_guard_for_failure_cleanup(config_guard)
    except BaseException as exc:
        cleanup_errors.append(("config restore failed", exc))
    else:
        restore_required = False
```

Keep the normal pre-publication call to `_restore_config_guard` unchanged. If that normal call is interrupted, `restore_required` remains true and outer failure cleanup invokes the bounded wrapper; if an ordinary body error reaches failure cleanup first, the wrapper itself provides the one interruption retry. Even after a successful retry, it re-raises the first interruption so the body error stays top-level and receives the interruption as a cleanup note.

The normal-success order is:

```text
stop exact spawned group
collect retained evidence
capture postflight
construct result and JSON payload
restore exact config
close launcher guard
close retained game handle
close config guard
verify and fsync retained evidence
stage private probe JSON through retained evidence-directory handle
close retained evidence
commit staged probe JSON to the canonical name
return result
```

The exception order is:

```text
preserve the first body/interrupt exception
attempt config restoration
close guards
close retained evidence
close any staged JSON
attach later failures as notes
leave no canonical probe.json
re-raise the first exception
```

At the launch boundary, prevent a cleanup exception from replacing a monitor/body exception:

```python
launch_error: BaseException | None = None
try:
    process = subprocess.Popen(
        [str(launcher_guard.path)],
        cwd=str(game),
        shell=False,
        start_new_session=True,
    )
    spawned_pgid = _retained_spawned_pgid(process)
    _monitor_outcome = _wait_for_markers(
        process,
        game,
        before,
        timeout,
    )
except BaseException as exc:
    launch_error = exc
finally:
    if process is not None:
        try:
            cleanup_exit_code = _cleanup_spawned_process(
                process,
                spawned_pgid,
            )
        except BaseException as cleanup_error:
            if launch_error is None:
                raise
            _note_later_error(
                launch_error,
                "spawned process cleanup also failed",
                cleanup_error,
            )
if launch_error is not None:
    raise launch_error
```

After all guard cleanup succeeds, prepare publication exactly as:

```python
_verify_and_sync_retained_evidence(retained)
staged_probe = _stage_probe_json(
    result.evidence_dir,
    payload,
    _directory_handle=retained.directory_handle,
)
retained.close()
retained = None
_write_probe_json(
    result.evidence_dir,
    payload,
    _staged=staged_probe,
)
staged_probe = None
```

Keep `staged_probe` as an outer cleanup-owned variable until `_write_probe_json` returns; do not clear or alias it before the call. If a `BaseException` occurs at the function-call boundary before the writer takes ownership, outer cleanup closes its retained directory/verifier descriptors; the private pending artifact may remain as failure evidence, but no canonical name may appear. `_close_staged_probe_json` is idempotent, so a writer error may close it internally and outer cleanup may safely close it again. Do not stage JSON before cleanup. If retained-evidence close fails after staging, close the staged publisher and re-raise without exposing a canonical name. If publication fails, preserve the publication error and attach staged-close uncertainty as a note.

- [ ] **Step 7: Remove superseded ambient/final-scan logic**

Remove:

```text
_EXPECTED_COLLECTOR_INVENTORY
_observe_final_boot_logs
inventory-token set/reset in run_boot_probe
_verify_staged_probe_json_directory
```

Retain `_observe_boot_logs` and `_wait_for_markers` for bounded live monitoring.

- [ ] **Step 8: Run the complete run-lifecycle gate**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k 'probe_ and not write_probe_json and not rejects_evidence_directory_substitution_at_final_json_boundary'
```

Expected: every selected run-level test passes, controlled process groups are stopped, exact config bytes/mode are restored, normal negative results still publish `success: false`, and cleanup/integrity errors publish no canonical JSON. Do not stage or commit.

---

### Task 6: Reachable Canonical Reconciliation and Test-Quality Closure

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:2225-2778`
- Modify: `tests/test_oracle_boot.py:491-498`
- Modify: `tests/test_oracle_boot.py:4911-6005`

**Interfaces:**
- Consumes: `_StagedProbeJson`, `_stat_staged_probe_json_name`, `_preserve_canonical_probe_json_privately`, `_note_later_error`.
- Produces:
  - `_secure_private_probe_json(staged: _StagedProbeJson, private_name: str, expected_identity: tuple[int, int, int, int, int]) -> None`
  - `_quarantine_reachable_canonical_probe_json(staged: _StagedProbeJson, primary: BaseException) -> None`
  - bounded quarantine on every caught post-rename namespace-reconciliation failure
  - mode-`0600` retained-inode quarantine before a private move is treated as successful
  - explicit non-strict xfail metadata on the six parameter instances that exercise excluded active final-syscall replacement
  - shared `_exception_graph` use in in-scope publication tests

- [ ] **Step 1: Encode the active-adversary exclusions without hiding them**

Add this marker to each of the following four test functions:

```python
@pytest.mark.xfail(
    strict=False,
    reason=(
        "active final-syscall path replacement is outside the "
        "approved practical threat model"
    ),
)
```

The functions are:

```text
test_probe_rejects_evidence_directory_substitution_at_final_json_boundary
test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts
test_write_probe_json_rejects_post_publish_evidence_path_substitution
test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution
```

The last two are each parameterized twice, so this documents exactly six non-strict XFAIL/XPASS cases. Keep their bodies intact as visible aspirational coverage, but do not use them as focused acceptance gates.

- [ ] **Step 2: Write the failing reconciliation and quarantine-mode regressions**

Parameterize the first namespace check after rename and a namespace check after a successful publication fsync:

```python
@pytest.mark.parametrize("failure_point", ["initial-reconcile", "post-fsync"])
def test_write_probe_json_quarantines_reachable_canonical_after_reconcile_error(
    failure_point: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1, "success": True}
    expected = oracle_boot._encode_probe_json(payload)
    original_namespace = oracle_boot._probe_json_retained_namespace
    publish_seen = False
    namespace_calls_after_publish = 0
    original_renameatx = oracle_boot._renameatx

    def tracked_rename(*args, **kwargs):
        nonlocal publish_seen
        original_renameatx(*args, **kwargs)
        destination = _rename_destination_name(args, kwargs)
        if destination == "probe.json":
            publish_seen = True

    def fail_once_after_publish(staged):
        nonlocal namespace_calls_after_publish
        if publish_seen:
            namespace_calls_after_publish += 1
            selected = (
                namespace_calls_after_publish == 1
                if failure_point == "initial-reconcile"
                else namespace_calls_after_publish == 2
            )
            if selected:
                raise OSError(errno.EIO, f"injected {failure_point}")
        return original_namespace(staged)

    monkeypatch.setattr(oracle_boot, "_renameatx", tracked_rename)
    monkeypatch.setattr(
        oracle_boot,
        "_probe_json_retained_namespace",
        fail_once_after_publish,
    )

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._write_probe_json(evidence, payload)

    assert publish_seen
    assert any(
        failure_point in str(candidate)
        or any(failure_point in note for note in getattr(candidate, "__notes__", ()))
        for candidate in _exception_graph(raised.value)
    )
    assert not (evidence / "probe.json").exists()
    private = [
        path
        for path in evidence.iterdir()
        if path.is_file() and path.name != "probe.json"
    ]
    assert len(private) == 1
    assert private[0].read_bytes() == expected
    assert stat.S_IMODE(private[0].stat().st_mode) == 0o600


@pytest.mark.parametrize("initial_mode", [0o000, 0o644])
def test_preserve_canonical_probe_json_quarantine_forces_mode_0600(
    initial_mode: int,
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1, "success": True}
    staged = oracle_boot._stage_probe_json(evidence, payload)
    canonical_path = evidence / "probe.json"
    canonical_payload = b"sensitive mismatched canonical\n"
    canonical_path.write_bytes(canonical_payload)
    canonical_path.chmod(initial_mode)
    canonical_before = canonical_path.stat()
    primary = oracle_boot.BootProbeError(
        "force mismatched canonical quarantine"
    )

    try:
        canonical = oracle_boot._stat_staged_probe_json_name(
            staged,
            "probe.json",
        )
        assert canonical is not None
        oracle_boot._preserve_canonical_probe_json_privately(
            staged,
            canonical,
            primary=primary,
        )

        assert not canonical_path.exists()
        quarantined = [
            path
            for path in evidence.iterdir()
            if path.stat().st_ino == canonical_before.st_ino
            and path.stat().st_dev == canonical_before.st_dev
        ]
        assert len(quarantined) == 1
        observed = quarantined[0].stat()
        assert stat.S_ISREG(observed.st_mode)
        assert stat.S_IMODE(observed.st_mode) == 0o600
        assert quarantined[0].read_bytes() == canonical_payload
        assert getattr(primary, "__notes__", ()) == ()
    finally:
        oracle_boot._close_staged_probe_json(staged)
```

- [ ] **Step 3: Run the frozen-source RED gate**

Run:

```bash
PYTHONPATH=/private/tmp/ssr-task8-frozen-ebee41facd576a7a5695681a92dc6c6a96b0004fb082cb7aad4e93f5dd50954f/src \
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'quarantines_reachable_canonical_after_reconcile_error or quarantine_forces_mode_0600'
```

Expected: at least the initial reconciliation case leaves canonical success JSON on the frozen source, and each reachable mismatched canonical remains at its original non-`0600` mode (`0000` or `0644`) after the frozen quarantine path.

- [ ] **Step 4: Enforce private mode and implement bounded reachable-canonical quarantine**

Secure the exact moved inode through a retained descriptor before `_move_canonical_probe_json_to_private` reports success:

```python
def _secure_private_probe_json(
    staged: _StagedProbeJson,
    private_name: str,
    expected_identity: tuple[int, int, int, int, int],
) -> None:
    before = _stat_staged_probe_json_name(staged, private_name)
    if (
        before is None
        or not stat.S_ISREG(before.st_mode)
        or _stat_identity(before) != expected_identity
    ):
        raise BootProbeError(
            f"private probe JSON identity changed in "
            f"{staged.directory}"
        )
    os.chmod(
        private_name,
        0o600,
        dir_fd=staged.directory_handle.fd,
        follow_symlinks=False,
    )
    secured = _stat_staged_probe_json_name(staged, private_name)
    if secured is None:
        raise BootProbeError(
            f"private probe JSON disappeared while setting mode in "
            f"{staged.directory}"
        )
    if (
        not stat.S_ISREG(secured.st_mode)
        or (
            secured.st_dev,
            secured.st_ino,
            secured.st_size,
            secured.st_mtime_ns,
        )
        != (
            expected_identity[0],
            expected_identity[1],
            expected_identity[3],
            expected_identity[4],
        )
        or stat.S_IMODE(secured.st_mode) != 0o600
    ):
        raise BootProbeError(
            f"private probe JSON changed while setting mode in "
            f"{staged.directory}"
        )
    secured_identity = _stat_identity(secured)
    descriptor = os.open(
        private_name,
        os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
        dir_fd=staged.directory_handle.fd,
    )
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _stat_identity(opened) != secured_identity
        ):
            raise BootProbeError(
                f"private probe JSON identity changed in "
                f"{staged.directory}"
            )
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
        after = os.fstat(descriptor)
        named = _stat_staged_probe_json_name(staged, private_name)
        stable_after_chmod = (
            named is not None
            and stat.S_ISREG(after.st_mode)
            and stat.S_ISREG(named.st_mode)
            and _stat_identity(after) == secured_identity
            and _stat_identity(named) == secured_identity
            and stat.S_IMODE(after.st_mode) == 0o600
            and stat.S_IMODE(named.st_mode) == 0o600
        )
        if not stable_after_chmod:
            raise BootProbeError(
                f"private probe JSON changed while securing mode in "
                f"{staged.directory}"
            )
    except BaseException as primary:
        try:
            os.close(descriptor)
        except BaseException as close_error:
            _note_later_error(
                primary,
                "private probe JSON descriptor close also failed",
                close_error,
            )
        raise
    os.close(descriptor)
```

In `_move_canonical_probe_json_to_private`, replace the immediate successful return with:

```python
_secure_private_probe_json(
    staged,
    private_name,
    expected_identity,
)
return private_name, tuple(errors)
```

This applies equally to mismatched-canonical quarantine and durability rollback. It does not reopen through the public evidence path.

Then add the reachable-canonical helper:

```python
def _quarantine_reachable_canonical_probe_json(
    staged: _StagedProbeJson,
    primary: BaseException,
) -> None:
    try:
        canonical = _stat_staged_probe_json_name(staged, "probe.json")
    except BaseException as lookup_error:
        _note_later_error(
            primary,
            "canonical probe JSON lookup during reconciliation also failed",
            lookup_error,
        )
        return
    _preserve_canonical_probe_json_privately(
        staged,
        canonical,
        primary=primary,
    )
```

Wrap every `_probe_json_retained_namespace(staged)` call made after the exclusive publish attempt. On reconciliation failure:

```python
integrity_error = BootProbeError(
    f"cannot reconcile tentative probe JSON publication in "
    f"{staged.directory}"
)
_note_later_error(
    integrity_error,
    "post-rename probe JSON reconciliation failed",
    reconciliation_error,
)
if rename_error is not None:
    _note_later_error(
        integrity_error,
        "exclusive probe JSON rename also raised",
        rename_error,
    )
_quarantine_reachable_canonical_probe_json(staged, integrity_error)
raise integrity_error from reconciliation_error
```

Use the same helper for reconciliation failures after publication fsync. Keep existing 128-attempt collision bounds and three directory-fsync attempts.

- [ ] **Step 5: Consolidate in-scope publication-test helpers**

Replace repeated cause/context graph loops with `_exception_graph` in in-scope tests. Use `_assert_no_canonical_probe_json` in cleanup/integrity cases, and keep exact `BootProbeError` assertions on the new reachable-reconciliation regressions. Do not weaken ordinary negative-result JSON assertions. Do not strengthen or gate the six active-racer exclusions from Step 1.

- [ ] **Step 6: Run all in-scope publication and cleanup gates**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q \
  tests/test_oracle_boot.py \
  -k '(write_probe_json or canonical or cleanup_close or restore_failure) and not rejects_evidence_directory_substitution_at_final_json_boundary and not rejects_pending_name_substitution_and_preserves_both_artifacts and not rejects_post_publish_evidence_path_substitution and not rejects_post_publish_fsync_evidence_path_substitution'
```

Expected: all selected in-scope tests pass; any reachable canonical artifact is either exact committed output on success or collision-safe private mode-`0600` evidence on failure. The six non-strict active-racer cases are intentionally not selected here. Do not stage or commit.

---

### Task 7: Full Verification, Practical-Model Review, and the Single Task 8 Commit

**Files:**
- Verify and commit: `src/ssr_env/oracle_boot.py`
- Verify and commit: `tests/test_oracle_boot.py`
- Verify and commit: `tools/oracle_boot_probe.py`
- Read only: `docs/superpowers/specs/2026-07-29-oracle-practical-threat-model-design.md`
- Preserve all owner-local files listed in Global Constraints.

**Interfaces:**
- Consumes: completed Tasks 1A-6 and the approved practical threat model.
- Produces: one reviewed Task 8 commit named `feat: add controlled oracle boot probe`.

- [ ] **Step 1: Prove superseded logic is absent and compile all Task 8 artifacts**

Run:

```bash
rg -n '_verify_staged_probe_json_directory|_observe_final_boot_logs|_EXPECTED_COLLECTOR_INVENTORY' \
  src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m py_compile \
  src/ssr_env/oracle_boot.py \
  tests/test_oracle_boot.py \
  tools/oracle_boot_probe.py
```

Expected: `rg` reports no matches and compilation exits zero.

- [ ] **Step 2: Run the complete Task 8 and repository suites**

Run:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q tests/test_oracle_boot.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
```

Expected: every mandatory Task 8 test passes. The full repository has no new failure, retains its existing 120 expected xfails, and reports each of the six non-strict active-adversary exclusions as either XFAIL or XPASS without failing the suite.

- [ ] **Step 3: Run whitespace, scope, mode, and hash audits**

Run:

```bash
git diff --check
git diff --no-index --check /dev/null src/ssr_env/oracle_boot.py
git diff --no-index --check /dev/null tests/test_oracle_boot.py
git diff --no-index --check /dev/null tools/oracle_boot_probe.py
stat -f '%Sp %N' \
  src/ssr_env/oracle_boot.py \
  tests/test_oracle_boot.py \
  tools/oracle_boot_probe.py
shasum -a 256 \
  src/ssr_env/oracle_boot.py \
  tests/test_oracle_boot.py \
  tools/oracle_boot_probe.py
git status --short
git diff --cached --name-only
```

Expected: no whitespace errors; all three artifacts are mode `-rw-r--r--`; the index is empty; status contains only the known owner-local paths plus the three authorized Task 8 artifacts.

- [ ] **Step 4: Dispatch independent practical-model specification and quality reviews**

Give both reviewers:

```text
Review only src/ssr_env/oracle_boot.py, tests/test_oracle_boot.py, and
tools/oracle_boot_probe.py against
docs/superpowers/specs/2026-07-29-oracle-practical-threat-model-design.md.
The explicit active-adversary non-goals are exclusions, not defects.
Do not edit, stage, commit, launch the game, or inspect/mutate installed-game
state. Report Spec ACCEPT/FAIL and Quality ACCEPT/REJECT with exact evidence.
```

Require both reviews to accept. If either rejects an in-scope behavior, return to the smallest owning cohort, add a RED regression, implement the bounded fix, and repeat Steps 1-4.

- [ ] **Step 5: Stage exactly the three authorized artifacts**

Run:

```bash
git add \
  src/ssr_env/oracle_boot.py \
  tests/test_oracle_boot.py \
  tools/oracle_boot_probe.py
git diff --cached --name-only
git diff --cached --check
```

Expected staged names:

```text
src/ssr_env/oracle_boot.py
tests/test_oracle_boot.py
tools/oracle_boot_probe.py
```

- [ ] **Step 6: Commit Task 8 and verify the committed tree**

Run:

```bash
git commit -m "feat: add controlled oracle boot probe"
git show --stat --oneline --decorate HEAD
git status --short
```

Expected: one commit containing exactly the three authorized Task 8 artifacts. Owner-local paths remain unstaged and unchanged. No real game launch or installed-game write has occurred.

- [ ] **Step 7: Hand off to Task 9 without mutating the installed game**

Report the final test counts, three artifact SHA-256 values, both reviewer verdicts, and commit ID. State explicitly that Task 9 will rebuild pinned local artifacts, repeat read-only Tahoe 26.6 preflight, request separate installed-game mutation approval, and only then deploy and perform the already-authorized controlled boot.
