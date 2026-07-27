import json
import stat
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import pytest

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


def make_fake_game(root: Path, assembly: bytes) -> Path:
    managed = root / "Sausage.app/Contents/Resources/Data/Managed"
    managed.mkdir(parents=True)
    (managed / "Assembly-CSharp.dll").write_bytes(assembly)
    (root / "Sausage.app/Contents/MacOS").mkdir(parents=True)
    (root / "Sausage.app/Contents/MacOS/Sausage").write_bytes(b"mach-o")
    return root


def make_runtime_archive(path: Path, script: str = 'executable_name=""\n') -> Path:
    with ZipFile(path, "w") as zf:
        zf.writestr("run_bepinex.sh", script)
        zf.writestr("BepInEx/core/BepInEx.dll", b"core")
        zf.writestr("BepInEx/core/0Harmony.dll", b"harmony")
    return path


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


def test_archive_rejects_children_under_a_top_level_file_root(tmp_path: Path):
    archive = make_runtime_archive(tmp_path / "bad.zip")
    with ZipFile(archive, "a") as zf:
        zf.writestr("doorstop_config.ini/child", b"surprise")
    with pytest.raises(InstallError, match="top-level runtime file"):
        inspect_archive(archive)


@pytest.mark.parametrize(
    "missing",
    [
        "run_bepinex.sh",
        "BepInEx/core/BepInEx.dll",
        "BepInEx/core/0Harmony.dll",
    ],
)
def test_archive_requires_bepinex_and_harmony(tmp_path: Path, missing: str):
    required = {
        "run_bepinex.sh": b'executable_name=""\n',
        "BepInEx/core/BepInEx.dll": b"core",
        "BepInEx/core/0Harmony.dll": b"harmony",
    }
    archive = tmp_path / "incomplete.zip"
    with ZipFile(archive, "w") as zf:
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

    with pytest.raises(InstallError, match="deploy parent"):
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

    with pytest.raises(InstallError, match="path escapes game root"):
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
    }

    (game / "run_bepinex.sh").write_text("changed")
    assert main(["status", "--game-root", str(game)]) == 1
    unhealthy = json.loads(capsys.readouterr().out)
    assert unhealthy["changed"] == ["run_bepinex.sh"]
    assert unhealthy["healthy"] is False
