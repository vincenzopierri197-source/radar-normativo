"""Invio opzionale di nuove schede a Telegram tramite Bot API."""
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
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Invio Telegram non riuscito (rete o risposta non valida)") from None
    if not payload.get("ok"):
        description = str(payload.get("description") or "errore API")
        # La risposta API non dovrebbe contenere il token, ma non viene mai stampato l'URL.
        raise RuntimeError(f"Telegram ha rifiutato il messaggio: {description[:200]}")


def send_new_items(
    input_path: str | Path,
    ledger_path: str | Path,
    *,
    dry_run: bool = False,
    token: str | None = None,
    chat_id: str | None = None,
    sender: Callable[[str, str, str], None] | None = None,
) -> dict[str, int]:
    """Invia solo elementi non presenti nel registro persistente degli invii."""
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

    if dry_run:
        for item, _ in pending:
            print(render_briefing([item], limit=1).rstrip())
            print("---")
        return {"sent": 0, "pending": len(pending), "skipped": len(items) - len(pending)}

    resolved_token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    resolved_chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not resolved_token or not resolved_chat:
        raise ValueError(
            "Configurare TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID, oppure usare --dry-run"
        )

    send = sender or _send_message
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    sent_count = 0
    for item, key in pending:
        message = render_briefing([item], limit=1)
        # Telegram consente al massimo 4096 caratteri per messaggio.
        if len(message) > 3900:
            message = message[:3897].rstrip() + "..."
        send(resolved_token, resolved_chat, message)
        sent_ids[key] = datetime.now(timezone.utc).isoformat()
        ledger_file.write_text(
            json.dumps(
                {"schema_version": 1, "sent_ids": sent_ids},
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        sent_count += 1

    return {
        "sent": sent_count,
        "pending": len(pending),
        "skipped": len(items) - len(pending),
    }
