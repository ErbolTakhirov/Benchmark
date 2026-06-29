# Sample: CompanionBench full run using the EMOTomo model set via OpenRouter, 3 repeats (live — populate when run)

This directory is the home for a **full-family** CompanionBench evaluation of the **EMOTomo model
set** served via the **OpenRouter provider**, with repeats, bootstrap CIs, and a cost-quality
frontier. It is a **sample run, not a final leaderboard**: EMOTomo is one example model set and
OpenRouter is one provider adapter, not the benchmark itself (see
[`../../model_sets.md`](../../model_sets.md)). Producing it makes **live, paid API calls**, so it is
gated behind a key + `COMPANIONBENCH_LIVE=1` and is **not run in CI**. Until someone runs it with a
key, this README is the placeholder.

- For a **real (tiny)** first result, see [`../emotomo-openrouter-smoke/`](../emotomo-openrouter-smoke/)
  (deepseek-chat-v3-0324 + mistral-nemo, 2 adaptation tasks, live-verified, secret-scanned).
- For the **artifact shapes** this run will produce (CIs, behavior flags, frontier), see
  [`../pipeline-demo-r3/`](../pipeline-demo-r3/) (mock, offline).

## Reproduce (needs `OPENROUTER_API_KEY` + `COMPANIONBENCH_LIVE=1`)

```bash
# 1. Sync current OpenRouter prices so cost is real (not null):
companion-bench pricing sync-openrouter --out configs/pricing.openrouter.yaml

# 2. Optionally verify every enabled slug is live + priced before spending:
companion-bench models validate --model-set configs/model_sets/emotomo-openrouter.yaml --online

# 3. Full family, 3 repeats, with a hard $5 budget:
companion-bench run -m manifests/emotomo_smoke.yaml \
  --model-set configs/model_sets/emotomo-openrouter.yaml \
  --pricing configs/pricing.openrouter.yaml \
  --out runs/emotomo-openrouter-full-r3 \
  --live --yes --repeats 3 --shuffle-seed 42 --max-cost-usd 5

# 4. Score with bootstrap CIs, compare, and draw the frontier:
companion-bench score --run runs/emotomo-openrouter-full-r3 --bootstrap --bootstrap-resamples 5000 --bootstrap-seed 42
companion-bench report --run runs/emotomo-openrouter-full-r3
companion-bench frontier --run runs/emotomo-openrouter-full-r3
```

## Before committing the populated sample

- Copy only sanitized artifacts here: per-model `summary.md` + `scores.json`, `modelset.json`,
  `frontier.md` / `frontier.csv`, and this README. **Not** the raw `events.jsonl` (transcripts).
- Secret-scan first: grep the directory for OpenRouter key prefixes, long token-shaped strings,
  and auth-header names (Authorization / api-key); the result must be empty.
- Enable more of the 10 slugs in the model set as `--online` validation confirms them.
