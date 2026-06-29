# CompanionBench — benchmark card

A short, honest description of what this benchmark is for, what it is **not** for, and how to
read its numbers responsibly. Modeled on dataset/model cards.

- **Name:** CompanionBench
- **Version:** 0.1 (MVP scaffold)
- **License:** Apache-2.0
- **Scope:** Multi-turn evaluation of LLM companions / proactive assistants across initiative,
  timing, emotional attunement, preference adaptation, abstention, and safety.

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
- **Not** a benchmark of real models *in its MVP form*: the default model is a deterministic
  **mock simulator**, and mock scores validate the **pipeline**, not model quality.
- **Not** a substitute for human judgment about emotionally loaded interactions.
- **Not** a source of medical, legal, financial, or mental-health guidance.

## Known limitations

1. **Mock-first MVP.** The shipped numbers come from a simulator. Real-model comparison
   requires running the API adapters (which need keys) and, ideally, the judge/human path.
2. **Rule-based scoring is blunt.** Keyword/regex signals and structural checks cannot
   capture nuance, sarcasm, paraphrase, or genuinely novel-but-good responses. They can be
   gamed by surface matching and can both false-positive and false-negative.
3. **Small, illustrative task suite.** 8 tasks (2 per family) exercise every code path but are
   not representative or peer-reviewed. Results do not generalize.
4. **Structured-envelope assumption.** The MVP asks models for a `CompanionTurn` JSON. A model
   that is excellent in free-form prose but poor at the envelope is under-credited until the
   free-text + judge path lands.
5. **English / Western-default personas.** The current scenarios encode particular cultural
   norms about initiative, directness, and boundaries.
6. **Synthetic personas.** "Preferred style" is authored, not elicited from real users.
7. **No statistical treatment yet.** No confidence intervals, multiple-seed variance, or
   inter-task correlation analysis are reported in the MVP.

## Risks of LLM-as-judge

We deliberately **do not** ship an LLM judge in the MVP. When one is added (behind the
`RubricEvaluator` interface), these risks must be measured and disclosed:

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

1. **Gold set.** Sample probes across families/difficulties; collect ≥3 independent human
   ratings per probe per dimension with a written rubric.
2. **Agreement.** Report inter-rater reliability (e.g. Krippendorff's α) per dimension; revise
   rubrics where humans disagree.
3. **Calibration.** Measure rule-vs-human and judge-vs-human agreement per dimension. Treat
   humans as the reference; report where rules/judges systematically diverge.
4. **Vulnerable-context review.** Have domain experts (mental-health, safety) review the
   safety/abstention tasks specifically.
5. **Cadence.** Re-validate when tasks, the envelope, or the judge change.

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
