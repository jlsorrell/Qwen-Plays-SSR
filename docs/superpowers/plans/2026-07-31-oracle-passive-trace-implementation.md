# SSR Passive Settled-State Trace Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the reviewed passive real-game trace milestone through three independently reviewable offline implementation tracks, followed by a separately planned and approved one-launch acceptance operation.

**Architecture:** The Python protocol validator freezes the consumer contract and synthetic wire fixtures first. The Unity-free C# core and thin game adapter then produce exactly that contract and yield a literal reproducible `0.2.0` DLL hash. Finally, the Python passive controller reuses hardened installer/boot primitives, consumes both artifacts, and proves its complete lifecycle synthetically before any operational plan is written.

**Tech Stack:** Python 3.12+, pytest, C# 7.3, .NET Framework 3.5, .NET 10 test harness, BepInEx 5.4.23.5, HarmonyX 2.9.0, macOS Tahoe 26.6, Git worktrees and subagent review gates.

## Global Constraints

- The authoritative design is `docs/superpowers/specs/2026-07-31-oracle-passive-trace-capture-design.md`.
- Execute the detailed plans in the order below. A worker receives only one numbered task from one detailed plan, followed by specification review and code-quality review before the next task.
- Keep all implementation in the isolated `codex/oracle-passive-trace` worktree. Preserve the user's root-checkout `.DS_Store` changes and unrelated worktrees.
- Tasks in these three plans are offline. Synthetic child processes and read-only installed-game inspection are allowed; deployment, config mutation, preloader mutation, save mutation, and game launch are not.
- Never commit owner-local decompilation, levels, real traces, generated configs, isolated saves, recovery data, package caches, or build outputs.
- Stop on a changed pinned assembly, Mode-off fixture, installer state, app-signature identity, source hash, or cross-language fixture. Investigate the delta; do not update a pin to make a check pass.
- The standalone preflight must observe `/usr/bin/sw_vers -productVersion` under the fixed `C` locale, retain exact `macos_product_version = "26.6"`, and refuse any missing, failed, malformed, or different result before allocation, installer mutation, or launcher acquisition.
- For every detailed task, follow that detailed plan's stated check/review/commit order. In all cases, run its focused GREEN command and `git diff --check`, commit only that task's files, and do not begin the next task until fresh specification and code-quality approvals cover the exact committed diff. Any post-review change requires the GREEN command and both reviews again.
- The final operational acceptance is not part of these offline plans. It is written only after the reviewed plugin hash and controller paths are literal, then presented for separate explicit approval authorizing exactly one launch and no retry.

## Cross-plan interfaces

| Producer | Contract | Consumer |
| --- | --- | --- |
| Protocol plan | `OracleProtocolError`, `OracleRun`, `ErrorRecord`, `read_oracle_trace_stream`, `require_passive_success` | Passive probe; the path-opening `read_oracle_trace` wrapper remains internal to the protocol CLI/fixtures and is never used for retained evidence |
| Protocol plan | `passive-success.ndjson`, `passive-error.ndjson` exact synthetic bytes | C# encoder tests |
| Plugin plan | schema-v1 compact NDJSON, seven progress/terminal markers, fourteen record errors, eight marker-only errors | Protocol validator and passive monitor |
| Plugin plan | two byte-identical `0.2.0` DLLs and literal SHA-256 | Passive probe request and operational plan |
| Probe plan | `preflight_passive_probe`, `run_passive_probe`, CLI, `passive-probe.json` schema v1 retaining exact `macos_product_version`, final healthy-state proof | Operational acceptance |
| Probe plan | retained trace/log/config/save inventory and unchanged ordinary-save proof | Next parser/comparator design |

The schema constants, marker strings, error table, fixed counts/limits, and assembly hash are duplicated only as tested cross-language constants. Every other subsystem consumes the preceding plan's named API rather than reimplementing it.

## Spec coverage

