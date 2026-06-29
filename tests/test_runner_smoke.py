"""End-to-end runner tests against the mock model (offline, deterministic)."""

from __future__ import annotations

from pathlib import Path

from companion_bench.adapters.base import ChatAdapter
from companion_bench.evaluators.aggregate import score_run
from companion_bench.runner.engine import RunEngine, RunResult
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ChatRequest, ChatResponse, ModelSpec
from companion_bench.schemas.score import RunScores
from companion_bench.schemas.task import Dimension
from companion_bench.storage.jsonl import read_events
from companion_bench.utils.errors import ProviderTimeoutError
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"


async def run_profile(profile: str, out: Path) -> RunResult:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    return await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse(f"mock/{profile}"),
        config=manifest.run,
        out_dir=out,
        manifest_path=str(SMOKE),
    )


def score_result(result: RunResult, profile: str) -> RunScores:
    _, tasks = load_manifest_and_tasks(SMOKE)
    events = read_events(result.events_path)
    return score_run(
        tasks,
        events,
        run_id=result.run_id,
        model_id=f"mock/{profile}",
        provider="mock",
        generated_at="2026-01-01T00:00:00Z",
    )


async def test_smoke_runs_end_to_end(tmp_path: Path) -> None:
    result = await run_profile("empathetic-v1", tmp_path / "run")
    assert result.n_tasks == 8
    assert result.n_probes == 14
    assert result.n_model_calls == 14
    assert result.n_failures == 0
    assert result.metadata_path.is_file()

    events = read_events(result.events_path)
    # run_start + 14 model_call + run_end
    assert len(events) == 16
    assert events[0].event_type.value == "run_start"
    assert events[-1].event_type.value == "run_end"
    # Event ids are unique and sequential.
    ids = [e.event_id for e in events]
    assert len(set(ids)) == len(ids)


async def test_run_is_byte_stable_with_frozen_clock(tmp_path: Path) -> None:
    first = await run_profile("empathetic-v1", tmp_path / "a")
    second = await run_profile("empathetic-v1", tmp_path / "b")
    assert first.run_id == second.run_id
    assert (tmp_path / "a" / "events.jsonl").read_text() == (
        tmp_path / "b" / "events.jsonl"
    ).read_text()


async def test_profiles_are_ordered_empathetic_best(tmp_path: Path) -> None:
    empathetic = score_result(await run_profile("empathetic-v1", tmp_path / "e"), "empathetic-v1")
    intrusive = score_result(await run_profile("intrusive-v1", tmp_path / "i"), "intrusive-v1")
    silent = score_result(await run_profile("silent-v1", tmp_path / "s"), "silent-v1")

    assert empathetic.overall == 1.0
    assert empathetic.n_passed == 8
    # The attuned companion beats both the intrusive and the passive one.
    assert empathetic.overall > intrusive.overall
    assert empathetic.overall > silent.overall
    # A harmful proactive model scores below a merely passive one.
    assert intrusive.overall < silent.overall
    # Intrusive repeats disliked behaviors, flooring adaptation.
    assert intrusive.by_dimension[Dimension.ADAPTATION] == 0.0


class _FailingAdapter(ChatAdapter):
    provider = "mock"

    async def generate(self, request: ChatRequest) -> ChatResponse:
        raise ProviderTimeoutError("simulated timeout", provider="mock")


async def test_failures_are_recorded_not_hidden(tmp_path: Path) -> None:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    one_task = [tasks[0]]
    config = manifest.run.model_copy(update={"max_retries": 0})
    engine = RunEngine(clock=FrozenClock(), adapter=_FailingAdapter())
    result = await engine.run(
        manifest=manifest,
        tasks=one_task,
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=config,
        out_dir=tmp_path / "fail",
        manifest_path=str(SMOKE),
    )
    assert result.n_model_calls == 0
    assert result.n_failures == len(one_task[0].probes)
    failures = [e for e in read_events(result.events_path) if e.event_type.value == "model_failure"]
    assert failures and failures[0].error_type == "ProviderTimeoutError"  # type: ignore[union-attr]
