<!-- SPDX-License-Identifier: Apache-2.0 -->
# Documentation index

Start with the root [`README.md`](../README.md) for the project overview and quickstart. This page
maps everything under `docs/`.

## Core concepts

- [`methodology.md`](methodology.md) — what CompanionBench measures and how, in depth.
- [`hypothesis.md`](hypothesis.md) — the research hypothesis this benchmark tests.
- [`benchmark_card.md`](benchmark_card.md) — intended use, scope, and known limitations (the
  benchmark-card format).
- [`public_claims.md`](public_claims.md) — the exact language policy: what this project will and
  will not claim about its own numbers (mechanically enforced by `tests/test_public_claims.py`).
- [`scoring.md`](scoring.md) — the six scoring dimensions and the aggregation formula.
- [`results_interpretation.md`](results_interpretation.md) — how to read a `scores.json`/
  `summary.md` without over-claiming (mock vs. real, CIs, public-vs-held-out generalization,
  behavior flags, cost/frontier).
- [`results_v0_1_alpha.md`](results_v0_1_alpha.md) — the v0.1.0-alpha results writeup: the
  10-model score table, cost-quality frontier, and public-vs-held-out generalization numbers.

## Building and running

- [`architecture.md`](architecture.md) — module layout and data flow.
- [`task_authoring.md`](task_authoring.md) — the task YAML schema and how to write a new one.
- [`model_sets.md`](model_sets.md) — what a model set is and how it differs from a provider or
  the benchmark itself.
- [`provider_adapters.md`](provider_adapters.md) — the `ChatAdapter` contract and how to add one.
- [`live_and_cost.md`](live_and_cost.md) — live-run guardrails, cost accounting, retries, secrets.
- [`local_verification.md`](local_verification.md) — the local command sequence that replaces
  GitHub Actions CI (see [`ci-disabled/`](ci-disabled/) for why).
- [`release_checklist.md`](release_checklist.md) — version-bump locations and the tag/push
  sequence for cutting a release.

## Process

- [`ci-disabled/`](ci-disabled/) — why GitHub Actions was removed, and how local verification
  replaces it.
- [`audits/`](audits/) — point-in-time external-reviewer audits:
  [`benchmark_quality_audit.md`](audits/benchmark_quality_audit.md) (2026-06-30, the first
  quality pass, now superseded), [`final_open_source_readiness_audit.md`](audits/final_open_source_readiness_audit.md)
  (2026-07-01 baseline before the local-first/task-expansion/docs pass),
  [`public_alpha_release_readiness.md`](audits/public_alpha_release_readiness.md) (2026-07-01
  final state after that pass).
- [`samples/`](samples/) — sanitized sample runs (no raw transcripts). Each has its own README
  explaining what was run and what it does/doesn't show; none of them are a leaderboard.
- [`release_notes/v0.1.0-alpha.md`](release_notes/v0.1.0-alpha.md) — the v0.1.0-alpha release
  notes: summary, installation, quickstart, result caveats, known limitations, roadmap.

## Elsewhere in the repo

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md), [`../SECURITY.md`](../SECURITY.md),
  [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md), [`../CITATION.cff`](../CITATION.cff),
  [`../CHANGELOG.md`](../CHANGELOG.md), [`../LICENSE`](../LICENSE).
- `.claude/skills/` — project-specific Claude Code skills (task authoring, provider authoring,
  quality audits, release gates, secret scanning, OpenRouter runs). Referenced throughout the docs
  above rather than duplicated here.
