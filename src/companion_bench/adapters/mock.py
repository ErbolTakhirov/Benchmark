"""Deterministic mock adapter — a *simulator*, not a model under test.

The mock reads the ``simulation_context`` that the conversation builder attaches to each
request (real adapters ignore that channel entirely) and applies a fixed per-profile
policy. This lets the smoke benchmark run fully offline, produce byte-stable artifacts,
and — crucially — *differentiate* behaviors so scoring is demonstrably meaningful:

- ``empathetic-v1`` follows the ideal decision, matches the preferred style, references
  the right target, asks permission when needed, and avoids disliked/forbidden phrasing.
- ``intrusive-v1`` always intervenes, uses a blunt style, leans on generic empathy,
  repeats disliked behaviors, skips permission, and trips safety traps.
- ``silent-v1`` always waits.

There are also **adversarial** profiles, each a specific way to game rule-based scoring —
``generic-empathy-v1`` (canned validation), ``style-liar-v1`` (claims a soft style, blunt
prose), ``permission-liar-v1`` (``ask_permission=true`` without ever asking),
``always-advise-v1``, ``wait-liar-v1`` (a "wait" that smuggles advice), and
``always-abstain-v1``. The scorer must penalize / flag them (see ``tests/test_adversarial_mocks``).

Because the mock can see the answer key, **mock scores validate the pipeline, not model
quality.** That separation is the whole point of the ``simulation_context`` channel.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import ClassVar, cast

from companion_bench.adapters.base import ChatAdapter, register_adapter
from companion_bench.config.providers import ProviderSettings
from companion_bench.schemas.model import (
    ChatRequest,
    ChatResponse,
    CompanionTurn,
    Decision,
    Style,
    TokenUsage,
)
from companion_bench.utils.errors import AdapterError

__all__ = ["MockAdapter"]

_STYLE_OPENERS: dict[Style, str] = {
    Style.GENTLE: "Hey, no pressure at all —",
    Style.REASSURING: "You're doing okay —",
    Style.DIRECT: "Here's the thing —",
    Style.PRACTICAL: "Let's keep this concrete —",
    Style.PLAYFUL: "Okay, tiny idea —",
    Style.CURIOUS: "I'm curious —",
    Style.CELEBRATORY: "That's genuinely great —",
    Style.NEUTRAL: "",
}


def _tok(text: str) -> int:
    """A crude but deterministic token estimate (~4 chars/token)."""
    return max(1, len(text) // 4)


@dataclass(frozen=True)
class _Situation:
    """Typed view over the request's ``simulation_context`` (mock-only)."""

    ideal_decision: Decision = Decision.WAIT
    in_window: bool = False
    preferred_style: Style | None = None
    target_keywords: tuple[str, ...] = ()
    positive_signals: tuple[str, ...] = ()
    negative_signals: tuple[str, ...] = ()
    disliked_behaviors: tuple[str, ...] = ()
    requires_permission: bool = False
    sensitive: bool = False
    safety_traps: tuple[str, ...] = ()
    scene: str = ""

    @classmethod
    def from_ctx(cls, ctx: Mapping[str, object]) -> _Situation:
        def as_tuple(key: str) -> tuple[str, ...]:
            value = ctx.get(key)
            if not value:
                return ()
            if isinstance(value, str):  # guard against a bare string exploding into chars
                return (value,)
            return tuple(str(item) for item in cast(Iterable[object], value))

        style_raw = ctx.get("preferred_style")
        decision_raw = ctx.get("ideal_decision", Decision.WAIT.value)
        return cls(
            ideal_decision=Decision(str(decision_raw)),
            in_window=bool(ctx.get("in_window", False)),
            preferred_style=Style(str(style_raw)) if style_raw else None,
            target_keywords=as_tuple("target_keywords"),
            positive_signals=as_tuple("positive_signals"),
            negative_signals=as_tuple("negative_signals"),
            disliked_behaviors=as_tuple("disliked_behaviors"),
            requires_permission=bool(ctx.get("requires_permission", False)),
            sensitive=bool(ctx.get("sensitive", False)),
            safety_traps=as_tuple("safety_traps"),
            scene=str(ctx.get("scene", "")),
        )


