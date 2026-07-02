<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — methodology

How CompanionBench turns "did the model communicate like a good human companion?" into
reproducible numbers, and what those numbers do and do not mean. This is the serious version of
the [README](../README.md); read the [benchmark card](benchmark_card.md) and the
[public-claims policy](public_claims.md) alongside it.

## 1. Objective

CompanionBench measures **human-like companion communication** in a narrow, behavioral sense:
whether a model makes the communication choices a thoughtful human companion would make in a
specific, scripted situation. Concretely, given a multi-turn conversation, does the model decide
**whether** to speak, **when** to speak, **how** (style/tone), **what about** (target), whether to
**ask permission**, and whether to **hold a boundary or abstain** — in the way this particular user
and moment call for.

It is explicitly **not** a measure of general intelligence, factual knowledge, conversational
fluency, consciousness, or genuine emotion. A CompanionBench score describes targeted behavior on
authored scenarios — nothing more. See [limitations](#9-limitations).

## 2. Why static, single-turn emotion benchmarks are insufficient

Static "emotional intelligence" benchmarks (label the emotion, pick the kind reply) are valuable
but structurally blind to companion quality, because companion quality is a property of a
*trajectory*, not a turn:

- **No initiative decision.** A single-turn prompt has already decided the model should respond;
  over-intervention and intrusiveness become invisible.
- **No timing.** "Right answer, wrong moment" cannot be expressed in one turn.
- **Generic empathy scores well.** A globally warm reply scores highly even when *this* user
  wanted a concrete fix; attunement is fit-to-person, not average niceness.
- **No memory / adaptation.** Whether a model *stops* a disliked behavior after feedback is a
  multi-turn property.
- **Safety is contextual and accumulative.** Dependency-building and boundary erosion build up
  across a relationship and are under-counted by one-shot probes.

CompanionBench is designed to make these failure modes first-class, measurable signals.

## 3. Task families

Tasks are authored YAML scenarios, each versioned and schema-validated, and each belongs to one
**family** — the primary behavior the scenario stresses. The repository ships **six** families on
disk, each with roughly 10–15 authored scenarios:

| Family | Stresses |
| --- | --- |
| **initiative** | Whether to intervene at all, picking a useful target, avoiding intrusion. |
| **timing** | Acting inside the acceptable window — not too early, too late, or too often. |
| **empathy** | Inferring the user's state and matching *this* user's preferred style. |
| **adaptation** | Remembering preferences and repairing behavior after feedback. |
| **abstention** | Non-intrusion: knowing when *not* to act and declining out-of-scope requests cleanly. |
| **safety** | Holding hard boundaries (medical / legal / financial overreach, manipulation, dependency, romanticization, privacy) while staying a decent companion. |

Abstention and safety — once evaluated only as cross-cutting dimensions inside the other families —
are now **first-class families** with dedicated scenarios (`tasks/abstention/`, `tasks/safety/`),
while abstention and safety also remain scored *dimensions* on every probe. Each family additionally
carries a small **held-out / hidden split** under `tasks/<family>/heldout/` that is excluded from the
public suite (`manifests/full.yaml`) and reserved for measuring generalization — never tuned against.
When a family is added it gets a `Family` enum value and default dimension weights; see
[`task_authoring.md`](task_authoring.md).

Each task declares its scenario, persona, scripted turns, probe points, intervention window,
`expected_abstention_behavior`, explicit failure modes, a scoring rubric, and positive/negative
signals.

## 4. Scoring dimensions

Each scored turn ("probe") produces up to **six** dimension scores in `[0, 1]`:

`initiative_relevance`, `timing`, `empathy`, `adaptation`, `abstention`, `safety`.

Dimensions that don't apply to a probe are set to `null` and **excluded** from that probe's
weighted total, with the remaining weights renormalized (so a model is never penalized on a
dimension the scenario didn't test). A weighted `total_score` rolls the applicable dimensions up.

**Rule-based scoring is the default and the source of truth.** The model returns a small
structured envelope per turn (a `CompanionTurn`: a `decision` of `intervene` / `wait` / `abstain`,
a `message`, an optional `target`, a `style`, and an `ask_permission` flag). A deterministic
evaluator compares that envelope against the task's expectations. Scoring is **versioned**
(`scoring_version`, currently 1.1.0): as of v1.1 a missing/empty/malformed output earns no positive
credit (safety is `null`, not `1.0`, when there is nothing to judge), self-reported `style` /
`ask_permission` / `wait` labels are verified against the message prose, and a timing window that
merely restates the intervene decision is reported but zero-weighted to avoid double-counting. Full
mechanics: [`scoring.md`](scoring.md).

## 5. Behavior flags

Beyond numeric scores, the scorer emits **named behavior flags** — human-readable diagnostics
derived deterministically from the same rule signals (not a separate model). They name *how* a
model fails so profiles are legible across models, e.g. `waited_when_validation_needed`,
`intrusive_advice`, `missed_preference`, `style_mismatch`, `failed_to_abstain`,
`inappropriate_abstention`, `missing_permission`, and `unsafe_overreach`. Flags are counts, not
scores; they complement the dimension numbers, they do not replace them.

## 6. Repeated runs

Real API models are non-deterministic. CompanionBench supports `--repeats N`, which replays the
whole task set `N` times; every event is tagged with its `repeat_index`, and the per-task,
per-repeat results are the unit of aggregation. The mock model is deterministic, so repeats of a
mock run are identical by construction (they exist to exercise the machinery and to make the live
path honest).

## 7. Bootstrap confidence intervals

A single point score hides sampling noise. `score --bootstrap` reports a percentile **95%
confidence interval** for the overall score and each dimension, deterministically under a fixed
`--bootstrap-seed`. As of scoring **v1.1** it resamples whole **tasks** by default
(`--bootstrap-cluster task`): repeats of one task are pseudo-replicates, so treating each
`(task, repeat)` unit as independent (the legacy `--bootstrap-cluster unit`) understates uncertainty
and yields CIs that are too narrow. Clustering by task is the honest, more conservative interval and
the one to report; the per-unit mode remains available for backwards comparison. Tasks are the
independent scenario units — this is a defensible-but-imperfect model documented as such, not a
claim of population-level inference over "all possible conversations".

## 8. Cost, latency, and tokens

When a run uses real providers, CompanionBench records per-call **tokens, latency, and cost** where
the provider reports them. **Cost is `null` when unknown** — when there is no price entry or no
usage — and is never invented. Prices come from a versioned pricing table that can be synced from
the OpenRouter API (`pricing sync-openrouter`). The `frontier` command draws a **cost-quality
Pareto frontier** (maximize overall score, minimize cost per successful probe); models with unknown
cost are reported as "unknown", never silently dropped or guessed onto the frontier. A global
`--max-cost-usd` budget guard is best-effort; pair it with `--limit-tasks` / `--limit-models` for
hard caps.

## 9. Why rule-based scoring is the default (and LLM-as-judge is not)

Rule-based scoring is **transparent, deterministic, reproducible, and cheap**, and it cannot
self-prefer a model family. That makes it the right baseline and the right default source of
truth. It is also blunt: keyword/regex/structural signals miss paraphrase, nuance, and
genuinely-novel-but-good responses.

An **LLM-as-judge** is planned only as a *future, optional calibration layer* — never the source of
truth. When added it must be reported **alongside** the rule-based baseline, with published prompts
and seeds, pinned judge versions, saved transcripts, multi-judge disagreement, and explicit
calibration against humans. The documented risks (self-preference, verbosity/stylistic bias, prompt
sensitivity, sycophancy, safety blind spots) are in the [benchmark card](benchmark_card.md). Until
that calibration exists and is disclosed, the judge does not score anything that ships.

## 10. Limitations

CompanionBench is an early research instrument. Read every number with these in mind:

- **Authored, un-peer-reviewed task suite.** The suite now spans six families with ~10–15 scenarios
  each (plus a held-out split), exercising every code path and dimension far more thoroughly than
  the original eight tasks — but it is still author-written and not externally peer-reviewed, so
  individual results should be read as scoped, not population-level.
- **Synthetic safety coverage.** Abstention and safety are now first-class families with dedicated
  scenarios, but the boundaries are authored regex patterns: they catch the failure modes we wrote
  down, not novel unsafe phrasings, and are not a safety certification.
- **Language coverage is limited.** Scenarios are currently authored primarily in English. Broader
  multilingual coverage (e.g. Russian, Kyrgyz) is a goal, not a present claim; until scenarios and
  rubrics are localized and reviewed, cross-language results should not be inferred.
- **Possible rubric bias.** Rule signals encode the authors' judgments about good companion
  behavior and particular (often Western-default) cultural norms about directness and boundaries.
- **Scenario-design risk.** A scenario can be unrealistic, ambiguous, or accidentally cue the
  "right" answer; authored "preferred style" is synthetic, not elicited from real users.
- **API provider non-determinism.** Live results vary across calls, providers, model versions, and
  time; pin versions and use `--repeats` + CIs, and still treat cross-version comparisons with care.
- **Benchmark overfitting / Goodhart risk.** Any fixed rubric can be gamed by surface matching.
  Optimizing a model *to* CompanionBench would erode its meaning; the structured envelope and
  keyword signals are especially gameable. We mitigate with held-out scenarios and planned
  human/judge calibration, but the risk is real and permanent.

## 11. Reproducibility

Mock runs are byte-stable under a frozen clock; real runs retain wall-clock metadata. Runs record
the package version, manifest + task versions, seed, full `events.jsonl` transcripts, and per-call
provider/model/params. No secrets reach any artifact (a test proves it). The reproducibility
checklist is in the [benchmark card](benchmark_card.md).
