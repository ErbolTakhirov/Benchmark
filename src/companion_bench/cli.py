"""CompanionBench command-line interface (Typer).

Thin orchestration over the runner, evaluators, and storage layers. Every command works
offline with the mock model; real providers only differ by needing API keys in the
environment. Both ``companion-bench <cmd>`` and ``python -m companion_bench.cli <cmd>`` work.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

import typer
from pydantic import TypeAdapter
from rich.console import Console
from rich.table import Table

from companion_bench import __version__
from companion_bench.adapters import describe_providers, probe_models
from companion_bench.config.model_sets import load_model_set, validate_model_set
from companion_bench.config.pricing import PricingTable, default_pricing, load_pricing
from companion_bench.config.providers import default_providers_config, load_providers_config
from companion_bench.evaluators.aggregate import render_summary, score_run
from companion_bench.evaluators.frontier import (
    FrontierRow,
    mark_pareto,
    render_csv,
    render_markdown,
)
from companion_bench.runner.engine import RunEngine, RunResult
from companion_bench.runner.manifest import load_manifest_and_tasks, validate_manifest
from companion_bench.runner.selection import select_tasks
from companion_bench.schemas.model import ModelSpec
from companion_bench.schemas.run import (
    ModelCallEvent,
    ModelRunRef,
    ModelSetRunIndex,
    RunConfig,
    RunMetadata,
)
from companion_bench.schemas.score import RunScores
from companion_bench.schemas.task import Dimension
from companion_bench.storage.export import ExportFormat, export_run
from companion_bench.storage.jsonl import read_events, read_model_json
from companion_bench.utils.errors import CompanionBenchError
from companion_bench.utils.ids import slugify
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
    out: Path = typer.Option(..., "--out", "-o", help="Output run directory."),
    model: str | None = typer.Option(
        None, "--model", help="Single model ref, e.g. mock/empathetic-v1."
    ),
    model_set: Path | None = typer.Option(
        None, "--model-set", help="Model-set YAML (runs each enabled model)."
    ),
    live: bool = typer.Option(
        False, "--live", help=f"Allow real-provider calls (needs {LIVE_ENV}=1)."
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip the live-run confirmation prompt."),
    seed: int | None = typer.Option(None, "--seed", help="Override the run seed."),
    limit: int | None = typer.Option(None, "--limit", help="Alias of --limit-tasks."),
    limit_tasks: int | None = typer.Option(
        None, "--limit-tasks", help="Only run the first N tasks."
    ),
    limit_models: int | None = typer.Option(
        None, "--limit-models", help="Only run the first N models."
    ),
    stratified: bool = typer.Option(
        False,
        "--stratified/--no-stratified",
        "--family-balanced/--no-family-balanced",
        help="With --limit-tasks, pick a family-balanced subset (round-robin) not the first N.",
    ),
    shuffle_seed: int | None = typer.Option(
        None, "--shuffle-seed", help="Deterministically shuffle tasks before selecting."
    ),
    repeats: int = typer.Option(1, "--repeats", min=1, help="Run each model this many times."),
    concurrency: int | None = typer.Option(None, "--concurrency", help="Override concurrency."),
    max_cost_usd: float | None = typer.Option(
        None, "--max-cost-usd", help="Global cost budget (USD)."
    ),
    pricing: Path | None = typer.Option(None, "--pricing", help="Pricing YAML (bundled default)."),
    providers_config: Path | None = typer.Option(
        None, "--providers-config", help="providers.yaml."
    ),
    run_id: str | None = typer.Option(
        None, "--run-id", help="Override the run id (single model only)."
    ),
) -> None:
    """Run a benchmark against one model (--model) or a model set (--model-set)."""
    try:
        manifest_obj, tasks = load_manifest_and_tasks(manifest)
        targets, set_id, is_multi = _run_targets(model, model_set, limit_models)
        pricing_table = load_pricing(pricing) if pricing else default_pricing()
        providers_cfg = (
            load_providers_config(providers_config)
            if providers_config
            else default_providers_config()
        )
    except CompanionBenchError as exc:
        _fail(str(exc))

    is_live = _check_live(targets, live)
    task_limit = limit_tasks if limit_tasks is not None else limit
    tasks = select_tasks(
        tasks, limit=task_limit, family_balanced=stratified, shuffle_seed=shuffle_seed
    )
    if is_live and max_cost_usd is not None:
        _check_budget_enforceable(targets, pricing_table, max_cost_usd, task_limit, limit_models)
    if is_live and not yes:
        real_count = sum(1 for t in targets if t.spec.provider != "mock")
        budget = f", budget ${max_cost_usd}" if max_cost_usd is not None else ""
        if not typer.confirm(
            f"About to make LIVE API calls for {real_count} real model(s){budget}. Continue?"
        ):
            _fail("aborted by user (no --yes).")

    # Tasks are already selected above; don't let the engine re-slice by limit.
    base_config = _merge_config(manifest_obj.run, seed=seed, limit=None, concurrency=concurrency)
    engine = RunEngine()
    manifest_abs = str(Path(manifest).resolve())
    spent = 0.0
    index_models: list[ModelRunRef] = []

    for target in targets:
        if max_cost_usd is not None and spent >= max_cost_usd:
            console.print("[yellow]⚠ budget reached; skipping remaining models[/]")
            break
        config = base_config.model_copy(update=target.overrides)
        settings = providers_cfg.for_provider(target.spec.provider)
        remaining = (max_cost_usd - spent) if max_cost_usd is not None else None
        # Sub-dir keyed on the unique (slugified) model id, NOT spec.slug: two entries can
        # share a provider/model (e.g. different temperatures) and would otherwise collide.
        out_sub = (out / slugify(target.id)) if is_multi else out
        try:
            result = asyncio.run(
                engine.run(
                    manifest=manifest_obj,
                    tasks=tasks,
                    model=target.spec,
                    config=config,
                    out_dir=out_sub,
                    manifest_path=manifest_abs,
                    run_id=(None if is_multi else run_id),
                    settings=settings,
                    requests_per_second=settings.requests_per_second,
                    pricing=pricing_table,
                    max_cost_usd=remaining,
                    repeats=repeats,
                )
            )
        except CompanionBenchError as exc:
            _fail(str(exc))

        spent += result.total_estimated_cost_usd or 0.0
        index_models.append(
            ModelRunRef(
                id=target.id,
                ref=target.spec.ref,
                slug=slugify(target.id),
                run_id=result.run_id,
                budget_exceeded=result.budget_exceeded,
            )
        )
        _print_run_result(target.id, result, is_multi)

    if is_multi:
        index = ModelSetRunIndex(
            set_id=set_id,
            manifest_name=manifest_obj.name,
            created_at=RealClock().now_iso(),
            models=tuple(index_models),
        )
        out.mkdir(parents=True, exist_ok=True)
        (out / "modelset.json").write_text(index.model_dump_json(indent=2) + "\n", encoding="utf-8")
    if max_cost_usd is not None:
        console.print(f"Total estimated cost: [bold]${spent:.6f}[/] (budget ${max_cost_usd}).")
    console.print(f"Next: [bold]companion-bench score --run {out}[/]")


@app.command()
def score(
    run: Path = typer.Option(..., "--run", help="A run (or model-set run) directory."),
    bootstrap: bool = typer.Option(False, "--bootstrap", help="Compute bootstrap 95% CIs."),
    bootstrap_resamples: int = typer.Option(
        2000, "--bootstrap-resamples", min=100, help="Bootstrap resamples."
    ),
    bootstrap_seed: int = typer.Option(42, "--bootstrap-seed", help="Bootstrap RNG seed."),
) -> None:
    """Score a run (or every sub-run of a model-set run) -> scores.json + summary.md."""
    run_dir = run
    boot = (bootstrap, bootstrap_resamples, bootstrap_seed)
    if (run_dir / "run.json").is_file():
        scores = _score_one(run_dir, boot)
        _print_scores(scores)
        console.print(f"  scores: {run_dir / 'scores.json'}  ·  summary: {run_dir / 'summary.md'}")
        return
    index = _load_modelset_index(run_dir)  # _fails if neither layout is present
    scored = 0
    for entry in index.models:
        sub = run_dir / entry.slug
        if (sub / "run.json").is_file():
            _score_one(sub, boot)
            scored += 1
    console.print(
        f"[green]✓[/] scored {scored}/{len(index.models)} model sub-run(s). "
        f"Compare with: [bold]companion-bench report --run {run_dir}[/]"
    )


@app.command()
def report(
    run: Path = typer.Option(..., "--run", help="A scored run (or model-set run) directory."),
) -> None:
    """Show a scored run, or compare every model in a scored model-set run."""
    run_dir = run
    if (run_dir / "run.json").is_file():
        scores_path = run_dir / "scores.json"
        if not scores_path.is_file():
            _fail(
                f"{run_dir} is not scored yet; run `companion-bench score --run {run_dir}` first."
            )
        scores = RunScores.model_validate_json(scores_path.read_text(encoding="utf-8"))
        _print_scores(scores)
        return

    index = _load_modelset_index(run_dir)
    rows: list[RunScores] = []
    for entry in index.models:
        sp = run_dir / entry.slug / "scores.json"
        if sp.is_file():
            rows.append(RunScores.model_validate_json(sp.read_text(encoding="utf-8")))
    if not rows:
        _fail(
            f"no scored sub-runs in {run_dir}; run `companion-bench score --run {run_dir}` first."
        )

    table = Table(title=f"Model comparison — {index.set_id or run_dir.name}")
    table.add_column("model")
    table.add_column("overall", justify="right")
    table.add_column("95% CI", justify="center")
    table.add_column("passed", justify="right")
    table.add_column("cost USD", justify="right")
    for dim in Dimension:
        table.add_column(dim.value[:4], justify="right")
    ranked = sorted(rows, key=lambda s: s.overall, reverse=True)
    for scores in ranked:
        cost = "n/a" if scores.total_cost_usd is None else f"{scores.total_cost_usd:.6f}"
        ci = (
            "—"
            if scores.overall_ci is None
            else f"[{scores.overall_ci[0]:.2f}, {scores.overall_ci[1]:.2f}]"
        )
        cells = [
            scores.model_id,
            f"{scores.overall:.3f}",
            ci,
            f"{scores.n_passed}/{scores.n_tasks}",
            cost,
        ]
        cells += [
            ("n/a" if scores.by_dimension.get(dim) is None else f"{scores.by_dimension[dim]:.2f}")
            for dim in Dimension
        ]
        table.add_row(*cells)
    console.print(table)
    for scores in ranked:
        if scores.behavior_flags:
            top = ", ".join(f"{k} ({v})" for k, v in list(scores.behavior_flags.items())[:3])
            console.print(f"  [bold]{scores.model_id}[/] top flags: {top}")


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
def frontier(
    run: Path = typer.Option(..., "--run", help="A scored run (or model-set run) directory."),
) -> None:
    """Cost-quality frontier across the scored models in a run (writes frontier.md + .csv)."""
    rows = _gather_frontier_rows(run)
    mark_pareto(rows)
    table = Table(title=f"Cost-quality frontier — {run.name}")
    table.add_column("model")
    table.add_column("overall", justify="right")
    table.add_column("95% CI", justify="center")
    table.add_column("cost USD", justify="right")
    table.add_column("cost/probe", justify="right")
    table.add_column("latency ms", justify="right")
    table.add_column("Pareto", justify="center")
    for r in sorted(rows, key=lambda x: x.overall, reverse=True):
        ci = "—" if r.overall_ci is None else f"[{r.overall_ci[0]:.2f}, {r.overall_ci[1]:.2f}]"
        cost = "n/a" if r.total_cost_usd is None else f"{r.total_cost_usd:.6f}"
        cps = "n/a" if r.cost_per_successful_probe is None else f"{r.cost_per_successful_probe:.6f}"
        lat = "—" if r.latency_ms_avg is None else f"{r.latency_ms_avg:.0f}"
        pareto = "n/a" if r.pareto_optimal is None else ("✅" if r.pareto_optimal else "—")
        table.add_row(r.model_id, f"{r.overall:.3f}", ci, cost, cps, lat, pareto)
    console.print(table)
    (run / "frontier.md").write_text(render_markdown(rows), encoding="utf-8")
    (run / "frontier.csv").write_text(render_csv(rows), encoding="utf-8")
    console.print(f"  wrote {run / 'frontier.md'} and {run / 'frontier.csv'}")


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
    # Re-validate: model_copy skips validation, so bad CLI inputs (e.g. --concurrency 0,
    # which would deadlock the semaphore) must be caught here.
    try:
        return RunConfig.model_validate({**base.model_dump(), **updates})
    except Exception as exc:
        _fail(f"invalid run config override: {exc}")


def _print_scores(scores: RunScores) -> None:
    table = Table(title=f"Scores — {scores.run_id}  (overall {scores.overall:.3f})")
    table.add_column("task_id")
    table.add_column("family")
    table.add_column("score", justify="right")
    table.add_column("pass", justify="center")
    for ts in scores.task_scores:
        table.add_row(ts.task_id, ts.family.value, f"{ts.total:.3f}", "✅" if ts.passed else "❌")
    console.print(table)
    ci = (
        ""
        if scores.overall_ci is None
        else f" (95% CI [{scores.overall_ci[0]:.3f}, {scores.overall_ci[1]:.3f}])"
    )
    console.print(
        f"[bold]{scores.n_passed}/{scores.n_tasks}[/] tasks passed · overall "
        f"[bold]{scores.overall:.3f}[/]{ci}"
    )
    if scores.total_cost_usd is not None:
        console.print(
            f"Estimated cost: [bold]${scores.total_cost_usd:.6f}[/] "
            f"({scores.total_tokens or 0} tokens)"
        )
    if scores.behavior_flags:
        top = ", ".join(f"{k} ({v})" for k, v in list(scores.behavior_flags.items())[:5])
        console.print(f"Top behavior flags: {top}")


@dataclass(frozen=True)
class _Target:
    id: str
    spec: ModelSpec
    overrides: dict[str, Any]


def _run_targets(
    model: str | None, model_set: Path | None, limit_models: int | None
) -> tuple[list[_Target], str | None, bool]:
    """Resolve the run into (targets, set_id, is_multi). Single model -> non-multi layout."""
    if model and model_set:
        _fail("pass either --model or --model-set, not both.")
    if not model and not model_set:
        _fail("pass --model <ref> or --model-set <path>.")
    if model:
        try:
            spec = ModelSpec.parse(model)
        except ValueError as exc:
            _fail(str(exc))
        return [_Target(spec.slug, spec, {})], None, False
    assert model_set is not None
    ms = load_model_set(model_set)
    enabled = ms.enabled_models()
    if limit_models is not None:
        enabled = enabled[:limit_models]
    if not enabled:
        _fail("model set has no enabled models.")
    targets = [_Target(e.id, e.spec(), e.config_overrides()) for e in enabled]
    return targets, ms.set_id, True


def _check_live(targets: list[_Target], live: bool) -> bool:
    """Enforce the live-call guardrails; return True for a real (live) run."""
    if not any(t.spec.provider != "mock" for t in targets):
        return False  # mock-only: offline, no confirmation needed
    if not live:
        _fail("real-provider runs require --live (and COMPANIONBENCH_LIVE=1).")
    if not _live_enabled():
        _fail(f"--live requires {LIVE_ENV}=1 (live network calls are opt-in).")
    return True


def _check_budget_enforceable(
    targets: list[_Target],
    pricing_table: PricingTable,
    max_cost_usd: float,
    task_limit: int | None,
    limit_models: int | None,
) -> None:
    """A budget can only bound spend for priced models. Refuse an unbounded paid run."""
    unpriced = sorted(
        {t.spec.ref for t in targets if pricing_table.rate(t.spec.provider, t.spec.model) is None}
    )
    if not unpriced:
        return
    msg = (
        f"--max-cost-usd ${max_cost_usd} cannot bound spend for unpriced model(s): {unpriced}. "
        "Add prices with --pricing <file>."
    )
    if task_limit is None and limit_models is None:
        _fail(f"{msg} Refusing an unbounded paid run — also set --limit-tasks/--limit-models.")
    err_console.print(
        f"[yellow]⚠ {msg} Relying on --limit-tasks/--limit-models as the hard cap.[/]"
    )


def _print_run_result(label: str, result: RunResult, is_multi: bool) -> None:
    cost = (
        ""
        if result.total_estimated_cost_usd is None
        else f", ${result.total_estimated_cost_usd:.6f}"
    )
    flag = " [yellow](budget hit)[/]" if result.budget_exceeded else ""
    console.print(
        f"[green]✓[/] [bold]{label}[/]: {result.n_model_calls} calls, "
        f"{result.n_failures} failure(s){cost}{flag} → {result.out_dir}"
    )


def _score_one(run_dir: Path, boot: tuple[bool, int, int] = (False, 2000, 42)) -> RunScores:
    """Score a single run directory and write its scores.json + summary.md."""
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
    bootstrap, resamples, seed = boot
    scores = score_run(
        tasks,
        events,
        run_id=meta.run_id,
        model_id=meta.model_id,
        provider=meta.provider,
        generated_at=RealClock().now_iso(),
        bootstrap=bootstrap,
        bootstrap_resamples=resamples,
        bootstrap_seed=seed,
    )
    (run_dir / "scores.json").write_text(scores.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (run_dir / "summary.md").write_text(render_summary(meta, scores), encoding="utf-8")
    return scores


def _load_modelset_index(run_dir: Path) -> ModelSetRunIndex:
    index_path = run_dir / "modelset.json"
    if not index_path.is_file():
        _fail(f"{run_dir} is not a run directory (need run.json or modelset.json).")
    return ModelSetRunIndex.model_validate_json(index_path.read_text(encoding="utf-8"))


def _gather_frontier_rows(run_dir: Path) -> list[FrontierRow]:
    """Collect a frontier row per scored model (single run or every model-set sub-run)."""
    if (run_dir / "scores.json").is_file():
        dirs = [run_dir]
    elif (run_dir / "modelset.json").is_file():
        index = _load_modelset_index(run_dir)
        dirs = [
            run_dir / m.slug for m in index.models if (run_dir / m.slug / "scores.json").is_file()
        ]
    else:
        _fail(f"{run_dir} is not a run directory (need scores.json or modelset.json).")
    if not dirs:
        _fail(f"no scored runs in {run_dir}; run `companion-bench score --run {run_dir}` first.")
    return [_frontier_row(d) for d in dirs]


def _frontier_row(run_dir: Path) -> FrontierRow:
    scores = RunScores.model_validate_json((run_dir / "scores.json").read_text(encoding="utf-8"))
    calls = [e for e in read_events(run_dir / "events.jsonl") if isinstance(e, ModelCallEvent)]
    n_successful = sum(1 for c in calls if c.parsed)
    latencies = [c.latency_ms for c in calls if c.latency_ms is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None
    cost = scores.total_cost_usd
    cost_per_probe = (cost / n_successful) if (cost is not None and n_successful) else None
    return FrontierRow(
        model_id=scores.model_id,
        overall=scores.overall,
        overall_ci=scores.overall_ci,
        total_cost_usd=cost,
        cost_per_successful_probe=cost_per_probe,
        total_tokens=scores.total_tokens,
        latency_ms_avg=avg_latency,
        n_successful_probes=n_successful,
        notes="" if cost is not None else "cost unknown (unpriced)",
    )


if __name__ == "__main__":  # pragma: no cover
    app()
