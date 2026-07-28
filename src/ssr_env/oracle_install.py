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
_RESTORE_SOURCE_COMMIT = "57f1fb859bd4d0264cd2a59074d0e96c6a492a33"
_RESTORE_DOTNET_SDK_VERSION = "8.0.419"
_RESTORE_BUILD_TARGET = (
    "BepInEx.Preloader/BepInEx.Preloader.csproj@framework=net35"
)


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
    backup_moved: bool = False
    provenance_moved: bool = False
    active_swapped: bool = False
    active_preserved: bool = False
    active_preserved_name: str = ""
    manifest_swapped: bool = False
    backup_directory_moved: bool = False
    compat_directory_moved: bool = False
    manifest_preserved: bool = False
    manifest_preserved_name: str = ""


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
    observed = datetime.now(UTC)
    timestamp = f"{observed:%Y%m%dT%H%M%SZ}"
    return f"{timestamp}-{secrets.token_hex(16)}"


def _restore_preloader_checkpoint(boundary: str) -> None:
    del boundary


def _restore_open_child_directory(
    parent: _DirectoryHandle,
    name: str,
    description: str,
) -> _DirectoryHandle:
    try:
        descriptor = os.open(name, _DIRECTORY_OPEN_FLAGS, dir_fd=parent.fd)
    except OSError as exc:
        raise InstallError(
            f"cannot open {description} without following symlinks: {exc}"
        ) from exc
    try:
        observed = os.fstat(descriptor)
    except OSError as exc:
        os.close(descriptor)
        raise InstallError(f"cannot inspect {description}: {exc}") from exc
    if not stat.S_ISDIR(observed.st_mode):
        os.close(descriptor)
        raise InstallError(f"{description} is not a directory")
    return _DirectoryHandle(
        descriptor,
        observed.st_dev,
        observed.st_ino,
        description,
    )


def _restore_open_absolute_directory(
    path: Path,
    description: str,
) -> _DirectoryHandle:
    parts = Path(path).parts
    if not parts or parts[0] != "/":
        raise InstallError(f"{description} must be an absolute path")
    descriptor = -1
    current: _DirectoryHandle | None = None
    try:
        descriptor = os.open("/", _DIRECTORY_OPEN_FLAGS)
        observed = os.fstat(descriptor)
        current = _DirectoryHandle(
            descriptor,
            observed.st_dev,
            observed.st_ino,
            f"{description} filesystem root",
        )
        descriptor = -1
        for part in parts[1:]:
            if part in {"", ".", ".."}:
                raise InstallError(f"{description} has an unsafe component")
            following = _restore_open_child_directory(
                current, part, description
            )
            os.close(current.fd)
            current = following
        return current
    except Exception:
        if current is not None:
            os.close(current.fd)
        if descriptor >= 0:
            os.close(descriptor)
        raise


def _restore_verify_named_directory(
    parent: _DirectoryHandle,
    name: str,
    child: _DirectoryHandle,
) -> None:
    parent_observed = os.fstat(parent.fd)
    child_observed = os.fstat(child.fd)
    named = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    if (
        not stat.S_ISDIR(parent_observed.st_mode)
        or parent_observed.st_dev != parent.device
        or parent_observed.st_ino != parent.inode
        or not stat.S_ISDIR(child_observed.st_mode)
        or child_observed.st_dev != child.device
        or child_observed.st_ino != child.inode
        or not stat.S_ISDIR(named.st_mode)
        or named.st_dev != child.device
        or named.st_ino != child.inode
    ):
        raise InstallError(f"{child.label} identity changed")


def _restore_verify_absolute_directory(
    path: Path,
    expected: _DirectoryHandle,
) -> None:
    observed = _restore_open_absolute_directory(
        path, f"revalidate {expected.label}"
    )
    try:
        if (
            observed.device != expected.device
            or observed.inode != expected.inode
        ):
            raise InstallError(f"{expected.label} pathname detached")
    finally:
        os.close(observed.fd)


def _restore_read_stable_file(
    parent: _DirectoryHandle,
    name: str,
    description: str,
) -> tuple[int, _StableFileSnapshot]:
    descriptor = -1
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=parent.fd,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise InstallError(f"{description} is not a safe regular file")
        payload = b""
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload += chunk
        after = os.fstat(descriptor)
        named = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(after.st_mode)
            or not stat.S_ISREG(named.st_mode)
            or before.st_dev != after.st_dev
            or before.st_ino != after.st_ino
            or before.st_size != after.st_size
            or before.st_mode & 0o7777 != after.st_mode & 0o7777
            or after.st_dev != named.st_dev
            or after.st_ino != named.st_ino
            or after.st_size != named.st_size
            or after.st_mode & 0o7777 != named.st_mode & 0o7777
            or len(payload) != after.st_size
        ):
            raise InstallError(f"{description} changed while being read")
        return (
            descriptor,
            _StableFileSnapshot(
                payload,
                after.st_mode & 0o7777,
                after.st_dev,
                after.st_ino,
                after.st_size,
            ),
        )
    except OSError as exc:
        if descriptor >= 0:
            os.close(descriptor)
        raise InstallError(
            f"{description} is not a safe regular file: {exc}"
        ) from exc
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        raise


def _restore_revalidate_stable_file(
    parent: _DirectoryHandle,
    name: str,
    descriptor: int,
    expected: _StableFileSnapshot,
    description: str,
) -> None:
    retained = os.fstat(descriptor)
    named = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    if (
        not stat.S_ISREG(retained.st_mode)
        or not stat.S_ISREG(named.st_mode)
        or retained.st_dev != expected.device
        or retained.st_ino != expected.inode
        or retained.st_size != expected.size
        or retained.st_mode & 0o7777 != expected.mode
        or named.st_dev != expected.device
        or named.st_ino != expected.inode
        or named.st_size != expected.size
        or named.st_mode & 0o7777 != expected.mode
    ):
        raise InstallError(f"{description} changed after validation")
    reopened, observed = _restore_read_stable_file(parent, name, description)
    try:
        if observed != expected:
            raise InstallError(f"{description} payload changed after validation")
    finally:
        os.close(reopened)


def _restore_directory_has_only(
    directory: _DirectoryHandle,
    expected_name: str,
) -> bool:
    count = 0
    matched = False
    with os.scandir(directory.fd) as entries:
        for entry in entries:
            count += 1
            if entry.name == expected_name:
                matched = True
    return count == 1 and matched


def _restore_is_lower_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    for character in value:
        if character not in "0123456789abcdef":
            return False
    return True


def _restore_safe_manifest_path(relative_path: str) -> tuple[str, ...]:
    if (
        not relative_path
        or relative_path[0] == "/"
        or "\x00" in relative_path
        or "\\" in relative_path
    ):
        raise InstallError("install manifest contains an unsafe path")
    parts = Path(relative_path).parts
    if not parts or parts[0] not in ALLOWED_TOP_LEVEL:
        raise InstallError("install manifest contains an unapproved path")
    for part in parts:
        if part in {"", ".", ".."}:
            raise InstallError("install manifest contains an unsafe path")
    canonical = ""
    for part in parts:
        canonical = part if not canonical else canonical + "/" + part
    if canonical != relative_path:
        raise InstallError("install manifest contains a noncanonical path")
    if parts[0] != "BepInEx" and len(parts) != 1:
        raise InstallError("install manifest contains an unapproved path")
    return parts


