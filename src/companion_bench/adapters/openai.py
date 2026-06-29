"""OpenAI adapter — the OpenAI-compatible adapter with OpenAI defaults.

Reads ``OPENAI_API_KEY`` (required) and optional ``OPENAI_BASE_URL`` (defaults to the
public API). Inherits the full request/response handling from
:class:`OpenAICompatibleAdapter`; this file exists to pin the config pattern, not to add
logic. Set ``params`` on the model spec to pass through extra OpenAI options.
"""

from __future__ import annotations

from companion_bench.adapters.base import register_adapter
from companion_bench.adapters.openai_compatible import OpenAICompatibleAdapter

__all__ = ["OpenAIAdapter"]


@register_adapter("openai")
class OpenAIAdapter(OpenAICompatibleAdapter):
    """Adapter for the OpenAI Chat Completions API."""

    provider = "openai"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    BASE_URL_ENV = "OPENAI_BASE_URL"
    API_KEY_ENV = "OPENAI_API_KEY"
    REQUIRES_KEY = True
    SUPPORTS_JSON_MODE = True
