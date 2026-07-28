from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ssr_env.oracle_compat import (
    CompatError,
    canonical_json,
    load_provenance,
    load_trust,
    parse_trust_data,
)


COMPAT_INPUTS = (
    "bepinex-macos15-platform.patch",
    "toolchain.json",
    "nuget-lock/BepInEx.Preloader/packages.lock.json",
    "nuget-lock/BepInEx/packages.lock.json",
    "nuget-lock/submodules/BepInEx.Harmony/BepInEx.Harmony/packages.lock.json",
    "nuget-lock/submodules/BepInEx.Harmony/HarmonyX2Interop/packages.lock.json",
    "nuget-lock/submodules/BepInEx.Harmony/HarmonyXInterop/packages.lock.json",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lock_tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    paths = (root / "oracle/compat/nuget-lock").rglob("*.json")
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(_sha256(path.read_bytes()).encode())
        digest.update(b"\n")
    return digest.hexdigest()


@pytest.fixture
def committed_compat_repo(tmp_path: Path) -> Path:
    source_root = Path(__file__).resolve().parents[1]
    for relative in COMPAT_INPUTS:
        destination = tmp_path / "oracle/compat" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / "oracle/compat" / relative, destination)

    dependencies = canonical_json({"packages": [], "schema_version": 1})
    (tmp_path / "oracle/compat/dependencies.json").write_bytes(dependencies)
    trust = {
        "schema_version": 1,
        "patch_sha256": _sha256(
            (tmp_path / "oracle/compat/bepinex-macos15-platform.patch").read_bytes()
        ),
        "toolchain_sha256": _sha256(
            (tmp_path / "oracle/compat/toolchain.json").read_bytes()
        ),
        "dependencies_sha256": _sha256(dependencies),
        "nuget_lock_tree_sha256": _lock_tree_sha256(tmp_path),
    }
    (tmp_path / "oracle/compat/trust.json").write_bytes(canonical_json(trust))
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "oracle/compat"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


@pytest.fixture
def valid_provenance(
    committed_compat_repo: Path,
    tmp_path: Path,
) -> Path:
    trust = load_trust(committed_compat_repo)
    data = {
        "schema_version": 1,
        "source_commit": "57f1fb859bd4d0264cd2a59074d0e96c6a492a33",
        "patch_sha256": trust.patch_sha256,
        "toolchain_lock_sha256": trust.toolchain_sha256,
        "dotnet_sdk_version": "8.0.419",
        "dependency_lock_sha256": trust.dependencies_sha256,
        "build_target": "BepInEx.Preloader/BepInEx.Preloader.csproj",
        "official_preloader_sha256": "3" * 64,
        "patched_preloader_sha256": "4" * 64,
    }
    path = tmp_path / "provenance.json"
    path.write_bytes(canonical_json(data))
    return path


def test_load_trust_requires_exact_schema_and_lowercase_hashes():
    malformed = {
        "schema_version": 1,
        "patch_sha256": "A" * 64,
        "toolchain_sha256": "0" * 64,
        "dependencies_sha256": "1" * 64,
        "nuget_lock_tree_sha256": "2" * 64,
    }
    with pytest.raises(CompatError, match="trust schema"):
        parse_trust_data(malformed)


def test_load_trust_rejects_untracked_or_dirty_named_input(
    committed_compat_repo: Path,
):
    patch = (
        committed_compat_repo
        / "oracle/compat/bepinex-macos15-platform.patch"
    )
    patch.write_text("locally replaced")
    with pytest.raises(CompatError, match="HEAD blob"):
        load_trust(committed_compat_repo)


def test_load_provenance_rejects_unknown_keys_and_hash_mismatch(
    committed_compat_repo: Path,
    valid_provenance: Path,
):
    trust = load_trust(committed_compat_repo)
    decoded = json.loads(valid_provenance.read_text())
    decoded["unexpected"] = True
    valid_provenance.write_bytes(canonical_json(decoded))
    with pytest.raises(CompatError, match="provenance"):
        load_provenance(valid_provenance, trust)


def test_canonical_json_is_sorted_utf8_with_final_newline():
    assert canonical_json({"b": 2, "a": 1}) == b'{\n  "a": 1,\n  "b": 2\n}\n'


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": True},
        {"extra": "not allowed"},
        {"patch_sha256": "a" * 63},
    ],
)
def test_trust_schema_rejects_wrong_types_unknown_keys_and_bad_hashes(change):
    data = {
        "schema_version": 1,
        "patch_sha256": "0" * 64,
        "toolchain_sha256": "1" * 64,
        "dependencies_sha256": "2" * 64,
        "nuget_lock_tree_sha256": "3" * 64,
    }
    data.update(change)
    with pytest.raises(CompatError, match="trust schema"):
        parse_trust_data(data)


def test_load_provenance_rejects_noncanonical_json(
    committed_compat_repo: Path,
    valid_provenance: Path,
):
    trust = load_trust(committed_compat_repo)
    valid_provenance.write_text(json.dumps(json.loads(valid_provenance.read_text())))
    with pytest.raises(CompatError, match="canonical"):
        load_provenance(valid_provenance, trust)
