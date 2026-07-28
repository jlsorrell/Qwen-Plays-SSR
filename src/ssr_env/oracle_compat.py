"""Strict trust and provenance primitives for the BepInEx compatibility build."""

from __future__ import annotations

import hashlib
import json
import re
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
