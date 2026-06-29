"""Model-facing schemas: the companion turn envelope, requests, and responses.

This module is the dependency leaf of the schema package — it imports nothing else
from ``companion_bench`` so that tasks, runs, and scores can all build on top of it.

The central idea is the :class:`CompanionTurn`: a small structured envelope that a
companion / proactive-assistant model returns at each decision point ("probe"). Making
the decision explicit (intervene / wait / abstain) is what lets the MVP score behavior
deterministically and transparently, and mirrors how real proactive systems actually
work — they decide *whether* to act before deciding *what* to say.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

__all__ = [
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CompanionTurn",
    "Decision",
    "ModelSpec",
    "Role",
    "Style",
    "TokenUsage",
]


class Role(StrEnum):
    """Speaker role in a chat transcript."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Decision(StrEnum):
    """The proactive decision a companion makes at a probe point.

    - ``intervene``: actively say/do something (the message is user-facing).
    - ``wait``: deliberately stay quiet this turn (no useful/appropriate action now).
    - ``abstain``: decline to act on a request or topic (e.g. out of scope, unsafe).
    """

    INTERVENE = "intervene"
    WAIT = "wait"
    ABSTAIN = "abstain"


class Style(StrEnum):
    """Response style / tone a companion can adopt.

    The evaluator uses a small compatibility map between these (see
    ``evaluators.rule_based``) so that, e.g., ``gentle`` and ``reassuring`` partially
    satisfy each other rather than being all-or-nothing.
    """

    GENTLE = "gentle"
    REASSURING = "reassuring"
    DIRECT = "direct"
    PRACTICAL = "practical"
    PLAYFUL = "playful"
    CURIOUS = "curious"
    CELEBRATORY = "celebratory"
    NEUTRAL = "neutral"


class ChatMessage(BaseModel):
    """A single message in a transcript sent to or returned from a model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Role
    content: str


class CompanionTurn(BaseModel):
    """Structured envelope a companion model returns at each probe.

    Parsed from the model's raw text by adapters via :meth:`from_text`. Extra keys are
    ignored (real models are messy); a turn that cannot be parsed at all is recorded as a
    failure by the engine rather than silently defaulted.
    """

    # Tolerant of unknown keys so a well-formed-but-chatty model output still parses.
    model_config = ConfigDict(extra="ignore", frozen=True)

    decision: Decision
    message: str = ""
    target: str | None = None
    style: Style | None = None
    ask_permission: bool = False
    rationale: str | None = None

    @classmethod
    def from_text(cls, text: str) -> CompanionTurn | None:
        """Best-effort parse of a model's raw text into a :class:`CompanionTurn`.

        Handles fenced ```json blocks and JSON embedded in surrounding prose. Returns
        ``None`` if no valid envelope can be extracted (the caller logs a failure).
        """
        candidate = text.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.DOTALL)
        if fence:
            candidate = fence.group(1)
        else:
            start, end = candidate.find("{"), candidate.rfind("}")
            if start != -1 and end > start:
                candidate = candidate[start : end + 1]
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        try:
            return cls.model_validate(data)
        except ValidationError:
            return None

    def to_json(self) -> str:
        """Serialize to the canonical JSON the adapters request from real models."""
        return self.model_dump_json()


class TokenUsage(BaseModel):
    """Token accounting as reported by a provider. Missing values stay ``None``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ModelSpec(BaseModel):
    """A parsed ``provider/model`` reference, e.g. ``openai/gpt-4o-mini``.

    The model portion may itself contain slashes (e.g. OpenRouter's
    ``openrouter/meta-llama/llama-3.1-70b-instruct``); only the first slash separates the
    provider from the model.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model: str
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider", "model")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("provider and model must be non-empty")
        return value

    @classmethod
    def parse(cls, ref: str, *, params: dict[str, Any] | None = None) -> ModelSpec:
        """Parse a ``provider/model`` string into a :class:`ModelSpec`."""
        provider, sep, model = ref.partition("/")
        if not sep or not provider or not model:
            raise ValueError(
                f"Invalid model reference {ref!r}; expected 'provider/model' "
                "(e.g. 'mock/empathetic-v1', 'openai/gpt-4o-mini')."
            )
        return cls(provider=provider, model=model, params=params or {})

    @property
    def ref(self) -> str:
        """The canonical ``provider/model`` string."""
        return f"{self.provider}/{self.model}"

    @property
    def slug(self) -> str:
        """A filesystem-safe slug for this model reference."""
        return re.sub(r"[^A-Za-z0-9._-]+", "-", self.ref)


class ChatRequest(BaseModel):
    """A single request to an adapter's ``generate`` method.

    ``simulation_context`` is read **only** by :class:`~companion_bench.adapters.mock`.
    Real provider adapters ignore it entirely and send only ``messages``; this keeps the
    deterministic mock simulator cleanly separated from real model evaluation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: ModelSpec
    messages: tuple[ChatMessage, ...]
    temperature: float = 0.0
    max_tokens: int | None = 512
    response_format: Literal["text", "json_object"] = "json_object"
    timeout_s: float = 60.0
    simulation_context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """A normalized response from any adapter.

    Transport-level failures are raised as exceptions (and recorded by the engine as
    failure events); a response whose envelope could not be parsed sets
    ``companion_turn`` to ``None`` with ``parsed=False`` so the failure is explicit.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model: str
    content: str
    companion_turn: CompanionTurn | None = None
    parsed: bool = False
    token_usage: TokenUsage | None = None
    latency_ms: float | None = None
    estimated_cost_usd: float | None = None
    raw: dict[str, Any] | None = None
