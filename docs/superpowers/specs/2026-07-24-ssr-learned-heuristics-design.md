# Studying Learned Heuristics in an Open-Weights Model Trained on Stephen's Sausage Roll

**Date:** 2026-07-24
**Status:** Design approved, pending implementation planning

---

## 1. Research question

What heuristics does an open-weights language model learn when trained with RL to
solve Stephen's Sausage Roll (SSR) levels, and can we measure them against exact
ground truth?

SSR is chosen because it admits a **complete oracle**: for levels below a
tractable size bound, the entire reachable state graph can be enumerated, giving
exact distance-to-goal and exact dead-state labels for every state the model
will ever visit. Very few interesting domains offer this.

### 1.1 This is not an "agent quality" project

Agent strength is a *constraint*, not the objective. This reframing drives three
decisions that a best-possible-agent project would get wrong (§3).

The precondition for Phase 6 is **statistical power on the probe sets**, not a
solve-rate threshold. A failing model still visits states carrying exact oracle
labels, so probe data accumulates regardless of success; what is required is that
behaviour be non-trivial enough for those activations to encode anything.
Solve rate (§7.1) is a training-progress metric and a sanity check, not a gate.

### 1.2 Non-goals

- Beating the exact solver at SSR. It will win. It is the ruler, not a competitor.
- Solving the hardest official levels. They exceed the oracle's tractability bound.
- Pixel-based play. State is symbolic throughout.

---

## 2. Prior art and what exists

