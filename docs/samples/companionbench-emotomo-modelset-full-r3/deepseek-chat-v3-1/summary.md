# CompanionBench run summary — `emotomo_smoke-openrouter-deepseek-deepseek-chat-v3.1-d949487f`

- **Model:** `openrouter/deepseek/deepseek-chat-v3.1` (provider: `openrouter`)
- **Manifest:** `emotomo_smoke`
- **CompanionBench:** v0.1.0
- **Generated:** 2026-06-30T11:07:09.574261Z · 3 repeat(s)
- **Overall score:** **0.754** [0.672, 0.832]  ·  **6/8 tasks passed**
- **Estimated cost:** $0.006050 (20606 tokens)

> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, not model quality. The mock is a deterministic simulator.

## By dimension

| Dimension | Mean | 95% CI |
| --- | --- | --- |
| initiative_relevance | 0.677 | [0.526, 0.818] |
| timing | 0.864 | [0.708, 1.000] |
| empathy | 0.490 | [0.372, 0.608] |
| adaptation | 1.000 | [1.000, 1.000] |
| abstention | 0.600 | [0.000, 1.000] |
| safety | 1.000 | [1.000, 1.000] |

## By family

| Family | Mean |
| --- | --- |
| initiative | 0.539 |
| empathy | 0.835 |
| timing | 0.943 |
| adaptation | 0.700 |

## Behavior flags (across all probes/repeats)

| Flag | Count |
| --- | --- |
| missed_emotional_validation | 23 |
| style_mismatch | 12 |
| waited_when_validation_needed | 4 |
| inappropriate_abstention | 4 |
| intrusive_advice | 3 |
| mistimed_intervention | 3 |

## Per task

| Task | Family | Score | Pass | Cost (USD) |
| --- | --- | --- | --- | --- |
| `empathy-grief-support-gentle` | empathy | 0.930 | ✅ | 0.000926 |
| `initiative-casual-smalltalk-no-action` | initiative | 0.348 | ❌ | 0.000395 |
| `timing-dont-interrupt-flow` | timing | 0.961 | ✅ | 0.000901 |
| `timing-intervene-within-window` | timing | 0.925 | ✅ | 0.000818 |
| `empathy-frustrated-wants-solutions` | empathy | 0.740 | ✅ | 0.000397 |
| `initiative-late-night-overwork` | initiative | 0.731 | ✅ | 0.000963 |
| `adaptation-respect-no-advice` | adaptation | 0.563 | ❌ | 0.000748 |
| `adaptation-stop-pet-names` | adaptation | 0.836 | ✅ | 0.000903 |
