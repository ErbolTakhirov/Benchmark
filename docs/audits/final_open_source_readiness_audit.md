<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — final open-source readiness audit (baseline, pre-v0.1-alpha pass)

**Auditor framing:** external reviewer deciding whether CompanionBench is a serious public-alpha
open-source benchmark. **Date:** 2026-07-01. **Scope:** the repository as it stands *before* this
session's Actions-removal / architecture / task-expansion / docs pass — i.e. this is the honest
"before" snapshot that the rest of this session's work (see
[`public_alpha_release_readiness.md`](public_alpha_release_readiness.md) for the "after") is
scoped against. It supersedes [`benchmark_quality_audit.md`](benchmark_quality_audit.md)
(2026-06-30), which predates the six-family task-suite expansion and the held-out validation run
and is kept only as a dated historical artifact.

> CompanionBench evaluates **targeted human-like companion-communication behaviors in defined
> multi-turn scenarios**: emotional attunement, appropriate initiative, timing and pacing,
> non-intrusion/abstention, preference adaptation, and safety boundaries. **EMOTomo is one example
> model set; OpenRouter is one example provider adapter** — neither is the benchmark's identity.
> `overall` is a companion-communication score, **not** a universal "humanity" score. Results are
> **sample runs, not a final leaderboard**, scoped to the tasks, settings, and model versions
> actually run.

## Verdict

**Benchmark instrument: public-alpha ready, trending toward release-candidate.**
**Open-source project: MVP-scaffold — not yet public-alpha ready as a released project.**

| Maturity ladder | Instrument | Project (docs/process/CI) |
| --- | --- | --- |
| not ready | — | — |
| **MVP ready** | ✅ exceeded | ✅ **current** |
| **public-alpha ready** | ✅ **current** | ⛔ blocked (see below) |
| serious-benchmark ready | ◑ closer than 2026-06-30 (held-out validation now exists) | ⛔ |

