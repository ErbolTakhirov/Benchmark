"""Shared pytest configuration.

Tests marked ``@pytest.mark.live`` make real network calls and are **skipped by default**.
Run them only when ``COMPANIONBENCH_LIVE=1`` is set (and the relevant API keys are present).
The default ``pytest -q`` and CI stay fully offline and keyless.
"""

from __future__ import annotations

import os

import pytest

LIVE_ENV = "COMPANIONBENCH_LIVE"


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get(LIVE_ENV) == "1":
        return
    skip_live = pytest.mark.skip(reason=f"live test; set {LIVE_ENV}=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
