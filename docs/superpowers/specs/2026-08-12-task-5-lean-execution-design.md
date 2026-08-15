# Task 5 Lean Execution Design

**Date:** 2026-08-12

**Status:** Approved section by section and as a complete design on 2026-08-12;
execution-plan consistency clarification added on 2026-08-13

## 1. Purpose

Task 5 implementation has not begun. Its behavioral design is already approved,
but the attempted bootstrap-recovery workflow grew into a byte-pinned execution
system whose structural checker consumed six one-shot launches on six different
checker defects before any implementation, build, or project test ran.

This design replaces only that execution workflow. It keeps the approved Task 5
behavior and the three-slice boundary, but executes them with ordinary reviewed
test-driven development, a small verification matrix, and five targeted mutation
checks.

The controlling behavioral specification remains
`docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md`. This document
does not change its protocol, state model, commit subjects, or out-of-scope
boundaries. Except for the narrow Task 5.3 test-ownership clarification in
section 2.1, it does not change file ownership.

## 2. Decision

Implement Task 5 as three sequential, independently reviewed TDD slices:

1. Task 5.1 — direction and Undo attribution, settled Step emission, and
   intermediate Ready reporting.
2. Task 5.2 — Restart and state-replacement lifecycle balancing.
3. Task 5.3 — terminal End, Close, and Complete behavior.

Each slice produces one reviewed implementation commit using the already
approved subject:

1. `feat: attribute passive input attempts`
2. `feat: balance passive lifecycle hooks`
3. `feat: finalize passive trace capture`

The tracked implementation plan is committed after this design and before Task
5.1. Task 5.1 is the plan commit's direct child; the three implementation
commits then remain consecutive and separately reviewed.

### 2.1 Narrow Task 5.3 test-ownership clarification

The controlling behavioral design requires Task 5.1 and Task 5.2 to prove the
checkpoint behavior `Ready(3)` after Step 2, while Task 5.3 changes that exact
continuation to terminal completion with no `Ready(3)`. To avoid retaining a
known-obsolete assertion, Task 5.3 may make one narrow change to
`PassiveDriverInputTests.cs`: rename the all-steps Ready helper to an
intermediate-steps helper, stop it after Step 1, and require Ready values
`0,1,2`. `PassiveDriverTerminalTests.cs` owns Step 2 and proves
`Step 2 -> End -> Close -> Complete` with no `Ready(3)`.

This clarification supersedes only the sentence in the behavioral design's
file-ownership table that says input tests remain unchanged in Task 5.3. It does
not move production ownership, add a fourth implementation commit, change a
registration, or weaken the requirement that the Task 5.1 and Task 5.2
checkpoints first demonstrate `Ready(3)`.

The implementation is written from the approved behavioral specification and
the current accepted source tree. Generated patches from the abandoned recovery
workflow may be read for context, but they are neither executable authority nor
patch input and must not be applied mechanically.

## 3. Superseded and preserved material

This design supersedes the bootstrap-recovery workflow described by:

- `docs/superpowers/specs/2026-08-10-task-5-bootstrap-recovery-design.md`; and
- the local historical plan
  `docs/superpowers/plans/2026-08-10-task-5-bootstrap-recovery.md`.

It does not supersede the Task 5 behavioral design.

Except for the narrow Task 5.3 test-ownership clarification in section 2.1,
sections 1 through 10 and the behavioral completion outcomes in section 13
remain controlling. Where sections 11 and 12 prescribe
execution and verification mechanics—exact diagnostic and byte pinning,
predeclared mutation patches, immutable review-package machinery, hash
authentication, and append-only correction workflow—this lean design supersedes
those mechanics.

The recovery plan, captured launch outputs, candidate bundles, audit roots,
review reports, and progress records are frozen historical evidence. They are
not edited, deleted, retried, sourced, executed, or extended. They explain why
the execution architecture changed; they do not gate normal development.

No fresh authority bundle, byte-pinned checker, controller, evidence namespace,
prospective commit hash, or one-shot launch is created for this workflow.

## 4. Slice workflow

The slices execute sequentially because each extends the passive driver's state
machine and tests from the previous slice. Within each slice:

1. Confirm the branch, parent commit, clean tracked/index state, and the expected
   historical untracked recovery-plan path.
2. Add or update only that slice's tests, support, and registration.
3. Run the focused cohort and retain a meaningful RED caused by missing or
   incorrect slice behavior. A compile-time RED is acceptable when a new
   production interface does not yet exist; unrelated failures are not.
4. Add the smallest production implementation satisfying the approved behavior.
5. Run the focused cohort to GREEN.
6. Run the complete verification matrix.
7. Obtain fresh independent specification and quality reviews of the actual
   working-tree diff and test evidence.