def _restore_revalidate_preflight_sources(
    managed: _DirectoryHandle,
    assembly_descriptor: int,
    assembly: _StableFileSnapshot,
    root: _DirectoryHandle,
    manifest_descriptor: int,
    manifest_snapshot: _StableFileSnapshot,
    core: _DirectoryHandle,
    active_descriptor: int,
    active: _StableFileSnapshot,
    bep_in_ex: _DirectoryHandle,
    backup_directory: _DirectoryHandle,
    backup_descriptor: int,
    backup: _StableFileSnapshot,
    compat_directory: _DirectoryHandle,
    provenance_descriptor: int,
    provenance: _StableFileSnapshot,
) -> None:
    _restore_revalidate_stable_file(
        managed,
        "Assembly-CSharp.dll",
        assembly_descriptor,
        assembly,
        "game assembly",
    )
    _restore_revalidate_stable_file(
        root,
        MANIFEST_NAME,
        manifest_descriptor,
        manifest_snapshot,
        "install manifest",
    )
    _restore_revalidate_stable_file(
        core,
        "BepInEx.Preloader.dll",
        active_descriptor,
        active,
        "active preloader",
    )
    _restore_revalidate_stable_file(
        backup_directory,
        "BepInEx.Preloader.dll",
        backup_descriptor,
        backup,
        "official preloader backup",
    )
    _restore_revalidate_stable_file(
        compat_directory,
        "preloader-provenance.json",
        provenance_descriptor,
        provenance,
        "preloader provenance",
    )
    _restore_verify_named_directory(
        bep_in_ex, ".ssr-oracle-backup", backup_directory
    )
    _restore_verify_named_directory(
        bep_in_ex, ".ssr-oracle-compat", compat_directory
    )
    if not _restore_directory_has_only(
        backup_directory, "BepInEx.Preloader.dll"
    ) or not _restore_directory_has_only(
        compat_directory, "preloader-provenance.json"
    ):
        raise InstallError("compatibility directories changed after validation")


