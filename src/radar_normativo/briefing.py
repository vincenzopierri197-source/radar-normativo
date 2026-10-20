"""Generazione di schede testuali pronte per revisione e pubblicazione."""
from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

PRIORITY_LABELS = {
    "alta": "ALTA",
    "media": "MEDIA",
    "bassa": "BASSA",
}

CATEGORY_ORDER = [
    "🇮🇹 NORMATIVA ITALIANA",
    "⚖️ GIURISPRUDENZA",
    "🇪🇺 NORMATIVA EUROPEA",
    "🏛 ATTIVITÀ PARLAMENTARE",
    "📌 ALTRE FONTI",
]


def _plain_text(value: Any) -> str:
    """Riduce descrizioni RSS HTML a testo semplice."""
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _safe_http_url(value: Any) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


def _category(item: dict[str, Any]) -> str:
    source = _plain_text(item.get("source_name")).casefold()
    if "eur-lex" in source or "europe" in source or "europea" in source:
        return "🇪🇺 NORMATIVA EUROPEA"
    if "corte costituzionale" in source or "giurisprudenza" in source:
        return "⚖️ GIURISPRUDENZA"
    if "senato" in source or "camera dei deputati" in source or "parlament" in source:
        return "🏛 ATTIVITÀ PARLAMENTARE"
    if "gazzetta ufficiale" in source or "minister" in source:
        return "🇮🇹 NORMATIVA ITALIANA"
    return "📌 ALTRE FONTI"


def render_briefing(items: list[dict[str, Any]], limit: int = 10) -> str:
    """Crea un riepilogo raggruppato per materia, pronto per Telegram."""
    if limit < 1:
        raise ValueError("Il limite deve essere almeno 1")

    ordered = sorted(
        items,
        key=lambda item: (
            {"alta": 3, "media": 2, "bassa": 1}.get(str(item.get("priority", "bassa")), 0),
            int(item.get("relevance_score") or 0),
            str(item.get("published_at") or ""),
        ),
        reverse=True,
    )[:limit]

    today = datetime.now(ZoneInfo("Europe/Rome")).strftime("%d/%m/%Y")
    if not ordered:
        return f"📡 RADAR NORMATIVO — RIEPILOGO GIORNALIERO\n🗓 {today}\n\nNessuna nuova pubblicazione rilevata."

    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in CATEGORY_ORDER}
    for item in ordered:
        grouped[_category(item)].append(item)

    lines = [f"📡 RADAR NORMATIVO — RIEPILOGO GIORNALIERO", f"🗓 {today}", ""]
    index = 0
    for category in CATEGORY_ORDER:
        category_items = grouped[category]
        if not category_items:
            continue
        lines.extend([category, ""])
        for item in category_items:
            index += 1
            title = _plain_text(item.get("title")) or "Titolo non disponibile"
            priority = PRIORITY_LABELS.get(str(item.get("priority", "bassa")), "DA VALUTARE")
            score = item.get("relevance_score", 0)
            try:
                score = max(0, min(100, int(score)))
            except (TypeError, ValueError):
                score = 0

            topics = item.get("topics", [])
            if not isinstance(topics, list):
                topics = []
            topic_text = ", ".join(_plain_text(topic) for topic in topics if _plain_text(topic))
            published = _plain_text(item.get("published_at")) or "data non disponibile"
            source = _plain_text(item.get("source_name")) or "fonte non specificata"
            url = _safe_http_url(item.get("url"))
            summary = _plain_text(item.get("summary"))
            if len(summary) > 320:
                summary = summary[:317].rstrip() + "..."

            lines.append(f"{index}. [{priority} | {score}/100] {title}")
            lines.append(f"Materia: {topic_text or 'da classificare'}")
            lines.append(f"Data: {published}")
            lines.append(f"Fonte: {source}")
            if summary:
                lines.append(f"Sintesi: {summary}")
            lines.append("Stato giuridico: NON VERIFICATO")
            lines.append(f"Collegamento: {url or 'URL non disponibile'}")
            lines.append("")

    lines.append("Nota: priorità e classificazione sono automatiche; lo stato giuridico non è stato verificato.")
    return "\n".join(lines).strip() + "\n"
