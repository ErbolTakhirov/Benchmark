# CompanionBench

**An open-source benchmark for evaluating human-like companion communication in LLMs** — how well
a model communicates like a high-quality human companion across realistic, multi-turn
conversations: emotionally attuned, context-aware, appropriately proactive, non-intrusive,
preference-adaptive, and safe. It measures **targeted behaviors under defined scenarios**, not a
universal "intelligence" or "human-likeness" score.

[![Local verification required](https://img.shields.io/badge/CI-local_verification_required-orange.svg)](docs/local_verification.md)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)

> **Status: public alpha (v0.1).** The end-to-end pipeline runs offline against deterministic mock
> models and live against real providers (opt-in, budget-capped). The public task suite covers 150
> tasks + a 36-task held-out split across six families; a held-out generalization check has been run
> (see [sample results](#sample-results)). LLM-as-judge and human evaluation are still ahead. **There
> is no GitHub Actions CI right now** (see [`docs/ci-disabled/`](docs/ci-disabled/)) — **local
> verification is the source of truth**: [`docs/local_verification.md`](docs/local_verification.md).
> See [Limitations](#limitations).

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

### What "human-like companion communication" means here

We use the phrase in a **deliberately narrow, behavioral** sense: communicating the way a thoughtful
human companion would in a specific situation — reading the moment, choosing whether and when to
speak, matching *this* person's preferred style, respecting stated boundaries, and abstaining when
that is the right move. We do **not** claim a model is "human-like" in general, conscious, or
emotionally genuine. CompanionBench scores observable communication choices on authored scenarios;
the numbers describe behavior on those scenarios, nothing more. See
[`docs/methodology.md`](docs/methodology.md) and the [public-claims policy](docs/public_claims.md).

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

## What CompanionBench does NOT measure

To be explicit about scope: this is **not** a general intelligence benchmark, a fluency/writing-
quality benchmark, a test of consciousness or genuine emotion, or a safety certification. It does
not measure "humanity" in general — `overall` is a **companion-communication score**, computed
from rule-based, deterministic scoring against authored scenarios, not a judgment about how human
a model is. It does not rank providers or model sets as an identity — EMOTomo is one example model
set and OpenRouter is one example provider adapter; neither is what CompanionBench *is*. See
[`docs/public_claims.md`](docs/public_claims.md) for the exact language this project holds itself
to, and [`docs/results_interpretation.md`](docs/results_interpretation.md) for how to read a score
without over-claiming.

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

### Real providers, model sets, and cost (live, opt-in)

```bash
companion-bench providers                                   # key presence (never values) + base URLs
companion-bench models validate --model-set configs/model_sets/example.yaml

# A live run needs BOTH --live AND COMPANIONBENCH_LIVE=1 (+ a key, + --yes or a confirm):
export OPENROUTER_API_KEY=...
COMPANIONBENCH_LIVE=1 companion-bench run -m manifests/smoke.yaml \
  --model-set configs/model_sets/your-set.yaml --out runs/live \
  --live --yes --max-cost-usd 1 --limit-tasks 2 --limit-models 2
companion-bench score  --run runs/live
companion-bench report --run runs/live                      # model-comparison table
```

Cost tracking, the `--max-cost-usd` budget guard, retry/backoff, provider config, and secret
handling are documented in [`docs/live_and_cost.md`](docs/live_and_cost.md).

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

### Models, model sets, and providers

CompanionBench keeps three things separate, on purpose:

- **The benchmark** is the tasks, scoring, and methodology in this repository. That is
  CompanionBench. It is model- and vendor-neutral.
- **A model set** is just a named, versioned list of *which models to compare* (see
  [`docs/model_sets.md`](docs/model_sets.md)). `configs/model_sets/emotomo-openrouter.yaml` is the
  **EMOTomo model set** — the models the EMOTomo product currently uses — and it is here only as an
  **example / first case study**. It is **not** the identity of the benchmark;
  you can point CompanionBench at any model set (`openai.yaml`, `anthropic.yaml`, `local-vllm.yaml`, …).
- **A provider** is just the API the calls go through. **OpenRouter is one provider adapter** among
  several (OpenAI, Anthropic, HF Inference Providers, OpenAI-compatible, mock). "Run the EMOTomo
  model set via OpenRouter" describes a *configuration*, never "the EMOTomo benchmark" or "the
  OpenRouter benchmark" — there is no such thing here.

So a sentence like *"CompanionBench evaluation using the EMOTomo model set via OpenRouter"* is
precise; *"EMOTomo benchmark"* or *"OpenRouter benchmark"* is not. See the
[public-claims policy](docs/public_claims.md) for the language we hold ourselves to.

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

## Limitations

This is a **public alpha (v0.1)**, not a finished, fully-validated benchmark. Honestly, right now:

- **The default model is a deterministic mock**, not a real LLM. The mock is a *simulator* used to
  validate the pipeline end-to-end and to produce reproducible artifacts; **mock scores measure the
  pipeline, not model quality.** The `manifests/smoke.yaml` 8-task set stays small and fixed on
  purpose — it's for fast pipeline sanity checks, not for evaluating a real model.
- **Scoring is rule-based only.** It is transparent and reproducible but blunt: it can be gamed by
  surface-level keyword overlap, and it cannot judge nuance the way a human (or a calibrated LLM
  judge) can. LLM-as-judge and human eval come next.
- **The public task suite is 150 tasks (25 per family across six families), with a 36-task
  held-out split (6 per family)** — enough for a held-out generalization check (see
  [sample results](#sample-results)) that shows the coarse "good vs. weak" signal holds up, but a
  fine-grained ranking of adjacent models is still not statistically reliable on this suite size.
- **Real provider adapters are interface-complete and exercised against real providers** (see
  sample results below) but not hardened against every provider quirk; unit tests use mocked
  transports, not live calls.
- **Cost/token accounting depends on what providers report**; missing values are recorded as `null`,
  never silently invented.
- **No GitHub Actions CI right now** — see [`docs/ci-disabled/`](docs/ci-disabled/) for why and
  [`docs/local_verification.md`](docs/local_verification.md) for the local replacement.

See the [benchmark card](docs/benchmark_card.md) for intended use, known limitations, and risks,
and [`docs/audits/`](docs/audits/) for the full external-reviewer-style audits.

## Sample results

Sanitized sample runs (no raw transcripts, never a leaderboard) live in
[`docs/samples/`](docs/samples/). Two are most representative of the current suite:

- [`companionbench-emotomo-fullsuite-r5/`](docs/samples/companionbench-emotomo-fullsuite-r5/) —
  10 models via OpenRouter across the full 150-task public suite (bootstrap 95% CIs).
- [`companionbench-emotomo-heldout-r5/`](docs/samples/companionbench-emotomo-heldout-r5/) — the
  same 10 models on the 36-task held-out split, checking whether the public-suite ranking
  generalizes.

See [`docs/results_interpretation.md`](docs/results_interpretation.md) for how to read either one
without over-claiming.

## Repository structure

```
src/companion_bench/   schemas, adapters, runner, evaluators, storage, config, utils, cli.py
tasks/<family>/         150 public task YAMLs (25 per family) + heldout/ (36, 6 per family)
manifests/              which tasks a run covers (smoke, full, heldout, mvp, ...)
configs/                pricing, provider overrides, model sets
docs/                   methodology, scoring, task authoring, audits/, samples/, ci-disabled/
tests/                  offline, keyless test suite
.claude/skills/         project-specific Claude Code skills (task authoring, audits, releases, ...)
```

See [`docs/architecture.md`](docs/architecture.md) for the data-flow view and
[`docs/index.md`](docs/index.md) for a full documentation map.

## Contributing & development

```bash
uv sync --all-extras
uv run ruff check .            # lint
uv run ruff format --check .   # format check
uv run pytest -q               # tests (all mocked, no network, no keys)
uv run mypy                    # static typing (strict)
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full contribution guide (task/provider authoring,
the no-secrets/no-raw-runs rules, commit conventions) and
[`docs/local_verification.md`](docs/local_verification.md) for the complete local gate — there is
no CI to catch what you skip locally right now. Project conventions and quality gates also live in
[`CLAUDE.md`](CLAUDE.md). Security issues: see [`SECURITY.md`](SECURITY.md), not a public issue.

## Citation

If you use CompanionBench, please cite it — see [`CITATION.cff`](CITATION.cff). This is a public
alpha (`0.1.0-alpha`); cite the specific commit/tag you used.

## License

[Apache License 2.0](LICENSE). See [`NOTICE`](NOTICE). Community standards:
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
