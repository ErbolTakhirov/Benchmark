"""Deterministic id generation.

Run ids and event ids are derived purely from their inputs (manifest, model, seed, and a
monotonic counter) so that re-running the same benchmark configuration yields identical
ids — a prerequisite for reproducible, diff-able artifacts.
"""

from __future__ import annotations

import hashlib
import re

__all__ = ["IdFactory", "make_run_id", "short_hash", "slugify"]

_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def slugify(text: str) -> str:
    """Lowercase, filesystem-safe slug."""
    return _SLUG_RE.sub("-", text).strip("-").lower()


def short_hash(*parts: str, length: int = 8) -> str:
    """A stable short hex digest of the given parts."""
    joined = "\x1f".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def make_run_id(manifest_name: str, model_ref: str, seed: int) -> str:
    """A deterministic, human-readable run id.

    Same (manifest, model, seed) always produces the same id, e.g.
    ``smoke-mock-empathetic-v1-1f3c9a2b``.
    """
    digest = short_hash(manifest_name, model_ref, str(seed))
    return f"{slugify(manifest_name)}-{slugify(model_ref)}-{digest}"


class IdFactory:
    """Issues deterministic, sequential event ids scoped to a run."""

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._counter = 0

    def next_event_id(self) -> str:
        event_id = f"{self._run_id}-evt-{self._counter:05d}"
        self._counter += 1
        return event_id

    @property
    def issued(self) -> int:
        return self._counter
