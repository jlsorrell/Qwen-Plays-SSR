import ast
import builtins
import errno
import json
import os
import pathlib
import shutil
import stat
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

import ssr_env.oracle_compat as oracle_compat
import ssr_env.oracle_install as oracle_install
from ssr_env.oracle_compat import BuildProvenance, CompatTrust, canonical_json
from ssr_env.oracle_install import (
    InstallError,
    InstallManifest,
    ManifestEntry,
    PreloaderCompatibilityStatus,
    _status_to_dict,
    install_runtime,
    main,
    status_install,
)


OFFICIAL_BYTES = b"official preloader"
PATCHED_BYTES = b"patched preloader"
BACKUP_ROOT = "BepInEx/.ssr-oracle-backup"
COMPAT_ROOT = "BepInEx/.ssr-oracle-compat"
ACTIVE_PATH = "BepInEx/core/BepInEx.Preloader.dll"
BACKUP_PATH = f"{BACKUP_ROOT}/BepInEx.Preloader.dll"
PROVENANCE_PATH = f"{COMPAT_ROOT}/preloader-provenance.json"


def _make_game(root: Path, assembly: bytes) -> Path:
    managed = root / "Sausage.app/Contents/Resources/Data/Managed"
    managed.mkdir(parents=True)
    (managed / "Assembly-CSharp.dll").write_bytes(assembly)
    executable = root / "Sausage.app/Contents/MacOS/Sausage"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"mach-o")
    return root


def _make_runtime_archive(path: Path) -> Path:
    with ZipFile(path, "w") as archive:
        archive.writestr(".doorstop_version", b"4.5.0")
        archive.writestr("changelog.txt", b"BepInEx 5.4.23.5")
        archive.writestr("BepInEx/", b"")
        archive.writestr("run_bepinex.sh", 'executable_name=""\n')
        archive.writestr("libdoorstop.dylib", b"doorstop")
        archive.writestr("BepInEx/core/BepInEx.dll", b"core")
        archive.writestr("BepInEx/core/0Harmony.dll", b"harmony")
        archive.writestr(ACTIVE_PATH, OFFICIAL_BYTES)
    return path


