# Radar Normativo 🇮🇹🇪🇺

Sistema indipendente per monitorare fonti normative italiane ed europee, classificare le pubblicazioni e preparare briefing verificabili.

> **Stato:** prototipo operativo in evoluzione. La raccolta automatica non equivale a una verifica giuridica: ogni scheda mantiene `legal_status: non_verificato` finché non viene controllata su fonti ufficiali.

## Funzionalità

- Raccolta RSS/Atom configurabile.
- Normalizzazione URL e deduplicazione per identificatore e URL canonico.
- Archivio storico con prima/ultima rilevazione e conteggio dei giorni UTC distinti in cui ogni atto è stato osservato.
- Classificazione euristica in italiano e inglese, utile anche per EUR-Lex.
- Punteggio editoriale spiegabile che non premia semplicemente la presenza di una data o di un URL.
- Briefing testuale e invio Telegram opzionale con registro anti-duplicati.
- Test automatici per classificazione, archivio, briefing, CLI e Telegram.

## Requisiti e installazione

Richiede Python 3.11 o superiore.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
python -m radar_normativo --help
pytest
```

## Fonti

Le fonti sono configurate in `config/sources.json`. Le fonti attuali sono la Gazzetta Ufficiale — Serie Generale e EUR-Lex — serie L. La raggiungibilità del feed viene controllata ad ogni scansione; la presenza nel feed non certifica che una norma sia vigente o applicabile.

## Flusso principale

```bash
python -m radar_normativo collect --config config/sources.json --output data/latest.json
python -m radar_normativo archive --latest data/latest.json --archive data/archive.json --new-items data/new_items.json
python -m radar_normativo briefing --input data/new_items.json --output data/briefing.txt --limit 10
```

Il workflow interrompe l'aggiornamento dell'archivio se una fonte non è leggibile; l'archivio rifiuta scansioni incomplete o prive dei risultati delle fonti. Il workflow GitHub Actions esegue la raccolta ogni 6 ore, tutti i giorni (cron UTC). Se trova aggiornamenti concorrenti sulla `main`, rilegge l'archivio più recente e riapplica la scansione, evitando di risolvere conflitti JSON tramite rebase.

## Telegram (opzionale)

Per simulare gli invii senza credenziali e senza modificare il registro:

```bash
python -m radar_normativo telegram --input data/new_items.json --ledger data/telegram_sent.json --dry-run
```

Per un invio reale, configura le variabili d'ambiente `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`, poi esegui:

```bash
python -m radar_normativo telegram --input data/new_items.json --ledger data/telegram_sent.json
```

Il registro `data/telegram_sent.json` impedisce di reinviare gli elementi già registrati. Non inserire mai token o credenziali nei file versionati: su GitHub configura i repository secrets `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.

Quando entrambi i secrets sono configurati, il workflow invia automaticamente su Telegram gli elementi nuovi individuati dalla scansione, anche durante le esecuzioni programmate ogni 6 ore. Se non vengono trovate nuove pubblicazioni, non viene inviato alcun avviso normativo. Le esecuzioni avviate manualmente con **Run workflow** inviano prima anche un messaggio di prova per verificare il collegamento; le esecuzioni programmate non inviano quel messaggio di prova.

## Campi e limiti

Ogni scheda può contenere `topics`, `relevance_score`, `priority`, `relevance_reasons`, `detection_status` e `legal_status`. I punteggi sono euristici e le classificazioni possono essere errate o incomplete. La data del feed può essere diversa dalla data di adozione, pubblicazione ufficiale o entrata in vigore. Le sintesi del feed non vengono inventate: se la fonte non ne fornisce una, il campo resta vuoto.

## Roadmap

- [x] Raccolta RSS/Atom configurabile e controllo fonti
- [x] Archivio storico e deduplicazione URL canonici
- [x] Classificazione multilingue e punteggio spiegabile
- [x] Briefing e invio Telegram manuale opzionale
- [ ] Verifica più ampia delle fonti ufficiali e dei feed
- [ ] Monitoraggio delle modifiche agli atti e briefing giornaliero Telegram
- [ ] Modulo AI opzionale con riferimenti controllabili alle fonti primarie
