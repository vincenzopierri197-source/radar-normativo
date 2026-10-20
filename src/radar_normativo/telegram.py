"""Invio del riepilogo giornaliero delle nuove schede a Telegram."""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from radar_normativo.briefing import render_briefing

TELEGRAM_SAFE_LIMIT = 3900


def _item_key(item: dict[str, Any]) -> str:
    """Identificatore stabile usato per evitare invii ripetuti."""
    if item.get("id"):
        return str(item["id"])
    identity = str(item.get("url") or item.get("title") or json.dumps(item, sort_keys=True))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _load_items(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        items = payload["items"]
    else:
        raise ValueError("Il JSON deve contenere una lista di elementi oppure una chiave 'items'")
    return [item for item in items if isinstance(item, dict)]


def _send_message(token: str, chat_id: str, text: str) -> None:
    """Invia un messaggio senza esporre il token nei messaggi di errore."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("Invio Telegram non riuscito (rete o risposta non valida)") from None
    if not payload.get("ok"):
        description = str(payload.get("description") or "errore API")
        raise RuntimeError(f"Telegram ha rifiutato il messaggio: {description[:200]}")


def _render_chunks(items: list[dict[str, Any]]) -> list[tuple[list[dict[str, Any]], str]]:
    """Raggruppa tutte le notizie in messaggi compatti entro il limite Telegram."""
    chunks: list[tuple[list[dict[str, Any]], str]] = []
    current: list[dict[str, Any]] = []

    for item in items:
        candidate = current + [item]
        message = render_briefing(candidate, limit=len(candidate)).strip()
        if current and len(message) > TELEGRAM_SAFE_LIMIT:
            current_message = render_briefing(current, limit=len(current)).strip()
            chunks.append((current, current_message))
            current = [item]
        else:
            current = candidate

    if current:
        message = render_briefing(current, limit=len(current)).strip()
        if len(message) > TELEGRAM_SAFE_LIMIT:
            message = message[: TELEGRAM_SAFE_LIMIT - 3].rstrip() + "..."
        chunks.append((current, message))
    return chunks


def send_new_items(
    input_path: str | Path,
    ledger_path: str | Path,
    *,
    dry_run: bool = False,
    token: str | None = None,
    chat_id: str | None = None,
    sender: Callable[[str, str, str], None] | None = None,
) -> dict[str, int]:
    """Invia un riepilogo unico con tutte le nuove notizie, senza duplicati."""
    items = _load_items(input_path)
    ledger_file = Path(ledger_path)
    if ledger_file.exists():
        ledger_payload = json.loads(ledger_file.read_text(encoding="utf-8"))
        sent_ids = ledger_payload.get("sent_ids", {})
        if not isinstance(sent_ids, dict):
            raise ValueError("Registro Telegram non valido: 'sent_ids' deve essere un oggetto")
    else:
        sent_ids = {}

    pending = [(item, _item_key(item)) for item in items]
    pending = [(item, key) for item, key in pending if key not in sent_ids]
    pending_items = [item for item, _ in pending]
    chunks = _render_chunks(pending_items)

    if dry_run:
        for _, message in chunks:
            print(message)
            print("---")
        return {"sent": 0, "pending": len(pending), "skipped": len(items) - len(pending)}

    if not pending:
        return {"sent": 0, "pending": 0, "skipped": len(items)}

    resolved_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    resolved_chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not resolved_token or not resolved_chat:
        raise ValueError(
            "Configurare TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID, oppure usare --dry-run"
        )

    send = sender or _send_message
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    sent_count = 0
    keys_by_id = {_item_key(item): key for item, key in pending}
    for chunk_items, message in chunks:
        send(resolved_token, resolved_chat, message)
        for item in chunk_items:
            key = keys_by_id[_item_key(item)]
            sent_ids[key] = datetime.now(timezone.utc).isoformat()
            sent_count += 1
        ledger_file.write_text(
            json.dumps(
                {"schema_version": 1, "sent_ids": sent_ids},
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    return {
        "sent": sent_count,
        "pending": len(pending),
        "skipped": len(items) - len(pending),
    }
