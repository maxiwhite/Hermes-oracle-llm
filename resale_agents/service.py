from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from hermes_brain import HermesBrain
from memory.store import update_memory
from oracle_v1.responses import error, ok
from runtime_state import atomic_write_json, resolve_data_root


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


class ResaleStore:
    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)
        self.resale_root = self.data_root / "resale"
        self.resale_root.mkdir(parents=True, exist_ok=True)
        self._ensure("inventory.json", [])
        self._ensure("approvals.json", [])
        self._ensure("events.json", [])

    def _ensure(self, name: str, default: Any) -> None:
        path = self.resale_root / name
        if not path.exists():
            atomic_write_json(path, default)

    def _read(self, name: str, default: Any) -> Any:
        path = self.resale_root / name
        try:
            payload = path.read_text(encoding="utf-8").strip()
            return default if not payload else __import__("json").loads(payload)
        except Exception:
            return default

    def _write(self, name: str, payload: Any) -> None:
        atomic_write_json(self.resale_root / name, payload)

    def inventory(self) -> list[dict[str, Any]]:
        return self._read("inventory.json", [])

    def approvals(self) -> list[dict[str, Any]]:
        return self._read("approvals.json", [])

    def events(self) -> list[dict[str, Any]]:
        return self._read("events.json", [])

    def save_inventory(self, items: list[dict[str, Any]]) -> None:
        self._write("inventory.json", items)

    def save_approvals(self, items: list[dict[str, Any]]) -> None:
        self._write("approvals.json", items)

    def save_events(self, items: list[dict[str, Any]]) -> None:
        self._write("events.json", items)


