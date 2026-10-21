"""Polling Telegram per i comandi interattivi di Radar Normativo.

Il processo deve restare in esecuzione su un host sempre acceso; GitHub Actions
continua a occuparsi della raccolta programmata e non ospita questo polling.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from radar_normativo.finance import render_market_briefing

ROME = ZoneInfo("Europe/Rome")
HELP = """Comandi Radar Normativo:
/start — avvia il bot
/ultime — ultime pubblicazioni
/oggi — novità pubblicate oggi
/ieri — pubblicazioni di ieri
/ultimi7giorni — pubblicazioni degli ultimi 7 giorni
/cerca parola — cerca nei titoli e nelle sintesi
/fonti — fonti configurate
/filtri — mostra i filtri; /filtri parola1, parola2 per impostarli; /filtri off per disattivarli
/stato — stato dell'archivio e delle fonti
/mercati — quotazioni e valutazione dei nove strumenti finanziari
/aiuto — mostra questo elenco

Nota: le schede sono rilevazioni automatiche, non certificazioni di vigenza."""


def _read_json(path: str | Path, default: Any) -> Any:
    file = Path(path)
    if not file.exists():
        return default
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: str | Path, payload: Any) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _items(archive_path: str | Path) -> list[dict[str, Any]]:
    payload = _read_json(archive_path, {})
    values = payload.get("items", []) if isinstance(payload, dict) else []
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _published_date(item: dict[str, Any]) -> date | None:
    value = str(item.get("published_at") or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(ROME).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _filters(state: dict[str, Any], chat_id: str) -> list[str]:
    value = state.get("filters", {}).get(chat_id, [])
    return [str(term).strip().casefold() for term in value if str(term).strip()] if isinstance(value, list) else []


def _matches_filter(item: dict[str, Any], terms: list[str]) -> bool:
    if not terms:
        return True
    topics = item.get("topics", [])
    text = " ".join([
        str(item.get("title") or ""),
        str(item.get("summary") or ""),
        str(item.get("source_name") or ""),
        " ".join(str(topic) for topic in topics) if isinstance(topics, list) else str(topics),
    ]).casefold()
    return any(term in text for term in terms)


def _format_items(items: list[dict[str, Any]], empty: str, limit: int = 10) -> str:
    if not items:
        return empty
    rows = []
    for index, item in enumerate(items[:limit], start=1):
        title = str(item.get("title") or "Titolo non disponibile").strip()
        url = str(item.get("url") or "").strip()
        source = str(item.get("source_name") or "Fonte non indicata").strip()
        published = str(item.get("published_at") or "data non indicata").strip()
        # Evita messaggi troppo lunghi e mantiene ogni scheda verificabile tramite il link.
        title = title[:220]
        rows.append(f"{index}. {title}\nFonte: {source} · Data: {published}" + (f"\n{url}" if url else ""))
    suffix = f"\n\nMostrate {min(len(items), limit)} di {len(items)} pubblicazioni." if len(items) > limit else ""
    return ("\n\n".join(rows) + suffix)[:3900]


def handle_command(
    text: str,
    chat_id: str | int,
    *,
    archive_path: str | Path = "data/archive.json",
    sources_path: str | Path = "config/sources.json",
    state_path: str | Path = "data/bot_state.json",
    latest_path: str | Path = "data/latest.json",
) -> str:
    """Elabora un comando senza chiamare la rete, così è testabile."""
    raw = text.strip()
    command, _, argument = raw.partition(" ")
    command = command.split("@", 1)[0].casefold()
    argument = argument.strip()
    chat_key = str(chat_id)
    state = _read_json(state_path, {})
    if not isinstance(state, dict):
        state = {}
    state.setdefault("filters", {})
    if not isinstance(state["filters"], dict):
        state["filters"] = {}

    if command == "/start":
        return "Radar Normativo è pronto. Usa /aiuto per vedere i comandi."
    if command == "/mercati":
        return render_market_briefing()
    if command in {"/aiuto", "/help"}:
        return HELP
    if command == "/filtri":
        if argument.casefold() == "off":
            state["filters"].pop(chat_key, None)
            _write_json(state_path, state)
            return "Filtri disattivati."
        if argument:
            terms = list(dict.fromkeys(term.strip() for term in argument.split(",") if term.strip()))
            if not terms:
                return "Scrivi i termini separati da virgola, oppure /filtri off."
            state["filters"][chat_key] = terms[:20]
            _write_json(state_path, state)
            return "Filtri salvati: " + ", ".join(state["filters"][chat_key])
        terms = _filters(state, chat_key)
        return "Filtri attivi: " + ", ".join(terms) if terms else "Nessun filtro attivo. Imposta con /filtri lavoro, fisco oppure usa /filtri off."
    if command == "/fonti":
        config = _read_json(sources_path, {})
        sources = config.get("sources", []) if isinstance(config, dict) else []
        if not sources:
            return "Non riesco a leggere le fonti configurate."
        return "Fonti configurate:\n" + "\n".join(
            f"• {source.get('name', 'Fonte senza nome')}\n  {source.get('url', '')}"
            for source in sources if isinstance(source, dict)
        )
    if command == "/stato":
        archive = _read_json(archive_path, {})
        latest = _read_json(latest_path, {})
        config = _read_json(sources_path, {})
        count = len(_items(archive_path))
        updated = archive.get("updated_at", "non disponibile") if isinstance(archive, dict) else "non disponibile"
        source_results = latest.get("source_results", []) if isinstance(latest, dict) else []
        if source_results:
            health = "\n".join(
                f"• {'OK' if source.get('ok') else 'ERRORE'} — {source.get('name', 'fonte')}"
                for source in source_results if isinstance(source, dict)
            )
            health = "\nStato ultima scansione:\n" + health
        else:
            health = "\nEsito dell'ultima scansione: non disponibile in questo ambiente."
        source_count = len(config.get("sources", [])) if isinstance(config, dict) else 0
        return f"Radar Normativo: processo comandi attivo.\nElementi in archivio: {count}\nArchivio aggiornato: {updated}\nFonti configurate: {source_count}{health}\nLo stato giuridico degli atti non è certificato automaticamente."
    if command == "/cerca":
        if not argument:
            return "Uso: /cerca parola o argomento"
        terms = [argument.casefold()]
        found = [
            item for item in _items(archive_path)
            if any(term in (str(item.get("title") or "") + " " + str(item.get("summary") or "")).casefold() for term in terms)
            and _matches_filter(item, _filters(state, chat_key))
        ]
        return _format_items(found, f"Nessun risultato per «{argument}».", limit=10)
    if command in {"/ultime", "/oggi", "/ieri", "/ultimi7giorni"}:
        items = _items(archive_path)
        items.sort(key=lambda item: str(item.get("published_at") or ""), reverse=True)
        filters = _filters(state, chat_key)
        items = [item for item in items if _matches_filter(item, filters)]
        today = datetime.now(ROME).date()
        if command == "/oggi":
            items = [item for item in items if _published_date(item) == today]
            heading = "Pubblicazioni di oggi"
        elif command == "/ieri":
            yesterday = today.fromordinal(today.toordinal() - 1)
            items = [item for item in items if _published_date(item) == yesterday]
            heading = f"Pubblicazioni di ieri ({yesterday.isoformat()})"
        elif command == "/ultimi7giorni":
            from datetime import timedelta
            start = today - timedelta(days=6)
            items = [item for item in items if (published := _published_date(item)) is not None and start <= published <= today]
            heading = f"Pubblicazioni ultimi 7 giorni ({start.isoformat()} — {today.isoformat()})"
        else:
            heading = "Ultime pubblicazioni"
        if not items and filters:
            return f"Nessuna pubblicazione trovata con i filtri attivi: {', '.join(filters)}."
        return heading + "\n\n" + _format_items(items, "Nessuna pubblicazione disponibile.", limit=10)
    return "Comando non riconosciuto. Usa /aiuto per l'elenco dei comandi."


def _api_call(token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = urllib.parse.urlencode(params).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("Chiamata Telegram non riuscita; controllare rete e configurazione.") from None
    if not isinstance(payload, dict) or not payload.get("ok"):
        raise RuntimeError("Telegram ha rifiutato la richiesta API.")
    return payload


def run_bot(
    *,
    archive_path: str = "data/archive.json",
    sources_path: str = "config/sources.json",
    state_path: str = "data/bot_state.json",
    latest_path: str = "data/latest.json",
) -> None:
    """Avvia il long polling: il processo deve restare attivo."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    allowed_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not allowed_chat:
        raise ValueError("Configurare TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nell'ambiente.")
    if not allowed_chat.lstrip("-").isdigit():
        raise ValueError("Per ricevere comandi, TELEGRAM_CHAT_ID deve essere l'ID numerico della chat privata.")
    # Pubblica il menu dei comandi nella UI Telegram, oltre a gestirli via polling.
    _api_call(token, "setMyCommands", {"commands": json.dumps([
        {"command": "start", "description": "Avvia il bot"},
        {"command": "ultime", "description": "Mostra le ultime pubblicazioni"},
        {"command": "oggi", "description": "Mostra le novità della giornata"},
        {"command": "ieri", "description": "Mostra le pubblicazioni di ieri"},
        {"command": "ultimi7giorni", "description": "Mostra le pubblicazioni degli ultimi 7 giorni"},
        {"command": "cerca", "description": "Cerca una parola o un argomento"},
        {"command": "fonti", "description": "Elenca le fonti monitorate"},
        {"command": "filtri", "description": "Configura gli argomenti d'interesse"},
        {"command": "stato", "description": "Mostra lo stato del sistema"},
        {"command": "mercati", "description": "Quotazioni e valutazione dei mercati"},
        {"command": "aiuto", "description": "Visualizza i comandi disponibili"},
    ])})
    offset = 0
    print("Bot Radar Normativo in ascolto. Interrompere con Ctrl+C.")
    while True:
        try:
            payload = _api_call(token, "getUpdates", {"timeout": 25, "offset": offset, "allowed_updates": '["message"]'})
            for update in payload.get("result", []):
                offset = max(offset, int(update.get("update_id", 0)) + 1)
                message = update.get("message") or {}
                chat = message.get("chat") or {}
                if str(chat.get("id", "")) != allowed_chat:
                    continue
                text = str(message.get("text") or "").strip()
                if not text.startswith("/"):
                    continue
                response = handle_command(
                    text, allowed_chat, archive_path=archive_path, sources_path=sources_path,
                    state_path=state_path, latest_path=latest_path,
                )
                _api_call(token, "sendMessage", {"chat_id": allowed_chat, "text": response, "disable_web_page_preview": "true"})
        except KeyboardInterrupt:
            print("Bot Radar Normativo arrestato.")
            return
        except Exception as exc:
            # Non stampa mai URL o token API.
            print(f"Errore temporaneo del bot: {str(exc)[:180]}")
            time.sleep(3)
