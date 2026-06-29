"""Rule-based scoring, aggregation, and the future LLM-judge rubric seam."""

from __future__ import annotations

from companion_bench.evaluators.aggregate import build_outcomes, render_summary, score_run
from companion_bench.evaluators.rubric import (
    LLMJudgeRubricEvaluator,
    RubricEvaluator,
    RubricVerdict,
)
from companion_bench.evaluators.rule_based import (
    FAMILY_DEFAULT_WEIGHTS,
    ProbeOutcome,
    effective_weights,
    score_probe,
    score_task,
    style_match,
)

__all__ = [
    "FAMILY_DEFAULT_WEIGHTS",
    "LLMJudgeRubricEvaluator",
    "ProbeOutcome",
    "RubricEvaluator",
    "RubricVerdict",
    "build_outcomes",
    "effective_weights",
    "render_summary",
    "score_probe",
    "score_run",
    "score_task",
    "style_match",
]
