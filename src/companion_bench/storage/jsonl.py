"""Append-only JSONL event log plus small JSON-object helpers.

``events.jsonl`` is the canonical raw artifact: one event per line, written append-only
and flushed immediately so a crashed run still leaves a readable partial log. Derived
single-object artifacts (``run.json``, ``scores.json``) use the model helpers here.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType
from typing import TextIO

from pydantic import BaseModel, TypeAdapter

from companion_bench.schemas.run import EVENT_ADAPTER, Event

__all__ = [
    "EventWriter",
    "read_events",
    "read_jsonl",
    "read_model_json",
    "write_model_json",
]


class EventWriter:
    """Context manager that appends events to a JSONL file, one per line.

    Each write is flushed so partial runs remain inspectable. Open in append mode so a
    resumed run never truncates prior history.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._handle: TextIO | None = None

    def __enter__(self) -> EventWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")
        return self

    def write(self, event: Event) -> None:
        if self._handle is None:  # pragma: no cover - misuse guard
            raise RuntimeError("EventWriter used outside of its context manager")
        self._handle.write(event.model_dump_json() + "\n")
        self._handle.flush()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


def read_jsonl(path: str | Path) -> Iterator[dict[str, object]]:
    """Yield each non-empty line of a JSONL file as a parsed dict."""
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_events(path: str | Path) -> list[Event]:
    """Read and validate every event from a JSONL event log."""
    return [EVENT_ADAPTER.validate_python(record) for record in read_jsonl(path)]


def write_model_json(path: str | Path, model: BaseModel) -> None:
    """Write a single Pydantic model to a pretty-printed JSON file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_model_json[ModelT: BaseModel](path: str | Path, adapter: TypeAdapter[ModelT]) -> ModelT:
    """Read and validate a single-object JSON file into a model."""
    return adapter.validate_json(Path(path).read_text(encoding="utf-8"))
