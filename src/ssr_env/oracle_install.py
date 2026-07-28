"""Safe installation and recovery helpers for the executable SSR oracle."""

from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
import secrets
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Literal, Sequence
from zipfile import BadZipFile, ZipFile, ZipInfo

from ssr_env.oracle_compat import (
    EXPECTED_PATCHED_PRELOADER_SHA256,
    CompatError,
    load_provenance,
    load_trust,
)

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
REQUIRED_ARCHIVE_FILES = {
    "run_bepinex.sh",
    ".doorstop_version",
    "libdoorstop.dylib",
    "BepInEx/core/BepInEx.dll",
    "BepInEx/core/0Harmony.dll",
}
REQUIRED_RUNTIME_DIRECTORIES = {
    "BepInEx",
    "BepInEx/core",
}
PLUGIN_RELATIVE_PATH = "BepInEx/plugins/SsrOracle.Plugin.dll"
CONFIG_RELATIVE_PATH = "BepInEx/config/dev.jlsor.ssr.oracle.cfg"
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
_PRELOADER_BACKUP_ROOT = "BepInEx/.ssr-oracle-backup"
_PRELOADER_COMPAT_ROOT = "BepInEx/.ssr-oracle-compat"
_HASH_LENGTH = 64


class InstallError(RuntimeError):
    """An installation request failed a validation or safety check."""


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


@dataclass(frozen=True, slots=True)
class PreloaderCompatibilityStatus:
    state: Literal["official", "patched", "invalid"]
    official_sha256: str
    active_sha256: str | None
    patched_sha256: str | None
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InstallStatus:
    manifest: InstallManifest
    missing: tuple[str, ...]
    changed: tuple[str, ...]
    preloader_compatibility: PreloaderCompatibilityStatus

    @property
    def healthy(self) -> bool:
        return (
            not self.missing
            and not self.changed
            and self.preloader_compatibility.state != "invalid"
        )


@dataclass(frozen=True, slots=True)
class _FileSnapshot:
    payload: bytes
    mode: int


@dataclass(frozen=True, slots=True)
class _StableFileSnapshot:
    payload: bytes
    mode: int
    device: int
    inode: int
    size: int


@dataclass(frozen=True, slots=True)
class _FileIdentity:
    device: int
    inode: int


@dataclass(slots=True)
class _DirectoryHandle:
    fd: int
    device: int
    inode: int
    label: str

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


@dataclass(slots=True)
class _CompatStaging:
    name: str
    root: _DirectoryHandle
    bep_in_ex: _DirectoryHandle
    backup: _DirectoryHandle
    compat: _DirectoryHandle
    core: _DirectoryHandle
    files: dict[str, tuple[_DirectoryHandle, str, _FileIdentity]]


@dataclass(slots=True)
class _CompatRecovery:
    parent: _DirectoryHandle
    parent_created: bool
    run_name: str
    run: _DirectoryHandle
    compat: _DirectoryHandle
    bep_in_ex: _DirectoryHandle
    backup: _DirectoryHandle
    provenance: _DirectoryHandle
    cleanup: _DirectoryHandle


