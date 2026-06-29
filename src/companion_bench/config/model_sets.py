"""Model sets: a named, versioned list of models to benchmark together.

A model set decouples *which models to run* from the manifest (*which tasks*). Each entry
records its provenance (``source``) and whether it still ``needs_mapping`` (i.e. the model
slug has not been verified against the provider). ``models validate`` checks the schema, that
each provider is registered, and flags unverified slugs and unknown prices.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from companion_bench.config.pricing import PricingTable
from companion_bench.schemas.model import ModelSpec
from companion_bench.utils.errors import ConfigError

__all__ = [
    "ModelEntry",
    "ModelSet",
    "ModelSetIssue",
    "ModelSetReport",
    "load_model_set",
    "validate_model_set",
]


class ModelEntry(BaseModel):
    """One model in a set."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    provider: str
    model: str
    enabled: bool = True
    temperature: float | None = None
    max_completion_tokens: int | None = Field(default=None, ge=1)
    source: str | None = None
    notes: str | None = None
    # True when the slug has not been verified against the provider (run --live to confirm).
    needs_mapping: bool = False

    @property
    def ref(self) -> str:
        return f"{self.provider}/{self.model}"

    def spec(self) -> ModelSpec:
        return ModelSpec(provider=self.provider, model=self.model)

    def config_overrides(self) -> dict[str, Any]:
        """Per-model RunConfig overrides (temperature / max_tokens) to merge at run time."""
        overrides: dict[str, Any] = {}
        if self.temperature is not None:
            overrides["temperature"] = self.temperature
        if self.max_completion_tokens is not None:
            overrides["max_tokens"] = self.max_completion_tokens
        return overrides


class ModelSet(BaseModel):
    """A named collection of models with provenance metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    set_id: str
    description: str = ""
    source_repo_path: str | None = None
    extracted_at: str | None = None
    models: tuple[ModelEntry, ...] = Field(min_length=1)

    def enabled_models(self) -> list[ModelEntry]:
        return [m for m in self.models if m.enabled]


class ModelSetIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["error", "warning"]
    model_id: str | None
    message: str


class ModelSetReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    set_id: str | None
    ok: bool
    n_models: int
    n_enabled: int
    issues: tuple[ModelSetIssue, ...]


def load_model_set(path: str | Path) -> ModelSet:
    """Load and validate a model-set YAML file."""
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"model set not found: {p}")
    try:
        return ModelSet.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
    except Exception as exc:
        raise ConfigError(f"invalid model set ({p}): {exc}") from exc


def validate_model_set(
    model_set: ModelSet, *, pricing: PricingTable | None = None
) -> ModelSetReport:
    """Validate providers, flag unverified slugs and unknown prices (collects all issues)."""
    # Lazy import keeps config import-time free of the adapters package.
    from companion_bench.adapters import available_providers

    providers = set(available_providers())
    issues: list[ModelSetIssue] = []
    seen_ids: set[str] = set()

    for entry in model_set.models:
        if entry.id in seen_ids:
            issues.append(
                ModelSetIssue(level="error", model_id=entry.id, message="duplicate model id")
            )
        seen_ids.add(entry.id)
        if entry.provider not in providers:
            issues.append(
                ModelSetIssue(
                    level="error",
                    model_id=entry.id,
                    message=f"unknown provider {entry.provider!r}; registered: {sorted(providers)}",
                )
            )
        if entry.needs_mapping:
            issues.append(
                ModelSetIssue(
                    level="warning",
                    model_id=entry.id,
                    message="needs_mapping: slug unverified — confirm with a live probe before trusting results",
                )
            )
        if pricing is not None and pricing.rate(entry.provider, entry.model) is None:
            issues.append(
                ModelSetIssue(
                    level="warning",
                    model_id=entry.id,
                    message="no price entry — cost will be null and the budget guard cannot price this model",
                )
            )

    ok = not any(i.level == "error" for i in issues)
    return ModelSetReport(
        set_id=model_set.set_id,
        ok=ok,
        n_models=len(model_set.models),
        n_enabled=len(model_set.enabled_models()),
        issues=tuple(issues),
    )
