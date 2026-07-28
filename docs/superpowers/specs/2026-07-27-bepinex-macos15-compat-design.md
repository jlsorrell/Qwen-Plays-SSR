# BepInEx macOS 15 Compatibility Layer Design

**Date:** 2026-07-27

**Status:** Approved approach; implementation pending

**Scope:** Unblock the executable SSR oracle on macOS 15 without modifying
`Sausage.app` or committing a third-party binary.

## Context

The executable-oracle runtime is intentionally installed beside the Steam game,
not inside its app bundle. Doorstop successfully enters BepInEx 5.4.23.5, but
the BepInEx preloader then aborts before the chainloader or SSR oracle plugin can
run:

```text
System.DllNotFoundException: libc.so.6
  at BepInEx.Preloader.PlatformUtils.uname_linux
  at BepInEx.Preloader.PreloaderRunner.PreloaderPreMain
  at Doorstop.Entrypoint.Start
```

The affected environment is:

- macOS 15.7.3;
- Stephen's Sausage Roll's Unity 2018.4.25f1 legacy Mono runtime, launched as
  x86_64 under Rosetta where necessary;
- the official BepInEx macOS universal 5.4.23.5 archive, SHA-256
  `01c2ae782eb016dfd6c345a18dbd2dcafffb3d9d318449d6486689f426b4a323`;
- BepInEx source commit
  `57f1fb859bd4d0264cd2a59074d0e96c6a492a33`;
- the official archive's `BepInEx.Preloader.dll`, SHA-256
  `309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627`;
- the expected game `Assembly-CSharp.dll`, SHA-256
  `886660b51e0cc6358c8a2cd194d2fc7f2d26303c19dfb307d93b53a2fda1c564`.

On this legacy Mono runtime, `Environment.OSVersion.Platform` reports `Unix`.
BepInEx 5.4.23.5 distinguishes macOS from Linux in that case by testing for
`/System/Library/AccessibilityBundles`. That obsolete directory is absent on
macOS 15.7.3, so the preloader classifies macOS as Linux and calls the Linux
library `libc.so.6`.

The failure is not caused by the Doorstop debug-console warning: the preloader
stack proves that injection succeeded. Doorstop flags cannot correct
BepInEx's platform classification. A `dllmap` would mask one Linux import
without fixing the false platform value and its downstream branches.
Downgrading BepInEx or moving to the current BepInEx 6 builds does not remove
the obsolete heuristic. Retargeting the SSR plugin to a newer framework cannot
change code that fails before plugin loading. Committing a rebuilt DLL would
make the provenance and reproducibility of privileged startup code harder to
audit.

## Goals

1. Apply one reviewable source patch to the exact pinned BepInEx 5.4.23.5
   source and build only the required preloader.
2. Make the build reproducible: two clean builds with the locked toolchain must
   produce byte-identical DLLs before deployment is allowed.
3. Deploy and restore the preloader transactionally through the existing
   manifest-based installer.
4. Preserve the official preloader byte-for-byte and make reversal a validated,
   first-class operation.
5. Record sufficient provenance to reconstruct and audit every deployed byte.
6. Leave `Sausage.app`, the game assembly, ordinary saves, and the normal Steam
   launcher untouched.

## Non-goals

- Maintaining a general-purpose BepInEx fork.
- Committing BepInEx source, NuGet packages, SDKs, or generated DLLs.
- Patching Doorstop, Unity, Mono, the game assembly, or unrelated BepInEx
  runtime components.
- Automatically upgrading BepInEx or accepting an unpinned upstream checkout.
- Generalizing platform detection beyond the legacy `Unix` ambiguity that
  blocks this game.
- Changing SSR mechanics, oracle protocol semantics, or simulator behavior.

## Repository Components

The implementation will use these committed components:

- `oracle/compat/bepinex-macos15-platform.patch` — the single exact source
  patch, including enough preimage context to reject an unexpected upstream
  tree.
- `oracle/compat/toolchain.json` — the source commit, supported host, exact
  .NET SDK version, dependency lock inputs, build target, deterministic build
  properties, and expected official preloader metadata/hash. It contains no
  machine-local paths.
- `oracle/compat/dependencies.json` and
  `oracle/compat/nuget-lock/**/*.lock.json` — exact NuGet package
  IDs/versions/SHA-256 values and the locked transitive restore graph, stored
  under their upstream-relative project paths.
