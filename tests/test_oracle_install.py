import json
import stat
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import pytest

import ssr_env.oracle_install as oracle_install
from ssr_env.oracle_install import (
    EXPECTED_ASSEMBLY_SHA256,
    MANIFEST_NAME,
    GameInstall,
    InstallError,
    deploy_plugin,
    inspect_archive,
    inspect_game,
    install_runtime,
    main,
    recover_install,
    status_install,
)

OFFICIAL_RUNTIME_ARCHIVE_SHA256 = (
    "01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323"
)


def make_fake_game(root: Path, assembly: bytes) -> Path:
    managed = root / "Sausage.app/Contents/Resources/Data/Managed"
    managed.mkdir(parents=True)
    (managed / "Assembly-CSharp.dll").write_bytes(assembly)
    (root / "Sausage.app/Contents/MacOS").mkdir(parents=True)
    (root / "Sausage.app/Contents/MacOS/Sausage").write_bytes(b"mach-o")
    return root


def make_runtime_archive(path: Path, script: str = 'executable_name=""\n') -> Path:
    with ZipFile(path, "w") as zf:
        zf.writestr(".doorstop_version", b"4.5.0")
        zf.writestr("changelog.txt", b"BepInEx 5.4.23.5")
        zf.writestr("BepInEx/", b"")
        zf.writestr("run_bepinex.sh", script)
        zf.writestr("libdoorstop.dylib", b"doorstop")
        zf.writestr("BepInEx/core/BepInEx.dll", b"core")
        zf.writestr("BepInEx/core/0Harmony.dll", b"harmony")
    return path


def pin_runtime_archive(
    monkeypatch: pytest.MonkeyPatch, archive: Path
) -> None:
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_RUNTIME_ARCHIVE_SHA256",
        sha256(archive.read_bytes()).hexdigest(),
        raising=False,
    )


