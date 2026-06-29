"""Anthropic adapter (Messages API).

Anthropic's API differs from the OpenAI shape — a dedicated ``/v1/messages`` endpoint, a
separate top-level ``system`` field, ``x-api-key`` auth, a required ``max_tokens``, and a
content-block response — so this adapter implements ``generate`` directly rather than
subclassing the OpenAI-compatible one. The structured CompanionTurn envelope is requested
via the system instruction the conversation builder injects (Anthropic has no
``response_format=json_object`` flag), then parsed tolerantly.

Reads ``ANTHROPIC_API_KEY`` (required) and optional ``ANTHROPIC_BASE_URL``.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import ValidationError

from companion_bench.adapters.base import ChatAdapter, register_adapter
from companion_bench.config.providers import ProviderSettings
from companion_bench.schemas.model import (
    ChatRequest,
    ChatResponse,
    CompanionTurn,
    Role,
    TokenUsage,
)
from companion_bench.utils.errors import (
    ConfigError,
    ProviderAuthError,
    ProviderResponseError,
    ProviderTimeoutError,
)

__all__ = ["AnthropicAdapter"]


@register_adapter("anthropic")
class AnthropicAdapter(ChatAdapter):
    """Adapter for the Anthropic Messages API."""

    provider = "anthropic"
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    BASE_URL_ENV = "ANTHROPIC_BASE_URL"
    API_KEY_ENV = "ANTHROPIC_API_KEY"
    REQUIRES_KEY = True
    ANTHROPIC_VERSION = "2023-06-01"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.AsyncClient | None = None,
        default_params: Mapping[str, object] | None = None,
        pricing: tuple[float, float] | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient()
        self._default_params = dict(default_params or {})
        self._pricing = pricing

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        settings: ProviderSettings | None = None,
    ) -> AnthropicAdapter:
        env = env if env is not None else os.environ
        settings = settings or ProviderSettings()
        api_key = env.get(cls.API_KEY_ENV, "")
        if not api_key:
            raise ProviderAuthError(
                f"AnthropicAdapter: missing API key; set {cls.API_KEY_ENV}.",
                provider=cls.provider,
            )
        base_url = env.get(cls.BASE_URL_ENV) or settings.base_url or cls.DEFAULT_BASE_URL
        if not base_url:  # pragma: no cover - defensive
            raise ConfigError("AnthropicAdapter: empty ANTHROPIC_BASE_URL.")
        return cls(api_key=api_key, base_url=base_url, default_params=settings.default_params)

    def _build_payload(self, request: ChatRequest) -> dict[str, Any]:
        system_parts = [m.content for m in request.messages if m.role is Role.SYSTEM]
        turns = [
            {"role": m.role.value, "content": m.content}
            for m in request.messages
            if m.role is not Role.SYSTEM
        ]
        payload: dict[str, Any] = {
            "model": request.model.model,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
            "messages": turns,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        payload.update(self._default_params)  # providers.yaml defaults
        payload.update(request.model.params)  # per-model params win
        return payload

    async def generate(self, request: ChatRequest) -> ChatResponse:
        url = f"{self._base_url}/v1/messages"
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self.ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
        try:
            response = await self._client.post(
                url, json=self._build_payload(request), headers=headers, timeout=request.timeout_s
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"anthropic request timed out after {request.timeout_s}s", provider=self.provider
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError(
                f"anthropic transport error: {exc}", provider=self.provider
            ) from exc

        if response.status_code in (401, 403):
            raise ProviderAuthError(
                f"anthropic authentication failed (HTTP {response.status_code}); "
                "check ANTHROPIC_API_KEY.",
                provider=self.provider,
            )
        if response.status_code >= 400:
            retryable = response.status_code == 429 or response.status_code >= 500
            retry_after = (
                _parse_retry_after(response.headers.get("retry-after"))
                if response.status_code == 429
                else None
            )
            raise ProviderResponseError(
                f"anthropic returned HTTP {response.status_code}: {response.text[:300]}",
                provider=self.provider,
                retryable=retryable,
                retry_after=retry_after,
            )

        data = self._parse_json_object(response)
        content = self._extract_text(data)
        turn = CompanionTurn.from_text(content)
        usage = self._extract_usage(data)
        return ChatResponse(
            provider=self.provider,
            model=request.model.model,
            content=content,
            companion_turn=turn,
            parsed=turn is not None,
            token_usage=usage,
            latency_ms=_elapsed_ms(response),
            estimated_cost_usd=self._estimate_cost(usage),
            raw=data,
        )

    def _parse_json_object(self, response: httpx.Response) -> dict[str, Any]:
        """Decode a JSON object body, mapping malformed bodies to a typed error."""
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise ProviderResponseError(
                f"anthropic: response body was not valid JSON: {response.text[:300]}",
                provider=self.provider,
                retryable=False,
            ) from exc
        if not isinstance(data, dict):
            raise ProviderResponseError(
                f"anthropic: response JSON was not an object (got {type(data).__name__}).",
                provider=self.provider,
                retryable=False,
            )
        return data

    def _extract_text(self, data: dict[str, Any]) -> str:
        blocks = data.get("content")
        if not isinstance(blocks, list):
            raise ProviderResponseError(
                "anthropic: unexpected response shape (no content blocks)",
                provider=self.provider,
                retryable=False,
            )
        texts = [
            b.get("text") or "" for b in blocks if isinstance(b, dict) and b.get("type") == "text"
        ]
        return "".join(texts)

    def _extract_usage(self, data: dict[str, Any]) -> TokenUsage | None:
        usage = data.get("usage")
        if not isinstance(usage, dict):
            return None
        prompt = usage.get("input_tokens")
        completion = usage.get("output_tokens")
        try:
            # `prompt + completion` must stay inside the guard: a non-conforming provider
            # could send non-addable token types, which would otherwise escape untyped.
            total = None if prompt is None or completion is None else prompt + completion
            return TokenUsage(
                prompt_tokens=prompt, completion_tokens=completion, total_tokens=total
            )
        except (ValidationError, TypeError):
            return None

    def _estimate_cost(self, usage: TokenUsage | None) -> float | None:
        if self._pricing is None or usage is None:
            return None
        price_in, price_out = self._pricing
        prompt = usage.prompt_tokens or 0
        completion = usage.completion_tokens or 0
        return round(prompt / 1e6 * price_in + completion / 1e6 * price_out, 6)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def __repr__(self) -> str:
        # Never include the API key in a repr / log line.
        return f"{type(self).__name__}(provider={self.provider!r}, base_url={self._base_url!r})"


def _elapsed_ms(response: httpx.Response) -> float | None:
    try:
        return response.elapsed.total_seconds() * 1000.0
    except RuntimeError:  # pragma: no cover
        return None


def _parse_retry_after(value: str | None) -> float | None:
    """Parse a numeric Retry-After (seconds). HTTP-date form is unsupported (returns None)."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None