- `oracle/compat/trust.json` — the expected SHA-256 values of the patch,
  toolchain lock, dependency manifest, and canonical digest of the NuGet lock
  tree.
- `src/ssr_env/oracle_compat.py` — side-effect-minimized validation,
  provenance, reproducible-build, and preloader-state helpers.
- `tools/build_bepinex_compat.py` — the operator CLI that invokes those helpers.
- `src/ssr_env/oracle_install.py` and `tools/oracle_install.py` — two new
  installer commands, `deploy-preloader` and `restore-preloader`, plus
  compatibility-aware status reporting.
- `tests/test_oracle_compat.py` and focused additions to
  `tests/test_oracle_install.py` — source, metadata, transaction, and restore
  tests.
- `oracle/README.md` — operator instructions, expected output, recovery steps,
  and the no-app-bundle invariant.

All fetched source, packages, intermediate files, DLLs, and local build
provenance live below `data/oracle/compat/`, which remains ignored. Build work
itself occurs in a new temporary directory so a failed or interrupted build
cannot contaminate either the supplied checkout or an earlier result.

## Source and Build Contract

The builder takes an explicit `--source` path to a local BepInEx Git checkout
and an explicit `--output-dir` below `data/oracle/compat/`. It performs no
network access. A separate fetch command may populate a local NuGet-feed
directory with the exact `.nupkg` files named in `dependencies.json`; fetching
is never combined with building or deployment.

Before copying any source, the builder must verify:

1. the source path is a Git worktree at exact commit
   `57f1fb859bd4d0264cd2a59074d0e96c6a492a33`;
2. the worktree and index are clean, with no untracked files that could affect
   the build;
3. the exact patch preimage exists once and the patched postimage does not;
4. `patch`, `toolchain.json`, `dependencies.json`, the NuGet lock tree, and
   `trust.json` are tracked, byte-identical to their `HEAD` Git blobs, and
   mutually match the hashes in `trust.json`;
5. the running SDK exactly matches `toolchain.json`, and every package in the
   explicit local feed matches `dependencies.json` with no extra package
   versions; and
6. the output directory is absent or contains only an identical completed
   build. It never overwrites a different completed result.

The builder copies the pinned checkout into a fresh temporary directory,
applies `git apply --check` followed by the patch, and builds only
`BepInEx.Preloader.dll` for the legacy CLR/.NET 3.5 target used by the official
archive. The implementation plan begins with a read-only inspection of the
pinned checkout that resolves the upstream project path, target framework,
build target, SDK, and complete restored dependency graph. Those concrete
values are committed in `toolchain.json` before builder implementation begins.
The production builder performs no discovery or fallback: it executes only that
fixed project/target and command. Schema validation and tests reject a lock file
missing any concrete value.

`dependencies.json` is canonical JSON containing the exact package ID, version,
filename, and SHA-256 of every package in the transitive graph. The
`nuget-lock/` tree contains the corresponding NuGet lock file for each restored
upstream project. Its canonical digest is SHA-256 over sorted pairs of
upstream-relative POSIX path and file SHA-256. Before each build, the builder
copies those locks into their recorded paths in the temporary source tree and
generates a temporary NuGet configuration with `<clear />` plus only the
validated local feed. It restores with locked mode into a fresh temporary
packages directory, with HTTP caches disabled, and fails on a missing, extra,
or changed graph entry. The subsequent compile uses `--no-restore`.

Deterministic and path-independent compiler properties, including a stable path
map and continuous-integration/deterministic flags supported by the pinned
project, are mandatory. The builder performs two independent clean builds in
different temporary paths. It fails unless their SHA-256 hashes and bytes are
identical.

The accepted DLL must then pass metadata checks:

- assembly identity is `BepInEx.Preloader`;
- product/file version is the pinned 5.4.23.5 release value recorded in the
  lock file;
- target runtime is CLR v2 and framework references remain compatible with the
  game's legacy Mono (`mscorlib` 2.0, with the precise reference set recorded
  by the lock);
- the patched method exists once; and
- no additional build output is selected for deployment.

