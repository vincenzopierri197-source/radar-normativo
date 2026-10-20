"""Command line interface for Radar Normativo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from radar_normativo.archive import update_archive
from radar_normativo.briefing import render_briefing
from radar_normativo.bot import run_bot
from radar_normativo.collector import collect_sources
from radar_normativo.telegram import send_new_items


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="radar-normativo",
        description="Raccoglie e archivia elementi da feed RSS/Atom configurati.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect", help="esegue una scansione delle fonti configurate")
    collect.add_argument("--config", default="config/sources.json", help="percorso del JSON delle fonti")
    collect.add_argument("--output", default="data/latest.json", help="percorso del JSON di output")

    archive = subparsers.add_parser("archive", help="aggiorna l'archivio e identifica nuove pubblicazioni")
    archive.add_argument("--latest", default="data/latest.json", help="scansione JSON da archiviare")
    archive.add_argument("--archive", dest="archive_path", default="data/archive.json", help="archivio storico")
    archive.add_argument("--new-items", default="data/new_items.json", help="pubblicazioni nuove della scansione")

    briefing = subparsers.add_parser("briefing", help="genera un briefing testuale pronto per revisione")
    briefing.add_argument("--input", default="data/new_items.json", help="JSON con lista items o singoli elementi")
    briefing.add_argument("--output", default="data/briefing.txt", help="file testuale generato")
    briefing.add_argument("--limit", type=int, default=10, help="numero massimo di schede")

    telegram = subparsers.add_parser("telegram", help="invia nuove schede Telegram o simula l'invio")
    telegram.add_argument("--input", default="data/new_items.json", help="JSON con le nuove schede")
    telegram.add_argument("--ledger", default="data/telegram_sent.json", help="registro locale degli invii")
    telegram.add_argument("--dry-run", action="store_true", help="mostra i messaggi senza inviarli né registrarli")

    bot = subparsers.add_parser("bot", help="avvia il bot Telegram interattivo (processo sempre attivo)")
    bot.add_argument("--archive", dest="archive_path", default="data/archive.json", help="archivio storico")
    bot.add_argument("--sources", dest="sources_path", default="config/sources.json", help="fonti configurate")
    bot.add_argument("--state", dest="state_path", default="data/bot_state.json", help="stato persistente dei filtri")
    bot.add_argument("--latest", dest="latest_path", default="data/latest.json", help="risultati dell'ultima scansione, se disponibili")

    args = parser.parse_args()

    if args.command == "collect":
        result = collect_sources(args.config)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        failed = sum(1 for source in result["source_results"] if not source["ok"])
        print(f"Scansione completata: {result['item_count']} elementi; {failed} fonti con errori; output: {output}")
    elif args.command == "archive":
        result = update_archive(args.latest, args.archive_path, args.new_items)
        print(f"Archivio aggiornato: {result['archive_count']} elementi totali; {result['new_item_count']} nuove pubblicazioni.")
    elif args.command == "briefing":
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
            items = payload["items"]
        else:
            parser.error("Il JSON deve contenere una lista di elementi oppure una chiave 'items'")
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_briefing(items, limit=args.limit), encoding="utf-8")
        print(f"Briefing generato: {len(items)} elementi disponibili; file: {output}")
    elif args.command == "telegram":
        result = send_new_items(args.input, args.ledger, dry_run=args.dry_run)
        mode = "simulazione" if args.dry_run else "invio"
        print(f"Telegram ({mode}): {result['sent']} inviati; {result['pending']} in coda; {result['skipped']} già registrati.")
    elif args.command == "bot":
        run_bot(
            archive_path=args.archive_path,
            sources_path=args.sources_path,
            state_path=args.state_path,
            latest_path=args.latest_path,
        )


if __name__ == "__main__":
    main()
