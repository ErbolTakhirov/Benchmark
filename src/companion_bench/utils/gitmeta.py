"""Best-effort git provenance for run artifacts.

Records the git commit of the checkout a run was launched from, so a scored artifact can be traced
back to code. In the normal dev / editable-install workflow that is the CompanionBench source
commit; if the package is pip-installed into a *different* repository, it is that repository's HEAD
instead (still useful provenance — the environment the run came from). Everything degrades to
``None`` when git is unavailable, the directory is not a repository, or the call fails — provenance
is a nicety, never a hard dependency, and an installed (non-git) package legitimately has no commit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["git_commit"]


def git_commit(*, short: bool = True, cwd: Path | None = None) -> str | None:
    """Return the current git commit hash, or ``None`` if it cannot be determined.

    ``None`` covers every failure mode — git not installed, not a work tree, an empty repo, or a
    timeout — so callers never have to handle an exception. A detached HEAD still returns its hash,
    which is exactly the provenance we want. Fixed argv, no shell, no user-supplied input.
    """
    rev = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
    try:
        result = subprocess.run(
            rev,
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(cwd) if cwd is not None else None,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = result.stdout.strip()
    return commit or None
