"""Pydantic v2 schemas: tasks, models/requests, run artifacts, and scores.

Dependency direction is strictly ``model -> task -> score`` (and ``model -> run``), so
importing any single module never triggers a cycle.
"""

from __future__ import annotations

from companion_bench.schemas.model import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CompanionTurn,
    Decision,
    ModelSpec,
    Role,
    Style,
    TokenUsage,
)
from companion_bench.schemas.run import (
    EVENT_ADAPTER,
    BaseEvent,
    Event,
    EventType,
    ModelCallEvent,
    ModelFailureEvent,
    RunConfig,
    RunEndEvent,
    RunMetadata,
    RunStartEvent,
)
from companion_bench.schemas.score import (
    DimensionScore,
    ProbeScore,
    RunScores,
    TaskScore,
)
from companion_bench.schemas.task import (
    DIMENSIONS,
    Difficulty,
    Dimension,
    Family,
    InterventionWindow,
    ProbeTurn,
    SafetyBoundary,
    SafetyCategory,
    ScoringRubric,
    ScriptTurn,
    SourceType,
    Task,
    Turn,
)

__all__ = [
    "DIMENSIONS",
    "EVENT_ADAPTER",
    "BaseEvent",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CompanionTurn",
    "Decision",
    "Difficulty",
    "Dimension",
    "DimensionScore",
    "Event",
    "EventType",
    "Family",
    "InterventionWindow",
    "ModelCallEvent",
    "ModelFailureEvent",
    "ModelSpec",
    "ProbeScore",
    "ProbeTurn",
    "Role",
    "RunConfig",
    "RunEndEvent",
    "RunMetadata",
    "RunScores",
    "RunStartEvent",
    "SafetyBoundary",
    "SafetyCategory",
    "ScoringRubric",
    "ScriptTurn",
    "SourceType",
    "Style",
    "Task",
    "TaskScore",
    "TokenUsage",
    "Turn",
]
