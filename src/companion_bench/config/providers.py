"""Provider settings overrides (base URL, timeout, headers, params, rate limit).

Resolution precedence is **CLI > env > providers.yaml > built-in adapter defaults**. This
layer supplies the ``providers.yaml`` tier; the env and built-in tiers live in each adapter's
``from_env``. The default config is empty — built-in defaults already cover every provider.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from companion_bench.utils.errors import ConfigError

__all__ = [
    "ProviderSettings",
    "ProvidersConfig",
    "default_providers_config",
    "load_providers_config",
]


class ProviderSettings(BaseModel):
    """Optional overrides for a single provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str | None = None
    requests_per_second: float | None = Field(default=None, gt=0.0)
    default_headers: dict[str, str] = Field(default_factory=dict)
    default_params: dict[str, Any] = Field(default_factory=dict)


class ProvidersConfig(BaseModel):
    """Versioned provider-settings overrides, keyed by provider name."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = "0"
    providers: dict[str, ProviderSettings] = Field(default_factory=dict)

    def for_provider(self, name: str) -> ProviderSettings:
        return self.providers.get(name, ProviderSettings())


def load_providers_config(path: str | Path | None = None) -> ProvidersConfig:
    """Load provider settings from YAML; an empty config when ``path`` is None."""
    if path is None:
        return ProvidersConfig()
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if data is None:  # empty file == no overrides
            return ProvidersConfig()
        return ProvidersConfig.model_validate(data)
    except Exception as exc:
        raise ConfigError(f"invalid providers config ({path}): {exc}") from exc


def default_providers_config() -> ProvidersConfig:
    """The default (empty) provider-settings config."""
    return ProvidersConfig()
