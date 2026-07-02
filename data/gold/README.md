<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench human gold-label pilot

This directory holds the **human gold-label** workflow: the schema, an annotation template, and a
small **pilot** used to prove the methodology, metrics, and calibration path. Human labels exist to
**calibrate** the automated scorers against what people actually value — they never replace the
rule-based scores, and a judge never replaces either. See
[`docs/human_gold_set.md`](../../docs/human_gold_set.md) and
[`docs/judge_calibration.md`](../../docs/judge_calibration.md).

## Real annotation round

To collect **real** human labels, use the packet at
[`../../analysis/annotation_round_v0_1/`](../../analysis/annotation_round_v0_1/) and the
`companion-bench gold import-human` de-identifier. Raw returned files go in
[`private/`](private/README.md) (git-ignored); only the de-identified aggregate is committed. Full
workflow: [`../../docs/human_gold_set.md`](../../docs/human_gold_set.md).

## ⚠️ The pilot here is SYNTHETIC, not real human ratings

`pilot_v0_1_alpha.jsonl` is a **test fixture**: every label is marked
`not_human_collected: true`, `source_type: synthetic_pilot_labels`, `purpose: schema/test fixture
only`. It exists to exercise the schema, agreement metrics, and calibration commands — **not** to
make any claim about any model. Real human collection is future work; see the limitations in
[`docs/human_gold_set.md`](../../docs/human_gold_set.md).

## Files

| File | What it is |
| --- | --- |
| `pilot_responses.jsonl` | The sanitized companion **responses** being rated (each references a real `task_id`/`probe_id` so the rule scorer and judge can re-score the *same* response). |
| `pilot_v0_1_alpha.jsonl` | The **gold labels** (one JSON object per annotator × response). |
| `annotation_template.csv` | A human-fillable template; the canonical storage format is the JSONL above. |

## Dimension names

Gold dimensions reuse the canonical scorer dimensions so calibration lines up 1:1. Human-friendly
names map as:

| Human-friendly | Canonical key |
| --- | --- |
| emotional attunement | `empathy` |
| initiative relevance | `initiative_relevance` |
| timing / pacing | `timing` |
| preference adaptation | `adaptation` |
| non-intrusion / abstention | `abstention` |
| safety boundaries | `safety` |

## Label schema (per annotator × response)

Each JSONL line validates against `companion_bench.schemas.gold.GoldLabel`:

- `gold_set_id`, `version`, `task_id`, `probe_id`, `response_id`, `model_id?`
- `annotator_id_hash` — an **opaque hash only**. Never a real name or email.
- `annotation_timestamp` (ISO-8601)
- `dimensions`: `{<canonical dim>: {rating: 1–5|null, confidence: 1–5|null, rationale, flags[]}}`.
  A skipped dimension may be omitted or set to `null`.
- `overall_preference`: `accept` | `reject` | `borderline`
- `notes`, `license_note`, `pii_check`, plus the provenance flags above.

Multiple annotators rate the same response by sharing `(task_id, probe_id, response_id)`; that is
what makes inter-rater agreement computable.

## Privacy

- Identify annotators by `annotator_id_hash` only. `companion-bench gold validate` runs a light
  email-shaped PII check and refuses obvious PII.
- Real annotations that could contain PII belong in `data/gold/private/` (git-ignored), never here.

## Commands

```bash
companion-bench gold validate  data/gold/pilot_v0_1_alpha.jsonl
companion-bench gold agreement data/gold/pilot_v0_1_alpha.jsonl
companion-bench calibrate rules --gold data/gold/pilot_v0_1_alpha.jsonl \
  --responses data/gold/pilot_responses.jsonl --out analysis/calibration/rules_vs_gold_pilot.md
# Offline mock judge (deterministic simulator; validates the pipeline, not judge quality):
companion-bench judge --responses data/gold/pilot_responses.jsonl \
  --judge-provider mock --judge-model demo --out analysis/judge/pilot
companion-bench calibrate judge --gold data/gold/pilot_v0_1_alpha.jsonl \
  --judge analysis/judge/pilot/judge_scores.json --out analysis/calibration/judge_vs_gold_pilot.md
```

`analysis/` outputs are git-ignored (regenerated from the committed inputs above).
