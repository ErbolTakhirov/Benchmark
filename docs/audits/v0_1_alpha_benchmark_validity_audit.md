<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench v0.1.0-alpha Benchmark Validity Audit

**Audit date:** 2026-07-03 · **Commit:** `feb4e88a05fcc2b1254280768d8e0619a76890f5` · **Tag:** `v0.1.0-alpha`
· **Branch:** `main` · **Scope:** offline, read-only, no live API calls.

This is an adversarial, evidence-first validity audit. It asks seven blunt questions: does the
benchmark actually run, are its numbers meaningful, does it capture real companion-communication
behavior, which parts are real model signal, which parts are scorer/task/format artifacts, how
strong is the alpha, and what must be fixed before a stable v0.1. It is deliberately unflattering.

### Evidence conventions

- Claims are cited as `path:line` or to a command in **Appendix A**. Statistics are reproduced by
  scripts whose output is in **Appendix B**; every headline number was recomputed this session
  from committed artifacts with stdlib-only code.
- **[VERIFIED]** — confirmed by reading source, running an offline command, or recomputing from a
  committed artifact this session.
- **[INFERENCE]** — a reasoned conclusion not directly executable offline (e.g. cluster-corrected
  CIs, live-run behavior). Labeled so the reader can discount it.
- **REQUIRES RUN** — needs a live provider call or a full run and was intentionally not executed;
  see **Appendix C**.
- **НЕ НАЙДЕНО** — a claim made somewhere in the repo that could not be reproduced from any
  committed artifact.
- Naming follows `docs/public_claims.md`: results are "the CompanionBench evaluation using the
  EMOTomo model set via OpenRouter"; the EMOTomo model set and the OpenRouter provider are never
  described as the benchmark itself.

---

## Executive verdict

**Public-alpha valid.**

CompanionBench v0.1.0-alpha is a real, working, honestly-scoped measurement instrument — not a
toy, and not a weak MVP. The pipeline runs end-to-end, is byte-deterministic, ships live
multi-model results, passes every local quality gate, and is unusually disciplined about not
overclaiming. That is genuinely more than most first public alphas deliver.

But it is **not** a serious/credible benchmark yet, and the gap is not cosmetic. The scores are a
**scorer-relative construct**, not validated companion quality: they are produced by a rule-based
substring/decision matcher with several exploitable asymmetries, over an all-synthetic English-only
task suite, with **zero human grounding** and **no calibrated judge** (the LLM-judge interface is
an intentional `NotImplementedError` stub — `src/companion_bench/evaluators/rubric.py:48,60`
[VERIFIED]). The published confidence intervals are pseudoreplicated and roughly **1.7× too
narrow** [INFERENCE], and at least one headline statistic (a Spearman of 0.573) cannot be
reproduced from any committed artifact [VERIFIED, НЕ НАЙДЕНО].

The honest one-line answer to "does it capture real companion-communication characteristics?":
**it captures a coarse, reproducible good-vs-weak signal that generalizes across splits, wrapped
around a fine-grained scoring layer that mostly measures whether a model can emit the scorer's
expected JSON labels and keywords.** The coarse signal is real. The fine rankings are largely
artifact.

---

## Grades

| Dimension | Grade | One-line justification |
| --- | --- | --- |
| Methodology | **B** | Exemplary claims policy and hedging; undermined by a stale/unreproducible statistic and docs that describe a mock-only MVP while the repo ships live results. |
| Task suite | **B−** | Perfect structural balance and licensing; weakened by a 100%-redundant timing dimension, keyword echoes, a gentle-style monoculture, and synthetic English-only scenarios. |
| Scoring validity | **C−** | Deterministic and transparent, but scores are scorer-relative: parse-failure asymmetry, substring matching, self-reported style/permission, and an always-wait refuge are all demonstrable. |
| Statistical reliability | **C+** | Internally exact and headline correlations reproduce; CIs are pseudoreplicated (~1.7× too narrow), one stat is unreproducible, and tier separability is overstated. |
| Reproducibility | **A−** | Green gates, byte-deterministic runs, keyless fresh-clone path; docked for version drift and no resume/checkpoint. |
| Security | **A** | No secrets in tree or history, `.env` untracked, samples sanitized, redaction tests present. |
| Architecture | **B+** | Clean layered DAG, provable adapter isolation, injectable clock; docked for a 791-LOC CLI god-module and a storage docstring that overpromises crash-safety. |
| Open-source readiness | **B−** | Apache-2.0, CITATION, strong docs; docked for a wrong NOTICE URL, no PyPI path, version drift, and a benchmark card that contradicts shipped results. |

---

## What CompanionBench measures reasonably well

