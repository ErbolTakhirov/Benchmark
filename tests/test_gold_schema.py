"""Human gold-label schema: validation, ranges, missing dims, and the committed pilot fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from companion_bench.schemas.gold import GoldDimensionRating, GoldLabel, GoldResponse
from companion_bench.schemas.task import Dimension

REPO_ROOT = Path(__file__).resolve().parents[1]
PILOT_LABELS = REPO_ROOT / "data" / "gold" / "pilot_v0_1_alpha.jsonl"
PILOT_RESPONSES = REPO_ROOT / "data" / "gold" / "pilot_responses.jsonl"


def _label(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "gold_set_id": "g",
        "task_id": "t",
        "probe_id": "p1",
        "response_id": "r1",
        "annotator_id_hash": "anon-1",
        "annotation_timestamp": "2026-01-01T00:00:00Z",
        "dimensions": {"empathy": {"rating": 4, "confidence": 3}},
        "overall_preference": "accept",
    }
    base.update(over)
    return base


def test_valid_label_parses() -> None:
    lab = GoldLabel.model_validate(_label())
    assert lab.dimensions[Dimension.EMPATHY].rating == 4
    assert lab.not_human_collected is True  # defaults to a fixture unless overridden


def test_rating_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldLabel.model_validate(_label(dimensions={"empathy": {"rating": 6}}))
    with pytest.raises(ValidationError):
        GoldLabel.model_validate(_label(dimensions={"safety": {"rating": 0}}))


def test_skipped_dimension_allowed() -> None:
    # A dimension may be omitted entirely, or present with rating=None.
    lab = GoldLabel.model_validate(
        _label(dimensions={"empathy": {"rating": None, "confidence": 2}})
    )
    assert lab.dimensions[Dimension.EMPATHY].rating is None
    assert GoldLabel.model_validate(_label(dimensions={})).dimensions == {}


def test_invalid_overall_preference_rejected() -> None:
    with pytest.raises(ValidationError):
        GoldLabel.model_validate(_label(overall_preference="maybe"))


def test_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        GoldLabel.model_validate(_label(surprise="x"))
    with pytest.raises(ValidationError):
        GoldDimensionRating.model_validate({"rating": 3, "surprise": 1})


def test_pilot_fixture_is_valid_and_synthetic() -> None:
    labels = [
        GoldLabel.model_validate(json.loads(x)) for x in PILOT_LABELS.read_text().splitlines()
    ]
    assert len(labels) >= 12
    # Honesty guard: the committed pilot must never masquerade as real human data.
    assert all(lab.not_human_collected for lab in labels)
    assert all(lab.source_type == "synthetic_pilot_labels" for lab in labels)
    assert len({lab.annotator_id_hash for lab in labels}) >= 2  # multiple annotators


def test_pilot_responses_are_valid() -> None:
    resps = [
        GoldResponse.model_validate(json.loads(x)) for x in PILOT_RESPONSES.read_text().splitlines()
    ]
    assert len(resps) >= 12
    # At least one deliberately-unparseable response (the parse/format-issue case).
    assert any(not r.parsed for r in resps)
    # Every labeled response_id has a matching response fixture.
    label_ids = {json.loads(x)["response_id"] for x in PILOT_LABELS.read_text().splitlines()}
    resp_ids = {r.response_id for r in resps}
    assert label_ids <= resp_ids
