"""Online model-set validation against OpenRouter metadata (offline: crafted metadata)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pytest
from typer.testing import CliRunner

from companion_bench.cli import app
from companion_bench.config.model_sets import ModelEntry, ModelSet, check_against_openrouter

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]
EMOTOMO_SET = REPO_ROOT / "configs" / "model_sets" / "emotomo-openrouter.yaml"

_META = [
    {
        "id": "deepseek/deepseek-chat-v3-0324",
        "pricing": {"prompt": "0.0000003", "completion": "0.0000009"},
        "context_length": 64000,
        "supported_parameters": ["temperature", "max_tokens"],
    },
    {"id": "x/no-price", "context_length": 8000},
    {
        "id": "x/small-ctx",
        "pricing": {"prompt": "0.0000001", "completion": "0.0000002"},
        "context_length": 100,
        "supported_parameters": ["temperature"],
    },
]


def _set(entries: list[ModelEntry]) -> ModelSet:
    return ModelSet(set_id="t", models=tuple(entries))


def test_online_statuses() -> None:
    ms = _set(
        [
            ModelEntry(
                id="a",
                provider="openrouter",
                model="deepseek/deepseek-chat-v3-0324",
                needs_mapping=True,
                temperature=0.7,
                max_completion_tokens=500,
            ),
            ModelEntry(id="b", provider="openrouter", model="missing/slug"),
            ModelEntry(id="c", provider="openrouter", model="x/no-price"),
            ModelEntry(
                id="d", provider="openrouter", model="x/small-ctx", max_completion_tokens=500
            ),
        ]
    )
    by_model: dict[str | None, list[tuple[str, str]]] = defaultdict(list)
    for issue in check_against_openrouter(ms, _META):
        by_model[issue.model_id].append((issue.level, issue.message))

    assert any("live_verified" in m for _, m in by_model["a"])
    assert any("needs_mapping is true" in m for _, m in by_model["a"])  # flagged, not flipped
    assert any(lvl == "error" and "unavailable" in m for lvl, m in by_model["b"])
    assert any("pricing_missing" in m for _, m in by_model["c"])
    assert any("exceeds context_length" in m for _, m in by_model["d"])


def test_online_ignores_non_openrouter() -> None:
    ms = _set([ModelEntry(id="m", provider="mock", model="empathetic-v1")])
    assert check_against_openrouter(ms, _META) == []


def test_online_never_mutates_entry() -> None:
    entry = ModelEntry(
        id="a", provider="openrouter", model="deepseek/deepseek-chat-v3-0324", needs_mapping=True
    )
    check_against_openrouter(_set([entry]), _META)
    assert entry.needs_mapping is True  # frozen + never auto-flipped


def test_cli_online_requires_live(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPANIONBENCH_LIVE", raising=False)
    result = runner.invoke(app, ["models", "validate", "--model-set", str(EMOTOMO_SET), "--online"])
    assert result.exit_code == 1  # network call requires COMPANIONBENCH_LIVE=1


def test_cli_offline_validate_still_works() -> None:
    result = runner.invoke(app, ["models", "validate", "--model-set", str(EMOTOMO_SET)])
    assert result.exit_code == 0
    assert "is valid" in result.stdout
