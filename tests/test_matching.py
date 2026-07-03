"""Whole-token, normalized signal matching (scoring v1.2.0).

Pins the behavior of the low-level `_contains` matcher: it must match author-written signal phrases
as whole tokens (no "help" inside "helpless"), tolerate non-word edges ($/digits/punctuation), and
normalize case + whitespace — without ever treating the needle as a regex.
"""

from __future__ import annotations

import pytest

from companion_bench.evaluators.rule_based import _contains, _coverage, _fraction_present


@pytest.mark.parametrize(
    ("haystack", "needle", "expected"),
    [
        # The headline word-boundary bug: a signal must not match inside a larger word.
        ("you are helpless here", "help", False),
        ("i can help with that", "help", True),
        ("that is honest feedback", "hon", False),  # short keyword no longer trips inside "honest"
        ("hey hon, take your time", "hon", True),
        # Non-word edges ($ / digits) are tolerated — whole "token" still bounded correctly.
        ("it was an $800 surprise", "$800", True),
        ("it was an $8000 surprise", "$800", False),
        ("let's meet at 9am eastern", "9am", True),
        ("let's meet at 99am", "9am", False),
        # Case + whitespace + spacing normalization.
        ("I'M   HERE for you", "i'm here", True),
        ("i am here for you", "i'm here", False),
        ("take\tyour   time now", "take your time", True),
        # Punctuation adjacency counts as a boundary.
        ("calm down, it is fine", "calm down", True),
        ("", "help", False),
        ("anything", "   ", False),  # empty/whitespace needle never matches
    ],
)
def test_contains_whole_token_semantics(haystack: str, needle: str, expected: bool) -> None:
    assert _contains(haystack, needle) is expected


def test_needle_is_escaped_not_a_regex() -> None:
    # Regex metacharacters in a signal are literal, not a pattern.
    assert _contains("cost is $5 (five)", "$5 (five)") is True
    assert _contains("anything at all", ".*") is False


def test_coverage_and_fraction_use_whole_token_matching() -> None:
    # Whole phrases still cover fully (the mock echoes signals verbatim as whole tokens).
    assert _coverage("i'm here for you, take your time", ("i'm here", "take your time")) == 1.0
    # A short signal that only appears inside a bigger word no longer counts as covered.
    assert _coverage("you seem helpless", ("help",)) == 0.0
    assert _fraction_present("please calm down already", ("calm down",)) == 1.0
    assert _fraction_present("this is calmness itself", ("calm",)) == 0.0
