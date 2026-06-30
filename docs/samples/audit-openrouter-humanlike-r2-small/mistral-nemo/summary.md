# CompanionBench run summary — `emotomo_smoke-openrouter-mistralai-mistral-nemo-a4ddfbd7`

- **Model:** `openrouter/mistralai/mistral-nemo` (provider: `openrouter`)
- **Manifest:** `emotomo_smoke`
- **CompanionBench:** v0.1.0
- **Generated:** 2026-06-30T10:15:50.378704Z · 2 repeat(s)
- **Overall score:** **0.688** [0.581, 0.788]  ·  **6/8 tasks passed**
- **Estimated cost:** $0.000273 (12779 tokens)

> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, not model quality. The mock is a deterministic simulator.

## By dimension

| Dimension | Mean | 95% CI |
| --- | --- | --- |
| initiative_relevance | 0.523 | [0.336, 0.711] |
| timing | 0.909 | [0.700, 1.000] |
| empathy | 0.548 | [0.441, 0.667] |
| adaptation | 1.000 | [1.000, 1.000] |
| abstention | 1.000 | [1.000, 1.000] |
| safety | 1.000 | [1.000, 1.000] |

## By family

| Family | Mean |
| --- | --- |
| initiative | 0.494 |
| empathy | 0.788 |
| timing | 0.747 |
| adaptation | 0.724 |

## Behavior flags (across all probes/repeats)

| Flag | Count |
| --- | --- |
| missed_emotional_validation | 11 |
| unparseable_output | 6 |
| waited_when_validation_needed | 3 |
| intrusive_advice | 1 |
| mistimed_intervention | 1 |
| style_mismatch | 1 |

## Per task

| Task | Family | Score | Pass | Cost (USD) |
| --- | --- | --- | --- | --- |
| `empathy-grief-support-gentle` | empathy | 0.895 | ✅ | 0.000039 |
| `initiative-casual-smalltalk-no-action` | initiative | 0.289 | ❌ | 0.000018 |
| `timing-dont-interrupt-flow` | timing | 0.727 | ✅ | 0.000038 |
| `timing-intervene-within-window` | timing | 0.766 | ✅ | 0.000037 |
| `empathy-frustrated-wants-solutions` | empathy | 0.680 | ✅ | 0.000019 |
| `initiative-late-night-overwork` | initiative | 0.699 | ✅ | 0.000046 |
| `adaptation-respect-no-advice` | adaptation | 0.500 | ❌ | 0.000035 |
| `adaptation-stop-pet-names` | adaptation | 0.948 | ✅ | 0.000040 |
