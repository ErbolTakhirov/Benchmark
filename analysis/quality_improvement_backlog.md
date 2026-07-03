<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench Quality-Improvement Backlog

Prioritized fixes to move from **6.35/10** (public-alpha valid) toward a credible, then mature
benchmark. Ranked by impact on the [scorecard](../docs/audits/benchmark_quality_scorecard.md).
Items marked **[done this sprint]** shipped in the quality-hardening pass; the rest are open.

## P0 — required before any stronger benchmark claim

- **Run a real human annotation round + agreement report.** _Open (needs annotators; cannot be done offline or fabricated)._ The workflow is ready (`analysis/annotation_round_v0_1/`, `gold import-human`, `gold agreement`). Blocks scorecard §4 and §5.
- **Rule-vs-human calibration once real labels exist.** _Open (depends on the round)._ `calibrate rules` is implemented and tested on the synthetic fixture only.
- **No-fabrication guard for synthetic labels.** **[done this sprint]** `quality status` detects synthetic-vs-real gold and warns against "human-validated"; gold rows carry `not_human_collected`.
- **External-validation status visible in the CLI + docs.** **[done this sprint]** `companion-bench quality status` + a machine-readable scorecard; docs point to both.
- **Scorer robustness tests for format/parse/fallback.** **[done this sprint]** `tests/test_parse_quality.py` + existing `tests/test_scoring_adversarial.py`.
- **Task-quality invariant checks at validation time.** **[done this sprint]** `validate --strict-quality` (`runner/quality_checks.py`).
- **Repo-hygiene guard (no raw runs / secrets / private labels tracked).** **[done this sprint]** `tests/test_repo_hygiene.py`.

## P1 — improves benchmark validity

- **Parse-quality disentanglement metric.** **[done this sprint]** `format_compliance` / `communication_score` / `parse_adjusted_score` (experimental, additive; `overall` unchanged).
- **Provenance block everywhere.** **[done this sprint]** git commit + pricing version/as-of + model-set id added to the summary provenance block.
- **Paraphrase-robust scoring layer.** _Open._ Move beyond substring matching (add word boundaries + a small paraphrase set per signal) to cut keyword gaming — `--strict-quality` already warns on ~9 echo tasks.
- **Task-clustered bootstrap as default.** _Already shipped pre-sprint_ (`--bootstrap-cluster task`).
- **Per-family score-reliability diagnostics.** _Open._ Report per-family CI width / variance so thin families are visible.
- **Resume/checkpoint for long live runs.** **[design only this sprint]** `docs/design/resume_checkpoint.md`; implementation deferred to protect the byte-stable engine path.
- **Stronger safety detection beyond pattern blocklists.** _Open._ Add structural/semantic checks so safety is not purely regex blocklists.

## P2 — open-source polish

- **Contributor task-review checklist.** _Open._ A `judge-rubric-review`-style checklist in `CONTRIBUTING`.
- **Issue templates.** _Open._ `.github/ISSUE_TEMPLATE/` (task proposal, bug, provider request).
- **Docs examples + API adapter guide + sample-artifact guide.** _Partly present_ (`docs/provider_adapters.md`, `docs/samples/`); expand with runnable examples.
- **Release checklist.** _Present_ (`docs/release_checklist.md`); extend with the quality-status gate.
- **Optional CI alternative docs.** _Open._ Document a non-GitHub-Actions CI (local pre-commit / self-hosted) while Actions stay disabled.
- **Split the CLI god-module** into per-command-group modules.

## This sprint's scope (top P0/P1, offline, no fabrication)

Shipped: the quality **scorecard** + current-state audit + this backlog; `quality status`;
`validate --strict-quality`; experimental **parse-quality** metrics; **provenance** completion; the
repo-hygiene guard; a resume/checkpoint **design doc**; and honest doc refresh. Deferred (need real
annotators or live APIs): the human round, rule/judge-vs-human calibration, paraphrase-robust
scoring, and resume/checkpoint implementation.
