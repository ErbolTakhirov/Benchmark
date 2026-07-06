<!-- SPDX-License-Identifier: Apache-2.0 -->
# Sample: CompanionBench held-out validation run (EMOTomo model set via OpenRouter, 12 hidden tasks, 5 repeats)

**This is a sanitized sample run for a CompanionBench evaluation using the EMOTomo model set via
OpenRouter. It is a scoped benchmark run.**

This is the **held-out / hidden split** (`manifests/heldout.yaml`, 2 tasks per family, deliberately
excluded from the public suite and never tuned against). It was run **only to check generalization** —
does the public-suite ranking hold up on tasks the suite was not built around? CompanionBench
evaluates targeted human-like companion-communication behaviors; EMOTomo is one example **model set**,
OpenRouter one **provider adapter** — the model set and provider are recorded as run metadata.
`overall` is a **companion-communication score**, not a universal "humanity" score, scoped to these 12
tasks and these model versions (2026-06-30). See [`../../public_claims.md`](../../public_claims.md).

## Headline

The full-suite ranking **partially generalizes**: held-out vs full-suite scores correlate
**Pearson 0.858**, rank correlation **Spearman 0.573**, and the held mean (0.700) matches the full
mean (0.698). **The extremes survive** — `deepseek/deepseek-chat-v3.1` stayed #1 and
`google/gemini-2.5-flash-lite` (#10, 36% parse) + `z-ai/glm-4.5-air` (#9) stayed the bottom two, still
statistically separable from the top. **The middle reshuffled** (e.g. `deepseek-chat-v3-0324` jumped
#7→#2 on 12 tasks) — expected, since the middle was a statistical tie. Total cost **$0.15** (budget
$10). Full analysis + tier-survival table in [`summary.md`](summary.md).

> **Recompute note (2026-07-06):** the **Spearman 0.573** quoted above is not reproducible from the
> committed scores — it recomputes to **0.612** (Pearson 0.858 does reproduce). This 12-task split is
> superseded by [`../companionbench-emotomo-heldout-expanded-r5/`](../companionbench-emotomo-heldout-expanded-r5/).
> See [`../../audits/humanity_validity_and_reliance_audit.md`](../../audits/humanity_validity_and_reliance_audit.md), Appendix B.

## Contents (sanitized — no raw transcripts)

```
summary.md                  held-out ranking vs full-suite, generalization metrics, per-family, verdict
modelset.json               the 10 models/providers compared
frontier.md, frontier.csv   cost-quality Pareto frontier (held-out)
<model>/scores.json         per-model scores (overall, by_family, by_dimension, dimension_ci, behavior_flags)
<model>/summary.md          per-model summary table
```

**Deliberately excluded:** raw `events.jsonl` and `run.json` — kept local only (`runs/` is gitignored).
Every committed file was secret-scanned (seeded with the live key) → clean.

## Run configuration

- Manifest `manifests/heldout.yaml` (12 hidden tasks, 2 per family).
- Model set `configs/model_sets/emotomo-openrouter.yaml` (10 enabled, all `live_verified`).
- `--repeats 5 --shuffle-seed 42 --max-cost-usd 10`; actual cost $0.15; 11 transient failures (glm-4.5-air).
- Scoring: rule-based; bootstrap 95% CIs, 5000 resamples, seed 42. **Nothing was tuned on this split.**

## Reproduce

Key in `<repo>/.env` (`OPENROUTER_API_KEY=...`, `COMPANIONBENCH_LIVE=1`), then:

```bash
companion-bench run -m manifests/heldout.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/companionbench-emotomo-heldout-r5 \
  --live --yes --repeats 5 --shuffle-seed 42 --max-cost-usd 10
companion-bench score --run runs/companionbench-emotomo-heldout-r5 --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench report  --run runs/companionbench-emotomo-heldout-r5
companion-bench frontier --run runs/companionbench-emotomo-heldout-r5
```

A 12-task split is small — read it as a generalization check on tiers, not a ranking. Remains a
**scoped benchmark run**.
