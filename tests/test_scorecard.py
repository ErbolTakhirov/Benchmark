"""The self-assessed quality scorecard JSON is well-formed (10 categories, scores in [0, 10])."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCORECARD = REPO_ROOT / "docs" / "audits" / "benchmark_quality_scorecard.json"


def test_scorecard_has_ten_unique_categories_in_range() -> None:
    data = json.loads(SCORECARD.read_text(encoding="utf-8"))
    categories = data["categories"]
    assert len(categories) == 10
    assert len({c["key"] for c in categories}) == 10  # unique keys
    for category in categories:
        assert 0 <= category["score"] <= 10, category
        assert category["name"] and category["justification"]


def test_scorecard_disclaims_human_validation() -> None:
    data = json.loads(SCORECARD.read_text(encoding="utf-8"))
    not_supported = " ".join(data["claims_not_supported"]).lower()
    assert "human-validated" in not_supported
    assert isinstance(data["overall_average"], (int, float))
