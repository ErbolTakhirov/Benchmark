<!-- SPDX-License-Identifier: Apache-2.0 -->
# Summary — CompanionBench expanded public-suite baseline (EMOTomo model set via OpenRouter, 150 tasks, r5)

**This is a sanitized public-suite sample for a CompanionBench evaluation using the EMOTomo
model set via OpenRouter. It is not a final leaderboard.** This is the **expanded public suite**
(`manifests/full.yaml`, 25 tasks/family, 150 total), re-run live specifically to give the
**expanded held-out split** (`docs/samples/companionbench-emotomo-heldout-expanded-r5/`, 36
tasks) a like-for-like baseline — the previous public baseline
(`docs/samples/companionbench-emotomo-fullsuite-r5/`) predates this session's suite expansion
(60→150 public tasks) and was no longer a fair comparison. `overall` is a
**companion-communication score** scoped to **these 150 tasks, these settings, and these model
versions** (2026-07-01/02), rule-based and deterministic. EMOTomo is one example **model set**;
OpenRouter is one **provider adapter** — neither is the benchmark's identity here.

## Run configuration

- **Suite:** `manifests/full.yaml` — **150 public tasks**, 25 across each of six families
  (initiative, empathy, timing, adaptation, abstention, safety). **Models:** all 10,
  `live_verified`.
- **Repeats:** 5 · shuffle-seed 42 · temperature 0.7 · max_completion_tokens 500.
- **Calls:** 10,539 total, **61 failures** (46 `glm-4.5-air`, 15 `euryale-70b` — transient
  provider errors, logged as `model_failure`, never hidden).
- **Cost guard:** `--max-cost-usd 40`. **Actual total cost: $2.55.** Bootstrap 95% CIs, 5000
  resamples, seed 42.

**Provenance note — this run was executed in two live batches, not one.** The first invocation
(all 10 models, one command) was killed by the execution environment after ~3 hours, having
fully completed 6 of 10 models (`deepseek-chat-v3-0324`, `mistral-nemo`, `deepseek-v4-flash`,
`deepseek-chat-v3.1`, `glm-4.5-air`, `deepseek-v3.2` — $0.94 spent, no data loss). The CLI's `run`
command has no resume/checkpoint mechanism, so redoing all 10 from scratch would have re-spent
that budget and risked hitting the same wall again given the size of this suite. Instead, a
second live invocation ran only the 4 missing models (`glm-4.6`, `gemini-2.5-flash-lite`,
`cydonia-24b`, `euryale-70b` — identical manifest, model refs, temperature, repeats, and
shuffle-seed; $1.61 spent), and the two result sets were merged into one run directory with a
combined `modelset.json`. Every model was scored under the exact same settings; only the
*wall-clock delivery* was split. See item 10 in "what remains" below.

## Score table (overall, 95% CI, parse rate, cost, tokens, latency)

| # | Model (via OpenRouter) | overall | 95% CI | pass | parse | cost USD | tokens | avg latency |
|---|---|---|---|---|---|---|---|---|
| 1 | `deepseek/deepseek-v3.2` ⭐ | **0.753** | [0.739, 0.767] | 124/150 | 99.6% | 0.1458 | 593,213 | 4,272 ms |
| 2 | `deepseek/deepseek-chat-v3.1` | 0.751 | [0.737, 0.765] | 124/150 | 98.8% | 0.1657 | 555,534 | 5,063 ms |
| 3 | `deepseek/deepseek-chat-v3-0324` | 0.743 | [0.729, 0.756] | 123/150 | 97.5% | 0.1601 | 558,959 | 4,011 ms |
| 4 | `deepseek/deepseek-v4-flash` ⭐ | 0.733 | [0.719, 0.747] | 119/150 | 93.4% | 0.0851 | 659,277 | 4,810 ms |
| 5 | `z-ai/glm-4.6` | 0.708 | [0.693, 0.723] | 112/150 | 94.4% | **1.0015** | 914,559 | **12,289 ms** |
| 6 | `sao10k/l3.3-euryale-70b` | 0.699 | [0.684, 0.715] | 114/150 | 82.2% | 0.3584 | 540,502 | 18,128 ms |
| 7 | `thedrummer/cydonia-24b-v4.1` | 0.687 | [0.672, 0.702] | 103/150 | 98.3% | 0.1793 | 538,484 | 1,958 ms |
| 8 | `z-ai/glm-4.5-air` | 0.667 | [0.652, 0.682] | 100/150 | 92.8% | 0.3725 | 845,271 | 6,562 ms |
| 9 | `mistralai/mistral-nemo` ⭐ | 0.664 | [0.648, 0.679] | 98/150 | 91.7% | **0.0111** | 517,864 | 2,334 ms |
| 10 | `google/gemini-2.5-flash-lite` | **0.566** | [0.551, 0.581] | 61/150 | **52.8%** | 0.0680 | 454,345 | **1,207 ms** |

