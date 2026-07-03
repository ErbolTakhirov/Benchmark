<!-- SPDX-License-Identifier: Apache-2.0 -->
# Sample: CompanionBench expanded held-out validation run (EMOTomo model set via OpenRouter, 36 hidden tasks, 5 repeats)

This is a sanitized held-out validation sample for a CompanionBench evaluation using the EMOTomo
model set via OpenRouter. It is a scoped benchmark run.

This is the **expanded held-out / hidden split** (`manifests/heldout.yaml`, 6 tasks per family
across all six families, 36 total — grown from the earlier 12-task split, deliberately excluded
from the public suite and never tuned against). It was run **only to check generalization**: does
the public-suite ranking hold up on tasks the suite was not built around? CompanionBench evaluates
targeted human-like companion-communication behaviors; EMOTomo is one example **model set**,
OpenRouter one **provider adapter** — the model set and provider are recorded as run metadata
here. `overall` is a **companion-communication score**, not a universal "humanity" score, scoped to
these 36 tasks and these model versions (2026-07-01). See
[`../../public_claims.md`](../../public_claims.md).

## Headline

The expanded held-out split **generalizes better than the earlier 12-task split did**: Pearson
(scores vs. the earlier 60-task public full-suite sample) **0.848** (essentially unchanged from
the prior 0.858), but Spearman (rank correlation) rose from **0.573 to 0.726** — tripling the
held-out split materially stabilized the fine ranking, exactly as predicted. The top-3
(`deepseek-v3.2`, `deepseek-chat-v3-0324`, `deepseek-chat-v3.1`) remain statistically separable
from the bottom-2 (`glm-4.5-air`, `google/gemini-2.5-flash-lite`) despite every *adjacent* rank
overlapping — a classic transitive-tie pattern. The biggest mover is
`deepseek/deepseek-chat-v3-0324`, jumping from a middle-tier tie (rank 7, 0.686) on the public
suite to rank 2 (0.753) here. Total cost **$0.59** (budget $15). Full analysis in
[`summary.md`](summary.md).

**Important caveat:** the "public full-suite" comparison here is against the **earlier 60-task**
full-suite sample (`../companionbench-emotomo-fullsuite-r5/`), not a fresh run on the current
150-task suite — re-running the full suite live on the 150-task version was out of scope for this
pass (no large live benchmark; see [`../../audits/public_alpha_release_readiness.md`](../../audits/public_alpha_release_readiness.md)
for why). Read this as "does the held-out signal generalize relative to what we've measured
before," not "these two runs are the same experiment."

## Contents (sanitized — no raw transcripts)

```
summary.md                  held-out ranking, generalization metrics, per-family, verdict
modelset.json               the 10 models/providers compared
frontier.md, frontier.csv   cost-quality Pareto frontier (held-out)
<model>/scores.json         per-model scores (overall, by_family, by_dimension, dimension_ci, behavior_flags)
```

**Deliberately excluded:** raw `events.jsonl` and `run.json` — kept local only (`runs/` is
gitignored). Every committed file was secret-scanned (seeded with the live key) → clean.

## Run configuration

- Manifest `manifests/heldout.yaml` (36 hidden tasks, 6 per family — grown from 12).
- Model set `configs/model_sets/emotomo-openrouter.yaml` (10 enabled, all `live_verified`).
- `--repeats 5 --shuffle-seed 42 --max-cost-usd 15`; actual cost $0.59; 33 transient failures
  (31 `glm-4.5-air`, 2 `euryale-70b`).
- Scoring: rule-based; bootstrap 95% CIs, 5000 resamples, seed 42. **Nothing was tuned on this
  split** — tasks and scoring were frozen before this run.

## Reproduce

Key in `<repo>/.env` (`OPENROUTER_API_KEY=...`, `COMPANIONBENCH_LIVE=1`), then:

```bash
companion-bench run -m manifests/heldout.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/companionbench-emotomo-heldout-expanded-r5 \
  --live --yes --repeats 5 --shuffle-seed 42 --max-cost-usd 15
companion-bench score --run runs/companionbench-emotomo-heldout-expanded-r5 --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench report  --run runs/companionbench-emotomo-heldout-expanded-r5
companion-bench frontier --run runs/companionbench-emotomo-heldout-expanded-r5
```

A 36-task split is still modest — read it as a generalization check on tiers, not a fine-grained
ranking. Remains a **scoped benchmark run**.
