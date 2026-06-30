"""Audit: safety is NOT always 1.000 — unsafe behavior is actually penalized.

The full live run found safety == 1.000 for every model because real models did not emit the
authored forbidden patterns on the tiny suite. Offline, the deterministic ``intrusive-v1`` (which
emits a forbidden pattern) must drive the safety dimension below 1.0, and ``empathetic-v1`` must
never trip a boundary it was given (which also catches the authoring bug where a positive_signal
overlaps a forbidden_pattern).
"""

from __future__ import annotations

from companion_bench.schemas.task import Dimension, Family
from suite_helpers import load_full_tasks, score_suite


def _safety(score) -> float | None:
    return score.dimension_means[Dimension.SAFETY]


def test_intrusive_trips_safety_across_the_suite() -> None:
    scores = score_suite(load_full_tasks(), "intrusive-v1")
    safety = [v for s in scores if (v := _safety(s)) is not None]
    assert safety, "no applicable safety scores"
    assert min(safety) < 1.0, "safety scored 1.000 everywhere even for intrusive-v1"
    assert sum(1 for v in safety if v < 1.0) >= 3, "too few tasks actually penalize unsafe output"


def test_safety_family_reliably_catches_intrusive() -> None:
    safety_tasks = [t for t in load_full_tasks() if t.family is Family.SAFETY]
    scores = score_suite(safety_tasks, "intrusive-v1")
    tripped = [s for s in scores if (v := _safety(s)) is not None and v < 0.5]
    assert len(tripped) >= max(1, len(safety_tasks) // 2), (
        "safety-family tasks do not reliably catch unsafe output from intrusive-v1"
    )


def test_empathetic_is_safe_on_every_task() -> None:
    # The well-behaved reference must never trip a boundary it was handed; a value < 1.0 here
    # means a positive_signal / target overlaps a forbidden_pattern (an authoring bug).
    for s in score_suite(load_full_tasks(), "empathetic-v1"):
        v = _safety(s)
        assert v is None or v == 1.0, (
            f"{s.task_id}: empathetic-v1 safety={v} (signal/forbidden overlap?)"
        )
