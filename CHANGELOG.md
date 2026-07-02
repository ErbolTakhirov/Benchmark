<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

All notable changes to CompanionBench are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Pre-alpha history (the initial pipeline
scaffold, provider adapters, EMOTomo model set, pricing/frontier/bootstrap work) lives in `git log`
rather than being reconstructed here.

## [Unreleased]

### Real human-annotation workflow

Prepares (but does not fabricate) a **real** human-annotation round to calibrate the rule scorer
against human judgment. See `docs/human_gold_set.md`.

- **Annotation packet** at `analysis/annotation_round_v0_1/`: `README_FOR_ANNOTATORS.md`,
  `annotation_instructions.md`, `annotation_examples.md`, `rubric_short.md`, `rubric_full.md`,
  `consent_and_privacy_note.md`, and a **blinded** `annotation_packet.csv` + `.jsonl` — 72 items,
  12 per family, incl. strong / weak / parse-format / unsafe-overreach / abstention / generic-empathy
  / preference-adaptation cases. Stimuli are offline-simulator outputs over real tasks (NOT
  model-under-test outputs); model identity is hidden and the `response_id → source` map is kept
  private/git-ignored.
- **De-identifying importer** `companion-bench gold import-human`
  (`companion_bench.gold_ingest`): salted-hash of annotator handles, drops name/email/phone columns,
  validates ratings, and **refuses to write** if an email/phone survives in the free text. Stamps
  `source_type=real_human_pilot`. Salt comes from `--annotator-id-hash-salt-env`; no network.
- **Privacy**: raw annotations live only in `data/gold/private/` (git-ignored — README + `.gitkeep`
  tracked, contents never); `.gitignore` re-includes the committed packet but keeps its `private/`
  working dir (blinding map) ignored. `calibrate rules` now surfaces mismatched gold/response ids.
- Docs updated (`human_gold_set.md`, `judge_calibration.md`, `results_interpretation.md`,
  `benchmark_card.md`); tests in `tests/test_gold_import.py`.
- **No real labels collected yet** — operator sends the packet to ≥3 annotators, drops returned
  files in `data/gold/private/`, runs `gold import-human`, then `gold agreement` + `calibrate rules`.

### Human-agreement + judge-calibration pilot

A small, offline-first pilot for **external validity**: human gold labels + an opt-in LLM judge,
both **calibration signals reported alongside — never replacing — the rule-based scores**. See
`docs/human_gold_set.md` and `docs/judge_calibration.md`.

- **Gold-label schema** (`companion_bench.schemas.gold`): per-annotator, per-response 1–5 ratings +
  confidence + rationale + flags across the six canonical dimensions, `overall_preference`
  (accept/reject/borderline), opaque `annotator_id_hash` (no names/emails), and provenance
  (`source_type`, `not_human_collected`, `pii_check`). Multiple annotators per item supported.
- **Agreement metrics** (`companion_bench.evaluators.agreement`, stdlib): percent agreement, Cohen's
  kappa (2 annotators), Krippendorff's alpha (nominal + ordinal; verified against the reference
  example), Pearson/Spearman, missingness. CLI: `companion-bench gold validate|agreement`.
- **Rule-vs-gold + judge-vs-gold calibration** (`companion_bench.evaluators.calibration`): per-
  dimension MAE/Pearson/Spearman + accept/reject agreement + top disagreements, with pilot caveats.
  CLI: `companion-bench calibrate rules|judge`. Calibration never changes any score.
- **Opt-in LLM-as-judge** (`companion_bench.evaluators.judge`, `judge_prompts`, and a realized
  `rubric.LLMJudgeRubricEvaluator`): versioned prompt, hidden model identity, strict-JSON parsing
  (malformed → recorded failure, never coerced), separate `judge_scores.json`/`judge_events.jsonl`.
  An **offline mock judge** validates the pipeline; a **real judge is live-gated** (`--live` +
  `COMPANIONBENCH_LIVE=1` + `--max-cost-usd` + confirmation). CLI: `companion-bench judge`.
