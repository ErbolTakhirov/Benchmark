<!-- SPDX-License-Identifier: Apache-2.0 -->
# Sample: CompanionBench evaluation using the EMOTomo model set via OpenRouter — capped audit run (4 models, 2 repeats)

**This is a sanitized sample run for benchmark-quality verification. It is not a final leaderboard.**

CompanionBench evaluates **targeted human-like companion-communication behaviors in defined
multi-turn scenarios**: emotional attunement, appropriate initiative, timing, non-intrusion,
preference adaptation, abstention behavior, and safety boundaries. **EMOTomo is one example model
set; OpenRouter is one provider adapter** — a model set or provider is never the benchmark's identity
here. Scores are **scoped to these 8 tasks, these settings, and these model versions** (2026-06-30),
produced by rule-based deterministic scoring, and are **not statistically separable** (the 95% CIs
overlap). See [`../../public_claims.md`](../../public_claims.md).

## What this run was for

A controlled, cost-capped **quality-verification** run to exercise the live OpenRouter path
end-to-end (pricing sync → online slug verification → capped run → bootstrap CIs → cost-quality
frontier → secret scan) and to sanity-check whether the benchmark measures what it claims. The
headline read of the results is in [`summary.md`](summary.md); the instrument review is in
[`../../audits/benchmark_quality_audit.md`](../../audits/benchmark_quality_audit.md).

## Contents (sanitized — no raw transcripts)

```
summary.md                      cross-model analysis (overall + CIs, per-dimension, flags, frontier, caveats)
modelset.json                   which models/providers were compared
frontier.md, frontier.csv       cost-quality Pareto frontier
<model>/scores.json             per-model scores (overall, by_dimension, dimension_ci, behavior_flags, tokens)
<model>/summary.md              per-model summary table
```

**Deliberately excluded:** raw `events.jsonl` (full transcripts) and `run.json` are kept **local
only** (`runs/` is gitignored). Every committed file was secret-scanned (seeded with the live key)
and is clean.

## Run configuration

- Manifest `manifests/emotomo_smoke.yaml` — 8 tasks (2× initiative / empathy / timing / adaptation).
- Model set `configs/model_sets/emotomo-openrouter.yaml` — 4 enabled, all `live_verified`:
  `deepseek/deepseek-chat-v3-0324`, `mistralai/mistral-nemo`, `z-ai/glm-4.5-air`,
  `google/gemini-2.5-flash-lite`.
- `--repeats 2 --shuffle-seed 42 --max-cost-usd 3`; **actual total cost $0.0147**.
- Scoring: rule-based; bootstrap 95% CIs, 2000 resamples, seed 42.

## Reproduce

Put your key in `<repo>/.env` (`OPENROUTER_API_KEY=...`, `COMPANIONBENCH_LIVE=1`), then:

```bash
companion-bench pricing sync-openrouter --out configs/pricing.openrouter.yaml
companion-bench models validate --model-set configs/model_sets/emotomo-openrouter.yaml --online
companion-bench run -m manifests/emotomo_smoke.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/audit-openrouter-humanlike-r2-small \
  --live --yes --limit-models 4 --repeats 2 --shuffle-seed 42 --max-cost-usd 3
companion-bench score --run runs/audit-openrouter-humanlike-r2-small --bootstrap --bootstrap-resamples 2000 --bootstrap-seed 42
companion-bench report  --run runs/audit-openrouter-humanlike-r2-small
companion-bench frontier --run runs/audit-openrouter-humanlike-r2-small
```

Live results vary across calls, providers, model versions, and time; pin versions and re-run with
more repeats before drawing any conclusion. This remains a **sample run, not a final leaderboard**.
