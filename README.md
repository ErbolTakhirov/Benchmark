# CompanionBench

**The first clean, API-first, open-source benchmark for evaluating LLM companions and proactive
assistants across realistic multi-turn conversations.**

[![CI](https://github.com/companion-bench/companion-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/companion-bench/companion-bench/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)

> **Status: MVP scaffold (v0.1).** The end-to-end pipeline runs offline against a deterministic mock
> model. Real provider adapters ship with clean interfaces; LLM-as-judge and human evaluation are the
> next milestones. See [MVP limitations](#mvp-limitations).

---

## What is CompanionBench?

Most "emotional intelligence" benchmarks score a model on **static, single-turn prompts**: label the
emotion, pick the empathetic reply. But a real companion or proactive assistant lives in a *stream* of
interaction, where quality is about **decisions over time**:

- *Should I say something right now, or stay quiet?*
- *Is this the right moment, or am I interrupting?*
- *Does this particular user want comfort, or a fix?*
- *They told me to stop doing that two turns ago — did I actually stop?*
- *Is this a moment to abstain, ask permission, or hold a boundary?*

CompanionBench measures exactly these behaviors through **multi-turn, API-mediated conversations**. It
jointly evaluates **initiative selection, intervention timing, emotional attunement, multi-turn
preference adaptation, abstention, and safety boundaries** — not just whether a single reply *sounds*
nice.

## Research hypothesis

> LLM companion quality is better measured by realistic multi-turn, API-mediated conversations that
> jointly evaluate initiative selection, intervention timing, emotional attunement, and preference
> adaptation than by static single-turn emotion-label or generic chatbot benchmarks alone.

See [`docs/hypothesis.md`](docs/hypothesis.md) for the full statement, predictions, and how we plan to
test it.

## What it compares

CompanionBench compares API-served LLMs and assistant systems across five dimensions:

| Dimension | Question it answers |
| --- | --- |
| **Initiative relevance** | Does the model correctly decide *whether* to intervene, pick a useful target, and avoid intrusive suggestions? |
| **Timing & pacing** | Does it act inside the acceptable window — not too early, too late, or too often? |
| **Emotional attunement** | Does it infer the user's state and choose the style *this* user prefers, not generic nice-sounding empathy? |
| **Preference adaptation** | Does it remember preferences, repair behavior after feedback, and avoid repeating disliked behaviors? |
| **Safety & boundaries** | Does it avoid manipulation, dependency-building, romanticization, and medical/legal/financial overreach — and ask permission or abstain when it should? |

## Why static emotion benchmarks are insufficient

Static single-turn emotion benchmarks are valuable but structurally blind to companion quality:

1. **No initiative decision.** A single-turn prompt already decides *that* the model should respond.
   Real companions must first decide *whether* to speak at all. Over-intervention and intrusiveness
   are invisible to single-turn setups.
2. **No timing.** "Right answer, wrong moment" cannot be expressed in one turn. Interrupting deep work
   and waiting too long to flag distress are both failures a static benchmark cannot see.
3. **Generic empathy scores well.** A globally "warm" reply gets high marks even when *this* user
   wanted a concrete fix. Attunement is about fit to a specific person, not average niceness.
4. **No memory / adaptation.** Whether a model *stops* a disliked behavior after feedback is a property
   of a trajectory, not a turn.
5. **Safety is contextual.** Dependency-building and boundary erosion accumulate across a relationship;
   a one-shot probe under-counts them.

CompanionBench is designed to make these failure modes **first-class, measurable signals**.

## Quickstart

Requires **Python 3.12+** and [**uv**](https://docs.astral.sh/uv/). No API keys are needed for the
mocked smoke benchmark — it runs fully offline.

```bash
# 1. Install dependencies (creates .venv and installs the package in editable mode)
uv sync --all-extras

# 2. Validate the smoke manifest and all referenced tasks
uv run companion-bench validate manifests/smoke.yaml

# 3. Run the smoke benchmark against the deterministic mock model
uv run companion-bench run --manifest manifests/smoke.yaml --model mock/empathetic-v1 --out runs/smoke

# 4. Score the run (rule-based, transparent, deterministic)
uv run companion-bench score --run runs/smoke

# 5. (optional) Export raw events + scores to Parquet
uv run companion-bench export --run runs/smoke --format parquet
```

This produces, under `runs/smoke/`:

- `events.jsonl` — append-only raw events (every model call, token/cost/latency, and failures)
- `run.json` — run metadata (run id, manifest, model, config, resolved task list)
- `scores.json` — per-dimension and aggregate scores
- `summary.md` — a human-readable summary table
- `export/` — optional Parquet files

> If the `companion-bench` console script is unavailable, every command also works as
> `uv run python -m companion_bench.cli <command> ...`.

## API-first design

CompanionBench talks to models exclusively through a small async adapter contract, so any
API-served system can be benchmarked without touching the runner:

```python
class ChatAdapter(Protocol):
    async def generate(self, request: ChatRequest) -> ChatResponse: ...
```

**Canonical public track (the default):** OpenAI, Anthropic, OpenRouter, Hugging Face Inference
Providers, and a generic OpenAI-compatible adapter.

**Secondary / future track:** local open-weight models via vLLM and Ollama through their
OpenAI-compatible endpoints. Local models are **not** the MVP default.

Models are addressed as `provider/model`, e.g. `openai/gpt-4o-mini`, `anthropic/claude-sonnet-4-6`,
`openrouter/meta-llama/llama-3.1-70b-instruct`, or `mock/empathetic-v1` for the offline mock.

See [`docs/provider_adapters.md`](docs/provider_adapters.md).

## How scoring works

For the MVP, scoring is **rule-based, deterministic, and fully transparent** — no LLM judge yet. Each
model turn returns a small structured envelope (a `CompanionTurn`): a `decision`
(`intervene` / `wait` / `abstain`), a `message`, an optional proactive `target`, a `style`, and an
`ask_permission` flag. The evaluator compares that envelope against each task's expectations to produce
six dimension scores in `[0, 1]` plus a weighted `total_score`:

`initiative_relevance_score`, `timing_score`, `empathy_score`, `adaptation_score`,
`abstention_score`, `safety_score`.

Dimensions that don't apply to a task are excluded and the weights renormalized. A future
**LLM-as-judge** and **human-evaluation** path is specified behind a `RubricEvaluator` interface; the
risks of LLM judges are documented in the [benchmark card](docs/benchmark_card.md). Full details:
[`docs/scoring.md`](docs/scoring.md).

## How to add a provider

1. Copy `src/companion_bench/adapters/openai_compatible.py` as a starting point.
2. Implement `async def generate(self, request: ChatRequest) -> ChatResponse`.
3. Register it with `@register_adapter("yourprovider")`.
4. Add config (base URL, API-key env var) following the existing pattern — **never hard-code keys**.
5. Add a mocked unit test (use `httpx.MockTransport`; no real network in tests).

The `add-provider` project skill (`.claude/skills/add-provider/`) walks through this step by step.
See [`docs/provider_adapters.md`](docs/provider_adapters.md).

## How to add a task

1. Create a versioned YAML file under `tasks/<family>/<task_id>.yaml`.
2. Fill in the [task schema](docs/task_authoring.md): scenario, persona, conversation turns, probes,
   intervention window, expected abstention, scoring rubric, positive/negative signals, and safety
   boundaries.
3. Reference it from a manifest under `manifests/`.
4. Run `companion-bench validate <manifest>` — every task is schema-validated.

The `add-task-family` skill scaffolds a new family. See [`docs/task_authoring.md`](docs/task_authoring.md).

## Architecture

```
manifest ─▶ runner.engine ─▶ adapters.* ─▶ CompanionTurn ─▶ events.jsonl
                  │                                              │
            conversation                                        ▼
            (replays turns,                              evaluators.rule_based
             builds requests)                                    │
                                                                 ▼
                                                    scores.json + summary.md
```

Full design notes in [`docs/architecture.md`](docs/architecture.md).

## MVP limitations

This is a **v0.1 scaffold**. Deliberately, in this milestone:

- **The default model is a deterministic mock**, not a real LLM. The mock is a *simulator* used to
  validate the pipeline end-to-end and to produce reproducible artifacts; **mock scores measure the
  pipeline, not model quality.**
- **Scoring is rule-based only.** It is transparent and reproducible but blunt: it cannot judge nuance
  the way a human (or a calibrated LLM judge) can. LLM-as-judge and human eval come next.
- **The task set is small** (8 smoke tasks, 2 per family) — enough to exercise every code path, not
  yet a representative evaluation suite.
- **Real provider adapters are interface-complete but lightly exercised.** Their unit tests use mocked
  transports; they have not been hardened against every provider quirk.
- **Cost/token accounting depends on what providers report**; missing values are recorded as `null`,
  never silently invented.

See the [benchmark card](docs/benchmark_card.md) for intended use, known limitations, and risks.

## Contributing & development

```bash
uv sync --all-extras
uv run ruff check .            # lint
uv run ruff format --check .   # format check
uv run pytest -q               # tests (all mocked, no network, no keys)
uv run mypy                    # optional static typing
```

Project conventions, commands, and quality gates live in [`CLAUDE.md`](CLAUDE.md).

## License

[Apache License 2.0](LICENSE). See [`NOTICE`](NOTICE).
