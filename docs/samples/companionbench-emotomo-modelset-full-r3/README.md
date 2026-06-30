<!-- SPDX-License-Identifier: Apache-2.0 -->
# Sample: CompanionBench evaluation using the EMOTomo model set via OpenRouter — full run (10 models, 3 repeats)

**This is a sanitized sample run for a CompanionBench evaluation using the EMOTomo model set via
OpenRouter. It is not a final leaderboard.**

CompanionBench evaluates **targeted human-like companion-communication behaviors in defined
multi-turn scenarios**: emotional attunement, appropriate initiative, timing and pacing,
non-intrusion, preference adaptation, abstention behavior, and safety boundaries. EMOTomo is one
example **model set**; OpenRouter is one **provider adapter** — a model set or provider is never the
benchmark's identity here. `overall` is a **companion-communication score**, not a universal
"humanity" score. Scores are **scoped to these 8 tasks, these settings, and these model versions**
(2026-06-30), are rule-based and deterministic, and are **not statistically separable** (all 95% CIs
overlap). See [`../../public_claims.md`](../../public_claims.md).

## Headline

All **10** EMOTomo-model-set slugs ran live on OpenRouter, **total cost $0.0973** (budget $10). The
full cross-model analysis — overall + 95% CIs, per-dimension, behavior flags, cost-quality frontier,
and a **blunt verdict on whether the benchmark is useful** — is in [`summary.md`](summary.md).
Short version: **the live pipeline works and is a useful MVP differential profiler, but the 8-task
suite is too small to statistically separate models** (so this is a scoped comparison, not a ranking).

## Contents (sanitized — no raw transcripts)

```
summary.md                  cross-model analysis (overall + CIs, per-dimension, flags, frontier, verdict)
modelset.json               which 10 models/providers were compared
frontier.md, frontier.csv   cost-quality Pareto frontier (⭐ Pareto: euryale-70b, deepseek-v3.2, deepseek-v4-flash, mistral-nemo)
<model>/scores.json         per-model scores (overall, by_dimension, dimension_ci, behavior_flags, tokens)
<model>/summary.md          per-model summary table
```

**Deliberately excluded:** raw `events.jsonl` (full transcripts) and `run.json` — kept **local only**
(`runs/` is gitignored). Every committed file was secret-scanned (seeded with the live key) → clean.

## Reproduce

Put your key in `<repo>/.env` (`OPENROUTER_API_KEY=...`, `COMPANIONBENCH_LIVE=1`), then:

```bash
companion-bench pricing sync-openrouter --out configs/pricing.openrouter.yaml
companion-bench models validate --model-set configs/model_sets/emotomo-openrouter.yaml --online
companion-bench run -m manifests/emotomo_smoke.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/companionbench-emotomo-modelset-full-r3 \
  --live --yes --repeats 3 --shuffle-seed 42 --max-cost-usd 10
companion-bench score --run runs/companionbench-emotomo-modelset-full-r3 --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench report  --run runs/companionbench-emotomo-modelset-full-r3
companion-bench frontier --run runs/companionbench-emotomo-modelset-full-r3
```

Live results vary across calls, providers, model versions, and time; pin versions and expand the
task suite before drawing conclusions. This remains a **sample run, not a final leaderboard**.
