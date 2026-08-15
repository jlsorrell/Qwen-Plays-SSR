# Task 5 Passive Driver Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Unity-free passive driver in three separately owned implementation commits, preserve the sealed Task 4.2 boundary, append the two required Task 5.3 concurrency/protocol corrections, qualify every targeted mutation, and publish one compact verification report without entering Task 6.

**Architecture:** Extend the sealed Task 4.2 driver through a strict linear lineage. Task 5.1 owns manual input attribution and every durable Step; Task 5.2 owns Restart/state-set lifecycle balancing; Task 5.3 owns successful terminal completion. Two immutable follow-up commits then serialize all output handoffs and rebase a deferred ordinary fault after an overlapping Step becomes durable. All edits remain in Unity-free Core and its local C# harness; every checkpoint is authenticated and tested offline before the next commit.

**Tech Stack:** C# 7.3-compatible Core sources, .NET SDK `10.0.300` for the net10 unit harness, compile-only `net35`, Git full-index patches, Apple `/bin/bash` 3.2, and the pinned Python environment for the unchanged oracle-protocol suite and final stale-trace parser proof.

## Global Constraints

- This base document is not executable while any injection marker remains. Materialization requires replacing exactly ten implementation-patch blocks and the one mutation-catalog block with authenticated literals, then repeating the self-review at the end of this plan.
- The current Task 5 worktree is already isolated and is the sole primary implementation checkout. No second worktree is mandatory. Keep all approved implementation, staging, commits, builds, and ordinary tests there; never use the user's real worktree, a derivation checkout, or a protected Task 4.2 checkout. After approval, disposable local no-hardlink clones are permitted solely for the declared mutation and T5M28 proof transactions. Before approval, the single narrower checker exception below applies and grants no implementation authority.
- The accepted Task 4.2 seal is `S4=f5de26f3dea85f14f25e3540da9f29130e27a09b`, tree `4bdb6fed33ea4ae0df6d956e512849c57b26b44c`.
- The approved Task 5 design is `D=9f69d2c40406461a28f018290d579cf313f22287`, tree `a691afd8ae55f3676bcf1ffe0f6ef3b15b1d2feb`, exact sole parent S4.
- The required lineage is exactly `S4 -> D -> P -> C51 -> C52 -> C53 -> C53C1 -> C53C2 -> R`. No merge commit, squash, amendment, rebase, replacement, or side commit is permitted in this chain.
- `P`, `C51`, `C52`, `C53`, `C53C1`, `C53C2`, and `R` are future real commits while this plan is being prepared. This plan deliberately does not self-pin their future object IDs or root trees. P through C53C2 are authenticated at runtime by exact parent, subject, scope, resolved tree, and the exact plugin/Core/tests subtrees and file bytes below, then recorded both externally and in R. R is resolved only after its commit and is recorded externally and in the final handoff; R never self-pins its own object ID or root tree.
- Committing and reviewing P ends planning. After P is committed, stop and obtain the user's explicit approval to begin implementation. Outside that named checker exception, do not create the Task 5 evidence root, run Task 0, extract or apply a patch, build, test, clone, mutate, or write R before that approval. The checker exception remains audit-only and cannot create a real checkpoint or implementation result.
- Once a commit or review package enters formal review, it is immutable. A Critical or Important finding is corrected only in a new append-only descendant commit and receives a fresh affected review.
- All package and test execution is offline. Every `dotnet` build and run contains `--no-restore`. Set `UV_OFFLINE=1` for Python. Do not run restore, install, fetch, pull, curl, wget, package acquisition, a network-URL clone, or any other network-capable command. The only preapproval clone exception is the checker’s one build-free `git clone --no-hardlinks` of authenticated local D beneath its fresh `/private/tmp` audit root. After approval, the only clone exceptions are the declared local no-hardlink mutation and T5M28-proof checkouts.
- The only .NET executable is `/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet`; require exact `10.0.300` before any build. Do not accept another SDK selected through `PATH`, a roll-forward policy, or a global.json change.
- Shell helpers must parse and run under macOS `/bin/bash` 3.2 with `--noprofile --norc`. Do not use associative arrays, `mapfile`, `readarray`, `${name,,}`, negative array indices, `wait -n`, or any Bash 4+ syntax. Do not place a brace-expanded manifest literal inside a quoted `test`; compare manifests line by line under `LC_ALL=C`.
- Use `PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Cellar/dotnet/10.0.300/bin`, `LC_ALL=C`, `GIT_CONFIG_NOSYSTEM=1`, and `GIT_CONFIG_GLOBAL=/dev/null` for authenticated gates.
- Do not launch Stephen's Sausage Roll, Steam, Unity, Mono, BepInEx, the plugin, or any GUI. Do not read or modify game files, saves, installed configuration, compatibility deployment, or boot evidence.
- Do not perform Task 6 adapter wiring, Harmony patching, replay injection, configuration, installation, runtime probing, or training-pipeline work.
- Do not modify `oracle/plugin/Core/PassiveDriverBoundaries.cs`, `HookKind`, `HookToken`, `UpdateDirective`, `GateSample`, protocol DTOs, `ITraceSink`, or `IPassiveReporter`.
- Do not modify the Task 4.2 design, plan, seal, historical monolithic plan, ignored brief, ignored helper, ignored ledgers, mutation patches, or any accepted/rejected Task 4.2 artifact. Task 5 creates no Task 4.2 evidence and never appends to a Task 4.2 ledger.
- Do not execute or cite a legacy Task 5.1-5.3 body as an instruction source. This plan restates the complete executable workflow; older bodies are historical context only.
- Do not reintroduce `SetNeutralSeenForDefensiveTest`, `AssertCandidateClearedForDefensiveTest`, or an equivalent manufactured-state seam. The corrected NotInspected case must use real callbacks.
- Task 5 creates no raw tracked transcript ledger, no controller replay ledger, and no separate seal. Raw logs and mutation patches live only in an external `/private/tmp` evidence root. `R` is one compact tracked report.
- Each canonical patch has final LF, uses `git diff --binary --full-index`, applies from exactly one declared parent without fuzz-dependent trust, and is authenticated by patch SHA-256, lines, bytes, parent blob/file SHA-256, result blob/file SHA-256, and result tree. During the named checker audit, extract only authenticated bodies from the candidate or P into its fresh external audit root and apply/reverse them only in its disposable clone. During approved implementation, extract embedded patches from committed P into external evidence; apply only with `git apply --check --index` followed by `git apply --index`, then prove the staged full-index diff is byte-identical to the extracted patch for its exact disjoint scope.
- Never use `git clean`, destructive reset, broad checkout, or file deletion to establish cleanliness. Existing ignored Task 4.2 evidence is preserved byte for byte.
- Every accepted GREEN build has zero warnings and zero errors. The successful C# harness stdout is exactly one line, `SSR oracle unit harness ready`, unless the command is the explicitly declared 20-iteration stress loop.
- Any ancestry, scope, hash, RED, GREEN, review, mutation, restoration, parser-provenance, or cleanliness mismatch stops execution. Do not update a pin to bless the mismatch.
- The only shell execution outside `task5_clean_call` is the standalone
  candidate-audit/P-commit/committed-audit transaction before approval and the
  one-time bootstrap after approval. Both checker invocations begin at process
  start with the exact clean environment prescribed below. The checker's own
  build-free disposable replay is the sole preapproval clone/apply exception.
  Formal-review and user coordination is non-shell. After bootstrap, the only repository edit outside a controller
  action is one `apply_patch` creation of the fixed R path, bracketed by
  `report-gate authorize` and `report-gate candidate`. Workers and reviewers
  may not create, replace, chmod, or otherwise edit the controller-owned
  command ledger, state seals, aliases, or immutable review packages; a
  non-shell coordinator may write only the two fixed reviewer-assignment paths
  for a target before its package freezes and may finalize only those files to
  mode 400; each must be owned regular, non-symlink, mode 400, and final-LF-
  terminated with exactly one report-safe coordination-reference line and no
  CR or extra byte. A
  reviewer may write only its assigned fixed pending-response path.

TASK5-PREAPPROVAL-REPLAY-EXCEPTION: checker-only-build-free-no-hardlink-local

TASK5-COORDINATION-REFERENCE-CONTRACT: ascii-safe-no-standalone-r-v1

Every implementation-actor, approval, spec-reviewer, quality-reviewer, and
reviewer-assignment reference is nonempty; contains only ASCII letters, digits,
`.`, `_`, `:`, `/`, and `-`; and, under `LC_ALL=C`, does not match the tracked
report scanner's case-insensitive `(^|[^a-z0-9])r([^a-z0-9]|$)` boundary.
A standalone single-letter `r` segment is reserved for the future R checkpoint
and is forbidden at string edges or between any permitted delimiters. Thus
`R`, `agent/R`, `reviewer-R`, and `r_1` are invalid, while `reviewer`, `R1`,
`1R`, `agent/R2`, and `reviewer-r2` remain valid. The same predicate applies at
selection, authority receipt validation, approval-reference validation,
assignment ingestion, package freeze, response sealing, and every later
revalidation; it is tamper-evident coordination provenance, not identity proof.

TASK5-STRUCTURED-TEXT-NUL-DEFENSE-V1

Every coordination reference is validated against its raw file bytes before
command substitution can normalize them: the file is owned, regular,
non-symlink, mode 400, has exactly one LF-terminated line, and its byte count
is exactly the validated shell value length plus that final LF. Every fixed
authority receipt or identity is NUL-free before any field parser reads it,
and the tracked report is NUL-free before either its closed review-record
parser or its broad standalone-R scanner runs. These are structural text
requirements; complete reviewer responses remain byte-exact and are carried
losslessly by the lowercase-hex representation below.

TASK5-REPORT-RESPONSE-ENCODING-CONTRACT: exact-lowercase-hex-v1

No reviewer-derived free text is copied into the report as raw text. Before
report authorization, the controller derives one canonical block of exactly 14
records for `P C51 C52 C53 C53C1 C53C2 FINAL` crossed with `spec quality`.
Each record binds the allowed checkpoint and lane, package and response
SHA-256, exact response byte count, validated actor and reviewer references,
verbatim structured verdict encoded as lowercase hex, reviewer-derived Minor
count, and lowercase hex of the complete immutable response bytes. Every complete immutable response is reconstructible from that authenticated hex;
all unrestricted findings and Minor dispositions remain exact without entering
the broad standalone-R scanner as raw text. The report contains the generated
block byte-for-byte between its fixed markers, with no R-checkpoint record and
no extra record. Candidate, stage, reviewed, and final-audit gates rederive or
authenticate the sealed expected-block SHA and byte-compare the report block.

The only preapproval extraction, clone, apply, or mutation exception is the
standalone candidate/committed checker's own audit. It may extract only the
marker-authenticated bodies from the candidate or P, create one fresh
no-hardlink clone of the authenticated local D checkout beneath its fresh
`/private/tmp` audit root, and apply and reverse those bodies only in that
disposable clone, never the real worktree or its index. The exception permits
no source edit, commit, build, test, restore, network, game, or GUI. All other
implementation extraction, cloning, applying, mutation, and execution remains
prohibited until the committed P reviews and explicit approval are sealed.

---

## Authority and Lineage

### Controlling authority

The behavioral authority, in descending order, is:

1. `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`, SHA-256 `33209340e884fcd580f68183c77b1b8ed6142a13eb30b7f7c530800832b8c8ef` at D.
2. `docs/superpowers/specs/2026-08-04-task-4.2-scope-pure-hardening-design.md`, SHA-256 `1c97f6feeab11f50d16cbc0ebcbfe0e5dce764566537e1999273a49c4a6b9c2a`, and `docs/superpowers/specs/2026-08-04-task-4.2-review-correction-design.md`, SHA-256 `1a848ce91732bbb456246eab453e26cdd4d3b1a6170c6a3cd50219d9e7a29fa1`, at D.
3. `docs/superpowers/plans/2026-08-04-task-4.2-review-correction.md`, SHA-256 `52d899d9c058171f814e09e403f52d00897fad5c4b956fc3fa0930c2ae8eac4c`, and the sealed Task 4.2 production/test boundary at S4, including `docs/superpowers/evidence/2026-08-04-task-4.2-review-correction-evidence.md`, SHA-256 `6a6c43466b32628551f473d839689533c1f2ef7e358e926f78594b1a4c767adb`.
4. `docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md`, SHA-256 `f44dd6709f9ca8af17b5dfabec8da7bc1566fb3b6b1f77cfb4874a12aed0e1a4` at D.
5. This standalone plan after all injection markers are resolved, independently reviewed, committed as P, and explicitly approved for implementation by the user.

TASK5-DESIGN-AMENDMENT: U-T5-C53-INTERMEDIATE-READY-01

After D was committed, the user was paged in on the proposed test amendments
and supplied the following two explicit approvals, in order:

> The amendments to the tests sound good, thanks for getting me paged in

> Approved.

This higher-priority user amendment overrides only the Task 5.3 ownership-table phrase `input tests remain unchanged` in D. It authorizes only the C53 intermediate-Ready expectation amendment already specified below: the existing
input registration stops after Step 1, retains Ready values `0,1,2`, and leaves
the Step-2 terminal branch to the first terminal registration. All other D ownership and behavior remain unchanged. The future post-P implementation-
authority receipt must identify the resolved P and ratify `U-T5-C53-INTERMEDIATE-READY-01`; P does not self-authorize this exception.

The superseded Task 5 prose in `docs/superpowers/plans/2026-07-31-oracle-passive-plugin.md` has no executable authority. Its byte identity is pinned only so Task 5 cannot silently rewrite Task 4.2 history.

### Commit graph and exact scopes

| Alias | Required subject | Exact parent | Exact committed scope |
|---|---|---|---|
| S4 | `docs: seal Task 4.2 correction evidence` | `6ade9cd2a06548741d104a38b6498f4e5b48af7f` | `docs/superpowers/evidence/2026-08-04-task-4.2-review-correction-evidence.md` |
| D | `docs: design Task 5 passive driver completion` | S4 | `docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md` |
| P | `docs: plan Task 5 passive driver completion` | D | `docs/superpowers/plans/2026-08-07-task-5-passive-driver.md` |
| C51 | `feat: attribute passive input attempts` | P | `oracle/plugin/Core/PassiveDriver.cs`; `oracle/plugin/Core/PassiveDriverInput.cs`; `oracle/plugin/tests/PassiveDriverInputTests.cs`; `oracle/plugin/tests/PassiveDriverTestSupport.cs`; `oracle/plugin/tests/Program.cs` |
| C52 | `feat: balance passive lifecycle hooks` | C51 | `oracle/plugin/Core/PassiveDriver.cs`; `oracle/plugin/Core/PassiveDriverInput.cs`; `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs`; `oracle/plugin/tests/PassiveDriverInputTests.cs`; `oracle/plugin/tests/Program.cs` |
| C53 | `feat: finalize passive trace capture` | C52 | `oracle/plugin/Core/PassiveDriver.cs`; `oracle/plugin/Core/PassiveDriverCompletion.cs`; `oracle/plugin/Core/PassiveDriverInput.cs`; `oracle/plugin/tests/PassiveDriverInputTests.cs`; `oracle/plugin/tests/PassiveDriverTerminalTests.cs`; `oracle/plugin/tests/PassiveDriverTestSupport.cs`; `oracle/plugin/tests/PassiveDriverTests.cs`; `oracle/plugin/tests/Program.cs` |
| C53C1 | `fix: serialize passive terminal handoff` | C53 | `oracle/plugin/Core/PassiveDriver.cs`; `oracle/plugin/Core/PassiveDriverCompletion.cs`; `oracle/plugin/Core/PassiveDriverInput.cs`; `oracle/plugin/tests/PassiveDriverTerminalTests.cs`; `oracle/plugin/tests/PassiveDriverTestSupport.cs` |
| C53C2 | `fix: rebase deferred step faults` | C53C1 | `oracle/plugin/Core/PassiveDriverInput.cs`; `oracle/plugin/tests/PassiveDriverTerminalTests.cs` |
| R | `docs: record Task 5 passive driver verification` | C53C2 | `docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md` |

At each commit, resolve the alias with `git rev-parse HEAD`, record it outside the repository, and assert the next commit's sole parent equals that resolved 40-character lowercase ID. Never insert an unresolved future commit ID into P itself.

## Immutable Pins

### S4/D commit pins

| Item at D unless stated otherwise | SHA-256 | Git blob | Lines | Bytes |
|---|---:|---:|---:|---:|
| capture design | `33209340e884fcd580f68183c77b1b8ed6142a13eb30b7f7c530800832b8c8ef` | `afe01e2721732b5b62d5b7c1628a7885b1e2fdb6` | 1159 | 56180 |
| Task 4.2 scope-pure hardening design | `1c97f6feeab11f50d16cbc0ebcbfe0e5dce764566537e1999273a49c4a6b9c2a` | `b22e1403b420a0ba5ae5c9436f4c4902a2443a36` | 358 | 16762 |
| Task 4.2 correction design | `1a848ce91732bbb456246eab453e26cdd4d3b1a6170c6a3cd50219d9e7a29fa1` | `19efb6017f070616d4ae978372185651eb7607b9` | 623 | 31014 |
| Task 5 design | `f44dd6709f9ca8af17b5dfabec8da7bc1566fb3b6b1f77cfb4874a12aed0e1a4` | `e87ac8ebcd12ed403fd1c34dc74a54a0823c1c50` | 494 | 23089 |
| superseded monolithic plan | `f0018c53591a7bb73b9c92902570167f3144174fdda83eda20716dbb0fded65e` | `7099498479f58a5bd9f5facb7b0c3c77307d7e31` | 28913 | 1132724 |
| Task 4.2 correction plan | `52d899d9c058171f814e09e403f52d00897fad5c4b956fc3fa0930c2ae8eac4c` | `283d691e50acfbd8ed71950412aead0e20e087d8` | 7310 | 293649 |
| Task 4.2 evidence seal | `6a6c43466b32628551f473d839689533c1f2ef7e358e926f78594b1a4c767adb` | `d236429e96eaca01b6e6bfdb240c069869a3656d` | 120 | 53031 |
| `CanonicalJson.cs` | `7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c` | `110716e97b10e2575ea2fa61a01f3f5077f40408` | 345 | 11884 |
| `CaptureException.cs` | `88e7fa226a595059a72e01eea69f33160b08721f6c61db68a69c25fc334db2bd` | `01a27b53f56314e251ee4f4f81402d7d585f4ea7` | 14 | 259 |
| `CaptureSignature.cs` | `335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54` | `8f1817ec80ac57a8cdfaa4dda326aa9b38592221` | 55 | 2001 |
| `NdjsonTraceSink.cs` | `b3bd207ec4684de5e5a896d76eda1aeaaff88f8f5638ebdcee74f9a23535c6fb` | `6135c09c9586ec31a17b7e22921d2297bd929a04` | 274 | 7545 |
| `OracleProtocol.cs` | `a82c1c403d19cef3cd67a4c363c3e6582bbe394af648a5c740e28f31213554ce` | `5068184fdd4ac50e638296b173db269648c3665c` | 433 | 15371 |
| `PassiveDriver.cs` | `0ab8b9dfb537577fb052e6e5dab2ca744bc08cfb92206e44fd00e4552cee56a6` | `16ae4d36bc03bfb9d4e3b4948d5b356709f66636` | 865 | 24715 |
| `PassiveDriverBoundaries.cs` | `1a130383302b315f43f8643fab5c13ec8d643727c2095ca21929aac306cdf133` | `b575724daf03cdf7d9a96722945a55ccd46a6e87` | 434 | 10977 |
| `PassiveDriverBoundaryTests.cs` | `20c90060294a822967ff7d9e75f6a86fdae2ba247b6a9a08eb327b623424e0fc` | `9dc0261bc4abd0a91ce818396d455b16561ed944` | 1368 | 49452 |
| `PassiveDriverInitialTests.cs` | `0590e9ae35cc074e012dcffb86fae94e35bdd9d9225446b490bcce19de0c1b85` | `1528db5f92ec836a841a76f4f0edd858355678ad` | 1745 | 60511 |
| `PassiveDriverTestSupport.cs` | `ee3af9a57cc539262d2bd80e8f163ea60988087d39fe2600cbf3f38169d9edb9` | `d089f8514b450384a6f72080d3bde2cea5218d38` | 475 | 13008 |
| `Program.cs` | `9372ea72e23ca9d8a95f2cce1f7146713b603ce7ea733fe2e0756a33c6b25004` | `386f79c6cfb6b5b4100c413c2802b2191f1b79e3` | 38 | 1077 |
| `SsrOracle.UnitTests.csproj` | `f8c5924d6e08cec8c08f7bafde2a5ef874d2bb17739cdfcf4f2b9924e51ff688` | `14df214f1e404fa584912ca6b7b074d75a3d3d73` | 12 | 362 |
| `SsrOracle.Core.Net35.csproj` | `2cba9da0e4d8b751a27405c1d721dfd418b6ef15dd6fcab2a45bf00aeaab0151` | `c371a863b008a29cd080a0db0b1a583afc2c0548` | 20 | 799 |
| `Directory.Build.props` | `9a4fe75bf551bd68539265b8ef587be8875891490324e00d14944c5947bcbc85` | `a5aa60be6f09a030ace1464e19a3461d17097f2d` | 6 | 278 |
| `TestSupport.cs` | `fbe3965629bd9bcd82ba2e55be04829f86302ceb544a5ea117b942a5f2a3842f` | `ca67d433debcb534aaf8bb4bc5453766f23e8bd0` | 430 | 17375 |
| Python trace reader | `9feab69eec050eea51670c9f80b00acba06799e500a4ed3502f02722d5ea7108` | `f390923533985d4b1595ea50f5dcf8119d1c1cca` | 960 | 33901 |
| Python protocol tests | `a0689d3233f55e24a95de5f5f6212690b2b820f03aaf47db8a383dfff4e2ead4` | `0c0afbc7d859aac06f88c8514b28a2a3c0703c53` | 1900 | 58585 |
| `tests/test_oracle_install_compat.py` | `bb85418b25dfc18c7f0ea268ff65c2442ae41a3a6c93217911a11774cff9a5e0` | `bf4867f9f73668cf1db2d62a7fac030fbf78930f` | 7543 | 255854 |

The sealed S4 subtree pins are:

| S4 path | Git tree |
|---|---|
| `docs/superpowers/specs` | `3afac5e2b6846c23dff21282fe8010b1e6a5fb33` |
| `docs/superpowers/plans` | `3d0ac5e512fc975258dc41b6489b19beb5026de6` |
| `docs/superpowers/evidence` | `a0d4a02cefc6193c881627eec9e919123aab71bd` |
| `oracle/plugin` | `aa2a29d64b2e17ddc438f38060d0855d65d3cd1e` |
| `oracle/plugin/Core` | `6961f005d1f95199c7ffed83d2062a1c221d54b6` |
| `oracle/plugin/tests` | `2a9f6d872e7dcd82ba98fab051cd5366f904d0e8` |
| `tests` | `bde2451478abb76b9b0ac39b6783c171dcef845f` |
| `src/ssr_env` | `82dc33143bc7654d31ae88a7da7f09f826bd0c2f` |

At D the future files `PassiveDriverInput.cs`, `PassiveDriverLifecycleHooks.cs`, `PassiveDriverCompletion.cs`, `PassiveDriverInputTests.cs`, `PassiveDriverTerminalTests.cs`, and `PassiveDriverTests.cs` are absent. Their creation points are fixed by the commit-scope table.

### Checkpoint output pins

The following qualification lineage is exact derivation provenance. Its scratch commit IDs and root trees are not the future real commit IDs or root trees: P adds the committed plan to the docs tree, and C53C1/C53C2 were qualified on an equivalent synthetic C53 lineage. Future real commit IDs, root trees, RED/GREEN log hashes, and P-through-FINAL review identities/package hashes are resolved at runtime; the compact report records only evidence available through FINAL. R and its package/responses are resolved later and recorded only in external evidence, final audit, and handoff. The `oracle/plugin`, `Core`, and `tests` subtree IDs, full patch bytes, and listed file bytes are exact pins because the P docs-only change does not alter them.

| Derivation pin | Parent in derivation | Subject | Derivation root tree | `oracle/plugin` | `Core` | `tests` |
|---|---|---|---|---|---|---|
| C51 `f23a7bb64af40b148b80a3f435d9d1e1bb10cec5` | D `9f69d2c40406461a28f018290d579cf313f22287` | `feat: attribute passive input attempts` | `ae5742b68785e4e2c1c10b6beb06916f421d2daf` | `694928891148bfad6b4215f9d4efbb943f44a104` | `26a0c6acfc7b9ce22f5f93a879b462bf721baa33` | `2fa6213f563d4a8d9aa01f1cb590f34b04f34e8e` |
| C52 `d39e4a8d7bb3735ef0b122f33c626f6b4603a499` | C51 | `feat: balance passive lifecycle hooks` | `223c6155231587edf2f7b5a1737e53bb03ab29e7` | `1a3379be8b250f1a0ef6020ca2265be98ec1353a` | `81fe40cec8877c937ed2b7f9e9dca967d5179add` | `c2a8b9b184298fb75659c345e0c1aec493ff4b73` |
| initial C53 `9fdff9172c43ffbca1bb5623d20f80d9c193e6bc` | C52 | `feat: finalize passive trace capture` | `7b1706545deacd1a9481c20a376e19985a5ccb31` | `1364987fc311b8ade46ac8599f06140befd50d7d` | `f709ff7d0496ee8214f582eb1a7d0dadd895941f` | `c6a18ad771bf796dc91103ba19a853890e6b449a` |
| qualification C53C1 `8a013f317d0695827b0ebd976cb92ecc0c74f9d7` | equivalent C53 `b13863fb84cead6b13ee010609bbc72e057f0655` | `fix: serialize passive terminal handoff` | `aee67f966bccd9055b353f06f88e7a07b4648de2` | `8afbf9d17f762bec53f31fa30648e7a77f396085` | `d1ac5945be7ef1cb32603fe5525defd073a584d4` | `596492b71f9e386470d5c0615543524835f3f28c` |
| qualification C53C2 `bab6c1c1970fea0623fe957e3c006668513fe3c7` | qualification C53C1 | `fix: rebase deferred step faults` | `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16` | `5a7db9d1e661dd97bd6a939d375dd2008506f679` | `531718e596ed3f49f97f92c14edc69c69d60b834` | `b75e36e1ce25538fd1d3cdd85c49f04d003af416` |

The equivalent synthetic C53 has root tree `7d3d5fee7e4255bfc15add09bec205f3b4cb9ea2` and exactly the same plugin/Core/tests subtree IDs as initial C53.

| Full checkpoint patch | SHA-256 | LF lines | Bytes |
|---|---|---:|---:|
| C51 | `544518e3a90c03f7f9af944deb34fa43a4a9f4236d8033b8ee765a874064ed56` | 1965 | 74921 |
| C52 | `b5f9b19188eca3bd1ff856086d06254fd95dc23efe34d844601d42e4e352d8f0` | 1275 | 51615 |
| initial C53 | `9bf687e61eecaeb4786b16f9b08e7b5bfa0f46d5f24fe69b4cacfa89425f56c2` | 1282 | 48611 |
| C53C1 | `0254fc008db0fb43c7fedb5e63ead12c3450555ab84b6f500b117ed90976aca2` | 3066 | 113646 |
| C53C2 | `98dddb0bc658e02dfb884a0f079b0bfe48b0d99f0e2d5723d458bcd275d03ccb` | 213 | 8408 |

Each row is the exact LF-terminated `git diff --binary --full-index parent child`; the artifacts are `task-5.1-full.patch`, `task-5.2-full.patch`, `task-5.3-initial-full.patch`, `task-5.3-correction1-full.patch`, and `task-5.3-correction2-full.patch` under the authenticated derivation evidence root.

Result-file pins are SHA-256 / Git blob / LF lines / bytes. A predecessor is the prior row for that path; the D predecessor pins appear in the S4/D table above. `ABSENT` is an authenticated nonexistence result.

| Pin | Path | SHA-256 | Blob | Lines | Bytes |
|---|---|---|---|---:|---:|
| C51 | `Core/PassiveDriver.cs` | `e20194c9dc2f63842b6dd159819e592ce9bf99a8323c646fd95d629b5f16dfca` | `9227970d1ea6a2d20420bf42a24d51318a301184` | 1097 | 31428 |
| C51 | `Core/PassiveDriverInput.cs` | `67baef638f3fc160512f09f31931b6096a710e7863ddc8c8b525ed9aced80691` | `a61e8b856a010b8a439dd5b1d196213e3f31f634` | 221 | 6090 |
| C51 | `tests/PassiveDriverInputTests.cs` | `76d0de3f9b8616157cc8be25a600bbbad510c9ae9907cfdef20370a8af78af14` | `ec2f13dff1e6e2925fd7749592b127928518d7b4` | 1111 | 46634 |
| C51 | `tests/PassiveDriverTestSupport.cs` | `949c10710520956671fdde096246a2f1b18331c37f5c32b61dd78f6e83742949` | `973127b67e1e5f7d760696f3f82f61ad144272c7` | 526 | 14382 |
| C51 | `tests/Program.cs` | `40a4801b6ce166c67d9cd098525a68ec910e237c22c02f554491f61c089dab8c` | `b89c789b98c2f6872521d0c3655ed32af168220a` | 40 | 1161 |
| C52 | `Core/PassiveDriver.cs` | `92f48f2c109caa9bde0726e23a6860af85a7883fff7d1648d21468ee66034746` | `bf8a6b9417d7b04126f6907441a0633e5f112f6c` | 1121 | 32110 |
| C52 | `Core/PassiveDriverInput.cs` | `6000c5edbac887cbf29f03c593dc17d00c85f41f40449852db80baf13334421d` | `d2c55897bf4ce17a7a1c5604e6952ab9fb07110e` | 261 | 7221 |
| C52 | `Core/PassiveDriverLifecycleHooks.cs` | `c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002` | `d4f1b49e8680676cd6b632390aa337dd58799d70` | 207 | 5771 |
| C52 | `tests/PassiveDriverInputTests.cs` | `8ce3b290640784b7554aec1c6a98d56a4c1cda49172b5e7c035c4b646016a635` | `e0a09eb8931838d12984a05cfa6fd90bf280557d` | 1957 | 83611 |
| C52 | `tests/Program.cs` | `f668a65f46f2bb30678059ecc423a89019775b4340da2f63b491238cafb44a29` | `d1d808c2b052fd1ca2dfe710f7af2dbe4607be42` | 40 | 1161 |
| C53 | `Core/PassiveDriver.cs` | `1b6f4e9db72cb120eb977210179b4343f43c3cc3959f419797ca789e0b3b4eaa` | `a9e7320a3ce3bb43863f5864585364c2f472b0ce` | 1127 | 32339 |
| C53 | `Core/PassiveDriverCompletion.cs` | `1b64d47f491fb0863ce5711de8b4297cafc627147d96a676e6ad476dda460769` | `02437c82042f5f540789afdbbfe71a5b36c7cef7` | 56 | 1465 |
| C53 | `Core/PassiveDriverInput.cs` | `37f9777e467402086f791ffe16a2b46830b49c653879f6648f83766b84fcdef7` | `5fd9120fcdbe364013a08379fc3848cbea4d35ff` | 269 | 7408 |
| C53 | `tests/PassiveDriverInputTests.cs` | `b3fff960738ddb38861c0bc6dea8e517b4b85aaa54d3a88cca9a26bdeeea2330` | `fbbe505b6b9782610c9e2f4108cd1945418d126d` | 1947 | 83173 |
| C53 | `tests/PassiveDriverTerminalTests.cs` | `80714a1223d28b6981801cb52da8775f989f8a0a072306f60e62ed8f93cf4a7a` | `c88849e2f4d9406ad3ca3b1fb646c740d0fd1179` | 847 | 32411 |
| C53 | `tests/PassiveDriverTestSupport.cs` | `1bf00c6d47856fde758d0a184d4a168f4fbe608947ab1f0a65060660c8d736bc` | `d0c0850c83bdf75804927cfc0c844a046d71ea2f` | 619 | 16849 |
| C53 | `tests/PassiveDriverTests.cs` | `be190c28526b9fc4a78ea2bafdc06d6e84457850301c59922f53e3d5149acc20` | `6de99a4feb1440044ba0b6f7c6be99d751ee736d` | 10 | 315 |
| C53 | `tests/Program.cs` | `03c1f2ed72db209e9d3200e9486afa375d6935be42549896fa263f2cb31b09f0` | `9dc3eb50ac4bbf54c2f3f2d9d672c7cc2a1c117f` | 39 | 1091 |
| C53C1 | `Core/PassiveDriver.cs` | `093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130` | `b132f89b321345452901faab870ea0d642b93e06` | 1380 | 39473 |
| C53C1 | `Core/PassiveDriverCompletion.cs` | `27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4` | `638d2882e988b17d686a7791604a497438e7d4e3` | 59 | 1593 |
| C53C1 | `Core/PassiveDriverInput.cs` | `283190a8d3097daa30b247881c01df96ef94400276897c76f872ed0adfdf616c` | `88951007d1f25df778c025009c0b1d23cd6645ef` | 322 | 9036 |
| C53C1 | `tests/PassiveDriverTerminalTests.cs` | `037b201a765b8a9df4bec2b08acd8c8c030ab57597967e3ee37ad68152068626` | `1387c3685204d73e7dee077e232f87fdcb2d6e0f` | 2424 | 90775 |
| C53C1 | `tests/PassiveDriverTestSupport.cs` | `a40e1d2ea2f8040db74353522b0ce28edc61ea77e6a1a9630be1d0c1d6dd6e23` | `97ac074afa25befbcf2d01c377e92da175894a58` | 775 | 20838 |
| C53C2 | `Core/PassiveDriverInput.cs` | `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` | `4bd5d0ba1200e3971416e361407fa5eac2efd0b4` | 334 | 9447 |
| C53C2 | `tests/PassiveDriverTerminalTests.cs` | `cc3001bee5c239b1a1e3c34fecafa3ad80c379e8c3b2c88b787dfaaae8d74bf9` | `60a8a94fd8d0603b861fb7ccf80a7d20d1697d59` | 2429 | 90700 |

At C51, lifecycle/completion/terminal/aggregate files are absent; at C52 only lifecycle exists; C53 creates the remaining files. `SsrOracle.UnitTests.csproj` remains exactly SHA-256 `f8c5924d6e08cec8c08f7bafde2a5ef874d2bb17739cdfcf4f2b9924e51ff688`, blob `14df214f1e404fa584912ca6b7b074d75a3d3d73`, 12 lines, 362 bytes through C53C2.

## Task 4.2 Ignored-Evidence Closure

Task 5 does not inherit authority to alter Task 4.2's ignored evidence. It proves closure twice: once before Task 5 execution and once immediately before R.

The sealed physical root is repo-relative `.superpowers/sdd/2026-07-31-oracle-passive-plugin`. Its support anchors are exact:

| Path | SHA-256 | LF lines | Bytes |
|---|---|---:|---:|
| `task-4.2-brief.md` | `e32a768a46da5d90077481a520c36e7943339c864db8a4f719b008e7318ae6dd` | 4983 | 179731 |
| `task-4.2-review-correction-r04-brief.md` | `376e3900e6ee50278bc4c3743b67581a948eefb5fdcb29020057bc40e7f6b589` | 202 | 10876 |
| `task-4.2-forced-suite.sh` | `627b108d9c95600f966b00a2517788774cda1eb8bf54b2f4bf4ef56cc9572224` | 74 | 2858 |
| `task-4.2-report.md` | `cb9df2a70fac25b9b370f7eb6450e370938fb8f8baaac6bae366d4a68c6e9581` | 452 | 164470 |
| `progress.md` | `248fa456d57555a7af6c81872190780e471f9177224f04ef5619923c04171cc8` | 699 | 202952 |
| parent policy `.superpowers/sdd/.gitignore` | `cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b` | 1 | 2 |

The four correction namespaces are the C-sorted manifest of `SHA256`, two spaces, and basename plus final LF, including each round brief:

| Namespace | Files | Manifest SHA-256 |
|---|---:|---|
| r01 | 26 | `2dae97f85eff03f60eecdf7e87f517119c91acf8a83c808d74cdf3e6b6f9e640` |
| r02 | 82 | `a085b38274c50e6d93efa7c17ca76cc9afcff88707276bf8ac7786642bb54a73` |
| r03 | 132 | `34f895728843b9541d3ceca818c95fcf1d353619f3e12d7658c20f576c90ea9b` |
| r04 | 134 | `17e8f52e34e80e32859d8002ad76724866707cd7091aa2edd1cd5c5f2ffbd524` |

Exactly 374 correction-namespace files are gated. No gate counts every file in the physical directory.

The closure procedure is descendant-safe and read-only:

- resolve the repository and physical evidence root with `pwd -P`; require the root to equal the repo-relative descendant above and reject a symlink root;
- enumerate only immediate regular, non-symlink descendants matching each correction round plus that round's brief; require every candidate's physical parent to equal the physical root before opening it;
- hash complete bytes of the two ledgers and every support anchor, require exact sizes/line counts, and permit no Task 5 suffix;
- build each C-sorted `SHA256  basename` manifest, require the exact per-round count and digest above, and prove r01/r02/r03 basenames cannot satisfy an r04 basename;
- verify all 374 namespace paths and support anchors are ignored without executing any of them; do not gate any other physical-directory file;
- verify the brief/helper/policy hashes above without executing the helper;
- record only the closure result and aggregate manifest identity in Task 5's external evidence root; and
- repeat the same checks before R, requiring byte-for-byte equality with the Task 0 snapshot.

If the physical ignored evidence is unavailable, incomplete, longer than the frozen size without an already sealed suffix, or mismatched, stop. Do not reconstruct, copy, normalize, truncate, delete, or append it.

## File Responsibility

| File | Task 5 responsibility | First owner |
|---|---|---|
| `oracle/plugin/Core/PassiveDriver.cs` | shared phase, counters, pending-attempt state, fault precedence, output lease, deferred terminal work, and disposal | 5.1, extended by 5.2/5.3/C53C1 |
| `oracle/plugin/Core/PassiveDriverInput.cs` | cardinal/Undo correlation, attempt outcome, settling, every Step write, durable-Step continuation and C53C2 rebase | 5.1 |
| `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs` | Restart stack/depth, StateSet context, post-state replacement, typed/general throw cleanup | 5.2 |
| `oracle/plugin/Core/PassiveDriverCompletion.cs` | expected-count completion claim, End/Close/Complete ordering and post-close reporter failure | 5.3, serialized by C53C1 |
| `oracle/plugin/Core/PassiveDriverBoundaries.cs` | immutable Task 4.2 hook/directive/gate/reporter firewall | unchanged |
| `oracle/plugin/tests/PassiveDriverInputTests.cs` | six 5.1 registrations plus two appended 5.2 registrations; one narrow 5.3 intermediate-only expectation amendment | 5.1 |
| `oracle/plugin/tests/PassiveDriverLifecycleHooks.cs` | no such test file is created; lifecycle cases remain in the two frozen input registrations | n/a |
| `oracle/plugin/tests/PassiveDriverTerminalTests.cs` | six terminal registrations, deterministic output-race barriers, parser-position assertions, and correction REDs | 5.3, extended by C53C1/C53C2 |
| `oracle/plugin/tests/PassiveDriverTestSupport.cs` | complete fake sink/reporter, real NDJSON sink fixtures, deterministic output-entry barriers, no production seam | 5.1, extended by 5.3/C53C1 |
| `oracle/plugin/tests/PassiveDriverTests.cs` | aggregate boundary -> initial -> input -> terminal registration order | 5.3 |
| `oracle/plugin/tests/Program.cs` | exact cohort counts and top-level aggregate registration | 5.1/5.2/5.3 |
| `docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md` | compact final commands/results/provenance/review report only | R |

No production file may absorb test-only barriers, trace-export hooks, or manufactured-state helpers.

## Stable Interfaces

### Inherited interfaces

The complete `HookKind`, `HookToken`, `UpdateDirective`, `GateSample`, `IPassiveReporter`, `IPassiveUpdateObservation`, and `PassiveUpdateBoundary` surface remains byte-identical to D. The constructor continues to validate `expectedInputCount == OracleProtocol.ExpectedInputCount`; Task 5.3 stores that already validated value and does not broaden the schema.

### Task 5.1 additions

```csharp
internal HookToken ProcessInputEntered(
    object stateReference,
    int rawDirection,
    double nowSeconds);
internal void ProcessInputReturned(
    HookToken token,
    bool accepted,
    bool movementScheduled);
internal void ProcessInputThrew(HookToken token);

internal HookToken UndoEntered(
    object stateReference,
    double nowSeconds);
internal void RestoreObserved();
internal void UndoReturned(
    HookToken token,
    bool movementScheduled);
internal void UndoThrew(HookToken token);

internal OracleInput PendingInput { get; }
internal bool PendingAccepted { get; }
internal bool PendingMovementScheduled { get; }
```

Raw direction mapping is exactly `0 -> North`, `1 -> South`, `2 -> West`, `3 -> East`, and `8 -> None`. A cardinal ProcessInput is attributed only inside the matching native poll scope, with exactly one physical poll and one manual call. A second attempt before settlement faults `overlapping_input`; it never finalizes the earlier attempt.

Task 5.1 owns every durable Step. A Step is flushed before a Ready callback; its index is the pre-increment `completedInputs`. After Step durability, attempt/candidate/last-capture state clears and `completedInputs` increments while the output lease still controls the handoff.

### Task 5.2 additions

```csharp
internal HookToken RestartEntered();
internal void RestartReturned(HookToken token);
internal void RestartThrew(HookToken token);

internal HookToken StateSetEntered(
    object beforeState,
    object requestedState);
internal void StateSetReturned(
    HookToken token,
    object afterState,
    double nowSeconds);
internal void StateSetThrew(HookToken token);
internal void ClearThrew(HookToken token);
```

Restart depth is established before its fault can re-enter observers. The outer Restart claims `unexpected_input` with null input fields; nested Restart/Undo/Restore callbacks balance bookkeeping without opening an attempt. StateSet ignores the requested value and judges replacement from the actual post-return object reference. `ClearThrew` dispatches by token kind and cannot clear another context.

### Task 5.3 and correction invariants

After the third durable Step, the driver validates the final count and UTC relation, claims success through the same atomic terminal owner used by ordinary faults, writes End, closes once, enters Done, then calls Complete. The observable success order is exactly:

```text
Step 2 -> End -> Close -> Complete
```

C53C1 introduces one serialized output-lease domain for Run, Initial, every Step, terminal Error/End, Close, and reporter handoff. No driver monitor is held across sink or reporter code. A terminal claim may return while an output callback is blocked, but its Error/Close/Failed work is queued until the in-flight output and its durable state transition finish.

C53C2 fixes the sole protocol hole found in C53C1: if an ordinary fault claims while Step N is in flight and that Step later becomes durable, the pre-Step Error snapshot at index N is stale because the parser is now at position N+1. Under the output lease, C53C2 first clears the attempt and increments the durable Step count, then rebuilds only deferred `OrdinaryFault` work as:

```csharp
new ErrorRecord(
    runId,
    null,
    null,
    deferredTerminalWork.Code,
    0,
    null)
```

The rebase does not touch deferred Dispose or TraceIo work. If the Step write/flush itself fails, queued ordinary fault work is replaced by marker-only `trace_io_failed`; no Error record may claim durability after a compromised Step.

## Frozen Registrations

Registration identities and order are protocol. No correction may rename, reorder, split, merge, or add a registration without a newly approved append-only plan.

`driver-boundary` remains:

1. `hook token is owner bound and single consume`
2. `update directive authorizes rebases and consumes once`

`driver-initial` remains:

1. `prepare activate separation`
2. `pre epoch neutral does not leak`
3. `matching pair writes initial`
4. `not inspected breaks pair`
5. `nonquiescent breaks pair`
6. `cardinal clears candidate`
7. `replacement rebases same callback`
8. `exact deadline and pre overrun`

Task 5.1 creates the first six `driver-input` registrations and Task 5.2 appends the last two:

1. `all cardinals correlate`
2. `filtered and zero poll open no attempt`
3. `duplicate mismatch and unknown fault`
4. `unscoped policy follows phase`
5. `accepted and refused direction outcomes`
6. `Undo acceptance and restore rules`
7. `restart depth and null fields`
8. `state replacement and ClearThrew`

Task 5.3 creates `driver-terminal`:

1. `three steps End Close Complete order`
2. `error field policy is exact`
3. `sink failure uses trace io marker`
4. `completion reporter cannot rewrite trace`
5. `first fault wins race`
6. `Dispose and late callbacks are final`

The final aggregator order is boundary, initial, input, terminal. `Program.cs` registers protocol, encoding/signature, sink, then the driver aggregator, and verifies exactly:

```csharp
{ "protocol", 4 },
{ "encoding", 5 },
{ "sink", 6 },
{ "driver-boundary", 2 },
{ "driver-initial", 8 },
{ "driver-input", 8 },
{ "driver-terminal", 6 }
```

The authorized narrow Task 5.3 amendment changes only the existing helper expectation from “every settled Step reports Ready” to “every intermediate settled Step reports Ready.” It stops after Step 1, expects Ready values `0,1,2`, retains the same `accepted and refused direction outcomes` registration, and transfers the Step-2 terminal branch to the first terminal registration. This is the only Task 5.3 change allowed in `PassiveDriverInputTests.cs`.

## Patch and RED Catalog

The materialized plan must replace every patch marker below with one block containing an exact metadata line, `<!-- PATCH TAG BEGIN -->`, a `diff` fence holding the LF-terminated `git diff --binary --full-index` body, and `<!-- PATCH TAG END -->`. Tags are `C51-TESTS`, `C51-PRODUCTION`, `C52-TESTS`, `C52-PRODUCTION`, `C53-TESTS`, `C53-PRODUCTION`, `C53C1-TESTS`, `C53C1-PRODUCTION`, `C53C2-TESTS`, and `C53C2-PRODUCTION`. Test and production patches are disjoint so every RED is demonstrated before production changes.

At execution, the dispatcher reads P from the authenticated `P.alias` and
snapshots `TASK5_PLAN_COMMIT:TASK5_PLAN_PATH` into the external evidence root.
Use one Apple-Bash-3.2-compatible `awk` extractor that requires exactly one
begin tag, one opening `diff` fence, one closing fence, and one end tag, emits
only the fenced body with final LF, and exits nonzero for a duplicate, missing,
nested, reversed, or unterminated delimiter. Syntax-check the extractor under
`/bin/bash --noprofile --norc -n`. For each extracted patch:

1. require its declared SHA-256, LF-line count, byte count, full-index headers, exact paths, and final LF;
2. run `git apply --check --index patch` and then `git apply --index patch` from its exact predecessor;
3. regenerate `git diff --cached --binary --full-index` for the patch's exact disjoint path set and require byte equality with the extracted patch; and
4. after both halves, regenerate the complete parent-to-result full patch and require the checkpoint identity above.

Pass `task5_extract_and_stage_plan_patch` the runtime-resolved exact parent
HEAD and exact pre-apply index tree. For a tests half, the pre-apply tree must
equal `HEAD^{tree}` with an empty index; for its production half, it must
equal the just-authenticated tests-only index tree with exactly the hardcoded
tests scope already staged. After both halves, call
`task5_authenticate_checkpoint_index` with that checkpoint's exact parent
tree before any GREEN gate or commit. Do not substitute a qualification
scratch root tree for a future runtime-resolved root.

### C51 patches

**C51-TESTS patch:** SHA-256 `27b5d2da89f011a1e3c84a6cb27077ad093e46ab3ac05bb4bef4386c8c73d6eb`; 1213 LF lines; 51384 bytes.
<!-- TASK5-PATCH-BEGIN:C51-TESTS -->
~~~diff
diff --git a/oracle/plugin/tests/PassiveDriverInputTests.cs b/oracle/plugin/tests/PassiveDriverInputTests.cs
new file mode 100644
index 0000000000000000000000000000000000000000..ec2f13dff1e6e2925fd7749592b127928518d7b4
--- /dev/null
+++ b/oracle/plugin/tests/PassiveDriverInputTests.cs
@@ -0,0 +1,1111 @@
+using System;
+
+internal static class PassiveDriverInputTests
+{
+    internal static void Register(TestRegistry tests)
+    {
+        tests.Add("driver-input", "all cardinals correlate",
+            AllCardinalsCorrelate);
+        tests.Add("driver-input", "filtered and zero poll open no attempt",
+            FilteredAndZeroPollOpenNoAttempt);
+        tests.Add("driver-input", "duplicate mismatch and unknown fault",
+            DuplicateMismatchAndUnknownFault);
+        tests.Add("driver-input", "unscoped policy follows phase",
+            UnscopedPolicyFollowsPhase);
+        tests.Add("driver-input", "accepted and refused direction outcomes",
+            AcceptedAndRefusedDirectionOutcomes);
+        tests.Add("driver-input", "Undo acceptance and restore rules",
+            UndoAcceptanceAndRestoreRules);
+    }
+
+    private static void AllCardinalsCorrelate()
+    {
+        int[] raw = new int[] { 0, 1, 2, 3 };
+        OracleInput[] expected = new OracleInput[]
+        {
+            OracleInput.North,
+            OracleInput.South,
+            OracleInput.West,
+            OracleInput.East
+        };
+        for (int index = 0; index < raw.Length; index++)
+        {
+            DriverFixture fixture = DriverFixture.Ready();
+            fixture.OpenDirection(raw[index], true, true, 10.0);
+            Check.Equal(
+                PassivePhase.Settling,
+                fixture.Driver.Phase,
+                "cardinal opens attempt " + index.ToString());
+            Check.Equal(
+                expected[index],
+                fixture.Driver.PendingInput,
+                "mapped cardinal " + index.ToString());
+        }
+    }
+
+    private static void FilteredAndZeroPollOpenNoAttempt()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        HookToken empty = fixture.Driver.PlayerPollEntered();
+        fixture.Driver.PlayerPollReturned(empty);
+        Check.Equal(
+            PassivePhase.Ready,
+            fixture.Driver.Phase,
+            "zero-poll early gate");
+
+        fixture.CardinalOnly(2);
+        Check.Equal(
+            PassivePhase.Ready,
+            fixture.Driver.Phase,
+            "filtered cardinal");
+        Check.Equal(0, fixture.Sink.StepRecords.Count, "no attempt emitted");
+        Check.Equal(0, fixture.Sink.ErrorRecords.Count, "no fault emitted");
+    }
+
+    private static void DuplicateMismatchAndUnknownFault()
+    {
+        DriverFixture duplicate = DriverFixture.Ready();
+        HookToken duplicatePoll =
+            duplicate.Driver.PlayerPollEntered();
+        duplicate.Driver.PhysicalPollReturned(0);
+        duplicate.Driver.PhysicalPollReturned(0);
+        duplicate.Driver.PlayerPollReturned(duplicatePoll);
+        Check.Equal(
+            "hook_order_mismatch",
+            duplicate.Sink.ErrorRecords[0].Code,
+            "second physical poll");
+
+        DriverFixture mismatch = DriverFixture.Ready();
+        HookToken mismatchPoll =
+            mismatch.Driver.PlayerPollEntered();
+        mismatch.Driver.PhysicalPollReturned(0);
+        mismatch.Driver.ProcessInputEntered(
+            mismatch.State, 1, 10.0);
+        mismatch.Driver.PlayerPollReturned(mismatchPoll);
+        ErrorRecord mismatchError = mismatch.Sink.ErrorRecords[0];
+        Check.Equal(
+            "hook_order_mismatch",
+            mismatchError.Code,
+            "argument differs from physical poll");
+        Check.Equal((int?)0, mismatchError.InputIndex,
+            "Ready mismatch next input index");
+        Check.Equal((OracleInput?)OracleInput.South,
+            mismatchError.Input,
+            "Ready mismatch offending ProcessInput argument");
+        Check.Equal(0, mismatchError.SettleFrames,
+            "Ready mismatch has no attempt frames");
+
+        DriverFixture unknown = DriverFixture.Ready();
+        HookToken unknownPoll = unknown.Driver.PlayerPollEntered();
+        unknown.Driver.PhysicalPollReturned(99);
+        unknown.Driver.PlayerPollReturned(unknownPoll);
+        ErrorRecord error = unknown.Sink.ErrorRecords[0];
+        Check.Equal("unexpected_input", error.Code, "unknown direction");
+        Check.Equal((int?)0, error.InputIndex, "next input index");
+        Check.False(error.Input.HasValue, "unknown has null input");
+
+        DriverFixture duringAttempt = DriverFixture.Ready();
+        duringAttempt.OpenDirection(2, true, true, 10.0);
+        duringAttempt.Observe(
+            duringAttempt.State,
+            duringAttempt.State,
+            11.0,
+            false,
+            ProtocolSamples.MovedCapture);
+        HookToken settlingPoll =
+            duringAttempt.Driver.PlayerPollEntered();
+        duringAttempt.Driver.PhysicalPollReturned(99);
+        duringAttempt.Driver.PlayerPollReturned(settlingPoll);
+        ErrorRecord settling = duringAttempt.Sink.ErrorRecords[0];
+        Check.Equal(
+            "unexpected_input",
+            settling.Code,
+            "unknown while settling");
+        Check.Equal(
+            (int?)0,
+            settling.InputIndex,
+            "pending attempt retains its index");
+        Check.Equal(
+            (OracleInput?)OracleInput.West,
+            settling.Input,
+            "pending attempt outranks unknown offending input");
+        Check.Equal(
+            1,
+            settling.SettleFrames,
+            "unknown retains active attempt frame count");
+
+        ScopedInputBeforeInitialFaults();
+        OverlappingInputRetainsAttempt();
+        CardinalCorrelationOrderAndFields();
+        NestedInputOrderFaults();
+    }
+
+    private static void CardinalCorrelationOrderAndFields()
+    {
+        DriverFixture beforePhysical = DriverFixture.Ready();
+        beforePhysical.Driver.PlayerPollEntered();
+        beforePhysical.Driver.ProcessInputEntered(
+            beforePhysical.State, 3, 10.0);
+        ErrorRecord beforePhysicalError =
+            beforePhysical.Sink.ErrorRecords[0];
+        Check.Equal("hook_order_mismatch", beforePhysicalError.Code,
+            "ProcessInput before physical poll code");
+        Check.Equal((int?)0, beforePhysicalError.InputIndex,
+            "ProcessInput before physical poll next index");
+        Check.Equal((OracleInput?)OracleInput.East,
+            beforePhysicalError.Input,
+            "ProcessInput before physical poll mapped argument");
+        Check.Equal(0, beforePhysicalError.SettleFrames,
+            "ProcessInput before physical poll frames");
+
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        Check.Equal(1, awaitingInitial.Driver.CurrentSettleFrames,
+            "AwaitInitialNeutral has one active frame");
+        HookToken awaitingInitialPoll =
+            awaitingInitial.Driver.PlayerPollEntered();
+        awaitingInitial.Driver.PhysicalPollReturned(0);
+        awaitingInitial.Driver.ProcessInputEntered(
+            awaitingInitial.State, 1, 2.0);
+        awaitingInitial.Driver.PlayerPollReturned(
+            awaitingInitialPoll);
+        ErrorRecord awaitingInitialError =
+            awaitingInitial.Sink.ErrorRecords[0];
+        Check.Equal("hook_order_mismatch", awaitingInitialError.Code,
+            "AwaitInitialNeutral mismatch code");
+        Check.Equal((int?)0, awaitingInitialError.InputIndex,
+            "AwaitInitialNeutral mismatch next index");
+        Check.Equal((OracleInput?)OracleInput.South,
+            awaitingInitialError.Input,
+            "AwaitInitialNeutral mismatch mapped argument");
+        Check.Equal(0, awaitingInitialError.SettleFrames,
+            "AwaitInitialNeutral mismatch ignores active frames");
+
+        DriverFixture pending = DriverFixture.Ready();
+        pending.OpenDirection(2, true, true, 10.0);
+        pending.Observe(
+            pending.State,
+            pending.State,
+            11.0,
+            false,
+            ProtocolSamples.MovedCapture);
+        HookToken pendingPoll = pending.Driver.PlayerPollEntered();
+        pending.Driver.PhysicalPollReturned(0);
+        pending.Driver.ProcessInputEntered(
+            pending.State, 1, 12.0);
+        pending.Driver.PlayerPollReturned(pendingPoll);
+        ErrorRecord pendingError = pending.Sink.ErrorRecords[0];
+        Check.Equal("hook_order_mismatch", pendingError.Code,
+            "pending mismatch code");
+        Check.Equal((int?)0, pendingError.InputIndex,
+            "pending mismatch retains attempt index");
+        Check.Equal((OracleInput?)OracleInput.West,
+            pendingError.Input,
+            "pending attempt overrides offending mismatch input");
+        Check.Equal(1, pendingError.SettleFrames,
+            "pending mismatch retains active attempt frames");
+    }
+
+    private static void NestedInputOrderFaults()
+    {
+        DriverFixture secondProcessInput = DriverFixture.Ready();
+        HookToken sharedPoll =
+            secondProcessInput.Driver.PlayerPollEntered();
+        secondProcessInput.Driver.PhysicalPollReturned(2);
+        HookToken firstProcess =
+            secondProcessInput.Driver.ProcessInputEntered(
+                secondProcessInput.State, 2, 10.0);
+        secondProcessInput.Driver.ProcessInputReturned(
+            firstProcess, true, true);
+        secondProcessInput.Driver.ProcessInputEntered(
+            secondProcessInput.State, 2, 11.0);
+        secondProcessInput.Driver.PlayerPollReturned(sharedPoll);
+        Check.Equal("hook_order_mismatch",
+            secondProcessInput.Sink.ErrorRecords[0].Code,
+            "second matching ProcessInput in one poll");
+
+        DriverFixture outerBeforeInner = DriverFixture.Ready();
+        HookToken outer = outerBeforeInner.Driver.PlayerPollEntered();
+        outerBeforeInner.Driver.PhysicalPollReturned(2);
+        HookToken inner = outerBeforeInner.Driver.ProcessInputEntered(
+            outerBeforeInner.State, 2, 10.0);
+        outerBeforeInner.Driver.PlayerPollReturned(outer);
+        Check.Equal(1, outerBeforeInner.Sink.ErrorRecords.Count,
+            "outer poll return with live ProcessInput faults");
+        Check.Equal("hook_order_mismatch",
+            outerBeforeInner.Sink.ErrorRecords[0].Code,
+            "outer poll return before ProcessInput return code");
+        outerBeforeInner.Driver.ProcessInputThrew(inner);
+        outerBeforeInner.Driver.ProcessInputThrew(inner);
+
+        DriverFixture secondUndo = DriverFixture.Ready();
+        secondUndo.Driver.UndoEntered(secondUndo.State, 10.0);
+        secondUndo.Driver.UndoEntered(secondUndo.State, 11.0);
+        Check.Equal("hook_order_mismatch",
+            secondUndo.Sink.ErrorRecords[0].Code,
+            "second live top-level Undo");
+
+        DriverFixture duplicateRestore = DriverFixture.Ready();
+        duplicateRestore.Driver.UndoEntered(
+            duplicateRestore.State, 10.0);
+        duplicateRestore.Driver.RestoreObserved();
+        duplicateRestore.Driver.RestoreObserved();
+        Check.Equal("hook_order_mismatch",
+            duplicateRestore.Sink.ErrorRecords[0].Code,
+            "duplicate Restore");
+    }
+
+    private static void UnscopedPolicyFollowsPhase()
+    {
+        DriverFixture awaitingGame = DriverFixture.Active();
+        HookToken ignoredAwaitingGame =
+            awaitingGame.Driver.ProcessInputEntered(
+                awaitingGame.State, 99, 1.0);
+        awaitingGame.Driver.ProcessInputReturned(
+            ignoredAwaitingGame, true, true);
+        Check.Equal(
+            PassivePhase.AwaitGame,
+            awaitingGame.Driver.Phase,
+            "AwaitGame unscoped unknown ignored");
+        Check.Equal(
+            0,
+            awaitingGame.Sink.ErrorRecords.Count,
+            "AwaitGame unscoped unknown emits no fault");
+
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        HookToken ignoredAwaitingInitial =
+            awaitingInitial.Driver.ProcessInputEntered(
+                awaitingInitial.State, 99, 2.0);
+        awaitingInitial.Driver.ProcessInputReturned(
+            ignoredAwaitingInitial, true, true);
+        Check.Equal(
+            PassivePhase.AwaitInitialNeutral,
+            awaitingInitial.Driver.Phase,
+            "AwaitInitialNeutral unscoped unknown ignored");
+        Check.Equal(
+            0,
+            awaitingInitial.Sink.ErrorRecords.Count,
+            "AwaitInitialNeutral unscoped unknown emits no fault");
+
+        DriverFixture readyCardinal = DriverFixture.Ready();
+        readyCardinal.Driver.ProcessInputEntered(
+            readyCardinal.State, 0, 10.0);
+        ErrorRecord cardinalError =
+            readyCardinal.Sink.ErrorRecords[0];
+        Check.Equal(
+            "unscoped_process_input",
+            cardinalError.Code,
+            "Ready unscoped cardinal code");
+        Check.False(cardinalError.InputIndex.HasValue,
+            "Ready unscoped cardinal index is null");
+        Check.False(cardinalError.Input.HasValue,
+            "Ready unscoped cardinal input is null");
+        Check.Equal(0, cardinalError.SettleFrames,
+            "Ready unscoped cardinal frames are zero");
+
+        DriverFixture readyUnknown = DriverFixture.Ready();
+        readyUnknown.Driver.ProcessInputEntered(
+            readyUnknown.State, 99, 10.0);
+        ErrorRecord unknownError =
+            readyUnknown.Sink.ErrorRecords[0];
+        Check.Equal(
+            "unscoped_process_input",
+            unknownError.Code,
+            "Ready unscoped unknown code");
+        Check.False(unknownError.InputIndex.HasValue,
+            "Ready unscoped unknown index is null");
+        Check.False(unknownError.Input.HasValue,
+            "Ready unscoped unknown input is null");
+        Check.Equal(0, unknownError.SettleFrames,
+            "Ready unscoped unknown frames are zero");
+
+        DriverFixture settling = DriverFixture.Ready();
+        settling.OpenDirection(2, true, true, 10.0);
+        HookToken automatic = settling.Driver.ProcessInputEntered(
+            settling.State, 99, 11.0);
+        settling.Driver.ProcessInputReturned(
+            automatic, true, true);
+        Check.Equal(
+            PassivePhase.Settling,
+            settling.Driver.Phase,
+            "Settling unscoped unknown ignored");
+        Check.Equal(
+            0,
+            settling.Sink.ErrorRecords.Count,
+            "Settling unscoped unknown emits no fault");
+
+        StateIdentityFollowsPhase();
+    }
+
+    private static void AcceptedAndRefusedDirectionOutcomes()
+    {
+        DriverFixture accepted = DriverFixture.Ready();
+        accepted.OpenDirection(2, true, true, 10.0);
+        Check.True(
+            accepted.Driver.PendingAccepted,
+            "exact ProcessInput result");
+        Check.True(
+            accepted.Driver.PendingMovementScheduled,
+            "immediate Moving result");
+        accepted.SettleCurrent(
+            ProtocolSamples.MovedCapture, 11.0);
+        StepRecord first = accepted.Sink.StepRecords[0];
+        Check.Equal(OracleInput.West, first.Input, "west step");
+        Check.True(first.Accepted, "accepted step");
+        Check.True(first.MovementScheduled, "movement scheduled");
+        Check.Equal(2, first.SettleFrames, "two-sample settle");
+
+        DriverFixture refused = DriverFixture.Ready();
+        refused.OpenDirection(0, false, false, 10.0);
+        Check.False(refused.Driver.PendingAccepted, "refused result");
+        Check.False(
+            refused.Driver.PendingMovementScheduled,
+            "no immediate movement");
+        refused.SettleCurrent(
+            ProtocolSamples.InitialCapture, 11.0);
+        StepRecord second = refused.Sink.StepRecords[0];
+        Check.Equal(OracleInput.North, second.Input, "north step");
+        Check.False(second.Accepted, "refused step");
+        Check.False(second.MovementScheduled, "no scheduled movement");
+
+        ValueEqualCapturesSettle();
+        SettlingCandidateBreaksRestartPair();
+        SettlingDeadlineOrderIsExact();
+        PopulatedErrorPreflightRejectsBoundaryCapture();
+        StepFailureIsTerminal();
+        StepPrecedesIntermediateReady();
+        EverySettledStepReportsReady();
+    }
+
+    private static void UndoAcceptanceAndRestoreRules()
+    {
+        DriverFixture accepted = DriverFixture.Ready();
+        accepted.OpenUndo(true, false, 10.0);
+        Check.Equal(
+            OracleInput.Undo,
+            accepted.Driver.PendingInput,
+            "Undo input");
+        Check.True(accepted.Driver.PendingAccepted, "restore accepted");
+        Check.False(
+            accepted.Driver.PendingMovementScheduled,
+            "top-level Moving result");
+
+        DriverFixture refused = DriverFixture.Ready();
+        refused.OpenUndo(false, false, 10.0);
+        Check.False(refused.Driver.PendingAccepted, "no restore refused");
+
+        DriverFixture outside = DriverFixture.Ready();
+        outside.Driver.RestoreObserved();
+        Check.Equal(
+            "hook_order_mismatch",
+            outside.Sink.ErrorRecords[0].Code,
+            "restore outside Undo");
+
+        UndoBeforeInitialFaults();
+        ThrownInputHooksBalance();
+    }
+
+    private static void ThrownInputHooksBalance()
+    {
+        DriverFixture process = DriverFixture.Ready();
+        HookToken poll = process.Driver.PlayerPollEntered();
+        process.Driver.PhysicalPollReturned(2);
+        HookToken processToken = process.Driver.ProcessInputEntered(
+            process.State, 2, 10.0);
+        Check.True(processToken.Active, "ProcessInput throw token active");
+        process.Driver.ProcessInputThrew(processToken);
+        process.Driver.ProcessInputThrew(processToken);
+        Check.Equal(0, process.Sink.ErrorRecords.Count,
+            "repeated ProcessInput cleanup is idempotent");
+        process.Driver.PlayerPollReturned(poll);
+        HookToken secondPoll = process.Driver.PlayerPollEntered();
+        process.Driver.PhysicalPollReturned(0);
+        process.Driver.ProcessInputEntered(
+            process.State, 0, 11.0);
+        process.Driver.PlayerPollReturned(secondPoll);
+        Check.Equal("overlapping_input",
+            process.Sink.ErrorRecords[0].Code,
+            "ProcessInput throw clears context behaviorally");
+
+        DriverFixture undo = DriverFixture.Ready();
+        HookToken undoToken = undo.Driver.UndoEntered(
+            undo.State, 10.0);
+        Check.True(undoToken.Active, "Undo throw token active");
+        undo.Driver.UndoThrew(undoToken);
+        undo.Driver.UndoThrew(undoToken);
+        Check.Equal(0, undo.Sink.ErrorRecords.Count,
+            "repeated Undo cleanup is idempotent");
+        undo.Driver.UndoEntered(undo.State, 11.0);
+        Check.Equal("overlapping_input",
+            undo.Sink.ErrorRecords[0].Code,
+            "Undo throw clears context behaviorally");
+    }
+
+    private static void UndoBeforeInitialFaults()
+    {
+        DriverFixture awaitingGame = DriverFixture.Active();
+        awaitingGame.OpenUndo(false, false, 1.0);
+        Check.Equal(1, awaitingGame.Sink.ErrorRecords.Count,
+            "AwaitGame Undo emits one Error");
+        ErrorRecord first = awaitingGame.Sink.ErrorRecords[0];
+        Check.Equal("input_before_initial", first.Code,
+            "AwaitGame Undo code");
+        Check.Equal((int?)0, first.InputIndex,
+            "AwaitGame Undo next input index");
+        Check.Equal((OracleInput?)OracleInput.Undo, first.Input,
+            "AwaitGame Undo input");
+        Check.Equal(0, first.SettleFrames,
+            "AwaitGame Undo has no settle budget");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:error:input_before_initial",
+                "sink:close",
+                "report:failed:input_before_initial"
+            },
+            awaitingGame.Events.GetRange(
+                awaitingGame.Events.Count - 3, 3).ToArray(),
+            "AwaitGame Undo failure order");
+
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        Check.Equal(PassivePhase.AwaitInitialNeutral,
+            awaitingInitial.Driver.Phase,
+            "Undo fixture awaits Initial");
+        awaitingInitial.OpenUndo(false, false, 2.0);
+        Check.Equal(1, awaitingInitial.Sink.ErrorRecords.Count,
+            "AwaitInitialNeutral Undo emits one Error");
+        ErrorRecord second = awaitingInitial.Sink.ErrorRecords[0];
+        Check.Equal("input_before_initial", second.Code,
+            "AwaitInitialNeutral Undo code");
+        Check.Equal((int?)0, second.InputIndex,
+            "AwaitInitialNeutral Undo next input index");
+        Check.Equal((OracleInput?)OracleInput.Undo, second.Input,
+            "AwaitInitialNeutral Undo input");
+        Check.Equal(0, second.SettleFrames,
+            "AwaitInitialNeutral Undo has no settle budget");
+    }
+
+    private static void ScopedInputBeforeInitialFaults()
+    {
+        DriverFixture awaitingGame = DriverFixture.Active();
+        HookToken firstPoll = awaitingGame.Driver.PlayerPollEntered();
+        awaitingGame.Driver.PhysicalPollReturned(0);
+        HookToken firstProcess = awaitingGame.Driver.ProcessInputEntered(
+            awaitingGame.State, 0, 1.0);
+        awaitingGame.Driver.ProcessInputReturned(
+            firstProcess, true, true);
+        awaitingGame.Driver.PlayerPollReturned(firstPoll);
+        ErrorRecord first = awaitingGame.Sink.ErrorRecords[0];
+        Check.Equal("input_before_initial", first.Code,
+            "AwaitGame scoped input code");
+        Check.Equal((int?)0, first.InputIndex,
+            "AwaitGame next input index");
+        Check.Equal((OracleInput?)OracleInput.North, first.Input,
+            "AwaitGame mapped input");
+        Check.Equal(0, first.SettleFrames,
+            "AwaitGame has no settle budget");
+
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        HookToken secondPoll =
+            awaitingInitial.Driver.PlayerPollEntered();
+        awaitingInitial.Driver.PhysicalPollReturned(3);
+        HookToken secondProcess =
+            awaitingInitial.Driver.ProcessInputEntered(
+                awaitingInitial.State, 3, 2.0);
+        awaitingInitial.Driver.ProcessInputReturned(
+            secondProcess, true, true);
+        awaitingInitial.Driver.PlayerPollReturned(secondPoll);
+        ErrorRecord second = awaitingInitial.Sink.ErrorRecords[0];
+        Check.Equal("input_before_initial", second.Code,
+            "AwaitInitialNeutral scoped input code");
+        Check.Equal((OracleInput?)OracleInput.East, second.Input,
+            "AwaitInitialNeutral mapped input");
+        Check.Equal(0, second.SettleFrames,
+            "offending input has no attempt frame override");
+    }
+
+    private static void OverlappingInputRetainsAttempt()
+    {
+        DriverFixture direction = DriverFixture.Ready();
+        direction.OpenDirection(2, true, true, 10.0);
+        HookToken poll = direction.Driver.PlayerPollEntered();
+        direction.Driver.PhysicalPollReturned(0);
+        HookToken process = direction.Driver.ProcessInputEntered(
+            direction.State, 0, 11.0);
+        direction.Driver.ProcessInputReturned(process, true, true);
+        direction.Driver.PlayerPollReturned(poll);
+        ErrorRecord first = direction.Sink.ErrorRecords[0];
+        Check.Equal("overlapping_input", first.Code,
+            "second direction code");
+        Check.Equal((int?)0, first.InputIndex,
+            "pending attempt index wins");
+        Check.Equal((OracleInput?)OracleInput.West, first.Input,
+            "pending attempt input wins");
+        Check.Equal(0, first.SettleFrames,
+            "no update committed yet");
+
+        DriverFixture undo = DriverFixture.Ready();
+        undo.OpenDirection(2, true, true, 10.0);
+        HookToken undoToken = undo.Driver.UndoEntered(
+            undo.State, 11.0);
+        undo.Driver.UndoReturned(undoToken, false);
+        Check.Equal("overlapping_input",
+            undo.Sink.ErrorRecords[0].Code,
+            "overlapping Undo code");
+        Check.Equal((OracleInput?)OracleInput.West,
+            undo.Sink.ErrorRecords[0].Input,
+            "Undo cannot replace pending direction");
+    }
+
+    private static void StateIdentityFollowsPhase()
+    {
+        DriverFixture manual = DriverFixture.Ready();
+        HookToken poll = manual.Driver.PlayerPollEntered();
+        manual.Driver.PhysicalPollReturned(2);
+        HookToken process = manual.Driver.ProcessInputEntered(
+            manual.OtherState, 2, 10.0);
+        manual.Driver.ProcessInputReturned(process, true, true);
+        manual.Driver.PlayerPollReturned(poll);
+        ErrorRecord manualError = manual.Sink.ErrorRecords[0];
+        Check.Equal("state_replaced", manualError.Code,
+            "attempt must open on stable reference");
+        Check.False(manualError.InputIndex.HasValue,
+            "rejected attempt never becomes pending");
+
+        DriverFixture ready = DriverFixture.Ready();
+        FakeUpdateObservation readyObservation = ready.Observe(
+            ready.State,
+            true,
+            ready.OtherState,
+            true,
+            10.0,
+            true,
+            ProtocolSamples.MovedCapture);
+        Check.Equal("state_replaced", ready.Sink.ErrorRecords[0].Code,
+            "Ready re-read identity");
+        Check.Equal(0, readyObservation.GateCalls,
+            "Ready replacement faults before gate");
+
+        DriverFixture settling = DriverFixture.Ready();
+        settling.OpenDirection(2, true, true, 10.0);
+        FakeUpdateObservation settlingObservation = settling.Observe(
+            settling.State,
+            true,
+            settling.OtherState,
+            true,
+            11.0,
+            true,
+            ProtocolSamples.MovedCapture);
+        ErrorRecord settlingError = settling.Sink.ErrorRecords[0];
+        Check.Equal("state_replaced", settlingError.Code,
+            "Settling re-read identity");
+        Check.Equal((OracleInput?)OracleInput.West,
+            settlingError.Input,
+            "Settling replacement retains pending input");
+        Check.Equal(1, settlingError.SettleFrames,
+            "Settling replacement retains committed frame");
+        Check.Equal(0, settlingObservation.GateCalls,
+            "Settling replacement faults before gate");
+    }
+
+    private static void ValueEqualCapturesSettle()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.Neutral();
+        CaptureRecord first = ProtocolSamples.Capture("equal-attempt");
+        CaptureRecord equal = ProtocolSamples.Capture("equal-attempt");
+        Check.False(Object.ReferenceEquals(first, equal),
+            "fixture captures are distinct objects");
+        fixture.Observe(fixture.State, fixture.State, 11.0, true, first);
+        Check.Equal(0, fixture.Sink.StepRecords.Count,
+            "first value is only a candidate");
+        fixture.Observe(fixture.State, fixture.State, 12.0, true, equal);
+        Check.Equal(1, fixture.Sink.StepRecords.Count,
+            "equal complete value settles");
+        Check.Same(equal, fixture.Sink.StepRecords[0].Capture,
+            "newest matching capture is written");
+        Check.Equal(2, fixture.Sink.StepRecords[0].SettleFrames,
+            "two distinct update samples");
+    }
+
+    private static void SettlingCandidateBreaksRestartPair()
+    {
+        CaptureRecord first = ProtocolSamples.Capture("pair-a");
+        CaptureRecord second = ProtocolSamples.Capture("pair-b");
+
+        DriverFixture notInspectedControl = DriverFixture.Ready();
+        notInspectedControl.OpenDirection(2, true, true, 10.0);
+        notInspectedControl.Neutral();
+        notInspectedControl.Observe(
+            notInspectedControl.State,
+            notInspectedControl.State,
+            11.0,
+            true,
+            ProtocolSamples.Capture("not-inspected-control"));
+        notInspectedControl.Observe(
+            notInspectedControl.State,
+            notInspectedControl.State,
+            12.0,
+            true,
+            ProtocolSamples.Capture("not-inspected-control"));
+        Check.Equal(1, notInspectedControl.Sink.StepRecords.Count,
+            "control settles without defensive neutral change");
+
+        DriverFixture notInspected = DriverFixture.Ready();
+        notInspected.OpenDirection(2, true, true, 10.0);
+        FakeUpdateObservation skipped = notInspected.Observe(
+            notInspected.State,
+            notInspected.State,
+            12.0,
+            true,
+            ProtocolSamples.Capture("not-inspected-value"));
+        Check.Equal(0, skipped.GateCalls,
+            "settling NotInspected skips gate");
+        Check.Equal(0, skipped.CaptureCalls,
+            "settling NotInspected skips capture");
+        notInspected.Neutral();
+        notInspected.Observe(
+            notInspected.State,
+            notInspected.State,
+            13.0,
+            true,
+            ProtocolSamples.Capture("not-inspected-value"));
+        Check.Equal(0, notInspected.Sink.StepRecords.Count,
+            "first fresh eligible capture does not settle");
+        notInspected.Observe(
+            notInspected.State,
+            notInspected.State,
+            14.0,
+            true,
+            ProtocolSamples.Capture("not-inspected-value"));
+        Check.Equal(1, notInspected.Sink.StepRecords.Count,
+            "fresh pair settles after NotInspected");
+
+        DriverFixture unequal = DriverFixture.Ready();
+        unequal.OpenDirection(2, true, true, 10.0);
+        unequal.Neutral();
+        unequal.Observe(unequal.State, unequal.State, 11.0, true, first);
+        unequal.Observe(unequal.State, unequal.State, 12.0, true, second);
+        Check.Equal(0, unequal.Sink.StepRecords.Count,
+            "unequal capture replaces candidate");
+        unequal.Observe(unequal.State, unequal.State, 13.0, true,
+            ProtocolSamples.Capture("pair-b"));
+        Check.Equal(1, unequal.Sink.StepRecords.Count,
+            "replacement candidate needs its own match");
+        Check.Equal(3, unequal.Sink.StepRecords[0].SettleFrames,
+            "unequal sample remains a committed frame");
+
+        DriverFixture nonquiescent = DriverFixture.Ready();
+        nonquiescent.OpenDirection(2, true, true, 10.0);
+        nonquiescent.Neutral();
+        nonquiescent.Observe(
+            nonquiescent.State, nonquiescent.State, 11.0, true, first);
+        nonquiescent.Observe(
+            nonquiescent.State, nonquiescent.State, 12.0, false, first);
+        nonquiescent.Observe(
+            nonquiescent.State, nonquiescent.State, 13.0, true, first);
+        Check.Equal(0, nonquiescent.Sink.StepRecords.Count,
+            "nonquiescent sample clears candidate");
+        nonquiescent.Observe(
+            nonquiescent.State, nonquiescent.State, 14.0, true, first);
+        Check.Equal(1, nonquiescent.Sink.StepRecords.Count,
+            "post-break pair settles");
+
+        DriverFixture cardinal = DriverFixture.Ready();
+        cardinal.OpenDirection(2, true, true, 10.0);
+        cardinal.Neutral();
+        cardinal.Observe(cardinal.State, cardinal.State, 11.0, true, first);
+        cardinal.CardinalOnly(0);
+        cardinal.Neutral();
+        cardinal.Observe(cardinal.State, cardinal.State, 12.0, true, first);
+        Check.Equal(0, cardinal.Sink.StepRecords.Count,
+            "cardinal poll clears candidate");
+        cardinal.Observe(cardinal.State, cardinal.State, 13.0, true, first);
+        Check.Equal(1, cardinal.Sink.StepRecords.Count,
+            "new neutral pair settles");
+    }
+
+    private static void SettlingDeadlineOrderIsExact()
+    {
+        CaptureRecord capture = ProtocolSamples.Capture("deadline");
+
+        DriverFixture exactFrame = DriverFixture.Active(3, 30.0);
+        ReadyForCustomBudget(exactFrame);
+        exactFrame.OpenDirection(2, true, true, 10.0);
+        exactFrame.Observe(
+            exactFrame.State, exactFrame.State, 10.5, true, capture);
+        exactFrame.Neutral();
+        exactFrame.Observe(
+            exactFrame.State, exactFrame.State, 11.0, true, capture);
+        exactFrame.Observe(
+            exactFrame.State, exactFrame.State, 12.0, true,
+            ProtocolSamples.Capture("deadline"));
+        Check.Equal(1, exactFrame.Sink.StepRecords.Count,
+            "matching pair wins on frame cap");
+        Check.Equal(3, exactFrame.Sink.StepRecords[0].SettleFrames,
+            "frame cap is included");
+
+        DriverFixture exactTime = DriverFixture.Ready();
+        exactTime.OpenDirection(2, true, true, 10.0);
+        exactTime.Neutral();
+        exactTime.Observe(
+            exactTime.State, exactTime.State, 39.0, true, capture);
+        exactTime.Observe(
+            exactTime.State, exactTime.State, 40.0, true,
+            ProtocolSamples.Capture("deadline"));
+        Check.Equal(1, exactTime.Sink.StepRecords.Count,
+            "matching pair wins at exact time deadline");
+
+        DriverFixture exactTimeFailure = DriverFixture.Ready();
+        exactTimeFailure.OpenDirection(2, true, true, 10.0);
+        exactTimeFailure.Neutral();
+        exactTimeFailure.Observe(
+            exactTimeFailure.State,
+            exactTimeFailure.State,
+            39.0,
+            true,
+            ProtocolSamples.Capture("time-deadline-a"));
+        CaptureRecord timeDeadlineLast =
+            ProtocolSamples.Capture("time-deadline-b");
+        FakeUpdateObservation exactTimeFailureObservation =
+            exactTimeFailure.Observe(
+                exactTimeFailure.State,
+                exactTimeFailure.State,
+                40.0,
+                true,
+                timeDeadlineLast);
+        Check.Equal(1, exactTimeFailure.Sink.ErrorRecords.Count,
+            "unmatched exact time deadline emits one Error");
+        ErrorRecord exactTimeError =
+            exactTimeFailure.Sink.ErrorRecords[0];
+        Check.Equal("settle_timeout", exactTimeError.Code,
+            "unmatched exact time deadline faults after sample");
+        Check.Equal(2, exactTimeError.SettleFrames,
+            "exact time deadline keeps committed frame count");
+        Check.Same(timeDeadlineLast, exactTimeError.LastCapture,
+            "exact time deadline retains sampled capture");
+        Check.Equal(1, exactTimeFailureObservation.CaptureCalls,
+            "exact time deadline is sampled before failure");
+
+        DriverFixture postSample = DriverFixture.Active(3, 30.0);
+        ReadyForCustomBudget(postSample);
+        postSample.OpenDirection(2, true, true, 10.0);
+        postSample.Neutral();
+        postSample.Observe(
+            postSample.State, postSample.State, 11.0, true, capture);
+        CaptureRecord middle = ProtocolSamples.Capture("deadline-middle");
+        postSample.Observe(
+            postSample.State, postSample.State, 12.0, true, middle);
+        CaptureRecord last = ProtocolSamples.Capture("deadline-final");
+        FakeUpdateObservation lastObservation = postSample.Observe(
+            postSample.State, postSample.State, 13.0, true, last);
+        Check.Equal(1, postSample.Sink.ErrorRecords.Count,
+            "unmatched frame cap emits one Error");
+        ErrorRecord postSampleError = postSample.Sink.ErrorRecords[0];
+        Check.Equal("settle_timeout", postSampleError.Code,
+            "unmatched cap faults after sample");
+        Check.Equal(3, postSampleError.SettleFrames,
+            "post-sample cap frame count");
+        Check.Same(last, postSampleError.LastCapture,
+            "cap sample becomes last_capture");
+        Check.Equal(1, lastObservation.CaptureCalls,
+            "cap update was sampled");
+
+        DriverFixture preOverrun = DriverFixture.Ready();
+        preOverrun.OpenDirection(2, true, true, 10.0);
+        preOverrun.Neutral();
+        FakeUpdateObservation overrunObservation = preOverrun.Observe(
+            preOverrun.State,
+            preOverrun.State,
+            40.0001,
+            true,
+            capture);
+        Check.Equal(1, preOverrun.Sink.ErrorRecords.Count,
+            "time overrun emits one Error");
+        ErrorRecord overrun = preOverrun.Sink.ErrorRecords[0];
+        Check.Equal("settle_timeout", overrun.Code,
+            "time overrun faults before sample");
+        Check.Equal(1, overrun.SettleFrames,
+            "pre-overrun reports bounded next frame");
+        Check.Equal(0, overrunObservation.PathCalls,
+            "pre-overrun precedes save-path verification");
+        Check.Equal(0, overrunObservation.CaptureCalls,
+            "pre-overrun precedes capture");
+
+        DriverFixture capped = DriverFixture.Ready();
+        capped.OpenDirection(2, true, true, 10.0);
+        capped.SetCurrentFramesForDefensiveTest(600);
+        FakeUpdateObservation cappedObservation = capped.Observe(
+            capped.State, capped.State, 11.0, true, capture);
+        Check.Equal(1, capped.Sink.ErrorRecords.Count,
+            "frame overrun emits one Error");
+        Check.Equal("settle_timeout",
+            capped.Sink.ErrorRecords[0].Code,
+            "frame overrun code");
+        Check.Equal(600, capped.Sink.ErrorRecords[0].SettleFrames,
+            "frame overrun is capped at protocol maximum");
+        Check.Equal(0, cappedObservation.PathCalls,
+            "capped overrun is pre-sample");
+        Check.Equal(0, cappedObservation.CaptureCalls,
+            "capped overrun never captures");
+    }
+
+    private static void StepFailureIsTerminal()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.Sink.StepFailure = new TraceIoException("step");
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            "Step I/O failure faults");
+        Check.Equal(1, fixture.Sink.StepCalls, "one Step attempt");
+        Check.Equal(0, fixture.Sink.StepRecords.Count,
+            "failed Step is not claimed durable");
+        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
+            "Step I/O failure cannot claim Error durability");
+        Check.Equal(1, fixture.Sink.CloseCalls, "sink closed once");
+        Check.Equal(1, fixture.Reporter.FailedCodes.Count,
+            "one trace I/O marker");
+        Check.Equal("trace_io_failed",
+            fixture.Reporter.FailedCodes[0],
+            "trace I/O marker");
+        int tail = fixture.Events.Count - 3;
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:0",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            fixture.Events.GetRange(tail, 3).ToArray(),
+            "Step failure order");
+    }
+
+    private static void PopulatedErrorPreflightRejectsBoundaryCapture()
+    {
+        string[] codes = new string[]
+        {
+            "patch_install_failed",
+            "input_before_initial",
+            "overlapping_input",
+            "unexpected_input",
+            "unscoped_process_input",
+            "hook_order_mismatch",
+            "game_method_exception",
+            "observer_exception",
+            "capture_failed",
+            "record_too_large",
+            "initial_settle_timeout",
+            "settle_timeout",
+            "state_replaced",
+            "save_path_changed"
+        };
+        CaptureRecord empty = ProtocolSamples.Capture(String.Empty);
+        string longestCode = null;
+        int longestNullLength = -1;
+        for (int index = 0; index < codes.Length; index++)
+        {
+            int length = CanonicalJson.EncodeError(
+                new ErrorRecord(
+                    ProtocolSamples.RunId,
+                    null,
+                    null,
+                    codes[index],
+                    OracleProtocol.MaxSettleFrames,
+                    empty)).Length;
+            if (length > longestNullLength)
+            {
+                longestNullLength = length;
+                longestCode = codes[index];
+            }
+        }
+
+        const int MaximumEncodedRecordBytes = 16 * 1024 * 1024 - 1;
+        CaptureRecord boundary = ProtocolSamples.Capture(
+            new string(
+                'x', MaximumEncodedRecordBytes - longestNullLength));
+        Check.Equal(
+            MaximumEncodedRecordBytes,
+            CanonicalJson.EncodeError(
+                new ErrorRecord(
+                    ProtocolSamples.RunId,
+                    null,
+                    null,
+                    longestCode,
+                    OracleProtocol.MaxSettleFrames,
+                    boundary)).Length,
+            "all-null Error boundary fits");
+        Check.Throws<RecordTooLargeException>(
+            delegate
+            {
+                CanonicalJson.EncodeError(
+                    new ErrorRecord(
+                        ProtocolSamples.RunId,
+                        Int32.MaxValue,
+                        OracleInput.North,
+                        longestCode,
+                        OracleProtocol.MaxSettleFrames,
+                        boundary));
+            },
+            "populated Error boundary exceeds line limit");
+
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.Neutral();
+        FakeUpdateObservation observation = fixture.Observe(
+            fixture.State,
+            fixture.State,
+            11.0,
+            true,
+            boundary);
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            "populated Error preflight rejects boundary capture");
+        Check.Equal("record_too_large",
+            fixture.Sink.ErrorRecords[0].Code,
+            "populated Error preflight classification");
+        Check.True(fixture.Sink.ErrorRecords[0].LastCapture == null,
+            "populated Error preflight precedes last_capture");
+        Check.Equal(1, observation.CaptureCalls,
+            "boundary capture was authorized");
+    }
+
+    private static void StepPrecedesIntermediateReady()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
+        Check.Equal(PassivePhase.Ready, fixture.Driver.Phase,
+            "step returns to Ready");
+        Check.Equal(2, fixture.Reporter.ReadyValues.Count,
+            "initial and progress markers");
+        Check.Equal(1, fixture.Reporter.ReadyValues[1],
+            "first completed input count");
+        int tail = fixture.Events.Count - 2;
+        Check.Sequence(
+            new string[] { "sink:step:0", "report:ready:1/3" },
+            fixture.Events.GetRange(tail, 2).ToArray(),
+            "durable Step precedes progress marker");
+
+        DriverFixture failure = DriverFixture.Ready();
+        failure.Reporter.ReadyFailure =
+            new InvalidOperationException("ready marker");
+        failure.OpenDirection(2, true, true, 10.0);
+        failure.SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
+        Check.Equal(1, failure.Sink.StepRecords.Count,
+            "Step remains durable when Ready fails");
+        Check.Equal("observer_exception",
+            failure.Sink.ErrorRecords[0].Code,
+            "Ready exception is observed");
+        Check.True(failure.Sink.ErrorRecords[0].LastCapture == null,
+            "completed epoch capture is cleared before marker");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:0",
+                "report:ready:1/3",
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:observer_exception"
+            },
+            failure.Events.GetRange(
+                failure.Events.Count - 5, 5).ToArray(),
+            "progress failure ordering");
+    }
+
+    private static void ReadyForCustomBudget(DriverFixture fixture)
+    {
+        fixture.Observe(
+            fixture.State,
+            true,
+            fixture.State,
+            true,
+            1.0,
+            true,
+            ProtocolSamples.Capture("custom-ready-a"));
+        fixture.Neutral();
+        fixture.Observe(
+            fixture.State,
+            true,
+            fixture.State,
+            true,
+            2.0,
+            true,
+            ProtocolSamples.Capture("custom-ready-pair"));
+        fixture.Observe(
+            fixture.State,
+            true,
+            fixture.State,
+            true,
+            3.0,
+            true,
+            ProtocolSamples.Capture("custom-ready-pair"));
+        Check.Equal(PassivePhase.Ready, fixture.Driver.Phase,
+            "custom-budget ready fixture");
+    }
+
+    private static void EverySettledStepReportsReady()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.SettleCurrent(
+            ProtocolSamples.Capture("step-zero"), 11.0);
+
+        fixture.OpenDirection(0, false, false, 20.0);
+        fixture.SettleCurrent(
+            ProtocolSamples.Capture("step-one"), 21.0);
+
+        fixture.OpenUndo(true, false, 30.0);
+        fixture.SettleCurrent(
+            ProtocolSamples.Capture("step-two"), 31.0);
+
+        Check.Equal(3, fixture.Sink.StepRecords.Count,
+            "three settled attempts write three Steps");
+        Check.Equal(0, fixture.Sink.StepRecords[0].InputIndex,
+            "Step 0 index");
+        Check.Equal(1, fixture.Sink.StepRecords[1].InputIndex,
+            "Step 1 index");
+        Check.Equal(2, fixture.Sink.StepRecords[2].InputIndex,
+            "Step 2 index");
+        Check.Equal(4, fixture.Reporter.ReadyValues.Count,
+            "Initial and every Step report Ready");
+        Check.Equal(1, fixture.Reporter.ReadyValues[1],
+            "Step 0 reports Ready(1)");
+        Check.Equal(2, fixture.Reporter.ReadyValues[2],
+            "Step 1 reports Ready(2)");
+        Check.Equal(3, fixture.Reporter.ReadyValues[3],
+            "Step 2 reports Ready(3)");
+        Check.Equal(PassivePhase.Ready, fixture.Driver.Phase,
+            "Task 5.1 Step 2 remains Ready");
+        Check.Sequence(
+            new string[] { "sink:step:2", "report:ready:3/3" },
+            fixture.Events.GetRange(
+                fixture.Events.Count - 2, 2).ToArray(),
+            "Step 2 is durable before Ready(3)");
+    }
+
+}
diff --git a/oracle/plugin/tests/PassiveDriverTestSupport.cs b/oracle/plugin/tests/PassiveDriverTestSupport.cs
index d089f8514b450384a6f72080d3bde2cea5218d38..973127b67e1e5f7d760696f3f82f61ad144272c7 100644
--- a/oracle/plugin/tests/PassiveDriverTestSupport.cs
+++ b/oracle/plugin/tests/PassiveDriverTestSupport.cs
@@ -23,6 +23,7 @@ internal sealed class FakeTraceSink : ITraceSink
         new List<ErrorRecord>();
     internal Exception RunFailure { get; set; }
     internal Exception InitialFailure { get; set; }
+    internal Exception StepFailure { get; set; }
     internal Exception ErrorFailure { get; set; }
     internal Exception CloseFailure { get; set; }
     internal int RunCalls;
@@ -53,7 +54,9 @@ internal sealed class FakeTraceSink : ITraceSink
     public void WriteStep(StepRecord record)
     {
         StepCalls++;
-        Add("sink:step");
+        Add("sink:step:" + record.InputIndex.ToString());
+        if (StepFailure != null)
+            throw StepFailure;
         StepRecords.Add(record);
     }
 
@@ -473,3 +476,51 @@ internal sealed partial class DriverFixture
         return field;
     }
 }
+
+internal sealed partial class DriverFixture
+{
+    internal void OpenDirection(
+        int rawDirection,
+        bool accepted,
+        bool movementScheduled,
+        double nowSeconds)
+    {
+        HookToken poll = Driver.PlayerPollEntered();
+        Driver.PhysicalPollReturned(rawDirection);
+        HookToken process = Driver.ProcessInputEntered(
+            State, rawDirection, nowSeconds);
+        Driver.ProcessInputReturned(
+            process, accepted, movementScheduled);
+        Driver.PlayerPollReturned(poll);
+    }
+
+    internal void OpenUndo(
+        bool restored,
+        bool movementScheduled,
+        double nowSeconds)
+    {
+        HookToken undo = Driver.UndoEntered(State, nowSeconds);
+        if (restored)
+            Driver.RestoreObserved();
+        Driver.UndoReturned(undo, movementScheduled);
+    }
+
+    internal void SettleCurrent(
+        CaptureRecord capture,
+        double firstUpdateSeconds)
+    {
+        Neutral();
+        Observe(
+            State,
+            State,
+            firstUpdateSeconds,
+            true,
+            capture);
+        Observe(
+            State,
+            State,
+            firstUpdateSeconds + 1.0,
+            true,
+            capture);
+    }
+}
diff --git a/oracle/plugin/tests/Program.cs b/oracle/plugin/tests/Program.cs
index 386f79c6cfb6b5b4100c413c2802b2191f1b79e3..b89c789b98c2f6872521d0c3655ed32af168220a 100644
--- a/oracle/plugin/tests/Program.cs
+++ b/oracle/plugin/tests/Program.cs
@@ -15,13 +15,15 @@ private static int Main(string[] args)
         TraceSinkTests.Register(tests);
         PassiveDriverBoundaryTests.Register(tests);
         PassiveDriverInitialTests.Register(tests);
+        PassiveDriverInputTests.Register(tests);
         tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
         {
             { "protocol", 4 },
             { "encoding", 5 },
             { "sink", 6 },
             { "driver-boundary", 2 },
-            { "driver-initial", 8 }
+            { "driver-initial", 8 },
+            { "driver-input", 6 }
         });
         int result = tests.Run(options.Cohort);
         if (result != 0)
~~~
<!-- TASK5-PATCH-END:C51-TESTS -->

**C51-PRODUCTION patch:** SHA-256 `dc60e234556f4cd5717dab1422c18edc63e42a87046200c135ff5f8fc32755c0`; 752 LF lines; 23537 bytes.
<!-- TASK5-PATCH-BEGIN:C51-PRODUCTION -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index 16ae4d36bc03bfb9d4e3b4948d5b356709f66636..9227970d1ea6a2d20420bf42a24d51318a301184 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -1,7 +1,7 @@
 using System;
 using System.Threading;
 
-internal sealed class PassiveDriver : IDisposable
+internal sealed partial class PassiveDriver : IDisposable
 {
     private static readonly string[] RecordErrorCodes =
         new string[]
@@ -26,10 +26,15 @@ internal sealed class PassiveDriver : IDisposable
     {
         internal long Id;
         internal bool SawPhysicalPoll;
+        internal int RawDirection;
+        internal bool SawManualProcessInput;
     }
 
     private struct FaultRequest
     {
+        internal bool HasOffendingInput;
+        internal int? OffendingIndex;
+        internal OracleInput? OffendingInput;
         internal int? FrameOverride;
 
         internal static FaultRequest Derived()
@@ -43,6 +48,17 @@ internal sealed class PassiveDriver : IDisposable
             value.FrameOverride = frames;
             return value;
         }
+
+        internal static FaultRequest Offending(
+            int index,
+            OracleInput? input)
+        {
+            FaultRequest value = new FaultRequest();
+            value.HasOffendingInput = true;
+            value.OffendingIndex = index;
+            value.OffendingInput = input;
+            return value;
+        }
     }
 
     private readonly ITraceSink sink;
@@ -61,17 +77,27 @@ internal sealed class PassiveDriver : IDisposable
 
     private string runId;
     private DateTime startedAtUtc;
+    private int completedInputs;
     private long nextHookId;
     private long nextUpdateId;
     private long epoch;
     private UpdateDirective outstandingUpdate;
 
     private object epochState;
+    private object stableState;
     private double epochStartedAt;
     private int currentFrames;
     private bool neutralSeen;
     private byte[] candidateSignature;
     private CaptureRecord lastCapture;
+
+    private bool attemptPending;
+    private bool attemptOutcomeKnown;
+    private OracleInput attemptInput;
+    private bool attemptAccepted;
+    private bool attemptMovementScheduled;
+    private object attemptState;
+
     private PlayerPollContext playerPoll;
 
     internal PassiveDriver(
@@ -120,9 +146,45 @@ internal sealed class PassiveDriver : IDisposable
         get { return startedAtUtc; }
     }
 
+    internal OracleInput PendingInput
+    {
+        get
+        {
+            if (!attemptPending)
+                throw new InvalidOperationException("no pending attempt");
+            return attemptInput;
+        }
+    }
+
+    internal bool PendingAccepted
+    {
+        get
+        {
+            if (!attemptOutcomeKnown)
+            {
+                throw new InvalidOperationException(
+                    "attempt outcome is unavailable");
+            }
+            return attemptAccepted;
+        }
+    }
+
+    internal bool PendingMovementScheduled
+    {
+        get
+        {
+            if (!attemptOutcomeKnown)
+            {
+                throw new InvalidOperationException(
+                    "attempt outcome is unavailable");
+            }
+            return attemptMovementScheduled;
+        }
+    }
+
     internal bool UpdateObservationActive
     {
-        get { return IsInitialObservationActive(); }
+        get { return IsObservationActive(); }
     }
 
     internal bool Prepare(RunRecord run)
@@ -176,7 +238,7 @@ internal sealed class PassiveDriver : IDisposable
         bool usableGame,
         double nowSeconds)
     {
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
             return UpdateDirective.Inactive(this);
         if (!IsValidMonotonic(nowSeconds))
         {
@@ -204,7 +266,8 @@ internal sealed class PassiveDriver : IDisposable
         int settleFrames = 0;
         bool inspectGate = false;
         bool timeoutAfterSample = false;
-        if (phase == PassivePhase.AwaitInitialNeutral)
+        if (phase == PassivePhase.AwaitInitialNeutral
+            || phase == PassivePhase.Settling)
         {
             if (nowSeconds < epochStartedAt)
             {
@@ -217,8 +280,12 @@ internal sealed class PassiveDriver : IDisposable
             if (nextFrames > maxSettleFrames
                 || elapsed > maxSettleSeconds)
             {
+                string code =
+                    phase == PassivePhase.AwaitInitialNeutral
+                    ? "initial_settle_timeout"
+                    : "settle_timeout";
                 TryFaultInternal(
-                    "initial_settle_timeout",
+                    code,
                     FaultRequest.DerivedWithFrames(
                         Math.Min(nextFrames, maxSettleFrames)));
                 return UpdateDirective.Inactive(this);
@@ -261,7 +328,7 @@ internal sealed class PassiveDriver : IDisposable
                 "hook_order_mismatch", FaultRequest.Derived());
             return false;
         }
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
         {
             ConsumeAuthorizedDirective(directive);
             return false;
@@ -316,8 +383,20 @@ internal sealed class PassiveDriver : IDisposable
             return true;
         }
 
-        ConsumeAuthorizedDirective(directive);
-        return false;
+        object expectedState =
+            phase == PassivePhase.Settling
+            ? attemptState
+            : stableState;
+        if (!usableGame
+            || stateReference == null
+            || !Object.ReferenceEquals(expectedState, stateReference))
+        {
+            ConsumeAuthorizedDirective(directive);
+            TryFaultInternal(
+                "state_replaced", FaultRequest.Derived());
+            return false;
+        }
+        return true;
     }
 
     internal void CompleteUpdate(
@@ -337,7 +416,7 @@ internal sealed class PassiveDriver : IDisposable
                 "update directive is not outstanding");
         }
         outstandingUpdate = null;
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
             return;
         if (directive.Epoch != epoch)
         {
@@ -400,7 +479,7 @@ internal sealed class PassiveDriver : IDisposable
 
     internal HookToken PlayerPollEntered()
     {
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
             return HookToken.Inert(HookKind.PlayerPoll);
         if (playerPoll != null)
         {
@@ -415,7 +494,7 @@ internal sealed class PassiveDriver : IDisposable
 
     internal void PhysicalPollReturned(int rawDirection)
     {
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
             return;
         if (playerPoll == null || playerPoll.SawPhysicalPoll)
         {
@@ -424,22 +503,34 @@ internal sealed class PassiveDriver : IDisposable
             return;
         }
         playerPoll.SawPhysicalPoll = true;
+        playerPoll.RawDirection = rawDirection;
         if (rawDirection == 8)
         {
-            if (phase == PassivePhase.AwaitInitialNeutral)
+            if (phase == PassivePhase.AwaitInitialNeutral
+                || phase == PassivePhase.Settling)
+            {
                 neutralSeen = true;
+            }
             return;
         }
-        if (phase == PassivePhase.AwaitInitialNeutral)
+        if (phase == PassivePhase.AwaitInitialNeutral
+            || phase == PassivePhase.Settling)
         {
             neutralSeen = false;
             candidateSignature = null;
         }
+        OracleInput ignored;
+        if (!TryMapCardinal(rawDirection, out ignored))
+        {
+            TryFaultInternal(
+                "unexpected_input",
+                FaultRequest.Offending(completedInputs, null));
+        }
     }
 
     internal void PlayerPollReturned(HookToken token)
     {
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
         {
             ConsumeLateToken(token, HookKind.PlayerPoll);
             return;
@@ -453,11 +544,16 @@ internal sealed class PassiveDriver : IDisposable
             return;
         }
         playerPoll = null;
+        if (processInput != null)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+        }
     }
 
     internal void PlayerPollThrew(HookToken token)
     {
-        if (!IsInitialObservationActive())
+        if (!IsObservationActive())
         {
             ConsumeLateToken(token, HookKind.PlayerPoll);
             return;
@@ -501,14 +597,16 @@ internal sealed class PassiveDriver : IDisposable
     {
         if (sample == null)
             throw new ArgumentNullException("sample");
-        if (phase == PassivePhase.AwaitGame)
+        if (phase == PassivePhase.AwaitGame
+            || phase == PassivePhase.Ready)
         {
             if (sample.Kind != GateSampleKind.NotInspected)
                 throw new InvalidOperationException(
                     "gate inspected without an active epoch");
             return;
         }
-        if (phase != PassivePhase.AwaitInitialNeutral)
+        if (phase != PassivePhase.AwaitInitialNeutral
+            && phase != PassivePhase.Settling)
             return;
 
         if (sample.Kind == GateSampleKind.NotInspected)
@@ -535,7 +633,16 @@ internal sealed class PassiveDriver : IDisposable
             if (candidateSignature != null
                 && SameBytes(candidateSignature, signature))
             {
-                EmitInitial(sample.Capture);
+                if (phase == PassivePhase.AwaitInitialNeutral)
+                {
+                    EmitInitial(sample.Capture);
+                }
+                else
+                {
+                    EmitSettledAttempt(
+                        sample.Capture,
+                        directive.SettleFrames);
+                }
                 return;
             }
             candidateSignature = signature;
@@ -548,7 +655,9 @@ internal sealed class PassiveDriver : IDisposable
         if (directive.TimeoutAfterSample)
         {
             TryFaultInternal(
-                "initial_settle_timeout",
+                phase == PassivePhase.AwaitInitialNeutral
+                    ? "initial_settle_timeout"
+                    : "settle_timeout",
                 FaultRequest.Derived());
         }
     }
@@ -560,8 +669,8 @@ internal sealed class PassiveDriver : IDisposable
             CanonicalJson.EncodeError(
                 new ErrorRecord(
                     runId,
-                    null,
-                    null,
+                    Int32.MaxValue,
+                    OracleInput.North,
                     RecordErrorCodes[index],
                     OracleProtocol.MaxSettleFrames,
                     capture));
@@ -574,6 +683,7 @@ internal sealed class PassiveDriver : IDisposable
     private void EmitInitial(CaptureRecord capture)
     {
         sink.WriteInitial(new InitialRecord(runId, capture));
+        stableState = epochState;
         phase = PassivePhase.Ready;
         currentFrames = 0;
         neutralSeen = false;
@@ -590,6 +700,58 @@ internal sealed class PassiveDriver : IDisposable
         }
     }
 
+    private bool HandleManualAttempt(
+        OracleInput input,
+        object stateReference,
+        double nowSeconds)
+    {
+        if (!IsValidMonotonic(nowSeconds))
+        {
+            TryFaultInternal(
+                "observer_exception", FaultRequest.Derived());
+            return false;
+        }
+        if (phase == PassivePhase.AwaitGame
+            || phase == PassivePhase.AwaitInitialNeutral)
+        {
+            TryFaultInternal(
+                "input_before_initial",
+                FaultRequest.Offending(completedInputs, input));
+            return false;
+        }
+        if (phase == PassivePhase.Settling)
+        {
+            TryFaultInternal(
+                "overlapping_input", FaultRequest.Derived());
+            return false;
+        }
+        if (phase != PassivePhase.Ready)
+            return false;
+        if (stateReference == null
+            || !Object.ReferenceEquals(stableState, stateReference))
+        {
+            TryFaultInternal(
+                "state_replaced", FaultRequest.Derived());
+            return false;
+        }
+
+        epoch++;
+        phase = PassivePhase.Settling;
+        epochState = stateReference;
+        epochStartedAt = nowSeconds;
+        currentFrames = 0;
+        neutralSeen = false;
+        candidateSignature = null;
+        lastCapture = null;
+        attemptPending = true;
+        attemptOutcomeKnown = false;
+        attemptInput = input;
+        attemptAccepted = false;
+        attemptMovementScheduled = false;
+        attemptState = stateReference;
+        return true;
+    }
+
     private void StartInitialEpoch(
         object stateReference,
         double nowSeconds,
@@ -603,6 +765,7 @@ internal sealed class PassiveDriver : IDisposable
         neutralSeen = false;
         candidateSignature = null;
         lastCapture = null;
+        ClearAttemptFields();
     }
 
     private void ResetToAwaitGame()
@@ -614,6 +777,27 @@ internal sealed class PassiveDriver : IDisposable
         neutralSeen = false;
         candidateSignature = null;
         lastCapture = null;
+        ClearAttemptFields();
+    }
+
+    private void ClearAttemptAfterStep()
+    {
+        phase = PassivePhase.Ready;
+        currentFrames = 0;
+        neutralSeen = false;
+        candidateSignature = null;
+        epochState = stableState;
+        ClearAttemptFields();
+    }
+
+    private void ClearAttemptFields()
+    {
+        attemptPending = false;
+        attemptOutcomeKnown = false;
+        attemptInput = OracleInput.North;
+        attemptAccepted = false;
+        attemptMovementScheduled = false;
+        attemptState = null;
     }
 
     private void ConsumeAuthorizedDirective(UpdateDirective directive)
@@ -740,9 +924,31 @@ internal sealed class PassiveDriver : IDisposable
         FaultRequest request,
         PassivePhase faultPhase)
     {
+        int? inputIndex;
+        OracleInput? input;
+        if (attemptPending)
+        {
+            inputIndex = completedInputs;
+            input = attemptInput;
+        }
+        else if (request.HasOffendingInput)
+        {
+            inputIndex = request.OffendingIndex;
+            input = request.OffendingInput;
+        }
+        else
+        {
+            inputIndex = null;
+            input = null;
+        }
+
         int frames;
         if (request.FrameOverride.HasValue)
             frames = request.FrameOverride.Value;
+        else if (attemptPending)
+            frames = currentFrames;
+        else if (request.HasOffendingInput)
+            frames = 0;
         else if (faultPhase == PassivePhase.AwaitInitialNeutral)
             frames = currentFrames;
         else
@@ -750,8 +956,8 @@ internal sealed class PassiveDriver : IDisposable
 
         return new ErrorRecord(
             runId,
-            null,
-            null,
+            inputIndex,
+            input,
             code,
             frames,
             lastCapture);
@@ -820,14 +1026,16 @@ internal sealed class PassiveDriver : IDisposable
         }
     }
 
-    private bool IsInitialObservationActive()
+    private bool IsObservationActive()
     {
         return Read(ref prepared) != 0
             && Read(ref disabled) == 0
             && Read(ref disposed) == 0
             && !TerminalSelected()
             && (phase == PassivePhase.AwaitGame
-                || phase == PassivePhase.AwaitInitialNeutral);
+                || phase == PassivePhase.AwaitInitialNeutral
+                || phase == PassivePhase.Ready
+                || phase == PassivePhase.Settling);
     }
 
     private bool TerminalSelected()
@@ -847,6 +1055,30 @@ internal sealed class PassiveDriver : IDisposable
             && !Double.IsInfinity(value);
     }
 
+    private static bool TryMapCardinal(
+        int rawDirection,
+        out OracleInput input)
+    {
+        switch (rawDirection)
+        {
+            case 0:
+                input = OracleInput.North;
+                return true;
+            case 1:
+                input = OracleInput.South;
+                return true;
+            case 2:
+                input = OracleInput.West;
+                return true;
+            case 3:
+                input = OracleInput.East;
+                return true;
+            default:
+                input = OracleInput.North;
+                return false;
+        }
+    }
+
     private static bool SameBytes(byte[] left, byte[] right)
     {
         if (left == null
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
new file mode 100644
index 0000000000000000000000000000000000000000..a61e8b856a010b8a439dd5b1d196213e3f31f634
--- /dev/null
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -0,0 +1,221 @@
+using System;
+
+internal sealed partial class PassiveDriver
+{
+    private sealed class ProcessInputContext
+    {
+        internal long Id;
+    }
+
+    private sealed class UndoContext
+    {
+        internal long Id;
+        internal bool RestoreSeen;
+    }
+
+    private ProcessInputContext processInput;
+    private UndoContext undoContext;
+
+    internal HookToken ProcessInputEntered(
+        object stateReference,
+        int rawDirection,
+        double nowSeconds)
+    {
+        if (!IsObservationActive())
+            return HookToken.Inert(HookKind.ProcessInput);
+
+        if (playerPoll == null)
+        {
+            if (phase == PassivePhase.Ready)
+            {
+                TryFaultInternal(
+                    "unscoped_process_input",
+                    FaultRequest.Derived());
+            }
+            return HookToken.Inert(HookKind.ProcessInput);
+        }
+
+        OracleInput input;
+        if (!TryMapCardinal(rawDirection, out input))
+        {
+            TryFaultInternal(
+                "unexpected_input",
+                FaultRequest.Offending(completedInputs, null));
+            return HookToken.Inert(HookKind.ProcessInput);
+        }
+
+        if (!playerPoll.SawPhysicalPoll
+            || playerPoll.SawManualProcessInput
+            || playerPoll.RawDirection != rawDirection
+            || processInput != null)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch",
+                FaultRequest.Offending(completedInputs, input));
+            return HookToken.Inert(HookKind.ProcessInput);
+        }
+        playerPoll.SawManualProcessInput = true;
+
+        if (!HandleManualAttempt(
+            input, stateReference, nowSeconds))
+        {
+            return HookToken.Inert(HookKind.ProcessInput);
+        }
+
+        HookToken token = NewToken(HookKind.ProcessInput);
+        if (!token.Active)
+            return token;
+        processInput =
+            new ProcessInputContext { Id = token.Id };
+        return token;
+    }
+
+    internal void ProcessInputReturned(
+        HookToken token,
+        bool accepted,
+        bool movementScheduled)
+    {
+        if (!ConsumeOrdinaryToken(
+            token, HookKind.ProcessInput))
+        {
+            return;
+        }
+        if (processInput == null
+            || processInput.Id != token.Id
+            || !attemptPending
+            || attemptOutcomeKnown)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return;
+        }
+        processInput = null;
+        attemptAccepted = accepted;
+        attemptMovementScheduled = movementScheduled;
+        attemptOutcomeKnown = true;
+    }
+
+    internal void ProcessInputThrew(HookToken token)
+    {
+        if (!ConsumeCleanupToken(
+            token, HookKind.ProcessInput))
+        {
+            return;
+        }
+        if (processInput == null
+            || processInput.Id != token.Id)
+        {
+            throw new InvalidOperationException(
+                "ProcessInput token mismatch");
+        }
+        processInput = null;
+    }
+
+    internal HookToken UndoEntered(
+        object stateReference,
+        double nowSeconds)
+    {
+        if (!IsObservationActive())
+            return HookToken.Inert(HookKind.Undo);
+        if (undoContext != null)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return HookToken.Inert(HookKind.Undo);
+        }
+        if (!HandleManualAttempt(
+            OracleInput.Undo, stateReference, nowSeconds))
+        {
+            return HookToken.Inert(HookKind.Undo);
+        }
+        HookToken token = NewToken(HookKind.Undo);
+        if (!token.Active)
+            return token;
+        undoContext = new UndoContext { Id = token.Id };
+        return token;
+    }
+
+    internal void RestoreObserved()
+    {
+        if (!IsObservationActive())
+            return;
+        if (undoContext == null || undoContext.RestoreSeen)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return;
+        }
+        undoContext.RestoreSeen = true;
+    }
+
+    internal void UndoReturned(
+        HookToken token,
+        bool movementScheduled)
+    {
+        if (!ConsumeOrdinaryToken(token, HookKind.Undo))
+            return;
+        if (undoContext == null
+            || undoContext.Id != token.Id
+            || !attemptPending
+            || attemptOutcomeKnown)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return;
+        }
+        bool accepted = undoContext.RestoreSeen;
+        undoContext = null;
+        attemptAccepted = accepted;
+        attemptMovementScheduled = movementScheduled;
+        attemptOutcomeKnown = true;
+    }
+
+    internal void UndoThrew(HookToken token)
+    {
+        if (!ConsumeCleanupToken(token, HookKind.Undo))
+            return;
+        if (undoContext == null
+            || undoContext.Id != token.Id)
+        {
+            throw new InvalidOperationException(
+                "Undo token mismatch");
+        }
+        undoContext = null;
+    }
+
+    private void EmitSettledAttempt(
+        CaptureRecord capture,
+        int settleFrames)
+    {
+        if (!attemptPending || !attemptOutcomeKnown)
+        {
+            throw new InvalidOperationException(
+                "settled attempt has no complete outcome");
+        }
+
+        sink.WriteStep(
+            new StepRecord(
+                runId,
+                completedInputs,
+                attemptInput,
+                attemptAccepted,
+                attemptMovementScheduled,
+                settleFrames,
+                false,
+                capture));
+        completedInputs++;
+        stableState = attemptState;
+        ClearAttemptAfterStep();
+        lastCapture = null;
+
+        try
+        {
+            reporter.Ready(completedInputs);
+        }
+        catch (Exception)
+        {
+            TryFaultInternal(
+                "observer_exception", FaultRequest.Derived());
+        }
+    }
+}
~~~
<!-- TASK5-PATCH-END:C51-PRODUCTION -->

The C51 tests-only forced build must exit `1` solely with the exact authenticated missing-member CS1061 set for `PendingInput`, `PendingAccepted`, `PendingMovementScheduled`, `ProcessInputEntered`, `ProcessInputReturned`, `ProcessInputThrew`, `UndoEntered`, `RestoreObserved`, `UndoReturned`, and `UndoThrew`. The raw build emits 112 error lines; C-sorting and exact de-duplication yields 56 normalized error lines with SHA-256 `131716de08fd210fb96b3b6ed99e6222137f7eccf70573024cd1ad339df73b22`. The canonical compact diagnostic is 56 lines, 4195 bytes, SHA-256 `8ad0bdc10e58042f48d9e52314f96be314c15b4848fcfa2e49d0a6c21f568d44`. No production diagnostic, fixture error, restore error, SDK error, permission error, warning, or unrelated compiler code is accepted.

The sole executable C51 compiler-RED invocation appears in Task 1 Step 2;
this catalog paragraph is descriptive and must not be run separately.

### C52 patches

**C52-TESTS patch:** SHA-256 `13beee22b9b661320226c8deeb7979c574918d50c30b9f4498f5d35a9294e80c`; 880 LF lines; 39208 bytes.
<!-- TASK5-PATCH-BEGIN:C52-TESTS -->
~~~diff
diff --git a/oracle/plugin/tests/PassiveDriverInputTests.cs b/oracle/plugin/tests/PassiveDriverInputTests.cs
index ec2f13dff1e6e2925fd7749592b127928518d7b4..e0a09eb8931838d12984a05cfa6fd90bf280557d 100644
--- a/oracle/plugin/tests/PassiveDriverInputTests.cs
+++ b/oracle/plugin/tests/PassiveDriverInputTests.cs
@@ -1,4 +1,5 @@
 using System;
+using System.Collections.Generic;
 
 internal static class PassiveDriverInputTests
 {
@@ -16,6 +17,10 @@ internal static class PassiveDriverInputTests
             AcceptedAndRefusedDirectionOutcomes);
         tests.Add("driver-input", "Undo acceptance and restore rules",
             UndoAcceptanceAndRestoreRules);
+        tests.Add("driver-input", "restart depth and null fields",
+            RestartDepthAndNullFields);
+        tests.Add("driver-input", "state replacement and ClearThrew",
+            StateReplacementAndClearThrew);
     }
 
     private static void AllCardinalsCorrelate()
@@ -1108,4 +1113,845 @@ internal static class PassiveDriverInputTests
             "Step 2 is durable before Ready(3)");
     }
 
+    private static void RestartDepthAndNullFields()
+    {
+        RestartFieldsFollowEveryActivePhase();
+        RestartDepthPrecedesFault();
+        RestartNestedPathsBalance();
+        RestartCleanupIsLifoAndSingleUse();
+    }
+
+    private static void RestartFieldsFollowEveryActivePhase()
+    {
+        DriverFixture awaitingGame = DriverFixture.Active();
+        HookToken gameRestart = awaitingGame.Driver.RestartEntered();
+        Check.True(gameRestart.Active, "AwaitGame Restart token active");
+        AssertRestartError(
+            awaitingGame, 0, "AwaitGame Restart fields");
+        awaitingGame.Driver.RestartReturned(gameRestart);
+
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        HookToken initialRestart =
+            awaitingInitial.Driver.RestartEntered();
+        Check.True(initialRestart.Active,
+            "AwaitInitialNeutral Restart token active");
+        AssertRestartError(
+            awaitingInitial, 1, "AwaitInitialNeutral Restart fields");
+        awaitingInitial.Driver.RestartReturned(initialRestart);
+
+        DriverFixture ready = DriverFixture.Ready();
+        HookToken readyRestart = ready.Driver.RestartEntered();
+        Check.True(readyRestart.Active, "Ready Restart token active");
+        AssertRestartError(ready, 0, "Ready Restart fields");
+        ready.Driver.RestartReturned(readyRestart);
+
+        DriverFixture settling = DriverFixture.Ready();
+        settling.OpenDirection(2, true, true, 10.0);
+        settling.Observe(
+            settling.State,
+            settling.State,
+            11.0,
+            false,
+            ProtocolSamples.MovedCapture);
+        HookToken settlingRestart = settling.Driver.RestartEntered();
+        Check.True(settlingRestart.Active,
+            "Settling Restart token active");
+        AssertRestartError(settling, 1, "Settling Restart fields");
+        Check.Equal(0, settling.Sink.StepRecords.Count,
+            "Restart never emits a Step");
+        settling.Driver.RestartReturned(settlingRestart);
+    }
+
+    private static void RestartDepthPrecedesFault()
+    {
+        List<string> events = new List<string>();
+        FakeTraceSink innerSink = new FakeTraceSink(events);
+        ReentrantErrorTraceSink sink =
+            new ReentrantErrorTraceSink(innerSink);
+        FakePassiveReporter reporter =
+            new FakePassiveReporter(events);
+        PassiveDriver driver = new PassiveDriver(
+            sink,
+            reporter,
+            OracleProtocol.ExpectedInputCount,
+            600,
+            30.0);
+        sink.Driver = driver;
+        Check.True(driver.Prepare(ProtocolSamples.Run),
+            "reentrant Restart prepare");
+        Check.True(driver.Activate(), "reentrant Restart activate");
+
+        HookToken outer = driver.RestartEntered();
+        Check.True(outer.Active, "outer Restart token active");
+        Check.True(sink.InnerRestart != null,
+            "Restart depth is established before Error emission");
+        Check.True(sink.InnerRestart.Active,
+            "reentrant Restart remains active after fault selection");
+        Check.False(sink.NestedUndo.Active,
+            "Undo nested under Restart is bookkeeping-only");
+        Check.Equal(1, innerSink.ErrorRecords.Count,
+            "reentrant Restart emits one Error");
+        driver.RestartReturned(sink.InnerRestart);
+        driver.RestartReturned(outer);
+    }
+
+    private static void RestartNestedPathsBalance()
+    {
+        DriverFixture returned = DriverFixture.Ready();
+        HookToken outer = returned.Driver.RestartEntered();
+        HookToken recursive = returned.Driver.RestartEntered();
+        Check.True(recursive.Active, "recursive Restart token active");
+        HookToken nestedUndo = returned.Driver.UndoEntered(
+            returned.State, 10.0);
+        Check.False(nestedUndo.Active,
+            "nested Undo is suppressed by Restart depth");
+        returned.Driver.RestoreObserved();
+        returned.Driver.UndoReturned(nestedUndo, false);
+        returned.Driver.RestartReturned(recursive);
+        returned.Driver.RestartReturned(outer);
+        Check.Equal(1, returned.Sink.ErrorRecords.Count,
+            "returned nested Restart path preserves first fault");
+
+        DriverFixture threw = DriverFixture.Ready();
+        HookToken threwOuter = threw.Driver.RestartEntered();
+        HookToken threwInner = threw.Driver.RestartEntered();
+        threw.Driver.RestartThrew(threwInner);
+        threw.Driver.RestartThrew(threwOuter);
+        threw.Driver.RestartThrew(threwOuter);
+        Check.Equal(1, threw.Sink.ErrorRecords.Count,
+            "throwing Restart path preserves first fault");
+
+        DriverFixture cleared = DriverFixture.Ready();
+        HookToken clearOuter = cleared.Driver.RestartEntered();
+        HookToken clearInner = cleared.Driver.RestartEntered();
+        cleared.Driver.ClearThrew(clearInner);
+        cleared.Driver.ClearThrew(clearOuter);
+        cleared.Driver.ClearThrew(clearOuter);
+        Check.Equal(1, cleared.Sink.ErrorRecords.Count,
+            "generic Restart cleanup preserves first fault");
+    }
+
+    private static void RestartCleanupIsLifoAndSingleUse()
+    {
+        DriverFixture returned = DriverFixture.Ready();
+        HookToken outer = returned.Driver.RestartEntered();
+        HookToken inner = returned.Driver.RestartEntered();
+        Check.Throws<InvalidOperationException>(
+            delegate { returned.Driver.RestartReturned(outer); },
+            "Restart return rejects non-LIFO token");
+        returned.Driver.ClearThrew(inner);
+        returned.Driver.ClearThrew(inner);
+        returned.Driver.ClearThrew(outer);
+        HookToken afterReturn = returned.Driver.RestartEntered();
+        Check.False(afterReturn.Active,
+            "rejected outer return remains cleanable");
+        Check.Equal(1, returned.Sink.ErrorRecords.Count,
+            "non-LIFO return cannot claim another fault");
+
+        DriverFixture threw = DriverFixture.Ready();
+        HookToken threwOuter = threw.Driver.RestartEntered();
+        HookToken threwInner = threw.Driver.RestartEntered();
+        Check.Throws<InvalidOperationException>(
+            delegate { threw.Driver.RestartThrew(threwOuter); },
+            "Restart throw rejects non-LIFO token");
+        threw.Driver.RestartThrew(threwInner);
+        threw.Driver.RestartThrew(threwInner);
+        threw.Driver.RestartThrew(threwOuter);
+        HookToken afterThrow = threw.Driver.RestartEntered();
+        Check.False(afterThrow.Active,
+            "rejected outer throw remains cleanable");
+        Check.Equal(1, threw.Sink.ErrorRecords.Count,
+            "non-LIFO throw cannot claim another fault");
+    }
+
+    private static void AssertRestartError(
+        DriverFixture fixture,
+        int expectedFrames,
+        string label)
+    {
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            label + " count");
+        ErrorRecord error = fixture.Sink.ErrorRecords[0];
+        Check.Equal("unexpected_input", error.Code,
+            label + " code");
+        Check.False(error.InputIndex.HasValue,
+            label + " input index is null");
+        Check.False(error.Input.HasValue,
+            label + " input is null");
+        Check.Equal(expectedFrames, error.SettleFrames,
+            label + " frame count");
+    }
+
+    private static void StateReplacementAndClearThrew()
+    {
+        StateSetUsesActualReturnedIdentity();
+        StateSetContextIdentityIsAuthoritative();
+        StateSetBeforeInitialRulesAreExact();
+        StateSetAfterInitialRulesAreExact();
+        ClearThrewDispatchesAndProtectsOwnership();
+        LateHookCleanupIsOutputInert();
+    }
+
+    private static void StateSetUsesActualReturnedIdentity()
+    {
+        DriverFixture requestedDifferent = DriverFixture.Ready();
+        HookToken same = requestedDifferent.Driver.StateSetEntered(
+            requestedDifferent.State,
+            requestedDifferent.OtherState);
+        requestedDifferent.Driver.StateSetReturned(
+            same, requestedDifferent.State, 10.0);
+        Check.Equal(PassivePhase.Ready,
+            requestedDifferent.Driver.Phase,
+            "requested state is observational only");
+        Check.Equal(0, requestedDifferent.Sink.ErrorRecords.Count,
+            "same actual post-state is not replacement");
+
+        DriverFixture requestedSame = DriverFixture.Ready();
+        HookToken changed = requestedSame.Driver.StateSetEntered(
+            requestedSame.State,
+            requestedSame.State);
+        requestedSame.Driver.StateSetReturned(
+            changed, requestedSame.OtherState, 10.0);
+        Check.Equal("state_replaced",
+            requestedSame.Sink.ErrorRecords[0].Code,
+            "actual post-state controls replacement");
+    }
+
+    private static void StateSetContextIdentityIsAuthoritative()
+    {
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            0.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        awaitingInitial.Neutral();
+        CaptureRecord candidate =
+            ProtocolSamples.Capture("hook-identity-initial");
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            true,
+            candidate);
+        HookToken initialToken =
+            awaitingInitial.Driver.StateSetEntered(
+                awaitingInitial.OtherState,
+                awaitingInitial.State);
+        awaitingInitial.Driver.StateSetReturned(
+            initialToken, awaitingInitial.OtherState, 2.0);
+        Check.Equal(PassivePhase.AwaitInitialNeutral,
+            awaitingInitial.Driver.Phase,
+            "hook identity preserves AwaitInitial phase");
+        Check.Equal(2, awaitingInitial.Driver.CurrentSettleFrames,
+            "hook identity preserves AwaitInitial frame count");
+        Check.Equal(0, awaitingInitial.Sink.ErrorRecords.Count,
+            "hook identity preserves AwaitInitial without Error");
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            3.0,
+            true,
+            candidate);
+        Check.Equal(1,
+            awaitingInitial.Sink.InitialRecords.Count,
+            "hook identity preserves initial neutral and candidate");
+
+        DriverFixture ready = DriverFixture.Ready();
+        HookToken readyToken = ready.Driver.StateSetEntered(
+            ready.OtherState, ready.State);
+        ready.Driver.StateSetReturned(
+            readyToken, ready.OtherState, 10.0);
+        Check.Equal(PassivePhase.Ready, ready.Driver.Phase,
+            "hook identity preserves Ready phase");
+        Check.Equal(0, ready.Sink.ErrorRecords.Count,
+            "hook identity preserves Ready without Error");
+
+        DriverFixture settling = DriverFixture.Ready();
+        settling.OpenDirection(2, true, false, 10.0);
+        settling.Observe(
+            settling.State,
+            settling.State,
+            11.0,
+            false,
+            ProtocolSamples.MovedCapture);
+        HookToken settlingToken = settling.Driver.StateSetEntered(
+            settling.OtherState, settling.State);
+        settling.Driver.StateSetReturned(
+            settlingToken, settling.OtherState, 12.0);
+        Check.Equal(PassivePhase.Settling, settling.Driver.Phase,
+            "hook identity preserves Settling phase");
+        Check.Equal((OracleInput?)OracleInput.West,
+            (OracleInput?)settling.Driver.PendingInput,
+            "hook identity preserves pending input");
+        Check.True(settling.Driver.PendingAccepted,
+            "hook identity preserves accepted outcome");
+        Check.False(settling.Driver.PendingMovementScheduled,
+            "hook identity preserves movement outcome");
+        Check.Equal(1, settling.Driver.CurrentSettleFrames,
+            "hook identity preserves pending frame count");
+        Check.Equal(0, settling.Sink.ErrorRecords.Count,
+            "hook identity preserves Settling without Error");
+    }
+
+    private static void StateSetBeforeInitialRulesAreExact()
+    {
+        DriverFixture sameAwaitGame = DriverFixture.Active();
+        HookToken sameGame = sameAwaitGame.Driver.StateSetEntered(
+            sameAwaitGame.State, sameAwaitGame.OtherState);
+        sameAwaitGame.Driver.StateSetReturned(
+            sameGame, sameAwaitGame.State, 1.0);
+        Check.Equal(PassivePhase.AwaitGame,
+            sameAwaitGame.Driver.Phase,
+            "same-reference AwaitGame state is not replacement");
+        Check.Equal(0, sameAwaitGame.Driver.CurrentSettleFrames,
+            "same-reference AwaitGame state keeps frame zero");
+
+        DriverFixture nullAwaitGame = DriverFixture.Active();
+        HookToken nullGame = nullAwaitGame.Driver.StateSetEntered(
+            nullAwaitGame.State, nullAwaitGame.OtherState);
+        nullAwaitGame.Driver.StateSetReturned(nullGame, null, 1.0);
+        Check.Equal(PassivePhase.AwaitGame,
+            nullAwaitGame.Driver.Phase,
+            "null AwaitGame post-state stays AwaitGame");
+
+        DriverFixture awaitingInitial = DriverFixture.Active();
+        awaitingInitial.Observe(
+            awaitingInitial.State,
+            awaitingInitial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        HookToken sameInitial = awaitingInitial.Driver.StateSetEntered(
+            awaitingInitial.State, awaitingInitial.OtherState);
+        awaitingInitial.Driver.StateSetReturned(
+            sameInitial, awaitingInitial.State, 2.0);
+        Check.Equal(PassivePhase.AwaitInitialNeutral,
+            awaitingInitial.Driver.Phase,
+            "same-reference initial state keeps epoch");
+        Check.Equal(1, awaitingInitial.Driver.CurrentSettleFrames,
+            "same-reference initial state keeps frame count");
+
+        HookToken nullInitial = awaitingInitial.Driver.StateSetEntered(
+            awaitingInitial.State, awaitingInitial.OtherState);
+        awaitingInitial.Driver.StateSetReturned(nullInitial, null, 3.0);
+        Check.Equal(PassivePhase.AwaitGame,
+            awaitingInitial.Driver.Phase,
+            "null pre-Initial post-state returns AwaitGame");
+        Check.Equal(0, awaitingInitial.Driver.CurrentSettleFrames,
+            "null pre-Initial post-state clears frames");
+
+        DriverFixture explicitReplacement = DriverFixture.Active();
+        CaptureRecord oldCandidate =
+            ProtocolSamples.Capture("explicit-old-candidate");
+        explicitReplacement.Observe(
+            explicitReplacement.State,
+            explicitReplacement.State,
+            0.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        explicitReplacement.Neutral();
+        explicitReplacement.Observe(
+            explicitReplacement.State,
+            explicitReplacement.State,
+            1.0,
+            true,
+            oldCandidate);
+        HookToken replace = explicitReplacement.Driver.StateSetEntered(
+            explicitReplacement.State,
+            explicitReplacement.State);
+        explicitReplacement.Driver.StateSetReturned(
+            replace, explicitReplacement.OtherState, 2.0);
+        Check.Equal(PassivePhase.AwaitInitialNeutral,
+            explicitReplacement.Driver.Phase,
+            "explicit replacement starts a fresh initial epoch");
+        Check.Equal(0, explicitReplacement.Driver.CurrentSettleFrames,
+            "explicit StateSet replacement begins at frame zero");
+        FakeUpdateObservation withoutNeutral =
+            explicitReplacement.Observe(
+                explicitReplacement.OtherState,
+                explicitReplacement.OtherState,
+                3.0,
+                true,
+                oldCandidate);
+        Check.Equal(0, withoutNeutral.GateCalls,
+            "explicit replacement clears neutral eligibility");
+        explicitReplacement.Neutral();
+        explicitReplacement.Observe(
+            explicitReplacement.OtherState,
+            explicitReplacement.OtherState,
+            4.0,
+            true,
+            oldCandidate);
+        Check.Equal(0,
+            explicitReplacement.Sink.InitialRecords.Count,
+            "explicit replacement clears the old candidate");
+        explicitReplacement.Observe(
+            explicitReplacement.OtherState,
+            explicitReplacement.OtherState,
+            5.0,
+            true,
+            ProtocolSamples.Capture("explicit-old-candidate"));
+        Check.Equal(1,
+            explicitReplacement.Sink.InitialRecords.Count,
+            "two fresh replacement captures settle");
+
+        DriverFixture lastCapture = DriverFixture.Active();
+        lastCapture.Observe(
+            lastCapture.State,
+            lastCapture.State,
+            0.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        lastCapture.Neutral();
+        lastCapture.Observe(
+            lastCapture.State,
+            lastCapture.State,
+            1.0,
+            true,
+            ProtocolSamples.Capture("explicit-last"));
+        HookToken clearLast = lastCapture.Driver.StateSetEntered(
+            lastCapture.State, lastCapture.State);
+        lastCapture.Driver.StateSetReturned(
+            clearLast, lastCapture.OtherState, 2.0);
+        lastCapture.Driver.TryFault("observer_exception");
+        Check.True(lastCapture.Sink.ErrorRecords[0].LastCapture == null,
+            "explicit replacement clears last_capture");
+
+        DriverFixture boundaryReplacement = DriverFixture.Active();
+        boundaryReplacement.Observe(
+            boundaryReplacement.State,
+            boundaryReplacement.State,
+            0.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        boundaryReplacement.Observe(
+            boundaryReplacement.State,
+            true,
+            boundaryReplacement.OtherState,
+            true,
+            2.0,
+            true,
+            ProtocolSamples.InitialCapture);
+        Check.Equal(1,
+            boundaryReplacement.Boundary.LastDirective.SettleFrames,
+            "same-update boundary replacement remains frame one");
+    }
+
+    private static void StateSetAfterInitialRulesAreExact()
+    {
+        DriverFixture same = DriverFixture.Ready();
+        HookToken sameToken = same.Driver.StateSetEntered(
+            same.State, same.OtherState);
+        same.Driver.StateSetReturned(sameToken, same.State, 10.0);
+        Check.Equal(0, same.Sink.ErrorRecords.Count,
+            "same-reference Ready state is not replacement");
+
+        DriverFixture invalidTime = DriverFixture.Ready();
+        HookToken invalidTimeToken = invalidTime.Driver.StateSetEntered(
+            invalidTime.State, invalidTime.OtherState);
+        invalidTime.Driver.StateSetReturned(
+            invalidTimeToken, invalidTime.State, Double.NaN);
+        Check.Equal(1, invalidTime.Sink.ErrorRecords.Count,
+            "invalid StateSet time emits one Error");
+        ErrorRecord invalidTimeError =
+            invalidTime.Sink.ErrorRecords[0];
+        Check.Equal("observer_exception", invalidTimeError.Code,
+            "invalid StateSet time uses observer policy");
+        Check.False(invalidTimeError.InputIndex.HasValue,
+            "invalid StateSet time has null input index");
+        Check.False(invalidTimeError.Input.HasValue,
+            "invalid StateSet time has null input");
+        Check.Equal(0, invalidTimeError.SettleFrames,
+            "invalid StateSet time has zero frames");
+        Check.Equal(0, invalidTime.Sink.StepRecords.Count,
+            "invalid StateSet time is not a replacement Step");
+
+        DriverFixture changed = DriverFixture.Ready();
+        HookToken changedToken = changed.Driver.StateSetEntered(
+            changed.State, changed.State);
+        changed.Driver.StateSetReturned(
+            changedToken, changed.OtherState, 10.0);
+        Check.Equal("state_replaced",
+            changed.Sink.ErrorRecords[0].Code,
+            "different Ready state faults");
+        Check.Equal(0, changed.Sink.StepRecords.Count,
+            "Ready replacement emits no Step");
+
+        DriverFixture nullState = DriverFixture.Ready();
+        HookToken nullToken = nullState.Driver.StateSetEntered(
+            nullState.State, nullState.OtherState);
+        nullState.Driver.StateSetReturned(nullToken, null, 10.0);
+        Check.Equal("state_replaced",
+            nullState.Sink.ErrorRecords[0].Code,
+            "null Ready state faults as replacement");
+
+        DriverFixture pending = DriverFixture.Ready();
+        pending.OpenDirection(2, true, true, 10.0);
+        pending.Observe(
+            pending.State,
+            pending.State,
+            11.0,
+            false,
+            ProtocolSamples.MovedCapture);
+        HookToken pendingToken = pending.Driver.StateSetEntered(
+            pending.State, pending.State);
+        pending.Driver.StateSetReturned(
+            pendingToken, pending.OtherState, 12.0);
+        ErrorRecord pendingError = pending.Sink.ErrorRecords[0];
+        Check.Equal("state_replaced", pendingError.Code,
+            "Settling explicit replacement code");
+        Check.Equal((int?)0, pendingError.InputIndex,
+            "Settling replacement retains pending index");
+        Check.Equal((OracleInput?)OracleInput.West,
+            pendingError.Input,
+            "Settling replacement retains pending input");
+        Check.Equal(1, pendingError.SettleFrames,
+            "Settling replacement retains committed frame");
+        Check.Equal(0, pending.Sink.StepRecords.Count,
+            "Settling replacement emits no Step");
+    }
+
+    private static void ClearThrewDispatchesAndProtectsOwnership()
+    {
+        DriverFixture player = DriverFixture.Ready();
+        HookToken playerToken = player.Driver.PlayerPollEntered();
+        player.Driver.ClearThrew(playerToken);
+        player.Driver.ClearThrew(playerToken);
+        HookToken nextPlayer = player.Driver.PlayerPollEntered();
+        Check.True(nextPlayer.Active,
+            "ClearThrew clears PlayerPoll context once");
+        player.Driver.PlayerPollReturned(nextPlayer);
+
+        DriverFixture process = DriverFixture.Ready();
+        HookToken processPoll = process.Driver.PlayerPollEntered();
+        process.Driver.PhysicalPollReturned(2);
+        HookToken processToken = process.Driver.ProcessInputEntered(
+            process.State, 2, 10.0);
+        process.Driver.ClearThrew(processToken);
+        process.Driver.ClearThrew(processToken);
+        process.Driver.PlayerPollReturned(processPoll);
+        HookToken nextProcessPoll = process.Driver.PlayerPollEntered();
+        process.Driver.PhysicalPollReturned(0);
+        process.Driver.ProcessInputEntered(
+            process.State, 0, 11.0);
+        process.Driver.PlayerPollReturned(nextProcessPoll);
+        Check.Equal("overlapping_input",
+            process.Sink.ErrorRecords[0].Code,
+            "ClearThrew clears ProcessInput context once");
+
+        DriverFixture undo = DriverFixture.Ready();
+        HookToken undoToken = undo.Driver.UndoEntered(
+            undo.State, 10.0);
+        undo.Driver.ClearThrew(undoToken);
+        undo.Driver.ClearThrew(undoToken);
+        undo.Driver.UndoEntered(undo.State, 11.0);
+        Check.Equal("overlapping_input",
+            undo.Sink.ErrorRecords[0].Code,
+            "ClearThrew clears Undo context once");
+
+        DriverFixture stateSet = DriverFixture.Ready();
+        HookToken stateToken = stateSet.Driver.StateSetEntered(
+            stateSet.State, stateSet.OtherState);
+        stateSet.Driver.StateSetThrew(stateToken);
+        stateSet.Driver.StateSetThrew(stateToken);
+        HookToken nextState = stateSet.Driver.StateSetEntered(
+            stateSet.State, stateSet.OtherState);
+        Check.True(nextState.Active,
+            "typed StateSet throw clears context once");
+        stateSet.Driver.ClearThrew(nextState);
+        HookToken thirdState = stateSet.Driver.StateSetEntered(
+            stateSet.State, stateSet.OtherState);
+        Check.True(thirdState.Active,
+            "generic StateSet throw clears context once");
+        stateSet.Driver.StateSetReturned(
+            thirdState, stateSet.State, 12.0);
+
+        DriverFixture wrongKind = DriverFixture.Ready();
+        HookToken ownedState = wrongKind.Driver.StateSetEntered(
+            wrongKind.State, wrongKind.OtherState);
+        HookToken ownedPoll = wrongKind.Driver.PlayerPollEntered();
+        wrongKind.Driver.ClearThrew(ownedPoll);
+        wrongKind.Driver.StateSetReturned(
+            ownedState, wrongKind.State, 10.0);
+        Check.Equal(0, wrongKind.Sink.ErrorRecords.Count,
+            "wrong kind cannot clear StateSet context");
+
+        DriverFixture owner = DriverFixture.Ready();
+        HookToken ownerState = owner.Driver.StateSetEntered(
+            owner.State, owner.OtherState);
+        DriverFixture foreign = DriverFixture.Ready();
+        HookToken foreignState = foreign.Driver.StateSetEntered(
+            foreign.State, foreign.OtherState);
+        Check.Throws<InvalidOperationException>(
+            delegate { owner.Driver.ClearThrew(foreignState); },
+            "foreign cleanup token is rejected");
+        owner.Driver.StateSetReturned(
+            ownerState, owner.State, 10.0);
+        foreign.Driver.StateSetThrew(foreignState);
+        Check.Equal(0, owner.Sink.ErrorRecords.Count,
+            "foreign token cannot clear owned StateSet context");
+
+        DriverFixture stale = DriverFixture.Ready();
+        HookToken staleState = stale.Driver.StateSetEntered(
+            stale.State, stale.OtherState);
+        stale.Driver.ClearThrew(staleState);
+        HookToken currentState = stale.Driver.StateSetEntered(
+            stale.State, stale.OtherState);
+        stale.Driver.ClearThrew(staleState);
+        stale.Driver.StateSetReturned(
+            currentState, stale.State, 10.0);
+        Check.Equal(0, stale.Sink.ErrorRecords.Count,
+            "consumed token cannot clear a later StateSet context");
+
+        stateSet.Driver.ClearThrew(null);
+        stateSet.Driver.ClearThrew(HookToken.Inert(HookKind.StateSet));
+    }
+
+    private static void LateHookCleanupIsOutputInert()
+    {
+        DriverFixture disabledPlayer = DriverFixture.Ready();
+        HookToken disabledPlayerToken =
+            disabledPlayer.Driver.PlayerPollEntered();
+        disabledPlayer.Driver.Disable();
+        int disabledPlayerEvents = disabledPlayer.Events.Count;
+        disabledPlayer.Driver.PlayerPollReturned(disabledPlayerToken);
+        disabledPlayer.Driver.PlayerPollReturned(disabledPlayerToken);
+        Check.False(disabledPlayerToken.TryConsume(),
+            "disabled PlayerPoll return consumes token once");
+        Check.Equal(disabledPlayerEvents, disabledPlayer.Events.Count,
+            "disabled PlayerPoll return cleanup is output-inert");
+
+        DriverFixture faultedPlayer = DriverFixture.Ready();
+        HookToken faultedPlayerToken =
+            faultedPlayer.Driver.PlayerPollEntered();
+        faultedPlayer.Driver.TryFault("observer_exception");
+        int faultedPlayerEvents = faultedPlayer.Events.Count;
+        faultedPlayer.Driver.ClearThrew(faultedPlayerToken);
+        faultedPlayer.Driver.ClearThrew(faultedPlayerToken);
+        Check.False(faultedPlayerToken.TryConsume(),
+            "faulted PlayerPoll throw consumes token once");
+        Check.Equal(faultedPlayerEvents, faultedPlayer.Events.Count,
+            "faulted PlayerPoll throw cleanup is output-inert");
+
+        DriverFixture disposedPlayer = DriverFixture.Ready();
+        HookToken disposedPlayerToken =
+            disposedPlayer.Driver.PlayerPollEntered();
+        disposedPlayer.Driver.Dispose();
+        int disposedPlayerEvents = disposedPlayer.Events.Count;
+        disposedPlayer.Driver.PlayerPollThrew(disposedPlayerToken);
+        disposedPlayer.Driver.PlayerPollThrew(disposedPlayerToken);
+        Check.False(disposedPlayerToken.TryConsume(),
+            "disposed PlayerPoll throw consumes token once");
+        Check.Equal(disposedPlayerEvents, disposedPlayer.Events.Count,
+            "disposed PlayerPoll throw cleanup is output-inert");
+        Check.Equal(1, disposedPlayer.Sink.CloseCalls,
+            "disposed PlayerPoll cleanup does not close twice");
+
+        DriverFixture disabledProcess = DriverFixture.Ready();
+        HookToken processPoll = disabledProcess.Driver.PlayerPollEntered();
+        disabledProcess.Driver.PhysicalPollReturned(2);
+        HookToken process = disabledProcess.Driver.ProcessInputEntered(
+            disabledProcess.State, 2, 10.0);
+        disabledProcess.Driver.Disable();
+        int disabledProcessEvents = disabledProcess.Events.Count;
+        disabledProcess.Driver.ProcessInputReturned(process, true, true);
+        disabledProcess.Driver.ProcessInputReturned(process, true, true);
+        Check.Throws<InvalidOperationException>(
+            delegate
+            {
+                disabledProcess.Driver.PendingAccepted.ToString();
+            },
+            "disabled ProcessInput leaves acceptance unavailable");
+        Check.Throws<InvalidOperationException>(
+            delegate
+            {
+                disabledProcess.Driver.PendingMovementScheduled.ToString();
+            },
+            "disabled ProcessInput leaves movement unavailable");
+        disabledProcess.Driver.ClearThrew(processPoll);
+        Check.False(process.TryConsume(),
+            "disabled ProcessInput return consumes token once");
+        Check.False(processPoll.TryConsume(),
+            "disabled PlayerPoll cleanup consumes token once");
+        Check.Equal(disabledProcessEvents,
+            disabledProcess.Events.Count,
+            "disabled ProcessInput return cleanup is output-inert");
+
+        DriverFixture disabledUndo = DriverFixture.Ready();
+        HookToken disabledUndoToken = disabledUndo.Driver.UndoEntered(
+            disabledUndo.State, 10.0);
+        disabledUndo.Driver.Disable();
+        int disabledUndoEvents = disabledUndo.Events.Count;
+        disabledUndo.Driver.UndoReturned(disabledUndoToken, true);
+        disabledUndo.Driver.UndoReturned(disabledUndoToken, true);
+        Check.Throws<InvalidOperationException>(
+            delegate
+            {
+                disabledUndo.Driver.PendingAccepted.ToString();
+            },
+            "disabled Undo leaves acceptance unavailable");
+        Check.Throws<InvalidOperationException>(
+            delegate
+            {
+                disabledUndo.Driver.PendingMovementScheduled.ToString();
+            },
+            "disabled Undo leaves movement unavailable");
+        Check.False(disabledUndoToken.TryConsume(),
+            "disabled Undo return consumes token once");
+        Check.Equal(disabledUndoEvents, disabledUndo.Events.Count,
+            "disabled Undo return cleanup is output-inert");
+
+        DriverFixture faultedProcess = DriverFixture.Ready();
+        HookToken faultedPoll = faultedProcess.Driver.PlayerPollEntered();
+        faultedProcess.Driver.PhysicalPollReturned(2);
+        HookToken faultedProcessToken =
+            faultedProcess.Driver.ProcessInputEntered(
+                faultedProcess.State, 2, 10.0);
+        faultedProcess.Driver.TryFault("observer_exception");
+        int faultedProcessEvents = faultedProcess.Events.Count;
+        faultedProcess.Driver.ClearThrew(faultedProcessToken);
+        faultedProcess.Driver.ClearThrew(faultedPoll);
+        Check.False(faultedProcessToken.TryConsume(),
+            "faulted ProcessInput cleanup consumes token once");
+        Check.False(faultedPoll.TryConsume(),
+            "faulted outer poll cleanup consumes token once");
+        Check.Equal(faultedProcessEvents,
+            faultedProcess.Events.Count,
+            "faulted ProcessInput cleanup is output-inert");
+
+        DriverFixture disposedUndo = DriverFixture.Ready();
+        HookToken undo = disposedUndo.Driver.UndoEntered(
+            disposedUndo.State, 10.0);
+        disposedUndo.Driver.Dispose();
+        int disposedUndoEvents = disposedUndo.Events.Count;
+        disposedUndo.Driver.ClearThrew(undo);
+        Check.False(undo.TryConsume(),
+            "disposed Undo cleanup consumes token once");
+        Check.Equal(disposedUndoEvents, disposedUndo.Events.Count,
+            "disposed Undo cleanup is output-inert");
+
+        DriverFixture faultedState = DriverFixture.Ready();
+        HookToken state = faultedState.Driver.StateSetEntered(
+            faultedState.State, faultedState.OtherState);
+        faultedState.Driver.TryFault("observer_exception");
+        int faultedStateEvents = faultedState.Events.Count;
+        faultedState.Driver.StateSetReturned(
+            state, faultedState.OtherState, 10.0);
+        faultedState.Driver.StateSetReturned(
+            state, faultedState.OtherState, 10.0);
+        Check.False(state.TryConsume(),
+            "faulted StateSet return consumes token once");
+        Check.Equal(faultedStateEvents, faultedState.Events.Count,
+            "faulted StateSet return cleanup is output-inert");
+
+        DriverFixture disposedStateReturn = DriverFixture.Ready();
+        HookToken disposedStateReturnToken =
+            disposedStateReturn.Driver.StateSetEntered(
+                disposedStateReturn.State,
+                disposedStateReturn.OtherState);
+        disposedStateReturn.Driver.Dispose();
+        int disposedStateReturnEvents =
+            disposedStateReturn.Events.Count;
+        disposedStateReturn.Driver.StateSetReturned(
+            disposedStateReturnToken,
+            disposedStateReturn.OtherState,
+            10.0);
+        disposedStateReturn.Driver.StateSetReturned(
+            disposedStateReturnToken,
+            disposedStateReturn.OtherState,
+            10.0);
+        Check.False(disposedStateReturnToken.TryConsume(),
+            "disposed StateSet return consumes token once");
+        Check.Equal(disposedStateReturnEvents,
+            disposedStateReturn.Events.Count,
+            "disposed StateSet return cleanup is output-inert");
+        Check.Equal(1, disposedStateReturn.Sink.CloseCalls,
+            "disposed StateSet return does not close twice");
+
+        DriverFixture disabledState = DriverFixture.Ready();
+        HookToken disabledStateToken =
+            disabledState.Driver.StateSetEntered(
+                disabledState.State, disabledState.OtherState);
+        disabledState.Driver.Disable();
+        int disabledStateEvents = disabledState.Events.Count;
+        disabledState.Driver.StateSetThrew(disabledStateToken);
+        Check.False(disabledStateToken.TryConsume(),
+            "disabled StateSet throw consumes token once");
+        Check.Equal(disabledStateEvents, disabledState.Events.Count,
+            "disabled StateSet throw cleanup is output-inert");
+
+        DriverFixture disposedState = DriverFixture.Ready();
+        HookToken disposedStateToken =
+            disposedState.Driver.StateSetEntered(
+                disposedState.State, disposedState.OtherState);
+        disposedState.Driver.Dispose();
+        int disposedStateEvents = disposedState.Events.Count;
+        disposedState.Driver.ClearThrew(disposedStateToken);
+        Check.False(disposedStateToken.TryConsume(),
+            "disposed StateSet cleanup consumes token once");
+        Check.Equal(disposedStateEvents, disposedState.Events.Count,
+            "disposed generic StateSet cleanup is output-inert");
+    }
+
+}
+
+internal sealed class ReentrantErrorTraceSink : ITraceSink
+{
+    private readonly FakeTraceSink inner;
+    private bool reentered;
+
+    internal ReentrantErrorTraceSink(FakeTraceSink inner)
+    {
+        this.inner = inner;
+    }
+
+    internal PassiveDriver Driver;
+    internal HookToken InnerRestart;
+    internal HookToken NestedUndo;
+
+    public void WriteRun(RunRecord record)
+    {
+        inner.WriteRun(record);
+    }
+
+    public void WriteInitial(InitialRecord record)
+    {
+        inner.WriteInitial(record);
+    }
+
+    public void WriteStep(StepRecord record)
+    {
+        inner.WriteStep(record);
+    }
+
+    public void WriteEnd(EndRecord record)
+    {
+        inner.WriteEnd(record);
+    }
+
+    public void WriteError(ErrorRecord record)
+    {
+        if (!reentered)
+        {
+            reentered = true;
+            InnerRestart = Driver.RestartEntered();
+            NestedUndo = Driver.UndoEntered(new object(), 1.0);
+            Driver.RestoreObserved();
+            Driver.UndoReturned(NestedUndo, false);
+        }
+        inner.WriteError(record);
+    }
+
+    public void Close()
+    {
+        inner.Close();
+    }
 }
diff --git a/oracle/plugin/tests/Program.cs b/oracle/plugin/tests/Program.cs
index b89c789b98c2f6872521d0c3655ed32af168220a..d1d808c2b052fd1ca2dfe710f7af2dbe4607be42 100644
--- a/oracle/plugin/tests/Program.cs
+++ b/oracle/plugin/tests/Program.cs
@@ -23,7 +23,7 @@ private static int Main(string[] args)
             { "sink", 6 },
             { "driver-boundary", 2 },
             { "driver-initial", 8 },
-            { "driver-input", 6 }
+            { "driver-input", 8 }
         });
         int result = tests.Run(options.Cohort);
         if (result != 0)
~~~
<!-- TASK5-PATCH-END:C52-TESTS -->

**C52-PRODUCTION patch:** SHA-256 `69f717ed83deb3ff86fed13798764aa29f0120b29b7a649104d6cace218edd7e`; 395 LF lines; 12407 bytes.
<!-- TASK5-PATCH-BEGIN:C52-PRODUCTION -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index 9227970d1ea6a2d20420bf42a24d51318a301184..bf8a6b9417d7b04126f6907441a0633e5f112f6c 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -32,6 +32,7 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private struct FaultRequest
     {
+        internal bool ForceNullInputs;
         internal bool HasOffendingInput;
         internal int? OffendingIndex;
         internal OracleInput? OffendingInput;
@@ -59,6 +60,13 @@ internal sealed partial class PassiveDriver : IDisposable
             value.OffendingInput = input;
             return value;
         }
+
+        internal static FaultRequest Restart()
+        {
+            FaultRequest value = new FaultRequest();
+            value.ForceNullInputs = true;
+            return value;
+        }
     }
 
     private readonly ITraceSink sink;
@@ -532,7 +540,12 @@ internal sealed partial class PassiveDriver : IDisposable
     {
         if (!IsObservationActive())
         {
-            ConsumeLateToken(token, HookKind.PlayerPoll);
+            if (ConsumeLateToken(token, HookKind.PlayerPoll)
+                && playerPoll != null
+                && playerPoll.Id == token.Id)
+            {
+                playerPoll = null;
+            }
             return;
         }
         if (!ConsumeOrdinaryToken(token, HookKind.PlayerPoll))
@@ -555,7 +568,12 @@ internal sealed partial class PassiveDriver : IDisposable
     {
         if (!IsObservationActive())
         {
-            ConsumeLateToken(token, HookKind.PlayerPoll);
+            if (ConsumeLateToken(token, HookKind.PlayerPoll)
+                && playerPoll != null
+                && playerPoll.Id == token.Id)
+            {
+                playerPoll = null;
+            }
             return;
         }
         if (!ConsumeCleanupToken(token, HookKind.PlayerPoll))
@@ -872,14 +890,15 @@ internal sealed partial class PassiveDriver : IDisposable
         return token.TryConsume();
     }
 
-    private void ConsumeLateToken(
+    private bool ConsumeLateToken(
         HookToken token,
         HookKind expectedKind)
     {
         if (token == null || !token.Active)
-            return;
+            return false;
         if (token.BelongsTo(this) && token.Kind == expectedKind)
-            token.TryConsume();
+            return token.TryConsume();
+        return false;
     }
 
     private bool TryFaultInternal(
@@ -926,7 +945,12 @@ internal sealed partial class PassiveDriver : IDisposable
     {
         int? inputIndex;
         OracleInput? input;
-        if (attemptPending)
+        if (request.ForceNullInputs)
+        {
+            inputIndex = null;
+            input = null;
+        }
+        else if (attemptPending)
         {
             inputIndex = completedInputs;
             input = attemptInput;
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index a61e8b856a010b8a439dd5b1d196213e3f31f634..d2c55897bf4ce17a7a1c5604e6952ab9fb07110e 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -75,15 +75,34 @@ internal sealed partial class PassiveDriver
         bool accepted,
         bool movementScheduled)
     {
+        if (!IsObservationActive())
+        {
+            if (ConsumeLateToken(token, HookKind.ProcessInput)
+                && processInput != null
+                && processInput.Id == token.Id)
+            {
+                processInput = null;
+            }
+            return;
+        }
         if (!ConsumeOrdinaryToken(
             token, HookKind.ProcessInput))
         {
             return;
         }
         if (processInput == null
-            || processInput.Id != token.Id
-            || !attemptPending
-            || attemptOutcomeKnown)
+            || processInput.Id != token.Id)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return;
+        }
+        if (!IsObservationActive())
+        {
+            processInput = null;
+            return;
+        }
+        if (!attemptPending || attemptOutcomeKnown)
         {
             TryFaultInternal(
                 "hook_order_mismatch", FaultRequest.Derived());
@@ -115,6 +134,8 @@ internal sealed partial class PassiveDriver
         object stateReference,
         double nowSeconds)
     {
+        if (restartDepth > 0)
+            return HookToken.Inert(HookKind.Undo);
         if (!IsObservationActive())
             return HookToken.Inert(HookKind.Undo);
         if (undoContext != null)
@@ -137,7 +158,7 @@ internal sealed partial class PassiveDriver
 
     internal void RestoreObserved()
     {
-        if (!IsObservationActive())
+        if (restartDepth > 0 || !IsObservationActive())
             return;
         if (undoContext == null || undoContext.RestoreSeen)
         {
@@ -152,12 +173,31 @@ internal sealed partial class PassiveDriver
         HookToken token,
         bool movementScheduled)
     {
+        if (!IsObservationActive())
+        {
+            if (ConsumeLateToken(token, HookKind.Undo)
+                && undoContext != null
+                && undoContext.Id == token.Id)
+            {
+                undoContext = null;
+            }
+            return;
+        }
         if (!ConsumeOrdinaryToken(token, HookKind.Undo))
             return;
         if (undoContext == null
-            || undoContext.Id != token.Id
-            || !attemptPending
-            || attemptOutcomeKnown)
+            || undoContext.Id != token.Id)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return;
+        }
+        if (!IsObservationActive())
+        {
+            undoContext = null;
+            return;
+        }
+        if (!attemptPending || attemptOutcomeKnown)
         {
             TryFaultInternal(
                 "hook_order_mismatch", FaultRequest.Derived());
diff --git a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
new file mode 100644
index 0000000000000000000000000000000000000000..d4f1b49e8680676cd6b632390aa337dd58799d70
--- /dev/null
+++ b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
@@ -0,0 +1,207 @@
+using System;
+using System.Collections.Generic;
+
+internal sealed partial class PassiveDriver
+{
+    private sealed class StateSetContext
+    {
+        internal long Id;
+        internal object Before;
+    }
+
+    private readonly List<long> restartContexts =
+        new List<long>();
+    private int restartDepth;
+    private StateSetContext stateSetContext;
+
+    internal HookToken RestartEntered()
+    {
+        bool nested = restartDepth > 0;
+        if (!nested && !IsObservationActive())
+            return HookToken.Inert(HookKind.Restart);
+
+        HookToken token = NewToken(HookKind.Restart);
+        if (!token.Active)
+            return token;
+        restartContexts.Add(token.Id);
+        restartDepth++;
+
+        if (!nested)
+        {
+            TryFaultInternal(
+                "unexpected_input", FaultRequest.Restart());
+        }
+        return token;
+    }
+
+    internal void RestartReturned(HookToken token)
+    {
+        ValidateRestartPopOrder(token);
+        if (!ConsumeOrdinaryToken(token, HookKind.Restart))
+            return;
+        PopRestart(token.Id);
+    }
+
+    internal void RestartThrew(HookToken token)
+    {
+        ValidateRestartPopOrder(token);
+        if (!ConsumeCleanupToken(token, HookKind.Restart))
+            return;
+        PopRestart(token.Id);
+    }
+
+    internal HookToken StateSetEntered(
+        object beforeState,
+        object requestedState)
+    {
+        if (!IsObservationActive())
+            return HookToken.Inert(HookKind.StateSet);
+        if (stateSetContext != null)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return HookToken.Inert(HookKind.StateSet);
+        }
+        HookToken token = NewToken(HookKind.StateSet);
+        if (!token.Active)
+            return token;
+        stateSetContext = new StateSetContext
+        {
+            Id = token.Id,
+            Before = beforeState
+        };
+        return token;
+    }
+
+    internal void StateSetReturned(
+        HookToken token,
+        object afterState,
+        double nowSeconds)
+    {
+        if (!IsObservationActive())
+        {
+            if (ConsumeLateToken(token, HookKind.StateSet)
+                && stateSetContext != null
+                && stateSetContext.Id == token.Id)
+            {
+                stateSetContext = null;
+            }
+            return;
+        }
+        if (!ConsumeOrdinaryToken(token, HookKind.StateSet))
+            return;
+        if (stateSetContext == null
+            || stateSetContext.Id != token.Id)
+        {
+            TryFaultInternal(
+                "hook_order_mismatch", FaultRequest.Derived());
+            return;
+        }
+        StateSetContext context = stateSetContext;
+        stateSetContext = null;
+        if (!IsObservationActive())
+            return;
+        if (!IsValidMonotonic(nowSeconds))
+        {
+            TryFaultInternal(
+                "observer_exception", FaultRequest.Derived());
+            return;
+        }
+
+        if (phase == PassivePhase.AwaitGame
+            || phase == PassivePhase.AwaitInitialNeutral)
+        {
+            if (afterState == null)
+            {
+                ResetToAwaitGame();
+            }
+            else if (!Object.ReferenceEquals(
+                context.Before, afterState))
+            {
+                StartInitialEpoch(afterState, nowSeconds, false);
+            }
+            return;
+        }
+
+        if (!Object.ReferenceEquals(context.Before, afterState))
+        {
+            TryFaultInternal(
+                "state_replaced", FaultRequest.Derived());
+        }
+    }
+
+    internal void StateSetThrew(HookToken token)
+    {
+        if (!ConsumeCleanupToken(token, HookKind.StateSet))
+            return;
+        if (stateSetContext == null
+            || stateSetContext.Id != token.Id)
+        {
+            throw new InvalidOperationException(
+                "SetGameState token mismatch");
+        }
+        stateSetContext = null;
+    }
+
+    internal void ClearThrew(HookToken token)
+    {
+        if (token == null || !token.Active)
+            return;
+        switch (token.Kind)
+        {
+            case HookKind.PlayerPoll:
+                PlayerPollThrew(token);
+                return;
+            case HookKind.ProcessInput:
+                ProcessInputThrew(token);
+                return;
+            case HookKind.Undo:
+                UndoThrew(token);
+                return;
+            case HookKind.Restart:
+                RestartThrew(token);
+                return;
+            case HookKind.StateSet:
+                StateSetThrew(token);
+                return;
+            default:
+                throw new InvalidOperationException(
+                    "unknown hook token kind");
+        }
+    }
+
+    private void PopRestart(long id)
+    {
+        int last = restartContexts.Count - 1;
+        if (last < 0 || restartContexts[last] != id)
+        {
+            throw new InvalidOperationException(
+                "Restart token mismatch");
+        }
+        restartContexts.RemoveAt(last);
+        restartDepth--;
+        if (restartDepth < 0
+            || restartDepth != restartContexts.Count)
+        {
+            throw new InvalidOperationException(
+                "Restart depth imbalance");
+        }
+    }
+
+    private void ValidateRestartPopOrder(HookToken token)
+    {
+        if (token == null
+            || !token.Active
+            || !token.BelongsTo(this)
+            || token.Kind != HookKind.Restart)
+        {
+            return;
+        }
+        int index = restartContexts.IndexOf(token.Id);
+        if (index >= 0 && index != restartContexts.Count - 1)
+        {
+            throw new InvalidOperationException(
+                "Restart token mismatch");
+        }
+    }
+}
~~~
<!-- TASK5-PATCH-END:C52-PRODUCTION -->

The C52 tests-only forced build must exit `1` solely with the authenticated missing-member set for `RestartEntered`, `RestartReturned`, `RestartThrew`, `StateSetEntered`, `StateSetReturned`, `StateSetThrew`, and `ClearThrew`. The raw build emits 232 error lines; C-sorting and exact de-duplication yields 116 normalized error lines with SHA-256 `7f3ccf0944fa78360f52ab8c00731d388f4ed30d92dc9abf985db54603ba7c76`. The canonical compact diagnostic is 116 lines, 8431 bytes, SHA-256 `4222e97661293a4ff7b83a3c3e2352e56894fa7e260e8389a718667148069935`. It must preserve the six C51 registration identities and fail before a test run.

The sole executable C52 compiler-RED invocation appears in Task 2 Step 2;
this catalog paragraph is descriptive and must not be run separately.

### C53 patches

**C53-TESTS patch:** SHA-256 `d56cb0b64868120338b27ced71299da7b78a87187a7b8dfa70b63bde329e7dcc`; 1123 LF lines; 43301 bytes.
<!-- TASK5-PATCH-BEGIN:C53-TESTS -->
~~~diff
diff --git a/oracle/plugin/tests/PassiveDriverInputTests.cs b/oracle/plugin/tests/PassiveDriverInputTests.cs
index e0a09eb8931838d12984a05cfa6fd90bf280557d..fbbe505b6b9782610c9e2f4108cd1945418d126d 100644
--- a/oracle/plugin/tests/PassiveDriverInputTests.cs
+++ b/oracle/plugin/tests/PassiveDriverInputTests.cs
@@ -390,7 +390,7 @@ internal static class PassiveDriverInputTests
         PopulatedErrorPreflightRejectsBoundaryCapture();
         StepFailureIsTerminal();
         StepPrecedesIntermediateReady();
-        EverySettledStepReportsReady();
+        EveryIntermediateSettledStepReportsReady();
     }
 
     private static void UndoAcceptanceAndRestoreRules()
@@ -1072,7 +1072,7 @@ internal static class PassiveDriverInputTests
             "custom-budget ready fixture");
     }
 
-    private static void EverySettledStepReportsReady()
+    private static void EveryIntermediateSettledStepReportsReady()
     {
         DriverFixture fixture = DriverFixture.Ready();
 
@@ -1084,33 +1084,23 @@ internal static class PassiveDriverInputTests
         fixture.SettleCurrent(
             ProtocolSamples.Capture("step-one"), 21.0);
 
-        fixture.OpenUndo(true, false, 30.0);
-        fixture.SettleCurrent(
-            ProtocolSamples.Capture("step-two"), 31.0);
-
-        Check.Equal(3, fixture.Sink.StepRecords.Count,
-            "three settled attempts write three Steps");
+        Check.Equal(2, fixture.Sink.StepRecords.Count,
+            "two intermediate attempts write two Steps");
         Check.Equal(0, fixture.Sink.StepRecords[0].InputIndex,
             "Step 0 index");
         Check.Equal(1, fixture.Sink.StepRecords[1].InputIndex,
             "Step 1 index");
-        Check.Equal(2, fixture.Sink.StepRecords[2].InputIndex,
-            "Step 2 index");
-        Check.Equal(4, fixture.Reporter.ReadyValues.Count,
-            "Initial and every Step report Ready");
-        Check.Equal(1, fixture.Reporter.ReadyValues[1],
-            "Step 0 reports Ready(1)");
-        Check.Equal(2, fixture.Reporter.ReadyValues[2],
-            "Step 1 reports Ready(2)");
-        Check.Equal(3, fixture.Reporter.ReadyValues[3],
-            "Step 2 reports Ready(3)");
+        Check.Sequence(
+            new int[] { 0, 1, 2 },
+            fixture.Reporter.ReadyValues,
+            "Initial and intermediate Steps report Ready 0 1 2");
         Check.Equal(PassivePhase.Ready, fixture.Driver.Phase,
-            "Task 5.1 Step 2 remains Ready");
+            "Step 1 returns to Ready");
         Check.Sequence(
-            new string[] { "sink:step:2", "report:ready:3/3" },
+            new string[] { "sink:step:1", "report:ready:2/3" },
             fixture.Events.GetRange(
                 fixture.Events.Count - 2, 2).ToArray(),
-            "Step 2 is durable before Ready(3)");
+            "Step 1 is durable before Ready(2)");
     }
 
     private static void RestartDepthAndNullFields()
diff --git a/oracle/plugin/tests/PassiveDriverTerminalTests.cs b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
new file mode 100644
index 0000000000000000000000000000000000000000..c88849e2f4d9406ad3ca3b1fb646c740d0fd1179
--- /dev/null
+++ b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
@@ -0,0 +1,847 @@
+using System;
+using System.Collections.Generic;
+using System.Threading;
+
+internal static class PassiveDriverTerminalTests
+{
+    internal static void Register(TestRegistry tests)
+    {
+        tests.Add("driver-terminal", "three steps End Close Complete order",
+            ThreeStepsEndCloseCompleteOrder);
+        tests.Add("driver-terminal", "error field policy is exact",
+            ErrorFieldPolicyIsExact);
+        tests.Add("driver-terminal", "sink failure uses trace io marker",
+            SinkFailureUsesTraceIoMarker);
+        tests.Add("driver-terminal", "completion reporter cannot rewrite trace",
+            CompletionReporterCannotRewriteTrace);
+        tests.Add("driver-terminal", "first fault wins race",
+            FirstFaultWinsRace);
+        tests.Add("driver-terminal", "Dispose and late callbacks are final",
+            DisposeAndLateCallbacksAreFinal);
+    }
+
+    private static void ThreeStepsEndCloseCompleteOrder()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteThreeSteps();
+
+        Check.Equal(
+            PassivePhase.Done,
+            fixture.Driver.Phase,
+            "durable Step 2 must enter Done without Ready(3) and emit End Close Complete");
+        Check.Equal(3, fixture.Sink.StepRecords.Count,
+            "exactly three durable Steps");
+        for (int index = 0; index < 3; index++)
+        {
+            Check.Equal(index, fixture.Sink.StepRecords[index].InputIndex,
+                "Step indices are contiguous");
+        }
+        Check.Sequence(
+            new int[] { 0, 1, 2 },
+            fixture.Reporter.ReadyValues,
+            "terminal Step emits no Ready(3)");
+        Check.Equal(1, fixture.Sink.EndRecords.Count, "one End");
+        Check.Equal(OracleProtocol.ExpectedInputCount,
+            fixture.Sink.EndRecords[0].InputCount,
+            "End carries the validated expected count");
+        Check.Equal(DriverFixture.UtcFinish,
+            fixture.Sink.EndRecords[0].FinishedAtUtc,
+            "End carries the final observation UTC");
+        Check.Equal(1, fixture.Sink.CloseCalls, "one Close");
+        Check.Equal(1, fixture.Reporter.CompleteCalls, "one Complete");
+        Check.Equal(0, fixture.Reporter.FailedCalls, "no failure marker");
+        Check.Equal(0, fixture.Sink.ErrorCalls, "success never attempts Error");
+        Check.Equal(0, fixture.Sink.ErrorRecords.Count, "success has no Error");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:run",
+                "sink:initial",
+                "report:ready:0/3",
+                "sink:step:0",
+                "report:ready:1/3",
+                "sink:step:1",
+                "report:ready:2/3",
+                "sink:step:2",
+                "sink:end",
+                "sink:close",
+                "report:complete"
+            },
+            TerminalEvents(fixture),
+            "Step 2 End Close Complete order is exact");
+
+        DriverFixture equality = DriverFixture.Ready();
+        equality.CompleteFirstTwoSteps();
+        equality.CompleteThirdStep(equality.Driver.StartedAtUtc);
+        Check.Equal(PassivePhase.Done, equality.Driver.Phase,
+            "UTC equal to started_at_utc is accepted");
+        Check.Equal(equality.Driver.StartedAtUtc,
+            equality.Sink.EndRecords[0].FinishedAtUtc,
+            "UTC equality is retained in End");
+    }
+
+    private static void ErrorFieldPolicyIsExact()
+    {
+        DriverFixture offending = DriverFixture.Active();
+        HookToken offendingPoll = offending.Driver.PlayerPollEntered();
+        offending.Driver.PhysicalPollReturned(0);
+        offending.Driver.ProcessInputEntered(
+            offending.State, 0, 1.0);
+        offending.Driver.PlayerPollReturned(offendingPoll);
+        AssertError(
+            offending.Sink.ErrorRecords[0],
+            "input_before_initial",
+            0,
+            OracleInput.North,
+            0,
+            "recognized offending input");
+
+        DriverFixture unknown = DriverFixture.Ready();
+        HookToken unknownPoll = unknown.Driver.PlayerPollEntered();
+        unknown.Driver.PhysicalPollReturned(77);
+        unknown.Driver.PlayerPollReturned(unknownPoll);
+        AssertError(
+            unknown.Sink.ErrorRecords[0],
+            "unexpected_input",
+            0,
+            null,
+            0,
+            "unknown native input");
+
+        DriverFixture pending = DriverFixture.Ready();
+        pending.OpenDirection(2, true, true, 10.0);
+        pending.Neutral();
+        pending.Observe(
+            pending.State,
+            pending.State,
+            11.0,
+            true,
+            ProtocolSamples.MovedCapture);
+        pending.Driver.TryFault("settle_timeout");
+        AssertError(
+            pending.Sink.ErrorRecords[0],
+            "settle_timeout",
+            0,
+            OracleInput.West,
+            1,
+            "pending attempt");
+        Check.Same(ProtocolSamples.MovedCapture,
+            pending.Sink.ErrorRecords[0].LastCapture,
+            "pending attempt retains latest bounded capture");
+
+        DriverFixture pendingUnknown = DriverFixture.Ready();
+        pendingUnknown.OpenDirection(2, true, true, 10.0);
+        HookToken pendingUnknownPoll =
+            pendingUnknown.Driver.PlayerPollEntered();
+        pendingUnknown.Driver.PhysicalPollReturned(77);
+        pendingUnknown.Driver.PlayerPollReturned(pendingUnknownPoll);
+        AssertError(
+            pendingUnknown.Sink.ErrorRecords[0],
+            "unexpected_input",
+            0,
+            OracleInput.West,
+            0,
+            "pending attempt overrides unknown native fields");
+
+        DriverFixture restart = DriverFixture.Ready();
+        restart.OpenDirection(2, true, true, 10.0);
+        restart.Observe(
+            restart.State,
+            restart.State,
+            11.0,
+            false,
+            ProtocolSamples.MovedCapture);
+        HookToken restartToken = restart.Driver.RestartEntered();
+        restart.Driver.RestartReturned(restartToken);
+        AssertError(
+            restart.Sink.ErrorRecords[0],
+            "unexpected_input",
+            null,
+            null,
+            1,
+            "Restart overrides pending input fields");
+
+        DriverFixture initial = DriverFixture.Active();
+        initial.Observe(
+            initial.State,
+            initial.State,
+            1.0,
+            false,
+            ProtocolSamples.InitialCapture);
+        initial.Driver.TryFault("observer_exception");
+        AssertError(
+            initial.Sink.ErrorRecords[0],
+            "observer_exception",
+            null,
+            null,
+            1,
+            "generic initial fault uses active initial frames");
+
+        DriverFixture generic = DriverFixture.Ready();
+        generic.Driver.TryFault("observer_exception");
+        AssertError(
+            generic.Sink.ErrorRecords[0],
+            "observer_exception",
+            null,
+            null,
+            0,
+            "generic Ready fault has null fields and zero frames");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:observer_exception"
+            },
+            Tail(TerminalEvents(generic), 3),
+            "ordinary fault order is Error Close Failed");
+
+        DriverFixture earlyUtc = DriverFixture.Ready();
+        earlyUtc.CompleteFirstTwoSteps();
+        DateTime beforeStart = earlyUtc.Driver.StartedAtUtc.AddTicks(-1L);
+        earlyUtc.CompleteThirdStep(beforeStart);
+        Check.Equal(3, earlyUtc.Sink.StepRecords.Count,
+            "UTC relation is checked after durable Step 2");
+        Check.Equal(PassivePhase.Faulted, earlyUtc.Driver.Phase,
+            "UTC before started_at_utc faults");
+        Check.Equal(0, earlyUtc.Sink.EndRecords.Count,
+            "invalid final UTC emits no End");
+        Check.Equal(0, earlyUtc.Sink.EndCalls,
+            "invalid final UTC never attempts End");
+        Check.Equal(0, earlyUtc.Reporter.CompleteCalls,
+            "invalid final UTC emits no Complete");
+        AssertError(
+            earlyUtc.Sink.ErrorRecords[0],
+            "observer_exception",
+            null,
+            null,
+            0,
+            "invalid final UTC follows ordinary observer policy");
+        Check.True(earlyUtc.Sink.ErrorRecords[0].LastCapture == null,
+            "invalid final UTC has no pending capture");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:observer_exception"
+            },
+            Tail(TerminalEvents(earlyUtc), 4),
+            "invalid final UTC keeps Step 2 then Error Close Failed");
+    }
+
+    private static void SinkFailureUsesTraceIoMarker()
+    {
+        DriverFixture step = DriverFixture.Ready();
+        step.CompleteFirstTwoSteps();
+        step.Sink.StepFailure = new TraceIoException("step 2");
+        step.CompleteThirdStep(DriverFixture.UtcFinish);
+        Check.Equal(PassivePhase.Faulted, step.Driver.Phase,
+            "Step 2 failure phase");
+        Check.Equal(3, step.Sink.StepCalls, "Step 2 attempted once");
+        Check.Equal(2, step.Sink.StepRecords.Count,
+            "failed Step 2 is not claimed durable");
+        Check.Equal(0, step.Sink.ErrorCalls,
+            "Step 2 failure never attempts Error");
+        Check.Equal(0, step.Sink.EndCalls,
+            "Step 2 failure never attempts End");
+        AssertTraceIoTerminal(step, 0, 0,
+            "Step 2 failure is marker-only");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            Tail(TerminalEvents(step), 3),
+            "Step 2 failure closes without Error Ready or completion");
+        Check.Sequence(new int[] { 0, 1, 2 },
+            step.Reporter.ReadyValues,
+            "Step 2 failure emits no Ready(3)");
+
+        DriverFixture errorWrite = DriverFixture.Ready();
+        errorWrite.Sink.ErrorFailure = new TraceIoException("error");
+        errorWrite.Driver.TryFault("observer_exception");
+        Check.Equal(1, errorWrite.Sink.ErrorCalls, "Error attempted once");
+        Check.Equal(0, errorWrite.Sink.ErrorRecords.Count,
+            "failed Error is not claimed durable");
+        AssertTraceIoTerminal(errorWrite, 0, 0,
+            "Error write failure is marker-only");
+
+        DriverFixture ordinaryClose = DriverFixture.Ready();
+        ordinaryClose.Sink.CloseFailure =
+            new TraceIoException("ordinary close");
+        ordinaryClose.Driver.TryFault("observer_exception");
+        Check.Equal(1, ordinaryClose.Sink.ErrorRecords.Count,
+            "Error is durable before ordinary Close failure");
+        Check.Equal(1, ordinaryClose.Sink.ErrorCalls,
+            "ordinary fault attempts Error once");
+        AssertTraceIoTerminal(ordinaryClose, 1, 0,
+            "ordinary Close failure uses trace I/O marker");
+
+        DriverFixture end = DriverFixture.Ready();
+        end.Sink.EndFailure = new TraceIoException("end");
+        end.CompleteThreeSteps();
+        Check.Equal(1, end.Sink.EndCalls, "End attempted once");
+        Check.Equal(0, end.Sink.EndRecords.Count,
+            "failed End is not claimed durable");
+        Check.Equal(0, end.Sink.ErrorCalls,
+            "End failure never attempts Error");
+        AssertTraceIoTerminal(end, 0, 0,
+            "End failure is marker-only");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:end",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            Tail(TerminalEvents(end), 4),
+            "End failure order");
+
+        DriverFixture terminalClose = DriverFixture.Ready();
+        terminalClose.Sink.CloseFailure =
+            new TraceIoException("terminal close");
+        terminalClose.CompleteThreeSteps();
+        Check.Equal(1, terminalClose.Sink.EndRecords.Count,
+            "End remains durable before terminal Close failure");
+        Check.Equal(1, terminalClose.Sink.EndCalls,
+            "terminal End is attempted once");
+        Check.Equal(0, terminalClose.Sink.ErrorCalls,
+            "terminal Close failure never attempts Error");
+        AssertTraceIoTerminal(terminalClose, 0, 1,
+            "terminal Close failure is marker-only");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:end",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            Tail(TerminalEvents(terminalClose), 4),
+            "terminal Close failure order");
+    }
+
+    private static void CompletionReporterCannotRewriteTrace()
+    {
+        AssertCompleteFailure(false);
+        AssertCompleteFailure(true);
+    }
+
+    private static void AssertCompleteFailure(bool failedAlsoThrows)
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.Reporter.CompleteFailure =
+            new InvalidOperationException("complete");
+        if (failedAlsoThrows)
+        {
+            fixture.Reporter.FailedFailure =
+                new InvalidOperationException("failed");
+        }
+        fixture.CompleteThreeSteps();
+
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            "Complete exception changes only in-memory phase");
+        Check.Equal(1, fixture.Sink.EndRecords.Count,
+            "closed success End remains unique");
+        Check.Equal(1, fixture.Sink.EndCalls,
+            "closed success End is attempted once");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "Complete exception never attempts Error");
+        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
+            "Complete exception cannot append Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "Complete exception cannot Close twice");
+        Check.Equal(1, fixture.Reporter.CompleteCalls,
+            "Complete attempted exactly once");
+        Check.Equal(1, fixture.Reporter.FailedCalls,
+            "observer_exception fallback attempted exactly once");
+        Check.Sequence(
+            new string[] { "observer_exception" },
+            fixture.Reporter.FailedCodes,
+            "Complete exception owns explicit observer fallback");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:end",
+                "sink:close",
+                "report:complete",
+                "report:failed:observer_exception"
+            },
+            Tail(TerminalEvents(fixture), 5),
+            "Complete failure leaves closed trace immutable");
+
+        int terminalCount = TerminalEvents(fixture).Count;
+        Check.False(fixture.Driver.TryFault("capture_failed"),
+            "later fault cannot replace Complete failure");
+        fixture.Driver.Dispose();
+        fixture.Driver.Dispose();
+        Check.Equal(terminalCount, TerminalEvents(fixture).Count,
+            "fallback failure and Dispose remain output-inert");
+    }
+
+    private static void FirstFaultWinsRace()
+    {
+        FaultFaultRace();
+        SuccessWinsWhileEndIsBlocked();
+        SuccessWinsWhileCompleteIsBlocked();
+        FaultWinsWhileDurableStepIsBlocked();
+    }
+
+    private static void FaultFaultRace()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        int winners = 0;
+        Exception firstError = null;
+        Exception secondError = null;
+        using (ManualResetEvent start = new ManualResetEvent(false))
+        {
+            Thread first = new Thread(delegate()
+            {
+                try
+                {
+                    start.WaitOne();
+                    if (fixture.Driver.TryFault("observer_exception"))
+                        Interlocked.Increment(ref winners);
+                }
+                catch (Exception error)
+                {
+                    firstError = error;
+                }
+            });
+            Thread second = new Thread(delegate()
+            {
+                try
+                {
+                    start.WaitOne();
+                    if (fixture.Driver.TryFault("capture_failed"))
+                        Interlocked.Increment(ref winners);
+                }
+                catch (Exception error)
+                {
+                    secondError = error;
+                }
+            });
+            first.Start();
+            second.Start();
+            start.Set();
+            bool firstJoined = first.Join(5000);
+            bool secondJoined = second.Join(5000);
+            Check.True(firstJoined && secondJoined,
+                "fault race threads finish");
+        }
+        Check.True(firstError == null && secondError == null,
+            "fault race worker has no exception");
+        Check.Equal(1, winners, "one fault owns terminal state");
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            "fault race writes one Error");
+        string winningCode = fixture.Sink.ErrorRecords[0].Code;
+        Check.True(
+            winningCode == "observer_exception"
+                || winningCode == "capture_failed",
+            "fault race retains one of the two raced codes");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "fault race closes once");
+        Check.Equal(1, fixture.Reporter.FailedCalls,
+            "fault race reports one failure marker");
+        Check.Equal(winningCode, fixture.Reporter.FailedCodes[0],
+            "fault race Error and Failed preserve the same winner");
+    }
+
+    private static void SuccessWinsWhileEndIsBlocked()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = true;
+        bool faultFinishedBeforeRelease = false;
+        using (ManualResetEvent endEntered = new ManualResetEvent(false))
+        using (ManualResetEvent releaseEnd = new ManualResetEvent(false))
+        using (ManualResetEvent faultFinished = new ManualResetEvent(false))
+        {
+            fixture.Sink.EndObserved = delegate(EndRecord record)
+            {
+                endEntered.Set();
+                releaseEnd.WaitOne();
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("observer_exception");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+                finally
+                {
+                    faultFinished.Set();
+                }
+            });
+            completion.Start();
+            bool reachedEnd = endEntered.WaitOne(5000);
+            bool completionJoined;
+            bool faultJoined;
+            try
+            {
+                if (reachedEnd)
+                {
+                    fault.Start();
+                    faultFinishedBeforeRelease =
+                        faultFinished.WaitOne(1000);
+                }
+            }
+            finally
+            {
+                releaseEnd.Set();
+            }
+            completionJoined = completion.Join(5000);
+            faultJoined = !reachedEnd || fault.Join(5000);
+
+            Check.True(reachedEnd, "success race reaches durable End");
+            Check.True(faultFinishedBeforeRelease,
+                "TryFault returns while WriteEnd is blocked without a driver monitor");
+            Check.True(completionJoined && faultJoined,
+                "success race threads finish");
+        }
+        Check.True(completionError == null && faultError == null,
+            "success race worker has no exception");
+        Check.False(faultResult,
+            "success terminal owner rejects concurrent fault");
+        Check.Equal(PassivePhase.Done, fixture.Driver.Phase,
+            "success race remains Done");
+        Check.Equal(1, fixture.Sink.EndRecords.Count,
+            "success race writes one End");
+        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
+            "success race writes no Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "success race closes once");
+        Check.Equal(1, fixture.Reporter.CompleteCalls,
+            "success race completes once");
+    }
+
+    private static void FaultWinsWhileDurableStepIsBlocked()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = false;
+        bool faultFinishedBeforeRelease = false;
+        using (ManualResetEvent stepEntered = new ManualResetEvent(false))
+        using (ManualResetEvent releaseStep = new ManualResetEvent(false))
+        using (ManualResetEvent faultFinished = new ManualResetEvent(false))
+        {
+            fixture.Sink.StepObserved = delegate(StepRecord record)
+            {
+                if (record.InputIndex == 2)
+                {
+                    stepEntered.Set();
+                    releaseStep.WaitOne();
+                }
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult = fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+                finally
+                {
+                    faultFinished.Set();
+                }
+            });
+            completion.Start();
+            bool reachedStep = stepEntered.WaitOne(5000);
+            bool completionJoined;
+            bool faultJoined;
+            try
+            {
+                if (reachedStep)
+                {
+                    fault.Start();
+                    faultFinishedBeforeRelease =
+                        faultFinished.WaitOne(1000);
+                }
+            }
+            finally
+            {
+                releaseStep.Set();
+            }
+            completionJoined = completion.Join(5000);
+            faultJoined = !reachedStep || fault.Join(5000);
+
+            Check.True(reachedStep, "fault race reaches durable Step 2");
+            Check.True(faultFinishedBeforeRelease,
+                "TryFault returns while WriteStep is blocked without a driver monitor");
+            Check.True(completionJoined && faultJoined,
+                "fault-first race threads finish");
+        }
+        Check.True(completionError == null && faultError == null,
+            "fault-first race worker has no exception");
+        Check.True(faultResult,
+            "fault claims shared owner before success");
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            "fault-first race remains Faulted after Step returns");
+        Check.Equal(3, fixture.Sink.StepRecords.Count,
+            "fault-first race retains durable Step 2");
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            "fault-first race writes one Error");
+        Check.Equal(0, fixture.Sink.EndRecords.Count,
+            "fault-first race suppresses End");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "fault-first race closes once");
+        Check.Equal(0, fixture.Reporter.CompleteCalls,
+            "fault-first race suppresses Complete");
+        Check.Equal(1, fixture.Reporter.FailedCalls,
+            "fault-first race reports one failure marker");
+    }
+
+    private static void SuccessWinsWhileCompleteIsBlocked()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = true;
+        bool faultFinishedBeforeRelease = false;
+        using (ManualResetEvent completeEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseComplete =
+            new ManualResetEvent(false))
+        using (ManualResetEvent faultFinished =
+            new ManualResetEvent(false))
+        {
+            fixture.Reporter.CompleteObserved = delegate()
+            {
+                completeEntered.Set();
+                releaseComplete.WaitOne();
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+                finally
+                {
+                    faultFinished.Set();
+                }
+            });
+            completion.Start();
+            bool reachedComplete = completeEntered.WaitOne(5000);
+            bool completionJoined;
+            bool faultJoined;
+            try
+            {
+                if (reachedComplete)
+                {
+                    fault.Start();
+                    faultFinishedBeforeRelease =
+                        faultFinished.WaitOne(1000);
+                }
+            }
+            finally
+            {
+                releaseComplete.Set();
+            }
+            completionJoined = completion.Join(5000);
+            faultJoined = !reachedComplete || fault.Join(5000);
+
+            Check.True(reachedComplete,
+                "completion race reaches reporter Complete");
+            Check.True(faultFinishedBeforeRelease,
+                "TryFault returns while Complete is blocked without a driver monitor");
+            Check.True(completionJoined && faultJoined,
+                "completion callback race threads finish");
+        }
+        Check.True(completionError == null && faultError == null,
+            "completion callback race worker has no exception");
+        Check.False(faultResult,
+            "success owner rejects fault during Complete callback");
+        Check.Equal(PassivePhase.Done, fixture.Driver.Phase,
+            "completion callback race remains Done");
+        Check.Equal(1, fixture.Sink.EndCalls,
+            "completion callback race attempts End once");
+        Check.Equal(1, fixture.Sink.EndRecords.Count,
+            "completion callback race retains one End");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "completion callback race never attempts Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "completion callback race closes once");
+        Check.Equal(1, fixture.Reporter.CompleteCalls,
+            "completion callback race attempts Complete once");
+        Check.Equal(0, fixture.Reporter.FailedCalls,
+            "completion callback race emits no failure marker");
+    }
+
+    private static void DisposeAndLateCallbacksAreFinal()
+    {
+        DriverFixture disposed = DriverFixture.Active();
+        HookToken openPoll = disposed.Driver.PlayerPollEntered();
+        disposed.Driver.Dispose();
+        disposed.Driver.Dispose();
+        disposed.Driver.ClearThrew(openPoll);
+        disposed.Driver.ClearThrew(openPoll);
+        Check.Equal(1, disposed.Sink.CloseCalls,
+            "Dispose closes at most once");
+        Check.Equal(0, disposed.Sink.EndRecords.Count,
+            "Dispose writes no End");
+        Check.Equal(0, disposed.Sink.ErrorRecords.Count,
+            "Dispose writes no Error");
+        Check.Equal(0, disposed.Reporter.FailedCalls,
+            "Dispose emits no terminal marker");
+        Check.False(disposed.Driver.TryFault("observer_exception"),
+            "disposed late fault is inert");
+        FakeUpdateObservation late =
+            new FakeUpdateObservation(disposed.Events)
+            {
+                FirstState = disposed.State,
+                SecondState = disposed.State,
+                Now = 5.0
+            };
+        disposed.Boundary.Observe(late);
+        Check.Equal(0, late.StateCalls,
+            "disposed late update does not inspect observation");
+
+        DriverFixture done = DriverFixture.Ready();
+        HookToken openStateSet =
+            done.Driver.StateSetEntered(done.State, done.State);
+        done.CompleteThreeSteps();
+        int doneEvents = done.Events.Count;
+        done.Driver.StateSetReturned(
+            openStateSet, done.State, 40.0);
+        done.Driver.StateSetReturned(
+            openStateSet, done.State, 40.0);
+        done.Driver.ClearThrew(openStateSet);
+        done.Driver.RestartEntered();
+        done.Driver.TryFault("observer_exception");
+        done.Driver.Dispose();
+        done.Driver.Dispose();
+        Check.Equal(doneEvents, done.Events.Count,
+            "Done matching cleanup and later callbacks are output-inert");
+        Check.Equal(PassivePhase.Done, done.Driver.Phase,
+            "Done remains final");
+        Check.Equal(1, done.Sink.CloseCalls,
+            "Done Dispose cannot Close twice");
+    }
+
+    private static void AssertError(
+        ErrorRecord error,
+        string code,
+        int? inputIndex,
+        OracleInput? input,
+        int frames,
+        string label)
+    {
+        Check.Equal(code, error.Code, label + " code");
+        Check.Equal(inputIndex, error.InputIndex, label + " input index");
+        Check.Equal(input, error.Input, label + " input");
+        Check.Equal(frames, error.SettleFrames, label + " frames");
+    }
+
+    private static void AssertTraceIoTerminal(
+        DriverFixture fixture,
+        int expectedErrors,
+        int expectedEnds,
+        string label)
+    {
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            label + " phase");
+        Check.Equal(expectedErrors, fixture.Sink.ErrorRecords.Count,
+            label + " Error count");
+        Check.Equal(expectedEnds, fixture.Sink.EndRecords.Count,
+            label + " End count");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            label + " Close count");
+        Check.Equal(0, fixture.Reporter.CompleteCalls,
+            label + " Complete count");
+        Check.Equal(1, fixture.Reporter.FailedCalls,
+            label + " failure marker count");
+        Check.Sequence(
+            new string[] { "trace_io_failed" },
+            fixture.Reporter.FailedCodes,
+            label + " failure marker");
+    }
+
+    private static List<string> TerminalEvents(DriverFixture fixture)
+    {
+        List<string> result = new List<string>();
+        for (int index = 0; index < fixture.Events.Count; index++)
+        {
+            string value = fixture.Events[index];
+            if (value.StartsWith("sink:", StringComparison.Ordinal)
+                || (value.StartsWith("report:", StringComparison.Ordinal)
+                    && !value.StartsWith(
+                        "report:diagnostic:", StringComparison.Ordinal)))
+            {
+                result.Add(value);
+            }
+        }
+        return result;
+    }
+
+    private static List<string> Tail(List<string> values, int count)
+    {
+        return values.GetRange(values.Count - count, count);
+    }
+}
diff --git a/oracle/plugin/tests/PassiveDriverTestSupport.cs b/oracle/plugin/tests/PassiveDriverTestSupport.cs
index 973127b67e1e5f7d760696f3f82f61ad144272c7..d0c0850c83bdf75804927cfc0c844a046d71ea2f 100644
--- a/oracle/plugin/tests/PassiveDriverTestSupport.cs
+++ b/oracle/plugin/tests/PassiveDriverTestSupport.cs
@@ -24,8 +24,11 @@ internal sealed class FakeTraceSink : ITraceSink
     internal Exception RunFailure { get; set; }
     internal Exception InitialFailure { get; set; }
     internal Exception StepFailure { get; set; }
+    internal Exception EndFailure { get; set; }
     internal Exception ErrorFailure { get; set; }
     internal Exception CloseFailure { get; set; }
+    internal Action<StepRecord> StepObserved { get; set; }
+    internal Action<EndRecord> EndObserved { get; set; }
     internal int RunCalls;
     internal int InitialCalls;
     internal int StepCalls;
@@ -58,13 +61,19 @@ internal sealed class FakeTraceSink : ITraceSink
         if (StepFailure != null)
             throw StepFailure;
         StepRecords.Add(record);
+        if (StepObserved != null)
+            StepObserved(record);
     }
 
     public void WriteEnd(EndRecord record)
     {
         EndCalls++;
         Add("sink:end");
+        if (EndFailure != null)
+            throw EndFailure;
         EndRecords.Add(record);
+        if (EndObserved != null)
+            EndObserved(record);
     }
 
     public void WriteError(ErrorRecord record)
@@ -103,8 +112,10 @@ internal sealed class FakePassiveReporter : IPassiveReporter
     internal readonly List<string> FailedCodes = new List<string>();
     internal readonly List<string> Diagnostics = new List<string>();
     internal Exception ReadyFailure { get; set; }
+    internal Exception CompleteFailure { get; set; }
     internal Exception FailedFailure { get; set; }
     internal Exception DiagnosticFailure { get; set; }
+    internal Action CompleteObserved { get; set; }
     internal int CompleteCalls;
     internal int FailedCalls;
     internal int DiagnosticCalls;
@@ -121,6 +132,10 @@ internal sealed class FakePassiveReporter : IPassiveReporter
     {
         CompleteCalls++;
         Add("report:complete");
+        if (CompleteObserved != null)
+            CompleteObserved();
+        if (CompleteFailure != null)
+            throw CompleteFailure;
     }
 
     public void Failed(string code)
@@ -363,6 +378,27 @@ internal sealed partial class DriverFixture
             capture);
     }
 
+    internal FakeUpdateObservation ObserveAtUtc(
+        object firstState,
+        object secondState,
+        double now,
+        bool quiescent,
+        CaptureRecord capture,
+        DateTime utc)
+    {
+        FakeUpdateObservation observation = NewObservation(
+            firstState,
+            firstState != null,
+            secondState,
+            secondState != null,
+            now,
+            quiescent,
+            capture);
+        observation.Utc = utc;
+        Boundary.Observe(observation);
+        return observation;
+    }
+
     internal FakeUpdateObservation Observe(
         object firstState,
         bool firstUsable,
@@ -508,6 +544,14 @@ internal sealed partial class DriverFixture
     internal void SettleCurrent(
         CaptureRecord capture,
         double firstUpdateSeconds)
+    {
+        SettleCurrentAtUtc(capture, firstUpdateSeconds, UtcFinish);
+    }
+
+    internal void SettleCurrentAtUtc(
+        CaptureRecord capture,
+        double firstUpdateSeconds,
+        DateTime finalUtc)
     {
         Neutral();
         Observe(
@@ -516,11 +560,60 @@ internal sealed partial class DriverFixture
             firstUpdateSeconds,
             true,
             capture);
-        Observe(
+        ObserveAtUtc(
             State,
             State,
             firstUpdateSeconds + 1.0,
             true,
-            capture);
+            capture,
+            finalUtc);
+    }
+
+    internal void CompleteFirstTwoSteps()
+    {
+        OpenDirection(2, true, true, 10.0);
+        SettleCurrent(ProtocolSamples.MovedCapture, 11.0);
+        OpenDirection(0, false, false, 20.0);
+        SettleCurrent(ProtocolSamples.MovedCapture, 21.0);
+    }
+
+    internal void OpenThirdStep()
+    {
+        OpenUndo(true, false, 30.0);
+    }
+
+    internal void ObserveThirdCandidate()
+    {
+        Neutral();
+        Observe(
+            State,
+            State,
+            31.0,
+            true,
+            ProtocolSamples.InitialCapture);
+    }
+
+    internal void ObserveThirdMatch(DateTime finalUtc)
+    {
+        ObserveAtUtc(
+            State,
+            State,
+            32.0,
+            true,
+            ProtocolSamples.InitialCapture,
+            finalUtc);
+    }
+
+    internal void CompleteThirdStep(DateTime finalUtc)
+    {
+        OpenThirdStep();
+        ObserveThirdCandidate();
+        ObserveThirdMatch(finalUtc);
+    }
+
+    internal void CompleteThreeSteps()
+    {
+        CompleteFirstTwoSteps();
+        CompleteThirdStep(UtcFinish);
     }
 }
diff --git a/oracle/plugin/tests/PassiveDriverTests.cs b/oracle/plugin/tests/PassiveDriverTests.cs
new file mode 100644
index 0000000000000000000000000000000000000000..6de99a4feb1440044ba0b6f7c6be99d751ee736d
--- /dev/null
+++ b/oracle/plugin/tests/PassiveDriverTests.cs
@@ -0,0 +1,10 @@
+internal static class PassiveDriverTests
+{
+    internal static void Register(TestRegistry tests)
+    {
+        PassiveDriverBoundaryTests.Register(tests);
+        PassiveDriverInitialTests.Register(tests);
+        PassiveDriverInputTests.Register(tests);
+        PassiveDriverTerminalTests.Register(tests);
+    }
+}
diff --git a/oracle/plugin/tests/Program.cs b/oracle/plugin/tests/Program.cs
index d1d808c2b052fd1ca2dfe710f7af2dbe4607be42..9dc3eb50ac4bbf54c2f3f2d9d672c7cc2a1c117f 100644
--- a/oracle/plugin/tests/Program.cs
+++ b/oracle/plugin/tests/Program.cs
@@ -13,9 +13,7 @@ private static int Main(string[] args)
         EncodingTests.Register(tests);
         CaptureSignatureTests.Register(tests);
         TraceSinkTests.Register(tests);
-        PassiveDriverBoundaryTests.Register(tests);
-        PassiveDriverInitialTests.Register(tests);
-        PassiveDriverInputTests.Register(tests);
+        PassiveDriverTests.Register(tests);
         tests.VerifyManifest(new Dictionary<string, int>(StringComparer.Ordinal)
         {
             { "protocol", 4 },
@@ -23,7 +21,8 @@ private static int Main(string[] args)
             { "sink", 6 },
             { "driver-boundary", 2 },
             { "driver-initial", 8 },
-            { "driver-input", 8 }
+            { "driver-input", 8 },
+            { "driver-terminal", 6 }
         });
         int result = tests.Run(options.Cohort);
         if (result != 0)
~~~
<!-- TASK5-PATCH-END:C53-TESTS -->

**C53-PRODUCTION patch:** SHA-256 `918cbac02ec8e01ee61e89c0b5418d6430547c33b46ea949bc9f073943dc298c`; 159 LF lines; 5310 bytes.
<!-- TASK5-PATCH-BEGIN:C53-PRODUCTION -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index bf8a6b9417d7b04126f6907441a0633e5f112f6c..a9e7320a3ce3bb43863f5864585364c2f472b0ce 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -71,6 +71,7 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private readonly ITraceSink sink;
     private readonly IPassiveReporter reporter;
+    private readonly int expectedInputCount;
     private readonly int maxSettleFrames;
     private readonly double maxSettleSeconds;
 
@@ -134,6 +135,7 @@ internal sealed partial class PassiveDriver : IDisposable
         }
         this.sink = sink;
         this.reporter = reporter;
+        this.expectedInputCount = expectedInputCount;
         this.maxSettleFrames = maxSettleFrames;
         this.maxSettleSeconds = maxSettleSeconds;
         phase = PassivePhase.Disabled;
@@ -435,7 +437,7 @@ internal sealed partial class PassiveDriver : IDisposable
         try
         {
             OracleValidation.Utc(utcNow, "utcNow");
-            CompleteUpdateCore(directive, sample);
+            CompleteUpdateCore(directive, sample, utcNow);
         }
         catch (RecordTooLargeException)
         {
@@ -611,7 +613,8 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private void CompleteUpdateCore(
         UpdateDirective directive,
-        GateSample sample)
+        GateSample sample,
+        DateTime utcNow)
     {
         if (sample == null)
             throw new ArgumentNullException("sample");
@@ -659,7 +662,8 @@ internal sealed partial class PassiveDriver : IDisposable
                 {
                     EmitSettledAttempt(
                         sample.Capture,
-                        directive.SettleFrames);
+                        directive.SettleFrames,
+                        utcNow);
                 }
                 return;
             }
@@ -800,10 +804,12 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private void ClearAttemptAfterStep()
     {
-        phase = PassivePhase.Ready;
+        if (!TerminalSelected())
+            phase = PassivePhase.Ready;
         currentFrames = 0;
         neutralSeen = false;
         candidateSignature = null;
+        lastCapture = null;
         epochState = stableState;
         ClearAttemptFields();
     }
diff --git a/oracle/plugin/Core/PassiveDriverCompletion.cs b/oracle/plugin/Core/PassiveDriverCompletion.cs
new file mode 100644
index 0000000000000000000000000000000000000000..02437c82042f5f540789afdbbfe71a5b36c7cef7
--- /dev/null
+++ b/oracle/plugin/Core/PassiveDriverCompletion.cs
@@ -0,0 +1,56 @@
+using System;
+using System.Threading;
+
+internal sealed partial class PassiveDriver
+{
+    private void FinishExpectedInputCount(DateTime finishedAtUtc)
+    {
+        OracleValidation.Utc(finishedAtUtc, "finishedAtUtc");
+        if (finishedAtUtc < startedAtUtc)
+        {
+            throw new ArgumentOutOfRangeException(
+                "finishedAtUtc",
+                "completion timestamp precedes the run start");
+        }
+        if (completedInputs != expectedInputCount)
+        {
+            throw new InvalidOperationException(
+                "completion requires the expected input count");
+        }
+        if (Interlocked.CompareExchange(
+            ref terminalOwner, 1, 0) != 0)
+        {
+            return;
+        }
+
+        try
+        {
+            sink.WriteEnd(
+                new EndRecord(
+                    runId,
+                    expectedInputCount,
+                    finishedAtUtc));
+            CloseSink();
+        }
+        catch (Exception error)
+        {
+            phase = PassivePhase.Faulted;
+            SafeDiagnostic(error);
+            BestEffortClose();
+            SafeFailed("trace_io_failed");
+            return;
+        }
+
+        phase = PassivePhase.Done;
+        try
+        {
+            reporter.Complete();
+        }
+        catch (Exception error)
+        {
+            phase = PassivePhase.Faulted;
+            SafeDiagnostic(error);
+            SafeFailed("observer_exception");
+        }
+    }
+}
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index d2c55897bf4ce17a7a1c5604e6952ab9fb07110e..5fd9120fcdbe364013a08379fc3848cbea4d35ff 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -225,7 +225,8 @@ internal sealed partial class PassiveDriver
 
     private void EmitSettledAttempt(
         CaptureRecord capture,
-        int settleFrames)
+        int settleFrames,
+        DateTime utcNow)
     {
         if (!attemptPending || !attemptOutcomeKnown)
         {
@@ -243,10 +244,17 @@ internal sealed partial class PassiveDriver
                 settleFrames,
                 false,
                 capture));
-        completedInputs++;
         stableState = attemptState;
         ClearAttemptAfterStep();
-        lastCapture = null;
+        completedInputs++;
+
+        if (TerminalSelected())
+            return;
+        if (completedInputs == expectedInputCount)
+        {
+            FinishExpectedInputCount(utcNow);
+            return;
+        }
 
         try
         {
~~~
<!-- TASK5-PATCH-END:C53-PRODUCTION -->

The C53 tests-only forced build must succeed with zero warnings/errors. The no-build `driver-terminal` run must exit `1`, emit exactly one cohort-failure line, and first fail exactly:

```text
cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: durable Step 2 must enter Done without Ready(3) and emit End Close Complete
```

The RED proves the C52 driver still returns to Ready after Step 2 and emits no End/Close/Complete.

### C53C1 patches

**C53C1-TESTS patch:** SHA-256 `a37a0ea03c285bfc8d8068bbb7179787293ce925dc8d7c42ad47a9b53ada0112`; 2468 LF lines; 95234 bytes.
<!-- TASK5-PATCH-BEGIN:C53C1-TESTS -->
~~~diff
diff --git a/oracle/plugin/tests/PassiveDriverTerminalTests.cs b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
index c88849e2f4d9406ad3ca3b1fb646c740d0fd1179..1387c3685204d73e7dee077e232f87fdcb2d6e0f 100644
--- a/oracle/plugin/tests/PassiveDriverTerminalTests.cs
+++ b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
@@ -1,5 +1,6 @@
 using System;
 using System.Collections.Generic;
+using System.Text;
 using System.Threading;
 
 internal static class PassiveDriverTerminalTests
@@ -269,6 +270,15 @@ internal static class PassiveDriverTerminalTests
             "failed Error is not claimed durable");
         AssertTraceIoTerminal(errorWrite, 0, 0,
             "Error write failure is marker-only");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            Tail(TerminalEvents(errorWrite), 3),
+            "Error write failure closes before trace I/O marker");
 
         DriverFixture ordinaryClose = DriverFixture.Ready();
         ordinaryClose.Sink.CloseFailure =
@@ -280,6 +290,15 @@ internal static class PassiveDriverTerminalTests
             "ordinary fault attempts Error once");
         AssertTraceIoTerminal(ordinaryClose, 1, 0,
             "ordinary Close failure uses trace I/O marker");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            Tail(TerminalEvents(ordinaryClose), 3),
+            "ordinary Close failure precedes trace I/O marker");
 
         DriverFixture end = DriverFixture.Ready();
         end.Sink.EndFailure = new TraceIoException("end");
@@ -387,97 +406,179 @@ internal static class PassiveDriverTerminalTests
 
     private static void FirstFaultWinsRace()
     {
+        FaultWaitsForInFlightRun();
+        FaultWaitsForInFlightInitial();
+        FaultDuringInitialReadyIsDeferred();
+        FaultWaitsForInFlightRealStep();
+        StepFailureOverridesQueuedFault();
+        FaultWinsAtIntermediateHandoff();
+        FaultWinsWhileDurableStepIsBlocked();
+        FaultDuringReadyIsDeferred();
         FaultFaultRace();
         SuccessWinsWhileEndIsBlocked();
         SuccessWinsWhileCompleteIsBlocked();
-        FaultWinsWhileDurableStepIsBlocked();
     }
 
-    private static void FaultFaultRace()
+    private static void FaultWaitsForInFlightRun()
     {
-        DriverFixture fixture = DriverFixture.Ready();
-        int winners = 0;
-        Exception firstError = null;
-        Exception secondError = null;
-        using (ManualResetEvent start = new ManualResetEvent(false))
+        DriverFixture fixture = DriverFixture.Unprepared();
+        Exception prepareError = null;
+        Exception faultError = null;
+        bool prepareResult = true;
+        bool faultResult = false;
+        bool reachedRun;
+        bool faultStarted = false;
+        bool faultJoinedBeforeRelease = false;
+        bool faultJoinedAfterRelease = false;
+        bool prepareJoined;
+        int blockedRunCalls = -1;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent runEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseRun =
+            new ManualResetEvent(false))
         {
-            Thread first = new Thread(delegate()
+            fixture.Sink.RunEntering = delegate(RunRecord record)
+            {
+                runEntered.Set();
+                releaseRun.WaitOne();
+            };
+            Thread prepare = new Thread(delegate()
             {
                 try
                 {
-                    start.WaitOne();
-                    if (fixture.Driver.TryFault("observer_exception"))
-                        Interlocked.Increment(ref winners);
+                    prepareResult =
+                        fixture.Driver.Prepare(ProtocolSamples.Run);
                 }
                 catch (Exception error)
                 {
-                    firstError = error;
+                    prepareError = error;
                 }
             });
-            Thread second = new Thread(delegate()
+            Thread fault = new Thread(delegate()
             {
                 try
                 {
-                    start.WaitOne();
-                    if (fixture.Driver.TryFault("capture_failed"))
-                        Interlocked.Increment(ref winners);
+                    faultResult =
+                        fixture.Driver.TryFault("capture_failed");
                 }
                 catch (Exception error)
                 {
-                    secondError = error;
+                    faultError = error;
                 }
             });
-            first.Start();
-            second.Start();
-            start.Set();
-            bool firstJoined = first.Join(5000);
-            bool secondJoined = second.Join(5000);
-            Check.True(firstJoined && secondJoined,
-                "fault race threads finish");
+            prepare.Start();
+            reachedRun = runEntered.WaitOne(5000);
+            try
+            {
+                if (reachedRun)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultJoinedBeforeRelease = fault.Join(5000);
+                    blockedRunCalls = fixture.Sink.RunCalls;
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseRun.Set();
+            }
+            prepareJoined = prepare.Join(5000);
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
         }
-        Check.True(firstError == null && secondError == null,
-            "fault race worker has no exception");
-        Check.Equal(1, winners, "one fault owns terminal state");
-        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
-            "fault race writes one Error");
-        string winningCode = fixture.Sink.ErrorRecords[0].Code;
-        Check.True(
-            winningCode == "observer_exception"
-                || winningCode == "capture_failed",
-            "fault race retains one of the two raced codes");
+
+        Check.True(reachedRun,
+            "Run reaches its absolute pre-durability barrier");
+        Check.True(faultJoinedBeforeRelease,
+            "fault claim returns before Run release");
+        Check.True(faultJoinedAfterRelease,
+            "Run fault thread remains joined after release");
+        Check.True(prepareJoined,
+            "Prepare finishes after Run release");
+        Check.True(prepareError == null && faultError == null,
+            "Run race workers have no exception");
+        Check.True(faultResult,
+            "fault owns terminal state during Run output");
+        Check.Equal(0, blockedRunCalls,
+            "Run barrier is the first sink operation");
+        Check.Equal(0, blockedErrors,
+            "preparation fault never attempts Error");
+        Check.Equal(0, blockedCloses,
+            "fault Close waits for active Run output");
+        Check.Equal(0, blockedFailures,
+            "fault marker waits for active Run output");
+        Check.False(prepareResult,
+            "faulted Run is not published as prepared");
+        Check.Equal(1, fixture.Sink.RunCalls,
+            "entered Run completes exactly once");
+        Check.Equal(1, fixture.Sink.RunRecords.Count,
+            "entered Run becomes durable after release");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "preparation fault remains marker-only");
         Check.Equal(1, fixture.Sink.CloseCalls,
-            "fault race closes once");
-        Check.Equal(1, fixture.Reporter.FailedCalls,
-            "fault race reports one failure marker");
-        Check.Equal(winningCode, fixture.Reporter.FailedCodes[0],
-            "fault race Error and Failed preserve the same winner");
+            "faulted preparation closes once");
+        Check.Sequence(
+            new string[] { "trace_io_failed" },
+            fixture.Reporter.FailedCodes,
+            "preparation fault uses trace I/O marker");
+        Check.False(fixture.Driver.Activate(),
+            "faulted preparation cannot activate");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:run",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            TerminalEvents(fixture),
+            "Run completes before deferred Close and marker");
     }
 
-    private static void SuccessWinsWhileEndIsBlocked()
+    private static void FaultWaitsForInFlightInitial()
     {
-        DriverFixture fixture = DriverFixture.Ready();
-        fixture.CompleteFirstTwoSteps();
-        fixture.OpenThirdStep();
-        fixture.ObserveThirdCandidate();
+        DriverFixture fixture = DriverFixture.Active();
+        CaptureRecord capture =
+            ProtocolSamples.Capture("initial-race-pair");
+        PrimeInitialCandidate(fixture, capture);
 
         Exception completionError = null;
         Exception faultError = null;
-        bool faultResult = true;
-        bool faultFinishedBeforeRelease = false;
-        using (ManualResetEvent endEntered = new ManualResetEvent(false))
-        using (ManualResetEvent releaseEnd = new ManualResetEvent(false))
-        using (ManualResetEvent faultFinished = new ManualResetEvent(false))
+        bool faultResult = false;
+        bool reachedInitial;
+        bool faultStarted = false;
+        bool faultJoinedBeforeRelease = false;
+        bool faultJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedInitialCalls = -1;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent initialEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseInitial =
+            new ManualResetEvent(false))
         {
-            fixture.Sink.EndObserved = delegate(EndRecord record)
+            fixture.Sink.InitialEntering = delegate(InitialRecord record)
             {
-                endEntered.Set();
-                releaseEnd.WaitOne();
+                initialEntered.Set();
+                releaseInitial.WaitOne();
             };
             Thread completion = new Thread(delegate()
             {
                 try
                 {
-                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        3.0,
+                        true,
+                        capture);
                 }
                 catch (Exception error)
                 {
@@ -489,87 +590,128 @@ internal static class PassiveDriverTerminalTests
                 try
                 {
                     faultResult =
-                        fixture.Driver.TryFault("observer_exception");
+                        fixture.Driver.TryFault("capture_failed");
                 }
                 catch (Exception error)
                 {
                     faultError = error;
                 }
-                finally
-                {
-                    faultFinished.Set();
-                }
             });
             completion.Start();
-            bool reachedEnd = endEntered.WaitOne(5000);
-            bool completionJoined;
-            bool faultJoined;
+            reachedInitial = initialEntered.WaitOne(5000);
             try
             {
-                if (reachedEnd)
+                if (reachedInitial)
                 {
                     fault.Start();
-                    faultFinishedBeforeRelease =
-                        faultFinished.WaitOne(1000);
+                    faultStarted = true;
+                    faultJoinedBeforeRelease = fault.Join(5000);
+                    blockedInitialCalls = fixture.Sink.InitialCalls;
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
                 }
             }
             finally
             {
-                releaseEnd.Set();
+                releaseInitial.Set();
             }
             completionJoined = completion.Join(5000);
-            faultJoined = !reachedEnd || fault.Join(5000);
-
-            Check.True(reachedEnd, "success race reaches durable End");
-            Check.True(faultFinishedBeforeRelease,
-                "TryFault returns while WriteEnd is blocked without a driver monitor");
-            Check.True(completionJoined && faultJoined,
-                "success race threads finish");
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
         }
+
+        Check.True(reachedInitial,
+            "Initial reaches its absolute pre-durability barrier");
+        Check.True(faultJoinedBeforeRelease,
+            "fault claim returns before Initial release");
+        Check.True(faultJoinedAfterRelease,
+            "Initial fault thread remains joined after release");
+        Check.True(completionJoined,
+            "initial completion finishes after release");
         Check.True(completionError == null && faultError == null,
-            "success race worker has no exception");
-        Check.False(faultResult,
-            "success terminal owner rejects concurrent fault");
-        Check.Equal(PassivePhase.Done, fixture.Driver.Phase,
-            "success race remains Done");
-        Check.Equal(1, fixture.Sink.EndRecords.Count,
-            "success race writes one End");
-        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
-            "success race writes no Error");
-        Check.Equal(1, fixture.Sink.CloseCalls,
-            "success race closes once");
-        Check.Equal(1, fixture.Reporter.CompleteCalls,
-            "success race completes once");
+            "Initial race workers have no exception");
+        Check.True(faultResult,
+            "fault owns terminal state during Initial output");
+        Check.Equal(0, blockedInitialCalls,
+            "Initial barrier is the first sink operation");
+        Check.Equal(0, blockedErrors,
+            "Initial Error waits for active output");
+        Check.Equal(0, blockedCloses,
+            "Initial Close waits for active output");
+        Check.Equal(0, blockedFailures,
+            "Initial marker waits for active output");
+        Check.Equal(1, fixture.Sink.InitialCalls,
+            "entered Initial completes exactly once");
+        Check.Equal(1, fixture.Sink.InitialRecords.Count,
+            "entered Initial becomes durable after release");
+        Check.Same(capture, fixture.Sink.InitialRecords[0].Capture,
+            "durable Initial preserves the paired capture");
+        Check.Sequence(new int[0], fixture.Reporter.ReadyValues,
+            "fault during Initial suppresses Ready(0)");
+        AssertError(
+            fixture.Sink.ErrorRecords[0],
+            "capture_failed",
+            null,
+            null,
+            3,
+            "Initial fault preserves active settle fields");
+        Check.Same(capture,
+            fixture.Sink.ErrorRecords[0].LastCapture,
+            "Initial fault preserves the latest capture");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:initial",
+                "sink:error:capture_failed",
+                "sink:close",
+                "report:failed:capture_failed"
+            },
+            Tail(TerminalEvents(fixture), 4),
+            "Initial completes before deferred Error Close Failed");
     }
 
-    private static void FaultWinsWhileDurableStepIsBlocked()
+    private static void FaultDuringInitialReadyIsDeferred()
     {
-        DriverFixture fixture = DriverFixture.Ready();
-        fixture.CompleteFirstTwoSteps();
-        fixture.OpenThirdStep();
-        fixture.ObserveThirdCandidate();
+        DriverFixture fixture = DriverFixture.Active();
+        CaptureRecord capture =
+            ProtocolSamples.Capture("initial-ready-race-pair");
+        PrimeInitialCandidate(fixture, capture);
 
         Exception completionError = null;
         Exception faultError = null;
         bool faultResult = false;
-        bool faultFinishedBeforeRelease = false;
-        using (ManualResetEvent stepEntered = new ManualResetEvent(false))
-        using (ManualResetEvent releaseStep = new ManualResetEvent(false))
-        using (ManualResetEvent faultFinished = new ManualResetEvent(false))
+        bool reachedReady;
+        bool faultStarted = false;
+        bool faultJoinedBeforeRelease = false;
+        bool faultJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent readyEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseReady =
+            new ManualResetEvent(false))
         {
-            fixture.Sink.StepObserved = delegate(StepRecord record)
+            fixture.Reporter.ReadyObserved = delegate(int completedInputs)
             {
-                if (record.InputIndex == 2)
+                if (completedInputs == 0)
                 {
-                    stepEntered.Set();
-                    releaseStep.WaitOne();
+                    readyEntered.Set();
+                    releaseReady.WaitOne();
                 }
             };
             Thread completion = new Thread(delegate()
             {
                 try
                 {
-                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        3.0,
+                        true,
+                        capture);
                 }
                 catch (Exception error)
                 {
@@ -580,91 +722,147 @@ internal static class PassiveDriverTerminalTests
             {
                 try
                 {
-                    faultResult = fixture.Driver.TryFault("capture_failed");
+                    faultResult =
+                        fixture.Driver.TryFault("observer_exception");
                 }
                 catch (Exception error)
                 {
                     faultError = error;
                 }
-                finally
-                {
-                    faultFinished.Set();
-                }
             });
             completion.Start();
-            bool reachedStep = stepEntered.WaitOne(5000);
-            bool completionJoined;
-            bool faultJoined;
+            reachedReady = readyEntered.WaitOne(5000);
             try
             {
-                if (reachedStep)
+                if (reachedReady)
                 {
                     fault.Start();
-                    faultFinishedBeforeRelease =
-                        faultFinished.WaitOne(1000);
+                    faultStarted = true;
+                    faultJoinedBeforeRelease = fault.Join(5000);
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
                 }
             }
             finally
             {
-                releaseStep.Set();
+                releaseReady.Set();
             }
             completionJoined = completion.Join(5000);
-            faultJoined = !reachedStep || fault.Join(5000);
-
-            Check.True(reachedStep, "fault race reaches durable Step 2");
-            Check.True(faultFinishedBeforeRelease,
-                "TryFault returns while WriteStep is blocked without a driver monitor");
-            Check.True(completionJoined && faultJoined,
-                "fault-first race threads finish");
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
         }
+
+        Check.True(reachedReady,
+            "initial completion reaches blocked Ready(0)");
+        Check.True(faultJoinedBeforeRelease,
+            "fault returns before Ready(0) release");
+        Check.True(faultJoinedAfterRelease,
+            "Ready(0) fault thread remains joined after release");
+        Check.True(completionJoined,
+            "Ready(0) completion thread finishes after release");
         Check.True(completionError == null && faultError == null,
-            "fault-first race worker has no exception");
+            "Ready(0) race workers have no exception");
         Check.True(faultResult,
-            "fault claims shared owner before success");
-        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
-            "fault-first race remains Faulted after Step returns");
-        Check.Equal(3, fixture.Sink.StepRecords.Count,
-            "fault-first race retains durable Step 2");
-        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
-            "fault-first race writes one Error");
-        Check.Equal(0, fixture.Sink.EndRecords.Count,
-            "fault-first race suppresses End");
-        Check.Equal(1, fixture.Sink.CloseCalls,
-            "fault-first race closes once");
-        Check.Equal(0, fixture.Reporter.CompleteCalls,
-            "fault-first race suppresses Complete");
-        Check.Equal(1, fixture.Reporter.FailedCalls,
-            "fault-first race reports one failure marker");
+            "fault owns terminal state during Ready(0)");
+        Check.Equal(0, blockedErrors,
+            "Error waits for Ready(0) callback");
+        Check.Equal(0, blockedCloses,
+            "Close waits for Ready(0) callback");
+        Check.Equal(0, blockedFailures,
+            "Failed waits for Ready(0) callback");
+        Check.Sequence(new int[] { 0 },
+            fixture.Reporter.ReadyValues,
+            "leased Ready(0) completes before its fault");
+        AssertError(
+            fixture.Sink.ErrorRecords[0],
+            "observer_exception",
+            null,
+            null,
+            0,
+            "Ready(0) fault observes published initial state");
+        Check.True(fixture.Sink.ErrorRecords[0].LastCapture == null,
+            "Ready(0) fault observes cleared capture");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:initial",
+                "report:ready:0/3",
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:observer_exception"
+            },
+            Tail(TerminalEvents(fixture), 5),
+            "Ready(0) drains Error Close Failed after release");
     }
 
-    private static void SuccessWinsWhileCompleteIsBlocked()
+    private static void PrimeInitialCandidate(
+        DriverFixture fixture,
+        CaptureRecord capture)
+    {
+        fixture.Observe(
+            fixture.State,
+            fixture.State,
+            1.0,
+            true,
+            ProtocolSamples.Capture("initial-race-start"));
+        fixture.Neutral();
+        fixture.Observe(
+            fixture.State,
+            fixture.State,
+            2.0,
+            true,
+            capture);
+    }
+
+    private static void StepFailureOverridesQueuedFault()
     {
         DriverFixture fixture = DriverFixture.Ready();
-        fixture.CompleteFirstTwoSteps();
-        fixture.OpenThirdStep();
-        fixture.ObserveThirdCandidate();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.Neutral();
+        fixture.Observe(
+            fixture.State,
+            fixture.State,
+            11.0,
+            true,
+            ProtocolSamples.MovedCapture);
+        fixture.Sink.StepFailure =
+            new TraceIoException("in-flight Step");
 
         Exception completionError = null;
         Exception faultError = null;
-        bool faultResult = true;
-        bool faultFinishedBeforeRelease = false;
-        using (ManualResetEvent completeEntered =
-            new ManualResetEvent(false))
-        using (ManualResetEvent releaseComplete =
+        bool faultResult = false;
+        bool reachedStep;
+        bool faultStarted = false;
+        bool faultJoined = false;
+        bool faultJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent stepEntered =
             new ManualResetEvent(false))
-        using (ManualResetEvent faultFinished =
+        using (ManualResetEvent releaseStep =
             new ManualResetEvent(false))
         {
-            fixture.Reporter.CompleteObserved = delegate()
+            fixture.Sink.StepEntering = delegate(StepRecord record)
             {
-                completeEntered.Set();
-                releaseComplete.WaitOne();
+                if (record.InputIndex == 0)
+                {
+                    stepEntered.Set();
+                    releaseStep.WaitOne();
+                }
             };
             Thread completion = new Thread(delegate()
             {
                 try
                 {
-                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        12.0,
+                        true,
+                        ProtocolSamples.MovedCapture);
                 }
                 catch (Exception error)
                 {
@@ -682,107 +880,1463 @@ internal static class PassiveDriverTerminalTests
                 {
                     faultError = error;
                 }
-                finally
-                {
-                    faultFinished.Set();
-                }
             });
             completion.Start();
-            bool reachedComplete = completeEntered.WaitOne(5000);
-            bool completionJoined;
-            bool faultJoined;
+            reachedStep = stepEntered.WaitOne(5000);
             try
             {
-                if (reachedComplete)
+                if (reachedStep)
                 {
                     fault.Start();
-                    faultFinishedBeforeRelease =
-                        faultFinished.WaitOne(1000);
+                    faultStarted = true;
+                    faultJoined = fault.Join(5000);
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
                 }
             }
             finally
             {
-                releaseComplete.Set();
+                releaseStep.Set();
             }
             completionJoined = completion.Join(5000);
-            faultJoined = !reachedComplete || fault.Join(5000);
-
-            Check.True(reachedComplete,
-                "completion race reaches reporter Complete");
-            Check.True(faultFinishedBeforeRelease,
-                "TryFault returns while Complete is blocked without a driver monitor");
-            Check.True(completionJoined && faultJoined,
-                "completion callback race threads finish");
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
         }
+
+        Check.True(reachedStep,
+            "failing Step reaches its pre-durability barrier");
+        Check.True(faultJoined,
+            "queued fault claim returns before failing Step release");
+        Check.True(faultJoinedAfterRelease,
+            "queued fault thread remains joined after Step release");
+        Check.True(completionJoined,
+            "failing Step completion thread finishes");
         Check.True(completionError == null && faultError == null,
-            "completion callback race worker has no exception");
-        Check.False(faultResult,
+            "failing Step race workers have no exception");
+        Check.True(faultResult,
+            "ordinary fault first claims during failing Step");
+        Check.Equal(0, blockedErrors,
+            "queued Error waits for failing Step");
+        Check.Equal(0, blockedCloses,
+            "queued Close waits for failing Step");
+        Check.Equal(0, blockedFailures,
+            "queued Failed waits for failing Step");
+        Check.Equal(1, fixture.Sink.StepCalls,
+            "failing Step is attempted once");
+        Check.Equal(0, fixture.Sink.StepRecords.Count,
+            "failing Step is not durable");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "compromised Step suppresses queued Error attempt");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "compromised Step closes once");
+        Check.Sequence(
+            new string[] { "trace_io_failed" },
+            fixture.Reporter.FailedCodes,
+            "Step trace failure overrides queued ordinary marker");
+        Check.Sequence(new int[] { 0 }, fixture.Reporter.ReadyValues,
+            "failing Step emits no Ready continuation");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:0",
+                "sink:close",
+                "report:failed:trace_io_failed"
+            },
+            Tail(TerminalEvents(fixture), 3),
+            "failing Step drains Close then trace I/O marker only");
+    }
+
+    private static void FaultDuringReadyIsDeferred()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.Neutral();
+        fixture.Observe(
+            fixture.State,
+            fixture.State,
+            11.0,
+            true,
+            ProtocolSamples.MovedCapture);
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = false;
+        bool reachedReady;
+        bool faultStarted = false;
+        bool faultJoinedBeforeRelease = false;
+        bool faultJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent readyEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseReady =
+            new ManualResetEvent(false))
+        {
+            fixture.Reporter.ReadyObserved = delegate(int completedInputs)
+            {
+                if (completedInputs == 1)
+                {
+                    readyEntered.Set();
+                    releaseReady.WaitOne();
+                }
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        12.0,
+                        true,
+                        ProtocolSamples.MovedCapture);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("observer_exception");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+            completion.Start();
+            reachedReady = readyEntered.WaitOne(5000);
+            try
+            {
+                if (reachedReady)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultJoinedBeforeRelease = fault.Join(5000);
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseReady.Set();
+            }
+            completionJoined = completion.Join(5000);
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
+        }
+
+        Check.True(reachedReady,
+            "completion reaches blocked Ready(1)");
+        Check.True(faultJoinedBeforeRelease,
+            "separate fault thread returns before Ready(1) release");
+        Check.True(faultJoinedAfterRelease,
+            "Ready(1) fault thread remains joined after release");
+        Check.True(completionJoined,
+            "Ready(1) completion thread finishes after release");
+        Check.True(completionError == null && faultError == null,
+            "Ready(1) race workers have no exception");
+        Check.True(faultResult,
+            "separate Ready fault claims terminal owner");
+        Check.Equal(0, blockedErrors,
+            "separate Error waits for Ready lease");
+        Check.Equal(0, blockedCloses,
+            "separate Close waits for Ready lease");
+        Check.Equal(0, blockedFailures,
+            "separate Failed waits for Ready lease");
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            "separate Ready fault remains Faulted");
+        Check.Sequence(new int[] { 0, 1 },
+            fixture.Reporter.ReadyValues,
+            "leased Ready completes before its separate fault");
+        AssertError(
+            fixture.Sink.ErrorRecords[0],
+            "observer_exception",
+            null,
+            null,
+            0,
+            "separate Ready fault observes cleared attempt");
+        Check.True(fixture.Sink.ErrorRecords[0].LastCapture == null,
+            "separate Ready fault observes cleared capture");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:0",
+                "report:ready:1/3",
+                "sink:error:observer_exception",
+                "sink:close",
+                "report:failed:observer_exception"
+            },
+            Tail(TerminalEvents(fixture), 5),
+            "Ready lease drains separate Error Close Failed afterward");
+    }
+
+    private static void FaultWinsAtIntermediateHandoff()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.Neutral();
+        fixture.Observe(
+            fixture.State,
+            fixture.State,
+            11.0,
+            true,
+            ProtocolSamples.MovedCapture);
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = false;
+        bool reachedStep;
+        bool faultStarted = false;
+        bool faultJoined = false;
+        bool faultJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent stepEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseStep =
+            new ManualResetEvent(false))
+        {
+            fixture.Sink.StepObserved = delegate(StepRecord record)
+            {
+                if (record.InputIndex == 0)
+                {
+                    stepEntered.Set();
+                    releaseStep.WaitOne();
+                }
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        12.0,
+                        true,
+                        ProtocolSamples.MovedCapture);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+            completion.Start();
+            reachedStep = stepEntered.WaitOne(5000);
+            try
+            {
+                if (reachedStep)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultJoined = fault.Join(5000);
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseStep.Set();
+            }
+            completionJoined = completion.Join(5000);
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
+        }
+
+        Check.True(reachedStep,
+            "intermediate Step reaches post-durability handoff");
+        Check.True(faultJoined,
+            "intermediate fault claim returns before Step release");
+        Check.True(faultJoinedAfterRelease,
+            "intermediate fault thread remains joined after release");
+        Check.True(completionJoined,
+            "intermediate handoff completion thread finishes");
+        Check.True(completionError == null && faultError == null,
+            "intermediate handoff workers have no exception");
+        Check.True(faultResult,
+            "intermediate handoff fault claims terminal owner");
+        Check.Equal(0, blockedErrors,
+            "intermediate Error waits for Step handoff");
+        Check.Equal(0, blockedCloses,
+            "intermediate Close waits for Step handoff");
+        Check.Equal(0, blockedFailures,
+            "intermediate Failed waits for Step handoff");
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            "intermediate handoff remains Faulted");
+        Check.Equal(1, fixture.Sink.StepRecords.Count,
+            "intermediate Step remains durable");
+        Check.Sequence(new int[] { 0 }, fixture.Reporter.ReadyValues,
+            "intermediate fault suppresses Ready(1)");
+        AssertError(
+            fixture.Sink.ErrorRecords[0],
+            "capture_failed",
+            0,
+            OracleInput.West,
+            2,
+            "intermediate handoff preserves pending Error fields");
+        Check.Same(
+            ProtocolSamples.MovedCapture,
+            fixture.Sink.ErrorRecords[0].LastCapture,
+            "intermediate handoff preserves last capture");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:0",
+                "sink:error:capture_failed",
+                "sink:close",
+                "report:failed:capture_failed"
+            },
+            Tail(TerminalEvents(fixture), 4),
+            "intermediate handoff order is Step Error Close Failed");
+    }
+
+    private static void FaultWaitsForInFlightRealStep()
+    {
+        using (ManualResetEvent writeEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseWrite =
+            new ManualResetEvent(false))
+        {
+            BlockingTraceOutput output = new BlockingTraceOutput();
+            NdjsonTraceSink sink = new NdjsonTraceSink(output);
+            DriverFixture fixture = DriverFixture.ReadyWithSink(sink);
+            fixture.CompleteFirstTwoSteps();
+            fixture.OpenThirdStep();
+            fixture.ObserveThirdCandidate();
+            int baselineBytes = output.ByteCount;
+            int baselineFlushes = output.FlushCalls;
+            output.BlockNextWrite(writeEntered, releaseWrite);
+
+            Exception completionError = null;
+            Exception faultError = null;
+            bool faultResult = false;
+            bool faultStarted = false;
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+
+            completion.Start();
+            bool reachedWrite = writeEntered.WaitOne(5000);
+            bool faultJoined = false;
+            int blockedBytes = -1;
+            int blockedFlushes = -1;
+            int blockedCloses = -1;
+            int blockedFailures = -1;
+            bool completionJoined;
+            bool faultJoinedAfterRelease = false;
+            try
+            {
+                if (reachedWrite)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultJoined = fault.Join(5000);
+                    blockedBytes = output.ByteCount;
+                    blockedFlushes = output.FlushCalls;
+                    blockedCloses = output.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseWrite.Set();
+            }
+            completionJoined = completion.Join(5000);
+            if (faultStarted)
+                faultJoinedAfterRelease = fault.Join(5000);
+
+            Check.True(reachedWrite,
+                "real Step reaches its pre-durability output barrier");
+            Check.True(faultJoined,
+                "fault claim returns while real Step output is blocked");
+            Check.True(faultJoinedAfterRelease,
+                "real Step fault thread remains joined after release");
+            Check.True(completionJoined,
+                "real Step completion finishes after release");
+            Check.True(completionError == null && faultError == null,
+                "real Step race workers have no exception");
+            Check.True(faultResult,
+                "fault atomically claims during real Step output");
+            Check.Equal(baselineBytes, blockedBytes,
+                "fault terminal trace waits for active Step output");
+            Check.Equal(baselineFlushes, blockedFlushes,
+                "fault flush waits for active Step output");
+            Check.Equal(0, blockedCloses,
+                "fault Close waits for active Step output");
+            Check.Equal(0, blockedFailures,
+                "fault marker waits for active Step output");
+            Check.Equal(1, output.CloseCalls,
+                "real trace closes once after deferred fault");
+            Check.Sequence(
+                new string[] { "capture_failed" },
+                fixture.Reporter.FailedCodes,
+                "deferred fault retains its winning marker");
+            AssertLastRealTraceLines(
+                output.SnapshotBytes(),
+                CanonicalJson.EncodeStep(ProtocolSamples.Step2),
+                CanonicalJson.EncodeError(new ErrorRecord(
+                    ProtocolSamples.RunId,
+                    2,
+                    OracleInput.Undo,
+                    "capture_failed",
+                    2,
+                    ProtocolSamples.InitialCapture)),
+                "real Step remains durable before deferred Error");
+        }
+    }
+
+    private static void FaultFaultRace()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        int winners = 0;
+        Exception firstError = null;
+        Exception secondError = null;
+        using (ManualResetEvent start = new ManualResetEvent(false))
+        {
+            Thread first = new Thread(delegate()
+            {
+                try
+                {
+                    start.WaitOne();
+                    if (fixture.Driver.TryFault("observer_exception"))
+                        Interlocked.Increment(ref winners);
+                }
+                catch (Exception error)
+                {
+                    firstError = error;
+                }
+            });
+            Thread second = new Thread(delegate()
+            {
+                try
+                {
+                    start.WaitOne();
+                    if (fixture.Driver.TryFault("capture_failed"))
+                        Interlocked.Increment(ref winners);
+                }
+                catch (Exception error)
+                {
+                    secondError = error;
+                }
+            });
+            first.Start();
+            second.Start();
+            start.Set();
+            bool firstJoined = first.Join(5000);
+            bool secondJoined = second.Join(5000);
+            Check.True(firstJoined && secondJoined,
+                "fault race threads finish");
+        }
+        Check.True(firstError == null && secondError == null,
+            "fault race worker has no exception");
+        Check.Equal(1, winners, "one fault owns terminal state");
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            "fault race writes one Error");
+        string winningCode = fixture.Sink.ErrorRecords[0].Code;
+        Check.True(
+            winningCode == "observer_exception"
+                || winningCode == "capture_failed",
+            "fault race retains one of the two raced codes");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "fault race closes once");
+        Check.Equal(1, fixture.Reporter.FailedCalls,
+            "fault race reports one failure marker");
+        Check.Equal(winningCode, fixture.Reporter.FailedCodes[0],
+            "fault race Error and Failed preserve the same winner");
+    }
+
+    private static void SuccessWinsWhileEndIsBlocked()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = true;
+        bool faultStarted = false;
+        bool faultFinishedBeforeRelease = false;
+        using (ManualResetEvent endEntered = new ManualResetEvent(false))
+        using (ManualResetEvent releaseEnd = new ManualResetEvent(false))
+        {
+            fixture.Sink.EndObserved = delegate(EndRecord record)
+            {
+                endEntered.Set();
+                releaseEnd.WaitOne();
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("observer_exception");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+            completion.Start();
+            bool reachedEnd = endEntered.WaitOne(5000);
+            bool completionJoined;
+            bool faultJoined;
+            try
+            {
+                if (reachedEnd)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultFinishedBeforeRelease =
+                        fault.Join(5000);
+                }
+            }
+            finally
+            {
+                releaseEnd.Set();
+            }
+            completionJoined = completion.Join(5000);
+            faultJoined = true;
+            if (faultStarted)
+                faultJoined = fault.Join(5000);
+
+            Check.True(reachedEnd, "success race reaches durable End");
+            Check.True(faultFinishedBeforeRelease,
+                "TryFault returns while WriteEnd is blocked without a driver monitor");
+            Check.True(completionJoined && faultJoined,
+                "success race threads finish");
+        }
+        Check.True(completionError == null && faultError == null,
+            "success race worker has no exception");
+        Check.False(faultResult,
+            "success terminal owner rejects concurrent fault");
+        Check.Equal(PassivePhase.Done, fixture.Driver.Phase,
+            "success race remains Done");
+        Check.Equal(1, fixture.Sink.EndRecords.Count,
+            "success race writes one End");
+        Check.Equal(0, fixture.Sink.ErrorRecords.Count,
+            "success race writes no Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "success race closes once");
+        Check.Equal(1, fixture.Reporter.CompleteCalls,
+            "success race completes once");
+    }
+
+    private static void FaultWinsWhileDurableStepIsBlocked()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = false;
+        bool faultStarted = false;
+        bool faultFinishedBeforeRelease = false;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent stepEntered = new ManualResetEvent(false))
+        using (ManualResetEvent releaseStep = new ManualResetEvent(false))
+        {
+            fixture.Sink.StepObserved = delegate(StepRecord record)
+            {
+                if (record.InputIndex == 2)
+                {
+                    stepEntered.Set();
+                    releaseStep.WaitOne();
+                }
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult = fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+            completion.Start();
+            bool reachedStep = stepEntered.WaitOne(5000);
+            bool completionJoined;
+            bool faultJoined;
+            try
+            {
+                if (reachedStep)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultFinishedBeforeRelease =
+                        fault.Join(5000);
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseStep.Set();
+            }
+            completionJoined = completion.Join(5000);
+            faultJoined = true;
+            if (faultStarted)
+                faultJoined = fault.Join(5000);
+
+            Check.True(reachedStep, "fault race reaches durable Step 2");
+            Check.True(faultFinishedBeforeRelease,
+                "TryFault returns while WriteStep is blocked without a driver monitor");
+            Check.True(completionJoined && faultJoined,
+                "fault-first race threads finish");
+        }
+        Check.True(completionError == null && faultError == null,
+            "fault-first race worker has no exception");
+        Check.True(faultResult,
+            "fault claims shared owner before success");
+        Check.Equal(0, blockedErrors,
+            "terminal Error waits for Step handoff");
+        Check.Equal(0, blockedCloses,
+            "terminal Close waits for Step handoff");
+        Check.Equal(0, blockedFailures,
+            "terminal Failed waits for Step handoff");
+        Check.Equal(PassivePhase.Faulted, fixture.Driver.Phase,
+            "fault-first race remains Faulted after Step returns");
+        Check.Equal(3, fixture.Sink.StepRecords.Count,
+            "fault-first race retains durable Step 2");
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            "fault-first race writes one Error");
+        Check.Equal(0, fixture.Sink.EndRecords.Count,
+            "fault-first race suppresses End");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "fault-first race closes once");
+        Check.Equal(0, fixture.Reporter.CompleteCalls,
+            "fault-first race suppresses Complete");
+        Check.Equal(1, fixture.Reporter.FailedCalls,
+            "fault-first race reports one failure marker");
+        Check.Sequence(new int[] { 0, 1, 2 },
+            fixture.Reporter.ReadyValues,
+            "terminal fault suppresses Ready(3)");
+        AssertError(
+            fixture.Sink.ErrorRecords[0],
+            "capture_failed",
+            2,
+            OracleInput.Undo,
+            2,
+            "terminal handoff preserves pending Error fields");
+        Check.Same(
+            ProtocolSamples.InitialCapture,
+            fixture.Sink.ErrorRecords[0].LastCapture,
+            "terminal handoff preserves last capture");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:error:capture_failed",
+                "sink:close",
+                "report:failed:capture_failed"
+            },
+            Tail(TerminalEvents(fixture), 4),
+            "terminal handoff order is Step Error Close Failed");
+    }
+
+    private static void SuccessWinsWhileCompleteIsBlocked()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception faultError = null;
+        bool faultResult = true;
+        bool faultStarted = false;
+        bool faultFinishedBeforeRelease = false;
+        using (ManualResetEvent completeEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseComplete =
+            new ManualResetEvent(false))
+        {
+            fixture.Reporter.CompleteObserved = delegate()
+            {
+                completeEntered.Set();
+                releaseComplete.WaitOne();
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+            completion.Start();
+            bool reachedComplete = completeEntered.WaitOne(5000);
+            bool completionJoined;
+            bool faultJoined;
+            try
+            {
+                if (reachedComplete)
+                {
+                    fault.Start();
+                    faultStarted = true;
+                    faultFinishedBeforeRelease =
+                        fault.Join(5000);
+                }
+            }
+            finally
+            {
+                releaseComplete.Set();
+            }
+            completionJoined = completion.Join(5000);
+            faultJoined = true;
+            if (faultStarted)
+                faultJoined = fault.Join(5000);
+
+            Check.True(reachedComplete,
+                "completion race reaches reporter Complete");
+            Check.True(faultFinishedBeforeRelease,
+                "TryFault returns while Complete is blocked without a driver monitor");
+            Check.True(completionJoined && faultJoined,
+                "completion callback race threads finish");
+        }
+        Check.True(completionError == null && faultError == null,
+            "completion callback race worker has no exception");
+        Check.False(faultResult,
             "success owner rejects fault during Complete callback");
         Check.Equal(PassivePhase.Done, fixture.Driver.Phase,
-            "completion callback race remains Done");
-        Check.Equal(1, fixture.Sink.EndCalls,
-            "completion callback race attempts End once");
+            "completion callback race remains Done");
+        Check.Equal(1, fixture.Sink.EndCalls,
+            "completion callback race attempts End once");
+        Check.Equal(1, fixture.Sink.EndRecords.Count,
+            "completion callback race retains one End");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "completion callback race never attempts Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "completion callback race closes once");
+        Check.Equal(1, fixture.Reporter.CompleteCalls,
+            "completion callback race attempts Complete once");
+        Check.Equal(0, fixture.Reporter.FailedCalls,
+            "completion callback race emits no failure marker");
+    }
+
+    private static void DisposeAndLateCallbacksAreFinal()
+    {
+        DisposeWaitsForInFlightRun();
+        DisposeWaitsForInFlightInitial();
+        DisposeWaitsForInFlightStep();
+        DisposeDuringErrorLeavesFaultOwner();
+        DisposeDuringEndLeavesSuccessOwner();
+
+        DriverFixture disposed = DriverFixture.Active();
+        HookToken openPoll = disposed.Driver.PlayerPollEntered();
+        disposed.Driver.Dispose();
+        disposed.Driver.Dispose();
+        disposed.Driver.ClearThrew(openPoll);
+        disposed.Driver.ClearThrew(openPoll);
+        Check.Equal(1, disposed.Sink.CloseCalls,
+            "Dispose closes at most once");
+        Check.Equal(0, disposed.Sink.EndRecords.Count,
+            "Dispose writes no End");
+        Check.Equal(0, disposed.Sink.ErrorRecords.Count,
+            "Dispose writes no Error");
+        Check.Equal(0, disposed.Reporter.FailedCalls,
+            "Dispose emits no terminal marker");
+        Check.False(disposed.Driver.TryFault("observer_exception"),
+            "disposed late fault is inert");
+        FakeUpdateObservation late =
+            new FakeUpdateObservation(disposed.Events)
+            {
+                FirstState = disposed.State,
+                SecondState = disposed.State,
+                Now = 5.0
+            };
+        disposed.Boundary.Observe(late);
+        Check.Equal(0, late.StateCalls,
+            "disposed late update does not inspect observation");
+
+        DriverFixture done = DriverFixture.Ready();
+        HookToken openStateSet =
+            done.Driver.StateSetEntered(done.State, done.State);
+        done.CompleteThreeSteps();
+        int doneEvents = done.Events.Count;
+        done.Driver.StateSetReturned(
+            openStateSet, done.State, 40.0);
+        done.Driver.StateSetReturned(
+            openStateSet, done.State, 40.0);
+        done.Driver.ClearThrew(openStateSet);
+        done.Driver.RestartEntered();
+        done.Driver.TryFault("observer_exception");
+        done.Driver.Dispose();
+        done.Driver.Dispose();
+        Check.Equal(doneEvents, done.Events.Count,
+            "Done matching cleanup and later callbacks are output-inert");
+        Check.Equal(PassivePhase.Done, done.Driver.Phase,
+            "Done remains final");
+        Check.Equal(1, done.Sink.CloseCalls,
+            "Done Dispose cannot Close twice");
+    }
+
+    private static void DisposeDuringErrorLeavesFaultOwner()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        Exception faultError = null;
+        Exception disposeError = null;
+        bool faultResult = false;
+        bool reachedError;
+        bool disposeStarted = false;
+        bool disposeJoinedBeforeRelease = false;
+        bool disposeJoinedAfterRelease = false;
+        bool faultJoined;
+        int blockedErrorCalls = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent errorEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseError =
+            new ManualResetEvent(false))
+        {
+            fixture.Sink.ErrorEntering = delegate(ErrorRecord record)
+            {
+                errorEntered.Set();
+                releaseError.WaitOne();
+            };
+            Thread fault = new Thread(delegate()
+            {
+                try
+                {
+                    faultResult =
+                        fixture.Driver.TryFault("capture_failed");
+                }
+                catch (Exception error)
+                {
+                    faultError = error;
+                }
+            });
+            Thread dispose = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Driver.Dispose();
+                }
+                catch (Exception error)
+                {
+                    disposeError = error;
+                }
+            });
+            fault.Start();
+            reachedError = errorEntered.WaitOne(5000);
+            try
+            {
+                if (reachedError)
+                {
+                    dispose.Start();
+                    disposeStarted = true;
+                    disposeJoinedBeforeRelease = dispose.Join(5000);
+                    blockedErrorCalls = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseError.Set();
+            }
+            faultJoined = fault.Join(5000);
+            if (disposeStarted)
+                disposeJoinedAfterRelease = dispose.Join(5000);
+        }
+
+        Check.True(reachedError,
+            "fault reaches already-owned Error entry");
+        Check.True(disposeJoinedBeforeRelease,
+            "Dispose returns before Error release");
+        Check.True(disposeJoinedAfterRelease,
+            "Error Dispose thread remains joined after release");
+        Check.True(faultJoined,
+            "fault owner finishes after Error release");
+        Check.True(faultError == null && disposeError == null,
+            "Error Dispose workers have no exception");
+        Check.True(faultResult,
+            "ordinary fault owns Error before Dispose");
+        Check.Equal(0, blockedErrorCalls,
+            "Error barrier is the first sink operation");
+        Check.Equal(0, blockedCloses,
+            "Dispose cannot Close while fault owns Error");
+        Check.Equal(0, blockedFailures,
+            "Dispose cannot emit a marker while Error is blocked");
+        Check.Equal(1, fixture.Sink.ErrorCalls,
+            "fault owner writes Error exactly once");
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            "fault owner retains one durable Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "fault owner closes exactly once");
+        Check.Sequence(
+            new string[] { "capture_failed" },
+            fixture.Reporter.FailedCodes,
+            "fault owner retains its failure marker");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:error:capture_failed",
+                "sink:close",
+                "report:failed:capture_failed"
+            },
+            Tail(TerminalEvents(fixture), 3),
+            "fault owner completes Error Close Failed after Dispose");
+    }
+
+    private static void DisposeDuringEndLeavesSuccessOwner()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.CompleteFirstTwoSteps();
+        fixture.OpenThirdStep();
+        fixture.ObserveThirdCandidate();
+
+        Exception completionError = null;
+        Exception disposeError = null;
+        bool reachedEnd;
+        bool disposeStarted = false;
+        bool disposeJoinedBeforeRelease = false;
+        bool disposeJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedEnds = -1;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedCompletes = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent endEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseEnd =
+            new ManualResetEvent(false))
+        {
+            fixture.Sink.EndObserved = delegate(EndRecord record)
+            {
+                endEntered.Set();
+                releaseEnd.WaitOne();
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.ObserveThirdMatch(DriverFixture.UtcFinish);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread dispose = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Driver.Dispose();
+                }
+                catch (Exception error)
+                {
+                    disposeError = error;
+                }
+            });
+            completion.Start();
+            reachedEnd = endEntered.WaitOne(5000);
+            try
+            {
+                if (reachedEnd)
+                {
+                    dispose.Start();
+                    disposeStarted = true;
+                    disposeJoinedBeforeRelease = dispose.Join(5000);
+                    blockedEnds = fixture.Sink.EndRecords.Count;
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedCompletes = fixture.Reporter.CompleteCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseEnd.Set();
+            }
+            completionJoined = completion.Join(5000);
+            if (disposeStarted)
+                disposeJoinedAfterRelease = dispose.Join(5000);
+        }
+
+        Check.True(reachedEnd,
+            "success reaches already-owned durable End");
+        Check.True(disposeJoinedBeforeRelease,
+            "Dispose returns before End release");
+        Check.True(disposeJoinedAfterRelease,
+            "End Dispose thread remains joined after release");
+        Check.True(completionJoined,
+            "success owner finishes after End release");
+        Check.True(completionError == null && disposeError == null,
+            "End Dispose workers have no exception");
+        Check.Equal(1, blockedEnds,
+            "End is durable before its barrier");
+        Check.Equal(0, blockedErrors,
+            "Dispose cannot replace success with Error");
+        Check.Equal(0, blockedCloses,
+            "Dispose cannot Close while success owns End");
+        Check.Equal(0, blockedCompletes,
+            "Complete waits for End release");
+        Check.Equal(0, blockedFailures,
+            "Dispose cannot emit a marker while End is blocked");
+        Check.Equal(PassivePhase.Done, fixture.Driver.Phase,
+            "success remains Done after concurrent Dispose");
         Check.Equal(1, fixture.Sink.EndRecords.Count,
-            "completion callback race retains one End");
+            "success retains one durable End");
         Check.Equal(0, fixture.Sink.ErrorCalls,
-            "completion callback race never attempts Error");
+            "success emits no Error");
         Check.Equal(1, fixture.Sink.CloseCalls,
-            "completion callback race closes once");
+            "success owner closes exactly once");
         Check.Equal(1, fixture.Reporter.CompleteCalls,
-            "completion callback race attempts Complete once");
+            "success owner completes exactly once");
         Check.Equal(0, fixture.Reporter.FailedCalls,
-            "completion callback race emits no failure marker");
+            "success emits no failure marker");
+        Check.Sequence(
+            new string[]
+            {
+                "sink:step:2",
+                "sink:end",
+                "sink:close",
+                "report:complete"
+            },
+            Tail(TerminalEvents(fixture), 4),
+            "success owner completes Step End Close Complete");
     }
 
-    private static void DisposeAndLateCallbacksAreFinal()
+    private static void DisposeWaitsForInFlightRun()
     {
-        DriverFixture disposed = DriverFixture.Active();
-        HookToken openPoll = disposed.Driver.PlayerPollEntered();
-        disposed.Driver.Dispose();
-        disposed.Driver.Dispose();
-        disposed.Driver.ClearThrew(openPoll);
-        disposed.Driver.ClearThrew(openPoll);
-        Check.Equal(1, disposed.Sink.CloseCalls,
-            "Dispose closes at most once");
-        Check.Equal(0, disposed.Sink.EndRecords.Count,
-            "Dispose writes no End");
-        Check.Equal(0, disposed.Sink.ErrorRecords.Count,
-            "Dispose writes no Error");
-        Check.Equal(0, disposed.Reporter.FailedCalls,
-            "Dispose emits no terminal marker");
-        Check.False(disposed.Driver.TryFault("observer_exception"),
-            "disposed late fault is inert");
-        FakeUpdateObservation late =
-            new FakeUpdateObservation(disposed.Events)
+        DriverFixture fixture = DriverFixture.Unprepared();
+        Exception prepareError = null;
+        Exception disposeError = null;
+        bool prepareResult = true;
+        bool reachedRun;
+        bool disposeStarted = false;
+        bool disposeJoinedBeforeRelease = false;
+        bool disposeJoinedAfterRelease = false;
+        bool prepareJoined;
+        int blockedRunCalls = -1;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent runEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseRun =
+            new ManualResetEvent(false))
+        {
+            fixture.Sink.RunEntering = delegate(RunRecord record)
             {
-                FirstState = disposed.State,
-                SecondState = disposed.State,
-                Now = 5.0
+                runEntered.Set();
+                releaseRun.WaitOne();
             };
-        disposed.Boundary.Observe(late);
-        Check.Equal(0, late.StateCalls,
-            "disposed late update does not inspect observation");
+            Thread prepare = new Thread(delegate()
+            {
+                try
+                {
+                    prepareResult =
+                        fixture.Driver.Prepare(ProtocolSamples.Run);
+                }
+                catch (Exception error)
+                {
+                    prepareError = error;
+                }
+            });
+            Thread dispose = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Driver.Dispose();
+                }
+                catch (Exception error)
+                {
+                    disposeError = error;
+                }
+            });
+            prepare.Start();
+            reachedRun = runEntered.WaitOne(5000);
+            try
+            {
+                if (reachedRun)
+                {
+                    dispose.Start();
+                    disposeStarted = true;
+                    disposeJoinedBeforeRelease = dispose.Join(5000);
+                    blockedRunCalls = fixture.Sink.RunCalls;
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseRun.Set();
+            }
+            prepareJoined = prepare.Join(5000);
+            if (disposeStarted)
+                disposeJoinedAfterRelease = dispose.Join(5000);
+        }
 
-        DriverFixture done = DriverFixture.Ready();
-        HookToken openStateSet =
-            done.Driver.StateSetEntered(done.State, done.State);
-        done.CompleteThreeSteps();
-        int doneEvents = done.Events.Count;
-        done.Driver.StateSetReturned(
-            openStateSet, done.State, 40.0);
-        done.Driver.StateSetReturned(
-            openStateSet, done.State, 40.0);
-        done.Driver.ClearThrew(openStateSet);
-        done.Driver.RestartEntered();
-        done.Driver.TryFault("observer_exception");
-        done.Driver.Dispose();
-        done.Driver.Dispose();
-        Check.Equal(doneEvents, done.Events.Count,
-            "Done matching cleanup and later callbacks are output-inert");
-        Check.Equal(PassivePhase.Done, done.Driver.Phase,
-            "Done remains final");
-        Check.Equal(1, done.Sink.CloseCalls,
-            "Done Dispose cannot Close twice");
+        Check.True(reachedRun,
+            "Dispose race reaches pre-durability Run entry");
+        Check.True(disposeJoinedBeforeRelease,
+            "Dispose returns before Run release");
+        Check.True(disposeJoinedAfterRelease,
+            "Run Dispose thread remains joined after release");
+        Check.True(prepareJoined,
+            "disposed Prepare finishes after Run release");
+        Check.True(prepareError == null && disposeError == null,
+            "Run Dispose workers have no exception");
+        Check.False(prepareResult,
+            "disposed Run is not published as prepared");
+        Check.Equal(0, blockedRunCalls,
+            "Run Dispose barrier is the first sink operation");
+        Check.Equal(0, blockedErrors,
+            "Run Dispose never attempts Error");
+        Check.Equal(0, blockedCloses,
+            "Dispose Close waits for active Run output");
+        Check.Equal(0, blockedFailures,
+            "Run Dispose emits no failure marker");
+        Check.Equal(1, fixture.Sink.RunCalls,
+            "entered disposed Run completes once");
+        Check.Equal(1, fixture.Sink.RunRecords.Count,
+            "entered disposed Run becomes durable");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "disposed Run closes once after release");
+        Check.Equal(0, fixture.Reporter.FailedCalls,
+            "disposed Run remains marker-free");
+        Check.False(fixture.Driver.Activate(),
+            "disposed Run cannot activate");
+        Check.Sequence(
+            new string[] { "sink:run", "sink:close" },
+            TerminalEvents(fixture),
+            "disposed Run cleanup order is Run Close");
+    }
+
+    private static void DisposeWaitsForInFlightInitial()
+    {
+        DriverFixture fixture = DriverFixture.Active();
+        CaptureRecord capture =
+            ProtocolSamples.Capture("dispose-initial-race-pair");
+        PrimeInitialCandidate(fixture, capture);
+
+        Exception completionError = null;
+        Exception disposeError = null;
+        bool reachedInitial;
+        bool disposeStarted = false;
+        bool disposeJoinedBeforeRelease = false;
+        bool disposeJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedInitialCalls = -1;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent initialEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseInitial =
+            new ManualResetEvent(false))
+        {
+            fixture.Sink.InitialEntering = delegate(InitialRecord record)
+            {
+                initialEntered.Set();
+                releaseInitial.WaitOne();
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        3.0,
+                        true,
+                        capture);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread dispose = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Driver.Dispose();
+                }
+                catch (Exception error)
+                {
+                    disposeError = error;
+                }
+            });
+            completion.Start();
+            reachedInitial = initialEntered.WaitOne(5000);
+            try
+            {
+                if (reachedInitial)
+                {
+                    dispose.Start();
+                    disposeStarted = true;
+                    disposeJoinedBeforeRelease = dispose.Join(5000);
+                    blockedInitialCalls = fixture.Sink.InitialCalls;
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseInitial.Set();
+            }
+            completionJoined = completion.Join(5000);
+            if (disposeStarted)
+                disposeJoinedAfterRelease = dispose.Join(5000);
+        }
+
+        Check.True(reachedInitial,
+            "Dispose race reaches pre-durability Initial entry");
+        Check.True(disposeJoinedBeforeRelease,
+            "Dispose returns before Initial release");
+        Check.True(disposeJoinedAfterRelease,
+            "Initial Dispose thread remains joined after release");
+        Check.True(completionJoined,
+            "disposed Initial completion finishes after release");
+        Check.True(completionError == null && disposeError == null,
+            "Initial Dispose workers have no exception");
+        Check.Equal(0, blockedInitialCalls,
+            "Initial Dispose barrier is the first sink operation");
+        Check.Equal(0, blockedErrors,
+            "Initial Dispose never attempts Error");
+        Check.Equal(0, blockedCloses,
+            "Dispose Close waits for active Initial output");
+        Check.Equal(0, blockedFailures,
+            "Initial Dispose emits no failure marker");
+        Check.Equal(1, fixture.Sink.InitialCalls,
+            "entered disposed Initial completes once");
+        Check.Equal(1, fixture.Sink.InitialRecords.Count,
+            "entered disposed Initial becomes durable");
+        Check.Same(capture, fixture.Sink.InitialRecords[0].Capture,
+            "disposed Initial preserves the paired capture");
+        Check.Sequence(new int[0], fixture.Reporter.ReadyValues,
+            "Dispose during Initial suppresses Ready(0)");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "disposed Initial emits no Error");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "disposed Initial closes once after release");
+        Check.Equal(0, fixture.Reporter.FailedCalls,
+            "disposed Initial emits no failure marker");
+        Check.Sequence(
+            new string[] { "sink:initial", "sink:close" },
+            Tail(TerminalEvents(fixture), 2),
+            "disposed Initial cleanup order is Initial Close");
+    }
+
+    private static void DisposeWaitsForInFlightStep()
+    {
+        DriverFixture fixture = DriverFixture.Ready();
+        fixture.OpenDirection(2, true, true, 10.0);
+        fixture.Neutral();
+        fixture.Observe(
+            fixture.State,
+            fixture.State,
+            11.0,
+            true,
+            ProtocolSamples.MovedCapture);
+
+        Exception completionError = null;
+        Exception disposeError = null;
+        bool reachedStep;
+        bool disposeStarted = false;
+        bool disposeJoined = false;
+        bool disposeJoinedAfterRelease = false;
+        bool completionJoined;
+        int blockedStepCalls = -1;
+        int blockedErrors = -1;
+        int blockedCloses = -1;
+        int blockedFailures = -1;
+        using (ManualResetEvent stepEntered =
+            new ManualResetEvent(false))
+        using (ManualResetEvent releaseStep =
+            new ManualResetEvent(false))
+        {
+            fixture.Sink.StepEntering = delegate(StepRecord record)
+            {
+                if (record.InputIndex == 0)
+                {
+                    stepEntered.Set();
+                    releaseStep.WaitOne();
+                }
+            };
+            Thread completion = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Observe(
+                        fixture.State,
+                        fixture.State,
+                        12.0,
+                        true,
+                        ProtocolSamples.MovedCapture);
+                }
+                catch (Exception error)
+                {
+                    completionError = error;
+                }
+            });
+            Thread dispose = new Thread(delegate()
+            {
+                try
+                {
+                    fixture.Driver.Dispose();
+                }
+                catch (Exception error)
+                {
+                    disposeError = error;
+                }
+            });
+            completion.Start();
+            reachedStep = stepEntered.WaitOne(5000);
+            try
+            {
+                if (reachedStep)
+                {
+                    dispose.Start();
+                    disposeStarted = true;
+                    disposeJoined = dispose.Join(5000);
+                    blockedStepCalls = fixture.Sink.StepCalls;
+                    blockedErrors = fixture.Sink.ErrorCalls;
+                    blockedCloses = fixture.Sink.CloseCalls;
+                    blockedFailures = fixture.Reporter.FailedCalls;
+                }
+            }
+            finally
+            {
+                releaseStep.Set();
+            }
+            completionJoined = completion.Join(5000);
+            if (disposeStarted)
+                disposeJoinedAfterRelease = dispose.Join(5000);
+        }
+
+        Check.True(reachedStep,
+            "Dispose race reaches pre-durability Step entry");
+        Check.True(disposeJoined,
+            "Dispose returns before in-flight Step release");
+        Check.True(disposeJoinedAfterRelease,
+            "Dispose thread remains joined after Step release");
+        Check.True(completionJoined,
+            "disposed Step completion thread finishes");
+        Check.True(completionError == null && disposeError == null,
+            "Dispose race workers have no exception");
+        Check.Equal(0, blockedStepCalls,
+            "pre-durability barrier is the first Step operation");
+        Check.Equal(0, blockedErrors,
+            "Dispose never attempts Error during Step");
+        Check.Equal(0, blockedCloses,
+            "Dispose Close waits for in-flight Step");
+        Check.Equal(0, blockedFailures,
+            "Dispose emits no marker during Step");
+        Check.Equal(1, fixture.Sink.StepCalls,
+            "entered Step completes exactly once after release");
+        Check.Equal(1, fixture.Sink.StepRecords.Count,
+            "entered Step becomes durable after release");
+        Check.Equal(0, fixture.Sink.ErrorCalls,
+            "disposed Step emits no Error");
+        Check.Equal(0, fixture.Sink.EndCalls,
+            "disposed Step emits no End");
+        Check.Equal(1, fixture.Sink.CloseCalls,
+            "disposed Step closes once after relinquishing ownership");
+        Check.Equal(0, fixture.Reporter.CompleteCalls,
+            "disposed Step emits no Complete");
+        Check.Equal(0, fixture.Reporter.FailedCalls,
+            "disposed Step emits no Failed marker");
+        Check.Sequence(new int[] { 0 }, fixture.Reporter.ReadyValues,
+            "disposed Step emits no Ready continuation");
+        Check.Sequence(
+            new string[] { "sink:step:0", "sink:close" },
+            Tail(TerminalEvents(fixture), 2),
+            "disposed Step cleanup order is Step Close");
     }
 
     private static void AssertError(
@@ -840,6 +2394,29 @@ internal static class PassiveDriverTerminalTests
         return result;
     }
 
+    private static void AssertLastRealTraceLines(
+        byte[] payload,
+        byte[] expectedFirst,
+        byte[] expectedSecond,
+        string label)
+    {
+        UTF8Encoding utf8 = new UTF8Encoding(false, true);
+        string[] lines = utf8.GetString(payload).Split(
+            new char[] { '\n' });
+        Check.True(lines.Length >= 3,
+            label + " line count");
+        Check.Equal(String.Empty, lines[lines.Length - 1],
+            label + " final LF");
+        Check.Equal(
+            utf8.GetString(expectedFirst),
+            lines[lines.Length - 3],
+            label + " first line");
+        Check.Equal(
+            utf8.GetString(expectedSecond),
+            lines[lines.Length - 2],
+            label + " second line");
+    }
+
     private static List<string> Tail(List<string> values, int count)
     {
         return values.GetRange(values.Count - count, count);
diff --git a/oracle/plugin/tests/PassiveDriverTestSupport.cs b/oracle/plugin/tests/PassiveDriverTestSupport.cs
index d0c0850c83bdf75804927cfc0c844a046d71ea2f..97ac074afa25befbcf2d01c377e92da175894a58 100644
--- a/oracle/plugin/tests/PassiveDriverTestSupport.cs
+++ b/oracle/plugin/tests/PassiveDriverTestSupport.cs
@@ -1,6 +1,121 @@
 using System;
 using System.Collections.Generic;
+using System.IO;
 using System.Reflection;
+using System.Threading;
+
+internal sealed class BlockingTraceOutput : ITraceOutput
+{
+    private readonly object sync = new object();
+    private readonly List<byte> bytes = new List<byte>();
+    private ManualResetEvent writeEntered;
+    private ManualResetEvent releaseWrite;
+    private bool blockNextWrite;
+    private bool closed;
+    private int flushCalls;
+    private int closeCalls;
+
+    internal int ByteCount
+    {
+        get
+        {
+            lock (sync)
+                return bytes.Count;
+        }
+    }
+
+    internal int FlushCalls
+    {
+        get
+        {
+            lock (sync)
+                return flushCalls;
+        }
+    }
+
+    internal int CloseCalls
+    {
+        get
+        {
+            lock (sync)
+                return closeCalls;
+        }
+    }
+
+    internal void BlockNextWrite(
+        ManualResetEvent entered,
+        ManualResetEvent release)
+    {
+        if (entered == null)
+            throw new ArgumentNullException("entered");
+        if (release == null)
+            throw new ArgumentNullException("release");
+        lock (sync)
+        {
+            if (blockNextWrite)
+                throw new InvalidOperationException(
+                    "a write is already armed");
+            writeEntered = entered;
+            releaseWrite = release;
+            blockNextWrite = true;
+        }
+    }
+
+    internal byte[] SnapshotBytes()
+    {
+        lock (sync)
+            return bytes.ToArray();
+    }
+
+    public int Write(byte[] buffer, int offset, int count)
+    {
+        ManualResetEvent entered = null;
+        ManualResetEvent release = null;
+        lock (sync)
+        {
+            if (blockNextWrite)
+            {
+                blockNextWrite = false;
+                entered = writeEntered;
+                release = releaseWrite;
+            }
+        }
+        if (entered != null)
+        {
+            entered.Set();
+            release.WaitOne();
+        }
+        lock (sync)
+        {
+            if (closed)
+                throw new IOException("write after close");
+            for (int index = 0; index < count; index++)
+                bytes.Add(buffer[offset + index]);
+        }
+        return count;
+    }
+
+    public void Flush()
+    {
+        lock (sync)
+        {
+            if (closed)
+                throw new IOException("flush after close");
+            flushCalls++;
+        }
+    }
+
+    public void Close()
+    {
+        lock (sync)
+        {
+            closeCalls++;
+            if (closed)
+                throw new IOException("duplicate close");
+            closed = true;
+        }
+    }
+}
 
 internal sealed class FakeTraceSink : ITraceSink
 {
@@ -27,8 +142,12 @@ internal sealed class FakeTraceSink : ITraceSink
     internal Exception EndFailure { get; set; }
     internal Exception ErrorFailure { get; set; }
     internal Exception CloseFailure { get; set; }
+    internal Action<RunRecord> RunEntering { get; set; }
+    internal Action<InitialRecord> InitialEntering { get; set; }
+    internal Action<StepRecord> StepEntering { get; set; }
     internal Action<StepRecord> StepObserved { get; set; }
     internal Action<EndRecord> EndObserved { get; set; }
+    internal Action<ErrorRecord> ErrorEntering { get; set; }
     internal int RunCalls;
     internal int InitialCalls;
     internal int StepCalls;
@@ -38,6 +157,8 @@ internal sealed class FakeTraceSink : ITraceSink
 
     public void WriteRun(RunRecord record)
     {
+        if (RunEntering != null)
+            RunEntering(record);
         RunCalls++;
         Add("sink:run");
         if (RunFailure != null)
@@ -47,6 +168,8 @@ internal sealed class FakeTraceSink : ITraceSink
 
     public void WriteInitial(InitialRecord record)
     {
+        if (InitialEntering != null)
+            InitialEntering(record);
         InitialCalls++;
         Add("sink:initial");
         if (InitialFailure != null)
@@ -56,6 +179,8 @@ internal sealed class FakeTraceSink : ITraceSink
 
     public void WriteStep(StepRecord record)
     {
+        if (StepEntering != null)
+            StepEntering(record);
         StepCalls++;
         Add("sink:step:" + record.InputIndex.ToString());
         if (StepFailure != null)
@@ -78,6 +203,8 @@ internal sealed class FakeTraceSink : ITraceSink
 
     public void WriteError(ErrorRecord record)
     {
+        if (ErrorEntering != null)
+            ErrorEntering(record);
         ErrorCalls++;
         Add("sink:error:" + record.Code);
         if (ErrorFailure != null)
@@ -115,6 +242,7 @@ internal sealed class FakePassiveReporter : IPassiveReporter
     internal Exception CompleteFailure { get; set; }
     internal Exception FailedFailure { get; set; }
     internal Exception DiagnosticFailure { get; set; }
+    internal Action<int> ReadyObserved { get; set; }
     internal Action CompleteObserved { get; set; }
     internal int CompleteCalls;
     internal int FailedCalls;
@@ -124,6 +252,8 @@ internal sealed class FakePassiveReporter : IPassiveReporter
     {
         ReadyValues.Add(completedInputs);
         Add("report:ready:" + completedInputs.ToString() + "/3");
+        if (ReadyObserved != null)
+            ReadyObserved(completedInputs);
         if (ReadyFailure != null)
             throw ReadyFailure;
     }
@@ -283,12 +413,20 @@ internal sealed partial class DriverFixture
     internal readonly PassiveDriver Driver;
     internal readonly PassiveUpdateBoundary Boundary;
 
-    private DriverFixture(int maxFrames, double maxSeconds)
+    private DriverFixture(
+        int maxFrames,
+        double maxSeconds,
+        ITraceSink traceSink)
     {
-        Sink = new FakeTraceSink(Events);
+        Sink = traceSink as FakeTraceSink;
+        if (traceSink == null)
+        {
+            Sink = new FakeTraceSink(Events);
+            traceSink = Sink;
+        }
         Reporter = new FakePassiveReporter(Events);
         Driver = new PassiveDriver(
-            Sink,
+            traceSink,
             Reporter,
             OracleProtocol.ExpectedInputCount,
             maxFrames,
@@ -305,7 +443,7 @@ internal sealed partial class DriverFixture
         int maxFrames,
         double maxSeconds)
     {
-        return new DriverFixture(maxFrames, maxSeconds);
+        return new DriverFixture(maxFrames, maxSeconds, null);
     }
 
     internal static DriverFixture Active()
@@ -328,7 +466,25 @@ internal sealed partial class DriverFixture
 
     internal static DriverFixture Ready()
     {
-        DriverFixture fixture = Active();
+        return MakeReady(Active());
+    }
+
+    internal static DriverFixture ReadyWithSink(ITraceSink sink)
+    {
+        if (sink == null)
+            throw new ArgumentNullException("sink");
+        DriverFixture fixture =
+            new DriverFixture(600, 30.0, sink);
+        Check.True(
+            fixture.Driver.Prepare(ProtocolSamples.Run),
+            "custom sink prepare");
+        Check.True(fixture.Driver.Activate(),
+            "custom sink activate");
+        return MakeReady(fixture);
+    }
+
+    private static DriverFixture MakeReady(DriverFixture fixture)
+    {
         fixture.Observe(
             fixture.State,
             true,
~~~
<!-- TASK5-PATCH-END:C53C1-TESTS -->

**C53C1-PRODUCTION patch:** SHA-256 `7c000fabda103b116b7a5ebc773da13692d3b4a838dcf280dd68b7ab5590102c`; 598 LF lines; 18412 bytes.
<!-- TASK5-PATCH-BEGIN:C53C1-PRODUCTION -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index a9e7320a3ce3bb43863f5864585364c2f472b0ce..b132f89b321345452901faab870ea0d642b93e06 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -3,6 +3,60 @@ using System.Threading;
 
 internal sealed partial class PassiveDriver : IDisposable
 {
+    private const int NoTerminalOwner = 0;
+    private const int FaultTerminalOwner = 1;
+    private const int SuccessTerminalOwner = 2;
+    private const int DisposeTerminalOwner = 3;
+
+    private enum TerminalWorkKind
+    {
+        OrdinaryFault,
+        TraceIoFailure,
+        Dispose
+    }
+
+    private enum StepContinuation
+    {
+        None,
+        Ready,
+        Complete
+    }
+
+    private sealed class TerminalWork
+    {
+        internal TerminalWorkKind Kind;
+        internal string Code;
+        internal ErrorRecord Error;
+
+        internal static TerminalWork Ordinary(
+            string code,
+            ErrorRecord error)
+        {
+            return new TerminalWork
+            {
+                Kind = TerminalWorkKind.OrdinaryFault,
+                Code = code,
+                Error = error
+            };
+        }
+
+        internal static TerminalWork TraceIo()
+        {
+            return new TerminalWork
+            {
+                Kind = TerminalWorkKind.TraceIoFailure
+            };
+        }
+
+        internal static TerminalWork DisposeOnly()
+        {
+            return new TerminalWork
+            {
+                Kind = TerminalWorkKind.Dispose
+            };
+        }
+    }
+
     private static readonly string[] RecordErrorCodes =
         new string[]
         {
@@ -71,6 +125,7 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private readonly ITraceSink sink;
     private readonly IPassiveReporter reporter;
+    private readonly object outputLeaseSync = new object();
     private readonly int expectedInputCount;
     private readonly int maxSettleFrames;
     private readonly double maxSettleSeconds;
@@ -83,6 +138,8 @@ internal sealed partial class PassiveDriver : IDisposable
     private int disposed;
     private int sinkCloseAttempted;
     private int terminalOwner;
+    private bool outputLeaseActive;
+    private TerminalWork deferredTerminalWork;
 
     private string runId;
     private DateTime startedAtUtc;
@@ -208,19 +265,40 @@ internal sealed partial class PassiveDriver : IDisposable
         }
         if (Read(ref disposed) != 0 || Read(ref disabled) != 0)
             return false;
+        if (!TryAcquireOutputLease())
+            return false;
+
+        bool traceIoFailure = false;
         try
         {
-            sink.WriteRun(run);
-            runId = run.RunId;
-            startedAtUtc = run.StartedAtUtc;
-            Interlocked.Exchange(ref prepared, 1);
-            return true;
+            try
+            {
+                sink.WriteRun(run);
+            }
+            catch (Exception error)
+            {
+                traceIoFailure = true;
+                SelectTraceIoFailure();
+                SafeDiagnostic(error);
+                return false;
+            }
+            lock (outputLeaseSync)
+            {
+                if (TerminalSelected()
+                    || Read(ref disposed) != 0
+                    || Read(ref disabled) != 0)
+                {
+                    return false;
+                }
+                runId = run.RunId;
+                startedAtUtc = run.StartedAtUtc;
+                Interlocked.Exchange(ref prepared, 1);
+                return true;
+            }
         }
-        catch (Exception error)
+        finally
         {
-            SafeDiagnostic(error);
-            SelectTraceIoFailure();
-            return false;
+            ReleaseOutputLease(traceIoFailure);
         }
     }
 
@@ -608,7 +686,21 @@ internal sealed partial class PassiveDriver : IDisposable
         if (Interlocked.CompareExchange(ref disposed, 1, 0) != 0)
             return;
         Interlocked.Exchange(ref disabled, 1);
-        BestEffortClose();
+        TerminalWork work = null;
+        bool execute = false;
+        lock (outputLeaseSync)
+        {
+            if (Interlocked.CompareExchange(
+                ref terminalOwner,
+                DisposeTerminalOwner,
+                NoTerminalOwner) == NoTerminalOwner)
+            {
+                work = TerminalWork.DisposeOnly();
+                execute = QueueOrAcquireOutputLeaseLocked(work);
+            }
+        }
+        if (execute)
+            ExecuteTerminalWorkAndRelease(work);
     }
 
     private void CompleteUpdateCore(
@@ -704,24 +796,72 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private void EmitInitial(CaptureRecord capture)
     {
-        sink.WriteInitial(new InitialRecord(runId, capture));
-        stableState = epochState;
-        phase = PassivePhase.Ready;
-        currentFrames = 0;
-        neutralSeen = false;
-        candidateSignature = null;
-        lastCapture = null;
+        InitialRecord record = new InitialRecord(runId, capture);
+        if (!TryAcquireOutputLease())
+        {
+            ClearInitialAfterTerminalReturn();
+            return;
+        }
+
+        bool traceIoFailure = false;
         try
         {
-            reporter.Ready(0);
+            try
+            {
+                sink.WriteInitial(record);
+            }
+            catch (TraceIoException)
+            {
+                traceIoFailure = true;
+                SelectTraceIoFailure();
+                throw;
+            }
+
+            bool emitReady = false;
+            lock (outputLeaseSync)
+            {
+                if (TerminalSelected()
+                    || Read(ref disposed) != 0
+                    || Read(ref disabled) != 0)
+                {
+                    ClearInitialAfterTerminalReturn();
+                }
+                else
+                {
+                    stableState = epochState;
+                    phase = PassivePhase.Ready;
+                    ClearInitialAfterTerminalReturn();
+                    emitReady = true;
+                }
+            }
+            if (emitReady)
+            {
+                try
+                {
+                    reporter.Ready(0);
+                }
+                catch (Exception)
+                {
+                    TryFaultInternal(
+                        "observer_exception", FaultRequest.Derived());
+                }
+            }
         }
-        catch (Exception)
+        finally
         {
-            TryFaultInternal(
-                "observer_exception", FaultRequest.Derived());
+            ReleaseOutputLease(traceIoFailure);
         }
     }
 
+    private void ClearInitialAfterTerminalReturn()
+    {
+        currentFrames = 0;
+        neutralSeen = false;
+        candidateSignature = null;
+        lastCapture = null;
+        ClearAttemptFields();
+    }
+
     private bool HandleManualAttempt(
         OracleInput input,
         object stateReference,
@@ -804,8 +944,12 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private void ClearAttemptAfterStep()
     {
-        if (!TerminalSelected())
+        if (!TerminalSelected()
+            && Read(ref disposed) == 0
+            && Read(ref disabled) == 0)
+        {
             phase = PassivePhase.Ready;
+        }
         currentFrames = 0;
         neutralSeen = false;
         candidateSignature = null;
@@ -912,35 +1056,29 @@ internal sealed partial class PassiveDriver : IDisposable
         FaultRequest request)
     {
         OracleErrors.ForCode(code);
-        if (Interlocked.CompareExchange(
-            ref terminalOwner, 1, 0) != 0)
-        {
-            return false;
-        }
-
-        PassivePhase faultPhase = phase;
-        phase = PassivePhase.Faulted;
-        if (Read(ref prepared) == 0)
-        {
-            BestEffortClose();
-            SafeFailed("trace_io_failed");
-            return true;
-        }
+        TerminalWork work = null;
+        bool execute = false;
+        lock (outputLeaseSync)
+        {
+            if (Interlocked.CompareExchange(
+                ref terminalOwner,
+                FaultTerminalOwner,
+                NoTerminalOwner) != NoTerminalOwner)
+            {
+                return false;
+            }
 
-        bool durable = false;
-        try
-        {
-            sink.WriteError(
-                BuildErrorRecord(code, request, faultPhase));
-            CloseSink();
-            durable = true;
-        }
-        catch (Exception error)
-        {
-            SafeDiagnostic(error);
-            BestEffortClose();
+            PassivePhase faultPhase = phase;
+            phase = PassivePhase.Faulted;
+            work = Read(ref prepared) == 0
+                ? TerminalWork.TraceIo()
+                : TerminalWork.Ordinary(
+                    code,
+                    BuildErrorRecord(code, request, faultPhase));
+            execute = QueueOrAcquireOutputLeaseLocked(work);
         }
-        SafeFailed(durable ? code : "trace_io_failed");
+        if (execute)
+            ExecuteTerminalWorkAndRelease(work);
         return true;
     }
 
@@ -995,14 +1133,129 @@ internal sealed partial class PassiveDriver : IDisposable
 
     private void SelectTraceIoFailure()
     {
-        if (Interlocked.CompareExchange(
-            ref terminalOwner, 1, 0) != 0)
+        TerminalWork work = null;
+        bool execute = false;
+        lock (outputLeaseSync)
+        {
+            if (Interlocked.CompareExchange(
+                ref terminalOwner,
+                FaultTerminalOwner,
+                NoTerminalOwner) != NoTerminalOwner)
+            {
+                return;
+            }
+            phase = PassivePhase.Faulted;
+            work = TerminalWork.TraceIo();
+            execute = QueueOrAcquireOutputLeaseLocked(work);
+        }
+        if (execute)
+            ExecuteTerminalWorkAndRelease(work);
+    }
+
+    private bool TryAcquireOutputLease()
+    {
+        lock (outputLeaseSync)
         {
-            return;
+            if (TerminalSelected()
+                || Read(ref disposed) != 0
+                || Read(ref disabled) != 0)
+            {
+                return false;
+            }
+            if (outputLeaseActive)
+                throw new InvalidOperationException(
+                    "output lease is already active");
+            outputLeaseActive = true;
+            return true;
+        }
+    }
+
+    private bool QueueOrAcquireOutputLeaseLocked(TerminalWork work)
+    {
+        if (work == null)
+            throw new ArgumentNullException("work");
+        if (outputLeaseActive)
+        {
+            if (deferredTerminalWork != null)
+            {
+                throw new InvalidOperationException(
+                    "terminal work is already deferred");
+            }
+            deferredTerminalWork = work;
+            return false;
+        }
+        outputLeaseActive = true;
+        return true;
+    }
+
+    private void ReleaseOutputLease(bool traceIoFailure)
+    {
+        TerminalWork work = null;
+        lock (outputLeaseSync)
+        {
+            if (!outputLeaseActive)
+                throw new InvalidOperationException(
+                    "output lease is not active");
+            if (traceIoFailure
+                && deferredTerminalWork != null
+                && deferredTerminalWork.Kind
+                    == TerminalWorkKind.OrdinaryFault)
+            {
+                deferredTerminalWork = TerminalWork.TraceIo();
+            }
+            if (deferredTerminalWork == null)
+            {
+                outputLeaseActive = false;
+            }
+            else
+            {
+                work = deferredTerminalWork;
+                deferredTerminalWork = null;
+            }
+        }
+        if (work != null)
+            ExecuteTerminalWorkAndRelease(work);
+    }
+
+    private void ExecuteTerminalWorkAndRelease(TerminalWork work)
+    {
+        try
+        {
+            if (work.Kind == TerminalWorkKind.OrdinaryFault)
+            {
+                bool durable = false;
+                try
+                {
+                    sink.WriteError(work.Error);
+                    CloseSink();
+                    durable = true;
+                }
+                catch (Exception error)
+                {
+                    SafeDiagnostic(error);
+                    BestEffortClose();
+                }
+                SafeFailed(
+                    durable ? work.Code : "trace_io_failed");
+            }
+            else if (work.Kind == TerminalWorkKind.TraceIoFailure)
+            {
+                phase = PassivePhase.Faulted;
+                BestEffortClose();
+                SafeFailed("trace_io_failed");
+            }
+            else
+            {
+                BestEffortClose();
+            }
+        }
+        finally
+        {
+            lock (outputLeaseSync)
+            {
+                outputLeaseActive = false;
+            }
         }
-        phase = PassivePhase.Faulted;
-        BestEffortClose();
-        SafeFailed("trace_io_failed");
     }
 
     private void CloseSink()
diff --git a/oracle/plugin/Core/PassiveDriverCompletion.cs b/oracle/plugin/Core/PassiveDriverCompletion.cs
index 02437c82042f5f540789afdbbfe71a5b36c7cef7..638d2882e988b17d686a7791604a497438e7d4e3 100644
--- a/oracle/plugin/Core/PassiveDriverCompletion.cs
+++ b/oracle/plugin/Core/PassiveDriverCompletion.cs
@@ -3,7 +3,8 @@ using System.Threading;
 
 internal sealed partial class PassiveDriver
 {
-    private void FinishExpectedInputCount(DateTime finishedAtUtc)
+    private bool TryClaimExpectedInputCompletion(
+        DateTime finishedAtUtc)
     {
         OracleValidation.Utc(finishedAtUtc, "finishedAtUtc");
         if (finishedAtUtc < startedAtUtc)
@@ -17,12 +18,14 @@ internal sealed partial class PassiveDriver
             throw new InvalidOperationException(
                 "completion requires the expected input count");
         }
-        if (Interlocked.CompareExchange(
-            ref terminalOwner, 1, 0) != 0)
-        {
-            return;
-        }
+        return Interlocked.CompareExchange(
+            ref terminalOwner,
+            SuccessTerminalOwner,
+            NoTerminalOwner) == NoTerminalOwner;
+    }
 
+    private void FinishExpectedInputCount(DateTime finishedAtUtc)
+    {
         try
         {
             sink.WriteEnd(
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 5fd9120fcdbe364013a08379fc3848cbea4d35ff..88951007d1f25df778c025009c0b1d23cd6645ef 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -233,37 +233,90 @@ internal sealed partial class PassiveDriver
             throw new InvalidOperationException(
                 "settled attempt has no complete outcome");
         }
-
-        sink.WriteStep(
-            new StepRecord(
-                runId,
-                completedInputs,
-                attemptInput,
-                attemptAccepted,
-                attemptMovementScheduled,
-                settleFrames,
-                false,
-                capture));
-        stableState = attemptState;
-        ClearAttemptAfterStep();
-        completedInputs++;
-
-        if (TerminalSelected())
-            return;
-        if (completedInputs == expectedInputCount)
+        if (!TryAcquireOutputLease())
         {
-            FinishExpectedInputCount(utcNow);
+            ClearAttemptAfterTerminalReturn();
             return;
         }
 
+        bool traceIoFailure = false;
         try
         {
-            reporter.Ready(completedInputs);
+            try
+            {
+                sink.WriteStep(
+                    new StepRecord(
+                        runId,
+                        completedInputs,
+                        attemptInput,
+                        attemptAccepted,
+                        attemptMovementScheduled,
+                        settleFrames,
+                        false,
+                        capture));
+            }
+            catch (TraceIoException)
+            {
+                traceIoFailure = true;
+                SelectTraceIoFailure();
+                throw;
+            }
+
+            StepContinuation continuation =
+                SelectDurableStepContinuation(utcNow);
+            if (continuation == StepContinuation.Complete)
+            {
+                FinishExpectedInputCount(utcNow);
+            }
+            else if (continuation == StepContinuation.Ready)
+            {
+                try
+                {
+                    reporter.Ready(completedInputs);
+                }
+                catch (Exception)
+                {
+                    TryFaultInternal(
+                        "observer_exception", FaultRequest.Derived());
+                }
+            }
         }
-        catch (Exception)
+        finally
         {
-            TryFaultInternal(
-                "observer_exception", FaultRequest.Derived());
+            ReleaseOutputLease(traceIoFailure);
         }
     }
+
+    private StepContinuation SelectDurableStepContinuation(
+        DateTime utcNow)
+    {
+        lock (outputLeaseSync)
+        {
+            stableState = attemptState;
+            ClearAttemptAfterStep();
+            completedInputs++;
+            if (TerminalSelected()
+                || Read(ref disposed) != 0
+                || Read(ref disabled) != 0)
+            {
+                return StepContinuation.None;
+            }
+            if (completedInputs == expectedInputCount)
+            {
+                return TryClaimExpectedInputCompletion(utcNow)
+                    ? StepContinuation.Complete
+                    : StepContinuation.None;
+            }
+            return StepContinuation.Ready;
+        }
+    }
+
+    private void ClearAttemptAfterTerminalReturn()
+    {
+        currentFrames = 0;
+        neutralSeen = false;
+        candidateSignature = null;
+        lastCapture = null;
+        ClearAttemptFields();
+    }
 }
~~~
<!-- TASK5-PATCH-END:C53C1-PRODUCTION -->

The C53C1 tests-only forced build must succeed. The no-build `driver-terminal` run must exit `1`, emit exactly one cohort-failure line, and first fail exactly:

```text
cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: fault Close waits for active Run output
```

The correction must cover Run, Initial, Ready(0), intermediate Step/Ready, final Step/End/Complete, Step failure, Error/Close failure, Dispose, and late callbacks with deterministic entry/release barriers rather than timing-only sleeps.

C53C1 is not the final accepted correction. Synthetic qualification produced the
`C53C1-STALE-QUEUED-ERROR-INDEX` hypothesis: an overlapping successful Step
could leave a queued ordinary Error with stale `input_index=N` although the
flushed-step parser position had advanced to `N+1`. Preserve C53C1 unchanged;
future blind reviewers derive and seal the actual disposition before C53C2 may
proceed.

### C53C2 patches

**C53C2-TESTS patch:** SHA-256 `175d83ab045a264e76f537b5c4d94ea3f945ac874bf7caa6417de2183976ece1`; 190 LF lines; 7397 bytes.
<!-- TASK5-PATCH-BEGIN:C53C2-TESTS -->
~~~diff
diff --git a/oracle/plugin/tests/PassiveDriverTerminalTests.cs b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
index 1387c3685204d73e7dee077e232f87fdcb2d6e0f..60a8a94fd8d0603b861fb7ccf80a7d20d1697d59 100644
--- a/oracle/plugin/tests/PassiveDriverTerminalTests.cs
+++ b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
@@ -90,7 +90,7 @@ internal static class PassiveDriverTerminalTests
             offending.State, 0, 1.0);
         offending.Driver.PlayerPollReturned(offendingPoll);
         AssertError(
-            offending.Sink.ErrorRecords[0],
+            offending,
             "input_before_initial",
             0,
             OracleInput.North,
@@ -102,7 +102,7 @@ internal static class PassiveDriverTerminalTests
         unknown.Driver.PhysicalPollReturned(77);
         unknown.Driver.PlayerPollReturned(unknownPoll);
         AssertError(
-            unknown.Sink.ErrorRecords[0],
+            unknown,
             "unexpected_input",
             0,
             null,
@@ -120,7 +120,7 @@ internal static class PassiveDriverTerminalTests
             ProtocolSamples.MovedCapture);
         pending.Driver.TryFault("settle_timeout");
         AssertError(
-            pending.Sink.ErrorRecords[0],
+            pending,
             "settle_timeout",
             0,
             OracleInput.West,
@@ -137,7 +137,7 @@ internal static class PassiveDriverTerminalTests
         pendingUnknown.Driver.PhysicalPollReturned(77);
         pendingUnknown.Driver.PlayerPollReturned(pendingUnknownPoll);
         AssertError(
-            pendingUnknown.Sink.ErrorRecords[0],
+            pendingUnknown,
             "unexpected_input",
             0,
             OracleInput.West,
@@ -155,7 +155,7 @@ internal static class PassiveDriverTerminalTests
         HookToken restartToken = restart.Driver.RestartEntered();
         restart.Driver.RestartReturned(restartToken);
         AssertError(
-            restart.Sink.ErrorRecords[0],
+            restart,
             "unexpected_input",
             null,
             null,
@@ -171,7 +171,7 @@ internal static class PassiveDriverTerminalTests
             ProtocolSamples.InitialCapture);
         initial.Driver.TryFault("observer_exception");
         AssertError(
-            initial.Sink.ErrorRecords[0],
+            initial,
             "observer_exception",
             null,
             null,
@@ -181,7 +181,7 @@ internal static class PassiveDriverTerminalTests
         DriverFixture generic = DriverFixture.Ready();
         generic.Driver.TryFault("observer_exception");
         AssertError(
-            generic.Sink.ErrorRecords[0],
+            generic,
             "observer_exception",
             null,
             null,
@@ -212,7 +212,7 @@ internal static class PassiveDriverTerminalTests
         Check.Equal(0, earlyUtc.Reporter.CompleteCalls,
             "invalid final UTC emits no Complete");
         AssertError(
-            earlyUtc.Sink.ErrorRecords[0],
+            earlyUtc,
             "observer_exception",
             null,
             null,
@@ -650,7 +650,7 @@ internal static class PassiveDriverTerminalTests
         Check.Sequence(new int[0], fixture.Reporter.ReadyValues,
             "fault during Initial suppresses Ready(0)");
         AssertError(
-            fixture.Sink.ErrorRecords[0],
+            fixture,
             "capture_failed",
             null,
             null,
@@ -775,7 +775,7 @@ internal static class PassiveDriverTerminalTests
             fixture.Reporter.ReadyValues,
             "leased Ready(0) completes before its fault");
         AssertError(
-            fixture.Sink.ErrorRecords[0],
+            fixture,
             "observer_exception",
             null,
             null,
@@ -1058,7 +1058,7 @@ internal static class PassiveDriverTerminalTests
             fixture.Reporter.ReadyValues,
             "leased Ready completes before its separate fault");
         AssertError(
-            fixture.Sink.ErrorRecords[0],
+            fixture,
             "observer_exception",
             null,
             null,
@@ -1191,16 +1191,14 @@ internal static class PassiveDriverTerminalTests
         Check.Sequence(new int[] { 0 }, fixture.Reporter.ReadyValues,
             "intermediate fault suppresses Ready(1)");
         AssertError(
-            fixture.Sink.ErrorRecords[0],
+            fixture,
             "capture_failed",
+            null,
+            null,
             0,
-            OracleInput.West,
-            2,
-            "intermediate handoff preserves pending Error fields");
-        Check.Same(
-            ProtocolSamples.MovedCapture,
-            fixture.Sink.ErrorRecords[0].LastCapture,
-            "intermediate handoff preserves last capture");
+            "intermediate handoff clears durable attempt fields");
+        Check.True(fixture.Sink.ErrorRecords[0].LastCapture == null,
+            "intermediate handoff clears last capture");
         Check.Sequence(
             new string[]
             {
@@ -1319,11 +1317,11 @@ internal static class PassiveDriverTerminalTests
                 CanonicalJson.EncodeStep(ProtocolSamples.Step2),
                 CanonicalJson.EncodeError(new ErrorRecord(
                     ProtocolSamples.RunId,
-                    2,
-                    OracleInput.Undo,
+                    null,
+                    null,
                     "capture_failed",
-                    2,
-                    ProtocolSamples.InitialCapture)),
+                    0,
+                    null)),
                 "real Step remains durable before deferred Error");
         }
     }
@@ -1584,16 +1582,14 @@ internal static class PassiveDriverTerminalTests
             fixture.Reporter.ReadyValues,
             "terminal fault suppresses Ready(3)");
         AssertError(
-            fixture.Sink.ErrorRecords[0],
+            fixture,
             "capture_failed",
-            2,
-            OracleInput.Undo,
-            2,
-            "terminal handoff preserves pending Error fields");
-        Check.Same(
-            ProtocolSamples.InitialCapture,
-            fixture.Sink.ErrorRecords[0].LastCapture,
-            "terminal handoff preserves last capture");
+            null,
+            null,
+            0,
+            "terminal handoff clears durable attempt fields");
+        Check.True(fixture.Sink.ErrorRecords[0].LastCapture == null,
+            "terminal handoff clears last capture");
         Check.Sequence(
             new string[]
             {
@@ -2340,13 +2336,22 @@ internal static class PassiveDriverTerminalTests
     }
 
     private static void AssertError(
-        ErrorRecord error,
+        DriverFixture fixture,
         string code,
         int? inputIndex,
         OracleInput? input,
         int frames,
         string label)
     {
+        Check.Equal(1, fixture.Sink.ErrorRecords.Count,
+            label + " Error count");
+        ErrorRecord error = fixture.Sink.ErrorRecords[0];
+        if (error.InputIndex.HasValue)
+        {
+            Check.Equal(fixture.Sink.StepRecords.Count,
+                error.InputIndex.Value,
+                label + " parser position");
+        }
         Check.Equal(code, error.Code, label + " code");
         Check.Equal(inputIndex, error.InputIndex, label + " input index");
         Check.Equal(input, error.Input, label + " input");
~~~
<!-- TASK5-PATCH-END:C53C2-TESTS -->

**C53C2-PRODUCTION patch:** SHA-256 `0ee216ead3ab2bd602bbcd42aa67eda31943f55db558250288452b785053354e`; 23 LF lines; 1011 bytes.
<!-- TASK5-PATCH-BEGIN:C53C2-PRODUCTION -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 88951007d1f25df778c025009c0b1d23cd6645ef..4bd5d0ba1200e3971416e361407fa5eac2efd0b4 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -295,6 +295,18 @@ internal sealed partial class PassiveDriver
             stableState = attemptState;
             ClearAttemptAfterStep();
             completedInputs++;
+            if (deferredTerminalWork != null
+                && deferredTerminalWork.Kind
+                    == TerminalWorkKind.OrdinaryFault)
+            {
+                deferredTerminalWork.Error = new ErrorRecord(
+                    runId,
+                    null,
+                    null,
+                    deferredTerminalWork.Code,
+                    0,
+                    null);
+            }
             if (TerminalSelected()
                 || Read(ref disposed) != 0
                 || Read(ref disabled) != 0)
~~~
<!-- TASK5-PATCH-END:C53C2-PRODUCTION -->

The C53C2 tests-only forced build must succeed. The no-build `driver-terminal` run must exit `1`, emit exactly one cohort-failure line, and first fail exactly:

```text
cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: real Step remains durable before deferred Error second line
```

The production patch may add only the post-durable-Step deferred ordinary Error rebuild described in Stable Interfaces. It must leave Step TraceIo marker-only behavior unchanged.

## Mutations

The final Task 5 mutation catalog is T5M01 through T5M28. Each row must declare: exact clean parent commit/tree; patch SHA-256/lines/bytes; target file parent SHA-256/blob; target function; one semantic; mutated file SHA-256/blob; mutated tree; forced-build log/status; selected frozen registration; unique first-failure fragment; RED log/status; exact reverse restoration; restored-build log/status; and fresh focused GREEN log/status.

### Task 5 mutation catalog A — T5M01–T5M17

## Provenance and future gate

Qualification baseline: scratch HEAD `bab6c1c1970fea0623fe957e3c006668513fe3c7`, root tree `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`, stable `oracle/plugin` subtree `5a7db9d1e661dd97bd6a939d375dd2008506f679`. The scratch root and per-mutant root trees below are provenance only: the future branch also tracks the Task 5 plan. At execution, bind the actual final Task 5.3 commit/tree, require clean HEAD/index/worktree and exact clean plugin subtree `5a7db9d1e661dd97bd6a939d375dd2008506f679`, apply one mutant with `git apply --index`, require its exact target SHA/blob and stable mutated plugin subtree, and record the future branch's computed full mutated tree. Reverse the same bytes with `git apply --reverse --index`; require the actual final tree, clean plugin subtree, clean status, and restored target SHA/blob.

Every canonical qualification had: one successful forced net10 `Rebuild` with `--no-restore`, warnings as errors, `-m:1`, and shared compilation disabled; RED status bytes exactly `31 0a` (`1\n`); exactly one `cohort ...` failure line, equal to the line catalogued below; exact reversal to root `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16` and plugin `5a7db9d1e661dd97bd6a939d375dd2008506f679`; then a fresh successful forced rebuild and focused GREEN. Every GREEN was `SSR oracle unit harness ready\n`, one line / 30 bytes, SHA-256 `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc`. Mutants are never committed. T5M15 is transient inherited-behavior testing, not authority to change `PassiveDriverBoundaries.cs` in Task 5.

## Exact identities

| ID | Target file / function and semantic | Patch SHA-256; lines / bytes | Parent/restored target SHA-256 / blob | Mutated target SHA-256 / blob | Qualified root / stable mutated plugin subtree |
|---|---|---|---|---|---|
| T5M01 | `oracle/plugin/Core/PassiveDriverInput.cs` / `ProcessInputEntered` — invert exact cardinal correlation | `d1933eadca9505e3d105db334b613be4e89196263498e8b96be05f89439acbbf`; 13 / 633 | `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` / `4bd5d0ba1200e3971416e361407fa5eac2efd0b4` | `d60603b1155a876f3d9a6563e3b2b45507e7970bbd4347ec11701b6b6cfe0b59` / `f0fd7de8497651011c25cee8b290adbc14119193` | `0a133da9ed2f330aff65843127fbd731e41cdb35` / `07e64d70a4eaa7598c6867d0369297a8d28e16e3` |
| T5M02 | `oracle/plugin/Core/PassiveDriver.cs` / `PhysicalPollReturned` — retain the candidate after a later cardinal poll | `b7f2c2ca8cff261303f8d8805336d4536a0c5bc5cec6338128386c4d82feec2a`; 12 / 576 | `093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130` / `b132f89b321345452901faab870ea0d642b93e06` | `ebc3af64300acbcf0d80a62c4b4fc435fbea232fc95ce8629c002ca8a0cfc955` / `3e03edfc9b189c5a52f4fc6df9352dd5c79eb646` | `34c1f471051aceadd16a34254a51ead052951dfa` / `31095186dbca4342471acd1f9f2582deacd7cf4c` |
| T5M03 | `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs` / `StateSetEntered` — retain epoch identity rather than hook-entry identity | `b426eb4706f9c4613f470c318d01e6ace393b4e77a16467a4de85f64013d956c`; 13 / 580 | `c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002` / `d4f1b49e8680676cd6b632390aa337dd58799d70` | `45c4cad51bf9e59b348c89ecfedf7bdc755ae7006a34d89226de334263c2573c` / `dbf219c18858e4bbeb779bd4490994067f0da35a` | `9da1959f7827903f5fb7bedc881bf2ed2d57bca4` / `0f3b231e673dd9f6f23045e5052a0a6c0ef9f681` |
| T5M04 | `oracle/plugin/Core/PassiveDriverInput.cs` / `EmitSettledAttempt` — report Ready before the durable Step | `048481433a1cfa640f44b73d829e98fcff1f3203255f472d8cca791eb5116e88`; 35 / 1309 | `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` / `4bd5d0ba1200e3971416e361407fa5eac2efd0b4` | `3c678f1838795178110ddc5a404ebae17cac7ca69fcc9aeec47ba92fa4c2b949` / `8ee91c0db2fcef803f5a9d996e57274d2b9b0f72` | `c2cd5a05e16277a3fafc69f6fa86d58aef3f9826` / `31693c7b3bd2e16ff929b3fe376c7e9ffd9577c0` |
| T5M05 | `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs` / `RestartEntered` — establish restart depth after fault selection | `a936e9ab5183511dc144c127a7ab5bbbdd77f0a9dee3ccbce5cfdaa1f403defe`; 19 / 703 | `c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002` / `d4f1b49e8680676cd6b632390aa337dd58799d70` | `6236fb28b0b7b700dd81de0482b89648d47b3014299167d30034c89bfda4b154` / `d20928e7addd3232a3b3f592e7d2898c0f6d43af` | `f9e7f696c7ca438c70d875469583868c1a4d76e7` / `be51e9487a94a8a73b1fbc99d324a28d227a1d0e` |
| T5M06 | `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs` / `StateSetEntered` — observe requested state rather than actual before-state | `cc764023239a341d5f1a830e74e2a281b0ee1a81ada1515d265fa8b4780cce57`; 13 / 584 | `c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002` / `d4f1b49e8680676cd6b632390aa337dd58799d70` | `e3d6348f60b0e2b421ad54cae8f79e4b5dce268122356a8f10295c31d92f2225` / `811a5fb252b3cecd96d2980d521d8721a8a753b9` | `afa24b28477b9caf975923e73d75a5ba05094787` / `1203a31914327f89e93f38dae930a2cea9ebb970` |
| T5M07 | `oracle/plugin/Core/PassiveDriverInput.cs` / `ProcessInputReturned` — inspect rather than consume a late typed token | `acd27cc07fe21b72108b26163d345bebc844c01c96b4464bffd5f1704b63a95e`; 16 / 736 | `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` / `4bd5d0ba1200e3971416e361407fa5eac2efd0b4` | `3b80cedb47d8ecd0933342dd09ac1fe80aa0f6b7ac4039f17316ae2783171dbc` / `f8649619a600ac26d1c4602ac7c105c6595b3f1e` | `6c1696a0947880fa35893f5c69ee0c0699579cad` / `fcc4ed7ede55c5850cac41ee3ed7eca64f708363` |
| T5M08 | `oracle/plugin/Core/PassiveDriverInput.cs` / `SelectDurableStepContinuation` — miss completion at the exact count | `3e334b7f4fe7ba1215bd89cac2de14085870a4487c80d4d33b9bd23336b56cd7`; 13 / 667 | `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` / `4bd5d0ba1200e3971416e361407fa5eac2efd0b4` | `6af76f1f9492c24e7c8499058b89f56d3e3bb4fdf828c53d847dc768be74fbd0` / `22c1535701d1388188e7a5e7d779f26c612dbe98` | `4f125bc15d67b865db6783908ff0acfd5dbb1091` / `9d3737ee6579614c0c6165ae7241b0fea923440c` |
| T5M09 | `oracle/plugin/Core/PassiveDriverCompletion.cs` / `TryClaimExpectedInputCompletion` / `FinishExpectedInputCount` — delay atomic success ownership | `068c96f07aac340876a269a8b9dd918dd0a31f54bde084516925da580693327c`; 27 / 1149 | `27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4` / `638d2882e988b17d686a7791604a497438e7d4e3` | `8b3aa73f949879014aa070a83a7d45e3fae220f5e02737d551ef77e7d86ee8fe` / `0f08b69e7046209bf671d0744ef9a90039943a33` | `658b9cf5f2cb1f0fe8efb775736f33593d864bb8` / `dfff42dc5930398730d63fd24a7d79df2d6fa723` |
| T5M10 | `oracle/plugin/Core/PassiveDriverInput.cs` / `EmitSettledAttempt` — turn Step trace-I/O failure into an ordinary fault | `87a1e87bb1581f621c2ed48e802bb1e45ee855da3dee5371047f1138a35434a4`; 15 / 644 | `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` / `4bd5d0ba1200e3971416e361407fa5eac2efd0b4` | `6753e731a1b8f22c049b00f23cb768749298e13a3fa8a9cb43526311c3a7d6b8` / `077c6da6a86fe0c11c483ebb7f1205f92b6d6940` | `b991e2a9208b657a6362c360e32f43b130f40291` / `d33672ff48210e9a47d044d9b95b66e9bd43deee` |
| T5M11 | `oracle/plugin/Core/PassiveDriverCompletion.cs` / `FinishExpectedInputCount` — continue after End/Close failure | `fdc867802747ac1153cbd3e94363b560d0218c9223e51c5f7716d8aa0bbdfec8`; 12 / 551 | `27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4` / `638d2882e988b17d686a7791604a497438e7d4e3` | `88075f592f0828f09c1068b07f163d68182c4b6d85204253281238fb4b5581d2` / `c2db4f7f4dbeb5845511b604b4d92012ae96ce77` | `803f0e74f422b552662b50c53911cb22474db56a` / `6c7744951d076122a2e421925cf3c908030e1fad` |
| T5M12 | `oracle/plugin/Core/PassiveDriverCompletion.cs` / `FinishExpectedInputCount` — route Complete failure through ordinary arbitration | `0b8c8184b2f15ed3a0c8984009dcfdb857458924a7fb82a99ebb0e612a34bc90`; 19 / 740 | `27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4` / `638d2882e988b17d686a7791604a497438e7d4e3` | `23e13d0131607c2e387e830d731f374cb319ccf85d6ef18cb404d87bf49573e4` / `e2c978c1c394c6bfdcf55f17585966542674d275` | `01ae359e74207af2836d7225a7792d9f0c3dfbcb` / `cf2cf8a6e0d9c74255f66d6bf6ca963f4aaa333b` |
| T5M13 | `oracle/plugin/Core/PassiveDriver.cs` / `CompleteUpdateCore` / `StartInitialEpoch` — retain a candidate across invalidation/rebase | `c2b718251cd91a10366dbd99c9a0cab10759db6c8ccb976a71326f31eb66bc7f`; 20 / 924 | `093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130` / `b132f89b321345452901faab870ea0d642b93e06` | `61839f2d1285a8a5e2ab0beac7ba63b60b55a1a0a2979d040e31b786971924f1` / `16390c2b8aaa9324bdbb75f89768f42768da75e9` | `2c9ab221eebf30c1cb4ce8c9572286775ae60561` / `2c9f42a62add99844c1c7cc2aa502b5d819ed56e` |
| T5M14 | `oracle/plugin/Core/PassiveDriver.cs` / `ValidateAndRememberCapture` — compare raw save rather than the complete signature | `b78d661029de14189be8864c12f9133d0924b347d49b4f0d6aef444fe512ccb5`; 14 / 654 | `093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130` / `b132f89b321345452901faab870ea0d642b93e06` | `59eebe420c07a851b702a07b5b2e23cfd33d3f2aed93f1b6e04f766b8ddbc6ff` / `24382e03d3c352a26e65408cf5b6f04ed38f3f54` | `1d64e1bce84c4011cf30bdcab0e04cf8553c29c3` / `228738c999afa6bb054c8225f4ee0d6943969e7a` |
| T5M15 | `oracle/plugin/Core/PassiveDriverBoundaries.cs` / `PassiveUpdateBoundary.Observe` — inspect/capture before authorization | `a7d7f2af440075e395346748d2ca9771c18dec8b052b9211131ff34964fa53bb`; 93 / 2879 | `1a130383302b315f43f8643fab5c13ec8d643727c2095ca21929aac306cdf133` / `b575724daf03cdf7d9a96722945a55ccd46a6e87` | `04b166764a03582ea8abaa83564e4402223d823000a36a7ae8aebcb4a13d9435` / `d2d8de03129cc90caa08d46b9ae8aebe3aa5f6c9` | `c0907e5c9da2694225670ac254d28b6c4b9a9774` / `fd750eb82dd3dd890e4caedadf130cf1cebd3983` |
| T5M16 | `oracle/plugin/Core/PassiveDriver.cs` / `BuildErrorRecord` — let a pending attempt defeat Restart's null override | `75c7af5e49cf50eef84382640ea9ab62c270948a6769a43538fd6c80ed3604bd`; 13 / 574 | `093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130` / `b132f89b321345452901faab870ea0d642b93e06` | `24a17a796b98bcacebd861ec460db6e9ef20d89b0f5bef25f224c917aa5e7471` / `8a0e556289e51803e368df04d34866437e7836a3` | `206bd99e8dbc7a64e3c93cefa57fa36f9168496d` / `c4a7e48a1a1fc218e2b07a68079ed387f783c19c` |
| T5M17 | `oracle/plugin/Core/PassiveDriverCompletion.cs` / `TryClaimExpectedInputCompletion` — reject UTC equal to run start | `be1da505f26c232382f0ec3ea686896cd7c3d17e9459dd6d53c4d241cfdbfed8`; 13 / 654 | `27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4` / `638d2882e988b17d686a7791604a497438e7d4e3` | `bf923b575cfac81d078c879bf929ab9066d2a73789bcf7c97147db144c5103dc` / `a75307c935e4cb91ccf4d2a4ecfb356a20d119ba` | `9e2d8a4a6bf2b00a413d784aa9f307b487f76344` / `377e166509a12db266fd7ec0e62bc6a8d958bbe4` |

## Exact kill oracles

| ID | Cohort / registration | Exact first failure line |
|---|---|---|
| T5M01 | `driver-input` / `all cardinals correlate` | `cohort 'driver-input', test 'all cardinals correlate': System.InvalidOperationException: cardinal opens attempt 0` |
| T5M02 | `driver-input` / `accepted and refused direction outcomes` | `cohort 'driver-input', test 'accepted and refused direction outcomes': System.InvalidOperationException: cardinal poll clears candidate` |
| T5M03 | `driver-input` / `state replacement and ClearThrew` | `cohort 'driver-input', test 'state replacement and ClearThrew': System.InvalidOperationException: hook identity preserves AwaitInitial frame count` |
| T5M04 | `driver-input` / `accepted and refused direction outcomes` | `cohort 'driver-input', test 'accepted and refused direction outcomes': System.InvalidOperationException: durable Step precedes progress marker at index 0` |
| T5M05 | `driver-input` / `restart depth and null fields` | `cohort 'driver-input', test 'restart depth and null fields': System.InvalidOperationException: reentrant Restart remains active after fault selection` |
| T5M06 | `driver-input` / `state replacement and ClearThrew` | `cohort 'driver-input', test 'state replacement and ClearThrew': System.InvalidOperationException: requested state is observational only` |
| T5M07 | `driver-input` / `state replacement and ClearThrew` | `cohort 'driver-input', test 'state replacement and ClearThrew': System.InvalidOperationException: disabled ProcessInput return consumes token once` |
| T5M08 | `driver-terminal` / `three steps End Close Complete order` | `cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: durable Step 2 must enter Done without Ready(3) and emit End Close Complete` |
| T5M09 | `driver-terminal` / `first fault wins race` | `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: success terminal owner rejects concurrent fault` |
| T5M10 | `driver-terminal` / `sink failure uses trace io marker` | `cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: Step 2 failure never attempts Error` |
| T5M11 | `driver-terminal` / `sink failure uses trace io marker` | `cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: End failure is marker-only phase` |
| T5M12 | `driver-terminal` / `completion reporter cannot rewrite trace` | `cohort 'driver-terminal', test 'completion reporter cannot rewrite trace': System.InvalidOperationException: Complete exception changes only in-memory phase` |
| T5M13 | `driver-initial` / `replacement rebases same callback` | `cohort 'driver-initial', test 'replacement rebases same callback': System.InvalidOperationException: replacement requires two fresh candidate captures` |
| T5M14 | `driver-initial` / `matching pair writes initial` | `cohort 'driver-initial', test 'matching pair writes initial': System.InvalidOperationException: same raw save with unequal complete signature does not settle` |
| T5M15 | `driver-initial` / `matching pair writes initial` | `cohort 'driver-initial', test 'matching pair writes initial': System.InvalidOperationException: authorization precedes gate inspection` |
| T5M16 | `driver-terminal` / `error field policy is exact` | `cohort 'driver-terminal', test 'error field policy is exact': System.InvalidOperationException: Restart overrides pending input fields input index` |
| T5M17 | `driver-terminal` / `three steps End Close Complete order` | `cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: UTC equal to started_at_utc is accepted` |

## Embedded exact canonical forward patches

Within each marker pair, the `diff` fence contains the complete canonical patch body. Materialize only those bytes with one final LF and recheck the catalogued SHA-256, line count, and byte count before applying.

<!-- BEGIN T5M01 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..f0fd7de8497651011c25cee8b290adbc14119193 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -46,7 +46,7 @@ internal sealed partial class PassiveDriver
 
         if (!playerPoll.SawPhysicalPoll
             || playerPoll.SawManualProcessInput
-            || playerPoll.RawDirection != rawDirection
+            || playerPoll.RawDirection == rawDirection
             || processInput != null)
         {
             TryFaultInternal(
~~~
<!-- END T5M01 CANONICAL PATCH -->

<!-- BEGIN T5M02 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..3e03edfc9b189c5a52f4fc6df9352dd5c79eb646 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -605,7 +605,6 @@ internal sealed partial class PassiveDriver : IDisposable
             || phase == PassivePhase.Settling)
         {
             neutralSeen = false;
-            candidateSignature = null;
         }
         OracleInput ignored;
         if (!TryMapCardinal(rawDirection, out ignored))
~~~
<!-- END T5M02 CANONICAL PATCH -->

<!-- BEGIN T5M03 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
index d4f1b49e8680676cd6b632390aa337dd58799d70..dbf219c18858e4bbeb779bd4490994067f0da35a 100644
--- a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
+++ b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
@@ -68,7 +68,7 @@ internal sealed partial class PassiveDriver
         stateSetContext = new StateSetContext
         {
             Id = token.Id,
-            Before = beforeState
+            Before = epochState
         };
         return token;
     }
~~~
<!-- END T5M03 CANONICAL PATCH -->

<!-- BEGIN T5M04 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..8ee91c0db2fcef803f5a9d996e57274d2b9b0f72 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -242,6 +242,20 @@ internal sealed partial class PassiveDriver
         bool traceIoFailure = false;
         try
         {
+            bool readyReportedEarly =
+                completedInputs + 1 < expectedInputCount;
+            if (readyReportedEarly)
+            {
+                try
+                {
+                    reporter.Ready(completedInputs + 1);
+                }
+                catch (Exception)
+                {
+                    TryFaultInternal(
+                        "observer_exception", FaultRequest.Derived());
+                }
+            }
             try
             {
                 sink.WriteStep(
@@ -268,7 +282,8 @@ internal sealed partial class PassiveDriver
             {
                 FinishExpectedInputCount(utcNow);
             }
-            else if (continuation == StepContinuation.Ready)
+            else if (continuation == StepContinuation.Ready
+                && !readyReportedEarly)
             {
                 try
                 {
~~~
<!-- END T5M04 CANONICAL PATCH -->

<!-- BEGIN T5M05 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
index d4f1b49e8680676cd6b632390aa337dd58799d70..d20928e7addd3232a3b3f592e7d2898c0f6d43af 100644
--- a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
+++ b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
@@ -24,13 +24,13 @@ internal sealed partial class PassiveDriver
         if (!token.Active)
             return token;
         restartContexts.Add(token.Id);
-        restartDepth++;
 
         if (!nested)
         {
             TryFaultInternal(
                 "unexpected_input", FaultRequest.Restart());
         }
+        restartDepth++;
         return token;
     }
 
~~~
<!-- END T5M05 CANONICAL PATCH -->

<!-- BEGIN T5M06 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
index d4f1b49e8680676cd6b632390aa337dd58799d70..811a5fb252b3cecd96d2980d521d8721a8a753b9 100644
--- a/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
+++ b/oracle/plugin/Core/PassiveDriverLifecycleHooks.cs
@@ -68,7 +68,7 @@ internal sealed partial class PassiveDriver
         stateSetContext = new StateSetContext
         {
             Id = token.Id,
-            Before = beforeState
+            Before = requestedState
         };
         return token;
     }
~~~
<!-- END T5M06 CANONICAL PATCH -->

<!-- BEGIN T5M07 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..f8649619a600ac26d1c4602ac7c105c6595b3f1e 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -77,7 +77,10 @@ internal sealed partial class PassiveDriver
     {
         if (!IsObservationActive())
         {
-            if (ConsumeLateToken(token, HookKind.ProcessInput)
+            if (token != null
+                && token.Active
+                && token.BelongsTo(this)
+                && token.Kind == HookKind.ProcessInput
                 && processInput != null
                 && processInput.Id == token.Id)
             {
~~~
<!-- END T5M07 CANONICAL PATCH -->

<!-- BEGIN T5M08 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..22c1535701d1388188e7a5e7d779f26c612dbe98 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -313,7 +313,7 @@ internal sealed partial class PassiveDriver
             {
                 return StepContinuation.None;
             }
-            if (completedInputs == expectedInputCount)
+            if (completedInputs > expectedInputCount)
             {
                 return TryClaimExpectedInputCompletion(utcNow)
                     ? StepContinuation.Complete
~~~
<!-- END T5M08 CANONICAL PATCH -->

<!-- BEGIN T5M09 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverCompletion.cs b/oracle/plugin/Core/PassiveDriverCompletion.cs
index 638d2882e988b17d686a7791604a497438e7d4e3..0f08b69e7046209bf671d0744ef9a90039943a33 100644
--- a/oracle/plugin/Core/PassiveDriverCompletion.cs
+++ b/oracle/plugin/Core/PassiveDriverCompletion.cs
@@ -18,10 +18,7 @@ internal sealed partial class PassiveDriver
             throw new InvalidOperationException(
                 "completion requires the expected input count");
         }
-        return Interlocked.CompareExchange(
-            ref terminalOwner,
-            SuccessTerminalOwner,
-            NoTerminalOwner) == NoTerminalOwner;
+        return true;
     }
 
     private void FinishExpectedInputCount(DateTime finishedAtUtc)
@@ -33,6 +30,10 @@ internal sealed partial class PassiveDriver
                     runId,
                     expectedInputCount,
                     finishedAtUtc));
+            Interlocked.CompareExchange(
+                ref terminalOwner,
+                SuccessTerminalOwner,
+                NoTerminalOwner);
             CloseSink();
         }
         catch (Exception error)
~~~
<!-- END T5M09 CANONICAL PATCH -->

<!-- BEGIN T5M10 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..077c6da6a86fe0c11c483ebb7f1205f92b6d6940 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -257,8 +257,8 @@ internal sealed partial class PassiveDriver
             }
             catch (TraceIoException)
             {
-                traceIoFailure = true;
-                SelectTraceIoFailure();
+                TryFaultInternal(
+                    "observer_exception", FaultRequest.Derived());
                 throw;
             }
 
~~~
<!-- END T5M10 CANONICAL PATCH -->

<!-- BEGIN T5M11 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverCompletion.cs b/oracle/plugin/Core/PassiveDriverCompletion.cs
index 638d2882e988b17d686a7791604a497438e7d4e3..c2db4f7f4dbeb5845511b604b4d92012ae96ce77 100644
--- a/oracle/plugin/Core/PassiveDriverCompletion.cs
+++ b/oracle/plugin/Core/PassiveDriverCompletion.cs
@@ -41,7 +41,6 @@ internal sealed partial class PassiveDriver
             SafeDiagnostic(error);
             BestEffortClose();
             SafeFailed("trace_io_failed");
-            return;
         }
 
         phase = PassivePhase.Done;
~~~
<!-- END T5M11 CANONICAL PATCH -->

<!-- BEGIN T5M12 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverCompletion.cs b/oracle/plugin/Core/PassiveDriverCompletion.cs
index 638d2882e988b17d686a7791604a497438e7d4e3..e2c978c1c394c6bfdcf55f17585966542674d275 100644
--- a/oracle/plugin/Core/PassiveDriverCompletion.cs
+++ b/oracle/plugin/Core/PassiveDriverCompletion.cs
@@ -49,11 +49,10 @@ internal sealed partial class PassiveDriver
         {
             reporter.Complete();
         }
-        catch (Exception error)
+        catch (Exception)
         {
-            phase = PassivePhase.Faulted;
-            SafeDiagnostic(error);
-            SafeFailed("observer_exception");
+            TryFaultInternal(
+                "observer_exception", FaultRequest.Derived());
         }
     }
 }
~~~
<!-- END T5M12 CANONICAL PATCH -->

<!-- BEGIN T5M13 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..16390c2b8aaa9324bdbb75f89768f42768da75e9 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -727,7 +727,6 @@ internal sealed partial class PassiveDriver : IDisposable
             if (directive.InspectGate)
                 throw new InvalidOperationException(
                     "eligible update was not inspected");
-            candidateSignature = null;
         }
         else if (sample.Kind == GateSampleKind.NonQuiescent)
         {
@@ -925,7 +924,6 @@ internal sealed partial class PassiveDriver : IDisposable
         epochStartedAt = nowSeconds;
         currentFrames = countCurrentUpdate ? 1 : 0;
         neutralSeen = false;
-        candidateSignature = null;
         lastCapture = null;
         ClearAttemptFields();
     }
~~~
<!-- END T5M13 CANONICAL PATCH -->

<!-- BEGIN T5M14 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..24382e03d3c352a26e65408cf5b6f04ed38f3f54 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -789,7 +789,8 @@ internal sealed partial class PassiveDriver : IDisposable
                     OracleProtocol.MaxSettleFrames,
                     capture));
         }
-        byte[] signature = CaptureSignature.Compute(capture);
+        byte[] signature =
+            CanonicalJson.StrictUtf8(capture.RawSave);
         lastCapture = capture;
         return signature;
     }
~~~
<!-- END T5M14 CANONICAL PATCH -->

<!-- BEGIN T5M15 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverBoundaries.cs b/oracle/plugin/Core/PassiveDriverBoundaries.cs
index b575724daf03cdf7d9a96722945a55ccd46a6e87..d2d8de03129cc90caa08d46b9ae8aebe3aa5f6c9 100644
--- a/oracle/plugin/Core/PassiveDriverBoundaries.cs
+++ b/oracle/plugin/Core/PassiveDriverBoundaries.cs
@@ -355,6 +355,33 @@ internal sealed class PassiveUpdateBoundary
             return;
         }
 
+        GateSample sample = null;
+        if (directive.InspectGate && verifiedUsable)
+        {
+            try
+            {
+                if (!observation.IsQuiescent(verifiedState))
+                {
+                    sample = GateSample.NonQuiescent();
+                }
+                else
+                {
+                    sample = GateSample.Captured(
+                        observation.Capture(verifiedState));
+                }
+            }
+            catch (CaptureException)
+            {
+                SafeFail(directive, "capture_failed");
+                return;
+            }
+            catch (Exception)
+            {
+                SafeFail(directive, "observer_exception");
+                return;
+            }
+        }
+
         bool authorized;
         try
         {
@@ -377,33 +404,35 @@ internal sealed class PassiveUpdateBoundary
         if (!authorized)
             return;
 
-        GateSample sample;
-        try
+        if (sample == null)
         {
-            if (!directive.InspectGate)
+            try
             {
-                sample = GateSample.NotInspected();
+                if (!directive.InspectGate)
+                {
+                    sample = GateSample.NotInspected();
+                }
+                else if (!observation.IsQuiescent(verifiedState))
+                {
+                    sample = GateSample.NonQuiescent();
+                }
+                else
+                {
+                    sample = GateSample.Captured(
+                        observation.Capture(verifiedState));
+                }
             }
-            else if (!observation.IsQuiescent(verifiedState))
+            catch (CaptureException)
             {
-                sample = GateSample.NonQuiescent();
+                SafeFail(directive, "capture_failed");
+                return;
             }
-            else
+            catch (Exception)
             {
-                sample = GateSample.Captured(
-                    observation.Capture(verifiedState));
+                SafeFail(directive, "observer_exception");
+                return;
             }
         }
-        catch (CaptureException)
-        {
-            SafeFail(directive, "capture_failed");
-            return;
-        }
-        catch (Exception)
-        {
-            SafeFail(directive, "observer_exception");
-            return;
-        }
 
         try
         {
~~~
<!-- END T5M15 CANONICAL PATCH -->

<!-- BEGIN T5M16 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..8a0e556289e51803e368df04d34866437e7836a3 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -1089,7 +1089,7 @@ internal sealed partial class PassiveDriver : IDisposable
     {
         int? inputIndex;
         OracleInput? input;
-        if (request.ForceNullInputs)
+        if (request.ForceNullInputs && !attemptPending)
         {
             inputIndex = null;
             input = null;
~~~
<!-- END T5M16 CANONICAL PATCH -->

<!-- BEGIN T5M17 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverCompletion.cs b/oracle/plugin/Core/PassiveDriverCompletion.cs
index 638d2882e988b17d686a7791604a497438e7d4e3..a75307c935e4cb91ccf4d2a4ecfb356a20d119ba 100644
--- a/oracle/plugin/Core/PassiveDriverCompletion.cs
+++ b/oracle/plugin/Core/PassiveDriverCompletion.cs
@@ -7,7 +7,7 @@ internal sealed partial class PassiveDriver
         DateTime finishedAtUtc)
     {
         OracleValidation.Utc(finishedAtUtc, "finishedAtUtc");
-        if (finishedAtUtc < startedAtUtc)
+        if (finishedAtUtc <= startedAtUtc)
         {
             throw new ArgumentOutOfRangeException(
                 "finishedAtUtc",
~~~
<!-- END T5M17 CANONICAL PATCH -->


### Task 5 mutation catalog B — T5M18–T5M28

## Future-lineage acceptance rule

The authenticated report below records qualification scratch HEAD `bab6c1c1970fea0623fe957e3c006668513fe3c7` and root tree `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`. Those full-root identities and each qualification-mutated full-root tree are provenance only: the future real branch also tracks the Task 5 plan. The future gate must capture its actual final Task 5.3 commit/root tree, require clean HEAD/index/worktree, and cross-lineage pin the clean `oracle/plugin` subtree to `5a7db9d1e661dd97bd6a939d375dd2008506f679`. After each canonical apply it must require the catalogued target SHA/blob and the corresponding stable mutated plugin subtree, record its freshly computed future full tree, then exact-reverse to its captured final tree, clean plugin subtree, restored target, and empty status before the fresh rebuild/GREEN.

Stable mutated `oracle/plugin` subtree IDs for T5M18–T5M28, in order: `733fc8babfb3ea8531b95a75508f06655778f444`, `df3d8b853557213996b4812fe9b9c7659928d84f`, `d413c11760f2ac1b1499208031757c7c933ed357`, `d3566afdf180e0d0c99b9d695b178ad88d8d6441`, `79eb88d8a946750228a8b0935a502cda62dc92ba`, `6e7433b3dc3504095445290dd02cdcb8cf1854d5`, `7efaf1fbefa97c06bc8a639b54710d8efd72b6a1`, `79e53b868a058bc8baa7bbdeb8e9ca2acba97274`, `a722ea76d89dffa6e856e86c0a8da51a6552363d`, `85642fb6f56ebf394004e248074c4d1110bb1483`, `449fab97552259bcae3adfeb68e87224f9a7734a`.

For the M28 Python proof, pin the imported primary-worktree source `src/ssr_env/oracle_protocol.py` to SHA-256/blob `9feab69eec050eea51670c9f80b00acba06799e500a4ed3502f02722d5ea7108` / `f390923533985d4b1595ea50f5dcf8119d1c1cca` and run the exact `$execution_root/.venv/bin/python` with `PYTHONPATH="$execution_root/src"` and `UV_OFFLINE=1`; reject an installed-package or clone-local import. The execution must materialize the embedded hook and qualified probe from committed P, perform the exact path-only transform below into a newly created runtime directory, and export the fresh trace there; no pre-existing qualification `/private/tmp` file is an input.

Use this exact Bash 3.2-compatible path-only transform after the qualified
probe fence has been materialized as
`$task5_artifact_dir/T5M28-qualified-stale-probe.py`. It refuses a non-fresh
runtime directory, proves that replacing the new path with the historical
literal recovers the qualified bytes exactly, records the transformed
SHA/line/byte identity, and checks that Python imports the pinned repository
source. The export-hook run must write
`$task5_m28_runtime/actual-clean-trace.ndjson` only after the pre-export
absence check; the transformed probe then consumes that freshly exported
file. Thus neither execution nor acceptance reads the historical directory.

~~~bash
set -eu

test -n "$execution_root"
test -n "$clone_root"
test -n "$task5_artifact_dir"
execution_root=$(cd "$execution_root" && pwd -P)
clone_root=$(cd "$clone_root" && pwd -P)
test "$execution_root" != "$clone_root"
test "$(git -C "$execution_root" rev-parse --show-toplevel)" = "$execution_root"
test "$(git -C "$clone_root" rev-parse --show-toplevel)" = "$clone_root"
task5_python="$execution_root/.venv/bin/python"
test -x "$task5_python"
task5_qualified_probe="$task5_artifact_dir/T5M28-qualified-stale-probe.py"
task5_qualified_probe_sha=0efd1cdcb2fef895c29d566512af85d86d31aa4cf247e338af912d6de24b04c8
task5_old_m28_path=/private/tmp/ssr-t5m18-28.nRkx7h/evidence-c/M28

test "$(shasum -a 256 "$task5_qualified_probe" | awk '{print $1}')" \
    = "$task5_qualified_probe_sha"
test "$(wc -l < "$task5_qualified_probe" | tr -d ' ')" = 33
test "$(wc -c < "$task5_qualified_probe" | tr -d ' ')" = 1142
test "$(awk -v needle="$task5_old_m28_path" \
    'index($0, needle) { count++ } END { print count + 0 }' \
    "$task5_qualified_probe")" = 1

task5_m28_runtime="$task5_artifact_dir/runtime"
test ! -e "$task5_m28_runtime"
test ! -L "$task5_m28_runtime"
mkdir -m 700 "$task5_m28_runtime"
test -d "$task5_m28_runtime"
test ! -L "$task5_m28_runtime"
test "$(stat -f '%Lp' "$task5_m28_runtime")" = 700
test "$(stat -f '%u' "$task5_m28_runtime")" = "$(id -u)"
test "$(cd "$task5_m28_runtime/.." && pwd -P)" = "$task5_artifact_dir"
test -z "$(find "$task5_m28_runtime" -mindepth 1 -print -quit)"
task5_transformed_probe="$task5_m28_runtime/stale_probe.py"
sed "s#$task5_old_m28_path#$task5_m28_runtime#g" \
    "$task5_qualified_probe" > "$task5_transformed_probe"
test "$(wc -l < "$task5_transformed_probe" | tr -d ' ')" = 33
test "$(awk -v needle="$task5_old_m28_path" \
    'index($0, needle) { count++ } END { print count + 0 }' \
    "$task5_transformed_probe")" = 0

task5_probe_roundtrip="$task5_m28_runtime/stale_probe.roundtrip.py"
sed "s#$task5_m28_runtime#$task5_old_m28_path#g" \
    "$task5_transformed_probe" > "$task5_probe_roundtrip"
cmp -s "$task5_qualified_probe" "$task5_probe_roundtrip"

task5_transformed_sha=$(shasum -a 256 "$task5_transformed_probe" |
    awk '{print $1}')
task5_transformed_lines=$(wc -l < "$task5_transformed_probe" | tr -d ' ')
task5_transformed_bytes=$(wc -c < "$task5_transformed_probe" | tr -d ' ')
printf '%s|%s|%s|%s\n' \
    T5M28 "$task5_transformed_sha" "$task5_transformed_lines" \
    "$task5_transformed_bytes" \
    > "$task5_artifact_dir/T5M28-transformed-probe.identity"

test ! -e "$task5_m28_runtime/actual-clean-trace.ndjson"
test "$(shasum -a 256 \
    "$execution_root/src/ssr_env/oracle_protocol.py" | awk '{print $1}')" \
    = 9feab69eec050eea51670c9f80b00acba06799e500a4ed3502f02722d5ea7108
test "$(git hash-object \
    "$execution_root/src/ssr_env/oracle_protocol.py")" \
    = f390923533985d4b1595ea50f5dcf8119d1c1cca
task5_imported_protocol=$(
    cd "$execution_root"
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$execution_root/src" UV_OFFLINE=1 \
    "$task5_python" -c \
    'from pathlib import Path; import ssr_env.oracle_protocol as p; print(Path(p.__file__).resolve())'
)
test "$task5_imported_protocol" \
    = "$execution_root/src/ssr_env/oracle_protocol.py"

# In clone_root, apply the embedded export hook and run the focused cohort with:
# SSR_T5M28_TRACE_PROBE="$task5_m28_runtime/actual-clean-trace.ndjson"
# Exact-reverse the hook, authenticate the restored checkpoint, then run:
# (cd "$execution_root" && PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 \
#     PYTHONPATH="$execution_root/src" "$task5_python" "$task5_transformed_probe")
~~~

## Authenticated aggregate tables and evidence

# Correction-critical Task 5 mutation qualification — T5M18–T5M28

## Verdict

PASS. All eleven canonical mutations are valid, killed, one-semantic, and mutually non-redundant. Each exact forward patch was derived from clean tip `bab6c1c1970fea0623fe957e3c006668513fe3c7`, received exactly one successful forced canonical-mutant net10 rebuild, produced status `1\n` and its unique catalogued first failure in the narrow `driver-terminal` cohort, was exactly reversed, restored the clean parent, received a fresh forced restored rebuild, and passed a focused GREEN. No canonical mutation changed a test/registration, no such change survives, and no commit was made. T5M28's temporary, exactly reversed test-only trace-export hook is disclosed in its dedicated proof below.

Two non-canonical derivations are retained and excluded: T5M20's rejected-scope compile failure and T5M23's rejected-broad handoff deletion.

## Authenticated parent and commands

- Parent HEAD / parent tree: `bab6c1c1970fea0623fe957e3c006668513fe3c7` / `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`.
- Driver parent SHA-256 / blob: `093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130` / `b132f89b321345452901faab870ea0d642b93e06`.
- Input parent SHA-256 / blob: `4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128` / `4bd5d0ba1200e3971416e361407fa5eac2efd0b4`.
- Terminal-test parent/restored SHA-256 / blob: `cc3001bee5c239b1a1e3c34fecafa3ad80c379e8c3b2c88b787dfaaae8d74bf9` / `60a8a94fd8d0603b861fb7ccf80a7d20d1697d59`.
- Unit csproj parent/restored SHA-256 / blob: `f8c5924d6e08cec8c08f7bafde2a5ef874d2bb17739cdfcf4f2b9924e51ff688` / `14df214f1e404fa584912ca6b7b074d75a3d3d73`.
- Forced build: `dotnet build oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false`.
- Narrow run: `dotnet run --project oracle/plugin/tests/SsrOracle.UnitTests.csproj --configuration Release --no-restore --no-build -- --cohort driver-terminal`.
- Canonical build logs are each `7` lines / `206` bytes and say `Build succeeded.`, `0 Warning(s)`, `0 Error(s)`. Every canonical status artifact is exactly two bytes, hex `31 0a` (`1\n`).

## Exact canonical mutations

`D` means the shared Driver parent above; `I` means the shared Input parent above. The linked patch is the exact full-index patch body, including its final LF.

| ID | Exact patch body | Patch SHA-256 / lines / bytes | Parent | Target function and one semantic | Mutated target SHA-256 / blob | Mutated tree |
|---|---|---|---|---|---|---|
| T5M18 | `evidence-a/T5M18/forward.patch` | `e3caa55377b3a6200973310f336c42bb786779e25db57b3a461c262fdc8f6434` / 62 / 1962 | D | `Prepare`: omit Run output-lease acquisition/release | `fee41934f82b2e79e2fa5a538edec2a7573a5c435c396055c8f77b7d88e695d4` / `1c4b058e273e0d301b4eab83bf966952d486f5f3` | `4b6802818dc780728f6c3029a52b9b66c709ea40` |
| T5M19 | `evidence-a/T5M19/forward.patch` | `a6f01ada63cba3c9aaf40a0d17afb3bbe0321b6617bfb13ce1dd704f3fcf994b` / 91 / 2854 | D | `EmitInitial`: omit Initial output-lease acquisition/release | `a7e7236bc3a7cb5eb0098da59caea33387db98e9f29df30e71eafe3e81bf7d68` / `048177cb176b26cbc40726c9fc230acd703eaa69` | `0503472b11bf6ecb46457ed67e4034454c69d1b0` |
| T5M20 | `evidence-a/T5M20/forward.patch` | `8e5617ac4385209efd55aa82342b597a52f1aa9485150701dd2862accf9a0335` / 56 / 1664 | D | `EmitInitial`: release the retained Initial lease before `Ready(0)`; hoist only the callback-decision local | `b5b717979aa7cb69d3db47b3a1ef1a86082fa9005489fb33a67ea26af7462acf` / `72b107730e71323398dece74736fc649568d5d08` | `e57ef04b3cdc7eec384b8c8b61ad9f60082139cb` |
| T5M21 | `evidence-a/T5M21/forward.patch` | `7bd93518c41f62bfb72cc254f7817e1c372801a14030a6833806c8bac1e0a61d` / 111 / 3553 | D | `TryFaultInternal`: eagerly execute terminal work only behind an active pending Settling Step; the unchanged terminal body is mechanically extracted so the Step lease remains held | `102d882993f8fb6d28ee330a051afad7e537b7c81820455c63cde8039a30abc4` / `3de91bff0cdc945a52ea17db94c41e6320280322` | `97e4a08c5ae5f4ea1231679b792a1a20e8d42ebd` |
| T5M22 | `evidence-b/M22/T5M22.patch` | `76bea7cc72c86a978a9329046a1b266eca62a27972e3f43aefc8974609b9f069` / 14 / 646 | I | `SelectDurableStepContinuation`: omit only terminal ownership from the intermediate-continuation gate | `2f8837686521350e94de0b74fad1f6a64c30eaff5bee88b832a1fe307b65cfe6` / `9d3bf10ac32c364c6c6aec7f22f3f2bad1b9889b` | `66169f1a63144bb525be25cb3f188084cf808da2` |
| T5M23 | `evidence-b/M23/T5M23.patch` | `9ce1757858a93e6581ad88f237445499976da102184f47e7e8432d3852dbc665` / 18 / 826 | I | `SelectDurableStepContinuation`: drop only a final-Step queued ordinary-fault handoff; preserve Initial/intermediate, TraceIo, and Dispose handoffs | `d9d3f1225e255a1f3ebc0b22be00f488d20f7b2c378f0129ce79cdc417d5f75c` / `ca3a175dc35d112158f7916fe94020e6469cd781` | `a780d9ff6993231e37677dac2e1dccc9eb803390` |
| T5M24 | `evidence-b/M24/T5M24.patch` | `c5bb317a2a4db15a02114a71554b2d994e9013489c044b4437c9a0df7b79100e` / 18 / 874 | D | `ReleaseOutputLease`: omit only the failing-Step override of queued ordinary fault by marker-only TraceIo work | `a9384bb75f6eb288da48b5cb3c32905efd9257c7f9bcff6ae9c17977d80010a7` / `7856883075bc08072784df9bcada1baeffbd6ba3` | `78ffd289e75a50b4e6d8001d4c5d67887a7293e5` |
| T5M25 | `evidence-b/M25/T5M25.patch` | `b7cceee7030a41131b9dfdcd1354c777d7f411457d069d28c0e60b36b42a1577` / 30 / 1248 | D | `Dispose`: close immediately only behind an active pending Step lease; Run/Initial still queue | `f4c34a2ab5e42835d9f329c14bf29e42de9a4706d46223cf3d6d1801b7d31c55` / `2d38882f466e6f1fd0b5b57b6928659ac23e1bec` | `11c07198e71ff6f3a78c04b8bbe2140a5c7430f0` |
| T5M26 | `evidence-c/M26/T5M26.patch` | `3ace6fa03b74e065b5d2106b04a391c0834747f0fda6c9ee38f531f5e085918f` / 17 / 751 | I | `SelectDurableStepContinuation`: allow only a disposed in-flight intermediate Step through the terminal/disabled continuation gate | `41c0b0a6bf29cc3b6c9c24c3d7d19aebcb3f04f4900b713e46944d30b4d7467e` / `73db8395f91cfcbcc168404f5fec5ba15866d4da` | `9c6d8f9f56d69be9b0ad102b12f36c601edd2899` |
| T5M27 | `evidence-c/M27/T5M27.patch` | `f25e9c2eab1030b3fdfeb7299787b2a53d47b1d2042362dce53251679933e4ca` / 28 / 1130 | D | `ExecuteTerminalWorkAndRelease`: on Error/Close exception, emit `trace_io_failed` before best-effort Close | `443832f608b86bc0d7522092e7710ffc0cd6ef76405f2ce41d0badc855d7e114` / `ba6378b817588ea19549d96ec143e8c0f1e5fd14` | `427a47933e77f6c3912ce3714a66aefe086e929a` |
| T5M28 | `evidence-c/M28/T5M28.patch` | `6787476f2830289a1e2660fd7e2bb299cabbd14ccd4bd9650df2cad0df0bd5a3` / 23 / 1011 | I | `SelectDurableStepContinuation`: delete only post-durable-Step rebasing, preserving the claim-time pre-Step Error snapshot | `283190a8d3097daa30b247881c01df96ef94400276897c76f872ed0adfdf616c` / `88951007d1f25df778c025009c0b1d23cd6645ef` | `b39ef4cebc10e7ecf4aa65849af3c4a60b2c722e` |

## Build, RED, and restored GREEN evidence

Build/test entries give `SHA-256 / lines / bytes`. Every mutated build exited `0`; every RED exited `1`; every restored build and GREEN exited `0`.

| ID | Mutated build | RED log | Registration | Restored build | Fresh GREEN |
|---|---|---|---|---|---|
| T5M18 | `39a3cb40053139ec79b6f4dc78cdaeda38c8d256faddcb073abec233e3e9bcb5` / 7 / 206 | `a8f10ba379dadfd006efe1c0c75adbe50c8fbbf7edba4944f6ad15f4048908fe` / 5 / 731 | `first fault wins race` | `1351660618efb522a2d4eb25aefbf606865092f6e8aa8b968c5f6313c10ed124` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M19 | `f6b1b111d907f9c9ad53aa87f136faf48a83130afab0026ff4b952e858424d70` / 7 / 206 | `15a89475afc5b321e9babe059b07ce9fca91bd8e6a5a1f0afa7b5ef00d17d9fc` / 5 / 733 | `first fault wins race` | `1c1f1af4f42c484b42c28341fe9278f1c24cb0eb5fb761bf98706b6ac78ec1bb` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M20 | `ccf588d76b8ac8f4c6246887ad45a60562d5f5f0111013345e63efc149d37cbb` / 7 / 206 | `73372eccb5b432ae44d532b721f6a3c8ab909f8115dd3401e2156a47f268c506` / 5 / 734 | `first fault wins race` | `aad8f60678c68c64f936cb389d262dd040f3f94230c2dae42fe0bd08b7a5be39` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M21 | `5fb8d885511014b530575a248e4171cce284d3e1264760b7ecdd7e0f84ead1a3` / 7 / 206 | `40122c023f9519b500750f6239b9347288399b135005a6b63c723e0039bbd7cb` / 5 / 747 | `first fault wins race` | `5b40641f3b3fb160c95fa6d9eae1fe49986ab18a3383c82fb2bcb9acb213f295` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M22 | `3422659a3d7e1832b188765ffc15781c16e6b5c650e55eaa560ccf7e627e871b` / 7 / 206 | `99ff2ef0831c34c103a96649215d36c5f2dc7860b3aea4151b07cb14e37fe60f` / 5 / 752 | `first fault wins race` | `0487d5ec641e77587c6d6ca6451a0ee0bbbc5ffe581e5f62c20f1f475d374cb0` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M23 | `3422659a3d7e1832b188765ffc15781c16e6b5c650e55eaa560ccf7e627e871b` / 7 / 206 | `3a033c288a50c68214aebbf7400fc3b57b42529c7b80b3d790fdaec58b795990` / 5 / 741 | `first fault wins race` | `e071311e203d4e02a773ca488b0f8a86122d0b3a62d875f22c93705f624dd4d0` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M24 | `f374f78bd25bd5f3b36a9787edbbcd22fb2bc0e2b9122259dbb8dcedc22fec23` / 7 / 206 | `48f9c4614225d8cf8a69b531ef9126f2b99fe1015011dc260edd96327f90b459` / 5 / 747 | `first fault wins race` | `f806d0fd5121d57fe1469279785a327b5e869e67883dcc2972a720aec834fe7a` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M25 | `be7af60dcc58d4dd096d1e8e86ba3d113d3a8c13b672aa14114bed6c1fcfa849` / 7 / 206 | `9ffe4c9dd9732b0474010c8e1d43940754c4fe1f6559e9cd92e444e497066d6c` / 5 / 763 | `Dispose and late callbacks are final` | `c3fd800543b86ffcd5cae48e6a26819a039b4f19aa45e9e2027a0448b78a73b4` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M26 | `6b4c46cfc95b4a1784d9a69fd2de84f01b0072baa2c5f698a0bb38862f8cdea3` / 7 / 206 | `1caffb23989645fbdb541cfb626768c0af514b3c098546e46a135891b745688c` / 5 / 781 | `Dispose and late callbacks are final` | `43f3efa2f6da48807a805a0bcecd4411b77b5b461061799357580cf3691095fa` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M27 | `13eb795600326d3dfa8d7cf19ac764d5baa27f831eb2ffba956c3269d0e1e2dc` / 7 / 206 | `b4002b9b7df001310b1631ea3e2a5e28938b39d58b0e3e5df3b7ce03fef7dae2` / 4 / 627 | `sink failure uses trace io marker` | `46c298a8bb01cbcb84c5a0e664a871ed0d331fe50fb515c6f4cb4f93bb1cc0ab` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |
| T5M28 | `50962174753db33e6b02fcdf422e99ace059dd4f1aed1844cea5f91241eb46e7` / 7 / 206 | `b7197b1f489323148d0b248ccfec122f703a17d9fa028d41992d6fcc686984f8` / 6 / 994 | `first fault wins race` | `ceff9b6529c047efe7337dafc7b51d0a9bd973fc3dacc74706cffd83d524d21c` | `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc` |

T5M22 and T5M23 have identical deterministic build-stdout hashes, but their patches, target blobs, trees, RED logs, and failure contracts differ; they are not redundant.

## Exact first failure lines

- T5M18: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: fault Close waits for active Run output`
- T5M19: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: Initial Error waits for active output`
- T5M20: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: Error waits for Ready(0) callback`
- T5M21: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: fault terminal trace waits for active Step output`
- T5M22: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: intermediate fault suppresses Ready(1)`
- T5M23: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: real trace closes once after deferred fault`
- T5M24: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: compromised Step suppresses queued Error attempt`
- T5M25: `cohort 'driver-terminal', test 'Dispose and late callbacks are final': System.InvalidOperationException: Dispose Close waits for in-flight Step`
- T5M26: `cohort 'driver-terminal', test 'Dispose and late callbacks are final': System.InvalidOperationException: disposed Step emits no Ready continuation`
- T5M27: `cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: Error write failure closes before trace I/O marker at index 1`
- T5M28: `cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: real Step remains durable before deferred Error second line`

Every line above is line 1 of its RED log and the only `cohort ...` failure line in that log. M24's registration is the only selection that required explicit reconciliation: `StepFailureOverridesQueuedFault` is invoked only by `FirstFaultWinsRace` at terminal-test line 413, and execution confirms that registration; no registration was edited.

## Exact restoration and independent replay

Each canonical patch was reversed with its own exact bytes. Per-mutant restoration recovered HEAD/tree `bab6c1c1970fea0623fe957e3c006668513fe3c7` / `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`, the relevant parent SHA-256/blob listed above, and clean status before its restored rebuild/GREEN.

An independent fresh-clone cached-index replay then applied and reversed T5M18 through T5M28 one at a time. Every apply touched exactly its declared production file, reproduced the table's target SHA-256/blob and mutated tree, passed patch checks, and reversed to tree `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`. There are 11 distinct patch hashes and 11 distinct mutated trees.

Final no-build `driver-terminal` GREEN runs in restored clones A, B, and C each exited `0` and produced one line, `SSR oracle unit harness ready`; each log SHA-256 is `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc`.

## T5M28 independent Python stale-trace proof

- A temporary test-only export hook was applied to clean clone C only: `evidence-c/M28/temporary-export-hook.patch`, SHA-256 `04e413ee1c486d60bdbfefe9033dd1232a19b4f2d46011f5a02d11d13dd6f8f7`, 26 lines / 1246 bytes.
- Its forced build exited `0` (`export-build.log` SHA-256 `0dc3fa184d9fe533f55e3abb4cfb5b8a2d49a3c91fc2185c557084230cb2a377`) and its focused run exited `0` (`export-test.log` SHA-256 `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc`). It freshly exported the clean real-sink trace `actual-clean-trace.ndjson`, SHA-256 `df50d409c3264ce12e33bab510fa7caf65a18cec1ddfa303fe57d04e46c1c577`, 6 lines / 2138 bytes.
- The hook was exactly reversed. The terminal test restored to SHA-256/blob `cc3001bee5c239b1a1e3c34fecafa3ad80c379e8c3b2c88b787dfaaae8d74bf9` / `60a8a94fd8d0603b861fb7ccf80a7d20d1697d59`, and its identifier is absent. A post-hook forced rebuild exited `0` (`export-restored-build.log` SHA-256 `3b25729cd4e6b1d3f4fd77b03c3d32687f3f71bdac433630d1a0092b4d0e4a6e`) and focused GREEN exited `0` (`export-restored-green.log` SHA-256 `541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc`).
- `stale_probe.py`, SHA-256 `0efd1cdcb2fef895c29d566512af85d86d31aa4cf247e338af912d6de24b04c8`, 33 lines / 1142 bytes, changed only the terminal Error to the claim-time Step-2 snapshot. The stale trace SHA-256 is `933657b5b7cca75860106a6cb99b3d43e1cd569b489733c781fda699db9911cf`, 6 lines / 2357 bytes.
- `PYTHONPATH=src python3 /private/tmp/ssr-t5m18-28.nRkx7h/evidence-c/M28/stale_probe.py` exited `0` and printed exactly `PASS stale trace rejected: error input_index must equal the flushed-step count`; log SHA-256 `992e6beb20c4e31aafea61fe528de5c542767a8c93e486c2680aab64920becdc`.

## Invalid/redundant accounting

- Canonical: 11 valid; 0 invalid; 0 redundant; all 11 killed.
- Rejected T5M20 scope candidate: `evidence-a/T5M20/rejected-forward-attempt1.patch`, SHA-256 `bd025237bc8baf67b95066f6e074c14dd3d1a4193ca2aa5794361848d0ec56d4`, 40 lines / 1214 bytes. It failed its only build with CS0103/CS0219, status `1`, 0 warnings / 2 errors, zero successful builds, and no test run. Build log SHA-256: `24c8e9e7258d6fc6d18bb0338e60d4c1ba07c2b017d02eafdf50e4c58786b485`. It was exactly reversed before canonical derivation.
- Rejected T5M23 broad candidate: `evidence-b/M23-rejected-broad/T5M23.patch`, SHA-256 `3ebacfe9b8f471e4e67770302a7e4728bb22d9ab2a9bced33a171b82f1299f4f`, 14 lines / 584 bytes. It compiled, but deleted every terminal handoff and first failed earlier in `sink failure uses trace io marker` at `Step 2 failure is marker-only Close count`, proving loss of queued TraceIo work. It is invalid for T5M23 and was exactly reversed before canonical derivation.

## Aggregate identities and final protection check

- Group reports: `evidence-a/report.md` SHA-256 `aa6e37c85a3f0c241ebc7016ade378234e729b65c9080e75276c42688a00e56b`; `evidence-b/report.md` `fcf60d65690db7220ebc22d428f58efd6aa8cd77048734c9e0f44b633afd91ca`; `evidence-c/report.md` `d216087500b655c235e184c4ea4484a28d11ebf978f2ec12124b8caee5530cdf`.
- Ordered canonical patch manifest: `canonical-patch-manifest.sha256`, 11 lines / 1039 bytes, SHA-256 `6aded89fb6211d219f647bcf74a89a876365cfd07dc8b8c154d64332fa6c81d9`.
- Ordered raw-byte concatenation of canonical T5M18…T5M28 patches: SHA-256 `d5261446b2f5cb33b205203da3ab495f000e0f279afa2337d0939275c85d1331`.
- Sorted 101-file evidence manifest: `evidence-manifest.sha256`, 101 lines / 9942 bytes, SHA-256 `1cc12eceac30cb22d1fd1f9dc97dd0f2be0a936edcf831abdbe8d3f3104ccdfd`.
- Ordered raw-byte concatenation of those same 101 evidence files in locale-C path order: combined evidence SHA-256 `1d60ab64a283a7c1f72c96cf5ce8f79a73f62c3b431894634accd49902a62824`.
- Clone A, B, and C final HEAD/index tree: `bab6c1c1970fea0623fe957e3c006668513fe3c7` / `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`; all clean, no commits.
- Protected primary scratch final HEAD/tree/index: `bab6c1c1970fea0623fe957e3c006668513fe3c7` / `a3bdcc8c48e19ed47eb58e30e5496cbff5ee2b16`; clean and untouched.
- The real worktree was never used for mutation, build, probe, restore, or edit. Its independent pre-existing HEAD is outside the correction scratch scope.

## Embedded exact canonical forward patches

Within each marker pair, the `diff` fence contains the complete canonical patch body. Materialize only those bytes with one final LF and recheck its report SHA-256, line count, and byte count before applying.

<!-- BEGIN T5M18 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..1c4b058e273e0d301b4eab83bf966952d486f5f3 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -265,40 +265,28 @@ internal sealed partial class PassiveDriver : IDisposable
         }
         if (Read(ref disposed) != 0 || Read(ref disabled) != 0)
             return false;
-        if (!TryAcquireOutputLease())
-            return false;
-
-        bool traceIoFailure = false;
         try
         {
-            try
-            {
-                sink.WriteRun(run);
-            }
-            catch (Exception error)
+            sink.WriteRun(run);
+        }
+        catch (Exception error)
+        {
+            SelectTraceIoFailure();
+            SafeDiagnostic(error);
+            return false;
+        }
+        lock (outputLeaseSync)
+        {
+            if (TerminalSelected()
+                || Read(ref disposed) != 0
+                || Read(ref disabled) != 0)
             {
-                traceIoFailure = true;
-                SelectTraceIoFailure();
-                SafeDiagnostic(error);
                 return false;
             }
-            lock (outputLeaseSync)
-            {
-                if (TerminalSelected()
-                    || Read(ref disposed) != 0
-                    || Read(ref disabled) != 0)
-                {
-                    return false;
-                }
-                runId = run.RunId;
-                startedAtUtc = run.StartedAtUtc;
-                Interlocked.Exchange(ref prepared, 1);
-                return true;
-            }
-        }
-        finally
-        {
-            ReleaseOutputLease(traceIoFailure);
+            runId = run.RunId;
+            startedAtUtc = run.StartedAtUtc;
+            Interlocked.Exchange(ref prepared, 1);
+            return true;
         }
     }
 
~~~
<!-- END T5M18 CANONICAL PATCH -->

<!-- BEGIN T5M19 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..048177cb176b26cbc40726c9fc230acd703eaa69 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -797,60 +797,45 @@ internal sealed partial class PassiveDriver : IDisposable
     private void EmitInitial(CaptureRecord capture)
     {
         InitialRecord record = new InitialRecord(runId, capture);
-        if (!TryAcquireOutputLease())
+        try
         {
-            ClearInitialAfterTerminalReturn();
-            return;
+            sink.WriteInitial(record);
+        }
+        catch (TraceIoException)
+        {
+            SelectTraceIoFailure();
+            throw;
         }
 
-        bool traceIoFailure = false;
-        try
+        bool emitReady = false;
+        lock (outputLeaseSync)
         {
-            try
+            if (TerminalSelected()
+                || Read(ref disposed) != 0
+                || Read(ref disabled) != 0)
             {
-                sink.WriteInitial(record);
+                ClearInitialAfterTerminalReturn();
             }
-            catch (TraceIoException)
+            else
             {
-                traceIoFailure = true;
-                SelectTraceIoFailure();
-                throw;
+                stableState = epochState;
+                phase = PassivePhase.Ready;
+                ClearInitialAfterTerminalReturn();
+                emitReady = true;
             }
-
-            bool emitReady = false;
-            lock (outputLeaseSync)
+        }
+        if (emitReady)
+        {
+            try
             {
-                if (TerminalSelected()
-                    || Read(ref disposed) != 0
-                    || Read(ref disabled) != 0)
-                {
-                    ClearInitialAfterTerminalReturn();
-                }
-                else
-                {
-                    stableState = epochState;
-                    phase = PassivePhase.Ready;
-                    ClearInitialAfterTerminalReturn();
-                    emitReady = true;
-                }
+                reporter.Ready(0);
             }
-            if (emitReady)
+            catch (Exception)
             {
-                try
-                {
-                    reporter.Ready(0);
-                }
-                catch (Exception)
-                {
-                    TryFaultInternal(
-                        "observer_exception", FaultRequest.Derived());
-                }
+                TryFaultInternal(
+                    "observer_exception", FaultRequest.Derived());
             }
         }
-        finally
-        {
-            ReleaseOutputLease(traceIoFailure);
-        }
     }
 
     private void ClearInitialAfterTerminalReturn()
~~~
<!-- END T5M19 CANONICAL PATCH -->

<!-- BEGIN T5M20 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..72b107730e71323398dece74736fc649568d5d08 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -804,6 +804,7 @@ internal sealed partial class PassiveDriver : IDisposable
         }
 
         bool traceIoFailure = false;
+        bool emitReady = false;
         try
         {
             try
@@ -817,7 +818,6 @@ internal sealed partial class PassiveDriver : IDisposable
                 throw;
             }
 
-            bool emitReady = false;
             lock (outputLeaseSync)
             {
                 if (TerminalSelected()
@@ -834,23 +834,23 @@ internal sealed partial class PassiveDriver : IDisposable
                     emitReady = true;
                 }
             }
-            if (emitReady)
-            {
-                try
-                {
-                    reporter.Ready(0);
-                }
-                catch (Exception)
-                {
-                    TryFaultInternal(
-                        "observer_exception", FaultRequest.Derived());
-                }
-            }
         }
         finally
         {
             ReleaseOutputLease(traceIoFailure);
         }
+        if (emitReady)
+        {
+            try
+            {
+                reporter.Ready(0);
+            }
+            catch (Exception)
+            {
+                TryFaultInternal(
+                    "observer_exception", FaultRequest.Derived());
+            }
+        }
     }
 
     private void ClearInitialAfterTerminalReturn()
~~~
<!-- END T5M20 CANONICAL PATCH -->

<!-- BEGIN T5M21 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..3de91bff0cdc945a52ea17db94c41e6320280322 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -1058,6 +1058,7 @@ internal sealed partial class PassiveDriver : IDisposable
         OracleErrors.ForCode(code);
         TerminalWork work = null;
         bool execute = false;
+        bool drainBehindActiveStep = false;
         lock (outputLeaseSync)
         {
             if (Interlocked.CompareExchange(
@@ -1075,10 +1076,25 @@ internal sealed partial class PassiveDriver : IDisposable
                 : TerminalWork.Ordinary(
                     code,
                     BuildErrorRecord(code, request, faultPhase));
-            execute = QueueOrAcquireOutputLeaseLocked(work);
+            if (outputLeaseActive
+                && attemptPending
+                && faultPhase == PassivePhase.Settling)
+            {
+                execute = true;
+                drainBehindActiveStep = true;
+            }
+            else
+            {
+                execute = QueueOrAcquireOutputLeaseLocked(work);
+            }
         }
         if (execute)
-            ExecuteTerminalWorkAndRelease(work);
+        {
+            if (drainBehindActiveStep)
+                ExecuteTerminalWork(work);
+            else
+                ExecuteTerminalWorkAndRelease(work);
+        }
         return true;
     }
 
@@ -1221,40 +1237,45 @@ internal sealed partial class PassiveDriver : IDisposable
     {
         try
         {
-            if (work.Kind == TerminalWorkKind.OrdinaryFault)
+            ExecuteTerminalWork(work);
+        }
+        finally
+        {
+            lock (outputLeaseSync)
             {
-                bool durable = false;
-                try
-                {
-                    sink.WriteError(work.Error);
-                    CloseSink();
-                    durable = true;
-                }
-                catch (Exception error)
-                {
-                    SafeDiagnostic(error);
-                    BestEffortClose();
-                }
-                SafeFailed(
-                    durable ? work.Code : "trace_io_failed");
+                outputLeaseActive = false;
             }
-            else if (work.Kind == TerminalWorkKind.TraceIoFailure)
+        }
+    }
+
+    private void ExecuteTerminalWork(TerminalWork work)
+    {
+        if (work.Kind == TerminalWorkKind.OrdinaryFault)
+        {
+            bool durable = false;
+            try
             {
-                phase = PassivePhase.Faulted;
-                BestEffortClose();
-                SafeFailed("trace_io_failed");
+                sink.WriteError(work.Error);
+                CloseSink();
+                durable = true;
             }
-            else
+            catch (Exception error)
             {
+                SafeDiagnostic(error);
                 BestEffortClose();
             }
+            SafeFailed(
+                durable ? work.Code : "trace_io_failed");
         }
-        finally
+        else if (work.Kind == TerminalWorkKind.TraceIoFailure)
         {
-            lock (outputLeaseSync)
-            {
-                outputLeaseActive = false;
-            }
+            phase = PassivePhase.Faulted;
+            BestEffortClose();
+            SafeFailed("trace_io_failed");
+        }
+        else
+        {
+            BestEffortClose();
         }
     }
 
~~~
<!-- END T5M21 CANONICAL PATCH -->

<!-- BEGIN T5M22 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..9d3bf10ac32c364c6c6aec7f22f3f2bad1b9889b 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -307,8 +307,7 @@ internal sealed partial class PassiveDriver
                     0,
                     null);
             }
-            if (TerminalSelected()
-                || Read(ref disposed) != 0
+            if (Read(ref disposed) != 0
                 || Read(ref disabled) != 0)
             {
                 return StepContinuation.None;
~~~
<!-- END T5M22 CANONICAL PATCH -->

<!-- BEGIN T5M23 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..ca3a175dc35d112158f7916fe94020e6469cd781 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -307,6 +307,13 @@ internal sealed partial class PassiveDriver
                     0,
                     null);
             }
+            if (completedInputs == expectedInputCount
+                && deferredTerminalWork != null
+                && deferredTerminalWork.Kind
+                    == TerminalWorkKind.OrdinaryFault)
+            {
+                deferredTerminalWork = null;
+            }
             if (TerminalSelected()
                 || Read(ref disposed) != 0
                 || Read(ref disabled) != 0)
~~~
<!-- END T5M23 CANONICAL PATCH -->

<!-- BEGIN T5M24 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..7856883075bc08072784df9bcada1baeffbd6ba3 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -1196,13 +1196,6 @@ internal sealed partial class PassiveDriver : IDisposable
             if (!outputLeaseActive)
                 throw new InvalidOperationException(
                     "output lease is not active");
-            if (traceIoFailure
-                && deferredTerminalWork != null
-                && deferredTerminalWork.Kind
-                    == TerminalWorkKind.OrdinaryFault)
-            {
-                deferredTerminalWork = TerminalWork.TraceIo();
-            }
             if (deferredTerminalWork == null)
             {
                 outputLeaseActive = false;
~~~
<!-- END T5M24 CANONICAL PATCH -->

<!-- BEGIN T5M25 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..2d38882f466e6f1fd0b5b57b6928659ac23e1bec 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -688,6 +688,7 @@ internal sealed partial class PassiveDriver : IDisposable
         Interlocked.Exchange(ref disabled, 1);
         TerminalWork work = null;
         bool execute = false;
+        bool closeImmediately = false;
         lock (outputLeaseSync)
         {
             if (Interlocked.CompareExchange(
@@ -696,10 +697,15 @@ internal sealed partial class PassiveDriver : IDisposable
                 NoTerminalOwner) == NoTerminalOwner)
             {
                 work = TerminalWork.DisposeOnly();
-                execute = QueueOrAcquireOutputLeaseLocked(work);
+                if (outputLeaseActive && attemptPending)
+                    closeImmediately = true;
+                else
+                    execute = QueueOrAcquireOutputLeaseLocked(work);
             }
         }
-        if (execute)
+        if (closeImmediately)
+            BestEffortClose();
+        else if (execute)
             ExecuteTerminalWorkAndRelease(work);
     }
 
~~~
<!-- END T5M25 CANONICAL PATCH -->

<!-- BEGIN T5M26 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..73db8395f91cfcbcc168404f5fec5ba15866d4da 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -307,9 +307,9 @@ internal sealed partial class PassiveDriver
                     0,
                     null);
             }
-            if (TerminalSelected()
-                || Read(ref disposed) != 0
-                || Read(ref disabled) != 0)
+            if (Read(ref disposed) == 0
+                && (TerminalSelected()
+                    || Read(ref disabled) != 0))
             {
                 return StepContinuation.None;
             }
~~~
<!-- END T5M26 CANONICAL PATCH -->

<!-- BEGIN T5M27 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..ba6378b817588ea19549d96ec143e8c0f1e5fd14 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -1223,20 +1223,19 @@ internal sealed partial class PassiveDriver : IDisposable
         {
             if (work.Kind == TerminalWorkKind.OrdinaryFault)
             {
-                bool durable = false;
                 try
                 {
                     sink.WriteError(work.Error);
                     CloseSink();
-                    durable = true;
                 }
                 catch (Exception error)
                 {
                     SafeDiagnostic(error);
+                    SafeFailed("trace_io_failed");
                     BestEffortClose();
+                    return;
                 }
-                SafeFailed(
-                    durable ? work.Code : "trace_io_failed");
+                SafeFailed(work.Code);
             }
             else if (work.Kind == TerminalWorkKind.TraceIoFailure)
             {
~~~
<!-- END T5M27 CANONICAL PATCH -->

<!-- BEGIN T5M28 CANONICAL PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriverInput.cs b/oracle/plugin/Core/PassiveDriverInput.cs
index 4bd5d0ba1200e3971416e361407fa5eac2efd0b4..88951007d1f25df778c025009c0b1d23cd6645ef 100644
--- a/oracle/plugin/Core/PassiveDriverInput.cs
+++ b/oracle/plugin/Core/PassiveDriverInput.cs
@@ -295,18 +295,6 @@ internal sealed partial class PassiveDriver
             stableState = attemptState;
             ClearAttemptAfterStep();
             completedInputs++;
-            if (deferredTerminalWork != null
-                && deferredTerminalWork.Kind
-                    == TerminalWorkKind.OrdinaryFault)
-            {
-                deferredTerminalWork.Error = new ErrorRecord(
-                    runId,
-                    null,
-                    null,
-                    deferredTerminalWork.Code,
-                    0,
-                    null);
-            }
             if (TerminalSelected()
                 || Read(ref disposed) != 0
                 || Read(ref disabled) != 0)
~~~
<!-- END T5M28 CANONICAL PATCH -->

## Embedded exact T5M28 proof artifacts

<!-- BEGIN T5M28 TEMPORARY EXPORT HOOK -->
~~~diff
diff --git a/oracle/plugin/tests/PassiveDriverTerminalTests.cs b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
index 60a8a94fd8d0603b861fb7ccf80a7d20d1697d59..0f057da9dd9fd4396404c2d3c4afcca4fafa98cf 100644
--- a/oracle/plugin/tests/PassiveDriverTerminalTests.cs
+++ b/oracle/plugin/tests/PassiveDriverTerminalTests.cs
@@ -1,5 +1,6 @@
 using System;
 using System.Collections.Generic;
+using System.IO;
 using System.Text;
 using System.Threading;
 
@@ -1312,8 +1313,13 @@ internal static class PassiveDriverTerminalTests
                 new string[] { "capture_failed" },
                 fixture.Reporter.FailedCodes,
                 "deferred fault retains its winning marker");
+            byte[] traceBytes = output.SnapshotBytes();
+            string probePath = Environment.GetEnvironmentVariable(
+                "SSR_T5M28_TRACE_PROBE");
+            if (!String.IsNullOrEmpty(probePath))
+                File.WriteAllBytes(probePath, traceBytes);
             AssertLastRealTraceLines(
-                output.SnapshotBytes(),
+                traceBytes,
                 CanonicalJson.EncodeStep(ProtocolSamples.Step2),
                 CanonicalJson.EncodeError(new ErrorRecord(
                     ProtocolSamples.RunId,
~~~
<!-- END T5M28 TEMPORARY EXPORT HOOK -->

<!-- BEGIN T5M28 QUALIFIED STALE PROBE -->
~~~python
import json
from pathlib import Path

from ssr_env.oracle_protocol import OracleProtocolError, read_oracle_trace_stream


evidence = Path("/private/tmp/ssr-t5m18-28.nRkx7h/evidence-c/M28")
actual = evidence / "actual-clean-trace.ndjson"
lines = actual.read_bytes().splitlines()
assert len(lines) == 6

step = json.loads(lines[-2])
error = json.loads(lines[-1])
assert step["kind"] == "step" and step["input_index"] == 2
assert error["kind"] == "error" and error["input_index"] is None

error["input_index"] = 2
error["input"] = "Undo"
error["settle_frames"] = 2
error["last_capture"] = step["capture"]
lines[-1] = json.dumps(error, separators=(",", ":")).encode("utf-8")
stale = evidence / "stale-claim-time-trace.ndjson"
stale.write_bytes(b"\n".join(lines) + b"\n")

expected = "error input_index must equal the flushed-step count"
try:
    with stale.open("rb") as stream:
        read_oracle_trace_stream(stream, source=str(stale))
except OracleProtocolError as caught:
    assert expected in str(caught)
    print(f"PASS stale trace rejected: {expected}")
else:
    raise AssertionError("claim-time pre-Step Error snapshot was accepted")
~~~
<!-- END T5M28 QUALIFIED STALE PROBE -->

Qualification rules:

- derive and run mutations only after C53C2 in disposable clones created with `git clone --no-hardlinks "$execution_root" clone-path` from the authenticated local worktree; reject a source containing a URL scheme, scp-like remote syntax, or a different resolved tip/tree;
- one mutant per clean clone state and never across a commit boundary;
- modify production only, never a test or registration;
- require exactly one successful forced mutated-tree net10 build before the intended nonzero focused run;
- require the catalogued registration and unique first-failure fragment to be the actual first failure;
- reverse the exact forward patch, authenticate parent tree/file/index/status, perform a fresh forced rebuild, and run a fresh focused GREEN;
- independently replay forward and reverse applicability against a fresh clone using read-only/cached-index checks;
- reject any compile-failing, multi-semantic, redundant, wrong-first-failure, or incompletely restored candidate; and
- store raw mutation evidence outside the repository and summarize only authenticated identities in R.

Retain two rejected candidates as non-canonical provenance:

- the rejected T5M20 scope attempt failed to compile with exactly CS0103 and CS0219, zero warnings and two errors; it received no test run and was reversed before the canonical T5M20 derivation;
- the rejected broad T5M23 removed every deferred terminal kind and first broke the independent TraceIo contract in `sink failure uses trace io marker`; it was reversed before the narrow canonical T5M23 derivation.

**REJECTED-T5M20-SCOPE patch:** SHA-256 `bd025237bc8baf67b95066f6e074c14dd3d1a4193ca2aa5794361848d0ec56d4`; 40 LF lines; 1214 bytes.
<!-- BEGIN REJECTED-T5M20-SCOPE PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..f2520f7a688910f95004d1edfc7fadc1008cda23 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -834,23 +834,23 @@ internal sealed partial class PassiveDriver : IDisposable
                     emitReady = true;
                 }
             }
-            if (emitReady)
-            {
-                try
-                {
-                    reporter.Ready(0);
-                }
-                catch (Exception)
-                {
-                    TryFaultInternal(
-                        "observer_exception", FaultRequest.Derived());
-                }
-            }
         }
         finally
         {
             ReleaseOutputLease(traceIoFailure);
         }
+        if (emitReady)
+        {
+            try
+            {
+                reporter.Ready(0);
+            }
+            catch (Exception)
+            {
+                TryFaultInternal(
+                    "observer_exception", FaultRequest.Derived());
+            }
+        }
     }
 
     private void ClearInitialAfterTerminalReturn()
~~~
<!-- END REJECTED-T5M20-SCOPE PATCH -->

**REJECTED-T5M23-BROAD patch:** SHA-256 `3ebacfe9b8f471e4e67770302a7e4728bb22d9ab2a9bced33a171b82f1299f4f`; 14 LF lines; 584 bytes.
<!-- BEGIN REJECTED-T5M23-BROAD PATCH -->
~~~diff
diff --git a/oracle/plugin/Core/PassiveDriver.cs b/oracle/plugin/Core/PassiveDriver.cs
index b132f89b321345452901faab870ea0d642b93e06..18aa7e38a8b68101e4d7c29b7fc605b67c9bd02d 100644
--- a/oracle/plugin/Core/PassiveDriver.cs
+++ b/oracle/plugin/Core/PassiveDriver.cs
@@ -1209,8 +1209,8 @@ internal sealed partial class PassiveDriver : IDisposable
             }
             else
             {
-                work = deferredTerminalWork;
                 deferredTerminalWork = null;
+                outputLeaseActive = false;
             }
         }
         if (work != null)
~~~
<!-- END REJECTED-T5M23-BROAD PATCH -->

T5M28 additionally requires a real-sink stale-trace proof. In a disposable clone only, apply a separately hashed temporary test-only export hook, force-build, run the unchanged focused test to export real NDJSON bytes, reverse the hook exactly, authenticate its complete absence and the restored test blob, then force-build and run GREEN again. Construct the stale trace only by changing the real trace's terminal Error to the claim-time pre-Step snapshot. Run the exact pinned `read_oracle_trace_stream` and require exit `0` with stdout exactly:

```text
PASS stale trace rejected: error input_index must equal the flushed-step count
```

R must record the export-hook patch identity, real-trace SHA-256/lines/bytes, stale-transform script identity, stale-trace SHA-256/lines/bytes, exact reader source pin, command, stdout, and exit status. A hand-written standalone JSON fixture is not acceptable provenance.

## Common Gates

### Standalone candidate/committed plan-audit gate

Planning has a separate, pre-runtime trust boundary. Extract the one checker
below from the candidate plan and run it before staging P. The checker has only
`candidate` and `committed` modes, closes over every embedded-artifact identity,
and emits the plan, checker, runtime, and core-manifest identities that must be
identical on the two sides of the commit. Both modes begin at process start with
the literal minimal `env -i` launch below; an inherited Bash invocation is not a
checker gate. It never sources the plan or runtime. Its one build-free local
no-hardlink replay clone is the named preapproval audit exception and cannot be
retained or imported into implementation evidence.

<!-- TASK5-PLAN-AUDIT-BEGIN -->
```bash
set -euo pipefail
umask 077

# These checks detect accidental inherited state, but cannot defend against a
# hostile startup file that ran before this byte stream. The prescribed
# process-start /usr/bin/env -i launch below is the trust boundary.
test -z "${BASH_ENV+x}"
test -z "${ENV+x}"
test -z "$(declare -F)"
test -z "$(alias -p)"
test "${PATH-}" = /usr/bin:/bin:/usr/sbin:/sbin
test "${LC_ALL-}" = C
test "${LANG-}" = C
test "${HOME-}" = /private/tmp
test "${TMPDIR-}" = /private/tmp
test "${GIT_CONFIG_NOSYSTEM-}" = 1
test "${GIT_CONFIG_GLOBAL-}" = /dev/null
test "${GIT_TERMINAL_PROMPT-}" = 0
test "$(type -P git)" = /usr/bin/git
test "$(type -P shasum)" = /usr/bin/shasum
test "$(/usr/bin/env | /usr/bin/cut -d= -f1 | /usr/bin/sort)" = \
  "$(printf '%s\n' GIT_CONFIG_GLOBAL GIT_CONFIG_NOSYSTEM \
    GIT_TERMINAL_PROMPT HOME LANG LC_ALL PATH PWD SHLVL TMPDIR _ | \
    /usr/bin/sort)"

test "$#" = 2 || exit 64
case "$1" in
  candidate|committed) audit_mode="$1" ;;
  *) exit 64 ;;
esac
audit_target="$2"

audit_expected_root=/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-oracle-passive-trace
audit_expected_branch=refs/heads/codex/oracle-passive-task5-rebase
audit_expected_parent=9f69d2c40406461a28f018290d579cf313f22287
audit_expected_subject='docs: plan Task 5 passive driver completion'
audit_plan_path=docs/superpowers/plans/2026-08-07-task-5-passive-driver.md
audit_expected_header='# Task 5 Passive Driver Completion Implementation Plan'
audit_checker_begin='<!-- TASK5-PLAN-AUDIT-BEGIN -->'
audit_checker_end='<!-- TASK5-PLAN-AUDIT-END -->'
audit_bootstrap_begin='<!-- TASK5-BOOTSTRAP-BEGIN -->'
audit_bootstrap_end='<!-- TASK5-BOOTSTRAP-END -->'
audit_runtime_begin='<!-- TASK5-RUNTIME-BEGIN -->'
audit_runtime_end='<!-- TASK5-RUNTIME-END -->'
audit_preapproval_launch_begin='<!-- TASK5-PREAPPROVAL-CHECKER-LAUNCHES-BEGIN -->'
audit_preapproval_launch_end='<!-- TASK5-PREAPPROVAL-CHECKER-LAUNCHES-END -->'
audit_preapproval_policy_line='TASK5-PREAPPROVAL-REPLAY-EXCEPTION: checker-only-build-free-no-hardlink-local'
audit_coordination_reference_contract_line='TASK5-COORDINATION-REFERENCE-CONTRACT: ascii-safe-no-standalone-r-v1'
audit_coordination_reference_defense_marker='# TASK5-COORDINATION-REFERENCE-STANDALONE-R-DEFENSE-V1'
audit_structured_text_nul_defense_marker='# TASK5-STRUCTURED-TEXT-NUL-DEFENSE-V1'
audit_report_response_encoding_contract_line='TASK5-REPORT-RESPONSE-ENCODING-CONTRACT: exact-lowercase-hex-v1'
test "$PWD" = "$audit_expected_root"

audit_fail() {
  printf 'Task 5 plan audit failure: %s\n' "$*" >&2
  exit 1
}

audit_sha256() {
  shasum -a 256 "$1" | awk '{print $1}'
}

audit_require_p_identity() {
  test "$#" = 4
  test "$1" = jess || return 1
  test "$2" = optimistindustries@gmail.com || return 1
  test "$3" = jess || return 1
  test "$4" = optimistindustries@gmail.com || return 1
}

audit_require_coordination_reference() {
  test "$#" = 1 || return 1
  test -n "$1" || return 1
  case "$1" in
    *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:/-]*) \
      return 1 ;;
  esac
# TASK5-COORDINATION-REFERENCE-STANDALONE-R-DEFENSE-V1
  if printf '%s\n' "$1" | awk '
    {
      lower = tolower($0)
      if (lower ~ /(^|[^a-z0-9])r([^a-z0-9]|$)/)
        found = 1
    }
    END {exit(found ? 0 : 1)}
  '; then
    return 1
  fi
}

audit_require_no_nul_file() {
  test "$#" = 1 || return 1
  test -f "$1" || return 1
  test ! -L "$1" || return 1
# TASK5-STRUCTURED-TEXT-NUL-DEFENSE-V1
  if od -An -tu1 -v "$1" | awk '
    {
      for (field = 1; field <= NF; field++)
        if ($field == 0)
          found = 1
    }
    END {exit(found ? 0 : 1)}
  '; then
    return 1
  fi
}

if audit_require_p_identity WRONG optimistindustries@gmail.com jess optimistindustries@gmail.com; then
  audit_fail 'P identity negative proof accepted a wrong author'
fi
audit_require_p_identity \
  jess optimistindustries@gmail.com jess optimistindustries@gmail.com

if audit_require_coordination_reference R; then
  audit_fail 'coordination reference accepted reserved R'
fi
if audit_require_coordination_reference agent/R; then
  audit_fail 'coordination reference accepted a delimited reserved R'
fi
audit_require_coordination_reference reviewer
for audit_rejected_reference in r R/agent foo-R-bar reviewer:r:west \
    reviewer_R_west R_1 _R_ /R/ R- -r foo./R_-bar 1_r; do
  if audit_require_coordination_reference "$audit_rejected_reference"; then
    audit_fail "coordination reference accepted reserved segment: $audit_rejected_reference"
  fi
done
for audit_accepted_reference in root reviewer cr bar R1 1R AR RA rr \
    agent/R1 foo.r2 reviewer-r2 1R- -R1 _R1 1R_ . _ : / -; do
  audit_require_coordination_reference "$audit_accepted_reference" || \
    audit_fail "coordination reference rejected safe token: $audit_accepted_reference"
done

audit_require_absent_path() {
  test "$#" = 1
  test ! -e "$1"
  test ! -L "$1"
}

audit_require_owned_regular() {
  test "$#" = 1
  test -f "$1"
  test ! -L "$1"
  test "$(stat -f '%u' "$1")" = "$(id -u)"
}

audit_artifact_catalog() {
  cat <<'TASK5_AUDIT_ARTIFACTS'
C51-TESTS|implementation|~~~diff|27b5d2da89f011a1e3c84a6cb27077ad093e46ab3ac05bb4bef4386c8c73d6eb|1213|51384
C51-PRODUCTION|implementation|~~~diff|dc60e234556f4cd5717dab1422c18edc63e42a87046200c135ff5f8fc32755c0|752|23537
C52-TESTS|implementation|~~~diff|13beee22b9b661320226c8deeb7979c574918d50c30b9f4498f5d35a9294e80c|880|39208
C52-PRODUCTION|implementation|~~~diff|69f717ed83deb3ff86fed13798764aa29f0120b29b7a649104d6cace218edd7e|395|12407
C53-TESTS|implementation|~~~diff|d56cb0b64868120338b27ced71299da7b78a87187a7b8dfa70b63bde329e7dcc|1123|43301
C53-PRODUCTION|implementation|~~~diff|918cbac02ec8e01ee61e89c0b5418d6430547c33b46ea949bc9f073943dc298c|159|5310
C53C1-TESTS|implementation|~~~diff|a37a0ea03c285bfc8d8068bbb7179787293ce925dc8d7c42ad47a9b53ada0112|2468|95234
C53C1-PRODUCTION|implementation|~~~diff|7c000fabda103b116b7a5ebc773da13692d3b4a838dcf280dd68b7ab5590102c|598|18412
C53C2-TESTS|implementation|~~~diff|175d83ab045a264e76f537b5c4d94ea3f945ac874bf7caa6417de2183976ece1|190|7397
C53C2-PRODUCTION|implementation|~~~diff|0ee216ead3ab2bd602bbcd42aa67eda31943f55db558250288452b785053354e|23|1011
T5M01|canonical|~~~diff|d1933eadca9505e3d105db334b613be4e89196263498e8b96be05f89439acbbf|13|633
T5M02|canonical|~~~diff|b7f2c2ca8cff261303f8d8805336d4536a0c5bc5cec6338128386c4d82feec2a|12|576
T5M03|canonical|~~~diff|b426eb4706f9c4613f470c318d01e6ace393b4e77a16467a4de85f64013d956c|13|580
T5M04|canonical|~~~diff|048481433a1cfa640f44b73d829e98fcff1f3203255f472d8cca791eb5116e88|35|1309
T5M05|canonical|~~~diff|a936e9ab5183511dc144c127a7ab5bbbdd77f0a9dee3ccbce5cfdaa1f403defe|19|703
T5M06|canonical|~~~diff|cc764023239a341d5f1a830e74e2a281b0ee1a81ada1515d265fa8b4780cce57|13|584
T5M07|canonical|~~~diff|acd27cc07fe21b72108b26163d345bebc844c01c96b4464bffd5f1704b63a95e|16|736
T5M08|canonical|~~~diff|3e334b7f4fe7ba1215bd89cac2de14085870a4487c80d4d33b9bd23336b56cd7|13|667
T5M09|canonical|~~~diff|068c96f07aac340876a269a8b9dd918dd0a31f54bde084516925da580693327c|27|1149
T5M10|canonical|~~~diff|87a1e87bb1581f621c2ed48e802bb1e45ee855da3dee5371047f1138a35434a4|15|644
T5M11|canonical|~~~diff|fdc867802747ac1153cbd3e94363b560d0218c9223e51c5f7716d8aa0bbdfec8|12|551
T5M12|canonical|~~~diff|0b8c8184b2f15ed3a0c8984009dcfdb857458924a7fb82a99ebb0e612a34bc90|19|740
T5M13|canonical|~~~diff|c2b718251cd91a10366dbd99c9a0cab10759db6c8ccb976a71326f31eb66bc7f|20|924
T5M14|canonical|~~~diff|b78d661029de14189be8864c12f9133d0924b347d49b4f0d6aef444fe512ccb5|14|654
T5M15|canonical|~~~diff|a7d7f2af440075e395346748d2ca9771c18dec8b052b9211131ff34964fa53bb|93|2879
T5M16|canonical|~~~diff|75c7af5e49cf50eef84382640ea9ab62c270948a6769a43538fd6c80ed3604bd|13|574
T5M17|canonical|~~~diff|be1da505f26c232382f0ec3ea686896cd7c3d17e9459dd6d53c4d241cfdbfed8|13|654
T5M18|canonical|~~~diff|e3caa55377b3a6200973310f336c42bb786779e25db57b3a461c262fdc8f6434|62|1962
T5M19|canonical|~~~diff|a6f01ada63cba3c9aaf40a0d17afb3bbe0321b6617bfb13ce1dd704f3fcf994b|91|2854
T5M20|canonical|~~~diff|8e5617ac4385209efd55aa82342b597a52f1aa9485150701dd2862accf9a0335|56|1664
T5M21|canonical|~~~diff|7bd93518c41f62bfb72cc254f7817e1c372801a14030a6833806c8bac1e0a61d|111|3553
T5M22|canonical|~~~diff|76bea7cc72c86a978a9329046a1b266eca62a27972e3f43aefc8974609b9f069|14|646
T5M23|canonical|~~~diff|9ce1757858a93e6581ad88f237445499976da102184f47e7e8432d3852dbc665|18|826
T5M24|canonical|~~~diff|c5bb317a2a4db15a02114a71554b2d994e9013489c044b4437c9a0df7b79100e|18|874
T5M25|canonical|~~~diff|b7cceee7030a41131b9dfdcd1354c777d7f411457d069d28c0e60b36b42a1577|30|1248
T5M26|canonical|~~~diff|3ace6fa03b74e065b5d2106b04a391c0834747f0fda6c9ee38f531f5e085918f|17|751
T5M27|canonical|~~~diff|f25e9c2eab1030b3fdfeb7299787b2a53d47b1d2042362dce53251679933e4ca|28|1130
T5M28|canonical|~~~diff|6787476f2830289a1e2660fd7e2bb299cabbd14ccd4bd9650df2cad0df0bd5a3|23|1011
REJECTED-T5M20-SCOPE|rejected|~~~diff|bd025237bc8baf67b95066f6e074c14dd3d1a4193ca2aa5794361848d0ec56d4|40|1214
REJECTED-T5M23-BROAD|rejected|~~~diff|3ebacfe9b8f471e4e67770302a7e4728bb22d9ab2a9bced33a171b82f1299f4f|14|584
T5M28-EXPORT-HOOK|hook|~~~diff|04e413ee1c486d60bdbfefe9033dd1232a19b4f2d46011f5a02d11d13dd6f8f7|26|1246
T5M28-QUALIFIED-PROBE|probe|~~~python|0efd1cdcb2fef895c29d566512af85d86d31aa4cf247e338af912d6de24b04c8|33|1142
TASK5_AUDIT_ARTIFACTS
}

audit_root="$(mktemp -d /private/tmp/ssr-task5-plan-audit.XXXXXXXX)"
test -d "$audit_root"
test ! -L "$audit_root"
chmod 700 "$audit_root"
test "$(stat -f '%Lp' "$audit_root")" = 700
test "$(stat -f '%u' "$audit_root")" = "$(id -u)"

audit_bootstrap_env_probe="$audit_root/bootstrap-env-probe.sh"
audit_bootstrap_env_sentinel="$audit_root/bootstrap-env-sentinel"
audit_require_absent_path "$audit_bootstrap_env_probe"
audit_require_absent_path "$audit_bootstrap_env_sentinel"
printf '%s\n' \
  'git() { return 77; }' \
  'export -f git' \
  'printf poison > "$TASK5_BOOTSTRAP_ENV_SENTINEL"' \
  > "$audit_bootstrap_env_probe"
audit_require_owned_regular "$audit_bootstrap_env_probe"
set +e
BASH_ENV="$audit_bootstrap_env_probe" \
TASK5_BOOTSTRAP_ENV_SENTINEL="$audit_bootstrap_env_sentinel" \
  /bin/bash --noprofile --norc -c 'git' >/dev/null 2>&1
audit_bootstrap_env_negative_status=$?
set -e
test "$audit_bootstrap_env_negative_status" = 77
audit_bootstrap_env_negative_status=77
test -f "$audit_bootstrap_env_sentinel"
test ! -L "$audit_bootstrap_env_sentinel"
test "$(cat "$audit_bootstrap_env_sentinel")" = poison
rm "$audit_bootstrap_env_sentinel"
audit_require_absent_path "$audit_bootstrap_env_sentinel"
BASH_ENV="$audit_bootstrap_env_probe" \
TASK5_BOOTSTRAP_ENV_SENTINEL="$audit_bootstrap_env_sentinel" \
  /usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C LANG=C \
    HOME=/private/tmp TMPDIR=/private/tmp GIT_CONFIG_NOSYSTEM=1 \
    GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 \
    /bin/bash --noprofile --norc -c \
      'test -z "${BASH_ENV+x}"; test -z "${ENV+x}"; test -z "$(declare -F)"; test "$(type -t git)" = file; test "$(command -v git)" = /usr/bin/git'
audit_require_absent_path "$audit_bootstrap_env_sentinel"
printf 'bootstrap-env-adversarial=PASS\n'

audit_execution_root="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
test "$audit_execution_root" = "$audit_expected_root"
test "$(git -C "$audit_execution_root" symbolic-ref -q HEAD)" = \
  "$audit_expected_branch"

case "$audit_mode" in
  candidate)
    test "$(git -C "$audit_execution_root" rev-parse HEAD)" = \
      "$audit_expected_parent"
    test "$audit_target" = "$audit_expected_root/$audit_plan_path"
    test "$(git -C "$audit_execution_root" status --porcelain=v1 \
      --untracked-files=all)" = "?? $audit_plan_path"
    audit_require_owned_regular "$audit_target"
    test "$(cd "${audit_target%/*}" && pwd -P)" = \
      "$audit_expected_root/docs/superpowers/plans"
    audit_candidate_sha="$(audit_sha256 "$audit_target")"
    audit_plan="$audit_root/candidate-plan.md"
    audit_require_absent_path "$audit_plan"
    cp -p "$audit_target" "$audit_plan"
    audit_require_owned_regular "$audit_plan"
    cmp -s "$audit_target" "$audit_plan"
    test "$(audit_sha256 "$audit_plan")" = "$audit_candidate_sha"
    ;;
  committed)
    P="$audit_target"
    case "$P" in
      ????????????????????????????????????????) ;;
      *) audit_fail 'P is not a full commit OID' ;;
    esac
    case "$P" in
      *[!0123456789abcdef]*) audit_fail 'P is not lowercase hexadecimal' ;;
    esac
    test "$(git -C "$audit_execution_root" rev-parse HEAD)" = "$P"
    test "$(git -C "$audit_execution_root" rev-parse --verify "$P^{commit}")" = "$P"
    test "$(git -C "$audit_execution_root" rev-list --parents -n 1 "$P")" = \
      "$P $audit_expected_parent"
    test "$(git -C "$audit_execution_root" show -s --format=%s "$P")" = \
      "$audit_expected_subject"
    audit_require_p_identity \
      "$(git -C "$audit_execution_root" show -s --format=%an "$P")" \
      "$(git -C "$audit_execution_root" show -s --format=%ae "$P")" \
      "$(git -C "$audit_execution_root" show -s --format=%cn "$P")" \
      "$(git -C "$audit_execution_root" show -s --format=%ce "$P")"
    test "$(git -C "$audit_execution_root" diff-tree --no-commit-id \
      --name-only -r "$P")" = "$audit_plan_path"
    test "$(git -C "$audit_execution_root" ls-tree "$P" -- \
      "$audit_plan_path" | awk '{print $1}')" = 100644
    test -z "$(git -C "$audit_execution_root" status --porcelain=v1 \
      --untracked-files=all)"
    audit_plan="$audit_root/committed-plan.md"
    audit_require_absent_path "$audit_plan"
    git -C "$audit_execution_root" show "$P:$audit_plan_path" > "$audit_plan"
    audit_require_owned_regular "$audit_plan"
    ;;
esac

audit_require_no_nul_file "$audit_plan" || \
  audit_fail 'plan contains a NUL byte'
test "$(grep -Fxc "$audit_preapproval_policy_line" "$audit_plan")" = 1
test "$(grep -Fxc "$audit_coordination_reference_contract_line" \
  "$audit_plan")" = 1
test "$(grep -Fxc "$audit_coordination_reference_defense_marker" \
  "$audit_plan")" = 3
test "$(grep -Fxc "$audit_structured_text_nul_defense_marker" \
  "$audit_plan")" = 3
test "$(grep -Fxc "$audit_report_response_encoding_contract_line" \
  "$audit_plan")" = 1
test "$(grep -Fxc 'task5_bootstrap_read_coordination_reference_file() {' \
  "$audit_plan")" = 1
test "$(grep -Fxc 'task5_read_coordination_reference_file() {' \
  "$audit_plan")" = 1
test "$(grep -Fxc '  task5_require_no_nul_file "$report_path" || return 1' \
  "$audit_plan")" = 1
test "$(grep -Fxc 'task5_write_report_review_records() (' \
  "$audit_plan")" = 1
test "$(grep -Fxc 'task5_require_report_review_record_file() (' \
  "$audit_plan")" = 1
test "$(grep -Fxc 'task5_require_report_review_records() (' \
  "$audit_plan")" = 1
test "$(grep -Fxc '  task5_write_report_review_records "$derived_path"' \
  "$audit_plan")" = 1
test "$(grep -Fxc '  cmp -s "$expected_path" "$derived_path" || return 1' \
  "$audit_plan")" = 1
test "$(grep -Fxc "$audit_preapproval_launch_begin" "$audit_plan")" = 1
test "$(grep -Fxc "$audit_preapproval_launch_end" "$audit_plan")" = 1
audit_preapproval_launch_body="$audit_root/preapproval-checker-launches.txt"
audit_preapproval_launch_expected="$audit_root/preapproval-checker-launches.expected"
audit_require_absent_path "$audit_preapproval_launch_body"
audit_require_absent_path "$audit_preapproval_launch_expected"
awk -v first="$audit_preapproval_launch_begin" \
    -v last="$audit_preapproval_launch_end" '
  $0 == first {inside=1; next}
  $0 == last {inside=0; exit}
  inside {print}
' "$audit_plan" > "$audit_preapproval_launch_body"
audit_preapproval_markdown_fence='```'
{
  printf '%s\n' \
    "${audit_preapproval_markdown_fence}text" \
    '/usr/bin/env -i \' \
    '  PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C LANG=C \' \
    '  HOME=/private/tmp TMPDIR=/private/tmp \' \
    '  GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \' \
    '  GIT_TERMINAL_PROMPT=0 \' \
    '  /bin/bash --noprofile --norc "$candidate_checker" candidate "$plan_path"'
  printf '\n'
  printf '%s\n' \
    '/usr/bin/env -i \' \
    '  PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C LANG=C \' \
    '  HOME=/private/tmp TMPDIR=/private/tmp \' \
    '  GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \' \
    '  GIT_TERMINAL_PROMPT=0 \' \
    '  /bin/bash --noprofile --norc "$committed_checker" committed "$P"' \
    "$audit_preapproval_markdown_fence"
} > "$audit_preapproval_launch_expected"
cmp -s "$audit_preapproval_launch_body" \
  "$audit_preapproval_launch_expected"
audit_require_owned_regular "$audit_preapproval_launch_body"
audit_require_owned_regular "$audit_preapproval_launch_expected"

test "$(sed -n '1p' "$audit_plan")" = "$audit_expected_header"
test "$(awk 'index($0, sprintf("%c", 13)) {n++} END {print n + 0}' \
  "$audit_plan")" = 0
test "$(tail -c 1 "$audit_plan" | od -An -tu1 | tr -d '[:space:]')" = 10
audit_forbidden_injection='__TASK''5_'
audit_forbidden_braces='{''{'
audit_forbidden_insert='<IN''SERT'
audit_forbidden_todo='TO''DO'
audit_forbidden_tbd='T''BD'
for audit_forbidden in "$audit_forbidden_injection" "$audit_forbidden_braces" \
    "$audit_forbidden_insert" "$audit_forbidden_todo" "$audit_forbidden_tbd"; do
  if grep -F "$audit_forbidden" "$audit_plan" >/dev/null; then
    audit_fail 'placeholder or injection token remains'
  fi
done
audit_bad_iso=2026-08-0''8
audit_bad_aug='Aug'' 8'
if grep -F "$audit_bad_iso" "$audit_plan" >/dev/null || \
    grep -F "$audit_bad_aug" "$audit_plan" >/dev/null; then
  audit_fail 'date drift detected'
fi

audit_catalog="$audit_root/expected-artifacts.manifest"
audit_actual="$audit_root/actual-artifacts.manifest"
audit_expected_markers="$audit_root/expected-artifact-markers"
audit_actual_markers="$audit_root/actual-artifact-markers"
audit_require_absent_path "$audit_catalog"
audit_require_absent_path "$audit_actual"
audit_require_absent_path "$audit_expected_markers"
audit_require_absent_path "$audit_actual_markers"
audit_artifact_catalog > "$audit_catalog"
: > "$audit_actual"
: > "$audit_expected_markers"
test "$(wc -l < "$audit_catalog" | tr -d '[:space:]')" = 42
test "$(cut -d '|' -f 1 "$audit_catalog" | sort -u | wc -l | \
  tr -d '[:space:]')" = 42

audit_implementation=0
audit_canonical=0
audit_rejected=0
audit_hook=0
audit_probe=0
audit_diff_fences=0
while IFS='|' read -r artifact_id artifact_kind artifact_fence \
    artifact_sha artifact_lines artifact_bytes; do
  case "$artifact_kind:$artifact_id" in
    implementation:*)
      artifact_begin="<!-- TASK5-PATCH-BEGIN:$artifact_id -->"
      artifact_end="<!-- TASK5-PATCH-END:$artifact_id -->"
      audit_implementation=$((audit_implementation + 1)) ;;
    canonical:T5M??)
      artifact_begin="<!-- BEGIN $artifact_id CANONICAL PATCH -->"
      artifact_end="<!-- END $artifact_id CANONICAL PATCH -->"
      audit_canonical=$((audit_canonical + 1)) ;;
    rejected:REJECTED-T5M20-SCOPE)
      artifact_begin='<!-- BEGIN REJECTED-T5M20-SCOPE PATCH -->'
      artifact_end='<!-- END REJECTED-T5M20-SCOPE PATCH -->'
      audit_rejected=$((audit_rejected + 1)) ;;
    rejected:REJECTED-T5M23-BROAD)
      artifact_begin='<!-- BEGIN REJECTED-T5M23-BROAD PATCH -->'
      artifact_end='<!-- END REJECTED-T5M23-BROAD PATCH -->'
      audit_rejected=$((audit_rejected + 1)) ;;
    hook:T5M28-EXPORT-HOOK)
      artifact_begin='<!-- BEGIN T5M28 TEMPORARY EXPORT HOOK -->'
      artifact_end='<!-- END T5M28 TEMPORARY EXPORT HOOK -->'
      audit_hook=$((audit_hook + 1)) ;;
    probe:T5M28-QUALIFIED-PROBE)
      artifact_begin='<!-- BEGIN T5M28 QUALIFIED STALE PROBE -->'
      artifact_end='<!-- END T5M28 QUALIFIED STALE PROBE -->'
      audit_probe=$((audit_probe + 1)) ;;
    *) audit_fail "unknown artifact catalog entry: $artifact_kind:$artifact_id" ;;
  esac
  printf '%s\n%s\n' "$artifact_begin" "$artifact_end" \
    >> "$audit_expected_markers"
  test "$(awk -v wanted="$artifact_begin" \
    '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
  test "$(awk -v wanted="$artifact_end" \
    '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
  artifact_begin_line="$(awk -v wanted="$artifact_begin" \
    '$0 == wanted {print NR}' "$audit_plan")"
  artifact_end_line="$(awk -v wanted="$artifact_end" \
    '$0 == wanted {print NR}' "$audit_plan")"
  test "$artifact_begin_line" -lt "$artifact_end_line"
  test "$(sed -n "$((artifact_begin_line + 1))p" "$audit_plan")" = \
    "$artifact_fence"
  test "$(sed -n "$((artifact_end_line - 1))p" "$audit_plan")" = '~~~'
  test "$(awk -v first="$artifact_begin_line" -v last="$artifact_end_line" \
    'NR > first && NR < last && substr($0,1,3) == "~~~" {n++} \
     END {print n + 0}' "$audit_plan")" = 2
  artifact_path="$audit_root/$artifact_id.body"
  audit_require_absent_path "$artifact_path"
  awk -v first="$((artifact_begin_line + 1))" \
    -v last="$((artifact_end_line - 1))" \
    'NR > first && NR < last {print}' "$audit_plan" > "$artifact_path"
  audit_require_owned_regular "$artifact_path"
  test "$(tail -c 1 "$artifact_path" | od -An -tu1 | tr -d '[:space:]')" = 10
  test "$(audit_sha256 "$artifact_path")" = "$artifact_sha"
  test "$(wc -l < "$artifact_path" | tr -d '[:space:]')" = "$artifact_lines"
  test "$(wc -c < "$artifact_path" | tr -d '[:space:]')" = "$artifact_bytes"
  printf '%s|%s|%s|%s|%s|%s\n' "$artifact_id" "$artifact_kind" \
    "$artifact_fence" "$artifact_sha" "$artifact_lines" "$artifact_bytes" \
    >> "$audit_actual"
  if test "$artifact_fence" = '~~~diff'; then
    audit_diff_fences=$((audit_diff_fences + 1))
  fi
done < "$audit_catalog"
cmp -s "$audit_catalog" "$audit_actual"
awk '
  /^<!-- TASK5-PATCH-(BEGIN|END):[A-Z0-9-]+ -->$/ ||
  /^<!-- (BEGIN|END) T5M[0-9][0-9] CANONICAL PATCH -->$/ ||
  $0 == "<!-- BEGIN REJECTED-T5M20-SCOPE PATCH -->" ||
  $0 == "<!-- END REJECTED-T5M20-SCOPE PATCH -->" ||
  $0 == "<!-- BEGIN REJECTED-T5M23-BROAD PATCH -->" ||
  $0 == "<!-- END REJECTED-T5M23-BROAD PATCH -->" ||
  $0 == "<!-- BEGIN T5M28 TEMPORARY EXPORT HOOK -->" ||
  $0 == "<!-- END T5M28 TEMPORARY EXPORT HOOK -->" ||
  $0 == "<!-- BEGIN T5M28 QUALIFIED STALE PROBE -->" ||
  $0 == "<!-- END T5M28 QUALIFIED STALE PROBE -->" { print }
' "$audit_plan" | sort > "$audit_actual_markers"
sort "$audit_expected_markers" > "$audit_expected_markers.sorted"
cmp -s "$audit_expected_markers.sorted" "$audit_actual_markers"
test "$audit_implementation" = 10
test "$audit_canonical" = 28
test "$audit_rejected" = 2
test "$audit_hook" = 1
test "$audit_probe" = 1
test "$audit_diff_fences" = 41
test "$(awk '$0 == "~~~diff" {n++} END {print n + 0}' "$audit_plan")" = 41

audit_whitespace="$audit_root/narrative-whitespace.report"
audit_require_absent_path "$audit_whitespace"
awk '
  function fail(message) {
    printf "%s:%d:%s\n", FILENAME, NR, message > "/dev/stderr"
    bad = 1
  }
  function begins(line) {
    return line ~ /^<!-- TASK5-PATCH-BEGIN:[A-Z0-9-]+ -->$/ ||
      line ~ /^<!-- BEGIN T5M[0-9][0-9] CANONICAL PATCH -->$/ ||
      line == "<!-- BEGIN REJECTED-T5M20-SCOPE PATCH -->" ||
      line == "<!-- BEGIN REJECTED-T5M23-BROAD PATCH -->" ||
      line == "<!-- BEGIN T5M28 TEMPORARY EXPORT HOOK -->" ||
      line == "<!-- BEGIN T5M28 QUALIFIED STALE PROBE -->"
  }
  function ends(line) {
    return line ~ /^<!-- TASK5-PATCH-END:[A-Z0-9-]+ -->$/ ||
      line ~ /^<!-- END T5M[0-9][0-9] CANONICAL PATCH -->$/ ||
      line == "<!-- END REJECTED-T5M20-SCOPE PATCH -->" ||
      line == "<!-- END REJECTED-T5M23-BROAD PATCH -->" ||
      line == "<!-- END T5M28 TEMPORARY EXPORT HOOK -->" ||
      line == "<!-- END T5M28 QUALIFIED STALE PROBE -->"
  }
  begins($0) { in_artifact = 1; next }
  in_artifact && ends($0) { in_artifact = 0; next }
  in_artifact { next }
  /[ \t]+$/ { fail("narrative trailing whitespace") }
  {
    prefix = $0
    sub(/[^ \t].*$/, "", prefix)
    if (prefix ~ / \t/)
      fail("narrative space before tab in indentation")
  }
  END {
    if (in_artifact)
      fail("unterminated authenticated artifact")
    if (bad)
      exit 1
    print "narrative-whitespace=PASS"
  }
' "$audit_plan" > "$audit_whitespace"
test "$(cat "$audit_whitespace")" = 'narrative-whitespace=PASS'

audit_bash_root="$audit_root/bash-fences"
test ! -e "$audit_bash_root"
test ! -L "$audit_bash_root"
mkdir -m 700 "$audit_bash_root"
audit_bash_manifest="$audit_root/bash-fences.manifest"
audit_require_absent_path "$audit_bash_manifest"
awk -v output_root="$audit_bash_root" -v manifest="$audit_bash_manifest" '
  ($0 == "```bash" || $0 == "~~~bash") && !inside {
    inside = 1
    delimiter = substr($0, 1, 3)
    count++
    output = sprintf("%s/fence-%03d.sh", output_root, count)
    next
  }
  inside && $0 == delimiter {
    close(output)
    print output >> manifest
    inside = 0
    next
  }
  inside { print > output }
  END {
    if (inside || count == 0)
      exit 1
  }
' "$audit_plan"
audit_all_bash="$audit_root/all-bash-fences.sh"
audit_require_absent_path "$audit_all_bash"
: > "$audit_all_bash"
audit_bash_count=0
while IFS= read -r audit_bash_path; do
  audit_require_owned_regular "$audit_bash_path"
  /bin/bash --noprofile --norc -n "$audit_bash_path"
  cat "$audit_bash_path" >> "$audit_all_bash"
  audit_bash_count=$((audit_bash_count + 1))
done < "$audit_bash_manifest"
/bin/bash --noprofile --norc -n "$audit_all_bash"

audit_runtime="$audit_root/task5-controller.sh"
audit_require_absent_path "$audit_runtime"
test "$(awk -v wanted="$audit_runtime_begin" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
test "$(awk -v wanted="$audit_runtime_end" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
audit_runtime_first="$(awk -v wanted="$audit_runtime_begin" \
  '$0 == wanted {print NR}' "$audit_plan")"
audit_runtime_last="$(awk -v wanted="$audit_runtime_end" \
  '$0 == wanted {print NR}' "$audit_plan")"
test "$(sed -n "$((audit_runtime_first + 1))p" "$audit_plan")" = '```bash'
test "$(sed -n "$((audit_runtime_last - 1))p" "$audit_plan")" = '```'
awk -v first="$((audit_runtime_first + 1))" \
  -v last="$((audit_runtime_last - 1))" \
  'NR > first && NR < last {print}' "$audit_plan" > "$audit_runtime"
audit_require_owned_regular "$audit_runtime"
/bin/bash --noprofile --norc -n "$audit_runtime"

audit_runtime_library="$audit_root/task5-controller-library.sh"
audit_require_absent_path "$audit_runtime_library"
sed '$d' "$audit_runtime" > "$audit_runtime_library"
audit_require_owned_regular "$audit_runtime_library"
/bin/bash --noprofile --norc -n "$audit_runtime_library"
audit_fail_closed_target="$audit_root/fail-closed.target"
audit_fail_closed_link="$audit_root/fail-closed.link"
audit_fail_closed_reference="$audit_root/fail-closed.reference"
audit_fail_closed_valid_reference="$audit_root/fail-closed-valid.reference"
audit_fail_closed_receipt="$audit_root/fail-closed.receipt"
audit_fail_closed_report="$audit_root/fail-closed-report.md"
for audit_fail_closed_path in "$audit_fail_closed_target" \
    "$audit_fail_closed_link" "$audit_fail_closed_reference" \
    "$audit_fail_closed_valid_reference" "$audit_fail_closed_receipt" \
    "$audit_fail_closed_report"; do
  audit_require_absent_path "$audit_fail_closed_path"
done
: > "$audit_fail_closed_target"
chmod 400 "$audit_fail_closed_target"
ln -s "$audit_fail_closed_target" "$audit_fail_closed_link"
printf 'safe\0hidden\n' > "$audit_fail_closed_reference"
printf 'reviewer-r2\n' > "$audit_fail_closed_valid_reference"
printf 'implementation-actor-reference=safe\0hidden\n' \
  > "$audit_fail_closed_receipt"
printf 'P-THROUGH-FINAL-REVIEWS: recorded\nR-SELF-REVIEW: excluded-from-tracked-report\nsafe\0 R review\n' \
  > "$audit_fail_closed_report"
chmod 400 "$audit_fail_closed_reference" \
  "$audit_fail_closed_valid_reference" "$audit_fail_closed_receipt" \
  "$audit_fail_closed_report"
(
  . "$audit_runtime_library"
  if task5_require_sha256 abc 2>/dev/null; then exit 1; fi
  if task5_require_coordination_reference 'bad@ref' 2>/dev/null; then
    exit 1
  fi
  if task5_require_owned_regular "$audit_fail_closed_link"; then exit 1; fi
  if task5_require_owned_regular "$audit_root/fail-closed.missing" \
      2>/dev/null; then
    exit 1
  fi
  if task5_require_absent_path "$audit_fail_closed_target"; then exit 1; fi
  test "$(task5_read_coordination_reference_file \
    "$audit_fail_closed_valid_reference")" = reviewer-r2
  if task5_read_coordination_reference_file \
      "$audit_fail_closed_reference" >/dev/null 2>&1; then
    exit 1
  fi
  if task5_receipt_value "$audit_fail_closed_receipt" \
      implementation-actor-reference >/dev/null 2>&1; then
    exit 1
  fi
  if task5_require_report_noncircularity \
      "$audit_fail_closed_report" >/dev/null 2>&1; then
    exit 1
  fi
)
printf 'fail-closed-runtime-probes=PASS helpers=5 raw-ingresses=3\n'

audit_mutation_manifest_begin='# TASK5-CANONICAL-MUTATION-MANIFEST-BEGIN'
audit_mutation_manifest_end='# TASK5-CANONICAL-MUTATION-MANIFEST-END'
test "$(awk -v wanted="$audit_mutation_manifest_begin" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_runtime")" = 1
test "$(awk -v wanted="$audit_mutation_manifest_end" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_runtime")" = 1
audit_mutation_manifest_first="$(awk -v wanted="$audit_mutation_manifest_begin" \
  '$0 == wanted {print NR}' "$audit_runtime")"
audit_mutation_manifest_last="$(awk -v wanted="$audit_mutation_manifest_end" \
  '$0 == wanted {print NR}' "$audit_runtime")"
test "$audit_mutation_manifest_first" -lt "$audit_mutation_manifest_last"
audit_mutation_manifest="$audit_root/canonical-mutations.manifest"
audit_require_absent_path "$audit_mutation_manifest"
awk -v first="$audit_mutation_manifest_first" \
  -v last="$audit_mutation_manifest_last" \
  'NR > first && NR < last {print}' "$audit_runtime" \
  > "$audit_mutation_manifest"
audit_require_owned_regular "$audit_mutation_manifest"
test "$(wc -l < "$audit_mutation_manifest" | tr -d '[:space:]')" = 28
test "$(awk -F '|' 'NF != 12 {n++} END {print n + 0}' \
  "$audit_mutation_manifest")" = 0
audit_mutation_expected_ids="$audit_root/canonical-mutation-ids.expected"
audit_mutation_actual_ids="$audit_root/canonical-mutation-ids.actual"
audit_require_absent_path "$audit_mutation_expected_ids"
audit_require_absent_path "$audit_mutation_actual_ids"
audit_mutation_number=1
while test "$audit_mutation_number" -le 28; do
  printf 'T5M%02d\n' "$audit_mutation_number" \
    >> "$audit_mutation_expected_ids"
  audit_mutation_number=$((audit_mutation_number + 1))
done
cut -d '|' -f 1 "$audit_mutation_manifest" > "$audit_mutation_actual_ids"
cmp -s "$audit_mutation_expected_ids" "$audit_mutation_actual_ids"
test "$(grep -Fc 'mutation_result_sha=' "$audit_runtime")" = 0
while IFS='|' read -r mutation_id mutation_patch_sha \
    mutation_patch_lines mutation_patch_bytes mutation_target \
    mutation_parent_sha mutation_parent_blob mutation_result_sha \
    mutation_result_blob mutation_plugin_tree mutation_cohort \
    mutation_failure; do
  mutation_catalog_row="$(awk -F '|' -v wanted="$mutation_id" \
    '$1 == wanted && $2 == "canonical" {n++; row=$0} \
     END {if (n != 1) exit 1; print row}' "$audit_catalog")"
  test "$(printf '%s\n' "$mutation_catalog_row" | cut -d '|' -f 4)" = \
    "$mutation_patch_sha"
  test "$(printf '%s\n' "$mutation_catalog_row" | cut -d '|' -f 5)" = \
    "$mutation_patch_lines"
  test "$(printf '%s\n' "$mutation_catalog_row" | cut -d '|' -f 6)" = \
    "$mutation_patch_bytes"
  for mutation_sha in "$mutation_patch_sha" "$mutation_parent_sha" \
      "$mutation_result_sha"; do
    test "${#mutation_sha}" = 64
    case "$mutation_sha" in
      *[!0123456789abcdef]*) audit_fail 'invalid mutation SHA-256' ;;
    esac
  done
  for mutation_oid in "$mutation_parent_blob" "$mutation_result_blob" \
      "$mutation_plugin_tree"; do
    test "${#mutation_oid}" = 40
    case "$mutation_oid" in
      *[!0123456789abcdef]*) audit_fail 'invalid mutation Git identity' ;;
    esac
  done
  case "$mutation_target" in
    oracle/plugin/Core/*.cs) ;;
    *) audit_fail 'mutation target is outside production Core' ;;
  esac
  case "$mutation_cohort" in
    driver-input|driver-initial|driver-terminal) ;;
    *) audit_fail 'mutation cohort is outside the closed set' ;;
  esac
  test -n "$mutation_failure"
done < "$audit_mutation_manifest"
test "$(sed -n '19p' "$audit_mutation_manifest" | cut -d '|' -f 8)" = \
  a7e7236bc3a7cb5eb0098da59caea33387db98e9f29df30e71eafe3e81bf7d68

audit_mutation_replay_root="$audit_root/mutation-replay"
audit_require_absent_path "$audit_mutation_replay_root"
test "$(cd "$audit_mutation_replay_root/.." 2>/dev/null || \
  cd "$audit_root"; pwd -P)" = "$audit_root"
audit_checker_clone_count="$(grep -Ec \
  '^git -c protocol[.]file[.]allow=always clone --no-local --no-hardlinks \\' \
  "$0")"
test "$audit_checker_clone_count" = 1
for audit_checker_forbidden_command in \
    '/opt/homebrew/Cellar/'dot'net' ' dot''net ' 'git com''mit ' \
    'git a''dd ' 'git fe''tch' 'git pu''ll' 'cu''rl ' 'w''get ' \
    'py''test' 'Ste''am' 'Uni''ty' 'Bep''InEx'; do
  if grep -F "$audit_checker_forbidden_command" "$0" >/dev/null; then
    audit_fail 'checker contains a preapproval-forbidden command'
  fi
done
audit_mutation_clone_stdout="$audit_root/mutation-replay-clone.stdout"
audit_mutation_clone_stderr="$audit_root/mutation-replay-clone.stderr"
audit_mutation_clone_status_path="$audit_root/mutation-replay-clone.status"
for audit_mutation_output in "$audit_mutation_clone_stdout" \
    "$audit_mutation_clone_stderr" "$audit_mutation_clone_status_path"; do
  audit_require_absent_path "$audit_mutation_output"
done
set +e
git -c protocol.file.allow=always clone --no-local --no-hardlinks \
  --no-checkout "$audit_execution_root" "$audit_mutation_replay_root" \
  > "$audit_mutation_clone_stdout" 2> "$audit_mutation_clone_stderr"
audit_mutation_clone_status=$?
set -e
printf '%s\n' "$audit_mutation_clone_status" \
  > "$audit_mutation_clone_status_path"
test "$audit_mutation_clone_status" = 0
test -d "$audit_mutation_replay_root/.git"
test ! -L "$audit_mutation_replay_root/.git"
test "$(cd "$audit_mutation_replay_root/.." && pwd -P)" = "$audit_root"
test "$(find "$audit_root" -type d -name .git -print | \
  wc -l | tr -d '[:space:]')" = 1
test "$(git -C "$audit_mutation_replay_root" remote get-url origin)" = \
  "$audit_execution_root"
git -C "$audit_mutation_replay_root" remote remove origin
test -z "$(git -C "$audit_mutation_replay_root" remote)"
audit_mutation_alternates="$(git -C "$audit_mutation_replay_root" \
  rev-parse --git-path objects/info/alternates)"
case "$audit_mutation_alternates" in
  /*) ;;
  *) audit_mutation_alternates="$audit_mutation_replay_root/$audit_mutation_alternates" ;;
esac
audit_require_absent_path "$audit_mutation_alternates"
git -C "$audit_mutation_replay_root" config core.autocrlf false
git -C "$audit_mutation_replay_root" checkout -q --detach \
  "$audit_expected_parent"
test "$(git -C "$audit_mutation_replay_root" rev-parse HEAD)" = \
  "$audit_expected_parent"
audit_implementation_replay_count=0
for audit_implementation_id in \
    C51-TESTS C51-PRODUCTION C52-TESTS C52-PRODUCTION \
    C53-TESTS C53-PRODUCTION C53C1-TESTS C53C1-PRODUCTION \
    C53C2-TESTS C53C2-PRODUCTION; do
  audit_implementation_patch="$audit_root/$audit_implementation_id.body"
  audit_require_owned_regular "$audit_implementation_patch"
  git -C "$audit_mutation_replay_root" apply --check --index \
    "$audit_implementation_patch"
  git -C "$audit_mutation_replay_root" apply --index \
    "$audit_implementation_patch"
  audit_implementation_replay_count=$((audit_implementation_replay_count + 1))
done
audit_implementation_replay_count=10
audit_mutation_clean_tree="$(git -C "$audit_mutation_replay_root" \
  write-tree)"
audit_mutation_clean_plugin="$(git -C "$audit_mutation_replay_root" \
  ls-tree "$audit_mutation_clean_tree" oracle/plugin | awk '{print $3}')"
test "$audit_mutation_clean_plugin" = \
  5a7db9d1e661dd97bd6a939d375dd2008506f679
git -C "$audit_mutation_replay_root" diff --quiet
audit_mutation_clean_status="$audit_root/mutation-replay-clean.status"
audit_require_absent_path "$audit_mutation_clean_status"
git -C "$audit_mutation_replay_root" status --porcelain=v1 \
  --untracked-files=all > "$audit_mutation_clean_status"
audit_mutation_replay_count=0
while IFS='|' read -r mutation_id mutation_patch_sha \
    mutation_patch_lines mutation_patch_bytes mutation_target \
    mutation_parent_sha mutation_parent_blob mutation_result_sha \
    mutation_result_blob mutation_plugin_tree mutation_cohort \
    mutation_failure; do
  mutation_patch="$audit_root/$mutation_id.body"
  audit_require_owned_regular "$mutation_patch"
  test "$(audit_sha256 "$audit_mutation_replay_root/$mutation_target")" = \
    "$mutation_parent_sha"
  test "$(git -C "$audit_mutation_replay_root" hash-object \
    "$mutation_target")" = "$mutation_parent_blob"
  git -C "$audit_mutation_replay_root" apply --check --index \
    "$mutation_patch"
  git -C "$audit_mutation_replay_root" apply --index "$mutation_patch"
  test "$(git -C "$audit_mutation_replay_root" diff --cached \
    --name-only "$audit_mutation_clean_tree" --)" = "$mutation_target"
  test "$(audit_sha256 "$audit_mutation_replay_root/$mutation_target")" = \
    "$mutation_result_sha"
  test "$(git -C "$audit_mutation_replay_root" hash-object \
    "$mutation_target")" = "$mutation_result_blob"
  audit_mutated_tree="$(git -C "$audit_mutation_replay_root" write-tree)"
  test "$(git -C "$audit_mutation_replay_root" ls-tree \
    "$audit_mutated_tree" oracle/plugin | awk '{print $3}')" = \
    "$mutation_plugin_tree"
  git -C "$audit_mutation_replay_root" apply --check --reverse --index \
    "$mutation_patch"
  git -C "$audit_mutation_replay_root" apply --reverse --index \
    "$mutation_patch"
  test "$(git -C "$audit_mutation_replay_root" write-tree)" = \
    "$audit_mutation_clean_tree"
  git -C "$audit_mutation_replay_root" diff --quiet
  test "$(audit_sha256 "$audit_mutation_replay_root/$mutation_target")" = \
    "$mutation_parent_sha"
  test "$(git -C "$audit_mutation_replay_root" hash-object \
    "$mutation_target")" = "$mutation_parent_blob"
  test "$(git -C "$audit_mutation_replay_root" ls-tree \
    "$audit_mutation_clean_tree" oracle/plugin | awk '{print $3}')" = \
    "$audit_mutation_clean_plugin"
  audit_mutation_after_status="$audit_root/$mutation_id.restored.status"
  audit_require_absent_path "$audit_mutation_after_status"
  git -C "$audit_mutation_replay_root" status --porcelain=v1 \
    --untracked-files=all > "$audit_mutation_after_status"
  cmp -s "$audit_mutation_clean_status" "$audit_mutation_after_status"
  audit_mutation_replay_count=$((audit_mutation_replay_count + 1))
done < "$audit_mutation_manifest"
audit_mutation_replay_count=28
audit_proof_patch_replay_count=0
while IFS='|' read -r audit_proof_id audit_proof_target \
    audit_proof_result_blob; do
  audit_proof_patch="$audit_root/$audit_proof_id.body"
  audit_require_owned_regular "$audit_proof_patch"
  git -C "$audit_mutation_replay_root" apply --check --index \
    "$audit_proof_patch"
  git -C "$audit_mutation_replay_root" apply --index "$audit_proof_patch"
  test "$(git -C "$audit_mutation_replay_root" diff --cached \
    --name-only "$audit_mutation_clean_tree" --)" = "$audit_proof_target"
  test "$(git -C "$audit_mutation_replay_root" hash-object \
    "$audit_proof_target")" = "$audit_proof_result_blob"
  if test "$audit_proof_id" = T5M28-EXPORT-HOOK; then
    audit_proof_tree="$(git -C "$audit_mutation_replay_root" write-tree)"
    test "$(git -C "$audit_mutation_replay_root" ls-tree \
      "$audit_proof_tree" oracle/plugin | awk '{print $3}')" = \
      f4e650335dbe5f6656ee19fefafd8d5bad367f73
  fi
  git -C "$audit_mutation_replay_root" apply --check --reverse --index \
    "$audit_proof_patch"
  git -C "$audit_mutation_replay_root" apply --reverse --index \
    "$audit_proof_patch"
  test "$(git -C "$audit_mutation_replay_root" write-tree)" = \
    "$audit_mutation_clean_tree"
  git -C "$audit_mutation_replay_root" diff --quiet
  audit_proof_after_status="$audit_root/$audit_proof_id.restored.status"
  audit_require_absent_path "$audit_proof_after_status"
  git -C "$audit_mutation_replay_root" status --porcelain=v1 \
    --untracked-files=all > "$audit_proof_after_status"
  cmp -s "$audit_mutation_clean_status" "$audit_proof_after_status"
  audit_proof_patch_replay_count=$((audit_proof_patch_replay_count + 1))
done <<'TASK5_AUDIT_PROOF_PATCHES'
REJECTED-T5M20-SCOPE|oracle/plugin/Core/PassiveDriver.cs|f2520f7a688910f95004d1edfc7fadc1008cda23
REJECTED-T5M23-BROAD|oracle/plugin/Core/PassiveDriver.cs|18aa7e38a8b68101e4d7c29b7fc605b67c9bd02d
T5M28-EXPORT-HOOK|oracle/plugin/tests/PassiveDriverTerminalTests.cs|0f057da9dd9fd4396404c2d3c4afcca4fafa98cf
TASK5_AUDIT_PROOF_PATCHES
audit_proof_patch_replay_count=3
printf 'mutation-replay=PASS implementation=10 canonical=28 rejected=2 hook=1 proof-patches=3\n'

audit_bootstrap="$audit_root/task5-bootstrap.sh"
audit_require_absent_path "$audit_bootstrap"
test "$(awk -v wanted="$audit_bootstrap_begin" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
test "$(awk -v wanted="$audit_bootstrap_end" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
audit_bootstrap_first="$(awk -v wanted="$audit_bootstrap_begin" \
  '$0 == wanted {print NR}' "$audit_plan")"
audit_bootstrap_last="$(awk -v wanted="$audit_bootstrap_end" \
  '$0 == wanted {print NR}' "$audit_plan")"
test "$(sed -n "$((audit_bootstrap_first + 1))p" "$audit_plan")" = '```bash'
test "$(sed -n "$((audit_bootstrap_last - 1))p" "$audit_plan")" = '```'
awk -v first="$((audit_bootstrap_first + 1))" \
  -v last="$((audit_bootstrap_last - 1))" \
  'NR > first && NR < last {print}' "$audit_plan" > "$audit_bootstrap"
audit_require_owned_regular "$audit_bootstrap"
/bin/bash --noprofile --norc -n "$audit_bootstrap"
chmod 400 "$audit_bootstrap"
audit_require_owned_regular "$audit_bootstrap"
test "$(stat -f '%Lp' "$audit_bootstrap")" = 400

audit_bootstrap_probe_library="$audit_root/task5-bootstrap-probe-library.sh"
audit_require_absent_path "$audit_bootstrap_probe_library"
: > "$audit_bootstrap_probe_library"
for audit_bootstrap_probe_function in \
    task5_bootstrap_require_owned_regular \
    task5_bootstrap_require_coordination_reference \
    task5_bootstrap_require_no_nul_file \
    task5_bootstrap_read_coordination_reference_file \
    task5_bootstrap_receipt_value; do
  awk -v signature="$audit_bootstrap_probe_function() {" '
    $0 == signature {inside=1}
    inside {print}
    inside && $0 == "}" {exit}
  ' "$audit_bootstrap" >> "$audit_bootstrap_probe_library"
done
audit_require_owned_regular "$audit_bootstrap_probe_library"
/bin/bash --noprofile --norc -n "$audit_bootstrap_probe_library"
(
  . "$audit_bootstrap_probe_library"
  if task5_bootstrap_require_coordination_reference 'bad@ref'; then
    exit 1
  fi
  test "$(task5_bootstrap_read_coordination_reference_file \
    "$audit_fail_closed_valid_reference")" = reviewer-r2
  if task5_bootstrap_read_coordination_reference_file \
      "$audit_fail_closed_reference" >/dev/null 2>&1; then
    exit 1
  fi
  if task5_bootstrap_receipt_value "$audit_fail_closed_receipt" \
      implementation-actor-reference >/dev/null 2>&1; then
    exit 1
  fi
)
printf 'fail-closed-bootstrap-probes=PASS raw-ingresses=2\n'

audit_runtime_symbols="$audit_root/runtime-symbols.report"
audit_require_absent_path "$audit_runtime_symbols"
awk '
  {
    line = $0
    while (match(line, /task5_[A-Za-z0-9_]+/)) {
      name = substr(line, RSTART, RLENGTH)
      before = substr(line, 1, RSTART - 1)
      after = substr(line, RSTART + RLENGTH)
      if (after ~ /^[ \t]*[(][)][ \t]*[({]/)
        defined[name] = 1
      else if (before ~ /[$][(]$/ ||
          before ~ /(^|[;|&({!])[ \t]*$/ ||
          before ~ /(^|[;|&({!])[ \t]*(if|then|do)[ \t]+$/)
        called[name] = 1
      line = after
    }
  }
  END {
    bad = 0
    for (name in called) {
      if (!(name in defined)) {
        print "undefined=" name
        bad = 1
      }
    }
    if (bad)
      exit 1
    print "runtime-symbols=PASS"
  }
' "$audit_runtime" | sort > "$audit_runtime_symbols"
test "$(cat "$audit_runtime_symbols")" = 'runtime-symbols=PASS'

audit_checker="$audit_root/task5-plan-audit.sh"
audit_require_absent_path "$audit_checker"
test "$(awk -v wanted="$audit_checker_begin" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
test "$(awk -v wanted="$audit_checker_end" \
  '$0 == wanted {n++} END {print n + 0}' "$audit_plan")" = 1
audit_checker_first="$(awk -v wanted="$audit_checker_begin" \
  '$0 == wanted {print NR}' "$audit_plan")"
audit_checker_last="$(awk -v wanted="$audit_checker_end" \
  '$0 == wanted {print NR}' "$audit_plan")"
test "$(sed -n "$((audit_checker_first + 1))p" "$audit_plan")" = '```bash'
test "$(sed -n "$((audit_checker_last - 1))p" "$audit_plan")" = '```'
awk -v first="$((audit_checker_first + 1))" \
  -v last="$((audit_checker_last - 1))" \
  'NR > first && NR < last {print}' "$audit_plan" > "$audit_checker"
audit_require_owned_regular "$audit_checker"
/bin/bash --noprofile --norc -n "$audit_checker"
audit_require_owned_regular "$0"
cmp -s "$audit_checker" "$0"

audit_plan_sha="$(audit_sha256 "$audit_plan")"
audit_checker_sha="$(audit_sha256 "$audit_checker")"
audit_runtime_sha="$(audit_sha256 "$audit_runtime")"
audit_bootstrap_sha="$(audit_sha256 "$audit_bootstrap")"
audit_mutation_manifest_sha="$(audit_sha256 "$audit_mutation_manifest")"
audit_core_manifest="$audit_root/core.manifest"
audit_require_absent_path "$audit_core_manifest"
printf 'plan|%s|%s|%s\n' "$audit_plan_sha" \
  "$(wc -l < "$audit_plan" | tr -d '[:space:]')" \
  "$(wc -c < "$audit_plan" | tr -d '[:space:]')" > "$audit_core_manifest"
printf 'checker|%s|%s|%s\n' "$audit_checker_sha" \
  "$(wc -l < "$audit_checker" | tr -d '[:space:]')" \
  "$(wc -c < "$audit_checker" | tr -d '[:space:]')" >> "$audit_core_manifest"
printf 'runtime|%s|%s|%s\n' "$audit_runtime_sha" \
  "$(wc -l < "$audit_runtime" | tr -d '[:space:]')" \
  "$(wc -c < "$audit_runtime" | tr -d '[:space:]')" >> "$audit_core_manifest"
printf 'bootstrap|%s|%s|%s\n' "$audit_bootstrap_sha" \
  "$(wc -l < "$audit_bootstrap" | tr -d '[:space:]')" \
  "$(wc -c < "$audit_bootstrap" | tr -d '[:space:]')" >> "$audit_core_manifest"
printf 'canonical-mutations|%s|28|%s\n' "$audit_mutation_manifest_sha" \
  "$(wc -c < "$audit_mutation_manifest" | tr -d '[:space:]')" \
  >> "$audit_core_manifest"
printf 'fences|bash=%s|diff=41|implementation=10|canonical=28|rejected=2|hook=1|probe=1\n' \
  "$audit_bash_count" >> "$audit_core_manifest"
cat "$audit_catalog" >> "$audit_core_manifest"
audit_core_sha="$(audit_sha256 "$audit_core_manifest")"

case "$audit_mode" in
  candidate)
    test "$(git -C "$audit_execution_root" rev-parse HEAD)" = \
      "$audit_expected_parent"
    test "$(git -C "$audit_execution_root" status --porcelain=v1 \
      --untracked-files=all)" = "?? $audit_plan_path"
    audit_require_owned_regular "$audit_target"
    cmp -s "$audit_target" "$audit_plan"
    test "$(audit_sha256 "$audit_target")" = "$audit_candidate_sha" ;;
  committed)
    test "$(git -C "$audit_execution_root" rev-parse HEAD)" = "$P"
    test -z "$(git -C "$audit_execution_root" status --porcelain=v1 \
      --untracked-files=all)" ;;
esac

printf 'mode=%s\n' "$audit_mode"
printf 'plan-sha256=%s\n' "$audit_plan_sha"
printf 'checker-sha256=%s\n' "$audit_checker_sha"
printf 'runtime-sha256=%s\n' "$audit_runtime_sha"
printf 'bootstrap-sha256=%s\n' "$audit_bootstrap_sha"
printf 'canonical-mutation-manifest-sha256=%s\n' \
  "$audit_mutation_manifest_sha"
printf 'bootstrap-path=%s\n' "$audit_bootstrap"
printf 'core-manifest-sha256=%s\n' "$audit_core_sha"
printf 'artifacts=42 diff-fences=41 bash-fences=%s\n' "$audit_bash_count"
printf 'audit-evidence=%s\n' "$audit_root"
```
<!-- TASK5-PLAN-AUDIT-END -->

The only preapproval shell transaction is exact and ordered: from D, extract
the checker bytes between the authenticated checker markers into a fresh
external `candidate_checker`, set `plan_path` to the exact absolute plan path,
and invoke the candidate command below; record its complete stdout; stage only
the plan; commit only P with subject
`docs: plan Task 5 passive driver completion`, hooks disabled and signing off;
pin `user.useConfigOnly=true`, `user.name=jess`, and
`user.email=optimistindustries@gmail.com` for that commit;
assign `P="$(git rev-parse HEAD)"`; extract the checker again only with
`git show "$P:docs/superpowers/plans/2026-08-07-task-5-passive-driver.md"`
into a fresh `committed_checker`; require byte equality with the candidate
checker; and invoke the committed command below. Each checker invocation must
begin at process start with the literal minimal `/usr/bin/env -i` environment;
a plain or inherited-shell `/bin/bash` launch is unauthorized because
`BASH_ENV` and exported functions run before the checker can inspect them.
Candidate and committed plan/checker/runtime/core identities must match
exactly. The non-shell P-review phase below then freezes the package before
dispatch and stops for explicit user approval. No Task 5 execution evidence
namespace exists before that approval.

<!-- TASK5-PREAPPROVAL-CHECKER-LAUNCHES-BEGIN -->
```text
/usr/bin/env -i \
  PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C LANG=C \
  HOME=/private/tmp TMPDIR=/private/tmp \
  GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
  GIT_TERMINAL_PROMPT=0 \
  /bin/bash --noprofile --norc "$candidate_checker" candidate "$plan_path"

/usr/bin/env -i \
  PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C LANG=C \
  HOME=/private/tmp TMPDIR=/private/tmp \
  GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
  GIT_TERMINAL_PROMPT=0 \
  /bin/bash --noprofile --norc "$committed_checker" committed "$P"
```
<!-- TASK5-PREAPPROVAL-CHECKER-LAUNCHES-END -->

Those two invocations are the only prescribed candidate/committed checker
launches before approval. The checker cannot self-protect after shell startup;
the literal clean process boundary is mandatory in addition to its internal
environment assertions and negative control.

<!-- TASK5-P-REVIEW-COORDINATION-BEGIN -->
Before either P review is dispatched, the non-shell coordinator performs this
closed preapproval sequence:

1. Choose the implementation actor and two lane reviewer references, validate
   all three with the exact report-safe coordination-reference contract above,
   and require the spec and quality references distinct from each other and
   from the actor.
2. Freeze one fresh preapproval P-review coordination package outside the
   repository. It is coordination material, not the Task 5 execution evidence namespace. Its directory is owned, non-symlink, and mode 500; its eight
   owned regular, non-symlink, mode-400 files are exactly `package.identity`,
   `plan.md`, `checker.sh`, `runtime.sh`, `bootstrap.sh`,
   `canonical-mutations.manifest`, `core.manifest`, and `manifest.sha256`.
   `package.identity` has the exact 14 fields specified below, including the
   implementation actor and two lane reviewer references. The manifest covers
   each of the other seven files exactly once using canonical relative paths.
3. Dispatch that same immutable package to both independent P lanes. Each
   dispatch supplies its exact manifest SHA-256 and assigned reviewer reference.
   Each response binds that package SHA, its assigned reviewer reference, the
   actor reference, an independently derived verdict/finding set, and exact
   reviewer-derived Minor dispositions. The non-shell coordinator byte-copies
   each response into an immutable response record and creates its exact
   six-field identity; it does not rewrite reviewer bytes or conclusions.
4. After both sealed P responses and explicit user approval, byte-copy that
   exact unchanged package, both exact responses/identities, and the approval
   bytes/reference into the final authority bundle. Do not rebuild, regenerate,
   or redispatch the P package. The authority receipt binds the same package
   manifest SHA, response SHAs, actor/lane references, resolved P, checker/core
   identities, amendment ID, and approval records.
<!-- TASK5-P-REVIEW-COORDINATION-END -->

The non-shell coordination channel must then finalize exactly one fixed
`/private/tmp/ssr-task5-authority-bundle` directory. It is an immutable
coordination receipt, not a cryptographic signature. It is created only after
the committed-mode audit and two independent P reviews have completed and the
user has explicitly approved implementation. Every directory is owned, mode
500, and non-symlink; every file is owned, mode 400, regular, and non-symlink.
Its outer `manifest.sha256` covers every other file and has a SHA-256 returned
through the same non-shell handoff. The bundle contains exactly these required
records plus the files authenticated by the nested review-package manifest:

- `authority.receipt`, with unique `version=1`, `P`, plan/checker/runtime/core-
  manifest/bootstrap/canonical-mutation-manifest-sha256, P-review-package manifest SHA-256, both response SHA-256
  values, `amendment=U-T5-C53-INTERMEDIATE-READY-01`, approval text/reference
  SHA-256 fields, and report-safe stable `implementation-actor-reference`,
  `spec-reviewer-reference`, and `quality-reviewer-reference` fields; this
  fixed structured receipt and every parsed identity are NUL-free before any
  unique-field extraction;
- `implementation-approval.txt`, the exact user approval bytes, which contain
  exactly one `P=<resolved-P>`, `AMENDMENT=U-T5-C53-INTERMEDIATE-READY-01`,
  `IMPLEMENTATION-ACTOR-REFERENCE=<receipt-value>`, and `DECISION=APPROVE` line;
- `implementation-approval.reference`, exactly one stable non-shell
  coordination reference satisfying the same ASCII-safe/no-standalone-R
  predicate as every actor and reviewer reference, stored as exact raw bytes:
  one final-LF-terminated line, no NUL or other hidden/extra byte, and byte
  count equal to the validated reference length plus one;
- a complete self-contained `P-review-package/` with exactly
  `P-review-package/package.identity`, `P-review-package/plan.md`,
  `P-review-package/checker.sh`, `P-review-package/runtime.sh`,
  `P-review-package/bootstrap.sh`,
  `P-review-package/canonical-mutations.manifest`,
  `P-review-package/core.manifest`, and its own
  `P-review-package/manifest.sha256`; `package.identity` binds P, D, plan path,
  the amendment ID, and every copied core identity to the receipt through
  unique `format=task5-plan-review-v1`, `P`, `D`, `plan-path`, `plan-sha256`,
  `checker-sha256`, `runtime-sha256`, `bootstrap-sha256`,
  `canonical-mutation-manifest-sha256`, `core-manifest-sha256`, `amendment`,
  `implementation-actor-reference`, `spec-reviewer-reference`, and
  `quality-reviewer-reference` fields;
- `P.spec.response.md`, `P.quality.response.md`, and their corresponding
  `.identity` files, each binding the same P package, complete response bytes,
  its lane's report-safe stable reviewer reference, the implementation-actor
  reference, and actual verdict. The two reviewer references must be distinct
  from each other and from the implementation actor/controller reference.
  Both verdicts must be `APPROVE` with zero Critical and Important findings;
  actual nonnegative Minor counts and their exact dispositions remain
  reviewer-derived.

After approval, the one-time bootstrap below copies and seals that bundle and
creates the sole Task 5 evidence namespace. Its first executable lifecycle call
is
`task5_clean_call plan-postcommit <recorded-plan-sha256>
<recorded-checker-sha256> <authority-bundle-manifest-sha256>`; that action
re-extracts and executes the identical committed checker, then authenticates
every authority receipt binding before Task 0. Any mismatch aborts and retires
the namespace.

### Runtime protocol: authenticated patches, RED evidence, gates, and mutation clones

All commands in this section target Apple Bash 3.2. The runtime fence is a
private function library plus an authenticated, explicit-allowlist dispatcher;
never source it or call a library function directly. Keep the bootstrap shell
alive and perform every post-bootstrap executable action through
`task5_clean_call <allowlisted-action> ...`, which starts a fresh `env -i`
controller and reauthenticates the physical worktree, branch, P alias, driver,
and evidence root before dispatch. `repo_root` always means the
physical absolute Git top level. A caller obtains `task5_evidence_root` by
the one-time bootstrap (whose creation contract is also encoded by
`task5_init_evidence_root`). Never create or switch to a second evidence root
after the clean controller launch. No function writes into the frozen Task 4.2
evidence namespace.

Every postbootstrap formal response keeps its reviewer-derived Minor count. If
the verdict records `MINOR=N`, the response contains exactly that many nonempty
`MINOR-DISPOSITION: ` lines and none when `N=0`; their contents remain wholly
reviewer-derived. Sealing authenticates package/schema/bytes only, while the
later transition gate validates the applicable outcome and these dispositions.
Before `freeze-review-package <target>`, the non-shell coordinator writes exactly
one safe reference line to each fixed
`review-inbox/<target>.spec.reviewer-reference` and
`review-inbox/<target>.quality.reviewer-reference` path. Each assignment record
is owned regular, non-symlink, mode 400, and final-LF-terminated, contains no CR
or extra byte, and has exactly one report-safe coordination reference. The
controller applies the same ASCII-safe/no-standalone-R predicate used for the
authority actor, P reviewers, and approval reference, freezes both assignments
into the package identity, requires them distinct from each other and from the
authority bundle's implementation actor/controller reference, and later binds
each response and sealed identity to the assigned reference. These are
tamper-evident coordination references, not cryptographic identity claims; a
reference may be reused for the same lane at another checkpoint unless a future
design explicitly forbids it.

Every postbootstrap `checkpoint.identity` contains unique
`implementation-actor-reference`, `spec-reviewer-reference`, and
`quality-reviewer-reference` fields. Each pending and sealed response contains
exactly one `REVIEWER-REFERENCE: <assigned-lane-reference>` and one
`IMPLEMENTATION-ACTOR-REFERENCE: <authority-value>` line. Its six-line sealed
identity contains unique `checkpoint`, `lane`, `package-sha256`,
`response-sha256`, `reviewer-reference`, and
`implementation-actor-reference` fields. The package manifest authenticates the
package identity; the response SHA authenticates those response fields; every
transition and final audit revalidates the complete binding.

Patch bodies in the committed plan blob must be byte-for-byte output from
`git diff --cached --binary --full-index --no-ext-diff`. Each marker pair
contains exactly one `~~~diff` fence: the opening fence is the line immediately
after the begin marker and its `~~~` close is the line immediately before the
end marker. For patch ID `C51-TESTS`, for example, the exact marker lines are
`<!-- TASK5-PATCH-BEGIN:C51-TESTS -->` and
`<!-- TASK5-PATCH-END:C51-TESTS -->`. The extraction function takes the
committed plan OID and plan path at execution time; there is no prospective
commit placeholder.

Bootstrap trust setup itself begins inside a clean environment. From the
physical Task 5 worktree, the first bootstrap command must be the following
literal `/usr/bin/env -i` invocation with the authenticated committed-bootstrap
path/SHA-256 and exact authority-manifest SHA-256 from the non-shell handoff
substituted for the three angle-bracket tokens. Do not run an assignment,
command substitution, shell helper, Git command, or trust check first.
`BASH_ENV`, `ENV`, exported functions, aliases, and the inherited `PATH` are
therefore absent before any trust decision. The fixed clean validator
authenticates the committed-mode checker's extracted bootstrap bytes, then a
second `env -i` executes them as the sole rcfile of the persistent interactive
Bash used for every later `task5_clean_call`; no function export is involved:

```bash
/usr/bin/env -i \
  PATH=/usr/bin:/bin LC_ALL=C LANG=C HOME=/private/tmp HISTFILE=/dev/null \
  TMPDIR=/private/tmp \
  GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 \
  TASK5_BOOTSTRAP_PATH=<authenticated-committed-bootstrap-path> \
  TASK5_BOOTSTRAP_SHA256=<authenticated-committed-bootstrap-sha256> \
  TASK5_AUTHORITY_BUNDLE_SOURCE=/private/tmp/ssr-task5-authority-bundle \
  TASK5_AUTHORITY_BUNDLE_SHA256=<authority-bundle-manifest-sha256> \
  /bin/bash --noprofile --norc -c '
    set -euo pipefail
    test -z "${BASH_ENV+x}"
    test -z "${ENV+x}"
    test -z "$(declare -F)"
    test "${#TASK5_BOOTSTRAP_SHA256}" = 64
    case "$TASK5_BOOTSTRAP_SHA256" in *[!0123456789abcdef]*) exit 1 ;; esac
    test "${#TASK5_AUTHORITY_BUNDLE_SHA256}" = 64
    case "$TASK5_AUTHORITY_BUNDLE_SHA256" in *[!0123456789abcdef]*) exit 1 ;; esac
    test "$TASK5_AUTHORITY_BUNDLE_SOURCE" = /private/tmp/ssr-task5-authority-bundle
    test -f "$TASK5_BOOTSTRAP_PATH"
    test ! -L "$TASK5_BOOTSTRAP_PATH"
    test "$(/usr/bin/stat -f %u "$TASK5_BOOTSTRAP_PATH")" = "$(/usr/bin/id -u)"
    test "$(/usr/bin/stat -f %Lp "$TASK5_BOOTSTRAP_PATH")" = 400
    test "$(/usr/bin/shasum -a 256 "$TASK5_BOOTSTRAP_PATH" | /usr/bin/cut -d " " -f1)" = "$TASK5_BOOTSTRAP_SHA256"
    test -d "$TASK5_AUTHORITY_BUNDLE_SOURCE"
    test ! -L "$TASK5_AUTHORITY_BUNDLE_SOURCE"
    test "$(/usr/bin/shasum -a 256 "$TASK5_AUTHORITY_BUNDLE_SOURCE/manifest.sha256" | /usr/bin/cut -d " " -f1)" = "$TASK5_AUTHORITY_BUNDLE_SHA256"
    exec /usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C LANG=C \
      HOME=/private/tmp HISTFILE=/dev/null TMPDIR=/private/tmp \
      GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
      GIT_TERMINAL_PROMPT=0 \
      TASK5_BOOTSTRAP_PATH="$TASK5_BOOTSTRAP_PATH" \
      TASK5_BOOTSTRAP_SHA256="$TASK5_BOOTSTRAP_SHA256" \
      TASK5_AUTHORITY_BUNDLE_SOURCE="$TASK5_AUTHORITY_BUNDLE_SOURCE" \
      TASK5_AUTHORITY_BUNDLE_SHA256="$TASK5_AUTHORITY_BUNDLE_SHA256" \
      /bin/bash --noprofile --rcfile "$TASK5_BOOTSTRAP_PATH" -i
  '
```

The committed-mode checker extracts the following marked rcfile, sets it mode
400, and returns its absolute path and SHA-256. The clean validator above is the
only authorized way to execute it. The initial bootstrap may then resolve the physical worktree, create the external
evidence root, copy/authenticate the authority bundle, and materialize/syntax-
check/hash the generated controller. All subsequent authenticated commands use
their own clean controller environments; exporting over an inherited shell is
not an equivalent gate:

<!-- TASK5-BOOTSTRAP-BEGIN -->
```bash
set -euo pipefail
case "$-" in
  *i*) ;;
  *) exit 64 ;;
esac
test -z "${BASH_ENV+x}"
test -z "${ENV+x}"
test "$(declare -F | wc -l | tr -d '[:space:]')" = 0
test -z "$(alias -p)"
test "$(type -t git)" = file
test "$(command -v git)" = /usr/bin/git
test "$(type -t shasum)" = file
test "$(command -v shasum)" = /usr/bin/shasum
test "${TASK5_BOOTSTRAP_PATH-}" = \
  "$(cd "${TASK5_BOOTSTRAP_PATH%/*}" && pwd -P)/${TASK5_BOOTSTRAP_PATH##*/}"
test -f "$TASK5_BOOTSTRAP_PATH"
test ! -L "$TASK5_BOOTSTRAP_PATH"
test "$(stat -f '%Lp' "$TASK5_BOOTSTRAP_PATH")" = 400
test "$(shasum -a 256 "$TASK5_BOOTSTRAP_PATH" | awk '{print $1}')" = \
  "$TASK5_BOOTSTRAP_SHA256"
test "$(cd "$(/bin/pwd -P)" && /bin/pwd -P)" = \
  /Users/jlsor/Documents/Research/SSR/.worktrees/ssr-oracle-passive-trace
test "$(/usr/bin/env | /usr/bin/cut -d= -f1 | /usr/bin/sort)" = \
'GIT_CONFIG_GLOBAL
GIT_CONFIG_NOSYSTEM
GIT_TERMINAL_PROMPT
HOME
HISTFILE
LANG
LC_ALL
PATH
PWD
SHLVL
TASK5_AUTHORITY_BUNDLE_SHA256
TASK5_AUTHORITY_BUNDLE_SOURCE
TASK5_BOOTSTRAP_PATH
TASK5_BOOTSTRAP_SHA256
TMPDIR
_'
task5_authority_source="$TASK5_AUTHORITY_BUNDLE_SOURCE"
task5_authority_expected_sha="$TASK5_AUTHORITY_BUNDLE_SHA256"
task5_bootstrap_path="$TASK5_BOOTSTRAP_PATH"
task5_bootstrap_sha="$TASK5_BOOTSTRAP_SHA256"
unset TASK5_AUTHORITY_BUNDLE_SOURCE TASK5_AUTHORITY_BUNDLE_SHA256 \
  TASK5_BOOTSTRAP_PATH TASK5_BOOTSTRAP_SHA256
set -E
umask 077
set -C

task5_evidence_root=
task5_bootstrap_abort() {
  task5_abort_status="$1"
  trap - ERR
  if test -n "${task5_evidence_root-}"; then
    task5_abort_namespace="$task5_evidence_root"
    if test "$(type -t task5_bootstrap_retire_namespace)" = function && \
        test ! -e "${retired_path-}" && test ! -L "${retired_path-}"; then
      set +e
      (
        set -e
        task5_bootstrap_retire_namespace "$task5_abort_status" \
          bootstrap 000000
      )
      task5_retire_attempt_status=$?
      set -e
      if test "$task5_retire_attempt_status" != 0; then
        printf 'Task 5 namespace retirement itself failed with status %s; preserve every byte and stop.\n' \
          "$task5_retire_attempt_status" >&2
      fi
    fi
  else
    task5_abort_namespace=UNALLOCATED
  fi
  printf 'Task 5 bootstrap/controller aborted with status %s. Preserve evidence namespace %s; do not reuse it.\n' \
    "$task5_abort_status" "$task5_abort_namespace" >&2
  exit "$task5_abort_status"
}
trap 'task5_bootstrap_abort "$?"' ERR

task5_bootstrap_require_absent_path() {
  test "$#" = 1 || return 1
  test ! -e "$1" || return 1
  test ! -L "$1" || return 1
  return 0
}

task5_bootstrap_require_owned_regular() {
  test "$#" = 1 || return 1
  test -f "$1" || return 1
  test ! -L "$1" || return 1
  test "$(stat -f '%u' "$1")" = "$(id -u)" || return 1
  return 0
}

task5_bootstrap_require_owned_directory() {
  test "$#" = 2
  test -d "$1"
  test ! -L "$1"
  test "$(stat -f '%Lp' "$1")" = "$2"
  test "$(stat -f '%u' "$1")" = "$(id -u)"
}

task5_bootstrap_require_sha256() {
  test "$#" = 1 || return 1
  test "${#1}" = 64 || return 1
  case "$1" in
    *[!0123456789abcdef]*) return 1 ;;
  esac
  return 0
}

task5_bootstrap_require_coordination_reference() {
  test "$#" = 1 || return 1
  test -n "$1" || return 1
  case "$1" in
    *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:/-]*) \
      return 1 ;;
  esac
# TASK5-COORDINATION-REFERENCE-STANDALONE-R-DEFENSE-V1
  if printf '%s\n' "$1" | awk '
    {
      lower = tolower($0)
      if (lower ~ /(^|[^a-z0-9])r([^a-z0-9]|$)/)
        found = 1
    }
    END {exit(found ? 0 : 1)}
  '; then
    return 1
  fi
  return 0
}

task5_bootstrap_require_no_nul_file() {
  test "$#" = 1 || return 1
  task5_bootstrap_require_owned_regular "$1" || return 1
# TASK5-STRUCTURED-TEXT-NUL-DEFENSE-V1
  if od -An -tu1 -v "$1" | awk '
    {
      for (field = 1; field <= NF; field++)
        if ($field == 0)
          found = 1
    }
    END {exit(found ? 0 : 1)}
  '; then
    return 1
  fi
  return 0
}

task5_bootstrap_read_coordination_reference_file() {
  test "$#" = 1 || return 1
  task5_bootstrap_require_owned_regular "$1" || return 1
  test "$(stat -f '%Lp' "$1")" = 400 || return 1
  test "$(wc -l < "$1" | tr -d '[:space:]')" = 1 || return 1
  test "$(tail -c 1 "$1" | od -An -tu1 | tr -d '[:space:]')" = 10 || \
    return 1
  task5_bootstrap_reference_value="$(cat "$1")" || return 1
  task5_bootstrap_require_coordination_reference \
    "$task5_bootstrap_reference_value" || return 1
  test "$(wc -c < "$1" | tr -d '[:space:]')" = \
    "$(( ${#task5_bootstrap_reference_value} + 1 ))" || return 1
  printf '%s\n' "$task5_bootstrap_reference_value"
}

task5_bootstrap_require_independent_reviewer_references() {
  test "$#" = 3
  task5_bootstrap_actor_reference="$1"
  task5_bootstrap_spec_reference="$2"
  task5_bootstrap_quality_reference="$3"
  task5_bootstrap_require_coordination_reference \
    "$task5_bootstrap_actor_reference" || return 1
  task5_bootstrap_require_coordination_reference \
    "$task5_bootstrap_spec_reference" || return 1
  task5_bootstrap_require_coordination_reference \
    "$task5_bootstrap_quality_reference" || return 1
  test "$task5_bootstrap_spec_reference" != \
    "$task5_bootstrap_quality_reference" || return 1
  test "$task5_bootstrap_spec_reference" != \
    "$task5_bootstrap_actor_reference" || return 1
  test "$task5_bootstrap_quality_reference" != \
    "$task5_bootstrap_actor_reference" || return 1
}

task5_bootstrap_require_minor_dispositions() (
  set -euo pipefail
  test "$#" = 1
  task5_bootstrap_response_path="$1"
  task5_bootstrap_verdict="$(grep '^VERDICT:' \
    "$task5_bootstrap_response_path")"
  task5_bootstrap_minor_count="$(printf '%s\n' "$task5_bootstrap_verdict" | \
    sed -E 's/^.* MINOR=([0-9]+)$/\1/')"
  case "$task5_bootstrap_minor_count" in
    ''|*[!0123456789]*) return 1 ;;
  esac
  task5_bootstrap_disposition_count="$(awk \
    '/^MINOR-DISPOSITION: .+/ {n++} END {print n + 0}' \
    "$task5_bootstrap_response_path")"
  task5_bootstrap_disposition_prefix_count="$(awk \
    '/^MINOR-DISPOSITION:/ {n++} END {print n + 0}' \
    "$task5_bootstrap_response_path")"
  test "$task5_bootstrap_disposition_prefix_count" = \
    "$task5_bootstrap_disposition_count"
  test "$task5_bootstrap_disposition_count" = \
    "$task5_bootstrap_minor_count"
)

task5_bootstrap_verify_manifest_root() {
  test "$#" = 3
  task5_verify_root="$1"
  task5_verify_manifest="$2"
  task5_verify_expected_sha="$3"
  task5_bootstrap_require_owned_directory "$task5_verify_root" 500
  task5_bootstrap_require_owned_regular "$task5_verify_manifest"
  test "$(stat -f '%Lp' "$task5_verify_manifest")" = 400
  task5_bootstrap_require_sha256 "$task5_verify_expected_sha"
  test "$(shasum -a 256 "$task5_verify_manifest" | awk '{print $1}')" = \
    "$task5_verify_expected_sha"
  case "$task5_verify_manifest" in
    "$task5_verify_root"/*)
      task5_verify_manifest_relative="${task5_verify_manifest#"$task5_verify_root/"}" ;;
    *) return 1 ;;
  esac
  task5_verify_duplicate_paths="$(awk '
    {
      separator = index($0, "  ")
      if (!separator) { bad = 1; next }
      digest = substr($0, 1, separator - 1)
      relative = substr($0, separator + 2)
      if (length(digest) != 64 || digest !~ /^[0-9a-f]+$/) {
        bad = 1
        next
      }
      if (relative == "" || relative ~ /^\// || relative ~ /^\.\// ||
          relative == "." || relative == ".." || relative ~ /^\.\.\// ||
          relative ~ /\/\.\// || relative ~ /\/\.$/ ||
          relative ~ /\/\.\.\// || relative ~ /\/\.\.$/ ||
          relative ~ /\/\// || relative ~ /\/$/ ||
          relative ~ /[^0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._\/-]/) {
        bad = 1
        next
      }
      folded_relative = tolower(relative)
      if (seen[folded_relative]++) bad = 1
    }
    END {print bad + 0}
  ' "$task5_verify_manifest")"
  if test "$task5_verify_duplicate_paths" != 0; then
    printf 'manifest path is not canonical or contains duplicate relative paths\n' >&2
    return 1
  fi
  test -z "$(find "$task5_verify_root" -type l -print)"
  test -z "$(find "$task5_verify_root" ! -type d ! -type f -print)"
  task5_verify_entries=0
  while IFS='  ' read -r task5_verify_sha task5_verify_relative; do
    task5_bootstrap_require_sha256 "$task5_verify_sha"
    test -n "$task5_verify_relative"
    if test "$task5_verify_relative" = "$task5_verify_manifest_relative"; then
      printf 'manifest must not authenticate itself\n' >&2
      return 1
    fi
    case "$task5_verify_relative" in
      /*|..|../*|*/..|*/../*) return 1 ;;
    esac
    task5_verify_path="$task5_verify_root/$task5_verify_relative"
    task5_bootstrap_require_owned_regular "$task5_verify_path"
    test "$(stat -f '%Lp' "$task5_verify_path")" = 400
    test "$(shasum -a 256 "$task5_verify_path" | awk '{print $1}')" = \
      "$task5_verify_sha"
    task5_verify_entries=$((task5_verify_entries + 1))
  done < "$task5_verify_manifest"
  test "$task5_verify_entries" -gt 0
  test "$(find "$task5_verify_root" -type f | wc -l | tr -d '[:space:]')" = \
    "$((task5_verify_entries + 1))"
  find "$task5_verify_root" -type d -print | while IFS= read -r task5_verify_dir; do
    task5_bootstrap_require_owned_directory "$task5_verify_dir" 500
  done
}

task5_bootstrap_receipt_value() {
  test "$#" = 2 || return 1
  task5_bootstrap_require_no_nul_file "$1" || return 1
  test "$(awk -F= -v key="$2" '$1 == key {n++} END {print n + 0}' "$1")" = 1 || \
    return 1
  awk -F= -v key="$2" '$1 == key {sub(/^[^=]*=/, ""); print}' "$1"
}

task5_bootstrap_capture_repo_state() {
  test "$#" = 2
  task5_capture_root="$1"
  task5_capture_prefix="$2"
  task5_capture_porcelain="$task5_capture_prefix.porcelain"
  task5_capture_identity="$task5_capture_prefix.identity"
  task5_bootstrap_require_absent_path "$task5_capture_porcelain"
  task5_bootstrap_require_absent_path "$task5_capture_identity"
  git -C "$task5_capture_root" status --porcelain=v1 --untracked-files=all \
    > "$task5_capture_porcelain"
  task5_capture_porcelain_sha="$(shasum -a 256 "$task5_capture_porcelain" | \
    awk '{print $1}')"
  printf 'HEAD=%s\nindex-tree=%s\nbranch=%s\nporcelain-sha256=%s\n' \
    "$(git -C "$task5_capture_root" rev-parse HEAD)" \
    "$(git -C "$task5_capture_root" write-tree)" \
    "$(git -C "$task5_capture_root" symbolic-ref -q HEAD)" \
    "$task5_capture_porcelain_sha" > "$task5_capture_identity"
  task5_bootstrap_require_owned_regular "$task5_capture_porcelain"
  task5_bootstrap_require_owned_regular "$task5_capture_identity"
}

task5_bootstrap_retire_namespace() (
  trap - ERR
  set -euo pipefail
  umask 077
  test "$#" = 3
  task5_retire_status="$1"
  task5_retire_action="$2"
  task5_retire_ordinal="$3"
  task5_bootstrap_require_absent_path "$retired_path"
  task5_bootstrap_require_absent_path "$retired_manifest_path"
  task5_retire_porcelain="$task5_evidence_root/retired.porcelain"
  task5_bootstrap_require_absent_path "$task5_retire_porcelain"
  git -C "$execution_root" status --porcelain=v1 --untracked-files=all \
    > "$task5_retire_porcelain"
  task5_retire_porcelain_sha="$(shasum -a 256 "$task5_retire_porcelain" | \
    awk '{print $1}')"
  task5_retire_head="$(git -C "$execution_root" rev-parse HEAD)" || return 1
  task5_retire_tree="$(git -C "$execution_root" write-tree)" || return 1
  task5_retire_authority_sha="${authority_bundle_sha-$task5_authority_expected_sha}"
  printf 'status=%s\naction=%s\nordinal=%s\nP=%s\nHEAD=%s\nindex-tree=%s\nporcelain-sha256=%s\nauthority-bundle-manifest-sha256=%s\nimplementation-actor-reference=%s\n' \
    "$task5_retire_status" "$task5_retire_action" "$task5_retire_ordinal" \
    "$plan_commit" "$task5_retire_head" "$task5_retire_tree" \
    "$task5_retire_porcelain_sha" \
    "$task5_retire_authority_sha" \
    "${task5_implementation_actor_reference-UNAUTHENTICATED}" > "$retired_path"
  : > "$retired_manifest_path"
  find "$task5_evidence_root" -type f ! -path "$retired_manifest_path" -print | \
    LC_ALL=C sort | while IFS= read -r task5_retire_file; do
      task5_retire_relative="${task5_retire_file#"$task5_evidence_root/"}"
      task5_retire_file_sha="$(shasum -a 256 "$task5_retire_file" | \
        awk '{print $1}')" || exit 1
      printf '%s  %s\n' "$task5_retire_file_sha" \
        "$task5_retire_relative" >> "$retired_manifest_path"
    done
  test -s "$retired_manifest_path"
  find "$task5_evidence_root" -type f -exec chmod 400 {} \;
  find "$task5_evidence_root" -depth -type d -exec chmod 500 {} \;
  task5_bootstrap_require_owned_regular "$retired_path"
  task5_bootstrap_require_owned_regular "$retired_manifest_path"
  test "$(stat -f '%Lp' "$retired_path")" = 400
  test "$(stat -f '%Lp' "$retired_manifest_path")" = 400
  if test -n "${commands_root-}" && test -d "$commands_root"; then
    task5_bootstrap_require_owned_directory "$commands_root" 500
  fi
  task5_bootstrap_require_owned_directory "$task5_evidence_root" 500
)

export PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Cellar/dotnet/10.0.300/bin
export LC_ALL=C
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL=/dev/null
TASK5_EXPECTED_EXECUTION_ROOT=/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-oracle-passive-trace
TASK5_EXPECTED_BRANCH=refs/heads/codex/oracle-passive-task5-rebase
TASK5_EXPECTED_PARENT=9f69d2c40406461a28f018290d579cf313f22287
TASK5_EXPECTED_SUBJECT='docs: plan Task 5 passive driver completion'
TASK5_EXPECTED_PLAN_PATH=docs/superpowers/plans/2026-08-07-task-5-passive-driver.md

test "$task5_authority_source" = /private/tmp/ssr-task5-authority-bundle
task5_bootstrap_require_sha256 "$task5_authority_expected_sha"
task5_bootstrap_verify_manifest_root "$task5_authority_source" \
  "$task5_authority_source/manifest.sha256" "$task5_authority_expected_sha"

execution_root="$(cd "$(git rev-parse --show-toplevel)" && pwd -P)"
test "$execution_root" = "$TASK5_EXPECTED_EXECUTION_ROOT"
test "$(git -C "$execution_root" symbolic-ref -q HEAD)" = "$TASK5_EXPECTED_BRANCH"
plan_commit="$(git -C "$execution_root" rev-parse HEAD)"
test "$(git -C "$execution_root" rev-parse --verify "$plan_commit^{commit}")" = "$plan_commit"
test "$(git -C "$execution_root" show -s --format=%s "$plan_commit")" = "$TASK5_EXPECTED_SUBJECT"
test "$(git -C "$execution_root" rev-list --parents -n 1 "$plan_commit")" = \
  "$plan_commit $TASK5_EXPECTED_PARENT"
test "$(git -C "$execution_root" diff-tree --no-commit-id --name-only -r "$plan_commit")" = \
  "$TASK5_EXPECTED_PLAN_PATH"
test "$(git -C "$execution_root" show -s --format=%an "$plan_commit")" = jess
test "$(git -C "$execution_root" show -s --format=%ae "$plan_commit")" = \
  optimistindustries@gmail.com
test "$(git -C "$execution_root" show -s --format=%cn "$plan_commit")" = jess
test "$(git -C "$execution_root" show -s --format=%ce "$plan_commit")" = \
  optimistindustries@gmail.com

git_dir_token="$(git -C "$execution_root" rev-parse --git-dir)"
case "$git_dir_token" in
  /*) git_dir="$(cd "$git_dir_token" && pwd -P)" ;;
  *) git_dir="$(cd "$execution_root/$git_dir_token" && pwd -P)" ;;
esac
common_dir_token="$(git -C "$execution_root" rev-parse --git-common-dir)"
case "$common_dir_token" in
  /*) common_dir="$(cd "$common_dir_token" && pwd -P)" ;;
  *) common_dir="$(cd "$execution_root/$common_dir_token" && pwd -P)" ;;
esac
test "$git_dir" != "$common_dir"
worktree_record="$(git -C "$execution_root" worktree list --porcelain | \
  awk -v wanted="worktree $execution_root" '
    $1 == "worktree" { selected = ($0 == wanted) }
    selected { print }
  ')"
test "$(printf '%s\n' "$worktree_record" | awk -v wanted="worktree $execution_root" \
  '$0 == wanted {n++} END {print n + 0}')" = 1
test "$(printf '%s\n' "$worktree_record" | awk -v wanted="HEAD $plan_commit" \
  '$0 == wanted {n++} END {print n + 0}')" = 1
test "$(printf '%s\n' "$worktree_record" | awk -v wanted="branch $TASK5_EXPECTED_BRANCH" \
  '$0 == wanted {n++} END {print n + 0}')" = 1
test "$(printf '%s\n' "$worktree_record" | \
  awk '/^(detached|locked|prunable)([[:space:]]|$)/ {n++} END {print n + 0}')" = 0

plan_path="$TASK5_EXPECTED_PLAN_PATH"
task5_evidence_root="$(mktemp -d /private/tmp/ssr-task5-evidence.XXXXXXXX)"
retired_path="$task5_evidence_root/retired.identity"
retired_manifest_path="$task5_evidence_root/retired.manifest.sha256"
chmod 700 "$task5_evidence_root"
task5_bootstrap_require_owned_directory "$task5_evidence_root" 700
controller_home="$task5_evidence_root/controller-home"
commands_root="$task5_evidence_root/commands"
aliases_root="$task5_evidence_root/aliases"
review_packages_root="$task5_evidence_root/review-packages"
review_inbox_root="$task5_evidence_root/review-inbox"
review_responses_root="$task5_evidence_root/review-responses"
state_root="$task5_evidence_root/state"
report_gates_root="$task5_evidence_root/report-gates"
finalized_path="$task5_evidence_root/finalized"
for task5_bootstrap_dir in "$controller_home" "$commands_root" \
    "$aliases_root" "$review_packages_root" "$review_inbox_root" \
    "$review_responses_root" "$state_root" "$report_gates_root"; do
  task5_bootstrap_require_absent_path "$task5_bootstrap_dir"
  mkdir -m 700 "$task5_bootstrap_dir"
  task5_bootstrap_require_owned_directory "$task5_bootstrap_dir" 700
  test "$(cd "$task5_bootstrap_dir/.." && pwd -P)" = "$task5_evidence_root"
done
authority_bundle_root="$task5_evidence_root/authority-bundle"
task5_bootstrap_require_absent_path "$authority_bundle_root"
cp -R -p "$task5_authority_source" "$authority_bundle_root"
task5_bootstrap_verify_manifest_root "$authority_bundle_root" \
  "$authority_bundle_root/manifest.sha256" "$task5_authority_expected_sha"
test "$(find "$authority_bundle_root" -type d | wc -l | tr -d '[:space:]')" = 2
test "$(find "$authority_bundle_root" -type f | wc -l | tr -d '[:space:]')" = 16
authority_bundle_sha="$task5_authority_expected_sha"
authority_receipt="$authority_bundle_root/authority.receipt"
approval_text="$authority_bundle_root/implementation-approval.txt"
approval_reference="$authority_bundle_root/implementation-approval.reference"
p_review_package="$authority_bundle_root/P-review-package"
p_review_manifest="$p_review_package/manifest.sha256"
p_review_identity="$p_review_package/package.identity"
p_review_plan="$p_review_package/plan.md"
p_review_checker="$p_review_package/checker.sh"
p_review_runtime="$p_review_package/runtime.sh"
p_review_bootstrap="$p_review_package/bootstrap.sh"
p_review_mutations="$p_review_package/canonical-mutations.manifest"
p_review_core="$p_review_package/core.manifest"
for task5_authority_file in "$authority_receipt" "$approval_text" \
    "$approval_reference" "$p_review_manifest" "$p_review_identity" \
    "$p_review_plan" "$p_review_checker" "$p_review_runtime" \
    "$p_review_bootstrap" "$p_review_mutations" "$p_review_core" \
    "$authority_bundle_root/P.spec.response.md" \
    "$authority_bundle_root/P.spec.identity" \
    "$authority_bundle_root/P.quality.response.md" \
    "$authority_bundle_root/P.quality.identity"; do
  task5_bootstrap_require_owned_regular "$task5_authority_file"
  test "$(stat -f '%Lp' "$task5_authority_file")" = 400
done
test "$(task5_bootstrap_receipt_value "$authority_receipt" version)" = 1
test "$(wc -l < "$authority_receipt" | tr -d '[:space:]')" = 17
test "$(task5_bootstrap_receipt_value "$authority_receipt" P)" = "$plan_commit"
test "$(task5_bootstrap_receipt_value "$authority_receipt" amendment)" = \
  U-T5-C53-INTERMEDIATE-READY-01
task5_implementation_actor_reference="$(task5_bootstrap_receipt_value \
  "$authority_receipt" implementation-actor-reference)"
task5_p_spec_reviewer_reference="$(task5_bootstrap_receipt_value \
  "$authority_receipt" spec-reviewer-reference)"
task5_p_quality_reviewer_reference="$(task5_bootstrap_receipt_value \
  "$authority_receipt" quality-reviewer-reference)"
task5_bootstrap_require_independent_reviewer_references \
  "$task5_implementation_actor_reference" \
  "$task5_p_spec_reviewer_reference" \
  "$task5_p_quality_reviewer_reference"
for task5_authority_sha_field in plan-sha256 checker-sha256 runtime-sha256 \
    core-manifest-sha256 bootstrap-sha256 \
    canonical-mutation-manifest-sha256 review-package-sha256 spec-response-sha256 \
    quality-response-sha256 approval-text-sha256 \
    approval-reference-sha256; do
  task5_bootstrap_require_sha256 "$(task5_bootstrap_receipt_value \
    "$authority_receipt" "$task5_authority_sha_field")"
done
canonical_mutation_manifest_sha="$(task5_bootstrap_receipt_value \
  "$authority_receipt" canonical-mutation-manifest-sha256)"
p_review_package_sha="$(task5_bootstrap_receipt_value \
  "$authority_receipt" review-package-sha256)"
task5_bootstrap_verify_manifest_root "$p_review_package" \
  "$p_review_manifest" "$p_review_package_sha"
test "$(find "$p_review_package" -type d | wc -l | tr -d '[:space:]')" = 1
test "$(find "$p_review_package" -type f | wc -l | tr -d '[:space:]')" = 8
test "$(wc -l < "$p_review_identity" | tr -d '[:space:]')" = 14
test "$(task5_bootstrap_receipt_value "$p_review_identity" format)" = \
  task5-plan-review-v1
test "$(task5_bootstrap_receipt_value "$p_review_identity" P)" = "$plan_commit"
test "$(task5_bootstrap_receipt_value "$p_review_identity" D)" = \
  "$TASK5_EXPECTED_PARENT"
test "$(task5_bootstrap_receipt_value "$p_review_identity" plan-path)" = \
  "$plan_path"
test "$(task5_bootstrap_receipt_value "$p_review_identity" amendment)" = \
  U-T5-C53-INTERMEDIATE-READY-01
test "$(task5_bootstrap_receipt_value "$p_review_identity" \
  implementation-actor-reference)" = "$task5_implementation_actor_reference"
test "$(task5_bootstrap_receipt_value "$p_review_identity" \
  spec-reviewer-reference)" = "$task5_p_spec_reviewer_reference"
test "$(task5_bootstrap_receipt_value "$p_review_identity" \
  quality-reviewer-reference)" = "$task5_p_quality_reviewer_reference"
for task5_p_review_sha_field in plan-sha256 checker-sha256 runtime-sha256 \
    bootstrap-sha256 canonical-mutation-manifest-sha256 \
    core-manifest-sha256; do
  test "$(task5_bootstrap_receipt_value "$p_review_identity" \
    "$task5_p_review_sha_field")" = \
    "$(task5_bootstrap_receipt_value "$authority_receipt" \
      "$task5_p_review_sha_field")"
done
test "$(shasum -a 256 "$p_review_plan" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" plan-sha256)"
test "$(shasum -a 256 "$p_review_checker" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" checker-sha256)"
test "$(shasum -a 256 "$p_review_runtime" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" runtime-sha256)"
test "$(shasum -a 256 "$p_review_bootstrap" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" bootstrap-sha256)"
test "$(shasum -a 256 "$p_review_mutations" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" \
    canonical-mutation-manifest-sha256)"
test "$(shasum -a 256 "$p_review_core" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" core-manifest-sha256)"
test "$(shasum -a 256 "$approval_text" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" approval-text-sha256)"
test "$(shasum -a 256 "$approval_reference" | awk '{print $1}')" = \
  "$(task5_bootstrap_receipt_value "$authority_receipt" approval-reference-sha256)"
test -s "$approval_text"
test "$(tail -c 1 "$approval_text" | od -An -tu1 | tr -d '[:space:]')" = 10
test "$(awk 'index($0, sprintf("%c", 13)) {n++} END {print n + 0}' \
  "$approval_text")" = 0
test "$(grep -Fxc "P=$plan_commit" "$approval_text")" = 1
test "$(grep -Fxc 'AMENDMENT=U-T5-C53-INTERMEDIATE-READY-01' \
  "$approval_text")" = 1
test "$(grep -Fxc "IMPLEMENTATION-ACTOR-REFERENCE=$task5_implementation_actor_reference" \
  "$approval_text")" = 1
test "$(grep -Fxc 'DECISION=APPROVE' "$approval_text")" = 1
test "$(grep -Ec '^P=' "$approval_text")" = 1
test "$(grep -Ec '^AMENDMENT=' "$approval_text")" = 1
test "$(grep -Ec '^IMPLEMENTATION-ACTOR-REFERENCE=' "$approval_text")" = 1
test "$(grep -Ec '^DECISION=' "$approval_text")" = 1
task5_bootstrap_require_no_nul_file "$approval_text"
task5_approval_reference="$(task5_bootstrap_read_coordination_reference_file \
  "$approval_reference")"
for task5_review_lane in spec quality; do
  task5_review_response="$authority_bundle_root/P.$task5_review_lane.response.md"
  task5_review_identity="$authority_bundle_root/P.$task5_review_lane.identity"
  task5_response_sha="$(shasum -a 256 "$task5_review_response" | awk '{print $1}')"
  test "$task5_response_sha" = "$(task5_bootstrap_receipt_value \
    "$authority_receipt" "$task5_review_lane-response-sha256")"
  test "$(grep -Fxc "PACKAGE-SHA256: $p_review_package_sha" \
    "$task5_review_response")" = 1
  test "$(grep -Ec '^PACKAGE-SHA256:' "$task5_review_response")" = 1
  if test "$task5_review_lane" = spec; then
    task5_expected_reviewer_reference="$task5_p_spec_reviewer_reference"
  else
    task5_expected_reviewer_reference="$task5_p_quality_reviewer_reference"
  fi
  test "$(grep -Fxc "REVIEWER-REFERENCE: $task5_expected_reviewer_reference" \
    "$task5_review_response")" = 1
  test "$(grep -Ec '^REVIEWER-REFERENCE:' "$task5_review_response")" = 1
  test "$(grep -Fxc "IMPLEMENTATION-ACTOR-REFERENCE: $task5_implementation_actor_reference" \
    "$task5_review_response")" = 1
  test "$(grep -Ec '^IMPLEMENTATION-ACTOR-REFERENCE:' \
    "$task5_review_response")" = 1
  test "$(grep -Ec '^VERDICT:' "$task5_review_response")" = 1
  test "$(grep -Ec \
    '^VERDICT: APPROVE CRITICAL=0 IMPORTANT=0 MINOR=[0-9]+$' \
    "$task5_review_response")" = 1
  task5_bootstrap_require_minor_dispositions "$task5_review_response"
  test "$(wc -l < "$task5_review_identity" | tr -d '[:space:]')" = 6
  test "$(task5_bootstrap_receipt_value "$task5_review_identity" checkpoint)" = P
  test "$(task5_bootstrap_receipt_value "$task5_review_identity" lane)" = \
    "$task5_review_lane"
  test "$(task5_bootstrap_receipt_value "$task5_review_identity" \
    package-sha256)" = "$p_review_package_sha"
  test "$(task5_bootstrap_receipt_value "$task5_review_identity" \
    response-sha256)" = "$task5_response_sha"
  test "$(task5_bootstrap_receipt_value "$task5_review_identity" \
    reviewer-reference)" = "$task5_expected_reviewer_reference"
  test "$(task5_bootstrap_receipt_value "$task5_review_identity" \
    implementation-actor-reference)" = "$task5_implementation_actor_reference"
done
p_alias="$task5_evidence_root/P.alias"
task5_bootstrap_require_absent_path "$p_alias"
printf '%s\n' "$plan_commit" > "$p_alias"
chmod 600 "$p_alias"
task5_bootstrap_require_owned_regular "$p_alias"
test "$(stat -f '%Lp' "$p_alias")" = 600
test "$(cat "$p_alias")" = "$plan_commit"
plan_blob="$task5_evidence_root/committed-plan.md"
task5_bootstrap_require_absent_path "$plan_blob"
git -C "$execution_root" show "$plan_commit:$plan_path" > "$plan_blob"
task5_bootstrap_require_owned_regular "$plan_blob"
test "$(shasum -a 256 "$plan_blob" | awk '{print $1}')" = \
  "$(git -C "$execution_root" show "$plan_commit:$plan_path" | \
    shasum -a 256 | awk '{print $1}')"
checker_begin='<!-- TASK5-PLAN-AUDIT-BEGIN -->'
checker_end='<!-- TASK5-PLAN-AUDIT-END -->'
test "$(awk -v marker="$checker_begin" \
  '$0 == marker {n++} END {print n + 0}' "$plan_blob")" = 1
test "$(awk -v marker="$checker_end" \
  '$0 == marker {n++} END {print n + 0}' "$plan_blob")" = 1
checker_begin_line="$(awk -v marker="$checker_begin" \
  '$0 == marker {print NR}' "$plan_blob")"
checker_end_line="$(awk -v marker="$checker_end" \
  '$0 == marker {print NR}' "$plan_blob")"
test "$checker_begin_line" -lt "$checker_end_line"
test "$(sed -n "$((checker_begin_line + 1))p" "$plan_blob")" = '```bash'
test "$(sed -n "$((checker_end_line - 1))p" "$plan_blob")" = '```'
plan_auditor="$task5_evidence_root/task5-plan-audit.sh"
task5_bootstrap_require_absent_path "$plan_auditor"
awk -v first="$((checker_begin_line + 1))" \
  -v last="$((checker_end_line - 1))" \
  'NR > first && NR < last {print}' "$plan_blob" > "$plan_auditor"
task5_bootstrap_require_owned_regular "$plan_auditor"
/bin/bash --noprofile --norc -n "$plan_auditor"
plan_auditor_sha="$(shasum -a 256 "$plan_auditor" | awk '{print $1}')"
chmod 400 "$plan_auditor"
test "$(stat -f '%Lp' "$plan_auditor")" = 400
runtime_begin='<!-- TASK5-RUNTIME-BEGIN -->'
runtime_end='<!-- TASK5-RUNTIME-END -->'
test "$(awk -v marker="$runtime_begin" \
  '$0 == marker {n++} END {print n + 0}' "$plan_blob")" = 1
test "$(awk -v marker="$runtime_end" \
  '$0 == marker {n++} END {print n + 0}' "$plan_blob")" = 1
begin_line="$(awk -v marker="$runtime_begin" \
  '$0 == marker {print NR}' "$plan_blob")"
end_line="$(awk -v marker="$runtime_end" \
  '$0 == marker {print NR}' "$plan_blob")"
test "$begin_line" -lt "$end_line"
test "$(sed -n "$((begin_line + 1))p" "$plan_blob")" = '```bash'
test "$(sed -n "$((end_line - 1))p" "$plan_blob")" = '```'
task5_driver="$task5_evidence_root/task5-controller.sh"
task5_bootstrap_require_absent_path "$task5_driver"
awk -v first="$((begin_line + 1))" -v last="$((end_line - 1))" \
  'NR > first && NR < last {print}' "$plan_blob" > "$task5_driver"
task5_bootstrap_require_owned_regular "$task5_driver"
test "$(tail -c 1 "$task5_driver" | od -An -tu1 | tr -d '[:space:]')" = 10
test "$(awk 'index($0, sprintf("%c", 13)) {n++} END {print n + 0}' \
  "$task5_driver")" = 0
/bin/bash --noprofile --norc -n "$task5_driver"
task5_driver_sha="$(shasum -a 256 "$task5_driver" | awk '{print $1}')"
test "${#task5_driver_sha}" = 64
chmod 400 "$task5_driver"
test "$(stat -f '%Lp' "$task5_driver")" = 400
test "$(stat -f '%u' "$task5_driver")" = "$(id -u)"
test "$(task5_bootstrap_receipt_value "$authority_receipt" plan-sha256)" = \
  "$(shasum -a 256 "$plan_blob" | awk '{print $1}')"
test "$(task5_bootstrap_receipt_value "$authority_receipt" checker-sha256)" = \
  "$plan_auditor_sha"
test "$(task5_bootstrap_receipt_value "$authority_receipt" runtime-sha256)" = \
  "$task5_driver_sha"
test "$(task5_bootstrap_receipt_value "$authority_receipt" bootstrap-sha256)" = \
  "$task5_bootstrap_sha"

readonly TASK5_EXPECTED_EXECUTION_ROOT TASK5_EXPECTED_BRANCH
readonly TASK5_EXPECTED_PARENT TASK5_EXPECTED_SUBJECT
readonly TASK5_EXPECTED_PLAN_PATH execution_root plan_commit plan_path
readonly task5_evidence_root controller_home p_alias plan_blob
readonly authority_bundle_root authority_bundle_sha authority_receipt
readonly task5_implementation_actor_reference
readonly approval_text approval_reference p_review_package p_review_manifest
readonly task5_bootstrap_path task5_bootstrap_sha
readonly canonical_mutation_manifest_sha
readonly commands_root aliases_root review_packages_root review_inbox_root
readonly review_responses_root state_root report_gates_root
readonly finalized_path retired_path retired_manifest_path
readonly plan_auditor plan_auditor_sha task5_driver task5_driver_sha

task5_bootstrap_audit_ledger() {
  task5_bootstrap_require_owned_directory "$commands_root" 700
  task5_expected_ordinal=1
  for task5_entry in "$commands_root"/[0-9][0-9][0-9][0-9][0-9][0-9]; do
    test -e "$task5_entry"
    task5_expected_name="$(printf '%06d' "$task5_expected_ordinal")"
    test "${task5_entry##*/}" = "$task5_expected_name"
    task5_bootstrap_require_owned_directory "$task5_entry" 500
    task5_manifest="$task5_entry/manifest.sha256"
    task5_bootstrap_require_owned_regular "$task5_manifest"
    test -z "$(find "$task5_entry" -type l -print)"
    test -z "$(find "$task5_entry" ! -type d ! -type f -print)"
    task5_manifest_entries=0
    while IFS='  ' read -r task5_manifest_sha task5_manifest_relative; do
      test -n "$task5_manifest_sha"
      test -n "$task5_manifest_relative"
      case "$task5_manifest_relative" in
        /*|*..*) return 1 ;;
      esac
      task5_manifest_path="$task5_entry/$task5_manifest_relative"
      task5_bootstrap_require_owned_regular "$task5_manifest_path"
      test "$(shasum -a 256 "$task5_manifest_path" | awk '{print $1}')" = \
        "$task5_manifest_sha"
      task5_manifest_entries=$((task5_manifest_entries + 1))
    done < "$task5_manifest"
    test "$(find "$task5_entry" -type f | wc -l | tr -d '[:space:]')" = \
      "$((task5_manifest_entries + 1))"
    find "$task5_entry" -type f -print | while IFS= read -r task5_file; do
      task5_bootstrap_require_owned_regular "$task5_file"
      test "$(stat -f '%Lp' "$task5_file")" = 400
    done
    find "$task5_entry" -type d -print | while IFS= read -r task5_dir; do
      task5_bootstrap_require_owned_directory "$task5_dir" 500
    done
    test "$(cat "$task5_entry/exit")" = 0
    test "$(task5_bootstrap_receipt_value \
      "$task5_entry/controller.identity" implementation-actor-reference)" = \
      "$task5_implementation_actor_reference"
    task5_expected_ordinal=$((task5_expected_ordinal + 1))
  done
  test "$task5_expected_ordinal" = 149
}

task5_clean_call() {
  test "$#" -ge 1
  if test -e "$retired_path" || test -L "$retired_path"; then
    task5_bootstrap_require_owned_regular "$retired_path"
    task5_bootstrap_require_owned_regular "$retired_manifest_path"
    test "$(stat -f '%Lp' "$retired_path")" = 400
    test "$(stat -f '%Lp' "$retired_manifest_path")" = 400
    printf 'Task 5 evidence namespace is retired; no later action is authorized.\n' \
      >&2
    return 1
  fi
  if test -e "$finalized_path" || test -L "$finalized_path"; then
    task5_bootstrap_require_owned_regular "$finalized_path"
    test "$(stat -f '%Lp' "$finalized_path")" = 400
    printf 'Task 5 evidence namespace is finalized; no later action is authorized.\n' \
      >&2
    return 1
  fi
  task5_action="$1"
  task5_ordinal=1
  while :; do
    task5_entry="$commands_root/$(printf '%06d' "$task5_ordinal")"
    if mkdir -m 700 "$task5_entry" 2>/dev/null; then
      break
    fi
    if test -e "$task5_entry" || test -L "$task5_entry"; then
      task5_ordinal=$((task5_ordinal + 1))
    else
      return 1
    fi
  done
  task5_bootstrap_require_owned_directory "$task5_entry" 700
  test "$(cd "$task5_entry/.." && pwd -P)" = "$commands_root"
  if test "$task5_ordinal" = 1; then
    test "$task5_action" = plan-postcommit
  else
    test "$task5_action" != plan-postcommit
  fi
  task5_action_dir="$task5_entry/artifacts"
  task5_bootstrap_require_absent_path "$task5_action_dir"
  mkdir -m 700 "$task5_action_dir"
  task5_bootstrap_require_owned_directory "$task5_action_dir" 700

  task5_argv_path="$task5_entry/argv.q"
  task5_stdout_path="$task5_entry/stdout"
  task5_stderr_path="$task5_entry/stderr"
  task5_exit_path="$task5_entry/exit"
  task5_controller_identity="$task5_entry/controller.identity"
  task5_manifest_path="$task5_entry/manifest.sha256"
  for task5_output_path in "$task5_argv_path" "$task5_stdout_path" \
      "$task5_stderr_path" "$task5_exit_path" "$task5_controller_identity" \
      "$task5_manifest_path"; do
    task5_bootstrap_require_absent_path "$task5_output_path"
  done
  printf '%q ' /bin/bash --noprofile --norc "$task5_driver" > "$task5_argv_path"
  for task5_argv in "$@"; do
    printf '%q ' "$task5_argv" >> "$task5_argv_path"
  done
  printf '\n' >> "$task5_argv_path"
  task5_bootstrap_capture_repo_state "$execution_root" "$task5_entry/before"
  printf 'controller-sha256=%s\nplan-auditor-sha256=%s\nbootstrap-sha256=%s\ncanonical-mutation-manifest-sha256=%s\nauthority-bundle-manifest-sha256=%s\nimplementation-actor-reference=%s\nP=%s\nplan-path=%s\n' \
    "$task5_driver_sha" "$plan_auditor_sha" "$task5_bootstrap_sha" \
    "$canonical_mutation_manifest_sha" "$authority_bundle_sha" \
    "$task5_implementation_actor_reference" "$plan_commit" "$plan_path" \
    > "$task5_controller_identity"

  if /usr/bin/env -i \
    PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Cellar/dotnet/10.0.300/bin \
    LC_ALL=C LANG=C \
    HOME="$controller_home" TMPDIR=/private/tmp \
    GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 \
    DOTNET_CLI_HOME="$controller_home" DOTNET_CLI_UI_LANGUAGE=en \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true \
    DOTNET_SDK_VULNERABILITY_CHECK_DISABLE=true DOTNET_NOLOGO=1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 NUGET_XMLDOC_MODE=skip \
    PYTHONDONTWRITEBYTECODE=1 PIP_NO_INDEX=1 UV_OFFLINE=1 \
    TASK5_CLEAN_CONTROLLER=1 \
    TASK5_EXECUTION_ROOT="$execution_root" \
    TASK5_EVIDENCE_ROOT="$task5_evidence_root" \
    TASK5_COMMANDS_ROOT="$commands_root" \
    TASK5_ACTION_DIR="$task5_action_dir" \
    TASK5_PLAN_COMMIT="$plan_commit" \
    TASK5_PLAN_PATH="$plan_path" \
    TASK5_P_ALIAS="$p_alias" \
    TASK5_DRIVER_PATH="$task5_driver" \
    TASK5_DRIVER_SHA="$task5_driver_sha" \
    TASK5_PLAN_AUDITOR_PATH="$plan_auditor" \
    TASK5_PLAN_AUDITOR_SHA="$plan_auditor_sha" \
    TASK5_BOOTSTRAP_SHA="$task5_bootstrap_sha" \
    TASK5_CANONICAL_MUTATION_MANIFEST_SHA="$canonical_mutation_manifest_sha" \
    TASK5_AUTHORITY_BUNDLE_ROOT="$authority_bundle_root" \
    TASK5_AUTHORITY_BUNDLE_SHA="$authority_bundle_sha" \
    TASK5_IMPLEMENTATION_ACTOR_REFERENCE="$task5_implementation_actor_reference" \
    TASK5_REVIEW_PACKAGES_ROOT="$review_packages_root" \
    TASK5_REVIEW_INBOX_ROOT="$review_inbox_root" \
    TASK5_REVIEW_RESPONSES_ROOT="$review_responses_root" \
    TASK5_STATE_ROOT="$state_root" \
    TASK5_REPORT_GATES_ROOT="$report_gates_root" \
    TASK5_EXPECTED_BRANCH="$TASK5_EXPECTED_BRANCH" \
    TASK5_EXPECTED_PARENT="$TASK5_EXPECTED_PARENT" \
    TASK5_EXPECTED_SUBJECT="$TASK5_EXPECTED_SUBJECT" \
      /bin/bash --noprofile --norc "$task5_driver" "$@" \
      > "$task5_stdout_path" 2> "$task5_stderr_path"; then
    task5_child_status=0
  else
    task5_child_status=$?
  fi
  printf '%s\n' "$task5_child_status" > "$task5_exit_path"
  task5_bootstrap_capture_repo_state "$execution_root" "$task5_entry/after"
  cat "$task5_stdout_path"
  cat "$task5_stderr_path" >&2

  task5_bootstrap_require_absent_path "$task5_manifest_path"
  : > "$task5_manifest_path"
  for task5_manifest_file in argv.q stdout stderr exit controller.identity \
      before.porcelain before.identity after.porcelain after.identity; do
    printf '%s  %s\n' \
      "$(shasum -a 256 "$task5_entry/$task5_manifest_file" | awk '{print $1}')" \
      "$task5_manifest_file" >> "$task5_manifest_path"
  done
  find "$task5_action_dir" -type f -print | LC_ALL=C sort | \
    while IFS= read -r task5_artifact_file; do
      task5_artifact_relative="${task5_artifact_file#"$task5_entry/"}"
      printf '%s  %s\n' \
        "$(shasum -a 256 "$task5_artifact_file" | awk '{print $1}')" \
        "$task5_artifact_relative" >> "$task5_manifest_path"
    done
  test -z "$(find "$task5_entry" -type l -print)"
  test -z "$(find "$task5_entry" ! -type d ! -type f -print)"
  task5_manifest_entries="$(wc -l < "$task5_manifest_path" | tr -d '[:space:]')"
  test "$(find "$task5_entry" -type f | wc -l | tr -d '[:space:]')" = \
    "$((task5_manifest_entries + 1))"
  find "$task5_entry" -type f -print | while IFS= read -r task5_file; do
    task5_bootstrap_require_owned_regular "$task5_file"
  done
  find "$task5_entry" -type f -exec chmod 400 {} \;
  find "$task5_entry" -depth -type d -exec chmod 500 {} \;
  task5_bootstrap_require_owned_directory "$task5_entry" 500
  task5_bootstrap_require_owned_regular "$task5_manifest_path"
  find "$task5_entry" -type d -print | while IFS= read -r task5_dir; do
    task5_bootstrap_require_owned_directory "$task5_dir" 500
  done

  if test "$task5_action" = final-audit && test "$task5_child_status" = 0; then
    test "$task5_ordinal" = 148
    task5_bootstrap_audit_ledger
    task5_bootstrap_require_absent_path "$finalized_path"
    printf 'final-entry=%s\ncontroller-sha256=%s\nplan-auditor-sha256=%s\nbootstrap-sha256=%s\nauthority-bundle-manifest-sha256=%s\nimplementation-actor-reference=%s\n' \
      "${task5_entry##*/}" "$task5_driver_sha" "$plan_auditor_sha" \
      "$task5_bootstrap_sha" "$authority_bundle_sha" \
      "$task5_implementation_actor_reference" \
      > "$finalized_path"
    chmod 400 "$finalized_path"
    task5_bootstrap_require_owned_regular "$finalized_path"
    test "$(stat -f '%Lp' "$finalized_path")" = 400
    chmod 500 "$commands_root"
    task5_bootstrap_require_owned_directory "$commands_root" 500
  fi
  if test "$task5_child_status" -ne 0; then
    task5_bootstrap_retire_namespace "$task5_child_status" "$task5_action" \
      "${task5_entry##*/}"
  fi
  return "$task5_child_status"
}

readonly -f task5_bootstrap_abort
readonly -f task5_bootstrap_require_absent_path
readonly -f task5_bootstrap_require_owned_regular
readonly -f task5_bootstrap_require_owned_directory
readonly -f task5_bootstrap_require_sha256
readonly -f task5_bootstrap_require_coordination_reference
readonly -f task5_bootstrap_require_no_nul_file
readonly -f task5_bootstrap_read_coordination_reference_file
readonly -f task5_bootstrap_require_independent_reviewer_references
readonly -f task5_bootstrap_require_minor_dispositions
readonly -f task5_bootstrap_verify_manifest_root
readonly -f task5_bootstrap_receipt_value
readonly -f task5_bootstrap_capture_repo_state
readonly -f task5_bootstrap_retire_namespace
readonly -f task5_bootstrap_audit_ledger
readonly -f task5_clean_call
printf 'Task 5 bootstrap ready: evidence=%s controller=%s auditor=%s\n' \
  "$task5_evidence_root" "$task5_driver_sha" "$plan_auditor_sha"
printf 'Run plan-postcommit with the recorded plan/checker/authority SHA-256 values before Task 0.\n'
```
<!-- TASK5-BOOTSTRAP-END -->

<!-- TASK5-RUNTIME-BEGIN -->
```bash
set -euo pipefail
umask 077
set -C

task5_fail() {
  printf 'task5 runtime failure: %s\n' "$*" >&2
  return 1
}

task5_sha256() {
  shasum -a 256 "$1" | awk '{print $1}'
}

task5_require_commit_file_pin() (
  set -euo pipefail
  test "$#" = 7
  repo_root="$1"
  commit_oid="$2"
  relative_path="$3"
  expected_sha="$4"
  expected_blob="$5"
  expected_lines="$6"
  expected_bytes="$7"
  test "$(git -C "$repo_root" ls-tree "$commit_oid" -- \
    "$relative_path" | awk '{print $1}')" = 100644
  test "$(git -C "$repo_root" rev-parse "$commit_oid:$relative_path")" = \
    "$expected_blob"
  test "$(git -C "$repo_root" show "$commit_oid:$relative_path" | \
    shasum -a 256 | awk '{print $1}')" = "$expected_sha"
  test "$(git -C "$repo_root" show "$commit_oid:$relative_path" | \
    wc -l | tr -d '[:space:]')" = "$expected_lines"
  test "$(git -C "$repo_root" show "$commit_oid:$relative_path" | \
    wc -c | tr -d '[:space:]')" = "$expected_bytes"
)

task5_authenticate_s4_d_pins() (
  set -euo pipefail
  test "$#" = 1
  repo_root="$(task5_physical_repo_root "$1")"
  S4=f5de26f3dea85f14f25e3540da9f29130e27a09b
  D=9f69d2c40406461a28f018290d579cf313f22287
  test "$(git -C "$repo_root" rev-parse "$S4^{tree}")" = \
    4bdb6fed33ea4ae0df6d956e512849c57b26b44c
  test "$(git -C "$repo_root" rev-list --parents -n 1 "$S4")" = \
    "$S4 6ade9cd2a06548741d104a38b6498f4e5b48af7f"
  test "$(git -C "$repo_root" show -s --format=%s "$S4")" = \
    'docs: seal Task 4.2 correction evidence'
  test "$(git -C "$repo_root" diff-tree --no-commit-id --name-only -r \
    "$S4")" = \
    docs/superpowers/evidence/2026-08-04-task-4.2-review-correction-evidence.md
  test "$(git -C "$repo_root" rev-parse "$D^{tree}")" = \
    a691afd8ae55f3676bcf1ffe0f6ef3b15b1d2feb
  test "$(git -C "$repo_root" rev-list --parents -n 1 "$D")" = "$D $S4"
  test "$(git -C "$repo_root" show -s --format=%s "$D")" = \
    'docs: design Task 5 passive driver completion'
  test "$(git -C "$repo_root" diff-tree --no-commit-id --name-only -r \
    "$D")" = docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md

  test "$(git -C "$repo_root" rev-parse "$S4:docs/superpowers/specs")" = \
    3afac5e2b6846c23dff21282fe8010b1e6a5fb33
  test "$(git -C "$repo_root" rev-parse "$S4:docs/superpowers/plans")" = \
    3d0ac5e512fc975258dc41b6489b19beb5026de6
  test "$(git -C "$repo_root" rev-parse "$S4:docs/superpowers/evidence")" = \
    a0d4a02cefc6193c881627eec9e919123aab71bd
  test "$(git -C "$repo_root" rev-parse "$S4:oracle/plugin")" = \
    aa2a29d64b2e17ddc438f38060d0855d65d3cd1e
  test "$(git -C "$repo_root" rev-parse "$S4:oracle/plugin/Core")" = \
    6961f005d1f95199c7ffed83d2062a1c221d54b6
  test "$(git -C "$repo_root" rev-parse "$S4:oracle/plugin/tests")" = \
    2a9f6d872e7dcd82ba98fab051cd5366f904d0e8
  test "$(git -C "$repo_root" rev-parse "$S4:tests")" = \
    bde2451478abb76b9b0ac39b6783c171dcef845f
  test "$(git -C "$repo_root" rev-parse "$S4:src/ssr_env")" = \
    82dc33143bc7654d31ae88a7da7f09f826bd0c2f

  while IFS='|' read -r relative_path expected_sha expected_blob \
      expected_lines expected_bytes; do
    task5_require_commit_file_pin "$repo_root" "$D" "$relative_path" \
      "$expected_sha" "$expected_blob" "$expected_lines" "$expected_bytes"
  done <<'TASK5_IMMUTABLE_PINS'
docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md|33209340e884fcd580f68183c77b1b8ed6142a13eb30b7f7c530800832b8c8ef|afe01e2721732b5b62d5b7c1628a7885b1e2fdb6|1159|56180
docs/superpowers/specs/2026-08-04-task-4.2-scope-pure-hardening-design.md|1c97f6feeab11f50d16cbc0ebcbfe0e5dce764566537e1999273a49c4a6b9c2a|b22e1403b420a0ba5ae5c9436f4c4902a2443a36|358|16762
docs/superpowers/specs/2026-08-04-task-4.2-review-correction-design.md|1a848ce91732bbb456246eab453e26cdd4d3b1a6170c6a3cd50219d9e7a29fa1|19efb6017f070616d4ae978372185651eb7607b9|623|31014
docs/superpowers/specs/2026-08-07-task-5-passive-driver-design.md|f44dd6709f9ca8af17b5dfabec8da7bc1566fb3b6b1f77cfb4874a12aed0e1a4|e87ac8ebcd12ed403fd1c34dc74a54a0823c1c50|494|23089
docs/superpowers/plans/2026-07-31-oracle-passive-plugin.md|f0018c53591a7bb73b9c92902570167f3144174fdda83eda20716dbb0fded65e|7099498479f58a5bd9f5facb7b0c3c77307d7e31|28913|1132724
docs/superpowers/plans/2026-08-04-task-4.2-review-correction.md|52d899d9c058171f814e09e403f52d00897fad5c4b956fc3fa0930c2ae8eac4c|283d691e50acfbd8ed71950412aead0e20e087d8|7310|293649
docs/superpowers/evidence/2026-08-04-task-4.2-review-correction-evidence.md|6a6c43466b32628551f473d839689533c1f2ef7e358e926f78594b1a4c767adb|d236429e96eaca01b6e6bfdb240c069869a3656d|120|53031
oracle/plugin/Core/CanonicalJson.cs|7e6e50f22aae26bad26f26f6fd248d32f08e116bf2598dc572eff2000151826c|110716e97b10e2575ea2fa61a01f3f5077f40408|345|11884
oracle/plugin/Core/CaptureException.cs|88e7fa226a595059a72e01eea69f33160b08721f6c61db68a69c25fc334db2bd|01a27b53f56314e251ee4f4f81402d7d585f4ea7|14|259
oracle/plugin/Core/CaptureSignature.cs|335c500506354defba8331eddf1492568797c97170ee1754d319fcf97e9a9d54|8f1817ec80ac57a8cdfaa4dda326aa9b38592221|55|2001
oracle/plugin/Core/NdjsonTraceSink.cs|b3bd207ec4684de5e5a896d76eda1aeaaff88f8f5638ebdcee74f9a23535c6fb|6135c09c9586ec31a17b7e22921d2297bd929a04|274|7545
oracle/plugin/Core/OracleProtocol.cs|a82c1c403d19cef3cd67a4c363c3e6582bbe394af648a5c740e28f31213554ce|5068184fdd4ac50e638296b173db269648c3665c|433|15371
oracle/plugin/Core/PassiveDriver.cs|0ab8b9dfb537577fb052e6e5dab2ca744bc08cfb92206e44fd00e4552cee56a6|16ae4d36bc03bfb9d4e3b4948d5b356709f66636|865|24715
oracle/plugin/Core/PassiveDriverBoundaries.cs|1a130383302b315f43f8643fab5c13ec8d643727c2095ca21929aac306cdf133|b575724daf03cdf7d9a96722945a55ccd46a6e87|434|10977
oracle/plugin/tests/PassiveDriverBoundaryTests.cs|20c90060294a822967ff7d9e75f6a86fdae2ba247b6a9a08eb327b623424e0fc|9dc0261bc4abd0a91ce818396d455b16561ed944|1368|49452
oracle/plugin/tests/PassiveDriverInitialTests.cs|0590e9ae35cc074e012dcffb86fae94e35bdd9d9225446b490bcce19de0c1b85|1528db5f92ec836a841a76f4f0edd858355678ad|1745|60511
oracle/plugin/tests/PassiveDriverTestSupport.cs|ee3af9a57cc539262d2bd80e8f163ea60988087d39fe2600cbf3f38169d9edb9|d089f8514b450384a6f72080d3bde2cea5218d38|475|13008
oracle/plugin/tests/Program.cs|9372ea72e23ca9d8a95f2cce1f7146713b603ce7ea733fe2e0756a33c6b25004|386f79c6cfb6b5b4100c413c2802b2191f1b79e3|38|1077
oracle/plugin/tests/SsrOracle.UnitTests.csproj|f8c5924d6e08cec8c08f7bafde2a5ef874d2bb17739cdfcf4f2b9924e51ff688|14df214f1e404fa584912ca6b7b074d75a3d3d73|12|362
oracle/plugin/tests/SsrOracle.Core.Net35.csproj|2cba9da0e4d8b751a27405c1d721dfd418b6ef15dd6fcab2a45bf00aeaab0151|c371a863b008a29cd080a0db0b1a583afc2c0548|20|799
oracle/plugin/tests/Directory.Build.props|9a4fe75bf551bd68539265b8ef587be8875891490324e00d14944c5947bcbc85|a5aa60be6f09a030ace1464e19a3461d17097f2d|6|278
oracle/plugin/tests/TestSupport.cs|fbe3965629bd9bcd82ba2e55be04829f86302ceb544a5ea117b942a5f2a3842f|ca67d433debcb534aaf8bb4bc5453766f23e8bd0|430|17375
src/ssr_env/oracle_protocol.py|9feab69eec050eea51670c9f80b00acba06799e500a4ed3502f02722d5ea7108|f390923533985d4b1595ea50f5dcf8119d1c1cca|960|33901
tests/test_oracle_protocol.py|a0689d3233f55e24a95de5f5f6212690b2b820f03aaf47db8a383dfff4e2ead4|0c0afbc7d859aac06f88c8514b28a2a3c0703c53|1900|58585
tests/test_oracle_install_compat.py|bb85418b25dfc18c7f0ea268ff65c2442ae41a3a6c93217911a11774cff9a5e0|bf4867f9f73668cf1db2d62a7fac030fbf78930f|7543|255854
TASK5_IMMUTABLE_PINS

  for future_path in \
      oracle/plugin/Core/PassiveDriverInput.cs \
      oracle/plugin/Core/PassiveDriverLifecycleHooks.cs \
      oracle/plugin/Core/PassiveDriverCompletion.cs \
      oracle/plugin/tests/PassiveDriverInputTests.cs \
      oracle/plugin/tests/PassiveDriverTerminalTests.cs \
      oracle/plugin/tests/PassiveDriverTests.cs; do
    if git -C "$repo_root" cat-file -e "$D:$future_path" 2>/dev/null; then
      task5_fail "future Task 5 path exists at D"
    fi
  done
  printf 'S4-D-immutable-pins=PASS files=25 future-absences=6\n'
)

task5_run_preflight() (
  set -euo pipefail
  test "$#" = 2
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  P="$(task5_resolve_alias "$evidence_root" P)"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$P"
  test -z "$(git -C "$repo_root" status --porcelain=v1 \
    --untracked-files=all)"
  task5_require_committed_checkpoint "$repo_root" "$evidence_root" P
  task5_authenticate_s4_d_pins "$repo_root"
  test "$(git -C "$repo_root" -c user.useConfigOnly=true \
    -c user.name=jess -c user.email=optimistindustries@gmail.com \
    config user.name)" = jess
  test "$(git -C "$repo_root" -c user.useConfigOnly=true \
    -c user.name=jess -c user.email=optimistindustries@gmail.com \
    config user.email)" = optimistindustries@gmail.com
  task5_require_dotnet
)

task5_require_sha256() {
  test "$#" = 1 || return 1
  if test "${#1}" != 64; then
    task5_fail "invalid SHA-256 length"
    return 1
  fi
  case "$1" in
    *[!0123456789abcdef]*)
      task5_fail "SHA-256 must be lowercase hexadecimal"
      return 1
      ;;
  esac
  return 0
}

task5_require_coordination_reference() {
  test "$#" = 1 || return 1
  test -n "$1" || return 1
  case "$1" in
    *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:/-]*)
      task5_fail "unsafe coordination reference"
      return 1
      ;;
  esac
# TASK5-COORDINATION-REFERENCE-STANDALONE-R-DEFENSE-V1
  if printf '%s\n' "$1" | awk '
    {
      lower = tolower($0)
      if (lower ~ /(^|[^a-z0-9])r([^a-z0-9]|$)/)
        found = 1
    }
    END {exit(found ? 0 : 1)}
  '; then
    return 1
  fi
  return 0
}

task5_require_no_nul_file() {
  test "$#" = 1 || return 1
  task5_require_owned_regular "$1" || return 1
# TASK5-STRUCTURED-TEXT-NUL-DEFENSE-V1
  if od -An -tu1 -v "$1" | awk '
    {
      for (field = 1; field <= NF; field++)
        if ($field == 0)
          found = 1
    }
    END {exit(found ? 0 : 1)}
  '; then
    task5_fail "structured text contains a NUL byte"
    return 1
  fi
  return 0
}

task5_read_coordination_reference_file() {
  test "$#" = 1 || return 1
  task5_require_owned_regular "$1" 400 || return 1
  test "$(wc -l < "$1" | tr -d '[:space:]')" = 1 || return 1
  test "$(tail -c 1 "$1" | od -An -tu1 | tr -d '[:space:]')" = 10 || \
    return 1
  coordination_reference_value="$(cat "$1")" || return 1
  task5_require_coordination_reference "$coordination_reference_value" || \
    return 1
  test "$(wc -c < "$1" | tr -d '[:space:]')" = \
    "$(( ${#coordination_reference_value} + 1 ))" || return 1
  printf '%s\n' "$coordination_reference_value"
}

task5_require_independent_reviewer_references() {
  test "$#" = 3
  actor_reference="$1"
  spec_reference="$2"
  quality_reference="$3"
  task5_require_coordination_reference "$actor_reference" || return 1
  task5_require_coordination_reference "$spec_reference" || return 1
  task5_require_coordination_reference "$quality_reference" || return 1
  test "$spec_reference" != "$quality_reference" || return 1
  test "$spec_reference" != "$actor_reference" || return 1
  test "$quality_reference" != "$actor_reference" || return 1
}

task5_require_p_identity() (
  set -euo pipefail
  test "$#" = 2
  commit_oid="$1"
  repo_root="$2"
  test "$(git -C "$repo_root" show -s --format=%an "$commit_oid")" = jess
  test "$(git -C "$repo_root" show -s --format=%ae "$commit_oid")" = \
    optimistindustries@gmail.com
  test "$(git -C "$repo_root" show -s --format=%cn "$commit_oid")" = jess
  test "$(git -C "$repo_root" show -s --format=%ce "$commit_oid")" = \
    optimistindustries@gmail.com
)

task5_require_absent_path() {
  test "$#" = 1 || return 1
  test ! -e "$1" || return 1
  test ! -L "$1" || return 1
  return 0
}

task5_require_owned_regular() {
  test "$#" = 1 || test "$#" = 2 || return 1
  test -f "$1" || return 1
  test ! -L "$1" || return 1
  test "$(stat -f '%u' "$1")" = "$(id -u)" || return 1
  if test "$#" = 2; then
    test "$(stat -f '%Lp' "$1")" = "$2" || return 1
  fi
  return 0
}

task5_require_owned_directory() {
  test "$#" = 2
  test -d "$1"
  test ! -L "$1"
  test "$(stat -f '%Lp' "$1")" = "$2"
  test "$(stat -f '%u' "$1")" = "$(id -u)"
}

task5_receipt_value() {
  test "$#" = 2 || return 1
  task5_require_no_nul_file "$1" || return 1
  test "$(awk -F= -v key="$2" '$1 == key {n++} END {print n + 0}' \
    "$1")" = 1 || return 1
  awk -F= -v key="$2" '$1 == key {sub(/^[^=]*=/, ""); print}' "$1"
}

task5_verify_manifest_root() (
  set -euo pipefail
  test "$#" = 3
  root="$1"
  manifest="$2"
  expected_sha="$3"
  task5_require_owned_directory "$root" 500
  task5_require_owned_regular "$manifest" 400
  task5_require_sha256 "$expected_sha"
  test "$(task5_sha256 "$manifest")" = "$expected_sha"
  case "$manifest" in
    "$root"/*) manifest_relative="${manifest#"$root/"}" ;;
    *) task5_fail "authority manifest is outside its root" ;;
  esac
  duplicate_paths="$(awk '
    {
      separator = index($0, "  ")
      if (!separator) { bad = 1; next }
      digest = substr($0, 1, separator - 1)
      relative = substr($0, separator + 2)
      if (length(digest) != 64 || digest !~ /^[0-9a-f]+$/) {
        bad = 1
        next
      }
      if (relative == "" || relative ~ /^\// || relative ~ /^\.\// ||
          relative == "." || relative == ".." || relative ~ /^\.\.\// ||
          relative ~ /\/\.\// || relative ~ /\/\.$/ ||
          relative ~ /\/\.\.\// || relative ~ /\/\.\.$/ ||
          relative ~ /\/\// || relative ~ /\/$/ ||
          relative ~ /[^0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._\/-]/) {
        bad = 1
        next
      }
      folded_relative = tolower(relative)
      if (seen[folded_relative]++) bad = 1
    }
    END {print bad + 0}
  ' "$manifest")"
  if test "$duplicate_paths" != 0; then
    task5_fail "manifest path is not canonical or contains duplicate relative paths"
  fi
  test -z "$(find "$root" -type l -print)"
  test -z "$(find "$root" ! -type d ! -type f -print)"
  entries=0
  while IFS='  ' read -r expected_file_sha relative_path; do
    task5_require_sha256 "$expected_file_sha"
    test -n "$relative_path"
    if test "$relative_path" = "$manifest_relative"; then
      task5_fail "manifest must not authenticate itself"
    fi
    case "$relative_path" in
      /*|..|../*|*/..|*/../*) task5_fail "unsafe authority manifest path" ;;
    esac
    task5_require_owned_regular "$root/$relative_path" 400
    test "$(task5_sha256 "$root/$relative_path")" = "$expected_file_sha"
    entries=$((entries + 1))
  done < "$manifest"
  test "$entries" -gt 0
  test "$(find "$root" -type f | wc -l | tr -d '[:space:]')" = \
    "$((entries + 1))"
  find "$root" -type d -print | while IFS= read -r directory; do
    task5_require_owned_directory "$directory" 500
  done
)

task5_require_authority_bundle() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 0
  test "${TASK5_AUTHORITY_BUNDLE_ROOT-}" = \
    "$TASK5_EVIDENCE_ROOT/authority-bundle"
  task5_require_sha256 "${TASK5_AUTHORITY_BUNDLE_SHA-}"
  task5_require_coordination_reference \
    "${TASK5_IMPLEMENTATION_ACTOR_REFERENCE-}"
  task5_verify_manifest_root "$TASK5_AUTHORITY_BUNDLE_ROOT" \
    "$TASK5_AUTHORITY_BUNDLE_ROOT/manifest.sha256" \
    "$TASK5_AUTHORITY_BUNDLE_SHA"
  test "$(find "$TASK5_AUTHORITY_BUNDLE_ROOT" -type d | \
    wc -l | tr -d '[:space:]')" = 2
  test "$(find "$TASK5_AUTHORITY_BUNDLE_ROOT" -type f | \
    wc -l | tr -d '[:space:]')" = 16
  receipt="$TASK5_AUTHORITY_BUNDLE_ROOT/authority.receipt"
  approval_text="$TASK5_AUTHORITY_BUNDLE_ROOT/implementation-approval.txt"
  approval_reference="$TASK5_AUTHORITY_BUNDLE_ROOT/implementation-approval.reference"
  review_root="$TASK5_AUTHORITY_BUNDLE_ROOT/P-review-package"
  review_manifest="$review_root/manifest.sha256"
  review_identity="$review_root/package.identity"
  review_plan="$review_root/plan.md"
  review_checker="$review_root/checker.sh"
  review_runtime="$review_root/runtime.sh"
  review_bootstrap="$review_root/bootstrap.sh"
  review_mutations="$review_root/canonical-mutations.manifest"
  review_core="$review_root/core.manifest"
  task5_require_owned_regular "$receipt" 400
  task5_require_owned_regular "$approval_text" 400
  task5_require_owned_regular "$approval_reference" 400
  test "$(wc -l < "$receipt" | tr -d '[:space:]')" = 17
  test "$(task5_receipt_value "$receipt" version)" = 1
  test "$(task5_receipt_value "$receipt" P)" = "$TASK5_PLAN_COMMIT"
  test "$(task5_receipt_value "$receipt" amendment)" = \
    U-T5-C53-INTERMEDIATE-READY-01
  implementation_actor_reference="$(task5_receipt_value \
    "$receipt" implementation-actor-reference)"
  p_spec_reviewer_reference="$(task5_receipt_value \
    "$receipt" spec-reviewer-reference)"
  p_quality_reviewer_reference="$(task5_receipt_value \
    "$receipt" quality-reviewer-reference)"
  task5_require_independent_reviewer_references \
    "$implementation_actor_reference" "$p_spec_reviewer_reference" \
    "$p_quality_reviewer_reference"
  test "$implementation_actor_reference" = \
    "$TASK5_IMPLEMENTATION_ACTOR_REFERENCE"
  for field in plan-sha256 checker-sha256 runtime-sha256 \
      core-manifest-sha256 bootstrap-sha256 \
      canonical-mutation-manifest-sha256 review-package-sha256 \
      spec-response-sha256 quality-response-sha256 approval-text-sha256 \
      approval-reference-sha256; do
    task5_require_sha256 "$(task5_receipt_value "$receipt" "$field")"
  done
  test "$(task5_receipt_value "$receipt" plan-sha256)" = \
    "$(task5_sha256 "$TASK5_EVIDENCE_ROOT/committed-plan.md")"
  test "$(task5_receipt_value "$receipt" checker-sha256)" = \
    "$TASK5_PLAN_AUDITOR_SHA"
  test "$(task5_receipt_value "$receipt" runtime-sha256)" = \
    "$TASK5_DRIVER_SHA"
  test "$(task5_receipt_value "$receipt" bootstrap-sha256)" = \
    "$TASK5_BOOTSTRAP_SHA"
  test "$(task5_receipt_value "$receipt" \
    canonical-mutation-manifest-sha256)" = \
    "$TASK5_CANONICAL_MUTATION_MANIFEST_SHA"
  review_package_sha="$(task5_receipt_value "$receipt" \
    review-package-sha256)"
  task5_verify_manifest_root "$review_root" "$review_manifest" \
    "$review_package_sha"
  test "$(find "$review_root" -type d | wc -l | tr -d '[:space:]')" = 1
  test "$(find "$review_root" -type f | wc -l | tr -d '[:space:]')" = 8
  for review_file in "$review_identity" "$review_plan" "$review_checker" \
      "$review_runtime" "$review_bootstrap" "$review_mutations" \
      "$review_core"; do
    task5_require_owned_regular "$review_file" 400
  done
  test "$(wc -l < "$review_identity" | tr -d '[:space:]')" = 14
  test "$(task5_receipt_value "$review_identity" format)" = \
    task5-plan-review-v1
  test "$(task5_receipt_value "$review_identity" P)" = "$TASK5_PLAN_COMMIT"
  test "$(task5_receipt_value "$review_identity" D)" = \
    "$TASK5_EXPECTED_PARENT"
  test "$(task5_receipt_value "$review_identity" plan-path)" = \
    "$TASK5_PLAN_PATH"
  test "$(task5_receipt_value "$review_identity" amendment)" = \
    U-T5-C53-INTERMEDIATE-READY-01
  test "$(task5_receipt_value "$review_identity" \
    implementation-actor-reference)" = "$implementation_actor_reference"
  test "$(task5_receipt_value "$review_identity" \
    spec-reviewer-reference)" = "$p_spec_reviewer_reference"
  test "$(task5_receipt_value "$review_identity" \
    quality-reviewer-reference)" = "$p_quality_reviewer_reference"
  for review_sha_field in plan-sha256 checker-sha256 runtime-sha256 \
      bootstrap-sha256 canonical-mutation-manifest-sha256 \
      core-manifest-sha256; do
    test "$(task5_receipt_value "$review_identity" "$review_sha_field")" = \
      "$(task5_receipt_value "$receipt" "$review_sha_field")"
  done
  test "$(task5_sha256 "$review_plan")" = \
    "$(task5_receipt_value "$receipt" plan-sha256)"
  test "$(task5_sha256 "$review_checker")" = \
    "$(task5_receipt_value "$receipt" checker-sha256)"
  test "$(task5_sha256 "$review_runtime")" = \
    "$(task5_receipt_value "$receipt" runtime-sha256)"
  test "$(task5_sha256 "$review_bootstrap")" = \
    "$(task5_receipt_value "$receipt" bootstrap-sha256)"
  test "$(task5_sha256 "$review_mutations")" = \
    "$(task5_receipt_value "$receipt" canonical-mutation-manifest-sha256)"
  test "$(task5_sha256 "$review_core")" = \
    "$(task5_receipt_value "$receipt" core-manifest-sha256)"
  test "$(task5_sha256 "$approval_text")" = \
    "$(task5_receipt_value "$receipt" approval-text-sha256)"
  test "$(task5_sha256 "$approval_reference")" = \
    "$(task5_receipt_value "$receipt" approval-reference-sha256)"
  test "$(grep -Fxc "P=$TASK5_PLAN_COMMIT" "$approval_text")" = 1
  test "$(grep -Fxc 'AMENDMENT=U-T5-C53-INTERMEDIATE-READY-01' \
    "$approval_text")" = 1
  test "$(grep -Fxc "IMPLEMENTATION-ACTOR-REFERENCE=$implementation_actor_reference" \
    "$approval_text")" = 1
  test "$(grep -Fxc 'DECISION=APPROVE' "$approval_text")" = 1
  test "$(grep -Ec '^P=' "$approval_text")" = 1
  test "$(grep -Ec '^AMENDMENT=' "$approval_text")" = 1
  test "$(grep -Ec '^IMPLEMENTATION-ACTOR-REFERENCE=' \
    "$approval_text")" = 1
  test "$(grep -Ec '^DECISION=' "$approval_text")" = 1
  task5_require_no_nul_file "$approval_text"
  approval_coordination_reference="$(task5_read_coordination_reference_file \
    "$approval_reference")"
  for lane in spec quality; do
    response="$TASK5_AUTHORITY_BUNDLE_ROOT/P.$lane.response.md"
    identity="$TASK5_AUTHORITY_BUNDLE_ROOT/P.$lane.identity"
    task5_require_owned_regular "$response" 400
    task5_require_owned_regular "$identity" 400
    response_sha="$(task5_sha256 "$response")"
    test "$response_sha" = \
      "$(task5_receipt_value "$receipt" "$lane-response-sha256")"
    test "$(grep -Fxc "PACKAGE-SHA256: $review_package_sha" \
      "$response")" = 1
    test "$(grep -Ec '^PACKAGE-SHA256:' "$response")" = 1
    if test "$lane" = spec; then
      expected_reviewer_reference="$p_spec_reviewer_reference"
    else
      expected_reviewer_reference="$p_quality_reviewer_reference"
    fi
    test "$(grep -Fxc "REVIEWER-REFERENCE: $expected_reviewer_reference" \
      "$response")" = 1
    test "$(grep -Ec '^REVIEWER-REFERENCE:' "$response")" = 1
    test "$(grep -Fxc "IMPLEMENTATION-ACTOR-REFERENCE: $implementation_actor_reference" \
      "$response")" = 1
    test "$(grep -Ec '^IMPLEMENTATION-ACTOR-REFERENCE:' "$response")" = 1
    test "$(grep -Ec '^VERDICT:' "$response")" = 1
    test "$(grep -Ec \
      '^VERDICT: APPROVE CRITICAL=0 IMPORTANT=0 MINOR=[0-9]+$' \
      "$response")" = 1
    task5_require_minor_dispositions "$response"
    test "$(wc -l < "$identity" | tr -d '[:space:]')" = 6
    test "$(task5_receipt_value "$identity" checkpoint)" = P
    test "$(task5_receipt_value "$identity" lane)" = "$lane"
    test "$(task5_receipt_value "$identity" package-sha256)" = \
      "$review_package_sha"
    test "$(task5_receipt_value "$identity" response-sha256)" = \
      "$response_sha"
    test "$(task5_receipt_value "$identity" reviewer-reference)" = \
      "$expected_reviewer_reference"
    test "$(task5_receipt_value "$identity" \
      implementation-actor-reference)" = "$implementation_actor_reference"
  done
)

task5_require_physical_descendant() (
  set -euo pipefail
  test "$#" = 3
  ancestor="$1"
  child="$2"
  mode="$3"
  task5_require_owned_directory "$ancestor" 700
  task5_require_owned_directory "$child" "$mode"
  physical_ancestor="$(cd "$ancestor" && pwd -P)"
  physical_child="$(cd "$child" && pwd -P)"
  case "$physical_child" in
    "$physical_ancestor"/*) ;;
    *) task5_fail "directory is not beneath authenticated ancestor" ;;
  esac
)

task5_require_checkpoint() {
  test "$#" = 1
  case "$1" in
    P|C51|C52|C53|C53C1|C53C2|R) ;;
    *) task5_fail "checkpoint is outside the closed Task 5 lineage" ;;
  esac
}

task5_require_commit_checkpoint() {
  test "$#" = 1
  case "$1" in
    C51|C52|C53|C53C1|C53C2|R) ;;
    *) task5_fail "checkpoint is not controller-committable" ;;
  esac
}

task5_require_review_target() {
  test "$#" = 1
  case "$1" in
    C51|C52|C53|C53C1|C53C2|FINAL|R) ;;
    *) task5_fail "target is outside the closed Task 5 review set" ;;
  esac
}

task5_require_review_lane() {
  test "$#" = 1
  case "$1" in
    spec|quality) ;;
    *) task5_fail "review lane must be spec or quality" ;;
  esac
}

task5_read_review_assignment() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 2 || return 1
  checkpoint="$1"
  lane="$2"
  task5_require_review_target "$checkpoint" || return 1
  task5_require_review_lane "$lane" || return 1
  assignment_path="$TASK5_REVIEW_INBOX_ROOT/$checkpoint.$lane.reviewer-reference"
  task5_read_coordination_reference_file "$assignment_path"
)

task5_require_state() {
  test "$#" = 1
  case "$1" in
    clean|tests-staged|green-staged|report-candidate|report-staged|committed) ;;
    *) task5_fail "state is outside the closed authentication enum" ;;
  esac
}

task5_alias_path() {
  test "$#" = 2
  evidence_root="$1"
  checkpoint="$2"
  task5_require_evidence_root "$evidence_root"
  task5_require_checkpoint "$checkpoint"
  case "$checkpoint" in
    P) printf '%s\n' "$evidence_root/P.alias" ;;
    *) printf '%s\n' "$evidence_root/aliases/$checkpoint.alias" ;;
  esac
}

task5_resolve_alias() (
  set -euo pipefail
  test "$#" = 2
  alias_path="$(task5_alias_path "$1" "$2")"
  task5_require_owned_regular "$alias_path" 600
  test "$(wc -l < "$alias_path" | tr -d '[:space:]')" = 1
  alias_oid="$(cat "$alias_path")"
  case "$alias_oid" in
    ????????????????????????????????????????) ;;
    *) task5_fail "alias is not a full commit OID" ;;
  esac
  case "$alias_oid" in
    *[!0123456789abcdef]*) task5_fail "alias is not lowercase hexadecimal" ;;
  esac
  printf '%s\n' "$alias_oid"
)

task5_create_alias() (
  set -euo pipefail
  umask 077
  test "$#" = 3
  evidence_root="$1"
  checkpoint="$2"
  alias_oid="$3"
  task5_require_commit_checkpoint "$checkpoint"
  alias_path="$(task5_alias_path "$evidence_root" "$checkpoint")"
  task5_require_absent_path "$alias_path"
  case "$alias_oid" in
    ????????????????????????????????????????) ;;
    *) task5_fail "new alias is not a full commit OID" ;;
  esac
  case "$alias_oid" in
    *[!0123456789abcdef]*) task5_fail "new alias is not lowercase hexadecimal" ;;
  esac
  printf '%s\n' "$alias_oid" > "$alias_path"
  chmod 600 "$alias_path"
  task5_require_owned_regular "$alias_path" 600
  test "$(cat "$alias_path")" = "$alias_oid"
)

task5_require_execution_identity() (
  set -euo pipefail
  export LC_ALL=C
  expected_root=/Users/jlsor/Documents/Research/SSR/.worktrees/ssr-oracle-passive-trace
  expected_branch=refs/heads/codex/oracle-passive-task5-rebase
  expected_parent=9f69d2c40406461a28f018290d579cf313f22287
  expected_subject='docs: plan Task 5 passive driver completion'
  expected_plan=docs/superpowers/plans/2026-08-07-task-5-passive-driver.md
  test "${TASK5_EXECUTION_ROOT-}" = "$expected_root"
  test "${TASK5_PLAN_PATH-}" = "$expected_plan"
  test "${TASK5_EXPECTED_BRANCH-}" = "$expected_branch"
  test "${TASK5_EXPECTED_PARENT-}" = "$expected_parent"
  test "${TASK5_EXPECTED_SUBJECT-}" = "$expected_subject"
  execution_root="$(cd "$TASK5_EXECUTION_ROOT" && pwd -P)"
  test "$execution_root" = "$expected_root"
  task5_require_evidence_root "${TASK5_EVIDENCE_ROOT-}"
  test "${TASK5_COMMANDS_ROOT-}" = "$TASK5_EVIDENCE_ROOT/commands"
  task5_require_owned_directory "$TASK5_COMMANDS_ROOT" 700
  task5_require_physical_descendant \
    "$TASK5_COMMANDS_ROOT" "${TASK5_ACTION_DIR-}" 700
  test "${TASK5_REVIEW_PACKAGES_ROOT-}" = \
    "$TASK5_EVIDENCE_ROOT/review-packages"
  test "${TASK5_REVIEW_INBOX_ROOT-}" = "$TASK5_EVIDENCE_ROOT/review-inbox"
  test "${TASK5_REVIEW_RESPONSES_ROOT-}" = \
    "$TASK5_EVIDENCE_ROOT/review-responses"
  test "${TASK5_STATE_ROOT-}" = "$TASK5_EVIDENCE_ROOT/state"
  test "${TASK5_REPORT_GATES_ROOT-}" = "$TASK5_EVIDENCE_ROOT/report-gates"
  test "${TASK5_AUTHORITY_BUNDLE_ROOT-}" = \
    "$TASK5_EVIDENCE_ROOT/authority-bundle"
  task5_require_sha256 "${TASK5_AUTHORITY_BUNDLE_SHA-}"
  task5_require_sha256 "${TASK5_BOOTSTRAP_SHA-}"
  task5_require_sha256 "${TASK5_CANONICAL_MUTATION_MANIFEST_SHA-}"
  for controlled_root in "$TASK5_REVIEW_PACKAGES_ROOT" \
      "$TASK5_REVIEW_INBOX_ROOT" "$TASK5_REVIEW_RESPONSES_ROOT" \
      "$TASK5_STATE_ROOT" "$TASK5_REPORT_GATES_ROOT"; do
    task5_require_owned_directory "$controlled_root" 700
    test "$(cd "$controlled_root/.." && pwd -P)" = "$TASK5_EVIDENCE_ROOT"
  done
  test "${TASK5_P_ALIAS-}" = "$TASK5_EVIDENCE_ROOT/P.alias"
  test -f "$TASK5_P_ALIAS"
  test ! -L "$TASK5_P_ALIAS"
  test "$(stat -f '%Lp' "$TASK5_P_ALIAS")" = 600
  test "$(stat -f '%u' "$TASK5_P_ALIAS")" = "$(id -u)"
  test "$(wc -l < "$TASK5_P_ALIAS" | tr -d '[:space:]')" = 1
  plan_commit="$(cat "$TASK5_P_ALIAS")"
  test "$plan_commit" = "${TASK5_PLAN_COMMIT-}"
  case "$plan_commit" in
    ????????????????????????????????????????) ;;
    *) task5_fail "P alias is not a full commit OID" ;;
  esac
  case "$plan_commit" in
    *[!0123456789abcdef]*) task5_fail "P alias is not lowercase hexadecimal" ;;
  esac
  test "$(git -C "$execution_root" rev-parse --verify "$plan_commit^{commit}")" = "$plan_commit"
  test "$(git -C "$execution_root" show -s --format=%s "$plan_commit")" = "$expected_subject"
  test "$(git -C "$execution_root" rev-list --parents -n 1 "$plan_commit")" = \
    "$plan_commit $expected_parent"
  test "$(git -C "$execution_root" diff-tree --no-commit-id --name-only -r "$plan_commit")" = \
    "$expected_plan"
  task5_require_p_identity "$plan_commit" "$execution_root"
  task5_require_authority_bundle
  runtime_mutation_manifest_sha="$(task5_canonical_mutation_manifest | awk \
    '$0 == "# TASK5-CANONICAL-MUTATION-MANIFEST-BEGIN" {inside=1; next} \
     $0 == "# TASK5-CANONICAL-MUTATION-MANIFEST-END" {inside=0} \
     inside {print}' | shasum -a 256 | awk '{print $1}')"
  test "$runtime_mutation_manifest_sha" = "$TASK5_CANONICAL_MUTATION_MANIFEST_SHA"
  head_commit="$(git -C "$execution_root" rev-parse HEAD)"
  git -C "$execution_root" merge-base --is-ancestor "$plan_commit" "$head_commit"
  test "$(git -C "$execution_root" symbolic-ref -q HEAD)" = "$expected_branch"

  git_dir_token="$(git -C "$execution_root" rev-parse --git-dir)"
  case "$git_dir_token" in
    /*) git_dir="$(cd "$git_dir_token" && pwd -P)" ;;
    *) git_dir="$(cd "$execution_root/$git_dir_token" && pwd -P)" ;;
  esac
  common_dir_token="$(git -C "$execution_root" rev-parse --git-common-dir)"
  case "$common_dir_token" in
    /*) common_dir="$(cd "$common_dir_token" && pwd -P)" ;;
    *) common_dir="$(cd "$execution_root/$common_dir_token" && pwd -P)" ;;
  esac
  test "$git_dir" != "$common_dir"
  record="$(git -C "$execution_root" worktree list --porcelain | \
    awk -v wanted="worktree $execution_root" '
      $1 == "worktree" { selected = ($0 == wanted) }
      selected { print }
    ')"
  test "$(printf '%s\n' "$record" | awk -v wanted="worktree $execution_root" \
    '$0 == wanted {n++} END {print n + 0}')" = 1
  test "$(printf '%s\n' "$record" | awk -v wanted="HEAD $head_commit" \
    '$0 == wanted {n++} END {print n + 0}')" = 1
  test "$(printf '%s\n' "$record" | awk -v wanted="branch $expected_branch" \
    '$0 == wanted {n++} END {print n + 0}')" = 1
  test "$(printf '%s\n' "$record" | \
    awk '/^(detached|locked|prunable)([[:space:]]|$)/ {n++} END {print n + 0}')" = 0
  test -f "${TASK5_DRIVER_PATH-}"
  test ! -L "$TASK5_DRIVER_PATH"
  test "$(stat -f '%Lp' "$TASK5_DRIVER_PATH")" = 400
  test "$(stat -f '%u' "$TASK5_DRIVER_PATH")" = "$(id -u)"
  task5_require_sha256 "${TASK5_DRIVER_SHA-}"
  test "$(task5_sha256 "$TASK5_DRIVER_PATH")" = "$TASK5_DRIVER_SHA"
  task5_require_owned_regular "${TASK5_PLAN_AUDITOR_PATH-}" 400
  task5_require_sha256 "${TASK5_PLAN_AUDITOR_SHA-}"
  test "$(task5_sha256 "$TASK5_PLAN_AUDITOR_PATH")" = \
    "$TASK5_PLAN_AUDITOR_SHA"
)

task5_require_clean_controller() (
  set -euo pipefail
  test "$#" = 2
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  task5_require_evidence_root "$evidence_root"
  test "${TASK5_CLEAN_CONTROLLER-}" = 1
  test "${TASK5_EXECUTION_ROOT-}" = "$repo_root"
  test "${TASK5_EVIDENCE_ROOT-}" = "$evidence_root"
  test "${TASK5_PLAN_PATH-}" = \
    docs/superpowers/plans/2026-08-07-task-5-passive-driver.md
  test "${TASK5_P_ALIAS-}" = "$evidence_root/P.alias"
  test "${TASK5_COMMANDS_ROOT-}" = "$evidence_root/commands"
  test "${TASK5_AUTHORITY_BUNDLE_ROOT-}" = \
    "$evidence_root/authority-bundle"
  task5_require_sha256 "${TASK5_AUTHORITY_BUNDLE_SHA-}"
  task5_require_sha256 "${TASK5_BOOTSTRAP_SHA-}"
  task5_require_sha256 "${TASK5_CANONICAL_MUTATION_MANIFEST_SHA-}"
  task5_require_physical_descendant \
    "$TASK5_COMMANDS_ROOT" "${TASK5_ACTION_DIR-}" 700
  test "${PATH-}" = \
    /usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Cellar/dotnet/10.0.300/bin
  test "${LC_ALL-}" = C
  test "${LANG-}" = C
  test "${GIT_CONFIG_NOSYSTEM-}" = 1
  test "${GIT_CONFIG_GLOBAL-}" = /dev/null
  test "${GIT_TERMINAL_PROMPT-}" = 0
  test "${UV_OFFLINE-}" = 1
  test "${PIP_NO_INDEX-}" = 1
  task5_require_sha256 "${TASK5_DRIVER_SHA-}"
)

task5_physical_repo_root() (
  set -euo pipefail
  test "$#" = 1
  physical_root="$(cd "$1" && pwd -P)"
  test "$(git -C "$physical_root" rev-parse --show-toplevel)" = "$physical_root"
  printf '%s\n' "$physical_root"
)

task5_require_evidence_root() (
  set -euo pipefail
  test "$#" = 1
  supplied_root="$1"
  test -d "$supplied_root"
  test ! -L "$supplied_root"
  physical_root="$(cd "$supplied_root" && pwd -P)"
  test "$supplied_root" = "$physical_root"
  physical_parent="$(cd "$physical_root/.." && pwd -P)"
  test "$physical_parent" = /private/tmp
  root_name="${physical_root##*/}"
  case "$root_name" in
    ssr-task5-evidence.*) ;;
    *) task5_fail "evidence root is outside the Task 5 namespace" ;;
  esac
  root_suffix="${root_name#ssr-task5-evidence.}"
  case "$root_suffix" in
    ''|*..*|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-]*)
      task5_fail "unsafe evidence-root suffix" ;;
  esac
  test "$(stat -f '%Lp' "$physical_root")" = 700
  test "$(stat -f '%u' "$physical_root")" = "$(id -u)"
)

task5_init_evidence_root() (
  set -euo pipefail
  umask 077
  evidence_root="$(mktemp -d /private/tmp/ssr-task5-evidence.XXXXXXXX)"
  test -d "$evidence_root"
  test ! -L "$evidence_root"
  chmod 700 "$evidence_root"
  test "$(stat -f '%Lp' "$evidence_root")" = 700
  test "$(stat -f '%u' "$evidence_root")" = "$(id -u)"
  printf '%s\n' "$evidence_root"
)

task5_init_artifact_dir() (
  set -euo pipefail
  umask 077
  test "$#" = 2
  evidence_root="$1"
  artifact_name="$2"
  task5_require_evidence_root "$evidence_root"
  case "$artifact_name" in
    ''|*..*|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-]*)
      task5_fail "unsafe artifact directory name" ;;
  esac
  task5_require_physical_descendant \
    "$TASK5_COMMANDS_ROOT" "$TASK5_ACTION_DIR" 700
  artifact_dir="$TASK5_ACTION_DIR/$artifact_name"
  task5_require_absent_path "$artifact_dir"
  mkdir -m 700 "$artifact_dir"
  task5_require_owned_directory "$artifact_dir" 700
  test "$(cd "$artifact_dir/.." && pwd -P)" = "$TASK5_ACTION_DIR"
  printf '%s\n' "$artifact_dir"
)

task5_write_patch_path_manifest() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 3
  patch_id="$1"
  manifest_kind="$2"
  output_path="$3"
  task5_require_absent_path "$output_path"
  case "$manifest_kind" in
    patch|prior) ;;
    *) task5_fail "invalid patch-manifest kind" ;;
  esac
  case "$patch_id:$manifest_kind" in
    C51-TESTS:patch)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C51-PRODUCTION:patch)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverInput.cs > "$output_path" ;;
    C51-PRODUCTION:prior)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C52-TESTS:patch)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C52-PRODUCTION:patch)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverInput.cs \
        oracle/plugin/Core/PassiveDriverLifecycleHooks.cs > "$output_path" ;;
    C52-PRODUCTION:prior)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C53-TESTS:patch)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs \
        oracle/plugin/tests/PassiveDriverTests.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C53-PRODUCTION:patch)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverCompletion.cs \
        oracle/plugin/Core/PassiveDriverInput.cs > "$output_path" ;;
    C53-PRODUCTION:prior)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs \
        oracle/plugin/tests/PassiveDriverTests.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C53C1-TESTS:patch)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs > "$output_path" ;;
    C53C1-PRODUCTION:patch)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverCompletion.cs \
        oracle/plugin/Core/PassiveDriverInput.cs > "$output_path" ;;
    C53C1-PRODUCTION:prior)
      printf '%s\n' \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs > "$output_path" ;;
    C53C2-TESTS:patch)
      printf '%s\n' oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        > "$output_path" ;;
    C53C2-PRODUCTION:patch)
      printf '%s\n' oracle/plugin/Core/PassiveDriverInput.cs \
        > "$output_path" ;;
    C53C2-PRODUCTION:prior)
      printf '%s\n' oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        > "$output_path" ;;
    *-TESTS:prior) : > "$output_path" ;;
    *) task5_fail "unsupported patch ID/kind" ;;
  esac
  sorted_path="$output_path.sorted"
  task5_require_absent_path "$sorted_path"
  sort -u "$output_path" > "$sorted_path"
  cmp -s "$output_path" "$sorted_path"
  task5_require_owned_regular "$output_path"
  task5_require_owned_regular "$sorted_path"
)

task5_extract_and_stage_plan_patch() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 10
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  plan_commit="$3"
  plan_path="$4"
  patch_id="$5"
  expected_sha="$6"
  expected_lines="$7"
  expected_bytes="$8"
  expected_head="$9"
  expected_before_tree="${10}"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  task5_require_sha256 "$expected_sha"
  case "$plan_commit" in
    ????????????????????????????????????????) ;;
    *) task5_fail "plan commit must be a full 40-character OID" ;;
  esac
  case "$plan_commit" in
    *[!0123456789abcdef]*) task5_fail "plan OID must be lowercase hexadecimal" ;;
  esac
  case "$plan_path" in
    ''|/*|*:*|*'..'*|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._/-]*)
      task5_fail "unsafe committed plan path" ;;
  esac
  test "$plan_path" = docs/superpowers/plans/2026-08-07-task-5-passive-driver.md
  test "$plan_commit" = "${TASK5_PLAN_COMMIT-}"
  case "$patch_id" in
    ''|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-]*)
      task5_fail "unsafe patch ID" ;;
  esac
  case "$patch_id" in
    C51-TESTS)
      catalog_sha=27b5d2da89f011a1e3c84a6cb27077ad093e46ab3ac05bb4bef4386c8c73d6eb
      catalog_lines=1213
      catalog_bytes=51384
      expected_metadata='**C51-TESTS patch:** SHA-256 `27b5d2da89f011a1e3c84a6cb27077ad093e46ab3ac05bb4bef4386c8c73d6eb`; 1213 LF lines; 51384 bytes.' ;;
    C51-PRODUCTION)
      catalog_sha=dc60e234556f4cd5717dab1422c18edc63e42a87046200c135ff5f8fc32755c0
      catalog_lines=752
      catalog_bytes=23537
      expected_metadata='**C51-PRODUCTION patch:** SHA-256 `dc60e234556f4cd5717dab1422c18edc63e42a87046200c135ff5f8fc32755c0`; 752 LF lines; 23537 bytes.' ;;
    C52-TESTS)
      catalog_sha=13beee22b9b661320226c8deeb7979c574918d50c30b9f4498f5d35a9294e80c
      catalog_lines=880
      catalog_bytes=39208
      expected_metadata='**C52-TESTS patch:** SHA-256 `13beee22b9b661320226c8deeb7979c574918d50c30b9f4498f5d35a9294e80c`; 880 LF lines; 39208 bytes.' ;;
    C52-PRODUCTION)
      catalog_sha=69f717ed83deb3ff86fed13798764aa29f0120b29b7a649104d6cace218edd7e
      catalog_lines=395
      catalog_bytes=12407
      expected_metadata='**C52-PRODUCTION patch:** SHA-256 `69f717ed83deb3ff86fed13798764aa29f0120b29b7a649104d6cace218edd7e`; 395 LF lines; 12407 bytes.' ;;
    C53-TESTS)
      catalog_sha=d56cb0b64868120338b27ced71299da7b78a87187a7b8dfa70b63bde329e7dcc
      catalog_lines=1123
      catalog_bytes=43301
      expected_metadata='**C53-TESTS patch:** SHA-256 `d56cb0b64868120338b27ced71299da7b78a87187a7b8dfa70b63bde329e7dcc`; 1123 LF lines; 43301 bytes.' ;;
    C53-PRODUCTION)
      catalog_sha=918cbac02ec8e01ee61e89c0b5418d6430547c33b46ea949bc9f073943dc298c
      catalog_lines=159
      catalog_bytes=5310
      expected_metadata='**C53-PRODUCTION patch:** SHA-256 `918cbac02ec8e01ee61e89c0b5418d6430547c33b46ea949bc9f073943dc298c`; 159 LF lines; 5310 bytes.' ;;
    C53C1-TESTS)
      catalog_sha=a37a0ea03c285bfc8d8068bbb7179787293ce925dc8d7c42ad47a9b53ada0112
      catalog_lines=2468
      catalog_bytes=95234
      expected_metadata='**C53C1-TESTS patch:** SHA-256 `a37a0ea03c285bfc8d8068bbb7179787293ce925dc8d7c42ad47a9b53ada0112`; 2468 LF lines; 95234 bytes.' ;;
    C53C1-PRODUCTION)
      catalog_sha=7c000fabda103b116b7a5ebc773da13692d3b4a838dcf280dd68b7ab5590102c
      catalog_lines=598
      catalog_bytes=18412
      expected_metadata='**C53C1-PRODUCTION patch:** SHA-256 `7c000fabda103b116b7a5ebc773da13692d3b4a838dcf280dd68b7ab5590102c`; 598 LF lines; 18412 bytes.' ;;
    C53C2-TESTS)
      catalog_sha=175d83ab045a264e76f537b5c4d94ea3f945ac874bf7caa6417de2183976ece1
      catalog_lines=190
      catalog_bytes=7397
      expected_metadata='**C53C2-TESTS patch:** SHA-256 `175d83ab045a264e76f537b5c4d94ea3f945ac874bf7caa6417de2183976ece1`; 190 LF lines; 7397 bytes.' ;;
    C53C2-PRODUCTION)
      catalog_sha=0ee216ead3ab2bd602bbcd42aa67eda31943f55db558250288452b785053354e
      catalog_lines=23
      catalog_bytes=1011
      expected_metadata='**C53C2-PRODUCTION patch:** SHA-256 `0ee216ead3ab2bd602bbcd42aa67eda31943f55db558250288452b785053354e`; 23 LF lines; 1011 bytes.' ;;
    *) task5_fail "patch ID is outside the exact Task 5 implementation set" ;;
  esac
  test "$expected_sha" = "$catalog_sha"
  test "$expected_lines" = "$catalog_lines"
  test "$expected_bytes" = "$catalog_bytes"
  case "$expected_lines:$expected_bytes" in
    *[!0123456789:]*) task5_fail "patch counts must be decimal" ;;
  esac
  test "$expected_lines" -gt 0
  test "$expected_bytes" -gt 0
  case "$expected_head:$expected_before_tree" in
    *[!0123456789abcdef:]*) task5_fail "expected Git IDs must be lowercase hexadecimal" ;;
  esac
  test "${#expected_head}" = 40
  test "${#expected_before_tree}" = 40
  test "$(git -C "$repo_root" rev-parse --verify "$plan_commit^{commit}")" = "$plan_commit"
  git -C "$repo_root" cat-file -e "$plan_commit:$plan_path"

  begin_marker="<!-- TASK5-PATCH-BEGIN:$patch_id -->"
  end_marker="<!-- TASK5-PATCH-END:$patch_id -->"
  blob_path="$TASK5_ACTION_DIR/$patch_id.plan-blob.md"
  patch_path="$TASK5_ACTION_DIR/$patch_id.patch"
  cached_path="$TASK5_ACTION_DIR/$patch_id.cached.diff"
  expected_patch_paths="$TASK5_ACTION_DIR/$patch_id.expected-patch-paths"
  expected_prior_paths="$TASK5_ACTION_DIR/$patch_id.expected-prior-paths"
  actual_patch_paths="$TASK5_ACTION_DIR/$patch_id.actual-patch-paths"
  actual_prior_paths="$TASK5_ACTION_DIR/$patch_id.actual-prior-paths"
  task5_require_absent_path "$blob_path"
  task5_require_absent_path "$patch_path"
  task5_require_absent_path "$cached_path"
  task5_write_patch_path_manifest "$patch_id" patch "$expected_patch_paths"
  task5_write_patch_path_manifest "$patch_id" prior "$expected_prior_paths"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$expected_head"
  test "$(git -C "$repo_root" write-tree)" = "$expected_before_tree"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  git -C "$repo_root" diff --cached --name-only --diff-filter=ACDMRTUXB \
    | sort -u > "$actual_prior_paths"
  cmp -s "$actual_prior_paths" "$expected_prior_paths"
  if test ! -s "$expected_prior_paths"; then
    git -C "$repo_root" diff --cached --quiet
    test "$expected_before_tree" = \
      "$(git -C "$repo_root" rev-parse "$expected_head^{tree}")"
  fi
  git -C "$repo_root" show "$plan_commit:$plan_path" > "$blob_path"
  test "$(awk -v marker="$begin_marker" '$0 == marker {n++} END {print n + 0}' "$blob_path")" = 1
  test "$(awk -v marker="$end_marker" '$0 == marker {n++} END {print n + 0}' "$blob_path")" = 1
  begin_line="$(awk -v marker="$begin_marker" '$0 == marker {print NR}' "$blob_path")"
  end_line="$(awk -v marker="$end_marker" '$0 == marker {print NR}' "$blob_path")"
  test "$begin_line" -lt "$end_line"
  test "$(sed -n "$((begin_line - 1))p" "$blob_path")" = "$expected_metadata"
  opening_count="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && $0 == "~~~diff" {n++} END {print n + 0}' "$blob_path")"
  closing_count="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && $0 == "~~~" {n++} END {print n + 0}' "$blob_path")"
  delimiter_count="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && substr($0, 1, 3) == "~~~" {n++} END {print n + 0}' "$blob_path")"
  nested_marker_count="$(awk -v first="$begin_line" -v last="$end_line" '
    NR > first && NR < last &&
      ($0 ~ /^<!--[[:space:]]*TASK5-PATCH-BEGIN:/ ||
       $0 ~ /^<!--[[:space:]]*TASK5-PATCH-END:/) {n++}
    END {print n + 0}
  ' "$blob_path")"
  test "$opening_count" = 1
  test "$closing_count" = 1
  test "$delimiter_count" = 2
  test "$nested_marker_count" = 0
  opening_line="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && $0 == "~~~diff" {print NR}' "$blob_path")"
  closing_line="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && $0 == "~~~" {print NR}' "$blob_path")"
  test "$opening_line" = "$((begin_line + 1))"
  test "$closing_line" = "$((end_line - 1))"
  test "$opening_line" -lt "$closing_line"
  awk -v first="$opening_line" -v last="$closing_line" \
    'NR > first && NR < last {print}' "$blob_path" > "$patch_path"
  test "$(awk 'index($0, sprintf("%c", 13)) {n++} END {print n + 0}' "$patch_path")" = 0
  test "$(tail -c 1 "$patch_path" | od -An -tu1 | tr -d '[:space:]')" = 10
  test "$(task5_sha256 "$patch_path")" = "$expected_sha"
  test "$(wc -l < "$patch_path" | tr -d '[:space:]')" = "$expected_lines"
  test "$(wc -c < "$patch_path" | tr -d '[:space:]')" = "$expected_bytes"
  awk '
    $1 == "diff" && $2 == "--git" {
      diffs++
      if (substr($3, 1, 2) != "a/" || substr($4, 1, 2) != "b/")
        exit 70
      left = substr($3, 3)
      right = substr($4, 3)
      if (left != right || left == "" || left ~ /[[:space:]]/)
        exit 71
      print left
      next
    }
    $1 == "index" {
      token = $2
      if (length(token) != 82 || substr(token, 41, 2) != "..")
        exit 72
      left = substr(token, 1, 40)
      right = substr(token, 43, 40)
      check = left right
      gsub(/[0123456789abcdef]/, "", check)
      if (check != "")
        exit 73
      indexes++
    }
    END {
      if (diffs == 0 || indexes != diffs)
        exit 74
    }
  ' "$patch_path" | sort -u > "$actual_patch_paths"
  cmp -s "$actual_patch_paths" "$expected_patch_paths"

  cd "$repo_root"
  before_tree="$(git write-tree)"
  test "$before_tree" = "$expected_before_tree"
  git apply --check --index --whitespace=error-all "$patch_path"
  git apply --index --whitespace=error-all "$patch_path"
  git diff --cached --binary --full-index --no-ext-diff "$before_tree" -- > "$cached_path"
  cmp -s "$patch_path" "$cached_path"
  test "$(task5_sha256 "$cached_path")" = "$expected_sha"
  test "$(wc -l < "$cached_path" | tr -d '[:space:]')" = "$expected_lines"
  test "$(wc -c < "$cached_path" | tr -d '[:space:]')" = "$expected_bytes"
  git diff --cached --check
  printf '%s  %s lines  %s bytes  %s\n' \
    "$expected_sha" "$expected_lines" "$expected_bytes" "$patch_id"
)

task5_authenticate_checkpoint_index() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  parent_tree="$4"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  case "$parent_tree" in
    *[!0123456789abcdef]*) task5_fail "parent tree must be lowercase hexadecimal" ;;
  esac
  test "${#parent_tree}" = 40
  case "$checkpoint" in
    C51)
      tests_id=C51-TESTS
      production_id=C51-PRODUCTION
      expected_sha=544518e3a90c03f7f9af944deb34fa43a4a9f4236d8033b8ee765a874064ed56
      expected_lines=1965
      expected_bytes=74921
      expected_plugin=694928891148bfad6b4215f9d4efbb943f44a104
      expected_core=26a0c6acfc7b9ce22f5f93a879b462bf721baa33
      expected_tests=2fa6213f563d4a8d9aa01f1cb590f34b04f34e8e ;;
    C52)
      tests_id=C52-TESTS
      production_id=C52-PRODUCTION
      expected_sha=b5f9b19188eca3bd1ff856086d06254fd95dc23efe34d844601d42e4e352d8f0
      expected_lines=1275
      expected_bytes=51615
      expected_plugin=1a3379be8b250f1a0ef6020ca2265be98ec1353a
      expected_core=81fe40cec8877c937ed2b7f9e9dca967d5179add
      expected_tests=c2a8b9b184298fb75659c345e0c1aec493ff4b73 ;;
    C53)
      tests_id=C53-TESTS
      production_id=C53-PRODUCTION
      expected_sha=9bf687e61eecaeb4786b16f9b08e7b5bfa0f46d5f24fe69b4cacfa89425f56c2
      expected_lines=1282
      expected_bytes=48611
      expected_plugin=1364987fc311b8ade46ac8599f06140befd50d7d
      expected_core=f709ff7d0496ee8214f582eb1a7d0dadd895941f
      expected_tests=c6a18ad771bf796dc91103ba19a853890e6b449a ;;
    C53C1)
      tests_id=C53C1-TESTS
      production_id=C53C1-PRODUCTION
      expected_sha=0254fc008db0fb43c7fedb5e63ead12c3450555ab84b6f500b117ed90976aca2
      expected_lines=3066
      expected_bytes=113646
      expected_plugin=8afbf9d17f762bec53f31fa30648e7a77f396085
      expected_core=d1ac5945be7ef1cb32603fe5525defd073a584d4
      expected_tests=596492b71f9e386470d5c0615543524835f3f28c ;;
    C53C2)
      tests_id=C53C2-TESTS
      production_id=C53C2-PRODUCTION
      expected_sha=98dddb0bc658e02dfb884a0f079b0bfe48b0d99f0e2d5723d458bcd275d03ccb
      expected_lines=213
      expected_bytes=8408
      expected_plugin=5a7db9d1e661dd97bd6a939d375dd2008506f679
      expected_core=531718e596ed3f49f97f92c14edc69c69d60b834
      expected_tests=b75e36e1ce25538fd1d3cdd85c49f04d003af416 ;;
    *) task5_fail "unsupported checkpoint" ;;
  esac
  test "$(git -C "$repo_root" rev-parse HEAD^{tree})" = "$parent_tree"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  full_patch="$TASK5_ACTION_DIR/$checkpoint.full-index.patch"
  expected_paths="$TASK5_ACTION_DIR/$checkpoint.expected-paths"
  actual_paths="$TASK5_ACTION_DIR/$checkpoint.actual-paths"
  tests_paths="$TASK5_ACTION_DIR/$checkpoint.tests-paths"
  production_paths="$TASK5_ACTION_DIR/$checkpoint.production-paths"
  for artifact in "$full_patch" "$expected_paths" "$actual_paths" \
      "$tests_paths" "$production_paths"; do
    task5_require_absent_path "$artifact"
  done
  task5_write_patch_path_manifest "$tests_id" patch "$tests_paths"
  task5_write_patch_path_manifest "$production_id" patch "$production_paths"
  sort -u "$tests_paths" "$production_paths" > "$expected_paths"
  git -C "$repo_root" diff --cached --binary --full-index --no-ext-diff \
    "$parent_tree" -- > "$full_patch"
  test "$(task5_sha256 "$full_patch")" = "$expected_sha"
  test "$(wc -l < "$full_patch" | tr -d '[:space:]')" = "$expected_lines"
  test "$(wc -c < "$full_patch" | tr -d '[:space:]')" = "$expected_bytes"
  git -C "$repo_root" diff --cached --name-only --diff-filter=ACDMRTUXB \
    "$parent_tree" -- | sort -u > "$actual_paths"
  cmp -s "$actual_paths" "$expected_paths"
  git -C "$repo_root" diff --cached --check
  index_tree="$(git -C "$repo_root" write-tree)"
  plugin_tree="$(git -C "$repo_root" ls-tree "$index_tree" oracle/plugin | awk '{print $3}')"
  core_tree="$(git -C "$repo_root" ls-tree "$plugin_tree" Core | awk '{print $3}')"
  tests_tree="$(git -C "$repo_root" ls-tree "$plugin_tree" tests | awk '{print $3}')"
  test "$plugin_tree" = "$expected_plugin"
  test "$core_tree" = "$expected_core"
  test "$tests_tree" = "$expected_tests"
  printf '%s full=%s index-tree=%s plugin=%s Core=%s tests=%s\n' \
    "$checkpoint" "$expected_sha" "$index_tree" \
    "$plugin_tree" "$core_tree" "$tests_tree"
)

task5_extract_plan_fence() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 12
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  output_dir="$3"
  plan_commit="$4"
  plan_path="$5"
  artifact_id="$6"
  begin_marker="$7"
  end_marker="$8"
  opening_fence="$9"
  expected_sha="${10}"
  expected_lines="${11}"
  expected_bytes="${12}"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  test -d "$output_dir"
  test ! -L "$output_dir"
  test "$(cd "$output_dir/.." && pwd -P)" = "$evidence_root"
  test "$(stat -f '%Lp' "$output_dir")" = 700
  test "$(stat -f '%u' "$output_dir")" = "$(id -u)"
  case "${output_dir##*/}" in
    ''|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-]*)
      task5_fail "unsafe artifact directory" ;;
  esac
  case "$artifact_id" in
    ''|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-]*)
      task5_fail "unsafe artifact ID" ;;
  esac
  case "$opening_fence" in
    '~~~diff'|'~~~python'|'~~~bash') ;;
    *) task5_fail "unsupported artifact fence" ;;
  esac
  case "$plan_commit" in
    ????????????????????????????????????????) ;;
    *) task5_fail "plan commit must be a full 40-character OID" ;;
  esac
  case "$plan_commit" in
    *[!0123456789abcdef]*) task5_fail "plan OID must be lowercase hexadecimal" ;;
  esac
  case "$plan_path" in
    ''|/*|*:*|*'..'*|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._/-]*)
      task5_fail "unsafe committed plan path" ;;
  esac
  test "$plan_path" = docs/superpowers/plans/2026-08-07-task-5-passive-driver.md
  test "$plan_commit" = "${TASK5_PLAN_COMMIT-}"
  case "$expected_lines:$expected_bytes" in
    *[!0123456789:]*) task5_fail "artifact counts must be decimal" ;;
  esac
  task5_require_sha256 "$expected_sha"
  test "$expected_lines" -gt 0
  test "$expected_bytes" -gt 0
  test "$(git -C "$repo_root" rev-parse --verify "$plan_commit^{commit}")" = "$plan_commit"
  git -C "$repo_root" cat-file -e "$plan_commit:$plan_path"

  blob_path="$output_dir/$artifact_id.plan-blob.md"
  artifact_path="$output_dir/$artifact_id"
  task5_require_absent_path "$blob_path"
  task5_require_absent_path "$artifact_path"
  git -C "$repo_root" show "$plan_commit:$plan_path" > "$blob_path"
  test "$(awk -v marker="$begin_marker" '$0 == marker {n++} END {print n + 0}' "$blob_path")" = 1
  test "$(awk -v marker="$end_marker" '$0 == marker {n++} END {print n + 0}' "$blob_path")" = 1
  begin_line="$(awk -v marker="$begin_marker" '$0 == marker {print NR}' "$blob_path")"
  end_line="$(awk -v marker="$end_marker" '$0 == marker {print NR}' "$blob_path")"
  test "$begin_line" -lt "$end_line"
  opening_count="$(awk -v first="$begin_line" -v last="$end_line" \
    -v fence="$opening_fence" \
    'NR > first && NR < last && $0 == fence {n++} END {print n + 0}' "$blob_path")"
  closing_count="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && $0 == "~~~" {n++} END {print n + 0}' "$blob_path")"
  delimiter_count="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && substr($0, 1, 3) == "~~~" {n++} END {print n + 0}' "$blob_path")"
  test "$opening_count" = 1
  test "$closing_count" = 1
  test "$delimiter_count" = 2
  opening_line="$(awk -v first="$begin_line" -v last="$end_line" \
    -v fence="$opening_fence" \
    'NR > first && NR < last && $0 == fence {print NR}' "$blob_path")"
  closing_line="$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && $0 == "~~~" {print NR}' "$blob_path")"
  test "$opening_line" = "$((begin_line + 1))"
  test "$closing_line" = "$((end_line - 1))"
  awk -v first="$opening_line" -v last="$closing_line" \
    'NR > first && NR < last {print}' "$blob_path" > "$artifact_path"
  test "$(awk 'index($0, sprintf("%c", 13)) {n++} END {print n + 0}' "$artifact_path")" = 0
  test "$(tail -c 1 "$artifact_path" | od -An -tu1 | tr -d '[:space:]')" = 10
  test "$(task5_sha256 "$artifact_path")" = "$expected_sha"
  test "$(wc -l < "$artifact_path" | tr -d '[:space:]')" = "$expected_lines"
  test "$(wc -c < "$artifact_path" | tr -d '[:space:]')" = "$expected_bytes"
  printf '%s  %s lines  %s bytes  %s\n' \
    "$expected_sha" "$expected_lines" "$expected_bytes" "$artifact_id"
)

task5_check_plan_narrative_whitespace() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 2
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  test "${TASK5_PLAN_PATH-}" = \
    docs/superpowers/plans/2026-08-07-task-5-passive-driver.md
  test "${TASK5_PLAN_COMMIT-}" = "$(cat "$TASK5_P_ALIAS")"
  plan_copy="$TASK5_ACTION_DIR/narrative-whitespace.plan.md"
  report="$TASK5_ACTION_DIR/narrative-whitespace.report"
  task5_require_absent_path "$plan_copy"
  test ! -L "$plan_copy"
  task5_require_absent_path "$report"
  test ! -L "$report"
  git -C "$repo_root" show \
    "$TASK5_PLAN_COMMIT:$TASK5_PLAN_PATH" > "$plan_copy"
  test "$(tail -c 1 "$plan_copy" | od -An -tu1 | tr -d '[:space:]')" = 10
  test "$(awk 'index($0, sprintf("%c", 13)) {n++} END {print n + 0}' \
    "$plan_copy")" = 0
  awk '
    function fail(message) {
      print "line " NR ": " message
      bad = 1
    }
    $0 == "~~~diff" {
      if (in_diff)
        fail("nested diff fence")
      if (previous ~ /^<!--[[:space:]]*TASK5-PATCH-BEGIN:(C51-TESTS|C51-PRODUCTION|C52-TESTS|C52-PRODUCTION|C53-TESTS|C53-PRODUCTION|C53C1-TESTS|C53C1-PRODUCTION|C53C2-TESTS|C53C2-PRODUCTION)[[:space:]]*-->$/) {
        implementation++
        kind = "catalog"
      } else if (previous ~ /^<!-- BEGIN T5M(0[1-9]|1[0-9]|2[0-8]) CANONICAL PATCH -->$/) {
        canonical++
        kind = "catalog"
      } else if (previous ~ /^<!-- BEGIN REJECTED-T5M(20-SCOPE|23-BROAD) PATCH -->$/) {
        rejected++
        kind = "catalog"
      } else if (previous == "<!-- BEGIN T5M28 TEMPORARY EXPORT HOOK -->") {
        hook++
        kind = "hook"
      } else {
        fail("unauthenticated diff fence")
        kind = "unknown"
      }
      diffs++
      in_diff = 1
      next
    }
    in_diff {
      if ($0 == "~~~") {
        in_diff = 0
        kind = ""
      } else if ($0 == " ") {
        if (kind == "hook")
          hook_single_space++
        else if (kind == "catalog")
          catalog_single_space++
      }
      next
    }
    /[ \t]+$/ { fail("narrative trailing whitespace") }
    { previous = $0 }
    END {
      if (in_diff)
        fail("unterminated diff fence")
      if (diffs != 41 || implementation != 10 || canonical != 28 ||
          rejected != 2 || hook != 1)
        fail("unexpected authenticated diff-fence counts")
      if (catalog_single_space != 105 || hook_single_space != 1)
        fail("unexpected raw-diff single-space context counts")
      printf "diffs=41 implementation=10 canonical=28 rejected=2 hook=1 catalog-single-space=105 hook-single-space=1\n"
      if (bad)
        exit 1
    }
  ' "$plan_copy" > "$report"
  test "$(cat "$report")" = \
    'diffs=41 implementation=10 canonical=28 rejected=2 hook=1 catalog-single-space=105 hook-single-space=1'
  cat "$report"
)

task5_canonicalize_cs1061_red() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 10
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  red_output="$4"
  expected_emitted="$5"
  expected_unique="$6"
  expected_full_sha="$7"
  expected_compact_sha="$8"
  expected_compact_lines="$9"
  expected_compact_bytes="${10}"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  task5_require_sha256 "$expected_full_sha"
  task5_require_sha256 "$expected_compact_sha"
  case "$checkpoint" in
    C51|C52) ;;
    *) task5_fail "compiler RED checkpoint must be C51 or C52" ;;
  esac
  case "$expected_emitted:$expected_unique:$expected_compact_lines:$expected_compact_bytes" in
    *[!0123456789:]*) task5_fail "RED counts must be decimal" ;;
  esac
  test "$expected_emitted" -gt 0
  test "$expected_unique" -gt 0
  test "$expected_compact_lines" = "$expected_unique"
  test "$expected_compact_bytes" -gt 0
  test -f "$red_output"
  test ! -L "$red_output"
  if grep -E ': warning |warning CS|error MSB|NETSDK|assets file|fixture|permission denied|Permission denied|Operation not permitted|UnauthorizedAccessException|timed out|timeout|NU1|Segmentation fault|Killed' "$red_output" >/dev/null; then
    task5_fail "$checkpoint RED contains a forbidden diagnostic"
  fi
  all_error_count="$(awk 'index($0, ": error ") != 0 {n++} END {print n + 0}' "$red_output")"
  cs1061_count="$(awk 'index($0, ": error CS1061: ") != 0 {n++} END {print n + 0}' "$red_output")"
  test "$all_error_count" = "$cs1061_count"
  test "$cs1061_count" = "$expected_emitted"
  summary_count="$(awk '
    /^[[:space:]]*[0-9]+ Error[(]s[)][[:space:]]*$/ {
      value = $0
      sub(/^[[:space:]]*/, "", value)
      sub(/[[:space:]].*$/, "", value)
      print value
    }
  ' "$red_output")"
  test "$(printf '%s\n' "$summary_count" | awk 'NF {n++} END {print n + 0}')" = 1
  test "$summary_count" = "$expected_unique"

  full_raw="$TASK5_ACTION_DIR/$checkpoint.cs1061-full.raw"
  full_path="$TASK5_ACTION_DIR/$checkpoint.cs1061-full.txt"
  unique_path="$TASK5_ACTION_DIR/$checkpoint.cs1061-full-unique.txt"
  compact_raw="$TASK5_ACTION_DIR/$checkpoint.cs1061-compact.raw"
  compact_path="$TASK5_ACTION_DIR/$checkpoint.cs1061-compact.txt"
  for artifact in "$full_raw" "$full_path" "$unique_path" "$compact_raw" "$compact_path"; do
    task5_require_absent_path "$artifact"
  done
  awk -v root="$repo_root" '
    index($0, ": error CS1061: ") != 0 {
      line = $0
      while ((at = index(line, root)) != 0)
        line = substr(line, 1, at - 1) "<WORKTREE>" substr(line, at + length(root))
      sub(/^[[:space:]]*/, "", line)
      print line
    }
  ' "$red_output" > "$full_raw"
  sort "$full_raw" > "$full_path"
  sort -u "$full_path" > "$unique_path"
  awk '
    {
      split_at = index($0, ": error CS1061: ")
      if (split_at == 0)
        exit 65
      source = substr($0, 1, split_at - 1)
      message = substr($0, split_at + length(": error CS1061: "))
      fields = split(message, quoted, "\047")
      if (fields < 5 || quoted[2] == "" || quoted[4] == "")
        exit 66
      sub(/^.*\//, "", source)
      print source ": CS1061 " quoted[2] "." quoted[4]
    }
  ' "$unique_path" > "$compact_raw"
  sort -u "$compact_raw" > "$compact_path"
  test "$(wc -l < "$unique_path" | tr -d '[:space:]')" = "$expected_unique"
  test "$(wc -l < "$compact_raw" | tr -d '[:space:]')" = "$expected_unique"
  test "$(wc -l < "$compact_path" | tr -d '[:space:]')" = "$expected_unique"
  test "$(wc -c < "$compact_path" | tr -d '[:space:]')" = "$expected_compact_bytes"
  test "$(task5_sha256 "$unique_path")" = "$expected_full_sha"
  test "$(task5_sha256 "$compact_path")" = "$expected_compact_sha"
  printf '%s emitted=%s unique=%s full=%s compact=%s compact-bytes=%s\n' \
    "$checkpoint" "$expected_emitted" "$expected_unique" \
    "$expected_full_sha" "$expected_compact_sha" "$expected_compact_bytes"
)

task5_run_compiler_red() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  task5_export_offline_environment
  task5_require_dotnet
  case "$checkpoint" in
    C51)
      expected_emitted=112
      expected_unique=56
      expected_full_sha=131716de08fd210fb96b3b6ed99e6222137f7eccf70573024cd1ad339df73b22
      expected_compact_sha=8ad0bdc10e58042f48d9e52314f96be314c15b4848fcfa2e49d0a6c21f568d44
      expected_compact_lines=56
      expected_compact_bytes=4195 ;;
    C52)
      expected_emitted=232
      expected_unique=116
      expected_full_sha=7f3ccf0944fa78360f52ab8c00731d388f4ed30d92dc9abf985db54603ba7c76
      expected_compact_sha=4222e97661293a4ff7b83a3c3e2352e56894fa7e260e8389a718667148069935
      expected_compact_lines=116
      expected_compact_bytes=8431 ;;
    *) task5_fail "compiler RED checkpoint must be C51 or C52" ;;
  esac
  dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
  unit_project="$repo_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  red_output="$TASK5_ACTION_DIR/$checkpoint.compiler-red.log"
  status_output="$TASK5_ACTION_DIR/$checkpoint.compiler-red.status"
  task5_require_absent_path "$red_output"
  task5_require_absent_path "$status_output"
  test -x "$dotnet_bin"
  test -f "$unit_project"
  set +e
  "$dotnet_bin" build "$unit_project" \
    --configuration Release --no-restore --nologo \
    -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false \
    > "$red_output" 2>&1
  red_status=$?
  set -e
  printf '%s\n' "$red_status" > "$status_output"
  test "$red_status" = 1
  test "$(awk '$0 == "Build FAILED." {n++} END {print n + 0}' \
    "$red_output")" = 1
  test "$(awk '/^[[:space:]]*0 Warning[(]s[)]$/ {n++} END {print n + 0}' \
    "$red_output")" = 1
  test "$(awk -v count="$expected_unique" '
    {
      expected = "^[[:space:]]*" count " Error[(]s[)]$"
      if ($0 ~ expected)
        n++
    }
    END {print n + 0}
  ' "$red_output")" = 1
  task5_canonicalize_cs1061_red \
    "$repo_root" "$evidence_root" "$checkpoint" "$red_output" \
    "$expected_emitted" "$expected_unique" \
    "$expected_full_sha" "$expected_compact_sha" \
    "$expected_compact_lines" "$expected_compact_bytes"
)

task5_run_behavioral_red() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  task5_export_offline_environment
  case "$checkpoint" in
    C53)
      expected_line="cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: durable Step 2 must enter Done without Ready(3) and emit End Close Complete" ;;
    C53C1)
      expected_line="cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: fault Close waits for active Run output" ;;
    C53C2)
      expected_line="cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: real Step remains durable before deferred Error second line" ;;
    *) task5_fail "behavioral RED checkpoint must be C53, C53C1, or C53C2" ;;
  esac
  artifact_dir="$(task5_init_artifact_dir "$evidence_root" "$checkpoint-behavioral-red")"
  dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
  unit_project="$repo_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  build_command="$artifact_dir/build.command"
  build_output="$artifact_dir/build.stdout-stderr"
  build_status_path="$artifact_dir/build.status"
  run_command="$artifact_dir/run.command"
  run_output="$artifact_dir/run.stdout-stderr"
  run_status_path="$artifact_dir/run.status"
  identity_path="$artifact_dir/pre-run.identity"
  status_before="$artifact_dir/pre-run.status"
  status_after="$artifact_dir/post-run.status"
  for artifact in "$build_command" "$build_output" "$build_status_path" \
      "$run_command" "$run_output" "$run_status_path" "$identity_path" \
      "$status_before" "$status_after"; do
    task5_require_absent_path "$artifact"
    test ! -L "$artifact"
  done
  printf '%s\n' \
    "$dotnet_bin build $unit_project --configuration Release --no-restore --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false" \
    > "$build_command"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  printf 'tip=%s\nindex-tree=%s\nworktree-equals-index=1\n' \
    "$(git -C "$repo_root" rev-parse HEAD)" \
    "$(git -C "$repo_root" write-tree)" > "$identity_path"
  git -C "$repo_root" status --porcelain=v1 --untracked-files=all > "$status_before"
  task5_require_dotnet
  set +e
  "$dotnet_bin" build "$unit_project" \
    --configuration Release --no-restore --nologo \
    -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false \
    > "$build_output" 2>&1
  build_status=$?
  set -e
  printf '%s\n' "$build_status" > "$build_status_path"
  test "$build_status" = 0
  task5_require_clean_build_output "$(cat "$build_output")"
  printf '%s\n' \
    "$dotnet_bin run --project $unit_project --configuration Release --no-restore --no-build -- --cohort driver-terminal" \
    > "$run_command"
  task5_require_dotnet
  set +e
  "$dotnet_bin" run --project "$unit_project" \
    --configuration Release --no-restore --no-build -- \
    --cohort driver-terminal > "$run_output" 2>&1
  run_status=$?
  set -e
  printf '%s\n' "$run_status" > "$run_status_path"
  test "$run_status" = 1
  test "$(wc -l < "$run_output" | tr -d '[:space:]')" = 1
  test "$(awk '/^cohort / {n++} END {print n + 0}' "$run_output")" = 1
  test "$(cat "$run_output")" = "$expected_line"
  git -C "$repo_root" status --porcelain=v1 --untracked-files=all > "$status_after"
  cmp -s "$status_before" "$status_after"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  test "$(awk -F= '$1 == "worktree-equals-index" {print $2}' \
    "$identity_path")" = 1
  test "$(git -C "$repo_root" rev-parse HEAD)" = \
    "$(awk -F= '$1 == "tip" {print $2}' "$identity_path")"
  test "$(git -C "$repo_root" write-tree)" = \
    "$(awk -F= '$1 == "index-tree" {print $2}' "$identity_path")"
  printf '%s\n' "$expected_line"
)

task5_check_ignored_anchor() (
  set -euo pipefail
  test "$#" = 5
  repo_root="$1"
  relative_path="$2"
  expected_sha="$3"
  expected_lines="$4"
  expected_bytes="$5"
  absolute_path="$repo_root/$relative_path"
  lexical_parent="$repo_root/${relative_path%/*}"
  test -f "$absolute_path"
  test ! -L "$absolute_path"
  test "$(cd "${absolute_path%/*}" && pwd -P)" = "$lexical_parent"
  git -C "$repo_root" check-ignore -q -- "$relative_path"
  test "$(task5_sha256 "$absolute_path")" = "$expected_sha"
  test "$(wc -l < "$absolute_path" | tr -d '[:space:]')" = "$expected_lines"
  test "$(wc -c < "$absolute_path" | tr -d '[:space:]')" = "$expected_bytes"
)

task5_verify_task42_namespace() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 8
  repo_root="$1"
  evidence_root="$2"
  snapshot_dir="$3"
  round="$4"
  expected_pattern_count="$5"
  expected_total_count="$6"
  expected_digest="$7"
  frozen_root="$8"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  test -d "$snapshot_dir"
  test ! -L "$snapshot_dir"
  task5_require_physical_descendant "$TASK5_ACTION_DIR" "$snapshot_dir" 700
  task5_require_sha256 "$expected_digest"
  raw_manifest="$snapshot_dir/task42-$round.manifest.raw"
  manifest="$snapshot_dir/task42-$round.manifest"
  task5_require_absent_path "$raw_manifest"
  task5_require_absent_path "$manifest"
  : > "$raw_manifest"
  pattern_count=0
  for selected in "$frozen_root"/task-4.2-correction-"$round"-*; do
    test -e "$selected"
    test -f "$selected"
    test ! -L "$selected"
    test "$(cd "${selected%/*}" && pwd -P)" = "$frozen_root"
    basename="${selected##*/}"
    relative_path=".superpowers/sdd/2026-07-31-oracle-passive-plugin/$basename"
    git -C "$repo_root" check-ignore -q -- "$relative_path"
    printf '%s  %s\n' "$(task5_sha256 "$selected")" "$basename" >> "$raw_manifest"
    pattern_count=$((pattern_count + 1))
  done
  test "$pattern_count" = "$expected_pattern_count"
  selected="$frozen_root/task-4.2-review-correction-$round-brief.md"
  test -f "$selected"
  test ! -L "$selected"
  test "$(cd "${selected%/*}" && pwd -P)" = "$frozen_root"
  basename="${selected##*/}"
  relative_path=".superpowers/sdd/2026-07-31-oracle-passive-plugin/$basename"
  git -C "$repo_root" check-ignore -q -- "$relative_path"
  printf '%s  %s\n' "$(task5_sha256 "$selected")" "$basename" >> "$raw_manifest"
  sort "$raw_manifest" > "$manifest"
  test "$(wc -l < "$manifest" | tr -d '[:space:]')" = "$expected_total_count"
  test "$(task5_sha256 "$manifest")" = "$expected_digest"
  printf '%s count=%s digest=%s\n' "$round" "$expected_total_count" "$expected_digest"
)

task5_verify_task42_ignored_closure() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  phase="$3"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  case "$phase" in
    initial|final) ;;
    *) task5_fail "Task 4.2 closure phase must be initial or final" ;;
  esac
  if test "$phase" = final; then
    task5_require_sealed_review_pair C53C2
  fi
  snapshot_dir="$(task5_init_artifact_dir \
    "$evidence_root" "task42-$phase")"
  initial_pointer="$TASK5_STATE_ROOT/task42-initial.path"
  if test "$phase" = initial; then
    task5_require_absent_path "$initial_pointer"
    printf '%s\n' "$snapshot_dir" > "$initial_pointer"
    chmod 600 "$initial_pointer"
    task5_require_owned_regular "$initial_pointer" 600
  else
    task5_require_owned_regular "$initial_pointer" 600
  fi
  frozen_relative='.superpowers/sdd/2026-07-31-oracle-passive-plugin'
  frozen_root="$repo_root/$frozen_relative"
  test -d "$frozen_root"
  test ! -L "$frozen_root"
  test "$(cd "$frozen_root/.." && pwd -P)" = \
    "$repo_root/.superpowers/sdd"

  task5_check_ignored_anchor "$repo_root" '.superpowers/sdd/.gitignore' \
    cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b 1 2
  task5_check_ignored_anchor "$repo_root" "$frozen_relative/task-4.2-brief.md" \
    e32a768a46da5d90077481a520c36e7943339c864db8a4f719b008e7318ae6dd 4983 179731
  task5_check_ignored_anchor "$repo_root" "$frozen_relative/task-4.2-review-correction-r04-brief.md" \
    376e3900e6ee50278bc4c3743b67581a948eefb5fdcb29020057bc40e7f6b589 202 10876
  task5_check_ignored_anchor "$repo_root" "$frozen_relative/task-4.2-forced-suite.sh" \
    627b108d9c95600f966b00a2517788774cda1eb8bf54b2f4bf4ef56cc9572224 74 2858
  task5_check_ignored_anchor "$repo_root" "$frozen_relative/task-4.2-report.md" \
    cb9df2a70fac25b9b370f7eb6450e370938fb8f8baaac6bae366d4a68c6e9581 452 164470
  task5_check_ignored_anchor "$repo_root" "$frozen_relative/progress.md" \
    248fa456d57555a7af6c81872190780e471f9177224f04ef5619923c04171cc8 699 202952

  anchors_manifest="$snapshot_dir/anchors.manifest"
  task5_require_absent_path "$anchors_manifest"
  for relative_path in \
      .superpowers/sdd/.gitignore \
      "$frozen_relative/task-4.2-brief.md" \
      "$frozen_relative/task-4.2-review-correction-r04-brief.md" \
      "$frozen_relative/task-4.2-forced-suite.sh" \
      "$frozen_relative/task-4.2-report.md" \
      "$frozen_relative/progress.md"; do
    printf '%s  %s\n' \
      "$(task5_sha256 "$repo_root/$relative_path")" "$relative_path"
  done | sort > "$anchors_manifest"
  test "$(wc -l < "$anchors_manifest" | tr -d '[:space:]')" = 6

  task5_verify_task42_namespace "$repo_root" "$evidence_root" \
    "$snapshot_dir" r01 25 26 \
    2dae97f85eff03f60eecdf7e87f517119c91acf8a83c808d74cdf3e6b6f9e640 "$frozen_root"
  task5_verify_task42_namespace "$repo_root" "$evidence_root" \
    "$snapshot_dir" r02 81 82 \
    a085b38274c50e6d93efa7c17ca76cc9afcff88707276bf8ac7786642bb54a73 "$frozen_root"
  task5_verify_task42_namespace "$repo_root" "$evidence_root" \
    "$snapshot_dir" r03 131 132 \
    34f895728843b9541d3ceca818c95fcf1d353619f3e12d7658c20f576c90ea9b "$frozen_root"
  task5_verify_task42_namespace "$repo_root" "$evidence_root" \
    "$snapshot_dir" r04 133 134 \
    17e8f52e34e80e32859d8002ad76724866707cd7091aa2edd1cd5c5f2ffbd524 "$frozen_root"
  if test "$phase" = final; then
    initial_dir="$(cat "$initial_pointer")"
    test -d "$initial_dir"
    test ! -L "$initial_dir"
    for artifact in anchors.manifest \
        task42-r01.manifest task42-r02.manifest \
        task42-r03.manifest task42-r04.manifest; do
      cmp -s "$initial_dir/$artifact" "$snapshot_dir/$artifact"
    done
  fi
)

task5_export_offline_environment() {
  test "${TASK5_CLEAN_CONTROLLER-}" = 1
  test "${TASK5_EVIDENCE_ROOT-}" != ""
  task5_require_evidence_root "$TASK5_EVIDENCE_ROOT"
  test "${PATH-}" = \
    /usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Cellar/dotnet/10.0.300/bin
  test "${LC_ALL-}" = C
  test "${LANG-}" = C
  test "${GIT_CONFIG_NOSYSTEM-}" = 1
  test "${GIT_CONFIG_GLOBAL-}" = /dev/null
  test "${GIT_TERMINAL_PROMPT-}" = 0
  test "${UV_OFFLINE-}" = 1
  test "${PIP_NO_INDEX-}" = 1
  task5_require_sha256 "${TASK5_DRIVER_SHA-}"
  export PATH='/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/opt/homebrew/Cellar/dotnet/10.0.300/bin'
  export LC_ALL=C
  export GIT_CONFIG_NOSYSTEM=1
  export GIT_CONFIG_GLOBAL=/dev/null
  export DOTNET_CLI_UI_LANGUAGE=en
  export DOTNET_CLI_TELEMETRY_OPTOUT=1
  export DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE=true
  export DOTNET_SDK_VULNERABILITY_CHECK_DISABLE=true
  export DOTNET_NOLOGO=1
  export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
  export NUGET_XMLDOC_MODE=skip
  export PYTHONDONTWRITEBYTECODE=1
  export PIP_NO_INDEX=1
  export UV_OFFLINE=1
  export GIT_TERMINAL_PROMPT=0
}

task5_run_recorded_command() {
  test "$#" -ge 2
  command_prefix="$1"
  shift
  case "$command_prefix" in
    force-net10|force-net35|focused-csharp|full-csharp|full-python) ;;
    *) task5_fail "recorded command prefix is outside the matrix set" ;;
  esac
  command_path="$TASK5_ACTION_DIR/$command_prefix.command"
  stdout_path="$TASK5_ACTION_DIR/$command_prefix.stdout"
  stderr_path="$TASK5_ACTION_DIR/$command_prefix.stderr"
  status_path="$TASK5_ACTION_DIR/$command_prefix.status"
  for command_output in "$command_path" "$stdout_path" "$stderr_path" \
      "$status_path"; do
    task5_require_absent_path "$command_output"
  done
  task5_record_argv "$command_path" "$@"
  if "$@" > "$stdout_path" 2> "$stderr_path"; then
    command_status=0
  else
    command_status=$?
  fi
  printf '%s\n' "$command_status" > "$status_path"
  task5_require_owned_regular "$stdout_path"
  task5_require_owned_regular "$stderr_path"
  task5_require_owned_regular "$status_path"
  cat "$stdout_path"
  cat "$stderr_path" >&2
  return "$command_status"
}

task5_require_dotnet() (
  set -euo pipefail
  task5_export_offline_environment
  dotnet_bin=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
  test -x "$dotnet_bin"
  set +e
  version_output="$("$dotnet_bin" --version 2>&1)"
  version_status=$?
  set -e
  printf '%s\n' "$version_output"
  test "$version_status" = 0
  test "$(printf '%s\n' "$version_output" | wc -l | tr -d '[:space:]')" = 1
  test "$version_output" = 10.0.300
)

task5_require_clean_build_output() (
  set -euo pipefail
  test "$#" = 1
  build_output="$1"
  test "$(printf '%s\n' "$build_output" | awk '$0 == "Build succeeded." {n++} END {print n + 0}')" = 1
  test "$(printf '%s\n' "$build_output" | awk '/^[[:space:]]*0 Warning[(]s[)]$/ {n++} END {print n + 0}')" = 1
  test "$(printf '%s\n' "$build_output" | awk '/^[[:space:]]*0 Error[(]s[)]$/ {n++} END {print n + 0}')" = 1
  case "$build_output" in
    *': error '*|*': warning '*|*'error CS'*|*'warning CS'*|*'Build FAILED.'*|\
    *'error MSB'*|*'NETSDK'*|*'assets file'*|*'fixture'*|\
    *'permission denied'*|*'Permission denied'*|*'Operation not permitted'*|\
    *'UnauthorizedAccessException'*|*'timed out'*|*'timeout'*|*'NU1'*)
      task5_fail "build output is not a clean success" ;;
  esac
)

task5_require_matrix_state() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  state="$4"
  case "$checkpoint:$state" in
    P:clean|C51:green-staged|C52:green-staged|C53:green-staged|\
    C53C1:green-staged|C53C2:green-staged|C53C2:committed) ;;
    *) task5_fail "matrix checkpoint/state pair is not authorized" ;;
  esac
  if test "$checkpoint:$state" = C53C2:committed; then
    task5_require_sealed_review_pair C53C2
  fi
  state_path="$TASK5_STATE_ROOT/$checkpoint.$state"
  task5_require_owned_regular "$state_path" 400
  test "$(wc -l < "$state_path" | tr -d '[:space:]')" = 6
  test "$(grep -Fxc "checkpoint=$checkpoint" "$state_path")" = 1
  test "$(grep -Fxc "state=$state" "$state_path")" = 1
  current_head="$(git -C "$repo_root" rev-parse HEAD)"
  current_index="$(git -C "$repo_root" write-tree)"
  current_branch="$(git -C "$repo_root" symbolic-ref -q HEAD)"
  current_status_sha="$(git -C "$repo_root" \
    status --porcelain=v1 --untracked-files=all | \
    shasum -a 256 | awk '{print $1}')"
  test "$(awk -F= '$1 == "HEAD" {print $2}' "$state_path")" = \
    "$current_head"
  test "$(awk -F= '$1 == "index-tree" {print $2}' "$state_path")" = \
    "$current_index"
  test "$(awk -F= '$1 == "branch" {print $2}' "$state_path")" = \
    "$current_branch"
  test "$(awk -F= '$1 == "status-sha256" {print $2}' "$state_path")" = \
    "$current_status_sha"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  case "$state" in
    clean|committed)
      test "$current_head" = \
        "$(task5_resolve_alias "$evidence_root" "$checkpoint")"
      git -C "$repo_root" diff --cached --quiet
      test -z "$(git -C "$repo_root" \
        status --porcelain=v1 --untracked-files=all)" ;;
    green-staged)
      parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
      test "$current_head" = \
        "$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
      test -n "$(git -C "$repo_root" diff --cached --name-only)" ;;
  esac
)

task5_force_net10() (
  set -euo pipefail
  task5_export_offline_environment
  task5_require_dotnet
  test "$#" = 1
  repo_root="$(task5_physical_repo_root "$1")"
  dotnet_bin='/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet'
  unit_project="$repo_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  test -x "$dotnet_bin"
  test -f "$unit_project"
  if task5_run_recorded_command force-net10 "$dotnet_bin" build \
      "$unit_project" --configuration Release --no-restore --nologo \
      -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false; then
    build_status=0
  else
    build_status=$?
  fi
  build_output="$(cat "$TASK5_ACTION_DIR/force-net10.stdout"; \
    cat "$TASK5_ACTION_DIR/force-net10.stderr")"
  test "$build_status" = 0
  task5_require_clean_build_output "$build_output"
)

task5_force_net35() (
  set -euo pipefail
  task5_export_offline_environment
  task5_require_dotnet
  test "$#" = 1
  repo_root="$(task5_physical_repo_root "$1")"
  dotnet_bin='/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet'
  net35_project="$repo_root/oracle/plugin/tests/SsrOracle.Core.Net35.csproj"
  test -x "$dotnet_bin"
  test -f "$net35_project"
  if task5_run_recorded_command force-net35 "$dotnet_bin" build \
      "$net35_project" --configuration Release --no-restore --nologo \
      -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false; then
    build_status=0
  else
    build_status=$?
  fi
  build_output="$(cat "$TASK5_ACTION_DIR/force-net35.stdout"; \
    cat "$TASK5_ACTION_DIR/force-net35.stderr")"
  test "$build_status" = 0
  task5_require_clean_build_output "$build_output"
)

task5_run_focused_csharp() (
  set -euo pipefail
  task5_export_offline_environment
  task5_require_dotnet
  test "$#" = 2
  repo_root="$(task5_physical_repo_root "$1")"
  cohort="$2"
  case "$cohort" in
    driver-input|driver-terminal|driver-initial) ;;
    *) task5_fail "unsupported focused cohort" ;;
  esac
  dotnet_bin='/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet'
  unit_project="$repo_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  if task5_run_recorded_command focused-csharp "$dotnet_bin" run \
      --project "$unit_project" --configuration Release --no-restore \
      --no-build -- --cohort "$cohort"; then
    run_status=0
  else
    run_status=$?
  fi
  run_output="$(cat "$TASK5_ACTION_DIR/focused-csharp.stdout")"
  test "$run_status" = 0
  test ! -s "$TASK5_ACTION_DIR/focused-csharp.stderr"
  test "$run_output" = 'SSR oracle unit harness ready'
)

task5_run_full_csharp() (
  set -euo pipefail
  task5_export_offline_environment
  task5_require_dotnet
  test "$#" = 1
  repo_root="$(task5_physical_repo_root "$1")"
  dotnet_bin='/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet'
  unit_project="$repo_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  if task5_run_recorded_command full-csharp "$dotnet_bin" run \
      --project "$unit_project" --configuration Release --no-restore \
      --no-build; then
    run_status=0
  else
    run_status=$?
  fi
  run_output="$(cat "$TASK5_ACTION_DIR/full-csharp.stdout")"
  test "$run_status" = 0
  test ! -s "$TASK5_ACTION_DIR/full-csharp.stderr"
  test "$run_output" = 'SSR oracle unit harness ready'
)

task5_run_full_python() (
  set -euo pipefail
  task5_export_offline_environment
  test "$#" = 1
  repo_root="$(task5_physical_repo_root "$1")"
  test "$repo_root" = "${TASK5_EXECUTION_ROOT-}"
  task5_require_clean_controller "$repo_root" "$TASK5_EVIDENCE_ROOT"
  python_bin="$repo_root/.venv/bin/python"
  test -x "$python_bin"
  test "$(task5_sha256 "$repo_root/src/ssr_env/oracle_protocol.py")" = \
    9feab69eec050eea51670c9f80b00acba06799e500a4ed3502f02722d5ea7108
  test "$(task5_sha256 "$repo_root/tests/test_oracle_protocol.py")" = \
    a0689d3233f55e24a95de5f5f6212690b2b820f03aaf47db8a383dfff4e2ead4
  cd "$repo_root"
  if task5_run_recorded_command full-python /usr/bin/env \
      PYTHONDONTWRITEBYTECODE=1 "PYTHONPATH=$repo_root/src" UV_OFFLINE=1 \
      "$python_bin" -m pytest -q -rX; then
    python_status=0
  else
    python_status=$?
  fi
  python_output="$(cat "$TASK5_ACTION_DIR/full-python.stdout")"
  test "$python_status" = 0
  test ! -s "$TASK5_ACTION_DIR/full-python.stderr"
  case "$python_output" in
    *'1822 passed, 120 xfailed, 6 xpassed in '*) ;;
    *) task5_fail "unexpected full Python summary" ;;
  esac
  case "$python_output" in
    *' failed'*|*' error'*|*' skipped'*|*'permission denied'*|\
    *'Permission denied'*|*'Operation not permitted'*|\
    *'UnauthorizedAccessException'*|*'timed out'*|*'timeout'*)
      task5_fail "full Python suite contains a forbidden outcome" ;;
  esac
)

task5_stress_task5_cohorts() (
  set -euo pipefail
  task5_export_offline_environment
  export LC_ALL=C
  umask 077
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  phase="$4"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  case "$checkpoint:$phase" in
    C53C1:postcommit|C53C2:postcommit|C53C2:task4) ;;
    *) task5_fail "stress checkpoint/phase is outside the closed set" ;;
  esac
  if test "$phase" = task4; then
    task5_require_sealed_review_pair C53C2
  fi
  checkpoint_oid="$(task5_resolve_alias "$evidence_root" "$checkpoint")"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$checkpoint_oid"
  task5_require_committed_checkpoint "$repo_root" "$evidence_root" \
    "$checkpoint"
  test -z "$(git -C "$repo_root" status --porcelain=v1 \
    --untracked-files=all)"
  artifact_dir="$(task5_init_artifact_dir \
    "$evidence_root" "stress-$checkpoint-$phase")"
  dotnet_bin='/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet'
  unit_project="$repo_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  aggregate_manifest="$artifact_dir/aggregate.manifest"
  aggregate_sha_path="$artifact_dir/aggregate.sha256"
  task5_require_absent_path "$aggregate_manifest"
  test ! -L "$aggregate_manifest"
  task5_require_absent_path "$aggregate_sha_path"
  test ! -L "$aggregate_sha_path"
  : > "$aggregate_manifest"
  iterations=20
  iteration=1
  all_green=1
  while test "$iteration" -le "$iterations"; do
    ordinal="$(printf '%02d' "$iteration")"
    command_path="$artifact_dir/run-$ordinal.command"
    stdout_path="$artifact_dir/run-$ordinal.stdout"
    stderr_path="$artifact_dir/run-$ordinal.stderr"
    status_path="$artifact_dir/run-$ordinal.status"
    identity_path="$artifact_dir/run-$ordinal.identity"
    repo_status_before="$artifact_dir/run-$ordinal.repo-status-before"
    repo_status_after="$artifact_dir/run-$ordinal.repo-status-after"
    for artifact in "$command_path" "$stdout_path" "$stderr_path" \
        "$status_path" "$identity_path" "$repo_status_before" \
        "$repo_status_after"; do
      task5_require_absent_path "$artifact"
    done
    tip="$(git -C "$repo_root" rev-parse HEAD)"
    tree="$(git -C "$repo_root" write-tree)"
    git -C "$repo_root" status --porcelain=v1 --untracked-files=all \
      > "$repo_status_before"
    test ! -s "$repo_status_before"
    printf 'tip-before=%s\nindex-tree-before=%s\n' "$tip" "$tree" \
      > "$identity_path"
    printf '%s\n' \
      "$dotnet_bin run --project $unit_project --configuration Release --no-restore --no-build -- --cohort driver-terminal" \
      > "$command_path"
    task5_require_dotnet >/dev/null
    set +e
    "$dotnet_bin" run --project "$unit_project" \
      --configuration Release --no-restore --no-build -- \
      --cohort driver-terminal > "$stdout_path" 2> "$stderr_path"
    run_status=$?
    set -e
    printf '%s\n' "$run_status" > "$status_path"
    stdout_sha="$(task5_sha256 "$stdout_path")"
    stderr_sha="$(task5_sha256 "$stderr_path")"
    git -C "$repo_root" status --porcelain=v1 --untracked-files=all \
      > "$repo_status_after"
    test ! -s "$repo_status_after"
    cmp -s "$repo_status_before" "$repo_status_after"
    repo_status_sha="$(task5_sha256 "$repo_status_before")"
    printf 'tip-after=%s\nindex-tree-after=%s\n' \
      "$(git -C "$repo_root" rev-parse HEAD)" \
      "$(git -C "$repo_root" write-tree)" >> "$identity_path"
    printf '%s|status=%s|stdout-sha256=%s|stderr-sha256=%s|tip=%s|tree=%s|repo-status-sha256=%s\n' \
      "$ordinal" "$run_status" "$stdout_sha" "$stderr_sha" \
      "$tip" "$tree" "$repo_status_sha" >> "$aggregate_manifest"
    if test "$run_status" != 0 || \
        test "$(cat "$stdout_path")" != 'SSR oracle unit harness ready' || \
        test -s "$stderr_path"; then
      all_green=0
    fi
    test "$(git -C "$repo_root" rev-parse HEAD)" = "$tip"
    test "$(git -C "$repo_root" write-tree)" = "$tree"
    iteration=$((iteration + 1))
  done
  test "$(wc -l < "$aggregate_manifest" | tr -d '[:space:]')" = 20
  aggregate_sha="$(task5_sha256 "$aggregate_manifest")"
  printf '%s  aggregate.manifest\n' "$aggregate_sha" > "$aggregate_sha_path"
  test "$all_green" = 1
  printf 'Task 5 terminal stress passed: iterations=%s cohort-runs=%s\n' \
    "$iterations" "$iterations"
)

task5_obj_manifest() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 2
  repo_root="$1"
  output_path="$2"
  task5_require_absent_path "$output_path"
  for relative_dir in oracle/plugin/obj oracle/plugin/tests/obj; do
    test -d "$repo_root/$relative_dir"
    test ! -L "$repo_root/$relative_dir"
    test -z "$(find "$repo_root/$relative_dir" -type l -print)"
    test -z "$(find "$repo_root/$relative_dir" ! -type d ! -type f -print)"
  done
  (
    cd "$repo_root"
    find oracle/plugin/obj oracle/plugin/tests/obj -type f -print | sort | while IFS= read -r relative_path; do
      git check-ignore -q -- "$relative_path"
      printf '%s  %s\n' "$(task5_sha256 "$relative_path")" "$relative_path"
    done
  ) > "$output_path"
  test "$(wc -l < "$output_path" | tr -d '[:space:]')" -gt 0
)

task5_canonical_mutation_manifest() {
  cat <<'TASK5_CANONICAL_MUTATIONS'
# TASK5-CANONICAL-MUTATION-MANIFEST-BEGIN
T5M01|d1933eadca9505e3d105db334b613be4e89196263498e8b96be05f89439acbbf|13|633|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|d60603b1155a876f3d9a6563e3b2b45507e7970bbd4347ec11701b6b6cfe0b59|f0fd7de8497651011c25cee8b290adbc14119193|07e64d70a4eaa7598c6867d0369297a8d28e16e3|driver-input|cohort 'driver-input', test 'all cardinals correlate': System.InvalidOperationException: cardinal opens attempt 0
T5M02|b7f2c2ca8cff261303f8d8805336d4536a0c5bc5cec6338128386c4d82feec2a|12|576|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|ebc3af64300acbcf0d80a62c4b4fc435fbea232fc95ce8629c002ca8a0cfc955|3e03edfc9b189c5a52f4fc6df9352dd5c79eb646|31095186dbca4342471acd1f9f2582deacd7cf4c|driver-input|cohort 'driver-input', test 'accepted and refused direction outcomes': System.InvalidOperationException: cardinal poll clears candidate
T5M03|b426eb4706f9c4613f470c318d01e6ace393b4e77a16467a4de85f64013d956c|13|580|oracle/plugin/Core/PassiveDriverLifecycleHooks.cs|c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002|d4f1b49e8680676cd6b632390aa337dd58799d70|45c4cad51bf9e59b348c89ecfedf7bdc755ae7006a34d89226de334263c2573c|dbf219c18858e4bbeb779bd4490994067f0da35a|0f3b231e673dd9f6f23045e5052a0a6c0ef9f681|driver-input|cohort 'driver-input', test 'state replacement and ClearThrew': System.InvalidOperationException: hook identity preserves AwaitInitial frame count
T5M04|048481433a1cfa640f44b73d829e98fcff1f3203255f472d8cca791eb5116e88|35|1309|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|3c678f1838795178110ddc5a404ebae17cac7ca69fcc9aeec47ba92fa4c2b949|8ee91c0db2fcef803f5a9d996e57274d2b9b0f72|31693c7b3bd2e16ff929b3fe376c7e9ffd9577c0|driver-input|cohort 'driver-input', test 'accepted and refused direction outcomes': System.InvalidOperationException: durable Step precedes progress marker at index 0
T5M05|a936e9ab5183511dc144c127a7ab5bbbdd77f0a9dee3ccbce5cfdaa1f403defe|19|703|oracle/plugin/Core/PassiveDriverLifecycleHooks.cs|c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002|d4f1b49e8680676cd6b632390aa337dd58799d70|6236fb28b0b7b700dd81de0482b89648d47b3014299167d30034c89bfda4b154|d20928e7addd3232a3b3f592e7d2898c0f6d43af|be51e9487a94a8a73b1fbc99d324a28d227a1d0e|driver-input|cohort 'driver-input', test 'restart depth and null fields': System.InvalidOperationException: reentrant Restart remains active after fault selection
T5M06|cc764023239a341d5f1a830e74e2a281b0ee1a81ada1515d265fa8b4780cce57|13|584|oracle/plugin/Core/PassiveDriverLifecycleHooks.cs|c64c8e5a2fc6a9a6e251245bdb7fb713f81eb479cb3b0b14b8f4eb5b12ebc002|d4f1b49e8680676cd6b632390aa337dd58799d70|e3d6348f60b0e2b421ad54cae8f79e4b5dce268122356a8f10295c31d92f2225|811a5fb252b3cecd96d2980d521d8721a8a753b9|1203a31914327f89e93f38dae930a2cea9ebb970|driver-input|cohort 'driver-input', test 'state replacement and ClearThrew': System.InvalidOperationException: requested state is observational only
T5M07|acd27cc07fe21b72108b26163d345bebc844c01c96b4464bffd5f1704b63a95e|16|736|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|3b80cedb47d8ecd0933342dd09ac1fe80aa0f6b7ac4039f17316ae2783171dbc|f8649619a600ac26d1c4602ac7c105c6595b3f1e|fcc4ed7ede55c5850cac41ee3ed7eca64f708363|driver-input|cohort 'driver-input', test 'state replacement and ClearThrew': System.InvalidOperationException: disabled ProcessInput return consumes token once
T5M08|3e334b7f4fe7ba1215bd89cac2de14085870a4487c80d4d33b9bd23336b56cd7|13|667|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|6af76f1f9492c24e7c8499058b89f56d3e3bb4fdf828c53d847dc768be74fbd0|22c1535701d1388188e7a5e7d779f26c612dbe98|9d3737ee6579614c0c6165ae7241b0fea923440c|driver-terminal|cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: durable Step 2 must enter Done without Ready(3) and emit End Close Complete
T5M09|068c96f07aac340876a269a8b9dd918dd0a31f54bde084516925da580693327c|27|1149|oracle/plugin/Core/PassiveDriverCompletion.cs|27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4|638d2882e988b17d686a7791604a497438e7d4e3|8b3aa73f949879014aa070a83a7d45e3fae220f5e02737d551ef77e7d86ee8fe|0f08b69e7046209bf671d0744ef9a90039943a33|dfff42dc5930398730d63fd24a7d79df2d6fa723|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: success terminal owner rejects concurrent fault
T5M10|87a1e87bb1581f621c2ed48e802bb1e45ee855da3dee5371047f1138a35434a4|15|644|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|6753e731a1b8f22c049b00f23cb768749298e13a3fa8a9cb43526311c3a7d6b8|077c6da6a86fe0c11c483ebb7f1205f92b6d6940|d33672ff48210e9a47d044d9b95b66e9bd43deee|driver-terminal|cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: Step 2 failure never attempts Error
T5M11|fdc867802747ac1153cbd3e94363b560d0218c9223e51c5f7716d8aa0bbdfec8|12|551|oracle/plugin/Core/PassiveDriverCompletion.cs|27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4|638d2882e988b17d686a7791604a497438e7d4e3|88075f592f0828f09c1068b07f163d68182c4b6d85204253281238fb4b5581d2|c2db4f7f4dbeb5845511b604b4d92012ae96ce77|6c7744951d076122a2e421925cf3c908030e1fad|driver-terminal|cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: End failure is marker-only phase
T5M12|0b8c8184b2f15ed3a0c8984009dcfdb857458924a7fb82a99ebb0e612a34bc90|19|740|oracle/plugin/Core/PassiveDriverCompletion.cs|27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4|638d2882e988b17d686a7791604a497438e7d4e3|23e13d0131607c2e387e830d731f374cb319ccf85d6ef18cb404d87bf49573e4|e2c978c1c394c6bfdcf55f17585966542674d275|cf2cf8a6e0d9c74255f66d6bf6ca963f4aaa333b|driver-terminal|cohort 'driver-terminal', test 'completion reporter cannot rewrite trace': System.InvalidOperationException: Complete exception changes only in-memory phase
T5M13|c2b718251cd91a10366dbd99c9a0cab10759db6c8ccb976a71326f31eb66bc7f|20|924|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|61839f2d1285a8a5e2ab0beac7ba63b60b55a1a0a2979d040e31b786971924f1|16390c2b8aaa9324bdbb75f89768f42768da75e9|2c9f42a62add99844c1c7cc2aa502b5d819ed56e|driver-initial|cohort 'driver-initial', test 'replacement rebases same callback': System.InvalidOperationException: replacement requires two fresh candidate captures
T5M14|b78d661029de14189be8864c12f9133d0924b347d49b4f0d6aef444fe512ccb5|14|654|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|59eebe420c07a851b702a07b5b2e23cfd33d3f2aed93f1b6e04f766b8ddbc6ff|24382e03d3c352a26e65408cf5b6f04ed38f3f54|228738c999afa6bb054c8225f4ee0d6943969e7a|driver-initial|cohort 'driver-initial', test 'matching pair writes initial': System.InvalidOperationException: same raw save with unequal complete signature does not settle
T5M15|a7d7f2af440075e395346748d2ca9771c18dec8b052b9211131ff34964fa53bb|93|2879|oracle/plugin/Core/PassiveDriverBoundaries.cs|1a130383302b315f43f8643fab5c13ec8d643727c2095ca21929aac306cdf133|b575724daf03cdf7d9a96722945a55ccd46a6e87|04b166764a03582ea8abaa83564e4402223d823000a36a7ae8aebcb4a13d9435|d2d8de03129cc90caa08d46b9ae8aebe3aa5f6c9|fd750eb82dd3dd890e4caedadf130cf1cebd3983|driver-initial|cohort 'driver-initial', test 'matching pair writes initial': System.InvalidOperationException: authorization precedes gate inspection
T5M16|75c7af5e49cf50eef84382640ea9ab62c270948a6769a43538fd6c80ed3604bd|13|574|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|24a17a796b98bcacebd861ec460db6e9ef20d89b0f5bef25f224c917aa5e7471|8a0e556289e51803e368df04d34866437e7836a3|c4a7e48a1a1fc218e2b07a68079ed387f783c19c|driver-terminal|cohort 'driver-terminal', test 'error field policy is exact': System.InvalidOperationException: Restart overrides pending input fields input index
T5M17|be1da505f26c232382f0ec3ea686896cd7c3d17e9459dd6d53c4d241cfdbfed8|13|654|oracle/plugin/Core/PassiveDriverCompletion.cs|27ba46134ddd929ca68e2d53f903deea665a9ce57ec91e09f6bdc52c62351ae4|638d2882e988b17d686a7791604a497438e7d4e3|bf923b575cfac81d078c879bf929ab9066d2a73789bcf7c97147db144c5103dc|a75307c935e4cb91ccf4d2a4ecfb356a20d119ba|377e166509a12db266fd7ec0e62bc6a8d958bbe4|driver-terminal|cohort 'driver-terminal', test 'three steps End Close Complete order': System.InvalidOperationException: UTC equal to started_at_utc is accepted
T5M18|e3caa55377b3a6200973310f336c42bb786779e25db57b3a461c262fdc8f6434|62|1962|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|fee41934f82b2e79e2fa5a538edec2a7573a5c435c396055c8f77b7d88e695d4|1c4b058e273e0d301b4eab83bf966952d486f5f3|733fc8babfb3ea8531b95a75508f06655778f444|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: fault Close waits for active Run output
T5M19|a6f01ada63cba3c9aaf40a0d17afb3bbe0321b6617bfb13ce1dd704f3fcf994b|91|2854|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|a7e7236bc3a7cb5eb0098da59caea33387db98e9f29df30e71eafe3e81bf7d68|048177cb176b26cbc40726c9fc230acd703eaa69|df3d8b853557213996b4812fe9b9c7659928d84f|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: Initial Error waits for active output
T5M20|8e5617ac4385209efd55aa82342b597a52f1aa9485150701dd2862accf9a0335|56|1664|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|b5b717979aa7cb69d3db47b3a1ef1a86082fa9005489fb33a67ea26af7462acf|72b107730e71323398dece74736fc649568d5d08|d413c11760f2ac1b1499208031757c7c933ed357|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: Error waits for Ready(0) callback
T5M21|7bd93518c41f62bfb72cc254f7817e1c372801a14030a6833806c8bac1e0a61d|111|3553|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|102d882993f8fb6d28ee330a051afad7e537b7c81820455c63cde8039a30abc4|3de91bff0cdc945a52ea17db94c41e6320280322|d3566afdf180e0d0c99b9d695b178ad88d8d6441|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: fault terminal trace waits for active Step output
T5M22|76bea7cc72c86a978a9329046a1b266eca62a27972e3f43aefc8974609b9f069|14|646|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|2f8837686521350e94de0b74fad1f6a64c30eaff5bee88b832a1fe307b65cfe6|9d3bf10ac32c364c6c6aec7f22f3f2bad1b9889b|79eb88d8a946750228a8b0935a502cda62dc92ba|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: intermediate fault suppresses Ready(1)
T5M23|9ce1757858a93e6581ad88f237445499976da102184f47e7e8432d3852dbc665|18|826|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|d9d3f1225e255a1f3ebc0b22be00f488d20f7b2c378f0129ce79cdc417d5f75c|ca3a175dc35d112158f7916fe94020e6469cd781|6e7433b3dc3504095445290dd02cdcb8cf1854d5|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: real trace closes once after deferred fault
T5M24|c5bb317a2a4db15a02114a71554b2d994e9013489c044b4437c9a0df7b79100e|18|874|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|a9384bb75f6eb288da48b5cb3c32905efd9257c7f9bcff6ae9c17977d80010a7|7856883075bc08072784df9bcada1baeffbd6ba3|7efaf1fbefa97c06bc8a639b54710d8efd72b6a1|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: compromised Step suppresses queued Error attempt
T5M25|b7cceee7030a41131b9dfdcd1354c777d7f411457d069d28c0e60b36b42a1577|30|1248|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|f4c34a2ab5e42835d9f329c14bf29e42de9a4706d46223cf3d6d1801b7d31c55|2d38882f466e6f1fd0b5b57b6928659ac23e1bec|79e53b868a058bc8baa7bbdeb8e9ca2acba97274|driver-terminal|cohort 'driver-terminal', test 'Dispose and late callbacks are final': System.InvalidOperationException: Dispose Close waits for in-flight Step
T5M26|3ace6fa03b74e065b5d2106b04a391c0834747f0fda6c9ee38f531f5e085918f|17|751|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|41c0b0a6bf29cc3b6c9c24c3d7d19aebcb3f04f4900b713e46944d30b4d7467e|73db8395f91cfcbcc168404f5fec5ba15866d4da|a722ea76d89dffa6e856e86c0a8da51a6552363d|driver-terminal|cohort 'driver-terminal', test 'Dispose and late callbacks are final': System.InvalidOperationException: disposed Step emits no Ready continuation
T5M27|f25e9c2eab1030b3fdfeb7299787b2a53d47b1d2042362dce53251679933e4ca|28|1130|oracle/plugin/Core/PassiveDriver.cs|093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130|b132f89b321345452901faab870ea0d642b93e06|443832f608b86bc0d7522092e7710ffc0cd6ef76405f2ce41d0badc855d7e114|ba6378b817588ea19549d96ec143e8c0f1e5fd14|85642fb6f56ebf394004e248074c4d1110bb1483|driver-terminal|cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: Error write failure closes before trace I/O marker at index 1
T5M28|6787476f2830289a1e2660fd7e2bb299cabbd14ccd4bd9650df2cad0df0bd5a3|23|1011|oracle/plugin/Core/PassiveDriverInput.cs|4aa3a4c3548b3a28bd3d2d56198236e1129d887e2279c64619fc0f59aa976128|4bd5d0ba1200e3971416e361407fa5eac2efd0b4|283190a8d3097daa30b247881c01df96ef94400276897c76f872ed0adfdf616c|88951007d1f25df778c025009c0b1d23cd6645ef|449fab97552259bcae3adfeb68e87224f9a7734a|driver-terminal|cohort 'driver-terminal', test 'first fault wins race': System.InvalidOperationException: real Step remains durable before deferred Error second line
# TASK5-CANONICAL-MUTATION-MANIFEST-END
TASK5_CANONICAL_MUTATIONS
}

task5_canonical_mutation_ids() {
  task5_canonical_mutation_manifest | \
    awk -F '|' '$1 ~ /^T5M[0-9][0-9]$/ {print $1}'
}

task5_load_canonical_mutation() {
  test "$#" = 1
  mutation_id="$1"
  mutation_row="$(task5_canonical_mutation_manifest | \
    awk -F '|' -v wanted="$mutation_id" '$1 == wanted {n++; row=$0} END {if (n != 1) exit 1; print row}')"
  test -n "$mutation_row"
  IFS='|' read -r mutation_loaded_id mutation_patch_sha \
    mutation_patch_lines mutation_patch_bytes mutation_target \
    mutation_parent_sha mutation_parent_blob mutation_result_sha \
    mutation_result_blob mutation_plugin mutation_cohort mutation_failure \
    <<TASK5_MUTATION_ROW
$mutation_row
TASK5_MUTATION_ROW
  test "$mutation_loaded_id" = "$mutation_id"
  task5_require_sha256 "$mutation_patch_sha"
  task5_require_sha256 "$mutation_parent_sha"
  task5_require_sha256 "$mutation_result_sha"
  case "$mutation_patch_lines:$mutation_patch_bytes" in
    *[!0123456789:]*) task5_fail "mutation lines/bytes are not decimal" ;;
  esac
  test "$mutation_patch_lines" -gt 0
  test "$mutation_patch_bytes" -gt 0
  test "${#mutation_parent_blob}" = 40
  test "${#mutation_result_blob}" = 40
  test "${#mutation_plugin}" = 40
  case "$mutation_parent_blob$mutation_result_blob$mutation_plugin" in
    *[!0123456789abcdef]*) task5_fail "mutation Git identity is invalid" ;;
  esac
  case "$mutation_target" in
    oracle/plugin/Core/*.cs) ;;
    *) task5_fail "mutation target is outside production Core" ;;
  esac
  case "$mutation_cohort" in
    driver-input|driver-initial|driver-terminal) ;;
    *) task5_fail "mutation cohort is invalid" ;;
  esac
  test -n "$mutation_failure"
}

task5_record_argv() {
  test "$#" -ge 2
  output_path="$1"
  shift
  task5_require_absent_path "$output_path"
  printf '%q ' "$@" > "$output_path"
  printf '\n' >> "$output_path"
  task5_require_owned_regular "$output_path"
}

task5_raw_force_net10() {
  test "$#" = 3
  raw_repo="$1"
  raw_dir="$2"
  raw_label="$3"
  raw_dotnet=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
  raw_project="$raw_repo/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  raw_command="$raw_dir/$raw_label.command"
  raw_stdout="$raw_dir/$raw_label.stdout"
  raw_stderr="$raw_dir/$raw_label.stderr"
  raw_status="$raw_dir/$raw_label.status"
  for raw_output in "$raw_stdout" "$raw_stderr" "$raw_status"; do
    task5_require_absent_path "$raw_output"
  done
  task5_record_argv "$raw_command" "$raw_dotnet" build "$raw_project" \
    --configuration Release --no-restore --nologo -warnaserror -t:Rebuild \
    -m:1 -p:UseSharedCompilation=false
  task5_require_dotnet >/dev/null
  set +e
  "$raw_dotnet" build "$raw_project" --configuration Release --no-restore \
    --nologo -warnaserror -t:Rebuild -m:1 -p:UseSharedCompilation=false \
    > "$raw_stdout" 2> "$raw_stderr"
  raw_exit=$?
  set -e
  printf '%s\n' "$raw_exit" > "$raw_status"
}

task5_raw_focused_csharp() {
  test "$#" = 4
  raw_repo="$1"
  raw_cohort="$2"
  raw_dir="$3"
  raw_label="$4"
  case "$raw_cohort" in
    driver-initial|driver-input|driver-terminal) ;;
    *) task5_fail "raw cohort is outside the closed set" ;;
  esac
  raw_dotnet=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
  raw_project="$raw_repo/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  raw_command="$raw_dir/$raw_label.command"
  raw_stdout="$raw_dir/$raw_label.stdout"
  raw_stderr="$raw_dir/$raw_label.stderr"
  raw_status="$raw_dir/$raw_label.status"
  for raw_output in "$raw_stdout" "$raw_stderr" "$raw_status"; do
    task5_require_absent_path "$raw_output"
  done
  task5_record_argv "$raw_command" "$raw_dotnet" run --project "$raw_project" \
    --configuration Release --no-restore --no-build -- --cohort "$raw_cohort"
  task5_require_dotnet >/dev/null
  set +e
  "$raw_dotnet" run --project "$raw_project" --configuration Release \
    --no-restore --no-build -- --cohort "$raw_cohort" \
    > "$raw_stdout" 2> "$raw_stderr"
  raw_exit=$?
  set -e
  printf '%s\n' "$raw_exit" > "$raw_status"
}

task5_require_raw_build_green() (
  set -euo pipefail
  test "$#" = 2
  raw_dir="$1"
  raw_label="$2"
  test "$(cat "$raw_dir/$raw_label.status")" = 0
  build_output="$(cat "$raw_dir/$raw_label.stdout"; \
    cat "$raw_dir/$raw_label.stderr")"
  task5_require_clean_build_output "$build_output"
)

task5_require_raw_focused_green() (
  set -euo pipefail
  test "$#" = 2
  raw_dir="$1"
  raw_label="$2"
  raw_stdout="$raw_dir/$raw_label.stdout"
  raw_stderr="$raw_dir/$raw_label.stderr"
  test "$(cat "$raw_dir/$raw_label.status")" = 0
  test ! -s "$raw_stderr"
  test "$(cat "$raw_stdout")" = 'SSR oracle unit harness ready'
  test "$(wc -l < "$raw_stdout" | tr -d '[:space:]')" = 1
  test "$(wc -c < "$raw_stdout" | tr -d '[:space:]')" = 30
  test "$(task5_sha256 "$raw_stdout")" = \
    541d051ca0d24f44e9163a6ccb40346b96e115b1373b669c6f036179677b1adc
)

task5_extract_catalog_artifact() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 3
  artifact_kind="$1"
  artifact_id="$2"
  output_dir="$3"
  task5_require_physical_descendant "$TASK5_ACTION_DIR" "$output_dir" 700
  case "$artifact_kind:$artifact_id" in
    canonical:T5M??)
      task5_load_canonical_mutation "$artifact_id"
      begin_marker="<!-- BEGIN $artifact_id CANONICAL PATCH -->"
      end_marker="<!-- END $artifact_id CANONICAL PATCH -->"
      opening_fence='~~~diff'
      expected_sha="$mutation_patch_sha"
      expected_lines="$mutation_patch_lines"
      expected_bytes="$mutation_patch_bytes"
      artifact_name="$artifact_id.patch" ;;
    rejected:T5M20)
      begin_marker='<!-- BEGIN REJECTED-T5M20-SCOPE PATCH -->'
      end_marker='<!-- END REJECTED-T5M20-SCOPE PATCH -->'
      opening_fence='~~~diff'
      expected_sha=bd025237bc8baf67b95066f6e074c14dd3d1a4193ca2aa5794361848d0ec56d4
      expected_lines=40
      expected_bytes=1214
      artifact_name=REJECTED-T5M20-SCOPE.patch ;;
    rejected:T5M23)
      begin_marker='<!-- BEGIN REJECTED-T5M23-BROAD PATCH -->'
      end_marker='<!-- END REJECTED-T5M23-BROAD PATCH -->'
      opening_fence='~~~diff'
      expected_sha=3ebacfe9b8f471e4e67770302a7e4728bb22d9ab2a9bced33a171b82f1299f4f
      expected_lines=14
      expected_bytes=584
      artifact_name=REJECTED-T5M23-BROAD.patch ;;
    proof:hook)
      begin_marker='<!-- BEGIN T5M28 TEMPORARY EXPORT HOOK -->'
      end_marker='<!-- END T5M28 TEMPORARY EXPORT HOOK -->'
      opening_fence='~~~diff'
      expected_sha=04e413ee1c486d60bdbfefe9033dd1232a19b4f2d46011f5a02d11d13dd6f8f7
      expected_lines=26
      expected_bytes=1246
      artifact_name=T5M28-temporary-export-hook.patch ;;
    proof:probe)
      begin_marker='<!-- BEGIN T5M28 QUALIFIED STALE PROBE -->'
      end_marker='<!-- END T5M28 QUALIFIED STALE PROBE -->'
      opening_fence='~~~python'
      expected_sha=0efd1cdcb2fef895c29d566512af85d86d31aa4cf247e338af912d6de24b04c8
      expected_lines=33
      expected_bytes=1142
      artifact_name=T5M28-qualified-stale-probe.py ;;
    *) task5_fail "artifact request is outside the closed catalog" ;;
  esac
  plan_copy="$output_dir/$artifact_name.plan.md"
  artifact_path="$output_dir/$artifact_name"
  task5_require_absent_path "$plan_copy"
  task5_require_absent_path "$artifact_path"
  git -C "$TASK5_EXECUTION_ROOT" show \
    "$TASK5_PLAN_COMMIT:$TASK5_PLAN_PATH" > "$plan_copy"
  test "$(awk -v wanted="$begin_marker" \
    '$0 == wanted {n++} END {print n + 0}' "$plan_copy")" = 1
  test "$(awk -v wanted="$end_marker" \
    '$0 == wanted {n++} END {print n + 0}' "$plan_copy")" = 1
  begin_line="$(awk -v wanted="$begin_marker" \
    '$0 == wanted {print NR}' "$plan_copy")"
  end_line="$(awk -v wanted="$end_marker" \
    '$0 == wanted {print NR}' "$plan_copy")"
  test "$begin_line" -lt "$end_line"
  test "$(sed -n "$((begin_line + 1))p" "$plan_copy")" = "$opening_fence"
  test "$(sed -n "$((end_line - 1))p" "$plan_copy")" = '~~~'
  test "$(awk -v first="$begin_line" -v last="$end_line" \
    'NR > first && NR < last && substr($0,1,3) == "~~~" {n++} \
     END {print n + 0}' "$plan_copy")" = 2
  awk -v first="$((begin_line + 1))" -v last="$((end_line - 1))" \
    'NR > first && NR < last {print}' "$plan_copy" > "$artifact_path"
  task5_require_owned_regular "$artifact_path"
  test "$(tail -c 1 "$artifact_path" | od -An -tu1 | tr -d '[:space:]')" = 10
  test "$(task5_sha256 "$artifact_path")" = "$expected_sha"
  test "$(wc -l < "$artifact_path" | tr -d '[:space:]')" = "$expected_lines"
  test "$(wc -c < "$artifact_path" | tr -d '[:space:]')" = "$expected_bytes"
  printf '%s\n' "$artifact_path"
)

task5_run_clone_setup_step() (
  set -euo pipefail
  umask 077
  test "$#" -ge 3
  clone_name="$1"
  step_name="$2"
  shift 2
  case "$clone_name:$step_name" in
    *..*|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._:-]*)
      task5_fail "unsafe clone setup label" ;;
  esac
  prefix="$TASK5_ACTION_DIR/$clone_name.setup.$step_name"
  command_path="$prefix.command"
  stdout_path="$prefix.stdout"
  stderr_path="$prefix.stderr"
  status_path="$prefix.status"
  for output_path in "$command_path" "$stdout_path" "$stderr_path" \
      "$status_path"; do
    task5_require_absent_path "$output_path"
  done
  task5_record_argv "$command_path" "$@"
  set +e
  "$@" > "$stdout_path" 2> "$stderr_path"
  step_status=$?
  set -e
  printf '%s\n' "$step_status" > "$status_path"
  for output_path in "$command_path" "$stdout_path" "$stderr_path" \
      "$status_path"; do
    task5_require_owned_regular "$output_path"
  done
  test "$step_status" = 0
)

task5_require_no_shared_obj_inodes() (
  set -euo pipefail
  test "$#" = 3
  source_root="$1"
  clone_root="$2"
  source_manifest="$3"
  while IFS= read -r manifest_line; do
    relative_path="${manifest_line#*  }"
    test "$(stat -f '%d:%i' "$source_root/$relative_path")" != \
      "$(stat -f '%d:%i' "$clone_root/$relative_path")"
  done < "$source_manifest"
)

task5_write_clone_identity() (
  set -euo pipefail
  test "$#" = 6
  clone_root="$1"
  target_commit="$2"
  expected_tree="$3"
  source_manifest="$4"
  clone_manifest="$5"
  identity_path="$6"
  task5_require_absent_path "$identity_path"
  actual_head="$(git -C "$clone_root" rev-parse HEAD)"
  actual_tree="$(git -C "$clone_root" rev-parse HEAD^{tree})"
  remote_output="$(git -C "$clone_root" remote)"
  alternates_path="$(git -C "$clone_root" rev-parse --git-path \
    objects/info/alternates)"
  case "$alternates_path" in
    /*) ;;
    *) alternates_path="$clone_root/$alternates_path" ;;
  esac
  task5_require_absent_path "$alternates_path"
  status_sha="$(git -C "$clone_root" \
    status --porcelain=v1 --untracked-files=all | \
    shasum -a 256 | awk '{print $1}')"
  test "$actual_head" = "$target_commit"
  test "$actual_tree" = "$expected_tree"
  test -z "$remote_output"
  test "$status_sha" = \
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
  printf 'HEAD=%s\ntree=%s\nremotes=0\nalternates=ABSENT\nstatus-sha256=%s\nobj-source-sha256=%s\nobj-clone-sha256=%s\n' \
    "$actual_head" "$actual_tree" "$status_sha" \
    "$(task5_sha256 "$source_manifest")" \
    "$(task5_sha256 "$clone_manifest")" > "$identity_path"
  task5_require_owned_regular "$identity_path"
)

task5_create_fresh_clone() (
  set -euo pipefail
  export LC_ALL=C
  export GIT_TERMINAL_PROMPT=0
  export GIT_ALLOW_PROTOCOL=file
  umask 077
  test "$#" = 4
  source_root="$(task5_physical_repo_root "$1")"
  target_commit="$2"
  expected_tree="$3"
  clone_name="$4"
  case "$clone_name" in
    ''|*..*|*[!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz._-]*)
      task5_fail "unsafe clone name" ;;
  esac
  test "$(git -C "$source_root" rev-parse HEAD)" = "$target_commit"
  test "$(git -C "$source_root" rev-parse "$target_commit^{tree}")" = \
    "$expected_tree"
  git -C "$source_root" diff --quiet
  git -C "$source_root" diff --cached --quiet
  test -z "$(git -C "$source_root" status --porcelain=v1 --untracked-files=all)"
  clone_root="$TASK5_ACTION_DIR/$clone_name"
  task5_require_absent_path "$clone_root"
  task5_run_clone_setup_step "$clone_name" 01-clone \
    git clone --no-hardlinks --no-checkout -- "$source_root" "$clone_root"
  task5_run_clone_setup_step "$clone_name" 02-remove-origin \
    git -C "$clone_root" remote remove origin
  task5_run_clone_setup_step "$clone_name" 03-disable-protocol \
    git -C "$clone_root" config --local protocol.allow never
  task5_run_clone_setup_step "$clone_name" 04-enable-file-protocol \
    git -C "$clone_root" config --local protocol.file.allow always
  task5_run_clone_setup_step "$clone_name" 05-checkout \
    git -C "$clone_root" checkout --detach "$target_commit"
  task5_run_clone_setup_step "$clone_name" 06-mkdir-obj \
    mkdir -p "$clone_root/oracle/plugin" "$clone_root/oracle/plugin/tests"
  task5_run_clone_setup_step "$clone_name" 07-copy-plugin-obj \
    cp -R -p "$source_root/oracle/plugin/obj" "$clone_root/oracle/plugin/obj"
  task5_run_clone_setup_step "$clone_name" 08-copy-tests-obj \
    cp -R -p "$source_root/oracle/plugin/tests/obj" \
      "$clone_root/oracle/plugin/tests/obj"
  source_manifest="$TASK5_ACTION_DIR/$clone_name.obj-source.manifest"
  clone_manifest="$TASK5_ACTION_DIR/$clone_name.obj-clone.manifest"
  task5_require_absent_path "$source_manifest"
  task5_require_absent_path "$clone_manifest"
  task5_run_clone_setup_step "$clone_name" 09-source-manifest \
    task5_obj_manifest "$source_root" "$source_manifest"
  task5_run_clone_setup_step "$clone_name" 10-clone-manifest \
    task5_obj_manifest "$clone_root" "$clone_manifest"
  task5_run_clone_setup_step "$clone_name" 11-compare-manifests \
    cmp -s "$source_manifest" "$clone_manifest"
  task5_run_clone_setup_step "$clone_name" 12-no-shared-inodes \
    task5_require_no_shared_obj_inodes \
      "$source_root" "$clone_root" "$source_manifest"
  identity_path="$TASK5_ACTION_DIR/$clone_name.setup.identity"
  task5_run_clone_setup_step "$clone_name" 13-authenticate-clone \
    task5_write_clone_identity "$clone_root" "$target_commit" \
      "$expected_tree" "$source_manifest" "$clone_manifest" "$identity_path"
  printf '%s\n' "$clone_root"
)

task5_apply_exact_patch() (
  set -euo pipefail
  test "$#" = 4
  clone_root="$1"
  patch_path="$2"
  direction="$3"
  label="$4"
  case "$direction" in
    forward) apply_direction= ;;
    reverse) apply_direction=--reverse ;;
    *) task5_fail "patch direction must be forward or reverse" ;;
  esac
  for phase in check apply; do
    command_path="$TASK5_ACTION_DIR/$label.$phase.command"
    stdout_path="$TASK5_ACTION_DIR/$label.$phase.stdout"
    stderr_path="$TASK5_ACTION_DIR/$label.$phase.stderr"
    status_path="$TASK5_ACTION_DIR/$label.$phase.status"
    for output_path in "$stdout_path" "$stderr_path" "$status_path"; do
      task5_require_absent_path "$output_path"
    done
    if test "$phase" = check; then
      task5_record_argv "$command_path" git -C "$clone_root" apply \
        ${apply_direction:+"$apply_direction"} --check --index "$patch_path"
      set +e
      git -C "$clone_root" apply ${apply_direction:+"$apply_direction"} \
        --check --index "$patch_path" > "$stdout_path" 2> "$stderr_path"
    else
      task5_record_argv "$command_path" git -C "$clone_root" apply \
        ${apply_direction:+"$apply_direction"} --index "$patch_path"
      set +e
      git -C "$clone_root" apply ${apply_direction:+"$apply_direction"} \
        --index "$patch_path" > "$stdout_path" 2> "$stderr_path"
    fi
    apply_status=$?
    set -e
    printf '%s\n' "$apply_status" > "$status_path"
    test "$apply_status" = 0
    test ! -s "$stdout_path"
    test ! -s "$stderr_path"
  done
)

task5_assert_restored_clone() (
  set -euo pipefail
  test "$#" = 7
  clone_root="$1"
  clean_commit="$2"
  clean_tree="$3"
  target_path="$4"
  parent_sha="$5"
  parent_blob="$6"
  clean_plugin="$7"
  test "$(git -C "$clone_root" rev-parse HEAD)" = "$clean_commit"
  test "$(git -C "$clone_root" write-tree)" = "$clean_tree"
  test "$(git -C "$clone_root" ls-tree "$clean_tree" oracle/plugin | \
    awk '{print $3}')" = "$clean_plugin"
  test "$(task5_sha256 "$clone_root/$target_path")" = "$parent_sha"
  test "$(git -C "$clone_root" hash-object "$target_path")" = "$parent_blob"
  git -C "$clone_root" diff --quiet
  git -C "$clone_root" diff --cached --quiet
  test -z "$(git -C "$clone_root" status --porcelain=v1 --untracked-files=all)"
)

task5_run_canonical_mutation() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  mutation_id="$4"
  test "$checkpoint" = C53C2
  task5_require_sealed_review_pair C53C2
  task5_load_canonical_mutation "$mutation_id"
  task5_require_committed_checkpoint "$repo_root" "$evidence_root" C53C2
  C53C2="$(task5_resolve_alias "$evidence_root" C53C2)"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$C53C2"
  clean_tree="$(git -C "$repo_root" rev-parse "$C53C2^{tree}")"
  clean_plugin="$(git -C "$repo_root" ls-tree "$clean_tree" oracle/plugin | \
    awk '{print $3}')"
  clean_core="$(git -C "$repo_root" ls-tree "$clean_plugin" Core | awk '{print $3}')"
  clean_tests="$(git -C "$repo_root" ls-tree "$clean_plugin" tests | awk '{print $3}')"
  test "$clean_plugin" = 5a7db9d1e661dd97bd6a939d375dd2008506f679
  test "$clean_core" = 531718e596ed3f49f97f92c14edc69c69d60b834
  test "$clean_tests" = b75e36e1ce25538fd1d3cdd85c49f04d003af416
  task5_assert_restored_clone "$repo_root" "$C53C2" "$clean_tree" \
    "$mutation_target" "$mutation_parent_sha" "$mutation_parent_blob" \
    "$clean_plugin"
  artifact_dir="$(task5_init_artifact_dir "$evidence_root" \
    "canonical-$mutation_id")"
  patch_path="$(task5_extract_catalog_artifact canonical "$mutation_id" \
    "$artifact_dir")"

  clone_root="$(task5_create_fresh_clone "$repo_root" "$C53C2" \
    "$clean_tree" "$mutation_id-run")"
  task5_apply_exact_patch "$clone_root" "$patch_path" forward \
    "$mutation_id.forward"
  test "$(git -C "$clone_root" diff --cached --name-only)" = "$mutation_target"
  test "$(task5_sha256 "$clone_root/$mutation_target")" = "$mutation_result_sha"
  test "$(git -C "$clone_root" hash-object "$mutation_target")" = \
    "$mutation_result_blob"
  mutated_tree="$(git -C "$clone_root" write-tree)"
  mutated_plugin="$(git -C "$clone_root" ls-tree "$mutated_tree" oracle/plugin | \
    awk '{print $3}')"
  test "$mutated_plugin" = "$mutation_plugin"
  identity_path="$artifact_dir/$mutation_id.mutated.identity"
  task5_require_absent_path "$identity_path"
  printf 'checkpoint=%s\nclean-tree=%s\nmutated-tree=%s\nclean-plugin=%s\nmutated-plugin=%s\ntarget=%s\nparent-sha256=%s\nparent-blob=%s\nmutated-sha256=%s\nmutated-blob=%s\n' \
    "$C53C2" "$clean_tree" "$mutated_tree" "$clean_plugin" \
    "$mutated_plugin" "$mutation_target" "$mutation_parent_sha" \
    "$mutation_parent_blob" "$mutation_result_sha" "$mutation_result_blob" \
    > "$identity_path"

  task5_raw_force_net10 "$clone_root" "$artifact_dir" mutated-build
  task5_require_raw_build_green "$artifact_dir" mutated-build
  task5_raw_focused_csharp "$clone_root" "$mutation_cohort" \
    "$artifact_dir" mutated-red
  test "$(cat "$artifact_dir/mutated-red.status")" = 1
  test ! -s "$artifact_dir/mutated-red.stderr"
  test "$(sed -n '1p' "$artifact_dir/mutated-red.stdout")" = \
    "$mutation_failure"
  test "$(awk '/^cohort / {n++} END {print n + 0}' \
    "$artifact_dir/mutated-red.stdout")" = 1

  task5_apply_exact_patch "$clone_root" "$patch_path" reverse \
    "$mutation_id.reverse"
  task5_assert_restored_clone "$clone_root" "$C53C2" "$clean_tree" \
    "$mutation_target" "$mutation_parent_sha" "$mutation_parent_blob" \
    "$clean_plugin"
  task5_raw_force_net10 "$clone_root" "$artifact_dir" restored-build
  task5_require_raw_build_green "$artifact_dir" restored-build
  task5_raw_focused_csharp "$clone_root" "$mutation_cohort" \
    "$artifact_dir" restored-green
  task5_require_raw_focused_green "$artifact_dir" restored-green

  replay_root="$(task5_create_fresh_clone "$repo_root" "$C53C2" \
    "$clean_tree" "$mutation_id-replay")"
  task5_apply_exact_patch "$replay_root" "$patch_path" forward \
    "$mutation_id.replay-forward"
  test "$(task5_sha256 "$replay_root/$mutation_target")" = "$mutation_result_sha"
  test "$(git -C "$replay_root" hash-object "$mutation_target")" = \
    "$mutation_result_blob"
  replay_tree="$(git -C "$replay_root" write-tree)"
  test "$(git -C "$replay_root" ls-tree "$replay_tree" oracle/plugin | \
    awk '{print $3}')" = "$mutation_plugin"
  task5_apply_exact_patch "$replay_root" "$patch_path" reverse \
    "$mutation_id.replay-reverse"
  task5_assert_restored_clone "$replay_root" "$C53C2" "$clean_tree" \
    "$mutation_target" "$mutation_parent_sha" "$mutation_parent_blob" \
    "$clean_plugin"
  printf '%s killed-and-restored checkpoint=%s mutated-tree=%s replay-tree=%s\n' \
    "$mutation_id" "$C53C2" "$mutated_tree" "$replay_tree"
)

task5_run_rejected_mutation() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  rejected_id="$4"
  test "$checkpoint" = C53C2
  task5_require_sealed_review_pair C53C2
  case "$rejected_id" in
    T5M20)
      target_path=oracle/plugin/Core/PassiveDriver.cs
      parent_sha=093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130
      parent_blob=b132f89b321345452901faab870ea0d642b93e06 ;;
    T5M23)
      target_path=oracle/plugin/Core/PassiveDriver.cs
      parent_sha=093ff0c2254909167d9666dcac3fb2ee59178623788577fbc1a5bbef4f6a5130
      parent_blob=b132f89b321345452901faab870ea0d642b93e06 ;;
    *) task5_fail "rejected mutation ID must be T5M20 or T5M23" ;;
  esac
  task5_require_committed_checkpoint "$repo_root" "$evidence_root" C53C2
  C53C2="$(task5_resolve_alias "$evidence_root" C53C2)"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$C53C2"
  clean_tree="$(git -C "$repo_root" rev-parse "$C53C2^{tree}")"
  clean_plugin=5a7db9d1e661dd97bd6a939d375dd2008506f679
  artifact_dir="$(task5_init_artifact_dir "$evidence_root" \
    "rejected-$rejected_id")"
  patch_path="$(task5_extract_catalog_artifact rejected "$rejected_id" \
    "$artifact_dir")"
  clone_root="$(task5_create_fresh_clone "$repo_root" "$C53C2" \
    "$clean_tree" "rejected-$rejected_id-clone")"
  task5_apply_exact_patch "$clone_root" "$patch_path" forward \
    "rejected-$rejected_id.forward"
  test "$(git -C "$clone_root" diff --cached --name-only)" = "$target_path"
  mutated_blob="$(git -C "$clone_root" hash-object "$target_path")"
  case "$rejected_id:$mutated_blob" in
    T5M20:f2520f7a688910f95004d1edfc7fadc1008cda23) ;;
    T5M23:18aa7e38a8b68101e4d7c29b7fc605b67c9bd02d) ;;
    *) task5_fail "rejected mutation produced an unexpected target blob" ;;
  esac

  task5_raw_force_net10 "$clone_root" "$artifact_dir" rejected-build
  if test "$rejected_id" = T5M20; then
    test "$(cat "$artifact_dir/rejected-build.status")" = 1
    diagnostics="$artifact_dir/rejected-build.diagnostics"
    task5_require_absent_path "$diagnostics"
    (cat "$artifact_dir/rejected-build.stdout"; \
      cat "$artifact_dir/rejected-build.stderr") | \
      awk 'match($0, /error CS[0-9]+/) {print substr($0,RSTART+6,6)}' | \
      sort -u > "$diagnostics"
    test "$(cat "$diagnostics")" = "CS0103
CS0219"
    combined_build="$(cat "$artifact_dir/rejected-build.stdout"; \
      cat "$artifact_dir/rejected-build.stderr")"
    test "$(printf '%s\n' "$combined_build" | awk \
      '/^[[:space:]]*0 Warning[(]s[)]$/ {n++} END {print n + 0}')" = 1
    test "$(printf '%s\n' "$combined_build" | awk \
      '/^[[:space:]]*2 Error[(]s[)]$/ {n++} END {print n + 0}')" = 1
    no_test_path="$artifact_dir/mutated-test.not-run"
    task5_require_absent_path "$no_test_path"
    printf 'mutated-test-invocations=0\n' > "$no_test_path"
  else
    task5_require_raw_build_green "$artifact_dir" rejected-build
    task5_raw_focused_csharp "$clone_root" driver-terminal \
      "$artifact_dir" rejected-red
    test "$(cat "$artifact_dir/rejected-red.status")" = 1
    test ! -s "$artifact_dir/rejected-red.stderr"
    expected_failure="cohort 'driver-terminal', test 'sink failure uses trace io marker': System.InvalidOperationException: Step 2 failure is marker-only Close count"
    test "$(sed -n '1p' "$artifact_dir/rejected-red.stdout")" = \
      "$expected_failure"
    test "$(awk '/^cohort / {n++} END {print n + 0}' \
      "$artifact_dir/rejected-red.stdout")" = 1
  fi

  task5_apply_exact_patch "$clone_root" "$patch_path" reverse \
    "rejected-$rejected_id.reverse"
  task5_assert_restored_clone "$clone_root" "$C53C2" "$clean_tree" \
    "$target_path" "$parent_sha" "$parent_blob" "$clean_plugin"
  task5_raw_force_net10 "$clone_root" "$artifact_dir" restored-build
  task5_require_raw_build_green "$artifact_dir" restored-build
  task5_raw_focused_csharp "$clone_root" driver-terminal \
    "$artifact_dir" restored-green
  task5_require_raw_focused_green "$artifact_dir" restored-green
  printf 'rejected-%s provenance=PASS restored-tree=%s\n' \
    "$rejected_id" "$clean_tree"
)

task5_run_t5m28_proof() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  proof_name="$4"
  test "$checkpoint" = C53C2
  case "$proof_name" in
    C53C2-T5M28-proof|Task4-T5M28-replay) ;;
    *) task5_fail "T5M28 proof name is outside the closed set" ;;
  esac
  if test "$proof_name" = Task4-T5M28-replay; then
    task5_require_sealed_review_pair C53C2
  fi
  task5_require_committed_checkpoint "$repo_root" "$evidence_root" C53C2
  C53C2="$(task5_resolve_alias "$evidence_root" C53C2)"
  P="$(task5_resolve_alias "$evidence_root" P)"
  test "$P" = "$TASK5_PLAN_COMMIT"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$C53C2"
  clean_tree="$(git -C "$repo_root" rev-parse "$C53C2^{tree}")"
  clean_plugin=5a7db9d1e661dd97bd6a939d375dd2008506f679
  terminal_test=oracle/plugin/tests/PassiveDriverTerminalTests.cs
  terminal_sha=cc3001bee5c239b1a1e3c34fecafa3ad80c379e8c3b2c88b787dfaaae8d74bf9
  terminal_blob=60a8a94fd8d0603b861fb7ccf80a7d20d1697d59
  task5_assert_restored_clone "$repo_root" "$C53C2" "$clean_tree" \
    "$terminal_test" "$terminal_sha" "$terminal_blob" "$clean_plugin"

  artifact_dir="$(task5_init_artifact_dir "$evidence_root" "$proof_name")"
  clone_root="$(task5_create_fresh_clone "$repo_root" "$C53C2" \
    "$clean_tree" "$proof_name-clone")"
  hook_path="$(task5_extract_catalog_artifact proof hook "$artifact_dir")"
  qualified_probe="$(task5_extract_catalog_artifact proof probe "$artifact_dir")"
  runtime_dir="$artifact_dir/runtime"
  task5_require_absent_path "$runtime_dir"
  mkdir -m 700 "$runtime_dir"
  task5_require_owned_directory "$runtime_dir" 700
  test "$(cd "$runtime_dir/.." && pwd -P)" = "$artifact_dir"
  test -z "$(find "$runtime_dir" -mindepth 1 -print -quit)"

  historical_path=/private/tmp/ssr-t5m18-28.nRkx7h/evidence-c/M28
  test "$(awk -v needle="$historical_path" \
    'index($0,needle) {n++} END {print n + 0}' "$qualified_probe")" = 1
  transformed_probe="$runtime_dir/stale_probe.py"
  roundtrip_probe="$artifact_dir/stale_probe.roundtrip.py"
  transform_identity="$artifact_dir/T5M28-transformed-probe.identity"
  for output_path in "$transformed_probe" "$roundtrip_probe" \
      "$transform_identity"; do
    task5_require_absent_path "$output_path"
  done
  sed "s#$historical_path#$runtime_dir#g" "$qualified_probe" \
    > "$transformed_probe"
  sed "s#$runtime_dir#$historical_path#g" "$transformed_probe" \
    > "$roundtrip_probe"
  cmp -s "$qualified_probe" "$roundtrip_probe"
  test "$(wc -l < "$transformed_probe" | tr -d '[:space:]')" = 33
  test "$(awk -v needle="$historical_path" \
    'index($0,needle) {n++} END {print n + 0}' "$transformed_probe")" = 0
  printf 'proof=%s\ntransformed-sha256=%s\ntransformed-lines=%s\ntransformed-bytes=%s\n' \
    "$proof_name" "$(task5_sha256 "$transformed_probe")" \
    "$(wc -l < "$transformed_probe" | tr -d '[:space:]')" \
    "$(wc -c < "$transformed_probe" | tr -d '[:space:]')" \
    > "$transform_identity"

  python_bin="$repo_root/.venv/bin/python"
  reader_path="$repo_root/src/ssr_env/oracle_protocol.py"
  test -x "$python_bin"
  test "$(task5_sha256 "$reader_path")" = \
    9feab69eec050eea51670c9f80b00acba06799e500a4ed3502f02722d5ea7108
  test "$(git -C "$repo_root" hash-object src/ssr_env/oracle_protocol.py)" = \
    f390923533985d4b1595ea50f5dcf8119d1c1cca
  import_command="$artifact_dir/import.command"
  import_stdout="$artifact_dir/import.stdout"
  import_stderr="$artifact_dir/import.stderr"
  import_status_path="$artifact_dir/import.status"
  for output_path in "$import_stdout" "$import_stderr" "$import_status_path"; do
    task5_require_absent_path "$output_path"
  done
  task5_record_argv "$import_command" /usr/bin/env \
    PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 "PYTHONPATH=$repo_root/src" \
    "$python_bin" -c \
    'from pathlib import Path; import ssr_env.oracle_protocol as p; print(Path(p.__file__).resolve())'
  set +e
  (cd "$repo_root" && PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 \
    PYTHONPATH="$repo_root/src" "$python_bin" -c \
    'from pathlib import Path; import ssr_env.oracle_protocol as p; print(Path(p.__file__).resolve())') \
    > "$import_stdout" 2> "$import_stderr"
  import_status=$?
  set -e
  printf '%s\n' "$import_status" > "$import_status_path"
  test "$import_status" = 0
  test ! -s "$import_stderr"
  test "$(cat "$import_stdout")" = "$reader_path"

  task5_apply_exact_patch "$clone_root" "$hook_path" forward \
    "$proof_name.hook-forward"
  test "$(git -C "$clone_root" diff --cached --name-only)" = "$terminal_test"
  test "$(git -C "$clone_root" hash-object "$terminal_test")" = \
    0f057da9dd9fd4396404c2d3c4afcca4fafa98cf
  hook_identity="$artifact_dir/hook-mutated.identity"
  task5_require_absent_path "$hook_identity"
  hook_tree="$(git -C "$clone_root" write-tree)"
  hook_plugin="$(git -C "$clone_root" ls-tree "$hook_tree" oracle/plugin | \
    awk '{print $3}')"
  test "$(task5_sha256 "$clone_root/$terminal_test")" = \
    15da95949ec0df98f8ec7b9bec4e10738257b2c678ff53535fe8930025cd1698
  test "$hook_plugin" = f4e650335dbe5f6656ee19fefafd8d5bad367f73
  printf 'test-sha256=%s\ntest-blob=%s\nplugin-tree=%s\nfull-tree=%s\n' \
    "$(task5_sha256 "$clone_root/$terminal_test")" \
    "$(git -C "$clone_root" hash-object "$terminal_test")" \
    "$hook_plugin" "$hook_tree" > "$hook_identity"
  task5_raw_force_net10 "$clone_root" "$artifact_dir" export-build
  task5_require_raw_build_green "$artifact_dir" export-build

  real_trace="$runtime_dir/actual-clean-trace.ndjson"
  task5_require_absent_path "$real_trace"
  export_dotnet=/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet
  export_project="$clone_root/oracle/plugin/tests/SsrOracle.UnitTests.csproj"
  export_command="$artifact_dir/export-run.command"
  export_stdout="$artifact_dir/export-run.stdout"
  export_stderr="$artifact_dir/export-run.stderr"
  export_status_path="$artifact_dir/export-run.status"
  for output_path in "$export_stdout" "$export_stderr" "$export_status_path"; do
    task5_require_absent_path "$output_path"
  done
  task5_record_argv "$export_command" /usr/bin/env \
    "SSR_T5M28_TRACE_PROBE=$real_trace" "$export_dotnet" run --project \
    "$export_project" --configuration Release --no-restore --no-build -- \
    --cohort driver-terminal
  task5_require_dotnet >/dev/null
  set +e
  SSR_T5M28_TRACE_PROBE="$real_trace" "$export_dotnet" run --project \
    "$export_project" --configuration Release --no-restore --no-build -- \
    --cohort driver-terminal > "$export_stdout" 2> "$export_stderr"
  export_status=$?
  set -e
  printf '%s\n' "$export_status" > "$export_status_path"
  test "$export_status" = 0
  test ! -s "$export_stderr"
  test "$(cat "$export_stdout")" = 'SSR oracle unit harness ready'
  task5_require_owned_regular "$real_trace"
  test "$(task5_sha256 "$real_trace")" = \
    df50d409c3264ce12e33bab510fa7caf65a18cec1ddfa303fe57d04e46c1c577
  test "$(wc -l < "$real_trace" | tr -d '[:space:]')" = 6
  test "$(wc -c < "$real_trace" | tr -d '[:space:]')" = 2138

  task5_apply_exact_patch "$clone_root" "$hook_path" reverse \
    "$proof_name.hook-reverse"
  task5_assert_restored_clone "$clone_root" "$C53C2" "$clean_tree" \
    "$terminal_test" "$terminal_sha" "$terminal_blob" "$clean_plugin"
  task5_raw_force_net10 "$clone_root" "$artifact_dir" restored-build
  task5_require_raw_build_green "$artifact_dir" restored-build
  task5_raw_focused_csharp "$clone_root" driver-terminal \
    "$artifact_dir" restored-green
  task5_require_raw_focused_green "$artifact_dir" restored-green

  parser_command="$artifact_dir/parser.command"
  parser_stdout="$artifact_dir/parser.stdout"
  parser_stderr="$artifact_dir/parser.stderr"
  parser_status_path="$artifact_dir/parser.status"
  for output_path in "$parser_stdout" "$parser_stderr" "$parser_status_path"; do
    task5_require_absent_path "$output_path"
  done
  task5_record_argv "$parser_command" /usr/bin/env PYTHONDONTWRITEBYTECODE=1 \
    UV_OFFLINE=1 "PYTHONPATH=$repo_root/src" "$python_bin" "$transformed_probe"
  real_trace_sha_before="$(task5_sha256 "$real_trace")"
  set +e
  (cd "$repo_root" && PYTHONDONTWRITEBYTECODE=1 UV_OFFLINE=1 \
    PYTHONPATH="$repo_root/src" "$python_bin" "$transformed_probe") \
    > "$parser_stdout" 2> "$parser_stderr"
  parser_status=$?
  set -e
  printf '%s\n' "$parser_status" > "$parser_status_path"
  test "$parser_status" = 0
  test ! -s "$parser_stderr"
  test "$(cat "$parser_stdout")" = \
    'PASS stale trace rejected: error input_index must equal the flushed-step count'
  test "$(task5_sha256 "$parser_stdout")" = \
    992e6beb20c4e31aafea61fe528de5c542767a8c93e486c2680aab64920becdc
  stale_trace="$runtime_dir/stale-claim-time-trace.ndjson"
  task5_require_owned_regular "$stale_trace"
  test "$(task5_sha256 "$stale_trace")" = \
    933657b5b7cca75860106a6cb99b3d43e1cd569b489733c781fda699db9911cf
  test "$(wc -l < "$stale_trace" | tr -d '[:space:]')" = 6
  test "$(wc -c < "$stale_trace" | tr -d '[:space:]')" = 2357
  test "$(task5_sha256 "$real_trace")" = "$real_trace_sha_before"
  test "$(task5_sha256 "$real_trace")" = \
    df50d409c3264ce12e33bab510fa7caf65a18cec1ddfa303fe57d04e46c1c577
  test -z "$(find "$runtime_dir" -type l -print)"
  test -z "$(find "$runtime_dir" ! -type d ! -type f -print)"
  test "$(find "$runtime_dir" -mindepth 1 -type f -print | \
    wc -l | tr -d '[:space:]')" = 3
  test "$(find "$runtime_dir" -mindepth 1 -type d -print | \
    wc -l | tr -d '[:space:]')" = 0
  printf '%s checkpoint=%s real-trace=%s stale-trace=%s parser=PASS\n' \
    "$proof_name" "$C53C2" "$real_trace_sha_before" \
    "$(task5_sha256 "$stale_trace")"
)

task5_parent_checkpoint() {
  test "$#" = 1
  case "$1" in
    C51) printf '%s\n' P ;;
    C52) printf '%s\n' C51 ;;
    C53) printf '%s\n' C52 ;;
    C53C1) printf '%s\n' C53 ;;
    C53C2) printf '%s\n' C53C1 ;;
    R) printf '%s\n' C53C2 ;;
    *) task5_fail "checkpoint has no controller-managed parent" ;;
  esac
}

task5_checkpoint_subject() {
  test "$#" = 1
  case "$1" in
    P) printf '%s\n' 'docs: plan Task 5 passive driver completion' ;;
    C51) printf '%s\n' 'feat: attribute passive input attempts' ;;
    C52) printf '%s\n' 'feat: balance passive lifecycle hooks' ;;
    C53) printf '%s\n' 'feat: finalize passive trace capture' ;;
    C53C1) printf '%s\n' 'fix: serialize passive terminal handoff' ;;
    C53C2) printf '%s\n' 'fix: rebase deferred step faults' ;;
    R) printf '%s\n' 'docs: record Task 5 passive driver verification' ;;
    *) task5_fail "checkpoint has no exact subject" ;;
  esac
}

task5_write_checkpoint_scope() (
  set -euo pipefail
  test "$#" = 2
  checkpoint="$1"
  output_path="$2"
  task5_require_checkpoint "$checkpoint"
  task5_require_absent_path "$output_path"
  case "$checkpoint" in
    P)
      printf '%s\n' \
        docs/superpowers/plans/2026-08-07-task-5-passive-driver.md \
        > "$output_path" ;;
    C51)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverInput.cs \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C52)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverInput.cs \
        oracle/plugin/Core/PassiveDriverLifecycleHooks.cs \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C53)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverCompletion.cs \
        oracle/plugin/Core/PassiveDriverInput.cs \
        oracle/plugin/tests/PassiveDriverInputTests.cs \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs \
        oracle/plugin/tests/PassiveDriverTests.cs \
        oracle/plugin/tests/Program.cs > "$output_path" ;;
    C53C1)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriver.cs \
        oracle/plugin/Core/PassiveDriverCompletion.cs \
        oracle/plugin/Core/PassiveDriverInput.cs \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs \
        oracle/plugin/tests/PassiveDriverTestSupport.cs > "$output_path" ;;
    C53C2)
      printf '%s\n' \
        oracle/plugin/Core/PassiveDriverInput.cs \
        oracle/plugin/tests/PassiveDriverTerminalTests.cs > "$output_path" ;;
    R)
      printf '%s\n' \
        docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md \
        > "$output_path" ;;
  esac
  task5_require_owned_regular "$output_path"
  test "$(sort -u "$output_path" | wc -l | tr -d '[:space:]')" = \
    "$(wc -l < "$output_path" | tr -d '[:space:]')"
)

task5_require_committed_checkpoint() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  task5_require_checkpoint "$checkpoint"
  commit_oid="$(task5_resolve_alias "$evidence_root" "$checkpoint")"
  test "$(git -C "$repo_root" rev-parse --verify "$commit_oid^{commit}")" = \
    "$commit_oid"
  test "$(git -C "$repo_root" show -s --format=%s "$commit_oid")" = \
    "$(task5_checkpoint_subject "$checkpoint")"
  if test "$checkpoint" = P; then
    expected_parent=9f69d2c40406461a28f018290d579cf313f22287
    task5_require_p_identity "$commit_oid" "$repo_root"
  else
    parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
    expected_parent="$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
  fi
  test "$(git -C "$repo_root" rev-list --parents -n 1 "$commit_oid")" = \
    "$commit_oid $expected_parent"
  expected_scope="$TASK5_ACTION_DIR/$checkpoint.expected-committed-scope"
  actual_scope="$TASK5_ACTION_DIR/$checkpoint.actual-committed-scope"
  task5_write_checkpoint_scope "$checkpoint" "$expected_scope"
  task5_require_absent_path "$actual_scope"
  git -C "$repo_root" diff-tree --no-commit-id --name-only -r "$commit_oid" | \
    LC_ALL=C sort -u > "$actual_scope"
  cmp -s "$expected_scope" "$actual_scope"
  commit_tree="$(git -C "$repo_root" rev-parse "$commit_oid^{tree}")"
  case "$checkpoint" in
    C51)
      expected_plugin=694928891148bfad6b4215f9d4efbb943f44a104
      expected_core=26a0c6acfc7b9ce22f5f93a879b462bf721baa33
      expected_tests=2fa6213f563d4a8d9aa01f1cb590f34b04f34e8e ;;
    C52)
      expected_plugin=1a3379be8b250f1a0ef6020ca2265be98ec1353a
      expected_core=81fe40cec8877c937ed2b7f9e9dca967d5179add
      expected_tests=c2a8b9b184298fb75659c345e0c1aec493ff4b73 ;;
    C53)
      expected_plugin=1364987fc311b8ade46ac8599f06140befd50d7d
      expected_core=f709ff7d0496ee8214f582eb1a7d0dadd895941f
      expected_tests=c6a18ad771bf796dc91103ba19a853890e6b449a ;;
    C53C1)
      expected_plugin=8afbf9d17f762bec53f31fa30648e7a77f396085
      expected_core=d1ac5945be7ef1cb32603fe5525defd073a584d4
      expected_tests=596492b71f9e386470d5c0615543524835f3f28c ;;
    C53C2)
      expected_plugin=5a7db9d1e661dd97bd6a939d375dd2008506f679
      expected_core=531718e596ed3f49f97f92c14edc69c69d60b834
      expected_tests=b75e36e1ce25538fd1d3cdd85c49f04d003af416 ;;
    P|R) expected_plugin= expected_core= expected_tests= ;;
  esac
  if test -n "$expected_plugin"; then
    plugin_tree="$(git -C "$repo_root" ls-tree "$commit_tree" oracle/plugin | \
      awk '{print $3}')"
    core_tree="$(git -C "$repo_root" ls-tree "$plugin_tree" Core | awk '{print $3}')"
    tests_tree="$(git -C "$repo_root" ls-tree "$plugin_tree" tests | awk '{print $3}')"
    test "$plugin_tree" = "$expected_plugin"
    test "$core_tree" = "$expected_core"
    test "$tests_tree" = "$expected_tests"
  fi
  printf '%s=%s tree=%s parent=%s\n' \
    "$checkpoint" "$commit_oid" "$commit_tree" "$expected_parent"
)

task5_run_plan_postcommit() (
  set -euo pipefail
  umask 077
  test "$#" = 5
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  expected_plan_sha="$3"
  expected_checker_sha="$4"
  expected_authority_sha="$5"
  task5_require_evidence_root "$evidence_root"
  task5_require_clean_controller "$repo_root" "$evidence_root"
  task5_require_sha256 "$expected_plan_sha"
  task5_require_sha256 "$expected_checker_sha"
  task5_require_sha256 "$expected_authority_sha"
  test "$expected_checker_sha" = "$TASK5_PLAN_AUDITOR_SHA"
  test "$expected_authority_sha" = "$TASK5_AUTHORITY_BUNDLE_SHA"
  task5_require_authority_bundle
  P="$(task5_resolve_alias "$evidence_root" P)"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$P"
  git -C "$repo_root" diff --quiet
  git -C "$repo_root" diff --cached --quiet
  test -z "$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)"
  audit_stdout="$TASK5_ACTION_DIR/plan-postcommit.stdout"
  audit_stderr="$TASK5_ACTION_DIR/plan-postcommit.stderr"
  audit_status_path="$TASK5_ACTION_DIR/plan-postcommit.status"
  for output_path in "$audit_stdout" "$audit_stderr" "$audit_status_path"; do
    task5_require_absent_path "$output_path"
  done
  set +e
  (cd "$repo_root" && /usr/bin/env -i \
    PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C LANG=C \
    HOME=/private/tmp TMPDIR=/private/tmp \
    GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
    GIT_TERMINAL_PROMPT=0 \
    /bin/bash --noprofile --norc "$TASK5_PLAN_AUDITOR_PATH" committed "$P") \
    > "$audit_stdout" 2> "$audit_stderr"
  audit_status=$?
  set -e
  printf '%s\n' "$audit_status" > "$audit_status_path"
  test "$audit_status" = 0
  test ! -s "$audit_stderr"
  test "$(awk -F= '$1 == "plan-sha256" {print $2}' "$audit_stdout")" = \
    "$expected_plan_sha"
  test "$(awk -F= '$1 == "checker-sha256" {print $2}' "$audit_stdout")" = \
    "$expected_checker_sha"
  authority_receipt="$TASK5_AUTHORITY_BUNDLE_ROOT/authority.receipt"
  test "$(task5_receipt_value "$authority_receipt" plan-sha256)" = \
    "$expected_plan_sha"
  test "$(task5_receipt_value "$authority_receipt" checker-sha256)" = \
    "$expected_checker_sha"
  test "$(task5_receipt_value "$authority_receipt" runtime-sha256)" = \
    "$(awk -F= '$1 == "runtime-sha256" {print $2}' "$audit_stdout")"
  test "$(task5_receipt_value "$authority_receipt" bootstrap-sha256)" = \
    "$(awk -F= '$1 == "bootstrap-sha256" {print $2}' "$audit_stdout")"
  test "$(task5_receipt_value "$authority_receipt" core-manifest-sha256)" = \
    "$(awk -F= '$1 == "core-manifest-sha256" {print $2}' "$audit_stdout")"
  test "$(task5_receipt_value "$authority_receipt" canonical-mutation-manifest-sha256)" = \
    "$(awk -F= '$1 == "canonical-mutation-manifest-sha256" {print $2}' \
      "$audit_stdout")"
  test "$(awk -F= '$1 == "mode" {print $2}' "$audit_stdout")" = committed
  printf 'authority-bundle-manifest-sha256=%s\n' \
    "$expected_authority_sha"
  cat "$audit_stdout"
)

task5_stage_checkpoint_patch() (
  set -euo pipefail
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  patch_kind="$4"
  task5_require_commit_checkpoint "$checkpoint"
  test "$checkpoint" != R
  case "$patch_kind" in
    tests|production) ;;
    *) task5_fail "patch kind must be tests or production" ;;
  esac
  parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
  parent_oid="$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
  case "$checkpoint" in
    C52) task5_require_sealed_review_pair C51 ;;
    C53) task5_require_sealed_review_pair C52 ;;
    C53C1) task5_require_sealed_review_pair C53 ;;
    C53C2) task5_require_sealed_review_pair C53C1 ;;
  esac
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$parent_oid"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  if test "$patch_kind" = tests; then
    git -C "$repo_root" diff --cached --quiet
    patch_id="$checkpoint-TESTS"
  else
    tests_state="$TASK5_STATE_ROOT/$checkpoint.tests-staged"
    task5_require_owned_regular "$tests_state" 400
    test "$(awk -F= '$1 == "index-tree" {print $2}' "$tests_state")" = \
      "$(git -C "$repo_root" write-tree)"
    patch_id="$checkpoint-PRODUCTION"
  fi
  case "$patch_id" in
    C51-TESTS) patch_sha=27b5d2da89f011a1e3c84a6cb27077ad093e46ab3ac05bb4bef4386c8c73d6eb; patch_lines=1213; patch_bytes=51384 ;;
    C51-PRODUCTION) patch_sha=dc60e234556f4cd5717dab1422c18edc63e42a87046200c135ff5f8fc32755c0; patch_lines=752; patch_bytes=23537 ;;
    C52-TESTS) patch_sha=13beee22b9b661320226c8deeb7979c574918d50c30b9f4498f5d35a9294e80c; patch_lines=880; patch_bytes=39208 ;;
    C52-PRODUCTION) patch_sha=69f717ed83deb3ff86fed13798764aa29f0120b29b7a649104d6cace218edd7e; patch_lines=395; patch_bytes=12407 ;;
    C53-TESTS) patch_sha=d56cb0b64868120338b27ced71299da7b78a87187a7b8dfa70b63bde329e7dcc; patch_lines=1123; patch_bytes=43301 ;;
    C53-PRODUCTION) patch_sha=918cbac02ec8e01ee61e89c0b5418d6430547c33b46ea949bc9f073943dc298c; patch_lines=159; patch_bytes=5310 ;;
    C53C1-TESTS) patch_sha=a37a0ea03c285bfc8d8068bbb7179787293ce925dc8d7c42ad47a9b53ada0112; patch_lines=2468; patch_bytes=95234 ;;
    C53C1-PRODUCTION) patch_sha=7c000fabda103b116b7a5ebc773da13692d3b4a838dcf280dd68b7ab5590102c; patch_lines=598; patch_bytes=18412 ;;
    C53C2-TESTS) patch_sha=175d83ab045a264e76f537b5c4d94ea3f945ac874bf7caa6417de2183976ece1; patch_lines=190; patch_bytes=7397 ;;
    C53C2-PRODUCTION) patch_sha=0ee216ead3ab2bd602bbcd42aa67eda31943f55db558250288452b785053354e; patch_lines=23; patch_bytes=1011 ;;
  esac
  before_tree="$(git -C "$repo_root" write-tree)"
  task5_extract_and_stage_plan_patch "$repo_root" "$evidence_root" \
    "$TASK5_PLAN_COMMIT" "$TASK5_PLAN_PATH" "$patch_id" \
    "$patch_sha" "$patch_lines" "$patch_bytes" "$parent_oid" "$before_tree"
)

task5_write_state_seal() (
  set -euo pipefail
  test "$#" = 4
  checkpoint="$1"
  state="$2"
  repo_root="$3"
  status_sha="$4"
  task5_require_checkpoint "$checkpoint"
  task5_require_state "$state"
  task5_require_sha256 "$status_sha"
  seal_path="$TASK5_STATE_ROOT/$checkpoint.$state"
  task5_require_absent_path "$seal_path"
  printf 'checkpoint=%s\nstate=%s\nHEAD=%s\nindex-tree=%s\nbranch=%s\nstatus-sha256=%s\n' \
    "$checkpoint" "$state" "$(git -C "$repo_root" rev-parse HEAD)" \
    "$(git -C "$repo_root" write-tree)" \
    "$(git -C "$repo_root" symbolic-ref -q HEAD)" "$status_sha" > "$seal_path"
  chmod 400 "$seal_path"
  task5_require_owned_regular "$seal_path" 400
)

task5_authenticate_state() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 4
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  state="$4"
  task5_require_checkpoint "$checkpoint"
  task5_require_state "$state"
  status_path="$TASK5_ACTION_DIR/$checkpoint.$state.porcelain"
  task5_require_absent_path "$status_path"
  git -C "$repo_root" status --porcelain=v1 --untracked-files=all > "$status_path"
  status_sha="$(task5_sha256 "$status_path")"
  case "$state" in
    clean|committed)
      commit_oid="$(task5_resolve_alias "$evidence_root" "$checkpoint")"
      test "$(git -C "$repo_root" rev-parse HEAD)" = "$commit_oid"
      test ! -s "$status_path"
      task5_require_committed_checkpoint "$repo_root" "$evidence_root" "$checkpoint" ;;
    tests-staged)
      test "$checkpoint" != P
      test "$checkpoint" != R
      parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
      parent_oid="$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
      test "$(git -C "$repo_root" rev-parse HEAD)" = "$parent_oid"
      git -C "$repo_root" diff --quiet
      test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
      expected_paths="$TASK5_ACTION_DIR/$checkpoint.tests.expected"
      actual_paths="$TASK5_ACTION_DIR/$checkpoint.tests.actual"
      task5_write_patch_path_manifest "$checkpoint-TESTS" patch "$expected_paths"
      task5_require_absent_path "$actual_paths"
      git -C "$repo_root" diff --cached --name-only --diff-filter=ACDMRTUXB | \
        sort -u > "$actual_paths"
      cmp -s "$expected_paths" "$actual_paths" ;;
    green-staged)
      test "$checkpoint" != P
      test "$checkpoint" != R
      parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
      parent_oid="$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
      test "$(git -C "$repo_root" rev-parse HEAD)" = "$parent_oid"
      task5_authenticate_checkpoint_index "$repo_root" "$evidence_root" \
        "$checkpoint" "$(git -C "$repo_root" rev-parse "$parent_oid^{tree}")" ;;
    report-candidate)
      test "$checkpoint" = R
      report_path=docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md
      test "$(cat "$status_path")" = "?? $report_path"
      task5_require_owned_regular "$repo_root/$report_path"
      test "$(cd "$repo_root/${report_path%/*}" && pwd -P)" = \
        "$repo_root/docs/superpowers/reports" ;;
    report-staged)
      test "$checkpoint" = R
      report_path=docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md
      git -C "$repo_root" diff --quiet
      test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
      test "$(git -C "$repo_root" diff --cached --name-only)" = "$report_path" ;;
  esac
  task5_write_state_seal "$checkpoint" "$state" "$repo_root" "$status_sha"
  printf '%s %s HEAD=%s index-tree=%s status=%s\n' "$checkpoint" "$state" \
    "$(git -C "$repo_root" rev-parse HEAD)" \
    "$(git -C "$repo_root" write-tree)" "$status_sha"
)

task5_commit_checkpoint() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  task5_require_review_target "$checkpoint"
  parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
  parent_oid="$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$parent_oid"
  if test "$checkpoint" = R; then
    gate_path="$TASK5_REPORT_GATES_ROOT/reviewed"
    task5_require_owned_regular "$gate_path" 400
    state_path="$TASK5_STATE_ROOT/R.report-staged"
  else
    state_path="$TASK5_STATE_ROOT/$checkpoint.green-staged"
  fi
  task5_require_owned_regular "$state_path" 400
  expected_tree="$(awk -F= '$1 == "index-tree" {print $2}' "$state_path")"
  test "$(git -C "$repo_root" write-tree)" = "$expected_tree"
  git -C "$repo_root" diff --quiet
  test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
  expected_scope="$TASK5_ACTION_DIR/$checkpoint.expected-commit-scope"
  actual_scope="$TASK5_ACTION_DIR/$checkpoint.actual-commit-scope"
  task5_write_checkpoint_scope "$checkpoint" "$expected_scope"
  task5_require_absent_path "$actual_scope"
  git -C "$repo_root" diff --cached --name-only --diff-filter=ACDMRTUXB | \
    sort -u > "$actual_scope"
  cmp -s "$expected_scope" "$actual_scope"
  subject="$(task5_checkpoint_subject "$checkpoint")"
  command_path="$TASK5_ACTION_DIR/$checkpoint.commit.command"
  stdout_path="$TASK5_ACTION_DIR/$checkpoint.commit.stdout"
  stderr_path="$TASK5_ACTION_DIR/$checkpoint.commit.stderr"
  status_path="$TASK5_ACTION_DIR/$checkpoint.commit.status"
  for output_path in "$command_path" "$stdout_path" "$stderr_path" "$status_path"; do
    task5_require_absent_path "$output_path"
  done
  printf '%q ' git -C "$repo_root" -c core.hooksPath=/dev/null \
    -c commit.gpgsign=false -c user.useConfigOnly=true -c user.name=jess \
    -c user.email=optimistindustries@gmail.com \
    commit --no-verify -m "$subject" > "$command_path"
  printf '\n' >> "$command_path"
  set +e
  git -C "$repo_root" -c core.hooksPath=/dev/null -c commit.gpgsign=false \
    -c user.useConfigOnly=true -c user.name=jess \
    -c user.email=optimistindustries@gmail.com \
    commit --no-verify -m "$subject" > "$stdout_path" 2> "$stderr_path"
  commit_status=$?
  set -e
  printf '%s\n' "$commit_status" > "$status_path"
  test "$commit_status" = 0
  commit_oid="$(git -C "$repo_root" rev-parse HEAD)"
  test "$(git -C "$repo_root" rev-list --parents -n 1 "$commit_oid")" = \
    "$commit_oid $parent_oid"
  test "$(git -C "$repo_root" rev-parse "$commit_oid^{tree}")" = "$expected_tree"
  test "$(git -C "$repo_root" show -s --format=%s "$commit_oid")" = "$subject"
  test "$(git -C "$repo_root" show -s --format=%an "$commit_oid")" = jess
  test "$(git -C "$repo_root" show -s --format=%ae "$commit_oid")" = \
    optimistindustries@gmail.com
  test "$(git -C "$repo_root" show -s --format=%cn "$commit_oid")" = jess
  test "$(git -C "$repo_root" show -s --format=%ce "$commit_oid")" = \
    optimistindustries@gmail.com
  git -C "$repo_root" diff --quiet
  git -C "$repo_root" diff --cached --quiet
  test -z "$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)"
  task5_create_alias "$evidence_root" "$checkpoint" "$commit_oid"
  task5_require_committed_checkpoint "$repo_root" "$evidence_root" "$checkpoint"
)

task5_require_minor_dispositions() (
  set -euo pipefail
  test "$#" = 1
  response_path="$1"
  task5_require_owned_regular "$response_path" 400
  verdict="$(grep '^VERDICT:' "$response_path")"
  test "$(grep -Ec '^VERDICT:' "$response_path")" = 1
  test "$(printf '%s\n' "$verdict" | grep -Ec \
    '^VERDICT: (APPROVE|REJECT) CRITICAL=[0-9]+ IMPORTANT=[0-9]+ MINOR=[0-9]+$')" = 1
  minor_count="$(printf '%s\n' "$verdict" | \
    sed -E 's/^.* MINOR=([0-9]+)$/\1/')"
  disposition_count="$(awk '/^MINOR-DISPOSITION: .+/ {n++} END {print n + 0}' \
    "$response_path")"
  disposition_prefix_count="$(awk '/^MINOR-DISPOSITION:/ {n++} END {print n + 0}' \
    "$response_path")"
  test "$disposition_prefix_count" = "$disposition_count"
  test "$disposition_count" = "$minor_count"
)

task5_require_hypothesis_disposition() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 2
  checkpoint="$1"
  response_path="$2"
  task5_require_owned_regular "$response_path" 400
  case "$checkpoint" in
    C53)
      expected_finding='FINDING-ID: C53-UNSERIALIZED-TERMINAL-HANDOFF' ;;
    C53C1)
      expected_finding='FINDING-ID: C53C1-STALE-QUEUED-ERROR-INDEX' ;;
    *) task5_fail "checkpoint has no qualified hypothesis" ;;
  esac
  test "$(grep -Fxc 'HYPOTHESIS-DISPOSITION: CONFIRMED' \
    "$response_path")" = 1
  test "$(grep -Fxc 'HYPOTHESIS-DISPOSITION: DISPUTED' \
    "$response_path")" = 0
  test "$(grep -Ec '^HYPOTHESIS-DISPOSITION:' "$response_path")" = 1
  test "$(grep -Fxc "$expected_finding" "$response_path")" = 1
  verdict="$(grep '^VERDICT:' "$response_path")"
  test "$(printf '%s\n' "$verdict" | grep -Ec \
    '^VERDICT: REJECT CRITICAL=[0-9]+ IMPORTANT=[0-9]+ MINOR=[0-9]+$')" = 1
  critical="$(printf '%s\n' "$verdict" | \
    sed -E 's/^.* CRITICAL=([0-9]+) .*$/\1/')"
  important="$(printf '%s\n' "$verdict" | \
    sed -E 's/^.* IMPORTANT=([0-9]+) .*$/\1/')"
  test "$((critical + important))" = 1
  task5_require_minor_dispositions "$response_path"
)

task5_require_accepted_review() (
  set -euo pipefail
  test "$#" = 3
  checkpoint="$1"
  lane="$2"
  response_path="$3"
  task5_require_review_target "$checkpoint"
  task5_require_review_lane "$lane"
  task5_require_owned_regular "$response_path" 400
  test "$(grep -Ec \
    '^VERDICT: APPROVE CRITICAL=0 IMPORTANT=0 MINOR=[0-9]+$' \
    "$response_path")" = 1
  task5_require_minor_dispositions "$response_path"
  if test "$checkpoint" = FINAL && test "$lane" = quality; then
    test "$(grep -Ec '^INDEPENDENT-MUTATION-AUDIT:' \
      "$response_path")" = 1
    test "$(grep -Fxc 'INDEPENDENT-MUTATION-AUDIT: PASS CANONICAL=28 KILLED=28 REJECTED=2 T5M28-PROOFS=2 RESTORATION=PASS SURVIVORS=0' \
      "$response_path")" = 1
  fi
)

task5_print_c53c2_review_scope() {
  test "$#" = 0
  printf '%s\n' \
    oracle/plugin/Core/PassiveDriver.cs \
    oracle/plugin/Core/PassiveDriverCompletion.cs \
    oracle/plugin/Core/PassiveDriverInput.cs \
    oracle/plugin/tests/PassiveDriverInputTests.cs \
    oracle/plugin/tests/PassiveDriverTerminalTests.cs \
    oracle/plugin/tests/PassiveDriverTestSupport.cs \
    oracle/plugin/tests/PassiveDriverTests.cs \
    oracle/plugin/tests/Program.cs
}

task5_print_final_review_scope() {
  test "$#" = 0
  printf '%s\n' \
    oracle/plugin/Core/PassiveDriver.cs \
    oracle/plugin/Core/PassiveDriverCompletion.cs \
    oracle/plugin/Core/PassiveDriverInput.cs \
    oracle/plugin/Core/PassiveDriverLifecycleHooks.cs \
    oracle/plugin/tests/PassiveDriverInputTests.cs \
    oracle/plugin/tests/PassiveDriverTerminalTests.cs \
    oracle/plugin/tests/PassiveDriverTestSupport.cs \
    oracle/plugin/tests/PassiveDriverTests.cs \
    oracle/plugin/tests/Program.cs
}

task5_require_sealed_review_pair() (
  set -euo pipefail
  test "$#" = 1
  checkpoint="$1"
  task5_require_review_target "$checkpoint"
  task5_require_owned_directory \
    "$TASK5_REVIEW_RESPONSES_ROOT/$checkpoint" 500
  package_root="$TASK5_REVIEW_PACKAGES_ROOT/$checkpoint"
  package_manifest="$package_root/manifest.sha256"
  task5_require_owned_directory "$package_root" 500
  task5_require_owned_regular "$package_manifest" 400
  test -z "$(find "$package_root" -type l -print)"
  test -z "$(find "$package_root" ! -type d ! -type f -print)"
  find "$package_root" -type d -print | while IFS= read -r package_dir; do
    task5_require_owned_directory "$package_dir" 500
  done
  package_entries=0
  while IFS='  ' read -r expected_sha relative_path; do
    task5_require_sha256 "$expected_sha"
    case "$relative_path" in
      /*|*..*) task5_fail "unsafe review-package manifest path" ;;
    esac
    package_file="$package_root/$relative_path"
    task5_require_owned_regular "$package_file" 400
    test "$(task5_sha256 "$package_file")" = "$expected_sha"
    package_entries=$((package_entries + 1))
  done < "$package_manifest"
  test "$package_entries" -gt 0
  test "$(find "$package_root" -type f | wc -l | tr -d '[:space:]')" = \
    "$((package_entries + 1))"
  metadata_path="$package_root/checkpoint.identity"
  scope_path="$package_root/scope.manifest"
  task5_require_owned_regular "$metadata_path" 400
  task5_require_owned_regular "$scope_path" 400
  test "$(wc -l < "$metadata_path" | tr -d '[:space:]')" = 14
  if test "$checkpoint" = FINAL; then
    expected_parent_checkpoint=P
    expected_parent="$(task5_resolve_alias "$TASK5_EVIDENCE_ROOT" P)"
    expected_range_checkpoint=P
    expected_range_parent="$expected_parent"
    expected_range_child_checkpoint=C53C2
    expected_child="$(task5_resolve_alias "$TASK5_EVIDENCE_ROOT" C53C2)"
    expected_child_tree="$(git -C "$TASK5_EXECUTION_ROOT" rev-parse \
      "$expected_child^{tree}")"
    expected_subject='FINAL-PACKAGE-FORMAT: task5-final-qualification-v1'
    test "$(task5_sha256 "$scope_path")" = \
      "$(task5_print_final_review_scope | shasum -a 256 | awk '{print $1}')"
  else
    expected_parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
    expected_parent="$(task5_resolve_alias \
      "$TASK5_EVIDENCE_ROOT" "$expected_parent_checkpoint")"
    expected_range_checkpoint="$expected_parent_checkpoint"
    expected_range_parent="$expected_parent"
    expected_range_child_checkpoint="$checkpoint"
    expected_subject="$(task5_checkpoint_subject "$checkpoint")"
  fi
  if test "$checkpoint" = C53C2; then
    expected_range_checkpoint=C52
    expected_range_parent="$(task5_resolve_alias "$TASK5_EVIDENCE_ROOT" C52)"
    test "$(task5_sha256 "$scope_path")" = \
      "$(task5_print_c53c2_review_scope | shasum -a 256 | awk '{print $1}')"
  fi
  if test "$checkpoint" = R; then
    expected_child=STAGED-R
    report_state="$TASK5_STATE_ROOT/R.report-staged"
    task5_require_owned_regular "$report_state" 400
    expected_child_tree="$(awk -F= '$1 == "index-tree" {print $2}' \
      "$report_state")"
  elif test "$checkpoint" != FINAL; then
    expected_child="$(task5_resolve_alias "$TASK5_EVIDENCE_ROOT" "$checkpoint")"
    expected_child_tree="$(git -C "$TASK5_EXECUTION_ROOT" rev-parse \
      "$expected_child^{tree}")"
  fi
  test "$(task5_receipt_value "$metadata_path" checkpoint)" = \
    "$checkpoint"
  test "$(task5_receipt_value "$metadata_path" parent-checkpoint)" = \
    "$expected_parent_checkpoint"
  test "$(task5_receipt_value "$metadata_path" parent)" = \
    "$expected_parent"
  test "$(task5_receipt_value "$metadata_path" range-parent-checkpoint)" = \
    "$expected_range_checkpoint"
  test "$(task5_receipt_value "$metadata_path" range-parent)" = \
    "$expected_range_parent"
  test "$(task5_receipt_value "$metadata_path" range-child-checkpoint)" = \
    "$expected_range_child_checkpoint"
  test "$(task5_receipt_value "$metadata_path" child)" = \
    "$expected_child"
  test "$(task5_receipt_value "$metadata_path" child-tree)" = \
    "$expected_child_tree"
  test "$(task5_receipt_value "$metadata_path" subject)" = \
    "$expected_subject"
  test "$(task5_receipt_value "$metadata_path" P)" = \
    "$TASK5_PLAN_COMMIT"
  test "$(task5_receipt_value "$metadata_path" \
    authority-bundle-manifest-sha256)" = "$TASK5_AUTHORITY_BUNDLE_SHA"
  implementation_actor_reference="$(task5_receipt_value "$metadata_path" \
    implementation-actor-reference)"
  spec_reviewer_reference="$(task5_receipt_value "$metadata_path" \
    spec-reviewer-reference)"
  quality_reviewer_reference="$(task5_receipt_value "$metadata_path" \
    quality-reviewer-reference)"
  test "$implementation_actor_reference" = \
    "$TASK5_IMPLEMENTATION_ACTOR_REFERENCE"
  task5_require_independent_reviewer_references \
    "$implementation_actor_reference" "$spec_reviewer_reference" \
    "$quality_reviewer_reference"
  task5_verify_manifest_root "$package_root/authority-bundle" \
    "$package_root/authority-bundle/manifest.sha256" \
    "$TASK5_AUTHORITY_BUNDLE_SHA"
  package_sha="$(task5_sha256 "$package_manifest")"
  for lane in spec quality; do
    response_path="$TASK5_REVIEW_RESPONSES_ROOT/$checkpoint/$lane.response.md"
    identity_path="$TASK5_REVIEW_RESPONSES_ROOT/$checkpoint/$lane.identity"
    task5_require_owned_regular "$response_path" 400
    task5_require_owned_regular "$identity_path" 400
    if test "$lane" = spec; then
      expected_reviewer_reference="$spec_reviewer_reference"
    else
      expected_reviewer_reference="$quality_reviewer_reference"
    fi
    test "$(grep -Fxc "PACKAGE-SHA256: $package_sha" \
      "$response_path")" = 1
    test "$(grep -Ec '^PACKAGE-SHA256:' "$response_path")" = 1
    test "$(grep -Fxc "REVIEWER-REFERENCE: $expected_reviewer_reference" \
      "$response_path")" = 1
    test "$(grep -Ec '^REVIEWER-REFERENCE:' "$response_path")" = 1
    test "$(grep -Fxc "IMPLEMENTATION-ACTOR-REFERENCE: $implementation_actor_reference" \
      "$response_path")" = 1
    test "$(grep -Ec '^IMPLEMENTATION-ACTOR-REFERENCE:' \
      "$response_path")" = 1
    test "$(wc -l < "$identity_path" | tr -d '[:space:]')" = 6
    test "$(task5_receipt_value "$identity_path" checkpoint)" = \
      "$checkpoint"
    test "$(task5_receipt_value "$identity_path" lane)" = "$lane"
    test "$(task5_receipt_value "$identity_path" package-sha256)" = \
      "$package_sha"
    test "$(task5_receipt_value "$identity_path" response-sha256)" = \
      "$(task5_sha256 "$response_path")"
    test "$(task5_receipt_value "$identity_path" reviewer-reference)" = \
      "$expected_reviewer_reference"
    test "$(task5_receipt_value "$identity_path" \
      implementation-actor-reference)" = "$implementation_actor_reference"
    if test "$checkpoint" = C53 || test "$checkpoint" = C53C1; then
      task5_require_hypothesis_disposition "$checkpoint" "$response_path"
    else
      task5_require_accepted_review "$checkpoint" "$lane" "$response_path"
    fi
  done
)

task5_freeze_review_package() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  checkpoint="$3"
  task5_require_review_target "$checkpoint"
  task5_require_authority_bundle
  implementation_actor_reference="$TASK5_IMPLEMENTATION_ACTOR_REFERENCE"
  spec_reviewer_reference="$(task5_read_review_assignment "$checkpoint" spec)"
  quality_reviewer_reference="$(task5_read_review_assignment \
    "$checkpoint" quality)"
  task5_require_independent_reviewer_references \
    "$implementation_actor_reference" "$spec_reviewer_reference" \
    "$quality_reviewer_reference"
  package_root="$TASK5_REVIEW_PACKAGES_ROOT/$checkpoint"
  task5_require_absent_path "$package_root"
  mkdir -m 700 "$package_root"
  task5_require_owned_directory "$package_root" 700
  metadata_path="$package_root/checkpoint.identity"
  patch_path="$package_root/change.patch"
  scope_path="$package_root/scope.manifest"
  ledger_copy="$package_root/commands"
  prior_reviews="$package_root/prior-reviews"
  prior_packages="$package_root/prior-packages"
  qualification_spec="$package_root/qualification.spec"
  authority_copy="$package_root/authority-bundle"
  manifest_path="$package_root/manifest.sha256"
  for output_path in "$metadata_path" "$patch_path" "$scope_path" \
      "$ledger_copy" "$prior_reviews" "$authority_copy" "$manifest_path"; do
    task5_require_absent_path "$output_path"
  done
  if test "$checkpoint" = FINAL; then
    task5_require_pre_report_completion 135
    for review_checkpoint in C51 C52 C53 C53C1 C53C2; do
      task5_require_sealed_review_pair "$review_checkpoint"
    done
    parent_checkpoint=P
    parent_oid="$(task5_resolve_alias "$evidence_root" P)"
    range_parent_checkpoint=P
    range_parent="$parent_oid"
    range_child_checkpoint=C53C2
    child_oid="$(task5_resolve_alias "$evidence_root" C53C2)"
    child_tree="$(git -C "$repo_root" rev-parse "$child_oid^{tree}")"
    package_subject='FINAL-PACKAGE-FORMAT: task5-final-qualification-v1'
    task5_require_committed_checkpoint "$repo_root" "$evidence_root" C53C2
    test "$(git -C "$repo_root" rev-parse HEAD)" = "$child_oid"
    git -C "$repo_root" diff --quiet
    git -C "$repo_root" diff --cached --quiet
    test -z "$(git -C "$repo_root" status --porcelain=v1 \
      --untracked-files=all)"
    git -C "$repo_root" diff --binary --full-index --no-ext-diff \
      "$range_parent" "$child_oid" -- > "$patch_path"
    task5_require_absent_path "$qualification_spec"
    printf '%s\n' \
      'FINAL-PACKAGE-FORMAT: task5-final-qualification-v1' \
      'range-parent-checkpoint=P' \
      'range-child-checkpoint=C53C2' \
      'required-final-matrix=1' \
      'required-stress=1' \
      'required-canonical-mutations=28' \
      'required-rejected-mutations=2' \
      'required-t5m28-proofs=2' \
      'required-task42-final-closure=1' \
      'required-restoration-evidence=1' \
      'required-killed-survivor-accounting=1' \
      "authority-bundle-manifest-sha256=$TASK5_AUTHORITY_BUNDLE_SHA" \
      > "$qualification_spec"
  else
    parent_checkpoint="$(task5_parent_checkpoint "$checkpoint")"
    parent_oid="$(task5_resolve_alias "$evidence_root" "$parent_checkpoint")"
    range_parent_checkpoint="$parent_checkpoint"
    range_parent="$parent_oid"
    range_child_checkpoint="$checkpoint"
    package_subject="$(task5_checkpoint_subject "$checkpoint")"
  fi
  if test "$checkpoint" = R; then
    task5_require_owned_regular "$TASK5_REPORT_GATES_ROOT/stage" 400
    report_state="$TASK5_STATE_ROOT/R.report-staged"
    task5_require_owned_regular "$report_state" 400
    child_oid=STAGED-R
    child_tree="$(git -C "$repo_root" write-tree)"
    test "$child_tree" = \
      "$(awk -F= '$1 == "index-tree" {print $2}' "$report_state")"
    test "$(git -C "$repo_root" rev-parse HEAD)" = "$parent_oid"
    git -C "$repo_root" diff --quiet
    test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
    test "$(git -C "$repo_root" diff --cached --name-only)" = \
      docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md
    git -C "$repo_root" diff --cached --binary --full-index --no-ext-diff \
      "$parent_oid^{tree}" -- > "$patch_path"
  elif test "$checkpoint" != FINAL; then
    child_oid="$(task5_resolve_alias "$evidence_root" "$checkpoint")"
    child_tree="$(git -C "$repo_root" rev-parse "$child_oid^{tree}")"
    task5_require_committed_checkpoint "$repo_root" "$evidence_root" "$checkpoint"
    task5_require_checkpoint_review_completion "$checkpoint"
    if test "$checkpoint" = C53C2; then
      range_parent_checkpoint=C52
      range_parent="$(task5_resolve_alias "$evidence_root" C52)"
    fi
    git -C "$repo_root" diff --binary --full-index --no-ext-diff \
      "$range_parent" "$child_oid" -- > "$patch_path"
  fi
  printf 'checkpoint=%s\nparent-checkpoint=%s\nparent=%s\nrange-parent-checkpoint=%s\nrange-parent=%s\nrange-child-checkpoint=%s\nchild=%s\nchild-tree=%s\nsubject=%s\nP=%s\nauthority-bundle-manifest-sha256=%s\nimplementation-actor-reference=%s\nspec-reviewer-reference=%s\nquality-reviewer-reference=%s\n' \
    "$checkpoint" "$parent_checkpoint" "$parent_oid" \
    "$range_parent_checkpoint" "$range_parent" "$range_child_checkpoint" \
    "$child_oid" "$child_tree" "$package_subject" \
    "$TASK5_PLAN_COMMIT" "$TASK5_AUTHORITY_BUNDLE_SHA" \
    "$implementation_actor_reference" "$spec_reviewer_reference" \
    "$quality_reviewer_reference" > "$metadata_path"
  test "$(wc -l < "$metadata_path" | tr -d '[:space:]')" = 14
  if test "$checkpoint" = FINAL; then
    task5_require_absent_path "$scope_path"
    git -C "$repo_root" diff --name-only "$range_parent" "$child_oid" -- | \
      LC_ALL=C sort -u > "$scope_path"
    test "$(task5_sha256 "$scope_path")" = \
      "$(task5_print_final_review_scope | shasum -a 256 | awk '{print $1}')"
  elif test "$checkpoint" = C53C2; then
    task5_require_absent_path "$scope_path"
    git -C "$repo_root" diff --name-only "$range_parent" "$child_oid" -- | \
      LC_ALL=C sort -u > "$scope_path"
    test "$(task5_sha256 "$scope_path")" = \
      "$(task5_print_c53c2_review_scope | shasum -a 256 | awk '{print $1}')"
  else
    task5_write_checkpoint_scope "$checkpoint" "$scope_path"
  fi
  mkdir -m 700 "$ledger_copy"
  for ledger_entry in "$TASK5_COMMANDS_ROOT"/[0-9][0-9][0-9][0-9][0-9][0-9]; do
    if test -f "$ledger_entry/manifest.sha256" && \
        test ! -L "$ledger_entry/manifest.sha256"; then
      cp -R -p "$ledger_entry" "$ledger_copy/${ledger_entry##*/}"
    fi
  done
  mkdir -m 700 "$prior_reviews"
  for review_checkpoint in C51 C52 C53 C53C1 C53C2 FINAL; do
    review_source="$TASK5_REVIEW_RESPONSES_ROOT/$review_checkpoint"
    if test -d "$review_source" && test ! -L "$review_source"; then
      task5_require_owned_directory "$review_source" 500
      cp -R -p "$review_source" \
        "$prior_reviews/${review_source##*/}"
    fi
  done
  if test "$checkpoint" = FINAL || test "$checkpoint" = R; then
    task5_require_absent_path "$prior_packages"
    mkdir -m 700 "$prior_packages"
    for review_checkpoint in C51 C52 C53 C53C1 C53C2 FINAL; do
      test "$review_checkpoint" = "$checkpoint" && continue
      package_source="$TASK5_REVIEW_PACKAGES_ROOT/$review_checkpoint"
      if test -d "$package_source" && test ! -L "$package_source"; then
        task5_require_owned_directory "$package_source" 500
        cp -R -p "$package_source" \
          "$prior_packages/${package_source##*/}"
      fi
    done
  fi
  cp -R -p "$TASK5_AUTHORITY_BUNDLE_ROOT" "$authority_copy"
  task5_verify_manifest_root "$authority_copy" \
    "$authority_copy/manifest.sha256" "$TASK5_AUTHORITY_BUNDLE_SHA"
  test -z "$(find "$package_root" -type l -print)"
  test -z "$(find "$package_root" ! -type d ! -type f -print)"
  : > "$manifest_path"
  find "$package_root" -type f ! -path "$manifest_path" -print | \
    LC_ALL=C sort | while IFS= read -r package_file; do
      package_relative="${package_file#"$package_root/"}"
      printf '%s  %s\n' "$(task5_sha256 "$package_file")" \
        "$package_relative" >> "$manifest_path"
    done
  test -s "$manifest_path"
  package_sha="$(task5_sha256 "$manifest_path")"
  find "$package_root" -type f -exec chmod 400 {} \;
  find "$package_root" -depth -type d -exec chmod 500 {} \;
  task5_require_owned_directory "$package_root" 500
  task5_require_owned_regular "$manifest_path" 400
  printf '%s package=%s manifest-sha256=%s\n' \
    "$checkpoint" "$package_root" "$package_sha"
)

task5_seal_review_response() (
  set -euo pipefail
  umask 077
  test "$#" = 5
  checkpoint="$1"
  lane="$2"
  response_sha="$3"
  packages_root="$4"
  inbox_root="$5"
  task5_require_review_target "$checkpoint"
  task5_require_review_lane "$lane"
  task5_require_sha256 "$response_sha"
  test "$packages_root" = "$TASK5_REVIEW_PACKAGES_ROOT"
  test "$inbox_root" = "$TASK5_REVIEW_INBOX_ROOT"
  package_manifest="$packages_root/$checkpoint/manifest.sha256"
  package_identity="$packages_root/$checkpoint/checkpoint.identity"
  task5_require_owned_regular "$package_manifest" 400
  task5_require_owned_regular "$package_identity" 400
  package_sha="$(task5_sha256 "$package_manifest")"
  implementation_actor_reference="$(task5_receipt_value "$package_identity" \
    implementation-actor-reference)"
  spec_reviewer_reference="$(task5_receipt_value "$package_identity" \
    spec-reviewer-reference)"
  quality_reviewer_reference="$(task5_receipt_value "$package_identity" \
    quality-reviewer-reference)"
  test "$implementation_actor_reference" = \
    "$TASK5_IMPLEMENTATION_ACTOR_REFERENCE"
  task5_require_independent_reviewer_references \
    "$implementation_actor_reference" "$spec_reviewer_reference" \
    "$quality_reviewer_reference"
  if test "$lane" = spec; then
    reviewer_reference="$spec_reviewer_reference"
  else
    reviewer_reference="$quality_reviewer_reference"
  fi
  pending_path="$inbox_root/$checkpoint.$lane.pending.md"
  task5_require_owned_regular "$pending_path"
  test "$(task5_sha256 "$pending_path")" = "$response_sha"
  test "$(grep -Fxc "PACKAGE-SHA256: $package_sha" "$pending_path")" = 1
  test "$(grep -Ec '^PACKAGE-SHA256:' "$pending_path")" = 1
  test "$(grep -Fxc "REVIEWER-REFERENCE: $reviewer_reference" \
    "$pending_path")" = 1
  test "$(grep -Ec '^REVIEWER-REFERENCE:' "$pending_path")" = 1
  test "$(grep -Fxc "IMPLEMENTATION-ACTOR-REFERENCE: $implementation_actor_reference" \
    "$pending_path")" = 1
  test "$(grep -Ec '^IMPLEMENTATION-ACTOR-REFERENCE:' "$pending_path")" = 1
  test "$(grep -Ec '^VERDICT:' "$pending_path")" = 1
  test "$(grep -Ec '^VERDICT: (APPROVE|REJECT) CRITICAL=[0-9]+ IMPORTANT=[0-9]+ MINOR=[0-9]+$' \
    "$pending_path")" = 1
  response_dir="$TASK5_REVIEW_RESPONSES_ROOT/$checkpoint"
  if test ! -e "$response_dir" && test ! -L "$response_dir"; then
    mkdir -m 700 "$response_dir"
  fi
  task5_require_owned_directory "$response_dir" 700
  sealed_path="$response_dir/$lane.response.md"
  identity_path="$response_dir/$lane.identity"
  task5_require_absent_path "$sealed_path"
  task5_require_absent_path "$identity_path"
  /bin/cat "$pending_path" > "$sealed_path"
  cmp -s "$pending_path" "$sealed_path"
  test "$(task5_sha256 "$sealed_path")" = "$response_sha"
  printf 'checkpoint=%s\nlane=%s\npackage-sha256=%s\nresponse-sha256=%s\nreviewer-reference=%s\nimplementation-actor-reference=%s\n' \
    "$checkpoint" "$lane" "$package_sha" "$response_sha" \
    "$reviewer_reference" "$implementation_actor_reference" > "$identity_path"
  chmod 400 "$sealed_path" "$identity_path"
  task5_require_owned_regular "$sealed_path" 400
  task5_require_owned_regular "$identity_path" 400
  other_lane=spec
  if test "$lane" = spec; then
    other_lane=quality
  fi
  if test -f "$response_dir/$other_lane.response.md" && \
      test ! -L "$response_dir/$other_lane.response.md"; then
    task5_require_owned_regular "$response_dir/$other_lane.response.md" 400
    task5_require_owned_regular "$response_dir/$other_lane.identity" 400
    chmod 500 "$response_dir"
    task5_require_owned_directory "$response_dir" 500
  fi
  printf '%s %s response=%s package=%s\n' \
    "$checkpoint" "$lane" "$response_sha" "$package_sha"
)

task5_match_ledger_argument() {
  test "$#" = 2
  expected_argument="$1"
  actual_argument="$2"
  case "$expected_argument" in
    ABSENT) test -z "$actual_argument" ;;
    SHA256)
      case "$actual_argument" in
        ????????????????????????????????????????????????????????????????) ;;
        *) return 1 ;;
      esac
      case "$actual_argument" in
        *[!0123456789abcdef]*) return 1 ;;
      esac ;;
    *) test "$actual_argument" = "$expected_argument" ;;
  esac
}

task5_require_ledger_action_count() (
  set -euo pipefail
  test "$#" = 6
  expected_count="$1"
  expected_action="$2"
  expected_arity="$3"
  expected_arg1="$4"
  expected_arg2="$5"
  expected_arg3="$6"
  case "$expected_count:$expected_arity" in
    *[!0123456789:]*|*:*:*) task5_fail "invalid ledger count/arity" ;;
  esac
  actual_count=0
  for entry in "$TASK5_COMMANDS_ROOT"/[0-9][0-9][0-9][0-9][0-9][0-9]; do
    manifest="$entry/manifest.sha256"
    if test ! -f "$manifest" || test -L "$manifest"; then
      continue
    fi
    task5_require_owned_directory "$entry" 500
    task5_require_owned_regular "$manifest" 400
    test -z "$(find "$entry" -type l -print)"
    test -z "$(find "$entry" ! -type d ! -type f -print)"
    manifest_entries=0
    while IFS='  ' read -r manifest_sha manifest_relative; do
      task5_require_sha256 "$manifest_sha"
      case "$manifest_relative" in
        /*|*..*) task5_fail "unsafe command-ledger manifest path" ;;
      esac
      manifest_file="$entry/$manifest_relative"
      task5_require_owned_regular "$manifest_file" 400
      test "$(task5_sha256 "$manifest_file")" = "$manifest_sha"
      manifest_entries=$((manifest_entries + 1))
    done < "$manifest"
    test "$(find "$entry" -type f | wc -l | tr -d '[:space:]')" = \
      "$((manifest_entries + 1))"
    find "$entry" -type d -print | while IFS= read -r entry_dir; do
      task5_require_owned_directory "$entry_dir" 500
    done
    argv_path="$entry/argv.q"
    task5_require_owned_regular "$argv_path" 400
    argv_manifest_sha="$(awk '$2 == "argv.q" {print $1}' "$manifest")"
    task5_require_sha256 "$argv_manifest_sha"
    test "$(task5_sha256 "$argv_path")" = "$argv_manifest_sha"
    task5_require_owned_regular "$entry/exit" 400
    test "$(cat "$entry/exit")" = 0
    find "$entry" -type f \
      \( -name 'argv.q' -o -name '*.command' -o -name '*.commands' \) \
      -print | while IFS= read -r command_record; do
        if grep -E '(^|[[:space:]])(curl|wget|git[[:space:]]+(fetch|pull)|dotnet[[:space:]]+restore|Steam|Unity|Mono|BepInEx)([[:space:]]|$)|https?://|ssh://|git@' \
            "$command_record" >/dev/null; then
          task5_fail "forbidden command appears before report authorization"
        fi
      done
    set -- $(cat "$argv_path")
    test "${1-}" = /bin/bash
    test "${2-}" = --noprofile
    test "${3-}" = --norc
    test "${4-}" = "$TASK5_DRIVER_PATH"
    actual_action="${5-}"
    actual_arity=$(( $# - 5 ))
    actual_arg1="${6-}"
    actual_arg2="${7-}"
    actual_arg3="${8-}"
    if test "$actual_action" = "$expected_action" && \
        test "$actual_arity" = "$expected_arity" && \
        task5_match_ledger_argument "$expected_arg1" "$actual_arg1" && \
        task5_match_ledger_argument "$expected_arg2" "$actual_arg2" && \
        task5_match_ledger_argument "$expected_arg3" "$actual_arg3"; then
      actual_count=$((actual_count + 1))
    fi
  done
  test "$actual_count" = "$expected_count"
)

task5_require_finalized_ledger_count() (
  set -euo pipefail
  test "$#" = 1
  expected_count="$1"
  actual_count=0
  for entry in "$TASK5_COMMANDS_ROOT"/[0-9][0-9][0-9][0-9][0-9][0-9]; do
    if test -f "$entry/manifest.sha256" && \
        test ! -L "$entry/manifest.sha256"; then
      actual_count=$((actual_count + 1))
    fi
  done
  test "$actual_count" = "$expected_count"
)

task5_sequence_normalize_argument() {
  test "$#" = 1
  sequence_argument="$1"
  if test -z "$sequence_argument"; then
    printf '%s\n' ABSENT
    return
  fi
  case "$sequence_argument" in
    ????????????????????????????????????????????????????????????????)
      case "$sequence_argument" in
        *[!0123456789abcdef]*) ;;
        *) printf '%s\n' SHA256; return ;;
      esac ;;
  esac
  printf '%s\n' "$sequence_argument"
}

task5_sequence_emit() {
  test "$#" = 4
  sequence_action="$1"
  sequence_arg1="$2"
  sequence_arg2="$3"
  sequence_arg3="$4"
  sequence_arity=0
  test "$sequence_arg1" = ABSENT || sequence_arity=1
  test "$sequence_arg2" = ABSENT || sequence_arity=2
  test "$sequence_arg3" = ABSENT || sequence_arity=3
  printf '%06d|%s|%s|%s|%s|%s\n' \
    "$TASK5_SEQUENCE_ORDINAL" "$sequence_action" "$sequence_arity" \
    "$sequence_arg1" "$sequence_arg2" "$sequence_arg3" \
    >> "$TASK5_SEQUENCE_EXPECTED"
  TASK5_SEQUENCE_ORDINAL=$((TASK5_SEQUENCE_ORDINAL + 1))
}

task5_sequence_emit_matrix() {
  test "$#" = 2
  sequence_checkpoint="$1"
  sequence_state="$2"
  task5_sequence_emit force-net10 "$sequence_checkpoint" \
    "$sequence_state" ABSENT
  case "$sequence_checkpoint:$sequence_state" in
    P:clean)
      task5_sequence_emit focused-csharp P clean driver-initial ;;
    C51:green-staged|C52:green-staged)
      task5_sequence_emit focused-csharp "$sequence_checkpoint" \
        green-staged driver-input
      task5_sequence_emit focused-csharp "$sequence_checkpoint" \
        green-staged driver-initial ;;
    C53:green-staged|C53C1:green-staged|C53C2:green-staged|\
    C53C2:committed)
      task5_sequence_emit focused-csharp "$sequence_checkpoint" \
        "$sequence_state" driver-initial
      task5_sequence_emit focused-csharp "$sequence_checkpoint" \
        "$sequence_state" driver-input
      task5_sequence_emit focused-csharp "$sequence_checkpoint" \
        "$sequence_state" driver-terminal ;;
    *) task5_fail "expected matrix sequence is outside the closed set" ;;
  esac
  task5_sequence_emit full-csharp "$sequence_checkpoint" \
    "$sequence_state" ABSENT
  task5_sequence_emit force-net35 "$sequence_checkpoint" \
    "$sequence_state" ABSENT
  task5_sequence_emit full-python "$sequence_checkpoint" \
    "$sequence_state" ABSENT
}

task5_sequence_emit_checkpoint() {
  test "$#" = 1
  sequence_checkpoint="$1"
  case "$sequence_checkpoint" in
    C51|C52) sequence_red=compiler-red ;;
    C53|C53C1|C53C2) sequence_red=behavioral-red ;;
    *) task5_fail "expected checkpoint sequence is outside implementation" ;;
  esac
  task5_sequence_emit stage-plan-patch "$sequence_checkpoint" tests ABSENT
  task5_sequence_emit authenticate-state "$sequence_checkpoint" \
    tests-staged ABSENT
  task5_sequence_emit "$sequence_red" "$sequence_checkpoint" ABSENT ABSENT
  task5_sequence_emit stage-plan-patch "$sequence_checkpoint" \
    production ABSENT
  task5_sequence_emit authenticate-state "$sequence_checkpoint" \
    green-staged ABSENT
  task5_sequence_emit_matrix "$sequence_checkpoint" green-staged
  task5_sequence_emit commit-checkpoint "$sequence_checkpoint" ABSENT ABSENT
  task5_sequence_emit authenticate-state "$sequence_checkpoint" committed ABSENT
  if test "$sequence_checkpoint" = C53C1; then
    task5_sequence_emit stress C53C1 postcommit ABSENT
  fi
  if test "$sequence_checkpoint" = C53C2; then
    task5_sequence_emit stress C53C2 postcommit ABSENT
    task5_sequence_emit t5m28-proof C53C2 C53C2-T5M28-proof ABSENT
  fi
  task5_sequence_emit freeze-review-package "$sequence_checkpoint" ABSENT ABSENT
  task5_sequence_emit seal-review-response "$sequence_checkpoint" spec SHA256
  task5_sequence_emit seal-review-response "$sequence_checkpoint" quality SHA256
}

task5_write_expected_ledger_sequence() (
  set -euo pipefail
  test "$#" = 2
  expected_path="$1"
  expected_phase="$2"
  case "$expected_phase" in
    pre-final|pre-report|post-report) ;;
    *) task5_fail "expected ledger phase is outside the closed set" ;;
  esac
  task5_require_absent_path "$expected_path"
  : > "$expected_path"
  TASK5_SEQUENCE_EXPECTED="$expected_path"
  TASK5_SEQUENCE_ORDINAL=1
  task5_sequence_emit plan-postcommit SHA256 SHA256 SHA256
  task5_sequence_emit task42-closure initial ABSENT ABSENT
  task5_sequence_emit preflight ABSENT ABSENT ABSENT
  task5_sequence_emit authenticate-state P clean ABSENT
  task5_sequence_emit_matrix P clean
  for sequence_checkpoint in C51 C52 C53 C53C1 C53C2; do
    task5_sequence_emit_checkpoint "$sequence_checkpoint"
  done
  task5_sequence_emit_matrix C53C2 committed
  task5_sequence_emit stress C53C2 task4 ABSENT
  for sequence_mutation in $(task5_canonical_mutation_ids); do
    task5_sequence_emit canonical-mutation C53C2 \
      "$sequence_mutation" ABSENT
  done
  task5_sequence_emit rejected-mutation C53C2 T5M20 ABSENT
  task5_sequence_emit rejected-mutation C53C2 T5M23 ABSENT
  task5_sequence_emit t5m28-proof C53C2 Task4-T5M28-replay ABSENT
  task5_sequence_emit task42-closure final ABSENT ABSENT
  test "$((TASK5_SEQUENCE_ORDINAL - 1))" = 135
  if test "$expected_phase" != pre-final; then
    task5_sequence_emit freeze-review-package FINAL ABSENT ABSENT
    task5_sequence_emit seal-review-response FINAL spec SHA256
    task5_sequence_emit seal-review-response FINAL quality SHA256
    test "$((TASK5_SEQUENCE_ORDINAL - 1))" = 138
  fi
  if test "$expected_phase" = post-report; then
    task5_sequence_emit report-gate authorize ABSENT ABSENT
    task5_sequence_emit report-gate candidate ABSENT ABSENT
    task5_sequence_emit report-gate stage ABSENT ABSENT
    task5_sequence_emit freeze-review-package R ABSENT ABSENT
    task5_sequence_emit seal-review-response R spec SHA256
    task5_sequence_emit seal-review-response R quality SHA256
    task5_sequence_emit report-gate reviewed ABSENT ABSENT
    task5_sequence_emit commit-checkpoint R ABSENT ABSENT
    task5_sequence_emit authenticate-state R committed ABSENT
    test "$((TASK5_SEQUENCE_ORDINAL - 1))" = 147
  fi
  task5_require_owned_regular "$expected_path"
)

task5_write_actual_ledger_sequence() (
  set -euo pipefail
  test "$#" = 1
  actual_path="$1"
  task5_require_absent_path "$actual_path"
  : > "$actual_path"
  for entry in "$TASK5_COMMANDS_ROOT"/[0-9][0-9][0-9][0-9][0-9][0-9]; do
    manifest="$entry/manifest.sha256"
    if test ! -f "$manifest" || test -L "$manifest"; then
      continue
    fi
    task5_require_owned_directory "$entry" 500
    task5_require_owned_regular "$manifest" 400
    argv_path="$entry/argv.q"
    task5_require_owned_regular "$argv_path" 400
    argv_manifest_sha="$(awk '$2 == "argv.q" {print $1}' "$manifest")"
    task5_require_sha256 "$argv_manifest_sha"
    test "$(task5_sha256 "$argv_path")" = "$argv_manifest_sha"
    task5_require_owned_regular "$entry/exit" 400
    test "$(cat "$entry/exit")" = 0
    set -- $(cat "$argv_path")
    test "${1-}" = /bin/bash
    test "${2-}" = --noprofile
    test "${3-}" = --norc
    test "${4-}" = "$TASK5_DRIVER_PATH"
    shift 4
    actual_action="${1-}"
    test -n "$actual_action"
    shift
    actual_arity="$#"
    test "$actual_arity" -le 3
    actual_arg1="$(task5_sequence_normalize_argument "${1-}")"
    actual_arg2="$(task5_sequence_normalize_argument "${2-}")"
    actual_arg3="$(task5_sequence_normalize_argument "${3-}")"
    printf '%s|%s|%s|%s|%s|%s\n' "${entry##*/}" "$actual_action" \
      "$actual_arity" "$actual_arg1" "$actual_arg2" "$actual_arg3" \
      >> "$actual_path"
  done
  task5_require_owned_regular "$actual_path"
)

task5_require_ledger_sequence() (
  set -euo pipefail
  test "$#" = 1
  sequence_phase="$1"
  expected_path="$TASK5_ACTION_DIR/$sequence_phase.expected-sequence"
  actual_path="$TASK5_ACTION_DIR/$sequence_phase.actual-sequence"
  task5_write_expected_ledger_sequence "$expected_path" "$sequence_phase"
  task5_write_actual_ledger_sequence "$actual_path"
  cmp -s "$expected_path" "$actual_path"
)

task5_require_matrix_ledger() (
  set -euo pipefail
  test "$#" = 2
  checkpoint="$1"
  state="$2"
  case "$checkpoint:$state" in
    P:clean) input_count=0; terminal_count=0 ;;
    C51:green-staged|C52:green-staged)
      input_count=1; terminal_count=0 ;;
    C53:green-staged|C53C1:green-staged|C53C2:green-staged|\
    C53C2:committed)
      input_count=1; terminal_count=1 ;;
    *) task5_fail "matrix ledger checkpoint/state pair is not authorized" ;;
  esac
  task5_require_ledger_action_count 1 force-net10 2 \
    "$checkpoint" "$state" ABSENT
  task5_require_ledger_action_count 1 force-net35 2 \
    "$checkpoint" "$state" ABSENT
  task5_require_ledger_action_count 1 full-csharp 2 \
    "$checkpoint" "$state" ABSENT
  task5_require_ledger_action_count 1 full-python 2 \
    "$checkpoint" "$state" ABSENT
  task5_require_ledger_action_count 1 focused-csharp 3 \
    "$checkpoint" "$state" driver-initial
  task5_require_ledger_action_count "$input_count" focused-csharp 3 \
    "$checkpoint" "$state" driver-input
  task5_require_ledger_action_count "$terminal_count" focused-csharp 3 \
    "$checkpoint" "$state" driver-terminal
)

task5_require_checkpoint_review_completion() (
  set -euo pipefail
  test "$#" = 1
  checkpoint="$1"
  case "$checkpoint" in
    C51)
      red_action=compiler-red ;;
    C52)
      red_action=compiler-red ;;
    C53)
      red_action=behavioral-red ;;
    C53C1)
      red_action=behavioral-red ;;
    C53C2)
      red_action=behavioral-red ;;
    *) task5_fail "review completion checkpoint is outside implementation" ;;
  esac
  task5_require_owned_regular "$TASK5_STATE_ROOT/$checkpoint.committed" 400
  task5_require_ledger_action_count 1 stage-plan-patch 2 \
    "$checkpoint" tests ABSENT
  task5_require_ledger_action_count 1 authenticate-state 2 \
    "$checkpoint" tests-staged ABSENT
  task5_require_ledger_action_count 1 "$red_action" 1 \
    "$checkpoint" ABSENT ABSENT
  task5_require_ledger_action_count 1 stage-plan-patch 2 \
    "$checkpoint" production ABSENT
  task5_require_ledger_action_count 1 authenticate-state 2 \
    "$checkpoint" green-staged ABSENT
  task5_require_ledger_action_count 1 commit-checkpoint 1 \
    "$checkpoint" ABSENT ABSENT
  task5_require_ledger_action_count 1 authenticate-state 2 \
    "$checkpoint" committed ABSENT
  task5_require_matrix_ledger "$checkpoint" green-staged
  if test "$checkpoint" = C53C1; then
    task5_require_ledger_action_count 1 stress 2 C53C1 postcommit ABSENT
  fi
  if test "$checkpoint" = C53C2; then
    task5_require_ledger_action_count 1 stress 2 C53C2 postcommit ABSENT
    task5_require_ledger_action_count 1 t5m28-proof 2 C53C2 \
      C53C2-T5M28-proof ABSENT
  fi
)

task5_require_pre_report_completion() (
  set -euo pipefail
  test "$#" = 1
  task5_require_finalized_ledger_count "$1"
  case "$1" in
    135) task5_require_ledger_sequence pre-final ;;
    138) task5_require_ledger_sequence pre-report ;;
    147) task5_require_ledger_sequence post-report ;;
    *) task5_fail "pre-report ledger cardinality is unauthorized" ;;
  esac
  task5_require_ledger_action_count 1 plan-postcommit 3 SHA256 SHA256 SHA256
  task5_require_ledger_action_count 1 preflight 0 ABSENT ABSENT ABSENT
  task5_require_ledger_action_count 1 task42-closure 1 initial ABSENT ABSENT
  task5_require_ledger_action_count 1 task42-closure 1 final ABSENT ABSENT
  task5_require_ledger_action_count 1 authenticate-state 2 P clean ABSENT
  task5_require_matrix_ledger P clean
  for checkpoint in C51 C52 C53 C53C1 C53C2; do
    task5_require_ledger_action_count 1 stage-plan-patch 2 \
      "$checkpoint" tests ABSENT
    task5_require_ledger_action_count 1 authenticate-state 2 \
      "$checkpoint" tests-staged ABSENT
    task5_require_ledger_action_count 1 stage-plan-patch 2 \
      "$checkpoint" production ABSENT
    task5_require_ledger_action_count 1 authenticate-state 2 \
      "$checkpoint" green-staged ABSENT
    task5_require_ledger_action_count 1 commit-checkpoint 1 \
      "$checkpoint" ABSENT ABSENT
    task5_require_ledger_action_count 1 authenticate-state 2 \
      "$checkpoint" committed ABSENT
    task5_require_ledger_action_count 1 freeze-review-package 1 \
      "$checkpoint" ABSENT ABSENT
    task5_require_ledger_action_count 1 seal-review-response 3 \
      "$checkpoint" spec SHA256
    task5_require_ledger_action_count 1 seal-review-response 3 \
      "$checkpoint" quality SHA256
    task5_require_matrix_ledger "$checkpoint" green-staged
  done
  task5_require_matrix_ledger C53C2 committed
  task5_require_ledger_action_count 1 compiler-red 1 C51 ABSENT ABSENT
  task5_require_ledger_action_count 1 compiler-red 1 C52 ABSENT ABSENT
  task5_require_ledger_action_count 1 behavioral-red 1 C53 ABSENT ABSENT
  task5_require_ledger_action_count 1 behavioral-red 1 C53C1 ABSENT ABSENT
  task5_require_ledger_action_count 1 behavioral-red 1 C53C2 ABSENT ABSENT
  task5_require_ledger_action_count 1 stress 2 C53C1 postcommit ABSENT
  task5_require_ledger_action_count 1 stress 2 C53C2 postcommit ABSENT
  task5_require_ledger_action_count 1 stress 2 C53C2 task4 ABSENT
  task5_require_ledger_action_count 1 t5m28-proof 2 C53C2 \
    C53C2-T5M28-proof ABSENT
  task5_require_ledger_action_count 1 t5m28-proof 2 C53C2 \
    Task4-T5M28-replay ABSENT
  for mutation_id in $(task5_canonical_mutation_ids); do
    task5_require_ledger_action_count 1 canonical-mutation 2 \
      C53C2 "$mutation_id" ABSENT
  done
  task5_require_ledger_action_count 1 rejected-mutation 2 \
    C53C2 T5M20 ABSENT
  task5_require_ledger_action_count 1 rejected-mutation 2 \
    C53C2 T5M23 ABSENT
  if test "$1" = 138 || test "$1" = 147; then
    task5_require_ledger_action_count 1 freeze-review-package 1 \
      FINAL ABSENT ABSENT
    task5_require_ledger_action_count 1 seal-review-response 3 \
      FINAL spec SHA256
    task5_require_ledger_action_count 1 seal-review-response 3 \
      FINAL quality SHA256
  fi
)

task5_require_post_report_completion() (
  set -euo pipefail
  task5_require_pre_report_completion 147
  for gate in authorize candidate stage reviewed; do
    task5_require_ledger_action_count 1 report-gate 1 "$gate" ABSENT ABSENT
  done
  task5_require_ledger_action_count 1 freeze-review-package 1 R ABSENT ABSENT
  task5_require_ledger_action_count 1 seal-review-response 3 R spec SHA256
  task5_require_ledger_action_count 1 seal-review-response 3 R quality SHA256
  task5_require_ledger_action_count 1 commit-checkpoint 1 R ABSENT ABSENT
  task5_require_ledger_action_count 1 authenticate-state 2 R committed ABSENT
)

task5_require_report_review_record_file() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 1 || return 1
  record_path="$1"
  task5_require_owned_regular "$record_path" 400 || return 1
  task5_require_no_nul_file "$record_path" || return 1
  test "$(wc -l < "$record_path" | tr -d '[:space:]')" = 14 || \
    return 1
  review_record_count=0
  while IFS=' ' read -r review_record_label review_checkpoint_field \
      review_lane_field review_package_field review_response_field \
      review_bytes_field review_actor_field review_reviewer_field \
      review_verdict_field review_minor_field review_hex_field \
      review_extra_field; do
    test "$review_record_label" = REVIEW-RESPONSE-HEX || return 1
    test -z "$review_extra_field" || return 1
    review_checkpoint_value="${review_checkpoint_field#checkpoint=}"
    review_lane_value="${review_lane_field#lane=}"
    review_package_value="${review_package_field#package-sha256=}"
    review_response_value="${review_response_field#response-sha256=}"
    review_bytes_value="${review_bytes_field#response-bytes=}"
    review_actor_value="${review_actor_field#implementation-actor-reference=}"
    review_reviewer_value="${review_reviewer_field#reviewer-reference=}"
    review_verdict_value="${review_verdict_field#verdict-hex=}"
    review_minor_value="${review_minor_field#minor-count=}"
    review_hex_value="${review_hex_field#response-hex=}"
    test "$review_checkpoint_field" = \
      "checkpoint=$review_checkpoint_value" || return 1
    test "$review_lane_field" = "lane=$review_lane_value" || return 1
    test "$review_package_field" = \
      "package-sha256=$review_package_value" || return 1
    test "$review_response_field" = \
      "response-sha256=$review_response_value" || return 1
    test "$review_bytes_field" = \
      "response-bytes=$review_bytes_value" || return 1
    test "$review_actor_field" = \
      "implementation-actor-reference=$review_actor_value" || return 1
    test "$review_reviewer_field" = \
      "reviewer-reference=$review_reviewer_value" || return 1
    test "$review_verdict_field" = \
      "verdict-hex=$review_verdict_value" || return 1
    test "$review_minor_field" = \
      "minor-count=$review_minor_value" || return 1
    test "$review_hex_field" = "response-hex=$review_hex_value" || return 1
    case "$review_checkpoint_value" in
      P|C51|C52|C53|C53C1|C53C2|FINAL) ;;
      *) return 1 ;;
    esac
    case "$review_lane_value" in
      spec|quality) ;;
      *) return 1 ;;
    esac
    task5_require_sha256 "$review_package_value" || return 1
    task5_require_sha256 "$review_response_value" || return 1
    case "$review_bytes_value" in
      ''|*[!0123456789]*) return 1 ;;
    esac
    case "$review_minor_value" in
      ''|*[!0123456789]*) return 1 ;;
    esac
    test "$review_bytes_value" -gt 0 || return 1
    task5_require_coordination_reference "$review_actor_value" || return 1
    task5_require_coordination_reference "$review_reviewer_value" || return 1
    case "$review_verdict_value" in
      ''|*[!0123456789abcdef]*) return 1 ;;
    esac
    case "$review_hex_value" in
      ''|*[!0123456789abcdef]*) return 1 ;;
    esac
    test "${#review_hex_value}" = "$((review_bytes_value * 2))" || \
      return 1
    review_record_count=$((review_record_count + 1))
  done < "$record_path"
  test "$review_record_count" = 14 || return 1
  for review_checkpoint_value in P C51 C52 C53 C53C1 C53C2 FINAL; do
    for review_lane_value in spec quality; do
      test "$(grep -Ec "^REVIEW-RESPONSE-HEX checkpoint=$review_checkpoint_value lane=$review_lane_value " \
        "$record_path")" = 1 || return 1
    done
  done
)

task5_write_report_review_records() (
  set -euo pipefail
  export LC_ALL=C
  umask 077
  test "$#" = 1
  output_path="$1"
  task5_require_absent_path "$output_path"
  task5_require_authority_bundle
  review_record_count=0
  {
    for review_checkpoint in P C51 C52 C53 C53C1 C53C2 FINAL; do
      if test "$review_checkpoint" != P; then
        task5_require_sealed_review_pair "$review_checkpoint"
      fi
      for review_lane in spec quality; do
        if test "$review_checkpoint" = P; then
          review_receipt="$TASK5_AUTHORITY_BUNDLE_ROOT/authority.receipt"
          review_package_sha="$(task5_receipt_value \
            "$review_receipt" review-package-sha256)"
          review_response="$TASK5_AUTHORITY_BUNDLE_ROOT/P.$review_lane.response.md"
          review_identity="$TASK5_AUTHORITY_BUNDLE_ROOT/P.$review_lane.identity"
        else
          review_package_manifest="$TASK5_REVIEW_PACKAGES_ROOT/$review_checkpoint/manifest.sha256"
          review_response="$TASK5_REVIEW_RESPONSES_ROOT/$review_checkpoint/$review_lane.response.md"
          review_identity="$TASK5_REVIEW_RESPONSES_ROOT/$review_checkpoint/$review_lane.identity"
          task5_require_owned_regular "$review_package_manifest" 400
          review_package_sha="$(task5_sha256 "$review_package_manifest")"
        fi
        task5_require_owned_regular "$review_response" 400
        task5_require_owned_regular "$review_identity" 400
        review_response_sha="$(task5_sha256 "$review_response")"
        review_response_bytes="$(wc -c < "$review_response" | \
          tr -d '[:space:]')"
        case "$review_response_bytes" in
          ''|*[!0123456789]*) task5_fail "review response byte count is invalid" ;;
        esac
        test "$review_response_bytes" -gt 0
        review_actor_reference="$(task5_receipt_value "$review_identity" \
          implementation-actor-reference)"
        review_reviewer_reference="$(task5_receipt_value "$review_identity" \
          reviewer-reference)"
        test "$review_actor_reference" = "$TASK5_IMPLEMENTATION_ACTOR_REFERENCE"
        task5_require_coordination_reference "$review_actor_reference"
        task5_require_coordination_reference "$review_reviewer_reference"
        review_verdict="$(grep '^VERDICT:' "$review_response")"
        test "$(grep -Ec '^VERDICT:' "$review_response")" = 1
        test "$(printf '%s\n' "$review_verdict" | grep -Ec \
          '^VERDICT: (APPROVE|REJECT) CRITICAL=[0-9]+ IMPORTANT=[0-9]+ MINOR=[0-9]+$')" = 1
        review_minor_count="$(printf '%s\n' "$review_verdict" | \
          sed -E 's/^.* MINOR=([0-9]+)$/\1/')"
        case "$review_minor_count" in
          ''|*[!0123456789]*) task5_fail "review Minor count is invalid" ;;
        esac
        review_verdict_hex="$(printf '%s' "$review_verdict" | \
          od -An -tx1 -v | tr -d '[:space:]')"
        review_response_hex="$(od -An -tx1 -v "$review_response" | \
          tr -d '[:space:]')"
        test "${#review_response_hex}" = \
          "$((review_response_bytes * 2))"
        case "$review_verdict_hex$review_response_hex" in
          ''|*[!0123456789abcdef]*) \
            task5_fail "review response hex is not lowercase hexadecimal" ;;
        esac
        printf 'REVIEW-RESPONSE-HEX checkpoint=%s lane=%s package-sha256=%s response-sha256=%s response-bytes=%s implementation-actor-reference=%s reviewer-reference=%s verdict-hex=%s minor-count=%s response-hex=%s\n' \
          "$review_checkpoint" "$review_lane" "$review_package_sha" \
          "$review_response_sha" "$review_response_bytes" \
          "$review_actor_reference" "$review_reviewer_reference" \
          "$review_verdict_hex" "$review_minor_count" \
          "$review_response_hex"
        review_record_count=$((review_record_count + 1))
      done
    done
  } > "$output_path"
  test "$review_record_count" = 14
  test "$(wc -l < "$output_path" | tr -d '[:space:]')" = 14
  chmod 400 "$output_path"
  task5_require_owned_regular "$output_path" 400
  task5_require_report_review_record_file "$output_path"
)

task5_require_report_review_records() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 1 || return 1
  report_path="$1"
  expected_path="$TASK5_REPORT_GATES_ROOT/review-records.expected"
  authorize_path="$TASK5_REPORT_GATES_ROOT/authorize"
  task5_require_owned_regular "$report_path" || return 1
  task5_require_owned_regular "$expected_path" 400 || return 1
  task5_require_owned_regular "$authorize_path" 400 || return 1
  task5_require_report_review_record_file "$expected_path" || return 1
  test "$(task5_sha256 "$expected_path")" = \
    "$(task5_receipt_value "$authorize_path" \
      review-records-sha256)" || return 1
  derived_path="$TASK5_ACTION_DIR/report-review-records.derived"
  task5_require_absent_path "$derived_path" || return 1
  task5_write_report_review_records "$derived_path"
  cmp -s "$expected_path" "$derived_path" || return 1
  review_records_begin='<!-- TASK5-REPORT-REVIEW-RECORDS-BEGIN -->'
  review_records_end='<!-- TASK5-REPORT-REVIEW-RECORDS-END -->'
  test "$(grep -Fxc "$review_records_begin" "$report_path")" = 1 || \
    return 1
  test "$(grep -Fxc "$review_records_end" "$report_path")" = 1 || \
    return 1
  actual_path="$TASK5_ACTION_DIR/report-review-records.actual"
  task5_require_absent_path "$actual_path" || return 1
  awk -v first="$review_records_begin" -v last="$review_records_end" '
    $0 == first {inside=1; next}
    $0 == last {inside=0; exit}
    inside {print}
  ' "$report_path" > "$actual_path"
  chmod 400 "$actual_path"
  task5_require_owned_regular "$actual_path" 400 || return 1
  task5_require_report_review_record_file "$actual_path" || return 1
  cmp -s "$expected_path" "$actual_path" || return 1
)

task5_require_report_noncircularity() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 1 || return 1
  report_path="$1"
  task5_require_owned_regular "$report_path" || return 1
  task5_require_no_nul_file "$report_path" || return 1
  test "$(grep -Fxc 'P-THROUGH-FINAL-REVIEWS: recorded' \
    "$report_path")" = 1 || return 1
  test "$(grep -Fxc 'R-SELF-REVIEW: excluded-from-tracked-report' \
    "$report_path")" = 1 || return 1
  test "$(awk '
    $0 == "R-SELF-REVIEW: excluded-from-tracked-report" {next}
    {
      lower = tolower($0)
      if (lower ~ /(^|[^a-z0-9])r([^a-z0-9]|$)/) {
        n++
      }
    }
    END {print n + 0}
  ' "$report_path")" = 0 || return 1
)

task5_report_gate() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 3
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  gate="$3"
  report_path=docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md
  absolute_report="$repo_root/$report_path"
  case "$gate" in
    authorize|candidate|stage|reviewed) ;;
    *) task5_fail "report gate is outside the closed enum" ;;
  esac
  gate_path="$TASK5_REPORT_GATES_ROOT/$gate"
  review_records_path="$TASK5_REPORT_GATES_ROOT/review-records.expected"
  task5_require_absent_path "$gate_path"
  C53C2="$(task5_resolve_alias "$evidence_root" C53C2)"
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$C53C2"
  case "$gate" in
    authorize)
      task5_require_sealed_review_pair C53C2
      task5_require_sealed_review_pair FINAL
      task5_require_pre_report_completion 138
      task5_write_report_review_records "$review_records_path"
      git -C "$repo_root" diff --quiet
      git -C "$repo_root" diff --cached --quiet
      test -z "$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)"
      task5_require_absent_path "$absolute_report" ;;
    candidate)
      task5_require_owned_regular "$TASK5_REPORT_GATES_ROOT/authorize" 400
      task5_require_report_noncircularity "$absolute_report"
      task5_require_report_review_records "$absolute_report"
      task5_authenticate_state "$repo_root" "$evidence_root" R report-candidate ;;
    stage)
      task5_require_owned_regular "$TASK5_REPORT_GATES_ROOT/candidate" 400
      candidate_state="$TASK5_STATE_ROOT/R.report-candidate"
      task5_require_owned_regular "$candidate_state" 400
      task5_require_owned_regular "$absolute_report"
      task5_require_report_noncircularity "$absolute_report"
      task5_require_report_review_records "$absolute_report"
      test "$(task5_receipt_value "$TASK5_REPORT_GATES_ROOT/candidate" \
        review-records-sha256)" = "$(task5_sha256 "$review_records_path")"
      test "$(task5_sha256 "$absolute_report")" = \
        "$(awk -F= '$1 == "report-sha256" {print $2}' \
          "$TASK5_REPORT_GATES_ROOT/candidate")"
      test "$(awk -F= '$1 == "status-sha256" {print $2}' "$candidate_state")" = \
        "$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all | \
          shasum -a 256 | awk '{print $1}')"
      git -C "$repo_root" add -- "$report_path"
      task5_authenticate_state "$repo_root" "$evidence_root" R report-staged ;;
    reviewed)
      task5_require_owned_regular "$TASK5_REPORT_GATES_ROOT/stage" 400
      task5_require_sealed_review_pair R
      task5_require_report_noncircularity "$absolute_report"
      task5_require_report_review_records "$absolute_report"
      test "$(task5_receipt_value "$TASK5_REPORT_GATES_ROOT/stage" \
        review-records-sha256)" = "$(task5_sha256 "$review_records_path")"
      report_state="$TASK5_STATE_ROOT/R.report-staged"
      task5_require_owned_regular "$report_state" 400
      git -C "$repo_root" diff --quiet
      test -z "$(git -C "$repo_root" ls-files --others --exclude-standard)"
      test "$(git -C "$repo_root" diff --cached --name-only)" = "$report_path"
      test "$(git -C "$repo_root" write-tree)" = \
        "$(awk -F= '$1 == "index-tree" {print $2}' "$report_state")"
      package_root="$TASK5_REVIEW_PACKAGES_ROOT/R"
      task5_require_owned_regular "$package_root/checkpoint.identity" 400
      task5_require_owned_regular "$package_root/change.patch" 400
      task5_require_owned_regular "$package_root/scope.manifest" 400
      test "$(cat "$package_root/scope.manifest")" = "$report_path"
      test "$(awk -F= '$1 == "child-tree" {print $2}' \
        "$package_root/checkpoint.identity")" = \
        "$(git -C "$repo_root" write-tree)"
      test "$(git -C "$repo_root" diff --cached --binary --full-index \
        --no-ext-diff "$C53C2^{tree}" -- | shasum -a 256 | \
        awk '{print $1}')" = \
        "$(task5_sha256 "$package_root/change.patch")"
      test "$(awk -F= '$1 == "report-sha256" {print $2}' \
        "$TASK5_REPORT_GATES_ROOT/stage")" = \
        "$(task5_sha256 "$absolute_report")" ;;
  esac
  task5_require_owned_regular "$review_records_path" 400
  review_records_sha="$(task5_sha256 "$review_records_path")"
  if test "$gate" != authorize; then
    test "$review_records_sha" = "$(task5_receipt_value \
      "$TASK5_REPORT_GATES_ROOT/authorize" review-records-sha256)"
  fi
  printf 'gate=%s\nHEAD=%s\nindex-tree=%s\nreport-sha256=%s\nreview-records-sha256=%s\n' \
    "$gate" "$(git -C "$repo_root" rev-parse HEAD)" \
    "$(git -C "$repo_root" write-tree)" \
    "$(if test -f "$absolute_report" && test ! -L "$absolute_report"; then \
      task5_sha256 "$absolute_report"; else printf '%s' ABSENT; fi)" \
    "$review_records_sha" > "$gate_path"
  chmod 400 "$gate_path"
  task5_require_owned_regular "$gate_path" 400
  cat "$gate_path"
)

task5_final_audit() (
  set -euo pipefail
  export LC_ALL=C
  test "$#" = 2
  repo_root="$(task5_physical_repo_root "$1")"
  evidence_root="$2"
  task5_require_evidence_root "$evidence_root"
  task5_require_authority_bundle
  task5_require_post_report_completion
  task5_authenticate_s4_d_pins "$repo_root"
  task5_require_report_noncircularity \
    "$repo_root/docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md"
  task5_require_report_review_records \
    "$repo_root/docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md"
  test "$(git -C "$repo_root" rev-parse \
    9f69d2c40406461a28f018290d579cf313f22287^{tree})" = \
    a691afd8ae55f3676bcf1ffe0f6ef3b15b1d2feb
  test "$(git -C "$repo_root" rev-list --parents -n 1 \
    9f69d2c40406461a28f018290d579cf313f22287)" = \
    '9f69d2c40406461a28f018290d579cf313f22287 f5de26f3dea85f14f25e3540da9f29130e27a09b'
  previous=9f69d2c40406461a28f018290d579cf313f22287
  for checkpoint in P C51 C52 C53 C53C1 C53C2 R; do
    current="$(task5_resolve_alias "$evidence_root" "$checkpoint")"
    test "$(git -C "$repo_root" rev-list --parents -n 1 "$current")" = \
      "$current $previous"
    task5_require_committed_checkpoint "$repo_root" "$evidence_root" "$checkpoint"
    previous="$current"
  done
  for checkpoint in C51 C52 C53 C53C1 C53C2 FINAL R; do
    task5_require_sealed_review_pair "$checkpoint"
  done
  test "$(git -C "$repo_root" rev-parse HEAD)" = "$previous"
  test -z "$(git -C "$repo_root" status --porcelain=v1 --untracked-files=all)"
  task5_require_owned_regular "$TASK5_STATE_ROOT/task42-initial.path" 600
  initial_dir="$(cat "$TASK5_STATE_ROOT/task42-initial.path")"
  task5_require_owned_directory "$initial_dir" 500
  final_count="$(find "$TASK5_COMMANDS_ROOT" -path '*/artifacts/task42-final' \
    -type d -print | wc -l | tr -d '[:space:]')"
  test "$final_count" = 1
  prior_entries=0
  for entry in "$TASK5_COMMANDS_ROOT"/[0-9][0-9][0-9][0-9][0-9][0-9]; do
    if test "$entry" = "${TASK5_ACTION_DIR%/artifacts}"; then
      continue
    fi
    task5_require_owned_directory "$entry" 500
    manifest="$entry/manifest.sha256"
    task5_require_owned_regular "$manifest" 400
    while IFS='  ' read -r expected_sha relative_path; do
      case "$relative_path" in
        /*|*..*) task5_fail "unsafe command-ledger manifest path" ;;
      esac
      task5_require_owned_regular "$entry/$relative_path" 400
      test "$(task5_sha256 "$entry/$relative_path")" = "$expected_sha"
    done < "$manifest"
    test "$(task5_receipt_value "$entry/controller.identity" \
      implementation-actor-reference)" = \
      "$TASK5_IMPLEMENTATION_ACTOR_REFERENCE"
    test "$(cat "$entry/exit")" = 0
    find "$entry" -type f \
      \( -name 'argv.q' -o -name '*.command' -o -name '*.commands' \) \
      -print | while IFS= read -r command_record; do
        if grep -E '(^|[[:space:]])(curl|wget|git[[:space:]]+(fetch|pull)|dotnet[[:space:]]+restore|Steam|Unity|Mono|BepInEx)([[:space:]]|$)|https?://|ssh://|git@' \
            "$command_record" >/dev/null; then
          task5_fail "forbidden command appears in authenticated ledger"
        fi
      done
    prior_entries=$((prior_entries + 1))
  done
  test "$prior_entries" -gt 0
  printf 'final-audit=PASS HEAD=%s prior-command-entries=%s\n' \
    "$previous" "$prior_entries"
)

task5_dispatch() {
  set -euo pipefail
  test "$#" -ge 1
  TASK5_ACTION="$1"
  shift
  TASK5_ARGUMENT_COUNT="$#"
  TASK5_ARG1="${1-}"
  TASK5_ARG2="${2-}"
  TASK5_ARG3="${3-}"
  readonly TASK5_ACTION TASK5_ARGUMENT_COUNT
  readonly TASK5_ARG1 TASK5_ARG2 TASK5_ARG3
  readonly TASK5_CLEAN_CONTROLLER TASK5_EXECUTION_ROOT TASK5_EVIDENCE_ROOT
  readonly TASK5_PLAN_COMMIT TASK5_PLAN_PATH TASK5_P_ALIAS
  readonly TASK5_DRIVER_PATH TASK5_DRIVER_SHA
  readonly TASK5_COMMANDS_ROOT TASK5_ACTION_DIR
  readonly TASK5_PLAN_AUDITOR_PATH TASK5_PLAN_AUDITOR_SHA
  readonly TASK5_BOOTSTRAP_SHA
  readonly TASK5_CANONICAL_MUTATION_MANIFEST_SHA
  readonly TASK5_AUTHORITY_BUNDLE_ROOT TASK5_AUTHORITY_BUNDLE_SHA
  readonly TASK5_IMPLEMENTATION_ACTOR_REFERENCE
  readonly TASK5_REVIEW_PACKAGES_ROOT TASK5_REVIEW_INBOX_ROOT
  readonly TASK5_REVIEW_RESPONSES_ROOT TASK5_STATE_ROOT
  readonly TASK5_REPORT_GATES_ROOT
  readonly TASK5_EXPECTED_BRANCH TASK5_EXPECTED_PARENT TASK5_EXPECTED_SUBJECT
  task5_require_execution_identity
  case "$TASK5_ACTION" in
    preflight)
      test "$TASK5_ARGUMENT_COUNT" = 0
      task5_run_preflight \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" ;;
    plan-postcommit)
      test "$TASK5_ARGUMENT_COUNT" = 3
      task5_run_plan_postcommit \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" "$TASK5_ARG3" ;;
    stage-plan-patch)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_stage_checkpoint_patch \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    authenticate-state)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_authenticate_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    commit-checkpoint)
      test "$TASK5_ARGUMENT_COUNT" = 1
      task5_commit_checkpoint \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" "$TASK5_ARG1" ;;
    freeze-review-package)
      test "$TASK5_ARGUMENT_COUNT" = 1
      task5_freeze_review_package \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" "$TASK5_ARG1" ;;
    seal-review-response)
      test "$TASK5_ARGUMENT_COUNT" = 3
      task5_seal_review_response \
        "$TASK5_ARG1" "$TASK5_ARG2" "$TASK5_ARG3" \
        "$TASK5_REVIEW_PACKAGES_ROOT" "$TASK5_REVIEW_INBOX_ROOT" ;;
    report-gate)
      test "$TASK5_ARGUMENT_COUNT" = 1
      task5_report_gate \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" "$TASK5_ARG1" ;;
    final-audit)
      test "$TASK5_ARGUMENT_COUNT" = 0
      task5_final_audit "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" ;;
    compiler-red)
      test "$TASK5_ARGUMENT_COUNT" = 1
      task5_run_compiler_red \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" "$TASK5_ARG1" ;;
    behavioral-red)
      test "$TASK5_ARGUMENT_COUNT" = 1
      task5_run_behavioral_red \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" "$TASK5_ARG1" ;;
    task42-closure)
      test "$TASK5_ARGUMENT_COUNT" = 1
      task5_verify_task42_ignored_closure \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" "$TASK5_ARG1" ;;
    force-net10)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2"
      task5_force_net10 "$TASK5_EXECUTION_ROOT"
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    force-net35)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2"
      task5_force_net35 "$TASK5_EXECUTION_ROOT"
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    focused-csharp)
      test "$TASK5_ARGUMENT_COUNT" = 3
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2"
      task5_run_focused_csharp "$TASK5_EXECUTION_ROOT" "$TASK5_ARG3"
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    full-csharp)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2"
      task5_run_full_csharp "$TASK5_EXECUTION_ROOT"
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    full-python)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2"
      task5_run_full_python "$TASK5_EXECUTION_ROOT"
      task5_require_matrix_state \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    stress)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_stress_task5_cohorts \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    canonical-mutation)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_run_canonical_mutation \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    rejected-mutation)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_run_rejected_mutation \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    t5m28-proof)
      test "$TASK5_ARGUMENT_COUNT" = 2
      task5_run_t5m28_proof \
        "$TASK5_EXECUTION_ROOT" "$TASK5_EVIDENCE_ROOT" \
        "$TASK5_ARG1" "$TASK5_ARG2" ;;
    *) task5_fail "dispatcher action is not allowlisted: $TASK5_ACTION" ;;
  esac
}

task5_dispatch "$@"
```
<!-- TASK5-RUNTIME-END -->

The Task 4.2 closure deliberately authenticates six anchors and four frozen
namespaces only. For each round, its manifest consists of the top-level
regular, non-symlink `task-4.2-correction-rXX-*` files plus that round's exact
`task-4.2-review-correction-rXX-brief.md`, rendered as C-sorted
`SHA256  basename` lines. No gate counts all files in the physical evidence root, because unrelated
descendants and future Task 5 namespaces make a physical-total gate unsound. It authenticates but never executes
`task-4.2-forced-suite.sh` or any old terminal verifier; the pinned Task 5
functions are the executable gates.

Overall execution initializes one evidence root once, repeats the committed-P
audit, and records the `initial` Task 4.2 closure. Each implementation slice
uses only closed dispatcher actions: authenticate the current state; stage the
internally mapped tests patch; authenticate `tests-staged`; run the declared
RED action; stage the internally mapped production patch; authenticate
`green-staged`; run the exact GREEN matrix; commit through
`commit-checkpoint`; authenticate `committed`; freeze one immutable review
package; and seal both responses from their fixed pending paths. Task 4 alone
records the `final` Task 4.2 closure and compares it to `initial`. After each of
C53C1 and C53C2, `task5_clean_call stress C53C1 postcommit` and
`task5_clean_call stress C53C2 postcommit`, respectively, record exactly 20 terminal runs
in fresh action-owned directories. The authenticated primary Task 5 worktree
is never a mutation clone. Every canonical, rejected, and T5M28 transaction
creates its own no-hardlink local clone internally. Full Python and both
T5M28 parser proofs always use the pinned interpreter and source in the
primary worktree with explicit primary `PYTHONPATH` and `UV_OFFLINE=1`.

Every baseline/GREEN matrix action carries its exact checkpoint and state as
dispatcher arguments and authenticates that immutable state seal before and
after the command. The final `C53C2 committed` matrix, Task 4 stress/proof,
mutation transactions, and final Task 4.2 closure additionally require the
exact sealed corrected-5.3 response pair and its reviewer-derived transition
validation. Before R is authorized, the controller
compares the exact ordinal action/arity/argument sequence, not only cumulative
counts.

Every checkpoint commit from C51 through R uses that same closed Git author
and committer identity via internally mapped `-c` arguments; the preflight and
postcommit checks authenticate it even though the controller suppresses all
global Git configuration.

## Traceability

| Requirement | Owning task/gate |
|---|---|
| direction/native-poll correlation and exact raw mapping | Task 1; six `driver-input` registrations |
| Undo/Restore attribution and typed throw cleanup | Task 1 |
| real-callback NotInspected correction; no private manufactured seam | Task 1 plus `driver-initial` regression |
| stable object-reference identity, neutral/candidate reset, Step durability | Task 1 and T5M01-T5M17 |
| Restart depth before fault; nested suppression; LIFO cleanup | Task 2 |
| actual post-StateSet identity and pre/post-initial replacement policy | Task 2 |
| third Step -> End -> Close -> Complete and final UTC | Task 3 |
| shared terminal owner and output serialization | Task 3C1 and T5M18-T5M27 |
| stale deferred Error parser position | Task 3C2, T5M28, and Python stale-trace proof |
| net10 behavior and net35 source compatibility | Common gates after every GREEN |
| sealed Task 4.2 regression | `driver-initial`, pin checks, ignored-evidence closure |
| full Python protocol compatibility | Common Python gate and T5M28 reader proof |
| immutable append-only review history | Tasks 1-4 and correction protocol |
| concise reproducible evidence | Task 4 report requirements |
| no game/network/Task 6 work | Global constraints and final scope audit |

## Task 0: Authenticate P and Close the Task 4.2 Boundary

**Files:**

- Read-only: every pin and ignored artifact named above
- Create outside repository: one Task 5 evidence root under `/private/tmp`
- Modify: none

**Interfaces:**

- Consumes: exact S4, D, the materialized P commit, and the sealed Task 4.2 evidence.
- Produces: authenticated alias map for S4/D/P, initial ignored-evidence closure snapshot, pristine baseline hashes, and captured command/tool identities used by every later task.

- [ ] **Entry gate: Confirm explicit implementation approval**

Require that P has already been committed and reviewed, and that the user subsequently gave explicit approval to execute this implementation plan. Record that approval reference externally. If it is absent or predates the final reviewed P, stop before creating evidence or running any command below.

In one dedicated Apple Bash 3.2 shell, run the bootstrap fence exactly once.
Its first controller action must be `task5_clean_call plan-postcommit` followed
by exactly the recorded candidate `plan-sha256`, `checker-sha256`, and authority-
bundle `manifest.sha256` lowercase 64-character literals, in that order. Do not
assign or infer any value from the now-committed worktree. Require the action's
committed-mode identities and sealed authority receipt to equal the precommit
and non-shell approval records before continuing. The checker executed by
`plan-postcommit` begins through the same literal minimal `env -i` process-start
boundary as both preapproval modes; inheriting the controller's larger clean
environment is not equivalent.

- [ ] **Step 1: Authenticate the existing isolated execution checkout**

Remain in the current already-isolated Task 5 worktree; do not create a second worktree. Require HEAD=P, exact sole parent D, exact P subject, and exact one-file P scope. Require D's exact sole parent S4, subjects/scopes above, and the exact S4/D trees. If the current checkout is no longer the isolated Task 5 worktree, stop instead of falling back to the real worktree.

- [ ] **Step 2: Authenticate every immutable tracked pin and future-file absence**

Recompute SHA-256, blob, lines, and bytes for the pin table. Require all six future production/test files to be absent at D. Require `PassiveDriverBoundaries.cs`, both csproj files, and the Python reader/tests to match before continuing.

- [ ] **Step 3: Close Task 4.2 ignored evidence read-only**

Perform the exact closure procedure above, record aggregate results externally, and prove the closure command itself made no file change. Do not run the Task 4.2 helper.

Invoke `task5_clean_call task42-closure initial` exactly once; preserve its
fresh `task42-initial` snapshot directory for the final comparison.

- [ ] **Step 4: Authenticate tools and offline environment**

Run the pinned tool preflight in `/usr/bin/env -i` with the global environment. Syntax-check any generated Task 5 shell driver with `/bin/bash --noprofile --norc -n` before execution. Reject Bash 4 syntax and any network/restore/game command string.

```bash
task5_clean_call preflight
```

- [ ] **Step 5: Run the clean baseline matrix**

Authenticate clean P before the matrix. Run forced net10 build,
`driver-initial`, full C# harness, forced net35 build, and the pinned Python
suite. Every bound action re-authenticates the same P-clean seal before and
after execution, so the final Python action supplies the closing clean-P
check.

```bash
task5_clean_call authenticate-state P clean
task5_clean_call force-net10 P clean
task5_clean_call focused-csharp P clean driver-initial
task5_clean_call full-csharp P clean
task5_clean_call force-net35 P clean
task5_clean_call full-python P clean
```

- [ ] **Step 6: Record the baseline externally**

Record commands, exits, stdout/stderr hashes, P-resolved ID/tree, tool versions, and initial closure aggregate in the Task 5 evidence root. Do not create a repository ledger or commit.

## Task 1: Commit C51 — Attribute Manual Attempts and Emit Steps

**Files:**

- Modify: `oracle/plugin/Core/PassiveDriver.cs`
- Create: `oracle/plugin/Core/PassiveDriverInput.cs`
- Create: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTestSupport.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**

- Consumes: P and the inherited Task 4.2 phase/update boundary.
- Produces: the Task 5.1 interfaces and semantics defined above, exactly six input registrations, every Step write, and intermediate Ready markers.

- [ ] **Step 1: Authenticate P and materialize the C51 tests-only patch**

Require a clean P. Extract the exact committed C51 test block into external evidence, authenticate it, apply it once with the required `git apply --check --index` / `git apply --index` protocol, and prove cached-diff byte equality. Production must remain byte-identical to P.

```bash
task5_clean_call stage-plan-patch C51 tests
task5_clean_call authenticate-state C51 tests-staged
```

- [ ] **Step 2: Run and authenticate the C51 compiler RED**

Run the forced net10 build once. Require the declared nonzero status and exact missing-member diagnostic multiset, with no unrelated diagnostics. Do not run tests after a compile RED.

```bash
task5_clean_call compiler-red C51
```

- [ ] **Step 3: Apply the C51 production patch**

Extract and authenticate the committed production block, apply it once to the tests-only tree with the index protocol, and prove cached-diff equality plus the declared result hashes/tree. Implement one pending attempt, exact cardinal/Undo correlation, real-callback settling, stable reference identity, bounded captures, Step-before-Ready ordering, and typed throw cleanup. Do not add Restart, StateSet, stored expected count, terminal completion, or output-lease serialization.

```bash
task5_clean_call stage-plan-patch C51 production
task5_clean_call authenticate-state C51 green-staged
```

- [ ] **Step 4: Run C51 GREEN gates**

Run forced net10 build, `driver-input`, `driver-initial`, full C# harness, forced net35 build, and pinned Python. Require six input registrations and all inherited registrations exactly.

```bash
task5_clean_call force-net10 C51 green-staged
task5_clean_call focused-csharp C51 green-staged driver-input
task5_clean_call focused-csharp C51 green-staged driver-initial
task5_clean_call full-csharp C51 green-staged
task5_clean_call force-net35 C51 green-staged
task5_clean_call full-python C51 green-staged
```

- [ ] **Step 5: Commit and authenticate C51**

Commit with exact subject `feat: attribute passive input attempts`. Require sole parent P and exact five-file scope. Resolve C51 externally; record commit/tree/file hashes and clean status.

```bash
task5_clean_call commit-checkpoint C51
task5_clean_call authenticate-state C51 committed
```

- [ ] **Step 6: Review immutable P..C51**

Create one exact immutable review package and dispatch separate specification/protocol and quality reviews. Require no Critical or Important finding before Task 2. Record review identities, complete verdicts, and package hash externally.

Run `task5_clean_call freeze-review-package C51`. Dispatch its fixed immutable
package through the non-shell review channel. Each reviewer writes only the
fixed `C51.spec.pending.md` or `C51.quality.pending.md` inbox path and returns
that file's exact lowercase SHA-256 through the same channel. For each lane,
invoke `task5_clean_call seal-review-response C51 spec` or
`task5_clean_call seal-review-response C51 quality`, appending the returned
SHA-256 literal as the final argument. Both sealed approvals are prerequisites
to staging C52.

## Task 2: Commit C52 — Balance Restart and State Replacement

**Files:**

- Modify: `oracle/plugin/Core/PassiveDriver.cs`
- Modify: `oracle/plugin/Core/PassiveDriverInput.cs`
- Create: `oracle/plugin/Core/PassiveDriverLifecycleHooks.cs`
- Modify: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**

- Consumes: exact C51 and all six C51 input registrations.
- Produces: Restart/StateSet/ClearThrew interfaces, two appended registrations, lifecycle balancing, and state-replacement behavior. It still does not store expected count, hand off UTC into Step completion, write End, or call Complete.

- [ ] **Step 1: Authenticate C51 and apply the C52 tests-only patch**

Require exact clean C51 and its accepted immutable reviews. Extract/authenticate/apply the committed tests block once with the index protocol and prove cached-diff equality. Require production hashes remain exactly C51.

```bash
task5_clean_call stage-plan-patch C52 tests
task5_clean_call authenticate-state C52 tests-staged
```

- [ ] **Step 2: Run and authenticate the C52 compiler RED**

Run one forced net10 build. Require only the declared lifecycle missing-member set and exact nonzero status. No test run follows a compile RED.

```bash
task5_clean_call compiler-red C52
```

- [ ] **Step 3: Apply the C52 production patch**

Extract/authenticate/apply only the committed production block with the index protocol. Implement Restart depth before fault, recursive/nested bookkeeping, LIFO cleanup, actual post-StateSet identity, pre-initial epoch rules, post-initial `state_replaced`, and complete kind-dispatched throw cleanup; prove cached-diff equality and authenticate its output tree.

```bash
task5_clean_call stage-plan-patch C52 production
task5_clean_call authenticate-state C52 green-staged
```

- [ ] **Step 4: Run C52 GREEN gates**

Run forced net10 build, `driver-input`, `driver-initial`, full C# harness, forced net35 build, and pinned Python. Require exactly eight input registrations in frozen order.

```bash
task5_clean_call force-net10 C52 green-staged
task5_clean_call focused-csharp C52 green-staged driver-input
task5_clean_call focused-csharp C52 green-staged driver-initial
task5_clean_call full-csharp C52 green-staged
task5_clean_call force-net35 C52 green-staged
task5_clean_call full-python C52 green-staged
```

- [ ] **Step 5: Commit and authenticate C52**

Commit with exact subject `feat: balance passive lifecycle hooks`. Require sole parent C51 and exact five-file scope. Resolve C52 externally and prove clean status.

```bash
task5_clean_call commit-checkpoint C52
task5_clean_call authenticate-state C52 committed
```

- [ ] **Step 6: Review immutable C51..C52**

Create exact specification/protocol and quality review packages. Require no Critical or Important finding before Task 3; record review identities/verdicts/package hashes externally.

Run `task5_clean_call freeze-review-package C52`, dispatch that fixed immutable
package non-shell, and have the two reviewers write only the fixed
`C52.spec.pending.md` and `C52.quality.pending.md` inbox paths. Invoke
`task5_clean_call seal-review-response C52 spec` and
`task5_clean_call seal-review-response C52 quality`, appending the exact
lowercase response SHA-256 returned by the corresponding non-shell handoff.
Both sealed approvals are prerequisites to staging C53.

## Task 3: Commit C53 — Finalize Successful Completion

**Files:**

- Modify: `oracle/plugin/Core/PassiveDriver.cs`
- Create: `oracle/plugin/Core/PassiveDriverCompletion.cs`
- Modify: `oracle/plugin/Core/PassiveDriverInput.cs`
- Modify narrowly: `oracle/plugin/tests/PassiveDriverInputTests.cs`
- Create: `oracle/plugin/tests/PassiveDriverTerminalTests.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTestSupport.cs`
- Create: `oracle/plugin/tests/PassiveDriverTests.cs`
- Modify: `oracle/plugin/tests/Program.cs`

**Interfaces:**

- Consumes: exact C52, every Step owned by 5.1, lifecycle behavior owned by 5.2, and the constructor's existing expected-count validation.
- Produces: stored expected count, final observation UTC handoff, Step-2 terminal branch, End/Close/Complete, six terminal registrations, and the final aggregator.

- [ ] **Step 1: Authenticate C52 and apply the C53 tests-only patch**

Extract/authenticate/apply the committed tests/support/aggregator block with the index protocol. Prove cached-diff equality and that `PassiveDriverInputTests.cs` differs only by the authorized intermediate-only Ready amendment. Production remains exactly C52.

```bash
task5_clean_call stage-plan-patch C53 tests
task5_clean_call authenticate-state C53 tests-staged
```

- [ ] **Step 2: Run and authenticate the C53 behavioral RED**

Force-build successfully, then run only `driver-terminal` without rebuilding. Require status `1` and the exact first failure from the patch catalog. Reject any earlier registration/failure.

```bash
task5_clean_call behavioral-red C53
```

- [ ] **Step 3: Apply the C53 production patch**

Extract/authenticate/apply only the committed production block with the index protocol. Store only the already validated expected count, thread validated UTC to settled emission, and implement Step 2 -> End -> Close -> Complete. Preserve 5.1 Step ownership and 5.2 lifecycle ownership; prove cached-diff equality and authenticate every result file and tree.

```bash
task5_clean_call stage-plan-patch C53 production
task5_clean_call authenticate-state C53 green-staged
```

- [ ] **Step 4: Run C53 GREEN gates**

Run forced net10 build, all three driver cohorts, full C# harness, forced net35 build, and pinned Python. Require 39 total frozen registrations and exact successful harness stdout.

```bash
task5_clean_call force-net10 C53 green-staged
task5_clean_call focused-csharp C53 green-staged driver-initial
task5_clean_call focused-csharp C53 green-staged driver-input
task5_clean_call focused-csharp C53 green-staged driver-terminal
task5_clean_call full-csharp C53 green-staged
task5_clean_call force-net35 C53 green-staged
task5_clean_call full-python C53 green-staged
```

- [ ] **Step 5: Commit and authenticate C53**

Commit with exact subject `feat: finalize passive trace capture`. Require sole parent C52 and exact eight-file scope. Resolve C53 externally and prove clean status.

```bash
task5_clean_call commit-checkpoint C53
task5_clean_call authenticate-state C53 committed
```

- [ ] **Step 6: Formally review immutable C52..C53**

Freeze one runtime package from the resolved real C52 and C53: exact IDs/trees/parents/subjects/scopes, full-index diff, changed-file pins, RED/GREEN commands and hashes, and registration manifest. Hash the package only after it is immutable; record its runtime-resolved path/hash outside the repository. Dispatch independent specification/protocol and quality/concurrency reviews against that same package, preserve each identity and complete response, and never amend C53. The plan supplies `C53-UNSERIALIZED-TERMINAL-HANDOFF` only as a qualified hypothesis: terminal output and reporter handoffs may not share one serialized lease, allowing a terminal claim to close/fail while Run, Initial, or Step output is still active. Blind reviewers independently return `CONFIRMED or DISPUTED`, unrestricted findings, and their actual severity counts. Response sealing authenticates only package/schema/bytes. Continuation requires both reviewers independently to confirm that hypothesis with no additional Critical or Important finding. A dispute or any newly reported Critical or Important finding stops the lifecycle for user adjudication through a new append-only plan. No future package or review-response hash is claimed by P.

Run `task5_clean_call freeze-review-package C53`, dispatch only that fixed
immutable package non-shell, and have the reviewers write only the fixed
`C53.spec.pending.md` and `C53.quality.pending.md` inbox paths. Invoke
`task5_clean_call seal-review-response C53 spec` and
`task5_clean_call seal-review-response C53 quality`, appending each exact
lowercase response SHA-256 from the non-shell handoff. Preserve the sealed
response pair exactly; the transition gate independently evaluates whether its
actual dispositions authorize staging C53C1.

## Task 3C1: Commit C53C1 — Serialize Passive Terminal Handoff

**Files:**

- Modify: `oracle/plugin/Core/PassiveDriver.cs`
- Modify: `oracle/plugin/Core/PassiveDriverCompletion.cs`
- Modify: `oracle/plugin/Core/PassiveDriverInput.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTerminalTests.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTestSupport.cs`

**Interfaces:**

- Consumes: immutable C53 and its formal finding.
- Produces: shared output lease, deferred terminal work, serialized Run/Initial/Step/Error/End/Close/reporter handoff, deterministic race barriers, and the sole terminal-owner semantics described above.

- [ ] **Step 1: Authenticate C53 and apply C53C1 concurrency tests only**

Extract/authenticate/apply the committed test/support block with the index protocol and prove cached-diff equality. Require production exactly C53 and registration identities unchanged.

```bash
task5_clean_call stage-plan-patch C53C1 tests
task5_clean_call authenticate-state C53C1 tests-staged
```

- [ ] **Step 2: Run and authenticate the C53C1 behavioral RED**

Force-build successfully and run `driver-terminal`. Require the exact `first fault wins race` / `fault Close waits for active Run output` first failure. Reject a timeout-only or nondeterministic failure.

```bash
task5_clean_call behavioral-red C53C1
```

- [ ] **Step 3: Apply the C53C1 output-lease correction**

Extract/authenticate/apply only the committed production block with the index protocol and prove cached-diff equality. Serialize terminal work without holding a driver monitor across external callbacks. Preserve marker-only Step failure, at-most-once Close, success/fault atomic ownership, and post-close Complete-failure asymmetry.

```bash
task5_clean_call stage-plan-patch C53C1 production
task5_clean_call authenticate-state C53C1 green-staged
```

- [ ] **Step 4: Run C53C1 GREEN gates**

Run the complete common matrix. The stress action requires a clean committed
checkpoint and therefore runs in Step 5, not against this staged tree.

```bash
task5_clean_call force-net10 C53C1 green-staged
task5_clean_call focused-csharp C53C1 green-staged driver-initial
task5_clean_call focused-csharp C53C1 green-staged driver-input
task5_clean_call focused-csharp C53C1 green-staged driver-terminal
task5_clean_call full-csharp C53C1 green-staged
task5_clean_call force-net35 C53C1 green-staged
task5_clean_call full-python C53C1 green-staged
```

- [ ] **Step 5: Commit and authenticate C53C1**

Commit with exact subject `fix: serialize passive terminal handoff`. Require sole parent C53 and exact five-file scope. Resolve C53C1 externally; never amend it.

```bash
task5_clean_call commit-checkpoint C53C1
task5_clean_call authenticate-state C53C1 committed
task5_clean_call stress C53C1 postcommit
```

The stress action authenticates committed C53C1 and exact empty porcelain,
then records 20 immutable per-iteration command/status/identity/status-before/
status-after sets and their aggregate hash.

- [ ] **Step 6: Formally review the immutable C53..C53C1 hypothesis**

Freeze a new runtime package from the resolved real C53/C53C1 pair with the same metadata, patch, command, log, and manifest fields; hash and record it externally before dispatch. Preserve separate specification/protocol and quality/concurrency responses. The plan supplies `C53C1-STALE-QUEUED-ERROR-INDEX` only as a qualified hypothesis: an overlapping successful Step may leave ordinary Error `input_index=N` stale after the durable Step advances the parser position to `N+1`. Blind reviewers independently return `CONFIRMED or DISPUTED`, unrestricted findings, and actual severity counts. Response sealing authenticates package/schema/bytes without evaluating the conclusion. Continuation requires both reviewers independently to confirm only that hypothesis; a dispute or any new Critical or Important finding stops for user adjudication through a new append-only plan. Do not amend C53C1; proceed only through C53C2. No future package or response hash is claimed by P.

Run `task5_clean_call freeze-review-package C53C1`, dispatch that fixed
immutable package non-shell, and have the two reviewers write only the fixed
`C53C1.spec.pending.md` and `C53C1.quality.pending.md` inbox paths. Invoke
`task5_clean_call seal-review-response C53C1 spec` and
`task5_clean_call seal-review-response C53C1 quality`, appending each exact
lowercase response SHA-256 from the non-shell handoff. Preserve the exact sealed
response pair; the transition gate independently evaluates whether its actual
dispositions authorize staging C53C2.

## Task 3C2: Commit C53C2 — Rebase Deferred Ordinary Step Faults

**Files:**

- Modify: `oracle/plugin/Core/PassiveDriverInput.cs`
- Modify: `oracle/plugin/tests/PassiveDriverTerminalTests.cs`

**Interfaces:**

- Consumes: immutable C53C1, its stale-parser-position finding, and the real NDJSON sink fixture.
- Produces: post-durable-Step rebase of deferred ordinary Error, parser-position assertions, real-trace RED/GREEN, and unchanged marker-only Step TraceIo behavior.

- [ ] **Step 1: Authenticate C53C1 and apply C53C2 tests only**

Extract/authenticate/apply the committed terminal-test block with the index protocol and prove cached-diff equality. It must change no registration identity and no support/production file.

```bash
task5_clean_call stage-plan-patch C53C2 tests
task5_clean_call authenticate-state C53C2 tests-staged
```

- [ ] **Step 2: Run and authenticate the C53C2 behavioral RED**

Force-build successfully and run `driver-terminal`. Require status `1` and the exact `real Step remains durable before deferred Error second line` first failure. Preserve the RED log before applying production.

```bash
task5_clean_call behavioral-red C53C2
```

- [ ] **Step 3: Apply the narrow C53C2 production patch**

Extract/authenticate/apply only the committed production block with the index protocol and prove cached-diff equality. Under the existing output-lease lock, after the Step is durable, clear attempt state, increment `completedInputs`, and rebuild only deferred ordinary Error with null index/input, zero settle frames, and null last capture. Do not change TraceIo or Dispose work. Authenticate the exact two-file result tree.

```bash
task5_clean_call stage-plan-patch C53C2 production
task5_clean_call authenticate-state C53C2 green-staged
```

- [ ] **Step 4: Run C53C2 GREEN and Python gates**

Run the complete common matrix. Re-authenticate the pristine indexed C53C2
result. The stress action requires a clean committed checkpoint and therefore
runs in Step 5. Do not start T5M28 or any other clone-based transaction yet:
the required real C53C2 commit does not exist until Step 5.

```bash
task5_clean_call force-net10 C53C2 green-staged
task5_clean_call focused-csharp C53C2 green-staged driver-initial
task5_clean_call focused-csharp C53C2 green-staged driver-input
task5_clean_call focused-csharp C53C2 green-staged driver-terminal
task5_clean_call full-csharp C53C2 green-staged
task5_clean_call force-net35 C53C2 green-staged
task5_clean_call full-python C53C2 green-staged
```

- [ ] **Step 5: Commit and authenticate C53C2**

Commit with exact subject `fix: rebase deferred step faults`. Require sole parent C53C1 and exact two-file scope. Resolve C53C2 externally and prove clean status.

```bash
task5_clean_call commit-checkpoint C53C2
task5_clean_call authenticate-state C53C2 committed
task5_clean_call stress C53C2 postcommit
```

The stress action authenticates committed C53C2 and exact empty porcelain
before and after every one of its 20 iterations.

- [ ] **Step 6: Run the fresh clone-based T5M28 real-trace parser proof**

Now that resolved C53C2 exists, create a disposable no-hardlink clone from the authenticated local `execution_root` at exact C53C2. Materialize the committed P plan's exact temporary export hook and qualified stale probe with the fenced-artifact extractor, perform the catalogued fresh path-only transform, force-build and export a new real-sink trace in the clone, exact-reverse the hook, authenticate restored test/tree/index/status, force-build and focused-GREEN again, and run the transformed probe only through `$execution_root/.venv/bin/python` with the pinned primary source, explicit `PYTHONPATH="$execution_root/src"`, and `UV_OFFLINE=1`. Require every hook/trace/probe/stale-trace identity and exact PASS stdout declared in the catalog. Preserve this proof package externally for Step 7 and Task 4.

```bash
task5_clean_call t5m28-proof C53C2 C53C2-T5M28-proof
```

Use that exact fresh child for the two committed-plan extractions and the path-transform identity. Never reuse it for the independent Task 4 replay.

- [ ] **Step 7: Run fresh corrected-5.3 formal reviews**

At runtime, freeze one corrected-5.3 package covering resolved C52..C53C2, both correction diffs, every affected command/log identity, the stress gate, the real-NDJSON terminal tests, and Step 6's actual T5M28 export/stale-transform/parser proof. Its authenticated identity records both immediate parent C53C1 and range parent C52, and its scope is the exact eight-path C52..C53C2 union rather than only C53C2's two-file commit scope. Hash the package externally, dispatch fresh independent reviewers, and retain their identities and complete response bytes. Each reviewer derives unrestricted findings and its actual nonnegative Minor count. Continuation requires `APPROVE` with zero Critical and Important findings; response sealing does not prewrite or evaluate that outcome. Do not prestate future package or response hashes in P; record the resolved values externally and in R.

Run `task5_clean_call freeze-review-package C53C2`, dispatch that fixed
immutable package non-shell, and have the reviewers write only the fixed
`C53C2.spec.pending.md` and `C53C2.quality.pending.md` inbox paths. Invoke
`task5_clean_call seal-review-response C53C2 spec` and
`task5_clean_call seal-review-response C53C2 quality`, appending each exact
lowercase response SHA-256 from the non-shell handoff. The transition gate
requires both independent approvals before Task 4.

## Task 4: Qualify Mutations, Verify the Full Lineage, and Commit R

**Files:**

- Create: `docs/superpowers/reports/2026-08-07-task-5-passive-driver-verification.md`
- Read-only: complete S4..C53C2 chain, Task 4.2 ignored evidence, all external Task 5 evidence
- Modify: nothing else

**Interfaces:**

- Consumes: accepted C53C2, both fresh corrected-5.3 reviews, all checkpoint packages, all 28 mutation transactions, and the Step 6 stale-trace proof package.
- Produces: compact tracked report R and final user handoff. It produces no new runtime behavior.

- [ ] **Step 1: Authenticate the complete linear lineage**

Resolve and verify every alias, parent, subject, exact scope, tree, and checkpoint file hash from S4 through C53C2. Require no merge parent and no rewritten reviewed commit.

- [ ] **Step 2: Run the final clean verification matrix**

From exact C53C2 run forced net10 build, `driver-initial`, `driver-input`, `driver-terminal`, full C# harness, forced net35 build, pinned Python, and the 20-iteration terminal stress loop. Capture commands, exact tip/tree, cohorts, exits, log hashes, warning/error counts, iteration count, and aggregate result.

```bash
task5_clean_call force-net10 C53C2 committed
task5_clean_call focused-csharp C53C2 committed driver-initial
task5_clean_call focused-csharp C53C2 committed driver-input
task5_clean_call focused-csharp C53C2 committed driver-terminal
task5_clean_call full-csharp C53C2 committed
task5_clean_call force-net35 C53C2 committed
task5_clean_call full-python C53C2 committed
task5_clean_call stress C53C2 task4
```

- [ ] **Step 3: Qualify and independently audit T5M01-T5M28**

Execute the mutation protocol in disposable no-hardlink clones from exact committed C53C2, retain rejected T5M20 and broad T5M23 separately, and obtain an independent read-only audit of patch fidelity, first failures, restoration, and T5M28 provenance. Require 28 canonical, killed, single-semantic, nonredundant mutations and no surviving change.

Run all canonical transactions as separate controller actions with this literal
closed loop, then run the rejected-candidate transactions separately:

```bash
for mutation_id in \
    T5M01 T5M02 T5M03 T5M04 T5M05 T5M06 T5M07 \
    T5M08 T5M09 T5M10 T5M11 T5M12 T5M13 T5M14 \
    T5M15 T5M16 T5M17 T5M18 T5M19 T5M20 T5M21 \
    T5M22 T5M23 T5M24 T5M25 T5M26 T5M27 T5M28; do
  task5_clean_call canonical-mutation C53C2 "$mutation_id"
done
task5_clean_call rejected-mutation C53C2 T5M20
task5_clean_call rejected-mutation C53C2 T5M23
```

Independently replay Step 6's T5M28 real-sink proof through the second closed
proof name:

```bash
task5_clean_call t5m28-proof C53C2 Task4-T5M28-replay
```

That action internally creates a distinct fresh artifact child, sibling
no-hardlink clone, and contained `runtime/`; extracts and authenticates the
committed hook and probe; reversibly transforms only the catalogued historical
path without reading it; exports and pins the real trace; reverses/restores and
GREENs the clone; and runs the transformed probe only through the pinned
primary interpreter/source with `UV_OFFLINE=1`. Require the exact hook,
probe, reader, real-trace, stale-trace, command, stdout, and status identities
declared by the runtime. Never reuse the C53C2 proof child.

- [ ] **Step 4: Re-run the Task 4.2 ignored-evidence closure**

Repeat Task 0's read-only closure. Require the same aggregate manifest identity and exact ledger/helper/brief bytes. Confirm no Task 5 path was written under the Task 4.2 namespace.

Invoke `task5_clean_call task42-closure final` exactly once. Its fresh
`task42-final` snapshot must compare byte-for-byte to every declared initial
anchor/namespace manifest inside the function.

- [ ] **Step 5: Freeze and independently review FINAL qualification**

Freeze one authenticated `FINAL` qualification package only after the exact
135-action implementation/qualification sequence has completed. Its
`FINAL-PACKAGE-FORMAT: task5-final-qualification-v1` identity binds the exact
P..C53C2 full implementation patch, nine-path union scope, linear lineage,
sealed authority receipt, every prior package and complete response, final
matrix and stress evidence, all 28 canonical and two rejected mutation
transactions, both T5M28 proof packages, and the final Task 4.2 closure. The
package records `range-parent-checkpoint=P` and
`range-child-checkpoint=C53C2`; it contains no report or prospective R bytes.

Dispatch that same immutable package to a fresh specification/protocol lane
and a fresh quality/evidence lane. Response sealing authenticates only package,
schema, and bytes. Each lane derives unrestricted findings and its actual
nonnegative Minor count; continuation requires `APPROVE` with zero Critical
and Important findings. The quality/evidence response must additionally derive
and carry exactly `INDEPENDENT-MUTATION-AUDIT: PASS CANONICAL=28 KILLED=28
REJECTED=2 T5M28-PROOFS=2 RESTORATION=PASS SURVIVORS=0` from the package's
28+2 transactions, first failures, reverse applications, restoration
identities, and both T5M28 proofs. Any other disposition stops the lifecycle.

```text
task5_clean_call freeze-review-package FINAL
task5_clean_call seal-review-response FINAL spec <sha256>
task5_clean_call seal-review-response FINAL quality <sha256>
```

The non-shell handoff writes only `FINAL.spec.pending.md` and
`FINAL.quality.pending.md` before the corresponding seal calls. A dispute,
rejection, or new Critical or Important finding terminally consumes the
namespace and requires user adjudication through a new append-only plan.

- [ ] **Step 6: Write the compact self-describing report**

Use `apply_patch` to create the one report. It must record:

- S4/D/P/C51/C52/C53/C53C1/C53C2 resolved IDs, trees, parents, subjects, and scopes;
- every patch/test/result hash and exact RED first failure;
- every final command exactly as run, exit status, tip/tree, cohort, stdout/stderr hash, and warning/error count;
- 20-iteration stress-loop command, count, per-iteration/aggregate status, and output hash;
- Python command, interpreter/source pins, full-suite summary, T5M28 parser command, exact stdout, and exit;
- mutation table identities, invalid/redundant accounting, rejected candidates, restoration, and independent audit verdict;
- Task 4.2 closure identities before/after;
- the authority-bundle identity and every formal review identity, package hash,
  reviewer reference, verbatim verdict, hypothesis disposition, and mutation-
  audit disposition available from P through FINAL, explicitly excluding R;
- confirmation that no network, restore, game launch, game/save/config mutation, Task 6 work, tracked raw ledger, or separate seal occurred; and
- the controller-generated canonical response block whose exact 14 lowercase-
  hex records losslessly preserve every complete sealed P-through-FINAL
  response, including every unrestricted finding and reviewer-derived Minor
  disposition.

The report contains exactly one `P-THROUGH-FINAL-REVIEWS: recorded` marker and
one `R-SELF-REVIEW: excluded-from-tracked-report` marker. R review identities, reviewer references, verdicts, and Minor dispositions live only in the immutable
external package/response ledger, the final audit, and the handoff because none
exists when the tracked report candidate freezes. Do not paste raw logs into R.
Cite their external hashes and the exact facts necessary to reproduce them.
The report is NUL-free before either marker parsing or the C-locale broad
standalone-R scan; a NUL cannot hide later report text from either parser.

No reviewer-authored free text is copied into the readable report narrative.
The complete immutable response bytes are instead represented only by the
canonical lines generated under the exact-lowercase-hex-v1 contract. The
readable verdict, count, reference, and disposition-index fields are a compact
index; the full response hex is the authoritative exact-byte representation of
every finding and disposition and is reconstructible without paraphrase. In
the real tracked report, write the exact line
`<!-- TASK5-REPORT-REVIEW-RECORDS-BEGIN -->`, append the 14-line generated file
byte-for-byte, and then write the exact line
`<!-- TASK5-REPORT-REVIEW-RECORDS-END -->`. There is no blank, unknown,
duplicate, extra, or R-checkpoint record inside that block.

Before editing, run `task5_clean_call report-gate authorize`. That action
validates all 14 immutable sources, exclusively creates mode-400
`report-gates/review-records.expected`, and binds its SHA-256 in the authorize
gate. Then use `apply_patch` once, outside shell, to create only the fixed report
path and copy the expected file's exact lines between the fixed markers. Run
`task5_clean_call report-gate candidate` immediately afterward; it must
byte-compare that block, reauthenticate the broad standalone-R exclusion, bind
the expected-block SHA, authenticate the exact one-untracked-path state, and
seal the report-candidate identity. Stage, reviewed, and final-audit repeat the
same expected-block authentication. No other postbootstrap repository edit is
permitted.

- [ ] **Step 7: Review the report without changing implementation history**

Run a fresh specification/protocol review and quality/evidence review of C53C2 plus the staged report. Any report-only defect is fixed before R is committed; no production/test commit may change. Any implementation defect triggers the append-only correction protocol instead.

Run `task5_clean_call report-gate stage`, then
`task5_clean_call freeze-review-package R`. Dispatch only that fixed immutable
package non-shell. The reviewers write only `R.spec.pending.md` and
`R.quality.pending.md`; invoke `task5_clean_call seal-review-response R spec`
and `task5_clean_call seal-review-response R quality`, appending each exact
lowercase response SHA-256 from the non-shell handoff. Finally run
`task5_clean_call report-gate reviewed`. If a report-only defect is found,
stop and preserve the consumed one-shot namespace. This plan authorizes no
mid-lineage bootstrap or report-correction restart; recovery requires a new
append-only plan and explicit user approval that defines and authenticates the
replacement transaction from unchanged C53C2.

The R package and both sealed R responses bind their assigned reviewer
references and the authority actor externally. They are intentionally absent
from the already-frozen report and are authenticated by `report-gate reviewed`,
`final-audit`, and the final handoff.

- [ ] **Step 8: Commit and authenticate R**

Commit only the report with subject `docs: record Task 5 passive driver verification`. Require sole parent C53C2, exact one-file scope, clean status, and no non-ignored untracked path. Resolve R for the handoff, but do not amend the report to self-pin R.

```bash
task5_clean_call commit-checkpoint R
task5_clean_call authenticate-state R committed
```

- [ ] **Step 9: Final protected-state and command-scope check**

Verify the real worktree, derivation checkout, protected Task 4.2 checkout, and Task 4.2 ignored evidence retain their pre-execution identities. Do not read the game installation, saves, or configuration to manufacture a before/after claim. Instead, authenticate the complete external command ledger and generated-driver hash, require that every executed command belongs to this plan's allowlist, and prove no command named or accessed a game/install/save/config path or launched Steam, Unity, Mono, BepInEx, the plugin, or a GUI. Report pre-existing unrelated worktree dirt without altering it.

```bash
task5_clean_call final-audit
```

`final-audit` is the last executable action. On success the outer bootstrap
also re-authenticates every completed ordinal ledger entry and its manifest;
no later command is authorized in that evidence namespace.

## Append-Only Corrections

The known append-only history is intentional:

- C53 remains the immutable original completion implementation.
- C53C1 remains the immutable serialization correction and carries the qualified
  stale-index hypothesis; it is never assumed finally accepted before the
  actual sealed review bytes satisfy the transition gate.
- C53C2 is the separate narrow protocol correction and receives fresh affected reviews.

If any new Critical or Important finding appears before R:

1. stop and preserve every commit, package, log, and review response;
2. if C53C2 does not yet exist, write and obtain approval for a narrow descendant planning artifact from the current immutable tip, and name its correction from that actual parent; never pretend C53C2 or its parent relation already exists;
3. reserve `C53C3` for a correction whose exact parent is an existing C53C2; otherwise use the next monotonic suffix defined by the approved descendant plan;
4. approve that narrow descendant plan before editing code;
5. begin with a test-only RED, apply a separately authenticated production patch, and rerun all affected common gates;
6. regenerate every mutation whose parent/context/expected result changed;
7. obtain fresh affected reviews and a final cross-slice review; and
8. update the declared lineage only in a new descendant planning/report artifact, never by rewriting P or a reviewed commit.

A failed gate is evidence, not permission to rerun under the same artifact
identity. Any unexpected postbootstrap failure terminally consumes this plan and its evidence namespace. Preserve the exact failed state; do not invoke this
plan's bootstrap again. Continuation requires a new explicit user-approved append-only recovery plan that authenticates the actual HEAD, index, and worktree,
the retired namespace manifest, its immutable command/package/response
identities, the revised lineage, and every specifically authorized restoration or evidence-import operation. That new plan must define its own fresh namespace
and bootstrap from the authenticated actual state. This plan authorizes no generic resume bootstrap.

## Self-Review

Before P is committed, the standalone checker—not the future committed-P
controller—performs the candidate audit. After the one-file P commit it is
re-extracted from P, required byte-identical, and performs the committed audit;
the plan/checker/runtime/core-manifest identities from both modes must match.
Both preapproval checker modes and the later `plan-postcommit` checker begin at
process start through the exact minimal `env -i` contract. The checker-only
disposable replay is audit evidence, not implementation execution or reusable
state.
Formal reviews then run non-shell and execution stops for approval. Only after
approval does bootstrap create the evidence namespace, and its first action,
`plan-postcommit`, repeats the committed audit before Task 0.

- [ ] The candidate and committed checker modes both pass with identical
  plan/checker/runtime/core-manifest identities; P has exact parent, subject,
  mode, one-file scope, and committed bytes.
- [ ] The authenticated artifact catalog contains exactly 10 implementation,
  28 canonical, 2 rejected, 1 hook, and 1 probe bodies, with 41 diff fences.
- [ ] Every injected patch ends in LF, hashes to its declared SHA-256, has declared line/byte counts, uses full-index blob IDs, and applies only to its exact predecessor.
- [ ] The patch/RED catalog and its owning task steps together bind every checkpoint's parent/result pins, runtime-resolved tree, RED status/first failure, GREEN gates, and immutable review-package protocol.
- [ ] S4 and D IDs/trees/subjects/scopes match this plan and the Task 4.2 seal.
- [ ] No future commit ID is self-pinned in P; aliases are resolved only after their commits exist.
- [ ] File scopes match the commit graph exactly, including the single authorized Task 5.3 input-test amendment.
- [ ] All 2 boundary, 8 initial, 8 input, and 6 terminal identities appear once in frozen order; Program's final manifest is exact.
- [ ] C53C1's qualified stale-index hypothesis and actual sealed disposition are
  preserved, and C53C2's null-field rebase excludes TraceIo/Dispose.
- [ ] Every formal review records reviewer-derived actual outcomes and every actual Minor disposition.
- [ ] Every actor, approval, reviewer, and assignment reference satisfies the
  one shared ASCII-safe/no-standalone-R predicate; the candidate checker,
  bootstrap, runtime ingestion, package/response revalidation, and tracked
  report boundary agree on its truth table.
- [ ] Every fixed coordination-reference file is byte-exact with one final LF,
  and every parsed authority receipt/identity and the tracked report passes the
  authenticated NUL defense before command substitution, field extraction, or
  standalone-R scanning.
- [ ] No corrected-5.3 or R Minor count or conclusion is prewritten; the report
  records only outcomes available through FINAL and the external final handoff
  records R's later outcome.
- [ ] The tracked report contains exactly the controller-generated 14-record
  P-through-FINAL response block. Its complete lowercase response hex is the
  lossless representation of unrestricted findings and Minor dispositions;
  no reviewer-authored free text or R review record appears raw in the report.
- [ ] The final report requirements include commands, exits, tip/tree, cohorts, stress metadata, and Python parser stdout/exit.
- [ ] Task 4.2 ignored evidence is read-only and closed before and after Task 5.
- [ ] Every command is Apple Bash 3.2-compatible, offline, pinned to dotnet 10.0.300, and contains no game/Task 6 action.
- [ ] The dispatcher exposes every required lifecycle, gate, mutation, proof,
  and test action at its exact arity; the runtime has no called-but-undefined
  `task5_*` symbol.
- [ ] Bootstrap is fail-fast, preserves and retires its namespace on error, and
  each `task5_clean_call` finalizes one immutable ordinal ledger entry.
- [ ] Behavioral RED proves actual worktree/index equality, and every stress
  iteration preserves exact before/after porcelain bytes and records their
  SHA-256 in the aggregate row.
- [ ] No step delegates execution to a legacy Task 5 body.
- [ ] The traceability table covers every approved design requirement.
- [ ] The fence-aware narrative whitespace checker passes for the materialized
  plan; it excludes only the 41 authenticated `~~~diff` bodies. The 40
  implementation/canonical/rejected bodies contain 105 intentional
  single-space context lines, and the separately authenticated T5M28 export
  hook contains one more.

## Handoff

Task 5 is complete only when the handoff states:

- the resolved exact chain `S4 -> D -> P -> C51 -> C52 -> C53 -> C53C1 -> C53C2 -> R`;
- all required subjects, parent relations, scopes, trees, and file hashes;
- all REDs, GREENs, net10/net35 builds, focused/full C# runs, Python suite, stress loop, and T5M28 parser proof with exact statuses;
- all 28 canonical mutations killed, restored, and independently audited, with rejected T5M20/T5M23 candidates segregated;
- the sealed authority-bundle identity, amendment ratification, exact approval
  and implementation-actor references, and actual reviewer-derived findings,
  reviewer references, and Minor dispositions through FINAL in R's readable
  structured index and exact 14-record response-hex block, and for R in the
  immutable external ledger/final audit;
- both FINAL lanes `APPROVE` with zero Critical and Important findings and the quality/evidence lane's independently derived mutation-audit disposition;
- Task 4.2 ignored evidence identical before and after;
- R committed as the sole child of C53C2 with one-file scope and a clean Task 5 worktree; and
- no network, restore, real-game launch, game/save/config change, Task 6 work, protected-checkout edit, raw tracked ledger, or new seal.

The next authorized work is planning Task 6 from R. This plan grants no Task 6 execution authority.
