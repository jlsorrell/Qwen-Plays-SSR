# Task 5 Passive Driver Verification

## Scope and lineage

Task 5 completed the Unity-free passive driver under the controlling behavioral
design and lean-execution clarification. The accepted linear lineage is:

```text
b042eaa72c1def65f1c76f6bbcf01bf2dc3c1ed2  docs: clarify lean Task 5 execution
  -> 3c3ddfc911417bf219f272ea45a057f5031af822  docs: plan lean Task 5 execution
  -> 02d19eecac2cbdd9292b1e5e35efaea4a14d0c04  feat: attribute passive input attempts
  -> 3bcab694bb41d43f55b0f3269e54dff1f13635f5  feat: balance passive lifecycle hooks
  -> 1f643e88b8e87f941a0e6dbc74c04066e6fa2979  feat: finalize passive trace capture
```

The plan commit is the sole parent of Task 5.1; each implementation commit has
the preceding listed commit as its sole parent. The accepted implementation tip
is `1f643e88b8e87f941a0e6dbc74c04066e6fa2979`. No implementation finding was
accepted after that commit, so no append-only correction commit exists.

Across the three commits, exactly nine production/test/registration paths
change: `PassiveDriver.cs`, `PassiveDriverInput.cs`,
`PassiveDriverLifecycleHooks.cs`, `PassiveDriverCompletion.cs`,
`PassiveDriverInputTests.cs`, `PassiveDriverTerminalTests.cs`,
`PassiveDriverTestSupport.cs`, `PassiveDriverTests.cs`, and `Program.cs`, all
under `oracle/plugin/`. No boundary, DTO, sink/reporter interface, project,
Unity/BepInEx, save, network, adapter, game-launch, or Task 6 operational path
changes.

## Task 5.1 RED, GREEN, reviews, and commit

The strict test-only RED used:

```text
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false
```

It exited `1` with `0` warnings and exactly `37` CS1061 errors. The unique
missing-member set was exactly `PendingInput`, `PendingAccepted`,
`PendingMovementScheduled`, `ProcessInputEntered`, `ProcessInputReturned`,
`ProcessInputThrew`, `UndoEntered`, `RestoreObserved`, `UndoReturned`, and
`UndoThrew`; there was no unrelated diagnostic.

The first precommit specification review returned `REVISE C0/I1/M0`: a Step
could become durable before the native ProcessInput/Undo outcome existed. The
quality review returned `APPROVE C0/I0/M0`. Two real-callback regressions then
withheld the native return. Their focused RED command was:

```text
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-input
```

It exited `1` for the six-test cohort with exact first failure:

```text
cohort 'driver-input', test 'accepted and refused direction outcomes': System.InvalidOperationException: direction without returned outcome Error count
```

The outcome-known guard was added at the sole Step-emission boundary; the same
command then exited `0`. The fresh matrix exited `0`: warning-free
net10/net35 builds, boundary `2`, Initial `8`, input `6`, full C# `31`, and
Python `1822 passed, 120 xfailed, 6 xpassed`. Both scoped re-reviews approved
with no open Critical/Important finding, and both immutable postcommit reviews
returned `APPROVE C0/I0/M0`.

Commit `02d19eecac2cbdd9292b1e5e35efaea4a14d0c04`, parent
`3c3ddfc911417bf219f272ea45a057f5031af822`, subject
`feat: attribute passive input attempts`, has exact five-file scope:

- modified `oracle/plugin/Core/PassiveDriver.cs`;
- added `oracle/plugin/Core/PassiveDriverInput.cs`;
- added `oracle/plugin/tests/PassiveDriverInputTests.cs`;
- modified `oracle/plugin/tests/PassiveDriverTestSupport.cs`; and
- modified `oracle/plugin/tests/Program.cs`.

## Task 5.2 RED, GREEN, reviews, and commit

The test-only forced rebuild used the same exact net10 build command above and
exited `1` with `0` warnings and exactly `79` CS1061 errors. The unique missing
set was exactly `RestartEntered`, `RestartReturned`, `RestartThrew`,
`StateSetEntered`, `StateSetReturned`, `StateSetThrew`, and `ClearThrew`; no
other diagnostic occurred.

After the lifecycle implementation, the exact offline matrix exited `0`:
warning-free net10/net35 builds, boundary `2`, Initial `8`, input `8`, full C#
`33`, and Python `1822 passed, 120 xfailed, 6 xpassed`. Both precommit reviews
and both immutable postcommit reviews returned `APPROVE C0/I0/M0`, with no
fix round or parked finding.

Commit `3bcab694bb41d43f55b0f3269e54dff1f13635f5`, parent
`02d19eecac2cbdd9292b1e5e35efaea4a14d0c04`, subject
`feat: balance passive lifecycle hooks`, has exact five-file scope:

