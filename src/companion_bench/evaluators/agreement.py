"""Inter-rater agreement metrics for human gold labels (stdlib only, offline).

Why these exist: a gold set is only trustworthy if annotators agree with *each other*. Low
agreement means the dimension is ambiguous or the rubric is underspecified — a finding about the
benchmark, not the models. We report several complementary views because each has blind spots:

- **percent agreement** — intuitive but ignores chance; inflated when one category dominates.
- **Cohen's kappa** — chance-corrected, but only for exactly two annotators, nominal.
- **Krippendorff's alpha** — handles any number of annotators, missing data, and nominal *or*
  ordinal scales (the right tool for 1-5 Likert dimensions with skipped cells).
- **Pearson/Spearman** — linear / rank correlation of two annotators' numeric ratings.

None is "the" number; read them together with the missingness report.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from companion_bench.schemas.gold import GoldLabel
from companion_bench.schemas.task import Dimension

__all__ = [
    "AgreementReport",
    "DimensionAgreement",
    "OverallAgreement",
    "cohens_kappa",
    "compute_agreement",
    "krippendorff_alpha",
    "pearson",
    "percent_agreement",
    "spearman",
]

# Below this, alpha is conventionally "unreliable" — worth a loud warning in a pilot.
_LOW_ALPHA = 0.667


# --------------------------------------------------------------------------- primitive metrics
def percent_agreement(units: Sequence[Sequence[object]]) -> float | None:
    """Mean over units of the fraction of *agreeing annotator pairs* (chance-uncorrected).

    ``units`` is one list of annotator values per item; values may repeat. Items with < 2 values
    are skipped. Returns ``None`` if no item has a comparable pair.
    """
    ratios: list[float] = []
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        pairs = m * (m - 1) / 2
        agree = sum(c * (c - 1) / 2 for c in Counter(vals).values())
        ratios.append(agree / pairs)
    return sum(ratios) / len(ratios) if ratios else None


def cohens_kappa(pairs: list[tuple[object, object]]) -> float | None:
    """Cohen's kappa for two annotators over aligned ``(a, b)`` category pairs."""
    n = len(pairs)
    if n == 0:
        return None
    po = sum(1 for a, b in pairs if a == b) / n
    a_counts = Counter(a for a, _ in pairs)
    b_counts = Counter(b for _, b in pairs)
    pe = sum((a_counts[c] / n) * (b_counts[c] / n) for c in set(a_counts) | set(b_counts))
    if pe >= 1.0:
        return 1.0 if po >= 1.0 else 0.0
    return (po - pe) / (1 - pe)


def _delta_sq(
    c: object, k: object, level: str, order: list[object], marg: dict[object, float]
) -> float:
    if c == k:
        return 0.0
    if level == "nominal":
        return 1.0
    # ordinal metric: squared distance uses marginals of the values lying between c and k.
    i, j = order.index(c), order.index(k)
    lo, hi = (i, j) if i < j else (j, i)
    between = sum(marg[order[g]] for g in range(lo, hi + 1))
    return (between - (marg[c] + marg[k]) / 2.0) ** 2


def krippendorff_alpha(units: Sequence[Sequence[object]], level: str = "nominal") -> float | None:
    """Krippendorff's alpha over reliability data (``level`` = ``"nominal"`` or ``"ordinal"``).

    Each unit is the list of values assigned by annotators (missing cells simply omitted). Units
    with < 2 values do not contribute pairs. Returns ``None`` if there is no pairable data;
    ``1.0`` for perfect agreement. Ordinal treats the values as an ordered scale.
    """
    # Coincidence matrix o[(c, k)] from within-unit ordered pairs, weighted by 1/(m-1).
    o: dict[tuple[object, object], float] = defaultdict(float)
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[(vals[i], vals[j])] += 1.0 / (m - 1)
    if not o:
        return None
    values = sorted({c for c, _ in o}, key=_sort_key)
    marg = {c: sum(o[(c, k)] for k in values if (c, k) in o) for c in values}
    n = sum(marg.values())
    if n <= 1:
        return None
    num = sum(o[(c, k)] * _delta_sq(c, k, level, values, marg) for (c, k) in o)
    den = sum(
        marg[c] * marg[k] * _delta_sq(c, k, level, values, marg) for c in values for k in values
    )
    if den == 0:
        # No expected disagreement (all one value) -> perfect agreement by convention.
        return 1.0
    return 1.0 - (n - 1) * (num / den)


