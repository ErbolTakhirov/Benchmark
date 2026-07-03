<!-- SPDX-License-Identifier: Apache-2.0 -->
# Design: Resume / checkpoint for long runs (deferred)

**Status: design only.** Not implemented in v0.1.0-alpha. This documents the intended approach and
why it is deferred, so a future implementation does not have to rediscover the constraints. The
`run` command is unchanged.

## Problem

A large live run (e.g. 10 models × 150 tasks × 5 repeats) can be interrupted — a transient provider
outage, a budget cap, a laptop sleep. Today an interrupted run must restart from zero, re-spending
tokens on probes already completed. We want to resume from where it stopped.

## Why it is not free

The engine's headline property is **byte-stable, deterministic artifacts** (`events.jsonl` written
in a fixed repeat→task→probe order with sequentially assigned ids; verified by
`tests/test_runner_smoke.py::test_run_is_byte_stable_with_frozen_clock`). A naive resume that
appends new events to a partial file, or re-numbers ids on the second pass, breaks that guarantee
and makes runs non-comparable. Resume must preserve determinism, not trade it away.

## Proposed approach

1. **Checkpoint unit = `(task_id, probe_id, repeat_index)`.** The natural completion key; probes
   within a task are sequential, so a task resumes at its first incomplete probe.
2. **Checkpoint source of truth = the existing `events.jsonl`.** On `--resume`, read the partial
   `events.jsonl` (if present), build the set of completed `(task, probe, repeat)` keys from
   `ModelCallEvent` / `ModelFailureEvent`, and skip those probes. No new sidecar file is required;
   the canonical raw artifact already records exactly what finished.
3. **Deterministic re-assembly.** Keep the current design of collecting events per task and writing
   them in fixed order. On resume, merge completed events with newly produced ones, then **re-emit
   the whole file in canonical order with freshly assigned ids** — so a resumed run is byte-identical
   to an uninterrupted one with the same seed. (Ids are run-local and derived from `IdFactory`, so
   re-assignment is safe.)
4. **Retry/backoff seeding is unchanged.** Backoff jitter is already seeded per
   `(task, probe, attempt)` (`runner/retry.py`), so a resumed probe retries identically.
5. **Cost accounting.** Re-sum cost/tokens from the merged event set rather than carrying a running
   total across the interruption, so the budget guard stays correct after resume.
6. **CLI surface.** `run ... --resume` (opt-in). Absent the flag, behavior is exactly as today.

## Determinism test plan (when implemented)

- Run N probes, kill mid-way, resume → final `events.jsonl` is **byte-identical** to an
  uninterrupted run at the same seed (extends the existing byte-stability test).
- A completed-then-resumed run issues **zero** new model calls (all keys already present).
- Budget/cost totals after resume equal the uninterrupted totals.

## Why deferred for v0.1.0-alpha

The offline pipeline does not need it, and getting the byte-stability interaction wrong would
regress a load-bearing guarantee. It is a **P1** item (see
[`analysis/quality_improvement_backlog.md`](../../analysis/quality_improvement_backlog.md)) to
implement with the determinism tests above, not a rushed addition.
