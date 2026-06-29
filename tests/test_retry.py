"""Deterministic retry/backoff + rate-limiter tests (no real sleeps)."""

from __future__ import annotations

from pathlib import Path

from companion_bench.adapters.base import ChatAdapter
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.runner.retry import RateLimiter, backoff_delay
from companion_bench.schemas.model import ChatRequest, ChatResponse, ModelSpec
from companion_bench.schemas.run import ModelFailureEvent, RunConfig
from companion_bench.storage.jsonl import read_events
from companion_bench.utils.errors import ProviderTimeoutError
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"


# --------------------------------------------------------------------------- backoff
def test_backoff_is_deterministic_and_bounded() -> None:
    cfg = RunConfig(base_delay_s=1.0, max_delay_s=8.0, seed=0)
    d1 = backoff_delay(cfg, 1, None, task_id="t", probe_id="p")
    assert d1 == backoff_delay(cfg, 1, None, task_id="t", probe_id="p")  # reproducible
    assert 0.0 <= d1 < 1.0  # full jitter within base*2^0
    assert 0.0 <= backoff_delay(cfg, 2, None, task_id="t", probe_id="p") < 2.0
    assert 0.0 <= backoff_delay(cfg, 10, None, task_id="t", probe_id="p") < 8.0  # capped


def test_backoff_differs_by_probe_and_attempt() -> None:
    cfg = RunConfig(base_delay_s=1.0, seed=0)
    assert backoff_delay(cfg, 1, None, task_id="t", probe_id="a") != backoff_delay(
        cfg, 1, None, task_id="t", probe_id="b"
    )


def test_retry_after_raises_the_floor() -> None:
    cfg = RunConfig(base_delay_s=1.0, max_delay_s=8.0, seed=0)
    assert backoff_delay(cfg, 1, 5.0, task_id="t", probe_id="p") >= 5.0


# --------------------------------------------------------------------------- rate limiter
async def test_rate_limiter_noop_when_unset() -> None:
    sleeps: list[float] = []
    rl = RateLimiter(None, lambda d: _record(sleeps, d))
    await rl.acquire()
    await rl.acquire()
    assert sleeps == []


async def test_rate_limiter_spaces_requests() -> None:
    sleeps: list[float] = []
    rl = RateLimiter(2.0, lambda d: _record(sleeps, d))  # 0.5s interval
    await rl.acquire()  # first: no wait
    await rl.acquire()
    await rl.acquire()
    assert sleeps == [0.5, 0.5]


async def _record(sink: list[float], delay: float) -> None:
    sink.append(delay)


# --------------------------------------------------------------------------- engine integration
class _AlwaysTimeout(ChatAdapter):
    provider = "mock"

    async def generate(self, request: ChatRequest) -> ChatResponse:
        raise ProviderTimeoutError("simulated timeout", provider="mock")


def _single_probe_task() -> object:
    _, tasks = load_manifest_and_tasks(SMOKE)
    return next(t for t in tasks if len(t.probes) == 1)


async def test_engine_retries_with_recorded_backoff(tmp_path: Path) -> None:
    manifest, _ = load_manifest_and_tasks(SMOKE)
    task = _single_probe_task()
    sleeps: list[float] = []
    config = manifest.run.model_copy(update={"max_retries": 2, "base_delay_s": 1.0})
    engine = RunEngine(
        clock=FrozenClock(), adapter=_AlwaysTimeout(), sleep=lambda d: _record(sleeps, d)
    )
    result = await engine.run(
        manifest=manifest,
        tasks=[task],  # type: ignore[list-item]
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=config,
        out_dir=tmp_path / "r",
        manifest_path=str(SMOKE),
    )
    assert result.n_failures == 1
    failures = [e for e in read_events(result.events_path) if isinstance(e, ModelFailureEvent)]
    assert len(failures) == 1
    fail = failures[0]
    assert fail.attempts == 3  # 1 initial + 2 retries
    assert len(sleeps) == 2  # two backoff waits
    # Deterministic and consistent with what's recorded on the event.
    assert fail.retry_wait_ms == sum(sleeps) * 1000.0
    expected = [
        backoff_delay(config, 1, None, task_id=fail.task_id, probe_id=fail.probe_id),
        backoff_delay(config, 2, None, task_id=fail.task_id, probe_id=fail.probe_id),
    ]
    assert sleeps == expected


async def test_deadline_stops_retries_early(tmp_path: Path) -> None:
    manifest, _ = load_manifest_and_tasks(SMOKE)
    task = _single_probe_task()
    sleeps: list[float] = []
    # A tiny deadline: the first backoff already exceeds it, so no retry happens.
    config = manifest.run.model_copy(
        update={"max_retries": 5, "base_delay_s": 1.0, "deadline_s": 0.0001}
    )
    engine = RunEngine(
        clock=FrozenClock(), adapter=_AlwaysTimeout(), sleep=lambda d: _record(sleeps, d)
    )
    result = await engine.run(
        manifest=manifest,
        tasks=[task],  # type: ignore[list-item]
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=config,
        out_dir=tmp_path / "r",
        manifest_path=str(SMOKE),
    )
    failures = [e for e in read_events(result.events_path) if isinstance(e, ModelFailureEvent)]
    assert failures[0].attempts == 1
    assert sleeps == []
