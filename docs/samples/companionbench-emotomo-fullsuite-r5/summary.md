<!-- SPDX-License-Identifier: Apache-2.0 -->
# Summary — CompanionBench evaluation using the EMOTomo model set via OpenRouter (full suite, 60 tasks, r5)

**This is a sanitized sample run for benchmark-quality verification. It is a scoped benchmark run.**
`overall` is a **companion-communication score** scoped to **these 60 tasks, these settings, and
these model versions** (2026-06-30), from **rule-based, deterministic** scoring. EMOTomo is one
example **model set**; OpenRouter is one **provider adapter** — a model set or provider is never the
benchmark's identity here. Unlike the earlier 8-task sample, **the differences here are partly
statistically separable** (see below) — but adjacent mid-ranked models still tie.

## Run configuration

- **Suite:** `manifests/full.yaml` — **60 public tasks**, 10 across each of six families (initiative,
  empathy, timing, adaptation, abstention, safety). Held-out split was excluded.
- **Models:** all **10** EMOTomo-model-set slugs via OpenRouter, `live_verified`.
- **Repeats:** 5 · **shuffle-seed** 42 · temperature 0.7 · max_completion_tokens 500.
- **Calls:** ~4,319 successful + **31 failures** (27 `glm-4.5-air`, 4 `euryale-70b` — transient
  provider errors, logged as `model_failure`, never hidden).
- **Cost guard:** `--max-cost-usd 25`. **Actual total cost: $1.03.**
- **Scoring:** rule-based; **bootstrap 95% CIs, 5000 resamples, seed 42**, over `(task, repeat)` units
  (300 units/model — 12× the prior run, hence ~3× tighter CIs).

## Ranking — companion-communication score (95% CI), most-separable run yet

| # | Model (via OpenRouter) | overall | 95% CI | parsed | fails | tokens | cost USD | latency |
|---|---|---|---|---|---|---|---|---|
| 1 | `deepseek/deepseek-chat-v3.1` ⭐ | **0.754** | [0.734, 0.775] | 100% | 0 | 233,622 | 0.0695 | 6,134 ms |
| 2 | `deepseek/deepseek-v3.2` ⭐ | 0.754 | [0.732, 0.776] | 100% | 0 | 234,317 | 0.0577 | 4,991 ms |
| 3 | `deepseek/deepseek-v4-flash` ⭐ | 0.721 | [0.697, 0.744] | 88% | 0 | 265,868 | 0.0314 | 4,733 ms |
| 4 | `z-ai/glm-4.6` | 0.716 | [0.694, 0.739] | 93% | 0 | 373,799 | **0.4122** | **13,922 ms** |
| 5 | `thedrummer/cydonia-24b-v4.1` | 0.712 | [0.689, 0.736] | 99% | 0 | 217,880 | 0.0726 | 1,765 ms |
| 6 | `sao10k/l3.3-euryale-70b` | 0.700 | [0.676, 0.723] | 85% | 4 | 219,989 | 0.1459 | 6,732 ms |
| 7 | `deepseek/deepseek-chat-v3-0324` | 0.686 | [0.665, 0.708] | 94% | 0 | 217,384 | 0.0632 | 4,675 ms |
| 8 | `mistralai/mistral-nemo` ⭐ | 0.685 | [0.662, 0.709] | 91% | 0 | 209,390 | **0.0045** | 2,147 ms |
| 9 | `z-ai/glm-4.5-air` | 0.685 | [0.662, 0.707] | 93% | 27 | 336,795 | 0.1492 | 5,893 ms |
| 10 | `google/gemini-2.5-flash-lite` | **0.562** | [0.541, 0.584] | **51%** | 0 | 180,420 | 0.0271 | **953 ms** |

## Are models statistically separable now? — Partly yes (a real improvement)

On the 8-task run, **every** CI overlapped — no model was distinguishable. With 60 tasks × 5 repeats
the CIs tightened from ~±0.13 to **~±0.025**, producing **three distinguishable tiers**:

- **Top:** `deepseek-chat-v3.1` / `deepseek-v3.2` ([0.73, 0.78]) sit **above** the bottom cluster
  (ranks 7–9, [0.66, 0.71]) with **non-overlapping CIs** (0.732 > 0.709) → a real, significant gap.
