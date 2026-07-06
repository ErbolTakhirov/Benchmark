<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — benchmark card

A short, honest description of what this benchmark is for, what it is **not** for, and how to
read its numbers responsibly. Modeled on dataset/model cards. For a one-command snapshot of the
current external-validation state, run `companion-bench quality status`; for the full self-assessed
quality roadmap see [`audits/benchmark_quality_scorecard.md`](audits/benchmark_quality_scorecard.md).

- **Name:** CompanionBench
- **Version:** 0.1.0-alpha (public alpha — not a mature, fully-validated benchmark)
- **License:** Apache-2.0
- **Scope:** Multi-turn evaluation of **human-like companion communication** in LLMs / proactive
  assistants across initiative, timing, emotional attunement, preference adaptation, abstention,
  and safety. "Human-like" is meant behaviorally (the communication choices a thoughtful human
  companion would make on a scenario), not as a claim about general intelligence or genuine emotion.
- **Vendor/provider-neutral:** the benchmark is the tasks + scoring. *Which* models are compared is
  a **model set**; the API used is a **provider**. See [`model_sets.md`](model_sets.md),
  [`methodology.md`](methodology.md), and the [`public-claims policy`](public_claims.md).

## Intended use

- **Research instrument** for studying multi-turn companion/proactive-assistant behavior, and
  for testing the [research hypothesis](hypothesis.md).
- **Differential, multi-dimensional comparison** of API-served models — reading *per-dimension
  profiles* (a model can be empathetic yet badly timed), not just a single leaderboard number.
- **Regression testing** of a companion system across versions on a fixed task suite.
- **A reproducible baseline** (rule-based scoring) against which future LLM-judge and human
  evaluations are calibrated.

## Not intended use

- **Not** a safety certification, clinical/therapeutic validation, or fitness-for-deployment
  signal. A high score does not make a system safe for vulnerable users.
- **Not** a single "companion IQ" ranking. The dimensions are partly independent by design;
  collapsing them hides the trade-offs that matter.
- **Attributed to model set + provider as metadata.** A result is *"a CompanionBench evaluation
  using the EMOTomo model set via OpenRouter"* — EMOTomo is one example model set, OpenRouter one
  provider adapter, each recorded as run metadata. See the [scoped-reporting policy](public_claims.md).
- **Scoped to the evaluated scenarios.** Scores describe targeted behaviors on authored scenarios for
  the model set and settings actually run — a scoped result on this task suite.
- **Not** defined by its default model: the offline default is a deterministic **mock simulator**,
  and mock scores validate the **pipeline**, not model quality. Live provider runs *have* been
  performed (see [`results_v0_1_alpha.md`](results_v0_1_alpha.md)) and are reported as scoped runs
  for a specific model set / provider / settings.
- **Not** a substitute for human judgment about emotionally loaded interactions.
- **Not** a source of medical, legal, financial, or mental-health guidance.

## Known limitations

1. **Human validation is a future milestone.** The committed gold labels are a **synthetic** pilot
   fixture (`data/gold/`, `not_human_collected`); a real annotation round has not been run yet, so
   results are reported as scoped runs with calibration signals. The offline default model is also a
   deterministic simulator (mock scores validate the pipeline, not model quality); live runs exist
   and are reported as scoped snapshots. Run `companion-bench quality status` for the current state.
2. **Rule-based scoring is blunt.** Keyword/regex signals and structural checks cannot
   capture nuance, sarcasm, paraphrase, or genuinely novel-but-good responses. They can be
   gamed by surface matching and can both false-positive and false-negative. Scoring **v1.1–v1.2.0**
   hardened several known gaming vectors — parse/empty outputs no longer earn free safety credit,
   self-reported `style`/`ask_permission`/`wait` labels are verified against the prose, and a
   redundant timing window is no longer double-counted (see [`scoring.md`](scoring.md)) — but the
   scorer remains rule-based (v1.2.0 also makes keyword matching whole-token rather than substring), and paraphrase limits stand until a calibrated judge and a
   human gold set exist.
3. **Authored, un-peer-reviewed task suite.** The suite spans **six families** (initiative, empathy,
   timing, adaptation, abstention, safety) with **25 public scenarios each** (150 total), plus a
   **6-per-family held-out hidden split** (36 total; `tasks/<family>/heldout/`, run via
   `manifests/heldout.yaml`) reserved for generalization. It exercises every code path and dimension,
   but is author-written and not yet externally peer-reviewed — read individual results as scoped,
   not population-level. `validate --strict-quality` enforces suite invariants at authoring time.
4. **Structured-envelope assumption.** The MVP asks models for a `CompanionTurn` JSON. A model
   that is excellent in free-form prose but poor at the envelope is under-credited until the
   free-text + judge path lands.
