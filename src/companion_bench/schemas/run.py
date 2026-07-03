"""Run artifacts: append-only events plus run configuration and metadata.

``events.jsonl`` is the canonical raw artifact — one JSON object per line, append-only,
covering the run lifecycle (start/end), every model call (with full transcript, parsed
envelope, latency, tokens, cost), and every failure. Derived scores live separately in
``scores.json`` (see ``schemas.score``); the two are intentionally not mixed so the raw
record stays immutable and re-scoring never rewrites history.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from companion_bench.schemas.model import ChatMessage, CompanionTurn, TokenUsage

__all__ = [
    "EVENT_ADAPTER",
    "BaseEvent",
    "Event",
    "EventType",
    "ModelCallEvent",
    "ModelFailureEvent",
    "RunConfig",
    "RunEndEvent",
    "RunMetadata",
    "RunStartEvent",
]


class EventType(StrEnum):
    RUN_START = "run_start"
    MODEL_CALL = "model_call"
    MODEL_FAILURE = "model_failure"
    RUN_END = "run_end"


class BaseEvent(BaseModel):
    """Fields common to every event."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    run_id: str
    timestamp: str
    event_type: EventType


class RunStartEvent(BaseEvent):
    event_type: Literal[EventType.RUN_START] = EventType.RUN_START
    model_id: str
    provider: str
    manifest_name: str
    task_ids: tuple[str, ...]


class ModelCallEvent(BaseEvent):
    """A successful model invocation at a single probe (raw transcript + metadata)."""

    event_type: Literal[EventType.MODEL_CALL] = EventType.MODEL_CALL
    task_id: str
    probe_id: str
    model_id: str
    provider: str
    input_messages: tuple[ChatMessage, ...]
    output_text: str
    output_message: CompanionTurn | None
    parsed: bool
    latency_ms: float | None = None
    token_usage: TokenUsage | None = None
    estimated_cost_usd: float | None = None
    attempts: int = 1
    retry_wait_ms: float = 0.0
    repeat_index: int = 0


class ModelFailureEvent(BaseEvent):
    """A failed model invocation. Failures are recorded, never silently dropped."""

    event_type: Literal[EventType.MODEL_FAILURE] = EventType.MODEL_FAILURE
    task_id: str
    probe_id: str
    model_id: str
    provider: str
    input_messages: tuple[ChatMessage, ...]
    error_type: str
    error_message: str
    retryable: bool
    attempts: int
    retry_wait_ms: float = 0.0
    repeat_index: int = 0


class RunEndEvent(BaseEvent):
    event_type: Literal[EventType.RUN_END] = EventType.RUN_END
    n_tasks: int
    n_probes: int
    n_model_calls: int
    n_failures: int
    wall_ms: float | None = None
    total_estimated_cost_usd: float | None = None
    total_tokens: int | None = None
    budget_exceeded: bool = False


Event = Annotated[
    RunStartEvent | ModelCallEvent | ModelFailureEvent | RunEndEvent,
    Field(discriminator="event_type"),
]

# Parse a single JSONL line into the correct concrete event type.
EVENT_ADAPTER: TypeAdapter[Event] = TypeAdapter(Event)


class RunConfig(BaseModel):
    """Execution knobs for a run (recorded in ``run.json`` for reproducibility)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    concurrency: int = Field(default=4, ge=1)
    max_retries: int = Field(default=2, ge=0)
    timeout_s: float = Field(default=60.0, gt=0.0)
    temperature: float = 0.0
    max_tokens: int | None = 512
    seed: int = 0
    limit: int | None = Field(default=None, ge=1)
    # Retry backoff (exponential + full jitter); deadline caps total wait per request.
    base_delay_s: float = Field(default=0.5, ge=0.0)
    max_delay_s: float = Field(default=8.0, ge=0.0)
    deadline_s: float | None = Field(default=None, gt=0.0)


class RunMetadata(BaseModel):
    """Everything needed to interpret and reproduce a run; written to ``run.json``."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    companion_bench_version: str
    created_at: str
    manifest_path: str
    manifest_name: str
    model_id: str
    provider: str
    config: RunConfig
    task_ids: tuple[str, ...]
    n_repeats: int = 1
    # Provenance (best-effort; ``None`` when unknown, never invented). ``git_commit`` records the
    # git checkout the run was launched from (the CompanionBench source in a dev/editable install);
    # pricing fields record which price table the run's cost numbers came from. Additive with
    # defaults so older ``run.json`` still validates.
    git_commit: str | None = None
    pricing_version: str | None = None
    pricing_as_of: str | None = None


class ModelRunRef(BaseModel):
    """A pointer to one model's sub-run within a model-set run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    ref: str
    slug: str
    run_id: str
    budget_exceeded: bool = False


class ModelSetRunIndex(BaseModel):
    """``modelset.json`` — the index of a model-set run's per-model sub-runs."""

    model_config = ConfigDict(extra="forbid")

    set_id: str | None
    manifest_name: str
    created_at: str
    models: tuple[ModelRunRef, ...]
