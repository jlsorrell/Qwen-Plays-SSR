#!/usr/bin/env python3
"""Fetch and lock the immutable NuGet inputs for the compatibility build."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from ssr_env.oracle_compat import (
    CompatError,
    build_compat_preloader,
    canonical_json,
    inspect_assembly,
    load_toolchain,
    nuget_lock_tree_sha256,
)


NUGET_ORG_INDEX = "https://api.nuget.org/v3/index.json"
NUGET_ORG_PACKAGES = "https://api.nuget.org/v3-flatcontainer"
BEPINEX_INDEX = "https://nuget.bepinex.dev/v3/index.json"
BEPINEX_PACKAGES = "https://nuget.bepinex.dev/v3/package"
LOCK_ROOT = Path("oracle/compat/nuget-lock")
PACKAGE_SOURCES = {
    ("HarmonyX", "2.0.6"): (NUGET_ORG_INDEX, NUGET_ORG_PACKAGES),
    ("HarmonyX", "2.9.0"): (NUGET_ORG_INDEX, NUGET_ORG_PACKAGES),
    ("Microsoft.NETFramework.ReferenceAssemblies", "1.0.3"): (
        NUGET_ORG_INDEX,
        NUGET_ORG_PACKAGES,
    ),
    ("Microsoft.NETFramework.ReferenceAssemblies.net35", "1.0.3"): (
        NUGET_ORG_INDEX,
        NUGET_ORG_PACKAGES,
    ),
    ("Mono.Cecil", "0.10.4"): (NUGET_ORG_INDEX, NUGET_ORG_PACKAGES),
    ("MonoMod.RuntimeDetour", "20.5.21.5"): (
        NUGET_ORG_INDEX,
        NUGET_ORG_PACKAGES,
    ),
    ("MonoMod.RuntimeDetour", "22.1.29.1"): (
        NUGET_ORG_INDEX,
        NUGET_ORG_PACKAGES,
    ),
    ("MonoMod.Utils", "20.5.21.5"): (NUGET_ORG_INDEX, NUGET_ORG_PACKAGES),
    ("MonoMod.Utils", "22.1.29.1"): (NUGET_ORG_INDEX, NUGET_ORG_PACKAGES),
    ("UnityEngine", "5.6.1"): (BEPINEX_INDEX, BEPINEX_PACKAGES),
}


class _HttpsOnlyRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme.lower() != "https":
            raise CompatError("NuGet redirect target is not HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _locked_packages(repo_root: Path) -> dict[tuple[str, str], str]:
    packages: dict[tuple[str, str], str] = {}
    for path in sorted((repo_root / LOCK_ROOT).rglob("packages.lock.json")):
        decoded = json.loads(path.read_bytes())
        if not isinstance(decoded, dict) or decoded.get("version") != 1:
            raise CompatError(f"unsupported NuGet lock schema: {path}")
        frameworks = decoded.get("dependencies")
        if not isinstance(frameworks, dict):
            raise CompatError(f"invalid NuGet dependency tree: {path}")
        for dependencies in frameworks.values():
            if not isinstance(dependencies, dict):
                raise CompatError(f"invalid NuGet framework tree: {path}")
            for package_id, record in dependencies.items():
                if not isinstance(record, dict) or record.get("type") == "Project":
                    continue
                version = record.get("resolved")
                content_hash = record.get("contentHash")
                if not isinstance(version, str) or not isinstance(content_hash, str):
                    raise CompatError(f"incomplete NuGet pin for {package_id}")
                key = (package_id, version)
                previous = packages.setdefault(key, content_hash)
                if previous != content_hash:
                    raise CompatError(f"conflicting contentHash for {package_id} {version}")
    if len(packages) != 10:
        raise CompatError(f"expected exactly ten NuGet pins, found {len(packages)}")
    return packages


def _filename(package_id: str, version: str) -> str:
    return f"{package_id}.{version}.nupkg".lower()


def _source(package_id: str, version: str) -> tuple[str, str]:
    try:
        return PACKAGE_SOURCES[(package_id, version)]
    except KeyError as exc:
        raise CompatError(
            f"no trusted package source for {package_id} {version}"
        ) from exc


def _source_index(package_id: str, version: str) -> str:
    return _source(package_id, version)[0]


def _package_url(package_id: str, version: str) -> str:
    lowered_id = urllib.parse.quote(package_id.lower(), safe="")
    lowered_version = urllib.parse.quote(version.lower(), safe="")
    package_base = _source(package_id, version)[1]
    return (
        f"{package_base}/{lowered_id}/{lowered_version}/"
        f"{lowered_id}.{lowered_version}.nupkg"
    )


def fetch_packages(repo_root: Path, feed_dir: Path) -> None:
    feed_dir.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(
        _HttpsOnlyRedirects(), urllib.request.HTTPSHandler(context=ssl.create_default_context())
    )
    for package_id, version in sorted(
        _locked_packages(repo_root), key=lambda item: (item[0].lower(), item[1])
    ):
        destination = feed_dir / _filename(package_id, version)
        digest = hashlib.sha256()
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", dir=feed_dir
        )
        try:
            with os.fdopen(fd, "wb") as output:
                request = urllib.request.Request(
                    _package_url(package_id, version),
                    headers={"User-Agent": "ssr-bepinex-compat/1"},
                )
                with opener.open(request) as response:
                    final_scheme = urllib.parse.urlsplit(response.geturl()).scheme.lower()
                    if final_scheme != "https":
                        raise CompatError("NuGet response URL is not HTTPS")
                    while chunk := response.read(1024 * 1024):
                        digest.update(chunk)
                        output.write(chunk)
            temporary = Path(temporary_name)
            if destination.exists():
                existing = hashlib.sha256(destination.read_bytes()).hexdigest()
                if existing != digest.hexdigest():
                    raise CompatError(
                        f"refusing to overwrite different bytes: {destination}"
                    )
            else:
                temporary.replace(destination)
            print(f"{destination.name} {digest.hexdigest()}")
        finally:
            Path(temporary_name).unlink(missing_ok=True)


def _require_clean_inputs(repo_root: Path) -> tuple[bytes, bytes]:
    from ssr_env.oracle_compat import _require_head_blob

    patch = _require_head_blob(
        repo_root, "oracle/compat/bepinex-macos15-platform.patch"
    )
    toolchain = _require_head_blob(repo_root, "oracle/compat/toolchain.json")
    nuget_lock_tree_sha256(repo_root, require_head=True)
    return patch, toolchain


def lock_packages(repo_root: Path, feed_dir: Path) -> None:
    patch, toolchain_bytes = _require_clean_inputs(repo_root)
    load_toolchain(repo_root / "oracle/compat/toolchain.json")
    records = []
    for (package_id, version), content_hash in sorted(
        _locked_packages(repo_root).items(),
        key=lambda item: (item[0][0].lower(), item[0][1]),
    ):
        filename = _filename(package_id, version)
        package_path = feed_dir / filename
        try:
            package_bytes = package_path.read_bytes()
        except OSError as exc:
            raise CompatError(f"missing package: {package_path}") from exc
        sha256 = hashlib.sha256(package_bytes).hexdigest()
        records.append(
            {
                "content_hash": content_hash,
                "filename": filename,
                "package_id": package_id,
                "sha256": sha256,
                "source_index": _source_index(package_id, version),
                "version": version,
            }
        )

    dependencies_bytes = canonical_json(
        {"packages": records, "schema_version": 1}
    )
    dependencies_path = repo_root / "oracle/compat/dependencies.json"
    dependencies_path.write_bytes(dependencies_bytes)
    trust_bytes = canonical_json(
        {
            "dependencies_sha256": hashlib.sha256(dependencies_bytes).hexdigest(),
            "nuget_lock_tree_sha256": nuget_lock_tree_sha256(
                repo_root, require_head=True
            ),
            "patch_sha256": hashlib.sha256(patch).hexdigest(),
            "schema_version": 1,
            "toolchain_sha256": hashlib.sha256(toolchain_bytes).hexdigest(),
        }
    )
    (repo_root / "oracle/compat/trust.json").write_bytes(trust_bytes)
    print(f"wrote {dependencies_path.relative_to(repo_root)} ({len(records)} packages)")
    print("wrote oracle/compat/trust.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("fetch-packages", "lock"):
        subparser = commands.add_parser(command)
        subparser.add_argument("--feed-dir", type=Path, required=True)
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("--assembly", type=Path, required=True)
    inspect_parser.add_argument("--inspector", type=Path, required=True)
    build_parser = commands.add_parser("build")
    build_parser.add_argument("--source", type=Path, required=True)
    build_parser.add_argument("--sdk", type=Path, required=True)
    build_parser.add_argument("--feed-dir", type=Path, required=True)
    build_parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch-packages":
            fetch_packages(_repo_root(), args.feed_dir)
        elif args.command == "lock":
            lock_packages(_repo_root(), args.feed_dir)
        elif args.command == "inspect":
            metadata = inspect_assembly(args.assembly, args.inspector)
            sys.stdout.write(
                canonical_json(
                    {
                        "assembly_name": metadata.name,
                        "assembly_version": metadata.version,
                        "metadata_version": metadata.metadata_version,
                        "references": dict(metadata.references),
                        "target_framework": metadata.target_framework,
                    }
                ).decode("utf-8")
            )
        else:
            result = build_compat_preloader(
                source=args.source,
                sdk=args.sdk,
                feed_dir=args.feed_dir,
                output_dir=args.output_dir,
                repo_root=_repo_root(),
            )
            sys.stdout.write(
                canonical_json(
                    {
                        "dll": str(result.dll),
                        "patched_sha256": result.patched_sha256,
                        "provenance": str(result.provenance),
                    }
                ).decode("utf-8")
            )
    except CompatError as exc:
        parser.exit(1, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
