"""Event constructors.

Thin builders that stamp each event with the current clock time and leave ``event_id``
blank — the engine assigns ids in a deterministic post-order after all tasks finish, so
ids and ordering are reproducible regardless of concurrent scheduling.
"""

from __future__ import annotations

from collections.abc import Sequence

from companion_bench.schemas.model import ChatMessage, ChatResponse, ModelSpec
from companion_bench.schemas.run import (
    ModelCallEvent,
    ModelFailureEvent,
    RunEndEvent,
    RunStartEvent,
)
from companion_bench.utils.errors import AdapterError
from companion_bench.utils.secrets import collect_secret_values, redact
from companion_bench.utils.timing import Clock

__all__ = [
    "model_call_event",
    "model_failure_event",
    "run_end_event",
    "run_start_event",
]


def run_start_event(
    run_id: str, clock: Clock, model: ModelSpec, manifest_name: str, task_ids: Sequence[str]
) -> RunStartEvent:
    return RunStartEvent(
        event_id="",
        run_id=run_id,
        timestamp=clock.now_iso(),
        model_id=model.ref,
        provider=model.provider,
        manifest_name=manifest_name,
        task_ids=tuple(task_ids),
    )


def model_call_event(
    run_id: str,
    clock: Clock,
    task_id: str,
    probe_id: str,
    model: ModelSpec,
    input_messages: Sequence[ChatMessage],
    response: ChatResponse,
    attempts: int,
    *,
    retry_wait_ms: float = 0.0,
    cost_usd: float | None = None,
) -> ModelCallEvent:
    # The engine is authoritative on cost (pricing table, or the adapter value when no table);
    # ``cost_usd`` already reflects that decision, so do not second-guess it here.
    return ModelCallEvent(
        event_id="",
        run_id=run_id,
        timestamp=clock.now_iso(),
        task_id=task_id,
        probe_id=probe_id,
        model_id=model.ref,
        provider=model.provider,
        input_messages=tuple(input_messages),
        output_text=response.content,
        output_message=response.companion_turn,
        parsed=response.parsed,
        latency_ms=response.latency_ms,
        token_usage=response.token_usage,
        estimated_cost_usd=cost_usd,
        attempts=attempts,
        retry_wait_ms=retry_wait_ms,
    )


def model_failure_event(
    run_id: str,
    clock: Clock,
    task_id: str,
    probe_id: str,
    model: ModelSpec,
    input_messages: Sequence[ChatMessage],
    error: BaseException,
    attempts: int,
    *,
    retry_wait_ms: float = 0.0,
) -> ModelFailureEvent:
    retryable = error.retryable if isinstance(error, AdapterError) else False
    # Defense-in-depth: a hostile/misconfigured endpoint could echo an auth header into its
    # error body, which an adapter embeds via response.text[:300]. Redact before persisting.
    error_message = redact(str(error), collect_secret_values())
    return ModelFailureEvent(
        event_id="",
        run_id=run_id,
        timestamp=clock.now_iso(),
        task_id=task_id,
        probe_id=probe_id,
        model_id=model.ref,
        provider=model.provider,
        input_messages=tuple(input_messages),
        error_type=type(error).__name__,
        error_message=error_message,
        retryable=retryable,
        attempts=attempts,
        retry_wait_ms=retry_wait_ms,
    )


def run_end_event(
    run_id: str,
    clock: Clock,
    n_tasks: int,
    n_probes: int,
    n_model_calls: int,
    n_failures: int,
    *,
    total_estimated_cost_usd: float | None = None,
    total_tokens: int | None = None,
    budget_exceeded: bool = False,
) -> RunEndEvent:
    return RunEndEvent(
        event_id="",
        run_id=run_id,
        timestamp=clock.now_iso(),
        n_tasks=n_tasks,
        n_probes=n_probes,
        n_model_calls=n_model_calls,
        n_failures=n_failures,
        total_estimated_cost_usd=total_estimated_cost_usd,
        total_tokens=total_tokens,
        budget_exceeded=budget_exceeded,
    )
