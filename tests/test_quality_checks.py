"""`validate --strict-quality` invariants: catch weak tasks, pass the real suite."""

from __future__ import annotations

from companion_bench.runner.quality_checks import (
    check_task_quality,
    missing_failure_modes,
    positive_signal_overlaps,
    prompt_leakage,
    safety_task_without_boundaries,
)
from companion_bench.schemas.task import Family, SafetyBoundary, SafetyCategory, ScriptTurn
from suite_helpers import load_full_tasks, load_heldout_tasks


def _base_task():  # type: ignore[no-untyped-def]
    return next(iter(load_full_tasks()))


def test_real_suite_has_no_hard_errors() -> None:
    tasks = [*load_full_tasks(), *load_heldout_tasks()]
    report = check_task_quality(tasks, enforce_family_counts=False)
    assert report.errors == (), report.errors  # keyword-echo warnings are allowed, hard errors not
    assert set(report.family_counts) == {f.value for f in Family}


def test_full_suite_meets_family_thresholds() -> None:
    report = check_task_quality(load_full_tasks(), enforce_family_counts=True)
    assert report.errors == (), report.errors


def test_missing_failure_modes_detected() -> None:
    base = _base_task()
    weak = base.model_copy(
        update={"metadata": {k: v for k, v in base.metadata.items() if k != "failure_modes"}}
    )
    assert missing_failure_modes(weak)
    assert any("failure_modes" in e for e in check_task_quality([weak]).errors)


def test_safety_task_without_boundaries_detected() -> None:
    safety = next(t for t in load_full_tasks() if t.family is Family.SAFETY)
    weak = safety.model_copy(update={"safety_boundaries": ()})
    assert safety_task_without_boundaries(weak)
    assert any("safety_boundaries" in e for e in check_task_quality([weak]).errors)


def test_positive_signal_overlapping_forbidden_pattern_detected() -> None:
    boundary = SafetyBoundary(
        boundary_id="b",
        category=SafetyCategory.MEDICAL_OVERREACH,
        description="no dosing",
        forbidden_patterns=("take two",),
    )
    weak = _base_task().model_copy(
        update={"positive_signals": ("please take two pills",), "safety_boundaries": (boundary,)}
    )
    hits = positive_signal_overlaps(weak)
    assert hits and hits[0][1] == "take two"
    assert any("forbidden pattern" in e for e in check_task_quality([weak]).errors)


def test_prompt_leakage_detected_as_warning() -> None:
    leak = ScriptTurn(role="user", content="I'm anxious about the quarterly synergy report tonight")
    weak = _base_task().model_copy(
        update={
            "conversation_turns": (leak, *_base_task().conversation_turns),
            "positive_signals": ("quarterly synergy report",),
        }
    )
    assert "quarterly synergy report" in prompt_leakage(weak)
    assert any("keyword-echo" in w for w in check_task_quality([weak]).warnings)


def test_suite_without_wait_or_abstain_is_flagged() -> None:
    # A suite of only-intervene tasks leaves abstention/timing negatives untested.
    intervene_only = [
        t
        for t in load_full_tasks()
        if all(p.expected_decision.value == "intervene" for p in t.probes)
    ]
    if intervene_only:
        report = check_task_quality(intervene_only[:3])
        assert any("WAIT/ABSTAIN" in e for e in report.errors)
