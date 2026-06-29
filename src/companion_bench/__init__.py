"""CompanionBench — an API-first benchmark for LLM companions and proactive assistants.

The public surface is intentionally small. Most users interact through the CLI
(``companion-bench`` / ``python -m companion_bench.cli``); library users compose the
schemas, adapters, runner, and evaluators directly.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
