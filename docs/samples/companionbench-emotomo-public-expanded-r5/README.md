<!-- SPDX-License-Identifier: Apache-2.0 -->
# Sample: CompanionBench expanded public-suite run (EMOTomo model set via OpenRouter, 150 tasks, 5 repeats)

This is a sanitized public-suite sample for a CompanionBench evaluation using the EMOTomo model
set via OpenRouter. It is not a final leaderboard.

This is the **expanded public suite** (`manifests/full.yaml`, 25 tasks per family across all six
families, 150 total — grown from the earlier 60-task suite), re-run live to give the **expanded
held-out split** (`docs/samples/companionbench-emotomo-heldout-expanded-r5/`, 36 tasks) a
like-for-like baseline: the previous public sample
(`docs/samples/companionbench-emotomo-fullsuite-r5/`) predates this session's suite expansion and
was no longer a fair comparison point. CompanionBench evaluates targeted human-like
companion-communication behaviors; EMOTomo is one example **model set**, OpenRouter one example
**provider adapter** — a model set or provider is never the benchmark's identity here. `overall`
is a **companion-communication score**, not a universal "humanity" score, scoped to these 150
tasks and these model versions (2026-07-01/02). See
[`../../public_claims.md`](../../public_claims.md).

## Headline

Comparing the public suite against the held-out split **at both suites' true expanded sizes**
produces the strongest generalization result this project has recorded: Pearson (scores) **0.968**
and Spearman (rank correlation) **0.939** — both sharply up from the previous round's 0.848/0.726
(which compared the held-out split against a stale, smaller public baseline). All three score
tiers — top-4, middle-2, bottom-4 — survived with at most a 2-rank shuffle; the top-4
(`deepseek-v3.2`, `deepseek-chat-v3.1`, `deepseek-chat-v3-0324`, `deepseek-v4-flash`) are
statistically separable from ranks 6–10, and `gemini-2.5-flash-lite` remains distinctly worst on
both splits. The biggest mover is `mistral-nemo` (rank 7→9, held→public). Total cost **$2.55**
(budget $40). Full analysis in [`summary.md`](summary.md).

**Provenance caveat:** this run's live API calls were made across **two invocations**, not one —
the first (all 10 models) was killed by the execution environment after ~3 hours, having fully
completed 6 of 10 models cleanly. A second invocation, using an identical manifest/model
refs/temperature/repeats/shuffle-seed but restricted to only the 4 missing models, completed the
set; the two result sets were merged into one run directory with a hand-combined `modelset.json`.
Every model was evaluated under identical settings — only the wall-clock delivery was split. See
`summary.md` for the full account.

## Contents (sanitized — no raw transcripts)

```
summary.md                  public-suite ranking, held-out generalization metrics, per-family, verdict
modelset.json                the 10 models/providers compared
frontier.md, frontier.csv    cost-quality Pareto frontier (public suite)
<model>/scores.json          per-model scores (overall, by_family, by_dimension, dimension_ci, behavior_flags)
```

**Deliberately excluded:** raw `events.jsonl` and `run.json` — kept local only (`runs/` is
gitignored). Every committed file was secret-scanned (seeded with the live key) → clean.

## Run configuration

- Manifest `manifests/full.yaml` (150 public tasks, 25 per family — grown from 60).
- Model set `configs/model_sets/emotomo-openrouter.yaml` (10 enabled, all `live_verified`).
- `--repeats 5 --shuffle-seed 42`; combined cost cap across both invocations effectively $40;
  actual total cost $2.55; 61 transient failures (46 `glm-4.5-air`, 15 `euryale-70b`).
- Scoring: rule-based; bootstrap 95% CIs, 5000 resamples, seed 42. **Nothing was tuned on this
  run** — tasks and scoring were frozen before it started.

## Reproduce

Key in `<repo>/.env` (`OPENROUTER_API_KEY=...`, `COMPANIONBENCH_LIVE=1`), then:

```bash
companion-bench run -m manifests/full.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/companionbench-emotomo-public-expanded-r5 \
  --live --yes --repeats 5 --shuffle-seed 42 --max-cost-usd 40
companion-bench score --run runs/companionbench-emotomo-public-expanded-r5 --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench report  --run runs/companionbench-emotomo-public-expanded-r5
companion-bench frontier --run runs/companionbench-emotomo-public-expanded-r5
```

On a fast/reliable connection this should complete as a single invocation. If it is interrupted
partway (the CLI has no built-in resume), the only current recovery path is to re-run only the
missing models via a model-set file with the completed models' `enabled:` flags set to `false`,
into a separate `--out`, then merge the resulting subdirectories and `modelset.json` by hand — as
was necessary for this sample. A first-class `--resume` flag is on the roadmap; see `summary.md`.

A 150-task suite is still fully synthetic, AI-authored, and rule-scored — read this as a
generalization and cost/latency reference, not a fine-grained ranking. Remains a **sample run, not
a final leaderboard**.
