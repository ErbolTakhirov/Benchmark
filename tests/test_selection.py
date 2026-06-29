"""Deterministic task selection (family-balanced + shuffle)."""

from __future__ import annotations

from pathlib import Path

from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.runner.selection import select_tasks

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"


def _tasks() -> list:
    _, tasks = load_manifest_and_tasks(SMOKE)
    return tasks


def test_no_limit_returns_all() -> None:
    tasks = _tasks()
    assert select_tasks(tasks) == tasks


def test_family_balanced_one_per_family() -> None:
    tasks = _tasks()  # 8 tasks, 2 per family (4 families)
    chosen = select_tasks(tasks, limit=4, family_balanced=True)
    assert len(chosen) == 4
    assert len({t.family for t in chosen}) == 4  # one from each family


def test_family_balanced_is_deterministic() -> None:
    tasks = _tasks()
    a = [t.task_id for t in select_tasks(tasks, limit=5, family_balanced=True)]
    b = [t.task_id for t in select_tasks(tasks, limit=5, family_balanced=True)]
    assert a == b


def test_plain_limit_takes_first_n() -> None:
    tasks = _tasks()
    chosen = select_tasks(tasks, limit=2, family_balanced=False)
    assert chosen == tasks[:2]  # both adaptation (the old behavior, opt-in now)


def test_shuffle_seed_reproducible_and_seed_dependent() -> None:
    tasks = _tasks()
    one = [t.task_id for t in select_tasks(tasks, shuffle_seed=1)]
    one_again = [t.task_id for t in select_tasks(tasks, shuffle_seed=1)]
    two = [t.task_id for t in select_tasks(tasks, shuffle_seed=2)]
    assert one == one_again  # reproducible under a fixed seed
    assert one != two  # different seed -> different order (8! permutations)
    assert sorted(one) == sorted(t.task_id for t in tasks)  # same set, just reordered


def test_shuffle_then_family_balanced_stays_balanced() -> None:
    tasks = _tasks()
    chosen = select_tasks(tasks, limit=4, family_balanced=True, shuffle_seed=7)
    assert len({t.family for t in chosen}) == 4
