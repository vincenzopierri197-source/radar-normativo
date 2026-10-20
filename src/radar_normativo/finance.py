"""Quote indicative per il riepilogo giornaliero dei mercati."""
from __future__ import annotations
import json, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo
ROME=ZoneInfo("Europe/Rome")
INSTRUMENTS=[
("Dow Jones Industrial Average","^DJI","USA"),
("JPMorgan Global Select Equity","JGLO","Globale"),
("UBS MSCI China A","CHINA.MI","Cina"),
("JPM China A-Share Opportunities","0P0001LMEZ.F","Cina"),
("Fidelity Global Industrials","0P0000CO6N.F","Industriali"),
("FTSE MIB","FTSEMIB.MI","Italia"),
("1ST SICAV - Italy I EUR Acc","0P0001BRM8.F","Italia"),
("India Globalization Capital","IGS1.SG","India"),
("Fidelity India Focus A-EUR","0P00000ZJK.F","India")]
def _fetch_chart(symbol:str)->dict[str,Any]:
 q=urllib.parse.urlencode({"range":"5d","interval":"1d"})
 url=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol,safe='^')}?{q}"
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 RadarNormativo/1.0"})
 with urllib.request.urlopen(req,timeout=12) as response: payload=json.loads(response.read().decode())
 result=payload.get("chart",{}).get("result") or []
 if not result: raise ValueError("quotazione non disponibile")
 chart=result[0]; meta=chart.get("meta") or {}
 quote=(chart.get("indicators",{}).get("quote") or [{}])[0]
 closes=[float(x) for x in quote.get("close",[]) if x is not None]
 current=meta.get("regularMarketPrice")
 if current is None and closes: current=closes[-1]
 if current is None: raise ValueError("nessun prezzo")
 previous=meta.get("chartPreviousClose") or meta.get("previousClose")
 if previous is None and len(closes)>1: previous=closes[-2]
 change=(float(current)/float(previous)-1)*100 if previous else None
 stamp=datetime.fromtimestamp(int(meta["regularMarketTime"]),timezone.utc).astimezone(ROME) if meta.get("regularMarketTime") else None
 return {"value":float(current),"change_pct":change,"currency":str(meta.get("currency") or ""),"time":stamp}
def collect_market_data()->list[dict[str,Any]]:
 rows=[]
 for name,symbol,region in INSTRUMENTS:
  try: rows.append({"name":name,"symbol":symbol,"region":region,"ok":True,**_fetch_chart(symbol)})
  except (urllib.error.URLError,TimeoutError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
   rows.append({"name":name,"symbol":symbol,"region":region,"ok":False,"error":str(exc)[:100]})
 return rows
def render_market_briefing(rows:list[dict[str,Any]]|None=None)->str:
 data=collect_market_data() if rows is None else rows
 lines=["📈 RADAR FINANZIARIO",f"🕒 Rilevazione: {datetime.now(ROME).strftime('%d/%m/%Y %H:%M')} (ora italiana)",""]
 changes=[]; regions={}
 for row in data:
  if not row.get("ok"):
   lines.append(f"⚪ {row['name']} ({row['symbol']}): dato non disponibile"); continue
  val=row.get("value"); ch=row.get("change_pct"); cur=row.get("currency") or ""
  value=f"{val:,.4f} {cur}".strip() if val is not None else "valore n.d."
  if ch is None: change="variazione n.d."; icon="⚪"
  else:
   change=f"{ch:+.2f}%"; icon="🟢" if ch>0.05 else "🔴" if ch< -0.05 else "🟡"
   changes.append(ch); regions.setdefault(row["region"],[]).append(ch)
  stamp=row.get("time"); when=stamp.strftime("%d/%m %H:%M") if stamp else "ora n.d."
  lines.append(f"{icon} {row['name']}: {value} ({change}) · {when}")
 lines.extend(["","VALUTAZIONE COMPLESSIVA"])
 if not changes: lines.append("Dati insufficienti per una valutazione complessiva.")
 else:
  avg=sum(changes)/len(changes); pos=sum(x>0.05 for x in changes); neg=sum(x< -0.05 for x in changes); neu=len(changes)-pos-neg
  mood="prevalentemente positivo" if avg>0.15 and pos>neg else "prevalentemente negativo" if avg< -0.15 and neg>pos else "misto o stabile"
  lines.append(f"Quadro {mood}; media semplice indicativa dei {len(changes)} strumenti disponibili: {avg:+.2f}%.")
  lines.append(f"Positivi: {pos}; negativi: {neg}; stabili: {neu}.")
  regional=sorted((sum(v)/len(v),k) for k,v in regions.items())
  if regional: lines.append(f"Gruppo più forte: {regional[-1][1]} ({regional[-1][0]:+.2f}%); più debole: {regional[0][1]} ({regional[0][0]:+.2f}%).")
  lines.append("La media non è il rendimento del portafoglio: non considera pesi, costi o cambi.")
 lines.extend(["","Nota: dati indicativi da Yahoo Finance, eventualmente ritardati; ticker non disponibili segnalati senza stimare valori. Non è consulenza finanziaria."])
 return "\n".join(lines)
