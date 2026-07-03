"""Suite-level task-quality invariants, shared by the ``validate --strict-quality`` CLI gate and
the test suite so there is exactly one implementation of each check.

The schema (``schemas/task.py``) already enforces *structural* integrity (probe ids, window
references). These are the *authoring-quality* invariants a valid-but-weak task can still violate:
missing failure modes, a safety task with no boundaries, a positive signal that trips its own
safety boundary, keyword-echo leakage, and family/coverage thresholds.

Findings are split into **errors** (genuine defects — the shipped suite must be clean) and
**warnings** (known, accepted limitations such as keyword echo — surfaced, never a hard gate). The
positive-signal/forbidden-pattern check here is a fast per-signal approximation;
``tests/test_signal_disjointness.py`` drives the real scoring pipeline and remains authoritative
(it also catches join-boundary matches this check cannot see).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from companion_bench.schemas.model import Decision
from companion_bench.schemas.task import Family, ScriptTurn, Task

__all__ = [
    "MIN_HELDOUT_PER_FAMILY",
    "MIN_PUBLIC_PER_FAMILY",
    "QualityReport",
    "check_task_quality",
    "difficulty_distribution",
    "family_balance",
    "missing_failure_modes",
    "positive_signal_overlaps",
    "prompt_leakage",
    "safety_task_without_boundaries",
]

# Per-family coverage thresholds for the public / held-out suites (single source of truth; the
# task-suite tests import these rather than re-declaring them).
MIN_PUBLIC_PER_FAMILY = 25
MIN_HELDOUT_PER_FAMILY = 6

# Prompt phrases shorter than this are ignored for the echo check — short signals ("i hear you")
# recur naturally and would be all noise.
_MIN_ECHO_LEN = 12


@dataclass(frozen=True)
class QualityReport:
    """Result of a strict-quality pass over a task list."""

    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    difficulty: dict[str, int]
    family_counts: dict[str, int]

    @property
    def ok(self) -> bool:
        return not self.errors


def _positive_signals(task: Task) -> list[str]:
    """Every phrase a well-behaved model is *rewarded* for producing (task + probe level)."""
    signals = list(task.positive_signals)
    for probe in task.probes:
        signals.extend(probe.positive_signals)
        signals.extend(probe.expected_target_keywords)
    return [s for s in signals if s.strip()]


def missing_failure_modes(task: Task) -> bool:
    """True when the task has no non-empty ``metadata.failure_modes`` list."""
    fm = task.metadata.get("failure_modes")
    return not (isinstance(fm, list) and fm)


def safety_task_without_boundaries(task: Task) -> bool:
    """True when a SAFETY-family task declares no ``safety_boundaries`` (safety would score 1.0)."""
    return task.family is Family.SAFETY and not task.safety_boundaries


def positive_signal_overlaps(task: Task) -> list[tuple[str, str]]:
    """``(signal, pattern)`` pairs where a positive signal trips the task's own forbidden pattern."""
    signals = _positive_signals(task)
    hits: list[tuple[str, str]] = []
    for boundary in task.safety_boundaries:
        for pattern in boundary.forbidden_patterns:
            try:
                rx = re.compile(pattern, re.IGNORECASE)
            except re.error:
                continue  # a bad regex is the scorer's problem, not this approximation's
            hits.extend((signal, pattern) for signal in signals if rx.search(signal))
    return hits


def prompt_leakage(task: Task, *, min_len: int = _MIN_ECHO_LEN) -> list[str]:
    """Positive signals that appear verbatim in the visible (non-assistant) prompt (echo risk)."""
    visible = " \n ".join(
        turn.content.casefold()
        for turn in task.conversation_turns
        if isinstance(turn, ScriptTurn) and turn.role in {"user", "context", "system"}
    )
    leaked = {
        signal
        for signal in _positive_signals(task)
        if len(signal) >= min_len and signal.casefold() in visible
    }
    return sorted(leaked)


def difficulty_distribution(tasks: list[Task]) -> dict[str, int]:
    return dict(sorted(Counter(t.difficulty.value for t in tasks).items()))


def family_balance(tasks: list[Task]) -> dict[str, int]:
    return dict(sorted(Counter(t.family.value for t in tasks).items()))


def check_task_quality(
    tasks: list[Task],
    *,
    enforce_family_counts: bool = False,
    heldout_ids: frozenset[str] = frozenset(),
) -> QualityReport:
    """Run every invariant over ``tasks``.

    ``enforce_family_counts`` gates the 25-per-family public threshold (meaningful only for the
    full suite, not arbitrary manifests). ``heldout_ids`` (the sibling held-out split, if any) lets
    the check confirm no held-out task leaked into this manifest.
    """
    errors: list[str] = []
    warnings: list[str] = []
    for task in tasks:
        if missing_failure_modes(task):
            errors.append(f"{task.task_id}: missing a non-empty metadata.failure_modes list")
        if safety_task_without_boundaries(task):
            errors.append(f"{task.task_id}: safety-family task declares no safety_boundaries")
        for signal, pattern in positive_signal_overlaps(task):
            errors.append(
                f"{task.task_id}: positive signal {signal!r} matches its own forbidden pattern "
                f"{pattern!r} (see tests/test_signal_disjointness.py for the authoritative check)"
            )
        for signal in prompt_leakage(task):
            warnings.append(
                f"{task.task_id}: positive signal {signal!r} appears verbatim in the prompt "
                "(keyword-echo risk — a documented scoring limitation)"
            )

    if not any(
        probe.expected_decision in {Decision.WAIT, Decision.ABSTAIN}
        for task in tasks
        for probe in task.probes
    ):
        errors.append("suite has no WAIT/ABSTAIN probes — abstention/timing negatives are untested")

    if heldout_ids:
        leaked = sorted({t.task_id for t in tasks} & heldout_ids)
        if leaked:
            errors.append(f"held-out tasks leak into this manifest: {leaked}")

    family_counts = family_balance(tasks)
    if enforce_family_counts:
        for family in Family:
            count = family_counts.get(family.value, 0)
            if count < MIN_PUBLIC_PER_FAMILY:
                errors.append(
                    f"family {family.value!r}: {count} task(s) < {MIN_PUBLIC_PER_FAMILY} threshold"
                )

    return QualityReport(
        errors=tuple(errors),
        warnings=tuple(warnings),
        difficulty=difficulty_distribution(tasks),
        family_counts=family_counts,
    )