| Design section | Implementing tasks |
| --- | --- |
| 1-4 Context, decision, goals, non-goals | Global constraints in all plans; plugin Track 10 and controller family 21 document status without automated replay, raw-save parsing, semantic simulator comparison, or launch. |
| 5 Architecture and boundaries | Plugin Tracks 1-9, protocol Tasks 1-26, controller families 4-21. |
| 6 Modes and configuration | Plugin Tracks 6-9; controller families 8, 17, and 19-21. |
| 7 Trace protocol | Plugin Tracks 1-5 and 7-9 produce it; protocol Tasks 1-26 consume and freeze it; controller families 9-11 authenticate it. |
| 8 Observation and settling | Plugin Tracks 4-5 implement epochs/attempts; Tracks 7-9 implement adapter/Core boundaries/hooks/lifecycle. |
| 9 Python validation | Protocol Tasks 1-26. |
| 10 Probe and evidence | Controller families 4-21; coordinator Task 4 plans the separately authorized runtime execution. |
| 11 Failure and restoration | Plugin Tracks 3, 5, 8, and 9; controller families 1-6, 10-11, and 16-20. |
| 12 Test strategy | Every detailed task begins RED and ends GREEN; each plan has a full offline exit gate. |
| 13 Deliverables | Protocol Tasks 1-26, all 24 decimal plugin tasks across Tracks 1-10, and all 43 controller tasks across families 1-21. |
| 14 Completion boundary | Deferred. Coordinator Task 4 prepares the separately approved operational plan; that later plan must contain the one execution and post-run verification. Raw-save parsing, semantic simulator comparison, and automated replay remain outside this milestone. |

---

### Task 1: Implement and review the strict Python protocol validator

**Files:**
- Plan: `docs/superpowers/plans/2026-07-31-oracle-passive-protocol.md`
- Primary implementation: `src/ssr_env/oracle_protocol.py`, `tools/oracle_trace_check.py`
- Primary tests: `tests/test_oracle_protocol.py`, `tests/fixtures/oracle_trace/`

**Interfaces:**
- Produces every Python protocol and fixture contract in the table above.
- Has no dependency on plugin or probe implementation.
- Must finish before the C# encoder's golden-byte gate and before passive monitor implementation.

- [ ] **Step 1: Execute Tasks 1-26 from the protocol plan with fresh implementer/reviewer gates**

Use the exact RED/GREEN/commit commands in that document. Keep each numbered task as its own commit; do not batch parser, relational validation, CLI, and fixture work into one review.

- [ ] **Step 2: Run the protocol exit gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q \
  src/ssr_env/oracle_protocol.py tools/oracle_trace_check.py \
  tests/test_oracle_protocol.py
git diff --check
```

Require independent specification approval for every design-section 7/9 rule and code-quality approval for bounded allocation, deterministic errors, and fixture independence.

### Task 2: Implement and review the passive `0.2.0` plugin

**Files:**
- Plan: `docs/superpowers/plans/2026-07-31-oracle-passive-plugin.md`
- Primary implementation: `oracle/plugin/Core/`, `oracle/plugin/GameAdapter.cs`, `oracle/plugin/PassivePatches.cs`, `oracle/plugin/PassiveController.cs`, `oracle/plugin/Plugin.cs`
- Primary tests: `oracle/plugin/tests/`

**Interfaces:**
- Consumes the protocol plan's exact synthetic fixtures.
- Produces the reviewed reproducible DLL hash required by Task 3.
- Remains offline; a successful build is not a deployment or runtime result.

- [ ] **Step 1: Execute all 24 decimal tasks across Tracks 1-10 from the plugin plan with fresh implementer/reviewer gates**

Keep protocol/encoder, sink, initial driver, input driver, configuration,
adapter, Core firewall/startup policy, game-facing shell, and reproducibility
as distinct reviewable commits. Use a reviewer with the complete approved
design for specification gates and a fresh reviewer with only the task
diff/base for code-quality gates.

- [ ] **Step 2: Run the plugin exit gate and freeze the literal hash in its review record**

```bash
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet run \
  --project oracle/plugin/tests/SsrOracle.UnitTests.csproj \
  -c Release --no-restore -- \
  --assembly "/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed/Assembly-CSharp.dll" \
  --plugin "$PWD/oracle/plugin/bin/Release/net35/SsrOracle.Plugin.dll" \
  --mode-off-fixture "$PWD/data/oracle/boot-probe.cfg"
