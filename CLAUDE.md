# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## What this is

**CompanionBench** — an API-first, open-source benchmark for evaluating LLM companions and
proactive assistants across realistic multi-turn conversations. It jointly measures initiative
relevance, intervention timing, emotional attunement, preference adaptation, abstention, and
safety. See [`README.md`](README.md) and [`docs/`](docs/).

Status: **MVP scaffold (v0.1).** The pipeline runs end-to-end offline against a deterministic
mock model. Real provider adapters are interface-complete; LLM-as-judge and human eval are next.

## Commands

```bash
uv sync --all-extras                       # install (incl. export + dev extras)

uv run ruff check .                        # lint
uv run ruff format --check .               # format check (use `ruff format .` to fix)
uv run mypy                                 # static types (strict, src only)
uv run pytest -q                            # tests (offline, no keys)

# Benchmark pipeline (offline mock):
uv run companion-bench validate manifests/smoke.yaml
uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/smoke
uv run companion-bench score --run runs/smoke
uv run companion-bench report --run runs/smoke              # show scores (single or model-set)
uv run companion-bench export --run runs/smoke --format parquet
uv run companion-bench list-tasks manifests/smoke.yaml

# Providers + model sets (offline checks):
uv run companion-bench providers                            # key presence (never values) + base URLs
uv run companion-bench models validate --model-set configs/model_sets/example.yaml
uv run companion-bench run -m manifests/smoke.yaml --model-set configs/model_sets/mock-profiles.yaml --out runs/multi

# Real providers (LIVE, opt-in): needs --live AND COMPANIONBENCH_LIVE=1 (+ a key, + --yes/confirm)
# COMPANIONBENCH_LIVE=1 companion-bench run -m manifests/smoke.yaml --model-set <set> --out runs/live --live --yes --max-cost-usd 1 --limit-tasks 2 --limit-models 2
```

Both `companion-bench <cmd>` and `uv run python -m companion_bench.cli <cmd>` work.

## Architecture (one-liner per layer)

- `schemas/` — Pydantic v2 models; dependency order `model → task → score` (and `model → run`).
- `adapters/` — `ChatAdapter` ABC + registry; `mock` (deterministic simulator) + real HTTPX
  adapters (`openai_compatible`, `openai`, `anthropic`, `openrouter`).
- `runner/` — `manifest` (load/validate/resolve), `conversation` (scripted replay → requests),
  `engine` (async, bounded concurrency, retries, failure capture), `events` (builders).
- `evaluators/` — `rule_based` (6 dimension scorers), `aggregate` (rollups + summary), `rubric`
  (future LLM-judge interface, intentionally not implemented).
- `storage/` — `jsonl` (append-only events + JSON helpers), `export` (optional Parquet).
- `config/` — versioned YAML config: `pricing` (cost table), `providers` (per-provider
  overrides), `model_sets` (which models to run). Bundled defaults in `config/data/`.
- `utils/` — `ids`, `timing` (Clock/FrozenClock), `errors`, `secrets` (redact/scan).

Full notes: [`docs/architecture.md`](docs/architecture.md). Scoring: [`docs/scoring.md`](docs/scoring.md).
Live runs / cost / retries / secrets: [`docs/live_and_cost.md`](docs/live_and_cost.md).

## Core rules (do not break)

- **Python 3.12+**, **uv** for deps, **Typer** CLI, **Pydantic v2**, **HTTPX** async, **pytest**,
  **ruff**, **mypy**.
- **No real API keys in tests.** All provider tests use `httpx.MockTransport` or the mock
  adapter. **Never commit secrets;** `.env` is gitignored; keep `.env.example` keyless. Keys are
  resolved **only** from env vars and must never reach an artifact (a test proves this).
- **Live calls are opt-in:** a real-provider run requires `--live` AND `COMPANIONBENCH_LIVE=1`
  (+ confirmation unless `--yes`). Tests marked `@pytest.mark.live` are skipped unless
  `COMPANIONBENCH_LIVE=1`; default `pytest -q` and CI stay offline + keyless.
- **Cost is null when unknown** (no price entry or no usage) — never invented. `--max-cost-usd`
  is a best-effort global budget; pair with `--limit-tasks`/`--limit-models` for hard caps.
- **Retry backoff is deterministic** (jitter seeded per task/probe/attempt); inject the sleeper
  in tests — never sleep for real in a test.
- **JSONL is the canonical raw artifact** (`events.jsonl`, append-only). Parquet/DuckDB export
  is optional (the `export` extra) and must not be required by the core loop.
- **Failed provider calls are logged as `model_failure` events, never silently hidden.**
- **Every task is versioned + schema-validated** and must declare `expected_abstention_behavior`
  and explicit failure modes.
- **Outputs preserve** raw transcripts, model/provider metadata, and token/cost/latency when
  available; missing values stay `null` (never invented).
- **Determinism:** the engine takes an injectable `Clock`; mock runs are byte-stable under
  `FrozenClock`. Don't introduce wall-clock/random nondeterminism into scored paths.
- **The mock is a simulator.** It reads `ChatRequest.simulation_context`; real adapters must
  ignore that field. Mock scores validate the pipeline, not model quality — say so in docs.
- Keep code **modular, typed, and clean**; match the surrounding style.

## Quality gates (must all pass before commit/PR)

1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run mypy`
4. `uv run pytest -q`
5. `uv run companion-bench validate manifests/smoke.yaml`
6. smoke `run` + `score` succeed offline

CI (`.github/workflows/ci.yml`) runs all of these on Python 3.12 and 3.13.

## Conventions

- `__all__` is kept isort-sorted (ruff RUF022 enforces it).
- Pydantic models use `ConfigDict(extra="forbid")`; value objects are `frozen=True`.
  `CompanionTurn` uses `extra="ignore"` so messy real-model JSON still parses.
- SPDX/Apache-2.0 project; add a `NOTICE` entry for substantial third-party inclusions.
- Commit messages: conventional prefixes (`feat`, `fix`, `chore`, `docs`, `test`). Commit in
  logical chunks; run the gates first.

## Adding things

- **Provider:** implement `ChatAdapter.generate`, register with `@register_adapter`, add env
  vars to `.env.example`, add a MockTransport test. Skill: `add-provider`. Doc:
  [`docs/provider_adapters.md`](docs/provider_adapters.md).
- **Task / family:** add a YAML task (+ `Family` enum and family default weights if new) and
  reference it from a manifest. Skill: `add-task-family`. Doc:
  [`docs/task_authoring.md`](docs/task_authoring.md).
- **Scorer:** implement `RubricEvaluator` in `evaluators/rubric.py`. See `docs/benchmark_card.md`
  for the LLM-judge risks and the human-eval plan.

Project skills live in `.claude/skills/`: `add-provider`, `add-task-family`,
`run-smoke-benchmark`, `release-check`, `judge-rubric-review`.

## Gotchas

- Manifest task globs resolve relative to the manifest's directory and may use `..`; resolution
  uses the stdlib `glob` module (not `Path.glob`) for that reason.
- `score` reloads tasks from the **absolute** `manifest_path` stored in `run.json`, so runs are
  scorable regardless of CWD.
- Typer `Option`/`Argument` defaults are whitelisted for ruff B008 in `pyproject.toml`.
