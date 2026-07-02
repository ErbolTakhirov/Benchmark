"""LLM-as-judge runner — opt-in, live-gated, and stored in its own artifacts.

Two paths share one interface:

- ``mock`` provider → :func:`run_mock_judge`, a deterministic **offline simulator** that mirrors the
  rule-based signal. It validates the judge *pipeline* (prompting, parsing, calibration), NOT judge
  quality — exactly like the mock model validates the run pipeline.
- any real provider → :func:`run_live_judge`, which calls the provider adapter, parses **strict**
  JSON, records malformed output as an explicit failure (never coerced to a high score), and stops
  at a cost cap. The CLI gates this behind ``--live`` + ``COMPANIONBENCH_LIVE=1`` + confirmation.

Judge output never touches the rule-based ``scores.json``; it is written to ``judge_scores.json`` /
``judge_events.jsonl``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from companion_bench.adapters.base import create_adapter
from companion_bench.config.pricing import PricingTable
from companion_bench.config.providers import ProviderSettings
from companion_bench.evaluators.calibration import response_to_outcome
from companion_bench.evaluators.judge_prompts import (
    JUDGE_PROMPT_VERSION,
    build_judge_messages,
    parse_judge_verdict,
)
from companion_bench.evaluators.rule_based import effective_weights, score_probe
from companion_bench.schemas.gold import GoldResponse
from companion_bench.schemas.judge import JudgeProbeResult, JudgeRunScores, JudgeVerdict
from companion_bench.schemas.model import ChatMessage, ChatRequest, ModelSpec, Role
from companion_bench.schemas.task import Dimension, ProbeTurn, Task
from companion_bench.storage.jsonl import write_model_json

__all__ = [
    "JudgeItem",
    "build_items_from_responses",
    "mock_verdict",
    "run_live_judge",
    "run_mock_judge",
    "write_judge_artifacts",
]


@dataclass(frozen=True)
class JudgeItem:
    """One response to be judged, with the task context needed to build the prompt."""

    response_id: str
    task: Task
    probe: ProbeTurn
    response: GoldResponse


def build_items_from_responses(
    responses: list[GoldResponse], tasks_by_id: dict[str, Task]
) -> tuple[list[JudgeItem], list[str]]:
    """Pair each sanitized response with its task/probe; collect warnings for unknown ids."""
    items: list[JudgeItem] = []
    warnings: list[str] = []
    for resp in responses:
        task = tasks_by_id.get(resp.task_id)
        if task is None:
            warnings.append(f"response {resp.response_id}: unknown task_id {resp.task_id!r}")
            continue
        probe = next((p for p in task.probes if p.probe_id == resp.probe_id), None)
        if probe is None:
            warnings.append(f"response {resp.response_id}: unknown probe_id {resp.probe_id!r}")
            continue
        items.append(JudgeItem(resp.response_id, task, probe, resp))
    return items, warnings


def _by_dimension(results: list[JudgeProbeResult]) -> dict[Dimension, float | None]:
    acc: dict[Dimension, list[float]] = {d: [] for d in Dimension}
    for r in results:
        if r.verdict is not None:
            for dim, v in r.verdict.dimension_scores.items():
                acc[dim].append(v)
    return {d: (sum(vs) / len(vs) if vs else None) for d, vs in acc.items()}


def mock_verdict(item: JudgeItem) -> JudgeVerdict:
    """Deterministic offline verdict: the rule-based per-dimension signal, gently hedged.

    Applies a fixed monotone squish toward the middle so it is not byte-identical to the rule
    scores (exercising the calibration/agreement code) while staying fully deterministic.
    """
    ps = score_probe(
        item.task, item.probe, response_to_outcome(item.response), effective_weights(item.task)
    )
    scores = {
        dim: max(0.0, min(1.0, round(0.85 * ds.value + 0.075, 3)))
        for dim, ds in ps.dimensions.items()
        if ds.value is not None
    }
    return JudgeVerdict(
        dimension_scores=scores,
        confidence=0.6,
        rationale="(mock judge) deterministic pipeline simulator mirroring the rule-based signal.",
        uncertainty_notes="Mock judge — not a real model verdict; for offline pipeline validation.",
    )


def run_mock_judge(
    items: list[JudgeItem], *, judge_run_id: str, generated_at: str, judge_model: str = "demo"
) -> JudgeRunScores:
    """Offline deterministic judge over the given items."""
    results = [
        JudgeProbeResult(
            response_id=it.response_id,
            task_id=it.task.task_id,
            probe_id=it.response.probe_id,
            model_id=it.response.model_id,
            parsed=True,
            verdict=mock_verdict(it),
            raw_excerpt="(mock judge; no raw model output)",
        )
        for it in items
    ]
    return JudgeRunScores(
        judge_run_id=judge_run_id,
        judge_provider="mock",
        judge_model=judge_model,
        judge_prompt_version=JUDGE_PROMPT_VERSION,
        generated_at=generated_at,
        source="mock",
        probe_results=tuple(results),
        by_dimension=_by_dimension(results),
        n_probes=len(results),
        n_failed=0,
        total_cost_usd=0.0,
    )


async def run_live_judge(
    items: list[JudgeItem],
    *,
    provider: str,
    model: str,
    judge_run_id: str,
    generated_at: str,
    env: Mapping[str, str] | None = None,
    settings: ProviderSettings | None = None,
    pricing: PricingTable | None = None,
    max_cost_usd: float | None = None,
) -> JudgeRunScores:
    """Live judge over the given items via a real provider adapter (caller enforces the live gate)."""
    adapter = create_adapter(provider, env, settings=settings)
    results: list[JudgeProbeResult] = []
    total_cost = 0.0
    priced_any = False
    try:
        for it in items:
            if max_cost_usd is not None and total_cost >= max_cost_usd:
                results.append(
                    JudgeProbeResult(
                        response_id=it.response_id,
                        task_id=it.task.task_id,
                        probe_id=it.response.probe_id,
                        model_id=it.response.model_id,
                        parsed=False,
                        error="cost budget reached before this item; not judged",
                    )
                )
                continue
            messages = tuple(
                ChatMessage(role=Role(m["role"]), content=m["content"])
                for m in build_judge_messages(it.task, it.probe, it.response)
            )
            request = ChatRequest(
                model=ModelSpec(provider=provider, model=model),
                messages=messages,
                temperature=0.0,
                response_format="json_object",
                simulation_context=None,
            )
            try:
                resp = await adapter.generate(request)
            except Exception as exc:  # record every failure, never hide it
                results.append(
                    JudgeProbeResult(
                        response_id=it.response_id,
                        task_id=it.task.task_id,
                        probe_id=it.response.probe_id,
                        model_id=it.response.model_id,
                        parsed=False,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue
            cost = (
                pricing.cost(provider, model, resp.token_usage)
                if pricing is not None
                else resp.estimated_cost_usd
            )
            if cost is not None:
                total_cost += cost
                priced_any = True
            verdict = parse_judge_verdict(resp.content)
            results.append(
                JudgeProbeResult(
                    response_id=it.response_id,
                    task_id=it.task.task_id,
                    probe_id=it.response.probe_id,
                    model_id=it.response.model_id,
                    parsed=verdict is not None,
                    verdict=verdict,
                    error=None
                    if verdict is not None
                    else "judge output did not parse to a verdict",
                    raw_excerpt=resp.content[:300],
                )
            )
    finally:
        await adapter.aclose()

    return JudgeRunScores(
        judge_run_id=judge_run_id,
        judge_provider=provider,
        judge_model=model,
        judge_prompt_version=JUDGE_PROMPT_VERSION,
        generated_at=generated_at,
        source="live",
        probe_results=tuple(results),
        by_dimension=_by_dimension(results),
        n_probes=len(results),
        n_failed=sum(1 for r in results if r.verdict is None),
        total_cost_usd=round(total_cost, 8) if priced_any else None,
    )


def write_judge_artifacts(out_dir: str | Path, scores: JudgeRunScores) -> tuple[Path, Path]:
    """Write ``judge_scores.json`` + ``judge_events.jsonl`` (separate from rule-based artifacts)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scores_path = out / "judge_scores.json"
    events_path = out / "judge_events.jsonl"
    write_model_json(scores_path, scores)
    with events_path.open("w", encoding="utf-8") as fh:
        for r in scores.probe_results:
            fh.write(r.model_dump_json() + "\n")
    return scores_path, events_path
