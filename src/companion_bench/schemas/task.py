"""Task schema: a versioned, schema-validated companion benchmark scenario.

A task scripts a short multi-turn conversation and marks one or more **probe** points
where the model under test is invoked. Each probe carries the expectations the evaluator
checks against (the right decision, the preferred style, the relevant target, etc.), so a
task is simultaneously the stimulus and the answer key.

The canonical scoring dimensions live here (on :class:`Dimension`) because the per-task
:class:`ScoringRubric` references them; the score schemas import them back from this
module, keeping the dependency direction ``model -> task -> score`` acyclic.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from companion_bench.schemas.model import Decision, Style

__all__ = [
    "DIMENSIONS",
    "Difficulty",
    "Dimension",
    "Family",
    "InterventionWindow",
    "ProbeTurn",
    "SafetyBoundary",
    "SafetyCategory",
    "ScoringRubric",
    "ScriptTurn",
    "SourceType",
    "Task",
    "Turn",
]


class Family(StrEnum):
    """Top-level task family (the primary dimension a task stresses)."""

    INITIATIVE = "initiative"
    EMPATHY = "empathy"
    TIMING = "timing"
    ADAPTATION = "adaptation"
    ABSTENTION = "abstention"
    SAFETY = "safety"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SourceType(StrEnum):
    """Provenance of a task, for licensing/repro transparency."""

    ORIGINAL = "original"
    ADAPTED_PUBLIC = "adapted_public"
    SYNTHETIC = "synthetic"
    HUMAN_GOLD = "human_gold"


class Dimension(StrEnum):
    """The six scored dimensions. Values are the keys used in scores and rubrics."""

    INITIATIVE_RELEVANCE = "initiative_relevance"
    TIMING = "timing"
    EMPATHY = "empathy"
    ADAPTATION = "adaptation"
    ABSTENTION = "abstention"
    SAFETY = "safety"


DIMENSIONS: tuple[str, ...] = tuple(d.value for d in Dimension)


class SafetyCategory(StrEnum):
    """Category of safety boundary a task guards against."""

    MANIPULATION = "manipulation"
    DEPENDENCY = "dependency"
    ROMANTICIZATION = "romanticization"
    MEDICAL_OVERREACH = "medical_overreach"
    LEGAL_OVERREACH = "legal_overreach"
    FINANCIAL_OVERREACH = "financial_overreach"
    PRIVACY = "privacy"
    OTHER = "other"


class ScriptTurn(BaseModel):
    """A fixed, pre-scripted line of the conversation (not a model invocation).

    ``role="context"`` is narrative scene-setting (e.g. "3 hours pass") rather than a
    literal chat message; the conversation builder folds it into a system note.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["script"] = "script"
    role: Literal["system", "user", "assistant", "context"]
    content: str


class ProbeTurn(BaseModel):
    """A point where the model under test is invoked, plus the answer key for it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["probe"] = "probe"
    probe_id: str
    instruction: str | None = None
    expected_decision: Decision
    preferred_style: Style | None = None
    expected_target_keywords: tuple[str, ...] = ()
    requires_permission: bool = False
    sensitive: bool = False
    # Per-probe signal extensions (merged with the task-level signals during scoring).
    positive_signals: tuple[str, ...] = ()
    negative_signals: tuple[str, ...] = ()
    # Behaviors the user has, by this point in the conversation, asked the model to stop.
    disliked_behaviors: tuple[str, ...] = ()
    # Whether to append the model's output to the running history for later probes.
    inject_response: bool = True


Turn = Annotated[ScriptTurn | ProbeTurn, Field(discriminator="kind")]


class InterventionWindow(BaseModel):
    """The set of probes at which intervening is considered well-timed.

    Intervening at a probe whose id is listed here scores full timing credit; intervening
    elsewhere is "too early / too late". Referenced probe ids must exist in the task.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    probe_ids: tuple[str, ...] = ()
    description: str | None = None


class ScoringRubric(BaseModel):
    """Per-task scoring configuration.

    ``weights`` maps a :class:`Dimension` to a non-negative weight. An empty mapping means
    "use the family defaults" (see ``evaluators.aggregate``). Only the dimensions present
    (after applicability filtering) contribute to the total, with weights renormalized.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    weights: dict[Dimension, float] = Field(default_factory=dict)
    pass_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    notes: str | None = None

    @field_validator("weights")
    @classmethod
    def _weights_non_negative(cls, weights: dict[Dimension, float]) -> dict[Dimension, float]:
        for dim, w in weights.items():
            if w < 0:
                raise ValueError(f"weight for {dim.value!r} must be >= 0, got {w}")
        return weights


class SafetyBoundary(BaseModel):
    """A boundary the model must not cross, expressed as forbidden text patterns.

    ``forbidden_patterns`` are treated as case-insensitive regular expressions by the
    safety evaluator. A ``hard`` violation floors the safety score to 0.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    boundary_id: str
    category: SafetyCategory
    description: str
    forbidden_patterns: tuple[str, ...] = ()
    severity: Literal["hard", "soft"] = "hard"


class Task(BaseModel):
    """A complete, versioned companion benchmark task.

    Field names follow the CompanionBench task contract exactly so authored YAML stays
    stable across versions. See ``docs/task_authoring.md``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str
    version: str
    family: Family
    difficulty: Difficulty
    source_type: SourceType
    license_note: str
    scenario_context: str
    user_persona: str
    conversation_turns: tuple[Turn, ...]
    allowed_intervention_window: InterventionWindow
    expected_abstention_behavior: str
    scoring_rubric: ScoringRubric
    positive_signals: tuple[str, ...] = ()
    negative_signals: tuple[str, ...] = ()
    safety_boundaries: tuple[SafetyBoundary, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    # -- derived views ------------------------------------------------------
    @property
    def probes(self) -> tuple[ProbeTurn, ...]:
        """The probe turns, in conversation order."""
        return tuple(t for t in self.conversation_turns if isinstance(t, ProbeTurn))

    @property
    def probe_ids(self) -> tuple[str, ...]:
        return tuple(p.probe_id for p in self.probes)

    def probe_index(self, probe_id: str) -> int:
        """0-based index of a probe among the task's probes."""
        return self.probe_ids.index(probe_id)

    # -- integrity checks ---------------------------------------------------
    @model_validator(mode="after")
    def _check_integrity(self) -> Task:
        probe_ids = [p.probe_id for p in self.probes]
        if not probe_ids:
            raise ValueError(f"task {self.task_id!r} has no probe turns")
        dupes = {pid for pid in probe_ids if probe_ids.count(pid) > 1}
        if dupes:
            raise ValueError(f"task {self.task_id!r} has duplicate probe ids: {sorted(dupes)}")
        unknown = [
            pid for pid in self.allowed_intervention_window.probe_ids if pid not in probe_ids
        ]
        if unknown:
            raise ValueError(
                f"task {self.task_id!r} intervention window references unknown probe ids: {unknown}"
            )
        return self
