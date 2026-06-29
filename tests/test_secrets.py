"""Secret handling: redaction, scanning, and proof that keys never reach artifacts."""

from __future__ import annotations

from pathlib import Path

import httpx

from companion_bench.adapters.openai_compatible import OpenAICompatibleAdapter
from companion_bench.runner.engine import RunEngine
from companion_bench.runner.events import model_call_event
from companion_bench.runner.manifest import load_manifest_and_tasks
from companion_bench.schemas.model import ChatMessage, ChatRequest, ModelSpec, Role
from companion_bench.utils.secrets import (
    collect_secret_values,
    redact,
    scan_run_dir,
    scan_text_for_secrets,
)
from companion_bench.utils.timing import FrozenClock

REPO_ROOT = Path(__file__).resolve().parents[1]
SMOKE = REPO_ROOT / "manifests" / "smoke.yaml"
FAKE_KEY = "sk-fake-SECRET-do-not-leak-1234567890"


def test_collect_only_takes_known_nontrivial_vars() -> None:
    env = {"OPENROUTER_API_KEY": FAKE_KEY, "OPENAI_API_KEY": "short", "UNRELATED": FAKE_KEY}
    values = collect_secret_values(env)
    assert FAKE_KEY in values  # from OPENROUTER_API_KEY
    assert "short" not in values  # too short
    assert len(values) == 1  # UNRELATED is not a secret var


def test_redact_and_scan() -> None:
    text = f"Authorization: Bearer {FAKE_KEY} trailing"
    assert FAKE_KEY not in redact(text, {FAKE_KEY})
    assert "***REDACTED***" in redact(text, {FAKE_KEY})
    assert scan_text_for_secrets(text, {FAKE_KEY}) == 1  # count, not the value
    assert scan_text_for_secrets("clean", {FAKE_KEY}) == 0


def test_adapter_repr_never_contains_key() -> None:
    adapter = OpenAICompatibleAdapter(base_url="https://x/v1", api_key=FAKE_KEY)
    assert FAKE_KEY not in repr(adapter)
    assert "x/v1" in repr(adapter)


async def test_key_never_reaches_a_serialized_event() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"decision":"wait"}'}}]}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = OpenAICompatibleAdapter(base_url="https://x/v1", api_key=FAKE_KEY, client=client)
    try:
        request = ChatRequest(
            model=ModelSpec.parse("openai_compatible/m"),
            messages=(ChatMessage(role=Role.USER, content="hi"),),
        )
        response = await adapter.generate(request)
    finally:
        await client.aclose()

    # The key WAS sent in the request header...
    assert captured["auth"] == f"Bearer {FAKE_KEY}"
    # ...but it must not appear in the serialized event written to events.jsonl.
    event = model_call_event(
        "run", FrozenClock(), "t", "p1", request.model, request.messages, response, attempts=1
    )
    assert FAKE_KEY not in event.model_dump_json()


async def test_full_mock_run_artifacts_contain_no_env_secret(tmp_path: Path) -> None:
    # A secret is present in the environment; a full offline run must not write it anywhere.
    manifest, tasks = load_manifest_and_tasks(SMOKE)
    engine = RunEngine(clock=FrozenClock(), env={"OPENROUTER_API_KEY": FAKE_KEY})
    result = await engine.run(
        manifest=manifest,
        tasks=tasks,
        model=ModelSpec.parse("mock/empathetic-v1"),
        config=manifest.run,
        out_dir=tmp_path / "run",
        manifest_path=str(SMOKE),
    )
    leaks = scan_run_dir(result.out_dir, {FAKE_KEY})
    assert leaks == {}, f"secret leaked into artifacts: {leaks}"
