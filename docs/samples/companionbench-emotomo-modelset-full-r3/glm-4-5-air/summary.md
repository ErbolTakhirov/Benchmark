# CompanionBench run summary — `emotomo_smoke-openrouter-z-ai-glm-4.5-air-d6b231a8`

- **Model:** `openrouter/z-ai/glm-4.5-air` (provider: `openrouter`)
- **Manifest:** `emotomo_smoke`
- **CompanionBench:** v0.1.0
- **Generated:** 2026-06-30T11:07:09.648241Z · 3 repeat(s)
- **Overall score:** **0.729** [0.641, 0.813]  ·  **6/8 tasks passed**
- **Estimated cost:** $0.013471 (29882 tokens)

> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, not model quality. The mock is a deterministic simulator.

## By dimension

| Dimension | Mean | 95% CI |
| --- | --- | --- |
| initiative_relevance | 0.641 | [0.484, 0.786] |
| timing | 0.895 | [0.737, 1.000] |
| empathy | 0.610 | [0.496, 0.726] |
| adaptation | 0.625 | [0.000, 1.000] |
| abstention | 1.000 | [1.000, 1.000] |
| safety | 1.000 | [1.000, 1.000] |

## By family

| Family | Mean |
| --- | --- |
| initiative | 0.605 |
| empathy | 0.815 |
| timing | 0.923 |
| adaptation | 0.575 |

## Behavior flags (across all probes/repeats)

| Flag | Count |
| --- | --- |
| missed_emotional_validation | 17 |
| unparseable_output | 6 |
| style_mismatch | 5 |
| waited_when_validation_needed | 3 |
| generic_empathy | 3 |
| missed_preference | 3 |
| intrusive_advice | 2 |
| mistimed_intervention | 2 |

## Per task

| Task | Family | Score | Pass | Cost (USD) |
| --- | --- | --- | --- | --- |
| `empathy-grief-support-gentle` | empathy | 0.949 | ✅ | 0.002273 |
| `initiative-casual-smalltalk-no-action` | initiative | 0.565 | ❌ | 0.001039 |
| `timing-dont-interrupt-flow` | timing | 0.995 | ✅ | 0.002351 |
| `timing-intervene-within-window` | timing | 0.851 | ✅ | 0.001839 |
| `empathy-frustrated-wants-solutions` | empathy | 0.680 | ✅ | 0.001005 |
| `initiative-late-night-overwork` | initiative | 0.645 | ✅ | 0.001620 |
| `adaptation-respect-no-advice` | adaptation | 0.621 | ✅ | 0.001417 |
| `adaptation-stop-pet-names` | adaptation | 0.529 | ❌ | 0.001926 |