- **Pilot fixture** (`data/gold/`): 14 sanitized responses across all six families (strong / weak /
  parse-format / unsafe-overreach / abstention / generic-empathy / preference-adaptation) with 3
  **synthetic** annotators, plus `README.md` and `annotation_template.csv`. Clearly marked
  `not_human_collected` — a schema/test fixture, not real human data or a leaderboard.
- New docs `docs/human_gold_set.md`, `docs/judge_calibration.md`; updated `docs/scoring.md`,
  `docs/results_interpretation.md`, `docs/methodology.md`, `docs/benchmark_card.md`,
  `docs/public_claims.md`. `.gitignore`: `analysis/` (generated) + `data/gold/private/` (PII).
- **No live judge run was performed**; live judge-vs-human calibration is marked REQUIRES LIVE RUN.

### Scoring-validity hardening (**scoring v1.1.0**)

Scoring-validity hardening sprint (**scoring v1.1.0**), acting on
`docs/audits/v0_1_alpha_benchmark_validity_audit.md`. Rule-based scoring only — no LLM judge, no
task retuning, no model-config changes. **Scores produced under scoring v1.1.0 are not directly
comparable to the pre-1.1 sample results in `docs/samples/`; re-run to compare.**

### Changed

- **Parse-failure policy.** A missing, empty, or malformed model output no longer earns positive
  safety credit. `safety` is `None` (not-applicable) when there is nothing to judge — a provider
  failure (empty text), a malformed output with no detectable violation, or a decision with an empty
  message (e.g. a bare `wait`). A real violation in malformed free text is still caught. This closes
  the audit's headline defect (a failed initiative-task call scored ~0.333, not 0) and the always-
  wait safety refuge. Outcomes are classified `ok` / `provider_failure` / `malformed`
  (`rule_based.outcome_kind`).
- **Self-report verification.** Model-controlled labels are checked against the message prose:
  `style` (blunt prose vs a claimed gentle/reassuring label), `ask_permission` (verified against a
  permission phrase, not the boolean), and a `wait` decision that actually delivers advice.
- **Timing de-redundancy.** When a task's `allowed_intervention_window` exactly equals its set of
  intervene-expected probes, timing is reported but zero-weighted so it no longer double-counts the
  intervene decision. A genuinely different window re-activates timing automatically.
- **Bootstrap defaults to task-clustered CIs** (`--bootstrap-cluster task`), which resamples whole
  tasks so repeats are treated as pseudo-replicates. The legacy per-unit behavior is available with
  `--bootstrap-cluster unit`. Clustered CIs are wider and more honest.
- `test_runner_smoke.py` persona-ordering assertions re-baselined to v1.1 semantics.

### Added

- New behavior flags (score-inert diagnostics): `provider_failure`, `malformed_output`,
  `self_report_mismatch`, `claimed_permission_without_phrase`, `claimed_empathy_without_validation`,
  `claimed_wait_but_advised`, `generic_validation_only`.
- Adversarial mock profiles (`src/companion_bench/adapters/mock.py` +
  `configs/model_sets/adversarial-mocks.yaml`): `generic-empathy-v1`, `style-liar-v1`,
  `permission-liar-v1`, `always-advise-v1`, `wait-liar-v1`, `always-abstain-v1` — each targets a
  gaming vector the scorer must penalize.
- `tests/test_scoring_adversarial.py` and `tests/test_adversarial_mocks.py` — scorer- and
  mock-level coverage for parse failures, safety-on-empty, self-report lies, always-wait/abstain/
  advise refuges, timing/initiative divergence, and clustered bootstrap.
- **Provenance block** in every `summary.md` and a footer in `report` output: benchmark version,
  `scoring_version` + `scorer_type`, manifest path + task count, provider, repeats, and bootstrap
  method/seed. `scores.json` now carries `scoring_version`, `scorer_type`, and `bootstrap_method`.

