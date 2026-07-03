<!-- SPDX-License-Identifier: Apache-2.0 -->
# Results — v0.1.0-alpha

This is the results writeup for the **v0.1.0-alpha** release: a CompanionBench evaluation using
the EMOTomo model set via OpenRouter, across the full public task suite and the held-out
validation split. Read it as a **scoped benchmark run** — read
[`results_interpretation.md`](results_interpretation.md) and [`public_claims.md`](public_claims.md)
alongside this page, and see [Conservative interpretation](#conservative-interpretation) below
before drawing conclusions from any single number here.

`overall` is a **companion-communication score** scoped to these tasks, these settings, and these
model versions (2026-07-01/02). EMOTomo is one example **model set** and OpenRouter one example
**provider adapter**, each recorded as run metadata.

## Run configuration

| | Public suite | Held-out split |
| --- | --- | --- |
| Manifest | `manifests/full.yaml` | `manifests/heldout.yaml` |
| Tasks | 150 (25 × 6 families) | 36 (6 × 6 families) |
| Models | 10, all `live_verified` via `configs/model_sets/emotomo-openrouter.yaml` | same 10 |
| Repeats / shuffle-seed | 5 / 42 | 5 / 42 |
| Scoring | rule-based; bootstrap 95% CI, 5000 resamples, seed 42 | same |
| Total cost | $2.55 | $0.59 |
| Calls / failures | 10,539 / 61 (46 `glm-4.5-air`, 15 `euryale-70b`) | 2,517 / 33 (31 `glm-4.5-air`, 2 `euryale-70b`) |

Nothing was tuned on either run — tasks and scoring were frozen before both. Sanitized samples
(no raw transcripts, `events.jsonl`/`run.json` excluded):
[`../docs/samples/companionbench-emotomo-public-expanded-r5/`](samples/companionbench-emotomo-public-expanded-r5/)
and
[`../docs/samples/companionbench-emotomo-heldout-expanded-r5/`](samples/companionbench-emotomo-heldout-expanded-r5/).

The public-suite run's live API calls were split across two invocations (the first was killed by
the execution environment after completing 6/10 models cleanly; a second invocation completed the
remaining 4 under identical settings) — see that sample's own README for the full provenance note.
Every model was evaluated under identical settings; only the wall-clock delivery was split.

## Public suite — score table

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

