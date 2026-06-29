"""CLI tests for model-set runs, multi-model score/report, and live guardrails (offline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from companion_bench.cli import app

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"
MOCK_SET = REPO_ROOT / "configs" / "model_sets" / "mock-profiles.yaml"
runner = CliRunner()


def test_modelset_run_score_report(tmp_path: Path) -> None:
    out = tmp_path / "multi"
    run_res = runner.invoke(
        app, ["run", "-m", str(SMOKE), "--model-set", str(MOCK_SET), "--out", str(out)]
    )
    assert run_res.exit_code == 0, run_res.stdout
    assert (out / "modelset.json").is_file()
    assert (out / "mock-empathetic-v1" / "run.json").is_file()
    assert (out / "mock-intrusive-v1" / "run.json").is_file()

    score_res = runner.invoke(app, ["score", "--run", str(out)])
    assert score_res.exit_code == 0, score_res.stdout
    assert (out / "mock-empathetic-v1" / "scores.json").is_file()

    report_res = runner.invoke(app, ["report", "--run", str(out)])
    assert report_res.exit_code == 0, report_res.stdout
    assert "comparison" in report_res.stdout.lower()


def test_limit_models_caps_the_set(tmp_path: Path) -> None:
    out = tmp_path / "m"
    res = runner.invoke(
        app,
        [
            "run",
            "-m",
            str(SMOKE),
            "--model-set",
            str(MOCK_SET),
            "--out",
            str(out),
            "--limit-models",
            "1",
        ],
    )
    assert res.exit_code == 0
    index = json.loads((out / "modelset.json").read_text())
    assert len(index["models"]) == 1


def test_limit_tasks_caps_tasks(tmp_path: Path) -> None:
    out = tmp_path / "single"
    res = runner.invoke(
        app,
        [
            "run",
            "-m",
            str(SMOKE),
            "--model",
            "mock/empathetic-v1",
            "--out",
            str(out),
            "--limit-tasks",
            "2",
        ],
    )
    assert res.exit_code == 0
    meta = json.loads((out / "run.json").read_text())
    assert len(meta["task_ids"]) == 2


def test_run_rejects_model_and_model_set(tmp_path: Path) -> None:
    res = runner.invoke(
        app,
        [
            "run",
            "-m",
            str(SMOKE),
            "--model",
            "mock/empathetic-v1",
            "--model-set",
            str(MOCK_SET),
            "--out",
            str(tmp_path / "x"),
        ],
    )
    assert res.exit_code == 1


def test_run_requires_a_model(tmp_path: Path) -> None:
    res = runner.invoke(app, ["run", "-m", str(SMOKE), "--out", str(tmp_path / "x")])
    assert res.exit_code == 1


def test_real_model_requires_live_flag(tmp_path: Path) -> None:
    # Must NOT make a network call — it fails the guardrail before running.
    res = runner.invoke(
        app,
        ["run", "-m", str(SMOKE), "--model", "openai/gpt-4o-mini", "--out", str(tmp_path / "x")],
    )
    assert res.exit_code == 1


def test_live_flag_requires_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPANIONBENCH_LIVE", raising=False)
    res = runner.invoke(
        app,
        [
            "run",
            "-m",
            str(SMOKE),
            "--model",
            "openai/gpt-4o-mini",
            "--out",
            str(tmp_path / "x"),
            "--live",
            "--yes",
        ],
    )
    assert res.exit_code == 1  # --live needs COMPANIONBENCH_LIVE=1
    assert not (tmp_path / "x").exists()  # nothing ran


def test_report_unscored_run_fails(tmp_path: Path) -> None:
    out = tmp_path / "single"
    runner.invoke(
        app, ["run", "-m", str(SMOKE), "--model", "mock/empathetic-v1", "--out", str(out)]
    )
    res = runner.invoke(app, ["report", "--run", str(out)])
    assert res.exit_code == 1  # not scored yet
