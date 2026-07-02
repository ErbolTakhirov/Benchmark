"""Human-annotation import: de-identification, PII refusal, and the committed packet's hygiene."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from companion_bench.cli import app
from companion_bench.evaluators.agreement import compute_agreement
from companion_bench.evaluators.calibration import calibrate_rules_vs_gold
from companion_bench.gold_ingest import hash_annotator, import_human_rows, scan_pii
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.gold import GoldLabel, GoldResponse
from companion_bench.schemas.model import Decision

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKET = REPO_ROOT / "analysis" / "annotation_round_v0_1"
TS = "2026-07-03T00:00:00Z"


def _row(**over: str) -> dict[str, str]:
    base = {
        "task_id": "empathy-grief-support-gentle",
        "probe_id": "p1",
        "response_id": "itm-001",
        "annotator_id": "alice",
        "annotator_name": "Alice Real",
        "annotator_email": "alice@example.com",
        "empathy_rating": "5",
        "empathy_confidence": "4",
        "empathy_rationale": "warm and specific",
        "safety_rating": "5",
        "overall_preference": "accept",
        "notes": "",
    }
    base.update(over)
    return base


def _import(rows: list[dict[str, str]], salt: str = "s") -> tuple[list[GoldLabel], list[str]]:
    return import_human_rows(rows, salt=salt, gold_set_id="human-v0.1", annotation_timestamp=TS)


# --------------------------------------------------------------------------- hashing
def test_hash_is_deterministic_and_salt_sensitive() -> None:
    assert hash_annotator("alice", "s") == hash_annotator("alice", "s")
    assert hash_annotator("alice", "s") != hash_annotator("alice", "other")
    assert hash_annotator("alice", "s") != hash_annotator("bob", "s")
    assert hash_annotator("alice", "s").startswith("anon-")


def test_scan_pii_detects_email_and_phone_not_dates() -> None:
    assert "email" in scan_pii("reach me at a@b.com")
    assert "phone" in scan_pii("call 415-555-2671")
    assert scan_pii("it happened on 2026-07-03 at noon") == []  # ISO date is not a phone


# --------------------------------------------------------------------------- de-identification
def test_import_drops_identity_and_hashes() -> None:
    labels, issues = _import([_row()])
    assert issues == []
    assert len(labels) == 1
    lab = labels[0]
    assert lab.annotator_id_hash == hash_annotator("alice", "s")
    assert lab.source_type == "real_human_pilot"
    assert lab.not_human_collected is False
    # Identity never reaches the label.
    blob = lab.model_dump_json()
    assert "alice@example.com" not in blob and "Alice Real" not in blob and "alice" not in blob


def test_invalid_rating_is_rejected() -> None:
    _, issues = _import([_row(empathy_rating="6")])
    assert any("row 1" in i for i in issues)


def test_email_in_rationale_refused() -> None:
    _, issues = _import([_row(empathy_rationale="ping carol@example.com")])
    assert any("email" in i for i in issues)


def test_phone_in_notes_refused() -> None:
    _, issues = _import([_row(notes="my cell is 415-555-2671")])
    assert any("phone" in i for i in issues)


def test_bare_and_local_phone_refused() -> None:
    # Bare 10-digit and local NNN-NNNN forms must be caught (the fail-closed fix).
    assert any("phone" in i for i in _import([_row(notes="call 4155552671 anytime")])[1])
    assert any("phone" in i for i in _import([_row(empathy_rationale="ext 555-2671")])[1])


def test_iso_date_is_not_a_phone() -> None:
    labels, issues = _import([_row(notes="we spoke on 2026-07-03 about it")])
    assert issues == [] and len(labels) == 1  # a date must not trip the phone scan


def test_name_or_email_in_hash_column_is_re_hashed_not_stored() -> None:
    # A value pasted into annotator_id_hash that isn't an opaque anon id gets hashed, not stored.
    labels, issues = _import([_row(annotator_id="", annotator_id_hash="Jane Q Public")])
    assert issues == []
    assert labels[0].annotator_id_hash == hash_annotator("Jane Q Public", "s")
    assert "Jane" not in labels[0].model_dump_json()
    # An email pasted into the id column is hashed AWAY (de-identified), so nothing leaks.
    labels2, issues2 = _import([_row(annotator_id="", annotator_id_hash="jane@example.com")])
    assert issues2 == []
    assert labels2[0].annotator_id_hash == hash_annotator("jane@example.com", "s")
    assert "jane@example.com" not in labels2[0].model_dump_json()


def test_model_id_is_never_imported() -> None:
    # model identity is dropped even if a raw column supplies it (packet is blinded).
    labels, _ = _import([{**_row(), "model_id": "openrouter/some-model"}])
    assert labels[0].model_id is None


def test_missing_annotator_id_flagged() -> None:
    _, issues = _import([_row(annotator_id="", annotator_name="", annotator_email="")])
    assert any("annotator_id" in i for i in issues)


def test_imported_labels_feed_agreement() -> None:
    rows = [
        _row(annotator_id="alice"),
        _row(annotator_id="bob", empathy_rating="4", overall_preference="borderline"),
    ]
    labels, issues = _import(rows)
    assert issues == []
    report = compute_agreement(labels)
    assert report.overall.n_annotators == 2  # two distinct hashed annotators on one item


# --------------------------------------------------------------------------- committed hygiene
def test_committed_packet_has_no_pii() -> None:
    from companion_bench.gold_ingest import EMAIL_RE, PHONE_RE

    for name in ("annotation_packet.csv", "annotation_packet.jsonl"):
        text = (PACKET / name).read_text(encoding="utf-8")
        assert not EMAIL_RE.search(text), name
        assert not PHONE_RE.search(text), name


def test_committed_packet_is_blinded_and_covers_families() -> None:
    import csv

    resps = [
        GoldResponse.model_validate(json.loads(x))
        for x in (PACKET / "annotation_packet.jsonl").read_text().splitlines()
    ]
    assert len(resps) >= 60
    assert all(r.model_id == "blinded" for r in resps)  # model identity hidden
    assert any(not r.parsed for r in resps)  # includes parse/format cases
    with (PACKET / "annotation_packet.csv").open(encoding="utf-8", newline="") as fh:
        families = {row["family"] for row in csv.DictReader(fh)}
    assert families == {"empathy", "initiative", "timing", "adaptation", "abstention", "safety"}


def test_gitignore_protects_private_data() -> None:
    import subprocess

    def ignored(path: str) -> bool:
        return (
            subprocess.run(
                ["git", "check-ignore", "-q", path], cwd=REPO_ROOT, check=False
            ).returncode
            == 0
        )

    # Raw annotator files + the private blinding map must be ignored; the packet must NOT be.
    assert ignored("data/gold/private/annotator_raw.csv")
    assert ignored("analysis/annotation_round_v0_1/private/blinding_map.jsonl")
    assert not ignored("analysis/annotation_round_v0_1/annotation_packet.csv")
    assert not ignored("data/gold/private/README.md")


# --------------------------------------------------------------------------- calibration mismatch
def test_calibration_surfaces_mismatched_ids() -> None:
    _, tasks = load_manifest_and_tasks(REPO_ROOT / "manifests" / "full.yaml")
    idx = {t.task_id: t for t in tasks}
    gold = _import([_row(response_id="ghost")])[0]
    resp = GoldResponse(
        response_id="real-one",
        task_id="empathy-grief-support-gentle",
        probe_id="p1",
        parsed=True,
        decision=Decision.INTERVENE,
        message="I'm here with you",
    )
    report = calibrate_rules_vs_gold(gold, [resp], idx)
    assert any("no matching scored response" in c for c in report.caveats)


# --------------------------------------------------------------------------- CLI gate
def test_cli_import_requires_salt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMPANIONBENCH_ANNOTATOR_SALT", raising=False)
    raw = tmp_path / "raw.csv"
    raw.write_text(
        "task_id,probe_id,response_id,annotator_id,empathy_rating,overall_preference\n"
        "empathy-grief-support-gentle,p1,itm-001,alice,5,accept\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(
        app, ["gold", "import-human", "--input", str(raw), "--out", str(tmp_path / "o.jsonl")]
    )
    assert result.exit_code == 1
    assert not (tmp_path / "o.jsonl").exists()


def test_cli_import_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMPANIONBENCH_ANNOTATOR_SALT", "unit-salt")
    raw = tmp_path / "raw.csv"
    raw.write_text(
        "task_id,probe_id,response_id,annotator_id,annotator_email,empathy_rating,overall_preference\n"
        "empathy-grief-support-gentle,p1,itm-001,alice,alice@example.com,5,accept\n",
        encoding="utf-8",
    )
    out = tmp_path / "deid.jsonl"
    result = CliRunner().invoke(
        app, ["gold", "import-human", "--input", str(raw), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert out.is_file()
    assert "alice@example.com" not in out.read_text()  # email dropped
