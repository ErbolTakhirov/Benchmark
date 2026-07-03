"""`quality status`: offline external-validation status is honest about synthetic gold labels."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from companion_bench.cli import app
from companion_bench.quality import collect_quality_status
from companion_bench.schemas.gold import GoldLabel, OverallPreference

REPO_ROOT = Path(__file__).resolve().parents[1]
FULL = REPO_ROOT / "manifests" / "full.yaml"

runner = CliRunner()


def _gold_dir_with_label(tmp_path: Path, **overrides: object) -> Path:
    gold = tmp_path / "gold"
    gold.mkdir()
    label = GoldLabel(
        gold_set_id="t",
        task_id="x",
        probe_id="p",
        response_id="r",
        annotator_id_hash="h",
        annotation_timestamp="t",
        overall_preference=OverallPreference.ACCEPT,
        **overrides,  # type: ignore[arg-type]
    )
    (gold / "labels.jsonl").write_text(label.model_dump_json() + "\n", encoding="utf-8")
    return gold


def test_status_reports_synthetic_gold_and_warns() -> None:
    status = collect_quality_status(FULL, repo_root=REPO_ROOT)
    # The committed gold set is a synthetic fixture, so real-human validation is NOT claimable.
    assert status.gold_real_labels is False
    assert status.gold_synthetic_only is True
    assert any("human-validated" in w for w in status.warnings)
    # Structural facts.
    assert status.manifest_ok is True
    assert status.heldout_disjoint is True
    assert status.scoring_version == "1.1.0"
    assert all(count >= 25 for count in status.families.values())
    # The pilot fixture has multiple annotators per item, so agreement is computable.
    assert status.agreement_available is True


def test_status_embeds_ten_category_scorecard() -> None:
    status = collect_quality_status(FULL, repo_root=REPO_ROOT)
    assert status.scorecard is not None
    assert len(status.scorecard["categories"]) == 10


def test_unknown_synthetic_source_type_is_not_treated_as_real(tmp_path: Path) -> None:
    # Fail-safe: a synthetic label with an unrecognized source_type must NOT be reported as real
    # (that would silently switch off the "do NOT claim human-validated" warning).
    gold = _gold_dir_with_label(
        tmp_path, source_type="synthetic_v2_unknown", not_human_collected=True
    )
    status = collect_quality_status(FULL, repo_root=REPO_ROOT, gold_dir=gold)
    assert status.gold_real_labels is False
    assert any("human-validated" in w for w in status.warnings)


def test_explicit_human_collected_label_is_treated_as_real(tmp_path: Path) -> None:
    gold = _gold_dir_with_label(tmp_path, source_type="real_human_pilot", not_human_collected=False)
    status = collect_quality_status(FULL, repo_root=REPO_ROOT, gold_dir=gold)
    assert status.gold_real_labels is True


def test_status_cli_runs_and_json_parses() -> None:
    text = runner.invoke(app, ["quality", "status"])
    assert text.exit_code == 0, text.stdout
    assert "quality status" in text.stdout

    as_json = runner.invoke(app, ["quality", "status", "--json"])
    assert as_json.exit_code == 0, as_json.stdout
    payload = json.loads(as_json.stdout)
    assert payload["gold_real_labels"] is False
    assert payload["warnings"]
