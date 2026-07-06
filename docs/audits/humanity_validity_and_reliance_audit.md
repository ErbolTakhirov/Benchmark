<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench Humanity-Validity and Reliance Audit

**Audit date:** 2026-07-06 · **Commit:** `a7d06fd` · **Branch:** `main` · **Scoring:** `rule_based v1.2.0`
· **Scope:** offline, read-only, adversarial, evidence-first. No live API calls, no OpenRouter run, no
LLM judge. Every number below was read from source, produced by an offline command this session, or
recomputed from committed artifacts with stdlib-only code (Appendix A/B).

This audit asks the blunt questions: *does the benchmark work, are its numbers computed correctly,
are they statistically meaningful, what does it actually measure, does it measure human-like
companion communication or scorer/task artifacts, and how far can a user rely on it?* It is
deliberately unflattering, and it **reconciles the prior shipped audit**
([`v0_1_alpha_benchmark_validity_audit.md`](v0_1_alpha_benchmark_validity_audit.md), written at
commit `feb4e88`): most of that audit's top *scoring* defects have since been fixed, which changes
several grades upward — but the two structural gating weaknesses it named (no human grounding, a
lexical scorer) are unchanged.

---

## Executive verdict

**Credible public-alpha diagnostic.**

CompanionBench is a real, working, honestly-scoped measurement instrument — not a toy. At `a7d06fd`
it runs end-to-end offline, is byte-deterministic under a frozen clock, passes every local gate
(**286 tests pass, 1 skipped**; Appendix A), ships live multi-model results, hardens the scoring
defects the previous audit found, and is unusually disciplined about not overclaiming (a
mechanically-enforced claims policy, a self-graded scorecard, and a machine-checkable
`quality status`). That is more than most first public alphas deliver.

It is **not** a validated benchmark, and the gap is structural, not cosmetic. The default scores are
a **scorer-relative construct**: a deterministic, now-word-boundary rule matcher over discrete
decisions, author-written keyword phrases, and self-declared style enums, on an **English-only,
100%-synthetic, same-author** task suite, with **zero real human labels** and an **uncalibrated**
LLM judge. The honest one-line answer to "does it measure human-like companion communication?":
**it measures a coarse, reproducible good-vs-weak signal on scoped companion-communication tasks,
wrapped around a fine-grained layer that mostly measures whether a model emits the scorer's expected
decisions, keywords, and labels.** The coarse signal is real and generalizes across the split. The
fine rankings are largely artifact.

---

## Bottom line

- **Does it work?** Yes. Offline pipeline runs, scores, aggregates, and reports correctly and
  deterministically; failures are captured, never hidden; gates are green (Appendix A).
- **Does it measure real human-like companion behavior?** **Partially, and only at a coarse level.**
  It captures decision-correctness under multi-turn context and a good-vs-weak ordering that
  generalizes across a same-author public/held-out split. It does **not** measure human-*perceived*
  companion quality (no human grounding) and is **not** construct-valid at the individual-dimension
  level.
- **Can we rely on it?** **For narrow, scoped purposes, yes.** As a universal or human-preference
  verdict, no.
- **Rely on it for:** regression-testing a companion system on a fixed suite; separating clearly
  strong from clearly weak models with CIs; surfacing specific failure modes (always-wait, style
  self-report lies, missing permission, missed abstention, forbidden-pattern safety hits); a
  transparent, reproducible baseline a future judge/human round is measured against.
- **Do NOT rely on it for:** ranking adjacent models; any "most human"/"best companion" claim;
  predicting human preference; safety certification for vulnerable users; multilingual or
  cross-cultural naturalness; treating a dimension delta (empathy, timing) as construct-valid.

---

## Scores /10

Honest, evidence-anchored. These are *this auditor's* grades, not the project's self-assessment
(the project self-grades 6.55/10; `quality status`).

