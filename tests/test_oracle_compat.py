from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ssr_env.oracle_compat import (
    CompatError,
    SourceCheckout,
    canonical_json,
    load_provenance,
    load_trust,
    parse_trust_data,
    prepare_source,
    source_differences,
    validate_source_checkout,
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

PACKAGE_SOURCES = (
    ("HarmonyX", "2.0.6", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/harmonyx/2.0.6/harmonyx.2.0.6.nupkg"),
    ("HarmonyX", "2.9.0", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/harmonyx/2.9.0/harmonyx.2.9.0.nupkg"),
    ("Microsoft.NETFramework.ReferenceAssemblies", "1.0.3",
     "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/microsoft.netframework.referenceassemblies/1.0.3/microsoft.netframework.referenceassemblies.1.0.3.nupkg"),
    ("Microsoft.NETFramework.ReferenceAssemblies.net35", "1.0.3",
     "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/microsoft.netframework.referenceassemblies.net35/1.0.3/microsoft.netframework.referenceassemblies.net35.1.0.3.nupkg"),
    ("Mono.Cecil", "0.10.4", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/mono.cecil/0.10.4/mono.cecil.0.10.4.nupkg"),
    ("MonoMod.RuntimeDetour", "20.5.21.5", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/monomod.runtimedetour/20.5.21.5/monomod.runtimedetour.20.5.21.5.nupkg"),
    ("MonoMod.RuntimeDetour", "22.1.29.1", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/monomod.runtimedetour/22.1.29.1/monomod.runtimedetour.22.1.29.1.nupkg"),
    ("MonoMod.Utils", "20.5.21.5", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/monomod.utils/20.5.21.5/monomod.utils.20.5.21.5.nupkg"),
    ("MonoMod.Utils", "22.1.29.1", "https://api.nuget.org/v3/index.json",
     "https://api.nuget.org/v3-flatcontainer/monomod.utils/22.1.29.1/monomod.utils.22.1.29.1.nupkg"),
    ("UnityEngine", "5.6.1", "https://nuget.bepinex.dev/v3/index.json",
     "https://nuget.bepinex.dev/v3/package/unityengine/5.6.1/unityengine.5.6.1.nupkg"),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module")
def compat_cli():
    path = Path(__file__).resolve().parents[1] / "tools/build_bepinex_compat.py"
    spec = importlib.util.spec_from_file_location("build_bepinex_compat", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


@pytest.fixture(scope="module")
def pinned_recursive_checkout() -> Path:
    checkout = (
        Path(__file__).resolve().parents[1]
        / "data/oracle/compat/upstream/BepInEx-5.4.23.5"
    )
    assert (
        subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=checkout,
            check=True,
            text=True,
            capture_output=True,
        ).stdout
        == ""
    )
    return checkout


@pytest.fixture
def recursive_source_checkout(
    pinned_recursive_checkout: Path,
    tmp_path: Path,
) -> Path:
    checkout = tmp_path / "source"
    shutil.copytree(pinned_recursive_checkout, checkout, symlinks=True)
    return checkout


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
    ("package_id", "version", "source_index", "package_url"),
    PACKAGE_SOURCES,
)
def test_package_routing_uses_exact_authoritative_https_source(
    compat_cli,
    package_id,
    version,
    source_index,
    package_url,
):
    assert compat_cli._source_index(package_id, version) == source_index
    assert compat_cli._package_url(package_id, version) == package_url


def test_package_routing_rejects_pin_outside_exact_allowlist(compat_cli):
    with pytest.raises(CompatError, match="no trusted package source"):
        compat_cli._package_url("UnityEngine", "5.6.2")


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


def test_prepare_source_changes_only_platform_cs_one_hunk(
    pinned_recursive_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(pinned_recursive_checkout, trust)
    prepared = prepare_source(source, tmp_path / "prepared", trust)
    platform = prepared / "BepInEx.Preloader/Platform.cs"
    assert "AccessibilityBundles" not in platform.read_text(encoding="utf-8-sig")
    assert platform.read_text(encoding="utf-8-sig").count(
        "/System/Library/CoreServices"
    ) == 1
    changed = source_differences(pinned_recursive_checkout, prepared)
    assert changed == ["BepInEx.Preloader/Platform.cs"]


def test_validate_source_checkout_rejects_wrong_head(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
):
    marker = recursive_source_checkout / "wrong-head"
    marker.write_text("new commit\n")
    subprocess.run(
        ["git", "add", "wrong-head"], cwd=recursive_source_checkout, check=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "wrong head",
        ],
        cwd=recursive_source_checkout,
        check=True,
    )
    with pytest.raises(CompatError, match="source commit"):
        validate_source_checkout(
            recursive_source_checkout, load_trust(committed_compat_repo)
        )


def test_validate_source_checkout_rejects_dirty_tracked_file(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
):
    (recursive_source_checkout / "README.md").write_text("dirty\n")
    with pytest.raises(CompatError, match="clean checkout"):
        validate_source_checkout(
            recursive_source_checkout, load_trust(committed_compat_repo)
        )


def test_validate_source_checkout_rejects_untracked_file(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
):
    (recursive_source_checkout / "untracked").write_text("untracked\n")
    with pytest.raises(CompatError, match="clean checkout"):
        validate_source_checkout(
            recursive_source_checkout, load_trust(committed_compat_repo)
        )


def test_validate_source_checkout_requires_exact_harmony_submodule(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
):
    harmony = recursive_source_checkout / "submodules/BepInEx.Harmony"
    previous = subprocess.run(
        ["git", "rev-parse", "HEAD^"],
        cwd=harmony,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    subprocess.run(["git", "checkout", "-q", previous], cwd=harmony, check=True)
    with pytest.raises(CompatError, match="submodule commit"):
        validate_source_checkout(
            recursive_source_checkout, load_trust(committed_compat_repo)
        )


def test_prepare_source_rejects_already_patched_source(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    patch = committed_compat_repo / "oracle/compat/bepinex-macos15-platform.patch"
    subprocess.run(
        ["git", "apply", str(patch)],
        cwd=recursive_source_checkout,
        check=True,
    )
    with pytest.raises(CompatError, match="patch preimage"):
        prepare_source(source, tmp_path / "prepared", trust)


def test_prepare_source_rejects_changed_preimage(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    platform = recursive_source_checkout / "BepInEx.Preloader/Platform.cs"
    platform.write_text(
        platform.read_text(encoding="utf-8-sig").replace(
            "current = Platform.Android;", "current = Platform.Windows;"
        ),
        encoding="utf-8",
    )
    with pytest.raises(CompatError, match="patch preimage"):
        prepare_source(source, tmp_path / "prepared", trust)


def test_validate_source_checkout_rejects_symlinked_root(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    link = tmp_path / "source-link"
    link.symlink_to(recursive_source_checkout, target_is_directory=True)
    with pytest.raises(CompatError, match="checkout root"):
        validate_source_checkout(link, load_trust(committed_compat_repo))


def test_prepare_source_rejects_symlinked_patch_target(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    platform = recursive_source_checkout / "BepInEx.Preloader/Platform.cs"
    original = recursive_source_checkout / "Platform-original.cs"
    platform.rename(original)
    platform.symlink_to(original)
    with pytest.raises(CompatError, match="patch target"):
        prepare_source(source, tmp_path / "prepared", trust)


def test_prepare_source_rejects_destination_inside_checkout(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    with pytest.raises(CompatError, match="outside source checkout"):
        prepare_source(source, recursive_source_checkout / "prepared", trust)
    assert not (recursive_source_checkout / "prepared").exists()


def test_source_checkout_is_an_immutable_resolved_record(
    pinned_recursive_checkout: Path,
    committed_compat_repo: Path,
):
    source = validate_source_checkout(
        pinned_recursive_checkout, load_trust(committed_compat_repo)
    )
    assert isinstance(source, SourceCheckout)
    assert source.root == pinned_recursive_checkout.resolve()
    with pytest.raises(AttributeError):
        source.source_commit = "0" * 40
