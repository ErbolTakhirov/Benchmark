<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — scoped reporting policy

How to describe CompanionBench results in the README, docs, samples, papers, issues, and any public
communication. The principle is simple: **say exactly what was measured, and attribute it precisely.**
Precise, scoped language is part of the methodology — it keeps an honest benchmark honest.

A companion guard test (`tests/test_public_claims.py`) enforces the naming and scope rules
mechanically; this document is the human-readable policy behind it.

## Project framing

CompanionBench is a **benchmark**: a versioned suite of authored, multi-turn tasks plus a
transparent, rule-based scorer. A run's **model set** (which models were compared) and **provider**
(which API served them) are **run metadata** — inputs to a run, recorded alongside the results, not
the identity of the benchmark. So EMOTomo is one example model set and OpenRouter is one provider
adapter; a run using them is *"a CompanionBench evaluation using the EMOTomo model set via
OpenRouter."*

## Scoped reporting policy — the one rule

> Report **targeted behaviors under defined scenarios**, attributed to a specific **model set** and
> **provider**, as a **scoped run** — with its tasks, settings, model versions, and scorer design.

## Allowed claims (precise and scoped)

Each of these is bounded by what the run actually measured:

- "CompanionBench evaluates targeted companion-communication behaviors under defined tasks."
- "This scoped run compares **these models** under **these tasks** and **these settings**."
- "Under the EMOTomo model set via OpenRouter, model A scored higher than model B on adaptation in
  this scoped run."
- "Scores describe behavior on authored scenarios, scoped to this task suite and scorer design."
- "The EMOTomo model set is one example model set; OpenRouter is one provider adapter — both recorded
  as run metadata."
- "This is a scoped benchmark run; report it with its tasks, settings, and model versions."
- "With 95% bootstrap CIs over N repeats, the difference was / was not statistically distinguishable."
- "On the small synthetic pilot, the rule scorer agreed with the human consensus at rate X per
  dimension." (A workflow/calibration result on a fixture.)
- "The LLM judge (model M, prompt version V) is an opt-in calibration signal reported alongside the
  rule-based scores." (Alongside, never in place of them.)

## Claims requiring more evidence

Reserve these until the supporting evidence exists — and describe the evidence when it does:

- **External / human validation.** Human labels *calibrate* the scorer; a completed round is
  reported as a calibration result with inter-rater agreement, not as validation of the task design.
  The committed gold set today is a synthetic pilot fixture (a workflow proof).
- **LLM-judge conclusions.** The judge is an opt-in, biased calibration signal; report it next to the
  rule-based baseline with its model + prompt version, never as the source of truth.
- **Cross-model rankings.** Report score differences with their bootstrap CIs; call two scores a
  "win" only when they are statistically distinguishable, and keep the ranking scoped to the run.

## Good wording (use these shapes)

| Instead of… | Write… |
| --- | --- |
| "the EMOTomo benchmark" | "a CompanionBench evaluation using the EMOTomo model set" |
| "the OpenRouter benchmark" | "a CompanionBench run served via the OpenRouter provider" |
| "the benchmark proves X" | "this scoped run shows X, within the stated limitations" |
| "the most human-like model" | "higher on these companion-communication tasks in this run" |
| "human-validated" | "human validation is a future milestone; current labels are calibration signals" |
| "the final leaderboard" | "a scoped benchmark run, not a universal ranking" |

## Overclaims to avoid

Keep these out of public communication — the repository does not support them:

- ❌ "Model X is the most human-like model overall." (No universal human-likeness is measured.)
- ❌ "This proves model X is the best companion." (A scoped run, not proof.)
- ❌ "CompanionBench is the first / definitive / final benchmark for companions." (Unproven.)
- ❌ "Model X is safe for vulnerable users." (A score is not a safety certification.)
- ❌ "Model X is emotionally intelligent" as a global trait. (Behavior on scenarios only.)
- ❌ "CompanionBench is human-validated / human-approved." (Current gold labels are a synthetic pilot
  fixture; human validation is a future milestone.)
- ❌ "The LLM judge shows model X is best." (The judge is a biased calibration signal, not a
  leaderboard, and never the source of truth.)

## Required hedges for any result

Whenever you publish numbers, keep these nearby:

1. **Scope:** which model set, which provider, which manifest/tasks, how many repeats.
2. **Scoped run:** the task suite is small and illustrative (see
   [methodology limitations](methodology.md#10-limitations)).
3. **Uncertainty:** report bootstrap 95% CIs; treat indistinguishable scores as a tie.
4. **Scoring basis:** rule-based and deterministic — a transparent baseline, reported as such.
5. **Cost honesty:** cost is `null` when unknown, never invented.

## Why this matters

CompanionBench exists to make companion-communication failure modes measurable. That value holds
when results are reported precisely: a small, authored, rule-scored **scoped run** is described with
its tasks, settings, and model versions, and its model set / provider are recorded as metadata.
Holding the line on precise language is part of the methodology. See the
[benchmark card](benchmark_card.md) and [methodology](methodology.md).
