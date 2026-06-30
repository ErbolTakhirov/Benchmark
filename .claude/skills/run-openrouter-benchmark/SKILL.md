---
name: run-openrouter-benchmark
description: Safely run a cost-capped live OpenRouter model comparison from a local .env (guardrails, pricing sync, online validation, capped run, score/report/frontier, secret scan, sanitized sample).
---

# Run a live OpenRouter comparison (safe, capped)

Produces a **sample run, not a final leaderboard**, scoped to these tasks, settings, and model
versions. Live calls cost **real money** — every safeguard below is mandatory.

## 1. Key in `.env` (never in chat, never on the CLI)

Put the key in `<repo>/.env`:

```
OPENROUTER_API_KEY=sk-or-...
COMPANIONBENCH_LIVE=1
OPENROUTER_REFERER=https://example.com
OPENROUTER_TITLE=CompanionBench Local OpenRouter Eval
```

`.env` is gitignored; the CLI loads it via `python-dotenv` with `override=False` (a real shell
export still wins). **Never print the key.** Tell the user only: `Put your OpenRouter key in: <repo>/.env`.

## 2. Guardrails (never weaken)

A non-mock `run` requires **`--live` AND `COMPANIONBENCH_LIVE=1` AND `--yes`/confirm**. Always pair
`--max-cost-usd` with `--limit-models`/`--limit-tasks` as **hard** caps. Cost is `null` when unknown.

## 3. Procedure

```bash
# prices (network)
uv run companion-bench pricing sync-openrouter --out configs/pricing.openrouter.yaml
# verify slugs live; enable ONLY verified ones in the model set
uv run companion-bench models validate --model-set configs/model_sets/<set>.yaml --online
# one capped run
uv run companion-bench run -m manifests/emotomo_smoke.yaml --model-set configs/model_sets/<set>.yaml \
  --pricing configs/pricing.openrouter.yaml --out runs/<name> --live --yes \
  --limit-models 4 --repeats 2 --shuffle-seed 42 --max-cost-usd 3
uv run companion-bench score --run runs/<name> --bootstrap --bootstrap-resamples 2000 --bootstrap-seed 42
uv run companion-bench report --run runs/<name>
uv run companion-bench frontier --run runs/<name>
```

Stop and **ask before any larger run**.

## 4. After the run

- Secret-scan all artifacts (skill: **secret-scan-artifacts**). Empty before committing anything.
- Commit a **sanitized sample only** (`README`, `summary.md`, `scores.json`, `modelset.json`,
  `frontier.*`) — **never** raw `events.jsonl`, never `.env`, never `runs/`.
- Describe results per [`public_claims.md`](../../docs/public_claims.md): "CompanionBench evaluation
  using the <set> model set via OpenRouter (sample run, not a leaderboard)".
