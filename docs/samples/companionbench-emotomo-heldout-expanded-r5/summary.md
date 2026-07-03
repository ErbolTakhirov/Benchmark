<!-- SPDX-License-Identifier: Apache-2.0 -->
# Summary — CompanionBench expanded held-out validation (EMOTomo model set via OpenRouter, 36 hidden tasks, r5)

**This is a sanitized held-out validation sample for a CompanionBench evaluation using the EMOTomo
model set via OpenRouter. It is a scoped benchmark run.** This is the **expanded held-out / hidden
split** (`manifests/heldout.yaml`, 6 tasks/family, 36 total, never tuned against), run to check
whether the public-suite ranking **generalizes** — and whether growing the held-out split from 12
to 36 tasks stabilizes the fine ranking the way more public tasks stabilized the public ranking.
`overall` is a **companion-communication score** scoped to **these 36 tasks, these settings, and
these model versions** (2026-07-01), rule-based and deterministic. EMOTomo is one example **model
set**; OpenRouter is one **provider adapter** — neither is the benchmark's identity here.

## Run configuration

- **Suite:** held-out split — **36 tasks**, 6 each across six families. **Models:** all 10,
  `live_verified`.
- **Repeats:** 5 · shuffle-seed 42 · temp 0.7. **Calls:** 2,517 total, **33 failures** (31
  `glm-4.5-air`, 2 `euryale-70b` — transient provider errors, logged as `model_failure`).
- **Cost guard:** `--max-cost-usd 15`. **Actual total cost: $0.59.** Bootstrap 95% CIs, 5000
  resamples, seed 42.

## Score table (overall, 95% CI, parse rate, cost, tokens, latency)

| # | Model (via OpenRouter) | overall | 95% CI | pass | parse | cost USD | tokens | avg latency |
|---|---|---|---|---|---|---|---|---|
| 1 | `deepseek/deepseek-v3.2` | **0.756** | [0.726, 0.786] | 31/36 | 98.8% | 0.0342 | 139,011 | 4,719 ms |
| 2 | `deepseek/deepseek-chat-v3-0324` | 0.753 | [0.725, 0.781] | 30/36 | 94.9% | 0.0373 | 128,547 | 4,509 ms |
| 3 | `deepseek/deepseek-chat-v3.1` | 0.751 | [0.722, 0.780] | 31/36 | 96.1% | 0.0412 | 139,479 | 5,806 ms |
| 4 | `deepseek/deepseek-v4-flash` | 0.720 | [0.689, 0.751] | 27/36 | 95.7% | 0.0216 | 163,347 | 5,208 ms |
| 5 | `sao10k/l3.3-euryale-70b` | 0.712 | [0.681, 0.741] | 30/36 | 78.3% | 0.0869 | 131,183 | 9,950 ms |
| 6 | `z-ai/glm-4.6` | 0.710 | [0.678, 0.741] | 28/36 | 97.3% | **0.2265** | 212,157 | **11,338 ms** |
| 7 | `mistralai/mistral-nemo` | 0.687 | [0.656, 0.718] | 26/36 | 90.6% | **0.0027** | 124,332 | 1,657 ms |
| 8 | `thedrummer/cydonia-24b-v4.1` | 0.684 | [0.652, 0.716] | 23/36 | 100% | 0.0431 | 129,596 | 1,751 ms |
| 9 | `z-ai/glm-4.5-air` | 0.647 | [0.617, 0.677] | 24/36 | 91.1% | 0.0834 | 188,232 | 9,625 ms |
| 10 | `google/gemini-2.5-flash-lite` | **0.592** | [0.560, 0.625] | 21/36 | **59.2%** | 0.0180 | 120,401 | 927 ms |

**Grand mean overall: 0.701.** Total: 2,517 calls, $0.59, 1,476,285 tokens.

## Per-family scores

| Model | initiative | empathy | timing | adaptation | abstention | safety |
|---|---|---|---|---|---|---|
| deepseek-v3.2 | 0.693 | 0.703 | 0.897 | 0.764 | 0.698 | 0.781 |
| deepseek-chat-v3-0324 | 0.647 | 0.694 | 0.801 | 0.774 | 0.730 | **0.874** |
| deepseek-chat-v3.1 | 0.707 | 0.705 | 0.875 | 0.755 | **0.761** | 0.705 |
| deepseek-v4-flash | 0.597 | 0.714 | 0.848 | 0.758 | 0.753 | 0.648 |
| euryale-70b | 0.700 | 0.694 | 0.714 | 0.830 | 0.720 | 0.611 |
| glm-4.6 | 0.668 | 0.708 | 0.873 | 0.780 | 0.693 | 0.537 |
| mistral-nemo | 0.689 | 0.701 | 0.750 | **0.803** | 0.727 | 0.454 |
| cydonia-24b-v4.1 | 0.613 | 0.702 | 0.839 | 0.799 | 0.715 | **0.437** |
| glm-4.5-air | 0.588 | 0.676 | 0.762 | 0.681 | 0.607 | 0.570 |
| gemini-2.5-flash-lite | **0.579** | **0.629** | **0.615** | **0.515** | 0.579 | 0.637 |

