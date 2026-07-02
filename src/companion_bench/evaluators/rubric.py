"""Rubric evaluator interface + the per-probe LLM-as-judge adapter.

The MVP scores with transparent rules (:mod:`companion_bench.evaluators.rule_based`). This module
defines the *interface* a judge implements so it drops in **alongside** (never replacing) the
rule-based scorer. As of the calibration pilot the LLM-judge seam is realized:
:class:`LLMJudgeRubricEvaluator` delegates to the versioned prompts in
:mod:`companion_bench.evaluators.judge_prompts` through an injected provider adapter. Batch judging
+ artifacts + cost gating live in :mod:`companion_bench.evaluators.judge`.

Judge output is a biased, opt-in calibration signal (self-preference, stylistic/verbosity bias,
prompt-sensitivity, non-determinism — see ``docs/benchmark_card.md`` /
``docs/judge_calibration.md``). It is reported next to, and calibrated against, the rule-based
baseline and human gold labels — never as the source of truth.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from companion_bench.adapters.base import ChatAdapter
from companion_bench.evaluators.judge_prompts import build_judge_messages, parse_judge_verdict
from companion_bench.evaluators.rule_based import ProbeOutcome
from companion_bench.schemas.gold import GoldResponse
from companion_bench.schemas.model import ChatMessage, ChatRequest, ModelSpec, Role
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
    """Per-probe LLM-as-judge: versioned prompt -> injected adapter -> validated verdict.

    The adapter is injected so this is testable offline with a stub and so the live gate stays in
    the CLI. A verdict that does not parse yields a zero-confidence :class:`RubricVerdict` flagged
    ``judge_parse_failure`` — never a coerced high score.
    """

    def __init__(self, adapter: ChatAdapter, *, provider: str, judge_model: str) -> None:
        self._adapter = adapter
        self.provider = provider
        self.judge_model = judge_model

    async def evaluate_probe(
        self, task: Task, probe: ProbeTurn, outcome: ProbeOutcome
    ) -> RubricVerdict:
        turn = outcome.turn
        response = GoldResponse(
            response_id=f"{task.task_id}:{probe.probe_id}",
            task_id=task.task_id,
            probe_id=probe.probe_id,
            parsed=turn is not None,
            output_text=outcome.output_text or (turn.message if turn else ""),
            decision=turn.decision if turn else None,
            message=turn.message if turn else "",
            target=turn.target if turn else None,
            style=turn.style if turn else None,
            ask_permission=turn.ask_permission if turn else False,
        )
        messages = tuple(
            ChatMessage(role=Role(m["role"]), content=m["content"])
            for m in build_judge_messages(task, probe, response)
        )
        chat = await self._adapter.generate(
            ChatRequest(
                model=ModelSpec(provider=self.provider, model=self.judge_model),
                messages=messages,
                temperature=0.0,
                response_format="json_object",
            )
        )
        verdict = parse_judge_verdict(chat.content)
        if verdict is None:
            return RubricVerdict(
                scores={},
                rationale="judge output did not parse into a valid verdict",
                confidence=0.0,
                flags=("judge_parse_failure",),
            )
        return RubricVerdict(
            scores=dict(verdict.dimension_scores),
            rationale=verdict.rationale,
            confidence=verdict.confidence,
            flags=verdict.flags,
        )
