"""LLM-as-judge schemas — a *separate*, explicitly-labeled artifact.

Judge output never overwrites or merges into the rule-based ``scores.json``. It lives in its own
``judge_scores.json`` / ``judge_events.jsonl`` so a reader always knows which numbers came from a
(biased, opt-in) model judge versus the deterministic rule scorer. Dimensions reuse the canonical
:class:`~companion_bench.schemas.task.Dimension` enum for calibration.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from companion_bench.schemas.task import Dimension

__all__ = ["JudgeProbeResult", "JudgeRunScores", "JudgeVerdict"]

_Unit = Annotated[float, Field(ge=0.0, le=1.0)]


class JudgeVerdict(BaseModel):
    """A judge's per-dimension verdict for one response (values in ``[0, 1]``)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension_scores: dict[Dimension, _Unit] = Field(default_factory=dict)
    confidence: _Unit = 1.0
    rationale: str = ""
    flags: tuple[str, ...] = ()
    uncertainty_notes: str = ""


class JudgeProbeResult(BaseModel):
    """The judge's outcome for one response, including explicit failure capture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    response_id: str
    task_id: str
    probe_id: str
    model_id: str | None = None
    parsed: bool
    verdict: JudgeVerdict | None = None
    error: str | None = None
    # A short excerpt of the judge's raw output for auditing (truncated; never a whole transcript).
    raw_excerpt: str = ""


class JudgeRunScores(BaseModel):
    """Top-level judge artifact written to ``judge_scores.json`` (distinct from rule scores)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    judge_run_id: str
    judge_provider: str
    judge_model: str
    judge_prompt_version: str
    generated_at: str
    # "mock" = offline deterministic simulator (validates the pipeline, not judge quality);
    # "live" = real provider calls.
    source: str
    probe_results: tuple[JudgeProbeResult, ...]
    by_dimension: dict[Dimension, float | None] = Field(default_factory=dict)
    n_probes: int = 0
    n_failed: int = 0
    total_cost_usd: float | None = None
    scoring_note: str = (
        "Judge output is a biased, opt-in calibration signal — reported ALONGSIDE, never "
        "replacing, the rule-based scores."
    )
