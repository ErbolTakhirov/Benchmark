"""Suite-wide guard: a task's own positive signals must never trip its own safety boundaries.

The mock scorer's mechanism (see ``adapters/mock.py::_compose_supportive`` and
``evaluators/rule_based.py::_safety``): on an INTERVENE probe, ``empathetic-v1`` builds its
message by joining ``task.positive_signals + probe.positive_signals`` and
``probe.expected_target_keywords`` verbatim into the response text; the safety scorer then
regex-searches (case-insensitive) every one of the task's ``safety_boundaries[].
forbidden_patterns`` against that same response text. If a forbidden pattern happens to
regex-match inside one of the task's own positive signals or target keywords, the *correct*
mock persona trips a safety violation just by giving its right answer — this test catches that
before it ships, rather than relying on authors noticing it by hand.

(The reverse direction — a positive signal being a short substring of a longer forbidden
pattern — is not a bug: the longer pattern won't spuriously appear in a message that only
contains the shorter signal, so it is intentionally not checked here.)
"""

from __future__ import annotations

import re

from companion_bench.schemas.task import Decision, ProbeTurn, Task
from suite_helpers import load_full_tasks, load_heldout_tasks


def _pattern_present(text: str, pattern: str) -> bool:
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in text.lower()


def _intervene_signals(task: Task, probe: ProbeTurn) -> list[str]:
    """Every string the empathetic mock would embed verbatim in this probe's response."""
    return [
        *task.positive_signals,
        *probe.positive_signals,
        *probe.expected_target_keywords,
    ]


def _check_task(task: Task) -> list[str]:
    patterns = [p for b in task.safety_boundaries for p in b.forbidden_patterns]
    if not patterns:
        return []
    violations: list[str] = []
    for probe in task.probes:
        if probe.expected_decision is not Decision.INTERVENE:
            continue  # WAIT -> empty message; ABSTAIN -> fixed boilerplate; neither uses signals
        for signal in _intervene_signals(task, probe):
            for pattern in patterns:
                if _pattern_present(signal, pattern):
                    violations.append(
                        f"{task.task_id}/{probe.probe_id}: signal {signal!r} "
                        f"matches forbidden_pattern {pattern!r}"
                    )
    return violations


def test_no_task_self_trips_its_own_safety_boundaries() -> None:
    violations: list[str] = []
    for task in [*load_full_tasks(), *load_heldout_tasks()]:
        violations.extend(_check_task(task))
    assert not violations, "\n".join(violations)
