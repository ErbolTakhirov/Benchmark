"""Human gold-label schemas: per-annotator, per-response ratings for calibration.

These capture what a **human** thought of a companion response, so the rule-based scorer (and,
later, an LLM judge) can be *calibrated* against people — never replaced by them. One
:class:`GoldLabel` is one annotator's rating of one response; multiple annotators rating the same
response are multiple labels sharing a ``(task_id, probe_id, response_id)`` key, which is what makes
inter-rater agreement computable.

Privacy: annotators are identified only by an opaque ``annotator_id_hash`` — never a real name or
email. ``pii_check`` records that the annotator confirmed no personal data is present in free text.

Dimensions reuse the canonical :class:`~companion_bench.schemas.task.Dimension` enum so gold ratings
line up 1:1 with rule-based / judge dimensions. Human-friendly names (emotional attunement →
``empathy``, non-intrusion/abstention → ``abstention``, preference adaptation → ``adaptation``,
safety boundaries → ``safety``) live in ``data/gold/README.md``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from companion_bench.schemas.model import Decision, Style
from companion_bench.schemas.task import Dimension

__all__ = [
    "GoldDimensionRating",
    "GoldLabel",
    "GoldResponse",
    "OverallPreference",
]

# 1-5 Likert, or None when the annotator skipped this dimension.
_Rating = Annotated[int, Field(ge=1, le=5)] | None


class OverallPreference(StrEnum):
    """An annotator's holistic verdict on a response."""

    ACCEPT = "accept"
    REJECT = "reject"
    BORDERLINE = "borderline"


class GoldDimensionRating(BaseModel):
    """One annotator's rating of one dimension of one response.

    ``rating``/``confidence`` are 1-5 Likert or ``None`` (skipped). ``flags`` are free-text
    behavior tags the annotator noticed (mirroring the scorer's named flags where they overlap).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rating: _Rating = None
    confidence: _Rating = None
    rationale: str = ""
    flags: tuple[str, ...] = ()


class GoldLabel(BaseModel):
    """One annotator's full rating of one response (probe-level).

    Multiple annotators → multiple labels sharing ``(task_id, probe_id, response_id)``.
    Dimensions the annotator skipped may simply be absent from ``dimensions``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    gold_set_id: str
    version: str = "0.1"
    task_id: str
    probe_id: str
    response_id: str
    model_id: str | None = None
    annotator_id_hash: str
    annotation_timestamp: str
    dimensions: dict[Dimension, GoldDimensionRating] = Field(default_factory=dict)
    overall_preference: OverallPreference
    notes: str = ""
    # Provenance/honesty: keep it explicit whether these are real human labels or a fixture.
    source_type: str = "synthetic_pilot_labels"
    not_human_collected: bool = True
    purpose: str = "schema/test fixture only"
    license_note: str = "Original synthetic scenario, CC0-1.0. No real user data."
    pii_check: bool = True


class GoldResponse(BaseModel):
    """A sanitized companion response that gold labels rate.

    Kept separate from the labels so the *same* response can be re-scored by the rule-based scorer
    (and by a judge) and compared against the human ratings. Carries enough of the
    :class:`~companion_bench.schemas.model.CompanionTurn` envelope to rebuild a scoring outcome; a
    parse/format-issue case sets ``parsed=False`` and leaves ``decision=None`` with the raw
    ``output_text``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    response_id: str
    task_id: str
    probe_id: str
    model_id: str | None = None
    parsed: bool = True
    output_text: str = ""
    decision: Decision | None = None
    message: str = ""
    target: str | None = None
    style: Style | None = None
    ask_permission: bool = False
    note: str = ""
