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
- Bot Telegram interattivo con comandi per ultime pubblicazioni, novità giornaliere, ricerca, fonti, filtri e stato del sistema.
- Test automatici per classificazione, archivio, briefing, CLI, bot e Telegram.

## Requisiti e installazione

Richiede Python 3.11 o superiore.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install -e ".[dev]"
python -m radar_normativo --help
pytest
```

## Fonti

Le fonti sono configurate in `config/sources.json`. Le fonti attuali sono la Gazzetta Ufficiale — Serie Generale, la Gazzetta Ufficiale — Corte costituzionale e EUR-Lex — serie L. La raggiungibilità del feed viene controllata ad ogni scansione; la presenza nel feed non certifica che una norma sia vigente o applicabile.

## Flusso principale

```bash
python -m radar_normativo collect --config config/sources.json --output data/latest.json
python -m radar_normativo archive --latest data/latest.json --archive data/archive.json --new-items data/new_items.json
python -m radar_normativo briefing --input data/new_items.json --output data/briefing.txt --limit 10
```

Il workflow GitHub Actions esegue la raccolta ogni 6 ore, tutti i giorni (cron UTC). L'archivio non viene aggiornato se una fonte è in errore.

## Telegram: notifiche automatiche e comandi

Per le notifiche automatiche, configura i secrets GitHub `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`. Non inserire mai il token nei file versionati.

Per attivare i comandi interattivi, installa il progetto su un computer/server sempre acceso, configura le stesse variabili d'ambiente e avvia:

```bash
python -m radar_normativo bot
```

Il comando avvia un processo di long polling che deve restare in esecuzione. **GitHub Actions esegue la raccolta programmata, ma non è un host permanente per il bot interattivo.** Per l'accesso ai comandi, `TELEGRAM_CHAT_ID` deve essere l'ID numerico della chat privata autorizzata. Non condividere il token.

Comandi disponibili in Telegram:

- `/start` — avvia il bot
- `/ultime` — mostra le ultime pubblicazioni archiviate
- `/oggi` — mostra le pubblicazioni con data odierna (fuso Europe/Rome)
- `/cerca parola` — cerca nei titoli e nelle sintesi
- `/fonti` — elenca le fonti configurate
- `/filtri` — mostra i filtri attivi; `/filtri fisco, lavoro` li imposta; `/filtri off` li disattiva
- `/stato` — mostra l'archivio e, se disponibile localmente, l'esito dell'ultima scansione
- `/aiuto` — visualizza i comandi disponibili

I filtri vengono salvati localmente in `data/bot_state.json` e applicati alle liste. Se il bot è ospitato su un server separato, occorre sincronizzare periodicamente `data/archive.json` e `config/sources.json` dal repository per vedere gli aggiornamenti più recenti.

Il registro `data/telegram_sent.json` impedisce di reinviare gli elementi già notificati. Se non vengono trovate nuove pubblicazioni, non viene inviato alcun avviso normativo.

## Campi e limiti

Ogni scheda può contenere `topics`, `relevance_score`, `priority`, `relevance_reasons`, `detection_status` e `legal_status`. I punteggi sono euristici e le classificazioni possono essere errate o incomplete. La data del feed può essere diversa dalla data di adozione, pubblicazione ufficiale o entrata in vigore. Le sintesi del feed non vengono inventate: se la fonte non ne fornisce una, il campo resta vuoto.

## Roadmap

- [x] Raccolta RSS/Atom configurabile e controllo fonti
- [x] Archivio storico e deduplicazione URL canonici
- [x] Classificazione multilingue e punteggio spiegabile
- [x] Briefing e invio Telegram manuale opzionale
- [x] Comandi Telegram interattivi e filtri locali
- [ ] Verifica più ampia delle fonti ufficiali e dei feed
- [ ] Monitoraggio delle modifiche agli atti e briefing giornaliero Telegram
- [ ] Modulo AI opzionale con riferimenti controllabili alle fonti primarie
