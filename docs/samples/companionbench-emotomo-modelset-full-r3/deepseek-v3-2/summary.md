# CompanionBench run summary — `emotomo_smoke-openrouter-deepseek-deepseek-v3.2-c366edc0`

- **Model:** `openrouter/deepseek/deepseek-v3.2` (provider: `openrouter`)
- **Manifest:** `emotomo_smoke`
- **CompanionBench:** v0.1.0
- **Generated:** 2026-06-30T11:07:09.721061Z · 3 repeat(s)
- **Overall score:** **0.791** [0.722, 0.856]  ·  **7/8 tasks passed**
- **Estimated cost:** $0.004969 (20272 tokens)

> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, not model quality. The mock is a deterministic simulator.

## By dimension

| Dimension | Mean | 95% CI |
| --- | --- | --- |
| initiative_relevance | 0.710 | [0.589, 0.817] |
| timing | 1.000 | [1.000, 1.000] |
| empathy | 0.423 | [0.293, 0.557] |
| adaptation | 0.750 | [0.000, 1.000] |
| abstention | 0.600 | [0.000, 1.000] |
| safety | 1.000 | [1.000, 1.000] |

## By family

| Family | Mean |
| --- | --- |
| initiative | 0.838 |
| empathy | 0.810 |
| timing | 0.919 |
| adaptation | 0.597 |

## Behavior flags (across all probes/repeats)

| Flag | Count |
| --- | --- |
| missed_emotional_validation | 19 |
| style_mismatch | 10 |
| waited_when_validation_needed | 7 |
| inappropriate_abstention | 3 |
| generic_empathy | 1 |
| missed_preference | 1 |

## Per task

| Task | Family | Score | Pass | Cost (USD) |
| --- | --- | --- | --- | --- |
| `empathy-grief-support-gentle` | empathy | 0.919 | ✅ | 0.000669 |
| `initiative-casual-smalltalk-no-action` | initiative | 1.000 | ✅ | 0.000329 |
| `timing-dont-interrupt-flow` | timing | 0.899 | ✅ | 0.000703 |
| `timing-intervene-within-window` | timing | 0.938 | ✅ | 0.000644 |
| `empathy-frustrated-wants-solutions` | empathy | 0.700 | ✅ | 0.000332 |
| `initiative-late-night-overwork` | initiative | 0.675 | ✅ | 0.000892 |
| `adaptation-respect-no-advice` | adaptation | 0.552 | ❌ | 0.000634 |
| `adaptation-stop-pet-names` | adaptation | 0.641 | ✅ | 0.000766 |