- **A coarse good-vs-weak ordering that generalizes across held-out tasks.** Model overall scores
  on the 150-task public split and the 36-task held-out split correlate **Pearson 0.967 / Spearman
  0.939** (recomputed; Appendix B §2) [VERIFIED]. The top cluster (the DeepSeek family) sits well
  above the bottom (gemini-2.5-flash-lite, glm-4.5-air) on **both** splits, and the gap survives
  even under cluster-corrected CIs [INFERENCE]. A model that is clearly better here is probably
  clearly better on unseen authored scenarios of the same kind.
- **Decision correctness under multi-turn context.** The core construct — *whether* to intervene,
  wait, or abstain given prior turns — is genuinely multi-turn (probe *n+1* sees the model's turn
  *n*, `src/companion_bench/runner/engine.py:168-201`) and is scored consistently [VERIFIED].
- **Safety-refusal and timing behavior generalize best per-family.** Cross-split family
  correlations: safety **0.956/0.964**, timing **0.916/0.939** (Appendix B §; recomputed)
  [VERIFIED]. These two dimensions carry the most stable signal.
- **Cost and latency accounting is honest.** Cost is `null` when unknown, never invented
  (`CLAUDE.md` core rule; `evaluators/aggregate.py:141`); the frontier command computes a real
  Pareto set. Sample cost sums reproduce exactly ($2.55 public / $0.59 held-out; Appendix B §5)
  [VERIFIED].
- **Determinism.** Two seeded offline smoke runs produced identical `scores.json` and identical
  `events.jsonl` modulo `run_id`/`timestamp`/`event_id` (Appendix A) [VERIFIED]. Scored paths are
  reproducible.
- **Behavior flags are honestly derived.** Each named flag maps 1:1 from a concrete scorer signal
  (`evaluators/flags.py:19-34`); they are count-only and never feed back into scores [VERIFIED].

## What CompanionBench does NOT measure yet

- **Human-perceived companion quality.** There is no human gold set and no human-agreement study;
  `docs/benchmark_card.md` and `docs/methodology.md` acknowledge human eval as future work. Nothing
  ties the numbers to what a person would call good companionship [VERIFIED].
- **Calibrated judgment of message *content*.** The LLM-judge is a stub
  (`evaluators/rubric.py:48,60` raise `NotImplementedError`) [VERIFIED]. All content scoring is
  substring/keyword coverage.
- **Emotional attunement independent of a self-declared label.** Empathy's style component reads
  the model's own `turn.style` field, not the prose (`evaluators/rule_based.py:208`) [VERIFIED].
- **Quality of a correct abstention.** For abstain-expected tasks (e.g. the safety-refusal suite),
  a warm, helpful decline and a cold, unhelpful refusal score identically, because empathy/positive
  signals only apply on `INTERVENE` (`rule_based.py:200-201`); the rubric prose that names "a cold
  refusal is the weaker failure" is never scored [VERIFIED].
- **Paraphrase robustness.** Scoring is literal substring matching (`rule_based.py:95-110`); a
  correct answer phrased without the expected keywords is under-credited [VERIFIED].
- **Anything non-English or non-synthetic.** All 186 tasks are `source_type: synthetic`, English
  (Appendix B §; task scan) [VERIFIED].

## What parts of the result are likely real model signal

- The **cross-split rank correlation** (0.967/0.939) and **tier *membership* stability** (the
  top-4 stay top-4; gemini is last on both splits) — Appendix B §2/§3 [VERIFIED].
- **Per-model parse/failure rates** as a behavioral property: `unparseable_output` totals 1099
  (public) / 280 (held-out) and are concentrated in specific models; a model that cannot reliably
  emit the required envelope is genuinely worse at this structured task [VERIFIED].
- **Safety and timing family orderings**, which generalize across splits (0.956 / 0.916 Pearson)
  [VERIFIED].
- **Cost/latency frontier** positions (real usage-based accounting) [VERIFIED].

## What parts are likely scorer/task/format artifacts

- **`missed_emotional_validation` is the single most common flag** (5652 public occurrences,
  Appendix B §5) and maps from `weak_positive_signals` — i.e. the model's message didn't contain
  every expected keyword substring. This is a coverage artifact, not a measured empathy failure
  [VERIFIED].
- **Parse–format entanglement.** A transport/parse failure on an initiative task scores ~0.333,
  not 0 (initiative=0, timing/empathy/adaptation→N/A weight-redistributed, **safety defaults to
  1.0**), so score partly tracks JSON-compliance, not companionship (`rule_based.py:148-149,
  185-186, 200-201, 263-266`; `aggregate.py:42-45`) [VERIFIED].
- **Fine (adjacent-rank) differences.** Only 1/9 (public) and 0/9 (held-out) adjacent ranks have
  non-overlapping CIs even at the published, too-narrow widths (Appendix B §3) [VERIFIED].
- **The timing dimension**, which is 100% redundant with the intervene decision (see below).
- **The gentle-style prior.** 76/195 style-bearing probes prefer `gentle`; a model biased toward a
  gentle self-declared label is rewarded by the base rate [VERIFIED].
- **English-only synthetic scenarios**, which cannot speak to real or multilingual usage.

---

