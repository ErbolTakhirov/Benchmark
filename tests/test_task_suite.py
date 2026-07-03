"""The full public suite: family balance, required metadata, and the held-out hidden split."""

from __future__ import annotations

from collections import Counter

from companion_bench.runner.manifest import validate_manifest
from companion_bench.runner.quality_checks import (
    MIN_HELDOUT_PER_FAMILY,
    MIN_PUBLIC_PER_FAMILY,
    missing_failure_modes,
    safety_task_without_boundaries,
)
from companion_bench.schemas.task import Family
from suite_helpers import FULL, load_full_tasks, load_heldout_tasks


def test_full_manifest_validates_all_six_families() -> None:
    report = validate_manifest(FULL)
    assert report.ok, report.errors
    assert set(report.families) == {f.value for f in Family}  # all six families present


def test_at_least_min_public_tasks_per_family() -> None:
    counts = Counter(t.family for t in load_full_tasks())
    for fam in Family:
        assert counts[fam] >= MIN_PUBLIC_PER_FAMILY, (fam.value, counts[fam])


def test_at_least_min_heldout_tasks_per_family() -> None:
    counts = Counter(t.family for t in load_heldout_tasks())
    for fam in Family:
        assert counts[fam] >= MIN_HELDOUT_PER_FAMILY, (fam.value, counts[fam])


def test_every_task_declares_failure_modes_and_abstention() -> None:
    # Covers held-out too: this is an authoring-quality invariant, not a public-only one, and a
    # held-out task added later could otherwise ship silently incomplete.
    for t in [*load_full_tasks(), *load_heldout_tasks()]:
        assert t.expected_abstention_behavior.strip(), t.task_id
        assert not missing_failure_modes(t), f"{t.task_id} is missing metadata.failure_modes"


def test_every_safety_family_task_declares_boundaries() -> None:
    # Covers held-out too, for the same reason: an empty safety_boundaries list makes the SAFETY
    # dimension vacuously score 1.0 (evaluators/rule_based.py::_safety), silently regardless of
    # which split the task lives in.
    for t in [*load_full_tasks(), *load_heldout_tasks()]:
        if t.family is Family.SAFETY:
            assert not safety_task_without_boundaries(t), (
                f"{t.task_id} (safety family) declares no safety_boundaries"
            )


def test_public_tasks_marked_public() -> None:
    for t in load_full_tasks():
        # Originals predate the split marker; default them to public.
        assert t.metadata.get("split", "public") == "public", t.task_id


def test_heldout_split_exists_disjoint_and_excluded() -> None:
    public_ids = {t.task_id for t in load_full_tasks()}
    held = load_heldout_tasks()
    held_ids = {t.task_id for t in held}
    assert held_ids, "held-out split is empty"
    # A held-out task must NEVER leak into the public evaluation suite.
    assert public_ids.isdisjoint(held_ids), sorted(public_ids & held_ids)
    # Every family contributes at least one held-out task.
    assert {t.family for t in held} == set(Family)
    # Held-out tasks mark themselves hidden.
    for t in held:
        assert t.metadata.get("split") == "hidden", t.task_id
