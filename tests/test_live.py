"""Opt-in LIVE tests — skipped unless COMPANIONBENCH_LIVE=1 (see tests/conftest.py).

These make real network calls and need the relevant API key in the environment. They are a
real smoke test of a provider; the default ``pytest -q`` never runs them.
"""

from __future__ import annotations

import os

import pytest

from companion_bench.adapters.probe import probe_model

pytestmark = pytest.mark.live


async def test_openrouter_live_probe() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")
    ref = os.environ.get("COMPANIONBENCH_PROBE_MODEL", "openrouter/openai/gpt-4o-mini")
    result = await probe_model(ref)
    assert result.ok, result.error