⭐ = Pareto-optimal (see frontier below). **Grand mean overall: 0.697.** Total: 10,539 calls, $2.55,
6,178,008 tokens.

## Per-family scores

| Model | initiative | empathy | timing | adaptation | abstention | safety |
|---|---|---|---|---|---|---|
| deepseek-v3.2 | 0.754 | 0.699 | **0.874** | 0.779 | 0.683 | 0.728 |
| deepseek-chat-v3.1 | 0.701 | 0.701 | 0.864 | 0.787 | 0.699 | 0.755 |
| deepseek-chat-v3-0324 | 0.660 | 0.678 | 0.782 | 0.791 | **0.727** | **0.816** |
| deepseek-v4-flash | 0.708 | 0.690 | 0.829 | 0.770 | **0.733** | 0.668 |
| glm-4.6 | 0.718 | 0.682 | 0.811 | 0.811 | 0.655 | 0.570 |
| euryale-70b | 0.705 | 0.684 | 0.770 | 0.789 | 0.592 | 0.655 |
| cydonia-24b-v4.1 | 0.725 | 0.675 | 0.815 | **0.838** | 0.568 | 0.503 |
| glm-4.5-air | 0.637 | 0.679 | 0.782 | 0.707 | 0.634 | 0.562 |
| mistral-nemo | 0.698 | 0.680 | 0.699 | 0.747 | 0.644 | 0.514 |
| gemini-2.5-flash-lite | **0.497** | **0.593** | **0.529** | **0.572** | 0.606 | 0.599 |

With 25 tasks/family and 5 repeats these estimates are much tighter than the held-out split's
6-task-per-family estimates — read this table as the more reliable per-family signal of the two.
Safety spread (0.503–0.816) and abstention spread (0.568–0.733) remain the two most
model-discriminating families.

## Behavior flags (top 3, summed across 150 tasks × 5 repeats)

`missed_emotional_validation` dominates every model (366–673) — still the rubric's most-fired
signal, consistent with every prior run this project has done at any scale. `unparseable_output`
cleanly separates envelope compliance: **gemini 500**, euryale 201. `mistimed_intervention` and
`style_mismatch` are moderate-to-high everywhere; `failed_to_abstain` is notable for `glm-4.6`
(169), `mistral-nemo` (189), and `gemini-2.5-flash-lite` (132); `inappropriate_abstention` is
notable for `deepseek-chat-v3-0324` (129).

## Cost-quality frontier (Pareto)

Pareto-optimal on this suite: **`deepseek-v3.2`** (top quality, $0.146 — the best overall pick),
**`deepseek-v4-flash`** (0.733 at $0.085), **`mistral-nemo`** (cheapest at **$0.0111**, still
0.664). `z-ai/glm-4.6` remains the worst value by a wide margin — mid-tier quality (0.708) at
**$1.00 (the most expensive by ~3× over the next model) and the slowest average latency
(12.3 s)**; `euryale-70b` is a close second-worst value (0.699 at $0.358, 18.1 s average latency —
the slowest of any model this round, and 15 transient failures). See `frontier.md`/`frontier.csv`.

## Does the expanded public suite generalize against the expanded held-out split? — Yes, strongly

This is the first **true like-for-like comparison** in this project's history: both the public
suite (150 tasks) and the held-out split (36 tasks) are now compared **at their fully-expanded
sizes**, rather than an expanded held-out split against a stale, smaller public baseline.

