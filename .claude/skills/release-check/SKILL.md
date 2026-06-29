---
name: release-check
description: Pre-release checklist for CompanionBench (gates, smoke run, secrets, version, docs).
---

# Pre-release checklist

Run these **in order**. Stop and fix on the first failure. Everything here is offline and needs no
API keys.

## 1. Install / sync deps

```bash
uv sync --all-extras
```

## 2. Quality gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
```

All four must be clean. (`ruff format --check` only checks — do not auto-format during the release
check; if it fails, fix in a separate change and re-run.)

## 3. Validate + smoke run/score + config checks + build

```bash
uv run companion-bench validate manifests/smoke.yaml
uv run companion-bench providers                              # offline; key presence only
uv run companion-bench models validate --model-set configs/model_sets/example.yaml
uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/smoke
uv run companion-bench score --run runs/smoke
uv build                                                      # wheel + sdist build cleanly
```

Confirm the run completes with no failures and `score` prints sane numbers (empathetic-v1 should
score well — it validates the pipeline, not model quality). `uv build` must succeed and include the
bundled `config/data/pricing.yaml`.

## 4. Confirm NO secrets are committed

- `.env` is gitignored (and `.env.*` except `.env.example`); only `.env.example`, with blank values,
  should be tracked.
- Grep the tree for accidental keys:
  ```bash
  grep -rnE 'sk-[A-Za-z0-9]{16,}|sk-ant-|sk-or-|api[_-]?key\s*[:=]\s*["'"'"']?[A-Za-z0-9]{16,}' \
    --exclude-dir=.git --exclude-dir=.venv --exclude-dir=runs .
  ```
  Any hit that is a real key is a blocker. `.env.example` must contain only empty values.
- The secret-leak test must pass (it runs a benchmark with a fake key set and scans every
  artifact): `uv run pytest tests/test_secrets.py -q`.
- If you produced any LIVE run artifacts, scan them before committing (and prefer NOT to commit
  live artifacts at all — only sanitized samples):
  ```bash
  uv run python -c "import os,sys; from companion_bench.utils.secrets import collect_secret_values, scan_run_dir; \
    leaks=scan_run_dir(sys.argv[1], collect_secret_values()); print('LEAKS:', leaks); sys.exit(1 if leaks else 0)" runs/<dir>
  ```

## 5. Confirm the version is bumped (both files must match)

- `pyproject.toml` -> `[project] version = "X.Y.Z"`
- `src/companion_bench/__init__.py` -> `__version__ = "X.Y.Z"`

```bash
grep -nE '^version' pyproject.toml
grep -n '__version__' src/companion_bench/__init__.py
uv run companion-bench version          # prints the installed __version__
```

The two strings must be identical and greater than the last release.

## 6. Confirm the README quickstart still matches the CLI

Re-read the Quickstart in `README.md` and confirm every command and flag still exists and the listed
run artifacts are accurate. The CLI is the source of truth:

```bash
uv run companion-bench --help
```

Cross-check command names (`validate`, `run`, `score`, `report`, `export`, `list-tasks`,
`providers`, `models validate`, `version`), the run flags (`--manifest`, `--model`,
`--model-set`, `--out`, `--live`, `--yes`, `--limit-tasks`, `--limit-models`, `--max-cost-usd`,
`--pricing`, `--providers-config`, `--seed`, `--concurrency`, `--run-id`), and the documented
artifacts (`events.jsonl`, `run.json`, `scores.json`, `summary.md`, `export/`, and
`modelset.json` for model-set runs).

## Checklist

- [ ] `uv sync --all-extras` clean.
- [ ] ruff check, ruff format --check, mypy, pytest all green (default pytest is offline; live
      tests are skipped without `COMPANIONBENCH_LIVE=1`).
- [ ] `validate`, `providers`, `models validate` pass; smoke run + score complete with no
      failures; `uv build` succeeds.
- [ ] No real secrets committed; `.env` gitignored; `.env.example` is blanks only; the secret-leak
      test passes and any live artifacts are scanned (or not committed).
- [ ] Version bumped and identical in `pyproject.toml` and `src/companion_bench/__init__.py`.
- [ ] README quickstart matches the actual CLI commands, flags, and artifacts.
