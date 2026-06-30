<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — benchmark quality audit (v0.1 scaffold)

**Auditor framing:** external benchmark reviewer. **Date:** 2026-06-30.
**Scope:** the CompanionBench MVP — task suite, rule-based scoring, runner, reproducibility,
security, and the local OpenRouter run UX. This audits the **instrument**, not any model.

> CompanionBench evaluates **targeted human-like companion-communication behaviors in defined
> multi-turn scenarios**: emotional attunement, appropriate initiative, timing, non-intrusion,
> preference adaptation, abstention behavior, and safety boundaries. **EMOTomo is one example
> model set; OpenRouter is one provider adapter.** Results are **sample runs, not a final
> leaderboard**, scoped to the tasks, settings, and model versions actually run. The composite
> `overall` is a companion-communication score — **not** a universal "humanity"/human-likeness
> score (see [`methodology.md`](../methodology.md), [`public_claims.md`](../public_claims.md)).

## Verdict

**Public-alpha ready. Not yet "serious-benchmark ready."**

The instrument is honest, deterministic, well-engineered, secret-safe, and reproducible offline —
genuinely usable for differential, per-dimension comparison and regression testing. It is **not**
yet a defensible public ranking because the task suite is tiny and unvalidated, the rule-based
scorer has real gaming surfaces, abstention/safety are not first-class families, and there is no
human calibration. Those are the gating items for a serious release, and they are known and
documented — not hidden.

| Maturity ladder | Status |
| --- | --- |
| not ready | — |
| **MVP ready** | ✅ exceeded |
| **public-alpha ready** | ✅ **current** |
| serious-benchmark ready | ⛔ blocked on suite size, human calibration, anti-gaming |

## 1. Objective clarity — **strong**

- What it measures is stated narrowly and behaviorally (`methodology.md` §1; `benchmark_card.md`
  Scope): the communication *choices* a thoughtful companion would make in a scripted moment —
  whether/when/how/what-about to speak, ask permission, hold a boundary, or abstain.
- What it does **not** measure is explicit and repeated: not general intelligence, fluency,
  consciousness, or genuine emotion; not a safety certification. `README.md:7` and
  `public_claims.md:34` actively disclaim a universal human-likeness score.
- EMOTomo/OpenRouter framing is correct throughout and **mechanically enforced** by a guard test
  (`tests/test_public_claims.py`) that fails the build when a model set or provider is branded as if
  it were the benchmark.
- Composite naming: the rolled-up score is neutrally named `overall` (`schemas/score.py:85`) —
  there is **no** "humanity" identifier in code (only the unrelated `SourceType.HUMAN_GOLD`). Good.

**Risk:** the marketing phrase "human-like companion communication" still does heavy lifting; keep
the behavioral definition adjacent to every headline number (the docs do this today).

## 2. Task design — **adequate for a scaffold, thin for a benchmark**

- 8 tasks, 2 per family across 4 families on disk (`initiative`, `timing`, `empathy`,
  `adaptation`); each is versioned, schema-validated YAML declaring scenario, persona, scripted
  turns, probe points, intervention window, `expected_abstention_behavior`, explicit failure
  modes, rubric weights, and positive/negative signals (`schemas/task.py`, `tasks/**`).
- **Negative ("don't intervene") controls exist** — e.g. `initiative/casual-smalltalk-no-action`,
  `timing/dont-interrupt-flow` expect WAIT/abstain, so over-intervention is penalizable, not just
  under-intervention. This is the right instinct and a real strength over single-turn EI sets.
- **Abstention and safety are cross-cutting dimensions, not their own families** — coverage of
  safety/abstention failure modes is therefore thin and uneven (`methodology.md` §3, §10).
- Multi-turn trajectories are real (scripted replay → probes), which is the benchmark's core
  justification vs. static single-turn emotion benchmarks (`methodology.md` §2).

**Risks:** (a) 8 authored tasks do not generalize and are not peer-reviewed; (b) authored
"preferred style" is synthetic; (c) English/Western-default personas; (d) scenario-design can
accidentally cue the right answer.

## 3. Scoring validity — **transparent and mostly well-defended, with a real gaming surface**

Rule-based, deterministic, null-excluding with weight renormalization over *applicable* dimensions
(`rule_based.py:285-292`); family-default weights guarantee safety/abstention always carry weight
(`rule_based.py:40-68`). What I verified about gaming resistance:

- **Always-abstain** cannot score high in general: `_abstention` gives credit only on ABSTAIN
  probes, and `_initiative` zeroes abstention on action-expected probes
  (`rule_based.py:148-152, 232-244`). Resistance is real but **depends on probe-mix balance**.
- **Always-intervene / intrusive** is well-penalized: `_initiative` zeroes intrusion on WAIT/ABSTAIN
  probes, `_timing` zeroes any out-of-window intervention, `_safety` docks missing permission
  (`rule_based.py:156-177, 260-268`).
