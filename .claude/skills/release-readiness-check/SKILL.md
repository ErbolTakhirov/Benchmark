---
name: release-readiness-check
description: Public-release readiness gate for CompanionBench — extends release-check with the quality audit, the public-claims guard, and sanitized-sample verification.
---

# Release readiness check

Builds on [release-check](../release-check/SKILL.md) for a **public-facing** release. Run in order;
stop and fix on the first failure.

## 1. Full release-check

Gates (ruff/format/mypy/pytest/build), offline smoke run+score, secret hygiene, version bump,
README-vs-CLI parity — per [release-check](../release-check/SKILL.md).

## 2. Public-claims guard (framing)

```bash
uv run pytest tests/test_public_claims.py -q
```

No "EMOTomo benchmark" / "OpenRouter benchmark" framing in public docs; results are described as a
**sample run, not a leaderboard**, per [`public_claims.md`](../../docs/public_claims.md).

## 3. Quality audit is current

[`docs/audits/benchmark_quality_audit.md`](../../docs/audits/benchmark_quality_audit.md) reflects the
current verdict on the ladder and an up-to-date top-10 fix list.

## 4. Samples are sanitized

Every `docs/samples/**` dir contains only `README` + `summary.md` + `scores.json` + `modelset.json`
+ `frontier.*` — **no** raw `events.jsonl` — and is clearly marked "sample run, not a leaderboard".

## 5. Secret-scan everything to be committed

Run skill **secret-scan-artifacts** over the repo, `docs/samples`, and `configs`. Must be empty
(besides the known fake test fixtures). Never commit `.env` or `runs/`.

## Checklist

- [ ] release-check fully green.
- [ ] `tests/test_public_claims.py` passes; no overclaiming in docs/README.
- [ ] audit doc current (verdict + top-10).
- [ ] samples sanitized (no `events.jsonl`); each marked a sample, not a leaderboard.
- [ ] secret scan empty; no `.env` / `runs/` / keys staged.