@pytest.fixture
def installed_official_game(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    assembly = b"known assembly"
    official_hash = sha256(OFFICIAL_BYTES).hexdigest()
    game = _make_game(tmp_path / "game", assembly)
    archive = _make_runtime_archive(tmp_path / "runtime.zip")
    monkeypatch.setattr(
        oracle_install, "EXPECTED_ASSEMBLY_SHA256", sha256(assembly).hexdigest()
    )
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_RUNTIME_ARCHIVE_SHA256",
        sha256(archive.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_OFFICIAL_PRELOADER_SHA256",
        official_hash,
        raising=False,
    )
    install_runtime(game, archive)
    return game


@pytest.fixture
def trust() -> CompatTrust:
    return CompatTrust(
        schema_version=1,
        patch_sha256="1" * 64,
        toolchain_sha256="2" * 64,
        dependencies_sha256="3" * 64,
        nuget_lock_tree_sha256="4" * 64,
    )


def _provenance(trust: CompatTrust) -> BuildProvenance:
    return BuildProvenance(
        schema_version=1,
        source_commit="57f1fb859bd4d0264cd2a59074d0e96c6a492a33",
        patch_sha256=trust.patch_sha256,
        toolchain_lock_sha256=trust.toolchain_sha256,
        dotnet_sdk_version="8.0.419",
        dependency_lock_sha256=trust.dependencies_sha256,
        build_target=(
            "BepInEx.Preloader/BepInEx.Preloader.csproj@framework=net35"
        ),
        official_preloader_sha256=sha256(OFFICIAL_BYTES).hexdigest(),
        patched_preloader_sha256=sha256(PATCHED_BYTES).hexdigest(),
    )


def _write_deploy_request(
    tmp_path: Path,
    trust: CompatTrust,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    official_hash = sha256(OFFICIAL_BYTES).hexdigest()
    patched_hash = sha256(PATCHED_BYTES).hexdigest()
    monkeypatch.setattr(
        oracle_compat, "_OFFICIAL_PRELOADER_SHA256", official_hash
    )
    monkeypatch.setattr(
        oracle_compat, "EXPECTED_PATCHED_PRELOADER_SHA256", patched_hash
    )
    monkeypatch.setattr(
        oracle_install, "EXPECTED_PATCHED_PRELOADER_SHA256", patched_hash
    )
    monkeypatch.setattr(oracle_install, "load_trust", lambda _: trust)
    preloader = tmp_path / "reviewed-preloader.dll"
    preloader.write_bytes(PATCHED_BYTES)
    provenance = tmp_path / "reviewed-provenance.json"
    provenance.write_bytes(canonical_json(asdict(_provenance(trust))))
    return preloader, provenance


@pytest.fixture
def deploy_request(
    tmp_path: Path,
    trust: CompatTrust,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    return _write_deploy_request(tmp_path, trust, monkeypatch)


def _write_patched_install(
    game: Path,
    trust: CompatTrust,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    official_hash = sha256(OFFICIAL_BYTES).hexdigest()
    patched_hash = sha256(PATCHED_BYTES).hexdigest()
    monkeypatch.setattr(
        oracle_compat, "_OFFICIAL_PRELOADER_SHA256", official_hash
    )
    monkeypatch.setattr(
        oracle_compat, "EXPECTED_PATCHED_PRELOADER_SHA256", patched_hash
    )
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_PATCHED_PRELOADER_SHA256",
        patched_hash,
        raising=False,
    )
    provenance = _provenance(trust)
    active = game / ACTIVE_PATH
    active.write_bytes(PATCHED_BYTES)
    backup = game / BACKUP_PATH
    backup.parent.mkdir()
    backup.write_bytes(OFFICIAL_BYTES)
    provenance_path = game / PROVENANCE_PATH
    provenance_path.parent.mkdir()
    provenance_path.write_bytes(canonical_json(asdict(provenance)))

    manifest = oracle_install._load_manifest(game)
    by_path = {entry.relative_path: entry for entry in manifest.entries}
    by_path[ACTIVE_PATH] = ManifestEntry(
        ACTIVE_PATH, "file", sha256(PATCHED_BYTES).hexdigest()
    )
    by_path[BACKUP_ROOT] = ManifestEntry(BACKUP_ROOT, "directory", None)
    by_path[BACKUP_PATH] = ManifestEntry(
        BACKUP_PATH, "file", sha256(OFFICIAL_BYTES).hexdigest()
    )
    by_path[COMPAT_ROOT] = ManifestEntry(COMPAT_ROOT, "directory", None)
    by_path[PROVENANCE_PATH] = ManifestEntry(
        PROVENANCE_PATH,
        "file",
        sha256(provenance_path.read_bytes()).hexdigest(),
    )
    oracle_install._write_manifest(
        game,
        InstallManifest(
            schema_version=manifest.schema_version,
            game_assembly_sha256=manifest.game_assembly_sha256,
            runtime_archive_sha256=manifest.runtime_archive_sha256,
            entries=tuple(by_path.values()),
        ),
    )
    monkeypatch.setattr(oracle_install, "load_trust", lambda _: trust, raising=False)


@pytest.fixture
def installed_patched_game(
    installed_official_game: Path,
    trust: CompatTrust,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    _write_patched_install(installed_official_game, trust, monkeypatch)
    return installed_official_game


def _create_path_of_kind(
    path: Path, kind: str, tmp_path: Path
) -> None:
    if kind == "file":
        path.write_bytes(b"unmanaged")
    elif kind == "directory":
        path.mkdir()
    else:
        target = tmp_path / "symlink-target"
        target.mkdir(exist_ok=True)
        path.symlink_to(target, target_is_directory=True)


def test_status_reports_official_only_when_reserved_paths_absent(
    installed_official_game: Path,
):
    status = status_install(installed_official_game)
    assert status.preloader_compatibility.state == "official"
    assert status.preloader_compatibility.issues == ()
    assert status.healthy


def test_status_reports_patched_only_when_all_hashes_agree(
    installed_official_game: Path,
    trust: CompatTrust,
    monkeypatch: pytest.MonkeyPatch,
):
    _write_patched_install(installed_official_game, trust, monkeypatch)
    status = status_install(installed_official_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.state == "patched"
    assert status.preloader_compatibility.issues == ()
    assert status.healthy


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_status_rejects_unmanaged_reserved_path(
    kind: str,
    installed_official_game: Path,
    tmp_path: Path,
):
    reserved = installed_official_game / COMPAT_ROOT
    _create_path_of_kind(reserved, kind, tmp_path)
    status = status_install(installed_official_game)
    assert status.preloader_compatibility.state == "invalid"
    assert "unmanaged_reserved_path" in status.preloader_compatibility.issues
    assert not status.healthy


def test_status_reports_invalid_stable_issue_codes(
    installed_patched_game: Path,
):
    active = installed_patched_game / ACTIVE_PATH
    active.write_bytes(b"changed")
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.issues == ("active_hash_mismatch",)


def test_status_rejects_hash_consistent_arbitrary_unreviewed_active_bytes(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_PATCHED_PRELOADER_SHA256",
        "a" * 64,
        raising=False,
    )
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.state == "invalid"
    assert status.preloader_compatibility.issues == (
        "active_hash_mismatch",
    )


def test_compatibility_status_is_immutable():
    status = PreloaderCompatibilityStatus(
        state="official",
        official_sha256="0" * 64,
        active_sha256="0" * 64,
        patched_sha256=None,
        issues=(),
    )
    with pytest.raises(AttributeError):
        status.state = "invalid"  # type: ignore[misc]


def test_status_serialization_preserves_existing_fields_and_adds_compatibility(
    installed_official_game: Path,
):
    status = status_install(installed_official_game)
    serialized = _status_to_dict(status)
    assert set(serialized) == {
        "manifest",
        "missing",
        "changed",
        "healthy",
        "preloader_compatibility",
    }
    assert serialized["preloader_compatibility"] == {
        "state": "official",
        "official_sha256": sha256(OFFICIAL_BYTES).hexdigest(),
        "active_sha256": sha256(OFFICIAL_BYTES).hexdigest(),
        "patched_sha256": None,
        "issues": [],
    }


@pytest.mark.parametrize("reserved_root", [BACKUP_ROOT, COMPAT_ROOT])
@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_status_rejects_each_unmanaged_reserved_root_kind(
    reserved_root: str,
    kind: str,
    installed_official_game: Path,
    tmp_path: Path,
):
    _create_path_of_kind(
        installed_official_game / reserved_root, kind, tmp_path
    )
    status = status_install(installed_official_game)
    assert status.preloader_compatibility.issues == (
        "unmanaged_reserved_path",
    )


@pytest.mark.parametrize(
    ("relative_path", "expected_issue"),
    [
        (BACKUP_PATH, "backup_missing"),
        (PROVENANCE_PATH, "provenance_missing"),
    ],
)
def test_status_rejects_missing_patched_artifacts(
    relative_path: str,
    expected_issue: str,
    installed_patched_game: Path,
):
    (installed_patched_game / relative_path).unlink()
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.state == "invalid"
    assert expected_issue in status.preloader_compatibility.issues


@pytest.mark.parametrize(
    ("relative_path", "expected_issue"),
    [
        (ACTIVE_PATH, "active_unsafe"),
        (BACKUP_PATH, "backup_unsafe"),
        (PROVENANCE_PATH, "provenance_unsafe"),
    ],
)
def test_status_rejects_symlinked_compatibility_files(
    relative_path: str,
    expected_issue: str,
    installed_patched_game: Path,
    tmp_path: Path,
):
    path = installed_patched_game / relative_path
    payload = path.read_bytes()
    path.unlink()
    target = tmp_path / ("outside-" + path.name)
    target.write_bytes(payload)
    path.symlink_to(target)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.state == "invalid"
    assert expected_issue in status.preloader_compatibility.issues


@pytest.mark.parametrize(
    ("root_relative", "artifact_relative", "expected_issue"),
    [
        (BACKUP_ROOT, BACKUP_PATH, "backup_unsafe"),
        (COMPAT_ROOT, PROVENANCE_PATH, "provenance_unsafe"),
    ],
)
def test_status_rejects_symlinked_compatibility_parent(
    root_relative: str,
    artifact_relative: str,
    expected_issue: str,
    installed_patched_game: Path,
    tmp_path: Path,
):
    artifact = installed_patched_game / artifact_relative
    payload = artifact.read_bytes()
    artifact.unlink()
    parent = installed_patched_game / root_relative
    parent.rmdir()
    outside = tmp_path / ("outside-" + parent.name)
    outside.mkdir()
    (outside / Path(artifact_relative).name).write_bytes(payload)
    parent.symlink_to(outside, target_is_directory=True)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.state == "invalid"
    assert expected_issue in status.preloader_compatibility.issues


@pytest.mark.parametrize(
    ("parent_relative", "artifact_relative", "unsafe_issue", "missing_issue"),
    [
        ("BepInEx/core", ACTIVE_PATH, "active_unsafe", "active_missing"),
        (BACKUP_ROOT, BACKUP_PATH, "backup_unsafe", "backup_missing"),
        (
            COMPAT_ROOT,
            PROVENANCE_PATH,
            "provenance_unsafe",
            "provenance_missing",
        ),
    ],
)
def test_status_reports_symlinked_parent_as_unsafe_when_child_is_absent(
    parent_relative: str,
    artifact_relative: str,
    unsafe_issue: str,
    missing_issue: str,
    installed_patched_game: Path,
    tmp_path: Path,
):
    parent = installed_patched_game / parent_relative
    preserved = tmp_path / ("preserved-" + parent.name)
    parent.replace(preserved)
    empty = tmp_path / ("empty-" + parent.name)
    empty.mkdir()
    parent.symlink_to(empty, target_is_directory=True)

    status = status_install(installed_patched_game, repo_root=Path("/unused"))

    assert unsafe_issue in status.preloader_compatibility.issues
    assert missing_issue not in status.preloader_compatibility.issues
    assert not (empty / Path(artifact_relative).name).exists()


@pytest.mark.parametrize(
    ("artifact_relative", "unsafe_issue"),
    [
        (BACKUP_PATH, "backup_unsafe"),
        (PROVENANCE_PATH, "provenance_unsafe"),
    ],
)
def test_status_rejects_expected_reserved_child_with_directory_type(
    artifact_relative: str,
    unsafe_issue: str,
    installed_patched_game: Path,
):
    artifact = installed_patched_game / artifact_relative
    artifact.unlink()
    artifact.mkdir()

    status = status_install(installed_patched_game, repo_root=Path("/unused"))

    assert unsafe_issue in status.preloader_compatibility.issues
    assert "unmanaged_reserved_path" in status.preloader_compatibility.issues


def test_status_rejects_noncanonical_provenance(
    installed_patched_game: Path,
):
    provenance = installed_patched_game / PROVENANCE_PATH
    provenance.write_text(provenance.read_text().replace("  ", " "))
    _replace_manifest_file_hash(installed_patched_game, PROVENANCE_PATH)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert "provenance_invalid" in status.preloader_compatibility.issues


def test_status_rejects_malformed_canonical_provenance(
    installed_patched_game: Path,
):
    provenance = installed_patched_game / PROVENANCE_PATH
    decoded = json.loads(provenance.read_bytes())
    decoded["unexpected"] = True
    provenance.write_bytes(canonical_json(decoded))
    _replace_manifest_file_hash(installed_patched_game, PROVENANCE_PATH)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert "provenance_invalid" in status.preloader_compatibility.issues


def _replace_manifest_file_hash(game: Path, relative_path: str) -> None:
    manifest = oracle_install._load_manifest(game)
    entries = tuple(
        ManifestEntry(
            entry.relative_path,
            entry.kind,
            sha256((game / relative_path).read_bytes()).hexdigest()
            if entry.relative_path == relative_path
            else entry.sha256,
        )
        for entry in manifest.entries
    )
    oracle_install._write_manifest(
        game,
        InstallManifest(
            manifest.schema_version,
            manifest.game_assembly_sha256,
            manifest.runtime_archive_sha256,
            entries,
        ),
    )


def _set_manifest_file_hash_to_genuine_mismatch(
    game: Path,
    relative_path: str,
) -> None:
    manifest_path = game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    matching_entries = [
        entry
        for entry in decoded["entries"]
        if entry["relative_path"] == relative_path
    ]
    assert len(matching_entries) == 1
    current = matching_entries[0]["sha256"]
    assert isinstance(current, str) and len(current) == 64
    replacement_first = "0" if current[0] != "0" else "1"
    mismatched = replacement_first + current[1:]
    assert mismatched != current
    matching_entries[0]["sha256"] = mismatched
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )


@pytest.mark.parametrize(
    "relative_path",
    [BACKUP_PATH, PROVENANCE_PATH],
)
def test_status_rejects_missing_compatibility_manifest_ownership(
    relative_path: str,
    installed_patched_game: Path,
):
    manifest = oracle_install._load_manifest(installed_patched_game)
    oracle_install._write_manifest(
        installed_patched_game,
        InstallManifest(
            manifest.schema_version,
            manifest.game_assembly_sha256,
            manifest.runtime_archive_sha256,
            tuple(
                entry
                for entry in manifest.entries
                if entry.relative_path != relative_path
            ),
        ),
    )
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert "manifest_compatibility_ownership_mismatch" in (
        status.preloader_compatibility.issues
    )


def test_status_rejects_extra_compatibility_manifest_ownership(
    installed_patched_game: Path,
):
    extra = installed_patched_game / f"{COMPAT_ROOT}/extra"
    extra.write_bytes(b"extra")
    manifest = oracle_install._load_manifest(installed_patched_game)
    oracle_install._write_manifest(
        installed_patched_game,
        InstallManifest(
            manifest.schema_version,
            manifest.game_assembly_sha256,
            manifest.runtime_archive_sha256,
            manifest.entries
            + (
                ManifestEntry(
                    f"{COMPAT_ROOT}/extra",
                    "file",
                    sha256(b"extra").hexdigest(),
                ),
            ),
        ),
    )
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert "manifest_compatibility_ownership_mismatch" in (
        status.preloader_compatibility.issues
    )


@pytest.mark.parametrize("reserved_root", [BACKUP_ROOT, COMPAT_ROOT])
@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_status_rejects_unowned_reserved_tree_children(
    reserved_root: str,
    kind: str,
    installed_patched_game: Path,
    tmp_path: Path,
):
    extra = installed_patched_game / reserved_root / "unowned"
    _create_path_of_kind(extra, kind, tmp_path)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.state == "invalid"
    assert "unmanaged_reserved_path" in status.preloader_compatibility.issues


def test_status_rejects_backup_hash_mismatch(
    installed_patched_game: Path,
):
    backup = installed_patched_game / BACKUP_PATH
    backup.write_bytes(b"changed backup")
    _replace_manifest_file_hash(installed_patched_game, BACKUP_PATH)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.issues == ("backup_hash_mismatch",)


def test_status_rejects_provenance_manifest_hash_mismatch(
    installed_patched_game: Path,
):
    manifest = oracle_install._load_manifest(installed_patched_game)
    entries = tuple(
        ManifestEntry(entry.relative_path, entry.kind, "9" * 64)
        if entry.relative_path == PROVENANCE_PATH
        else entry
        for entry in manifest.entries
    )
    oracle_install._write_manifest(
        installed_patched_game,
        InstallManifest(
            manifest.schema_version,
            manifest.game_assembly_sha256,
            manifest.runtime_archive_sha256,
            entries,
        ),
    )
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert "provenance_hash_mismatch" in status.preloader_compatibility.issues


def test_status_rejects_invalid_or_dirty_trust(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    def reject_trust(_: Path):
        raise oracle_install.CompatError("does not match its HEAD blob")

    monkeypatch.setattr(oracle_install, "load_trust", reject_trust)
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.preloader_compatibility.issues == (
        "compatibility_trust_invalid",
    )
    assert status.preloader_compatibility.patched_sha256 is None


def test_status_rejects_wrong_runtime_archive(
    installed_official_game: Path,
):
    manifest = oracle_install._load_manifest(installed_official_game)
    oracle_install._write_manifest(
        installed_official_game,
        InstallManifest(
            manifest.schema_version,
            manifest.game_assembly_sha256,
            "9" * 64,
            manifest.entries,
        ),
    )
    status = status_install(installed_official_game)
    assert status.preloader_compatibility.issues == (
        "runtime_archive_mismatch",
    )


def test_status_rejects_wrong_game(
    installed_official_game: Path,
):
    assembly = (
        installed_official_game
        / "Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
    )
    assembly.write_bytes(b"wrong")
    with pytest.raises(InstallError, match="unsupported Assembly-CSharp"):
        status_install(installed_official_game)


def test_status_rejects_ambiguous_partial_patched_state(
    installed_official_game: Path,
):
    backup = installed_official_game / BACKUP_PATH
    backup.parent.mkdir()
    backup.write_bytes(OFFICIAL_BYTES)
    status = status_install(installed_official_game)
    assert status.preloader_compatibility.state == "invalid"
    assert "unmanaged_reserved_path" in status.preloader_compatibility.issues


def _tree_snapshot(root: Path) -> tuple[tuple[str, int, bytes | str], ...]:
    snapshot: list[tuple[str, int, bytes | str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if path.is_symlink():
            content: bytes | str = os.readlink(path)
        elif path.is_file():
            content = path.read_bytes()
        else:
            content = b""
        snapshot.append((relative, mode, content))
    return tuple(snapshot)


def _tree_snapshot_without_recovery(
    root: Path,
) -> tuple[tuple[str, int, bytes | str], ...]:
    return tuple(
        entry
        for entry in _tree_snapshot(root)
        if entry[0] != ".ssr-oracle-recovery"
        and not entry[0].startswith(".ssr-oracle-recovery/")
    )


def test_status_is_strictly_read_only(
    installed_patched_game: Path,
):
    before = _tree_snapshot(installed_patched_game)
    status_install(installed_patched_game, repo_root=Path("/unused"))
    assert _tree_snapshot(installed_patched_game) == before


def _file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _manifest_compatibility_entries(
    manifest: InstallManifest,
) -> dict[str, ManifestEntry]:
    return {
        entry.relative_path: entry
        for entry in manifest.entries
        if entry.relative_path in {BACKUP_ROOT, COMPAT_ROOT}
        or entry.relative_path.startswith(BACKUP_ROOT + "/")
        or entry.relative_path.startswith(COMPAT_ROOT + "/")
    }


def test_deploy_preloader_publishes_reviewed_artifacts_and_manifest_last(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    active.chmod(0o640)
    manifest_path.chmod(0o600)

    manifest = oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )

    backup = installed_official_game / BACKUP_PATH
    deployed_provenance = installed_official_game / PROVENANCE_PATH
    assert active.read_bytes() == PATCHED_BYTES
    assert backup.read_bytes() == OFFICIAL_BYTES
    assert deployed_provenance.read_bytes() == provenance.read_bytes()
    assert _file_mode(active) == 0o640
    assert _file_mode(backup) == 0o640
    assert _file_mode(deployed_provenance) == 0o644
    assert _file_mode(manifest_path) == 0o600
    entries = {entry.relative_path: entry for entry in manifest.entries}
    assert entries[ACTIVE_PATH].sha256 == sha256(PATCHED_BYTES).hexdigest()
    assert _manifest_compatibility_entries(manifest) == {
        BACKUP_ROOT: ManifestEntry(BACKUP_ROOT, "directory", None),
        BACKUP_PATH: ManifestEntry(
            BACKUP_PATH, "file", sha256(OFFICIAL_BYTES).hexdigest()
        ),
        COMPAT_ROOT: ManifestEntry(COMPAT_ROOT, "directory", None),
        PROVENANCE_PATH: ManifestEntry(
            PROVENANCE_PATH,
            "file",
            sha256(provenance.read_bytes()).hexdigest(),
        ),
    }
    status = status_install(installed_official_game, repo_root=Path("/unused"))
    assert status.healthy
    assert status.preloader_compatibility.state == "patched"
    assert not tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )


def test_deploy_preloader_is_byte_identically_idempotent(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
):
    preloader, provenance = deploy_request
    first = oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )
    before = _tree_snapshot(installed_official_game)

    second = oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )

    assert second == first
    assert _tree_snapshot(installed_official_game) == before


def test_deploy_preloader_idempotence_rejects_concurrent_active_change(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )
    active = installed_official_game / ACTIVE_PATH

    def change_during_revalidation(boundary: str) -> None:
        if boundary == "idempotent_revalidate":
            active.write_bytes(b"concurrent change")

    monkeypatch.setattr(
        oracle_install,
        "_deploy_preloader_checkpoint",
        change_during_revalidation,
    )

    with pytest.raises(InstallError, match="changed during validation"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )


@pytest.mark.parametrize("request_kind", ["preloader", "provenance"])
def test_deploy_preloader_idempotence_revalidates_request_leaf(
    request_kind: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )
    target = preloader if request_kind == "preloader" else provenance
    held = tmp_path / f"held-{request_kind}"

    def change_during_revalidation(boundary: str) -> None:
        if boundary == "idempotent_revalidate":
            target.replace(held)
            target.write_bytes(b"concurrent request")

    monkeypatch.setattr(
        oracle_install,
        "_deploy_preloader_checkpoint",
        change_during_revalidation,
    )

    with pytest.raises(InstallError, match="changed during validation"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )


@pytest.mark.parametrize("directory_name", ["BepInEx", "core"])
def test_deploy_preloader_idempotence_reanchors_directory_edges(
    directory_name: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )
    target = (
        installed_official_game / "BepInEx"
        if directory_name == "BepInEx"
        else installed_official_game / "BepInEx/core"
    )
    held = tmp_path / f"held-{directory_name}"

    def change_during_revalidation(boundary: str) -> None:
        if boundary == "idempotent_revalidate":
            target.replace(held)
            target.mkdir()
            (target / "unrelated").write_bytes(b"keep")

    monkeypatch.setattr(
        oracle_install,
        "_deploy_preloader_checkpoint",
        change_during_revalidation,
    )

    with pytest.raises(InstallError, match="directory entry changed"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert (target / "unrelated").read_bytes() == b"keep"


def test_deploy_preloader_rejects_symlinked_request_parent(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
):
    preloader, provenance = deploy_request
    actual = tmp_path / "actual-request"
    actual.mkdir()
    copied = actual / preloader.name
    copied.write_bytes(preloader.read_bytes())
    linked = tmp_path / "linked-request"
    linked.symlink_to(actual, target_is_directory=True)

    with pytest.raises(InstallError, match="without following symlinks"):
        oracle_install.deploy_preloader(
            installed_official_game,
            linked / copied.name,
            provenance,
            repo_root=Path("/unused"),
        )


@pytest.mark.parametrize(
    ("damage", "message"),
    [
        ("wrong_game", "unsupported Assembly-CSharp"),
        ("wrong_archive", "runtime archive"),
        ("unhealthy_manifest", "healthy official"),
        ("changed_active", "healthy official"),
        ("forged_provenance", "provenance"),
        ("non_reviewed_dll", "reviewed patched"),
        ("unmanaged_backup", "healthy official"),
        ("symlink_compat_parent", "healthy official"),
    ],
)
def test_deploy_preloader_rejects_preflight_failures_without_mutation(
    damage: str,
    message: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    if damage == "wrong_game":
        (
            installed_official_game
            / "Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
        ).write_bytes(b"wrong")
    elif damage == "wrong_archive":
        manifest = oracle_install._load_manifest(installed_official_game)
        oracle_install._write_manifest(
            installed_official_game,
            InstallManifest(
                manifest.schema_version,
                manifest.game_assembly_sha256,
                "9" * 64,
                manifest.entries,
            ),
        )
    elif damage == "unhealthy_manifest":
        (installed_official_game / "BepInEx/core/BepInEx.dll").write_bytes(
            b"changed"
        )
    elif damage == "changed_active":
        (installed_official_game / ACTIVE_PATH).write_bytes(b"changed")
    elif damage == "forged_provenance":
        decoded = json.loads(provenance.read_bytes())
        decoded["patch_sha256"] = "9" * 64
        provenance.write_bytes(canonical_json(decoded))
    elif damage == "non_reviewed_dll":
        preloader.write_bytes(b"different patched build")
    elif damage == "unmanaged_backup":
        reserved = installed_official_game / BACKUP_ROOT
        reserved.mkdir()
        (reserved / "user-file").write_bytes(b"keep")
    else:
        outside = tmp_path / "outside-compat"
        outside.mkdir()
        (installed_official_game / COMPAT_ROOT).symlink_to(
            outside, target_is_directory=True
        )
    before = _tree_snapshot(installed_official_game)
    stage_called = False

    def observe_stage(*args, **kwargs):
        nonlocal stage_called
        stage_called = True
        raise AssertionError("preflight must finish before staging")

    monkeypatch.setattr(
        oracle_install, "_create_compat_staging", observe_stage
    )

    with pytest.raises(InstallError, match=message):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert not stage_called
    assert _tree_snapshot(installed_official_game) == before


def test_deploy_preloader_refuses_a_different_build_over_a_patched_install(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
):
    preloader, provenance = deploy_request
    oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )
    different = preloader.with_name("different.dll")
    different.write_bytes(b"different patched build")
    before = _tree_snapshot(installed_official_game)

    with pytest.raises(InstallError, match="different patched build"):
        oracle_install.deploy_preloader(
            installed_official_game,
            different,
            provenance,
            repo_root=Path("/unused"),
        )

    assert _tree_snapshot(installed_official_game) == before


@pytest.mark.parametrize("source_name", ["preloader", "provenance"])
def test_deploy_preloader_rejects_symlinked_request_files_before_staging(
    source_name: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    source = preloader if source_name == "preloader" else provenance
    payload = source.read_bytes()
    source.unlink()
    outside = tmp_path / f"outside-{source_name}"
    outside.write_bytes(payload)
    source.symlink_to(outside)
    before = _tree_snapshot(installed_official_game)
    stage_called = False

    def observe_stage(*args, **kwargs):
        nonlocal stage_called
        stage_called = True
        raise AssertionError("unsafe request must fail before staging")

    monkeypatch.setattr(oracle_install, "_create_compat_staging", observe_stage)

    with pytest.raises(InstallError, match="safe regular file"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert not stage_called
    assert _tree_snapshot(installed_official_game) == before


def test_deploy_preloader_rejects_an_unsafe_recovery_parent_before_staging(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    outside = tmp_path / "outside-recovery"
    outside.mkdir()
    (installed_official_game / ".ssr-oracle-recovery").symlink_to(
        outside, target_is_directory=True
    )
    before = _tree_snapshot(installed_official_game)
    stage_called = False

    def observe_stage(*args, **kwargs):
        nonlocal stage_called
        stage_called = True
        raise AssertionError("unsafe recovery must fail before staging")

    monkeypatch.setattr(oracle_install, "_create_compat_staging", observe_stage)

    with pytest.raises(InstallError, match="recovery parent"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert not stage_called
    assert _tree_snapshot(installed_official_game) == before


def test_deploy_preloader_rejects_provenance_changed_during_preflight(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    valid = provenance.read_bytes()
    forged = json.loads(valid)
    forged["patch_sha256"] = "9" * 64
    provenance.write_bytes(canonical_json(forged))
    diverted = provenance.with_name("diverted-provenance.json")
    original_load = oracle_install.load_provenance
    stage_called = False

    def swap_then_load(path: Path, observed_trust: CompatTrust):
        provenance.replace(diverted)
        provenance.write_bytes(valid)
        return original_load(path, observed_trust)

    def observe_stage(*args, **kwargs):
        nonlocal stage_called
        stage_called = True
        raise AssertionError("changed provenance must fail before staging")

    monkeypatch.setattr(oracle_install, "load_provenance", swap_then_load)
    monkeypatch.setattr(oracle_install, "_create_compat_staging", observe_stage)
    before = _tree_snapshot(installed_official_game)

    with pytest.raises(InstallError, match="provenance is invalid"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert not stage_called
    assert _tree_snapshot(installed_official_game) == before


def test_deploy_preloader_preserves_a_partially_written_staging_tree(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    before = _tree_snapshot_without_recovery(installed_official_game)
    original_checkpoint = oracle_install._deploy_preloader_checkpoint

    def fail_staged_file(boundary: str) -> None:
        if boundary == "stage_backup_fsync":
            raise InstallError("injected staging durability failure")
        original_checkpoint(boundary)

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_staged_file
    )

    with pytest.raises(InstallError, match="staging durability"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert _tree_snapshot_without_recovery(installed_official_game) == before
    assert not tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )
    preserved_backup = tuple(
        (
            installed_official_game / ".ssr-oracle-recovery"
        ).glob(
            "*/cleanup/directory-*/BepInEx/"
            ".ssr-oracle-backup/BepInEx.Preloader.dll"
        )
    )
    assert len(preserved_backup) == 1
    assert preserved_backup[0].read_bytes() == OFFICIAL_BYTES


@pytest.mark.parametrize(
    "boundary",
    [
        "staging_root_mkdir",
        "staging_root_child_fsync",
        "staging_root_parent_fsync",
        "staging_bepinex_mkdir",
        "staging_bepinex_child_fsync",
        "staging_bepinex_parent_fsync",
        "staging_backup_dir_mkdir",
        "staging_backup_dir_child_fsync",
        "staging_backup_dir_parent_fsync",
        "staging_compat_dir_mkdir",
        "staging_compat_dir_child_fsync",
        "staging_compat_dir_parent_fsync",
        "staging_core_dir_mkdir",
        "staging_core_dir_child_fsync",
        "staging_core_dir_parent_fsync",
        "stage_backup_write",
        "stage_backup_fsync",
        "stage_backup_parent_fsync",
        "stage_provenance_write",
        "stage_provenance_fsync",
        "stage_provenance_parent_fsync",
        "stage_active_write",
        "stage_active_fsync",
        "stage_active_parent_fsync",
    ],
)
def test_deploy_preloader_stage_sub_boundaries_leave_game_exact(
    boundary: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    before = _tree_snapshot_without_recovery(installed_official_game)
    injected = False

    def fail_boundary(observed: str) -> None:
        nonlocal injected
        if not injected and observed == boundary:
            injected = True
            raise InstallError(f"injected {boundary} failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_boundary
    )

    with pytest.raises(InstallError, match=f"injected {boundary}"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert injected
    assert _tree_snapshot_without_recovery(installed_official_game) == before


@pytest.mark.parametrize(
    "boundary",
    [
        "live_backup_dir_mkdir",
        "live_backup_dir_child_fsync",
        "live_backup_dir_parent_fsync",
        "live_compat_dir_mkdir",
        "live_compat_dir_child_fsync",
        "live_compat_dir_parent_fsync",
    ],
)
def test_deploy_preloader_live_parent_sub_boundaries_leave_game_exact(
    boundary: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    before = _tree_snapshot_without_recovery(installed_official_game)
    injected = False

    def fail_boundary(observed: str) -> None:
        nonlocal injected
        if not injected and observed == boundary:
            injected = True
            raise InstallError(f"injected {boundary} failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_boundary
    )

    with pytest.raises(InstallError, match=f"injected {boundary}"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert injected
    assert _tree_snapshot_without_recovery(installed_official_game) == before


@pytest.mark.parametrize(
    "boundary",
    [
        "backup_post_rename_preopen",
        "backup_replace",
        "backup_staging_parent_fsync",
        "backup_live_parent_fsync",
        "provenance_post_rename_preopen",
        "provenance_replace",
        "provenance_staging_parent_fsync",
        "provenance_live_parent_fsync",
        "active_post_rename_preopen",
        "active_replace",
        "active_staging_parent_fsync",
        "active_live_parent_fsync",
        "manifest_temporary_write",
        "manifest_temporary_fsync",
        "manifest_post_rename_preopen",
        "manifest_replace",
        "manifest_parent_fsync",
    ],
)
def test_deploy_preloader_publish_sub_boundaries_restore_exact_state(
    boundary: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    active.chmod(0o640)
    manifest_path.chmod(0o600)
    active_before = (active.read_bytes(), _file_mode(active))
    manifest_before = (manifest_path.read_bytes(), _file_mode(manifest_path))
    injected = False

    def fail_boundary(observed: str) -> None:
        nonlocal injected
        if not injected and observed == boundary:
            injected = True
            raise InstallError(f"injected {boundary} failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_boundary
    )

    with pytest.raises(InstallError, match=f"injected {boundary}"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert injected
    assert (active.read_bytes(), _file_mode(active)) == active_before
    assert (
        manifest_path.read_bytes(),
        _file_mode(manifest_path),
    ) == manifest_before
    assert not (installed_official_game / BACKUP_ROOT).exists()
    assert not (installed_official_game / COMPAT_ROOT).exists()
    assert not tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )
    assert not tuple(
        installed_official_game.glob(
            f".{oracle_install.MANIFEST_NAME}.*.tmp"
        )
    )


def test_deploy_preloader_recovers_backup_when_post_replace_sync_fails(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    failed = False

    def fail_backup_sync(boundary: str) -> None:
        nonlocal failed
        if not failed and boundary == "backup_live_parent_fsync":
            failed = True
            raise InstallError("injected backup directory sync failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_backup_sync
    )

    with pytest.raises(InstallError, match="backup directory sync"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    recovered = tuple(
        (
            installed_official_game / ".ssr-oracle-recovery"
        ).glob(f"*/compat/{BACKUP_PATH}")
    )
    assert len(recovered) == 1
    assert recovered[0].read_bytes() == OFFICIAL_BYTES
    assert not (installed_official_game / BACKUP_ROOT).exists()


def test_deploy_preloader_rolls_back_when_staging_cleanup_fails(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    original_cleanup = oracle_install._cleanup_compat_staging_fd
    calls = 0

    def fail_once(root_handle, staging_handle, recovery_handle) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise InstallError("injected staging cleanup failure")
        original_cleanup(root_handle, staging_handle, recovery_handle)

    monkeypatch.setattr(
        oracle_install, "_cleanup_compat_staging_fd", fail_once
    )

    with pytest.raises(InstallError, match="staging cleanup failure"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    recovery = installed_official_game / ".ssr-oracle-recovery"
    assert len(tuple(recovery.glob(f"*/compat/{BACKUP_PATH}"))) == 1
    assert len(tuple(recovery.glob(f"*/compat/{PROVENANCE_PATH}"))) == 1
    assert not (installed_official_game / BACKUP_ROOT).exists()
    assert not (installed_official_game / COMPAT_ROOT).exists()


@pytest.mark.parametrize(
    "cleanup_boundary",
    [
        "staging_cleanup_preserve_source_parent_fsync",
        "staging_cleanup_preserve_destination_parent_fsync",
    ],
)
def test_deploy_preloader_cleanup_boundary_failure_rolls_back_exactly(
    cleanup_boundary: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    publication_failed = False
    failed = False

    def fail_cleanup(observed: str) -> None:
        nonlocal publication_failed, failed
        if not publication_failed and observed == "backup_replace":
            publication_failed = True
            raise InstallError("original publication failure")
        if publication_failed and not failed and observed == cleanup_boundary:
            failed = True
            raise InstallError(f"injected {cleanup_boundary} failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_cleanup
    )

    with pytest.raises(
        InstallError,
        match=(
            rf"original publication failure.*"
            rf"injected {cleanup_boundary} failure"
        ),
    ):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert publication_failed and failed
    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    recovery_parent = installed_official_game / ".ssr-oracle-recovery"
    recovered_backup = tuple(
        recovery_parent.glob(f"*/compat/{BACKUP_PATH}")
    )
    assert len(recovered_backup) == 1
    assert recovered_backup[0].read_bytes() == OFFICIAL_BYTES
    assert not tuple(
        recovery_parent.glob(f"*/compat/{PROVENANCE_PATH}")
    )
    assert not (installed_official_game / BACKUP_ROOT).exists()
    assert not (installed_official_game / COMPAT_ROOT).exists()
    assert not tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )


def test_deploy_preloader_preserves_complete_staging_tree_in_recovery(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
):
    preloader, provenance = deploy_request
    oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )

    preserved = tuple(
        (
            installed_official_game / ".ssr-oracle-recovery"
        ).glob("*/cleanup/directory-*/BepInEx")
    )
    assert len(preserved) == 1
    assert (preserved[0] / ".ssr-oracle-backup").is_dir()
    assert (preserved[0] / ".ssr-oracle-compat").is_dir()
    assert (preserved[0] / "core").is_dir()


def test_deploy_preloader_preserves_substituted_staging_root_exactly(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    original_renameatx = oracle_install._renameatx
    substituted = False
    replacement_identity: tuple[int, int] | None = None

    def substitute_staging_root(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal replacement_identity, substituted
        if (
            not substituted
            and description
            == "preserve staging_cleanup directory"
        ):
            substituted = True
            os.rename(
                source,
                "owned-staging",
                src_dir_fd=source_parent.fd,
                dst_dir_fd=destination_parent.fd,
            )
            os.mkdir(source, dir_fd=source_parent.fd)
            replacement = os.stat(
                source,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            replacement_identity = (
                replacement.st_dev,
                replacement.st_ino,
            )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install,
        "_renameatx",
        substitute_staging_root,
    )

    oracle_install.deploy_preloader(
        installed_official_game,
        preloader,
        provenance,
        repo_root=Path("/unused"),
    )

    assert substituted
    assert replacement_identity is not None
    remaining = tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )
    assert len(remaining) == 1 and remaining[0].is_dir()
    observed = remaining[0].stat()
    assert (observed.st_dev, observed.st_ino) == replacement_identity
    recovered = tuple(
        (
            installed_official_game / ".ssr-oracle-recovery"
        ).glob("*/cleanup/owned-staging/BepInEx")
    )
    assert len(recovered) == 1


def test_deploy_preloader_revalidates_live_parents_after_staging(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    outside = tmp_path / "outside-backup"
    outside.mkdir()
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    original_create = oracle_install._create_live_compat_directories

    def redirect_after_parent_creation(bep_in_ex, recovery):
        created = original_create(bep_in_ex, recovery)
        backup_root = installed_official_game / BACKUP_ROOT
        diverted = tmp_path / "diverted-live-backup"
        backup_root.replace(diverted)
        backup_root.symlink_to(outside, target_is_directory=True)
        return created

    monkeypatch.setattr(
        oracle_install,
        "_create_live_compat_directories",
        redirect_after_parent_creation,
    )

    with pytest.raises(InstallError, match="directory entry"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    assert not (outside / "BepInEx.Preloader.dll").exists()


def test_deploy_preloader_publish_is_pinned_against_parent_swap_inside_replace(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    outside = tmp_path / "outside-replace"
    outside.mkdir()
    backup_root = installed_official_game / BACKUP_ROOT
    diverted = tmp_path / "diverted-backup"
    original_renameatx = oracle_install._renameatx
    swapped = False
    outside_write_observed = False

    def swap_inside_replace(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal outside_write_observed, swapped
        if (
            not swapped
            and source == "BepInEx.Preloader.dll"
            and destination == "BepInEx.Preloader.dll"
            and description.endswith("backup")
            and backup_root.is_dir()
        ):
            swapped = True
            backup_root.replace(diverted)
            backup_root.symlink_to(outside, target_is_directory=True)
        result = original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )
        if swapped and (outside / "BepInEx.Preloader.dll").exists():
            outside_write_observed = True
        return result

    monkeypatch.setattr(
        oracle_install, "_renameatx", swap_inside_replace
    )

    with pytest.raises(InstallError):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert swapped
    assert not outside_write_observed
    assert not (outside / "BepInEx.Preloader.dll").exists()


def test_deploy_preloader_exclusive_publish_preserves_racing_leaf(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    original_renameatx = oracle_install._renameatx
    raced = False

    def race_backup_leaf(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal raced
        if not raced and description.endswith("backup"):
            raced = True
            descriptor = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=destination_parent.fd,
            )
            os.write(descriptor, b"unrelated")
            os.close(descriptor)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_renameatx", race_backup_leaf
    )

    with pytest.raises(InstallError):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert raced
    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    assert (
        installed_official_game / BACKUP_PATH
    ).read_bytes() == b"unrelated"


def test_deploy_preloader_directory_publish_preserves_racing_source(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    held = tmp_path / "held-live-backup-directory"
    original_renameatx = oracle_install._renameatx
    raced = False

    def race_directory_source(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal raced
        if (
            not raced
            and description
            == "publish live backup directory directory"
        ):
            raced = True
            os.rename(source, held, src_dir_fd=source_parent.fd)
            os.mkdir(source, dir_fd=source_parent.fd)
            raced_directory = os.open(
                source,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=source_parent.fd,
            )
            try:
                descriptor = os.open(
                    "unrelated",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=raced_directory,
                )
                os.write(descriptor, b"keep")
                os.close(descriptor)
            finally:
                os.close(raced_directory)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_renameatx", race_directory_source
    )

    with pytest.raises(InstallError, match="entry changed"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert raced
    assert held.is_dir()
    assert (
        installed_official_game / BACKUP_ROOT / "unrelated"
    ).read_bytes() == b"keep"


@pytest.mark.parametrize(
    ("raced_target", "compensation_boundary"),
    [
        ("active", None),
        ("manifest", None),
        ("active", "active_race_restore_source_parent_fsync"),
        ("active", "active_race_restore_destination_parent_fsync"),
        ("manifest", "manifest_race_restore_source_parent_fsync"),
    ],
)
def test_deploy_preloader_swap_restores_racing_existing_leaf(
    raced_target: str,
    compensation_boundary: str | None,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    target = active if raced_target == "active" else manifest_path
    original_payload = target.read_bytes()
    held = tmp_path / f"held-{raced_target}"
    unrelated = f"unrelated-{raced_target}".encode()
    original_renameatx = oracle_install._renameatx
    raced = False

    def race_existing_leaf(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal raced
        should_race = (
            raced_target == "active"
            and description == "publish compatibility artifact active"
        ) or (
            raced_target == "manifest"
            and description == "atomically swap manifest"
        )
        if not raced and should_race:
            raced = True
            target.replace(held)
            target.write_bytes(unrelated)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_renameatx", race_existing_leaf
    )
    if compensation_boundary is not None:
        monkeypatch.setattr(
            oracle_install,
            "_deploy_preloader_checkpoint",
            lambda boundary: (
                (_ for _ in ()).throw(
                    InstallError(
                        f"injected {compensation_boundary} failure"
                    )
                )
                if boundary == compensation_boundary
                else None
            ),
        )

    expected_error = (
        f"injected {compensation_boundary} failure"
        if compensation_boundary is not None
        else "changed"
    )
    with pytest.raises(InstallError, match=expected_error):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert raced
    assert target.read_bytes() == unrelated
    assert held.read_bytes() == original_payload
    if raced_target == "manifest":
        assert active.read_bytes() == OFFICIAL_BYTES
    assert not tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )
    assert not tuple(
        installed_official_game.glob(
            f".{oracle_install.MANIFEST_NAME}.*.tmp"
        )
    )


@pytest.mark.parametrize(
    ("boundary", "recovered"),
    [
        ("backup", {BACKUP_PATH}),
        ("provenance", {BACKUP_PATH, PROVENANCE_PATH}),
        ("active", {BACKUP_PATH, PROVENANCE_PATH}),
        ("manifest", {BACKUP_PATH, PROVENANCE_PATH}),
    ],
)
def test_deploy_preloader_failure_boundaries_restore_exact_state_and_recover(
    boundary: str,
    recovered: set[str],
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    active.chmod(0o640)
    manifest_path.chmod(0o600)
    active_before = active.read_bytes()
    manifest_before = manifest_path.read_bytes()
    active_mode = _file_mode(active)
    manifest_mode = _file_mode(manifest_path)

    def fail_at(observed: str) -> None:
        if observed == boundary:
            raise InstallError(f"injected {boundary} publication failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_at, raising=False
    )

    with pytest.raises(InstallError, match=f"injected {boundary}"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert active.read_bytes() == active_before
    assert manifest_path.read_bytes() == manifest_before
    assert _file_mode(active) == active_mode
    assert _file_mode(manifest_path) == manifest_mode
    assert not (installed_official_game / BACKUP_ROOT).exists()
    assert not (installed_official_game / COMPAT_ROOT).exists()
    recoveries = tuple(
        (installed_official_game / ".ssr-oracle-recovery").glob("*")
    )
    assert len(recoveries) == 1
    compat = recoveries[0] / "compat"
    observed = {
        path.relative_to(compat).as_posix()
        for path in compat.rglob("*")
        if path.is_file()
    }
    assert observed == recovered
    if BACKUP_PATH in recovered:
        backup = compat / BACKUP_PATH
        assert backup.read_bytes() == OFFICIAL_BYTES
        assert _file_mode(backup) == active_mode
    if PROVENANCE_PATH in recovered:
        deployed_provenance = compat / PROVENANCE_PATH
        assert deployed_provenance.read_bytes() == provenance.read_bytes()
        assert _file_mode(deployed_provenance) == 0o644


def test_deploy_preloader_retries_an_exclusive_recovery_collision(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    recovery_parent = installed_official_game / ".ssr-oracle-recovery"
    recovery_parent.mkdir()
    collision = recovery_parent / "collision"
    collision.mkdir()
    (collision / "keep").write_bytes(b"user")
    names = iter(("collision", "fresh"))
    monkeypatch.setattr(
        oracle_install, "_compat_recovery_name", lambda: next(names), raising=False
    )
    monkeypatch.setattr(
        oracle_install,
        "_deploy_preloader_checkpoint",
        lambda boundary: (
            (_ for _ in ()).throw(InstallError("injected failure"))
            if boundary == "backup"
            else None
        ),
        raising=False,
    )

    with pytest.raises(InstallError, match="injected failure"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert (collision / "keep").read_bytes() == b"user"
    assert (
        recovery_parent / "fresh/compat" / BACKUP_PATH
    ).read_bytes() == OFFICIAL_BYTES


@pytest.mark.parametrize(
    "recovery_boundary",
    [
        "recovery_parent_mkdir",
        "recovery_parent_child_fsync",
        "recovery_parent_parent_fsync",
        "recovery_run_mkdir",
        "recovery_run_child_fsync",
        "recovery_run_parent_fsync",
        "recovery_compat_mkdir",
        "recovery_compat_child_fsync",
        "recovery_compat_parent_fsync",
        "recovery_bepinex_mkdir",
        "recovery_bepinex_child_fsync",
        "recovery_bepinex_parent_fsync",
        "recovery_backup_dir_mkdir",
        "recovery_backup_dir_child_fsync",
        "recovery_backup_dir_parent_fsync",
        "recovery_provenance_dir_mkdir",
        "recovery_provenance_dir_child_fsync",
        "recovery_provenance_dir_parent_fsync",
        "recovery_cleanup_dir_mkdir",
        "recovery_cleanup_dir_child_fsync",
        "recovery_cleanup_dir_parent_fsync",
    ],
)
def test_deploy_preloader_recovery_allocation_failure_preserves_scaffolding(
    recovery_boundary: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    recovery_failed = False
    deletion_calls: list[str] = []
    original_unlink = oracle_install.os.unlink
    original_rmdir = oracle_install.os.rmdir

    def fail_boundaries(observed: str) -> None:
        nonlocal recovery_failed
        if not recovery_failed and observed == recovery_boundary:
            recovery_failed = True
            raise InstallError(f"injected {recovery_boundary} failure")

    def record_unlink(*args, **kwargs):
        deletion_calls.append("unlink")
        return original_unlink(*args, **kwargs)

    def record_rmdir(*args, **kwargs):
        deletion_calls.append("rmdir")
        return original_rmdir(*args, **kwargs)

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_boundaries
    )
    monkeypatch.setattr(oracle_install.os, "unlink", record_unlink)
    monkeypatch.setattr(oracle_install.os, "rmdir", record_rmdir)

    with pytest.raises(
        InstallError,
        match=rf"injected {recovery_boundary} failure.*preserved",
    ):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert recovery_failed
    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    recovery_parent = installed_official_game / ".ssr-oracle-recovery"
    assert recovery_parent.is_dir()
    assert not deletion_calls
    assert not tuple(
        installed_official_game.glob(".ssr-oracle-compat-staging-*")
    )
    assert not (installed_official_game / BACKUP_ROOT).exists()
    assert not (installed_official_game / COMPAT_ROOT).exists()


def test_deploy_preloader_allocates_one_recovery_before_staging_and_reuses_it(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    original_allocate = oracle_install._allocate_compat_recovery_fd
    original_staging = oracle_install._create_compat_staging
    allocations = []

    def record_allocate(*args, **kwargs):
        recovery = original_allocate(*args, **kwargs)
        allocations.append(recovery)
        return recovery

    def require_recovery_before_staging(*args, **kwargs):
        assert len(allocations) == 1
        return original_staging(*args, **kwargs)

    monkeypatch.setattr(
        oracle_install, "_allocate_compat_recovery_fd", record_allocate
    )
    monkeypatch.setattr(
        oracle_install, "_create_compat_staging", require_recovery_before_staging
    )
    monkeypatch.setattr(
        oracle_install,
        "_deploy_preloader_checkpoint",
        lambda boundary: (
            (_ for _ in ()).throw(InstallError("injected active failure"))
            if boundary == "active"
            else None
        ),
    )

    with pytest.raises(InstallError, match="injected active failure"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert len(allocations) == 1
    run = (
        installed_official_game
        / ".ssr-oracle-recovery"
        / allocations[0].run_name
    )
    assert (run / "cleanup").is_dir()
    assert (run / "compat" / BACKUP_PATH).read_bytes() == OFFICIAL_BYTES
    assert (
        run / "compat" / PROVENANCE_PATH
    ).read_bytes() == provenance.read_bytes()
    cleanup_directories = tuple(
        path for path in (run / "cleanup").iterdir() if path.is_dir()
    )
    assert len(cleanup_directories) == 3
    assert sum(not any(path.iterdir()) for path in cleanup_directories) == 2


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_preserve_owned_entry_moves_exact_inode_into_cleanup(
    kind: str,
    tmp_path: Path,
):
    game_path = tmp_path / "game"
    source_path = game_path / "source"
    game_path.mkdir()
    source_path.mkdir()
    owned = source_path / "owned"
    if kind == "file":
        owned.write_bytes(b"owned")
    else:
        owned.mkdir()
    observed = owned.stat()
    identity = oracle_install._FileIdentity(
        observed.st_dev,
        observed.st_ino,
    )
    root = oracle_install._open_absolute_directory(game_path, "test game")
    source = oracle_install._open_child_directory(
        root, "source", "test source"
    )
    recovery = oracle_install._allocate_compat_recovery_fd(root)
    try:
        leaf = oracle_install._preserve_owned_entry_at(
            source,
            "owned",
            kind,
            identity,
            recovery,
            "test cleanup",
        )
    finally:
        oracle_install._close_recovery(recovery)
        source.close()
        root.close()

    assert not owned.exists()
    preserved = tuple(
        (game_path / ".ssr-oracle-recovery").glob(f"*/cleanup/{leaf}")
    )
    assert len(preserved) == 1
    recovered = preserved[0].stat()
    assert (recovered.st_dev, recovered.st_ino) == (
        identity.device,
        identity.inode,
    )
    assert preserved[0].is_file() if kind == "file" else preserved[0].is_dir()


def test_recovery_allocator_refuses_substituted_temporary_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_path = tmp_path / "game"
    game_path.mkdir()
    root = oracle_install._open_absolute_directory(game_path, "test game")
    original_renameatx = oracle_install._renameatx
    substituted = False

    def substitute_temporary(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal substituted
        if (
            not substituted
            and description
            == "publish compatibility recovery run directory"
        ):
            substituted = True
            os.rename(
                source,
                "held-pinned-run",
                src_dir_fd=source_parent.fd,
                dst_dir_fd=source_parent.fd,
            )
            os.mkdir(source, dir_fd=source_parent.fd)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_renameatx", substitute_temporary
    )
    try:
        with pytest.raises(InstallError, match="directory entry changed"):
            oracle_install._allocate_compat_recovery_fd(root)
    finally:
        root.close()

    assert substituted
    recovery_parent = game_path / ".ssr-oracle-recovery"
    held = recovery_parent / "held-pinned-run"
    published = tuple(
        path
        for path in recovery_parent.iterdir()
        if path.name != "held-pinned-run"
    )
    assert held.is_dir()
    assert len(published) == 1
    assert published[0].is_dir()
    assert held.stat().st_ino != published[0].stat().st_ino


def test_recovery_allocator_propagates_noncollision_publish_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_path = tmp_path / "game"
    game_path.mkdir()
    root = oracle_install._open_absolute_directory(game_path, "test game")
    original_renameatx = oracle_install._renameatx
    run_publications = 0

    def fail_run_publish(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal run_publications
        if description == "publish compatibility recovery run directory":
            run_publications += 1
            raise oracle_install._RenameAtError(
                errno.EIO, "injected recovery-run publish I/O failure"
            )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(oracle_install, "_renameatx", fail_run_publish)
    try:
        with pytest.raises(
            InstallError, match="injected recovery-run publish I/O failure"
        ):
            oracle_install._allocate_compat_recovery_fd(root)
    finally:
        root.close()

    assert run_publications == 1
    retained = tuple(
        (game_path / ".ssr-oracle-recovery").iterdir()
    )
    assert len(retained) == 1
    assert retained[0].is_dir()


def test_preserve_owned_entry_retries_only_cleanup_leaf_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_path = tmp_path / "game"
    source_path = game_path / "source"
    game_path.mkdir()
    source_path.mkdir()
    owned = source_path / "owned"
    owned.write_bytes(b"owned")
    observed = owned.stat()
    identity = oracle_install._FileIdentity(
        observed.st_dev, observed.st_ino
    )
    root = oracle_install._open_absolute_directory(game_path, "test game")
    source = oracle_install._open_child_directory(
        root, "source", "test source"
    )
    recovery = oracle_install._allocate_compat_recovery_fd(root)
    collision = game_path / ".ssr-oracle-recovery" / recovery.run_name
    collision = collision / "cleanup/file-collision"
    collision.write_bytes(b"unrelated")
    names = iter(("collision", "fresh"))
    monkeypatch.setattr(
        oracle_install.secrets, "token_hex", lambda _: next(names)
    )
    try:
        leaf = oracle_install._preserve_owned_entry_at(
            source,
            "owned",
            "file",
            identity,
            recovery,
            "test cleanup",
        )
    finally:
        oracle_install._close_recovery(recovery)
        source.close()
        root.close()

    assert leaf == "file-fresh"
    assert collision.read_bytes() == b"unrelated"
    assert (collision.parent / leaf).read_bytes() == b"owned"


def test_preserve_owned_entry_reports_cleanup_leaf_collision_exhaustion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_path = tmp_path / "game"
    source_path = game_path / "source"
    game_path.mkdir()
    source_path.mkdir()
    owned = source_path / "owned"
    owned.write_bytes(b"owned")
    observed = owned.stat()
    identity = oracle_install._FileIdentity(
        observed.st_dev, observed.st_ino
    )
    root = oracle_install._open_absolute_directory(game_path, "test game")
    source = oracle_install._open_child_directory(
        root, "source", "test source"
    )
    recovery = oracle_install._allocate_compat_recovery_fd(root)
    cleanup = (
        game_path
        / ".ssr-oracle-recovery"
        / recovery.run_name
        / "cleanup"
    )
    (cleanup / "file-collision").write_bytes(b"unrelated")
    monkeypatch.setattr(
        oracle_install.secrets, "token_hex", lambda _: "collision"
    )
    try:
        with pytest.raises(
            InstallError,
            match="cannot allocate an exclusive cleanup leaf",
        ):
            oracle_install._preserve_owned_entry_at(
                source,
                "owned",
                "file",
                identity,
                recovery,
                "test cleanup",
            )
    finally:
        oracle_install._close_recovery(recovery)
        source.close()
        root.close()

    assert owned.read_bytes() == b"owned"
    assert (cleanup / "file-collision").read_bytes() == b"unrelated"


def test_preserve_owned_entry_propagates_noncollision_rename_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_path = tmp_path / "game"
    source_path = game_path / "source"
    game_path.mkdir()
    source_path.mkdir()
    owned = source_path / "owned"
    owned.write_bytes(b"owned")
    observed = owned.stat()
    identity = oracle_install._FileIdentity(
        observed.st_dev, observed.st_ino
    )
    root = oracle_install._open_absolute_directory(game_path, "test game")
    source = oracle_install._open_child_directory(
        root, "source", "test source"
    )
    recovery = oracle_install._allocate_compat_recovery_fd(root)

    def fail_rename(*args, **kwargs):
        raise oracle_install._RenameAtError(
            errno.EIO, "injected cleanup rename I/O failure"
        )

    monkeypatch.setattr(oracle_install, "_renameatx", fail_rename)
    try:
        with pytest.raises(
            InstallError, match="injected cleanup rename I/O failure"
        ):
            oracle_install._preserve_owned_entry_at(
                source,
                "owned",
                "file",
                identity,
                recovery,
                "test cleanup",
            )
    finally:
        oracle_install._close_recovery(recovery)
        source.close()
        root.close()

    assert owned.read_bytes() == b"owned"


def test_preserve_owned_entry_fsync_failure_retains_moved_inode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_path = tmp_path / "game"
    source_path = game_path / "source"
    game_path.mkdir()
    source_path.mkdir()
    owned = source_path / "owned"
    owned.write_bytes(b"owned")
    observed = owned.stat()
    identity = oracle_install._FileIdentity(
        observed.st_dev, observed.st_ino
    )
    root = oracle_install._open_absolute_directory(game_path, "test game")
    source = oracle_install._open_child_directory(
        root, "source", "test source"
    )
    recovery = oracle_install._allocate_compat_recovery_fd(root)

    def fail_source_fsync(boundary: str) -> None:
        if boundary == "test_cleanup_preserve_source_parent_fsync":
            raise InstallError("injected cleanup fsync failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_source_fsync
    )
    try:
        with pytest.raises(
            InstallError,
            match=r"was preserved.*injected cleanup fsync failure",
        ):
            oracle_install._preserve_owned_entry_at(
                source,
                "owned",
                "file",
                identity,
                recovery,
                "test_cleanup",
            )
    finally:
        oracle_install._close_recovery(recovery)
        source.close()
        root.close()

    assert not owned.exists()
    preserved = tuple(
        (
            game_path
            / ".ssr-oracle-recovery"
            / recovery.run_name
            / "cleanup"
        ).iterdir()
    )
    assert len(preserved) == 1
    recovered = preserved[0].stat()
    assert (recovered.st_dev, recovered.st_ino) == (
        identity.device,
        identity.inode,
    )


def test_deploy_preloader_recovery_uses_retained_parent_descriptor(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    recovery_parent = installed_official_game / ".ssr-oracle-recovery"
    recovery_parent.mkdir()
    outside = tmp_path / "outside-recovery"
    outside.mkdir()
    diverted = installed_official_game / ".diverted-recovery"
    original_duplicate = oracle_install._duplicate_directory_handle
    swapped = False

    def swap_before_duplicate(handle, label):
        nonlocal swapped
        if not swapped and label == "recovery parent":
            swapped = True
            recovery_parent.replace(diverted)
            recovery_parent.symlink_to(outside, target_is_directory=True)
        return original_duplicate(handle, label)

    def fail_after_active(boundary: str) -> None:
        if boundary == "active":
            raise InstallError("original publication failure")

    monkeypatch.setattr(
        oracle_install,
        "_duplicate_directory_handle",
        swap_before_duplicate,
    )
    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_after_active
    )

    with pytest.raises(InstallError, match="original publication failure"):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert swapped
    assert not tuple(outside.iterdir())
    assert len(tuple(diverted.glob(f"*/compat/{BACKUP_PATH}"))) == 1
    assert len(tuple(diverted.glob(f"*/compat/{PROVENANCE_PATH}"))) == 1


@pytest.mark.parametrize(
    "compensation_boundary",
    [
        None,
        "recovery_backup_race_restore_source_parent_fsync",
        "recovery_backup_race_restore_destination_parent_fsync",
    ],
)
def test_deploy_preloader_recovery_move_preserves_substituted_source(
    compensation_boundary: str | None,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    held = tmp_path / "held-recovery-backup"
    original_renameatx = oracle_install._renameatx
    substituted = False

    def substitute_recovery_source(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal substituted
        if (
            not substituted
            and description == "preserve compatibility backup"
        ):
            substituted = True
            os.rename(source, held, src_dir_fd=source_parent.fd)
            descriptor = os.open(
                source,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=source_parent.fd,
            )
            os.write(descriptor, b"unrelated recovery source")
            os.close(descriptor)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    primary_failed = False

    def fail_after_active(boundary: str) -> None:
        nonlocal primary_failed
        if boundary == "active":
            primary_failed = True
            raise InstallError("original publication failure")
        if primary_failed and boundary == compensation_boundary:
            raise InstallError(
                f"injected {compensation_boundary} failure"
            )

    monkeypatch.setattr(
        oracle_install, "_renameatx", substitute_recovery_source
    )
    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_after_active
    )

    recovery_error = (
        rf"injected {compensation_boundary} failure"
        if compensation_boundary is not None
        else r"changed during recovery move"
    )
    with pytest.raises(
        InstallError,
        match=rf"original publication failure.*{recovery_error}",
    ):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert substituted
    assert held.read_bytes() == OFFICIAL_BYTES
    assert (
        installed_official_game / BACKUP_PATH
    ).read_bytes() == b"unrelated recovery source"
    assert (
        installed_official_game / ACTIVE_PATH
    ).read_bytes() == OFFICIAL_BYTES


@pytest.mark.parametrize(
    "recovery_boundary",
    [
        "recovery_backup_post_rename_preopen",
        "recovery_backup_move",
        "recovery_backup_source_fsync",
        "recovery_backup_destination_fsync",
        "recovery_provenance_post_rename_preopen",
        "recovery_provenance_move",
        "recovery_provenance_source_fsync",
        "recovery_provenance_destination_fsync",
    ],
)
def test_deploy_preloader_recovery_move_failure_preserves_one_exact_copy(
    recovery_boundary: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    active = installed_official_game / ACTIVE_PATH
    manifest_path = installed_official_game / oracle_install.MANIFEST_NAME
    before = (active.read_bytes(), manifest_path.read_bytes())
    primary_failed = False
    recovery_failed = False

    def fail_boundaries(observed: str) -> None:
        nonlocal primary_failed, recovery_failed
        if not primary_failed and observed == "active":
            primary_failed = True
            raise InstallError("original publication failure")
        if (
            primary_failed
            and not recovery_failed
            and observed == recovery_boundary
        ):
            recovery_failed = True
            raise InstallError(f"injected {recovery_boundary} failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_boundaries
    )

    with pytest.raises(
        InstallError,
        match=(
            rf"original publication failure.*"
            rf"injected {recovery_boundary} failure"
        ),
    ):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )

    assert primary_failed and recovery_failed
    assert (active.read_bytes(), manifest_path.read_bytes()) == before
    recovery_parent = installed_official_game / ".ssr-oracle-recovery"
    recovered_backup = tuple(
        recovery_parent.glob(f"*/compat/{BACKUP_PATH}")
    )
    recovered_provenance = tuple(
        recovery_parent.glob(f"*/compat/{PROVENANCE_PATH}")
    )
    assert len(recovered_backup) == 1
    assert recovered_backup[0].read_bytes() == OFFICIAL_BYTES
    assert len(recovered_provenance) == 1
    assert recovered_provenance[0].read_bytes() == provenance.read_bytes()
    assert not (installed_official_game / BACKUP_ROOT).exists()
    assert not (installed_official_game / COMPAT_ROOT).exists()


def test_deploy_preloader_surfaces_rollback_failure_with_original_error(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
):
    preloader, provenance = deploy_request
    monkeypatch.setattr(
        oracle_install,
        "_deploy_preloader_checkpoint",
        lambda boundary: (
            (_ for _ in ()).throw(InstallError("original publication failure"))
            if boundary == "backup"
            else None
        ),
        raising=False,
    )
    monkeypatch.setattr(
        oracle_install,
        "_preserve_compat_recovery_fd",
        lambda *args, **kwargs: (
            (_ for _ in ()).throw(InstallError("recovery write failure"))
        ),
        raising=False,
    )

    with pytest.raises(
        InstallError,
        match=r"original publication failure.*rollback failed.*recovery write failure",
    ):
        oracle_install.deploy_preloader(
            installed_official_game,
            preloader,
            provenance,
            repo_root=Path("/unused"),
        )


def test_cli_deploy_preloader_prints_canonical_manifest(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
):
    preloader, provenance = deploy_request

    result = main(
        [
            "deploy-preloader",
            "--game-root",
            str(installed_official_game),
            "--preloader",
            str(preloader),
            "--provenance",
            str(provenance),
            "--repo-root",
            "/unused",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert captured.err == ""
    assert captured.out == (
        json.dumps(
            oracle_install._manifest_to_dict(
                oracle_install._load_manifest(installed_official_game)
            ),
            sort_keys=True,
        )
        + "\n"
    )


def test_cli_deploy_preloader_reports_one_error_line(
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
):
    preloader, provenance = deploy_request
    preloader.write_bytes(b"unreviewed")

    result = main(
        [
            "deploy-preloader",
            "--game-root",
            str(installed_official_game),
            "--preloader",
            str(preloader),
            "--provenance",
            str(provenance),
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err.startswith("error: ")
    assert captured.err.count("\n") == 1


@pytest.mark.parametrize(
    "loop_location", ["repository", "game", "input"]
)
def test_cli_deploy_preloader_normalizes_symlink_loop_errors(
    loop_location: str,
    installed_official_game: Path,
    deploy_request: tuple[Path, Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    preloader, provenance = deploy_request
    loop = tmp_path / f"{loop_location}-loop"
    loop.symlink_to(loop.name)
    game_root = installed_official_game
    repository = Path("/unused")
    if loop_location == "repository":
        repository = loop
    elif loop_location == "game":
        game_root = loop
    else:
        preloader = loop / "reviewed-preloader.dll"

    result = main(
        [
            "deploy-preloader",
            "--game-root",
            str(game_root),
            "--preloader",
            str(preloader),
            "--provenance",
            str(provenance),
            "--repo-root",
            str(repository),
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err.startswith("error: ")
    assert captured.err.count("\n") == 1


def test_atomic_replace_composes_temporary_cleanup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    parent_path = tmp_path / "parent"
    parent_path.mkdir()
    target = parent_path / "target"
    target.write_bytes(b"before")
    handle = oracle_install._open_absolute_directory(
        parent_path, "atomic test parent"
    )
    target_fd, target_snapshot = oracle_install._open_stable_child_file(
        handle, "target", "atomic test target"
    )
    os.close(target_fd)
    recovery = oracle_install._allocate_compat_recovery_fd(handle)
    observed_primary = False

    def fail_boundaries(boundary: str) -> None:
        nonlocal observed_primary
        if boundary == "atomic_test_temporary_fsync":
            observed_primary = True
            raise InstallError("original temporary failure")
        if (
            observed_primary
            and boundary
            == "atomic_test_temporary_cleanup_preserve_source_parent_fsync"
        ):
            raise InstallError("injected temporary cleanup failure")

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_boundaries
    )
    try:
        with pytest.raises(
            InstallError,
            match=(
                r"original temporary failure.*"
                r"injected temporary cleanup failure"
            ),
        ):
            oracle_install._atomic_replace_at(
                handle,
                "target",
                b"after",
                0o644,
                "atomic_test",
                target_snapshot,
                recovery,
            )
    finally:
        oracle_install._close_recovery(recovery)
        handle.close()

    assert target.read_bytes() == b"before"
    assert not tuple(parent_path.glob(".target.*.tmp"))
    assert len(
        tuple(
            (
                parent_path
                / ".ssr-oracle-recovery"
                / recovery.run_name
                / "cleanup"
            ).glob("file-*")
        )
    ) == 1


def test_atomic_replace_preserves_preexisting_temporary_name_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    parent_path = tmp_path / "parent"
    parent_path.mkdir()
    target = parent_path / "target"
    target.write_bytes(b"before")
    collision = parent_path / ".target.fixed.tmp"
    collision.write_bytes(b"unrelated")
    monkeypatch.setattr(
        oracle_install.secrets, "token_hex", lambda _: "fixed"
    )
    handle = oracle_install._open_absolute_directory(
        parent_path, "atomic test parent"
    )
    target_fd, target_snapshot = oracle_install._open_stable_child_file(
        handle, "target", "atomic test target"
    )
    os.close(target_fd)
    recovery = oracle_install._allocate_compat_recovery_fd(handle)
    try:
        with pytest.raises(InstallError, match="cleanup refused"):
            oracle_install._atomic_replace_at(
                handle,
                "target",
                b"after",
                0o644,
                "atomic_test",
                target_snapshot,
                recovery,
            )
    finally:
        oracle_install._close_recovery(recovery)
        handle.close()

    assert target.read_bytes() == b"before"
    assert collision.read_bytes() == b"unrelated"


def test_atomic_replace_cleanup_preserves_substituted_temporary_leaf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    parent_path = tmp_path / "parent"
    parent_path.mkdir()
    target = parent_path / "target"
    target.write_bytes(b"before")
    handle = oracle_install._open_absolute_directory(
        parent_path, "atomic test parent"
    )
    target_fd, target_snapshot = oracle_install._open_stable_child_file(
        handle, "target", "atomic test target"
    )
    os.close(target_fd)
    recovery = oracle_install._allocate_compat_recovery_fd(handle)
    recovery_path = (
        parent_path
        / ".ssr-oracle-recovery"
        / recovery.run_name
        / "cleanup"
    )
    held = recovery_path / "owned-temporary"
    original_renameatx = oracle_install._renameatx
    primary_failed = False
    substituted = False

    def fail_write(boundary: str) -> None:
        nonlocal primary_failed
        if boundary == "atomic_test_temporary_fsync":
            primary_failed = True
            raise InstallError("original temporary failure")

    def substitute_inside_quarantine(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal substituted
        if (
            primary_failed
            and not substituted
            and description
            == "preserve atomic_test_temporary_cleanup file"
        ):
            substituted = True
            os.rename(source, held, src_dir_fd=source_parent.fd)
            descriptor = os.open(
                source,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=source_parent.fd,
            )
            os.write(descriptor, b"unrelated temporary leaf")
            os.close(descriptor)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_deploy_preloader_checkpoint", fail_write
    )
    monkeypatch.setattr(
        oracle_install, "_renameatx", substitute_inside_quarantine
    )
    try:
        with pytest.raises(
            InstallError,
            match=r"original temporary failure",
        ):
            oracle_install._atomic_replace_at(
                handle,
                "target",
                b"after",
                0o644,
                "atomic_test",
                target_snapshot,
                recovery,
            )
    finally:
        oracle_install._close_recovery(recovery)
        handle.close()

    assert substituted
    assert target.read_bytes() == b"before"
    assert held.read_bytes() == b"after"
    temporary = tuple(parent_path.glob(".target.*.tmp"))
    assert len(temporary) == 1
    assert temporary[0].read_bytes() == b"unrelated temporary leaf"


def test_preserve_owned_file_keeps_concurrent_replacement_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_root = tmp_path / "game"
    parent_path = game_root / "parent"
    parent_path.mkdir(parents=True)
    owned = parent_path / "owned"
    owned.write_bytes(b"owned")
    observed = owned.stat()
    identity = oracle_install._FileIdentity(
        observed.st_dev,
        observed.st_ino,
    )
    parent = oracle_install._open_absolute_directory(
        parent_path,
        "cleanup test parent",
    )
    replacement_bytes = b"concurrent replacement"
    original_renameatx = oracle_install._renameatx
    substituted = False
    game = oracle_install._open_absolute_directory(game_root, "test game")
    recovery = oracle_install._allocate_compat_recovery_fd(game)
    recovery_root = (
        game_root / ".ssr-oracle-recovery" / recovery.run_name / "cleanup"
    )
    recovered = recovery_root / "owned-file"

    def substitute_after_quarantine(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal substituted
        if (
            not substituted
            and description == "preserve cleanup_test file"
        ):
            substituted = True
            os.rename(
                source,
                recovered,
                src_dir_fd=source_parent.fd,
            )
            descriptor = os.open(
                source,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=source_parent.fd,
            )
            os.write(descriptor, replacement_bytes)
            os.close(descriptor)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install,
        "_renameatx",
        substitute_after_quarantine,
    )
    cleanup_error: InstallError | None = None
    try:
        try:
            oracle_install._preserve_owned_file_at(
                parent,
                "owned",
                identity,
                recovery,
                "cleanup_test",
            )
        except InstallError as exc:
            cleanup_error = exc
    finally:
        oracle_install._close_recovery(recovery)
        game.close()
        parent.close()

    assert substituted
    assert owned.read_bytes() == replacement_bytes
    recovered_owned = [
        path
        for path in recovery_root.rglob("*")
        if path.is_file()
        and (path.stat().st_dev, path.stat().st_ino)
        == (identity.device, identity.inode)
    ]
    assert recovered_owned == [recovered]
    assert cleanup_error is None, str(cleanup_error)


@contextmanager
def _terminal_deletion_spies(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[list[str]]:
    calls: list[str] = []

    def forbidden(name: str):
        def spy(*args: object, **kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"terminal deletion called: {name}")
        return spy

    targets = (
        (os, "unlink"),
        (os, "remove"),
        (os, "rmdir"),
        (os, "removedirs"),
        (pathlib.Path, "unlink"),
        (pathlib.Path, "rmdir"),
        (shutil, "rmtree"),
    )
    with monkeypatch.context() as patch:
        for owner, name in targets:
            patch.setattr(owner, name, forbidden(f"{owner.__name__}.{name}"))
        try:
            yield calls
        finally:
            assert calls == []


@pytest.fixture
def restore_no_terminal_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    with _terminal_deletion_spies(monkeypatch):
        yield


def _restore_recovery_runs(game: Path) -> tuple[Path, ...]:
    parent = game / ".ssr-oracle-recovery"
    if not parent.is_dir():
        return ()
    return tuple(sorted(parent.iterdir()))


def _restore_paths(game: Path) -> dict[str, Path]:
    return {
        "active": game / ACTIVE_PATH,
        "backup": game / BACKUP_PATH,
        "provenance": game / PROVENANCE_PATH,
        "manifest": game / oracle_install.MANIFEST_NAME,
        "backup_directory": game / BACKUP_ROOT,
        "compat_directory": game / COMPAT_ROOT,
    }


def _restore_file_evidence(path: Path) -> tuple[int, int, int, bytes]:
    observed = path.stat(follow_symlinks=False)
    return (
        observed.st_dev,
        observed.st_ino,
        stat.S_IMODE(observed.st_mode),
        path.read_bytes(),
    )


def _restore_directory_evidence(path: Path) -> tuple[int, int, int]:
    observed = path.stat(follow_symlinks=False)
    return (
        observed.st_dev,
        observed.st_ino,
        stat.S_IMODE(observed.st_mode),
    )


def _restore_inode_locations(
    roots: tuple[Path, ...],
    identity: tuple[int, int],
) -> tuple[Path, ...]:
    locations: set[Path] = set()
    for root in roots:
        if not root.exists() or root.is_symlink():
            continue
        candidates = (root, *root.rglob("*"))
        for path in candidates:
            try:
                observed = path.stat(follow_symlinks=False)
            except OSError:
                continue
            if (observed.st_dev, observed.st_ino) == identity:
                locations.add(path)
    return tuple(sorted(locations))


def _assert_restore_evidence_at_original_or_recovery(
    game: Path,
    evidence: dict[str, tuple[Path, tuple[int, int], int, bytes | None]],
    *extra_roots: Path,
) -> None:
    runs = _restore_recovery_runs(game)
    roots = (game, *runs, *extra_roots)
    for label, (original, identity, mode, payload) in evidence.items():
        locations = _restore_inode_locations(roots, identity)
        assert len(locations) == 1, (label, identity, locations)
        location = locations[0]
        assert location == original or any(
            location == run or run in location.parents for run in runs
        ) or any(
            location == root or root in location.parents for root in extra_roots
        ), (label, location)
        assert stat.S_IMODE(location.stat(follow_symlinks=False).st_mode) == mode
        if payload is not None:
            assert location.read_bytes() == payload


def _restore_preflight_evidence(
    game: Path,
) -> dict[str, tuple[Path, tuple[int, int], int, bytes | None]]:
    paths = _restore_paths(game)
    evidence: dict[
        str, tuple[Path, tuple[int, int], int, bytes | None]
    ] = {}
    for label in ("active", "backup", "provenance", "manifest"):
        path = paths[label]
        device, inode, mode, payload = _restore_file_evidence(path)
        evidence[label] = (path, (device, inode), mode, payload)
    for label in ("backup_directory", "compat_directory"):
        path = paths[label]
        device, inode, mode = _restore_directory_evidence(path)
        evidence[label] = (path, (device, inode), mode, None)
    return evidence


def _install_restore_checkpoint_failure(
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    *,
    after_primary: bool = False,
) -> list[str]:
    observed: list[str] = []
    primary_failed = False

    def fail(observed_boundary: str) -> None:
        nonlocal primary_failed
        observed.append(observed_boundary)
        if after_primary and observed_boundary == "restore_forward_failure":
            primary_failed = True
            raise InstallError("injected restore forward failure")
        if observed_boundary == boundary and (not after_primary or primary_failed):
            raise InstallError(f"injected {boundary} failure")

    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        fail,
        raising=False,
    )
    return observed


def test_restore_tests_cannot_bypass_terminal_deletion_spies(
    restore_no_terminal_deletion: None,
) -> None:
    tree = ast.parse(
        Path("tests/test_oracle_install_compat.py").read_text(
            encoding="utf-8"
        )
    )
    missing_fixture = []
    for node in tree.body:
        if (
            not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            or not node.name.startswith("test_restore_")
        ):
            continue
        parameter_names = {
            argument.arg
            for argument in (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            )
        }
        if "restore_no_terminal_deletion" not in parameter_names:
            missing_fixture.append(node.name)
    assert not missing_fixture, missing_fixture


def test_restore_preloader_success_retains_exact_audit_evidence(
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    paths = _restore_paths(installed_patched_game)
    paths["active"].chmod(0o640)
    paths["backup"].chmod(0o604)
    paths["provenance"].chmod(0o640)
    patched_active_before = _restore_file_evidence(paths["active"])
    backup_before = _restore_file_evidence(paths["backup"])
    provenance_before = _restore_file_evidence(paths["provenance"])
    former_directory_identities = {
        (
            paths["backup_directory"].stat().st_dev,
            paths["backup_directory"].stat().st_ino,
        ),
        (
            paths["compat_directory"].stat().st_dev,
            paths["compat_directory"].stat().st_ino,
        ),
    }

    manifest, recovery = oracle_install.restore_preloader(
        installed_patched_game, repo_root=Path("/unused")
    )

    assert recovery.is_absolute()
    assert recovery.parent == installed_patched_game / ".ssr-oracle-recovery"
    assert paths["active"].read_bytes() == OFFICIAL_BYTES
    assert _file_mode(paths["active"]) == backup_before[2]
    assert not paths["backup_directory"].exists()
    assert not paths["compat_directory"].exists()
    assert _manifest_compatibility_entries(manifest) == {}
    assert oracle_install._load_manifest(installed_patched_game) == manifest
    status = status_install(installed_patched_game, repo_root=Path("/unused"))
    assert status.healthy
    assert status.preloader_compatibility.state == "official"
    recovered_backup = recovery / "compat" / BACKUP_PATH
    recovered_provenance = recovery / "compat" / PROVENANCE_PATH
    assert _restore_file_evidence(recovered_backup) == backup_before
    assert _restore_file_evidence(recovered_provenance) == provenance_before
    patched_locations = _restore_inode_locations(
        (recovery,), patched_active_before[:2]
    )
    assert len(patched_locations) == 1
    assert patched_locations[0].read_bytes() == patched_active_before[3]
    assert _file_mode(patched_locations[0]) == patched_active_before[2]
    cleanup_directories = tuple(
        path for path in (recovery / "cleanup").iterdir() if path.is_dir()
    )
    assert len(cleanup_directories) >= 2
    recovered_empty_identities = {
        (path.stat().st_dev, path.stat().st_ino)
        for path in cleanup_directories
        if not any(path.iterdir())
    }
    assert former_directory_identities <= recovered_empty_identities


def test_restore_final_verify_closes_active_fd_when_manifest_open_fails(
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    active_fd = os.open(os.devnull, os.O_RDONLY)
    active_snapshot = oracle_install._StableFileSnapshot(
        b"official", 0o644, 1, 2, 8
    )
    calls = 0

    def fail_second_open(*args: object, **kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 1:
            return active_fd, active_snapshot
        raise InstallError("injected manifest open failure")

    monkeypatch.setattr(
        oracle_install, "_restore_read_stable_file", fail_second_open
    )
    try:
        with pytest.raises(InstallError, match="injected manifest open failure"):
            oracle_install._restore_final_verify(
                None,
                None,
                None,
                None,
                b"",
                b"",
                0o644,
                None,
            )
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(active_fd)
    finally:
        try:
            os.close(active_fd)
        except OSError:
            pass


@pytest.mark.parametrize(
    "state_change",
    [
        "official",
        "game_assembly_bytes",
        "manifest_game_hash",
        "manifest_archive_hash",
        "expected_archive_hash",
        "active_bytes",
        "backup_bytes",
        "provenance_bytes",
        "manifest_active_hash",
        "manifest_backup_hash",
        "manifest_provenance_hash",
        "provenance_official_hash",
        "provenance_patched_hash",
        "trust_patch",
        "trust_toolchain",
        "active_symlink",
        "manifest_symlink",
        "backup_symlink",
        "provenance_symlink",
        "backup_parent_symlink",
        "compat_parent_symlink",
        "recovery_parent_symlink",
    ],
)
def test_restore_preconditions_fail_closed_without_live_mutation(
    state_change: str,
    installed_patched_game: Path,
    trust: CompatTrust,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    game = installed_patched_game
    paths = _restore_paths(game)
    if state_change == "official":
        paths["active"].write_bytes(OFFICIAL_BYTES)
        paths["backup_directory"].rename(tmp_path / "official-backup-dir")
        paths["compat_directory"].rename(tmp_path / "official-compat-dir")
        manifest = oracle_install._load_manifest(game)
        oracle_install._write_manifest(
            game,
            InstallManifest(
                manifest.schema_version,
                manifest.game_assembly_sha256,
                manifest.runtime_archive_sha256,
                tuple(
                    entry
                    for entry in manifest.entries
                    if entry.relative_path
                    not in {BACKUP_ROOT, BACKUP_PATH, COMPAT_ROOT, PROVENANCE_PATH}
                ),
            ),
        )
    elif state_change == "game_assembly_bytes":
        (
            game
            / "Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
        ).write_bytes(b"unexpected game assembly")
    elif state_change in {"manifest_game_hash", "manifest_archive_hash"}:
        decoded = json.loads(paths["manifest"].read_bytes())
        decoded[
            (
                "game_assembly_sha256"
                if state_change == "manifest_game_hash"
                else "runtime_archive_sha256"
            )
        ] = "d" * 64
        paths["manifest"].write_bytes(
            (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
        )
    elif state_change == "expected_archive_hash":
        monkeypatch.setattr(
            oracle_install,
            "EXPECTED_RUNTIME_ARCHIVE_SHA256",
            "c" * 64,
        )
    elif state_change == "active_bytes":
        paths["active"].write_bytes(b"changed active")
    elif state_change == "backup_bytes":
        paths["backup"].write_bytes(b"changed backup")
    elif state_change == "provenance_bytes":
        paths["provenance"].write_bytes(b"changed provenance")
    elif state_change in {
        "manifest_active_hash",
        "manifest_backup_hash",
        "manifest_provenance_hash",
    }:
        _set_manifest_file_hash_to_genuine_mismatch(
            game,
            {
                "manifest_active_hash": ACTIVE_PATH,
                "manifest_backup_hash": BACKUP_PATH,
                "manifest_provenance_hash": PROVENANCE_PATH,
            }[state_change],
        )
    elif state_change in {"provenance_official_hash", "provenance_patched_hash"}:
        decoded = json.loads(paths["provenance"].read_bytes())
        decoded[
            (
                "official_preloader_sha256"
                if state_change == "provenance_official_hash"
                else "patched_preloader_sha256"
            )
        ] = "b" * 64
        paths["provenance"].write_bytes(canonical_json(decoded))
        _replace_manifest_file_hash(game, PROVENANCE_PATH)
    elif state_change in {"trust_patch", "trust_toolchain"}:
        monkeypatch.setattr(
            oracle_install,
            "load_trust",
            lambda _: CompatTrust(
                trust.schema_version,
                "f" * 64 if state_change == "trust_patch" else trust.patch_sha256,
                (
                    "e" * 64
                    if state_change == "trust_toolchain"
                    else trust.toolchain_sha256
                ),
                trust.dependencies_sha256,
                trust.nuget_lock_tree_sha256,
            ),
        )
    elif state_change in {
        "active_symlink",
        "manifest_symlink",
        "backup_symlink",
        "provenance_symlink",
    }:
        target = paths[
            {
                "active_symlink": "active",
                "manifest_symlink": "manifest",
                "backup_symlink": "backup",
                "provenance_symlink": "provenance",
            }[state_change]
        ]
        held = tmp_path / f"held-{state_change}"
        target.rename(held)
        target.symlink_to(held)
    elif state_change in {"backup_parent_symlink", "compat_parent_symlink"}:
        target = paths[
            "backup_directory"
            if state_change == "backup_parent_symlink"
            else "compat_directory"
        ]
        held = tmp_path / f"held-{state_change}"
        target.rename(held)
        target.symlink_to(held, target_is_directory=True)
    elif state_change == "recovery_parent_symlink":
        outside = tmp_path / "outside-recovery"
        outside.mkdir()
        (game / ".ssr-oracle-recovery").symlink_to(
            outside, target_is_directory=True
        )
    before = _tree_snapshot(game)

    with pytest.raises(
        InstallError,
        match=(
            "preloader compatibility is not patched"
            if state_change == "official"
            else None
        ),
    ):
        oracle_install.restore_preloader(game, repo_root=Path("/unused"))

    assert _tree_snapshot(game) == before
    assert _restore_recovery_runs(game) == ()


def test_restore_cli_success_reports_manifest_and_absolute_recovery(
    installed_patched_game: Path,
    capsys: pytest.CaptureFixture[str],
    restore_no_terminal_deletion: None,
) -> None:
    result = main(
        [
            "restore-preloader",
            "--game-root",
            str(installed_patched_game),
            "--repo-root",
            "/unused",
        ]
    )
    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert set(output) == {"manifest", "recovery"}
    assert Path(output["recovery"]).is_absolute()


def test_restore_cli_official_state_exits_two_with_one_error_line(
    installed_official_game: Path,
    capsys: pytest.CaptureFixture[str],
    restore_no_terminal_deletion: None,
) -> None:
    result = main(
        [
            "restore-preloader",
            "--game-root",
            str(installed_official_game),
            "--repo-root",
            "/unused",
        ]
    )
    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err == "preloader compatibility is not patched\n"


@pytest.mark.parametrize(
    "boundary",
    [
        "recovery_parent_mkdir",
        "recovery_parent_child_fsync",
        "recovery_parent_parent_fsync",
        "recovery_run_mkdir",
        "recovery_run_child_fsync",
        "recovery_run_parent_fsync",
        "recovery_compat_mkdir",
        "recovery_compat_child_fsync",
        "recovery_compat_parent_fsync",
        "recovery_bepinex_mkdir",
        "recovery_bepinex_child_fsync",
        "recovery_bepinex_parent_fsync",
        "recovery_backup_dir_mkdir",
        "recovery_backup_dir_child_fsync",
        "recovery_backup_dir_parent_fsync",
        "recovery_provenance_dir_mkdir",
        "recovery_provenance_dir_child_fsync",
        "recovery_provenance_dir_parent_fsync",
        "recovery_cleanup_dir_mkdir",
        "recovery_cleanup_dir_child_fsync",
        "recovery_cleanup_dir_parent_fsync",
        "restore_recovery_graph_pinned",
    ],
)
def test_restore_recovery_allocation_boundaries_preserve_partial_scaffolding(
    boundary: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    before = _tree_snapshot_without_recovery(installed_patched_game)
    observed = _install_restore_checkpoint_failure(monkeypatch, boundary)

    with pytest.raises(
        InstallError,
        match=f"injected {boundary}|restore_preloader",
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert boundary in observed
    assert _tree_snapshot_without_recovery(installed_patched_game) == before
    if boundary.startswith(
        (
            "recovery_run_",
            "recovery_compat_",
            "recovery_bepinex_",
            "recovery_backup_dir_",
            "recovery_provenance_dir_",
            "recovery_cleanup_dir_",
            "restore_recovery_graph_",
        )
    ):
        assert _restore_recovery_runs(installed_patched_game)


def test_restore_complete_recovery_graph_is_durable_before_live_mutation(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    seen: list[str] = []
    opened_directories: dict[tuple[int, int], list[int]] = {}
    fsynced_directories: list[tuple[int, int]] = []
    original_open = oracle_install.os.open
    original_fsync = oracle_install.os.fsync

    def trace_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        flags = args[1] if len(args) > 1 else kwargs["flags"]
        observed = os.fstat(descriptor)
        if stat.S_ISDIR(observed.st_mode):
            opened_directories.setdefault(
                (observed.st_dev, observed.st_ino), []
            ).append(flags)
        return descriptor

    def trace_fsync(descriptor: int) -> None:
        observed = os.fstat(descriptor)
        if stat.S_ISDIR(observed.st_mode):
            fsynced_directories.append((observed.st_dev, observed.st_ino))
        original_fsync(descriptor)

    def inspect(boundary: str) -> None:
        seen.append(boundary)
        if boundary != "restore_before_first_live_mutation":
            return
        runs = _restore_recovery_runs(installed_patched_game)
        assert len(runs) == 1
        run = runs[0]
        graph = (
            run,
            run / "compat",
            run / "compat/BepInEx",
            run / "compat/BepInEx/.ssr-oracle-backup",
            run / "compat/BepInEx/.ssr-oracle-compat",
            run / "cleanup",
        )
        for path in graph:
            identity = (
                path.stat(follow_symlinks=False).st_dev,
                path.stat(follow_symlinks=False).st_ino,
            )
            assert identity in opened_directories, path
            assert any(
                flags & os.O_DIRECTORY and flags & os.O_NOFOLLOW
                for flags in opened_directories[identity]
            ), path
            assert identity in fsynced_directories, (path, "child fsync")
            parent_observed = path.parent.stat(follow_symlinks=False)
            assert (
                parent_observed.st_dev,
                parent_observed.st_ino,
            ) in fsynced_directories, (path, "parent fsync")
        required = {
            "recovery_run_mkdir",
            "recovery_run_child_fsync",
            "recovery_run_parent_fsync",
            "recovery_compat_mkdir",
            "recovery_compat_child_fsync",
            "recovery_compat_parent_fsync",
            "recovery_bepinex_mkdir",
            "recovery_bepinex_child_fsync",
            "recovery_bepinex_parent_fsync",
            "recovery_backup_dir_mkdir",
            "recovery_backup_dir_child_fsync",
            "recovery_backup_dir_parent_fsync",
            "recovery_provenance_dir_mkdir",
            "recovery_provenance_dir_child_fsync",
            "recovery_provenance_dir_parent_fsync",
            "recovery_cleanup_dir_mkdir",
            "recovery_cleanup_dir_child_fsync",
            "recovery_cleanup_dir_parent_fsync",
            "restore_recovery_graph_pinned",
        }
        assert required <= set(seen)
        raise InstallError("stop before first live mutation")

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", inspect, raising=False
    )
    monkeypatch.setattr(oracle_install.os, "open", trace_open)
    monkeypatch.setattr(oracle_install.os, "fsync", trace_fsync)
    before = _tree_snapshot_without_recovery(installed_patched_game)
    with pytest.raises(
        InstallError,
        match="stop before first live mutation|restore_preloader",
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )
    assert _tree_snapshot_without_recovery(installed_patched_game) == before


def test_restore_retries_only_top_level_run_publication_eexist_with_fresh_random(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    (installed_patched_game / ".ssr-oracle-recovery").mkdir()
    token_hex_calls: list[int] = []
    candidate_tokens: list[str] = []
    events: list[tuple[str, str]] = []
    original_renameatx = oracle_install._renameatx
    publications = 0
    published_names: list[str] = []

    def fresh_token_hex(byte_count: int) -> str:
        token_hex_calls.append(byte_count)
        return f"{len(token_hex_calls):032x}"

    def reviewed_recovery_name() -> str:
        token = oracle_install.secrets.token_hex(16)
        candidate_tokens.append(token)
        events.append(("candidate", token))
        return "20260728T120000Z-" + token

    def collide_once(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal publications
        if description == "publish compatibility recovery run directory":
            publications += 1
            published_names.append(destination)
            events.append(("publication", destination.rsplit("-", 1)[1]))
            if publications == 1:
                events.append(("eexist", destination.rsplit("-", 1)[1]))
                raise oracle_install._RenameAtError(
                    errno.EEXIST, "injected top-level run collision"
                )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(oracle_install.secrets, "token_hex", fresh_token_hex)
    monkeypatch.setattr(
        oracle_install, "_compat_recovery_name", reviewed_recovery_name
    )
    monkeypatch.setattr(oracle_install, "_renameatx", collide_once)
    _install_restore_checkpoint_failure(
        monkeypatch, "restore_before_first_live_mutation"
    )
    before = _tree_snapshot_without_recovery(installed_patched_game)

    with pytest.raises(
        InstallError,
        match="injected restore_before_first_live_mutation|restore_preloader",
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert publications == 2
    assert len(candidate_tokens) == 2
    assert candidate_tokens[0] != candidate_tokens[1]
    assert set(token_hex_calls) == {16}
    assert published_names[0] != published_names[1]
    assert published_names[0].endswith("-" + candidate_tokens[0])
    assert published_names[1].endswith("-" + candidate_tokens[1])
    candidate_events = [
        event for event in events if event[0] in {"candidate", "publication", "eexist"}
    ]
    assert candidate_events == [
        ("candidate", candidate_tokens[0]),
        ("publication", candidate_tokens[0]),
        ("eexist", candidate_tokens[0]),
        ("candidate", candidate_tokens[1]),
        ("publication", candidate_tokens[1]),
    ]
    assert _tree_snapshot_without_recovery(installed_patched_game) == before
    runs = _restore_recovery_runs(installed_patched_game)
    assert not any(path.name == published_names[0] for path in runs)
    assert sum(path.name == published_names[1] for path in runs) == 1


@pytest.mark.parametrize("error_number", [errno.EIO, errno.EPERM])
def test_restore_non_eexist_run_publication_error_never_retries(
    error_number: int,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    original_renameatx = oracle_install._renameatx
    publications = 0

    def fail_publish(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal publications
        if description == "publish compatibility recovery run directory":
            publications += 1
            raise oracle_install._RenameAtError(
                error_number, "injected noncollision publication failure"
            )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(oracle_install, "_renameatx", fail_publish)
    before = _tree_snapshot_without_recovery(installed_patched_game)
    with pytest.raises(
        InstallError,
        match="injected noncollision publication failure|restore_preloader",
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )
    assert publications == 1
    assert _tree_snapshot_without_recovery(installed_patched_game) == before


@pytest.mark.parametrize(
    ("description", "destination_kind"),
    [
        ("publish compatibility recovery directory", "directory"),
        ("publish recovery BepInEx directory", "directory"),
        ("publish recovery backup directory directory", "directory"),
        ("publish recovery provenance directory directory", "directory"),
        ("publish recovery cleanup directory directory", "directory"),
    ],
)
def test_restore_child_collision_after_run_selection_is_a_hard_failure(
    description: str,
    destination_kind: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    del destination_kind
    original_renameatx = oracle_install._renameatx
    collisions = 0

    def collide(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        observed_description,
    ):
        nonlocal collisions
        if observed_description == description:
            collisions += 1
            os.mkdir(destination, 0o700, dir_fd=destination_parent.fd)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            observed_description,
        )

    monkeypatch.setattr(oracle_install, "_renameatx", collide)
    before = _tree_snapshot_without_recovery(installed_patched_game)
    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )
    assert collisions == 1
    assert _tree_snapshot_without_recovery(installed_patched_game) == before
    if collisions:
        assert len(_restore_recovery_runs(installed_patched_game)) == 1


RESTORE_FORWARD_BOUNDARIES = [
    "restore_before_recovery_parent_create",
    "restore_after_recovery_parent_create",
    "restore_before_recovery_parent_open",
    "restore_after_recovery_parent_open",
    "restore_before_recovery_parent_fsync",
    "restore_after_recovery_parent_fsync",
    "restore_before_recovery_parent_child_fsync",
    "restore_after_recovery_parent_child_fsync",
    "restore_before_recovery_parent_parent_fsync",
    "restore_after_recovery_parent_parent_fsync",
    "restore_before_recovery_run_publish",
    "restore_after_recovery_run_publish",
    "restore_before_recovery_run_open",
    "restore_after_recovery_run_open",
    "restore_before_recovery_run_fsync",
    "restore_after_recovery_run_fsync",
    "restore_before_recovery_run_child_fsync",
    "restore_after_recovery_run_child_fsync",
    "restore_before_recovery_run_parent_fsync",
    "restore_after_recovery_run_parent_fsync",
    "restore_before_recovery_compat_create",
    "restore_after_recovery_compat_create",
    "restore_before_recovery_compat_open",
    "restore_after_recovery_compat_open",
    "restore_before_recovery_compat_fsync",
    "restore_after_recovery_compat_fsync",
    "restore_before_recovery_compat_child_fsync",
    "restore_after_recovery_compat_child_fsync",
    "restore_before_recovery_compat_parent_fsync",
    "restore_after_recovery_compat_parent_fsync",
    "restore_before_recovery_bepinex_create",
    "restore_after_recovery_bepinex_create",
    "restore_before_recovery_bepinex_open",
    "restore_after_recovery_bepinex_open",
    "restore_before_recovery_bepinex_child_fsync",
    "restore_after_recovery_bepinex_child_fsync",
    "restore_before_recovery_bepinex_parent_fsync",
    "restore_after_recovery_bepinex_parent_fsync",
    "restore_before_recovery_backup_create",
    "restore_after_recovery_backup_create",
    "restore_before_recovery_backup_open",
    "restore_after_recovery_backup_open",
    "restore_before_recovery_backup_child_fsync",
    "restore_after_recovery_backup_child_fsync",
    "restore_before_recovery_backup_parent_fsync",
    "restore_after_recovery_backup_parent_fsync",
    "restore_before_recovery_provenance_create",
    "restore_after_recovery_provenance_create",
    "restore_before_recovery_provenance_open",
    "restore_after_recovery_provenance_open",
    "restore_before_recovery_provenance_child_fsync",
    "restore_after_recovery_provenance_child_fsync",
    "restore_before_recovery_provenance_parent_fsync",
    "restore_after_recovery_provenance_parent_fsync",
    "restore_before_recovery_cleanup_create",
    "restore_after_recovery_cleanup_create",
    "restore_before_recovery_cleanup_open",
    "restore_after_recovery_cleanup_open",
    "restore_before_recovery_cleanup_fsync",
    "restore_after_recovery_cleanup_fsync",
    "restore_before_recovery_cleanup_child_fsync",
    "restore_after_recovery_cleanup_child_fsync",
    "restore_before_recovery_cleanup_parent_fsync",
    "restore_after_recovery_cleanup_parent_fsync",
    "restore_before_official_active_write",
    "restore_after_official_active_write",
    "restore_before_official_active_chmod",
    "restore_after_official_active_chmod",
    "restore_before_official_active_file_fsync",
    "restore_after_official_active_file_fsync",
    "restore_before_official_manifest_write",
    "restore_after_official_manifest_write",
    "restore_before_official_manifest_chmod",
    "restore_after_official_manifest_chmod",
    "restore_before_official_manifest_file_fsync",
    "restore_after_official_manifest_file_fsync",
    "restore_before_backup_move",
    "restore_after_backup_move",
    "restore_before_backup_reopen",
    "restore_after_backup_reopen",
    "restore_before_backup_snapshot_validation",
    "restore_after_backup_snapshot_validation",
    "restore_before_backup_source_parent_fsync",
    "restore_after_backup_source_parent_fsync",
    "restore_before_backup_destination_parent_fsync",
    "restore_after_backup_destination_parent_fsync",
    "restore_before_provenance_move",
    "restore_after_provenance_move",
    "restore_before_provenance_reopen",
    "restore_after_provenance_reopen",
    "restore_before_provenance_snapshot_validation",
    "restore_after_provenance_snapshot_validation",
    "restore_before_provenance_source_parent_fsync",
    "restore_after_provenance_source_parent_fsync",
    "restore_before_provenance_destination_parent_fsync",
    "restore_after_provenance_destination_parent_fsync",
    "restore_before_active_swap",
    "restore_after_active_swap",
    "restore_before_active_displaced_validation",
    "restore_after_active_displaced_validation",
    "restore_before_active_staging_parent_fsync",
    "restore_after_active_staging_parent_fsync",
    "restore_before_active_live_parent_fsync",
    "restore_after_active_live_parent_fsync",
    "restore_before_manifest_swap",
    "restore_after_manifest_swap",
    "restore_before_manifest_displaced_validation",
    "restore_after_manifest_displaced_validation",
    "restore_before_manifest_staging_parent_fsync",
    "restore_after_manifest_staging_parent_fsync",
    "restore_before_manifest_live_parent_fsync",
    "restore_after_manifest_live_parent_fsync",
    "restore_before_backup_directory_move",
    "restore_after_backup_directory_move",
    "restore_before_backup_directory_reopen",
    "restore_after_backup_directory_reopen",
    "restore_before_backup_directory_validation",
    "restore_after_backup_directory_validation",
    "restore_before_backup_directory_source_parent_fsync",
    "restore_after_backup_directory_source_parent_fsync",
    "restore_before_backup_directory_destination_parent_fsync",
    "restore_after_backup_directory_destination_parent_fsync",
    "restore_before_compat_directory_move",
    "restore_after_compat_directory_move",
    "restore_before_compat_directory_reopen",
    "restore_after_compat_directory_reopen",
    "restore_before_compat_directory_validation",
    "restore_after_compat_directory_validation",
    "restore_before_compat_directory_source_parent_fsync",
    "restore_after_compat_directory_source_parent_fsync",
    "restore_before_compat_directory_destination_parent_fsync",
    "restore_after_compat_directory_destination_parent_fsync",
    "restore_before_cleanup_preservation_move",
    "restore_after_cleanup_preservation_move",
    "restore_before_cleanup_preservation_source_parent_fsync",
    "restore_after_cleanup_preservation_source_parent_fsync",
    "restore_before_cleanup_preservation_destination_parent_fsync",
    "restore_after_cleanup_preservation_destination_parent_fsync",
    "restore_before_recovery_directory_fsync",
    "restore_after_recovery_directory_fsync",
    "restore_before_final_status_verification",
    "restore_after_final_status_verification",
]


def _restore_boundary_primitives(boundary: str) -> tuple[str, ...]:
    if boundary.endswith(("write",)):
        return ("write",)
    if boundary.endswith(("chmod",)):
        return ("fchmod",)
    if "fsync" in boundary:
        return ("fsync",)
    if boundary.endswith(("open", "reopen")):
        return ("open",)
    if boundary.endswith("directory_validation"):
        return ("fstat", "scandir")
    if boundary.endswith(
        ("snapshot_validation", "displaced_validation")
    ):
        return ("fstat", "read")
    if boundary.endswith("final_status_verification"):
        return ("fstat", "read", "stat", "scandir")
    if boundary.endswith(("create",)):
        return ("mkdir",)
    if any(
        word in boundary
        for word in ("publish", "move", "swap", "restore", "preservation")
    ):
        return ("renameatx",)
    raise AssertionError(f"boundary has no reviewed primitive: {boundary}")


def _restore_created_path(
    path: object,
    dir_fd: int | None,
    descriptor_path: Callable[[int], Path],
) -> Path:
    candidate = Path(os.fsdecode(path))
    if candidate.is_absolute():
        return candidate
    assert dir_fd is not None
    return descriptor_path(dir_fd) / candidate


def _trace_restore_primitives(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[tuple[object, ...]],
    dict[tuple[int, int], Path],
    Callable[[int], Path],
]:
    events: list[tuple[object, ...]] = []
    created_identities: dict[tuple[int, int], Path] = {}
    descriptor_paths: dict[int, Path] = {}
    original_open = oracle_install.os.open
    original_fstat = oracle_install.os.fstat
    original_read = oracle_install.os.read
    original_stat = oracle_install.os.stat
    original_scandir = oracle_install.os.scandir
    original_write = oracle_install.os.write
    original_fchmod = oracle_install.os.fchmod
    original_fsync = oracle_install.os.fsync
    original_mkdir = oracle_install.os.mkdir
    original_renameatx = oracle_install._renameatx

    def fd_identity(descriptor: int) -> tuple[int, int]:
        observed = original_fstat(descriptor)
        return observed.st_dev, observed.st_ino

    def parent_identity(
        descriptor: int | None,
    ) -> tuple[int, int] | None:
        return None if descriptor is None else fd_identity(descriptor)

    def descriptor_path(descriptor: int) -> Path:
        known = descriptor_paths.get(descriptor)
        if known is not None:
            return known
        identity = fd_identity(descriptor)
        candidates = {
            path
            for known_descriptor, path in descriptor_paths.items()
            if fd_identity(known_descriptor) == identity
        }
        assert len(candidates) == 1, (descriptor, identity, candidates)
        known = candidates.pop()
        descriptor_paths[descriptor] = known
        return known

    def relocate_descriptor_paths(source: Path, destination: Path) -> None:
        for descriptor, known in tuple(descriptor_paths.items()):
            if known == source or source in known.parents:
                descriptor_paths[descriptor] = (
                    destination / known.relative_to(source)
                )

    def trace_open(*args, **kwargs):
        descriptor = original_open(*args, **kwargs)
        flags = args[1] if len(args) > 1 else kwargs["flags"]
        dir_fd = kwargs.get("dir_fd")
        identity = fd_identity(descriptor)
        created_path = _restore_created_path(
            args[0], dir_fd, descriptor_path
        )
        descriptor_paths[descriptor] = created_path
        events.append(
            (
                "open",
                parent_identity(dir_fd),
                os.fsdecode(args[0]),
                flags,
                identity,
                dir_fd,
                descriptor,
                created_path,
            )
        )
        if flags & os.O_CREAT and flags & os.O_EXCL:
            created_identities[identity] = created_path
        return descriptor

    def trace_fstat(*args, **kwargs):
        observed = original_fstat(*args, **kwargs)
        descriptor = args[0]
        events.append(
            (
                "fstat",
                (observed.st_dev, observed.st_ino),
                descriptor,
                observed.st_size,
                descriptor_path(descriptor),
            )
        )
        return observed

    def trace_read(*args, **kwargs):
        descriptor = args[0]
        requested = args[1]
        payload = original_read(*args, **kwargs)
        events.append(
            (
                "read",
                fd_identity(descriptor),
                requested,
                len(payload),
                descriptor,
                descriptor_path(descriptor),
            )
        )
        return payload

    def trace_stat(*args, **kwargs):
        path = args[0]
        dir_fd = kwargs.get("dir_fd")
        semantic_path = _restore_created_path(
            path, dir_fd, descriptor_path
        )
        event_prefix = (
            "stat",
            parent_identity(dir_fd),
            os.fsdecode(path),
        )
        event_suffix = (
            dir_fd,
            semantic_path,
            kwargs.get("follow_symlinks", True),
        )
        try:
            observed = original_stat(*args, **kwargs)
        except FileNotFoundError:
            events.append((*event_prefix, None, *event_suffix))
            raise
        events.append(
            (
                *event_prefix,
                (observed.st_dev, observed.st_ino),
                *event_suffix,
            )
        )
        return observed

    def trace_scandir(*args, **kwargs):
        target = args[0]
        identity = fd_identity(target) if isinstance(target, int) else None
        path = (
            descriptor_path(target)
            if isinstance(target, int)
            else Path(os.fsdecode(target))
        )
        events.append(("scandir", identity, target, path))
        return original_scandir(*args, **kwargs)

    def trace_write(*args, **kwargs):
        written = original_write(*args, **kwargs)
        events.append(
            ("write", fd_identity(args[0]), len(args[1]), written)
        )
        return written

    def trace_fchmod(*args, **kwargs):
        result = original_fchmod(*args, **kwargs)
        events.append(("fchmod", fd_identity(args[0]), args[1]))
        return result

    def trace_fsync(*args, **kwargs):
        identity = fd_identity(args[0])
        result = original_fsync(*args, **kwargs)
        events.append(
            (
                "fsync",
                identity,
                args[0],
                descriptor_path(args[0]),
            )
        )
        return result

    def trace_mkdir(*args, **kwargs):
        result = original_mkdir(*args, **kwargs)
        path = args[0]
        dir_fd = kwargs.get("dir_fd")
        observed = original_stat(
            path, dir_fd=dir_fd, follow_symlinks=False
        )
        identity = (observed.st_dev, observed.st_ino)
        events.append(
            (
                "mkdir",
                parent_identity(dir_fd),
                os.fsdecode(path),
                args[1] if len(args) > 1 else kwargs.get("mode", 0o777),
                identity,
                dir_fd,
                _restore_created_path(path, dir_fd, descriptor_path),
            )
        )
        created_identities[identity] = (
            _restore_created_path(path, dir_fd, descriptor_path)
        )
        return result

    def trace_renameatx(*args, **kwargs):
        source_parent, source, destination_parent, destination, flags = args[:5]
        try:
            source_stat = original_stat(
                source,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            source_identity = (source_stat.st_dev, source_stat.st_ino)
        except OSError:
            source_identity = None
        try:
            destination_stat = original_stat(
                destination,
                dir_fd=destination_parent.fd,
                follow_symlinks=False,
            )
            destination_identity = (
                destination_stat.st_dev,
                destination_stat.st_ino,
            )
        except OSError:
            destination_identity = None
        source_parent_path = descriptor_path(source_parent.fd)
        destination_parent_path = descriptor_path(destination_parent.fd)
        source_path = source_parent_path / source
        destination_path = destination_parent_path / destination
        result = original_renameatx(*args, **kwargs)
        if flags == oracle_install._RENAME_SWAP:
            source_updates = {
                descriptor: path
                for descriptor, path in descriptor_paths.items()
                if path == source_path or source_path in path.parents
            }
            destination_updates = {
                descriptor: path
                for descriptor, path in descriptor_paths.items()
                if path == destination_path or destination_path in path.parents
            }
            relocate_descriptor_paths(source_path, destination_path)
            relocate_descriptor_paths(destination_path, source_path)
            for descriptor, path in source_updates.items():
                descriptor_paths[descriptor] = (
                    destination_path / path.relative_to(source_path)
                )
            for descriptor, path in destination_updates.items():
                descriptor_paths[descriptor] = (
                    source_path / path.relative_to(destination_path)
                )
        else:
            relocate_descriptor_paths(source_path, destination_path)
        events.append(
            (
                "renameatx",
                (source_parent.device, source_parent.inode),
                source,
                (destination_parent.device, destination_parent.inode),
                destination,
                flags,
                source_identity,
                destination_identity,
                source_parent.fd,
                destination_parent.fd,
                source_parent_path,
                destination_parent_path,
            )
        )
        return result

    monkeypatch.setattr(oracle_install.os, "open", trace_open)
    monkeypatch.setattr(oracle_install.os, "fstat", trace_fstat)
    monkeypatch.setattr(oracle_install.os, "read", trace_read)
    monkeypatch.setattr(oracle_install.os, "stat", trace_stat)
    monkeypatch.setattr(oracle_install.os, "scandir", trace_scandir)
    monkeypatch.setattr(oracle_install.os, "write", trace_write)
    monkeypatch.setattr(oracle_install.os, "fchmod", trace_fchmod)
    monkeypatch.setattr(oracle_install.os, "fsync", trace_fsync)
    monkeypatch.setattr(oracle_install.os, "mkdir", trace_mkdir)
    monkeypatch.setattr(oracle_install, "_renameatx", trace_renameatx)
    return events, created_identities, descriptor_path


def _restore_path_identity(path: Path) -> tuple[int, int]:
    observed = path.stat(follow_symlinks=False)
    return observed.st_dev, observed.st_ino


def _restore_selected_recovery_run(game: Path) -> Path:
    runs = _restore_recovery_runs(game)
    assert len(runs) == 1, runs
    return runs[0]


def _restore_expected_open_path(boundary: str, game: Path) -> Path:
    if "recovery_parent_open" in boundary:
        return game / ".ssr-oracle-recovery"
    run = _restore_selected_recovery_run(game)
    if "recovery_run_open" in boundary:
        return run
    if "recovery_compat_open" in boundary:
        return run / "compat"
    if "recovery_bepinex_open" in boundary:
        return run / "compat/BepInEx"
    if "recovery_backup_open" in boundary:
        return run / "compat" / BACKUP_ROOT
    if "recovery_provenance_open" in boundary:
        return run / "compat" / COMPAT_ROOT
    if "recovery_cleanup_open" in boundary:
        return run / "cleanup"
    if "backup_directory_reopen" in boundary:
        return run / "cleanup/.ssr-oracle-backup"
    if "compat_directory_reopen" in boundary:
        return run / "cleanup/.ssr-oracle-compat"
    if "backup_reopen" in boundary:
        return run / "compat" / BACKUP_PATH
    if "provenance_reopen" in boundary:
        return run / "compat" / PROVENANCE_PATH
    raise AssertionError(f"open boundary has no exact path: {boundary}")


def _restore_expected_mkdir_path(boundary: str, game: Path) -> Path:
    if "recovery_parent_create" in boundary:
        return game / ".ssr-oracle-recovery"
    run = _restore_selected_recovery_run(game)
    suffixes = {
        "recovery_compat_create": Path("compat"),
        "recovery_bepinex_create": Path("compat/BepInEx"),
        "recovery_backup_create": Path("compat") / BACKUP_ROOT,
        "recovery_provenance_create": Path("compat") / COMPAT_ROOT,
        "recovery_cleanup_create": Path("cleanup"),
    }
    matches = [
        run / suffix
        for marker, suffix in suffixes.items()
        if marker in boundary
    ]
    assert len(matches) == 1, (boundary, matches)
    return matches[0]


def _assert_restore_boundary_events(
    boundary: str,
    paired_events: list[tuple[object, ...]],
    prior_events: list[tuple[object, ...]],
    game: Path,
    evidence: dict[str, tuple[Path, tuple[int, int], int, bytes | None]],
    created: dict[tuple[int, int], Path],
) -> None:
    primitives = _restore_boundary_primitives(boundary)
    by_primitive = {
        primitive: [
            event for event in paired_events if event[0] == primitive
        ]
        for primitive in primitives
    }
    assert all(by_primitive.values()), (boundary, paired_events)

    stable_reads: dict[
        tuple[str, int, tuple[int, int], Path],
        list[tuple[object, ...]],
    ] = {}
    for event in by_primitive.get("read", []):
        assert len(event) == 6, event
        identity, requested, returned, descriptor, path = event[1:]
        assert (
            identity is not None
            and isinstance(descriptor, int)
            and descriptor >= 0
            and isinstance(path, Path)
            and path.is_absolute()
            and requested > 0
            and 0 <= returned <= requested
        ), event
        stable_reads.setdefault(
            (boundary, descriptor, identity, path), []
        ).append(event)

    fstat_events = by_primitive.get("fstat", [])
    for key, read_events in stable_reads.items():
        _, descriptor, identity, path = key
        matching_fstats = [
            event
            for event in fstat_events
            if len(event) == 5
            and event[1] == identity
            and event[2] == descriptor
            and event[4] == path
        ]
        assert len(matching_fstats) >= 2, (
            boundary,
            key,
            matching_fstats,
            paired_events,
        )
        expected_sizes = {event[3] for event in matching_fstats}
        assert len(expected_sizes) == 1, (
            boundary,
            key,
            expected_sizes,
        )
        expected_size = expected_sizes.pop()
        assert isinstance(expected_size, int) and expected_size >= 0

        consumed = 0
        reached_eof = False
        for event in read_events:
            returned = event[3]
            if returned == 0:
                assert not reached_eof, (boundary, key, read_events)
                assert consumed == expected_size, (
                    boundary,
                    key,
                    consumed,
                    expected_size,
                    read_events,
                )
                reached_eof = True
                continue
            assert not reached_eof, (boundary, key, read_events)
            consumed += returned
            assert consumed <= expected_size, (
                boundary,
                key,
                consumed,
                expected_size,
                read_events,
            )
        assert reached_eof and consumed == expected_size, (
            boundary,
            key,
            consumed,
            expected_size,
            read_events,
        )
    for event in by_primitive.get("scandir", []):
        assert event[1] is not None, event

    validation_target: tuple[int, int] | None = None
    if "backup_snapshot_validation" in boundary:
        validation_target = evidence["backup"][1]
    elif "provenance_snapshot_validation" in boundary:
        validation_target = evidence["provenance"][1]
    elif "backup_directory_validation" in boundary:
        validation_target = evidence["backup_directory"][1]
    elif "compat_directory_validation" in boundary:
        validation_target = evidence["compat_directory"][1]
    elif "displaced_validation" in boundary:
        leaf = (
            oracle_install.MANIFEST_NAME
            if "manifest" in boundary
            else "BepInEx.Preloader.dll"
        )
        swaps = [
            event
            for event in prior_events
            if event[0] == "renameatx"
            and event[4] == leaf
            and event[5] == oracle_install._RENAME_SWAP
        ]
        assert swaps, (boundary, prior_events)
        validation_target = swaps[-1][7]
        assert validation_target is not None

    if validation_target is not None:
        for primitive in primitives:
            identities = {event[1] for event in by_primitive[primitive]}
            assert validation_target in identities, (
                boundary,
                primitive,
                validation_target,
                paired_events,
            )

    if "final_status_verification" in boundary:
        required_files = {
            _restore_path_identity(game / ACTIVE_PATH),
            _restore_path_identity(game / oracle_install.MANIFEST_NAME),
        }
        fstat_identities = {
            event[1] for event in by_primitive["fstat"]
        }
        read_identities = {
            event[1] for event in by_primitive["read"]
        }
        assert required_files <= fstat_identities
        assert required_files <= read_identities
        bep_in_ex_identity = _restore_path_identity(game / "BepInEx")
        live_compat_names = {
            Path(BACKUP_ROOT).name,
            Path(COMPAT_ROOT).name,
        }
        absence_stats = [
            event
            for event in by_primitive["stat"]
            if event[1] == bep_in_ex_identity
            and event[2] in live_compat_names
            and event[3] is None
            and event[5]
            == game / "BepInEx" / event[2]
            and event[6] is False
        ]
        assert {
            event[2] for event in absence_stats
        } == live_compat_names, (boundary, absence_stats, paired_events)

        run = _restore_selected_recovery_run(game)
        expected_scans = {
            run / "compat" / BACKUP_ROOT,
            run / "compat" / COMPAT_ROOT,
        }
        observed_scans = {
            event[3]
            for event in by_primitive["scandir"]
            if event[1] == _restore_path_identity(event[3])
        }
        assert observed_scans == expected_scans, (
            boundary,
            observed_scans,
            expected_scans,
            paired_events,
        )

    rename_events = by_primitive.get("renameatx", [])
    if rename_events:
        assert len(rename_events) == 1, (boundary, rename_events)
        event = rename_events[0]
        source_leaf, destination_leaf, flags = event[2], event[4], event[5]
        source_path = event[10] / source_leaf
        destination_path = event[11] / destination_leaf
        assert event[1] == _restore_path_identity(event[10]), event
        assert event[3] == _restore_path_identity(event[11]), event
        if flags == oracle_install._RENAME_EXCL:
            assert event[7] is None, event
        else:
            displaced_key = "manifest" if "manifest" in boundary else "active"
            if boundary.startswith("restore_rollback_"):
                assert event[6] == evidence[displaced_key][1], event
                assert event[7] in created, event
            else:
                assert event[6] in created, event
                assert event[7] == evidence[displaced_key][1], event
        expected_leaf: str | None = None
        if "backup_directory" in boundary:
            expected_leaf = ".ssr-oracle-backup"
        elif "compat_directory" in boundary:
            expected_leaf = ".ssr-oracle-compat"
        elif "provenance" in boundary:
            expected_leaf = "preloader-provenance.json"
        elif "manifest" in boundary:
            expected_leaf = oracle_install.MANIFEST_NAME
        elif "active" in boundary or "backup" in boundary:
            expected_leaf = "BepInEx.Preloader.dll"
        if expected_leaf is not None:
            assert expected_leaf in {source_leaf, destination_leaf}, (
                boundary,
                event,
            )
        if "swap" in boundary:
            assert flags == oracle_install._RENAME_SWAP, (boundary, event)
        else:
            assert flags == oracle_install._RENAME_EXCL, (boundary, event)
        assert event[1] is not None and event[3] is not None
        assert event[6] is not None
        assert source_path.parent == event[10]
        assert destination_path.parent == event[11]

        recovery_runs = _restore_recovery_runs(game)
        rollback_restore_keys = {
            "backup_directory_restore": "backup_directory",
            "compat_directory_restore": "compat_directory",
            "backup_restore": "backup",
            "provenance_restore": "provenance",
        }
        rollback_restore_key = next(
            (
                key
                for marker, key in rollback_restore_keys.items()
                if marker in boundary
            ),
            None,
        )
        if "recovery_run_publish" in boundary:
            assert event[10] == event[11] == game / ".ssr-oracle-recovery"
        elif rollback_restore_key is not None:
            original_path = evidence[rollback_restore_key][0]
            forward_moves = [
                candidate
                for candidate in prior_events
                if candidate[0] == "renameatx"
                and candidate[5] == oracle_install._RENAME_EXCL
                and candidate[6] == evidence[rollback_restore_key][1]
                and candidate[10] / candidate[2] == original_path
                and any(
                    run == candidate[11] or run in candidate[11].parents
                    for run in recovery_runs
                )
            ]
            assert forward_moves, (boundary, prior_events)
            forward_move = forward_moves[-1]
            assert (
                event[10],
                source_leaf,
                event[11],
                destination_leaf,
                flags,
                event[6],
                event[7],
            ) == (
                forward_move[11],
                forward_move[4],
                original_path.parent,
                original_path.name,
                oracle_install._RENAME_EXCL,
                evidence[rollback_restore_key][1],
                None,
            ), (boundary, event, forward_move)
        elif "backup_move" in boundary or "provenance_move" in boundary:
            source_key = (
                "provenance" if "provenance" in boundary else "backup"
            )
            assert event[10] == evidence[source_key][0].parent
            assert source_leaf == evidence[source_key][0].name
            assert any(run in event[11].parents for run in recovery_runs)
            assert event[6] == evidence[source_key][1]
        elif "active_swap" in boundary:
            assert event[10] == event[11] == game / "BepInEx/core"
        elif "manifest_swap" in boundary:
            assert event[10] == event[11] == game
        elif "directory_move" in boundary:
            assert event[10] == game / "BepInEx"
            assert any(run in event[11].parents for run in recovery_runs)
            source_key = (
                "compat_directory"
                if "compat_directory" in boundary
                else "backup_directory"
            )
            assert event[6] == evidence[source_key][1]
        elif "preservation" in boundary:
            run = _restore_selected_recovery_run(game)
            assert event[11] == run / "cleanup", (boundary, event)
            assert event[7] is None
            assert flags == oracle_install._RENAME_EXCL
            destination_kind = (
                "directory"
                if destination_path.is_dir()
                else "file"
            )
            assert destination_leaf.startswith(f"{destination_kind}-")
            token = destination_leaf.removeprefix(f"{destination_kind}-")
            assert len(token) == 32
            assert token == token.lower()
            assert all(character in "0123456789abcdef" for character in token)
            owned_source_paths: set[Path] = set()
            if event[6] in created:
                owned_source_paths.add(created[event[6]])
            for candidate in prior_events:
                if (
                    candidate[0] == "renameatx"
                    and candidate[5] == oracle_install._RENAME_SWAP
                    and candidate[7] == event[6]
                ):
                    owned_source_paths.add(candidate[10] / candidate[2])
            assert source_path in owned_source_paths, (
                boundary,
                event,
                owned_source_paths,
            )

    for primitive in ("write", "fchmod"):
        for event in by_primitive.get(primitive, []):
            assert event[1] in created, (boundary, event, created)

    fsync_events = by_primitive.get("fsync", [])
    if fsync_events:
        assert len(fsync_events) == 1, (boundary, fsync_events)
        event = fsync_events[0]
        assert event[1] == _restore_path_identity(event[3]), event
        earlier = [*prior_events, *paired_events]
        if "source_parent_fsync" in boundary:
            rename = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] == "renameatx"
            )
            assert (event[1], event[3]) == (rename[1], rename[10])
        elif "destination_parent_fsync" in boundary:
            rename = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] == "renameatx"
            )
            assert (event[1], event[3]) == (rename[3], rename[11])
        elif "staging_parent_fsync" in boundary:
            rename = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] == "renameatx"
            )
            assert (event[1], event[3]) == (rename[1], rename[10])
        elif "live_parent_fsync" in boundary:
            rename = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] == "renameatx"
            )
            assert (event[1], event[3]) == (rename[3], rename[11])
        elif "file_fsync" in boundary:
            mutation = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] in {"write", "fchmod"}
            )
            assert event[1] == mutation[1]
        elif "recovery_directory_fsync" in boundary:
            assert event[3] in _restore_recovery_runs(game)
        elif "child_fsync" in boundary:
            opened = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] == "open"
            )
            assert (event[1], event[3]) == (opened[4], opened[7])
        elif "parent_fsync" in boundary:
            opened = next(
                candidate
                for candidate in reversed(earlier)
                if candidate[0] == "open"
            )
            assert (event[1], event[3]) == (opened[1], opened[7].parent)

    open_events = by_primitive.get("open", [])
    if open_events:
        assert len(open_events) == 1, (boundary, open_events)
        expected_path = _restore_expected_open_path(boundary, game)
    for event in open_events:
        assert event[1] == _restore_path_identity(event[7].parent), event
        assert event[4] == _restore_path_identity(event[7]), event
        assert event[2] == event[7].name, event
        assert event[7] == expected_path, (boundary, event, expected_path)
        assert event[2] not in {"", ".", ".."}, (boundary, event)
        assert event[3] & os.O_NOFOLLOW, (boundary, event)
        if boundary.endswith("reopen"):
            if "directory" in boundary:
                assert event[3] & os.O_DIRECTORY, (boundary, event)
                expected_key = (
                    "compat_directory"
                    if "compat_directory" in boundary
                    else "backup_directory"
                )
            else:
                assert not event[3] & os.O_DIRECTORY, (boundary, event)
                expected_key = (
                    "provenance" if "provenance" in boundary else "backup"
                )
            assert event[4] == evidence[expected_key][1], event
        else:
            assert event[3] & os.O_DIRECTORY, (boundary, event)
            assert event[4] in created, (boundary, event, created)
            assert created[event[4]] == event[7], (boundary, event, created)

    mkdir_events = by_primitive.get("mkdir", [])
    if mkdir_events:
        assert len(mkdir_events) == 1, (boundary, mkdir_events)
        expected_path = _restore_expected_mkdir_path(boundary, game)
    for event in mkdir_events:
        assert event[1] == _restore_path_identity(event[6].parent), event
        assert event[2] == event[6].name, event
        assert event[6] == expected_path, (boundary, event, expected_path)
        assert stat.S_IMODE(event[3]) == 0o700, event
        assert event[4] == _restore_path_identity(event[6]), event
        assert created[event[4]] == event[6], (boundary, event, created)


def _assert_created_restore_identities_retained(
    game: Path,
    created: dict[tuple[int, int], Path],
    *retained_recovery_roots: Path,
) -> None:
    runs = (*_restore_recovery_runs(game), *retained_recovery_roots)
    for identity, creation_name in created.items():
        locations = _restore_inode_locations(
            (game, *retained_recovery_roots), identity
        )
        assert len(locations) == 1, (identity, creation_name, locations)
        location = locations[0]
        assert location == creation_name or any(
            location == run or run in location.parents for run in runs
        ), (identity, creation_name, location, runs)


def test_restore_created_inventory_child_root_cannot_prove_retained_ancestor(
    tmp_path: Path,
    restore_no_terminal_deletion: None,
) -> None:
    game = tmp_path / "game"
    game.mkdir()
    retained_parent = tmp_path / "held/.ssr-oracle-recovery"
    retained_run = retained_parent / f"20000101T000000Z-{'a' * 32}"
    retained_run.mkdir(parents=True)
    parent_identity = _restore_path_identity(retained_parent)
    created = {
        parent_identity: game / ".ssr-oracle-recovery",
    }

    with pytest.raises(AssertionError):
        _assert_created_restore_identities_retained(
            game,
            created,
            retained_run,
        )
    _assert_created_restore_identities_retained(
        game,
        created,
        retained_parent,
    )


def test_restore_trace_uses_portable_descriptor_identity_paths(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    events, _, _ = _trace_restore_primitives(monkeypatch)

    def forbid_readlink(*args: object, **kwargs: object) -> str:
        raise AssertionError((args, kwargs, "trace must not use readlink"))

    def stop_after_allocation(boundary: str) -> None:
        if boundary == "restore_before_first_live_mutation":
            raise InstallError("portable trace stop")

    monkeypatch.setattr(os, "readlink", forbid_readlink)
    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        stop_after_allocation,
    )

    with pytest.raises(InstallError, match="portable trace stop"):
        oracle_install.restore_preloader(
            installed_patched_game,
            repo_root=Path("/unused"),
        )

    assert events
    for event in events:
        if event[0] == "open":
            assert event[7].is_absolute(), event
        elif event[0] in {"fstat", "read", "scandir"}:
            assert event[-1].is_absolute(), event
        elif event[0] == "stat":
            assert event[5].is_absolute(), event
        elif event[0] == "fsync":
            assert event[3].is_absolute(), event
        elif event[0] == "renameatx":
            assert event[10].is_absolute(), event
            assert event[11].is_absolute(), event


def _restore_stable_read_trace_events(
    path: Path,
    identity: tuple[int, int],
    size: int,
    read_lengths: tuple[int, ...],
    *,
    descriptor: int = 41,
) -> list[tuple[object, ...]]:
    events: list[tuple[object, ...]] = [
        ("fstat", identity, descriptor, size, path)
    ]
    events.extend(
        ("read", identity, max(size, 1), length, descriptor, path)
        for length in read_lengths
    )
    events.append(("fstat", identity, descriptor, size, path))
    return events


def test_restore_boundary_trace_accepts_one_terminal_eof_at_expected_size(
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    path, identity, _, payload = evidence["backup"]
    assert payload is not None

    _assert_restore_boundary_events(
        "restore_after_backup_snapshot_validation",
        _restore_stable_read_trace_events(
            path, identity, len(payload), (len(payload), 0)
        ),
        [],
        installed_patched_game,
        evidence,
        {},
    )


@pytest.mark.parametrize(
    "invalid_sequence",
    [
        "premature_eof",
        "repeated_eof",
        "data_after_eof",
        "missing_eof",
        "data_beyond_expected_size",
    ],
    ids=[
        "premature-eof",
        "repeated-eof",
        "data-after-eof",
        "missing-eof",
        "data-beyond-expected-size",
    ],
)
def test_restore_boundary_trace_rejects_invalid_stable_read_sequences(
    invalid_sequence: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    path, identity, _, payload = evidence["backup"]
    assert payload is not None and len(payload) > 1
    size = len(payload)
    read_lengths = {
        "premature_eof": (1, 0),
        "repeated_eof": (size, 0, 0),
        "data_after_eof": (size, 0, 1),
        "missing_eof": (size,),
        "data_beyond_expected_size": (size + 1, 0),
    }[invalid_sequence]

    with pytest.raises(AssertionError):
        _assert_restore_boundary_events(
            "restore_after_backup_snapshot_validation",
            _restore_stable_read_trace_events(
                path, identity, size, read_lengths
            ),
            [],
            installed_patched_game,
            evidence,
            {},
        )


@pytest.mark.parametrize(
    "corruption",
    ["missing_live_absence_stat", "wrong_recovery_scan_target"],
)
def test_restore_final_status_trace_rejects_incomplete_semantic_evidence(
    corruption: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    events, created, _ = _trace_restore_primitives(monkeypatch)
    event_start: int | None = None
    checked = False

    def corrupt_final_trace(boundary: str) -> None:
        nonlocal event_start, checked
        if boundary == "restore_before_final_status_verification":
            event_start = len(events)
            return
        if boundary != "restore_after_final_status_verification":
            return
        assert event_start is not None
        paired = list(events[event_start:])
        if corruption == "missing_live_absence_stat":
            omitted = Path(BACKUP_ROOT).name
            paired = [
                event
                for event in paired
                if not (event[0] == "stat" and event[2] == omitted)
            ]
        else:
            scan_index = next(
                index
                for index, event in enumerate(paired)
                if event[0] == "scandir"
            )
            scan = paired[scan_index]
            paired[scan_index] = (*scan[:3], installed_patched_game / "BepInEx")
        with pytest.raises(AssertionError):
            _assert_restore_boundary_events(
                boundary,
                paired,
                events[:event_start],
                installed_patched_game,
                evidence,
                created,
            )
        checked = True
        raise InstallError("negative final-status trace proof stop")

    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        corrupt_final_trace,
    )
    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game,
            repo_root=Path("/unused"),
        )
    assert checked


def _restore_rollback_swap_trace(
    game: Path,
    target: str,
    source_identity: tuple[int, int],
    destination_identity: tuple[int, int],
) -> tuple[object, ...]:
    parent = game if target == "manifest" else game / "BepInEx/core"
    leaf = (
        oracle_install.MANIFEST_NAME
        if target == "manifest"
        else "BepInEx.Preloader.dll"
    )
    return (
        "renameatx",
        _restore_path_identity(parent),
        f".ssr-oracle-restore-{target}-proof",
        _restore_path_identity(parent),
        leaf,
        oracle_install._RENAME_SWAP,
        source_identity,
        destination_identity,
        -1,
        -1,
        parent,
        parent,
    )


@pytest.mark.parametrize("target", ["active", "manifest"])
def test_restore_boundary_trace_accepts_exact_rollback_swap_sides(
    target: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    created_identity = (999_991, 888_881)
    event = _restore_rollback_swap_trace(
        installed_patched_game,
        target,
        evidence[target][1],
        created_identity,
    )

    _assert_restore_boundary_events(
        f"restore_rollback_after_{target}_swap",
        [event],
        [],
        installed_patched_game,
        evidence,
        {created_identity: event[10] / event[2]},
    )


@pytest.mark.parametrize("target", ["active", "manifest"])
@pytest.mark.parametrize(
    "corruption",
    ["reversed_sides", "inexact_source", "inexact_destination"],
)
def test_restore_boundary_trace_rejects_inexact_rollback_swap_sides(
    target: str,
    corruption: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    created_identity = (999_992, 888_882)
    source_identity = evidence[target][1]
    destination_identity = created_identity
    if corruption == "reversed_sides":
        source_identity, destination_identity = (
            destination_identity,
            source_identity,
        )
    elif corruption == "inexact_source":
        source_identity = (777_771, 666_661)
    else:
        destination_identity = (777_772, 666_662)
    event = _restore_rollback_swap_trace(
        installed_patched_game,
        target,
        source_identity,
        destination_identity,
    )

    with pytest.raises(AssertionError):
        _assert_restore_boundary_events(
            f"restore_rollback_after_{target}_swap",
            [event],
            [],
            installed_patched_game,
            evidence,
            {created_identity: event[10] / event[2]},
        )


@pytest.mark.parametrize(
    "wrong_primitive",
    ["validation", "rename", "fsync", "open", "mkdir"],
)
def test_restore_boundary_trace_rejects_unrelated_descriptor_calls(
    wrong_primitive: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    unrelated = (999_999, 888_888)
    if wrong_primitive == "validation":
        boundary = "restore_after_backup_snapshot_validation"
        paired = [
            ("fstat", unrelated),
            ("read", unrelated, 4096, 32),
        ]
        prior: list[tuple[object, ...]] = []
        created: dict[tuple[int, int], Path] = {}
    else:
        recovery = installed_patched_game / ".ssr-oracle-recovery"
        recovery.mkdir(exist_ok=True)
        run = recovery / f"20000101T000000.000000Z-{'a' * 32}"
        run.mkdir()
        cleanup = run / "cleanup"
        cleanup.mkdir()
        recovered_backup_parent = run / "compat" / BACKUP_ROOT
        recovered_backup_parent.mkdir(parents=True)
        wrong_directory = run / "wrong-created"
        wrong_directory.mkdir()
        recovery_identity = _restore_path_identity(recovery)
        run_identity = _restore_path_identity(run)
        cleanup_identity = _restore_path_identity(cleanup)
        recovered_backup_identity = _restore_path_identity(
            recovered_backup_parent
        )
        wrong_identity = _restore_path_identity(wrong_directory)
        source_path = evidence["backup"][0]
        os.link(source_path, cleanup / source_path.name)
        forward_rename = (
            "renameatx",
            _restore_path_identity(source_path.parent),
            source_path.name,
            recovered_backup_identity,
            source_path.name,
            oracle_install._RENAME_EXCL,
            evidence["backup"][1],
            None,
            -1,
            -1,
            source_path.parent,
            recovered_backup_parent,
        )
        created = {wrong_identity: wrong_directory}
        if wrong_primitive == "rename":
            boundary = "restore_after_backup_move"
            paired = [
                (
                    "renameatx",
                    cleanup_identity,
                    source_path.name,
                    recovered_backup_identity,
                    source_path.name,
                    oracle_install._RENAME_EXCL,
                    evidence["backup"][1],
                    None,
                    -1,
                    -1,
                    cleanup,
                    recovered_backup_parent,
                )
            ]
            prior = []
        elif wrong_primitive == "fsync":
            boundary = "restore_after_backup_source_parent_fsync"
            paired = [("fsync", recovered_backup_identity, -1, recovered_backup_parent)]
            prior = [forward_rename]
        elif wrong_primitive == "open":
            boundary = "restore_after_recovery_compat_open"
            paired = [
                (
                    "open",
                    run_identity,
                    wrong_directory.name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    wrong_identity,
                    -1,
                    -1,
                    wrong_directory,
                )
            ]
            prior = []
        else:
            boundary = "restore_after_recovery_compat_create"
            paired = [
                (
                    "mkdir",
                    run_identity,
                    wrong_directory.name,
                    0o700,
                    wrong_identity,
                    -1,
                    wrong_directory,
                )
            ]
            prior = []
    with pytest.raises(AssertionError):
        _assert_restore_boundary_events(
            boundary,
            paired,
            prior,
            installed_patched_game,
            evidence,
            created,
        )


@pytest.mark.parametrize("boundary", RESTORE_FORWARD_BOUNDARIES)
def test_restore_forward_failure_boundaries_restore_or_preserve_every_copy(
    boundary: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    before = _tree_snapshot_without_recovery(installed_patched_game)
    evidence = _restore_preflight_evidence(installed_patched_game)
    events, created_identities, _ = _trace_restore_primitives(monkeypatch)
    paired_before = boundary.replace("restore_after_", "restore_before_", 1)
    event_start: int | None = None
    observed: list[str] = []

    def fail_at_operation(observed_boundary: str) -> None:
        nonlocal event_start
        observed.append(observed_boundary)
        if boundary.startswith("restore_after_") and (
            observed_boundary == paired_before
        ):
            event_start = len(events)
        if observed_boundary != boundary:
            return
        if boundary.startswith("restore_after_"):
            assert event_start is not None, (
                boundary,
                "missing paired before checkpoint",
            )
            _assert_restore_boundary_events(
                boundary,
                events[event_start:],
                events[:event_start],
                installed_patched_game,
                evidence,
                created_identities,
            )
        raise InstallError(f"injected {boundary} failure")

    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        fail_at_operation,
        raising=False,
    )

    with pytest.raises(
        InstallError,
        match=f"injected {boundary}|restore_preloader",
    ) as raised:
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert boundary in observed
    current = _tree_snapshot_without_recovery(installed_patched_game)
    if current != before:
        assert "rollback" in str(raised.value).lower()
        _assert_restore_evidence_at_original_or_recovery(
            installed_patched_game, evidence
        )
    else:
        status = status_install(
            installed_patched_game, repo_root=Path("/unused")
        )
        assert status.preloader_compatibility.state == "patched"
        for label, (
            path,
            identity,
            mode,
            payload,
        ) in evidence.items():
            observed_stat = path.stat(follow_symlinks=False)
            assert (observed_stat.st_dev, observed_stat.st_ino) == identity, label
            assert stat.S_IMODE(observed_stat.st_mode) == mode, label
            if payload is not None:
                assert path.read_bytes() == payload, label
    _assert_created_restore_identities_retained(
        installed_patched_game, created_identities
    )


RESTORE_ROLLBACK_BOUNDARIES = [
    "restore_rollback_before_backup_directory_restore",
    "restore_rollback_after_backup_directory_restore",
    "restore_rollback_before_backup_directory_validation",
    "restore_rollback_after_backup_directory_validation",
    "restore_rollback_before_backup_directory_source_parent_fsync",
    "restore_rollback_after_backup_directory_source_parent_fsync",
    "restore_rollback_before_backup_directory_destination_parent_fsync",
    "restore_rollback_after_backup_directory_destination_parent_fsync",
    "restore_rollback_before_compat_directory_restore",
    "restore_rollback_after_compat_directory_restore",
    "restore_rollback_before_compat_directory_validation",
    "restore_rollback_after_compat_directory_validation",
    "restore_rollback_before_compat_directory_source_parent_fsync",
    "restore_rollback_after_compat_directory_source_parent_fsync",
    "restore_rollback_before_compat_directory_destination_parent_fsync",
    "restore_rollback_after_compat_directory_destination_parent_fsync",
    "restore_rollback_before_active_swap",
    "restore_rollback_after_active_swap",
    "restore_rollback_before_active_displaced_validation",
    "restore_rollback_after_active_displaced_validation",
    "restore_rollback_before_active_staging_parent_fsync",
    "restore_rollback_after_active_staging_parent_fsync",
    "restore_rollback_before_active_live_parent_fsync",
    "restore_rollback_after_active_live_parent_fsync",
    "restore_rollback_before_backup_restore",
    "restore_rollback_after_backup_restore",
    "restore_rollback_before_backup_snapshot_validation",
    "restore_rollback_after_backup_snapshot_validation",
    "restore_rollback_before_backup_source_parent_fsync",
    "restore_rollback_after_backup_source_parent_fsync",
    "restore_rollback_before_backup_destination_parent_fsync",
    "restore_rollback_after_backup_destination_parent_fsync",
    "restore_rollback_before_provenance_restore",
    "restore_rollback_after_provenance_restore",
    "restore_rollback_before_provenance_snapshot_validation",
    "restore_rollback_after_provenance_snapshot_validation",
    "restore_rollback_before_provenance_source_parent_fsync",
    "restore_rollback_after_provenance_source_parent_fsync",
    "restore_rollback_before_provenance_destination_parent_fsync",
    "restore_rollback_after_provenance_destination_parent_fsync",
    "restore_rollback_before_manifest_swap",
    "restore_rollback_after_manifest_swap",
    "restore_rollback_before_manifest_displaced_validation",
    "restore_rollback_after_manifest_displaced_validation",
    "restore_rollback_before_manifest_staging_parent_fsync",
    "restore_rollback_after_manifest_staging_parent_fsync",
    "restore_rollback_before_manifest_live_parent_fsync",
    "restore_rollback_after_manifest_live_parent_fsync",
    "restore_rollback_before_temporary_preservation",
    "restore_rollback_after_temporary_preservation",
    "restore_rollback_before_displaced_preservation",
    "restore_rollback_after_displaced_preservation",
    "restore_rollback_before_cleanup_preservation_source_parent_fsync",
    "restore_rollback_after_cleanup_preservation_source_parent_fsync",
    "restore_rollback_before_cleanup_preservation_destination_parent_fsync",
    "restore_rollback_after_cleanup_preservation_destination_parent_fsync",
    "restore_rollback_before_recovery_directory_fsync",
    "restore_rollback_after_recovery_directory_fsync",
]


@pytest.mark.parametrize("boundary", RESTORE_ROLLBACK_BOUNDARIES)
def test_restore_rollback_failure_boundaries_report_both_errors_and_preserve_copies(
    boundary: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    evidence = _restore_preflight_evidence(installed_patched_game)
    events, created_identities, _ = _trace_restore_primitives(monkeypatch)
    paired_before = boundary.replace(
        "restore_rollback_after_",
        "restore_rollback_before_",
        1,
    )
    event_start: int | None = None
    forward_failed = False
    observed: list[str] = []

    def fail(observed_boundary: str) -> None:
        nonlocal event_start, forward_failed
        observed.append(observed_boundary)
        if (
            not forward_failed
            and observed_boundary == "restore_after_compat_directory_move"
        ):
            forward_failed = True
            raise InstallError("injected primary restore failure")
        if (
            forward_failed
            and boundary.startswith("restore_rollback_after_")
            and observed_boundary == paired_before
        ):
            event_start = len(events)
        if forward_failed and observed_boundary == boundary:
            if boundary.startswith("restore_rollback_after_"):
                assert event_start is not None
                _assert_restore_boundary_events(
                    boundary,
                    events[event_start:],
                    events[:event_start],
                    installed_patched_game,
                    evidence,
                    created_identities,
                )
            raise InstallError(f"injected {boundary} failure")

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", fail, raising=False
    )
    with pytest.raises(InstallError) as raised:
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert boundary in observed
    error_text = str(raised.value)
    assert "injected primary restore failure" in error_text
    assert f"injected {boundary} failure" in error_text
    assert "rollback" in error_text.lower()
    assert _restore_recovery_runs(installed_patched_game)
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, evidence
    )
    _assert_created_restore_identities_retained(
        installed_patched_game, created_identities
    )


@pytest.mark.parametrize("target", ["active", "manifest"])
def test_restore_forward_displaced_inode_mismatch_swaps_back_exact_live_leaf(
    target: str,
    installed_patched_game: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    paths = _restore_paths(installed_patched_game)
    preflight = _restore_preflight_evidence(installed_patched_game)
    _, created_identities, _ = _trace_restore_primitives(monkeypatch)
    traced_renameatx = oracle_install._renameatx
    live = paths[target]
    held = tmp_path / f"held-forward-{target}"
    marker = f"unrelated-forward-{target}".encode()
    marker_evidence: tuple[int, int, int, bytes] | None = None
    staged_identity: tuple[int, int] | None = None
    observed_checkpoints: list[str] = []
    swap_calls = 0
    mismatch_injected = False
    original_renameatx = oracle_install._renameatx

    def checkpoint(boundary: str) -> None:
        nonlocal marker_evidence, mismatch_injected
        observed_checkpoints.append(boundary)
        if boundary != f"restore_before_{target}_swap" or mismatch_injected:
            return
        mismatch_injected = True
        live.rename(held)
        live.write_bytes(marker)
        marker_evidence = _restore_file_evidence(live)

    def trace_swap(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal staged_identity, swap_calls
        if mismatch_injected and flags & oracle_install._RENAME_SWAP:
            swap_calls += 1
            if staged_identity is None:
                observed = os.stat(
                    source,
                    dir_fd=source_parent.fd,
                    follow_symlinks=False,
                )
                staged_identity = (observed.st_dev, observed.st_ino)
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", checkpoint, raising=False
    )
    monkeypatch.setattr(oracle_install, "_renameatx", trace_swap)
    with pytest.raises(
        InstallError, match=f"{target}.*changed|displaced.*{target}"
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert mismatch_injected
    assert swap_calls >= 2
    assert f"restore_after_{target}_swap_back" in observed_checkpoints
    assert marker_evidence is not None
    assert _restore_file_evidence(live) == marker_evidence
    original = preflight[target]
    assert _restore_file_evidence(held) == (
        original[1][0],
        original[1][1],
        original[2],
        original[3],
    )
    assert staged_identity is not None
    staged_locations = _restore_inode_locations(
        (installed_patched_game,), staged_identity
    )
    assert len(staged_locations) == 1
    runs = _restore_recovery_runs(installed_patched_game)
    assert any(
        location == run or run in location.parents
        for location in staged_locations
        for run in runs
    )
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, preflight, tmp_path
    )
    _assert_created_restore_identities_retained(
        installed_patched_game, created_identities
    )


@pytest.mark.parametrize("target", ["active", "manifest"])
def test_restore_rollback_displaced_inode_mismatch_swaps_back_exact_live_leaf(
    target: str,
    installed_patched_game: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    paths = _restore_paths(installed_patched_game)
    preflight = _restore_preflight_evidence(installed_patched_game)
    _, created_identities, _ = _trace_restore_primitives(monkeypatch)
    live = paths[target]
    held = tmp_path / f"held-rollback-{target}"
    marker = f"unrelated-rollback-{target}".encode()
    marker_evidence: tuple[int, int, int, bytes] | None = None
    held_evidence: tuple[int, int, int, bytes] | None = None
    observed_checkpoints: list[str] = []
    rollback_started = False
    swap_calls = 0
    original_renameatx = oracle_install._renameatx

    def checkpoint(boundary: str) -> None:
        nonlocal held_evidence, marker_evidence, rollback_started
        observed_checkpoints.append(boundary)
        if (
            not rollback_started
            and boundary == "restore_after_compat_directory_move"
        ):
            rollback_started = True
            raise InstallError("injected primary restore failure")
        if (
            rollback_started
            and boundary == f"restore_rollback_before_{target}_swap"
            and marker_evidence is None
        ):
            live.rename(held)
            held_evidence = _restore_file_evidence(held)
            live.write_bytes(marker)
            marker_evidence = _restore_file_evidence(live)

    def trace_swap(*args, **kwargs):
        nonlocal swap_calls
        flags = args[4] if len(args) > 4 else kwargs["flags"]
        if marker_evidence is not None and flags & oracle_install._RENAME_SWAP:
            swap_calls += 1
        return original_renameatx(*args, **kwargs)

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", checkpoint, raising=False
    )
    monkeypatch.setattr(oracle_install, "_renameatx", trace_swap)
    with pytest.raises(
        InstallError,
        match=r"injected primary restore failure.*rollback.*changed",
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert rollback_started
    assert marker_evidence is not None
    assert held_evidence is not None
    assert swap_calls >= 2
    assert f"restore_rollback_after_{target}_swap_back" in observed_checkpoints
    assert _restore_file_evidence(live) == marker_evidence
    assert _restore_file_evidence(held) == held_evidence
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, preflight, tmp_path
    )
    patched_locations = _restore_inode_locations(
        (installed_patched_game,), preflight[target][1]
    )
    assert len(patched_locations) == 1
    runs = _restore_recovery_runs(installed_patched_game)
    assert patched_locations[0] == preflight[target][0] or any(
        patched_locations[0] == run or run in patched_locations[0].parents
        for run in runs
    )
    _assert_created_restore_identities_retained(
        installed_patched_game, created_identities, tmp_path
    )


@pytest.mark.parametrize(
    ("target", "race"),
    [
        (target, race)
        for target in (
            "backup",
            "provenance",
            "active",
            "manifest",
            "backup_directory",
            "compat_directory",
        )
        for race in ("parent_replacement", "source_substitution")
    ]
    + [
        ("active", "live_leaf_substitution"),
        ("manifest", "live_leaf_substitution"),
    ],
)
def test_restore_descriptor_relative_races_preserve_unrelated_objects(
    target: str,
    race: str,
    installed_patched_game: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    paths = _restore_paths(installed_patched_game)
    preflight = _restore_preflight_evidence(installed_patched_game)
    _, created_identities, descriptor_path = _trace_restore_primitives(
        monkeypatch
    )
    traced_renameatx = oracle_install._renameatx
    target_path = paths[target]
    marker = f"unrelated-{target}-{race}".encode()
    held = tmp_path / f"held-{target}-{race}"
    injected = False
    held_identity: tuple[int, int] | None = None
    marker_identity: tuple[int, int] | None = None
    recovery_run_identity: tuple[int, int] | None = None
    armed = False
    operation_seen = False
    substitution_path: Path | None = None
    substitution_held: Path | None = None

    def race_at(boundary: str) -> None:
        nonlocal armed
        expected = f"restore_before_{target}_{race}"
        if boundary == expected:
            armed = True

    def create_descriptor_replacement(
        parent,
        name: str,
        directory: bool,
    ) -> tuple[int, int]:
        if directory:
            os.mkdir(name, 0o700, dir_fd=parent.fd)
            directory_fd = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent.fd,
            )
            try:
                marker_fd = os.open(
                    "keep",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory_fd,
                )
                try:
                    os.write(marker_fd, marker)
                    observed = os.fstat(marker_fd)
                finally:
                    os.close(marker_fd)
            finally:
                os.close(directory_fd)
        else:
            marker_fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent.fd,
            )
            try:
                os.write(marker_fd, marker)
                observed = os.fstat(marker_fd)
            finally:
                os.close(marker_fd)
        return observed.st_dev, observed.st_ino

    def inject_at_next_rename(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal armed, held_identity, injected
        nonlocal marker_identity, operation_seen, recovery_run_identity
        nonlocal substitution_path, substitution_held
        if armed:
            armed = False
            injected = True
            operation_seen = True
            runs_before_race = _restore_recovery_runs(installed_patched_game)
            assert len(runs_before_race) == 1
            run_stat = runs_before_race[0].stat(follow_symlinks=False)
            recovery_run_identity = (run_stat.st_dev, run_stat.st_ino)
            if race == "parent_replacement":
                parent = target_path.parent
                parent.rename(held)
                parent.mkdir()
                held_stat = held.stat(follow_symlinks=False)
                held_identity = (held_stat.st_dev, held_stat.st_ino)
                marker_path = parent / "unrelated-parent-marker"
                marker_path.write_bytes(marker)
                marker_stat = marker_path.stat(follow_symlinks=False)
                marker_identity = (marker_stat.st_dev, marker_stat.st_ino)
            else:
                operation_parent = (
                    destination_parent
                    if race == "live_leaf_substitution"
                    else source_parent
                )
                operation_name = (
                    destination
                    if race == "live_leaf_substitution"
                    else source
                )
                substitution_path = (
                    descriptor_path(operation_parent.fd) / operation_name
                )
                observed = os.stat(
                    operation_name,
                    dir_fd=operation_parent.fd,
                    follow_symlinks=False,
                )
                is_directory = stat.S_ISDIR(observed.st_mode)
                operation_held = held
                if race == "source_substitution":
                    runs = _restore_recovery_runs(installed_patched_game)
                    assert len(runs) == 1
                    operation_held = (
                        runs[0] / "cleanup" / f"race-held-{target}"
                    )
                    substitution_held = operation_held
                os.rename(
                    operation_name,
                    operation_held,
                    src_dir_fd=operation_parent.fd,
                )
                held_stat = operation_held.stat(follow_symlinks=False)
                held_identity = (held_stat.st_dev, held_stat.st_ino)
                marker_identity = create_descriptor_replacement(
                    operation_parent,
                    operation_name,
                    is_directory,
                )
        return traced_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", race_at, raising=False
    )
    monkeypatch.setattr(
        oracle_install, "_renameatx", inject_at_next_rename
    )
    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert operation_seen
    assert not armed
    assert held_identity is not None
    assert marker_identity is not None
    assert recovery_run_identity is not None
    held_locations = _restore_inode_locations((tmp_path,), held_identity)
    marker_locations = _restore_inode_locations((tmp_path,), marker_identity)
    assert len(held_locations) == 1
    assert len(marker_locations) == 1
    assert marker_locations[0].read_bytes() == marker
    if race == "source_substitution" and target in {
        "active",
        "manifest",
        "backup_directory",
        "compat_directory",
    }:
        assert substitution_path is not None
        assert substitution_held is not None
        assert held_locations == (substitution_held,)
        expected_marker_path = (
            substitution_path / "keep"
            if target.endswith("_directory")
            else substitution_path
        )
        assert marker_locations == (expected_marker_path,)
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, preflight, tmp_path
    )
    retained_runs = _restore_inode_locations(
        (tmp_path,), recovery_run_identity
    )
    assert len(retained_runs) == 1
    _assert_created_restore_identities_retained(
        installed_patched_game,
        created_identities,
        retained_runs[0].parent,
    )


def _create_restore_collision_at(
    source_parent,
    source: str,
    destination_parent,
    destination: str,
    marker: bytes,
) -> tuple[tuple[int, int], tuple[int, int] | None]:
    source_stat = os.stat(
        source,
        dir_fd=source_parent.fd,
        follow_symlinks=False,
    )
    child_identity: tuple[int, int] | None = None
    if stat.S_ISDIR(source_stat.st_mode):
        os.mkdir(destination, 0o700, dir_fd=destination_parent.fd)
        directory_fd = os.open(
            destination,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=destination_parent.fd,
        )
        try:
            child_fd = os.open(
                "keep",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory_fd,
            )
            try:
                os.write(child_fd, marker)
                child_stat = os.fstat(child_fd)
                child_identity = (child_stat.st_dev, child_stat.st_ino)
            finally:
                os.close(child_fd)
        finally:
            os.close(directory_fd)
    else:
        descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=destination_parent.fd,
        )
        try:
            os.write(descriptor, marker)
        finally:
            os.close(descriptor)
    observed = os.stat(
        destination,
        dir_fd=destination_parent.fd,
        follow_symlinks=False,
    )
    return (observed.st_dev, observed.st_ino), child_identity


@pytest.mark.parametrize(
    "target",
    [
        "backup",
        "provenance",
        "backup_directory",
        "compat_directory",
        "cleanup_preservation",
    ],
)
def test_restore_forward_destination_collision_uses_exact_operation_destination(
    target: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    preflight = _restore_preflight_evidence(installed_patched_game)
    marker = f"forward-collision-{target}".encode()
    attempts = 0
    armed = False
    injected = False
    collision_identity: tuple[int, int] | None = None
    child_identity: tuple[int, int] | None = None
    original_renameatx = oracle_install._renameatx
    boundary = (
        f"restore_before_{target}_move"
        if target != "cleanup_preservation"
        else "restore_before_cleanup_preservation_move"
    )

    def checkpoint(observed_boundary: str) -> None:
        nonlocal armed
        if observed_boundary == boundary:
            armed = True

    def collide(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal armed, attempts, child_identity, collision_identity, injected
        if armed:
            armed = False
            injected = True
            attempts += 1
            assert flags & oracle_install._RENAME_EXCL
            collision_identity, child_identity = _create_restore_collision_at(
                source_parent,
                source,
                destination_parent,
                destination,
                marker,
            )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", checkpoint, raising=False
    )
    monkeypatch.setattr(oracle_install, "_renameatx", collide)
    with pytest.raises(InstallError, match="exist|collision"):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert attempts == 1
    assert collision_identity is not None
    collision_locations = _restore_inode_locations(
        (installed_patched_game,), collision_identity
    )
    assert len(collision_locations) == 1
    collision = collision_locations[0]
    if child_identity is None:
        assert collision.read_bytes() == marker
    else:
        child_locations = _restore_inode_locations(
            (installed_patched_game,), child_identity
        )
        assert len(child_locations) == 1
        assert child_locations[0].read_bytes() == marker
        assert collision in child_locations[0].parents
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, preflight
    )


@pytest.mark.parametrize(
    "target",
    [
        "backup",
        "provenance",
        "backup_directory",
        "compat_directory",
        "cleanup_preservation",
    ],
)
def test_restore_rollback_destination_collision_forces_rollback_and_preserves_both(
    target: str,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    preflight = _restore_preflight_evidence(installed_patched_game)
    marker = f"rollback-collision-{target}".encode()
    collision_identity: tuple[int, int] | None = None
    child_identity: tuple[int, int] | None = None
    attempts = 0
    armed = False
    injected = False
    rollback_started = False
    original_renameatx = oracle_install._renameatx
    boundary = (
        f"restore_rollback_before_{target}_restore"
        if target != "cleanup_preservation"
        else "restore_rollback_before_temporary_preservation"
    )

    def checkpoint(observed_boundary: str) -> None:
        nonlocal armed, rollback_started
        if (
            not rollback_started
            and observed_boundary == "restore_after_compat_directory_move"
        ):
            rollback_started = True
            raise InstallError("injected primary restore failure")
        if rollback_started and observed_boundary == boundary:
            armed = True

    def collide(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal armed, attempts, child_identity, collision_identity, injected
        if armed:
            armed = False
            injected = True
            attempts += 1
            assert flags & oracle_install._RENAME_EXCL
            collision_identity, child_identity = _create_restore_collision_at(
                source_parent,
                source,
                destination_parent,
                destination,
                marker,
            )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", checkpoint, raising=False
    )
    monkeypatch.setattr(oracle_install, "_renameatx", collide)
    with pytest.raises(InstallError) as raised:
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert rollback_started
    assert injected
    assert attempts == 1
    error_text = str(raised.value)
    assert "injected primary restore failure" in error_text
    assert "rollback" in error_text.lower()
    assert "exist" in error_text.lower() or "collision" in error_text.lower()
    assert collision_identity is not None
    collision_locations = _restore_inode_locations(
        (installed_patched_game,), collision_identity
    )
    assert len(collision_locations) == 1
    if child_identity is None:
        assert collision_locations[0].read_bytes() == marker
    else:
        child_locations = _restore_inode_locations(
            (installed_patched_game,), child_identity
        )
        assert len(child_locations) == 1
        assert child_locations[0].read_bytes() == marker
    assert _restore_recovery_runs(installed_patched_game)
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, preflight
    )


@pytest.mark.parametrize(
    "target",
    ["active", "manifest", "backup_directory", "compat_directory"],
)
def test_restore_post_verification_substitution_is_not_adopted_or_deleted(
    target: str,
    installed_patched_game: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    paths = _restore_paths(installed_patched_game)
    preflight = _restore_preflight_evidence(installed_patched_game)
    _, created_identities, descriptor_path = _trace_restore_primitives(
        monkeypatch
    )
    traced_renameatx = oracle_install._renameatx
    marker = f"post-verification-{target}".encode()
    held = tmp_path / f"held-post-verification-{target}"
    injected = False
    armed = False
    interceptor_calls = 0
    held_identity: tuple[int, int] | None = None
    marker_identity: tuple[int, int] | None = None

    def arm_substitution(boundary: str) -> None:
        nonlocal armed
        if boundary == f"restore_after_{target}_verification":
            assert not armed
            armed = True

    def substitute_at_next_namespace_operation(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal armed, held_identity, injected, interceptor_calls
        nonlocal marker_identity
        if armed:
            expected_leaf, expected_flags = {
                "active": (
                    oracle_install.MANIFEST_NAME,
                    oracle_install._RENAME_SWAP,
                ),
                "manifest": (
                    ".ssr-oracle-backup",
                    oracle_install._RENAME_EXCL,
                ),
                "backup_directory": (
                    ".ssr-oracle-backup",
                    oracle_install._RENAME_EXCL,
                ),
                "compat_directory": (
                    ".ssr-oracle-compat",
                    oracle_install._RENAME_EXCL,
                ),
            }[target]
            source_parent_path = descriptor_path(source_parent.fd)
            destination_parent_path = descriptor_path(destination_parent.fd)
            source_path = source_parent_path / source
            destination_path = destination_parent_path / destination
            source_identity = _restore_path_identity(source_path)
            try:
                destination_identity = _restore_path_identity(destination_path)
            except FileNotFoundError:
                destination_identity = None
            assert flags == expected_flags
            if target == "active":
                assert source_parent_path == installed_patched_game
                assert source_identity in created_identities
                assert created_identities[source_identity] == source_path
                assert destination == oracle_install.MANIFEST_NAME
                assert destination_parent_path == installed_patched_game
                assert destination_identity == preflight["manifest"][1]
            else:
                expected_key = {
                    "manifest": "backup_directory",
                    "backup_directory": "backup_directory",
                    "compat_directory": "compat_directory",
                }[target]
                assert source == expected_leaf
                assert source_parent_path == installed_patched_game / "BepInEx"
                assert source_identity == preflight[expected_key][1]
                assert destination == expected_leaf
                recovery_runs = _restore_recovery_runs(installed_patched_game)
                assert len(recovery_runs) == 1
                assert destination_parent_path == recovery_runs[0] / "cleanup"
                assert destination_identity is None
            assert (
                source_parent.device,
                source_parent.inode,
            ) == _restore_path_identity(source_parent_path)
            assert (
                destination_parent.device,
                destination_parent.inode,
            ) == _restore_path_identity(destination_parent_path)
            armed = False
            injected = True
            interceptor_calls += 1

            path = paths[target]
            path.rename(held)
            held_stat = held.stat(follow_symlinks=False)
            held_identity = (held_stat.st_dev, held_stat.st_ino)
            if target.endswith("_directory"):
                path.mkdir()
                marker_path = path / "keep"
                marker_path.write_bytes(marker)
            else:
                path.write_bytes(marker)
                marker_path = path
            marker_stat = marker_path.stat(follow_symlinks=False)
            marker_identity = (marker_stat.st_dev, marker_stat.st_ino)
        return traced_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        arm_substitution,
        raising=False,
    )
    monkeypatch.setattr(
        oracle_install,
        "_renameatx",
        substitute_at_next_namespace_operation,
    )
    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert interceptor_calls == 1
    assert not armed
    assert held_identity is not None
    assert marker_identity is not None
    held_locations = _restore_inode_locations((tmp_path,), held_identity)
    marker_locations = _restore_inode_locations((tmp_path,), marker_identity)
    assert len(held_locations) == 1
    assert len(marker_locations) == 1
    assert marker_locations[0].read_bytes() == marker
    _assert_restore_evidence_at_original_or_recovery(
        installed_patched_game, preflight, tmp_path
    )
    _assert_created_restore_identities_retained(
        installed_patched_game,
        created_identities,
        *((tmp_path,) if target in {"active", "manifest"} else ()),
    )


@pytest.mark.parametrize(
    "malformation",
    [
        "unsafe_path",
        "duplicate_path",
        "unapproved_path",
        "malformed_hash",
        "malformed_structure",
    ],
)
def test_restore_rejects_malformed_or_unsafe_manifest_before_recovery(
    malformation: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    manifest_path = installed_patched_game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    if malformation == "malformed_structure":
        decoded["entries"] = {"not": "a list"}
    elif malformation == "duplicate_path":
        decoded["entries"].append(dict(decoded["entries"][0]))
    elif malformation in {"unsafe_path", "unapproved_path"}:
        decoded["entries"].append(
            {
                "relative_path": (
                    "../escape"
                    if malformation == "unsafe_path"
                    else "not-owned/payload"
                ),
                "kind": "file",
                "sha256": "a" * 64,
            }
        )
    else:
        entry = next(
            candidate
            for candidate in decoded["entries"]
            if candidate["relative_path"] == ACTIVE_PATH
        )
        entry["sha256"] = "not-a-sha256"
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("source_commit", "0" * 40),
        ("dotnet_sdk_version", "0.0.0"),
        ("build_target", "Other.csproj@framework=net35"),
    ],
)
def test_restore_rejects_unpinned_provenance_fields_before_recovery(
    field: str,
    replacement: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    provenance = installed_patched_game / PROVENANCE_PATH
    decoded = json.loads(provenance.read_bytes())
    decoded[field] = replacement
    provenance.write_bytes(canonical_json(decoded))
    _replace_manifest_file_hash(installed_patched_game, PROVENANCE_PATH)
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


def test_restore_rejects_intermediate_symlink_in_game_root_path(
    installed_patched_game: Path,
    tmp_path: Path,
    restore_no_terminal_deletion: None,
) -> None:
    outer = tmp_path / "outer"
    outer.mkdir()
    (outer / "linked").symlink_to(
        installed_patched_game.parent, target_is_directory=True
    )
    aliased_game = outer / "linked" / installed_patched_game.name
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            aliased_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


@pytest.mark.parametrize("race", ["added_entry", "named_substitution"])
def test_restore_revalidates_live_compat_directory_after_initial_scan(
    race: str,
    installed_patched_game: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    backup_directory = installed_patched_game / BACKUP_ROOT
    injected = False
    marker = b"post-scan unrelated"

    def race_after_scan(boundary: str) -> None:
        nonlocal injected
        if boundary != "restore_before_preflight_revalidation" or injected:
            return
        injected = True
        if race == "added_entry":
            (backup_directory / "unrelated").write_bytes(marker)
        else:
            held = tmp_path / "held-backup-directory"
            backup_directory.rename(held)
            backup_directory.mkdir()
            (backup_directory / "unrelated").write_bytes(marker)

    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        race_after_scan,
        raising=False,
    )

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert _restore_recovery_runs(installed_patched_game) == ()
    assert (backup_directory / "unrelated").read_bytes() == marker


@pytest.mark.parametrize("race", ["descriptor_mode", "named_identity"])
def test_restore_rejects_file_or_named_mutation_during_snapshot_window(
    race: str,
    installed_patched_game: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    active = installed_patched_game / ACTIVE_PATH
    held = tmp_path / "held-active"
    original_read = oracle_install.os.read
    injected = False

    def mutate_mode_after_read(descriptor: int, size: int) -> bytes:
        nonlocal injected
        payload = original_read(descriptor, size)
        if payload == PATCHED_BYTES and not injected:
            injected = True
            if race == "descriptor_mode":
                active.chmod(0o600)
            else:
                active.rename(held)
                active.write_bytes(PATCHED_BYTES)
        return payload

    monkeypatch.setattr(oracle_install.os, "read", mutate_mode_after_read)
    expected_payload = active.read_bytes()

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert active.read_bytes() == expected_payload
    assert _restore_recovery_runs(installed_patched_game) == ()
    if race == "named_identity":
        assert held.read_bytes() == expected_payload


@pytest.mark.parametrize(
    ("boundary", "expected_publications"),
    [
        ("restore_before_recovery_run_publish", 0),
        ("restore_after_recovery_run_publish", 1),
    ],
)
def test_restore_checkpoint_eexist_never_retries_run_publication(
    boundary: str,
    expected_publications: int,
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    original_renameatx = oracle_install._renameatx
    name_calls = 0
    publications = 0

    def reviewed_name() -> str:
        nonlocal name_calls
        name_calls += 1
        return f"20260728T120000Z-{name_calls:032x}"

    def count_publications(*args, **kwargs):
        nonlocal publications
        if args[5] == "publish compatibility recovery run directory":
            publications += 1
        return original_renameatx(*args, **kwargs)

    def fail_checkpoint(observed: str) -> None:
        if observed == boundary:
            raise oracle_install._RenameAtError(
                errno.EEXIST, f"injected checkpoint EEXIST at {boundary}"
            )

    monkeypatch.setattr(oracle_install, "_compat_recovery_name", reviewed_name)
    monkeypatch.setattr(oracle_install, "_renameatx", count_publications)
    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", fail_checkpoint
    )
    before = _tree_snapshot_without_recovery(installed_patched_game)

    with pytest.raises(
        InstallError, match="injected checkpoint EEXIST|restore_preloader"
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert name_calls == 1
    assert publications == expected_publications
    assert _tree_snapshot_without_recovery(installed_patched_game) == before


@pytest.mark.parametrize(
    "aliased_path",
    [
        "BepInEx//core",
        "BepInEx/./core",
        "BepInEx/core/",
    ],
)
def test_restore_rejects_noncanonical_manifest_path_aliases(
    aliased_path: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    manifest_path = installed_patched_game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    entry = next(
        candidate
        for candidate in decoded["entries"]
        if candidate["relative_path"] == "BepInEx/core"
    )
    entry["relative_path"] = aliased_path
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


def test_restore_rejects_logical_duplicate_through_manifest_alias(
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    manifest_path = installed_patched_game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    original = next(
        candidate
        for candidate in decoded["entries"]
        if candidate["relative_path"] == "BepInEx/core"
    )
    duplicate = dict(original)
    duplicate["relative_path"] = "BepInEx//core"
    decoded["entries"].append(duplicate)
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


@pytest.mark.parametrize("schema_version", [True, 1.0])
def test_restore_rejects_non_integer_manifest_schema_version(
    schema_version: object,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    manifest_path = installed_patched_game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    decoded["schema_version"] = schema_version
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


def test_restore_accepts_valid_out_of_order_manifest_entries(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    manifest_path = installed_patched_game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    decoded["entries"] = list(reversed(decoded["entries"]))
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )
    reached_barrier = False

    def stop_at_barrier(boundary: str) -> None:
        nonlocal reached_barrier
        if boundary == "restore_before_first_live_mutation":
            reached_barrier = True
            raise InstallError("out-of-order manifest reached allocation barrier")

    monkeypatch.setattr(
        oracle_install, "_restore_preloader_checkpoint", stop_at_barrier
    )

    with pytest.raises(
        InstallError, match="out-of-order manifest reached allocation barrier"
    ):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert reached_barrier
    assert len(_restore_recovery_runs(installed_patched_game)) == 1


@pytest.mark.parametrize(
    "missing_path",
    ["run_bepinex.sh", "BepInEx/core"],
)
def test_restore_rejects_missing_required_runtime_manifest_ownership(
    missing_path: str,
    installed_patched_game: Path,
    restore_no_terminal_deletion: None,
) -> None:
    manifest_path = installed_patched_game / oracle_install.MANIFEST_NAME
    decoded = json.loads(manifest_path.read_bytes())
    decoded["entries"] = [
        entry
        for entry in decoded["entries"]
        if entry["relative_path"] != missing_path
    ]
    manifest_path.write_bytes(
        (json.dumps(decoded, sort_keys=True, indent=2) + "\n").encode()
    )
    before = _tree_snapshot(installed_patched_game)

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert _tree_snapshot(installed_patched_game) == before
    assert _restore_recovery_runs(installed_patched_game) == ()


def test_restore_revalidates_mutation_after_public_preflight_callback(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    active = installed_patched_game / ACTIVE_PATH
    injected = False

    def mutate_after_callback(boundary: str) -> None:
        nonlocal injected
        if boundary == "restore_after_preflight_revalidation":
            injected = True
            active.write_bytes(b"changed after public preflight callback")

    monkeypatch.setattr(
        oracle_install,
        "_restore_preloader_checkpoint",
        mutate_after_callback,
    )

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert _restore_recovery_runs(installed_patched_game) == ()


def test_restore_final_sweep_catches_cross_directory_first_sweep_race(
    installed_patched_game: Path,
    monkeypatch: pytest.MonkeyPatch,
    restore_no_terminal_deletion: None,
) -> None:
    backup_directory = installed_patched_game / BACKUP_ROOT
    compat_directory = installed_patched_game / COMPAT_ROOT
    compat_observed = compat_directory.stat(follow_symlinks=False)
    compat_identity = (compat_observed.st_dev, compat_observed.st_ino)
    original_scandir = oracle_install.os.scandir
    compat_scans = 0
    injected = False

    def mutate_backup_during_compat_rescan(target):
        nonlocal compat_scans, injected
        if isinstance(target, int):
            observed = os.fstat(target)
            if (observed.st_dev, observed.st_ino) == compat_identity:
                compat_scans += 1
                if compat_scans == 2:
                    injected = True
                    (backup_directory / "cross-directory-race").write_bytes(
                        b"unrelated"
                    )
        return original_scandir(target)

    monkeypatch.setattr(
        oracle_install.os, "scandir", mutate_backup_during_compat_rescan
    )

    with pytest.raises(InstallError):
        oracle_install.restore_preloader(
            installed_patched_game, repo_root=Path("/unused")
        )

    assert injected
    assert _restore_recovery_runs(installed_patched_game) == ()
    assert (
        backup_directory / "cross-directory-race"
    ).read_bytes() == b"unrelated"


def _restore_direct_sha256_result_edge(
    callee: ast.expr,
    imported_callables: dict[str, str],
) -> str | None:
    if not (
        isinstance(callee, ast.Attribute)
        and callee.attr == "hexdigest"
        and isinstance(callee.value, ast.Call)
        and isinstance(callee.value.func, ast.Name)
        and imported_callables.get(callee.value.func.id) == "hashlib.sha256"
    ):
        return None
    return "hashlib.sha256().hexdigest"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("sha256(payload).hexdigest()", "hashlib.sha256().hexdigest"),
        ("sha256(payload).digest()", None),
        ("other(payload).hexdigest()", None),
        ("sha256(payload).strftime()", None),
        ("datetime.now().strftime('%Y')", None),
    ],
)
def test_restore_static_graph_allows_only_direct_sha256_hexdigest_result_method(
    expression: str,
    expected: str | None,
    restore_no_terminal_deletion: None,
) -> None:
    call = ast.parse(expression, mode="eval").body
    assert isinstance(call, ast.Call)
    assert (
        _restore_direct_sha256_result_edge(
            call.func,
            {"sha256": "hashlib.sha256"},
        )
        == expected
    )


def test_restore_transaction_static_graph_has_no_terminal_deletion(
    restore_no_terminal_deletion: None,
) -> None:
    tree = ast.parse(
        Path("src/ssr_env/oracle_install.py").read_text(encoding="utf-8")
    )
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    class_nodes = {
        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
    }
    PASSIVE_DATACLASSES = {
        "GameInstall",
        "ArchiveMember",
        "ManifestEntry",
        "InstallManifest",
        "PreloaderCompatibilityStatus",
        "InstallStatus",
        "_FileSnapshot",
        "_StableFileSnapshot",
        "_FileIdentity",
        "_DirectoryHandle",
        "_CompatStaging",
        "_CompatRecovery",
        "_PathEvidence",
    }
    SAFE_LOCAL_EXCEPTIONS = {
        "InstallError",
        "_RenameAtError",
        "_RetainedDirectoryCollision",
    }
    forbidden_passive_hooks = {
        "__init__", "__post_init__", "__new__", "__setattr__", "__delattr__",
    }

    def is_dataclass_decorator(decorator: ast.expr) -> bool:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        return isinstance(target, ast.Name) and target.id == "dataclass"

    def has_default_factory(node: ast.ClassDef) -> bool:
        for statement in node.body:
            value = (
                statement.value
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                else None
            )
            if not isinstance(value, ast.Call):
                continue
            callee = value.func
            is_field = (
                isinstance(callee, ast.Name) and callee.id == "field"
            ) or (
                isinstance(callee, ast.Attribute)
                and isinstance(callee.value, ast.Name)
                and callee.value.id == "dataclasses"
                and callee.attr == "field"
            )
            if is_field and any(
                keyword.arg == "default_factory"
                for keyword in value.keywords
            ):
                return True
        return False

    assert PASSIVE_DATACLASSES <= class_nodes.keys()
    for name in PASSIVE_DATACLASSES:
        class_node = class_nodes[name]
        assert not class_node.keywords, (name, "metaclass/class keywords")
        assert len(class_node.decorator_list) == 1, (name, "extra decorators")
        assert is_dataclass_decorator(class_node.decorator_list[0]), name
        custom_hooks = {
            child.name
            for child in class_node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name in forbidden_passive_hooks
        }
        assert not custom_hooks, (name, custom_hooks)
        assert not has_default_factory(class_node), name

    builtin_exception_bases = {
        "BaseException", "Exception", "RuntimeError",
    }

    def is_exception_subclass(name: str, seen: set[str]) -> bool:
        if name in builtin_exception_bases:
            return True
        if name in seen or name not in class_nodes:
            return False
        seen = seen | {name}
        bases = class_nodes[name].bases
        return bool(bases) and all(
            isinstance(base, ast.Name)
            and is_exception_subclass(base.id, seen)
            for base in bases
        )

    assert SAFE_LOCAL_EXCEPTIONS <= class_nodes.keys()
    exception_hooks: dict[str, dict[str, ast.FunctionDef | ast.AsyncFunctionDef]] = {}
    for name in SAFE_LOCAL_EXCEPTIONS:
        class_node = class_nodes[name]
        assert is_exception_subclass(name, set()), name
        assert not class_node.decorator_list, (name, "exception decorator")
        assert not class_node.keywords, (name, "metaclass/class keywords")
        hooks = {
            child.name: child
            for child in class_node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name in {"__new__", "__init__"}
        }
        forbidden_hooks = {
            child.name
            for child in class_node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name.startswith("__")
            and child.name.endswith("__")
            and child.name not in {"__new__", "__init__"}
        }
        assert not forbidden_hooks, (name, forbidden_hooks)
        assert all(not hook.decorator_list for hook in hooks.values()), name
        exception_hooks[name] = hooks
        for hook_name, hook in hooks.items():
            functions[f"{name}.{hook_name}"] = hook
    imported_modules: dict[str, str] = {}
    imported_callables: dict[str, str] = {}
    import_aliases: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".", 1)[0]
                imported_modules[local_name] = alias.name
                if alias.asname is not None:
                    import_aliases.add(local_name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local_name = alias.asname or alias.name
                imported_callables[local_name] = (
                    f"{node.module}.{alias.name}"
                )
                if alias.asname is not None:
                    import_aliases.add(local_name)

    terminal = {"unlink", "remove", "rmdir", "removedirs", "rmtree"}
    forbidden_dynamic = {
        "eval", "exec", "getattr", "globals", "locals", "__import__",
        "attrgetter", "methodcaller", "partial",
    }
    allowed_builtin_calls = {
        "builtins.bool", "builtins.bytes", "builtins.bytearray",
        "builtins.dict", "builtins.enumerate", "builtins.frozenset",
        "builtins.int", "builtins.isinstance", "builtins.len",
        "builtins.list", "builtins.max", "builtins.min",
        "builtins.range", "builtins.reversed", "builtins.set",
        "builtins.sorted", "builtins.str", "builtins.super", "builtins.tuple",
        "builtins.zip",
    }
    allowed_external_calls = {
        "ctypes.get_errno",
        "datetime.datetime.now",
        "hashlib.sha256",
        "hashlib.sha256().hexdigest",
        "json.dumps",
        "json.loads",
        "os.close",
        "os.fchmod",
        "os.fstat",
        "os.fsync",
        "os.fsencode",
        "os.mkdir",
        "os.open",
        "os.read",
        "os.scandir",
        "os.stat",
        "os.strerror",
        "os.write",
        "pathlib.Path",
        "secrets.token_hex",
        "stat.S_ISDIR",
        "stat.S_ISLNK",
        "stat.S_ISREG",
        "ssr_env.oracle_compat.load_trust",
        "builtins.RuntimeError.__init__",
    }
    allowed_transaction_primitives = {
        "module_global._RENAMEATX_NP",
    }
    forbidden_external_prefixes = {
        "asyncio.create_subprocess", "multiprocessing", "os.exec",
        "os.fork", "os.forkpty", "os.popen", "os.posix_spawn",
        "os.spawn", "os.system", "pty", "subprocess",
    }
    allowed_exception_super_edges = {
        ("_RenameAtError.__init__", "__init__"):
            "builtins.RuntimeError.__init__",
    }

    pending = ["restore_preloader"]
    reachable: set[str] = set()
    observed_builtins: set[str] = set()
    observed_external: set[str] = set()
    observed_primitives: set[str] = set()
    violations: list[tuple[str, int, str]] = []

    def dotted_name(node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = dotted_name(node.value)
            return None if prefix is None else f"{prefix}.{node.attr}"
        return None

    while pending:
        function_name = pending.pop()
        if function_name in reachable:
            continue
        function = functions.get(function_name)
        assert function is not None, f"unresolved local edge: {function_name}"
        reachable.add(function_name)
        parents = {
            id(child): parent
            for parent in ast.walk(function)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(function):
            if (
                isinstance(node, (ast.Lambda, ast.ClassDef))
                or (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node is not function
                )
            ):
                violations.append(
                    (function_name, node.lineno, "dynamic callable definition")
                )
            if isinstance(node, ast.Name) and node.id in functions:
                parent = parents.get(id(node))
                if not (isinstance(parent, ast.Call) and parent.func is node):
                    violations.append(
                        (
                            function_name,
                            node.lineno,
                            f"indirect local function reference: {node.id}",
                        )
                    )
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            if isinstance(callee, ast.Name):
                name = callee.id
                if name in functions:
                    pending.append(name)
                elif name in terminal or name in forbidden_dynamic:
                    violations.append((function_name, node.lineno, name))
                elif name in PASSIVE_DATACLASSES:
                    pass
                elif name in SAFE_LOCAL_EXCEPTIONS:
                    pending.extend(
                        f"{name}.{hook_name}"
                        for hook_name in exception_hooks[name]
                    )
                elif name in import_aliases:
                    violations.append(
                        (
                            function_name,
                            node.lineno,
                            f"import alias forbidden: {name}",
                        )
                    )
                elif name in imported_callables:
                    observed_external.add(imported_callables[name])
                elif name in dir(builtins):
                    observed_builtins.add(f"builtins.{name}")
                elif f"module_global.{name}" in allowed_transaction_primitives:
                    observed_primitives.add(f"module_global.{name}")
                else:
                    violations.append(
                        (
                            function_name,
                            node.lineno,
                            f"unresolved bare callable: {name}",
                        )
                    )
            elif isinstance(callee, ast.Attribute):
                if callee.attr in terminal | forbidden_dynamic:
                    violations.append(
                        (function_name, node.lineno, callee.attr)
                    )
                    continue
                hash_result_edge = _restore_direct_sha256_result_edge(
                    callee,
                    imported_callables,
                )
                if hash_result_edge is not None:
                    observed_external.add(hash_result_edge)
                    continue
                is_super_hook = (
                    isinstance(callee.value, ast.Call)
                    and isinstance(callee.value.func, ast.Name)
                    and callee.value.func.id == "super"
                    and not callee.value.args
                    and not callee.value.keywords
                    and callee.attr in {"__new__", "__init__"}
                )
                if is_super_hook:
                    edge = allowed_exception_super_edges.get(
                        (function_name, callee.attr)
                    )
                    if edge is None:
                        violations.append(
                            (
                                function_name,
                                node.lineno,
                                f"unresolved exception super hook: {callee.attr}",
                            )
                        )
                    else:
                        observed_external.add(edge)
                    continue
                raw = dotted_name(callee)
                if raw is None:
                    violations.append(
                        (
                            function_name,
                            node.lineno,
                            "dynamic attribute dispatch",
                        )
                    )
                    continue
                root, dot, suffix = raw.partition(".")
                if root in import_aliases:
                    violations.append(
                        (
                            function_name,
                            node.lineno,
                            f"import alias forbidden: {root}",
                        )
                    )
                elif root in imported_modules and dot:
                    observed_external.add(
                        f"{imported_modules[root]}.{suffix}"
                    )
                elif root in imported_callables and dot:
                    observed_external.add(
                        f"{imported_callables[root]}.{suffix}"
                    )
                else:
                    violations.append(
                        (
                            function_name,
                            node.lineno,
                            f"unresolved object dispatch: {raw}",
                        )
                    )
            else:
                violations.append(
                    (function_name, node.lineno, "indirect call expression")
                )
    unlisted_builtins = observed_builtins - allowed_builtin_calls
    unlisted_external = observed_external - allowed_external_calls
    unlisted_primitives = observed_primitives - allowed_transaction_primitives
    launched_processes = {
        edge
        for edge in observed_external
        if any(
            edge == prefix or edge.startswith(prefix + ".")
            for prefix in forbidden_external_prefixes
        )
    }
    assert not unlisted_builtins, unlisted_builtins
    assert not unlisted_external, unlisted_external
    assert not unlisted_primitives, unlisted_primitives
    assert not launched_processes, launched_processes
    assert not violations, violations


def test_preserve_owned_directory_keeps_concurrent_replacement_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game_root = tmp_path / "game"
    parent_path = game_root / "parent"
    parent_path.mkdir(parents=True)
    owned = parent_path / "owned"
    owned.mkdir()
    parent = oracle_install._open_absolute_directory(
        parent_path,
        "cleanup test parent",
    )
    child = oracle_install._open_child_directory(
        parent,
        "owned",
        "owned cleanup test directory",
    )
    owned_identity = (child.device, child.inode)
    replacement_identity: tuple[int, int] | None = None
    original_renameatx = oracle_install._renameatx
    substituted = False
    game = oracle_install._open_absolute_directory(game_root, "test game")
    recovery = oracle_install._allocate_compat_recovery_fd(game)
    recovery_root = (
        game_root / ".ssr-oracle-recovery" / recovery.run_name / "cleanup"
    )
    recovered = recovery_root / "owned-directory"

    def substitute_after_quarantine(
        source_parent,
        source,
        destination_parent,
        destination,
        flags,
        description,
    ):
        nonlocal replacement_identity, substituted
        if (
            not substituted
            and description
            == "preserve owned cleanup test directory"
        ):
            substituted = True
            os.rename(
                source,
                recovered,
                src_dir_fd=source_parent.fd,
            )
            os.mkdir(source, dir_fd=source_parent.fd)
            replacement = os.stat(
                source,
                dir_fd=source_parent.fd,
                follow_symlinks=False,
            )
            replacement_identity = (
                replacement.st_dev,
                replacement.st_ino,
            )
        return original_renameatx(
            source_parent,
            source,
            destination_parent,
            destination,
            flags,
            description,
        )

    monkeypatch.setattr(
        oracle_install,
        "_renameatx",
        substitute_after_quarantine,
    )
    cleanup_error: InstallError | None = None
    try:
        try:
            oracle_install._preserve_owned_empty_directory_at(
                parent,
                "owned",
                child,
                recovery,
                "owned cleanup test",
            )
        except InstallError as exc:
            cleanup_error = exc
    finally:
        oracle_install._close_recovery(recovery)
        game.close()
        child.close()
        parent.close()

    assert substituted
    assert replacement_identity is not None
    observed_replacement = owned.stat()
    assert (
        observed_replacement.st_dev,
        observed_replacement.st_ino,
    ) == replacement_identity
    recovered_owned = [
        path
        for path in recovery_root.rglob("*")
        if path.is_dir()
        and (path.stat().st_dev, path.stat().st_ino) == owned_identity
    ]
    assert recovered_owned == [recovered]
    assert cleanup_error is None, str(cleanup_error)
