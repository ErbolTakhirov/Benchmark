"""Guard: raw runs, secrets, and private annotations must never be git-tracked."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_KEEP_PRIVATE = {"README.md", ".gitkeep"}


def _tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        pytest.skip("not a git checkout")
    return result.stdout.splitlines()


def test_no_raw_runs_env_or_private_labels_are_tracked() -> None:
    offenders = [
        path
        for path in _tracked_files()
        if path == ".env"
        or path.startswith("runs/")
        or path.endswith((".parquet", ".duckdb"))
        or (path.startswith("data/gold/private/") and Path(path).name not in _KEEP_PRIVATE)
        or path.endswith("events.jsonl")
    ]
    assert not offenders, offenders
