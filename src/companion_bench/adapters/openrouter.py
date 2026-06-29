"""OpenRouter adapter — OpenAI-compatible with OpenRouter defaults + attribution headers.

Reads ``OPENROUTER_API_KEY`` (required) and optional ``OPENROUTER_BASE_URL``. OpenRouter
recommends sending ``HTTP-Referer`` and ``X-Title`` for attribution; these are populated
from ``OPENROUTER_REFERER`` / ``OPENROUTER_TITLE`` if set. Models are referenced as
``openrouter/<vendor>/<model>`` (the vendor/model part may contain slashes).
"""

from __future__ import annotations

from collections.abc import Mapping

from companion_bench.adapters.base import register_adapter
from companion_bench.adapters.openai_compatible import OpenAICompatibleAdapter

__all__ = ["OpenRouterAdapter"]


@register_adapter("openrouter")
class OpenRouterAdapter(OpenAICompatibleAdapter):
    """Adapter for the OpenRouter aggregator API."""

    provider = "openrouter"
    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    BASE_URL_ENV = "OPENROUTER_BASE_URL"
    API_KEY_ENV = "OPENROUTER_API_KEY"
    REQUIRES_KEY = True
    SUPPORTS_JSON_MODE = True

    @classmethod
    def _env_headers(cls, env: Mapping[str, str]) -> dict[str, str]:
        headers: dict[str, str] = {}
        referer = env.get("OPENROUTER_REFERER")
        title = env.get("OPENROUTER_TITLE", "CompanionBench")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        return headers
