---
name: task-suite-review
description: Suite-wide invariant sweep for CompanionBench's task suite — id uniqueness, safety disjointness, per-family counts, manifest partition correctness, decision-mix sanity. Distinct from judge-rubric-review (single-task rubric quality).
---

# Task suite review

A **suite-wide** sweep, run after any bulk task-authoring pass and before committing. Distinct
from `judge-rubric-review` (which reviews one task's scoring signals for fairness) — this skill
checks structural invariants across the *whole* suite at once.

## 1. Global `task_id` uniqueness

```bash
grep -rh "^task_id:" tasks/ | sed 's/^task_id: *//' | sort | uniq -d
```

Must be empty. `task_id`s share the same `<family>-<slug>` convention across public and held-out,
so check uniqueness across both splits together, not per-split.

## 2. Per-family counts vs. the test thresholds

```bash
find tasks -name '*.yaml' | grep -v heldout | sed 's#tasks/##;s#/.*##' | sort | uniq -c
find tasks -path '*/heldout/*.yaml' | sed 's#tasks/##;s#/heldout.*##' | sort | uniq -c
```

Compare against `MIN_PUBLIC_PER_FAMILY` / `MIN_HELDOUT_PER_FAMILY` in
`tests/test_task_suite.py` — if the suite grew, the constants should reflect the real achieved
counts (never left stale-and-passing-by-accident below what's actually on disk).

## 3. Manifest partition correctness

```bash
uv run companion-bench validate manifests/full.yaml
uv run companion-bench validate manifests/heldout.yaml
```

`full.yaml` (`tasks/*/*.yaml`, non-recursive) must never pick up a `heldout/` file;
`heldout.yaml` (`tasks/*/heldout/*.yaml`) must contain only held-out files. The reported family
counts in each command's output are the ground truth — cross-check against step 2.

## 4. Safety disjointness (the invariant that isn't obvious from a schema check alone)

```bash
uv run pytest tests/test_signal_disjointness.py -q
```

No task's own `positive_signals`/`expected_target_keywords` may regex-match inside any of that
same task's `safety_boundaries[].forbidden_patterns` — otherwise the *correct* mock persona
(`empathetic-v1`) trips its own safety check by giving the right answer. See the test's docstring
for the exact mechanism.

## 5. Decision-mix and regression sanity

```bash
uv run pytest tests/test_task_suite.py tests/test_safety_audit.py tests/test_regression_personas.py tests/test_selection.py -q
```

Covers: every family present in `full.yaml`; every task has `expected_abstention_behavior` +
`metadata.failure_modes`; every `safety`-family task has non-empty `safety_boundaries`; held-out
is disjoint from and excluded from public; safety is not saturated at 1.0 for a bad persona;
always-silent/always-intrusive/generic-empathy mocks score worse than the good persona;
family-balanced sampling is deterministic.

## 6. Empirical confirmation (belt-and-suspenders beyond the static checks above)

```bash
uv run companion-bench run --manifest manifests/full.yaml --model mock/empathetic-v1 --out runs/_review-empathetic
uv run companion-bench score --run runs/_review-empathetic   # expect overall == 1.000
uv run companion-bench run --manifest manifests/heldout.yaml --model mock/intrusive-v1 --out runs/_review-intrusive
uv run companion-bench score --run runs/_review-intrusive    # expect most tasks to FAIL, safety well below 1.0
```

If `empathetic-v1` doesn't hit 1.000 somewhere, a newly-authored task likely has a schema/signal
mismatch with its own answer key. If `intrusive-v1` passes too many tasks or safety looks
saturated, the suite has gotten weaker at catching bad behavior, not stronger. Don't commit
`runs/_review-*` — it's gitignored.

## When to run this

After every bulk task-authoring pass (a new family, an expansion, a held-out top-up), before the
commit that adds the new task files.
