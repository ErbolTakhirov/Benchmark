"""Validation tests for the shipped manifests and authored tasks."""

from __future__ import annotations

from pathlib import Path

import pytest

from companion_bench.runner.manifest import (
    load_manifest_and_tasks,
    validate_manifest,
)
from companion_bench.schemas.task import Family
from companion_bench.utils.errors import ManifestError

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"
MVP = REPO_ROOT / "manifests" / "mvp.yaml"


def test_smoke_manifest_validates_with_eight_balanced_tasks() -> None:
    report = validate_manifest(SMOKE)
    assert report.ok, report.errors
    assert report.n_tasks == 8
    assert report.families == {"adaptation": 2, "empathy": 2, "initiative": 2, "timing": 2}
    assert len(set(report.task_ids)) == 8


def test_mvp_manifest_validates() -> None:
    report = validate_manifest(MVP)
    assert report.ok, report.errors
    assert report.n_tasks == 8


def test_load_manifest_and_tasks_returns_all_probes() -> None:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    assert manifest.name == "smoke"
    assert len(tasks) == 8
    # 14 probes total across the suite (see task authoring notes).
    assert sum(len(t.probes) for t in tasks) == 14
    # The smoke slice is intentionally the four original families; the full suite
    # (manifests/full.yaml) covers all six, including abstention and safety.
    assert {t.family for t in tasks} == {
        Family.INITIATIVE,
        Family.EMPATHY,
        Family.TIMING,
        Family.ADAPTATION,
    }


def test_every_task_declares_abstention_and_a_window() -> None:
    _, tasks = load_manifest_and_tasks(SMOKE)
    for task in tasks:
        assert task.expected_abstention_behavior.strip(), task.task_id
        # Window probe ids must be a subset of the task's probes (schema guarantees it).
        assert set(task.allowed_intervention_window.probe_ids) <= set(task.probe_ids)


def test_missing_manifest_reports_not_ok() -> None:
    report = validate_manifest(REPO_ROOT / "manifests" / "does-not-exist.yaml")
    assert report.ok is False
    assert report.errors


def test_manifest_with_unmatched_pattern_is_reported(tmp_path: Path) -> None:
    manifest = tmp_path / "broken.yaml"
    manifest.write_text(
        "name: broken\nversion: 1.0.0\ntask_paths:\n  - 'nope/*.yaml'\n",
        encoding="utf-8",
    )
    report = validate_manifest(manifest)
    assert report.ok is False
    assert any("matched no files" in e for e in report.errors)


def test_load_manifest_and_tasks_raises_on_empty_match(tmp_path: Path) -> None:
    manifest = tmp_path / "empty.yaml"
    manifest.write_text(
        "name: empty\nversion: 1.0.0\ntask_paths:\n  - 'nothing/*.yaml'\n",
        encoding="utf-8",
    )
    with pytest.raises(ManifestError, match="no task files matched"):
        load_manifest_and_tasks(manifest)
