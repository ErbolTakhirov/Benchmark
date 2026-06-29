"""Guard test: keep misleading framing out of the public docs.

CompanionBench is a general companion-communication benchmark — not an "EMOTomo benchmark" and
not an "OpenRouter benchmark" (EMOTomo is one example *model set*; OpenRouter is one *provider*).
This test fails if those bare phrases appear in the public prose docs **except** in an explicitly
negating / policy context (e.g. "not an EMOTomo benchmark", "there is no OpenRouter benchmark").

``docs/public_claims.md`` is exempt by design: it is the policy document that *catalogs* the
forbidden phrases, so it necessarily quotes them. A linter does not lint its own rule list.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Public prose we hold to the naming policy: the README and every Markdown doc...
DOC_PATHS: list[Path] = [REPO_ROOT / "README.md", *sorted((REPO_ROOT / "docs").rglob("*.md"))]
# ...except the policy doc itself, which intentionally quotes the bad phrases as examples.
EXEMPT = {REPO_ROOT / "docs" / "public_claims.md"}

# The phrases that brand a model set / provider as if it were the benchmark.
BAD_PHRASE = re.compile(r"emotomo benchmark|open ?router benchmark", re.IGNORECASE)

# A flagged line is acceptable only when it is clearly negating / disclaiming the phrase.
ALLOW_MARKERS = ("not a", "no such thing", "never", "is not", "isn't", "❌")


def _offending_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for n, line in enumerate(text.splitlines(), start=1):
        # Strip Markdown emphasis so "**not** an" / "**EMOTomo benchmark**" match plainly.
        norm = re.sub(r"[*_`]", "", line)
        if BAD_PHRASE.search(norm):
            low = norm.lower()
            if not any(marker in low for marker in ALLOW_MARKERS):
                out.append((n, line.strip()))
    return out


def test_no_emotomo_or_openrouter_benchmark_framing() -> None:
    violations: list[str] = []
    for path in DOC_PATHS:
        if path in EXEMPT or not path.is_file():
            continue
        for lineno, line in _offending_lines(path.read_text(encoding="utf-8")):
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel}:{lineno}: {line}")
    assert not violations, (
        "Misleading 'EMOTomo/OpenRouter benchmark' framing in public docs "
        "(use 'CompanionBench evaluation using the EMOTomo model set via OpenRouter' instead):\n"
        + "\n".join(violations)
    )


def test_policy_doc_exists_and_catalogs_the_phrases() -> None:
    # The exemption is only safe if the policy doc actually defines the rule.
    policy = (REPO_ROOT / "docs" / "public_claims.md").read_text(encoding="utf-8").lower()
    assert "emotomo benchmark" in policy
    assert "openrouter benchmark" in policy
    assert "model set" in policy and "provider" in policy