## [0.1.0-alpha] - 2026-07-02

Public-alpha readiness pass: local-first, expanded task suite, full open-source scaffolding, and
a completed live evaluation run on the expanded suite.

### Added

- Task suite grown from 10 public + 2 held-out tasks per family to **25 public + 6 held-out per
  family** (150 public + 36 held-out = 186 tasks total, across all six families: initiative,
  empathy, timing, adaptation, abstention, safety).
- `tests/test_signal_disjointness.py` — a suite-wide, mechanism-accurate automated check that no
  task's own positive signals can trip its own safety boundaries (previously enforced only by
  author discipline).
- Open-source project scaffolding: `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `CITATION.cff`, this `CHANGELOG.md`.
- New docs: `docs/index.md`, `docs/local_verification.md`, `docs/results_interpretation.md`,
  `docs/release_checklist.md`, `docs/results_v0_1_alpha.md` (the release results writeup),
  `docs/release_notes/v0.1.0-alpha.md`, `docs/ci-disabled/` (archived CI workflow + rationale).
- New project skills: `task-suite-review` (suite-wide invariant sweep), `docs-polish`
  (doc-freshness sweep).
- `docs/audits/final_open_source_readiness_audit.md` (baseline, before this pass) and
  `docs/audits/public_alpha_release_readiness.md` (final state, after this pass).
- **A completed live OpenRouter model-set run on the fully expanded suite**: 10 models × 150
  public tasks and 10 models × 36 held-out tasks, 5 repeats each, bootstrap 95% CIs. Sanitized
  samples added at
  [`docs/samples/companionbench-emotomo-public-expanded-r5/`](docs/samples/companionbench-emotomo-public-expanded-r5/)
  and
  [`docs/samples/companionbench-emotomo-heldout-expanded-r5/`](docs/samples/companionbench-emotomo-heldout-expanded-r5/)
  (raw transcripts excluded, secret-scanned clean). This is the first like-for-like comparison of
  both suites at their final expanded sizes: Pearson 0.968, Spearman 0.939 — see
  `docs/results_v0_1_alpha.md`.

### Changed

- GitHub Actions CI removed (`.github/workflows/ci.yml` deleted) — the hosting account has an
  account-level Actions billing lock unrelated to this repo's code. The repo is now **local-first**:
  `docs/local_verification.md` is the source of truth, and the archived workflow lives at
  `docs/ci-disabled/ci.yml.txt` for reference/future re-enabling.
- `config/pricing.py`'s `load_pricing()` now raises a clean `ConfigError` on a missing/bad explicit
  `--pricing` path, matching the other config loaders, instead of a raw `FileNotFoundError`.
- README, `CLAUDE.md`, and `docs/task_authoring.md` updated to reflect the current six-family,
  186-task suite (previously described a stale 8-task/4-family state); README also gained an
  explicit "what this does NOT measure" section, a repository-structure tree, sample-results links,
  and a citation section; the dead CI badge was replaced with a local-verification note.
- `pyproject.toml`'s `[project.urls]` fixed to point at the real repository instead of a
  placeholder org.

### Removed

- `utils/errors.py`'s unused `BudgetExceededError` and `ResponseParseError` exception classes
  (never raised anywhere — budget/parse failures are already signaled through
  `run_result.budget_exceeded` and `CompanionTurn.parsed`).

### Fixed

- `docs/audits/final_open_source_readiness_audit.md`'s own description of the public-claims guard
  test briefly quoted the exact phrase the guard forbids, tripping its own check.

## Earlier history

See `git log` for the full pre-alpha history: the initial offline pipeline scaffold, real
provider adapters, the EMOTomo OpenRouter model set, repeats + bootstrap confidence intervals,
the cost-quality frontier, and the first sanitized live-run samples.
