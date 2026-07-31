# SSR Oracle Canonical Boot Log Observer Correction

**Date:** 2026-07-30

**Status:** Approved; implementation and review pending

## Context

Exactly one approval-gated initial Tahoe 26.6 boot used the reviewed patched
BepInEx preloader, rebuilt SSR oracle plugin, and `Mode = off` configuration.
The automated probe timed out after 120 seconds and reported no boot markers.
Its failure evidence is retained below:

```text
data/oracle/boot-probe/
  20260730T200305.402992Z-e06acd9ac663f5472416663ffc82e38a/
    probe.json
```

The installed game was then returned transactionally to healthy `official`
preloader state. The game assembly, oracle configuration, and rebuilt plugin
retained their reviewed hashes. No corrected second launch or re-deploy
occurred.

Read-only investigation demonstrated that the runtime boot itself succeeded.
`BepInEx/LogOutput.log`, created during the approved launch, records:

```text
BepInEx 5.4.23.5
System platform: Bits64, MacOS
Preloader finished
Detected Unity version: v2018.4.25f1
Chainloader started
Loading [SSR Executable Oracle 0.1.0]
SSR oracle boot probe loaded
Chainloader startup complete
```

Unity's `Player.log` independently records the same startup sequence. Neither
log contains `DllNotFoundException` or `Preloader error`. Byte-for-byte
forensic copies are retained in the ignored directory:

```text
data/oracle/boot-probe-forensics/
  20260730T200305.402992Z-e06acd9ac663f5472416663ffc82e38a/
    BepInEx-LogOutput.log
    Unity-Player.log
```

The false negative has two confirmed causes:

1. the probe monitors only recursively discovered `preloader_*.log` files;
2. the probe requires the literal `Unity v2018.4.25f1`, which authentic
   BepInEx 5.4.23.5 never writes in its successful disk log.

The pinned BepInEx source explains the mismatch. Successful chainloader
initialization creates `BepInEx/LogOutput.log`. A `preloader_<timestamp>.log`
is a silent exception artifact written by the preloader catch paths. The
probe therefore watched the failure-only log family for success markers.

The original executable-oracle plan correctly identified
`BepInEx/LogOutput.log` as the expected evidence. The later compatibility
design narrowed collection to `preloader_*.log`, and the tests encoded that
drift by placing synthetic success text in `preloader_probe.log`.

## Goals

1. Observe the exact successful disk log produced by the pinned BepInEx
   5.4.23.5 runtime.
2. Retain `preloader_*.log` monitoring as failure evidence.
3. Match the authentic, exact BepInEx Unity-version line without accepting
   extended or lookalike versions.
4. Prevent stale markers in an append-mode or unchanged log from producing a
   false success.
5. Bind the final decision to the exact canonical log bytes preserved in the
   durable evidence transaction.
6. Preserve the existing practical threat model, descriptor-lifecycle
   guarantees, process-group cleanup, exact oracle-config restoration, and
   public API compatibility.
7. Complete all implementation and review offline before requesting separate
   approval for another installed-game mutation or launch.

## Non-Goals

- Capturing or interpreting the launcher's inherited stdout and stderr.
- Reading the user-global Unity `Player.log` as acceptance evidence.
- Changing the patched preloader, SSR plugin, Doorstop wrapper, game assembly,
  app bundle, Steam launcher, or ordinary saves.
- Generalizing the probe into a logging framework for arbitrary Unity games or
  BepInEx versions.
- Accepting a noncanonical BepInEx fallback log as successful evidence.
- Defending against a hostile same-user process concurrently rewriting trusted
  game paths; the approved practical threat model still applies.
- Launching the game during implementation, testing, or code review.

Launcher stream capture remains a useful separate hardening task. It requires
new bounded-drain, interruption, descriptor-ownership, evidence-schema, and
publication behavior and will not be bundled into this correction.

## Authoritative Pinned Runtime Behavior

The correction is specific to the already-pinned BepInEx source commit
`57f1fb859bd4d0264cd2a59074d0e96c6a492a33`.