The scoring engine, task schema, reproducibility, and security posture are unchanged and remain
strong (§3-5, §7 below carry forward the 2026-06-30 audit's findings, re-verified). What has
materially improved since that audit: the task suite grew from 8 tasks/4 families to **60 public +
12 held-out tasks across all 6 families** (abstention and safety are now first-class, not
cross-cutting-only), and a **held-out generalization check has actually been run** — a real
first for this project (§5). What is now the binding constraint is **open-source project
hygiene, not benchmark methodology**: no CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/CITATION/CHANGELOG,
a GitHub Actions workflow that cannot run (account-level billing lock) with no local-first
fallback documented, two small but real code-quality nits, stale figures in three docs, and
`pyproject.toml` metadata pointing at a placeholder org. None of these are benchmark-validity
problems; all of them block a stranger from trusting and using the repo. That is exactly the gap
this session's remaining phases close.

## 1. Benchmark objective — strong, unchanged

Stated narrowly and behaviorally (`docs/methodology.md`, `docs/benchmark_card.md`): the
communication *choices* a thoughtful companion makes in a scripted moment — whether/when/how to
speak, ask permission, hold a boundary, or abstain. Non-goals (general intelligence, fluency,
consciousness, genuine emotion, safety certification) are explicit and repeated in
`README.md`/`docs/public_claims.md`. Model-set/provider separation from the benchmark's identity
is **mechanically enforced** by `tests/test_public_claims.py`, which fails the build on
"EMOTomo/OpenRouter benchmark" phrasing. No "humanity score" naming survives anywhere in code
(`schemas/score.py` carries an explicit guard comment); the only `human`-adjacent identifier is the
unrelated `SourceType.HUMAN_GOLD` (task provenance, not a score).

## 2. Task suite — six families, real scale, still synthetic and unreviewed

- **Public: 60 tasks, 10 per family** across `initiative, empathy, timing, adaptation, abstention,
  safety`. **Held-out: 12 tasks, 2 per family**, structurally excluded from the public manifest
  (`manifests/full.yaml` globs `tasks/*/*.yaml`, non-recursive, so `tasks/*/heldout/*.yaml` is
  unreachable; `manifests/heldout.yaml` targets exactly that subdirectory).
- Every task is versioned YAML declaring scenario, persona, scripted turns, probes, intervention
  window, `expected_abstention_behavior`, explicit `metadata.failure_modes`, rubric weights, and
  positive/negative signals (`schemas/task.py`, `extra="forbid"`).
- **Abstention and safety are now first-class families** (10 public + 2 held-out tasks each), not
  cross-cutting afterthoughts — the single biggest suite improvement since the last audit.
- Negative ("don't intervene") controls exist across families, so over-intervention is penalizable,
  not just under-intervention.
- **Risks, unchanged in kind, larger in surface area now that there are 72 tasks instead of 8:**
  synthetic personas, English/Western-default norms, no peer review, no non-English coverage, and
  the disjointness invariant between `positive_signals`/`expected_target_keywords` and
  `safety_boundaries.forbidden_patterns` (needed so the *correct* mock persona doesn't self-trip a
  safety violation by using its own correct answer) is currently enforced only by author
  discipline, with **no automated suite-wide test**.
- 10 (public) / 2 (held-out) tasks per family is still thin for fine-grained ranking — the held-out
  run itself (§5) empirically demonstrates this.

## 3. Scoring validity — transparent, same gaming surface as before

Rule-based, deterministic, null-excluding with weight renormalization over applicable dimensions;
family-default weights guarantee safety/abstention always carry some weight for every family
(`evaluators/rule_based.py`). Verified behavior, consistent with the 2026-06-30 audit:

- Always-intervene/intrusive personas are well-penalized (timing/initiative zero out
  out-of-window or unwanted interventions); always-abstain cannot score high in general but
  resistance is probe-mix-sensitive.
- **Substring matching remains the dominant gaming vector** — `positive_signals`/
  `expected_target_keywords` are matched as case-insensitive substrings, so keyword-stuffing the
  expected phrase verbatim maximizes sub-scores. No length/verbosity penalty exists for generic
  empathy; detection is a blocklist over authored `negative_signals`.
- Safety is the strongest dimension (hard pattern floors, soft penalties, missing-permission
  penalty) but is a **pattern blocklist** — novel unsafe phrasings pass undetected; default is
  innocent-until-matched.
- Flag surfacing has improved since 2026-06-30 (`generic_empathy`, `missed_emotional_validation`
  are now wired in `evaluators/flags.py`) but some computed signals (`partial_target`,
  `abstained_instead_of_waiting`, `waited_instead_of_abstaining`, `acted_when_abstention_expected`)
  remain unsurfaced.

## 4. Statistical reliability — materially stronger than the last audit

This is the most-improved area since 2026-06-30:

- `--repeats N` + `score --bootstrap` (percentile 95% CIs, deterministic seed) both exist and are
  exercised, not just implemented.
- A **60-task, 5-repeat, 10-model live run** (`docs/samples/companionbench-emotomo-fullsuite-r5/`)
  tightened CIs from ~±0.13 (the old 8-task run) to **~±0.025**, producing three genuinely
  distinguishable tiers instead of total overlap — a real, demonstrated improvement in
  discriminative power from suite growth alone.
- A **held-out validation run** now exists (`docs/samples/companionbench-emotomo-heldout-r5/`,
  12 hidden tasks never tuned against) — the first time this project has checked whether its
  ranking generalizes off the tasks it was built around. Result: **Pearson 0.858** (scores track
  strongly), **Spearman 0.573** (exact rank order shifts moderately, concentrated in a
  statistically-tied middle tier), held-mean 0.700 ≈ full-mean 0.698 (no difficulty-drift/leakage).
  Top-1 and bottom-2 models survived with non-overlapping CIs; the middle did not survive as an
  ordering. This is exactly the honest, expected signature of a public-alpha suite: coarse
  signal generalizes, fine ranking does not yet.
- Bootstrap still treats `(task, repeat)` units as i.i.d. without task-level
  blocking/stratification — a documented, defensible approximation on a still-small suite, not
  population-level inference.

## 5. Reproducibility — strong, unchanged

`run.json` records package version, manifest path, seed, provider, model id, resolved task ids,
and repeat count; `events.jsonl` retains full transcripts, tokens, latency, cost, and
`model_failure` events. Runs are deterministic under `FrozenClock`; retry-backoff jitter is
seeded per `task:probe:repeat:attempt`. A fresh clone runs the whole pipeline offline and keyless.
Live calls require `--live` **and** `COMPANIONBENCH_LIVE=1` **and** `--yes`/confirm, and are
budget-capped (`--max-cost-usd` best-effort, `--limit-tasks`/`--limit-models` hard caps). Cost is
`null` when unknown, never invented.

## 6. Security — strong, tested, unchanged

Keys resolve only from `os.environ`, never CLI args or YAML. `.env`/`.env.*` are gitignored
(`.env.example` stays keyless). `utils/secrets.py` provides `collect_secret_values`/`redact`/
`scan_paths_for_secrets`/`scan_run_dir`, exercised by `tests/test_secrets.py` (proves a key reaches
the request header but never a persisted artifact, tested against both a fake and the real env
value). `runs/` is gitignored; every committed sample run in `docs/samples/` is a hand-curated,
secret-scanned subset (no raw `events.jsonl`, no `run.json`).

## 7. Open-source readiness — the actual gate right now

| Item | Status |
| --- | --- |
| README clarity | Present (1705 words), largely good, but **stale**: says "8 smoke tasks, 2 per family" (actually 60/12 across 6 families); CI badge points at a workflow about to be deleted; no "what this does NOT measure" heading; no links to `docs/samples/`; no citation section; no repo-structure tree. |
| CONTRIBUTING.md | **Missing.** Dev workflow only lives inline in README + `CLAUDE.md`. |
| LICENSE | Present, Apache-2.0, plus `NOTICE`. Good. |
| SECURITY.md | **Missing.** No documented vulnerability-reporting path despite real secret-handling code worth having a policy around. |
| CODE_OF_CONDUCT.md | **Missing.** |
| CITATION.cff | **Missing.** No formal citation path for a research-adjacent benchmark. |
| CHANGELOG.md | **Missing.** |
| docs/ index & coverage | 11 solid docs exist (architecture, benchmark_card, hypothesis, live_and_cost, methodology, model_sets, provider_adapters, public_claims, scoring, task_authoring) but there is no `docs/index.md` map; `docs/task_authoring.md`'s family table only lists 4 of 6 families (stale); no `docs/local_verification.md`, `docs/results_interpretation.md`, or `docs/release_checklist.md`. |
| Examples / sample results | 7 sanitized sample run directories exist under `docs/samples/` — a genuine strength, not referenced from README. |
| Issue/PR templates | None exist (nothing broken to fix, just absent). |
| `pyproject.toml` metadata | `[project.urls]` point at a placeholder `github.com/companion-bench/companion-bench` that does not match the real origin (`github.com/ErbolTakhirov/Benchmark`) — a real, fixable inaccuracy. |
| CI / local-first workflow | `.github/workflows/ci.yml` exists (61 lines, fully offline/mocked, no secrets) but **cannot run** — the GitHub account has a billing lock unrelated to this repo's code. No documented local-first replacement exists yet. |
| Project skills | 9 exist under `.claude/skills/` (add-provider, add-task-family, benchmark-quality-audit, judge-rubric-review, release-check, release-readiness-check, run-openrouter-benchmark, run-smoke-benchmark, secret-scan-artifacts) — a real strength, but `CLAUDE.md`'s own skill list only names 5 of them (stale). |

Two small, real, low-risk architecture nits (not scoring bugs, not urgent, but worth fixing before
calling this "clean"): `config/pricing.py`'s `load_pricing()` reads an explicit `--pricing` path
outside its error-handling try block (a bad path raises a raw `FileNotFoundError` instead of the
clean `ConfigError` every sibling loader produces); `utils/errors.py` defines
`BudgetExceededError`/`ResponseParseError` that are never raised anywhere in the codebase.

## Risk register

- **Scoring/methodology risks (carried forward, unchanged):** substring keyword-stuffing; no
  empathy verbosity penalty; safety blocklist misses novel phrasings; suite still synthetic,
  English-only, unreviewed by outside parties.
- **New/updated risk:** the disjointness invariant between positive signals and forbidden safety
  patterns has no automated suite-wide test — it currently depends on every task author
  remembering the rule by hand across 72 (soon many more) files.
- **Open-source risk:** a new visitor cannot currently find a contribution path, a security
  reporting path, a citation format, or a working CI signal — this is a trust/adoption blocker
  independent of benchmark quality.
- **Process risk:** GitHub Actions is billing-locked at the account level; until that is resolved
  or the repo goes local-first explicitly, any CI badge or CI-dependent claim is misleading.

## What would move this from "public-alpha instrument, MVP-scaffold project" to full public-alpha

1. Remove the non-functional Actions workflow and document local verification as the source of
   truth (this session, Phase 2).
2. Fix the two architecture nits (this session, Phase 3).
3. Grow the task suite meaningfully beyond 10/2 per family and add an automated disjointness test
   (this session, Phase 4).
4. Ship CONTRIBUTING/SECURITY/CODE_OF_CONDUCT/CITATION.cff/CHANGELOG + the missing docs/ files,
   and fix the stale figures/URLs identified above (this session, Phase 5).
5. Re-audit against the finished state (this session, Phase 6 —
   [`public_alpha_release_readiness.md`](public_alpha_release_readiness.md)).

## Audit execution log

Read-only investigation this session (three parallel Explore agents + one Plan agent) confirmed
every figure above directly against source: `find`/`grep` task counts, `Family` enum in
`schemas/task.py`, manifest glob resolution via `companion-bench list-tasks`, test thresholds in
`tests/test_task_suite.py`/`test_safety_audit.py`/`test_regression_personas.py`/
`test_manifest_validation.py`, `FAMILY_DEFAULT_WEIGHTS` in `evaluators/rule_based.py`, full file
listings under `.github/`, `docs/`, `.claude/skills/`, `git log`/`status`/`remote -v`. No files
were modified to produce this audit. Live-run evidence cited above (§4) is the existing sanitized
samples already committed at `6d97cad`/`14ceb0c`, re-read in full for this document.
