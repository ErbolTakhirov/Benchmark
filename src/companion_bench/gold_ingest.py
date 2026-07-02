"""Import raw human annotations into de-identified gold labels — offline, privacy-first.

A raw annotator CSV (the annotation packet, filled in) may contain names/emails/phones and a
real annotator handle. This module turns it into validated :class:`~companion_bench.schemas.gold.GoldLabel`
records that are safe to commit:

- annotator identity is replaced by a **salted hash** (`anon-<16hex>`); the salt comes from an env
  var so the mapping cannot be reversed from the committed file alone;
- name/email/phone *columns* are dropped entirely (never read into a label);
- retained free-text (rationales, notes) is **PII-scanned**; if an email or phone survives, the
  import is refused rather than writing anything (fail closed);
- ratings are validated (1-5) by the schema;
- each label is stamped ``source_type="real_human_pilot"``, ``not_human_collected=False``.

No network, no live APIs. The raw input file is never modified.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence

from companion_bench.schemas.gold import GoldDimensionRating, GoldLabel
from companion_bench.schemas.task import Dimension

__all__ = [
    "EMAIL_RE",
    "PHONE_RE",
    "hash_annotator",
    "import_human_rows",
    "scan_pii",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone-focused, fail-closed. Matches intl "+…", (NNN) NNN-NNNN, NNN-NNN-NNNN, local NNN-NNNN, AND
# bare runs of 10+ digits. It will NOT match ISO dates like 2026-07-03 (max 4 consecutive digits).
# Best-effort only — the operator must still eyeball free text (obfuscations like "j [at] x" slip by).
PHONE_RE = re.compile(
    r"\+\d[\d\s().-]{7,}\d"
    r"|\(\d{3}\)\s?\d{3}[\s.-]?\d{4}"
    r"|\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b"
    r"|\b\d{3}[\s.-]\d{4}\b"
    r"|\b\d{10,}\b"
)

# An already-opaque annotator id. Anything NOT matching this is (re-)hashed, so a name/email pasted
# into the annotator_id_hash column is de-identified rather than stored verbatim.
_ANON_RE = re.compile(r"anon-[0-9a-f]{16}")


def hash_annotator(identifier: str, salt: str) -> str:
    """Salted, one-way annotator id -> ``anon-<16hex>`` (stable for a given salt)."""
    digest = hashlib.sha256(f"{salt}:{identifier}".encode()).hexdigest()
    return f"anon-{digest[:16]}"


def scan_pii(text: str) -> list[str]:
    """Return the PII kinds (``email``/``phone``) found in ``text`` (empty if clean)."""
    kinds: list[str] = []
    if EMAIL_RE.search(text):
        kinds.append("email")
    if PHONE_RE.search(text):
        kinds.append("phone")
    return kinds


def _parse_rating(raw: str, field: str, row_num: int, issues: list[str]) -> int | None:
    value = raw.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        issues.append(f"row {row_num}: {field} is not an integer ({value!r})")
        return None


def _dimensions(
    row: Mapping[str, str], row_num: int, issues: list[str]
) -> dict[Dimension, GoldDimensionRating]:
    dims: dict[Dimension, GoldDimensionRating] = {}
    for dim in Dimension:
        rating = _parse_rating(
            row.get(f"{dim.value}_rating", ""), f"{dim.value}_rating", row_num, issues
        )
        confidence = _parse_rating(
            row.get(f"{dim.value}_confidence", ""), f"{dim.value}_confidence", row_num, issues
        )
        rationale = (row.get(f"{dim.value}_rationale", "") or "").strip()
        if rating is None and confidence is None and not rationale:
            continue  # dimension skipped by the annotator
        try:
            dims[dim] = GoldDimensionRating(
                rating=rating, confidence=confidence, rationale=rationale
            )
        except Exception as exc:  # out-of-range rating etc. -> a fixable data issue
            issues.append(f"row {row_num}: invalid {dim.value} rating/confidence ({exc})")
    return dims


def import_human_rows(
    rows: Sequence[Mapping[str, str]],
    *,
    salt: str,
    gold_set_id: str,
    version: str = "0.1",
    annotation_timestamp: str,
) -> tuple[list[GoldLabel], list[str]]:
    """De-identify + validate raw annotation rows.

    Returns ``(labels, issues)``. When ``issues`` is non-empty the caller must refuse to write —
    nothing is de-identified with unresolved PII or invalid ratings.
    """
    labels: list[GoldLabel] = []
    issues: list[str] = []
    for i, row in enumerate(rows, start=1):
        before = len(issues)
        # Annotator identity: hash any value that isn't already an opaque anon id (so a name/email in
        # either the annotator_id or annotator_id_hash column is de-identified, never stored raw).
        ident = (row.get("annotator_id") or row.get("annotator_id_hash") or "").strip()
        if not ident:
            issues.append(f"row {i}: missing annotator_id")
            continue
        annotator_hash = ident if _ANON_RE.fullmatch(ident) else hash_annotator(ident, salt)

        notes = (row.get("notes") or "").strip()
        dims = _dimensions(row, i, issues)
        # PII scan over the free text that would be written (rationales + notes).
        for field_name, text in [
            ("notes", notes),
            *((f"{d.value}_rationale", dr.rationale) for d, dr in dims.items()),
        ]:
            for kind in scan_pii(text):
                issues.append(f"row {i}: {kind} detected in {field_name} — redact before importing")

        pref = (row.get("overall_preference") or "").strip().lower()
        try:
            label = GoldLabel.model_validate(
                {
                    "gold_set_id": gold_set_id,
                    "version": version,
                    "task_id": (row.get("task_id") or "").strip(),
                    "probe_id": (row.get("probe_id") or "").strip(),
                    "response_id": (row.get("response_id") or "").strip(),
                    # model identity is never imported from a raw annotation (packet is blinded).
                    "model_id": None,
                    "annotator_id_hash": annotator_hash,
                    "annotation_timestamp": annotation_timestamp,
                    "dimensions": {d.value: dr.model_dump() for d, dr in dims.items()},
                    "overall_preference": pref,
                    "notes": notes,
                    "source_type": "real_human_pilot",
                    "not_human_collected": False,
                    "purpose": "real human annotation pilot",
                    "pii_check": True,
                }
            )
        except Exception as exc:  # pydantic ValidationError etc. -> a fixable data issue
            issues.append(f"row {i}: invalid label ({exc})")
            continue
        # Backstop: scan the FULL serialized label so PII in any field (ids, etc.) can't slip through.
        for kind in scan_pii(label.model_dump_json()):
            issues.append(
                f"row {i}: {kind} detected somewhere in the label — redact before importing"
            )
        if len(issues) == before:
            labels.append(label)  # only clean rows are kept; the caller refuses on any issue
    return labels, issues
