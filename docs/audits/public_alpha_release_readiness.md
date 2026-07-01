<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — public alpha release readiness audit (final state)

**Auditor framing:** external reviewer, same lens as
[`final_open_source_readiness_audit.md`](final_open_source_readiness_audit.md) (the "before"
snapshot for this pass). **Date:** 2026-07-01. **Scope:** the repository after this session's
Actions-removal, architecture-cleanup, task-suite-expansion, docs, code-review, and verification
work.

## Verdict: public alpha, ready to publish

Both halves that the baseline audit found split — a public-alpha-ready **instrument** and an
MVP-scaffold **project** — are now aligned. The instrument side kept its existing strengths
(deterministic, reproducible, secret-safe scoring; real live-provider results already on record);
the project side closed every concrete gap the baseline audit listed. Nothing found in this pass
is a release blocker — the honest gaps below are v0.1-stable roadmap items, not v0.1-alpha
blockers.

| Maturity ladder | Status |
| --- | --- |
| not ready | — |
| MVP ready | ✅ exceeded |
| **public-alpha ready** | ✅ **current** |
| v0.1 release candidate | ◑ close — see "what's still weak" |
| serious benchmark ready | ⛔ blocked on human/LLM-judge calibration, outside task review |

## What's working

- **Local-first, no dependency on a broken CI signal.** `.github/` is gone entirely; the archived
  workflow lives at `docs/ci-disabled/ci.yml.txt`; `docs/local_verification.md` is the documented,
  exercised replacement (every command in it was run this session and passed).
- **Task suite grew 2.5x**: 60→150 public tasks, 12→36 held-out, still perfectly balanced (25/6
  per family across all six families). Authored by six parallel passes (one per family) following
  a fixed schema/invariant checklist, then verified suite-wide (global `task_id` uniqueness,
  manifest partition correctness, a full mock run+score in both `empathetic-v1` and
  `intrusive-v1`).
- **A real, previously-missing automated safety-disjointness check now exists and was
  code-reviewed into a stronger form**: `tests/test_signal_disjointness.py` drives every
  safety-boundary-carrying task through the actual mock+scorer pipeline (not a hand-rolled
  re-derivation of the matching logic), so it can't silently drift from the mechanism it
  protects, and it catches join-boundary cases a naive per-signal check would miss (confirmed by
  live reproduction during code review, then fixed).
- **Architecture is clean.** Two real, low-risk fixes landed (`load_pricing`'s error handling,
  removal of two dead exception classes); everything else was independently reviewed and judged
  sound — no rewrite, matching the instruction to change only what's broken.
- **Full open-source scaffolding now exists**: CONTRIBUTING, SECURITY, CODE_OF_CONDUCT,
  CITATION.cff, CHANGELOG, a docs index, a results-interpretation guide, a release checklist, and
  two new project skills (`task-suite-review`, `docs-polish`).
- **Every local gate is green**: ruff, format, mypy (strict), pytest (182 passed, 1 skipped —
  live), `uv build`, all three manifests validate, offline mock runs pass, and a small live
  OpenRouter smoke run (2 models, $0.002) confirms the pipeline still works against a real
  provider after the suite expansion.
- **A `/code-review` pass and a `/verify` pass both ran** against this session's diff; the real
  findings from both were fixed (test-mechanism drift, held-out coverage gaps in two suite
  checks, a `FAMILY_DEFAULT_WEIGHTS` completeness gap), not just logged.

## What's still weak (honest gaps, not blockers)

1. **Held-out validation was run on the *previous* 12-task split, not the new 36-task split.**
   The existing sample (`docs/samples/companionbench-emotomo-heldout-r5/`) showed the coarse
   "good vs. weak" signal generalizes (Pearson 0.858) while fine ranking did not (Spearman 0.573)
   — informative, but it predates this session's task-suite growth. Re-running held-out
   validation on the new 36-task split is the single most valuable next live-data step, and was
   deliberately **not** done in this session (no large live benchmark, by instruction).
2. Scoring is still rule-based with known gaming surfaces: substring/keyword matching, no
   verbosity penalty on generic empathy, a safety pattern-blocklist that misses novel unsafe
   phrasings. LLM-as-judge and human calibration remain an intentional, unimplemented seam
   (`evaluators/rubric.py`).
3. The suite is still fully synthetic, authored this session by AI agents against a fixed
   checklist and empirically self-verified — not yet reviewed by outside human evaluators, and
   English-only.
4. A few small, explicitly-deferred code-quality items surfaced by this session's `/code-review`:
   `config/providers.py::load_providers_config` still lacks the `is_file()` guard its three
   sibling loaders now have (a bad `--providers-config` path still raises a raw error there);
   `tests/test_safety_audit.py`'s "reliably catches" regression guard uses floor division
   (`len(safety_tasks) // 2`), which could tolerate the suite regressing to just under half before
   failing; `load_pricing`'s "not found" message is technically imprecise for an existing-but-not-
   a-file path (e.g. a directory) — cosmetic, matches the existing sibling convention.
