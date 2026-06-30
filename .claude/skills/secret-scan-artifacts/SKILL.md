---
name: secret-scan-artifacts
description: Scan the repo and run artifacts for leaked API keys / auth headers before committing (utils.secrets value-scan + regex shape-grep + .env hygiene).
---

# Secret-scan artifacts

Run before committing anything — **especially** after a live run. Two complementary scans.

## 1. Value scan (exact, seeded from the live environment)

Catches the *actual* secret values currently in the environment (incl. a loaded `.env`):

```bash
uv run python -c "import sys; from companion_bench.utils.secrets import collect_secret_values, scan_run_dir; \
  leaks = scan_run_dir(sys.argv[1], collect_secret_values()); print('LEAKS:', leaks); sys.exit(1 if leaks else 0)" runs/<dir>
```

`LEAKS: {}` and exit 0 => clean. (`scan_paths_for_secrets` does the same for an arbitrary file list.)

## 2. Pattern grep (shape-based, catches keys not in the current env)

```bash
grep -rnE 'sk-or-[A-Za-z0-9]|sk-ant-|sk-[A-Za-z0-9]{16,}|Bearer [A-Za-z0-9]|x-api-key' \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=runs .
```

Expected hits are only the **fake** fixtures in `tests/test_secrets.py` / `tests/test_providers.py`
(they prove redaction). Any other hit is a blocker.

## 3. `.env` hygiene

- `.env` and `.env.*` gitignored; only `.env.example` (blank values) is tracked.
- Never commit raw `events.jsonl` (full transcripts) — sanitized samples only.

## If a real secret is found

**Stop. Do not commit. Rotate the key. Never print it.** Then re-scan until clean.
