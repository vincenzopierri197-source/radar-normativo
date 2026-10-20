"""Command line interface for Radar Normativo."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from radar_normativo.archive import update_archive
from radar_normativo.briefing import render_briefing
from radar_normativo.bot import run_bot
from radar_normativo.collector import collect_sources
from radar_normativo.telegram import send_new_items
def main()->None:
 parser=argparse.ArgumentParser(prog="radar-normativo",description="Monitoraggio normativo e finanziario.")
 subs=parser.add_subparsers(dest="command",required=True)
 collect=subs.add_parser("collect",help="raccoglie le fonti"); collect.add_argument("--config",default="config/sources.json"); collect.add_argument("--output",default="data/latest.json")
 archive=subs.add_parser("archive",help="aggiorna archivio"); archive.add_argument("--latest",default="data/latest.json"); archive.add_argument("--archive",dest="archive_path",default="data/archive.json"); archive.add_argument("--new-items",default="data/new_items.json")
 briefing=subs.add_parser("briefing",help="genera briefing normativo"); briefing.add_argument("--input",default="data/new_items.json"); briefing.add_argument("--output",default="data/briefing.txt"); briefing.add_argument("--limit",type=int,default=10)
 telegram=subs.add_parser("telegram",help="invia il riepilogo Telegram"); telegram.add_argument("--input",default="data/new_items.json"); telegram.add_argument("--ledger",default="data/telegram_sent.json"); telegram.add_argument("--dry-run",action="store_true"); telegram.add_argument("--finance",action="store_true",help="include quotazioni e valutazione dei mercati")
 bot=subs.add_parser("bot",help="avvia il bot Telegram interattivo"); bot.add_argument("--archive",dest="archive_path",default="data/archive.json"); bot.add_argument("--sources",dest="sources_path",default="config/sources.json"); bot.add_argument("--state",dest="state_path",default="data/bot_state.json"); bot.add_argument("--latest",dest="latest_path",default="data/latest.json")
 args=parser.parse_args()
 if args.command=="collect":
  result=collect_sources(args.config); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); failed=sum(not s["ok"] for s in result["source_results"]); print(f"Scansione: {result['item_count']} elementi; {failed} fonti con errori; output: {out}")
 elif args.command=="archive":
  result=update_archive(args.latest,args.archive_path,args.new_items); print(f"Archivio: {result['archive_count']} elementi; {result['new_item_count']} nuovi.")
 elif args.command=="briefing":
  payload=json.loads(Path(args.input).read_text(encoding="utf-8")); items=payload if isinstance(payload,list) else payload.get("items",[]) if isinstance(payload,dict) else []; out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(render_briefing(items,limit=args.limit),encoding="utf-8"); print(f"Briefing generato: {len(items)} elementi; {out}")
 elif args.command=="telegram":
  result=send_new_items(args.input,args.ledger,dry_run=args.dry_run,include_finance=args.finance); mode="simulazione" if args.dry_run else "invio"; print(f"Telegram ({mode}): {result['sent']} schede inviate; {result['pending']} nuove; {result['skipped']} già registrate.")
 elif args.command=="bot": run_bot(archive_path=args.archive_path,sources_path=args.sources_path,state_path=args.state_path,latest_path=args.latest_path)
if __name__=="__main__": main()
