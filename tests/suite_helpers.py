"""Shared helpers for full-suite tests.

Drives a task through the **real** conversation driver + mock adapter + rule-based scorer
(exactly what the engine does, minus retries), so suite-level assertions reflect the production
scoring path. Not a test module (no ``test_`` prefix), so pytest does not collect it.
"""

from __future__ import annotations

import asyncio
from collections import Counter
from pathlib import Path

from companion_bench.adapters.mock import MockAdapter
from companion_bench.evaluators.flags import behavior_flags
from companion_bench.evaluators.rule_based import ProbeOutcome, score_task
from companion_bench.runner.conversation import ConversationDriver
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ModelSpec
from companion_bench.schemas.run import RunConfig
from companion_bench.schemas.score import TaskScore
from companion_bench.schemas.task import Task

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL = REPO_ROOT / "manifests" / "full.yaml"
HELDOUT = REPO_ROOT / "manifests" / "heldout.yaml"


def load_full_tasks() -> list[Task]:
    _, tasks = load_manifest_and_tasks(FULL)
    return tasks


def load_heldout_tasks() -> list[Task]:
    _, tasks = load_manifest_and_tasks(HELDOUT)
    return tasks


async def _drive(task: Task, profile: str) -> TaskScore:
    driver = ConversationDriver(task, ModelSpec.parse(f"mock/{profile}"), RunConfig())
    adapter = MockAdapter()
    outcomes: dict[str, ProbeOutcome] = {}
    step = driver.next_probe()
    while step is not None:
        resp = await adapter.generate(step.request)
        outcomes[step.probe.probe_id] = ProbeOutcome(
            turn=resp.companion_turn, parsed=resp.parsed, output_text=resp.content
        )
        driver.record_response(resp.companion_turn)
        step = driver.next_probe()
    return score_task(task, outcomes)


def score_task_with_mock(task: Task, profile: str) -> TaskScore:
    """Drive one task through a mock profile and return its TaskScore (synchronous wrapper)."""
    return asyncio.run(_drive(task, profile))


def score_suite(tasks: list[Task], profile: str) -> list[TaskScore]:
    return [score_task_with_mock(t, profile) for t in tasks]


def suite_overall(scores: list[TaskScore]) -> float:
    return sum(s.total for s in scores) / len(scores) if scores else 0.0


def suite_flags(scores: list[TaskScore]) -> Counter[str]:
    flags: Counter[str] = Counter()
    for s in scores:
        flags.update(behavior_flags(s.probe_scores))
    return flags
