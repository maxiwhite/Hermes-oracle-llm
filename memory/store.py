from datetime import datetime
from pathlib import Path
from typing import Any

from runtime_state import append_text, atomic_write_json, ensure_runtime_state


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_NAMESPACE = "hermes_brain"


def _runtime_paths():
    runtime = ensure_runtime_state(REPO_ROOT)
    return runtime.memory_dir / "structured.json", runtime.logs_dir / "sessions.md"


def _read_structured_payload() -> dict[str, Any]:
    structured_path, _ = _runtime_paths()
    try:
        import json

        with structured_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except (FileNotFoundError, OSError, ValueError):
        return {}


def _write_structured_payload(payload: dict[str, Any]) -> None:
    structured_path, _ = _runtime_paths()
    atomic_write_json(structured_path, payload)


def _summarize_value(value: Any, limit: int = 240) -> Any:
    if isinstance(value, dict):
        summary: dict[str, Any] = {}
        for key in (
            "result",
            "message",
            "provider",
            "model",
            "mode",
            "specialist",
            "route",
            "task_type",
            "status",
            "action",
            "action_result",
            "next_action",
            "service",
            "inventory_count",
            "pending_approvals",
            "latest_item_id",
        ):
            if key in value:
                summary[key] = _summarize_value(value[key], limit)
        if summary:
            return summary
        return {key: _summarize_value(item, limit) for key, item in list(value.items())[:8]}
    if isinstance(value, list):
        return [_summarize_value(item, limit) for item in value[:8]]
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def read_memory(prompt):
    return _read_structured_payload()


def append_context_event(namespace: str, event: dict[str, Any], *, limit: int = 100) -> dict[str, Any]:
    data = _read_structured_payload()
    context = data.setdefault(namespace, {})
    if not isinstance(context, dict):
        context = {}
        data[namespace] = context

    events = context.setdefault("events", [])
    if not isinstance(events, list):
        events = []
        context["events"] = events

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **{key: _summarize_value(value) for key, value in event.items()},
    }
    events.append(entry)
    if len(events) > limit:
        del events[:-limit]

    context["last_event"] = entry
    context["event_count"] = len(events)
    data[namespace] = context
    _write_structured_payload(data)
    return entry


def read_context_profile(namespace: str = DEFAULT_CONTEXT_NAMESPACE, *, limit: int = 5) -> dict[str, Any]:
    data = _read_structured_payload()
    context = data.get(namespace, {})
    if not isinstance(context, dict):
        context = {}
    events = context.get("events", [])
    if not isinstance(events, list):
        events = []
    return {
        "namespace": namespace,
        "event_count": int(context.get("event_count", len(events))),
        "recent": events[-limit:],
        "last_event": context.get("last_event"),
        "task_summaries": {key: _summarize_value(value) for key, value in data.items() if key != namespace},
    }


def update_memory(prompt, response):
    data = _read_structured_payload()

    key = prompt["task_type"]
    data[key] = response
    data["last_task_type"] = key
    data["last_response"] = _summarize_value(response)

    _write_structured_payload(data)
    append_context_event(
        DEFAULT_CONTEXT_NAMESPACE,
        {
            "task_type": key,
            "prompt": {"task_type": key},
            "response": _summarize_value(response),
        },
    )


def log_session(user_input, output):
    _, log_path = _runtime_paths()
    append_text(
        log_path,
        f"\n[{datetime.now()}]\nINPUT: {user_input}\nOUTPUT: {output}\n",
        redact=True,
    )
