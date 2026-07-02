"""LLM-as-judge: strict parsing, deterministic mock judge, rubric seam, and live gating.

No test makes a network call — the mock judge is offline and the rubric seam uses a stub adapter.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from companion_bench.adapters.base import ChatAdapter
from companion_bench.cli import app
from companion_bench.evaluators.calibration import calibrate_judge_vs_gold
from companion_bench.evaluators.judge import (
    build_items_from_responses,
    run_mock_judge,
    write_judge_artifacts,
)
from companion_bench.evaluators.judge_prompts import parse_judge_verdict
from companion_bench.evaluators.rubric import LLMJudgeRubricEvaluator
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.gold import GoldLabel, GoldResponse
from companion_bench.schemas.model import ChatRequest, ChatResponse, CompanionTurn, Decision
from companion_bench.schemas.task import Dimension, Task

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD = REPO_ROOT / "data" / "gold"


class _StubAdapter(ChatAdapter):
    """Returns a fixed body, no network — for testing the judge/rubric parse path."""

    provider = "stub"

    def __init__(self, content: str) -> None:
        self._content = content

    async def generate(self, request: ChatRequest) -> ChatResponse:
        return ChatResponse(provider="stub", model="stub", content=self._content, parsed=False)


def _tasks() -> dict[str, Task]:
    idx: dict[str, Task] = {}
    for name in ("full", "heldout"):
        _, tasks = load_manifest_and_tasks(REPO_ROOT / "manifests" / f"{name}.yaml")
        for t in tasks:
            idx[t.task_id] = t
    return idx


def _responses() -> list[GoldResponse]:
    return [
        GoldResponse.model_validate(json.loads(x))
        for x in (GOLD / "pilot_responses.jsonl").read_text().splitlines()
    ]


# --------------------------------------------------------------------------- parsing
def test_parse_valid_verdict() -> None:
    v = parse_judge_verdict(
        '{"dimension_scores": {"empathy": 0.8, "safety": 1.0}, "confidence": 0.7}'
    )
    assert v is not None
    assert v.dimension_scores[Dimension.EMPATHY] == 0.8
    assert v.confidence == 0.7


def test_parse_clamps_and_drops_unknown_dims() -> None:
    v = parse_judge_verdict('{"dimension_scores": {"empathy": 1.7, "made_up": 0.5, "safety": -3}}')
    assert v is not None
    assert v.dimension_scores[Dimension.EMPATHY] == 1.0  # clamped, not inflated beyond 1
    assert v.dimension_scores[Dimension.SAFETY] == 0.0
    assert Dimension.EMPATHY in v.dimension_scores and "made_up" not in {
        d.value for d in v.dimension_scores
    }


def test_parse_malformed_is_failure_not_coerced() -> None:
    assert parse_judge_verdict("not json at all") is None
    assert parse_judge_verdict('{"no_scores_here": true}') is None
    assert parse_judge_verdict('{"dimension_scores": {}}') is None  # empty -> failure


def test_parse_nan_infinity_not_coerced_to_high_score() -> None:
    # json.loads accepts NaN/Infinity; they must NOT clamp to a perfect 1.0.
    v = parse_judge_verdict(
        '{"dimension_scores": {"empathy": Infinity, "safety": NaN, "timing": 0.4}}'
    )
    assert v is not None
    assert Dimension.EMPATHY not in v.dimension_scores  # inf dropped, not clamped to 1.0
    assert Dimension.SAFETY not in v.dimension_scores  # NaN dropped
    assert v.dimension_scores[Dimension.TIMING] == 0.4
    # A non-finite / bool confidence falls back to the neutral default, never 1.0.
    v2 = parse_judge_verdict('{"dimension_scores": {"empathy": 0.5}, "confidence": Infinity}')
    assert v2 is not None and v2.confidence == 0.5
    v3 = parse_judge_verdict('{"dimension_scores": {"empathy": 0.5}, "confidence": true}')
    assert v3 is not None and v3.confidence == 0.5


# --------------------------------------------------------------------------- mock judge
def test_mock_judge_is_deterministic() -> None:
    items, _ = build_items_from_responses(_responses(), _tasks())
    a = run_mock_judge(items, judge_run_id="j", generated_at="t")
    b = run_mock_judge(items, judge_run_id="j", generated_at="t")
    assert a.by_dimension == b.by_dimension
    assert a.source == "mock"
    assert a.n_failed == 0
    assert a.total_cost_usd == 0.0


def test_judge_vs_gold_offline() -> None:
    labels = [
        GoldLabel.model_validate(json.loads(x))
        for x in (GOLD / "pilot_v0_1_alpha.jsonl").read_text().splitlines()
    ]
    items, _ = build_items_from_responses(_responses(), _tasks())
    judge = run_mock_judge(items, judge_run_id="j", generated_at="t")
    report = calibrate_judge_vs_gold(labels, judge)
    assert report.label == "judge-vs-gold"
    assert report.n_items > 0
    assert any("MOCK judge" in c for c in report.caveats)


def test_write_judge_artifacts(tmp_path: Path) -> None:
    items, _ = build_items_from_responses(_responses(), _tasks())
    judge = run_mock_judge(items, judge_run_id="j", generated_at="t")
    sp, ep = write_judge_artifacts(tmp_path, judge)
    assert sp.is_file() and ep.is_file()
    assert sp.name == "judge_scores.json" and ep.name == "judge_events.jsonl"
    # events file has one line per probe result.
    assert len(ep.read_text().splitlines()) == judge.n_probes


# --------------------------------------------------------------------------- rubric seam
def _mini_task() -> tuple[Task, Any]:
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
    }
    task = Task.model_validate(data)
    return task, task.probes[0]


async def test_rubric_judge_seam_parses_and_flags_failure() -> None:
    from companion_bench.evaluators.rule_based import ProbeOutcome

    task, probe = _mini_task()
    outcome = ProbeOutcome(
        turn=CompanionTurn(decision=Decision.INTERVENE, message="hi"), parsed=True
    )

    ok = LLMJudgeRubricEvaluator(
        _StubAdapter(
            '{"dimension_scores": {"empathy": 0.9}, "confidence": 0.8, "rationale": "ok"}'
        ),
        provider="stub",
        judge_model="x",
    )
    verdict = await ok.evaluate_probe(task, probe, outcome)
    assert verdict.scores[Dimension.EMPATHY] == 0.9
    assert "judge_parse_failure" not in verdict.flags

    bad = LLMJudgeRubricEvaluator(_StubAdapter("garbage"), provider="stub", judge_model="x")
    verdict2 = await bad.evaluate_probe(task, probe, outcome)
    assert verdict2.confidence == 0.0
    assert "judge_parse_failure" in verdict2.flags  # never coerced to a high score


# --------------------------------------------------------------------------- CLI live gate
def test_cli_mock_judge_runs_offline(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "judge",
            "--responses",
            str(GOLD / "pilot_responses.jsonl"),
            "--judge-provider",
            "mock",
            "--judge-model",
            "demo",
            "--out",
            str(tmp_path / "j"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "j" / "judge_scores.json").is_file()


def test_cli_real_judge_refused_without_live_gate(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "judge",
            "--responses",
            str(GOLD / "pilot_responses.jsonl"),
            "--judge-provider",
            "openrouter",
            "--judge-model",
            "some/model",
            "--out",
            str(tmp_path / "j"),
        ],
    )
    # Refused before any network call (no --live).
    assert result.exit_code == 1
    assert not (tmp_path / "j" / "judge_scores.json").exists()