def _sort_key(v: object) -> tuple[int, object]:
    # Sort numbers numerically, everything else by string — keeps ordinal order sane.
    if isinstance(v, (int, float)):
        return (0, v)
    return (1, str(v))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def _ranks(vals: list[float]) -> list[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return pearson(_ranks(xs), _ranks(ys))


# --------------------------------------------------------------------------- report
@dataclass(frozen=True)
class DimensionAgreement:
    dimension: Dimension
    n_items: int
    alpha_ordinal: float | None
    pearson: float | None
    spearman: float | None
    missing_frac: float


@dataclass(frozen=True)
class OverallAgreement:
    n_items: int
    n_annotators: int
    percent: float | None
    cohens_kappa: float | None
    alpha_nominal: float | None


@dataclass(frozen=True)
class AgreementReport:
    gold_set_id: str
    overall: OverallAgreement
    per_dimension: dict[Dimension, DimensionAgreement]
    warnings: list[str] = field(default_factory=list)


def _item_key(label: GoldLabel) -> tuple[str, str, str]:
    return (label.task_id, label.probe_id, label.response_id)


def compute_agreement(labels: list[GoldLabel]) -> AgreementReport:
    """Group labels by rated item and compute per-dimension + overall agreement."""
    by_item: dict[tuple[str, str, str], list[GoldLabel]] = defaultdict(list)
    for lab in labels:
        by_item[_item_key(lab)].append(lab)
    annotators = {lab.annotator_id_hash for lab in labels}
    gold_set_id = labels[0].gold_set_id if labels else ""
    warnings: list[str] = []

    # --- overall_preference (nominal) ---
    pref_units = [[lab.overall_preference.value for lab in labs] for labs in by_item.values()]
    kappa = _two_annotator_kappa(by_item, annotators)
    overall = OverallAgreement(
        n_items=len(by_item),
        n_annotators=len(annotators),
        percent=percent_agreement(pref_units),
        cohens_kappa=kappa,
        alpha_nominal=krippendorff_alpha(pref_units, "nominal"),
    )
    if len(annotators) < 2:
        warnings.append("Only one annotator: inter-rater agreement is undefined (need >= 2).")
    elif overall.alpha_nominal is not None and overall.alpha_nominal < _LOW_ALPHA:
        warnings.append(
            f"Low overall-preference agreement (nominal alpha={overall.alpha_nominal:.3f} "
            f"< {_LOW_ALPHA}); the accept/reject rubric may be ambiguous."
        )

    # --- per dimension (ordinal 1-5) ---
    per_dim: dict[Dimension, DimensionAgreement] = {}
    for dim in Dimension:
        units: list[list[object]] = []
        cells = missing = 0
        for labs in by_item.values():
            vals: list[object] = []
            for lab in labs:
                cells += 1
                dr = lab.dimensions.get(dim)
                if dr is None or dr.rating is None:
                    missing += 1
                else:
                    vals.append(dr.rating)
            if vals:
                units.append(vals)
        p, s = _two_annotator_corr(by_item, annotators, dim)
        alpha = krippendorff_alpha(units, "ordinal")
        per_dim[dim] = DimensionAgreement(
            dimension=dim,
            n_items=len(units),
            alpha_ordinal=alpha,
            pearson=p,
            spearman=s,
            missing_frac=(missing / cells) if cells else 0.0,
        )
        if alpha is not None and alpha < _LOW_ALPHA and len(annotators) >= 2:
            warnings.append(f"Low agreement on {dim.value} (ordinal alpha={alpha:.3f}).")

    return AgreementReport(gold_set_id, overall, per_dim, warnings)


def _two_annotator_kappa(
    by_item: dict[tuple[str, str, str], list[GoldLabel]], annotators: set[str]
) -> float | None:
    """Cohen's kappa on overall_preference when there are exactly two annotators."""
    if len(annotators) != 2:
        return None
    a, b = sorted(annotators)
    pairs: list[tuple[object, object]] = []
    for labs in by_item.values():
        va = next((x.overall_preference.value for x in labs if x.annotator_id_hash == a), None)
        vb = next((x.overall_preference.value for x in labs if x.annotator_id_hash == b), None)
        if va is not None and vb is not None:
            pairs.append((va, vb))
    return cohens_kappa(pairs)


def _two_annotator_corr(
    by_item: dict[tuple[str, str, str], list[GoldLabel]], annotators: set[str], dim: Dimension
) -> tuple[float | None, float | None]:
    """Pearson/Spearman on a dimension's ratings when there are exactly two annotators."""
    if len(annotators) != 2:
        return None, None
    a, b = sorted(annotators)
    xs: list[float] = []
    ys: list[float] = []
    for labs in by_item.values():
        ra = _rating(labs, a, dim)
        rb = _rating(labs, b, dim)
        if ra is not None and rb is not None:
            xs.append(ra)
            ys.append(rb)
    return pearson(xs, ys), spearman(xs, ys)


def _rating(labs: list[GoldLabel], annotator: str, dim: Dimension) -> float | None:
    for lab in labs:
        if lab.annotator_id_hash == annotator:
            dr = lab.dimensions.get(dim)
            return None if dr is None or dr.rating is None else float(dr.rating)
    return None
