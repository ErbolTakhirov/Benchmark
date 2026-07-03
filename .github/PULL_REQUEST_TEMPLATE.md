<!-- Thanks for contributing to CompanionBench! There is no hosted CI right now
     (see docs/ci-disabled/ and docs/ci_alternative.md) — local verification is the source of truth. -->

## Summary
<!-- What changed and why. Link the issue it closes. -->

## Local gate (all must pass — see docs/local_verification.md)
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy`
- [ ] `uv run pytest -q`
- [ ] `uv build`
- [ ] `uv run companion-bench validate manifests/full.yaml --strict-quality` (if tasks/scoring changed)

## Safety / hygiene
- [ ] No secrets, `.env`, raw `runs/`, `*.parquet`, or private annotation files staged
- [ ] Result wording stays scoped to the evaluated tasks / settings / model versions, with model set + provider as run metadata (see `docs/public_claims.md`)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Scoring semantics changed? bumped `SCORING_VERSION` and noted cross-version comparability
