"""Shared pytest configuration.

Tests marked ``@pytest.mark.live`` make real network calls and are **skipped by default**.
Run them only when ``COMPANIONBENCH_LIVE=1`` is set (and the relevant API keys are present).
The default ``pytest -q`` and CI stay fully offline and keyless.
"""

from __future__ import annotations

import os

import pytest

from companion_bench.utils.secrets import SECRET_ENV_VARS

LIVE_ENV = "COMPANIONBENCH_LIVE"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get(LIVE_ENV) == "1":
        return
    skip_live = pytest.mark.skip(reason=f"live test; set {LIVE_ENV}=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(autouse=True)
def _keyless_offline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the default suite offline + keyless even when a populated local ``.env`` exists.

    A real ``.env`` (``OPENROUTER_API_KEY`` + ``COMPANIONBENCH_LIVE=1``) must never bleed into
    tests via the CLI's dotenv-loading callback. When the live opt-in is *not* set in the shell,
    strip the live flag and every secret env var before each test. An explicit
    ``COMPANIONBENCH_LIVE=1`` shell export (used to run ``@pytest.mark.live`` tests) is left alone.
    """
    if os.environ.get(LIVE_ENV) == "1":
        return
    monkeypatch.delenv(LIVE_ENV, raising=False)
    for name in SECRET_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
