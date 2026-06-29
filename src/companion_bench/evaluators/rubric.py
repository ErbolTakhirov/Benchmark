"""Rubric evaluator interface — the seam for future LLM-as-judge and human evaluation.

The MVP scores with transparent rules (:mod:`companion_bench.evaluators.rule_based`). This
module defines the *interface* a future judge will implement so it can be dropped in
alongside (or compared against) the rule-based scorer, without changing the runner or the
artifact schema. **It is intentionally not implemented in the MVP.**

Why not ship a judge now? See ``docs/benchmark_card.md`` — LLM judges introduce
self-preference, stylistic bias, prompt-sensitivity, and non-determinism. The plan is to
(1) keep rule-based scoring as a reproducible baseline, (2) add an LLM judge behind this
interface with published prompts and seeds, and (3) calibrate both against a human-rated
gold set before reporting judge-based numbers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from companion_bench.evaluators.rule_based import ProbeOutcome
from companion_bench.schemas.task import Dimension, ProbeTurn, Task

__all__ = ["LLMJudgeRubricEvaluator", "RubricEvaluator", "RubricVerdict"]


@dataclass(frozen=True)
class RubricVerdict:
    """A judge's per-dimension verdict for one probe.

    ``scores`` maps a dimension to a value in ``[0, 1]``; ``confidence`` and ``rationale``
    let downstream aggregation weight or audit the judgment.
    """

    scores: dict[Dimension, float]
    rationale: str
    confidence: float = 1.0
    flags: tuple[str, ...] = field(default_factory=tuple)


class RubricEvaluator(ABC):
    """Abstract rubric-based (e.g. LLM-as-judge) probe evaluator."""

    @abstractmethod
    async def evaluate_probe(
        self, task: Task, probe: ProbeTurn, outcome: ProbeOutcome
    ) -> RubricVerdict:
        """Return a :class:`RubricVerdict` for a single probe outcome."""
        raise NotImplementedError


class LLMJudgeRubricEvaluator(RubricEvaluator):
    """Placeholder for the future LLM-as-judge evaluator (not implemented in the MVP)."""

    def __init__(self, judge_model: str = "anthropic/claude-sonnet-4-6") -> None:
        self.judge_model = judge_model

    async def evaluate_probe(
        self, task: Task, probe: ProbeTurn, outcome: ProbeOutcome
    ) -> RubricVerdict:
        raise NotImplementedError(
            "LLM-as-judge scoring is a planned milestone, not part of the MVP. "
            "Use the rule-based evaluator (companion_bench.evaluators.rule_based). "
            "See docs/scoring.md and docs/benchmark_card.md for the judge/human-eval plan."
        )