`BepInEx/Bootstrap/Chainloader.cs` constructs:

```text
DiskLogListener("LogOutput.log", ...)
```

`BepInEx/Logging/DiskLogListener.cs` opens that path beneath the BepInEx root
using:

```text
FileMode.Append  when Logging.Disk.AppendLog = true
FileMode.Create  when Logging.Disk.AppendLog = false
```

The pinned defaults are:

```ini
[Logging.Disk]
AppendLog = false
Enabled = true
LogLevels = Fatal, Error, Warning, Message, Info
```

If the canonical path cannot be opened, the runtime attempts
`LogOutput.log.1` through `LogOutput.log.4`. Those fallbacks are useful
diagnostic evidence but indicate that the reviewed canonical logging contract
was not met.

The preloader writes `preloader_<timestamp>.log` only from caught startup
exception paths. A stable scan that observes a new or changed member of that
family therefore establishes a boot failure even when its exception text is
not one of the probe's previously enumerated error substrings.

## Monitored Log Set

The recursive no-follow scanner will classify only these exact families:

1. canonical success log:
   `BepInEx/LogOutput.log`;
2. canonical fallback logs:
   `BepInEx/LogOutput.log.1` through
   `BepInEx/LogOutput.log.4`;
3. failure logs:
   any basename matching the existing case-sensitive
   `preloader_*.log` rule within the game root.

No other `*.log` path is included. In particular, the probe does not scan
outside the game root or consume `~/Library/Logs/Unity/Player.log`.

The existing public names
`fingerprint_preloader_logs(...)` and
`collect_boot_evidence(...)` remain unchanged for compatibility. Internally
and in new documentation, their inputs are described as monitored boot logs.
`LogFingerprint` retains its existing public fields and JSON representation.
Log kind is derived from the validated game-relative path rather than added to
the public record.

Every classified path remains subject to the current rules:

- every path component is inspected without following symlinks;
- regular files are opened with `O_NOFOLLOW | O_NONBLOCK`;
- special files and unsafe identities fail closed;
- monitored payloads remain bounded by the existing byte limit;
- fingerprints bind path, type, inode, size, nanosecond mtime, and SHA-256.

## BepInEx Disk-Logging Preflight

Before launch, the probe will validate the effective disk-logging contract.

If `BepInEx/config/BepInEx.cfg` is absent, the pinned source defaults above are
accepted. If it exists, it must be an ordinary non-symlink file whose relevant
configuration is unambiguous:

- exactly one `[Logging.Disk]` section;
- exactly one `Enabled` entry with value `true`;
- exactly one `AppendLog` entry with value `false`;
- exactly one `LogLevels` entry containing at least `Fatal`, `Error`,
  `Warning`, `Message`, and `Info`.

The section and key spellings are the exact case-sensitive names used by the
pinned BepInEx `ConfigDefinition` objects. Boolean values and `LogLevel`
members may use the case-insensitive value syntax accepted by BepInEx.
Duplicate sections, duplicate relevant keys, malformed values, missing
required levels, or an unsafe path are rejection conditions.

The probe intentionally accepts a deterministic subset of BepInEx's broader
configuration grammar:

- strict UTF-8 with an optional UTF-8 BOM and LF or CRLF line endings;
- blank lines and trimmed full-line `#` comments;
- the exact case-sensitive section and key names above;
- boolean values spelled `true` or `false`, compared case-insensitively;
- `LogLevels` as a comma-separated, case-insensitive list of unique symbolic
  members from `Fatal`, `Error`, `Warning`, `Message`, `Info`, and `Debug`, or
  the single value `All`;
- leading or trailing whitespace outside a complete section line, plus
  whitespace around keys, values, and commas as accepted by the pinned parser.

The text inside the section brackets remains exactly `Logging.Disk`; internal
section-name whitespace is not accepted.

