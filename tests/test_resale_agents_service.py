from __future__ import annotations

import importlib
from pathlib import Path

from resale_agents.service import ResaleAgentService


def test_resale_service_captures_and_completes_approval_flow(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HERMES_DATA_DIR", str(tmp_path / "runtime"))
    service = ResaleAgentService()

    captured = service.capture_item(
        {
            "title": "Vintage Seiko Watch",
            "brand": "Seiko",
            "condition": "good",
            "photos": ["front.jpg", "back.jpg"],
        }
    )
    item_id = captured["data"]["item"]["item_id"]

    draft = service.run_until_approval(item_id)
    assert draft["data"]["approval_required"] is True
    assert draft["data"]["listing"]["platform"] == "eBay"
    assert "approval" in draft["data"]["next_step"]

    approved = service.approve_item(item_id, note="Looks good")
    assert approved["status"] == "ok"

    ready = service.run_until_approval(item_id)
    assert ready["data"]["approval_required"] is False
    assert ready["data"]["listing"]["status"] == "ready_to_post"
    assert ready["data"]["listing"]["specialist"] == "RESALE AGENT"

    health = service.health()
    assert health["status"] == "ok"
    assert health["inventory_count"] == 1
    assert health["pending_approvals"] >= 0