The resulting Task 4 artifact is also pinned in reviewed source as
`5a777c72ee4cb592f5ea7b0fa7bb15f1db7fa417f1374536f327e3d42aad4816`.
This value was derived only after two authenticated builds in both in-repository
and external output roots produced byte-identical DLLs and the non-loading
inspector validated the compiled patch and exact legacy metadata. Subsequent
builds fail unless they reproduce this exact accepted artifact.

If reproducibility or metadata compatibility cannot be achieved with the
locked source and toolchain, the builder stops. A locally successful but
variable build is not deployable.

## Patch Semantics

The patch changes only the legacy platform-detection branch that receives
`PlatformID.Unix` in the pinned upstream file
`BepInEx.Preloader/Platform.cs`:

```text
if /System/Library/CoreServices exists:
    classify as macOS
else:
    classify as Linux
```

`/System/Library/CoreServices` is a stable macOS system directory present in
the supported environment. The patch removes the dependency on the obsolete
`/System/Library/AccessibilityBundles` probe. Explicit platform values and all
non-`Unix` branches remain unchanged.

The committed patch must be a one-hunk diff. Tests inspect the diff itself:
only `BepInEx.Preloader/Platform.cs` may change, no binary patch is allowed, the
old probe must be removed exactly once, and the new probe must appear exactly
once.

## Provenance

Each successful build writes canonical, UTF-8 JSON with sorted keys and a final
newline. The schema is versioned and contains exactly:

```json
{
  "schema_version": 1,
  "source_commit": "57f1fb859bd4d0264cd2a59074d0e96c6a492a33",
  "patch_sha256": "<64 lowercase hex>",
  "toolchain_lock_sha256": "<64 lowercase hex>",
  "dotnet_sdk_version": "<exact locked version>",
  "dependency_lock_sha256": "<64 lowercase hex>",
  "build_target": "<exact locked project and target>",
  "official_preloader_sha256": "309dd5f1f1dda9209dfc4522a29ac983994f0cca135dee7012582028e9a47627",
  "patched_preloader_sha256": "<64 lowercase hex>"
}
```

The build result is a pair: the patched DLL and this provenance file. The
builder writes both to a new hash-addressed result directory and atomically
publishes a small `current.json` pointer only after all validation and the
double-build comparison succeed. Paths and timestamps are deliberately absent
from provenance so they cannot make equivalent builds differ.

The trust model protects against accidental corruption, stale output, and
uncommitted local substitution. Build, deploy, restore, and patched status all
read `trust.json` from the repository and require it and every file it names to
be tracked and byte-identical to the corresponding `HEAD` blob. A repository
commit that deliberately changes the trust catalog remains a normal
security-sensitive code-review event; defending against a compromised Git
history or malicious repository maintainer is outside this local tool's threat
model.

## Deployment Contract

The installer command is:

```text
oracle_install.py deploy-preloader \
  --game-root <game-root> \
  --preloader <patched-dll> \
  --provenance <provenance-json>
```

Before any mutation it must:

1. inspect the expected SSR game and verify the pinned game assembly hash;
2. load a recognized, healthy SSR oracle install manifest tied to the official
   BepInEx archive hash;
3. validate the provenance schema, all pinned values, the committed patch and
   lock hashes, and the supplied DLL hash/metadata;
4. require the current `BepInEx/core/BepInEx.Preloader.dll` to equal both its
   manifest entry and the official preloader hash;
5. refuse symlinks, traversal, unexpected file types, unmanaged compatibility
   paths, or a pre-existing non-identical backup; and
6. snapshot the current manifest and all targets needed for rollback.

All mutable game, staging, and recovery directories are opened and retained by
descriptor using `O_DIRECTORY | O_NOFOLLOW`. Publication, rollback, recovery
moves, and manifest replacement use descriptor-relative operations and verify
the pinned directory device/inode identities, so a pathname component swapped
after preflight cannot redirect a write outside the inspected game root.
Supplied DLL and provenance inputs are likewise opened through a no-follow
component chain and read from stable regular-file descriptors.

On the supported macOS platform, absent destinations are installed with
descriptor-relative `renameatx_np(RENAME_EXCL | RENAME_NOFOLLOW_ANY)`.
Existing active/manifest files are replaced with
`renameatx_np(RENAME_SWAP | RENAME_NOFOLLOW_ANY)`; the displaced inode is then
validated against the preflight snapshot from the private staging directory.
An unexpected displaced inode is atomically swapped back and the transaction
fails, so a concurrent leaf substitution is neither overwritten nor adopted.