def make_known_game(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    assembly = b"known"
    monkeypatch.setattr(
        "ssr_env.oracle_install.EXPECTED_ASSEMBLY_SHA256",
        sha256(assembly).hexdigest(),
    )
    game = make_fake_game(tmp_path / "game", assembly)
    archive = make_runtime_archive(tmp_path / "runtime.zip")
    pin_runtime_archive(monkeypatch, archive)
    return game, archive


def manifest_data(game: Path) -> dict[str, object]:
    return json.loads((game / MANIFEST_NAME).read_text())


def write_manifest(game: Path, data: dict[str, object]) -> None:
    (game / MANIFEST_NAME).write_text(json.dumps(data))


def test_inspect_game_identifies_the_expected_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    assembly = b"known"
    expected_hash = sha256(assembly).hexdigest()
    monkeypatch.setattr(
        "ssr_env.oracle_install.EXPECTED_ASSEMBLY_SHA256", expected_hash
    )
    game = make_fake_game(tmp_path / "game", assembly)

    inspected = inspect_game(game)

    assert inspected == GameInstall(
        root=game.resolve(),
        app=(game / "Sausage.app").resolve(),
        managed=(
            game / "Sausage.app/Contents/Resources/Data/Managed"
        ).resolve(),
        assembly=(
            game
            / "Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
        ).resolve(),
        assembly_sha256=expected_hash,
    )


def test_archive_rejects_parent_traversal(tmp_path: Path):
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("../outside", b"no")
    with pytest.raises(InstallError, match="unsafe archive member"):
        inspect_archive(archive)


def test_archive_rejects_absolute_paths(tmp_path: Path):
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("/tmp/outside", b"no")
    with pytest.raises(InstallError, match="unsafe archive member"):
        inspect_archive(archive)


def test_archive_rejects_symlinks(tmp_path: Path):
    archive = tmp_path / "bad.zip"
    link = ZipInfo("BepInEx/core/link")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with ZipFile(archive, "w") as zf:
        zf.writestr(link, "target")
    with pytest.raises(InstallError, match="symlink"):
        inspect_archive(archive)


def test_archive_rejects_unknown_top_level_paths(tmp_path: Path):
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("README.txt", b"surprise")
    with pytest.raises(InstallError, match="unknown top-level"):
        inspect_archive(archive)


def test_archive_accepts_the_exact_official_top_level_layout(tmp_path: Path):
    archive = make_runtime_archive(tmp_path / "official-shape.zip")

    members = inspect_archive(archive)

    assert {
        member.name.split("/", 1)[0]
        for member in members
    } == {
        ".doorstop_version",
        "BepInEx",
        "changelog.txt",
        "libdoorstop.dylib",
        "run_bepinex.sh",
    }
    doorstop_version = next(
        member for member in members if member.name == ".doorstop_version"
    )
    assert not doorstop_version.is_dir
    assert doorstop_version.size == len(b"4.5.0")


def test_archive_rejects_legacy_doorstop_config(tmp_path: Path):
    archive = tmp_path / "legacy.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("run_bepinex.sh", 'executable_name=""\n')
        zf.writestr("doorstop_config.ini", b"not in the official archive")
        zf.writestr("libdoorstop.dylib", b"doorstop")
        zf.writestr("BepInEx/core/BepInEx.dll", b"core")
        zf.writestr("BepInEx/core/0Harmony.dll", b"harmony")

    with pytest.raises(
        InstallError, match=r"unknown top-level.*doorstop_config\.ini"
    ):
        inspect_archive(archive)


def test_archive_rejects_children_under_a_top_level_file_root(tmp_path: Path):
    archive = make_runtime_archive(tmp_path / "bad.zip")
    with ZipFile(archive, "a") as zf:
        zf.writestr("changelog.txt/child", b"surprise")
    with pytest.raises(InstallError, match="top-level runtime file"):
        inspect_archive(archive)


@pytest.mark.parametrize(
    "missing",
    [
        "run_bepinex.sh",
        ".doorstop_version",
        "libdoorstop.dylib",
        "BepInEx/core/BepInEx.dll",
        "BepInEx/core/0Harmony.dll",
    ],
)
def test_archive_requires_bepinex_and_harmony(tmp_path: Path, missing: str):
    required = {
        "run_bepinex.sh": b'executable_name=""\n',
        ".doorstop_version": b"4.5.0",
        "libdoorstop.dylib": b"doorstop",
        "BepInEx/core/BepInEx.dll": b"core",
        "BepInEx/core/0Harmony.dll": b"harmony",
    }
    archive = tmp_path / "incomplete.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("BepInEx/", b"")
        zf.writestr("changelog.txt", b"BepInEx 5.4.23.5")
        for name, payload in required.items():
            if name != missing:
                zf.writestr(name, payload)
    with pytest.raises(InstallError, match="missing required archive member"):
        inspect_archive(archive)


def test_install_refuses_wrong_game_assembly(tmp_path: Path):
    game = make_fake_game(tmp_path / "game", b"wrong")
    archive = make_runtime_archive(tmp_path / "runtime.zip")
    with pytest.raises(InstallError, match=EXPECTED_ASSEMBLY_SHA256):
        install_runtime(game, archive)


def test_install_refuses_wrong_runtime_archive_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    assembly = b"known"
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_ASSEMBLY_SHA256",
        sha256(assembly).hexdigest(),
    )
    game = make_fake_game(tmp_path / "game", assembly)
    archive = make_runtime_archive(tmp_path / "not-official-bytes.zip")

    with pytest.raises(
        InstallError, match=OFFICIAL_RUNTIME_ARCHIVE_SHA256
    ):
        install_runtime(game, archive)

    assert not (game / "BepInEx").exists()
    assert not (game / MANIFEST_NAME).exists()


