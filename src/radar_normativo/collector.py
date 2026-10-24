"""Raccolta RSS/Atom; non determina lo stato giuridico degli atti."""
from __future__ import annotations

import hashlib
import json
import posixpath
import re
from calendar import timegm
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit

import feedparser

from radar_normativo.analysis import analyze_item
from radar_normativo.classifier import classify_topics


def _first_text(entry: Any, *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if value:
            return str(value).strip()
    return ""


def _canonical_url(value: str) -> str:
    """Normalizza URL senza cambiare query o identificatori dell'atto."""
    value = value.strip()
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return value
    path = posixpath.normpath(parts.path or "/")
    if parts.path.endswith("/") and not path.endswith("/"):
        path += "/"
    if parts.path.startswith("/") and not path.startswith("/"):
        path = "/" + path
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, parts.fragment))


def _entry_title(entry: Any) -> str:
    """Rimuove il prefisso CELEX ridondante solo se dopo c'è un vero titolo."""
    title = _first_text(entry, "title")
    match = re.match(r"^CELEX:[^:]+:\s*(.+?)\s*$", title, flags=re.IGNORECASE)
    if match:
        cleaned_title = match.group(1).strip()
        if cleaned_title:
            return cleaned_title
    return title


def _entry_summary(entry: Any) -> str:
    summary = _first_text(entry, "summary", "description")
    if summary:
        return summary
    content = entry.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("value"):
                return str(part["value"]).strip()
    return ""


def _entry_date(entry: Any) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc).isoformat()
    return _first_text(entry, "published", "updated") or None


def _parse_feed(url: str) -> Any:
    """Scarica un feed con timeout e User-Agent espliciti, poi lo analizza."""
    request = Request(
        url,
        headers={
            "User-Agent": "RadarNormativo/1.0 (+https://github.com/vincenzopierri197-source/radar-normativo)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urlopen(request, timeout=25) as response:
            status = getattr(response, "status", 200)
            if status < 200 or status >= 300:
                raise RuntimeError(f"HTTP {status} durante il download del feed")
            payload = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} durante il download del feed") from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"errore di rete durante il download del feed: {reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("timeout durante il download del feed (25 secondi)") from exc

    if not payload.strip():
        raise ValueError("il server ha restituito una risposta vuota")
    return feedparser.parse(payload)


def collect_sources(config_path: str | Path) -> dict[str, Any]:
    """Legge i feed configurati e restituisce una scansione serializzabile."""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    items: dict[str, dict[str, Any]] = {}
    source_results: list[dict[str, Any]] = []

    for source in config.get("sources", []):
        name = str(source.get("name", "Fonte senza nome"))
        url = str(source.get("url", "")).strip()
        if not url:
            source_results.append({"name": name, "ok": False, "required": source.get("required", True), "error": "URL mancante"})
            continue
        try:
            feed = _parse_feed(url)
            if getattr(feed, "bozo", False) and not feed.entries:
                raise ValueError(f"RSS/Atom non valido: {getattr(feed, 'bozo_exception', 'errore di parsing sconosciuto')}")
            count = 0
            for entry in feed.entries:
                link = _canonical_url(_first_text(entry, "link"))
                title = _entry_title(entry)
                if not link or not title:
                    continue
                item_id = hashlib.sha256(link.encode("utf-8")).hexdigest()[:20]
                summary = _entry_summary(entry)
                item = {
                    "id": item_id,
                    "title": title,
                    "url": link,
                    "source_name": name,
                    "source_url": url,
                    "published_at": _entry_date(entry),
                    "summary": summary,
                    "language": source.get("language"),
                    "topics": classify_topics(title, summary),
                    "legal_status": "non_verificato",
                    "detection_status": "rilevato_da_feed",
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                items[item_id] = analyze_item(item)
                count += 1
            source_results.append({"name": name, "ok": True, "required": source.get("required", True), "items": count})
        except Exception as exc:
            source_results.append({"name": name, "ok": False, "required": source.get("required", True), "error": f"{type(exc).__name__}: {exc}"[:300]})

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "item_count": len(items),
        "source_results": source_results,
        "items": sorted(
            items.values(),
            key=lambda item: (item.get("published_at") or "", item["title"]),
            reverse=True,
        ),
    }
