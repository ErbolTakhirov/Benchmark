"""CLI tests via Typer's CliRunner (offline; no API keys)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from companion_bench import __version__
from companion_bench.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_validate_ok() -> None:
    result = runner.invoke(app, ["validate", str(SMOKE)])
    assert result.exit_code == 0
    assert "valid" in result.stdout


def test_validate_bad_manifest_exits_nonzero(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: bad\nversion: 1.0.0\ntask_paths:\n  - 'nope/*.yaml'\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", str(bad)])
    assert result.exit_code == 1


def test_list_tasks() -> None:
    result = runner.invoke(app, ["list-tasks", str(SMOKE)])
    assert result.exit_code == 0
    assert "initiative-late-night-overwork" in result.stdout


def test_run_then_score_pipeline(tmp_path: Path) -> None:
    out = tmp_path / "smoke"
    run_result = runner.invoke(
        app,
        ["run", "--manifest", str(SMOKE), "--model", "mock/empathetic-v1", "--out", str(out)],
    )
    assert run_result.exit_code == 0, run_result.stdout
    assert (out / "events.jsonl").is_file()
    assert (out / "run.json").is_file()

    score_result = runner.invoke(app, ["score", "--run", str(out)])
    assert score_result.exit_code == 0, score_result.stdout
    assert (out / "scores.json").is_file()
    assert (out / "summary.md").is_file()

    scores = json.loads((out / "scores.json").read_text(encoding="utf-8"))
    assert scores["overall"] == 1.0
    assert scores["n_passed"] == 8
    assert scores["n_tasks"] == 8

    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "CompanionBench run summary" in summary
    assert "8/8 tasks passed" in summary
    assert "Overall score" in summary


def test_run_rejects_bad_model_ref(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--manifest",
            str(SMOKE),
            "--model",
            "not-a-valid-ref",
            "--out",
            str(tmp_path / "x"),
        ],
    )
    assert result.exit_code == 1


def test_export_creates_parquet(tmp_path: Path) -> None:
    pytest.importorskip("polars")
    out = tmp_path / "smoke"
    runner.invoke(
        app,
        ["run", "--manifest", str(SMOKE), "--model", "mock/empathetic-v1", "--out", str(out)],
    )
    result = runner.invoke(app, ["export", "--run", str(out), "--format", "parquet"])
    assert result.exit_code == 0, result.stdout
    assert (out / "export" / "events.parquet").is_file()


def test_export_duckdb_not_implemented_message(tmp_path: Path) -> None:
    out = tmp_path / "smoke"
    runner.invoke(
        app,
        ["run", "--manifest", str(SMOKE), "--model", "mock/empathetic-v1", "--out", str(out)],
    )
    result = runner.invoke(app, ["export", "--run", str(out), "--format", "duckdb"])
    assert result.exit_code == 1
