<!-- SPDX-License-Identifier: Apache-2.0 -->
# Summary — CompanionBench evaluation using the EMOTomo model set via OpenRouter (capped audit run)

**This is a sanitized sample run for benchmark-quality verification. It is a scoped benchmark run.**
Scores are scoped to **these 8 tasks, these settings, and these model versions** (run 2026-06-30),
produced by **rule-based, deterministic** scoring. Differences below are **not statistically
separable** — the 95% bootstrap CIs overlap heavily. EMOTomo is one example **model set**; OpenRouter
is one **provider adapter**, each recorded as run metadata.

## Run configuration

- **Manifest:** `manifests/emotomo_smoke.yaml` — 8 tasks, 2 each in `initiative`, `empathy`,
  `timing`, `adaptation`.
- **Model set:** `configs/model_sets/emotomo-openrouter.yaml` (4 enabled, all `live_verified`).
- **Settings:** `--repeats 2 --shuffle-seed 42`, `temperature 0.7`, `max_completion_tokens 500`.
- **Cost guard:** `--max-cost-usd 3`. **Actual total cost: $0.0147.**
- **Scoring:** rule-based; **bootstrap 95% CIs**, 2000 resamples, seed 42. `(task, repeat)` units.

## Overall (companion-communication composite — NOT a "humanity" score)

| Model (via OpenRouter) | overall | 95% CI | parsed | failures | tokens | cost USD | avg latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek/deepseek-chat-v3-0324` | **0.735** | [0.64, 0.82] | 28/28 (100%) | 0 | 13,532 | 0.003851 | 4,944 ms |
| `mistralai/mistral-nemo` | 0.688 | [0.58, 0.79] | 22/28 (79%) | 0 | 12,779 | **0.000273** | 2,937 ms |
| `z-ai/glm-4.5-air` | 0.670 | [0.57, 0.77] | 23/25 (92%) | 3 | 19,834 | 0.008778 | 7,589 ms |
| `google/gemini-2.5-flash-lite` | 0.622 | [0.54, 0.71] | 15/28 (54%) | 0 | 12,750 | 0.001824 | **1,017 ms** |

Totals: **4 models · 4 families · 2 repeats · 109 successful calls · 3 failures** (all on
`glm-4.5-air`, logged as `model_failure` events, never hidden).

## Per-dimension (mean; n/a = dimension never applied on a scorable probe)

| Model | initiative | timing | empathy | adaptation | abstention | safety |
| --- | --- | --- | --- | --- | --- | --- |
| `deepseek-chat-v3-0324` | 0.641 | 0.867 | 0.496 | 1.000 | 0.500 | 1.000 |
| `mistral-nemo` | 0.523 | 0.909 | 0.548 | 1.000 | 1.000 | 1.000 |
| `glm-4.5-air` | 0.562 | 0.857 | 0.549 | 0.500 | 1.000 | 1.000 |
| `gemini-2.5-flash-lite` | 0.334 | 1.000 | 0.500 | n/a | 0.000 | 1.000 |

(Per-dimension 95% CIs are in each model's `scores.json` → `dimension_ci`; they are wide on this
tiny suite, e.g. `deepseek` abstention spans [0.0, 1.0].)

## Behavior flags (top, counts across probes × repeats)

| Model | most frequent named flags |
| --- | --- |
| `deepseek-chat-v3-0324` | missed_emotional_validation ×14 · style_mismatch ×7 · inappropriate_abstention ×4 |
| `mistral-nemo` | missed_emotional_validation ×11 · unparseable_output ×6 · waited_when_validation_needed ×3 |
| `glm-4.5-air` | missed_emotional_validation ×12 · style_mismatch ×5 · unparseable_output ×5 · generic_empathy ×3 |
| `gemini-2.5-flash-lite` | unparseable_output ×13 · missed_emotional_validation ×8 · waited_when_validation_needed ×3 |

`missed_emotional_validation` and `generic_empathy` are **newly surfaced** in this audit (the scorer
emitted the underlying signals but previously dropped them). They are now the most informative
cross-model diagnostics. No `unsafe_overreach` flags fired (see safety caveat below).

## Cost-quality frontier (Pareto)

- **Pareto-optimal:** `deepseek/deepseek-chat-v3-0324` (top quality) and `mistralai/mistral-nemo`
  (near-top quality at ~1/14th the cost — the value pick).
- **Dominated:** `z-ai/glm-4.5-air` (lower quality *and* most expensive + slowest) and
  `google/gemini-2.5-flash-lite` (lower quality than mistral-nemo, and pricier). See `frontier.md`.

## How to read this (caveats that change the conclusion)

1. **Not separable.** All four CIs overlap; on 8 tasks × 2 repeats no model is a statistically
   distinguishable "winner". Treat the ordering as illustrative, not a ranking.
2. **Parse-rate confound.** `gemini-2.5-flash-lite` returned a valid `CompanionTurn` envelope only
   **54%** of the time (13 `unparseable_output`); unparseable turns score 0 on initiative/abstention,
   so its low score reflects **JSON-envelope non-compliance**, not necessarily worse companion
   behavior. `mistral-nemo` (79%) is similarly affected. This is the documented structured-envelope
   limitation, not a model-quality verdict.
3. **Safety is uninformative here.** Every model scored 1.000 — the 8-task suite barely stresses
   safety (it is a cross-cutting dimension, not its own family), and safety is an authored-pattern
   blocklist. **A high safety score is not a safety certification.**
4. **Empathy looks uniformly low** (~0.50–0.55) with pervasive `missed_emotional_validation`. This is
   partly a real signal and partly the rule-based rubric matching **substrings** of authored
   validation phrases — paraphrased validation can be under-credited. Read it as "worth a human
   look", not as proof.
5. **Rule-based = blunt.** Deterministic and reproducible, but it cannot judge nuance and is gameable
   by keyword overlap. No LLM-judge or human calibration was used.

See [`../../audits/benchmark_quality_audit.md`](../../audits/benchmark_quality_audit.md) and
[`../../public_claims.md`](../../public_claims.md).
