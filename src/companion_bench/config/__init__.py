"""Versioned, schema-validated configuration: pricing, provider settings, model sets.

These are deliberately separate from ``schemas`` (which models run artifacts). Config is
loaded from YAML (bundled defaults live in ``config/data/``; users override with their own
files) and validated with Pydantic, so a malformed config fails loudly rather than silently
mis-pricing or mis-routing a run.
"""

from __future__ import annotations

from companion_bench.config.pricing import (
    PriceEntry,
    PricingTable,
    default_pricing,
    load_pricing,
)
from companion_bench.config.providers import (
    ProvidersConfig,
    ProviderSettings,
    default_providers_config,
    load_providers_config,
)

__all__ = [
    "PriceEntry",
    "PricingTable",
    "ProviderSettings",
    "ProvidersConfig",
    "default_pricing",
    "default_providers_config",
    "load_pricing",
    "load_providers_config",
]
