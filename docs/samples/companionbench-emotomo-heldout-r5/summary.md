<!-- SPDX-License-Identifier: Apache-2.0 -->
# Summary — CompanionBench held-out validation run (EMOTomo model set via OpenRouter, 12 hidden tasks, r5)

**This is a sanitized sample run for benchmark-quality verification. It is a scoped benchmark run.**
This is the **held-out / hidden split** (`manifests/heldout.yaml`, 2 tasks/family, never tuned
against), run to check whether the public-suite ranking **generalizes**. `overall` is a
**companion-communication score** scoped to **these 12 tasks, these settings, and these model
versions** (2026-06-30), rule-based and deterministic. EMOTomo is one example **model set**;
OpenRouter is one **provider adapter** — the model set and provider are recorded as run metadata
here. The split is small (12 tasks), so CIs are **wider** than the 60-task public run.

## Run configuration

- **Suite:** held-out split — **12 tasks**, 2 each across six families. **Models:** all 10, `live_verified`.
- **Repeats:** 5 · shuffle-seed 42 · temp 0.7. **Calls:** ~840 + **11 failures** (all `glm-4.5-air`).
- **Cost guard:** `--max-cost-usd 10`. **Actual total cost: $0.15.** Bootstrap 95% CIs, 5000 resamples, seed 42.

## Held-out ranking vs full-suite ranking

| Held # | (full #) | Model | overall | 95% CI | parse | cost | Δ vs full |
|---|---|---|---|---|---|---|---|
| 1 | (1) | `deepseek/deepseek-chat-v3.1` | **0.788** | [0.738,0.834] | 98% | $0.0135 | +0.034 |
| 2 | (7) | `deepseek/deepseek-chat-v3-0324` | 0.773 | [0.721,0.823] | 100% | $0.0131 | **+0.087** |
| 3 | (4) | `z-ai/glm-4.6` | 0.749 | [0.698,0.798] | 99% | $0.0301 | +0.033 |
| 4 | (2) | `deepseek/deepseek-v3.2` | 0.748 | [0.693,0.799] | 96% | $0.0116 | −0.006 |
| 5 | (8) | `mistralai/mistral-nemo` | 0.723 | [0.671,0.773] | 91% | $0.0009 | +0.038 |
| 6 | (6) | `sao10k/l3.3-euryale-70b` | 0.719 | [0.664,0.770] | 82% | $0.0288 | +0.019 |
| 7 | (3) | `deepseek/deepseek-v4-flash` | 0.717 | [0.662,0.774] | 92% | $0.0062 | −0.004 |
| 8 | (5) | `thedrummer/cydonia-24b-v4.1` | 0.685 | [0.628,0.742] | 99% | $0.0143 | −0.027 |
| 9 | (9) | `z-ai/glm-4.5-air` | 0.608 | [0.555,0.661] | 93% | $0.0269 | **−0.077** |
| 10 | (10) | `google/gemini-2.5-flash-lite` | **0.491** | [0.449,0.536] | **36%** | $0.0043 | −0.071 |

## Did the ranking generalize?

- **Pearson (held vs full overall): 0.858** — the *scores* track strongly between public and hidden tasks.
- **Spearman (rank correlation): 0.573** — the *exact ordering* shifts moderately, almost entirely in
  the middle.
- **Mean parity:** held 0.700 vs full 0.698 — the held-out split is **not** systematically easier or
  harder (good — no leakage / no difficulty drift).

**Tier survival:**
- **Top survives:** `deepseek-chat-v3.1` stayed **#1** (0.788), and its CI [0.738, 0.834] is **above**
  the bottom two (`glm-4.5-air` [0.555,0.661], `gemini` [0.449,0.536]) — still statistically separable.
- **Bottom survives, robustly:** `gemini-2.5-flash-lite` (#10, 0.491, **36% parse**) and `glm-4.5-air`
  (#9, 0.608) stayed the two worst with non-overlapping CIs vs the top.
- **Middle does NOT survive as an ordering:** `deepseek-chat-v3-0324` jumped #7→#2 (+0.087),
  `deepseek-v4-flash` #3→#7, `cydonia` #5→#8. These were a statistical tie on the full suite, so on 12
  tasks they reshuffle — exactly what a held-out split is meant to reveal.

## Biggest movers (small-sample swings)

- `deepseek-chat-v3-0324` **+0.087** — on the 12 hidden tasks it scored much higher on safety (0.82)
  and abstention (0.77); a few tasks swung it. Evidence that per-model estimates need more than 12 tasks.
- `glm-4.5-air` **−0.077** (11 failures hurt) and `gemini` **−0.071** (parse fell to 36%).

## Per-family (held-out — 2 tasks/family, so NOISY)

| Model | init | empathy | timing | adapt | abstention | safety |
|---|---|---|---|---|---|---|
| deepseek-chat-v3.1 | 0.85 | 0.75 | 0.89 | 0.72 | 0.81 | 0.71 |
| deepseek-chat-v3-0324 | 0.60 | 0.75 | 0.90 | 0.80 | 0.77 | 0.82 |
| glm-4.6 | 0.75 | 0.75 | 0.91 | 0.74 | 0.77 | 0.58 |
| deepseek-v3.2 | 0.71 | 0.75 | 0.90 | 0.73 | 0.71 | 0.69 |
| mistral-nemo | 0.87 | 0.75 | 0.81 | 0.77 | 0.75 | **0.39** |
| euryale-70b | 0.79 | 0.74 | 0.74 | 0.79 | 0.74 | 0.51 |
| deepseek-v4-flash | 0.53 | 0.71 | 0.91 | 0.68 | 0.75 | 0.71 |
| cydonia-24b-v4.1 | 0.63 | 0.71 | 0.88 | 0.85 | 0.67 | **0.36** |
| glm-4.5-air | 0.61 | 0.64 | 0.74 | 0.75 | 0.46 | 0.44 |
| gemini-2.5-flash-lite | 0.38 | 0.68 | 0.61 | 0.50 | 0.39 | 0.40 |

With only 2 tasks/family the per-family numbers are **high-variance** — e.g. abstention reads higher
here (0.67–0.81) than on the full suite (0.55–0.70), and safety swings hard (cydonia 0.36, mistral
0.39). Read per-family on the **full** suite, not on this split.

## Weaknesses the held-out run exposed

1. **A 12-task split is too small for fine ranking** — Spearman 0.573 and a +0.087 single-model swing.
   The public suite (10/family) is enough for tiers, not for ordering neighbours; per-family needs
   many more than 2/family.
2. **Format/quality entanglement persists** — `gemini` parsed only **36%** here (51% on full), and that
   alone explains most of its last place.
3. **Safety is noisy on few tasks** — it differentiates, but 2 tasks/family makes the per-family safety
   signal unstable.

## Honest verdict

The **coarse signal generalizes and is robust** (scores correlate 0.86; top-1 and bottom-2 survive and
stay statistically separable), but the **fine ordering does not** on a small hidden split. That is the
correct, expected outcome for a public-alpha suite — and the held-out check did its job: it confirmed
the middle ranking is noise. See [`../../audits/benchmark_quality_audit.md`](../../audits/benchmark_quality_audit.md)
and [`../../public_claims.md`](../../public_claims.md).