def _restore_manifest_and_snapshots(
    game_root: Path,
    repo_root: Path | None,
) -> tuple[
    Path,
    InstallManifest,
    _DirectoryHandle,
    _DirectoryHandle,
    _DirectoryHandle,
    _DirectoryHandle,
    _DirectoryHandle,
    int,
    _StableFileSnapshot,
    int,
    _StableFileSnapshot,
    int,
    _StableFileSnapshot,
    int,
    _StableFileSnapshot,
    int,
    _StableFileSnapshot,
    _DirectoryHandle,
    _DirectoryHandle,
    _DirectoryHandle,
    _DirectoryHandle,
    _DirectoryHandle,
]:
    game_path = Path(game_root)
    root_descriptor = -1
    assembly_descriptor = -1
    manifest_descriptor = -1
    active_descriptor = -1
    backup_descriptor = -1
    provenance_descriptor = -1
    root: _DirectoryHandle | None = None
    bep_in_ex: _DirectoryHandle | None = None
    core: _DirectoryHandle | None = None
    backup_directory: _DirectoryHandle | None = None
    compat_directory: _DirectoryHandle | None = None
    app: _DirectoryHandle | None = None
    contents: _DirectoryHandle | None = None
    resources: _DirectoryHandle | None = None
    data: _DirectoryHandle | None = None
    managed: _DirectoryHandle | None = None
    try:
        root = _restore_open_absolute_directory(
            game_path,
            "game root",
        )

        app = _restore_open_child_directory(root, "Sausage.app", "game app")
        contents = _restore_open_child_directory(app, "Contents", "app Contents")
        resources = _restore_open_child_directory(
            contents, "Resources", "app Resources"
        )
        data = _restore_open_child_directory(resources, "Data", "game Data")
        managed = _restore_open_child_directory(
            data, "Managed", "game Managed"
        )
        assembly_descriptor, assembly = _restore_read_stable_file(
            managed, "Assembly-CSharp.dll", "game assembly"
        )
        assembly_hash = sha256(assembly.payload).hexdigest()
        if assembly_hash != EXPECTED_ASSEMBLY_SHA256:
            raise InstallError("unsupported game assembly")

        manifest_descriptor, manifest_snapshot = _restore_read_stable_file(
            root, MANIFEST_NAME, "install manifest"
        )
        try:
            decoded = json.loads(manifest_snapshot.payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InstallError(f"cannot parse install manifest: {exc}") from exc
        if (
            not isinstance(decoded, dict)
            or set(decoded)
            != {
                "schema_version",
                "game_assembly_sha256",
                "runtime_archive_sha256",
                "entries",
            }
            or not isinstance(decoded["schema_version"], int)
            or isinstance(decoded["schema_version"], bool)
            or decoded["schema_version"] != 1
            or decoded["game_assembly_sha256"] != assembly_hash
            or decoded["runtime_archive_sha256"]
            != EXPECTED_RUNTIME_ARCHIVE_SHA256
            or not isinstance(decoded["entries"], list)
        ):
            raise InstallError("install manifest does not match the game")

        entries: tuple[ManifestEntry, ...] = ()
        seen_paths: tuple[str, ...] = ()
        directory_paths: tuple[str, ...] = ()
        active_entry_hash: str | None = None
        backup_entry_hash: str | None = None
        provenance_entry_hash: str | None = None
        backup_root_count = 0
        compat_root_count = 0
        for raw_entry in decoded["entries"]:
            if (
                not isinstance(raw_entry, dict)
                or set(raw_entry) != {"relative_path", "kind", "sha256"}
                or not isinstance(raw_entry["relative_path"], str)
                or not isinstance(raw_entry["kind"], str)
            ):
                raise InstallError("malformed install manifest entry")
            relative_path = raw_entry["relative_path"]
            kind = raw_entry["kind"]
            entry_hash = raw_entry["sha256"]
            parts = _restore_safe_manifest_path(relative_path)
            if relative_path in seen_paths:
                raise InstallError("install manifest contains a duplicate path")
            seen_paths += (relative_path,)
            if kind not in {"file", "directory"}:
                raise InstallError("malformed install manifest entry kind")
            if kind == "file" and not _restore_is_lower_sha256(entry_hash):
                raise InstallError("malformed install manifest file hash")
            if kind == "directory" and entry_hash is not None:
                raise InstallError("malformed install manifest directory hash")
            if relative_path == "BepInEx" and kind != "directory":
                raise InstallError("BepInEx manifest root is not a directory")
            if parts[0] != "BepInEx" and kind != "file":
                raise InstallError("top-level runtime entry is not a file")
            if kind == "directory":
                directory_paths += (relative_path,)
            entries += (
                ManifestEntry(
                    relative_path,
                    kind,
                    entry_hash if isinstance(entry_hash, str) else None,
                ),
            )
            if relative_path == PRELOADER_RELATIVE_PATH and kind == "file":
                active_entry_hash = entry_hash
            if (
                relative_path == PRELOADER_BACKUP_RELATIVE_PATH
                and kind == "file"
            ):
                backup_entry_hash = entry_hash
            if (
                relative_path == PRELOADER_PROVENANCE_RELATIVE_PATH
                and kind == "file"
            ):
                provenance_entry_hash = entry_hash
            if (
                relative_path == _PRELOADER_BACKUP_ROOT
                or relative_path[: len(_PRELOADER_BACKUP_ROOT) + 1]
                == _PRELOADER_BACKUP_ROOT + "/"
            ):
                backup_root_count += 1
            if (
                relative_path == _PRELOADER_COMPAT_ROOT
                or relative_path[: len(_PRELOADER_COMPAT_ROOT) + 1]
                == _PRELOADER_COMPAT_ROOT + "/"
            ):
                compat_root_count += 1

        for entry in entries:
            parts = _restore_safe_manifest_path(entry.relative_path)
            prefix = ""
            index = 0
            for part in parts:
                prefix = part if not prefix else prefix + "/" + part
                index += 1
                if index < len(parts) and prefix not in directory_paths:
                    raise InstallError(
                        "install manifest path lacks a directory parent"
                    )
        for required_file in REQUIRED_ARCHIVE_FILES:
            found_required_file = False
            for entry in entries:
                if (
                    entry.relative_path == required_file
                    and entry.kind == "file"
                ):
                    found_required_file = True
            if not found_required_file:
                raise InstallError(
                    "install manifest lacks required runtime file ownership"
                )
        for required_directory in REQUIRED_RUNTIME_DIRECTORIES:
            found_required_directory = False
            for entry in entries:
                if (
                    entry.relative_path == required_directory
                    and entry.kind == "directory"
                ):
                    found_required_directory = True
            if not found_required_directory:
                raise InstallError(
                    "install manifest lacks required runtime directory ownership"
                )

        manifest = InstallManifest(
            1,
            decoded["game_assembly_sha256"],
            decoded["runtime_archive_sha256"],
            entries,
        )
        bep_in_ex = _restore_open_child_directory(
            root, "BepInEx", "live BepInEx"
        )
        core = _restore_open_child_directory(
            bep_in_ex, "core", "live preloader parent"
        )
        active_descriptor, active = _restore_read_stable_file(
            core, "BepInEx.Preloader.dll", "active preloader"
        )
        active_hash = sha256(active.payload).hexdigest()
        if (
            active_hash == EXPECTED_OFFICIAL_PRELOADER_SHA256
            and backup_root_count == 0
            and compat_root_count == 0
        ):
            raise InstallError("preloader compatibility is not patched")
        if (
            active_hash != EXPECTED_PATCHED_PRELOADER_SHA256
            or active_entry_hash != active_hash
            or backup_root_count != 2
            or compat_root_count != 2
        ):
            raise InstallError("preloader compatibility state is invalid")

        backup_directory = _restore_open_child_directory(
            bep_in_ex,
            ".ssr-oracle-backup",
            "live compatibility backup directory",
        )
        compat_directory = _restore_open_child_directory(
            bep_in_ex,
            ".ssr-oracle-compat",
            "live compatibility provenance directory",
        )
        if not _restore_directory_has_only(
            backup_directory, "BepInEx.Preloader.dll"
        ) or not _restore_directory_has_only(
            compat_directory, "preloader-provenance.json"
        ):
            raise InstallError("compatibility directories are not exactly owned")
        backup_descriptor, backup = _restore_read_stable_file(
            backup_directory,
            "BepInEx.Preloader.dll",
            "official preloader backup",
        )
        provenance_descriptor, provenance = _restore_read_stable_file(
            compat_directory,
            "preloader-provenance.json",
            "preloader provenance",
        )
        backup_hash = sha256(backup.payload).hexdigest()
        provenance_hash = sha256(provenance.payload).hexdigest()
        if (
            backup_hash != EXPECTED_OFFICIAL_PRELOADER_SHA256
            or backup_entry_hash != backup_hash
            or provenance_entry_hash != provenance_hash
        ):
            raise InstallError("compatibility snapshots do not match manifest")
        try:
            provenance_data = json.loads(provenance.payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InstallError(f"cannot parse preloader provenance: {exc}") from exc
        if not isinstance(provenance_data, dict):
            raise InstallError("preloader provenance is malformed")
        try:
            trust = load_trust(
                Path(repo_root)
                if repo_root is not None
                else Path(__file__).parents[2]
            )
        except (CompatError, OSError) as exc:
            raise InstallError(f"compatibility trust is invalid: {exc}") from exc
        if (
            set(provenance_data)
            != {
                "schema_version",
                "source_commit",
                "patch_sha256",
                "toolchain_lock_sha256",
                "dotnet_sdk_version",
                "dependency_lock_sha256",
                "build_target",
                "official_preloader_sha256",
                "patched_preloader_sha256",
            }
            or provenance_data["schema_version"] != 1
            or provenance_data["patch_sha256"] != trust.patch_sha256
            or provenance_data["toolchain_lock_sha256"]
            != trust.toolchain_sha256
            or provenance_data["dependency_lock_sha256"]
            != trust.dependencies_sha256
            or provenance_data["source_commit"] != _RESTORE_SOURCE_COMMIT
            or provenance_data["dotnet_sdk_version"]
            != _RESTORE_DOTNET_SDK_VERSION
            or provenance_data["build_target"] != _RESTORE_BUILD_TARGET
            or provenance_data["official_preloader_sha256"] != backup_hash
            or provenance_data["patched_preloader_sha256"] != active_hash
        ):
            raise InstallError("preloader provenance does not match trust")

        recovery_kind = "absent"
        try:
            recovery_observed = os.stat(
                ".ssr-oracle-recovery",
                dir_fd=root.fd,
                follow_symlinks=False,
            )
            if stat.S_ISDIR(recovery_observed.st_mode):
                recovery_kind = "directory"
            elif stat.S_ISLNK(recovery_observed.st_mode):
                recovery_kind = "symlink"
            else:
                recovery_kind = "other"
        except FileNotFoundError:
            recovery_kind = "absent"
        except OSError as exc:
            raise InstallError(f"cannot inspect recovery parent: {exc}") from exc
        if recovery_kind not in {"absent", "directory"}:
            raise InstallError("recovery parent is not a safe directory")

        _restore_preloader_checkpoint("restore_before_preflight_revalidation")
        _restore_revalidate_preflight_sources(
            managed,
            assembly_descriptor,
            assembly,
            root,
            manifest_descriptor,
            manifest_snapshot,
            core,
            active_descriptor,
            active,
            bep_in_ex,
            backup_directory,
            backup_descriptor,
            backup,
            compat_directory,
            provenance_descriptor,
            provenance,
        )
        _restore_preloader_checkpoint("restore_after_preflight_revalidation")
        _restore_revalidate_preflight_sources(
            managed,
            assembly_descriptor,
            assembly,
            root,
            manifest_descriptor,
            manifest_snapshot,
            core,
            active_descriptor,
            active,
            bep_in_ex,
            backup_directory,
            backup_descriptor,
            backup,
            compat_directory,
            provenance_descriptor,
            provenance,
        )
        return (
            game_path,
            manifest,
            root,
            bep_in_ex,
            core,
            backup_directory,
            compat_directory,
            manifest_descriptor,
            manifest_snapshot,
            active_descriptor,
            active,
            backup_descriptor,
            backup,
            provenance_descriptor,
            provenance,
            assembly_descriptor,
            assembly,
            managed,
            data,
            resources,
            contents,
            app,
        )
    except Exception:
        if provenance_descriptor >= 0:
            os.close(provenance_descriptor)
        if backup_descriptor >= 0:
            os.close(backup_descriptor)
        if active_descriptor >= 0:
            os.close(active_descriptor)
        if manifest_descriptor >= 0:
            os.close(manifest_descriptor)
        if assembly_descriptor >= 0:
            os.close(assembly_descriptor)
        if managed is not None:
            os.close(managed.fd)
        if data is not None:
            os.close(data.fd)
        if resources is not None:
            os.close(resources.fd)
        if contents is not None:
            os.close(contents.fd)
        if app is not None:
            os.close(app.fd)
        if compat_directory is not None:
            os.close(compat_directory.fd)
        if backup_directory is not None:
            os.close(backup_directory.fd)
        if core is not None:
            os.close(core.fd)
        if bep_in_ex is not None:
            os.close(bep_in_ex.fd)
        if root is not None:
            os.close(root.fd)
        if root_descriptor >= 0:
            os.close(root_descriptor)
        raise


def _restore_checkpoint_fsync(
    handle: _DirectoryHandle,
    before: str,
    after: str,
    legacy: str,
) -> None:
    _restore_preloader_checkpoint(before)
    os.fsync(handle.fd)
    _restore_preloader_checkpoint(after)
    if legacy:
        _restore_preloader_checkpoint(legacy)


def _restore_create_published_child(
    parent: _DirectoryHandle,
    name: str,
    description: str,
    create_prefix: str,
    legacy_prefix: str,
    standalone_fsync: bool,
) -> _DirectoryHandle:
    child: _DirectoryHandle | None = None
    temporary = f".ssr-oracle-recovery-dir-{secrets.token_hex(16)}"
    try:
        _restore_preloader_checkpoint(
            f"restore_before_{create_prefix}_create"
        )
        os.mkdir(name, 0o700, dir_fd=parent.fd)
        _restore_preloader_checkpoint(
            f"restore_after_{create_prefix}_create"
        )
        _restore_preloader_checkpoint(f"restore_before_{create_prefix}_open")
        child = _restore_open_child_directory(parent, name, description)
        _restore_preloader_checkpoint(f"restore_after_{create_prefix}_open")
        _renameatx(
            parent,
            name,
            parent,
            temporary,
            _RENAME_EXCL,
            f"stage {description} directory",
        )
        _renameatx(
            parent,
            temporary,
            parent,
            name,
            _RENAME_EXCL,
            f"publish {description} directory",
        )
        _restore_verify_named_directory(parent, name, child)
        _restore_preloader_checkpoint(f"{legacy_prefix}_mkdir")
        if standalone_fsync:
            _restore_checkpoint_fsync(
                child,
                f"restore_before_{create_prefix}_fsync",
                f"restore_after_{create_prefix}_fsync",
                "",
            )
        _restore_checkpoint_fsync(
            child,
            f"restore_before_{create_prefix}_child_fsync",
            f"restore_after_{create_prefix}_child_fsync",
            f"{legacy_prefix}_child_fsync",
        )
        _restore_checkpoint_fsync(
            parent,
            f"restore_before_{create_prefix}_parent_fsync",
            f"restore_after_{create_prefix}_parent_fsync",
            f"{legacy_prefix}_parent_fsync",
        )
        return child
    except Exception:
        if child is not None:
            os.close(child.fd)
        raise


def _restore_allocate_recovery(
    root: _DirectoryHandle,
) -> _CompatRecovery:
    parent: _DirectoryHandle | None = None
    run: _DirectoryHandle | None = None
    compat: _DirectoryHandle | None = None
    bep_in_ex: _DirectoryHandle | None = None
    backup: _DirectoryHandle | None = None
    provenance: _DirectoryHandle | None = None
    cleanup: _DirectoryHandle | None = None
    parent_created = False
    run_name = ""
    try:
        try:
            observed = os.stat(
                ".ssr-oracle-recovery",
                dir_fd=root.fd,
                follow_symlinks=False,
            )
            parent_exists = stat.S_ISDIR(observed.st_mode)
        except FileNotFoundError:
            parent_exists = False
        if not parent_exists:
            _restore_preloader_checkpoint(
                "restore_before_recovery_parent_create"
            )
            os.mkdir(".ssr-oracle-recovery", 0o700, dir_fd=root.fd)
            _restore_preloader_checkpoint(
                "restore_after_recovery_parent_create"
            )
            _restore_preloader_checkpoint("recovery_parent_mkdir")
            parent_created = True
        _restore_preloader_checkpoint(
            "restore_before_recovery_parent_open"
        )
        parent = _restore_open_child_directory(
            root, ".ssr-oracle-recovery", "recovery parent"
        )
        _restore_preloader_checkpoint("restore_after_recovery_parent_open")
        _restore_checkpoint_fsync(
            root,
            "restore_before_recovery_parent_fsync",
            "restore_after_recovery_parent_fsync",
            "",
        )
        _restore_checkpoint_fsync(
            parent,
            "restore_before_recovery_parent_child_fsync",
            "restore_after_recovery_parent_child_fsync",
            "recovery_parent_child_fsync",
        )
        _restore_checkpoint_fsync(
            root,
            "restore_before_recovery_parent_parent_fsync",
            "restore_after_recovery_parent_parent_fsync",
            "recovery_parent_parent_fsync",
        )

        temporary = f".ssr-oracle-recovery-run-{secrets.token_hex(16)}"
        os.mkdir(temporary, 0o700, dir_fd=parent.fd)
        for _ in range(128):
            run_name = _compat_recovery_name()
            _restore_preloader_checkpoint(
                "restore_before_recovery_run_publish"
            )
            try:
                _renameatx(
                    parent,
                    temporary,
                    parent,
                    run_name,
                    _RENAME_EXCL,
                    "publish compatibility recovery run directory",
                )
            except _RenameAtError as exc:
                if exc.error_number == errno.EEXIST:
                    continue
                raise
            _restore_preloader_checkpoint(
                "restore_after_recovery_run_publish"
            )
            break
        else:
            raise InstallError(
                "cannot allocate an exclusive compatibility recovery run"
            )
        _restore_preloader_checkpoint("recovery_run_mkdir")
        _restore_preloader_checkpoint("restore_before_recovery_run_open")
        run = _restore_open_child_directory(
            parent, run_name, "compatibility recovery run"
        )
        _restore_preloader_checkpoint("restore_after_recovery_run_open")
        _restore_checkpoint_fsync(
            run,
            "restore_before_recovery_run_fsync",
            "restore_after_recovery_run_fsync",
            "",
        )
        _restore_checkpoint_fsync(
            run,
            "restore_before_recovery_run_child_fsync",
            "restore_after_recovery_run_child_fsync",
            "recovery_run_child_fsync",
        )
        _restore_checkpoint_fsync(
            parent,
            "restore_before_recovery_run_parent_fsync",
            "restore_after_recovery_run_parent_fsync",
            "recovery_run_parent_fsync",
        )

        compat = _restore_create_published_child(
            run,
            "compat",
            "compatibility recovery",
            "recovery_compat",
            "recovery_compat",
            True,
        )
        bep_in_ex = _restore_create_published_child(
            compat,
            "BepInEx",
            "recovery BepInEx",
            "recovery_bepinex",
            "recovery_bepinex",
            False,
        )
        backup = _restore_create_published_child(
            bep_in_ex,
            ".ssr-oracle-backup",
            "recovery backup directory",
            "recovery_backup",
            "recovery_backup_dir",
            False,
        )
        provenance = _restore_create_published_child(
            bep_in_ex,
            ".ssr-oracle-compat",
            "recovery provenance directory",
            "recovery_provenance",
            "recovery_provenance_dir",
            False,
        )
        cleanup = _restore_create_published_child(
            run,
            "cleanup",
            "recovery cleanup directory",
            "recovery_cleanup",
            "recovery_cleanup_dir",
            True,
        )
        recovery = _CompatRecovery(
            parent,
            parent_created,
            run_name,
            run,
            compat,
            bep_in_ex,
            backup,
            provenance,
            cleanup,
            False,
            False,
            False,
            False,
            "",
            False,
            False,
            False,
            False,
            "",
        )
        _restore_preloader_checkpoint("restore_recovery_graph_pinned")
        return recovery
    except Exception as exc:
        if cleanup is not None:
            os.close(cleanup.fd)
        if provenance is not None:
            os.close(provenance.fd)
        if backup is not None:
            os.close(backup.fd)
        if bep_in_ex is not None:
            os.close(bep_in_ex.fd)
        if compat is not None:
            os.close(compat.fd)
        if run is not None:
            os.close(run.fd)
        if parent is not None:
            os.close(parent.fd)
        raise InstallError(
            f"restore_preloader recovery allocation failed: {exc}"
        ) from exc


def _restore_close_recovery(recovery: _CompatRecovery) -> None:
    os.close(recovery.cleanup.fd)
    os.close(recovery.provenance.fd)
    os.close(recovery.backup.fd)
    os.close(recovery.bep_in_ex.fd)
    os.close(recovery.compat.fd)
    os.close(recovery.run.fd)
    os.close(recovery.parent.fd)


def _restore_close_preflight(
    preflight: tuple[
        Path,
        InstallManifest,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
    ],
) -> None:
    os.close(preflight[15])
    os.close(preflight[13])
    os.close(preflight[11])
    os.close(preflight[9])
    os.close(preflight[7])
    os.close(preflight[17].fd)
    os.close(preflight[18].fd)
    os.close(preflight[19].fd)
    os.close(preflight[20].fd)
    os.close(preflight[21].fd)
    os.close(preflight[6].fd)
    os.close(preflight[5].fd)
    os.close(preflight[4].fd)
    os.close(preflight[3].fd)
    os.close(preflight[2].fd)


def _restore_official_manifest(
    patched: InstallManifest,
) -> tuple[InstallManifest, bytes]:
    ordered: tuple[ManifestEntry, ...] = ()
    for entry in patched.entries:
        relative_path = entry.relative_path
        if (
            relative_path == _PRELOADER_BACKUP_ROOT
            or relative_path[: len(_PRELOADER_BACKUP_ROOT) + 1]
            == _PRELOADER_BACKUP_ROOT + "/"
            or relative_path == _PRELOADER_COMPAT_ROOT
            or relative_path[: len(_PRELOADER_COMPAT_ROOT) + 1]
            == _PRELOADER_COMPAT_ROOT + "/"
        ):
            continue
        candidate = (
            ManifestEntry(
                PRELOADER_RELATIVE_PATH,
                "file",
                EXPECTED_OFFICIAL_PRELOADER_SHA256,
            )
            if relative_path == PRELOADER_RELATIVE_PATH
            else entry
        )
        inserted = False
        rebuilt: tuple[ManifestEntry, ...] = ()
        for observed in ordered:
            if (
                not inserted
                and candidate.relative_path < observed.relative_path
            ):
                rebuilt += (candidate,)
                inserted = True
            rebuilt += (observed,)
        if not inserted:
            rebuilt += (candidate,)
        ordered = rebuilt
    official = InstallManifest(
        patched.schema_version,
        patched.game_assembly_sha256,
        patched.runtime_archive_sha256,
        ordered,
    )
    raw_entries: tuple[dict[str, object], ...] = ()
    for entry in ordered:
        raw_entries += (
            {
                "relative_path": entry.relative_path,
                "kind": entry.kind,
                "sha256": entry.sha256,
            },
        )
    encoded = json.dumps(
        {
            "schema_version": official.schema_version,
            "game_assembly_sha256": official.game_assembly_sha256,
            "runtime_archive_sha256": official.runtime_archive_sha256,
            "entries": raw_entries,
        },
        sort_keys=True,
        indent=2,
    )
    return official, bytes(encoded + "\n", "utf-8")


def _restore_stage_file(
    parent: _DirectoryHandle,
    name: str,
    payload: bytes,
    mode: int,
    prefix: str,
) -> _StableFileSnapshot:
    descriptor = -1
    try:
        descriptor = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
            dir_fd=parent.fd,
        )
        _restore_preloader_checkpoint(f"restore_before_{prefix}_write")
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise InstallError(f"cannot write {prefix}")
            offset += written
        _restore_preloader_checkpoint(f"restore_after_{prefix}_write")
        _restore_preloader_checkpoint(f"restore_before_{prefix}_chmod")
        os.fchmod(descriptor, mode)
        _restore_preloader_checkpoint(f"restore_after_{prefix}_chmod")
        _restore_preloader_checkpoint(f"restore_before_{prefix}_file_fsync")
        os.fsync(descriptor)
        _restore_preloader_checkpoint(f"restore_after_{prefix}_file_fsync")
        observed = os.fstat(descriptor)
        return _StableFileSnapshot(
            payload,
            observed.st_mode & 0o7777,
            observed.st_dev,
            observed.st_ino,
            observed.st_size,
        )
    except OSError as exc:
        raise InstallError(f"cannot stage {prefix}: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _restore_sync_rename_parents(
    source_parent: _DirectoryHandle,
    destination_parent: _DirectoryHandle,
    prefix: str,
) -> None:
    _restore_checkpoint_fsync(
        source_parent,
        f"restore_before_{prefix}_source_parent_fsync",
        f"restore_after_{prefix}_source_parent_fsync",
        "",
    )
    _restore_checkpoint_fsync(
        destination_parent,
        f"restore_before_{prefix}_destination_parent_fsync",
        f"restore_after_{prefix}_destination_parent_fsync",
        "",
    )


def _restore_sync_rollback_parents(
    source_parent: _DirectoryHandle,
    destination_parent: _DirectoryHandle,
    prefix: str,
) -> None:
    _restore_checkpoint_fsync(
        source_parent,
        f"restore_rollback_before_{prefix}_source_parent_fsync",
        f"restore_rollback_after_{prefix}_source_parent_fsync",
        "",
    )
    _restore_checkpoint_fsync(
        destination_parent,
        f"restore_rollback_before_{prefix}_destination_parent_fsync",
        f"restore_rollback_after_{prefix}_destination_parent_fsync",
        "",
    )


def _restore_move_live_file(
    source_parent: _DirectoryHandle,
    source_parent_parent: _DirectoryHandle,
    source_parent_name: str,
    source_name: str,
    source_descriptor: int,
    expected: _StableFileSnapshot,
    destination_parent: _DirectoryHandle,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    _restore_verify_named_directory(
        source_parent_parent, source_parent_name, source_parent
    )
    _restore_revalidate_stable_file(
        source_parent,
        source_name,
        source_descriptor,
        expected,
        prefix,
    )
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_parent_replacement"
    )
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_source_substitution"
    )
    _restore_preloader_checkpoint(f"restore_before_{prefix}_move")
    _renameatx(
        source_parent,
        source_name,
        destination_parent,
        source_name,
        _RENAME_EXCL,
        f"move restore {prefix} to recovery",
    )
    if prefix == "backup":
        recovery.backup_moved = True
    else:
        recovery.provenance_moved = True
    _restore_preloader_checkpoint(f"restore_after_{prefix}_move")
    _restore_preloader_checkpoint(f"restore_before_{prefix}_reopen")
    reopened, observed = _restore_read_stable_file(
        destination_parent, source_name, f"recovered {prefix}"
    )
    _restore_preloader_checkpoint(f"restore_after_{prefix}_reopen")
    try:
        _restore_preloader_checkpoint(
            f"restore_before_{prefix}_snapshot_validation"
        )
        _restore_revalidate_stable_file(
            destination_parent,
            source_name,
            reopened,
            observed,
            f"recovered {prefix}",
        )
        if observed != expected:
            _renameatx(
                destination_parent,
                source_name,
                source_parent,
                source_name,
                _RENAME_EXCL,
                f"restore unexpected recovered {prefix}",
            )
            _restore_sync_rename_parents(
                destination_parent,
                source_parent,
                f"{prefix}_mismatch_restore",
            )
            if prefix == "backup":
                recovery.backup_moved = False
            else:
                recovery.provenance_moved = False
            raise InstallError(f"{prefix} source changed during move")
        _restore_preloader_checkpoint(
            f"restore_after_{prefix}_snapshot_validation"
        )
    finally:
        os.close(reopened)
    _restore_sync_rename_parents(
        source_parent, destination_parent, prefix
    )


