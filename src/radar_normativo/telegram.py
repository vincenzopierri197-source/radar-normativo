"""Invio del riepilogo giornaliero normativo e finanziario a Telegram."""
from __future__ import annotations
import hashlib,json,os,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Callable
from radar_normativo.briefing import render_briefing
from radar_normativo.finance import render_market_briefing
TELEGRAM_SAFE_LIMIT=3900
def _item_key(item:dict[str,Any])->str:
 if item.get("id"): return str(item["id"])
 identity=str(item.get("url") or item.get("title") or json.dumps(item,sort_keys=True))
 return hashlib.sha256(identity.encode()).hexdigest()[:24]
def _load_items(path:str|Path)->list[dict[str,Any]]:
 payload=json.loads(Path(path).read_text(encoding="utf-8"))
 items=payload if isinstance(payload,list) else payload.get("items") if isinstance(payload,dict) else None
 if not isinstance(items,list): raise ValueError("JSON deve contenere una lista o una chiave items")
 return [x for x in items if isinstance(x,dict)]
def _send_message(token:str,chat_id:str,text:str)->None:
 url=f"https://api.telegram.org/bot{token}/sendMessage"
 body=urllib.parse.urlencode({"chat_id":chat_id,"text":text,"disable_web_page_preview":"true"}).encode()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,data=body,method="POST"),timeout=20) as response: payload=json.loads(response.read().decode())
 except (urllib.error.URLError,TimeoutError,json.JSONDecodeError): raise RuntimeError("Invio Telegram non riuscito (rete o risposta non valida)") from None
 if not payload.get("ok"): raise RuntimeError(f"Telegram ha rifiutato il messaggio: {str(payload.get('description') or 'errore API')[:200]}")
def _render_chunks(items:list[dict[str,Any]],include_finance:bool)->list[tuple[list[dict[str,Any]],str]]:
 finance=render_market_briefing() if include_finance else ""
 if not items:
  text=("📡 RADAR NORMATIVO — RIEPILOGO GIORNALIERO\nNessuna nuova pubblicazione normativa rilevata oggi.\n\n"+finance) if include_finance else ""
  return [([],text)] if text else []
 chunks=[]; current=[]
 for item in items:
  candidate=current+[item]; msg=render_briefing(candidate,limit=len(candidate)).strip()
  if current and len(msg)>TELEGRAM_SAFE_LIMIT:
   chunks.append((current,render_briefing(current,limit=len(current)).strip())); current=[item]
  else: current=candidate
 if current: chunks.append((current,render_briefing(current,limit=len(current)).strip()))
 if finance:
  if len(chunks[-1][1])+len(finance)+4<=TELEGRAM_SAFE_LIMIT:
   a,b=chunks[-1]; chunks[-1]=(a,b+"\n\n"+finance)
  else: chunks.append(([],finance[:TELEGRAM_SAFE_LIMIT]))
 return chunks
def send_new_items(input_path:str|Path,ledger_path:str|Path,*,dry_run:bool=False,token:str|None=None,chat_id:str|None=None,sender:Callable[[str,str,str],None]|None=None,include_finance:bool=False)->dict[str,int]:
 items=_load_items(input_path); ledger=Path(ledger_path)
 if ledger.exists():
  payload=json.loads(ledger.read_text(encoding="utf-8")); sent_ids=payload.get("sent_ids",{})
  if not isinstance(sent_ids,dict): raise ValueError("Registro Telegram non valido")
 else: sent_ids={}
 pending=[(x,_item_key(x)) for x in items if _item_key(x) not in sent_ids]
 chunks=_render_chunks([x for x,_ in pending],include_finance)
 if dry_run:
  for _,msg in chunks: print(msg); print("---")
  return {"sent":0,"pending":len(pending),"skipped":len(items)-len(pending)}
 if not chunks: return {"sent":0,"pending":0,"skipped":len(items)}
 tok=token or os.environ.get("TELEGRAM_BOT_TOKEN"); chat=chat_id or os.environ.get("TELEGRAM_CHAT_ID")
 if not tok or not chat: raise ValueError("Configurare TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID, oppure usare --dry-run")
 send=sender or _send_message; ledger.parent.mkdir(parents=True,exist_ok=True); keys={_item_key(x):k for x,k in pending}; count=0
 for chunk_items,msg in chunks:
  send(tok,chat,msg)
  for item in chunk_items: sent_ids[keys[_item_key(item)]]=datetime.now(timezone.utc).isoformat(); count+=1
  if chunk_items: ledger.write_text(json.dumps({"schema_version":1,"sent_ids":sent_ids},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return {"sent":count,"pending":len(pending),"skipped":len(items)-len(pending)}
