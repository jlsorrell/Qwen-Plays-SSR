from __future__ import annotations

import errno
import fcntl
import hashlib
import inspect
import json
import os
import re
import secrets
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
import signal
import stat
import subprocess
import sys
import textwrap
import time
from types import SimpleNamespace

import pytest

from ssr_env import oracle_boot
from ssr_env.oracle_boot import (
    collect_boot_evidence,
    fingerprint_preloader_logs,
    run_boot_probe,
)


REQUIRED_MARKERS = (
    "BepInEx 5.4.23.5",
    "Unity v2018.4.25f1",
    "SSR oracle boot probe loaded",
)
ORIGINAL_CONFIG = b"; preserve this comment\r\n[Oracle]\r\nMode=off\r\n"
BEPINEX_DISK_CONFIG = (
    b"[Logging.Disk]\n"
    b"Enabled = true\n"
    b"AppendLog = false\n"
    b"LogLevels = Fatal, Error, Warning, Message, Info\n"
)


class _AlreadyExitedProcess:
    """Deterministic Popen double for pre-monitor launcher exits."""

    def __init__(self, exit_code: int):
        self.pid = 424242
        self.returncode = exit_code

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        del timeout
        return self.returncode


EXPECTED_ASSEMBLY_SHA256 = (
    "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564"
)


@pytest.fixture
def controlled_processes():
    tracked: list[tuple[subprocess.Popen[bytes], int, int]] = []
    pytest_pid = os.getpid()
    pytest_pgid = os.getpgrp()

    def track(process: subprocess.Popen[bytes]):
        pid = process.pid
        pgid = os.getpgid(pid)
        assert pid != pytest_pid
        assert pgid not in {pytest_pgid, 0, 1}
        tracked.append((process, pid, pgid))
        return process

    track.tracked = tracked
    yield track

    def group_exists(pgid: int) -> bool:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    groups = tuple(dict.fromkeys(pgid for _, _, pgid in reversed(tracked)))
    for pgid in groups:
        assert pgid not in {pytest_pgid, 0, 1}
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline and any(
        group_exists(pgid) for pgid in groups
    ):
        for process, _, _ in tracked:
            if process.poll() is not None:
                try:
                    process.wait(timeout=0)
                except (subprocess.TimeoutExpired, ChildProcessError):
                    pass
        time.sleep(0.01)
    for pgid in groups:
        if group_exists(pgid):
            os.killpg(pgid, signal.SIGKILL)
    for process, _, _ in reversed(tracked):
        try:
            process.wait(timeout=0.5)
        except (subprocess.TimeoutExpired, ChildProcessError):
            pass
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline and any(
        group_exists(pgid) for pgid in groups
    ):
        time.sleep(0.01)
    surviving_groups = [
        pgid for pgid in groups if group_exists(pgid)
    ]
    assert not surviving_groups, (
        "controlled process groups survived cleanup",
        surviving_groups,
    )


class _ModuleProxy:
    def __init__(self, base, **overrides):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name: str):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


@pytest.fixture
def tracked_probe_popen(
    monkeypatch: pytest.MonkeyPatch,
    controlled_processes,
):
    original_popen = subprocess.Popen

    def tracked_popen(*args, **kwargs):
        return controlled_processes(original_popen(*args, **kwargs))

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=tracked_popen),
        raising=False,
    )
    return SimpleNamespace(
        original=original_popen,
        popen=tracked_popen,
        tracked=controlled_processes.tracked,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _descriptor_identity(
    observed: os.stat_result,
) -> tuple[int, int, int]:
    return (
        observed.st_dev,
        observed.st_ino,
        stat.S_IFMT(observed.st_mode),
    )


class _InjectedWriterBoundaryError(OSError):
    pass


class _InjectedAcquisitionBoundaryInterrupt(KeyboardInterrupt):
    pass


def _next_line_interrupt_trace(
    target,
    armed,
    interrupt: BaseException,
):
    def trace(frame, event, _arg):
        if (
            event == "line"
            and frame.f_code is target.__code__
            and armed()
        ):
            sys.settrace(None)
            raise interrupt
        return trace

    return trace


def _assert_acquired_descriptors_closed(
    descriptors: list[int],
) -> None:
    leaked: list[int] = []
    for descriptor in dict.fromkeys(descriptors):
        try:
            os.fstat(descriptor)
        except OSError as exc:
            assert exc.errno == errno.EBADF
        else:
            leaked.append(descriptor)
    for descriptor in leaked:
        try:
            os.close(descriptor)
        except OSError as exc:
            assert exc.errno == errno.EBADF
    assert leaked == []


@pytest.mark.parametrize("guard_kind", ["config", "launcher"])
@pytest.mark.parametrize(
    "boundary",
    ["parent-return", "descriptor-return", "guard-handoff"],
)
def test_guard_opener_interrupt_at_acquisition_boundary_closes_each_owner_once(
    guard_kind: str,
    boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / (
        "oracle.cfg" if guard_kind == "config" else "launcher"
    )
    if guard_kind == "config":
        target.write_bytes(ORIGINAL_CONFIG)
        target.chmod(0o640)
    else:
        target.write_bytes(b"#!/bin/sh\nexit 0\n")
        target.chmod(0o755)

    opener = getattr(oracle_boot, f"_open_{guard_kind}_guard")
    guard_name = f"_{guard_kind.title()}Guard"
    original_guard_type = getattr(oracle_boot, guard_name)
    original_open_parent = oracle_boot._open_absolute_directory
    original_open = os.open
    original_close = os.close
    owned: dict[str, int] = {}
    close_calls: dict[str, int] = {}
    constructed_guard = None
    armed = False

    def capture_parent(*args, **kwargs):
        nonlocal armed
        parent = original_open_parent(*args, **kwargs)
        owned["parent"] = parent.fd
        close_calls["parent"] = 0
        if boundary == "parent-return":
            armed = True
        return parent

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal armed
        descriptor = original_open(
            path,
            flags,
            mode,
            dir_fd=dir_fd,
        )
        if dir_fd is not None and os.fspath(path) == target.name:
            owned["file"] = descriptor
            close_calls["file"] = 0
            if boundary == "descriptor-return":
                armed = True
        return descriptor

    def tracked_close(descriptor: int) -> None:
        for role, owned_descriptor in owned.items():
            if descriptor == owned_descriptor:
                close_calls[role] += 1
                if close_calls[role] > 1:
                    raise AssertionError(
                        f"{guard_kind} {role} descriptor closed twice"
                    )
                break
        original_close(descriptor)

    def capture_guard(*args, **kwargs):
        nonlocal armed, constructed_guard
        constructed_guard = original_guard_type(*args, **kwargs)
        if boundary == "guard-handoff":
            armed = True
        return constructed_guard

    monkeypatch.setattr(
        oracle_boot,
        "_open_absolute_directory",
        capture_parent,
    )
    monkeypatch.setattr(
        oracle_boot,
        guard_name,
        capture_guard,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_open,
            close=tracked_close,
        ),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        f"{guard_kind}-{boundary}"
    )
    previous_trace = sys.gettrace()

    try:
        sys.settrace(
            _next_line_interrupt_trace(
                opener,
                lambda: armed,
                interrupt,
            )
        )
        try:
            with pytest.raises(
                _InjectedAcquisitionBoundaryInterrupt,
            ) as raised:
                opener(target)
        finally:
            sys.settrace(previous_trace)

        assert raised.value is interrupt
        assert owned
        assert close_calls == {role: 1 for role in owned}
        _assert_acquired_descriptors_closed(list(owned.values()))
        assert getattr(interrupt, "__notes__", ()) == ()
        if guard_kind == "config":
            assert target.read_bytes() == ORIGINAL_CONFIG
            assert stat.S_IMODE(target.stat().st_mode) == 0o640
    finally:
        sys.settrace(previous_trace)
        if constructed_guard is not None:
            try:
                constructed_guard.close()
            except (OSError, AssertionError):
                pass
        for descriptor in dict.fromkeys(owned.values()):
            try:
                original_close(descriptor)
            except OSError as exc:
                assert exc.errno == errno.EBADF


@pytest.mark.parametrize("guard_kind", ["config", "launcher"])
def test_guard_opener_preserves_primary_and_notes_both_close_failures(
    guard_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    target = tmp_path / (
        "oracle.cfg" if guard_kind == "config" else "launcher"
    )
    if guard_kind == "config":
        target.write_bytes(ORIGINAL_CONFIG)
        target.chmod(0o640)
    else:
        target.write_bytes(b"#!/bin/sh\nexit 0\n")
        target.chmod(0o755)

    class LaterFileCloseError(OSError):
        pass

    class LaterParentCloseError(OSError):
        pass

    primary = RuntimeError(f"primary {guard_kind} acquisition failure")
    opener = getattr(oracle_boot, f"_open_{guard_kind}_guard")
    original_open_parent = oracle_boot._open_absolute_directory
    original_open = os.open
    original_close = os.close
    owned: dict[str, int] = {}
    close_calls = {"file": 0, "parent": 0}

    def capture_parent(*args, **kwargs):
        parent = original_open_parent(*args, **kwargs)
        owned["parent"] = parent.fd
        return parent

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        descriptor = original_open(
            path,
            flags,
            mode,
            dir_fd=dir_fd,
        )
        if dir_fd is not None and os.fspath(path) == target.name:
            owned["file"] = descriptor
        return descriptor

    def close_then_fail(descriptor: int) -> None:
        role = next(
            (
                candidate
                for candidate, owned_descriptor in owned.items()
                if descriptor == owned_descriptor
            ),
            None,
        )
        original_close(descriptor)
        if role is None:
            return
        close_calls[role] += 1
        if role == "file":
            raise LaterFileCloseError("later file close failure")
        raise LaterParentCloseError("later parent close failure")

    def fail_after_both_resources_are_owned(*_args, **_kwargs):
        assert set(owned) == {"file", "parent"}
        raise primary

    monkeypatch.setattr(
        oracle_boot,
        "_open_absolute_directory",
        capture_parent,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_open,
            close=close_then_fail,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        (
            "_read_config_snapshot"
            if guard_kind == "config"
            else "_hash_retained_regular"
        ),
        fail_after_both_resources_are_owned,
    )

    try:
        with pytest.raises(RuntimeError) as raised:
            opener(target)

        assert raised.value is primary
        assert close_calls == {"file": 1, "parent": 1}
        _assert_acquired_descriptors_closed(list(owned.values()))
        notes = getattr(primary, "__notes__", ())
        assert any("later file close failure" in note for note in notes)
        assert any("later parent close failure" in note for note in notes)
        if guard_kind == "config":
            assert target.read_bytes() == ORIGINAL_CONFIG
            assert stat.S_IMODE(target.stat().st_mode) == 0o640
    finally:
        for descriptor in dict.fromkeys(owned.values()):
            try:
                original_close(descriptor)
            except OSError as exc:
                assert exc.errno == errno.EBADF


@pytest.mark.parametrize("guard_kind", ["config", "launcher"])
def test_run_boot_probe_interrupt_after_guard_helper_return_closes_guards(
    guard_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    launcher = _write_executable(
        tmp_path / "launcher",
        "raise SystemExit(0)\n",
    )
    original_open_config = oracle_boot._open_config_guard
    original_open_launcher = oracle_boot._open_launcher_guard
    returned_guards = []
    returned_descriptors: list[int] = []
    armed = False
    launcher_open_calls = 0
    process_calls = 0
    stage_calls = 0
    publish_calls = 0

    def capture_config(path):
        nonlocal armed
        guard = original_open_config(path)
        returned_guards.append(guard)
        returned_descriptors.extend((guard.fd, guard.parent.fd))
        if guard_kind == "config":
            armed = True
        return guard

    def capture_launcher(path):
        nonlocal armed, launcher_open_calls
        launcher_open_calls += 1
        guard = original_open_launcher(path)
        returned_guards.append(guard)
        returned_descriptors.extend((guard.fd, guard.parent.fd))
        if guard_kind == "launcher":
            armed = True
        return guard

    def forbidden_process(*_args, **_kwargs):
        nonlocal process_calls
        process_calls += 1
        raise AssertionError("launcher executed after guard-return interrupt")

    def forbidden_stage(*_args, **_kwargs):
        nonlocal stage_calls
        stage_calls += 1
        raise AssertionError("probe JSON staged after guard-return interrupt")

    def forbidden_publish(*_args, **_kwargs):
        nonlocal publish_calls
        publish_calls += 1
        raise AssertionError(
            "probe JSON published after guard-return interrupt"
        )

    monkeypatch.setattr(
        oracle_boot,
        "_open_config_guard",
        capture_config,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_open_launcher_guard",
        capture_launcher,
    )
    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden_process),
        raising=False,
    )
    monkeypatch.setattr(oracle_boot, "_stage_probe_json", forbidden_stage)
    monkeypatch.setattr(oracle_boot, "_write_probe_json", forbidden_publish)
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        f"run-after-{guard_kind}-guard-return"
    )
    previous_trace = sys.gettrace()

    try:
        sys.settrace(
            _next_line_interrupt_trace(
                oracle_boot.run_boot_probe,
                lambda: armed,
                interrupt,
            )
        )
        try:
            with pytest.raises(
                _InjectedAcquisitionBoundaryInterrupt,
            ) as raised:
                oracle_boot.run_boot_probe(
                    layout.game,
                    launcher,
                    layout.config,
                    layout.evidence,
                    2,
                )
        finally:
            sys.settrace(previous_trace)

        assert raised.value is interrupt
        assert len(returned_guards) == (
            1 if guard_kind == "config" else 2
        )
        assert len(returned_descriptors) == (
            2 if guard_kind == "config" else 4
        )
        _assert_acquired_descriptors_closed(returned_descriptors)
        assert launcher_open_calls == (
            0 if guard_kind == "config" else 1
        )
        assert process_calls == 0
        assert stage_calls == 0
        assert publish_calls == 0
        assert layout.config.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
        _assert_no_canonical_probe_json(layout.evidence)
        if layout.evidence.exists():
            assert tuple(
                layout.evidence.rglob(".probe-json-*.pending")
            ) == ()
    finally:
        sys.settrace(previous_trace)
        for guard in reversed(returned_guards):
            try:
                guard.close()
            except OSError:
                pass


class _OwnedDescriptorRecord:
    def __init__(
        self,
        descriptor: int,
        generation: int,
        identity: tuple[int, int, int],
        role: str,
    ):
        self.descriptor = descriptor
        self.generation = generation
        self.identity = identity
        self.role = role