The command stages same-filesystem temporary files, then atomically installs:

- the official backup at
  `BepInEx/.ssr-oracle-backup/BepInEx.Preloader.dll`;
- canonical deployment provenance at
  `BepInEx/.ssr-oracle-compat/preloader-provenance.json`; and
- the patched DLL at `BepInEx/core/BepInEx.Preloader.dll`.

It updates the existing install manifest last. The updated manifest owns the
backup and provenance directories/files and records the patched preloader hash
in place of the official hash. On any failure, rollback restores the exact
pre-call bytes and modes of the preloader and manifest and moves any
newly-created compatibility artifacts into a timestamped directory below
`.ssr-oracle-recovery/`; it does not delete them or touch unrelated paths.
Recovery directories use the UTC timestamp plus a cryptographically random
128-bit suffix and are created with an exclusive operation, so retries cannot
collide.

The deploy transaction performs no terminal `unlink` or `rmdir`. macOS has no
atomic unlink-by-verified-inode primitive, so even a quarantined name retains a
post-verification substitution window. All verified transaction-owned staging,
temporary, quarantine, and empty-directory leftovers are instead moved
atomically and exclusively into the transaction's private recovery directory
and preserved for audit on success or failure.

Deployment is idempotent only when the currently deployed DLL, backup,
provenance, and manifest are all healthy and byte-identical to the request. A
different patch or build must first be restored to official state; in-place
compatibility upgrades are refused.

## Restore Contract

The reverse command is:

```text
oracle_install.py restore-preloader --game-root <game-root>
```

It requires:

- the expected game and archive hashes;
- a compatibility-aware, internally consistent manifest;
- a current preloader matching the patched hash in provenance and manifest;
- a backup matching both the official hash in provenance and the pinned
  official hash; and
- provenance whose patch and toolchain-lock hashes match the committed inputs.

Restore is transactional but is not described as globally atomic. After
snapshotting the live preloader, backup, provenance, their modes, both owned
live-directory identities, and the manifest, it fully allocates and pins by
descriptor one exclusive recovery run before the first live-state mutation:

```text
.ssr-oracle-recovery/<timestamp>-<128-bit-random>/
  compat/BepInEx/.ssr-oracle-backup/
  compat/BepInEx/.ssr-oracle-compat/
  cleanup/
```

Creation of this recovery scaffolding is itself preparatory filesystem
mutation. A partially allocated run is retained if allocation or durability
fails; restore does not mutate the active preloader, manifest, backup,
provenance, or live compatibility directories until the complete run,
`compat`, and `cleanup` graph has been opened with
`O_DIRECTORY | O_NOFOLLOW`, identity-pinned, and parent-fsynced.

There is exactly one retryable destination collision: before any live-state
mutation, publishing the top-level random recovery-run name below the pinned
`.ssr-oracle-recovery` parent with
`renameatx_np(RENAME_EXCL | RENAME_NOFOLLOW_ANY)` may return `EEXIST`. The
command abandons that candidate name and retries with a fresh independent
128-bit random suffix. No child of the selected run may already exist. Once a
run name has been published, every destination collision during allocation,
forward mutation, cleanup preservation, or rollback is a hard failure that
preserves both distinguishable objects. Errors other than `EEXIST` from the
top-level run-name publication are never retried.

The forward transaction then uses this exact order:

1. move the backup and provenance to their required-absent recovery
   destinations with descriptor-relative
   `renameatx_np(RENAME_EXCL | RENAME_NOFOLLOW_ANY)`, reopen the moved leaves,
   and validate them against the preflight snapshots;
2. replace the active preloader with validated official bytes staged on the
   same filesystem using
   `renameatx_np(RENAME_SWAP | RENAME_NOFOLLOW_ANY)`, validate the displaced
   patched inode in private staging, and immediately swap back and fail if the
   displaced inode is not the preflight snapshot;
3. install one final manifest containing the official preloader hash and no
   compatibility entries using the same swap, displaced-inode validation, and
   swap-back protocol; and
4. after verifying that each pinned live compatibility directory is the exact
   expected empty directory, move it atomically and exclusively into the
   retained `cleanup/` directory. The transaction never calls `rmdir`.

