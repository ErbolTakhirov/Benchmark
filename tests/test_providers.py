"""Offline tests for the providers command + live-probe helper (no real network)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from companion_bench.adapters import describe_providers, probe_models
from companion_bench.cli import app

runner = CliRunner()


def test_describe_providers_reports_key_presence() -> None:
    infos = {i.provider: i for i in describe_providers({"OPENROUTER_API_KEY": "x" * 20})}
    assert infos["openrouter"].key_present is True
    assert infos["openrouter"].requires_key is True
    assert infos["mock"].requires_key is False
    assert infos["openai"].key_present is False  # not provided


def test_describe_providers_never_returns_key_value() -> None:
    secret = "sk-super-secret-value-1234567890"
    assert secret not in str(describe_providers({"OPENAI_API_KEY": secret}))


async def test_probe_mock_offline() -> None:
    results = await probe_models(["mock/empathetic-v1"])
    assert results[0].ok is True
    assert results[0].total_tokens and results[0].total_tokens > 0


def test_cli_providers_lists() -> None:
    result = runner.invoke(app, ["providers"])
    assert result.exit_code == 0
    assert "openrouter" in result.stdout
    assert "mock" in result.stdout


def test_cli_providers_probe_requires_live_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPANIONBENCH_LIVE", raising=False)
    result = runner.invoke(app, ["providers", "--probe"])
    assert result.exit_code == 1
