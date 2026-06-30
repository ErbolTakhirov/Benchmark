---
name: benchmark-quality-audit
description: Run an offline external-reviewer quality audit of CompanionBench (objective, task design, scoring validity, reproducibility, statistics, security, verdict + top-10 fixes).
---

# Benchmark quality audit

Audit the **instrument**, not a model. The living audit is
[`docs/audits/benchmark_quality_audit.md`](../../docs/audits/benchmark_quality_audit.md) — update it,
don't duplicate it. End with a verdict on the ladder:
**not ready / MVP ready / public-alpha ready / serious-benchmark ready.**

## 0. Framing (never break)

CompanionBench evaluates **targeted human-like companion-communication behaviors in defined
multi-turn scenarios**. EMOTomo is one example model set; OpenRouter is one provider adapter — never
"the EMOTomo/OpenRouter benchmark". The composite `overall` is **not** a universal humanity score.
Enforced by `tests/test_public_claims.py`.

## 1. Offline gates (no keys)

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q && uv build
uv run companion-bench validate manifests/smoke.yaml
uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/audit-offline-smoke
uv run companion-bench score --run runs/audit-offline-smoke
```

## 2. Review dimensions (ask hard questions)

- **Objective clarity** — is what it does/does-not measure explicit and behavioral?
- **Task design** — negative ("don't intervene") controls per family? abstention/safety coverage?
  is there scoring-signal leakage into prompts?
- **Scoring validity** — can generic/verbose empathy, always-abstain, or always-intervene game it?
  substring keyword-stuffing of `positive_signals`/`expected_target_keywords`? safety-blocklist gaps?
  are behavior flags deterministic and actually surfaced (`evaluators/flags.py`)?
- **Reproducibility** — `run.json` provenance (version/manifest/seed/provider/model/tokens/cost);
  fresh clone runs offline keyless; live opt-in + budget cap.
- **Statistical honesty** — repeats + bootstrap 95% CIs deterministic under seed; `(task,repeat)`
  pseudo-replication caveat stated; small-sample limits stated.
- **Human-eval readiness** — `evaluators/rubric.py` seam; gold-set + rules-vs-judge-vs-human plan.
- **Security** — env/`.env`-only keys; `.env` gitignored; scanners exist; no key in artifacts.
- **Best practice** — HELM (multi-metric), MT-Bench/Arena (multi-turn/pairwise), MLPerf (rules),
  HF Evaluate (metric docs), ACM badging (available/functional/reusable/validated).

## 3. Output

verdict · strengths · blockers · non-blocking improvements · scoring/methodology/repro/security risk
register · **top-10 fixes before public v0.1** · exact commands run · exact tests passed/failed.
