<!-- SPDX-License-Identifier: Apache-2.0 -->
# LLM-as-judge (opt-in) & calibration

CompanionBench can run an **optional** LLM-as-judge as a *second* automated signal, calibrated
against the rule-based scorer and the human gold set. The judge is **opt-in, live-gated, biased,
and stored separately** — it never overwrites or replaces the rule-based scores, and it is never
the source of truth. This page documents how it works and how much to trust it (not much, yet).

## What the judge is — and is not

- **Is:** a versioned prompt (`judge_prompts.JUDGE_PROMPT_VERSION`) sent to a provider model that
  returns per-dimension 0–1 scores, parsed strictly into a `JudgeVerdict` and written to
  `judge_scores.json` / `judge_events.jsonl` (schema: `companion_bench.schemas.judge`).
- **Is not:** a replacement for rules or humans, a leaderboard, or a trusted number. LLM judges are
  known to be biased — verbosity/length bias, position bias (in pairwise setups), self-preference
  (favoring their own family), prompt-sensitivity, and non-determinism.

## Bias mitigations built into the prompt

- **Model identity is hidden** from the judge (it sees only the response text).
- The prompt tells the judge to **score against the rubric, not length**, and not to reward generic
  warmth or verbosity.
- **Format-compliance is kept separate** from companion quality.
- Rationales are required to be **short**, reducing rationalization drift.

These reduce, but do not eliminate, bias. Treat judge numbers as a rough, biased signal.

## Running the judge

```bash
# OFFLINE mock judge — a deterministic simulator (validates the pipeline, NOT judge quality):
companion-bench judge --responses data/gold/pilot_responses.jsonl \
  --judge-provider mock --judge-model demo --out analysis/judge/pilot

# LIVE real judge — gated: needs --live AND COMPANIONBENCH_LIVE=1 AND --max-cost-usd AND confirmation:
COMPANIONBENCH_LIVE=1 companion-bench judge --run runs/<a_run> \
  --judge-provider openrouter --judge-model <slug> \
  --out analysis/judge/<run> --live --yes --max-cost-usd 2
```

Hard constraints (enforced in code + tests):

- A real judge requires **all** of `--live`, `COMPANIONBENCH_LIVE=1`, `--max-cost-usd`, and
  confirmation (`--yes` or interactive). Without them it refuses **before any network call**.
- **Tests never call a live judge** — the mock judge is offline; the rubric seam is unit-tested
  with a stub adapter.
- Malformed judge output is recorded as an explicit **failure**, never coerced to a high score.
- Judge cost stops at the cap; cost is `null` when unknown, never invented.

## Judge-vs-gold (and judge-vs-rule) calibration

```bash
companion-bench calibrate judge --gold data/gold/pilot_v0_1_alpha.jsonl \
  --judge analysis/judge/pilot/judge_scores.json --out analysis/calibration/judge_vs_gold_pilot.md
```

Reports per-dimension MAE + Pearson + Spearman and overall accept/reject agreement against the
human consensus, with bias caveats attached. The offline **mock** judge is a deterministic
simulator that mirrors the rule-based signal, so mock judge-vs-gold ≈ rule-vs-gold — it proves the
*pipeline*, not judge quality.

## Status

- **Judge interface:** implemented (offline mock + live-gated real provider path).
- **Live judge-vs-human calibration: REQUIRES LIVE RUN.** No live judge run was performed in this
  pilot; the numbers here come from the offline mock only.

## Allowed vs. forbidden claims

See [`public_claims.md`](public_claims.md). You may report, with the judge model + prompt version +
that it is one biased judge: "judge X agreed with the pilot consensus at rate Y (small synthetic
fixture)." You may **not** present judge scores as the benchmark result, as a leaderboard, or as
"human-validated"; and you must always show the rule-based baseline alongside.
