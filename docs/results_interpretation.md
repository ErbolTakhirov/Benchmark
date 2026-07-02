<!-- SPDX-License-Identifier: Apache-2.0 -->
# Reading CompanionBench results

This page is about **how to read** a `scores.json`/`summary.md` output without over-claiming what
it means. For the scoring *formula* itself, see [`scoring.md`](scoring.md) — this page doesn't
repeat it.

## What a score is

Every scored task produces six dimension scores in `[0, 1]`
(`initiative_relevance`, `timing`, `empathy`, `adaptation`, `abstention`, `safety`) plus a weighted
`total_score`. A run's `overall` is the mean of `total_score` across all scored tasks (and, with
`--repeats`, across all repeats). **`overall` is a companion-communication score scoped to the
tasks actually run — not a universal "humanity" or intelligence score.** See
[`public_claims.md`](public_claims.md) for the exact language this project holds itself to.

## The single most important caveat: mock vs. real

If the model is any `mock/*` profile — the calibrated `empathetic-v1`/`intrusive-v1`/`silent-v1`,
or the adversarial `style-liar-v1`/`permission-liar-v1`/`generic-empathy-v1`/`always-advise-v1`/
`wait-liar-v1`/`always-abstain-v1` — **the score measures the pipeline and scorer, not model
quality** — these are deterministic simulators used to validate scoring logic and produce
reproducible regression fixtures (see `tests/suite_helpers.py`, `tests/test_regression_personas.py`,
`tests/test_adversarial_mocks.py`). A perfect `empathetic-v1` score means the scorer correctly
rewards the answer-key behavior; it says nothing about any real LLM. Only scores from a real
provider (`openai/...`, `anthropic/...`, `openrouter/...`, etc.) describe actual model behavior.

## Reading confidence intervals

`score --bootstrap` reports a percentile 95% CI per dimension and for `overall`. Two models whose
CIs **don't overlap** are meaningfully different on this suite; CIs that **do overlap** should be
read as a statistical tie, not "close but still ranked."

**Cluster by task (the v1.1 default).** As of scoring v1.1 the bootstrap resamples whole **tasks**
(`--bootstrap-cluster task`), not individual `(task, repeat)` units. Repeats of one task are
pseudo-replicates — nearly identical draws of the same scenario — so resampling them as if they were
independent observations understates uncertainty and produces CIs that are too narrow (roughly
1.5–2× too tight on the existing multi-repeat samples). Clustering first collapses each task to its
across-repeat mean, then resamples tasks, which is the honest, more conservative interval. The
legacy per-unit behavior is still available with `--bootstrap-cluster unit`, but the clustered CI is
the one to report. **This means CIs computed under v1.1 are wider than — and not directly comparable
to — the CIs in the pre-1.1 sample runs under `docs/samples/`.**

Run size still matters a lot: more tasks and more repeats buy real statistical power. The provenance
block in every `summary.md` records which method, seed, and resample count produced a given CI.

## Public suite vs. held-out — what generalizes and what doesn't

If you have both a `manifests/full.yaml` run and a `manifests/heldout.yaml` run for the same
models, compare them (see
[`docs/samples/companionbench-emotomo-heldout-r5/summary.md`](samples/companionbench-emotomo-heldout-r5/summary.md)
for a worked example). In that reference run: scores correlated strongly (Pearson 0.858) and the
top and bottom of the ranking survived with non-overlapping CIs, but the exact rank order in the
statistically-tied middle did not (Spearman 0.573) — meaning **a coarse "good vs. weak" read
generalizes off the public suite; a fine-grained ranking of adjacent models does not yet**, given
the current suite size. Read any single-run ranking with that asymmetry in mind: trust large gaps,
distrust close calls.

## Behavior flags

`scores.json` includes named behavior flags (`evaluators/flags.py`) surfaced from the underlying
rubric signals — e.g. `missed_emotional_validation`, `generic_empathy`, `failed_to_abstain`,
`unparseable_output`, `mistimed_intervention`. These are diagnostic, not scored directly; a model
with a mediocre `overall` but a very specific, consistent flag profile is usually more informative
than the number alone. `unparseable_output` in particular can dominate a low score for reasons
that are about envelope/format compliance, not companion-communication quality — check parse rate
before concluding a model is "bad at companionship."

## Cost and the frontier

`companion-bench frontier` computes the cost-quality Pareto frontier across models in a run.
Cost is `null` whenever a price or token-usage figure is unknown — never invented — so a model
with `null` cost simply won't appear positioned on the frontier plot/table; that's a data gap, not
a claim that it's free.

## Scoring version and comparability

Every `scores.json` and every report's **Provenance** block records a `scoring_version` (currently
**1.1.0**) and `scorer_type`. Scores are only comparable across runs that share a scoring version.
v1.1.0 changed the semantics (parse-failure handling, safety-on-empty, self-report verification,
timing de-redundancy, and task-clustered CIs — see [`scoring.md`](scoring.md)), so its numbers are
**not directly comparable** to the pre-1.1 results in `docs/samples/` unless those are re-scored or
re-run. When in doubt, compare the `scoring_version` fields before comparing the numbers.

## Human labels and the LLM judge are calibration, not the score

CompanionBench has an optional human gold set and an opt-in LLM judge. Both are **calibration
signals reported alongside — never replacing — the rule-based scores** (`scores.json` is
untouched; judge output lives in a separate `judge_scores.json`). The judge is biased and
live-gated; the committed gold set is a **synthetic pilot fixture**, not real human data. A **real**
human round is now runnable (packet + de-identifying importer — see
[`human_gold_set.md`](human_gold_set.md)), but even a completed round is a **small pilot**:
**check inter-rater agreement first** (low agreement = the rubric is ambiguous, not the models),
and never read one round as validation. So: don't read a calibration number as a benchmark result,
don't call the benchmark "human-validated", and don't treat the judge as a leaderboard. See
[`human_gold_set.md`](human_gold_set.md) and [`judge_calibration.md`](judge_calibration.md).

## What NOT to conclude from any of this

Don't say a run "proves model X is the best" or is "the most human." Don't compare across
different runs (different task counts, seeds, model versions, **or scoring versions**) as if they
were the same experiment. Don't treat a sample run in `docs/samples/` as a leaderboard — every one of them says
so explicitly in its own README. See [`public_claims.md`](public_claims.md) for the full list of
claims this project will not make about its own numbers.