def test_install_refuses_existing_unmanaged_bepinex(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    unmanaged = game / "BepInEx"
    unmanaged.mkdir()
    (unmanaged / "user-file").write_text("keep")

    with pytest.raises(InstallError, match="unmanaged BepInEx"):
        install_runtime(game, archive)

    assert (unmanaged / "user-file").read_text() == "keep"


def test_install_refuses_an_existing_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    (game / MANIFEST_NAME).write_text("{}")
    with pytest.raises(InstallError, match="manifest already exists"):
        install_runtime(game, archive)


def test_install_rewrites_only_the_executable_name_assignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, _ = make_known_game(tmp_path, monkeypatch)
    script = (
        '# executable_name="" is documented here\r\n'
        'prefix=\'executable_name=""\'\r\n'
        'executable_name=""\r\n'
        'executable_name="already-set"\r\n'
    )
    archive = make_runtime_archive(tmp_path / "custom.zip", script)
    pin_runtime_archive(monkeypatch, archive)

    install_runtime(game, archive)

    installed = game / "run_bepinex.sh"
    assert installed.read_bytes() == (
        b'# executable_name="" is documented here\r\n'
        b'prefix=\'executable_name=""\'\r\n'
        b'executable_name="Sausage.app"\r\n'
        b'executable_name="already-set"\r\n'
    )
    assert stat.S_IMODE(installed.stat().st_mode) == 0o755


def test_install_manifest_records_archive_hash_and_created_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)

    manifest = install_runtime(game, archive)

    assert manifest.schema_version == 1
    assert manifest.runtime_archive_sha256 == sha256(
        archive.read_bytes()
    ).hexdigest()
    entries = {entry.relative_path: entry for entry in manifest.entries}
    assert entries["BepInEx"].kind == "directory"
    assert entries["BepInEx/core"].kind == "directory"
    assert entries["run_bepinex.sh"].sha256 == sha256(
        b'executable_name="Sausage.app"\n'
    ).hexdigest()
    assert entries["BepInEx/core/BepInEx.dll"].sha256 == sha256(
        b"core"
    ).hexdigest()
    assert entries[".doorstop_version"].sha256 == sha256(b"4.5.0").hexdigest()
    assert entries["changelog.txt"].sha256 == sha256(
        b"BepInEx 5.4.23.5"
    ).hexdigest()
    assert "doorstop_config.ini" not in entries
    assert not (game / "doorstop_config.ini").exists()
    encoded = (game / MANIFEST_NAME).read_text()
    assert encoded.endswith("\n")
    assert json.loads(encoded) == {
        "entries": [
            {
                "kind": entry.kind,
                "relative_path": entry.relative_path,
                "sha256": entry.sha256,
            }
            for entry in manifest.entries
        ],
        "game_assembly_sha256": manifest.game_assembly_sha256,
        "runtime_archive_sha256": manifest.runtime_archive_sha256,
        "schema_version": 1,
    }
    assert [entry.relative_path for entry in manifest.entries] == sorted(
        entry.relative_path for entry in manifest.entries
    )


def test_install_wraps_archive_extraction_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game, archive = make_known_game(tmp_path, monkeypatch)

    def fail_open(*args, **kwargs):
        raise RuntimeError("injected extraction failure")

    monkeypatch.setattr(ZipFile, "open", fail_open)

    with pytest.raises(InstallError, match="extract archive member"):
        install_runtime(game, archive)

    assert not (game / "BepInEx").exists()


