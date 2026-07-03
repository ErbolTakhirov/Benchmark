"""Experimental parse-quality metrics: additive to `overall`, and sensitive to parse failures."""

from __future__ import annotations

from pathlib import Path

from companion_bench.evaluators.aggregate import score_run
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ModelSpec
from companion_bench.schemas.run import Event, ModelCallEvent, ModelFailureEvent
from companion_bench.schemas.score import RunScores
from companion_bench.storage.jsonl import read_events
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"


async def _run_and_events(profile: str, tmp: Path) -> tuple[list, list[Event]]:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse(f"mock/{profile}"),
        config=manifest.run,
        out_dir=tmp / profile,
        manifest_path=str(SMOKE),
    )
    return tasks, read_events(result.events_path)


def _score(tasks: list, events: list[Event]) -> RunScores:
    return score_run(tasks, events, run_id="r", model_id="m", provider="mock", generated_at="t")


def _inject_one_failure(events: list[Event]) -> list[Event]:
    """Replace the first successful model call with a provider failure (unparsed probe)."""
    out: list[Event] = []
    replaced = False
    for event in events:
        if not replaced and isinstance(event, ModelCallEvent):
            out.append(
                ModelFailureEvent(
                    event_id=event.event_id,
                    run_id=event.run_id,
                    timestamp=event.timestamp,
                    task_id=event.task_id,
                    probe_id=event.probe_id,
                    model_id=event.model_id,
                    provider=event.provider,
                    input_messages=event.input_messages,
                    error_type="AdapterError",
                    error_message="simulated",
                    retryable=False,
                    attempts=1,
                    repeat_index=event.repeat_index,
                )
            )
            replaced = True
        else:
            out.append(event)
    return out


async def test_all_parsed_run_has_full_compliance(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("empathetic-v1", tmp_path)
    scores = _score(tasks, events)
    assert scores.format_compliance == 1.0
    # communication_score is `overall` over fully-parsed units, so at 100% compliance every unit is
    # kept and it equals `overall` exactly (by construction, not coincidence); parse-adjusted too.
    assert scores.communication_score == scores.overall
    assert scores.parse_adjusted_score == scores.overall


async def test_parse_failure_lowers_compliance_without_touching_overall(tmp_path: Path) -> None:
    tasks, events = await _run_and_events("empathetic-v1", tmp_path)
    clean = _score(tasks, events)
    degraded = _score(tasks, _inject_one_failure(events))
    # Format compliance drops; the experimental metrics never feed back into the canonical score.
    assert degraded.format_compliance is not None and degraded.format_compliance < 1.0
    assert degraded.communication_score is not None
    # communication_score excludes the whole failed task-unit, so it stays >= the parse-inclusive
    # overall (which still averages that dragged-down unit in).
    assert degraded.communication_score >= degraded.overall
    assert clean.format_compliance == 1.0
