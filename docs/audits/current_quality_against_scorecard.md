<!-- SPDX-License-Identifier: Apache-2.0 -->
# Current Quality Against the Scorecard (v0.1.0-alpha)

Audited **2026-07-03** against [`benchmark_quality_scorecard.md`](benchmark_quality_scorecard.md).
Grades are grounded in the repo, its tests, its samples, and the adversarial validity audit
([`v0_1_alpha_benchmark_validity_audit.md`](v0_1_alpha_benchmark_validity_audit.md)). That audit was
written at commit `feb4e88`, **before** the v1.1.0 scoring hardening and the agreement/calibration
pilots; where those later commits closed a defect, the grade reflects the current state and says so.

**Overall: 6.35 / 10** — a credible public alpha. **Lowest: Human agreement / external validation
(2.5)** and **LLM-judge calibration (3.5)**. **Highest: Security (9.0)** and **Reproducibility (8.0)**.

---

### 1. Methodology validity — 7.0/10
- **Evidence:** narrow behavioral objective (`README.md`, `docs/methodology.md`); strict claims policy + machine guard (`docs/public_claims.md`, `tests/test_public_claims.py`); headline public↔held-out correlation reproduces (Pearson 0.968 / Spearman 0.939, App. A of the validity audit).
- **Blockers to 9:** operationalize and partially test the research hypothesis (`docs/hypothesis.md`); retire every unreproducible statistic from the docs (the old Spearman 0.573 recomputes to 0.612).
- **Blockers to 10:** independent methodological review; validate the construct against an external criterion (needs §4).
- **Tasks:** finish de-staling `docs/benchmark_card.md` (done this sprint); add a hypothesis-test writeup.

### 2. Task suite quality — 6.5/10
- **Evidence:** 186 tasks, perfect 6×31 family balance, held-out split (`tests/test_task_suite.py`); safety-signal disjointness driven through the real pipeline (`tests/test_signal_disjointness.py`); now a validate-time gate (`validate --strict-quality`).
- **Blockers to 9:** calibrated, discriminating difficulty; paraphrase-robust signals (keyword-echo warnings still fire on ~9 tasks — surfaced by `--strict-quality`); some external authoring review.
- **Blockers to 10:** multiple suite generations; **non-English / cross-cultural coverage** (currently English-only); independent task review.
- **Tasks:** a paraphrase-robust scoring layer; a difficulty-calibration pass; a non-English pilot family.

### 3. Scoring validity — 6.0/10
- **Evidence:** deterministic rule-based scorer; v1.1.0 closed the parse-failure asymmetry, the always-wait safety refuge, self-report style/permission gaming, and timing double-counting (`docs/scoring.md`, `tests/test_scoring_adversarial.py`, `tests/test_adversarial_mocks.py`). Parse quality is now **disentangled** from content (`format_compliance` / `communication_score` / `parse_adjusted_score`, experimental).
- **Blockers to 9:** paraphrase/semantic matching (still substring-based, no word boundaries); calibration of the scorer against humans (needs §4).
- **Blockers to 10:** demonstrated correlation with a human criterion within a stated tolerance.
- **Tasks:** word-boundary + paraphrase matching; ship the parse-adjusted view in the results doc.

### 4. Human agreement / external validation — 2.5/10  ← gating weakness
- **Evidence:** **No real human labels exist** — `data/gold/private/` holds only `README.md` + `.gitkeep`. The committed gold set is a **synthetic** fixture (`data/gold/pilot_v0_1_alpha.jsonl`, every row `not_human_collected: true`). The *workflow* is ready: schema, agreement metrics (Cohen's κ, Krippendorff's α), a PII-refusing importer, and a blinded annotation packet (`analysis/annotation_round_v0_1/`). `companion-bench quality status` reports `gold label source = synthetic pilot` and warns against any "human-validated" claim.
- **Blockers to 9:** run a **real** ≥3-annotator round, import de-identified labels, and report inter-rater agreement above threshold + rule-vs-human calibration.
- **Blockers to 10:** a published, independently reproduced human study.
- **Tasks:** collect the real round (operator step, out of scope for offline work); then `gold agreement` + `calibrate rules`.

