# Task 5 Bootstrap Recovery Design

**Date:** 2026-08-10

**Status:** User-approved approach; written specification pending final user review

## 1. Purpose

Task 5 implementation did not begin. The one authorized launch of the
committed Task 5 bootstrap exited with status 1 before it allocated an
evidence namespace, changed a tracked file, staged a patch, ran a build, or
ran a project test. The failure came from a deterministic ordering defect in
the reviewed bootstrap itself.

This design defines the smallest append-only recovery that preserves the
failed plan and every reviewed artifact, corrects the bootstrap trust check,
and reuses P0's previously approved implementation bodies only as authenticated
source material. It changes no Stephen's Sausage Roll simulator behavior and
changes none of the 42 authenticated implementation and qualification bodies;
the recovered executable still requires fresh authority.

The consumed Task 5 plan is never retried. Recovery receives a new design
commit, a new executable-plan commit, fresh plan reviews, fresh explicit user
approval, a fresh authority bundle, and a fresh evidence namespace.

## 2. Accepted state and failure facts

The immutable pre-failure chain is:

```text
S4 f5de26f3dea85f14f25e3540da9f29130e27a09b
└─ D  9f69d2c40406461a28f018290d579cf313f22287
   └─ P 13305954d2b6a42a02ef0eae4aa6843a2f18c46e
```

P has subject `docs: plan Task 5 passive driver completion`, sole parent D,
tree `1d1d03c0f7589c582d9de6ee123add11a77e94a8`, and exact one-file scope
`docs/superpowers/plans/2026-08-07-task-5-passive-driver.md`. Its important
reviewed identities are:

| Artifact | SHA-256 |
|---|---|
| committed plan | `af1b536f268f11bfe9abaf2a30fe49fcfe06bbc225df774c49a6b443515650a3` |
| plan checker | `be8181d60d2acb180fcdfab06b0d0dad7a10f53b7abea04bf49c8465b297a7ae` |
| runtime | `27c49be6211d826a45a3aa68d1bd05f8b35f3146aa9ab7863d49eaab33ad93a3` |
| bootstrap | `f155abbeb615a152db6111fc11d3e0f46998899bc6e2ea7095cc804b8e313f72` |
| core manifest | `4f6baa223f6e6bf8545bcf92c96039438d4916c82de41025c155ebdedf37fbcc` |
| canonical-mutation manifest | `b9c740421824b9cdd0e482ee63ad2baf1da9f83d8c43e89dbb37094699342b92` |
| P review package manifest | `cec514599bef23edec74d53dddba04816eaf6e932e80b469ec17d6da80ad6508` |
| P spec response | `32224b7fa12bf6d299e9dbd86195e11bbbe898bd2fb60d05eceaf27d349d92d0` |
| P quality response | `06bb0743187087789c405baeb5df973ae4747e7846aa343f5c7c71a81e271081` |
| original authority manifest | `43b68dd5ebc00fc65a045b4c3fdc5e4662addf7b478ef52ff109e8813ee7ddf7` |

Both formal P lanes returned `APPROVE CRITICAL=0 IMPORTANT=0 MINOR=0`, and the
user then replied exactly `Let's do it!` to the explicit P implementation
gate. The original authority bundle preserved that approval in an independently
audited structured envelope.

The authorized bootstrap launch exited 1 with empty captured stdout and
stderr. Its early rcfile computes environment-variable names with
`LC_ALL=C sort`, but its literal expected value places these adjacent lines in
the wrong order:

```text
HOME
HISTFILE
```

The actual C-sorted order is:

```text
HISTFILE
HOME
```

The failed assertion precedes `task5_evidence_root=`, ERR-trap installation,
and `mktemp`. Independent read-only checks found no path matching
`/private/tmp/ssr-task5-evidence.*`. HEAD, branch, index, worktree, and
untracked-file state remained clean at P. Therefore the failed attempt is
recorded as `namespace=UNALLOCATED` and `retired-manifest=ABSENT`; recovery
must not invent a retired namespace or manifest.

## 3. Decision and commit graph

Recovery is a new append-only planning lineage:

```text
S4 -> D -> P -> D5R1 -> P5R1 -> C51 -> C52 -> C53 -> C53C1 -> C53C2 -> R
```

- `D5R1` is this design commit. It has author and committer
  `jess <optimistindustries@gmail.com>`, subject
  `docs: design Task 5 bootstrap recovery`, sole parent P, and exact one-file
  scope containing only this design path.