Numeric enum values, unknown members or bits, `None`, `All` combined with
another member, inline comments, NUL bytes, invalid UTF-8, duplicate symbolic
members, and case-fold lookalikes of the relevant section or keys are
rejected. Unrelated well-formed sections and keys are ignored. This narrower
grammar is fail-closed and covers the file generated by the pinned runtime.

Requiring the full pinned default visibility set prevents a configuration
from retaining the three success checkpoints while suppressing fatal, error,
or warning diagnostics. `Debug` is optional, and the single value `All`
satisfies the requirement.

The probe never edits `BepInEx.cfg`. A pre-existing accepted file is
fingerprinted and rechecked immediately before launch. Under the practical
threat model no other local process changes it during the run.

The `AppendLog = false` gate is essential. It ties a changed canonical log to
the current launch because the pinned runtime opens it with `FileMode.Create`,
which truncates or creates the file rather than retaining prior marker bytes.

## Marker and Error Contract

Successful evidence must contain all three authentic checkpoints in the same
canonical `BepInEx/LogOutput.log` payload:

```text
BepInEx 5.4.23.5
Detected Unity version: v2018.4.25f1
SSR oracle boot probe loaded
```

The version matchers keep the existing token-boundary protection. They reject
prefixes, suffixes, and extended versions such as `5.4.23.50`,
`v2018.4.25f10`, or an added alphanumeric version token.

`Running under Unity vUnknown (post-2017)` does not satisfy the Unity marker.
Only the later detected-version line does.

Success markers may not be assembled across unrelated files. All three must
come from the exact canonical success log. Error literals are evaluated across
the canonical log, fallback logs, and preloader exception logs.

The public marker values do not change:

```text
BepInEx 5.4.23.5
Unity v2018.4.25f1
SSR oracle boot probe loaded
```

`BootProbeResult.markers`, the CLI JSON, and `probe.json.markers` continue to
return those schema-v1 semantic identifiers. An internal exact-pattern mapping
matches the public Unity identifier only against the authentic source line
`Detected Unity version: v2018.4.25f1`. The other two identifiers already
match their authentic log substrings. This separates stable output semantics
from the pinned runtime's presentation without a public API or schema change.

The following conditions fail even if the canonical log contains all three
success markers:

- a new or changed `preloader_*.log`;
- a new or changed `LogOutput.log.1` through `LogOutput.log.4`;
- any existing configured boot-error literal;
- an unsafe monitored path or unstable read;
- a logging-contract mismatch;
- a missing, unchanged, or unpreserved canonical log;
- any existing preflight, cleanup, evidence, signature, hash, or config
  restoration issue.

Requiring `Chainloader startup complete` is intentionally deferred. The exact
oracle plugin marker already proves that the requested plugin was constructed
and executed, and adding a fourth public marker is not necessary to repair the
confirmed observer defects.

## Baseline, Live Monitoring, and Attribution

The boot sequence becomes:

1. validate request paths and open the exact oracle-config guard;
2. validate the BepInEx disk-logging contract;
3. take a preliminary safety fingerprint of the complete monitored boot-log
   set;
4. run the existing installer, assembly, preloader, signature, launcher, and
   oracle-config preflight;
5. recheck the logging contract and launcher/config guards;
6. immediately before `Popen`, fingerprint the complete monitored set again,
   fail without launching if it differs from the preliminary inventory, and
   use this second snapshot as the authoritative run baseline;
7. launch the exact wrapper in its dedicated process session;
8. poll the canonical success log and failure families until:
   - all authentic canonical markers appear,
   - a failure condition appears,
   - the child exits unexpectedly, or
   - the bounded timeout expires;
9. terminate only the launched process group through the existing cleanup
   state machine;
10. take the final monitored-log inventory and collect exact evidence;
11. derive the final markers and errors from the retained evidence bytes;
12. run postflight, restore the exact oracle configuration, fsync evidence,
    and publish `probe.json` through the existing exclusive transaction.

The practical model excludes a writer racing the final baseline syscall and
`Popen`. An ordinary change during the longer preflight interval is detected
by the required two-snapshot reconciliation and cannot become current-run
marker evidence.

