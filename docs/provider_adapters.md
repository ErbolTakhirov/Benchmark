# Provider adapters

CompanionBench talks to every model through one async contract, so adding a provider never
touches the runner or evaluators.

> For running real providers (the `providers` command, model sets, live guardrails, cost,
> retries, and secrets) see [`live_and_cost.md`](live_and_cost.md). This page is about the
> adapter contract and adding a new provider.

```python
class ChatAdapter(ABC):
    provider: ClassVar[str]
    async def generate(self, request: ChatRequest) -> ChatResponse: ...
    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "ChatAdapter": ...
    async def aclose(self) -> None: ...
```

Adapters are registered by name and built from the environment:

```python
from companion_bench.adapters import create_adapter, available_providers
available_providers()           # ['anthropic', 'mock', 'openai', 'openai_compatible', 'openrouter']
adapter = create_adapter("openai")     # reads OPENAI_API_KEY etc. from os.environ
```

Models are addressed as `provider/model`. Only the first slash splits provider from model, so
`openrouter/meta-llama/llama-3.1-70b-instruct` is provider `openrouter`, model
`meta-llama/llama-3.1-70b-instruct`.

## Built-in providers

| Provider | Class | Base URL env / default | Key env |
| --- | --- | --- | --- |
| `mock` | `MockAdapter` | — (offline) | — |
| `openai` | `OpenAIAdapter` | `OPENAI_BASE_URL` / `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| `anthropic` | `AnthropicAdapter` | `ANTHROPIC_BASE_URL` / `https://api.anthropic.com` | `ANTHROPIC_API_KEY` |
| `openrouter` | `OpenRouterAdapter` | `OPENROUTER_BASE_URL` / `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| `openai_compatible` | `OpenAICompatibleAdapter` | `OPENAI_COMPATIBLE_BASE_URL` | `OPENAI_COMPATIBLE_API_KEY` (optional) |

### Hugging Face Inference Providers
HF exposes an OpenAI-compatible router. Point the generic adapter at it:

```bash
export OPENAI_COMPATIBLE_BASE_URL=https://router.huggingface.co/v1
export OPENAI_COMPATIBLE_API_KEY=$HF_TOKEN
companion-bench run -m manifests/smoke.yaml --model "openai_compatible/<vendor>/<model>" -o runs/hf
```

### Local / open-weight (secondary track)
vLLM and Ollama both speak the OpenAI-compatible shape — use `openai_compatible` with a
`http://localhost:.../v1` base URL and no key. Local models are **not** the MVP default.

## The structured envelope
Adapters request the `CompanionTurn` JSON via the system instruction the conversation builder
injects, and (for OpenAI-shaped providers) `response_format={"type": "json_object"}`. Responses
are parsed tolerantly by `CompanionTurn.from_text` (handles fenced/embedded JSON). A response
that cannot be parsed yields `parsed=False` and is recorded as a failure — never silently
defaulted.

## Errors and retries
`generate` raises typed `AdapterError` subclasses carrying a `retryable` flag:
`ProviderTimeoutError` (retryable), `ProviderResponseError` (retryable for 429/5xx, not for
4xx), `ProviderAuthError` (not retryable), `ResponseParseError`. The engine retries retryable
errors up to `max_retries`, then records a `model_failure` event.

## Adding a provider

For an OpenAI-compatible server, subclass and set the defaults (this is the entire
`OpenAIAdapter`):

```python
from companion_bench.adapters.base import register_adapter
from companion_bench.adapters.openai_compatible import OpenAICompatibleAdapter

@register_adapter("myprovider")
class MyProviderAdapter(OpenAICompatibleAdapter):
    provider = "myprovider"
    DEFAULT_BASE_URL = "https://api.myprovider.com/v1"
    BASE_URL_ENV = "MYPROVIDER_BASE_URL"
    API_KEY_ENV = "MYPROVIDER_API_KEY"
    REQUIRES_KEY = True
```

For a non-OpenAI shape, subclass `ChatAdapter` directly and implement `generate` (see
`anthropic.py`). Then:

1. Import it (and add to `__all__`) in `adapters/__init__.py` so it registers.
2. Add the env vars to `.env.example` — **never commit real keys**.
3. Add a unit test using `httpx.MockTransport` (accept an injectable `client`); **no real
   network in tests**.
4. `uv run ruff check . && uv run mypy && uv run pytest -q`.

The `add-provider` project skill walks through this step by step.

## Cost & tokens
`token_usage`, `latency_ms`, and `estimated_cost_usd` are recorded when the provider reports
them; missing values stay `null` (never invented). `estimated_cost_usd` is populated only when
an adapter is constructed with a `pricing=(input_per_1M, output_per_1M)` tuple.