5. Bootstrap CIs still treat `(task, repeat)` units as i.i.d. without task-level
   stratification/blocking — a defensible approximation on this suite size, not population-level
   inference (documented, not hidden).
6. GitHub Actions remains billing-locked at the account level; this is an external constraint, not
   something this session could resolve — local verification is the accepted interim source of
   truth.

## Task counts (final)

| Family | Public | Held-out |
| --- | --- | --- |
| initiative | 25 | 6 |
| empathy | 25 | 6 |
| timing | 25 | 6 |
| adaptation | 25 | 6 |
| abstention | 25 | 6 |
| safety | 25 | 6 |
| **Total** | **150** | **36** |

`manifests/smoke.yaml`/`mvp.yaml`/`emotomo_smoke.yaml` remain pinned at their original 8 tasks
(4 families, 2 each) for fast pipeline sanity checks — untouched by this expansion, as intended.

## Held-out validation summary (historical, pre-expansion — see gap #1 above)

From `docs/samples/companionbench-emotomo-heldout-r5/` (12-task split, 10 models via OpenRouter,
5 repeats): Pearson (held vs. full overall) **0.858**; Spearman (rank correlation) **0.573**; held
mean 0.700 vs. full mean 0.698 (no difficulty drift). Top-1 and bottom-2 models survived with
non-overlapping CIs; the statistically-tied middle reshuffled. Read as: the coarse signal
generalized on the suite as it stood *before* this session's expansion; it has not yet been
re-checked on the larger 36-task held-out split.

## Sample results available

Seven sanitized sample run directories under `docs/samples/`, none a leaderboard:
`companionbench-emotomo-fullsuite-r5`, `companionbench-emotomo-heldout-r5`,
`companionbench-emotomo-modelset-full-r3`, `emotomo-openrouter-full-r3`, `emotomo-openrouter-smoke`,
`pipeline-demo-r3`, `audit-openrouter-humanlike-r2-small`.

## Local verification (exact commands, all run and passing this session)

```bash
uv sync --all-extras
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest -q
uv run companion-bench validate manifests/smoke.yaml
uv run companion-bench validate manifests/full.yaml
uv run companion-bench validate manifests/heldout.yaml
uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/check
uv run companion-bench score --run runs/check
uv build
```

Full sequence with rationale: [`docs/local_verification.md`](../local_verification.md).

## Security status

Every artifact created this session (audits, docs, 186 task YAMLs, test files, sample runs) was
checked for secret leakage at multiple points this session (value-scan seeded from the live
environment, plus regex shape-grep); all clean. `.env` and `runs/` never staged. A final,
comprehensive scan of the complete working tree and the full diff since `origin/main` runs
immediately before push (see the commit that follows this one).

## No-active-Actions note

Confirmed: `.github/` does not exist on disk (verified via `find` during `/verify`, not just
`git log`). `docs/ci-disabled/README.md` documents why and how to restore it.

## Top 10 next improvements before v0.1 stable

1. Re-run held-out validation live on the new 36-task split (biggest single next step).
2. Start the LLM-as-judge path behind the existing `RubricEvaluator` seam, with a small human
   gold-label set for rules-vs-judge-vs-human calibration.
3. Reduce substring-gaming: paraphrase-robust matching (synonym sets, embeddings, or judge
   calibration) and an empathy verbosity/genericness penalty.
4. Promote the suite-quality invariants currently enforced only by tests (safety tasks must
   declare `safety_boundaries`, every task must declare `expected_abstention_behavior` +
   `failure_modes`) into a schema-level check or a `companion-bench validate` extension, so they
   apply to any manifest, not just the two tests happen to load.
5. Layer safety detection (patterns + a classifier) so novel unsafe phrasings are caught, not just
   pre-authored patterns.
6. Stratified/blocked bootstrap by task, with per-task variance reported alongside the aggregate.
7. Get the task suite in front of outside human reviewers; add non-English coverage.
8. Fix the small deferred code-quality items from this session's review: guard
   `load_providers_config`'s file read like its three siblings; tighten
   `test_safety_audit.py`'s floor-division threshold; consider a shared YAML-loader helper across
   the four near-identical loaders if a fifth one is ever added.
9. Add a provenance block to every report (provider, model-version snapshot, pricing `as_of`,
   scoring version) for defensible cross-run comparison.
10. Resolve the GitHub Actions billing lock (or adopt an alternative CI provider) and re-enable
    automated verification on every PR, using `docs/ci-disabled/ci.yml.txt` as the starting point.
