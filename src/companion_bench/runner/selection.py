"""Deterministic task selection for a run.

The old behavior — ``tasks[:limit]`` over the alphabetically-sorted list — picked only the
first family (e.g. all ``adaptation``). This selects a **family-balanced** subset instead
(round-robin across families), and supports a reproducible shuffle. All ordering is
deterministic given ``shuffle_seed``.
"""

from __future__ import annotations

import random
from collections import OrderedDict

from companion_bench.schemas.task import Family, Task

__all__ = ["select_tasks"]


def select_tasks(
    tasks: list[Task],
    *,
    limit: int | None = None,
    family_balanced: bool = False,
    shuffle_seed: int | None = None,
) -> list[Task]:
    """Pick a deterministic subset of ``tasks``.

    - ``shuffle_seed`` set → reproducibly shuffle before selecting (else keep load order).
    - ``family_balanced`` → round-robin across families so a small ``limit`` spans families.
    - otherwise → the first ``limit`` of the (possibly shuffled) order.
    """
    ordered = list(tasks)
    if shuffle_seed is not None:
        ordered = ordered[:]
        random.Random(shuffle_seed).shuffle(ordered)
    if limit is None or limit >= len(ordered):
        return ordered
    if family_balanced:
        return _round_robin(ordered, limit)
    return ordered[:limit]


def _round_robin(ordered: list[Task], limit: int) -> list[Task]:
    """One task from each family in turn (families in enum order), preserving inner order."""
    groups: OrderedDict[Family, list[Task]] = OrderedDict()
    for task in ordered:
        groups.setdefault(task.family, []).append(task)
    family_order = sorted(groups, key=lambda f: f.value)
    queues = {f: list(groups[f]) for f in family_order}
    out: list[Task] = []
    while len(out) < limit and any(queues.values()):
        for family in family_order:
            if queues[family]:
                out.append(queues[family].pop(0))
                if len(out) >= limit:
                    break
    return out
