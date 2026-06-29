# Architecture

CompanionBench is a small, typed, modular pipeline. Data flows one direction; each layer has
a single responsibility and a stable schema at its boundary.

```
 manifest.yaml ──▶ runner.manifest ──▶ [Task, …]
                                          │
                                          ▼
            runner.engine ──▶ runner.conversation ──▶ ChatRequest ──▶ adapters.*
              (async,            (replays scripted        │              (mock | openai |
               bounded            turns, builds the        │               anthropic | …)
               concurrency)       per-probe request)       ▼
                  │                                    CompanionTurn
                  ▼                                        │
            storage.jsonl  ◀───────── events ◀─────────────┘
            (events.jsonl, append-only)
                  │
                  ▼
            evaluators.aggregate ──▶ evaluators.rule_based ──▶ scores.json + summary.md
                  │
                  ▼
            storage.export ──▶ export/*.parquet   (optional)
```

## Layers

| Package | Responsibility |
| --- | --- |
| `schemas/` | Pydantic v2 models. `model.py` (CompanionTurn, ChatRequest/Response, ModelSpec), `task.py` (Task + turns + dimensions), `run.py` (Event union, RunConfig/Metadata), `score.py` (scores). Dependency order is `model → task → score`. |
| `adapters/` | The `ChatAdapter` contract + provider registry. `mock.py` is a deterministic simulator; the rest are real async HTTPX clients. |
| `runner/` | `manifest.py` (load/validate/resolve tasks), `conversation.py` (scripted replay → requests), `engine.py` (async orchestration, retries, failure capture), `events.py` (event builders). |
| `evaluators/` | `rule_based.py` (six dimension scorers), `aggregate.py` (rollups + summary), `rubric.py` (future LLM-judge interface). |
| `storage/` | `jsonl.py` (append-only events + JSON helpers), `export.py` (optional Parquet). |
| `utils/` | `ids.py` (deterministic ids), `timing.py` (Clock/FrozenClock), `errors.py` (typed errors). |

## Key design decisions

### The `CompanionTurn` envelope
Each model invocation ("probe") returns a small JSON object: `decision`
(`intervene`/`wait`/`abstain`), `message`, `target`, `style`, `ask_permission`, `rationale`.
Making the decision explicit is what lets the MVP score behavior deterministically and
mirrors how real proactive systems work — they decide *whether* to act before *what* to say.
See [`scoring.md`](scoring.md).

### Mock = simulator, cleanly separated
`ChatRequest` carries the real NL `messages` **plus** an optional `simulation_context` that
**only `MockAdapter` reads**. Real adapters ignore it. The mock applies a deterministic
per-profile policy over that context, so the smoke benchmark differentiates behaviors without
the mock "seeing" the rubric through the model channel. **Mock scores validate the pipeline,
not model quality.**

### `run` vs `score` split
`run` produces the immutable raw artifact (`events.jsonl` — every model call, token/cost/
latency, and failure) plus `run.json`. `score` re-reads those events, re-loads the tasks
referenced by `run.json`, and derives `scores.json` + `summary.md`. Raw and derived artifacts
are never mixed, so re-scoring never rewrites history.

### Determinism
The engine takes an injectable `Clock` and assigns event ids in a deterministic post-order
after all (concurrent) tasks finish. With a `FrozenClock` and the mock's fixed simulated
latency, `events.jsonl` is byte-stable — which is what the tests assert.

### Failures are first-class
A provider error (after retries on retryable errors) becomes a `model_failure` event with the
error type, message, and attempt count. Failures are recorded, never silently dropped.

## Extending the pipeline

- **New provider:** implement `ChatAdapter.generate`, register with `@register_adapter`. See
  [`provider_adapters.md`](provider_adapters.md).
- **New task / family:** add a versioned YAML task and reference it from a manifest. See
  [`task_authoring.md`](task_authoring.md).
- **New scorer (LLM judge / human eval):** implement the `RubricEvaluator` interface in
  `evaluators/rubric.py`. See [`scoring.md`](scoring.md) and [`benchmark_card.md`](benchmark_card.md).
