"""CompanionBench command-line interface (Typer).

Thin orchestration over the runner, evaluators, and storage layers. Every command works
offline with the mock model; real providers only differ by needing API keys in the
environment. Both ``companion-bench <cmd>`` and ``python -m companion_bench.cli <cmd>`` work.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import NoReturn, cast

import typer
from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from companion_bench import __version__
from companion_bench.evaluators.aggregate import render_summary, score_run
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.manifest import load_manifest_and_tasks, validate_manifest
from companion_bench.schemas.model import ModelSpec
from companion_bench.schemas.run import RunConfig, RunMetadata
from companion_bench.schemas.score import RunScores
from companion_bench.storage.export import ExportFormat, export_run
from companion_bench.storage.jsonl import read_events, read_model_json
from companion_bench.utils.errors import CompanionBenchError
from companion_bench.utils.timing import RealClock

app = typer.Typer(
    name="companion-bench",
    help="API-first benchmark for LLM companions and proactive assistants.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)

_RUN_META_ADAPTER: TypeAdapter[RunMetadata] = TypeAdapter(RunMetadata)


def _fail(message: str) -> NoReturn:
    err_console.print(f"[red]error:[/] {message}")
    raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Print the installed CompanionBench version."""
    console.print(__version__)


@app.command()
def validate(
    manifest: Path = typer.Argument(..., help="Path to a manifest YAML file."),
) -> None:
    """Validate a manifest and every task it references."""
    report = validate_manifest(manifest)
    if report.ok:
        console.print(
            f"[green]✓[/] manifest [bold]{report.name}[/] is valid — "
            f"{report.n_tasks} task(s): {report.families}"
        )
        return
    err_console.print(f"[red]✗[/] manifest at {report.manifest_path} is INVALID:")
    for error in report.errors:
        err_console.print(f"  [red]•[/] {error}")
    raise typer.Exit(code=1)


@app.command(name="list-tasks")
def list_tasks(
    manifest: Path = typer.Argument(..., help="Path to a manifest YAML file."),
) -> None:
    """List the tasks a manifest resolves to."""
    try:
        _, tasks = load_manifest_and_tasks(manifest)
    except CompanionBenchError as exc:
        _fail(str(exc))
    table = Table(title=f"Tasks in {manifest}")
    table.add_column("task_id")
    table.add_column("family")
    table.add_column("difficulty")
    table.add_column("probes", justify="right")
    for task in tasks:
        table.add_row(task.task_id, task.family.value, task.difficulty.value, str(len(task.probes)))
    console.print(table)


@app.command()
def run(
    manifest: Path = typer.Option(..., "--manifest", "-m", help="Manifest YAML to run."),
    model: str = typer.Option(..., "--model", help="Model ref, e.g. mock/empathetic-v1."),
    out: Path = typer.Option(..., "--out", "-o", help="Output run directory."),
    seed: int | None = typer.Option(None, "--seed", help="Override the run seed."),
    limit: int | None = typer.Option(None, "--limit", help="Only run the first N tasks."),
    concurrency: int | None = typer.Option(None, "--concurrency", help="Override concurrency."),
    run_id: str | None = typer.Option(None, "--run-id", help="Override the derived run id."),
) -> None:
    """Run a benchmark and write events.jsonl + run.json."""
    try:
        manifest_obj, tasks = load_manifest_and_tasks(manifest)
        spec = ModelSpec.parse(model)
        config = _merge_config(manifest_obj.run, seed=seed, limit=limit, concurrency=concurrency)
        engine = RunEngine()
        result = asyncio.run(
            engine.run(
                manifest=manifest_obj,
                tasks=tasks,
                model=spec,
                config=config,
                out_dir=out,
                manifest_path=str(Path(manifest).resolve()),
                run_id=run_id,
            )
        )
    except CompanionBenchError as exc:
        _fail(str(exc))

    console.print(
        f"[green]✓[/] run [bold]{result.run_id}[/] complete — "
        f"{result.n_model_calls} calls across {result.n_tasks} tasks, "
        f"{result.n_failures} failure(s)."
    )
    console.print(f"  events: {result.events_path}")
    console.print(f"  run.json: {result.metadata_path}")
    if result.n_failures:
        err_console.print(f"[yellow]⚠[/] {result.n_failures} probe(s) failed; see events.jsonl.")
    console.print(f"Next: [bold]companion-bench score --run {out}[/]")


@app.command()
def score(
    run: Path = typer.Option(..., "--run", help="A run directory produced by `run`."),
) -> None:
    """Score a run and write scores.json + summary.md."""
    run_dir = run
    meta_path = run_dir / "run.json"
    events_path = run_dir / "events.jsonl"
    if not meta_path.is_file() or not events_path.is_file():
        _fail(f"{run_dir} is not a run directory (need run.json and events.jsonl).")

    try:
        meta = read_model_json(meta_path, _RUN_META_ADAPTER)
        events = read_events(events_path)
        _, all_tasks = load_manifest_and_tasks(meta.manifest_path)
    except CompanionBenchError as exc:
        _fail(str(exc))

    by_id = {t.task_id: t for t in all_tasks}
    missing = [tid for tid in meta.task_ids if tid not in by_id]
    if missing:
        _fail(f"tasks referenced by the run are no longer in the manifest: {missing}")
    tasks = [by_id[tid] for tid in meta.task_ids]

    scores = score_run(
        tasks,
        events,
        run_id=meta.run_id,
        model_id=meta.model_id,
        provider=meta.provider,
        generated_at=RealClock().now_iso(),
    )
    (run_dir / "scores.json").write_text(scores.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (run_dir / "summary.md").write_text(render_summary(meta, scores), encoding="utf-8")

    _print_scores(scores)
    console.print(f"  scores: {run_dir / 'scores.json'}")
    console.print(f"  summary: {run_dir / 'summary.md'}")


@app.command()
def export(
    run: Path = typer.Option(..., "--run", help="A run directory to export."),
    output_format: str = typer.Option("parquet", "--format", help="parquet | duckdb."),
) -> None:
    """Export a run's events (and scores) to Parquet."""
    if output_format not in ("parquet", "duckdb"):
        _fail(f"unknown format {output_format!r}; expected 'parquet' or 'duckdb'.")
    try:
        written = export_run(run, cast(ExportFormat, output_format))
    except CompanionBenchError as exc:
        _fail(str(exc))
    console.print(f"[green]✓[/] exported {len(written)} file(s):")
    for path in written:
        console.print(f"  {path}")


# --------------------------------------------------------------------------- helpers
def _merge_config(
    base: RunConfig, *, seed: int | None, limit: int | None, concurrency: int | None
) -> RunConfig:
    updates: dict[str, int] = {}
    if seed is not None:
        updates["seed"] = seed
    if limit is not None:
        updates["limit"] = limit
    if concurrency is not None:
        updates["concurrency"] = concurrency
    return base.model_copy(update=updates)


def _print_scores(scores: RunScores) -> None:
    table = Table(title=f"Scores — {scores.run_id}  (overall {scores.overall:.3f})")
    table.add_column("task_id")
    table.add_column("family")
    table.add_column("score", justify="right")
    table.add_column("pass", justify="center")
    for ts in scores.task_scores:
        table.add_row(ts.task_id, ts.family.value, f"{ts.total:.3f}", "✅" if ts.passed else "❌")
    console.print(table)
    console.print(
        f"[bold]{scores.n_passed}/{scores.n_tasks}[/] tasks passed · overall "
        f"[bold]{scores.overall:.3f}[/]"
    )


if __name__ == "__main__":  # pragma: no cover
    app()
