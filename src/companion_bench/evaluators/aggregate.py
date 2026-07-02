"""Aggregate probe/task scores into a run-level result and a Markdown summary.

Reads the raw events back into per-probe outcomes, scores each task with the rule-based
evaluator, and rolls everything up by family and by dimension. With repeated runs it scores
each (task, repeat) and can compute **bootstrap 95% confidence intervals** by resampling those
task-score units. Also surfaces named behavior flags and renders ``summary.md``.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Literal

from companion_bench.evaluators.flags import behavior_flags
from companion_bench.evaluators.rule_based import (
    SCORER_TYPE,
    SCORING_VERSION,
    ProbeOutcome,
    score_task,
)
from companion_bench.schemas.run import Event, ModelCallEvent, ModelFailureEvent, RunMetadata
from companion_bench.schemas.score import RunScores, TaskScore
from companion_bench.schemas.task import Dimension, Family, Task

__all__ = ["build_outcomes", "build_outcomes_by_repeat", "render_summary", "score_run"]

_Outcomes = dict[str, dict[str, ProbeOutcome]]


def build_outcomes(events: list[Event]) -> _Outcomes:
    """Group model outputs into ``task_id -> probe_id -> outcome`` (last repeat wins)."""
    outcomes: _Outcomes = defaultdict(dict)
    for repeat in build_outcomes_by_repeat(events).values():
        for task_id, probes in repeat.items():
            outcomes[task_id].update(probes)
    return outcomes


def build_outcomes_by_repeat(events: list[Event]) -> dict[int, _Outcomes]:
    """Group outputs by ``repeat_index -> task_id -> probe_id -> outcome``."""
    by_repeat: dict[int, _Outcomes] = defaultdict(lambda: defaultdict(dict))
    for event in events:
        if isinstance(event, ModelCallEvent):
            by_repeat[event.repeat_index][event.task_id][event.probe_id] = ProbeOutcome(
                turn=event.output_message, parsed=event.parsed, output_text=event.output_text
            )
        elif isinstance(event, ModelFailureEvent):
            by_repeat[event.repeat_index][event.task_id][event.probe_id] = ProbeOutcome(
                turn=None, parsed=False, output_text=""
            )
    return by_repeat


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _mean_or_none(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return _mean(present) if present else None


def score_run(
    tasks: list[Task],
    events: list[Event],
    *,
    run_id: str,
    model_id: str,
    provider: str,
    generated_at: str,
    bootstrap: bool = False,
    bootstrap_resamples: int = 2000,
    bootstrap_seed: int = 0,
    bootstrap_cluster: Literal["task", "unit"] = "task",
) -> RunScores:
    """Score a run (across repeats), roll up by family/dimension, optionally bootstrap CIs.

    ``bootstrap_cluster`` picks the resampling unit: ``"task"`` (default, recommended) resamples
    whole tasks so repeats of one task are treated as the pseudo-replicates they are; ``"unit"``
    resamples every (task, repeat) unit (legacy — narrower, over-confident CIs).
    """
    by_repeat = build_outcomes_by_repeat(events)
    repeats = sorted(by_repeat) or [0]
    cost_by_task, total_cost, total_tokens, any_cost = _cost_rollup(events)

    # Score each task once per repeat — these (task, repeat) scores are the bootstrap units.
    units: list[TaskScore] = []
    per_task: dict[str, list[TaskScore]] = defaultdict(list)
    for repeat in repeats:
        outs = by_repeat.get(repeat, {})
        for task in tasks:
            ts = score_task(task, outs.get(task.task_id, {}))
            per_task[task.task_id].append(ts)
            units.append(ts)

    # Aggregate per task across repeats (mean); keep repeat 0's probe detail as representative.
    task_scores: list[TaskScore] = []
    for task in tasks:
        reps = per_task[task.task_id]
        total = _mean([t.total for t in reps])
        dim_means = {
            dim: _mean_or_none([t.dimension_means[dim] for t in reps]) for dim in Dimension
        }
        task_scores.append(
            TaskScore(
                task_id=task.task_id,
                family=task.family,
                probe_scores=reps[0].probe_scores,
                dimension_means=dim_means,
                total=total,
                pass_threshold=task.scoring_rubric.pass_threshold,
                passed=total >= task.scoring_rubric.pass_threshold,
                cost_usd=cost_by_task.get(task.task_id),
            )
        )

    # Run rollups over ALL (task, repeat) units.
    family_totals: dict[Family, list[float]] = defaultdict(list)
    dimension_values: dict[Dimension, list[float]] = defaultdict(list)
    for unit in units:
        family_totals[unit.family].append(unit.total)
        for dim, value in unit.dimension_means.items():
            if value is not None:
                dimension_values[dim].append(value)
    by_family = {family: _mean(totals) for family, totals in family_totals.items()}
    by_dimension: dict[Dimension, float | None] = {
        dim: (_mean(dimension_values[dim]) if dimension_values[dim] else None) for dim in Dimension
    }
    overall = _mean([unit.total for unit in units])
    n_passed = sum(1 for ts in task_scores if ts.passed)

    flag_counts: Counter[str] = Counter()
    for unit in units:
        flag_counts.update(behavior_flags(unit.probe_scores))

    overall_ci: tuple[float, float] | None = None
    dimension_ci: dict[Dimension, tuple[float, float] | None] = {}
    if bootstrap:
        # Each method needs >= 2 of its own resampling units: the unit bootstrap needs >= 2
        # (task, repeat) units; the task-clustered bootstrap needs >= 2 distinct tasks (a single
        # task gives a degenerate zero-width CI). Too few -> leave the CI as None, don't fake one.
        if bootstrap_cluster == "unit" and len(units) >= 2:
            overall_ci, dimension_ci = _bootstrap(units, bootstrap_resamples, bootstrap_seed)
        elif bootstrap_cluster == "task" and len(per_task) >= 2:
            overall_ci, dimension_ci = _bootstrap_clustered(
                per_task, bootstrap_resamples, bootstrap_seed
            )

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
        total_cost_usd=round(total_cost, 8) if any_cost else None,
        total_tokens=total_tokens or None,
        n_repeats=len(repeats),
        overall_ci=overall_ci,
        dimension_ci=dimension_ci,
        bootstrap_resamples=bootstrap_resamples if bootstrap else None,
        bootstrap_seed=bootstrap_seed if bootstrap else None,
        bootstrap_method=bootstrap_cluster if bootstrap else None,
        scoring_version=SCORING_VERSION,
        scorer_type=SCORER_TYPE,
        behavior_flags=dict(flag_counts.most_common()),
    )


def _cost_rollup(events: list[Event]) -> tuple[dict[str, float], float, int, bool]:
    """Sum estimated cost per task and total tokens from the model-call events."""
    cost_by_task: dict[str, float] = defaultdict(float)
    total_cost = 0.0
    total_tokens = 0
    any_cost = False
    for event in events:
        if not isinstance(event, ModelCallEvent):
            continue
        if event.estimated_cost_usd is not None:
            cost_by_task[event.task_id] += event.estimated_cost_usd
            total_cost += event.estimated_cost_usd
            any_cost = True
        if event.token_usage and event.token_usage.total_tokens:
            total_tokens += event.token_usage.total_tokens
    return dict(cost_by_task), total_cost, total_tokens, any_cost


def _bootstrap(
    units: list[TaskScore], resamples: int, seed: int
) -> tuple[tuple[float, float], dict[Dimension, tuple[float, float] | None]]:
    """Bootstrap 95% CIs by resampling the (task, repeat) task-score units with replacement."""
    rng = random.Random(seed)
    n = len(units)
    totals = [u.total for u in units]
    dim_vals = {dim: [u.dimension_means[dim] for u in units] for dim in Dimension}

    overall_samples: list[float] = []
    dim_samples: dict[Dimension, list[float]] = {dim: [] for dim in Dimension}
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        overall_samples.append(sum(totals[i] for i in idx) / n)
        for dim in Dimension:
            picked = [v for i in idx if (v := dim_vals[dim][i]) is not None]
            if picked:
                dim_samples[dim].append(sum(picked) / len(picked))

    overall_ci = _percentile_ci(overall_samples)
    dim_ci = {dim: (_percentile_ci(s) if len(s) >= 2 else None) for dim, s in dim_samples.items()}
    return overall_ci, dim_ci


def _bootstrap_clustered(
    per_task: dict[str, list[TaskScore]], resamples: int, seed: int
) -> tuple[tuple[float, float], dict[Dimension, tuple[float, float] | None]]:
    """Task-clustered bootstrap: resample whole tasks (not (task, repeat) units).

    Repeats of one task are pseudo-replicates — resampling them as if independent understates
    uncertainty. Clustering by task first collapses each task to its across-repeat mean, then
    resamples tasks with replacement, yielding wider, more honest CIs.
    """
    rng = random.Random(seed)
    task_ids = list(per_task)
    n = len(task_ids)
    task_total = {tid: _mean([t.total for t in reps]) for tid, reps in per_task.items()}
    task_dim: dict[Dimension, dict[str, float]] = {}
    for dim in Dimension:
        collapsed: dict[str, float] = {}
        for tid, reps in per_task.items():
            vals = [v for t in reps if (v := t.dimension_means[dim]) is not None]
            if vals:
                collapsed[tid] = sum(vals) / len(vals)
        task_dim[dim] = collapsed

    overall_samples: list[float] = []
    dim_samples: dict[Dimension, list[float]] = {dim: [] for dim in Dimension}
    for _ in range(resamples):
        picked = [task_ids[rng.randrange(n)] for _ in range(n)]
        overall_samples.append(sum(task_total[t] for t in picked) / n)
        for dim in Dimension:
            vals = [task_dim[dim][t] for t in picked if t in task_dim[dim]]
            if vals:
                dim_samples[dim].append(sum(vals) / len(vals))

    overall_ci = _percentile_ci(overall_samples)
    dim_ci = {dim: (_percentile_ci(s) if len(s) >= 2 else None) for dim, s in dim_samples.items()}
    return overall_ci, dim_ci


def _percentile_ci(samples: list[float], lo: float = 2.5, hi: float = 97.5) -> tuple[float, float]:
    ordered = sorted(samples)

    def pct(p: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        k = (len(ordered) - 1) * (p / 100.0)
        floor = int(k)
        ceil = min(floor + 1, len(ordered) - 1)
        return ordered[floor] + (ordered[ceil] - ordered[floor]) * (k - floor)

    return (round(pct(lo), 6), round(pct(hi), 6))


# --------------------------------------------------------------------------- rendering
def _provenance_block(metadata: RunMetadata, scores: RunScores) -> list[str]:
    """A compact, auditable record of exactly how these numbers were produced."""
    if scores.bootstrap_method:
        method = "task-clustered" if scores.bootstrap_method == "task" else "per-unit (legacy)"
        boot = f"{method}, {scores.bootstrap_resamples} resamples, seed {scores.bootstrap_seed}"
    else:
        boot = "none (point estimates only)"
    return [
        "## Provenance",
        "",
        f"- **CompanionBench:** v{metadata.companion_bench_version}",
        f"- **Scoring:** {scores.scorer_type or 'rule_based'} v{scores.scoring_version or 'n/a'} "
        "(rule-based, deterministic — not a human or calibrated-judge verdict)",
        f"- **Manifest:** `{metadata.manifest_name}` — `{metadata.manifest_path}` "
        f"({len(metadata.task_ids)} task(s))",
        f"- **Provider:** `{scores.provider}`  ·  **Model:** `{scores.model_id}`",
        f"- **Repeats:** {scores.n_repeats}  ·  **Run seed:** {metadata.config.seed}",
        f"- **Bootstrap:** {boot}",
        "",
    ]


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _ci(ci: tuple[float, float] | None) -> str:
    return "" if ci is None else f" [{ci[0]:.3f}, {ci[1]:.3f}]"


def render_summary(metadata: RunMetadata, scores: RunScores) -> str:
    """Render a Markdown summary of a scored run."""
    repeats_note = f" · {scores.n_repeats} repeat(s)" if scores.n_repeats > 1 else ""
    lines: list[str] = [
        f"# CompanionBench run summary — `{scores.run_id}`",
        "",
        f"- **Model:** `{scores.model_id}` (provider: `{scores.provider}`)",
        f"- **Manifest:** `{metadata.manifest_name}`",
        f"- **CompanionBench:** v{metadata.companion_bench_version}",
        f"- **Generated:** {scores.generated_at}{repeats_note}",
        f"- **Overall score:** **{scores.overall:.3f}**{_ci(scores.overall_ci)}  ·  "
        f"**{scores.n_passed}/{scores.n_tasks} tasks passed**",
        _cost_line(scores),
        "",
        "> ⚠️ If the model is a `mock/*` profile, these scores validate the **pipeline**, "
        "not model quality. The mock is a deterministic simulator.",
        "",
        *_provenance_block(metadata, scores),
        "## By dimension",
        "",
        "| Dimension | Mean | 95% CI |",
        "| --- | --- | --- |",
    ]
    for dim in Dimension:
        ci = scores.dimension_ci.get(dim)
        lines.append(
            f"| {dim.value} | {_fmt(scores.by_dimension.get(dim))} | "
            f"{'—' if ci is None else f'[{ci[0]:.3f}, {ci[1]:.3f}]'} |"
        )

    lines += ["", "## By family", "", "| Family | Mean |", "| --- | --- |"]
    for family in Family:
        if family in scores.by_family:
            lines.append(f"| {family.value} | {scores.by_family[family]:.3f} |")

    if scores.behavior_flags:
        lines += [
            "",
            "## Behavior flags (across all probes/repeats)",
            "",
            "| Flag | Count |",
            "| --- | --- |",
        ]
        for flag, count in scores.behavior_flags.items():
            lines.append(f"| {flag} | {count} |")

    lines += [
        "",
        "## Per task",
        "",
        "| Task | Family | Score | Pass | Cost (USD) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for ts in scores.task_scores:
        mark = "✅" if ts.passed else "❌"
        cost = "n/a" if ts.cost_usd is None else f"{ts.cost_usd:.6f}"
        lines.append(f"| `{ts.task_id}` | {ts.family.value} | {ts.total:.3f} | {mark} | {cost} |")

    lines.append("")
    return "\n".join(lines)


def _cost_line(scores: RunScores) -> str:
    if scores.total_cost_usd is None:
        tokens = f"{scores.total_tokens} tokens" if scores.total_tokens else "no token data"
        return f"- **Estimated cost:** n/a ({tokens}; price unknown for these models)"
    return f"- **Estimated cost:** ${scores.total_cost_usd:.6f} ({scores.total_tokens or 0} tokens)"