def test_install_wraps_top_level_publication_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    original_replace = Path.replace

    def fail_runtime_move(path: Path, target: Path):
        if path.name == "BepInEx" and ".ssr-oracle-staging-" in str(path.parent):
            raise OSError("injected publication failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_runtime_move)

    with pytest.raises(InstallError, match="publish runtime root"):
        install_runtime(game, archive)

    assert not (game / "BepInEx").exists()


def test_install_wraps_manifest_tempfile_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    game, archive = make_known_game(tmp_path, monkeypatch)

    def fail_mkstemp(*args, **kwargs):
        raise OSError("injected temporary-file failure")

    monkeypatch.setattr(oracle_install.tempfile, "mkstemp", fail_mkstemp)

    with pytest.raises(InstallError, match="atomically write"):
        install_runtime(game, archive)

    assert not (game / "BepInEx").exists()


def test_deploy_refuses_a_non_dll_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "plugin.txt"
    plugin.write_text("not a DLL")

    with pytest.raises(InstallError, match=r"\.dll"):
        deploy_plugin(game, plugin, "enabled = true\n")


def test_deploy_requires_a_recognized_runtime_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, _ = make_known_game(tmp_path, monkeypatch)
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")

    with pytest.raises(InstallError, match="manifest"):
        deploy_plugin(game, plugin, "enabled = true\n")


def test_deploy_rejects_a_manifest_without_required_runtime_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    assembly_hash = sha256(b"known").hexdigest()
    write_manifest(
        game,
        {
            "schema_version": 1,
            "game_assembly_sha256": assembly_hash,
            "runtime_archive_sha256": sha256(archive.read_bytes()).hexdigest(),
            "entries": [],
        },
    )
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")

    with pytest.raises(InstallError, match="required runtime ownership"):
        deploy_plugin(game, plugin, "enabled = true\n")

    assert not (game / "BepInEx").exists()


def test_deploy_refuses_changed_required_runtime_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    (game / "BepInEx/core/BepInEx.dll").write_bytes(b"changed")
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")

    with pytest.raises(InstallError, match="runtime is not healthy"):
        deploy_plugin(game, plugin, "enabled = true\n")

    assert not (game / "BepInEx/plugins/SsrOracle.Plugin.dll").exists()


def test_deploy_wraps_plugin_read_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")
    original_read_bytes = Path.read_bytes

    def fail_plugin_read(path: Path):
        if path == plugin:
            raise OSError("injected plugin read failure")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_plugin_read)

    with pytest.raises(InstallError, match="cannot read plugin"):
        deploy_plugin(game, plugin, "enabled = true\n")


def test_deploy_uses_fixed_paths_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "Anything.DLL"
    plugin.write_bytes(b"plugin-v1")

    first = deploy_plugin(game, plugin, "enabled = true\n")
    plugin.write_bytes(b"plugin-v2")
    second = deploy_plugin(game, plugin, "enabled = false\n")

    plugin_target = game / "BepInEx/plugins/SsrOracle.Plugin.dll"
    config_target = game / "BepInEx/config/dev.jlsor.ssr.oracle.cfg"
    assert plugin_target.read_bytes() == b"plugin-v2"
    assert config_target.read_text() == "enabled = false\n"
    entries = {entry.relative_path: entry for entry in second.entries}
    assert entries["BepInEx/plugins"].kind == "directory"
    assert entries["BepInEx/config"].kind == "directory"
    assert entries["BepInEx/plugins/SsrOracle.Plugin.dll"].sha256 == sha256(
        b"plugin-v2"
    ).hexdigest()
    assert len(first.entries) == len(second.entries)


def test_deploy_rolls_back_when_the_second_payload_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    manifest_before = (game / MANIFEST_NAME).read_bytes()
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")
    original_atomic_write = oracle_install._atomic_write_bytes

    def fail_config(target: Path, payload: bytes, mode: int = 0o644):
        if target == game / "BepInEx/config/dev.jlsor.ssr.oracle.cfg":
            raise InstallError("injected config publication failure")
        return original_atomic_write(target, payload, mode)

    monkeypatch.setattr(oracle_install, "_atomic_write_bytes", fail_config)

    with pytest.raises(InstallError, match="config publication"):
        deploy_plugin(game, plugin, "enabled = true\n")

    assert (game / MANIFEST_NAME).read_bytes() == manifest_before
    assert not (game / "BepInEx/plugins/SsrOracle.Plugin.dll").exists()
    assert not (game / "BepInEx/config/dev.jlsor.ssr.oracle.cfg").exists()
    assert not (game / "BepInEx/plugins").exists()
    assert not (game / "BepInEx/config").exists()