def _restore_validated_swap(
    parent: _DirectoryHandle,
    cleanup: _DirectoryHandle,
    live_name: str,
    staging_name: str,
    retained_live_descriptor: int,
    expected_live: _StableFileSnapshot,
    expected_staging: _StableFileSnapshot,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    _restore_revalidate_stable_file(
        parent,
        live_name,
        retained_live_descriptor,
        expected_live,
        prefix,
    )
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_parent_replacement"
    )
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_source_substitution"
    )
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_live_leaf_substitution"
    )
    _restore_preloader_checkpoint(f"restore_before_{prefix}_swap")
    _renameatx(
        parent,
        staging_name,
        parent,
        live_name,
        _RENAME_SWAP,
        f"swap official restore {prefix}",
    )
    if prefix == "active":
        recovery.active_swapped = True
    else:
        recovery.manifest_swapped = True
    _restore_preloader_checkpoint(f"restore_after_{prefix}_swap")
    displaced = -1
    try:
        _restore_preloader_checkpoint(
            f"restore_before_{prefix}_displaced_validation"
        )
        displaced, observed = _restore_read_stable_file(
            parent, staging_name, f"displaced {prefix}"
        )
        _restore_revalidate_stable_file(
            parent,
            staging_name,
            displaced,
            observed,
            f"displaced {prefix}",
        )
        live_descriptor, live_observed = _restore_read_stable_file(
            parent, live_name, f"official {prefix}"
        )
        os.close(live_descriptor)
        if observed != expected_live or live_observed != expected_staging:
            _restore_preloader_checkpoint(
                f"restore_before_{prefix}_swap_back"
            )
            _renameatx(
                parent,
                staging_name,
                parent,
                live_name,
                _RENAME_SWAP,
                f"swap back changed restore {prefix}",
            )
            if prefix == "active":
                recovery.active_swapped = False
            else:
                recovery.manifest_swapped = False
            _restore_preloader_checkpoint(
                f"restore_after_{prefix}_swap_back"
            )
            _restore_preserve_expected_if_present(
                parent,
                staging_name,
                expected_staging,
                cleanup,
                f"{prefix}_mismatch_preservation",
                recovery,
            )
            raise InstallError(f"displaced {prefix} changed")
        _restore_preloader_checkpoint(
            f"restore_after_{prefix}_displaced_validation"
        )
    finally:
        if displaced >= 0:
            os.close(displaced)
    _restore_checkpoint_fsync(
        parent,
        f"restore_before_{prefix}_staging_parent_fsync",
        f"restore_after_{prefix}_staging_parent_fsync",
        "",
    )
    _restore_checkpoint_fsync(
        parent,
        f"restore_before_{prefix}_live_parent_fsync",
        f"restore_after_{prefix}_live_parent_fsync",
        "",
    )


