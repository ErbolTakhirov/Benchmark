# Sample: Sprint 3 pipeline demo (repeats → bootstrap → frontier)

**This is a MOCK pipeline-validation sample**, not a real model evaluation. It exercises the
full Sprint 3 flow — repeated runs, bootstrap confidence intervals, behavior flags, and the
cost-quality frontier — against the three deterministic mock profiles, so it shows the **shape
of the new artifacts** without spending money or needing keys.

> ⚠️ Mock scores validate the **pipeline**, not model quality. The mock is a deterministic
> simulator. For a *real* (tiny) result, see [`../emotomo-openrouter-smoke/`](../emotomo-openrouter-smoke/).

- **Date:** 2026-06-29  ·  **Manifest:** `manifests/emotomo_smoke.yaml` (8 tasks, all 4 families)
- **Models:** `configs/model_sets/mock-profiles.yaml` (empathetic / intrusive / silent)
- **Repeats:** 3  ·  **Bootstrap:** 5000 resamples, seed 42  ·  **Secrets:** none (offline, no network)

## What to look at

- `*/scores.json` — `overall_ci`, `dimension_ci`, `n_repeats: 3`, and `behavior_flags`
  (e.g. the intrusive profile shows `intrusive_advice`, `style_mismatch`, `unsafe_overreach`).
- `*/summary.md` — overall score with its 95% CI, a per-dimension CI column, and a behavior-flag table.
- `frontier.md` / `frontier.csv` — per-model overall + CI, cost, cost/successful-probe, latency,
  Pareto. Cost and Pareto are `n/a` here because mock models are unpriced; on a live run with
  `--pricing configs/pricing.openrouter.yaml` they populate.

Mock comparison (validates the pipeline): empathetic 1.000 > silent 0.622 > intrusive 0.404,
with CIs that **tighten** as repeats increase.

## Reproduce (fully offline, no keys)

```bash
companion-bench run -m manifests/emotomo_smoke.yaml \
  --model-set configs/model_sets/mock-profiles.yaml --out runs/pipeline-demo \
  --repeats 3 --shuffle-seed 42
companion-bench score --run runs/pipeline-demo --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench frontier --run runs/pipeline-demo
```
