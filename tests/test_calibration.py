"""Rule-vs-gold calibration over the committed pilot fixture (deterministic, offline)."""

from __future__ import annotations

import json
from pathlib import Path

from companion_bench.evaluators.calibration import (
    calibrate_rules_vs_gold,
    gold_consensus,
    render_calibration_md,
    response_to_outcome,
)
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.gold import GoldLabel, GoldResponse
from companion_bench.schemas.model import Decision
from companion_bench.schemas.task import Dimension

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD = REPO_ROOT / "data" / "gold"


def _load_tasks() -> dict[str, object]:
    idx: dict[str, object] = {}
    for name in ("full", "heldout"):
        _, tasks = load_manifest_and_tasks(REPO_ROOT / "manifests" / f"{name}.yaml")
        for t in tasks:
            idx[t.task_id] = t
    return idx


def _labels() -> list[GoldLabel]:
    return [
        GoldLabel.model_validate(json.loads(x))
        for x in (GOLD / "pilot_v0_1_alpha.jsonl").read_text().splitlines()
    ]


def _responses() -> list[GoldResponse]:
    return [
        GoldResponse.model_validate(json.loads(x))
        for x in (GOLD / "pilot_responses.jsonl").read_text().splitlines()
    ]


def test_response_to_outcome_roundtrip() -> None:
    parsed = GoldResponse(
        response_id="r",
        task_id="t",
        probe_id="p1",
        parsed=True,
        decision=Decision.INTERVENE,
        message="hi there",
    )
    oc = response_to_outcome(parsed)
    assert oc.turn is not None and oc.turn.decision is Decision.INTERVENE
    unparsed = GoldResponse(
        response_id="r2", task_id="t", probe_id="p1", parsed=False, output_text="not json"
    )
    assert response_to_outcome(unparsed).turn is None


def test_gold_consensus_shapes() -> None:
    dims, accept = gold_consensus(_labels())
    # Consensus values are normalized to [0, 1].
    for per in dims.values():
        for v in per.values():
            assert 0.0 <= v <= 1.0
    assert accept["emp-grief-strong"] is True  # clear-accept case
    assert accept["safety-fakeemergency-comply"] is False  # clear-reject case


def test_rules_vs_gold_calibration_is_sane_and_deterministic() -> None:
    labels, responses, tasks = _labels(), _responses(), _load_tasks()
    a = calibrate_rules_vs_gold(labels, responses, tasks)
    b = calibrate_rules_vs_gold(labels, responses, tasks)
    assert a == b  # deterministic
    assert a.n_items == 14
    # The rule scorer should track the (synthetic) human consensus fairly well on clear cases.
    assert a.overall_accept_agreement is not None and a.overall_accept_agreement >= 0.8
    abst = a.per_dimension[Dimension.ABSTENTION]
    assert abst.pearson is not None and abst.pearson > 0.8
    assert abst.mae is not None and abst.mae < 0.3
    # Report renders with the mandatory caveats + tables.
    md = render_calibration_md(a)
    assert "NOT statistically definitive" in md
    assert "Per-dimension" in md and "Top disagreements" in md


def test_no_fabricated_results_when_tasks_missing() -> None:
    # An unknown task id is reported as a warning, not silently scored.
    labels = _labels()
    bogus = [
        GoldResponse(
            response_id="x",
            task_id="does-not-exist",
            probe_id="p1",
            parsed=True,
            decision=Decision.WAIT,
        )
    ]
    report = calibrate_rules_vs_gold(labels, bogus, {})
    assert report.n_items == 0
    assert any("unknown task_id" in c for c in report.caveats)
