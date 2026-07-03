"""Offline benchmark-quality status: what the suite structurally is, what external validation
actually exists, and which public claims the current evidence does **not** support.

This is the machine-checkable companion to the prose honesty policy (``docs/public_claims.md``) and
the self-assessed scorecard (``docs/audits/benchmark_quality_scorecard.md``). It answers, from the
committed repo alone: how many tasks per family, is the held-out split disjoint, which scoring
version produced the numbers, are the committed gold labels **real human** or a **synthetic**
fixture, is inter-rater agreement / calibration computable, and what warnings follow.

Privacy: read-only, and it reports **counts and yes/no booleans only** — never an annotator
identity, never a private filename, never any label free-text. Files under ``data/gold/private/``
are counted, never opened.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict
from rich.table import Table

from companion_bench.evaluators.rule_based import (
    PARSE_METRICS_VERSION,
    SCORER_TYPE,
    SCORING_VERSION,
)
from companion_bench.runner.manifest import load_manifest_and_tasks, validate_manifest
from companion_bench.schemas.gold import GoldLabel
from companion_bench.utils.errors import CompanionBenchError

__all__ = ["QualityStatus", "collect_quality_status", "render_quality_status"]

# A label counts as REAL human data only when it is EXPLICITLY marked so — either
# ``not_human_collected=False`` or a whitelisted real source type (the importer stamps both). This
# is a whitelist on purpose: an unknown/new synthetic ``source_type`` must NOT be mistaken for real
# and silently switch off the "do NOT claim human-validated" warning (fail-safe toward synthetic).
_REAL_SOURCE_TYPES = frozenset({"real_human_pilot"})
_KEEP_PRIVATE = frozenset({"README.md", ".gitkeep"})


class QualityStatus(BaseModel):
    """A snapshot of the benchmark's structural + external-validation state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest_name: str | None
    manifest_ok: bool
    n_tasks: int
    families: dict[str, int]
    n_heldout: int | None
    heldout_disjoint: bool | None
    scoring_version: str
    scorer_type: str
    parse_metrics_version: str
    n_gold_labels: int
    n_gold_annotators: int
    n_gold_items: int
    gold_real_labels: bool
    gold_synthetic_only: bool
    private_label_files_present: bool
    agreement_available: bool
    rule_calibration_available: bool
    judge_calibration_available: bool
    sample_runs: tuple[str, ...]
    scorecard: dict[str, Any] | None
    warnings: tuple[str, ...]


def _load_gold_labels(gold_dir: Path) -> list[GoldLabel]:
    """Load every committed gold label defensively (a bad line is skipped, never fatal)."""
    labels: list[GoldLabel] = []
    if not gold_dir.is_dir():
        return labels
    for path in sorted(gold_dir.glob("*.jsonl")):
        if "response" in path.name:  # response fixtures are not labels
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                labels.append(GoldLabel.model_validate_json(line))
            except Exception:
                continue  # a malformed/foreign row degrades to "not a label", never a crash
    return labels


def _private_label_files_present(gold_dir: Path) -> bool:
    """True if ``data/gold/private/`` holds anything beyond its README/.gitkeep — count only."""
    private = gold_dir / "private"
    if not private.is_dir():
        return False
    return any(p.is_file() and p.name not in _KEEP_PRIVATE for p in private.iterdir())


def _find_file(name: str, dirs: list[Path]) -> bool:
    return any((d / name).is_file() for d in dirs if d.is_dir())


def collect_quality_status(
    manifest: Path,
    *,
    repo_root: Path,
    heldout: Path | None = None,
    gold_dir: Path | None = None,
    samples_dir: Path | None = None,
    scorecard_path: Path | None = None,
) -> QualityStatus:
    """Collect the offline quality/validation status of the benchmark from committed artifacts."""
    heldout = heldout if heldout is not None else repo_root / "manifests" / "heldout.yaml"
    gold_dir = gold_dir if gold_dir is not None else repo_root / "data" / "gold"
    samples_dir = samples_dir if samples_dir is not None else repo_root / "docs" / "samples"
    scorecard_path = (
        scorecard_path
        if scorecard_path is not None
        else repo_root / "docs" / "audits" / "benchmark_quality_scorecard.json"
    )

    report = validate_manifest(manifest)
    public_ids: set[str] = set(report.task_ids)

    n_heldout: int | None = None
    heldout_disjoint: bool | None = None
    if heldout.is_file():
        try:
            _, held_tasks = load_manifest_and_tasks(heldout)
            held_ids = {t.task_id for t in held_tasks}
            n_heldout = len(held_ids)
            heldout_disjoint = public_ids.isdisjoint(held_ids)
        except CompanionBenchError:
            n_heldout = None

    labels = _load_gold_labels(gold_dir)
    annotators = {lab.annotator_id_hash for lab in labels}
    items: dict[tuple[str, str, str], set[str]] = {}
    for lab in labels:
        items.setdefault((lab.task_id, lab.probe_id, lab.response_id), set()).add(
            lab.annotator_id_hash
        )
    gold_real_labels = any(
        (not lab.not_human_collected) or (lab.source_type in _REAL_SOURCE_TYPES) for lab in labels
    )
    private_present = _private_label_files_present(gold_dir)
    agreement_available = any(len(who) >= 2 for who in items.values())
    responses_present = _find_file("pilot_responses.jsonl", [gold_dir]) or any(
        gold_dir.glob("*responses*.jsonl")
    )
    rule_calibration_available = bool(labels) and responses_present
    judge_calibration_available = bool(labels) and _find_file(
        "judge_scores.json", [gold_dir, samples_dir]
    )

    sample_runs = (
        tuple(sorted(p.name for p in samples_dir.glob("*") if p.is_dir()))
        if (samples_dir.is_dir())
        else ()
    )

    scorecard: dict[str, Any] | None = None
    if scorecard_path.is_file():
        try:
            loaded = json.loads(scorecard_path.read_text(encoding="utf-8"))
            scorecard = loaded if isinstance(loaded, dict) else None
        except (OSError, json.JSONDecodeError):
            scorecard = None

    warnings = _build_warnings(
        manifest_ok=report.ok,
        heldout_disjoint=heldout_disjoint,
        gold_real_labels=gold_real_labels,
        private_present=private_present,
        agreement_available=agreement_available,
        scorecard_present=scorecard is not None,
    )

    return QualityStatus(
        manifest_name=report.name,
        manifest_ok=report.ok,
        n_tasks=report.n_tasks,
        families=report.families,
        n_heldout=n_heldout,
        heldout_disjoint=heldout_disjoint,
        scoring_version=SCORING_VERSION,
        scorer_type=SCORER_TYPE,
        parse_metrics_version=PARSE_METRICS_VERSION,
        n_gold_labels=len(labels),
        n_gold_annotators=len(annotators),
        n_gold_items=len(items),
        gold_real_labels=gold_real_labels,
        gold_synthetic_only=bool(labels) and not gold_real_labels,
        private_label_files_present=private_present,
        agreement_available=agreement_available,
        rule_calibration_available=rule_calibration_available,
        judge_calibration_available=judge_calibration_available,
        sample_runs=sample_runs,
        scorecard=scorecard,
        warnings=warnings,
    )


