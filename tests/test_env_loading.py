"""Safe local ``.env`` loading: no crash when absent, shell env wins, never leaks into tests.

These exercise the CLI's dotenv support added for local OpenRouter runs. The autouse
``_keyless_offline_env`` fixture (see ``conftest.py``) plus the callback's pytest guard keep the
default suite offline + keyless even though the developer machine has a populated ``.env``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from companion_bench.cli import _load_local_dotenv, _main

# A neutral probe var the keyless fixture does not strip, so these tests are self-contained.
_VAR = "COMPANIONBENCH_DOTENV_PROBE"


def test_missing_dotenv_does_not_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)  # no .env here or in any parent
    monkeypatch.delenv(_VAR, raising=False)
    _load_local_dotenv()  # must be a silent no-op, not an error
    assert _VAR not in os.environ


def test_dotenv_values_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(_VAR, raising=False)
    (tmp_path / ".env").write_text(f"{_VAR}=from_dotenv\n", encoding="utf-8")
    _load_local_dotenv()
    assert os.environ[_VAR] == "from_dotenv"


def test_shell_env_overrides_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # override=False: a real exported value must win over the file (live opt-in stays explicit).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(_VAR, "from_shell")
    (tmp_path / ".env").write_text(f"{_VAR}=from_dotenv\n", encoding="utf-8")
    _load_local_dotenv()
    assert os.environ[_VAR] == "from_shell"


def test_callback_skips_dotenv_under_pytest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The Typer callback must NOT load .env during pytest, so a populated local .env never bleeds
    # the key / COMPANIONBENCH_LIVE into the keyless default suite. PYTEST_CURRENT_TEST is set now.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(_VAR, raising=False)
    (tmp_path / ".env").write_text(f"{_VAR}=should_not_load\n", encoding="utf-8")
    _main()
    assert _VAR not in os.environ


def test_env_is_gitignored() -> None:
    gitignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert "!.env.example" in gitignore  # the keyless template stays committable
