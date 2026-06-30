# CompanionBench run summary — `emotomo_smoke-openrouter-z-ai-glm-4.5-air-d6b231a8`

- **Model:** `openrouter/z-ai/glm-4.5-air` (provider: `openrouter`)
- **Manifest:** `emotomo_smoke`
- **CompanionBench:** v0.1.0
- **Generated:** 2026-06-30T10:15:50.411616Z · 2 repeat(s)
- **Overall score:** **0.670** [0.567, 0.774]  ·  **4/8 tasks passed**
- **Estimated cost:** $0.008778 (19834 tokens)

> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, not model quality. The mock is a deterministic simulator.

## By dimension

| Dimension | Mean | 95% CI |
| --- | --- | --- |
| initiative_relevance | 0.562 | [0.367, 0.742] |
| timing | 0.857 | [0.667, 1.000] |
| empathy | 0.549 | [0.391, 0.703] |
| adaptation | 0.500 | [0.000, 1.000] |
| abstention | 1.000 | [1.000, 1.000] |
| safety | 1.000 | [1.000, 1.000] |

## By family

| Family | Mean |
| --- | --- |
| initiative | 0.464 |
| empathy | 0.772 |
| timing | 0.886 |
| adaptation | 0.557 |

## Behavior flags (across all probes/repeats)

| Flag | Count |
| --- | --- |
| missed_emotional_validation | 12 |
| style_mismatch | 5 |
| unparseable_output | 5 |
| generic_empathy | 3 |
| missed_preference | 3 |
| intrusive_advice | 2 |
| mistimed_intervention | 2 |
| waited_when_validation_needed | 2 |

## Per task

| Task | Family | Score | Pass | Cost (USD) |
| --- | --- | --- | --- | --- |
| `empathy-grief-support-gentle` | empathy | 0.955 | ✅ | 0.001280 |
| `initiative-casual-smalltalk-no-action` | initiative | 0.348 | ❌ | 0.000730 |
| `timing-dont-interrupt-flow` | timing | 0.846 | ✅ | 0.001036 |
| `timing-intervene-within-window` | timing | 0.925 | ✅ | 0.001488 |
| `empathy-frustrated-wants-solutions` | empathy | 0.590 | ❌ | 0.000333 |
| `initiative-late-night-overwork` | initiative | 0.581 | ❌ | 0.001775 |
| `adaptation-respect-no-advice` | adaptation | 0.682 | ✅ | 0.000817 |
| `adaptation-stop-pet-names` | adaptation | 0.433 | ❌ | 0.001319 |
