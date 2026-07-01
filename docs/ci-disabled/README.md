<!-- SPDX-License-Identifier: Apache-2.0 -->
# GitHub Actions — disabled reference, not an active workflow

This directory holds an **inert text archive** of the GitHub Actions CI workflow that previously
lived at `.github/workflows/ci.yml`. It is **not** picked up by GitHub (the file extension is
`.txt`, and nothing under `docs/` is treated as a workflow) — it exists purely so the exact steps
are not lost.

## Why CI was removed

The GitHub account hosting this repository currently has an **account-level billing lock** on
Actions minutes, unrelated to this repository's code or configuration. Rather than leave a
workflow file that will only ever show a red/blocked status, the workflow was deleted and this
repository is **local-first**: local verification is the source of truth until Actions billing is
resolved. See [`../local_verification.md`](../local_verification.md) for the exact command
sequence a contributor should run before opening a PR — it mirrors the archived workflow below
step for step, so nothing about the *quality bar* changed, only *where* it's enforced.

## Re-enabling later

If/when Actions billing is available again, restore CI by:

1. `mkdir -p .github/workflows`
2. Copy [`ci.yml.txt`](ci.yml.txt) to `.github/workflows/ci.yml` (the content is unchanged and
   was working before removal — it ran offline/mocked with no secrets required).
3. Commit and push; GitHub will pick it up automatically on the next push/PR.

No other repository changes are needed to re-enable it — this was a clean removal, not a
placeholder or a stub.

## Archived file

[`ci.yml.txt`](ci.yml.txt) — verbatim copy of the last working `.github/workflows/ci.yml` (matrix
Python 3.12/3.13; `uv sync` → ruff lint/format → mypy → pytest → manifest validate → offline
providers/model-set validation → offline mock smoke run → score → parquet export). It required no
secrets and made no network calls.