- `P5R1` is the forthcoming recovery-plan commit. It has the same exact author
  and committer, subject
  `docs: plan Task 5 bootstrap recovery`, sole parent D5R1, and exact one-file
  scope containing only
  `docs/superpowers/plans/2026-08-10-task-5-bootstrap-recovery.md`.
- P remains the immutable source-plan commit and is called `P0` throughout
  recovery. P5R1 remains `P5R1` in controller actions, review records, report
  records, and final lineage; the recovery runtime must not reuse the label
  `P` for changed executable bytes. C51 retains its established task name and
  subject but names P5R1 as its exact parent.
- Future implementation and report commits retain their approved subjects and
  source/test/report scopes, but their exact sole-parent chain begins at P5R1.

Neither P nor its plan file is amended, replaced, rebased, or squashed. Its
terminal-failure clause and exact commit identity make it source-only after the
failed launch.

## 4. Recovery scope

### 4.1 In scope

- A sealed external record of the failed launch and unchanged repository.
- Separate immutable identities for source plan P0 and execution plan P5R1.
- A corrected bootstrap environment-order assertion.
- Exact authenticated deltas that derive the recovery checker, bootstrap, and
  runtime from reviewed P0 bytes.
- Rebinding bootstrap ancestry, authority, patch extraction, lifecycle
  sequencing, reviews, and report provenance to D5R1/P5R1.
- Fresh candidate and committed recovery-plan audits.
- Fresh independent P5R1 specification/protocol and shell/evidence reviews.
- Fresh explicit user approval after those reviews.
- A fresh authority bundle and evidence namespace.
- Resumption of the original Task 5 Task 0 through Task 4 workflow.

### 4.2 Out of scope

- Modifying committed P0, or launching, sourcing, executing, or using P0's
  bootstrap as an rcfile. Recovery may transform only an authenticated copy in
  a disposable audit directory into separately named P5R1 artifact bytes.
- Rewriting any historical commit, review response, package, authority record,
  or failed-attempt fact.
- Any change to simulator, oracle, plugin, Core, test, protocol, mutation,
  trace-export, or Python-probe behavior before the recovered controller
  applies the already reviewed Task 5 bodies.
- Regenerating an implementation or mutation body merely because docs-only
  ancestry changed.
- Game, Steam, Unity, Mono, BepInEx, adapter, configuration, install, save,
  network, restore, GUI, training, or Task 6 work.

## 5. Failed-attempt record

Only after this design commit receives explicit written-spec approval, and as
part of authorized recovery-plan preparation rather than Task 5 execution,
non-shell coordination creates one fresh immutable failure package outside the
repository and outside every Task 5 evidence namespace. The package is created
before P5R1 is finalized. The recovery plan fixes its exact path, schema,
manifest SHA-256, ownership, modes, and file hashes. It contains only:

1. the exact authorized launch text with the three substituted bootstrap and
   authority values;
2. an identity binding P0, branch, P0 tree, clean index/worktree status, working
   directory, bootstrap SHA-256, and original authority-manifest SHA-256;
3. exit status 1 and the SHA-256/byte counts of the empty captured stdout and
   stderr;
4. a post-failure manifest showing no matching Task 5 evidence root, plus a
   literal `prelaunch-inventory=UNAVAILABLE` because no separate prelaunch
   inventory artifact was captured; the authenticated failing-code position
   proves the launch itself could not reach namespace allocation;
5. `namespace=UNALLOCATED` and `retired-manifest=ABSENT`;
6. the exact original and C-sorted environment-name fragments; and
7. a canonical self-excluding manifest covering every other package file.

The package states what was observed and labels unavailable data explicitly.
It does not synthesize a controller ledger entry, retirement record, or shell
transcript that never existed. Candidate audit, committed audit, recovery
bootstrap, final report, and final audit all authenticate the unchanged
failure package.

## 6. Two-source recovery architecture

Recovery separates immutable implementation authority from executable recovery
authority.

### 6.1 Source-plan authority

P0 supplies the already reviewed:

- 10 implementation patch bodies;
- 28 canonical mutation bodies;
- two rejected mutation bodies;
- T5M28 export hook and probe;
- source/result SHA-256 and Git blob pins;
- plugin, Core, and tests subtree pins;
- RED/GREEN expectations; and
- Task 4.2 closure inputs.

