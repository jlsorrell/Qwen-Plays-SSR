# SSR Oracle Practical Threat Model Design

**Date:** 2026-07-29

**Status:** Approved direction; written design pending final user review

## Context

The controlled Stephen's Sausage Roll boot probe has accumulated extensive
defenses against filesystem and process races. Final review showed that
incremental hardening could continue indefinitely if the probe is expected to
withstand an active local adversary that rewrites trusted game paths or forces
process-identifier reuse during a run.

That is not the operating environment for this research project. The probe
runs locally, under the researcher's account, against a known Steam
installation. Its purpose is to make real-game observations reproducible and
reversible, not to create a security boundary against another malicious local
process.

This addendum narrows the threat model while retaining protections that matter
for safe research operation.

## Goals

1. Fail closed when ordinary files, hashes, signatures, configuration, log
   inventories, or expected process outcomes do not match.
2. Avoid indefinite blocking on special files and bound game-process cleanup.
3. Restore the exact original configuration bytes and mode after every normal
   exception path that the probe can catch.
4. Preserve collected logs and publish canonical success evidence only after
   the exact evidence directory and final log contents have been validated.
5. Keep deployment and boot probing reversible and leave `Sausage.app`, its
   assembly, ordinary saves, and the Steam launcher unchanged.
6. Reach a controlled real-game boot on macOS Tahoe 26.6 without expanding the
   harness into a privileged or adversary-resistant launcher.

## Assumptions

- No hostile process concurrently rewrites the Steam game directory, oracle
  evidence directory, launcher, configuration hierarchy, or repository while
  a probe is running.
- The operating system and the current user account are trusted.
- Ordinary accidental changes remain possible: Steam may update files between
  runs, a prior run may leave unexpected artifacts, a path may already be a
  symlink or special file, a child process may hang, and I/O operations may
  fail.
- A single asynchronous interruption can occur. Repeated uncatchable
  interruption or forced process-identifier reuse is outside the guarantee.

## In-Scope Safety Contract

### Preflight and file access

- Validate the known game assembly, BepInEx state, preloader hash, launcher,
  configuration, and app signature before launch.
- Open files without following symlinks.
- Add `O_NONBLOCK` before determining whether a reopened source or hash target
  is a regular file, so an accidental FIFO substitution cannot hang the probe.
- Reject changed identities, wrong types, unexpected hashes, or unsafe paths.

### Configuration restoration

- Retain the opened configuration descriptor across the run.
- Restore and verify the retained file's original bytes and mode before
  reporting a public-path identity change.
- Never write through a replacement public path.
- Preserve the primary probe error when restoration or cleanup also fails.

### Log and evidence integrity

- Bind the final marker/error decision to the exact log bytes preserved as
  evidence, rather than to an earlier scan that can become stale.
- Recheck the monitored log inventory at the collection boundary and fail if
  an accidental addition, removal, or content change is observed.
- Retain the allocated evidence-directory identity through final
  `probe.json` publication.
- Revalidate the collected evidence immediately before publication.
- Fsync retained collected log files and the relevant directories before
  publishing durable success evidence.
- On any detected publication or reconciliation failure, move a canonical
  `probe.json` to private mode-`0600` storage when it is reachable through the
  retained directory, and never intentionally leave canonical success-looking
  JSON behind.

### Process control

- Launch with an argument vector and `shell=False`.
- Start a distinct process group/session and never search by process name.
- Bound TERM grace and KILL escalation to the numeric group created for the
  launched probe.
- Attempt cleanup after a caught interruption and report cleanup uncertainty.

### Public interfaces and CLI

- `LogFingerprint` includes `file_type`, because the lstat type is part of the
  safety contract.
- `run_boot_probe` accepts the documented keyword names `launcher` and
  `config`, while retaining positional compatibility.
- `collect_boot_evidence` remains a public three-argument function.
- The thin executable wrapper propagates `main()`'s process exit status.
- Relative evidence-root arguments resolve against the caller's working
  directory, matching the documented Task 9 command.

## Explicit Non-Goals

The probe does not promise to withstand:

- replacement of a verified launcher, working directory, configuration
  hierarchy, or evidence leaf by a malicious process in the final syscall
  window;
- deliberate PID/PGID churn intended to make the kernel reuse a numeric process
  group identifier during cleanup;
- repeated asynchronous `BaseException` injection that prevents cleanup code
  from running;
- adversarial same-context reentrant calls into private collection state;
- arbitrary power loss at every individual filesystem instruction; or
- use as a privilege boundary or multi-user hostile service.

Supporting those guarantees would require a different architecture: a
long-lived supervisor, stable kernel process handles unavailable through the
current portable Python interface, and descriptor-native execution/publication
throughout. That redesign is intentionally deferred.

## Implementation Shape

The existing module remains the implementation boundary. The bounded repair
will:

1. add focused regressions for the in-scope failures reproduced by final
   review;
2. fix nonblocking regular-file acquisition and retained-descriptor
   configuration restoration;
3. carry the evidence-directory handle and exact final evidence inventory
   through publication;
4. make the final marker/error decision from the preserved evidence;
5. reconcile canonical JSON on reachable failure paths;
6. align the public keyword names and strengthen CLI/wrapper tests; and
7. remove only dead logic encountered directly in those paths.

It will not add a supervisor process, execute the launcher through a shell, or
attempt to close the explicit active-adversary gaps.

## Verification

Before Task 8 is committed:

- every new behavioral regression must be observed RED against the frozen
  current source;
- all focused regressions and the complete `tests/test_oracle_boot.py` file
  must pass;
- the full Python repository suite must pass with only its existing expected
  failures;
- compilation, whitespace, scope, and artifact-hash checks must be clean;
- a final reviewer must evaluate the implementation against this practical
  threat model rather than the rejected active-adversary model; and
- no installed-game mutation or launch may occur.

Task 9 will then rebuild the pinned local artifacts, run read-only preflight,
request separate installed-game mutation approval, and perform the controlled
Tahoe 26.6 boot.
