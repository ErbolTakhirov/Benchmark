"""Model-set schema, validation, and the `models validate` CLI command."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from companion_bench.cli import app
from companion_bench.config.model_sets import ModelSet, load_model_set, validate_model_set

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "configs" / "model_sets" / "example.yaml"
runner = CliRunner()


def make_set(models: list[dict[str, Any]], set_id: str = "s") -> ModelSet:
    return ModelSet.model_validate({"set_id": set_id, "models": models})


def test_model_entry_derived_views() -> None:
    ms = make_set(
        [
            {
                "id": "m",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.2,
                "max_completion_tokens": 256,
            }
        ]
    )
    entry = ms.models[0]
    assert entry.ref == "openai/gpt-4o-mini"
    assert entry.spec().provider == "openai"
    assert entry.config_overrides() == {"temperature": 0.2, "max_tokens": 256}


def test_enabled_models_filters() -> None:
    ms = make_set(
        [
            {"id": "a", "provider": "mock", "model": "empathetic-v1", "enabled": True},
            {"id": "b", "provider": "mock", "model": "silent-v1", "enabled": False},
        ]
    )
    assert [m.id for m in ms.enabled_models()] == ["a"]


def test_validate_ok_for_registered_providers() -> None:
    ms = make_set([{"id": "a", "provider": "openrouter", "model": "vendor/x"}])
    report = validate_model_set(ms)
    assert report.ok is True


def test_validate_errors_on_unknown_provider() -> None:
    ms = make_set([{"id": "a", "provider": "not-a-provider", "model": "x"}])
    report = validate_model_set(ms)
    assert report.ok is False
    assert any(i.level == "error" and "unknown provider" in i.message for i in report.issues)


def test_validate_warns_on_needs_mapping() -> None:
    ms = make_set([{"id": "a", "provider": "openrouter", "model": "x", "needs_mapping": True}])
    report = validate_model_set(ms)
    assert report.ok is True  # warning, not error
    assert any(i.level == "warning" and "needs_mapping" in i.message for i in report.issues)


def test_load_example_model_set() -> None:
    ms = load_model_set(EXAMPLE)
    assert ms.set_id == "example"
    assert len(ms.enabled_models()) == 1


def test_cli_models_validate_ok() -> None:
    result = runner.invoke(app, ["models", "validate", "--model-set", str(EXAMPLE)])
    assert result.exit_code == 0
    assert "is valid" in result.stdout


def test_cli_models_validate_rejects_bad_provider(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "set_id: bad\nmodels:\n  - id: a\n    provider: nope\n    model: x\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["models", "validate", "--model-set", str(bad)])
    assert result.exit_code == 1