The P5R1 checker authenticates P0's commit, plan bytes, checker, bootstrap,
runtime, manifests, 42 bodies, original package, responses, approval, and
authority bundle before importing any of them. Runtime extraction reads those
bodies from `P0:docs/superpowers/plans/2026-08-07-task-5-passive-driver.md`.
The bodies are not copied into P5R1 and cannot silently drift.

All 42 bodies and touched-file pins remain byte-identical. D5R1 and P5R1 are
docs-only, so the plugin/Core/tests subtrees at the execution baseline remain
the authenticated P0 values. Full repository trees and future commit OIDs are
resolved and sealed at runtime, as P already required; P5R1 does not
self-reference a prospective commit or tree.

### 6.2 Recovery-plan authority

P5R1 embeds a complete recovery checker and corrected bootstrap as executable
fences, plus exact hash-pinned delta patches and prospective result hashes for
the checker, bootstrap, runtime, and any plan-independent derivation manifest.
The audit core manifest contains P5R1's plan SHA-256 and therefore is never
prospectively hashed inside its own plan blob: candidate audit materializes it,
committed audit reproduces and byte-compares it, and the postcommit review
package and fresh authority bundle seal its resolved hash. The complete checker
is necessary to establish the preapproval trust boundary; it is never
materialized by an unauthenticated transform. Candidate and committed audits:

1. extract the reviewed source bytes from P0 into a disposable audit directory,
   without modifying, sourcing, or executing the committed originals;
2. authenticate their exact source hashes;
3. apply each exact delta in a disposable audit directory;
4. require the resulting hashes, final LF, Apple Bash 3.2 syntax, dispatcher
   arities, called-versus-defined symbols, and closed action sequence;
5. structurally replay every imported patch body against the appropriate fresh
   no-hardlink disposable docs-only lineage using apply, check, reverse, hash,
   blob, and tree comparisons only; and
6. prove the audit changed neither the real worktree nor any Task 5 evidence
   namespace.

Both preapproval audit modes are build-free and test-free. They do not execute
the T5M28 probe, run a compiler or project test, create a source commit, edit
the real worktree or index, or allocate an execution evidence namespace. Hook
and probe bytes are authenticated; the hook receives structural apply/reverse
coverage, while the probe is not run until its approved Task 4 transaction.

The recovered runtime changes only the trust and lineage plumbing required to:

- authenticate `D -> P0 -> D5R1 -> P5R1`;
- make P5R1 the explicitly named baseline checkpoint and C51's exact parent,
  without relabeling P5R1 as P;
- keep P0 as the exclusive source of imported artifact bodies;
- bind the failure package and both old and new authority layers;
- regenerate ordinal/action-sequence counts and hashes;
- update review-package range parents and final lineage/report checks; and
- record a distinct source-plan provenance block in R.

It does not alter an implementation patch, mutation semantic, build command,
focused cohort, stress iteration, parser proof, or Task 4.2 closure rule.

## 7. Causal bootstrap regression

The recovery checker must exercise the exact defect, not merely search for two
strings.

Under Apple Bash 3.2 and a literal minimal `env -i` boundary, it captures the
C-sorted environment-name bytes used by bootstrap. It proves:

1. a nonallocating predicate harness containing the exact authenticated P0
   comparison rejects those bytes for the expected reason;
2. the corrected literal accepts those same bytes;
3. `HISTFILE` occurs exactly once immediately before `HOME`;
4. hostile inherited `BASH_ENV`, `ENV`, aliases, and exported functions do not
   cross the clean process boundary; and
5. the corrected bootstrap still rejects every missing, extra, duplicated,
   reordered, or unsafe environment name.

This probe runs in both candidate and committed audit modes before user
approval. It never launches, sources, or uses P0's bootstrap as an rcfile. The
postapproval bootstrap rechecks the identical materialized P5R1 bytes and
result hash before executing those distinct recovered bytes as its sole rcfile.

## 8. Fresh authority and execution lifecycle

Original P0 reviews and approval remain authenticated provenance, but they do
not approve changed recovery code. Before execution, non-shell coordination
must:

1. freeze one complete P5R1 review package containing the recovery design,
   recovery plan, failure package, imported P0 identities, materialized
   checker/bootstrap/runtime, delta bodies, and audit results;