class _OwnedWriterDescriptors:
    """Track only descriptors opened by the writer under test."""

    def __init__(self, evidence: Path, boundary: str):
        self.evidence = evidence
        observed_evidence = evidence.stat(follow_symlinks=False)
        self.evidence_identity = _descriptor_identity(observed_evidence)
        self.boundary = boundary
        self.injection_reached = False
        self._real_open = os.open
        self._real_close = os.close
        self._real_fsync = os.fsync
        self._real_fstat = os.fstat
        self._generation = 0
        self._owned: dict[int, _OwnedDescriptorRecord] = {}
        self._open_order: list[_OwnedDescriptorRecord] = []
        self._reuse_events: list[_OwnedDescriptorRecord] = []
        self._pending_identity: tuple[int, int] | None = None

    def _discover_pending_identity(self) -> tuple[int, int]:
        directory_fd = self._real_open(
            self.evidence,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            candidates: list[tuple[int, int]] = []
            for name in os.listdir(directory_fd):
                if not (
                    name.startswith(".probe-json-")
                    and name.endswith(".pending")
                ):
                    continue
                observed = os.stat(
                    name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                assert stat.S_ISREG(observed.st_mode)
                assert stat.S_IMODE(observed.st_mode) == 0o600
                candidates.append((observed.st_dev, observed.st_ino))
        finally:
            self._real_close(directory_fd)
        assert len(candidates) == 1, candidates
        return candidates[0]

    def _matching_record(
        self,
        descriptor: int,
    ) -> _OwnedDescriptorRecord | None:
        record = self._owned.get(descriptor)
        if record is None:
            return None
        try:
            current = _descriptor_identity(
                self._real_fstat(descriptor)
            )
        except OSError as exc:
            if exc.errno != errno.EBADF:
                raise
            if self._owned.get(descriptor) is record:
                del self._owned[descriptor]
            return None
        if current != record.identity:
            if self._owned.get(descriptor) is record:
                del self._owned[descriptor]
            self._reuse_events.append(record)
            return None
        return record

    def open(
        self,
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        parent = (
            self._matching_record(dir_fd)
            if dir_fd is not None
            else None
        )
        if dir_fd is None:
            descriptor = self._real_open(path, flags, mode)
        else:
            descriptor = self._real_open(
                path,
                flags,
                mode,
                dir_fd=dir_fd,
            )
        stale = self._owned.pop(descriptor, None)
        if stale is not None:
            self._reuse_events.append(stale)
        try:
            observed = self._real_fstat(descriptor)
        except BaseException:
            self._real_close(descriptor)
            raise
        identity = _descriptor_identity(observed)
        record = _OwnedDescriptorRecord(
            descriptor,
            self._generation,
            identity,
            "other",
        )
        self._generation += 1
        self._owned[descriptor] = record
        self._open_order.append(record)
        if (
            stat.S_ISDIR(observed.st_mode)
            and identity == self.evidence_identity
        ):
            record.role = "evidence_candidate"
        exclusive_writable_create = (
            bool(flags & os.O_CREAT)
            and bool(flags & os.O_EXCL)
            and (flags & os.O_ACCMODE) in (os.O_WRONLY, os.O_RDWR)
        )
        if (
            parent is not None
            and self._owned.get(parent.descriptor) is parent
            and parent.role
            in {"evidence_candidate", "writer_directory"}
            and exclusive_writable_create
            and stat.S_ISREG(observed.st_mode)
        ):
            record.role = "writer_file"
            parent.role = "writer_directory"
        return descriptor

    def _raise_after_boundary(self, role: str, operation: str) -> None:
        boundary_role = {
            "writer_file": "file",
            "writer_directory": "directory",
        }.get(role)
        if (
            boundary_role is not None
            and not self.injection_reached
            and self.boundary == f"{boundary_role}_{operation}"
        ):
            self.injection_reached = True
            raise _InjectedWriterBoundaryError(
                f"injected after writer {boundary_role} {operation}"
            )

    def fsync(self, descriptor: int) -> None:
        record = self._matching_record(descriptor)
        if record is None:
            raise AssertionError(
                f"writer attempted fsync on unowned descriptor {descriptor}"
            )
        if record.role == "writer_file":
            if self._pending_identity is None:
                self._pending_identity = self._discover_pending_identity()
            assert record.identity[:2] == self._pending_identity
            assert stat.S_ISREG(record.identity[2])
        elif record.role == "writer_directory":
            assert record.identity == self.evidence_identity
        else:
            raise AssertionError(
                f"writer attempted fsync on unrelated descriptor {descriptor}"
            )
        self._real_fsync(descriptor)
        self._raise_after_boundary(record.role, "fsync")

    def close(self, descriptor: int) -> None:
        record = self._matching_record(descriptor)
        if record is None:
            raise AssertionError(
                f"writer attempted close on unowned descriptor {descriptor}"
            )
        self._real_close(descriptor)
        if self._owned.get(descriptor) is record:
            del self._owned[descriptor]
            self._raise_after_boundary(record.role, "close")

    def reclaim_matching_owned(
        self,
    ) -> tuple[
        tuple[int, ...],
        tuple[int, ...],
        tuple[tuple[int, OSError], ...],
    ]:
        reclaimed: list[int] = []
        cleanup_errors: list[tuple[int, OSError]] = []
        for record in reversed(self._open_order):
            descriptor = record.descriptor
            if self._owned.get(descriptor) is not record:
                continue
            if self._matching_record(descriptor) is not record:
                continue
            try:
                self._real_close(descriptor)
            except OSError as exc:
                cleanup_errors.append((descriptor, exc))
                continue
            if self._owned.get(descriptor) is record:
                del self._owned[descriptor]
            reclaimed.append(descriptor)
        return (
            tuple(reclaimed),
            tuple(record.descriptor for record in self._reuse_events),
            tuple(cleanup_errors),
        )

    def assert_canonical_identity(self) -> None:
        assert self._pending_identity is not None
        canonical = self.evidence / "probe.json"
        observed = canonical.stat(follow_symlinks=False)
        assert (observed.st_dev, observed.st_ino) == self._pending_identity


def _assert_probe_commit_tree(
    evidence: Path,
    expected_payload: bytes,
    *,
    returned: bool,
) -> None:
    entries = {
        relative: (kind, payload)
        for relative, kind, payload in _test_tree_snapshot(evidence)
    }
    assert entries.pop("keep.bin") == (
        "file",
        b"evidence sentinel survives",
    )
    if returned:
        assert entries == {
            "probe.json": ("file", expected_payload),
        }
        assert json.loads((evidence / "probe.json").read_bytes()) == {
            "schema_version": 1,
            "success": True,
        }
        return

    assert "probe.json" not in entries
    assert len(entries) <= 1
    for relative, (kind, payload) in entries.items():
        pending = evidence / relative
        assert kind == "file"
        assert payload == expected_payload
        assert stat.S_IMODE(
            pending.stat(follow_symlinks=False).st_mode
        ) == 0o600


def _test_tree_snapshot(root: Path) -> tuple[tuple[str, str, bytes], ...]:
    if not root.exists():
        return ()
    entries: list[tuple[str, str, bytes]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        observed = path.stat(follow_symlinks=False)
        if stat.S_ISDIR(observed.st_mode):
            entries.append((relative, "directory", b""))
        elif stat.S_ISLNK(observed.st_mode):
            entries.append(
                (relative, "symlink", os.readlink(path).encode())
            )
        elif stat.S_ISREG(observed.st_mode):
            entries.append((relative, "file", path.read_bytes()))
        elif stat.S_ISFIFO(observed.st_mode):
            entries.append((relative, "fifo", b""))
        elif stat.S_ISSOCK(observed.st_mode):
            entries.append((relative, "socket", b""))
        else:
            entries.append((relative, "other", b""))
    return tuple(entries)


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


def _write_executable(path: Path, body: str) -> Path:
    path.write_text(
        "#!/usr/bin/env python3\n"
        + textwrap.dedent(body).lstrip(),
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _launcher(
    tmp_path: Path,
    *,
    log_text: str,
    log_relative: str = "nested/preloader_probe.log",
    additional_logs: tuple[tuple[str, str], ...] = (),
    linger_seconds: float = 60.0,
    ignore_term: bool = False,
    spawn_descendant: bool = False,
    observed_config: Path | None = None,
    mutate_config_to: bytes | None = None,
    changed_log: Path | None = None,
    changed_log_text: str = "",
    exit_code: int | None = None,
    term_append_text: str | None = None,
) -> Path:
    descendant_setup = ""
    if spawn_descendant:
        descendant_setup = (
            "descendant = subprocess.Popen([sys.executable, '-c', "
            "'import signal,time;"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
            "print(\"ready\", flush=True);"
            "time.sleep(60)'], "
            "stdout=subprocess.PIPE, text=True); "
            "assert descendant.stdout is not None; "
            "assert descendant.stdout.readline() == 'ready\\n'; "
            "descendant.stdout.close(); "
            "(root / 'descendant.pid').write_text("
            "str(descendant.pid), encoding='ascii'); "
            "(root / 'descendant.pgid').write_text("
            "str(os.getpgid(descendant.pid)), encoding='ascii')"
        )
    config_setup = ""
    if observed_config is not None:
        observed_bytes = tmp_path / "observed-config.bin"
        observed_mode = tmp_path / "observed-config.mode"
        config_setup = (
            f"observed_config = Path({str(observed_config)!r}); "
            f"Path({str(observed_bytes)!r}).write_bytes("
            "observed_config.read_bytes()); "
            f"Path({str(observed_mode)!r}).write_text("
            "oct(observed_config.stat().st_mode & 0o7777), "
            "encoding='ascii'); "
        )
        if mutate_config_to is not None:
            config_setup += (
                f"observed_config.write_bytes({mutate_config_to!r}); "
                "observed_config.chmod(0o600)"
            )
    changed_log_setup = ""
    if changed_log is not None:
        changed_log_setup = (
            f"changed_log = Path({str(changed_log)!r}); "
            "changed_log.parent.mkdir(parents=True, exist_ok=True); "
            f"changed_log.write_text({changed_log_text!r}, encoding='utf-8')"
        )
    termination_setup = ""
    if term_append_text is not None:
        termination_setup = textwrap.indent(
            textwrap.dedent(
                f"""
                def append_log_on_term(_signum, _frame):
                    with log.open("a", encoding="utf-8") as stream:
                        stream.write({term_append_text!r})
                        stream.flush()
                        os.fsync(stream.fileno())
                    raise SystemExit(0)

                signal.signal(signal.SIGTERM, append_log_on_term)
                """
            ).strip(),
            "        ",
        )
    elif ignore_term:
        termination_setup = (
            "        signal.signal(signal.SIGTERM, signal.SIG_IGN)"
        )
    return _write_executable(
        tmp_path / f"launcher-{time.monotonic_ns()}.py",
        f"""
        import os
        from pathlib import Path
        import signal
        import subprocess
        import sys
        import time

        root = Path.cwd()
        (root / "spawned.pid").write_text(str(os.getpid()), encoding="ascii")
        (root / "spawned.pgid").write_text(
            str(os.getpgrp()), encoding="ascii"
        )
        {config_setup}
        {changed_log_setup}
        {descendant_setup}
        log = root / {log_relative!r}
        log.parent.mkdir(parents=True, exist_ok=True)
        for relative, text in {additional_logs!r}:
            additional_log = root / relative
            additional_log.parent.mkdir(parents=True, exist_ok=True)
            additional_log.write_text(text, encoding="utf-8")
{termination_setup}
        log.write_text({log_text!r}, encoding="utf-8")
        {("raise SystemExit(" + str(exit_code) + ")" if exit_code is not None else "time.sleep(" + repr(linger_seconds) + ")")}
        """,
    )


def _probe_layout(tmp_path: Path) -> SimpleNamespace:
    game = tmp_path / "game"
    game.mkdir()
    app = game / "Sausage.app"
    managed = app / "Contents/Resources/Data/Managed"
    managed.mkdir(parents=True)
    config = tmp_path / "oracle.cfg"
    config.write_bytes(ORIGINAL_CONFIG)
    config.chmod(0o640)
    evidence = tmp_path / "evidence"

    # Real hashes are intentionally exercised even when install/signature
    # discovery is patched at the external boundary.
    assembly = managed / "Assembly-CSharp.dll"
    assembly.write_bytes(b"controlled assembly")
    preloader = game / "BepInEx/core/BepInEx.Preloader.dll"
    preloader.parent.mkdir(parents=True)
    preloader.write_bytes(b"controlled patched preloader")
    bepinex = game / "BepInEx"
    bepinex_config = bepinex / "config/BepInEx.cfg"
    bepinex_config.parent.mkdir()
    return SimpleNamespace(
        game=game,
        app=app,
        config=config,
        evidence=evidence,
        assembly=assembly,
        preloader=preloader,
        bepinex=bepinex,
        bepinex_config=bepinex_config,
        canonical_log=bepinex / "LogOutput.log",
        fallback_logs=tuple(
            bepinex / f"LogOutput.log.{index}" for index in range(1, 5)
        ),
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"[Logging.Disk]\nEnabled = true\nAppendLog = false\nLogLevels = Fatal, Error, Warning, Message, Info\n",
        b"\xef\xbb\xbf [Logging.Disk] \r\n Enabled = TRUE \r\n AppendLog = False \r\n LogLevels = All \r\n",
        b"[Other]\nValue = okay\n[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=debug,info,message,warning,error,fatal\n",
        b"[Logging.Console]\nLogLevels = Fatal, Error, Warning, Message, Info\n[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=All\n",
        b"[Logging.Console]\nOther = value\n[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=All\n",
    ],
    ids=(
        "required-levels",
        "leading-bom-and-outer-whitespace",
        "unrelated-section-and-debug",
        "configured-console",
        "pinned-console-defaults",
    ),
)
def test_bepinex_disk_config_parser_accepts_pinned_contracts(
    payload: bytes,
    tmp_path: Path,
):
    path = tmp_path / "BepInEx/config/BepInEx.cfg"

    assert oracle_boot._parse_bepinex_disk_logging(payload, path) is None


@pytest.mark.parametrize(
    ("case", "payload"),
    [
        ("disabled", b"[Logging.Disk]\nEnabled=false\nAppendLog=false\nLogLevels=Fatal,Error,Warning,Message,Info\n"),
        ("append", b"[Logging.Disk]\nEnabled=true\nAppendLog=true\nLogLevels=Fatal,Error,Warning,Message,Info\n"),
        ("too-few-levels", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=Message,Info\n"),
        ("missing-enabled", b"[Logging.Disk]\nAppendLog=false\nLogLevels=Fatal,Error,Warning,Message,Info\n"),
        ("missing-append", b"[Logging.Disk]\nEnabled=true\nLogLevels=Fatal,Error,Warning,Message,Info\n"),
        ("missing-levels", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\n"),
        ("duplicate-disk-section", BEPINEX_DISK_CONFIG + BEPINEX_DISK_CONFIG),
        ("duplicate-enabled", b"[Logging.Disk]\nEnabled=true\nEnabled=true\nAppendLog=false\nLogLevels=All\n"),
        ("lowercase-section", b"[logging.disk]\nEnabled=true\nAppendLog=false\nLogLevels=All\n"),
        ("section-whitespace-lookalike", b"[Logging. Disk]\nEnabled=true\nAppendLog=false\nLogLevels=All\n"),
        ("lowercase-key", b"[Logging.Disk]\nenabled=true\nAppendLog=false\nLogLevels=All\n"),
        ("key-whitespace-lookalike", b"[Logging.Disk]\nEnabled=true\nAppend Log=false\nLogLevels=All\n"),
        ("unknown-level", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=Fatal,Error,Warning,Message,Trace\n"),
        ("numeric-level", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=Fatal,Error,Warning,Message,1\n"),
        ("duplicate-level", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=Fatal,Error,Warning,Message,Info,Info\n"),
        ("none-level", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=None\n"),
        ("all-plus-debug", b"[Logging.Disk]\nEnabled=true\nAppendLog=false\nLogLevels=All,Debug\n"),
        ("nul", BEPINEX_DISK_CONFIG + b"\x00"),
        ("invalid-utf8", BEPINEX_DISK_CONFIG + b"\xff"),
        ("embedded-bom", BEPINEX_DISK_CONFIG + b"\xef\xbb\xbf"),
        ("bare-cr", b"[Logging.Disk]\nEnabled=true\rAppendLog=false\nLogLevels=All\n"),
        ("inline-comment", b"[Logging.Disk]\nEnabled=true # required\nAppendLog=false\nLogLevels=All\n"),
        ("malformed-line", BEPINEX_DISK_CONFIG + b"malformed\n"),
        ("incomplete-section", BEPINEX_DISK_CONFIG + b"[Other\n"),
        ("extra-section-syntax", BEPINEX_DISK_CONFIG + b"[Other] trailing\n"),
        ("console-levels-do-not-count-for-disk", b"[Logging.Console]\nLogLevels=All\n[Logging.Disk]\nEnabled=true\nAppendLog=false\n"),
    ],
)
def test_bepinex_disk_config_parser_rejects_invalid_disk_contract(
    case: str,
    payload: bytes,
    tmp_path: Path,
):
    del case
    path = tmp_path / "BepInEx/config/BepInEx.cfg"

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._parse_bepinex_disk_logging(payload, path)

    assert str(path) in str(raised.value)


@pytest.mark.parametrize(
    ("case", "console"),
    [
        ("missing-fatal", b"LogLevels=Error,Warning,Message,Info\n"),
        ("missing-error", b"LogLevels=Fatal,Warning,Message,Info\n"),
        ("missing-warning", b"LogLevels=Fatal,Error,Message,Info\n"),
        ("missing-message", b"LogLevels=Fatal,Error,Warning,Info\n"),
        ("missing-info", b"LogLevels=Fatal,Error,Warning,Message\n"),
        ("duplicate-key", b"LogLevels=All\nLogLevels=All\n"),
        ("none", b"LogLevels=None\n"),
        ("all-plus-debug", b"LogLevels=All, Debug\n"),
        ("lowercase-key", b"loglevels=All\n"),
        ("whitespace-key", b"Log Levels=All\n"),
    ],
)
def test_bepinex_disk_config_parser_rejects_invalid_console_contract(
    case: str,
    console: bytes,
    tmp_path: Path,
):
    del case
    path = tmp_path / "BepInEx/config/BepInEx.cfg"
    payload = b"[Logging.Console]\n" + console + BEPINEX_DISK_CONFIG

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._parse_bepinex_disk_logging(payload, path)

    assert str(path) in str(raised.value)


@pytest.mark.parametrize(
    "payload",
    [
        b"[Logging.Console]\nOther=value\n[Logging.Console]\nOther=value\n" + BEPINEX_DISK_CONFIG,
        b"[logging.console]\nLogLevels=All\n" + BEPINEX_DISK_CONFIG,
        b"[Logging. Console]\nLogLevels=All\n" + BEPINEX_DISK_CONFIG,
    ],
    ids=("duplicate-console-section", "lowercase-console-section", "console-section-whitespace"),
)
def test_bepinex_disk_config_parser_rejects_invalid_console_sections(
    payload: bytes,
    tmp_path: Path,
):
    path = tmp_path / "BepInEx/config/BepInEx.cfg"

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._parse_bepinex_disk_logging(payload, path)

    assert str(path) in str(raised.value)


def test_bepinex_disk_config_guard_records_absent_leaf(
    tmp_path: Path,
):
    bepinex = tmp_path / "game/BepInEx"
    (bepinex / "config").mkdir(parents=True)

    guard = oracle_boot._open_bepinex_disk_logging_guard(tmp_path / "game")
    try:
        assert guard.bepinex is not None
        assert guard.config is not None
        assert guard.fd == -1
        assert guard.original is None
    finally:
        guard.close()


def test_bepinex_disk_config_guard_records_absent_config_directory(
    tmp_path: Path,
):
    bepinex = tmp_path / "game/BepInEx"
    bepinex.mkdir(parents=True)

    guard = oracle_boot._open_bepinex_disk_logging_guard(tmp_path / "game")
    try:
        assert guard.bepinex is not None
        assert guard.config is None
        assert guard.fd == -1
        assert guard.original is None
    finally:
        guard.close()


def test_bepinex_disk_config_guard_consumes_valid_existing_config(
    tmp_path: Path,
):
    path = tmp_path / "game/BepInEx/config/BepInEx.cfg"
    path.parent.mkdir(parents=True)
    path.write_bytes(BEPINEX_DISK_CONFIG)
    path.chmod(0o640)
    guard = oracle_boot._open_bepinex_disk_logging_guard(tmp_path / "game")

    assert guard.config is not None
    assert guard.original is not None
    assert guard.original.payload == BEPINEX_DISK_CONFIG
    contract = oracle_boot._verify_and_close_bepinex_disk_logging_guard(guard)

    assert contract.canonical_overwrite is True
    assert guard.fd == -1
    assert guard.config.fd == -1
    assert guard.bepinex.fd == -1


@pytest.mark.parametrize("entry_kind", ["symlink", "fifo"])
def test_bepinex_disk_config_guard_rejects_unsafe_leaf_without_following(
    entry_kind: str,
    tmp_path: Path,
):
    path = tmp_path / "game/BepInEx/config/BepInEx.cfg"
    path.parent.mkdir(parents=True)
    if entry_kind == "symlink":
        target = tmp_path / "target.cfg"
        target.write_bytes(BEPINEX_DISK_CONFIG)
        path.symlink_to(target)
    else:
        os.mkfifo(path)

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._open_bepinex_disk_logging_guard(tmp_path / "game")

    assert str(path) in str(raised.value)


def test_bepinex_disk_config_guard_rejects_symlinked_config_parent(
    tmp_path: Path,
):
    bepinex = tmp_path / "game/BepInEx"
    bepinex.mkdir(parents=True)
    real_config = tmp_path / "real-config"
    real_config.mkdir()
    (bepinex / "config").symlink_to(real_config, target_is_directory=True)

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._open_bepinex_disk_logging_guard(tmp_path / "game")

    assert str(bepinex / "config") in str(raised.value)


@pytest.mark.parametrize(
    "mutation",
    [
        "content",
        "same-bytes-new-inode",
        "absent-leaf-invalid",
        "absent-leaf-valid",
        "absent-config-directory",
        "replace-config-directory",
        "replace-bepinex-directory",
    ],
)
def test_bepinex_disk_config_prelaunch_revalidation_blocks_changed_state(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    if mutation not in {
        "absent-leaf-invalid",
        "absent-leaf-valid",
        "absent-config-directory",
    }:
        layout.bepinex_config.write_bytes(BEPINEX_DISK_CONFIG)
        layout.bepinex_config.chmod(0o640)
    if mutation == "absent-config-directory":
        layout.bepinex_config.parent.rmdir()

    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        exit_code=0,
    )
    original_verify = oracle_boot._verify_config_guard_unchanged
    verify_calls = 0
    popen_calls = 0

    def mutate_after_last_oracle_config_verification(guard):
        nonlocal verify_calls
        original_verify(guard)
        verify_calls += 1
        if verify_calls != 2:
            return
        if mutation == "content":
            layout.bepinex_config.write_bytes(
                BEPINEX_DISK_CONFIG.replace(b"false", b"true")
            )
        elif mutation == "same-bytes-new-inode":
            replacement = layout.bepinex_config.with_suffix(".new")
            replacement.write_bytes(BEPINEX_DISK_CONFIG)
            replacement.chmod(0o640)
            os.replace(replacement, layout.bepinex_config)
        elif mutation == "absent-leaf-invalid":
            layout.bepinex_config.write_bytes(b"invalid\n")
        elif mutation == "absent-leaf-valid":
            layout.bepinex_config.write_bytes(BEPINEX_DISK_CONFIG)
        elif mutation == "absent-config-directory":
            layout.bepinex_config.parent.mkdir()
        elif mutation == "replace-config-directory":
            displaced = layout.bepinex / "config.displaced"
            layout.bepinex_config.parent.rename(displaced)
            layout.bepinex_config.parent.mkdir()
            layout.bepinex_config.write_bytes(BEPINEX_DISK_CONFIG)
        else:
            displaced = layout.game / "BepInEx.displaced"
            layout.bepinex.rename(displaced)
            layout.bepinex_config.parent.mkdir(parents=True)
            layout.bepinex_config.write_bytes(BEPINEX_DISK_CONFIG)

    class ForbiddenLaunch(AssertionError):
        pass

    def forbidden_popen(*_args, **_kwargs):
        nonlocal popen_calls
        popen_calls += 1
        raise ForbiddenLaunch("changed BepInEx config state reached Popen")

    monkeypatch.setattr(
        oracle_boot,
        "_verify_config_guard_unchanged",
        mutate_after_last_oracle_config_verification,
    )
    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden_popen),
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot.run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except BaseException as exc:
        raised = exc

    assert isinstance(raised, oracle_boot.BootProbeError)
    assert verify_calls == 2
    assert popen_calls == 0
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    assert not (layout.game / "spawned.pid").exists()
    assert not (layout.game / "spawned.pgid").exists()
    _assert_no_canonical_probe_json(layout.evidence)


def _tahoe_code_signature_lines(app: Path) -> tuple[str, ...]:
    bundle = (
        app.resolve()
        / "Contents"
        / "Plugins"
        / "Foregroundr.bundle"
    )
    return (
        f"file added: {bundle / 'Contents/_CodeSignature/CodeResources'}\n",
        f"file added: {bundle / 'Contents/_CodeSignature/CodeDirectory'}\n",
        f"file added: {bundle / 'Contents/_CodeSignature/CodeRequirements'}\n",
        f"file added: {bundle / 'Contents/_CodeSignature/CodeSignature'}\n",
        f"file added: {bundle / 'Contents/MacOS/Foregroundr'}\n",
        f"file added: {bundle / 'Contents/Info.plist'}\n",
        f"file missing: {bundle}\n",
    )


def _tahoe_code_signature(
    app: Path,
    *,
    stdout_lines: tuple[str, ...] | None = None,
    stderr: str | None = None,
    returncode: int = 1,
) -> oracle_boot._AppSignature:
    lines = (
        _tahoe_code_signature_lines(app)
        if stdout_lines is None
        else stdout_lines
    )
    diagnostic = (
        f"{app.resolve()}: a sealed resource is missing or invalid\n"
        if stderr is None
        else stderr
    )
    return oracle_boot._AppSignature(
        returncode=returncode,
        stdout="".join(lines),
        stderr=diagnostic,
    )


def _clean_code_signature(app: Path) -> oracle_boot._AppSignature:
    resolved = app.resolve()
    return oracle_boot._AppSignature(
        returncode=0,
        stdout="",
        stderr=(
            f"{resolved}: valid on disk\n"
            f"{resolved}: satisfies its Designated Requirement\n"
        ),
    )


def _patch_healthy_preflight(
    monkeypatch: pytest.MonkeyPatch, layout: SimpleNamespace
) -> None:
    monkeypatch.setattr(
        oracle_boot,
        "EXPECTED_ASSEMBLY_SHA256",
        _sha256(layout.assembly),
        raising=False,
    )
    compatibility = SimpleNamespace(
        state="patched",
        official_sha256="0" * 64,
        active_sha256=_sha256(layout.preloader),
        patched_sha256=_sha256(layout.preloader),
        issues=(),
    )
    manifest = SimpleNamespace(
        game_assembly_sha256=_sha256(layout.assembly),
        assembly_sha256=_sha256(layout.assembly),
    )
    status = SimpleNamespace(
        healthy=True,
        missing=(),
        changed=(),
        manifest=manifest,
        preloader_compatibility=compatibility,
    )
    monkeypatch.setattr(oracle_boot, "status_install", lambda _root: status)

    monkeypatch.setattr(
        oracle_boot,
        "_capture_app_signature",
        lambda app: _tahoe_code_signature(app),
        raising=False,
    )


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _wait_for_pid_exit(pid: int, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_exists(pid):
            return True
        time.sleep(0.02)
    return not _pid_exists(pid)


def _wait_for_group_exit(pgid: int, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.01)
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    return False


def _assert_tracked_probe_groups_stopped(tracked_probe_popen) -> None:
    assert tracked_probe_popen.tracked
    for process, _, pgid in tracked_probe_popen.tracked:
        assert process.poll() is not None
        assert _wait_for_group_exit(pgid), pgid


class _InjectedCleanupCloseError(RuntimeError):
    pass


class _InjectedPrimaryRestoreError(RuntimeError):
    pass


def _inject_retained_cleanup_close_failure(
    monkeypatch: pytest.MonkeyPatch,
    cleanup_guard: str,
) -> SimpleNamespace:
    state = SimpleNamespace(
        target=None,
        reached=False,
        message=f"injected {cleanup_guard} cleanup close failure",
    )

    if cleanup_guard == "launcher_guard":
        original_open = oracle_boot._open_launcher_guard
        original_close = oracle_boot._LauncherGuard.close

        def capture_target(path):
            guard = original_open(path)
            assert state.target is None
            state.target = guard
            return guard

        def close_then_fail(guard) -> None:
            is_target = guard is state.target
            original_close(guard)
            if is_target and not state.reached:
                state.reached = True
                raise _InjectedCleanupCloseError(state.message)

        monkeypatch.setattr(
            oracle_boot,
            "_open_launcher_guard",
            capture_target,
            raising=False,
        )
        monkeypatch.setattr(
            oracle_boot._LauncherGuard,
            "close",
            close_then_fail,
        )
    elif cleanup_guard == "retained_game_handle":
        original_verify = oracle_boot._verify_pinned_directory_path
        original_close = oracle_boot._DirectoryHandle.close

        def capture_target(path, pinned, label) -> None:
            if label == "game root at launch":
                assert state.target is None or state.target is pinned
                state.target = pinned
            original_verify(path, pinned, label)

        def close_then_fail(handle) -> None:
            is_target = handle is state.target
            original_close(handle)
            if is_target and not state.reached:
                state.reached = True
                raise _InjectedCleanupCloseError(state.message)

        monkeypatch.setattr(
            oracle_boot,
            "_verify_pinned_directory_path",
            capture_target,
            raising=False,
        )
        monkeypatch.setattr(
            oracle_boot._DirectoryHandle,
            "close",
            close_then_fail,
        )
    elif cleanup_guard == "config_guard":
        original_open = oracle_boot._open_config_guard
        original_close = oracle_boot._ConfigGuard.close

        def capture_target(path):
            guard = original_open(path)
            assert state.target is None
            state.target = guard
            return guard

        def close_then_fail(guard) -> None:
            is_target = guard is state.target
            original_close(guard)
            if is_target and not state.reached:
                state.reached = True
                raise _InjectedCleanupCloseError(state.message)

        monkeypatch.setattr(
            oracle_boot,
            "_open_config_guard",
            capture_target,
            raising=False,
        )
        monkeypatch.setattr(
            oracle_boot._ConfigGuard,
            "close",
            close_then_fail,
        )
    else:
        raise AssertionError(f"unknown cleanup guard: {cleanup_guard}")

    return state


def test_boot_public_records_have_exact_frozen_slotted_schemas(
    tmp_path: Path,
):
    fingerprint = oracle_boot.LogFingerprint(
        path=(tmp_path / "preloader_a.log").resolve(),
        file_type="regular",
        inode=11,
        size=12,
        mtime_ns=13,
        sha256="a" * 64,
    )
    evidence = oracle_boot.BootEvidence(
        evidence_dir=(tmp_path / "evidence").resolve(),
        moved_logs=((tmp_path / "moved.log").resolve(),),
        copied_logs=((tmp_path / "copied.log").resolve(),),
        issues=("changed",),
    )
    result = oracle_boot.BootProbeResult(
        success=False,
        evidence_dir=evidence.evidence_dir,
        moved_logs=evidence.moved_logs,
        copied_logs=evidence.copied_logs,
        markers=(REQUIRED_MARKERS[0],),
        issues=evidence.issues,
        exit_code=None,
    )

    assert [field.name for field in fields(type(fingerprint))] == [
        "path",
        "file_type",
        "inode",
        "size",
        "mtime_ns",
        "sha256",
    ]
    assert [field.name for field in fields(type(evidence))] == [
        "evidence_dir",
        "moved_logs",
        "copied_logs",
        "issues",
    ]
    assert [field.name for field in fields(type(result))] == [
        "success",
        "evidence_dir",
        "moved_logs",
        "copied_logs",
        "markers",
        "issues",
        "exit_code",
    ]
    mutations = [
        (fingerprint, "sha256", "b" * 64, "a" * 64),
        (evidence, "issues", (), ("changed",)),
        (result, "success", True, False),
    ]
    for record, field_name, replacement, original in mutations:
        assert not hasattr(record, "__dict__")
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, field_name, replacement)
        assert getattr(record, field_name) == original


def test_fingerprint_logs_is_recursive_case_sensitive_and_exact(
    tmp_path: Path,
):
    game = tmp_path / "game"
    (game / "a/deep").mkdir(parents=True)
    (game / "B").mkdir()
    matching = [
        game / "B/preloader_a.log",
        game / "a/deep/preloader_z.log",
        game / "preloader_root.log",
        game / "BepInEx/LogOutput.log",
        game / "BepInEx/LogOutput.log.1",
        game / "BepInEx/LogOutput.log.4",
    ]
    (game / "BepInEx").mkdir()
    payloads = [b"B", b"nested", b"root", b"canonical", b"one", b"four"]
    for path, payload in zip(matching, payloads, strict=True):
        path.write_bytes(payload)
    (game / "Preloader_wrong.log").write_bytes(b"wrong case")
    (game / "preloader_wrong.LOG").write_bytes(b"wrong suffix")
    (game / "not_preloader.log").write_bytes(b"wrong prefix")
    (game / "BepInEx/logoutput.log").write_bytes(b"wrong case")
    (game / "BepInEx/LogOutput.log.0").write_bytes(b"wrong index")
    (game / "BepInEx/LogOutput.log.5").write_bytes(b"wrong index")
    (game / "BepInEx/nested").mkdir()
    (game / "BepInEx/nested/LogOutput.log").write_bytes(b"wrong parent")

    outside = tmp_path / "outside"
    outside.mkdir()
    outside_log = outside / "preloader_outside.log"
    outside_log.write_bytes(b"must not be read")
    (game / "linked-directory").symlink_to(
        outside, target_is_directory=True
    )
    expected_stats = {
        path.resolve(): path.stat(follow_symlinks=False)
        for path in matching
    }

    observed = fingerprint_preloader_logs(game)

    expected_paths = sorted(
        (path.resolve() for path in matching),
        key=lambda path: path.relative_to(game.resolve()).as_posix(),
    )
    assert [item.path for item in observed] == expected_paths
    for item in observed:
        expected_stat = expected_stats[item.path]
        assert item.file_type == "regular"
        assert item.inode == expected_stat.st_ino
        assert item.size == expected_stat.st_size
        assert item.mtime_ns == expected_stat.st_mtime_ns
        assert item.sha256 == _sha256(item.path)
        assert item.path.is_absolute()
        assert item.path.is_relative_to(game.resolve())
    assert outside_log.read_bytes() == b"must not be read"


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        (Path("BepInEx/LogOutput.log"), "canonical"),
        (Path("BepInEx/LogOutput.log.1"), "fallback"),
        (Path("BepInEx/LogOutput.log.4"), "fallback"),
        (Path("preloader_root.log"), "preloader"),
        (Path("nested/preloader_failure.log"), "preloader"),
        (Path("BepInEx/logoutput.log"), None),
        (Path("BepInEx/LogOutput.log.0"), None),
        (Path("BepInEx/LogOutput.log.5"), None),
        (Path("BepInEx/nested/LogOutput.log"), None),
        (Path("preloader_wrong.LOG"), None),
    ],
)
def test_boot_log_kind_classifies_exact_relative_paths(
    relative_path: Path,
    expected: str | None,
):
    assert oracle_boot._boot_log_kind(relative_path) == expected


@pytest.mark.parametrize(
    "unsafe_kind",
    [
        "matching_symlink",
        "matching_fifo",
        "canonical_symlink",
        "canonical_fifo",
        "fallback_symlink",
        "fallback_fifo",
        "root_symlink",
        "symlink_parent",
    ],
)
def test_fingerprint_rejects_unsafe_monitored_or_special_paths_without_hashing(
    unsafe_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    real_parent = tmp_path / "real-parent"
    game = real_parent / "game"
    game.mkdir(parents=True)
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"outside must remain unread")
    requested_root = game
    special: Path | None = None

    if unsafe_kind == "matching_symlink":
        special = game / "preloader_link.log"
        special.symlink_to(outside)
    elif unsafe_kind == "matching_fifo":
        special = game / "preloader_pipe.log"
        os.mkfifo(special, 0o600)
    elif unsafe_kind == "canonical_symlink":
        special = game / "BepInEx/LogOutput.log"
        special.parent.mkdir()
        special.symlink_to(outside)
    elif unsafe_kind == "canonical_fifo":
        special = game / "BepInEx/LogOutput.log"
        special.parent.mkdir()
        os.mkfifo(special, 0o600)
    elif unsafe_kind == "fallback_symlink":
        special = game / "BepInEx/LogOutput.log.1"
        special.parent.mkdir()
        special.symlink_to(outside)
    elif unsafe_kind == "fallback_fifo":
        special = game / "BepInEx/LogOutput.log.1"
        special.parent.mkdir()
        os.mkfifo(special, 0o600)
    elif unsafe_kind == "root_symlink":
        requested_root = tmp_path / "game-link"
        requested_root.symlink_to(game, target_is_directory=True)
    else:
        parent_link = tmp_path / "parent-link"
        parent_link.symlink_to(real_parent, target_is_directory=True)
        requested_root = parent_link / "game"

    hash_calls: list[Path] = []

    def forbidden_hash(path: Path):
        hash_calls.append(path)
        raise AssertionError("unsafe or special path must not be opened")

    monkeypatch.setattr(
        oracle_boot, "_sha256_file", forbidden_hash, raising=False
    )
    started = time.monotonic()
    with pytest.raises(Exception):
        fingerprint_preloader_logs(requested_root)
    elapsed = time.monotonic() - started

    assert elapsed < 0.5
    assert hash_calls == []
    assert outside.read_bytes() == b"outside must remain unread"
    if special is not None:
        assert os.path.lexists(special)


def test_fingerprint_logs_validate_baseline_accepts_crafted_canonical_log_fingerprint(
    tmp_path: Path,
):
    game = tmp_path / "game"
    (game / "BepInEx").mkdir(parents=True)
    canonical = game / "BepInEx/LogOutput.log"
    fingerprint = oracle_boot.LogFingerprint(
        path=canonical,
        file_type="regular",
        inode=1,
        size=2,
        mtime_ns=3,
        sha256="a" * 64,
    )

    assert oracle_boot._validate_baseline((fingerprint,), game) == {
        canonical: fingerprint
    }


def test_collect_preserves_relative_paths_and_rejects_adversarial_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    (game / "old").mkdir(parents=True)
    changed = game / "old/preloader_changed.log"
    changed.write_bytes(b"before")
    unchanged = game / "preloader_unchanged.log"
    unchanged.write_bytes(b"unchanged")
    before = fingerprint_preloader_logs(game)
    changed.write_bytes(b"after")

    new_left = game / "left/preloader_duplicate.log"
    new_right = game / "right/preloader_duplicate.log"
    new_left.parent.mkdir()
    new_right.parent.mkdir()
    new_left.write_bytes(b"left")
    new_right.write_bytes(b"right")
    unrelated = game / "unrelated.keep"
    unrelated.write_bytes(b"survive")
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"outside")
    symlink_log = game / "preloader_escape.log"
    symlink_log.symlink_to(outside)
    fifo = game / "preloader_never_open.log"
    os.mkfifo(fifo, 0o600)

    original_hash = oracle_boot._sha256_file
    hash_calls: list[Path] = []

    def guarded_hash(path: Path):
        assert path.resolve() != fifo.resolve()
        hash_calls.append(path)
        return original_hash(path)

    monkeypatch.setattr(
        oracle_boot, "_sha256_file", guarded_hash, raising=False
    )
    monkeypatch.setattr(
        oracle_boot,
        "_utc_now",
        lambda: datetime(
            2026, 7, 28, 12, 34, 56, 123456, tzinfo=timezone.utc
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_random_token",
        lambda: "0123456789abcdef0123456789abcdef",
        raising=False,
    )

    started = time.monotonic()
    result = collect_boot_evidence(
        before, game, tmp_path / "evidence"
    )
    elapsed = time.monotonic() - started

    assert elapsed < 0.5
    assert result.evidence_dir == (
        tmp_path
        / "evidence"
        / "20260728T123456.123456Z-0123456789abcdef0123456789abcdef"
    ).resolve()
    expected_moved = (
        result.evidence_dir / new_left.relative_to(game),
        result.evidence_dir / new_right.relative_to(game),
    )
    assert result.moved_logs == expected_moved
    assert [path.read_bytes() for path in result.moved_logs] == [
        b"left",
        b"right",
    ]
    assert not new_left.exists()
    assert not new_right.exists()
    expected_copy = result.evidence_dir / changed.relative_to(game)
    assert result.copied_logs == (expected_copy,)
    assert expected_copy.read_bytes() == b"after"
    assert changed.read_bytes() == b"after"
    assert unchanged.read_bytes() == b"unchanged"
    assert unrelated.read_bytes() == b"survive"
    assert symlink_log.is_symlink()
    assert outside.read_bytes() == b"outside"
    assert stat.S_ISFIFO(fifo.stat(follow_symlinks=False).st_mode)
    assert not any(path.resolve() == fifo.resolve() for path in hash_calls)
    assert any("preloader_escape.log" in issue for issue in result.issues)
    assert any("preloader_never_open.log" in issue for issue in result.issues)


def test_collect_rejects_out_of_root_baseline_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    new_log = game / "preloader_new.log"
    new_log.write_bytes(b"new")
    outside = tmp_path / "preloader_outside.log"
    outside.write_bytes(b"outside")
    observed = outside.stat(follow_symlinks=False)
    crafted = oracle_boot.LogFingerprint(
        path=outside.resolve(),
        file_type="regular",
        inode=observed.st_ino,
        size=observed.st_size,
        mtime_ns=observed.st_mtime_ns,
        sha256=_sha256(outside),
    )
    evidence_root = tmp_path / "evidence"
    game_before = _test_tree_snapshot(game)
    mutation_calls: list[tuple[str, tuple[object, ...]]] = []

    def forbidden_mkdir(*args, **_kwargs):
        mutation_calls.append(("mkdir", args))
        raise AssertionError("baseline must be validated before allocation")

    def forbidden_rename(*args, **_kwargs):
        mutation_calls.append(("rename", args))
        raise AssertionError("baseline must be validated before movement")

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            mkdir=forbidden_mkdir,
            rename=forbidden_rename,
        ),
        raising=False,
    )

    with pytest.raises(Exception):
        collect_boot_evidence((crafted,), game, evidence_root)

    assert mutation_calls == []
    assert _test_tree_snapshot(game) == game_before
    assert new_log.read_bytes() == b"new"
    assert outside.read_bytes() == b"outside"
    assert not evidence_root.exists()


def test_collect_retained_evidence_keeps_exact_files_open_until_close(
    tmp_path: Path,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "nested/preloader_probe.log"
    source.parent.mkdir()
    source.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
    source_payload = source.read_bytes()
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
        item = retained.files[0]
        assert item.relative_path == Path("nested/preloader_probe.log")
        observed = os.fstat(item.descriptor)
        preserved = retained.public.evidence_dir / item.relative_path
        named = preserved.stat(follow_symlinks=False)
        assert item.identity == oracle_boot._stat_identity(observed)
        assert oracle_boot._stat_identity(named) == item.identity
        assert (
            fcntl.fcntl(item.descriptor, fcntl.F_GETFL)
            & os.O_ACCMODE
        ) == os.O_RDWR
        assert item.fingerprint == oracle_boot.LogFingerprint(
            path=preserved,
            file_type="regular",
            inode=observed.st_ino,
            size=len(source_payload),
            mtime_ns=observed.st_mtime_ns,
            sha256=hashlib.sha256(source_payload).hexdigest(),
        )
        nested = preserved.parent.stat(follow_symlinks=False)
        assert retained.directories == (
            oracle_boot._EvidenceDirectoryIdentity(
                relative_path=Path("."),
                device=retained.directory_handle.device,
                inode=retained.directory_handle.inode,
            ),
            oracle_boot._EvidenceDirectoryIdentity(
                relative_path=Path("nested"),
                device=nested.st_dev,
                inode=nested.st_ino,
            ),
        )
        assert retained.decision == oracle_boot._EvidenceDecision(
            markers=REQUIRED_MARKERS,
            errors=(),
            fingerprints=(item.fingerprint,),
        )
        assert all(os.fstat(descriptor) for descriptor in descriptors)
    finally:
        retained.close()
    for descriptor in descriptors:
        with pytest.raises(OSError) as raised:
            os.fstat(descriptor)
        assert raised.value.errno == errno.EBADF


def test_read_retained_evidence_rejects_same_metadata_byte_substitution(
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
        item = retained.files[0]
        preserved = (
            retained.public.evidence_dir / item.relative_path
        )
        before = preserved.stat(follow_symlinks=False)
        original = preserved.read_bytes()
        replacement = original.replace(b"\n", b" ", 1)
        assert replacement != original
        assert len(replacement) == len(original)

        preserved.write_bytes(replacement)
        os.utime(
            preserved,
            ns=(before.st_atime_ns, before.st_mtime_ns),
            follow_symlinks=False,
        )
        after = preserved.stat(follow_symlinks=False)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
        )
        assert before_identity == item.identity
        assert after_identity == item.identity
        assert preserved.read_bytes() == replacement

        with pytest.raises(
            oracle_boot.BootProbeError,
            match="fingerprint changed",
        ):
            oracle_boot._read_retained_evidence_file(retained, item)
    finally:
        retained.close()


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


def test_verify_retained_evidence_rejects_replaced_public_root(
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
    public_root = retained.public.evidence_dir
    displaced = public_root.with_name(f"{public_root.name}-displaced")
    public_root.rename(displaced)
    public_root.mkdir(mode=0o700)
    attacker = public_root / "attacker.keep"
    attacker.write_bytes(b"replacement")

    try:
        with pytest.raises(
            oracle_boot.BootProbeError,
            match="retained evidence directory changed",
        ):
            oracle_boot._verify_and_sync_retained_evidence(retained)
        assert attacker.read_bytes() == b"replacement"
        assert (
            displaced / "nested/preloader_probe.log"
        ).read_text(encoding="utf-8") == "\n".join(REQUIRED_MARKERS)
    finally:
        retained.close()


def test_verify_retained_evidence_fsyncs_exact_tree_deepest_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    log = game / "nested/deep/preloader_probe.log"
    log.parent.mkdir(parents=True)
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

    assert events == [
        ("file", None),
        ("directory", Path("nested/deep")),
        ("directory", Path("nested")),
        ("directory", Path(".")),
    ]


def test_verify_retained_evidence_rejects_transient_pre_fsync_decision(
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
    item = retained.files[0]
    original_capture = oracle_boot._capture_retained_evidence_decision
    original_fsync = os.fsync
    file_fsync_started = False

    def capture_transient_pre_fsync_disagreement(candidate):
        decision = original_capture(candidate)
        if not file_fsync_started:
            return oracle_boot._EvidenceDecision(
                markers=decision.markers,
                errors=decision.errors + ("transient pre-fsync error",),
                fingerprints=decision.fingerprints,
            )
        return decision

    def track_file_fsync(descriptor: int) -> None:
        nonlocal file_fsync_started
        if descriptor == item.descriptor:
            file_fsync_started = True
        original_fsync(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "_capture_retained_evidence_decision",
        capture_transient_pre_fsync_disagreement,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=track_file_fsync),
        raising=False,
    )
    try:
        with pytest.raises(
            oracle_boot.BootProbeError,
            match="changed before fsync",
        ):
            oracle_boot._verify_and_sync_retained_evidence(retained)
    finally:
        retained.close()


def test_verify_retained_evidence_post_fsync_recapture_exposes_mutation(
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
    item = retained.files[0]
    preserved = retained.public.evidence_dir / item.relative_path
    original = preserved.read_bytes()
    replacement = original.replace(b"\n", b" ", 1)
    assert replacement != original
    assert len(replacement) == len(original)
    original_fsync = os.fsync
    mutation_injected = False

    def mutate_during_file_fsync(descriptor: int) -> None:
        nonlocal mutation_injected
        original_fsync(descriptor)
        if descriptor == item.descriptor and not mutation_injected:
            before = preserved.stat(follow_symlinks=False)
            preserved.write_bytes(replacement)
            os.utime(
                preserved,
                ns=(before.st_atime_ns, before.st_mtime_ns),
                follow_symlinks=False,
            )
            mutation_injected = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=mutate_during_file_fsync),
        raising=False,
    )
    try:
        with pytest.raises(
            oracle_boot.BootProbeError,
            match="fingerprint changed",
        ):
            oracle_boot._verify_and_sync_retained_evidence(retained)
        assert mutation_injected
    finally:
        retained.close()


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


def test_collect_retained_evidence_keeps_exact_copied_file_writable(
    tmp_path: Path,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "nested/preloader_changed.log"
    source.parent.mkdir()
    source.write_bytes(b"before")
    before = oracle_boot._fingerprint_regular_preloader_logs(game)
    copied_payload = b"after allocation boundary"
    source.write_bytes(copied_payload)
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)

    retained = oracle_boot._collect_boot_evidence_retained(
        before,
        game,
        tmp_path / "evidence",
        expected_inventory=expected,
    )
    try:
        assert retained.public.moved_logs == ()
        assert len(retained.public.copied_logs) == 1
        assert len(retained.files) == 1
        item = retained.files[0]
        preserved = retained.public.evidence_dir / item.relative_path
        observed = os.fstat(item.descriptor)
        assert preserved == retained.public.copied_logs[0]
        assert source.read_bytes() == copied_payload
        assert preserved.read_bytes() == copied_payload
        assert item.identity == oracle_boot._stat_identity(observed)
        assert item.identity == oracle_boot._stat_identity(
            preserved.stat(follow_symlinks=False)
        )
        assert (
            fcntl.fcntl(item.descriptor, fcntl.F_GETFL)
            & os.O_ACCMODE
        ) == os.O_RDWR
        assert item.fingerprint == oracle_boot.LogFingerprint(
            path=preserved,
            file_type="regular",
            inode=observed.st_ino,
            size=len(copied_payload),
            mtime_ns=observed.st_mtime_ns,
            sha256=hashlib.sha256(copied_payload).hexdigest(),
        )
    finally:
        retained.close()


def test_collect_retained_inventory_check_precedes_every_transfer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    (game / "preloader_expected.log").write_bytes(b"expected")
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    original_scan = oracle_boot._scan_preloader_logs
    original_allocate = oracle_boot._allocate_evidence_directory
    events: list[str] = []
    allocated_descriptor = -1

    def tracked_scan(*args, **kwargs):
        events.append("scan")
        return original_scan(*args, **kwargs)

    def allocate_then_add(*args, **kwargs):
        nonlocal allocated_descriptor
        events.append("allocate")
        evidence_dir, handle = original_allocate(*args, **kwargs)
        allocated_descriptor = handle.fd
        (game / "preloader_late.log").write_bytes(b"late")
        return evidence_dir, handle

    def forbidden_transfer(*_args, **_kwargs):
        events.append("transfer")
        raise AssertionError("inventory validation followed a transfer")

    monkeypatch.setattr(
        oracle_boot,
        "_scan_preloader_logs",
        tracked_scan,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_allocate_evidence_directory",
        allocate_then_add,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_move_regular_exclusive",
        forbidden_transfer,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_copy_regular_exclusive",
        forbidden_transfer,
    )

    with pytest.raises(oracle_boot.BootProbeError, match="inventory added"):
        oracle_boot._collect_boot_evidence_retained(
            (),
            game,
            tmp_path / "evidence",
            expected_inventory=expected,
        )

    assert events == ["scan", "allocate", "scan"]
    assert allocated_descriptor >= 0
    with pytest.raises(OSError) as raised:
        os.fstat(allocated_descriptor)
    assert raised.value.errno == errno.EBADF


def test_collect_retained_closes_file_returned_before_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    (game / "preloader_probe.log").write_text(
        "\n".join(REQUIRED_MARKERS),
        encoding="utf-8",
    )
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    original_move = oracle_boot._move_regular_exclusive
    returned_descriptor = -1

    class InjectedRegistrationError(KeyboardInterrupt):
        pass

    class FailingRegistrationRecord:
        def __init__(self, item):
            self.item = item

        @property
        def relative_path(self):
            return self.item.relative_path

        @relative_path.setter
        def relative_path(self, _value):
            raise InjectedRegistrationError("registration interrupted")

        def close(self):
            self.item.close()

    def interrupt_registration(*args, **kwargs):
        nonlocal returned_descriptor
        item = original_move(*args, **kwargs)
        returned_descriptor = item.descriptor
        return FailingRegistrationRecord(item)

    monkeypatch.setattr(
        oracle_boot,
        "_move_regular_exclusive",
        interrupt_registration,
    )

    with pytest.raises(
        InjectedRegistrationError,
        match="registration interrupted",
    ):
        oracle_boot._collect_boot_evidence_retained(
            (),
            game,
            tmp_path / "evidence",
            expected_inventory=expected,
        )

    assert returned_descriptor >= 0
    with pytest.raises(OSError) as raised:
        os.fstat(returned_descriptor)
    assert raised.value.errno == errno.EBADF


@pytest.mark.parametrize(
    "boundary",
    ["initial_scan", "allocation", "final_scan"],
)
def test_collect_retained_acquisition_boundary_interrupt_closes_ownership(
    boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    acquired_descriptors: list[int] = []
    evidence_descriptor: list[int] = []
    armed = False
    scan_calls = 0
    original_scan = oracle_boot._scan_preloader_logs
    original_allocate = oracle_boot._allocate_evidence_directory

    def capture_scan(*args, **kwargs):
        nonlocal armed, scan_calls
        scan = original_scan(*args, **kwargs)
        scan_calls += 1
        selected = (
            boundary == "initial_scan" and scan_calls == 1
        ) or (
            boundary == "final_scan" and scan_calls == 2
        )
        if selected:
            acquired_descriptors.extend(
                handle.fd for handle in scan.handles
            )
            armed = True
        return scan

    def capture_allocation(*args, **kwargs):
        nonlocal armed
        evidence_dir, handle = original_allocate(*args, **kwargs)
        evidence_descriptor.append(handle.fd)
        if boundary == "allocation":
            acquired_descriptors.append(handle.fd)
            armed = True
        return evidence_dir, handle

    monkeypatch.setattr(
        oracle_boot,
        "_scan_preloader_logs",
        capture_scan,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_allocate_evidence_directory",
        capture_allocation,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(boundary)
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._collect_boot_evidence_retained,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._collect_boot_evidence_retained(
                (),
                game,
                tmp_path / "evidence",
                expected_inventory=(),
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)
    if boundary == "final_scan":
        assert evidence_descriptor
        _assert_acquired_descriptors_closed(evidence_descriptor)


@pytest.mark.parametrize("transfer_kind", ["copy", "move"])
def test_evidence_transfer_acquisition_boundary_interrupt_closes_source(
    transfer_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "preloader_source.log"
    source.write_bytes(b"payload")
    scan = oracle_boot._scan_preloader_logs(game)
    entry = scan.entries[0]
    expected = oracle_boot._fingerprint_scanned(entry)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    destination_parent = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    target = (
        oracle_boot._copy_regular_exclusive
        if transfer_kind == "copy"
        else oracle_boot._move_regular_exclusive
    )
    acquired_descriptors: list[int] = []
    armed = False
    original_open = os.open

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal armed
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == entry.name and dir_fd == entry.parent.fd:
            acquired_descriptors.append(descriptor)
            armed = True
        return descriptor

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, open=capture_open),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(transfer_kind)
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            target,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            target(
                entry,
                destination_parent,
                f"{transfer_kind}.log",
                evidence / f"{transfer_kind}.log",
                expected,
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)
    destination_parent.close()
    scan.close()


def test_duplicate_directory_handle_acquisition_boundary_interrupt_closes_dup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    directory = tmp_path / "directory"
    directory.mkdir()
    original_handle = oracle_boot._open_absolute_directory(
        directory,
        "directory",
    )
    acquired_descriptors: list[int] = []
    armed = False
    original_dup = os.dup

    def capture_dup(descriptor: int) -> int:
        nonlocal armed
        duplicate = original_dup(descriptor)
        acquired_descriptors.append(duplicate)
        armed = True
        return duplicate

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, dup=capture_dup),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("duplicate")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._duplicate_directory_handle,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._duplicate_directory_handle(original_handle)
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)
    assert os.fstat(original_handle.fd)
    original_handle.close()


@pytest.mark.parametrize(
    "handle_source",
    ["path_open", "retained_duplicate"],
)
def test_stage_probe_json_acquisition_boundary_interrupt_closes_directory(
    handle_source: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    retained_handle = None
    acquired_descriptors: list[int] = []
    armed = False
    if handle_source == "path_open":
        original_acquire = oracle_boot._open_absolute_directory
        acquire_name = "_open_absolute_directory"
    else:
        retained_handle = oracle_boot._open_absolute_directory(
            evidence,
            "evidence directory",
        )
        original_acquire = oracle_boot._duplicate_directory_handle
        acquire_name = "_duplicate_directory_handle"

    def capture_acquisition(*args, **kwargs):
        nonlocal armed
        handle = original_acquire(*args, **kwargs)
        acquired_descriptors.append(handle.fd)
        armed = True
        return handle

    monkeypatch.setattr(
        oracle_boot,
        acquire_name,
        capture_acquisition,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(handle_source)
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._stage_probe_json,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._stage_probe_json(
                evidence,
                {"schema_version": 1},
                _directory_handle=retained_handle,
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)
    if retained_handle is not None:
        assert os.fstat(retained_handle.fd)
        retained_handle.close()


def test_opened_directory_acquisition_boundary_interrupt_closes_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    directory = tmp_path / "directory"
    directory.mkdir()
    descriptor = os.open(
        directory,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    acquired_descriptors = [descriptor]
    armed = False
    original_fstat = os.fstat

    def capture_fstat(candidate: int):
        nonlocal armed
        observed = original_fstat(candidate)
        if candidate == descriptor:
            armed = True
        return observed

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fstat=capture_fstat),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("opened-directory")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._opened_directory,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._opened_directory(descriptor, directory)
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_open_absolute_directory_acquisition_boundary_interrupt_closes_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    directory = tmp_path / "parent" / "leaf"
    directory.mkdir(parents=True)
    acquired_descriptors: list[int] = []
    armed = False
    original_open = os.open

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal armed
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == directory.name:
            acquired_descriptors.append(descriptor)
            armed = True
        return descriptor

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, open=capture_open),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("absolute-child")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._open_absolute_directory,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._open_absolute_directory(directory, "directory")
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_open_child_directory_acquisition_boundary_interrupt_closes_child(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    parent_path = tmp_path / "parent"
    parent_path.mkdir()
    child_path = parent_path / "child"
    child_path.mkdir()
    parent = oracle_boot._open_absolute_directory(
        parent_path,
        "parent",
    )
    observed = child_path.stat(follow_symlinks=False)
    acquired_descriptors: list[int] = []
    armed = False
    original_opened = oracle_boot._opened_directory

    def capture_opened(*args, **kwargs):
        nonlocal armed
        child = original_opened(*args, **kwargs)
        acquired_descriptors.append(child.fd)
        armed = True
        return child

    monkeypatch.setattr(
        oracle_boot,
        "_opened_directory",
        capture_opened,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("open-child")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._open_child_directory,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._open_child_directory(
                parent,
                child_path.name,
                child_path,
                observed,
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert os.fstat(parent.fd)
    parent.close()
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)


@pytest.mark.parametrize("scan_boundary", ["root", "child"])
def test_scan_preloader_logs_acquisition_boundary_interrupt_closes_handles(
    scan_boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    if scan_boundary == "child":
        (game / "nested").mkdir()
    acquired_descriptors: list[int] = []
    root_descriptors: list[int] = []
    armed = False
    original_root_open = oracle_boot._open_absolute_directory
    original_child_open = oracle_boot._open_child_directory

    def capture_root(*args, **kwargs):
        nonlocal armed
        handle = original_root_open(*args, **kwargs)
        root_descriptors.append(handle.fd)
        if scan_boundary == "root":
            acquired_descriptors.append(handle.fd)
            armed = True
        return handle

    def capture_child(*args, **kwargs):
        nonlocal armed
        handle = original_child_open(*args, **kwargs)
        acquired_descriptors.append(handle.fd)
        armed = True
        return handle

    monkeypatch.setattr(
        oracle_boot,
        "_open_absolute_directory",
        capture_root,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_open_child_directory",
        capture_child,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        f"scan-{scan_boundary}"
    )
    if scan_boundary == "root":
        trace = _next_line_interrupt_trace(
            oracle_boot._scan_preloader_logs,
            lambda: armed,
            interrupt,
        )
    else:
        scan_filename = (
            oracle_boot._scan_preloader_logs.__code__.co_filename
        )

        def trace(frame, event, _arg):
            if (
                event == "line"
                and frame.f_code.co_name == "visit"
                and frame.f_code.co_filename == scan_filename
                and armed
            ):
                sys.settrace(None)
                raise interrupt
            return trace

    previous_trace = sys.gettrace()
    sys.settrace(trace)
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._scan_preloader_logs(game)
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(
        [*acquired_descriptors, *root_descriptors]
    )


def test_allocate_evidence_acquisition_boundary_interrupt_closes_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    acquired_descriptors: list[int] = []
    armed = False
    original_open_child = oracle_boot._open_child_directory

    def capture_child(*args, **kwargs):
        nonlocal armed
        handle = original_open_child(*args, **kwargs)
        acquired_descriptors.append(handle.fd)
        armed = True
        return handle

    monkeypatch.setattr(
        oracle_boot,
        "_open_child_directory",
        capture_child,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("allocation-result")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._allocate_evidence_directory,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._allocate_evidence_directory(evidence, True)
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)


@pytest.mark.parametrize("parent_boundary", ["duplicate", "child"])
def test_make_evidence_parents_acquisition_boundary_interrupt_closes_handles(
    parent_boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    original_handle = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    acquired_descriptors: list[int] = []
    armed = False
    original_dup = os.dup
    original_open_child = oracle_boot._open_child_directory

    def capture_dup(descriptor: int) -> int:
        nonlocal armed
        duplicate = original_dup(descriptor)
        acquired_descriptors.append(duplicate)
        if parent_boundary == "duplicate":
            armed = True
        return duplicate

    def capture_child(*args, **kwargs):
        nonlocal armed
        handle = original_open_child(*args, **kwargs)
        acquired_descriptors.append(handle.fd)
        armed = True
        return handle

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, dup=capture_dup),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_open_child_directory",
        capture_child,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        f"evidence-parent-{parent_boundary}"
    )
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._make_evidence_parents,
            lambda: armed,
            interrupt,
        )
    )
    relative_parent = (
        Path(".") if parent_boundary == "duplicate" else Path("nested")
    )
    known_directories = {
        evidence: (
            original_handle.device,
            original_handle.inode,
        )
    }
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._make_evidence_parents(
                original_handle,
                relative_parent,
                known_directories,
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert os.fstat(original_handle.fd)
    original_handle.close()
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)


@pytest.mark.parametrize("transfer_kind", ["copy", "move"])
def test_collect_parent_acquisition_boundary_interrupt_closes_parent(
    transfer_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "nested" / "preloader_source.log"
    source.parent.mkdir()
    if transfer_kind == "copy":
        source.write_bytes(b"before")
        before = oracle_boot._fingerprint_regular_preloader_logs(game)
        source.write_bytes(b"after")
    else:
        before = ()
        source.write_bytes(b"new")
    expected = oracle_boot._fingerprint_regular_preloader_logs(game)
    acquired_descriptors: list[int] = []
    armed = False
    original_make_parents = oracle_boot._make_evidence_parents

    def capture_parent(*args, **kwargs):
        nonlocal armed
        handle = original_make_parents(*args, **kwargs)
        acquired_descriptors.append(handle.fd)
        armed = True
        return handle

    monkeypatch.setattr(
        oracle_boot,
        "_make_evidence_parents",
        capture_parent,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        f"collector-parent-{transfer_kind}"
    )
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._collect_boot_evidence_retained,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._collect_boot_evidence_retained(
                before,
                game,
                tmp_path / "evidence",
                expected_inventory=expected,
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert acquired_descriptors
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_copy_close_transition_acquisition_boundary_interrupt_closes_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "preloader_source.log"
    source.write_bytes(b"payload")
    scan = oracle_boot._scan_preloader_logs(game)
    entry = scan.entries[0]
    expected = oracle_boot._fingerprint_scanned(entry)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    destination_parent = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    acquired_descriptors: list[int] = []
    source_descriptor = -1
    armed = False
    original_open = os.open
    original_close = os.close

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal source_descriptor
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == entry.name and dir_fd == entry.parent.fd:
            source_descriptor = descriptor
            acquired_descriptors.append(descriptor)
        elif path == "copied.log" and flags & os.O_CREAT:
            acquired_descriptors.append(descriptor)
        return descriptor

    def arm_after_source_close(descriptor: int) -> None:
        nonlocal armed
        original_close(descriptor)
        if descriptor == source_descriptor:
            armed = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_open,
            close=arm_after_source_close,
        ),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        "copy-close-transition"
    )
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._copy_regular_exclusive,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._copy_regular_exclusive(
                entry,
                destination_parent,
                "copied.log",
                evidence / "copied.log",
                expected,
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert len(acquired_descriptors) == 2
    destination_parent.close()
    scan.close()
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_stage_file_handoff_acquisition_boundary_interrupt_closes_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    acquired_descriptors: list[int] = []
    original_open = os.open

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if (
            isinstance(path, str)
            and path.startswith(".probe-json-")
            and path.endswith(".pending")
            and flags & os.O_CREAT
        ):
            acquired_descriptors.append(descriptor)
        return descriptor

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, open=capture_open),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("stage-file-handoff")
    target_code = oracle_boot._stage_probe_json.__code__

    def trace(frame, event, _arg):
        descriptor_to_close = frame.f_locals.get(
            "descriptor_to_close",
            -1,
        )
        if (
            event == "line"
            and frame.f_code is target_code
            and frame.f_locals.get("descriptor") == -1
            and descriptor_to_close in acquired_descriptors
        ):
            sys.settrace(None)
            raise interrupt
        return trace

    previous_trace = sys.gettrace()
    sys.settrace(trace)
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._stage_probe_json(
                evidence,
                {"schema_version": 1},
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert len(acquired_descriptors) == 1
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_copy_post_successful_close_interrupt_preserves_reused_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "preloader_source.log"
    source.write_bytes(b"payload")
    scan = oracle_boot._scan_preloader_logs(game)
    entry = scan.entries[0]
    expected = oracle_boot._fingerprint_scanned(entry)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    destination_parent = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    source_descriptor = -1
    replacement_descriptor = -1
    close_calls: list[int] = []
    armed = False
    original_open = os.open
    original_close = os.close

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal source_descriptor
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == entry.name and dir_fd == entry.parent.fd:
            source_descriptor = descriptor
        return descriptor

    def close_then_reuse(descriptor: int) -> None:
        nonlocal armed, replacement_descriptor
        if source_descriptor >= 0:
            close_calls.append(descriptor)
        original_close(descriptor)
        if (
            descriptor == source_descriptor
            and replacement_descriptor < 0
        ):
            replacement_descriptor = original_open(
                source,
                os.O_RDONLY | os.O_NOFOLLOW,
            )
            assert replacement_descriptor == source_descriptor
            armed = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_open,
            close=close_then_reuse,
        ),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        "copy-after-successful-close"
    )
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._copy_regular_exclusive,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._copy_regular_exclusive(
                entry,
                destination_parent,
                "copied.log",
                evidence / "copied.log",
                expected,
            )
    finally:
        sys.settrace(previous_trace)

    try:
        assert raised.value is interrupt
        assert replacement_descriptor == source_descriptor
        assert os.fstat(replacement_descriptor)
        assert os.lseek(replacement_descriptor, 0, os.SEEK_CUR) == 0
        assert close_calls.count(source_descriptor) == 1
        assert not getattr(raised.value, "__notes__", ())
    finally:
        if replacement_descriptor >= 0:
            try:
                original_close(replacement_descriptor)
            except OSError as exc:
                assert exc.errno == errno.EBADF
        destination_parent.close()
        scan.close()


def test_stage_post_successful_close_interrupt_preserves_reused_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    writer_descriptor = -1
    writer_name = ""
    writer_dir_fd = -1
    replacement_descriptor = -1
    close_calls: list[int] = []
    armed = False
    original_open = os.open
    original_close = os.close

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal writer_descriptor, writer_dir_fd, writer_name
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if (
            isinstance(path, str)
            and path.startswith(".probe-json-")
            and path.endswith(".pending")
            and flags & os.O_CREAT
        ):
            writer_descriptor = descriptor
            writer_name = path
            writer_dir_fd = dir_fd if dir_fd is not None else -1
        return descriptor

    def close_then_reuse(descriptor: int) -> None:
        nonlocal armed, replacement_descriptor
        if writer_descriptor >= 0:
            close_calls.append(descriptor)
        original_close(descriptor)
        if (
            descriptor == writer_descriptor
            and replacement_descriptor < 0
        ):
            replacement_descriptor = original_open(
                writer_name,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=writer_dir_fd,
            )
            assert replacement_descriptor == writer_descriptor
            armed = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_open,
            close=close_then_reuse,
        ),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        "stage-after-successful-close"
    )
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._stage_probe_json,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._stage_probe_json(
                evidence,
                {"schema_version": 1},
            )
    finally:
        sys.settrace(previous_trace)

    try:
        assert raised.value is interrupt
        assert replacement_descriptor == writer_descriptor
        assert os.fstat(replacement_descriptor)
        assert os.lseek(replacement_descriptor, 0, os.SEEK_CUR) == 0
        assert close_calls.count(writer_descriptor) == 1
        assert not getattr(raised.value, "__notes__", ())
    finally:
        if replacement_descriptor >= 0:
            try:
                original_close(replacement_descriptor)
            except OSError as exc:
                assert exc.errno == errno.EBADF


def test_write_probe_json_acquisition_boundary_interrupt_closes_staged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    acquired_descriptors: list[int] = []
    armed = False
    original_stage = oracle_boot._stage_probe_json

    def capture_stage(*args, **kwargs):
        nonlocal armed
        staged = original_stage(*args, **kwargs)
        acquired_descriptors.extend(
            (
                staged.directory_handle.fd,
                staged.verifier_fd,
            )
        )
        armed = True
        return staged

    monkeypatch.setattr(
        oracle_boot,
        "_stage_probe_json",
        capture_stage,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("write-staged")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._write_probe_json,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._write_probe_json(
                evidence,
                {"schema_version": 1},
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert len(acquired_descriptors) == 2
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_write_committed_acquisition_boundary_interrupt_closes_staged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1}
    acquired_descriptors: list[int] = []
    armed = False
    original_commit = oracle_boot._commit_staged_probe_json

    def capture_commit(staged):
        nonlocal armed
        original_commit(staged)
        assert staged.committed
        acquired_descriptors.extend(
            (
                staged.directory_handle.fd,
                staged.verifier_fd,
            )
        )
        armed = True

    monkeypatch.setattr(
        oracle_boot,
        "_commit_staged_probe_json",
        capture_commit,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("write-committed")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot._write_probe_json,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._write_probe_json(evidence, payload)
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert (evidence / "probe.json").read_bytes() == (
        oracle_boot._encode_probe_json(payload)
    )
    assert len(acquired_descriptors) == 2
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_public_collect_acquisition_boundary_interrupt_closes_retained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "preloader_source.log"
    source.write_bytes(b"payload")
    acquired_descriptors: list[int] = []
    armed = False
    original_collect = oracle_boot._collect_boot_evidence_retained

    def capture_collect(*args, **kwargs):
        nonlocal armed
        retained = original_collect(*args, **kwargs)
        acquired_descriptors.extend(
            (
                retained.directory_handle.fd,
                *(item.descriptor for item in retained.files),
            )
        )
        armed = True
        return retained

    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        capture_collect,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt("public-collector")
    previous_trace = sys.gettrace()
    sys.settrace(
        _next_line_interrupt_trace(
            oracle_boot.collect_boot_evidence,
            lambda: armed,
            interrupt,
        )
    )
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot.collect_boot_evidence(
                (),
                game,
                tmp_path / "evidence",
            )
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert len(acquired_descriptors) == 2
    _assert_acquired_descriptors_closed(acquired_descriptors)


def test_open_absolute_directory_transfer_interrupt_deduplicates_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    directory = tmp_path / "parent" / "leaf"
    directory.mkdir(parents=True)
    opened_descriptors: list[int] = []
    close_calls: list[int] = []
    armed = False
    injected = False
    aliased_descriptor = -1
    original_open = os.open
    original_close = os.close

    def capture_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal armed
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        opened_descriptors.append(descriptor)
        if path == directory.name:
            armed = True
        return descriptor

    def capture_close(descriptor: int) -> None:
        if injected:
            close_calls.append(descriptor)
        original_close(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_open,
            close=capture_close,
        ),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(
        "absolute-transfer-alias"
    )
    target_code = oracle_boot._open_absolute_directory.__code__

    def trace(frame, event, _arg):
        nonlocal aliased_descriptor, injected
        if event == "line" and frame.f_code is target_code and armed:
            owned = [
                frame.f_locals.get(name, -1)
                for name in (
                    "descriptor",
                    "following_descriptor",
                    "previous_descriptor",
                    "opened_descriptor",
                )
            ]
            aliased = next(
                (
                    descriptor
                    for descriptor in owned
                    if descriptor >= 0
                    and owned.count(descriptor) > 1
                ),
                -1,
            )
            if aliased >= 0:
                aliased_descriptor = aliased
                injected = True
                sys.settrace(None)
                raise interrupt
        return trace

    previous_trace = sys.gettrace()
    sys.settrace(trace)
    try:
        with pytest.raises(
            _InjectedAcquisitionBoundaryInterrupt,
        ) as raised:
            oracle_boot._open_absolute_directory(directory, "directory")
    finally:
        sys.settrace(previous_trace)

    assert raised.value is interrupt
    assert aliased_descriptor >= 0
    _assert_acquired_descriptors_closed(opened_descriptors)
    assert close_calls.count(aliased_descriptor) == 1
    assert not getattr(interrupt, "__notes__", ())


def test_allocate_evidence_exhausted_collisions_raise_and_close_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    timestamp = "20260729T120000.000000Z"
    token = "f" * 32
    (evidence / f"{timestamp}-{token}").mkdir()
    root_descriptors: list[int] = []
    original_open = oracle_boot._open_absolute_directory

    def capture_root(*args, **kwargs):
        handle = original_open(*args, **kwargs)
        root_descriptors.append(handle.fd)
        return handle

    monkeypatch.setattr(
        oracle_boot,
        "_utc_now",
        lambda: datetime(
            2026,
            7,
            29,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )
    monkeypatch.setattr(oracle_boot, "_random_token", lambda: token)
    monkeypatch.setattr(
        oracle_boot,
        "_open_absolute_directory",
        capture_root,
    )

    with pytest.raises(
        oracle_boot.BootProbeError,
        match="after 128 attempts",
    ):
        oracle_boot._allocate_evidence_directory(evidence, True)

    assert len(root_descriptors) == 1
    _assert_acquired_descriptors_closed(root_descriptors)


@pytest.mark.parametrize("transfer_kind", ["copy", "move"])
def test_evidence_transfer_close_failure_preserves_primary_and_closes_locals(
    transfer_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "preloader_source.log"
    source.write_bytes(b"payload")
    scan = oracle_boot._scan_preloader_logs(game)
    entry = scan.entries[0]
    expected = oracle_boot._fingerprint_scanned(entry)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    destination_parent = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    destination_name = f"{transfer_kind}.log"
    original_open = os.open
    original_close = os.close
    original_fsync = os.fsync
    source_descriptor = -1
    destination_descriptor = -1

    class PrimaryTransferError(OSError):
        pass

    class InjectedCloseError(OSError):
        pass

    def tracked_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal source_descriptor, destination_descriptor
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == entry.name and dir_fd == entry.parent.fd:
            source_descriptor = descriptor
        elif (
            path == destination_name
            and dir_fd == destination_parent.fd
            and flags & os.O_CREAT
        ):
            destination_descriptor = descriptor
        return descriptor

    def failing_fsync(descriptor: int) -> None:
        primary_target = (
            destination_parent.fd
            if transfer_kind == "copy"
            else entry.parent.fd
        )
        if descriptor == primary_target:
            raise PrimaryTransferError("primary transfer failure")
        original_fsync(descriptor)

    def failing_close(descriptor: int) -> None:
        close_target = (
            destination_descriptor
            if transfer_kind == "copy"
            else source_descriptor
        )
        original_close(descriptor)
        if descriptor == close_target:
            raise InjectedCloseError("local close failed")

    transfer = (
        oracle_boot._copy_regular_exclusive
        if transfer_kind == "copy"
        else oracle_boot._move_regular_exclusive
    )
    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(
                oracle_boot,
                "os",
                _ModuleProxy(
                    os,
                    open=tracked_open,
                    close=failing_close,
                    fsync=failing_fsync,
                ),
                raising=False,
            )
            with pytest.raises(
                PrimaryTransferError,
                match="primary transfer failure",
            ) as raised:
                transfer(
                    entry,
                    destination_parent,
                    destination_name,
                    evidence / destination_name,
                    expected,
                )

        expected_note = (
            "copy destination close also failed"
            if transfer_kind == "copy"
            else "move source close also failed"
        )
        assert any(
            expected_note in note and "local close failed" in note
            for note in getattr(raised.value, "__notes__", ())
        )
        captured = [source_descriptor]
        if destination_descriptor >= 0:
            captured.append(destination_descriptor)
        assert all(descriptor >= 0 for descriptor in captured)
        for descriptor in captured:
            with pytest.raises(OSError) as closed:
                os.fstat(descriptor)
            assert closed.value.errno == errno.EBADF
    finally:
        for descriptor in (source_descriptor, destination_descriptor):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        destination_parent.close()
        scan.close()


def test_copy_source_close_failure_cannot_orphan_destination_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    source = game / "preloader_source.log"
    source.write_bytes(b"payload")
    scan = oracle_boot._scan_preloader_logs(game)
    entry = scan.entries[0]
    expected = oracle_boot._fingerprint_scanned(entry)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    destination_parent = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    original_open = os.open
    original_close = os.close
    source_descriptor = -1
    destination_descriptor = -1

    class SourceCloseError(OSError):
        pass

    def tracked_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal source_descriptor, destination_descriptor
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == entry.name and dir_fd == entry.parent.fd:
            source_descriptor = descriptor
        elif (
            path == "copied.log"
            and dir_fd == destination_parent.fd
            and flags & os.O_CREAT
        ):
            destination_descriptor = descriptor
        return descriptor

    def fail_source_close(descriptor: int) -> None:
        original_close(descriptor)
        if descriptor == source_descriptor:
            raise SourceCloseError("source close failed")

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(
                oracle_boot,
                "os",
                _ModuleProxy(
                    os,
                    open=tracked_open,
                    close=fail_source_close,
                ),
                raising=False,
            )
            with pytest.raises(
                SourceCloseError,
                match="source close failed",
            ):
                oracle_boot._copy_regular_exclusive(
                    entry,
                    destination_parent,
                    "copied.log",
                    evidence / "copied.log",
                    expected,
                )

        assert source_descriptor >= 0
        assert destination_descriptor >= 0
        for descriptor in (source_descriptor, destination_descriptor):
            with pytest.raises(OSError) as closed:
                os.fstat(descriptor)
            assert closed.value.errno == errno.EBADF
    finally:
        for descriptor in (source_descriptor, destination_descriptor):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        destination_parent.close()
        scan.close()


def test_collect_retained_final_scan_replaces_stale_unsafe_issues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"outside")
    transient = game / "preloader_transient.log"
    transient.symlink_to(outside)
    original_allocate = oracle_boot._allocate_evidence_directory

    def allocate_then_remove(*args, **kwargs):
        result = original_allocate(*args, **kwargs)
        transient.unlink()
        return result

    monkeypatch.setattr(
        oracle_boot,
        "_allocate_evidence_directory",
        allocate_then_remove,
    )

    retained = oracle_boot._collect_boot_evidence_retained(
        (),
        game,
        tmp_path / "evidence",
        expected_inventory=None,
    )
    try:
        assert retained.public.issues == ()
        assert retained.public.moved_logs == ()
        assert retained.public.copied_logs == ()
        assert retained.files == ()
    finally:
        retained.close()
    assert outside.read_bytes() == b"outside"


def test_public_collect_signature_delegates_and_closes_retained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    signature = inspect.signature(collect_boot_evidence)
    assert tuple(signature.parameters) == (
        "before",
        "game_root",
        "evidence_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        and parameter.default is inspect.Parameter.empty
        for parameter in signature.parameters.values()
    )
    public = oracle_boot.BootEvidence(
        evidence_dir=tmp_path / "evidence-run",
        moved_logs=(),
        copied_logs=(),
        issues=(),
    )
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    verification_calls: list[object] = []
    close_calls = 0

    class FakeRetained:
        def __init__(self):
            self.public = public

        def close(self):
            nonlocal close_calls
            close_calls += 1

    fake_retained = FakeRetained()

    def collect_private(*args, **kwargs):
        calls.append((args, kwargs))
        return fake_retained

    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        collect_private,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_verify_and_sync_retained_evidence",
        verification_calls.append,
    )
    game = tmp_path / "game"
    evidence = tmp_path / "evidence"

    observed = collect_boot_evidence((), game, evidence)

    assert observed is public
    assert calls == [
        (
            ((), game, evidence),
            {"expected_inventory": None},
        )
    ]
    assert verification_calls == [fake_retained]
    assert close_calls == 1


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


def test_collect_retries_only_eexist_with_exact_utc_token_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    new_log = game / "preloader_new.log"
    new_log.write_bytes(b"new")
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    timestamp = "20260728T123456.123456Z"
    first = "0" * 32
    second = "1" * 32
    collision = evidence_root / f"{timestamp}-{first}"
    collision.mkdir()
    marker = collision / "keep"
    marker.write_bytes(b"collision survives")
    tokens = iter((first, second))
    token_calls = 0

    def next_token() -> str:
        nonlocal token_calls
        token_calls += 1
        return next(tokens)

    monkeypatch.setattr(
        oracle_boot,
        "_utc_now",
        lambda: datetime(
            2026, 7, 28, 12, 34, 56, 123456, tzinfo=timezone.utc
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot, "_random_token", next_token, raising=False
    )

    result = collect_boot_evidence((), game, evidence_root)

    assert token_calls == 2
    assert result.evidence_dir == (
        evidence_root / f"{timestamp}-{second}"
    ).resolve()
    assert re.fullmatch(
        r"\d{8}T\d{6}\.\d{6}Z-[0-9a-f]{32}",
        result.evidence_dir.name,
    )
    assert marker.read_bytes() == b"collision survives"
    assert result.moved_logs == (
        result.evidence_dir / "preloader_new.log",
    )


def test_random_token_uses_exact_token_hex_16_boundary(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[int] = []
    expected = "0123456789abcdef0123456789abcdef"

    def token_hex(byte_count: int) -> str:
        calls.append(byte_count)
        return expected

    monkeypatch.setattr(
        oracle_boot,
        "secrets",
        _ModuleProxy(secrets, token_hex=token_hex),
        raising=False,
    )

    observed = oracle_boot._random_token()

    assert calls == [16]
    assert observed == expected
    assert re.fullmatch(r"[0-9a-f]{32}", observed)


@pytest.mark.parametrize(
    "invalid_token",
    [
        "A" * 32,
        "g" * 32,
        "a" * 31,
    ],
    ids=["uppercase", "nonhex", "wrong-length"],
)
def test_collect_rejects_invalid_random_token_before_allocation_or_move(
    invalid_token: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    new_log = game / "preloader_new.log"
    new_log.write_bytes(b"new")
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    sentinel = evidence_root / "keep"
    sentinel.write_bytes(b"keep")
    game_before = _test_tree_snapshot(game)
    evidence_before = _test_tree_snapshot(evidence_root)
    token_calls = 0
    mutation_calls: list[tuple[str, tuple[object, ...]]] = []

    def token() -> str:
        nonlocal token_calls
        token_calls += 1
        return invalid_token

    def forbidden_mkdir(*args, **_kwargs):
        mutation_calls.append(("mkdir", args))
        raise AssertionError("invalid token must precede allocation")

    def forbidden_rename(*args, **_kwargs):
        mutation_calls.append(("rename", args))
        raise AssertionError("invalid token must precede movement")

    monkeypatch.setattr(
        oracle_boot, "_random_token", token, raising=False
    )
    monkeypatch.setattr(
        oracle_boot,
        "_utc_now",
        lambda: datetime(
            2026, 7, 28, 12, 34, 56, 123456, tzinfo=timezone.utc
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            mkdir=forbidden_mkdir,
            rename=forbidden_rename,
        ),
        raising=False,
    )

    with pytest.raises(Exception):
        collect_boot_evidence((), game, evidence_root)

    assert token_calls == 1
    assert mutation_calls == []
    assert _test_tree_snapshot(game) == game_before
    assert _test_tree_snapshot(evidence_root) == evidence_before


@pytest.mark.parametrize(
    "unsafe_root",
    ["root_symlink", "parent_symlink", "parent_file"],
)
def test_collect_rejects_unsafe_evidence_roots_without_retry_or_mutation(
    unsafe_root: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game = tmp_path / "game"
    game.mkdir()
    new_log = game / "preloader_new.log"
    new_log.write_bytes(b"new")
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside survives")
    token_calls = 0

    if unsafe_root == "root_symlink":
        target = tmp_path / "target"
        target.mkdir()
        protected_root = target
        evidence_root = tmp_path / "evidence-link"
        evidence_root.symlink_to(target, target_is_directory=True)
    elif unsafe_root == "parent_symlink":
        protected_root = real_parent
        parent_link = tmp_path / "parent-link"
        parent_link.symlink_to(real_parent, target_is_directory=True)
        evidence_root = parent_link / "evidence"
    else:
        protected_root = real_parent
        parent_file = tmp_path / "parent-file"
        parent_file.write_bytes(b"not a directory")
        evidence_root = parent_file / "evidence"
    sentinel = protected_root / "sentinel/nested/keep.bin"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"sentinel survives")
    protected_before = _test_tree_snapshot(protected_root)
    outside_before = outside.read_bytes()

    def token() -> str:
        nonlocal token_calls
        token_calls += 1
        return "2" * 32

    monkeypatch.setattr(
        oracle_boot, "_random_token", token, raising=False
    )

    with pytest.raises(Exception):
        collect_boot_evidence((), game, evidence_root)

    assert token_calls == 0
    assert _test_tree_snapshot(protected_root) == protected_before
    assert sentinel.read_bytes() == b"sentinel survives"
    assert outside.read_bytes() == outside_before
    assert new_log.read_bytes() == b"new"
    if unsafe_root == "root_symlink":
        assert {
            path.relative_to(protected_root).as_posix()
            for path in protected_root.rglob("*")
        } == {
            "sentinel",
            "sentinel/nested",
            "sentinel/nested/keep.bin",
        }
    elif unsafe_root == "parent_symlink":
        assert not (real_parent / "evidence").exists()
    else:
        assert (tmp_path / "parent-file").read_bytes() == b"not a directory"


def test_stage_probe_json_duplicates_retained_directory_handle(
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
    original_descriptor = retained.directory_handle.fd
    staged = None
    retained_closed = False
    try:
        staged = oracle_boot._stage_probe_json(
            retained.public.evidence_dir,
            {"schema_version": 1},
            _directory_handle=retained.directory_handle,
        )
        staged_descriptors = (
            staged.directory_handle.fd,
            staged.verifier_fd,
        )
        assert len(set((original_descriptor, *staged_descriptors))) == 3
        assert (
            staged.directory_handle.device,
            staged.directory_handle.inode,
        ) == (
            retained.directory_handle.device,
            retained.directory_handle.inode,
        )
        assert all(
            os.fstat(descriptor)
            for descriptor in (original_descriptor, *staged_descriptors)
        )

        retained.close()
        retained_closed = True
        with pytest.raises(OSError) as raised:
            os.fstat(original_descriptor)
        assert raised.value.errno == errno.EBADF
        assert all(
            os.fstat(descriptor) for descriptor in staged_descriptors
        )

        oracle_boot._close_staged_probe_json(staged)
        for descriptor in staged_descriptors:
            with pytest.raises(OSError) as raised:
                os.fstat(descriptor)
            assert raised.value.errno == errno.EBADF
        staged = None
    finally:
        if not retained_closed:
            retained.close()
        if staged is not None:
            oracle_boot._close_staged_probe_json(staged)


def test_stage_probe_json_encodes_before_retained_handle_duplication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    handle = oracle_boot._open_absolute_directory(
        evidence,
        "evidence directory",
    )
    original_duplicate = oracle_boot._duplicate_directory_handle
    duplicates: list[oracle_boot._DirectoryHandle] = []

    def capture_duplicate(candidate):
        duplicate = original_duplicate(candidate)
        duplicates.append(duplicate)
        return duplicate

    monkeypatch.setattr(
        oracle_boot,
        "_duplicate_directory_handle",
        capture_duplicate,
    )
    try:
        with pytest.raises(TypeError):
            oracle_boot._stage_probe_json(
                evidence,
                {"not-json": object()},
                _directory_handle=handle,
            )
        assert duplicates == []
        assert os.fstat(handle.fd)
    finally:
        for duplicate in duplicates:
            duplicate.close()
        handle.close()


@pytest.mark.parametrize(
    "existing_kind",
    ["file", "directory", "symlink"],
)
def test_write_probe_json_is_canonical_exclusive_and_no_overwrite(
    existing_kind: str,
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {
        "z": "snowman \u2603",
        "a": [3, 2, 1],
        "nested": {"b": False, "a": None},
    }
    probe = evidence / "probe.json"

    oracle_boot._write_probe_json(evidence, payload)

    expected = (
        b'{\n'
        b'  "a": [\n'
        b'    3,\n'
        b'    2,\n'
        b'    1\n'
        b'  ],\n'
        b'  "nested": {\n'
        b'    "a": null,\n'
        b'    "b": false\n'
        b'  },\n'
        b'  "z": "snowman \xe2\x98\x83"\n'
        b'}\n'
    )
    assert probe.read_bytes() == expected
    original_stat = probe.stat(follow_symlinks=False)
    with pytest.raises(Exception):
        oracle_boot._write_probe_json(evidence, {"replacement": True})
    assert probe.read_bytes() == expected
    after_stat = probe.stat(follow_symlinks=False)
    assert (after_stat.st_dev, after_stat.st_ino) == (
        original_stat.st_dev,
        original_stat.st_ino,
    )

    collision_dir = tmp_path / f"collision-{existing_kind}"
    collision_dir.mkdir()
    collision = collision_dir / "probe.json"
    outside = tmp_path / f"outside-{existing_kind}"
    if existing_kind == "file":
        collision.write_bytes(b"keep file")
    elif existing_kind == "directory":
        collision.mkdir()
        (collision / "keep").write_bytes(b"keep directory")
    else:
        outside.write_bytes(b"keep outside")
        collision.symlink_to(outside)
    with pytest.raises(Exception):
        oracle_boot._write_probe_json(collision_dir, payload)
    if existing_kind == "file":
        assert collision.read_bytes() == b"keep file"
    elif existing_kind == "directory":
        assert (collision / "keep").read_bytes() == b"keep directory"
    else:
        assert collision.is_symlink()
        assert outside.read_bytes() == b"keep outside"


@pytest.mark.parametrize(
    "boundary",
    [
        "file_fsync",
        "file_close",
        "directory_fsync",
        "directory_close",
    ],
)
def test_write_probe_json_commits_only_after_required_boundaries(
    boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    sentinel = evidence / "keep.bin"
    sentinel.write_bytes(b"evidence sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    owned = _OwnedWriterDescriptors(evidence, boundary)
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=owned.open,
            fsync=owned.fsync,
            close=owned.close,
        ),
        raising=False,
    )
    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc
    finally:
        reclaimed, reused, cleanup_errors = (
            owned.reclaim_matching_owned()
        )

    assert owned.injection_reached
    if boundary != "directory_close":
        assert raised is not None
        chain = _exception_graph(raised)
        assert any(
            isinstance(candidate, _InjectedWriterBoundaryError)
            for candidate in chain
        ), chain
        returned = False
    else:
        returned = raised is None
    _assert_probe_commit_tree(
        evidence,
        expected_payload,
        returned=returned,
    )
    if returned:
        owned.assert_canonical_identity()
    assert reclaimed == ()
    assert reused == ()
    assert cleanup_errors == ()
    assert sentinel.read_bytes() == b"evidence sentinel survives"
    assert outside.read_bytes() == b"outside sentinel survives"


@pytest.mark.parametrize("unsafe_kind", ["directory_symlink", "parent_symlink"])
def test_write_probe_json_rejects_unsafe_containment(
    unsafe_kind: str,
    tmp_path: Path,
):
    real_parent = tmp_path / "real-parent"
    evidence = real_parent / "evidence"
    evidence.mkdir(parents=True)
    if unsafe_kind == "directory_symlink":
        requested = tmp_path / "evidence-link"
        requested.symlink_to(evidence, target_is_directory=True)
    else:
        parent_link = tmp_path / "parent-link"
        parent_link.symlink_to(real_parent, target_is_directory=True)
        requested = parent_link / "evidence"

    with pytest.raises(Exception):
        oracle_boot._write_probe_json(requested, {"safe": False})

    assert not (evidence / "probe.json").exists()


def test_boot_probe_pins_exact_reviewed_game_assembly_sha256():
    assert oracle_boot.EXPECTED_ASSEMBLY_SHA256 == EXPECTED_ASSEMBLY_SHA256


@pytest.mark.parametrize("result_kind", ["clean", "tahoe_reordered"])
def test_tahoe_code_signature_capture_uses_one_verbose_command_and_preserves_raw_streams(
    result_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    calls: list[tuple[list[str], dict[str, object]]] = []
    if result_kind == "clean":
        expected = _clean_code_signature(layout.app)
    else:
        expected = _tahoe_code_signature(
            layout.app,
            stdout_lines=tuple(
                reversed(_tahoe_code_signature_lines(layout.app))
            ),
        )

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(
            argv,
            expected.returncode,
            stdout=expected.stdout.encode("utf-8"),
            stderr=expected.stderr.encode("utf-8"),
        )

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, run=fake_run),
        raising=False,
    )

    observed = oracle_boot._capture_app_signature(layout.app)

    assert layout.app.resolve().is_dir()
    assert not layout.app.is_symlink()
    assert calls == [
        (
            [
                "codesign",
                "--verify",
                "--deep",
                "--strict",
                "--verbose=1",
                str(layout.app.resolve()),
            ],
            {
                "capture_output": True,
                "check": False,
            },
        )
    ]
    assert observed == expected
    assert not hasattr(observed, "__dict__")
    with pytest.raises((AttributeError, TypeError)):
        observed.stderr = "mutated"


@pytest.mark.parametrize(
    ("raw_stdout", "raw_stderr", "expected_stdout", "expected_stderr"),
    [
        (
            b"file added: first\nfile missing: second\n",
            b"Sausage.app: a sealed resource is missing or invalid\n",
            "file added: first\nfile missing: second\n",
            "Sausage.app: a sealed resource is missing or invalid\n",
        ),
        (
            b"file added: first\r\nfile missing: second\r\n",
            b"Sausage.app: a sealed resource is missing or invalid\r\n",
            "file added: first\r\nfile missing: second\r\n",
            "Sausage.app: a sealed resource is missing or invalid\r\n",
        ),
    ],
)
def test_tahoe_code_signature_raw_capture_preserves_lf_and_crlf(
    raw_stdout: bytes,
    raw_stderr: bytes,
    expected_stdout: str,
    expected_stderr: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(
            argv,
            1,
            stdout=raw_stdout,
            stderr=raw_stderr,
        )

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, run=fake_run),
        raising=False,
    )

    observed = oracle_boot._capture_app_signature(layout.app)

    assert calls == [
        (
            [
                "codesign",
                "--verify",
                "--deep",
                "--strict",
                "--verbose=1",
                str(layout.app.resolve()),
            ],
            {
                "capture_output": True,
                "check": False,
            },
        )
    ]
    assert observed == oracle_boot._AppSignature(
        returncode=1,
        stdout=expected_stdout,
        stderr=expected_stderr,
    )


@pytest.mark.parametrize(
    ("invalid_stream", "raw_stdout", "raw_stderr"),
    [
        ("stdout", b"valid line\n\xff", b""),
        ("stderr", b"", b"valid line\n\xff"),
    ],
)
def test_tahoe_code_signature_raw_capture_rejects_invalid_utf8(
    invalid_stream: str,
    raw_stdout: bytes,
    raw_stderr: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)

    def fake_run(argv, **_kwargs):
        return subprocess.CompletedProcess(
            argv,
            1,
            stdout=raw_stdout,
            stderr=raw_stderr,
        )

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, run=fake_run),
        raising=False,
    )

    with pytest.raises(
        oracle_boot.BootProbeError,
        match=rf"codesign {invalid_stream} is not valid UTF-8",
    ) as raised:
        oracle_boot._capture_app_signature(layout.app)

    assert isinstance(raised.value.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize(
    "signature",
    [
        (0, "", ""),
        (
            1,
            "",
            "Foregroundr.bundle: code object is not signed at all\n",
        ),
    ],
)
def test_capture_boot_snapshot_hashes_real_paths_and_exact_boundaries(
    signature: tuple[int, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    compatibility = SimpleNamespace(state="patched")
    status = SimpleNamespace(
        healthy=True,
        missing=(),
        changed=(),
        preloader_compatibility=compatibility,
    )
    status_calls: list[Path] = []
    signature_calls: list[Path] = []
    hash_calls: list[Path] = []
    original_hash = oracle_boot._sha256_file
    signature_snapshot = oracle_boot._AppSignature(
        returncode=signature[0],
        stdout=signature[1],
        stderr=signature[2],
    )

    def capture_status(game_root: Path):
        status_calls.append(game_root)
        return status

    def capture_signature(app: Path):
        signature_calls.append(app)
        return signature_snapshot

    def capture_hash(path: Path):
        hash_calls.append(path)
        return original_hash(path)

    monkeypatch.setattr(
        oracle_boot, "status_install", capture_status, raising=False
    )
    monkeypatch.setattr(
        oracle_boot,
        "_capture_app_signature",
        capture_signature,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot, "_sha256_file", capture_hash, raising=False
    )

    snapshot = oracle_boot._capture_boot_snapshot(layout.game)

    assert status_calls == [layout.game.resolve()]
    assert signature_calls == [layout.app.resolve()]
    assert hash_calls == [
        layout.assembly.resolve(),
        layout.preloader.resolve(),
    ]
    assert snapshot.assembly_sha256 == _sha256(layout.assembly)
    assert snapshot.active_preloader_sha256 == _sha256(layout.preloader)
    assert snapshot.installer_healthy is True
    assert snapshot.compatibility_state == "patched"
    assert snapshot.app_signature == signature_snapshot
    assert not hasattr(snapshot, "__dict__")
    with pytest.raises((AttributeError, TypeError)):
        snapshot.installer_healthy = False


def _boot_signature(layout: SimpleNamespace, kind: str):
    if kind == "clean":
        return _clean_code_signature(layout.app)
    if kind == "foreground":
        return _tahoe_code_signature(layout.app)
    if kind == "other":
        return oracle_boot._AppSignature(
            1,
            "",
            f"{layout.app.resolve() / 'Contents/Resources/Other.bundle'}: "
            "code object is not signed at all\n",
        )
    if kind == "foreground_plus_other":
        signature = _tahoe_code_signature(layout.app)
        return oracle_boot._AppSignature(
            signature.returncode,
            signature.stdout
            + f"file added: "
            f"{layout.app.resolve() / 'Contents/Resources/Other.bundle'}\n",
            signature.stderr,
        )
    if kind == "foreground_changed":
        lines = _tahoe_code_signature_lines(layout.app)
        return _tahoe_code_signature(
            layout.app,
            stdout_lines=(
                lines[0].replace("CodeResources", "CodeResources.changed"),
                *lines[1:],
            ),
        )
    raise AssertionError(kind)


def _boot_snapshot(
    layout: SimpleNamespace,
    *,
    state: str = "patched",
    healthy: bool = True,
    assembly_sha256: str = EXPECTED_ASSEMBLY_SHA256,
    preloader_sha256: str = "a" * 64,
    signature: str | oracle_boot._AppSignature = "clean",
):
    app_signature = (
        _boot_signature(layout, signature)
        if isinstance(signature, str)
        else signature
    )
    return oracle_boot._BootSnapshot(
        assembly_sha256=assembly_sha256,
        active_preloader_sha256=preloader_sha256,
        installer_healthy=healthy,
        compatibility_state=state,
        app_signature=app_signature,
    )


@pytest.mark.parametrize(
    "signature_kind",
    ["clean", "tahoe_original_order", "tahoe_reverse_order"],
)
def test_tahoe_code_signature_preflight_accepts_only_reviewed_identity_orders(
    signature_kind: str,
    tmp_path: Path,
):
    layout = _probe_layout(tmp_path)
    if signature_kind == "clean":
        signature = _clean_code_signature(layout.app)
    else:
        lines = _tahoe_code_signature_lines(layout.app)
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=(
                lines
                if signature_kind == "tahoe_original_order"
                else tuple(reversed(lines))
            ),
        )
    snapshot = _boot_snapshot(layout, signature=signature)

    assert oracle_boot._preflight_issues(
        snapshot,
        layout.app.resolve(),
    ) == ()


def test_tahoe_code_signature_probe_accepts_order_only_delta_and_preserves_raw_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    lines = _tahoe_code_signature_lines(layout.app)
    before_signature = _tahoe_code_signature(
        layout.app,
        stdout_lines=lines,
    )
    after_signature = _tahoe_code_signature(
        layout.app,
        stdout_lines=tuple(reversed(lines)),
    )
    snapshots = iter(
        (
            _boot_snapshot(layout, signature=before_signature),
            _boot_snapshot(layout, signature=after_signature),
        )
    )
    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        lambda _game_root: next(snapshots),
        raising=False,
    )

    result = oracle_boot.run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is True
    assert result.markers == REQUIRED_MARKERS
    assert result.issues == ()
    payload = json.loads(
        (result.evidence_dir / "probe.json").read_text(encoding="utf-8")
    )
    assert payload["before"]["app_signature"] == {
        "returncode": 1,
        "stdout": before_signature.stdout,
        "stderr": before_signature.stderr,
    }
    assert payload["after"]["app_signature"] == {
        "returncode": 1,
        "stdout": after_signature.stdout,
        "stderr": after_signature.stderr,
    }
    assert before_signature.stdout != after_signature.stdout


@pytest.mark.parametrize(
    "unreviewed_case",
    [
        "missing_line",
        "duplicate_replacing_line",
        "duplicate_extra_expected_line",
        "changed_line",
        "outside_bundle_line",
        "modified_inside_bundle",
        "extra_stderr",
        "unattributed_nonverbose",
        "wrong_returncode",
        "missing_final_newline",
        "crlf_line_endings",
        "stderr_missing_final_newline",
        "stderr_crlf_line_ending",
        "stdout_finding_moved_to_stderr",
        "stale_resources_location",
        "clean_empty_stderr",
        "clean_stdout_diagnostic",
        "clean_stderr_diagnostic",
    ],
)
def test_tahoe_code_signature_preflight_rejects_every_unreviewed_result_before_launch(
    unreviewed_case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    lines = _tahoe_code_signature_lines(layout.app)
    exact = _tahoe_code_signature(layout.app)
    if unreviewed_case == "missing_line":
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=lines[:-1],
        )
    elif unreviewed_case == "duplicate_replacing_line":
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=(*lines[:-1], lines[0]),
        )
    elif unreviewed_case == "duplicate_extra_expected_line":
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=(*lines, lines[0]),
        )
    elif unreviewed_case == "changed_line":
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=(
                lines[0].replace(
                    "CodeResources",
                    "CodeResources.changed",
                ),
                *lines[1:],
            ),
        )
    elif unreviewed_case == "outside_bundle_line":
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=(
                *lines,
                f"file added: "
                f"{layout.app.resolve() / 'Contents/Resources/Other.bundle'}\n",
            ),
        )
    elif unreviewed_case == "modified_inside_bundle":
        signature = _tahoe_code_signature(
            layout.app,
            stdout_lines=(
                lines[0].replace("file added:", "file modified:"),
                *lines[1:],
            ),
        )
    elif unreviewed_case == "extra_stderr":
        signature = _tahoe_code_signature(
            layout.app,
            stderr=exact.stderr + "unexpected diagnostic\n",
        )
    elif unreviewed_case == "unattributed_nonverbose":
        signature = oracle_boot._AppSignature(1, "", exact.stderr)
    elif unreviewed_case == "wrong_returncode":
        signature = _tahoe_code_signature(layout.app, returncode=2)
    elif unreviewed_case == "missing_final_newline":
        signature = oracle_boot._AppSignature(
            exact.returncode,
            exact.stdout[:-1],
            exact.stderr,
        )
    elif unreviewed_case == "crlf_line_endings":
        signature = oracle_boot._AppSignature(
            exact.returncode,
            exact.stdout.replace("\n", "\r\n"),
            exact.stderr,
        )
    elif unreviewed_case == "stderr_missing_final_newline":
        signature = oracle_boot._AppSignature(
            exact.returncode,
            exact.stdout,
            exact.stderr[:-1],
        )
    elif unreviewed_case == "stderr_crlf_line_ending":
        signature = oracle_boot._AppSignature(
            exact.returncode,
            exact.stdout,
            exact.stderr.replace("\n", "\r\n"),
        )
    elif unreviewed_case == "stdout_finding_moved_to_stderr":
        signature = oracle_boot._AppSignature(
            exact.returncode,
            "".join(lines[1:]),
            lines[0] + exact.stderr,
        )
    elif unreviewed_case == "stale_resources_location":
        signature = oracle_boot._AppSignature(
            1,
            "",
            f"{layout.app.resolve() / 'Contents/Resources/Foregroundr.bundle'}: "
            "code object is not signed at all\n",
        )
    elif unreviewed_case == "clean_empty_stderr":
        signature = oracle_boot._AppSignature(0, "", "")
    elif unreviewed_case == "clean_stdout_diagnostic":
        signature = oracle_boot._AppSignature(0, "diagnostic\n", "")
    elif unreviewed_case == "clean_stderr_diagnostic":
        signature = oracle_boot._AppSignature(0, "", "diagnostic\n")
    else:
        raise AssertionError(unreviewed_case)
    snapshot = _boot_snapshot(layout, signature=signature)
    popen_calls = 0

    def capture_snapshot(_game_root: Path):
        return snapshot

    def forbidden_popen(*_args, **_kwargs):
        nonlocal popen_calls
        popen_calls += 1
        raise AssertionError("unreviewed signature must fail before launch")

    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        capture_snapshot,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden_popen),
        raising=False,
    )

    result = oracle_boot.run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is False
    assert result.markers == ()
    assert (
        "game app code signature is not an accepted exact result"
        in result.issues
    )
    assert popen_calls == 0
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


def test_tahoe_code_signature_postflight_semantic_delta_fails_despite_all_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    lines = _tahoe_code_signature_lines(layout.app)
    before_signature = _tahoe_code_signature(layout.app)
    after_signature = _tahoe_code_signature(
        layout.app,
        stdout_lines=(
            lines[0].replace("CodeResources", "CodeResources.changed"),
            *lines[1:],
        ),
    )
    snapshots = iter(
        (
            _boot_snapshot(layout, signature=before_signature),
            _boot_snapshot(layout, signature=after_signature),
        )
    )
    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        lambda _game_root: next(snapshots),
        raising=False,
    )

    result = oracle_boot.run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is False
    assert result.markers == REQUIRED_MARKERS
    assert any(
        "code-signature result changed during boot probe" in issue
        for issue in result.issues
    )
    assert all(
        process.poll() is not None
        for process, _, _ in tracked_probe_popen.tracked
    )


@pytest.mark.parametrize(
    ("state", "healthy", "signature", "assembly_sha256"),
    [
        ("official", True, "clean", EXPECTED_ASSEMBLY_SHA256),
        ("invalid", True, "clean", EXPECTED_ASSEMBLY_SHA256),
        ("patched", False, "clean", EXPECTED_ASSEMBLY_SHA256),
        ("patched", True, "other", EXPECTED_ASSEMBLY_SHA256),
        (
            "patched",
            True,
            "foreground_plus_other",
            EXPECTED_ASSEMBLY_SHA256,
        ),
        (
            "patched",
            True,
            "foreground_changed",
            EXPECTED_ASSEMBLY_SHA256,
        ),
        ("patched", True, "clean", "d" * 64),
    ],
)
def test_probe_preflight_rejects_invalid_snapshot_without_launch(
    state: str,
    healthy: bool,
    signature: str,
    assembly_sha256: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        exit_code=0,
    )
    snapshot_calls: list[Path] = []
    preflight = _boot_snapshot(
        layout,
        state=state,
        healthy=healthy,
        signature=signature,
        assembly_sha256=assembly_sha256,
    )
    popen_calls = 0

    def capture_snapshot(game_root: Path):
        snapshot_calls.append(game_root)
        return preflight

    def forbidden_popen(*_args, **_kwargs):
        nonlocal popen_calls
        popen_calls += 1
        raise AssertionError("invalid preflight must not launch")

    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        capture_snapshot,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden_popen),
        raising=False,
    )

    result = oracle_boot.run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is False
    assert result.issues
    assert result.evidence_dir.is_dir()
    assert snapshot_calls == [layout.game.resolve()]
    assert popen_calls == 0
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