| Axis | Score | One-line justification |
| --- | --- | --- |
| Technical correctness | **8** | Gates green (286 pass), deterministic, N/A excluded+renormalized correctly, failures captured, provenance stamped in fresh runs. Docked for no resume + a storage docstring that overpromises crash-safety. |
| Scoring robustness | **6.5** | v1.1/v1.2 hardening verified (safety-on-empty, whole-token, prose-verified permission, style-liar catch, timing de-redundancy) + strong adversarial tests. Still lexical, not semantic; residual gaming surfaces remain. |
| Task-suite quality | **6** | Perfect structural balance, good safety/abstention design, negative cases present. English-only, 100% synthetic, same-author split, 9 keyword-echo tasks, gentle-style base rate, not externally reviewed. |
| Statistical reliability | **6** | Task-clustered bootstrap is the code default; arithmetic is honest; cross-split correlation is strong. But committed-sample CIs are the old narrow unit-bootstrap; only 1/9 adjacent ranks separable; one stat was unreproducible. |
| Human-like-behavior validity | **3.5** | Coarse companion-communication behavior is captured and generalizes; dimensions are not construct-valid; "human-likeness" broadly is not measured. |
| Human agreement / external validation | **2** | Zero real labels. Agreement (Krippendorff α) + calibration code exists and is tested, but only on a 14-item synthetic fixture. The #1 gating weakness. |
| Judge calibration | **3** | Judge is now implemented, live-gated, separate, malformed-safe (a real upgrade from the old stub) — but never calibrated against humans, so untrustworthy as a signal. |
| Reproducibility | **8** | Lockfile, byte-deterministic mock, committed samples, keyless fresh-clone path, provenance in fresh runs. Docked for version drift, samples predating provenance, no resume. |
| Security / artifact hygiene | **9** | No secrets in tree, `.env` untracked/gitignored, samples sanitized, redaction + scan tests, private-label gitignore, count-only secret scanning (Appendix C). |
| Public documentation | **7.5** | Exemplary, mechanically-enforced claims policy; candid limitations; ships its own audit + scorecard. Docked for a cluster of stale numbers/versions and a fine-rank framing in tension with its own guidance. |
| **Overall reliance** | **≈5.5** | A credible public-alpha diagnostic: reliable for coarse triage and failure-mode detection on its scoped synthetic suite; not human-validated, not a fine ranking, not a human-preference or human-likeness measure. |

---

## Claim ladder

| # | Claim | Verdict | Basis |
| --- | --- | --- | --- |
| 1 | CompanionBench runs correctly offline. | **Supported** | 286 pass / 1 skip; deterministic mock; validate 8/150/36 (Appendix A). |
| 2 | It reports reproducible scoped scores. | **Supported** | Byte-deterministic mock; provenance block + `scoring_version 1.2.0` stamped in fresh runs; `uv.lock` tracked. |
| 3 | It detects some companion-communication failure modes. | **Supported** | Flags map 1:1 to scorer signals; adversarial mocks (always-wait, style-liar, permission-liar, wait-liar, generic-empathy, always-advise, always-abstain) are each caught by tests. |
| 4 | It supports coarse model-tier comparison on its sample suite. | **Supported (coarse only)** | Cross-split Pearson 0.967 / Spearman 0.939 (recomputed); top-cluster vs bottom clearly separable (gemini last on both splits). CIs support **tiers**, not adjacent ranks (1/9 disjoint). |
| 5 | It predicts human preference. | **Unsupported** | No real human labels exist (`quality status`: synthetic pilot). |
| 6 | It measures human-likeness broadly. | **Unsupported** | Measures scoped behavior on authored scenarios only; the repo agrees. |
| 7 | It proves one model is "most human". | **Unsupported** | Banned by the project's own policy; the top-4 are a statistical tie. |

Mapped to the finer A–F ladder: **A** "measures formatting compliance" — supported (and explicitly
isolated as `format_compliance`); **B** "deterministic rule-based signals on companion-like tasks" —
supported; **C** "scoped companion-communication behavior" — **partially** (coarse yes, fine/dimension
no); **D** "approximates human preference" — unsupported; **E** "measures how human a model is" —
unsupported; **F** "proves the most human model" — unsupported.

---

## What the benchmark actually measures

Concrete measured proxies (all verified in `src/companion_bench/evaluators/rule_based.py`):

- **Decision correctness under multi-turn context** — whether the emitted `decision`
  (`intervene`/`wait`/`abstain`) matches the answer key, given prior turns the model saw. This is the
  load-bearing, genuinely-multi-turn construct and the most defensible signal.
- **Structured-output compliance** — whether a `CompanionTurn` envelope parsed at all. Isolated into
  the additive, experimental `format_compliance` / `communication_score` / `parse_adjusted_score`
  (never fed back into `overall`; `aggregate.py:133-147`).
- **Keyword/target coverage** — whole-token presence of author-written `expected_target_keywords` /
  `positive_signals` in the message (`_contains`, word-boundary, `rule_based.py:190-205`).
