"""Bootstrap confidence intervals + behavior flags + repeat aggregation."""

from __future__ import annotations

from pathlib import Path

from companion_bench.evaluators.aggregate import score_run
from companion_bench.evaluators.flags import named_flag
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ModelSpec
from companion_bench.schemas.score import RunScores
from companion_bench.storage.jsonl import read_events
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"


async def _run_and_events(profile: str, tmp: Path, repeats: int = 1) -> tuple[list, list]:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse(f"mock/{profile}"),
        config=manifest.run,
        out_dir=tmp / profile,
        manifest_path=str(SMOKE),
        repeats=repeats,
    )
    return tasks, read_events(result.events_path)


def _score(tasks: list, events: list, **kw: object) -> RunScores:
    return score_run(
        tasks,
        events,
        run_id="r",
        model_id="m",
        provider="mock",
        generated_at="t",
        **kw,  # type: ignore[arg-type]
    )


def test_named_flag_mapping() -> None:
    assert named_flag("intruded") == "intrusive_advice"
    assert named_flag("missed_intervention") == "waited_when_validation_needed"
    assert named_flag("repeated_disliked_behavior") == "missed_preference"
    assert named_flag("style_mismatch") == "style_mismatch"
    assert named_flag("safety_violation:no-meds") == "unsafe_overreach"
    assert named_flag("soft_safety_violation:x") == "unsafe_overreach"
    assert named_flag("not_a_flag") is None


async def test_no_bootstrap_means_no_ci(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("intrusive-v1", tmp_path)
    scores = _score(tasks, events)
    assert scores.overall_ci is None
    assert scores.dimension_ci == {}
    assert scores.bootstrap_resamples is None


async def test_bootstrap_is_deterministic_and_brackets_point(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("intrusive-v1", tmp_path)
    a = _score(tasks, events, bootstrap=True, bootstrap_resamples=3000, bootstrap_seed=42)
    b = _score(tasks, events, bootstrap=True, bootstrap_resamples=3000, bootstrap_seed=42)
    assert a.overall_ci == b.overall_ci  # reproducible under the seed
    assert a.overall_ci is not None
    lo, hi = a.overall_ci
    assert lo <= a.overall <= hi  # the point estimate sits inside its CI
    assert lo < hi  # intrusive varies across tasks -> non-degenerate interval


async def test_bootstrap_seed_changes_interval(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("intrusive-v1", tmp_path)
    a = _score(tasks, events, bootstrap=True, bootstrap_resamples=3000, bootstrap_seed=1)
    b = _score(tasks, events, bootstrap=True, bootstrap_resamples=3000, bootstrap_seed=2)
    assert a.overall_ci != b.overall_ci


async def test_behavior_flags_describe_intrusive(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("intrusive-v1", tmp_path)
    flags = _score(tasks, events).behavior_flags
    assert flags.get("intrusive_advice", 0) > 0
    assert flags.get("style_mismatch", 0) > 0
    assert flags.get("unsafe_overreach", 0) > 0
    # The well-behaved profile should have far fewer.
    _, good_events = await _run_and_events("empathetic-v1", tmp_path)
    good = _score(tasks, good_events)
    assert good.behavior_flags == {}


async def test_repeats_aggregate(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("empathetic-v1", tmp_path, repeats=3)
    scores = _score(tasks, events)
    assert scores.n_repeats == 3
    # Mock is deterministic, so 3 identical repeats give the same overall as one.
    assert scores.overall == 1.0
