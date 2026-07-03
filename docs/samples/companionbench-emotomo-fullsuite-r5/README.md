<!-- SPDX-License-Identifier: Apache-2.0 -->
# Sample: CompanionBench evaluation using the EMOTomo model set via OpenRouter — full suite (60 tasks, 5 repeats)

**This is a sanitized sample run for a CompanionBench evaluation using the EMOTomo model set via
OpenRouter. It is a scoped benchmark run.**

CompanionBench evaluates **targeted human-like companion-communication behaviors in defined
multi-turn scenarios**: emotional attunement, appropriate initiative, timing and pacing,
non-intrusion, preference adaptation, abstention behavior, and safety boundaries. EMOTomo is one
example **model set**; OpenRouter is one **provider adapter** — a model set or provider is never the
benchmark's identity here. `overall` is a **companion-communication score**, not a universal
"humanity" score. Scores are **scoped to these 60 tasks, these settings, and these model versions**
(2026-06-30) and are rule-based and deterministic. See [`../../public_claims.md`](../../public_claims.md).

## Headline

This is the first run on the **expanded 60-task, six-family suite** with **5 repeats** — and it is
the first CompanionBench run where models are **partly statistically separable**: bootstrap 95% CIs
tightened from ~±0.13 (the earlier 8-task run) to **~±0.025**, splitting the field into three
distinguishable tiers. All 10 EMOTomo-model-set slugs ran live; **total cost $1.03** (budget $25).
The full analysis — ranking + CIs, per-family scores, behavior flags, cost-quality frontier, and a
blunt separability verdict — is in [`summary.md`](summary.md).

Top tier (scoped to this suite): `deepseek/deepseek-v3.2` and `deepseek/deepseek-chat-v3.1`.
Distinctly weakest: `google/gemini-2.5-flash-lite` (partly a 51% envelope-parse rate). Worst value:
`z-ai/glm-4.6` (priciest by 3×, slowest, mid quality).

## Contents (sanitized — no raw transcripts)

```
summary.md                  ranking + CIs, separability, per-family, flags, frontier, verdict
modelset.json               the 10 models/providers compared
frontier.md, frontier.csv   cost-quality Pareto frontier
<model>/scores.json         per-model scores (overall, by_family, by_dimension, dimension_ci, behavior_flags, tokens)
<model>/summary.md          per-model summary table
```

**Deliberately excluded:** raw `events.jsonl` (full transcripts) and `run.json` — kept **local only**
(`runs/` is gitignored). Every committed file was secret-scanned (seeded with the live key) → clean.

## Run configuration

- Manifest `manifests/full.yaml` (60 tasks: 10 each across initiative / empathy / timing / adaptation
  / abstention / safety).
- Model set `configs/model_sets/emotomo-openrouter.yaml` (10 enabled, all `live_verified`).
- `--repeats 5 --shuffle-seed 42 --max-cost-usd 25`; **actual total cost $1.03**; 31 transient
  failures (27 glm-4.5-air, 4 euryale-70b).
- Scoring: rule-based; bootstrap 95% CIs, 5000 resamples, seed 42.

## Reproduce

Put your key in `<repo>/.env` (`OPENROUTER_API_KEY=...`, `COMPANIONBENCH_LIVE=1`), then:

```bash
companion-bench pricing sync-openrouter --out configs/pricing.openrouter.yaml
companion-bench models validate --model-set configs/model_sets/emotomo-openrouter.yaml --online
companion-bench run -m manifests/full.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/companionbench-emotomo-fullsuite-r5 \
  --live --yes --repeats 5 --shuffle-seed 42 --max-cost-usd 25
companion-bench score --run runs/companionbench-emotomo-fullsuite-r5 --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench report  --run runs/companionbench-emotomo-fullsuite-r5
companion-bench frontier --run runs/companionbench-emotomo-fullsuite-r5
```

Live results vary across calls, providers, model versions, and time; pin versions and re-run before
drawing conclusions. This remains a **scoped benchmark run**.