### 5. LLM-judge calibration quality — 3.5/10
- **Evidence:** the judge seam is implemented (offline mock + live-gated real, `evaluators/judge.py`, `docs/judge_calibration.md`), stored separately (`judge_scores.json`), never the source of truth. **No live judge run and no judge-vs-human calibration have been performed** (both marked REQUIRES LIVE RUN).
- **Blockers to 9:** a live judge run calibrated against **real** human labels (depends on §4); quantified judge bias/agreement.
- **Blockers to 10:** calibration reproduced across judge models.
- **Tasks:** after §4, run `calibrate judge` on real labels; report bias.

### 6. Statistical reliability — 6.5/10
- **Evidence:** repeats + bootstrap CIs, **task-clustered by default** (`--bootstrap-cluster task`), which fixes the ~1.7×-too-narrow pseudoreplicated CIs the audit flagged (`evaluators/aggregate.py`, `tests/test_bootstrap.py`).
- **Blockers to 9:** per-family reliability diagnostics; drop any overstated tier-separability claim; more than one suite generation.
- **Blockers to 10:** power analysis; pre-registered separability thresholds.
- **Tasks:** a per-family CI/variance diagnostic in the report.

### 7. Reproducibility — 8.0/10
- **Evidence:** byte-deterministic mock runs under `FrozenClock` (`tests/test_runner_smoke.py`); green local gates; keyless offline path; provenance block now includes **git commit + pricing table/as-of + model-set id** (`evaluators/aggregate.py`, `tests/test_provenance.py`); `uv build` succeeds.
- **Blockers to 9:** resume/checkpoint for long live runs (**design only** this sprint — `docs/design/resume_checkpoint.md`); a pinned/locked environment story.
- **Blockers to 10:** an independent third-party reproduction on record.
- **Tasks:** implement resume/checkpoint from the design doc; document environment pinning.

### 8. Security / artifact hygiene — 9.0/10
- **Evidence:** no secrets in tree/history; `.env` untracked; raw `runs/`, `*.parquet`, and `data/gold/private/*` gitignored and now **test-guarded** (`tests/test_repo_hygiene.py`, `tests/test_secrets.py`); sanitized samples; PII-refusing gold importer (`gold_ingest.py`).
- **Blockers to 9→10:** audited supply chain; signed releases.
- **Tasks:** signed release artifacts when packaging.

### 9. Architecture / maintainability — 7.5/10
- **Evidence:** clean layered DAG, provable adapter isolation, injectable clock, strict `mypy` + `ruff`; new logic is modular (`quality.py`, `runner/quality_checks.py`, `utils/gitmeta.py`) with shared predicates (tests + CLI use one implementation).
- **Blockers to 9:** the CLI is a large single module (~1.3k LOC) — split into command groups.
- **Blockers to 10:** a documented stable public API + deprecation policy.
- **Tasks:** refactor `cli.py` into per-group modules.

### 10. Open-source usability / documentation — 7.0/10
- **Evidence:** Apache-2.0, `CONTRIBUTING`/`SECURITY`/`CODE_OF_CONDUCT`/`CITATION`/`CHANGELOG`, thorough `docs/` + project skills; `quality status` gives newcomers a one-command honesty snapshot.
- **Blockers to 9:** issue templates + contributor task-review checklist; a packaged (PyPI) release; a stable CI or a documented substitute beyond local gates.
- **Blockers to 10:** an active external contributor community.
- **Tasks:** add `.github/ISSUE_TEMPLATE/`, a contributor task-review checklist, and a CI-alternative doc.

---

## What must NOT be claimed yet

- **Not** "human-validated / human-aligned / human-approved" — no real labels exist (§4).
- **Not** "most human-like / best companion" or any fine, statistically distinguishable rank order.
- **Not** "the LLM judge shows model X is best" — the judge is uncalibrated and auxiliary (§5).
- **Never** an "EMOTomo benchmark" or an "OpenRouter benchmark" — those are a model set and a
  provider, never the benchmark's identity.
- **Not** "safe for vulnerable users." Scores are scoped to these tasks, settings, model versions,
  and this scorer design.

## Highest-impact next work

1. **Run the real human annotation round** (§4) — unlocks §4, §5, and part of §3 at once. This is the single biggest lever from 6.35 toward 8+.
2. **Paraphrase-robust scoring + word-boundary matching** (§3) — the largest remaining scorer artifact.
3. **Non-English pilot family** (§2) and **per-family reliability diagnostics** (§6) — breadth + honesty.
