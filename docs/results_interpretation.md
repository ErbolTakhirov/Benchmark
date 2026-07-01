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

If the model is `mock/empathetic-v1`, `mock/intrusive-v1`, or `mock/silent-v1`, **the score
measures the pipeline, not model quality** — these are deterministic simulators used to validate
scoring logic and produce reproducible regression fixtures (see `tests/suite_helpers.py`,
`tests/test_regression_personas.py`). A perfect `empathetic-v1` score means the scorer correctly
rewards the answer-key behavior; it says nothing about any real LLM. Only scores from a real
provider (`openai/...`, `anthropic/...`, `openrouter/...`, etc.) describe actual model behavior.

## Reading confidence intervals

`score --bootstrap` reports a percentile 95% CI per dimension and for `overall`, resampling
`(task, repeat)` units with replacement. Two models whose CIs **don't overlap** are meaningfully
different on this suite; CIs that **do overlap** should be read as a statistical tie, not "close
but still ranked." The bootstrap treats `(task, repeat)` units as i.i.d. without task-level
blocking — a defensible approximation on a still-modest suite, not population-level inference. Run
size matters a lot here: the existing samples in `docs/samples/` show CIs tightening from ~±0.13 on
an 8-task run to ~±0.025 on the 60-task, 5-repeat full-suite run — more tasks and more repeats
buy real statistical power, not just a longer runtime.

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

## What NOT to conclude from any of this

Don't say a run "proves model X is the best" or is "the most human." Don't compare across
different runs (different task counts, seeds, or model versions) as if they were the same
experiment. Don't treat a sample run in `docs/samples/` as a leaderboard — every one of them says
so explicitly in its own README. See [`public_claims.md`](public_claims.md) for the full list of
claims this project will not make about its own numbers.
