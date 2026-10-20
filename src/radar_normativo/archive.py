"""Archivio storico e rilevamento delle nuove pubblicazioni."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def update_archive(
    latest_path: str | Path,
    archive_path: str | Path,
    new_items_path: str | Path,
) -> dict[str, Any]:
    """Unisce una scansione completa all'archivio, deduplicando per ID/URL."""
    latest_file = Path(latest_path)
    archive_file = Path(archive_path)
    new_file = Path(new_items_path)
    latest = json.loads(latest_file.read_text(encoding="utf-8"))

    failures = [
        source for source in latest.get("source_results", [])
        if not source.get("ok", False)
    ]
    if failures:
        names = ", ".join(str(source.get("name", "fonte sconosciuta")) for source in failures)
        raise ValueError(f"Archivio non aggiornato: scansione incompleta ({names})")

    scan_time = latest.get("generated_at") or _now()
    if archive_file.exists():
        stored = json.loads(archive_file.read_text(encoding="utf-8"))
        existing_items = stored.get("items", [])
    else:
        existing_items = []

    items_by_id: dict[str, dict[str, Any]] = {}
    for item in existing_items:
        item_id = str(item.get("id") or hashlib.sha256(str(item.get("url", "")).encode()).hexdigest()[:20])
        items_by_id[item_id] = dict(item)

    newly_discovered: list[dict[str, Any]] = []
    for current in latest.get("items", []):
        item = dict(current)
        item_id = str(item.get("id") or hashlib.sha256(str(item.get("url", "")).encode()).hexdigest()[:20])
        if item_id in items_by_id:
            previous = items_by_id[item_id]
            first_seen = previous.get("first_seen_at", scan_time)
            seen_count = int(previous.get("seen_count", 1)) + 1
            previous.update(item)
            previous["first_seen_at"] = first_seen
            previous["last_seen_at"] = scan_time
            previous["seen_count"] = seen_count
        else:
            item["first_seen_at"] = scan_time
            item["last_seen_at"] = scan_time
            item["seen_count"] = 1
            items_by_id[item_id] = item
            newly_discovered.append(dict(item))

    all_items = sorted(
        items_by_id.values(),
        key=lambda item: (item.get("published_at") or "", item.get("title") or ""),
        reverse=True,
    )
    archive = {
        "schema_version": 1,
        "updated_at": scan_time,
        "item_count": len(all_items),
        "items": all_items,
    }
    new_scan = {
        "schema_version": 1,
        "generated_at": scan_time,
        "new_item_count": len(newly_discovered),
        "items": newly_discovered,
    }

    archive_file.parent.mkdir(parents=True, exist_ok=True)
    new_file.parent.mkdir(parents=True, exist_ok=True)
    archive_file.write_text(json.dumps(archive, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    new_file.write_text(json.dumps(new_scan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "archive_count": len(all_items),
        "new_item_count": len(newly_discovered),
        "archive_path": str(archive_file),
        "new_items_path": str(new_file),
    }
