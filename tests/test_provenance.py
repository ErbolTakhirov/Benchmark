"""Provenance: git-commit capture degrades gracefully and reaches run metadata + the summary."""

from __future__ import annotations

from pathlib import Path

from companion_bench.evaluators.aggregate import render_summary, score_run
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ModelSpec
from companion_bench.storage.jsonl import read_events
from companion_bench.utils.gitmeta import git_commit
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"


def test_git_commit_returns_str_or_none() -> None:
    commit = git_commit()
    assert commit is None or (isinstance(commit, str) and commit)


def test_git_commit_outside_a_repo_is_none(tmp_path: Path) -> None:
    assert git_commit(cwd=tmp_path) is None


async def test_run_metadata_and_summary_carry_provenance(tmp_path: Path) -> None:
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock())
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=manifest.run,
        out_dir=tmp_path / "r",
        manifest_path=str(SMOKE),
    )
    scores = score_run(
        tasks,
        read_events(result.events_path),
        run_id=result.run_id,
        model_id="mock/empathetic-v1",
        provider="mock",
        generated_at="t",
    )
    summary = render_summary(result.metadata, scores)
    assert "## Provenance" in summary
    assert "Commit:" in summary
    assert "## Parse quality (experimental)" in summary