def test_deploy_rolls_back_when_manifest_publication_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin-v1")
    deploy_plugin(game, plugin, "enabled = true\n")
    plugin_target = game / "BepInEx/plugins/SsrOracle.Plugin.dll"
    config_target = game / "BepInEx/config/dev.jlsor.ssr.oracle.cfg"
    plugin_target.chmod(0o600)
    config_target.chmod(0o640)
    manifest_before = (game / MANIFEST_NAME).read_bytes()
    plugin_before = plugin_target.read_bytes()
    config_before = config_target.read_bytes()
    modes_before = (
        stat.S_IMODE(plugin_target.stat().st_mode),
        stat.S_IMODE(config_target.stat().st_mode),
    )
    plugin.write_bytes(b"plugin-v2")
    original_atomic_write = oracle_install._atomic_write_bytes

    def fail_manifest(target: Path, payload: bytes, mode: int = 0o644):
        if target == game / MANIFEST_NAME:
            raise InstallError("injected manifest publication failure")
        return original_atomic_write(target, payload, mode)

    monkeypatch.setattr(oracle_install, "_atomic_write_bytes", fail_manifest)

    with pytest.raises(InstallError, match="manifest publication"):
        deploy_plugin(game, plugin, "enabled = false\n")

    assert (game / MANIFEST_NAME).read_bytes() == manifest_before
    assert plugin_target.read_bytes() == plugin_before
    assert config_target.read_bytes() == config_before
    assert (
        stat.S_IMODE(plugin_target.stat().st_mode),
        stat.S_IMODE(config_target.stat().st_mode),
    ) == modes_before


def test_deploy_cleans_staging_when_preserving_an_owned_target_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin-v1")
    deploy_plugin(game, plugin, "enabled = true\n")
    plugin_target = game / "BepInEx/plugins/SsrOracle.Plugin.dll"
    config_target = game / "BepInEx/config/dev.jlsor.ssr.oracle.cfg"
    manifest_before = (game / MANIFEST_NAME).read_bytes()
    plugin_before = plugin_target.read_bytes()
    config_before = config_target.read_bytes()
    original_read_bytes = Path.read_bytes

    def fail_owned_snapshot(path: Path):
        if path == plugin_target:
            raise OSError("injected snapshot failure")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_owned_snapshot)
    plugin.write_bytes(b"plugin-v2")

    with pytest.raises(InstallError, match="preserve existing file"):
        deploy_plugin(game, plugin, "enabled = false\n")

    assert original_read_bytes(game / MANIFEST_NAME) == manifest_before
    assert original_read_bytes(plugin_target) == plugin_before
    assert original_read_bytes(config_target) == config_before
    assert not tuple(game.glob(".ssr-oracle-deploy-staging-*"))


def test_deploy_refuses_an_owned_target_redirected_by_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin-v1")
    deploy_plugin(game, plugin, "enabled = true\n")
    plugin_target = game / "BepInEx/plugins/SsrOracle.Plugin.dll"
    plugin_target.unlink()
    user_file = game / "BepInEx/user-owned.dll"
    user_file.write_bytes(b"user")
    plugin_target.symlink_to(user_file)
    plugin.write_bytes(b"plugin-v2")

    with pytest.raises(InstallError, match="changed type"):
        deploy_plugin(game, plugin, "enabled = false\n")

    assert user_file.read_bytes() == b"user"


def test_deploy_refuses_a_runtime_root_with_the_wrong_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    shutil_target = game / "BepInEx"
    for child in sorted(shutil_target.rglob("*"), reverse=True):
        if child.is_dir():
            child.rmdir()
        else:
            child.unlink()
    shutil_target.rmdir()
    shutil_target.write_text("not a directory")
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")

    with pytest.raises(InstallError, match="runtime is not healthy"):
        deploy_plugin(game, plugin, "generated")