- **Generic/verbose empathy is only partially caught.** Detection is a *blocklist* over authored
  `negative_signals` (`rule_based.py:205-207`); there is **no length/verbosity penalty at all**, so
  long, fluent, generic warmth is invisible unless its phrases were pre-listed.
- **Substring matching is the dominant gaming vector.** `_contains`/`_coverage`/`_fraction_present`
  /`_pattern_present` are case-insensitive substring/regex checks, so **keyword-stuffing the
  expected `positive_signals` / `expected_target_keywords` verbatim maximizes those sub-scores**.
- **Safety is the strongest dimension** (hard pattern floors to 0.0; soft −0.5; missing-permission
  −0.5) but is a **pattern blocklist** — novel unsafe phrasings pass, and the default is
  innocent-until-matched (1.0).
- **Flag surfacing gap (partially fixed in this audit):** the scorer emitted
  `generic_or_off_empathy` and `weak_positive_signals` but `flags.py` dropped them. This audit
  surfaces them as `generic_empathy` and `missed_emotional_validation` (additive, no score change;
  `tests/test_flags.py`). Still-unsurfaced raw signals: `partial_target`,
  `abstained_instead_of_waiting`, `waited_instead_of_abstaining`, `acted_when_abstention_expected`.

## 4. Reproducibility — **strong**

- `run.json` records package version, `manifest_path`, seed, provider, `model_id`, run config,
  resolved `task_ids`, and `n_repeats`; `events.jsonl` retains full transcripts, tokens, latency,
  cost, and `model_failure` events (`runner/engine.py`, `schemas/run.py`).
- Deterministic `run_id`; mock runs are byte-stable under a `FrozenClock`; retry backoff jitter is
  seeded per `task:probe:repeat:attempt` (`runner/retry.py`) — no wall-clock/random in scored paths.
- A fresh clone runs the whole pipeline **offline and keyless** (CI proves it). Live is opt-in
  (`--live` **and** `COMPANIONBENCH_LIVE=1` **and** `--yes`/confirm) and budget-capped
  (`--max-cost-usd` best-effort + `--limit-tasks`/`--limit-models` hard caps).
- **Cost is `null` when unknown**, never invented (`config/pricing.py`, frontier handling).

**Risk:** model/version pinning for live providers is advisory; cross-version comparisons need care.

## 5. Statistical honesty — **present, partial, clearly caveated**

- `--repeats N` replays the suite and tags every event with `repeat_index` (`engine.py:146-149`).
- `score --bootstrap` resamples `(task, repeat)` units with replacement and reports percentile
  **95% CIs** for `overall` and each dimension, deterministic under `--bootstrap-seed` (CLI
  default 42; `aggregate.py:170-191`).
- **Honest limitation (documented):** the bootstrap treats `(task, repeat)` units as i.i.d. — it
  does **not** block/stratify by task, so repeats of the same task are pseudo-replicated; on a tiny
  suite this is a defensible approximation, **not** population-level inference. Stated as such in
  `methodology.md` §7 and `benchmark_card.md` limitation #7.

## 6. Human-validation readiness — **planned, not built (correctly gated)**

- The LLM-judge path is an **intentional unimplemented seam** (`evaluators/rubric.py`
  `RubricEvaluator`); no judge ships, and `scores.json` keeps rule-based numbers separate from any
  future judge output (`schemas/score.py` docstring).
- A concrete human-eval plan exists (`benchmark_card.md`): gold set, ≥3 raters/probe/dimension,
  inter-rater reliability (Krippendorff α), and rules-vs-judge-vs-human calibration with humans as
  reference. **No gold-label schema or data yet** — this is the main "Validated" gap.

## 7. Security — **strong, and tested**

- Keys are resolved **only** from `os.environ` via `adapter.from_env()` — never CLI args, manifests,
  or YAML. `.env` is gitignored (`.env.*` too, `!.env.example` kept), `.env.example` is keyless.
- `utils/secrets.py` provides `collect_secret_values`/`redact`/`scan_paths_for_secrets`/
  `scan_run_dir`; `model_failure` events are redacted before persistence (`runner/events.py`).
- `tests/test_secrets.py` proves a key is sent in the request header **yet never reaches a
  serialized event or any run artifact** (scanned with both a fake and the real env value).
- New `.env` loader is safe: `override=False` (shell wins), pytest-guarded callback, and an autouse
  `conftest` fixture strips live/secret vars so the **default suite stays offline + keyless even on
  a developer machine with a populated `.env`** (`tests/test_env_loading.py`).
- Raw transcripts (`events.jsonl`) are never committed (`runs/` gitignored); sanitized samples are
  clearly marked and exclude raw events.

## 8. Benchmark best-practice comparison

