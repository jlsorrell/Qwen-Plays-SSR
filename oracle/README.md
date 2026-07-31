# SSR Executable Oracle

> **Safety invariant:** never modify `Sausage.app`,
> `Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll`, ordinary
> saves, or the Steam launcher. The tested BepInEx runtime, plugin, manifest,
> and recovery data live beside `Sausage.app` in the explicit game root.

This directory contains a minimal BepInEx 5 plugin compatibility probe for
Stephen's Sausage Roll. The probe targets .NET Framework 3.5, checks that the
three game methods needed by later oracle work are present, and writes one load
marker. It does not patch the game assembly or implement later oracle behavior.

The current controlled-boot target is **macOS Tahoe 26.6**. macOS 15.7.3 is
historical context only: it is where the original obsolete-platform-probe
failure was recorded. Exactly one approved initial Tahoe boot occurred. Its
runtime boot succeeded, but the old observer watched only `preloader_*.log`
and therefore missed the authentic `BepInEx/LogOutput.log` success output. The
official preloader was then restored transactionally and its healthy
`official` state verified.

The canonical observer correction is implemented and offline-tested. Its
immutable code/test evidence is the commit range
`2f27ede141b3b16b57806e18b7e82b4e8658b394` through
`8a63be151f9a08c7e0674d6de74548396fa9f623`; final independent branch/PR
review remains pending. Corrected runtime validation is also pending: no
second deployment, game launch, end-to-end installed-game pass, or installed
plugin/config change has occurred.

## Current stop gate

Offline rebuilds, tests, and the read-only status and preflight commands remain
usable. The observer is implemented and offline-tested, but it has not been
exercised by a corrected second game launch and final branch/PR review remains
pending. The mutation, boot, restore, and re-deploy commands below are
reference-only; this document does not authorize their execution.

Before *any* mutation, deploy, restore, or launch command below is used, run a
fresh read-only preflight and obtain separate explicit approval that names the
exact command sequence. That approval must limit the operation to
installer-only deployment, exactly one corrected bounded probe, and a verified
official restore; it must not be inferred from the first launch or from this
runbook. Do not make individual commands from the transactional section
generally runnable or reuse an approval for another deployment, launch, or
re-deployment.

Run all repository commands below from the root of the
`ssr-executable-oracle` worktree. Networked acquisition and installed-game
mutation are separately identified; neither is part of an offline rebuild or
read-only preflight.

## Pinned upstream, patch, and official bytes