- modified `oracle/plugin/Core/PassiveDriver.cs`;
- modified `oracle/plugin/Core/PassiveDriverInput.cs`;
- added `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs`;
- modified `oracle/plugin/tests/PassiveDriverInputTests.cs`; and
- modified `oracle/plugin/tests/Program.cs`.

## Task 5.3 three REDs, GREEN, stress, reviews, and commit

Each behavioral RED used this exact command:

```text
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-terminal
```

The ordered six-test failures, each at exit `1`, were exactly:

```text
cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: no Ready(3)
cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: Close still blocked
cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: rebased Error line
```

These respectively proved the inherited Step-2 Ready continuation, missing
serialized invalid-UTC ownership, and stale deferred attempt fields. The
production sequence then reached GREEN: warning-free net10/net35 builds,
boundary `2`, Initial `8`, input `8`, terminal `6`, full C# `39`, and Python
`1822 passed, 120 xfailed, 6 xpassed`.

The initial specification review returned `APPROVE C0/I0/M0`; quality returned
`REVISE C0/I1/M0` because Run/Initial trace-I/O failure selected ownership only
after an external Diagnostic callback could reenter Dispose. Two deterministic
regressions produced a focused RED with the same terminal command, exit `1`, and
exact first failure:

```text
cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: Run sink failure owns before Diagnostic Dispose
```

Moving trace-I/O selection before Diagnostic made the cohort GREEN. Both scoped
re-reviews approved the correction with no new Critical or Important finding;
the scoped specification re-review and both immutable postcommit reviews
explicitly returned `APPROVE C0/I0/M0`.

The corrected slice matrix exited `0` with the same `39` C#/`1822` Python
totals. Its exact common stress ran under `/bin/bash`: `20/20` terminal-cohort
runs exited `0`, each executed six tests, emitted exactly `SSR oracle unit
harness ready\n`, left stderr empty, and preserved HEAD, index, tracked diff,
untracked contents, and porcelain status.

Commit `1f643e88b8e87f941a0e6dbc74c04066e6fa2979`, parent
`3bcab694bb41d43f55b0f3269e54dff1f13635f5`, subject
`feat: finalize passive trace capture`, has exact eight-file scope:

- modified `oracle/plugin/Core/PassiveDriver.cs`;
- added `oracle/plugin/Core/PassiveDriverCompletion.cs`;
- modified `oracle/plugin/Core/PassiveDriverInput.cs`;
- modified `oracle/plugin/tests/PassiveDriverInputTests.cs`;
- added `oracle/plugin/tests/PassiveDriverTerminalTests.cs`;
- modified `oracle/plugin/tests/PassiveDriverTestSupport.cs`;
- added `oracle/plugin/tests/PassiveDriverTests.cs`; and
- modified `oracle/plugin/tests/Program.cs`.

## Final offline verification matrix

All final commands ran from exact accepted tip `1f643e8`, offline, with pinned
SDK `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet` version `10.0.300` and
`--no-restore` on every dotnet invocation.

| Check | Exact command | Exit | Total/result |
|---|---|---:|---|
| net10 rebuild | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false` | 0 | 0 warnings, 0 errors |
| boundary | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-boundary` | 0 | 2; exact stdout; empty stderr |
| Initial | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-initial` | 0 | 8; exact stdout; empty stderr |
| input | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-input` | 0 | 8; exact stdout; empty stderr |
| terminal | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-terminal` | 0 | 6; exact stdout; empty stderr |
| full C# | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build` | 0 | exactly 39 (`4+5+6+2+8+8+6`); exact stdout; empty stderr |
| net35 rebuild | `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build oracle/plugin/tests/SsrOracle.Core.Net35.csproj --configuration Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false` | 0 | 0 warnings, 0 errors |
| Python | `PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 PYTHONPATH="$PWD/src" .venv/bin/python -m pytest -q -rX` | 0 | 1822 passed, 120 xfailed, 6 xpassed in 109.90s |

The final `/bin/bash` stress repeated the exact pinned `driver-terminal` command
above 20 times: all `20` statuses were `0`, all `20` stdout files were
byte-exact, all `20` stderr files were empty, and Git state was unchanged. The
authoritative result record ended at 124 lines, SHA-256
`7df53625cbd2dfa619b1f6a2d4a3995335fd3af4a2b9af7cd9ff53cb4ae2f671`;
its original 94-line prefix remained byte-identical.

## Five targeted mutation outcomes

All corrected transactions used fresh `git clone --no-hardlinks` copies of
accepted tip `1f643e8` and the literal pinned SDK path. Clone forced rebuilds
exited `0` before each non-omitted focused failure.

