"""Safe installation and recovery helpers for the executable SSR oracle."""

from __future__ import annotations

import argparse
import json
import os
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
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, target)
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
    for name in ("inspect", "install", "deploy", "status", "recover"):
        command = sub.add_parser(name)
        command.add_argument("--game-root", type=Path, required=True)
        if name == "install":
            command.add_argument("--archive", type=Path, required=True)
        if name == "deploy":
            command.add_argument("--plugin", type=Path, required=True)
            command.add_argument("--config", type=Path, required=True)
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