/opt/homebrew/Cellar/dotnet/10.0.300/bin/dotnet build \
  oracle/plugin/SsrOracle.Plugin.csproj -c Release --no-restore -warnaserror \
  -p:GameManagedDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/Sausage.app/Contents/Resources/Data/Managed" \
  -p:BepInExCoreDir="/Users/jlsor/Library/Application Support/Steam/steamapps/common/Stephen's Sausage Roll/BepInEx/core"
git diff --check
```

The task report must name both independently built DLL paths, their identical literal SHA-256, the exact assembly-surface result, and Mode-off fixture identity. Do not begin installed-game work.

### Task 3: Implement and review the bounded passive controller

**Files:**
- Plan: `docs/superpowers/plans/2026-07-31-oracle-passive-probe.md`
- Primary implementation: `src/ssr_env/oracle_passive_probe.py`, narrow shared changes in `oracle_boot.py`/`oracle_install.py`, `tools/oracle_passive_probe.py`
- Primary tests: `tests/test_oracle_passive_probe.py` plus existing oracle regression suites

**Interfaces:**
- Consumes the protocol validator and the literal plugin hash/two verified DLL copies.
- Produces an offline-tested one-launch controller but does not invoke it against the installed game.
- Preserves existing boot/install public contracts.

- [ ] **Step 1: Execute all 43 tasks across families 1-21 from the passive-probe plan with fresh implementer/reviewer gates**

Do not combine installer interruption repair, shared primitive extraction, save proof, monitor, result/evidence, lifecycle, or CLI/docs. The shared-primitive task must receive explicit legacy boot-probe review before passive code consumes it.

- [ ] **Step 2: Run the controller exit gate**

```bash
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_protocol.py tests/test_oracle_passive_probe.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q --tb=short \
  tests/test_oracle_boot.py tests/test_oracle_install.py \
  tests/test_oracle_install_compat.py tests/test_oracle_compat.py
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run pytest -q
UV_CACHE_DIR=/tmp/ssr-uv-cache uv run python -m compileall -q src tools tests
git diff --check
```

Require synthetic proof of at most one game-launcher acquisition (inventory
and signature subprocesses are tracked separately), prompt order, full process
cleanup, unchanged ordinary saves, installer-only Mode-off restoration,
official preloader restoration, auxiliary evidence fsync, and JSON-last
publication.

### Task 4: Prepare—but do not execute—the operational acceptance

**Files:**
- Create after Tasks 1-3: `docs/superpowers/plans/2026-07-31-oracle-passive-runtime-acceptance.md`.
- Modify only after a real result: `oracle/README.md` and the passive design's implementation-status section.

**Interfaces:**
- Consumes literal reviewed artifact hashes, paths, current `official` status, current app-signature result, current Mode-off bytes, and current read-only ordinary-save proof.
- Produces one exact command sequence and one explicit approval request; it does not execute the sequence.

- [ ] **Step 1: Re-run read-only preflight after all offline reviews**

Use the final controller's read-only preflight and existing installer status. Record exact `macos_product_version`, current hashes, and status without mutation; require the product version to remain `26.6`. If any identity differs from reviewed evidence, stop and diagnose before writing an operational plan.

- [ ] **Step 2: Write the operational plan with literal values only**

Include the final plugin SHA-256, exact built artifact paths,
preloader/provenance paths, Mode-off fixture path/hash,
game/launcher/evidence paths, single controller command, exact four prompted
phases containing five physical input events (Action twice, one accepted
direction, one blocked direction, and Undo), 300-second bound, expected seven
markers, process/save/config/preloader recovery checks, and explicit no-retry
boundary. Do not use unresolved variables in destructive or mutation commands.

- [ ] **Step 3: Present the operational plan and request separate approval**

The approval request must state that it authorizes installer-only deployment,
exactly one real game launch, five named physical input events across four
prompted phases, evidence retention, Mode-off redeployment, and
official-preloader restore. Silence, prior launch approval, or approval of
these offline plans is not authorization.

Stop here until the user approves. After one approved run, whether success or failure, do not launch again under the same approval.