@pytest.mark.parametrize(
    ("mismatch", "pre_signature", "post_signature"),
    [
        ("state_official", "clean", "clean"),
        ("state_invalid", "clean", "clean"),
        ("patched_unhealthy", "clean", "clean"),
        ("assembly", "clean", "clean"),
        ("preloader", "clean", "clean"),
        ("signature_added", "clean", "foreground"),
        ("signature_removed", "foreground", "clean"),
        ("signature_changed", "foreground", "foreground_changed"),
    ],
)
def test_probe_postflight_mismatch_fails_despite_all_markers(
    mismatch: str,
    pre_signature: str,
    post_signature: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    preflight = _boot_snapshot(layout, signature=pre_signature)
    post_kwargs: dict[str, object] = {"signature": post_signature}
    if mismatch == "state_official":
        post_kwargs["state"] = "official"
    elif mismatch == "state_invalid":
        post_kwargs["state"] = "invalid"
    elif mismatch == "patched_unhealthy":
        post_kwargs["healthy"] = False
    elif mismatch == "assembly":
        post_kwargs["assembly_sha256"] = "b" * 64
    elif mismatch == "preloader":
        post_kwargs["preloader_sha256"] = "c" * 64
    postflight = _boot_snapshot(layout, **post_kwargs)
    snapshots = iter((preflight, postflight))
    snapshot_calls: list[Path] = []

    def capture_snapshot(game_root: Path):
        snapshot_calls.append(game_root)
        return next(snapshots)

    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        capture_snapshot,
        raising=False,
    )

    result = oracle_boot.run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert snapshot_calls == [
        layout.game.resolve(),
        layout.game.resolve(),
    ]
    with pytest.raises(StopIteration):
        next(snapshots)
    assert result.success is False
    assert result.markers == REQUIRED_MARKERS
    assert result.issues
    assert result.evidence_dir.is_dir()
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    assert all(
        process.poll() is not None
        for process, _, _ in tracked_probe_popen.tracked
    )


