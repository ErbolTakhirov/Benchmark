"""The async run engine.

Each task's probes are inherently sequential (probe *n+1* sees what the model said at
probe *n*), but tasks run concurrently under a bounded semaphore. To keep artifacts
reproducible regardless of scheduling, events are collected per task and then written in
deterministic task/probe order with sequentially-assigned ids. Every model call becomes a
``model_call`` event; every failure (after retries) becomes a ``model_failure`` event —
failures are recorded, never hidden.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from companion_bench import __version__
from companion_bench.adapters.base import ChatAdapter, create_adapter
from companion_bench.runner.conversation import ConversationDriver
from companion_bench.runner.events import (
    model_call_event,
    model_failure_event,
    run_end_event,
    run_start_event,
)
from companion_bench.runner.manifest import Manifest
from companion_bench.schemas.model import ChatRequest, ChatResponse, ModelSpec
from companion_bench.schemas.run import (
    Event,
    ModelCallEvent,
    ModelFailureEvent,
    RunConfig,
    RunMetadata,
)
from companion_bench.schemas.task import Task
from companion_bench.storage.jsonl import EventWriter, write_model_json
from companion_bench.utils.errors import AdapterError
from companion_bench.utils.ids import IdFactory, make_run_id
from companion_bench.utils.timing import Clock, RealClock

__all__ = ["RunEngine", "RunResult"]


@dataclass(frozen=True)
class RunResult:
    """Outcome of a run: where artifacts landed and high-level counts."""

    run_id: str
    out_dir: Path
    events_path: Path
    metadata_path: Path
    metadata: RunMetadata
    n_tasks: int
    n_probes: int
    n_model_calls: int
    n_failures: int


class RunEngine:
    """Executes a manifest's tasks against a model, writing ``events.jsonl`` + ``run.json``.

    A :class:`Clock` and/or a pre-built adapter can be injected for deterministic, offline
    tests.
    """

    def __init__(
        self,
        *,
        clock: Clock | None = None,
        env: Mapping[str, str] | None = None,
        adapter: ChatAdapter | None = None,
    ) -> None:
        self._clock = clock or RealClock()
        self._env = env
        self._adapter_override = adapter

    async def run(
        self,
        *,
        manifest: Manifest,
        tasks: Sequence[Task],
        model: ModelSpec,
        config: RunConfig,
        out_dir: str | Path,
        manifest_path: str,
        run_id: str | None = None,
    ) -> RunResult:
        # Output dirs are created lazily by EventWriter / write_model_json (both mkdir
        # their parents), so there is no blocking filesystem call on the event loop here.
        out = Path(out_dir)
        run_id = run_id or make_run_id(manifest.name, model.ref, config.seed)
        tasks_to_run = list(tasks)[: config.limit] if config.limit else list(tasks)

        adapter = self._adapter_override or create_adapter(model.provider, self._env)
        try:
            semaphore = asyncio.Semaphore(config.concurrency)

            async def guarded(task: Task) -> list[Event]:
                async with semaphore:
                    return await self._run_task(run_id, task, model, config, adapter)

            per_task_events = await asyncio.gather(*(guarded(task) for task in tasks_to_run))
        finally:
            if self._adapter_override is None:
                await adapter.aclose()

        return self._write_artifacts(
            out=out,
            run_id=run_id,
            manifest=manifest,
            manifest_path=manifest_path,
            model=model,
            config=config,
            tasks_to_run=tasks_to_run,
            per_task_events=per_task_events,
        )

    # -- per-task / per-probe execution ------------------------------------
    async def _run_task(
        self,
        run_id: str,
        task: Task,
        model: ModelSpec,
        config: RunConfig,
        adapter: ChatAdapter,
    ) -> list[Event]:
        driver = ConversationDriver(task, model, config)
        events: list[Event] = []
        while (step := driver.next_probe()) is not None:
            response, error, attempts = await self._call_with_retries(adapter, step.request, config)
            if response is not None:
                events.append(
                    model_call_event(
                        run_id,
                        self._clock,
                        task.task_id,
                        step.probe.probe_id,
                        model,
                        step.request.messages,
                        response,
                        attempts,
                    )
                )
                driver.record_response(response.companion_turn)
            else:
                err = error if error is not None else AdapterError("unknown adapter failure")
                events.append(
                    model_failure_event(
                        run_id,
                        self._clock,
                        task.task_id,
                        step.probe.probe_id,
                        model,
                        step.request.messages,
                        err,
                        attempts,
                    )
                )
                driver.record_response(None)
        return events

    async def _call_with_retries(
        self, adapter: ChatAdapter, request: ChatRequest, config: RunConfig
    ) -> tuple[ChatResponse | None, BaseException | None, int]:
        attempts = 0
        while True:
            attempts += 1
            try:
                return await adapter.generate(request), None, attempts
            except AdapterError as exc:
                if exc.retryable and attempts <= config.max_retries:
                    await asyncio.sleep(0)
                    continue
                return None, exc, attempts
            except Exception as exc:  # record any failure, never hide it
                return None, exc, attempts

    # -- artifact assembly --------------------------------------------------
    def _write_artifacts(
        self,
        *,
        out: Path,
        run_id: str,
        manifest: Manifest,
        manifest_path: str,
        model: ModelSpec,
        config: RunConfig,
        tasks_to_run: list[Task],
        per_task_events: list[list[Event]],
    ) -> RunResult:
        ids = IdFactory(run_id)
        events_path = out / "events.jsonl"
        events_path.unlink(missing_ok=True)

        n_calls = n_failures = n_probes = 0
        start = run_start_event(
            run_id, self._clock, model, manifest.name, [t.task_id for t in tasks_to_run]
        )
        with EventWriter(events_path) as writer:
            start.event_id = ids.next_event_id()
            writer.write(start)
            for task_events in per_task_events:
                for event in task_events:
                    event.event_id = ids.next_event_id()
                    if isinstance(event, ModelCallEvent):
                        n_calls += 1
                        n_probes += 1
                    elif isinstance(event, ModelFailureEvent):
                        n_failures += 1
                        n_probes += 1
                    writer.write(event)
            end = run_end_event(
                run_id, self._clock, len(tasks_to_run), n_probes, n_calls, n_failures
            )
            end.event_id = ids.next_event_id()
            writer.write(end)

        metadata = RunMetadata(
            run_id=run_id,
            companion_bench_version=__version__,
            created_at=self._clock.now_iso(),
            manifest_path=manifest_path,
            manifest_name=manifest.name,
            model_id=model.ref,
            provider=model.provider,
            config=config,
            task_ids=tuple(t.task_id for t in tasks_to_run),
        )
        metadata_path = out / "run.json"
        write_model_json(metadata_path, metadata)

        return RunResult(
            run_id=run_id,
            out_dir=out,
            events_path=events_path,
            metadata_path=metadata_path,
            metadata=metadata,
            n_tasks=len(tasks_to_run),
            n_probes=n_probes,
            n_model_calls=n_calls,
            n_failures=n_failures,
        )
