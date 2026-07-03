<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench Quality Scorecard

A rigorous, 10-category rubric for judging how close CompanionBench is to a **genuinely
high-quality open-source benchmark** — and an honest self-grade against it.

> **This is a quality roadmap, not marketing.** The scores below are the project's own
> assessment, not an external grade. A high number is a claim we must be able to defend with
> evidence; where the evidence is thin, the number is low **on purpose**. The machine-readable
> copy lives at [`benchmark_quality_scorecard.json`](benchmark_quality_scorecard.json) (read by
> `companion-bench quality status`), and the evidence-by-evidence current-state audit is in
> [`current_quality_against_scorecard.md`](current_quality_against_scorecard.md).

## Scoring bands (apply to every category)

| Band | Meaning |
| --- | --- |
| **0–3** | **Weak.** Missing, broken, or unsupported by evidence. |
| **4–6** | **Usable MVP.** Works and is honest, but a knowledgeable reviewer would not yet trust the numbers as validated. |
| **7–8** | **Public-alpha / credible.** Defensible for an alpha: real evidence, honest limitations, no known correctness holes. |
| **9** | **Strong v0.1-ready.** Externally checkable, robust, and hard to fault for a first stable release. |
| **10** | **Mature benchmark-level.** Independently reproduced, human-validated, stress-tested across generations, community-reviewed. |

**A 10 requires extraordinary evidence** — independent reproduction, published human agreement,
and external review. No category should reach 10 on internal work alone.

## Penalty rules (these cap the score regardless of other strengths)

- **No real human validation** caps *Human agreement / external validation* at **3**.
- **Synthetic-only gold labels** presented as validation caps *Methodology* at **7**.
- **Demonstrable scorer artifacts** (substring gaming, self-report trust, parse asymmetry) cap
  *Scoring validity* at **6** until closed and regression-tested.
- **Parse/format entanglement** left un-disentangled in reports caps *Scoring validity* at **6**.
- **No non-English / cross-cultural coverage** caps *Task suite quality* at **7**.
- **No external reviewers** caps *Task suite quality* and *Methodology* at **8**.
- **No stable CI** (while GitHub Actions stay disabled) caps *Reproducibility* at **8**.

---

## The ten categories

For each: what a **7**, a **9**, and a **10** look like, plus the specific ways to lose points.

### 1. Methodology validity
Is the objective narrow, honest, and measured by a design that actually tests it?
- **7:** clear scoped objective, strong public-claims policy, honest hedging; docs match the shipped state.
- **9:** the research hypothesis is operationalized and at least partially tested; every headline statistic reproduces.
- **10:** independent methodological review; the construct is validated against an external criterion.
- **Lose points for:** stale docs that contradict the shipped state, unreproducible statistics, or any drift toward "most human" framing.

### 2. Task suite quality
Are the tasks realistic, balanced, discriminating, and free of leakage?
- **7:** balanced families, held-out split, licensing, structural invariants enforced.
- **9:** difficulty is calibrated and discriminates models; signals resist keyword gaming; some external authoring review.
- **10:** multiple suite generations, non-English / cross-cultural coverage, independent task review.
- **Lose points for:** synthetic-only English-only scenarios, keyword-echo signals, a redundant dimension, a gentle-style monoculture.

### 3. Scoring validity
Do the scores measure the behavior, not an artifact of the scorer?
- **7:** deterministic, transparent, with the worst gaming vectors closed and regression-tested.
- **9:** paraphrase-robust matching, parse/format disentangled from content, adversarial mocks pinned.
- **10:** scores correlate with a human criterion within a stated tolerance.
- **Lose points for:** substring matching without word boundaries, trusting self-reported labels, parse-failure asymmetry, always-wait/abstain refuges.

### 4. Human agreement / external validation
Do real people agree the "good" answers are good?
- **7:** a completed real annotation round with reported inter-rater agreement above a threshold.
- **9:** multi-annotator agreement across families with rule-vs-human calibration reported.
- **10:** published, independently reproduced human study.
- **Lose points for:** **no real labels at all**, synthetic labels presented as validation, no agreement reporting, single-annotator claims.

### 5. LLM-judge calibration quality
If an LLM judge is used, is it calibrated and kept auxiliary?
- **7:** judge is opt-in, stored separately, never the source of truth, with documented bias mitigations.
- **9:** judge-vs-human calibration reported on real labels; bias/agreement quantified.
- **10:** judge calibration reproduced across judge models and shown stable.
- **Lose points for:** no live/real judge run, no calibration against humans, any judge-as-leaderboard use.

### 6. Statistical reliability
Are the numbers reported with honest uncertainty?
- **7:** repeats + bootstrap CIs, with the resampling unit matched to the data.
- **9:** task-clustered CIs by default, per-family reliability diagnostics, no overstated separability.
- **10:** power analysis; separability claims backed by pre-registered thresholds.
- **Lose points for:** pseudoreplicated CIs, unreproducible correlations, overstated tier separation.

### 7. Reproducibility
Can a stranger get the same numbers?
- **7:** green local gates, deterministic mock runs, keyless offline path, recorded provenance.
- **9:** full provenance (commit, versions, pricing), resume/checkpoint for long runs, pinned environment.
- **10:** independent third-party reproduction on record.
- **Lose points for:** version drift, missing provenance, no resume, no CI.

### 8. Security / artifact hygiene
Are secrets and PII kept out, and artifacts safe to publish?
- **7:** no secrets in tree/history, `.env` untracked, raw runs gitignored, redaction tests.
- **9:** sanitized samples, PII-refusing importers, secret-scan discipline, private data never committed.
- **10:** audited supply chain + signed releases.
- **Lose points for:** any secret/PII exposure, raw transcripts committed, unsanitized samples.

### 9. Architecture / maintainability
Is the code modular, typed, and easy to extend?
- **7:** clean layers, strict typing, injectable clock, provable adapter isolation.
- **9:** no god-modules, documented extension points, high cohesion.
- **10:** stable public API with deprecation policy.
- **Lose points for:** oversized modules, hidden coupling, docstrings that overpromise guarantees.

### 10. Open-source usability / documentation
Can a newcomer install, run, contribute, and cite it?
- **7:** README, CONTRIBUTING, SECURITY, license, CITATION, CHANGELOG, task/provider guides.
- **9:** issue templates, contributor checklists, examples, a packaged release, stable CI or a documented substitute.
- **10:** an active external contributor community.
- **Lose points for:** no packaged release, no CI, doc drift, missing contributor scaffolding.

---

## Current self-assessment (v0.1.0-alpha, 2026-07-03)

| # | Category | Score /10 |
| --- | --- | --- |
| 1 | Methodology validity | 7.0 |
| 2 | Task suite quality | 6.5 |
| 3 | Scoring validity | 6.75 |
| 4 | Human agreement / external validation | **2.5** |
| 5 | LLM-judge calibration quality | **3.5** |
| 6 | Statistical reliability | 7.0 |
| 7 | Reproducibility | 8.25 |
| 8 | Security / artifact hygiene | 9.0 |
| 9 | Architecture / maintainability | 7.5 |
| 10 | Open-source usability / documentation | 7.5 |
| | **Overall average** | **6.55 / 10** |

**Headline:** a credible public alpha whose instrument, reproducibility, and hygiene are strong,
but whose **external validity is the gating weakness** — there are no real human labels yet, and
the LLM judge has never been calibrated against people. See
[`current_quality_against_scorecard.md`](current_quality_against_scorecard.md) for the evidence,
blockers to 9/10 and 10/10, and the engineering tasks behind each number.