def _build_warnings(
    *,
    manifest_ok: bool,
    heldout_disjoint: bool | None,
    gold_real_labels: bool,
    private_present: bool,
    agreement_available: bool,
    scorecard_present: bool,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not manifest_ok:
        warnings.append("Default manifest is INVALID — run `companion-bench validate` for details.")
    if heldout_disjoint is False:
        warnings.append(
            "Held-out split leaks into the public suite — do NOT report generalization until fixed."
        )
    if not gold_real_labels:
        warnings.append(
            "No real human labels are committed — do NOT claim 'human-validated' / 'human-aligned' "
            "/ 'human-approved'. The committed gold set is a synthetic pilot fixture (workflow "
            "validation only)."
        )
        if private_present:
            warnings.append(
                "Private annotation files are present but no real labels are committed yet — run "
                "`companion-bench gold import-human` then `gold agreement` + `calibrate rules`."
            )
    if not agreement_available:
        warnings.append(
            "Inter-rater agreement is not computable from committed labels (need >= 2 annotators "
            "on the same item)."
        )
    if not scorecard_present:
        warnings.append(
            "No committed scorecard found — status shows suite structure only "
            "(expected docs/audits/benchmark_quality_scorecard.json)."
        )
    warnings.append(
        "Scores are scoped to these tasks, settings, model versions, and the rule-based scorer "
        "design — never a universal capability or 'most human' verdict."
    )
    return tuple(warnings)


def _yn(value: bool | None) -> str:
    return "n/a" if value is None else ("yes" if value else "no")


def render_quality_status(status: QualityStatus) -> Table:
    """A compact Rich table of the quality status (warnings are printed separately by the CLI)."""
    table = Table(title="CompanionBench quality status (offline, self-assessed)")
    table.add_column("field")
    table.add_column("value")

    def add(field: str, value: str) -> None:
        table.add_row(field, value)

    add("manifest", f"{status.manifest_name} ({'valid' if status.manifest_ok else 'INVALID'})")
    add("tasks", str(status.n_tasks))
    add("families", ", ".join(f"{k}={v}" for k, v in status.families.items()) or "n/a")
    add(
        "held-out split",
        "n/a" if status.n_heldout is None else f"{status.n_heldout} task(s)",
    )
    add("held-out disjoint", _yn(status.heldout_disjoint))
    add("scorer", f"{status.scorer_type} v{status.scoring_version}")
    add("parse metrics", status.parse_metrics_version)
    add(
        "gold labels",
        f"{status.n_gold_labels} label(s), {status.n_gold_annotators} annotator(s), "
        f"{status.n_gold_items} item(s)",
    )
    add(
        "gold label source",
        "REAL human" if status.gold_real_labels else "synthetic pilot (not human-collected)",
    )
    add("private label files present", _yn(status.private_label_files_present))
    add("human agreement available", _yn(status.agreement_available))
    add("rule calibration available", _yn(status.rule_calibration_available))
    add("judge calibration available", _yn(status.judge_calibration_available))
    add("sample runs", f"{len(status.sample_runs)} in docs/samples/")
    if status.scorecard is not None:
        avg = status.scorecard.get("overall_average")
        cats = status.scorecard.get("categories")
        n_cats = len(cats) if isinstance(cats, list) else 0
        add(
            "scorecard (self-assessed)",
            f"overall {avg}/10 across {n_cats} categories (roadmap, not an external grade)",
        )
    else:
        add("scorecard (self-assessed)", "not found")
    return table
