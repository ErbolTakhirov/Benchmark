"""The ``ChatAdapter`` contract and a small provider registry.

Every provider — mock or real — implements one async method::

    async def generate(self, request: ChatRequest) -> ChatResponse

Adapters are registered by provider name with :func:`register_adapter` and constructed
from the environment via :func:`create_adapter`, so the runner never imports a concrete
provider directly. This is the single seam new providers plug into.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import ClassVar

from companion_bench.config.providers import ProviderSettings
from companion_bench.schemas.model import ChatRequest, ChatResponse
from companion_bench.utils.errors import ConfigError

__all__ = [
    "ChatAdapter",
    "ProviderInfo",
    "available_providers",
    "create_adapter",
    "describe_providers",
    "get_adapter_class",
    "register_adapter",
]


class ChatAdapter(ABC):
    """Abstract base for all chat adapters.

    Concrete adapters set :attr:`provider` (done automatically by
    :func:`register_adapter`) and implement :meth:`generate` and :meth:`from_env`.
    """

    provider: ClassVar[str] = ""

    @abstractmethod
    async def generate(self, request: ChatRequest) -> ChatResponse:
        """Produce a single :class:`ChatResponse` for ``request``.

        Transport-level failures must raise an
        :class:`~companion_bench.utils.errors.AdapterError` subclass so the engine can
        record a failure event and decide whether to retry.
        """
        raise NotImplementedError

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        settings: ProviderSettings | None = None,
    ) -> ChatAdapter:
        """Construct an adapter from environment variables and optional provider settings.

        Resolution precedence for base URL etc. is env > ``settings`` (providers.yaml) >
        built-in defaults.
        """
        raise NotImplementedError(f"{cls.__name__} does not implement from_env()")

    async def aclose(self) -> None:
        """Release any resources (e.g. HTTP clients). Default: no-op."""
        return None


_REGISTRY: dict[str, type[ChatAdapter]] = {}


def register_adapter[A: type[ChatAdapter]](provider: str) -> Callable[[A], A]:
    """Class decorator registering an adapter under ``provider``."""

    def decorate(cls: A) -> A:
        cls.provider = provider
        _REGISTRY[provider] = cls
        return cls

    return decorate


def available_providers() -> list[str]:
    """Sorted list of registered provider names."""
    return sorted(_REGISTRY)


def get_adapter_class(provider: str) -> type[ChatAdapter]:
    """Look up a registered adapter class, or raise :class:`ConfigError`."""
    try:
        return _REGISTRY[provider]
    except KeyError as exc:
        raise ConfigError(
            f"unknown provider {provider!r}; available providers: {available_providers()}"
        ) from exc


def create_adapter(
    provider: str,
    env: Mapping[str, str] | None = None,
    *,
    settings: ProviderSettings | None = None,
) -> ChatAdapter:
    """Instantiate the adapter for ``provider`` from the environment + provider settings."""
    return get_adapter_class(provider).from_env(env, settings=settings)


@dataclass(frozen=True)
class ProviderInfo:
    """Non-secret configuration status for a registered provider."""

    provider: str
    requires_key: bool
    key_env_var: str | None
    base_url: str | None
    key_present: bool


def describe_providers(env: Mapping[str, str] | None = None) -> list[ProviderInfo]:
    """Report each registered provider's config status — **never the key value itself**."""
    source = env if env is not None else os.environ
    infos: list[ProviderInfo] = []
    for name, cls in sorted(_REGISTRY.items()):
        key_env = getattr(cls, "API_KEY_ENV", None)
        base_env = getattr(cls, "BASE_URL_ENV", None)
        base_url = getattr(cls, "DEFAULT_BASE_URL", None)
        if base_env and source.get(base_env):
            base_url = source[base_env]
        infos.append(
            ProviderInfo(
                provider=name,
                requires_key=bool(getattr(cls, "REQUIRES_KEY", False)),
                key_env_var=key_env,
                base_url=base_url,
                key_present=bool(key_env and source.get(key_env)),
            )
        )
    return infos