@pytest.mark.parametrize(
    "relative",
    [
        "BepInEx/plugins/SsrOracle.Plugin.dll",
        "BepInEx/config/dev.jlsor.ssr.oracle.cfg",
    ],
)
def test_deploy_refuses_an_existing_unmanaged_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, relative: str
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    target = game / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("user")
    plugin = tmp_path / "plugin.dll"
    plugin.write_bytes(b"plugin")

    with pytest.raises(InstallError, match="unmanaged deploy target"):
        deploy_plugin(game, plugin, "generated")

    assert target.read_text() == "user"


def test_status_detects_changed_manifest_owned_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    (game / "BepInEx/core/BepInEx.dll").write_bytes(b"tampered")

    status = status_install(game)

    assert not status.healthy
    assert status.missing == ()
    assert status.changed == ("BepInEx/core/BepInEx.dll",)


def test_status_detects_an_owned_file_redirected_by_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    owned = game / "BepInEx/core/BepInEx.dll"
    same_content = game / "BepInEx/core/user-copy.dll"
    same_content.write_bytes(owned.read_bytes())
    owned.unlink()
    owned.symlink_to(same_content)

    status = status_install(game)

    assert status.changed == ("BepInEx/core/BepInEx.dll",)


def test_status_detects_missing_files_and_wrong_directory_types(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    (game / "BepInEx/core/0Harmony.dll").unlink()
    (game / "BepInEx/core/BepInEx.dll").unlink()
    (game / "BepInEx/core").rmdir()
    (game / "BepInEx/core").write_text("not a directory")

    status = status_install(game)

    assert status.missing == (
        "BepInEx/core/0Harmony.dll",
        "BepInEx/core/BepInEx.dll",
    )
    assert status.changed == ("BepInEx/core",)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", 2, "schema"),
        ("entries", [], "duplicate"),
    ],
)
def test_status_rejects_unrecognized_or_duplicate_manifest_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    message: str,
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    data = manifest_data(game)
    if field == "entries":
        entries = data["entries"]
        assert isinstance(entries, list)
        data[field] = [entries[0], entries[0]]
    else:
        data[field] = value
    write_manifest(game, data)

    with pytest.raises(InstallError, match=message):
        status_install(game)


def test_status_rejects_malformed_file_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    data = manifest_data(game)
    entries = data["entries"]
    assert isinstance(entries, list)
    next(entry for entry in entries if entry["kind"] == "file")["sha256"] = "BAD"
    write_manifest(game, data)

    with pytest.raises(InstallError, match="sha256"):
        status_install(game)


@pytest.mark.parametrize(
    "entries",
    [
        [
            {
                "relative_path": "BepInEx/..",
                "kind": "directory",
                "sha256": None,
            },
        ],
        [
            {
                "relative_path": "BepInEx/..",
                "kind": "directory",
                "sha256": None,
            },
            {
                "relative_path": "BepInEx/../keep-me.txt",
                "kind": "file",
                "sha256": sha256(b"user").hexdigest(),
            },
        ],
    ],
)
def test_status_rejects_parent_components_even_when_they_resolve_inside_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entries: list[dict[str, object]],
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    (game / "keep-me.txt").write_bytes(b"user")
    data = manifest_data(game)
    raw_entries = data["entries"]
    assert isinstance(raw_entries, list)
    raw_entries.extend(entries)
    write_manifest(game, data)

    with pytest.raises(InstallError, match="parent traversal"):
        status_install(game)


def test_status_rejects_a_non_string_manifest_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    data = manifest_data(game)
    entries = data["entries"]
    assert isinstance(entries, list)
    entries[0]["kind"] = []
    write_manifest(game, data)

    with pytest.raises(InstallError, match="kind"):
        status_install(game)