def _compose_supportive(style: Style, s: _Situation) -> str:
    """A supportive message that surfaces the positive signals + target verbatim."""
    opener = _STYLE_OPENERS.get(style, "")
    body_parts: list[str] = list(s.positive_signals)
    if s.target_keywords:
        body_parts.append("we could focus on " + " and ".join(s.target_keywords))
    body = " ".join(body_parts) if body_parts else "I'm here with you"
    message = f"{opener} {body}".strip()
    if not message.endswith((".", "!", "?")):
        message += "."
    if s.requires_permission:
        message += " Would it be okay if I helped with that?"
    return message


def _empathetic(s: _Situation) -> CompanionTurn:
    if s.ideal_decision is Decision.INTERVENE:
        style = s.preferred_style or Style.GENTLE
        return CompanionTurn(
            decision=Decision.INTERVENE,
            message=_compose_supportive(style, s),
            target=", ".join(s.target_keywords) or None,
            style=style,
            ask_permission=s.requires_permission,
            rationale="Acting within the acceptable window, in the user's preferred style.",
        )
    if s.ideal_decision is Decision.ABSTAIN:
        return CompanionTurn(
            decision=Decision.ABSTAIN,
            message=(
                "I want to be careful here — that's outside what I should weigh in on, "
                "but I'm glad to listen or help you find the right person."
            ),
            style=s.preferred_style,
            ask_permission=s.sensitive,
            rationale="Respecting a boundary and staying within scope.",
        )
    return CompanionTurn(
        decision=Decision.WAIT,
        message="",
        style=None,
        ask_permission=False,
        rationale="No wanted intervention right now; giving the user space.",
    )


def _intrusive(s: _Situation) -> CompanionTurn:
    target = ", ".join(s.target_keywords) or "this"
    generic = s.negative_signals[0] if s.negative_signals else "I know exactly how you feel."
    pieces = [f"You really need to handle {target} right now.", generic]
    if s.disliked_behaviors:
        pieces.append(s.disliked_behaviors[0])
    if s.safety_traps:
        pieces.append(s.safety_traps[0])
    return CompanionTurn(
        decision=Decision.INTERVENE,
        message=" ".join(pieces),
        target=target,
        style=Style.DIRECT,
        ask_permission=False,
        rationale="Always push a suggestion, regardless of timing or preference.",
    )


def _silent(_: _Situation) -> CompanionTurn:
    return CompanionTurn(
        decision=Decision.WAIT,
        message="",
        style=None,
        ask_permission=False,
        rationale="Stay quiet no matter what.",
    )


# --------------------------------------------------------------------------- adversarial profiles
# These exist to keep the scorer honest: each is a specific way to *game* rule-based scoring, and
# the tests assert the scorer penalizes / flags them. They are simulator inputs, not model claims.


def _generic_empathy(_: _Situation) -> CompanionTurn:
    """Says the same context-free validation every time, regardless of the situation."""
    return CompanionTurn(
        decision=Decision.INTERVENE,
        message="I understand, that sounds really hard. I'm sorry you're going through this.",
        target=None,
        style=Style.GENTLE,
        ask_permission=False,
        rationale="Be generically supportive no matter what is actually needed.",
    )


def _style_liar(s: _Situation) -> CompanionTurn:
    """Follows the decision but self-declares a gentle style while writing blunt, pushy prose."""
    if s.ideal_decision is Decision.INTERVENE:
        target = ", ".join(s.target_keywords) or "this"
        return CompanionTurn(
            decision=Decision.INTERVENE,
            message=f"You need to handle {target} right now. Just do it, no excuses.",
            target=target,
            style=Style.GENTLE,  # claims gentle; the prose is anything but
            ask_permission=False,
            rationale="Claim a soft style while being blunt.",
        )
    return _empathetic(s)


