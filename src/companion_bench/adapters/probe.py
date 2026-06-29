"""One-shot live probes: send a tiny request to a provider/model to confirm it works.

Used by ``companion-bench providers --probe`` (guarded by ``COMPANIONBENCH_LIVE=1``) and as a
quick way to verify a model slug before a real run. Probes run sequentially to be gentle on
providers, and any error is captured (never raised) so one bad target doesn't abort the rest.
Error strings come from typed adapter errors and never contain the API key.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from companion_bench.adapters.base import create_adapter
from companion_bench.schemas.model import ChatMessage, ChatRequest, ModelSpec, Role
from companion_bench.utils.secrets import collect_secret_values, redact

__all__ = ["ProbeResult", "probe_model", "probe_models"]


def _err(exc: Exception) -> str:
    # Redact any env secret that might appear in a provider's error body.
    return redact(f"{type(exc).__name__}: {exc}", collect_secret_values())


@dataclass(frozen=True)
class ProbeResult:
    ref: str
    ok: bool
    latency_ms: float | None = None
    total_tokens: int | None = None
    parsed: bool | None = None
    error: str | None = None


async def probe_model(
    ref: str, env: Mapping[str, str] | None = None, *, timeout_s: float = 20.0
) -> ProbeResult:
    """Send one tiny request to ``provider/model`` and report the outcome."""
    try:
        spec = ModelSpec.parse(ref)
        adapter = create_adapter(spec.provider, env)
    except Exception as exc:
        return ProbeResult(ref=ref, ok=False, error=_err(exc))

    request = ChatRequest(
        model=spec,
        messages=(
            ChatMessage(role=Role.USER, content="Reply with the JSON envelope: a brief hello."),
        ),
        max_tokens=64,
        timeout_s=timeout_s,
    )
    try:
        response = await adapter.generate(request)
        tokens = response.token_usage.total_tokens if response.token_usage else None
        return ProbeResult(
            ref=ref,
            ok=True,
            latency_ms=response.latency_ms,
            total_tokens=tokens,
            parsed=response.parsed,
        )
    except Exception as exc:
        return ProbeResult(ref=ref, ok=False, error=_err(exc))
    finally:
        await adapter.aclose()


async def probe_models(
    refs: Sequence[str], env: Mapping[str, str] | None = None, *, timeout_s: float = 20.0
) -> list[ProbeResult]:
    """Probe several provider/model refs sequentially."""
    return [await probe_model(ref, env, timeout_s=timeout_s) for ref in refs]
