"""Provider adapters implementing the ``ChatAdapter`` contract.

Importing this package registers every built-in provider (``mock``,
``openai_compatible``, ``openai``, ``anthropic``, ``openrouter``) so that
:func:`create_adapter` can resolve them by name.
"""

from __future__ import annotations

from companion_bench.adapters.anthropic import AnthropicAdapter
from companion_bench.adapters.base import (
    ChatAdapter,
    ProviderInfo,
    available_providers,
    create_adapter,
    describe_providers,
    get_adapter_class,
    register_adapter,
)
from companion_bench.adapters.mock import MockAdapter
from companion_bench.adapters.openai import OpenAIAdapter
from companion_bench.adapters.openai_compatible import OpenAICompatibleAdapter
from companion_bench.adapters.openrouter import OpenRouterAdapter
from companion_bench.adapters.probe import ProbeResult, probe_model, probe_models

__all__ = [
    "AnthropicAdapter",
    "ChatAdapter",
    "MockAdapter",
    "OpenAIAdapter",
    "OpenAICompatibleAdapter",
    "OpenRouterAdapter",
    "ProbeResult",
    "ProviderInfo",
    "available_providers",
    "create_adapter",
    "describe_providers",
    "get_adapter_class",
    "probe_model",
    "probe_models",
    "register_adapter",
]
