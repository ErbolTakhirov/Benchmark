<!-- SPDX-License-Identifier: Apache-2.0 -->
# CompanionBench — model sets

A **model set** is a named, versioned list of *which models to compare*. It is the single most
important separation in CompanionBench:

> The **benchmark** is the tasks, scoring, and methodology. A **model set** is just a roster of
> models you point the benchmark at. A **provider** is just the API the calls go through.

Keeping these apart is what lets CompanionBench compare *any* LLM or API model without changing the
benchmark, and it is why there is no such thing as an "EMOTomo benchmark" or an "OpenRouter
benchmark" here — only "CompanionBench run with model set X via provider Y".

## What a model set is (and isn't)

A model set decouples *which models* from *which tasks*. The manifest
(`manifests/*.yaml`) chooses the tasks; the model set (`configs/model_sets/*.yaml`) chooses the
models; you combine them on the command line:

```bash
companion-bench run -m manifests/emotomo_smoke.yaml \
  --model-set configs/model_sets/<your-set>.yaml --out runs/<name>
```

A model set is **not**:

- the benchmark (the benchmark is vendor-neutral and lives in `tasks/` + `evaluators/`),
- a provider (a set can mix providers; one set can list OpenAI, Anthropic, and OpenRouter models),
- a leaderboard or an endorsement of the listed models.

## Schema

Each entry is a [`ModelEntry`](../src/companion_bench/config/model_sets.py). Fields:

| Field | Meaning |
| --- | --- |
| `id` | Unique label within the set. |
| `provider` | Registered provider adapter (`openai`, `anthropic`, `openrouter`, `openai_compatible`, `mock`). |
| `model` | The provider's model slug (e.g. `deepseek/deepseek-chat-v3-0324`). |
| `enabled` | Whether this entry runs (disabled entries are documented but skipped). |
| `temperature`, `max_completion_tokens` | Optional per-model run overrides. |
| `source` | Provenance — where this slug came from. |
| `needs_mapping` | `true` until the slug is verified against the provider; surfaces a warning. |
| `notes` | Free-text (e.g. a live-verification record). |

Validate any set offline with:

```bash
companion-bench models validate --model-set configs/model_sets/<set>.yaml
# add --online (needs COMPANIONBENCH_LIVE=1) to check slugs/pricing against live OpenRouter metadata
```

`models validate` checks the schema, that every provider is registered, flags `needs_mapping`
slugs and unknown prices, and — with `--online` — reports `live_verified` / `unavailable` /
`pricing_missing`. It **never** auto-flips `needs_mapping`; verification is a human decision.

## The EMOTomo model set (the first example set)

[`configs/model_sets/emotomo-openrouter.yaml`](../configs/model_sets/emotomo-openrouter.yaml) is the
**EMOTomo model set**: the OpenRouter slugs the EMOTomo product currently configures, extracted
read-only from its model registry (no secrets copied — only slugs and non-secret params). It is in
this repository as the **first example / case study**, to demonstrate evaluating a real product's
roster end-to-end. It is **not** the identity of the benchmark.

Two well-established slugs (`deepseek/deepseek-chat-v3-0324`, `mistralai/mistral-nemo`) are enabled
and live-verified; the rest are listed but disabled, pending verification. The sanitized result of
a tiny run lives at [`samples/emotomo-openrouter-smoke/`](samples/emotomo-openrouter-smoke/) and is
clearly marked a **sample run, not a leaderboard**.

## Adding another model set

Copy [`configs/model_sets/example.yaml`](../configs/model_sets/example.yaml) and edit. Some sets you
might add:

- `general-openrouter.yaml` — a broad cross-vendor roster served via OpenRouter.
- `openai.yaml` — OpenAI models via the `openai` adapter.
- `anthropic.yaml` — Claude models via the `anthropic` adapter.
- `local-vllm.yaml` — local open-weight models via a vLLM OpenAI-compatible endpoint
  (`provider: openai_compatible`).

Then:

1. Give it a unique `set_id` and a short `description`.
2. List models with `provider` + `model`; set `needs_mapping: true` until you've confirmed the
   slug with a live probe (or `models validate --online`).
3. Run `companion-bench models validate --model-set <path>` (offline) and fix any errors.
4. Use it: `companion-bench run -m <manifest> --model-set <path> --out runs/<name>`.

## Keeping secrets out of configs

- **No API keys in model sets, manifests, or any config — ever.** Keys are resolved **only** from
  environment variables (e.g. `OPENROUTER_API_KEY`), never from CLI args or YAML. A test proves no
  key reaches an artifact.
- A model set holds **slugs and non-secret params only**. When extracting a roster from another
  repository, copy model identifiers and public parameters — not credentials, endpoints with
  embedded tokens, or `.env` contents.
- `.env` is gitignored; `.env.example` stays keyless.
- Before committing any run artifact, scan it for key-shaped strings and auth headers (the result
  must be empty), and never commit raw transcripts unless sanitized and explicitly approved.

See [`live_and_cost.md`](live_and_cost.md) for the full live-run, cost, and secret-handling rules,
and [`public_claims.md`](public_claims.md) for how to describe model-set results responsibly.
