<!-- SPDX-License-Identifier: Apache-2.0 -->
# Security policy

## Supported versions

CompanionBench is public-alpha software (`0.1.0-alpha`). There is one supported line: the latest
commit on `main`. There are no older maintained releases to backport fixes to yet.

| Version | Supported |
| --- | --- |
| `0.1.0-alpha` (main) | ✅ |
| anything earlier | ❌ |

## Reporting a vulnerability

This is a solo-maintained project — please set expectations accordingly (best-effort response,
not a 24/7 security team). To report a vulnerability privately, use
[GitHub's private security advisory feature](https://github.com/ErbolTakhirov/Benchmark/security/advisories/new)
on this repository rather than opening a public issue. If that is unavailable to you, open an
issue that says only "security issue, please contact me privately" with no details, and the
maintainer will follow up for a private channel.

Please include: what you found, how to reproduce it, and what you think the impact is. You do not
need a working exploit — a clear description of the risk is enough to start from.

## What's actually sensitive in this repo

CompanionBench talks to LLM provider APIs, so the main asset worth protecting is **API keys**,
never the benchmark results themselves. Concretely:

- **API keys** for any provider (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`,
  `HF_TOKEN`, `OPENAI_COMPATIBLE_API_KEY`) — resolved **only** from environment variables
  (`adapter.from_env()`), never from CLI arguments, YAML config, or manifests. They should never
  appear in a run artifact, a log line, or a commit.
- **`.env`** — gitignored (`.env`, `.env.*`, with `.env.example` explicitly un-ignored and kept
  keyless). Never commit a populated `.env`.
- **Raw run artifacts** (`runs/`, `events.jsonl`, `run.json`) — gitignored. These can contain full
  model transcripts and, in a misconfigured environment, could inadvertently capture
  sensitive request/response content. If you want to share a run, sanitize it first (see
  `docs/samples/*/README.md` for the pattern this repo already uses, or run the
  `secret-scan-artifacts` skill before committing anything derived from a run).
- **`COMPANIONBENCH_LIVE=1`** is not a secret but is a live-call arming switch — it and `--live`
  both have to be set for any real network/spend-incurring call to happen, and `run` additionally
  requires `--yes` or an interactive confirm.

## Built-in tooling you can rely on

`src/companion_bench/utils/secrets.py` is the canonical secret-hygiene module:

- `collect_secret_values()` — gathers the current non-trivial values of every var in
  `SECRET_ENV_VARS`.
- `redact(text, secret_values)` — replaces secret values with a placeholder (longest-match-first).
- `scan_text_for_secrets` / `scan_paths_for_secrets` / `scan_run_dir` — count (never print) how
  many times a secret value appears in text/files/a run directory.

`tests/test_secrets.py` proves a real key reaches the outgoing request header but never a
persisted artifact. The `secret-scan-artifacts` project skill wraps this into a pre-commit-style
check over the working tree; run it before committing anything that touched a live run.

## If a secret is accidentally committed

1. **Rotate the key immediately** with the provider — assume it is compromised the moment it hits
   a commit, even if you plan to remove it from history.
2. Remove it from the working tree and open an issue/advisory (private, per above) so history
   rewriting (if needed) can be coordinated rather than done unilaterally.
3. Do not just delete the file in a new commit and call it done — the key is still in git history
   until it's rotated.
