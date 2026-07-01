"""Cost tracking + budget-guard tests (offline, mock-priced)."""

from __future__ import annotations

from pathlib import Path

import pytest

from companion_bench.config.pricing import PriceEntry, PricingTable, load_pricing
from companion_bench.evaluators.aggregate import render_summary, score_run
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ModelSpec
from companion_bench.schemas.run import ModelCallEvent
from companion_bench.storage.jsonl import read_events
from companion_bench.utils.errors import ConfigError
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"

# Price the mock model so cost flows end-to-end.
MOCK_PRICING = PricingTable(
    version="test",
    entries=(
        PriceEntry(
            provider="mock",
            model="empathetic-v1",
            input_usd_per_1m=1.0,
            output_usd_per_1m=2.0,
            source="test",
            as_of="2026-01-01",
        ),
    ),
)


def test_load_pricing_missing_path_raises_config_error(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"
    with pytest.raises(ConfigError, match="pricing file not found"):
        load_pricing(missing)


def test_load_pricing_invalid_yaml_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad-pricing.yaml"
    bad.write_text("version: test\nentries: [not-a-valid-entry]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid pricing config"):
        load_pricing(bad)


def test_load_pricing_bundled_default_still_loads() -> None:
    table = load_pricing(None)
    assert table.version
    assert len(table.entries) > 0


def test_pricing_cost_unknown_is_none() -> None:
    from companion_bench.schemas.model import TokenUsage

    assert (
        MOCK_PRICING.cost("mock", "unknown", TokenUsage(prompt_tokens=10, completion_tokens=5))
        is None
    )


async def test_cost_flows_into_events_and_scores(tmp_path: Path) -> None:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=manifest.run,
        out_dir=tmp_path / "run",
        manifest_path=str(SMOKE),
        pricing=MOCK_PRICING,
    )
    assert result.total_estimated_cost_usd is not None and result.total_estimated_cost_usd > 0
    assert result.total_tokens and result.total_tokens > 0
    assert not result.budget_exceeded

    events = read_events(result.events_path)
    calls = [e for e in events if isinstance(e, ModelCallEvent)]
    assert all(c.estimated_cost_usd is not None for c in calls)

    scores = score_run(
        tasks,
        events,
        run_id=result.run_id,
        model_id="mock/empathetic-v1",
        provider="mock",
        generated_at="2026-01-01T00:00:00Z",
    )
    assert scores.total_cost_usd is not None and scores.total_cost_usd > 0
    # Per-task costs sum to the run total (within rounding).
    per_task = sum(ts.cost_usd or 0.0 for ts in scores.task_scores)
    assert abs(per_task - scores.total_cost_usd) < 1e-6
    assert "$" in render_summary(result.metadata, scores)


async def test_budget_guard_aborts_run(tmp_path: Path) -> None:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=manifest.run,
        out_dir=tmp_path / "run",
        manifest_path=str(SMOKE),
        pricing=MOCK_PRICING,
        max_cost_usd=0.0,  # zero budget => stop before any call
    )
    assert result.budget_exceeded is True
    assert result.n_model_calls == 0


async def test_no_budget_runs_everything(tmp_path: Path) -> None:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=manifest.run,
        out_dir=tmp_path / "run",
        manifest_path=str(SMOKE),
        pricing=MOCK_PRICING,
        max_cost_usd=1000.0,  # generous
    )
    assert result.budget_exceeded is False
    assert result.n_model_calls == 14