With 6 tasks/family this is still noisier than the full public suite — read per-family trends
directionally, not as precise estimates. Safety spread (0.437–0.874) confirms the family
continues to discriminate meaningfully on held-out tasks, not just on the public suite.

## Did the ranking generalize? — Better than last time

- **Pearson (held vs. earlier 60-task full-suite overall): 0.848** — essentially unchanged from
  the prior 12-task held-out check (0.858). Scores still track strongly between public and hidden
  tasks.
- **Spearman (rank correlation): 0.726** — up sharply from **0.573** on the earlier 12-task split.
  Tripling the held-out split materially stabilized the ordering, exactly as the prior held-out
  report predicted it would.
- **Mean parity:** held 0.701 vs. (old) full-suite 0.698 — still no systematic difficulty
  drift.

**Tier survival:**
- **Top survives, with a new member.** `deepseek-v3.2` and `deepseek-chat-v3.1` — the prior
  full-suite's top-2 — both remain in the top 3 here (ranks 1 and 3). `deepseek-chat-v3-0324`
  (previously mid-pack, rank 7) joins them at rank 2. All three CIs overlap each other, but their
  **combined floor (0.722) sits above the bottom-2's combined ceiling (0.677)** — the top-3
  cluster is statistically separable from the bottom-2, even though every *adjacent* rank in the
  full chain overlaps (a transitive-tie pattern: 1 ties 2, 2 ties 3, ... but 1 is still
  significantly better than 10).
- **Bottom survives, identically.** `gemini-2.5-flash-lite` (rank 10, 0.592, parse rate still the
  lowest at 59%) and `glm-4.5-air` (rank 9, 0.647, 31 failures) are the same two worst models as
  on the full suite, in the same order.
- **Middle does not survive as an ordering**, again — `deepseek-chat-v3-0324` (#7→#2),
  `cydonia-24b` (#5→#8), and `euryale-70b` (#6→#5) all moved multiple ranks. These were
  statistical ties on the full suite; 36 tasks narrowed but did not eliminate that tie.

## Biggest movers

- **`deepseek-chat-v3-0324` +0.067** (0.686→0.753, rank 7→2) — the standout mover, now
  scoring strongly on safety (0.874, the best of any model) and abstention (0.730).
- **`cydonia-24b-v4.1` −0.028** (0.712→0.684, rank 5→8) — safety fell further (0.437, the
  weakest of any model on held-out), consistent with its known safety weakness on the full suite.
- **`glm-4.5-air` −0.038** (0.685→0.647) — compounded by 31 failures (the most of any model),
  consistent with its instability across every run this project has done.
- **`euryale-70b` +0.012**, **`gemini-2.5-flash-lite` +0.030** (parse rate actually improved
  slightly, 51%→59%, though still the clear outlier) — modest, within-noise movement.
- Everyone else (`deepseek-v3.2`, `deepseek-chat-v3.1`, `deepseek-v4-flash`, `glm-4.6`,
  `mistral-nemo`) moved by 0.001–0.012 — essentially stable.

## Behavior flags (top 3, summed across 36 tasks × 5 repeats)

`missed_emotional_validation` dominates every model (99–164) — still the rubric's most-fired
signal, consistent with the public suite. `unparseable_output` cleanly separates envelope
compliance: **gemini 104**, euryale 57, glm-4.5-air 51. `style_mismatch` and
`mistimed_intervention` are moderate everywhere; `inappropriate_abstention` is notable for
`deepseek-chat-v3-0324` (25).

## Cost-quality frontier (Pareto)

Pareto-optimal on this split: **`deepseek-v3.2`** (top quality, $0.034 — the best overall pick),
**`deepseek-v4-flash`** (0.720 at $0.022), **`mistral-nemo`** (cheapest at **$0.0027**, still
0.687). `z-ai/glm-4.6` remains a poor value — mid-tier quality (0.710) at **$0.227 (the most
expensive by ~3×) and the slowest average latency (11.3 s)**. See `frontier.md`/`frontier.csv`.

## Honest verdict

**The coarse signal continues to generalize and is now more robust than before**: top-3 and
bottom-2 survive with clean separation, and — new this round — tripling the held-out split
measurably tightened the *rank* correlation (0.573→0.726), not just held the *score* correlation
steady (0.858→0.848). That is direct evidence the suite-expansion strategy works: more tasks (both
public and held-out) buys real statistical power, not just more data. **The fine ranking among
closely-clustered models still does not generalize** — this round's biggest mover
(`deepseek-chat-v3-0324`, +0.067/+5 ranks) is exactly the kind of instability a still-modest
36-task split can't fully resolve. Read this as: **CompanionBench is stable enough for public-alpha
"good vs. weak" comparisons, and getting more stable at fine-grained ranking as the suite grows —
but not there yet.** See
[`../../audits/public_alpha_release_readiness.md`](../../audits/public_alpha_release_readiness.md)
and [`../../public_claims.md`](../../public_claims.md).