An absent baseline canonical log that appears during launch is a new log. It
is moved into the evidence directory under its game-relative
`BepInEx/LogOutput.log` path.

A pre-existing canonical log is expected to change under the validated
overwrite-mode contract. It is copied into evidence and left in the installed
game. Unlike a changed generic preloader log, that exact canonical change does
not add an ambiguity issue. Its complete post-launch bytes are current-run
bytes because append mode was rejected before launch.

An unchanged pre-existing canonical log cannot satisfy the current run. It is
not treated as marker evidence and produces a missing-current-log failure.

Existing preloader-log behavior remains conservative:

- new regular failure logs are moved to evidence;
- changed pre-existing failure logs are copied, left installed, and reported
  as failures;
- unchanged pre-existing failure logs are baseline history and do not affect
  the new run;
- missing or unsafe pre-existing members are failures.

The live monitor retains an internal record of every new or changed
preloader/fallback path observed by a stable scan. Such an observation can
trigger cleanup promptly, but collection must still preserve the final exact
file before its contents are graded. If an observed failure path disappears,
is replaced, becomes unsafe, or cannot be retained, the probe records an
`observed failure log could not be preserved` evidence-integrity issue and
cannot succeed. It does not silently discard the live observation or invent
content that was not preserved.

## Evidence and Schema

The retained-evidence transaction remains the authority for success.
Monitoring can stop the process promptly, but an earlier live scan never
substitutes unretained bytes for the final content decision. Success markers
and error literals come from preserved bytes. The inability to preserve a
stably observed failure artifact is separately an evidence-integrity failure.

The canonical log uses the same retained descriptor, inventory revalidation,
byte revalidation, file fsync, directory fsync, and exclusive publication
machinery as preloader logs. `probe.json` remains schema version 1 because its
generic `before_logs`, `after_logs`, `moved_logs`, and `copied_logs` fields can
already represent the canonical path without changing their shape. The
existing `issues` array can represent an unpreservable observed-failure
artifact without adding a field.

Issue wording and internal helper names may be generalized from "preloader
log" to "monitored boot log" where needed for accuracy. Public function
signatures do not change.

The existing failed `probe.json` is not rewritten. The separately preserved
forensic copies remain diagnostic evidence and are not retroactively inserted
into the probe-owned evidence directory.

## Failure Handling

All existing failure ordering remains in force:

- no launch after a preflight or logging-contract rejection;
- process cleanup precedes evidence finalization;
- exact oracle-config restoration precedes canonical success publication;
- a later cleanup or restoration problem is attached without hiding the
  primary error;
- publication failure cannot leave success-looking canonical JSON;
- recovery and evidence files are retained rather than manually deleted.

If the canonical log cannot be opened and BepInEx selects a numbered fallback,
the probe retains that fallback and fails with a specific noncanonical-log
issue. It does not silently broaden acceptance.

## Test-Driven Implementation

Before production changes, freeze the current package source used by the
tests and record its exact SHA-256. New behavioral tests must be observed RED
against that frozen source for the intended reason.

Focused regressions will cover:

1. an authentic new `BepInEx/LogOutput.log` fixture with all real lines is
   currently invisible and becomes successful;
2. the authentic Unity source line produces the unchanged public
   `Unity v2018.4.25f1` marker, while a payload containing only the invented
   old literal and any extended version are rejected;
3. all success markers must come from the canonical log;
4. a pre-existing canonical log under validated overwrite mode is copied,
   preserved in place, and can produce success without an ambiguity issue;
5. `AppendLog = true` is rejected before launch, including when a stale
   canonical log already contains every marker;
6. disabled disk logging, missing required log levels, duplicate relevant
   sections/keys, malformed values, and unsafe config paths fail before
   launch, including rejection of `Message, Info` without the full pinned
   default visibility set;
7. absent `BepInEx.cfg` uses the pinned defaults;
8. an initially accepted config that changes or is replaced before `Popen`,
   including a change to `AppendLog = true`, fails without launch; an
   initially absent config that appears invalid before `Popen` does the same;
