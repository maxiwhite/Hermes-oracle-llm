from __future__ import annotations

from core import executor
from llm import client as llm_client


def test_execute_task_preserves_raw_simple_chat_and_skips_memory(monkeypatch):
    captured = {}

    class FakeRouter:
        def __init__(self, *args, memory_reader, **kwargs):
            self.memory_reader = memory_reader

        def run_task(self, user_input, infer):
            plan = {"task_route": "simple_chat"}
            captured["memory"] = self.memory_reader(plan)
            return {
                "source": "model",
                **infer(
                    {
                        "provider": {
                            "name": "lmstudio_windows",
                            "provider": {"base_url": "http://127.0.0.1:1234/v1"},
                        },
                        "model": "hermes-free",
                        "task_route": "simple_chat",
                        "params": {},
                        "memory": captured["memory"],
                        "repo_index": None,
                    }
                ),
            }

    def fake_call_model(prompt, route, config):
        captured["prompt"] = prompt
        return {
            "result": "ORANGE FALCON 5531",
            "meta": {"mode": "local", "provider": "lmstudio_windows", "model": route["model"]},
        }

    monkeypatch.setattr(executor, "ModelRouter", FakeRouter)
    monkeypatch.setattr(executor, "call_model", fake_call_model)
    monkeypatch.setattr(executor, "read_memory", lambda _compressed: {"poisoned": "stale output"})
    monkeypatch.setattr(executor, "update_memory", lambda *_args, **_kwargs: None)

    result = executor.execute_task(
        "Reply with exactly: ORANGE FALCON 5531",
        {"cloud_enabled": False},
    )

    assert captured["memory"] == {}
    assert captured["prompt"]["task"]["compressed_prompt"] == "Reply with exactly: ORANGE FALCON 5531"
    assert captured["prompt"]["raw_chat"] is True
    assert "T:text_reasoning" not in captured["prompt"]["task"]["compressed_prompt"]
    assert result["result"] == "ORANGE FALCON 5531"


def test_raw_chat_preserves_safety_system_message_and_exact_user_text():
    prompt = {
        "task": {
            "goal": "Reply with exactly: SILVER COMET 8274",
            "compressed_prompt": "Reply with exactly: SILVER COMET 8274",
        },
        "raw_chat": True,
        "memory": {"stale": "must not be injected"},
    }

    messages = llm_client._messages_for_local_runtime(prompt)

    assert messages[0]["role"] == "system"
    assert "avoid unsafe or unverified actions" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Reply with exactly: SILVER COMET 8274"}
    assert "stale" not in messages[1]["content"]


def test_native_chat_accepts_raw_user_text_with_safety_system_message(monkeypatch):
    requests = []

    def request(url, **kwargs):
        requests.append((url, kwargs))
        if url.endswith("/models"):
            return {"data": [{"id": "hermes-free"}]}
        return {"output": [{"type": "message", "content": "LOCAL READY"}]}

    monkeypatch.setattr(llm_client, "_request_json", request)

    result = llm_client._openai_compatible_local_response(
        {
            "task": {"compressed_prompt": "Reply exactly: LOCAL READY"},
            "raw_chat": True,
        },
        "lmstudio_windows",
        {"base_url": "http://localhost:1234/v1", "native_chat": True},
        "hermes-free",
        {"max_tokens": 32},
    )

    assert result["result"] == "LOCAL READY"
    payload = requests[-1][1]["payload"]
    assert payload["input"] == "Reply exactly: LOCAL READY"
    assert "avoid unsafe or unverified actions" in payload["system_prompt"]