⭐ = Pareto-optimal. Grand mean overall: 0.697. Parse rate is the share of turns that returned a
valid structured envelope — a low parse rate (e.g. `gemini-2.5-flash-lite` at 52.8%) drags `overall`
down for format-compliance reasons, separate from companion-communication quality; see
[Parse-format entanglement](../README.md#limitations).

## Pareto-optimal models (cost-quality frontier)

- **`deepseek/deepseek-v3.2`** — top quality (0.753) at $0.146 for all 150 tasks. The best overall
  pick on this suite.
- **`deepseek/deepseek-v4-flash`** — 0.733 at $0.085, the best quality-per-dollar among the
  higher-scoring models.
- **`mistralai/mistral-nemo`** — cheapest Pareto-optimal option at **$0.0111**, still scoring 0.664.

`z-ai/glm-4.6` is the worst value by a wide margin: mid-tier quality (0.708) at **$1.00 (~3× the
next most expensive model) and the slowest average latency (12.3 s)**. `sao10k/l3.3-euryale-70b` is
a close second-worst value (0.699 at $0.358, 18.1 s average latency — the slowest of any model this
round, and the highest failure count after `glm-4.5-air`). Full table:
[`../docs/samples/companionbench-emotomo-public-expanded-r5/frontier.md`](samples/companionbench-emotomo-public-expanded-r5/frontier.md).

## Public suite vs. held-out generalization

This is the first **true like-for-like comparison** in this project's history: both the public
suite (150 tasks) and the held-out split (36 tasks) are compared **at their fully-expanded sizes**,
rather than a larger held-out split against a stale, smaller public baseline.

- **Pearson (public vs. held-out overall): 0.968** — up sharply from an earlier reading of **0.848**
  (the expanded held-out split compared against a now-superseded, smaller public baseline). Scores
  now track almost linearly between the public suite and the hidden split.
- **Spearman (rank correlation): 0.939** — up sharply from **0.726** on that same earlier
  comparison. The fine-grained ranking itself now generalizes strongly, not just the coarse
  "good vs. weak" signal.
- **Mean parity:** public 0.697 vs. held-out 0.701 — no systematic difficulty drift between the
  two splits.

**Tier survival:** the top-4 (`deepseek-v3.2`, `deepseek-chat-v3.1`, `deepseek-chat-v3-0324`,
`deepseek-v4-flash`) survive as a group in near-identical order and are statistically separable
from ranks 6–10; the middle (`glm-4.6`, `euryale-70b`) and bottom four survive with at most a
one-rank swap each. The single biggest mover across both splits is `mistral-nemo` (rank 7 on
held-out → rank 9 on public) — a real but modest score change (0.687 → 0.664), not a tier jump.
`gemini-2.5-flash-lite` is distinctly worst on both splits, with no CI overlap against any other
model in either run.

Held-out suite score table (same models, same settings, 36 tasks):

| # | Model (via OpenRouter) | overall | 95% CI | pass | parse |
|---|---|---|---|---|---|
| 1 | `deepseek/deepseek-v3.2` | **0.756** | [0.726, 0.786] | 31/36 | 98.8% |
| 2 | `deepseek/deepseek-chat-v3-0324` | 0.753 | [0.725, 0.781] | 30/36 | 94.9% |
| 3 | `deepseek/deepseek-chat-v3.1` | 0.751 | [0.722, 0.780] | 31/36 | 96.1% |
| 4 | `deepseek/deepseek-v4-flash` | 0.720 | [0.689, 0.751] | 27/36 | 95.7% |
| 5 | `sao10k/l3.3-euryale-70b` | 0.712 | [0.681, 0.741] | 30/36 | 78.3% |
| 6 | `z-ai/glm-4.6` | 0.710 | [0.678, 0.741] | 28/36 | 97.3% |
| 7 | `mistralai/mistral-nemo` | 0.687 | [0.656, 0.718] | 26/36 | 90.6% |
| 8 | `thedrummer/cydonia-24b-v4.1` | 0.684 | [0.652, 0.716] | 23/36 | 100% |
| 9 | `z-ai/glm-4.5-air` | 0.647 | [0.617, 0.677] | 24/36 | 91.1% |
| 10 | `google/gemini-2.5-flash-lite` | **0.592** | [0.560, 0.625] | 21/36 | **59.2%** |

Full breakdown (per-family, behavior flags, biggest movers):
[`../docs/samples/companionbench-emotomo-public-expanded-r5/summary.md`](samples/companionbench-emotomo-public-expanded-r5/summary.md)
and
[`../docs/samples/companionbench-emotomo-heldout-expanded-r5/summary.md`](samples/companionbench-emotomo-heldout-expanded-r5/summary.md).

## Conservative interpretation

**What this does show:**

- On this task suite, in this configuration, the ten evaluated models separate into a
  statistically distinguishable top tier, middle tier, and bottom tier — the gaps are not noise.
- The public suite's ranking is a reasonable proxy for how these models behave on tasks they were
  not directly measured against (strong Pearson/Spearman agreement with the held-out split).
- Cost and latency vary enormously (over 100× on cost, ~15× on latency) with only a loose
  relationship to score — cheap and fast models are not automatically worse here.
- Parse-rate / format compliance is a real, separable failure mode from communication quality for
  at least one model in this set.

**What this does NOT show:**

- A universal "best companion", generally "emotionally intelligent", or production-ready verdict —
  these are companion-*communication* scores on 186 authored, synthetic, English-language tasks,
  scoped to this suite, not a general-capability or safety certification.
- A precise ranking between adjacent models whose CIs overlap (e.g. within the top-4, or within
  the bottom-4) — treat those as statistical ties, not fine-grained orderings.
- That these results transfer to a different task suite, a different scoring method (rule-based
  only, no LLM-as-judge or human calibration yet), a different language, or future model versions —
  model identifiers are versioned as of 2026-07-01/02 and will drift.
- Anything about models or providers not in this model set — this is one example model set run
  through one example provider adapter, not a comparison of "all LLMs" or "all providers."

See [`benchmark_card.md`](benchmark_card.md) for the full intended-use and limitations statement,
and [`audits/public_alpha_release_readiness.md`](audits/public_alpha_release_readiness.md) for the
external-reviewer-style verdict on this release.
