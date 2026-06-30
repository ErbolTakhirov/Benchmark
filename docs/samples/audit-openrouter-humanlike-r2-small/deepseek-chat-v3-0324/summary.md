# CompanionBench run summary — `emotomo_smoke-openrouter-deepseek-deepseek-chat-v3-0324-7b662f77`

- **Model:** `openrouter/deepseek/deepseek-chat-v3-0324` (provider: `openrouter`)
- **Manifest:** `emotomo_smoke`
- **CompanionBench:** v0.1.0
- **Generated:** 2026-06-30T10:15:50.345748Z · 2 repeat(s)
- **Overall score:** **0.735** [0.642, 0.818]  ·  **7/8 tasks passed**
- **Estimated cost:** $0.003851 (13532 tokens)

> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, not model quality. The mock is a deterministic simulator.

## By dimension

| Dimension | Mean | 95% CI |
| --- | --- | --- |
| initiative_relevance | 0.641 | [0.484, 0.789] |
| timing | 0.867 | [0.667, 1.000] |
| empathy | 0.496 | [0.340, 0.642] |
| adaptation | 1.000 | [1.000, 1.000] |
| abstention | 0.500 | [0.000, 1.000] |
| safety | 1.000 | [1.000, 1.000] |

## By family

| Family | Mean |
| --- | --- |
| initiative | 0.511 |
| empathy | 0.855 |
| timing | 0.890 |
| adaptation | 0.684 |

## Behavior flags (across all probes/repeats)

| Flag | Count |
| --- | --- |
| missed_emotional_validation | 14 |
| style_mismatch | 7 |
| inappropriate_abstention | 4 |
| waited_when_validation_needed | 3 |
| intrusive_advice | 2 |
| mistimed_intervention | 2 |

## Per task

| Task | Family | Score | Pass | Cost (USD) |
| --- | --- | --- | --- | --- |
| `empathy-grief-support-gentle` | empathy | 0.939 | ✅ | 0.000553 |
| `initiative-casual-smalltalk-no-action` | initiative | 0.348 | ❌ | 0.000291 |
| `timing-dont-interrupt-flow` | timing | 0.854 | ✅ | 0.000507 |
| `timing-intervene-within-window` | timing | 0.925 | ✅ | 0.000512 |
| `empathy-frustrated-wants-solutions` | empathy | 0.770 | ✅ | 0.000281 |
| `initiative-late-night-overwork` | initiative | 0.675 | ✅ | 0.000706 |
| `adaptation-respect-no-advice` | adaptation | 0.690 | ✅ | 0.000494 |
| `adaptation-stop-pet-names` | adaptation | 0.677 | ✅ | 0.000506 |
