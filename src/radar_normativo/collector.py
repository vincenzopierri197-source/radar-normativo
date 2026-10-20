"""Raccolta generica RSS/Atom; non determina lo stato giuridico degli atti."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import feedparser


def _first_text(entry: Any, *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if value:
            return str(value).strip()
    return ""


def _entry_date(entry: Any) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        from time import struct_time, strftime, gmtime, mktime
        # feedparser supplies a UTC-like struct_time for parsed feed dates.
        return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc).isoformat()
    return _first_text(entry, "published", "updated") or None


def collect_sources(config_path: str | Path) -> dict[str, Any]:
    """Legge i feed configurati e restituisce una scansione serializzabile."""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    items: dict[str, dict[str, Any]] = {}
    source_results: list[dict[str, Any]] = []

    for source in config.get("sources", []):
        name = str(source.get("name", "Fonte senza nome"))
        url = str(source.get("url", "")).strip()
        if not url:
            source_results.append({"name": name, "ok": False, "error": "URL mancante"})
            continue
        try:
            feed = feedparser.parse(url)
            if getattr(feed, "bozo", False) and not feed.entries:
                raise ValueError(str(getattr(feed, "bozo_exception", "feed non leggibile")))
            count = 0
            for entry in feed.entries:
                link = _first_text(entry, "link")
                title = _first_text(entry, "title")
                if not link or not title:
                    continue
                stable_key = link.strip()
                item_id = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:20]
                items[item_id] = {
                    "id": item_id,
                    "title": title,
                    "url": link,
                    "source_name": name,
                    "source_url": url,
                    "published_at": _entry_date(entry),
                    "summary": _first_text(entry, "summary", "description"),
                    "language": source.get("language"),
                    "topics": [],
                    "legal_status": "non_verificato",
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                count += 1
            source_results.append({"name": name, "ok": True, "items": count})
        except Exception as exc:  # keep other sources running if one feed fails
            source_results.append({"name": name, "ok": False, "error": str(exc)[:300]})

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(items),
        "source_results": source_results,
        "items": sorted(items.values(), key=lambda item: (item.get("published_at") or "", item["title"]), reverse=True),
    }