@pytest.mark.parametrize("signature", ["clean", "foreground"])
def test_probe_accepts_stable_reviewed_pre_and_post_snapshots(
    signature: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    snapshot = _boot_snapshot(layout, signature=signature)
    snapshot_calls: list[Path] = []

    def capture_snapshot(game_root: Path):
        snapshot_calls.append(game_root)
        return snapshot

    monkeypatch.setattr(
        oracle_boot,
        "_capture_boot_snapshot",
        capture_snapshot,
        raising=False,
    )

    result = oracle_boot.run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert snapshot_calls == [
        layout.game.resolve(),
        layout.game.resolve(),
    ]
    assert result.success is True
    assert result.markers == REQUIRED_MARKERS
    assert result.issues == ()
    assert result.evidence_dir.is_dir()
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


@pytest.mark.parametrize(
    ("case", "log_text", "exit_code", "expected_markers"),
    [
        (
            "missing_bepinex",
            "\n".join(REQUIRED_MARKERS[1:]),
            None,
            REQUIRED_MARKERS[1:],
        ),
        (
            "missing_unity",
            "\n".join((REQUIRED_MARKERS[0], REQUIRED_MARKERS[2])),
            None,
            (REQUIRED_MARKERS[0], REQUIRED_MARKERS[2]),
        ),
        (
            "missing_oracle",
            "\n".join(REQUIRED_MARKERS[:2]),
            None,
            REQUIRED_MARKERS[:2],
        ),
        (
            "wrong_bepinex",
            "\n".join(
                (
                    "BepInEx 5.4.23.4",
                    REQUIRED_MARKERS[1],
                    REQUIRED_MARKERS[2],
                )
            ),
            None,
            REQUIRED_MARKERS[1:],
        ),
        (
            "wrong_unity",
            "\n".join(
                (
                    REQUIRED_MARKERS[0],
                    "Unity v2018.4.26f1",
                    REQUIRED_MARKERS[2],
                )
            ),
            None,
            (REQUIRED_MARKERS[0], REQUIRED_MARKERS[2]),
        ),
        (
            "wrong_oracle",
            "\n".join(
                (
                    REQUIRED_MARKERS[0],
                    REQUIRED_MARKERS[1],
                    "SSR oracle boot probe not loaded",
                )
            ),
            None,
            REQUIRED_MARKERS[:2],
        ),
        (
            "dll_not_found",
            "\n".join((*REQUIRED_MARKERS, "DllNotFoundException: libc")),
            None,
            REQUIRED_MARKERS,
        ),
        (
            "preloader_error",
            "\n".join((*REQUIRED_MARKERS, "Preloader error: injected")),
            None,
            REQUIRED_MARKERS,
        ),
    ],
)
def test_probe_marker_error_and_exit_outcomes_are_strict(
    case: str,
    log_text: str,
    exit_code: int | None,
    expected_markers: tuple[str, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text=log_text,
        exit_code=exit_code,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        1,
    )

    assert result.success is False, case
    assert result.markers == expected_markers
    assert all(marker in REQUIRED_MARKERS for marker in result.markers)
    assert tuple(
        marker for marker in REQUIRED_MARKERS if marker in result.markers
    ) == result.markers
    assert result.issues
    assert result.exit_code == exit_code
    assert result.evidence_dir.is_dir()
    assert (result.evidence_dir / "probe.json").is_file()
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_probe_already_exited_launcher_preserves_all_marker_evidence(
    exit_code: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="unused deterministic Popen double",
    )
    log = layout.game / "nested/preloader_probe.log"
    popen_calls: list[tuple[list[str], dict[str, object]]] = []
    signal_calls: list[tuple[int, int]] = []
    group_absence_probes = 0
    getpgid_calls = 0

    def exited_popen(argv, **kwargs):
        popen_calls.append((list(argv), dict(kwargs)))
        layout.config.write_bytes(b"[Oracle]\nMode=mutated-before-exit\n")
        layout.config.chmod(0o600)
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
        return _AlreadyExitedProcess(exit_code)

    def forbidden_getpgid(_pid: int) -> int:
        nonlocal getpgid_calls
        getpgid_calls += 1
        raise AssertionError("start_new_session PGID must use the retained PID")

    def absent_synthetic_group(pgid: int, sent_signal: int) -> None:
        nonlocal group_absence_probes
        assert pgid == 424242
        if sent_signal == 0:
            group_absence_probes += 1
            raise ProcessLookupError
        signal_calls.append((pgid, sent_signal))

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=exited_popen),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            getpgid=forbidden_getpgid,
            killpg=absent_synthetic_group,
        ),
        raising=False,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        1,
    )

    expected_evidence_log = result.evidence_dir / "nested/preloader_probe.log"
    assert result.success is False
    assert result.markers == REQUIRED_MARKERS
    assert result.exit_code == exit_code
    assert any(
        "unexpected" in issue.lower()
        and "exit" in issue.lower()
        and str(exit_code) in issue
        for issue in result.issues
    )
    assert result.moved_logs == (expected_evidence_log,)
    assert result.copied_logs == ()
    assert expected_evidence_log.read_text(encoding="utf-8") == "\n".join(
        REQUIRED_MARKERS
    )
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    probe = result.evidence_dir / "probe.json"
    payload = json.loads(probe.read_bytes())
    assert set(payload) == {
        "schema_version",
        "success",
        "exit_code",
        "markers",
        "issues",
        "before",
        "after",
        "before_logs",
        "after_logs",
        "moved_logs",
        "copied_logs",
    }
    assert payload["schema_version"] == 1
    assert payload["success"] is False
    assert payload["exit_code"] == exit_code
    assert payload["markers"] == list(REQUIRED_MARKERS)
    assert payload["issues"] == list(result.issues)
    expected_probe_bytes = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    assert probe.read_bytes() == expected_probe_bytes
    assert popen_calls == [
        (
            [str(launcher.resolve())],
            {
                "cwd": str(layout.game.resolve()),
                "shell": False,
                "start_new_session": True,
            },
        )
    ]
    assert getpgid_calls == 0
    assert group_absence_probes == 1
    assert signal_calls == []


