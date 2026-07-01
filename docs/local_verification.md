<!-- SPDX-License-Identifier: Apache-2.0 -->
# Local verification

CompanionBench is **local-first**: the GitHub account hosting this repo has an account-level
Actions billing lock unrelated to the code, so there is no working CI signal right now (see
[`ci-disabled/README.md`](ci-disabled/README.md)). Until that's resolved, **the commands on this
page are the source of truth** for whether a change is safe to merge — they are exactly what the
archived CI workflow ran, so nothing about the quality bar changed, only where it's enforced.

## The full local gate

Run all of these, in order, before committing or opening a PR. All of them are offline and need
no API keys.

```bash
uv sync --all-extras                       # install (incl. export + dev extras)

uv run ruff check .                        # lint
uv run ruff format --check .               # format check (`ruff format .` to fix)
uv run mypy                                 # static types (strict, src/companion_bench only)
uv run pytest -q                            # tests (offline, no keys, no network)

uv run companion-bench validate manifests/smoke.yaml
uv run companion-bench validate manifests/full.yaml
uv run companion-bench validate manifests/heldout.yaml

uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/local-check
uv run companion-bench score --run runs/local-check
uv run companion-bench report --run runs/local-check

uv build                                    # confirm the package still builds
```

If you touched provider/model-set config, also run the offline-only parts of provider
verification (no network, no keys):

```bash
uv run companion-bench providers
uv run companion-bench models validate --model-set configs/model_sets/example.yaml
```

## If you touched the task suite

Also run a full mock pass over the public and held-out manifests (this is slower — hundreds of
mock calls, but still offline/instant, no network):

```bash
uv run companion-bench run --manifest manifests/full.yaml --model mock/empathetic-v1 --out runs/full-check
uv run companion-bench score --run runs/full-check
uv run companion-bench run --manifest manifests/heldout.yaml --model mock/intrusive-v1 --out runs/heldout-check
uv run companion-bench score --run runs/heldout-check   # sanity check: safety should be < 1.0 somewhere
```

Never commit anything under `runs/` — it's gitignored on purpose (see
[`SECURITY.md`](../SECURITY.md)).

## Before a public-facing release

Use the packaged skills rather than re-deriving this checklist by hand:

- `.claude/skills/release-check/` — the gate above, plus version/README/build checks.
- `.claude/skills/release-readiness-check/` — extends `release-check` with the quality audit, the
  public-claims guard (`tests/test_public_claims.py`), and sanitized-sample verification. This is
  the one to run before tagging a release. See [`release_checklist.md`](release_checklist.md) for
  the parts that skill doesn't cover (version bump locations, tagging, the push itself).
- `.claude/skills/secret-scan-artifacts/` — run before committing anything derived from a live run.

## Re-enabling CI later

If GitHub Actions billing is resolved, restoring CI is a two-step, no-code-change operation — see
[`ci-disabled/README.md`](ci-disabled/README.md).
