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
    TaskLoadError,
)
from companion_bench.utils.ids import IdFactory, make_run_id, short_hash, slugify
from companion_bench.utils.secrets import (
    SECRET_ENV_VARS,
    collect_secret_values,
    redact,
    scan_run_dir,
    scan_text_for_secrets,
)
from companion_bench.utils.timing import Clock, FrozenClock, RealClock, Stopwatch, iso

__all__ = [
    "SECRET_ENV_VARS",
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
    "Stopwatch",
    "TaskLoadError",
    "collect_secret_values",
    "iso",
    "make_run_id",
    "redact",
    "scan_run_dir",
    "scan_text_for_secrets",
    "short_hash",
    "slugify",
]
