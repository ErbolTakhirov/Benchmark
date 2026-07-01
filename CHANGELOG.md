<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

All notable changes to CompanionBench are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Pre-alpha history (the initial pipeline
scaffold, provider adapters, EMOTomo model set, pricing/frontier/bootstrap work) lives in `git log`
rather than being reconstructed here.

## [0.1.0-alpha] - 2026-07-01

Public-alpha readiness pass: local-first, expanded task suite, full open-source scaffolding.

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
  `docs/release_checklist.md`, `docs/ci-disabled/` (archived CI workflow + rationale).
- New project skills: `task-suite-review` (suite-wide invariant sweep), `docs-polish`
  (doc-freshness sweep).
- `docs/audits/final_open_source_readiness_audit.md` (baseline, before this pass) and
  `docs/audits/public_alpha_release_readiness.md` (final state, after this pass).

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