def _restore_move_live_directory(
    bep_in_ex: _DirectoryHandle,
    source_name: str,
    source: _DirectoryHandle,
    cleanup: _DirectoryHandle,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    _restore_verify_named_directory(bep_in_ex, source_name, source)
    if not _restore_directory_has_only_empty(source):
        raise InstallError(f"{prefix} is not empty before recovery")
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_parent_replacement"
    )
    _restore_preloader_checkpoint(
        f"restore_before_{prefix}_source_substitution"
    )
    _restore_preloader_checkpoint(f"restore_before_{prefix}_move")
    _renameatx(
        bep_in_ex,
        source_name,
        cleanup,
        source_name,
        _RENAME_EXCL,
        f"move restore {prefix} to cleanup",
    )
    if prefix == "backup_directory":
        recovery.backup_directory_moved = True
    else:
        recovery.compat_directory_moved = True
    _restore_preloader_checkpoint(f"restore_after_{prefix}_move")
    _restore_preloader_checkpoint(f"restore_before_{prefix}_reopen")
    reopened = _restore_open_child_directory(
        cleanup, source_name, f"recovered {prefix}"
    )
    _restore_preloader_checkpoint(f"restore_after_{prefix}_reopen")
    try:
        _restore_preloader_checkpoint(
            f"restore_before_{prefix}_validation"
        )
        _restore_verify_named_directory(cleanup, source_name, reopened)
        if (
            reopened.device != source.device
            or reopened.inode != source.inode
            or not _restore_directory_has_only_empty(reopened)
        ):
            _restore_require_absent(
                bep_in_ex, source_name, f"{prefix} mismatch restore"
            )
            _renameatx(
                cleanup,
                source_name,
                bep_in_ex,
                source_name,
                _RENAME_EXCL,
                f"restore unexpected recovered {prefix}",
            )
            if prefix == "backup_directory":
                recovery.backup_directory_moved = False
            else:
                recovery.compat_directory_moved = False
            _restore_verify_named_directory(
                bep_in_ex, source_name, reopened
            )
            _restore_sync_rename_parents(
                cleanup, bep_in_ex, f"{prefix}_mismatch_restore"
            )
            raise InstallError(f"{prefix} changed during recovery")
        _restore_preloader_checkpoint(
            f"restore_after_{prefix}_validation"
        )
    finally:
        os.close(reopened.fd)
    _restore_sync_rename_parents(bep_in_ex, cleanup, prefix)