def test_probe_exact_markers_are_ordered_deduplicated_and_group_terminated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(
            (
                "noise",
                REQUIRED_MARKERS[2],
                REQUIRED_MARKERS[0],
                REQUIRED_MARKERS[1],
                REQUIRED_MARKERS[0],
            )
        ),
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is True
    assert result.markers == REQUIRED_MARKERS
    assert result.exit_code is None
    assert result.issues == ()
    assert (result.evidence_dir / "probe.json").is_file()
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


def test_probe_rechecks_shutdown_log_and_rejects_term_appended_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    late_error = "\nDllNotFoundException: injected during shutdown\n"
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        term_append_text=late_error,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    preserved = result.evidence_dir / "nested/preloader_probe.log"
    assert result.success is False
    assert result.exit_code is None
    assert any(
        "DllNotFoundException" in issue for issue in result.issues
    )
    assert late_error.strip() in preserved.read_text(encoding="utf-8")
    payload = json.loads((result.evidence_dir / "probe.json").read_bytes())
    assert payload["success"] is False
    assert payload["exit_code"] is None
    assert payload["issues"] == list(result.issues)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


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


def test_probe_reports_natural_exit_between_marker_scan_and_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="unused deterministic Popen double",
    )
    log = layout.game / "nested/preloader_probe.log"
    exit_code = 23
    signal_calls: list[tuple[int, int]] = []

    class ExitAfterMarkerScan:
        pid = 424242

        def __init__(self):
            self.poll_calls = 0
            self.wait_timeouts: list[float | None] = []

        def poll(self) -> int | None:
            self.poll_calls += 1
            return None if self.poll_calls == 1 else exit_code

        def wait(self, timeout: float | None = None) -> int:
            self.wait_timeouts.append(timeout)
            return exit_code

    process = ExitAfterMarkerScan()

    def fake_popen(*_args, **_kwargs):
        log.parent.mkdir(parents=True)
        log.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")
        return process

    def absent_group(pgid: int, sent_signal: int) -> None:
        assert pgid == process.pid
        if sent_signal == 0:
            raise ProcessLookupError
        signal_calls.append((pgid, sent_signal))

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=fake_popen),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, killpg=absent_group),
        raising=False,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is False
    assert result.exit_code == exit_code
    assert any(
        "unexpected" in issue.lower()
        and "exit" in issue.lower()
        and str(exit_code) in issue
        for issue in result.issues
    )
    assert signal_calls == []
    assert process.poll_calls >= 2
    assert process.wait_timeouts == [0]
    payload = json.loads((result.evidence_dir / "probe.json").read_bytes())
    assert payload["success"] is False
    assert payload["exit_code"] == exit_code
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


@pytest.mark.parametrize(
    ("case", "log_text", "expected_markers"),
    [
        (
            "bepinex_version_extension",
            "\n".join(
                (
                    "BepInEx 5.4.23.50",
                    "Detected Unity version: v2018.4.25f1",
                    REQUIRED_MARKERS[2],
                )
            ),
            REQUIRED_MARKERS[1:],
        ),
        (
            "unity_version_extension",
            "\n".join(
                (
                    REQUIRED_MARKERS[0],
                    "Detected Unity version: v2018.4.25f10",
                    REQUIRED_MARKERS[2],
                )
            ),
            (REQUIRED_MARKERS[0], REQUIRED_MARKERS[2]),
        ),
    ],
)
def test_probe_rejects_extended_version_tokens(
    case: str,
    log_text: str,
    expected_markers: tuple[str, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(tmp_path, log_text=log_text)

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        1,
    )

    assert result.success is False, case
    assert result.markers == expected_markers
    assert result.issues
    assert result.exit_code is None
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


def test_probe_accepts_exact_version_tokens_inside_realistic_log_framing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(
            (
                "[Message:   BepInEx] BepInEx 5.4.23.5 - SSR",
                "[Info   :   BepInEx] Detected Unity version: "
                "v2018.4.25f1",
                "[Info   : SsrOracle] SSR oracle boot probe loaded",
            )
        ),
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is True
    assert result.markers == REQUIRED_MARKERS
    assert result.issues == ()
    assert result.exit_code is None
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


def test_authentic_unity_marker_matches_only_exact_detected_version_line():
    payload = (
        Path(__file__).parent
        / "fixtures/oracle_boot/BepInEx-LogOutput-5.4.23.5.log"
    ).read_bytes()

    assert tuple(
        marker
        for marker in REQUIRED_MARKERS
        if oracle_boot._payload_contains_boot_marker(payload, marker)
    ) == REQUIRED_MARKERS
    for invalid in (
        b"Unity v2018.4.25f1",
        b"Detected Unity version: v2018.4.25f10",
        b"Detected Unity version: xv2018.4.25f1",
    ):
        assert not oracle_boot._payload_contains_boot_marker(
            invalid, REQUIRED_MARKERS[1]
        )


def _signature_json(signature) -> dict[str, object]:
    return {
        "returncode": signature.returncode,
        "stdout": signature.stdout,
        "stderr": signature.stderr,
    }


def _snapshot_json(snapshot) -> dict[str, object]:
    return {
        "assembly_sha256": snapshot.assembly_sha256,
        "active_preloader_sha256": snapshot.active_preloader_sha256,
        "installer_healthy": snapshot.installer_healthy,
        "compatibility_state": snapshot.compatibility_state,
        "app_signature": _signature_json(snapshot.app_signature),
    }


def _fingerprint_json(fingerprint) -> dict[str, object]:
    return {
        "path": str(fingerprint.path),
        "file_type": fingerprint.file_type,
        "inode": fingerprint.inode,
        "size": fingerprint.size,
        "mtime_ns": fingerprint.mtime_ns,
        "sha256": fingerprint.sha256,
    }


def _independent_log_fingerprint(path: Path) -> dict[str, object]:
    observed = path.stat(follow_symlinks=False)
    return {
        "path": str(path.resolve()),
        "file_type": "regular",
        "inode": observed.st_ino,
        "size": observed.st_size,
        "mtime_ns": observed.st_mtime_ns,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


@pytest.mark.parametrize("ordinary_failure", [False, True])
def test_probe_json_schema_v1_matches_independent_exact_encoding(
    ordinary_failure: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    existing = layout.game / "existing/preloader_existing.log"
    existing.parent.mkdir()
    existing.write_text("before", encoding="utf-8")
    before_logs = [_independent_log_fingerprint(existing)]
    log_text = "\n".join(
        REQUIRED_MARKERS if not ordinary_failure else REQUIRED_MARKERS[:2]
    )
    launcher = _launcher(
        tmp_path,
        log_text=log_text,
        changed_log=existing if ordinary_failure else None,
        changed_log_text="after",
    )
    snapshot = _boot_snapshot(layout, signature="clean")
    snapshot_calls: list[Path] = []
    after_logs: list[dict[str, object]] = []
    original_collect_retained = oracle_boot._collect_boot_evidence_retained

    def capture_snapshot(game_root: Path):
        snapshot_calls.append(game_root)
        return snapshot

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
        "_capture_boot_snapshot",
        capture_snapshot,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_utc_now",
        lambda: datetime(
            2026, 7, 28, 12, 34, 56, 123456, tzinfo=timezone.utc
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_random_token",
        lambda: "0123456789abcdef0123456789abcdef",
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        capture_after_logs,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        1,
    )

    assert result.success is (not ordinary_failure)
    expected_markers = (
        REQUIRED_MARKERS if not ordinary_failure else REQUIRED_MARKERS[:2]
    )
    expected_issues = (
        ()
        if not ordinary_failure
        else (
            f"pre-existing preloader log changed: {existing.resolve()}",
            f"missing required boot marker: {REQUIRED_MARKERS[2]}",
        )
    )
    expected_moved = (
        result.evidence_dir / "nested/preloader_probe.log",
    )
    expected_copied = (
        (result.evidence_dir / "existing/preloader_existing.log",)
        if ordinary_failure
        else ()
    )
    assert result.exit_code is None
    assert result.markers == expected_markers
    assert result.issues == expected_issues
    assert result.moved_logs == expected_moved
    assert result.copied_logs == expected_copied
    assert snapshot_calls == [
        layout.game.resolve(),
        layout.game.resolve(),
    ]
    assert result.moved_logs
    assert all(path.is_file() for path in result.moved_logs)
    if ordinary_failure:
        assert result.copied_logs
        assert existing.read_text(encoding="utf-8") == "after"
    else:
        assert result.copied_logs == ()

    after_logs = sorted(
        after_logs,
        key=lambda item: Path(str(item["path"])).relative_to(
            layout.game.resolve()
        ).as_posix(),
    )
    payload = {
        "schema_version": 1,
        "success": not ordinary_failure,
        "exit_code": None,
        "markers": list(expected_markers),
        "issues": list(expected_issues),
        "before": _snapshot_json(snapshot),
        "after": _snapshot_json(snapshot),
        "before_logs": before_logs,
        "after_logs": after_logs,
        "moved_logs": [str(path) for path in expected_moved],
        "copied_logs": [str(path) for path in expected_copied],
    }
    expected = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    assert (result.evidence_dir / "probe.json").read_bytes() == expected
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


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


def test_probe_launches_exact_argv_without_shell_in_distinct_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    controlled_processes,
):
    del controlled_processes
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        exit_code=0,
    )
    observed: dict[str, object] = {}

    class LaunchObserved(RuntimeError):
        pass

    def observe_popen(argv, **kwargs):
        observed["argv"] = argv
        observed.update(kwargs)
        raise LaunchObserved

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        SimpleNamespace(Popen=observe_popen),
        raising=False,
    )

    with pytest.raises(LaunchObserved):
        oracle_boot.run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            5,
        )

    assert observed == {
        "argv": [str(launcher.resolve())],
        "cwd": str(layout.game.resolve()),
        "shell": False,
        "start_new_session": True,
    }


def test_probe_kills_exact_child_handle_when_pgid_retention_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        exit_code=0,
    )
    rejected_pid = os.getpgrp()
    direct_signal_calls: list[tuple[str, tuple[object, ...]]] = []

    class RejectedPgidProcess:
        def __init__(self):
            self.pid = rejected_pid
            self.returncode: int | None = None
            self.kill_calls = 0
            self.wait_timeouts: list[float | None] = []

        def poll(self) -> int | None:
            return self.returncode

        def kill(self) -> None:
            self.kill_calls += 1
            self.returncode = -signal.SIGKILL

        def wait(self, timeout: float | None = None) -> int:
            self.wait_timeouts.append(timeout)
            assert self.returncode is not None
            return self.returncode

    process = RejectedPgidProcess()

    def forbidden_direct_signal(*args):
        direct_signal_calls.append(("signal", args))
        raise AssertionError("rejected PID must not reach an OS signal API")

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=lambda *_args, **_kwargs: process),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            getpgid=forbidden_direct_signal,
            kill=forbidden_direct_signal,
            killpg=forbidden_direct_signal,
        ),
        raising=False,
    )

    with pytest.raises(
        oracle_boot.BootProbeError,
        match="unsafe spawned process-group id",
    ) as caught:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    chain: list[BaseException] = []
    current: BaseException | None = caught.value
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    assert any(
        isinstance(candidate, oracle_boot.BootProbeError)
        and "unsafe spawned process-group id" in str(candidate)
        for candidate in chain
    )
    assert process.kill_calls == 1
    assert process.wait_timeouts == [
        oracle_boot._TERMINATION_GRACE_SECONDS
    ]
    assert direct_signal_calls == []
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


def test_probe_rejects_replaced_absolute_config_parent_at_launch_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    live_parent = tmp_path / "config-live"
    live_parent.mkdir()
    layout.config = layout.config.rename(live_parent / "oracle.cfg")
    retained_parent = tmp_path / "config-retained"
    passive_config = b"; replacement tree\n[Oracle]\nMode=passive\n"
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        exit_code=0,
    )
    original_verify_launcher = oracle_boot._verify_launcher_guard
    mutation_reached = False
    popen_calls = 0

    def replace_config_parent_at_boundary(guard):
        nonlocal mutation_reached
        original_verify_launcher(guard)
        live_parent.rename(retained_parent)
        live_parent.mkdir()
        replacement = live_parent / "oracle.cfg"
        replacement.write_bytes(passive_config)
        replacement.chmod(0o604)
        mutation_reached = True

    def forbidden_popen(*_args, **_kwargs):
        nonlocal popen_calls
        popen_calls += 1
        raise AssertionError("replaced absolute config must not be launched")

    monkeypatch.setattr(
        oracle_boot,
        "_verify_launcher_guard",
        replace_config_parent_at_boundary,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden_popen),
        raising=False,
    )

    raised: Exception | None = None
    try:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised = exc

    assert mutation_reached
    assert raised is not None
    assert _test_tree_snapshot(retained_parent) == (
        ("oracle.cfg", "file", ORIGINAL_CONFIG),
    )
    assert stat.S_IMODE(
        (retained_parent / "oracle.cfg").stat().st_mode
    ) == 0o640
    assert _test_tree_snapshot(live_parent) == (
        ("oracle.cfg", "file", passive_config),
    )
    assert stat.S_IMODE((live_parent / "oracle.cfg").stat().st_mode) == 0o604
    assert popen_calls == 0
    assert isinstance(raised, oracle_boot.BootProbeError)


def test_probe_preserves_full_group_grace_after_term_exits_leader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    grace_seconds = 0.05
    monkeypatch.setattr(
        oracle_boot,
        "_TERMINATION_GRACE_SECONDS",
        grace_seconds,
        raising=False,
    )
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _write_executable(
        tmp_path / "leader-exits-on-term.py",
        f"""
        import os
        from pathlib import Path
        import signal
        import subprocess
        import sys
        import time

        root = Path.cwd()
        (root / "spawned.pid").write_text(str(os.getpid()), encoding="ascii")
        (root / "spawned.pgid").write_text(
            str(os.getpgrp()), encoding="ascii"
        )
        child_code = (
            "import signal,time;"
            "from pathlib import Path;"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN);"
            "Path('descendant.ready').write_text('ready', encoding='ascii');"
            "time.sleep(60)"
        )
        descendant = subprocess.Popen(
            [sys.executable, "-c", child_code],
            cwd=root,
        )
        (root / "descendant.pid").write_text(
            str(descendant.pid), encoding="ascii"
        )
        (root / "descendant.pgid").write_text(
            str(os.getpgid(descendant.pid)), encoding="ascii"
        )
        while not (root / "descendant.ready").exists():
            time.sleep(0.001)
        log = root / "nested" / "preloader_probe.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text({chr(10).join(REQUIRED_MARKERS)!r}, encoding="utf-8")
        time.sleep(60)
        """,
    )
    real_killpg = os.killpg
    group_calls: list[tuple[int, int, float]] = []

    def record_killpg(pgid: int, sent_signal: int):
        group_calls.append((pgid, sent_signal, time.monotonic()))
        return real_killpg(pgid, sent_signal)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, killpg=record_killpg),
        raising=False,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )
    assert result.success is True

    leader_pid = int(
        (layout.game / "spawned.pid").read_text(encoding="ascii")
    )
    leader_pgid = int(
        (layout.game / "spawned.pgid").read_text(encoding="ascii")
    )
    descendant_pid = int(
        (layout.game / "descendant.pid").read_text(encoding="ascii")
    )
    descendant_pgid = int(
        (layout.game / "descendant.pgid").read_text(encoding="ascii")
    )
    assert len(tracked_probe_popen.tracked) == 1
    tracked_process, tracked_pid, tracked_pgid = (
        tracked_probe_popen.tracked[0]
    )
    assert tracked_process.pid == tracked_pid == tracked_pgid == leader_pid
    assert leader_pgid == descendant_pgid == tracked_pgid
    assert {pgid for pgid, _, _ in group_calls} == {tracked_pgid}
    termination_calls = [
        event
        for event in group_calls
        if event[1] in {signal.SIGTERM, signal.SIGKILL}
    ]
    assert [event[1] for event in termination_calls] == [
        signal.SIGTERM,
        signal.SIGKILL,
    ]
    elapsed = termination_calls[1][2] - termination_calls[0][2]
    assert grace_seconds * 0.8 <= elapsed < 1.0
    assert _wait_for_pid_exit(leader_pid)
    assert _wait_for_pid_exit(descendant_pid)
    assert _wait_for_group_exit(tracked_pgid)


def test_probe_escalates_term_to_kill_for_spawned_process_tree_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    assert oracle_boot._TERMINATION_GRACE_SECONDS == 10.0
    monkeypatch.setattr(
        oracle_boot,
        "_TERMINATION_GRACE_SECONDS",
        0.05,
        raising=False,
    )
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        ignore_term=True,
        spawn_descendant=True,
    )
    real_killpg = os.killpg
    group_signals: list[tuple[int, signal.Signals, float]] = []

    def record_killpg(pgid: int, sent_signal: signal.Signals):
        group_signals.append((pgid, sent_signal, time.monotonic()))
        return real_killpg(pgid, sent_signal)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, killpg=record_killpg),
        raising=False,
    )
    unrelated = tracked_probe_popen.original(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=True,
    )
    unrelated_pgid = os.getpgid(unrelated.pid)
    try:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            1,
        )
        leader_pid = int(
            (layout.game / "spawned.pid").read_text(encoding="ascii")
        )
        descendant_pid = int(
            (layout.game / "descendant.pid").read_text(encoding="ascii")
        )
        leader_pgid = int(
            (layout.game / "spawned.pgid").read_text(encoding="ascii")
        )
        descendant_pgid = int(
            (layout.game / "descendant.pgid").read_text(encoding="ascii")
        )
        assert len(tracked_probe_popen.tracked) == 1
        spawned_process, spawned_pid, spawned_pgid = (
            tracked_probe_popen.tracked[0]
        )
        assert spawned_process.pid == spawned_pid == leader_pid
        assert leader_pgid == descendant_pgid == spawned_pgid
        exact_group_signals = [
            event for event in group_signals if event[0] == spawned_pgid
        ]
        assert [event[1] for event in exact_group_signals] == [
            signal.SIGTERM,
            signal.SIGKILL,
        ]
        elapsed = exact_group_signals[1][2] - exact_group_signals[0][2]
        assert 0.04 <= elapsed < 1.0
        assert unrelated_pgid not in {
            pgid for pgid, _, _ in group_signals
        }

        assert _wait_for_pid_exit(leader_pid)
        assert _wait_for_pid_exit(descendant_pid)
        assert unrelated.poll() is None
        assert os.getpgid(unrelated.pid) == unrelated_pgid
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=3)


def test_confirm_process_group_stopped_retries_permission_error_until_absent(
    monkeypatch: pytest.MonkeyPatch,
):
    pgid = 424242
    group_probes: list[tuple[str, int, int]] = []
    virtual_time = -0.25
    sleep_calls: list[float] = []

    def scripted_probe(
        api: str,
        candidate: int,
        sent_signal: int,
    ) -> None:
        group_probes.append((api, candidate, sent_signal))
        if len(group_probes) == 1:
            raise PermissionError("transient group confirmation denial")
        raise ProcessLookupError

    def probe_with_killpg(candidate: int, sent_signal: int) -> None:
        return scripted_probe("killpg", candidate, sent_signal)

    def probe_with_raw_kill(candidate: int, sent_signal: int) -> None:
        return scripted_probe("kill", candidate, sent_signal)

    def monotonic() -> float:
        nonlocal virtual_time
        virtual_time += 0.25
        return virtual_time

    def sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            killpg=probe_with_killpg,
            kill=probe_with_raw_kill,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "time",
        _ModuleProxy(time, monotonic=monotonic, sleep=sleep),
        raising=False,
    )

    oracle_boot._confirm_process_group_stopped(pgid)

    assert len(group_probes) == 2
    assert all(
        sent_signal == 0
        and (
            (api == "killpg" and candidate == pgid)
            or (api == "kill" and candidate == -pgid)
        )
        for api, candidate, sent_signal in group_probes
    )
    assert sleep_calls


def test_confirm_process_group_stopped_bounds_persistent_permission_error(
    monkeypatch: pytest.MonkeyPatch,
):
    pgid = 424242
    group_probes: list[tuple[str, int, int]] = []
    start_time = 100.0
    virtual_time = start_time
    monotonic_observations: list[float] = []
    sleep_calls: list[tuple[float, float]] = []
    call_budget = 256

    def deny_group_probe(
        api: str,
        candidate: int,
        sent_signal: int,
    ) -> None:
        if len(group_probes) >= call_budget:
            raise AssertionError(
                "persistent EPERM probe call budget exceeded"
            )
        group_probes.append((api, candidate, sent_signal))
        raise PermissionError("persistent group confirmation denial")

    def probe_with_killpg(candidate: int, sent_signal: int) -> None:
        return deny_group_probe("killpg", candidate, sent_signal)

    def probe_with_raw_kill(candidate: int, sent_signal: int) -> None:
        return deny_group_probe("kill", candidate, sent_signal)

    def monotonic() -> float:
        if len(monotonic_observations) >= call_budget:
            raise AssertionError(
                "persistent EPERM monotonic call budget exceeded"
            )
        monotonic_observations.append(virtual_time)
        return virtual_time

    def sleep(seconds: float) -> None:
        nonlocal virtual_time
        if len(sleep_calls) >= call_budget:
            raise AssertionError(
                "persistent EPERM sleep call budget exceeded"
            )
        sleep_calls.append((virtual_time, seconds))
        virtual_time += seconds

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            killpg=probe_with_killpg,
            kill=probe_with_raw_kill,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "time",
        _ModuleProxy(time, monotonic=monotonic, sleep=sleep),
        raising=False,
    )

    with pytest.raises(
        oracle_boot.BootProbeError,
        match="survived cleanup",
    ):
        oracle_boot._confirm_process_group_stopped(pgid)

    assert len(group_probes) >= 2
    assert all(
        sent_signal == 0
        and (
            (api == "killpg" and candidate == pgid)
            or (api == "kill" and candidate == -pgid)
        )
        for api, candidate, sent_signal in group_probes
    )
    assert 2 <= len(group_probes) < call_budget
    assert len(sleep_calls) < call_budget
    assert monotonic_observations


