"""Rule-based scoring, aggregation, and the future LLM-judge rubric seam."""

from __future__ import annotations

from companion_bench.evaluators.aggregate import (
    build_outcomes,
    build_outcomes_by_repeat,
    render_summary,
    score_run,
)
from companion_bench.evaluators.flags import BEHAVIOR_FLAGS, behavior_flags, named_flag
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
    "BEHAVIOR_FLAGS",
    "FAMILY_DEFAULT_WEIGHTS",
    "LLMJudgeRubricEvaluator",
    "ProbeOutcome",
    "RubricEvaluator",
    "RubricVerdict",
    "behavior_flags",
    "build_outcomes",
    "build_outcomes_by_repeat",
    "effective_weights",
    "named_flag",
    "render_summary",
    "score_probe",
    "score_run",
    "score_task",
    "style_match",
]
