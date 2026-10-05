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


def test_brain_routes_listing_draft_request() -> None:
    brain = HermesBrain()

    decision = brain.analyse(
        "Generate a listing draft for this vintage Seiko watch.",
        {"brand": "Seiko", "condition": "good", "photos": ["front.jpg"]},
    )

    assert decision["task_type"] == "listing_draft"
    assert decision["specialist"] == "LISTING DRAFTER"
    assert decision["needs_approval"] is True
    assert "listing draft" in decision["next_step"].lower()


def test_brain_routes_freebuff_logarhythm_work_to_bridge() -> None:
    brain = HermesBrain()

    decision = brain.analyse("Bring the LOGARHYTHM work from Freebuff into Fridge Brain safely.")

    assert decision["task_type"] == "freebuff_bridge"
    assert decision["specialist"] == "LOGARHYTHM BRIDGE"
    assert decision["needs_approval"] is True
    assert "read-only" in decision["next_step"].lower()


def test_brain_routes_listing_draft_via_metadata() -> None:
    brain = HermesBrain()

    decision = brain.analyse(
        "Process this item.",
        {"listing_draft": True, "brand": "Nike", "condition": "new", "size": "10", "photos": ["side.jpg"]},
    )

    assert decision["task_type"] == "listing_draft"
    assert decision["specialist"] == "LISTING DRAFTER"
    assert decision["missing_information"] == []


def test_brain_listing_draft_missing_info_flags_approval() -> None:
    brain = HermesBrain()

    decision = brain.analyse(
        "Create a listing description for this jacket.",
        {},
    )

    assert decision["task_type"] == "listing_draft"
    assert decision["specialist"] == "LISTING DRAFTER"
    assert "condition" in decision["missing_information"]
    assert "brand" in decision["missing_information"]
    assert decision["needs_approval"] is True


def test_memory_store_tracks_context_events(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HERMES_DATA_DIR", str(tmp_path / "runtime"))
    module = importlib.reload(memory_store)

    module.update_memory({"task_type": "resale"}, {"result": {"status": "ready"}})
    profile = module.read_context_profile()

    assert profile["event_count"] == 1
    assert profile["recent"][-1]["task_type"] == "resale"
    assert profile["last_event"]["task_type"] == "resale"