class ResaleAgentService:
    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root = Path(data_root or resolve_data_root())
        self.store = ResaleStore(self.data_root)
        self.brain = HermesBrain(memory_namespace="resale_brain")

    @classmethod
    def from_repo_root(cls) -> "ResaleAgentService":
        return cls(resolve_data_root())

    def health(self) -> dict[str, Any]:
        inventory = self.store.inventory()
        approvals = self.store.approvals()
        return {
            "status": "ok",
            "service": "resale-agents",
            "mode": "local-only",
            "inventory_count": len(inventory),
            "pending_approvals": sum(1 for item in approvals if item.get("status") == "pending"),
            "latest_item_id": inventory[-1]["item_id"] if inventory else None,
        }

    def _find_item(self, item_id: str) -> dict[str, Any] | None:
        return next((item for item in self.store.inventory() if item.get("item_id") == item_id), None)

    def _infer_category(self, item: dict[str, Any]) -> str:
        text = " ".join(str(item.get(key, "")) for key in ("title", "description", "brand", "condition", "notes")).lower()
        if any(token in text for token in ("watch", "gold", "silver", "jewellery", "jewelry", "ring", "chain")):
            return "accessories"
        if any(token in text for token in ("shoe", "trainer", "sneaker", "boot")):
            return "footwear"
        if any(token in text for token in ("jacket", "coat", "shirt", "dress", "trousers", "jeans")):
            return "clothing"
        if any(token in text for token in ("phone", "laptop", "console", "camera", "speaker", "electronic")):
            return "electronics"
        if any(token in text for token in ("chair", "table", "lamp", "furniture")):
            return "home"
        return str(item.get("category") or "general")

    def _choose_platform(self, category: str, item: dict[str, Any]) -> str:
        text = " ".join(str(item.get(key, "")) for key in ("title", "description", "brand", "condition")).lower()
        if category in {"clothing", "footwear"}:
            return "Vinted" if "designer" not in text else "Depop"
        if category in {"accessories", "electronics"}:
            return "eBay"
        if category == "home":
            return "Facebook Marketplace"
        return "eBay"

    def _estimate_value(self, category: str, item: dict[str, Any]) -> dict[str, Any]:
        base = {
            "clothing": 22,
            "footwear": 28,
            "accessories": 35,
            "electronics": 55,
            "home": 18,
            "general": 24,
        }.get(category, 24)
        condition = str(item.get("condition") or "").lower()
        multiplier = 1.0
        if any(token in condition for token in ("new", "unused", "excellent")):
            multiplier = 1.5
        elif any(token in condition for token in ("very good", "good")):
            multiplier = 1.2
        elif any(token in condition for token in ("fair", "used")):
            multiplier = 0.85
        low = round(base * multiplier * 0.8)
        high = round(base * multiplier * 1.2)
        recommended = round((low + high) / 2)
        return {"low": low, "high": high, "recommended": recommended, "currency": "GBP"}

    def _listing_title(self, item: dict[str, Any], category: str) -> str:
        parts = [str(item.get("brand") or "").strip(), str(item.get("title") or "").strip()]
        if not parts[0]:
            parts[0] = category.title()
        title = " ".join(part for part in parts if part)
        return re.sub(r"\s+", " ", title).strip()[:80]

    def _listing_description(self, item: dict[str, Any], category: str, missing: list[str], price: dict[str, Any]) -> str:
        pieces = [
            f"Category: {category}.",
            f"Condition: {item.get('condition') or 'not specified'}.",
            f"Recommended price: {price['currency']} {price['recommended']}.",
        ]
        if item.get("brand"):
            pieces.append(f"Brand: {item['brand']}.")
        if item.get("size"):
            pieces.append(f"Size: {item['size']}.")
        if missing:
            pieces.append("Missing details: " + ", ".join(missing) + ".")
        if item.get("photos"):
            pieces.append(f"Photos supplied: {len(item['photos'])}.")
        pieces.append("Approval required before publishing.")
        return " ".join(pieces)

    def _record_event(self, kind: str, item_id: str, details: dict[str, Any]) -> None:
        events = self.store.events()
        events.append(
            {
                "timestamp": utc_now(),
                "kind": kind,
                "item_id": item_id,
                "details": details,
            }
        )
        self.store.save_events(events)

    def capture_item(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title") or payload.get("name") or payload.get("text") or "").strip()
        if not title:
            return error("invalid_item", "Item capture requires at least a title, name, or text field.")

        item = {
            "item_id": str(payload.get("item_id") or f"resale-{_slug(title)}-{uuid4().hex[:8]}"),
            "title": title,
            "description": str(payload.get("description") or "").strip(),
            "brand": str(payload.get("brand") or "").strip() or None,
            "condition": str(payload.get("condition") or "").strip() or None,
            "size": str(payload.get("size") or "").strip() or None,
            "photos": list(payload.get("photos") or []),
            "source": str(payload.get("source") or "manual"),
            "status": "captured",
            "approval_state": "pending",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        inventory = self.store.inventory()
        inventory = [existing for existing in inventory if existing.get("item_id") != item["item_id"]]
        inventory.append(item)
        self.store.save_inventory(inventory)
        self._record_event("capture", item["item_id"], {"title": item["title"], "source": item["source"]})
        return ok({"item": item, "inventory_count": len(inventory)})

    def get_item(self, item_id: str) -> dict[str, Any]:
        item = self._find_item(item_id)
        if item is None:
            return error("not_found", f"Item '{item_id}' was not found.")
        return ok({"item": item})

    def list_tasks(self) -> list[dict[str, Any]]:
        return [item for item in self.store.inventory() if item.get("status") != "ready_to_post"]

    def list_approvals(self) -> list[dict[str, Any]]:
        return self.store.approvals()

    def approve_item(self, item_id: str, note: str = "") -> dict[str, Any]:
        item = self._find_item(item_id)
        if item is None:
            return error("not_found", f"Item '{item_id}' was not found.")
        item["approval_state"] = "approved"
        item["approval_note"] = note
        item["updated_at"] = utc_now()
        inventory = self.store.inventory()
        for index, existing in enumerate(inventory):
            if existing.get("item_id") == item_id:
                inventory[index] = item
                break
        self.store.save_inventory(inventory)
        approvals = self.store.approvals()
        approvals.append({"item_id": item_id, "status": "approved", "note": note, "created_at": utc_now()})
        self.store.save_approvals(approvals)
        self._record_event("approval", item_id, {"note": note, "status": "approved"})
        return ok({"item": item})

    def run_until_approval(self, item_id: str) -> dict[str, Any]:
        item = self._find_item(item_id)
        if item is None:
            return error("not_found", f"Item '{item_id}' was not found.")

        specialist = self.brain.route(f"Resale item workflow for {item.get('title', '')}", metadata={"resale": True, "inventory": True})
        category = self._infer_category(item)
        missing = [field for field in ("condition", "brand", "size") if not item.get(field)]
        if not item.get("photos"):
            missing.append("photos")
        price = self._estimate_value(category, item)
        platform = self._choose_platform(category, item)
        listing = {
            "item_id": item_id,
            "category": category,
            "platform": platform,
            "title": self._listing_title(item, category),
            "description": self._listing_description(item, category, missing, price),
            "price": price,
            "missing_information": missing,
            "approval_state": item.get("approval_state", "pending"),
            "specialist": specialist,
            "status": "ready_to_post" if item.get("approval_state") == "approved" else "approval_pending",
        }

        item["listing"] = listing
        item["status"] = listing["status"]
        item["updated_at"] = utc_now()
        item["category"] = category
        item["platform"] = platform
        item["price_recommendation"] = price
        inventory = self.store.inventory()
        for index, existing in enumerate(inventory):
            if existing.get("item_id") == item_id:
                inventory[index] = item
                break
        self.store.save_inventory(inventory)

        approval_needed = listing["status"] != "ready_to_post"
        if approval_needed:
            approvals = self.store.approvals()
            if not any(entry.get("item_id") == item_id for entry in approvals):
                approvals.append(
                    {
                        "item_id": item_id,
                        "status": "pending",
                        "note": "Human approval required before publishing.",
                        "created_at": utc_now(),
                    }
                )
                self.store.save_approvals(approvals)

        workflow = {
            "item": item,
            "listing": listing,
            "approval_required": approval_needed,
            "next_step": "human_approval" if approval_needed else "ready_to_post",
            "specialist": specialist,
        }
        self._record_event("workflow", item_id, workflow)
        update_memory({"task_type": "inventory"}, {"result": workflow})
        return ok(workflow)