def _restore_directory_has_only_empty(directory: _DirectoryHandle) -> bool:
    count = 0
    with os.scandir(directory.fd) as entries:
        for _ in entries:
            count += 1
    return count == 0


def _restore_preserve_file(
    source_parent: _DirectoryHandle,
    source_name: str,
    cleanup: _DirectoryHandle,
    prefix: str,
    recovery: _CompatRecovery,
) -> str:
    destination = f"file-{secrets.token_hex(16)}"
    if prefix == "cleanup_preservation":
        recovery.active_preserved_name = destination
    elif prefix == "displaced_preservation":
        recovery.manifest_preserved_name = destination
    _restore_preloader_checkpoint(f"restore_before_{prefix}_move")
    _renameatx(
        source_parent,
        source_name,
        cleanup,
        destination,
        _RENAME_EXCL,
        f"preserve restore {prefix}",
    )
    if prefix == "cleanup_preservation":
        recovery.active_preserved = True
    elif prefix == "displaced_preservation":
        recovery.manifest_preserved = True
    _restore_preloader_checkpoint(f"restore_after_{prefix}_move")
    _restore_sync_rename_parents(source_parent, cleanup, prefix)
    return destination


def _restore_require_absent(
    parent: _DirectoryHandle,
    name: str,
    description: str,
) -> None:
    try:
        os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise InstallError(f"{description} rollback destination is not absent")