def test_probe_launcher_observes_exact_off_config_then_restores_mutation(
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
        mutate_config_to=b"launcher mutation\n",
    )
    run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert (tmp_path / "observed-config.bin").read_bytes() == ORIGINAL_CONFIG
    assert (tmp_path / "observed-config.mode").read_text(
        encoding="ascii"
    ) == oct(0o640)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


@pytest.mark.parametrize("initial_mode", ["passive", "replay"])
def test_probe_refuses_initial_non_off_config_before_launch_or_mutation(
    initial_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    non_off = ORIGINAL_CONFIG.replace(
        b"Mode=off", f"Mode={initial_mode}".encode()
    )
    layout.config.write_bytes(non_off)
    layout.config.chmod(0o604)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        exit_code=0,
    )
    popen_calls = 0

    def forbidden_popen(*_args, **_kwargs):
        nonlocal popen_calls
        popen_calls += 1
        raise AssertionError("non-off config must be refused before launch")

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        SimpleNamespace(Popen=forbidden_popen),
        raising=False,
    )

    raised_error: Exception | None = None
    result = None
    try:
        result = oracle_boot.run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised_error = exc
    else:
        assert result.success is False

    assert raised_error is not None or result is not None
    assert popen_calls == 0
    assert layout.config.read_bytes() == non_off
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o604


@pytest.mark.parametrize(
    "failure_stage",
    ["launch", "monitor", "evidence", "postflight", "probe_json"],
)
def test_probe_restores_exact_config_after_exception_at_every_stage(
    failure_stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    mutated = f"injected {failure_stage}\n".encode()
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated,
    )
    injection_reached = False

    class InjectedStageError(RuntimeError):
        pass

    def raise_after_mutation(*_args, **_kwargs):
        nonlocal injection_reached
        assert layout.config.read_bytes() == mutated
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o600
        injection_reached = True
        raise InjectedStageError(f"injected {failure_stage}")

    if failure_stage == "launch":
        def injected_launch(*_args, **_kwargs):
            nonlocal injection_reached
            layout.config.write_bytes(mutated)
            layout.config.chmod(0o600)
            injection_reached = True
            raise InjectedStageError("injected launch")

        popen = injected_launch
    elif failure_stage == "monitor":
        def mutate_before_monitor(*args, **kwargs):
            process = tracked_probe_popen.popen(*args, **kwargs)
            layout.config.write_bytes(mutated)
            layout.config.chmod(0o600)
            return process

        popen = mutate_before_monitor
    else:
        popen = tracked_probe_popen.popen

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        SimpleNamespace(
            Popen=popen,
            TimeoutExpired=subprocess.TimeoutExpired,
        ),
        raising=False,
    )

    if failure_stage == "monitor":
        monkeypatch.setattr(
            oracle_boot,
            "_wait_for_markers",
            raise_after_mutation,
            raising=False,
        )
    elif failure_stage == "evidence":
        monkeypatch.setattr(
            oracle_boot,
            "_collect_boot_evidence_retained",
            raise_after_mutation,
            raising=False,
        )
    elif failure_stage == "postflight":
        original_snapshot = oracle_boot._capture_boot_snapshot
        snapshot_calls = 0

        def fail_second_snapshot(*args, **kwargs):
            nonlocal snapshot_calls
            snapshot_calls += 1
            if snapshot_calls == 2:
                return raise_after_mutation(*args, **kwargs)
            return original_snapshot(*args, **kwargs)

        monkeypatch.setattr(
            oracle_boot,
            "_capture_boot_snapshot",
            fail_second_snapshot,
            raising=False,
        )
    elif failure_stage == "probe_json":
        def raise_after_restoration(*_args, **_kwargs):
            nonlocal injection_reached
            assert layout.config.read_bytes() == ORIGINAL_CONFIG
            assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
            injection_reached = True
            raise InjectedStageError("injected probe_json")

        monkeypatch.setattr(
            oracle_boot,
            "_write_probe_json",
            raise_after_restoration,
            raising=False,
        )

    raised_error: Exception | None = None
    result = None
    try:
        result = oracle_boot.run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised_error = exc
    else:
        assert result.success is False

    assert injection_reached
    if raised_error is not None:
        chain: list[BaseException] = []
        current: BaseException | None = raised_error
        while current is not None and current not in chain:
            chain.append(current)
            current = current.__cause__ or current.__context__
        assert any(
            isinstance(candidate, InjectedStageError)
            for candidate in chain
        ), chain
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    assert all(
        process.poll() is not None
        for process, _, _ in tracked_probe_popen.tracked
    )
    for _, _, pgid in tracked_probe_popen.tracked:
        with pytest.raises(ProcessLookupError):
            os.killpg(pgid, 0)


def test_probe_restore_failure_cannot_leave_canonical_success_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    mutated = b"successful probe mutation before restore\n"
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated,
    )
    original_restore = oracle_boot._restore_config_guard

    class InjectedRestoreError(RuntimeError):
        pass

    def restore_then_fail(guard):
        assert layout.config.read_bytes() == mutated
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o600
        original_restore(guard)
        assert layout.config.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
        raise InjectedRestoreError("injected failure after exact restore")

    monkeypatch.setattr(
        oracle_boot,
        "_restore_config_guard",
        restore_then_fail,
        raising=False,
    )

    with pytest.raises(
        InjectedRestoreError,
        match="injected failure after exact restore",
    ):
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    evidence_runs = tuple(
        path for path in layout.evidence.iterdir() if path.is_dir()
    )
    assert len(evidence_runs) == 1
    preserved = evidence_runs[0] / "nested/preloader_probe.log"
    assert preserved.read_text(encoding="utf-8") == "\n".join(
        REQUIRED_MARKERS
    )
    for probe in evidence_runs[0].rglob("probe.json"):
        payload = json.loads(probe.read_bytes())
        assert payload["success"] is False
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


def test_restore_config_guard_orders_retained_repair_before_public_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    config = tmp_path / "oracle.cfg"
    config.write_bytes(ORIGINAL_CONFIG)
    config.chmod(0o640)
    guard = oracle_boot._open_config_guard(config)
    events: list[str | tuple[str, int]] = []
    retained_reader = getattr(
        oracle_boot,
        "_read_retained_config_snapshot",
        None,
    )
    original_verify = oracle_boot._verify_current_config_path_identity

    if retained_reader is None:
        retained_reader = oracle_boot._read_config_snapshot

        def read_then_record(*args, **kwargs):
            events.append("retained-read")
            return retained_reader(*args, **kwargs)

        monkeypatch.setattr(
            oracle_boot,
            "_read_config_snapshot",
            read_then_record,
        )
    else:
        def read_then_record(*args, **kwargs):
            events.append("retained-read")
            return retained_reader(*args, **kwargs)

        monkeypatch.setattr(
            oracle_boot,
            "_read_retained_config_snapshot",
            read_then_record,
        )

    def fsync_then_record(descriptor: int) -> None:
        events.append(("fsync", descriptor))
        os.fsync(descriptor)

    def verify_then_record(current_guard) -> None:
        events.append("public-verify")
        original_verify(current_guard)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=fsync_then_record),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_verify_current_config_path_identity",
        verify_then_record,
        raising=False,
    )

    try:
        os.lseek(guard.fd, 0, os.SEEK_SET)
        os.ftruncate(guard.fd, 0)
        os.write(guard.fd, b"mutated retained config\n")
        os.fchmod(guard.fd, 0o600)

        oracle_boot._restore_config_guard(guard)

        assert events == [
            "retained-read",
            ("fsync", guard.fd),
            "retained-read",
            ("fsync", guard.parent.fd),
            "public-verify",
        ]
        assert config.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(config.stat().st_mode) == 0o640
    finally:
        guard.close()


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
        replacement = parent / config.name
        replacement_before = replacement.stat(follow_symlinks=False)
        replacement_metadata = (
            replacement_before.st_dev,
            replacement_before.st_ino,
            replacement_before.st_mode,
            replacement_before.st_size,
            replacement_before.st_mtime_ns,
            replacement_before.st_ctime_ns,
        )

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
        assert replacement.read_bytes() == replacement_payload
        replacement_after = replacement.stat(follow_symlinks=False)
        assert (
            replacement_after.st_dev,
            replacement_after.st_ino,
            replacement_after.st_mode,
            replacement_after.st_size,
            replacement_after.st_mtime_ns,
            replacement_after.st_ctime_ns,
        ) == replacement_metadata
    finally:
        guard.close()


@pytest.mark.parametrize(
    "cleanup_guard",
    [
        "launcher_guard",
        "retained_game_handle",
        "config_guard",
    ],
)
def test_probe_cleanup_close_failure_cannot_leave_success_json(
    cleanup_guard: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    layout.evidence.mkdir()
    evidence_sentinel = layout.evidence / "root.keep"
    evidence_sentinel.write_bytes(b"evidence root survives")
    outside_sentinel = tmp_path / "outside.keep"
    outside_sentinel.write_bytes(b"outside survives")
    _patch_healthy_preflight(monkeypatch, layout)
    mutated = f"{cleanup_guard} close mutation\n".encode()
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated,
    )
    original_collect = oracle_boot._collect_boot_evidence_retained
    original_retained_close = oracle_boot._RetainedBootEvidence.close
    retained_descriptors: list[int] = []
    retained_close_calls = 0
    stage_calls = 0

    class LaterRetainedCloseError(OSError):
        pass

    def capture_retained(*args, **kwargs):
        retained = original_collect(*args, **kwargs)
        retained_descriptors.extend(
            (
                retained.directory_handle.fd,
                *(item.descriptor for item in retained.files),
            )
        )
        return retained

    def close_retained_then_fail(retained) -> None:
        nonlocal retained_close_calls
        retained_close_calls += 1
        original_retained_close(retained)
        raise LaterRetainedCloseError(
            "later retained evidence close failure"
        )

    def forbidden_stage(*_args, **_kwargs):
        nonlocal stage_calls
        stage_calls += 1
        raise AssertionError(
            "probe JSON staged before guard cleanup completed"
        )

    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        capture_retained,
    )
    monkeypatch.setattr(
        oracle_boot._RetainedBootEvidence,
        "close",
        close_retained_then_fail,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_stage_probe_json",
        forbidden_stage,
    )
    close_injection = _inject_retained_cleanup_close_failure(
        monkeypatch,
        cleanup_guard,
    )

    with pytest.raises(
        _InjectedCleanupCloseError,
        match=close_injection.message,
    ) as raised:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )

    preserved_logs = tuple(
        layout.evidence.rglob("preloader_probe.log")
    )
    assert close_injection.target is not None
    assert close_injection.reached
    assert stage_calls == 0
    assert retained_close_calls == 1
    assert len(retained_descriptors) == 2
    _assert_acquired_descriptors_closed(retained_descriptors)
    assert any(
        "retained boot evidence close failed" in note
        and "later retained evidence close failure" in note
        for note in getattr(raised.value, "__notes__", ())
    )
    assert len(preserved_logs) == 1
    assert preserved_logs[0].read_text(encoding="utf-8") == "\n".join(
        REQUIRED_MARKERS
    )
    assert evidence_sentinel.read_bytes() == b"evidence root survives"
    assert outside_sentinel.read_bytes() == b"outside survives"
    _assert_no_canonical_probe_json(layout.evidence)
    assert not tuple(
        layout.evidence.rglob(".probe-json-*.pending")
    )
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


@pytest.mark.parametrize(
    "cleanup_guard",
    [
        "launcher_guard",
        "retained_game_handle",
        "config_guard",
    ],
)
def test_probe_preserves_primary_restore_error_over_cleanup_close_error(
    cleanup_guard: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    layout.evidence.mkdir()
    evidence_sentinel = layout.evidence / "root.keep"
    evidence_sentinel.write_bytes(b"evidence root survives")
    outside_sentinel = tmp_path / "outside.keep"
    outside_sentinel.write_bytes(b"outside survives")
    _patch_healthy_preflight(monkeypatch, layout)
    mutated = f"restore and {cleanup_guard} failure mutation\n".encode()
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated,
    )
    original_restore = oracle_boot._restore_config_guard
    restore_injection_reached = False

    def restore_then_fail(guard) -> None:
        nonlocal restore_injection_reached
        assert layout.config.read_bytes() == mutated
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o600
        original_restore(guard)
        assert layout.config.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
        if not restore_injection_reached:
            restore_injection_reached = True
            raise _InjectedPrimaryRestoreError(
                "injected primary restore failure"
            )

    monkeypatch.setattr(
        oracle_boot,
        "_restore_config_guard",
        restore_then_fail,
        raising=False,
    )
    close_injection = _inject_retained_cleanup_close_failure(
        monkeypatch,
        cleanup_guard,
    )

    raised: Exception | None = None
    try:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised = exc

    preserved_logs = tuple(
        layout.evidence.rglob("preloader_probe.log")
    )
    assert restore_injection_reached
    assert close_injection.target is not None
    assert close_injection.reached
    assert type(raised) is _InjectedPrimaryRestoreError
    assert str(raised) == "injected primary restore failure"
    assert len(preserved_logs) == 1
    assert preserved_logs[0].read_text(encoding="utf-8") == "\n".join(
        REQUIRED_MARKERS
    )
    assert evidence_sentinel.read_bytes() == b"evidence root survives"
    assert outside_sentinel.read_bytes() == b"outside survives"
    assert not tuple(layout.evidence.rglob("probe.json"))
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


@pytest.mark.parametrize("transfer_kind", ["move", "copy"])
def test_probe_evidence_source_open_is_nonblocking_before_fifo_substitution(
    transfer_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    mutated_config = f"{transfer_kind} evidence mutation\n".encode()
    if transfer_kind == "move":
        source = layout.game / "nested/preloader_probe.log"
        source_payload = "\n".join(REQUIRED_MARKERS).encode()
        changed_log = None
        changed_log_text = ""
    else:
        source = layout.game / "existing/preloader_changed.log"
        source.parent.mkdir()
        source.write_bytes(b"before probe")
        source_payload = b"changed during probe"
        changed_log = source
        changed_log_text = source_payload.decode()
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated_config,
        changed_log=changed_log,
        changed_log_text=changed_log_text,
    )
    displaced = tmp_path / f"displaced-{transfer_kind}.log"
    outside = tmp_path / f"outside-{transfer_kind}.keep"
    outside.write_bytes(b"outside survives")
    original_open = os.open
    original_renameatx = oracle_boot._renameatx
    transfer_name = (
        "_move_regular_exclusive"
        if transfer_kind == "move"
        else "_copy_regular_exclusive"
    )
    original_transfer = getattr(oracle_boot, transfer_name)
    injection_reached = False
    open_guard_active = False
    matching_reopen_flags: list[int] = []
    missing_nonblock = False
    target_rename_calls = 0
    evidence_before_transfer: tuple[tuple[str, str, bytes], ...] | None = None

    class MissingNonblockingSourceOpen(AssertionError):
        pass

    def source_parent_matches(dir_fd: int | None) -> bool:
        if dir_fd is None or not source.parent.exists():
            return False
        retained = os.fstat(dir_fd)
        named = source.parent.stat(follow_symlinks=False)
        return (retained.st_dev, retained.st_ino) == (
            named.st_dev,
            named.st_ino,
        )

    def guarded_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal missing_nonblock
        if (
            open_guard_active
            and path == source.name
            and source_parent_matches(dir_fd)
        ):
            matching_reopen_flags.append(flags)
            if flags & os.O_NONBLOCK == 0:
                missing_nonblock = True
                raise MissingNonblockingSourceOpen(
                    f"{transfer_kind} evidence source open omitted "
                    "O_NONBLOCK after FIFO substitution"
                )
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def inject_fifo_at_transfer(entry, *args, **kwargs):
        nonlocal injection_reached
        nonlocal open_guard_active
        nonlocal evidence_before_transfer
        assert not injection_reached
        assert entry.path == source.resolve()
        assert entry.name == source.name
        assert entry.file_type == "regular"
        current = source.stat(follow_symlinks=False)
        assert (
            current.st_dev,
            current.st_ino,
            current.st_mode,
            current.st_size,
            current.st_mtime_ns,
        ) == (
            entry.observed.st_dev,
            entry.observed.st_ino,
            entry.observed.st_mode,
            entry.observed.st_size,
            entry.observed.st_mtime_ns,
        )
        evidence_before_transfer = _test_tree_snapshot(layout.evidence)
        source.rename(displaced)
        os.mkfifo(source, 0o600)
        injection_reached = True
        open_guard_active = True
        try:
            return original_transfer(entry, *args, **kwargs)
        finally:
            open_guard_active = False

    def tracked_renameatx(*args, **kwargs):
        nonlocal target_rename_calls
        if (
            len(args) >= 2
            and args[1] == source.name
            and source_parent_matches(args[0].fd)
        ):
            target_rename_calls += 1
        return original_renameatx(*args, **kwargs)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, open=guarded_open),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        transfer_name,
        inject_fifo_at_transfer,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        tracked_renameatx,
        raising=False,
    )

    raised: Exception | None = None
    started = time.monotonic()
    try:
        run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised = exc
    elapsed = time.monotonic() - started

    assert raised is not None
    assert injection_reached
    assert elapsed < 1.0
    assert target_rename_calls == 0
    assert outside.read_bytes() == b"outside survives"
    assert stat.S_ISFIFO(source.stat(follow_symlinks=False).st_mode)
    assert displaced.read_bytes() == source_payload
    assert evidence_before_transfer is not None
    assert _test_tree_snapshot(layout.evidence) == evidence_before_transfer
    _assert_no_canonical_probe_json(layout.evidence)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)
    if missing_nonblock:
        assert isinstance(raised, MissingNonblockingSourceOpen)
        pytest.fail(str(raised))

    assert all(
        flags & os.O_NONBLOCK for flags in matching_reopen_flags
    )
    assert isinstance(raised, oracle_boot.BootProbeError)
    assert "substitut" in str(raised).lower()


@pytest.mark.parametrize("mutation", ["changed", "removed"])
def test_probe_rejects_new_log_inventory_change_after_shutdown_snapshot(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    mutated_config = f"post-snapshot {mutation}\n".encode()
    initial_payload = "\n".join(REQUIRED_MARKERS).encode()
    changed_payload = initial_payload + b"\nchanged after shutdown snapshot\n"
    launcher = _launcher(
        tmp_path,
        log_text=initial_payload.decode(),
        observed_config=layout.config,
        mutate_config_to=mutated_config,
    )
    source = layout.game / "nested/preloader_probe.log"
    displaced = tmp_path / "removed-after-snapshot.log"
    original_verify = oracle_boot._verify_pinned_directory_path
    injection_reached = False

    def inject_after_log_snapshot(path, pinned, label, *args, **kwargs):
        nonlocal injection_reached
        result = original_verify(path, pinned, label, *args, **kwargs)
        if label == "game root after log snapshot":
            assert not injection_reached
            assert source.read_bytes() == initial_payload
            injection_reached = True
            if mutation == "changed":
                source.write_bytes(changed_payload)
            else:
                source.rename(displaced)
        return result

    monkeypatch.setattr(
        oracle_boot,
        "_verify_pinned_directory_path",
        inject_after_log_snapshot,
        raising=False,
    )

    raised: Exception | None = None
    result = None
    started = time.monotonic()
    try:
        result = run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised = exc
    elapsed = time.monotonic() - started

    assert injection_reached
    assert elapsed < 3.0
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)
    if mutation == "changed":
        preserved_payloads: list[bytes] = []
        if source.is_file():
            preserved_payloads.append(source.read_bytes())
        if layout.evidence.exists():
            preserved_payloads.extend(
                path.read_bytes()
                for path in layout.evidence.rglob(source.name)
                if path.is_file() and not path.is_symlink()
            )
        assert changed_payload in preserved_payloads
    else:
        assert not source.exists()
        assert displaced.read_bytes() == initial_payload

    if raised is not None:
        detail = str(raised).lower()
        assert any(
            word in detail
            for word in (
                mutation,
                "inventory",
                "mismatch",
                "snapshot",
            )
        )
        _assert_no_canonical_probe_json(layout.evidence)
        return

    assert result is not None
    assert result.success is False
    assert any(
        mutation in issue.lower() and str(source) in issue
        for issue in result.issues
    )
    _assert_no_canonical_probe_json(result.evidence_dir)


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


@pytest.mark.xfail(
    strict=False,
    reason=(
        "active final-syscall path replacement is outside the "
        "approved practical threat model"
    ),
)
def test_probe_rejects_evidence_directory_substitution_at_final_json_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    mutated_config = b"evidence directory substitution\n"
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated_config,
    )
    original_write = oracle_boot._write_probe_json
    injection_reached = False
    original_evidence_dir: Path | None = None
    displaced: Path | None = None
    sentinel: Path | None = None

    def substitute_then_write(
        evidence_dir: Path,
        payload: dict[str, object],
        *args,
        **kwargs,
    ):
        nonlocal injection_reached, original_evidence_dir, displaced, sentinel
        assert not injection_reached
        injection_reached = True
        original_evidence_dir = evidence_dir
        displaced = evidence_dir.with_name(f"{evidence_dir.name}-displaced")
        evidence_dir.rename(displaced)
        evidence_dir.mkdir(mode=0o700)
        sentinel = evidence_dir / "replacement.keep"
        sentinel.write_bytes(b"replacement survives")
        return original_write(
            evidence_dir,
            payload,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        oracle_boot,
        "_write_probe_json",
        substitute_then_write,
        raising=False,
    )

    raised: Exception | None = None
    result = None
    try:
        result = run_boot_probe(
            layout.game,
            launcher,
            layout.config,
            layout.evidence,
            2,
        )
    except Exception as exc:
        raised = exc

    assert injection_reached
    assert original_evidence_dir is not None
    assert displaced is not None
    assert sentinel is not None
    preserved_log = displaced / "nested/preloader_probe.log"
    assert preserved_log.read_text(encoding="utf-8") == "\n".join(
        REQUIRED_MARKERS
    )
    assert sentinel.read_bytes() == b"replacement survives"
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)
    assert raised is not None, (
        "evidence directory identity substitution was accepted",
        result,
    )
    detail = str(raised).lower()
    assert "identity" in detail or "substitut" in detail
    assert result is None
    _assert_no_canonical_probe_json(displaced, original_evidence_dir)


def test_probe_orders_cleanup_evidence_verification_and_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    mutated_config = b"mutated before ordered cleanup\n"
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        observed_config=layout.config,
        mutate_config_to=mutated_config,
    )
    events: list[str] = []
    targets = SimpleNamespace(
        config=None,
        launcher=None,
        game=None,
        retained=None,
    )
    original_open_config = oracle_boot._open_config_guard
    original_open_launcher = oracle_boot._open_launcher_guard
    original_verify_path = oracle_boot._verify_pinned_directory_path
    original_restore = oracle_boot._restore_config_guard
    original_launcher_close = oracle_boot._LauncherGuard.close
    original_directory_close = oracle_boot._DirectoryHandle.close
    original_config_close = oracle_boot._ConfigGuard.close
    original_collect = oracle_boot._collect_boot_evidence_retained
    original_verify_evidence = (
        oracle_boot._verify_and_sync_retained_evidence
    )
    original_stage = oracle_boot._stage_probe_json
    original_retained_close = oracle_boot._RetainedBootEvidence.close
    original_write = oracle_boot._write_probe_json

    def capture_config(path):
        guard = original_open_config(path)
        assert targets.config is None
        targets.config = guard
        return guard

    def capture_launcher(path):
        guard = original_open_launcher(path)
        assert targets.launcher is None
        targets.launcher = guard
        return guard

    def capture_game(path, pinned, label) -> None:
        if label == "game root at launch":
            assert targets.game is None or targets.game is pinned
            targets.game = pinned
        original_verify_path(path, pinned, label)

    def restore_config(guard) -> None:
        assert guard is targets.config
        assert layout.config.read_bytes() == mutated_config
        original_restore(guard)
        assert layout.config.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
        events.append("config-restored")

    def close_launcher(guard) -> None:
        is_target = guard is targets.launcher
        original_launcher_close(guard)
        if is_target:
            events.append("launcher-guard-closed")

    def close_directory(handle) -> None:
        is_target = handle is targets.game
        original_directory_close(handle)
        if is_target:
            events.append("game-root-handle-closed")

    def close_config(guard) -> None:
        is_target = guard is targets.config
        original_config_close(guard)
        if is_target:
            events.append("config-guard-closed")

    def collect_retained(*args, **kwargs):
        retained = original_collect(*args, **kwargs)
        assert targets.retained is None
        targets.retained = retained
        return retained

    def verify_evidence(retained) -> None:
        assert retained is targets.retained
        original_verify_evidence(retained)
        events.append("retained-evidence-verified")

    def stage_json(evidence_dir, payload, *args, **kwargs):
        assert targets.retained is not None
        assert (
            kwargs.get("_directory_handle")
            is targets.retained.directory_handle
        )
        staged = original_stage(
            evidence_dir,
            payload,
            *args,
            **kwargs,
        )
        events.append("probe-json-staged")
        return staged

    def close_retained(retained) -> None:
        assert retained is targets.retained
        original_retained_close(retained)
        events.append("retained-evidence-closed")

    def write_json(*args, **kwargs) -> None:
        original_write(*args, **kwargs)
        events.append("probe-json-committed")

    monkeypatch.setattr(
        oracle_boot,
        "_open_config_guard",
        capture_config,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_open_launcher_guard",
        capture_launcher,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_verify_pinned_directory_path",
        capture_game,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_restore_config_guard",
        restore_config,
    )
    monkeypatch.setattr(
        oracle_boot._LauncherGuard,
        "close",
        close_launcher,
    )
    monkeypatch.setattr(
        oracle_boot._DirectoryHandle,
        "close",
        close_directory,
    )
    monkeypatch.setattr(
        oracle_boot._ConfigGuard,
        "close",
        close_config,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_collect_boot_evidence_retained",
        collect_retained,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_verify_and_sync_retained_evidence",
        verify_evidence,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_stage_probe_json",
        stage_json,
    )
    monkeypatch.setattr(
        oracle_boot._RetainedBootEvidence,
        "close",
        close_retained,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_write_probe_json",
        write_json,
    )

    result = run_boot_probe(
        layout.game,
        launcher,
        layout.config,
        layout.evidence,
        2,
    )

    assert result.success is True
    assert events == [
        "config-restored",
        "launcher-guard-closed",
        "game-root-handle-closed",
        "config-guard-closed",
        "retained-evidence-verified",
        "probe-json-staged",
        "retained-evidence-closed",
        "probe-json-committed",
    ]
    assert targets.config is not None
    assert targets.launcher is not None
    assert targets.game is not None
    assert targets.retained is not None
    assert (result.evidence_dir / "probe.json").is_file()
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    _assert_tracked_probe_groups_stopped(tracked_probe_popen)


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


def test_collect_moves_only_new_regular_logs(tmp_path: Path):
    game = tmp_path / "game"
    game.mkdir()
    old = game / "preloader_old.log"
    old.write_text("keep", encoding="utf-8")
    before = fingerprint_preloader_logs(game)

    nested = game / "logs" / "z"
    nested.mkdir(parents=True)
    new = nested / "preloader_new.log"
    new.write_text("\n".join(REQUIRED_MARKERS), encoding="utf-8")

    result = collect_boot_evidence(before, game, tmp_path / "evidence")

    assert old.read_text(encoding="utf-8") == "keep"
    assert not new.exists()
    assert [path.name for path in result.moved_logs] == ["preloader_new.log"]
    assert result.moved_logs[0].read_text(encoding="utf-8") == "\n".join(
        REQUIRED_MARKERS
    )
    assert result.copied_logs == ()
    assert result.issues == ()


def test_collect_leaves_changed_preexisting_log_and_copies_evidence(
    tmp_path: Path,
):
    game = tmp_path / "game"
    game.mkdir()
    existing = game / "preloader_existing.log"
    existing.write_bytes(b"before")
    before = fingerprint_preloader_logs(game)

    existing.write_bytes(b"after launch")
    result = collect_boot_evidence(before, game, tmp_path / "evidence")

    assert existing.read_bytes() == b"after launch"
    assert result.moved_logs == ()
    assert len(result.copied_logs) == 1
    assert result.copied_logs[0].read_bytes() == b"after launch"
    assert result.copied_logs[0].resolve().is_relative_to(
        result.evidence_dir.resolve()
    )
    assert any(
        "pre-existing" in issue and "changed" in issue
        for issue in result.issues
    )


def test_collect_rejects_new_symlink_log(tmp_path: Path):
    game = tmp_path / "game"
    game.mkdir()
    outside = tmp_path / "outside.log"
    outside.write_bytes(b"must remain outside")
    before = fingerprint_preloader_logs(game)

    link = game / "preloader_escape.log"
    link.symlink_to(outside)
    result = collect_boot_evidence(before, game, tmp_path / "evidence")

    assert link.is_symlink()
    assert outside.read_bytes() == b"must remain outside"
    assert result.moved_logs == ()
    assert result.copied_logs == ()
    assert any(
        "symlink" in issue and "preloader_escape.log" in issue
        for issue in result.issues
    )


def test_probe_requires_all_three_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS[:2]),
        linger_seconds=60,
    )

    result = run_boot_probe(
        layout.game, launcher, layout.config, layout.evidence, 2
    )

    assert result.success is False
    assert result.markers == REQUIRED_MARKERS[:2]
    assert any(
        REQUIRED_MARKERS[2] in issue and "missing" in issue.lower()
        for issue in result.issues
    )
    assert result.evidence_dir.is_dir()
    assert layout.config.read_bytes() == ORIGINAL_CONFIG


def test_probe_terminates_only_spawned_process_and_resets_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
        linger_seconds=60,
    )
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=True,
    )
    try:
        result = run_boot_probe(
            layout.game, launcher, layout.config, layout.evidence, 5
        )
        spawned_pid = int(
            (layout.game / "spawned.pid").read_text(encoding="ascii")
        )

        assert result.success is True
        assert _wait_for_pid_exit(spawned_pid)
        assert unrelated.poll() is None
        assert layout.config.read_bytes() == ORIGINAL_CONFIG
        assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=3)


def test_probe_timeout_is_failure_with_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tracked_probe_popen,
):
    layout = _probe_layout(tmp_path)
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text=REQUIRED_MARKERS[0],
        linger_seconds=60,
    )

    result = run_boot_probe(
        layout.game, launcher, layout.config, layout.evidence, 1
    )

    spawned_pid = int((layout.game / "spawned.pid").read_text(encoding="ascii"))
    assert result.success is False
    assert result.evidence_dir.is_dir()
    assert result.moved_logs
    assert any("timeout" in issue.lower() for issue in result.issues)
    assert result.exit_code is None
    assert _wait_for_pid_exit(spawned_pid)
    assert layout.config.read_bytes() == ORIGINAL_CONFIG
    assert stat.S_IMODE(layout.config.stat().st_mode) == 0o640