## Methodology audit

**Objective and construct.** The stated objective — jointly measuring initiative relevance, timing,
empathy, adaptation, abstention, and safety in multi-turn companion conversations — is coherent and
genuinely under-served by existing benchmarks. The six-dimension decomposition is reasonable.

**Claims policy is a real strength.** `docs/public_claims.md` is exemplary: it forbids
"most human-like", forbids branding the model set or provider as the benchmark, forbids "final
leaderboard", and *requires* bootstrap CIs and scope hedges [VERIFIED]. A guard test
(`tests/test_public_claims.py`) mechanically enforces the naming subset over the README and all
docs [VERIFIED]. This is the kind of discipline mature benchmarks adopt late; here it is present at
alpha.

**Model-set / provider separation is respected** throughout the prose and enforced by the guard.

**Weaknesses (claim-vs-reality gaps):**

1. **A headline statistic is unreproducible.** `docs/results_interpretation.md:44` and the
   `heldout-r5` sample docs report a Spearman rank correlation of **0.573**. The paired Pearson
   (0.858) reproduces exactly from the committed `fullsuite-r5`×`heldout-r5` scores, but the
   Spearman recomputes to **0.6121**, not 0.573 (Appendix B §2) [VERIFIED, НЕ НАЙДЕНО]. The
   direction is conservative (the true rank agreement is higher), but an unreproducible published
   number is a methodology defect, and it propagates into the "0.573 → 0.726 improvement" narrative
   in the expanded summaries.
2. **The benchmark card contradicts the shipped results.** `docs/benchmark_card.md:7,39,45` still
   says "Version 0.1 (MVP scaffold)", "the shipped numbers come from a simulator", and "mock scores
   validate the pipeline, not model quality" — while the repo now ships live OpenRouter results for
   10 real models [VERIFIED]. The card that is supposed to be the authoritative description is
   stale.
3. **README internal contradiction.** `README.md:62` says the benchmark compares models "across
   five dimensions"; `README.md:200`, `docs/scoring.md`, and `docs/architecture.md` all correctly
   say six [VERIFIED].
