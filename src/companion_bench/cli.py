"""CompanionBench command-line interface (Typer).

This module is intentionally thin: it parses arguments and delegates to the runner,
evaluators, and storage layers. Full implementation lands in a later build step.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="companion-bench",
    help="API-first benchmark for LLM companions and proactive assistants.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def version() -> None:
    """Print the installed CompanionBench version."""
    from companion_bench import __version__

    typer.echo(__version__)


if __name__ == "__main__":  # pragma: no cover
    app()
