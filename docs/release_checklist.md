<!-- SPDX-License-Identifier: Apache-2.0 -->
# Release checklist

This page is deliberately thin — the actual gate lives in the `release-readiness-check` project
skill so there's one place to update it. This page covers the two things that skill doesn't:
**where version numbers live** and **the tag/push sequence**.

## 1. Run the gate

```
Skill: .claude/skills/release-readiness-check/
```

This runs the full local gate (`release-check`: ruff/format/mypy/pytest/build, offline manifest
validation + smoke run/score, secret hygiene, README-vs-CLI parity), plus the public-facing layer:
the public-claims guard (`tests/test_public_claims.py`), confirming
[`docs/audits/`](audits/) reflects the current state, and confirming every directory under
[`docs/samples/`](samples/) is still sanitized (no `events.jsonl`, no `run.json`, no raw
transcripts). Don't tag a release until this skill's checklist is fully green.

Also run the quality gates and read their output before tagging:

```bash
uv run companion-bench validate manifests/full.yaml --strict-quality   # suite invariants (0 errors)
uv run companion-bench quality status                                  # external-validation snapshot
```

`quality status` prints the warnings that constrain public claims — e.g. it will say the committed
labels are a synthetic pilot until a real annotation round is imported, so keep release notes scoped
(human validation is a future milestone). Keep the scorecard
([`docs/audits/benchmark_quality_scorecard.md`](audits/benchmark_quality_scorecard.md) + its `.json`)
in sync with the shipped state.

## 2. Where version numbers live (keep these in sync)

| Location | Current value | Notes |
| --- | --- | --- |
| `pyproject.toml` → `[project] version` | `0.1.0` | The installed package version (PEP 440 — no `-alpha` suffix here). |
| `CITATION.cff` → `version` | `0.1.0-alpha` | Deliberately a distinct, more descriptive label than the package version — this is what a paper/README citation should reference. |
| `CHANGELOG.md` | `## [0.1.0-alpha] - YYYY-MM-DD` | Keep-a-Changelog format; one entry per release. |

When cutting a release, bump `pyproject.toml`'s version, add a new `CHANGELOG.md` entry, and update
`CITATION.cff`'s `version`/`date-released` together, in the same commit.

## 3. Tag and push

```bash
git tag -a v0.1.0-alpha -m "CompanionBench v0.1.0-alpha"
git push origin main
git push origin v0.1.0-alpha
```

Use an annotated tag (`-a`) so it carries a message and date. Never force-push a tag that's
already been pushed — cut a new one instead if something was wrong.

## 4. After tagging

Re-run `uv run companion-bench version` and confirm it reports the tagged version, and skim
`docs/local_verification.md` once more against a truly clean checkout (`git clone` into a scratch
directory) to catch anything that only worked because of local, uncommitted state.
