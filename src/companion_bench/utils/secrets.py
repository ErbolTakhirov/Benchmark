"""Secret handling: env-only resolution, redaction, and artifact scanning.

CompanionBench resolves API keys **only** from environment variables — never from CLI
arguments, manifests, or config files — and never writes them into artifacts. This module
provides the redaction helper used on any text that might contain a key, and the scanner the
secret-leak test and ``release-check`` use to prove no key reached a run's artifacts.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from pathlib import Path

__all__ = [
    "SECRET_ENV_VARS",
    "collect_secret_values",
    "redact",
    "scan_paths_for_secrets",
    "scan_run_dir",
    "scan_text_for_secrets",
]

# Environment variables that hold secrets. Adapters read keys only from these.
SECRET_ENV_VARS: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENAI_COMPATIBLE_API_KEY",
    "HF_TOKEN",
)

# Ignore very short values to avoid false-positive substring matches when scanning.
_MIN_SECRET_LEN = 8

_PLACEHOLDER = "***REDACTED***"


def collect_secret_values(env: Mapping[str, str] | None = None) -> set[str]:
    """The non-trivial secret values currently set in the environment."""
    source = env if env is not None else os.environ
    values: set[str] = set()
    for name in SECRET_ENV_VARS:
        value = source.get(name)
        if value and len(value) >= _MIN_SECRET_LEN:
            values.add(value)
    return values


def redact(text: str, secret_values: Iterable[str], placeholder: str = _PLACEHOLDER) -> str:
    """Replace every secret value in ``text`` with a placeholder (longest first)."""
    for secret in sorted((s for s in secret_values if s), key=len, reverse=True):
        text = text.replace(secret, placeholder)
    return text


def scan_text_for_secrets(text: str, secret_values: Iterable[str]) -> list[str]:
    """Return the secret values that appear in ``text`` (empty if none)."""
    return sorted({s for s in secret_values if s and s in text})


def scan_paths_for_secrets(
    paths: Iterable[str | Path], secret_values: Iterable[str]
) -> dict[str, list[str]]:
    """Scan files for secret values; returns ``{path: [leaked values]}`` for any hits."""
    values = list(secret_values)
    hits: dict[str, list[str]] = {}
    for path in paths:
        p = Path(path)
        if not p.is_file():
            continue
        found = scan_text_for_secrets(p.read_text(encoding="utf-8", errors="ignore"), values)
        if found:
            hits[str(p)] = found
    return hits


def scan_run_dir(run_dir: str | Path, secret_values: Iterable[str]) -> dict[str, list[str]]:
    """Scan every file under a run directory for leaked secret values."""
    root = Path(run_dir)
    files = (p for p in root.rglob("*") if p.is_file())
    return scan_paths_for_secrets(files, secret_values)