Every successful move or swap fsyncs both affected parent directories before
the next state transition. If a source changes during an exclusive move, the
command moves it back only to its required-absent original name; a collision is
a hard failure and neither object is overwritten. Every transaction-owned
staging file, swap-displaced file, temporary file, quarantine entry, and empty
directory is moved atomically and exclusively into `cleanup/` and retained for
audit. Restore performs no terminal `unlink` or `rmdir` on success, rollback,
or error cleanup.

Until step 3 completes, status is allowed to report `invalid`; no intermediate
manifest is written. Rollback reverses only completed transitions in this
order: move the exact pinned empty live directories back from `cleanup/` with
exclusive required-absent renames; restore the patched active preloader with a
validated swap; restore backup and provenance from recovery with exclusive
required-absent renames; then restore the patched manifest last with a
validated swap. Each rollback source is checked against its retained snapshot.
Any source substitution, destination collision, unexpected displaced inode, or
fsync failure is a hard rollback failure: preserve all distinguishable copies
and report their recovery location rather than overwrite, delete, or silently
adopt one. The sole top-level pre-mutation run-name `EEXIST` retry described
above is not a rollback collision and is the only exception.

Failure injection covers every forward and rollback write, file fsync,
directory fsync, exclusive move, swap, displaced-inode validation, swap-back,
recovery allocation, and cleanup-preservation boundary. Race tests substitute
each mutable parent, source leaf, destination leaf, active/manifest leaf, and
empty live directory before its descriptor-relative operation.

The restore transaction is implemented only by direct calls among
module-level local functions. Transaction mutation does not use class or
instance methods, local callable aliases, callbacks, `functools.partial`,
`getattr`/`globals` lookup, or other dynamic dispatch. A conservative AST audit
starts at `restore_preloader`, traverses every directly called module-level
local helper, rejects any local function reference that is not the direct
callee of a call, and fails closed on an unresolved or indirect call edge in
transaction logic. It rejects terminal deletion calls in the complete
reachable graph. Independently, runtime tests replace the `os`, `pathlib`, and
`shutil` terminal-deletion primitives with raising spies while exercising
restore success and every forward failure, rollback failure, fsync failure,
destination collision, and substitution case; all spies must record zero
calls. An external crash may leave the deliberately fail-closed `invalid` state
with all copies preserved; status reports stable recovery guidance and no
command claims success.

The command verifies the restored DLL hash, mode, manifest health, absence of
live compatibility entries, and retained recovery contents before reporting
success. If validation or any mutation fails, it returns to the complete
patched state or reports a hard failure with all surviving states preserved for
manual recovery. It never silently chooses one of two inconsistent copies.

## Status Model

`status` remains read-only and retains its existing `healthy`, `missing`, and
`changed` fields. It adds a `preloader_compatibility` object:

```json
{
  "state": "official | patched | invalid",
  "official_sha256": "<pinned hash>",
  "active_sha256": "<observed hash or null>",
  "patched_sha256": "<provenance hash or null>",
  "issues": ["<stable machine-readable issue code>"]
}
```

- `official` means the active DLL has the pinned official hash, no live
  compatibility manifest entries exist, and both reserved live paths
  `BepInEx/.ssr-oracle-backup` and `BepInEx/.ssr-oracle-compat` are absent
  without following symlinks.
- `patched` means the active, backup, provenance, committed-input hashes, and
  manifest entries agree, and the provenance plus active bytes equal the
  reviewed Task 4 patched-preloader hash.
- `invalid` covers every other state and makes overall `healthy` false.

Status never repairs a state, trusts provenance without hashing its referenced
files, or follows symlinks. Human-facing detail may be printed separately, but
tests depend only on stable issue codes.

## Controlled Boot and Evidence

The compatibility layer is accepted only through a controlled oracle-mode boot:

1. confirm oracle config mode is `off`;
2. record the game assembly hash, active preloader hash, installer status, and
   current app-bundle signature result;
3. enable the narrow boot-probe configuration and launch the exact known game
   process;
4. wait for bounded log markers showing BepInEx 5.4.23.5, Unity 2018.4.25f1,
   and the SSR oracle plugin load marker;
5. terminate only the process started by the probe, return mode to `off`, and
   re-run all preflight checks.

