"""Command line interface for Radar Normativo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from radar_normativo.collector import collect_sources


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="radar-normativo",
        description="Raccoglie elementi da feed RSS/Atom configurati.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect = subparsers.add_parser(
        "collect", help="esegue una scansione delle fonti configurate"
    )
    collect.add_argument("--config", default="config/sources.json", help="percorso del file JSON delle fonti")
    collect.add_argument("--output", default="data/latest.json", help="percorso del JSON di output")
    args = parser.parse_args()

    if args.command == "collect":
        result = collect_sources(args.config)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        failed = sum(1 for source in result["source_results"] if not source["ok"])
        print(
            f"Scansione completata: {result['item_count']} elementi; "
            f"{failed} fonti con errori; output: {output}"
        )


if __name__ == "__main__":
    main()
