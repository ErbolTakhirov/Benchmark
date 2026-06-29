# Live runs, cost, retries, and secrets

Sprint 2 makes the API track real and safe. This page covers the live-run guardrails, cost
tracking, retry/backoff, provider/pricing config, and secret handling. **The default
experience is still fully offline** against the mock.

## Live runs are opt-in (two gates + a confirmation)

Any run that touches a real provider requires **both**:

1. `--live` on the `run` command, and
2. `COMPANIONBENCH_LIVE=1` in the environment.

…and, unless you pass `--yes`, an interactive confirmation. Mock runs need none of this.

```bash
export OPENROUTER_API_KEY=...           # key comes ONLY from the environment
export COMPANIONBENCH_LIVE=1            # opt in to live network calls
companion-bench run -m manifests/smoke.yaml \
  --model-set configs/model_sets/your-set.yaml \
  --out runs/live --live --yes \
  --limit-tasks 2 --limit-models 2 --max-cost-usd 1
```

Check what's configured (never prints key values) and optionally send one tiny live probe:

```bash
companion-bench providers                 # table of providers + key presence + base URLs
companion-bench providers --probe         # one tiny LIVE call each (needs COMPANIONBENCH_LIVE=1)
companion-bench providers --probe --probe-model openrouter/openai/gpt-4o-mini
```

## Model sets

A **model set** decouples *which models* from *which tasks* (the manifest). Run a manifest
against every enabled model in a set:

```bash
companion-bench models validate --model-set configs/model_sets/your-set.yaml
companion-bench run -m manifests/smoke.yaml --model-set ... --out runs/multi --live --yes
companion-bench score  --run runs/multi      # scores every sub-run
companion-bench report --run runs/multi      # model-comparison table
```

A model-set run writes per-model sub-runs under `runs/multi/<provider-model-slug>/` plus a
`modelset.json` index. `score`/`report` understand both single-run and model-set layouts.
See [`task_authoring.md`](task_authoring.md) for tasks; model-set fields: `set_id`,
`description`, `models[].{id, provider, model, temperature, max_completion_tokens, enabled,
source, notes, needs_mapping}`. `needs_mapping: true` flags a slug you have not yet verified.

## Cost tracking

Costs come from a **versioned pricing table** (`provider/model → USD per 1M input/output`),
with a `source` and `as_of` date per entry. The bundled `config/data/pricing.yaml` is
**illustrative** — supply `--pricing your-pricing.yaml` with current numbers for real
reporting.

- `estimated_cost_usd` is recorded per call when usage **and** a price are known; otherwise it
  stays `null` (never invented).
- `score`/`report` roll cost up per task and per run; `summary.md` shows it.
- `--max-cost-usd` is a **global** budget across all models in a run. It is best-effort: the
  guard stops issuing new calls once spend reaches the cap, but in-flight calls may overshoot
  by up to the concurrency width — pair it with `--limit-tasks`/`--limit-models` for a hard cap.

## Retry & backoff

Retryable provider errors (timeouts, 429, 5xx) are retried with **exponential backoff + full
jitter**, honoring a `Retry-After` header on 429 and a per-request `deadline_s`. The jitter is
seeded per (task, probe, attempt), so retry timing is **deterministic** and reproducible
regardless of concurrency. Knobs live on `RunConfig`: `max_retries`, `base_delay_s`,
`max_delay_s`, `deadline_s`. Each event records `attempts` and total `retry_wait_ms`. An
optional per-provider `requests_per_second` (from `providers.yaml`) rate-limits requests.

## Provider config (`providers.yaml`)

Optional overrides per provider — `base_url`, `default_headers`, `default_params`,
`requests_per_second`. Resolution precedence is **CLI > env > providers.yaml > built-in
default**. The built-in defaults already cover every provider, so this file is only needed for
custom endpoints (e.g. a self-hosted OpenAI-compatible server) or rate limits.

## Secret handling

- **Keys are read only from environment variables** (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
  `OPENROUTER_API_KEY`, `OPENAI_COMPATIBLE_API_KEY`, `HF_TOKEN`) — never from CLI args,
  manifests, or config files.
- Keys are sent **only** in request headers and never written to any artifact
  (`events.jsonl`, `run.json`, `scores.json`, `summary.md`, Parquet) — verified by a test that
  runs with a fake key set and scans every artifact.
- Adapters carry a key-hiding `__repr__`; `companion-bench providers` reports key *presence*,
  never values.
- `companion_bench.utils.secrets` provides `redact()` and `scan_run_dir()` for your own checks;
  the `release-check` skill scans the tree + artifacts before a release.

**Never commit a real `.env` or live-run artifacts containing keys.** `.env` and `runs/` are
gitignored; commit only sanitized sample artifacts.
