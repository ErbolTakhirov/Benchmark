"""Adapter tests: deterministic mock profiles + HTTP adapters via MockTransport.

No test in this file touches the real network: the mock is offline by construction, and
the HTTP adapters are driven through ``httpx.MockTransport``.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from companion_bench.adapters import (
    AnthropicAdapter,
    MockAdapter,
    OpenAIAdapter,
    OpenAICompatibleAdapter,
    available_providers,
    create_adapter,
)
from companion_bench.schemas.model import ChatMessage, ChatRequest, Decision, ModelSpec, Role, Style
from companion_bench.utils.errors import AdapterError, ProviderAuthError, ProviderResponseError

INTERVENE_CTX: dict[str, Any] = {
    "ideal_decision": "intervene",
    "in_window": True,
    "preferred_style": "gentle",
    "target_keywords": ["break"],
    "positive_signals": ["take a break"],
    "requires_permission": True,
}


def mock_request(profile: str, ctx: dict[str, Any] | None = None) -> ChatRequest:
    return ChatRequest(
        model=ModelSpec.parse(f"mock/{profile}"),
        messages=(ChatMessage(role=Role.USER, content="still working"),),
        simulation_context=ctx,
    )


# --------------------------------------------------------------------------- registry
def test_registry_has_all_builtin_providers() -> None:
    assert available_providers() == [
        "anthropic",
        "mock",
        "openai",
        "openai_compatible",
        "openrouter",
    ]


def test_create_adapter_returns_mock() -> None:
    assert isinstance(create_adapter("mock"), MockAdapter)


# --------------------------------------------------------------------------- mock determinism
async def test_mock_is_deterministic() -> None:
    adapter = MockAdapter()
    first = await adapter.generate(mock_request("empathetic-v1", INTERVENE_CTX))
    second = await adapter.generate(mock_request("empathetic-v1", INTERVENE_CTX))
    assert first == second


async def test_mock_reports_usage_cost_and_latency() -> None:
    resp = await MockAdapter().generate(mock_request("empathetic-v1", INTERVENE_CTX))
    assert resp.parsed is True
    assert resp.estimated_cost_usd == 0.0
    assert resp.latency_ms == 6.0
    assert resp.token_usage is not None
    assert resp.token_usage.total_tokens == (resp.token_usage.prompt_tokens or 0) + (
        resp.token_usage.completion_tokens or 0
    )


async def test_unknown_mock_profile_raises() -> None:
    with pytest.raises(AdapterError, match="unknown mock profile"):
        await MockAdapter().generate(mock_request("does-not-exist", INTERVENE_CTX))


# --------------------------------------------------------------------------- profile behavior
async def test_empathetic_follows_ideal_and_includes_signals() -> None:
    turn = (
        await MockAdapter().generate(mock_request("empathetic-v1", INTERVENE_CTX))
    ).companion_turn
    assert turn is not None
    assert turn.decision is Decision.INTERVENE
    assert turn.style is Style.GENTLE
    assert turn.ask_permission is True
    assert "take a break" in turn.message
    assert "break" in turn.message


async def test_empathetic_waits_when_ideal_is_wait() -> None:
    turn = (
        await MockAdapter().generate(mock_request("empathetic-v1", {"ideal_decision": "wait"}))
    ).companion_turn
    assert turn is not None and turn.decision is Decision.WAIT
    assert turn.message == ""


async def test_intrusive_always_intervenes_bluntly() -> None:
    ctx = {"ideal_decision": "wait", "negative_signals": ["I know exactly how you feel"]}
    turn = (await MockAdapter().generate(mock_request("intrusive-v1", ctx))).companion_turn
    assert turn is not None
    assert turn.decision is Decision.INTERVENE  # wrong: ideal was wait
    assert turn.style is Style.DIRECT
    assert turn.ask_permission is False
    assert "I know exactly how you feel" in turn.message


async def test_intrusive_repeats_disliked_behavior() -> None:
    ctx = {"ideal_decision": "intervene", "disliked_behaviors": ["sweetie"]}
    turn = (await MockAdapter().generate(mock_request("intrusive-v1", ctx))).companion_turn
    assert turn is not None and "sweetie" in turn.message


async def test_silent_always_waits() -> None:
    for ideal in ("intervene", "abstain", "wait"):
        turn = (
            await MockAdapter().generate(mock_request("silent-v1", {"ideal_decision": ideal}))
        ).companion_turn
        assert turn is not None and turn.decision is Decision.WAIT


# --------------------------------------------------------------------------- OpenAI-compatible
def _openai_handler(captured: dict[str, Any]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"decision": "intervene", "message": "hi", "style": "gentle"}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    return httpx.MockTransport(handler)


async def test_openai_compatible_builds_request_and_parses_response() -> None:
    captured: dict[str, Any] = {}
    client = httpx.AsyncClient(transport=_openai_handler(captured))
    adapter = OpenAICompatibleAdapter(
        base_url="https://api.example.com/v1", api_key="sk-test", client=client
    )
    try:
        request = ChatRequest(
            model=ModelSpec.parse("openai_compatible/some-model"),
            messages=(ChatMessage(role=Role.USER, content="hello"),),
        )
        resp = await adapter.generate(request)
    finally:
        await client.aclose()

    assert resp.parsed is True
    assert resp.companion_turn is not None
    assert resp.companion_turn.decision is Decision.INTERVENE
    assert resp.token_usage is not None and resp.token_usage.total_tokens == 15
    assert captured["url"].endswith("/chat/completions")
    assert captured["headers"]["authorization"] == "Bearer sk-test"
    assert captured["payload"]["model"] == "some-model"
    assert captured["payload"]["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize(
    ("status", "retryable"), [(429, True), (500, True), (400, False), (404, False)]
)
async def test_openai_compatible_http_error_maps_to_provider_error(
    status: int, retryable: bool
) -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(status, text="boom"))
    client = httpx.AsyncClient(transport=transport)
    adapter = OpenAICompatibleAdapter(
        base_url="https://api.example.com/v1", api_key="k", client=client
    )
    try:
        with pytest.raises(ProviderResponseError) as excinfo:
            await adapter.generate(
                ChatRequest(
                    model=ModelSpec.parse("openai_compatible/m"),
                    messages=(ChatMessage(role=Role.USER, content="hi"),),
                )
            )
        assert excinfo.value.retryable is retryable
    finally:
        await client.aclose()


async def test_openai_adapter_requires_key() -> None:
    with pytest.raises(ProviderAuthError):
        OpenAIAdapter.from_env({})


async def test_openai_adapter_from_env_sets_defaults() -> None:
    adapter = OpenAIAdapter.from_env({"OPENAI_API_KEY": "sk-x"})
    try:
        assert adapter._base_url == "https://api.openai.com/v1"
        assert adapter.provider == "openai"
    finally:
        await adapter.aclose()


# --------------------------------------------------------------------------- Anthropic
async def test_openai_compatible_non_json_body_is_typed_error() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(200, text="<html>gateway</html>"))
    client = httpx.AsyncClient(transport=transport)
    adapter = OpenAICompatibleAdapter(base_url="https://x/v1", api_key="k", client=client)
    try:
        with pytest.raises(ProviderResponseError) as excinfo:
            await adapter.generate(
                ChatRequest(
                    model=ModelSpec.parse("openai_compatible/m"),
                    messages=(ChatMessage(role=Role.USER, content="hi"),),
                )
            )
        assert excinfo.value.retryable is False
    finally:
        await client.aclose()


async def test_openai_compatible_401_maps_to_auth_error() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(401, text="nope"))
    client = httpx.AsyncClient(transport=transport)
    adapter = OpenAICompatibleAdapter(base_url="https://x/v1", api_key="bad", client=client)
    try:
        with pytest.raises(ProviderAuthError):
            await adapter.generate(
                ChatRequest(
                    model=ModelSpec.parse("openai_compatible/m"),
                    messages=(ChatMessage(role=Role.USER, content="hi"),),
                )
            )
    finally:
        await client.aclose()


async def test_openai_compatible_list_content_is_joined() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": [{"type": "text", "text": '{"decision": "wait"}'}]}}
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = OpenAICompatibleAdapter(base_url="https://x/v1", api_key="k", client=client)
    try:
        resp = await adapter.generate(
            ChatRequest(
                model=ModelSpec.parse("openai_compatible/m"),
                messages=(ChatMessage(role=Role.USER, content="hi"),),
            )
        )
        assert resp.companion_turn is not None and resp.companion_turn.decision is Decision.WAIT
    finally:
        await client.aclose()


async def test_anthropic_non_dict_body_is_typed_error() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=[1, 2]))
    )
    adapter = AnthropicAdapter(api_key="k", client=client)
    try:
        with pytest.raises(ProviderResponseError):
            await adapter.generate(
                ChatRequest(
                    model=ModelSpec.parse("anthropic/c"),
                    messages=(ChatMessage(role=Role.USER, content="hi"),),
                )
            )
    finally:
        await client.aclose()


async def test_anthropic_tolerates_malformed_usage() -> None:
    # Regression: mismatched token types must not raise out of generate().
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": '{"decision": "wait"}'}],
                "usage": {"input_tokens": "12", "output_tokens": 5},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = AnthropicAdapter(api_key="k", client=client)
    try:
        resp = await adapter.generate(
            ChatRequest(
                model=ModelSpec.parse("anthropic/c"),
                messages=(ChatMessage(role=Role.USER, content="hi"),),
            )
        )
        assert resp.companion_turn is not None and resp.companion_turn.decision is Decision.WAIT
        assert resp.token_usage is None  # malformed usage tolerated, not crashed
    finally:
        await client.aclose()


async def test_anthropic_maps_system_and_parses_blocks() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": '{"decision": "wait", "message": ""}'}],
                "usage": {"input_tokens": 7, "output_tokens": 3},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = AnthropicAdapter(api_key="ant-key", client=client)
    try:
        request = ChatRequest(
            model=ModelSpec.parse("anthropic/claude-sonnet-4-6"),
            messages=(
                ChatMessage(role=Role.SYSTEM, content="You are a companion."),
                ChatMessage(role=Role.USER, content="hey"),
            ),
        )
        resp = await adapter.generate(request)
    finally:
        await client.aclose()

    assert resp.companion_turn is not None and resp.companion_turn.decision is Decision.WAIT
    assert resp.token_usage is not None and resp.token_usage.total_tokens == 10
    assert captured["url"].endswith("/v1/messages")
    assert captured["headers"]["x-api-key"] == "ant-key"
    assert captured["payload"]["system"] == "You are a companion."
    assert captured["payload"]["messages"] == [{"role": "user", "content": "hey"}]
