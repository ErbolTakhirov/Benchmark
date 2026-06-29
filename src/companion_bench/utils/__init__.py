"""Small shared utilities: ids, timing/clock, and the error hierarchy."""

from __future__ import annotations

from companion_bench.utils.errors import (
    AdapterError,
    CompanionBenchError,
    ConfigError,
    ExportError,
    ManifestError,
    ProviderAuthError,
    ProviderResponseError,
    ProviderTimeoutError,
    ResponseParseError,
    TaskLoadError,
)
from companion_bench.utils.ids import IdFactory, make_run_id, short_hash, slugify
from companion_bench.utils.timing import Clock, FrozenClock, RealClock, Stopwatch, iso

__all__ = [
    "AdapterError",
    "Clock",
    "CompanionBenchError",
    "ConfigError",
    "ExportError",
    "FrozenClock",
    "IdFactory",
    "ManifestError",
    "ProviderAuthError",
    "ProviderResponseError",
    "ProviderTimeoutError",
    "RealClock",
    "ResponseParseError",
    "Stopwatch",
    "TaskLoadError",
    "iso",
    "make_run_id",
    "short_hash",
    "slugify",
]
