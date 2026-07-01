"""Suite-wide guard: a task's own positive signals must never trip its own safety boundaries.

Drives every task that declares ``safety_boundaries`` through the **real** pipeline
(``ConversationDriver`` + ``MockAdapter`` + the rule-based scorer, via
``suite_helpers.score_task_with_mock``) with the ``empathetic-v1`` persona — the mock that echoes
a task's own ``positive_signals``/``expected_target_keywords`` verbatim into its response (see
``adapters/mock.py::_compose_supportive``). If a ``safety_boundaries[].forbidden_patterns`` entry
happens to match somewhere in that echoed text — whether inside a single signal or spanning the
join between several — the safety scorer (``evaluators/rule_based.py::_safety``) flags a
``safety_violation``/``soft_safety_violation`` on the *correct* answer, which is exactly the
authoring mistake this test exists to catch.

Driving the real pipeline, rather than re-deriving the mock's message composition and the
scorer's pattern matching by hand, means this test can never drift from the mechanism it models
and catches join-boundary cases a per-signal string check would miss.
"""

from __future__ import annotations

from companion_bench.schemas.score import TaskScore
from companion_bench.schemas.task import Dimension
from suite_helpers import load_full_tasks, load_heldout_tasks, score_task_with_mock


def _safety_violation_flags(score: TaskScore) -> list[str]:
    flags: list[str] = []
    for probe in score.probe_scores:
        dim = probe.dimensions.get(Dimension.SAFETY)
        if dim is None:
            continue
        flags.extend(f for f in dim.flags if "safety_violation" in f)
    return flags


def test_no_task_self_trips_its_own_safety_boundaries() -> None:
    tasks = [t for t in [*load_full_tasks(), *load_heldout_tasks()] if t.safety_boundaries]
    assert tasks, "expected at least one task with safety_boundaries"
    violations: list[str] = []
    for task in tasks:
        score = score_task_with_mock(task, "empathetic-v1")
        flags = _safety_violation_flags(score)
        if flags:
            violations.append(f"{task.task_id}: {flags}")
    assert not violations, "\n".join(violations)
