---
name: add-provider
description: Add a new provider adapter to CompanionBench (registration, env config, mocked test).
---

# Add a provider adapter

Add a new `ChatAdapter` so `provider/model` refs (e.g. `myprovider/some-model`) resolve. The
adapter is the single seam new providers plug into; the runner never imports a concrete provider.

**Golden rule: never hard-code an API key, never commit a real key, never hit the real network in
tests.** Keys come from env vars only; tests use `httpx.MockTransport`.

## 1. Pick the implementation path

- **OpenAI-compatible server** (vLLM, Ollama, LM Studio, an aggregator, etc.): subclass
  `OpenAICompatibleAdapter` and just override the class attrs — like
  `src/companion_bench/adapters/openai.py` and `openrouter.py`. No `generate` needed.
- **Different wire shape** (own endpoint/auth/response): implement `generate` directly, like
  `src/companion_bench/adapters/anthropic.py`. Copy `openai_compatible.py` as a starting point.

## 2. Create the adapter file

`src/companion_bench/adapters/myprovider.py`. Subclass example:

```python
from __future__ import annotations

from companion_bench.adapters.base import register_adapter
from companion_bench.adapters.openai_compatible import OpenAICompatibleAdapter

__all__ = ["MyProviderAdapter"]


@register_adapter("myprovider")
class MyProviderAdapter(OpenAICompatibleAdapter):
    """Adapter for MyProvider's OpenAI-compatible API."""

    provider = "myprovider"
    DEFAULT_BASE_URL = "https://api.myprovider.com/v1"
    BASE_URL_ENV = "MYPROVIDER_BASE_URL"
    API_KEY_ENV = "MYPROVIDER_API_KEY"
    REQUIRES_KEY = True          # False if a local server needs no key
    SUPPORTS_JSON_MODE = True    # False if the server has no response_format=json_object
```

For the direct path: implement `async def generate(self, request: ChatRequest) -> ChatResponse`,
read config in `from_env(cls, env)`, take an injectable `client: httpx.AsyncClient | None = None`
in `__init__`, and raise `ProviderTimeoutError` / `ProviderResponseError` / `ProviderAuthError`
(from `companion_bench.utils.errors`) on failures — mirror `anthropic.py`.

Config comes only from `from_env` (base class handles it for subclasses): base URL from
`BASE_URL_ENV` or `DEFAULT_BASE_URL`; key from `API_KEY_ENV`; raise `ProviderAuthError` if
`REQUIRES_KEY` and no key.

## 3. Register it in the package

Edit `src/companion_bench/adapters/__init__.py`: add the import and add the class name to
`__all__`, which is **kept sorted**.

```python
from companion_bench.adapters.myprovider import MyProviderAdapter
```

Importing the package is what registers the provider so `create_adapter("myprovider", env)` works.

## 4. Document env vars

Add an entry to `.env.example` (empty value + base URL), e.g.:

```
# --- MyProvider -----------------------------------------------------------
MYPROVIDER_API_KEY=
MYPROVIDER_BASE_URL=https://api.myprovider.com/v1
```

`.env` is gitignored; `.env.example` carries blanks only.

## 5. Write a mocked unit test

Add to `tests/test_mock_adapter.py` (or a new test file). Tests are async (`asyncio_mode = auto`,
no decorator needed) and must use `httpx.MockTransport` — no real network:

```python
import httpx
from companion_bench.adapters.myprovider import MyProviderAdapter
from companion_bench.schemas.model import ChatMessage, ChatRequest, Decision, ModelSpec, Role


async def test_myprovider_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"decision": "wait", "message": ""}'}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 0, "total_tokens": 5},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = MyProviderAdapter(
        base_url="https://api.myprovider.com/v1", api_key="k", client=client
    )
    try:
        resp = await adapter.generate(
            ChatRequest(
                model=ModelSpec.parse("myprovider/some-model"),
                messages=(ChatMessage(role=Role.USER, content="hi"),),
            )
        )
    finally:
        await client.aclose()
    assert resp.companion_turn is not None
    assert resp.companion_turn.decision is Decision.WAIT
```

If you touch the registry, update `test_registry_has_all_builtin_providers` — it asserts the exact
sorted provider list, which your new provider changes.

## 6. Run the quality gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
```

## Checklist

- [ ] Subclassed `OpenAICompatibleAdapter` (or implemented `generate` directly for a custom shape).
- [ ] `@register_adapter("name")` applied; class attrs / `from_env` set base URL + key env vars.
- [ ] Import + sorted `__all__` entry added to `adapters/__init__.py`.
- [ ] Env vars added to `.env.example` (no real key).
- [ ] Mocked `httpx.MockTransport` test added; registry test updated if needed.
- [ ] No hard-coded keys anywhere; ruff/format/mypy/pytest all green.
