"""Cost-quality frontier: rank models by score vs cost and mark the Pareto front.

A model is **Pareto-optimal** if no other (priced) model is at least as good on overall score
*and* at least as cheap, with a strict win on one of them. Models with unknown cost can't be
placed on the cost axis, so their ``pareto_optimal`` is ``None`` (reported, not guessed).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

__all__ = ["FrontierRow", "mark_pareto", "render_csv", "render_markdown"]


@dataclass
class FrontierRow:
    model_id: str
    overall: float
    overall_ci: tuple[float, float] | None
    total_cost_usd: float | None
    cost_per_successful_probe: float | None
    total_tokens: int | None
    latency_ms_avg: float | None
    n_successful_probes: int
    pareto_optimal: bool | None = None
    notes: str = ""


def mark_pareto(rows: list[FrontierRow]) -> None:
    """Set ``pareto_optimal`` in place: 2D Pareto over (max overall, min cost) for priced rows."""
    priced = [r for r in rows if r.total_cost_usd is not None]
    for row in rows:
        if row.total_cost_usd is None:
            row.pareto_optimal = None
            continue
        cost = row.total_cost_usd
        dominated = any(
            other is not row
            and other.total_cost_usd is not None
            and other.overall >= row.overall
            and other.total_cost_usd <= cost
            and (other.overall > row.overall or other.total_cost_usd < cost)
            for other in priced
        )
        row.pareto_optimal = not dominated


def _ci(ci: tuple[float, float] | None) -> str:
    return "" if ci is None else f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def _num(value: float | None, fmt: str = "{:.6f}") -> str:
    return "" if value is None else fmt.format(value)


def _pareto(flag: bool | None) -> str:
    return "n/a" if flag is None else ("yes" if flag else "no")


def render_markdown(rows: list[FrontierRow]) -> str:
    """Render the frontier as a Markdown table (sorted by overall desc)."""
    ordered = sorted(rows, key=lambda r: r.overall, reverse=True)
    lines = [
        "# Cost-quality frontier",
        "",
        "| model | overall | 95% CI | total cost USD | cost/probe | tokens | latency ms | "
        "successful probes | Pareto | notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in ordered:
        lines.append(
            f"| `{r.model_id}` | {r.overall:.3f} | {_ci(r.overall_ci)} | "
            f"{_num(r.total_cost_usd) or 'n/a'} | {_num(r.cost_per_successful_probe) or 'n/a'} | "
            f"{r.total_tokens or ''} | {_num(r.latency_ms_avg, '{:.0f}') or ''} | "
            f"{r.n_successful_probes} | {_pareto(r.pareto_optimal)} | {r.notes} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_csv(rows: list[FrontierRow]) -> str:
    """Render the frontier as CSV (stable column order)."""
    ordered = sorted(rows, key=lambda r: r.overall, reverse=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "model_id",
            "overall",
            "ci_low",
            "ci_high",
            "total_cost_usd",
            "cost_per_successful_probe",
            "total_tokens",
            "latency_ms_avg",
            "n_successful_probes",
            "pareto_optimal",
            "notes",
        ]
    )
    for r in ordered:
        writer.writerow(
            [
                r.model_id,
                f"{r.overall:.6f}",
                "" if r.overall_ci is None else f"{r.overall_ci[0]:.6f}",
                "" if r.overall_ci is None else f"{r.overall_ci[1]:.6f}",
                _num(r.total_cost_usd),
                _num(r.cost_per_successful_probe),
                "" if r.total_tokens is None else r.total_tokens,
                _num(r.latency_ms_avg, "{:.3f}"),
                r.n_successful_probes,
                _pareto(r.pareto_optimal),
                r.notes,
            ]
        )
    return buf.getvalue()
