"""Sync a pricing table from the OpenRouter ``GET /api/v1/models`` endpoint.

The models endpoint is public (no key needed; a key is used only if present, env-only). Each
model reports ``pricing.prompt`` / ``pricing.completion`` as **USD per token** strings; we
convert to USD per 1M tokens and keep the raw per-token values + context length for
reproducibility. Models with missing/non-numeric pricing are skipped (their cost stays null).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import httpx

from companion_bench.config.pricing import PriceEntry, PricingTable
from companion_bench.utils.errors import ProviderResponseError, ProviderTimeoutError

__all__ = ["build_openrouter_pricing", "fetch_openrouter_models"]

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


async def fetch_openrouter_models(
    env: Mapping[str, str] | None = None,
    *,
    base_url: str | None = None,
    client: httpx.AsyncClient | None = None,
    timeout_s: float = 30.0,
) -> list[dict[str, Any]]:
    """GET the OpenRouter models list (the ``data`` array). Key is optional, env-only."""
    source = env if env is not None else os.environ
    base = (base_url or source.get("OPENROUTER_BASE_URL") or _DEFAULT_BASE_URL).rstrip("/")
    api_key = source.get("OPENROUTER_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    owns_client = client is None
    http = client or httpx.AsyncClient()
    try:
        response = await http.get(f"{base}/models", headers=headers, timeout=timeout_s)
    except httpx.TimeoutException as exc:
        raise ProviderTimeoutError(
            "openrouter models request timed out", provider="openrouter"
        ) from exc
    except httpx.HTTPError as exc:
        raise ProviderResponseError(
            f"openrouter transport error: {exc}", provider="openrouter"
        ) from exc
    finally:
        if owns_client:
            await http.aclose()

    if response.status_code >= 400:
        raise ProviderResponseError(
            f"openrouter /models returned HTTP {response.status_code}: {response.text[:300]}",
            provider="openrouter",
            retryable=response.status_code >= 500,
        )
    data = response.json()
    models = data.get("data") if isinstance(data, dict) else None
    return list(models) if isinstance(models, list) else []


def build_openrouter_pricing(
    models: list[dict[str, Any]], *, as_of: str, version: str | None = None
) -> tuple[PricingTable, list[str]]:
    """Build a PricingTable from OpenRouter model dicts; returns (table, skipped_slugs)."""
    entries: list[PriceEntry] = []
    skipped: list[str] = []
    for model in models:
        slug = model.get("id") or model.get("canonical_slug")
        pricing = model.get("pricing")
        if not slug or not isinstance(pricing, dict):
            if slug:
                skipped.append(str(slug))
            continue
        try:
            prompt = float(pricing["prompt"])
            completion = float(pricing["completion"])
        except (KeyError, TypeError, ValueError):
            skipped.append(str(slug))
            continue
        ctx = model.get("context_length")
        entries.append(
            PriceEntry(
                provider="openrouter",
                model=str(slug),
                input_usd_per_1m=round(prompt * 1_000_000, 8),
                output_usd_per_1m=round(completion * 1_000_000, 8),
                source="openrouter_api",
                as_of=as_of,
                currency="USD",
                units="per_1m_tokens",
                context_length=int(ctx) if isinstance(ctx, (int, float)) else None,
                prompt_price_per_token=prompt,
                completion_price_per_token=completion,
            )
        )
    table = PricingTable(version=version or f"openrouter-{as_of}", entries=tuple(entries))
    return table, skipped
