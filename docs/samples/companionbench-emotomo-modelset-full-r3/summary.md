<!-- SPDX-License-Identifier: Apache-2.0 -->
# Summary — CompanionBench evaluation using the EMOTomo model set via OpenRouter (full run, 10 models, r3)

**This is a sanitized sample run for benchmark-quality verification. It is a scoped benchmark run.**
Scores are scoped to **these 8 tasks, these settings, and these model versions** (2026-06-30), from
**rule-based, deterministic** scoring. `overall` is a **companion-communication score**, not a
universal "humanity" score. EMOTomo is one example **model set**; OpenRouter is one **provider
adapter**. The differences below are **not statistically separable** — every 95% bootstrap CI
overlaps its neighbours.

## Run configuration

- **Models:** all **10** EMOTomo-model-set slugs, each `live_verified` on OpenRouter.
- **Tasks:** `manifests/emotomo_smoke.yaml` — 8 tasks, 2 each in initiative / empathy / timing / adaptation.
- **Repeats:** 3 · **shuffle-seed** 42 · temperature 0.7 · max_completion_tokens 500.
- **Calls:** ~415 (10×42, minus 5 failed on glm-4.5-air). **5 model_failure events** total (glm-4.5-air, transient provider errors — logged, never hidden).
- **Cost guard:** `--max-cost-usd 10`. **Actual total cost: $0.0973.**
- **Scoring:** rule-based; **bootstrap 95% CIs**, 5000 resamples, seed 42, over `(task, repeat)` units.

## Overall companion-communication score (sorted; ⭐ = Pareto-optimal)

| # | Model (via OpenRouter) | overall | 95% CI | parsed | fails | tokens | cost USD | latency |
|---|---|---|---|---|---|---|---|---|
| 1 | sao10k/l3.3-euryale-70b ⭐ | **0.795** | [0.73, 0.85] | 39/42 (93%) | 0 | 20,328 | 0.013463 | 5,202 ms |
| 2 | deepseek/deepseek-v3.2 ⭐ | 0.791 | [0.72, 0.86] | 42/42 (100%) | 0 | 20,272 | 0.004969 | 3,892 ms |
| 3 | thedrummer/cydonia-24b-v4.1 | 0.778 | [0.71, 0.84] | 42/42 (100%) | 0 | 19,982 | 0.006646 | 1,565 ms |
| 4 | deepseek/deepseek-v4-flash ⭐ | 0.777 | [0.69, 0.85] | 41/42 (98%) | 0 | 24,789 | 0.002972 | 5,525 ms |
| 5 | deepseek/deepseek-chat-v3.1 | 0.754 | [0.67, 0.83] | 42/42 (100%) | 0 | 20,606 | 0.006050 | 10,404 ms |
| 6 | z-ai/glm-4.6 | 0.742 | [0.66, 0.82] | 41/42 (98%) | 0 | 36,252 | **0.041025** | 12,974 ms |
| 7 | z-ai/glm-4.5-air | 0.729 | [0.64, 0.81] | 36/37 (97%) | **5** | 29,882 | 0.013471 | 8,620 ms |
| 8 | deepseek/deepseek-chat-v3-0324 | 0.705 | [0.63, 0.77] | 42/42 (100%) | 0 | 20,164 | 0.005710 | 4,199 ms |
| 9 | mistralai/mistral-nemo ⭐ | 0.684 | [0.60, 0.76] | 37/42 (88%) | 0 | 19,049 | **0.000405** | 1,961 ms |
| 10 | google/gemini-2.5-flash-lite | 0.650 | [0.57, 0.73] | **24/42 (57%)** | 0 | 18,139 | 0.002582 | **903 ms** |

## Per-dimension (mean; n/a = never applied on a scorable probe)

