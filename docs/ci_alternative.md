<!-- SPDX-License-Identifier: Apache-2.0 -->
# CI alternative (while GitHub Actions is disabled)

CompanionBench has **no hosted CI right now** — the account has an Actions billing lock unrelated to
this repo (see [`ci-disabled/`](ci-disabled/)). Until Actions is re-enabled, **local verification is
the source of truth** ([`local_verification.md`](local_verification.md)). This page documents how to
make that local gate hard to skip, so quality does not depend on remembering to run it.

> This repo deliberately ships **no** `.github/workflows/` file. Adding one could trigger the
> account's Actions billing — don't, until that's resolved.

## The gate (run before every push)

```bash
uv sync --all-extras
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
uv build
uv run companion-bench validate manifests/full.yaml --strict-quality   # if tasks/scoring changed
```

These are the same checks a CI job would run. The `release-check` / `release-readiness-check` project
skills wrap them for releases.

## Make it automatic with a local pre-commit / pre-push hook

Option A — a git hook you can drop in (no extra dependency). Save as `.git/hooks/pre-push`, `chmod +x`:

```bash
#!/usr/bin/env bash
set -euo pipefail
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
# Block the classic footguns before they leave your machine:
if git diff --cached --name-only | grep -qE '(^|/)\.env$|^runs/|\.parquet$|events\.jsonl$'; then
  echo "refusing to push: raw runs / .env / events.jsonl staged" >&2
  exit 1
fi
```

Option B — [`pre-commit`](https://pre-commit.com/) framework. A `.pre-commit-config.yaml` using the
local hooks above works the same way; it is **not** installed by default so contributors opt in.

## When Actions returns

Restore the archived workflow from [`ci-disabled/ci.yml.txt`](ci-disabled/) into
`.github/workflows/ci.yml`, confirm it runs the gate above, and delete this page's "no workflows"
caveat. Until then, the local gate + the hook are the substitute.
