---
name: docs-polish
description: Doc-freshness sweep for CompanionBench — stale hardcoded counts, dead repo URLs, broken internal doc/sample links, stale CI references, README/CLI drift.
---

# Docs polish

A doc-freshness sweep, distinct from `release-check`/`release-readiness-check` (which gate
code/release correctness, not prose). Run this any time a change touches task counts, CLI flags,
family names, or repository URLs — the kind of edit that silently makes a doc wrong without
breaking any test.

## 1. Stale counts

Docs like `README.md`, `docs/task_authoring.md`, and `CHANGELOG.md` sometimes hardcode task
counts or family lists. Cross-check them against reality:

```bash
find tasks -name '*.yaml' | grep -v heldout | sed 's#tasks/##;s#/.*##' | sort | uniq -c
find tasks -path '*/heldout/*.yaml' | sed 's#tasks/##;s#/heldout.*##' | sort | uniq -c
uv run python -c "from companion_bench.schemas.task import Family; print([f.value for f in Family])"
```

Grep for numbers that look like task counts (`grep -n "tasks\|families\|per family" README.md
docs/*.md`) and confirm they match.

## 2. Dead or placeholder repository URLs

```bash
git remote -v   # the real origin
grep -rn "github.com/companion-bench\|github.com/<org>\|example.com" README.md pyproject.toml CITATION.cff docs/*.md 2>/dev/null
```

Any URL in a public file should point at the real remote, not a placeholder.

## 3. Broken internal links

```bash
# crude but effective: every markdown link target that looks like a repo-relative path
grep -rnoE '\]\(([^)h][^)]*\.md)\)' README.md docs/*.md docs/**/*.md 2>/dev/null | sed 's/.*(//;s/)$//' | sort -u | while read -r p; do
  [ -f "docs/$p" ] || [ -f "$p" ] || echo "MISSING: $p"
done
```

Adjust the relative-path resolution per the file you're checking from — the point is to catch
links to files that were renamed or never created.

## 4. Stale CI / Actions references

```bash
grep -rln "github/workflows\|actions/checkout\|CI badge\|\.github/workflows" README.md docs/*.md 2>/dev/null
```

Should only appear inside `docs/ci-disabled/` (the intentional archive) — anywhere else is a
leftover reference to a workflow that no longer exists.

## 5. README vs. actual CLI surface

```bash
uv run companion-bench --help
uv run companion-bench run --help
```

Skim for any command, flag, or default mentioned in `README.md`'s quickstart that no longer
matches. This drifts easily whenever a CLI option is added/renamed.

## 6. Public-claims framing (cheap, always worth a final check)

```bash
uv run pytest tests/test_public_claims.py -q
```

Catches "EMOTomo benchmark" / "OpenRouter benchmark" framing creeping into new prose.

## When to run this

After any commit that changes task counts/families, CLI flags, or repository metadata — and
always as part of `release-readiness-check` before a public-facing release.
