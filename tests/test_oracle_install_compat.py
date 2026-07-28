import json
import os
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


def test_status_is_strictly_read_only(
    installed_patched_game: Path,
):
    before = _tree_snapshot(installed_patched_game)
    status_install(installed_patched_game, repo_root=Path("/unused"))
    assert _tree_snapshot(installed_patched_game) == before
