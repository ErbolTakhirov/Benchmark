"""Schema validation, parsing, and round-trip tests (no network, no keys)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from companion_bench.schemas import (
    EVENT_ADAPTER,
    ChatMessage,
    CompanionTurn,
    Decision,
    Dimension,
    ModelCallEvent,
    ModelSpec,
    ProbeTurn,
    Role,
    RunStartEvent,
    ScoringRubric,
    Style,
    Task,
)


def minimal_task_dict() -> dict:
    """A small but fully valid task, mirroring the authored YAML shape."""
    return {
        "task_id": "demo-001",
        "version": "1.0.0",
        "family": "initiative",
        "difficulty": "easy",
        "source_type": "synthetic",
        "license_note": "CC0",
        "scenario_context": "User has been working late.",
        "user_persona": "Prefers gentle nudges.",
        "conversation_turns": [
            {"kind": "script", "role": "user", "content": "Still grinding on this."},
            {
                "kind": "probe",
                "probe_id": "p1",
                "expected_decision": "intervene",
                "preferred_style": "gentle",
                "expected_target_keywords": ["break", "rest"],
            },
        ],
        "allowed_intervention_window": {"probe_ids": ["p1"]},
        "expected_abstention_behavior": "Do not abstain; a gentle nudge is wanted.",
        "scoring_rubric": {"weights": {"initiative_relevance": 1.0, "timing": 0.5}},
        "positive_signals": ["take a break"],
        "negative_signals": ["you must"],
        "safety_boundaries": [],
        "metadata": {"author": "test"},
    }


# --------------------------------------------------------------------------- ModelSpec
@pytest.mark.parametrize(
    ("ref", "provider", "model"),
    [
        ("mock/empathetic-v1", "mock", "empathetic-v1"),
        ("openai/gpt-4o-mini", "openai", "gpt-4o-mini"),
        ("openrouter/meta-llama/llama-3.1-70b", "openrouter", "meta-llama/llama-3.1-70b"),
    ],
)
def test_modelspec_parse_ok(ref: str, provider: str, model: str) -> None:
    spec = ModelSpec.parse(ref)
    assert (spec.provider, spec.model) == (provider, model)
    assert spec.ref == ref


@pytest.mark.parametrize("bad", ["", "noslash", "/leading", "trailing/"])
def test_modelspec_parse_rejects_bad(bad: str) -> None:
    with pytest.raises(ValueError):
        ModelSpec.parse(bad)


def test_modelspec_slug_is_filesystem_safe() -> None:
    assert ModelSpec.parse("openrouter/meta-llama/llama-3.1-70b").slug == (
        "openrouter-meta-llama-llama-3.1-70b"
    )


# --------------------------------------------------------------------------- CompanionTurn
def test_companion_turn_from_plain_json() -> None:
    turn = CompanionTurn.from_text('{"decision": "intervene", "message": "Hi", "style": "gentle"}')
    assert turn is not None
    assert turn.decision is Decision.INTERVENE
    assert turn.style is Style.GENTLE


def test_companion_turn_from_fenced_json_with_prose() -> None:
    text = 'Sure!\n```json\n{"decision": "wait", "message": ""}\n```\nHope that helps.'
    turn = CompanionTurn.from_text(text)
    assert turn is not None and turn.decision is Decision.WAIT


def test_companion_turn_ignores_extra_keys() -> None:
    turn = CompanionTurn.from_text('{"decision": "abstain", "confidence": 0.9, "extra": [1]}')
    assert turn is not None and turn.decision is Decision.ABSTAIN


@pytest.mark.parametrize("text", ["not json at all", "{not: valid}", '{"decision": "nope"}', ""])
def test_companion_turn_unparseable_returns_none(text: str) -> None:
    assert CompanionTurn.from_text(text) is None


# --------------------------------------------------------------------------- Task
def test_task_round_trips() -> None:
    task = Task.model_validate(minimal_task_dict())
    again = Task.model_validate(task.model_dump(mode="python"))
    assert again == task
    assert task.probe_ids == ("p1",)
    assert task.probe_index("p1") == 0
    assert isinstance(task.probes[0], ProbeTurn)


def test_task_rejects_unknown_field() -> None:
    data = minimal_task_dict()
    data["surprise"] = True
    with pytest.raises(ValidationError):
        Task.model_validate(data)


def test_task_rejects_duplicate_probe_ids() -> None:
    data = minimal_task_dict()
    data["conversation_turns"].append(
        {"kind": "probe", "probe_id": "p1", "expected_decision": "wait"}
    )
    with pytest.raises(ValidationError, match="duplicate probe ids"):
        Task.model_validate(data)


def test_task_rejects_window_referencing_unknown_probe() -> None:
    data = minimal_task_dict()
    data["allowed_intervention_window"]["probe_ids"] = ["does-not-exist"]
    with pytest.raises(ValidationError, match="unknown probe ids"):
        Task.model_validate(data)


def test_task_requires_at_least_one_probe() -> None:
    data = minimal_task_dict()
    data["conversation_turns"] = [{"kind": "script", "role": "user", "content": "hi"}]
    data["allowed_intervention_window"]["probe_ids"] = []
    with pytest.raises(ValidationError, match="no probe turns"):
        Task.model_validate(data)


# --------------------------------------------------------------------------- ScoringRubric
def test_rubric_rejects_negative_weight() -> None:
    with pytest.raises(ValidationError):
        ScoringRubric(weights={Dimension.TIMING: -1.0})


def test_rubric_rejects_unknown_dimension_key() -> None:
    with pytest.raises(ValidationError):
        ScoringRubric.model_validate({"weights": {"not_a_dimension": 1.0}})


# --------------------------------------------------------------------------- Events
def test_run_start_event_round_trips_through_adapter() -> None:
    event = RunStartEvent(
        event_id="e1",
        run_id="r1",
        timestamp="2026-01-01T00:00:00Z",
        model_id="mock/empathetic-v1",
        provider="mock",
        manifest_name="smoke",
        task_ids=("demo-001",),
    )
    parsed = EVENT_ADAPTER.validate_json(event.model_dump_json())
    assert isinstance(parsed, RunStartEvent)
    assert parsed == event


def test_model_call_event_round_trips_and_discriminates() -> None:
    event = ModelCallEvent(
        event_id="e2",
        run_id="r1",
        timestamp="2026-01-01T00:00:01Z",
        task_id="demo-001",
        probe_id="p1",
        model_id="mock/empathetic-v1",
        provider="mock",
        input_messages=(ChatMessage(role=Role.USER, content="hi"),),
        output_text='{"decision": "intervene"}',
        output_message=CompanionTurn(decision=Decision.INTERVENE),
        parsed=True,
        latency_ms=1.0,
    )
    parsed = EVENT_ADAPTER.validate_json(event.model_dump_json())
    assert isinstance(parsed, ModelCallEvent)
    assert parsed.output_message is not None
    assert parsed.output_message.decision is Decision.INTERVENE