4. **The "hidden" split is only hidden by convention.** Held-out tasks live in plaintext under
   `tasks/*/heldout/`, and their results are published in `docs/samples/`. The split is enforced by
   glob path, and task metadata even calls it `split: hidden` (vocabulary drift vs the docs' "held-
   out") [VERIFIED]. Cross-split correlation is a useful generalization probe, but because both
   splits were authored by the same hand with the same templates, it measures template
   transfer, not true out-of-distribution generalization [INFERENCE].

**Grade: B.**

---

## Task suite audit

**Counts (recomputed from `tasks/`; Appendix B §):**

| Family | Public | Held-out | Total |
| --- | --- | --- | --- |
| initiative | 25 | 6 | 31 |
| timing | 25 | 6 | 31 |
| empathy | 25 | 6 | 31 |
| adaptation | 25 | 6 | 31 |
| abstention | 25 | 6 | 31 |
| safety | 25 | 6 | 31 |
| **Total** | **150** | **36** | **186** |

Perfectly balanced (6 × (25 + 6)). Manifests resolve to exactly these counts (`validate` output,
Appendix A). All 186 are `source_type: synthetic`, CC0-licensed, with `expected_abstention_behavior`
and `failure_modes` present [VERIFIED].

**Probe decision mix (263 probes):** 149 intervene / 65 wait / 49 abstain. **Difficulty:** 58 easy
/ 83 medium / 45 hard. **Permission probes:** only 8 in the whole suite (the permission dock is
barely exercised). **Style prior:** gentle 76, practical 51, direct 23, reassuring 19, celebratory
9, curious 8, playful 7, neutral 2 (gentle+reassuring ≈ 49% of style-bearing probes) [VERIFIED].

**Strong tasks (well-designed scenarios):**

1. `tasks/safety/heldout/doxxing-refusal.yaml` — realistic manipulation, articulated hard-vs-weak
   failure modes, content-meaningful positive signals.
2. `tasks/safety/heldout/extreme-fasting-plan-refusal.yaml` — medical-safety refusal with a
   redirect-to-clinician expectation.
3. `tasks/safety/heldout/gaslight-user-self-doubt-refusal.yaml` — subtle third-party-harm case,
   correctly rated `hard`.
4. `tasks/safety/heldout/deceptive-review-refusal.yaml` — decline deception *and* offer an honest
   alternative (tests the "help ≠ comply" boundary).
5. `tasks/initiative/quick-question-then-chitchat.yaml` — a clean restraint test: wait expected,
   empty intervention window, negative signals that penalize manufactured proactivity.

**Weak tasks / design smells:**

1. **The entire timing family** (e.g. `tasks/timing/*.yaml`) — the timing dimension is redundant
   (see Scoring), so these 31 tasks add little independent signal beyond the intervene decision.
2. `tasks/abstention/decline-major-life-decision.yaml` and its domain-swapped twin
   `tasks/abstention/heldout/decline-choose-vote.yaml` — same template/rubric pattern, different
   surface topic; dilutes the held-out generalization signal.
3. `tasks/adaptation/drop-the-ex-topic.yaml` — an `expected_target_keyword` ("Saturday") appears
   verbatim in the scripted dialogue the model reads, so it is trivially echoable under substring
   matching.
4. `tasks/adaptation/dislikes-rhetorical-questions.yaml` — likewise ("the workshop" echoes).
5. Any abstain-expected task whose probe `positive_signals` are set — those signals are dead code
   for scoring (empathy is N/A on abstain), so the authored nuance is uncredited.

**Leakage / gaming inventory:**

- **Keyword echo:** 37 (task, probe) pairs have an `expected_target_keyword` appearing verbatim in
  their own scripted dialogue (Appendix B §) [VERIFIED]. Under substring matching a model can lift
  the keyword straight from context.
- **Answer key in-repo:** the entire scoring rubric (expected decisions, keywords, forbidden
  patterns) ships in the same repo as the tasks; a model trained on or prompted with the repo can
  reach the ceiling. The public/held-out split is the only mitigation, and it is plaintext.
- **Vestigial fields:** top-level `positive_signals: []` in all 186 tasks; 89/263 probes carry no
  probe-level positive signals [VERIFIED].
- **Near-duplicates across the split** (abstention and adaptation pairs) reduce the effective size
  of the held-out set.

**Grade: B−.**

---

## Scoring validity audit

The scorer is transparent and deterministic — every number traces to a rule
(`evaluators/rule_based.py`). That is its great virtue and, simultaneously, the source of its
gameability: the rules are simple enough to satisfy without doing the underlying thing.

**Score decomposition.** Per probe, six dimension scorers return a value in [0,1] or `None`
(not-applicable → weight redistributed, `rule_based.py:301-308`). Task total = weighted mean;
run overall = **unweighted mean over all (task, repeat) units** (`aggregate.py:118`) [VERIFIED].

**Parse-failure handling (the load-bearing defect).** When output does not parse:
initiative → 0.0, timing/empathy/adaptation → `None`, abstention → `None` (on intervene-expected
probes), **safety → 1.0** (it scans empty text and finds no forbidden pattern). Net: a failed call
on an initiative task scores **(1.0·0.0 + 0.5·1.0)/1.5 = 0.333**, not 0
(`rule_based.py:148-149,263-266`; weights `rule_based.py:43-49`) [VERIFIED]. Failures are fed to
the scorer as empty text (`aggregate.py:42-45`).

**Top-10 gaming vectors (ranked by exploitability × impact):**

| # | Vector | Mechanism | Evidence | Est. impact |
| --- | --- | --- | --- | --- |
| 1 | **Echo the answer key** | Substring coverage credits keywords copied from context/repo | `rule_based.py:95-110`; 37 echo probes (App. B) | Ceiling on echoable tasks |
| 2 | **Always WAIT** | timing/empathy/adaptation → N/A, safety → 1.0; middling score for doing nothing | Offline: mock/silent-v1 = ~0.63, **4/8 passed**, safety 1.00 (App. A) | Passing score with zero capability |
| 3 | **Fail to parse on hard probes** | 0.333 floor > honest-wrong 0.0–0.2 | `rule_based.py:263`; §above | Rewards refusing to answer over trying |
| 4 | **Self-declare the preferred style** | Empathy reads `turn.style` label, not prose | `rule_based.py:208` | Free empathy credit |
| 5 | **Self-report ask_permission=true** | Permission dock checks the boolean, not the message | `rule_based.py:277-284` | Avoids permission penalty |
| 6 | **Decision arbitrage** | WAIT-instead-of-ABSTAIN = 0.7; ABSTAIN-instead-of-WAIT = 0.6 partial credit | `rule_based.py:174,179` | Partial credit for wrong-but-adjacent |
| 7 | **Exploit timing redundancy** | Timing = 1.0 iff intervene∈window, and window ≡ intervene set | `rule_based.py:187`; 186/186 (App. B) | Double credit for one correct decision |
| 8 | **Cold correct abstention** | Warm vs cold decline score identically on abstain tasks | `rule_based.py:200-201` | Nuance uncredited |
| 9 | **Silence guarantees safety 1.0** | Safety only docks on forbidden patterns / missing permission | `rule_based.py:263-288` | Do-nothing → perfect safety |
| 10 | **Substring false-positives** | `_contains` has no word boundaries ("help" ⊂ "helpless") | `rule_based.py:95-96` | Noise in coverage scores |

**Timing is 100% redundant** [VERIFIED]: across all 186 tasks, `allowed_intervention_window.probe_ids`
equals exactly the set of probes whose `expected_decision` is intervene (0 mismatches; Appendix B §).
So the timing scorer awards 1.0 exactly when the model intervenes where intervention was expected —
the same condition the initiative scorer already rewards — and 0.0 when it intervenes where it
should not. Timing adds no information beyond the decision; it is double-counting.

**Empirical gaming demonstration (offline).** The always-wait `mock/silent-v1` profile scored
**~0.63 with 4/8 tasks passed and safety 1.00** on the smoke manifest, *beating* the active-but-wrong
`mock/intrusive-v1` (~0.44, 1/8) (Appendix A) [VERIFIED]. A do-nothing agent both passes tasks and
outranks a wrong-but-engaged one. This is the always-wait refuge, live.

**Safety detection is pattern-only.** The safety scorer docks solely on `forbidden_patterns`
(regex/substring) in the message, or a missing-permission flag (`rule_based.py:263-288`). 88/186
tasks even carry safety boundaries; the rest default to 1.0. Real unsafe behavior phrased outside
the pattern list is invisible. In the public sample, `unsafe_overreach` fired only 8 times across
150 tasks × 10 models × 5 repeats — consistent with a weak detector, not a safe fleet [VERIFIED,
INFERENCE on cause].

**Behavior flags are score-inert** (`flags.py`) — a reporting layer only [VERIFIED].

**Verdict — true companion quality vs scorer-relative construct.** The scores are a
**scorer-relative performance measure**: they quantify how well a model emits the decisions,
labels, and keyword substrings the rule-based scorer expects, under authored scenarios. They are a
useful, reproducible *proxy at the coarse level* (good models score higher, and it generalizes),
but they are **not** a measure of companion quality, and several of the fine-grained sub-scores
(timing, self-reported empathy/style, permission, cold-vs-warm abstention) are artifacts of the
rule design rather than model behavior. Treat overall as an ordinal coarse signal; do not treat
dimension deltas as construct-valid.

**Grade: C−.**

---

## Statistical reliability audit

**Internal consistency (recomputed).** Across all 40 model×split score files, the stored `overall`
matches the mean of per-task totals to within **5.3×10⁻⁷**, and `n_passed` recounts exactly
(Appendix B §1) [VERIFIED]. The arithmetic is honest.

**Correlation provenance (recomputed; Appendix B §2):**

| Pair | Claimed | Recomputed | Match |
| --- | --- | --- | --- |
| public-expanded (150) ↔ held-out-expanded (36) | 0.968 / 0.939 | **0.9674 / 0.9394** | ✅ |
| fullsuite (60) ↔ held-out-expanded (36) | 0.848 / 0.726 | **0.8477 / 0.7212** | ✅ |
| fullsuite (60) ↔ held-out (12) | 0.858 / **0.573** | 0.8584 / **0.6121** | Pearson ✅, Spearman ❌ НЕ НАЙДЕНО |

The 0.573 rank correlation in `docs/results_interpretation.md:44` and the `heldout-r5` docs is not
reproducible from any committed artifact (recomputes to 0.6121) [VERIFIED].

**Confidence intervals are pseudoreplicated.** The bootstrap resamples individual **(task, repeat)**
units (`aggregate.py:174-183`), treating 5 repeats of the same task as 5 independent observations.
Repeats of one task are highly correlated, so this understates uncertainty. A task-level cluster
re-bootstrap (5000 resamples, seed 42, over per-task means) yields CIs **~1.77× wider (public) and
~1.69× wider (held-out)** on average (Appendix B §4) [INFERENCE — exact clustering needs the
per-repeat units, which `scores.json` does not persist].

**Separability is overstated.** At the *published* (too-narrow) widths:
- Public 150: only **1/9** adjacent ranks have disjoint CIs; 32/45 all-pairs disjoint.
- Held-out 36: **0/9** adjacent ranks disjoint; 20/45 all-pairs disjoint.

The top-4 are a transitive tie (deepseek-v3.2 [0.739,0.767] overlaps deepseek-chat-v3.1
[0.737,0.765]); the sample docs' "three tiers survived intact" is defensible only as *membership*,
not as statistical separability. Under cluster CIs the middle collapses further [INFERENCE].

**Supported conclusions:**
- Strong cross-split correlation at expanded sizes (0.967/0.939) [VERIFIED].
- Coarse good-vs-weak ordering; top-cluster vs bottom-cluster separation survives cluster CIs
  [INFERENCE].
- gemini-2.5-flash-lite is clearly last on both splits [VERIFIED].
- Tier *membership* is stable (max adjacent rank movement ≈ 2) [VERIFIED].
- Mean/cost parity across generations [VERIFIED].
- safety and timing generalize best per-family (0.956 / 0.916 Pearson) [VERIFIED].

**NOT supported:**
- A single "top model" (top-3 are tied) — only a tied-first cluster.
- Fine or adjacent-rank ordering.
- "Three statistically distinguishable tiers."
- Held-out-standalone ranking (0/9 adjacent separable).
- Family-level fine claims for initiative (0.606/0.418) and abstention (0.461/0.588) — noisy
  [VERIFIED].
- The 0.573 statistic.

**Allowed claim granularity:** coarse tier membership and top-cluster-vs-bottom-cluster, always
with CIs; never a numeric rank order or a "best model".

**Grade: C+.**

---

## Reproducibility audit

**Local gates (this session; Appendix A):**

| Gate | Result |
| --- | --- |
| `uv sync --all-extras` | exit 0 |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | passed |
| `uv run mypy` | Success: no issues in 41 files |
| `uv run pytest -q` | **182 passed, 1 skipped** |
| `uv build` | built `companion_bench-0.1.0` (sdist + wheel) |
| `validate` smoke/full/held-out | 8 / 150 / 36 tasks, all valid |
| offline smoke `run`+`score`+`report` | exit 0, empathetic overall 1.000 |
| multi-model mock + bootstrap + report | exit 0, persona ordering correct |

**Determinism [VERIFIED].** Two seeded smoke runs → identical `scores.json` and `events.jsonl`
(modulo `run_id`/`timestamp`/`event_id`).

**Fresh-clone story [VERIFIED].** The documented command sequence runs keyless and offline against
the mock; the quickstart matches the CLI. A newcomer can reproduce the smoke path command-for-
command.

**ACM-style artifact mapping:**

| Level | Verdict | Note |
| --- | --- | --- |
| Available | **Yes** | Public repo, Apache-2.0, tagged release. |
| Functional | **Yes** | Gates green; pipeline runs end-to-end offline. |
| Reusable | **Partial→Yes** | Clean adapters/skills; docked for version drift and no resume. |
| Validated (results reproducible) | **Partial** | Offline mock + committed stats reproduce; live numbers REQUIRE RUN (Appendix C). |

**Deductions:** (1) **Version drift** — `pyproject.toml:7` is `0.1.0` while the tag/CITATION/CHANGELOG
are `0.1.0-alpha`; the built wheel and `--version` report `0.1.0` [VERIFIED]. (2) **No
resume/checkpoint** — the public sample was assembled from two invocations because a mid-run failure
loses everything (see Architecture); `docs/samples/.../README.md:76` admits "the CLI has no built-in
resume" [VERIFIED]. (3) Stale model-set/doc headers.

**Grade: A−.**

---

## Security and artifact hygiene audit

**Scan (tracked files; values never printed; Appendix A):**

| Check | Result |
| --- | --- |
| Key shapes (`sk-or-v1-`, `sk-ant-`, `AKIA…`, `ghp_…`, PRIVATE KEY blocks) | **none** in tracked files |
| Literal `OPENROUTER_API_KEY=`/`Authorization: Bearer`/`x-api-key` assignments | **none** |
| `sk-or-` occurrences | 3, all placeholders/grep-patterns in skill docs (e.g. `SKILL.md:16` `sk-or-...`) |
| `.env` tracked | **No** (untracked, gitignored) |
| Raw `*.jsonl` runs tracked | **No** |
| `.github/` present | **No** (CI archived under `docs/ci-disabled/`) |

**Findings:** clean. No secrets in the working tree; `.env` hygiene correct; samples are sanitized
(rationales are closed-set scorer template strings, not raw model text). A dedicated
`tests/test_secrets.py` proves keys never reach an artifact. Residual, local-only, theoretical
concern: redaction is exact-value based; this does not affect committed artifacts.

**Grade: A.**

---

## Architecture audit

**Strengths.** Clean layered dependency DAG (`schemas → adapters/runner/evaluators → cli`), no
cycles [VERIFIED by imports]. Adapter isolation is real: only the mock reads
`ChatRequest.simulation_context`; real adapters ignore it (a test proves it). The engine takes an
injectable `Clock` and `Sleeper` for deterministic, offline, no-real-sleep tests. Registry-based
adapters (`@register_adapter`: mock, openai, openai_compatible, anthropic, openrouter). 25 test
files including persona-regression, signal-disjointness, safety-audit, bootstrap, and public-claims
guards [VERIFIED].

**Risks / debt:**

1. **Storage docstring overpromises crash-safety** [VERIFIED]. `storage/jsonl.py:3-4` says a
   "crashed run still leaves a readable partial log" and `:33` says "a resumed run never truncates
   prior history". But the engine buffers **all** events in RAM (`engine.py:138,149`), calls
   `events_path.unlink(missing_ok=True)` (`engine.py:289`), and writes the whole log only at the
   very end (`engine.py:298-322`). The `EventWriter` is append+flush in isolation, but the engine
   never streams to it, so a crash during the model-call phase (the likely failure point in a long
   live run) persists **zero** events, and there is no resume. This is the mechanism behind the
   two-invocation public sample.
2. **CLI god-module.** `src/companion_bench/cli.py` is **791 LOC** (~12% of ~6.6k source LOC in one
   file) mixing arg parsing, layout sniffing, table formatting, and frontier assembly [VERIFIED].
3. **`rubric.py` is an intentional stub** (`NotImplementedError`) — fine as a documented interface,
   but it means the "future judge" the whole design points at is unbuilt [VERIFIED].
4. **Minor:** the timing dimension's redundancy is baked into the data model, not the code; some
   adapter code (`anthropic`/`openai_compatible`) overlaps.

**Grade: B+.**

---

## External benchmark comparison

Honest positioning against mature efforts (model knowledge; [INFERENCE] where noted):

- **vs HELM.** CompanionBench shares the multi-metric, taxonomy-driven spirit and adds a construct
  HELM under-covers (proactive/companion behavior). It lacks HELM's breadth, robustness/calibration
  metrics, and per-instance transparency. Far smaller and younger.
- **vs MT-Bench / Chatbot Arena.** It is genuinely multi-turn and, unlike single-response judging,
  scores *whether and when to speak*. But MT-Bench/Arena are grounded in human or strong-judge
  preference; CompanionBench has **no human grounding and no judge** — the central external-validity
  gap.
- **vs MLPerf.** It borrows good discipline (seeds, pins, cost caps, disclosure, deterministic
  replay) but lacks a formal run-rules spec, divisions, and third-party submission/audit; served
  models are not version-pinned.
- **vs HF Evaluate.** Docs and metric transparency are above the typical bar, but there is no PyPI
  package / `pip install` path documented, and the metric is a single bespoke rule scorer rather
  than a modular card library.
- **vs ACM artifact badging.** Available/Functional yes; Reusable partial; Validated partial (see
  Reproducibility).

**Maturity verdict: public-alpha.** More than an internal tool (real live results, honest claims
policy, green gates, sanitized samples); well short of a credible/serious benchmark (no human
calibration, gameable rule scorer, pseudoreplicated CIs, tiny synthetic suite). This matches the
repo's own `0.1.0-alpha` self-label — no equality with mature benchmarks is claimed here.

---

## Supported claims

- "CompanionBench runs end-to-end offline and deterministically; all local gates pass." [VERIFIED]
- "In the CompanionBench evaluation using the EMOTomo model set via OpenRouter, model orderings
  correlate strongly across the public and held-out splits (Pearson 0.967 / Spearman 0.939 at
  expanded sizes), within stated limits." [VERIFIED]
- "A coarse good-vs-weak separation (top DeepSeek cluster vs gemini-2.5-flash-lite / glm-4.5-air)
  holds on both splits and survives cluster-corrected CIs." [VERIFIED / INFERENCE]
- "safety and timing family orderings generalize best across splits." [VERIFIED]
- "Cost is reported honestly (null when unknown); sample cost sums reproduce ($2.55 / $0.59)."
  [VERIFIED]
- "Scores are rule-based, deterministic, scoped to these tasks/settings/model versions, and are not
  a human or calibrated-judge verdict." [VERIFIED]

## Unsupported / forbidden claims

- ❌ Any "most human-like" / "best companion" / universal-quality claim (banned by policy; no such
  construct is measured).
- ❌ Branding the model set or the provider as the benchmark itself (banned by policy).
- ❌ "There is a single top model" — the top-3 are statistically tied.
- ❌ "Three statistically distinguishable tiers" / any fine or adjacent-rank ordering.
- ❌ Citing "Spearman 0.573" — it is not reproducible from committed artifacts (actual 0.6121).
- ❌ "The scores measure empathy / emotional intelligence / safety" as validated traits — they
  measure scorer-relative behavior on authored scenarios.
- ❌ Treating the held-out split as true out-of-distribution generalization (same author,
  templates, plaintext).

---

## Top 15 fixes before v0.1 stable

Ordered by impact on validity:

1. **Build a human gold set** and report human–scorer agreement (κ/correlation) — the missing
   external-validity anchor.
2. **Implement the LLM-as-judge** behind `rubric.py`, kept *separate* from and measured *against*
   the rule scorer (never silently blended).
3. **Fix parse-failure scoring** — floor a non-parse to 0 (or a defined low), and stop letting
   safety default to 1.0 on empty/unparsed output (`rule_based.py:263-266`).
4. **De-redundantize timing** — either make the window genuinely differ from the intervene set, or
   drop timing as a separate dimension and fold it into initiative (currently 186/186 identical).
5. **Verify self-reported fields** — score empathy/style from the message prose, not `turn.style`;
   verify `ask_permission` against the text (`rule_based.py:208,277`).
6. **Paraphrase-robust matching** — add word boundaries and semantic/synonym matching; remove the
   37 in-dialogue keyword echoes so answers can't be lifted from context.
7. **Cluster the bootstrap by task** (or persist per-repeat units and resample tasks) so CIs stop
   being ~1.7× too narrow (`aggregate.py:174`).
8. **Score the quality of a correct abstention** — credit warm-vs-cold declines differently so the
   safety-refusal suite's authored nuance is not dead (`rule_based.py:200`).
9. **Strengthen safety detection** beyond forbidden-pattern substrings (classifier or judge), and
   add per-task safety gates so silence can't guarantee 1.0.
10. **Fix the stale statistic and stale docs** — remove/recompute the 0.573, and update
    `benchmark_card.md` so it no longer describes a mock-only MVP while shipping live results.
11. **Resolve version drift** — set `pyproject.toml` to `0.1.0-alpha` (or the intended value) so
    the wheel/`--version`/tag agree.
12. **Add resume/checkpoint** and stream events to disk during the run (stop buffering-then-writing-
    at-end + `unlink`) so a crashed live run keeps its partial log (`engine.py:289,298`); align the
    `storage/jsonl.py` docstring with reality.
13. **Diversify the suite** — non-English coverage, non-synthetic/real-derived scenarios, and remove
    cross-split near-duplicates and the gentle-style monoculture.
14. **Add adversarial scorer tests** — always-wait, always-abstain, style-liar, generic-template,
    and malformed-but-safe bots, asserting they do *not* pass (today `mock/silent-v1` passes 4/8).
15. **Fix repo-hygiene loose ends** — the wrong `NOTICE` URL (`companion-bench/companion-bench` vs
    `ErbolTakhirov/Benchmark`), the README "five dimensions" line, and add a documented
    `pip install` / PyPI path; add a provenance block (commit, model versions, seeds, CI widths) to
    every report.

---

## Appendix A — command transcript (offline, this session)

| Command | Exit |
| --- | --- |
| `git rev-parse HEAD` → `feb4e88…` ; `git describe` → `v0.1.0-alpha` | 0 |
| `uv sync --all-extras` | 0 |
| `uv run ruff check .` | 0 (All checks passed) |
| `uv run ruff format --check .` | 0 |
| `uv run mypy` | 0 (41 files) |
| `uv run pytest -q` | 0 (182 passed, 1 skipped) |
| `uv build` | 0 (`companion_bench-0.1.0` sdist+wheel) |
| `companion-bench validate manifests/{smoke,full,heldout}.yaml` | 0 / 0 / 0 (8 / 150 / 36 tasks) |
| `companion-bench run --model mock/empathetic-v1` (smoke) + `score` + `report` | 0 (overall 1.000, 8/8) |
| second seeded smoke run + `score` → determinism diff | identical (modulo run_id/ts) |
| `companion-bench run --model-set mock-profiles` + `score --bootstrap` + `report` | 0 (empathetic 1.000 > silent ~0.63 (4/8) > intrusive ~0.44 (1/8)) |
| secret shape-scan over tracked files | clean |

Raw logs are in the session scratchpad (`evidence/00–07`), not committed. Runs live under `runs/`
(gitignored); nothing from `runs/` was staged.

## Appendix B — statistics detail

Recomputed with stdlib-only Python from committed samples under `docs/samples/`:

1. **Internal consistency:** max |recomputed overall − stored overall| = 5.33×10⁻⁷ across 40
   model×split files; all `n_passed` recounts match.
2. **Correlations:** public150↔held36 = 0.9674/0.9394; fullsuite60↔held36 = 0.8477/0.7212;
   fullsuite60↔held12 = 0.8584 (Pearson) / **0.6121** (Spearman, vs published 0.573).
3. **CI separability (published widths):** public 1/9 adjacent, 32/45 all-pairs disjoint; held-out
   0/9 adjacent, 20/45 disjoint.
4. **Cluster re-bootstrap (per-task means, 5000, seed 42):** mean width ratio vs published =
   **1.77× (public)**, **1.69× (held-out)** [INFERENCE].
5. **Cost / flags:** public Σcost = $2.5474, grand-mean overall 0.6970; held-out Σcost = $0.5948,
   grand-mean 0.7013. Dominant flag: `missed_emotional_validation` (5652 public / 1351 held-out);
   `unparseable_output` 1099 / 280; `unsafe_overreach` 8 / 0.
6. **Per-family cross-split (Pearson/Spearman):** safety 0.956/0.964, timing 0.916/0.939,
   adaptation 0.926/0.600, empathy 0.918/0.697, initiative 0.606/0.418, abstention 0.461/0.588.
7. **Task scan (186 tasks):** timing window ≡ intervene set in 186/186; decisions 149/65/49;
   difficulty 58/83/45; split public/hidden 150/36; source_type synthetic 186/186; 37 keyword
   echoes; top-level `positive_signals` empty in all 186; 8 permission probes; 88/186 with safety
   boundaries.

## Appendix C — REQUIRES RUN register (not executed; live/cost)

- Live per-model overall scores, latency, and the 61/33 transient-failure counts in the samples —
  reproducing them needs live OpenRouter calls (cost + `COMPANIONBENCH_LIVE=1`). НЕ verified here by
  design.
- Whether real models exhibit the always-wait / self-declared-style gaming vectors in practice
  (demonstrated only with the offline mock).
- Online model-set verification (`models validate --online`) and OpenRouter pricing sync.
