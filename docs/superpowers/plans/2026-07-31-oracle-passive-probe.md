# SSR Passive Probe Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an offline-tested, fail-closed controller that can preflight and, only under later separate approval, perform one authenticated passive capture while retaining every reachable artifact and restoring exact Mode-off/official state.

**Architecture:** Keep `run_boot_probe`, `BootProbeResult`, and canonical `probe.json` byte-for-byte compatible. Add only three behavior-preserving seams to `oracle_boot.py`: structured changed-log observation, caller-owned auxiliary evidence, and selectable canonical JSON name. Put save proofs, private layout, trace authentication, process inventory, passive snapshots, preflight, orchestration, and the `passive-probe.json` contract in `oracle_passive_probe.py`. Each task below is one independently testable reviewer gate.

**Tech Stack:** Python 3.12+, pytest, POSIX descriptor-relative/no-follow filesystem operations, macOS `sysctl`, `subprocess` process groups, existing `ssr_env.oracle_boot` and `ssr_env.oracle_install`, and `ssr_env.oracle_protocol` from the protocol plan.

## File map

- `src/ssr_env/oracle_install.py`: installer transaction ownership and rollback only.
- `src/ssr_env/oracle_boot.py`: legacy-compatible shared log/evidence/publication seams only.
- `src/ssr_env/oracle_passive_probe.py`: every passive-only type and lifecycle operation.
- `tools/oracle_passive_probe.py`: import-only CLI wrapper.
- `tests/test_oracle_install.py`: plugin-deployment interruption tests.
- `tests/test_oracle_install_compat.py`: preloader deploy/restore interruption tests.
- `tests/test_oracle_boot.py`: shared-seam compatibility tests.
- `tests/test_oracle_passive_probe.py`: passive unit, transaction, and synthetic end-to-end tests.
- `oracle/README.md`: offline/runbook status and exact future command contract.
- `docs/superpowers/plans/2026-07-27-executable-oracle.md`: pointer from superseded flexible-input text to the approved passive schema.
- `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`: implementation status only; never weaken the approved requirements.

## Global constraints

- The authoritative design is `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`, especially sections 5.5, 9-11, and 12.4-12.5.
- Every task in this plan is offline implementation and synthetic verification only. Do not deploy to, mutate, or launch the installed game.
- Standalone preflight must run absolute `/usr/bin/sw_vers -productVersion` with `LC_ALL=C` and a five-second timeout, retain exact product version `26.6`, and reject a missing, failed, malformed, or different result before allocation, installer mutation, or launcher acquisition.
- Do not change `run_boot_probe`, `BootProbeResult`, its CLI, its marker tuple, or canonical `probe.json` schema version 1. Generalized helpers must default to the old behavior, and `tests/test_oracle_boot.py` must remain GREEN after every shared-helper task.
- Do not add passive lifecycle logic to the already-large `oracle_boot.py`; it owns only the three shared seams listed in the architecture.
- Before any real launch, the protocol plan, plugin plan, this plan, independent reviews, two byte-identical `0.2.0` builds, a literal reviewed plugin SHA-256, and a fresh standalone read-only preflight must pass. A separate operational-acceptance plan requests approval afterward.
- One approval authorizes at most one launcher acquisition and no retry. The controller never injects input, invokes a gameplay method, launches through Steam, or treats terminal stdout as authoritative.
- The five physical input events are two menu confirmations, one visibly accepted direction, one visibly refused direction, and one Undo, grouped into four authenticated prompt phases.
- The ordinary save path is exactly `$HOME/Library/Application Support/unity.increpare games/Sausage`. Success requires byte-for-byte-equal before, post-process, and final no-follow proofs.
- Existing ordinary-save trees permit only real directories and regular files, at most 4,096 descendants excluding the root and at most 256 MiB of regular-file bytes. Root, every directory entry, and every existing absence-chain ancestor retain actual size, nanosecond mtime, and nanosecond ctime.
- Evidence/output and isolated-save leaves are distinct sibling directories under ignored `data/oracle/`, mode `0700`, with no symlink component or containment in either direction. Evidence files become `0600`; isolated regular files become `0600` and isolated directories `0700` without traversing an unsupported entry.
- The generated passive config is strict UTF-8 without BOM, uses exact LF lines, is required evidence named `passive.cfg`, and is bounded at 64 KiB. The trace target is optional evidence named `passive-trace.ndjson`, is bounded at 128 MiB, and must be absent before deployment and startup.
- A record-code failure marker is authoritative only with a stable, closed, structurally valid terminal-Error trace whose exact error code matches the marker. A marker-only code may have no trace. Any stable trace bytes that do exist after reaping—including malformed, partial `trace_io_failed`, or early-exit bytes—remain retained.
- Completion requires the completion marker plus two identical descriptor-opened reads that pass both `read_oracle_trace_stream` and `require_passive_success`.
- Cleanup order is process group, evidence staging, ordinary proof, Mode-off installer deployment, official-preloader restore, final installed/process/save proofs, evidence fsync, then exclusive `passive-probe.json` publication last.
- Preserve the identical primary `BaseException`; attach later cleanup failures in deterministic order. Never improvise by copying, deleting, re-signing, relaunching, or directly editing the installed tree.
- Use strict TDD. Each task has one RED command, one GREEN command, a fresh review gate, and one commit.
- Before Task 1, verify the protocol and plugin prerequisites from the coordinator rather than trusting branch position: record the 26 protocol commit SHAs and their approved review artifacts, the 24 decimal plugin commit SHAs/cohorts and their approved review artifacts, the literal protocol API signatures consumed below, the two byte-identical `0.2.0` DLL paths and SHA-256, the pinned assembly SHA-256, and the Mode-off fixture SHA-256. Run the protocol and plugin exit gates exactly as written in the coordinator and require the recorded heads/artifact pins to match. Any missing commit, cohort, API, review artifact, or changed pin stops before Task 1.
- Every detailed task has six sequential checklist actions: register the exact RED, run that RED and observe the named failure, implement the complete minimal change, run the exact GREEN, obtain fresh specification and code-quality reviews and save both review artifact paths/SHAs in the task report, then make exactly one commit containing only that task. A prior task's review never satisfies a later task; after either reviewer requests changes, rerun the GREEN and both fresh reviews before committing.
- Frozen task-base hashes are:

```text
ccc76c24075a69bf69c2d6febb3513e8e0ff47d3c424b65fb76d2825e86af083  src/ssr_env/oracle_boot.py
554e7443f60e40f9279af28f9dd1a6e2d0752124855d9bbc68191f68a9247bec  src/ssr_env/oracle_install.py
ef6805de04970cc8fbbec09bcebea125d6124a7740cc9ab2f4b09f9e5152f7f3  tests/test_oracle_boot.py
```

## Exact execution and test ledger

The coordinator's probe Tasks 1-21 remain stable task families. This repaired plan expands them into 43 independently reviewed gates (`1`, `2`, `3`, `4`, `5A`-`5C`, `6`, `7A`-`7C`, `8A`-`8C`, `9`, `10A`-`10C`, `11`, `12A`-`12C`, `13A`-`13C`, `14A`-`14B`, `15A`-`15C`, `16`, `17A`-`17C`, `18`, `19A`-`19D`, `20A`-`20C`, `21`). A coordinator instruction to execute family N means execute every lettered gate in that family in order. Each gate has its own RED, GREEN, review, and commit; lettered gates may not be batched.

The prerequisite ledger is Task 0 and is not a commit: it must record the coordinator/protocol/plugin heads, all prerequisite decimal commit cohorts, their per-task specification/quality approvals, the literal `read_oracle_trace_stream`/`require_passive_success` API signatures, both DLL paths, and all three artifact pins before Task 1 begins.

The new pytest registration ledger is normative. Parameterization counts as collected items, not one source function:

```text
1=35 2=21 3=21 4=2 5A=8 5B=12 5C=4 6=3
7A=6 7B=21 7C=22 8A=1 8B=9 8C=21 9=12
10A=10 10B=12 10C=15 11=12 12A=5 12B=12 12C=26
13A=12 13B=3 13C=7 14A=19 14B=17 15A=4 15B=16
15C=5 16=12 17A=3 17B=25 17C=25 18=8 19A=28 19B=21
19C=12 19D=10 20A=3 20B=21 20C=58 21=14
Q = 613 new probe items
```

The frozen post-protocol baseline is `B = 1582 + P = 1582 + 240 = 1822` passing items. Therefore the post-probe suite must collect `2435 + 120 + 6 = 2561` items and report exactly `2435 passed, 120 xfailed, 6 xpassed`. The protocol total is frozen at `P = 240`; do not float it. `B + Q = 1822 + 613 = 2435`, and `2435 + 120 + 6 = 2561`. Task 21 mechanically checks working-tree and clean committed-checkout collection, exact outcome totals, and the exact six XPASS node IDs, so a missing parametrized row, omitted test file, uncommitted test file, unexecuted cohort, unexpected XPASS, or unexpected result class cannot pass merely because pytest exits zero.

---

### Task 1: Make plugin deployment interruption-safe

**Files:**
- Modify: `src/ssr_env/oracle_install.py:792-1069`
- Modify: `tests/test_oracle_install.py:380-670`

**Interfaces:**
- Preserves `deploy_plugin(game_root: Path, plugin: Path, config_text: str) -> InstallManifest` and all ordinary `InstallError` behavior.
- Produces private `_deploy_plugin_bytes(game_root: Path, plugin_bytes: bytes, expected_plugin_sha256: str, config_text: str) -> InstallManifest`. The existing public wrapper authenticates its path once, then delegates. Passive lifecycle code passes already authenticated retained bytes to the private transaction, so no controller check is followed by an installer pathname reopen.
- Produces private `_deploy_plugin_checkpoint(boundary: str) -> None` with the exact closed boundary set below.
- Produces private `_note_installer_secondary(primary: BaseException, stage: str, secondary: BaseException) -> None` used by all three installer-hardening tasks.
- Guarantees logical rollback of plugin bytes, config bytes, modes, manifest bytes, owned-directory inventory, and `status_install`; atomic replacement may legitimately change inode identity.

- [ ] **Step 1: Add the failing interruption matrix**

Add this helper and test to `tests/test_oracle_install.py`:

```python
def _logical_owned_snapshot(game: Path) -> tuple[tuple[str, str, int, bytes], ...]:
    rows: list[tuple[str, str, int, bytes]] = []
    for path in sorted(game.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(game).as_posix()
        observed = path.lstat()
        if path.is_symlink():
            rows.append((relative, "symlink", stat.S_IMODE(observed.st_mode), os.readlink(path).encode()))
        elif path.is_dir():
            rows.append((relative, "directory", stat.S_IMODE(observed.st_mode), b""))
        elif path.is_file():
            rows.append((relative, "file", stat.S_IMODE(observed.st_mode), path.read_bytes()))
        else:
            raise AssertionError(f"unexpected test entry: {path}")
    return tuple(rows)


@pytest.mark.parametrize(
    "boundary",
    (
        "after_staging_mkdir",
        "after_staging_plugin",
        "after_staging_config",
        "before_first_mutation",
        "after_plugin_publish",
        "after_config_publish",
        "after_manifest_publish",
        "before_final_validation",
        "after_final_validation",
    ),
)
@pytest.mark.parametrize(
    "primary",
    (KeyboardInterrupt("stop"), SystemExit(73), GeneratorExit("stop")),
)
def test_deploy_plugin_rolls_back_every_base_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    primary: BaseException,
) -> None:
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin-v1")
    deploy_plugin(game, plugin, "mode = off\n")
    before_tree = _logical_owned_snapshot(game)
    before_status = status_install(game)
    plugin.write_bytes(b"plugin-v2")

    def interrupt(observed: str) -> None:
        if observed == boundary:
            raise primary

    monkeypatch.setattr(oracle_install, "_deploy_plugin_checkpoint", interrupt)
    with pytest.raises(BaseException) as caught:
        deploy_plugin(game, plugin, "mode = passive\n")

    assert caught.value is primary
    assert _logical_owned_snapshot(game) == before_tree
    assert status_install(game) == before_status
    assert not tuple(game.glob(".ssr-oracle-deploy-staging-*"))
    assert not tuple(game.rglob("*.pending"))


def test_deploy_plugin_rejects_source_substitution_after_its_only_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin = tmp_path / "reviewed.dll"
    plugin.write_bytes(b"reviewed-plugin")
    held = tmp_path / "reviewed.held"
    source_opens = 0
    original_open = oracle_install.os.open

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal source_opens
        if dir_fd is not None and os.fspath(path) == plugin.name:
            source_opens += 1
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def checkpoint(boundary: str, observed: Path) -> None:
        if boundary == "after_descriptor_read" and observed == plugin:
            plugin.rename(held)
            plugin.write_bytes(b"replacement-plugin")

    monkeypatch.setattr(oracle_install.os, "open", opening)
    monkeypatch.setattr(oracle_install, "_deploy_plugin_source_checkpoint", checkpoint)
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("substituted source must not reach deployment")
        ),
    )
    with pytest.raises(oracle_install.InstallError, match="changed while authenticating"):
        oracle_install.deploy_plugin(tmp_path / "game", plugin, "mode = off\n")
    assert source_opens == 1


def test_deploy_plugin_delegates_retained_bytes_without_reopening_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin = tmp_path / "reviewed.dll"
    original_payload = b"reviewed-plugin"
    plugin.write_bytes(original_payload)
    held = tmp_path / "reviewed.held"
    source_opens = 0
    original_open = oracle_install.os.open
    delegated: list[tuple[bytes, str, str]] = []
    sentinel = object()

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal source_opens
        if dir_fd is not None and os.fspath(path) == plugin.name:
            source_opens += 1
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def checkpoint(boundary: str, observed: Path) -> None:
        if boundary == "after_named_after" and observed == plugin:
            plugin.rename(held)
            plugin.write_bytes(b"late-replacement")

    def deploy(
        _root: Path,
        payload: bytes,
        expected_sha256: str,
        config_text: str,
    ) -> object:
        delegated.append((payload, expected_sha256, config_text))
        return sentinel

    monkeypatch.setattr(oracle_install.os, "open", opening)
    monkeypatch.setattr(oracle_install, "_deploy_plugin_source_checkpoint", checkpoint)
    monkeypatch.setattr(oracle_install, "_deploy_plugin_bytes", deploy)
    assert oracle_install.deploy_plugin(
        tmp_path / "game", plugin, "mode = passive\n"
    ) is sentinel
    assert source_opens == 1
    assert delegated == [
        (
            original_payload,
            sha256(original_payload).hexdigest(),
            "mode = passive\n",
        )
    ]


@pytest.mark.parametrize(
    "primary",
    (KeyboardInterrupt("stop"), SystemExit(74), GeneratorExit("stop")),
)
@pytest.mark.parametrize("handoff", ("child_snapshot", "absolute_child"))
def test_stable_plugin_source_acquisition_closes_each_owner_on_base_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    primary: BaseException,
    handoff: str,
) -> None:
    plugin = tmp_path / "reviewed.dll"
    plugin.write_bytes(b"reviewed-plugin")
    original_open = oracle_install.os.open
    original_close = oracle_install.os.close
    close_counts: dict[int, int] = {}

    def closing(descriptor: int) -> None:
        close_counts[descriptor] = close_counts.get(descriptor, 0) + 1
        original_close(descriptor)

    monkeypatch.setattr(oracle_install.os, "close", closing)
    if handoff == "child_snapshot":
        parent = oracle_install._open_absolute_directory(
            plugin.parent,
            "test plugin parent",
        )
        opened: list[int] = []

        def opening(
            name: object,
            flags: int,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> int:
            descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
            if name == plugin.name and dir_fd == parent.fd:
                opened.append(descriptor)
            return descriptor

        monkeypatch.setattr(oracle_install.os, "open", opening)
        monkeypatch.setattr(
            oracle_install,
            "_stable_snapshot_fd",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(primary),
        )
        try:
            with pytest.raises(BaseException) as caught:
                oracle_install._open_stable_child_file(
                    parent,
                    plugin.name,
                    "plugin source",
                )
            assert caught.value is primary
            assert len(opened) == 1
            assert close_counts[opened[0]] == 1
        finally:
            parent.close()
        return

    opened_parent: list[int] = []
    original_parent = oracle_install._open_absolute_directory

    def opening_parent(path: Path, label: str):
        handle = original_parent(path, label)
        opened_parent.append(handle.fd)
        return handle

    monkeypatch.setattr(
        oracle_install,
        "_open_absolute_directory",
        opening_parent,
    )
    monkeypatch.setattr(
        oracle_install,
        "_open_stable_child_file",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(primary),
    )
    with pytest.raises(BaseException) as caught:
        oracle_install._open_stable_absolute_file(plugin, "plugin source")
    assert caught.value is primary
    assert len(opened_parent) == 1
    assert close_counts[opened_parent[0]] == 1
```

- [ ] **Step 2: Run the focused RED test**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install.py \
  -k 'deploy_plugin_rolls_back_every_base_exception or deploy_plugin_rejects_source_substitution or deploy_plugin_delegates_retained_bytes or stable_plugin_source_acquisition'
```

Expected: collection or execution fails because the checkpoint/byte-delegate seams are absent, the source pathname is reopened, or an injected `BaseException` bypasses the current `Exception` rollback handler.

- [ ] **Step 3: Add exact checkpoint and `BaseException` ownership code**

Add this code beside the existing deploy helpers:

```python
_DEPLOY_PLUGIN_CHECKPOINTS = frozenset(
    {
        "after_staging_mkdir",
        "after_staging_plugin",
        "after_staging_config",
        "before_first_mutation",
        "after_plugin_publish",
        "after_config_publish",
        "after_manifest_publish",
        "before_final_validation",
        "after_final_validation",
    }
)


def _deploy_plugin_checkpoint(boundary: str) -> None:
    if boundary not in _DEPLOY_PLUGIN_CHECKPOINTS:
        raise AssertionError(f"unknown deploy-plugin checkpoint: {boundary}")


def _cleanup_deploy_staging(staging: Path | None) -> None:
    if staging is None:
        return
    if not staging.name.startswith(".ssr-oracle-deploy-staging-"):
        raise InstallError(f"refusing unexpected deploy staging path: {staging}")
    shutil.rmtree(staging)


def _note_installer_secondary(
    primary: BaseException,
    stage: str,
    secondary: BaseException,
) -> None:
    try:
        primary.add_note(
            f"secondary installer failure during {stage}: "
            f"{type(secondary).__name__}: {secondary}"
        )
    except BaseException:
        return


def _deploy_plugin_source_checkpoint(_boundary: str, _path: Path) -> None:
    return None


def _read_deploy_plugin_source_once(plugin: Path) -> tuple[bytes, str]:
    if not isinstance(plugin, Path) or plugin.suffix.lower() != ".dll":
        raise InstallError(f"plugin must have a .dll suffix: {plugin}")
    parent, name, descriptor, snapshot = _open_stable_absolute_file(
        plugin,
        "plugin source",
    )
    owned_descriptor: int | None = descriptor
    try:
        _deploy_plugin_source_checkpoint("after_descriptor_read", plugin)
        named_after = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
        descriptor_after = os.fstat(descriptor)
        expected = (
            snapshot.device,
            snapshot.inode,
            snapshot.size,
            snapshot.mode,
        )
        if (
            not stat.S_ISREG(named_after.st_mode)
            or (
                named_after.st_dev,
                named_after.st_ino,
                named_after.st_size,
                stat.S_IMODE(named_after.st_mode),
            )
            != expected
            or (
                descriptor_after.st_dev,
                descriptor_after.st_ino,
                descriptor_after.st_size,
                stat.S_IMODE(descriptor_after.st_mode),
            )
            != expected
        ):
            raise InstallError(f"plugin source changed while authenticating: {plugin}")
        _deploy_plugin_source_checkpoint("after_named_after", plugin)
        payload = snapshot.payload
        return payload, sha256(payload).hexdigest()
    finally:
        active = sys.exception()
        first_close: BaseException | None = None
        if owned_descriptor is not None:
            closing = owned_descriptor
            owned_descriptor = None
            try:
                os.close(closing)
            except BaseException as error:
                first_close = error
        try:
            parent.close()
        except BaseException as error:
            if first_close is None:
                first_close = error
            else:
                _note_installer_secondary(
                    first_close,
                    "plugin source parent close",
                    error,
                )
        if first_close is not None:
            if active is None:
                raise first_close
            _note_installer_secondary(
                active,
                "plugin source owner close",
                first_close,
            )


def deploy_plugin(
    game_root: Path,
    plugin: Path,
    config_text: str,
) -> InstallManifest:
    """Authenticate the plugin source once, then deploy retained bytes."""
    plugin_bytes, plugin_sha256 = _read_deploy_plugin_source_once(plugin)
    return _deploy_plugin_bytes(
        game_root,
        plugin_bytes,
        plugin_sha256,
        config_text,
    )
```

The public wrapper is safe only if the existing shared stable-open handoffs also treat process-level exceptions as ownership exits. Replace their `except Exception` blocks with these exact `BaseException` finalizers; each helper clears or consumes the owner exactly once, preserves the identical primary, and attaches a close failure without changing ordinary `InstallError` translation elsewhere:

```python
def _open_stable_child_file(
    parent: _DirectoryHandle,
    name: str,
    description: str,
) -> tuple[int, _StableFileSnapshot]:
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=parent.fd,
        )
    except OSError as exc:
        raise InstallError(
            f"{description} is not a safe regular file: "
            f"cannot open without following symlinks: {exc}"
        ) from exc
    try:
        return descriptor, _stable_snapshot_fd(descriptor, description)
    except BaseException as primary:
        try:
            os.close(descriptor)
        except BaseException as secondary:
            _note_installer_secondary(
                primary,
                f"{description} descriptor close",
                secondary,
            )
        raise


def _open_stable_absolute_file(
    path: Path,
    description: str,
) -> tuple[_DirectoryHandle, str, int, _StableFileSnapshot]:
    absolute = _lexical_absolute(path, description)
    parent = _open_absolute_directory(absolute.parent, f"{description} parent")
    try:
        descriptor, snapshot = _open_stable_child_file(
            parent,
            absolute.name,
            description,
        )
    except BaseException as primary:
        try:
            parent.close()
        except BaseException as secondary:
            _note_installer_secondary(
                primary,
                f"{description} parent close",
                secondary,
            )
        raise
    return parent, absolute.name, descriptor, snapshot
```

Refactor the existing complete deploy transaction into `_deploy_plugin_bytes` with the exact signature in `Interfaces`. Its first executable check requires `hashlib.sha256(plugin_bytes).hexdigest() == expected_plugin_sha256`, and its payload map uses `plugin_bytes` directly. The literal public wrapper above is the only pathname consumer; `_deploy_plugin_bytes` must not receive or reopen a source path. All existing public tests remain byte-identical.

Replace `_stage_deploy_payloads`'s `except OSError` with `except BaseException as primary`; clean the exact owned staging path with `_cleanup_deploy_staging`, attach a cleanup failure to the identical primary, translate only ordinary `OSError` to the legacy `InstallError`, and re-raise process-level primaries by identity. Call `after_staging_mkdir` after assigning `staging`, `after_staging_plugin` after the plugin fsync, and `after_staging_config` after the config fsync. Call the three staging checkpoints immediately after ownership is registered. Wrap staging plus publication in one `BaseException` transaction: on any boundary, roll back published state when mutation began, then attempt staging cleanup even if rollback failed. Preserve the identical process-level primary; attach rollback and staging-cleanup failures in that deterministic order. Replace the current inner publication block with this exact sequence:

```python
created_directories = _create_deploy_parents(
    game.root,
    tuple(targets.values()),
)
_deploy_plugin_checkpoint("before_first_mutation")
_atomic_write_bytes(
    targets[PLUGIN_RELATIVE_PATH],
    staged[PLUGIN_RELATIVE_PATH].read_bytes(),
)
_deploy_plugin_checkpoint("after_plugin_publish")
_atomic_write_bytes(
    targets[CONFIG_RELATIVE_PATH],
    staged[CONFIG_RELATIVE_PATH].read_bytes(),
)
_deploy_plugin_checkpoint("after_config_publish")
_write_manifest(game.root, updated)
_deploy_plugin_checkpoint("after_manifest_publish")
_deploy_plugin_checkpoint("before_final_validation")
validated = status_install(game.root)
if not validated.healthy or validated.manifest != updated:
    raise InstallError("deployed plugin failed final validation")
_deploy_plugin_checkpoint("after_final_validation")
return updated
```

Replace the transaction-owning handler with this exact code:

```diff
except BaseException as primary:
    rollback_error: BaseException | None = None
    try:
        _restore_deploy_state(
            targets=targets,
            snapshots=snapshots,
            manifest_path=manifest_path,
            manifest_snapshot=manifest_snapshot,
            created_directories=created_directories,
        )
    except BaseException as secondary:
        rollback_error = secondary
        _note_installer_secondary(primary, "plugin deploy rollback", secondary)
    try:
        _cleanup_deploy_staging(staging)
        staging = None
    except BaseException as secondary:
        _note_installer_secondary(primary, "plugin deploy staging cleanup", secondary)
    if not isinstance(primary, Exception):
        raise primary
    if rollback_error is not None:
        raise InstallError(f"deploy failed ({primary}); {rollback_error}") from primary
    if isinstance(primary, InstallError):
        raise
    if isinstance(primary, OSError):
        raise InstallError(f"cannot publish deploy payloads: {primary}") from primary
    raise
```

On the success path, cleanup the staging owner before return. The `before_first_mutation` checkpoint remains inside this owner-safe transaction, so a fault there cannot leak staging even though no live target has changed.

Do not include validation code outside the mutation transaction. For every descriptor-owning `close`, pre-clear before the syscall:

```python
descriptor = self.fd
self.fd = -1
os.close(descriptor)
```

- [ ] **Step 4: Run plugin-deployment GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install.py
```

Expected: all plugin-deployment and legacy installer tests pass; the injected object is preserved by identity in every parameter row.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the independently reviewed transaction**

```bash
git diff --check
git add src/ssr_env/oracle_install.py tests/test_oracle_install.py
git commit -m "fix: roll back interrupted plugin deployment"
```

### Task 2: Make patched-preloader deployment interruption-safe

**Files:**
- Modify: `src/ssr_env/oracle_install.py:1238-2860,4966-5488`
- Modify: `tests/test_oracle_install_compat.py:65-3299`

**Interfaces:**
- Preserves `deploy_preloader(game_root: Path, preloader: Path, provenance: Path, repo_root: Path | None = None) -> InstallManifest`.
- Consumes `_note_installer_secondary` from Task 1 and the existing `_deploy_preloader_checkpoint(boundary)` seam.
- Guarantees logical rollback and retention of any displaced pre-call inode exactly once at its original name or in the existing recovery graph.

- [ ] **Step 1: Add the concrete patched-deploy interruption test**

Add this parameterized test to `tests/test_oracle_install_compat.py`:

```python
def _compat_live_snapshot(root: Path) -> tuple[tuple[str, str, int, bytes], ...]:
    rows: list[tuple[str, str, int, bytes]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root)
        if relative.parts[0] == ".ssr-oracle-recovery" or relative.parts[0].startswith(
            ".ssr-oracle-compat-staging-"
        ):
            continue
        observed = path.lstat()
        if path.is_symlink():
            rows.append((relative.as_posix(), "symlink", stat.S_IMODE(observed.st_mode), os.readlink(path).encode()))
        elif path.is_dir():
            rows.append((relative.as_posix(), "directory", stat.S_IMODE(observed.st_mode), b""))
        elif path.is_file():
            rows.append((relative.as_posix(), "file", stat.S_IMODE(observed.st_mode), path.read_bytes()))
        else:
            rows.append((relative.as_posix(), "other", stat.S_IMODE(observed.st_mode), b""))
    return tuple(rows)


@pytest.mark.parametrize(
    "boundary",
    (
        "recovery_run_mkdir",
        "stage_active_fsync",
        "backup",
        "provenance",
        "active",
        "manifest",
        "idempotent_revalidate",
    ),
)
@pytest.mark.parametrize(
    "primary",
    (KeyboardInterrupt("stop"), SystemExit(74), GeneratorExit("stop")),
)
def test_deploy_preloader_rolls_back_every_base_exception(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    primary: BaseException,
) -> None:
    preloader, provenance = deploy_request
    before = _compat_live_snapshot(installed_official_game)
    before_status = status_install(installed_official_game)

    def interrupt(observed: str) -> None:
        if observed == boundary:
            raise primary

    monkeypatch.setattr(oracle_install, "_deploy_preloader_checkpoint", interrupt)
    with pytest.raises(BaseException) as caught:
        deploy_preloader(installed_official_game, preloader, provenance)

    assert caught.value is primary
    assert _compat_live_snapshot(installed_official_game) == before
    assert status_install(installed_official_game) == before_status
    recovery_parent = installed_official_game / ".ssr-oracle-recovery"
    if recovery_parent.exists():
        assert recovery_parent.is_dir() and not recovery_parent.is_symlink()
```

- [ ] **Step 2: Run the patched-deploy RED test**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install_compat.py \
  -k 'deploy_preloader_rolls_back_every_base_exception'
```

Expected: at least one `KeyboardInterrupt`, `SystemExit`, or `GeneratorExit` escapes before the existing rollback completes.

- [ ] **Step 3: Replace the complete `deploy_preloader` owner handler and finalizer**

Add `import sys` and `from collections.abc import Callable`. Replace only `deploy_preloader`'s outer `except Exception as exc` handler with this complete handler; parsing/validation helpers keep their existing exception scopes:

```diff
except BaseException as primary:
    details: list[str] = []
    if (
        root is not None
        and bep_in_ex is not None
        and core is not None
        and active_snapshot is not None
        and manifest_snapshot is not None
        and recovery is not None
        and (backup is not None or compat is not None)
    ):
        try:
            _rollback_preloader_deploy_fd(
                root=root,
                bep_in_ex=bep_in_ex,
                core=core,
                active_snapshot=active_snapshot,
                manifest_snapshot=manifest_snapshot,
                published_active=(published_active[0] if published_active else None),
                published_manifest=(published_manifest[0] if published_manifest else None),
                backup=backup,
                compat=compat,
                possibly_published=possibly_published,
                published_artifacts=published_artifacts,
                recovery=recovery,
            )
        except BaseException as secondary:
            _note_installer_secondary(primary, "patched-preloader rollback", secondary)
            details.append(str(secondary))
    if root is not None and staging is not None:
        staging_owned = staging
        staging = None
        try:
            _cleanup_compat_staging_fd(root, staging_owned, recovery)
        except BaseException as secondary:
            _note_installer_secondary(primary, "patched-preloader staging cleanup", secondary)
            details.append(f"staging cleanup failed: {secondary}")
    if not isinstance(primary, Exception):
        raise
    if details:
        raise InstallError(
            f"deploy-preloader failed ({primary}); " + "; ".join(details)
        ) from primary
    if isinstance(primary, InstallError):
        raise
    if isinstance(primary, (OSError, RuntimeError)):
        raise InstallError(f"deploy-preloader failed: {primary}") from primary
    raise
```

Define this local helper immediately before `deploy_preloader`'s outer `try`:

```python
def close_owned(stage: str, operation: Callable[[], None]) -> None:
    nonlocal close_primary
    try:
        operation()
    except BaseException as secondary:
        if active is not None:
            _note_installer_secondary(active, stage, secondary)
        elif close_primary is None:
            close_primary = secondary
        else:
            _note_installer_secondary(close_primary, stage, secondary)
```

Initialize `close_primary: BaseException | None = None` beside the helper. Add two RED registrations: one injects a close failure in the first owner with no active primary and proves every later owner still closes before that exact close error is raised; the other injects an active `KeyboardInterrupt` plus failures in two closes and proves the interruption retains identity while both close diagnostics are attached. In the complete `finally`, set `active = sys.exception()` before the first owner, execute every listed close, then end with:

```python
if active is None and close_primary is not None:
    raise close_primary
```

Replace the successful tail

```python
_cleanup_compat_staging_fd(root, staging, recovery)
staging = None
compat.close()
backup.close()
return updated
```

with:

```python
_cleanup_compat_staging_fd(root, staging, recovery)
staging = None
return updated
```

Replace the entire outer `finally` block with this resulting body. Every list owner is removed before its close, every nullable owner is cleared before its close, and every close has a fixed diagnostic label:

```diff
finally:
    active = sys.exception()
    while request_descriptors:
        descriptor = request_descriptors.pop()
        close_owned(
            f"patched-preloader request descriptor {descriptor} close",
            lambda descriptor=descriptor: os.close(descriptor),
        )
    while request_parents:
        parent = request_parents.pop()
        close_owned("patched-preloader request parent close", parent.close)
    if compat is not None:
        compat_owned = compat
        compat = None
        close_owned("patched-preloader compat close", compat_owned.close)
    if backup is not None:
        backup_owned = backup
        backup = None
        close_owned("patched-preloader backup close", backup_owned.close)
    if core is not None:
        core_owned = core
        core = None
        close_owned("patched-preloader core close", core_owned.close)
    if recovery is not None:
        recovery_owned = recovery
        recovery = None
        close_owned(
            "patched-preloader recovery close",
            lambda: _close_recovery(recovery_owned),
        )
    if recovery_parent is not None:
        recovery_parent_owned = recovery_parent
        recovery_parent = None
        close_owned(
            "patched-preloader recovery parent close",
            recovery_parent_owned.close,
        )
    if bep_in_ex is not None:
        bep_in_ex_owned = bep_in_ex
        bep_in_ex = None
        close_owned("patched-preloader BepInEx close", bep_in_ex_owned.close)
    if root is not None:
        root_owned = root
        root = None
        close_owned("patched-preloader root close", root_owned.close)
    if active is None and close_primary is not None:
        raise close_primary
```

- [ ] **Step 4: Run patched-preloader GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install_compat.py \
  -k 'deploy_preloader or status_install'
```

Expected: all selected tests pass with identical public results and manifest bytes.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the patched-deploy gate**

```bash
git diff --check
git add src/ssr_env/oracle_install.py tests/test_oracle_install_compat.py
git commit -m "fix: roll back interrupted preloader deployment"
```

### Task 3: Make official-preloader restoration interruption-safe

**Files:**
- Modify: `src/ssr_env/oracle_install.py:1582-4094`
- Modify: `tests/test_oracle_install_compat.py:3303-4970`

**Interfaces:**
- Preserves `restore_preloader(game_root: Path, repo_root: Path | None = None) -> tuple[InstallManifest, Path]`.
- Consumes `_note_installer_secondary` and the existing `_restore_preloader_checkpoint(boundary)`.
- Retains the existing stronger restore rule: every displaced inode is reachable exactly once through its original name or the returned recovery path.

- [ ] **Step 1: Add the concrete restore interruption matrix**

Add this test to `tests/test_oracle_install_compat.py`:

```python
@pytest.mark.parametrize(
    "boundary",
    (
        "restore_before_first_live_mutation",
        "restore_after_official_active_file_fsync",
        "restore_after_backup_move",
        "restore_after_provenance_move",
        "restore_after_active_verification",
        "restore_after_manifest_verification",
        "restore_after_final_status_verification",
    ),
)
@pytest.mark.parametrize(
    "primary",
    (KeyboardInterrupt("stop"), SystemExit(75), GeneratorExit("stop")),
)
def test_restore_preloader_preserves_primary_and_recovery(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    primary: BaseException,
) -> None:
    before = _compat_live_snapshot(installed_patched_game)
    before_status = status_install(installed_patched_game)

    def interrupt(observed: str) -> None:
        if observed == boundary:
            raise primary

    monkeypatch.setattr(oracle_install, "_restore_preloader_checkpoint", interrupt)
    with pytest.raises(BaseException) as caught:
        restore_preloader(installed_patched_game)

    assert caught.value is primary
    assert status_install(installed_patched_game) == before_status
    assert _compat_live_snapshot(installed_patched_game) == before
    recovery_parent = installed_patched_game / ".ssr-oracle-recovery"
    assert recovery_parent.is_dir() and not recovery_parent.is_symlink()
    assert all(path.is_dir() and not path.is_symlink() for path in recovery_parent.iterdir())
```

- [ ] **Step 2: Run the restore RED test**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install_compat.py \
  -k 'restore_preloader_preserves_primary_and_recovery'
```

Expected: an injected process-level exception bypasses at least one current `Exception` ownership handler.

- [ ] **Step 3: Harden only restore ownership handlers**

Replace `restore_preloader`'s current `except InstallError` block with this complete handler. It preserves the legacy `InstallError` messages while retaining the original identity of `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit`:

```diff
except BaseException as primary:
    if recovery is None:
        raise
    recovery_path = preflight[0] / ".ssr-oracle-recovery" / recovery.run_name
    rollback_error: BaseException | None = None
    containment_error: BaseException | None = None
    try:
        _restore_rollback(
            preflight,
            recovery,
            active_staging_name,
            manifest_staging_name,
            active_staging,
            manifest_staging,
        )
    except BaseException as secondary:
        rollback_error = secondary
        _note_installer_secondary(primary, "official-preloader rollback", secondary)
        try:
            _restore_contain_after_rollback_failure(
                preflight,
                recovery,
                active_staging_name,
                manifest_staging_name,
                active_staging,
                manifest_staging,
            )
        except BaseException as secondary:
            containment_error = secondary
            _note_installer_secondary(primary, "official-preloader containment", secondary)
    if not isinstance(primary, InstallError):
        raise
    if rollback_error is None:
        raise InstallError(
            f"{primary}; rollback succeeded; recovery retained at {recovery_path}"
        ) from primary
    containment_detail = (
        "" if containment_error is None else f"; containment failed: {containment_error}"
    )
    raise InstallError(
        f"{primary}; rollback failed: {rollback_error}; "
        f"recovery retained at {recovery_path}{containment_detail}"
    ) from rollback_error
```

Replace the entire `finally` block with this complete body; define the same accumulator-based local `close_owned` helper shown in Task 2 immediately before the outer `try`. Add the same two RED registrations for first-close failure without a primary and two close failures with an active `SystemExit`; all preflight/recovery owners must be attempted and the first close failure or original primary must retain identity:

```diff
finally:
    active = sys.exception()
    if recovery is not None:
        recovery_owned = recovery
        recovery = None
        close_owned(
            "official-preloader recovery close",
            lambda: _restore_close_recovery(recovery_owned),
        )
    preflight_owned = preflight
    preflight = None
    close_owned(
        "official-preloader preflight close",
        lambda: _restore_close_preflight(preflight_owned),
    )
    if active is None and close_primary is not None:
        raise close_primary
```

There are no other transaction-owner handler changes in this task.

- [ ] **Step 4: Run the complete installer GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_install.py tests/test_oracle_install_compat.py
```

Expected: every installer test passes; public signatures, normal exceptions, CLI text, and manifest bytes remain unchanged.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the restore gate**

```bash
git diff --check
git add src/ssr_env/oracle_install.py tests/test_oracle_install_compat.py
git commit -m "fix: preserve interrupted preloader restoration"
```

### Task 4: Expose changed canonical-log payloads without changing boot behavior

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:199-246,1160-1276`
- Modify: `tests/test_oracle_boot.py`

**Interfaces:**
- Produces frozen `_ObservedLogPayloads(canonical_payload, error_payloads, issues, observed_failures)`.
- Produces `_observe_changed_log_payloads(game_root: Path, before: tuple[LogFingerprint, ...]) -> _ObservedLogPayloads`.
- Preserves `_observe_boot_logs(...)` exactly as a pure projection to its existing four-tuple.

- [ ] **Step 1: Add exact raw-payload RED tests**

Add these tests beside the existing boot-log observation tests:

```python
def test_changed_log_payloads_return_one_canonical_and_all_error_bytes(
    tmp_path: Path,
) -> None:
    game = tmp_path / "game"
    canonical = game / "BepInEx" / "LogOutput.log"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(b"old\n")
    before = fingerprint_preloader_logs(game)
    canonical.write_bytes(
        b"[Message:   BepInEx] BepInEx 5.4.23.5 - SSR\n"
        b"[Info   :   BepInEx] Detected Unity version: v2018.4.25f1\n"
        b"[Info   :SSR Executable Oracle] SSR oracle boot probe loaded\n"
    )
    fallback = game / "BepInEx" / "LogOutput.log.1"
    fallback.write_bytes(b"fallback failure\n")

    observed = oracle_boot._observe_changed_log_payloads(
        game,
        before,
    )

    assert observed.canonical_payload == canonical.read_bytes()
    assert observed.error_payloads == (
        canonical.read_bytes(),
        b"fallback failure\n",
    )
    assert observed.issues == ("observed fallback failure log: BepInEx/LogOutput.log.1",)
    assert tuple(item.kind for item in observed.observed_failures) == ("fallback",)


def test_observe_boot_logs_remains_the_exact_projection(
    tmp_path: Path,
) -> None:
    game = tmp_path / "game"
    canonical = game / "BepInEx" / "LogOutput.log"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes(b"old\n")
    before = fingerprint_preloader_logs(game)
    canonical.write_bytes(
        b"[Message:   BepInEx] BepInEx 5.4.23.5 - SSR\n"
        b"[Info   :   BepInEx] Detected Unity version: v2018.4.25f1\n"
        b"[Info   :SSR Executable Oracle] SSR oracle boot probe loaded\n"
    )
    raw = oracle_boot._observe_changed_log_payloads(game, before)
    projected = oracle_boot._observe_boot_logs(game, before)
    assert projected == (
        ("BepInEx 5.4.23.5", "Unity v2018.4.25f1", "SSR oracle boot probe loaded"),
        (),
        raw.issues,
        raw.observed_failures,
    )
```

- [ ] **Step 2: Run changed-log RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py -k 'changed_log_payloads or exact_projection'
```

Expected: `_ObservedLogPayloads` or `_observe_changed_log_payloads` is missing.

- [ ] **Step 3: Extract the exact payload-returning implementation**

Add the model beside `_ObservedFailureLog`:

```python
@dataclass(frozen=True, slots=True)
class _ObservedLogPayloads:
    canonical_payload: bytes | None
    error_payloads: tuple[bytes, ...]
    issues: tuple[str, ...]
    observed_failures: tuple[_ObservedFailureLog, ...]
```

Apply this exact hunk to the existing scanner; its loop body between the shown signature and tail anchors is unchanged:

```diff
-def _observe_boot_logs(
+def _observe_changed_log_payloads(
     game_root: Path,
     before: tuple[LogFingerprint, ...],
-) -> tuple[
-    tuple[str, ...],
-    tuple[str, ...],
-    tuple[str, ...],
-    tuple[_ObservedFailureLog, ...],
-]:
+) -> _ObservedLogPayloads:
@@
     finally:
         scan.close()
-    markers = tuple(
-        marker
-        for marker in _REQUIRED_BOOT_MARKERS
-        if any(
-            _payload_contains_boot_marker(payload, marker)
-            for payload in canonical_payloads
-        )
-    )
-    errors = tuple(
-        marker
-        for marker in _BOOT_ERROR_MARKERS
-        if any(
-            marker.encode("ascii") in payload
-            for payload in error_payloads
-        )
-    )
-    return markers, errors, tuple(issues), tuple(observed_failures)
+    if len(canonical_payloads) > 1:
+        raise BootProbeError("multiple changed canonical boot logs")
+    return _ObservedLogPayloads(
+        canonical_payload=(canonical_payloads[0] if canonical_payloads else None),
+        error_payloads=tuple(error_payloads),
+        issues=tuple(issues),
+        observed_failures=tuple(observed_failures),
+    )
```

Reintroduce `_observe_boot_logs` with the unchanged public-private contract:

```python
def _observe_boot_logs(
    game_root: Path,
    before: tuple[LogFingerprint, ...],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[_ObservedFailureLog, ...],
]:
    observed = _observe_changed_log_payloads(game_root, before)
    markers = tuple(
        marker
        for marker in _REQUIRED_BOOT_MARKERS
        if observed.canonical_payload is not None
        and _payload_contains_boot_marker(observed.canonical_payload, marker)
    )
    errors = tuple(
        marker
        for marker in _BOOT_ERROR_MARKERS
        if any(marker.encode("ascii") in payload for payload in observed.error_payloads)
    )
    return markers, errors, observed.issues, observed.observed_failures
```

Run this non-pytest AST assertion after the hunk and wrapper are present. It proves there is one raw scanner, one compatibility projection, and no second scanner hidden in the wrapper:

```python
import ast
from pathlib import Path

source = Path("src/ssr_env/oracle_boot.py").read_text()
tree = ast.parse(source)
functions = {
    node.name: ast.get_source_segment(source, node)
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
raw = functions["_observe_changed_log_payloads"]
projection = functions["_observe_boot_logs"]
assert source.count("def _observe_changed_log_payloads(") == 1
assert source.count("def _observe_boot_logs(") == 1
assert raw.count("_scan_preloader_logs(") == 1
assert raw.count("_read_monitored_log(") == 1
assert raw.count("return _ObservedLogPayloads(") == 1
assert "_REQUIRED_BOOT_MARKERS" not in raw
assert projection.count("_observe_changed_log_payloads(") == 1
assert "_scan_preloader_logs(" not in projection
assert projection.count("return markers, errors, observed.issues, observed.observed_failures") == 1
```

- [ ] **Step 4: Run the complete boot observer GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py
```

Expected: all boot tests pass and existing `_observe_boot_logs` callers receive identical values.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the log seam**

```bash
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "refactor: expose changed boot log payloads"
```

### Task 5A: Define the closed auxiliary-evidence schema

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:97-159,3401-4008`
- Modify: `tests/test_oracle_boot.py`

**Interfaces:**
- Produces frozen `_AuxiliaryEvidenceSpec` and accepts only the exact config and trace shapes below.
- Adds `kind` and `max_bytes` to `_RetainedEvidenceFile`; marker/error grading still reads only `kind == "boot_log"`.

- [ ] **Step 1: Add the closed-shape RED matrix**

Add this concrete table to `tests/test_oracle_boot.py`:

```python
def _aux_specs(
    config_identity: tuple[int, int, int, int, int],
    config_sha256: str,
) -> tuple[oracle_boot._AuxiliaryEvidenceSpec, ...]:
    return (
        oracle_boot._AuxiliaryEvidenceSpec(
            relative_path=Path("passive.cfg"),
            kind="passive_config",
            required=True,
            max_bytes=64 * 1024,
            expected_identity=config_identity,
            expected_sha256=config_sha256,
        ),
        oracle_boot._AuxiliaryEvidenceSpec(
            relative_path=Path("passive-trace.ndjson"),
            kind="passive_trace",
            required=False,
            max_bytes=128 * 1024 * 1024,
            expected_identity=None,
            expected_sha256=None,
        ),
    )


@pytest.mark.parametrize(
    "changes",
    (
        {"relative_path": Path("passive-trace.ndjson")},
        {"kind": "passive_trace"},
        {"required": False},
        {"max_bytes": 128 * 1024 * 1024},
        {"expected_identity": None},
        {"expected_sha256": None},
    ),
)
def test_auxiliary_config_rejects_every_noncanonical_shape(changes: dict[str, object]) -> None:
    values: dict[str, object] = {
        "relative_path": Path("passive.cfg"),
        "kind": "passive_config",
        "required": True,
        "max_bytes": 64 * 1024,
        "expected_identity": (1, 2, stat.S_IFREG | 0o600, 9, 10),
        "expected_sha256": "a" * 64,
    }
    values.update(changes)
    with pytest.raises(ValueError, match="canonical auxiliary evidence shape"):
        oracle_boot._AuxiliaryEvidenceSpec(**values)


@pytest.mark.parametrize(
    ("identity", "digest"),
    ((None, "b" * 64), ((1, 2, stat.S_IFREG | 0o600, 9, 10), None)),
)
def test_auxiliary_trace_expected_metadata_is_both_or_neither(
    identity: tuple[int, int, int, int, int] | None,
    digest: str | None,
) -> None:
    with pytest.raises(ValueError, match="canonical auxiliary evidence shape"):
        oracle_boot._AuxiliaryEvidenceSpec(
            Path("passive-trace.ndjson"),
            "passive_trace",
            False,
            128 * 1024 * 1024,
            identity,
            digest,
        )
```

- [ ] **Step 2: Run the schema RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'auxiliary_config_rejects or auxiliary_trace_expected_metadata'
```

Expected: `_AuxiliaryEvidenceSpec` is missing or accepts at least one malformed cross-pair.

- [ ] **Step 3: Implement the exact typed auxiliary seam**

Add these definitions:

```python
@dataclass(frozen=True, slots=True)
class _AuxiliaryEvidenceSpec:
    relative_path: Path
    kind: Literal["passive_config", "passive_trace"]
    required: bool
    max_bytes: int
    expected_identity: tuple[int, int, int, int, int] | None
    expected_sha256: str | None

    def __post_init__(self) -> None:
        config_shape = (
            self.relative_path == Path("passive.cfg")
            and self.kind == "passive_config"
            and self.required is True
            and self.max_bytes == 64 * 1024
            and self.expected_identity is not None
            and self.expected_sha256 is not None
        )
        trace_shape = (
            self.relative_path == Path("passive-trace.ndjson")
            and self.kind == "passive_trace"
            and self.required is False
            and self.max_bytes == 128 * 1024 * 1024
            and ((self.expected_identity is None) == (self.expected_sha256 is None))
        )
        if not (config_shape or trace_shape):
            raise ValueError("invalid canonical auxiliary evidence shape")
        if self.expected_sha256 is not None and re.fullmatch(
            r"[0-9a-f]{64}", self.expected_sha256
        ) is None:
            raise ValueError("invalid auxiliary evidence SHA-256")


@dataclass(slots=True)
class _RetainedEvidenceFile:
    relative_path: Path
    descriptor: int
    identity: tuple[int, int, int, int, int]
    fingerprint: LogFingerprint
    kind: Literal["boot_log", "passive_config", "passive_trace"] = "boot_log"
    max_bytes: int = 64 * 1024 * 1024

    def close(self) -> None:
        if self.descriptor >= 0:
            descriptor = self.descriptor
            self.descriptor = -1
            os.close(descriptor)
```

- [ ] **Step 4: Run the schema GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py -k 'auxiliary_config_rejects or auxiliary_trace_expected_metadata'
```

Expected: only the exact required config shape and the optional trace shape construct.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the closed schema**

```bash
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "refactor: define closed auxiliary evidence specs"
```

### Task 5B: Secure an auxiliary file once and read it twice without mutation

**Files:**
- Modify: `src/ssr_env/oracle_boot.py`
- Modify: `tests/test_oracle_boot.py`

**Interfaces:**
- Produces `_open_auxiliary_evidence(...) -> _RetainedEvidenceFile | None`.
- Validates name/descriptor identity and regular-file type before an at-most-once `fchmod` when mode is not already `0600`, establishes the seal afterward, and performs two byte-identical mutation-free reads. An upstream-sealed `0600` trace/config is never chmodded again, so its ctime pin remains valid.

- [ ] **Step 1: Add ordering, stability, and substitution RED tests**

Add these complete twelve items (`2 + 4 + 3 + 2 + 1`):

```python
import errno
import hashlib


def _trace_aux_spec() -> oracle_boot._AuxiliaryEvidenceSpec:
    return oracle_boot._AuxiliaryEvidenceSpec(
        Path("passive-trace.ndjson"), "passive_trace", False,
        128 * 1024 * 1024, None, None,
    )


def _open_test_evidence(tmp_path: Path) -> tuple[Path, oracle_boot._DirectoryHandle]:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    return evidence, oracle_boot._open_absolute_directory(evidence, "test evidence")


@pytest.mark.parametrize(
    ("initial_mode", "expected_events"),
    (
        (0o644, ("named_validate", "fstat_validate", "fchmod", "named_seal", "fstat_seal", "read_1", "read_2")),
        (0o600, ("named_validate", "fstat_validate", "named_seal", "fstat_seal", "read_1", "read_2")),
    ),
)
def test_auxiliary_order_seals_once_then_reads_twice_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    initial_mode: int,
    expected_events: tuple[str, ...],
) -> None:
    evidence, handle = _open_test_evidence(tmp_path)
    path = evidence / "passive-trace.ndjson"
    payload = b'{"partial":true}\n'
    path.write_bytes(payload)
    path.chmod(initial_mode)
    events: list[str] = []
    state = {"named": 0, "descriptor": 0, "read": 0, "in_read": False, "sealed": False}
    original_stat = oracle_boot.os.stat
    original_fstat = oracle_boot.os.fstat
    original_fchmod = oracle_boot.os.fchmod
    original_read = oracle_boot._read_auxiliary_pass

    def traced_stat(name: object, *args: object, **kwargs: object) -> os.stat_result:
        observed = original_stat(name, *args, **kwargs)
        if not state["in_read"] and os.fspath(name) == path.name:
            events.append("named_validate" if state["named"] == 0 else "named_seal")
            state["named"] += 1
        return observed

    def traced_fstat(descriptor: int) -> os.stat_result:
        observed = original_fstat(descriptor)
        if not state["in_read"]:
            events.append("fstat_validate" if state["descriptor"] == 0 else "fstat_seal")
            state["descriptor"] += 1
            if state["descriptor"] == 2:
                state["sealed"] = True
        return observed

    def traced_fchmod(descriptor: int, mode: int) -> None:
        assert state["sealed"] is False and mode == 0o600
        events.append("fchmod")
        original_fchmod(descriptor, mode)

    def traced_read(*args: object, **kwargs: object) -> tuple[bytes, str]:
        state["read"] += 1
        events.append(f"read_{state['read']}")
        state["in_read"] = True
        try:
            return original_read(*args, **kwargs)
        finally:
            state["in_read"] = False

    def forbidden_post_seal_mutation(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("mutation after auxiliary seal")

    monkeypatch.setattr(oracle_boot.os, "stat", traced_stat)
    monkeypatch.setattr(oracle_boot.os, "fstat", traced_fstat)
    monkeypatch.setattr(oracle_boot.os, "fchmod", traced_fchmod)
    monkeypatch.setattr(oracle_boot, "_read_auxiliary_pass", traced_read)
    monkeypatch.setattr(oracle_boot.os, "write", forbidden_post_seal_mutation)
    monkeypatch.setattr(oracle_boot.os, "rename", forbidden_post_seal_mutation)
    monkeypatch.setattr(oracle_boot.os, "unlink", forbidden_post_seal_mutation)
    retained = None
    try:
        retained = oracle_boot._open_auxiliary_evidence(evidence, handle, _trace_aux_spec())
        assert retained is not None
        assert retained.fingerprint.sha256 == hashlib.sha256(payload).hexdigest()
        assert tuple(events) == expected_events
    finally:
        if retained is not None:
            retained.close()
        handle.close()


@pytest.mark.parametrize(
    "case",
    ("before_validation", "after_seal_before_first", "between_passes_name", "between_passes_same_inode_bytes"),
)
def test_auxiliary_substitution_or_same_size_byte_drift_is_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    evidence, handle = _open_test_evidence(tmp_path)
    path = evidence / "passive-trace.ndjson"
    path.write_bytes(b"AAAA")
    path.chmod(0o600)
    original_open = oracle_boot.os.open
    original_read = oracle_boot._read_auxiliary_pass
    reads = 0

    def replace_name(payload: bytes) -> None:
        held = evidence / f"held-{case}"
        path.rename(held)
        path.write_bytes(payload)
        path.chmod(0o600)

    def opening(name: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if case == "before_validation" and name == path.name and dir_fd == handle.fd:
            replace_name(b"BBBB")
        return descriptor

    def reading(*args: object, **kwargs: object) -> tuple[bytes, str]:
        nonlocal reads
        if case == "after_seal_before_first" and reads == 0:
            replace_name(b"BBBB")
        result = original_read(*args, **kwargs)
        reads += 1
        if reads == 1 and case == "between_passes_name":
            replace_name(b"BBBB")
        elif reads == 1 and case == "between_passes_same_inode_bytes":
            before = path.stat(follow_symlinks=False)
            path.write_bytes(b"BBBB")
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns), follow_symlinks=False)
        return result

    monkeypatch.setattr(oracle_boot.os, "open", opening)
    monkeypatch.setattr(oracle_boot, "_read_auxiliary_pass", reading)
    try:
        with pytest.raises(oracle_boot.BootProbeError, match="changed|disagree|unstable"):
            oracle_boot._open_auxiliary_evidence(evidence, handle, _trace_aux_spec())
    finally:
        handle.close()


@pytest.mark.parametrize("kind", ("symlink", "fifo", "oversize"))
def test_auxiliary_special_file_or_oversize_is_rejected(tmp_path: Path, kind: str) -> None:
    evidence, handle = _open_test_evidence(tmp_path)
    path = evidence / "passive-trace.ndjson"
    if kind == "symlink":
        target = evidence / "target"
        target.write_bytes(b"trace")
        path.symlink_to(target.name)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        with path.open("wb") as stream:
            stream.truncate(128 * 1024 * 1024 + 1)
    try:
        with pytest.raises(oracle_boot.BootProbeError, match="auxiliary|bounded|unsafe"):
            oracle_boot._open_auxiliary_evidence(evidence, handle, _trace_aux_spec())
    finally:
        handle.close()


@pytest.mark.parametrize("bad_pin", ("identity", "sha256"))
def test_auxiliary_two_pass_expected_pin_mismatch_closes_and_fails(tmp_path: Path, bad_pin: str) -> None:
    evidence, handle = _open_test_evidence(tmp_path)
    path = evidence / "passive.cfg"
    payload = b"[Oracle]\nMode = passive\n"
    path.write_bytes(payload)
    path.chmod(0o600)
    identity = oracle_boot._stat_identity(path.stat(follow_symlinks=False))
    digest = hashlib.sha256(payload).hexdigest()
    if bad_pin == "identity":
        identity = (identity[0], identity[1] + 1, *identity[2:])
    else:
        digest = "0" * 64 if digest != "0" * 64 else "1" * 64
    spec = oracle_boot._AuxiliaryEvidenceSpec(
        Path("passive.cfg"), "passive_config", True, 64 * 1024, identity, digest,
    )
    try:
        with pytest.raises(oracle_boot.BootProbeError, match="identity|hash"):
            oracle_boot._open_auxiliary_evidence(evidence, handle, spec)
    finally:
        handle.close()


def test_auxiliary_two_pass_primary_survives_descriptor_close_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence, handle = _open_test_evidence(tmp_path)
    path = evidence / "passive-trace.ndjson"
    path.write_bytes(b"trace")
    path.chmod(0o600)
    primary = RuntimeError("read failed")
    original_open = oracle_boot.os.open
    original_close = oracle_boot.os.close
    opened: list[int] = []

    def opening(name: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if name == path.name and dir_fd == handle.fd:
            opened.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if opened and descriptor == opened[0]:
            original_close(descriptor)
            raise OSError("close failed")
        original_close(descriptor)

    monkeypatch.setattr(oracle_boot.os, "open", opening)
    monkeypatch.setattr(
        oracle_boot, "_read_auxiliary_pass", lambda *_args, **_kwargs: (_ for _ in ()).throw(primary)
    )
    monkeypatch.setattr(oracle_boot.os, "close", closing)
    try:
        with pytest.raises(RuntimeError) as caught:
            oracle_boot._open_auxiliary_evidence(evidence, handle, _trace_aux_spec())
        assert caught.value is primary
        assert any("close failed" in note for note in getattr(primary, "__notes__", ()))
        with pytest.raises(OSError) as closed:
            os.fstat(opened[0])
        assert closed.value.errno == errno.EBADF
    finally:
        handle.close()
```

- [ ] **Step 2: Run the secure-reader RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'auxiliary_order or auxiliary_two_pass or auxiliary_substitution or auxiliary_special_file'
```

Expected: the old opener chmods before validation and performs only one authenticated read.

- [ ] **Step 3: Add the complete one-time seal and mutation-free pass**

Add this helper before the opener:

```python
@dataclass(frozen=True, slots=True)
class _AuxiliarySeal:
    identity: tuple[int, int, int, int, int]
    size: int


def _read_auxiliary_pass(
    evidence_handle: _DirectoryHandle,
    spec: _AuxiliaryEvidenceSpec,
    descriptor: int,
    seal: _AuxiliarySeal,
) -> tuple[bytes, str]:
    named_before = os.stat(
        spec.relative_path.name,
        dir_fd=evidence_handle.fd,
        follow_symlinks=False,
    )
    before = os.fstat(descriptor)
    if (
        _stat_identity(named_before) != seal.identity
        or _stat_identity(before) != seal.identity
        or before.st_size != seal.size
    ):
        raise BootProbeError(f"auxiliary evidence changed before read: {spec.relative_path}")
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = os.read(descriptor, min(1024 * 1024, spec.max_bytes + 1 - size))
        if not chunk:
            break
        size += len(chunk)
        if size > spec.max_bytes:
            raise BootProbeError(f"auxiliary evidence exceeds byte limit: {spec.relative_path}")
        chunks.append(chunk)
        digest.update(chunk)
    after = os.fstat(descriptor)
    named_after = os.stat(
        spec.relative_path.name,
        dir_fd=evidence_handle.fd,
        follow_symlinks=False,
    )
    if (
        _stat_identity(after) != seal.identity
        or _stat_identity(named_after) != seal.identity
        or after.st_size != seal.size
        or size != seal.size
    ):
        raise BootProbeError(f"auxiliary evidence changed during read: {spec.relative_path}")
    return b"".join(chunks), digest.hexdigest()
```

Replace the descriptor-relative opener with this complete body:

```python
def _open_auxiliary_evidence(
    evidence_dir: Path,
    evidence_handle: _DirectoryHandle,
    spec: _AuxiliaryEvidenceSpec,
) -> _RetainedEvidenceFile | None:
    try:
        descriptor = os.open(
            spec.relative_path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=evidence_handle.fd,
        )
    except FileNotFoundError:
        if spec.required:
            raise BootProbeError(
                f"required auxiliary evidence is missing: {spec.relative_path}"
            )
        return None
    try:
        named_validate = os.stat(
            spec.relative_path.name,
            dir_fd=evidence_handle.fd,
            follow_symlinks=False,
        )
        descriptor_validate = os.fstat(descriptor)
        if (
            not stat.S_ISREG(named_validate.st_mode)
            or not stat.S_ISREG(descriptor_validate.st_mode)
            or _stat_identity(named_validate) != _stat_identity(descriptor_validate)
        ):
            raise BootProbeError(f"auxiliary evidence name changed: {spec.relative_path}")
        if descriptor_validate.st_size > spec.max_bytes:
            raise BootProbeError(f"unsafe auxiliary evidence: {spec.relative_path}")
        if stat.S_IMODE(descriptor_validate.st_mode) != 0o600:
            os.fchmod(descriptor, 0o600)
        named_seal = os.stat(
            spec.relative_path.name,
            dir_fd=evidence_handle.fd,
            follow_symlinks=False,
        )
        descriptor_seal = os.fstat(descriptor)
        identity = _stat_identity(descriptor_seal)
        if identity != _stat_identity(named_seal) or not stat.S_ISREG(descriptor_seal.st_mode):
            raise BootProbeError(f"auxiliary evidence changed while securing: {spec.relative_path}")
        seal = _AuxiliarySeal(identity, descriptor_seal.st_size)
        first_bytes, first_sha256 = _read_auxiliary_pass(
            evidence_handle, spec, descriptor, seal
        )
        second_bytes, second_sha256 = _read_auxiliary_pass(
            evidence_handle, spec, descriptor, seal
        )
        if first_bytes != second_bytes or first_sha256 != second_sha256:
            raise BootProbeError(f"auxiliary evidence was unstable: {spec.relative_path}")
        if spec.expected_identity is not None and identity != spec.expected_identity:
            raise BootProbeError(f"auxiliary evidence identity changed: {spec.relative_path}")
        observed_sha256 = second_sha256
        if spec.expected_sha256 is not None and observed_sha256 != spec.expected_sha256:
            raise BootProbeError(f"auxiliary evidence hash changed: {spec.relative_path}")
        return _RetainedEvidenceFile(
            relative_path=spec.relative_path,
            descriptor=descriptor,
            identity=identity,
            fingerprint=LogFingerprint(
                path=evidence_dir / spec.relative_path,
                file_type="regular",
                inode=descriptor_seal.st_ino,
                size=descriptor_seal.st_size,
                mtime_ns=descriptor_seal.st_mtime_ns,
                sha256=observed_sha256,
            ),
            kind=spec.kind,
            max_bytes=spec.max_bytes,
        )
    except BaseException as primary:
        try:
            os.close(descriptor)
        except BaseException as secondary:
            primary.add_note(f"secondary auxiliary descriptor close failure: {secondary}")
        raise
```

- [ ] **Step 4: Run the secure-reader GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'auxiliary_order or auxiliary_two_pass or auxiliary_substitution or auxiliary_special_file'
```

Expected: validation precedes the sole chmod; both reads are mutation-free and byte-identical; all descriptors close on every error.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the secure auxiliary reader**

```bash
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "refactor: seal auxiliary evidence once"
```

### Task 5C: Collect auxiliary evidence into a caller-owned directory

**Files:**
- Modify: `src/ssr_env/oracle_boot.py`
- Modify: `tests/test_oracle_boot.py`

**Interfaces:**
- Produces `_collect_boot_evidence_into(...) -> _RetainedBootEvidence` without consuming the caller's handle.
- Required `passive.cfg` absence fails; optional trace absence succeeds. Present trace bytes are retained even when malformed.
- Preserves `_collect_boot_evidence_retained`, `collect_boot_evidence`, and their 64 MiB boot-log behavior.

- [ ] **Step 1: Add collection, absence, and handle-ownership RED tests**

Add these four complete items (`2 + 1 + 1`):

```python
def _caller_owned_aux_setup(
    tmp_path: Path,
    trace_payload: bytes | None,
) -> tuple[Path, Path, oracle_boot._DirectoryHandle, tuple[oracle_boot._AuxiliaryEvidenceSpec, ...]]:
    game = tmp_path / "game"
    game.mkdir()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    config = evidence / "passive.cfg"
    config_payload = b"[Oracle]\nMode = passive\n"
    config.write_bytes(config_payload)
    config.chmod(0o600)
    if trace_payload is not None:
        trace = evidence / "passive-trace.ndjson"
        trace.write_bytes(trace_payload)
        trace.chmod(0o600)
    handle = oracle_boot._open_absolute_directory(evidence, "test evidence")
    specs = _aux_specs(
        oracle_boot._stat_identity(config.stat(follow_symlinks=False)),
        hashlib.sha256(config_payload).hexdigest(),
    )
    return game, evidence, handle, specs


@pytest.mark.parametrize("trace_payload", (None, b'{"malformed":'))
def test_collect_into_requires_config_and_optionally_retains_raw_trace(
    tmp_path: Path,
    trace_payload: bytes | None,
) -> None:
    game, evidence, caller, specs = _caller_owned_aux_setup(tmp_path, trace_payload)
    caller_fd = caller.fd
    retained = oracle_boot._collect_boot_evidence_into(
        (), game, evidence, caller,
        expected_inventory=oracle_boot._capture_boot_log_inventory(game),
        run_contract=None,
        observed_failures=(),
        auxiliary_specs=specs,
    )
    try:
        by_kind = {item.kind: item for item in retained.files}
        assert set(by_kind) == ({"passive_config"} if trace_payload is None else {"passive_config", "passive_trace"})
        if trace_payload is not None:
            raw, _fingerprint = oracle_boot._read_retained_evidence_file(
                retained, by_kind["passive_trace"]
            )
            assert raw == trace_payload
        assert os.fstat(caller_fd)
    finally:
        retained.close()
        assert os.fstat(caller_fd)
        caller.close()


def test_collect_into_rejects_missing_required_config(tmp_path: Path) -> None:
    game = tmp_path / "game"
    game.mkdir()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    caller = oracle_boot._open_absolute_directory(evidence, "test evidence")
    specs = _aux_specs((1, 2, stat.S_IFREG | 0o600, 0, 0), "a" * 64)
    try:
        with pytest.raises(oracle_boot.BootProbeError, match="required auxiliary evidence is missing"):
            oracle_boot._collect_boot_evidence_into(
                (), game, evidence, caller,
                expected_inventory=oracle_boot._capture_boot_log_inventory(game),
                run_contract=None,
                observed_failures=(),
                auxiliary_specs=specs,
            )
        assert os.fstat(caller.fd)
    finally:
        caller.close()


def test_collect_into_caller_handle_survives_core_failure_and_closes_only_the_duplicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game, evidence, caller, specs = _caller_owned_aux_setup(tmp_path, None)
    original_duplicate = oracle_boot._duplicate_directory_handle
    duplicates: list[oracle_boot._DirectoryHandle] = []
    primary = RuntimeError("injected core scan failure")

    def duplicate(handle: oracle_boot._DirectoryHandle) -> oracle_boot._DirectoryHandle:
        owned = original_duplicate(handle)
        duplicates.append(owned)
        return owned

    monkeypatch.setattr(oracle_boot, "_duplicate_directory_handle", duplicate)
    monkeypatch.setattr(
        oracle_boot, "_scan_preloader_logs", lambda _game: (_ for _ in ()).throw(primary)
    )
    try:
        with pytest.raises(RuntimeError) as caught:
            oracle_boot._collect_boot_evidence_into(
                (), game, evidence, caller,
                expected_inventory=None,
                run_contract=None,
                observed_failures=(),
                auxiliary_specs=specs,
            )
        assert caught.value is primary
        assert len(duplicates) == 1 and duplicates[0].fd == -1
        assert os.fstat(caller.fd)
    finally:
        caller.close()
```

- [ ] **Step 2: Run the caller-owned collection RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py \
  -k 'collect_into_requires_config or optionally_retains_raw_trace or missing_required_config or caller_handle'
```

Expected: `_collect_boot_evidence_into` is missing or mishandles required absence/ownership.

- [ ] **Step 3: Implement caller-owned and legacy wrappers**

Apply these closed hunks to the existing collector. Every changed line is shown; all lines between the hunk anchors remain byte-for-byte unchanged:

```diff
-def _collect_boot_evidence_retained(
+def _collect_boot_evidence_core(
     before: tuple[LogFingerprint, ...],
     game_root: Path,
-    evidence_root: Path,
     *,
+    evidence_dir: Path,
+    evidence_handle: _DirectoryHandle,
     expected_inventory: _BootLogInventory | None,
-    run_contract: _ValidatedBootLogContract | None = None,
-    observed_failures: tuple[_ObservedFailureLog, ...] = (),
+    run_contract: _ValidatedBootLogContract | None,
+    observed_failures: tuple[_ObservedFailureLog, ...],
+    auxiliary_specs: tuple[_AuxiliaryEvidenceSpec, ...],
 ) -> _RetainedBootEvidence:
     game = _validate_directory(game_root, "game root")
+    if evidence_handle.fd < 0 or evidence_handle.path != evidence_dir:
+        raise BootProbeError("owned evidence handle does not match evidence directory")
+    named_evidence = os.stat(evidence_dir, follow_symlinks=False)
+    descriptor_evidence = os.fstat(evidence_handle.fd)
+    if (
+        not stat.S_ISDIR(named_evidence.st_mode)
+        or _stat_identity(named_evidence) != _stat_identity(descriptor_evidence)
+        or (descriptor_evidence.st_dev, descriptor_evidence.st_ino)
+        != (evidence_handle.device, evidence_handle.inode)
+    ):
+        raise BootProbeError("owned evidence directory changed before collection")
     baseline = _validate_baseline(before, game)
@@
-    evidence, evidence_exists = _validate_evidence_root(evidence_root)
     _capture_boot_log_inventory(game)

-    evidence_handle: _DirectoryHandle | None = None
     retained_files: list[_RetainedEvidenceFile] = []
     pending_retained_file: _RetainedEvidenceFile | None = None
     try:
-        evidence_dir, evidence_handle = _allocate_evidence_directory(
-            evidence, evidence_exists
-        )
         final_scan: _LogScan | None = None
@@
             if run_contract is not None and not canonical_current:
                 add_issue(
                     "current canonical boot log is missing or unchanged"
                 )
@@
         else:
             final_scan.close()
+
+        for spec in auxiliary_specs:
+            pending_retained_file = _open_auxiliary_evidence(
+                evidence_dir,
+                evidence_handle,
+                spec,
+            )
+            if pending_retained_file is not None:
+                retained_files.append(pending_retained_file)
+                pending_retained_file = None

         directory_identities = tuple(
@@
-        if evidence_handle is not None:
-            try:
-                evidence_handle.close()
-            except BaseException as exc:
-                _note_later_error(
-                    primary,
-                    "retained evidence directory close also failed",
-                    exc,
-                )
+        try:
+            evidence_handle.close()
+        except BaseException as exc:
+            _note_later_error(
+                primary,
+                "retained evidence directory close also failed",
+                exc,
+            )
         raise
```

Replace `_read_retained_evidence_file` and `_capture_retained_evidence_decision` in full with these bodies; this is the complete retained-read behavior after Task 5B:

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
        or before.st_size > item.max_bytes
    ):
        raise BootProbeError(f"retained evidence changed: {path}")
    os.lseek(item.descriptor, 0, os.SEEK_SET)
    payload = bytearray()
    digest = hashlib.sha256()
    while True:
        chunk = os.read(
            item.descriptor,
            min(1024 * 1024, item.max_bytes + 1 - len(payload)),
        )
        if not chunk:
            break
        payload.extend(chunk)
        if len(payload) > item.max_bytes:
            raise BootProbeError(f"retained evidence exceeds byte limit: {path}")
        digest.update(chunk)
    after = os.fstat(item.descriptor)
    if (
        _stat_identity(after) != item.identity
        or len(payload) != before.st_size
        or len(payload) != after.st_size
    ):
        raise BootProbeError(f"retained evidence was unstable: {path}")
    fingerprint = LogFingerprint(
        path=path,
        file_type="regular",
        inode=after.st_ino,
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        sha256=digest.hexdigest(),
    )
    if fingerprint != item.fingerprint:
        raise BootProbeError(f"retained evidence fingerprint changed: {path}")
    return bytes(payload), fingerprint


def _capture_retained_evidence_decision(
    retained: _RetainedBootEvidence,
) -> _EvidenceDecision:
    canonical_payload: bytes | None = None
    error_payloads: list[bytes] = []
    fingerprints: list[LogFingerprint] = []
    for item in retained.files:
        payload, fingerprint = _read_retained_evidence_file(retained, item)
        fingerprints.append(fingerprint)
        if item.kind != "boot_log":
            continue
        kind = _boot_log_kind(item.relative_path)
        if kind is None:
            raise BootProbeError(
                f"invalid retained boot log path: {item.relative_path}"
            )
        if kind == "canonical":
            if canonical_payload is not None:
                raise BootProbeError("duplicate retained canonical boot log")
            canonical_payload = payload
        error_payloads.append(payload)
    return _EvidenceDecision(
        markers=tuple(
            marker
            for marker in _REQUIRED_BOOT_MARKERS
            if canonical_payload is not None
            and _payload_contains_boot_marker(canonical_payload, marker)
        ),
        errors=tuple(
            marker
            for marker in _BOOT_ERROR_MARKERS
            if any(marker.encode("ascii") in payload for payload in error_payloads)
        ),
        fingerprints=tuple(fingerprints),
    )
```

Insert these two complete wrappers immediately after `_collect_boot_evidence_core`:

```python
def _collect_boot_evidence_into(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_dir: Path,
    evidence_handle: _DirectoryHandle,
    *,
    expected_inventory: _BootLogInventory | None,
    run_contract: _ValidatedBootLogContract | None,
    observed_failures: tuple[_ObservedFailureLog, ...],
    auxiliary_specs: tuple[_AuxiliaryEvidenceSpec, ...],
) -> _RetainedBootEvidence:
    owned_handle = _duplicate_directory_handle(evidence_handle)
    try:
        return _collect_boot_evidence_core(
            before,
            game_root,
            evidence_dir=evidence_dir,
            evidence_handle=owned_handle,
            expected_inventory=expected_inventory,
            run_contract=run_contract,
            observed_failures=observed_failures,
            auxiliary_specs=auxiliary_specs,
        )
    except BaseException as primary:
        if owned_handle.fd >= 0:
            try:
                owned_handle.close()
            except BaseException as secondary:
                _note_later_error(
                    primary,
                    "caller-owned evidence duplicate close also failed",
                    secondary,
                )
        raise


def _collect_boot_evidence_retained(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_root: Path,
    *,
    expected_inventory: _BootLogInventory | None,
    run_contract: _ValidatedBootLogContract | None = None,
    observed_failures: tuple[_ObservedFailureLog, ...] = (),
) -> _RetainedBootEvidence:
    evidence, exists = _validate_evidence_root(evidence_root)
    evidence_dir, evidence_handle = _allocate_evidence_directory(evidence, exists)
    try:
        return _collect_boot_evidence_core(
            before,
            game_root,
            evidence_dir=evidence_dir,
            evidence_handle=evidence_handle,
            expected_inventory=expected_inventory,
            run_contract=run_contract,
            observed_failures=observed_failures,
            auxiliary_specs=(),
        )
    except BaseException as primary:
        if evidence_handle.fd >= 0:
            try:
                evidence_handle.close()
            except BaseException as secondary:
                _note_later_error(
                    primary,
                    "allocated evidence directory close also failed",
                    secondary,
                )
        raise
```

Run this non-pytest structural assertion immediately after the edit. It proves that allocation exists only in the legacy wrapper, caller ownership is duplicated exactly once, the core opens auxiliary evidence exactly once per spec, each wrapper closes pre-core failures, the core owns the in-transaction failure close, and no retained reader can fall back to the boot-log byte bound:

```python
import ast
from pathlib import Path

source = Path("src/ssr_env/oracle_boot.py").read_text()
tree = ast.parse(source)
functions = {
    node.name: ast.get_source_segment(source, node)
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for name in (
    "_collect_boot_evidence_core",
    "_collect_boot_evidence_into",
    "_collect_boot_evidence_retained",
    "_read_retained_evidence_file",
    "_capture_retained_evidence_decision",
):
    assert functions[name] is not None
assert source.count("def _collect_boot_evidence_core(") == 1
assert source.count("def _collect_boot_evidence_into(") == 1
assert source.count("def _collect_boot_evidence_retained(") == 1
assert functions["_collect_boot_evidence_core"].count("_allocate_evidence_directory(") == 0
assert functions["_collect_boot_evidence_retained"].count("_allocate_evidence_directory(") == 1
assert functions["_collect_boot_evidence_into"].count("_duplicate_directory_handle(") == 1
assert functions["_collect_boot_evidence_into"].count("owned_handle.close()") == 1
assert functions["_collect_boot_evidence_retained"].count("evidence_handle.close()") == 1
assert functions["_collect_boot_evidence_core"].count("_open_auxiliary_evidence(") == 1
assert functions["_collect_boot_evidence_core"].count("evidence_handle.close()") == 1
assert "_MAX_MONITOR_LOG_BYTES" not in functions["_read_retained_evidence_file"]
assert functions["_read_retained_evidence_file"].count("item.max_bytes") == 3
assert functions["_capture_retained_evidence_decision"].count('item.kind != "boot_log"') == 1
```

- [ ] **Step 4: Run shared-evidence GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py
```

Expected: all old and new boot tests pass; the missing-config selector executes; default callers retain only boot logs and preserve their old bounds and payloads.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the caller-owned collection seam**

```bash
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "refactor: collect caller-owned oracle evidence"
```

### Task 6: Parameterize canonical evidence JSON publication

**Files:**
- Modify: `src/ssr_env/oracle_boot.py:377-386,4059-5041`
- Modify: `tests/test_oracle_boot.py`

**Interfaces:**
- Adds `_StagedProbeJson.canonical_name: Literal["probe.json", "passive-probe.json"]`.
- Changes `_stage_probe_json(..., canonical_name: str = "probe.json")`; verification, reconciliation, quarantine, and commit consume the retained name.
- Preserves every default `probe.json` byte and diagnostic.

- [ ] **Step 1: Add exact dual-name publication RED tests**

```python
@pytest.mark.parametrize("canonical_name", ("probe.json", "passive-probe.json"))
def test_staged_json_publishes_only_the_requested_canonical_name(
    tmp_path: Path,
    canonical_name: str,
) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1, "success": False}
    staged = oracle_boot._stage_probe_json(
        evidence,
        payload,
        canonical_name=canonical_name,
    )
    try:
        oracle_boot._verify_staged_probe_json(evidence, payload, staged)
        oracle_boot._commit_staged_probe_json(staged)
    finally:
        oracle_boot._close_staged_probe_json(staged)
    assert (evidence / canonical_name).read_bytes() == oracle_boot._encode_probe_json(payload)
    other = "passive-probe.json" if canonical_name == "probe.json" else "probe.json"
    assert not (evidence / other).exists()


def test_stage_json_rejects_every_other_name(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    with pytest.raises(BootProbeError, match="unsupported canonical JSON name"):
        oracle_boot._stage_probe_json(evidence, {}, canonical_name="../result.json")
```

- [ ] **Step 2: Run canonical-name RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py -k 'requested_canonical_name or every_other_name'
```

Expected: `_stage_probe_json` rejects the new keyword or still hard-codes `probe.json`.

- [ ] **Step 3: Retain and use the validated canonical name**

Change the staged model and add one validator:

```python
@dataclass(slots=True)
class _StagedProbeJson:
    directory: Path
    directory_handle: _DirectoryHandle
    pending_name: str
    canonical_name: Literal["probe.json", "passive-probe.json"]
    encoded: bytes
    pending_identity: tuple[int, int, int, int, int]
    verifier_fd: int = -1
    committed: bool = False


def _canonical_json_name(value: str) -> Literal["probe.json", "passive-probe.json"]:
    if value == "probe.json":
        return "probe.json"
    if value == "passive-probe.json":
        return "passive-probe.json"
    raise BootProbeError(f"unsupported canonical JSON name: {value!r}")
```

Apply the following exhaustive hunks. They enumerate every canonical-name lookup, rename source/destination, staging collision, pending stem, and legacy production call in the frozen source:

```diff
 def _probe_json_retained_namespace(
     staged: _StagedProbeJson,
 ) -> tuple[str, os.stat_result | None, os.stat_result | None]:
@@
-    canonical = _stat_staged_probe_json_name(staged, "probe.json")
+    canonical = _stat_staged_probe_json_name(staged, staged.canonical_name)
@@
 def _move_canonical_probe_json_to_private(
@@
             _renameatx(
                 staged.directory_handle,
-                "probe.json",
+                staged.canonical_name,
                 staged.directory_handle,
@@
-        canonical = _stat_staged_probe_json_name(staged, "probe.json")
+        canonical = _stat_staged_probe_json_name(staged, staged.canonical_name)
@@
 def _quarantine_reachable_canonical_probe_json(
@@
-        canonical = _stat_staged_probe_json_name(staged, "probe.json")
+        canonical = _stat_staged_probe_json_name(staged, staged.canonical_name)
@@
 def _stage_probe_json(
     evidence_dir: Path,
     payload: dict[str, Any],
     *,
+    canonical_name: str = "probe.json",
     _directory_handle: _DirectoryHandle | None = None,
 ) -> _StagedProbeJson:
+    canonical = _canonical_json_name(canonical_name)
     directory = _requested_path(evidence_dir, "evidence directory")
@@
         try:
             os.stat(
-                "probe.json",
+                canonical,
                 dir_fd=directory_handle.fd,
                 follow_symlinks=False,
             )
@@
         else:
             raise BootProbeError(
-                f"probe.json already exists in {directory}"
+                f"{canonical} already exists in {directory}"
             )

         pending_name: str | None = None
+        stem = canonical.removesuffix(".json")
         for _attempt in range(128):
@@
-            candidate = f".probe-json-{token}.pending"
+            candidate = f".{stem}-{token}.pending"
@@
             written = os.write(descriptor, view)
             if written <= 0:
-                raise OSError("short write while creating probe.json")
+                raise OSError(f"short write while creating {canonical}")
@@
         staged = _StagedProbeJson(
             directory=directory,
             directory_handle=directory_handle,
             pending_name=pending_name,
+            canonical_name=canonical,
             encoded=encoded,
             pending_identity=_stat_identity(created),
         )
@@
 def _commit_staged_probe_json(staged: _StagedProbeJson) -> None:
@@
             staged.directory_handle,
-            "probe.json",
+            staged.canonical_name,
             _RENAME_EXCL,
-            "publish canonical boot probe JSON",
+            f"publish canonical {staged.canonical_name}",
@@
     if state == "exact_pending" and rename_error is not None:
         raise BootProbeError(
-            f"cannot publish probe.json exclusively in "
+            f"cannot publish {staged.canonical_name} exclusively in "
             f"{staged.directory}: {rename_error}"
         ) from rename_error
@@
         staged_probe = _stage_probe_json(
             result.evidence_dir,
             payload,
+            canonical_name="probe.json",
             _directory_handle=retained.directory_handle,
         )
```

Run this non-pytest AST assertion immediately after applying the hunks. It fails if any canonical consumer still embeds a filename, if the stage lacks its validated retained field, or if the legacy production call ceases to select `probe.json` explicitly:

```python
import ast
from pathlib import Path

source = Path("src/ssr_env/oracle_boot.py").read_text()
tree = ast.parse(source)
functions = {
    node.name: ast.get_source_segment(source, node)
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for name in (
    "_probe_json_retained_namespace",
    "_move_canonical_probe_json_to_private",
    "_quarantine_reachable_canonical_probe_json",
    "_stage_probe_json",
    "_commit_staged_probe_json",
    "run_boot_probe",
):
    assert functions[name] is not None
for name in (
    "_probe_json_retained_namespace",
    "_move_canonical_probe_json_to_private",
    "_quarantine_reachable_canonical_probe_json",
    "_commit_staged_probe_json",
):
    assert '"probe.json"' not in functions[name]
assert functions["_probe_json_retained_namespace"].count("staged.canonical_name") == 1
assert functions["_move_canonical_probe_json_to_private"].count("staged.canonical_name") == 2
assert functions["_quarantine_reachable_canonical_probe_json"].count("staged.canonical_name") == 1
assert functions["_commit_staged_probe_json"].count("staged.canonical_name") == 3
stage = functions["_stage_probe_json"]
assert stage.count('canonical_name: str = "probe.json"') == 1
assert stage.count("canonical = _canonical_json_name(canonical_name)") == 1
assert stage.count("canonical_name=canonical") == 1
assert stage.count('os.stat(\n                "probe.json"') == 0
assert functions["run_boot_probe"].count('canonical_name="probe.json"') == 1
```

- [ ] **Step 4: Run complete publication GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py
```

Expected: all legacy publication/quarantine tests and both-name tests pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the publication seam**

```bash
git diff --check
git add src/ssr_env/oracle_boot.py tests/test_oracle_boot.py
git commit -m "refactor: select oracle evidence JSON name"
```

### Task 7A: Define ordinary-save proof models and exact bounds

**Files:**
- Create: `src/ssr_env/oracle_passive_probe.py`
- Create: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `PassiveProbeError(RuntimeError)`.
- Produces frozen `PathIdentity`, `SavePathNode`, `SaveTreeEntry`, and `SaveTreeProof` with the exact fields below.
- Every present root, directory entry, and existing absence-chain ancestor records actual `size`, `mtime_ns`, and `ctime_ns`; no directory field is normalized to zero.

- [ ] **Step 1: Add executable model, metadata, and exact-bound RED tests**

Create `tests/test_oracle_passive_probe.py` with:

```python
from __future__ import annotations

import os
import stat
from hashlib import sha256
from pathlib import Path

import pytest

from ssr_env import oracle_passive_probe as passive


def test_present_save_proof_keeps_root_and_directory_metadata(tmp_path: Path) -> None:
    root = tmp_path / "Sausage"
    root.mkdir()
    observed = root.stat(follow_symlinks=False)
    node = passive.SavePathNode(
        str(root), observed.st_dev, observed.st_ino, stat.S_IMODE(observed.st_mode),
        observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns,
    )
    entry = passive.SaveTreeEntry(
        "slot", "directory", observed.st_dev, observed.st_ino,
        stat.S_IMODE(observed.st_mode), observed.st_size,
        observed.st_mtime_ns, observed.st_ctime_ns, None,
    )
    proof = passive.SaveTreeProof(str(root), "present", node, (entry,), None, (), 0)
    assert proof.state == "present"
    assert proof.root == node and proof.entries == (entry,)
    assert node.size == entry.size == observed.st_size
    assert node.mtime_ns == entry.mtime_ns == observed.st_mtime_ns
    assert node.ctime_ns == entry.ctime_ns == observed.st_ctime_ns


def test_present_root_create_delete_changes_proof(tmp_path: Path) -> None:
    from dataclasses import fields

    assert tuple(item.name for item in fields(passive.SaveTreeProof)) == (
        "path", "state", "root", "entries", "missing_path", "ancestor_chain",
        "regular_bytes",
    )
    assert tuple(item.name for item in fields(passive.SavePathNode)) == (
        "path", "device", "inode", "mode", "size", "mtime_ns", "ctime_ns",
    )


def test_absent_target_create_delete_changes_ancestor_proof(tmp_path: Path) -> None:
    from dataclasses import FrozenInstanceError

    target = tmp_path / "Sausage"
    proof = passive.SaveTreeProof(
        str(target), "absent", None, (), str(target), (), 0,
    )
    assert proof.state == "absent" and proof.missing_path == str(target)
    with pytest.raises(FrozenInstanceError):
        proof.state = "present"


@pytest.mark.parametrize(("size", "fails"), ((8, False), (9, True)))
def test_save_proof_hash_bound_is_inclusive(
    tmp_path: Path,
    size: int,
    fails: bool,
) -> None:
    path = tmp_path / "save.bin"
    path.write_bytes(b"x" * size)
    descriptor = os.open(path, os.O_RDONLY)
    try:
        if fails:
            with pytest.raises(passive.PassiveProbeError, match="256 MiB"):
                passive._hash_open_regular(descriptor, 8)
        else:
            assert passive._hash_open_regular(descriptor, 8) == (
                8,
                sha256(b"x" * 8).hexdigest(),
            )
    finally:
        os.close(descriptor)


def test_save_proof_constants_are_exact() -> None:
    assert passive.MAX_SAVE_ENTRIES == 4_096
    assert passive.MAX_SAVE_BYTES == 256 * 1024 * 1024
```

- [ ] **Step 2: Run save-proof RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'save_proof or create_delete'
```

Expected: the module or `fingerprint_save_tree` is missing.

- [ ] **Step 3: Implement the descriptor-relative proof**

Create `src/ssr_env/oracle_passive_probe.py` with this foundation and implementation:

```python
from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


MAX_SAVE_ENTRIES = 4_096
MAX_SAVE_BYTES = 256 * 1024 * 1024
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK


class PassiveProbeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PathIdentity:
    path: str
    device: int
    inode: int
    mode: int


@dataclass(frozen=True, slots=True)
class SavePathNode:
    path: str
    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True, slots=True)
class SaveTreeEntry:
    relative_path: str
    kind: Literal["directory", "file"]
    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str | None


@dataclass(frozen=True, slots=True)
class SaveTreeProof:
    path: str
    state: Literal["present", "absent"]
    root: SavePathNode | None
    entries: tuple[SaveTreeEntry, ...]
    missing_path: str | None
    ancestor_chain: tuple[SavePathNode, ...]
    regular_bytes: int


def _save_node(path: Path, observed: os.stat_result) -> SavePathNode:
    return SavePathNode(
        path=str(path),
        device=observed.st_dev,
        inode=observed.st_ino,
        mode=stat.S_IMODE(observed.st_mode),
        size=observed.st_size,
        mtime_ns=observed.st_mtime_ns,
        ctime_ns=observed.st_ctime_ns,
    )


def _same_save_metadata(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _hash_open_regular(descriptor: int, limit: int) -> tuple[int, str]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = os.read(descriptor, min(1024 * 1024, limit + 1 - total))
        if not chunk:
            return total, digest.hexdigest()
        total += len(chunk)
        if total > limit:
            raise PassiveProbeError("ordinary save exceeds 256 MiB")
        digest.update(chunk)
```


- [ ] **Step 4: Run the model/bounds GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'save_proof or create_delete'
```

Expected: frozen proof objects preserve actual directory metadata and the inclusive exact bounds.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit models and bounds**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: define bounded ordinary save proofs"
```

### Task 7B: Walk a present ordinary-save tree with before/open/after agreement

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_walk_save_directory(...)` with stable byte-sorted traversal.
- For each directory and file, requires named-before == descriptor-before == descriptor-after == named-after; a same-type rename or inode substitution is terminal.

- [ ] **Step 1: Add present-tree replacement RED tests**

Add these twenty-one complete items (`4 checkpoints × 2 mutations + 4 bounds + 2 unsupported + 2 deep iterative walks + 2 close-failure ownership rows + nested-current-directory resolution + live-child-fd exit validation + post-child directory mutation`). The exact descendant-bound row also proves multiple byte-sorted siblings are all processed. The deep rows build 1,200 nested directories under a scaled `MAX_SAVE_ENTRIES=1_200`: the exact-bound case returns without `RecursionError`, and the plus-one case raises the descendant-bound `PassiveProbeError` before opening or descending into entry 1,201. The close rows inject a primary hashing failure plus failures closing two held child descriptors, and a first close failure with no active primary; both prove every acquired descriptor is attempted exactly once, the active primary is not masked, and absent a primary the first close error is raised only after all closes.

```python
@pytest.mark.parametrize(
    ("entry_kind", "boundary"),
    (
        ("file", "file_after_open"),
        ("file", "file_before_named_after"),
        ("directory", "directory_after_open"),
        ("directory", "directory_before_named_after"),
    ),
)
@pytest.mark.parametrize("mutation", ("rename", "substitute"))
def test_save_present_substitution_closes_the_held_descriptor_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entry_kind: str,
    boundary: str,
    mutation: str,
) -> None:
    root = tmp_path / "Sausage"
    root.mkdir()
    victim = root / "unique-victim"
    if entry_kind == "file":
        victim.write_bytes(b"original")
    else:
        victim.mkdir()
        (victim / "original-only").write_bytes(b"original")
    held = root / f"held-{entry_kind}-{boundary}-{mutation}"
    opened: list[int] = []
    close_count: dict[int, int] = {}
    fired = False
    original_open = passive.os.open
    original_close = passive.os.close

    def opening(name: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if dir_fd is not None and os.fspath(name) == victim.name:
            opened.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor in opened:
            close_count[descriptor] = close_count.get(descriptor, 0) + 1
        original_close(descriptor)

    def checkpoint(observed_boundary: str, observed_path: Path) -> None:
        nonlocal fired
        if fired or observed_boundary != boundary or observed_path != victim:
            return
        fired = True
        victim.rename(held)
        if mutation == "substitute":
            if entry_kind == "file":
                victim.write_bytes(b"replacement")
            else:
                victim.mkdir()
                (victim / "replacement-only").write_bytes(b"replacement")

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    with pytest.raises((passive.PassiveProbeError, FileNotFoundError)):
        passive.fingerprint_save_tree(root)
    assert fired is True
    assert len(opened) == 1
    assert close_count == {opened[0]: 1}


@pytest.mark.parametrize(
    ("resource", "amount", "fails"),
    (
        ("descendants", 2, False),
        ("descendants", 3, True),
        ("bytes", 8, False),
        ("bytes", 9, True),
    ),
)
def test_save_proof_enforces_exact_present_tree_bounds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    amount: int,
    fails: bool,
) -> None:
    root = tmp_path / "Sausage"
    root.mkdir()
    if resource == "descendants":
        monkeypatch.setattr(passive, "MAX_SAVE_ENTRIES", 2)
        for name in ("z", "a", "overflow")[:amount]:
            (root / name).write_bytes(b"")
        expected_message = "4096 descendants"
    else:
        monkeypatch.setattr(passive, "MAX_SAVE_BYTES", 8)
        (root / "payload").write_bytes(b"x" * amount)
        expected_message = "256 MiB"
    if fails:
        with pytest.raises(passive.PassiveProbeError, match=expected_message):
            passive.fingerprint_save_tree(root)
    else:
        proof = passive.fingerprint_save_tree(root)
        if resource == "descendants":
            assert tuple(item.relative_path for item in proof.entries) == ("a", "z")
        else:
            assert proof.regular_bytes == 8


@pytest.mark.parametrize("kind", ("symlink", "fifo"))
def test_save_proof_rejects_unsupported_present_entry(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "Sausage"
    root.mkdir()
    unsafe = root / "unsafe"
    if kind == "symlink":
        unsafe.symlink_to("missing")
    else:
        os.mkfifo(unsafe)
    with pytest.raises(passive.PassiveProbeError, match="unsupported save entry"):
        passive.fingerprint_save_tree(root)


def _build_deep_save_directories(root: Path, count: int) -> None:
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index in range(count):
            name = f"d{index:04d}"
            os.mkdir(name, dir_fd=descriptor)
            child = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
    finally:
        os.close(descriptor)


@pytest.mark.parametrize("overflow", (False, True))
def test_save_present_deep_tree_is_iterative_and_checks_bound_before_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    overflow: bool,
) -> None:
    root = tmp_path / "Sausage"
    root.mkdir()
    monkeypatch.setattr(passive, "MAX_SAVE_ENTRIES", 1_200)
    _build_deep_save_directories(root, 1_200 + int(overflow))
    original_open = passive.os.open
    overflow_opens = 0

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal overflow_opens
        if dir_fd is not None and os.fspath(path) == "d1200":
            overflow_opens += 1
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(passive.os, "open", opening)
    if overflow:
        with pytest.raises(passive.PassiveProbeError, match="4096 descendants"):
            passive.fingerprint_save_tree(root)
        assert overflow_opens == 0
    else:
        proof = passive.fingerprint_save_tree(root)
        assert len(proof.entries) == 1_200
        assert proof.entries[-1].relative_path.endswith("d1199")


@pytest.mark.parametrize("active_primary", (False, True))
def test_save_present_descriptor_cleanup_is_lifo_attempt_all(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    active_primary: bool,
) -> None:
    class CloseFailure(OSError):
        pass

    root = tmp_path / "Sausage"
    payload = root / "outer" / "inner" / "save.bin"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"save")
    directory_inodes = {path.stat().st_ino for path in (payload.parent.parent, payload.parent)}
    opened_directories: list[int] = []
    close_attempts: list[int] = []
    original_open = passive.os.open
    original_close = passive.os.close
    original_hash = passive._hash_open_regular
    primary = KeyboardInterrupt("hash interrupted")

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if dir_fd is not None and os.fstat(descriptor).st_ino in directory_inodes:
            opened_directories.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor in opened_directories:
            close_attempts.append(descriptor)
            original_close(descriptor)
            raise CloseFailure(f"close failed for {descriptor}")
        original_close(descriptor)

    def hashing(descriptor: int, limit: int) -> tuple[int, str]:
        if active_primary:
            raise primary
        return original_hash(descriptor, limit)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    monkeypatch.setattr(passive, "_hash_open_regular", hashing)
    if active_primary:
        with pytest.raises(KeyboardInterrupt) as caught:
            passive.fingerprint_save_tree(root)
        assert caught.value is primary
        assert sum("secondary ordinary-save descriptor close failure" in note for note in primary.__notes__) == 2
    else:
        with pytest.raises(CloseFailure):
            passive.fingerprint_save_tree(root)
    assert len(opened_directories) == 2
    assert close_attempts == list(reversed(opened_directories))
    assert len(set(close_attempts)) == 2


def test_save_present_nested_file_resolves_against_current_directory(
    tmp_path: Path,
) -> None:
    root = tmp_path / "Sausage"
    slot = root / "slot"
    slot.mkdir(parents=True)
    (root / "save.bin").write_bytes(b"root-decoy")
    (slot / "save.bin").write_bytes(b"nested-real")
    proof = passive.fingerprint_save_tree(root)
    by_path = {entry.relative_path: entry for entry in proof.entries}
    assert by_path["save.bin"].sha256 == sha256(b"root-decoy").hexdigest()
    assert by_path["slot/save.bin"].sha256 == sha256(b"nested-real").hexdigest()


def test_save_present_child_fd_remains_live_through_exit_revalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Sausage"
    slot = root / "slot"
    slot.mkdir(parents=True)
    (slot / "save.bin").write_bytes(b"nested")
    original_open = passive.os.open
    child_fds: list[int] = []
    checked = False

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if dir_fd is not None and os.fspath(path) == "slot":
            child_fds.append(descriptor)
        return descriptor

    def checkpoint(boundary: str, observed: Path) -> None:
        nonlocal checked
        if boundary == "directory_before_named_after" and observed == slot:
            assert len(child_fds) == 1
            assert stat.S_ISDIR(os.fstat(child_fds[0]).st_mode)
            checked = True

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    proof = passive.fingerprint_save_tree(root)
    assert checked is True
    assert tuple(entry.relative_path for entry in proof.entries) == ("slot", "slot/save.bin")


def test_save_present_revalidates_directory_after_all_descendants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "Sausage"
    slot = root / "slot"
    slot.mkdir(parents=True)
    save = slot / "save.bin"
    save.write_bytes(b"nested")
    fired = False

    def checkpoint(boundary: str, observed: Path) -> None:
        nonlocal fired
        if not fired and boundary == "file_before_named_after" and observed == save:
            fired = True
            (slot / "late-sibling").write_bytes(b"late")

    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="directory was unstable"):
        passive.fingerprint_save_tree(root)
    assert fired is True
```

- [ ] **Step 2: Run the present-tree RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'save_present or save_proof_rejects_unsupported or save_proof_enforces'
```

Expected: the previous walker omits siblings/descendants, uses the root descriptor for nested files, invalidates a transferred child fd before revalidation, skips post-child checks, or mishandles bounds/close ownership.

- [ ] **Step 3: Implement the complete stable walker**

Add `_save_proof_checkpoint(_boundary: str, _path: Path) -> None` and implement:

```python
import sys


def _save_proof_checkpoint(_boundary: str, _path: Path) -> None:
    return None


@dataclass(slots=True)
class _SaveDirectoryFrame:
    descriptor: int
    absolute: Path
    relative: Path
    names: tuple[str, ...]
    next_index: int
    owns_descriptor: bool
    parent_descriptor: int | None
    edge_name: str | None
    named_before: os.stat_result | None
    descriptor_before: os.stat_result | None
    entry_index: int | None


def _save_tree_entry(
    relative: Path,
    kind: Literal["directory", "file"],
    observed: os.stat_result,
    digest: str | None,
) -> SaveTreeEntry:
    return SaveTreeEntry(
        relative_path=relative.as_posix(),
        kind=kind,
        device=observed.st_dev,
        inode=observed.st_ino,
        mode=stat.S_IMODE(observed.st_mode),
        size=observed.st_size,
        mtime_ns=observed.st_mtime_ns,
        ctime_ns=observed.st_ctime_ns,
        sha256=digest,
    )


def _close_owned_save_descriptor(owned: list[int], descriptor: int) -> None:
    if not owned or owned[-1] != descriptor:
        raise AssertionError("ordinary-save descriptor ownership is not LIFO")
    # Clear ownership before the one permitted close attempt. If close raises,
    # no outer finalizer can retry a potentially reused descriptor number.
    owned.pop()
    active = sys.exception()
    try:
        os.close(descriptor)
    except BaseException as error:
        if active is None:
            raise
        try:
            active.add_note(
                "secondary ordinary-save descriptor close failure: "
                f"{type(error).__name__}: {error}"
            )
        except BaseException:
            pass


def _walk_save_directory(
    descriptor: int,
    absolute: Path,
    relative: Path,
    entries: list[SaveTreeEntry],
    regular_bytes: list[int],
) -> None:
    with os.scandir(descriptor) as discovered:
        root_names = tuple(
            sorted((entry.name for entry in discovered), key=os.fsencode)
        )
    stack = [
        _SaveDirectoryFrame(
            descriptor,
            absolute,
            relative,
            root_names,
            0,
            False,
            None,
            None,
            None,
            None,
            None,
        )
    ]
    owned: list[int] = []
    first_close: BaseException | None = None
    try:
        while stack:
            frame = stack[-1]
            if frame.next_index == len(frame.names):
                stack.pop()
                if not frame.owns_descriptor:
                    continue
                if (
                    frame.parent_descriptor is None
                    or frame.edge_name is None
                    or frame.named_before is None
                    or frame.descriptor_before is None
                    or frame.entry_index is None
                ):
                    raise AssertionError("incomplete ordinary-save EXIT frame")
                _save_proof_checkpoint(
                    "directory_before_named_after",
                    frame.absolute,
                )
                descriptor_after = os.fstat(frame.descriptor)
                named_after = os.stat(
                    frame.edge_name,
                    dir_fd=frame.parent_descriptor,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(descriptor_after.st_mode)
                    or not _same_save_metadata(
                        frame.named_before,
                        frame.descriptor_before,
                    )
                    or not _same_save_metadata(
                        frame.descriptor_before,
                        descriptor_after,
                    )
                    or not _same_save_metadata(descriptor_after, named_after)
                ):
                    raise PassiveProbeError(
                        f"ordinary save directory was unstable: {frame.absolute}"
                    )
                entries[frame.entry_index] = _save_tree_entry(
                    frame.relative,
                    "directory",
                    descriptor_after,
                    None,
                )
                _close_owned_save_descriptor(owned, frame.descriptor)
                continue

            name = frame.names[frame.next_index]
            frame.next_index += 1
            # The descendant reservation check precedes stat/open/descent, so
            # entry 4,097 is never opened even in a maximally deep tree.
            if len(entries) >= MAX_SAVE_ENTRIES:
                raise PassiveProbeError("ordinary save exceeds 4096 descendants")
            child_relative = (
                Path(name)
                if frame.relative == Path(".")
                else frame.relative / name
            )
            child_absolute = frame.absolute / name
            named_before = os.stat(
                name,
                dir_fd=frame.descriptor,
                follow_symlinks=False,
            )

            if stat.S_ISDIR(named_before.st_mode):
                child_fd = os.open(
                    name,
                    _DIRECTORY_FLAGS,
                    dir_fd=frame.descriptor,
                )
                owned.append(child_fd)
                descriptor_before = os.fstat(child_fd)
                if (
                    not stat.S_ISDIR(descriptor_before.st_mode)
                    or not _same_save_metadata(named_before, descriptor_before)
                ):
                    raise PassiveProbeError(
                        f"ordinary save directory changed: {child_absolute}"
                    )
                _save_proof_checkpoint("directory_after_open", child_absolute)
                entry_index = len(entries)
                entries.append(
                    _save_tree_entry(
                        child_relative,
                        "directory",
                        descriptor_before,
                        None,
                    )
                )
                with os.scandir(child_fd) as discovered:
                    child_names = tuple(
                        sorted(
                            (entry.name for entry in discovered),
                            key=os.fsencode,
                        )
                    )
                # Parent and child descriptors both stay live until this EXIT
                # frame runs after all descendants.
                stack.append(
                    _SaveDirectoryFrame(
                        child_fd,
                        child_absolute,
                        child_relative,
                        child_names,
                        0,
                        True,
                        frame.descriptor,
                        name,
                        named_before,
                        descriptor_before,
                        entry_index,
                    )
                )
                continue

            if stat.S_ISREG(named_before.st_mode):
                remaining = MAX_SAVE_BYTES - regular_bytes[0]
                if named_before.st_size > remaining:
                    raise PassiveProbeError("ordinary save exceeds 256 MiB")
                child_fd = os.open(
                    name,
                    _FILE_FLAGS,
                    dir_fd=frame.descriptor,
                )
                owned.append(child_fd)
                try:
                    descriptor_before = os.fstat(child_fd)
                    if (
                        not stat.S_ISREG(descriptor_before.st_mode)
                        or not _same_save_metadata(
                            named_before,
                            descriptor_before,
                        )
                        or descriptor_before.st_size > remaining
                    ):
                        raise PassiveProbeError(
                            f"ordinary save file changed: {child_absolute}"
                        )
                    _save_proof_checkpoint("file_after_open", child_absolute)
                    size, digest = _hash_open_regular(child_fd, remaining)
                    _save_proof_checkpoint(
                        "file_before_named_after",
                        child_absolute,
                    )
                    descriptor_after = os.fstat(child_fd)
                    named_after = os.stat(
                        name,
                        dir_fd=frame.descriptor,
                        follow_symlinks=False,
                    )
                    if (
                        not _same_save_metadata(
                            descriptor_before,
                            descriptor_after,
                        )
                        or not _same_save_metadata(
                            descriptor_after,
                            named_after,
                        )
                        or size != descriptor_after.st_size
                    ):
                        raise PassiveProbeError(
                            f"ordinary save file was unstable: {child_absolute}"
                        )
                    regular_bytes[0] += size
                    entries.append(
                        _save_tree_entry(
                            child_relative,
                            "file",
                            descriptor_after,
                            digest,
                        )
                    )
                finally:
                    _close_owned_save_descriptor(owned, child_fd)
                continue

            raise PassiveProbeError(
                f"unsupported save entry: {child_absolute}"
            )
    finally:
        active = sys.exception()
        while owned:
            closing = owned.pop()
            try:
                os.close(closing)
            except BaseException as error:
                if active is not None:
                    try:
                        active.add_note(
                            "secondary ordinary-save descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
                elif first_close is None:
                    first_close = error
                else:
                    try:
                        first_close.add_note(
                            "later ordinary-save descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
        if active is None and first_close is not None:
            raise first_close
```

The implementation must not use `_walk_save_directory` recursively; the fresh quality review must AST-check that its body contains no call to its own name and exercise the literal EXIT-frame path after descendant mutation.


- [ ] **Step 4: Run the present-tree GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'save_present or save_proof_rejects_unsupported or save_proof_enforces'
```

Expected: every child is stable across both named and descriptor checks; traversal order and bounds are exact.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the present-tree walker**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: authenticate present ordinary save trees"
```

### Task 7C: Authenticate the root and every existing absence-chain ancestor

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `fingerprint_save_tree(path: Path) -> SaveTreeProof`.
- Retains every ancestor descriptor and its parent/name edge; before return it proves descriptor-after and named-after equal the original seal for `/`, ancestors, target root, directories, and files.

- [ ] **Step 1: Add root/ancestor/absence substitution RED tests**

Add these twenty-two complete items (`9 present edges + 3 absence ancestors + 3 missing-component transitions + 1 unchanged proof + root-fstat failure + child-fstat failure + primary-with-two-close-failures + first-close-failure-without-primary + 2 exact-once identity-mismatch rows`). The `fstat` and identity-mismatch rows record every returned fd before injecting the exception and require all of them closed exactly once. The close rows require reverse-order attempt-all cleanup, identical active-primary identity, and deterministic close notes.

```python
from types import SimpleNamespace


def _save_stat_with_other_inode(observed: os.stat_result) -> SimpleNamespace:
    return SimpleNamespace(
        st_dev=observed.st_dev,
        st_ino=observed.st_ino + 1,
        st_mode=observed.st_mode,
        st_size=observed.st_size,
        st_mtime_ns=observed.st_mtime_ns,
        st_ctime_ns=observed.st_ctime_ns,
    )


@pytest.mark.parametrize(
    ("edge", "mutation"),
    (
        ("filesystem_root", "substitute"),
        ("existing_ancestor", "rename"),
        ("existing_ancestor", "substitute"),
        ("target_root", "rename"),
        ("target_root", "substitute"),
        ("nested_directory", "rename"),
        ("nested_directory", "substitute"),
        ("regular_file", "rename"),
        ("regular_file", "substitute"),
    ),
)
def test_save_root_substitution_rejects_every_present_named_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    edge: str,
    mutation: str,
) -> None:
    outer = tmp_path / "controlled-outer"
    ancestor = outer / "controlled-ancestor"
    target = ancestor / "Sausage"
    nested = target / "slot"
    regular = nested / "save.bin"
    nested.mkdir(parents=True)
    regular.write_bytes(b"original")
    original_stat = passive.os.stat
    state = {"armed_root": False, "fired": False}

    def stat_with_root_drift(path: object, *args: object, **kwargs: object) -> os.stat_result:
        observed = original_stat(path, *args, **kwargs)
        if state["armed_root"] and os.fspath(path) == "/" and kwargs.get("dir_fd") is None:
            state["armed_root"] = False
            state["fired"] = True
            return _save_stat_with_other_inode(observed)
        return observed

    def checkpoint(boundary: str, observed_path: Path) -> None:
        if state["fired"]:
            return
        if edge == "filesystem_root" and boundary == "before_present_chain_revalidation":
            state["armed_root"] = True
            return
        selected: Path | None = None
        if edge == "existing_ancestor" and boundary == "before_present_chain_revalidation":
            selected = ancestor
        elif edge == "target_root" and boundary == "before_present_chain_revalidation":
            selected = target
        elif edge == "nested_directory" and boundary == "directory_before_named_after" and observed_path == nested:
            selected = nested
        elif edge == "regular_file" and boundary == "file_before_named_after" and observed_path == regular:
            selected = regular
        if selected is None:
            return
        state["fired"] = True
        held = selected.with_name(selected.name + "-held")
        selected.rename(held)
        if mutation == "substitute":
            if edge == "regular_file":
                selected.write_bytes(b"replacement")
            else:
                selected.mkdir()

    monkeypatch.setattr(passive.os, "stat", stat_with_root_drift)
    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    with pytest.raises((passive.PassiveProbeError, FileNotFoundError)):
        passive.fingerprint_save_tree(target)
    assert state["fired"] is True


@pytest.mark.parametrize("edge", ("filesystem_root", "controlled_outer", "controlled_parent"))
def test_save_absence_substitution_rejects_each_retained_ancestor_edge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    edge: str,
) -> None:
    outer = tmp_path / "absence-outer"
    parent = outer / "absence-parent"
    parent.mkdir(parents=True)
    target = parent / "Sausage"
    original_stat = passive.os.stat
    state = {"armed_root": False, "fired": False}

    def stat_with_root_drift(path: object, *args: object, **kwargs: object) -> os.stat_result:
        observed = original_stat(path, *args, **kwargs)
        if state["armed_root"] and os.fspath(path) == "/" and kwargs.get("dir_fd") is None:
            state["armed_root"] = False
            state["fired"] = True
            return _save_stat_with_other_inode(observed)
        return observed

    def checkpoint(boundary: str, observed_path: Path) -> None:
        if boundary != "before_absence_chain_revalidation" or observed_path != target:
            return
        if edge == "filesystem_root":
            state["armed_root"] = True
            return
        selected = outer if edge == "controlled_outer" else parent
        held = selected.with_name(selected.name + "-held")
        selected.rename(held)
        selected.mkdir()
        state["fired"] = True

    monkeypatch.setattr(passive.os, "stat", stat_with_root_drift)
    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="ancestor changed"):
        passive.fingerprint_save_tree(target)
    assert state["fired"] is True


@pytest.mark.parametrize("transition", ("create", "create_remove", "create_remove_recreate"))
def test_save_absence_substitution_rejects_first_missing_component_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    transition: str,
) -> None:
    parent = tmp_path / "absence-parent"
    parent.mkdir()
    target = parent / "Sausage"
    fired = False

    def checkpoint(boundary: str, observed_path: Path) -> None:
        nonlocal fired
        if boundary != "between_absence_checks" or observed_path != target:
            return
        fired = True
        before = parent.stat(follow_symlinks=False)
        target.mkdir()
        if transition != "create":
            target.rmdir()
            os.utime(
                parent,
                ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000),
                follow_symlinks=False,
            )
        if transition == "create_remove_recreate":
            target.mkdir()

    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError):
        passive.fingerprint_save_tree(target)
    assert fired is True


def test_save_absence_substitution_unchanged_returns_exact_proof_and_revalidates_full_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "stable-parent"
    parent.mkdir()
    target = parent / "Sausage"
    original = passive._revalidate_held_save_chain
    observed_chains: list[tuple[str, ...]] = []

    def capture(handles: list[passive._HeldSaveDirectory]) -> None:
        observed_chains.append(tuple(str(handle.path) for handle in handles))
        original(handles)

    monkeypatch.setattr(passive, "_revalidate_held_save_chain", capture)
    first = passive.fingerprint_save_tree(target)
    second = passive.fingerprint_save_tree(target)
    assert first == second
    assert first.state == "absent" and first.missing_path == str(target)
    expected = tuple(node.path for node in first.ancestor_chain)
    assert observed_chains == [expected, expected, expected, expected]


@pytest.mark.parametrize("mismatch", ("root", "child"))
def test_save_root_and_child_identity_mismatch_closes_each_fd_exactly_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: str,
) -> None:
    target = tmp_path / "owned" / "Sausage"
    target.mkdir(parents=True)
    opened: list[int] = []
    close_count: dict[int, int] = {}
    fired = False
    original_open = passive.os.open
    original_fstat = passive.os.fstat
    original_close = passive.os.close

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        opened.append(descriptor)
        return descriptor

    def fstat(descriptor: int) -> os.stat_result:
        nonlocal fired
        observed = original_fstat(descriptor)
        selected = (
            mismatch == "root" and descriptor == opened[0]
        ) or (
            mismatch == "child" and descriptor != opened[0]
        )
        if selected and not fired:
            fired = True
            return _save_stat_with_other_inode(observed)
        return observed

    def closing(descriptor: int) -> None:
        close_count[descriptor] = close_count.get(descriptor, 0) + 1
        original_close(descriptor)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "fstat", fstat)
    monkeypatch.setattr(passive.os, "close", closing)
    with pytest.raises(passive.PassiveProbeError, match="root changed|ancestor changed"):
        passive.fingerprint_save_tree(target)
    assert fired is True
    assert opened
    assert close_count == {descriptor: 1 for descriptor in opened}


@pytest.mark.parametrize("failure", ("root_fstat", "child_fstat"))
def test_save_descriptor_fstat_failure_closes_every_returned_fd_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    target = tmp_path / "owned" / "Sausage"
    target.mkdir(parents=True)
    primary = KeyboardInterrupt(failure)
    opened: list[int] = []
    close_count: dict[int, int] = {}
    original_open = passive.os.open
    original_fstat = passive.os.fstat
    original_close = passive.os.close
    fired = False

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        opened.append(descriptor)
        return descriptor

    def fstat(descriptor: int) -> os.stat_result:
        nonlocal fired
        selected = (
            failure == "root_fstat" and opened and descriptor == opened[0]
        ) or (
            failure == "child_fstat" and len(opened) > 1 and descriptor == opened[-1]
        )
        if selected and not fired:
            fired = True
            raise primary
        return original_fstat(descriptor)

    def closing(descriptor: int) -> None:
        close_count[descriptor] = close_count.get(descriptor, 0) + 1
        original_close(descriptor)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "fstat", fstat)
    monkeypatch.setattr(passive.os, "close", closing)
    with pytest.raises(KeyboardInterrupt) as caught:
        passive.fingerprint_save_tree(target)
    assert caught.value is primary and fired
    assert close_count == {descriptor: 1 for descriptor in opened}


@pytest.mark.parametrize("active_primary", (False, True))
def test_save_held_close_failures_are_lifo_attempt_all_and_preserve_primary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    active_primary: bool,
) -> None:
    target = tmp_path / "owned" / "Sausage"
    target.mkdir(parents=True)
    opened: list[int] = []
    attempts: list[int] = []
    primary = KeyboardInterrupt("active save failure")
    original_open = passive.os.open
    original_close = passive.os.close

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        opened.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor in opened:
            attempts.append(descriptor)
            original_close(descriptor)
            raise OSError(f"close failed for {descriptor}")
        original_close(descriptor)

    def checkpoint(boundary: str, _path: Path) -> None:
        if active_primary and boundary == "before_present_chain_revalidation":
            raise primary

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    monkeypatch.setattr(passive, "_save_proof_checkpoint", checkpoint)
    if active_primary:
        with pytest.raises(KeyboardInterrupt) as caught:
            passive.fingerprint_save_tree(target)
        assert caught.value is primary
        assert len(primary.__notes__) == len(opened)
    else:
        with pytest.raises(OSError, match="close failed"):
            passive.fingerprint_save_tree(target)
    assert attempts == list(reversed(opened))
    assert len(attempts) == len(set(attempts))
```

- [ ] **Step 2: Run the root/absence RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'save_root_substitution or save_ancestor_substitution or save_absence_substitution or create_delete or save_descriptor_fstat_failure or save_held_close_failures or save_root_and_child_identity'
```

Expected: held-fd-only ancestor validation accepts at least one renamed/replaced name.

- [ ] **Step 3: Implement retained parent/name edge validation**

Add the held-edge type and validator, then use them in the complete top-level function:

```python
@dataclass(frozen=True, slots=True)
class _HeldSaveDirectory:
    descriptor: int
    parent_descriptor: int | None
    name: str | None
    path: Path
    node: SavePathNode


def _node_matches(observed: os.stat_result, expected: SavePathNode) -> bool:
    return _save_node(Path(expected.path), observed) == expected


def _revalidate_held_save_chain(handles: list[_HeldSaveDirectory]) -> None:
    for held in handles:
        descriptor_after = os.fstat(held.descriptor)
        named_after = (
            os.stat("/", follow_symlinks=False)
            if held.parent_descriptor is None
            else os.stat(
                held.name,
                dir_fd=held.parent_descriptor,
                follow_symlinks=False,
            )
        )
        if (
            not _node_matches(descriptor_after, held.node)
            or not _node_matches(named_after, held.node)
            or not _same_save_metadata(descriptor_after, named_after)
        ):
            raise PassiveProbeError(f"ordinary save ancestor changed: {held.path}")


def fingerprint_save_tree(path: Path) -> SaveTreeProof:
    if not isinstance(path, Path) or not path.is_absolute() or "\x00" in os.fspath(path):
        raise PassiveProbeError("ordinary save path must be an absolute Path")
    components = path.parts[1:]
    handles: list[_HeldSaveDirectory] = []
    owned: list[int] = []
    descriptor = os.open("/", _DIRECTORY_FLAGS)
    owned.append(descriptor)
    first_close: BaseException | None = None
    current = Path("/")
    try:
        root_named = os.stat("/", follow_symlinks=False)
        root_descriptor = os.fstat(descriptor)
        if not _same_save_metadata(root_named, root_descriptor):
            raise PassiveProbeError("ordinary save filesystem root changed")
        handles.append(
            _HeldSaveDirectory(
                descriptor, None, None, current, _save_node(current, root_descriptor)
            )
        )
        for index, component in enumerate(components):
            next_path = current / component
            try:
                named = os.stat(component, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                _save_proof_checkpoint("between_absence_checks", next_path)
                try:
                    os.stat(component, dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise PassiveProbeError(f"ordinary save appeared during proof: {next_path}")
                _save_proof_checkpoint("before_absence_chain_revalidation", next_path)
                _revalidate_held_save_chain(handles)
                try:
                    os.stat(component, dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise PassiveProbeError(f"ordinary save appeared during proof: {next_path}")
                _revalidate_held_save_chain(handles)
                return SaveTreeProof(
                    path=str(path),
                    state="absent",
                    root=None,
                    entries=(),
                    missing_path=str(next_path),
                    ancestor_chain=tuple(item.node for item in handles),
                    regular_bytes=0,
                )
            if not stat.S_ISDIR(named.st_mode):
                raise PassiveProbeError(f"ordinary save ancestor is not a directory: {next_path}")
            child_fd = os.open(component, _DIRECTORY_FLAGS, dir_fd=descriptor)
            # Register ownership before the first fallible inspection. No
            # mismatch branch closes manually; the single finalizer owns all
            # root/ancestor descriptors until it pops them before close.
            owned.append(child_fd)
            child_stat = os.fstat(child_fd)
            if not _same_save_metadata(named, child_stat):
                raise PassiveProbeError(f"ordinary save ancestor changed: {next_path}")
            parent_descriptor = descriptor
            descriptor = child_fd
            current = next_path
            handles.append(
                _HeldSaveDirectory(
                    descriptor,
                    parent_descriptor,
                    component,
                    current,
                    _save_node(current, child_stat),
                )
            )
            if index == len(components) - 1:
                entries: list[SaveTreeEntry] = []
                total = [0]
                before_root = os.fstat(descriptor)
                _walk_save_directory(descriptor, current, Path("."), entries, total)
                _save_proof_checkpoint("before_present_chain_revalidation", path)
                _revalidate_held_save_chain(handles)
                return SaveTreeProof(
                    path=str(path),
                    state="present",
                    root=handles[-1].node,
                    entries=tuple(sorted(entries, key=lambda item: os.fsencode(item.relative_path))),
                    missing_path=None,
                    ancestor_chain=(),
                    regular_bytes=total[0],
                )
        raise PassiveProbeError("ordinary save path may not be filesystem root")
    finally:
        active = sys.exception()
        while owned:
            closing = owned.pop()
            try:
                os.close(closing)
            except BaseException as error:
                if active is not None:
                    try:
                        active.add_note(
                            "secondary held save descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
                elif first_close is None:
                    first_close = error
                else:
                    try:
                        first_close.add_note(
                            "later held save descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
        if active is None and first_close is not None:
            raise first_close
```

- [ ] **Step 4: Run the full proof GREEN matrix**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'save_root_substitution or save_ancestor_substitution or save_absence_substitution or create_delete or save_descriptor_fstat_failure or save_held_close_failures or save_root_and_child_identity'
```

Expected: all proof, metadata, unsupported-entry, and scaled/exact-constant bound tests pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the proof gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: fingerprint ordinary oracle saves"
```

### Task 8A: Define private-layout ownership and path models

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces only mutable `PassiveLayout`, frozen `IsolatedSaveEntry`, `_approved_evidence_root() -> Path`, and the non-allocating helpers shown below. `_allocate_passive_layout` is intentionally absent until Task 8C.

- [ ] **Step 1: Add only the concrete model RED test**

```python
from collections.abc import Iterator


def test_layout_model_has_exact_owned_paths_handles_and_seals() -> None:
    from dataclasses import fields

    assert tuple(item.name for item in fields(passive.PassiveLayout)) == (
        "evidence_dir", "evidence_handle", "evidence_identity",
        "isolated_save_dir", "isolated_save_handle", "isolated_save_identity",
        "config_path", "config_identity", "config_sha256", "trace_path",
        "trace_identity", "trace_seal",
    )
    assert tuple(item.name for item in fields(passive.IsolatedSaveEntry)) == (
        "relative_path", "kind", "mode", "size", "sha256",
    )

```

- [ ] **Step 2: Run layout RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'layout_model'
```

Expected: `PassiveLayout` is missing. No allocator test is collected.

- [ ] **Step 3: Implement exact layout ownership and bytes**

Add these definitions:

```python
from datetime import UTC, datetime
import secrets
import sys

from ssr_env import oracle_boot


@dataclass(frozen=True, slots=True)
class IsolatedSaveEntry:
    relative_path: str
    kind: Literal["directory", "file", "symlink", "fifo", "other"]
    mode: int
    size: int
    sha256: str | None


@dataclass(slots=True)
class PassiveLayout:
    evidence_dir: Path
    evidence_handle: oracle_boot._DirectoryHandle
    evidence_identity: PathIdentity
    isolated_save_dir: Path
    isolated_save_handle: oracle_boot._DirectoryHandle
    isolated_save_identity: PathIdentity
    config_path: Path
    config_identity: PathIdentity
    config_sha256: str
    trace_path: Path
    trace_identity: PathIdentity | None = None
    trace_seal: _TraceFileSeal | None = None

    def close(self) -> None:
        primary: BaseException | None = None
        for handle in (self.isolated_save_handle, self.evidence_handle):
            try:
                handle.close()
            except BaseException as error:
                if primary is None:
                    primary = error
                else:
                    primary.add_note(f"layout handle close also failed: {error}")
        if primary is not None:
            raise primary


def _approved_evidence_root() -> Path:
    return Path(__file__).resolve(strict=True).parents[2] / "data" / "oracle"


def _utc_leaf_prefix() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _random_token() -> str:
    return secrets.token_hex(16)


def _layout_checkpoint(_boundary: str) -> None:
    return None


def _identity(path: Path, observed: os.stat_result) -> PathIdentity:
    return PathIdentity(
        path=str(path),
        device=observed.st_dev,
        inode=observed.st_ino,
        mode=stat.S_IMODE(observed.st_mode),
    )
```


- [ ] **Step 4: Run the model/ownership GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'layout_model'
```

Expected: the exact model field contracts pass. Allocator and close behavior remain unregistered until Task 8C.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit layout ownership models**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: define passive layout ownership"
```

### Task 8B: Encode the exact passive configuration

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_encode_passive_config(layout: PassiveLayout) -> bytes` as strict UTF-8 without BOM and with exact LF-delimited fields and final LF.
- Rejects NUL, CR, or LF in either interpolated path and enforces the 64 KiB limit before any file is created.
- Uses a Task-8B-local non-allocating layout fixture; `_allocate_passive_layout` is still absent.

- [ ] **Step 1: Add exact-byte and forbidden-path RED tests**

Add these nine complete items (`1 exact + 6 forbidden-path + 2 bound`). First add this self-contained fixture and use `config_layout` in every test below instead of the allocator-backed `passive_layout` fixture:

```python
@pytest.fixture
def config_layout(tmp_path: Path) -> Iterator[passive.PassiveLayout]:
    evidence = tmp_path / "evidence"
    save = tmp_path / "save"
    evidence.mkdir(mode=0o700)
    save.mkdir(mode=0o700)
    evidence_handle = oracle_boot._open_absolute_directory(evidence, "test evidence")
    save_handle = oracle_boot._open_absolute_directory(save, "test save")
    layout = passive.PassiveLayout(
        evidence_dir=evidence,
        evidence_handle=evidence_handle,
        evidence_identity=passive._identity(evidence, os.fstat(evidence_handle.fd)),
        isolated_save_dir=save,
        isolated_save_handle=save_handle,
        isolated_save_identity=passive._identity(save, os.fstat(save_handle.fd)),
        config_path=evidence / "passive.cfg",
        config_identity=passive.PathIdentity("", 0, 0, 0),
        config_sha256="",
        trace_path=evidence / "passive-trace.ndjson",
    )
    try:
        yield layout
    finally:
        layout.close()
```

```python
def _expected_passive_config(output: Path, save: Path) -> bytes:
    return (
        "[Oracle]\n"
        "Mode = passive\n"
        f"OutputDirectory = {output}\n"
        "RunName = passive-trace\n"
        f"SaveDirectory = {save}\n"
        "ExpectedPassiveInputs = 3\n"
        "MaxSettleFrames = 600\n"
        "MaxSettleSeconds = 30\n"
    ).encode("utf-8")


def test_passive_config_bytes_are_exact_utf8_lf_with_one_final_lf(
    config_layout: passive.PassiveLayout,
) -> None:
    passive_layout = config_layout
    encoded = passive._encode_passive_config(passive_layout)
    assert encoded == _expected_passive_config(
        passive_layout.evidence_dir, passive_layout.isolated_save_dir
    )
    assert encoded.endswith(b"\n") and not encoded.endswith(b"\n\n")
    assert b"\r" not in encoded and not encoded.startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("field", ("evidence_dir", "isolated_save_dir"))
@pytest.mark.parametrize("forbidden", ("\x00", "\r", "\n"))
def test_passive_config_forbidden_character_in_either_path_is_rejected(
    config_layout: passive.PassiveLayout,
    field: str,
    forbidden: str,
) -> None:
    passive_layout = config_layout
    original = getattr(passive_layout, field)
    setattr(passive_layout, field, Path(str(original) + forbidden + "suffix"))
    with pytest.raises(passive.PassiveProbeError, match="forbidden character"):
        passive._encode_passive_config(passive_layout)


@pytest.mark.parametrize(("target_size", "fails"), ((64 * 1024, False), (64 * 1024 + 1, True)))
def test_passive_config_bound_is_inclusive_and_checked_before_creation(
    config_layout: passive.PassiveLayout,
    target_size: int,
    fails: bool,
) -> None:
    passive_layout = config_layout
    save = Path("/s")
    base = _expected_passive_config(Path("/"), save)
    output = Path("/" + "x" * (target_size - len(base)))
    assert len(_expected_passive_config(output, save)) == target_size
    passive_layout.evidence_dir = output
    passive_layout.isolated_save_dir = save
    before = tuple(passive_layout.evidence_handle.path.iterdir())
    if fails:
        with pytest.raises(passive.PassiveProbeError, match="exceeds 64 KiB"):
            passive._encode_passive_config(passive_layout)
    else:
        assert len(passive._encode_passive_config(passive_layout)) == 64 * 1024
    assert tuple(passive_layout.evidence_handle.path.iterdir()) == before
```

- [ ] **Step 2: Run the config RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'passive_config_bytes or passive_config_forbidden or passive_config_bound'
```

Expected: exact encoding/limit validation is absent.

- [ ] **Step 3: Implement the complete encoder**

```python
def _encode_passive_config(layout: PassiveLayout) -> bytes:
    for value in (str(layout.evidence_dir), str(layout.isolated_save_dir)):
        if any(character in value for character in ("\x00", "\r", "\n")):
            raise PassiveProbeError("passive path contains a forbidden character")
    payload = "\n".join(
        (
            "[Oracle]",
            "Mode = passive",
            f"OutputDirectory = {layout.evidence_dir}",
            "RunName = passive-trace",
            f"SaveDirectory = {layout.isolated_save_dir}",
            "ExpectedPassiveInputs = 3",
            "MaxSettleFrames = 600",
            "MaxSettleSeconds = 30",
            "",
        )
    ).encode("utf-8")
    if len(payload) > 64 * 1024:
        raise PassiveProbeError("passive config exceeds 64 KiB")
    return payload
```

- [ ] **Step 4: Run the config GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'passive_config_bytes or passive_config_forbidden or passive_config_bound'
```

Expected: every exact byte and rejection row passes.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit exact config encoding**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: encode exact passive oracle config"
```

### Task 8C: Allocate both private siblings and create the config exclusively

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_allocate_passive_layout(evidence_root: Path) -> PassiveLayout`.
- Leaves every created private node in place on failure for diagnosis, never traverses a collision, and closes each acquired descriptor exactly once.
- Proves the trace target absent twice after the config is durable and before returning.

- [ ] **Step 1: Add allocation/interruption/absence RED tests**

Add these twenty-one complete items: move the three allocator tests and allocator-backed `passive_layout` fixture explicitly reserved in Task 8A into this task, then add the original sixteen items (`3 collisions + 8 interruptions + 1 short-write loop + 1 absence race + 2 replacements + 1 close failure`) plus two root-close rows. The fixture is not a collected item. One root-close row injects failure with no active primary and proves no `PassiveLayout` transfers; the other combines root-close failure with an allocation primary and proves the primary identity survives while evidence/save/config owners are all closed. The `after_config_open` row must assert the config fd was recorded before the checkpoint and closed exactly once.

The three moved allocator rows are exact: non-approved root creates nothing; 128 evidence-name collisions make exactly 128 `mkdir` calls and raise; forced `0755` drift after `fchmod` raises. Add this fixture before the remaining rows:

```python
@pytest.fixture
def passive_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[passive.PassiveLayout]:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "c" * 32)
    layout = passive._allocate_passive_layout(root)
    expected = _expected_passive_config(
        layout.evidence_dir, layout.isolated_save_dir
    )
    assert layout.config_path.read_bytes() == expected
    assert layout.config_sha256 == sha256(expected).hexdigest()
    try:
        yield layout
    finally:
        layout.close()
```

```python
def _configure_layout_test_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    token: str = "d" * 32,
) -> Path:
    root = tmp_path / "data" / "oracle"
    root.mkdir(parents=True)
    monkeypatch.setattr(passive, "_approved_evidence_root", lambda: root)
    monkeypatch.setattr(passive, "_utc_leaf_prefix", lambda: "20260731T191100000000Z")
    monkeypatch.setattr(passive, "_random_token", lambda: token)
    return root


def _layout_names(root: Path, token: str = "d" * 32) -> tuple[Path, Path]:
    stem = f"20260731T191100000000Z-{token}"
    return root / f"{stem}-evidence", root / f"{stem}-save"


def test_allocate_layout_nonapproved_root_creates_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approved = _configure_layout_test_root(tmp_path, monkeypatch)
    requested = tmp_path / "not-approved"
    requested.mkdir()
    mkdir_calls = 0
    original_mkdir = passive.os.mkdir

    def mkdir(*args: object, **kwargs: object) -> None:
        nonlocal mkdir_calls
        mkdir_calls += 1
        original_mkdir(*args, **kwargs)

    monkeypatch.setattr(passive.os, "mkdir", mkdir)
    with pytest.raises(passive.PassiveProbeError, match="approved"):
        passive._allocate_passive_layout(requested)
    assert mkdir_calls == 0
    assert tuple(approved.iterdir()) == ()


def test_allocate_layout_exhausts_exactly_128_evidence_name_collisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "4" * 32)
    evidence, _save = _layout_names(root, "4" * 32)
    evidence.mkdir()
    mkdir_calls = 0
    original_mkdir = passive.os.mkdir

    def mkdir(name: str, mode: int, *, dir_fd: int) -> None:
        nonlocal mkdir_calls
        mkdir_calls += 1
        original_mkdir(name, mode, dir_fd=dir_fd)

    monkeypatch.setattr(passive.os, "mkdir", mkdir)
    with pytest.raises(passive.PassiveProbeError, match="128 attempts"):
        passive._allocate_passive_layout(root)
    assert mkdir_calls == 128


def test_allocate_layout_rejects_directory_mode_drift_after_fchmod(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "5" * 32)
    child_fds: set[int] = set()
    original_child = oracle_boot._open_child_directory
    original_fstat = passive.os.fstat

    def open_child(*args: object, **kwargs: object):
        handle = original_child(*args, **kwargs)
        child_fds.add(handle.fd)
        return handle

    def fstat(descriptor: int) -> os.stat_result:
        observed = original_fstat(descriptor)
        if descriptor in child_fds:
            values = list(observed)
            values[0] = stat.S_IFDIR | 0o755
            return os.stat_result(values)
        return observed

    monkeypatch.setattr(oracle_boot, "_open_child_directory", open_child)
    monkeypatch.setattr(passive.os, "fstat", fstat)
    with pytest.raises(passive.PassiveProbeError, match="mode drifted"):
        passive._allocate_passive_layout(root)


@pytest.mark.parametrize("collision", ("evidence", "save", "config"))
def test_allocate_layout_never_traverses_any_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    collision: str,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch)
    evidence, save = _layout_names(root)
    sentinel = b"collision-sentinel"
    original_mkdir = passive.os.mkdir
    if collision == "evidence":
        evidence.mkdir()
        (evidence / "sentinel").write_bytes(sentinel)
    elif collision == "save":
        save.mkdir()
        (save / "sentinel").write_bytes(sentinel)
    else:
        def mkdir_with_config(name: str, mode: int, *, dir_fd: int) -> None:
            original_mkdir(name, mode, dir_fd=dir_fd)
            if name == evidence.name:
                (root / name / "passive.cfg").write_bytes(sentinel)
        monkeypatch.setattr(passive.os, "mkdir", mkdir_with_config)
    with pytest.raises((passive.PassiveProbeError, FileExistsError)):
        passive._allocate_passive_layout(root)
    collision_path = evidence if collision in {"evidence", "config"} else save
    expected_file = collision_path / ("passive.cfg" if collision == "config" else "sentinel")
    assert expected_file.read_bytes() == sentinel


@pytest.mark.parametrize(
    "boundary",
    (
        "after_evidence_mkdir", "after_save_mkdir", "after_evidence_open", "after_save_open",
        "after_config_open", "after_config_write", "after_config_fsync", "after_evidence_fsync",
    ),
)
def test_layout_interrupt_preserves_nodes_and_closes_each_acquisition_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "e" * 32)
    captured_handles: list[oracle_boot._DirectoryHandle] = []
    close_ids: list[int] = []
    config_fds: list[int] = []
    config_close_count: dict[int, int] = {}
    original_absolute = oracle_boot._open_absolute_directory
    original_child = oracle_boot._open_child_directory
    original_handle_close = oracle_boot._DirectoryHandle.close
    original_open = passive.os.open
    original_close = passive.os.close

    def open_absolute(*args: object, **kwargs: object) -> oracle_boot._DirectoryHandle:
        handle = original_absolute(*args, **kwargs)
        captured_handles.append(handle)
        return handle

    def open_child(*args: object, **kwargs: object) -> oracle_boot._DirectoryHandle:
        handle = original_child(*args, **kwargs)
        captured_handles.append(handle)
        return handle

    def tracked_handle_close(handle: oracle_boot._DirectoryHandle) -> None:
        if handle.fd >= 0:
            close_ids.append(id(handle))
        original_handle_close(handle)

    def tracked_open(name: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if name == "passive.cfg":
            config_fds.append(descriptor)
        return descriptor

    def tracked_close(descriptor: int) -> None:
        if descriptor in config_fds:
            config_close_count[descriptor] = config_close_count.get(descriptor, 0) + 1
        original_close(descriptor)

    monkeypatch.setattr(oracle_boot, "_open_absolute_directory", open_absolute)
    monkeypatch.setattr(oracle_boot, "_open_child_directory", open_child)
    monkeypatch.setattr(oracle_boot._DirectoryHandle, "close", tracked_handle_close)
    monkeypatch.setattr(passive.os, "open", tracked_open)
    monkeypatch.setattr(passive.os, "close", tracked_close)
    monkeypatch.setattr(
        passive,
        "_layout_checkpoint",
        lambda observed: (_ for _ in ()).throw(KeyboardInterrupt(observed)) if observed == boundary else None,
    )
    with pytest.raises(KeyboardInterrupt, match=boundary):
        passive._allocate_passive_layout(root)
    assert captured_handles and all(handle.fd == -1 for handle in captured_handles)
    assert len(close_ids) == len(set(close_ids)) == len(captured_handles)
    assert all(count == 1 for count in config_close_count.values())
    assert tuple(root.iterdir())


def test_allocate_layout_retries_partial_config_writes_until_exact_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "f" * 32)
    original_write = passive.os.write
    calls = 0

    def one_byte_write(descriptor: int, payload: memoryview) -> int:
        nonlocal calls
        calls += 1
        return original_write(descriptor, bytes(payload[:1]))

    monkeypatch.setattr(passive.os, "write", one_byte_write)
    layout = passive._allocate_passive_layout(root)
    try:
        expected = passive._encode_passive_config(layout)
        assert layout.config_path.read_bytes() == expected
        assert layout.config_sha256 == sha256(expected).hexdigest()
        assert calls == len(expected)
    finally:
        layout.close()


def test_trace_target_absence_is_proved_twice_after_config_fsync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "1" * 32)
    evidence, _save = _layout_names(root, "1" * 32)
    original_stat = passive.os.stat
    trace_stats = 0

    def substitute_on_second_stat(path: object, *args: object, **kwargs: object) -> os.stat_result:
        nonlocal trace_stats
        if os.fspath(path) == "passive-trace.ndjson":
            trace_stats += 1
            if trace_stats == 2:
                (evidence / "passive-trace.ndjson").write_bytes(b"replacement")
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(passive.os, "stat", substitute_on_second_stat)
    with pytest.raises(passive.PassiveProbeError, match="trace target already exists"):
        passive._allocate_passive_layout(root)
    assert trace_stats == 2
    assert (evidence / "passive.cfg").exists()


@pytest.mark.parametrize("replacement", ("approved_root", "evidence_name"))
def test_allocate_layout_rejects_root_or_named_directory_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replacement: str,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "2" * 32)
    evidence, _save = _layout_names(root, "2" * 32)
    fired = False

    def replace_after_durability(boundary: str) -> None:
        nonlocal fired
        if fired or boundary != "after_evidence_fsync":
            return
        fired = True
        if replacement == "approved_root":
            held = root.with_name("oracle-held")
            root.rename(held)
            root.mkdir()
        else:
            held = evidence.with_name(evidence.name + "-held")
            evidence.rename(held)
            evidence.mkdir(mode=0o700)

    monkeypatch.setattr(passive, "_layout_checkpoint", replace_after_durability)
    with pytest.raises(passive.PassiveProbeError, match="changed|replaced|identity"):
        passive._allocate_passive_layout(root)
    assert fired is True


def test_allocate_layout_close_failure_preserves_primary_and_still_closes_all_owners(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "3" * 32)
    primary = RuntimeError("injected allocation interruption")
    captured: list[oracle_boot._DirectoryHandle] = []
    original_absolute = oracle_boot._open_absolute_directory
    original_child = oracle_boot._open_child_directory
    original_close = oracle_boot._DirectoryHandle.close

    def capture_absolute(*args: object, **kwargs: object) -> oracle_boot._DirectoryHandle:
        handle = original_absolute(*args, **kwargs)
        captured.append(handle)
        return handle

    def capture_child(*args: object, **kwargs: object) -> oracle_boot._DirectoryHandle:
        handle = original_child(*args, **kwargs)
        captured.append(handle)
        return handle

    def close_with_one_failure(handle: oracle_boot._DirectoryHandle) -> None:
        if handle.fd >= 0 and handle.path.name.endswith("-save"):
            descriptor = handle.fd
            handle.fd = -1
            os.close(descriptor)
            raise OSError("save handle close failed")
        original_close(handle)

    monkeypatch.setattr(oracle_boot, "_open_absolute_directory", capture_absolute)
    monkeypatch.setattr(oracle_boot, "_open_child_directory", capture_child)
    monkeypatch.setattr(oracle_boot._DirectoryHandle, "close", close_with_one_failure)
    monkeypatch.setattr(
        passive,
        "_layout_checkpoint",
        lambda boundary: (_ for _ in ()).throw(primary) if boundary == "after_save_open" else None,
    )
    with pytest.raises(RuntimeError) as caught:
        passive._allocate_passive_layout(root)
    assert caught.value is primary
    assert all(handle.fd == -1 for handle in captured)
    assert any("save handle close failed" in note for note in getattr(primary, "__notes__", ()))


def test_allocate_layout_root_close_failure_transfers_no_layout_and_closes_children(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "6" * 32)
    captured: list[oracle_boot._DirectoryHandle] = []
    primary = OSError("approved root close failed")
    original_absolute = oracle_boot._open_absolute_directory
    original_child = oracle_boot._open_child_directory
    original_close = oracle_boot._DirectoryHandle.close

    def capture_absolute(*args: object, **kwargs: object):
        handle = original_absolute(*args, **kwargs)
        captured.append(handle)
        return handle

    def capture_child(*args: object, **kwargs: object):
        handle = original_child(*args, **kwargs)
        captured.append(handle)
        return handle

    def close(handle: oracle_boot._DirectoryHandle) -> None:
        if handle.path == root and handle.fd >= 0:
            descriptor = handle.fd
            handle.fd = -1
            os.close(descriptor)
            raise primary
        original_close(handle)

    monkeypatch.setattr(oracle_boot, "_open_absolute_directory", capture_absolute)
    monkeypatch.setattr(oracle_boot, "_open_child_directory", capture_child)
    monkeypatch.setattr(oracle_boot._DirectoryHandle, "close", close)
    with pytest.raises(OSError) as caught:
        passive._allocate_passive_layout(root)
    assert caught.value is primary
    assert len(captured) == 3 and all(handle.fd == -1 for handle in captured)


def test_allocate_layout_primary_survives_root_close_and_all_owners_close_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _configure_layout_test_root(tmp_path, monkeypatch, "7" * 32)
    primary = KeyboardInterrupt("after config open")
    captured: list[oracle_boot._DirectoryHandle] = []
    config_fds: list[int] = []
    config_close_count: dict[int, int] = {}
    original_absolute = oracle_boot._open_absolute_directory
    original_child = oracle_boot._open_child_directory
    original_handle_close = oracle_boot._DirectoryHandle.close
    original_open = passive.os.open
    original_close = passive.os.close

    def capture(operation: Callable[..., oracle_boot._DirectoryHandle]):
        def run(*args: object, **kwargs: object):
            handle = operation(*args, **kwargs)
            captured.append(handle)
            return handle
        return run

    def opening(name: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if name == "passive.cfg":
            config_fds.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor in config_fds:
            config_close_count[descriptor] = config_close_count.get(descriptor, 0) + 1
        original_close(descriptor)

    def close_handle(handle: oracle_boot._DirectoryHandle) -> None:
        if handle.path == root and handle.fd >= 0:
            descriptor = handle.fd
            handle.fd = -1
            original_close(descriptor)
            raise OSError("approved root close failed")
        original_handle_close(handle)

    monkeypatch.setattr(oracle_boot, "_open_absolute_directory", capture(original_absolute))
    monkeypatch.setattr(oracle_boot, "_open_child_directory", capture(original_child))
    monkeypatch.setattr(oracle_boot._DirectoryHandle, "close", close_handle)
    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    monkeypatch.setattr(
        passive,
        "_layout_checkpoint",
        lambda boundary: (_ for _ in ()).throw(primary)
        if boundary == "after_config_open"
        else None,
    )
    with pytest.raises(KeyboardInterrupt) as caught:
        passive._allocate_passive_layout(root)
    assert caught.value is primary
    assert len(config_fds) == 1 and config_close_count[config_fds[0]] == 1
    assert all(handle.fd == -1 for handle in captured)
    assert any("approved root" in note for note in primary.__notes__)
```

- [ ] **Step 2: Run the allocation RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'allocate_layout or trace_target_absence or layout_interrupt'
```

Expected: allocation helpers or complete boundary ownership are missing.

- [ ] **Step 3: Implement retained no-follow allocation and exclusive config creation**

Use this complete body:

```python
def _allocate_passive_layout(evidence_root: Path) -> PassiveLayout:
    approved = _approved_evidence_root()
    if evidence_root != approved or not evidence_root.is_absolute():
        raise PassiveProbeError("evidence_root is not the approved evidence root")
    root_handle: oracle_boot._DirectoryHandle | None = oracle_boot._open_absolute_directory(
        approved, "approved evidence root"
    )
    evidence_handle: oracle_boot._DirectoryHandle | None = None
    save_handle: oracle_boot._DirectoryHandle | None = None
    try:
        for _attempt in range(128):
            stem = f"{_utc_leaf_prefix()}-{_random_token()}"
            evidence_name = f"{stem}-evidence"
            save_name = f"{stem}-save"
            try:
                os.mkdir(evidence_name, 0o700, dir_fd=root_handle.fd)
            except FileExistsError:
                continue
            _layout_checkpoint("after_evidence_mkdir")
            os.mkdir(save_name, 0o700, dir_fd=root_handle.fd)
            _layout_checkpoint("after_save_mkdir")
            evidence_dir = approved / evidence_name
            save_dir = approved / save_name
            evidence_handle = oracle_boot._open_child_directory(
                root_handle,
                evidence_name,
                evidence_dir,
                os.stat(evidence_name, dir_fd=root_handle.fd, follow_symlinks=False),
            )
            _layout_checkpoint("after_evidence_open")
            save_handle = oracle_boot._open_child_directory(
                root_handle,
                save_name,
                save_dir,
                os.stat(save_name, dir_fd=root_handle.fd, follow_symlinks=False),
            )
            _layout_checkpoint("after_save_open")
            os.fchmod(evidence_handle.fd, 0o700)
            os.fchmod(save_handle.fd, 0o700)
            evidence_stat = os.fstat(evidence_handle.fd)
            save_stat = os.fstat(save_handle.fd)
            if (
                stat.S_IMODE(evidence_stat.st_mode) != 0o700
                or stat.S_IMODE(save_stat.st_mode) != 0o700
            ):
                raise PassiveProbeError("passive private directory mode drifted")
            provisional = PassiveLayout(
                evidence_dir=evidence_dir,
                evidence_handle=evidence_handle,
                evidence_identity=_identity(evidence_dir, evidence_stat),
                isolated_save_dir=save_dir,
                isolated_save_handle=save_handle,
                isolated_save_identity=_identity(save_dir, save_stat),
                config_path=evidence_dir / "passive.cfg",
                config_identity=PathIdentity("", 0, 0, 0),
                config_sha256="",
                trace_path=evidence_dir / "passive-trace.ndjson",
            )
            payload = _encode_passive_config(provisional)
            try:
                config_fd = os.open(
                    "passive.cfg",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=evidence_handle.fd,
                )
            except FileExistsError as error:
                raise PassiveProbeError("passive config target already exists") from error
            config_primary: BaseException | None = None
            try:
                _layout_checkpoint("after_config_open")
                os.fchmod(config_fd, 0o600)
                view = memoryview(payload)
                while view:
                    written = os.write(config_fd, view)
                    if written <= 0:
                        raise OSError("short passive config write")
                    view = view[written:]
                _layout_checkpoint("after_config_write")
                os.fsync(config_fd)
                _layout_checkpoint("after_config_fsync")
                config_stat = os.fstat(config_fd)
                if stat.S_IMODE(config_stat.st_mode) != 0o600:
                    raise PassiveProbeError("passive config mode drifted")
            except BaseException as error:
                config_primary = error
                raise
            finally:
                try:
                    os.close(config_fd)
                except BaseException as close_error:
                    if config_primary is None:
                        raise
                    config_primary.add_note(
                        f"secondary passive config descriptor close failure: {close_error}"
                    )
            os.fsync(evidence_handle.fd)
            _layout_checkpoint("after_evidence_fsync")
            for _absence_pass in range(2):
                try:
                    os.stat(
                        "passive-trace.ndjson",
                        dir_fd=evidence_handle.fd,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    continue
                raise PassiveProbeError("passive trace target already exists")
            root_named_after = os.stat(approved, follow_symlinks=False)
            evidence_named_after = os.stat(
                evidence_name, dir_fd=root_handle.fd, follow_symlinks=False
            )
            save_named_after = os.stat(
                save_name, dir_fd=root_handle.fd, follow_symlinks=False
            )
            config_named_after = os.stat(
                "passive.cfg",
                dir_fd=evidence_handle.fd,
                follow_symlinks=False,
            )
            if (
                _identity(approved, root_named_after)
                != _identity(approved, os.fstat(root_handle.fd))
                or _identity(evidence_dir, evidence_named_after)
                != _identity(evidence_dir, os.fstat(evidence_handle.fd))
                or _identity(save_dir, save_named_after)
                != _identity(save_dir, os.fstat(save_handle.fd))
                or not _same_save_metadata(config_stat, config_named_after)
            ):
                raise PassiveProbeError("passive layout identity changed before return")
            provisional.config_identity = _identity(provisional.config_path, config_stat)
            provisional.config_sha256 = hashlib.sha256(payload).hexdigest()
            root_owned = root_handle
            root_handle = None
            root_owned.close()
            return provisional
        raise PassiveProbeError("could not allocate passive layout after 128 attempts")
    except BaseException as primary:
        for label, handle in (
            ("isolated-save handle close", save_handle),
            ("evidence handle close", evidence_handle),
        ):
            if handle is None:
                continue
            try:
                handle.close()
            except BaseException as secondary:
                primary.add_note(f"secondary {label} failure: {secondary}")
        raise
    finally:
        active = sys.exception()
        if root_handle is not None:
            root_owned = root_handle
            root_handle = None
            try:
                root_owned.close()
            except BaseException as secondary:
                if active is None:
                    raise
                active.add_note(f"secondary approved-root handle close failure: {secondary}")
```

- [ ] **Step 4: Run layout/config GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'allocate_layout or passive_config or layout_interrupt or trace_target_absence'
```

Expected: all selected tests pass, including exact 128-collision exhaustion, interruption after each `mkdir`/handle return, retained created nodes, mode drift, config target collision, and exact config bytes/hash.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the private-layout gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: allocate private passive oracle layout"
```

### Task 9: Implement the monotone marker and prompt reducer

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces exact `PASSIVE_MARKERS`, `PASSIVE_INSTRUCTIONS`, `RECORD_ERROR_CODES`, and `MARKER_ONLY_CODES` constants.
- Produces frozen `_MarkerProgress(markers, prompt_count, complete)` and `_advance_marker_progress(payload, prior) -> tuple[_MarkerProgress, tuple[str, ...]]`.
- Accepts passive progress/completion/failure messages only as complete LF-delimited logical lines: either the exact bare test line or the exact BepInEx prefix `[Info   :SSR Executable Oracle] ` plus the exact message. Any prefix, suffix, CR, truncated final line, or unknown ready/failure spelling is terminal.
- Emits exactly four prompts and never emits one before its authenticated prerequisite.

- [ ] **Step 1: Add exact prompt-order RED tests**

```python
def _canonical_payload_through(index: int) -> bytes:
    return ("\n".join(passive.PASSIVE_MARKERS[: index + 1]) + "\n").encode("ascii")


def test_marker_reducer_emits_each_prompt_once_after_its_prerequisite() -> None:
    state = passive._MarkerProgress(markers=(), prompt_count=0, complete=False)
    prompts: list[str] = []
    for index in range(len(passive.PASSIVE_MARKERS)):
        state, emitted = passive._advance_marker_progress(
            _canonical_payload_through(index),
            state,
        )
        prompts.extend(emitted)
    state, emitted = passive._advance_marker_progress(
        _canonical_payload_through(len(passive.PASSIVE_MARKERS) - 1),
        state,
    )
    prompts.extend(emitted)
    assert tuple(prompts) == passive.PASSIVE_INSTRUCTIONS
    assert state.markers == passive.PASSIVE_MARKERS
    assert state.complete is True


@pytest.mark.parametrize(
    "payload",
    (
        b"SSR oracle passive trace ready: 0/3\n"
        b"BepInEx 5.4.23.5\n"
        b"Unity v2018.4.25f1\n"
        b"SSR oracle boot probe loaded\n",
        b"BepInEx 5.4.23.5\nSSR oracle passive trace ready: 1/3\n",
        b"BepInEx 5.4.23.5\nUnity v2018.4.25f1\nSSR oracle boot probe loaded\nSSR oracle passive trace ready: 0/3\nSSR oracle passive trace ready: 0/3\n",
        b"BepInEx 5.4.23.5\nUnity v2018.4.25f1\nSSR oracle boot probe loaded\nSSR oracle passive trace ready: 3/3\n",
    ),
)
def test_marker_reducer_rejects_gap_duplicate_and_unknown_progress(payload: bytes) -> None:
    with pytest.raises(passive.PassiveProbeError, match="passive marker"):
        passive._advance_marker_progress(
            payload,
            passive._MarkerProgress(markers=(), prompt_count=0, complete=False),
        )


@pytest.mark.parametrize(
    "payload",
    (
        b"prefix SSR oracle passive trace ready: 0/3\n",
        b"SSR oracle passive trace ready: 0/3 suffix\n",
        b"SSR oracle passive trace ready: 0/3\r\n",
        b"SSR oracle passive trace ready: 0/3",
        b"[Info   :wrong] SSR oracle passive trace ready: 0/3\n",
        b"SSR oracle passive trace complete!\n",
        b"SSR oracle passive trace failed: settle_timeout suffix\n",
    ),
)
def test_passive_protocol_messages_reject_nonexact_physical_lines(payload: bytes) -> None:
    with pytest.raises(passive.PassiveProbeError, match="passive log line"):
        passive._passive_log_messages(payload)
```

- [ ] **Step 2: Run marker-reducer RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'marker_reducer or passive_protocol_messages'
```

Expected: marker constants or `_advance_marker_progress` is missing.

- [ ] **Step 3: Add exact constants and reducer code**

```python
PASSIVE_MARKERS = (
    "BepInEx 5.4.23.5",
    "Unity v2018.4.25f1",
    "SSR oracle boot probe loaded",
    "SSR oracle passive trace ready: 0/3",
    "SSR oracle passive trace ready: 1/3",
    "SSR oracle passive trace ready: 2/3",
    "SSR oracle passive trace complete",
)

PASSIVE_INSTRUCTIONS = (
    "SSR passive probe: press and release Action on default Start; wait for Profile Select; press and release Action on default empty Slot 1; then release every control and wait.",
    "SSR passive probe: ready 0/3 — tap one direction that visibly succeeds; release every control and wait.",
    "SSR passive probe: ready 1/3 — tap one direction that is visibly blocked; release every control and wait.",
    "SSR passive probe: ready 2/3 — press Undo once; release every control and wait.",
)

RECORD_ERROR_CODES = frozenset(
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
        "save_path_changed",
    }
)

MARKER_ONLY_CODES = frozenset(
    {
        "invalid_mode",
        "invalid_configuration",
        "invalid_assembly",
        "invalid_reflection",
        "invalid_path",
        "trace_exists",
        "save_redirect_failed",
        "trace_io_failed",
    }
)


@dataclass(frozen=True, slots=True)
class _MarkerProgress:
    markers: tuple[str, ...]
    prompt_count: int
    complete: bool


def _advance_marker_progress(
    payload: bytes,
    prior: _MarkerProgress,
) -> tuple[_MarkerProgress, tuple[str, ...]]:
    passive_messages = _passive_log_messages(payload)
    for message in passive_messages:
        if message.startswith("SSR oracle passive trace failed: "):
            continue
        if message not in PASSIVE_MARKERS[3:]:
            raise PassiveProbeError(f"unknown passive marker line: {message}")

    complete_lines = tuple(payload.split(b"\n")[:-1])
    marker_positions: list[int | None] = []
    for marker_index, marker in enumerate(PASSIVE_MARKERS):
        if marker_index < 3:
            positions = tuple(
                line_index
                for line_index, line in enumerate(complete_lines)
                if line == marker.encode("ascii")
                or oracle_boot._payload_contains_boot_marker(line, marker)
            )
        else:
            encoded = marker.encode("ascii")
            positions = tuple(
                line_index
                for line_index, line in enumerate(complete_lines)
                if encoded in line
            )
        if len(positions) > 1:
            raise PassiveProbeError("duplicate passive marker")
        marker_positions.append(positions[0] if positions else None)

    observed_count = 0
    for position in marker_positions:
        if position is None:
            break
        observed_count += 1
    if any(position is not None for position in marker_positions[observed_count:]):
        raise PassiveProbeError("passive marker prefix has a gap")
    observed_positions = marker_positions[:observed_count]
    if any(
        left is None or right is None or left >= right
        for left, right in zip(observed_positions, observed_positions[1:])
    ):
        raise PassiveProbeError("passive marker order changed")
    observed = PASSIVE_MARKERS[:observed_count]
    if observed[: len(prior.markers)] != prior.markers:
        raise PassiveProbeError("passive marker state regressed")
    prompt_thresholds = (3, 4, 5, 6)
    target_prompt_count = sum(observed_count >= threshold for threshold in prompt_thresholds)
    if target_prompt_count < prior.prompt_count:
        raise PassiveProbeError("passive prompt state regressed")
    emitted = PASSIVE_INSTRUCTIONS[prior.prompt_count:target_prompt_count]
    return (
        _MarkerProgress(
            markers=observed,
            prompt_count=target_prompt_count,
            complete=observed_count == len(PASSIVE_MARKERS),
        ),
        emitted,
    )
```

Define the exact physical-line decoder used above and later by Task 11:

```python
_PASSIVE_LOG_PREFIX = "[Info   :SSR Executable Oracle] "
_PASSIVE_STEM = "SSR oracle passive trace "


def _passive_log_messages(payload: bytes) -> tuple[str, ...]:
    if b"\r" in payload and b"SSR oracle passive trace " in payload:
        raise PassiveProbeError("malformed passive log line: CR is forbidden")
    if b"SSR oracle passive trace " in payload and not payload.endswith(b"\n"):
        raise PassiveProbeError("malformed passive log line: final LF is required")
    messages: list[str] = []
    for raw in payload.split(b"\n")[:-1]:
        try:
            line = raw.decode("utf-8", "strict")
        except UnicodeDecodeError as error:
            if b"SSR oracle passive trace " in raw:
                raise PassiveProbeError("malformed passive log line: invalid UTF-8") from error
            continue
        if _PASSIVE_STEM not in line:
            continue
        if line.startswith(_PASSIVE_LOG_PREFIX):
            message = line.removeprefix(_PASSIVE_LOG_PREFIX)
        elif line.startswith(_PASSIVE_STEM):
            message = line
        else:
            raise PassiveProbeError(f"malformed passive log line: {line!r}")
        legal = message in PASSIVE_MARKERS[3:] or any(
            message == f"SSR oracle passive trace failed: {code}"
            for code in RECORD_ERROR_CODES | MARKER_ONLY_CODES
        )
        if not legal:
            raise PassiveProbeError(f"malformed passive log line: {line!r}")
        messages.append(message)
    return tuple(messages)
```

- [ ] **Step 4: Run marker-reducer GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'marker_reducer or passive_protocol_messages'
```

Expected: all prompt, gap, duplicate, unknown, and replayed-payload rows pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the marker reducer**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: authenticate passive oracle prompts"
```

### Task 10A: Define trace summaries, observations, and retained seals

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Consumes `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun`, `require_passive_success`, `ErrorRecord`, and `OracleProtocolError` from `ssr_env.oracle_protocol`.
- Produces frozen `TraceSummary` and `_TraceObservation` with exact fields below.
- Produces `_TraceFileSeal`, `TraceSummary`, and `_TraceObservation`; the observation always contains the exact raw bytes and the seal used to authenticate them.
- Stable malformed and partial bytes remain in place with `parse_status="malformed"`; absence returns `None` only when `required=False`.

- [ ] **Step 1: Add exact trace-model and retained-byte RED tests**

```python
from dataclasses import replace


@pytest.fixture
def terminal_error_trace() -> bytes:
    path = Path(__file__).parent / "fixtures" / "oracle_trace" / "passive-error.ndjson"
    payload = path.read_bytes()
    assert payload.endswith(b"\n")
    assert payload.count(b"\n") == 4
    assert b'"code":"settle_timeout","message":"input did not settle"' in payload
    return payload


@pytest.fixture
def mismatch_error_trace(terminal_error_trace: bytes) -> bytes:
    old = b'"code":"settle_timeout","message":"input did not settle"'
    new = b'"code":"state_replaced","message":"game state identity changed"'
    assert terminal_error_trace.count(old) == 1
    return terminal_error_trace.replace(old, new)


def _write_trace(layout: passive.PassiveLayout, payload: bytes) -> None:
    layout.trace_path.write_bytes(payload)


def test_trace_summary_model_retains_valid_error_and_raw_bytes(
    passive_layout: passive.PassiveLayout,
    terminal_error_trace: bytes,
) -> None:
    summary = passive.TraceSummary(
        str(passive_layout.trace_path), "valid_error", "error", "settle_timeout",
        4, 1, sha256(terminal_error_trace).hexdigest(), len(terminal_error_trace),
    )
    assert summary.parse_status == "valid_error"
    assert summary.error_code == "settle_timeout"
    assert summary.sha256 == sha256(terminal_error_trace).hexdigest()
    assert summary.size == len(terminal_error_trace)


def test_trace_observation_model_allows_optional_absence(
    passive_layout: passive.PassiveLayout,
) -> None:
    identity = passive.PathIdentity(str(passive_layout.trace_path), 1, 2, 0o600)
    seal = passive._TraceFileSeal(identity, (1, 2, stat.S_IFREG | 0o600, 0, 7), 0, 7, 8)
    summary = passive.TraceSummary(str(passive_layout.trace_path), "malformed", None, None, None, None, sha256(b"").hexdigest(), 0)
    observed = passive._TraceObservation(seal, identity, 0, 7, 8, summary, None, b"")
    assert observed.raw_bytes == b""
    assert observed.run is None and observed.summary.outcome is None


def test_stable_trace_requires_exact_bytes_not_only_equal_summary(
    passive_layout: passive.PassiveLayout,
) -> None:
    identity = passive.PathIdentity(str(passive_layout.trace_path), 1, 2, 0o600)
    seal = passive._TraceFileSeal(identity, (1, 2, stat.S_IFREG | 0o600, 5, 7), 5, 7, 8)
    summary = passive.TraceSummary(str(passive_layout.trace_path), "malformed", None, None, None, None, sha256(b"first").hexdigest(), 5)
    first = passive._TraceObservation(seal, identity, 5, 7, 8, summary, None, b"first")
    second = replace(first, raw_bytes=b"other")
    assert first.summary == second.summary
    assert first != second and first.raw_bytes != second.raw_bytes


def test_trace_matches_exact_seal_without_any_io(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passive_layout.trace_path.write_bytes(b"trace")
    observed = passive_layout.trace_path.stat(follow_symlinks=False)
    identity = passive._identity(passive_layout.trace_path, observed)
    seal = passive._TraceFileSeal(
        identity,
        oracle_boot._stat_identity(observed),
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
    )
    forbidden = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("pure seal predicate performed I/O")
    )
    monkeypatch.setattr(passive.os, "open", forbidden)
    monkeypatch.setattr(passive.os, "stat", forbidden)
    monkeypatch.setattr(passive.os, "fchmod", forbidden)
    assert passive._trace_matches_seal(passive_layout, observed, seal) is True


@pytest.mark.parametrize(
    "field",
    ("device", "inode", "mode", "size", "mtime", "ctime"),
)
def test_trace_matches_seal_rejects_each_field_mismatch(
    passive_layout: passive.PassiveLayout,
    field: str,
) -> None:
    passive_layout.trace_path.write_bytes(b"trace")
    observed = passive_layout.trace_path.stat(follow_symlinks=False)
    seal = passive._TraceFileSeal(
        passive._identity(passive_layout.trace_path, observed),
        oracle_boot._stat_identity(observed),
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
    )
    changed = SimpleNamespace(
        st_dev=observed.st_dev + int(field == "device"),
        st_ino=observed.st_ino + int(field == "inode"),
        st_mode=observed.st_mode ^ (0o100 if field == "mode" else 0),
        st_size=observed.st_size + int(field == "size"),
        st_mtime_ns=observed.st_mtime_ns + int(field == "mtime"),
        st_ctime_ns=observed.st_ctime_ns + int(field == "ctime"),
    )
    assert passive._trace_matches_seal(passive_layout, changed, seal) is False
```

- [ ] **Step 2: Run trace-authentication RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'trace_summary_model or trace_observation_model or stable_trace or trace_matches_seal or trace_matches_exact_seal'
```

Expected: `TraceSummary`, descriptor-opened trace helpers, or the pure exact-seal predicate is missing; all ten Task-10A registrations are selected.

- [ ] **Step 3: Implement two-pass descriptor-opened parsing and retention**

Add imports and models. The seven predicate RED items above vary device, inode, mode, size, mtime, and ctime one at a time and require `False`, then prove an exact post-chmod seal returns `True` and performs no open, chmod, or pathname read:

```python
import io
from typing import BinaryIO

from ssr_env.oracle_protocol import (
    ErrorRecord,
    OracleProtocolError,
    OracleRun,
    read_oracle_trace_stream,
    require_passive_success,
)


@dataclass(frozen=True, slots=True)
class TraceSummary:
    path: str
    parse_status: Literal["valid_success", "valid_error", "malformed"]
    outcome: Literal["success", "error"] | None
    error_code: str | None
    record_count: int | None
    step_count: int | None
    sha256: str
    size: int


@dataclass(frozen=True, slots=True)
class _TraceObservation:
    seal: _TraceFileSeal
    identity: PathIdentity
    size: int
    mtime_ns: int
    ctime_ns: int
    summary: TraceSummary
    run: OracleRun | None
    raw_bytes: bytes


@dataclass(frozen=True, slots=True)
class _TraceFileSeal:
    identity: PathIdentity
    evidence_identity: tuple[int, int, int, int, int]
    size: int
    mtime_ns: int
    ctime_ns: int
```

Add the complete pure predicate now; Task 10B consumes it without redefining it:

```python
def _trace_matches_seal(
    layout: PassiveLayout,
    observed: os.stat_result,
    seal: _TraceFileSeal,
) -> bool:
    return (
        _identity(layout.trace_path, observed) == seal.identity
        and oracle_boot._stat_identity(observed) == seal.evidence_identity
        and observed.st_size == seal.size
        and observed.st_mtime_ns == seal.mtime_ns
        and observed.st_ctime_ns == seal.ctime_ns
    )
```

Do not open or chmod the trace in this task.

- [ ] **Step 4: Run the trace-model GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'trace_summary_model or trace_observation_model or stable_trace or trace_matches_seal or trace_matches_exact_seal'
```

Expected: all ten rows pass; frozen models retain raw bytes, exact identity, size, timestamps, parse status, nullable outcome/error fields, and the no-I/O exact-seal predicate.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit trace models**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: define retained passive trace observations"
```

### Task 10B: Validate and secure the trace exactly once

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_secure_trace_once(layout, *, required) -> _TraceFileSeal | None` and `_trace_pass(layout, seal) -> _TraceObservation`.
- Validates type/name before the only `fchmod`; both descriptor reads after the retained seal contain no mutation syscall.

- [ ] **Step 1: Add one-time-security and mutation-free-pass RED tests**

```python
def test_trace_secure_once_validates_before_chmod_and_caches_only_after_close(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passive_layout.trace_path.write_bytes(b"not-json\n")
    passive_layout.trace_path.chmod(0o644)
    events: list[str] = []
    trace_fd = -1
    named_count = 0
    fstat_count = 0
    original_open = passive.os.open
    original_stat = passive.os.stat
    original_fstat = passive.os.fstat
    original_fchmod = passive.os.fchmod
    original_close = passive.os.close

    def opening(name, flags, mode=0o777, *, dir_fd=None):
        nonlocal trace_fd
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if name == passive_layout.trace_path.name and dir_fd == passive_layout.evidence_handle.fd:
            trace_fd = descriptor
        return descriptor

    def named(name, *args, **kwargs):
        nonlocal named_count
        observed = original_stat(name, *args, **kwargs)
        if os.fspath(name) == passive_layout.trace_path.name:
            events.append("named_validate" if named_count == 0 else "named_seal")
            named_count += 1
        return observed

    def descriptor(fd: int):
        nonlocal fstat_count
        observed = original_fstat(fd)
        if fd == trace_fd:
            events.append("fstat_validate" if fstat_count == 0 else "fstat_seal")
            fstat_count += 1
        return observed

    def chmod(fd: int, mode: int) -> None:
        assert events == ["named_validate", "fstat_validate"]
        assert fd == trace_fd and mode == 0o600
        events.append("fchmod")
        original_fchmod(fd, mode)

    def close(fd: int) -> None:
        if fd == trace_fd:
            events.append("close")
        original_close(fd)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "stat", named)
    monkeypatch.setattr(passive.os, "fstat", descriptor)
    monkeypatch.setattr(passive.os, "fchmod", chmod)
    monkeypatch.setattr(passive.os, "close", close)
    seal = passive._secure_trace_once(passive_layout, required=True)
    assert seal is not None
    assert events == [
        "named_validate", "fstat_validate", "fchmod",
        "named_seal", "fstat_seal", "close",
    ]
    before_reuse = tuple(events)
    assert passive._secure_trace_once(passive_layout, required=True) is seal
    assert tuple(events) == before_reuse
    assert passive_layout.trace_seal is seal


def test_trace_mutation_free_passes_make_no_mutation_syscall(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passive_layout.trace_path.write_bytes(b"not-json\n")
    seal = passive._secure_trace_once(passive_layout, required=True)
    assert seal is not None

    def forbidden(*_args, **_kwargs):
        raise AssertionError("mutation syscall in sealed trace pass")

    monkeypatch.setattr(passive.os, "fchmod", forbidden)
    monkeypatch.setattr(passive.os, "write", forbidden)
    monkeypatch.setattr(passive.os, "rename", forbidden)
    monkeypatch.setattr(passive.os, "unlink", forbidden)
    first = passive._trace_pass(passive_layout, seal)
    second = passive._trace_pass(passive_layout, seal)
    assert first == second
    assert first.raw_bytes == b"not-json\n"


@pytest.mark.parametrize("kind", ("symlink", "fifo", "oversize"))
def test_trace_secure_once_rejects_unbounded_or_nonregular_target(
    passive_layout: passive.PassiveLayout,
    kind: str,
) -> None:
    if kind == "symlink":
        target = passive_layout.evidence_dir / "trace-target"
        target.write_bytes(b"trace")
        passive_layout.trace_path.symlink_to(target.name)
    elif kind == "fifo":
        os.mkfifo(passive_layout.trace_path)
    else:
        with passive_layout.trace_path.open("wb") as stream:
            stream.truncate(128 * 1024 * 1024 + 1)
    with pytest.raises(passive.PassiveProbeError, match="trace|regular|bounded"):
        passive._secure_trace_once(passive_layout, required=True)


@pytest.mark.parametrize("case", ("before_secure", "after_secure_name", "same_size_bytes"))
def test_trace_substitution_or_same_size_byte_change_is_terminal(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    path = passive_layout.trace_path
    path.write_bytes(b"AAAA")
    path.chmod(0o600)
    original_open = passive.os.open

    def replace_name() -> None:
        held = path.with_name(f"held-{case}")
        path.rename(held)
        path.write_bytes(b"BBBB")
        path.chmod(0o600)

    def opening(name, flags, mode=0o777, *, dir_fd=None):
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if case == "before_secure" and name == path.name and dir_fd == passive_layout.evidence_handle.fd:
            replace_name()
        return descriptor

    monkeypatch.setattr(passive.os, "open", opening)
    if case == "before_secure":
        with pytest.raises(passive.PassiveProbeError, match="changed|stable|regular"):
            passive._secure_trace_once(passive_layout, required=True)
        return
    seal = passive._secure_trace_once(passive_layout, required=True)
    assert seal is not None
    if case == "after_secure_name":
        replace_name()
    else:
        before = path.stat(follow_symlinks=False)
        path.write_bytes(b"BBBB")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns), follow_symlinks=False)
    with pytest.raises(passive.PassiveProbeError, match="disagree|changed"):
        passive._trace_pass(passive_layout, seal)


def test_trace_secure_once_uses_post_chmod_ctime_without_fsync(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passive_layout.trace_path.write_bytes(b"trace")

    def forbidden_fsync(_descriptor: int) -> None:
        raise AssertionError("trace security must not depend on fsync")

    monkeypatch.setattr(passive.os, "fsync", forbidden_fsync)
    seal = passive._secure_trace_once(passive_layout, required=True)
    assert seal is not None
    observed = passive_layout.trace_path.stat(follow_symlinks=False)
    assert seal.ctime_ns == observed.st_ctime_ns
    assert seal.mtime_ns == observed.st_mtime_ns


def test_trace_secure_once_close_failure_does_not_commit_the_seal(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TraceCloseFailure(OSError):
        pass

    passive_layout.trace_path.write_bytes(b"trace")
    original_open = passive.os.open
    original_close = passive.os.close
    trace_fd = -1

    def opening(name, flags, mode=0o777, *, dir_fd=None):
        nonlocal trace_fd
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if name == passive_layout.trace_path.name and dir_fd == passive_layout.evidence_handle.fd:
            trace_fd = descriptor
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor == trace_fd:
            original_close(descriptor)
            raise TraceCloseFailure("trace close failed")
        original_close(descriptor)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    with pytest.raises(TraceCloseFailure, match="trace close failed"):
        passive._secure_trace_once(passive_layout, required=True)
    assert passive_layout.trace_seal is None
    assert passive_layout.trace_identity is None


@pytest.mark.parametrize("active_primary", (False, True))
def test_trace_pass_close_failure_is_exact_once_and_never_masks_primary(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    active_primary: bool,
) -> None:
    passive_layout.trace_path.write_bytes(b"not-json\n")
    seal = passive._secure_trace_once(passive_layout, required=True)
    assert seal is not None
    primary = KeyboardInterrupt("trace read interrupted")
    opened: list[int] = []
    close_count: dict[int, int] = {}
    original_open = passive.os.open
    original_read = passive.os.read
    original_close = passive.os.close
    original_fstat = passive.os.fstat

    def opening(name, flags, mode=0o777, *, dir_fd=None):
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if name == passive_layout.trace_path.name and dir_fd == passive_layout.evidence_handle.fd:
            opened.append(descriptor)
        return descriptor

    def reading(descriptor: int, maximum: int) -> bytes:
        if active_primary and descriptor in opened:
            raise primary
        return original_read(descriptor, maximum)

    def closing(descriptor: int) -> None:
        if descriptor in opened:
            close_count[descriptor] = close_count.get(descriptor, 0) + 1
            original_close(descriptor)
            raise OSError("trace pass close failed")
        original_close(descriptor)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "read", reading)
    monkeypatch.setattr(passive.os, "close", closing)
    if active_primary:
        with pytest.raises(KeyboardInterrupt) as caught:
            passive._trace_pass(passive_layout, seal)
        assert caught.value is primary
        assert any("descriptor close failure" in note for note in primary.__notes__)
    else:
        with pytest.raises(OSError, match="trace pass close failed"):
            passive._trace_pass(passive_layout, seal)
    assert len(opened) == 1 and close_count == {opened[0]: 1}
    with pytest.raises(OSError) as caught_closed:
        original_fstat(opened[0])
    assert caught_closed.value.errno == errno.EBADF
```

- [ ] **Step 2: Run the trace-seal RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'trace_secure_once or trace_mutation_free or trace_substitution or trace_pass_close_failure'
```

Expected: the old `_trace_pass(..., secure=True)` performs an `fchmod` in both passes and changes ctime itself.

- [ ] **Step 3: Implement one-time security and one mutation-free descriptor pass**

Add:

Consume Task 10A's `_trace_matches_seal` unchanged. The two literal close-failure RED rows above prove that a parser/read primary plus descriptor-close failure re-raises the identical primary with a close note, and that a close failure without a primary is raised after the descriptor is pre-cleared and proven closed.

```python
def _secure_trace_once(
    layout: PassiveLayout,
    *,
    required: bool,
) -> _TraceFileSeal | None:
    if layout.trace_seal is not None:
        return layout.trace_seal
    try:
        descriptor = os.open(
            layout.trace_path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=layout.evidence_handle.fd,
        )
    except FileNotFoundError:
        if required:
            raise PassiveProbeError("required passive trace is absent")
        return None
    try:
        named_validate = os.stat(
            layout.trace_path.name,
            dir_fd=layout.evidence_handle.fd,
            follow_symlinks=False,
        )
        descriptor_validate = os.fstat(descriptor)
        if (
            not stat.S_ISREG(named_validate.st_mode)
            or not stat.S_ISREG(descriptor_validate.st_mode)
            or not _same_save_metadata(named_validate, descriptor_validate)
            or descriptor_validate.st_size > 128 * 1024 * 1024
        ):
            raise PassiveProbeError("passive trace is not a bounded stable regular file")
        os.fchmod(descriptor, 0o600)
        named_seal = os.stat(
            layout.trace_path.name,
            dir_fd=layout.evidence_handle.fd,
            follow_symlinks=False,
        )
        descriptor_seal = os.fstat(descriptor)
        if (
            not stat.S_ISREG(descriptor_seal.st_mode)
            or not _same_save_metadata(named_seal, descriptor_seal)
        ):
            raise PassiveProbeError("passive trace changed while securing")
        seal = _TraceFileSeal(
            _identity(layout.trace_path, descriptor_seal),
            oracle_boot._stat_identity(descriptor_seal),
            descriptor_seal.st_size,
            descriptor_seal.st_mtime_ns,
            descriptor_seal.st_ctime_ns,
        )
    except BaseException as primary:
        try:
            os.close(descriptor)
        except BaseException as secondary:
            primary.add_note(f"secondary trace descriptor close failure: {secondary}")
        raise
    else:
        os.close(descriptor)
        layout.trace_identity = seal.identity
        layout.trace_seal = seal
        return seal
```

Replace `_trace_pass` with this mutation-free implementation:

```python
def _trace_pass(layout: PassiveLayout, seal: _TraceFileSeal) -> _TraceObservation:
    descriptor = os.open(
        layout.trace_path.name,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
        dir_fd=layout.evidence_handle.fd,
    )
    primary: BaseException | None = None
    try:
        named_before = os.stat(
            layout.trace_path.name,
            dir_fd=layout.evidence_handle.fd,
            follow_symlinks=False,
        )
        before = os.fstat(descriptor)
        if not _same_save_metadata(named_before, before) or not _trace_matches_seal(
            layout, before, seal
        ):
            raise PassiveProbeError("passive trace name and descriptor disagree before read")
        if not stat.S_ISREG(before.st_mode) or before.st_size > 128 * 1024 * 1024:
            raise PassiveProbeError("passive trace is not a bounded regular file")
        run: OracleRun | None
        parse_status: Literal["valid_success", "valid_error", "malformed"]
        outcome: Literal["success", "error"] | None
        error_code: str | None
        record_count: int | None
        step_count: int | None
        digest = hashlib.sha256()
        size = 0
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, 128 * 1024 * 1024 + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > 128 * 1024 * 1024:
                raise PassiveProbeError("passive trace exceeds 128 MiB")
            digest.update(chunk)
            chunks.append(chunk)
        raw_bytes = b"".join(chunks)
        try:
            run = read_oracle_trace_stream(
                io.BytesIO(raw_bytes),
                source=str(layout.trace_path),
            )
        except OracleProtocolError:
            run = None
            parse_status = "malformed"
            outcome = None
            error_code = None
            record_count = None
            step_count = None
        else:
            outcome = run.outcome
            parse_status = "valid_success" if outcome == "success" else "valid_error"
            error_code = run.terminal.code if isinstance(run.terminal, ErrorRecord) else None
            step_count = len(run.steps)
            record_count = 2 + len(run.steps) + (1 if run.initial is not None else 0)
        after = os.fstat(descriptor)
        named_after = os.stat(
            layout.trace_path.name,
            dir_fd=layout.evidence_handle.fd,
            follow_symlinks=False,
        )
        if (
            not _same_save_metadata(before, after)
            or not _same_save_metadata(named_after, after)
            or not _trace_matches_seal(layout, after, seal)
            or size != after.st_size
        ):
            raise PassiveProbeError("passive trace changed during descriptor read")
        identity = _identity(layout.trace_path, after)
        return _TraceObservation(
            seal=seal,
            identity=identity,
            size=after.st_size,
            mtime_ns=after.st_mtime_ns,
            ctime_ns=after.st_ctime_ns,
            summary=TraceSummary(
                path=str(layout.trace_path),
                parse_status=parse_status,
                outcome=outcome,
                error_code=error_code,
                record_count=record_count,
                step_count=step_count,
                sha256=digest.hexdigest(),
                size=after.st_size,
            ),
            run=run,
            raw_bytes=raw_bytes,
        )
    except BaseException as error:
        primary = error
        raise
    finally:
        owned_descriptor = descriptor
        descriptor = -1
        try:
            os.close(owned_descriptor)
        except BaseException as close_error:
            if primary is None:
                raise
            primary.add_note(
                f"secondary passive trace descriptor close failure: {close_error}"
            )
```


- [ ] **Step 4: Run the trace-seal GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'trace_secure_once or trace_mutation_free or trace_substitution or trace_pass_close_failure'
```

Expected: one post-validation chmod establishes the only seal; every later read is mutation-free and rejects name/descriptor/byte drift.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit one-time trace security**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: seal passive trace exactly once"
```

### Task 10C: Require two identical trace reads and authenticate terminal outcomes

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_read_stable_trace(layout, *, required)`, `_authenticate_record_error_trace(layout, code)`, and `_retain_post_reap_trace(layout)`.
- Uses the exact protocol API `read_oracle_trace_stream(stream: BinaryIO, *, source: str) -> OracleRun`; convenience path reopening is forbidden.

- [ ] **Step 1: Add absent/malformed/error/success and unequal-pass RED tests**

```python
def _protocol_fixture(name: str) -> bytes:
    payload = (Path(__file__).parent / "fixtures" / "oracle_trace" / name).read_bytes()
    assert payload.endswith(b"\n")
    return payload


@pytest.mark.parametrize(
    ("case", "parse_status", "outcome", "error_code"),
    (
        ("malformed", "malformed", None, None),
        ("partial", "malformed", None, None),
        ("passive-error.ndjson", "valid_error", "error", "settle_timeout"),
        ("passive-success.ndjson", "valid_success", "success", None),
    ),
)
def test_stable_trace_classifies_and_retains_exact_bytes(
    passive_layout: passive.PassiveLayout,
    case: str,
    parse_status: str,
    outcome: str | None,
    error_code: str | None,
) -> None:
    payload = {
        "malformed": b"not-json\n",
        "partial": b'{"kind":"run"',
    }.get(case)
    if payload is None:
        payload = _protocol_fixture(case)
    passive_layout.trace_path.write_bytes(payload)
    observed = passive._read_stable_trace(passive_layout, required=True)
    assert observed is not None
    assert observed.raw_bytes == payload
    assert observed.size == observed.summary.size == len(payload)
    assert observed.summary.sha256 == sha256(payload).hexdigest()
    assert observed.summary.parse_status == parse_status
    assert observed.summary.outcome == outcome
    assert observed.summary.error_code == error_code


@pytest.mark.parametrize("required", (False, True))
def test_stable_trace_absence_is_optional_only_when_requested(
    passive_layout: passive.PassiveLayout,
    required: bool,
) -> None:
    if required:
        with pytest.raises(passive.PassiveProbeError, match="required passive trace is absent"):
            passive._read_stable_trace(passive_layout, required=True)
    else:
        assert passive._read_stable_trace(passive_layout, required=False) is None
        assert passive_layout.trace_seal is None


@pytest.mark.parametrize("difference", ("raw_bytes", "seal_size", "identity"))
def test_trace_two_pass_rejects_any_unequal_authenticated_observation(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    difference: str,
) -> None:
    passive_layout.trace_path.write_bytes(b"not-json\n")
    seal = passive._secure_trace_once(passive_layout, required=True)
    assert seal is not None
    first = passive._trace_pass(passive_layout, seal)
    if difference == "raw_bytes":
        second = replace(first, raw_bytes=b"different\n")
    elif difference == "seal_size":
        second = replace(first, seal=replace(first.seal, size=first.seal.size + 1))
    else:
        second = replace(first, identity=replace(first.identity, inode=first.identity.inode + 1))
    passes = iter((first, second))
    monkeypatch.setattr(passive, "_trace_pass", lambda _layout, _seal: next(passes))
    with pytest.raises(passive.PassiveProbeError, match="not stable across two reads"):
        passive._read_stable_trace(passive_layout, required=True)


def test_trace_two_pass_calls_stream_parser_twice_with_exact_source(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import io

    payload = _protocol_fixture("passive-success.ndjson")
    passive_layout.trace_path.write_bytes(payload)
    original = passive.read_oracle_trace_stream
    calls: list[tuple[type[object], int, str]] = []

    def parse(stream, *, source: str):
        calls.append((type(stream), stream.tell(), source))
        return original(stream, source=source)

    monkeypatch.setattr(passive, "read_oracle_trace_stream", parse)
    observed = passive._read_stable_trace(passive_layout, required=True)
    assert observed is not None
    assert calls == [
        (io.BytesIO, 0, str(passive_layout.trace_path)),
        (io.BytesIO, 0, str(passive_layout.trace_path)),
    ]


@pytest.mark.parametrize(
    ("case", "expected_error"),
    (
        ("match", None),
        ("mismatch", "code mismatch"),
        ("malformed", "trace is malformed"),
        ("success", "not terminal Error"),
        ("absent", "trace is absent"),
    ),
)
def test_record_error_marker_requires_exact_closed_terminal_error(
    passive_layout: passive.PassiveLayout,
    case: str,
    expected_error: str | None,
) -> None:
    if case in {"match", "mismatch"}:
        passive_layout.trace_path.write_bytes(_protocol_fixture("passive-error.ndjson"))
    elif case == "malformed":
        passive_layout.trace_path.write_bytes(b'{"partial":')
    elif case == "success":
        passive_layout.trace_path.write_bytes(_protocol_fixture("passive-success.ndjson"))
    code = "other_code" if case == "mismatch" else "settle_timeout"
    if expected_error is None:
        observed = passive._authenticate_record_error_trace(passive_layout, code)
        assert observed.summary.parse_status == "valid_error"
        assert observed.summary.error_code == code
        assert observed.run is not None
    else:
        with pytest.raises(passive.PassiveProbeError, match=expected_error):
            passive._authenticate_record_error_trace(passive_layout, code)
```

- [ ] **Step 2: Run the two-pass authentication RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'record_error_marker or post_reap or stable_trace or trace_two_pass'
```

Expected: stable two-pass authentication or exact terminal-error matching is absent.

- [ ] **Step 3: Implement two passes over the retained seal**

```python
def _read_stable_trace(
    layout: PassiveLayout,
    *,
    required: bool,
) -> _TraceObservation | None:
    seal = _secure_trace_once(layout, required=required)
    if seal is None:
        return None
    first = _trace_pass(layout, seal)
    second = _trace_pass(layout, seal)
    if first != second or first.raw_bytes != second.raw_bytes:
        raise PassiveProbeError("passive trace was not stable across two reads")
    layout.trace_identity = second.identity
    return second


def _authenticate_record_error_trace(
    layout: PassiveLayout,
    code: str,
) -> _TraceObservation:
    try:
        observed = _read_stable_trace(layout, required=True)
    except PassiveProbeError as error:
        if str(error) == "required passive trace is absent":
            raise PassiveProbeError("record-code failure trace is absent") from error
        raise
    if observed is None:
        raise AssertionError("required trace returned None")
    if observed.summary.parse_status == "malformed":
        raise PassiveProbeError("record-code failure trace is malformed")
    if observed.summary.parse_status != "valid_error":
        raise PassiveProbeError("record-code failure trace is not terminal Error")
    if observed.summary.error_code != code:
        raise PassiveProbeError(
            f"record-code failure trace code mismatch: marker={code}, "
            f"trace={observed.summary.error_code}"
        )
    return observed


def _retain_post_reap_trace(layout: PassiveLayout) -> _TraceObservation | None:
    return _read_stable_trace(layout, required=False)
```

- [ ] **Step 4: Run trace-authentication GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'record_error_marker or post_reap or trace'
```

Expected: valid Error matches pass; absent, malformed, and mismatched record-code traces fail; malformed/partial post-reap bytes remain unchanged and summarized.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the trace gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: authenticate retained passive traces"
```

### Task 11: Integrate markers, failure traces, and the global monitor deadline

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces frozen `_PassiveMonitorOutcome(state, markers, issues, observed_failures, exit_code, trace)`.
- Produces `_wait_for_passive_trace(process, game_root, before_logs, layout, timeout_seconds, instruction_sink, process_tracker) -> _PassiveMonitorOutcome`; production callers must pass the Task 13B tracker and every poll samples it.
- Record-code markers synchronously authenticate their matching closed Error trace. Marker-only codes can terminate without a trace. Completion synchronously authenticates a valid relational success trace.

- [ ] **Step 1: Add synthetic monitor RED tests**

```python
from dataclasses import dataclass, field

from ssr_env import oracle_boot


@dataclass
class FakeProcess:
    pid: int = 9401
    exit_code: int | None = None
    poll_count: int = 0

    def poll(self) -> int | None:
        self.poll_count += 1
        return self.exit_code


@pytest.fixture
def fake_process() -> FakeProcess:
    return FakeProcess()


@dataclass
class CanonicalObserver:
    game_root: Path
    payloads: list[bytes] = field(default_factory=list)
    failures: tuple[oracle_boot._ObservedFailureLog, ...] = ()
    call_count: int = 0

    def __call__(
        self,
        game_root: Path,
        before: tuple[oracle_boot.LogFingerprint, ...],
    ) -> oracle_boot._ObservedLogPayloads:
        assert game_root == self.game_root
        assert before == ()
        payload = (
            self.payloads[min(self.call_count, len(self.payloads) - 1)]
            if self.payloads
            else None
        )
        self.call_count += 1
        return oracle_boot._ObservedLogPayloads(
            canonical_payload=payload,
            error_payloads=(() if payload is None else (payload,)),
            issues=(),
            observed_failures=self.failures,
        )


@pytest.fixture
def canonical_observer(tmp_path: Path) -> CanonicalObserver:
    game_root = tmp_path / "game"
    game_root.mkdir()
    return CanonicalObserver(game_root)


@dataclass
class FakeClock:
    now: float = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        assert 0.0 < seconds <= 0.1
        self.now += seconds


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock()


def test_monitor_authenticates_record_error_before_return(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    terminal_error_trace: bytes,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passive_layout.trace_path.write_bytes(terminal_error_trace)
    canonical_observer.payloads.append(
        b"BepInEx 5.4.23.5\nUnity v2018.4.25f1\nSSR oracle boot probe loaded\n"
        b"SSR oracle passive trace failed: settle_timeout\n"
    )
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
    )
    assert outcome.state == "failure"
    assert outcome.trace is not None
    assert outcome.trace.summary.error_code == "settle_timeout"


def test_monitor_marker_only_failure_does_not_require_trace(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_observer.payloads.append(
        b"SSR oracle passive trace failed: invalid_configuration\n"
    )
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
    )
    assert outcome.state == "failure"
    assert outcome.trace is None


def test_trace_io_failed_marker_allows_partial_trace_then_post_reap_retains_it(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial = b'{"kind":"run","schema_version":1'
    passive_layout.trace_path.write_bytes(partial)
    canonical_observer.payloads.append(
        b"SSR oracle passive trace failed: trace_io_failed\n"
    )
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
    )
    assert outcome.state == "failure"
    assert outcome.trace is None
    retained = passive._retain_post_reap_trace(passive_layout)
    assert retained is not None
    assert retained.summary.parse_status == "malformed"
    assert retained.summary.error_code is None
    assert passive_layout.trace_path.read_bytes() == partial


def test_early_exit_partial_trace_is_retained_after_reap(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    partial = b'{"kind":"run"}\n{"kind":"initial"'
    passive_layout.trace_path.write_bytes(partial)
    fake_process.exit_code = 17
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
    )
    assert outcome.state == "early_exit"
    assert outcome.exit_code == 17
    retained = passive._retain_post_reap_trace(passive_layout)
    assert retained is not None
    assert retained.summary.parse_status == "malformed"
    assert passive_layout.trace_path.read_bytes() == partial


def test_monitor_uses_one_global_deadline(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    fake_clock: FakeClock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    monkeypatch.setattr(passive.time, "monotonic", fake_clock.monotonic)
    monkeypatch.setattr(passive.time, "sleep", fake_clock.sleep)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
    )
    assert outcome.state == "timeout"
    assert fake_clock.now == pytest.approx(300.0)


@pytest.mark.parametrize(
    ("kind", "relative_path"),
    (("fallback", Path("BepInEx/LogOutput.log.1")), ("preloader", Path("preloader_1.log"))),
)
def test_monitor_stops_immediately_for_new_fallback_or_preloader_log(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    relative_path: Path,
) -> None:
    failure = oracle_boot._ObservedFailureLog(relative_path, kind, 1, 2, stat.S_IFREG | 0o600)
    canonical_observer.failures = (failure,)
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    outcome = passive._wait_for_passive_trace(
        fake_process, canonical_observer.game_root, (), passive_layout, 300, lambda _line: None
    )
    assert outcome.state == "failure"
    assert outcome.observed_failures == (failure,)
    assert fake_process.poll_count == 1


def test_monitor_completion_emits_exact_four_prompts_and_authenticates_success(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_observer.payloads.append(
        ("\n".join(passive.PASSIVE_MARKERS) + "\n").encode("ascii")
    )
    run = object()
    trace = SimpleNamespace(
        run=run,
        summary=SimpleNamespace(parse_status="valid_success"),
    )
    authenticated: list[object] = []
    instructions: list[str] = []
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    monkeypatch.setattr(passive, "_read_stable_trace", lambda *_args, **_kwargs: trace)
    monkeypatch.setattr(passive, "require_passive_success", authenticated.append)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        instructions.append,
    )
    assert outcome.state == "complete"
    assert outcome.trace is trace
    assert tuple(instructions) == passive.PASSIVE_INSTRUCTIONS
    assert authenticated == [run]


def test_monitor_samples_retained_process_tracker_before_poll(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_process.exit_code = 0
    observations: list[tuple[tuple[object, ...], int]] = []
    tracker = SimpleNamespace(
        observe=lambda rows, sampler_pid: observations.append((rows, sampler_pid))
    )
    snapshot = SimpleNamespace(rows=(), sampler_pid=8123)
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    monkeypatch.setattr(passive, "_process_snapshot", lambda: snapshot)
    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
        tracker,
    )
    assert outcome.state == "early_exit"
    assert observations == [((), 8123)]
    assert fake_process.poll_count == 1


def test_completion_marker_without_valid_success_trace_is_terminal(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passive_layout.trace_path.write_bytes(b'{"partial":\n')
    canonical_observer.payloads.append(
        ("\n".join(passive.PASSIVE_MARKERS) + "\n").encode("ascii")
    )
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    with pytest.raises(passive.PassiveProbeError, match="completion marker lacks"):
        passive._wait_for_passive_trace(
            fake_process, canonical_observer.game_root, (), passive_layout, 300, lambda _line: None
        )


def test_premature_exit_wins_over_a_late_visible_completion_payload(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_process.exit_code = 19
    canonical_observer.payloads.append(
        ("\n".join(passive.PASSIVE_MARKERS) + "\n").encode("ascii")
    )
    parsed: list[str] = []
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    monkeypatch.setattr(passive, "_read_stable_trace", lambda *_a, **_k: parsed.append("trace"))
    outcome = passive._wait_for_passive_trace(
        fake_process, canonical_observer.game_root, (), passive_layout, 300,
        lambda _line: None,
    )
    assert outcome.state == "early_exit" and outcome.exit_code == 19
    assert parsed == [] and canonical_observer.call_count == 0


def test_process_exit_during_success_trace_validation_cannot_return_complete(
    fake_process: FakeProcess,
    passive_layout: passive.PassiveLayout,
    canonical_observer: CanonicalObserver,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical_observer.payloads.append(
        ("\n".join(passive.PASSIVE_MARKERS) + "\n").encode("ascii")
    )
    polls = iter((None, 19))
    fake_process.poll = lambda: next(polls)
    trace = SimpleNamespace(
        run=object(),
        summary=SimpleNamespace(parse_status="valid_success"),
    )
    monkeypatch.setattr(oracle_boot, "_observe_changed_log_payloads", canonical_observer)
    monkeypatch.setattr(passive, "_read_stable_trace", lambda *_args, **_kwargs: trace)
    monkeypatch.setattr(passive, "require_passive_success", lambda _run: None)

    outcome = passive._wait_for_passive_trace(
        fake_process,
        canonical_observer.game_root,
        (),
        passive_layout,
        300,
        lambda _line: None,
    )

    assert outcome.state == "early_exit"
    assert outcome.exit_code == 19
    assert outcome.trace is trace
```

- [ ] **Step 2: Run monitor RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'monitor or post_reap or early_exit or premature_exit or process_exit_during or completion_marker'
```

Expected: `_PassiveMonitorOutcome` or `_wait_for_passive_trace` is missing; all twelve monitor registrations, including both process-exit races, are selected.

- [ ] **Step 3: Implement the one-deadline monitor**

Add imports, model, and exact failure extraction:

```python
import time
from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class _PassiveMonitorOutcome:
    state: Literal["complete", "failure", "timeout", "early_exit"]
    markers: tuple[str, ...]
    issues: tuple[str, ...]
    observed_failures: tuple[oracle_boot._ObservedFailureLog, ...]
    exit_code: int | None
    trace: _TraceObservation | None


def _failure_codes(payload: bytes | None) -> tuple[str, ...]:
    if payload is None:
        return ()
    prefix = "SSR oracle passive trace failed: "
    return tuple(
        message.removeprefix(prefix)
        for message in _passive_log_messages(payload)
        if message.startswith(prefix)
    )
```

Implement the monitor loop exactly:

```python
def _wait_for_passive_trace(
    process: subprocess.Popen[bytes],
    game_root: Path,
    before_logs: tuple[oracle_boot.LogFingerprint, ...],
    layout: PassiveLayout,
    timeout_seconds: int,
    instruction_sink: Callable[[str], None],
    process_tracker: _ObservedProcessTracker | None = None,
) -> _PassiveMonitorOutcome:
    deadline = time.monotonic() + timeout_seconds
    progress = _MarkerProgress(markers=(), prompt_count=0, complete=False)
    issues: list[str] = []
    failures: list[oracle_boot._ObservedFailureLog] = []
    while True:
        if process_tracker is not None:
            process_snapshot = _process_snapshot()
            process_tracker.observe(process_snapshot.rows, process_snapshot.sampler_pid)
        exit_code = process.poll()
        if exit_code is not None:
            return _PassiveMonitorOutcome(
                "early_exit", progress.markers, tuple(issues), tuple(failures), exit_code, None
            )
        observed = oracle_boot._observe_changed_log_payloads(game_root, before_logs)
        for issue in observed.issues:
            if issue not in issues:
                issues.append(issue)
        for failure in observed.observed_failures:
            if failure not in failures:
                failures.append(failure)
        if observed.observed_failures:
            return _PassiveMonitorOutcome(
                "failure", progress.markers, tuple(issues), tuple(failures), exit_code, None
            )
        codes = _failure_codes(observed.canonical_payload)
        if len(codes) > 1:
            raise PassiveProbeError("duplicate passive failure marker")
        if codes:
            code = codes[0]
            if code in RECORD_ERROR_CODES:
                trace = _authenticate_record_error_trace(layout, code)
            elif code in MARKER_ONLY_CODES:
                trace = None
            else:
                raise PassiveProbeError(f"unknown passive failure marker: {code}")
            return _PassiveMonitorOutcome(
                "failure", progress.markers, tuple(issues), tuple(failures), exit_code, trace
            )
        if observed.canonical_payload is not None:
            progress, prompts = _advance_marker_progress(observed.canonical_payload, progress)
            for prompt in prompts:
                instruction_sink(prompt)
            if progress.complete:
                trace = _read_stable_trace(layout, required=True)
                if trace is None or trace.run is None or trace.summary.parse_status != "valid_success":
                    raise PassiveProbeError("completion marker lacks a valid success trace")
                require_passive_success(trace.run)
                # Trace authentication can take long enough for the process to
                # exit after the loop-top poll. This second poll is the
                # authoritative completion boundary; an exit always wins.
                completion_exit = process.poll()
                if completion_exit is not None:
                    return _PassiveMonitorOutcome(
                        "early_exit",
                        progress.markers,
                        tuple(issues),
                        tuple(failures),
                        completion_exit,
                        trace,
                    )
                return _PassiveMonitorOutcome(
                    "complete", progress.markers, tuple(issues), tuple(failures), None, trace
                )
        now = time.monotonic()
        if now >= deadline:
            return _PassiveMonitorOutcome(
                "timeout", progress.markers, tuple(issues), tuple(failures), None, None
            )
        time.sleep(min(0.1, deadline - now))
```

- [ ] **Step 4: Run monitor GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'monitor or marker or trace or premature_exit or fallback_or_preloader or completion_marker_without'
```

Expected: progression, exact prompts, record-code authentication, marker-only absence, fallback/preloader failure, both premature-exit boundaries, and one global 300-second deadline all pass. A `[None, 19]` poll sequence can never produce `state="complete"`.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the monitor gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: monitor one passive oracle capture"
```

### Task 12A: Parse macOS process identity rows, including launchd

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces frozen `ProcessRow(pid, ppid, pgid, uid, start_time, executable, argv)` and `_ProcessIdentity(pid, start_time)`.
- Produces `_parse_ps_rows(payload)` for exact C-locale `lstart` rows. PID and PGID are positive, PPID and UID are nonnegative; PID 1/PPID 0 is valid.

- [ ] **Step 1: Add runnable native-parser RED tests**

```python
from io import BytesIO
import sys


def _procargs_payload(executable: str, argv: tuple[str, ...]) -> bytes:
    return (
        len(argv).to_bytes(4, byteorder=sys.byteorder, signed=True)
        + os.fsencode(executable)
        + b"\0\0"
        + b"\0".join(os.fsencode(item) for item in argv)
        + b"\0"
    )


def test_parse_ps_rows_accepts_launchd_ppid_zero_and_exact_lstart() -> None:
    assert passive._parse_ps_rows(
        b" 1 0 1 0 Thu Jul 31 12:34:56 2026\n"
        b"11 1 11 501 Thu Jul 31 12:35:00 2026\n"
    ) == (
        (1, 0, 1, 0, "Thu Jul 31 12:34:56 2026"),
        (11, 1, 11, 501, "Thu Jul 31 12:35:00 2026"),
    )
    with pytest.raises(passive.PassiveProbeError, match="process row"):
        passive._parse_ps_rows(b"10 1 10 501 not-an-lstart\n")


@pytest.mark.parametrize(
    "payload",
    (
        b"0 0 1 0 Thu Jul 31 12:34:56 2026\n",
        b"1 0 0 0 Thu Jul 31 12:34:56 2026\n",
        b"1 -1 1 0 Thu Jul 31 12:34:56 2026\n",
        b"1 0 1 -1 Thu Jul 31 12:34:56 2026\n",
    ),
)
def test_parse_ps_rows_rejects_invalid_numeric_domains(payload: bytes) -> None:
    with pytest.raises(passive.PassiveProbeError, match="process row"):
        passive._parse_ps_rows(payload)
```

- [ ] **Step 2: Run native-parser RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'procargs2 or parse_ps_rows'
```

Expected: `ProcessRow` and native parser functions are missing.

- [ ] **Step 3: Implement the exact native declarations and parsers**

Add imports, declarations, and model:

```python
import ctypes
import errno
import re
import subprocess
import sys


@dataclass(frozen=True, slots=True)
class ProcessRow:
    pid: int
    ppid: int
    pgid: int
    uid: int
    start_time: str
    executable: str
    argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ProcessIdentity:
    pid: int
    start_time: str


@dataclass(frozen=True, slots=True)
class _ProcessSnapshot:
    rows: tuple[ProcessRow, ...]
    sampler_pid: int


_LIBSYSTEM = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
_SYSCTL = _LIBSYSTEM.sysctl
_SYSCTL.argtypes = (
    ctypes.POINTER(ctypes.c_int),
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_size_t),
    ctypes.c_void_p,
    ctypes.c_size_t,
)
_SYSCTL.restype = ctypes.c_int
_SYSCTLBYNAME = _LIBSYSTEM.sysctlbyname
_SYSCTLBYNAME.argtypes = (
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_size_t),
    ctypes.c_void_p,
    ctypes.c_size_t,
)
_SYSCTLBYNAME.restype = ctypes.c_int
_CTL_KERN = 1
_KERN_PROCARGS2 = 49
```

Add complete lexical parsers:

```python
_PS_ROW = re.compile(
    r"^\s*([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+"
    r"((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
    r"(?: [1-9]|[12][0-9]|3[01]) [0-2][0-9]:[0-5][0-9]:[0-6][0-9] [0-9]{4})$"
)


def _parse_ps_rows(payload: bytes) -> tuple[tuple[int, int, int, int, str], ...]:
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError as error:
        raise PassiveProbeError("process rows are not ASCII") from error
    rows: list[tuple[int, int, int, int, str]] = []
    for line in text.splitlines():
        match = _PS_ROW.fullmatch(line)
        if match is None:
            raise PassiveProbeError(f"malformed process row: {line!r}")
        pid, ppid, pgid, uid = (int(match.group(index)) for index in range(1, 5))
        if pid <= 0 or ppid < 0 or pgid <= 0 or uid < 0:
            raise PassiveProbeError(f"invalid process row: {line!r}")
        rows.append((pid, ppid, pgid, uid, match.group(5)))
    return tuple(rows)
```


- [ ] **Step 4: Run the process-row GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'parse_ps_rows or launchd_ppid_zero'
```

Expected: launchd parses as `(pid=1, ppid=0, pgid=1)`; invalid PID/PGID zero and negative PPID/UID fail.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit stable process identities**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: parse stable macOS process identities"
```

### Task 12B: Parse exact same-UID `KERN_PROCARGS2` payloads

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_parse_kern_procargs2(payload)`, `_kern_argmax()`, and `_argv_for_pid(pid, maximum)` with the exact Darwin ABI and bounds.

- [ ] **Step 1: Add argv lexical/ABI RED tests**

```python
import ctypes
import errno


def test_argv_for_pid_uses_exact_kern_procargs2_mib_and_decodes_all_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executable = "/Applications/Stephen's Sausage Roll/Sausage"
    argv = (
        executable,
        "--game-root",
        "/Applications/Stephen's Sausage Roll",
        'literal"quote',
    )
    payload = _procargs_payload(executable, argv)
    calls: list[tuple[tuple[int, ...], int, int]] = []

    def sysctl(mib, mib_length, oldp, oldlenp, newp, newlen) -> int:
        assert newp is None and newlen == 0
        calls.append(
            (
                tuple(mib[index] for index in range(mib_length)),
                mib_length,
                ctypes.cast(oldlenp, ctypes.POINTER(ctypes.c_size_t))[0],
            )
        )
        ctypes.memmove(oldp, payload, len(payload))
        ctypes.cast(oldlenp, ctypes.POINTER(ctypes.c_size_t))[0] = len(payload)
        return 0

    monkeypatch.setattr(passive, "_SYSCTL", sysctl)
    assert passive._argv_for_pid(421, 4096) == (executable, argv)
    assert calls == [
        ((passive._CTL_KERN, passive._KERN_PROCARGS2, 421), 3, 4096)
    ]


@pytest.mark.parametrize(
    ("case", "payload"),
    (
        (
            "argc_zero",
            (0).to_bytes(4, byteorder=sys.byteorder, signed=True)
            + b"/bin/x\0\0",
        ),
        (
            "argc_4097",
            (4097).to_bytes(4, byteorder=sys.byteorder, signed=True)
            + b"/bin/x\0\0",
        ),
        (
            "empty_executable",
            (1).to_bytes(4, byteorder=sys.byteorder, signed=True)
            + b"\0\0x\0",
        ),
        (
            "empty_argv",
            (1).to_bytes(4, byteorder=sys.byteorder, signed=True)
            + b"/bin/x\0\0\0",
        ),
        (
            "trailing_bytes",
            _procargs_payload("/bin/x", ("/bin/x",)) + b"trailing",
        ),
        (
            "invalid_filesystem_text",
            (1).to_bytes(4, byteorder=sys.byteorder, signed=True)
            + b"/bin/x\0\0\xff\0",
        ),
    ),
)
def test_procargs2_rejects_every_lexical_or_bound_violation(
    case: str,
    payload: bytes,
) -> None:
    del case
    with pytest.raises(
        passive.PassiveProbeError,
        match="KERN_PROCARGS2|process text|filesystem",
    ):
        passive._parse_kern_procargs2(payload)


@pytest.mark.parametrize("value", (0, 1024 * 1024, 1024 * 1024 + 1))
def test_kern_argmax_accepts_only_the_inclusive_safe_range(
    monkeypatch: pytest.MonkeyPatch,
    value: int,
) -> None:
    def sysctlbyname(name, oldp, oldlenp, newp, newlen) -> int:
        assert name == b"kern.argmax"
        assert newp is None and newlen == 0
        ctypes.cast(oldp, ctypes.POINTER(ctypes.c_int))[0] = value
        ctypes.cast(oldlenp, ctypes.POINTER(ctypes.c_size_t))[0] = ctypes.sizeof(
            ctypes.c_int
        )
        return 0

    monkeypatch.setattr(passive, "_SYSCTLBYNAME", sysctlbyname)
    if value == 1024 * 1024:
        assert passive._kern_argmax() == value
    else:
        with pytest.raises(passive.PassiveProbeError, match="unsafe kern.argmax"):
            passive._kern_argmax()


@pytest.mark.parametrize("error_number", (errno.ESRCH, errno.EACCES))
def test_argv_for_pid_distinguishes_esrch_from_other_sysctl_failure(
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
) -> None:
    def sysctl(*_args) -> int:
        ctypes.set_errno(error_number)
        return -1

    monkeypatch.setattr(passive, "_SYSCTL", sysctl)
    if error_number == errno.ESRCH:
        with pytest.raises(ProcessLookupError) as caught:
            passive._argv_for_pid(7331, 4096)
        assert caught.value.args == (7331,)
    else:
        with pytest.raises(
            passive.PassiveProbeError,
            match="KERN_PROCARGS2 failed for pid 7331",
        ):
            passive._argv_for_pid(7331, 4096)
```

- [ ] **Step 2: Run the argv RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'procargs2 or kern_argmax or argv_for_pid'
```

Expected: exact ABI helpers are missing.

- [ ] **Step 3: Implement the exact process-argument decoder**

```python
def _decode_process_text(payload: bytes, label: str) -> str:
    try:
        text = os.fsdecode(payload)
    except UnicodeError as error:
        raise PassiveProbeError(f"invalid filesystem encoding in {label}") from error
    if any(0xDC80 <= ord(character) <= 0xDCFF for character in text):
        raise PassiveProbeError(f"surrogateescaped process text in {label}")
    return text


def _parse_kern_procargs2(payload: bytes) -> tuple[str, tuple[str, ...]]:
    integer_size = ctypes.sizeof(ctypes.c_int)
    if len(payload) < integer_size:
        raise PassiveProbeError("malformed KERN_PROCARGS2 argc")
    argc = int.from_bytes(payload[:integer_size], byteorder=sys.byteorder, signed=True)
    if argc <= 0 or argc > 4096:
        raise PassiveProbeError("malformed KERN_PROCARGS2 argc")
    cursor = integer_size
    executable_end = payload.find(b"\0", cursor)
    if executable_end <= cursor:
        raise PassiveProbeError("malformed KERN_PROCARGS2 executable")
    executable = _decode_process_text(payload[cursor:executable_end], "executable")
    cursor = executable_end
    while cursor < len(payload) and payload[cursor] == 0:
        cursor += 1
    argv: list[str] = []
    for index in range(argc):
        end = payload.find(b"\0", cursor)
        if end <= cursor:
            raise PassiveProbeError("malformed KERN_PROCARGS2 argv")
        argv.append(_decode_process_text(payload[cursor:end], f"argv[{index}]"))
        cursor = end + 1
    if any(payload[cursor:]):
        raise PassiveProbeError("malformed KERN_PROCARGS2 trailing bytes")
    return executable, tuple(argv)
```

Add bounded native acquisition:

```python
def _kern_argmax() -> int:
    value = ctypes.c_int()
    size = ctypes.c_size_t(ctypes.sizeof(value))
    if _SYSCTLBYNAME(b"kern.argmax", ctypes.byref(value), ctypes.byref(size), None, 0) != 0:
        error_number = ctypes.get_errno()
        raise PassiveProbeError(f"kern.argmax failed: {os.strerror(error_number)}")
    if size.value != ctypes.sizeof(value) or not 1 <= value.value <= 1024 * 1024:
        raise PassiveProbeError(f"unsafe kern.argmax value: {value.value}")
    return value.value


def _argv_for_pid(pid: int, maximum: int) -> tuple[str, tuple[str, ...]]:
    mib = (ctypes.c_int * 3)(_CTL_KERN, _KERN_PROCARGS2, pid)
    buffer = ctypes.create_string_buffer(maximum)
    size = ctypes.c_size_t(maximum)
    if _SYSCTL(mib, 3, buffer, ctypes.byref(size), None, 0) != 0:
        error_number = ctypes.get_errno()
        if error_number == errno.ESRCH:
            raise ProcessLookupError(pid)
        raise PassiveProbeError(
            f"KERN_PROCARGS2 failed for pid {pid}: {os.strerror(error_number)}"
        )
    return _parse_kern_procargs2(buffer.raw[: size.value])
```


- [ ] **Step 4: Run the argv GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'procargs2 or kern_argmax or argv_for_pid'
```

Expected: every lexical, range, `ESRCH`, and syscall-diagnostic row passes.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit exact process argv acquisition**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: read exact macOS process argv"
```

### Task 12C: Acquire a bounded process snapshot

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_ProcessSnapshot(rows, sampler_pid)` from `_process_snapshot()`.
- Bounds stdout at 8 MiB plus one overflow byte and stderr at 64 KiB plus one; sets `LC_ALL=C`; retrieves argv only for the controller UID; omits `ESRCH` rows and fails every other acquisition error.

- [ ] **Step 1: Add bounded concurrent-snapshot RED tests**

Keep the ten base rows below, add eight concurrency/identity/deadline rows, and add the eight-row owner-finalizer matrix, for twenty-six registrations total. The eight rows cover simultaneous partial/interleaved 8 MiB stdout and 64 KiB stderr production, stdout overflow while stderr fills, timeout, kill failure, parser plus selector/pipe cleanup failures, PID reuse between the first `ps` row, `KERN_PROCARGS2`, and the second identity sample, a fully consumed operational deadline whose bounded cleanup grace also expires before the mandatory no-timeout reap, and operational-clock failure immediately after `Popen`. The eight-row matrix independently covers selector construction, registration, poll, kill, cleanup wait, selector-plus-both-close, stdout-close, and stderr-close faults. The fake uses actual `os.pipe()` descriptors, accepts a bounded float or the final `None` reap, and gives every successful `_process_snapshot()` invocation two independent sampler instances because the first sampler is closed and reaped before the second identity sample begins. Every exceptional owner row asserts that the sampler has a non-`None` poll result before the original primary escapes.

```python
import threading


class SnapshotPipe:
    def __init__(
        self,
        payload: bytes,
        *,
        hold_open: bool = False,
        close_error: BaseException | None = None,
    ) -> None:
        self._read_fd, self._write_fd = os.pipe()
        self._payload = payload
        self._hold_open = hold_open
        self._close_error = close_error
        self._release = threading.Event()
        self._writer_done = threading.Event()
        self._writer_lock = threading.Lock()
        self.close_calls = 0
        self._writer = threading.Thread(target=self._write, daemon=True)
        self._writer.start()

    def _close_writer(self) -> None:
        with self._writer_lock:
            descriptor = self._write_fd
            self._write_fd = -1
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass

    def _write(self) -> None:
        view = memoryview(self._payload)
        try:
            while view:
                written = os.write(self._write_fd, view[:4096])
                view = view[written:]
            if self._hold_open:
                self._release.wait()
        except OSError:
            pass
        finally:
            self._close_writer()
            self._writer_done.set()

    def fileno(self) -> int:
        return self._read_fd

    def terminate_writer(self) -> None:
        self._release.set()
        self._close_writer()

    def wait_writer(self, timeout: float | None) -> bool:
        return self._writer_done.wait(timeout)

    def close(self) -> None:
        self.close_calls += 1
        descriptor = self._read_fd
        self._read_fd = -1
        if descriptor >= 0:
            os.close(descriptor)
        if self._close_error is not None:
            raise self._close_error


@dataclass
class SnapshotPsProcess:
    stdout_payload: bytes
    stderr_payload: bytes = b""
    pid: int = 7001
    exit_code: int = 0
    missing_pipe: str | None = None
    hold_open: bool = False
    kill_error: BaseException | None = None
    poll_error: BaseException | None = None
    wait_errors: list[BaseException] = field(default_factory=list)
    bounded_wait_times_out: bool = False
    stdout_close_error: BaseException | None = None
    stderr_close_error: BaseException | None = None
    killed: bool = False
    kill_calls: int = 0
    wait_calls: int = 0
    wait_timeouts: list[float | None] = field(default_factory=list)
    returncode: int | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.stdout = (
            None
            if self.missing_pipe == "stdout"
            else SnapshotPipe(
                self.stdout_payload,
                hold_open=self.hold_open,
                close_error=self.stdout_close_error,
            )
        )
        self.stderr = (
            None
            if self.missing_pipe == "stderr"
            else SnapshotPipe(
                self.stderr_payload,
                hold_open=self.hold_open,
                close_error=self.stderr_close_error,
            )
        )

    def kill(self) -> None:
        self.kill_calls += 1
        self.killed = True
        for stream in (self.stdout, self.stderr):
            if stream is not None:
                stream.terminate_writer()
        if self.kill_error is not None:
            raise self.kill_error

    def wait(self, timeout: float | None = None) -> int:
        assert timeout is None or 0.0 <= timeout <= 10.0
        self.wait_calls += 1
        self.wait_timeouts.append(timeout)
        if self.wait_errors:
            raise self.wait_errors.pop(0)
        if self.bounded_wait_times_out and timeout is not None:
            raise subprocess.TimeoutExpired("/bin/ps", timeout)
        deadline = None if timeout is None else time.monotonic() + timeout
        for stream in (self.stdout, self.stderr):
            if stream is not None and not stream.wait_writer(
                None if deadline is None else max(0.0, deadline - time.monotonic())
            ):
                raise subprocess.TimeoutExpired("/bin/ps", timeout)
        self.returncode = -9 if self.killed else self.exit_code
        return self.returncode

    def poll(self) -> int | None:
        if self.poll_error is not None:
            error = self.poll_error
            self.poll_error = None
            raise error
        return self.returncode


class DelegatingSnapshotSelector:
    def __init__(
        self,
        *,
        force_timeout: bool = False,
        close_error: BaseException | None = None,
        register_error: BaseException | None = None,
    ) -> None:
        self._inner = selectors.DefaultSelector()
        self._force_timeout = force_timeout
        self._close_error = close_error
        self._register_error = register_error
        self.select_timeouts: list[float] = []
        self.close_calls = 0

    def register(self, *args, **kwargs):
        if self._register_error is not None:
            error = self._register_error
            self._register_error = None
            raise error
        return self._inner.register(*args, **kwargs)

    def unregister(self, *args, **kwargs):
        return self._inner.unregister(*args, **kwargs)

    def get_map(self):
        return self._inner.get_map()

    def select(self, timeout: float):
        self.select_timeouts.append(timeout)
        if self._force_timeout:
            return []
        return self._inner.select(timeout)

    def close(self) -> None:
        self.close_calls += 1
        self._inner.close()
        if self._close_error is not None:
            raise self._close_error


class SnapshotClock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now


class DeadlineConsumingSnapshotSelector(DelegatingSnapshotSelector):
    def __init__(self, clock: SnapshotClock) -> None:
        super().__init__()
        self._clock = clock

    def select(self, timeout: float):
        self.select_timeouts.append(timeout)
        self._clock.now += timeout
        return []


def _install_snapshot_processes(
    monkeypatch: pytest.MonkeyPatch,
    *specifications: dict[str, object],
) -> tuple[list[SnapshotPsProcess], list[tuple[tuple[str, ...], dict[str, object]]]]:
    created: list[SnapshotPsProcess] = []
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def popen(argv, **kwargs):
        calls.append((argv, kwargs))
        process = SnapshotPsProcess(**specifications[len(created)])
        created.append(process)
        return process

    monkeypatch.setattr(passive.subprocess, "Popen", popen)
    return created, calls


def _one_ps_row(pid: int, uid: int) -> bytes:
    return (
        f"{pid} 1 {pid} {uid} Thu Jul 31 12:35:00 2026\n"
    ).encode("ascii")


def _ps_row_with_start(pid: int, uid: int, start: str) -> bytes:
    return f"{pid} 1 {pid} {uid} {start}\n".encode("ascii")


def test_process_snapshot_uses_exact_ps_invocation_and_same_uid_argv_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own_uid = os.getuid()
    payload = _one_ps_row(41, own_uid) + _one_ps_row(42, own_uid + 1)
    created, popen_calls = _install_snapshot_processes(
        monkeypatch,
        {"stdout_payload": payload, "pid": 7001},
        {"stdout_payload": payload, "pid": 7002},
    )
    argv_calls: list[tuple[int, int]] = []

    def argv_for_pid(pid: int, maximum: int):
        argv_calls.append((pid, maximum))
        return f"/proc/{pid}", (f"/proc/{pid}", "--flag")

    monkeypatch.setattr(passive, "_kern_argmax", lambda: 4096)
    monkeypatch.setattr(passive, "_argv_for_pid", argv_for_pid)
    snapshot = passive._process_snapshot()
    expected_call = (
        (
            "/bin/ps",
            "-ww",
            "-axo",
            "pid=,ppid=,pgid=,uid=,lstart=",
        ),
        {
            "stdout": passive.subprocess.PIPE,
            "stderr": passive.subprocess.PIPE,
            "env": {**os.environ, "LC_ALL": "C"},
            "shell": False,
        },
    )
    assert popen_calls == [expected_call, expected_call]
    assert snapshot.sampler_pid == 7001
    assert len(created) == 2
    assert all(process.wait_calls == 1 for process in created)
    assert all(process.kill_calls == 0 for process in created)
    assert all(process.stdout.close_calls == 1 for process in created)
    assert all(process.stderr.close_calls == 1 for process in created)
    assert argv_calls == [(41, 4096)]
    assert snapshot.rows[0].executable == "/proc/41"
    assert snapshot.rows[0].argv == ("/proc/41", "--flag")
    assert snapshot.rows[1].executable == ""
    assert snapshot.rows[1].argv == ()


@pytest.mark.parametrize("overflow", (False, True))
def test_process_snapshot_stdout_bound_is_inclusive(
    monkeypatch: pytest.MonkeyPatch,
    overflow: bool,
) -> None:
    limit = 8 * 1024 * 1024
    row = _one_ps_row(43, os.getuid() + 1)
    payload = b" " * (limit - len(row)) + row + (
        b"x" if overflow else b""
    )
    specifications = [{"stdout_payload": payload}]
    if not overflow:
        specifications.append({"stdout_payload": payload, "pid": 7002})
    created, _calls = _install_snapshot_processes(
        monkeypatch,
        *specifications,
    )
    monkeypatch.setattr(passive, "_kern_argmax", lambda: 4096)
    if overflow:
        with pytest.raises(passive.PassiveProbeError, match="exceeds 8 MiB"):
            passive._process_snapshot()
        assert created[0].killed is True and created[0].wait_calls == 1
    else:
        snapshot = passive._process_snapshot()
        assert tuple(row.pid for row in snapshot.rows) == (43,)
        assert len(created) == 2
        assert all(process.killed is False for process in created)


@pytest.mark.parametrize("overflow", (False, True))
def test_process_snapshot_stderr_bound_is_inclusive(
    monkeypatch: pytest.MonkeyPatch,
    overflow: bool,
) -> None:
    limit = 64 * 1024
    specification = {
        "stdout_payload": _one_ps_row(44, os.getuid() + 1),
        "stderr_payload": b"e" * (limit + int(overflow)),
    }
    specifications = [specification]
    if not overflow:
        specifications.append({**specification, "pid": 7002})
    created, _calls = _install_snapshot_processes(
        monkeypatch,
        *specifications,
    )
    monkeypatch.setattr(passive, "_kern_argmax", lambda: 4096)
    if overflow:
        with pytest.raises(
            passive.PassiveProbeError,
            match="stderr exceeds 64 KiB",
        ):
            passive._process_snapshot()
        assert created[0].killed is True and created[0].wait_calls == 1
    else:
        assert tuple(
            row.pid for row in passive._process_snapshot().rows
        ) == (44,)


def test_process_snapshot_rejects_either_missing_pipe_and_reaps_sampler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[SnapshotPsProcess] = []
    for missing in ("stdout", "stderr"):
        process = SnapshotPsProcess(b"", missing_pipe=missing, hold_open=True)
        created.append(process)
        monkeypatch.setattr(
            passive.subprocess,
            "Popen",
            lambda *_args, process=process, **_kwargs: process,
        )
        with pytest.raises(
            passive.PassiveProbeError,
            match="pipes are unavailable",
        ):
            passive._sample_ps_rows()
    assert all(
        process.killed and process.wait_calls == 1 and process.kill_calls == 1
        for process in created
    )
    assert created[0].stderr.close_calls == 1
    assert created[1].stdout.close_calls == 1


@pytest.mark.parametrize("failure", ("nonzero_exit", "wait_failure"))
def test_process_snapshot_rejects_nonzero_exit_or_wait_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    primary = passive.subprocess.TimeoutExpired("/bin/ps", 10)
    process = SnapshotPsProcess(
        _one_ps_row(45, os.getuid() + 1),
        b"ps failed" if failure == "nonzero_exit" else b"",
        exit_code=2 if failure == "nonzero_exit" else 0,
        wait_errors=[primary] if failure == "wait_failure" else [],
    )
    monkeypatch.setattr(
        passive.subprocess,
        "Popen",
        lambda *_args, **_kwargs: process,
    )
    monkeypatch.setattr(passive, "_kern_argmax", lambda: 4096)
    if failure == "nonzero_exit":
        with pytest.raises(
            passive.PassiveProbeError,
            match="process inventory failed: ps failed",
        ):
            passive._sample_ps_rows()
    else:
        with pytest.raises(passive.subprocess.TimeoutExpired) as caught:
            passive._sample_ps_rows()
        assert caught.value is primary
        assert process.kill_calls == 1 and process.wait_calls == 2
    assert process.stdout.close_calls == 1
    assert process.stderr.close_calls == 1


@pytest.mark.parametrize("error_kind", ("esrch", "other"))
def test_process_snapshot_omits_esrch_but_propagates_other_argv_error(
    monkeypatch: pytest.MonkeyPatch,
    error_kind: str,
) -> None:
    payload = _one_ps_row(46, os.getuid())
    created, _calls = _install_snapshot_processes(
        monkeypatch,
        {"stdout_payload": payload},
        {"stdout_payload": payload, "pid": 7002},
    )
    primary = passive.PassiveProbeError("argv permission failure")

    def argv_for_pid(pid: int, maximum: int):
        assert (pid, maximum) == (46, 4096)
        if error_kind == "esrch":
            raise ProcessLookupError(pid)
        raise primary

    monkeypatch.setattr(passive, "_kern_argmax", lambda: 4096)
    monkeypatch.setattr(passive, "_argv_for_pid", argv_for_pid)
    if error_kind == "esrch":
        assert passive._process_snapshot().rows == ()
    else:
        with pytest.raises(passive.PassiveProbeError) as caught:
            passive._process_snapshot()
        assert caught.value is primary
    assert all(process.wait_calls == 1 for process in created)


def test_process_snapshot_drains_simultaneous_exact_bounds_without_deadlock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout_limit = 8 * 1024 * 1024
    stderr_limit = 64 * 1024
    row = _one_ps_row(47, os.getuid() + 1)
    process = SnapshotPsProcess(
        b" " * (stdout_limit - len(row)) + row,
        b"e" * stderr_limit,
    )
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    rows, sampler_pid = passive._sample_ps_rows()
    assert tuple(row[0] for row in rows) == (47,)
    assert sampler_pid == process.pid
    assert process.wait_calls == 1 and not process.killed


def test_process_snapshot_stdout_overflow_while_stderr_fills_kills_and_reaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = SnapshotPsProcess(
        b"x" * (8 * 1024 * 1024 + 1),
        b"e" * (64 * 1024),
    )
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    with pytest.raises(passive.PassiveProbeError, match="exceeds 8 MiB"):
        passive._sample_ps_rows()
    assert process.kill_calls == 1 and process.wait_calls == 1
    assert process.stdout.close_calls == process.stderr.close_calls == 1


def test_process_snapshot_timeout_uses_remaining_deadline_and_reaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = SnapshotPsProcess(b"", hold_open=True)
    selector = DelegatingSnapshotSelector(force_timeout=True)
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(passive.selectors, "DefaultSelector", lambda: selector)
    with pytest.raises(passive.subprocess.TimeoutExpired):
        passive._sample_ps_rows()
    assert selector.select_timeouts and 0.0 < selector.select_timeouts[0] <= 10.0
    assert process.wait_timeouts and 0.0 <= process.wait_timeouts[-1] <= 10.0
    assert process.kill_calls == 1 and process.wait_calls == 1
    assert process.poll() == -9


def test_process_snapshot_expired_read_and_cleanup_deadlines_use_final_reap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = SnapshotClock()
    process = SnapshotPsProcess(
        b"",
        hold_open=True,
        bounded_wait_times_out=True,
    )
    selector = DeadlineConsumingSnapshotSelector(clock)
    monkeypatch.setattr(passive.time, "monotonic", clock.monotonic)
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(passive.selectors, "DefaultSelector", lambda: selector)
    with pytest.raises(passive.subprocess.TimeoutExpired) as caught:
        passive._sample_ps_rows()
    assert caught.value.cmd == "/bin/ps" and caught.value.timeout == 10
    assert selector.select_timeouts == [10.0]
    assert process.wait_timeouts == [10.0, None]
    assert process.kill_calls == 2
    assert process.returncode == -9 and process.poll() == -9
    assert process.stdout.close_calls == process.stderr.close_calls == 1
    assert any(
        "secondary ps bounded reap failure" in note
        for note in caught.value.__notes__
    )


def test_process_snapshot_clock_failure_after_popen_still_guarantees_reap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary = KeyboardInterrupt("operational deadline clock failed")
    process = SnapshotPsProcess(
        b"",
        hold_open=True,
        bounded_wait_times_out=True,
    )
    clock_calls = 0

    def monotonic() -> float:
        nonlocal clock_calls
        clock_calls += 1
        if clock_calls == 1:
            raise primary
        return 0.0

    monkeypatch.setattr(passive.time, "monotonic", monotonic)
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    with pytest.raises(KeyboardInterrupt) as caught:
        passive._sample_ps_rows()
    assert caught.value is primary
    assert process.wait_timeouts == [10.0, None]
    assert process.kill_calls == 2
    assert process.returncode == -9 and process.poll() == -9
    assert process.stdout.close_calls == process.stderr.close_calls == 1


def test_process_snapshot_kill_failure_still_reaps_and_closes_both_pipes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    kill_error = OSError("kill failed")
    process = SnapshotPsProcess(b"", hold_open=True, kill_error=kill_error)
    selector = DelegatingSnapshotSelector(force_timeout=True)
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(passive.selectors, "DefaultSelector", lambda: selector)
    with pytest.raises(passive.subprocess.TimeoutExpired) as caught:
        passive._sample_ps_rows()
    assert any("secondary ps kill failure" in note for note in caught.value.__notes__)
    assert process.kill_calls == 1 and process.wait_calls == 1
    assert process.stdout.close_calls == process.stderr.close_calls == 1


def test_process_snapshot_parser_primary_survives_selector_and_pipe_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primary = KeyboardInterrupt("parser interrupted")
    selector_error = OSError("selector close failed")
    process = SnapshotPsProcess(
        _one_ps_row(48, os.getuid() + 1),
        stdout_close_error=OSError("stdout close failed"),
        stderr_close_error=OSError("stderr close failed"),
    )
    selector = DelegatingSnapshotSelector(close_error=selector_error)
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    monkeypatch.setattr(passive.selectors, "DefaultSelector", lambda: selector)
    monkeypatch.setattr(passive, "_parse_ps_rows", lambda _payload: (_ for _ in ()).throw(primary))
    with pytest.raises(KeyboardInterrupt) as caught:
        passive._sample_ps_rows()
    assert caught.value is primary
    assert sum("secondary ps" in note for note in primary.__notes__) == 3
    assert selector.close_calls == 1
    assert process.stdout.close_calls == process.stderr.close_calls == 1


@pytest.mark.parametrize(
    "fault",
    (
        "selector_create",
        "selector_register",
        "poll",
        "kill",
        "cleanup_wait",
        "selector_and_both_closes",
        "stdout_close",
        "stderr_close",
    ),
)
def test_process_snapshot_owner_finalizer_attempts_every_remaining_owner(
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    injected = OSError(f"{fault} failed")
    timeout_fault = fault in {"poll", "kill", "cleanup_wait"}
    process = SnapshotPsProcess(
        b"" if timeout_fault or fault.startswith("selector_") else _one_ps_row(50, os.getuid() + 1),
        hold_open=timeout_fault or fault in {"selector_create", "selector_register"},
        poll_error=(injected if fault == "poll" else None),
        kill_error=(injected if fault == "kill" else None),
        wait_errors=([injected] if fault == "cleanup_wait" else []),
        stdout_close_error=(
            injected
            if fault in {"selector_and_both_closes", "stdout_close"}
            else None
        ),
        stderr_close_error=(
            OSError("stderr close failed")
            if fault == "selector_and_both_closes"
            else injected if fault == "stderr_close" else None
        ),
    )
    selector = DelegatingSnapshotSelector(
        force_timeout=timeout_fault,
        register_error=(injected if fault == "selector_register" else None),
        close_error=(injected if fault == "selector_and_both_closes" else None),
    )
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_a, **_k: process)
    if fault == "selector_create":
        monkeypatch.setattr(
            passive.selectors,
            "DefaultSelector",
            lambda: (_ for _ in ()).throw(injected),
        )
    else:
        monkeypatch.setattr(passive.selectors, "DefaultSelector", lambda: selector)

    with pytest.raises(BaseException) as caught:
        passive._sample_ps_rows()
    if fault in {"selector_create", "selector_register", "selector_and_both_closes", "stdout_close", "stderr_close"}:
        assert caught.value is injected
    else:
        assert isinstance(caught.value, passive.subprocess.TimeoutExpired)
        label = {
            "poll": "poll",
            "kill": "kill",
            "cleanup_wait": "bounded reap",
        }[fault]
        assert any(f"secondary ps {label}" in note for note in caught.value.__notes__)
    assert process.stdout.close_calls == 1
    assert process.stderr.close_calls == 1
    if fault != "selector_create":
        assert selector.close_calls == 1
    if fault == "selector_and_both_closes":
        assert len(caught.value.__notes__) == 2
    if fault == "cleanup_wait":
        assert process.wait_calls == 2
        assert process.poll() == -9
    assert process.poll() is not None


def test_process_snapshot_pid_reuse_after_argv_omits_reused_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own_uid = os.getuid()
    first = _ps_row_with_start(49, own_uid, "Thu Jul 31 12:35:00 2026")
    reused = _ps_row_with_start(49, own_uid, "Thu Jul 31 12:36:00 2026")
    created, _calls = _install_snapshot_processes(
        monkeypatch,
        {"stdout_payload": first, "pid": 7101},
        {"stdout_payload": reused, "pid": 7102},
    )
    argv_calls: list[int] = []
    monkeypatch.setattr(passive, "_kern_argmax", lambda: 4096)
    monkeypatch.setattr(
        passive,
        "_argv_for_pid",
        lambda pid, _maximum: (argv_calls.append(pid), ("/proc/49", ("/proc/49",)))[1],
    )
    snapshot = passive._process_snapshot()
    assert argv_calls == [49]
    assert snapshot.rows == ()
    assert snapshot.sampler_pid == 7101
    assert all(process.wait_calls == 1 for process in created)
```

- [ ] **Step 2: Run the bounded-snapshot RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'process_snapshot'
```

Expected: the exact `lstart` invocation or one bound/ownership case is absent; all twenty-six Task-12C registrations, including the bounded-grace/final-reap and post-`Popen` clock rows, are selected.

- [ ] **Step 3: Implement complete bounded concurrent snapshot acquisition**

Replace sequential `.read()` calls with a `selectors.DefaultSelector` loop over both real pipe fds. Each readiness callback reads at most 64 KiB and never lets the stdout/stderr bytearrays exceed `8 * 1024 * 1024 + 1` and `64 * 1024 + 1`. Acquire the monotonic ten-second operational deadline inside the post-`Popen` owner transaction. In one `BaseException` owner-finalizer, kill an unreaped sampler, grant it a fresh bounded ten-second grace wait independent of the exhausted read deadline, and, if that bounded wait fails or expires, perform a final no-timeout `wait()` until the child is reaped before any return or raise. Close both pipes attempt-all, preserve the first primary, and attach later clock/kill/wait/close failures. The final no-timeout reap is the standard post-kill ownership guarantee: exceptional cleanup may block rather than return a live child, and no control path may return or raise while `process.poll()` is `None`.

Factor the bounded `ps` invocation into `_sample_ps_rows()`. `_process_snapshot()` calls it once for lexical rows, acquires same-UID argv, calls it a second time, and retains a row only when `(pid, lstart)` is still identical in the second sample. Missing/reused rows are omitted; all other argv/syscall errors remain terminal. The complete implementation must contain no direct `process.stdout.read` or `process.stderr.read`.

```python
import selectors


def _sample_ps_rows() -> tuple[tuple[tuple[int, int, int, int, str], ...], int]:
    process = subprocess.Popen(
        ("/bin/ps", "-ww", "-axo", "pid=,ppid=,pgid=,uid=,lstart="),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "LC_ALL": "C"}, shell=False,
    )
    deadline: float | None = None
    stdout = None
    stderr = None
    selector: selectors.BaseSelector | None = None
    streams: dict[object, tuple[int, str, str]] = {}
    payloads: dict[object, bytearray] = {}
    result: tuple[tuple[tuple[int, int, int, int, str], ...], int] | None = None
    primary: BaseException | None = None
    reaped = False

    def retain_cleanup_error(stage: str, error: BaseException) -> None:
        nonlocal primary
        if primary is None:
            primary = error
            return
        try:
            primary.add_note(
                f"secondary ps {stage} failure: {type(error).__name__}: {error}"
            )
        except BaseException:
            pass

    try:
        # Ownership begins immediately after Popen: even missing attributes,
        # selector construction, or registration failure reaches one finalizer.
        stdout = process.stdout
        stderr = process.stderr
        if stdout is None or stderr is None:
            raise PassiveProbeError("process inventory pipes are unavailable")
        deadline = time.monotonic() + 10.0
        streams = {
            stdout: (8 * 1024 * 1024, "8 MiB", "stdout"),
            stderr: (64 * 1024, "64 KiB", "stderr"),
        }
        payloads = {stream: bytearray() for stream in streams}
        selector = selectors.DefaultSelector()
        for stream in streams:
            selector.register(stream, selectors.EVENT_READ)
        while selector.get_map():
            assert deadline is not None
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired("/bin/ps", 10)
            ready = selector.select(remaining)
            if not ready:
                raise subprocess.TimeoutExpired("/bin/ps", 10)
            for key, _mask in ready:
                stream = key.fileobj
                limit, label, stream_label = streams[stream]
                chunk = os.read(stream.fileno(), min(64 * 1024, limit + 1 - len(payloads[stream])))
                if not chunk:
                    selector.unregister(stream)
                    continue
                payloads[stream].extend(chunk)
                if len(payloads[stream]) > limit:
                    raise PassiveProbeError(
                        f"process inventory {stream_label} exceeds {label}"
                    )
        returncode = process.wait(
            timeout=max(0.0, deadline - time.monotonic())
        )
        reaped = True
        stderr_payload = bytes(payloads[stderr])
        if returncode != 0:
            raise PassiveProbeError(
                "process inventory failed: "
                f"{stderr_payload.decode('utf-8', 'replace')}"
            )
        result = (_parse_ps_rows(bytes(payloads[stdout])), process.pid)
    except BaseException as error:
        primary = error
    finally:
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                retain_cleanup_error("selector close", error)
        if not reaped:
            alive = True
            try:
                alive = process.poll() is None
            except BaseException as error:
                retain_cleanup_error("poll", error)
            if alive:
                try:
                    process.kill()
                except BaseException as error:
                    retain_cleanup_error("kill", error)
            try:
                cleanup_deadline = time.monotonic() + 10.0
                process.wait(timeout=max(0.0, cleanup_deadline - time.monotonic()))
                reaped = True
            except BaseException as error:
                retain_cleanup_error("bounded reap", error)
                alive_after_wait = True
                try:
                    alive_after_wait = process.poll() is None
                except BaseException as poll_error:
                    retain_cleanup_error("post-reap poll", poll_error)
                if alive_after_wait:
                    try:
                        process.kill()
                    except BaseException as kill_error:
                        retain_cleanup_error("post-reap kill", kill_error)
            while not reaped:
                try:
                    process.wait()
                    reaped = True
                except BaseException as final_wait_error:
                    retain_cleanup_error("final reap", final_wait_error)
                    try:
                        reaped = process.poll() is not None
                    except BaseException as poll_error:
                        retain_cleanup_error("final poll", poll_error)
        for label, stream in (("stdout", stdout), ("stderr", stderr)):
            if stream is None:
                continue
            try:
                stream.close()
            except BaseException as error:
                retain_cleanup_error(f"{label} close", error)
    if primary is not None:
        raise primary
    assert result is not None and reaped and process.poll() is not None
    return result


def _process_snapshot() -> _ProcessSnapshot:
    lexical, sampler_pid = _sample_ps_rows()
    argmax = _kern_argmax()
    own_uid = os.getuid()
    acquired: dict[int, tuple[str, tuple[str, ...]]] = {}
    for pid, _ppid, _pgid, uid, _start in lexical:
        if uid == own_uid:
            try:
                acquired[pid] = _argv_for_pid(pid, argmax)
            except ProcessLookupError:
                pass
    second, _second_sampler = _sample_ps_rows()
    live_identity = {pid: start for pid, _ppid, _pgid, _uid, start in second}
    rows: list[ProcessRow] = []
    for pid, ppid, pgid, uid, start_time in lexical:
        if live_identity.get(pid) != start_time:
            continue
        if uid == own_uid and pid not in acquired:
            continue
        executable, argv = acquired.get(pid, ("", ()))
        rows.append(ProcessRow(pid, ppid, pgid, uid, start_time, executable, argv))
    return _ProcessSnapshot(tuple(rows), sampler_pid)
```

- [ ] **Step 4: Run native-parser GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'procargs2 or parse_ps_rows or process_snapshot'
```

Expected: native lexical tests, concurrent stdout/stderr drain, exact bounds, timeout kill/reap, attempt-all cleanup, same-UID argv retrieval, `ESRCH` omission, permission failure, `kern.argmax` bounds, and `(pid, lstart)` reuse revalidation pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the native inventory reader**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: acquire bounded passive process snapshot"
```

### Task 13A: Match exact probe-related processes

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Consumes `ProcessRow` and `_process_snapshot` from Task 12.
- Produces `_matching_probe_processes(..., observed_identities) -> tuple[ProcessRow, ...]`.
- Produces generic `_require_no_matching_processes(matcher)` with two snapshots, each snapshot's real sampler PID, and one 0.1-second separation.
- Exact matching includes controller/spawned descendants, spawned PGID, launcher/game paths, adjacent second-probe argv tokens, and any identity previously observed by Task 13B.

- [ ] **Step 1: Add exact path/token/parent/PGID/CLI-form RED tests**

In addition to the eight rows below, add four second-probe rows: options reordered around the exact script token; `--game-root=<exact-root>`; a dangling `--game-root`; and two conflicting game-root forms. The first two must match and the last two must not match or raise a deterministic malformed-invocation `PassiveProbeError`; substring script/root values never match.

```python
def _row(
    pid: int,
    ppid: int,
    pgid: int,
    *argv: str,
    executable: str = "",
    start_time: str | None = None,
) -> passive.ProcessRow:
    return passive.ProcessRow(
        pid,
        ppid,
        pgid,
        os.getuid(),
        start_time or f"Thu Jul 31 12:{pid % 60:02d}:00 2026",
        executable,
        tuple(argv),
    )


def test_matching_processes_uses_numeric_and_exact_argv_rules(tmp_path: Path) -> None:
    launcher = tmp_path / "run_bepinex.sh"
    game = tmp_path / "Sausage.app/Contents/MacOS/Sausage"
    script = tmp_path / "tools/oracle_passive_probe.py"
    root = tmp_path / "Stephen's Sausage Roll"
    rows = (
        _row(20, 1, 20, str(launcher), executable=str(launcher)),
        _row(21, 20, 21, "helper"),
        _row(22, 1, 99, str(game), executable=str(game)),
        _row(23, 1, 23, "python", str(script), "--game-root", str(root)),
        _row(24, 1, 24, str(launcher) + ".backup", executable=str(launcher) + ".backup"),
    )
    matches = passive._matching_probe_processes(
        rows,
        controller_pid=10,
        sampler_pid=11,
        spawned_pid=20,
        spawned_pgid=20,
        launcher=launcher,
        game_executable=game,
        probe_script=script,
        game_root=root,
        observed_identities=frozenset(),
    )
    assert tuple(row.pid for row in matches) == (20, 21, 22, 23)


@pytest.mark.parametrize(
    ("form", "expected_error"),
    (
        ("reordered", None),
        ("equals", None),
        ("dangling", "malformed second-probe --game-root"),
        ("conflicting", "conflicting second-probe game roots"),
    ),
)
def test_matching_processes_handles_each_exact_second_probe_cli_form(
    tmp_path: Path,
    form: str,
    expected_error: str | None,
) -> None:
    script = tmp_path / "tools" / "oracle_passive_probe.py"
    root = tmp_path / "Stephen's Sausage Roll"
    argv = {
        "reordered": (
            "python",
            "--verbose",
            str(script),
            "--timeout",
            "300",
            "--game-root",
            str(root),
            "--preflight-only",
        ),
        "equals": ("python", str(script), f"--game-root={root}"),
        "dangling": ("python", str(script), "--game-root"),
        "conflicting": (
            "python",
            str(script),
            "--game-root",
            str(root),
            f"--game-root={tmp_path / 'different-root'}",
        ),
    }[form]
    row = _row(25, 1, 25, *argv)
    if expected_error is not None:
        with pytest.raises(passive.PassiveProbeError, match=expected_error):
            passive._matching_probe_processes(
                (row,),
                controller_pid=10,
                sampler_pid=11,
                spawned_pid=None,
                spawned_pgid=None,
                launcher=tmp_path / "launcher",
                game_executable=tmp_path / "game",
                probe_script=script,
                game_root=root,
                observed_identities=frozenset(),
            )
        return
    assert passive._matching_probe_processes(
        (row,),
        controller_pid=10,
        sampler_pid=11,
        spawned_pid=None,
        spawned_pgid=None,
        launcher=tmp_path / "launcher",
        game_executable=tmp_path / "game",
        probe_script=script,
        game_root=root,
        observed_identities=frozenset(),
    ) == (row,)
    assert passive._contains_probe_invocation(
        tuple(token + ".substring" for token in argv),
        script,
        root,
    ) is False


def test_matching_processes_excludes_only_controller_and_sampler(tmp_path: Path) -> None:
    rows = (_row(10, 1, 10, "controller"), _row(11, 10, 11, "/bin/ps"), _row(12, 10, 12, "child"))
    matches = passive._matching_probe_processes(
        rows,
        controller_pid=10,
        sampler_pid=11,
        spawned_pid=None,
        spawned_pgid=None,
        launcher=tmp_path / "launcher",
        game_executable=tmp_path / "game",
        probe_script=tmp_path / "probe.py",
        game_root=tmp_path / "root",
        observed_identities=frozenset(),
    )
    assert tuple(row.pid for row in matches) == (12,)


@pytest.mark.parametrize(
    ("target", "source"),
    (
        ("launcher", "executable"),
        ("launcher", "argv"),
        ("game", "executable"),
        ("game", "argv"),
    ),
)
def test_matching_processes_matches_each_exact_path_token_source(
    tmp_path: Path,
    target: str,
    source: str,
) -> None:
    launcher = tmp_path / "launcher"
    game = tmp_path / "Sausage"
    selected = launcher if target == "launcher" else game
    executable = str(selected) if source == "executable" else ""
    argv = (str(selected),) if source == "argv" else ("unrelated",)
    row = _row(71, 1, 71, *argv, executable=executable)
    matches = passive._matching_probe_processes(
        (row,),
        controller_pid=10,
        sampler_pid=11,
        spawned_pid=None,
        spawned_pgid=None,
        launcher=launcher,
        game_executable=game,
        probe_script=tmp_path / "probe.py",
        game_root=tmp_path / "root",
        observed_identities=frozenset(),
    )
    assert matches == (row,)


def test_process_absence_uses_each_real_sampler_pid_and_two_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter(
        (
            passive._ProcessSnapshot((), 8101),
            passive._ProcessSnapshot((), 8102),
        )
    )
    observed: list[tuple[tuple[passive.ProcessRow, ...], int]] = []
    sleeps: list[float] = []
    monkeypatch.setattr(passive, "_process_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(passive.time, "sleep", sleeps.append)

    result = passive._require_no_matching_processes(
        lambda rows, sampler_pid: observed.append((rows, sampler_pid)) or ()
    )

    assert result == ()
    assert observed == [((), 8101), ((), 8102)]
    assert sleeps == [0.1]


def test_process_absence_rejects_a_match_in_either_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    survivor = _row(90, 1, 90, "survivor")
    snapshots = iter(
        (
            passive._ProcessSnapshot((), 8201),
            passive._ProcessSnapshot((survivor,), 8202),
        )
    )
    monkeypatch.setattr(passive, "_process_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(passive.time, "sleep", lambda seconds: None)
    with pytest.raises(passive.PassiveProbeError, match="90"):
        passive._require_no_matching_processes(
            lambda rows, _sampler_pid: rows
        )
```

- [ ] **Step 2: Run process-matching RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'matching_processes or process_absence'
```

Expected: `_matching_probe_processes` is missing.

- [ ] **Step 3: Implement exact match and two-snapshot absence rules**

```python
def _parent_reaches(
    row: ProcessRow,
    by_pid: dict[int, ProcessRow],
    targets: frozenset[int],
) -> bool:
    seen: set[int] = set()
    parent = row.ppid
    while parent > 0 and parent not in seen:
        if parent in targets:
            return True
        seen.add(parent)
        ancestor = by_pid.get(parent)
        if ancestor is None:
            return False
        parent = ancestor.ppid
    if parent in seen:
        raise PassiveProbeError(f"process parent loop involving pid {row.pid}")
    return False


def _contains_probe_invocation(
    argv: tuple[str, ...],
    probe_script: Path,
    game_root: Path,
) -> bool:
    if str(probe_script) not in argv:
        return False
    roots: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--game-root":
            if index + 1 >= len(argv):
                raise PassiveProbeError("malformed second-probe --game-root")
            roots.append(argv[index + 1])
            index += 2
            continue
        if token.startswith("--game-root="):
            roots.append(token.removeprefix("--game-root="))
        index += 1
    if len(roots) > 1 and len(set(roots)) != 1:
        raise PassiveProbeError("conflicting second-probe game roots")
    return roots == [str(game_root)] or (
        len(roots) > 1 and set(roots) == {str(game_root)}
    )


def _matching_probe_processes(
    rows: tuple[ProcessRow, ...],
    *,
    controller_pid: int,
    sampler_pid: int,
    spawned_pid: int | None,
    spawned_pgid: int | None,
    launcher: Path,
    game_executable: Path,
    probe_script: Path,
    game_root: Path,
    observed_identities: frozenset[_ProcessIdentity],
) -> tuple[ProcessRow, ...]:
    by_pid = {row.pid: row for row in rows}
    targets = frozenset(
        pid for pid in (controller_pid, spawned_pid) if pid is not None
    )
    matches: list[ProcessRow] = []
    for row in rows:
        if row.pid in {controller_pid, sampler_pid}:
            continue
        tokens = (row.executable,) + row.argv
        exact_path = str(launcher) in tokens or str(game_executable) in tokens
        group_match = spawned_pgid is not None and row.pgid == spawned_pgid
        descendant = _parent_reaches(row, by_pid, targets)
        second_probe = _contains_probe_invocation(row.argv, probe_script, game_root)
        previously_observed = _ProcessIdentity(row.pid, row.start_time) in observed_identities
        if group_match or descendant or exact_path or second_probe or previously_observed:
            matches.append(row)
    return tuple(sorted(matches, key=lambda row: row.pid))


def _require_no_matching_processes(
    matcher: Callable[[tuple[ProcessRow, ...], int], tuple[ProcessRow, ...]],
) -> tuple[ProcessRow, ...]:
    for attempt in range(2):
        snapshot = _process_snapshot()
        matches = matcher(snapshot.rows, snapshot.sampler_pid)
        if matches:
            raise PassiveProbeError(
                "matching probe processes remain: "
                + ",".join(str(row.pid) for row in matches)
            )
        if attempt == 0:
            time.sleep(0.1)
    return ()
```


- [ ] **Step 4: Run exact matching GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'matching_processes or process_absence'
```

Expected: numeric, exact-token, exact-path, and prior-identity rules pass without substring matches.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit exact matching**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: match exact passive probe processes"
```

### Task 13B: Track descendant identities throughout monitoring

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces mutable `_ObservedProcessTracker`; its set grows monotonically in `(pid, lstart)` identities.
- A helper observed while it is a descendant/PGID/path match remains a match after double-fork reparenting, PGID change, argv/path change, or executable disappearance. PID reuse with a different `lstart` is not inherited.

- [ ] **Step 1: Add double-fork/orphan/PID-reuse RED tests**

```python
def test_process_tracker_keeps_reparented_double_fork_helper(tmp_path: Path) -> None:
    tracker = passive._ObservedProcessTracker.for_paths(
        controller_pid=10,
        spawned_pid=20,
        spawned_pgid=20,
        launcher=tmp_path / "launcher",
        game_executable=tmp_path / "game",
        probe_script=tmp_path / "probe.py",
        game_root=tmp_path / "root",
    )
    parent = _row(21, 20, 20, "helper-parent")
    helper = _row(22, 21, 20, "helper-child", start_time="Thu Jul 31 12:40:00 2026")
    assert tuple(row.pid for row in tracker.observe((parent, helper), sampler_pid=99)) == (21, 22)

    orphan = replace(helper, ppid=1, pgid=22, executable="", argv=("renamed",))
    assert tuple(row.pid for row in tracker.match((orphan,), sampler_pid=100)) == (22,)
    reused = replace(orphan, start_time="Thu Jul 31 13:40:00 2026")
    assert tracker.match((reused,), sampler_pid=101) == ()


@pytest.mark.parametrize("drift", ("pgid_and_parent", "path_and_argv"))
def test_process_tracker_identity_survives_each_post_observation_drift(
    tmp_path: Path,
    drift: str,
) -> None:
    launcher = tmp_path / "launcher"
    tracker = passive._ObservedProcessTracker.for_paths(
        controller_pid=10,
        spawned_pid=20,
        spawned_pgid=20,
        launcher=launcher,
        game_executable=tmp_path / "game",
        probe_script=tmp_path / "probe.py",
        game_root=tmp_path / "root",
    )
    original = _row(
        31,
        20,
        20,
        str(launcher),
        executable=str(launcher),
        start_time="Thu Jul 31 12:41:00 2026",
    )
    assert tracker.observe((original,), sampler_pid=90) == (original,)
    if drift == "pgid_and_parent":
        changed = replace(original, ppid=1, pgid=31)
    else:
        changed = replace(original, executable="", argv=("anonymous-helper",))
    assert tracker.match((changed,), sampler_pid=91) == (changed,)
    assert tracker.identities == {
        passive._ProcessIdentity(original.pid, original.start_time)
    }
```

- [ ] **Step 2: Run the tracker RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'process_tracker or double_fork or reparented'
```

Expected: the reparented/path-changed helper is lost or PID reuse is falsely retained.

- [ ] **Step 3: Implement monotone identity tracking**

```python
@dataclass(slots=True)
class _ObservedProcessTracker:
    controller_pid: int
    spawned_pid: int | None
    spawned_pgid: int | None
    launcher: Path
    game_executable: Path
    probe_script: Path
    game_root: Path
    identities: set[_ProcessIdentity] = field(default_factory=set)

    @classmethod
    def for_paths(
        cls,
        *,
        controller_pid: int,
        spawned_pid: int | None,
        spawned_pgid: int | None,
        launcher: Path,
        game_executable: Path,
        probe_script: Path,
        game_root: Path,
    ) -> _ObservedProcessTracker:
        return cls(
            controller_pid,
            spawned_pid,
            spawned_pgid,
            launcher,
            game_executable,
            probe_script,
            game_root,
        )

    def match(
        self,
        rows: tuple[ProcessRow, ...],
        sampler_pid: int,
    ) -> tuple[ProcessRow, ...]:
        return _matching_probe_processes(
            rows,
            controller_pid=self.controller_pid,
            sampler_pid=sampler_pid,
            spawned_pid=self.spawned_pid,
            spawned_pgid=self.spawned_pgid,
            launcher=self.launcher,
            game_executable=self.game_executable,
            probe_script=self.probe_script,
            game_root=self.game_root,
            observed_identities=frozenset(self.identities),
        )

    def observe(
        self,
        rows: tuple[ProcessRow, ...],
        sampler_pid: int,
    ) -> tuple[ProcessRow, ...]:
        matches = self.match(rows, sampler_pid)
        self.identities.update(_ProcessIdentity(row.pid, row.start_time) for row in matches)
        return matches
```

- [ ] **Step 4: Run the tracker GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'process_tracker or double_fork or reparented'
```

Expected: identities grow monotonically; orphan/path/PGID drift remains matched; PID reuse does not.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit monitored identity tracking**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: retain observed passive helper identities"
```

### Task 13C: Prove process absence twice after reaping

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_require_no_matching_processes(...)`, which requires two empty snapshots separated by exactly 100 ms, and `_require_no_matching_processes_for_preflight(preflight, tracker)`.
- The currently executing controller and each real sampler PID are the only exclusions.

- [ ] **Step 1: Add two-snapshot and orphan-helper RED tests**

Add this seven-item matrix. It supplies both snapshots explicitly, including each real sampler PID, and consumes the retained Task 13B identity rather than reconstructing ancestry after reaping:

```python
@pytest.mark.parametrize(
    ("case", "fails"),
    (
        ("both_empty", False),
        ("match_only_second", True),
        ("orphan_only_first", True),
        ("orphan_only_second", True),
        ("controller_only", False),
        ("second_probe_tokens", True),
        ("old_sampler_reappears", True),
    ),
)
def test_process_absence_uses_two_exact_snapshots_and_retained_identities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    fails: bool,
) -> None:
    launcher = tmp_path / "run_bepinex.sh"
    game = tmp_path / "game"
    probe = tmp_path / "tools" / "oracle_passive_probe.py"
    executable = game / "Sausage.app/Contents/MacOS/Sausage"
    tracker = passive._ObservedProcessTracker(
        controller_pid=10,
        spawned_pid=20,
        spawned_pgid=20,
        launcher=launcher,
        game_executable=executable,
        probe_script=probe,
        game_root=game,
    )
    orphan = passive.ProcessRow(
        30, 1, 31, os.getuid(), "Thu Jul 31 12:30:00 2026", "/usr/bin/helper", ()
    )
    tracker.identities.add(passive._ProcessIdentity(orphan.pid, orphan.start_time))
    direct = passive.ProcessRow(
        40, 1, 40, os.getuid(), "Thu Jul 31 12:40:00 2026", str(launcher), (str(launcher),)
    )
    controller = replace(direct, pid=10, start_time="Thu Jul 31 12:10:00 2026")
    second_probe = replace(
        direct,
        pid=50,
        start_time="Thu Jul 31 12:50:00 2026",
        executable="/usr/bin/python3",
        argv=("python3", str(probe), "--game-root", str(game)),
    )
    old_sampler = replace(direct, pid=111, start_time="Thu Jul 31 12:11:00 2026")
    rows_by_case = {
        "both_empty": (((), 101), ((), 102)),
        "match_only_second": (((), 101), ((direct,), 102)),
        "orphan_only_first": (((orphan,), 101), ((), 102)),
        "orphan_only_second": (((), 101), ((orphan,), 102)),
        "controller_only": (((controller,), 101), ((controller,), 102)),
        "second_probe_tokens": (((second_probe,), 101), ((), 102)),
        "old_sampler_reappears": (((old_sampler,), 111), ((old_sampler,), 222)),
    }
    snapshots = iter(
        passive._ProcessSnapshot(rows, sampler)
        for rows, sampler in rows_by_case[case]
    )
    monkeypatch.setattr(passive, "_process_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(passive.time, "sleep", lambda seconds: None)
    if fails:
        with pytest.raises(passive.PassiveProbeError, match="matching probe processes remain"):
            passive._require_no_matching_processes(tracker.match)
    else:
        assert passive._require_no_matching_processes(tracker.match) == ()
```

- [ ] **Step 2: Run the absence RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'process_absence or orphan_helper'
```

Expected: absence does not yet consume retained identities or both real sampler IDs.

- [ ] **Step 3: Implement the exact two-snapshot proof**

```python
def _process_tracker_for_preflight(
    preflight: PassivePreflight,
    spawned_pid: int | None,
    spawned_pgid: int | None,
) -> _ObservedProcessTracker:
    probe_script = (
        Path(__file__).resolve(strict=True).parents[2]
        / "tools"
        / "oracle_passive_probe.py"
    )
    game_executable = (
        preflight.game_root
        / "Sausage.app"
        / "Contents"
        / "MacOS"
        / "Sausage"
    )

    return _ObservedProcessTracker(
        controller_pid=os.getpid(),
        spawned_pid=spawned_pid,
        spawned_pgid=spawned_pgid,
        launcher=preflight.launcher,
        game_executable=game_executable,
        probe_script=probe_script,
        game_root=preflight.game_root,
    )


def _require_no_matching_processes_for_preflight(
    preflight: PassivePreflight,
    tracker: _ObservedProcessTracker,
) -> tuple[ProcessRow, ...]:
    if tracker.game_root != preflight.game_root or tracker.launcher != preflight.launcher:
        raise PassiveProbeError("process tracker does not belong to this preflight")
    return _require_no_matching_processes(tracker.match)
```

- [ ] **Step 4: Run process-absence GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'matching_processes or process_absence'
```

Expected: PGID, descendant, orphan, exact launcher/game token, adjacent second-probe tokens, controller/sampler exclusion, PID reuse, parent loop, and two-snapshot recurrence rows pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the process-absence gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: prove passive probe process absence"
```

### Task 14A: Scan the isolated-save tree without mutation

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Consumes `PassiveLayout`, `IsolatedSaveEntry`, `MAX_SAVE_ENTRIES`, and `MAX_SAVE_BYTES`.
- Produces frozen `IsolatedSaveObservation(inventory, safe, issues, regular_bytes, truncated)` and mutation-free `_scan_isolated_save_tree(layout)`.
- Every supported entry has named-before, descriptor-before, descriptor-after, and named-after agreement; file hash byte count equals descriptor-after size. Unsupported entries are recorded, never traversed, and yield a deterministic partial unsafe inventory.

- [ ] **Step 1: Add exact security/inventory/depth/close RED tests**

Add five rows to the fourteen below: a 1,200-directory exact-bound tree completes without `RecursionError`; the next descendant is rejected before open/descent; a hash primary plus two descriptor-close failures retains primary identity and attempts both closes; a first close failure without an active primary is raised only after every owner is attempted; and a mutation caused while visiting a descendant is caught by the parent directory's EXIT revalidation.

```python
def test_scan_isolated_tree_hashes_without_changing_modes(
    passive_layout: passive.PassiveLayout,
) -> None:
    directory = passive_layout.isolated_save_dir / "slot"
    directory.mkdir(mode=0o755)
    save = directory / "save.bin"
    save.write_bytes(b"isolated")
    save.chmod(0o644)

    observed = passive._scan_isolated_save_tree(passive_layout)

    assert observed.safe is True
    assert observed.inventory == (
        passive.IsolatedSaveEntry("slot", "directory", 0o755, directory.stat().st_size, None),
        passive.IsolatedSaveEntry(
            "slot/save.bin",
            "file",
            0o644,
            len(b"isolated"),
            sha256(b"isolated").hexdigest(),
        ),
    )
    assert stat.S_IMODE(directory.stat().st_mode) == 0o755
    assert stat.S_IMODE(save.stat().st_mode) == 0o644


def test_scan_isolated_tree_preserves_and_reports_symlink(
    passive_layout: passive.PassiveLayout,
) -> None:
    link = passive_layout.isolated_save_dir / "unsafe"
    link.symlink_to(passive_layout.evidence_dir)
    observed = passive._scan_isolated_save_tree(passive_layout)
    assert observed.safe is False
    assert observed.inventory == (
        passive.IsolatedSaveEntry("unsafe", "symlink", 0o777, link.lstat().st_size, None),
    )
    assert observed.issues == ("unsupported isolated save entry: unsafe (symlink)",)
    assert link.is_symlink()


def _replace_isolated_name(path: Path) -> None:
    held = path.with_name(f"{path.name}.held")
    path.rename(held)
    if held.is_dir():
        path.mkdir()
    else:
        path.write_bytes(held.read_bytes())


@pytest.mark.parametrize(
    ("case", "boundary", "relative"),
    (
        ("root_after_named_before", "root_after_named_before", "."),
        ("root_before_named_after", "root_before_named_after", "."),
        ("directory_after_named_before", "entry_after_named_before", "slot"),
        ("directory_before_named_after", "entry_before_named_after", "slot"),
        ("file_after_named_before", "entry_after_named_before", "slot/save.bin"),
        ("file_before_named_after", "entry_before_named_after", "slot/save.bin"),
    ),
)
def test_isolated_named_after_and_descriptor_checks_reject_replacement(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    boundary: str,
    relative: str,
) -> None:
    del case
    slot = passive_layout.isolated_save_dir / "slot"
    slot.mkdir()
    (slot / "save.bin").write_bytes(b"save")
    fired = False

    def checkpoint(observed_boundary: str, observed_relative: str) -> None:
        nonlocal fired
        if not fired and (observed_boundary, observed_relative) == (boundary, relative):
            fired = True
            target = (
                passive_layout.isolated_save_dir
                if relative == "."
                else passive_layout.isolated_save_dir / relative
            )
            _replace_isolated_name(target)

    monkeypatch.setattr(passive, "_isolated_scan_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="changed|disagree"):
        passive._scan_isolated_save_tree(passive_layout)
    assert fired is True


@pytest.mark.parametrize("overflow", (False, True))
def test_isolated_inventory_entry_bound_is_inclusive(
    passive_layout: passive.PassiveLayout,
    overflow: bool,
) -> None:
    count = passive.MAX_SAVE_ENTRIES + int(overflow)
    for index in range(count):
        (passive_layout.isolated_save_dir / f"entry-{index:04d}").write_bytes(b"")
    observed = passive._scan_isolated_save_tree(passive_layout)
    assert len(observed.inventory) == passive.MAX_SAVE_ENTRIES
    assert observed.truncated is overflow
    assert observed.safe is (not overflow)


@pytest.mark.parametrize("overflow", (False, True))
def test_isolated_inventory_byte_bound_is_inclusive(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    overflow: bool,
) -> None:
    path = passive_layout.isolated_save_dir / "save.bin"
    size = passive.MAX_SAVE_BYTES + int(overflow)
    with path.open("wb") as stream:
        stream.truncate(size)
    monkeypatch.setattr(
        passive,
        "_hash_open_regular",
        lambda _fd, maximum: (maximum, "0" * 64),
    )
    observed = passive._scan_isolated_save_tree(passive_layout)
    assert observed.truncated is overflow
    assert observed.safe is (not overflow)
    assert observed.regular_bytes == (passive.MAX_SAVE_BYTES if not overflow else 0)


def test_scan_isolated_tree_preserves_and_reports_fifo(
    passive_layout: passive.PassiveLayout,
) -> None:
    fifo = passive_layout.isolated_save_dir / "unsafe-fifo"
    os.mkfifo(fifo)
    observed = passive._scan_isolated_save_tree(passive_layout)
    assert observed.safe is False
    assert observed.inventory[0].kind == "fifo"
    assert observed.issues == (
        "unsupported isolated save entry: unsafe-fifo (fifo)",
    )
    assert stat.S_ISFIFO(fifo.lstat().st_mode)


def test_scan_isolated_tree_sorts_encoded_relative_paths_and_hashes_exact_size(
    passive_layout: passive.PassiveLayout,
) -> None:
    for name, payload in (("z.bin", b"z"), ("a.bin", b"alpha")):
        (passive_layout.isolated_save_dir / name).write_bytes(payload)
    observed = passive._scan_isolated_save_tree(passive_layout)
    assert tuple(item.relative_path for item in observed.inventory) == ("a.bin", "z.bin")
    assert tuple(item.size for item in observed.inventory) == (5, 1)
    assert observed.regular_bytes == 6


@pytest.mark.parametrize("overflow", (False, True))
def test_scan_isolated_deep_tree_is_iterative_and_bounds_before_open(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    overflow: bool,
) -> None:
    monkeypatch.setattr(passive, "MAX_SAVE_ENTRIES", 1_200)
    _build_deep_save_directories(
        passive_layout.isolated_save_dir,
        1_200 + int(overflow),
    )
    original_open = passive.os.open
    overflow_opens = 0

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal overflow_opens
        if dir_fd is not None and os.fspath(path) == "d1200":
            overflow_opens += 1
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(passive.os, "open", opening)
    observed = passive._scan_isolated_save_tree(passive_layout)
    assert len(observed.inventory) == 1_200
    assert observed.truncated is overflow
    assert observed.safe is (not overflow)
    assert overflow_opens == 0


@pytest.mark.parametrize("active_primary", (False, True))
def test_scan_isolated_descriptor_cleanup_is_lifo_attempt_all(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    active_primary: bool,
) -> None:
    class CloseFailure(OSError):
        pass

    payload = passive_layout.isolated_save_dir / "outer" / "inner" / "save.bin"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"save")
    directory_inodes = {path.stat().st_ino for path in (payload.parent.parent, payload.parent)}
    opened_directories: list[int] = []
    close_attempts: list[int] = []
    original_open = passive.os.open
    original_close = passive.os.close
    original_hash = passive._hash_open_regular
    primary = KeyboardInterrupt("isolated hash interrupted")

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if dir_fd is not None and os.fstat(descriptor).st_ino in directory_inodes:
            opened_directories.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor in opened_directories:
            close_attempts.append(descriptor)
            original_close(descriptor)
            raise CloseFailure(f"close failed for {descriptor}")
        original_close(descriptor)

    def hashing(descriptor: int, maximum: int) -> tuple[int, str]:
        if active_primary:
            raise primary
        return original_hash(descriptor, maximum)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    monkeypatch.setattr(passive, "_hash_open_regular", hashing)
    if active_primary:
        with pytest.raises(KeyboardInterrupt) as caught:
            passive._scan_isolated_save_tree(passive_layout)
        assert caught.value is primary
        assert sum("secondary isolated-scan descriptor close failure" in note for note in primary.__notes__) == 2
    else:
        with pytest.raises(CloseFailure):
            passive._scan_isolated_save_tree(passive_layout)
    assert close_attempts == list(reversed(opened_directories))
    assert len(opened_directories) == len(set(close_attempts)) == 2


def test_scan_isolated_revalidates_directory_after_descendant_mutation(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slot = passive_layout.isolated_save_dir / "slot"
    slot.mkdir()
    save = slot / "save.bin"
    save.write_bytes(b"save")
    fired = False

    def checkpoint(boundary: str, relative: str) -> None:
        nonlocal fired
        if not fired and (boundary, relative) == (
            "entry_before_named_after",
            "slot/save.bin",
        ):
            fired = True
            (slot / "late-sibling").write_bytes(b"late")

    monkeypatch.setattr(passive, "_isolated_scan_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="directory changed during scan"):
        passive._scan_isolated_save_tree(passive_layout)
    assert fired is True
```

- [ ] **Step 2: Run mutation-free inventory RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'scan_isolated or isolated_named_after or isolated_inventory'
```

Expected: the old implementation mutates during traversal, lacks named-after checks, or discards the partial unsafe inventory; all nineteen Task-14A registrations are selected.

- [ ] **Step 3: Implement the complete mutation-free scanner**

```python
@dataclass(frozen=True, slots=True)
class IsolatedSaveObservation:
    inventory: tuple[IsolatedSaveEntry, ...]
    safe: bool
    issues: tuple[str, ...]
    regular_bytes: int
    truncated: bool


def _isolated_kind(mode: int) -> Literal["directory", "file", "symlink", "fifo", "other"]:
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISFIFO(mode):
        return "fifo"
    return "other"


def _isolated_scan_checkpoint(boundary: str, relative: str) -> None:
    del boundary, relative


@dataclass(slots=True)
class _IsolatedScanFrame:
    descriptor: int
    relative: Path
    names: tuple[str, ...]
    next_index: int
    owns_descriptor: bool
    parent_descriptor: int | None
    edge_name: str | None
    named_before: os.stat_result | None
    descriptor_before: os.stat_result | None
    entry_index: int | None


def _isolated_entry(
    relative: Path,
    kind: Literal["directory", "file", "symlink", "fifo", "other"],
    observed: os.stat_result,
    digest: str | None,
) -> IsolatedSaveEntry:
    return IsolatedSaveEntry(
        relative.as_posix(),
        kind,
        stat.S_IMODE(observed.st_mode),
        observed.st_size,
        digest,
    )


def _close_owned_isolated_scan_descriptor(
    owned: list[int],
    descriptor: int,
) -> None:
    if not owned or owned[-1] != descriptor:
        raise AssertionError("isolated-scan descriptor ownership is not LIFO")
    owned.pop()
    active = sys.exception()
    try:
        os.close(descriptor)
    except BaseException as error:
        if active is None:
            raise
        try:
            active.add_note(
                "secondary isolated-scan descriptor close failure: "
                f"{type(error).__name__}: {error}"
            )
        except BaseException:
            pass


def _scan_isolated_directory(
    descriptor: int,
    relative: Path,
    entries: list[IsolatedSaveEntry],
    regular_bytes: list[int],
    issues: list[str],
    truncated: list[bool],
) -> None:
    with os.scandir(descriptor) as discovered:
        root_names = tuple(
            sorted((entry.name for entry in discovered), key=os.fsencode)
        )
    stack = [
        _IsolatedScanFrame(
            descriptor,
            relative,
            root_names,
            0,
            False,
            None,
            None,
            None,
            None,
            None,
        )
    ]
    owned: list[int] = []
    first_close: BaseException | None = None
    try:
        while stack:
            frame = stack[-1]
            if truncated[0] and frame.next_index < len(frame.names):
                frame.next_index = len(frame.names)
            if frame.next_index == len(frame.names):
                stack.pop()
                if not frame.owns_descriptor:
                    continue
                if (
                    frame.parent_descriptor is None
                    or frame.edge_name is None
                    or frame.named_before is None
                    or frame.descriptor_before is None
                    or frame.entry_index is None
                ):
                    raise AssertionError("incomplete isolated-scan EXIT frame")
                _isolated_scan_checkpoint(
                    "entry_before_named_after",
                    frame.relative.as_posix(),
                )
                descriptor_after = os.fstat(frame.descriptor)
                named_after = os.stat(
                    frame.edge_name,
                    dir_fd=frame.parent_descriptor,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(descriptor_after.st_mode)
                    or not _same_save_metadata(
                        frame.named_before,
                        frame.descriptor_before,
                    )
                    or not _same_save_metadata(
                        frame.descriptor_before,
                        descriptor_after,
                    )
                    or not _same_save_metadata(descriptor_after, named_after)
                ):
                    raise PassiveProbeError(
                        f"isolated directory changed during scan: {frame.relative}"
                    )
                entries[frame.entry_index] = _isolated_entry(
                    frame.relative,
                    "directory",
                    descriptor_after,
                    None,
                )
                _close_owned_isolated_scan_descriptor(
                    owned,
                    frame.descriptor,
                )
                continue

            name = frame.names[frame.next_index]
            frame.next_index += 1
            child_relative = (
                Path(name)
                if frame.relative == Path(".")
                else frame.relative / name
            )
            # Refuse the first unreservable descendant before stat/open. The
            # already-held directory frames still unwind and revalidate.
            if len(entries) >= MAX_SAVE_ENTRIES:
                issues.append(
                    "isolated save exceeds 4096 descendants at "
                    f"{child_relative.as_posix()}"
                )
                truncated[0] = True
                continue
            named_before = os.stat(
                name,
                dir_fd=frame.descriptor,
                follow_symlinks=False,
            )
            _isolated_scan_checkpoint(
                "entry_after_named_before",
                child_relative.as_posix(),
            )
            kind = _isolated_kind(named_before.st_mode)

            if kind == "directory":
                child_fd = os.open(
                    name,
                    _DIRECTORY_FLAGS,
                    dir_fd=frame.descriptor,
                )
                owned.append(child_fd)
                descriptor_before = os.fstat(child_fd)
                if (
                    not stat.S_ISDIR(descriptor_before.st_mode)
                    or not _same_save_metadata(
                        named_before,
                        descriptor_before,
                    )
                ):
                    raise PassiveProbeError(
                        f"isolated directory changed before scan: {child_relative}"
                    )
                entry_index = len(entries)
                entries.append(
                    _isolated_entry(
                        child_relative,
                        "directory",
                        descriptor_before,
                        None,
                    )
                )
                with os.scandir(child_fd) as discovered:
                    child_names = tuple(
                        sorted(
                            (entry.name for entry in discovered),
                            key=os.fsencode,
                        )
                    )
                stack.append(
                    _IsolatedScanFrame(
                        child_fd,
                        child_relative,
                        child_names,
                        0,
                        True,
                        frame.descriptor,
                        name,
                        named_before,
                        descriptor_before,
                        entry_index,
                    )
                )
                continue

            if kind == "file":
                child_fd = os.open(
                    name,
                    _FILE_FLAGS,
                    dir_fd=frame.descriptor,
                )
                owned.append(child_fd)
                try:
                    descriptor_before = os.fstat(child_fd)
                    if (
                        not stat.S_ISREG(descriptor_before.st_mode)
                        or not _same_save_metadata(
                            named_before,
                            descriptor_before,
                        )
                    ):
                        raise PassiveProbeError(
                            f"isolated file changed before scan: {child_relative}"
                        )
                    remaining = MAX_SAVE_BYTES - regular_bytes[0]
                    if descriptor_before.st_size > remaining:
                        size = descriptor_before.st_size
                        digest = None
                        issues.append(
                            "isolated save exceeds 256 MiB at "
                            f"{child_relative.as_posix()}"
                        )
                        truncated[0] = True
                    else:
                        size, digest = _hash_open_regular(
                            child_fd,
                            remaining,
                        )
                    _isolated_scan_checkpoint(
                        "entry_before_named_after",
                        child_relative.as_posix(),
                    )
                    descriptor_after = os.fstat(child_fd)
                    named_after = os.stat(
                        name,
                        dir_fd=frame.descriptor,
                        follow_symlinks=False,
                    )
                    if (
                        not _same_save_metadata(
                            descriptor_before,
                            descriptor_after,
                        )
                        or not _same_save_metadata(
                            descriptor_after,
                            named_after,
                        )
                        or (
                            digest is not None
                            and size != descriptor_after.st_size
                        )
                    ):
                        raise PassiveProbeError(
                            f"isolated file changed during scan: {child_relative}"
                        )
                    if digest is not None:
                        regular_bytes[0] += size
                    entries.append(
                        _isolated_entry(
                            child_relative,
                            "file",
                            descriptor_after,
                            digest,
                        )
                    )
                finally:
                    _close_owned_isolated_scan_descriptor(
                        owned,
                        child_fd,
                    )
                continue

            _isolated_scan_checkpoint(
                "entry_before_named_after",
                child_relative.as_posix(),
            )
            named_after = os.stat(
                name,
                dir_fd=frame.descriptor,
                follow_symlinks=False,
            )
            if not _same_save_metadata(named_before, named_after):
                raise PassiveProbeError(
                    f"unsupported isolated entry changed: {child_relative}"
                )
            entries.append(
                _isolated_entry(
                    child_relative,
                    kind,
                    named_after,
                    None,
                )
            )
            issues.append(
                "unsupported isolated save entry: "
                f"{child_relative.as_posix()} ({kind})"
            )
    finally:
        active = sys.exception()
        while owned:
            closing = owned.pop()
            try:
                os.close(closing)
            except BaseException as error:
                if active is not None:
                    try:
                        active.add_note(
                            "secondary isolated-scan descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
                elif first_close is None:
                    first_close = error
                else:
                    try:
                        first_close.add_note(
                            "later isolated-scan descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
        if active is None and first_close is not None:
            raise first_close


def _scan_isolated_save_tree(
    layout: PassiveLayout,
) -> IsolatedSaveObservation:
    entries: list[IsolatedSaveEntry] = []
    total = [0]
    issues: list[str] = []
    truncated = [False]
    named_before = os.stat(layout.isolated_save_dir, follow_symlinks=False)
    _isolated_scan_checkpoint("root_after_named_before", ".")
    descriptor_before = os.fstat(layout.isolated_save_handle.fd)
    if not _same_save_metadata(named_before, descriptor_before):
        raise PassiveProbeError("isolated save root name and descriptor disagree")
    _scan_isolated_directory(
        layout.isolated_save_handle.fd,
        Path("."),
        entries,
        total,
        issues,
        truncated,
    )
    descriptor_after = os.fstat(layout.isolated_save_handle.fd)
    _isolated_scan_checkpoint("root_before_named_after", ".")
    named_after = os.stat(layout.isolated_save_dir, follow_symlinks=False)
    if (
        not _same_save_metadata(descriptor_before, descriptor_after)
        or not _same_save_metadata(descriptor_after, named_after)
    ):
        raise PassiveProbeError("isolated save root changed during scan")
    inventory = tuple(sorted(entries, key=lambda item: os.fsencode(item.relative_path)))
    return IsolatedSaveObservation(
        inventory=inventory,
        safe=not issues and not truncated[0],
        issues=tuple(issues),
        regular_bytes=total[0],
        truncated=truncated[0],
    )
```

- [ ] **Step 4: Run mutation-free inventory GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'scan_isolated or isolated_named_after or isolated_inventory'
```

Expected: all nineteen rows pass; stable nested files/directories hash exactly; 1,200 levels do not recurse; bounds are checked before descent; substitutions and close failures fail without masking or leaking; unsupported symlink/FIFO rows return a defined partial unsafe inventory without traversal.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the mutation-free scanner**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: inventory retained isolated oracle saves"
```

### Task 14B: Secure a safe isolated tree once, then scan it twice

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_secure_isolated_save_tree(layout) -> IsolatedSaveObservation`.
- Runs one mutation-free validation scan first. If unsafe, returns it unchanged and performs zero chmod/fsync operations. If safe, validates each name/type, chmods each unique inode once (`0700` directory, `0600` file), fsyncs it, then performs two mutation-free scans and requires exact equality.

- [ ] **Step 1: Add securing, bounds, FIFO, fsync, depth, and close RED tests**

The seventeen rows below include four focused iterative-owner regressions beyond the original thirteen: 1,200 safe nested directories secure without `RecursionError`; the securing worklist never opens a node absent from the validation inventory; a retained child descriptor remains live through post-descendant EXIT validation; and descendant mutation is caught at that EXIT boundary. The two close rows independently prove that an active chmod primary plus two close failures retains identity and that, without a primary, the first close failure is raised only after all descriptors close.

```python
def test_secure_isolated_tree_sets_modes_then_reads_twice(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = passive_layout.isolated_save_dir / "slot"
    directory.mkdir(mode=0o755)
    save = directory / "save.bin"
    save.write_bytes(b"isolated")
    save.chmod(0o644)
    calls: list[str] = []
    original_scan = passive._scan_isolated_save_tree

    def scan(layout: passive.PassiveLayout) -> passive.IsolatedSaveObservation:
        calls.append("scan")
        return original_scan(layout)

    monkeypatch.setattr(passive, "_scan_isolated_save_tree", scan)
    observed = passive._secure_isolated_save_tree(passive_layout)
    assert observed.safe is True
    assert calls == ["scan", "scan", "scan"]  # validate, post-secure pass 1, pass 2
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(save.stat().st_mode) == 0o600


@pytest.mark.parametrize(
    ("case", "safe", "truncated"),
    (
        ("entries_exact", True, False),
        ("entries_plus_one", False, True),
        ("bytes_exact", True, False),
        ("bytes_plus_one", False, True),
    ),
)
def test_secure_isolated_tree_honors_inclusive_validation_bounds(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    safe: bool,
    truncated: bool,
) -> None:
    if case.startswith("entries"):
        inventory = tuple(
            passive.IsolatedSaveEntry(f"item-{index}", "file", 0o600, 0, sha256(b"").hexdigest())
            for index in range(passive.MAX_SAVE_ENTRIES)
        )
        regular_bytes = 0
    else:
        inventory = ()
        regular_bytes = passive.MAX_SAVE_BYTES if safe else 0
    issues = () if safe else (f"validation rejected {case}",)
    validation = passive.IsolatedSaveObservation(
        inventory=inventory,
        safe=safe,
        issues=issues,
        regular_bytes=regular_bytes,
        truncated=truncated,
    )
    scans: list[passive.IsolatedSaveObservation] = []
    secured: list[Path] = []

    def scan(_layout: passive.PassiveLayout) -> passive.IsolatedSaveObservation:
        scans.append(validation)
        return validation

    def secure(
        _fd: int,
        absolute: Path,
        _seen: set[tuple[int, int]],
        expected_inventory: tuple[passive.IsolatedSaveEntry, ...],
        *,
        is_root: bool,
    ) -> None:
        assert is_root is True
        assert expected_inventory == validation.inventory
        secured.append(absolute)

    monkeypatch.setattr(passive, "_scan_isolated_save_tree", scan)
    monkeypatch.setattr(passive, "_secure_isolated_directory_once", secure)
    assert passive._secure_isolated_save_tree(passive_layout) is validation
    assert len(scans) == (3 if safe else 1)
    assert secured == ([passive_layout.isolated_save_dir] if safe else [])


@pytest.mark.parametrize("kind", ("symlink", "fifo"))
def test_secure_isolated_tree_preserves_unsafe_entries_without_mutation(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    path = passive_layout.isolated_save_dir / "unsafe"
    if kind == "symlink":
        path.symlink_to(passive_layout.evidence_dir)
    else:
        os.mkfifo(path)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("unsafe validation must perform no chmod or fsync")

    monkeypatch.setattr(passive.os, "fchmod", forbidden)
    monkeypatch.setattr(passive.os, "fsync", forbidden)
    observed = passive._secure_isolated_save_tree(passive_layout)
    assert observed.safe is False
    assert observed.inventory[0].kind == kind
    assert passive._isolated_kind(path.lstat().st_mode) == kind


def test_secure_isolated_tree_rejects_named_replacement_before_chmod(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = passive_layout.isolated_save_dir / "save.bin"
    path.write_bytes(b"save")
    fired = False

    def checkpoint(boundary: str, absolute: Path) -> None:
        nonlocal fired
        if not fired and boundary == "before_chmod" and absolute == path:
            fired = True
            _replace_isolated_name(path)

    monkeypatch.setattr(passive, "_isolated_secure_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="changed"):
        passive._secure_isolated_save_tree(passive_layout)
    assert fired is True


@pytest.mark.parametrize("target", ("root", "directory", "file"))
def test_secure_isolated_tree_propagates_each_fsync_failure(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    slot = passive_layout.isolated_save_dir / "slot"
    slot.mkdir()
    save = slot / "save.bin"
    save.write_bytes(b"save")
    inode = {
        "root": passive_layout.isolated_save_dir.stat().st_ino,
        "directory": slot.stat().st_ino,
        "file": save.stat().st_ino,
    }[target]
    original_fsync = passive.os.fsync

    def fsync(descriptor: int) -> None:
        if passive.os.fstat(descriptor).st_ino == inode:
            raise OSError(f"{target} fsync failed")
        original_fsync(descriptor)

    monkeypatch.setattr(passive.os, "fsync", fsync)
    with pytest.raises(OSError, match=f"{target} fsync failed"):
        passive._secure_isolated_save_tree(passive_layout)


@pytest.mark.parametrize("active_primary", (False, True))
def test_isolated_close_attempts_every_owned_descriptor_and_preserves_primary(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    active_primary: bool,
) -> None:
    class CloseFailure(OSError):
        pass

    slot = passive_layout.isolated_save_dir / "slot"
    slot.mkdir()
    save = slot / "save.bin"
    save.write_bytes(b"save")
    safe = passive._scan_isolated_save_tree(passive_layout)
    monkeypatch.setattr(passive, "_scan_isolated_save_tree", lambda _layout: safe)
    original_open = passive.os.open
    original_close = passive.os.close
    original_fchmod = passive.os.fchmod
    owned: list[int] = []
    closed: list[int] = []
    primary = RuntimeError("active primary")
    save_inode = save.stat().st_ino

    def opening(name, flags, mode=0o777, *, dir_fd=None):
        descriptor = original_open(name, flags, mode, dir_fd=dir_fd)
        if dir_fd is not None:
            owned.append(descriptor)
        return descriptor

    def closing(descriptor: int) -> None:
        if descriptor in owned:
            closed.append(descriptor)
            original_close(descriptor)
            raise CloseFailure(f"close failed for {descriptor}")
        original_close(descriptor)

    def chmod(descriptor: int, mode: int) -> None:
        if active_primary and passive.os.fstat(descriptor).st_ino == save_inode:
            raise primary
        original_fchmod(descriptor, mode)

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive.os, "close", closing)
    monkeypatch.setattr(passive.os, "fchmod", chmod)
    if active_primary:
        with pytest.raises(RuntimeError) as caught:
            passive._secure_isolated_save_tree(passive_layout)
        assert caught.value is primary
        assert any("secondary isolated descriptor close failure" in note for note in primary.__notes__)
    else:
        with pytest.raises(CloseFailure):
            passive._secure_isolated_save_tree(passive_layout)
    assert len(owned) == 2
    assert set(closed) == set(owned)


def test_secure_isolated_deep_tree_is_iterative(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(passive, "MAX_SAVE_ENTRIES", 1_200)
    _build_deep_save_directories(passive_layout.isolated_save_dir, 1_200)
    observed = passive._secure_isolated_save_tree(passive_layout)
    assert observed.safe is True
    assert len(observed.inventory) == 1_200
    assert all(entry.kind == "directory" and entry.mode == 0o700 for entry in observed.inventory)


def test_secure_isolated_never_opens_growth_beyond_validation_inventory(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    late = passive_layout.isolated_save_dir / "late"
    original_open = passive.os.open
    late_opens = 0
    fired = False

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        nonlocal late_opens
        if dir_fd is not None and os.fspath(path) == late.name:
            late_opens += 1
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def checkpoint(boundary: str, absolute: Path) -> None:
        nonlocal fired
        if not fired and boundary == "before_chmod" and absolute == passive_layout.isolated_save_dir:
            fired = True
            late.write_bytes(b"late")

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive, "_isolated_secure_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="changed after validation"):
        passive._secure_isolated_save_tree(passive_layout)
    assert fired is True
    assert late_opens == 0


def test_secure_isolated_child_fd_is_live_at_post_descendant_exit(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slot = passive_layout.isolated_save_dir / "slot"
    slot.mkdir()
    (slot / "save.bin").write_bytes(b"save")
    original_open = passive.os.open
    opened: list[int] = []
    checked = False

    def opening(path: object, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if dir_fd is not None and os.fspath(path) == slot.name:
            opened.append(descriptor)
        return descriptor

    def checkpoint(boundary: str, absolute: Path) -> None:
        nonlocal checked
        if boundary == "directory_before_named_after" and absolute == slot:
            assert len(opened) == 1
            assert stat.S_ISDIR(os.fstat(opened[0]).st_mode)
            checked = True

    monkeypatch.setattr(passive.os, "open", opening)
    monkeypatch.setattr(passive, "_isolated_secure_checkpoint", checkpoint)
    observed = passive._secure_isolated_save_tree(passive_layout)
    assert observed.safe is True
    assert checked is True


def test_secure_isolated_revalidates_directory_after_descendant_mutation(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slot = passive_layout.isolated_save_dir / "slot"
    slot.mkdir()
    save = slot / "save.bin"
    save.write_bytes(b"save")
    fired = False

    def checkpoint(boundary: str, absolute: Path) -> None:
        nonlocal fired
        if not fired and boundary == "after_secure" and absolute == save:
            fired = True
            (slot / "late-sibling").write_bytes(b"late")

    monkeypatch.setattr(passive, "_isolated_secure_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="directory changed while securing"):
        passive._secure_isolated_save_tree(passive_layout)
    assert fired is True
```

- [ ] **Step 2: Run the securing RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'secure_isolated or isolated_exact_bound or isolated_fifo or isolated_fsync or isolated_close'
```

Expected: one-time security or the three-scan sequence is absent; all seventeen Task-14B registrations are selected.

- [ ] **Step 3: Implement one-time security and two mutation-free scans**

Add the complete owner and securing walk:

```python
def _same_isolated_object(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_size,
        left.st_mtime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_size,
        right.st_mtime_ns,
    )


def _isolated_secure_checkpoint(boundary: str, absolute: Path) -> None:
    del boundary, absolute


def _secure_one_isolated_inode(
    descriptor: int,
    mode: int,
    secured: set[tuple[int, int]],
) -> os.stat_result:
    before = os.fstat(descriptor)
    key = (before.st_dev, before.st_ino)
    if key not in secured:
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
        secured.add(key)
    after = os.fstat(descriptor)
    if (
        not _same_isolated_object(before, after)
        or stat.S_IMODE(after.st_mode) != mode
    ):
        raise PassiveProbeError("isolated save changed while securing")
    return after


@dataclass(slots=True)
class _IsolatedSecureFrame:
    descriptor: int
    absolute: Path
    relative: Path
    names: tuple[str, ...]
    next_index: int
    owns_descriptor: bool
    parent_descriptor: int | None
    edge_name: str | None
    named_before: os.stat_result | None
    descriptor_before: os.stat_result | None


def _close_owned_isolated_secure_descriptor(
    owned: list[int],
    descriptor: int,
) -> None:
    if not owned or owned[-1] != descriptor:
        raise AssertionError("isolated-secure descriptor ownership is not LIFO")
    owned.pop()
    active = sys.exception()
    try:
        os.close(descriptor)
    except BaseException as error:
        if active is None:
            raise
        try:
            active.add_note(
                "secondary isolated descriptor close failure: "
                f"{type(error).__name__}: {error}"
            )
        except BaseException:
            pass


def _secure_isolated_directory_once(
    descriptor: int,
    absolute: Path,
    secured: set[tuple[int, int]],
    expected_inventory: tuple[IsolatedSaveEntry, ...],
    *,
    is_root: bool,
) -> None:
    root_named = os.stat(absolute, follow_symlinks=False) if is_root else None
    root_before = os.fstat(descriptor)
    if root_named is not None and (
        not stat.S_ISDIR(root_named.st_mode)
        or not _same_save_metadata(root_named, root_before)
    ):
        raise PassiveProbeError("isolated save root changed before securing")
    _isolated_secure_checkpoint("before_chmod", absolute)
    _secure_one_isolated_inode(descriptor, 0o700, secured)
    expected = {
        entry.relative_path: entry.kind
        for entry in expected_inventory
    }
    if (
        len(expected) != len(expected_inventory)
        or any(kind not in {"directory", "file"} for kind in expected.values())
    ):
        raise PassiveProbeError("safe isolated validation inventory is inconsistent")
    with os.scandir(descriptor) as discovered:
        root_names = tuple(
            sorted((entry.name for entry in discovered), key=os.fsencode)
        )
    stack = [
        _IsolatedSecureFrame(
            descriptor,
            absolute,
            Path("."),
            root_names,
            0,
            False,
            None,
            None,
            None,
            None,
        )
    ]
    visited: set[str] = set()
    owned: list[int] = []
    first_close: BaseException | None = None
    try:
        while stack:
            frame = stack[-1]
            if frame.next_index == len(frame.names):
                stack.pop()
                if not frame.owns_descriptor:
                    continue
                if (
                    frame.parent_descriptor is None
                    or frame.edge_name is None
                    or frame.named_before is None
                    or frame.descriptor_before is None
                ):
                    raise AssertionError("incomplete isolated-secure EXIT frame")
                _isolated_secure_checkpoint(
                    "directory_before_named_after",
                    frame.absolute,
                )
                descriptor_after = os.fstat(frame.descriptor)
                named_after = os.stat(
                    frame.edge_name,
                    dir_fd=frame.parent_descriptor,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(descriptor_after.st_mode)
                    or stat.S_IMODE(descriptor_after.st_mode) != 0o700
                    or not _same_isolated_object(
                        frame.descriptor_before,
                        descriptor_after,
                    )
                    or not _same_save_metadata(descriptor_after, named_after)
                ):
                    raise PassiveProbeError(
                        f"isolated directory changed while securing: {frame.absolute}"
                    )
                _close_owned_isolated_secure_descriptor(
                    owned,
                    frame.descriptor,
                )
                continue

            name = frame.names[frame.next_index]
            frame.next_index += 1
            child_relative = (
                Path(name)
                if frame.relative == Path(".")
                else frame.relative / name
            )
            relative_text = child_relative.as_posix()
            child_absolute = frame.absolute / name
            # Membership and the global reservation bound are checked before
            # stat/open/descent. No post-validation growth is ever opened.
            expected_kind = expected.get(relative_text)
            if (
                expected_kind is None
                or relative_text in visited
                or len(visited) >= len(expected_inventory)
            ):
                raise PassiveProbeError(
                    f"isolated save changed after validation: {child_absolute}"
                )
            named_before = os.stat(
                name,
                dir_fd=frame.descriptor,
                follow_symlinks=False,
            )
            kind = _isolated_kind(named_before.st_mode)
            if kind != expected_kind or kind not in {"directory", "file"}:
                raise PassiveProbeError(
                    f"isolated save type changed after validation: {child_absolute}"
                )
            flags = _DIRECTORY_FLAGS if kind == "directory" else _FILE_FLAGS
            child_fd = os.open(
                name,
                flags,
                dir_fd=frame.descriptor,
            )
            owned.append(child_fd)
            descriptor_before = os.fstat(child_fd)
            if (
                not _same_save_metadata(named_before, descriptor_before)
                or (
                    kind == "directory"
                    and not stat.S_ISDIR(descriptor_before.st_mode)
                )
                or (
                    kind == "file"
                    and not stat.S_ISREG(descriptor_before.st_mode)
                )
            ):
                raise PassiveProbeError(
                    f"isolated save name changed before securing: {child_absolute}"
                )
            visited.add(relative_text)
            target_mode = 0o700 if kind == "directory" else 0o600
            _isolated_secure_checkpoint("before_chmod", child_absolute)
            _secure_one_isolated_inode(child_fd, target_mode, secured)
            _isolated_secure_checkpoint("after_secure", child_absolute)

            if kind == "directory":
                with os.scandir(child_fd) as discovered:
                    child_names = tuple(
                        sorted(
                            (entry.name for entry in discovered),
                            key=os.fsencode,
                        )
                    )
                stack.append(
                    _IsolatedSecureFrame(
                        child_fd,
                        child_absolute,
                        child_relative,
                        child_names,
                        0,
                        True,
                        frame.descriptor,
                        name,
                        named_before,
                        descriptor_before,
                    )
                )
                continue

            try:
                descriptor_after = os.fstat(child_fd)
                named_after = os.stat(
                    name,
                    dir_fd=frame.descriptor,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISREG(descriptor_after.st_mode)
                    or stat.S_IMODE(descriptor_after.st_mode) != 0o600
                    or not _same_isolated_object(
                        descriptor_before,
                        descriptor_after,
                    )
                    or not _same_save_metadata(descriptor_after, named_after)
                ):
                    raise PassiveProbeError(
                        f"isolated file changed while securing: {child_absolute}"
                    )
            finally:
                _close_owned_isolated_secure_descriptor(owned, child_fd)

        if visited != set(expected):
            missing = sorted(set(expected) - visited, key=os.fsencode)
            raise PassiveProbeError(
                "isolated save changed after validation; missing entries: "
                + ",".join(missing)
            )
        root_after = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(root_after.st_mode)
            or stat.S_IMODE(root_after.st_mode) != 0o700
            or not _same_isolated_object(root_before, root_after)
        ):
            raise PassiveProbeError(f"isolated directory mode drifted: {absolute}")
        if is_root:
            named_after = os.stat(absolute, follow_symlinks=False)
            if not _same_save_metadata(root_after, named_after):
                raise PassiveProbeError("isolated save root changed after securing")
    finally:
        active = sys.exception()
        while owned:
            closing = owned.pop()
            try:
                os.close(closing)
            except BaseException as error:
                if active is not None:
                    try:
                        active.add_note(
                            "secondary isolated descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
                elif first_close is None:
                    first_close = error
                else:
                    try:
                        first_close.add_note(
                            "later isolated descriptor close failure: "
                            f"{type(error).__name__}: {error}"
                        )
                    except BaseException:
                        pass
        if active is None and first_close is not None:
            raise first_close
```

Then add:

```python
def _secure_isolated_save_tree(layout: PassiveLayout) -> IsolatedSaveObservation:
    validation = _scan_isolated_save_tree(layout)
    if not validation.safe:
        return validation
    secured: set[tuple[int, int]] = set()
    _secure_isolated_directory_once(
        layout.isolated_save_handle.fd,
        layout.isolated_save_dir,
        secured,
        validation.inventory,
        is_root=True,
    )
    first = _scan_isolated_save_tree(layout)
    second = _scan_isolated_save_tree(layout)
    if first != second:
        raise PassiveProbeError("isolated save changed between stable scans")
    return second
```

- [ ] **Step 4: Run the securing GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'secure_isolated or isolated_exact_bound or isolated_fifo or isolated_fsync or isolated_close'
```

Expected: all seventeen rows pass; safe trees are secured once then read twice; 1,200 levels do not recurse; no securing descent exceeds the validation inventory; unsafe partial inventories are preserved without mutation; all failure-injection and attempt-all-close rows pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit isolated-save security**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: secure isolated saves before stable reads"
```

### Task 15A: Define passive lifecycle snapshot and result models

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces frozen `PassiveInstallSnapshot`, `SecondaryError`, `PassiveCleanup`, and `PassiveProbeResult` with exact fields below.
- Every passive snapshot wraps the complete legacy `_BootSnapshot`, observed installed plugin/config hashes, and exact `InstallStatus` values from both sides of the observation window.
- `PassiveProbeResult` carries the host-derived macOS product version from the later standalone preflight so every safely published lifecycle result retains that compatibility boundary.

- [ ] **Step 1: Add exact snapshot/result RED tests**

```python
from ssr_env import oracle_boot, oracle_install


@pytest.fixture
def installed_game(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, oracle_install.InstallStatus]:
    game = tmp_path / "game"
    plugin = game / oracle_install.PLUGIN_RELATIVE_PATH
    config = game / oracle_install.CONFIG_RELATIVE_PATH
    plugin.parent.mkdir(parents=True)
    config.parent.mkdir(parents=True, exist_ok=True)
    plugin.write_bytes(b"reviewed-plugin")
    config.write_bytes(b"[Oracle]\nMode = off\n")
    manifest = oracle_install.InstallManifest(
        schema_version=1,
        game_assembly_sha256="1" * 64,
        runtime_archive_sha256="4" * 64,
        entries=(
            oracle_install.ManifestEntry(
                oracle_install.PLUGIN_RELATIVE_PATH,
                "file",
                sha256(plugin.read_bytes()).hexdigest(),
            ),
            oracle_install.ManifestEntry(
                oracle_install.CONFIG_RELATIVE_PATH,
                "file",
                sha256(config.read_bytes()).hexdigest(),
            ),
        ),
    )
    status = oracle_install.InstallStatus(
        manifest=manifest,
        missing=(),
        changed=(),
        preloader_compatibility=oracle_install.PreloaderCompatibilityStatus(
            state="official",
            official_sha256="2" * 64,
            active_sha256="2" * 64,
            patched_sha256=None,
            issues=(),
        ),
    )
    monkeypatch.setattr(passive, "status_install", lambda _root: status)
    return game, status


def test_passive_snapshot_wraps_legacy_hashes_and_full_installer_status(
    installed_game: tuple[Path, oracle_install.InstallStatus],
) -> None:
    game, status = installed_game
    legacy = oracle_boot._BootSnapshot(
        assembly_sha256="1" * 64,
        active_preloader_sha256="2" * 64,
        installer_healthy=True,
        compatibility_state="official",
        app_signature=oracle_boot._AppSignature(0, "valid", ""),
    )
    observed = passive.PassiveInstallSnapshot(
        legacy,
        sha256((game / oracle_install.PLUGIN_RELATIVE_PATH).read_bytes()).hexdigest(),
        sha256((game / oracle_install.CONFIG_RELATIVE_PATH).read_bytes()).hexdigest(),
        status,
        status,
    )
    assert observed.legacy is legacy
    assert observed.installer_status_before is status
    assert observed.installer_status_after is status
    assert observed.installer_status is status


def test_trace_summary_payload_keeps_parse_status_and_nullable_error_code() -> None:
    malformed = passive.TraceSummary(
        path="/private/passive-trace.ndjson",
        parse_status="malformed",
        outcome=None,
        error_code=None,
        record_count=None,
        step_count=None,
        sha256="3" * 64,
        size=9,
    )
    assert malformed.parse_status == "malformed"
    assert malformed.outcome is malformed.error_code is None
    assert malformed.record_count is malformed.step_count is None
    assert malformed.sha256 == "3" * 64 and malformed.size == 9


def test_passive_snapshot_model_has_exact_frozen_fields() -> None:
    from dataclasses import fields

    assert tuple(item.name for item in fields(passive.PassiveInstallSnapshot)) == (
        "legacy",
        "observed_plugin_sha256",
        "observed_config_sha256",
        "installer_status_before",
        "installer_status_after",
    )


def test_passive_result_model_has_exact_lifecycle_fields() -> None:
    from dataclasses import fields

    assert tuple(item.name for item in fields(passive.PassiveProbeResult)) == (
        "success", "started_at_utc", "finished_at_utc", "controller_pid",
        "game_root", "macos_product_version", "launcher", "evidence_dir", "isolated_save_dir",
        "plugin_sha256", "mode_off_config_sha256", "passive_config_sha256",
        "markers", "issues", "secondary_errors", "exit_code", "run_id",
        "cleanup", "before", "patched", "post_process", "after",
        "before_logs", "after_logs", "ordinary_save_before",
        "ordinary_save_after", "ordinary_save_final", "isolated_save", "trace",
        "copied_logs", "moved_logs", "restore_recovery_dir",
    )
```

- [ ] **Step 2: Run snapshot/result RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'passive_snapshot or trace_summary_payload or passive_result_model'
```

Expected: passive snapshot/result types and payload helpers are missing.

- [ ] **Step 3: Add exact lifecycle models and serialization**

Add installer imports and models:

```python
from ssr_env import oracle_install
from ssr_env.oracle_install import InstallStatus, status_install


@dataclass(frozen=True, slots=True)
class PassiveInstallSnapshot:
    legacy: oracle_boot._BootSnapshot
    observed_plugin_sha256: str
    observed_config_sha256: str
    installer_status_before: InstallStatus
    installer_status_after: InstallStatus

    @property
    def installer_status(self) -> InstallStatus:
        return self.installer_status_after


@dataclass(frozen=True, slots=True)
class SecondaryError:
    stage: str
    type: str
    message: str


@dataclass(frozen=True, slots=True)
class PassiveCleanup:
    process_group_stopped: bool
    no_matching_processes: bool
    mode_off_restored: bool
    official_preloader_restored: bool
    installed_status_healthy: bool
    ordinary_save_unchanged: bool


@dataclass(frozen=True, slots=True)
class PassiveProbeResult:
    success: bool
    started_at_utc: str
    finished_at_utc: str
    controller_pid: int
    game_root: Path
    macos_product_version: str
    launcher: Path
    evidence_dir: Path
    isolated_save_dir: Path
    plugin_sha256: str
    mode_off_config_sha256: str
    passive_config_sha256: str
    markers: tuple[str, ...]
    issues: tuple[str, ...]
    secondary_errors: tuple[SecondaryError, ...]
    exit_code: int | None
    run_id: str | None
    cleanup: PassiveCleanup
    before: PassiveInstallSnapshot
    patched: PassiveInstallSnapshot | None
    post_process: PassiveInstallSnapshot | None
    after: PassiveInstallSnapshot | None
    before_logs: tuple[oracle_boot.LogFingerprint, ...]
    after_logs: tuple[oracle_boot.LogFingerprint, ...]
    ordinary_save_before: SaveTreeProof
    ordinary_save_after: SaveTreeProof | None
    ordinary_save_final: SaveTreeProof | None
    isolated_save: IsolatedSaveObservation
    trace: TraceSummary | None
    copied_logs: tuple[Path, ...]
    moved_logs: tuple[Path, ...]
    restore_recovery_dir: Path | None
```

- [ ] **Step 4: Run the lifecycle-model GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'passive_result_model or passive_snapshot or trace_summary_payload'
```

Expected: immutable models expose both installer statuses, complete cleanup, partial isolated diagnostics, required `before`, and exactly three nullable lifecycle stages: `patched`, `post_process`, and `after`.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit lifecycle models**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: define passive lifecycle evidence models"
```

### Task 15B: Capture stable installed snapshots with manifest agreement

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_hash_installed_file` and `_capture_passive_snapshot(game_root)`.
- Requires `status_before == status_after`; manifest plugin/config hashes equal the descriptor-observed hashes; manifest assembly and compatibility active hashes equal the legacy snapshot.

- [ ] **Step 1: Add status-race and manifest-mismatch RED tests**

Add the following sixteen collected cases. The checkpoint is a no-op production seam placed at `after_named_before` and `before_named_after` inside `_hash_installed_file`; it never changes the public interface:

```python
@pytest.mark.parametrize(
    "case",
    (
        "status_missing_drift",
        "status_changed_drift",
        "status_manifest_drift",
        "status_compatibility_drift",
        "manifest_plugin_mismatch",
        "manifest_config_mismatch",
        "manifest_assembly_mismatch",
        "active_preloader_mismatch",
        "plugin_replace_after_named_before",
        "plugin_replace_before_named_after",
        "config_replace_after_named_before",
        "config_replace_before_named_after",
        "hash_exact_bound",
        "hash_bound_plus_one",
        "close_failure_without_primary",
        "close_failure_with_primary",
    ),
)
def test_passive_snapshot_rejects_every_race_mismatch_and_owner_failure(
    installed_game: tuple[Path, oracle_install.InstallStatus],
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    game, healthy = installed_game
    plugin_path = game / oracle_install.PLUGIN_RELATIVE_PATH
    config_path = game / oracle_install.CONFIG_RELATIVE_PATH
    legacy = oracle_boot._BootSnapshot(
        healthy.manifest.game_assembly_sha256,
        healthy.preloader_compatibility.active_sha256,
        True,
        healthy.preloader_compatibility.state,
        oracle_boot._AppSignature(0, "valid", ""),
    )
    monkeypatch.setattr(oracle_boot, "_capture_boot_snapshot", lambda _root: legacy)

    if case.startswith("status_"):
        drift = {
            "status_missing_drift": replace(healthy, missing=("plugin",)),
            "status_changed_drift": replace(healthy, changed=("config",)),
            "status_manifest_drift": replace(
                healthy,
                manifest=replace(healthy.manifest, runtime_archive_sha256="9" * 64),
            ),
            "status_compatibility_drift": replace(
                healthy,
                preloader_compatibility=replace(
                    healthy.preloader_compatibility, state="patched"
                ),
            ),
        }[case]
        statuses = iter((healthy, drift))
        monkeypatch.setattr(passive, "status_install", lambda _root: next(statuses))
    elif case in {
        "manifest_plugin_mismatch",
        "manifest_config_mismatch",
        "manifest_assembly_mismatch",
        "active_preloader_mismatch",
    }:
        altered = healthy
        if case.startswith("manifest_plugin") or case.startswith("manifest_config"):
            target = (
                oracle_install.PLUGIN_RELATIVE_PATH
                if "plugin" in case
                else oracle_install.CONFIG_RELATIVE_PATH
            )
            altered_entries = tuple(
                replace(entry, sha256="8" * 64) if entry.relative_path == target else entry
                for entry in healthy.manifest.entries
            )
            altered = replace(healthy, manifest=replace(healthy.manifest, entries=altered_entries))
        elif case == "manifest_assembly_mismatch":
            altered = replace(
                healthy,
                manifest=replace(healthy.manifest, game_assembly_sha256="8" * 64),
            )
        else:
            altered = replace(
                healthy,
                preloader_compatibility=replace(
                    healthy.preloader_compatibility, active_sha256="8" * 64
                ),
            )
        monkeypatch.setattr(passive, "status_install", lambda _root: altered)
    elif "replace_" in case:
        target = plugin_path if case.startswith("plugin") else config_path
        boundary = (
            "after_named_before" if case.endswith("after_named_before") else "before_named_after"
        )
        fired = False

        def replace_name(observed: str, path: Path) -> None:
            nonlocal fired
            if not fired and observed == boundary and path == target:
                fired = True
                original = target.with_name(target.name + ".original")
                target.rename(original)
                target.write_bytes(original.read_bytes())

        monkeypatch.setattr(passive, "_installed_hash_checkpoint", replace_name)
    elif case in {"hash_exact_bound", "hash_bound_plus_one"}:
        plugin_path.write_bytes(b"x" * (8 if case == "hash_exact_bound" else 9))
        if case == "hash_exact_bound":
            assert passive._hash_installed_file(plugin_path, 8) == sha256(b"x" * 8).hexdigest()
            return
        with pytest.raises(passive.PassiveProbeError, match="byte limit|bounded"):
            passive._hash_installed_file(plugin_path, 8)
        return
    else:
        original_close = passive.os.close
        original_read = passive.os.read
        close_failed = False

        def fail_close(descriptor: int) -> None:
            nonlocal close_failed
            if not close_failed:
                close_failed = True
                raise OSError("synthetic close failure")
            original_close(descriptor)

        monkeypatch.setattr(passive.os, "close", fail_close)
        if case == "close_failure_with_primary":
            primary = KeyboardInterrupt("synthetic read interruption")
            monkeypatch.setattr(passive.os, "read", lambda *_args: (_ for _ in ()).throw(primary))
            with pytest.raises(KeyboardInterrupt) as caught:
                passive._hash_installed_file(plugin_path, 64 * 1024 * 1024)
            assert caught.value is primary
            return
        with pytest.raises(OSError, match="synthetic close failure"):
            passive._hash_installed_file(plugin_path, 64 * 1024 * 1024)
        monkeypatch.setattr(passive.os, "read", original_read)
        return

    with pytest.raises(passive.PassiveProbeError):
        passive._capture_passive_snapshot(game)
```

- [ ] **Step 2: Run the installed-snapshot RED gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'passive_snapshot or snapshot_status_drift or snapshot_manifest_mismatch'
```

Expected: the old single-status capture accepts a race or manifest/observed disagreement.

- [ ] **Step 3: Implement stable descriptor hashing and double-status validation**

```python
def _installed_hash_checkpoint(_boundary: str, _path: Path) -> None:
    return None


def _hash_installed_file(path: Path, maximum: int) -> str:
    parent = oracle_boot._open_absolute_directory(path.parent, "installed file parent")
    descriptor = -1
    primary: BaseException | None = None
    try:
        named_before = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
        _installed_hash_checkpoint("after_named_before", path)
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent.fd,
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or not _same_save_metadata(named_before, before)
            or before.st_size > maximum
        ):
            raise PassiveProbeError(f"installed file is not a stable bounded regular file: {path}")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise PassiveProbeError(f"installed file exceeds byte limit: {path}")
            digest.update(chunk)
        after = os.fstat(descriptor)
        _installed_hash_checkpoint("before_named_after", path)
        named_after = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
        if (
            not _same_save_metadata(before, after)
            or not _same_save_metadata(named_after, after)
            or total != after.st_size
        ):
            raise PassiveProbeError(f"installed file changed while hashing: {path}")
        return digest.hexdigest()
    except BaseException as error:
        primary = error
        raise
    finally:
        close_primary: BaseException | None = None
        if descriptor >= 0:
            owned_descriptor = descriptor
            descriptor = -1
            try:
                os.close(owned_descriptor)
            except BaseException as error:
                close_primary = error
        try:
            parent.close()
        except BaseException as error:
            if close_primary is None:
                close_primary = error
            else:
                close_primary.add_note(f"installed file parent close also failed: {error}")
        if close_primary is not None:
            if primary is None:
                raise close_primary
            primary.add_note(f"installed file owner close also failed: {close_primary}")


def _capture_passive_snapshot(game_root: Path) -> PassiveInstallSnapshot:
    status_before = status_install(game_root)
    legacy = oracle_boot._capture_boot_snapshot(game_root)
    plugin_hash = _hash_installed_file(
        game_root / oracle_install.PLUGIN_RELATIVE_PATH,
        64 * 1024 * 1024,
    )
    config_hash = _hash_installed_file(
        game_root / oracle_install.CONFIG_RELATIVE_PATH,
        64 * 1024,
    )
    status_after = status_install(game_root)
    if status_before != status_after:
        raise PassiveProbeError("installer status changed during passive snapshot")
    status = status_after
    if legacy.installer_healthy != status.healthy:
        raise PassiveProbeError("legacy and passive installer health snapshots disagree")
    if legacy.compatibility_state != status.preloader_compatibility.state:
        raise PassiveProbeError("legacy and passive compatibility snapshots disagree")
    if status.manifest.game_assembly_sha256 != legacy.assembly_sha256:
        raise PassiveProbeError("manifest and observed assembly hashes disagree")
    if status.preloader_compatibility.active_sha256 != legacy.active_preloader_sha256:
        raise PassiveProbeError("status and observed active preloader hashes disagree")
    by_path = {entry.relative_path: entry for entry in status.manifest.entries}
    for relative_path, observed_hash in (
        (oracle_install.PLUGIN_RELATIVE_PATH, plugin_hash),
        (oracle_install.CONFIG_RELATIVE_PATH, config_hash),
    ):
        entry = by_path.get(relative_path)
        if entry is None or entry.kind != "file" or entry.sha256 != observed_hash:
            raise PassiveProbeError(
                f"manifest and observed installed hash disagree: {relative_path}"
            )
    return PassiveInstallSnapshot(
        legacy,
        plugin_hash,
        config_hash,
        status_before,
        status_after,
    )
```

- [ ] **Step 4: Run the installed-snapshot GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'passive_snapshot or snapshot_status_drift or snapshot_manifest_mismatch'
```

Expected: status and every manifest-vs-observed comparison must remain exact across the entire capture window.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit stable installed snapshots**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: capture stable passive install snapshots"
```

### Task 15C: Serialize complete passive evidence models

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces deterministic payload helpers for installer status, lifecycle snapshots, and trace summaries. Task 16 owns isolated, cleanup, secondary-error, proof, and top-level result serialization.

- [ ] **Step 1: Add exact nested-payload RED tests**

Add these five concrete serialization items:

```python
@pytest.mark.parametrize(
    "case",
    (
        "status_before_and_after",
        "complete_manifest",
        "complete_preloader_status",
        "malformed_trace_nulls",
        "terminal_error_trace_fields",
    ),
)
def test_passive_nested_payloads_preserve_every_declared_field(
    installed_game: tuple[Path, oracle_install.InstallStatus],
    case: str,
) -> None:
    game, status = installed_game
    legacy = oracle_boot._BootSnapshot(
        status.manifest.game_assembly_sha256,
        status.preloader_compatibility.active_sha256,
        status.healthy,
        status.preloader_compatibility.state,
        oracle_boot._AppSignature(0, "valid", ""),
    )
    snapshot = passive.PassiveInstallSnapshot(
        legacy,
        sha256((game / oracle_install.PLUGIN_RELATIVE_PATH).read_bytes()).hexdigest(),
        sha256((game / oracle_install.CONFIG_RELATIVE_PATH).read_bytes()).hexdigest(),
        status,
        status,
    )
    if case in {"status_before_and_after", "complete_manifest", "complete_preloader_status"}:
        payload = passive._passive_snapshot_payload(snapshot)
        if case == "status_before_and_after":
            assert payload["installer_status_before"] == payload["installer_status_after"]
            assert set(payload) == {
                "installer_status_before",
                "installer_status_after",
                "legacy",
                "observed_config_sha256",
                "observed_plugin_sha256",
            }
        elif case == "complete_manifest":
            assert payload["installer_status_after"]["manifest"] == {
                "entries": [
                    {
                        "kind": entry.kind,
                        "relative_path": entry.relative_path,
                        "sha256": entry.sha256,
                    }
                    for entry in status.manifest.entries
                ],
                "game_assembly_sha256": status.manifest.game_assembly_sha256,
                "runtime_archive_sha256": status.manifest.runtime_archive_sha256,
                "schema_version": status.manifest.schema_version,
            }
        else:
            compatibility = status.preloader_compatibility
            assert payload["installer_status_after"]["preloader_compatibility"] == {
                "active_sha256": compatibility.active_sha256,
                "issues": list(compatibility.issues),
                "official_sha256": compatibility.official_sha256,
                "patched_sha256": compatibility.patched_sha256,
                "state": compatibility.state,
            }
        return
    summary = passive.TraceSummary(
        path="/private/passive-trace.ndjson",
        parse_status=("malformed" if case == "malformed_trace_nulls" else "valid_error"),
        outcome=(None if case == "malformed_trace_nulls" else "error"),
        error_code=(None if case == "malformed_trace_nulls" else "settle_timeout"),
        record_count=(None if case == "malformed_trace_nulls" else 4),
        step_count=(None if case == "malformed_trace_nulls" else 1),
        sha256="7" * 64,
        size=17,
    )
    payload = passive._trace_summary_payload(summary)
    assert set(payload) == {
        "error_code", "outcome", "parse_status", "path", "record_count",
        "sha256", "size", "step_count",
    }
    assert payload["error_code"] == summary.error_code
    assert payload["record_count"] == summary.record_count
```

- [ ] **Step 2: Run serialization RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'nested_payloads'
```

Expected: complete deterministic serialization is absent.

- [ ] **Step 3: Add complete nested payload helpers**

```python
def _installer_status_payload(status: InstallStatus) -> dict[str, object]:
    compatibility = status.preloader_compatibility
    return {
        "changed": list(status.changed),
        "healthy": status.healthy,
        "manifest": {
            "entries": [
                {
                    "kind": entry.kind,
                    "relative_path": entry.relative_path,
                    "sha256": entry.sha256,
                }
                for entry in status.manifest.entries
            ],
            "game_assembly_sha256": status.manifest.game_assembly_sha256,
            "runtime_archive_sha256": status.manifest.runtime_archive_sha256,
            "schema_version": status.manifest.schema_version,
        },
        "missing": list(status.missing),
        "preloader_compatibility": {
            "active_sha256": compatibility.active_sha256,
            "issues": list(compatibility.issues),
            "official_sha256": compatibility.official_sha256,
            "patched_sha256": compatibility.patched_sha256,
            "state": compatibility.state,
        },
    }


def _passive_snapshot_payload(snapshot: PassiveInstallSnapshot) -> dict[str, object]:
    return {
        "installer_status_before": _installer_status_payload(
            snapshot.installer_status_before
        ),
        "installer_status_after": _installer_status_payload(
            snapshot.installer_status_after
        ),
        "legacy": oracle_boot._boot_snapshot_payload(snapshot.legacy),
        "observed_config_sha256": snapshot.observed_config_sha256,
        "observed_plugin_sha256": snapshot.observed_plugin_sha256,
    }


def _trace_summary_payload(summary: TraceSummary) -> dict[str, object]:
    return {
        "error_code": summary.error_code,
        "outcome": summary.outcome,
        "parse_status": summary.parse_status,
        "path": summary.path,
        "record_count": summary.record_count,
        "sha256": summary.sha256,
        "size": summary.size,
        "step_count": summary.step_count,
    }
```

- [ ] **Step 4: Run snapshot/result GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'nested_payloads'
```

Expected: every manifest/status field, observed plugin/config hash, nullable snapshot stage, and trace parse state serializes by field name.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the snapshot/result contract**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: freeze passive oracle result contract"
```

### Task 16: Publish `passive-probe.json` only after safe final evidence

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_passive_result_payload(result: PassiveProbeResult) -> dict[str, object]` with the exact top-level keys below, including the host-derived `macos_product_version` retained from preflight.
- Produces `_stage_passive_result(...) -> _StagedProbeJson` and `_commit_staged_passive_result(staged) -> None` through Task 6's generalized transaction.
- Canonical `passive-probe.json` is pretty two-space, sorted-key UTF-8 plus LF and is published last with mode `0600`.
- Staging/verification does not publish. Lifecycle owners close before commit; the staged transaction's duplicate directory handle is the sole owner allowed to remain for the exclusive rename.
- This task tests only exact result serialization, stage-without-publication, evidence-fsync-before-stage, the requested canonical name, and commit-after-stage. Task 6's complete generalized publication suite remains the sole coverage for existing-target, substitution, rename, fsync, close, and quarantine faults; Task 16 does not claim new passive-specific rows for those cases.

- [ ] **Step 1: Add exact field-set and JSON-last RED tests**

```python
@pytest.fixture
def passive_result(
    installed_game: tuple[Path, oracle_install.InstallStatus],
    passive_layout: passive.PassiveLayout,
) -> passive.PassiveProbeResult:
    game, status = installed_game
    legacy = oracle_boot._BootSnapshot(
        assembly_sha256="1" * 64,
        active_preloader_sha256="2" * 64,
        installer_healthy=True,
        compatibility_state="official",
        app_signature=oracle_boot._AppSignature(0, "valid", ""),
    )
    snapshot = passive.PassiveInstallSnapshot(
        legacy=legacy,
        observed_plugin_sha256=sha256(
            (game / oracle_install.PLUGIN_RELATIVE_PATH).read_bytes()
        ).hexdigest(),
        observed_config_sha256=sha256(
            (game / oracle_install.CONFIG_RELATIVE_PATH).read_bytes()
        ).hexdigest(),
        installer_status_before=status,
        installer_status_after=status,
    )
    save_proof = passive.fingerprint_save_tree(passive_layout.isolated_save_dir)
    trace = passive.TraceSummary(
        path=str(passive_layout.trace_path),
        parse_status="malformed",
        outcome=None,
        error_code=None,
        record_count=None,
        step_count=None,
        sha256=sha256(b"").hexdigest(),
        size=0,
    )
    return passive.PassiveProbeResult(
        success=False,
        started_at_utc="2026-07-31T19:09:50.319910Z",
        finished_at_utc="2026-07-31T19:10:50.319910Z",
        controller_pid=42,
        game_root=game,
        macos_product_version="26.6",
        launcher=game / "run_bepinex.sh",
        evidence_dir=passive_layout.evidence_dir,
        isolated_save_dir=passive_layout.isolated_save_dir,
        plugin_sha256=snapshot.observed_plugin_sha256,
        mode_off_config_sha256="4" * 64,
        passive_config_sha256=passive_layout.config_sha256,
        markers=(),
        issues=("synthetic failure",),
        secondary_errors=(),
        exit_code=17,
        run_id=None,
        cleanup=passive.PassiveCleanup(True, True, True, True, True, True),
        before=snapshot,
        patched=None,
        post_process=None,
        after=snapshot,
        before_logs=(),
        after_logs=(),
        ordinary_save_before=save_proof,
        ordinary_save_after=save_proof,
        ordinary_save_final=save_proof,
        isolated_save=passive.IsolatedSaveObservation((), True, (), 0, False),
        trace=trace,
        copied_logs=(),
        moved_logs=(),
        restore_recovery_dir=None,
    )


@pytest.fixture
def retained_evidence(
    passive_result: passive.PassiveProbeResult,
    passive_layout: passive.PassiveLayout,
) -> Iterator[oracle_boot._RetainedBootEvidence]:
    canonical = passive_result.game_root / "BepInEx" / "LogOutput.log"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_bytes(b"SSR oracle boot probe loaded\n")
    config_stat = os.stat(
        passive_layout.config_path.name,
        dir_fd=passive_layout.evidence_handle.fd,
        follow_symlinks=False,
    )
    specs = (
        oracle_boot._AuxiliaryEvidenceSpec(
            Path("passive.cfg"),
            "passive_config",
            True,
            64 * 1024,
            oracle_boot._stat_identity(config_stat),
            passive_layout.config_sha256,
        ),
        oracle_boot._AuxiliaryEvidenceSpec(
            Path("passive-trace.ndjson"),
            "passive_trace",
            False,
            128 * 1024 * 1024,
            None,
            None,
        ),
    )
    retained = oracle_boot._collect_boot_evidence_into(
        (),
        passive_result.game_root,
        passive_layout.evidence_dir,
        passive_layout.evidence_handle,
        expected_inventory=None,
        run_contract=None,
        observed_failures=(),
        auxiliary_specs=specs,
    )
    try:
        yield retained
    finally:
        retained.close()


EXPECTED_PASSIVE_RESULT_KEYS = {
    "after",
    "after_logs",
    "before",
    "before_logs",
    "cleanup",
    "controller_pid",
    "copied_logs",
    "evidence_dir",
    "exit_code",
    "finished_at_utc",
    "game_root",
    "isolated_save_dir",
    "isolated_save",
    "issues",
    "launcher",
    "macos_product_version",
    "markers",
    "mode_off_config_sha256",
    "moved_logs",
    "ordinary_save_after",
    "ordinary_save_before",
    "ordinary_save_final",
    "passive_config_sha256",
    "patched",
    "plugin_sha256",
    "post_process",
    "restore_recovery_dir",
    "run_id",
    "schema_version",
    "secondary_errors",
    "started_at_utc",
    "success",
    "trace",
}


def test_passive_result_payload_has_exact_schema(passive_result: passive.PassiveProbeResult) -> None:
    payload = passive._passive_result_payload(passive_result)
    assert set(payload) == EXPECTED_PASSIVE_RESULT_KEYS
    assert payload["schema_version"] == 1
    assert payload["macos_product_version"] == "26.6"
    assert payload["trace"]["parse_status"] in {"valid_success", "valid_error", "malformed"}
    assert payload["before"]["installer_status_before"] == payload["before"]["installer_status_after"]


def test_stage_and_commit_passive_result_uses_passive_name_and_commits_last(
    passive_result: passive.PassiveProbeResult,
    passive_layout: passive.PassiveLayout,
    retained_evidence: oracle_boot._RetainedBootEvidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    original_verify = oracle_boot._verify_and_sync_retained_evidence
    original_commit = oracle_boot._commit_staged_probe_json
    monkeypatch.setattr(
        oracle_boot,
        "_verify_and_sync_retained_evidence",
        lambda retained: (events.append("evidence:fsync"), original_verify(retained))[1],
    )
    monkeypatch.setattr(
        oracle_boot,
        "_commit_staged_probe_json",
        lambda staged: (events.append("json:commit"), original_commit(staged))[1],
    )
    staged = passive._stage_passive_result(
        passive_result, passive_layout, retained_evidence
    )
    assert events == ["evidence:fsync"]
    assert not (passive_layout.evidence_dir / "passive-probe.json").exists()
    passive._commit_staged_passive_result(staged)
    assert events == ["evidence:fsync", "json:commit"]
    assert (passive_layout.evidence_dir / "passive-probe.json").is_file()
    assert not (passive_layout.evidence_dir / "probe.json").exists()


@pytest.mark.parametrize(
    "case",
    (
        "patched", "post_process", "ordinary_save_after", "ordinary_save_final",
        "trace", "run_id", "exit_code", "copied_logs", "moved_logs",
        "restore_recovery_dir",
    ),
)
def test_passive_result_payload_serializes_each_nullable_or_path_boundary(
    passive_result: passive.PassiveProbeResult,
    case: str,
) -> None:
    if case in {"patched", "post_process"}:
        value: object = passive_result.before
    elif case in {"ordinary_save_after", "ordinary_save_final", "trace", "exit_code"}:
        value = None
    elif case == "run_id":
        value = "a" * 32
    elif case in {"copied_logs", "moved_logs"}:
        value = (Path(f"/{case}/one.log"),)
    else:
        value = Path("/private/recovery")
    changed = replace(passive_result, **{case: value})
    payload = passive._passive_result_payload(changed)
    if case in {"patched", "post_process"}:
        assert payload[case] == passive._passive_snapshot_payload(passive_result.before)
    elif case in {"copied_logs", "moved_logs"}:
        assert payload[case] == [str(value[0])]
    elif case == "restore_recovery_dir":
        assert payload[case] == str(value)
    else:
        assert payload[case] == value
```

- [ ] **Step 2: Run publication RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'passive_result_payload or stage_and_commit_passive_result'
```

Expected: result payload and publication functions are missing.

- [ ] **Step 3: Implement exact result serialization and JSON-last commit**

Add generic dataclass serialization only for the declared proof/inventory types:

```python
from dataclasses import asdict


def _proof_payload(proof: SaveTreeProof | None) -> dict[str, object] | None:
    return None if proof is None else asdict(proof)


def _passive_result_payload(result: PassiveProbeResult) -> dict[str, object]:
    return {
        "after": None if result.after is None else _passive_snapshot_payload(result.after),
        "after_logs": [oracle_boot._log_fingerprint_payload(item) for item in result.after_logs],
        "before": _passive_snapshot_payload(result.before),
        "before_logs": [oracle_boot._log_fingerprint_payload(item) for item in result.before_logs],
        "cleanup": asdict(result.cleanup),
        "controller_pid": result.controller_pid,
        "copied_logs": [str(path) for path in result.copied_logs],
        "evidence_dir": str(result.evidence_dir),
        "exit_code": result.exit_code,
        "finished_at_utc": result.finished_at_utc,
        "game_root": str(result.game_root),
        "isolated_save_dir": str(result.isolated_save_dir),
        "isolated_save": {
            "inventory": [asdict(item) for item in result.isolated_save.inventory],
            "issues": list(result.isolated_save.issues),
            "regular_bytes": result.isolated_save.regular_bytes,
            "safe": result.isolated_save.safe,
            "truncated": result.isolated_save.truncated,
        },
        "issues": list(result.issues),
        "launcher": str(result.launcher),
        "macos_product_version": result.macos_product_version,
        "markers": list(result.markers),
        "mode_off_config_sha256": result.mode_off_config_sha256,
        "moved_logs": [str(path) for path in result.moved_logs],
        "ordinary_save_after": _proof_payload(result.ordinary_save_after),
        "ordinary_save_before": _proof_payload(result.ordinary_save_before),
        "ordinary_save_final": _proof_payload(result.ordinary_save_final),
        "passive_config_sha256": result.passive_config_sha256,
        "patched": None if result.patched is None else _passive_snapshot_payload(result.patched),
        "plugin_sha256": result.plugin_sha256,
        "post_process": (
            None if result.post_process is None else _passive_snapshot_payload(result.post_process)
        ),
        "restore_recovery_dir": (
            None if result.restore_recovery_dir is None else str(result.restore_recovery_dir)
        ),
        "run_id": result.run_id,
        "schema_version": 1,
        "secondary_errors": [asdict(item) for item in result.secondary_errors],
        "started_at_utc": result.started_at_utc,
        "success": result.success,
        "trace": None if result.trace is None else _trace_summary_payload(result.trace),
    }


def _stage_passive_result(
    result: PassiveProbeResult,
    layout: PassiveLayout,
    retained_evidence: oracle_boot._RetainedBootEvidence,
) -> oracle_boot._StagedProbeJson:
    payload = _passive_result_payload(result)
    oracle_boot._verify_and_sync_retained_evidence(retained_evidence)
    staged = oracle_boot._stage_probe_json(
        layout.evidence_dir,
        payload,
        canonical_name="passive-probe.json",
        _directory_handle=layout.evidence_handle,
    )
    try:
        oracle_boot._verify_staged_probe_json(layout.evidence_dir, payload, staged)
        return staged
    except BaseException as primary:
        try:
            oracle_boot._close_staged_probe_json(staged)
        except BaseException as secondary:
            primary.add_note(f"secondary staged JSON close failure: {secondary}")
        raise


def _commit_staged_passive_result(staged: oracle_boot._StagedProbeJson) -> None:
    try:
        oracle_boot._commit_staged_probe_json(staged)
    except BaseException as primary:
        try:
            oracle_boot._close_staged_probe_json(staged)
        except BaseException as secondary:
            primary.add_note(f"secondary staged JSON close failure: {secondary}")
        raise
    oracle_boot._close_staged_probe_json(staged)
```

- [ ] **Step 4: Run publication GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'result_payload or publication or stage_and_commit_passive_result'
```

Expected: the exact passive schema/nullable boundaries pass, staging leaves the canonical name absent, retained evidence fsync precedes stage return, and the explicit commit publishes only `passive-probe.json`. Task 6's already-GREEN generalized transaction suite supplies the remaining publication-fault coverage.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the publication gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: publish passive oracle evidence last"
```

### Task 17A: Define the standalone preflight request/result contract

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces frozen `PassivePreflight` with exact fields below.
- Defines only the frozen request/result carrier with the exact Tahoe product version, every exact artifact, installed/log/process/save observation, launch environment, and the required literal timeout `300`. Task 17B adds readers and Task 17C adds the public preflight implementation.

- [ ] **Step 1: Add the no-mutation preflight RED test**

```python
from collections.abc import Callable
from types import SimpleNamespace

from ssr_env import oracle_compat


@pytest.fixture
def complete_preflight_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, object]:
    game = tmp_path / "game"
    game.mkdir()
    launcher = tmp_path / "run_bepinex.sh"
    launcher.write_bytes(b"#!/bin/sh\nexit 0\n")
    launcher.chmod(0o700)
    evidence_root = tmp_path / "data" / "oracle"
    evidence_root.mkdir(parents=True)
    mode_off = tmp_path / "mode-off.cfg"
    mode_off.write_bytes(b"[Oracle]\nMode = off\n")
    plugin = tmp_path / "plugin.dll"
    plugin_copy = tmp_path / "plugin-copy.dll"
    plugin.write_bytes(b"reviewed-plugin")
    plugin_copy.write_bytes(plugin.read_bytes())
    preloader = tmp_path / "preloader.dll"
    preloader.write_bytes(b"reviewed-preloader")
    provenance = tmp_path / "preloader-provenance.json"
    provenance.write_bytes(b'{"reviewed":true}\n')

    manifest = oracle_install.InstallManifest(
        1,
        passive.EXPECTED_ASSEMBLY_SHA256,
        "5" * 64,
        (),
    )
    status = oracle_install.InstallStatus(
        manifest,
        (),
        (),
        oracle_install.PreloaderCompatibilityStatus(
            "official", "6" * 64, "6" * 64, None, ()
        ),
    )
    legacy = oracle_boot._BootSnapshot(
        passive.EXPECTED_ASSEMBLY_SHA256,
        "6" * 64,
        True,
        "official",
        oracle_boot._AppSignature(0, "valid", ""),
    )
    snapshot = passive.PassiveInstallSnapshot(
        legacy,
        sha256(plugin.read_bytes()).hexdigest(),
        sha256(mode_off.read_bytes()).hexdigest(),
        status,
        status,
    )
    monkeypatch.setattr(passive, "_approved_evidence_root", lambda: evidence_root)
    monkeypatch.setattr(passive, "_require_ignored_evidence_root", lambda _root: None)
    monkeypatch.setattr(passive, "MODE_OFF_CONFIG_SHA256", sha256(mode_off.read_bytes()).hexdigest())
    monkeypatch.setattr(passive, "_capture_passive_snapshot", lambda _root: snapshot)
    monkeypatch.setattr(oracle_boot, "_preflight_issues", lambda *_args: ())
    monkeypatch.setattr(oracle_boot, "_capture_boot_log_inventory", lambda _root: oracle_boot._BootLogInventory(()))
    monkeypatch.setattr(passive, "_process_snapshot", lambda: passive._ProcessSnapshot((), 9101))

    def exact_sw_vers(
        command: tuple[str, str],
        **kwargs: object,
    ) -> SimpleNamespace:
        assert command == ("/usr/bin/sw_vers", "-productVersion")
        assert kwargs == {
            "capture_output": True,
            "check": False,
            "env": {**os.environ, "LC_ALL": "C"},
            "shell": False,
            "stdin": passive.subprocess.DEVNULL,
            "timeout": 5.0,
        }
        return SimpleNamespace(returncode=0, stdout=b"26.6\n", stderr=b"")

    monkeypatch.setattr(passive.subprocess, "run", exact_sw_vers)
    monkeypatch.setattr(oracle_compat, "load_trust", lambda _root: object())
    monkeypatch.setattr(
        oracle_compat,
        "load_provenance_bytes",
        lambda _payload, _trust, *, source: SimpleNamespace(
            patched_preloader_sha256=sha256(preloader.read_bytes()).hexdigest()
        ),
    )
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return {
        "game_root": game,
        "launcher": launcher,
        "mode_off_config": mode_off,
        "plugin": plugin,
        "plugin_verification_copy": plugin_copy,
        "expected_plugin_sha256": sha256(plugin.read_bytes()).hexdigest(),
        "preloader": preloader,
        "provenance": provenance,
        "evidence_root": evidence_root,
        "timeout_seconds": 300,
    }


@pytest.fixture
def install_preflight_fault(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str], None]:
    def apply(fault: str) -> None:
        if fault == "plugin_copy_mismatch":
            Path(complete_preflight_request["plugin_verification_copy"]).write_bytes(b"different")
        elif fault == "plugin_hash_mismatch":
            complete_preflight_request["expected_plugin_sha256"] = "0" * 64
        elif fault == "mode_off_hash_mismatch":
            monkeypatch.setattr(passive, "MODE_OFF_CONFIG_SHA256", "0" * 64)
        elif fault == "preloader_provenance_mismatch":
            monkeypatch.setattr(
                oracle_compat,
                "load_provenance_bytes",
                lambda _payload, _trust, *, source: SimpleNamespace(patched_preloader_sha256="0" * 64),
            )
        elif fault == "signature_issue":
            monkeypatch.setattr(oracle_boot, "_preflight_issues", lambda *_args: ("signature issue",))
        elif fault == "unhealthy_installer":
            healthy = passive._capture_passive_snapshot(Path(complete_preflight_request["game_root"]))
            unhealthy = replace(
                healthy,
                legacy=replace(healthy.legacy, installer_healthy=False),
                installer_status_before=replace(
                    healthy.installer_status_before,
                    missing=("plugin",),
                ),
                installer_status_after=replace(
                    healthy.installer_status_after,
                    missing=("plugin",),
                ),
            )
            monkeypatch.setattr(passive, "_capture_passive_snapshot", lambda _root: unhealthy)
        elif fault == "changed_log_inventory":
            changed = oracle_boot.LogFingerprint(
                Path(complete_preflight_request["game_root"]) / "BepInEx/LogOutput.log",
                "regular",
                1,
                1,
                1,
                "7" * 64,
            )
            monkeypatch.setattr(oracle_boot, "fingerprint_preloader_logs", lambda _root: (changed,))
        elif fault == "matching_process":
            launcher = str(complete_preflight_request["launcher"])
            row = passive.ProcessRow(
                9201,
                1,
                9201,
                os.getuid(),
                "Thu Jul 31 12:35:00 2026",
                launcher,
                (launcher,),
            )
            monkeypatch.setattr(passive, "_process_snapshot", lambda: passive._ProcessSnapshot((row,), 9202))
        elif fault == "unsafe_save":
            monkeypatch.setattr(
                passive,
                "fingerprint_save_tree",
                lambda _path: (_ for _ in ()).throw(passive.PassiveProbeError("unsafe save")),
            )
        elif fault == "unignored_evidence_root":
            monkeypatch.setattr(
                passive,
                "_require_ignored_evidence_root",
                lambda _root: (_ for _ in ()).throw(
                    passive.PassiveProbeError("evidence root is not ignored by git")
                ),
            )
        else:
            raise AssertionError(f"unknown synthetic preflight fault: {fault}")

    return apply


def _preflight_model_value(request: dict[str, object]) -> passive.PassivePreflight:
    evidence_root = Path(request["evidence_root"])
    observed = evidence_root.stat(follow_symlinks=False)
    ordinary_path = Path("/private/home/Library/Application Support/unity.increpare games/Sausage")
    ordinary = passive.SaveTreeProof(
        str(ordinary_path), "absent", None, (), str(ordinary_path), (), 0,
    )
    return passive.PassivePreflight(
        game_root=Path(request["game_root"]),
        macos_product_version="26.6",
        launcher=Path(request["launcher"]),
        evidence_root=evidence_root,
        evidence_root_identity=passive.PathIdentity(
            str(evidence_root), observed.st_dev, observed.st_ino,
            stat.S_IMODE(observed.st_mode),
        ),
        evidence_root_ignored=True,
        mode_off_config=Path(request["mode_off_config"]),
        mode_off_config_sha256=passive.MODE_OFF_CONFIG_SHA256,
        plugin=Path(request["plugin"]),
        plugin_verification_copy=Path(request["plugin_verification_copy"]),
        plugin_sha256=str(request["expected_plugin_sha256"]),
        preloader=Path(request["preloader"]),
        preloader_sha256="6" * 64,
        provenance=Path(request["provenance"]),
        provenance_sha256="7" * 64,
        snapshot=SimpleNamespace(),
        before_logs=(),
        log_inventory=oracle_boot._BootLogInventory(()),
        matching_processes=(),
        ordinary_save=ordinary,
        launch_environment=(("HOME", "/private/home"),),
        timeout_seconds=300,
    )


def test_standalone_preflight_model_retains_every_request_and_observation(
    complete_preflight_request: dict[str, object],
) -> None:
    result = _preflight_model_value(complete_preflight_request)
    assert result.game_root == complete_preflight_request["game_root"]
    assert result.launcher == complete_preflight_request["launcher"]
    assert result.plugin_sha256 == complete_preflight_request["expected_plugin_sha256"]
    assert result.evidence_root_ignored is True
    assert result.matching_processes == ()


def test_preflight_model_has_the_exact_frozen_contract() -> None:
    from dataclasses import fields

    assert tuple(item.name for item in fields(passive.PassivePreflight)) == (
        "game_root", "macos_product_version", "launcher", "evidence_root", "evidence_root_identity",
        "evidence_root_ignored", "mode_off_config", "mode_off_config_sha256",
        "plugin", "plugin_verification_copy", "plugin_sha256", "preloader",
        "preloader_sha256", "provenance", "provenance_sha256", "snapshot",
        "before_logs", "log_inventory", "matching_processes", "ordinary_save",
        "launch_environment", "timeout_seconds",
    )


def test_preflight_request_contract_retains_literal_timeout_and_environment(
    complete_preflight_request: dict[str, object],
) -> None:
    observed = _preflight_model_value(complete_preflight_request)
    assert observed.macos_product_version == "26.6"
    assert observed.timeout_seconds == 300
    assert isinstance(observed.launch_environment, tuple)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in observed.launch_environment)
    assert not hasattr(observed, "close")
```

- [ ] **Step 2: Run standalone-preflight RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'standalone_preflight or preflight_model or preflight_request_contract'
```

Expected: `PassivePreflight` is missing. No test in this task calls `preflight_passive_probe`.

- [ ] **Step 3: Implement the exact request/result model only**

Add imports, constants, and model:

```python
from dataclasses import replace
from ssr_env import oracle_compat


MODE_OFF_CONFIG_SHA256 = "cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d"
EXPECTED_ASSEMBLY_SHA256 = "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564"
EXPECTED_MACOS_PRODUCT_VERSION = "26.6"


@dataclass(frozen=True, slots=True)
class PassivePreflight:
    game_root: Path
    macos_product_version: str
    launcher: Path
    evidence_root: Path
    evidence_root_identity: PathIdentity
    evidence_root_ignored: bool
    mode_off_config: Path
    mode_off_config_sha256: str
    plugin: Path
    plugin_verification_copy: Path
    plugin_sha256: str
    preloader: Path
    preloader_sha256: str
    provenance: Path
    provenance_sha256: str
    snapshot: PassiveInstallSnapshot
    before_logs: tuple[oracle_boot.LogFingerprint, ...]
    log_inventory: oracle_boot._BootLogInventory
    matching_processes: tuple[ProcessRow, ...]
    ordinary_save: SaveTreeProof
    launch_environment: tuple[tuple[str, str], ...]
    timeout_seconds: int
```

- [ ] **Step 4: Run the preflight-contract GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'standalone_preflight or preflight_model or preflight_request_contract'
```

Expected: the frozen model carries every observation and has no lifecycle owner or mutation method.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the preflight contract**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: define passive preflight contract"
```

### Task 17B: Authenticate artifacts and the ignored evidence root read-only

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `src/ssr_env/oracle_compat.py`
- Modify: `tests/test_oracle_passive_probe.py`
- Modify: `tests/test_oracle_compat.py`

**Interfaces:**
- Produces `_read_artifact` with descriptor/named before/after agreement and `_require_ignored_evidence_root` with a non-mutating Git query.
- Refactors `oracle_compat.load_provenance` through `load_provenance_bytes(payload: bytes, trust: CompatTrust, *, source: str) -> BuildProvenance`; the path wrapper opens once and delegates, while passive preflight parses only the bytes already authenticated by `_read_artifact`.

- [ ] **Step 1: Add artifact/root substitution and bound RED tests**

Add these twenty-five collected items: the twenty passive artifact/root rows below plus five task-local compatibility rows (byte-loader parity/no-I/O, single-read path-wrapper delegation, preserved path-read error translation, and two source-bearing decoder failures). `_artifact_checkpoint` is a no-op seam called at `after_named_before` and `before_named_after` by the implementation below. Also add one provenance-name substitution row to Task 17C: replace the provenance pathname after `_read_artifact` returns and prove preflight still parses the retained reviewed bytes (or refuses) and never calls `load_provenance(path, ...)`:

```python
@pytest.mark.parametrize(
    ("scope", "case"),
    (
        ("artifact", "mode_off_exact_bound"),
        ("artifact", "plugin_exact_bound"),
        ("artifact", "preloader_exact_bound"),
        ("artifact", "provenance_exact_bound"),
        ("artifact", "bound_plus_one"),
        ("artifact", "symlink"),
        ("artifact", "fifo"),
        ("artifact", "directory"),
        ("artifact", "replace_after_named_before"),
        ("artifact", "replace_before_named_after"),
        ("artifact", "short_read"),
        ("artifact", "close_failure"),
        ("root", "ignored"),
        ("root", "not_ignored"),
        ("root", "git_failure"),
        ("root", "nonabsolute"),
        ("root", "nul"),
        ("root", "symlink_component"),
        ("root", "named_identity_drift"),
        ("root", "no_allocation"),
    ),
)
def test_preflight_artifact_and_evidence_root_are_stable_and_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scope: str,
    case: str,
) -> None:
    if scope == "artifact":
        path = tmp_path / "artifact.bin"
        path.write_bytes(b"12345678")
        if case.endswith("exact_bound"):
            payload, digest = passive._read_artifact(path, case, 8)
            assert payload == b"12345678"
            assert digest == sha256(payload).hexdigest()
            return
        if case == "bound_plus_one":
            path.write_bytes(b"123456789")
        elif case == "symlink":
            target = tmp_path / "target.bin"
            path.rename(target)
            path.symlink_to(target)
        elif case == "fifo":
            path.unlink()
            os.mkfifo(path)
        elif case == "directory":
            path.unlink()
            path.mkdir()
        elif case.startswith("replace_"):
            boundary = case.removeprefix("replace_")
            fired = False

            def substitute(observed: str, target: Path) -> None:
                nonlocal fired
                if not fired and observed == boundary and target == path:
                    fired = True
                    parked = path.with_suffix(".original")
                    path.rename(parked)
                    path.write_bytes(parked.read_bytes())

            monkeypatch.setattr(passive, "_artifact_checkpoint", substitute)
        elif case == "short_read":
            monkeypatch.setattr(passive.os, "read", lambda *_args: b"")
        elif case == "close_failure":
            original_close = passive.os.close
            failed = False

            def fail_once(descriptor: int) -> None:
                nonlocal failed
                if not failed:
                    failed = True
                    raise OSError("synthetic artifact close failure")
                original_close(descriptor)

            monkeypatch.setattr(passive.os, "close", fail_once)
            with pytest.raises(OSError, match="artifact close failure"):
                passive._read_artifact(path, case, 8)
            return
        with pytest.raises((passive.PassiveProbeError, OSError)):
            passive._read_artifact(path, case, 8)
        return

    root = tmp_path / "data" / "oracle"
    root.mkdir(parents=True)
    if case in {"ignored", "not_ignored", "git_failure", "no_allocation"}:
        returncode = {"ignored": 0, "not_ignored": 1, "git_failure": 128, "no_allocation": 0}[case]
        monkeypatch.setattr(
            passive.subprocess,
            "run",
            lambda *_args, **_kwargs: SimpleNamespace(returncode=returncode, stderr=b"fatal"),
        )
        forbidden: list[Path] = []
        monkeypatch.setattr(
            passive,
            "_allocate_passive_layout",
            lambda path: forbidden.append(path),
            raising=False,
        )
        if returncode == 0:
            assert passive._require_ignored_evidence_root(root) is None
            assert forbidden == []
        else:
            with pytest.raises(passive.PassiveProbeError, match="not ignored"):
                passive._require_ignored_evidence_root(root)
        return
    if case == "nonabsolute":
        with pytest.raises(oracle_boot.BootProbeError):
            oracle_boot._open_absolute_directory(Path("data/oracle"), "evidence root")
        return
    if case == "nul":
        with pytest.raises((ValueError, oracle_boot.BootProbeError)):
            oracle_boot._open_absolute_directory(Path("/tmp/bad\x00root"), "evidence root")
        return
    if case == "symlink_component":
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)
        with pytest.raises(oracle_boot.BootProbeError):
            oracle_boot._open_absolute_directory(link, "evidence root")
        return
    handle = oracle_boot._open_absolute_directory(root, "evidence root")
    try:
        original = root.with_name("oracle-original")
        root.rename(original)
        root.mkdir()
        assert oracle_boot._stat_identity(os.fstat(handle.fd)) != oracle_boot._stat_identity(
            os.stat(root, follow_symlinks=False)
        )
    finally:
        handle.close()
```

Add these literal rows to `tests/test_oracle_compat.py`. They own the new byte API's RED gate in the same task that implements it:

```python
def test_load_provenance_bytes_matches_path_loader_without_filesystem_io(
    committed_compat_repo: Path,
    valid_provenance: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trust = load_trust(committed_compat_repo)
    payload = valid_provenance.read_bytes()
    expected = load_provenance(valid_provenance, trust)

    def forbidden_read(_path: Path) -> bytes:
        raise AssertionError("byte provenance loader performed pathname I/O")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    assert oracle_compat.load_provenance_bytes(
        payload,
        trust,
        source="retained://reviewed-provenance",
    ) == expected


def test_load_provenance_path_wrapper_reads_once_and_delegates_retained_bytes(
    committed_compat_repo: Path,
    valid_provenance: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trust = load_trust(committed_compat_repo)
    payload = valid_provenance.read_bytes()
    expected = load_provenance(valid_provenance, trust)
    original_read = Path.read_bytes
    reads = 0
    delegated: list[tuple[bytes, object, str]] = []

    def read_once(path: Path) -> bytes:
        nonlocal reads
        if path == valid_provenance:
            reads += 1
            if reads > 1:
                raise AssertionError("provenance path reopened")
        return original_read(path)

    def retained_loader(
        observed_payload: bytes,
        observed_trust: object,
        *,
        source: str,
    ) -> oracle_compat.BuildProvenance:
        delegated.append((observed_payload, observed_trust, source))
        return expected

    monkeypatch.setattr(Path, "read_bytes", read_once)
    monkeypatch.setattr(oracle_compat, "load_provenance_bytes", retained_loader)
    assert oracle_compat.load_provenance(valid_provenance, trust) == expected
    assert reads == 1
    assert delegated == [(payload, trust, str(valid_provenance))]


def test_load_provenance_path_wrapper_preserves_read_error_translation(
    committed_compat_repo: Path,
    tmp_path: Path,
) -> None:
    trust = load_trust(committed_compat_repo)
    missing = tmp_path / "missing-provenance.json"
    with pytest.raises(CompatError, match="provenance JSON cannot be read"):
        oracle_compat.load_provenance(missing, trust)


@pytest.mark.parametrize(
    ("payload", "message"),
    (
        (b"{", "cannot be read"),
        (b'{"schema_version":1}', "not canonical"),
    ),
)
def test_load_provenance_bytes_reports_the_retained_source(
    committed_compat_repo: Path,
    payload: bytes,
    message: str,
) -> None:
    trust = load_trust(committed_compat_repo)
    source = "retained://reviewed-provenance"
    with pytest.raises(CompatError, match=message) as caught:
        oracle_compat.load_provenance_bytes(payload, trust, source=source)
    assert source in str(caught.value)
```

- [ ] **Step 2: Run artifact/root RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'preflight_artifact_and_evidence_root'
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_compat.py \
  -k 'load_provenance_bytes or load_provenance_path_wrapper'
```

Expected: one artifact/root authentication boundary or provenance byte/path-wrapper contract is absent; the compatibility command selects all five Task-17B compatibility registrations.

- [ ] **Step 3: Implement stable artifact/root readers and byte-authenticated provenance parsing**

In `oracle_compat.py`, replace the existing path-only provenance loader with this exact byte decoder, complete validation body, and single-read path wrapper:

```python
def _decode_canonical_bytes(
    payload: bytes,
    label: str,
    *,
    source: str,
) -> object:
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatError(
            f"{label} JSON cannot be read from {source}: {exc}"
        ) from exc
    if payload != canonical_json(decoded):
        raise CompatError(f"{label} JSON from {source} is not canonical")
    return decoded


def load_provenance_bytes(
    payload: bytes,
    trust: CompatTrust,
    *,
    source: str,
) -> BuildProvenance:
    try:
        values = _exact_mapping(
            _decode_canonical_bytes(
                payload,
                "provenance",
                source=source,
            ),
            _PROVENANCE_KEYS,
            "provenance",
        )
        version = _integer(values["schema_version"], "provenance schema_version")
        if version != 1:
            raise CompatError("provenance schema_version must be 1")
        provenance = BuildProvenance(
            schema_version=version,
            source_commit=_match(
                values["source_commit"], _LOWER_COMMIT, "source commit"
            ),
            patch_sha256=_match(
                values["patch_sha256"], _LOWER_SHA256, "patch hash"
            ),
            toolchain_lock_sha256=_match(
                values["toolchain_lock_sha256"], _LOWER_SHA256, "toolchain hash"
            ),
            dotnet_sdk_version=_string(
                values["dotnet_sdk_version"], "SDK version"
            ),
            dependency_lock_sha256=_match(
                values["dependency_lock_sha256"], _LOWER_SHA256, "dependency hash"
            ),
            build_target=_relative_path(values["build_target"], "build target"),
            official_preloader_sha256=_match(
                values["official_preloader_sha256"],
                _LOWER_SHA256,
                "official preloader hash",
            ),
            patched_preloader_sha256=_match(
                values["patched_preloader_sha256"],
                _LOWER_SHA256,
                "patched preloader hash",
            ),
        )
        if (
            provenance.patch_sha256 != trust.patch_sha256
            or provenance.toolchain_lock_sha256 != trust.toolchain_sha256
            or provenance.dependency_lock_sha256 != trust.dependencies_sha256
        ):
            raise CompatError("provenance hashes do not match trust")
        if provenance.build_target != _BUILD_TARGET:
            raise CompatError("provenance build target is not exact")
        if provenance.source_commit != _SOURCE_COMMIT:
            raise CompatError("provenance source commit is not exact")
        if provenance.dotnet_sdk_version != _DOTNET_SDK_VERSION:
            raise CompatError("provenance SDK version is not exact")
        if provenance.official_preloader_sha256 != _OFFICIAL_PRELOADER_SHA256:
            raise CompatError("provenance official preloader hash is not exact")
        if (
            provenance.patched_preloader_sha256
            != EXPECTED_PATCHED_PRELOADER_SHA256
        ):
            raise CompatError("provenance patched preloader hash is not exact")
        return provenance
    except CompatError as exc:
        message = str(exc)
        if "provenance" not in message:
            message = f"provenance is invalid: {message}"
        if source not in message:
            message = f"{message} (source: {source})"
        raise CompatError(message) from exc


def load_provenance(path: Path, trust: CompatTrust) -> BuildProvenance:
    try:
        payload = Path(path).read_bytes()
    except OSError as exc:
        raise CompatError(
            f"provenance JSON cannot be read from {path}: {exc}"
        ) from exc
    return load_provenance_bytes(payload, trust, source=str(path))
```

```python
def _artifact_checkpoint(_boundary: str, _path: Path) -> None:
    return None


def _read_artifact(path: Path, label: str, maximum: int) -> tuple[bytes, str]:
    parent = oracle_boot._open_absolute_directory(path.parent, f"{label} parent")
    descriptor = -1
    primary: BaseException | None = None
    try:
        named_before = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
        _artifact_checkpoint("after_named_before", path)
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent.fd,
        )
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or not _same_save_metadata(named_before, before)
            or before.st_size > maximum
        ):
            raise PassiveProbeError(f"{label} is not a stable bounded regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise PassiveProbeError(f"{label} exceeds byte limit")
            chunks.append(chunk)
        after = os.fstat(descriptor)
        _artifact_checkpoint("before_named_after", path)
        named_after = os.stat(path.name, dir_fd=parent.fd, follow_symlinks=False)
        if (
            not _same_save_metadata(before, after)
            or not _same_save_metadata(named_after, after)
            or total != after.st_size
        ):
            raise PassiveProbeError(f"{label} changed while reading")
        payload = b"".join(chunks)
        return payload, hashlib.sha256(payload).hexdigest()
    except BaseException as error:
        primary = error
        raise
    finally:
        close_primary: BaseException | None = None
        if descriptor >= 0:
            owned_descriptor = descriptor
            descriptor = -1
            try:
                os.close(owned_descriptor)
            except BaseException as error:
                close_primary = error
        try:
            parent.close()
        except BaseException as error:
            if close_primary is None:
                close_primary = error
            else:
                close_primary.add_note(f"artifact parent close also failed: {error}")
        if close_primary is not None:
            if primary is None:
                raise close_primary
            primary.add_note(f"artifact owner close also failed: {close_primary}")


def _require_ignored_evidence_root(evidence_root: Path) -> None:
    completed = subprocess.run(
        ("git", "check-ignore", "--quiet", str(evidence_root)),
        cwd=Path(__file__).resolve(strict=True).parents[2],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise PassiveProbeError("evidence root is not ignored by git")
```

- [ ] **Step 4: Run artifact/root GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'preflight_artifact_and_evidence_root'
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_compat.py
```

Expected: exact bytes, identities, bounds, and ignored-root checks pass without mutation; the complete compatibility suite proves byte-loader parity, source-bearing errors, one-read wrapper delegation, and unchanged validation semantics.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit read-only artifact authentication**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py src/ssr_env/oracle_compat.py \
  tests/test_oracle_passive_probe.py tests/test_oracle_compat.py
git commit -m "feat: authenticate passive preflight artifacts"
```

### Task 17C: Execute every standalone preflight check without mutation

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `preflight_passive_probe(...) -> PassivePreflight` with the same ten required request parameters as `run_passive_probe`.
- Observes exact macOS product version `26.6` through absolute `/usr/bin/sw_vers -productVersion` before any mutable lifecycle resource can become reachable.
- Performs no private-leaf allocation, installer call, config write, evidence publication, or launcher acquisition.

- [ ] **Step 1: Add complete rejection, retained-provenance, and root-identity RED matrices**

Add the exact twenty-one-item rejection matrix, the two-row approved-root descriptor/name boundary matrix, the retained-provenance pathname-substitution row promised by Task 17B, and the root-close-primary row, for twenty-five Task-17C registrations. The first ten rejection rows consume the complete fault installer defined in Task 17A; the remaining rejection rows construct their boundary state directly. The single `timeout_invalid` registration independently invokes both `299` and Boolean `True`; the freed matrix row owns the closed Tahoe reader/refusal gate. Every new host/identity/source row proves no layout allocation or launcher acquisition becomes reachable:

```python
@pytest.mark.parametrize(
    ("fault", "message"),
    (
        ("plugin_copy_mismatch", "plugin copy mismatch"),
        ("plugin_hash_mismatch", "plugin hash mismatch"),
        ("mode_off_hash_mismatch", "Mode-off config hash mismatch"),
        ("preloader_provenance_mismatch", "preloader provenance mismatch"),
        ("signature_issue", "signature issue"),
        ("unhealthy_installer", "unhealthy installer"),
        ("changed_log_inventory", "changed log inventory"),
        ("matching_process", "matching process"),
        ("unsafe_save", "unsafe save"),
        ("unignored_evidence_root", "evidence root is not ignored"),
        ("timeout_invalid", "timeout must equal 300"),
        ("timeout_missing", "missing"),
        ("macos_version_invalid", "macOS product version"),
        ("home_missing", "HOME"),
        ("home_relative", "HOME"),
        ("home_nul", "ordinary save path"),
        ("second_probe", "matching process"),
        ("ordinary_symlink", "unsupported save entry|not a directory"),
        ("ordinary_fifo", "unsupported save entry|not a directory"),
        ("ordinary_bound", "4096 descendants"),
        ("invalid_mode_off_utf8", "strict UTF-8"),
    ),
)
def test_standalone_preflight_rejects_each_complete_check_without_mutation(
    complete_preflight_request: dict[str, object],
    install_preflight_fault: Callable[[str], None],
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
    message: str,
) -> None:
    request = dict(complete_preflight_request)
    if fault in {
        "plugin_copy_mismatch",
        "plugin_hash_mismatch",
        "mode_off_hash_mismatch",
        "preloader_provenance_mismatch",
        "signature_issue",
        "unhealthy_installer",
        "changed_log_inventory",
        "matching_process",
        "unsafe_save",
        "unignored_evidence_root",
    }:
        install_preflight_fault(fault)
    elif fault == "timeout_invalid":
        pass
    elif fault == "timeout_missing":
        request.pop("timeout_seconds")
        with pytest.raises(TypeError, match=message):
            passive.preflight_passive_probe(**request)
        return
    elif fault == "macos_version_invalid":
        pass
    elif fault == "home_missing":
        environment = dict(os.environ)
        environment.pop("HOME", None)
        monkeypatch.setattr(passive.os, "environ", environment)
    elif fault == "home_relative":
        environment = dict(os.environ)
        environment["HOME"] = "relative/home"
        monkeypatch.setattr(passive.os, "environ", environment)
    elif fault == "home_nul":
        environment = dict(os.environ)
        environment["HOME"] = "/tmp/bad\x00home"
        monkeypatch.setattr(passive.os, "environ", environment)
    elif fault == "second_probe":
        probe = Path(__file__).resolve().parents[1] / "tools/oracle_passive_probe.py"
        game = Path(request["game_root"])
        row = passive.ProcessRow(
            9331,
            1,
            9331,
            os.getuid(),
            "Thu Jul 31 12:33:00 2026",
            "/usr/bin/python3",
            ("python3", str(probe), "--game-root", str(game)),
        )
        monkeypatch.setattr(
            passive,
            "_process_snapshot",
            lambda: passive._ProcessSnapshot((row,), 9332),
        )
    elif fault.startswith("ordinary_"):
        home = Path(os.environ["HOME"])
        target = home / "Library/Application Support/unity.increpare games/Sausage"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(exist_ok=True)
        unsafe = target / "unsafe"
        if fault == "ordinary_symlink":
            unsafe.symlink_to(target)
        elif fault == "ordinary_fifo":
            os.mkfifo(unsafe)
        else:
            monkeypatch.setattr(passive, "MAX_SAVE_ENTRIES", 0)
            unsafe.write_bytes(b"")
    elif fault == "invalid_mode_off_utf8":
        Path(request["mode_off_config"]).write_bytes(b"\xff")
    else:
        raise AssertionError(f"unhandled preflight fault: {fault}")

    forbidden: list[str] = []
    monkeypatch.setattr(
        passive,
        "_allocate_passive_layout",
        lambda _root: forbidden.append("allocate"),
    )
    monkeypatch.setattr(
        passive,
        "_acquire_launcher",
        lambda _preflight: forbidden.append("launch"),
        raising=False,
    )
    if fault == "timeout_invalid":
        for invalid_timeout in (299, True):
            request["timeout_seconds"] = invalid_timeout
            with pytest.raises(passive.PassiveProbeError, match=message):
                passive.preflight_passive_probe(**request)
        assert forbidden == []
        return
    if fault == "macos_version_invalid":
        version_failures: tuple[tuple[object, str], ...] = (
            (SimpleNamespace(returncode=0, stdout=b"26.5\n", stderr=b""), "requires macOS Tahoe 26.6"),
            (SimpleNamespace(returncode=0, stdout=b"26.6", stderr=b""), "requires macOS Tahoe 26.6"),
            (SimpleNamespace(returncode=1, stdout=b"", stderr=b"failed\n"), "could not read macOS product version"),
            (OSError("sw_vers missing"), "could not read macOS product version"),
            (
                passive.subprocess.TimeoutExpired(
                    cmd=("/usr/bin/sw_vers", "-productVersion"),
                    timeout=5.0,
                ),
                "could not read macOS product version",
            ),
        )
        for outcome, expected_message in version_failures:
            def invalid_sw_vers(
                command: tuple[str, str],
                **kwargs: object,
            ) -> SimpleNamespace:
                assert command == ("/usr/bin/sw_vers", "-productVersion")
                assert kwargs == {
                    "capture_output": True,
                    "check": False,
                    "env": {**os.environ, "LC_ALL": "C"},
                    "shell": False,
                    "stdin": passive.subprocess.DEVNULL,
                    "timeout": 5.0,
                }
                if isinstance(outcome, BaseException):
                    raise outcome
                return outcome

            monkeypatch.setattr(passive.subprocess, "run", invalid_sw_vers)
            with pytest.raises(passive.PassiveProbeError, match=expected_message):
                passive.preflight_passive_probe(**request)
        assert forbidden == []
        return
    with pytest.raises(passive.PassiveProbeError, match=message):
        passive.preflight_passive_probe(**request)
    assert forbidden == []


@pytest.mark.parametrize("boundary", ("after_named_before", "before_named_after"))
def test_preflight_rejects_approved_root_name_substitution_at_each_boundary(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    evidence_root = Path(complete_preflight_request["evidence_root"])
    held = evidence_root.with_name(evidence_root.name + "-held")
    fired = False
    forbidden: list[str] = []

    def checkpoint(observed: str, path: Path) -> None:
        nonlocal fired
        if not fired and observed == boundary and path == evidence_root:
            fired = True
            evidence_root.rename(held)
            evidence_root.mkdir(mode=0o700)

    monkeypatch.setattr(passive, "_preflight_evidence_root_checkpoint", checkpoint)
    monkeypatch.setattr(
        passive,
        "_allocate_passive_layout",
        lambda _root: forbidden.append("allocate"),
    )
    monkeypatch.setattr(
        passive,
        "_acquire_launcher",
        lambda _preflight: forbidden.append("launch"),
        raising=False,
    )
    with pytest.raises(passive.PassiveProbeError, match="root identity changed"):
        passive.preflight_passive_probe(**complete_preflight_request)
    assert fired is True
    assert forbidden == []


def test_preflight_parses_retained_provenance_after_name_substitution(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provenance = Path(complete_preflight_request["provenance"])
    retained_payload = provenance.read_bytes()
    original_read = passive._read_artifact
    original_decode = oracle_compat.load_provenance_bytes
    decoded: list[tuple[bytes, object, str]] = []
    forbidden: list[str] = []
    fired = False

    def read_then_replace(
        path: Path,
        label: str,
        maximum: int,
    ) -> tuple[bytes, str]:
        nonlocal fired
        payload, digest = original_read(path, label, maximum)
        if path == provenance:
            assert fired is False
            fired = True
            parked = provenance.with_suffix(".reviewed")
            provenance.rename(parked)
            provenance.write_bytes(b"{}\n")
        return payload, digest

    def decode_retained(
        payload: bytes,
        trust: object,
        *,
        source: str,
    ) -> object:
        decoded.append((payload, trust, source))
        return original_decode(payload, trust, source=source)

    monkeypatch.setattr(passive, "_read_artifact", read_then_replace)
    monkeypatch.setattr(oracle_compat, "load_provenance_bytes", decode_retained)
    monkeypatch.setattr(
        oracle_compat,
        "load_provenance",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("preflight reopened provenance by pathname")
        ),
    )
    monkeypatch.setattr(
        passive,
        "_allocate_passive_layout",
        lambda _root: forbidden.append("allocate"),
    )
    monkeypatch.setattr(
        passive,
        "_acquire_launcher",
        lambda _preflight: forbidden.append("launch"),
        raising=False,
    )
    result = passive.preflight_passive_probe(**complete_preflight_request)
    assert fired is True
    assert provenance.read_bytes() != retained_payload
    assert len(decoded) == 1
    assert decoded[0][0] == retained_payload
    assert decoded[0][2] == str(provenance)
    assert result.provenance_sha256 == sha256(retained_payload).hexdigest()
    assert forbidden == []


def test_preflight_preserves_identity_primary_when_evidence_root_close_fails(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence_root = Path(complete_preflight_request["evidence_root"])
    primary = KeyboardInterrupt("identity interrupted")
    secondary = OSError("evidence-root close failed")
    original_open = oracle_boot._open_absolute_directory
    close_calls = 0

    class FaultingRootHandle:
        def __init__(self) -> None:
            self.fd = os.open(evidence_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

        def close(self) -> None:
            nonlocal close_calls
            close_calls += 1
            descriptor = self.fd
            self.fd = -1
            os.close(descriptor)
            raise secondary

    def open_directory(path: Path, description: str):
        if path == evidence_root and description == "approved evidence root":
            return FaultingRootHandle()
        return original_open(path, description)

    original_identity = passive._identity

    def identity(path: Path, observed: os.stat_result):
        if path == evidence_root:
            raise primary
        return original_identity(path, observed)

    monkeypatch.setattr(oracle_boot, "_open_absolute_directory", open_directory)
    monkeypatch.setattr(passive, "_identity", identity)
    with pytest.raises(KeyboardInterrupt) as caught:
        passive.preflight_passive_probe(**complete_preflight_request)
    assert caught.value is primary
    assert close_calls == 1
    assert any(
        "secondary approved evidence root close failure" in note
        and "evidence-root close failed" in note
        for note in primary.__notes__
    )
```

- [ ] **Step 2: Run complete preflight RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'preflight'
```

Expected: the complete public preflight or one no-mutation/rejection row is absent; the selector includes all twenty-five Task-17C registrations.

- [ ] **Step 3: Implement the complete public preflight**

```python
def _macos_product_version() -> str:
    try:
        completed = subprocess.run(
            ("/usr/bin/sw_vers", "-productVersion"),
            capture_output=True,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
            shell=False,
            stdin=subprocess.DEVNULL,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise PassiveProbeError("could not read macOS product version") from error
    if completed.returncode != 0 or completed.stderr != b"":
        raise PassiveProbeError("could not read macOS product version")
    if completed.stdout != b"26.6\n":
        raise PassiveProbeError("preflight requires macOS Tahoe 26.6")
    return EXPECTED_MACOS_PRODUCT_VERSION


def _preflight_evidence_root_checkpoint(_boundary: str, _path: Path) -> None:
    return None


def preflight_passive_probe(
    game_root: Path,
    launcher: Path,
    mode_off_config: Path,
    plugin: Path,
    plugin_verification_copy: Path,
    expected_plugin_sha256: str,
    preloader: Path,
    provenance: Path,
    evidence_root: Path,
    timeout_seconds: int,
) -> PassivePreflight:
    path_values = (
        game_root,
        launcher,
        mode_off_config,
        plugin,
        plugin_verification_copy,
        preloader,
        provenance,
        evidence_root,
    )
    if any(not isinstance(path, Path) or not path.is_absolute() for path in path_values):
        raise PassiveProbeError("every preflight path must be an absolute Path")
    if timeout_seconds != 300 or isinstance(timeout_seconds, bool):
        raise PassiveProbeError("timeout must equal 300")
    if re.fullmatch(r"[0-9a-f]{64}", expected_plugin_sha256) is None:
        raise PassiveProbeError("expected plugin SHA-256 must be lowercase 64-hex")

    macos_product_version = _macos_product_version()

    game = oracle_boot._validate_directory(game_root, "game root")
    launcher_file = oracle_boot._validate_regular_file(launcher, "launcher", executable=True)
    approved_root = _approved_evidence_root()
    if evidence_root != approved_root:
        raise PassiveProbeError("evidence root is not the approved evidence root")
    root_handle = oracle_boot._open_absolute_directory(evidence_root, "approved evidence root")
    root_primary: BaseException | None = None
    try:
        root_named_before = os.stat(evidence_root, follow_symlinks=False)
        _preflight_evidence_root_checkpoint("after_named_before", evidence_root)
        root_descriptor = os.fstat(root_handle.fd)
        _preflight_evidence_root_checkpoint("before_named_after", evidence_root)
        root_named_after = os.stat(evidence_root, follow_symlinks=False)
        if (
            not _same_save_metadata(root_named_before, root_descriptor)
            or not _same_save_metadata(root_descriptor, root_named_after)
        ):
            raise PassiveProbeError(
                "approved evidence root identity changed during preflight"
            )
        root_identity = _identity(evidence_root, root_descriptor)
    except BaseException as error:
        root_primary = error
        raise
    finally:
        owned_root = root_handle
        root_handle = None
        try:
            owned_root.close()
        except BaseException as close_error:
            if root_primary is None:
                raise
            try:
                root_primary.add_note(
                    "secondary approved evidence root close failure: "
                    f"{type(close_error).__name__}: {close_error}"
                )
            except BaseException:
                pass
    _require_ignored_evidence_root(evidence_root)

    off_bytes, off_hash = _read_artifact(mode_off_config, "Mode-off config", 64 * 1024)
    try:
        off_text = off_bytes.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise PassiveProbeError("Mode-off config is not strict UTF-8") from error
    if off_text.encode("utf-8") != off_bytes or off_hash != MODE_OFF_CONFIG_SHA256:
        raise PassiveProbeError("Mode-off config hash mismatch")

    plugin_bytes, plugin_hash = _read_artifact(plugin, "plugin", 64 * 1024 * 1024)
    copy_bytes, copy_hash = _read_artifact(
        plugin_verification_copy,
        "plugin verification copy",
        64 * 1024 * 1024,
    )
    if plugin_bytes != copy_bytes or plugin_hash != copy_hash:
        raise PassiveProbeError("plugin copy mismatch")
    if plugin_hash != expected_plugin_sha256:
        raise PassiveProbeError("plugin hash mismatch")

    preloader_bytes, preloader_hash = _read_artifact(preloader, "preloader", 64 * 1024 * 1024)
    provenance_bytes, provenance_hash = _read_artifact(provenance, "provenance", 1024 * 1024)
    trust = oracle_compat.load_trust(Path(__file__).resolve(strict=True).parents[2])
    reviewed_provenance = oracle_compat.load_provenance_bytes(
        provenance_bytes,
        trust,
        source=str(provenance),
    )
    if hashlib.sha256(preloader_bytes).hexdigest() != reviewed_provenance.patched_preloader_sha256:
        raise PassiveProbeError("preloader provenance mismatch")
    if hashlib.sha256(provenance_bytes).hexdigest() != provenance_hash:
        raise PassiveProbeError("provenance hash instability")

    snapshot = _capture_passive_snapshot(game)
    signature_snapshot = replace(snapshot.legacy, compatibility_state="patched")
    signature_issues = oracle_boot._preflight_issues(
        signature_snapshot,
        game / "Sausage.app",
    )
    if signature_issues:
        raise PassiveProbeError("signature issue: " + "; ".join(signature_issues))
    if not snapshot.installer_status.healthy or snapshot.legacy.compatibility_state != "official":
        raise PassiveProbeError("unhealthy installer official state")
    if snapshot.legacy.assembly_sha256 != EXPECTED_ASSEMBLY_SHA256:
        raise PassiveProbeError("assembly hash mismatch")
    if snapshot.observed_plugin_sha256 != plugin_hash:
        raise PassiveProbeError("installed plugin hash mismatch")
    if snapshot.observed_config_sha256 != off_hash:
        raise PassiveProbeError("installed Mode-off config hash mismatch")

    before_logs = oracle_boot.fingerprint_preloader_logs(game)
    log_inventory = oracle_boot._capture_boot_log_inventory(game)
    if before_logs != log_inventory.regular_fingerprints:
        raise PassiveProbeError("changed log inventory during preflight")
    probe_script = Path(__file__).resolve(strict=True).parents[2] / "tools" / "oracle_passive_probe.py"
    game_executable = game / "Sausage.app" / "Contents" / "MacOS" / "Sausage"
    def preflight_matcher(
        rows: tuple[ProcessRow, ...],
        sampler_pid: int,
    ) -> tuple[ProcessRow, ...]:
        return _matching_probe_processes(
            rows,
            controller_pid=os.getpid(),
            sampler_pid=sampler_pid,
            spawned_pid=None,
            spawned_pgid=None,
            launcher=launcher_file,
            game_executable=game_executable,
            probe_script=probe_script,
            game_root=game,
            observed_identities=frozenset(),
        )

    try:
        _require_no_matching_processes(preflight_matcher)
    except PassiveProbeError as error:
        raise PassiveProbeError(f"matching process exists before launch: {error}") from error

    launch_environment = dict(os.environ)
    home = launch_environment.get("HOME")
    if home is None or not home or not Path(home).is_absolute():
        raise PassiveProbeError("HOME must be one nonempty absolute path")
    ordinary_path = Path(home) / "Library/Application Support/unity.increpare games/Sausage"
    ordinary = fingerprint_save_tree(ordinary_path)
    return PassivePreflight(
        game_root=game,
        macos_product_version=macos_product_version,
        launcher=launcher_file,
        evidence_root=evidence_root,
        evidence_root_identity=root_identity,
        evidence_root_ignored=True,
        mode_off_config=mode_off_config,
        mode_off_config_sha256=off_hash,
        plugin=plugin,
        plugin_verification_copy=plugin_verification_copy,
        plugin_sha256=plugin_hash,
        preloader=preloader,
        preloader_sha256=preloader_hash,
        provenance=provenance,
        provenance_sha256=provenance_hash,
        snapshot=snapshot,
        before_logs=before_logs,
        log_inventory=log_inventory,
        matching_processes=(),
        ordinary_save=ordinary,
        launch_environment=tuple(sorted(launch_environment.items())),
        timeout_seconds=timeout_seconds,
    )
```

- [ ] **Step 4: Run standalone-preflight GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'preflight'
```

Expected: every read-only check and each rejection row passes, exact Tahoe product version `26.6` is retained, and no private leaf, installer call, config write, publication, or launcher acquisition occurs. Evidence-root close failure never masks an active identity primary and the owned handle is closed exactly once.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the standalone preflight**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: preflight passive oracle capture read only"
```

### Task 18: Acquire and own at most one launcher process

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_LauncherOwnership(process, pgid)` whose `close()` stops/reaps exactly once.
- Produces `_acquire_launcher(preflight: PassivePreflight) -> _LauncherOwnership`.
- Blocks `SIGINT` only across `Popen`, PID/PGID validation, and guard storage. A returned process is cleanup-reachable before the prior mask is restored.

- [ ] **Step 1: Add acquisition/handoff interruption RED tests**

```python
import signal


@dataclass
class TrackedProcess:
    pid: int = 9301
    returncode: int | None = None

    def poll(self) -> int | None:
        return self.returncode


@pytest.fixture
def tracked_process(monkeypatch: pytest.MonkeyPatch) -> TrackedProcess:
    process = TrackedProcess()
    monkeypatch.setattr(
        oracle_boot,
        "_retained_spawned_pgid",
        lambda observed: observed.pid,
    )
    return process


@pytest.fixture
def synthetic_preflight(
    complete_preflight_request: dict[str, object],
) -> passive.PassivePreflight:
    return passive.preflight_passive_probe(**complete_preflight_request)


@pytest.mark.parametrize(
    "boundary",
    ("after_popen_return", "after_guard_store", "during_mask_restore"),
)
def test_launcher_acquisition_owns_returned_process_before_interrupt(
    synthetic_preflight: passive.PassivePreflight,
    tracked_process: TrackedProcess,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    primary = KeyboardInterrupt(boundary)
    events: list[str] = []
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_args, **_kwargs: tracked_process)
    monkeypatch.setattr(passive, "_launcher_checkpoint", lambda observed: (_ for _ in ()).throw(primary) if observed == boundary else None)
    monkeypatch.setattr(
        oracle_boot,
        "_cleanup_spawned_process",
        lambda process, pgid: events.append(f"cleanup:{process.pid}:{pgid}"),
    )
    prior_mask = frozenset({signal.SIGTERM})
    masks: list[tuple[int, frozenset[signal.Signals]]] = []

    def fake_sigmask(how: int, mask: set[signal.Signals]) -> set[signal.Signals]:
        masks.append((how, frozenset(mask)))
        if boundary == "during_mask_restore" and how == signal.SIG_SETMASK:
            raise primary
        return set(prior_mask)

    monkeypatch.setattr(signal, "pthread_sigmask", fake_sigmask)
    with pytest.raises(BaseException) as caught:
        passive._acquire_launcher(synthetic_preflight)
    assert caught.value is primary
    assert events == [f"cleanup:{tracked_process.pid}:{tracked_process.pid}"]
    assert masks[0] == (signal.SIG_BLOCK, frozenset({signal.SIGINT}))


def test_launcher_guard_closes_exactly_once(
    synthetic_preflight: passive.PassivePreflight,
    tracked_process: TrackedProcess,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(passive.subprocess, "Popen", lambda *_args, **_kwargs: tracked_process)
    monkeypatch.setattr(signal, "pthread_sigmask", lambda _how, _mask: set())
    monkeypatch.setattr(
        oracle_boot,
        "_cleanup_spawned_process",
        lambda process, pgid: calls.append((process.pid, pgid)) or 0,
    )
    guard = passive._acquire_launcher(synthetic_preflight)
    assert guard.close() == 0
    assert guard.close() == 0
    assert calls == [(tracked_process.pid, tracked_process.pid)]


def test_launcher_guard_remains_recoverable_when_close_is_interrupted(
    tracked_process: TrackedProcess,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    interruption = KeyboardInterrupt("during process cleanup")
    calls = 0

    def cleanup(process: TrackedProcess, pgid: int) -> int:
        nonlocal calls
        calls += 1
        assert process is tracked_process
        assert pgid == tracked_process.pid
        if calls == 1:
            raise interruption
        return 0

    monkeypatch.setattr(oracle_boot, "_cleanup_spawned_process", cleanup)
    guard = passive._LauncherOwnership(tracked_process, tracked_process.pid)
    with pytest.raises(KeyboardInterrupt) as caught:
        guard.close()
    assert caught.value is interruption
    assert guard.process is tracked_process
    assert guard.close() == 0
    assert guard.process is None


def test_launcher_acquisition_uses_exact_popen_and_restores_prior_mask(
    synthetic_preflight: passive.PassivePreflight,
    tracked_process: TrackedProcess,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    popen_calls: list[tuple[tuple[str, ...], dict[str, object]]] = []
    mask_calls: list[tuple[int, frozenset[signal.Signals]]] = []
    prior = {signal.SIGTERM}

    def popen(argv, **kwargs):
        popen_calls.append((argv, kwargs))
        return tracked_process

    def sigmask(how: int, mask: set[signal.Signals]):
        mask_calls.append((how, frozenset(mask)))
        return prior

    monkeypatch.setattr(passive.subprocess, "Popen", popen)
    monkeypatch.setattr(signal, "pthread_sigmask", sigmask)
    monkeypatch.setattr(oracle_boot, "_cleanup_spawned_process", lambda *_args: 0)
    guard = passive._acquire_launcher(synthetic_preflight)
    try:
        assert popen_calls == [
            (
                (str(synthetic_preflight.launcher),),
                {
                    "cwd": synthetic_preflight.game_root,
                    "env": dict(synthetic_preflight.launch_environment),
                    "stdin": passive.subprocess.DEVNULL,
                    "stdout": passive.subprocess.DEVNULL,
                    "stderr": passive.subprocess.DEVNULL,
                    "shell": False,
                    "start_new_session": True,
                },
            )
        ]
        assert mask_calls == [
            (signal.SIG_BLOCK, frozenset({signal.SIGINT})),
            (signal.SIG_SETMASK, frozenset(prior)),
        ]
    finally:
        guard.close()


@pytest.mark.parametrize("failure", ("popen", "unsafe_pgid"))
def test_launcher_acquisition_preserves_validation_primary_and_cleans_if_spawned(
    synthetic_preflight: passive.PassivePreflight,
    tracked_process: TrackedProcess,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    primary = OSError("popen failed") if failure == "popen" else passive.PassiveProbeError("unsafe launcher PGID")
    cleaned: list[tuple[int, int]] = []

    def popen(*_args, **_kwargs):
        if failure == "popen":
            raise primary
        return tracked_process

    monkeypatch.setattr(passive.subprocess, "Popen", popen)
    monkeypatch.setattr(signal, "pthread_sigmask", lambda _how, _mask: set())
    if failure == "unsafe_pgid":
        monkeypatch.setattr(oracle_boot, "_retained_spawned_pgid", lambda _process: 0)
    monkeypatch.setattr(
        oracle_boot,
        "_cleanup_spawned_process",
        lambda process, pgid: cleaned.append((process.pid, pgid)) or 0,
    )
    with pytest.raises(BaseException) as caught:
        passive._acquire_launcher(synthetic_preflight)
    if failure == "popen":
        assert caught.value is primary
        assert cleaned == []
    else:
        assert isinstance(caught.value, passive.PassiveProbeError)
        assert str(caught.value) == "unsafe launcher PGID"
        assert cleaned == [(tracked_process.pid, tracked_process.pid)]
```

- [ ] **Step 2: Run launcher-ownership RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'launcher_acquisition or launcher_guard'
```

Expected: launcher guard and acquisition function are missing.

- [ ] **Step 3: Implement exact signal-mask and ownership transfer**

```python
import signal


_LAUNCHER_CHECKPOINTS = frozenset(
    {"after_popen_return", "after_guard_store", "during_mask_restore"}
)


def _launcher_checkpoint(boundary: str) -> None:
    if boundary not in _LAUNCHER_CHECKPOINTS:
        raise AssertionError(f"unknown launcher checkpoint: {boundary}")


@dataclass(slots=True)
class _LauncherOwnership:
    process: subprocess.Popen[bytes] | None
    pgid: int
    exit_code: int | None = None

    def close(self) -> int | None:
        if self.process is None:
            return self.exit_code
        process = self.process
        exit_code = oracle_boot._cleanup_spawned_process(process, self.pgid)
        self.exit_code = exit_code
        self.process = None
        return exit_code


def _acquire_launcher(preflight: PassivePreflight) -> _LauncherOwnership:
    prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    process: subprocess.Popen[bytes] | None = None
    guard: _LauncherOwnership | None = None
    try:
        process = subprocess.Popen(
            (str(preflight.launcher),),
            cwd=preflight.game_root,
            env=dict(preflight.launch_environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            start_new_session=True,
        )
        _launcher_checkpoint("after_popen_return")
        pgid = oracle_boot._retained_spawned_pgid(process)
        if pgid <= 0:
            raise PassiveProbeError("unsafe launcher PGID")
        guard = _LauncherOwnership(process=process, pgid=pgid)
        process = None
        _launcher_checkpoint("after_guard_store")
        _launcher_checkpoint("during_mask_restore")
        signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)
        return guard
    except BaseException as primary:
        if guard is not None:
            try:
                guard.close()
            except BaseException as secondary:
                primary.add_note(f"launcher guard cleanup also failed: {secondary}")
        elif process is not None:
            try:
                oracle_boot._cleanup_spawned_process(process, process.pid)
            except BaseException as secondary:
                primary.add_note(f"unretained launcher cleanup also failed: {secondary}")
        try:
            signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)
        except BaseException as secondary:
            if secondary is not primary:
                primary.add_note(f"signal-mask restoration also failed: {secondary}")
        raise
```

- [ ] **Step 4: Run launcher-ownership GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'launcher'
```

Expected: Popen failure, return-before-guard, stored-guard, mask-restore, first post-return callback, unsafe PGID, exact prior-mask restoration, and exact-once cleanup pass.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the launcher gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: own one passive oracle launcher"
```

### Task 19A: Validate the pre-mutation and patched lifecycle stages

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`
- Modify: `tests/test_oracle_install_compat.py`

**Interfaces:**
- Produces `_require_stage_snapshot`, `_require_empty_isolated_save`, and the exact timestamp helper used by later lifecycle tasks.
- Installed-tree mutation remains limited to `deploy_plugin`, `deploy_preloader`, and `restore_preloader`.

- [ ] **Step 1: Add exact stage/pre-mutation/isolated-identity RED tests**

The synthetic `test_success_lifecycle_has_one_launcher_and_json_last` body below is registered only in Task 19D against private `_run_passive_probe_lifecycle`; do not add or run it in Task 19A. The public `run_passive_probe` remains absent through Task 20B. Task 19A collects twenty-eight rows: ten exact stage mismatches, two empty/occupied rows, three fresh-preflight/independent-source rows, two named isolated-root replacement rows, eight private evidence-directory/config identity rows, two private-config descriptor-close ownership rows, and one real-installer manifest-transition composition row in `tests/test_oracle_install_compat.py`. The private identity matrix includes persistent same-type/same-byte replacements, within-read config substitutions, and evidence/config swap-back races at named-before/descriptor/named-after boundaries. Every pre-mutation/source/identity row asserts zero installer and launcher calls; the real composition row uses each mutation's exact returned `InstallManifest` and rejects a coherent but different manifest at all five lifecycle states. Because that final row lives in `tests/test_oracle_install_compat.py`, both this task's Files scope and commit command include that file.

```python
def test_success_lifecycle_has_one_launcher_and_json_last(
    complete_preflight_request: dict[str, object],
    synthetic_preflight: passive.PassivePreflight,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    instructions: list[str] = []
    launch_count = 0
    passive_config = tmp_path / "passive.cfg"
    passive_config.write_bytes(b"[Oracle]\nMode = passive\n")
    layout = SimpleNamespace(
        config_path=passive_config,
        config_sha256=sha256(passive_config.read_bytes()).hexdigest(),
        evidence_dir=tmp_path / "evidence",
        evidence_handle=object(),
        isolated_save_dir=tmp_path / "isolated",
        close=lambda: events.append("layout:close"),
    )
    layout.evidence_dir.mkdir()
    layout.isolated_save_dir.mkdir()
    patched_status = replace(
        synthetic_preflight.snapshot.installer_status,
        preloader_compatibility=replace(
            synthetic_preflight.snapshot.installer_status.preloader_compatibility,
            state="patched",
            active_sha256=synthetic_preflight.preloader_sha256,
            patched_sha256=synthetic_preflight.preloader_sha256,
        ),
    )
    patched = replace(
        synthetic_preflight.snapshot,
        legacy=replace(
            synthetic_preflight.snapshot.legacy,
            compatibility_state="patched",
            active_preloader_sha256=synthetic_preflight.preloader_sha256,
        ),
        observed_config_sha256=layout.config_sha256,
        installer_status_before=patched_status,
        installer_status_after=patched_status,
    )
    snapshots = iter(
        (("snapshot:patched", patched), ("snapshot:post_process", patched), ("snapshot:after", synthetic_preflight.snapshot))
    )

    class FakeLoggingGuard:
        def close(self) -> None:
            events.append("logging_guard:close")

    class FakeLauncherGuard:
        process = FakeProcess()
        pgid = 9401
        closed = False

        def close(self) -> int:
            if not self.closed:
                self.closed = True
                events.append("launcher:reap")
            return 0

    fake_launcher = FakeLauncherGuard()
    trace_run = SimpleNamespace(header=SimpleNamespace(run_id="a" * 32))
    trace = SimpleNamespace(
        run=trace_run,
        raw_bytes=b"x",
        summary=passive.TraceSummary(
            str(layout.evidence_dir / "passive-trace.ndjson"),
            "valid_success",
            "success",
            None,
            5,
            3,
            "8" * 64,
            1,
        ),
    )
    retained = SimpleNamespace(
        files=(),
        public=SimpleNamespace(copied_logs=(), moved_logs=()),
        close=lambda: events.append("retained:close"),
    )
    ordinary_calls = 0
    absence_calls = 0

    def capture(_root: Path) -> passive.PassiveInstallSnapshot:
        label, snapshot = next(snapshots)
        events.append(label)
        return snapshot

    def ordinary(_path: Path) -> passive.SaveTreeProof:
        nonlocal ordinary_calls
        ordinary_calls += 1
        events.append(("ordinary:recheck", "ordinary:post_process", "ordinary:final")[ordinary_calls - 1])
        return synthetic_preflight.ordinary_save

    def acquire(_preflight: passive.PassivePreflight) -> FakeLauncherGuard:
        nonlocal launch_count
        launch_count += 1
        events.append("launcher:acquire")
        return fake_launcher

    def monitor(*_args: object, **_kwargs: object) -> passive._PassiveMonitorOutcome:
        events.append("monitor:complete")
        for instruction in passive.PASSIVE_INSTRUCTIONS:
            instructions.append(instruction)
        return passive._PassiveMonitorOutcome(
            "complete", passive.PASSIVE_MARKERS, (), (), None, trace
        )

    def absence(*_args: object) -> tuple[passive.ProcessRow, ...]:
        nonlocal absence_calls
        absence_calls += 1
        events.append("processes:absent" if absence_calls == 1 else "processes:final_absent")
        return ()

    monkeypatch.setattr(passive, "preflight_passive_probe", lambda *_args, **_kwargs: events.append("preflight") or synthetic_preflight)
    monkeypatch.setattr(oracle_boot, "_open_bepinex_disk_logging_guard", lambda _root: events.append("logging_guard:open") or FakeLoggingGuard())
    monkeypatch.setattr(passive, "_allocate_passive_layout", lambda _root: events.append("layout:allocate") or layout)
    monkeypatch.setattr(
        passive,
        "_revalidate_pre_mutation",
        lambda _preflight, _layout: Path(synthetic_preflight.plugin).read_bytes(),
    )
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda _root, _bytes, _sha, text: (
            events.append("plugin:passive" if "passive" in text else "plugin:off")
            or synthetic_preflight.snapshot.installer_status.manifest
        ),
    )
    monkeypatch.setattr(
        oracle_install,
        "deploy_preloader",
        lambda *_args: (
            events.append("preloader:patched")
            or synthetic_preflight.snapshot.installer_status.manifest
        ),
    )
    monkeypatch.setattr(passive, "_capture_passive_snapshot", capture)
    monkeypatch.setattr(passive, "fingerprint_save_tree", ordinary)
    monkeypatch.setattr(passive, "_require_empty_isolated_save", lambda _layout: events.append("isolated:empty"))
    monkeypatch.setattr(oracle_boot, "_verify_and_close_bepinex_disk_logging_guard", lambda _guard: events.append("logging_guard:verify_close") or object())
    monkeypatch.setattr(passive, "_acquire_launcher", acquire)
    monkeypatch.setattr(passive, "_wait_for_passive_trace", monitor)
    monkeypatch.setattr(passive, "_require_no_matching_processes_for_preflight", absence)
    monkeypatch.setattr(passive, "_retain_post_reap_trace", lambda _layout: events.append("trace:retain") or trace)
    monkeypatch.setattr(passive, "require_passive_success", lambda _run: None)
    monkeypatch.setattr(
        passive,
        "_secure_isolated_save_tree",
        lambda _layout: events.append("isolated:secure")
        or passive.IsolatedSaveObservation((), True, (), 0, False),
    )
    monkeypatch.setattr(passive, "_auxiliary_specs", lambda *_args: ())
    monkeypatch.setattr(oracle_boot, "_collect_boot_evidence_into", lambda *_args, **_kwargs: events.append("evidence:collect") or retained)
    monkeypatch.setattr(passive, "_require_retained_success_evidence", lambda *_args: None)
    monkeypatch.setattr(
        passive,
        "_restore_success_stage",
        lambda *_args: (
            events.extend(("plugin:off", "preloader:official")) or synthetic_preflight.snapshot,
            tmp_path / "recovery",
        ),
    )
    staged = SimpleNamespace(committed=False)
    monkeypatch.setattr(
        passive,
        "_stage_passive_result",
        lambda *_args: events.append("evidence:fsync") or staged,
    )
    monkeypatch.setattr(
        passive,
        "_commit_staged_passive_result",
        lambda _staged: events.append("json:commit"),
    )

    result = passive._run_passive_probe_lifecycle(
        **complete_preflight_request,
        instruction_sink=instructions.append,
    )
    assert result.success is True
    assert events == [
        "preflight",
        "logging_guard:open",
        "layout:allocate",
        "plugin:passive",
        "preloader:patched",
        "snapshot:patched",
        "ordinary:recheck",
        "isolated:empty",
        "logging_guard:verify_close",
        "launcher:acquire",
        "monitor:complete",
        "launcher:reap",
        "processes:absent",
        "snapshot:post_process",
        "trace:retain",
        "isolated:secure",
        "evidence:collect",
        "ordinary:post_process",
        "plugin:off",
        "preloader:official",
        "processes:final_absent",
        "ordinary:final",
        "evidence:fsync",
        "retained:close",
        "layout:close",
        "json:commit",
    ]
    assert launch_count == 1
    assert tuple(instructions) == passive.PASSIVE_INSTRUCTIONS


@pytest.mark.parametrize(
    "case",
    (
        "unhealthy",
        "legacy_installer_health",
        "app_signature",
        "compatibility",
        "plugin",
        "config",
        "active_preloader",
        "assembly",
        "runtime_manifest",
        "manifest_entries",
    ),
)
def test_require_stage_snapshot_rejects_each_exact_mismatch(
    synthetic_preflight: passive.PassivePreflight,
    case: str,
) -> None:
    expected = synthetic_preflight.snapshot
    observed = expected
    if case == "unhealthy":
        unhealthy = replace(expected.installer_status_after, missing=("plugin",))
        observed = replace(
            expected,
            installer_status_before=unhealthy,
            installer_status_after=unhealthy,
        )
    elif case == "legacy_installer_health":
        observed = replace(
            expected,
            legacy=replace(expected.legacy, installer_healthy=False),
        )
    elif case == "app_signature":
        observed = replace(
            expected,
            legacy=replace(
                expected.legacy,
                app_signature=oracle_boot._AppSignature(
                    1,
                    "invalid",
                    "signature drift",
                ),
            ),
        )
    elif case == "compatibility":
        observed = replace(
            expected,
            legacy=replace(expected.legacy, compatibility_state="patched"),
        )
    elif case == "plugin":
        observed = replace(expected, observed_plugin_sha256="0" * 64)
    elif case == "config":
        observed = replace(expected, observed_config_sha256="0" * 64)
    elif case == "active_preloader":
        observed = replace(
            expected,
            legacy=replace(expected.legacy, active_preloader_sha256="0" * 64),
        )
    elif case == "assembly":
        observed = replace(
            expected,
            legacy=replace(expected.legacy, assembly_sha256="0" * 64),
        )
    elif case == "runtime_manifest":
        changed = replace(
            expected.installer_status.manifest,
            runtime_archive_sha256="0" * 64,
        )
        changed_status = replace(expected.installer_status, manifest=changed)
        observed = replace(
            expected,
            installer_status_before=changed_status,
            installer_status_after=changed_status,
        )
    else:
        changed = replace(
            expected.installer_status.manifest,
            entries=expected.installer_status.manifest.entries
            + (oracle_install.ManifestEntry("coherent-drift", "directory", None),),
        )
        changed_status = replace(expected.installer_status, manifest=changed)
        observed = replace(
            expected,
            installer_status_before=changed_status,
            installer_status_after=changed_status,
        )
    with pytest.raises(passive.PassiveProbeError):
        passive._require_stage_snapshot(
            observed,
            compatibility=expected.legacy.compatibility_state,
            plugin_sha256=expected.observed_plugin_sha256,
            config_sha256=expected.observed_config_sha256,
            active_preloader_sha256=expected.legacy.active_preloader_sha256,
            assembly_sha256=expected.legacy.assembly_sha256,
            installer_healthy=expected.legacy.installer_healthy,
            app_signature=expected.legacy.app_signature,
            expected_manifest=expected.installer_status.manifest,
        )


@pytest.mark.parametrize("occupied", (False, True))
def test_empty_isolated_before_launch_accepts_only_empty(
    passive_layout: passive.PassiveLayout,
    occupied: bool,
) -> None:
    if occupied:
        (passive_layout.isolated_save_dir / "unexpected").write_bytes(b"save")
        with pytest.raises(passive.PassiveProbeError, match="not empty"):
            passive._require_empty_isolated_save(passive_layout)
    else:
        passive._require_empty_isolated_save(passive_layout)


@pytest.mark.parametrize(
    "case",
    ("fresh_preflight", "plugin_source", "plugin_verification_copy"),
)
def test_pre_mutation_rejects_fresh_or_source_drift_before_any_mutation(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    mutation_calls: list[str] = []
    fresh = (
        replace(synthetic_preflight, plugin_sha256="0" * 64)
        if case == "fresh_preflight"
        else synthetic_preflight
    )

    def artifact(path: Path, _label: str, _maximum: int) -> tuple[bytes, str]:
        payload = path.read_bytes()
        digest = sha256(payload).hexdigest()
        if (
            (case == "plugin_source" and path == synthetic_preflight.plugin)
            or (
                case == "plugin_verification_copy"
                and path == synthetic_preflight.plugin_verification_copy
            )
        ):
            digest = "9" * 64
        return payload, digest

    monkeypatch.setattr(passive, "preflight_passive_probe", lambda *_a, **_k: fresh)
    monkeypatch.setattr(passive, "_read_artifact", artifact)
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda *_a, **_k: mutation_calls.append("plugin"),
    )
    monkeypatch.setattr(
        oracle_install,
        "deploy_preloader",
        lambda *_a, **_k: mutation_calls.append("preloader"),
    )
    monkeypatch.setattr(
        passive,
        "_acquire_launcher",
        lambda *_a, **_k: mutation_calls.append("launcher"),
    )
    with pytest.raises(passive.PassiveProbeError, match="changed"):
        passive._revalidate_pre_mutation(synthetic_preflight, passive_layout)
    assert mutation_calls == []


@pytest.mark.parametrize(
    ("target", "timing", "swap_back"),
    (
        ("evidence_dir", "before_gate", False),
        ("evidence_dir", "evidence_after_named_before", True),
        ("evidence_dir", "evidence_before_named_after", True),
        ("evidence_dir", "before_identity_after", False),
        ("config", "before_gate", False),
        ("config", "config_after_named_before", False),
        ("config", "config_before_named_after", True),
        ("config", "before_identity_after", False),
    ),
)
def test_pre_mutation_rejects_private_name_substitution_before_mutation(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    timing: str,
    swap_back: bool,
) -> None:
    mutation_calls: list[str] = []
    fired = False

    def substitute() -> None:
        nonlocal fired
        assert fired is False
        fired = True
        if target == "evidence_dir":
            original = passive_layout.evidence_dir
            parked = original.with_name(original.name + "-held")
            config_bytes = passive_layout.config_path.read_bytes()
            original.rename(parked)
            original.mkdir(mode=0o700)
            if swap_back:
                original.rmdir()
                parked.rename(original)
            else:
                (original / passive_layout.config_path.name).write_bytes(config_bytes)
        else:
            original = passive_layout.config_path
            parked = original.with_suffix(".original")
            payload = original.read_bytes()
            original.rename(parked)
            original.write_bytes(payload)
            if swap_back:
                original.unlink()
                parked.rename(original)

    def checkpoint(boundary: str, layout: passive.PassiveLayout) -> None:
        assert layout is passive_layout
        if boundary == timing and not fired:
            substitute()

    monkeypatch.setattr(
        passive,
        "preflight_passive_probe",
        lambda *_args, **_kwargs: synthetic_preflight,
    )
    monkeypatch.setattr(passive, "_pre_mutation_identity_checkpoint", checkpoint)
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda *_args, **_kwargs: mutation_calls.append("plugin"),
    )
    monkeypatch.setattr(
        oracle_install,
        "deploy_preloader",
        lambda *_args, **_kwargs: mutation_calls.append("preloader"),
    )
    monkeypatch.setattr(
        passive,
        "_acquire_launcher",
        lambda *_args, **_kwargs: mutation_calls.append("launcher"),
    )
    if timing == "before_gate":
        substitute()
    with pytest.raises(passive.PassiveProbeError, match="identity changed"):
        passive._revalidate_pre_mutation(synthetic_preflight, passive_layout)
    assert fired is True
    assert mutation_calls == []


@pytest.mark.parametrize("case", ("primary", "close_only"))
def test_private_config_reader_closes_once_without_masking_primary(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    primary = KeyboardInterrupt("private config read interrupted")
    secondary = OSError("private config descriptor close failed")
    original_close = passive.os.close
    close_calls: list[int] = []
    mutation_calls: list[str] = []

    def checkpoint(boundary: str, layout: passive.PassiveLayout) -> None:
        assert layout is passive_layout
        if case == "primary" and boundary == "config_before_named_after":
            raise primary

    def close_then_fail(descriptor: int) -> None:
        if close_calls:
            original_close(descriptor)
            return
        close_calls.append(descriptor)
        original_close(descriptor)
        raise secondary

    monkeypatch.setattr(passive, "_pre_mutation_identity_checkpoint", checkpoint)
    monkeypatch.setattr(passive.os, "close", close_then_fail)
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda *_args, **_kwargs: mutation_calls.append("plugin"),
    )
    monkeypatch.setattr(
        passive,
        "_acquire_launcher",
        lambda *_args, **_kwargs: mutation_calls.append("launcher"),
    )
    if case == "primary":
        with pytest.raises(KeyboardInterrupt) as caught:
            passive._read_retained_private_config(passive_layout)
        assert caught.value is primary
        assert any(
            "secondary private config descriptor close failure" in note
            and str(secondary) in note
            for note in primary.__notes__
        )
    else:
        with pytest.raises(OSError) as caught:
            passive._read_retained_private_config(passive_layout)
        assert caught.value is secondary
    assert len(close_calls) == 1
    with pytest.raises(OSError):
        os.fstat(close_calls[0])
    assert mutation_calls == []


@pytest.mark.parametrize("boundary", ("before_scan", "after_scan"))
def test_empty_isolated_rejects_named_root_replacement_at_each_scan_boundary(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    original = passive_layout.isolated_save_dir
    held = original.with_name(original.name + "-held")
    fired = False

    def checkpoint(observed: str) -> None:
        nonlocal fired
        if not fired and observed == boundary:
            fired = True
            original.rename(held)
            original.mkdir(mode=0o700)

    monkeypatch.setattr(passive, "_isolated_empty_checkpoint", checkpoint)
    with pytest.raises(passive.PassiveProbeError, match="changed"):
        passive._require_empty_isolated_save(passive_layout)
    assert fired is True


# Add this row to tests/test_oracle_install_compat.py, which owns the real
# official/preloader fixtures. Add
# `from dataclasses import replace`, `import ssr_env.oracle_boot as oracle_boot`,
# and `from ssr_env import oracle_passive_probe as passive` to that file's imports.
def test_real_installer_manifests_drive_every_lifecycle_stage(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    game = installed_official_game
    preloader, provenance = deploy_request
    plugin_bytes = b"reviewed-plugin"
    plugin_hash = sha256(plugin_bytes).hexdigest()
    off_text = "[Oracle]\nMode = off\n"
    passive_text = "[Oracle]\nMode = passive\n"
    signature = oracle_boot._AppSignature(0, "valid", "")

    def capture(
        expected_manifest: oracle_install.InstallManifest,
    ) -> passive.PassiveInstallSnapshot:
        status = oracle_install.status_install(game, repo_root=Path("/unused"))
        assert status.manifest == expected_manifest
        compatibility = status.preloader_compatibility
        legacy = oracle_boot._BootSnapshot(
            status.manifest.game_assembly_sha256,
            compatibility.active_sha256,
            status.healthy,
            compatibility.state,
            signature,
        )
        return passive.PassiveInstallSnapshot(
            legacy,
            sha256((game / oracle_install.PLUGIN_RELATIVE_PATH).read_bytes()).hexdigest(),
            sha256((game / oracle_install.CONFIG_RELATIVE_PATH).read_bytes()).hexdigest(),
            status,
            status,
        )

    official_off = oracle_install._deploy_plugin_bytes(
        game,
        plugin_bytes,
        plugin_hash,
        off_text,
    )
    manifests = passive._LifecycleManifests(official_off)
    stages: list[tuple[str, passive.PassiveInstallSnapshot, oracle_install.InstallManifest]] = [
        ("official", capture(official_off), official_off),
    ]
    manifests.official_passive = oracle_install._deploy_plugin_bytes(
        game,
        plugin_bytes,
        plugin_hash,
        passive_text,
    )
    stages.append(
        ("official", capture(manifests.official_passive), manifests.official_passive)
    )
    manifests.patched_passive = oracle_install.deploy_preloader(
        game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )
    stages.append(
        ("patched", capture(manifests.patched_passive), manifests.patched_passive)
    )
    manifests.patched_off = oracle_install._deploy_plugin_bytes(
        game,
        plugin_bytes,
        plugin_hash,
        off_text,
    )
    stages.append(("patched", capture(manifests.patched_off), manifests.patched_off))
    manifests.official_off, _recovery = oracle_install.restore_preloader(
        game,
        repo_root=Path("/unused"),
    )
    stages.append(("official", capture(manifests.official_off), manifests.official_off))

    baseline = stages[0][1]
    for compatibility, snapshot, exact_manifest in stages:
        passive._require_stage_snapshot(
            snapshot,
            compatibility=compatibility,
            plugin_sha256=plugin_hash,
            config_sha256=snapshot.observed_config_sha256,
            active_preloader_sha256=snapshot.legacy.active_preloader_sha256,
            assembly_sha256=baseline.legacy.assembly_sha256,
            installer_healthy=True,
            app_signature=signature,
            expected_manifest=exact_manifest,
        )
        coherent_other = replace(
            exact_manifest,
            entries=exact_manifest.entries
            + (oracle_install.ManifestEntry("coherent-but-unreturned", "directory", None),),
        )
        drift_status = replace(snapshot.installer_status, manifest=coherent_other)
        coherent_drift = replace(
            snapshot,
            installer_status_before=drift_status,
            installer_status_after=drift_status,
        )
        with pytest.raises(
            passive.PassiveProbeError,
            match="exact mutation result",
        ):
            passive._require_stage_snapshot(
                coherent_drift,
                compatibility=compatibility,
                plugin_sha256=plugin_hash,
                config_sha256=snapshot.observed_config_sha256,
                active_preloader_sha256=snapshot.legacy.active_preloader_sha256,
                assembly_sha256=baseline.legacy.assembly_sha256,
                installer_healthy=True,
                app_signature=signature,
                expected_manifest=exact_manifest,
            )
```

- [ ] **Step 2: Run stage/pre-mutation RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py tests/test_oracle_install_compat.py \
  -k 'require_stage_snapshot or empty_isolated_before_launch or pre_mutation or private_config_reader or named_root_replacement or real_installer_manifests_drive'
```

Expected: a stage pin, `_revalidate_pre_mutation`, retained private-config reader/close owner, or named private-root revalidation is missing. The success-lifecycle test is not collected.

- [ ] **Step 3: Implement exact stage and pre-mutation validation helpers**

Add helpers for timestamps, stage health, and empty isolated state:

```python
def _utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f0Z")


@dataclass(slots=True)
class _LifecycleManifests:
    official_off: oracle_install.InstallManifest
    official_passive: oracle_install.InstallManifest | None = None
    patched_passive: oracle_install.InstallManifest | None = None
    patched_off: oracle_install.InstallManifest | None = None

    @classmethod
    def from_preflight(cls, preflight: PassivePreflight) -> "_LifecycleManifests":
        return cls(preflight.snapshot.installer_status.manifest)


def _require_stage_snapshot(
    snapshot: PassiveInstallSnapshot,
    *,
    compatibility: Literal["official", "patched"],
    plugin_sha256: str,
    config_sha256: str,
    active_preloader_sha256: str,
    assembly_sha256: str,
    installer_healthy: bool,
    app_signature: oracle_boot._AppSignature,
    expected_manifest: oracle_install.InstallManifest,
) -> None:
    if not snapshot.installer_status.healthy:
        raise PassiveProbeError("installer snapshot is unhealthy")
    if snapshot.legacy.installer_healthy != installer_healthy:
        raise PassiveProbeError("legacy installer-health snapshot changed")
    if snapshot.legacy.installer_healthy != snapshot.installer_status.healthy:
        raise PassiveProbeError("legacy and current installer health disagree")
    if snapshot.legacy.app_signature != app_signature:
        raise PassiveProbeError("application signature snapshot changed")
    if snapshot.legacy.compatibility_state != compatibility:
        raise PassiveProbeError(f"unexpected compatibility state: {snapshot.legacy.compatibility_state}")
    if snapshot.observed_plugin_sha256 != plugin_sha256:
        raise PassiveProbeError("installed plugin hash mismatch")
    if snapshot.observed_config_sha256 != config_sha256:
        raise PassiveProbeError("installed config hash mismatch")
    if snapshot.legacy.active_preloader_sha256 != active_preloader_sha256:
        raise PassiveProbeError("installed active preloader hash mismatch")
    if snapshot.legacy.assembly_sha256 != assembly_sha256:
        raise PassiveProbeError("installed assembly hash mismatch")
    manifest = snapshot.installer_status.manifest
    if manifest != expected_manifest:
        raise PassiveProbeError("installed manifest differs from exact mutation result")
    if manifest.game_assembly_sha256 != assembly_sha256:
        raise PassiveProbeError("installed manifest assembly pin changed")


def _require_empty_isolated_save(layout: PassiveLayout) -> None:
    named_before = os.stat(layout.isolated_save_dir, follow_symlinks=False)
    descriptor_before = os.fstat(layout.isolated_save_handle.fd)
    if (
        _identity(layout.isolated_save_dir, named_before) != layout.isolated_save_identity
        or _identity(layout.isolated_save_dir, descriptor_before) != layout.isolated_save_identity
        or not _same_save_metadata(named_before, descriptor_before)
    ):
        raise PassiveProbeError("isolated save root changed before empty proof")
    _isolated_empty_checkpoint("before_scan")
    with os.scandir(layout.isolated_save_handle.fd) as entries:
        if next(entries, None) is not None:
            raise PassiveProbeError("isolated save is not empty before launch")
    _isolated_empty_checkpoint("after_scan")
    descriptor_after = os.fstat(layout.isolated_save_handle.fd)
    named_after = os.stat(layout.isolated_save_dir, follow_symlinks=False)
    if (
        not _same_save_metadata(descriptor_before, descriptor_after)
        or not _same_save_metadata(descriptor_after, named_after)
        or _identity(layout.isolated_save_dir, named_after) != layout.isolated_save_identity
    ):
        raise PassiveProbeError("isolated save root changed during empty proof")


def _isolated_empty_checkpoint(_boundary: str) -> None:
    return None


def _pre_mutation_identity_checkpoint(
    _boundary: str,
    _layout: PassiveLayout,
) -> None:
    return None


def _read_retained_private_config(
    layout: PassiveLayout,
) -> tuple[bytes, str, os.stat_result]:
    descriptor = -1
    primary: BaseException | None = None
    try:
        named_before = os.stat(
            layout.config_path.name,
            dir_fd=layout.evidence_handle.fd,
            follow_symlinks=False,
        )
        _pre_mutation_identity_checkpoint("config_after_named_before", layout)
        descriptor = os.open(
            layout.config_path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=layout.evidence_handle.fd,
        )
        descriptor_before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(descriptor_before.st_mode)
            or _identity(layout.config_path, named_before)
            != layout.config_identity
            or _identity(layout.config_path, descriptor_before)
            != layout.config_identity
            or not _same_save_metadata(named_before, descriptor_before)
            or descriptor_before.st_size > 64 * 1024
        ):
            raise PassiveProbeError(
                "passive config identity changed before retained read"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(
                descriptor,
                min(64 * 1024, 64 * 1024 + 1 - total),
            )
            if not chunk:
                break
            total += len(chunk)
            if total > 64 * 1024:
                raise PassiveProbeError("passive config exceeds byte limit")
            chunks.append(chunk)
        descriptor_after = os.fstat(descriptor)
        _pre_mutation_identity_checkpoint("config_before_named_after", layout)
        named_after = os.stat(
            layout.config_path.name,
            dir_fd=layout.evidence_handle.fd,
            follow_symlinks=False,
        )
        if (
            _identity(layout.config_path, descriptor_after)
            != layout.config_identity
            or _identity(layout.config_path, named_after)
            != layout.config_identity
            or not _same_save_metadata(descriptor_before, descriptor_after)
            or not _same_save_metadata(descriptor_after, named_after)
            or total != descriptor_after.st_size
        ):
            raise PassiveProbeError(
                "passive config identity changed during retained read"
            )
        payload = b"".join(chunks)
        return payload, hashlib.sha256(payload).hexdigest(), descriptor_after
    except BaseException as error:
        primary = error
        raise
    finally:
        if descriptor >= 0:
            owned_descriptor = descriptor
            descriptor = -1
            try:
                os.close(owned_descriptor)
            except BaseException as close_error:
                if primary is None:
                    raise
                try:
                    primary.add_note(
                        "secondary private config descriptor close failure: "
                        f"{type(close_error).__name__}: {close_error}"
                    )
                except BaseException:
                    pass
```

Add the complete pre-mutation gate. It re-runs the standalone preflight from retained request fields, requires exact equality with the retained preflight (including installed snapshot, ordinary proof, process/log observations, launch environment, and source hashes), re-reads both plugin copies, preloader, provenance bytes, and Mode-off config, requires all retained literal hashes again, validates the approved-root and both private named identities, proves the config identity/hash, proves the trace target absent twice, and calls `_require_empty_isolated_save`. It performs no mutation and acquires no launcher:

```python
def _revalidate_pre_mutation(preflight: PassivePreflight, layout: PassiveLayout) -> bytes:
    fresh = preflight_passive_probe(
        preflight.game_root, preflight.launcher, preflight.mode_off_config,
        preflight.plugin, preflight.plugin_verification_copy, preflight.plugin_sha256,
        preflight.preloader, preflight.provenance, preflight.evidence_root,
        preflight.timeout_seconds,
    )
    if fresh != preflight:
        raise PassiveProbeError("standalone preflight changed before mutation")
    approved_root_before = os.stat(preflight.evidence_root, follow_symlinks=False)
    evidence_named_before = os.stat(layout.evidence_dir, follow_symlinks=False)
    _pre_mutation_identity_checkpoint("evidence_after_named_before", layout)
    evidence_descriptor_before = os.fstat(layout.evidence_handle.fd)
    if (
        _identity(preflight.evidence_root, approved_root_before)
        != preflight.evidence_root_identity
        or _identity(layout.evidence_dir, evidence_named_before)
        != layout.evidence_identity
        or _identity(layout.evidence_dir, evidence_descriptor_before)
        != layout.evidence_identity
        or not _same_save_metadata(
            evidence_named_before,
            evidence_descriptor_before,
        )
    ):
        raise PassiveProbeError("pre-mutation private identity changed before proof")
    authenticated_plugin: bytes | None = None
    for path, label, maximum, expected in (
        (preflight.plugin, "plugin", 64 * 1024 * 1024, preflight.plugin_sha256),
        (preflight.plugin_verification_copy, "plugin verification copy", 64 * 1024 * 1024, preflight.plugin_sha256),
        (preflight.preloader, "preloader", 64 * 1024 * 1024, preflight.preloader_sha256),
        (preflight.provenance, "provenance", 1024 * 1024, preflight.provenance_sha256),
        (preflight.mode_off_config, "Mode-off config", 64 * 1024, preflight.mode_off_config_sha256),
    ):
        payload, digest = _read_artifact(path, label, maximum)
        if digest != expected:
            raise PassiveProbeError(f"{label} changed before mutation")
        if path == preflight.plugin:
            authenticated_plugin = payload
    _config_payload, config_digest, config_descriptor_seal = (
        _read_retained_private_config(layout)
    )
    if config_digest != layout.config_sha256:
        raise PassiveProbeError("passive config changed before mutation")
    _require_empty_isolated_save(layout)
    for _pass in range(2):
        try:
            os.stat(layout.trace_path.name, dir_fd=layout.evidence_handle.fd,
                    follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise PassiveProbeError("passive trace target appeared before mutation")
    _pre_mutation_identity_checkpoint("before_identity_after", layout)
    evidence_descriptor_after = os.fstat(layout.evidence_handle.fd)
    _pre_mutation_identity_checkpoint("evidence_before_named_after", layout)
    evidence_named_after = os.stat(layout.evidence_dir, follow_symlinks=False)
    config_named_final = os.stat(
        layout.config_path.name,
        dir_fd=layout.evidence_handle.fd,
        follow_symlinks=False,
    )
    approved_root_after = os.stat(preflight.evidence_root, follow_symlinks=False)
    if (
        _identity(preflight.evidence_root, approved_root_after)
        != preflight.evidence_root_identity
        or not _same_save_metadata(approved_root_before, approved_root_after)
        or _identity(layout.evidence_dir, evidence_named_after)
        != layout.evidence_identity
        or not _same_save_metadata(
            evidence_descriptor_before,
            evidence_descriptor_after,
        )
        or not _same_save_metadata(
            evidence_descriptor_after,
            evidence_named_after,
        )
        or _identity(layout.config_path, config_named_final)
        != layout.config_identity
        or not _same_save_metadata(config_descriptor_seal, config_named_final)
    ):
        raise PassiveProbeError("pre-mutation private identity changed during proof")
    if authenticated_plugin is None:
        raise AssertionError("pre-mutation plugin bytes were not retained")
    return authenticated_plugin
```


- [ ] **Step 4: Run the stage-validation GREEN gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py tests/test_oracle_install_compat.py \
  -k 'require_stage_snapshot or empty_isolated_before_launch or pre_mutation or private_config_reader or named_root_replacement or real_installer_manifests_drive'
```

Expected: every compatibility/plugin/config/status mismatch and nonempty isolated-save row fails closed; both private-config descriptor-close rows are selected and prove exact-once close without masking an active primary.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit lifecycle stage validation**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py \
  tests/test_oracle_install_compat.py
git commit -m "feat: validate passive lifecycle stages"
```

### Task 19B: Bind monitor, post-reap, and retained evidence to one trace

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_auxiliary_specs(layout, trace)` with exact config and trace identity/hash pairs.
- Produces `_require_retained_success_evidence(monitor_trace, post_reap_trace, retained)` and requires exact object identity metadata, raw bytes, hash, and size equality across all three observations.
- Requires retained canonical boot decision, every passive success marker, zero errors, zero failure markers, and zero structural/public issues.

- [ ] **Step 1: Add three-way identity/bytes and decision RED tests**

Add the following twenty-one-item matrix. It constructs all three owners independently, so equality cannot pass merely because two variables alias one object:

```python
def _synthetic_success_trace(layout: passive.PassiveLayout) -> passive._TraceObservation:
    raw = b'{"synthetic":"success"}\n'
    path_identity = passive.PathIdentity(str(layout.trace_path), 1, 2, 0o600)
    seal = passive._TraceFileSeal(
        path_identity,
        (1, 2, stat.S_IFREG | 0o600, len(raw), 7),
        len(raw),
        7,
        8,
    )
    summary = passive.TraceSummary(
        str(layout.trace_path), "valid_success", "success", None, 5, 3,
        sha256(raw).hexdigest(), len(raw),
    )
    run = SimpleNamespace(header=SimpleNamespace(run_id="a" * 32), outcome="success")
    return passive._TraceObservation(seal, path_identity, len(raw), 7, 8, summary, run, raw)


@pytest.mark.parametrize(
    "case",
    (
        "monitor_device", "monitor_inode", "monitor_mode", "monitor_size",
        "monitor_mtime", "monitor_ctime", "monitor_raw", "monitor_hash", "monitor_run",
        "retained_identity", "retained_raw", "retained_hash", "retained_size",
        "decision_absent", "decision_boot_marker", "decision_error", "public_issue",
        "canonical_absent", "canonical_failure", "canonical_passive_marker",
        "config_name_substitution",
    ),
)
def test_three_way_trace_and_canonical_decision_are_exact(
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    monitor = _synthetic_success_trace(passive_layout)
    post = replace(monitor)
    if case == "config_name_substitution":
        parked = passive_layout.config_path.with_suffix(".original")
        passive_layout.config_path.rename(parked)
        passive_layout.config_path.write_bytes(parked.read_bytes())
        with pytest.raises(passive.PassiveProbeError, match="config identity changed"):
            passive._auxiliary_specs(passive_layout, monitor)
        return
    if case.startswith("monitor_"):
        field = case.removeprefix("monitor_")
        if field in {"device", "inode", "mode"}:
            identity = replace(
                post.identity,
                **{field: getattr(post.identity, field) + 1},
            )
            post = replace(post, identity=identity)
        elif field in {"size", "mtime", "ctime"}:
            target = "mtime_ns" if field == "mtime" else "ctime_ns" if field == "ctime" else field
            post = replace(post, **{target: getattr(post, target) + 1})
        elif field == "raw":
            post = replace(post, raw_bytes=b'X"synthetic":"success"}\n')
        elif field == "hash":
            post = replace(post, summary=replace(post.summary, sha256="0" * 64))
        else:
            post = replace(post, run=SimpleNamespace(header=SimpleNamespace(run_id="b" * 32)))

    trace_file = SimpleNamespace(kind="passive_trace", identity=monitor.seal.evidence_identity)
    canonical_file = SimpleNamespace(
        kind="boot_log", relative_path=oracle_boot._CANONICAL_BOOT_LOG
    )
    files: tuple[object, ...] = (trace_file, canonical_file)
    decision = SimpleNamespace(markers=oracle_boot._REQUIRED_BOOT_MARKERS, errors=())
    public = SimpleNamespace(issues=())
    retained_raw = post.raw_bytes
    retained_hash = post.summary.sha256
    retained_size = post.summary.size
    canonical = ("\n".join(passive.PASSIVE_MARKERS) + "\n").encode("ascii")
    if case == "retained_identity":
        trace_file.identity = (9, 9, stat.S_IFREG | 0o600, len(retained_raw), 7)
    elif case == "retained_raw":
        retained_raw = b"different-but-retained\n"
    elif case == "retained_hash":
        retained_hash = "9" * 64
    elif case == "retained_size":
        retained_size += 1
    elif case == "decision_absent":
        decision = None
    elif case == "decision_boot_marker":
        decision = SimpleNamespace(markers=oracle_boot._REQUIRED_BOOT_MARKERS[:-1], errors=())
    elif case == "decision_error":
        decision = SimpleNamespace(markers=oracle_boot._REQUIRED_BOOT_MARKERS, errors=("boom",))
    elif case == "public_issue":
        public = SimpleNamespace(issues=("unsafe",))
    elif case == "canonical_absent":
        files = (trace_file,)
    elif case == "canonical_failure":
        canonical += b"SSR oracle passive trace failed: settle_timeout\n"
    elif case == "canonical_passive_marker":
        canonical = ("\n".join(passive.PASSIVE_MARKERS[:-1]) + "\n").encode("ascii")

    retained = SimpleNamespace(files=files, decision=decision, public=public)

    def read_retained(_retained: object, item: object) -> tuple[bytes, object]:
        if item is trace_file:
            return retained_raw, SimpleNamespace(sha256=retained_hash, size=retained_size)
        return canonical, SimpleNamespace(sha256=sha256(canonical).hexdigest(), size=len(canonical))

    monkeypatch.setattr(oracle_boot, "_read_retained_evidence_file", read_retained)
    with pytest.raises(passive.PassiveProbeError):
        passive._require_retained_success_evidence(monitor, post, retained)
```

- [ ] **Step 2: Run evidence-binding RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'three_way_trace or retained_success_decision or retained_passive_markers'
```

Expected: existing code validates each observation independently but not their exact equality.

- [ ] **Step 3: Implement exact auxiliary pins and retained-success validation**

```python
def _auxiliary_specs(
    layout: PassiveLayout,
    trace: _TraceObservation | None,
) -> tuple[oracle_boot._AuxiliaryEvidenceSpec, ...]:
    config_stat = os.stat(
        layout.config_path.name,
        dir_fd=layout.evidence_handle.fd,
        follow_symlinks=False,
    )
    if _identity(layout.config_path, config_stat) != layout.config_identity:
        raise PassiveProbeError("passive config identity changed before retention")
    trace_identity = None if trace is None else trace.seal.evidence_identity
    trace_sha256 = None if trace is None else trace.summary.sha256
    return (
        oracle_boot._AuxiliaryEvidenceSpec(
            Path("passive.cfg"),
            "passive_config",
            True,
            64 * 1024,
            oracle_boot._stat_identity(config_stat),
            layout.config_sha256,
        ),
        oracle_boot._AuxiliaryEvidenceSpec(
            Path("passive-trace.ndjson"),
            "passive_trace",
            False,
            128 * 1024 * 1024,
            trace_identity,
            trace_sha256,
        ),
    )


def _require_retained_success_evidence(
    monitor_trace: _TraceObservation,
    post_reap_trace: _TraceObservation,
    retained: oracle_boot._RetainedBootEvidence,
) -> None:
    if monitor_trace != post_reap_trace or monitor_trace.raw_bytes != post_reap_trace.raw_bytes:
        raise PassiveProbeError("monitor and post-reap trace observations differ")
    if retained.decision is None:
        raise PassiveProbeError("retained canonical decision is absent")
    if retained.decision.markers != oracle_boot._REQUIRED_BOOT_MARKERS:
        raise PassiveProbeError("retained canonical boot markers are incomplete")
    if retained.decision.errors or retained.public.issues:
        raise PassiveProbeError("retained canonical evidence has errors or structural issues")
    trace_files = tuple(item for item in retained.files if item.kind == "passive_trace")
    if len(trace_files) != 1:
        raise PassiveProbeError("retained evidence must contain exactly one passive trace")
    trace_file = trace_files[0]
    retained_bytes, retained_fingerprint = oracle_boot._read_retained_evidence_file(
        retained, trace_file
    )
    if (
        trace_file.identity != post_reap_trace.seal.evidence_identity
        or retained_bytes != post_reap_trace.raw_bytes
        or retained_fingerprint.sha256 != post_reap_trace.summary.sha256
        or retained_fingerprint.size != post_reap_trace.summary.size
        or len(retained_bytes) != post_reap_trace.summary.size
    ):
        raise PassiveProbeError("retained trace differs from authenticated post-reap trace")
    canonical_files = tuple(
        item
        for item in retained.files
        if item.kind == "boot_log"
        and oracle_boot._boot_log_kind(item.relative_path) == "canonical"
    )
    if len(canonical_files) != 1:
        raise PassiveProbeError("retained evidence must contain one canonical boot log")
    canonical_bytes, _fingerprint = oracle_boot._read_retained_evidence_file(
        retained, canonical_files[0]
    )
    progress, prompts = _advance_marker_progress(
        canonical_bytes,
        _MarkerProgress((), 0, False),
    )
    if (
        progress.markers != PASSIVE_MARKERS
        or not progress.complete
        or prompts != PASSIVE_INSTRUCTIONS
        or _failure_codes(canonical_bytes)
    ):
        raise PassiveProbeError("retained canonical passive markers are not exact success")
```

- [ ] **Step 4: Run evidence-binding GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'three_way_trace or retained_success_decision or retained_passive_markers'
```

Expected: monitor, post-reap, and retained descriptor observations are exactly equal and canonical success evidence is closed and issue-free.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit success-evidence binding**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: bind passive trace evidence end to end"
```

### Task 19C: Restore success only from the exact healthy patched/passive stage

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_restore_success_stage(preflight, layout, post_process, manifests) -> tuple[PassiveInstallSnapshot, Path | None]`.
- Captures and validates the current installed stage immediately before the first restoration mutation; uncertainty stops before any installer call.

- [ ] **Step 1: Add pre-restore drift and ordered restoration RED tests**

Add this twelve-item matrix. Add `plugin_source_drift`, `plugin_copy_source_drift`, and `plugin_source_race_between_reads`; every source row changes one copy after the current-stage capture and asserts zero installer calls. Every pre-mutation drift row asserts an empty installer-call list; only the explicit final-snapshot row can fail after the two authorized calls:

```python
@pytest.mark.parametrize(
    "case",
    (
        "healthy",
        "status_drift",
        "manifest_drift",
        "plugin_drift",
        "config_drift",
        "assembly_drift",
        "preloader_drift",
        "mode_off_artifact_drift",
        "plugin_source_drift",
        "plugin_copy_source_drift",
        "plugin_source_race_between_reads",
        "final_snapshot_invalid",
    ),
)
def test_restore_success_stage_captures_exact_current_state_before_mutation(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    before = synthetic_preflight.snapshot
    patched_compat = replace(
        before.installer_status.preloader_compatibility,
        state="patched",
        active_sha256=synthetic_preflight.preloader_sha256,
        patched_sha256=synthetic_preflight.preloader_sha256,
    )
    patched_status = replace(
        before.installer_status,
        preloader_compatibility=patched_compat,
    )
    post = replace(
        before,
        legacy=replace(
            before.legacy,
            compatibility_state="patched",
            active_preloader_sha256=synthetic_preflight.preloader_sha256,
        ),
        observed_config_sha256=passive_layout.config_sha256,
        installer_status_before=patched_status,
        installer_status_after=patched_status,
    )
    current = post
    if case == "status_drift":
        current = replace(
            post,
            installer_status_after=replace(post.installer_status_after, changed=("config",)),
        )
    elif case == "manifest_drift":
        changed_status = replace(
            post.installer_status,
            manifest=replace(post.installer_status.manifest, runtime_archive_sha256="9" * 64),
        )
        current = replace(post, installer_status_before=changed_status, installer_status_after=changed_status)
    elif case == "plugin_drift":
        current = replace(post, observed_plugin_sha256="9" * 64)
    elif case == "config_drift":
        current = replace(post, observed_config_sha256="9" * 64)
    elif case == "assembly_drift":
        current = replace(post, legacy=replace(post.legacy, assembly_sha256="9" * 64))
    elif case == "preloader_drift":
        current = replace(
            post,
            legacy=replace(post.legacy, active_preloader_sha256="9" * 64),
        )
    elif case == "mode_off_artifact_drift":
        Path(synthetic_preflight.mode_off_config).write_bytes(b"[Oracle]\nMode = changed\n")

    if case in {
        "plugin_source_drift",
        "plugin_copy_source_drift",
        "plugin_source_race_between_reads",
    }:
        original_artifact = passive._read_artifact
        first_plugin_read = False

        def artifact(path: Path, label: str, maximum: int) -> tuple[bytes, str]:
            nonlocal first_plugin_read
            if case == "plugin_source_drift" and path == synthetic_preflight.plugin:
                return b"changed-primary", sha256(b"changed-primary").hexdigest()
            if (
                case == "plugin_copy_source_drift"
                and path == synthetic_preflight.plugin_verification_copy
            ):
                return b"changed-copy", sha256(b"changed-copy").hexdigest()
            result = original_artifact(path, label, maximum)
            if (
                case == "plugin_source_race_between_reads"
                and path == synthetic_preflight.plugin
                and not first_plugin_read
            ):
                first_plugin_read = True
                synthetic_preflight.plugin_verification_copy.write_bytes(
                    b"changed-between-source-reads"
                )
            return result

        monkeypatch.setattr(passive, "_read_artifact", artifact)

    calls: list[str] = []
    final = before
    if case == "final_snapshot_invalid":
        final = replace(before, observed_config_sha256="9" * 64)
    off_status = replace(
        patched_status,
        manifest=before.installer_status.manifest,
    )
    patched_off = replace(
        post,
        observed_config_sha256=synthetic_preflight.mode_off_config_sha256,
        installer_status_before=off_status,
        installer_status_after=off_status,
    )
    captures = iter((current, patched_off, final))
    monkeypatch.setattr(passive, "_capture_passive_snapshot", lambda _root: next(captures))
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda *_args, **_kwargs: (
            calls.append("mode-off")
            or before.installer_status.manifest
        ),
    )
    monkeypatch.setattr(
        oracle_install,
        "restore_preloader",
        lambda *_args, **_kwargs: (
            calls.append("official")
            or before.installer_status.manifest,
            Path("/private/recovery"),
        ),
    )
    manifests = passive._LifecycleManifests.from_preflight(
        synthetic_preflight
    )
    manifests.patched_passive = post.installer_status.manifest
    if case == "healthy":
        after, recovery = passive._restore_success_stage(
            synthetic_preflight,
            passive_layout,
            post,
            manifests,
        )
        assert after == before
        assert recovery == Path("/private/recovery")
        assert calls == ["mode-off", "official"]
        return
    with pytest.raises(passive.PassiveProbeError):
        passive._restore_success_stage(
            synthetic_preflight,
            passive_layout,
            post,
            manifests,
        )
    if case == "final_snapshot_invalid":
        assert calls == ["mode-off", "official"]
    else:
        assert calls == []
```

- [ ] **Step 2: Run success-restoration RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'restore_success_stage or pre_restore_drift'
```

Expected: the monolithic lifecycle mutates without a fresh exact installed-state capture.

- [ ] **Step 3: Implement the exact success restoration helper**

```python
def _restore_success_stage(
    preflight: PassivePreflight,
    layout: PassiveLayout,
    post_process: PassiveInstallSnapshot,
    manifests: _LifecycleManifests,
) -> tuple[PassiveInstallSnapshot, Path | None]:
    if manifests.patched_passive is None:
        raise PassiveProbeError("patched/passive mutation manifest is unavailable")
    current = _capture_passive_snapshot(preflight.game_root)
    _require_stage_snapshot(
        current,
        compatibility="patched",
        plugin_sha256=preflight.plugin_sha256,
        config_sha256=layout.config_sha256,
        active_preloader_sha256=preflight.preloader_sha256,
        assembly_sha256=preflight.snapshot.legacy.assembly_sha256,
        installer_healthy=preflight.snapshot.legacy.installer_healthy,
        app_signature=preflight.snapshot.legacy.app_signature,
        expected_manifest=manifests.patched_passive,
    )
    if current != post_process:
        raise PassiveProbeError("installed state changed before success restoration")
    plugin_bytes, plugin_hash = _read_artifact(
        preflight.plugin, "plugin restoration source", 64 * 1024 * 1024
    )
    copy_bytes, copy_hash = _read_artifact(
        preflight.plugin_verification_copy,
        "plugin restoration verification copy",
        64 * 1024 * 1024,
    )
    if (
        plugin_bytes != copy_bytes
        or plugin_hash != copy_hash
        or plugin_hash != preflight.plugin_sha256
    ):
        raise PassiveProbeError("plugin restoration sources changed")
    off_bytes, off_hash = _read_artifact(
        preflight.mode_off_config,
        "Mode-off config",
        64 * 1024,
    )
    if off_hash != preflight.mode_off_config_sha256:
        raise PassiveProbeError("Mode-off config changed before restoration")
    off_text = off_bytes.decode("utf-8", "strict")
    # The private byte transaction receives retained authenticated bytes only
    # after both independent copies and the literal pin agree.
    manifests.patched_off = oracle_install._deploy_plugin_bytes(
        preflight.game_root, plugin_bytes, preflight.plugin_sha256, off_text
    )
    patched_off = _capture_passive_snapshot(preflight.game_root)
    _require_stage_snapshot(
        patched_off,
        compatibility="patched",
        plugin_sha256=preflight.plugin_sha256,
        config_sha256=preflight.mode_off_config_sha256,
        active_preloader_sha256=preflight.preloader_sha256,
        assembly_sha256=preflight.snapshot.legacy.assembly_sha256,
        installer_healthy=preflight.snapshot.legacy.installer_healthy,
        app_signature=preflight.snapshot.legacy.app_signature,
        expected_manifest=manifests.patched_off,
    )
    # Reauthenticate both sources again before the independently mutating
    # preloader restoration; a race after Mode-off deployment stops in the
    # resumable patched/off stage.
    second_plugin, second_hash = _read_artifact(
        preflight.plugin, "plugin restoration source", 64 * 1024 * 1024
    )
    second_copy, second_copy_hash = _read_artifact(
        preflight.plugin_verification_copy,
        "plugin restoration verification copy",
        64 * 1024 * 1024,
    )
    if (
        second_plugin != second_copy
        or second_hash != second_copy_hash
        or second_hash != preflight.plugin_sha256
    ):
        raise PassiveProbeError("plugin restoration sources changed before preloader restore")
    manifests.official_off, recovery_dir = oracle_install.restore_preloader(
        preflight.game_root
    )
    after = _capture_passive_snapshot(preflight.game_root)
    _require_stage_snapshot(
        after,
        compatibility="official",
        plugin_sha256=preflight.plugin_sha256,
        config_sha256=preflight.mode_off_config_sha256,
        active_preloader_sha256=preflight.snapshot.legacy.active_preloader_sha256,
        assembly_sha256=preflight.snapshot.legacy.assembly_sha256,
        installer_healthy=preflight.snapshot.legacy.installer_healthy,
        app_signature=preflight.snapshot.legacy.app_signature,
        expected_manifest=manifests.official_off,
    )
    if after.legacy.assembly_sha256 != preflight.snapshot.legacy.assembly_sha256:
        raise PassiveProbeError("game assembly changed across passive restoration")
    return after, recovery_dir
```

- [ ] **Step 4: Run success-restoration GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'restore_success_stage or pre_restore_drift'
```

Expected: mutation begins only from exact healthy patched/passive state and ends exact healthy official/Mode-off.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit exact success restoration**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: restore exact passive success state"
```

### Task 19D: Orchestrate one successful launch and publish after all owners close

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces private `_run_passive_probe_lifecycle(...) -> PassiveProbeResult` with all ten request parameters required. The public mutating `run_passive_probe` name remains absent until Task 20C installs complete failure restoration.
- Acquires one launcher, tracks descendants during every monitor poll, reaps before installer restoration, stages evidence before restoration, closes every success-sensitive lifecycle owner, and exclusively commits JSON last.

- [ ] **Step 1: Add one-launch/order/close/publication RED matrix**

Retain the complete one-launch event-order test in Task 19A and add these nine independently collected owner/publication cases. This body contains the faulting owners and publication doubles; no external harness is implied:

```python
@pytest.mark.parametrize(
    "case",
    (
        "all_close",
        "launcher_close",
        "logging_close",
        "retained_close",
        "layout_close",
        "staged_close",
        "stage_failure",
        "commit_failure",
        "no_retry",
    ),
)
def test_success_owner_close_and_json_last_matrix(
    passive_result: passive.PassiveProbeResult,
    passive_layout: passive.PassiveLayout,
    retained_evidence: oracle_boot._RetainedBootEvidence,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    events: list[str] = []
    calls: dict[str, int] = {}

    def operation(name: str) -> Callable[[], None]:
        def run() -> None:
            calls[name] = calls.get(name, 0) + 1
            events.append(name)
            if case == name:
                raise OSError(f"{name} failed")
        return run

    if case in {
        "all_close", "launcher_close", "logging_close", "retained_close",
        "layout_close", "no_retry",
    }:
        selected = "launcher_close" if case == "no_retry" else case
        operations = tuple(
            (name, operation(name))
            for name in (
                "launcher_close", "logging_close", "retained_close", "layout_close"
            )
        )
        original_case = case
        if case == "no_retry":
            case = selected
        primary = passive._close_all_owners(operations)
        assert events == [name for name, _operation in operations]
        assert all(count == 1 for count in calls.values())
        if original_case == "all_close":
            assert primary is None
        else:
            assert isinstance(primary, OSError)
            assert str(primary) == f"{selected} failed"
        return

    if case == "stage_failure":
        primary = OSError("stage failed")
        monkeypatch.setattr(
            oracle_boot,
            "_stage_probe_json",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(primary),
        )
        with pytest.raises(OSError) as caught:
            passive._stage_passive_result(passive_result, passive_layout, retained_evidence)
        assert caught.value is primary
        return

    staged = SimpleNamespace()
    commit_primary = OSError("commit failed")
    close_primary = OSError("staged close failed")
    monkeypatch.setattr(
        oracle_boot,
        "_commit_staged_probe_json",
        lambda observed: (
            events.append("commit"),
            setattr(observed, "committed", True),
        )
        if case == "staged_close"
        else (_ for _ in ()).throw(commit_primary),
    )
    monkeypatch.setattr(
        oracle_boot,
        "_close_staged_probe_json",
        lambda observed: (
            events.append("close"),
            None
            if observed.committed
            else (_ for _ in ()).throw(close_primary),
        )[1],
    )
    if case == "staged_close":
        passive._commit_staged_passive_result(staged)
        assert staged.committed is True
        assert events == ["commit", "close"]
        return
    with pytest.raises(OSError) as caught:
        passive._commit_staged_passive_result(staged)
    assert caught.value is commit_primary
    assert events == ["close"]
    assert any("staged JSON close failure" in note for note in commit_primary.__notes__)
```

- [ ] **Step 2: Run successful lifecycle RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'success_lifecycle or success_owner_close or success_json_last'
```

Expected: lifecycle ordering, exact trace binding, or owner-before-commit safety is incomplete.

- [ ] **Step 3: Implement the complete successful orchestration**

```python
def _close_all_owners(
    operations: tuple[tuple[str, Callable[[], object]], ...],
    primary: BaseException | None = None,
) -> BaseException | None:
    owned_primary = primary
    for stage, operation in operations:
        try:
            operation()
        except BaseException as error:
            if owned_primary is None:
                owned_primary = error
            else:
                try:
                    owned_primary.add_note(
                        f"secondary passive failure during {stage}: {type(error).__name__}: {error}"
                    )
                except BaseException:
                    pass
    return owned_primary


def _run_passive_probe_lifecycle(
    game_root: Path,
    launcher: Path,
    mode_off_config: Path,
    plugin: Path,
    plugin_verification_copy: Path,
    expected_plugin_sha256: str,
    preloader: Path,
    provenance: Path,
    evidence_root: Path,
    timeout_seconds: int,
    *,
    instruction_sink: Callable[[str], None] = lambda line: print(line, file=sys.stderr, flush=True),
) -> PassiveProbeResult:
    started = _utc_timestamp()
    preflight = preflight_passive_probe(
        game_root,
        launcher,
        mode_off_config,
        plugin,
        plugin_verification_copy,
        expected_plugin_sha256,
        preloader,
        provenance,
        evidence_root,
        timeout_seconds,
    )
    manifests = _LifecycleManifests.from_preflight(preflight)
    logging_guard = oracle_boot._open_bepinex_disk_logging_guard(preflight.game_root)
    layout: PassiveLayout | None = None
    launcher_guard: _LauncherOwnership | None = None
    retained: oracle_boot._RetainedBootEvidence | None = None
    staged: oracle_boot._StagedProbeJson | None = None
    try:
        layout = _allocate_passive_layout(preflight.evidence_root)
        passive_bytes, passive_hash = _read_artifact(
            layout.config_path,
            "passive config",
            64 * 1024,
        )
        if passive_hash != layout.config_sha256:
            raise PassiveProbeError("passive config changed before deployment")
        passive_text = passive_bytes.decode("utf-8", "strict")
        authenticated_plugin = _revalidate_pre_mutation(preflight, layout)
        manifests.official_passive = oracle_install._deploy_plugin_bytes(
            preflight.game_root,
            authenticated_plugin,
            preflight.plugin_sha256,
            passive_text,
        )
        manifests.patched_passive = oracle_install.deploy_preloader(
            preflight.game_root,
            preflight.preloader,
            preflight.provenance,
        )
        patched = _capture_passive_snapshot(preflight.game_root)
        _require_stage_snapshot(
            patched,
            compatibility="patched",
            plugin_sha256=preflight.plugin_sha256,
            config_sha256=layout.config_sha256,
            active_preloader_sha256=preflight.preloader_sha256,
            assembly_sha256=preflight.snapshot.legacy.assembly_sha256,
            installer_healthy=preflight.snapshot.legacy.installer_healthy,
            app_signature=preflight.snapshot.legacy.app_signature,
            expected_manifest=manifests.patched_passive,
        )
        if fingerprint_save_tree(Path(preflight.ordinary_save.path)) != preflight.ordinary_save:
            raise PassiveProbeError("ordinary save changed before launch")
        _require_empty_isolated_save(layout)
        run_contract = oracle_boot._verify_and_close_bepinex_disk_logging_guard(logging_guard)
        logging_guard = None
        launcher_guard = _acquire_launcher(preflight)
        if launcher_guard.process is None:
            raise AssertionError("new launcher guard has no process")
        spawned_pid = launcher_guard.process.pid
        spawned_pgid = launcher_guard.pgid
        process_tracker = _process_tracker_for_preflight(
            preflight,
            spawned_pid,
            spawned_pgid,
        )
        monitor = _wait_for_passive_trace(
            launcher_guard.process,
            preflight.game_root,
            preflight.before_logs,
            layout,
            preflight.timeout_seconds,
            instruction_sink,
            process_tracker,
        )
        exit_code = launcher_guard.close()
        launcher_guard = None
        _require_no_matching_processes_for_preflight(
            preflight,
            process_tracker,
        )
        if monitor.state != "complete":
            raise PassiveProbeError(f"passive monitor ended in state {monitor.state}")
        post_process = _capture_passive_snapshot(preflight.game_root)
        _require_stage_snapshot(
            post_process,
            compatibility="patched",
            plugin_sha256=preflight.plugin_sha256,
            config_sha256=layout.config_sha256,
            active_preloader_sha256=preflight.preloader_sha256,
            assembly_sha256=preflight.snapshot.legacy.assembly_sha256,
            installer_healthy=preflight.snapshot.legacy.installer_healthy,
            app_signature=preflight.snapshot.legacy.app_signature,
            expected_manifest=manifests.patched_passive,
        )
        trace = _retain_post_reap_trace(layout)
        if monitor.trace is None or trace is None or trace.run is None:
            raise PassiveProbeError("successful monitor has no retained trace")
        if monitor.trace != trace or monitor.trace.raw_bytes != trace.raw_bytes:
            raise PassiveProbeError("monitor and post-reap trace observations differ")
        require_passive_success(trace.run)
        isolated_save = _secure_isolated_save_tree(layout)
        if not isolated_save.safe:
            raise PassiveProbeError("isolated save inventory is unsafe")
        retained = oracle_boot._collect_boot_evidence_into(
            preflight.before_logs,
            preflight.game_root,
            layout.evidence_dir,
            layout.evidence_handle,
            expected_inventory=preflight.log_inventory,
            run_contract=run_contract,
            observed_failures=monitor.observed_failures,
            auxiliary_specs=_auxiliary_specs(layout, trace),
        )
        _require_retained_success_evidence(monitor.trace, trace, retained)
        if monitor.issues:
            raise PassiveProbeError("successful monitor retained structural issues")
        ordinary_after = fingerprint_save_tree(Path(preflight.ordinary_save.path))
        if ordinary_after != preflight.ordinary_save:
            raise PassiveProbeError("ordinary save proof changed after process exit")
        after, recovery_dir = _restore_success_stage(
            preflight,
            layout,
            post_process,
            manifests,
        )
        _require_no_matching_processes_for_preflight(preflight, process_tracker)
        ordinary_final = fingerprint_save_tree(Path(preflight.ordinary_save.path))
        if ordinary_after != preflight.ordinary_save or ordinary_final != preflight.ordinary_save:
            raise PassiveProbeError("ordinary save proof changed")
        trace_summary = trace.summary
        run_id = trace.run.header.run_id
        result = PassiveProbeResult(
            success=True,
            started_at_utc=started,
            finished_at_utc=_utc_timestamp(),
            controller_pid=os.getpid(),
            game_root=preflight.game_root,
            macos_product_version=preflight.macos_product_version,
            launcher=preflight.launcher,
            evidence_dir=layout.evidence_dir,
            isolated_save_dir=layout.isolated_save_dir,
            plugin_sha256=preflight.plugin_sha256,
            mode_off_config_sha256=preflight.mode_off_config_sha256,
            passive_config_sha256=layout.config_sha256,
            markers=monitor.markers,
            issues=(),
            secondary_errors=(),
            exit_code=exit_code,
            run_id=run_id,
            cleanup=PassiveCleanup(True, True, True, True, True, True),
            before=preflight.snapshot,
            patched=patched,
            post_process=post_process,
            after=after,
            before_logs=preflight.before_logs,
            after_logs=tuple(item.fingerprint for item in retained.files if item.kind == "boot_log"),
            ordinary_save_before=preflight.ordinary_save,
            ordinary_save_after=ordinary_after,
            ordinary_save_final=ordinary_final,
            isolated_save=isolated_save,
            trace=trace_summary,
            copied_logs=retained.public.copied_logs,
            moved_logs=retained.public.moved_logs,
            restore_recovery_dir=recovery_dir,
        )
        staged = _stage_passive_result(result, layout, retained)
        close_error = _close_all_owners(
            (
                ("retained evidence close", retained.close),
                ("passive layout close", layout.close),
            )
        )
        if close_error is not None:
            _close_all_owners(
                (("staged JSON close", lambda: oracle_boot._close_staged_probe_json(staged)),),
                close_error,
            )
            raise close_error
        retained = None
        layout = None
        _commit_staged_passive_result(staged)
        staged = None
        return result
    finally:
        active = sys.exception()
        operations: list[tuple[str, Callable[[], object]]] = []
        if launcher_guard is not None:
            operations.append(("launcher guard close", launcher_guard.close))
        if logging_guard is not None:
            operations.append(("logging guard close", logging_guard.close))
        if retained is not None:
            operations.append(("retained evidence close", retained.close))
        if layout is not None:
            operations.append(("passive layout close", layout.close))
        if staged is not None:
            operations.append(
                ("staged JSON close", lambda: oracle_boot._close_staged_probe_json(staged))
            )
        close_primary = _close_all_owners(tuple(operations), active)
        if active is None and close_primary is not None:
            raise close_primary
```

- [ ] **Step 4: Run successful lifecycle GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'success_lifecycle or success_owner_close_and_json_last_matrix'
```

Expected: the private lifecycle has one launcher, four prompt phases/five physical events, a fresh exact pre-mutation gate, exact three-way trace evidence, Mode-off/official restoration, all-owner close accumulation, and exclusive JSON-last publication. The public `run_passive_probe` symbol is still absent.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the successful lifecycle gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "feat: orchestrate successful passive oracle capture"
```

### Task 20A: Retain complete failure-lifecycle ownership and primary identity

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Adds `_LifecycleState` and deterministic `_record_secondary`; all process, log, evidence, layout, tracker, staged-JSON, and restoration state stays cleanup-reachable until its close/mutation call succeeds.

- [ ] **Step 1: Add only lifecycle-state/secondary-ownership RED tests**

Register only the three `test_failure_state_ownership_records_secondary_without_replacing_primary` parameter rows in this task. The two failure-finalizer tests and three process-level-primary rows shown below are reserved for Task 20C, where `_finish_failed_lifecycle` exists; they must not be collected or selected in Task 20A.

```python
@dataclass
class FailureGuard:
    process: FakeProcess | None = field(default_factory=FakeProcess)
    pgid: int = 9501
    close_count: int = 0

    def close(self) -> int:
        self.close_count += 1
        self.process = None
        return 23


def _failure_state(
    preflight: passive.PassivePreflight,
    layout: passive.PassiveLayout,
    guard: FailureGuard,
) -> passive._LifecycleState:
    return passive._LifecycleState(
        preflight=preflight,
        started_at_utc="2026-07-31T19:09:50.319910Z",
        layout=layout,
        logging_guard=None,
        launcher_guard=guard,
    )


def _install_failure_finalizer_fakes(
    monkeypatch: pytest.MonkeyPatch,
    preflight: passive.PassivePreflight,
    retained: object,
    calls: list[str],
    *,
    restore_error: BaseException | None = None,
) -> None:
    monkeypatch.setattr(passive, "_require_no_matching_processes_for_preflight", lambda *_args: calls.append("processes") or ())
    monkeypatch.setattr(passive, "_retain_post_reap_trace", lambda _layout: calls.append("trace") or None)
    monkeypatch.setattr(
        passive,
        "_secure_isolated_save_tree",
        lambda _layout: calls.append("isolated")
        or passive.IsolatedSaveObservation((), True, (), 0, False),
    )
    monkeypatch.setattr(passive, "fingerprint_save_tree", lambda _path: calls.append("ordinary") or preflight.ordinary_save)
    monkeypatch.setattr(oracle_boot, "_collect_boot_evidence_into", lambda *_args, **_kwargs: retained)
    def restore_stage(state: passive._LifecycleState) -> None:
        calls.extend(("mode-off", "restore"))
        if restore_error is not None:
            raise restore_error
        state.mode_off_restored = True
        state.official_preloader_restored = True
        state.installed_status_healthy = True
        state.after = preflight.snapshot
        state.recovery_dir = preflight.game_root / ".ssr-oracle-recovery/test"

    monkeypatch.setattr(passive, "_restore_failure_stage", restore_stage)
    monkeypatch.setattr(passive, "_capture_passive_snapshot", lambda _root: preflight.snapshot)
    monkeypatch.setattr(passive, "_require_stage_snapshot", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        passive,
        "_stage_passive_result",
        lambda *_args: calls.append("stage") or SimpleNamespace(),
    )
    monkeypatch.setattr(
        passive,
        "_commit_staged_passive_result",
        lambda _staged: calls.append("publish"),
    )


def test_failure_finalizer_never_retries_and_publishes_only_after_safe_evidence(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = FailureGuard()
    retained = SimpleNamespace(
        files=(),
        public=SimpleNamespace(copied_logs=(), moved_logs=()),
        close=lambda: calls.append("retained-close"),
    )
    calls: list[str] = []
    _install_failure_finalizer_fakes(
        monkeypatch,
        synthetic_preflight,
        retained,
        calls,
    )
    result = passive._finish_failed_lifecycle(
        _failure_state(synthetic_preflight, passive_layout, guard),
        passive.PassiveProbeError("monitor failed"),
    )
    assert result.success is False
    assert guard.close_count == 1
    assert calls.count("mode-off") == calls.count("restore") == 1
    assert calls[-1] == "publish"


def test_safe_failure_result_records_restore_failure_without_retry(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = FailureGuard(process=None)
    retained = SimpleNamespace(
        files=(),
        public=SimpleNamespace(copied_logs=(), moved_logs=()),
        close=lambda: calls.append("retained-close"),
    )
    calls: list[str] = []
    _install_failure_finalizer_fakes(
        monkeypatch,
        synthetic_preflight,
        retained,
        calls,
        restore_error=passive.PassiveProbeError("restore stopped"),
    )
    primary = passive.PassiveProbeError("monitor failed")
    with pytest.raises(passive.PassiveProbeError) as caught:
        passive._finish_failed_lifecycle(
            _failure_state(synthetic_preflight, passive_layout, guard),
            primary,
        )
    assert caught.value is primary
    assert calls.count("restore") == 1
    assert "publish" not in calls


@pytest.mark.parametrize(
    "primary",
    (KeyboardInterrupt("stop"), SystemExit(76), GeneratorExit("stop")),
)
def test_process_level_primary_is_re_raised_by_identity_after_cleanup(
    complete_preflight_request: dict[str, object],
    synthetic_preflight: passive.PassivePreflight,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    primary: BaseException,
) -> None:
    calls: list[str] = []
    retained = SimpleNamespace(
        files=(),
        public=SimpleNamespace(copied_logs=(), moved_logs=()),
        close=lambda: calls.append("retained-close"),
    )
    _install_failure_finalizer_fakes(
        monkeypatch,
        synthetic_preflight,
        retained,
        calls,
    )
    layout = SimpleNamespace(
        config_sha256="7" * 64,
        evidence_dir=tmp_path / "evidence",
        evidence_handle=object(),
        isolated_save_dir=tmp_path / "isolated",
        close=lambda: calls.append("layout-close"),
    )
    logging_guard = SimpleNamespace(close=lambda: calls.append("logging-close"))
    monkeypatch.setattr(
        passive,
        "preflight_passive_probe",
        lambda *_args, **_kwargs: synthetic_preflight,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_open_bepinex_disk_logging_guard",
        lambda _root: logging_guard,
    )
    monkeypatch.setattr(passive, "_allocate_passive_layout", lambda _root: layout)
    monkeypatch.setattr(passive, "_auxiliary_specs", lambda *_args: ())
    monkeypatch.setattr(
        passive,
        "_read_artifact",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(primary),
    )
    with pytest.raises(BaseException) as caught:
        passive._run_passive_probe_lifecycle(**complete_preflight_request)
    assert caught.value is primary
    assert calls.count("restore") == 1
    assert calls.count("logging-close") == 1
    assert calls.count("retained-close") == 1
    assert calls.count("layout-close") == 1
    assert "publish" not in calls


@pytest.mark.parametrize(
    "secondary",
    (OSError("close failed"), KeyboardInterrupt("interrupted"), GeneratorExit("stopped")),
)
def test_failure_state_ownership_records_secondary_without_replacing_primary(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    secondary: BaseException,
) -> None:
    state = _failure_state(synthetic_preflight, passive_layout, FailureGuard())
    primary = RuntimeError("first failure")
    passive._record_secondary(state, primary, "owner-close", secondary)
    assert state.secondary_errors == [
        passive.SecondaryError("owner-close", type(secondary).__name__, str(secondary))
    ]
    assert any(
        f"secondary passive failure during owner-close: {secondary}" in note
        for note in primary.__notes__
    )
```

- [ ] **Step 2: Run failure-lifecycle RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'failure_state_ownership'
```

Expected: `_LifecycleState` or `_record_secondary` is missing. No failure-finalizer test is collected yet.

- [ ] **Step 3: Add explicit lifecycle state and failure finalization**

Add the complete state model:

```python
from dataclasses import field


@dataclass(slots=True)
class _LifecycleState:
    preflight: PassivePreflight
    started_at_utc: str
    layout: PassiveLayout
    logging_guard: oracle_boot._DiskLoggingConfigGuard | None
    manifests: _LifecycleManifests | None = None
    launcher_guard: _LauncherOwnership | None = None
    process_tracker: _ObservedProcessTracker | None = None
    monitor: _PassiveMonitorOutcome | None = None
    retained: oracle_boot._RetainedBootEvidence | None = None
    patched: PassiveInstallSnapshot | None = None
    post_process: PassiveInstallSnapshot | None = None
    after: PassiveInstallSnapshot | None = None
    ordinary_after: SaveTreeProof | None = None
    ordinary_final: SaveTreeProof | None = None
    isolated_save: IsolatedSaveObservation | None = None
    trace: _TraceObservation | None = None
    trace_retention_complete: bool = False
    recovery_dir: Path | None = None
    exit_code: int | None = None
    process_group_stopped: bool = False
    no_matching_processes: bool = False
    mode_off_restored: bool = False
    official_preloader_restored: bool = False
    installed_status_healthy: bool = False
    ordinary_save_unchanged: bool = False
    post_evidence_safe: bool = False
    restore_stage: Literal[
        "already_restored",
        "official_passive",
        "patched_passive",
        "patched_off",
    ] | None = None
    staged_json: oracle_boot._StagedProbeJson | None = None
    layout_open: bool = True
    finalized: bool = False
    secondary_errors: list[SecondaryError] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.manifests is None:
            self.manifests = _LifecycleManifests.from_preflight(self.preflight)
```

Add deterministic secondary capture:

```python
def _record_secondary(
    state: _LifecycleState,
    primary: BaseException,
    stage: str,
    secondary: BaseException,
) -> None:
    state.secondary_errors.append(
        SecondaryError(stage, type(secondary).__name__, str(secondary))
    )
    try:
        primary.add_note(f"secondary passive failure during {stage}: {secondary}")
    except BaseException:
        return
```

- [ ] **Step 4: Run failure-ownership GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'failure_state_ownership'
```

Expected: every owner remains reachable through interruption and all close failures attach to the identical first primary.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit failure ownership**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "fix: retain passive failure ownership"
```

### Task 20B: Classify the exact current installed stage before restoration

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_classify_failure_restore_stage` with exactly four healthy states and `_restore_failure_stage`.
- Captures the current complete installed snapshot immediately before the first mutation. Invalid status, uncertain config, process uncertainty, or any unrecognized partial stage stops with zero further installer mutation.

- [ ] **Step 1: Add exact stage-classification/restoration RED matrix**

Add this twenty-one-item closed matrix. `patched_off` is accepted as the resumable intermediate and performs only official-preloader restoration. The two explicit interruption rows stop after successful Mode-off deployment and before/during official restore; the resumed call classifies `patched_off`, never redeploys Mode-off, and attempts official restore once. Independent coherent-manifest-entry, legacy-installer-health, and app-signature drift rows stop before mutation. Every accepted, rejected, and interrupted branch is constructed without a generic fault installer:

```python
@pytest.mark.parametrize(
    "case",
    (
        "already_restored", "official_passive", "patched_passive", "patched_off",
        "process_uncertain", "unhealthy", "runtime_manifest_drift",
        "manifest_entry_drift", "legacy_health_drift", "signature_drift",
        "plugin_drift", "unknown_config", "assembly_drift",
        "official_preloader_drift", "patched_preloader_drift",
        "unknown_compatibility",
        "deploy_failure", "restore_failure", "final_snapshot_failure",
    ),
)
def test_failure_restoration_accepts_only_three_exact_current_stages(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    off = synthetic_preflight.snapshot
    official_passive = replace(off, observed_config_sha256=passive_layout.config_sha256)
    patched_compat = replace(
        off.installer_status.preloader_compatibility,
        state="patched",
        active_sha256=synthetic_preflight.preloader_sha256,
        patched_sha256=synthetic_preflight.preloader_sha256,
    )
    patched_status = replace(off.installer_status, preloader_compatibility=patched_compat)
    patched = replace(
        official_passive,
        legacy=replace(
            off.legacy,
            compatibility_state="patched",
            active_preloader_sha256=synthetic_preflight.preloader_sha256,
        ),
        installer_status_before=patched_status,
        installer_status_after=patched_status,
    )
    current = {
        "already_restored": off,
        "official_passive": official_passive,
        "patched_passive": patched,
        "deploy_failure": official_passive,
        "restore_failure": patched,
        "final_snapshot_failure": official_passive,
    }.get(case, official_passive)
    if case == "unhealthy":
        unhealthy = replace(current.installer_status, missing=("plugin",))
        current = replace(current, installer_status_before=unhealthy, installer_status_after=unhealthy)
    elif case == "runtime_manifest_drift":
        drift = replace(
            current.installer_status,
            manifest=replace(current.installer_status.manifest, runtime_archive_sha256="9" * 64),
        )
        current = replace(current, installer_status_before=drift, installer_status_after=drift)
    elif case == "manifest_entry_drift":
        manifest = current.installer_status.manifest
        drift = replace(
            current.installer_status,
            manifest=replace(
                manifest,
                entries=manifest.entries
                + (
                    oracle_install.ManifestEntry(
                        "coherent-but-unreviewed",
                        "file",
                        "9" * 64,
                    ),
                ),
            ),
        )
        current = replace(
            current,
            installer_status_before=drift,
            installer_status_after=drift,
        )
    elif case == "legacy_health_drift":
        current = replace(
            current,
            legacy=replace(current.legacy, installer_healthy=False),
        )
    elif case == "signature_drift":
        current = replace(
            current,
            legacy=replace(
                current.legacy,
                app_signature=oracle_boot._AppSignature(
                    1,
                    "invalid",
                    "signature drift",
                ),
            ),
        )
    elif case == "plugin_drift":
        current = replace(current, observed_plugin_sha256="9" * 64)
    elif case == "unknown_config":
        current = replace(current, observed_config_sha256="9" * 64)
    elif case == "assembly_drift":
        current = replace(current, legacy=replace(current.legacy, assembly_sha256="9" * 64))
    elif case == "official_preloader_drift":
        current = replace(
            official_passive,
            legacy=replace(official_passive.legacy, active_preloader_sha256="9" * 64),
        )
    elif case == "patched_preloader_drift":
        current = replace(
            patched,
            legacy=replace(patched.legacy, active_preloader_sha256="9" * 64),
        )
    elif case == "patched_off":
        current = replace(patched, observed_config_sha256=off.observed_config_sha256)
    elif case == "unknown_compatibility":
        current = replace(
            official_passive,
            legacy=replace(official_passive.legacy, compatibility_state="unknown"),
        )

    state = passive._LifecycleState(
        preflight=synthetic_preflight,
        started_at_utc="2026-07-31T19:09:50.319910Z",
        layout=passive_layout,
        logging_guard=None,
    )
    assert state.manifests is not None
    state.manifests.official_passive = official_passive.installer_status.manifest
    state.manifests.patched_passive = patched.installer_status.manifest
    state.manifests.patched_off = patched.installer_status.manifest
    state.no_matching_processes = case != "process_uncertain"
    calls: list[str] = []
    final = off if case != "final_snapshot_failure" else replace(
        off, observed_config_sha256="9" * 64
    )
    mode_off_snapshot = (
        off
        if current.legacy.compatibility_state == "official"
        else replace(
            patched,
            observed_config_sha256=synthetic_preflight.mode_off_config_sha256,
        )
    )
    captures = iter(
        (current, mode_off_snapshot, final)
        if case in {"official_passive", "patched_passive", "restore_failure", "final_snapshot_failure"}
        else (current, final)
    )
    monkeypatch.setattr(passive, "_capture_passive_snapshot", lambda _root: next(captures))
    deploy_primary = OSError("deploy failed")
    restore_primary = OSError("restore failed")

    def deploy(*_args: object, **_kwargs: object):
        calls.append("deploy_off")
        if case == "deploy_failure":
            raise deploy_primary
        return off.installer_status.manifest

    def restore(*_args: object, **_kwargs: object) -> tuple[object, Path]:
        calls.append("restore_official")
        if case == "restore_failure":
            raise restore_primary
        return off.installer_status.manifest, Path("/private/recovery")

    monkeypatch.setattr(oracle_install, "_deploy_plugin_bytes", deploy)
    monkeypatch.setattr(oracle_install, "restore_preloader", restore)
    accepted = {
        "already_restored": [],
        "official_passive": ["deploy_off"],
        "patched_passive": ["deploy_off", "restore_official"],
        "patched_off": ["restore_official"],
    }
    if case in accepted:
        passive._restore_failure_stage(state)
        assert calls == accepted[case]
        return
    with pytest.raises(BaseException):
        passive._restore_failure_stage(state)
    if case == "deploy_failure":
        assert calls == ["deploy_off"]
    elif case == "restore_failure":
        assert calls == ["deploy_off", "restore_official"]
    elif case == "final_snapshot_failure":
        assert calls == ["deploy_off"]
    else:
        assert calls == []


@pytest.mark.parametrize("boundary", ("before_restore", "during_restore"))
def test_failure_restoration_resumes_patched_off_without_redeploy(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    off = synthetic_preflight.snapshot
    patched_compat = replace(
        off.installer_status.preloader_compatibility,
        state="patched",
        active_sha256=synthetic_preflight.preloader_sha256,
        patched_sha256=synthetic_preflight.preloader_sha256,
    )
    patched_status = replace(
        off.installer_status,
        preloader_compatibility=patched_compat,
    )
    patched_passive = replace(
        off,
        legacy=replace(
            off.legacy,
            compatibility_state="patched",
            active_preloader_sha256=synthetic_preflight.preloader_sha256,
        ),
        observed_config_sha256=passive_layout.config_sha256,
        installer_status_before=patched_status,
        installer_status_after=patched_status,
    )
    patched_off = replace(
        patched_passive,
        observed_config_sha256=synthetic_preflight.mode_off_config_sha256,
    )
    captures = iter((patched_passive, patched_off, patched_off, off))
    calls: list[str] = []
    restore_calls = 0
    state = passive._LifecycleState(
        preflight=synthetic_preflight,
        started_at_utc="2026-07-31T19:09:50.319910Z",
        layout=passive_layout,
        logging_guard=None,
        no_matching_processes=True,
    )
    assert state.manifests is not None
    state.manifests.patched_passive = patched_passive.installer_status.manifest

    def artifact(path: Path, _label: str, _maximum: int) -> tuple[bytes, str]:
        if path == synthetic_preflight.mode_off_config:
            return b"mode = off\n", synthetic_preflight.mode_off_config_sha256
        return b"reviewed-plugin", synthetic_preflight.plugin_sha256

    def restore(_root: Path) -> tuple[object, Path]:
        nonlocal restore_calls
        restore_calls += 1
        calls.append("restore")
        if restore_calls == 1:
            if boundary == "during_restore":
                calls.append("restore-mutated")
            raise OSError(f"interrupted {boundary}")
        return off.installer_status.manifest, Path("/private/recovery")

    monkeypatch.setattr(passive, "_capture_passive_snapshot", lambda _root: next(captures))
    monkeypatch.setattr(passive, "_read_artifact", artifact)
    monkeypatch.setattr(
        oracle_install,
        "_deploy_plugin_bytes",
        lambda *_args, **_kwargs: (
            calls.append("deploy_off")
            or patched_off.installer_status.manifest
        ),
    )
    monkeypatch.setattr(oracle_install, "restore_preloader", restore)
    with pytest.raises(OSError, match="interrupted"):
        passive._restore_failure_stage(state)
    passive._restore_failure_stage(state)
    assert calls.count("deploy_off") == 1
    assert calls.count("restore") == 2
    assert state.restore_stage == "patched_off"
    assert state.after == off
```

- [ ] **Step 2: Run restoration-classification RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'failure_restoration'
```

Expected: the old finalizer always deploys Mode-off and may mutate an unclassified state.

- [ ] **Step 3: Implement the closed stage classifier and restoration helper**

```python
def _classify_failure_restore_stage(
    state: _LifecycleState,
    current: PassiveInstallSnapshot,
) -> Literal["already_restored", "official_passive", "patched_passive", "patched_off"]:
    if not current.installer_status.healthy:
        raise PassiveProbeError("current installer state is unhealthy; restoration stopped")
    baseline = state.preflight.snapshot
    if (
        not current.legacy.installer_healthy
        or current.legacy.installer_healthy != current.installer_status.healthy
    ):
        raise PassiveProbeError("current legacy installer health is uncertain; restoration stopped")
    if current.legacy.app_signature != baseline.legacy.app_signature:
        raise PassiveProbeError("current application signature is uncertain; restoration stopped")
    if current.legacy.assembly_sha256 != baseline.legacy.assembly_sha256:
        raise PassiveProbeError("current assembly is uncertain; restoration stopped")
    if current.observed_plugin_sha256 != state.preflight.plugin_sha256:
        raise PassiveProbeError("current plugin is uncertain; restoration stopped")
    compatibility = current.legacy.compatibility_state
    config = current.observed_config_sha256
    stage: Literal[
        "already_restored",
        "official_passive",
        "patched_passive",
        "patched_off",
    ]
    if compatibility == "official" and config == state.preflight.mode_off_config_sha256:
        if (
            current.legacy.active_preloader_sha256
            != state.preflight.snapshot.legacy.active_preloader_sha256
        ):
            raise PassiveProbeError("current official preloader is uncertain; restoration stopped")
        stage = "already_restored"
    elif compatibility == "official" and config == state.layout.config_sha256:
        if (
            current.legacy.active_preloader_sha256
            != state.preflight.snapshot.legacy.active_preloader_sha256
        ):
            raise PassiveProbeError("current official preloader is uncertain; restoration stopped")
        stage = "official_passive"
    elif compatibility == "patched" and config == state.layout.config_sha256:
        if current.legacy.active_preloader_sha256 != state.preflight.preloader_sha256:
            raise PassiveProbeError("current patched preloader is uncertain; restoration stopped")
        stage = "patched_passive"
    elif compatibility == "patched" and config == state.preflight.mode_off_config_sha256:
        if current.legacy.active_preloader_sha256 != state.preflight.preloader_sha256:
            raise PassiveProbeError("current patched preloader is uncertain; restoration stopped")
        stage = "patched_off"
    else:
        raise PassiveProbeError(
            "unrecognized current restore stage: "
            f"compatibility={compatibility}, config={config}"
        )
    if state.manifests is None:
        raise PassiveProbeError("lifecycle mutation manifests are unavailable")
    expected_manifest = {
        "already_restored": state.manifests.official_off,
        "official_passive": state.manifests.official_passive,
        "patched_passive": state.manifests.patched_passive,
        "patched_off": state.manifests.patched_off,
    }[stage]
    if expected_manifest is None:
        raise PassiveProbeError(
            f"exact mutation manifest for {stage} is unavailable; restoration stopped"
        )
    baseline_manifest = baseline.installer_status.manifest
    if (
        expected_manifest.game_assembly_sha256
        != baseline_manifest.game_assembly_sha256
        or expected_manifest.runtime_archive_sha256
        != baseline_manifest.runtime_archive_sha256
    ):
        raise PassiveProbeError("stage manifest violates retained runtime pins")
    if current.installer_status.manifest != expected_manifest:
        raise PassiveProbeError(
            f"current manifest differs from exact {stage} mutation result"
        )
    return stage


def _restore_failure_stage(state: _LifecycleState) -> None:
    if not state.no_matching_processes:
        raise PassiveProbeError("process cleanup is uncertain; restoration stopped")
    current = _capture_passive_snapshot(state.preflight.game_root)
    stage = _classify_failure_restore_stage(state, current)
    state.restore_stage = stage
    if state.manifests is None:
        raise PassiveProbeError("lifecycle mutation manifests are unavailable")
    off_bytes, off_hash = _read_artifact(
        state.preflight.mode_off_config,
        "Mode-off config",
        64 * 1024,
    )
    if off_hash != state.preflight.mode_off_config_sha256:
        raise PassiveProbeError("Mode-off restoration artifact is uncertain")
    if stage in {"official_passive", "patched_passive"}:
        source_bytes, source_hash = _read_artifact(
            state.preflight.plugin, "plugin restoration source", 64 * 1024 * 1024
        )
        copy_bytes, copy_hash = _read_artifact(
            state.preflight.plugin_verification_copy,
            "plugin restoration verification copy",
            64 * 1024 * 1024,
        )
        if (
            source_bytes != copy_bytes
            or source_hash != copy_hash
            or source_hash != state.preflight.plugin_sha256
        ):
            raise PassiveProbeError("plugin restoration sources changed before Mode-off deploy")
        mode_off_manifest = oracle_install._deploy_plugin_bytes(
            state.preflight.game_root,
            source_bytes,
            state.preflight.plugin_sha256,
            off_bytes.decode("utf-8", "strict"),
        )
        if stage == "official_passive":
            state.manifests.official_off = mode_off_manifest
            mode_off_compatibility: Literal["official", "patched"] = "official"
            mode_off_active = state.preflight.snapshot.legacy.active_preloader_sha256
        else:
            state.manifests.patched_off = mode_off_manifest
            mode_off_compatibility = "patched"
            mode_off_active = state.preflight.preloader_sha256
        mode_off_snapshot = _capture_passive_snapshot(state.preflight.game_root)
        _require_stage_snapshot(
            mode_off_snapshot,
            compatibility=mode_off_compatibility,
            plugin_sha256=state.preflight.plugin_sha256,
            config_sha256=state.preflight.mode_off_config_sha256,
            active_preloader_sha256=mode_off_active,
            assembly_sha256=state.preflight.snapshot.legacy.assembly_sha256,
            installer_healthy=state.preflight.snapshot.legacy.installer_healthy,
            app_signature=state.preflight.snapshot.legacy.app_signature,
            expected_manifest=mode_off_manifest,
        )
    state.mode_off_restored = True
    if stage in {"patched_passive", "patched_off"}:
        source_bytes, source_hash = _read_artifact(
            state.preflight.plugin, "plugin restoration source", 64 * 1024 * 1024
        )
        copy_bytes, copy_hash = _read_artifact(
            state.preflight.plugin_verification_copy,
            "plugin restoration verification copy",
            64 * 1024 * 1024,
        )
        if (
            source_bytes != copy_bytes
            or source_hash != copy_hash
            or source_hash != state.preflight.plugin_sha256
        ):
            raise PassiveProbeError("plugin restoration sources changed before preloader restore")
        state.manifests.official_off, state.recovery_dir = oracle_install.restore_preloader(
            state.preflight.game_root
        )
    state.official_preloader_restored = True
    state.after = _capture_passive_snapshot(state.preflight.game_root)
    _require_stage_snapshot(
        state.after,
        compatibility="official",
        plugin_sha256=state.preflight.plugin_sha256,
        config_sha256=state.preflight.mode_off_config_sha256,
        active_preloader_sha256=state.preflight.snapshot.legacy.active_preloader_sha256,
        assembly_sha256=state.preflight.snapshot.legacy.assembly_sha256,
        installer_healthy=state.preflight.snapshot.legacy.installer_healthy,
        app_signature=state.preflight.snapshot.legacy.app_signature,
        expected_manifest=state.manifests.official_off,
    )
    if state.after.legacy.assembly_sha256 != state.preflight.snapshot.legacy.assembly_sha256:
        raise PassiveProbeError("assembly changed during failure restoration")
    state.installed_status_healthy = True
```

- [ ] **Step 4: Run restoration-classification GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'failure_restoration'
```

Expected: four exact states are accepted; only the three non-restored states mutate as specified, `already_restored` is a no-op, every uncertain state stops before mutation, and no branch retries.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit classified failure restoration**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "fix: classify passive restoration state"
```

### Task 20C: Finish failed lifecycles without losing the primary or publishing early

**Files:**
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`

**Interfaces:**
- Produces `_finish_failed_lifecycle(state, primary) -> PassiveProbeResult`.
- Ordinary `Exception` returns `success=False` only after safe publication. `KeyboardInterrupt`, `SystemExit`, and `GeneratorExit` retain identity and are re-raised after cleanup/publication attempts.
- Publication failure always re-raises the original primary; all eligible owners are closed and recorded as secondary errors; no precommit close failure can leave canonical JSON.

- [ ] **Step 1: Add failure matrix, primary identity, and publication RED tests**

Register the five failure-finalizer/process-primary rows explicitly reserved in Task 20A, then add the closed `26 × 2 = 52` matrix below and one independent launcher-close counter row. The seven added stage rows independently cover unsafe/truncated isolated evidence plus missing Mode-off, official-preloader, installer-health, final-snapshot, and ordinary-save equality conditions. The counter row makes `launcher_guard.close()` succeed in killing/reaping and then raise; `_finish_failed_lifecycle` must record the single cleanup attempt and must never call the guard again during publication or finalization. Total Task-20C registrations are 58. The helper it consumes is fully defined in Task 20A; every override below is shown, and both primary classes use the identical stage table:

```python
@pytest.mark.parametrize(
    "stage",
    (
        "baseline",
        "process_cleanup",
        "process_absence",
        "trace_retention",
        "isolated_scan",
        "isolated_unsafe",
        "isolated_truncated",
        "ordinary_after",
        "auxiliary_specs",
        "evidence_collection",
        "classified_restoration",
        "mode_off_missing",
        "official_restore_missing",
        "installed_unhealthy",
        "after_missing",
        "final_process_absence",
        "ordinary_final",
        "ordinary_changed",
        "publication_stage",
        "publication_verify",
        "logging_close",
        "retained_close",
        "layout_close",
        "staged_close",
        "publication_commit",
        "publication_commit_and_close",
    ),
)
@pytest.mark.parametrize("primary_kind", ("ordinary", "process"))
def test_failure_matrix_preserves_primary_and_never_publishes_before_closes(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    primary_kind: str,
) -> None:
    primary: BaseException = (
        passive.PassiveProbeError("original monitor failure")
        if primary_kind == "ordinary"
        else KeyboardInterrupt("original operator interruption")
    )
    secondary = OSError(f"synthetic {stage} failure")
    calls: list[str] = []
    guard = FailureGuard()
    real_commit_staged = passive._commit_staged_passive_result

    def retained_close() -> None:
        calls.append("retained-close")
        if stage in {"retained_close", "staged_close"}:
            raise secondary

    retained = SimpleNamespace(
        files=(),
        public=SimpleNamespace(copied_logs=(), moved_logs=()),
        close=retained_close,
    )
    _install_failure_finalizer_fakes(
        monkeypatch,
        synthetic_preflight,
        retained,
        calls,
        restore_error=(secondary if stage == "classified_restoration" else None),
    )
    state = _failure_state(synthetic_preflight, passive_layout, guard)

    if stage == "process_cleanup":
        monkeypatch.setattr(guard, "close", lambda: (_ for _ in ()).throw(secondary))
    elif stage == "process_absence":
        monkeypatch.setattr(
            passive,
            "_require_no_matching_processes_for_preflight",
            lambda *_args: (_ for _ in ()).throw(secondary),
        )
    elif stage == "trace_retention":
        monkeypatch.setattr(
            passive,
            "_retain_post_reap_trace",
            lambda _layout: (_ for _ in ()).throw(secondary),
        )
    elif stage == "isolated_scan":
        monkeypatch.setattr(
            passive,
            "_secure_isolated_save_tree",
            lambda _layout: (_ for _ in ()).throw(secondary),
        )
    elif stage == "isolated_unsafe":
        monkeypatch.setattr(
            passive,
            "_secure_isolated_save_tree",
            lambda _layout: passive.IsolatedSaveObservation(
                (),
                False,
                ("unsupported isolated entry",),
                0,
                False,
            ),
        )
    elif stage == "isolated_truncated":
        monkeypatch.setattr(
            passive,
            "_secure_isolated_save_tree",
            lambda _layout: passive.IsolatedSaveObservation(
                (),
                True,
                (),
                0,
                True,
            ),
        )
    elif stage == "ordinary_after":
        monkeypatch.setattr(
            passive,
            "fingerprint_save_tree",
            lambda _path: (_ for _ in ()).throw(secondary),
        )
    elif stage == "auxiliary_specs":
        monkeypatch.setattr(
            passive,
            "_auxiliary_specs",
            lambda *_args: (_ for _ in ()).throw(secondary),
        )
    elif stage == "evidence_collection":
        monkeypatch.setattr(
            oracle_boot,
            "_collect_boot_evidence_into",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(secondary),
        )
    elif stage in {
        "mode_off_missing",
        "official_restore_missing",
        "installed_unhealthy",
        "after_missing",
    }:
        def incomplete_restore(observed_state: passive._LifecycleState) -> None:
            calls.extend(("mode-off", "restore"))
            observed_state.mode_off_restored = stage != "mode_off_missing"
            observed_state.official_preloader_restored = (
                stage != "official_restore_missing"
            )
            observed_state.installed_status_healthy = (
                stage != "installed_unhealthy"
            )
            observed_state.after = (
                None if stage == "after_missing" else synthetic_preflight.snapshot
            )

        monkeypatch.setattr(passive, "_restore_failure_stage", incomplete_restore)
    elif stage == "final_process_absence":
        absence_calls = 0

        def absence(*_args: object) -> tuple[passive.ProcessRow, ...]:
            nonlocal absence_calls
            absence_calls += 1
            if absence_calls == 2:
                raise secondary
            return ()

        monkeypatch.setattr(passive, "_require_no_matching_processes_for_preflight", absence)
    elif stage == "ordinary_final":
        proof_calls = 0

        def proof(_path: Path) -> passive.SaveTreeProof:
            nonlocal proof_calls
            proof_calls += 1
            if proof_calls == 2:
                raise secondary
            return synthetic_preflight.ordinary_save

        monkeypatch.setattr(passive, "fingerprint_save_tree", proof)
    elif stage == "ordinary_changed":
        proof_calls = 0
        changed = replace(
            synthetic_preflight.ordinary_save,
            regular_bytes=synthetic_preflight.ordinary_save.regular_bytes + 1,
        )

        def proof(_path: Path) -> passive.SaveTreeProof:
            nonlocal proof_calls
            proof_calls += 1
            return synthetic_preflight.ordinary_save if proof_calls == 1 else changed

        monkeypatch.setattr(passive, "fingerprint_save_tree", proof)
    elif stage in {"publication_stage", "publication_verify"}:
        monkeypatch.setattr(
            passive,
            "_stage_passive_result",
            lambda *_args: (_ for _ in ()).throw(secondary),
        )
    elif stage == "logging_close":
        state.logging_guard = SimpleNamespace(
            close=lambda: (calls.append("logging-close"), (_ for _ in ()).throw(secondary))[1]
        )
    elif stage == "layout_close":
        monkeypatch.setattr(
            passive_layout,
            "close",
            lambda: (calls.append("layout-close"), (_ for _ in ()).throw(secondary))[1],
        )
    elif stage == "staged_close":
        monkeypatch.setattr(
            oracle_boot,
            "_close_staged_probe_json",
            lambda _staged: (calls.append("staged-close"), (_ for _ in ()).throw(secondary))[1],
        )
    elif stage in {"publication_commit", "publication_commit_and_close"}:
        monkeypatch.setattr(passive, "_commit_staged_passive_result", real_commit_staged)
        monkeypatch.setattr(
            oracle_boot,
            "_commit_staged_probe_json",
            lambda _staged: (
                calls.append("publish"),
                (_ for _ in ()).throw(secondary),
            )[1],
        )
        if stage == "publication_commit_and_close":
            monkeypatch.setattr(
                oracle_boot,
                "_close_staged_probe_json",
                lambda _staged: (calls.append("staged-close"), (_ for _ in ()).throw(OSError("close")))[1],
            )

    if primary_kind == "process":
        with pytest.raises(KeyboardInterrupt) as reraised:
            passive._finish_failed_lifecycle(state, primary)
        assert reraised.value is primary
        result: passive.PassiveProbeResult | None = None
    else:
        caught: BaseException | None = None
        result = None
        try:
            result = passive._finish_failed_lifecycle(state, primary)
        except BaseException as observed:
            caught = observed
        if caught is not None:
            assert caught is primary
        else:
            assert result is not None and result.success is False
            assert result.issues == (f"{type(primary).__name__}: {primary}",)
    assert guard.close_count <= 1
    assert calls.count("mode-off") <= 1
    assert calls.count("restore") <= 1
    if stage in {
        "trace_retention",
        "isolated_scan",
        "isolated_unsafe",
        "isolated_truncated",
        "ordinary_after",
        "auxiliary_specs",
        "evidence_collection",
    }:
        assert calls.count("restore") == 1
        assert "publish" not in calls
    if stage in {
        "classified_restoration",
        "mode_off_missing",
        "official_restore_missing",
        "installed_unhealthy",
        "after_missing",
        "final_process_absence",
        "ordinary_final",
        "ordinary_changed",
    }:
        assert "publish" not in calls
    if primary_kind == "process":
        assert "publish" not in calls
    if stage in {"logging_close", "retained_close", "layout_close", "staged_close"}:
        assert "publish" not in calls
    if stage == "publication_commit_and_close" and primary_kind == "ordinary":
        assert calls.count("publish") == calls.count("staged-close") == 1
        assert any(
            "secondary staged JSON close failure" in note
            for note in secondary.__notes__
        )


def test_failure_launcher_close_attempt_is_consumed_even_when_close_raises(
    synthetic_preflight: passive.PassivePreflight,
    passive_layout: passive.PassiveLayout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = FailureGuard()
    close_primary = OSError("launcher killed and reaped, then close reported failure")

    def close() -> int:
        guard.close_count += 1
        guard.process = None
        raise close_primary

    monkeypatch.setattr(guard, "close", close)
    state = _failure_state(synthetic_preflight, passive_layout, guard)
    state.layout_open = False
    primary = passive.PassiveProbeError("monitor failed")
    with pytest.raises(passive.PassiveProbeError) as caught:
        passive._finish_failed_lifecycle(state, primary)
    assert caught.value is primary
    assert guard.close_count == 1
    assert state.launcher_guard is None
    assert any(
        "process-group cleanup" in note and str(close_primary) in note
        for note in primary.__notes__
    )
```

- [ ] **Step 2: Run full failed-lifecycle RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py \
  -k 'failure_matrix or failure_launcher_close or failure_finalizer or safe_failure_result or process_level_primary'
```

Expected: primary identity, restoration safety, evidence retention, or JSON-last ownership fails; all fifty-eight Task-20C registrations, including the launcher-close and five transferred rows, are selected.

- [ ] **Step 3: Implement the complete failure finalizer**

```python
def _close_failure_state_owners(
    state: _LifecycleState,
    primary: BaseException,
    *,
    include_staged: bool,
) -> None:
    operations: list[tuple[str, Callable[[], object]]] = []
    if state.launcher_guard is not None:
        launcher = state.launcher_guard
        state.launcher_guard = None
        operations.append(("launcher guard close", launcher.close))
    if state.logging_guard is not None:
        logging_guard = state.logging_guard
        state.logging_guard = None
        operations.append(("logging guard close", logging_guard.close))
    if state.retained is not None:
        retained = state.retained
        state.retained = None
        operations.append(("retained evidence close", retained.close))
    if state.layout_open:
        state.layout_open = False
        operations.append(("passive layout close", state.layout.close))
    if include_staged and state.staged_json is not None:
        staged = state.staged_json
        state.staged_json = None
        operations.append(
            (
                "staged JSON close",
                lambda: oracle_boot._close_staged_probe_json(staged),
            )
        )
    for stage, operation in operations:
        try:
            operation()
        except BaseException as secondary:
            _record_secondary(state, primary, stage, secondary)


def _finish_failed_lifecycle(
    state: _LifecycleState,
    primary: BaseException,
) -> PassiveProbeResult:
    if state.launcher_guard is not None:
        launcher_guard = state.launcher_guard
        spawned_pid = (
            None
            if launcher_guard.process is None
            else launcher_guard.process.pid
        )
        spawned_pgid = launcher_guard.pgid
        if state.process_tracker is None:
            state.process_tracker = _process_tracker_for_preflight(
                state.preflight,
                spawned_pid,
                spawned_pgid,
            )
        # Transfer the attempt, not the retry right: one call is permitted.
        state.launcher_guard = None
        try:
            state.exit_code = launcher_guard.close()
            state.process_group_stopped = True
        except BaseException as secondary:
            _record_secondary(state, primary, "process-group cleanup", secondary)
    else:
        state.process_group_stopped = True
        if state.process_tracker is None:
            state.process_tracker = _process_tracker_for_preflight(
                state.preflight,
                None,
                None,
            )

    if state.process_group_stopped:
        try:
            _require_no_matching_processes_for_preflight(
                state.preflight,
                state.process_tracker,
            )
            state.no_matching_processes = True
        except BaseException as secondary:
            _record_secondary(state, primary, "process absence", secondary)

    if state.no_matching_processes:
        try:
            state.trace = _retain_post_reap_trace(state.layout)
            state.trace_retention_complete = True
        except BaseException as secondary:
            _record_secondary(state, primary, "trace retention", secondary)
        try:
            state.isolated_save = _secure_isolated_save_tree(state.layout)
        except BaseException as secondary:
            _record_secondary(state, primary, "isolated-save evidence", secondary)
        try:
            state.ordinary_after = fingerprint_save_tree(
                Path(state.preflight.ordinary_save.path)
            )
        except BaseException as secondary:
            _record_secondary(state, primary, "ordinary-save evidence", secondary)
        state.post_evidence_safe = (
            state.isolated_save is not None
            and state.isolated_save.safe
            and not state.isolated_save.truncated
            and state.ordinary_after is not None
        )

    # Evidence collection is attempted before restoration, but no evidence
    # failure is allowed to strand an exact, process-free patched install.
    if state.retained is None and state.no_matching_processes:
        try:
            state.retained = oracle_boot._collect_boot_evidence_into(
                state.preflight.before_logs,
                state.preflight.game_root,
                state.layout.evidence_dir,
                state.layout.evidence_handle,
                expected_inventory=state.preflight.log_inventory,
                run_contract=None,
                observed_failures=(
                    () if state.monitor is None else state.monitor.observed_failures
                ),
                auxiliary_specs=_auxiliary_specs(state.layout, state.trace),
            )
        except BaseException as secondary:
            _record_secondary(state, primary, "evidence collection", secondary)

    if state.no_matching_processes:
        try:
            _restore_failure_stage(state)
        except BaseException as secondary:
            _record_secondary(state, primary, "classified restoration", secondary)

    if state.installed_status_healthy:
        try:
            _require_no_matching_processes_for_preflight(
                state.preflight,
                state.process_tracker,
            )
            state.ordinary_final = fingerprint_save_tree(
                Path(state.preflight.ordinary_save.path)
            )
            state.ordinary_save_unchanged = (
                state.ordinary_after is not None
                and state.ordinary_after == state.preflight.ordinary_save
                and state.ordinary_final == state.preflight.ordinary_save
            )
        except BaseException as secondary:
            _record_secondary(state, primary, "final verification", secondary)
            state.no_matching_processes = False

    publication_safe = (
        isinstance(primary, Exception)
        and state.process_group_stopped
        and state.no_matching_processes
        and state.trace_retention_complete
        and state.post_evidence_safe
        and state.retained is not None
        and state.mode_off_restored
        and state.official_preloader_restored
        and state.installed_status_healthy
        and state.after is not None
        and state.ordinary_after is not None
        and state.ordinary_final is not None
        and state.ordinary_save_unchanged
        and state.isolated_save is not None
        and state.isolated_save.safe
        and not state.isolated_save.truncated
    )
    if not publication_safe:
        _close_failure_state_owners(
            state,
            primary,
            include_staged=True,
        )
        state.finalized = True
        raise primary

    assert state.retained is not None
    assert state.isolated_save is not None
    cleanup = PassiveCleanup(
        state.process_group_stopped,
        state.no_matching_processes,
        state.mode_off_restored,
        state.official_preloader_restored,
        state.installed_status_healthy,
        state.ordinary_save_unchanged,
    )
    monitor = state.monitor
    result = PassiveProbeResult(
        success=False,
        started_at_utc=state.started_at_utc,
        finished_at_utc=_utc_timestamp(),
        controller_pid=os.getpid(),
        game_root=state.preflight.game_root,
        macos_product_version=state.preflight.macos_product_version,
        launcher=state.preflight.launcher,
        evidence_dir=state.layout.evidence_dir,
        isolated_save_dir=state.layout.isolated_save_dir,
        plugin_sha256=state.preflight.plugin_sha256,
        mode_off_config_sha256=state.preflight.mode_off_config_sha256,
        passive_config_sha256=state.layout.config_sha256,
        markers=() if monitor is None else monitor.markers,
        issues=(f"{type(primary).__name__}: {primary}",),
        secondary_errors=tuple(state.secondary_errors),
        exit_code=state.exit_code,
        run_id=(None if state.trace is None or state.trace.run is None else state.trace.run.header.run_id),
        cleanup=cleanup,
        before=state.preflight.snapshot,
        patched=state.patched,
        post_process=state.post_process,
        after=state.after,
        before_logs=state.preflight.before_logs,
        after_logs=tuple(
            item.fingerprint for item in state.retained.files if item.kind == "boot_log"
        ),
        ordinary_save_before=state.preflight.ordinary_save,
        ordinary_save_after=state.ordinary_after,
        ordinary_save_final=state.ordinary_final,
        isolated_save=state.isolated_save,
        trace=None if state.trace is None else state.trace.summary,
        copied_logs=state.retained.public.copied_logs,
        moved_logs=state.retained.public.moved_logs,
        restore_recovery_dir=state.recovery_dir,
    )
    try:
        state.staged_json = _stage_passive_result(
            result,
            state.layout,
            state.retained,
        )
    except BaseException as secondary:
        _record_secondary(state, primary, "failure publication staging", secondary)
        _close_failure_state_owners(
            state,
            primary,
            include_staged=True,
        )
        state.finalized = True
        raise primary

    assert state.staged_json is not None
    secondary_count = len(state.secondary_errors)
    _close_failure_state_owners(
        state,
        primary,
        include_staged=False,
    )
    precommit_failed = len(state.secondary_errors) != secondary_count
    if precommit_failed:
        _close_failure_state_owners(
            state,
            primary,
            include_staged=True,
        )
        state.finalized = True
        raise primary

    staged = state.staged_json
    state.staged_json = None
    try:
        # `_commit_staged_passive_result` consumes and closes this owner on
        # both success and failure; clear state before transferring it.
        _commit_staged_passive_result(staged)
    except BaseException as secondary:
        _record_secondary(state, primary, "failure publication commit", secondary)
        state.finalized = True
        raise primary
    state.finalized = True
    return result
```

At the top of `_run_passive_probe_lifecycle`, add `state: _LifecycleState | None = None`. Immediately after layout allocation, initialize ownership with this exact code and thereafter treat these state fields—not detached aliases—as the owners:

```python
state = _LifecycleState(
    preflight=preflight,
    started_at_utc=started,
    layout=layout,
    logging_guard=logging_guard,
    manifests=manifests,
)
```

Use these exact state transitions at the corresponding Task 19 boundaries. Each installer result is assigned immediately on return, before any later capture or fallible operation; `_restore_success_stage` receives the same mutable manifest carrier, so a failure after Mode-off deployment retains the exact patched/off manifest for classified resume:

```python
assert state.manifests is not None
state.manifests.official_passive = oracle_install._deploy_plugin_bytes(
    preflight.game_root,
    authenticated_plugin,
    preflight.plugin_sha256,
    passive_text,
)
state.manifests.patched_passive = oracle_install.deploy_preloader(
    preflight.game_root,
    preflight.preloader,
    preflight.provenance,
)
state.patched = _capture_passive_snapshot(preflight.game_root)
state.logging_guard = None  # immediately after verified logging-guard close
state.post_process = _capture_passive_snapshot(preflight.game_root)
state.trace = _retain_post_reap_trace(state.layout)
state.trace_retention_complete = True
state.isolated_save = _secure_isolated_save_tree(state.layout)
state.retained = oracle_boot._collect_boot_evidence_into(
    preflight.before_logs,
    preflight.game_root,
    state.layout.evidence_dir,
    state.layout.evidence_handle,
    expected_inventory=preflight.log_inventory,
    run_contract=run_contract,
    observed_failures=state.monitor.observed_failures,
    auxiliary_specs=_auxiliary_specs(state.layout, state.trace),
)
_require_retained_success_evidence(
    state.monitor.trace,
    state.trace,
    state.retained,
)
state.ordinary_after = fingerprint_save_tree(
    Path(preflight.ordinary_save.path)
)
if state.ordinary_after != state.preflight.ordinary_save:
    raise PassiveProbeError("ordinary save changed before restoration")
state.post_evidence_safe = (
    state.isolated_save.safe
    and not state.isolated_save.truncated
)
after, recovery_dir = _restore_success_stage(
    preflight,
    state.layout,
    state.post_process,
    state.manifests,
)
state.mode_off_restored = True
state.recovery_dir = recovery_dir
state.official_preloader_restored = True
state.after = after
state.installed_status_healthy = True
state.ordinary_final = fingerprint_save_tree(
    Path(preflight.ordinary_save.path)
)
if (
    state.ordinary_after != state.preflight.ordinary_save
    or state.ordinary_final != state.preflight.ordinary_save
):
    raise PassiveProbeError("ordinary save changed during final verification")
state.ordinary_save_unchanged = True
```

In the `PassiveProbeResult` constructor, replace Task 19D's three remaining detached evidence references with these exact state-owned expressions:

```diff
-after_logs=tuple(item.fingerprint for item in retained.files if item.kind == "boot_log"),
+after_logs=tuple(item.fingerprint for item in state.retained.files if item.kind == "boot_log"),
-copied_logs=retained.public.copied_logs,
+copied_logs=state.retained.public.copied_logs,
-moved_logs=retained.public.moved_logs,
+moved_logs=state.retained.public.moved_logs,
```

Replace Task 19D's success staging/close/commit tail with this exact owner-transfer sequence. Every field is cleared before its one fallible consumption, and `state.finalized` is set before either a commit exception escapes or the result returns:

```python
state.staged_json = _stage_passive_result(
    result,
    state.layout,
    state.retained,
)
precommit_operations: list[tuple[str, Callable[[], object]]] = []
if state.logging_guard is not None:
    logging_owner = state.logging_guard
    state.logging_guard = None
    precommit_operations.append(("logging guard close", logging_owner.close))
if state.retained is not None:
    retained_owner = state.retained
    state.retained = None
    precommit_operations.append(("retained evidence close", retained_owner.close))
if state.layout_open:
    state.layout_open = False
    precommit_operations.append(("passive layout close", state.layout.close))
close_error = _close_all_owners(tuple(precommit_operations))
if close_error is not None:
    staged_owner = state.staged_json
    state.staged_json = None
    if staged_owner is not None:
        _close_all_owners(
            (
                (
                    "staged JSON close",
                    lambda: oracle_boot._close_staged_probe_json(staged_owner),
                ),
            ),
            close_error,
        )
    state.finalized = True
    raise close_error

staged_owner = state.staged_json
if staged_owner is None:
    raise AssertionError("successful publication has no staged JSON owner")
state.staged_json = None
try:
    _commit_staged_passive_result(staged_owner)
except BaseException:
    state.finalized = True
    raise
state.finalized = True
return result
```

The launcher portion must be this exact ownership sequence; no local transfer clears the guard before close:

```python
state.launcher_guard = _acquire_launcher(preflight)
if state.launcher_guard.process is None:
    raise AssertionError("new launcher guard has no process")
state.process_tracker = _process_tracker_for_preflight(
    preflight,
    state.launcher_guard.process.pid,
    state.launcher_guard.pgid,
)
state.monitor = _wait_for_passive_trace(
    state.launcher_guard.process,
    preflight.game_root,
    preflight.before_logs,
    state.layout,
    preflight.timeout_seconds,
    instruction_sink,
    state.process_tracker,
)
state.exit_code = state.launcher_guard.close()
state.launcher_guard = None
state.process_group_stopped = True
_require_no_matching_processes_for_preflight(preflight, state.process_tracker)
state.no_matching_processes = True
```

Replace the direct failure behavior with this exact branch:

```diff
except BaseException as primary:
    if state is None or state.finalized:
        raise
    failed = _finish_failed_lifecycle(state, primary)
    if isinstance(primary, Exception):
        return failed
    raise
```

Replace the Task 19 finalizer with this exact all-owner accumulator. The launcher owner is already consumed before `_finish_failed_lifecycle` calls `close`, so the finalizer cannot retry it. It does nothing after Task 20C marks the state finalized:

```diff
finally:
    active = sys.exception()
    close_operations: list[tuple[str, Callable[[], object]]] = []
    if state is not None and state.finalized:
        close_operations = []
    elif state is None:
        if logging_guard is not None:
            logging_owner = logging_guard
            logging_guard = None
            close_operations.append(("logging guard close", logging_owner.close))
    else:
        if state.launcher_guard is not None:
            launcher_owner = state.launcher_guard
            state.launcher_guard = None
            close_operations.append(("launcher guard close", launcher_owner.close))
        if state.logging_guard is not None:
            logging_owner = state.logging_guard
            state.logging_guard = None
            close_operations.append(("logging guard close", logging_owner.close))
        if state.retained is not None:
            retained_owner = state.retained
            state.retained = None
            close_operations.append(("retained evidence close", retained_owner.close))
        if state.layout_open:
            state.layout_open = False
            close_operations.append(("passive layout close", state.layout.close))
        if state.staged_json is not None:
            staged_owner = state.staged_json
            state.staged_json = None
            close_operations.append(
                (
                    "staged JSON close",
                    lambda: oracle_boot._close_staged_probe_json(staged_owner),
                )
            )
    close_primary = _close_all_owners(tuple(close_operations), active)
    if active is None and close_primary is not None:
        raise close_primary
```

Run this non-pytest structural assertion after updating `_run_passive_probe_lifecycle`. It proves the ownership-bearing success transitions occur in order, forbids the detached Task 19 owner variables after state initialization, and requires the single failure/finally owner paths:

```python
import ast
import re
from pathlib import Path

source = Path("src/ssr_env/oracle_passive_probe.py").read_text()
tree = ast.parse(source)
run_node = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "_run_passive_probe_lifecycle"
)
run = ast.get_source_segment(source, run_node)
assert run is not None
ordered = (
    "state = _LifecycleState(",
    "state.patched = _capture_passive_snapshot(",
    "state.logging_guard = None",
    "state.launcher_guard = _acquire_launcher(preflight)",
    "state.process_tracker = _process_tracker_for_preflight(",
    "state.monitor = _wait_for_passive_trace(",
    "state.exit_code = state.launcher_guard.close()",
    "state.launcher_guard = None",
    "state.process_group_stopped = True",
    "state.no_matching_processes = True",
    "state.post_process = _capture_passive_snapshot(",
    "state.trace = _retain_post_reap_trace(",
    "state.trace_retention_complete = True",
    "state.isolated_save = _secure_isolated_save_tree(",
    "state.retained = oracle_boot._collect_boot_evidence_into(",
    "state.ordinary_after = fingerprint_save_tree(",
    "if state.ordinary_after != state.preflight.ordinary_save:",
    "state.post_evidence_safe = (",
    "state.mode_off_restored = True",
    "state.recovery_dir = recovery_dir",
    "state.official_preloader_restored = True",
    "state.after = after",
    "state.installed_status_healthy = True",
    "state.ordinary_final = fingerprint_save_tree(",
    "or state.ordinary_final != state.preflight.ordinary_save",
    "state.ordinary_save_unchanged = True",
    "state.staged_json = _stage_passive_result(",
    "state.retained = None",
    "state.layout_open = False",
    "state.staged_json = None",
    "state.finalized = True",
)
cursor = -1
for token in ordered:
    position = run.find(token, cursor + 1)
    assert position > cursor, token
    cursor = position
tail = run[run.index("state = _LifecycleState("):]
for detached in ("launcher_guard", "retained", "staged"):
    assert re.search(rf"(?m)^        {detached}\s*=", tail) is None
post_evidence_assignments = [
    node
    for node in ast.walk(run_node)
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "state"
        and target.attr == "post_evidence_safe"
        for target in node.targets
    )
]
assert len(post_evidence_assignments) == 1
post_evidence_value = post_evidence_assignments[0].value
assert isinstance(post_evidence_value, ast.BoolOp)
assert isinstance(post_evidence_value.op, ast.And)
assert run.count("failed = _finish_failed_lifecycle(state, primary)") == 1
assert run.count("close_primary = _close_all_owners(tuple(close_operations), active)") == 1
assert run.count("if state is None or state.finalized:") == 1
```

`_require_no_matching_processes_for_preflight` consumes Task 13B's retained tracker; it never constructs a fresh tracker after reaping and never acquires a launcher.

Only after the complete failure matrix is GREEN, expose the public entrypoint without a second implementation:

```python
run_passive_probe = _run_passive_probe_lifecycle
```

The code-quality review must prove this assignment occurs textually after `_finish_failed_lifecycle`, and Task 19D's commit has no public mutating entrypoint.

- [ ] **Step 4: Run the complete failure matrix GREEN**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py
```

Expected: all success and failure stages pass; no retry occurs; unsafe process/evidence/publication states create no canonical JSON; reachable raw trace/config/log/save bytes remain private.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save the fresh specification-review and code-quality-review artifact paths and reviewer SHAs in this task's execution report. If either reviewer requests a change, apply it, rerun this task's GREEN command and \`git diff --check\`, and obtain both fresh approvals again. Do not reuse or batch a review from another detailed task.

- [ ] **Step 6: Commit the failure/restoration gate**

```bash
git diff --check
git add src/ssr_env/oracle_passive_probe.py tests/test_oracle_passive_probe.py
git commit -m "fix: close passive oracle failure lifecycle"
```

### Task 21: Add CLI, preflight-only mode, runbook, and full offline gate

**Files:**
- Create: `tools/oracle_passive_probe.py`
- Modify: `src/ssr_env/oracle_passive_probe.py`
- Modify: `tests/test_oracle_passive_probe.py`
- Modify: `oracle/README.md`
- Modify: `docs/superpowers/plans/2026-07-27-executable-oracle.md`
- Modify: `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`

**Interfaces:**
- CLI requires nine path/hash arguments, `--timeout 300`, and optional `--preflight-only`.
- Preflight-only calls only `preflight_passive_probe`, prints one sorted pretty JSON summary including exact `macos_product_version`, and exits `0`; invalid request/preflight exits `2`.
- Runtime prints the same retained host version and exits `0` success, `1` retained completed failure, and `2` invalid request/preflight/unsafe publication.
- Wrapper is exactly `raise SystemExit(main())`.

- [ ] **Step 1: Add direct-main, narrow refusal, and wrapper RED tests**

Add the fourteen registrations below. The two plain-`OSError` rows cover preflight-only and runtime mode. Two independent `oracle_compat.CompatError` rows cover malformed retained provenance/trust in those same modes. All four narrowly normalized failures return `2`, print one refusal line on stderr, print no traceback/stdout, preserve exact one-call behavior, and do not broaden the catch to `ValueError`.

```python
import json


def _cli_argv(request: dict[str, object]) -> list[str]:
    return [
        "--game-root", str(request["game_root"]),
        "--launcher", str(request["launcher"]),
        "--mode-off-config", str(request["mode_off_config"]),
        "--plugin", str(request["plugin"]),
        "--plugin-verification-copy", str(request["plugin_verification_copy"]),
        "--expected-plugin-sha256", str(request["expected_plugin_sha256"]),
        "--preloader", str(request["preloader"]),
        "--provenance", str(request["provenance"]),
        "--evidence-root", str(request["evidence_root"]),
        "--timeout", "300",
    ]


def test_main_preflight_only_never_calls_runtime(
    complete_preflight_request: dict[str, object],
    synthetic_preflight: passive.PassivePreflight,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(passive, "preflight_passive_probe", lambda **_kwargs: calls.append("preflight") or synthetic_preflight)
    monkeypatch.setattr(passive, "run_passive_probe", lambda **_kwargs: calls.append("runtime"))
    code = passive.main([*_cli_argv(complete_preflight_request), "--preflight-only"])
    captured = capsys.readouterr()
    assert code == 0
    assert calls == ["preflight"]
    payload = json.loads(captured.out)
    assert payload == {
        "evidence_root": str(synthetic_preflight.evidence_root),
        "game_root": str(synthetic_preflight.game_root),
        "macos_product_version": "26.6",
        "ordinary_save_state": synthetic_preflight.ordinary_save.state,
        "plugin_sha256": synthetic_preflight.plugin_sha256,
        "success": True,
    }
    assert captured.err == ""


def test_parser_requires_explicit_timeout_300(
    complete_preflight_request: dict[str, object],
) -> None:
    argv = _cli_argv(complete_preflight_request)
    timeout_index = argv.index("--timeout")
    del argv[timeout_index : timeout_index + 2]
    with pytest.raises(SystemExit) as caught:
        passive._parser().parse_args(argv)
    assert caught.value.code == 2


@pytest.mark.parametrize("value", ("299", "301"))
def test_parser_rejects_every_non_300_timeout(
    complete_preflight_request: dict[str, object],
    value: str,
) -> None:
    argv = _cli_argv(complete_preflight_request)
    argv[argv.index("--timeout") + 1] = value
    with pytest.raises(SystemExit) as caught:
        passive._parser().parse_args(argv)
    assert caught.value.code == 2


def test_parser_rejects_noncanonical_300_spelling(
    complete_preflight_request: dict[str, object],
) -> None:
    for value in ("0300", "+300"):
        argv = _cli_argv(complete_preflight_request)
        argv[argv.index("--timeout") + 1] = value
        with pytest.raises(SystemExit) as caught:
            passive._parser().parse_args(argv)
        assert caught.value.code == 2


@pytest.mark.parametrize(("success", "expected"), ((True, 0), (False, 1)))
def test_main_runtime_exit_codes_are_zero_or_one(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    success: bool,
    expected: int,
) -> None:
    result = SimpleNamespace(
        success=success,
        evidence_dir=Path("/private/evidence"),
        macos_product_version="26.6",
        issues=(() if success else ("retained failure",)),
        markers=(() if not success else passive.PASSIVE_MARKERS),
    )
    monkeypatch.setattr(passive, "run_passive_probe", lambda **_kwargs: result)
    assert passive.main(_cli_argv(complete_preflight_request)) == expected
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "evidence_dir": "/private/evidence",
        "issues": ([] if success else ["retained failure"]),
        "macos_product_version": "26.6",
        "markers": ([] if not success else list(passive.PASSIVE_MARKERS)),
        "success": success,
    }
    assert captured.err == ""


@pytest.mark.parametrize("preflight_only", (False, True))
def test_main_invalid_request_or_preflight_exits_two(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    preflight_only: bool,
) -> None:
    def refuse(**_kwargs: object) -> object:
        raise passive.PassiveProbeError("invalid preflight")

    monkeypatch.setattr(passive, "preflight_passive_probe", refuse)
    monkeypatch.setattr(passive, "run_passive_probe", refuse)
    argv = _cli_argv(complete_preflight_request)
    if preflight_only:
        argv.append("--preflight-only")
    assert passive.main(argv) == 2


@pytest.mark.parametrize("preflight_only", (True, False))
def test_main_normalizes_plain_oserror_without_retry_or_traceback(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    preflight_only: bool,
) -> None:
    calls: list[str] = []
    primary = OSError("synthetic operating-system refusal")

    def fail(stage: str):
        def run(**_kwargs: object) -> object:
            calls.append(stage)
            raise primary
        return run

    monkeypatch.setattr(passive, "preflight_passive_probe", fail("preflight"))
    monkeypatch.setattr(passive, "run_passive_probe", fail("runtime"))
    argv = _cli_argv(complete_preflight_request)
    if preflight_only:
        argv.append("--preflight-only")
    assert passive.main(argv) == 2
    captured = capsys.readouterr()
    assert calls == (["preflight"] if preflight_only else ["runtime"])
    assert captured.out == ""
    assert captured.err.splitlines() == [
        "passive oracle probe refused: synthetic operating-system refusal"
    ]
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("preflight_only", (True, False))
def test_main_normalizes_compaterror_without_retry_or_traceback(
    complete_preflight_request: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    preflight_only: bool,
) -> None:
    calls: list[str] = []
    primary = oracle_compat.CompatError("malformed retained provenance")

    def fail(stage: str):
        def run(**_kwargs: object) -> object:
            calls.append(stage)
            raise primary
        return run

    monkeypatch.setattr(passive, "preflight_passive_probe", fail("preflight"))
    monkeypatch.setattr(passive, "run_passive_probe", fail("runtime"))
    argv = _cli_argv(complete_preflight_request)
    if preflight_only:
        argv.append("--preflight-only")
    assert passive.main(argv) == 2
    captured = capsys.readouterr()
    assert calls == (["preflight"] if preflight_only else ["runtime"])
    assert captured.out == ""
    assert captured.err.splitlines() == [
        "passive oracle probe refused: malformed retained provenance"
    ]
    assert "Traceback" not in captured.err


def test_wrapper_is_exact_system_exit() -> None:
    source = Path("tools/oracle_passive_probe.py").read_text(encoding="utf-8")
    assert source == (
        "#!/usr/bin/env python3\n"
        "from ssr_env.oracle_passive_probe import main\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(main())\n"
    )
```

- [ ] **Step 2: Run CLI RED**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_passive_probe.py -k 'main_ or wrapper or parser_'
```

Expected: `main` and wrapper are missing; all fourteen Task-21 registrations, including both exact `CompatError` modes, are selected.

- [ ] **Step 3: Implement argparse, preflight-only, runtime exits, and offline documentation**

Add the complete CLI code to the module:

```python
import argparse
import json
from collections.abc import Sequence


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight or run one SSR passive oracle capture")
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--mode-off-config", type=Path, required=True)
    parser.add_argument("--plugin", type=Path, required=True)
    parser.add_argument("--plugin-verification-copy", type=Path, required=True)
    parser.add_argument("--expected-plugin-sha256", required=True)
    parser.add_argument("--preloader", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--timeout", type=_timeout_300, required=True)
    parser.add_argument("--preflight-only", action="store_true")
    return parser


def _timeout_300(value: str) -> int:
    if value != "300":
        raise argparse.ArgumentTypeError("timeout must be the canonical decimal text 300")
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise argparse.ArgumentTypeError("timeout must be the decimal integer 300") from error
    if parsed != 300:
        raise argparse.ArgumentTypeError("timeout must equal 300")
    return parsed


def _request_kwargs(namespace: argparse.Namespace) -> dict[str, object]:
    return {
        "game_root": namespace.game_root,
        "launcher": namespace.launcher,
        "mode_off_config": namespace.mode_off_config,
        "plugin": namespace.plugin,
        "plugin_verification_copy": namespace.plugin_verification_copy,
        "expected_plugin_sha256": namespace.expected_plugin_sha256,
        "preloader": namespace.preloader,
        "provenance": namespace.provenance,
        "evidence_root": namespace.evidence_root,
        "timeout_seconds": namespace.timeout,
    }


def main(argv: Sequence[str] | None = None) -> int:
    namespace = _parser().parse_args(argv)
    request = _request_kwargs(namespace)
    try:
        if namespace.preflight_only:
            preflight = preflight_passive_probe(**request)
            summary = {
                "evidence_root": str(preflight.evidence_root),
                "game_root": str(preflight.game_root),
                "macos_product_version": preflight.macos_product_version,
                "ordinary_save_state": preflight.ordinary_save.state,
                "plugin_sha256": preflight.plugin_sha256,
                "success": True,
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        result = run_passive_probe(**request)
    except (
        PassiveProbeError,
        oracle_boot.BootProbeError,
        oracle_install.InstallError,
        oracle_compat.CompatError,
        OSError,
    ) as error:
        print(f"passive oracle probe refused: {error}", file=sys.stderr)
        return 2
    summary = {
        "evidence_dir": str(result.evidence_dir),
        "issues": list(result.issues),
        "macos_product_version": result.macos_product_version,
        "markers": list(result.markers),
        "success": result.success,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.success else 1
```

Create the wrapper with these exact bytes:

```python
#!/usr/bin/env python3
from ssr_env.oracle_passive_probe import main

if __name__ == "__main__":
    raise SystemExit(main())
```

As part of the same implementation step, add this exact offline-only status block to `oracle/README.md` and point the superseded flexible-input section in the older plan to it:

```markdown
### Passive trace gate

The passive controller and its synthetic tests are an offline gate. They do not authorize deployment or launch. Run `tools/oracle_passive_probe.py --preflight-only` with the nine reviewed path/hash arguments first. It must report exact `macos_product_version` `26.6`; every other host result is a stop condition. A later operational plan must record that version plus the resulting literal hashes/status and request separate approval for exactly one launcher acquisition, no retry, and five physical input events in four authenticated prompt phases: two menu confirmations, one accepted direction, one blocked direction, and one Undo.

Real traces, generated configs, isolated saves, recovery trees, and `passive-probe.json` remain ignored under `data/oracle/`. Documentation may record reviewed hashes and non-sensitive pass/fail summaries only.
```

Set the passive design implementation status to `offline controller implemented and reviewed; operational gate not yet authorized or executed`. Do not claim a real capture or section 14 completion.

- [ ] **Step 4: Run the full offline GREEN verification**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py tests/test_oracle_passive_probe.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py tests/test_oracle_install.py \
  tests/test_oracle_install_compat.py tests/test_oracle_compat.py
set -o pipefail
audit_dir="$(mktemp -d /tmp/ssr-passive-probe-audit.XXXXXX)"
chmod 700 "$audit_dir"
trap 'rm -f "$audit_dir/collection.txt" "$audit_dir/results.txt" "$audit_dir/xpass.actual" "$audit_dir/xpass.expected"; rmdir "$audit_dir"' EXIT
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest --collect-only -q \
  | tee "$audit_dir/collection.txt"
rg -q '^2561 tests collected in ' "$audit_dir/collection.txt"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q -rxX \
  | tee "$audit_dir/results.txt"
rg -q '^2435 passed, 120 xfailed, 6 xpassed in ' \
  "$audit_dir/results.txt"
sed -n 's/^XPASS \([^ ]*\).*/\1/p' "$audit_dir/results.txt" | LC_ALL=C sort \
  > "$audit_dir/xpass.actual"
sed 's/^[[:space:]]*//' > "$audit_dir/xpass.expected" <<'EOF'
tests/test_oracle_boot.py::test_probe_rejects_evidence_directory_substitution_at_final_json_boundary
tests/test_oracle_boot.py::test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[raise]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[raise]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[return]
EOF
cmp -s "$audit_dir/xpass.expected" "$audit_dir/xpass.actual"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q src tools tests
git check-ignore data/oracle
git diff --check
git diff --name-status origin/main..HEAD
git status --short --branch
```

Expected: the confirmed frozen post-protocol baseline is `1822 passed`; the exact probe ledger adds `Q=613`, so collection is `2435 + 120 + 6 = 2561` and outcomes are exactly `2435 passed, 120 xfailed, 6 xpassed`, with zero failures, errors, or skips. The private audit directory is mode `0700`, is exclusively allocated by `mktemp`, owns both `tee` outputs and both XPASS lists, and is removed by the trap. The six and only six XPASS node IDs are:

```text
tests/test_oracle_boot.py::test_probe_rejects_evidence_directory_substitution_at_final_json_boundary
tests/test_oracle_boot.py::test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_evidence_path_substitution[raise]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[return]
tests/test_oracle_boot.py::test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution[raise]
```

No other XPASS or result class is allowed. No generated trace, config, save, recovery, build output, user path, or audit file is tracked. `P=240`, `B=1822`, and `Q=613` are frozen for this plan.

- [ ] **Step 5: Obtain fresh specification and code-quality approval**

Save both fresh review artifact paths and reviewer SHAs in the Task-21 execution report. The specification reviewer must check offline-only wording, exact CLI exits, prerequisite ledger closure, all 43 detailed task reports, and the frozen arithmetic. The quality reviewer must check the exact collection/outcome/XPASS audit, private audit-directory cleanup, balanced fences, no placeholders, and that only the six declared documentation/source/test files are staged. After any requested change, rerun every Step-4 command and both fresh reviews.

- [ ] **Step 6: Commit the offline gate**

```bash
git diff --check
git add tools/oracle_passive_probe.py src/ssr_env/oracle_passive_probe.py \
  tests/test_oracle_passive_probe.py oracle/README.md \
  docs/superpowers/plans/2026-07-27-executable-oracle.md \
  docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md
git commit -m "docs: prepare passive oracle runtime gate"
```

- [ ] **Step 7: Verify the committed-scope registration manifest**

After the Task-21 commit exists, collect from a clean detached worktree of that exact `HEAD`; a working-tree collection is not evidence that every row survived `git add` and commit. The explicit `git show` checks bind the cross-file Task-19A row and the new probe rows to committed bytes:

```bash
set -o pipefail
committed_parent="$(mktemp -d /tmp/ssr-passive-committed.XXXXXX)"
committed_checkout="$committed_parent/checkout"
trap 'git worktree remove --force "$committed_checkout" >/dev/null 2>&1 || true; rmdir "$committed_parent"' EXIT
git worktree add --detach "$committed_checkout" HEAD
committed_summary="$(
  cd "$committed_checkout"
  UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest --collect-only -q | tail -n 1
)"
printf '%s\n' "$committed_summary" | rg -q '^2561 tests collected in '
git -C "$committed_checkout" ls-files --error-unmatch \
  tests/test_oracle_passive_probe.py tests/test_oracle_install_compat.py \
  tests/test_oracle_compat.py
git -C "$committed_checkout" show HEAD:tests/test_oracle_install_compat.py \
  | rg -q '^def test_real_installer_manifests_drive_every_lifecycle_stage'
git -C "$committed_checkout" show HEAD:tests/test_oracle_passive_probe.py \
  | rg -q '^def test_process_snapshot_expired_read_and_cleanup_deadlines_use_final_reap'
git -C "$committed_checkout" show HEAD:tests/test_oracle_passive_probe.py \
  | rg -q '^def test_preflight_parses_retained_provenance_after_name_substitution'
git -C "$committed_checkout" show HEAD:tests/test_oracle_passive_probe.py \
  | rg -q '^def test_private_config_reader_closes_once_without_masking_primary'
git -C "$committed_checkout" show HEAD:tests/test_oracle_passive_probe.py \
  | rg -q '^def test_main_normalizes_compaterror_without_retry_or_traceback'
test -z "$(git -C "$committed_checkout" status --porcelain)"
git worktree remove --force "$committed_checkout"
rmdir "$committed_parent"
trap - EXIT
```

Expected: the detached committed checkout alone collects exactly `2561` items, all three test owners are tracked, all five cross-boundary regression functions are present in `HEAD`, and the detached checkout is clean. Task 21 is incomplete if the working tree reports `2561` but this committed-scope manifest does not.
