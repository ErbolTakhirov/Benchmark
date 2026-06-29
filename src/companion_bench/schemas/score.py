"""Score schemas: per-dimension, per-probe, per-task, and per-run results.

These are pure data containers. All scoring logic lives in ``evaluators`` — this keeps the
artifact shape stable and easy to read back from ``scores.json`` regardless of how the
numbers were produced (rule-based today, LLM-judge / human eval in future milestones).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from companion_bench.schemas.model import Decision
from companion_bench.schemas.task import Dimension, Family

__all__ = [
    "DimensionScore",
    "ProbeScore",
    "RunScores",
    "TaskScore",
]


class DimensionScore(BaseModel):
    """Score for a single dimension at a single probe.

    ``value is None`` means the dimension does not apply to this probe (e.g. timing when
    correctly not intervening); such dimensions are excluded from the weighted total and
    their weight is redistributed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: float | None
    weight: float = Field(ge=0.0)
    rationale: str
    flags: tuple[str, ...] = ()

    @property
    def applicable(self) -> bool:
        return self.value is not None


class ProbeScore(BaseModel):
    """Aggregated dimension scores for one probe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    probe_id: str
    expected_decision: Decision
    actual_decision: Decision | None
    parsed: bool
    dimensions: dict[Dimension, DimensionScore]
    total: float = Field(ge=0.0, le=1.0)


class TaskScore(BaseModel):
    """Scores for a whole task (mean across its probes)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str
    family: Family
    probe_scores: tuple[ProbeScore, ...]
    dimension_means: dict[Dimension, float | None]
    total: float = Field(ge=0.0, le=1.0)
    pass_threshold: float
    passed: bool
    cost_usd: float | None = None


class RunScores(BaseModel):
    """Top-level scoring artifact written to ``scores.json``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    model_id: str
    provider: str
    generated_at: str
    task_scores: tuple[TaskScore, ...]
    by_family: dict[Family, float]
    by_dimension: dict[Dimension, float | None]
    overall: float = Field(ge=0.0, le=1.0)
    n_tasks: int
    n_passed: int
    total_cost_usd: float | None = None
    total_tokens: int | None = None
