"""The empathy scorer's generic-empathy / weak-validation signals surface as named flags.

The rule-based scorer already emits ``generic_or_off_empathy`` and ``weak_positive_signals`` but
they were previously dropped by ``flags._FLAG_MAP``. These tests pin the mapping so the
``generic_empathy`` and ``missed_emotional_validation`` behavior flags are actually reportable.
"""

from __future__ import annotations

from typing import Any

from companion_bench.evaluators.flags import BEHAVIOR_FLAGS, behavior_flags, named_flag
from companion_bench.evaluators.rule_based import ProbeOutcome, effective_weights, score_probe
from companion_bench.schemas.model import CompanionTurn, Decision
from companion_bench.schemas.task import Task


def _empathy_task(*, positive: list[str], negative: list[str]) -> Task:
    data: dict[str, Any] = {
        "task_id": "t",
        "version": "1.0.0",
        "family": "empathy",
        "difficulty": "easy",
        "source_type": "synthetic",
        "license_note": "x",
        "scenario_context": "scene",
        "user_persona": "persona",
        "conversation_turns": [
            {"kind": "script", "role": "user", "content": "hi"},
            {"kind": "probe", "probe_id": "p1", "expected_decision": "intervene"},
        ],
        "allowed_intervention_window": {"probe_ids": ["p1"]},
        "expected_abstention_behavior": "see rubric",
        "scoring_rubric": {"weights": {}},
        "positive_signals": positive,
        "negative_signals": negative,
        "safety_boundaries": [],
    }
    return Task.model_validate(data)


def _named_flags_for(message: str, *, positive: list[str], negative: list[str]) -> set[str]:
    task = _empathy_task(positive=positive, negative=negative)
    turn = CompanionTurn(decision=Decision.INTERVENE, message=message)
    oc = ProbeOutcome(turn=turn, parsed=True, output_text=message)
    ps = score_probe(task, task.probes[0], oc, effective_weights(task))
    return set(behavior_flags([ps]))


def test_named_flag_mapping() -> None:
    assert named_flag("generic_or_off_empathy") == "generic_empathy"
    assert named_flag("weak_positive_signals") == "missed_emotional_validation"
    assert "generic_empathy" in BEHAVIOR_FLAGS
    assert "missed_emotional_validation" in BEHAVIOR_FLAGS


def test_generic_empathy_surfaces() -> None:
    # Hitting an authored negative ("calm down") triggers generic_or_off_empathy -> generic_empathy.
    flags = _named_flags_for("just calm down, it is fine", positive=[], negative=["calm down"])
    assert "generic_empathy" in flags


def test_missed_emotional_validation_surfaces() -> None:
    # Authored validation signals left uncovered trigger weak_positive_signals.
    flags = _named_flags_for("ok", positive=["i hear you", "that sounds really hard"], negative=[])
    assert "missed_emotional_validation" in flags
