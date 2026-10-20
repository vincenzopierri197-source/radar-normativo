# Radar Normativo + Radar Finanziario 📡📈

Riepilogo giornaliero Telegram che unisce nuove pubblicazioni normative e monitoraggio indicativo di nove strumenti finanziari.

- Fonti normative italiane ed europee e attività parlamentare configurate in `config/sources.json`.
- Archivio e deduplicazione delle notizie già inviate.
- Quote indicative e variazioni per Dow Jones, JGLO, CHINA.MI, 0P0001LMEZ.F, 0P0000CO6N.F, FTSEMIB.MI, 0P0001BRM8.F, IGS1.SG e 0P00000ZJK.F.
- Valutazione complessiva descrittiva basata solo sui dati disponibili, senza inventare valori né attribuire pesi di portafoglio ignoti.

## Programmazione
GitHub Actions esegue la scansione alle 08:00 Europe/Rome (ora legale/solare). Configurare i secrets `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`. Le quotazioni provengono dall'endpoint chart Yahoo Finance, possono essere ritardate e alcuni simboli potrebbero non essere disponibili.

## Installazione e test
Python 3.11+: `python -m pip install -e ".[dev]"` e `pytest`.

## Comandi
`python -m radar_normativo telegram --input data/new_items.json --ledger data/telegram_sent.json --finance --dry-run`

`python -m radar_normativo bot` avvia il polling interattivo e richiede un host sempre acceso. Le schede normative non certificano la vigenza; il report finanziario non è consulenza finanziaria.