def _restore_rollback_directory(
    bep_in_ex: _DirectoryHandle,
    name: str,
    source: _DirectoryHandle,
    cleanup: _DirectoryHandle,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    _restore_verify_named_directory(cleanup, name, source)
    _restore_verify_named_directory(recovery.run, "cleanup", cleanup)
    if not _restore_directory_has_only_empty(source):
        raise InstallError(f"rollback {prefix} source is not empty")
    _restore_require_absent(bep_in_ex, name, prefix)
    _restore_preloader_checkpoint(f"restore_rollback_before_{prefix}_restore")
    _renameatx(
        cleanup,
        name,
        bep_in_ex,
        name,
        _RENAME_EXCL,
        f"rollback restore {prefix}",
    )
    if prefix == "backup_directory":
        recovery.backup_directory_moved = False
    else:
        recovery.compat_directory_moved = False
    _restore_preloader_checkpoint(f"restore_rollback_after_{prefix}_restore")
    _restore_preloader_checkpoint(
        f"restore_rollback_before_{prefix}_validation"
    )
    _restore_verify_named_directory(bep_in_ex, name, source)
    if not _restore_directory_has_only_empty(source):
        raise InstallError(f"rollback {prefix} destination is not empty")
    _restore_preloader_checkpoint(
        f"restore_rollback_after_{prefix}_validation"
    )
    _restore_sync_rollback_parents(cleanup, bep_in_ex, prefix)


def _restore_rollback_moved_file(
    source_parent: _DirectoryHandle,
    destination_parent: _DirectoryHandle,
    destination_parent_parent: _DirectoryHandle,
    destination_parent_name: str,
    name: str,
    retained_descriptor: int,
    expected: _StableFileSnapshot,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    _restore_verify_named_directory(
        destination_parent_parent,
        destination_parent_name,
        destination_parent,
    )
    _restore_revalidate_stable_file(
        source_parent,
        name,
        retained_descriptor,
        expected,
        f"rollback {prefix}",
    )
    _restore_require_absent(destination_parent, name, prefix)
    _restore_preloader_checkpoint(f"restore_rollback_before_{prefix}_restore")
    _renameatx(
        source_parent,
        name,
        destination_parent,
        name,
        _RENAME_EXCL,
        f"rollback restore {prefix}",
    )
    if prefix == "backup":
        recovery.backup_moved = False
    else:
        recovery.provenance_moved = False
    _restore_preloader_checkpoint(f"restore_rollback_after_{prefix}_restore")
    _restore_preloader_checkpoint(
        f"restore_rollback_before_{prefix}_snapshot_validation"
    )
    _restore_revalidate_stable_file(
        destination_parent,
        name,
        retained_descriptor,
        expected,
        f"restored rollback {prefix}",
    )
    _restore_preloader_checkpoint(
        f"restore_rollback_after_{prefix}_snapshot_validation"
    )
    _restore_sync_rollback_parents(
        source_parent, destination_parent, prefix
    )


def _restore_rollback_swap(
    live_parent: _DirectoryHandle,
    source_parent: _DirectoryHandle,
    source_name: str,
    live_name: str,
    retained_patched_descriptor: int,
    patched: _StableFileSnapshot,
    official: _StableFileSnapshot,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    _restore_revalidate_stable_file(
        source_parent,
        source_name,
        retained_patched_descriptor,
        patched,
        f"rollback patched {prefix}",
    )
    official_descriptor, official_observed = _restore_read_stable_file(
        live_parent, live_name, f"rollback official {prefix}"
    )
    try:
        if official_observed != official:
            raise InstallError(f"rollback official {prefix} changed")
    finally:
        os.close(official_descriptor)
    _restore_preloader_checkpoint(f"restore_rollback_before_{prefix}_swap")
    _renameatx(
        source_parent,
        source_name,
        live_parent,
        live_name,
        _RENAME_SWAP,
        f"rollback swap patched {prefix}",
    )
    if prefix == "active":
        recovery.active_swapped = False
    else:
        recovery.manifest_swapped = False
    _restore_preloader_checkpoint(f"restore_rollback_after_{prefix}_swap")
    displaced_descriptor = -1
    try:
        _restore_preloader_checkpoint(
            f"restore_rollback_before_{prefix}_displaced_validation"
        )
        displaced_descriptor, displaced = _restore_read_stable_file(
            source_parent,
            source_name,
            f"rollback displaced official {prefix}",
        )
        if displaced != official:
            _restore_preloader_checkpoint(
                f"restore_rollback_before_{prefix}_swap_back"
            )
            _renameatx(
                source_parent,
                source_name,
                live_parent,
                live_name,
                _RENAME_SWAP,
                f"rollback swap back changed {prefix}",
            )
            if prefix == "active":
                recovery.active_swapped = True
            else:
                recovery.manifest_swapped = True
            _restore_preloader_checkpoint(
                f"restore_rollback_after_{prefix}_swap_back"
            )
            raise InstallError(f"rollback displaced official {prefix} changed")
        _restore_preloader_checkpoint(
            f"restore_rollback_after_{prefix}_displaced_validation"
        )
    finally:
        if displaced_descriptor >= 0:
            os.close(displaced_descriptor)
    _restore_checkpoint_fsync(
        source_parent,
        f"restore_rollback_before_{prefix}_staging_parent_fsync",
        f"restore_rollback_after_{prefix}_staging_parent_fsync",
        "",
    )
    _restore_checkpoint_fsync(
        live_parent,
        f"restore_rollback_before_{prefix}_live_parent_fsync",
        f"restore_rollback_after_{prefix}_live_parent_fsync",
        "",
    )


def _restore_preserve_if_present(
    source_parent: _DirectoryHandle,
    source_name: str,
    cleanup: _DirectoryHandle,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    try:
        observed = os.stat(
            source_name,
            dir_fd=source_parent.fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    if not stat.S_ISREG(observed.st_mode):
        raise InstallError(f"rollback {prefix} artifact changed type")
    _restore_preserve_file(
        source_parent, source_name, cleanup, prefix, recovery
    )


def _restore_restage_active_for_rollback(
    core: _DirectoryHandle,
    cleanup: _DirectoryHandle,
    staging_name: str,
    retained_descriptor: int,
    expected: _StableFileSnapshot,
    recovery: _CompatRecovery,
) -> None:
    _restore_verify_named_directory(recovery.run, "cleanup", cleanup)
    _restore_revalidate_stable_file(
        cleanup,
        recovery.active_preserved_name,
        retained_descriptor,
        expected,
        "rollback active restaging source",
    )
    _restore_require_absent(core, staging_name, "rollback active restaging")
    _renameatx(
        cleanup,
        recovery.active_preserved_name,
        core,
        staging_name,
        _RENAME_EXCL,
        "restage patched active for rollback",
    )
    recovery.active_preserved = False
    _restore_sync_rename_parents(
        cleanup, core, "active_rollback_restaging"
    )


def _restore_rollback_preserve_if_present(
    source_parent: _DirectoryHandle,
    source_name: str,
    cleanup: _DirectoryHandle,
    prefix: str,
    expected: _StableFileSnapshot | None,
) -> None:
    if expected is None:
        return
    try:
        descriptor, observed = _restore_read_stable_file(
            source_parent, source_name, f"rollback preserve {prefix}"
        )
    except InstallError:
        return
    try:
        if observed != expected:
            return
    finally:
        os.close(descriptor)
    destination = f"file-{secrets.token_hex(16)}"
    _restore_preloader_checkpoint(
        f"restore_rollback_before_{prefix}"
    )
    _renameatx(
        source_parent,
        source_name,
        cleanup,
        destination,
        _RENAME_EXCL,
        f"rollback preserve {prefix}",
    )
    _restore_preloader_checkpoint(
        f"restore_rollback_after_{prefix}"
    )


def _restore_preserve_expected_if_present(
    source_parent: _DirectoryHandle,
    source_name: str,
    expected: _StableFileSnapshot,
    cleanup: _DirectoryHandle,
    prefix: str,
    recovery: _CompatRecovery,
) -> None:
    try:
        descriptor, observed = _restore_read_stable_file(
            source_parent, source_name, f"contain {prefix}"
        )
    except InstallError:
        return
    try:
        if observed != expected:
            return
    finally:
        os.close(descriptor)
    _restore_preserve_file(
        source_parent, source_name, cleanup, prefix, recovery
    )


def _restore_contain_after_rollback_failure(
    preflight: tuple[
        Path,
        InstallManifest,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
    ],
    recovery: _CompatRecovery,
    active_staging_name: str,
    manifest_staging_name: str,
    active_staging: _StableFileSnapshot | None,
    manifest_staging: _StableFileSnapshot | None,
) -> None:
    if active_staging is not None and recovery.active_swapped:
        _restore_preserve_expected_if_present(
            preflight[4],
            "BepInEx.Preloader.dll",
            active_staging,
            recovery.cleanup,
            "active_failure_containment",
            recovery,
        )
    if manifest_staging is not None and recovery.manifest_swapped:
        _restore_preserve_expected_if_present(
            preflight[2],
            MANIFEST_NAME,
            manifest_staging,
            recovery.cleanup,
            "manifest_failure_containment",
            recovery,
        )
    manifest_source_expected = (
        preflight[8] if recovery.manifest_swapped else manifest_staging
    )
    if manifest_source_expected is not None:
        _restore_preserve_expected_if_present(
            preflight[2],
            manifest_staging_name,
            manifest_source_expected,
            recovery.cleanup,
            "manifest_source_failure_containment",
            recovery,
        )
    if active_staging is not None and not recovery.active_preserved:
        _restore_preserve_expected_if_present(
            preflight[4],
            active_staging_name,
            (
                preflight[10]
                if recovery.active_swapped
                else active_staging
            ),
            recovery.cleanup,
            "active_source_failure_containment",
            recovery,
        )
    os.fsync(recovery.cleanup.fd)
    os.fsync(recovery.run.fd)


def _restore_verify_patched_rollback(
    preflight: tuple[
        Path,
        InstallManifest,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
    ],
) -> None:
    _restore_revalidate_preflight_sources(
        preflight[17],
        preflight[15],
        preflight[16],
        preflight[2],
        preflight[7],
        preflight[8],
        preflight[4],
        preflight[9],
        preflight[10],
        preflight[3],
        preflight[5],
        preflight[11],
        preflight[12],
        preflight[6],
        preflight[13],
        preflight[14],
    )


def _restore_rollback(
    preflight: tuple[
        Path,
        InstallManifest,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        int,
        _StableFileSnapshot,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
        _DirectoryHandle,
    ],
    recovery: _CompatRecovery,
    active_staging_name: str,
    manifest_staging_name: str,
    active_staging: _StableFileSnapshot | None,
    manifest_staging: _StableFileSnapshot | None,
) -> None:
    if recovery.backup_directory_moved:
        _restore_rollback_directory(
            preflight[3],
            ".ssr-oracle-backup",
            preflight[5],
            recovery.cleanup,
            "backup_directory",
            recovery,
        )
    if recovery.compat_directory_moved:
        _restore_rollback_directory(
            preflight[3],
            ".ssr-oracle-compat",
            preflight[6],
            recovery.cleanup,
            "compat_directory",
            recovery,
        )
    if recovery.active_swapped:
        if recovery.active_preserved:
            _restore_restage_active_for_rollback(
                preflight[4],
                recovery.cleanup,
                active_staging_name,
                preflight[9],
                preflight[10],
                recovery,
            )
        active_source = (
            recovery.cleanup if recovery.active_preserved else preflight[4]
        )
        active_source_name = (
            recovery.active_preserved_name
            if recovery.active_preserved
            else active_staging_name
        )
        if active_staging is None:
            raise InstallError("rollback active staging snapshot is unavailable")
        _restore_rollback_swap(
            preflight[4],
            active_source,
            active_source_name,
            "BepInEx.Preloader.dll",
            preflight[9],
            preflight[10],
            active_staging,
            "active",
            recovery,
        )
    if recovery.backup_moved:
        _restore_rollback_moved_file(
            recovery.backup,
            preflight[5],
            preflight[3],
            ".ssr-oracle-backup",
            "BepInEx.Preloader.dll",
            preflight[11],
            preflight[12],
            "backup",
            recovery,
        )
    if recovery.provenance_moved:
        _restore_rollback_moved_file(
            recovery.provenance,
            preflight[6],
            preflight[3],
            ".ssr-oracle-compat",
            "preloader-provenance.json",
            preflight[13],
            preflight[14],
            "provenance",
            recovery,
        )
    if recovery.manifest_swapped:
        manifest_source = (
            recovery.cleanup if recovery.manifest_preserved else preflight[2]
        )
        manifest_source_name = (
            recovery.manifest_preserved_name
            if recovery.manifest_preserved
            else manifest_staging_name
        )
        if manifest_staging is None:
            raise InstallError("rollback manifest staging snapshot is unavailable")
        _restore_rollback_swap(
            preflight[2],
            manifest_source,
            manifest_source_name,
            MANIFEST_NAME,
            preflight[7],
            preflight[8],
            manifest_staging,
            "manifest",
            recovery,
        )
    _restore_rollback_preserve_if_present(
        preflight[4],
        active_staging_name,
        recovery.cleanup,
        "temporary_preservation",
        active_staging,
    )
    _restore_rollback_preserve_if_present(
        preflight[2],
        manifest_staging_name,
        recovery.cleanup,
        "displaced_preservation",
        manifest_staging,
    )
    _restore_sync_rollback_parents(
        preflight[2], recovery.cleanup, "cleanup_preservation"
    )
    _restore_checkpoint_fsync(
        recovery.run,
        "restore_rollback_before_recovery_directory_fsync",
        "restore_rollback_after_recovery_directory_fsync",
        "",
    )
    _restore_verify_patched_rollback(preflight)


def _restore_final_verify(
    root: _DirectoryHandle,
    bep_in_ex: _DirectoryHandle,
    core: _DirectoryHandle,
    official_manifest: InstallManifest,
    manifest_payload: bytes,
    official_payload: bytes,
    official_mode: int,
    recovery: _CompatRecovery,
) -> None:
    _restore_preloader_checkpoint(
        "restore_before_final_status_verification"
    )
    active_fd, active = _restore_read_stable_file(
        core, "BepInEx.Preloader.dll", "final official preloader"
    )
    manifest_fd = -1
    try:
        manifest_fd, manifest = _restore_read_stable_file(
            root, MANIFEST_NAME, "final official manifest"
        )
        if (
            active.payload != official_payload
            or active.mode != official_mode
            or sha256(active.payload).hexdigest()
            != EXPECTED_OFFICIAL_PRELOADER_SHA256
            or manifest.payload != manifest_payload
        ):
            raise InstallError("final official restore verification failed")
        for name in (".ssr-oracle-backup", ".ssr-oracle-compat"):
            try:
                os.stat(name, dir_fd=bep_in_ex.fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise InstallError("live compatibility directory remains")
        if (
            not _restore_directory_has_only(
                recovery.backup, "BepInEx.Preloader.dll"
            )
            or not _restore_directory_has_only(
                recovery.provenance, "preloader-provenance.json"
            )
        ):
            raise InstallError("recovery compatibility evidence is incomplete")
        if official_manifest.schema_version != 1:
            raise InstallError("final official manifest is invalid")
    finally:
        if manifest_fd >= 0:
            os.close(manifest_fd)
        os.close(active_fd)
    _restore_preloader_checkpoint(
        "restore_after_final_status_verification"
    )


def restore_preloader(
    game_root: Path,
    repo_root: Path | None = None,
) -> tuple[InstallManifest, Path]:
    """Restore the official preloader while retaining exact audit evidence."""
    preflight = _restore_manifest_and_snapshots(game_root, repo_root)
    recovery: _CompatRecovery | None = None
    active_staging_name = (
        f".ssr-oracle-restore-active-{secrets.token_hex(16)}"
    )
    manifest_staging_name = (
        f".ssr-oracle-restore-manifest-{secrets.token_hex(16)}"
    )
    active_staging: _StableFileSnapshot | None = None
    manifest_staging: _StableFileSnapshot | None = None
    try:
        official_manifest, manifest_payload = _restore_official_manifest(
            preflight[1]
        )
        recovery = _restore_allocate_recovery(preflight[2])
        _restore_preloader_checkpoint("restore_before_first_live_mutation")
        active_staging = _restore_stage_file(
            preflight[4],
            active_staging_name,
            preflight[12].payload,
            preflight[12].mode,
            "official_active",
        )
        manifest_staging = _restore_stage_file(
            preflight[2],
            manifest_staging_name,
            manifest_payload,
            preflight[8].mode,
            "official_manifest",
        )
        _restore_move_live_file(
            preflight[5],
            preflight[3],
            ".ssr-oracle-backup",
            "BepInEx.Preloader.dll",
            preflight[11],
            preflight[12],
            recovery.backup,
            "backup",
            recovery,
        )
        _restore_move_live_file(
            preflight[6],
            preflight[3],
            ".ssr-oracle-compat",
            "preloader-provenance.json",
            preflight[13],
            preflight[14],
            recovery.provenance,
            "provenance",
            recovery,
        )
        _restore_validated_swap(
            preflight[4],
            recovery.cleanup,
            "BepInEx.Preloader.dll",
            active_staging_name,
            preflight[9],
            preflight[10],
            active_staging,
            "active",
            recovery,
        )
        _restore_verify_named_directory(
            preflight[3], "core", preflight[4]
        )
        _restore_verify_named_directory(
            preflight[2], "BepInEx", preflight[3]
        )
        active_preserved_name = _restore_preserve_file(
            preflight[4],
            active_staging_name,
            recovery.cleanup,
            "cleanup_preservation",
            recovery,
        )
        _restore_preloader_checkpoint("restore_after_active_verification")
        _restore_validated_swap(
            preflight[2],
            recovery.cleanup,
            MANIFEST_NAME,
            manifest_staging_name,
            preflight[7],
            preflight[8],
            manifest_staging,
            "manifest",
            recovery,
        )
        _restore_verify_absolute_directory(preflight[0], preflight[2])
        _restore_preloader_checkpoint("restore_after_manifest_verification")
        _restore_preloader_checkpoint(
            "restore_after_backup_directory_verification"
        )
        _restore_move_live_directory(
            preflight[3],
            ".ssr-oracle-backup",
            preflight[5],
            recovery.cleanup,
            "backup_directory",
            recovery,
        )
        _restore_verify_named_directory(
            preflight[2], "BepInEx", preflight[3]
        )
        _restore_preloader_checkpoint(
            "restore_after_compat_directory_verification"
        )
        _restore_move_live_directory(
            preflight[3],
            ".ssr-oracle-compat",
            preflight[6],
            recovery.cleanup,
            "compat_directory",
            recovery,
        )
        _restore_verify_named_directory(
            preflight[2], "BepInEx", preflight[3]
        )
        _restore_preserve_file(
            preflight[2],
            manifest_staging_name,
            recovery.cleanup,
            "displaced_preservation",
            recovery,
        )
        _restore_checkpoint_fsync(
            recovery.run,
            "restore_before_recovery_directory_fsync",
            "restore_after_recovery_directory_fsync",
            "",
        )
        _restore_final_verify(
            preflight[2],
            preflight[3],
            preflight[4],
            official_manifest,
            manifest_payload,
            preflight[12].payload,
            preflight[12].mode,
            recovery,
        )
        return (
            official_manifest,
            preflight[0]
            / ".ssr-oracle-recovery"
            / recovery.run_name,
        )
    except InstallError as exc:
        if recovery is None:
            raise
        recovery_path = (
            preflight[0]
            / ".ssr-oracle-recovery"
            / recovery.run_name
        )
        try:
            _restore_rollback(
                preflight,
                recovery,
                active_staging_name,
                manifest_staging_name,
                active_staging,
                manifest_staging,
            )
        except InstallError as rollback_error:
            containment_error: InstallError | None = None
            try:
                _restore_contain_after_rollback_failure(
                    preflight,
                    recovery,
                    active_staging_name,
                    manifest_staging_name,
                    active_staging,
                    manifest_staging,
                )
            except InstallError as observed_containment_error:
                containment_error = observed_containment_error
            containment_detail = (
                ""
                if containment_error is None
                else f"; containment failed: {containment_error}"
            )
            raise InstallError(
                f"{exc}; rollback failed: {rollback_error}; "
                f"recovery retained at {recovery_path}{containment_detail}"
            ) from rollback_error
        raise InstallError(
            f"{exc}; rollback succeeded; recovery retained at {recovery_path}"
        ) from exc
    finally:
        if recovery is not None:
            _restore_close_recovery(recovery)
        _restore_close_preflight(preflight)


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
            errors.append(f"cannot preserve created live directory {name}: {exc}")
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
        "restore-preloader",
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
        if name == "restore-preloader":
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
        elif args.command == "restore-preloader":
            manifest, recovery = restore_preloader(
                args.game_root,
                repo_root=args.repo_root,
            )
            output = {
                "manifest": _manifest_to_dict(manifest),
                "recovery": str(recovery),
            }
            exit_code = 0
        elif args.command == "status":
            status = status_install(args.game_root)
            output = _status_to_dict(status)
            exit_code = 0 if status.healthy else 1
        else:
            output = {"recovery": str(recover_install(args.game_root))}
            exit_code = 0
    except InstallError as exc:
        if args.command == "restore-preloader":
            print(str(exc), file=sys.stderr)
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True))
    return exit_code