| Model | initiative | timing | empathy | adaptation | abstention | safety |
|---|---|---|---|---|---|---|
| euryale-70b | 0.73 | 0.95 | 0.48 | 1.00 | 1.00 | 1.00 |
| deepseek-v3.2 | 0.71 | 1.00 | 0.42 | 0.75 | 0.60 | 1.00 |
| cydonia-24b-v4.1 | 0.72 | 0.84 | 0.54 | 1.00 | 0.00 | 1.00 |
| deepseek-v4-flash | 0.69 | 0.85 | 0.61 | 1.00 | 0.67 | 1.00 |
| deepseek-chat-v3.1 | 0.68 | 0.86 | 0.49 | 1.00 | 0.60 | 1.00 |
| glm-4.6 | 0.65 | 0.85 | 0.53 | 1.00 | 0.67 | 1.00 |
| glm-4.5-air | 0.64 | 0.89 | 0.61 | 0.62 | 1.00 | 1.00 |
| deepseek-chat-v3-0324 | 0.56 | 0.85 | 0.51 | 1.00 | 0.43 | 1.00 |
| mistral-nemo | 0.53 | 0.89 | 0.49 | 1.00 | 0.33 | 1.00 |
| gemini-2.5-flash-lite | 0.38 | 1.00 | 0.53 | n/a | 0.67 | 1.00 |

(Per-dimension 95% CIs are in each model's `scores.json` → `dimension_ci`.)

## Behavior flags (most frequent, counts across 8 tasks × 3 repeats)

- **`missed_emotional_validation` dominates every model (11–25×)** — the single most consistent signal.
- **`unparseable_output`** cleanly separates envelope compliance: gemini-2.5-flash-lite 18, glm-4.5-air 6, mistral-nemo 5, euryale-70b 3 (the rest ~0).
- `style_mismatch` 4–12; `inappropriate_abstention` peaks on deepseek-chat-v3-0324 (8); `intrusive_advice` low everywhere (≤3); `waited_when_validation_needed` 3–7.

## Cost-quality frontier (Pareto)

The frontier is a sensible staircase (see `frontier.md`): **euryale-70b** (top quality) → **deepseek-v3.2** (near-top, ~3× cheaper) → **deepseek-v4-flash** (cheaper still) → **mistral-nemo** (cheapest, lowest-but-usable). **`z-ai/glm-4.6` is the worst deal** — mid quality at **$0.041 (10× the field) and the slowest (13 s)**; it is correctly dominated.

## Blunt verdict — is the benchmark useful or garbage?

**Verdict: the live pipeline works end-to-end and is a useful MVP differential profiler — but benchmark quality is gated by the tiny task suite; it cannot statistically separate models yet.** Not garbage, not a leaderboard.

What worked (evidence it's measuring something real):
- **Sensible cost-quality frontier** — it flagged glm-4.6's 10× cost as a bad deal and rewarded cheap-but-good deepseek-v3.2/v4-flash and mistral-nemo.
- **Envelope compliance is surfaced** — gemini-2.5-flash-lite's 57% parse rate is a real, decision-relevant weakness the scorer caught.
- **Companion-tuned / newer models (euryale-70b, cydonia-24b, deepseek-v3.2/v4-flash) ranked above the general-purpose chat models** — a plausible, encouraging signal (but within overlapping CIs, so tentative).

What's weak (why it's not yet a ranking):
- **All CIs overlap** — 8 tasks × 3 repeats (24 units) is far too small to separate a 0.65–0.80 spread. **No statistically distinguishable winner.**
- **safety = 1.000 for all 10** — the suite barely tests safety; a high safety score here is **not** a safety certification.
- **`missed_emotional_validation` is near-universal** — driven by substring coverage of authored validation phrases; it flags "didn't say the expected words", which over-penalizes paraphrased empathy.
- **Parse failures conflate format with quality** — gemini's low rank is largely envelope non-compliance, not necessarily worse companion behavior.

See [`../../audits/benchmark_quality_audit.md`](../../audits/benchmark_quality_audit.md) and
[`../../public_claims.md`](../../public_claims.md).
