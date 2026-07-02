"""Inter-rater agreement metrics: primitives + the report over the pilot fixture."""

from __future__ import annotations

import json
from pathlib import Path

from companion_bench.evaluators.agreement import (
    cohens_kappa,
    compute_agreement,
    krippendorff_alpha,
    percent_agreement,
)
from companion_bench.schemas.gold import GoldLabel

REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT = REPO_ROOT / "data" / "gold" / "pilot_v0_1_alpha.jsonl"


def test_krippendorff_matches_reference_example() -> None:
    # The `krippendorff` package's documented example: nominal ~0.691, ordinal ~0.807.
    n = None
    rows = [
        [n, n, n, n, n, 3, 4, 1, 2, 1, 1, 3, 3, n, 3],
        [1, n, 2, 1, 3, 3, 4, 3, n, n, n, n, n, n, n],
        [n, n, 2, 1, 3, 4, 4, n, 2, 1, 1, 3, 3, n, 4],
    ]
    units = [[rows[c][u] for c in range(3) if rows[c][u] is not None] for u in range(15)]
    assert round(krippendorff_alpha(units, "nominal"), 3) == 0.691
    assert round(krippendorff_alpha(units, "ordinal"), 3) == 0.807


def test_perfect_agreement_is_one() -> None:
    assert krippendorff_alpha([[3, 3, 3], [1, 1], [5, 5, 5]], "ordinal") == 1.0
    assert percent_agreement([[1, 1, 1], [2, 2]]) == 1.0
    assert cohens_kappa([("a", "a"), ("b", "b")]) == 1.0


def test_disagreement_scores_lower_than_agreement() -> None:
    agree = krippendorff_alpha([[1, 1], [2, 2], [3, 3], [4, 4]], "ordinal")
    disagree = krippendorff_alpha([[1, 4], [2, 3], [3, 2], [4, 1]], "ordinal")
    assert agree == 1.0
    assert disagree is not None and disagree < agree
    assert percent_agreement([[1, 2], [3, 4]]) == 0.0


def test_missing_and_single_value_units_handled() -> None:
    # Units with < 2 values contribute no pairs and must not crash.
    assert krippendorff_alpha([[3], [4], [1, 1]], "nominal") == 1.0
    assert percent_agreement([[3], []]) is None  # nothing comparable
    assert krippendorff_alpha([], "nominal") is None


def test_cohens_kappa_needs_pairs() -> None:
    assert cohens_kappa([]) is None
    # Half-agreement on two symmetric categories -> kappa 0.
    assert cohens_kappa([("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")]) == 0.0


def test_single_annotator_warns_not_crashes() -> None:
    labels = [
        GoldLabel.model_validate(
            {
                "gold_set_id": "g",
                "task_id": "t",
                "probe_id": "p1",
                "response_id": "r1",
                "annotator_id_hash": "solo",
                "annotation_timestamp": "2026-01-01T00:00:00Z",
                "dimensions": {"empathy": {"rating": 4}},
                "overall_preference": "accept",
            }
        )
    ]
    report = compute_agreement(labels)
    assert report.overall.n_annotators == 1
    assert any("one annotator" in w.lower() for w in report.warnings)


def test_pilot_agreement_report() -> None:
    labels = [GoldLabel.model_validate(json.loads(x)) for x in PILOT.read_text().splitlines()]
    report = compute_agreement(labels)
    assert report.overall.n_annotators == 3
    # Synthetic near-consensus fixture -> high overall agreement, Cohen's kappa n/a (>2 annotators).
    assert report.overall.alpha_nominal is not None and report.overall.alpha_nominal > 0.6
    assert report.overall.cohens_kappa is None
    assert report.per_dimension  # every dimension has an entry