_INVALID_PROBE_REQUESTS = (
    "game_missing",
    "game_file",
    "game_symlink",
    "game_symlink_parent",
    "launcher_missing",
    "launcher_directory",
    "launcher_symlink",
    "launcher_non_executable",
    "launcher_symlink_parent",
    "config_missing",
    "config_directory",
    "config_symlink",
    "config_symlink_parent",
    "evidence_file",
    "evidence_symlink",
    "evidence_symlink_parent",
    "timeout_zero",
    "timeout_negative",
    "timeout_true",
    "timeout_false",
    "timeout_float",
    "timeout_string",
)


@pytest.mark.parametrize("case", _INVALID_PROBE_REQUESTS)
def test_probe_rejects_invalid_requests_before_any_side_effect(
    case: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    game_root: object = layout.game
    launcher_path: object = launcher
    config_path: object = layout.config
    evidence_root: object = layout.evidence
    timeout: object = 120
    semantic = case.split("_", 1)[0]
    requested_path: Path | None = None

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.bin").write_bytes(b"outside sentinel")
    protected = tmp_path / "protected"
    protected.mkdir()
    (protected / "keep.bin").write_bytes(b"protected sentinel")

    if case == "game_missing":
        game_root = requested_path = tmp_path / "missing-game"
    elif case == "game_file":
        requested_path = tmp_path / "game-file"
        requested_path.write_bytes(b"not a directory")
        game_root = requested_path
    elif case == "game_symlink":
        requested_path = tmp_path / "game-link"
        requested_path.symlink_to(layout.game, target_is_directory=True)
        game_root = requested_path
    elif case == "game_symlink_parent":
        real_parent = outside / "game-parent"
        real_parent.mkdir()
        (real_parent / "game").mkdir()
        linked_parent = tmp_path / "linked-game-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        requested_path = linked_parent / "game"
        game_root = requested_path
    elif case == "launcher_missing":
        launcher_path = requested_path = tmp_path / "missing-launcher"
    elif case == "launcher_directory":
        requested_path = tmp_path / "launcher-directory"
        requested_path.mkdir()
        launcher_path = requested_path
    elif case == "launcher_symlink":
        requested_path = tmp_path / "launcher-link"
        requested_path.symlink_to(launcher)
        launcher_path = requested_path
    elif case == "launcher_non_executable":
        launcher.chmod(0o644)
        launcher_path = requested_path = launcher
    elif case == "launcher_symlink_parent":
        real_parent = outside / "launcher-parent"
        real_parent.mkdir()
        real_launcher = _write_executable(
            real_parent / "launcher.py",
            "raise SystemExit(0)\n",
        )
        linked_parent = tmp_path / "linked-launcher-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        requested_path = linked_parent / real_launcher.name
        launcher_path = requested_path
    elif case == "config_missing":
        config_path = requested_path = tmp_path / "missing-config"
    elif case == "config_directory":
        requested_path = tmp_path / "config-directory"
        requested_path.mkdir()
        config_path = requested_path
    elif case == "config_symlink":
        requested_path = tmp_path / "config-link"
        requested_path.symlink_to(layout.config)
        config_path = requested_path
    elif case == "config_symlink_parent":
        real_parent = outside / "config-parent"
        real_parent.mkdir()
        (real_parent / "oracle.cfg").write_bytes(ORIGINAL_CONFIG)
        linked_parent = tmp_path / "linked-config-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        requested_path = linked_parent / "oracle.cfg"
        config_path = requested_path
    elif case == "evidence_file":
        requested_path = tmp_path / "evidence-file"
        requested_path.write_bytes(b"not a directory")
        evidence_root = requested_path
    elif case == "evidence_symlink":
        requested_path = tmp_path / "evidence-link"
        requested_path.symlink_to(protected, target_is_directory=True)
        evidence_root = requested_path
    elif case == "evidence_symlink_parent":
        linked_parent = tmp_path / "linked-evidence-parent"
        linked_parent.symlink_to(outside, target_is_directory=True)
        requested_path = linked_parent / "evidence"
        evidence_root = requested_path
    elif case == "timeout_zero":
        timeout = 0
    elif case == "timeout_negative":
        timeout = -1
    elif case == "timeout_true":
        timeout = True
    elif case == "timeout_false":
        timeout = False
    elif case == "timeout_float":
        timeout = 1.5
    elif case == "timeout_string":
        timeout = "120"
    else:
        raise AssertionError(case)

    def forbidden(*_args, **_kwargs):
        raise AssertionError(f"{case} reached a side-effect boundary")

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot, "_capture_boot_snapshot", forbidden, raising=False
    )
    monkeypatch.setattr(
        oracle_boot, "collect_boot_evidence", forbidden, raising=False
    )
    monkeypatch.setattr(
        oracle_boot, "_write_probe_json", forbidden, raising=False
    )
    before = _test_tree_snapshot(tmp_path)
    config_before = layout.config.read_bytes()
    config_mode_before = stat.S_IMODE(layout.config.stat().st_mode)

    with pytest.raises((RuntimeError, ValueError, OSError)) as raised:
        run_boot_probe(
            game_root,
            launcher_path,
            config_path,
            evidence_root,
            timeout,
        )

    message = str(raised.value).lower()
    assert semantic in message
    if requested_path is not None:
        assert str(requested_path) in str(raised.value)
    assert layout.config.read_bytes() == config_before
    assert stat.S_IMODE(layout.config.stat().st_mode) == config_mode_before
    assert _test_tree_snapshot(tmp_path) == before


def _complete_boot_probe_result(
    tmp_path: Path,
    *,
    success: bool,
):
    evidence_dir = (tmp_path / "evidence/run").resolve()
    moved = (evidence_dir / "nested/preloader_new.log").resolve()
    copied = (evidence_dir / "existing/preloader_changed.log").resolve()
    issues = () if success else ("missing required boot marker",)
    markers = REQUIRED_MARKERS if success else REQUIRED_MARKERS[:2]
    return oracle_boot.BootProbeResult(
        success=success,
        evidence_dir=evidence_dir,
        moved_logs=(moved,),
        copied_logs=(copied,),
        markers=markers,
        issues=issues,
        exit_code=None,
    )


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


