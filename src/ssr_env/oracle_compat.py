"""Strict trust and provenance primitives for the BepInEx compatibility build."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class CompatError(ValueError):
    """Raised when compatibility inputs fail validation."""


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
class SourceCheckout:
    root: Path
    source_commit: str
    harmony_submodule_commit: str


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


_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LOWER_SHA512 = re.compile(r"[0-9a-f]{128}\Z")
_LOWER_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_SOURCE_COMMIT = "57f1fb859bd4d0264cd2a59074d0e96c6a492a33"
_HARMONY_SUBMODULE_COMMIT = "d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa"
_HARMONY_SUBMODULE_PATH = "submodules/BepInEx.Harmony"
_PLATFORM_RELATIVE = "BepInEx.Preloader/Platform.cs"
_OLD_PLATFORM_PROBE = "/System/Library/AccessibilityBundles"
_NEW_PLATFORM_PROBE = "/System/Library/CoreServices"
_TRUST_KEYS = {
    "schema_version",
    "patch_sha256",
    "toolchain_sha256",
    "dependencies_sha256",
    "nuget_lock_tree_sha256",
}
_PROVENANCE_KEYS = {
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
_TOOLCHAIN_KEYS = {
    "schema_version",
    "source_commit",
    "harmony_submodule_commit",
    "dotnet_sdk_version",
    "dotnet_sdk_archive_sha512",
    "project",
    "framework",
    "official_preloader_sha256",
    "build_properties",
}
_NUGET_LOCK_RELATIVES = (
    "oracle/compat/nuget-lock/BepInEx.Preloader/packages.lock.json",
    "oracle/compat/nuget-lock/BepInEx/packages.lock.json",
    "oracle/compat/nuget-lock/submodules/BepInEx.Harmony/"
    "BepInEx.Harmony/packages.lock.json",
    "oracle/compat/nuget-lock/submodules/BepInEx.Harmony/"
    "HarmonyX2Interop/packages.lock.json",
    "oracle/compat/nuget-lock/submodules/BepInEx.Harmony/"
    "HarmonyXInterop/packages.lock.json",
)


def canonical_json(value: object) -> bytes:
    """Encode JSON deterministically as sorted, indented UTF-8 plus newline."""
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CompatError(f"value is not canonical JSON: {exc}") from exc
    return (encoded + "\n").encode("utf-8")


def _exact_mapping(value: object, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise CompatError(f"{label} schema has unknown or missing keys")
    if not all(isinstance(key, str) for key in value):
        raise CompatError(f"{label} schema keys must be strings")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CompatError(f"{label} must be an integer")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value.encode("utf-8")) > 4096:
        raise CompatError(f"{label} must be a string of at most 4096 bytes")
    return value


def _match(value: object, pattern: re.Pattern[str], label: str) -> str:
    text = _string(value, label)
    if pattern.fullmatch(text) is None:
        raise CompatError(f"{label} has invalid format")
    return text


def _relative_path(value: object, label: str) -> str:
    text = _string(value, label)
    path = PurePosixPath(text)
    if (
        not text
        or path.is_absolute()
        or "\\" in text
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CompatError(f"{label} must be a safe relative POSIX path")
    return text


def _decode_canonical(path: Path, label: str) -> object:
    try:
        raw = path.read_bytes()
        decoded = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatError(f"{label} JSON cannot be read: {exc}") from exc
    if raw != canonical_json(decoded):
        raise CompatError(f"{label} JSON is not canonical")
    return decoded


def parse_trust_data(data: object) -> CompatTrust:
    values = _exact_mapping(data, _TRUST_KEYS, "trust")
    version = _integer(values["schema_version"], "trust schema_version")
    if version != 1:
        raise CompatError("trust schema_version must be 1")
    try:
        return CompatTrust(
            schema_version=version,
            patch_sha256=_match(values["patch_sha256"], _LOWER_SHA256, "patch hash"),
            toolchain_sha256=_match(
                values["toolchain_sha256"], _LOWER_SHA256, "toolchain hash"
            ),
            dependencies_sha256=_match(
                values["dependencies_sha256"], _LOWER_SHA256, "dependencies hash"
            ),
            nuget_lock_tree_sha256=_match(
                values["nuget_lock_tree_sha256"], _LOWER_SHA256, "lock tree hash"
            ),
        )
    except CompatError as exc:
        raise CompatError(f"trust schema is invalid: {exc}") from exc


def _git_head_blob(repo_root: Path, relative: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CompatError(f"{relative} is not a tracked HEAD blob") from exc
    return result.stdout


def _require_head_blob(repo_root: Path, relative: str) -> bytes:
    expected = _git_head_blob(repo_root, relative)
    try:
        actual = (repo_root / relative).read_bytes()
    except OSError as exc:
        raise CompatError(f"{relative} does not match its HEAD blob") from exc
    if actual != expected:
        raise CompatError(f"{relative} does not match its HEAD blob")
    return actual


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lock_paths(repo_root: Path) -> list[Path]:
    return [repo_root / relative for relative in sorted(_NUGET_LOCK_RELATIVES)]


def nuget_lock_tree_sha256(repo_root: Path, *, require_head: bool) -> str:
    digest = hashlib.sha256()
    paths = _lock_paths(repo_root)
    if not paths:
        raise CompatError("NuGet lock tree is empty")
    for path in paths:
        relative = path.relative_to(repo_root).as_posix()
        data = _require_head_blob(repo_root, relative) if require_head else path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(data).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_trust(repo_root: Path) -> CompatTrust:
    """Load trust only after every named input matches its committed HEAD blob."""
    trust_relative = "oracle/compat/trust.json"
    trust_bytes = _require_head_blob(repo_root, trust_relative)
    try:
        decoded = json.loads(trust_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatError(f"trust JSON cannot be read: {exc}") from exc
    if trust_bytes != canonical_json(decoded):
        raise CompatError("trust JSON is not canonical")
    trust = parse_trust_data(decoded)

    patch = _require_head_blob(
        repo_root, "oracle/compat/bepinex-macos15-platform.patch"
    )
    toolchain = _require_head_blob(repo_root, "oracle/compat/toolchain.json")
    dependencies = _require_head_blob(
        repo_root, "oracle/compat/dependencies.json"
    )
    observed = (
        _sha256(patch),
        _sha256(toolchain),
        _sha256(dependencies),
        nuget_lock_tree_sha256(repo_root, require_head=True),
    )
    expected = (
        trust.patch_sha256,
        trust.toolchain_sha256,
        trust.dependencies_sha256,
        trust.nuget_lock_tree_sha256,
    )
    if observed != expected:
        raise CompatError("trust hashes do not match committed HEAD blobs")
    return trust


def parse_toolchain_data(data: object) -> ToolchainLock:
    values = _exact_mapping(data, _TOOLCHAIN_KEYS, "toolchain")
    version = _integer(values["schema_version"], "toolchain schema_version")
    properties = values["build_properties"]
    if not isinstance(properties, dict) or not properties:
        raise CompatError("toolchain build_properties must be a nonempty object")
    pairs: list[tuple[str, str]] = []
    for key, value in sorted(properties.items()):
        pairs.append(
            (
                _string(key, "build property name"),
                _string(value, "build property value"),
            )
        )
    if version != 1:
        raise CompatError("toolchain schema_version must be 1")
    return ToolchainLock(
        schema_version=version,
        source_commit=_match(values["source_commit"], _LOWER_COMMIT, "source commit"),
        harmony_submodule_commit=_match(
            values["harmony_submodule_commit"], _LOWER_COMMIT, "Harmony commit"
        ),
        dotnet_sdk_version=_string(values["dotnet_sdk_version"], "SDK version"),
        dotnet_sdk_archive_sha512=_match(
            values["dotnet_sdk_archive_sha512"], _LOWER_SHA512, "SDK archive hash"
        ),
        project=_relative_path(values["project"], "project"),
        framework=_string(values["framework"], "framework"),
        official_preloader_sha256=_match(
            values["official_preloader_sha256"],
            _LOWER_SHA256,
            "official preloader hash",
        ),
        build_properties=tuple(pairs),
    )


def load_toolchain(path: Path) -> ToolchainLock:
    return parse_toolchain_data(_decode_canonical(path, "toolchain"))


def _git_text(root: Path, arguments: list[str], label: str) -> str:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CompatError(f"{label} cannot be inspected") from exc


def _tracked_relatives(root: Path) -> tuple[str, ...]:
    try:
        output = subprocess.run(
            ["git", "ls-files", "-z", "--recurse-submodules"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        decoded = output.decode("utf-8")
    except (OSError, UnicodeDecodeError, subprocess.CalledProcessError) as exc:
        raise CompatError("source checkout tracked files cannot be inspected") from exc
    relatives = tuple(item for item in decoded.split("\0") if item)
    if not relatives:
        raise CompatError("source checkout has no tracked files")
    for relative in relatives:
        _relative_path(relative, "source tracked file")
    return relatives


def _has_symlink_component(root: Path, relative: str) -> bool:
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def validate_source_checkout(source: Path, trust: CompatTrust) -> SourceCheckout:
    """Validate the exact clean recursive BepInEx checkout."""
    if not isinstance(trust, CompatTrust):
        raise CompatError("source trust is invalid")
    source_path = Path(source)
    if source_path.is_symlink():
        raise CompatError("source checkout root must not be symlinked")
    try:
        root = source_path.resolve(strict=True)
    except OSError as exc:
        raise CompatError("source checkout root cannot be resolved") from exc
    if not root.is_dir():
        raise CompatError("source checkout root must be a directory")

    source_commit = _git_text(root, ["rev-parse", "HEAD"], "source commit").strip()
    if source_commit != _SOURCE_COMMIT:
        raise CompatError("source commit does not match the pinned commit")

    submodule_lines = _git_text(
        root, ["submodule", "status", "--recursive"], "submodule commit"
    ).splitlines()
    if len(submodule_lines) != 1:
        raise CompatError("submodule commit does not match the pinned recursive tree")
    status = submodule_lines[0]
    fields = status[1:].split()
    if (
        not status.startswith(" ")
        or len(fields) < 2
        or fields[0] != _HARMONY_SUBMODULE_COMMIT
        or fields[1] != _HARMONY_SUBMODULE_PATH
    ):
        raise CompatError("submodule commit does not match the pinned recursive tree")

    dirty = _git_text(
        root,
        ["status", "--porcelain=v1", "--untracked-files=all"],
        "clean checkout",
    )
    if dirty != "":
        raise CompatError("source must be a clean checkout")
    if _has_symlink_component(root, _PLATFORM_RELATIVE):
        raise CompatError("source patch target must not be symlinked")

    return SourceCheckout(
        root=root,
        source_commit=source_commit,
        harmony_submodule_commit=_HARMONY_SUBMODULE_COMMIT,
    )


def _copy_tracked_source(source: Path, destination: Path) -> dict[str, str]:
    before: dict[str, str] = {}
    for relative in _tracked_relatives(source):
        if _has_symlink_component(source, relative):
            raise CompatError(f"source tracked file is symlinked: {relative}")
        source_file = source / relative
        if not source_file.is_file():
            raise CompatError(f"source tracked file cannot be read: {relative}")
        data = source_file.read_bytes()
        before[relative] = _sha256(data)
        destination_file = destination / relative
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination_file)
        if _sha256(destination_file.read_bytes()) != before[relative]:
            raise CompatError(f"source copy hash mismatch: {relative}")
    return before


def _compat_patch(trust: CompatTrust) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    relative = "oracle/compat/bepinex-macos15-platform.patch"
    patch = repo_root / relative
    if patch.is_symlink():
        raise CompatError("compatibility patch must not be symlinked")
    data = _require_head_blob(repo_root, relative)
    if _sha256(data) != trust.patch_sha256:
        raise CompatError("compatibility patch does not match trust")
    try:
        return patch.resolve(strict=True)
    except OSError as exc:
        raise CompatError("compatibility patch cannot be resolved") from exc


def prepare_source(
    source: SourceCheckout,
    destination: Path,
    trust: CompatTrust,
) -> Path:
    """Copy and patch a validated checkout without mutating its Git tree."""
    if not isinstance(source, SourceCheckout) or not isinstance(trust, CompatTrust):
        raise CompatError("source preparation inputs are invalid")
    if source.root.is_symlink() or _has_symlink_component(
        source.root, _PLATFORM_RELATIVE
    ):
        raise CompatError("source patch target must not be symlinked")
    destination_path = Path(destination)
    if destination_path.exists() or destination_path.is_symlink():
        raise CompatError("prepared source destination must be absent")
    destination_root = destination_path.resolve(strict=False)
    if destination_root.is_relative_to(source.root):
        raise CompatError("prepared source destination must be outside source checkout")
    destination_root.mkdir(parents=True)

    platform_source = source.root / _PLATFORM_RELATIVE
    try:
        preimage = platform_source.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise CompatError("patch preimage cannot be read") from exc
    if (
        preimage.count(_OLD_PLATFORM_PROBE) != 1
        or preimage.count(_NEW_PLATFORM_PROBE) != 0
    ):
        raise CompatError("patch preimage does not match the pinned source")

    before = _copy_tracked_source(source.root, destination_root)
    patch = _compat_patch(trust)
    patch_text = patch.read_text(encoding="utf-8")
    if not any(
        line.startswith("+") and "current = Platform.MacOS;" in line
        for line in patch_text.splitlines()
    ):
        raise CompatError("patch preimage does not contain the macOS platform hunk")
    apply_environment = os.environ.copy()
    apply_environment["GIT_CEILING_DIRECTORIES"] = str(destination_root.parent)
    try:
        subprocess.run(
            ["git", "apply", "--check", str(patch)],
            cwd=destination_root,
            check=True,
            text=True,
            capture_output=True,
            env=apply_environment,
        )
        subprocess.run(
            ["git", "apply", str(patch)],
            cwd=destination_root,
            check=True,
            text=True,
            capture_output=True,
            env=apply_environment,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CompatError(
            "patch preimage does not accept the compatibility patch"
        ) from exc

    after = {
        relative: _sha256((destination_root / relative).read_bytes())
        for relative in before
    }
    changed = sorted(
        relative for relative in before if before[relative] != after[relative]
    )
    if changed != [_PLATFORM_RELATIVE]:
        raise CompatError("prepared source changed files outside the patch target")
    platform = (destination_root / _PLATFORM_RELATIVE).read_text(
        encoding="utf-8-sig"
    )
    if (
        platform.count(_OLD_PLATFORM_PROBE) != 0
        or platform.count(_NEW_PLATFORM_PROBE) != 1
        or "current = Platform.MacOS;" not in platform
    ):
        raise CompatError("prepared source does not contain the exact macOS probe")
    return destination_root


def source_differences(source: Path, prepared: Path) -> list[str]:
    """List content differences between tracked source files and a prepared tree."""
    source_root = Path(source).resolve(strict=True)
    prepared_root = Path(prepared).resolve(strict=True)
    tracked = set(_tracked_relatives(source_root))
    prepared_files = {
        path.relative_to(prepared_root).as_posix()
        for path in prepared_root.rglob("*")
        if path.is_file()
    }
    changed: list[str] = []
    for relative in sorted(tracked | prepared_files):
        source_file = source_root / relative
        prepared_file = prepared_root / relative
        if (
            relative not in tracked
            or relative not in prepared_files
            or _sha256(source_file.read_bytes()) != _sha256(prepared_file.read_bytes())
        ):
            changed.append(relative)
    return changed


def load_provenance(path: Path, trust: CompatTrust) -> BuildProvenance:
    try:
        values = _exact_mapping(
            _decode_canonical(path, "provenance"), _PROVENANCE_KEYS, "provenance"
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
        return provenance
    except CompatError as exc:
        if "provenance" in str(exc):
            raise
        raise CompatError(f"provenance is invalid: {exc}") from exc