def test_status_rejects_a_forged_legacy_doorstop_config_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    data = manifest_data(game)
    entries = data["entries"]
    assert isinstance(entries, list)
    doorstop_version = next(
        entry
        for entry in entries
        if entry["relative_path"] == ".doorstop_version"
    )
    doorstop_version["relative_path"] = "doorstop_config.ini"
    (game / ".doorstop_version").replace(game / "doorstop_config.ini")
    write_manifest(game, data)

    with pytest.raises(
        InstallError, match=r"doorstop_config\.ini"
    ):
        status_install(game)


def test_recover_moves_only_manifest_owned_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    unrelated = game / "keep-me.txt"
    unrelated.write_text("user")

    recovery = recover_install(game)

    assert unrelated.read_text() == "user"
    assert (recovery / "run_bepinex.sh").is_file()
    assert (recovery / MANIFEST_NAME).is_file()
    assert not (game / "BepInEx").exists()
    assert not (game / MANIFEST_NAME).exists()


def test_recover_refuses_manifest_paths_outside_game_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    data = manifest_data(game)
    entries = data["entries"]
    assert isinstance(entries, list)
    entries.append(
        {"relative_path": "../keep-me.txt", "kind": "file", "sha256": "0" * 64}
    )
    write_manifest(game, data)
    outside = game.parent / "keep-me.txt"
    outside.write_text("user")

    with pytest.raises(InstallError, match="parent traversal"):
        recover_install(game)

    assert outside.read_text() == "user"
    assert (game / "BepInEx").is_dir()


def test_recover_refuses_a_top_level_root_redirected_by_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    install_runtime(game, archive)
    redirected = game / "user-owned-runtime"
    (game / "BepInEx").replace(redirected)
    (game / "BepInEx").symlink_to(redirected, target_is_directory=True)

    with pytest.raises(InstallError, match="symlink"):
        recover_install(game)

    assert redirected.is_dir()
    assert (game / "BepInEx").is_symlink()
    assert not (game / ".ssr-oracle-recovery").exists()


def test_cli_status_prints_deterministic_json_and_returns_health_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    game, archive = make_known_game(tmp_path, monkeypatch)
    official_preloader = b"official preloader"
    with ZipFile(archive, "a") as zf:
        zf.writestr(
            "BepInEx/core/BepInEx.Preloader.dll", official_preloader
        )
    pin_runtime_archive(monkeypatch, archive)
    monkeypatch.setattr(
        oracle_install,
        "EXPECTED_OFFICIAL_PRELOADER_SHA256",
        sha256(official_preloader).hexdigest(),
    )
    install_runtime(game, archive)

    assert main(["status", "--game-root", str(game)]) == 0
    healthy = json.loads(capsys.readouterr().out)
    assert healthy == {
        "changed": [],
        "healthy": True,
        "manifest": {
            "entries": [
                {
                    "kind": entry.kind,
                    "relative_path": entry.relative_path,
                    "sha256": entry.sha256,
                }
                for entry in status_install(game).manifest.entries
            ],
            "game_assembly_sha256": status_install(
                game
            ).manifest.game_assembly_sha256,
            "runtime_archive_sha256": status_install(
                game
            ).manifest.runtime_archive_sha256,
            "schema_version": 1,
        },
        "missing": [],
        "preloader_compatibility": {
            "active_sha256": sha256(official_preloader).hexdigest(),
            "issues": [],
            "official_sha256": sha256(official_preloader).hexdigest(),
            "patched_sha256": None,
            "state": "official",
        },
    }

    (game / "run_bepinex.sh").write_text("changed")
    assert main(["status", "--game-root", str(game)]) == 1
    unhealthy = json.loads(capsys.readouterr().out)
    assert unhealthy["changed"] == ["run_bepinex.sh"]
    assert unhealthy["healthy"] is False
