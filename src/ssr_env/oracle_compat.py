"""Strict trust and provenance primitives for the BepInEx compatibility build."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass
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


_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LOWER_SHA512 = re.compile(r"[0-9a-f]{128}\Z")
_LOWER_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_SOURCE_COMMIT = "57f1fb859bd4d0264cd2a59074d0e96c6a492a33"
_HARMONY_SUBMODULE_COMMIT = "d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa"
_HARMONY_SUBMODULE_PATH = "submodules/BepInEx.Harmony"
_HARMONY_SUBMODULE_STATUS = (
    f" {_HARMONY_SUBMODULE_COMMIT} {_HARMONY_SUBMODULE_PATH} (d4cdcb4)"
)
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
    if status != _HARMONY_SUBMODULE_STATUS:
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
    try:
        resolved_source_root = source.root.resolve(strict=True)
    except OSError as exc:
        raise CompatError("source checkout root cannot be resolved") from exc
    if source.root != resolved_source_root:
        raise CompatError("source checkout root does not match its validated path")
    if source.source_commit != _SOURCE_COMMIT:
        raise CompatError("source commit does not match the validated checkout")
    if source.harmony_submodule_commit != _HARMONY_SUBMODULE_COMMIT:
        raise CompatError("submodule commit does not match the validated checkout")
    destination_path = Path(destination)
    if destination_path.exists() or destination_path.is_symlink():
        raise CompatError("prepared source destination must be absent")
    destination_root = destination_path.resolve(strict=False)
    if destination_root.is_relative_to(source.root):
        raise CompatError("prepared source destination must be outside source checkout")

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

    patch = _compat_patch(trust)
    patch_text = patch.read_text(encoding="utf-8")
    if not any(
        line.startswith("+") and "current = Platform.MacOS;" in line
        for line in patch_text.splitlines()
    ):
        raise CompatError("patch preimage does not contain the macOS platform hunk")
    try:
        subprocess.run(
            ["git", "apply", "--check", str(patch)],
            cwd=source.root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CompatError(
            "patch preimage does not accept the compatibility patch"
        ) from exc

    revalidated = validate_source_checkout(source.root, trust)
    if revalidated != source:
        raise CompatError("source checkout identity changed after validation")

    destination_root.mkdir(parents=True)
    before = _copy_tracked_source(source.root, destination_root)
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


_ASSEMBLY_METADATA_KEYS = {
    "assembly_name",
    "assembly_version",
    "metadata_version",
    "references",
    "target_framework",
}
_EXPECTED_BUILD_PROPERTIES = {
    "Configuration": "Release",
    "ContinuousIntegrationBuild": "true",
    "Deterministic": "true",
    "PathMap": "{source_root}=/_/src",
}
_BUILD_TIMEOUT_SECONDS = 300


def inspect_assembly(path: Path, inspector: Path) -> AssemblyMetadata:
    """Inspect a managed PE through the non-loading metadata executable."""
    assembly = Path(path).resolve(strict=True)
    executable = Path(inspector).resolve(strict=True)
    environment = os.environ.copy()
    local_runtime = (
        Path(__file__).resolve().parents[2]
        / "data/oracle/compat/dotnet-8.0.419"
    )
    if local_runtime.is_dir():
        environment["DOTNET_ROOT"] = str(local_runtime)
    try:
        result = subprocess.run(
            [str(executable), str(assembly)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=_BUILD_TIMEOUT_SECONDS,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise CompatError("assembly inspection timed out") from exc
    except OSError as exc:
        raise CompatError("assembly inspector cannot be executed") from exc
    if result.returncode != 0:
        raise CompatError("assembly metadata is invalid")
    try:
        decoded = json.loads(result.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompatError("assembly inspector emitted invalid JSON") from exc
    if result.stdout != canonical_json(decoded):
        raise CompatError("assembly inspector JSON is not canonical")
    values = _exact_mapping(decoded, _ASSEMBLY_METADATA_KEYS, "assembly metadata")
    references = values["references"]
    if not isinstance(references, dict):
        raise CompatError("assembly metadata references must be an object")
    pairs: list[tuple[str, str]] = []
    for name, version in sorted(references.items()):
        pairs.append(
            (
                _string(name, "assembly reference name"),
                _string(version, "assembly reference version"),
            )
        )
    return AssemblyMetadata(
        name=_string(values["assembly_name"], "assembly name"),
        version=_string(values["assembly_version"], "assembly version"),
        metadata_version=_string(values["metadata_version"], "metadata version"),
        target_framework=_string(values["target_framework"], "target framework"),
        references=tuple(pairs),
    )


def _load_package_pins(path: Path) -> tuple[PackagePin, ...]:
    decoded = _decode_canonical(path, "dependencies")
    values = _exact_mapping(
        decoded, {"packages", "schema_version"}, "dependencies"
    )
    if _integer(values["schema_version"], "dependencies schema_version") != 1:
        raise CompatError("dependencies schema_version must be 1")
    records = values["packages"]
    if not isinstance(records, list) or len(records) != 10:
        raise CompatError("dependencies must contain exactly ten packages")
    pins: list[PackagePin] = []
    seen: set[str] = set()
    for record in records:
        item = _exact_mapping(
            record,
            {
                "content_hash",
                "filename",
                "package_id",
                "sha256",
                "source_index",
                "version",
            },
            "dependency",
        )
        filename = _relative_path(item["filename"], "package filename")
        if "/" in filename or not filename.endswith(".nupkg") or filename in seen:
            raise CompatError("dependency package filename is invalid or duplicate")
        seen.add(filename)
        pins.append(
            PackagePin(
                package_id=_string(item["package_id"], "package id"),
                version=_string(item["version"], "package version"),
                source_index=_string(item["source_index"], "package source"),
                filename=filename,
                sha256=_match(item["sha256"], _LOWER_SHA256, "package hash"),
                content_hash=_string(item["content_hash"], "package content hash"),
            )
        )
    return tuple(pins)


def _validate_feed(feed_dir: Path, pins: tuple[PackagePin, ...]) -> Path:
    feed = Path(feed_dir)
    if feed.is_symlink():
        raise CompatError("local package feed must not be symlinked")
    try:
        root = feed.resolve(strict=True)
    except OSError as exc:
        raise CompatError("local package feed cannot be resolved") from exc
    if not root.is_dir():
        raise CompatError("local package feed must be a directory")
    observed = {
        item.name for item in root.iterdir() if item.is_file() and item.suffix == ".nupkg"
    }
    expected = {pin.filename for pin in pins}
    if observed != expected:
        raise CompatError("local package feed must contain exactly ten locked packages")
    for pin in pins:
        package = root / pin.filename
        if package.is_symlink() or _sha256(package.read_bytes()) != pin.sha256:
            raise CompatError(f"local package hash mismatch: {pin.filename}")
    return root


def _execute_build_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=_BUILD_TIMEOUT_SECONDS,
    )


def _log_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _run_build_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
) -> subprocess.CompletedProcess[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = _execute_build_command(command, cwd=cwd, env=env)
    except subprocess.TimeoutExpired as exc:
        log_path.write_text(
            "$ " + " ".join(command) + "\n"
            + _log_text(exc.stdout or exc.output)
            + _log_text(exc.stderr),
            encoding="utf-8",
        )
        raise CompatError("BepInEx build timed out") from exc
    except OSError as exc:
        log_path.write_text(
            "$ " + " ".join(command) + f"\nprocess error: {exc}\n",
            encoding="utf-8",
        )
        raise CompatError("BepInEx build process could not start") from exc
    log_path.write_text(
        "$ " + " ".join(command) + "\n"
        + _log_text(result.stdout)
        + _log_text(result.stderr),
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise CompatError("BepInEx build failed")
    return result


def _nuget_config(feed: Path) -> bytes:
    source = html.escape(str(feed), quote=True)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<configuration>\n"
        "  <packageSources>\n"
        "    <clear />\n"
        f'    <add key="locked-local-feed" value="{source}" />\n'
        "  </packageSources>\n"
        "</configuration>\n"
    ).encode("utf-8")


def _copy_lock_files(repo_root: Path, prepared: Path) -> None:
    prefix = "oracle/compat/nuget-lock/"
    for relative in _NUGET_LOCK_RELATIVES:
        if not relative.startswith(prefix):
            raise CompatError("NuGet lock path is invalid")
        destination = prepared / relative.removeprefix(prefix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_bytes = _require_head_blob(repo_root, relative)
        destination.write_bytes(source_bytes)
        if destination.read_bytes() != source_bytes:
            raise CompatError("NuGet lock copy is not byte-identical")


def _build_environment(root: Path, packages: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "DOTNET_CLI_HOME": str(root / "dotnet-home"),
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_NOLOGO": "1",
            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
            "NUGET_PACKAGES": str(packages),
        }
    )
    return environment


def _build_inspector(
    sdk: Path,
    feed: Path,
    repo_root: Path,
    work: Path,
) -> Path:
    root = work / "inspector"
    packages = root / "packages"
    output = root / "publish"
    root.mkdir(parents=True)
    config = root / "NuGet.config"
    config.write_bytes(_nuget_config(feed))
    project = repo_root / "oracle/compat/inspector/SsrOracle.CompatInspector.csproj"
    environment = _build_environment(root, packages)
    intermediate = root / "obj"
    build_output = root / "bin"
    isolated_properties = [
        f"-p:BaseIntermediateOutputPath={intermediate}/",
        f"-p:MSBuildProjectExtensionsPath={intermediate}/",
        f"-p:BaseOutputPath={build_output}/",
    ]
    _run_build_command(
        [
            str(sdk),
            "restore",
            str(project),
            "--no-cache",
            "--packages",
            str(packages),
            "--configfile",
            str(config),
            *isolated_properties,
        ],
        cwd=root,
        env=environment,
        log_path=root / "restore.log",
    )
    _run_build_command(
        [
            str(sdk),
            "publish",
            str(project),
            "--configuration",
            "Release",
            "--no-restore",
            "--disable-build-servers",
            "--output",
            str(output),
            *isolated_properties,
        ],
        cwd=root,
        env=environment,
        log_path=root / "publish.log",
    )
    return output / "SsrOracle.CompatInspector"


def _build_once(
    source: SourceCheckout,
    trust: CompatTrust,
    toolchain: ToolchainLock,
    sdk: Path,
    feed: Path,
    repo_root: Path,
    root: Path,
) -> Path:
    prepared = prepare_source(source, root / "source", trust)
    _copy_lock_files(repo_root, prepared)
    packages = root / "packages"
    publish = root / "publish"
    config = root / "NuGet.config"
    config.write_bytes(_nuget_config(feed))
    environment = _build_environment(root, packages)
    project = prepared / toolchain.project
    _run_build_command(
        [
            str(sdk),
            "restore",
            str(project),
            "--locked-mode",
            "--no-cache",
            "--packages",
            str(packages),
            "--configfile",
            str(config),
            "-p:RestoreBuildInParallel=false",
        ],
        cwd=prepared,
        env=environment,
        log_path=root / "restore.log",
    )
    properties = dict(toolchain.build_properties)
    path_map = properties["PathMap"].replace("{source_root}", str(prepared))
    _run_build_command(
        [
            str(sdk),
            "publish",
            str(project),
            "--configuration",
            properties["Configuration"],
            "--framework",
            toolchain.framework,
            "--no-restore",
            "--disable-build-servers",
            "--output",
            str(publish),
            f"-p:Deterministic={properties['Deterministic']}",
            f"-p:ContinuousIntegrationBuild={properties['ContinuousIntegrationBuild']}",
            f"-p:PathMap={path_map}",
            "-p:BuildInParallel=false",
        ],
        cwd=prepared,
        env=environment,
        log_path=root / "publish.log",
    )
    candidates = list(publish.rglob("BepInEx.Preloader.dll"))
    if len(candidates) != 1 or candidates[0].parent != publish:
        raise CompatError("build did not produce exactly one preloader DLL")
    return candidates[0]


def _validate_legacy_metadata(
    metadata: AssemblyMetadata,
    toolchain: ToolchainLock,
) -> None:
    expected = (
        "BepInEx.Preloader",
        "5.4.23.5",
        ".NETFramework,Version=v3.5",
    )
    actual = (metadata.name, metadata.version, metadata.target_framework)
    references = dict(metadata.references)
    if (
        actual != expected
        or toolchain.framework != "net35"
        or metadata.metadata_version != "v2.0.50727"
        or references.get("mscorlib") != "2.0.0.0"
    ):
        raise CompatError("built preloader does not have exact legacy metadata")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_durable(path: Path, data: bytes) -> None:
    with path.open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())


def _publish_result(
    output_dir: Path,
    work: Path,
    dll_bytes: bytes,
    provenance: BuildProvenance,
) -> tuple[Path, Path]:
    digest = provenance.patched_preloader_sha256
    result = output_dir / digest
    dll_name = "BepInEx.Preloader.dll"
    provenance_name = "provenance.json"
    provenance_bytes = canonical_json(asdict(provenance))
    if result.exists():
        if (
            (result / dll_name).read_bytes() != dll_bytes
            or (result / provenance_name).read_bytes() != provenance_bytes
        ):
            raise CompatError("refusing different existing build bytes")
    else:
        staging = work / "publish-result"
        staging.mkdir()
        _write_durable(staging / dll_name, dll_bytes)
        _write_durable(staging / provenance_name, provenance_bytes)
        _fsync_directory(staging)
        os.replace(staging, result)
        _fsync_directory(output_dir)

    current_bytes = canonical_json(
        {
            "dll": f"{digest}/{dll_name}",
            "patched_sha256": digest,
            "provenance": f"{digest}/{provenance_name}",
        }
    )
    current_temp = output_dir / f".current.{uuid.uuid4().hex}.json"
    _write_durable(current_temp, current_bytes)
    os.replace(current_temp, output_dir / "current.json")
    _fsync_directory(output_dir)
    return result / dll_name, result / provenance_name


def build_compat_preloader(
    source: Path,
    sdk: Path,
    feed_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> BuildResult:
    """Build, compare, inspect, and atomically publish the patched preloader."""
    repository = Path(repo_root).resolve(strict=True)
    expected_repository = Path(__file__).resolve().parents[2]
    if repository != expected_repository:
        raise CompatError("compatibility repository root is invalid")
    trust = load_trust(repository)
    toolchain = load_toolchain(repository / "oracle/compat/toolchain.json")
    if (
        toolchain.source_commit != _SOURCE_COMMIT
        or toolchain.harmony_submodule_commit != _HARMONY_SUBMODULE_COMMIT
        or dict(toolchain.build_properties) != _EXPECTED_BUILD_PROPERTIES
        or toolchain.framework != "net35"
    ):
        raise CompatError("toolchain does not describe the exact build")
    pins = _load_package_pins(repository / "oracle/compat/dependencies.json")
    feed = _validate_feed(feed_dir, pins)
    checkout = validate_source_checkout(source, trust)

    sdk_path = Path(sdk).resolve(strict=True)
    output = Path(output_dir).resolve(strict=False)
    output.mkdir(parents=True, exist_ok=True)
    work = output / ".work" / uuid.uuid4().hex
    work.mkdir(parents=True)
    environment = _build_environment(work / "sdk-check", work / "sdk-packages")
    version_result = _run_build_command(
        [str(sdk_path), "--version"],
        cwd=work,
        env=environment,
        log_path=work / "sdk-version.log",
    )
    if _log_text(version_result.stdout).strip() != toolchain.dotnet_sdk_version:
        raise CompatError("SDK version does not match toolchain")

    inspector = _build_inspector(sdk_path, feed, repository, work)
    first = _build_once(
        checkout, trust, toolchain, sdk_path, feed, repository, work / "build-a"
    )
    second = _build_once(
        checkout, trust, toolchain, sdk_path, feed, repository, work / "build-b"
    )
    first_bytes = first.read_bytes()
    second_bytes = second.read_bytes()
    if first_bytes != second_bytes:
        raise CompatError("two fresh builds are not byte-identical")

    metadata = inspect_assembly(first, inspector)
    _validate_legacy_metadata(metadata, toolchain)
    patched_hash = _sha256(first_bytes)
    provenance = BuildProvenance(
        schema_version=1,
        source_commit=toolchain.source_commit,
        patch_sha256=trust.patch_sha256,
        toolchain_lock_sha256=trust.toolchain_sha256,
        dotnet_sdk_version=toolchain.dotnet_sdk_version,
        dependency_lock_sha256=trust.dependencies_sha256,
        build_target=toolchain.project,
        official_preloader_sha256=toolchain.official_preloader_sha256,
        patched_preloader_sha256=patched_hash,
    )
    dll, provenance_path = _publish_result(
        output, work, first_bytes, provenance
    )
    return BuildResult(
        dll=dll,
        provenance=provenance_path,
        patched_sha256=patched_hash,
        metadata=metadata,
        provenance_data=provenance,
    )
