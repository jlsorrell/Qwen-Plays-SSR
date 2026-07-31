"""Fail-closed boot probing and evidence preservation for the SSR oracle."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import subprocess
import sys
import time
from typing import Any

from ssr_env.oracle_install import _RENAME_EXCL, _renameatx, status_install


EXPECTED_ASSEMBLY_SHA256 = (
    "886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564"
)
_TERMINATION_GRACE_SECONDS = 10.0
_PROCESS_GROUP_EXIT_CONFIRM_SECONDS = 1.0
_PROCESS_POLL_SECONDS = 0.01
_PROBE_JSON_DIRECTORY_FSYNC_ATTEMPTS = 3
_MAX_MONITOR_LOG_BYTES = 64 * 1024 * 1024
_REQUIRED_BOOT_MARKERS = (
    "BepInEx 5.4.23.5",
    "Unity v2018.4.25f1",
    "SSR oracle boot probe loaded",
)
_VERSION_BOOT_MARKERS = frozenset(_REQUIRED_BOOT_MARKERS[:2])
_VERSION_TOKEN_BYTES = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    b"abcdefghijklmnopqrstuvwxyz"
    b"0123456789._+-"
)
_BOOT_ERROR_MARKERS = ("DllNotFoundException", "Preloader error")
_CANONICAL_BOOT_LOG = Path("BepInEx/LogOutput.log")
_FALLBACK_BOOT_LOGS = frozenset(
    Path(f"BepInEx/LogOutput.log.{index}") for index in range(1, 5)
)
_BOOT_MARKER_PATTERNS = {
    "BepInEx 5.4.23.5": b"BepInEx 5.4.23.5",
    "Unity v2018.4.25f1": b"Detected Unity version: v2018.4.25f1",
    "SSR oracle boot probe loaded": b"SSR oracle boot probe loaded",
}


class BootProbeError(RuntimeError):
    """Raised when a boot-probe path or artifact is unsafe."""


class _TransientLogChange(RuntimeError):
    """A monitored log changed between descriptor-pinned observations."""


def _note_later_error(
    primary: BaseException,
    label: str,
    later: BaseException,
) -> None:
    try:
        primary.add_note(
            f"{label}: {type(later).__name__}: {later}"
        )
    except BaseException:
        pass


@dataclass(frozen=True, slots=True)
class LogFingerprint:
    path: Path
    file_type: str
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


@dataclass(frozen=True, slots=True)
class BootProbeResult:
    success: bool
    evidence_dir: Path
    moved_logs: tuple[Path, ...]
    copied_logs: tuple[Path, ...]
    markers: tuple[str, ...]
    issues: tuple[str, ...]
    exit_code: int | None


@dataclass(frozen=True, slots=True)
class _AppSignature:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True, slots=True)
class _BootSnapshot:
    assembly_sha256: str
    active_preloader_sha256: str
    installer_healthy: bool
    compatibility_state: str
    app_signature: _AppSignature


@dataclass(frozen=True, slots=True)
class _ConfigSnapshot:
    payload: bytes
    mode: int
    device: int
    inode: int
    size: int
    mtime_ns: int = field(compare=False)


@dataclass(frozen=True, slots=True)
class _MonitorOutcome:
    state: str
    markers: tuple[str, ...]
    errors: tuple[str, ...]
    exit_code: int | None


@dataclass(slots=True)
class _DirectoryHandle:
    fd: int
    device: int
    inode: int
    path: Path

    def close(self) -> None:
        if self.fd >= 0:
            descriptor = self.fd
            self.fd = -1
            os.close(descriptor)


@dataclass(slots=True)
class _ConfigGuard:
    path: Path
    parent: _DirectoryHandle
    name: str
    fd: int
    original: _ConfigSnapshot

    def close(self) -> None:
        primary: BaseException | None = None
        if self.fd >= 0:
            descriptor = self.fd
            self.fd = -1
            try:
                os.close(descriptor)
            except BaseException as exc:
                primary = exc
        try:
            self.parent.close()
        except BaseException as exc:
            if primary is None:
                primary = exc
            else:
                _note_later_error(
                    primary,
                    "config parent close also failed",
                    exc,
                )
        if primary is not None:
            raise primary


@dataclass(slots=True)
class _DiskLoggingConfigGuard:
    bepinex_path: Path
    bepinex: _DirectoryHandle
    config: _DirectoryHandle | None
    path: Path
    name: str
    fd: int
    original: _ConfigSnapshot | None

    def close(self) -> None:
        primary: BaseException | None = None
        if self.fd >= 0:
            descriptor = self.fd
            self.fd = -1
            try:
                os.close(descriptor)
            except BaseException as exc:
                primary = exc
        if self.config is not None:
            try:
                self.config.close()
            except BaseException as exc:
                if primary is None:
                    primary = exc
                else:
                    _note_later_error(
                        primary,
                        "BepInEx config directory close also failed",
                        exc,
                    )
        try:
            self.bepinex.close()
        except BaseException as exc:
            if primary is None:
                primary = exc
            else:
                _note_later_error(
                    primary,
                    "BepInEx directory close also failed",
                    exc,
                )
        if primary is not None:
            raise primary


@dataclass(frozen=True, slots=True)
class _ValidatedBootLogContract:
    canonical_overwrite: bool


@dataclass(slots=True)
class _LauncherGuard:
    path: Path
    parent: _DirectoryHandle
    name: str
    fd: int
    identity: tuple[int, int, int, int, int]
    sha256: str

    def close(self) -> None:
        primary: BaseException | None = None
        if self.fd >= 0:
            descriptor = self.fd
            self.fd = -1
            try:
                os.close(descriptor)
            except BaseException as exc:
                primary = exc
        try:
            self.parent.close()
        except BaseException as exc:
            if primary is None:
                primary = exc
            else:
                _note_later_error(
                    primary,
                    "launcher parent close also failed",
                    exc,
                )
        if primary is not None:
            raise primary


@dataclass(slots=True)
class _StagedProbeJson:
    directory: Path
    directory_handle: _DirectoryHandle
    pending_name: str
    encoded: bytes
    pending_identity: tuple[int, int, int, int, int]
    verifier_fd: int = -1
    committed: bool = False


@dataclass(frozen=True, slots=True)
class _ScannedLog:
    path: Path
    kind: str
    parent: _DirectoryHandle
    name: str
    observed: os.stat_result
    file_type: str


@dataclass(slots=True)
class _LogScan:
    entries: tuple[_ScannedLog, ...]
    handles: tuple[_DirectoryHandle, ...]

    def close(self) -> None:
        for handle in reversed(self.handles):
            handle.close()


def _requested_path(value: object, label: str) -> Path:
    if not isinstance(value, Path):
        raise ValueError(f"{label} must be a Path")
    return Path(os.path.abspath(os.fspath(value)))


def _path_components(path: Path) -> tuple[Path, ...]:
    components: list[Path] = []
    current = path
    while current != current.parent:
        components.append(current)
        current = current.parent
    components.append(current)
    return tuple(reversed(components))


def _validate_no_symlink_components(
    path: Path,
    label: str,
    *,
    allow_missing_leaf: bool = False,
) -> Path:
    absolute = _requested_path(path, label)
    components = _path_components(absolute)
    for index, component in enumerate(components):
        try:
            observed = component.stat(follow_symlinks=False)
        except FileNotFoundError:
            if allow_missing_leaf and index == len(components) - 1:
                return absolute
            raise BootProbeError(f"{label} does not exist: {path}") from None
        if stat.S_ISLNK(observed.st_mode):
            raise BootProbeError(f"{label} contains a symlink: {path}")
        if index != len(components) - 1 and not stat.S_ISDIR(observed.st_mode):
            raise BootProbeError(
                f"{label} parent is not a directory: {component}"
            )
    return absolute


def _validate_directory(path: Path, label: str) -> Path:
    absolute = _validate_no_symlink_components(path, label)
    observed = absolute.stat(follow_symlinks=False)
    if not stat.S_ISDIR(observed.st_mode):
        raise BootProbeError(f"{label} is not a directory: {path}")
    return absolute


def _validate_regular_file(
    path: Path,
    label: str,
    *,
    executable: bool = False,
) -> Path:
    absolute = _validate_no_symlink_components(path, label)
    observed = absolute.stat(follow_symlinks=False)
    if not stat.S_ISREG(observed.st_mode):
        raise BootProbeError(f"{label} is not a regular file: {path}")
    if executable and observed.st_mode & 0o111 == 0:
        raise BootProbeError(f"{label} is not executable: {path}")
    return absolute


def _validate_evidence_root(path: Path) -> tuple[Path, bool]:
    absolute = _requested_path(path, "evidence root")
    try:
        observed = absolute.stat(follow_symlinks=False)
    except FileNotFoundError:
        try:
            _validate_directory(
                absolute.parent,
                "evidence root parent",
            )
        except BootProbeError as exc:
            raise BootProbeError(
                f"evidence root is unsafe: {path}: {exc}"
            ) from exc
        return absolute, False
    _validate_no_symlink_components(absolute, "evidence root")
    if not stat.S_ISDIR(observed.st_mode):
        raise BootProbeError(f"evidence root is not a directory: {path}")
    return absolute, True


def _decode_codesign_stream(payload: bytes, stream: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BootProbeError(
            f"codesign {stream} is not valid UTF-8"
        ) from exc


def _capture_app_signature(app_path: Path) -> _AppSignature:
    app = _validate_directory(app_path, "game app")
    parent = _open_absolute_directory(app.parent, "game app parent")
    app_handle: _DirectoryHandle | None = None
    try:
        observed = os.stat(
            app.name,
            dir_fd=parent.fd,
            follow_symlinks=False,
        )
        app_handle = _open_child_directory(
            parent,
            app.name,
            app,
            observed,
        )
        expected_identity = _stat_identity(observed)
        if _stat_identity(os.fstat(app_handle.fd)) != expected_identity:
            raise BootProbeError(
                f"game app changed before code-signature capture: {app}"
            )
        completed = subprocess.run(
            [
                "codesign",
                "--verify",
                "--deep",
                "--strict",
                "--verbose=1",
                str(app),
            ],
            capture_output=True,
            check=False,
        )
        after = os.stat(
            app.name,
            dir_fd=parent.fd,
            follow_symlinks=False,
        )
        retained_after = os.fstat(app_handle.fd)
        if (
            not stat.S_ISDIR(after.st_mode)
            or _stat_identity(after) != expected_identity
            or _stat_identity(retained_after) != expected_identity
        ):
            raise BootProbeError(
                f"game app changed during code-signature capture: {app}"
            )
        return _AppSignature(
            returncode=completed.returncode,
            stdout=_decode_codesign_stream(completed.stdout, "stdout"),
            stderr=_decode_codesign_stream(completed.stderr, "stderr"),
        )
    finally:
        if app_handle is not None:
            app_handle.close()
        parent.close()


def _sha256_file(path: Path) -> str:
    requested = _requested_path(path, "hash target")
    parent = _open_absolute_directory(
        requested.parent,
        "hash target parent",
    )
    descriptor = -1
    try:
        descriptor = os.open(
            requested.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent.fd,
        )
        observed = os.fstat(descriptor)
        if not stat.S_ISREG(observed.st_mode):
            raise BootProbeError(f"hash target is not a regular file: {path}")
        expected_identity = _stat_identity(observed)
        digests: list[str] = []
        for pass_index in range(2):
            if pass_index:
                os.lseek(descriptor, 0, os.SEEK_SET)
            digest = hashlib.sha256()
            byte_count = 0
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                byte_count += len(chunk)
                digest.update(chunk)
            after = os.fstat(descriptor)
            named = os.stat(
                requested.name,
                dir_fd=parent.fd,
                follow_symlinks=False,
            )
            if (
                _stat_identity(after) != expected_identity
                or _stat_identity(named) != expected_identity
                or byte_count != observed.st_size
            ):
                raise BootProbeError(
                    f"hash target changed while reading: {path}"
                )
            digests.append(digest.hexdigest())
        if digests[0] != digests[1]:
            raise BootProbeError(
                f"hash target content was unstable while reading: {path}"
            )
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        parent.close()
    return digests[0]


def _capture_boot_snapshot(game_root: Path) -> _BootSnapshot:
    game = _validate_directory(game_root, "game root")
    app = _validate_directory(game / "Sausage.app", "game app")
    assembly = _validate_regular_file(
        app
        / "Contents"
        / "Resources"
        / "Data"
        / "Managed"
        / "Assembly-CSharp.dll",
        "game assembly",
    )
    active_preloader = _validate_regular_file(
        game / "BepInEx" / "core" / "BepInEx.Preloader.dll",
        "active preloader",
    )
    install_status = status_install(game)
    compatibility = install_status.preloader_compatibility
    assembly_sha256 = _sha256_file(assembly)
    active_preloader_sha256 = _sha256_file(active_preloader)
    if hasattr(compatibility, "active_sha256"):
        status_active_sha256 = compatibility.active_sha256
        if (
            not isinstance(status_active_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", status_active_sha256) is None
            or status_active_sha256 != active_preloader_sha256
        ):
            raise BootProbeError(
                "active preloader changed relative to installer status"
            )
    return _BootSnapshot(
        assembly_sha256=assembly_sha256,
        active_preloader_sha256=active_preloader_sha256,
        installer_healthy=install_status.healthy,
        compatibility_state=compatibility.state,
        app_signature=_capture_app_signature(app),
    )


def _file_type(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "regular"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISFIFO(mode):
        return "fifo"
    if stat.S_ISSOCK(mode):
        return "socket"
    return "other"


def _is_preloader_log(path: Path) -> bool:
    return path.name.startswith("preloader_") and path.name.endswith(".log")


def _boot_log_kind(relative_path: Path) -> str | None:
    if relative_path == _CANONICAL_BOOT_LOG:
        return "canonical"
    if relative_path in _FALLBACK_BOOT_LOGS:
        return "fallback"
    if _is_preloader_log(relative_path):
        return "preloader"
    return None


_DIRECTORY_OPEN_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _opened_directory(
    descriptor: int,
    path: Path,
) -> _DirectoryHandle:
    opened: _DirectoryHandle | None = None
    try:
        observed = os.fstat(descriptor)
        if not stat.S_ISDIR(observed.st_mode):
            raise BootProbeError(f"not a directory: {path}")
        opened = _DirectoryHandle(
            fd=descriptor,
            device=observed.st_dev,
            inode=observed.st_ino,
            path=path,
        )
        return opened
    except BaseException as primary:
        if opened is not None:
            try:
                opened.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "opened directory close also failed",
                    exc,
                )
        else:
            try:
                os.close(descriptor)
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "directory descriptor close also failed",
                    exc,
                )
        raise


def _duplicate_directory_handle(
    handle: _DirectoryHandle,
) -> _DirectoryHandle:
    descriptor = -1
    duplicate: _DirectoryHandle | None = None
    try:
        descriptor = os.dup(handle.fd)
        observed = os.fstat(descriptor)
        if not stat.S_ISDIR(observed.st_mode):
            raise BootProbeError(f"not a directory: {handle.path}")
        duplicate = _DirectoryHandle(
            fd=descriptor,
            device=observed.st_dev,
            inode=observed.st_ino,
            path=handle.path,
        )
        if (duplicate.device, duplicate.inode) != (
            handle.device,
            handle.inode,
        ):
            raise BootProbeError(
                "retained directory changed while duplicating: "
                f"{handle.path}"
            )
        return duplicate
    except BaseException as primary:
        if duplicate is not None:
            descriptor = -1
            try:
                duplicate.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "duplicated directory close also failed",
                    exc,
                )
        elif descriptor >= 0:
            descriptor_to_close = descriptor
            descriptor = -1
            try:
                os.close(descriptor_to_close)
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "duplicated directory descriptor close also failed",
                    exc,
                )
        raise


def _open_absolute_directory(path: Path, label: str) -> _DirectoryHandle:
    absolute = _requested_path(path, label)
    descriptor = -1
    following_descriptor = -1
    previous_descriptor = -1
    opened_descriptor = -1
    opened: _DirectoryHandle | None = None
    try:
        descriptor = os.open("/", _DIRECTORY_OPEN_FLAGS)
        for part in absolute.parts[1:]:
            following_descriptor = os.open(
                part,
                _DIRECTORY_OPEN_FLAGS,
                dir_fd=descriptor,
            )
            previous_descriptor = descriptor
            descriptor = -1
            os.close(previous_descriptor)
            previous_descriptor = -1
            descriptor = following_descriptor
            following_descriptor = -1
        opened_descriptor = descriptor
        descriptor = -1
        try:
            opened = _opened_directory(opened_descriptor, absolute)
        except BaseException:
            opened_descriptor = -1
            raise
        return opened
    except BaseException as primary:
        if opened is not None:
            opened_descriptor = -1
            try:
                opened.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "absolute directory close also failed",
                    exc,
                )
        closed_descriptors: set[int] = set()
        for cleanup_label, owned_descriptor in (
            (
                "opened absolute directory descriptor close also failed",
                opened_descriptor,
            ),
            (
                "following directory descriptor close also failed",
                following_descriptor,
            ),
            (
                "previous directory descriptor close also failed",
                previous_descriptor,
            ),
            (
                "current directory descriptor close also failed",
                descriptor,
            ),
        ):
            if (
                owned_descriptor < 0
                or owned_descriptor in closed_descriptors
            ):
                continue
            closed_descriptors.add(owned_descriptor)
            try:
                os.close(owned_descriptor)
            except BaseException as exc:
                _note_later_error(primary, cleanup_label, exc)
        if isinstance(primary, OSError):
            raise BootProbeError(
                f"cannot open {label} without following symlinks: "
                f"{path}: {primary}"
            ) from primary
        raise


def _open_child_directory(
    parent: _DirectoryHandle,
    name: str,
    path: Path,
    expected: os.stat_result,
) -> _DirectoryHandle:
    descriptor = -1
    child: _DirectoryHandle | None = None
    try:
        try:
            descriptor = os.open(
                name,
                _DIRECTORY_OPEN_FLAGS,
                dir_fd=parent.fd,
            )
        except OSError as exc:
            raise BootProbeError(
                "cannot open directory without following symlinks: "
                f"{path}: {exc}"
            ) from exc
        try:
            child = _opened_directory(descriptor, path)
        except BaseException:
            descriptor = -1
            raise
        if (
            child.device != expected.st_dev
            or child.inode != expected.st_ino
        ):
            raise BootProbeError(f"directory changed during scan: {path}")
        return child
    except BaseException as primary:
        if child is not None:
            descriptor = -1
            try:
                child.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "child directory close also failed",
                    exc,
                )
        elif descriptor >= 0:
            try:
                os.close(descriptor)
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "child directory descriptor close also failed",
                    exc,
                )
        raise


def _scan_preloader_logs(
    game_root: Path,
) -> _LogScan:
    game = _requested_path(game_root, "game root")
    root: _DirectoryHandle | None = None
    pending_handle: _DirectoryHandle | None = None
    handles: list[_DirectoryHandle] = []
    entries: list[_ScannedLog] = []

    def visit(directory: _DirectoryHandle) -> None:
        nonlocal pending_handle
        try:
            with os.scandir(directory.fd) as discovered:
                children = sorted(discovered, key=lambda entry: entry.name)
        except OSError as exc:
            raise BootProbeError(
                f"cannot scan game root for monitored boot logs: "
                f"{directory.path}: {exc}"
            ) from exc
        for child_entry in children:
            candidate = directory.path / child_entry.name
            try:
                observed = os.stat(
                    child_entry.name,
                    dir_fd=directory.fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise BootProbeError(
                    f"cannot inspect monitored boot log scan entry: "
                    f"{candidate}: {exc}"
                ) from exc
            file_type = _file_type(observed.st_mode)
            relative_path = candidate.relative_to(game)
            log_kind = _boot_log_kind(relative_path)
            if log_kind is not None:
                entries.append(
                    _ScannedLog(
                        path=candidate,
                        kind=log_kind,
                        parent=directory,
                        name=child_entry.name,
                        observed=observed,
                        file_type=file_type,
                    )
                )
            if file_type == "directory":
                pending_handle = _open_child_directory(
                    directory,
                    child_entry.name,
                    candidate,
                    observed,
                )
                handles.append(pending_handle)
                child = pending_handle
                pending_handle = None
                visit(child)

    try:
        root = _open_absolute_directory(game, "game root")
        handles.append(root)
        visit(root)
        entries.sort(
            key=lambda entry: entry.path.relative_to(game).as_posix()
        )
        return _LogScan(tuple(entries), tuple(handles))
    except BaseException as primary:
        if (
            pending_handle is not None
            and all(
                pending_handle is not handle for handle in handles
            )
        ):
            try:
                pending_handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "pending preloader scan directory close also failed",
                    exc,
                )
        for handle in reversed(handles):
            try:
                handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "preloader scan directory close also failed",
                    exc,
                )
        if (
            root is not None
            and all(root is not handle for handle in handles)
        ):
            try:
                root.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "preloader scan root close also failed",
                    exc,
                )
        raise


def _fingerprint_scanned(entry: _ScannedLog) -> LogFingerprint:
    try:
        descriptor = os.open(
            entry.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=entry.parent.fd,
        )
    except OSError as exc:
        raise BootProbeError(
            f"cannot open monitored boot log without following symlinks: "
            f"{entry.path}: {exc}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        expected_identity = (
            entry.observed.st_dev,
            entry.observed.st_ino,
            entry.observed.st_mode,
            entry.observed.st_size,
            entry.observed.st_mtime_ns,
        )
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_size,
            before.st_mtime_ns,
        )
        if (
            not stat.S_ISREG(before.st_mode)
            or before_identity != expected_identity
        ):
            raise BootProbeError(
                f"monitored boot log changed before hashing: {entry.path}"
            )
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        named = os.stat(
            entry.name,
            dir_fd=entry.parent.fd,
            follow_symlinks=False,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_size,
            after.st_mtime_ns,
        )
        named_identity = (
            named.st_dev,
            named.st_ino,
            named.st_mode,
            named.st_size,
            named.st_mtime_ns,
        )
        if (
            after_identity != expected_identity
            or named_identity != expected_identity
        ):
            raise BootProbeError(
                f"monitored boot log changed while hashing: {entry.path}"
            )
        return LogFingerprint(
            path=entry.path,
            file_type="regular",
            inode=before.st_ino,
            size=before.st_size,
            mtime_ns=before.st_mtime_ns,
            sha256=digest.hexdigest(),
        )
    finally:
        os.close(descriptor)


def _read_monitored_log(entry: _ScannedLog) -> bytes:
    try:
        descriptor = os.open(
            entry.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=entry.parent.fd,
        )
    except OSError as exc:
        raise _TransientLogChange(str(entry.path)) from exc
    try:
        before = os.fstat(descriptor)
        expected_identity = _stat_identity(entry.observed)
        if before.st_size > _MAX_MONITOR_LOG_BYTES:
            raise BootProbeError(
                f"monitored boot log exceeds byte limit: {entry.path}"
            )
        if (
            not stat.S_ISREG(before.st_mode)
            or _stat_identity(before) != expected_identity
        ):
            raise _TransientLogChange(str(entry.path))
        chunks: list[bytes] = []
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            byte_count += len(chunk)
            if byte_count > _MAX_MONITOR_LOG_BYTES:
                raise BootProbeError(
                    f"monitored boot log exceeds byte limit: {entry.path}"
                )
            chunks.append(chunk)
        after = os.fstat(descriptor)
        try:
            named = os.stat(
                entry.name,
                dir_fd=entry.parent.fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise _TransientLogChange(str(entry.path)) from exc
        if (
            _stat_identity(after) != expected_identity
            or _stat_identity(named) != expected_identity
            or byte_count != before.st_size
        ):
            raise _TransientLogChange(str(entry.path))
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _payload_contains_boot_marker(payload: bytes, marker: str) -> bool:
    encoded = _BOOT_MARKER_PATTERNS[marker]
    if marker not in _VERSION_BOOT_MARKERS:
        return encoded in payload
    offset = 0
    while True:
        found = payload.find(encoded, offset)
        if found < 0:
            return False
        end = found + len(encoded)
        if (
            (found == 0 or payload[found - 1] not in _VERSION_TOKEN_BYTES)
            and (
                end == len(payload)
                or payload[end] not in _VERSION_TOKEN_BYTES
            )
        ):
            return True
        offset = found + 1


def _observe_boot_logs(
    game_root: Path,
    before: tuple[LogFingerprint, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    baseline = {fingerprint.path: fingerprint for fingerprint in before}
    scan = _scan_preloader_logs(game_root)
    try:
        unsafe = tuple(
            f"unsafe {entry.file_type} monitored boot log: {entry.path}"
            for entry in scan.entries
            if entry.file_type != "regular"
        )
        payloads: list[bytes] = []
        for entry in scan.entries:
            if entry.file_type != "regular":
                continue
            if entry.observed.st_size > _MAX_MONITOR_LOG_BYTES:
                raise BootProbeError(
                    f"monitored boot log exceeds byte limit: {entry.path}"
                )
            prior = baseline.get(entry.path)
            if prior is not None:
                try:
                    current = _fingerprint_scanned(entry)
                except (BootProbeError, OSError) as exc:
                    raise _TransientLogChange(str(entry.path)) from exc
                if _fingerprint_matches(prior, current):
                    continue
            payloads.append(_read_monitored_log(entry))
    finally:
        scan.close()
    markers = tuple(
        marker
        for marker in _REQUIRED_BOOT_MARKERS
        if any(
            _payload_contains_boot_marker(payload, marker)
            for payload in payloads
        )
    )
    errors = unsafe + tuple(
        marker
        for marker in _BOOT_ERROR_MARKERS
        if any(marker.encode("ascii") in payload for payload in payloads)
    )
    return markers, errors


def _wait_for_markers(
    process: subprocess.Popen[bytes],
    game_root: Path,
    before: tuple[LogFingerprint, ...],
    timeout_seconds: int,
) -> _MonitorOutcome:
    deadline = time.monotonic() + timeout_seconds
    markers: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    while True:
        observation_stable = True
        try:
            markers, errors = _observe_boot_logs(game_root, before)
        except _TransientLogChange:
            observation_stable = False
        except BootProbeError as exc:
            errors = (str(exc),)

        exit_code = process.poll()
        if not observation_stable and exit_code is not None:
            try:
                markers, errors = _observe_boot_logs(game_root, before)
            except _TransientLogChange:
                errors = ("monitored boot log was unstable at launcher exit",)
            except BootProbeError as exc:
                errors = (str(exc),)
            observation_stable = True
        if observation_stable:
            if errors:
                return _MonitorOutcome("error", markers, errors, exit_code)
            if exit_code is not None:
                return _MonitorOutcome(
                    "early_exit",
                    markers,
                    (),
                    exit_code,
                )
            if markers == _REQUIRED_BOOT_MARKERS:
                return _MonitorOutcome("markers", markers, (), None)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            if not observation_stable:
                try:
                    markers, errors = _observe_boot_logs(game_root, before)
                except _TransientLogChange:
                    errors = (
                        "monitored boot log remained unstable at deadline",
                    )
                except BootProbeError as exc:
                    errors = (str(exc),)
            exit_code = process.poll()
            if errors:
                return _MonitorOutcome("error", markers, errors, exit_code)
            if exit_code is not None:
                return _MonitorOutcome(
                    "early_exit",
                    markers,
                    (),
                    exit_code,
                )
            if markers == _REQUIRED_BOOT_MARKERS:
                return _MonitorOutcome("markers", markers, (), None)
            return _MonitorOutcome("timeout", markers, (), None)
        time.sleep(min(_PROCESS_POLL_SECONDS, remaining))


def fingerprint_preloader_logs(
    game_root: Path,
) -> tuple[LogFingerprint, ...]:
    game = _validate_directory(game_root, "game root")
    scan = _scan_preloader_logs(game)
    try:
        unsafe = next(
            (
                entry
                for entry in scan.entries
                if entry.file_type != "regular"
            ),
            None,
        )
        if unsafe is not None:
            raise BootProbeError(
                f"unsafe {unsafe.file_type} monitored boot log: {unsafe.path}"
            )
        return tuple(
            _fingerprint_scanned(entry) for entry in scan.entries
        )
    finally:
        scan.close()


def _fingerprint_regular_preloader_logs(
    game_root: Path,
) -> tuple[LogFingerprint, ...]:
    game = _validate_directory(game_root, "game root")
    scan = _scan_preloader_logs(game)
    try:
        return tuple(
            _fingerprint_scanned(entry)
            for entry in scan.entries
            if entry.file_type == "regular"
        )
    finally:
        scan.close()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _random_token() -> str:
    return secrets.token_hex(16)


def _random_probe_json_token() -> str:
    return secrets.token_hex(16)


def _validate_baseline(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
) -> dict[Path, LogFingerprint]:
    if not isinstance(before, tuple):
        raise ValueError("before must be a tuple of LogFingerprint records")
    baseline: dict[Path, LogFingerprint] = {}
    for fingerprint in before:
        if not isinstance(fingerprint, LogFingerprint):
            raise ValueError("before contains a non-LogFingerprint record")
        path = _requested_path(fingerprint.path, "baseline log path")
        if path != fingerprint.path or not path.is_relative_to(game_root):
            raise BootProbeError(
                f"baseline log path is outside game root: {fingerprint.path}"
            )
        if _boot_log_kind(path.relative_to(game_root)) is None:
            raise BootProbeError(f"invalid baseline log name: {path}")
        if fingerprint.file_type != "regular":
            raise BootProbeError(f"invalid baseline log type: {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint.sha256):
            raise BootProbeError(f"invalid baseline log hash: {path}")
        if path in baseline:
            raise BootProbeError(f"duplicate baseline log path: {path}")
        baseline[path] = fingerprint
    return baseline


def _fingerprint_matches(
    before: LogFingerprint,
    after: LogFingerprint,
) -> bool:
    return (
        before.file_type == after.file_type
        and before.inode == after.inode
        and before.size == after.size
        and before.mtime_ns == after.mtime_ns
        and before.sha256 == after.sha256
    )


def _post_shutdown_inventory_mismatches(
    expected: dict[Path, LogFingerprint],
    current_regular: dict[Path, LogFingerprint],
    current_paths: set[Path],
) -> tuple[str, ...]:
    mismatches: list[str] = []
    for path in sorted(expected):
        current = current_regular.get(path)
        if current is None:
            mutation = "changed" if path in current_paths else "removed"
            mismatches.append(
                f"post-shutdown preloader log inventory {mutation}: {path}"
            )
        elif not _fingerprint_matches(expected[path], current):
            mismatches.append(
                f"post-shutdown preloader log inventory changed: {path}"
            )
    for path in sorted(current_paths - expected.keys()):
        mismatches.append(
            f"post-shutdown preloader log inventory added: {path}"
        )
    return tuple(mismatches)


def _allocate_evidence_directory(
    evidence_root: Path,
    root_exists: bool,
) -> tuple[Path, _DirectoryHandle]:
    moment = _utc_now()
    if moment.tzinfo is None:
        raise BootProbeError("evidence timestamp must be timezone-aware")
    timestamp = moment.astimezone(timezone.utc).strftime(
        "%Y%m%dT%H%M%S.%fZ"
    )

    def validated_token() -> str:
        token = _random_token()
        if _TOKEN_PATTERN.fullmatch(token) is None:
            raise BootProbeError(f"invalid evidence token: {token!r}")
        return token

    token = validated_token()
    evidence_root_handle: _DirectoryHandle | None = None
    parent_handle: _DirectoryHandle | None = None
    evidence_handle: _DirectoryHandle | None = None
    try:
        if root_exists:
            evidence_root_handle = _open_absolute_directory(
                evidence_root,
                "evidence root",
            )
        else:
            parent_handle = _open_absolute_directory(
                evidence_root.parent,
                "evidence root parent",
            )
            try:
                os.mkdir(
                    evidence_root.name,
                    0o700,
                    dir_fd=parent_handle.fd,
                )
            except FileExistsError as exc:
                raise BootProbeError(
                    f"evidence root appeared during allocation: "
                    f"{evidence_root}"
                ) from exc
            os.fsync(parent_handle.fd)
            observed_root = os.stat(
                evidence_root.name,
                dir_fd=parent_handle.fd,
                follow_symlinks=False,
            )
            evidence_root_handle = _open_child_directory(
                parent_handle,
                evidence_root.name,
                evidence_root,
                observed_root,
            )

        for attempt in range(128):
            evidence_name = f"{timestamp}-{token}"
            evidence_dir = evidence_root / evidence_name
            try:
                os.mkdir(
                    evidence_name,
                    0o700,
                    dir_fd=evidence_root_handle.fd,
                )
            except FileExistsError:
                if attempt == 127:
                    break
                token = validated_token()
                continue
            os.fsync(evidence_root_handle.fd)
            observed = os.stat(
                evidence_name,
                dir_fd=evidence_root_handle.fd,
                follow_symlinks=False,
            )
            evidence_handle = _open_child_directory(
                evidence_root_handle,
                evidence_name,
                evidence_dir,
                observed,
            )
            break
        if evidence_handle is None:
            raise BootProbeError(
                "could not allocate unique boot-evidence directory "
                "after 128 attempts"
            )
        if evidence_root_handle is not None:
            evidence_root_handle.close()
            evidence_root_handle = None
        if parent_handle is not None:
            parent_handle.close()
            parent_handle = None
        return evidence_dir, evidence_handle
    except BaseException as primary:
        if evidence_handle is not None:
            try:
                evidence_handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "allocated evidence directory close also failed",
                    exc,
                )
        if evidence_root_handle is not None:
            try:
                evidence_root_handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "evidence root directory close also failed",
                    exc,
                )
        if parent_handle is not None:
            try:
                parent_handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "evidence root parent close also failed",
                    exc,
                )
        raise


def _make_evidence_parents(
    evidence_dir: _DirectoryHandle,
    relative_parent: Path,
    known_directories: dict[Path, tuple[int, int]],
) -> _DirectoryHandle:
    current: _DirectoryHandle | None = None
    pending: _DirectoryHandle | None = None
    try:
        current = _duplicate_directory_handle(evidence_dir)
        for part in relative_parent.parts:
            child_path = current.path / part
            created = False
            try:
                os.mkdir(part, 0o700, dir_fd=current.fd)
            except FileExistsError:
                known_identity = known_directories.get(child_path)
                if known_identity is None:
                    raise BootProbeError(
                        f"unowned evidence parent collision: {child_path}"
                    ) from None
                observed = os.stat(
                    part,
                    dir_fd=current.fd,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISDIR(observed.st_mode)
                    or (observed.st_dev, observed.st_ino)
                    != known_identity
                ):
                    raise BootProbeError(
                        f"unsafe evidence parent collision: {child_path}"
                    ) from None
            else:
                created = True
                os.fsync(current.fd)
                observed = os.stat(
                    part,
                    dir_fd=current.fd,
                    follow_symlinks=False,
                )
            pending = _open_child_directory(
                current,
                part,
                child_path,
                observed,
            )
            if created:
                known_directories[child_path] = (
                    pending.device,
                    pending.inode,
                )
            current.close()
            current = pending
            pending = None
        return current
    except BaseException as primary:
        if pending is not None and pending is not current:
            try:
                pending.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "pending evidence parent close also failed",
                    exc,
                )
        if current is not None:
            try:
                current.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "evidence parent close also failed",
                    exc,
                )
        raise


def _stat_identity(observed: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_size,
        observed.st_mtime_ns,
    )


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
        mtime_ns=observed.st_mtime_ns,
    )


def _read_config_snapshot(
    descriptor: int,
    parent: _DirectoryHandle,
    name: str,
    path: Path,
) -> _ConfigSnapshot:
    snapshot = _read_retained_config_snapshot(descriptor, path)
    observed = os.fstat(descriptor)
    named = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    if _stat_identity(named) != _stat_identity(observed):
        raise BootProbeError(f"config changed after being read: {path}")
    return snapshot


def _parse_bepinex_disk_logging(payload: bytes, path: Path) -> None:
    def reject(detail: str) -> None:
        raise BootProbeError(
            f"invalid BepInEx disk logging config: {path}: {detail}"
        )

    if payload.startswith(b"\xef\xbb\xbf"):
        payload = payload[3:]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BootProbeError(
            f"invalid BepInEx disk logging config UTF-8: {path}"
        ) from exc
    if "\x00" in text:
        reject("NUL byte")
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        reject("bare carriage return")
    if "\ufeff" in text:
        reject("embedded UTF-8 BOM")

    disk_section_count = 0
    console_section_count = 0
    disk_values: dict[str, str] = {}
    console_levels: str | None = None
    current_section: str | None = None
    section_targets = {
        "logging.disk": "Logging.Disk",
        "logging.console": "Logging.Console",
    }
    disk_key_targets = {
        "enabled": "Enabled",
        "appendlog": "AppendLog",
        "loglevels": "LogLevels",
    }

    for line_number, line in enumerate(text.split("\n"), 1):
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue
        if "#" in trimmed:
            reject(f"inline comment on line {line_number}")
        if trimmed.startswith("[") or trimmed.endswith("]"):
            if (
                not trimmed.startswith("[")
                or not trimmed.endswith("]")
                or trimmed.count("[") != 1
                or trimmed.count("]") != 1
            ):
                reject(f"malformed section on line {line_number}")
            section_name = trimmed[1:-1]
            if not section_name:
                reject(f"empty section on line {line_number}")
            normalized = re.sub(r"\s+", "", section_name).casefold()
            target = section_targets.get(normalized)
            if target is not None and section_name != target:
                reject(f"section-name lookalike on line {line_number}")
            current_section = section_name
            if current_section == "Logging.Disk":
                disk_section_count += 1
                if disk_section_count != 1:
                    reject("duplicate [Logging.Disk] section")
            elif current_section == "Logging.Console":
                console_section_count += 1
                if console_section_count != 1:
                    reject("duplicate [Logging.Console] section")
            continue

        if "=" not in trimmed:
            reject(f"malformed key line {line_number}")
        raw_key, value = trimmed.split("=", 1)
        key = raw_key.strip()
        if not key:
            reject(f"empty key on line {line_number}")
        relevant_targets = (
            disk_key_targets
            if current_section == "Logging.Disk"
            else {"loglevels": "LogLevels"}
            if current_section == "Logging.Console"
            else {}
        )
        normalized_key = re.sub(r"\s+", "", key).casefold()
        target_key = relevant_targets.get(normalized_key)
        if target_key is not None and key != target_key:
            reject(f"key-name lookalike on line {line_number}")
        if (
            current_section == "Logging.Disk"
            and key in disk_key_targets.values()
        ):
            if key in disk_values:
                reject(f"duplicate [Logging.Disk] {key} key")
            disk_values[key] = value.strip()
        elif current_section == "Logging.Console" and key == "LogLevels":
            if console_levels is not None:
                reject("duplicate [Logging.Console] LogLevels key")
            console_levels = value.strip()

    if disk_section_count != 1:
        reject("requires exactly one [Logging.Disk] section")
    if set(disk_values) != {"Enabled", "AppendLog", "LogLevels"}:
        reject(
            "requires exactly one Enabled, AppendLog, and LogLevels "
            "disk key"
        )
    if disk_values["Enabled"].casefold() != "true":
        reject("[Logging.Disk] Enabled must be true")
    if disk_values["AppendLog"].casefold() != "false":
        reject("[Logging.Disk] AppendLog must be false")

    required_levels = {"fatal", "error", "warning", "message", "info"}
    allowed_levels = required_levels | {"debug"}

    def validate_levels(value: str, section: str) -> None:
        levels = [level.strip().casefold() for level in value.split(",")]
        if (
            any(not level for level in levels)
            or len(set(levels)) != len(levels)
            or (
                levels != ["all"]
                and (
                    not set(levels).issubset(allowed_levels)
                    or not required_levels.issubset(levels)
                )
            )
        ):
            reject(f"invalid {section} LogLevels")

    validate_levels(disk_values["LogLevels"], "[Logging.Disk]")
    if console_levels is not None:
        validate_levels(console_levels, "[Logging.Console]")


def _open_bepinex_disk_logging_guard(
    game_root: Path,
) -> _DiskLoggingConfigGuard:
    game = _requested_path(game_root, "game root")
    bepinex_path = game / "BepInEx"
    config_path = bepinex_path / "config"
    path = config_path / "BepInEx.cfg"
    bepinex: _DirectoryHandle | None = None
    config: _DirectoryHandle | None = None
    descriptor = -1
    guard: _DiskLoggingConfigGuard | None = None
    try:
        bepinex = _open_absolute_directory(bepinex_path, "BepInEx directory")
        try:
            config_observed = os.stat(
                "config",
                dir_fd=bepinex.fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise BootProbeError(
                    "cannot inspect BepInEx config directory: "
                    f"{config_path}: {exc}"
                ) from exc
            guard = _DiskLoggingConfigGuard(
                bepinex_path,
                bepinex,
                None,
                path,
                path.name,
                -1,
                None,
            )
            bepinex = None
            return guard
        if not stat.S_ISDIR(config_observed.st_mode):
            raise BootProbeError(
                f"BepInEx config path is not a directory: {config_path}"
            )
        config = _open_child_directory(
            bepinex,
            "config",
            config_path,
            config_observed,
        )
        try:
            leaf_observed = os.stat(
                path.name,
                dir_fd=config.fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise BootProbeError(
                    "cannot inspect BepInEx disk logging config: "
                    f"{path}: {exc}"
                ) from exc
            guard = _DiskLoggingConfigGuard(
                bepinex_path,
                bepinex,
                config,
                path,
                path.name,
                -1,
                None,
            )
            bepinex = None
            config = None
            return guard
        if not stat.S_ISREG(leaf_observed.st_mode):
            raise BootProbeError(
                f"BepInEx disk logging config is not a regular file: {path}"
            )
        descriptor = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=config.fd,
        )
        original = _read_config_snapshot(
            descriptor,
            config,
            path.name,
            path,
        )
        _parse_bepinex_disk_logging(original.payload, path)
        guard = _DiskLoggingConfigGuard(
            bepinex_path,
            bepinex,
            config,
            path,
            path.name,
            descriptor,
            original,
        )
        descriptor = -1
        bepinex = None
        config = None
        return guard
    except BaseException as primary:
        if guard is not None:
            try:
                guard.close()
            except BaseException as close_error:
                _note_later_error(
                    primary,
                    "BepInEx disk logging guard close also failed",
                    close_error,
                )
        else:
            if descriptor >= 0:
                owned_descriptor = descriptor
                descriptor = -1
                try:
                    os.close(owned_descriptor)
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "BepInEx config descriptor close also failed",
                        close_error,
                    )
            if config is not None:
                owned_config = config
                config = None
                try:
                    owned_config.close()
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "BepInEx config directory close also failed",
                        close_error,
                    )
            if bepinex is not None:
                owned_bepinex = bepinex
                bepinex = None
                try:
                    owned_bepinex.close()
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "BepInEx directory close also failed",
                        close_error,
                    )
        if isinstance(primary, OSError):
            raise BootProbeError(
                "cannot open BepInEx disk logging config without following "
                f"symlinks: {path}: {primary}"
            ) from primary
        raise


def _verify_and_close_bepinex_disk_logging_guard(
    guard: _DiskLoggingConfigGuard,
) -> _ValidatedBootLogContract:
    try:
        _verify_pinned_directory_path(
            guard.bepinex_path,
            guard.bepinex,
            "BepInEx directory before launch",
        )
        if guard.config is None:
            try:
                os.stat(
                    "config",
                    dir_fd=guard.bepinex.fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise BootProbeError(
                        "cannot revalidate absent BepInEx config directory: "
                        f"{guard.path.parent}: {exc}"
                    ) from exc
            else:
                raise BootProbeError(
                    "BepInEx config directory appeared before launch: "
                    f"{guard.path.parent}"
                )
        else:
            config_named = os.stat(
                "config",
                dir_fd=guard.bepinex.fd,
                follow_symlinks=False,
            )
            config_retained = os.fstat(guard.config.fd)
            if (
                not stat.S_ISDIR(config_named.st_mode)
                or (config_named.st_dev, config_named.st_ino)
                != (guard.config.device, guard.config.inode)
                or (config_retained.st_dev, config_retained.st_ino)
                != (guard.config.device, guard.config.inode)
            ):
                raise BootProbeError(
                    "BepInEx config directory changed before launch: "
                    f"{guard.path.parent}"
                )
            _verify_pinned_directory_path(
                guard.path.parent,
                guard.config,
                "BepInEx config directory before launch",
            )
            if guard.original is None:
                try:
                    os.stat(
                        guard.name,
                        dir_fd=guard.config.fd,
                        follow_symlinks=False,
                    )
                except OSError as exc:
                    if exc.errno != errno.ENOENT:
                        raise BootProbeError(
                            "cannot revalidate absent BepInEx disk logging "
                            f"config: {guard.path}: {exc}"
                        ) from exc
                else:
                    raise BootProbeError(
                        "BepInEx disk logging config appeared before launch: "
                        f"{guard.path}"
                    )
            else:
                reread = _read_config_snapshot(
                    guard.fd,
                    guard.config,
                    guard.name,
                    guard.path,
                )
                original = guard.original
                if (
                    reread.payload != original.payload
                    or reread.mode != original.mode
                    or reread.device != original.device
                    or reread.inode != original.inode
                    or reread.size != original.size
                    or reread.mtime_ns != original.mtime_ns
                ):
                    raise BootProbeError(
                        "BepInEx disk logging config changed before launch: "
                        f"{guard.path}"
                    )
                _parse_bepinex_disk_logging(reread.payload, guard.path)
    except OSError as exc:
        raise BootProbeError(
            "cannot revalidate BepInEx disk logging config: "
            f"{guard.path}: {exc}"
        ) from exc
    guard.close()
    return _ValidatedBootLogContract(canonical_overwrite=True)


def _open_config_guard(config_path: Path) -> _ConfigGuard:
    config = _validate_regular_file(config_path, "config")
    parent: _DirectoryHandle | None = None
    descriptor = -1
    guard: _ConfigGuard | None = None
    try:
        parent = _open_absolute_directory(config.parent, "config parent")
        descriptor = os.open(
            config.name,
            os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent.fd,
        )
        original = _read_config_snapshot(
            descriptor,
            parent,
            config.name,
            config,
        )
        guard = _ConfigGuard(
            path=config,
            parent=parent,
            name=config.name,
            fd=descriptor,
            original=original,
        )
        descriptor = -1
        parent = None
        return guard
    except BaseException as primary:
        if guard is not None:
            try:
                guard.close()
            except BaseException as close_error:
                _note_later_error(
                    primary,
                    "config guard close also failed",
                    close_error,
                )
        else:
            if descriptor >= 0:
                owned_descriptor = descriptor
                descriptor = -1
                try:
                    os.close(owned_descriptor)
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "config descriptor close also failed",
                        close_error,
                    )
            if parent is not None:
                owned_parent = parent
                parent = None
                try:
                    owned_parent.close()
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "config parent close also failed",
                        close_error,
                    )
        raise


def _require_initial_off_config(guard: _ConfigGuard) -> None:
    try:
        text = guard.original.payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BootProbeError(
            f"config is not valid UTF-8: {guard.path}"
        ) from exc
    lines = text.splitlines()
    oracle_headers = [
        index
        for index, line in enumerate(lines)
        if line.strip().casefold() == "[oracle]"
    ]
    if (
        len(oracle_headers) != 1
        or lines[oracle_headers[0]] != "[Oracle]"
    ):
        raise BootProbeError(
            f"config must contain one exact [Oracle] section: {guard.path}"
        )
    section: list[str] = []
    for line in lines[oracle_headers[0] + 1 :]:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            break
        section.append(line)
    mode_assignments = [
        tuple(part.strip() for part in line.split("=", 1))
        for line in section
        if "=" in line
        and line.split("=", 1)[0].strip().casefold() == "mode"
    ]
    if mode_assignments != [("Mode", "off")]:
        raise BootProbeError(
            "config [Oracle] section must contain exactly one "
            f"case-sensitive Mode assignment set to off: {guard.path}"
        )


def _verify_current_config_path_identity(guard: _ConfigGuard) -> None:
    current_parent = _open_absolute_directory(
        guard.path.parent,
        "config parent at use",
    )
    descriptor = -1
    try:
        if (current_parent.device, current_parent.inode) != (
            guard.parent.device,
            guard.parent.inode,
        ):
            raise BootProbeError(
                f"config parent identity changed before use: {guard.path}"
            )
        descriptor = os.open(
            guard.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=current_parent.fd,
        )
        retained_before = os.fstat(guard.fd)
        current = os.fstat(descriptor)
        named = os.stat(
            guard.name,
            dir_fd=current_parent.fd,
            follow_symlinks=False,
        )
        retained_after = os.fstat(guard.fd)
        expected = _stat_identity(retained_before)
        if (
            not stat.S_ISREG(current.st_mode)
            or _stat_identity(current) != expected
            or _stat_identity(named) != expected
            or _stat_identity(retained_after) != expected
        ):
            raise BootProbeError(
                f"config path identity changed before use: {guard.path}"
            )
    except OSError as exc:
        raise BootProbeError(
            f"cannot verify config path before use: {guard.path}: {exc}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        current_parent.close()


def _verify_config_guard_unchanged(guard: _ConfigGuard) -> None:
    _verify_current_config_path_identity(guard)
    if (
        _read_config_snapshot(
            guard.fd,
            guard.parent,
            guard.name,
            guard.path,
        )
        != guard.original
    ):
        raise BootProbeError(f"config changed before use: {guard.path}")
    _verify_current_config_path_identity(guard)


def _restore_config_guard(guard: _ConfigGuard) -> None:
    current = _read_retained_config_snapshot(guard.fd, guard.path)
    original = guard.original
    if (current.device, current.inode) != (
        original.device,
        original.inode,
    ):
        raise BootProbeError(
            f"config identity changed before restore: {guard.path}"
        )
    if (
        current.payload != original.payload
        or current.mode != original.mode
        or current.size != original.size
    ):
        os.lseek(guard.fd, 0, os.SEEK_SET)
        os.ftruncate(guard.fd, 0)
        view = memoryview(original.payload)
        while view:
            written = os.write(guard.fd, view)
            if written <= 0:
                raise OSError("short write while restoring config")
            view = view[written:]
        os.fchmod(guard.fd, original.mode)
        os.fsync(guard.fd)
    restored = _read_retained_config_snapshot(guard.fd, guard.path)
    if restored != original:
        raise BootProbeError(
            f"config was not restored exactly: {guard.path}"
        )
    os.fsync(guard.parent.fd)
    _verify_current_config_path_identity(guard)


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


def _hash_retained_regular(
    descriptor: int,
    expected_identity: tuple[int, int, int, int, int],
    path: Path,
) -> str:
    digests: list[str] = []
    for _ in range(2):
        os.lseek(descriptor, 0, os.SEEK_SET)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or _stat_identity(before) != expected_identity
        ):
            raise BootProbeError(f"launcher identity changed: {path}")
        digest = hashlib.sha256()
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            byte_count += len(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (
            _stat_identity(after) != expected_identity
            or byte_count != before.st_size
        ):
            raise BootProbeError(f"launcher changed while being read: {path}")
        digests.append(digest.hexdigest())
    if digests[0] != digests[1]:
        raise BootProbeError(f"launcher content was unstable: {path}")
    return digests[0]


def _open_launcher_guard(launcher_path: Path) -> _LauncherGuard:
    launcher = _validate_regular_file(
        launcher_path,
        "launcher",
        executable=True,
    )
    parent: _DirectoryHandle | None = None
    descriptor = -1
    guard: _LauncherGuard | None = None
    try:
        parent = _open_absolute_directory(launcher.parent, "launcher parent")
        descriptor = os.open(
            launcher.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent.fd,
        )
        retained = os.fstat(descriptor)
        named = os.stat(
            launcher.name,
            dir_fd=parent.fd,
            follow_symlinks=False,
        )
        identity = _stat_identity(retained)
        if (
            not stat.S_ISREG(retained.st_mode)
            or retained.st_mode & 0o111 == 0
            or _stat_identity(named) != identity
        ):
            raise BootProbeError(f"launcher is not a stable executable: {launcher}")
        digest = _hash_retained_regular(descriptor, identity, launcher)
        guard = _LauncherGuard(
            path=launcher,
            parent=parent,
            name=launcher.name,
            fd=descriptor,
            identity=identity,
            sha256=digest,
        )
        descriptor = -1
        parent = None
        return guard
    except BaseException as primary:
        if guard is not None:
            try:
                guard.close()
            except BaseException as close_error:
                _note_later_error(
                    primary,
                    "launcher guard close also failed",
                    close_error,
                )
        else:
            if descriptor >= 0:
                owned_descriptor = descriptor
                descriptor = -1
                try:
                    os.close(owned_descriptor)
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "launcher descriptor close also failed",
                        close_error,
                    )
            if parent is not None:
                owned_parent = parent
                parent = None
                try:
                    owned_parent.close()
                except BaseException as close_error:
                    _note_later_error(
                        primary,
                        "launcher parent close also failed",
                        close_error,
                    )
        raise


def _verify_launcher_guard(guard: _LauncherGuard) -> None:
    current_parent = _open_absolute_directory(
        guard.path.parent,
        "launcher parent at use",
    )
    try:
        if (
            current_parent.device,
            current_parent.inode,
        ) != (
            guard.parent.device,
            guard.parent.inode,
        ):
            raise BootProbeError(
                f"launcher parent changed before use: {guard.path}"
            )
        retained = os.fstat(guard.fd)
        named = os.stat(
            guard.name,
            dir_fd=guard.parent.fd,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(retained.st_mode)
            or retained.st_mode & 0o111 == 0
            or _stat_identity(retained) != guard.identity
            or _stat_identity(named) != guard.identity
        ):
            raise BootProbeError(f"launcher changed before use: {guard.path}")
        if (
            _hash_retained_regular(
                guard.fd,
                guard.identity,
                guard.path,
            )
            != guard.sha256
        ):
            raise BootProbeError(
                f"launcher content changed before use: {guard.path}"
            )
        named_after = os.stat(
            guard.name,
            dir_fd=current_parent.fd,
            follow_symlinks=False,
        )
        if _stat_identity(named_after) != guard.identity:
            raise BootProbeError(f"launcher changed before use: {guard.path}")
    finally:
        current_parent.close()


def _verify_pinned_directory_path(
    path: Path,
    pinned: _DirectoryHandle,
    label: str,
) -> None:
    current = _open_absolute_directory(path, label)
    try:
        if (current.device, current.inode) != (
            pinned.device,
            pinned.inode,
        ):
            raise BootProbeError(f"{label} identity changed: {path}")
    finally:
        current.close()


def _retained_spawned_pgid(process: subprocess.Popen[bytes]) -> int:
    pgid = process.pid
    if (
        isinstance(pgid, bool)
        or not isinstance(pgid, int)
        or pgid <= 1
        or pgid == os.getpid()
        or pgid == os.getpgrp()
    ):
        raise BootProbeError(f"unsafe spawned process-group id: {pgid!r}")
    return pgid


def _process_group_exists(pgid: int) -> bool:
    deadline = (
        time.monotonic() + _PROCESS_GROUP_EXIT_CONFIRM_SECONDS
    )
    denied: PermissionError | None = None
    while True:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return False
        except PermissionError as exc:
            denied = exc
        else:
            return True

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BootProbeError(
                f"could not verify spawned process group {pgid} "
                "before cleanup"
            ) from denied
        time.sleep(min(_PROCESS_POLL_SECONDS, remaining))


def _confirm_process_group_stopped(pgid: int) -> None:
    deadline = (
        time.monotonic() + _PROCESS_GROUP_EXIT_CONFIRM_SECONDS
    )
    while True:
        try:
            os.kill(-pgid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            pass
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BootProbeError(
                f"spawned process group {pgid} survived cleanup"
            )
        time.sleep(min(_PROCESS_POLL_SECONDS, remaining))


def _reap_process_bounded(
    process: subprocess.Popen[bytes],
    timeout: float,
) -> int:
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise BootProbeError(
            f"spawned process {process.pid} did not exit after group cleanup"
        ) from exc


def _stop_unretained_spawned_process(
    process: subprocess.Popen[bytes],
) -> None:
    if process.poll() is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    _reap_process_bounded(process, _TERMINATION_GRACE_SECONDS)


def _stop_spawned_process_group(
    process: subprocess.Popen[bytes],
    pgid: int,
) -> int | None:
    if pgid != process.pid or pgid <= 1 or pgid == os.getpgrp():
        raise BootProbeError(f"refusing unsafe process-group cleanup: {pgid}")

    leader_exit = process.poll()
    if leader_exit is not None:
        if not _process_group_exists(pgid):
            _reap_process_bounded(process, 0)
            return leader_exit
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            _reap_process_bounded(process, 0)
            return leader_exit
        time.sleep(_TERMINATION_GRACE_SECONDS)
        if _process_group_exists(pgid):
            try:
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _confirm_process_group_stopped(pgid)
        _reap_process_bounded(process, 0)
        return leader_exit

    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return _reap_process_bounded(process, 0)
    termination_deadline = (
        time.monotonic() + _TERMINATION_GRACE_SECONDS
    )
    try:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        _reap_process_bounded(process, _TERMINATION_GRACE_SECONDS)
        _confirm_process_group_stopped(pgid)
        return None

    if not _process_group_exists(pgid):
        return None
    remaining_grace = termination_deadline - time.monotonic()
    if remaining_grace > 0:
        time.sleep(remaining_grace)
    if _process_group_exists(pgid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        _confirm_process_group_stopped(pgid)
    return None


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


def _close_transfer_descriptor_after_error(
    primary: BaseException,
    label: str,
    descriptor: int,
) -> None:
    try:
        os.close(descriptor)
    except BaseException as exc:
        _note_later_error(primary, label, exc)


def _prepare_descriptor_close_identity(
    descriptor: int,
    observed: os.stat_result,
) -> tuple[int, int, int, int]:
    # A same-inode reopen has matching stat metadata but an independent
    # file offset, so mark this open description before the close attempt.
    marker_offset = (1 << 61) | secrets.randbits(61)
    positioned = os.lseek(descriptor, marker_offset, os.SEEK_SET)
    if positioned != marker_offset:
        raise OSError(
            "could not mark descriptor ownership before close"
        )
    return (
        observed.st_dev,
        observed.st_ino,
        stat.S_IFMT(observed.st_mode),
        marker_offset,
    )


def _close_matching_descriptor_after_error(
    primary: BaseException,
    label: str,
    descriptor: int,
    expected_identity: tuple[int, int, int, int],
) -> None:
    try:
        observed = os.fstat(descriptor)
    except OSError as exc:
        if exc.errno == errno.EBADF:
            return
        _note_later_error(
            primary,
            f"{label} ownership inspection also failed",
            exc,
        )
        return
    except BaseException as exc:
        _note_later_error(
            primary,
            f"{label} ownership inspection also failed",
            exc,
        )
        return
    if (
        observed.st_dev,
        observed.st_ino,
        stat.S_IFMT(observed.st_mode),
    ) != expected_identity[:3]:
        return
    try:
        observed_offset = os.lseek(descriptor, 0, os.SEEK_CUR)
    except BaseException as exc:
        _note_later_error(
            primary,
            f"{label} ownership inspection also failed",
            exc,
        )
        return
    if observed_offset != expected_identity[3]:
        return
    _close_transfer_descriptor_after_error(
        primary,
        label,
        descriptor,
    )


def _copy_regular_exclusive(
    entry: _ScannedLog,
    destination_parent: _DirectoryHandle,
    destination_name: str,
    destination_path: Path,
    expected: LogFingerprint,
) -> _RetainedEvidenceFile:
    source_descriptor = -1
    source_descriptor_to_close = -1
    source_descriptor_identity: tuple[int, int, int, int] | None = None
    destination_descriptor = -1
    retained_file: _RetainedEvidenceFile | None = None
    try:
        source_descriptor = os.open(
            entry.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=entry.parent.fd,
        )
        source_before = os.fstat(source_descriptor)
        expected_identity = _stat_identity(entry.observed)
        if (
            not stat.S_ISREG(source_before.st_mode)
            or _stat_identity(source_before) != expected_identity
        ):
            raise BootProbeError(
                f"changed preloader log was substituted before copy: "
                f"{entry.path}"
            )
        destination_descriptor = os.open(
            destination_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=destination_parent.fd,
        )
        digest = hashlib.sha256()
        while True:
            chunk = os.read(source_descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(destination_descriptor, view)
                if written <= 0:
                    raise OSError(
                        "short write while copying preloader evidence"
                    )
                view = view[written:]
        os.fsync(destination_descriptor)
        os.lseek(destination_descriptor, 0, os.SEEK_SET)
        destination_digest = hashlib.sha256()
        while True:
            chunk = os.read(destination_descriptor, 1024 * 1024)
            if not chunk:
                break
            destination_digest.update(chunk)
        source_after = os.fstat(source_descriptor)
        named_after = os.stat(
            entry.name,
            dir_fd=entry.parent.fd,
            follow_symlinks=False,
        )
        copied = os.fstat(destination_descriptor)
        named_destination = os.stat(
            destination_name,
            dir_fd=destination_parent.fd,
            follow_symlinks=False,
        )
        if (
            _stat_identity(source_after) != expected_identity
            or _stat_identity(named_after) != expected_identity
            or not stat.S_ISREG(copied.st_mode)
            or _stat_identity(named_destination)
            != _stat_identity(copied)
            or copied.st_size != expected.size
            or digest.hexdigest() != expected.sha256
            or destination_digest.hexdigest() != expected.sha256
        ):
            raise BootProbeError(
                f"changed preloader log changed while copying to "
                f"{destination_path}: {entry.path}"
            )
        os.fsync(destination_parent.fd)
        source_descriptor_identity = _prepare_descriptor_close_identity(
            source_descriptor,
            source_after,
        )
    except BaseException as primary:
        if destination_descriptor >= 0:
            descriptor = destination_descriptor
            destination_descriptor = -1
            _close_transfer_descriptor_after_error(
                primary,
                "copy destination close also failed",
                descriptor,
            )
        if source_descriptor >= 0:
            descriptor = source_descriptor
            source_descriptor = -1
            _close_transfer_descriptor_after_error(
                primary,
                "copy source close also failed",
                descriptor,
            )
        raise

    try:
        source_descriptor_to_close = source_descriptor
        source_descriptor = -1
        os.close(source_descriptor_to_close)
        source_descriptor_to_close = -1
        retained_file = _RetainedEvidenceFile(
            relative_path=Path(destination_name),
            descriptor=-1,
            identity=_stat_identity(copied),
            fingerprint=LogFingerprint(
                path=destination_path,
                file_type="regular",
                inode=copied.st_ino,
                size=copied.st_size,
                mtime_ns=copied.st_mtime_ns,
                sha256=destination_digest.hexdigest(),
            ),
        )
        transferred_descriptor = destination_descriptor
        retained_file.descriptor = transferred_descriptor
        destination_descriptor = -1
        return retained_file
    except BaseException as primary:
        retained_descriptor = (
            retained_file.descriptor
            if retained_file is not None
            else -1
        )
        source_descriptor_owned = source_descriptor
        source_descriptor_to_close_owned = source_descriptor_to_close
        destination_descriptor_owned = destination_descriptor
        source_descriptor = -1
        source_descriptor_to_close = -1
        destination_descriptor = -1
        if retained_file is not None:
            retained_file.descriptor = -1
        closed_descriptors: set[int] = set()
        if source_descriptor_owned >= 0:
            closed_descriptors.add(source_descriptor_owned)
            _close_transfer_descriptor_after_error(
                primary,
                "copy source close also failed",
                source_descriptor_owned,
            )
        elif source_descriptor_to_close_owned >= 0:
            closed_descriptors.add(
                source_descriptor_to_close_owned
            )
            if source_descriptor_identity is None:
                _close_transfer_descriptor_after_error(
                    primary,
                    "copy source transition close also failed",
                    source_descriptor_to_close_owned,
                )
            else:
                _close_matching_descriptor_after_error(
                    primary,
                    "copy source transition close also failed",
                    source_descriptor_to_close_owned,
                    source_descriptor_identity,
                )
        for cleanup_label, descriptor in (
            (
                "copy destination close also failed",
                destination_descriptor_owned,
            ),
            (
                "transferred copy descriptor close also failed",
                retained_descriptor,
            ),
        ):
            if descriptor < 0 or descriptor in closed_descriptors:
                continue
            closed_descriptors.add(descriptor)
            _close_transfer_descriptor_after_error(
                primary,
                cleanup_label,
                descriptor,
            )
        raise


def _move_regular_exclusive(
    entry: _ScannedLog,
    destination_parent: _DirectoryHandle,
    destination_name: str,
    destination_path: Path,
    expected: LogFingerprint,
) -> _RetainedEvidenceFile:
    source_descriptor = -1
    retained_file: _RetainedEvidenceFile | None = None
    try:
        source_descriptor = os.open(
            entry.name,
            os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=entry.parent.fd,
        )
        source_before = os.fstat(source_descriptor)
        expected_identity = _stat_identity(entry.observed)
        if (
            not stat.S_ISREG(source_before.st_mode)
            or _stat_identity(source_before) != expected_identity
        ):
            raise BootProbeError(
                f"new preloader log was substituted before move: "
                f"{entry.path}"
            )
        source_digest = hashlib.sha256()
        while True:
            chunk = os.read(source_descriptor, 1024 * 1024)
            if not chunk:
                break
            source_digest.update(chunk)
        source_after_hash = os.fstat(source_descriptor)
        named_before_move = os.stat(
            entry.name,
            dir_fd=entry.parent.fd,
            follow_symlinks=False,
        )
        if (
            _stat_identity(source_after_hash) != expected_identity
            or _stat_identity(named_before_move) != expected_identity
            or source_digest.hexdigest() != expected.sha256
        ):
            raise BootProbeError(
                f"new preloader log changed while validating move: "
                f"{entry.path}"
            )

        try:
            _renameatx(
                entry.parent,
                entry.name,
                destination_parent,
                destination_name,
                _RENAME_EXCL,
                "move new preloader log into boot evidence",
            )
        except Exception as exc:
            raise BootProbeError(
                f"cannot move new preloader log exclusively: "
                f"{entry.path}: {exc}"
            ) from exc

        try:
            moved_observed = os.stat(
                destination_name,
                dir_fd=destination_parent.fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise BootProbeError(
                f"moved preloader evidence cannot be inspected: "
                f"{destination_path}: {exc}"
            ) from exc
        moved_identity = _stat_identity(moved_observed)
        moved_entry = _ScannedLog(
            path=destination_path,
            kind=entry.kind,
            parent=destination_parent,
            name=destination_name,
            observed=moved_observed,
            file_type=_file_type(moved_observed.st_mode),
        )

        mismatch: Exception | None = None
        try:
            retained_after_move = os.fstat(source_descriptor)
            if (
                _stat_identity(retained_after_move) != expected_identity
                or (
                    moved_observed.st_dev,
                    moved_observed.st_ino,
                )
                != (
                    retained_after_move.st_dev,
                    retained_after_move.st_ino,
                )
                or moved_entry.file_type != "regular"
            ):
                raise BootProbeError(
                    f"moved preloader evidence is not the retained source: "
                    f"{destination_path}"
                )
            moved_fingerprint = _fingerprint_scanned(moved_entry)
            if not _fingerprint_matches(expected, moved_fingerprint):
                raise BootProbeError(
                    f"moved preloader evidence identity mismatch: "
                    f"{destination_path}"
                )
            try:
                os.stat(
                    entry.name,
                    dir_fd=entry.parent.fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                pass
            else:
                raise BootProbeError(
                    f"new preloader source was recreated during move: "
                    f"{entry.path}"
                )
        except Exception as exc:
            mismatch = exc

        if mismatch is None:
            os.fsync(entry.parent.fd)
            if destination_parent.fd != entry.parent.fd:
                os.fsync(destination_parent.fd)
            retained_file = _RetainedEvidenceFile(
                relative_path=Path(destination_name),
                descriptor=-1,
                identity=_stat_identity(retained_after_move),
                fingerprint=moved_fingerprint,
            )
            transferred_descriptor = source_descriptor
            retained_file.descriptor = transferred_descriptor
            source_descriptor = -1
            return retained_file

        try:
            current_destination = os.stat(
                destination_name,
                dir_fd=destination_parent.fd,
                follow_symlinks=False,
            )
            if _stat_identity(current_destination) != moved_identity:
                raise BootProbeError(
                    "moved evidence changed before compensation; "
                    "preserving it"
                )
            _renameatx(
                destination_parent,
                destination_name,
                entry.parent,
                entry.name,
                _RENAME_EXCL,
                "compensate rejected preloader evidence move",
            )
            os.fsync(entry.parent.fd)
            if destination_parent.fd != entry.parent.fd:
                os.fsync(destination_parent.fd)
        except Exception as compensation_error:
            raise BootProbeError(
                f"{mismatch}; compensation failed without deleting either "
                f"path: {compensation_error}"
            ) from mismatch
        raise BootProbeError(
            f"{mismatch}; rejected move was restored to {entry.path}"
        ) from mismatch
    except BaseException as primary:
        if source_descriptor >= 0:
            descriptor = source_descriptor
            source_descriptor = -1
            _close_transfer_descriptor_after_error(
                primary,
                "move source close also failed",
                descriptor,
            )
        elif retained_file is not None:
            try:
                retained_file.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "transferred move descriptor close also failed",
                    exc,
                )
        raise


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
    pending_handle: _DirectoryHandle | None = None
    current_root: _DirectoryHandle | None = None

    def visit(
        directory: _DirectoryHandle,
        relative_parent: Path,
    ) -> None:
        nonlocal pending_handle
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
                pending_handle = _open_child_directory(
                    directory,
                    child_entry.name,
                    path,
                    observed,
                )
                child_handles.append(pending_handle)
                child = pending_handle
                pending_handle = None
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
        current_root = _open_absolute_directory(
            retained.public.evidence_dir,
            "retained evidence directory",
        )
        if (current_root.device, current_root.inode) != (
            retained.directory_handle.device,
            retained.directory_handle.inode,
        ):
            raise BootProbeError(
                f"retained evidence directory changed: "
                f"{retained.public.evidence_dir}"
            )
        current_root.close()
        current_root = None
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
        if current_root is not None:
            try:
                current_root.close()
            except BaseException as close_error:
                _note_later_error(
                    primary,
                    "evidence root verification handle close also failed",
                    close_error,
                )
        if (
            pending_handle is not None
            and all(
                pending_handle is not handle
                for handle in child_handles
            )
        ):
            try:
                pending_handle.close()
            except BaseException as close_error:
                _note_later_error(
                    primary,
                    "pending evidence tree scan handle close also failed",
                    close_error,
                )
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
    child_handles: tuple[_DirectoryHandle, ...] = ()
    primary: BaseException | None = None
    try:
        try:
            child_handles = _open_verified_evidence_directories(retained)
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
    finally:
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


def _collect_boot_evidence_retained(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_root: Path,
    *,
    expected_inventory: tuple[LogFingerprint, ...] | None,
) -> _RetainedBootEvidence:
    game = _validate_directory(game_root, "game root")
    baseline = _validate_baseline(before, game)
    evidence, evidence_exists = _validate_evidence_root(evidence_root)

    initial_scan: _LogScan | None = None
    try:
        initial_scan = _scan_preloader_logs(game)
        initial_issues = [
            f"unsafe {entry.file_type} preloader log: {entry.path}"
            for entry in initial_scan.entries
            if entry.file_type != "regular"
        ]
        for entry in initial_scan.entries:
            if entry.file_type == "regular":
                _fingerprint_scanned(entry)
    except BaseException as primary:
        if initial_scan is not None:
            try:
                initial_scan.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "initial preloader scan close also failed",
                    exc,
                )
        raise
    else:
        initial_scan.close()

    evidence_handle: _DirectoryHandle | None = None
    retained_files: list[_RetainedEvidenceFile] = []
    pending_retained_file: _RetainedEvidenceFile | None = None
    try:
        evidence_dir, evidence_handle = _allocate_evidence_directory(
            evidence, evidence_exists
        )
        final_scan: _LogScan | None = None
        try:
            final_scan = _scan_preloader_logs(game)
            final_regular: dict[Path, LogFingerprint] = {}
            final_entries = {
                entry.path: entry
                for entry in final_scan.entries
                if entry.file_type == "regular"
            }
            final_paths = {entry.path for entry in final_scan.entries}
            final_issues = [
                f"unsafe {entry.file_type} preloader log: {entry.path}"
                for entry in final_scan.entries
                if entry.file_type != "regular"
            ]
            issues = list(final_issues)
            for entry in final_scan.entries:
                if entry.file_type == "regular":
                    final_regular[entry.path] = _fingerprint_scanned(entry)

            if expected_inventory is not None:
                expected = _validate_baseline(expected_inventory, game)
                mismatches = _post_shutdown_inventory_mismatches(
                    expected,
                    final_regular,
                    final_paths,
                )
                if mismatches:
                    raise BootProbeError("; ".join(mismatches))

            changed: list[Path] = []
            new: list[Path] = []
            for path, fingerprint in final_regular.items():
                prior = baseline.get(path)
                if prior is None:
                    new.append(path)
                elif not _fingerprint_matches(prior, fingerprint):
                    changed.append(path)
                    issues.append(
                        f"pre-existing preloader log changed: {path}"
                    )
            for path in baseline:
                if path not in final_paths:
                    issues.append(
                        f"pre-existing preloader log missing: {path}"
                    )

            known_evidence_directories = {
                evidence_dir: (
                    evidence_handle.device,
                    evidence_handle.inode,
                )
            }
            moved_logs: list[Path] = []
            copied_logs: list[Path] = []
            for source in new:
                relative = source.relative_to(game)
                destination = evidence_dir / relative
                destination_parent: _DirectoryHandle | None = None
                try:
                    destination_parent = _make_evidence_parents(
                        evidence_handle,
                        relative.parent,
                        known_evidence_directories,
                    )
                    pending_retained_file = _move_regular_exclusive(
                        final_entries[source],
                        destination_parent,
                        relative.name,
                        destination,
                        final_regular[source],
                    )
                    pending_retained_file.relative_path = relative
                    retained_files.append(pending_retained_file)
                    pending_retained_file = None
                except BaseException as primary:
                    if destination_parent is not None:
                        try:
                            destination_parent.close()
                        except BaseException as exc:
                            _note_later_error(
                                primary,
                                "evidence parent close also failed",
                                exc,
                            )
                    raise
                else:
                    destination_parent.close()
                moved_logs.append(destination)
            for source in changed:
                relative = source.relative_to(game)
                destination = evidence_dir / relative
                destination_parent = None
                try:
                    destination_parent = _make_evidence_parents(
                        evidence_handle,
                        relative.parent,
                        known_evidence_directories,
                    )
                    pending_retained_file = _copy_regular_exclusive(
                        final_entries[source],
                        destination_parent,
                        relative.name,
                        destination,
                        final_regular[source],
                    )
                    pending_retained_file.relative_path = relative
                    retained_files.append(pending_retained_file)
                    pending_retained_file = None
                except BaseException as primary:
                    if destination_parent is not None:
                        try:
                            destination_parent.close()
                        except BaseException as exc:
                            _note_later_error(
                                primary,
                                "evidence parent close also failed",
                                exc,
                            )
                    raise
                else:
                    destination_parent.close()
                copied_logs.append(destination)
        except BaseException as primary:
            if final_scan is not None:
                try:
                    final_scan.close()
                except BaseException as exc:
                    _note_later_error(
                        primary,
                        "final preloader scan close also failed",
                        exc,
                    )
            raise
        else:
            final_scan.close()

        directory_identities = tuple(
            _EvidenceDirectoryIdentity(
                relative_path=path.relative_to(evidence_dir),
                device=identity[0],
                inode=identity[1],
            )
            for path, identity in sorted(
                known_evidence_directories.items(),
                key=lambda item: item[0]
                .relative_to(evidence_dir)
                .as_posix(),
            )
        )
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
        retained.decision = _capture_retained_evidence_decision(retained)
        return retained
    except BaseException as primary:
        if pending_retained_file is not None:
            try:
                pending_retained_file.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "pending retained evidence file close also failed",
                    exc,
                )
        for item in reversed(retained_files):
            try:
                item.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "retained evidence file close also failed",
                    exc,
                )
        if evidence_handle is not None:
            try:
                evidence_handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "retained evidence directory close also failed",
                    exc,
                )
        raise


def collect_boot_evidence(
    before: tuple[LogFingerprint, ...],
    game_root: Path,
    evidence_root: Path,
) -> BootEvidence:
    retained: _RetainedBootEvidence | None = None
    try:
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
            retained = None
            if primary is None:
                raise
            _note_later_error(
                primary,
                "retained boot evidence close also failed",
                close_error,
            )
        else:
            retained = None
        if primary is not None:
            raise primary
        return public
    except BaseException as primary:
        if retained is not None:
            try:
                retained.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "retained public collector close also failed",
                    exc,
                )
        raise


def _encode_probe_json(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _close_staged_probe_json(staged: _StagedProbeJson) -> None:
    primary: BaseException | None = None
    if staged.verifier_fd >= 0:
        descriptor = staged.verifier_fd
        staged.verifier_fd = -1
        try:
            os.close(descriptor)
        except BaseException as exc:
            primary = exc
    try:
        staged.directory_handle.close()
    except BaseException as exc:
        if primary is None:
            primary = exc
        else:
            _note_later_error(
                primary,
                "staged probe JSON directory close also failed",
                exc,
            )
    if primary is not None and not staged.committed:
        raise primary


def _verify_probe_json_descriptor(
    staged: _StagedProbeJson,
    descriptor: int,
) -> None:
    before = os.fstat(descriptor)
    os.lseek(descriptor, 0, os.SEEK_SET)
    observed_payload = bytearray()
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            break
        observed_payload.extend(chunk)
    after = os.fstat(descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o600
        or _stat_identity(before) != staged.pending_identity
        or _stat_identity(after) != staged.pending_identity
        or bytes(observed_payload) != staged.encoded
    ):
        raise BootProbeError(
            f"retained pending probe JSON changed in {staged.directory}"
        )


def _retain_staged_probe_json_verifier(
    staged: _StagedProbeJson,
) -> None:
    descriptor = -1
    try:
        descriptor = os.open(
            staged.pending_name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=staged.directory_handle.fd,
        )
        _verify_probe_json_descriptor(staged, descriptor)
        named = os.stat(
            staged.pending_name,
            dir_fd=staged.directory_handle.fd,
            follow_symlinks=False,
        )
        if _stat_identity(named) != staged.pending_identity:
            raise BootProbeError(
                f"pending probe JSON changed after writer close in "
                f"{staged.directory}"
            )
        staged.verifier_fd = descriptor
        descriptor = -1
    except BaseException as primary:
        if descriptor >= 0:
            descriptor_to_close = descriptor
            descriptor = -1
            try:
                os.close(descriptor_to_close)
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "pending probe JSON verifier close also failed",
                    exc,
                )
        raise


def _verify_staged_probe_json_retained_directory(
    staged: _StagedProbeJson,
) -> None:
    observed = os.fstat(staged.directory_handle.fd)
    if (
        not stat.S_ISDIR(observed.st_mode)
        or (observed.st_dev, observed.st_ino)
        != (
            staged.directory_handle.device,
            staged.directory_handle.inode,
        )
    ):
        raise BootProbeError(
            f"retained evidence directory changed before probe JSON "
            f"publication: {staged.directory}"
        )


def _verify_staged_probe_json_public_path(
    staged: _StagedProbeJson,
) -> None:
    _verify_pinned_directory_path(
        staged.directory,
        staged.directory_handle,
        "evidence directory at probe JSON publication",
    )


def _stat_staged_probe_json_name(
    staged: _StagedProbeJson,
    name: str,
) -> os.stat_result | None:
    try:
        return os.stat(
            name,
            dir_fd=staged.directory_handle.fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return None


def _probe_json_retained_namespace(
    staged: _StagedProbeJson,
) -> tuple[str, os.stat_result | None, os.stat_result | None]:
    _verify_staged_probe_json_retained_directory(staged)
    _verify_probe_json_descriptor(staged, staged.verifier_fd)
    pending = _stat_staged_probe_json_name(
        staged,
        staged.pending_name,
    )
    canonical = _stat_staged_probe_json_name(staged, "probe.json")
    pending_exact = (
        pending is not None
        and _stat_identity(pending) == staged.pending_identity
    )
    canonical_exact = (
        canonical is not None
        and _stat_identity(canonical) == staged.pending_identity
    )
    if canonical_exact and pending is None:
        state = "exact_canonical"
    elif pending_exact and canonical is None:
        state = "exact_pending"
    elif canonical is not None:
        state = "canonical_mismatch"
    else:
        state = "private_mismatch"
    return state, pending, canonical


def _probe_json_publication_namespace(
    staged: _StagedProbeJson,
) -> tuple[str, os.stat_result | None, os.stat_result | None]:
    namespace = _probe_json_retained_namespace(staged)
    _verify_staged_probe_json_public_path(staged)
    return namespace


def _fresh_probe_json_private_name(suffix: str) -> str:
    token = _random_probe_json_token()
    if _TOKEN_PATTERN.fullmatch(token) is None:
        raise BootProbeError(f"invalid probe JSON token: {token!r}")
    return f".probe-json-{token}.{suffix}"


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
    descriptor = -1
    descriptor_to_close = -1
    close_identity: tuple[int, int, int, int] | None = None
    try:
        descriptor = os.open(
            private_name,
            os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=staged.directory_handle.fd,
        )
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
        close_identity = _prepare_descriptor_close_identity(
            descriptor,
            after,
        )
        descriptor_to_close = descriptor
        descriptor = -1
        os.close(descriptor_to_close)
        descriptor_to_close = -1
        return
    except BaseException as primary:
        descriptor_owned = descriptor
        descriptor_to_close_owned = descriptor_to_close
        descriptor = -1
        descriptor_to_close = -1
        if descriptor_owned >= 0:
            _close_transfer_descriptor_after_error(
                primary,
                "private probe JSON descriptor close also failed",
                descriptor_owned,
            )
        elif descriptor_to_close_owned >= 0:
            if close_identity is None:
                _close_transfer_descriptor_after_error(
                    primary,
                    "private probe JSON descriptor close also failed",
                    descriptor_to_close_owned,
                )
            else:
                _close_matching_descriptor_after_error(
                    primary,
                    "private probe JSON descriptor close also failed",
                    descriptor_to_close_owned,
                    close_identity,
                )
        raise


def _move_canonical_probe_json_to_private(
    staged: _StagedProbeJson,
    expected_identity: tuple[int, int, int, int, int],
    *,
    prefer_original_pending_name: bool,
    description: str,
) -> tuple[str, tuple[BaseException, ...]]:
    errors: list[BaseException] = []
    try_original_pending_name = prefer_original_pending_name
    for _attempt in range(128):
        if try_original_pending_name:
            try_original_pending_name = False
            pending = _stat_staged_probe_json_name(
                staged,
                staged.pending_name,
            )
            if pending is None:
                private_name = staged.pending_name
            else:
                private_name = _fresh_probe_json_private_name(
                    "quarantine"
                )
        else:
            private_name = _fresh_probe_json_private_name("quarantine")

        rename_error: BaseException | None = None
        try:
            _renameatx(
                staged.directory_handle,
                "probe.json",
                staged.directory_handle,
                private_name,
                _RENAME_EXCL,
                description,
            )
        except BaseException as exc:
            rename_error = exc
            errors.append(exc)

        _verify_staged_probe_json_retained_directory(staged)
        _verify_probe_json_descriptor(staged, staged.verifier_fd)
        canonical = _stat_staged_probe_json_name(staged, "probe.json")
        private = _stat_staged_probe_json_name(staged, private_name)
        if (
            canonical is None
            and private is not None
            and _stat_identity(private) == expected_identity
        ):
            _secure_private_probe_json(
                staged,
                private_name,
                expected_identity,
            )
            return private_name, tuple(errors)

        canonical_still_expected = (
            canonical is not None
            and _stat_identity(canonical) == expected_identity
        )
        private_is_collision = (
            private is not None
            and _stat_identity(private) != expected_identity
        )
        if canonical_still_expected and (
            private is None or private_is_collision
        ):
            if rename_error is None:
                errors.append(
                    BootProbeError(
                        f"{description} returned without changing the "
                        "exact canonical namespace"
                    )
                )
            continue
        raise BootProbeError(
            f"cannot reconcile {description} in {staged.directory}"
        ) from rename_error
    raise BootProbeError(
        f"could not allocate private probe JSON quarantine after "
        f"128 attempts in {staged.directory}"
    )


def _preserve_canonical_probe_json_privately(
    staged: _StagedProbeJson,
    canonical: os.stat_result | None,
    *,
    primary: BaseException,
) -> None:
    if canonical is not None:
        canonical_identity = _stat_identity(canonical)
        try:
            _private_name, move_errors = (
                _move_canonical_probe_json_to_private(
                    staged,
                    canonical_identity,
                    prefer_original_pending_name=(
                        canonical_identity == staged.pending_identity
                    ),
                    description=(
                        "quarantine mismatched canonical probe JSON"
                    ),
                )
            )
        except BaseException as exc:
            _note_later_error(
                primary,
                "canonical probe JSON quarantine failed",
                exc,
            )
        else:
            for error in move_errors:
                _note_later_error(
                    primary,
                    "canonical probe JSON quarantine rename also raised",
                    error,
                )
    try:
        os.fsync(staged.directory_handle.fd)
    except BaseException as exc:
        _note_later_error(
            primary,
            "integrity evidence-directory fsync also failed",
            exc,
        )


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
    try:
        _preserve_canonical_probe_json_privately(
            staged,
            canonical,
            primary=primary,
        )
    except BaseException as quarantine_error:
        _note_later_error(
            primary,
            "canonical probe JSON quarantine during reconciliation "
            "also failed",
            quarantine_error,
        )


def _verify_probe_json_public_path_or_preserve(
    staged: _StagedProbeJson,
    canonical: os.stat_result | None,
    *,
    trigger: BaseException | None,
    trigger_label: str,
) -> None:
    try:
        _verify_staged_probe_json_public_path(staged)
    except BaseException as path_error:
        if trigger is not None:
            _note_later_error(
                path_error,
                trigger_label,
                trigger,
            )
        _preserve_canonical_probe_json_privately(
            staged,
            canonical,
            primary=path_error,
        )
        raise


def _raise_probe_json_integrity_error(
    staged: _StagedProbeJson,
    message: str,
    *,
    trigger: BaseException | None,
    canonical: os.stat_result | None,
) -> None:
    integrity_error = BootProbeError(message)
    if trigger is not None:
        _note_later_error(
            integrity_error,
            "probe JSON publication also raised",
            trigger,
        )
    _preserve_canonical_probe_json_privately(
        staged,
        canonical,
        primary=integrity_error,
    )
    raise integrity_error


def _stage_probe_json(
    evidence_dir: Path,
    payload: dict[str, Any],
    *,
    _directory_handle: _DirectoryHandle | None = None,
) -> _StagedProbeJson:
    directory = _requested_path(evidence_dir, "evidence directory")
    if _directory_handle is None:
        directory = _validate_directory(directory, "evidence directory")
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
    encoded = _encode_probe_json(payload)
    directory_handle: _DirectoryHandle | None = None
    descriptor = -1
    descriptor_to_close = -1
    writer_descriptor_identity: tuple[int, int, int, int] | None = None
    staged: _StagedProbeJson | None = None
    try:
        if _directory_handle is None:
            directory_handle = _open_absolute_directory(
                directory,
                "evidence directory",
            )
        else:
            directory_handle = _duplicate_directory_handle(
                _directory_handle
            )
        if directory_handle.fd < 0:
            raise BootProbeError(
                f"evidence directory handle is closed: {directory}"
            )
        try:
            os.stat(
                "probe.json",
                dir_fd=directory_handle.fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            pass
        else:
            raise BootProbeError(
                f"probe.json already exists in {directory}"
            )

        pending_name: str | None = None
        for _attempt in range(128):
            token = _random_probe_json_token()
            if _TOKEN_PATTERN.fullmatch(token) is None:
                raise BootProbeError(
                    f"invalid probe JSON token: {token!r}"
                )
            candidate = f".probe-json-{token}.pending"
            try:
                descriptor = os.open(
                    candidate,
                    (
                        os.O_RDWR
                        | os.O_CREAT
                        | os.O_EXCL
                        | os.O_NOFOLLOW
                    ),
                    0o600,
                    dir_fd=directory_handle.fd,
                )
            except FileExistsError:
                continue
            pending_name = candidate
            break
        if pending_name is None:
            raise BootProbeError(
                "could not allocate a private probe JSON pending file "
                "after 128 attempts"
            )

        os.fchmod(descriptor, 0o600)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while creating probe.json")
            view = view[written:]
        os.lseek(descriptor, 0, os.SEEK_SET)
        observed_payload = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            observed_payload.extend(chunk)
        created = os.fstat(descriptor)
        named = os.stat(
            pending_name,
            dir_fd=directory_handle.fd,
            follow_symlinks=False,
        )
        if (
            bytes(observed_payload) != encoded
            or not stat.S_ISREG(created.st_mode)
            or stat.S_IMODE(created.st_mode) != 0o600
            or _stat_identity(named) != _stat_identity(created)
        ):
            raise BootProbeError(
                f"pending probe JSON changed while writing in {directory}"
            )

        os.fsync(descriptor)
        os.fsync(directory_handle.fd)
        writer_descriptor_identity = _prepare_descriptor_close_identity(
            descriptor,
            created,
        )
        descriptor_to_close = descriptor
        descriptor = -1
        os.close(descriptor_to_close)
        descriptor_to_close = -1

        staged = _StagedProbeJson(
            directory=directory,
            directory_handle=directory_handle,
            pending_name=pending_name,
            encoded=encoded,
            pending_identity=_stat_identity(created),
        )
        _retain_staged_probe_json_verifier(staged)
        return staged
    except BaseException as primary:
        descriptor_owned = descriptor
        descriptor_to_close_owned = descriptor_to_close
        descriptor = -1
        descriptor_to_close = -1
        if descriptor_owned >= 0:
            _close_transfer_descriptor_after_error(
                primary,
                "pending probe JSON file close also failed",
                descriptor_owned,
            )
        elif descriptor_to_close_owned >= 0:
            if writer_descriptor_identity is None:
                _close_transfer_descriptor_after_error(
                    primary,
                    "pending probe JSON file close also failed",
                    descriptor_to_close_owned,
                )
            else:
                _close_matching_descriptor_after_error(
                    primary,
                    "pending probe JSON file close also failed",
                    descriptor_to_close_owned,
                    writer_descriptor_identity,
                )
        if staged is None and directory_handle is not None:
            try:
                directory_handle.close()
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "pending probe JSON directory close also failed",
                    exc,
                )
        else:
            try:
                _close_staged_probe_json(staged)
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "staged probe JSON close also failed",
                    exc,
                )
        raise


def _verify_staged_probe_json(
    evidence_dir: Path,
    payload: dict[str, Any],
    staged: _StagedProbeJson,
) -> None:
    directory = _validate_directory(evidence_dir, "evidence directory")
    encoded = _encode_probe_json(payload)
    if (
        staged.committed
        or staged.directory != directory
        or staged.directory_handle.fd < 0
        or staged.verifier_fd < 0
        or staged.directory_handle.path != directory
        or staged.encoded != encoded
    ):
        raise BootProbeError(
            f"staged probe JSON does not match {directory}"
        )

    state, _pending, canonical = (
        _probe_json_publication_namespace(staged)
    )
    if state == "canonical_mismatch":
        _raise_probe_json_integrity_error(
            staged,
            (
                "canonical probe JSON appeared before verification in "
                f"{directory}"
            ),
            trigger=None,
            canonical=canonical,
        )
    if state != "exact_pending":
        raise BootProbeError(
            f"pending probe JSON changed before commit in {directory}"
        )


def _commit_staged_probe_json(staged: _StagedProbeJson) -> None:
    rename_error: BaseException | None = None
    try:
        _renameatx(
            staged.directory_handle,
            staged.pending_name,
            staged.directory_handle,
            "probe.json",
            _RENAME_EXCL,
            "publish canonical boot probe JSON",
        )
    except BaseException as exc:
        rename_error = exc

    try:
        state, _pending, canonical = _probe_json_retained_namespace(
            staged
        )
    except BaseException as reconciliation_error:
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
        _quarantine_reachable_canonical_probe_json(
            staged,
            integrity_error,
        )
        raise integrity_error from reconciliation_error
    _verify_probe_json_public_path_or_preserve(
        staged,
        canonical,
        trigger=rename_error,
        trigger_label="exclusive probe JSON rename also raised",
    )

    if state == "exact_pending" and rename_error is not None:
        raise BootProbeError(
            f"cannot publish probe.json exclusively in "
            f"{staged.directory}: {rename_error}"
        ) from rename_error
    if state != "exact_canonical":
        _raise_probe_json_integrity_error(
            staged,
            (
                "probe JSON publication did not produce the exact "
                f"retained canonical artifact in {staged.directory}"
            ),
            trigger=rename_error,
            canonical=canonical,
        )

    durability_errors: list[BaseException] = []
    for _attempt in range(_PROBE_JSON_DIRECTORY_FSYNC_ATTEMPTS):
        try:
            os.fsync(staged.directory_handle.fd)
        except BaseException as exc:
            durability_errors.append(exc)
            try:
                state, _pending, canonical = (
                    _probe_json_retained_namespace(staged)
                )
            except BaseException as reconciliation_error:
                integrity_error = BootProbeError(
                    f"cannot reconcile tentative probe JSON "
                    f"publication after an evidence-directory fsync "
                    f"failure in {staged.directory}"
                )
                _note_later_error(
                    integrity_error,
                    "post-publication probe JSON reconciliation failed",
                    reconciliation_error,
                )
                _note_later_error(
                    integrity_error,
                    "post-publication evidence-directory fsync also "
                    "failed",
                    durability_errors[0],
                )
                for later_error in durability_errors[1:]:
                    _note_later_error(
                        integrity_error,
                        "later post-publication evidence-directory "
                        "fsync also failed",
                        later_error,
                    )
                if rename_error is not None:
                    _note_later_error(
                        integrity_error,
                        "exclusive probe JSON rename also raised",
                        rename_error,
                    )
                _quarantine_reachable_canonical_probe_json(
                    staged,
                    integrity_error,
                )
                raise integrity_error from reconciliation_error
            _verify_probe_json_public_path_or_preserve(
                staged,
                canonical,
                trigger=durability_errors[0],
                trigger_label=(
                    "post-publication evidence-directory fsync "
                    "also failed"
                ),
            )
            if state != "exact_canonical":
                _raise_probe_json_integrity_error(
                    staged,
                    (
                        "probe JSON namespace changed after a "
                        "post-publication evidence-directory fsync error"
                    ),
                    trigger=durability_errors[0],
                    canonical=canonical,
                )
            continue

        try:
            state, _pending, canonical = (
                _probe_json_retained_namespace(staged)
            )
        except BaseException as reconciliation_error:
            integrity_error = BootProbeError(
                f"cannot reconcile tentative probe JSON publication "
                f"after an evidence-directory fsync in "
                f"{staged.directory}"
            )
            _note_later_error(
                integrity_error,
                "post-publication probe JSON reconciliation failed",
                reconciliation_error,
            )
            if durability_errors:
                _note_later_error(
                    integrity_error,
                    "post-publication evidence-directory fsync also "
                    "failed",
                    durability_errors[0],
                )
                for later_error in durability_errors[1:]:
                    _note_later_error(
                        integrity_error,
                        "later post-publication evidence-directory "
                        "fsync also failed",
                        later_error,
                    )
            if rename_error is not None:
                _note_later_error(
                    integrity_error,
                    "exclusive probe JSON rename also raised",
                    rename_error,
                )
            _quarantine_reachable_canonical_probe_json(
                staged,
                integrity_error,
            )
            raise integrity_error from reconciliation_error
        _verify_probe_json_public_path_or_preserve(
            staged,
            canonical,
            trigger=None,
            trigger_label=(
                "post-publication evidence-directory fsync also failed"
            ),
        )
        if state != "exact_canonical":
            _raise_probe_json_integrity_error(
                staged,
                (
                    "probe JSON namespace changed before the durable "
                    f"commit in {staged.directory}"
                ),
                trigger=None,
                canonical=canonical,
            )
        staged.committed = True
        return

    first_durability_error = durability_errors[0]
    for later_error in durability_errors[1:]:
        _note_later_error(
            first_durability_error,
            "later post-publication evidence-directory fsync also failed",
            later_error,
        )
    try:
        _private_name, rollback_errors = (
            _move_canonical_probe_json_to_private(
                staged,
                staged.pending_identity,
                prefer_original_pending_name=True,
                description=(
                    "return undurable canonical probe JSON to "
                    "private storage"
                ),
            )
        )
    except BaseException as rollback_error:
        _note_later_error(
            first_durability_error,
            "probe JSON durability rollback failed",
            rollback_error,
        )
        raise first_durability_error
    for rollback_error in rollback_errors:
        _note_later_error(
            first_durability_error,
            "probe JSON durability rollback rename also raised",
            rollback_error,
        )
    try:
        os.fsync(staged.directory_handle.fd)
    except BaseException as rollback_fsync_error:
        _note_later_error(
            first_durability_error,
            "probe JSON rollback evidence-directory fsync also failed",
            rollback_fsync_error,
        )
    raise first_durability_error


def _write_probe_json(
    evidence_dir: Path,
    payload: dict[str, Any],
    *,
    _staged: _StagedProbeJson | None = None,
) -> None:
    staged: _StagedProbeJson | None = _staged
    try:
        if staged is None:
            staged = _stage_probe_json(evidence_dir, payload)
        _verify_staged_probe_json(evidence_dir, payload, staged)
        _commit_staged_probe_json(staged)
        _close_staged_probe_json(staged)
        staged = None
    except BaseException as primary:
        if staged is not None:
            try:
                _close_staged_probe_json(staged)
            except BaseException as exc:
                _note_later_error(
                    primary,
                    "staged probe JSON close also failed",
                    exc,
                )
        raise


def _validate_probe_request(
    game_root: Path,
    launcher_path: Path,
    config_path: Path,
    evidence_root: Path,
    timeout_seconds: int,
) -> tuple[Path, Path, Path, Path, int]:
    game = _validate_directory(game_root, "game root")
    launcher = _validate_regular_file(
        launcher_path,
        "launcher",
        executable=True,
    )
    config = _validate_regular_file(config_path, "config")
    evidence, _ = _validate_evidence_root(evidence_root)
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, int)
        or timeout_seconds <= 0
    ):
        raise ValueError("timeout must be a positive non-bool integer")
    return game, launcher, config, evidence, timeout_seconds


def _app_signature_identity(
    signature: _AppSignature,
) -> tuple[int, tuple[str, ...], str]:
    return (
        signature.returncode,
        tuple(sorted(signature.stdout.splitlines(keepends=True))),
        signature.stderr,
    )


def _preflight_issues(
    snapshot: _BootSnapshot,
    app: Path,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not snapshot.installer_healthy:
        issues.append("oracle installer status is not healthy")
    if snapshot.compatibility_state != "patched":
        issues.append(
            "active preloader compatibility state is not patched: "
            f"{snapshot.compatibility_state}"
        )
    if snapshot.assembly_sha256 != EXPECTED_ASSEMBLY_SHA256:
        issues.append(
            "game assembly SHA-256 does not match the reviewed build"
        )

    clean_signature = _AppSignature(
        0,
        "",
        (
            f"{app}: valid on disk\n"
            f"{app}: satisfies its Designated Requirement\n"
        ),
    )
    foreground_bundle = app / "Contents/Plugins/Foregroundr.bundle"
    foreground_only_signature = _AppSignature(
        1,
        "".join(
            (
                "file added: "
                f"{foreground_bundle / 'Contents/_CodeSignature/CodeResources'}\n",
                "file added: "
                f"{foreground_bundle / 'Contents/_CodeSignature/CodeDirectory'}\n",
                "file added: "
                f"{foreground_bundle / 'Contents/_CodeSignature/CodeRequirements'}\n",
                "file added: "
                f"{foreground_bundle / 'Contents/_CodeSignature/CodeSignature'}\n",
                "file added: "
                f"{foreground_bundle / 'Contents/MacOS/Foregroundr'}\n",
                "file added: "
                f"{foreground_bundle / 'Contents/Info.plist'}\n",
                f"file missing: {foreground_bundle}\n",
            )
        ),
        f"{app}: a sealed resource is missing or invalid\n",
    )
    if _app_signature_identity(snapshot.app_signature) not in {
        _app_signature_identity(clean_signature),
        _app_signature_identity(foreground_only_signature),
    }:
        issues.append("game app code signature is not an accepted exact result")
    return tuple(issues)


def _monitor_result_issues(
    outcome: _MonitorOutcome,
    timeout_seconds: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    markers = tuple(
        marker
        for marker in _REQUIRED_BOOT_MARKERS
        if marker in outcome.markers
    )
    missing_markers = tuple(
        marker for marker in _REQUIRED_BOOT_MARKERS if marker not in markers
    )
    issues = [
        f"missing required boot marker: {marker}"
        for marker in missing_markers
    ]
    issues.extend(
        f"boot monitor error: {error}" for error in outcome.errors
    )
    if outcome.state == "error" and not outcome.errors:
        issues.append("boot monitor reported an unspecified error")
    if outcome.state not in {
        "markers",
        "error",
        "timeout",
        "early_exit",
    }:
        issues.append(
            f"boot monitor returned an unexpected state: {outcome.state}"
        )
    if outcome.state == "timeout" and len(missing_markers) != 1:
        issues.append(
            f"boot probe timeout after {timeout_seconds} seconds"
        )
    if outcome.exit_code is not None:
        issues.append(
            "launcher exited unexpectedly before probe completion "
            f"with code {outcome.exit_code}"
        )
    elif outcome.state == "early_exit":
        issues.append(
            "launcher exited unexpectedly before probe completion "
            "without an exit code"
        )
    return markers, tuple(issues)


def _postflight_issues(
    preflight: _BootSnapshot,
    postflight: _BootSnapshot,
    app: Path,
) -> tuple[str, ...]:
    issues = list(_preflight_issues(postflight, app))
    if postflight.assembly_sha256 != preflight.assembly_sha256:
        issues.append("game assembly SHA-256 changed during boot probe")
    if (
        postflight.active_preloader_sha256
        != preflight.active_preloader_sha256
    ):
        issues.append("active preloader SHA-256 changed during boot probe")
    if _app_signature_identity(
        postflight.app_signature
    ) != _app_signature_identity(preflight.app_signature):
        issues.append(
            "game app code-signature result changed during boot probe"
        )
    return tuple(issues)


def _app_signature_payload(signature: _AppSignature) -> dict[str, Any]:
    return {
        "returncode": signature.returncode,
        "stdout": signature.stdout,
        "stderr": signature.stderr,
    }


def _boot_snapshot_payload(snapshot: _BootSnapshot) -> dict[str, Any]:
    return {
        "assembly_sha256": snapshot.assembly_sha256,
        "active_preloader_sha256": snapshot.active_preloader_sha256,
        "installer_healthy": snapshot.installer_healthy,
        "compatibility_state": snapshot.compatibility_state,
        "app_signature": _app_signature_payload(snapshot.app_signature),
    }


def _log_fingerprint_payload(
    fingerprint: LogFingerprint,
) -> dict[str, Any]:
    return {
        "path": str(fingerprint.path),
        "file_type": fingerprint.file_type,
        "inode": fingerprint.inode,
        "size": fingerprint.size,
        "mtime_ns": fingerprint.mtime_ns,
        "sha256": fingerprint.sha256,
    }


def _probe_result_payload(
    result: BootProbeResult,
    preflight: _BootSnapshot,
    postflight: _BootSnapshot,
    before_logs: tuple[LogFingerprint, ...],
    after_logs: tuple[LogFingerprint, ...],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "success": result.success,
        "exit_code": result.exit_code,
        "markers": list(result.markers),
        "issues": list(result.issues),
        "before": _boot_snapshot_payload(preflight),
        "after": _boot_snapshot_payload(postflight),
        "before_logs": [
            _log_fingerprint_payload(fingerprint)
            for fingerprint in before_logs
        ],
        "after_logs": [
            _log_fingerprint_payload(fingerprint)
            for fingerprint in after_logs
        ],
        "moved_logs": [str(path) for path in result.moved_logs],
        "copied_logs": [str(path) for path in result.copied_logs],
    }


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
    config_guard: _ConfigGuard | None = None
    disk_logging_guard: _DiskLoggingConfigGuard | None = None
    restore_required = False
    game_handle: _DirectoryHandle | None = None
    launcher_guard: _LauncherGuard | None = None
    retained: _RetainedBootEvidence | None = None
    staged_probe: _StagedProbeJson | None = None
    primary_error: BaseException | None = None
    try:
        config_guard = _open_config_guard(config_path)
        _require_initial_off_config(config_guard)
        restore_required = True
        disk_logging_guard = _open_bepinex_disk_logging_guard(game)
        game_handle = _open_absolute_directory(game, "game root")
        launcher_guard = _open_launcher_guard(launcher_path)
        before = fingerprint_preloader_logs(game)
        preflight = _capture_boot_snapshot(game)
        _verify_config_guard_unchanged(config_guard)
        issues = _preflight_issues(preflight, game / "Sausage.app")
        if issues:
            preserved = collect_boot_evidence(before, game, evidence)
            return BootProbeResult(
                success=False,
                evidence_dir=preserved.evidence_dir,
                moved_logs=preserved.moved_logs,
                copied_logs=preserved.copied_logs,
                markers=(),
                issues=issues + preserved.issues,
                exit_code=None,
            )

        _verify_pinned_directory_path(
            game,
            game_handle,
            "game root at launch",
        )
        _verify_launcher_guard(launcher_guard)
        _verify_config_guard_unchanged(config_guard)
        _boot_log_contract = (
            _verify_and_close_bepinex_disk_logging_guard(
                disk_logging_guard
            )
        )
        disk_logging_guard = None
        before = fingerprint_preloader_logs(game)
        process: subprocess.Popen[bytes] | None = None
        spawned_pgid: int | None = None
        cleanup_exit_code: int | None = None
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

        _verify_pinned_directory_path(
            game,
            game_handle,
            "game root after process cleanup",
        )
        final_exit_code = (
            _monitor_outcome.exit_code
            if _monitor_outcome.exit_code is not None
            else cleanup_exit_code
        )
        after_logs = _fingerprint_regular_preloader_logs(game)
        _verify_pinned_directory_path(
            game,
            game_handle,
            "game root after log snapshot",
        )
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
        preserved = retained.public
        final_outcome = _MonitorOutcome(
            state=_monitor_outcome.state,
            markers=decision.markers,
            errors=decision.errors,
            exit_code=final_exit_code,
        )
        _verify_pinned_directory_path(
            game,
            game_handle,
            "game root after evidence collection",
        )
        postflight = _capture_boot_snapshot(game)
        _verify_pinned_directory_path(
            game,
            game_handle,
            "game root after postflight",
        )
        markers, monitor_issues = _monitor_result_issues(
            final_outcome,
            timeout,
        )
        postflight_issues = _postflight_issues(
            preflight,
            postflight,
            game / "Sausage.app",
        )
        result_issues = (
            preserved.issues + monitor_issues + postflight_issues
        )
        monitor_succeeded = (
            final_outcome.state == "markers"
            and markers == _REQUIRED_BOOT_MARKERS
            and not final_outcome.errors
            and final_outcome.exit_code is None
        )
        result = BootProbeResult(
            success=monitor_succeeded and not result_issues,
            evidence_dir=preserved.evidence_dir,
            moved_logs=preserved.moved_logs,
            copied_logs=preserved.copied_logs,
            markers=markers,
            issues=result_issues,
            exit_code=final_outcome.exit_code,
        )
        payload = _probe_result_payload(
            result,
            preflight,
            postflight,
            before,
            after_logs,
        )

        _restore_config_guard(config_guard)
        restore_required = False

        launcher_guard.close()
        launcher_guard = None
        game_handle.close()
        game_handle = None
        config_guard.close()
        config_guard = None

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
        return result
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        cleanup_errors: list[tuple[str, BaseException]] = []

        if restore_required and config_guard is not None:
            try:
                _restore_config_guard_for_failure_cleanup(config_guard)
            except BaseException as exc:
                cleanup_errors.append(("config restore failed", exc))
            else:
                restore_required = False
        if launcher_guard is not None:
            try:
                launcher_guard.close()
            except BaseException as exc:
                cleanup_errors.append(("launcher guard close failed", exc))
        if disk_logging_guard is not None:
            try:
                disk_logging_guard.close()
            except BaseException as exc:
                cleanup_errors.append(
                    ("BepInEx disk logging guard close failed", exc)
                )
        if game_handle is not None:
            try:
                game_handle.close()
            except BaseException as exc:
                cleanup_errors.append(
                    ("retained game handle close failed", exc)
                )
        if config_guard is not None:
            try:
                config_guard.close()
            except BaseException as exc:
                cleanup_errors.append(("config guard close failed", exc))
        if retained is not None:
            try:
                retained.close()
            except BaseException as exc:
                cleanup_errors.append(
                    ("retained boot evidence close failed", exc)
                )
        if staged_probe is not None:
            try:
                _close_staged_probe_json(staged_probe)
            except BaseException as exc:
                cleanup_errors.append(
                    ("staged probe JSON close failed", exc)
                )

        if primary_error is not None:
            for label, error in cleanup_errors:
                _note_later_error(primary_error, label, error)
        elif cleanup_errors:
            _label, cleanup_error = cleanup_errors[0]
            for later_label, later_error in cleanup_errors[1:]:
                _note_later_error(
                    cleanup_error,
                    later_label,
                    later_error,
                )
            raise cleanup_error


_TOKEN_PATTERN = re.compile(r"[0-9a-f]{32}\Z")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the controlled SSR oracle boot probe.",
    )
    parser.add_argument("--game-root", required=True)
    parser.add_argument("--launcher", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    try:
        result = run_boot_probe(
            Path(os.path.abspath(args.game_root)),
            Path(os.path.abspath(args.launcher)),
            Path(os.path.abspath(args.config)),
            Path(os.path.abspath(args.evidence_root)),
            args.timeout,
        )
    except (ValueError, RuntimeError, OSError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    payload = {
        "success": result.success,
        "evidence_dir": str(result.evidence_dir),
        "moved_logs": [str(path) for path in result.moved_logs],
        "copied_logs": [str(path) for path in result.copied_logs],
        "markers": list(result.markers),
        "issues": list(result.issues),
        "exit_code": result.exit_code,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    sys.stdout.write(encoded + "\n")
    return 0 if result.success else 1