8. Resolve every Critical or Important finding and every accepted Minor finding,
   rerun affected verification, and re-review the corrected diff.
9. Commit exactly the reviewed slice files with its approved subject.
10. Authenticate that the resulting commit has the approved parent, subject,
    scope, and exact reviewed tree, then obtain fresh independent specification
    and quality reviews of the immutable predecessor-to-commit range. Do not
    begin the next slice until both reviews approve. A post-commit Critical or
    Important finding stops for user adjudication and an explicitly approved
    follow-up; the reviewed commit is never amended, rebased, or silently
    replaced.

Ordinary test failures use ordinary debugging. They do not consume an authority
or force a new planning lineage. No reviewer conclusion is assumed in advance.

## 5. Terminal corrections incorporated up front

The failed recovery effort's source reviews identified two useful terminal
requirements. They are part of Task 5.3's initial tests and implementation, not
separate correction commits.

### 5.1 Serialized output and terminal handoff

Run, Initial, Step, Error, End, Close, and reporter handoffs share one serialized
output lease. A terminal claim cannot close or fail the sink while another output
operation is active. The driver does not hold its state monitor across sink or
reporter callbacks. Atomic first-owner semantics, marker-only trace-I/O failure,
at-most-once Close, and post-close Complete-failure asymmetry remain intact.

### 5.2 Deferred ordinary fault rebasing

If an ordinary fault is deferred while a Step becomes durable, the driver first
clears the attempt, increments the completed-input count, and then rebuilds the
deferred ordinary Error for the new parser position: null input index, null input,
zero settle frames, and null last capture. Trace-I/O and disposal work are not
rebased. A real NDJSON sink test proves the durable Step precedes the corrected
Error record.

Folding these requirements into the original terminal slice preserves the user's
chosen three-commit history and avoids known-bad intermediate terminal states.

## 6. Verification matrix

Run one baseline before Task 5 edits and repeat the same matrix after every
slice reaches focused GREEN:

- forced Release rebuild of the .NET 10 C# harness with warnings as errors,
  no restore, one build worker, and shared compilation disabled;
- the slice's focused C# cohort, plus all established passive-driver cohorts;
- the complete C# harness;
- forced Release rebuild of the compile-only .NET 3.5 compatibility project,
  with warnings as errors and no restore; and
- the complete offline Python suite with the repository virtual environment,
  `PYTHONDONTWRITEBYTECODE=1`, `UV_OFFLINE=1`, and repository `src` on
  `PYTHONPATH`.

The implementation plan records the exact commands from the repository's real
project entry points. Verification results are summarized by command, exit
status, and test count; exact output-byte pinning is unnecessary.

Task 5.3 also receives a short repeated terminal-cohort stress run after its
ordinary matrix to exercise deterministic race barriers and output serialization.

## 7. Targeted mutation qualification

After all three implementation commits pass their reviews, run five narrow
mutations, one at a time, in disposable no-hardlink copies of the accepted final
tree:

1. corrupt one exact cardinal-direction correlation;
2. establish outermost Restart depth too late to suppress nested callbacks;
3. release the shared output lease before terminal Close;
4. retain the stale attempt index in an ordinary fault deferred across a
   durable Step; and
5. invoke Complete before Close.

Each mutation changes one semantic, must make its named focused test fail for the
expected reason, and is then discarded completely. The clean accepted tree must
return to GREEN after each transaction. A mutation that is redundant, fails to
apply narrowly, or does not produce the intended failure is corrected or omitted
with an explicit explanation; it is never counted as killed by assumption.

These five mutations replace the broader mutation catalog in section 11.1 of the
controlling behavioral design. Semantics not selected for mutation remain
mandatory and are covered by focused and full tests plus independent review. The
old 28-mutation catalog remains reference material only and is not replayed.

## 8. Review and completion

After mutation qualification:

1. run the complete verification matrix from the clean final implementation
   tree;
2. obtain fresh independent cross-slice specification and quality reviews over
   the three-commit range and verification evidence;
3. correct any implementation finding through normal TDD and re-review; and
4. write a compact verification report recording the three commit identities,
   commands and outcomes, reviewer verdicts and findings, five mutation outcomes,
   and any justified deviation.

The report is the only final documentation deliverable. It does not reproduce
large logs, generated patches, authority manifests, or shell controllers.

## 9. Safety and scope boundaries

The approved Task 5 out-of-scope boundary remains unchanged. In particular, this
workflow does not launch the game, modify Unity or BepInEx integration, install
the plugin, touch saves, use the network, or begin Task 6.

All builds and tests are local and offline. Temporary mutation copies are
disposable and must not share hardlinks with the working tree. Existing user
changes and historical artifacts are preserved. Beyond this design, its
implementation plan, and the compact final report, only explicitly reviewed
Task 5 source, test, support, and registration paths are committed.