2. obtain independent specification/protocol and shell/evidence reviews from
   report-safe reviewer references that are pairwise distinct from each other
   and from the implementation actor/controller reference;
3. require both verdicts to be `APPROVE` with zero Critical and Important
   findings while preserving reviewer-derived Minor dispositions, and bind
   the assigned reviewer plus actor references into each sealed response and
   response identity;
4. obtain a new explicit user approval that postdates both sealed responses;
   and
5. freeze a fresh recovery authority bundle binding P0, D5R1, resolved P5R1,
   the failed-attempt package, old provenance, new reviews, actor references,
   and the new approval bytes/reference.

Only then may one authenticated recovery bootstrap allocate a new path matching
`/private/tmp/ssr-task5-recovery-evidence.*`. Its first controller action must
authenticate the committed P5R1 plan/checker/runtime/bootstrap, source P0,
failure package, and complete fresh authority bundle before Task 0 begins.

No path matching the old `/private/tmp/ssr-task5-evidence.*` namespace may be
created or reused. The original authority bundle remains immutable and is
imported by value, never modified in place.

Every later action remains a fresh clean-controller call recorded in one
ordinal ledger. A post-allocation failure retires that fresh namespace with an
immutable manifest and forbids retry. A pre-allocation mismatch stops without
inventing a namespace. Any later recovery requires the next monotonic
append-only design/plan round.

R contains one active response block with exactly 14 records: the Cartesian
product of checkpoints `P5R1`, `C51`, `C52`, `C53`, `C53C1`, `C53C2`, and
`FINAL` with lanes `spec` and `quality`. P0 never occupies an active P5R1
review slot. A separate fixed recovery-provenance block binds P0's review
package manifest, both sealed response/identity pairs, complete lowercase
response hex, original approval text/reference hashes, and original authority
manifest. The report schema and final audit reject record substitution between
the active and provenance blocks.

## 9. Verification and review

Before P5R1 is offered for implementation approval, the recovery plan must
demonstrate all of the following from fresh commands:

- exact P0/D5R1/P5R1 ancestry, subjects, authorship, scopes, and bytes;
- unchanged clean source, index, and worktree at the committed P5R1 baseline;
- exact failure-package schema, hashes, absence claims, and provenance;
- exact old authority/package/response identities without modifying them;
- candidate and committed recovery audits with identical derived hashes;
- causal RED for P0's bad ordering and GREEN for the corrected ordering;
- Apple Bash 3.2 syntax for every executable fence and concatenated runtime;
- zero undefined `task5_*` symbols and exact dispatcher arities;
- a literal closed lifecycle sequence with regenerated ordinal counts/hashes;
- exact 42 imported bodies and complete disposable 10 + 28 + 2 + hook
  structural apply/check/reverse/hash/tree replay, with no preapproval build,
  test, or probe execution;
- unchanged result-file and plugin/Core/tests subtree pins;
- disposable-clone restoration to the docs-only recovered baseline;
- no game, network, restore, GUI, installed-plugin, save, configuration, or
  Task 6 command; and
- two independent exact-package P5R1 reviews.

After fresh user approval, recovered Task 0 reruns the full clean baseline and
Task 4.2 closure before any source patch. C51 through R then follow P0's existing
TDD, build, review, mutation, stress, report, and final-audit requirements with
the revised ancestry and source-plan provenance.

## 10. Completion criteria

Recovery is successful only when:

- P0 remains unchanged and its bootstrap is never relaunched;
- the failed attempt is preserved exactly as an unallocated attempt;
- D5R1 and P5R1 have the declared one-file docs-only scopes;
- both recovery-plan audit modes pass with the same derived identities;
- fresh reviewers and the user explicitly approve P5R1;
- exactly one fresh recovery namespace is allocated;
- Task 0 authenticates the recovered baseline before any source change;
- all original Task 5 implementation and qualification bodies remain exact;
- the final chain is
  `S4 -> D -> P0 -> D5R1 -> P5R1 -> C51 -> C52 -> C53 -> C53C1 -> C53C2 -> R`;
- R records both the original consumed-plan provenance and the recovered
  execution lineage; and
- every original Task 5 completion criterion not explicitly superseded by this
  design and the approved P5R1 plan remains satisfied.

No implementation command is authorized by this design. Execution requires a
separate committed P5R1 plan, two fresh formal reviews, and another explicit
user approval.
