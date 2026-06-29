"""Manifest schema and loading: resolve task globs and validate everything.

A manifest names a benchmark slice: which task files to include, default model(s), and
run knobs. ``validate_manifest`` returns a structured report the CLI prints, collecting
*all* task errors rather than failing on the first.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from companion_bench.schemas.run import RunConfig
from companion_bench.schemas.task import Task
from companion_bench.utils.errors import ManifestError, TaskLoadError

__all__ = [
    "Manifest",
    "ManifestReport",
    "load_manifest",
    "load_manifest_and_tasks",
    "load_task_file",
    "resolve_task_files",
    "validate_manifest",
]


class Manifest(BaseModel):
    """A benchmark manifest (YAML)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    version: str
    description: str = ""
    # Globs/paths to task YAML files, resolved relative to the manifest's directory.
    task_paths: tuple[str, ...] = Field(min_length=1)
    # Default model refs ("provider/model"); the CLI --model flag overrides these.
    models: tuple[str, ...] = ()
    run: RunConfig = RunConfig()


class ManifestReport(BaseModel):
    """Structured result of validating a manifest and its tasks."""

    model_config = ConfigDict(extra="forbid")

    manifest_path: str
    name: str | None
    ok: bool
    n_tasks: int
    families: dict[str, int]
    task_ids: tuple[str, ...]
    errors: tuple[str, ...]


def load_manifest(path: str | Path) -> Manifest:
    """Load and validate a manifest YAML file."""
    p = Path(path)
    if not p.is_file():
        raise ManifestError(f"manifest not found: {p}")
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"{p}: invalid YAML: {exc}") from exc
    try:
        return Manifest.model_validate(data)
    except ValidationError as exc:
        raise ManifestError(f"{p}: invalid manifest: {exc}") from exc


def resolve_task_files(manifest: Manifest, base_dir: str | Path) -> list[Path]:
    """Expand the manifest's task globs (relative to ``base_dir``) to sorted unique files."""
    base = Path(base_dir)
    files: set[Path] = set()
    for pattern in manifest.task_paths:
        files.update(p for p in base.glob(pattern) if p.is_file())
    return sorted(files)


def load_task_file(path: str | Path) -> Task:
    """Load and validate a single task YAML file."""
    p = Path(path)
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TaskLoadError(f"{p}: invalid YAML: {exc}") from exc
    try:
        return Task.model_validate(data)
    except ValidationError as exc:
        raise TaskLoadError(f"{p}: invalid task: {exc}") from exc


def load_manifest_and_tasks(path: str | Path) -> tuple[Manifest, list[Task]]:
    """Load a manifest plus every task it references; raise on any problem."""
    manifest = load_manifest(path)
    files = resolve_task_files(manifest, Path(path).parent)
    if not files:
        raise ManifestError(f"{path}: no task files matched {list(manifest.task_paths)}")
    tasks = [load_task_file(f) for f in files]
    _check_duplicate_ids(tasks)
    return manifest, tasks


def _check_duplicate_ids(tasks: list[Task]) -> None:
    counts = Counter(t.task_id for t in tasks)
    dupes = sorted(tid for tid, n in counts.items() if n > 1)
    if dupes:
        raise ManifestError(f"duplicate task_id(s) across tasks: {dupes}")


def validate_manifest(path: str | Path) -> ManifestReport:
    """Validate a manifest and all its tasks, collecting every error."""
    errors: list[str] = []
    try:
        manifest = load_manifest(path)
    except ManifestError as exc:
        return ManifestReport(
            manifest_path=str(path),
            name=None,
            ok=False,
            n_tasks=0,
            families={},
            task_ids=(),
            errors=(str(exc),),
        )

    base = Path(path).parent
    for pattern in manifest.task_paths:
        if not any(p.is_file() for p in base.glob(pattern)):
            errors.append(f"task pattern matched no files: {pattern}")

    tasks: list[Task] = []
    for file in resolve_task_files(manifest, base):
        try:
            tasks.append(load_task_file(file))
        except TaskLoadError as exc:
            errors.append(str(exc))

    counts = Counter(t.task_id for t in tasks)
    for tid, n in sorted(counts.items()):
        if n > 1:
            errors.append(f"duplicate task_id: {tid} ({n} files)")

    families = dict(sorted(Counter(t.family.value for t in tasks).items()))
    return ManifestReport(
        manifest_path=str(path),
        name=manifest.name,
        ok=not errors,
        n_tasks=len(tasks),
        families=families,
        task_ids=tuple(t.task_id for t in tasks),
        errors=tuple(errors),
    )