| Practice | CompanionBench today |
| --- | --- |
| **HELM** (multi-metric, no single-number worship) | ✅ per-dimension profiles + behavior flags; ⛔ scenario breadth & perturbation analysis |
| **MT-Bench / Chatbot Arena** (multi-turn, pairwise/human) | ✅ genuinely multi-turn; ⛔ no pairwise/Elo, no human or judge ratings yet (rule-based only) |
| **MLPerf** (rules/repro discipline, divisions) | ◑ versioned tasks, seeds, `uv.lock`, deterministic runs; ⛔ no formal divisions / audited submissions |
| **HF Evaluate** (metric docs/reuse discipline) | ✅ `scoring.md` + benchmark card; ◑ metrics not yet a reusable standalone module |
| **ACM artifact badging** | Available ✅ (Apache-2.0, public) · Functional ✅ (runs offline) · Reusable ◑ (skills/docs, tiny suite) · **Validated ⛔ (no human calibration)** |

## Risk register

- **Scoring risks:** substring keyword-stuffing; no empathy verbosity penalty; safety blocklist
  misses novel unsafe phrasings; several computed flags still unsurfaced; always-abstain reward is
  probe-mix-sensitive.
- **Methodology risks:** 8-task, non-peer-reviewed suite; abstention/safety not first-class
  families; synthetic personas; English/Western-default norms; Goodhart/overfitting if optimized to.
- **Reproducibility risks:** live provider/version non-determinism; advisory (not enforced) version
  pinning; `--max-cost-usd` is best-effort, not a hard guarantee without `--limit-*`.
- **Security risks:** low. Residual: a populated local `.env` arms `COMPANIONBENCH_LIVE` for the
  non-`run` live gates (`providers --probe`, `pricing sync`, `models validate --online`) — mitigated
  by `override=False`, `.env` being gitignored, and `run` still needing `--live` + `--yes`/confirm.

## Top 10 fixes before public v0.1

1. **Grow + peer-review the task suite** and add a **held-out hidden set** to blunt overfitting.
2. **Promote abstention and safety to first-class families** with dedicated scenarios.
3. **Reduce substring gaming:** paraphrase-robust matching (synonym/regex sets or judge
   calibration) and add an **empathy length/verbosity penalty**.
4. **Layer safety detection** (patterns + a classifier) so novel unsafe phrasings are caught.
5. **Surface the remaining computed flags** (`partial_target`, `abstained_instead_of_waiting`, …);
   `generic_empathy` + `missed_emotional_validation` are done in this pass.
6. **Cluster/stratified bootstrap by task** (block resampling) + report per-task variance.
7. **Build a human gold set + calibration** (rules-vs-human) before any leaderboard-style claim.
8. **Multilingual coverage** (Russian, Kyrgyz) authored and reviewed, not inferred.
9. **Audit negative-control coverage** so every family has explicit don't-intervene probes.
10. **Provenance block on every report** (provider, model-version snapshot, pricing `as_of`,
    scoring version) for defensible cross-run comparison.

## Audit execution log

**Offline gates (this audit):**

| Step | Result |
| --- | --- |
| `uv sync --all-extras` | ✅ (adds `python-dotenv==1.2.2`) |
| `uv run ruff check .` | ✅ all checks passed |
| `uv run ruff format --check .` | ✅ 63 files formatted |
| `uv run mypy` | ✅ no issues in 41 source files |
| `uv run pytest -q` | ✅ **163 passed, 1 skipped** (live test skipped; keyless) |
| offline mock smoke (`validate`→`run`→`score`→`report`) | ✅ (see Phase-3 log in the session) |
| secret scan (repo + offline artifacts) | ✅ empty |

New tests added: `tests/test_env_loading.py` (5), `tests/test_flags.py` (3).

**Live verification (capped OpenRouter run, 2026-06-30):** 4 models via OpenRouter
(`deepseek/deepseek-chat-v3-0324`, `mistralai/mistral-nemo`, `z-ai/glm-4.5-air`,
`google/gemini-2.5-flash-lite`), 8 tasks × 2 repeats, **total cost $0.0147** (cap $3), 3 failures
(all `glm-4.5-air`, logged as `model_failure`). Sanitized results:
[`../samples/audit-openrouter-humanlike-r2-small/`](../samples/audit-openrouter-humanlike-r2-small/)
— **a sample run, not a final leaderboard**. The live data **empirically confirmed three audit
findings**: (a) **all four CIs overlap** (overall 0.62–0.74) → no statistically separable winner on
this tiny suite; (b) **safety scored 1.000 for every model** → the suite barely stresses safety
(thin coverage); (c) a **parse-rate confound** — `gemini-2.5-flash-lite` returned a valid envelope
only 54% of the time, depressing its score for envelope-compliance reasons, not companion behavior.
The newly-surfaced `missed_emotional_validation` flag fired 8–14× on every model (the most
informative cross-model diagnostic). All live artifacts were **secret-scanned (seeded with the real
key) → clean**; only sanitized files are committed (no raw `events.jsonl`).