| Mutation | Outcome | Cohort exit | Exact first failure/reason |
|---|---|---:|---|
| M1, corrupt exact cardinal equality | KILLED | 1 | `cohort 'driver-input', test 'all cardinals correlate': System.InvalidOperationException: cardinal opens attempt 0` |
| M2, establish Restart depth after fault | KILLED | 1 | `cohort 'driver-input', test 'restart depth and null fields': System.InvalidOperationException: Restart depth is established before Error reentry` |
| M3, release private lease before Close | OMITTED-REDUNDANT | n/a | No edit/build/cohort or kill claim: the already-selected success owner independently rejects new producer/fault/disposal ownership, and changing only the private lease flag cannot alter End/Close/Complete without a prohibited private-state seam. |
| M4, retain stale deferred attempt fields | KILLED | 1 | `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: rebased Error line` |
| M5, Complete before Close | KILLED | 1 | `cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: terminal order at index 2` |

After every transaction, the primary tree was reauthenticated and returned to
GREEN. The fresh aggregate pinned build, `driver-boundary`, `driver-input`, and
`driver-terminal` all exited `0`. Four mutants were killed by their named
oracles; M3 was explicitly omitted under the design rule; no mutant remains.

## Cross-slice reviewer verdicts and findings

Fresh independent review covered immutable range
`3c3ddfc911417bf219f272ea45a057f5031af822..1f643e88b8e87f941a0e6dbc74c04066e6fa2979`,
both controlling specifications, the frozen plan, all immutable slice reviews,
the final matrix and stress, the real NDJSON Step/Error oracle, and all five
mutation outcomes.

- Cross-slice specification: `APPROVE C0/I0/M0`; implementation findings `0`,
  report/evidence-only findings `0`, stop condition not triggered.
- Cross-slice quality: `APPROVE C0/I0/M0`; implementation findings `0`,
  report/evidence-only findings `0`.
- Task 7 superseding re-review: specification `APPROVE C0/I0/M0` and quality
  `APPROVE C0/I0/M0`; both earlier Important evidence-process findings were
  resolved by the pinned rerun and verified clone cleanup.

Every immutable per-slice postcommit specification and quality review also
approved its exact predecessor-to-commit range at `C0/I0/M0`. No Critical,
Important, Minor, accepted implementation, parked, or open finding remains.

## Preserved historical recovery artifacts

`docs/superpowers/plans/2026-08-10-task-5-bootstrap-recovery.md` remains the
single pre-existing untracked historical path outside this report. It and the
superseded recovery workflow's launch outputs, candidate bundles, audit roots,
review reports, and progress records were not edited, deleted, retried, sourced,
executed, or extended. They remain historical evidence, not execution
authority. Before this report was created, tracked and staged diffs were empty;
after creation, the only intended new tracked-deliverable candidate is this
report, alongside the preserved untracked historical plan.

## Completion assessment and deviations

Task 5 meets the approved completion criteria at accepted implementation tip
`1f643e8`: three separate reviewed TDD commits in exact order and scope; all
focused/full net10 gates and compile-only net35 GREEN; exactly 39 C# tests;
offline Python GREEN; 20/20 final stress; four targeted kills plus one justified
redundant omission; independent cross-slice approvals; no surviving mutation;
no correction commit; and no Task 6+ operational work.

Recorded deviations and diagnostic events are:

- Initial `Ready(0)` failure deliberately omits the newly planned
  `SafeDiagnostic(error)`. This preserves the immutable Task 4.2 sequence
  `Initial -> Ready(0) -> Error -> Close -> Failed`; intermediate Step Ready
  failure retains its serialized Diagnostic. Both Task 5.3 immutable reviewers
  and both cross-slice reviewers accepted the ruling. The cost is that this one
  inherited Initial reporter failure exposes only categorical
  `observer_exception`, not the reporter exception type.
- One unchanged Python FIFO-copy timing assertion failed once at `2.56s` during
  Task 5.1 correction verification. The exact case passed `5/5` focused reruns
  and a fresh full suite passed `1822`; no Python source was changed.
- The exact common stress script runs under `/bin/bash` because zsh reserves
  `status`. The first zsh attempt stopped before executing tests; the unchanged
  Bash script passed 20/20.
- Task 7's first mutation pass used mutable `/opt/homebrew/bin/dotnet` and
  retained its disposable copies. All five transactions were rerun from fresh
  no-hardlink clones with the literal pinned Cellar binary. The prior 89 result
  rows remained byte-identical, correction rows were appended, and all five old
  plus five corrected clone roots were validated, removed, and verified absent.
- Task 8's first stress launch stopped before iteration 1 because sandboxed
  `git write-tree` could not create its transient index lock. Its empty temporary
  root was removed; the same logic then passed with permission. A subsequent
  `cmp -n` prefix audit reported EOF at the old-file boundary, so the portable
  `head -c <prefix-bytes> | cmp` form proved the original 94-line prefix
  byte-identical. No source, index, or result row changed in either event.

These deviations affect evidence execution or one explicitly ruled inherited
diagnostic detail; none changes the accepted implementation result.
