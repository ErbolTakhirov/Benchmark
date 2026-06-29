"""OpenRouter pricing sync: build conversion, mocked fetch, and the CLI gate (offline)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from companion_bench.cli import app
from companion_bench.config.openrouter_pricing import (
    build_openrouter_pricing,
    fetch_openrouter_models,
)
from companion_bench.config.pricing import load_pricing
from companion_bench.schemas.model import TokenUsage

runner = CliRunner()

_MODELS = [
    {
        "id": "deepseek/deepseek-chat-v3-0324",
        "pricing": {"prompt": "0.0000003", "completion": "0.0000009"},
        "context_length": 64000,
    },
    {"id": "broken/no-pricing"},  # no pricing block -> skipped
    {
        "id": "x/bad-number",
        "pricing": {"prompt": "abc", "completion": "0.1"},
    },  # non-numeric -> skipped
]


def test_build_converts_per_token_to_per_1m_and_skips_bad() -> None:
    table, skipped = build_openrouter_pricing(_MODELS, as_of="2026-06-29")
    assert len(table.entries) == 1
    entry = table.entries[0]
    assert entry.model == "deepseek/deepseek-chat-v3-0324"
    assert entry.input_usd_per_1m == 0.3  # 0.0000003 * 1e6
    assert entry.output_usd_per_1m == 0.9
    assert entry.source == "openrouter_api"
    assert entry.context_length == 64000
    assert entry.prompt_price_per_token == 0.0000003
    assert sorted(skipped) == ["broken/no-pricing", "x/bad-number"]


def test_built_table_prices_the_emotomo_slug() -> None:
    table, _ = build_openrouter_pricing(_MODELS, as_of="2026-06-29")
    cost = table.cost(
        "openrouter",
        "deepseek/deepseek-chat-v3-0324",
        TokenUsage(prompt_tokens=1_000_000, completion_tokens=0),
    )
    assert cost == 0.3  # 1M prompt tokens at $0.30/1M


def test_synced_yaml_round_trips(tmp_path: Path) -> None:
    import yaml

    table, _ = build_openrouter_pricing(_MODELS, as_of="2026-06-29")
    path = tmp_path / "pricing.yaml"
    path.write_text(
        yaml.safe_dump(table.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
    )
    reloaded = load_pricing(path)
    assert reloaded.rate("openrouter", "deepseek/deepseek-chat-v3-0324") == (0.3, 0.9)


async def test_fetch_via_mock_transport() -> None:
    payload = {"data": _MODELS}
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        models = await fetch_openrouter_models(env={}, client=client)
    finally:
        await client.aclose()
    assert captured["url"].endswith("/models")  # type: ignore[union-attr]
    assert models[0]["id"] == "deepseek/deepseek-chat-v3-0324"


def test_cli_sync_requires_live_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPANIONBENCH_LIVE", raising=False)
    result = runner.invoke(app, ["pricing", "sync-openrouter", "--out", str(tmp_path / "p.yaml")])
    assert result.exit_code == 1  # network call requires COMPANIONBENCH_LIVE=1
    assert not (tmp_path / "p.yaml").exists()
