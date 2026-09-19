from __future__ import annotations

import importlib
import json
from pathlib import Path

from hermes_brain import HermesBrain
from memory import store as memory_store


def test_brain_routes_resale_request_to_specialist() -> None:
    brain = HermesBrain()

    decision = brain.analyse(
        "Please price this vintage watch for resale.",
        {"brand": "Seiko", "condition": "good", "photos": ["front.jpg"]},
    )

    assert decision["specialist"] == "RESALE AGENT"
    assert decision["task_type"] == "resale"
    assert decision["complexity_score"] > 10
    assert decision["needs_approval"] is True
    assert "listing draft" in decision["next_step"].lower() or "details" in decision["next_step"].lower()


def test_memory_store_tracks_context_events(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HERMES_DATA_DIR", str(tmp_path / "runtime"))
    module = importlib.reload(memory_store)

    module.update_memory({"task_type": "resale"}, {"result": {"status": "ready"}})
    profile = module.read_context_profile()

    assert profile["event_count"] == 1
    assert profile["recent"][-1]["task_type"] == "resale"
    assert profile["last_event"]["task_type"] == "resale"
