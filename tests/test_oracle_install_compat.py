import errno
import json
import os
import stat
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
