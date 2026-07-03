"""Cost-quality frontier: Pareto marking, rendering, and the CLI command."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from companion_bench.cli import app
from companion_bench.evaluators.frontier import (
    FrontierRow,
    mark_pareto,
    render_csv,
    render_markdown,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"
MOCK_SET = REPO_ROOT / "configs" / "model_sets" / "mock-profiles.yaml"
runner = CliRunner()


def _row(model: str, overall: float, cost: float | None) -> FrontierRow:
    return FrontierRow(
        model_id=model,
        overall=overall,
        overall_ci=None,
        total_cost_usd=cost,
        cost_per_successful_probe=None if cost is None else cost / 10,
        total_tokens=100,
        latency_ms_avg=500.0,
        n_successful_probes=10,
    )


def test_mark_pareto_2d() -> None:
    cheap_good = _row("a", 0.8, 1.0)
    best = _row("b", 0.9, 2.0)
    dominated = _row("c", 0.7, 3.0)  # worse than a and pricier
    rows = [cheap_good, best, dominated]
    mark_pareto(rows)
    assert cheap_good.pareto_optimal is True
    assert best.pareto_optimal is True
    assert dominated.pareto_optimal is False


def test_mark_pareto_unknown_cost_is_none() -> None:
    rows = [_row("a", 0.8, None), _row("b", 0.9, 1.0)]
    mark_pareto(rows)
    assert rows[0].pareto_optimal is None  # unknown cost -> not placed
    assert rows[1].pareto_optimal is True


def test_render_csv_and_md() -> None:
    rows = [_row("a", 0.8, 1.0), _row("b", 0.9, 2.0)]
    mark_pareto(rows)
    csv = render_csv(rows)
    assert "model_id,overall" in csv.splitlines()[0]
    assert "b,0.900000" in csv  # sorted by overall desc -> b first row
    md = render_markdown(rows)
    assert "Cost-quality frontier" in md
    assert "Pareto" in md


def test_cli_frontier_writes_files(tmp_path: Path) -> None:
    out = tmp_path / "multi"
    runner.invoke(app, ["run", "-m", str(SMOKE), "--model-set", str(MOCK_SET), "--out", str(out)])
    runner.invoke(app, ["score", "--run", str(out), "--bootstrap", "--bootstrap-resamples", "500"])
    result = runner.invoke(app, ["frontier", "--run", str(out)])
    assert result.exit_code == 0, result.stdout
    assert (out / "frontier.md").is_file()
    assert (out / "frontier.csv").is_file()
    assert "mock/empathetic-v1" in (out / "frontier.csv").read_text()


def test_render_markdown_includes_provenance_when_given() -> None:
    rows = [_row("m", 0.5, 0.01)]
    assert "Scoring:" not in render_markdown(rows)  # none by default
    md = render_markdown(rows, provenance="Scoring: rule_based v1.2.0 · commit abc")
    assert "> Scoring: rule_based v1.2.0 · commit abc" in md
