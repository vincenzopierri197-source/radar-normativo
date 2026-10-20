"""Invia un messaggio di prova a Telegram usando i GitHub Actions secrets."""
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        missing = []
        if not token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        print("Configurazione mancante: " + ", ".join(missing))
        return 2

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({
            "chat_id": chat_id,
            "text": "✅ Test Telegram riuscito! Il collegamento con radar-normativo è attivo."
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            result = json.loads(exc.read().decode("utf-8"))
            description = result.get("description", "errore HTTP")
        except (ValueError, OSError):
            description = "risposta HTTP non leggibile"
        print(f"Telegram ha risposto HTTP {exc.code}: {description}")
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Errore di connessione a Telegram: {exc}")
        return 1

    if result.get("ok") is True:
        print("SUCCESSO: Telegram ha accettato il messaggio di prova.")
        return 0

    print("Telegram ha rifiutato il messaggio: " + str(result.get("description", "errore sconosciuto")))
    return 1


if __name__ == "__main__":
    sys.exit(main())