def _permission_liar(s: _Situation) -> CompanionTurn:
    """Sets ask_permission=true but the message never actually asks — it acts first.

    Deliberately does NOT echo the probe's positive_signals: some permission probes author their
    signals *as* permission phrasing ("want me to nudge you?"), which would make this fixture
    accidentally ask. A fixed, non-asking message keeps it a reliable liar on every probe.
    """
    if s.ideal_decision is Decision.INTERVENE:
        target = ", ".join(s.target_keywords) or "it"
        return CompanionTurn(
            decision=Decision.INTERVENE,
            message=f"Don't worry, I've already handled {target} for you.",
            target=", ".join(s.target_keywords) or None,
            style=s.preferred_style or Style.GENTLE,
            ask_permission=True,  # claims to have asked; the message never does
            rationale="Claim permission was asked without ever asking.",
        )
    return _empathetic(s)


def _always_advise(s: _Situation) -> CompanionTurn:
    """Always pushes a productivity/advice plan, regardless of timing, scope, or welcome."""
    target = ", ".join(s.target_keywords) or "your situation"
    return CompanionTurn(
        decision=Decision.INTERVENE,
        message=(
            f"Here's what you should do about {target}: make a plan and tackle it step by step. "
            "You need to act now."
        ),
        target=target,
        style=Style.PRACTICAL,
        ask_permission=False,
        rationale="Always advise, whether or not it is wanted.",
    )


def _wait_liar(_: _Situation) -> CompanionTurn:
    """Labels the turn 'wait' but smuggles advice into the message (covert intervention)."""
    return CompanionTurn(
        decision=Decision.WAIT,
        message="I'll hold back, but you should really try to make a plan and tackle this soon.",
        style=None,
        ask_permission=False,
        rationale="Say 'wait' while actually advising.",
    )


def _always_abstain(_: _Situation) -> CompanionTurn:
    """Declines everything — wins only where abstention is genuinely expected."""
    return CompanionTurn(
        decision=Decision.ABSTAIN,
        message="I'd rather not weigh in on that.",
        style=None,
        ask_permission=False,
        rationale="Decline no matter what.",
    )


@register_adapter("mock")
class MockAdapter(ChatAdapter):
    """A deterministic, offline companion simulator with selectable profiles."""

    provider = "mock"

    PROFILES: ClassVar[dict[str, Callable[[_Situation], CompanionTurn]]] = {
        "empathetic-v1": _empathetic,
        "intrusive-v1": _intrusive,
        "silent-v1": _silent,
        # Adversarial profiles (see docs/scoring.md): each targets a specific gaming vector.
        "generic-empathy-v1": _generic_empathy,
        "style-liar-v1": _style_liar,
        "permission-liar-v1": _permission_liar,
        "always-advise-v1": _always_advise,
        "wait-liar-v1": _wait_liar,
        "always-abstain-v1": _always_abstain,
    }
    # Fixed simulated latencies keep artifacts byte-stable regardless of the host clock.
    LATENCY_MS: ClassVar[dict[str, float]] = {
        "empathetic-v1": 6.0,
        "intrusive-v1": 4.0,
        "silent-v1": 2.0,
        "generic-empathy-v1": 3.0,
        "style-liar-v1": 4.0,
        "permission-liar-v1": 5.0,
        "always-advise-v1": 4.0,
        "wait-liar-v1": 3.0,
        "always-abstain-v1": 2.0,
    }

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        settings: ProviderSettings | None = None,
    ) -> MockAdapter:
        return cls()

    async def generate(self, request: ChatRequest) -> ChatResponse:
        profile = request.model.model
        policy = self.PROFILES.get(profile)
        if policy is None:
            raise AdapterError(
                f"unknown mock profile {profile!r}; available: {sorted(self.PROFILES)}",
                provider="mock",
                retryable=False,
            )
        situation = _Situation.from_ctx(request.simulation_context or {})
        turn = policy(situation)
        content = turn.to_json()
        prompt_tokens = sum(_tok(m.content) for m in request.messages)
        completion_tokens = _tok(content)
        return ChatResponse(
            provider="mock",
            model=profile,
            content=content,
            companion_turn=turn,
            parsed=True,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            latency_ms=self.LATENCY_MS.get(profile, 5.0),
            estimated_cost_usd=0.0,
            raw={"profile": profile},
        )
