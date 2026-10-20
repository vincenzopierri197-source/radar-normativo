# Radar Normativo 🇮🇹🇪🇺

Sistema indipendente per monitorare fonti normative italiane ed europee, con priorità a fisco, economia, imprese, lavoro e previdenza.

> **Stato del progetto:** fondamenta iniziali. Il progetto non è ancora un servizio di monitoraggio operativo e non fornisce consulenza legale. Ogni scheda dovrà rimandare alla fonte ufficiale; gli stati giuridici saranno indicati solo quando verificabili.

## Obiettivi

- Raccogliere atti e aggiornamenti da fonti ufficiali configurate.
- Normalizzare e deduplicare gli elementi raccolti.
- Conservare metadati, data di rilevazione e URL della fonte.
- Classificare per area tematica e stimare la rilevanza editoriale con regole trasparenti, senza confondere il punteggio con lo stato giuridico.
- Esporre i motivi del punteggio e mantenere lo stato giuridico `non_verificato` finché non viene verificato su fonti ufficiali.
- Inviare riepiloghi e avvisi Telegram, quando configurati.
- Mantenere l'architettura pronta per un futuro modulo AI opzionale, senza richiedere API a pagamento nella prima fase.

## Avvio locale

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

## Configurazione

Le fonti sono dichiarate in `config/sources.json`. Il raccoglitore supporta feed RSS/Atom esplicitamente configurati. L'elenco è intenzionalmente vuoto finché non sono verificati gli URL diretti dei feed ufficiali; non inserire la pagina HTML di un sito al posto del feed. Dopo la verifica, testare ogni fonte prima di abilitarla in produzione. Gli argomenti vengono classificati con regole lessicali trasparenti: la classificazione è indicativa e non determina lo stato giuridico.

Variabili d'ambiente opzionali per Telegram:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Non inserire mai token o credenziali nei file versionati. In GitHub vanno impostati come Actions secrets.

## Esecuzione

```bash
python -m radar_normativo collect
python -m radar_normativo collect --config config/sources.json --output data/latest.json
python -m radar_normativo archive --latest data/latest.json --archive data/archive.json --new-items data/new_items.json
python -m radar_normativo briefing --input data/new_items.json --output data/briefing.txt --limit 10
```

Il risultato è un JSON con gli elementi raccolti e metadati della scansione. Gli elementi includono `topics`, `relevance_score`, `priority`, `relevance_reasons`, `detection_status` e `legal_status`. Il punteggio è una stima editoriale euristica e spiegabile, non una valutazione legale. Il comando `briefing` produce un testo semplice ordinato per priorità, con materia, data, fonte, sintesi disponibile, URL e avvertenza sullo stato giuridico. Il briefing è preparatorio: non invia ancora messaggi a Telegram. La persistenza storica dipende dalla configurazione di versionamento e del workflow GitHub Actions.

## Principi di affidabilità

1. La fonte primaria e il suo URL devono essere conservati.
2. La data di pubblicazione non va confusa con quella di rilevazione.
3. Un feed o un titolo, da soli, non bastano a stabilire se una norma sia in vigore, abrogata o in attesa di attuazione.
4. Se lo stato non è verificato, dichiararlo esplicitamente come `non_verificato`.
5. I riepiloghi automatici non sostituiscono la lettura dell'atto ufficiale.

## Roadmap

- [x] Struttura iniziale, CLI e test automatici
- [x] Raccolta generica RSS/Atom configurabile
- [ ] Verifica e attivazione di feed ufficiali italiani ed europei (non attivi finché gli URL RSS non sono verificati)
- [x] Archivio storico versionato e rilevamento delle nuove pubblicazioni
- [x] Prima classificazione tematica euristica (da validare con casi reali)
- [x] Punteggio di rilevanza editoriale spiegabile e priorità bassa/media/alta
- [ ] Priorità configurabili e classificazione avanzata
- [x] Generazione di briefing testuali pronti per revisione e Telegram
- [ ] Invio Telegram e comandi
- [ ] Monitoraggio delle modifiche e briefing quotidiano
- [ ] Modulo AI opzionale con citazioni verificabili
