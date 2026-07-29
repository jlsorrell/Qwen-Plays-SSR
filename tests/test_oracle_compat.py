from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import pytest

import ssr_env.oracle_compat as oracle_compat
from ssr_env.oracle_compat import (
    AssemblyMetadata,
    BuildProvenance,
    BuildResult,
    CompatError,
    SourceCheckout,
    build_compat_preloader,
    canonical_json,
    inspect_assembly,
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

LEGACY_REFERENCES = (
    ("0Harmony", "2.9.0.0"),
    ("BepInEx", "5.4.23.5"),
    ("HarmonyXInterop", "1.0.0.0"),
    ("Mono.Cecil", "0.10.4.0"),
    ("MonoMod.RuntimeDetour", "22.1.29.1"),
    ("MonoMod.Utils", "22.1.29.1"),
    ("System", "2.0.0.0"),
    ("System.Core", "3.5.0.0"),
    ("mscorlib", "2.0.0.0"),
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


@pytest.fixture(scope="module")
def built_inspector(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = Path(__file__).resolve().parents[1]
    sdk = root / "data/oracle/compat/dotnet-8.0.419/dotnet"
    project = root / "oracle/compat/inspector/SsrOracle.CompatInspector.csproj"
    build_root = tmp_path_factory.mktemp("inspector")
    output = build_root / "publish"
    environment = os.environ.copy()
    environment["DOTNET_CLI_HOME"] = str(build_root / "dotnet-home")
    environment["NUGET_PACKAGES"] = str(build_root / "packages")
    environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    result = subprocess.run(
        [
            str(sdk),
            "publish",
            str(project),
            "--configuration",
            "Release",
            "--output",
            str(output),
            "--disable-build-servers",
            f"-p:BaseIntermediateOutputPath={build_root / 'obj'}/",
            f"-p:MSBuildProjectExtensionsPath={build_root / 'obj'}/",
            f"-p:BaseOutputPath={build_root / 'bin'}/",
        ],
        text=True,
        capture_output=True,
        timeout=300,
        env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return output / "SsrOracle.CompatInspector"


@pytest.fixture(scope="module")
def switch_il_mutator(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = Path(__file__).resolve().parents[1]
    sdk = root / "data/oracle/compat/dotnet-8.0.419/dotnet"
    project_root = tmp_path_factory.mktemp("switch-mutator")
    (project_root / "SwitchMutator.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>
"""
    )
    (project_root / "Program.cs").write_text(
        """using System.Buffers.Binary;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;

byte[] data = File.ReadAllBytes(args[0]);
using PEReader pe = new(new MemoryStream(data));
MetadataReader metadata = pe.GetMetadataReader();
MethodDefinition? match = null;
foreach (TypeDefinitionHandle typeHandle in metadata.TypeDefinitions)
{
    TypeDefinition type = metadata.GetTypeDefinition(typeHandle);
    if (metadata.GetString(type.Name) != "PlatformUtils"
        || metadata.GetString(type.Namespace) != "BepInEx.Preloader")
    {
        continue;
    }
    foreach (MethodDefinitionHandle methodHandle in type.GetMethods())
    {
        MethodDefinition method = metadata.GetMethodDefinition(methodHandle);
        if (metadata.GetString(method.Name) == "SetPlatform")
        {
            match = method;
        }
    }
}
MethodDefinition target = match
    ?? throw new InvalidOperationException("method missing");
byte[] il = pe.GetMethodBody(target.RelativeVirtualAddress).GetILBytes().ToArray();
int switchOffset = -1;
for (int index = 0; index <= il.Length - 5; index++)
{
    int count = BinaryPrimitives.ReadInt32LittleEndian(il.AsSpan(index + 1, 4));
    if (il[index] == 0x45
        && count > 0
        && count <= (il.Length - index - 5) / 4)
    {
        if (switchOffset != -1)
        {
            throw new InvalidOperationException("duplicate switch");
        }
        switchOffset = index;
    }
}
if (switchOffset == -1)
{
    throw new InvalidOperationException("switch missing");
}
SectionHeader section = pe.PEHeaders.SectionHeaders.Single(
    candidate => target.RelativeVirtualAddress >= candidate.VirtualAddress
        && target.RelativeVirtualAddress
            < candidate.VirtualAddress
                + Math.Max(candidate.VirtualSize, candidate.SizeOfRawData));
int bodyOffset = section.PointerToRawData
    + target.RelativeVirtualAddress
    - section.VirtualAddress;
int headerSize;
if ((data[bodyOffset] & 3) == 2)
{
    headerSize = 1;
}
else
{
    ushort flagsAndSize = BinaryPrimitives.ReadUInt16LittleEndian(
        data.AsSpan(bodyOffset, 2));
    headerSize = ((flagsAndSize >> 12) & 0xF) * 4;
}
BinaryPrimitives.WriteInt32LittleEndian(
    data.AsSpan(bodyOffset + headerSize + switchOffset + 1, 4),
    int.Parse(args[2]));
File.WriteAllBytes(args[1], data);
"""
    )
    output = project_root / "publish"
    environment = os.environ.copy()
    environment["DOTNET_CLI_HOME"] = str(project_root / "dotnet-home")
    environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    result = subprocess.run(
        [
            str(sdk),
            "publish",
            str(project_root / "SwitchMutator.csproj"),
            "--configuration",
            "Release",
            "--output",
            str(output),
            "--disable-build-servers",
        ],
        text=True,
        capture_output=True,
        timeout=300,
        env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return output / "SwitchMutator"


@pytest.fixture(scope="module")
def synthetic_net35_preloader(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    root = Path(__file__).resolve().parents[1]
    sdk = root / "data/oracle/compat/dotnet-8.0.419/dotnet"
    feed = root / "data/oracle/compat/fetch-acceptance"
    project_root = tmp_path_factory.mktemp("official-preloader")
    (project_root / "NuGet.config").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<configuration><packageSources><clear />"
        f'<add key="local" value="{feed}" />'
        "</packageSources></configuration>\n"
    )
    (project_root / "Official.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <AssemblyName>BepInEx.Preloader</AssemblyName>
    <AssemblyVersion>5.4.23.5</AssemblyVersion>
    <TargetFramework>net35</TargetFramework>
  </PropertyGroup>
</Project>
"""
    )
    (project_root / "Marker.cs").write_text(
        """namespace BepInEx.Preloader
{
    public static class PlatformUtils
    {
        public static int SetPlatform(int value)
        {
            switch (value)
            {
                case 0:
                    return "/System/Library/CoreServices".Length;
                case 1:
                    return 11;
                case 2:
                    return 12;
                case 3:
                    return 13;
                case 4:
                    return 14;
                default:
                    return System.Linq.Enumerable.Count(
                        System.Linq.Enumerable.Empty<int>());
            }
        }
    }
}
"""
    )
    environment = os.environ.copy()
    environment["DOTNET_CLI_HOME"] = str(project_root / "dotnet-home")
    environment["NUGET_PACKAGES"] = str(project_root / "packages")
    environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    result = subprocess.run(
        [
            str(sdk),
            "build",
            str(project_root / "Official.csproj"),
            "--configuration",
            "Release",
            "--configfile",
            str(project_root / "NuGet.config"),
            "--disable-build-servers",
        ],
        text=True,
        capture_output=True,
        timeout=300,
        env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return project_root / "bin/Release/net35/BepInEx.Preloader.dll"


@pytest.fixture(scope="module")
def official_preloader() -> Path:
    path = Path(
        "/Users/jlsor/Library/Application Support/Steam/steamapps/common/"
        "Stephen's Sausage Roll/BepInEx/core/BepInEx.Preloader.dll"
    )
    if not path.is_file():
        pytest.skip("canonical installed official preloader is absent")
    expected = "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627"
    if _sha256(path.read_bytes()) != expected:
        pytest.skip("canonical installed official preloader hash is not exact")
    return path


@pytest.fixture(scope="module")
def patched_preloader() -> Path:
    root = Path(__file__).resolve().parents[1] / "data/oracle/compat/builds"
    current = root / "current.json"
    if not current.is_file():
        pytest.skip("real patched compatibility build is absent")
    decoded = json.loads(current.read_bytes())
    path = root / decoded["dll"]
    if not path.is_file():
        pytest.skip("real patched preloader is absent")
    return path


@pytest.fixture(scope="module")
def net35_without_system_core(
    tmp_path_factory: pytest.TempPathFactory,
) -> Path:
    root = Path(__file__).resolve().parents[1]
    sdk = root / "data/oracle/compat/dotnet-8.0.419/dotnet"
    feed = root / "data/oracle/compat/fetch-acceptance"
    project_root = tmp_path_factory.mktemp("net35-without-system-core")
    (project_root / "NuGet.config").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<configuration><packageSources><clear />"
        f'<add key="local" value="{feed}" />'
        "</packageSources></configuration>\n"
    )
    (project_root / "Missing.csproj").write_text(
        """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net35</TargetFramework>
  </PropertyGroup>
</Project>
"""
    )
    (project_root / "Marker.cs").write_text(
        "public sealed class Marker { public static int Value() { return 1; } }\n"
    )
    environment = os.environ.copy()
    environment["DOTNET_CLI_HOME"] = str(project_root / "dotnet-home")
    environment["NUGET_PACKAGES"] = str(project_root / "packages")
    environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    result = subprocess.run(
        [
            str(sdk),
            "build",
            str(project_root / "Missing.csproj"),
            "--configuration",
            "Release",
            "--configfile",
            str(project_root / "NuGet.config"),
            "--disable-build-servers",
        ],
        text=True,
        capture_output=True,
        timeout=300,
        env=environment,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return project_root / "bin/Release/net35/Missing.dll"


def _legacy_metadata() -> AssemblyMetadata:
    return AssemblyMetadata(
        name="BepInEx.Preloader",
        version="5.4.23.5",
        metadata_version="v2.0.50727",
        target_framework=".NETFramework,Version=v3.5",
        references=LEGACY_REFERENCES,
    )


def _fake_build_process(
    monkeypatch,
    outputs: list[bytes | BaseException],
    *,
    authenticate_sdk: bool = True,
    pin_output: bool = True,
):
    state = {"publish": 0, "commands": [], "inspections": []}
    if pin_output and outputs and isinstance(outputs[0], bytes):
        monkeypatch.setattr(
            oracle_compat,
            "EXPECTED_PATCHED_PRELOADER_SHA256",
            _sha256(outputs[0]),
        )

    def execute(command, *, cwd, env):
        state["commands"].append(command)
        if command[-1:] == ["--version"]:
            return subprocess.CompletedProcess(command, 0, "8.0.419\n", "")
        if "publish" in command and any(
            item.endswith("BepInEx.Preloader.csproj") for item in command
        ):
            item = outputs[state["publish"]]
            state["publish"] += 1
            if isinstance(item, BaseException):
                raise item
            output = Path(command[command.index("--output") + 1])
            output.mkdir(parents=True, exist_ok=True)
            (output / "BepInEx.Preloader.dll").write_bytes(item)
        return subprocess.CompletedProcess(command, 0, "ok\n", "")

    monkeypatch.setattr(
        "ssr_env.oracle_compat._execute_build_command",
        execute,
    )
    def inspect(path, inspector, **kwargs):
        state["inspections"].append(kwargs.get("verified_dotnet"))
        return _legacy_metadata()

    monkeypatch.setattr("ssr_env.oracle_compat.inspect_assembly", inspect)
    if authenticate_sdk:
        def fake_authenticate_sdk(supplied_sdk, repo_root, toolchain, work):
            executable = work / "verified-sdk/dotnet"
            executable.parent.mkdir()
            executable.write_bytes(b"fake authenticated SDK")
            executable.chmod(0o755)
            return executable

        monkeypatch.setattr(
            "ssr_env.oracle_compat._authenticate_sdk",
            fake_authenticate_sdk,
        )
    return state


def test_build_timeout_terminates_descendant_processes(
    monkeypatch,
    tmp_path: Path,
):
    survivor = tmp_path / "descendant-survived"
    child = (
        "import pathlib,time;"
        "time.sleep(0.8);"
        f"pathlib.Path({str(survivor)!r}).write_text('survived')"
    )
    parent = (
        "import subprocess,sys,time;"
        f"subprocess.Popen([sys.executable, '-c', {child!r}]);"
        "print('child started', flush=True);"
        "time.sleep(10)"
    )
    monkeypatch.setattr(oracle_compat, "_BUILD_TIMEOUT_SECONDS", 0.1)

    with pytest.raises(CompatError, match="timed out"):
        oracle_compat._run_build_command(
            [sys.executable, "-c", parent],
            cwd=tmp_path,
            env=os.environ.copy(),
            log_path=tmp_path / "timeout.log",
        )

    time.sleep(1)
    assert not survivor.exists()
    assert "child started" in (tmp_path / "timeout.log").read_text()


def _build_with_fake_process(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
    outputs: list[bytes | BaseException],
    *,
    pin_output: bool = True,
):
    root = Path(__file__).resolve().parents[1]
    _fake_build_process(monkeypatch, outputs, pin_output=pin_output)
    return build_compat_preloader(
        source=pinned_recursive_checkout,
        sdk=root / "data/oracle/compat/dotnet-8.0.419/dotnet",
        feed_dir=root / "data/oracle/compat/fetch-acceptance",
        output_dir=tmp_path / "builds",
        repo_root=root,
    )


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
        "build_target": (
            "BepInEx.Preloader/BepInEx.Preloader.csproj@framework=net35"
        ),
        "official_preloader_sha256": (
            "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627"
        ),
        "patched_preloader_sha256": (
            "5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816"
        ),
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


def test_load_provenance_requires_framework_bearing_build_target(
    committed_compat_repo: Path,
    valid_provenance: Path,
):
    trust = load_trust(committed_compat_repo)
    decoded = json.loads(valid_provenance.read_text())
    decoded["build_target"] = "BepInEx.Preloader/BepInEx.Preloader.csproj"
    valid_provenance.write_bytes(canonical_json(decoded))
    with pytest.raises(CompatError, match="build target"):
        load_provenance(valid_provenance, trust)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_commit", "6" * 40, "source commit"),
        ("dotnet_sdk_version", "8.0.420", "SDK version"),
        ("official_preloader_sha256", "7" * 64, "official preloader"),
        ("patched_preloader_sha256", "8" * 64, "patched preloader"),
        (
            "build_target",
            "BepInEx.Preloader/BepInEx.Preloader.csproj@framework=net40",
            "build target",
        ),
    ],
)
def test_load_provenance_requires_all_pinned_identity_fields(
    committed_compat_repo: Path,
    valid_provenance: Path,
    field: str,
    value: str,
    message: str,
):
    trust = load_trust(committed_compat_repo)
    decoded = json.loads(valid_provenance.read_text())
    decoded[field] = value
    valid_provenance.write_bytes(canonical_json(decoded))
    with pytest.raises(CompatError, match=message):
        load_provenance(valid_provenance, trust)


def test_reviewed_patched_preloader_hash_is_exported_and_exact():
    assert oracle_compat.EXPECTED_PATCHED_PRELOADER_SHA256 == (
        "5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816"
    )


def test_real_committed_trust_accepts_reviewed_canonical_provenance(
    tmp_path: Path,
):
    root = Path(__file__).resolve().parents[1]
    trust = load_trust(root)
    path = tmp_path / "reviewed-provenance.json"
    path.write_bytes(
        canonical_json(
            {
                "schema_version": 1,
                "source_commit": (
                    "57f1fb859bd4d0264cd2a59074d0e96c6a492a33"
                ),
                "patch_sha256": trust.patch_sha256,
                "toolchain_lock_sha256": trust.toolchain_sha256,
                "dotnet_sdk_version": "8.0.419",
                "dependency_lock_sha256": trust.dependencies_sha256,
                "build_target": (
                    "BepInEx.Preloader/BepInEx.Preloader.csproj"
                    "@framework=net35"
                ),
                "official_preloader_sha256": (
                    "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627"
                ),
                "patched_preloader_sha256": (
                    "5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816"
                ),
            }
        )
    )

    provenance = load_provenance(path, trust)

    assert provenance.patched_preloader_sha256 == (
        oracle_compat.EXPECTED_PATCHED_PRELOADER_SHA256
    )


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


def test_validate_source_checkout_rejects_decorated_submodule_status(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
):
    harmony = recursive_source_checkout / "submodules/BepInEx.Harmony"
    subprocess.run(["git", "checkout", "-qb", "local"], cwd=harmony, check=True)
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


def test_prepare_source_revalidates_non_target_tracked_file(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    (recursive_source_checkout / "README.md").write_text("changed after validation\n")
    with pytest.raises(CompatError, match="clean checkout"):
        prepare_source(source, tmp_path / "prepared", trust)


def test_prepare_source_rejects_out_of_hunk_platform_mutation_after_validation(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    platform = recursive_source_checkout / "BepInEx.Preloader/Platform.cs"
    with platform.open("a", encoding="utf-8") as output:
        output.write("\n// mutation after validation\n")
    with pytest.raises(CompatError, match="clean checkout"):
        prepare_source(source, tmp_path / "prepared", trust)
    assert not (tmp_path / "prepared").exists()


def test_prepare_source_rejects_forged_checkout_identity(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    forged = SourceCheckout(
        root=recursive_source_checkout.resolve(),
        source_commit="0" * 40,
        harmony_submodule_commit="1" * 40,
    )
    with pytest.raises(CompatError, match="source commit"):
        prepare_source(forged, tmp_path / "prepared", trust)


def test_prepare_source_revalidates_submodule_after_validation(
    recursive_source_checkout: Path,
    committed_compat_repo: Path,
    tmp_path: Path,
):
    trust = load_trust(committed_compat_repo)
    source = validate_source_checkout(recursive_source_checkout, trust)
    harmony = recursive_source_checkout / "submodules/BepInEx.Harmony"
    subprocess.run(["git", "checkout", "-q", "HEAD^"], cwd=harmony, check=True)
    with pytest.raises(CompatError, match="submodule commit"):
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


def test_inspector_reports_identity_version_clr_and_references(
    official_preloader: Path,
    built_inspector: Path,
):
    metadata = inspect_assembly(official_preloader, built_inspector)
    assert metadata.name == "BepInEx.Preloader"
    assert metadata.version == "5.4.23.5"
    assert metadata.target_framework == ".NETFramework,Version=v3.5"
    assert metadata.metadata_version == "v2.0.50727"
    assert metadata.references == LEGACY_REFERENCES


def test_inspector_uses_explicit_verified_dotnet_runtime(
    monkeypatch,
    tmp_path: Path,
):
    assembly = tmp_path / "assembly.dll"
    assembly.write_bytes(b"managed fixture")
    verified_root = tmp_path / "verified-sdk"
    verified_root.mkdir()
    dotnet = verified_root / "dotnet"
    dotnet.write_bytes(b"verified host")
    dotnet.chmod(0o755)
    inspector = tmp_path / "inspector/SsrOracle.CompatInspector"
    inspector.parent.mkdir()
    inspector.write_bytes(b"apphost")
    inspector.chmod(0o755)
    inspector_dll = inspector.parent / f"{inspector.name}.dll"
    inspector_dll.write_bytes(b"inspector assembly")
    observed = {}
    repository_runtime = (
        Path(__file__).resolve().parents[1]
        / "data/oracle/compat/dotnet-8.0.419"
    )
    monkeypatch.setenv("DOTNET_ROOT_ARM64", str(repository_runtime))
    monkeypatch.setenv("DOTNET_ROOT_X64", str(repository_runtime))

    def run(command, **kwargs):
        observed["command"] = command
        observed["environment"] = kwargs["env"]
        return subprocess.CompletedProcess(
            command,
            0,
            canonical_json(
                {
                    "assembly_name": "BepInEx.Preloader",
                    "assembly_version": "5.4.23.5",
                    "metadata_version": "v2.0.50727",
                    "references": dict(LEGACY_REFERENCES),
                    "target_framework": ".NETFramework,Version=v3.5",
                }
            ),
            b"",
        )

    monkeypatch.setattr(oracle_compat.subprocess, "run", run)
    inspect_assembly(
        assembly,
        inspector,
        require_platform_patch=True,
        verified_dotnet=dotnet,
    )

    assert observed["command"] == [
        str(dotnet),
        str(inspector_dll),
        "--require-platform-patch",
        str(assembly),
    ]
    assert observed["environment"]["DOTNET_ROOT"] == str(verified_root)
    assert "DOTNET_ROOT_ARM64" not in observed["environment"]
    assert "DOTNET_ROOT_X64" not in observed["environment"]
    assert observed["environment"]["DOTNET_MULTILEVEL_LOOKUP"] == "0"
    assert str(repository_runtime) not in observed["command"]
    assert observed["environment"]["DOTNET_ROOT"] != str(repository_runtime)


def test_inspector_rejects_missing_net35_reference_signal(
    net35_without_system_core: Path,
    built_inspector: Path,
):
    with pytest.raises(CompatError, match="metadata is invalid"):
        inspect_assembly(net35_without_system_core, built_inspector)


def test_inspector_rejects_nonexact_clr_metadata_signal(
    synthetic_net35_preloader: Path,
    built_inspector: Path,
    tmp_path: Path,
):
    data = synthetic_net35_preloader.read_bytes()
    assert data.count(b"v2.0.50727") == 1
    changed = tmp_path / "wrong-clr.dll"
    changed.write_bytes(data.replace(b"v2.0.50727", b"v2.0.50728"))
    with pytest.raises(CompatError, match="metadata is invalid"):
        inspect_assembly(changed, built_inspector)


def test_inspector_rejects_managed_native_header(
    synthetic_net35_preloader: Path,
    built_inspector: Path,
    tmp_path: Path,
):
    data = bytearray(synthetic_net35_preloader.read_bytes())
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    coff = pe_offset + 4
    section_count = struct.unpack_from("<H", data, coff + 2)[0]
    optional_size = struct.unpack_from("<H", data, coff + 16)[0]
    optional = coff + 20
    magic = struct.unpack_from("<H", data, optional)[0]
    directory_base = optional + (96 if magic == 0x10B else 112)
    cli_rva = struct.unpack_from("<I", data, directory_base + 14 * 8)[0]
    section_table = optional + optional_size
    cli_offset = None
    for index in range(section_count):
        section = section_table + index * 40
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from(
            "<IIII",
            data,
            section + 8,
        )
        if virtual_address <= cli_rva < virtual_address + max(
            virtual_size,
            raw_size,
        ):
            cli_offset = raw_offset + cli_rva - virtual_address
            break
    assert cli_offset is not None
    struct.pack_into("<II", data, cli_offset + 64, cli_rva, 1)
    changed = tmp_path / "managed-native.dll"
    changed.write_bytes(data)

    with pytest.raises(CompatError, match="metadata is invalid"):
        inspect_assembly(changed, built_inspector)


@pytest.mark.parametrize("switch_count", [-1, 0x7FFFFFFF])
def test_inspector_reports_malformed_switch_il_as_invalid_assembly(
    synthetic_net35_preloader: Path,
    built_inspector: Path,
    switch_il_mutator: Path,
    tmp_path: Path,
    switch_count: int,
):
    changed = tmp_path / f"malformed-switch-{switch_count}.dll"
    environment = os.environ.copy()
    environment["DOTNET_ROOT"] = str(
        Path(__file__).resolve().parents[1]
        / "data/oracle/compat/dotnet-8.0.419"
    )
    mutation = subprocess.run(
        [
            str(switch_il_mutator),
            str(synthetic_net35_preloader),
            str(changed),
            str(switch_count),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        timeout=30,
    )
    assert mutation.returncode == 0, mutation.stderr

    result = subprocess.run(
        [
            str(built_inspector),
            "--require-platform-patch",
            str(changed),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        timeout=30,
    )

    assert result.returncode == 2
    assert b"invalid managed assembly" in result.stderr
    assert b"invalid switch operand" in result.stderr


def test_inspector_requires_compiled_platform_patch(
    patched_preloader: Path,
    built_inspector: Path,
):
    metadata = inspect_assembly(
        patched_preloader,
        built_inspector,
        require_platform_patch=True,
    )
    assert metadata.name == "BepInEx.Preloader"


def test_inspector_rejects_real_official_as_patched(
    official_preloader: Path,
    built_inspector: Path,
):
    with pytest.raises(CompatError, match="metadata is invalid"):
        inspect_assembly(
            official_preloader,
            built_inspector,
            require_platform_patch=True,
        )


def test_build_rejects_nonidentical_second_output(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    with pytest.raises(CompatError, match="byte-identical"):
        _build_with_fake_process(
            monkeypatch,
            pinned_recursive_checkout,
            tmp_path,
            [b"first", b"second"],
        )
    assert not (tmp_path / "builds/current.json").exists()


def test_build_rejects_output_equal_to_locked_official(
    monkeypatch,
    pinned_recursive_checkout: Path,
    official_preloader: Path,
    tmp_path: Path,
):
    official_bytes = official_preloader.read_bytes()
    with pytest.raises(CompatError, match="official preloader"):
        _build_with_fake_process(
            monkeypatch,
            pinned_recursive_checkout,
            tmp_path,
            [official_bytes, official_bytes],
        )
    assert not (tmp_path / "builds/current.json").exists()


def test_build_rejects_output_not_equal_to_reviewed_patched_hash(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    arbitrary = b"not the reviewed managed assembly"
    with pytest.raises(CompatError, match="reviewed preloader hash"):
        _build_with_fake_process(
            monkeypatch,
            pinned_recursive_checkout,
            tmp_path,
            [arbitrary, arbitrary],
            pin_output=False,
        )
    assert not (tmp_path / "builds/current.json").exists()


def test_build_rejects_symlinked_sdk_path(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    root = Path(__file__).resolve().parents[1]
    sdk_link = tmp_path / "dotnet-link"
    sdk_link.symlink_to(root / "data/oracle/compat/dotnet-8.0.419/dotnet")
    _fake_build_process(
        monkeypatch,
        [b"same", b"same"],
        authenticate_sdk=False,
    )
    with pytest.raises(CompatError, match="SDK"):
        build_compat_preloader(
            source=pinned_recursive_checkout,
            sdk=sdk_link,
            feed_dir=root / "data/oracle/compat/fetch-acceptance",
            output_dir=tmp_path / "builds",
            repo_root=root,
        )


def test_build_rejects_changed_sdk_archive(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    root = Path(__file__).resolve().parents[1]
    changed_archive = tmp_path / "changed-sdk.tar.gz"
    changed_archive.write_bytes(b"not the authenticated SDK archive")
    monkeypatch.setattr(
        "ssr_env.oracle_compat._sdk_archive_path",
        lambda repo_root: changed_archive,
        raising=False,
    )
    _fake_build_process(
        monkeypatch,
        [b"same", b"same"],
        authenticate_sdk=False,
    )
    with pytest.raises(CompatError, match="SDK archive"):
        build_compat_preloader(
            source=pinned_recursive_checkout,
            sdk=root / "data/oracle/compat/dotnet-8.0.419/dotnet",
            feed_dir=root / "data/oracle/compat/fetch-acceptance",
            output_dir=tmp_path / "builds",
            repo_root=root,
        )


def test_build_executes_sdk_from_fresh_verified_extraction(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    root = Path(__file__).resolve().parents[1]
    state = _fake_build_process(
        monkeypatch,
        [b"same", b"same"],
        authenticate_sdk=False,
    )
    build_compat_preloader(
        source=pinned_recursive_checkout,
        sdk=root / "data/oracle/compat/dotnet-8.0.419/dotnet",
        feed_dir=root / "data/oracle/compat/fetch-acceptance",
        output_dir=tmp_path / "builds",
        repo_root=root,
    )
    executables = {Path(command[0]) for command in state["commands"]}
    assert len(executables) == 1
    extracted = executables.pop()
    assert extracted.name == "dotnet"
    assert extracted.parent.name == "verified-sdk"
    assert extracted != root / "data/oracle/compat/dotnet-8.0.419/dotnet"
    assert state["inspections"] == [extracted]


@pytest.mark.parametrize(
    "change",
    [
        {"metadata_version": "v2.0.50728"},
        {"target_framework": ".NETFramework,Version=v3.0"},
    ],
)
def test_build_rejects_wrong_metadata(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
    change,
):
    _fake_build_process(monkeypatch, [b"same", b"same"])
    monkeypatch.setattr(
        "ssr_env.oracle_compat.inspect_assembly",
        lambda path, inspector, **kwargs: replace(_legacy_metadata(), **change),
    )
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(CompatError, match="legacy metadata"):
        build_compat_preloader(
            source=pinned_recursive_checkout,
            sdk=root / "data/oracle/compat/dotnet-8.0.419/dotnet",
            feed_dir=root / "data/oracle/compat/fetch-acceptance",
            output_dir=tmp_path / "builds",
            repo_root=root,
        )
    assert not (tmp_path / "builds/current.json").exists()


@pytest.mark.parametrize(
    "references",
    [
        LEGACY_REFERENCES[:-1],
        (*LEGACY_REFERENCES, ("Unexpected", "1.0.0.0")),
        tuple(
            (name, "2.0.0.1" if name == "mscorlib" else version)
            for name, version in LEGACY_REFERENCES
        ),
    ],
)
def test_build_rejects_nonexact_legacy_reference_map(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
    references,
):
    _fake_build_process(monkeypatch, [b"same", b"same"])
    monkeypatch.setattr(
        "ssr_env.oracle_compat.inspect_assembly",
        lambda path, inspector, **kwargs: replace(
            _legacy_metadata(),
            references=references,
        ),
    )
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(CompatError, match="exact legacy metadata"):
        build_compat_preloader(
            source=pinned_recursive_checkout,
            sdk=root / "data/oracle/compat/dotnet-8.0.419/dotnet",
            feed_dir=root / "data/oracle/compat/fetch-acceptance",
            output_dir=tmp_path / "builds",
            repo_root=root,
        )


def test_build_timeout_preserves_log(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    timeout = subprocess.TimeoutExpired(
        cmd=["dotnet", "publish"],
        timeout=300,
        output=b"restore completed\npublish still running\n",
        stderr=b"last diagnostic\n",
    )
    with pytest.raises(CompatError, match="BepInEx build timed out"):
        _build_with_fake_process(
            monkeypatch,
            pinned_recursive_checkout,
            tmp_path,
            [timeout],
        )
    logs = list((tmp_path / "builds/.work").rglob("*.log"))
    assert logs
    assert b"publish still running" in b"".join(path.read_bytes() for path in logs)
    assert b"last diagnostic" in b"".join(path.read_bytes() for path in logs)
    assert not (tmp_path / "builds/current.json").exists()


def test_build_publishes_only_after_all_checks(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    result = _build_with_fake_process(
        monkeypatch,
        pinned_recursive_checkout,
        tmp_path,
        [b"same deterministic preloader", b"same deterministic preloader"],
    )
    assert result.dll.parent.name == result.patched_sha256
    assert result.dll.read_bytes() == b"same deterministic preloader"
    assert result.provenance.read_bytes() == canonical_json(
        asdict(result.provenance_data)
    )
    current = json.loads((tmp_path / "builds/current.json").read_bytes())
    assert current == {
        "dll": f"{result.patched_sha256}/BepInEx.Preloader.dll",
        "patched_sha256": result.patched_sha256,
        "provenance": f"{result.patched_sha256}/provenance.json",
    }


@pytest.mark.parametrize(
    "position",
    [
        "output-root",
        "output-parent",
        "work",
        "digest-directory",
        "dll",
        "provenance",
        "current",
        "extra-entry",
    ],
)
def test_build_rejects_unsafe_publication_paths(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
    position: str,
):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "builds"
    sdk = root / "data/oracle/compat/dotnet-8.0.419/dotnet"
    feed = root / "data/oracle/compat/fetch-acceptance"

    if position == "output-root":
        external = tmp_path / "external-output"
        external.mkdir()
        output.symlink_to(external, target_is_directory=True)
    elif position == "output-parent":
        external = tmp_path / "external-parent"
        external.mkdir()
        linked_parent = tmp_path / "linked-parent"
        linked_parent.symlink_to(external, target_is_directory=True)
        output = linked_parent / "builds"
    else:
        _fake_build_process(monkeypatch, [b"same", b"same"])
        initial = build_compat_preloader(
            source=pinned_recursive_checkout,
            sdk=sdk,
            feed_dir=feed,
            output_dir=output,
            repo_root=root,
        )
        digest_dir = initial.dll.parent
        external = tmp_path / f"external-{position}"
        if position == "work":
            shutil.rmtree(output / ".work")
            external.mkdir()
            (output / ".work").symlink_to(external, target_is_directory=True)
        elif position == "digest-directory":
            shutil.copytree(digest_dir, external)
            shutil.rmtree(digest_dir)
            digest_dir.symlink_to(external, target_is_directory=True)
        elif position in {"dll", "provenance"}:
            victim = initial.dll if position == "dll" else initial.provenance
            external.write_bytes(victim.read_bytes())
            victim.unlink()
            victim.symlink_to(external)
        elif position == "current":
            current = output / "current.json"
            external.write_bytes(current.read_bytes())
            current.unlink()
            current.symlink_to(external)
        else:
            (digest_dir / "unexpected").write_bytes(b"extra")

    _fake_build_process(monkeypatch, [b"same", b"same"])
    with pytest.raises(CompatError, match="publication|output|build"):
        build_compat_preloader(
            source=pinned_recursive_checkout,
            sdk=sdk,
            feed_dir=feed,
            output_dir=output,
            repo_root=root,
        )


def test_build_restore_uses_locked_mode_without_unsupported_framework_switch(
    monkeypatch,
    pinned_recursive_checkout: Path,
    tmp_path: Path,
):
    state = _fake_build_process(monkeypatch, [b"same", b"same"])
    root = Path(__file__).resolve().parents[1]
    build_compat_preloader(
        source=pinned_recursive_checkout,
        sdk=root / "data/oracle/compat/dotnet-8.0.419/dotnet",
        feed_dir=root / "data/oracle/compat/fetch-acceptance",
        output_dir=tmp_path / "builds",
        repo_root=root,
    )
    restores = [
        command
        for command in state["commands"]
        if "restore" in command
        and any(item.endswith("BepInEx.Preloader.csproj") for item in command)
    ]
    assert len(restores) == 2
    assert all("--locked-mode" in command for command in restores)
    assert all("--framework" not in command for command in restores)
    assert all(
        "-p:RestoreBuildInParallel=false" in command for command in restores
    )
    publishes = [
        command
        for command in state["commands"]
        if "publish" in command
        and any(item.endswith("BepInEx.Preloader.csproj") for item in command)
    ]
    assert len(publishes) == 2
    assert all("-p:BuildInParallel=false" in command for command in publishes)
    assert all(
        "-p:EnableSourceControlManagerQueries=false" in command
        for command in publishes
    )


def test_build_cli_routes_exact_paths(compat_cli, monkeypatch, tmp_path, capsys):
    digest = "a" * 64
    metadata = _legacy_metadata()
    provenance_data = BuildProvenance(
        schema_version=1,
        source_commit="b" * 40,
        patch_sha256="c" * 64,
        toolchain_lock_sha256="d" * 64,
        dotnet_sdk_version="8.0.419",
        dependency_lock_sha256="e" * 64,
        build_target=(
            "BepInEx.Preloader/BepInEx.Preloader.csproj@framework=net35"
        ),
        official_preloader_sha256="f" * 64,
        patched_preloader_sha256=digest,
    )
    expected = BuildResult(
        dll=tmp_path / digest / "BepInEx.Preloader.dll",
        provenance=tmp_path / digest / "provenance.json",
        patched_sha256=digest,
        metadata=metadata,
        provenance_data=provenance_data,
    )
    observed = {}

    def fake_build(**arguments):
        observed.update(arguments)
        return expected

    monkeypatch.setattr(compat_cli, "build_compat_preloader", fake_build)
    assert compat_cli.main(
        [
            "build",
            "--source",
            "source",
            "--sdk",
            "sdk",
            "--feed-dir",
            "feed",
            "--output-dir",
            "output",
        ]
    ) == 0
    assert observed == {
        "source": Path("source"),
        "sdk": Path("sdk"),
        "feed_dir": Path("feed"),
        "output_dir": Path("output"),
        "repo_root": compat_cli._repo_root(),
    }
    assert json.loads(capsys.readouterr().out)["patched_sha256"] == digest
