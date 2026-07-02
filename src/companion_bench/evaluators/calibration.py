"""Calibrate rule-based scores (and, optionally, an LLM judge) against human gold labels.

Calibration answers "does the automated number track what people actually valued?" — it never
changes the automated number. Human ratings (1-5) are normalized to ``[0, 1]`` via ``(r-1)/4`` and
averaged across annotators into a per-item consensus; that consensus is compared, per dimension,
against the rule-based (or judge) value for the *same* response. A pilot this small is a workflow
proof, not a statistically definitive result.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from companion_bench.evaluators.agreement import pearson, spearman
from companion_bench.evaluators.rule_based import ProbeOutcome, effective_weights, score_probe
from companion_bench.schemas.gold import GoldLabel, GoldResponse, OverallPreference
from companion_bench.schemas.judge import JudgeRunScores
from companion_bench.schemas.model import CompanionTurn
from companion_bench.schemas.task import Dimension, Task

__all__ = [
    "CalibrationReport",
    "DimensionCalibration",
    "calibrate_judge_vs_gold",
    "calibrate_rules_vs_gold",
    "gold_consensus",
    "render_calibration_md",
    "response_to_outcome",
    "rule_values",
]

_PASS_THRESHOLD = 0.6  # default task pass line; used for the accept/reject categorical view


def response_to_outcome(resp: GoldResponse) -> ProbeOutcome:
    """Rebuild a scoring :class:`ProbeOutcome` from a sanitized gold response."""
    if resp.parsed and resp.decision is not None:
        turn = CompanionTurn(
            decision=resp.decision,
            message=resp.message,
            target=resp.target,
            style=resp.style,
            ask_permission=resp.ask_permission,
        )
        return ProbeOutcome(turn=turn, parsed=True, output_text=resp.output_text or resp.message)
    return ProbeOutcome(turn=None, parsed=False, output_text=resp.output_text)


def _norm(rating: float) -> float:
    """Normalize a 1-5 Likert rating to [0, 1]."""
    return (rating - 1.0) / 4.0


def gold_consensus(
    labels: list[GoldLabel],
) -> tuple[dict[str, dict[Dimension, float]], dict[str, bool]]:
    """Per-response consensus: mean normalized dimension ratings + majority accept flag."""
    by_resp: dict[str, list[GoldLabel]] = defaultdict(list)
    for lab in labels:
        by_resp[lab.response_id].append(lab)
    dim_consensus: dict[str, dict[Dimension, float]] = {}
    accept: dict[str, bool] = {}
    for rid, labs in by_resp.items():
        dims: dict[Dimension, float] = {}
        for dim in Dimension:
            vals = [
                _norm(dr.rating)
                for lab in labs
                if (dr := lab.dimensions.get(dim)) is not None and dr.rating is not None
            ]
            if vals:
                dims[dim] = sum(vals) / len(vals)
        dim_consensus[rid] = dims
        n_accept = sum(1 for lab in labs if lab.overall_preference is OverallPreference.ACCEPT)
        accept[rid] = n_accept * 2 > len(labs)  # strict majority accept
    return dim_consensus, accept


def rule_values(
    responses: list[GoldResponse], tasks_by_id: dict[str, Task]
) -> tuple[dict[str, dict[Dimension, float]], dict[str, float], list[str]]:
    """Score each response with the rule-based scorer; return per-dim values + probe total."""
    dim_values: dict[str, dict[Dimension, float]] = {}
    overall: dict[str, float] = {}
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
        ps = score_probe(task, probe, response_to_outcome(resp), effective_weights(task))
        dim_values[resp.response_id] = {
            dim: ds.value for dim, ds in ps.dimensions.items() if ds.value is not None
        }
        overall[resp.response_id] = ps.total
    return dim_values, overall, warnings


def _judge_values(
    judge: JudgeRunScores,
) -> tuple[dict[str, dict[Dimension, float]], dict[str, float]]:
    dim_values: dict[str, dict[Dimension, float]] = {}
    overall: dict[str, float] = {}
    for r in judge.probe_results:
        if r.verdict is None:
            continue
        dim_values[r.response_id] = dict(r.verdict.dimension_scores)
        vals = list(r.verdict.dimension_scores.values())
        if vals:
            overall[r.response_id] = sum(vals) / len(vals)
    return dim_values, overall


@dataclass(frozen=True)
class DimensionCalibration:
    dimension: Dimension
    n: int
    mae: float | None
    pearson: float | None
    spearman: float | None


@dataclass(frozen=True)
class CalibrationReport:
    label: str  # e.g. "rule-vs-gold"
    a_name: str
    b_name: str
    n_items: int
    per_dimension: dict[Dimension, DimensionCalibration]
    overall_accept_agreement: float | None
    disagreements: list[
        tuple[str, Dimension, float, float]
    ]  # (response_id, dim, a, b) top by |diff|
    caveats: list[str] = field(default_factory=list)


def _compare(
    a_dims: dict[str, dict[Dimension, float]],
    b_dims: dict[str, dict[Dimension, float]],
    a_accept: dict[str, bool],
    b_accept: dict[str, bool],
    *,
    label: str,
    a_name: str,
    b_name: str,
    caveats: list[str],
) -> CalibrationReport:
    items = sorted(set(a_dims) & set(b_dims))
    per_dim: dict[Dimension, DimensionCalibration] = {}
    disagreements: list[tuple[str, Dimension, float, float]] = []
    for dim in Dimension:
        xs: list[float] = []
        ys: list[float] = []
        abs_errs: list[float] = []
        for rid in items:
            av = a_dims[rid].get(dim)
            bv = b_dims[rid].get(dim)
            if av is None or bv is None:
                continue
            xs.append(av)
            ys.append(bv)
            abs_errs.append(abs(av - bv))
            disagreements.append((rid, dim, round(av, 3), round(bv, 3)))
        per_dim[dim] = DimensionCalibration(
            dimension=dim,
            n=len(xs),
            mae=(sum(abs_errs) / len(abs_errs)) if abs_errs else None,
            pearson=pearson(xs, ys),
            spearman=spearman(xs, ys),
        )
    accept_items = [r for r in items if r in a_accept and r in b_accept]
    accept_agree = (
        sum(1 for r in accept_items if a_accept[r] == b_accept[r]) / len(accept_items)
        if accept_items
        else None
    )
    disagreements.sort(key=lambda t: abs(t[2] - t[3]), reverse=True)
    return CalibrationReport(
        label=label,
        a_name=a_name,
        b_name=b_name,
        n_items=len(items),
        per_dimension=per_dim,
        overall_accept_agreement=accept_agree,
        disagreements=disagreements[:8],
        caveats=caveats,
    )


_PILOT_CAVEATS = [
    "Small pilot — NOT statistically definitive; it validates the workflow, not model quality.",
    "Human ratings are subjective; the consensus is a mean across a handful of annotators.",
    "1-5 ratings are normalized to [0,1] via (r-1)/4 to compare with 0-1 automated values.",
]


def calibrate_rules_vs_gold(
    labels: list[GoldLabel], responses: list[GoldResponse], tasks_by_id: dict[str, Task]
) -> CalibrationReport:
    """Compare rule-based dimension values to the human gold consensus for the same responses."""
    g_dims, g_accept = gold_consensus(labels)
    r_dims, r_overall, warnings = rule_values(responses, tasks_by_id)
    r_accept = {rid: total >= _PASS_THRESHOLD for rid, total in r_overall.items()}
    # Surface response_ids that were labeled by humans but have no matching scored response — a
    # mismatched packet, not a real 0-item calibration.
    unmatched = sorted(set(g_dims) - set(r_dims))
    if unmatched:
        warnings.append(
            f"{len(unmatched)} gold response_id(s) have no matching scored response "
            f"(e.g. {unmatched[:3]}); check the --responses packet matches the labels."
        )
    caveats = [*_PILOT_CAVEATS, *(f"WARNING: {w}" for w in warnings)]
    return _compare(
        r_dims,
        g_dims,
        r_accept,
        g_accept,
        label="rule-vs-gold",
        a_name="rule",
        b_name="gold",
        caveats=caveats,
    )


def calibrate_judge_vs_gold(labels: list[GoldLabel], judge: JudgeRunScores) -> CalibrationReport:
    """Compare judge dimension scores to the human gold consensus for the same responses."""
    g_dims, g_accept = gold_consensus(labels)
    j_dims, j_overall = _judge_values(judge)
    j_accept = {rid: v >= _PASS_THRESHOLD for rid, v in j_overall.items()}
    caveats = [
        *_PILOT_CAVEATS,
        f"Judge source: {judge.source} (provider={judge.judge_provider}, model={judge.judge_model}, "
        f"prompt={judge.judge_prompt_version}).",
        "LLM judges are biased (verbosity, position, self-preference, prompt-sensitivity, "
        "model-family). Judge numbers are reported ALONGSIDE, never replacing, rule-based scores.",
    ]
    if judge.source == "mock":
        caveats.append(
            "MOCK judge = offline deterministic simulator; real judge-vs-human is REQUIRES LIVE RUN."
        )
    unmatched = sorted(set(g_dims) - set(j_dims))
    if unmatched:
        caveats.append(
            f"WARNING: {len(unmatched)} gold response_id(s) have no matching judge verdict "
            f"(e.g. {unmatched[:3]}); check the judge run covered the labeled items."
        )
    return _compare(
        j_dims,
        g_dims,
        j_accept,
        g_accept,
        label="judge-vs-gold",
        a_name="judge",
        b_name="gold",
        caveats=caveats,
    )


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.3f}"


def render_calibration_md(report: CalibrationReport) -> str:
    """Render a calibration report as Markdown (for analysis/ or docs)."""
    lines = [
        f"# Calibration: {report.label}",
        "",
        f"- **Comparison:** `{report.a_name}` vs `{report.b_name}` (consensus)",
        f"- **Items compared:** {report.n_items}",
        f"- **Overall accept/reject agreement:** {_fmt(report.overall_accept_agreement)}",
        "",
        "> ⚠️ " + " ".join(report.caveats[:3]),
        "",
        "## Per-dimension",
        "",
        "| Dimension | n | MAE | Pearson | Spearman |",
        "| --- | --- | --- | --- | --- |",
    ]
    for dim in Dimension:
        dc = report.per_dimension.get(dim)
        if dc is None:
            continue
        lines.append(
            f"| {dim.value} | {dc.n} | {_fmt(dc.mae)} | {_fmt(dc.pearson)} | {_fmt(dc.spearman)} |"
        )
    lines += [
        "",
        "## Top disagreements",
        "",
        f"| response_id | dimension | {report.a_name} | {report.b_name} | abs_diff |",
        "| --- | --- | --- | --- | --- |",
    ]
    for rid, dim, a, b in report.disagreements:
        lines.append(f"| `{rid}` | {dim.value} | {a:.3f} | {b:.3f} | {abs(a - b):.3f} |")
    if len(report.caveats) > 3:
        lines += ["", "## Caveats", ""]
        lines += [f"- {c}" for c in report.caveats]
    lines.append("")
    return "\n".join(lines)
