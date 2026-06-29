"""Optional Parquet/DuckDB export of run artifacts.

Export is intentionally optional: the core run/score loop never needs it. Parquet support
comes from the ``export`` extra (``polars``); if it is not installed, a clear
:class:`ExportError` explains how to enable it. Events are flattened to a stable columnar
schema with the full original record preserved in a ``payload_json`` column, so no
information is lost regardless of event type.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from companion_bench.schemas.task import DIMENSIONS
from companion_bench.storage.jsonl import read_jsonl
from companion_bench.utils.errors import ExportError

__all__ = ["ExportFormat", "export_run"]

ExportFormat = Literal["parquet", "duckdb"]


def export_run(run_dir: str | Path, fmt: ExportFormat = "parquet") -> list[Path]:
    """Export a run directory's events (and scores, if present) to ``run_dir/export/``.

    Returns the list of files written. Raises :class:`ExportError` on any failure
    (missing optional dependency, missing inputs, unsupported format).
    """
    run_dir = Path(run_dir)
    if fmt == "parquet":
        return _export_parquet(run_dir)
    if fmt == "duckdb":
        raise ExportError(
            "DuckDB export is not implemented yet. Use --format parquet; DuckDB can query "
            "the generated .parquet files directly, e.g. "
            "SELECT * FROM read_parquet('export/events.parquet')."
        )
    raise ExportError(f"unknown export format {fmt!r}")


def _require_polars() -> Any:
    try:
        import polars as pl
    except ImportError as exc:  # pragma: no cover - exercised via skipif in tests
        raise ExportError(
            "Parquet export requires the optional 'export' extra. "
            "Install it with: uv sync --extra export  (or: pip install 'companion-bench[export]')."
        ) from exc
    return pl


def _export_parquet(run_dir: Path) -> list[Path]:
    pl = _require_polars()
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        raise ExportError(f"no events.jsonl found in {run_dir}")

    out_dir = run_dir / "export"
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    rows = [_event_row(ev) for ev in read_jsonl(events_path)]
    events_df = pl.DataFrame(rows, schema=_event_schema(pl))
    events_out = out_dir / "events.parquet"
    events_df.write_parquet(events_out)
    written.append(events_out)

    scores_path = run_dir / "scores.json"
    if scores_path.exists():
        scores = json.loads(scores_path.read_text(encoding="utf-8"))
        task_rows = [_task_score_row(ts) for ts in scores.get("task_scores", [])]
        if task_rows:
            scores_df = pl.DataFrame(task_rows, schema=_score_schema(pl))
            scores_out = out_dir / "task_scores.parquet"
            scores_df.write_parquet(scores_out)
            written.append(scores_out)

    return written


def _event_row(ev: dict[str, Any]) -> dict[str, Any]:
    usage = ev.get("token_usage") or {}
    return {
        "event_id": ev.get("event_id"),
        "run_id": ev.get("run_id"),
        "timestamp": ev.get("timestamp"),
        "event_type": ev.get("event_type"),
        "task_id": ev.get("task_id"),
        "probe_id": ev.get("probe_id"),
        "model_id": ev.get("model_id"),
        "provider": ev.get("provider"),
        "parsed": ev.get("parsed"),
        "latency_ms": ev.get("latency_ms"),
        "estimated_cost_usd": ev.get("estimated_cost_usd"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "error_type": ev.get("error_type"),
        "error_message": ev.get("error_message"),
        "payload_json": json.dumps(ev, ensure_ascii=False, sort_keys=True),
    }


def _task_score_row(ts: dict[str, Any]) -> dict[str, Any]:
    dims = ts.get("dimension_means", {}) or {}
    row: dict[str, Any] = {
        "task_id": ts.get("task_id"),
        "family": ts.get("family"),
        "total": ts.get("total"),
        "pass_threshold": ts.get("pass_threshold"),
        "passed": ts.get("passed"),
    }
    for dim in DIMENSIONS:
        row[f"dim_{dim}"] = dims.get(dim)
    return row


def _event_schema(pl: Any) -> dict[str, Any]:
    return {
        "event_id": pl.Utf8,
        "run_id": pl.Utf8,
        "timestamp": pl.Utf8,
        "event_type": pl.Utf8,
        "task_id": pl.Utf8,
        "probe_id": pl.Utf8,
        "model_id": pl.Utf8,
        "provider": pl.Utf8,
        "parsed": pl.Boolean,
        "latency_ms": pl.Float64,
        "estimated_cost_usd": pl.Float64,
        "prompt_tokens": pl.Int64,
        "completion_tokens": pl.Int64,
        "total_tokens": pl.Int64,
        "error_type": pl.Utf8,
        "error_message": pl.Utf8,
        "payload_json": pl.Utf8,
    }


def _score_schema(pl: Any) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "task_id": pl.Utf8,
        "family": pl.Utf8,
        "total": pl.Float64,
        "pass_threshold": pl.Float64,
        "passed": pl.Boolean,
    }
    for dim in DIMENSIONS:
        schema[f"dim_{dim}"] = pl.Float64
    return schema
