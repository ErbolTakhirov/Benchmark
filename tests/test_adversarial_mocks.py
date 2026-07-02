"""Adversarial mocks: each gaming vector must be penalized and/or flagged by the scorer.

A rule-based scorer is only defensible if it resists the obvious ways to game it. These drive the
real conversation driver + mock adapter + scorer (same path as the engine) for each adversarial
profile and assert the scorer does NOT reward the trick. Assertions are relative to the calibrated
``empathetic-v1`` baseline where possible, so they stay robust to weight tweaks.
"""

from __future__ import annotations

from companion_bench.schemas.task import Family
from suite_helpers import (
    load_full_tasks,
    load_heldout_tasks,
    score_suite,
    suite_flags,
    suite_overall,
)

TASKS = load_full_tasks()
ALL_TASKS = TASKS + load_heldout_tasks()


def _fam(family: Family) -> list:
    return [t for t in TASKS if t.family == family]


def test_generic_empathy_is_flagged_and_beaten() -> None:
    fam = _fam(Family.EMPATHY)
    generic = score_suite(fam, "generic-empathy-v1")
    assert suite_flags(generic).get("generic_validation_only", 0) >= 1
    # Canned niceness must not match the calibrated companion on the empathy family.
    assert suite_overall(generic) < suite_overall(score_suite(fam, "empathetic-v1"))


def test_style_liar_trips_self_report_mismatch() -> None:
    # Claims a gentle style while writing blunt prose -> the label is not trusted.
    assert suite_flags(score_suite(TASKS, "style-liar-v1")).get("self_report_mismatch", 0) >= 1


def test_permission_liar_is_flagged() -> None:
    # ask_permission=true without ever asking. Permission probes are rare, so scan every task.
    flags = suite_flags(score_suite(ALL_TASKS, "permission-liar-v1"))
    assert flags.get("claimed_permission_without_phrase", 0) >= 1


def test_wait_liar_is_flagged() -> None:
    # A 'wait' that smuggles advice is a covert intervention, not restraint.
    assert suite_flags(score_suite(TASKS, "wait-liar-v1")).get("claimed_wait_but_advised", 0) >= 1


def test_always_advise_fails_non_intrusion_family() -> None:
    fam = _fam(Family.ABSTENTION)
    advise = score_suite(fam, "always-advise-v1")
    flags = suite_flags(advise)
    assert flags.get("intrusive_advice", 0) + flags.get("inappropriate_abstention", 0) >= 1
    assert suite_overall(advise) < suite_overall(score_suite(fam, "empathetic-v1"))


def test_always_wait_fails_action_needed_and_gets_no_safety_boost() -> None:
    silent = score_suite(TASKS, "silent-v1")
    assert suite_overall(silent) < suite_overall(score_suite(TASKS, "empathetic-v1"))
    # It must be visibly missing needed interventions...
    assert suite_flags(silent).get("waited_when_validation_needed", 0) >= 1
    # ...and earn no free safety credit: a do-nothing bot should score low on the initiative family.
    init = _fam(Family.INITIATIVE)
    assert suite_overall(score_suite(init, "silent-v1")) < 0.5


def test_always_abstain_wins_only_where_abstention_expected() -> None:
    abst = suite_overall(score_suite(_fam(Family.ABSTENTION), "always-abstain-v1"))
    init_scores = score_suite(_fam(Family.INITIATIVE), "always-abstain-v1")
    init = suite_overall(init_scores)
    assert abst > init  # abstention is only right where it is expected
    assert init < 0.5  # declining everything fails the initiative family
    assert suite_flags(init_scores).get("inappropriate_abstention", 0) >= 1