5. **English / Western-default personas.** The current scenarios are authored primarily in English
   and encode particular cultural norms about initiative, directness, and boundaries. Broader
   multilingual coverage (e.g. Russian, Kyrgyz) is a goal, not a present claim.
6. **Synthetic personas.** "Preferred style" is authored, not elicited from real users.
7. **Statistics are present but partial.** Repeated runs (`--repeats`) and bootstrap 95% CIs
   (`score --bootstrap`) are supported and reported, but the resampling model (over `(task,
   repeat)` units on a small suite) is a defensible approximation, not population-level inference;
   inter-task correlation analysis is not yet reported.
8. **Goodhart / overfitting risk.** Any fixed rubric can be gamed by surface matching; optimizing a
   model *to* CompanionBench would erode its meaning.

## Risks of LLM-as-judge

The LLM judge is **opt-in and auxiliary**: it is implemented behind the `RubricEvaluator` interface
(offline mock + live-gated real), stored separately (`judge_scores.json`), and is **never the source
of truth** — the rule-based score is. It has **not** been calibrated against real humans yet, so
judge numbers are not reported as results. Whenever the judge is used, these risks must be measured
and disclosed:

- **Self-preference / family bias.** Judges tend to prefer outputs from their own model family
  or stylistic distribution, inflating related models.
- **Stylistic bias over substance.** Judges reward fluent, confident, "nice-sounding" text —
  exactly the *generic empathy* failure CompanionBench is built to penalize.
- **Prompt sensitivity & instability.** Verdicts shift with rubric wording, option order,
  and temperature; small prompt edits can reorder models.
- **Non-determinism.** Without fixed seeds and pinned model versions, scores are not
  reproducible across time.
- **Sycophancy & leniency drift.** Judges over-pass borderline cases, compressing the score
  range.
- **Safety blind spots.** A judge may rate a manipulative-but-warm response highly.

Mitigations we require before reporting judge numbers: published prompts and seeds, pinned
judge model versions, judge transcripts saved as artifacts, panels of multiple judges with
disagreement reported, and calibration against humans (below). Judge numbers are always
reported **alongside** the rule-based baseline, never replacing it.

## Human evaluation plan

The **workflow** for this plan is implemented (schema, agreement metrics, calibration commands, an
opt-in judge, a distributable annotation packet, and a privacy-safe de-identification importer) —
see [`human_gold_set.md`](human_gold_set.md) and [`judge_calibration.md`](judge_calibration.md). The
committed pilot labels are still **synthetic test fixtures** (`data/gold/`, marked
`not_human_collected`); a **real** round is now *runnable* (packet at
`analysis/annotation_round_v0_1/`, `companion-bench gold import-human`) but not yet done. Expert
review (step 4) remains future work; steps 2–3 run today on any gold file.

1. **Gold set.** Sample probes across families/difficulties; collect ≥3 independent human
   ratings per probe per dimension with a written rubric. *(Packet + de-identifying importer
   shipped; real collection not yet run.)*
2. **Agreement.** Report inter-rater reliability (percent, Cohen's κ, Krippendorff's α) per
   dimension; revise rubrics where humans disagree. *(Shipped: `companion-bench gold agreement`.)*
3. **Calibration.** Measure rule-vs-human and judge-vs-human agreement per dimension. Treat
   humans as the reference; report where rules/judges systematically diverge. *(Shipped:
   `companion-bench calibrate rules|judge`.)*
4. **Vulnerable-context review.** Have domain experts (mental-health, safety) review the
   safety/abstention tasks specifically. *(TODO.)*
5. **Cadence.** Re-validate when tasks, the envelope, the scorer, or the judge change.

## Reproducibility checklist

- [ ] Pinned deps via `uv.lock`; record `companion-bench` version (in `run.json`).
- [ ] Record the manifest + task versions used (the run resolves and stores `task_ids`).
- [ ] Fixed `seed`; deterministic `run_id` derived from manifest+model+seed.
- [ ] Raw `events.jsonl` retained (full transcripts, tokens, latency, cost, failures).
- [ ] Provider, model id, and model params recorded for every call.
- [ ] Mock runs are byte-stable under a frozen clock; real runs retain wall-clock metadata.
- [ ] Scoring is rule-based and versioned with the code; `scores.json` + `summary.md` kept.
- [ ] For judge runs (future): judge model+version, prompts, seeds, and transcripts retained.
- [ ] No secrets in any artifact or commit.

## Maintenance & feedback

CompanionBench is an early, evolving research artifact. Tasks, dimensions, and scoring will
change; treat cross-version comparisons with care and pin versions. Issues and task
contributions are welcome via the repository.