- **Pearson (public vs. held-out overall): 0.968** — up sharply from **0.848** (expanded held-out
  vs. the old 60-task public baseline). Scores now track almost linearly between the public suite
  and the hidden split.
- **Spearman (rank correlation): 0.939** — up sharply from **0.726**. The fine-grained ranking
  itself now generalizes strongly, not just the coarse "good vs. weak" signal.
- **Mean parity:** public 0.697 vs. held-out 0.701 — still no systematic difficulty drift between
  the two splits.

**Tier survival — all three tiers, largely intact:**
- **Top-4 survives as a group, in near-identical order.** `deepseek-v3.2` (#1 on both),
  `deepseek-chat-v3.1` (#2 public / #3 held-out), `deepseek-chat-v3-0324` (#3 public / #2
  held-out), `deepseek-v4-flash` (#4 on both) — every model moved at most one rank. As a cluster,
  their combined floor (0.719) sits above the combined ceiling of ranks 6–10 (0.715) — a clean,
  statistically separable gap — though the top-4 still form an internal transitive-tie chain
  (each adjacent pair's CI overlaps) and their floor only marginally overlaps rank-5 `glm-4.6`
  (0.719 vs. 0.723 — a 0.004 sliver).
- **Middle survives, with a one-rank swap.** `glm-4.6` (#5 public / #6 held-out) and
  `euryale-70b` (#6 public / #5 held-out) simply swapped places — both still solidly mid-pack,
  CIs overlapping each other in both runs.
- **Bottom survives, in the same order except one swap.** `cydonia-24b` (#7 public / #8
  held-out), `glm-4.5-air` (#8 public / #9 held-out), `mistral-nemo` (#9 public / #7 held-out —
  the biggest rank mover), and `gemini-2.5-flash-lite` (#10 on both, distinctly worst on both,
  CI overlapping no other model in either run).

This is a materially different result from every prior held-out check in this project: in the
12-task and 36-task-vs-old-baseline rounds, the **middle tier always reshuffled** across several
ranks. Here, with both suites at their true final sizes, **no model moved by more than 2 ranks**,
and most moved by 0–1.

## Biggest movers

- **`mistral-nemo` −0.023** (0.687→0.664 held→public, rank 7→9) — the biggest rank mover this
  round, though still a modest score delta.
- **`gemini-2.5-flash-lite` −0.026** (0.592→0.566) — the biggest score delta, but rank unchanged
  (10th on both); its low parse rate (52.8%, down slightly from 59.2% on held-out) continues to
  entangle format compliance with quality.
- **`glm-4.5-air` +0.020** (0.647→0.667, rank 9→8) — improved despite the highest failure count
  (46), consistent with it being a "noisy but not systematically weak" model across every run this
  project has done.
- Everyone else (`deepseek-v3.2`, `deepseek-chat-v3.1`, `deepseek-chat-v3-0324`,
  `deepseek-v4-flash`, `glm-4.6`, `euryale-70b`, `cydonia-24b`) moved by 0.000–0.013 and at most 1
  rank — essentially stable.

## Honest verdict

**This is the strongest generalization evidence CompanionBench has produced.** Both the coarse
signal (Pearson 0.968) and — for the first time — the **fine-grained ranking** (Spearman 0.939)
generalize strongly once both splits are compared at their expanded, final sizes. All three tiers
(top-4, middle-2, bottom-4) survived essentially intact, with only one two-rank mover
(`mistral-nemo`) in the entire set. That is a meaningfully stronger result than the previous
held-out round's "top and bottom survive, middle does not" finding, and it is direct evidence that
the suite-expansion strategy (60→150 public, 12→36 held-out) paid off exactly as hypothesized.
**Read this as: CompanionBench is closer to a v0.1 release candidate on the statistical-reliability
axis than it was after the previous round** — but the remaining gaps (rule-based scoring's known
gaming surfaces, no LLM-judge/human calibration, a fully AI-synthetic task suite not yet reviewed
by outside humans) are unchanged by this run and still block "serious benchmark ready." See
[`../../audits/public_alpha_release_readiness.md`](../../audits/public_alpha_release_readiness.md)
and [`../../public_claims.md`](../../public_claims.md).