9. new and changed preloader exception logs always fail, are retained when
   preservable, and otherwise produce an evidence-integrity failure;
10. numbered fallback logs are retained but never accepted as canonical
   success;
11. a stably observed failure/fallback log that disappears or is replaced
    before collection fails as unpreservable evidence;
12. a canonical log changed during preflight is rejected by the immediate
    pre-`Popen` baseline reconciliation;
13. symlink, FIFO, oversized, unstable, added, missing, and substituted
    canonical/fallback paths retain the existing nonblocking fail-closed
    behavior;
14. final grading uses exact preserved canonical bytes, including errors
    appended during shutdown;
15. the existing recursive preloader-log, process-group, oracle-config,
    evidence-publication, CLI, and JSON-schema tests remain green.

The realistic fixture will be derived from the 17-line successful
`LogOutput.log` while avoiding machine-local absolute paths. It will include
the exact pinned versions and plugin marker.

Verification requires:

- the new focused regressions;
- the complete `tests/test_oracle_boot.py` module;
- the focused oracle install/compatibility cohort;
- the complete Python repository suite with only documented expected
  failures;
- Python compilation, whitespace, scope, and artifact-hash checks;
- an independent specification review and code-quality review;
- no installed-game mutation or launch.

## Files in Scope

Expected implementation scope:

- `src/ssr_env/oracle_boot.py`;
- `tests/test_oracle_boot.py`;
- optionally one small test fixture below `tests/fixtures/oracle_boot/`;
- `oracle/README.md`;
- the executable-oracle plan only where its observed Task 2 result and
  corrected marker/path contract must be recorded.

The thin CLI wrapper is expected to remain unchanged. The BepInEx compatibility
builder, installer transactions, plugin, simulator, and model-training code
are outside this correction.

## Rollout

Implementation and review are offline. They do not mutate or launch the
installed game.

After every offline gate passes:

1. run a new read-only installed-state preflight;
2. present the exact planned mutation and one-launch sequence;
3. request separate approval for a second controlled launch;
4. deploy the already-reviewed plugin/config and patched preloader only through
   the installer;
5. run exactly one corrected bounded probe;
6. restore the official preloader and verify its exact hash;
7. if the corrected probe succeeded, redeploy the identical patched pair and
   repeat only the no-launch idempotence deployment;
8. leave the oracle configuration at `Mode = off` and record final hashes,
   status, signature identity, evidence paths, and recovery paths.

No approval from the first launch is reused for the second.

## Acceptance Criteria

The correction is ready for a new launch request only when:

- authentic successful BepInEx output is recognized from the canonical path;
- stale or appended output cannot satisfy the probe;
- authentic exact versions are required;
- failure and fallback log families remain fail-closed and retained;
- the final result is derived from durable canonical evidence;
- all offline verification and independent reviews pass;
- the installed game remains healthy `official`; and
- no second launch has occurred.

The end-to-end checkpoint is complete only after a separately approved
corrected probe succeeds, the official restore is verified, the identical
patched re-deploy is idempotent without another launch, and final documentation
records both the observer false negative and the successful corrected run.

## Alternatives Considered

### Expand only the filename matcher

Adding `LogOutput.log` and changing one marker is smaller, but it can accept
stale markers when append logging is enabled. It also leaves success markers
combinable across failure logs. This is rejected.

### Use Unity's global `Player.log`

The file corroborated this launch, but it is outside the game root, shared with
other Unity applications, overwritten globally, and not covered by the
probe's containment transaction. It remains forensic corroboration only.

### Capture launcher stdout and stderr now

This would preserve the noisy legacy-Mono fallback trace and improve future
diagnosis. A safe implementation needs bounded concurrent draining, explicit
descriptor ownership, interruption cleanup, evidence-schema changes, and
publication tests. Bundling it would enlarge the confirmed two-defect repair
into a process-observation redesign. It is deferred as a separate task.