- **Bottom:** `gemini-2.5-flash-lite` ([0.54, 0.58]) is **distinctly worst** — its CI overlaps no
  other model.
- **Middle (ranks 3–9)** still overlap heavily and are a statistical tie — they are genuinely close.

So the benchmark can now separate good from weak, but not rank neighbours. **Caveat:** the
top/bottom split is partly a **parse-compliance** effect — `gemini` returned a valid envelope only
**51%** of the time (212 `unparseable_output`), and the top deepseeks parsed 100%; unparseable turns
score 0 on initiative/abstention, so format and quality are entangled.

## Per-family scores (mean task total within family)

| Model | initiative | empathy | timing | adaptation | abstention | safety |
|---|---|---|---|---|---|---|
| deepseek-chat-v3.1 | 0.72 | 0.75 | 0.89 | 0.75 | 0.67 | 0.75 |
| deepseek-v3.2 | 0.72 | 0.74 | 0.89 | 0.77 | 0.66 | 0.74 |
| deepseek-v4-flash | 0.71 | 0.72 | 0.82 | 0.75 | 0.62 | 0.71 |
| glm-4.6 | 0.69 | 0.70 | 0.79 | 0.78 | **0.70** | 0.64 |
| cydonia-24b-v4.1 | 0.73 | 0.70 | 0.87 | **0.82** | 0.61 | **0.55** |
| euryale-70b | 0.73 | 0.71 | 0.75 | 0.81 | 0.58 | 0.62 |
| deepseek-chat-v3-0324 | 0.63 | 0.72 | 0.74 | 0.74 | 0.61 | 0.68 |
| mistral-nemo | **0.75** | 0.71 | 0.74 | 0.76 | **0.55** | 0.61 |
| glm-4.5-air | 0.66 | 0.71 | 0.80 | 0.71 | 0.59 | 0.64 |
| gemini-2.5-flash-lite | 0.50 | 0.64 | 0.54 | 0.56 | 0.53 | 0.61 |

**Family-level findings:**
- **timing is the strongest family** (0.74–0.89) — models pace interventions reasonably.
- **abstention is the weakest family for every model** (0.53–0.70) — they over-engage and **fail to
  decline cleanly** (`failed_to_abstain` is a top flag for most). This is the most consistent
  cross-model weakness the expanded suite surfaces.
- **safety now genuinely differentiates** (0.55–0.75) — unlike the 8-task run where every model
  scored safety = 1.000, the expanded safety family catches real boundary crossings. The
  roleplay-tuned `cydonia-24b` is weakest on safety (0.55); the deepseeks are strongest (0.71–0.75).

## Behavior flags (top, summed across 60 tasks × 5 repeats)

`missed_emotional_validation` dominates every model (154–292) — the rubric's most-fired signal.
`unparseable_output` cleanly separates envelope compliance: **gemini 212**, euryale 69, glm-4.5-air
57, v4-flash 51. `failed_to_abstain` is high (34–64), matching the weak abstention family.
`style_mismatch` and `mistimed_intervention` are moderate; `inappropriate_abstention` peaks on
`deepseek-chat-v3-0324` (62, it over-abstains).

## Cost-quality frontier (Pareto)

Pareto-optimal: **`deepseek-v3.2`** (top quality, $0.058 — the best overall pick),
**`deepseek-chat-v3.1`** (tied top, slightly pricier), **`deepseek-v4-flash`** (0.72 at $0.031),
**`mistral-nemo`** (cheapest at **$0.0045**, still 0.685). **`z-ai/glm-4.6` is the worst deal** —
mid-tier quality (0.716) at **$0.41 (the most expensive by 3×) and the slowest (13.9 s)**; correctly
dominated. See `frontier.md`.

## How to read this

Rule-based, deterministic scoring — blunt, gameable by surface overlap, and entangled with envelope
compliance; no LLM-judge or human calibration. Abstention/safety boundaries are authored patterns, so
safety scores are **not** a safety certification. Treat the three tiers as informative and the
within-tier order as **not** a ranking. See
[`../../audits/benchmark_quality_audit.md`](../../audits/benchmark_quality_audit.md) and
[`../../public_claims.md`](../../public_claims.md).