The upstream is [BepInEx/BepInEx](https://github.com/BepInEx/BepInEx). Its
`LICENSE` committed at the pinned source revision is the MIT License
(copyright 2018 Bepis). This repository redistributes the textual patch and
build metadata, not BepInEx source or binaries.

The complete reviewed identity is:

- BepInEx release/source parent:
  `57f1fb859bd4d0264cd2a59074d0e96c6a492a33`
- recursive `submodules/BepInEx.Harmony` revision:
  `d4cdcb4cdeac14a0b77012165f5f5a9f5032a9fa`
- official macOS universal 5.4.23.5 archive SHA-256:
  `01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323`
- official `BepInEx/core/BepInEx.Preloader.dll` SHA-256:
  `309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627`
- accepted patched `BepInEx.Preloader.dll` SHA-256:
  `5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816`
- expected game `Assembly-CSharp.dll` SHA-256:
  `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`

`oracle/compat/bepinex-macos15-platform.patch` is one hunk in
`BepInEx.Preloader/Platform.cs`. In the legacy `PlatformID.Unix` branch it
replaces the obsolete
`Directory.Exists("/System/Library/AccessibilityBundles")` test and
`Platform.iOS` result with
`Directory.Exists("/System/Library/CoreServices")` and `Platform.MacOS`.
Nothing else in upstream source may differ.

## Locked toolchain and package graph

The only supported compatibility-builder SDK is the macOS Arm64 .NET SDK
`8.0.419`. Its committed archive SHA-512 is:

```text
8a539eeefd2a8e7430c1967584a79dac366faad732541dfb8ed90192de776bd5be94170dfac493ee6b4a8ae2603de9952ce2d2b9022e90003c4b62d7aeb2379a
```

The fixed build target is
`BepInEx.Preloader/BepInEx.Preloader.csproj`, configuration `Release`, exact
framework `net35`. Deterministic and continuous-integration compilation, a
stable `PathMap`, and disabled source-control-manager queries are committed in
`oracle/compat/toolchain.json`.

`oracle/compat/dependencies.json` locks exactly these ten package
ID/version/SHA-256 triples:

| Package | Version | `.nupkg` SHA-256 |
| --- | --- | --- |
| `HarmonyX` | `2.0.6` | `cf65037064621575bf098172d30c3cf138266d73ab5be62d849e25a78cce732e` |
| `HarmonyX` | `2.9.0` | `290cdc58b664c2d40e8b86faf455d1a31e53fb7f1960079330daa7122e5aa18f` |
| `Microsoft.NETFramework.ReferenceAssemblies` | `1.0.3` | `141a093f90c7645d101ccd312e6f727781c965540eb92a52280f95411a698441` |
| `Microsoft.NETFramework.ReferenceAssemblies.net35` | `1.0.3` | `b16156111a88670d91a757fbd465fcb4856e034b1a4d523ae2c41a470f3578f9` |
| `Mono.Cecil` | `0.10.4` | `3451a4a112a81be0bf76b8dc2bca396acdf0455d80c8961e7903ce1fb35c2a9a` |
| `MonoMod.RuntimeDetour` | `20.5.21.5` | `c19a5354df13d6f21f70673bb269a745f6670f9013a11dfd4cf3a3ace6d4397f` |
| `MonoMod.RuntimeDetour` | `22.1.29.1` | `8224e82b4a473f9c66b43ae7bdd6202a26210ef9b6403e0837f443b095d43a2a` |
| `MonoMod.Utils` | `20.5.21.5` | `6298cdccdae0fa50ac2f108f9affd8c2f62c4e7ff361dd7cbae4efe03d0666ff` |
| `MonoMod.Utils` | `22.1.29.1` | `6f9c48ad7ed8fd862ac7b89df653245c97a046d9de3cd7256e3a3603c5a715ee` |
| `UnityEngine` | `5.6.1` | `350ab9017bfece555e9479949cff68a50aaca0d86075f426ae0acb132d057096` |

## Trust and practical threat boundary

The builder trusts compatibility inputs only when the named patch, toolchain,
dependency manifest, five NuGet lock files, and trust manifest are tracked and
byte-identical to their committed `HEAD` blobs. Their committed hashes must
agree with `oracle/compat/trust.json`.

It then requires the exact clean parent revision, an initialized clean Harmony
submodule at the exact recursive revision, the exact ten package files and
hashes, and the authenticated SDK archive. It applies the one-hunk patch to two
independent fresh source roots, performs locked local-feed restores with no
network source, and accepts only byte-identical deterministic outputs with
legacy CLR/net35 metadata. Publication pairs the hash-addressed DLL with
canonical `provenance.json`; `current.json` must select that same pair.
Neither the installer nor an operator may mix a DLL with different provenance.

The practical threat boundary assumes the operating system and the current
local user are trusted and that no hostile local process races the repository,
game root, configuration, launcher, or evidence tree. Accidental updates,
wrong hashes, symlinks, special files, changed identities, I/O failures,
timeouts, and one catchable interruption remain in scope and fail closed. This
is a reproducible research workflow, not a privilege boundary or hostile
multi-user launcher.

## Ignored and generated locations

Never commit or clean these owner-local/generated paths:

- `data/oracle/compat/upstream/` — recursive BepInEx checkout
- `data/oracle/compat/downloads/` — SDK and other authenticated downloads
- `data/oracle/compat/dotnet-8.0.419/` — extracted SDK
- `data/oracle/compat/feed/` — exact local NuGet feed
- `data/oracle/compat/builds/`, including hash-addressed DLL/provenance pairs,
  temporary logs, and `builds/current.json`
- `data/oracle/boot-probe/` — retained controlled-boot evidence
- `oracle/plugin/bin/` and `oracle/plugin/obj/`
- `oracle/plugin/tests/bin/` and `oracle/plugin/tests/obj/`

`data/oracle/` is ignored as a whole. Build failures, boot failures, and
transaction recovery are evidence; do not remove them to make a later run
appear clean.

## Networked acquisition (documentation only during an offline checkpoint)

These commands deliberately use the network and must run only as separately
authorized acquisition steps. They are not part of the offline rebuild.

Acquire and verify the exact recursive source:

```bash
git clone --no-checkout https://github.com/BepInEx/BepInEx.git \
  data/oracle/compat/upstream/BepInEx-5.4.23.5
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  checkout --detach 57f1fb859bd4d0264cd2a59074d0e96c6a492a33
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  submodule update --init --recursive
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 rev-parse HEAD
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  submodule status --recursive
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  status --porcelain=v1 --untracked-files=all
git -C data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  show 57f1fb859bd4d0264cd2a59074d0e96c6a492a33:LICENSE
```

The first result must be the pinned parent; recursive submodule status must be
exactly the pinned Harmony revision with a leading space; source status must
print nothing; the license must be MIT. Stop on any delta.

Acquire and verify SDK 8.0.419:

```bash
mkdir -p data/oracle/compat/downloads
curl --fail --location --proto '=https' \
  --output data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz \
  https://builds.dotnet.microsoft.com/dotnet/Sdk/8.0.419/dotnet-sdk-8.0.419-osx-arm64.tar.gz
curl --fail --location --proto '=https' \
  --output data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz.sha512 \
  https://builds.dotnet.microsoft.com/dotnet/Sdk/8.0.419/dotnet-sdk-8.0.419-osx-arm64.tar.gz.sha512
shasum -a 512 \
  data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz
sed -n '1p' \
  data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz.sha512
mkdir data/oracle/compat/dotnet-8.0.419
tar -xzf \
  data/oracle/compat/downloads/dotnet-sdk-8.0.419-osx-arm64.tar.gz \
  -C data/oracle/compat/dotnet-8.0.419
data/oracle/compat/dotnet-8.0.419/dotnet --version
```

The computed and Microsoft-published SHA-512 strings must both equal the
committed 128-hex value above before extraction; the version must print exactly
`8.0.419`.

Acquire the exact NuGet graph and reproduce its lock metadata:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py fetch-packages \
  --feed-dir /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/feed
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py lock \
  --feed-dir /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/feed
git diff --exit-code -- oracle/compat/dependencies.json \
  oracle/compat/trust.json
```

`fetch-packages` is the only package-network step. `lock` must reproduce the
committed canonical manifests byte-for-byte, and every feed hash must equal
the table above. A diff is a stop condition, not authorization to update a
pin.

The official BepInEx runtime archive is acquired and verified separately:

```bash
curl --fail --location --proto '=https' --tlsv1.2 \
  "https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.5/BepInEx_macos_universal_5.4.23.5.zip" \
  -o /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
shasum -a 256 /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
unzip -l /private/tmp/BepInEx_macos_universal_5.4.23.5.zip
```

Only the pinned archive hash is accepted. Initial runtime installation is an
installed-game mutation and requires separate authorization. In the same shell
that will perform an authorized initial install, run this install-only guard
immediately before the install command:

```bash
SSR_INSTALL_GAME_ROOT="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
SSR_RUNTIME_ARCHIVE="/private/tmp/BepInEx_macos_universal_5.4.23.5.zip"
readonly SSR_INSTALL_GAME_ROOT SSR_RUNTIME_ARCHIVE

case "$SSR_INSTALL_GAME_ROOT" in
  /*) ;;
  *) printf 'SSR_INSTALL_GAME_ROOT is not absolute\n' >&2; exit 1 ;;
esac
case "$SSR_RUNTIME_ARCHIVE" in
  /*) ;;
  *) printf 'SSR_RUNTIME_ARCHIVE is not absolute\n' >&2; exit 1 ;;
esac
test -d "$SSR_INSTALL_GAME_ROOT" && test ! -L "$SSR_INSTALL_GAME_ROOT" ||
  exit 1
test -f "$SSR_RUNTIME_ARCHIVE" && test ! -L "$SSR_RUNTIME_ARCHIVE" ||
  exit 1
printf 'SSR_INSTALL_GAME_ROOT=%s\n' "$SSR_INSTALL_GAME_ROOT"
printf 'SSR_RUNTIME_ARCHIVE=%s\n' "$SSR_RUNTIME_ARCHIVE"
printf '%s  %s\n' \
  01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323 \
  "$SSR_RUNTIME_ARCHIVE" |
  shasum -a 256 -c - || exit 1

UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py install \
  --game-root "$SSR_INSTALL_GAME_ROOT" \
  --archive "$SSR_RUNTIME_ARCHIVE"
```

The installer places BepInEx beside `Sausage.app`; never unpack or copy it
manually.

## Offline compatibility rebuild

With source, SDK, and feed already acquired, run this exact command. `UV_OFFLINE`
prevents `uv` from fetching, and the builder's generated NuGet configuration
clears all remote sources:

```bash
UV_OFFLINE=1 UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python \
  tools/build_bepinex_compat.py build \
  --source /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/upstream/BepInEx-5.4.23.5 \
  --sdk /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/dotnet-8.0.419/dotnet \
  --feed-dir /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/feed \
  --output-dir /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds
```

Require the reported hash to be
`5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816`.
The only deployable pair is:

```text
data/oracle/compat/builds/5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816/BepInEx.Preloader.dll
data/oracle/compat/builds/5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816/provenance.json
```

`current.json` must canonically select those two relative paths and the same
hash. The builder has already performed two independent builds; do not select
an output manually or pair the DLL with another provenance file.

## Plugin build and dependency-free harness

The plugin build requires explicit paths to the game's managed assemblies and
the installed BepInEx core. A one-time restore, when genuinely required, is a
separately authorized package-network operation:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet restore \
  oracle/plugin/SsrOracle.Plugin.csproj \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
```

Normal verification performs no restore:

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"

/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore
```

The build must have zero warnings and zero errors. The harness must print
exactly:

```text
SSR oracle unit harness ready
```

The plugin output is
`oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll`. Deployable Release
builds omit revision and debug/PDB metadata, so Git and artifact hashes remain
external provenance; no Release PDB is produced. The project removes
`tests/**/*.cs` from its compile items so the independent .NET 10 harness is
never compiled against the game's global types.

The game selects Unity's legacy scripting runtime and loads CLR
`v2.0.50727`/`mscorlib 2.0.0.0` assemblies. The shipped `UnityEngine.dll` is a
CLR 4 compatibility/type-forwarding facade, so every shipped BepInEx/game
reference is marked `ExternallyResolved`: this prevents MSBuild from traversing
that facade while preserving the exact `net35` target and the assembly graph
that the legacy Unity loader supplies. A verified build emits a
`v2.0.50727` plugin with direct references to `mscorlib 2.0.0.0` and
`BepInEx 5.4.23.5`, and does not copy the runtime or game dependency set.

## Installer states and read-only status

Always run status before mutation:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py status \
  --game-root "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
```

The compatibility state has exactly these meanings:

- `official`: the active preloader has the pinned official hash, there are no
  live compatibility manifest entries, and
  `BepInEx/.ssr-oracle-backup` plus `BepInEx/.ssr-oracle-compat` are absent.
- `patched`: active DLL, official backup, canonical provenance, committed
  input hashes, and manifest entries agree, and the active/provenance hash is
  the accepted patched hash.
- `invalid`: every other state. Overall installer `healthy` is false.

Status is read-only and never repairs. If status is `invalid`, unhealthy, or
reports any issue, stop. Do not deploy, boot, restore, rename, copy, or
manually reconcile the game root.

## Read-only preflight

Before every controlled mutation, record:

```bash
sw_vers
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py status \
  --game-root "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
shasum -a 256 \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll"
shasum -a 256 \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core/BepInEx.Preloader.dll"
shasum -a 256 \
  "/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816/BepInEx.Preloader.dll" \
  "/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816/provenance.json" \
  "/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll" \
  "/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/boot-probe.cfg"
codesign --verify --deep --strict --verbose=1 \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app"
stat -f '%Sp %Lp %N' \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/run_bepinex.sh" \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/config/dev.jlsor.ssr.oracle.cfg"
shasum -a 256 \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/config/dev.jlsor.ssr.oracle.cfg"
od -An -tx1 -v \
  "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/config/dev.jlsor.ssr.oracle.cfg"
```

The probe performs one
`codesign --verify --deep --strict --verbose=1 APP` call per signature
snapshot and preserves its raw return code, stdout, and stderr separately in
the evidence. Tahoe may reorder stdout lines between calls, so acceptance and
pre/post comparison treat stdout as an order-insensitive exact multiset while
preserving every line ending and duplicate. Stderr remains byte-exact and
separate from stdout.

The exact clean Tahoe result has return code 0, empty stdout, and exactly these
two path-derived stderr lines (each includes its trailing newline):

```text
/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app: valid on disk
/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app: satisfies its Designated Requirement
```

This identity was captured with the production
`codesign --verify --deep --strict --verbose=1 APP` command against a safe
locally ad-hoc-signed temporary app on Tahoe 26.6. The former empty-stderr
success identity came from non-verbose semantics and is not accepted.

The only accepted nonzero Tahoe result has return code 1, generic app-root
stderr, and exactly this seven-line stdout multiset (each line includes its
trailing newline):

```text
file added: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle/Contents/_CodeSignature/CodeResources
file added: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle/Contents/_CodeSignature/CodeDirectory
file added: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle/Contents/_CodeSignature/CodeRequirements
file added: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle/Contents/MacOS/Foregroundr
file added: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle/Contents/_CodeSignature/CodeSignature
file added: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle/Contents/Info.plist
file missing: /Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Plugins/Foregroundr.bundle
```

The exact stderr is this single line with its trailing newline:

```text
/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app: a sealed resource is missing or invalid
```

No historical non-Tahoe nonzero result is accepted. Supporting another macOS
result requires a separately reviewed capture. Any missing, added, duplicated,
moved-between-streams, or changed line—including any unrelated resource
difference—is a stop condition.

The config must be a regular non-symlink file with its exact recorded bytes and
mode, exactly one `[Oracle]` section, and exactly one `Mode = off` entry in
that section.

## Resolve mutation paths

Installed-game mutation requires separate approval. In one shell, set, make
read-only, validate, and print these explicit absolute paths before any
deploy, boot, restore, or re-deploy command:

```bash
SSR_GAME_ROOT="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll"
SSR_PATCHED_PRELOADER="/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816/BepInEx.Preloader.dll"
SSR_PATCHED_PROVENANCE="/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/compat/builds/5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816/provenance.json"
SSR_PLUGIN="/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll"
SSR_DEPLOY_CONFIG="/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/boot-probe.cfg"
SSR_LAUNCHER="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/run_bepinex.sh"
SSR_INSTALLED_CONFIG="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/config/dev.jlsor.ssr.oracle.cfg"
SSR_EVIDENCE_ROOT="/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-executable-oracle/data/oracle/boot-probe"
readonly SSR_GAME_ROOT SSR_PATCHED_PRELOADER SSR_PATCHED_PROVENANCE
readonly SSR_PLUGIN SSR_DEPLOY_CONFIG SSR_LAUNCHER SSR_INSTALLED_CONFIG
readonly SSR_EVIDENCE_ROOT

for SSR_ABSOLUTE_PATH in \
  "$SSR_GAME_ROOT" \
  "$SSR_PATCHED_PRELOADER" \
  "$SSR_PATCHED_PROVENANCE" \
  "$SSR_PLUGIN" \
  "$SSR_DEPLOY_CONFIG" \
  "$SSR_LAUNCHER" \
  "$SSR_INSTALLED_CONFIG" \
  "$SSR_EVIDENCE_ROOT"
do
  case "$SSR_ABSOLUTE_PATH" in
    /*) ;;
    *) printf 'path is not absolute: %s\n' "$SSR_ABSOLUTE_PATH" >&2; exit 1 ;;
  esac
done
unset SSR_ABSOLUTE_PATH

test -d "$SSR_GAME_ROOT" && test ! -L "$SSR_GAME_ROOT" || exit 1
for SSR_ORDINARY_FILE in \
  "$SSR_PATCHED_PRELOADER" \
  "$SSR_PATCHED_PROVENANCE" \
  "$SSR_PLUGIN" \
  "$SSR_DEPLOY_CONFIG" \
  "$SSR_LAUNCHER" \
  "$SSR_INSTALLED_CONFIG"
do
  test -f "$SSR_ORDINARY_FILE" && test ! -L "$SSR_ORDINARY_FILE" || exit 1
done
unset SSR_ORDINARY_FILE
test -x "$SSR_LAUNCHER" || exit 1
test ! -L "$SSR_EVIDENCE_ROOT" || exit 1
if test -e "$SSR_EVIDENCE_ROOT"; then
  test -d "$SSR_EVIDENCE_ROOT" && test ! -L "$SSR_EVIDENCE_ROOT" || exit 1
else
  test -d "${SSR_EVIDENCE_ROOT%/*}" &&
    test ! -L "${SSR_EVIDENCE_ROOT%/*}" || exit 1
fi

printf 'SSR_GAME_ROOT=%s\n' "$SSR_GAME_ROOT"
printf 'SSR_PATCHED_PRELOADER=%s\n' "$SSR_PATCHED_PRELOADER"
printf 'SSR_PATCHED_PROVENANCE=%s\n' "$SSR_PATCHED_PROVENANCE"
printf 'SSR_PLUGIN=%s\n' "$SSR_PLUGIN"
printf 'SSR_DEPLOY_CONFIG=%s\n' "$SSR_DEPLOY_CONFIG"
printf 'SSR_LAUNCHER=%s\n' "$SSR_LAUNCHER"
printf 'SSR_INSTALLED_CONFIG=%s\n' "$SSR_INSTALLED_CONFIG"
printf 'SSR_EVIDENCE_ROOT=%s\n' "$SSR_EVIDENCE_ROOT"

{
  printf '%s  %s\n' \
    5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816 \
    "$SSR_PATCHED_PRELOADER"
  printf '%s  %s\n' \
    1bc5a022de6940255aec977164e17c0c1f3c0c08bd480caf0a4caf248ed563db \
    "$SSR_PATCHED_PROVENANCE"
  printf '%s  %s\n' \
    73003a18348970edf3157fdc3865feb275eb254c8f6fd12ddcfa88b64135754b \
    "$SSR_PLUGIN"
  printf '%s  %s\n' \
    cd0f6f26a4f49d8eec9ca9bbf8a91aacf35d03c3f09f4cf52d193bd5036f787d \
    "$SSR_DEPLOY_CONFIG"
} | shasum -a 256 -c - || exit 1
```

Do not continue from another shell where these values were not printed and
validated. Do not substitute a relative path, stale `current.json` path, or
unresolved environment value. The four checksum results immediately before
the first mutation must all print `OK`; otherwise stop.

## Reviewed boot-log observer contract

The offline-tested observer classifies exactly three monitored families under
the game root, using the existing recursive no-follow scan:

1. the sole canonical success path, `BepInEx/LogOutput.log`;
2. canonical fallback paths, `BepInEx/LogOutput.log.1` through
   `BepInEx/LogOutput.log.4`;
3. failure paths whose basename matches the existing case-sensitive
   `preloader_*.log` rule.

No other `*.log` path, including Unity's user-global `Player.log`, is accepted
as probe evidence. Success is canonical-only: all three required markers must
come from one retained canonical `BepInEx/LogOutput.log`. The authentic Unity
source text is `Detected Unity version: v2018.4.25f1`; the observer derives
the stable public schema-v1 marker `Unity v2018.4.25f1` only from that exact
source line. `BootProbeResult.markers`, CLI JSON, and `probe.json.markers`
therefore retain their public marker names, and `probe.json` remains schema
version 1.

A new or changed member of either failure family (a numbered fallback or a
`preloader_*.log`) is always a structural failure when observed, even if the
canonical log contains every marker. The observer retains such evidence when
preservable and records an evidence-integrity issue when it cannot be
preserved. A new canonical log is moved into evidence; a changed pre-existing
canonical log is copied into evidence and remains installed. An unchanged
canonical log cannot satisfy a current run.

Before launch, the observer validates only the strict BepInEx logging subset
that guarantees canonical output and early-marker visibility. An absent
`BepInEx/config` directory or absent `BepInEx.cfg` leaf accepts the pinned
disk and console defaults. If `BepInEx.cfg` exists, it must be a regular,
no-follow file beneath a real `BepInEx/config` directory and the following
disk contract is mandatory:

```ini
[Logging.Disk]
AppendLog = false
Enabled = true
LogLevels = Fatal, Error, Warning, Message, Info

[Logging.Console]
LogLevels = Fatal, Error, Warning, Message, Info
```

The present-file cardinality and scope rules are exact:

- There must be exactly one exactly-spelled `[Logging.Disk]` section, with
  exactly one exactly-spelled `Enabled`, `AppendLog`, and `LogLevels` key in
  that section. A relevant key in another section does not satisfy the disk
  requirement.
- `[Logging.Console]` is optional. If present, there is at most one
  exactly-spelled console section and at most one exactly-spelled `LogLevels`
  key in it. An absent console section or console `LogLevels` uses the pinned
  console default; other keys and unrelated sections do not alter this subset.
- `Enabled` must be `true` and `AppendLog` must be `false`, case-insensitively
  after value trimming. Disk and explicit console `LogLevels` each accept
  either the singleton `All` (case-insensitively) or a comma-separated,
  duplicate-free list containing every required visibility level—`Fatal`,
  `Error`, `Warning`, `Message`, and `Info`—in any order, with one optional
  `Debug`. `All` cannot be combined with `Debug` or any other item.

The parser accepts a leading UTF-8 BOM and CRLF line endings, but rejects
invalid UTF-8, an embedded BOM, NUL bytes, and bare carriage returns. Blank
lines and whole-line `#` comments are allowed; inline comments are rejected.
Outer line and key/value whitespace is trimmed, but internal case/whitespace
lookalikes are not normalized into monitored names.
Every remaining line must be either a well-formed single-bracket section or a
key/value line with `=`. Malformed or empty sections/keys, duplicate relevant
sections or keys, and case/whitespace lookalikes of monitored keys within their
disk/console scope are rejected. Disabled, append-mode, unknown, repeated,
empty, or insufficient log-level lists are rejected; a console level list
cannot satisfy the required disk list.

The complete monitored inventory is fingerprinted twice before launch: once
before the longer preflight and once immediately before `Popen`. Any difference
between those snapshots rejects the probe before launch; the second snapshot
is the authoritative baseline.

## Transactional deploy and controlled boot

> **GATE — reference only:** the observer correction is implemented and
> offline-tested, but corrected runtime validation has not occurred. Do not run
> a command in this section without a fresh successful read-only preflight and
> separate explicit approval for the complete installer-only deployment, one
> bounded probe, and verified official-restore sequence.

For a future explicitly approved checkpoint, transactionally deploy the
hash-verified rebuilt plugin and Mode-off config only through the installer.
Healthy `official` status proves that the
installed plugin matches its existing manifest; it does not prove that it
matches this rebuild. The installed plugin remains
`6d06583d75bfdc5a677668c3c7b0bd88f9eec49be0d169cf6f357ccac4cc7de4`;
the required reproducible rebuild hash is
`73003a18348970edf3157fdc3865feb275eb254c8f6fd12ddcfa88b64135754b`.
Deploy both artifacts only through the installer:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py deploy \
  --game-root "$SSR_GAME_ROOT" \
  --plugin "$SSR_PLUGIN" \
  --config "$SSR_DEPLOY_CONFIG"
```

Deploy the paired preloader/provenance and require healthy `patched` status:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  deploy-preloader --game-root "$SSR_GAME_ROOT" \
  --preloader "$SSR_PATCHED_PRELOADER" \
  --provenance "$SSR_PATCHED_PROVENANCE"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  status --game-root "$SSR_GAME_ROOT"
```

Only then run the bounded boot probe:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_boot_probe.py \
  --game-root "$SSR_GAME_ROOT" \
  --launcher "$SSR_LAUNCHER" \
  --config "$SSR_INSTALLED_CONFIG" \
  --evidence-root "$SSR_EVIDENCE_ROOT" --timeout 120
```

Controlled-boot success requires all three exact markers:

```text
BepInEx 5.4.23.5
Unity v2018.4.25f1
SSR oracle boot probe loaded
```

It also requires no `DllNotFoundException`, no `Preloader error`, no timeout or
unexpected pre-termination exit, healthy `patched` status before and after,
unchanged assembly and active-preloader hashes, the same accepted
order-insensitive stdout signature multiset and byte-exact stderr/return code,
exact config-byte/mode restoration, and final `Mode = off`. Raw signature
streams remain preserved even though stdout order is normalized for
comparison. Missing or extended version markers are failures. Evidence is
retained below
`$SSR_EVIDENCE_ROOT/<UTC>-<128-bit-random>/` on success or failure.

## Exact restore and identical re-deploy

> **GATE — reference only:** this restore or re-deploy must be separately
> covered by the fresh preflight and explicit approval above. The official
> restore is required and must be verified after the one approved probe.

Restore requires a healthy patched state and moves the official preloader back
transactionally:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  restore-preloader --game-root "$SSR_GAME_ROOT"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  status --game-root "$SSR_GAME_ROOT"
shasum -a 256 "$SSR_GAME_ROOT/BepInEx/core/BepInEx.Preloader.dll"
```

Require healthy `official` status, the exact official preloader hash, absent
live compatibility roots, and the recovery path printed by restore.

Re-deploy the exact same pair, verify it, then repeat the identical command to
prove idempotence. Do not launch the game during the second deploy:

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  deploy-preloader --game-root "$SSR_GAME_ROOT" \
  --preloader "$SSR_PATCHED_PRELOADER" \
  --provenance "$SSR_PATCHED_PROVENANCE"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  status --game-root "$SSR_GAME_ROOT"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  deploy-preloader --game-root "$SSR_GAME_ROOT" \
  --preloader "$SSR_PATCHED_PRELOADER" \
  --provenance "$SSR_PATCHED_PROVENANCE"
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python tools/oracle_install.py \
  status --game-root "$SSR_GAME_ROOT"
```

Both results must be the same healthy `patched` state, with unchanged game
assembly and accepted patched-preloader hashes.

## Failure handling and retained recovery

Deploy and restore fail closed. They snapshot and validate the active
preloader, manifest, official backup, provenance, relevant directories, bytes,
hashes, identities, and modes. On a caught transaction failure they attempt to
restore the exact pre-call live bytes and modes while preserving the primary
error and any rollback concern.

Recovery is evidence, not scratch space. Transaction-owned staging,
temporary, displaced, quarantine, compatibility, and cleanup artifacts remain
under an exclusive
`.ssr-oracle-recovery/<UTC>-<128-bit-random>/` run. Deploy and restore perform
no terminal deletion (`unlink` or `rmdir`) of those artifacts, and operators
must not delete them manually.

The boot probe retains the opened config and parent descriptors and restores
the exact original config bytes and mode on every reachable exit. It never
writes through a replacement public path. If config restoration, process
cleanup, evidence publication, signature comparison, hash comparison, or
installer postflight fails, preserve all evidence and stop. Never “repair”
`invalid` state by copying, renaming, deleting, re-signing, relaunching through
Steam, or editing the config by hand.
