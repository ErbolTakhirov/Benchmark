<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — public-claims policy

This is a strict policy for how CompanionBench results may be described in the README, docs,
samples, papers, issues, and any public communication. The goal is simple: **say exactly what was
measured, and nothing more.** Overclaiming is the fastest way to make an honest benchmark
dishonest.

A companion guard test (`tests/test_public_claims.py`) enforces the most important naming rules
mechanically; this document is the human-readable contract behind it.

## The one rule

> Report **targeted behaviors under defined scenarios**, attributed to a specific **model set** and
> **provider**, as a **sample/run** — never as a universal verdict.

## Allowed (precise) claims

These are fine because each is bounded by what the run actually measured:

- "CompanionBench evaluates targeted companion-communication behaviors."
- "This run compares **these models** under **these tasks** and **these settings**."
- "Under the EMOTomo model set via OpenRouter, model A scored higher than model B on adaptation in
  this sample run."
- "Scores are not universal intelligence scores; they describe behavior on authored scenarios."
- "The EMOTomo model set is an example model set; OpenRouter is one provider adapter."
- "This is a sample run, not a final leaderboard."
- "With 95% bootstrap CIs over N repeats, the difference was / was not statistically distinguishable."
- "On the small synthetic pilot, the rule scorer agreed with the human consensus at rate X per
  dimension." (Calibration on a fixture — a workflow proof, not validation.)
- "The LLM judge (model M, prompt version V) is a biased, opt-in signal reported alongside the
  rule-based scores." (Never in place of them.)

## Not allowed (overclaims)

Do not write these, because the repository does not support them:

- ❌ "Model X is the most human-like model overall." (No universal human-likeness is measured.)
- ❌ "This proves model X is the best companion / best for all companions." (Sample, not proof.)
- ❌ "The **EMOTomo benchmark** shows…" (There is no EMOTomo benchmark; EMOTomo is a model set.)
- ❌ "The **OpenRouter benchmark** shows…" (There is no OpenRouter benchmark; it is a provider.)
- ❌ "CompanionBench is the first / definitive / final benchmark for companions." (Unproven.)
- ❌ "Model X is safe for vulnerable users." (A score is not a safety certification.)
- ❌ "Model X is emotionally intelligent / empathic" as a global trait. (Behavior on scenarios only.)
- ❌ "CompanionBench is human-validated / human-approved." (The shipped gold set is a *synthetic
  pilot fixture*; no real human study has been run.)
- ❌ "The LLM judge shows model X is best." (The judge is a biased calibration signal, not a
  leaderboard, and never the source of truth.)
- ❌ "Human ratings prove the benchmark is correct." (Human labels *calibrate*; they do not
  validate the task design or make a small pilot definitive.)

## Naming: model set and provider are not the benchmark

| Instead of… | Write… |
| --- | --- |
| "EMOTomo benchmark" | "CompanionBench evaluation using the EMOTomo model set" |
| "OpenRouter benchmark" | "CompanionBench run via the OpenRouter provider" |
| "EMOTomo/OpenRouter results" | "results for the EMOTomo model set, served via OpenRouter" |
| "the benchmark proves…" | "this sample run shows…, within the stated limitations" |

The only acceptable use of the bare phrases "EMOTomo benchmark" or "OpenRouter benchmark" in public
docs is to explain that **CompanionBench is not** an EMOTomo benchmark and **not** an OpenRouter
benchmark — i.e. in an explicitly negating or policy context like this one.

## Required hedges for any result

Whenever you publish numbers, keep these nearby:

1. **Scope:** which model set, which provider, which manifest/tasks, how many repeats.
2. **Sample, not leaderboard:** the task suite is small and illustrative (see
   [methodology limitations](methodology.md#10-limitations)).
3. **Uncertainty:** report bootstrap 95% CIs; do not call indistinguishable scores a "win".
4. **Scoring basis:** rule-based, deterministic — blunt, and not a human or calibrated-judge verdict.
5. **Cost honesty:** cost is `null` when unknown, never invented.

## Why this matters

CompanionBench exists to make companion-communication failure modes measurable. That value
evaporates the moment results are oversold — a small, authored, rule-scored sample is easy to
misread as a universal ranking. Holding the line on precise language is part of the methodology,
not a disclaimer bolted on after. See the [benchmark card](benchmark_card.md) and
[methodology](methodology.md).
