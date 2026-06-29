"""Typed exception hierarchy for CompanionBench.

All library errors derive from :class:`CompanionBenchError`. Adapter errors carry a
``retryable`` flag so the run engine can decide whether to retry without inspecting
provider-specific details.
"""

from __future__ import annotations

__all__ = [
    "AdapterError",
    "CompanionBenchError",
    "ConfigError",
    "ExportError",
    "ManifestError",
    "ProviderAuthError",
    "ProviderResponseError",
    "ProviderTimeoutError",
    "ResponseParseError",
    "TaskLoadError",
]


class CompanionBenchError(Exception):
    """Base class for all CompanionBench errors."""


class ConfigError(CompanionBenchError):
    """Invalid configuration, CLI arguments, or environment."""


class ManifestError(ConfigError):
    """A manifest file is missing, malformed, or references missing tasks."""


class TaskLoadError(ConfigError):
    """A task file failed to load or validate."""


class ExportError(CompanionBenchError):
    """An export target could not be produced (e.g. optional dependency missing)."""


class AdapterError(CompanionBenchError):
    """Base class for provider/adapter failures.

    ``retryable`` tells the engine whether retrying the same request might succeed.
    """

    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retryable: bool | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        # Server-suggested minimum wait before retrying (e.g. from a Retry-After header).
        self.retry_after = retry_after
        if retryable is not None:
            self.retryable = retryable


class ProviderAuthError(AdapterError):
    """Missing or invalid API credentials. Not retryable."""

    retryable = False


class ProviderTimeoutError(AdapterError):
    """The provider did not respond within the timeout. Retryable."""

    retryable = True


class ProviderResponseError(AdapterError):
    """The provider returned an error status or an unusable payload.

    Defaults to retryable (covers transient 5xx / rate-limit responses); callers should
    set ``retryable=False`` for definitive client errors (e.g. 400/404).
    """

    retryable = True


class ResponseParseError(AdapterError):
    """A response was received but no valid CompanionTurn envelope could be parsed.

    Not retryable by default — re-sending the identical request is unlikely to help.
    """

    retryable = False
