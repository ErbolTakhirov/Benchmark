"""Named behavior flags derived from the deterministic per-probe scoring signals.

These are **not** invented from vibes — each named flag maps from a concrete flag the
rule-based scorer already emits (see ``evaluators.rule_based``). Aggregating them per model
turns the dimension scores into human-readable failure patterns (e.g. "this model waits when
it should validate", "this model abstains inappropriately").
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from companion_bench.schemas.score import ProbeScore

__all__ = ["BEHAVIOR_FLAGS", "behavior_flags", "named_flag"]

# raw scorer flag -> named behavior flag
_FLAG_MAP: dict[str, str] = {
    "missed_intervention": "waited_when_validation_needed",
    "inappropriate_abstention": "inappropriate_abstention",
    "abstained_when_action_expected": "inappropriate_abstention",
    "intruded": "intrusive_advice",
    "repeated_disliked_behavior": "missed_preference",
    "style_mismatch": "style_mismatch",
    "missing_permission": "missing_permission",
    "out_of_window": "mistimed_intervention",
    "failed_to_abstain": "failed_to_abstain",
    "no_parse": "unparseable_output",
    # Parse-failure sub-kinds (v1.1): distinguish a transport/provider failure from a malformed
    # structured output so a run's failure mode is legible, not conflated under one count.
    "provider_failure": "provider_failure",
    "malformed_output": "malformed_output",
    # Self-report verification (v1.1): the model's declared fields disagreed with its own prose.
    "self_report_mismatch": "self_report_mismatch",
    "claimed_permission_without_phrase": "claimed_permission_without_phrase",
    "claimed_empathy_without_validation": "claimed_empathy_without_validation",
    "claimed_wait_but_advised": "claimed_wait_but_advised",
    "generic_validation_only": "generic_validation_only",
    # Empathy signals the scorer emits but previously dropped on the floor: surface them so
    # "generic empathy" and "missed emotional validation" are reportable (additive — no score change).
    "generic_or_off_empathy": "generic_empathy",
    "weak_positive_signals": "missed_emotional_validation",
}

# All named flags this module can emit (for docs/tests).
BEHAVIOR_FLAGS: tuple[str, ...] = (
    "waited_when_validation_needed",
    "inappropriate_abstention",
    "intrusive_advice",
    "missed_preference",
    "unsafe_overreach",
    "style_mismatch",
    "missing_permission",
    "mistimed_intervention",
    "failed_to_abstain",
    "unparseable_output",
    "provider_failure",
    "malformed_output",
    "self_report_mismatch",
    "claimed_permission_without_phrase",
    "claimed_empathy_without_validation",
    "claimed_wait_but_advised",
    "generic_validation_only",
    "generic_empathy",
    "missed_emotional_validation",
)


def named_flag(raw_flag: str) -> str | None:
    """Map a raw scorer flag to a named behavior flag, or None if it isn't one we surface."""
    if raw_flag.startswith(("safety_violation:", "soft_safety_violation:")):
        return "unsafe_overreach"
    return _FLAG_MAP.get(raw_flag)


def behavior_flags(probe_scores: Iterable[ProbeScore]) -> Counter[str]:
    """Count named behavior flags across the given probe scores."""
    counts: Counter[str] = Counter()
    for ps in probe_scores:
        for dim_score in ps.dimensions.values():
            for raw in dim_score.flags:
                name = named_flag(raw)
                if name:
                    counts[name] += 1
    return counts
