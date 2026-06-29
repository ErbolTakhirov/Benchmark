---
name: run-smoke-benchmark
description: Run the CompanionBench smoke benchmark end to end (validate, run, score, export).
---

# Run the smoke benchmark end to end

The smoke benchmark is 8 tasks (2 per family) exercising every code path and scoring dimension. It
runs fully offline against the deterministic mock model — **no API keys, no network**.

## Commands (in order)

```bash
# 0. (first time) install deps, including the optional export extra
uv sync --all-extras

# 1. Validate the manifest and every task it references
uv run companion-bench validate manifests/smoke.yaml

# 2. Run against the deterministic mock model
uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/smoke

# 3. Score the run (rule-based, transparent, deterministic)
uv run companion-bench score --run runs/smoke

# 4. (optional) Export raw events + scores to Parquet
uv run companion-bench export --run runs/smoke --format parquet
```

Both `companion-bench <cmd>` and `uv run python -m companion_bench.cli <cmd>` work. Useful `run`
flags: `--seed`, `--limit N` (first N tasks), `--run-id`, `--concurrency N`.

## Artifacts produced under the run dir (`runs/smoke/`)

- `events.jsonl` — raw, append-only events (every model call with token/cost/latency, plus failures)
- `run.json` — run metadata (run id, manifest path, model, config, resolved task list)
- `scores.json` — per-dimension and aggregate scores
- `summary.md` — human-readable summary table
- `export/*.parquet` — `events.parquet` and `task_scores.parquet` (only after `export`)

`runs/` and `*.parquet` are gitignored — they are regenerated, not committed.

## The three mock profiles

Pass any of these as `--model mock/<profile>`:

- `mock/empathetic-v1` — the default, the "good" companion (intervenes well, attunes, abstains, asks
  permission).
- `mock/intrusive-v1` — over-intervenes bluntly, ignores feedback, crosses boundaries.
- `mock/silent-v1` — always waits; misses moments and never abstains.

**Important framing:** the mock is a deterministic *simulator* that reads a `simulation_context`
channel which real provider adapters ignore entirely. So **mock scores validate the PIPELINE, not
model quality** — they prove the run/score/export loop works and produce reproducible artifacts, not
that one model is better than another.

## Compare profiles

Run each profile into its own `--out` dir, then score:

```bash
for p in empathetic-v1 intrusive-v1 silent-v1; do
  uv run companion-bench run --manifest manifests/smoke.yaml --model mock/$p --out runs/$p
  uv run companion-bench score --run runs/$p
done
```

Expected ordering (a smoke check that scoring works): **empathetic-v1 high, intrusive-v1 low,
silent-v1 middling**. Compare `runs/<profile>/summary.md` or the overall score printed by `score`.
