"""CompanionBench command-line interface (Typer).

Thin orchestration over the runner, evaluators, and storage layers. Every command works
offline with the mock model; real providers only differ by needing API keys in the
environment. Both ``companion-bench <cmd>`` and ``python -m companion_bench.cli <cmd>`` work.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import NoReturn, cast

import typer
from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from companion_bench import __version__
from companion_bench.adapters import describe_providers, probe_models
from companion_bench.config.model_sets import load_model_set, validate_model_set
from companion_bench.config.pricing import default_pricing, load_pricing
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

models_app = typer.Typer(
    name="models", help="Inspect and validate model sets.", no_args_is_help=True
)
app.add_typer(models_app)

_RUN_META_ADAPTER: TypeAdapter[RunMetadata] = TypeAdapter(RunMetadata)

# Live network calls are opt-in: every live path requires this env var set to "1".
LIVE_ENV = "COMPANIONBENCH_LIVE"
# Default tiny models used by `providers --probe` (override/extend with --probe-model).
_PROBE_MODELS = {"openai": "gpt-4o-mini", "anthropic": "claude-haiku-4-5-20251001"}


def _live_enabled() -> bool:
    return os.environ.get(LIVE_ENV) == "1"


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


@app.command()
def providers(
    probe: bool = typer.Option(
        False, "--probe", help=f"Send one tiny LIVE request per target (requires {LIVE_ENV}=1)."
    ),
    probe_model: list[str] = typer.Option(
        [], "--probe-model", help="Extra provider/model refs to probe (repeatable)."
    ),
) -> None:
    """List registered providers and whether their API keys are present (never values)."""
    infos = describe_providers()
    table = Table(title="Providers")
    table.add_column("provider")
    table.add_column("requires key", justify="center")
    table.add_column("key env")
    table.add_column("key present", justify="center")
    table.add_column("base url")
    for info in infos:
        table.add_row(
            info.provider,
            "yes" if info.requires_key else "no",
            info.key_env_var or "—",
            "yes" if info.key_present else "no",
            info.base_url or "—",
        )
    console.print(table)

    if not probe:
        return
    if not _live_enabled():
        _fail(f"--probe makes live network calls; set {LIVE_ENV}=1 to allow it.")

    refs = list(probe_model)
    for info in infos:
        if info.provider in _PROBE_MODELS and info.key_present:
            refs.append(f"{info.provider}/{_PROBE_MODELS[info.provider]}")
    if not refs:
        console.print(
            "[yellow]no probeable targets[/] — set a provider key, or pass "
            "--probe-model provider/model."
        )
        return

    console.print(f"[bold]Probing[/] {len(refs)} target(s) (live)…")
    results = asyncio.run(probe_models(refs))
    ptable = Table(title="Live probe")
    ptable.add_column("provider/model")
    ptable.add_column("ok", justify="center")
    ptable.add_column("latency ms", justify="right")
    ptable.add_column("tokens", justify="right")
    ptable.add_column("note")
    for r in results:
        note = r.error or ("parsed" if r.parsed else "ok (envelope not parsed)")
        ptable.add_row(
            r.ref,
            "✅" if r.ok else "❌",
            f"{r.latency_ms:.0f}" if r.latency_ms is not None else "—",
            str(r.total_tokens) if r.total_tokens is not None else "—",
            note,
        )
    console.print(ptable)
    if any(not r.ok for r in results):
        raise typer.Exit(code=1)


@models_app.command("validate")
def models_validate(
    model_set: Path = typer.Option(..., "--model-set", help="Path to a model-set YAML."),
    pricing: Path | None = typer.Option(None, "--pricing", help="Pricing YAML (bundled default)."),
) -> None:
    """Validate a model set: providers registered, slugs verified, prices known."""
    try:
        ms = load_model_set(model_set)
        price_table = load_pricing(pricing) if pricing else default_pricing()
    except CompanionBenchError as exc:
        _fail(str(exc))

    report = validate_model_set(ms, pricing=price_table)
    table = Table(
        title=f"Model set: {report.set_id}  ({report.n_enabled}/{report.n_models} enabled)"
    )
    table.add_column("id")
    table.add_column("provider/model")
    table.add_column("enabled", justify="center")
    table.add_column("price?", justify="center")
    table.add_column("needs_mapping", justify="center")
    for m in ms.models:
        priced = "yes" if price_table.rate(m.provider, m.model) else "no"
        table.add_row(
            m.id, m.ref, "yes" if m.enabled else "no", priced, "yes" if m.needs_mapping else "no"
        )
    console.print(table)
    for issue in report.issues:
        style = "red" if issue.level == "error" else "yellow"
        console.print(f"  [{style}]{issue.level}[/] {issue.model_id or ''}: {issue.message}")
    if not report.ok:
        raise typer.Exit(code=1)
    console.print(f"[green]✓[/] model set [bold]{report.set_id}[/] is valid")


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
