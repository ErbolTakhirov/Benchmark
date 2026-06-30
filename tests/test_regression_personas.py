"""Regression: degenerate personas must score worse and get the right behavior flags.

A benchmark that cannot tell apart an always-silent, an always-intrusive, and a calibrated
companion is not measuring anything. These pin that the suite separates them and surfaces the
named failure modes.
"""

from __future__ import annotations

from suite_helpers import load_full_tasks, score_suite, suite_flags, suite_overall


def test_calibrated_beats_silent_and_intrusive_overall() -> None:
    tasks = load_full_tasks()
    emp = suite_overall(score_suite(tasks, "empathetic-v1"))
    sil = suite_overall(score_suite(tasks, "silent-v1"))
    intr = suite_overall(score_suite(tasks, "intrusive-v1"))
    assert emp > sil, (emp, sil)
    assert emp > intr, (emp, intr)
    # A harmful proactive model must not beat even a merely passive one on average.
    assert emp > max(sil, intr)


def test_always_silent_misses_needed_interventions() -> None:
    flags = suite_flags(score_suite(load_full_tasks(), "silent-v1"))
    assert flags.get("waited_when_validation_needed", 0) >= 1, "always-silent missed nothing?"


def test_always_intrusive_trips_intrusion_and_safety() -> None:
    flags = suite_flags(score_suite(load_full_tasks(), "intrusive-v1"))
    assert flags.get("intrusive_advice", 0) >= 1, "no intrusion flagged for always-intrusive"
    assert flags.get("unsafe_overreach", 0) >= 1, "no safety overreach flagged for always-intrusive"


def test_generic_empathy_is_detected_for_intrusive() -> None:
    flags = suite_flags(score_suite(load_full_tasks(), "intrusive-v1"))
    # intrusive-v1 leans on generic, context-wrong empathy (the task's negative_signals).
    assert flags.get("generic_empathy", 0) >= 1, "generic empathy not detected for intrusive-v1"
