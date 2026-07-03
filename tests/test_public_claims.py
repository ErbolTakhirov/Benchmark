"""Guard test: public docs use precise, scoped framing — not branding or overclaims.

CompanionBench is the tasks + scoring; a run's model set and provider are recorded as **run
metadata**. This guard keeps two things out of visitor/contributor-facing Markdown:

1. **branding** that treats a model set / provider as the benchmark's identity ("EMOTomo
   benchmark", "OpenRouter benchmark");
2. **overclaims** the repository does not support ("most human", "human-validated", "final
   leaderboard", "safe for vulnerable users", "definitive benchmark").

A flagged phrase is allowed only when the line clearly negates or hedges it (a policy / roadmap
context). `docs/public_claims.md` is the policy catalog and is exempt (it lists the examples on
purpose); this guard instead checks that it *states the positive scoped-reporting policy*. The dated
`docs/audits/**` records are also exempt — they are point-in-time assessment artifacts.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Visitor- and contributor-facing Markdown held to the framing policy.
DOC_PATHS: list[Path] = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "CONTRIBUTING.md",
    *sorted((REPO_ROOT / "docs").rglob("*.md")),
    *sorted((REPO_ROOT / ".github").rglob("*.md")),
]


def _exempt(path: Path) -> bool:
    # The policy doc catalogs the anti-patterns as examples; audit docs are dated artifacts.
    return path.name == "public_claims.md" or "audits" in path.parts


# Branding that treats a model set / provider as the benchmark's identity.
BRANDING = re.compile(r"emotomo benchmark|open ?router benchmark", re.IGNORECASE)
# Universal claims the repository does not support.
OVERCLAIM = re.compile(
    r"most human|human-validated|human-approved|final leaderboard|"
    r"safe for vulnerable users|definitive benchmark",
    re.IGNORECASE,
)
# A flagged line is acceptable only when it clearly negates / hedges the phrase.
ALLOW_MARKERS = (
    "not ",
    "never",
    "no such thing",
    "isn't",
    "is not",
    "aren't",
    "❌",
    "avoid",
    "do not",
    "don't",
    "without",
    "pending",
    "not yet",
    "would require",
    "requires real",
    "instead of",
    "rather than",
)


def _flagged(text: str, pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for n, line in enumerate(text.splitlines(), start=1):
        norm = re.sub(r"[*_`]", "", line)  # strip markdown emphasis so "**not** an" matches plainly
        if pattern.search(norm) and not any(m in norm.lower() for m in ALLOW_MARKERS):
            out.append((n, line.strip()))
    return out


def _scan(pattern: re.Pattern[str]) -> list[str]:
    violations: list[str] = []
    for path in DOC_PATHS:
        if _exempt(path) or not path.is_file():
            continue
        for lineno, line in _flagged(path.read_text(encoding="utf-8"), pattern):
            violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line}")
    return violations


def test_public_docs_avoid_benchmark_branding() -> None:
    violations = _scan(BRANDING)
    assert not violations, (
        "A model set / provider is run metadata, not the benchmark's identity. "
        "Use 'CompanionBench evaluation using the EMOTomo model set via OpenRouter':\n"
        + "\n".join(violations)
    )


def test_public_docs_avoid_overclaims() -> None:
    violations = _scan(OVERCLAIM)
    assert not violations, (
        "Keep public docs scoped to the evaluated tasks / settings / model versions — "
        "avoid unsupported universal claims:\n" + "\n".join(violations)
    )


def test_public_claims_policy_states_scoped_framing() -> None:
    # The policy doc must state the positive scoped-reporting framing (not just list anti-patterns).
    policy = (REPO_ROOT / "docs" / "public_claims.md").read_text(encoding="utf-8").lower()
    for token in ("scoped", "model set", "provider", "metadata"):
        assert token in policy, (
            f"public_claims.md should state the scoped-reporting policy: {token!r}"
        )
    # The README must carry the same positive scoped framing a visitor reads first.
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "scoped" in readme and "task" in readme
