"""Versioned pricing table: (provider, model) -> USD per 1M input/output tokens.

Prices change and vary by provider, so every entry carries a ``source`` and an ``as_of``
date and the table is versioned. When a model has no entry, cost is recorded as ``null``
(never invented) and the budget guard treats it as unknown.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from companion_bench.schemas.model import TokenUsage
from companion_bench.utils.errors import ConfigError

__all__ = ["PriceEntry", "PricingTable", "default_pricing", "load_pricing"]


class PriceEntry(BaseModel):
    """Price for one provider/model, with provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    model: str
    input_usd_per_1m: float = Field(ge=0.0)
    output_usd_per_1m: float = Field(ge=0.0)
    source: str
    as_of: str  # ISO date, e.g. 2026-01-15
    # Optional provenance / raw source fields (populated by `pricing sync-openrouter`).
    currency: str = "USD"
    units: str = "per_1m_tokens"
    context_length: int | None = None
    prompt_price_per_token: float | None = None
    completion_price_per_token: float | None = None


class PricingTable(BaseModel):
    """A versioned set of price entries with cost lookup."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    entries: tuple[PriceEntry, ...] = ()

    def lookup(self, provider: str, model: str) -> PriceEntry | None:
        for entry in self.entries:
            if entry.provider == provider and entry.model == model:
                return entry
        return None

    def rate(self, provider: str, model: str) -> tuple[float, float] | None:
        """``(input_per_1m, output_per_1m)`` for a model, or ``None`` if unknown."""
        entry = self.lookup(provider, model)
        return (entry.input_usd_per_1m, entry.output_usd_per_1m) if entry else None

    def cost(self, provider: str, model: str, usage: TokenUsage | None) -> float | None:
        """Estimated USD cost for a call, or ``None`` if price or usage is unknown."""
        rate = self.rate(provider, model)
        if rate is None or usage is None:
            return None
        price_in, price_out = rate
        prompt = usage.prompt_tokens or 0
        completion = usage.completion_tokens or 0
        return round(prompt / 1e6 * price_in + completion / 1e6 * price_out, 8)


def _bundled_text(name: str) -> str:
    return (files("companion_bench.config") / "data" / name).read_text(encoding="utf-8")


def load_pricing(path: str | Path | None = None) -> PricingTable:
    """Load a pricing table from YAML (bundled default when ``path`` is None)."""
    text = _bundled_text("pricing.yaml") if path is None else Path(path).read_text(encoding="utf-8")
    try:
        return PricingTable.model_validate(yaml.safe_load(text))
    except Exception as exc:  # pydantic ValidationError or YAML error
        where = "bundled pricing.yaml" if path is None else str(path)
        raise ConfigError(f"invalid pricing config ({where}): {exc}") from exc


def default_pricing() -> PricingTable:
    """The bundled default pricing table."""
    return load_pricing(None)