def _sha256_file(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise InstallError(f"cannot read {path}: {exc}") from exc
    return digest.hexdigest()


def _inside(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise InstallError(f"path escapes game root: {candidate}")
    return resolved


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def inspect_game(game_root: Path) -> GameInstall:
    """Validate and describe the supported macOS Stephen's Sausage Roll install."""
    root = game_root.resolve()
    app = root / "Sausage.app"
    executable = app / "Contents/MacOS/Sausage"
    managed = app / "Contents/Resources/Data/Managed"
    assembly = managed / "Assembly-CSharp.dll"

    if not executable.is_file():
        raise InstallError(f"missing game executable: {executable}")
    if not assembly.is_file():
        raise InstallError(f"missing game assembly: {assembly}")

    assembly_hash = _sha256_file(assembly)
    if assembly_hash != EXPECTED_ASSEMBLY_SHA256:
        raise InstallError(
            "unsupported Assembly-CSharp.dll: "
            f"expected {EXPECTED_ASSEMBLY_SHA256}, got {assembly_hash}"
        )
    return GameInstall(
        root=root,
        app=app.resolve(),
        managed=managed.resolve(),
        assembly=assembly.resolve(),
        assembly_sha256=assembly_hash,
    )


def _archive_path(info: ZipInfo) -> tuple[str, bool]:
    raw_name = info.filename
    path = PurePosixPath(raw_name)
    if (
        not raw_name
        or "\x00" in raw_name
        or "\\" in raw_name
        or path.is_absolute()
        or raw_name.startswith("/")
        or any(part == ".." for part in path.parts)
    ):
        raise InstallError(f"unsafe archive member: {raw_name!r}")

    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise InstallError(f"unsafe archive member: {raw_name!r}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise InstallError(f"archive member is a symlink: {raw_name!r}")
    top_level = path.parts[0]
    if top_level not in ALLOWED_TOP_LEVEL:
        raise InstallError(f"unknown top-level archive member: {raw_name!r}")
    is_dir = info.is_dir()
    if top_level != "BepInEx" and (len(path.parts) != 1 or is_dir):
        raise InstallError(
            f"top-level runtime file cannot contain children: {raw_name!r}"
        )
    return normalized, is_dir


def _validated_archive_infos(
    archive: Path,
) -> tuple[tuple[ArchiveMember, ZipInfo], ...]:
    if not archive.is_file():
        raise InstallError(f"archive is not a file: {archive}")
    validated: list[tuple[ArchiveMember, ZipInfo]] = []
    seen: set[str] = set()
    try:
        with ZipFile(archive) as zf:
            for info in zf.infolist():
                name, is_dir = _archive_path(info)
                if name in seen:
                    raise InstallError(f"duplicate archive member: {name}")
                seen.add(name)
                validated.append(
                    (
                        ArchiveMember(
                            name=name,
                            is_dir=is_dir,
                            size=info.file_size,
                        ),
                        info,
                    )
                )
    except (BadZipFile, OSError) as exc:
        raise InstallError(f"cannot inspect archive {archive}: {exc}") from exc

    files = {member.name for member, _ in validated if not member.is_dir}
    missing = sorted(REQUIRED_ARCHIVE_FILES - files)
    if missing:
        raise InstallError(
            "missing required archive member(s): " + ", ".join(missing)
        )

    kinds = {member.name: member.is_dir for member, _ in validated}
    for name, is_dir in kinds.items():
        parts = PurePosixPath(name).parts
        for index in range(1, len(parts)):
            parent = PurePosixPath(*parts[:index]).as_posix()
            if parent in kinds and not kinds[parent]:
                raise InstallError(
                    f"archive file conflicts with child member: {parent}"
                )
        if is_dir and name in REQUIRED_ARCHIVE_FILES:
            raise InstallError(f"required archive member is not a file: {name}")
    return tuple(validated)


def inspect_archive(archive: Path) -> tuple[ArchiveMember, ...]:
    """Return validated, normalized archive members without extracting them."""
    return tuple(member for member, _ in _validated_archive_infos(archive))


def _manifest_to_dict(manifest: InstallManifest) -> dict[str, object]:
    entries = sorted(manifest.entries, key=lambda entry: entry.relative_path)
    return {
        "schema_version": manifest.schema_version,
        "game_assembly_sha256": manifest.game_assembly_sha256,
        "runtime_archive_sha256": manifest.runtime_archive_sha256,
        "entries": [
            {
                "relative_path": entry.relative_path,
                "kind": entry.kind,
                "sha256": entry.sha256,
            }
            for entry in entries
        ],
    }


def _atomic_replace_bytes(target: Path, payload: bytes, mode: int = 0o644) -> None:
    temporary: Path | None = None
    descriptor = -1
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        stream = os.fdopen(descriptor, "wb")
        descriptor = -1
        with stream:
            stream.write(payload)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        _fsync_directory(target.parent)
    except OSError as exc:
        raise InstallError(f"cannot atomically write {target}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None and _path_exists(temporary):
            try:
                temporary.unlink()
            except OSError:
                pass


def _fsync_directory(path: Path) -> None:
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        os.fsync(descriptor)
    except OSError as exc:
        raise InstallError(f"cannot durably sync directory {path}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _atomic_write_bytes(target: Path, payload: bytes, mode: int = 0o644) -> None:
    _atomic_replace_bytes(target, payload, mode)


def _write_manifest(root: Path, manifest: InstallManifest) -> None:
    payload = (
        json.dumps(_manifest_to_dict(manifest), sort_keys=True, indent=2) + "\n"
    ).encode()
    _atomic_write_bytes(root / MANIFEST_NAME, payload)


def _is_hash(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _HASH_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_keys(
    value: dict[str, object], required: set[str], description: str
) -> None:
    if set(value) != required:
        raise InstallError(
            f"malformed {description}: expected keys {sorted(required)}"
        )


def _validated_manifest_path(root: Path, relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if any(part == ".." for part in pure.parts):
        raise InstallError(
            f"manifest path contains parent traversal: {relative_path!r}"
        )
    candidate = root / Path(*pure.parts)
    if (
        not relative_path
        or "\x00" in relative_path
        or "\\" in relative_path
        or pure.is_absolute()
        or pure.as_posix() != relative_path
        or relative_path in {".", ".."}
    ):
        raise InstallError(f"malformed manifest path: {relative_path!r}")
    top_level = pure.parts[0]
    if top_level not in ALLOWED_TOP_LEVEL:
        raise InstallError(f"unapproved manifest path: {relative_path}")
    if top_level != "BepInEx" and len(pure.parts) != 1:
        raise InstallError(f"unapproved manifest path: {relative_path}")
    return candidate


def _load_manifest(root: Path) -> InstallManifest:
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise InstallError(f"recognized install manifest not found: {manifest_path}")
    try:
        decoded = json.loads(manifest_path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstallError(f"cannot parse install manifest: {exc}") from exc
    if not isinstance(decoded, dict):
        raise InstallError("malformed install manifest: expected an object")
    _require_keys(
        decoded,
        {
            "schema_version",
            "game_assembly_sha256",
            "runtime_archive_sha256",
            "entries",
        },
        "install manifest",
    )
    if type(decoded["schema_version"]) is not int or decoded["schema_version"] != 1:
        raise InstallError(
            f"unknown manifest schema: {decoded['schema_version']!r}"
        )
    game_hash = decoded["game_assembly_sha256"]
    archive_hash = decoded["runtime_archive_sha256"]
    if not _is_hash(game_hash):
        raise InstallError("malformed game_assembly_sha256")
    if archive_hash is not None and not _is_hash(archive_hash):
        raise InstallError("malformed runtime_archive_sha256")

    raw_entries = decoded["entries"]
    if not isinstance(raw_entries, list):
        raise InstallError("malformed manifest entries: expected a list")
    entries: list[ManifestEntry] = []
    seen: set[str] = set()
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            raise InstallError("malformed manifest entry: expected an object")
        _require_keys(
            raw_entry,
            {"relative_path", "kind", "sha256"},
            "manifest entry",
        )
        relative_path = raw_entry["relative_path"]
        kind = raw_entry["kind"]
        entry_hash = raw_entry["sha256"]
        if not isinstance(relative_path, str):
            raise InstallError("malformed manifest relative_path")
        _validated_manifest_path(root, relative_path)
        if relative_path in seen:
            raise InstallError(f"duplicate manifest path: {relative_path}")
        seen.add(relative_path)
        if not isinstance(kind, str) or kind not in {"file", "directory"}:
            raise InstallError(f"malformed manifest entry kind: {kind!r}")
        if kind == "file" and not _is_hash(entry_hash):
            raise InstallError(f"malformed sha256 for file {relative_path}")
        if kind == "directory" and entry_hash is not None:
            raise InstallError(
                f"directory sha256 must be null: {relative_path}"
            )
        pure = PurePosixPath(relative_path)
        if relative_path == "BepInEx" and kind != "directory":
            raise InstallError("BepInEx manifest root must be a directory")
        if pure.parts[0] != "BepInEx" and kind != "file":
            raise InstallError(
                f"top-level runtime target must be a file: {relative_path}"
            )
        entries.append(
            ManifestEntry(
                relative_path=relative_path,
                kind=kind,
                sha256=entry_hash if isinstance(entry_hash, str) else None,
            )
        )

    by_path = {entry.relative_path: entry for entry in entries}
    for entry in entries:
        parts = PurePosixPath(entry.relative_path).parts
        for index in range(1, len(parts)):
            parent = PurePosixPath(*parts[:index]).as_posix()
            parent_entry = by_path.get(parent)
            if parent_entry is None or parent_entry.kind != "directory":
                raise InstallError(
                    f"manifest path lacks owned directory parent: {entry.relative_path}"
                )
    if archive_hash is not None:
        missing_runtime_ownership = sorted(
            path
            for path in REQUIRED_ARCHIVE_FILES
            if by_path.get(path) is None or by_path[path].kind != "file"
        )
        missing_runtime_ownership.extend(
            sorted(
                path
                for path in REQUIRED_RUNTIME_DIRECTORIES
                if by_path.get(path) is None
                or by_path[path].kind != "directory"
            )
        )
        if missing_runtime_ownership:
            raise InstallError(
                "manifest lacks required runtime ownership: "
                + ", ".join(missing_runtime_ownership)
            )
    return InstallManifest(
        schema_version=1,
        game_assembly_sha256=game_hash,
        runtime_archive_sha256=archive_hash,
        entries=tuple(sorted(entries, key=lambda entry: entry.relative_path)),
    )


def _rewrite_executable_assignment(script: Path) -> None:
    try:
        payload = script.read_bytes()
    except OSError as exc:
        raise InstallError(f"cannot read run_bepinex.sh: {exc}") from exc
    found = False
    rewritten: list[bytes] = []
    for line in payload.splitlines(keepends=True):
        ending = b""
        body = line
        if line.endswith(b"\r\n"):
            body, ending = line[:-2], b"\r\n"
        elif line.endswith(b"\n") or line.endswith(b"\r"):
            body, ending = line[:-1], line[-1:]
        if body == b'executable_name=""':
            body = b'executable_name="Sausage.app"'
            found = True
        rewritten.append(body + ending)
    if not found:
        raise InstallError(
            'run_bepinex.sh lacks executable_name="" assignment'
        )
    try:
        script.write_bytes(b"".join(rewritten))
        script.chmod(0o755)
    except OSError as exc:
        raise InstallError(f"cannot update run_bepinex.sh: {exc}") from exc


def _entry_directories(members: Sequence[ArchiveMember]) -> set[str]:
    directories: set[str] = set()
    for member in members:
        parts = PurePosixPath(member.name).parts
        last = len(parts) if member.is_dir else len(parts) - 1
        for index in range(1, last + 1):
            directories.add(PurePosixPath(*parts[:index]).as_posix())
    return directories


def install_runtime(game_root: Path, archive: Path) -> InstallManifest:
    """Install a validated BepInEx archive and record exactly what it owns."""
    game = inspect_game(game_root)
    manifest_path = game.root / MANIFEST_NAME
    if _path_exists(manifest_path):
        raise InstallError(f"install manifest already exists: {manifest_path}")

    archive_hash = _sha256_file(archive)
    if archive_hash != EXPECTED_RUNTIME_ARCHIVE_SHA256:
        raise InstallError(
            "unsupported BepInEx runtime archive: "
            f"expected {EXPECTED_RUNTIME_ARCHIVE_SHA256}, got {archive_hash}"
        )
    validated = _validated_archive_infos(archive)
    members = tuple(member for member, _ in validated)
    top_levels = sorted(
        {PurePosixPath(member.name).parts[0] for member in members}
    )
    for top_level in top_levels:
        target = _inside(game.root, game.root / top_level)
        if _path_exists(target):
            if top_level == "BepInEx":
                raise InstallError(
                    f"unmanaged BepInEx already exists: {target}"
                )
            raise InstallError(
                f"unmanaged install target already exists: {target}"
            )

    try:
        staging = Path(
            tempfile.mkdtemp(prefix=".ssr-oracle-staging-", dir=game.root)
        )
    except OSError as exc:
        raise InstallError(f"cannot create runtime staging directory: {exc}") from exc
    moved: list[tuple[Path, Path]] = []
    try:
        with ZipFile(archive) as zf:
            for member, info in validated:
                target = _inside(
                    staging,
                    staging / Path(*PurePosixPath(member.name).parts),
                )
                if member.is_dir:
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with zf.open(info) as source, target.open("xb") as destination:
                        shutil.copyfileobj(source, destination)
                except (OSError, BadZipFile, EOFError, RuntimeError) as exc:
                    raise InstallError(
                        f"cannot extract archive member {member.name}: {exc}"
                    ) from exc

        script = staging / "run_bepinex.sh"
        _rewrite_executable_assignment(script)
        if _sha256_file(archive) != archive_hash:
            raise InstallError("BepInEx runtime archive changed during installation")
        directories = _entry_directories(members)
        entries = [
            ManifestEntry(path, "directory", None)
            for path in directories
        ]
        entries.extend(
            ManifestEntry(
                member.name,
                "file",
                _sha256_file(
                    staging / Path(*PurePosixPath(member.name).parts)
                ),
            )
            for member in members
            if not member.is_dir
        )
        manifest = InstallManifest(
            schema_version=1,
            game_assembly_sha256=game.assembly_sha256,
            runtime_archive_sha256=archive_hash,
            entries=tuple(
                sorted(entries, key=lambda entry: entry.relative_path)
            ),
        )

        for top_level in top_levels:
            source = _inside(staging, staging / top_level)
            target = _inside(game.root, game.root / top_level)
            try:
                source.replace(target)
            except OSError as exc:
                raise InstallError(
                    f"cannot publish runtime root {top_level}: {exc}"
                ) from exc
            moved.append((source, target))
        _write_manifest(game.root, manifest)
        return manifest
    except Exception:
        for source, target in reversed(moved):
            if _path_exists(target) and not _path_exists(source):
                target.replace(source)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _inspected_manifest(game_root: Path) -> tuple[GameInstall, InstallManifest]:
    game = inspect_game(game_root)
    manifest = _load_manifest(game.root)
    if manifest.game_assembly_sha256 != game.assembly_sha256:
        raise InstallError(
            "manifest game assembly hash does not match the inspected game"
        )
    return game, manifest


def _validate_deploy_parents(root: Path, target: Path) -> None:
    relative = target.relative_to(root)
    current = root
    for part in relative.parts[:-1]:
        current /= part
        if _path_exists(current) and (
            current.is_symlink() or not current.is_dir()
        ):
            raise InstallError(
                f"deploy parent is not a safe directory: {current}"
            )


def _entry_health(
    root: Path, entries: Sequence[ManifestEntry]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    missing: list[str] = []
    changed: list[str] = []
    for entry in entries:
        target = _validated_manifest_path(root, entry.relative_path)
        parts = PurePosixPath(entry.relative_path).parts
        current = root
        safe_parents = True
        unsafe_parent_kind = "other"
        for part in parts[:-1]:
            current /= part
            parent_kind = _lstat_kind(current)
            if parent_kind != "directory":
                safe_parents = False
                unsafe_parent_kind = parent_kind
                break
        target_kind = _lstat_kind(target) if safe_parents else "other"
        if target_kind == "absent" or (
            not safe_parents and unsafe_parent_kind in {"absent", "file"}
        ):
            missing.append(entry.relative_path)
        elif entry.kind == "directory":
            if target_kind != "directory":
                changed.append(entry.relative_path)
        elif target_kind != "file":
            changed.append(entry.relative_path)
        elif _sha256_file(target) != entry.sha256:
            changed.append(entry.relative_path)
    return tuple(sorted(missing)), tuple(sorted(changed))


def _require_healthy_runtime(root: Path, manifest: InstallManifest) -> None:
    required_paths = REQUIRED_ARCHIVE_FILES | REQUIRED_RUNTIME_DIRECTORIES
    required_entries = tuple(
        entry
        for entry in manifest.entries
        if entry.relative_path in required_paths
    )
    missing, changed = _entry_health(root, required_entries)
    if missing or changed:
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if changed:
            details.append("changed=" + ",".join(changed))
        raise InstallError("installed runtime is not healthy: " + "; ".join(details))


def _snapshot_file(path: Path) -> _FileSnapshot:
    try:
        return _FileSnapshot(
            payload=path.read_bytes(),
            mode=stat.S_IMODE(path.stat().st_mode),
        )
    except OSError as exc:
        raise InstallError(f"cannot preserve existing file {path}: {exc}") from exc


def _stage_deploy_payloads(
    root: Path, payloads: dict[str, bytes]
) -> tuple[Path, dict[str, Path]]:
    try:
        staging = Path(
            tempfile.mkdtemp(prefix=".ssr-oracle-deploy-staging-", dir=root)
        )
    except OSError as exc:
        raise InstallError(f"cannot create deploy staging directory: {exc}") from exc
    staged: dict[str, Path] = {}
    try:
        for relative_path, payload in payloads.items():
            target = _inside(
                staging,
                staging / Path(*PurePosixPath(relative_path).parts),
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            staged[relative_path] = target
    except OSError as exc:
        shutil.rmtree(staging, ignore_errors=True)
        raise InstallError(f"cannot stage deploy payloads: {exc}") from exc
    return staging, staged


def _create_deploy_parents(
    root: Path, targets: Sequence[Path]
) -> list[Path]:
    created: list[Path] = []
    try:
        for target in targets:
            relative = target.relative_to(root)
            current = root
            for part in relative.parts[:-1]:
                current /= part
                if not _path_exists(current):
                    current.mkdir()
                    created.append(current)
    except OSError as exc:
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise InstallError(f"cannot create deploy parent directories: {exc}") from exc
    return created


def _restore_deploy_state(
    *,
    targets: dict[str, Path],
    snapshots: dict[str, _FileSnapshot | None],
    manifest_path: Path,
    manifest_snapshot: _FileSnapshot,
    created_directories: Sequence[Path],
) -> None:
    errors: list[str] = []
    for relative_path, target in targets.items():
        snapshot = snapshots[relative_path]
        try:
            if snapshot is None:
                if _path_exists(target):
                    if target.is_symlink() or not target.is_file():
                        raise InstallError(
                            f"rollback target changed type: {target}"
                        )
                    target.unlink()
            else:
                _atomic_replace_bytes(target, snapshot.payload, snapshot.mode)
        except (InstallError, OSError) as exc:
            errors.append(str(exc))

    try:
        current_manifest = (
            _snapshot_file(manifest_path)
            if _path_exists(manifest_path)
            else None
        )
        if current_manifest != manifest_snapshot:
            _atomic_replace_bytes(
                manifest_path,
                manifest_snapshot.payload,
                manifest_snapshot.mode,
            )
    except InstallError as exc:
        errors.append(str(exc))

    for directory in reversed(created_directories):
        try:
            directory.rmdir()
        except OSError as exc:
            errors.append(f"cannot remove created deploy directory {directory}: {exc}")
    if errors:
        raise InstallError("deploy rollback failed: " + "; ".join(errors))


def deploy_plugin(
    game_root: Path, plugin: Path, config_text: str
) -> InstallManifest:
    """Deploy the oracle DLL and config into fixed, manifest-owned paths."""
    if plugin.suffix.lower() != ".dll":
        raise InstallError(f"plugin must have a .dll suffix: {plugin}")
    if not plugin.is_file():
        raise InstallError(f"plugin is not a file: {plugin}")
    game, manifest = _inspected_manifest(game_root)
    if manifest.runtime_archive_sha256 is None:
        raise InstallError("manifest does not describe an installed runtime")
    _require_healthy_runtime(game.root, manifest)

    try:
        plugin_payload = plugin.read_bytes()
    except OSError as exc:
        raise InstallError(f"cannot read plugin {plugin}: {exc}") from exc
    by_path = {entry.relative_path: entry for entry in manifest.entries}
    payloads = {
        PLUGIN_RELATIVE_PATH: plugin_payload,
        CONFIG_RELATIVE_PATH: config_text.encode(),
    }
    targets: dict[str, Path] = {}
    for relative_path in payloads:
        target = _validated_manifest_path(game.root, relative_path)
        targets[relative_path] = target
        owned = by_path.get(relative_path)
        if _path_exists(target):
            if owned is None:
                raise InstallError(
                    f"unmanaged deploy target already exists: {target}"
                )
            if owned.kind != "file" or target.is_symlink() or not target.is_file():
                raise InstallError(f"owned deploy target has changed type: {target}")
        _validate_deploy_parents(game.root, target)

    staging, staged = _stage_deploy_payloads(game.root, payloads)
    try:
        snapshots = {
            relative_path: (
                _snapshot_file(target) if _path_exists(target) else None
            )
            for relative_path, target in targets.items()
        }
        manifest_path = game.root / MANIFEST_NAME
        manifest_snapshot = _snapshot_file(manifest_path)
        for relative_path in targets:
            parts = PurePosixPath(relative_path).parts
            for index in range(1, len(parts)):
                directory = PurePosixPath(*parts[:index]).as_posix()
                by_path[directory] = ManifestEntry(
                    directory, "directory", None
                )
            by_path[relative_path] = ManifestEntry(
                relative_path,
                "file",
                sha256(payloads[relative_path]).hexdigest(),
            )
        updated = InstallManifest(
            schema_version=manifest.schema_version,
            game_assembly_sha256=manifest.game_assembly_sha256,
            runtime_archive_sha256=manifest.runtime_archive_sha256,
            entries=tuple(
                sorted(by_path.values(), key=lambda entry: entry.relative_path)
            ),
        )
        created_directories: list[Path] = []
        try:
            created_directories = _create_deploy_parents(
                game.root, tuple(targets.values())
            )
            for relative_path, target in targets.items():
                _atomic_write_bytes(
                    target, staged[relative_path].read_bytes()
                )
            _write_manifest(game.root, updated)
            return updated
        except Exception as exc:
            try:
                _restore_deploy_state(
                    targets=targets,
                    snapshots=snapshots,
                    manifest_path=manifest_path,
                    manifest_snapshot=manifest_snapshot,
                    created_directories=created_directories,
                )
            except InstallError as rollback_error:
                raise InstallError(
                    f"deploy failed ({exc}); {rollback_error}"
                ) from exc
            if isinstance(exc, InstallError):
                raise
            if isinstance(exc, OSError):
                raise InstallError(
                    f"cannot publish deploy payloads: {exc}"
                ) from exc
            raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


_DIRECTORY_OPEN_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_RENAME_SWAP = 0x00000002
_RENAME_EXCL = 0x00000004
_RENAME_NOFOLLOW_ANY = 0x00000010
_LIBC = ctypes.CDLL(None, use_errno=True)
_RENAMEATX_NP = _LIBC.renameatx_np
_RENAMEATX_NP.argtypes = (
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_uint,
)
_RENAMEATX_NP.restype = ctypes.c_int


def _require_safe_leaf(name: str, description: str) -> None:
    if not name or "/" in name or "\x00" in name or name in {".", ".."}:
        raise InstallError(f"unsafe leaf for {description}")


class _RenameAtError(InstallError):
    def __init__(self, error_number: int, message: str):
        super().__init__(message)
        self.error_number = error_number


def _renameatx(
    source_parent: _DirectoryHandle,
    source_name: str,
    destination_parent: _DirectoryHandle,
    destination_name: str,
    flags: int,
    description: str,
) -> None:
    for name in (source_name, destination_name):
        _require_safe_leaf(name, f"rename {description}")
    result = _RENAMEATX_NP(
        source_parent.fd,
        os.fsencode(source_name),
        destination_parent.fd,
        os.fsencode(destination_name),
        flags | _RENAME_NOFOLLOW_ANY,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise _RenameAtError(
            error_number,
            f"cannot {description}: "
            f"[Errno {error_number}] {os.strerror(error_number)}",
        )


def _fsync_rename_parents(
    source_parent: _DirectoryHandle,
    destination_parent: _DirectoryHandle,
    boundary_prefix: str,
) -> None:
    _fsync_handle(
        source_parent, f"{boundary_prefix}_source_parent_fsync"
    )
    if destination_parent.fd != source_parent.fd:
        _fsync_handle(
            destination_parent,
            f"{boundary_prefix}_destination_parent_fsync",
        )


def _lexical_absolute(path: Path, description: str) -> Path:
    try:
        raw = os.fspath(path)
        if "\x00" in raw:
            raise ValueError("NUL byte")
        return Path(os.path.abspath(raw))
    except (OSError, TypeError, ValueError) as exc:
        raise InstallError(f"cannot resolve {description}: {exc}") from exc


def _directory_handle(fd: int, label: str) -> _DirectoryHandle:
    try:
        observed = os.fstat(fd)
    except OSError as exc:
        os.close(fd)
        raise InstallError(f"cannot inspect {label}: {exc}") from exc
    if not stat.S_ISDIR(observed.st_mode):
        os.close(fd)
        raise InstallError(f"{label} is not a directory")
    return _DirectoryHandle(fd, observed.st_dev, observed.st_ino, label)


def _open_absolute_directory(path: Path, description: str) -> _DirectoryHandle:
    absolute = _lexical_absolute(path, description)
    current = -1
    try:
        current = os.open("/", _DIRECTORY_OPEN_FLAGS)
        for part in absolute.parts[1:]:
            following = os.open(part, _DIRECTORY_OPEN_FLAGS, dir_fd=current)
            os.close(current)
            current = following
        handle = _directory_handle(current, description)
        current = -1
        return handle
    except OSError as exc:
        raise InstallError(
            f"cannot open {description} without following symlinks: {exc}"
        ) from exc
    finally:
        if current >= 0:
            os.close(current)


def _open_child_directory(
    parent: _DirectoryHandle, name: str, description: str
) -> _DirectoryHandle:
    try:
        descriptor = os.open(
            name,
            _DIRECTORY_OPEN_FLAGS,
            dir_fd=parent.fd,
        )
    except OSError as exc:
        raise InstallError(
            f"cannot open {description} without following symlinks: {exc}"
        ) from exc
    return _directory_handle(descriptor, description)


def _verify_directory_handle(handle: _DirectoryHandle) -> None:
    try:
        observed = os.fstat(handle.fd)
    except OSError as exc:
        raise InstallError(f"cannot revalidate {handle.label}: {exc}") from exc
    if (
        not stat.S_ISDIR(observed.st_mode)
        or observed.st_dev != handle.device
        or observed.st_ino != handle.inode
    ):
        raise InstallError(f"{handle.label} identity changed")


def _verify_absolute_directory_identity(
    path: Path, handle: _DirectoryHandle
) -> None:
    _verify_directory_handle(handle)
    try:
        observed = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise InstallError(
            f"cannot revalidate {handle.label} path: {exc}"
        ) from exc
    if (
        not stat.S_ISDIR(observed.st_mode)
        or observed.st_dev != handle.device
        or observed.st_ino != handle.inode
    ):
        raise InstallError(f"{handle.label} path identity changed")


def _verify_named_directory(
    parent: _DirectoryHandle,
    name: str,
    child: _DirectoryHandle,
) -> None:
    _verify_directory_handle(parent)
    _verify_directory_handle(child)
    try:
        observed = os.stat(
            name,
            dir_fd=parent.fd,
            follow_symlinks=False,
        )
    except OSError as exc:
        raise InstallError(
            f"cannot revalidate {child.label} directory entry: {exc}"
        ) from exc
    if (
        not stat.S_ISDIR(observed.st_mode)
        or observed.st_dev != child.device
        or observed.st_ino != child.inode
    ):
        raise InstallError(f"{child.label} directory entry changed")


def _duplicate_directory_handle(
    handle: _DirectoryHandle, label: str
) -> _DirectoryHandle:
    _verify_directory_handle(handle)
    try:
        duplicate = os.dup(handle.fd)
    except OSError as exc:
        raise InstallError(f"cannot retain {label}: {exc}") from exc
    copied = _directory_handle(duplicate, label)
    if copied.device != handle.device or copied.inode != handle.inode:
        copied.close()
        raise InstallError(f"{label} identity changed while retaining")
    return copied


def _read_fd_payload(fd: int, description: str) -> bytes:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except OSError as exc:
        raise InstallError(f"cannot read {description}: {exc}") from exc


def _stable_snapshot_fd(fd: int, description: str) -> _StableFileSnapshot:
    try:
        before = os.fstat(fd)
    except OSError as exc:
        raise InstallError(f"cannot inspect {description}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise InstallError(f"{description} is not a safe regular file")
    payload = _read_fd_payload(fd, description)
    try:
        after = os.fstat(fd)
    except OSError as exc:
        raise InstallError(f"cannot recheck {description}: {exc}") from exc
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        stat.S_IMODE(before.st_mode),
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        stat.S_IMODE(after.st_mode),
    )
    if identity_before != identity_after or len(payload) != after.st_size:
        raise InstallError(f"{description} changed while being read")
    return _StableFileSnapshot(
        payload=payload,
        mode=stat.S_IMODE(after.st_mode),
        device=after.st_dev,
        inode=after.st_ino,
        size=after.st_size,
    )


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
    except Exception:
        os.close(descriptor)
        raise


def _open_stable_absolute_file(
    path: Path, description: str
) -> tuple[_DirectoryHandle, str, int, _StableFileSnapshot]:
    absolute = _lexical_absolute(path, description)
    parent = _open_absolute_directory(absolute.parent, f"{description} parent")
    try:
        descriptor, snapshot = _open_stable_child_file(
            parent, absolute.name, description
        )
    except Exception:
        parent.close()
        raise
    return parent, absolute.name, descriptor, snapshot


def _verify_stable_named_file(
    parent: _DirectoryHandle,
    name: str,
    descriptor: int,
    expected: _StableFileSnapshot,
    description: str,
) -> None:
    current = _stable_snapshot_fd(descriptor, description)
    try:
        named = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    except OSError as exc:
        raise InstallError(f"cannot revalidate {description}: {exc}") from exc
    if (
        current != expected
        or not stat.S_ISREG(named.st_mode)
        or named.st_dev != expected.device
        or named.st_ino != expected.inode
        or named.st_size != expected.size
        or stat.S_IMODE(named.st_mode) != expected.mode
    ):
        raise InstallError(f"{description} changed during validation")


def _fsync_handle(handle: _DirectoryHandle, boundary: str | None = None) -> None:
    _verify_directory_handle(handle)
    try:
        os.fsync(handle.fd)
    except OSError as exc:
        raise InstallError(f"cannot durably sync {handle.label}: {exc}") from exc
    if boundary is not None:
        _deploy_preloader_checkpoint(boundary)


def _mkdir_open_child(
    parent: _DirectoryHandle,
    name: str,
    description: str,
    boundary_prefix: str,
    recovery: _CompatRecovery,
) -> _DirectoryHandle:
    temporary = f".ssr-oracle-dir-{secrets.token_hex(16)}"
    try:
        os.mkdir(temporary, 0o700, dir_fd=parent.fd)
    except OSError as exc:
        raise InstallError(f"cannot create {description}: {exc}") from exc
    child: _DirectoryHandle | None = None
    published = False
    try:
        child = _open_child_directory(parent, temporary, description)
        _renameatx(
            parent,
            temporary,
            parent,
            name,
            _RENAME_EXCL,
            f"publish {description} directory",
        )
        published = True
        _verify_named_directory(parent, name, child)
        _deploy_preloader_checkpoint(f"{boundary_prefix}_mkdir")
        _fsync_handle(child, f"{boundary_prefix}_child_fsync")
        _fsync_handle(parent, f"{boundary_prefix}_parent_fsync")
        return child
    except Exception as exc:
        errors = [str(exc)]
        if child is None:
            errors.append(
                f"{description} cleanup refused without retained identity"
            )
            raise InstallError("; ".join(errors)) from exc
        cleanup_name = name if published else temporary
        try:
            _preserve_owned_empty_directory_at(
                parent,
                cleanup_name,
                child,
                recovery,
                description,
            )
        except (InstallError, OSError) as cleanup_error:
            child.close()
            errors.append(f"{description} cleanup failed: {cleanup_error}")
        raise InstallError("; ".join(errors)) from exc


class _RetainedDirectoryCollision(InstallError):
    pass


def _mkdir_open_retained_child(
    parent: _DirectoryHandle,
    name: str,
    description: str,
    boundary_prefix: str,
) -> _DirectoryHandle:
    _require_safe_leaf(name, description)
    temporary = ""
    for _ in range(128):
        temporary = (
            f".ssr-oracle-recovery-dir-{secrets.token_hex(16)}"
        )
        try:
            os.mkdir(temporary, 0o700, dir_fd=parent.fd)
        except FileExistsError:
            continue
        except OSError as exc:
            raise InstallError(
                f"cannot create temporary {description}: {exc}"
            ) from exc
        break
    else:
        raise InstallError(
            f"cannot allocate an exclusive temporary {description}"
        )

    child: _DirectoryHandle | None = None
    published = False
    try:
        child = _open_child_directory(parent, temporary, description)
        _verify_named_directory(parent, temporary, child)
        _renameatx(
            parent,
            temporary,
            parent,
            name,
            _RENAME_EXCL,
            f"publish {description} directory",
        )
        published = True
        _verify_named_directory(parent, name, child)
        _deploy_preloader_checkpoint(f"{boundary_prefix}_mkdir")
        _fsync_handle(child, f"{boundary_prefix}_child_fsync")
        _fsync_handle(parent, f"{boundary_prefix}_parent_fsync")
        return child
    except _RenameAtError as exc:
        if child is not None:
            child.close()
        message = (
            f"{exc}; preserved all partial {description} scaffolding"
        )
        if not published and exc.error_number == errno.EEXIST:
            raise _RetainedDirectoryCollision(message) from exc
        raise InstallError(message) from exc
    except Exception as exc:
        if child is not None:
            child.close()
        raise InstallError(
            f"{exc}; preserved all partial {description} scaffolding"
        ) from exc


def _write_new_file_at(
    parent: _DirectoryHandle,
    name: str,
    payload: bytes,
    mode: int,
    boundary_prefix: str,
    created: list[_FileIdentity] | None = None,
) -> _StableFileSnapshot:
    descriptor = -1
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
            dir_fd=parent.fd,
        )
        opened = os.fstat(descriptor)
        if created is not None:
            created.append(_FileIdentity(opened.st_dev, opened.st_ino))
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short file write")
            view = view[written:]
        _deploy_preloader_checkpoint(f"{boundary_prefix}_write")
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
        _deploy_preloader_checkpoint(f"{boundary_prefix}_fsync")
        observed = os.fstat(descriptor)
        return _StableFileSnapshot(
            payload=payload,
            mode=stat.S_IMODE(observed.st_mode),
            device=observed.st_dev,
            inode=observed.st_ino,
            size=observed.st_size,
        )
    except OSError as exc:
        raise InstallError(f"cannot write staged {boundary_prefix}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _entry_kind_at(
    parent: _DirectoryHandle, name: str
) -> Literal["absent", "file", "directory", "symlink", "other"]:
    try:
        observed = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "other"
    if stat.S_ISREG(observed.st_mode):
        return "file"
    if stat.S_ISDIR(observed.st_mode):
        return "directory"
    if stat.S_ISLNK(observed.st_mode):
        return "symlink"
    return "other"


def _named_file_matches(
    parent: _DirectoryHandle,
    name: str,
    expected: _StableFileSnapshot,
) -> bool:
    try:
        observed = os.stat(
            name, dir_fd=parent.fd, follow_symlinks=False
        )
    except OSError:
        return False
    return (
        stat.S_ISREG(observed.st_mode)
        and observed.st_dev == expected.device
        and observed.st_ino == expected.inode
        and observed.st_size == expected.size
        and stat.S_IMODE(observed.st_mode) == expected.mode
    )


def _named_file_is_identity(
    parent: _DirectoryHandle,
    name: str,
    expected: _FileIdentity,
) -> bool:
    try:
        observed = os.stat(
            name, dir_fd=parent.fd, follow_symlinks=False
        )
    except OSError:
        return False
    return (
        stat.S_ISREG(observed.st_mode)
        and observed.st_dev == expected.device
        and observed.st_ino == expected.inode
    )


def _preserve_owned_file_at(
    parent: _DirectoryHandle,
    name: str,
    identity: _FileIdentity,
    recovery: _CompatRecovery,
    boundary_prefix: str,
) -> None:
    _preserve_owned_entry_at(
        parent,
        name,
        "file",
        identity,
        recovery,
        boundary_prefix,
    )


def _preserve_owned_empty_directory_at(
    parent: _DirectoryHandle,
    name: str,
    child: _DirectoryHandle,
    recovery: _CompatRecovery,
    description: str,
) -> None:
    _verify_named_directory(parent, name, child)
    if not _directory_is_empty(child):
        raise InstallError(f"{description} is not empty")
    identity = _FileIdentity(child.device, child.inode)
    try:
        _preserve_owned_entry_at(
            parent,
            name,
            "directory",
            identity,
            recovery,
            description,
        )
    finally:
        child.close()


def _deploy_preloader_checkpoint(boundary: str) -> None:
    del boundary


def _compat_recovery_name() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{secrets.token_hex(16)}"


def _updated_preloader_manifest(
    manifest: InstallManifest,
    provenance_payload: bytes,
    patched_payload: bytes,
) -> InstallManifest:
    by_path = {entry.relative_path: entry for entry in manifest.entries}
    by_path[PRELOADER_RELATIVE_PATH] = ManifestEntry(
        PRELOADER_RELATIVE_PATH,
        "file",
        sha256(patched_payload).hexdigest(),
    )
    by_path[_PRELOADER_BACKUP_ROOT] = ManifestEntry(
        _PRELOADER_BACKUP_ROOT, "directory", None
    )
    by_path[PRELOADER_BACKUP_RELATIVE_PATH] = ManifestEntry(
        PRELOADER_BACKUP_RELATIVE_PATH,
        "file",
        EXPECTED_OFFICIAL_PRELOADER_SHA256,
    )
    by_path[_PRELOADER_COMPAT_ROOT] = ManifestEntry(
        _PRELOADER_COMPAT_ROOT, "directory", None
    )
    by_path[PRELOADER_PROVENANCE_RELATIVE_PATH] = ManifestEntry(
        PRELOADER_PROVENANCE_RELATIVE_PATH,
        "file",
        sha256(provenance_payload).hexdigest(),
    )
    return InstallManifest(
        schema_version=manifest.schema_version,
        game_assembly_sha256=manifest.game_assembly_sha256,
        runtime_archive_sha256=manifest.runtime_archive_sha256,
        entries=tuple(
            sorted(by_path.values(), key=lambda entry: entry.relative_path)
        ),
    )


def _create_compat_staging(
    root: _DirectoryHandle,
    payloads: dict[str, tuple[bytes, int]],
    recovery: _CompatRecovery,
) -> _CompatStaging:
    name = f".ssr-oracle-compat-staging-{secrets.token_hex(16)}"
    staging_root = _mkdir_open_child(
        root,
        name,
        "compatibility staging root",
        "staging_root",
        recovery,
    )

    opened: list[
        tuple[_DirectoryHandle, _DirectoryHandle, str]
    ] = []
    assembled: _CompatStaging | None = None
    try:
        bep_in_ex = _mkdir_open_child(
            staging_root,
            "BepInEx",
            "staging BepInEx",
            "staging_bepinex",
            recovery,
        )
        opened.append((bep_in_ex, staging_root, "BepInEx"))
        backup = _mkdir_open_child(
            bep_in_ex,
            ".ssr-oracle-backup",
            "staging backup directory",
            "staging_backup_dir",
            recovery,
        )
        opened.append((backup, bep_in_ex, ".ssr-oracle-backup"))
        compat = _mkdir_open_child(
            bep_in_ex,
            ".ssr-oracle-compat",
            "staging provenance directory",
            "staging_compat_dir",
            recovery,
        )
        opened.append((compat, bep_in_ex, ".ssr-oracle-compat"))
        core = _mkdir_open_child(
            bep_in_ex,
            "core",
            "staging core directory",
            "staging_core_dir",
            recovery,
        )
        opened.append((core, bep_in_ex, "core"))
        file_locations = {
            PRELOADER_BACKUP_RELATIVE_PATH: (
                backup,
                "BepInEx.Preloader.dll",
            ),
            PRELOADER_PROVENANCE_RELATIVE_PATH: (
                compat,
                "preloader-provenance.json",
            ),
            PRELOADER_RELATIVE_PATH: (
                core,
                "BepInEx.Preloader.dll",
            ),
        }
        files: dict[
            str, tuple[_DirectoryHandle, str, _FileIdentity]
        ] = {}
        labels = {
            PRELOADER_BACKUP_RELATIVE_PATH: "stage_backup",
            PRELOADER_PROVENANCE_RELATIVE_PATH: "stage_provenance",
            PRELOADER_RELATIVE_PATH: "stage_active",
        }
        assembled = _CompatStaging(
            name=name,
            root=staging_root,
            bep_in_ex=bep_in_ex,
            backup=backup,
            compat=compat,
            core=core,
            files=files,
        )
        for relative_path, (parent, leaf) in file_locations.items():
            payload, mode = payloads[relative_path]
            created: list[_FileIdentity] = []
            try:
                _write_new_file_at(
                    parent,
                    leaf,
                    payload,
                    mode,
                    labels[relative_path],
                    created,
                )
            finally:
                if created:
                    files[relative_path] = (
                        parent,
                        leaf,
                        created[0],
                    )
            _fsync_handle(parent, f"{labels[relative_path]}_parent_fsync")
        return assembled
    except Exception as exc:
        errors = [str(exc)]
        if assembled is not None:
            try:
                _cleanup_compat_staging_fd(root, assembled, recovery)
            except InstallError as cleanup_error:
                errors.append(f"staging cleanup failed: {cleanup_error}")
            raise InstallError("; ".join(errors)) from exc
        for handle, _, _ in reversed(opened):
            handle.close()
        try:
            _preserve_owned_entry_at(
                root,
                name,
                "directory",
                _FileIdentity(staging_root.device, staging_root.inode),
                recovery,
                "staging_cleanup",
            )
        except (InstallError, OSError) as cleanup_error:
            errors.append(f"staging cleanup failed: {cleanup_error}")
        finally:
            staging_root.close()
        raise InstallError("; ".join(errors)) from exc


def _directory_is_empty(handle: _DirectoryHandle) -> bool:
    try:
        with os.scandir(handle.fd) as entries:
            return next(entries, None) is None
    except OSError as exc:
        raise InstallError(f"cannot inspect {handle.label}: {exc}") from exc


def _cleanup_compat_staging_fd(
    root: _DirectoryHandle,
    staging: _CompatStaging,
    recovery: _CompatRecovery,
) -> None:
    identity = _FileIdentity(staging.root.device, staging.root.inode)
    try:
        _preserve_owned_entry_at(
            root,
            staging.name,
            "directory",
            identity,
            recovery,
            "staging_cleanup",
        )
    finally:
        staging.core.close()
        staging.compat.close()
        staging.backup.close()
        staging.bep_in_ex.close()
        staging.root.close()


def _create_live_compat_directories(
    bep_in_ex: _DirectoryHandle,
    recovery: _CompatRecovery,
) -> tuple[_DirectoryHandle, _DirectoryHandle]:
    backup = _mkdir_open_child(
        bep_in_ex,
        ".ssr-oracle-backup",
        "live backup directory",
        "live_backup_dir",
        recovery,
    )
    try:
        compat = _mkdir_open_child(
            bep_in_ex,
            ".ssr-oracle-compat",
            "live provenance directory",
            "live_compat_dir",
            recovery,
        )
    except Exception as exc:
        errors = [str(exc)]
        try:
            _preserve_owned_empty_directory_at(
                bep_in_ex,
                ".ssr-oracle-backup",
                backup,
                recovery,
                "live backup directory",
            )
        except (InstallError, OSError) as cleanup_error:
            backup.close()
            errors.append(
                f"live backup directory cleanup failed: {cleanup_error}"
            )
        raise InstallError("; ".join(errors)) from exc
    return backup, compat


def _atomic_replace_at(
    parent: _DirectoryHandle,
    name: str,
    payload: bytes,
    mode: int,
    boundary_prefix: str,
    expected: _StableFileSnapshot,
    recovery: _CompatRecovery,
    published: list[_StableFileSnapshot] | None = None,
) -> _StableFileSnapshot:
    temporary = f".{name}.{secrets.token_hex(16)}.tmp"
    created: list[_FileIdentity] = []
    primary_error: InstallError | OSError | None = None
    replacement: _StableFileSnapshot | None = None
    cleanup_identity: _FileIdentity | None = None
    try:
        staged = _write_new_file_at(
            parent,
            temporary,
            payload,
            mode,
            f"{boundary_prefix}_temporary",
            created,
        )
        cleanup_identity = _FileIdentity(staged.device, staged.inode)
        _renameatx(
            parent,
            temporary,
            parent,
            name,
            _RENAME_SWAP,
            f"atomically swap {boundary_prefix}",
        )
        replacement = staged
        cleanup_identity = _FileIdentity(
            expected.device, expected.inode
        )
        if published is not None:
            published.append(staged)
        _deploy_preloader_checkpoint(
            f"{boundary_prefix}_post_rename_preopen"
        )
        displaced_fd = -1
        replacement_fd = -1
        try:
            displaced_fd, displaced = _open_stable_child_file(
                parent, temporary, f"displaced {boundary_prefix}"
            )
            replacement_fd, replacement = _open_stable_child_file(
                parent, name, f"published {boundary_prefix}"
            )
        finally:
            if replacement_fd >= 0:
                os.close(replacement_fd)
            if displaced_fd >= 0:
                os.close(displaced_fd)
        if displaced != expected or (
            replacement.device != staged.device
            or replacement.inode != staged.inode
            or replacement.payload != payload
            or replacement.mode != mode
        ):
            _renameatx(
                parent,
                temporary,
                parent,
                name,
                _RENAME_SWAP,
                f"restore raced {boundary_prefix}",
            )
            cleanup_identity = _FileIdentity(
                staged.device, staged.inode
            )
            _fsync_rename_parents(
                parent,
                parent,
                f"{boundary_prefix}_race_restore",
            )
            cleanup_identity = _FileIdentity(staged.device, staged.inode)
            raise InstallError(
                f"{boundary_prefix} target changed during atomic swap"
            )
        _deploy_preloader_checkpoint(f"{boundary_prefix}_replace")
        _fsync_handle(parent, f"{boundary_prefix}_parent_fsync")
    except (InstallError, OSError) as exc:
        primary_error = exc

    cleanup_errors: list[str] = []
    if cleanup_identity is None and created:
        cleanup_identity = created[0]
    temporary_kind = _entry_kind_at(parent, temporary)
    if (
        temporary_kind == "file"
        and cleanup_identity is not None
        and _named_file_is_identity(
            parent, temporary, cleanup_identity
        )
    ):
        try:
            _preserve_owned_file_at(
                parent,
                temporary,
                cleanup_identity,
                recovery,
                f"{boundary_prefix}_temporary_cleanup",
            )
        except (InstallError, OSError) as cleanup_error:
            cleanup_errors.append(
                f"temporary cleanup failed: {cleanup_error}"
            )
    elif temporary_kind != "absent":
        cleanup_errors.append(
            f"temporary cleanup refused changed identity or type: {temporary}"
        )

    if primary_error is not None:
        if isinstance(primary_error, InstallError):
            errors = [str(primary_error)]
        else:
            errors = [
                f"cannot atomically replace {boundary_prefix}: "
                f"{primary_error}"
            ]
        errors.extend(cleanup_errors)
        raise InstallError("; ".join(errors)) from primary_error
    if cleanup_errors:
        raise InstallError("; ".join(cleanup_errors))
    if replacement is None:
        raise InstallError(f"{boundary_prefix} replacement was not published")
    return replacement


def _entry_is_owned(
    parent: _DirectoryHandle,
    name: str,
    expected_kind: Literal["file", "directory"],
    identity: _FileIdentity,
) -> bool:
    try:
        observed = os.stat(
            name, dir_fd=parent.fd, follow_symlinks=False
        )
    except OSError:
        return False
    return (
        (
            expected_kind == "file"
            and stat.S_ISREG(observed.st_mode)
        )
        or (
            expected_kind == "directory"
            and stat.S_ISDIR(observed.st_mode)
        )
    ) and (
        observed.st_dev == identity.device
        and observed.st_ino == identity.inode
    )


def _find_owned_cleanup_entry(
    recovery: _CompatRecovery,
    expected_kind: Literal["file", "directory"],
    identity: _FileIdentity,
) -> str | None:
    try:
        with os.scandir(recovery.cleanup.fd) as entries:
            for entry in entries:
                try:
                    observed = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                kind_matches = (
                    stat.S_ISREG(observed.st_mode)
                    if expected_kind == "file"
                    else stat.S_ISDIR(observed.st_mode)
                )
                if kind_matches and (
                    observed.st_dev,
                    observed.st_ino,
                ) == (identity.device, identity.inode):
                    return entry.name
    except OSError as exc:
        raise InstallError(
            f"cannot inspect recovery cleanup after preservation race: {exc}"
        ) from exc
    return None


def _preserve_owned_entry_at(
    source_parent: _DirectoryHandle,
    source_name: str,
    expected_kind: Literal["file", "directory"],
    identity: _FileIdentity,
    recovery: _CompatRecovery,
    boundary_prefix: str,
) -> str:
    _require_safe_leaf(source_name, boundary_prefix)
    if not _entry_is_owned(
        source_parent, source_name, expected_kind, identity
    ):
        raise InstallError(
            f"{boundary_prefix} {expected_kind} changed before preservation"
        )

    for _ in range(128):
        destination_name = (
            f"{expected_kind}-{secrets.token_hex(16)}"
        )
        try:
            _renameatx(
                source_parent,
                source_name,
                recovery.cleanup,
                destination_name,
                _RENAME_EXCL,
                f"preserve {boundary_prefix} {expected_kind}",
            )
        except _RenameAtError as exc:
            if exc.error_number == errno.EEXIST:
                if not _entry_is_owned(
                    source_parent,
                    source_name,
                    expected_kind,
                    identity,
                ):
                    raise InstallError(
                        f"{boundary_prefix} {expected_kind} changed while "
                        "retrying a cleanup-leaf collision"
                    ) from exc
                continue
            raise

        sync_error: InstallError | None = None
        try:
            _fsync_rename_parents(
                source_parent,
                recovery.cleanup,
                f"{boundary_prefix}_preserve",
            )
        except InstallError as exc:
            sync_error = exc
        if not _entry_is_owned(
            recovery.cleanup,
            destination_name,
            expected_kind,
            identity,
        ):
            restore_error: InstallError | None = None
            try:
                _renameatx(
                    recovery.cleanup,
                    destination_name,
                    source_parent,
                    source_name,
                    _RENAME_EXCL,
                    f"restore raced {boundary_prefix} {expected_kind}",
                )
                _fsync_rename_parents(
                    recovery.cleanup,
                    source_parent,
                    f"{boundary_prefix}_race_restore",
                )
            except InstallError as exc:
                restore_error = exc
            recovered_name = _find_owned_cleanup_entry(
                recovery,
                expected_kind,
                identity,
            )
            if recovered_name is not None and restore_error is None:
                if sync_error is not None:
                    raise InstallError(
                        f"{boundary_prefix} {expected_kind} was preserved "
                        f"but recovery sync failed: {sync_error}"
                    ) from sync_error
                return recovered_name
            message = (
                f"{boundary_prefix} {expected_kind} changed during "
                "preservation"
            )
            if restore_error is not None:
                message += f"; restore failed: {restore_error}"
            if recovered_name is not None:
                message += "; owned entry retained in recovery cleanup"
            if sync_error is not None:
                message += f"; recovery sync failed: {sync_error}"
            raise InstallError(message)
        if sync_error is not None:
            raise InstallError(
                f"{boundary_prefix} {expected_kind} was preserved but "
                f"recovery sync failed: {sync_error}"
            ) from sync_error
        return destination_name
    raise InstallError(
        f"cannot allocate an exclusive cleanup leaf for {boundary_prefix}"
    )


def _allocate_compat_recovery_fd(
    root: _DirectoryHandle,
    retained_parent: _DirectoryHandle | None = None,
) -> _CompatRecovery:
    parent_created = False
    parent: _DirectoryHandle | None = None
    run: _DirectoryHandle | None = None
    run_name = ""
    opened: list[_DirectoryHandle] = []
    try:
        if retained_parent is not None:
            _verify_named_directory(
                root, ".ssr-oracle-recovery", retained_parent
            )
            parent = _duplicate_directory_handle(
                retained_parent, "recovery parent"
            )
        elif _entry_kind_at(root, ".ssr-oracle-recovery") == "absent":
            parent = _mkdir_open_retained_child(
                root,
                ".ssr-oracle-recovery",
                "recovery parent",
                "recovery_parent",
            )
            parent_created = True
        else:
            raise InstallError("recovery parent changed after preflight")

        for _ in range(128):
            run_name = _compat_recovery_name()
            try:
                run = _mkdir_open_retained_child(
                    parent,
                    run_name,
                    "compatibility recovery run",
                    "recovery_run",
                )
            except _RetainedDirectoryCollision:
                continue
            break
        if run is None:
            raise InstallError(
                "cannot allocate an exclusive compatibility recovery"
            )
        compat = _mkdir_open_retained_child(
            run, "compat", "compatibility recovery", "recovery_compat"
        )
        opened.append(compat)
        bep_in_ex = _mkdir_open_retained_child(
            compat, "BepInEx", "recovery BepInEx", "recovery_bepinex"
        )
        opened.append(bep_in_ex)
        backup = _mkdir_open_retained_child(
            bep_in_ex,
            ".ssr-oracle-backup",
            "recovery backup directory",
            "recovery_backup_dir",
        )
        opened.append(backup)
        provenance = _mkdir_open_retained_child(
            bep_in_ex,
            ".ssr-oracle-compat",
            "recovery provenance directory",
            "recovery_provenance_dir",
        )
        opened.append(provenance)
        cleanup = _mkdir_open_retained_child(
            run,
            "cleanup",
            "recovery cleanup directory",
            "recovery_cleanup_dir",
        )
        opened.append(cleanup)
        return _CompatRecovery(
            parent=parent,
            parent_created=parent_created,
            run_name=run_name,
            run=run,
            compat=compat,
            bep_in_ex=bep_in_ex,
            backup=backup,
            provenance=provenance,
            cleanup=cleanup,
        )
    except Exception as exc:
        for handle in reversed(opened):
            handle.close()
        if run is not None:
            run.close()
        if parent is not None:
            parent.close()
        raise InstallError(
            f"{exc}; preserved any partial compatibility recovery scaffolding"
        ) from exc


def _close_recovery(recovery: _CompatRecovery) -> None:
    recovery.cleanup.close()
    recovery.provenance.close()
    recovery.backup.close()
    recovery.bep_in_ex.close()
    recovery.compat.close()
    recovery.run.close()
    recovery.parent.close()


def _preserve_compat_recovery_fd(
    backup: _DirectoryHandle,
    compat: _DirectoryHandle,
    possibly_published: Sequence[str],
    published_artifacts: dict[str, _StableFileSnapshot],
    recovery: _CompatRecovery,
) -> None:
    sources = {
        PRELOADER_BACKUP_RELATIVE_PATH: (
            backup,
            "BepInEx.Preloader.dll",
            "backup",
        ),
        PRELOADER_PROVENANCE_RELATIVE_PATH: (
            compat,
            "preloader-provenance.json",
            "provenance",
        ),
    }
    recoverable = tuple(
        relative_path
        for relative_path in possibly_published
        if relative_path in sources
        and relative_path in published_artifacts
        and _entry_kind_at(sources[relative_path][0], sources[relative_path][1])
        == "file"
        and _named_file_matches(
            sources[relative_path][0],
            sources[relative_path][1],
            published_artifacts[relative_path],
        )
    )
    if not recoverable:
        return
    errors: list[str] = []
    destinations = {
        PRELOADER_BACKUP_RELATIVE_PATH: (
            recovery.backup,
            "BepInEx.Preloader.dll",
        ),
        PRELOADER_PROVENANCE_RELATIVE_PATH: (
            recovery.provenance,
            "preloader-provenance.json",
        ),
    }
    for relative_path in recoverable:
        source_parent, source_name, label = sources[relative_path]
        destination_parent, destination_name = destinations[relative_path]
        if _entry_kind_at(destination_parent, destination_name) != "absent":
            errors.append(
                f"recovery destination already exists for {label}"
            )
            continue
        moved = False
        try:
            _renameatx(
                source_parent,
                source_name,
                destination_parent,
                destination_name,
                _RENAME_EXCL,
                f"preserve compatibility {label}",
            )
            moved = True
            _deploy_preloader_checkpoint(
                f"recovery_{label}_post_rename_preopen"
            )
            recovered_fd, recovered = _open_stable_child_file(
                destination_parent,
                destination_name,
                f"recovered compatibility {label}",
            )
            os.close(recovered_fd)
            if recovered != published_artifacts[relative_path]:
                _renameatx(
                    destination_parent,
                    destination_name,
                    source_parent,
                    source_name,
                    _RENAME_EXCL,
                    f"restore raced compatibility {label}",
                )
                _fsync_rename_parents(
                    destination_parent,
                    source_parent,
                    f"recovery_{label}_race_restore",
                )
                moved = False
                raise InstallError(
                    f"compatibility {label} changed during recovery move"
                )
            _deploy_preloader_checkpoint(f"recovery_{label}_move")
            _fsync_handle(
                source_parent, f"recovery_{label}_source_fsync"
            )
            _fsync_handle(
                destination_parent,
                f"recovery_{label}_destination_fsync",
            )
        except (InstallError, OSError) as exc:
            sync_errors: list[str] = []
            if moved:
                for handle in (source_parent, destination_parent):
                    try:
                        _fsync_handle(handle)
                    except InstallError as sync_error:
                        sync_errors.append(str(sync_error))
            errors.append(
                f"cannot preserve compatibility {label}: {exc}"
                + (
                    "; recovery sync failed: "
                    + "; ".join(sync_errors)
                    if sync_errors
                    else ""
                )
            )
    if errors:
        raise InstallError("; ".join(errors))


def _snapshot_child_if_safe(
    parent: _DirectoryHandle,
    name: str,
    description: str,
) -> _StableFileSnapshot | None:
    kind = _entry_kind_at(parent, name)
    if kind == "absent":
        return None
    if kind != "file":
        raise InstallError(f"{description} changed type")
    descriptor, snapshot = _open_stable_child_file(parent, name, description)
    os.close(descriptor)
    return snapshot


def _rollback_preloader_deploy_fd(
    *,
    root: _DirectoryHandle,
    bep_in_ex: _DirectoryHandle,
    core: _DirectoryHandle,
    active_snapshot: _StableFileSnapshot,
    manifest_snapshot: _StableFileSnapshot,
    published_active: _StableFileSnapshot | None,
    published_manifest: _StableFileSnapshot | None,
    backup: _DirectoryHandle | None,
    compat: _DirectoryHandle | None,
    possibly_published: Sequence[str],
    published_artifacts: dict[str, _StableFileSnapshot],
    recovery: _CompatRecovery,
) -> None:
    errors: list[str] = []
    try:
        current_active = _snapshot_child_if_safe(
            core, "BepInEx.Preloader.dll", "active preloader"
        )
        if current_active != active_snapshot:
            if current_active != published_active:
                raise InstallError(
                    "active preloader changed after publication"
                )
            _atomic_replace_at(
                core,
                "BepInEx.Preloader.dll",
                active_snapshot.payload,
                active_snapshot.mode,
                "rollback_active",
                current_active,
                recovery,
            )
    except InstallError as exc:
        errors.append(f"active restore failed: {exc}")
    try:
        current_manifest = _snapshot_child_if_safe(
            root, MANIFEST_NAME, "install manifest"
        )
        if current_manifest != manifest_snapshot:
            if current_manifest != published_manifest:
                raise InstallError(
                    "install manifest changed after publication"
                )
            _atomic_replace_at(
                root,
                MANIFEST_NAME,
                manifest_snapshot.payload,
                manifest_snapshot.mode,
                "rollback_manifest",
                current_manifest,
                recovery,
            )
    except InstallError as exc:
        errors.append(f"manifest restore failed: {exc}")
    if backup is not None and compat is not None:
        try:
            _preserve_compat_recovery_fd(
                backup,
                compat,
                possibly_published,
                published_artifacts,
                recovery,
            )
        except InstallError as exc:
            errors.append(f"compatibility recovery failed: {exc}")
    for handle, name in (
        (compat, ".ssr-oracle-compat"),
        (backup, ".ssr-oracle-backup"),
    ):
        if handle is None:
            continue
        try:
            _preserve_owned_empty_directory_at(
                bep_in_ex,
                name,
                handle,
                recovery,
                f"created live directory {name}",
            )
        except (InstallError, OSError) as exc:
            errors.append(f"cannot remove created live directory {name}: {exc}")
    if errors:
        raise InstallError("rollback failed: " + "; ".join(errors))


def _directory_entries_fd(
    handle: _DirectoryHandle,
) -> dict[str, Literal["file", "directory", "symlink", "other"]]:
    observed: dict[str, Literal["file", "directory", "symlink", "other"]] = {}
    try:
        with os.scandir(handle.fd) as entries:
            for entry in entries:
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISREG(mode):
                    kind = "file"
                elif stat.S_ISDIR(mode):
                    kind = "directory"
                elif stat.S_ISLNK(mode):
                    kind = "symlink"
                else:
                    kind = "other"
                observed[entry.name] = kind
    except OSError as exc:
        raise InstallError(f"cannot inspect {handle.label}: {exc}") from exc
    return observed


def _stable_idempotent_manifest(
    *,
    root: _DirectoryHandle,
    bep_in_ex: _DirectoryHandle,
    core: _DirectoryHandle,
    requested_preloader: _StableFileSnapshot,
    requested_provenance: _StableFileSnapshot,
    preloader_parent: _DirectoryHandle,
    preloader_name: str,
    preloader_fd: int,
    provenance_parent: _DirectoryHandle,
    provenance_name: str,
    provenance_fd: int,
    trust: object,
    repository: Path,
    game_path: Path,
) -> InstallManifest:
    backup = _open_child_directory(
        bep_in_ex,
        ".ssr-oracle-backup",
        "live backup directory",
    )
    compat = _open_child_directory(
        bep_in_ex,
        ".ssr-oracle-compat",
        "live provenance directory",
    )
    descriptors: list[int] = []
    try:
        if _directory_entries_fd(backup) != {
            "BepInEx.Preloader.dll": "file"
        } or _directory_entries_fd(compat) != {
            "preloader-provenance.json": "file"
        }:
            raise InstallError("patched compatibility tree is not exact")
        active_fd, active = _open_stable_child_file(
            core, "BepInEx.Preloader.dll", "active preloader"
        )
        descriptors.append(active_fd)
        backup_fd, backup_snapshot = _open_stable_child_file(
            backup, "BepInEx.Preloader.dll", "official preloader backup"
        )
        descriptors.append(backup_fd)
        deployed_provenance_fd, deployed_provenance = _open_stable_child_file(
            compat,
            "preloader-provenance.json",
            "deployed provenance",
        )
        descriptors.append(deployed_provenance_fd)
        manifest_fd, manifest_snapshot = _open_stable_child_file(
            root, MANIFEST_NAME, "install manifest"
        )
        descriptors.append(manifest_fd)
        if (
            active.payload != requested_preloader.payload
            or deployed_provenance.payload != requested_provenance.payload
            or backup_snapshot.payload == requested_preloader.payload
        ):
            raise InstallError(
                "different patched build is already installed; restore first"
            )
        try:
            os.lseek(deployed_provenance_fd, 0, os.SEEK_SET)
            deployed = load_provenance(
                Path(f"/dev/fd/{deployed_provenance_fd}"), trust
            )
        except (CompatError, OSError) as exc:
            raise InstallError(
                f"deployed provenance is invalid: {exc}"
            ) from exc
        if (
            deployed.patched_preloader_sha256
            != sha256(active.payload).hexdigest()
            or deployed.official_preloader_sha256
            != sha256(backup_snapshot.payload).hexdigest()
        ):
            raise InstallError("patched compatibility hashes are inconsistent")
        _verify_absolute_directory_identity(game_path, root)
        manifest = _load_manifest(game_path)
        status = status_install(game_path, repo_root=repository)
        if (
            not status.healthy
            or status.preloader_compatibility.state != "patched"
            or status.manifest != manifest
        ):
            raise InstallError("installed patched preloader is not healthy")
        _deploy_preloader_checkpoint("idempotent_revalidate")
        _verify_named_directory(root, "BepInEx", bep_in_ex)
        _verify_named_directory(bep_in_ex, "core", core)
        _verify_named_directory(
            bep_in_ex, ".ssr-oracle-backup", backup
        )
        _verify_named_directory(
            bep_in_ex, ".ssr-oracle-compat", compat
        )
        _verify_stable_named_file(
            preloader_parent,
            preloader_name,
            preloader_fd,
            requested_preloader,
            "supplied preloader",
        )
        _verify_stable_named_file(
            provenance_parent,
            provenance_name,
            provenance_fd,
            requested_provenance,
            "supplied provenance",
        )
        _verify_stable_named_file(
            core,
            "BepInEx.Preloader.dll",
            active_fd,
            active,
            "active preloader",
        )
        _verify_stable_named_file(
            backup,
            "BepInEx.Preloader.dll",
            backup_fd,
            backup_snapshot,
            "official preloader backup",
        )
        _verify_stable_named_file(
            compat,
            "preloader-provenance.json",
            deployed_provenance_fd,
            deployed_provenance,
            "deployed provenance",
        )
        _verify_stable_named_file(
            root,
            MANIFEST_NAME,
            manifest_fd,
            manifest_snapshot,
            "install manifest",
        )
        if _directory_entries_fd(backup) != {
            "BepInEx.Preloader.dll": "file"
        } or _directory_entries_fd(compat) != {
            "preloader-provenance.json": "file"
        }:
            raise InstallError(
                "patched compatibility tree changed during validation"
            )
        _verify_absolute_directory_identity(game_path, root)
        return manifest
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        compat.close()
        backup.close()


def deploy_preloader(
    game_root: Path,
    preloader: Path,
    provenance: Path,
    repo_root: Path | None = None,
) -> InstallManifest:
    """Transactionally deploy through pinned, no-follow directory descriptors."""
    try:
        if repo_root is not None and Path(repo_root).is_symlink():
            raise InstallError(
                "repository root is not a safe directory"
            )
        repository = (
            Path(repo_root).resolve()
            if repo_root is not None
            else Path(__file__).resolve().parents[2]
        )
    except InstallError:
        raise
    except (OSError, RuntimeError) as exc:
        raise InstallError(f"cannot resolve repository root: {exc}") from exc

    root: _DirectoryHandle | None = None
    bep_in_ex: _DirectoryHandle | None = None
    core: _DirectoryHandle | None = None
    request_parents: list[_DirectoryHandle] = []
    request_descriptors: list[int] = []
    staging: _CompatStaging | None = None
    backup: _DirectoryHandle | None = None
    compat: _DirectoryHandle | None = None
    recovery_parent: _DirectoryHandle | None = None
    recovery: _CompatRecovery | None = None
    active_snapshot: _StableFileSnapshot | None = None
    manifest_snapshot: _StableFileSnapshot | None = None
    published_active: list[_StableFileSnapshot] = []
    published_manifest: list[_StableFileSnapshot] = []
    published_artifacts: dict[str, _StableFileSnapshot] = {}
    possibly_published: list[str] = []
    try:
        game_path = _lexical_absolute(Path(game_root), "game root")
        root = _open_absolute_directory(game_path, "game root")
        game, manifest = _inspected_manifest(game_path)
        _verify_absolute_directory_identity(game_path, root)
        if manifest.runtime_archive_sha256 != EXPECTED_RUNTIME_ARCHIVE_SHA256:
            raise InstallError(
                "manifest runtime archive hash is not the pinned archive"
            )
        bep_in_ex = _open_child_directory(root, "BepInEx", "live BepInEx")
        core = _open_child_directory(bep_in_ex, "core", "live BepInEx/core")
        _verify_named_directory(root, "BepInEx", bep_in_ex)
        _verify_named_directory(bep_in_ex, "core", core)

        (
            preloader_parent,
            preloader_name,
            preloader_fd,
            requested_preloader,
        ) = _open_stable_absolute_file(
            Path(preloader), "supplied preloader"
        )
        request_parents.append(preloader_parent)
        request_descriptors.append(preloader_fd)
        (
            provenance_parent,
            provenance_name,
            provenance_fd,
            requested_provenance,
        ) = _open_stable_absolute_file(
            Path(provenance), "supplied provenance"
        )
        request_parents.append(provenance_parent)
        request_descriptors.append(provenance_fd)
        try:
            trust = load_trust(repository)
            os.lseek(provenance_fd, 0, os.SEEK_SET)
            provenance_data = load_provenance(
                Path(f"/dev/fd/{provenance_fd}"), trust
            )
        except (CompatError, OSError) as exc:
            raise InstallError(
                f"supplied provenance is invalid: {exc}"
            ) from exc
        _verify_stable_named_file(
            provenance_parent,
            provenance_name,
            provenance_fd,
            requested_provenance,
            "supplied provenance",
        )
        requested_hash = sha256(requested_preloader.payload).hexdigest()

        status = status_install(game_path, repo_root=repository)
        _verify_absolute_directory_identity(game_path, root)
        if status.preloader_compatibility.state == "patched":
            if requested_hash != provenance_data.patched_preloader_sha256:
                raise InstallError(
                    "different patched build is already installed; restore first"
                )
            _verify_stable_named_file(
                preloader_parent,
                preloader_name,
                preloader_fd,
                requested_preloader,
                "supplied preloader",
            )
            return _stable_idempotent_manifest(
                root=root,
                bep_in_ex=bep_in_ex,
                core=core,
                requested_preloader=requested_preloader,
                requested_provenance=requested_provenance,
                preloader_parent=preloader_parent,
                preloader_name=preloader_name,
                preloader_fd=preloader_fd,
                provenance_parent=provenance_parent,
                provenance_name=provenance_name,
                provenance_fd=provenance_fd,
                trust=trust,
                repository=repository,
                game_path=game_path,
            )
        if (
            status.preloader_compatibility.state != "official"
            or not status.healthy
        ):
            raise InstallError(
                "deploy-preloader requires a healthy official install"
            )
        if (
            requested_hash != provenance_data.patched_preloader_sha256
            or requested_hash != EXPECTED_PATCHED_PRELOADER_SHA256
        ):
            raise InstallError(
                "supplied preloader is not the reviewed patched artifact"
            )
        if (
            provenance_data.official_preloader_sha256
            != EXPECTED_OFFICIAL_PRELOADER_SHA256
        ):
            raise InstallError(
                "provenance official preloader hash is not pinned"
            )

        active_fd, active_snapshot = _open_stable_child_file(
            core, "BepInEx.Preloader.dll", "active preloader"
        )
        request_descriptors.append(active_fd)
        manifest_fd, manifest_snapshot = _open_stable_child_file(
            root, MANIFEST_NAME, "install manifest"
        )
        request_descriptors.append(manifest_fd)
        if (
            sha256(active_snapshot.payload).hexdigest()
            != EXPECTED_OFFICIAL_PRELOADER_SHA256
        ):
            raise InstallError(
                "active preloader is not the pinned official build"
            )
        active_entry = _manifest_entry(manifest, PRELOADER_RELATIVE_PATH)
        if (
            active_entry is None
            or active_entry.kind != "file"
            or active_entry.sha256 != EXPECTED_OFFICIAL_PRELOADER_SHA256
        ):
            raise InstallError(
                "active preloader does not match its official manifest entry"
            )
        if _entry_kind_at(bep_in_ex, ".ssr-oracle-backup") != "absent":
            raise InstallError("unmanaged compatibility backup target exists")
        if _entry_kind_at(bep_in_ex, ".ssr-oracle-compat") != "absent":
            raise InstallError("unmanaged compatibility provenance target exists")
        recovery_kind = _entry_kind_at(root, ".ssr-oracle-recovery")
        if recovery_kind not in {"absent", "directory"}:
            raise InstallError("recovery parent is not a safe directory")
        if recovery_kind == "directory":
            recovery_parent = _open_child_directory(
                root, ".ssr-oracle-recovery", "recovery parent"
            )
            _verify_named_directory(
                root, ".ssr-oracle-recovery", recovery_parent
            )

        _verify_stable_named_file(
            preloader_parent,
            preloader_name,
            preloader_fd,
            requested_preloader,
            "supplied preloader",
        )
        _verify_stable_named_file(
            provenance_parent,
            provenance_name,
            provenance_fd,
            requested_provenance,
            "supplied provenance",
        )
        _verify_stable_named_file(
            core,
            "BepInEx.Preloader.dll",
            active_fd,
            active_snapshot,
            "active preloader",
        )
        _verify_stable_named_file(
            root,
            MANIFEST_NAME,
            manifest_fd,
            manifest_snapshot,
            "install manifest",
        )
        _verify_absolute_directory_identity(game_path, root)
        if _load_manifest(game_path) != manifest:
            raise InstallError("install manifest changed during preflight")

        payloads = {
            PRELOADER_BACKUP_RELATIVE_PATH: (
                active_snapshot.payload,
                active_snapshot.mode,
            ),
            PRELOADER_PROVENANCE_RELATIVE_PATH: (
                requested_provenance.payload,
                0o644,
            ),
            PRELOADER_RELATIVE_PATH: (
                requested_preloader.payload,
                active_snapshot.mode,
            ),
        }
        updated = _updated_preloader_manifest(
            manifest,
            requested_provenance.payload,
            requested_preloader.payload,
        )
        recovery = _allocate_compat_recovery_fd(root, recovery_parent)
        staging = _create_compat_staging(root, payloads, recovery)
        backup, compat = _create_live_compat_directories(
            bep_in_ex, recovery
        )
        destinations = {
            PRELOADER_BACKUP_RELATIVE_PATH: (
                backup,
                "BepInEx.Preloader.dll",
                "backup",
            ),
            PRELOADER_PROVENANCE_RELATIVE_PATH: (
                compat,
                "preloader-provenance.json",
                "provenance",
            ),
            PRELOADER_RELATIVE_PATH: (
                core,
                "BepInEx.Preloader.dll",
                "active",
            ),
        }
        for relative_path in (
            PRELOADER_BACKUP_RELATIVE_PATH,
            PRELOADER_PROVENANCE_RELATIVE_PATH,
            PRELOADER_RELATIVE_PATH,
        ):
            source_parent, source_name, source_identity = staging.files[
                relative_path
            ]
            target_parent, target_name, label = destinations[relative_path]
            expected_kind = (
                "file"
                if relative_path == PRELOADER_RELATIVE_PATH
                else "absent"
            )
            if _entry_kind_at(target_parent, target_name) != expected_kind:
                raise InstallError(
                    f"compatibility publication target changed type: {label}"
                )
            source_fd, staged_source = _open_stable_child_file(
                source_parent,
                source_name,
                f"staged {label} artifact",
            )
            os.close(source_fd)
            if (
                staged_source.device != source_identity.device
                or staged_source.inode != source_identity.inode
            ):
                raise InstallError(
                    f"staged {label} artifact changed before publication"
                )
            if relative_path == PRELOADER_RELATIVE_PATH:
                _renameatx(
                    source_parent,
                    source_name,
                    target_parent,
                    target_name,
                    _RENAME_SWAP,
                    "publish compatibility artifact active",
                )
                possibly_published.append(relative_path)
                staging.files[relative_path] = (
                    source_parent,
                    source_name,
                    _FileIdentity(
                        active_snapshot.device,
                        active_snapshot.inode,
                    ),
                )
                published_active.append(staged_source)
                _deploy_preloader_checkpoint(
                    "active_post_rename_preopen"
                )
                displaced_fd = -1
                published_fd = -1
                try:
                    displaced_fd, displaced = _open_stable_child_file(
                        source_parent,
                        source_name,
                        "displaced official preloader",
                    )
                    published_fd, published = _open_stable_child_file(
                        target_parent,
                        target_name,
                        "published active preloader",
                    )
                finally:
                    if published_fd >= 0:
                        os.close(published_fd)
                    if displaced_fd >= 0:
                        os.close(displaced_fd)
                if displaced != active_snapshot or published != staged_source:
                    _renameatx(
                        source_parent,
                        source_name,
                        target_parent,
                        target_name,
                        _RENAME_SWAP,
                        "restore raced active publication",
                    )
                    staging.files[relative_path] = (
                        source_parent,
                        source_name,
                        source_identity,
                    )
                    _fsync_rename_parents(
                        source_parent,
                        target_parent,
                        "active_race_restore",
                    )
                    raise InstallError(
                        "active publication target changed during atomic swap"
                    )
            else:
                _renameatx(
                    source_parent,
                    source_name,
                    target_parent,
                    target_name,
                    _RENAME_EXCL,
                    f"publish compatibility artifact {label}",
                )
                possibly_published.append(relative_path)
                published_artifacts[relative_path] = staged_source
                _deploy_preloader_checkpoint(
                    f"{label}_post_rename_preopen"
                )
                published_fd, published = _open_stable_child_file(
                    target_parent,
                    target_name,
                    f"published {label} artifact",
                )
                os.close(published_fd)
                if published != staged_source:
                    _renameatx(
                        target_parent,
                        target_name,
                        source_parent,
                        source_name,
                        _RENAME_EXCL,
                        f"restore raced {label} publication",
                    )
                    _fsync_rename_parents(
                        target_parent,
                        source_parent,
                        f"{label}_race_restore",
                    )
                    raise InstallError(
                        f"{label} source changed during atomic publication"
                    )
            _deploy_preloader_checkpoint(f"{label}_replace")
            _deploy_preloader_checkpoint(label)
            _fsync_handle(
                source_parent, f"{label}_staging_parent_fsync"
            )
            _fsync_handle(
                target_parent, f"{label}_live_parent_fsync"
            )

        manifest_payload = (
            json.dumps(_manifest_to_dict(updated), sort_keys=True, indent=2)
            + "\n"
        ).encode()
        _atomic_replace_at(
            root,
            MANIFEST_NAME,
            manifest_payload,
            manifest_snapshot.mode,
            "manifest",
            manifest_snapshot,
            recovery,
            published_manifest,
        )
        _deploy_preloader_checkpoint("manifest")
        final_manifest = _stable_idempotent_manifest(
            root=root,
            bep_in_ex=bep_in_ex,
            core=core,
            requested_preloader=requested_preloader,
            requested_provenance=requested_provenance,
            preloader_parent=preloader_parent,
            preloader_name=preloader_name,
            preloader_fd=preloader_fd,
            provenance_parent=provenance_parent,
            provenance_name=provenance_name,
            provenance_fd=provenance_fd,
            trust=trust,
            repository=repository,
            game_path=game_path,
        )
        if final_manifest != updated:
            raise InstallError(
                "deployed preloader failed final manifest verification"
            )
        _cleanup_compat_staging_fd(root, staging, recovery)
        staging = None
        compat.close()
        backup.close()
        return updated
    except Exception as exc:
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
                    published_active=(
                        published_active[0] if published_active else None
                    ),
                    published_manifest=(
                        published_manifest[0] if published_manifest else None
                    ),
                    backup=backup,
                    compat=compat,
                    possibly_published=possibly_published,
                    published_artifacts=published_artifacts,
                    recovery=recovery,
                )
            except InstallError as rollback_error:
                details.append(str(rollback_error))
        if root is not None and staging is not None:
            try:
                _cleanup_compat_staging_fd(root, staging, recovery)
                staging = None
            except InstallError as cleanup_error:
                details.append(f"staging cleanup failed: {cleanup_error}")
        if details:
            raise InstallError(
                f"deploy-preloader failed ({exc}); " + "; ".join(details)
            ) from exc
        if isinstance(exc, InstallError):
            raise
        if isinstance(exc, (OSError, RuntimeError)):
            raise InstallError(f"deploy-preloader failed: {exc}") from exc
        raise
    finally:
        for descriptor in reversed(request_descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass
        for parent in reversed(request_parents):
            parent.close()
        if compat is not None:
            compat.close()
        if backup is not None:
            backup.close()
        if core is not None:
            core.close()
        if recovery is not None:
            _close_recovery(recovery)
        if recovery_parent is not None:
            recovery_parent.close()
        if bep_in_ex is not None:
            bep_in_ex.close()
        if root is not None:
            root.close()


def _lstat_kind(
    path: Path,
) -> Literal["absent", "file", "directory", "symlink", "other"]:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "other"
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    return "other"


@dataclass(frozen=True, slots=True)
class _PathEvidence:
    state: Literal["file", "missing", "unsafe"]
    sha256: str | None


def _regular_file_evidence(
    root: Path, relative_path: str
) -> _PathEvidence:
    current = root
    parts = PurePosixPath(relative_path).parts
    for part in parts[:-1]:
        current /= part
        parent_kind = _lstat_kind(current)
        if parent_kind == "absent":
            return _PathEvidence("missing", None)
        if parent_kind != "directory":
            return _PathEvidence("unsafe", None)
    target = current / parts[-1]
    target_kind = _lstat_kind(target)
    if target_kind == "absent":
        return _PathEvidence("missing", None)
    if target_kind != "file":
        return _PathEvidence("unsafe", None)
    try:
        return _PathEvidence("file", _sha256_file(target))
    except InstallError:
        return _PathEvidence("unsafe", None)


def _manifest_entry(
    manifest: InstallManifest, relative_path: str
) -> ManifestEntry | None:
    return next(
        (
            entry
            for entry in manifest.entries
            if entry.relative_path == relative_path
        ),
        None,
    )


def _compatibility_ownership_is_exact(manifest: InstallManifest) -> bool:
    expected_kinds = {
        _PRELOADER_BACKUP_ROOT: "directory",
        PRELOADER_BACKUP_RELATIVE_PATH: "file",
        _PRELOADER_COMPAT_ROOT: "directory",
        PRELOADER_PROVENANCE_RELATIVE_PATH: "file",
    }
    observed = {
        entry.relative_path: (entry.kind, entry.sha256)
        for entry in manifest.entries
        if entry.relative_path in {_PRELOADER_BACKUP_ROOT, _PRELOADER_COMPAT_ROOT}
        or entry.relative_path.startswith(_PRELOADER_BACKUP_ROOT + "/")
        or entry.relative_path.startswith(_PRELOADER_COMPAT_ROOT + "/")
    }
    return set(observed) == set(expected_kinds) and all(
        observed[path][0] == kind
        and (kind == "directory" or observed[path][1] is not None)
        for path, kind in expected_kinds.items()
    )


def _directory_tree_is_exact(
    root: Path,
    relative_path: str,
    expected: dict[str, Literal["file", "directory"]],
) -> bool:
    directory = root / relative_path
    current = root
    for part in PurePosixPath(relative_path).parts:
        current /= part
        if _lstat_kind(current) != "directory":
            return False
    descriptor = -1
    try:
        descriptor = os.open(
            directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        with os.scandir(descriptor) as entries:
            observed: dict[str, str] = {}
            for entry in entries:
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISREG(mode):
                    kind = "file"
                elif stat.S_ISDIR(mode):
                    kind = "directory"
                elif stat.S_ISLNK(mode):
                    kind = "symlink"
                else:
                    kind = "other"
                observed[entry.name] = kind
    except OSError:
        return False
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return observed == expected


def _preloader_compatibility_status(
    root: Path,
    manifest: InstallManifest,
    missing: tuple[str, ...],
    changed: tuple[str, ...],
    repo_root: Path | None,
) -> PreloaderCompatibilityStatus:
    issues: set[str] = set()
    active_evidence = _regular_file_evidence(root, PRELOADER_RELATIVE_PATH)
    active_hash = active_evidence.sha256
    active_entry = _manifest_entry(manifest, PRELOADER_RELATIVE_PATH)
    reserved_roots = (
        root / _PRELOADER_BACKUP_ROOT,
        root / _PRELOADER_COMPAT_ROOT,
    )
    reserved_present = any(
        _lstat_kind(path) != "absent" for path in reserved_roots
    )
    compatibility_entries = tuple(
        entry
        for entry in manifest.entries
        if entry.relative_path
        in {_PRELOADER_BACKUP_ROOT, _PRELOADER_COMPAT_ROOT}
        or entry.relative_path.startswith(_PRELOADER_BACKUP_ROOT + "/")
        or entry.relative_path.startswith(_PRELOADER_COMPAT_ROOT + "/")
    )

    if manifest.runtime_archive_sha256 != EXPECTED_RUNTIME_ARCHIVE_SHA256:
        issues.add("runtime_archive_mismatch")
    if active_evidence.state != "file":
        issues.add(
            "active_missing"
            if active_evidence.state == "missing"
            else "active_unsafe"
        )
    elif (
        active_entry is None
        or active_entry.kind != "file"
        or active_entry.sha256 != active_hash
    ):
        issues.add("active_hash_mismatch")

    non_compat_problems = (
        set(missing) | set(changed)
    ) - {
        PRELOADER_RELATIVE_PATH,
        PRELOADER_BACKUP_RELATIVE_PATH,
        PRELOADER_PROVENANCE_RELATIVE_PATH,
        _PRELOADER_BACKUP_ROOT,
        _PRELOADER_COMPAT_ROOT,
    }
    if non_compat_problems:
        issues.add("install_manifest_unhealthy")

    if not reserved_present and not compatibility_entries:
        if (
            active_hash is not None
            and active_hash != EXPECTED_OFFICIAL_PRELOADER_SHA256
        ):
            issues.add("active_hash_mismatch")
        state: Literal["official", "patched", "invalid"] = (
            "official" if not issues else "invalid"
        )
        return PreloaderCompatibilityStatus(
            state=state,
            official_sha256=EXPECTED_OFFICIAL_PRELOADER_SHA256,
            active_sha256=active_hash,
            patched_sha256=None,
            issues=tuple(sorted(issues)),
        )

    if reserved_present and not compatibility_entries:
        issues.add("unmanaged_reserved_path")
        return PreloaderCompatibilityStatus(
            state="invalid",
            official_sha256=EXPECTED_OFFICIAL_PRELOADER_SHA256,
            active_sha256=active_hash,
            patched_sha256=None,
            issues=tuple(sorted(issues)),
        )

    if not _compatibility_ownership_is_exact(manifest):
        issues.add("manifest_compatibility_ownership_mismatch")
    if not _directory_tree_is_exact(
        root,
        _PRELOADER_BACKUP_ROOT,
        {"BepInEx.Preloader.dll": "file"},
    ) or not _directory_tree_is_exact(
        root,
        _PRELOADER_COMPAT_ROOT,
        {"preloader-provenance.json": "file"},
    ):
        issues.add("unmanaged_reserved_path")

    backup_evidence = _regular_file_evidence(
        root, PRELOADER_BACKUP_RELATIVE_PATH
    )
    backup_hash = backup_evidence.sha256
    if backup_evidence.state != "file":
        issues.add(
            "backup_missing"
            if backup_evidence.state == "missing"
            else "backup_unsafe"
        )
    provenance_path = root / PRELOADER_PROVENANCE_RELATIVE_PATH
    provenance_evidence = _regular_file_evidence(
        root, PRELOADER_PROVENANCE_RELATIVE_PATH
    )
    if provenance_evidence.state != "file":
        issues.add(
            "provenance_missing"
            if provenance_evidence.state == "missing"
            else "provenance_unsafe"
        )

    provenance = None
    if provenance_evidence.state == "file":
        try:
            trust = load_trust(
                repo_root
                if repo_root is not None
                else Path(__file__).resolve().parents[2]
            )
        except (CompatError, OSError):
            issues.add("compatibility_trust_invalid")
        else:
            try:
                provenance = load_provenance(provenance_path, trust)
            except (CompatError, OSError):
                issues.add("provenance_invalid")

    patched_hash = (
        provenance.patched_preloader_sha256
        if provenance is not None
        else None
    )
    backup_entry = _manifest_entry(manifest, PRELOADER_BACKUP_RELATIVE_PATH)
    provenance_entry = _manifest_entry(
        manifest, PRELOADER_PROVENANCE_RELATIVE_PATH
    )
    provenance_hash = provenance_evidence.sha256
    if provenance is not None:
        if (
            active_hash is not None
            and (
                active_hash != provenance.patched_preloader_sha256
                or active_hash != EXPECTED_PATCHED_PRELOADER_SHA256
                or provenance.patched_preloader_sha256
                != EXPECTED_PATCHED_PRELOADER_SHA256
                or active_entry is None
                or active_entry.sha256
                != provenance.patched_preloader_sha256
            )
        ):
            issues.add("active_hash_mismatch")
        if (
            provenance.official_preloader_sha256
            != EXPECTED_OFFICIAL_PRELOADER_SHA256
            or (
                backup_hash is not None
                and (
                    backup_hash != EXPECTED_OFFICIAL_PRELOADER_SHA256
                    or backup_entry is None
                    or backup_entry.sha256
                    != EXPECTED_OFFICIAL_PRELOADER_SHA256
                )
            )
        ):
            issues.add("backup_hash_mismatch")
        if (
            provenance_entry is None
            or provenance_entry.sha256 != provenance_hash
        ):
            issues.add("provenance_hash_mismatch")

    return PreloaderCompatibilityStatus(
        state="patched" if not issues else "invalid",
        official_sha256=EXPECTED_OFFICIAL_PRELOADER_SHA256,
        active_sha256=active_hash,
        patched_sha256=patched_hash,
        issues=tuple(sorted(issues)),
    )


def status_install(
    game_root: Path, repo_root: Path | None = None
) -> InstallStatus:
    """Check every manifest-owned path without modifying the install."""
    game, manifest = _inspected_manifest(game_root)
    missing, changed = _entry_health(game.root, manifest.entries)
    return InstallStatus(
        manifest=manifest,
        missing=missing,
        changed=changed,
        preloader_compatibility=_preloader_compatibility_status(
            game.root, manifest, missing, changed, repo_root
        ),
    )


def recover_install(game_root: Path) -> Path:
    """Move manifest-owned runtime roots aside, preserving all recovered data."""
    root = game_root.resolve()
    manifest = _load_manifest(root)
    top_levels: set[str] = set()
    for entry in manifest.entries:
        _validated_manifest_path(root, entry.relative_path)
        top_level = PurePosixPath(entry.relative_path).parts[0]
        if top_level not in ALLOWED_TOP_LEVEL:
            raise InstallError(
                f"recovery refuses unrelated top-level target: {top_level}"
            )
        top_levels.add(top_level)

    existing_sources: list[Path] = []
    for top_level in sorted(top_levels):
        source = root / top_level
        _inside(root, source)
        if source.is_symlink():
            raise InstallError(
                f"recovery refuses symlinked owned root: {source}"
            )
        if _path_exists(source):
            existing_sources.append(source)

    recovery_parent = root / ".ssr-oracle-recovery"
    _inside(root, recovery_parent)
    if _path_exists(recovery_parent):
        if recovery_parent.is_symlink() or not recovery_parent.is_dir():
            raise InstallError(
                f"recovery parent is not a safe directory: {recovery_parent}"
            )
    else:
        recovery_parent.mkdir()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    recovery = _inside(root, recovery_parent / timestamp)
    if _path_exists(recovery):
        raise InstallError(f"recovery destination already exists: {recovery}")
    recovery.mkdir()

    sources: list[tuple[Path, Path]] = []
    for source in existing_sources:
        destination = _inside(recovery, recovery / source.name)
        if _path_exists(destination):
            raise InstallError(
                f"recovery destination target already exists: {destination}"
            )
        sources.append((source, destination))
    manifest_path = _inside(root, root / MANIFEST_NAME)
    try:
        for source, destination in sources:
            source.replace(destination)
        manifest_path.replace(recovery / MANIFEST_NAME)
    except OSError as exc:
        raise InstallError(f"cannot move owned install into recovery: {exc}") from exc
    return recovery


def _game_to_dict(game: GameInstall) -> dict[str, object]:
    return {
        "root": str(game.root),
        "app": str(game.app),
        "managed": str(game.managed),
        "assembly": str(game.assembly),
        "assembly_sha256": game.assembly_sha256,
    }


def _status_to_dict(status: InstallStatus) -> dict[str, object]:
    return {
        "manifest": _manifest_to_dict(status.manifest),
        "missing": list(status.missing),
        "changed": list(status.changed),
        "healthy": status.healthy,
        "preloader_compatibility": {
            "state": status.preloader_compatibility.state,
            "official_sha256": (
                status.preloader_compatibility.official_sha256
            ),
            "active_sha256": status.preloader_compatibility.active_sha256,
            "patched_sha256": status.preloader_compatibility.patched_sha256,
            "issues": list(status.preloader_compatibility.issues),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in (
        "inspect",
        "install",
        "deploy",
        "deploy-preloader",
        "status",
        "recover",
    ):
        command = sub.add_parser(name)
        command.add_argument("--game-root", type=Path, required=True)
        if name == "install":
            command.add_argument("--archive", type=Path, required=True)
        if name == "deploy":
            command.add_argument("--plugin", type=Path, required=True)
            command.add_argument("--config", type=Path, required=True)
        if name == "deploy-preloader":
            command.add_argument("--preloader", type=Path, required=True)
            command.add_argument("--provenance", type=Path, required=True)
            command.add_argument("--repo-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            output: object = _game_to_dict(inspect_game(args.game_root))
            exit_code = 0
        elif args.command == "install":
            output = _manifest_to_dict(
                install_runtime(args.game_root, args.archive)
            )
            exit_code = 0
        elif args.command == "deploy":
            try:
                config_text = args.config.read_text()
            except (OSError, UnicodeError) as exc:
                raise InstallError(f"cannot read config {args.config}: {exc}") from exc
            output = _manifest_to_dict(
                deploy_plugin(args.game_root, args.plugin, config_text)
            )
            exit_code = 0
        elif args.command == "deploy-preloader":
            output = _manifest_to_dict(
                deploy_preloader(
                    args.game_root,
                    args.preloader,
                    args.provenance,
                    repo_root=args.repo_root,
                )
            )
            exit_code = 0
        elif args.command == "status":
            status = status_install(args.game_root)
            output = _status_to_dict(status)
            exit_code = 0 if status.healthy else 1
        else:
            output = {"recovery": str(recover_install(args.game_root))}
            exit_code = 0
    except InstallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True))
    return exit_code