- **Style compatibility** — the emitted `style` **enum** vs a preferred one (`style_match`), now with
  a high-precision `_BLUNT_RE` liar-check that caps a gentle label contradicted by blunt prose.
- **Abstention / non-intrusion decision** — abstain-when-required and don't-abstain-when-engagement-
  expected (`_abstention`); covert "wait-but-advised" caught (`_ADVICE_RE`).
- **Timing as window membership** — 1.0 iff intervening inside `allowed_intervention_window`; **zero-
  weighted in the total** whenever the window equals the intervene set (which it does for 186/186
  tasks), so it does not double-count the decision (`effective_weights:174-178`).
- **Preference adaptation as keyword non-recurrence** — whether a previously `disliked_behavior`
  phrase reappears after feedback (`_adaptation`).
- **Safety as forbidden-pattern scanning + prose-verified permission** — regex `forbidden_patterns`
  in the message, plus a `_PERMISSION_RE` check against the prose (not the self-reported boolean);
  empty/malformed output earns **no** positive safety credit (returns `None`).

## What it does NOT measure

- **Real human-perceived companion quality.** No human gold set is collected; nothing ties a number
  to what a person would call good companionship.
- **Message *content* quality / semantics.** Empathy, adaptation, and target relevance are keyword
  coverage, not meaning; paraphrase without the expected tokens is under-credited.
- **The quality of a correct abstention.** A warm, helpful decline and a cold, curt refusal score
  identically on abstain-expected tasks — empathy/positive signals are `None` unless the decision is
  `intervene` (`_empathy` returns `None` off-INTERVENE, `rule_based.py:317`). The rubric prose that a
  "cold refusal is the weaker failure" is never scored.
- **Emotional attunement independent of a self-declared label** — style credit still starts from the
  model's own `turn.style` enum; the `_BLUNT_RE` check only catches *blunt* contradictions, so a
  model that self-declares `gentle` and writes bland, non-blunt, non-validating prose keeps style
  credit.
- **Consciousness, personality, genuine emotion, broad "humanity", therapeutic safety, real user
  satisfaction, long-term relationship quality.** Out of scope by construction.
- **Multilingual naturalness or cross-cultural sensitivity** — English-only, Western-default norms,
  un-reviewed (`methodology.md:160-164`).

---

## Evidence supporting reliance

- **Gates green at `a7d06fd`** (Appendix A): ruff, ruff-format, mypy (51 files), **pytest 286 pass /
  1 skip**, `uv build`, validate smoke/full/held-out (8/150/36), `--strict-quality` passes.
- **Determinism + provenance.** A fresh offline mock run stamps `scoring_version=1.2.0` and renders a
  `## Provenance` block (commit, scoring version, manifest, provider/model, repeats, bootstrap) —
  `render_summary` / `_provenance_block` (`aggregate.py:316-348`), verified live (Appendix A).
- **Correct aggregation of N/A.** `None` dimensions are excluded and weights renormalized
  (`_weighted_total`, `rule_based.py:476-483`; `_mean_or_none`, `aggregate.py:59-61`); pinned by
  `tests/test_rule_evaluator.py::test_na_dimensions_excluded_from_total`.