@pytest.mark.parametrize(
    ("semantic", "symlink_position"),
    [
        ("game", "leaf"),
        ("game", "parent"),
        ("launcher", "leaf"),
        ("launcher", "parent"),
        ("config", "leaf"),
        ("config", "parent"),
        ("evidence", "leaf"),
        ("evidence", "parent"),
    ],
)
def test_boot_main_rejects_supplied_symlink_paths_before_probe_side_effects(
    semantic: str,
    symlink_position: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    layout = _probe_layout(tmp_path)
    layout.evidence.mkdir()
    _patch_healthy_preflight(monkeypatch, layout)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    targets = {
        "game": layout.game,
        "launcher": launcher,
        "config": layout.config,
        "evidence": layout.evidence,
    }
    target = targets[semantic]
    if symlink_position == "leaf":
        requested = tmp_path / f"{semantic}-leaf-link"
        requested.symlink_to(
            target,
            target_is_directory=target.is_dir(),
        )
    else:
        linked_parent = tmp_path / f"{semantic}-parent-link"
        linked_parent.symlink_to(
            target.parent,
            target_is_directory=True,
        )
        requested = linked_parent / target.name

    supplied = dict(targets)
    supplied[semantic] = requested
    launch_calls = 0

    def forbidden_popen(*_args, **_kwargs):
        nonlocal launch_calls
        launch_calls += 1
        raise RuntimeError("symlink input reached launch boundary")

    monkeypatch.setattr(
        oracle_boot,
        "subprocess",
        _ModuleProxy(subprocess, Popen=forbidden_popen),
        raising=False,
    )
    before = _test_tree_snapshot(tmp_path)
    config_before = layout.config.read_bytes()
    config_mode_before = stat.S_IMODE(layout.config.stat().st_mode)

    exit_code = oracle_boot.main(
        [
            "--game-root",
            str(supplied["game"]),
            "--launcher",
            str(supplied["launcher"]),
            "--config",
            str(supplied["config"]),
            "--evidence-root",
            str(supplied["evidence"]),
            "--timeout",
            "2",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err.startswith("error: ")
    assert semantic in captured.err.lower()
    assert str(requested) in captured.err
    assert launch_calls == 0
    assert layout.config.read_bytes() == config_before
    assert stat.S_IMODE(layout.config.stat().st_mode) == config_mode_before
    assert _test_tree_snapshot(tmp_path) == before


@pytest.mark.parametrize("success", [True, False])
@pytest.mark.parametrize(
    ("timeout_args", "expected_timeout"),
    [
        ((), 120),
        (("--timeout", "37"), 37),
    ],
)
def test_boot_main_emits_canonical_public_json_and_exact_exit_code(
    success: bool,
    timeout_args: tuple[str, ...],
    expected_timeout: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )
    result = _complete_boot_probe_result(tmp_path, success=success)
    calls: list[tuple[Path, Path, Path, Path, int]] = []

    def fake_probe(
        game_root: Path,
        launcher_path: Path,
        config_path: Path,
        evidence_root: Path,
        timeout: int,
    ):
        calls.append(
            (
                game_root,
                launcher_path,
                config_path,
                evidence_root,
                timeout,
            )
        )
        return result

    monkeypatch.setattr(
        oracle_boot, "run_boot_probe", fake_probe, raising=False
    )
    argv = [
        "--game-root",
        str(layout.game),
        "--launcher",
        str(launcher),
        "--config",
        str(layout.config),
        "--evidence-root",
        str(layout.evidence),
        *timeout_args,
    ]

    exit_code = oracle_boot.main(argv)

    assert exit_code == (0 if success else 1)
    assert calls == [
        (
            layout.game.resolve(),
            launcher.resolve(),
            layout.config.resolve(),
            layout.evidence.resolve(),
            expected_timeout,
        )
    ]
    expected_evidence_dir = (tmp_path / "evidence/run").resolve()
    expected_moved = (
        expected_evidence_dir / "nested/preloader_new.log"
    ).resolve()
    expected_copied = (
        expected_evidence_dir / "existing/preloader_changed.log"
    ).resolve()
    payload = {
        "success": success,
        "evidence_dir": str(expected_evidence_dir),
        "moved_logs": [str(expected_moved)],
        "copied_logs": [str(expected_copied)],
        "markers": list(
            REQUIRED_MARKERS if success else REQUIRED_MARKERS[:2]
        ),
        "issues": [] if success else ["missing required boot marker"],
        "exit_code": None,
    }
    expected_stdout = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    captured = capsys.readouterr()
    assert captured.out == expected_stdout
    assert captured.err == ""


@pytest.mark.parametrize(
    ("error_type", "message"),
    [
        (ValueError, "invalid timeout"),
        (RuntimeError, "monitoring failed"),
        (OSError, "evidence write failed"),
    ],
)
def test_boot_main_reports_probe_errors_on_stderr_only(
    error_type: type[Exception],
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    layout = _probe_layout(tmp_path)
    launcher = _launcher(
        tmp_path,
        log_text="\n".join(REQUIRED_MARKERS),
    )

    def fail_probe(*_args, **_kwargs):
        raise error_type(message)

    monkeypatch.setattr(
        oracle_boot, "run_boot_probe", fail_probe, raising=False
    )

    exit_code = oracle_boot.main(
        [
            "--game-root",
            str(layout.game),
            "--launcher",
            str(launcher),
            "--config",
            str(layout.config),
            "--evidence-root",
            str(layout.evidence),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == f"error: {message}\n"


@pytest.mark.parametrize(
    "argv",
    [
        (
            "--launcher",
            "/tmp/launcher",
            "--config",
            "/tmp/config",
            "--evidence-root",
            "/tmp/evidence",
        ),
        (
            "--game-root",
            "/tmp/game",
            "--config",
            "/tmp/config",
            "--evidence-root",
            "/tmp/evidence",
        ),
        (
            "--game-root",
            "/tmp/game",
            "--launcher",
            "/tmp/launcher",
            "--evidence-root",
            "/tmp/evidence",
        ),
        (
            "--game-root",
            "/tmp/game",
            "--launcher",
            "/tmp/launcher",
            "--config",
            "/tmp/config",
        ),
        (
            "--game-root",
            "/tmp/game",
            "--launcher",
            "/tmp/launcher",
            "--config",
            "/tmp/config",
            "--evidence-root",
            "/tmp/evidence",
            "--timeout",
            "not-an-integer",
        ),
        (
            "--game-root",
            "/tmp/game",
            "--launcher",
            "/tmp/launcher",
            "--config",
            "/tmp/config",
            "--evidence-root",
            "/tmp/evidence",
            "--unknown",
        ),
    ],
)
def test_boot_main_argparse_errors_exit_two_without_running_probe(
    argv: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls = 0

    def forbidden_probe(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("argparse error reached run_boot_probe")

    monkeypatch.setattr(
        oracle_boot, "run_boot_probe", forbidden_probe, raising=False
    )

    with pytest.raises(SystemExit) as raised:
        oracle_boot.main(list(argv))

    captured = capsys.readouterr()
    assert raised.value.code == 2
    assert calls == 0
    assert captured.out == ""
    assert "usage:" in captured.err.lower()


def test_oracle_boot_probe_wrapper_help_executes_from_repo_root():
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = repo_root / "tools/oracle_boot_probe.py"

    completed = subprocess.run(
        [sys.executable, str(wrapper), "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    for flag in (
        "--game-root",
        "--launcher",
        "--config",
        "--evidence-root",
        "--timeout",
    ):
        assert flag in completed.stdout


class _VirtualCleanupClock:
    def __init__(self, start: float = 100.0, call_budget: int = 64):
        self.now = start
        self.start = start
        self.call_budget = call_budget
        self.monotonic_calls = 0
        self.sleep_calls: list[float] = []

    def monotonic(self) -> float:
        self.monotonic_calls += 1
        if self.monotonic_calls > self.call_budget:
            raise AssertionError("virtual monotonic call budget exceeded")
        return self.now

    def sleep(self, seconds: float) -> None:
        if len(self.sleep_calls) >= self.call_budget:
            raise AssertionError("virtual sleep call budget exceeded")
        assert seconds > 0
        self.sleep_calls.append(seconds)
        self.now += seconds


class _ExitedCleanupProcess:
    def __init__(self, pid: int, returncode: int = 23):
        self.pid = pid
        self.returncode = returncode
        self.wait_timeouts: list[float | None] = []

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.wait_timeouts.append(timeout)
        return self.returncode


def test_stop_spawned_process_group_retries_transient_permission_error_before_exact_cleanup(
    monkeypatch: pytest.MonkeyPatch,
):
    pgid = 424242
    clock = _VirtualCleanupClock()
    process = _ExitedCleanupProcess(pgid)
    events: list[tuple[str, int, int, float]] = []
    first_zero_probe = True
    clean_zero_verified = False
    clean_zero_verification_index: int | None = None
    post_term_absence_indices: list[int] = []
    term_sent = False

    def group_signal(api: str, target: int, sent_signal: int) -> None:
        nonlocal first_zero_probe
        nonlocal clean_zero_verified
        nonlocal clean_zero_verification_index
        nonlocal term_sent
        events.append((api, target, sent_signal, clock.now))
        event_index = len(events) - 1
        if sent_signal == 0:
            if first_zero_probe:
                first_zero_probe = False
                raise PermissionError("transient signal-zero denial")
            if term_sent:
                post_term_absence_indices.append(event_index)
                raise ProcessLookupError
            clean_zero_verified = True
            clean_zero_verification_index = event_index
            return
        if sent_signal != signal.SIGTERM:
            raise AssertionError("unexpected non-TERM process-group signal")
        assert clean_zero_verified, "TERM preceded a clean zero verification"
        assert not term_sent, "sent TERM more than once while group existed"
        term_sent = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            killpg=lambda target, sent_signal: group_signal(
                "killpg", target, sent_signal
            ),
            kill=lambda target, sent_signal: group_signal(
                "kill", target, sent_signal
            ),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "time",
        _ModuleProxy(
            time,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_PROCESS_GROUP_EXIT_CONFIRM_SECONDS",
        0.03,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_PROCESS_POLL_SECONDS",
        0.01,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_TERMINATION_GRACE_SECONDS",
        0.02,
        raising=False,
    )

    raised: BaseException | None = None
    result: int | None = None
    try:
        result = oracle_boot._stop_spawned_process_group(process, pgid)
    except BaseException as exc:
        raised = exc

    assert raised is None, (
        "transient signal-zero PermissionError escaped instead of retrying",
        raised,
    )
    assert result == process.returncode
    zero_events = [event for event in events if event[2] == 0]
    assert len(zero_events) >= 2
    nonzero_events = [event for event in events if event[2] != 0]
    assert len(nonzero_events) == 1
    api, target, sent_signal, _ = nonzero_events[0]
    assert sent_signal == signal.SIGTERM
    assert clean_zero_verified
    assert term_sent
    assert clean_zero_verification_index is not None
    term_index = events.index(nonzero_events[0])
    assert clean_zero_verification_index < term_index
    assert post_term_absence_indices
    assert all(index > term_index for index in post_term_absence_indices)
    assert (api, target) in {("killpg", pgid), ("kill", -pgid)}
    assert all(
        (api == "killpg" and target == pgid)
        or (api == "kill" and target == -pgid)
        for api, target, _, _ in events
    )
    assert all(
        timeout is not None
        and 0 <= timeout <= oracle_boot._TERMINATION_GRACE_SECONDS
        for timeout in process.wait_timeouts
    )
    assert clock.sleep_calls


def test_stop_spawned_process_group_bounds_persistent_permission_error_without_signaling_unverified_group(
    monkeypatch: pytest.MonkeyPatch,
):
    pgid = 424242
    clock = _VirtualCleanupClock(call_budget=256)
    process = _ExitedCleanupProcess(pgid)
    events: list[tuple[str, int, int, float]] = []

    def deny_group_signal(
        api: str,
        target: int,
        sent_signal: int,
    ) -> None:
        if len(events) >= clock.call_budget:
            raise AssertionError("signal call budget exceeded")
        events.append((api, target, sent_signal, clock.now))
        if sent_signal != 0:
            raise AssertionError(
                "sent a nonzero signal to an unverified process group"
            )
        raise PermissionError("persistent signal-zero denial")

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            killpg=lambda target, sent_signal: deny_group_signal(
                "killpg", target, sent_signal
            ),
            kill=lambda target, sent_signal: deny_group_signal(
                "kill", target, sent_signal
            ),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "time",
        _ModuleProxy(
            time,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        ),
        raising=False,
    )
    raised: BaseException | None = None
    try:
        oracle_boot._stop_spawned_process_group(process, pgid)
    except BaseException as exc:
        raised = exc

    assert isinstance(raised, oracle_boot.BootProbeError), raised
    assert not isinstance(raised, AssertionError)
    assert events
    assert all(sent_signal == 0 for _, _, sent_signal, _ in events)
    assert all(
        (api == "killpg" and target == pgid)
        or (api == "kill" and target == -pgid)
        for api, target, _, _ in events
    )
    assert 2 <= len(events) < clock.call_budget
    assert len(clock.sleep_calls) < clock.call_budget
    assert all(
        timeout is not None
        and 0 <= timeout <= oracle_boot._TERMINATION_GRACE_SECONDS
        for timeout in process.wait_timeouts
    )


@pytest.mark.xfail(
    strict=False,
    reason=(
        "active final-syscall path replacement is outside the "
        "approved practical threat model"
    ),
)
def test_write_probe_json_rejects_pending_name_substitution_and_preserves_both_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    sentinel = evidence / "keep.bin"
    sentinel.write_bytes(b"evidence sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    attacker_payload = b'{"origin":"attacker","success":true}\n'
    preserved_name = ".verified-probe-json.preserved"
    original_renameatx = oracle_boot._renameatx
    injection_reached = False
    retained_identities: dict[bytes, tuple[int, int]] = {}

    def substituting_renameatx(
        source_parent,
        source_name: str,
        destination_parent,
        destination_name: str,
        flags: int,
        description: str,
    ) -> None:
        nonlocal injection_reached
        if not injection_reached and destination_name == "probe.json":
            verified = os.stat(
                source_name,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            retained_identities[expected_payload] = (
                verified.st_dev,
                verified.st_ino,
            )
            os.rename(
                source_name,
                preserved_name,
                src_dir_fd=source_parent.fd,
                dst_dir_fd=source_parent.fd,
            )
            attacker_fd = os.open(
                source_name,
                (
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | os.O_NOFOLLOW
                ),
                0o600,
                dir_fd=source_parent.fd,
            )
            try:
                os.fchmod(attacker_fd, 0o600)
                view = memoryview(attacker_payload)
                while view:
                    written = os.write(attacker_fd, view)
                    assert written > 0
                    view = view[written:]
                os.fsync(attacker_fd)
                attacker = os.fstat(attacker_fd)
                retained_identities[attacker_payload] = (
                    attacker.st_dev,
                    attacker.st_ino,
                )
            finally:
                os.close(attacker_fd)
            os.fsync(source_parent.fd)
            injection_reached = True
        return original_renameatx(
            source_parent,
            source_name,
            destination_parent,
            destination_name,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        substituting_renameatx,
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc

    assert injection_reached
    assert raised is not None, (
        "writer accepted a different inode substituted at the verified name"
    )
    assert not (evidence / "probe.json").exists()
    artifacts = [
        path
        for path in evidence.iterdir()
        if path.name != sentinel.name
    ]
    assert len(artifacts) == 2
    observed_payloads: dict[bytes, tuple[int, int]] = {}
    for artifact in artifacts:
        observed = artifact.stat(follow_symlinks=False)
        assert stat.S_ISREG(observed.st_mode)
        assert stat.S_IMODE(observed.st_mode) == 0o600
        observed_payloads[artifact.read_bytes()] = (
            observed.st_dev,
            observed.st_ino,
        )
    assert observed_payloads == retained_identities
    assert (evidence / preserved_name).read_bytes() == expected_payload
    assert sentinel.read_bytes() == b"evidence sentinel survives"
    assert outside.read_bytes() == b"outside sentinel survives"


def test_write_probe_json_reconciles_rename_after_effect_as_exact_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    sentinel = evidence / "keep.bin"
    sentinel.write_bytes(b"evidence sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    original_renameatx = oracle_boot._renameatx
    injected = False
    retained_identity: tuple[int, int] | None = None

    class RenameCompletedThenRaised(OSError):
        pass

    def rename_then_raise_once(
        source_parent,
        source_name: str,
        destination_parent,
        destination_name: str,
        flags: int,
        description: str,
    ) -> None:
        nonlocal injected
        nonlocal retained_identity
        if not injected and destination_name == "probe.json":
            source = os.stat(
                source_name,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            retained_identity = (source.st_dev, source.st_ino)
            original_renameatx(
                source_parent,
                source_name,
                destination_parent,
                destination_name,
                flags,
                description,
            )
            canonical = os.stat(
                destination_name,
                dir_fd=destination_parent.fd,
                follow_symlinks=False,
            )
            assert (canonical.st_dev, canonical.st_ino) == retained_identity
            injected = True
            raise RenameCompletedThenRaised(
                "rename succeeded before wrapper raised"
            )
        return original_renameatx(
            source_parent,
            source_name,
            destination_parent,
            destination_name,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        rename_then_raise_once,
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc

    assert injected
    assert raised is None, (
        "exact committed inode was treated as a failed publication",
        raised,
    )
    canonical = evidence / "probe.json"
    assert canonical.read_bytes() == expected_payload
    observed = canonical.stat(follow_symlinks=False)
    assert (observed.st_dev, observed.st_ino) == retained_identity
    assert {
        path.name for path in evidence.iterdir()
    } == {"keep.bin", "probe.json"}
    assert sentinel.read_bytes() == b"evidence sentinel survives"
    assert outside.read_bytes() == b"outside sentinel survives"


def _dev_inode(observed: os.stat_result) -> tuple[int, int]:
    return observed.st_dev, observed.st_ino


def _rename_destination_name(args, kwargs) -> str | None:
    if "destination_name" in kwargs:
        return kwargs["destination_name"]
    if len(args) >= 4:
        return args[3]
    return None


class _ProbeJsonDurabilityTrace:
    """Accept fsync only for the staged pending inode or evidence directory."""

    def __init__(self, evidence: Path):
        self.evidence = evidence
        self.evidence_identity = _dev_inode(
            evidence.stat(follow_symlinks=False)
        )
        self.pending_identity: tuple[int, int] | None = None
        self.events: list[str] = []
        self._real_fsync = os.fsync

    def _discover_pending_identity(self) -> tuple[int, int]:
        directory_fd = os.open(
            self.evidence,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            candidates: list[tuple[int, int]] = []
            for name in os.listdir(directory_fd):
                if not (
                    name.startswith(".probe-json-")
                    and name.endswith(".pending")
                ):
                    continue
                observed = os.stat(
                    name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                assert stat.S_ISREG(observed.st_mode)
                assert stat.S_IMODE(observed.st_mode) == 0o600
                candidates.append(_dev_inode(observed))
        finally:
            os.close(directory_fd)
        assert len(candidates) == 1, candidates
        return candidates[0]

    def fsync(self, descriptor: int) -> None:
        observed = os.fstat(descriptor)
        identity = _dev_inode(observed)
        if identity == self.evidence_identity:
            assert stat.S_ISDIR(observed.st_mode)
            role = "evidence_fsync"
        else:
            if self.pending_identity is None:
                self.pending_identity = self._discover_pending_identity()
            assert identity == self.pending_identity, (
                "fsync used an unrelated descriptor",
                descriptor,
                identity,
                self.pending_identity,
            )
            assert stat.S_ISREG(observed.st_mode)
            assert stat.S_IMODE(observed.st_mode) == 0o600
            role = "pending_fsync"
        self._real_fsync(descriptor)
        self.events.append(role)

    def assert_canonical_identity(self) -> None:
        assert self.pending_identity is not None
        canonical = self.evidence / "probe.json"
        assert _dev_inode(
            canonical.stat(follow_symlinks=False)
        ) == self.pending_identity


@pytest.mark.parametrize(
    "failure_point",
    [
        "initial-reconcile",
        "failed-fsync-reconcile",
        "post-fsync-reconcile",
    ],
)
def test_write_probe_json_quarantines_reachable_canonical_after_reconcile_error(
    failure_point: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1, "success": True}
    expected = oracle_boot._encode_probe_json(payload)
    evidence_identity = _dev_inode(
        evidence.stat(follow_symlinks=False)
    )
    original_namespace = oracle_boot._probe_json_retained_namespace
    original_renameatx = oracle_boot._renameatx
    original_fsync = os.fsync
    publish_seen = False
    namespace_calls_after_publish = 0
    published_identity: tuple[int, int] | None = None
    reconciliation_error = OSError(
        errno.EIO,
        f"injected {failure_point}",
    )
    reconciliation_context_error = RuntimeError(
        "injected pre-existing reconciliation context"
    )
    durability_error = OSError(
        errno.ENOSPC,
        "injected failed publication-directory fsync",
    )
    durability_failure_seen = False
    publication_fsync_calls = 0
    fsync_calls_at_reconciliation: int | None = None

    def tracked_renameatx(*args, **kwargs) -> None:
        nonlocal publish_seen, published_identity
        original_renameatx(*args, **kwargs)
        if _rename_destination_name(args, kwargs) != "probe.json":
            return
        publish_seen = True
        destination_parent = (
            kwargs["destination_parent"]
            if "destination_parent" in kwargs
            else args[2]
        )
        canonical = os.stat(
            "probe.json",
            dir_fd=destination_parent.fd,
            follow_symlinks=False,
        )
        published_identity = _dev_inode(canonical)

    def fail_selected_directory_fsync(descriptor: int) -> None:
        nonlocal durability_failure_seen, publication_fsync_calls
        observed = os.fstat(descriptor)
        is_publication_directory = (
            publish_seen
            and stat.S_ISDIR(observed.st_mode)
            and _dev_inode(observed) == evidence_identity
        )
        if is_publication_directory:
            publication_fsync_calls += 1
        selected = (
            failure_point
            in {"failed-fsync-reconcile", "post-fsync-reconcile"}
            and not durability_failure_seen
            and is_publication_directory
        )
        if selected:
            durability_failure_seen = True
            raise durability_error
        original_fsync(descriptor)

    def fail_once_after_publish(staged):
        nonlocal namespace_calls_after_publish
        nonlocal fsync_calls_at_reconciliation
        if publish_seen:
            namespace_calls_after_publish += 1
            if failure_point == "initial-reconcile":
                selected_call = 1
            elif failure_point == "failed-fsync-reconcile":
                selected_call = 2
            else:
                selected_call = 3
            if namespace_calls_after_publish == selected_call:
                fsync_calls_at_reconciliation = publication_fsync_calls
                if failure_point == "post-fsync-reconcile":
                    reconciliation_error.__context__ = (
                        reconciliation_context_error
                    )
                raise reconciliation_error
        return original_namespace(staged)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=fail_selected_directory_fsync),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        tracked_renameatx,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_probe_json_retained_namespace",
        fail_once_after_publish,
    )

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._write_probe_json(evidence, payload)

    graph = _exception_graph(raised.value)
    assert publish_seen
    assert reconciliation_error in graph
    assert fsync_calls_at_reconciliation == {
        "initial-reconcile": 0,
        "failed-fsync-reconcile": 1,
        "post-fsync-reconcile": 2,
    }[failure_point]
    if failure_point != "initial-reconcile":
        assert durability_failure_seen
        assert any(
            note
            == (
                "post-publication evidence-directory fsync also "
                "failed: OSError: [Errno 28] injected failed "
                "publication-directory fsync"
            )
            for candidate in graph
            for note in getattr(candidate, "__notes__", ())
        )
    if failure_point == "failed-fsync-reconcile":
        assert durability_error in graph
    if failure_point == "post-fsync-reconcile":
        assert (
            reconciliation_error.__context__
            is reconciliation_context_error
        )
        assert reconciliation_context_error in graph
    _assert_no_canonical_probe_json(evidence)
    private = tuple(evidence.iterdir())
    assert len(private) == 1
    observed = private[0].stat(follow_symlinks=False)
    assert stat.S_ISREG(observed.st_mode)
    assert published_identity is not None
    assert _dev_inode(observed) == published_identity
    assert stat.S_IMODE(observed.st_mode) == 0o600
    assert private[0].read_bytes() == expected


@pytest.mark.parametrize("initial_mode", [0o000, 0o644])
def test_preserve_canonical_probe_json_quarantine_forces_mode_0600(
    initial_mode: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1, "success": True}
    staged = oracle_boot._stage_probe_json(evidence, payload)
    canonical_path = evidence / "probe.json"
    canonical_payload = b"sensitive mismatched canonical\n"
    canonical_path.write_bytes(canonical_payload)
    canonical_path.chmod(initial_mode)
    canonical_before = canonical_path.stat(follow_symlinks=False)
    canonical_identity = _dev_inode(canonical_before)
    primary = oracle_boot.BootProbeError(
        "force mismatched canonical quarantine"
    )
    original_open = os.open
    original_fchmod = os.fchmod
    original_fsync = os.fsync
    secure_opens: list[tuple[str, int, int | None, tuple[int, int]]] = []
    secure_fchmods: list[int] = []
    secure_fsyncs: list[tuple[int, int]] = []

    def tracked_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        observed = os.fstat(descriptor)
        if stat.S_ISREG(observed.st_mode) and (
            _dev_inode(observed) == canonical_identity
        ):
            secure_opens.append(
                (os.fspath(path), flags, dir_fd, _dev_inode(observed))
            )
        return descriptor

    def tracked_fchmod(descriptor: int, mode: int) -> None:
        if _dev_inode(os.fstat(descriptor)) == canonical_identity:
            secure_fchmods.append(mode)
        original_fchmod(descriptor, mode)

    def tracked_fsync(descriptor: int) -> None:
        observed = os.fstat(descriptor)
        if (
            stat.S_ISREG(observed.st_mode)
            and _dev_inode(observed) == canonical_identity
        ):
            secure_fsyncs.append(_dev_inode(observed))
        original_fsync(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=tracked_open,
            fchmod=tracked_fchmod,
            fsync=tracked_fsync,
        ),
        raising=False,
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
        quarantined: list[tuple[Path, os.stat_result]] = []
        for path in evidence.iterdir():
            observed = path.stat(follow_symlinks=False)
            if _dev_inode(observed) == canonical_identity:
                quarantined.append((path, observed))
        assert len(quarantined) == 1
        private_path, observed = quarantined[0]
        assert stat.S_ISREG(observed.st_mode)
        assert stat.S_IMODE(observed.st_mode) == 0o600
        assert private_path.read_bytes() == canonical_payload
        assert secure_opens == [
            (
                private_path.name,
                os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
                staged.directory_handle.fd,
                canonical_identity,
            )
        ]
        assert secure_fchmods == [0o600]
        assert secure_fsyncs == [canonical_identity]
        assert getattr(primary, "__notes__", ()) == ()
    finally:
        oracle_boot._close_staged_probe_json(staged)


@pytest.mark.parametrize("boundary", ["after-open", "after-close"])
def test_quarantine_forces_mode_0600_descriptor_ownership_at_interrupt_boundaries(
    boundary: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    staged = oracle_boot._stage_probe_json(
        evidence,
        {"schema_version": 1},
    )
    canonical_path = evidence / "probe.json"
    canonical_path.write_bytes(b"quarantine ownership\n")
    canonical = canonical_path.stat(follow_symlinks=False)
    expected_identity = oracle_boot._stat_identity(canonical)
    acquired_descriptors: list[int] = []
    secured_descriptor = -1
    private_name = ""
    private_dir_fd = -1
    replacement_descriptor = -1
    close_calls = 0
    armed = False
    original_open = os.open
    original_close = os.close

    def capture_secure_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal armed, secured_descriptor, private_name, private_dir_fd
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        observed = os.fstat(descriptor)
        if _dev_inode(observed) == _dev_inode(canonical):
            secured_descriptor = descriptor
            private_name = os.fspath(path)
            private_dir_fd = dir_fd if dir_fd is not None else -1
            acquired_descriptors.append(descriptor)
            if boundary == "after-open":
                armed = True
        return descriptor

    def close_then_maybe_reuse(descriptor: int) -> None:
        nonlocal armed, close_calls, replacement_descriptor
        if descriptor != secured_descriptor:
            original_close(descriptor)
            return
        close_calls += 1
        original_close(descriptor)
        if boundary == "after-close" and replacement_descriptor < 0:
            replacement_descriptor = original_open(
                private_name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=private_dir_fd,
            )
            assert replacement_descriptor == secured_descriptor
            armed = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_secure_open,
            close=close_then_maybe_reuse,
        ),
        raising=False,
    )
    interrupt = _InjectedAcquisitionBoundaryInterrupt(boundary)
    secure_target = getattr(
        oracle_boot,
        "_secure_private_probe_json",
        None,
    )
    previous_trace = sys.gettrace()

    try:
        if secure_target is not None:
            sys.settrace(
                _next_line_interrupt_trace(
                    secure_target,
                    lambda: armed,
                    interrupt,
                )
            )
        try:
            with pytest.raises(
                _InjectedAcquisitionBoundaryInterrupt,
            ) as raised:
                oracle_boot._move_canonical_probe_json_to_private(
                    staged,
                    expected_identity,
                    prefer_original_pending_name=False,
                    description="test quarantine ownership",
                )
        finally:
            sys.settrace(previous_trace)

        assert raised.value is interrupt
        assert len(acquired_descriptors) == 1
        assert close_calls == 1
        if boundary == "after-open":
            _assert_acquired_descriptors_closed(acquired_descriptors)
        else:
            assert replacement_descriptor == secured_descriptor
            assert os.fstat(replacement_descriptor)
            assert os.lseek(
                replacement_descriptor,
                0,
                os.SEEK_CUR,
            ) == 0
            assert getattr(interrupt, "__notes__", ()) == ()
    finally:
        if replacement_descriptor >= 0:
            try:
                original_close(replacement_descriptor)
            except OSError as exc:
                assert exc.errno == errno.EBADF
        oracle_boot._close_staged_probe_json(staged)


def test_quarantine_forces_mode_0600_preserves_fsync_error_over_close_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    staged = oracle_boot._stage_probe_json(
        evidence,
        {"schema_version": 1},
    )
    canonical_path = evidence / "probe.json"
    canonical_path.write_bytes(b"quarantine causal errors\n")
    canonical = canonical_path.stat(follow_symlinks=False)
    canonical_identity = _dev_inode(canonical)
    expected_identity = oracle_boot._stat_identity(canonical)
    secured_descriptor = -1
    close_calls = 0
    original_open = os.open
    original_close = os.close
    original_fsync = os.fsync
    fsync_error = OSError(errno.EIO, "injected private file fsync")
    close_error = _InjectedWriterBoundaryError(
        errno.EIO,
        "injected private descriptor close",
    )

    def capture_secure_open(
        path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ):
        nonlocal secured_descriptor
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if _dev_inode(os.fstat(descriptor)) == canonical_identity:
            secured_descriptor = descriptor
        return descriptor

    def fail_private_fsync(descriptor: int) -> None:
        if _dev_inode(os.fstat(descriptor)) == canonical_identity:
            raise fsync_error
        original_fsync(descriptor)

    def close_private_after_effect(descriptor: int) -> None:
        nonlocal close_calls
        if descriptor != secured_descriptor:
            original_close(descriptor)
            return
        close_calls += 1
        original_close(descriptor)
        raise close_error

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(
            os,
            open=capture_secure_open,
            fsync=fail_private_fsync,
            close=close_private_after_effect,
        ),
        raising=False,
    )

    try:
        with pytest.raises(OSError) as raised:
            oracle_boot._move_canonical_probe_json_to_private(
                staged,
                expected_identity,
                prefer_original_pending_name=False,
                description="test quarantine causal errors",
            )

        assert raised.value is fsync_error
        assert secured_descriptor >= 0
        assert close_calls == 1
        with pytest.raises(OSError) as closed:
            os.fstat(secured_descriptor)
        assert closed.value.errno == errno.EBADF
        assert any(
            "private probe JSON descriptor close also failed" in note
            and "injected private descriptor close" in note
            for note in getattr(fsync_error, "__notes__", ())
        )
    finally:
        oracle_boot._close_staged_probe_json(staged)


@pytest.mark.parametrize("failure_stage", ["lookup", "quarantine"])
def test_write_probe_json_quarantines_reachable_canonical_after_reconcile_error_notes_quarantine_failure(
    failure_stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"schema_version": 1, "success": True}
    original_namespace = oracle_boot._probe_json_retained_namespace
    original_renameatx = oracle_boot._renameatx
    original_stat_name = oracle_boot._stat_staged_probe_json_name
    original_preserve = (
        oracle_boot._preserve_canonical_probe_json_privately
    )
    publish_seen = False
    reconciliation_failed = False
    quarantine_failure_seen = False
    reconciliation_error = OSError(
        errno.EIO,
        "injected initial reconciliation",
    )
    quarantine_error = OSError(
        errno.EIO,
        f"injected quarantine {failure_stage} failure",
    )

    def tracked_renameatx(*args, **kwargs) -> None:
        nonlocal publish_seen
        original_renameatx(*args, **kwargs)
        if _rename_destination_name(args, kwargs) == "probe.json":
            publish_seen = True

    def fail_initial_reconciliation(staged):
        nonlocal reconciliation_failed
        if publish_seen and not reconciliation_failed:
            reconciliation_failed = True
            raise reconciliation_error
        return original_namespace(staged)

    def fail_quarantine_lookup(staged, name: str):
        nonlocal quarantine_failure_seen
        if (
            failure_stage == "lookup"
            and reconciliation_failed
            and name == "probe.json"
            and not quarantine_failure_seen
        ):
            quarantine_failure_seen = True
            raise quarantine_error
        return original_stat_name(staged, name)

    def fail_quarantine_move(*args, **kwargs):
        nonlocal quarantine_failure_seen
        if (
            failure_stage == "quarantine"
            and reconciliation_failed
            and not quarantine_failure_seen
        ):
            quarantine_failure_seen = True
            raise quarantine_error
        return original_preserve(*args, **kwargs)

    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        tracked_renameatx,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_probe_json_retained_namespace",
        fail_initial_reconciliation,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_stat_staged_probe_json_name",
        fail_quarantine_lookup,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_preserve_canonical_probe_json_privately",
        fail_quarantine_move,
    )

    with pytest.raises(oracle_boot.BootProbeError) as raised:
        oracle_boot._write_probe_json(evidence, payload)

    assert publish_seen
    assert reconciliation_failed
    assert quarantine_failure_seen
    graph = _exception_graph(raised.value)
    assert reconciliation_error in graph
    assert any(
        f"injected quarantine {failure_stage} failure" in note
        for candidate in graph
        for note in getattr(candidate, "__notes__", ())
    )


def test_write_probe_json_fsyncs_file_and_directory_on_both_sides_of_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    original_renameatx = oracle_boot._renameatx
    trace = _ProbeJsonDurabilityTrace(evidence)

    def traced_fsync(descriptor: int) -> None:
        trace.fsync(descriptor)

    def traced_renameatx(*args, **kwargs) -> None:
        original_renameatx(*args, **kwargs)
        if _rename_destination_name(args, kwargs) == "probe.json":
            trace.events.append("rename")

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=traced_fsync),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        traced_renameatx,
        raising=False,
    )

    oracle_boot._write_probe_json(evidence, payload)

    rename_index = trace.events.index("rename")
    pending_fsync_indices = [
        index
        for index, event in enumerate(trace.events)
        if event == "pending_fsync"
    ]
    evidence_fsync_indices = [
        index
        for index, event in enumerate(trace.events)
        if event == "evidence_fsync"
    ]
    assert pending_fsync_indices
    assert any(
        pending_index < evidence_index < rename_index
        for pending_index in pending_fsync_indices
        for evidence_index in evidence_fsync_indices
    )
    assert any(
        rename_index < evidence_index
        for evidence_index in evidence_fsync_indices
    ), trace.events
    trace.assert_canonical_identity()
    assert (evidence / "probe.json").read_bytes() == expected_payload
    assert {
        path.name for path in evidence.iterdir()
    } == {"probe.json"}


def test_write_probe_json_retries_transient_post_publish_directory_fsync_after_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    sentinel = evidence / "keep.bin"
    sentinel.write_bytes(b"evidence sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    original_renameatx = oracle_boot._renameatx
    trace = _ProbeJsonDurabilityTrace(evidence)
    rename_completed = False
    post_publish_attempts = 0
    completed_post_publish_fsyncs = 0

    class PostPublishFsyncCompletedThenRaised(OSError):
        pass

    def transient_fsync(descriptor: int) -> None:
        nonlocal post_publish_attempts
        nonlocal completed_post_publish_fsyncs
        trace.fsync(descriptor)
        if (
            not rename_completed
            or trace.events[-1] != "evidence_fsync"
        ):
            return
        post_publish_attempts += 1
        if post_publish_attempts == 1:
            raise PostPublishFsyncCompletedThenRaised(
                errno.EIO,
                "post-publish directory fsync raised after effect",
            )
        completed_post_publish_fsyncs += 1

    def tracked_renameatx(*args, **kwargs) -> None:
        nonlocal rename_completed
        original_renameatx(*args, **kwargs)
        if _rename_destination_name(args, kwargs) == "probe.json":
            rename_completed = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=transient_fsync),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        tracked_renameatx,
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc

    assert rename_completed
    assert post_publish_attempts == 2, (
        "writer returned without retrying the uncertain directory fsync"
    )
    assert completed_post_publish_fsyncs == 1
    assert raised is None, raised
    trace.assert_canonical_identity()
    assert (evidence / "probe.json").read_bytes() == expected_payload
    assert {
        path.name for path in evidence.iterdir()
    } == {"keep.bin", "probe.json"}
    assert sentinel.read_bytes() == b"evidence sentinel survives"
    assert outside.read_bytes() == b"outside sentinel survives"


def test_write_probe_json_bounds_persistent_post_publish_directory_fsync_and_preserves_private_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    sentinel = evidence / "keep.bin"
    sentinel.write_bytes(b"evidence sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    original_renameatx = oracle_boot._renameatx
    trace = _ProbeJsonDurabilityTrace(evidence)
    publish_completed = False
    post_publish_attempts = 0
    retry_attempts = 3
    rollback_fsyncs = 0
    rollback_fsync_budget = 3
    clock = _VirtualCleanupClock(call_budget=16)

    class PersistentPostPublishFsyncError(OSError):
        pass

    def canonical_is_exact_pending() -> bool:
        canonical = evidence / "probe.json"
        try:
            observed = canonical.stat(follow_symlinks=False)
        except FileNotFoundError:
            return False
        return (
            trace.pending_identity is not None
            and stat.S_ISREG(observed.st_mode)
            and stat.S_IMODE(observed.st_mode) == 0o600
            and _dev_inode(observed) == trace.pending_identity
        )

    def private_pending_is_preserved() -> bool:
        for candidate in evidence.iterdir():
            if candidate.name == sentinel.name:
                continue
            observed = candidate.stat(follow_symlinks=False)
            if (
                stat.S_ISREG(observed.st_mode)
                and stat.S_IMODE(observed.st_mode) == 0o600
                and _dev_inode(observed) == trace.pending_identity
                and candidate.read_bytes() == expected_payload
            ):
                return True
        return False

    def persistent_fsync(descriptor: int) -> None:
        nonlocal post_publish_attempts
        nonlocal rollback_fsyncs
        trace.fsync(descriptor)
        if (
            not publish_completed
            or trace.events[-1] != "evidence_fsync"
        ):
            return
        if canonical_is_exact_pending():
            post_publish_attempts += 1
            if post_publish_attempts > retry_attempts:
                raise AssertionError(
                    "persistent post-publish fsync call budget exceeded"
                )
            raise PersistentPostPublishFsyncError(
                errno.EIO,
                "persistent post-publish directory fsync failure",
            )
        assert private_pending_is_preserved(), (
            "rollback fsync ran before canonical pending evidence was "
            "exclusively returned to private storage"
        )
        rollback_fsyncs += 1
        if rollback_fsyncs > rollback_fsync_budget:
            raise AssertionError("rollback fsync call budget exceeded")

    def tracked_renameatx(*args, **kwargs) -> None:
        nonlocal publish_completed
        original_renameatx(*args, **kwargs)
        if _rename_destination_name(args, kwargs) == "probe.json":
            publish_completed = True

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=persistent_fsync),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        tracked_renameatx,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_PROBE_JSON_DIRECTORY_FSYNC_ATTEMPTS",
        retry_attempts,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "time",
        _ModuleProxy(
            time,
            monotonic=clock.monotonic,
            sleep=clock.sleep,
        ),
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc

    assert publish_completed
    assert post_publish_attempts == retry_attempts, (
        "writer did not use the defined post-publish fsync retry contract"
    )
    assert 1 <= rollback_fsyncs <= rollback_fsync_budget, (
        "rollback did not durably confirm its private pending evidence"
    )
    assert raised is not None
    assert not isinstance(raised, AssertionError), raised
    exception_graph = _exception_graph(raised)
    assert any(
        isinstance(candidate, PersistentPostPublishFsyncError)
        or any(
            "persistent post-publish directory fsync failure" in note
            for note in getattr(candidate, "__notes__", ())
        )
        for candidate in exception_graph
    ), exception_graph
    assert len(clock.sleep_calls) < clock.call_budget
    _assert_no_canonical_probe_json(evidence)
    artifacts = [
        path
        for path in evidence.iterdir()
        if path.name != sentinel.name
    ]
    assert len(artifacts) == 1
    preserved = artifacts[0]
    observed = preserved.stat(follow_symlinks=False)
    assert stat.S_ISREG(observed.st_mode)
    assert stat.S_IMODE(observed.st_mode) == 0o600
    assert _dev_inode(observed) == trace.pending_identity
    assert preserved.read_bytes() == expected_payload
    assert sentinel.read_bytes() == b"evidence sentinel survives"
    assert outside.read_bytes() == b"outside sentinel survives"


def test_write_probe_json_quarantines_canonical_mismatch_before_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    sentinel = evidence / "keep.bin"
    sentinel.write_bytes(b"evidence sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    attacker_payload = (
        b'{"origin":"attacker","schema_version":1,"success":true}\n'
    )

    staged = oracle_boot._stage_probe_json(evidence, payload)
    pending = os.stat(
        staged.pending_name,
        dir_fd=staged.directory_handle.fd,
        follow_symlinks=False,
    )
    pending_identity = _dev_inode(pending)
    assert stat.S_ISREG(pending.st_mode)
    assert stat.S_IMODE(pending.st_mode) == 0o600
    assert (evidence / staged.pending_name).read_bytes() == expected_payload

    attacker_fd = os.open(
        "probe.json",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=staged.directory_handle.fd,
    )
    try:
        os.fchmod(attacker_fd, 0o600)
        view = memoryview(attacker_payload)
        while view:
            written = os.write(attacker_fd, view)
            assert written > 0
            view = view[written:]
        os.fsync(attacker_fd)
        attacker = os.fstat(attacker_fd)
        attacker_identity = _dev_inode(attacker)
    finally:
        os.close(attacker_fd)
    os.fsync(staged.directory_handle.fd)
    assert attacker_identity != pending_identity

    owned_descriptors = (
        staged.verifier_fd,
        staged.directory_handle.fd,
    )
    assert len(set(owned_descriptors)) == 2
    assert all(descriptor >= 0 for descriptor in owned_descriptors)
    close_calls = {descriptor: 0 for descriptor in owned_descriptors}
    original_close = os.close

    def tracked_close(descriptor: int) -> None:
        if descriptor in close_calls:
            close_calls[descriptor] += 1
            if close_calls[descriptor] > 1:
                raise AssertionError(
                    f"staged descriptor {descriptor} was closed twice"
                )
        original_close(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, close=tracked_close),
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(
            evidence,
            payload,
            _staged=staged,
        )
    except BaseException as exc:
        raised = exc

    assert isinstance(raised, oracle_boot.BootProbeError), raised
    assert close_calls == {
        descriptor: 1 for descriptor in owned_descriptors
    }
    assert staged.verifier_fd == -1
    assert staged.directory_handle.fd == -1
    for descriptor in owned_descriptors:
        with pytest.raises(OSError) as closed:
            os.fstat(descriptor)
        assert closed.value.errno == errno.EBADF

    assert not (evidence / "probe.json").exists()
    artifacts = [
        path
        for path in evidence.iterdir()
        if path.name != sentinel.name
    ]
    assert len(artifacts) == 2
    observed_payloads: dict[bytes, tuple[int, int]] = {}
    for artifact in artifacts:
        assert artifact.name != "probe.json"
        observed = artifact.stat(follow_symlinks=False)
        assert stat.S_ISREG(observed.st_mode)
        assert stat.S_IMODE(observed.st_mode) == 0o600
        observed_payloads[artifact.read_bytes()] = _dev_inode(observed)
    assert observed_payloads == {
        expected_payload: pending_identity,
        attacker_payload: attacker_identity,
    }
    assert sentinel.read_bytes() == b"evidence sentinel survives"
    assert outside.read_bytes() == b"outside sentinel survives"


@pytest.mark.xfail(
    strict=False,
    reason=(
        "active final-syscall path replacement is outside the "
        "approved practical threat model"
    ),
)
@pytest.mark.parametrize("wrapper_mode", ["return", "raise"])
def test_write_probe_json_rejects_post_publish_evidence_path_substitution(
    wrapper_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    displaced = evidence.with_name(f"{evidence.name}-displaced")
    original_sentinel = evidence / "keep.bin"
    original_sentinel.write_bytes(b"displaced sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    replacement_sentinel_name = "replacement.keep"
    replacement_sentinel_bytes = b"replacement sentinel survives"
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    original_renameatx = oracle_boot._renameatx
    rename_call_budget = 16
    rename_calls = 0
    injection_reached = False
    pending_identity: tuple[int, int] | None = None

    class PostPublishEvidencePathSubstitution(OSError):
        pass

    def substituted_renameatx(*args, **kwargs) -> None:
        nonlocal injection_reached
        nonlocal pending_identity
        nonlocal rename_calls
        rename_calls += 1
        if rename_calls > rename_call_budget:
            raise AssertionError("probe JSON rename call budget exceeded")

        source_parent = (
            kwargs["source_parent"]
            if "source_parent" in kwargs
            else args[0]
        )
        source_name = (
            kwargs["source_name"]
            if "source_name" in kwargs
            else args[1]
        )
        destination_parent = (
            kwargs["destination_parent"]
            if "destination_parent" in kwargs
            else args[2]
        )
        destination_name = _rename_destination_name(args, kwargs)
        if (
            not injection_reached
            and source_name.startswith(".probe-json-")
            and source_name.endswith(".pending")
            and destination_name == "probe.json"
        ):
            source = os.stat(
                source_name,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            pending_identity = _dev_inode(source)
            assert stat.S_ISREG(source.st_mode)
            assert stat.S_IMODE(source.st_mode) == 0o600
            assert source_parent.fd == destination_parent.fd
            assert (evidence / source_name).read_bytes() == expected_payload

            original_renameatx(*args, **kwargs)
            canonical = os.stat(
                "probe.json",
                dir_fd=destination_parent.fd,
                follow_symlinks=False,
            )
            assert _dev_inode(canonical) == pending_identity
            evidence.rename(displaced)
            evidence.mkdir()
            (evidence / replacement_sentinel_name).write_bytes(
                replacement_sentinel_bytes
            )
            injection_reached = True
            if wrapper_mode == "raise":
                raise PostPublishEvidencePathSubstitution(
                    "exclusive publish completed before evidence path "
                    "was substituted"
                )
            return
        original_renameatx(*args, **kwargs)

    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        substituted_renameatx,
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc

    assert injection_reached
    assert 1 <= rename_calls <= rename_call_budget
    assert isinstance(raised, oracle_boot.BootProbeError), raised
    if wrapper_mode == "raise":
        pending_errors: list[BaseException] = [raised]
        exception_graph: list[BaseException] = []
        while pending_errors:
            current = pending_errors.pop()
            if any(current is candidate for candidate in exception_graph):
                continue
            exception_graph.append(current)
            if current.__cause__ is not None:
                pending_errors.append(current.__cause__)
            if current.__context__ is not None:
                pending_errors.append(current.__context__)
        assert any(
            isinstance(candidate, PostPublishEvidencePathSubstitution)
            or any(
                "PostPublishEvidencePathSubstitution" in note
                and "exclusive publish completed" in note
                for note in getattr(candidate, "__notes__", ())
            )
            for candidate in exception_graph
        ), exception_graph

    assert not (displaced / "probe.json").exists()
    assert not (evidence / "probe.json").exists()
    assert pending_identity is not None
    private_artifacts = [
        path
        for path in displaced.iterdir()
        if path.name != original_sentinel.name
    ]
    assert len(private_artifacts) == 1
    preserved = private_artifacts[0]
    assert preserved.name != "probe.json"
    observed = preserved.stat(follow_symlinks=False)
    assert stat.S_ISREG(observed.st_mode)
    assert stat.S_IMODE(observed.st_mode) == 0o600
    assert _dev_inode(observed) == pending_identity
    assert preserved.read_bytes() == expected_payload
    assert (displaced / original_sentinel.name).read_bytes() == (
        b"displaced sentinel survives"
    )
    assert {
        path.name for path in evidence.iterdir()
    } == {replacement_sentinel_name}
    assert (evidence / replacement_sentinel_name).read_bytes() == (
        replacement_sentinel_bytes
    )
    assert outside.read_bytes() == b"outside sentinel survives"


@pytest.mark.xfail(
    strict=False,
    reason=(
        "active final-syscall path replacement is outside the "
        "approved practical threat model"
    ),
)
@pytest.mark.parametrize("fsync_wrapper_mode", ["return", "raise"])
def test_write_probe_json_rejects_post_publish_fsync_evidence_path_substitution(
    fsync_wrapper_mode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    displaced = evidence.with_name(f"{evidence.name}-displaced")
    original_sentinel = evidence / "keep.bin"
    original_sentinel.write_bytes(b"displaced sentinel survives")
    outside = tmp_path / "outside.keep"
    outside.write_bytes(b"outside sentinel survives")
    replacement_sentinel_name = "replacement.keep"
    replacement_sentinel_bytes = b"replacement sentinel survives"
    payload = {"success": True, "schema_version": 1}
    expected_payload = (
        b"{\n"
        b'  "schema_version": 1,\n'
        b'  "success": true\n'
        b"}\n"
    )
    evidence_observed = evidence.stat(follow_symlinks=False)
    evidence_identity = _dev_inode(evidence_observed)
    original_fsync = os.fsync
    original_renameatx = oracle_boot._renameatx
    fsync_call_budget = 32
    rename_call_budget = 16
    fsync_calls = 0
    rename_calls = 0
    post_publish_evidence_fsyncs = 0
    publish_completed = False
    injection_reached = False
    published_identity: tuple[int, int] | None = None

    class PostPublishEvidenceFsyncPathSubstitution(OSError):
        pass

    def tracked_renameatx(*args, **kwargs) -> None:
        nonlocal publish_completed
        nonlocal published_identity
        nonlocal rename_calls
        rename_calls += 1
        if rename_calls > rename_call_budget:
            raise AssertionError("probe JSON rename call budget exceeded")

        source_parent = (
            kwargs["source_parent"]
            if "source_parent" in kwargs
            else args[0]
        )
        source_name = (
            kwargs["source_name"]
            if "source_name" in kwargs
            else args[1]
        )
        destination_name = _rename_destination_name(args, kwargs)
        is_publish = (
            not publish_completed
            and source_name.startswith(".probe-json-")
            and source_name.endswith(".pending")
            and destination_name == "probe.json"
        )
        if is_publish:
            pending = os.stat(
                source_name,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            assert stat.S_ISREG(pending.st_mode)
            assert stat.S_IMODE(pending.st_mode) == 0o600
            published_identity = _dev_inode(pending)

        original_renameatx(*args, **kwargs)
        if is_publish:
            publish_completed = True

    def substituted_fsync(descriptor: int) -> None:
        nonlocal fsync_calls
        nonlocal injection_reached
        nonlocal post_publish_evidence_fsyncs
        fsync_calls += 1
        if fsync_calls > fsync_call_budget:
            raise AssertionError("probe JSON fsync call budget exceeded")

        observed = os.fstat(descriptor)
        descriptor_identity = _dev_inode(observed)
        exact_evidence_directory = (
            descriptor_identity == evidence_identity
            and stat.S_ISDIR(observed.st_mode)
        )
        if publish_completed and exact_evidence_directory:
            post_publish_evidence_fsyncs += 1
        if (
            not injection_reached
            and publish_completed
            and exact_evidence_directory
        ):
            original_fsync(descriptor)
            canonical = os.stat(
                "probe.json",
                dir_fd=descriptor,
                follow_symlinks=False,
            )
            assert published_identity is not None
            assert _dev_inode(canonical) == published_identity
            assert stat.S_ISREG(canonical.st_mode)
            assert stat.S_IMODE(canonical.st_mode) == 0o600
            assert (evidence / "probe.json").read_bytes() == expected_payload

            evidence.rename(displaced)
            evidence.mkdir()
            (evidence / replacement_sentinel_name).write_bytes(
                replacement_sentinel_bytes
            )
            injection_reached = True
            if fsync_wrapper_mode == "raise":
                raise PostPublishEvidenceFsyncPathSubstitution(
                    "first post-publication fsync completed before "
                    "evidence path substitution"
                )
            return
        original_fsync(descriptor)

    monkeypatch.setattr(
        oracle_boot,
        "os",
        _ModuleProxy(os, fsync=substituted_fsync),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_boot,
        "_renameatx",
        tracked_renameatx,
        raising=False,
    )

    raised: BaseException | None = None
    try:
        oracle_boot._write_probe_json(evidence, payload)
    except BaseException as exc:
        raised = exc

    assert publish_completed
    assert injection_reached
    assert 1 <= post_publish_evidence_fsyncs <= fsync_call_budget
    assert 1 <= fsync_calls <= fsync_call_budget
    assert 1 <= rename_calls <= rename_call_budget
    assert raised is not None
    assert not isinstance(raised, AssertionError), raised
    if fsync_wrapper_mode == "raise":
        pending_errors: list[BaseException] = [raised]
        exception_graph: list[BaseException] = []
        while pending_errors:
            current = pending_errors.pop()
            if any(current is candidate for candidate in exception_graph):
                continue
            exception_graph.append(current)
            if current.__cause__ is not None:
                pending_errors.append(current.__cause__)
            if current.__context__ is not None:
                pending_errors.append(current.__context__)
        assert any(
            isinstance(
                candidate,
                PostPublishEvidenceFsyncPathSubstitution,
            )
            or any(
                "PostPublishEvidenceFsyncPathSubstitution" in note
                and "first post-publication fsync completed" in note
                for note in getattr(candidate, "__notes__", ())
            )
            for candidate in exception_graph
        ), exception_graph

    assert not (displaced / "probe.json").exists()
    assert not (evidence / "probe.json").exists()
    assert published_identity is not None
    private_artifacts = [
        path
        for path in displaced.iterdir()
        if path.name != original_sentinel.name
    ]
    assert len(private_artifacts) == 1
    preserved = private_artifacts[0]
    observed = preserved.stat(follow_symlinks=False)
    assert stat.S_ISREG(observed.st_mode)
    assert stat.S_IMODE(observed.st_mode) == 0o600
    assert _dev_inode(observed) == published_identity
    assert preserved.read_bytes() == expected_payload
    assert (displaced / original_sentinel.name).read_bytes() == (
        b"displaced sentinel survives"
    )
    assert {
        path.name for path in evidence.iterdir()
    } == {replacement_sentinel_name}
    assert (evidence / replacement_sentinel_name).read_bytes() == (
        replacement_sentinel_bytes
    )
    assert outside.read_bytes() == b"outside sentinel survives"
