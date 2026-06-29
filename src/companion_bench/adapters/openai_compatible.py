"""Generic OpenAI-compatible chat-completions adapter (async HTTPX).

Targets any server speaking the OpenAI ``/chat/completions`` shape — OpenAI itself,
OpenRouter, Hugging Face Inference Providers' router, vLLM, Ollama, LM Studio, ... Point
``OPENAI_COMPATIBLE_BASE_URL`` at the server; an API key is optional (local servers often
need none). The OpenAI/OpenRouter subclasses just override the defaults.

Tests inject an ``httpx.AsyncClient`` backed by ``httpx.MockTransport`` — there is no real
network access anywhere in the test suite.
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
    TokenUsage,
)
from companion_bench.utils.errors import (
    ConfigError,
    ProviderAuthError,
    ProviderResponseError,
    ProviderTimeoutError,
)

__all__ = ["OpenAICompatibleAdapter"]


@register_adapter("openai_compatible")
class OpenAICompatibleAdapter(ChatAdapter):
    """Adapter for OpenAI-compatible ``/chat/completions`` endpoints."""

    provider = "openai_compatible"

    # Subclasses customize these to describe a specific provider.
    DEFAULT_BASE_URL: str | None = None
    BASE_URL_ENV: str = "OPENAI_COMPATIBLE_BASE_URL"
    API_KEY_ENV: str = "OPENAI_COMPATIBLE_API_KEY"
    REQUIRES_KEY: bool = False
    SUPPORTS_JSON_MODE: bool = True

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str = "",
        client: httpx.AsyncClient | None = None,
        default_headers: Mapping[str, str] | None = None,
        default_params: Mapping[str, object] | None = None,
        pricing: tuple[float, float] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient()
        self._default_headers = dict(default_headers or {})
        self._default_params = dict(default_params or {})
        # (input, output) USD per 1M tokens; None => cost recorded as null.
        self._pricing = pricing

    # -- construction -------------------------------------------------------
    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        settings: ProviderSettings | None = None,
    ) -> OpenAICompatibleAdapter:
        env = env if env is not None else os.environ
        settings = settings or ProviderSettings()
        # Precedence: env > providers.yaml (settings) > built-in default.
        base_url = env.get(cls.BASE_URL_ENV) or settings.base_url or cls.DEFAULT_BASE_URL
        if not base_url:
            raise ConfigError(
                f"{cls.__name__}: no base URL; set {cls.BASE_URL_ENV} or pass base_url."
            )
        api_key = env.get(cls.API_KEY_ENV, "")
        if cls.REQUIRES_KEY and not api_key:
            raise ProviderAuthError(
                f"{cls.__name__}: missing API key; set {cls.API_KEY_ENV}.",
                provider=cls.provider,
            )
        return cls(
            base_url=base_url,
            api_key=api_key,
            default_headers={**settings.default_headers, **cls._env_headers(env)},
            default_params=settings.default_params,
        )

    @classmethod
    def _env_headers(cls, env: Mapping[str, str]) -> dict[str, str]:
        """Provider-specific extra headers (overridden by e.g. OpenRouter)."""
        return {}

    # -- request ------------------------------------------------------------
    def _build_payload(self, request: ChatRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model.model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format == "json_object" and self.SUPPORTS_JSON_MODE:
            payload["response_format"] = {"type": "json_object"}
        payload.update(self._default_params)  # providers.yaml defaults
        payload.update(request.model.params)  # per-model params win
        return payload

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **self._default_headers}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def generate(self, request: ChatRequest) -> ChatResponse:
        url = f"{self._base_url}/chat/completions"
        try:
            response = await self._client.post(
                url,
                json=self._build_payload(request),
                headers=self._headers(),
                timeout=request.timeout_s,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"{self.provider} request timed out after {request.timeout_s}s",
                provider=self.provider,
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError(
                f"{self.provider} transport error: {exc}", provider=self.provider
            ) from exc

        if response.status_code in (401, 403):
            raise ProviderAuthError(
                f"{self.provider} authentication failed (HTTP {response.status_code}); "
                f"check {self.API_KEY_ENV}.",
                provider=self.provider,
            )
        if response.status_code >= 400:
            retryable = response.status_code == 429 or response.status_code >= 500
            raise ProviderResponseError(
                f"{self.provider} returned HTTP {response.status_code}: {response.text[:300]}",
                provider=self.provider,
                retryable=retryable,
            )
        return self._build_response(request, response)

    # -- response parsing (overridable) ------------------------------------
    def _build_response(self, request: ChatRequest, response: httpx.Response) -> ChatResponse:
        data = self._parse_json_object(response)
        content = self._extract_content(data)
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
                f"{self.provider}: response body was not valid JSON: {response.text[:300]}",
                provider=self.provider,
                retryable=False,
            ) from exc
        if not isinstance(data, dict):
            raise ProviderResponseError(
                f"{self.provider}: response JSON was not an object (got {type(data).__name__}).",
                provider=self.provider,
                retryable=False,
            )
        return data

    def _extract_content(self, data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                f"{self.provider}: unexpected response shape (no choices[0].message.content)",
                provider=self.provider,
                retryable=False,
            ) from exc
        if content is None:
            return ""
        if isinstance(content, list):
            # Some servers return content as a list of typed parts; join only the text
            # parts (skip parts explicitly typed non-text that carry a stray text field).
            return "".join(
                p["text"]
                for p in content
                if isinstance(p, dict)
                and p.get("type") in (None, "text")
                and isinstance(p.get("text"), str)
            )
        if not isinstance(content, str):
            raise ProviderResponseError(
                f"{self.provider}: message content was not text (got {type(content).__name__}).",
                provider=self.provider,
                retryable=False,
            )
        return content

    def _extract_usage(self, data: dict[str, Any]) -> TokenUsage | None:
        usage = data.get("usage")
        if not isinstance(usage, dict):
            return None
        try:
            return TokenUsage(
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            )
        except ValidationError:
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
    except RuntimeError:  # pragma: no cover - elapsed not yet available
        return None