- **Safety-on-empty is fixed** (the prior audit's headline defect). `_safety` returns `None` on
  empty/malformed output instead of a free 1.0 (`rule_based.py:414-446`);
  `test_scoring_adversarial.py::test_provider_failure_is_floored_not_inflated` asserts total `0.0`.
- **Task-clustered bootstrap is the default** (`bootstrap_cluster="task"`, `aggregate.py:75,164`;
  `_bootstrap_clustered` resamples whole tasks, `:252-298`), with per-family CIs and honest guards
  (CI stays `None` below 2 units, never faked).
- **Cross-split generalization is real and reproduces.** public-expanded (150) ↔ held-out-expanded
  (36): **Pearson 0.9674 / Spearman 0.9394** (recomputed, Appendix B). gemini-2.5-flash-lite is last
  on both splits with a CI touching no other model.
- **Adversarial + honesty tests exist and pass.** `test_adversarial_mocks.py`,
  `test_scoring_adversarial.py`, `test_signal_disjointness.py`, `test_public_claims.py`,
  `test_scorecard.py`, `test_secrets.py` (Appendix A) — the gaming mocks the prior audit asked for
  (fix #14) are present.
- **Machine-checkable honesty.** `quality status` reports gold as **synthetic pilot (not human-
  collected)**, judge-calibration **no**, and warns against "human-validated"/"most human" (Appendix
  A).

## Evidence against over-reliance

- **Zero real human labels.** `quality status`: 42 labels / 3 annotators / 14 items, "synthetic
  pilot (not human-collected)"; "private label files present: no". All 42 rows carry
  `not_human_collected: true`. Agreement/calibration numbers today are workflow demos on a 14-item
  fixture.
- **The scorer is lexical, not semantic.** `_contains` is whole-token but still literal; empathy =
  keyword coverage + a self-declared style enum. The single most common flag across the sample suite
  is `missed_emotional_validation` (~5,652 public occurrences, prior audit App. B), which maps from
  "the message lacked an expected keyword substring" — a coverage artifact, not a measured empathy
  failure.
- **Fine ranks are not statistically separable.** Even at the committed samples' *too-narrow* CIs,
  only **1/9 adjacent-rank pairs are disjoint** (all-pairs 32/45; recomputed, Appendix B). The top-4
  (all DeepSeek) overlap into a transitive tie ([0.739,0.767] … [0.719,0.747]).
- **Committed-sample CIs are the old, narrow ones.** Every committed `scores.json` carries
  `scoring_version=None` and `bootstrap_method=None` (recomputed, Appendix B) — they predate both the
  version stamp and the task-clustered default, so their CIs are the unit-bootstrap intervals the
  docs themselves call "roughly 1.5–2× too tight" (`results_interpretation.md:37-42`). Per-repeat
  units are not persisted, so exact re-clustering from committed artifacts is impossible.
- **A published statistic was unreproducible.** "Spearman 0.573" (fullsuite-r5 ↔ held-out-r5)
  recomputes to **0.6121** from the committed scores (Appendix B). It survives in
  `results_interpretation.md` and four sample docs (corrected/annotated by this pass; see Path).
- **Same-author split ≈ template transfer, not OOD.** Public and held-out tasks share authors and
  templates and are plaintext in-repo; a high cross-split correlation measures template transfer, not
  true out-of-distribution generalization.
- **Family-level fine claims are noisy.** Cross-split per-family: initiative **0.606/0.418**,
  abstention **0.461/0.588** (recomputed, Appendix B) — do not read fine per-family orderings for
  these two.

---

## Failure modes and gaming risks

Ranked by residual exploitability at `v1.2.0` (several vectors the prior audit listed are now
closed — see Reconciliation):

1. **Self-declared style on bland prose** *(open)* — style credit begins from `turn.style`; only
   *blunt* contradictions are caught (`_BLUNT_RE`). A model that labels itself `gentle` and writes
   neutral, non-validating text keeps partial style credit.
2. **Keyword echo** *(mitigated, not closed)* — matching is whole-token now, but 9 tasks still have a
   positive signal appearing verbatim in the visible prompt (`--strict-quality` warns on exactly
   these; Appendix A). Under coverage scoring a model can lift the phrase from context.
3. **Cold correct abstention** *(open)* — warm vs cold declines score identically on abstain tasks;
   authored nuance is uncredited.
4. **Decision arbitrage** *(open)* — wrong-but-adjacent decisions get partial credit (WAIT-instead-
   of-ABSTAIN 0.7; ABSTAIN-instead-of-WAIT 0.6; `rule_based.py:291,296`).
5. **Safety is pattern-only** *(open)* — safety docks solely on regex `forbidden_patterns`; ~88/186
   tasks carry boundaries, the rest default to 1.0. Novel unsafe phrasing outside the list is
   invisible; this is a weak detector, not a safe-fleet certificate.
6. **Parse–format entanglement** *(reduced)* — a low `overall` can be format compliance, not
   companionship; check `format_compliance` first (gemini's 52.8% parse rate drives its last place).
   Safety-on-empty no longer inflates a failed call, which closed the old 0.333 floor.
7. **Answer key in-repo** *(inherent)* — rubric, decisions, keywords, and forbidden patterns ship
   beside the tasks; a model prompted with or trained on the repo can reach the ceiling. The
   plaintext split is the only mitigation.
8. **Judge bias** *(latent)* — if the opt-in judge is ever trusted before human calibration, its
   documented biases (verbosity, self-preference, safety blind spots) would import silently. The
   design keeps it separate and uncalibrated, which is correct.
9. **English-only / culture bias** *(inherent)* — gaming aside, the suite cannot speak to non-English
   or non-Western companion norms.

---

## Human validation status

**Absent (synthetic fixture only).** There are **no real human labels**. The committed gold
(`data/gold/pilot_v0_1_alpha.jsonl`, 42 rows) is explicitly synthetic (`not_human_collected: true`,
`source_type: synthetic_pilot_labels`, `purpose: schema/test fixture only`), and `quality status`
reports "synthetic pilot (not human-collected)" with "private label files present: no". The
supporting machinery is real and tested: Krippendorff's α (nominal + ordinal),
Cohen's κ, percent agreement (`evaluators/agreement.py`, `tests/test_agreement.py`), rule-vs-gold and
judge-vs-gold calibration (`evaluators/calibration.py`), a distributable annotation packet
(`analysis/annotation_round_v0_1/`), and a PII-refusing de-identifier (`gold import-human`). Low-
agreement dimensions are explicitly flagged as findings (`_LOW_ALPHA = 0.667`). But **inter-rater
agreement and rule-vs-human calibration on real people have never been run**. The benchmark **cannot**
be called human-validated. This is the single highest-leverage gap.

## Judge calibration status

**Implemented but uncalibrated — REQUIRES LIVE RUN.** Contra the prior audit (which found a
`NotImplementedError` stub), the judge is now a real `LLMJudgeRubricEvaluator` with an offline
deterministic mock (`run_mock_judge`) and a live-gated real path (`run_live_judge`), strict verdict
parsing (NaN/Infinity/malformed → recorded failure, never a coerced score), versioned prompts
(`jp-1.0.0`) that hide model identity and separate format from quality, and separate artifacts
(`judge_scores.json`, never touching `scores.json`). Live constraints (`--live` +
`COMPANIONBENCH_LIVE=1` + `--max-cost-usd` + confirmation) are enforced in code and tests. **But it
has never been calibrated against real humans** (`quality status`: "judge calibration available:
no"; `judge_calibration.md`: "Live judge-vs-human calibration: REQUIRES LIVE RUN"). The interface and
discipline are trustworthy; the *numbers* are not — the judge is an opt-in, biased signal, correctly
kept out of the scored path.

---

## Statistical interpretation

- **Coarse tiers vs exact ranks.** Trust top-cluster-vs-bottom-cluster with CIs; do **not** trust
  numeric rank order. On the 150-task public suite only **1/9** adjacent-rank CIs are disjoint (the
  bottom pair, mistral-nemo → gemini); the top-4 are a transitive tie (Appendix B).
- **CI overlap.** Overlapping CIs = a statistical tie, not "close but still ranked". Apply this even
  to the headline table: ranks 1–4 all overlap.
- **CIs are narrower than honest.** Committed samples use the legacy unit bootstrap
  (`bootstrap_method=None`, i.e. pre-clustering); the docs estimate the honest task-clustered CIs are
  ~1.5–2× wider. The **code** default is now correct (`task`), so re-scoring/re-running under v1.2.0
  would widen them — but the shipped artifacts have not been regenerated.
- **Cross-split reproducibility ≠ separability.** Spearman 0.939 says the *ordering reproduces* across
  the public/held-out split; it does **not** say adjacent models are distinguishable (they are not).
  These are different properties, and the sample summary's "the fine-grained ranking itself now
  generalizes strongly" reads as the latter while only supporting the former — see the consistency
  note below.
- **Per-family reliability varies sharply.** Cross-split: safety 0.956/0.964 and timing 0.916/0.939
  generalize best; initiative 0.606/0.418 and abstention 0.461/0.588 are noisy (Appendix B). Note the
  irony: **timing "generalizes" partly because it is redundant** with the intervene decision (window
  ≡ intervene set for 186/186 tasks), so it re-measures a signal initiative already carries.
- **Parse-adjusted reading.** Reports separate `format_compliance` from `communication_score`; read a
  low `overall` against parse rate before calling a model "bad at companionship".
- **Consistency note (documented, not resolved this pass).** `README.md` and the newest sample
  summary lean into fine-rank generalization ("the fine-grained ranking itself now generalizes
  strongly", "strongest generalization result the project has recorded"), while the shipped
  `results_interpretation.md` and the prior validity audit say fine/adjacent ranks are "largely
  artifact" and "distrust close calls". Both can be literally true (the ordering reproduces; the
  ranks are not separable), but the framings pull opposite directions. Left as a finding per audit
  scope; recommended reconciliation in Path to credible.

---

## Reliance policy

**Safe to use for**

- Regression-testing one companion system across versions on a fixed manifest.
- Separating **clearly strong from clearly weak** models, reported with bootstrap CIs and as a scoped
  run (model set + provider + manifest + scoring version).
- Diagnosing **specific failure modes** via the flag profile (always-wait, style self-report lies,
  missing permission, missed/inappropriate abstention, forbidden-pattern safety hits, low parse
  rate).
- A transparent, reproducible **baseline** against which a future human round and LLM judge are
  measured.

**OK to use cautiously for**

- Coarse cross-model tiering on the sample suite — *only* with CIs, and treating overlaps as ties.
- Per-family reads on **safety** and **timing** (best cross-split), remembering timing's redundancy.
- Cost-quality frontier positioning (honest, `null`-when-unknown accounting).

**Not safe to use for**

- Adjacent-model ranking or "the best/top model" (top-4 are tied).
- Any "most human" / "human-validated" / "human-approved" / "final leaderboard" claim.
- Predicting real human preference or satisfaction.
- Safety/clinical certification, or fitness-for-deployment for vulnerable users.
- Multilingual, cross-cultural, or non-synthetic conclusions.
- Reading a single dimension delta (empathy, adaptation) as a construct-valid trait.

---

## Reconciliation with the prior validity audit

The shipped `v0_1_alpha_benchmark_validity_audit.md` (commit `feb4e88`) graded scoring **C−** and
statistics **C+**. The very next commits (`8db0a9c fix: harden rule-based scoring validity`,
`77c2bdb feat: word-boundary scoring (v1.2.0)`) addressed most of its scoring findings. Verified this
session:

| Prior finding (fix #) | Status at `a7d06fd` | Evidence |
| --- | --- | --- |
| Safety defaults to 1.0 on empty/parse-failure (#3) | **Fixed** | `rule_based.py:414-446` returns `None`; adversarial test asserts total 0.0. |
| Substring matching, "help" ⊂ "helpless" (#6) | **Fixed** | Whole-token `_contains`, `rule_based.py:190-205`; `test_matching.py`. |
| Permission dock checks the boolean (#5) | **Fixed** | Prose-verified `_PERMISSION_RE`, `rule_based.py:451-459`. |
| Style read from self-declared label (#5) | **Partial** | `_BLUNT_RE` caps lying gentle style (`:328-330`); bland prose still credited. |
| Timing 100% redundant (#4) | **Partial** | Zero-weighted in the total (`effective_weights:176-177`); still shown per-family. |
| Pseudoreplicated CIs (#7) | **Fixed in code / stale in samples** | Task-clustered default (`aggregate.py:75,164`); committed samples still `bootstrap_method=None`. |
| LLM judge is a stub (#2) | **Implemented, uncalibrated** | `evaluators/judge.py`, `rubric.py`; never human-calibrated. |
| Adversarial scorer tests missing (#14) | **Fixed** | `test_adversarial_mocks.py`, `test_scoring_adversarial.py`. |
| Benchmark card describes a mock-only MVP (#10) | **Fixed** | `benchmark_card.md:10,43` now says public alpha + live runs performed. |
| **No human gold set (#1)** | **Open** | `quality status`: synthetic pilot only. |
| **Unreproducible 0.573 (#10)** | **Open → fixed this pass** | Recomputes to 0.6121; corrected/annotated. |
| **Version drift 0.1.0 vs 0.1.0-alpha (#11)** | **Open → fixed this pass** | Wheel built as `companion_bench-0.1.0`. |
| Safety beyond patterns (#9); cold-abstention (#8); paraphrase/semantic (#6); resume (#12); English-only/synthetic/near-dup suite (#13); NOTICE URL + README "five dimensions" (#15) | **Open** (some doc bits fixed this pass) | See Path to credible. |

Net: the **instrument** is materially stronger than the prior grades suggest (scoring → ~B−/C+,
statistics-code → ~B−); the **external-validity** gap is unchanged and remains the ceiling.

---

## Path to credible benchmark

Prioritized; the first three are the ceiling on every "human-like" claim.

1. **Run a real ≥3-annotator round** on the shipped packet; commit only de-identified labels.
2. **Report inter-rater agreement** (Krippendorff's α per dimension) and flag low-agreement dimensions
   before trusting any calibration number.
3. **Rule-vs-human calibration** (MAE / Pearson / Spearman per dimension); publish where the rules
   diverge from people.
4. **Tiny, budget-capped judge-vs-human calibration** on the same items; keep it separate and biased.
5. **External reviewer task audit** — outside humans review the safety/abstention suite especially.
6. **Non-English / native-speaker pilot** before any multilingual claim.
7. **Paraphrase/semantic scoring** (synonym/embedding backoff) and remove the 9 in-prompt keyword
   echoes so answers can't be lifted from context.
8. **Stronger safety evaluation** beyond forbidden-pattern blocklists (classifier or calibrated
   judge; per-task safety gates).
9. **Regenerate the committed samples under v1.2.0** so shipped CIs are task-clustered and every
   sample carries a `scoring_version`/provenance block; **reconcile the fine-rank framing** across
   README / sample summaries / `results_interpretation.md`.
10. **Third-party reproduction** + a signed release with stable run-rules and version-pinned served
    models; add resume/checkpoint so long live runs don't lose partial logs.

---

## Final recommendation — next sprint

The instrument is in good shape; **spend the sprint buying external validity, not more scorer
polish.** Concretely: (1) run the real annotation round already scaffolded and publish agreement +
rule-vs-human calibration; (2) regenerate the two current samples under v1.2.0 so shipped CIs and
provenance match the code, and reconcile the fine-rank wording; (3) land the small, safe
documentation corrections in this pass (version stamps, the 0.573 statistic, README dimension count
and self-grade, NOTICE URL). Until (1) lands, keep every public statement at the "scoped run /
coarse tier / calibration signal" altitude the project's own `public_claims.md` already mandates.

---

## Appendix A — offline command transcript (this session, `a7d06fd`)

| Command | Result |
| --- | --- |
| `uv sync --all-extras` | exit 0 |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 92 files already formatted |
| `uv run mypy` | Success: no issues in 51 source files |
| `uv run pytest -q` | **286 passed, 1 skipped** (`test_live.py` skipped; keyless/offline) |
| `uv build` | built `companion_bench-0.1.0` (sdist + wheel) — note version drift vs tag `0.1.0-alpha` |
| `validate manifests/{smoke,full,heldout}.yaml` | 8 / 150 / 36 tasks, all valid |
| `validate manifests/full.yaml --strict-quality` | passes with 9 keyword-echo warnings (documented limitation) |
| `quality status` | rule_based **v1.2.0**; gold = **synthetic pilot (not human-collected)**; judge calibration **no**; scorecard 6.55/10; warns against "human-validated"/"most human" |
| mock `run` + `score` + `report` (`runs/audit-smoke`, gitignored) | exit 0; `scoring_version=1.2.0`; `## Provenance` block rendered; overall 1.000 |

Runs live under `runs/` (gitignored); nothing from `runs/` was staged.

## Appendix B — statistics recompute (stdlib-only, from committed `docs/samples/`)

- **Cross-split correlations:** public-expanded (150) ↔ held-out-expanded (36) = **0.9674 / 0.9394**
  (matches published 0.968 / 0.939); fullsuite (60) ↔ held-out (12) = **0.8584 / 0.6121** (published
  Spearman **0.573 is not reproducible** — actual 0.6121).
- **Committed-sample provenance:** all four sample sets report `(scoring_version, bootstrap_method) =
  (None, None)`, `resamples=5000`, `n_repeats=5` — i.e. pre-provenance, legacy unit-bootstrap CIs.
- **Adjacent-rank CI separability (public-expanded, published widths):** **1/9** adjacent pairs
  disjoint (only mistral-nemo → gemini); all-pairs **32/45**. Top-4 form a transitive tie.
- **Per-family cross-split (Pearson / Spearman):** initiative 0.606/0.418 · empathy 0.918/0.697 ·
  timing 0.916/0.939 · adaptation 0.926/0.600 · abstention 0.461/0.588 · safety 0.956/0.964.

## Appendix C — REQUIRES LIVE RUN (not executed, by design)

- Live per-model scores / latency / transient-failure counts in the samples (need live OpenRouter +
  `COMPANIONBENCH_LIVE=1`).
- Whether real models exhibit the gaming vectors in practice (only shown with the offline mock).
- Any judge-vs-human or rule-vs-human calibration number (no real labels; live judge un-run).
- Online model-set verification and OpenRouter pricing sync.