- **[jbzdarkid/SSRDecompile](https://github.com/jbzdarkid/SSRDecompile)** — a TAS
  tool that injects inputs into the running Unity game via memory hacking. Not a
  reimplementation. Critically, it ships **121 `.dem` files**: recorded input
  sequences (`North`/`South`/`East`/`West`/`Undo`) solving every official level.
  These are the simulator's acceptance test.

  **Corpus composition (measured 2026-07-24).** 121 files, of which **120 are
  levels**; `all.dem` is the injector's concatenation of every level's inputs and
  has no corresponding geometry. Worlds 1-5 hold 65 levels; **world 6 holds 55**,
  including half-numbered entries (`6-8.5`, `6-9.5`, ...). World 6 is post-game
  content and the hardest material in the game.

  **Solution lengths are long**: min 15 (`1-0`), median 104, mean 138, max
  **1301** (`6-final`). These are demonstrations rather than optimal solutions —
  they wander and use `Undo` — so optimal lengths are shorter, but the order of
  magnitude stands. See §8 for the consequence.
- **PuzzleScript demake** — PuzzleScript is strictly 2D and cannot represent SSR's
  elevation, ladders, or fork separation. Not usable.
- **No open-source SSR simulator or RL environment exists.** Writing one is Phase 0
  and is the critical path for the entire project.

SSR is not Sokoban. It has irreversible failure states, a two-tile agent with
orientation, four independently-cookable surfaces per sausage, elevation, and a
return-to-origin terminal condition.

---

## 3. Core design principle: contamination discipline

> Any heuristic we inject into training is a heuristic we will later "discover."

This single principle drives the three non-obvious decisions below. Each is a
place where the convenient engineering choice would silently destroy the result.

### 3.1 Reward is binary and unshaped

SSR's reward is sparse (solved / not solved). The standard remedy is shaping —
partial credit for cooked faces, proximity to start, etc. **We do not shape.**
Shaping on "cook faces early" and then discovering that the model represents
cook-face priority is discovering our own reward function.

Tractability is bought with **curriculum** instead: solver-graded difficulty
bands, easiest first. Slower, but the findings survive review.

### 3.2 SFT uses uninformed exact search only, and no chain-of-thought

Traces for supervised fine-tuning come from BFS/Dijkstra — uninformed search
carries no heuristic, only ground-truth optimal behavior. A* or IDA* traces
would distil our hand-designed admissible heuristic into the model. Informed
search is reserved for offline analysis where contamination is harmless.

Separately, solver traces have no reasoning attached. The two ways to manufacture
some — hand-written rationales, or distilling a frontier model — both inject an
external agent's heuristics. **SFT therefore trains on bare move sequences**, to
teach output format and basic competence only. RL grows the reasoning.

### 3.3 No inference-time search

Search puts competence in the tree rather than the weights, making "what did the
model learn" unattributable. The trained policy acts alone.

The exception is *measurement*: policy-alone versus policy-plus-search is
reported as a quantity, since the gap indicates how much the learned heuristic
actually carries.

---

## 4. Architecture

```
ssr_env/          Python reference simulator (readable, authoritative for correctness)
ssr_core/         Rust port + PyO3 bindings (fast; for state-graph enumeration)
ssr_oracle/       Full reachable-state enumeration + backward BFS from goal
ssr_gen/          Level generator, curriculum bucketing, minimal-pair construction
ssr_render/       Symbolic state -> text encoding for the LLM
training/         SFT and GRPO configs (verl)
analysis/         Probes, regret decomposition, CoT faithfulness
```

### 4.1 The oracle (Phase 1)

For each level, enumerate the **entire reachable state graph once**, then BFS
*backward* from goal states. This yields, for every reachable state:

| Product | Use |
|---|---|
| Exact distance-to-goal | Linear probe target |
| Dead / alive (unreached by backward pass) | Binary probe target; the core non-trivial concept |
| Optimal action set | Per-move regret scoring |

Computed offline, once per level. This is the instrument the entire experimental
design rests on.

**Tractability bound.** Rough state count per sausage: position x orientation x
2^4 cook-faces ~= 3x10^3. Three sausages on a modest grid reaches ~10^10-10^13 in
the worst case, though the reachable component is far smaller. Early-to-mid
levels enumerate fine; the hardest official levels will not. This is acceptable
and useful — it sets a principled ceiling on generator difficulty.

### 4.2 Model and training

- **Base:** Qwen3-8B class, open weights.
- **SFT:** bare move sequences from uninformed search (§3.2).
- **RL:** GRPO, binary reward, curriculum over difficulty bands.
- **Framework:** verl. Chosen because it is the mature distributed backbone for
  multi-turn rollouts; vanilla TRL is single-turn oriented and is ruled out by §4.3.
- **Hardware:** 8 H100s comfortable, 16 buys wall-clock rather than capability.
  Phases 0-2 need zero GPUs.

### 4.3 Multi-turn interaction (decision)

The model emits **one move per turn** and receives the resulting state.

The alternative — emitting a full move sequence blind — is more elegant and
forces internal simulation, but yields exactly one activation snapshot per level.
Multi-turn yields an activation vector at *every visited state*, each pairing
one-to-one with that state's exact oracle label. For probing this is a vastly
richer dataset, and it is the entire reason the oracle exists. SSR's
irreversibility means a purely reactive policy still fails, so planning pressure
is retained.

Single-shot performance is retained as a **separate evaluation metric**: the
multi-turn/single-shot gap measures how much planning is internal versus
offloaded to the environment.

---

## 5. Validation strategy

### 5.1 Replay validation (automated, covers winning trajectories)

Replay all 120 level `.dem` input sequences against their extracted levels; assert each
one wins. This is near-total coverage of the mechanics — a real solution to a
late-game level exercises rolling, cook-face bookkeeping, elevation, ladders, and
fork separation, and fails loudly if any rule is off by one.

**Gate: Phase 1 does not begin until all 120 pass.** Expect the last handful to
take as long as the first hundred.

### 5.2 Human differential testing (covers the region replays cannot)

Replay validation only exercises *winning* trajectories. A correct solution never
burns a sausage, never drowns one, never enters a dead state. But every
dead-state label in §4.1 — the primary probe target — depends on simulating
exactly those states correctly. This region is otherwise entirely untested.

The project owner owns and plays SSR. Protocol:

1. The simulator generates move sequences it predicts reach failure or unusual
   off-solution configurations, prioritising states it labels **dead**.
2. It renders its predicted resulting state as ASCII.
3. The owner executes the same inputs in the real game and reports divergence.

Adversarial and failure cases are prioritised over ordinary play. Undo semantics
are explicitly included.

### 5.3 Differential testing between implementations

Random and adversarial move sequences are executed against both the Python
reference and the Rust port; states must agree exactly. Guards the port.

### 5.4 Representation validation (Phase 3)

The owner attempts to solve a level **from the ASCII rendering alone**, without
the game. If a strong human player cannot, the encoding is lossy and no model
will succeed. A five-minute test that de-risks the entire text-encoding decision
before any GPU time is spent.

---

## 6. Phase plan

| Phase | Weeks | GPUs | Output |
|---|---|---|---|
| 0. Simulator | 1-3 | 0 | `ssr_env` passing all 120 replays + human divergence tests |
| 1. Exact oracle | 3-5 | 0 | Rust port; distance-to-goal, dead-state, optimal-action maps |
| 2. Generator + curriculum | 5-7 | 0 | Graded train/test levels; minimal-pair probe sets |
| 3. First contact | 7 | 1 | vLLM stood up; baseline evals; state encoding locked |
| 4. SFT | 8-9 | 4 | Format-competent policy |
| 5. GRPO | 10-13 | 8-16 | Trained agent |
| 6. Analysis | 13-16 | 1-2 | Probes, faithfulness, regret decomposition |

GPUs are irrelevant for the first seven weeks. Request the allocation late.

### 6.1 Phase 2 — the generator is an experiment-design tool

Generate, solve, bucket by optimal solution length, discard unsolvable. Then
*separately* hand-design **minimal-pair sets**: levels A and B differing in
exactly one mechanic, matched on size and optimal solution length. These are
experimental stimuli, not a test set, and they are where the eventual claims get
their teeth.

### 6.2 Phase 6 — analysis

- Linear probes for distance-to-goal and dead-state, **split by level** so probe
  training does not leak across states of the same puzzle.
- Per-move regret against the optimal action set.
- Minimal-pair behavioural tests.
- CoT faithfulness: does stated reasoning predict the chosen action better or
  worse than activations do? Answerable here because ground truth exists.

### 6.3 Control experiment

A ~10M-parameter from-scratch policy network, trained around Phase 2-3. Cheap
(days, one GPU). It establishes which heuristics this environment affords *at
all*, which is the baseline that makes the 8B result interpretable rather than a
bare number.

---

## 7. Evaluation design

- **Primary test set:** held-out procedurally generated levels.
- **OOD check:** the 120 official levels, held out entirely from training.

### 7.1 Solve rate, defined

> Fraction of held-out levels reaching a goal state within **2x the oracle's
> optimal solution length**, pass@1, greedy decode, **no undo available**.

Each clause is load-bearing:

- **Budget tied to `d*`.** The Phase 1 oracle supplies optimal solution length
  free, so the budget adapts per level rather than arbitrarily penalising long
  puzzles. The 2x multiplier is fixed once, before results are inspected.
- **No undo in the primary metric.** SSR grants unlimited free undo. Exposed to
  the model without a budget, a random walker eventually solves any level — the
  metric would measure environment-mediated brute force, precisely what §3.3
  excludes. Undo returns as a *separate* measurement (solve rate with undo
  permitted, same budget); the gap between the two quantifies how much the model
  offloads to environment search. That gap is a result, not a confound, and
  parallels the policy-alone vs policy-plus-search comparison in §3.3.
- **Reported per difficulty band, never pooled.** A pooled figure is largely an
  artifact of how many easy levels the generator emitted, and is gameable by
  reweighting the test set. Report a curve over optimal solution length.
- **pass@1 greedy is the headline**; pass@k is reported alongside as a diversity
  measure, not as the score.

For the 120 official levels no `d*` exists on the hard ones (enumeration will not
finish). Use the `.dem` trace length as the budget there: it is a valid upper
bound on optimal, being a real winning trace, and a generous one since those
traces wander.

**Phase 0 consequence:** `step()` must expose undo as an explicitly *switchable*
capability. Replay validation requires it (`5-1.dem` uses `Undo`), while the
primary metric requires withholding it.

The official levels serve a specific methodological purpose: if the model is
trained and probed only on generated levels, apparent "heuristics" may be
artifacts of the generator's distributional biases. The official levels were
designed by a human with different intent and act as the independent check.

---

## 8. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Phase 0 slips, silently | High | Hard gate on 120/120 replays; no Phase 1 work until green |
| Generator bias contaminates all Phase 6 claims | High | Official levels held out as OOD check (§7) |
| Oracle intractable at useful difficulty | Medium | Generator difficulty capped at enumerable sizes |
| Model plateaus at trivial solve rate | Medium | Curriculum depth; SFT bootstrap; accept narrower claims |
| Episode length makes Phase 5 rollouts unaffordable | High | See §8.1 |
| Dead-state simulation wrong, poisoning main probe target | High | Human differential testing targets exactly this (§5.2) |

---

### 8.1 Episode length (raised by the §2 corpus measurement)

Official solution lengths (median 104, max 1301) interact badly with §4.3's
one-move-per-turn design. Each turn is a separate generation whose prompt carries
the conversation so far, so naive prefill cost over an `N`-move episode is
`O(N^2)`, multiplied again by the GRPO group size.

Mitigations, in order of preference:

1. **Small generated levels.** The §4.1 tractability bound already caps generated
   levels well below official sizes; target optimal solution lengths of ~30 moves.
   The oracle constraint and the rollout-cost constraint point the same way, which
   is fortunate.
2. **vLLM prefix caching.** Turn `k+1`'s prompt extends turn `k`'s, so the shared
   prefix is cacheable and the quadratic term largely collapses. Verify this is
   actually active in the verl rollout path — it is the single largest lever.
3. **Cap per-move reasoning tokens.** A hard budget per turn, tuned in Phase 4.
4. **Sliding history window** (last `k` states rather than full history) only if
   1-3 prove insufficient. It changes what the model can condition on and
   therefore what the probes in §6.2 are measuring, so it is a last resort.

**Consequence for evaluation.** World 6 levels are out of scope as RL targets on
length grounds alone, independent of the §4.1 oracle bound. Both constraints
exclude the same material. They remain usable as qualitative OOD probes (§7.1).

---

## 9. Open questions

- Exact tractability ceiling for full enumeration — measure empirically in Phase 1
  rather than estimating, then set generator bounds from the measurement.
- Whether LoRA suffices for SFT or full fine-tuning is needed. Decide in Phase 4
  from observed solve rates.
- Level extraction path from Unity assets (AssetRipper) is assumed workable but
  unverified. Confirm in week 1 — it is a hard dependency for §5.1.

---

## 10. Dependencies

- Stephen's Sausage Roll, installed (owned).
- `.dem` solution files from SSRDecompile.
- Cluster allocation, 4-16 H100s, from week 7.