Success requires all three markers and no preloader exception. A timeout,
unexpected process exit, version mismatch, or missing marker is a failure.
Before launch, the probe records the resolved path, file type, inode, size,
mtime, and SHA-256 of every existing `preloader_*.log`. After shutdown it moves
only new regular, non-symlink log paths created during the probe into a new
ignored `data/oracle/boot-probe/<timestamp>-<128-bit-random>/` evidence
directory, on success or failure. A pre-existing log is never moved or
overwritten. If one changes, the probe copies its post-launch bytes to evidence,
leaves the original in place, and fails because attribution is ambiguous. Logs
are never deleted. The game assembly hash must remain unchanged. The app-bundle
signature may retain only the already-recorded
`Foregroundr.bundle` failure; any new difference fails the probe.

The current `libc.so.6` boot is the end-to-end RED result. GREEN is not claimed
merely because the patched DLL builds or BepInEx proceeds farther.

## Test Strategy

Unit and integration tests use temporary fake game roots and local source
fixtures; they require no Steam install and no network.

Required tests cover:

- rejection of wrong, dirty, detached-at-wrong-commit, already-patched, and
  unexpected source trees;
- exact one-file/one-hunk patch validation;
- dirty/untracked trust inputs, mismatched trust hashes, incomplete or
  mismatched toolchain locks, local-feed packages, and dependency graphs;
- two-build byte equality, metadata checks, and rejection of non-legacy
  framework output;
- canonical provenance parsing, exact-key validation, hash validation, unknown
  schema rejection, and malicious path-like values;
- deploy preconditions, symlink/path traversal defense, idempotence, manifest
  ownership, mode preservation, and refusal of unmanaged or changed files;
- failure injection at every staged replacement and manifest write, proving
  exact rollback and recovery preservation;
- restore hash checks, exact official-byte restoration, descriptor-pinned
  recovery allocation, exclusive recovery/cleanup movement, validated
  active/manifest swaps, repeat-call behavior, rollback to the patched state,
  collision/substitution preservation, and a zero-terminal-deletion audit;
- all three status states, unmanaged reserved-path file/directory/symlink
  variants, and stable issue codes; and
- boot-probe marker parsing, timeout cleanup, mode reset, exact-process
  termination, pre-launch log baselines, and evidence movement.

The focused compatibility and installer tests run first. The complete Python
suite and the SSR plugin's legacy-runtime build/harness must then pass. The
controlled real-game boot is the final, explicitly operator-approved
integration check.

## Security, Licensing, and Auditability

The repository redistributes only the small textual patch and build metadata,
not upstream source or binaries. The README will identify the upstream BepInEx
license and source commit and require the operator to obtain source through the
upstream project. Generated material remains ignored.

No tool accepts a game root, source root, output root, or recovery target
through an unresolved environment variable. Every mutable path is resolved,
checked against its intended root, and rejected if it is a symlink or has an
unsafe parent. JSON inputs use exact schemas, bounded strings, lowercase
SHA-256 values, and no executable commands. Build commands are fixed by the
committed lock, not supplied through provenance.

## Upstream Replacement

There is no automatic compatibility upgrade. If an official BepInEx release
fixes legacy macOS detection, the patched preloader is first restored and
verified byte-for-byte. A separate change may then pin and test the new
official archive through the normal installer workflow. The compatibility
patch and builder remain historical audit material until that migration has
passed the same controlled boot criteria.

## Acceptance Criteria

The compatibility layer is complete only when:

1. the exact pinned source builds twice to a byte-identical, metadata-compatible
   preloader using the committed lock and patch;
2. no upstream source or generated binary is tracked by Git;
3. deploy, status, rollback, and restore tests prove exact byte and mode
   preservation under injected failures, concurrent substitutions, and
   destination collisions, and prove that deploy- and restore-reachable paths
   perform no terminal deletion;
4. the official preloader can be restored and reported as healthy with no live
   compatibility entries;
5. a patched controlled boot reaches the exact BepInEx, Unity, and SSR oracle
   plugin markers without the `libc.so.6` failure;
6. all generated logs are preserved outside the game directory;
7. `Sausage.app` and the game assembly remain unchanged; and
8. the focused tests, full Python suite, and legacy plugin build/harness all
   pass.
