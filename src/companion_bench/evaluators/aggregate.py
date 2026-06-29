"""Aggregate probe/task scores into a run-level result and a Markdown summary.

Reads the raw events back into per-probe outcomes, scores each task with the rule-based
evaluator, and rolls everything up by family and by dimension. Also renders the
human-readable ``summary.md``.
"""

from __future__ import annotations

from collections import defaultdict

from companion_bench.evaluators.rule_based import ProbeOutcome, score_task
from companion_bench.schemas.run import Event, ModelCallEvent, ModelFailureEvent, RunMetadata
from companion_bench.schemas.score import RunScores, TaskScore
from companion_bench.schemas.task import Dimension, Family, Task

__all__ = ["build_outcomes", "render_summary", "score_run"]


def build_outcomes(events: list[Event]) -> dict[str, dict[str, ProbeOutcome]]:
    """Group model outputs from the event log into ``task_id -> probe_id -> outcome``."""
    outcomes: dict[str, dict[str, ProbeOutcome]] = defaultdict(dict)
    for event in events:
        if isinstance(event, ModelCallEvent):
            outcomes[event.task_id][event.probe_id] = ProbeOutcome(
                turn=event.output_message,
                parsed=event.parsed,
                output_text=event.output_text,
            )
        elif isinstance(event, ModelFailureEvent):
            outcomes[event.task_id][event.probe_id] = ProbeOutcome(
                turn=None, parsed=False, output_text=""
            )
    return outcomes


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def score_run(
    tasks: list[Task],
    events: list[Event],
    *,
    run_id: str,
    model_id: str,
    provider: str,
    generated_at: str,
) -> RunScores:
    """Score every task in a run and roll up by family and dimension."""
    outcomes = build_outcomes(events)
    task_scores: list[TaskScore] = [
        score_task(task, outcomes.get(task.task_id, {})) for task in tasks
    ]

    family_totals: dict[Family, list[float]] = defaultdict(list)
    dimension_values: dict[Dimension, list[float]] = defaultdict(list)
    for ts in task_scores:
        family_totals[ts.family].append(ts.total)
        for dim, value in ts.dimension_means.items():
            if value is not None:
                dimension_values[dim].append(value)

    by_family = {family: _mean(totals) for family, totals in family_totals.items()}
    by_dimension: dict[Dimension, float | None] = {
        dim: (_mean(dimension_values[dim]) if dimension_values[dim] else None) for dim in Dimension
    }
    overall = _mean([ts.total for ts in task_scores])
    n_passed = sum(1 for ts in task_scores if ts.passed)

    return RunScores(
        run_id=run_id,
        model_id=model_id,
        provider=provider,
        generated_at=generated_at,
        task_scores=tuple(task_scores),
        by_family=by_family,
        by_dimension=by_dimension,
        overall=overall,
        n_tasks=len(task_scores),
        n_passed=n_passed,
    )


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def render_summary(metadata: RunMetadata, scores: RunScores) -> str:
    """Render a Markdown summary of a scored run."""
    lines: list[str] = [
        f"# CompanionBench run summary — `{scores.run_id}`",
        "",
        f"- **Model:** `{scores.model_id}` (provider: `{scores.provider}`)",
        f"- **Manifest:** `{metadata.manifest_name}`",
        f"- **CompanionBench:** v{metadata.companion_bench_version}",
        f"- **Generated:** {scores.generated_at}",
        f"- **Overall score:** **{scores.overall:.3f}**  ·  "
        f"**{scores.n_passed}/{scores.n_tasks} tasks passed**",
        "",
        "> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, "
        "not model quality. The mock is a deterministic simulator.",
        "",
        "## By dimension",
        "",
        "| Dimension | Mean |",
        "| --- | --- |",
    ]
    for dim in Dimension:
        lines.append(f"| {dim.value} | {_fmt(scores.by_dimension.get(dim))} |")

    lines += ["", "## By family", "", "| Family | Mean |", "| --- | --- |"]
    for family in Family:
        if family in scores.by_family:
            lines.append(f"| {family.value} | {scores.by_family[family]:.3f} |")

    lines += [
        "",
        "## Per task",
        "",
        "| Task | Family | Score | Pass |",
        "| --- | --- | --- | --- |",
    ]
    for ts in scores.task_scores:
        mark = "✅" if ts.passed else "❌"
        lines.append(f"| `{ts.task_id}` | {ts.family.value} | {ts.total:.3f} | {mark} |")

    lines.append("")
    return "\n".join(lines)
