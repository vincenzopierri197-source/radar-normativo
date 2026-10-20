# Radar Normativo 🇮🇹🇪🇺

Sistema indipendente per monitorare fonti normative italiane ed europee, con priorità a fisco, economia, imprese, lavoro e previdenza.

> **Stato del progetto:** fondamenta iniziali. Il progetto non è ancora un servizio di monitoraggio operativo e non fornisce consulenza legale. Ogni scheda dovrà rimandare alla fonte ufficiale; gli stati giuridici saranno indicati solo quando verificabili.

## Obiettivi

- Raccogliere atti e aggiornamenti da fonti ufficiali configurate.
- Normalizzare e deduplicare gli elementi raccolti.
- Conservare metadati, data di rilevazione e URL della fonte.
- Classificare per area tematica senza confondere classificazione automatica e stato giuridico.
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

Le fonti sono dichiarate in `config/sources.json`. Per ora il raccoglitore supporta feed RSS/Atom esplicitamente configurati. Aggiungere solo endpoint ufficiali verificati e testare ciascuna fonte prima di abilitarla in produzione.

Variabili d'ambiente opzionali per Telegram:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Non inserire mai token o credenziali nei file versionati. In GitHub vanno impostati come Actions secrets.

## Esecuzione

```bash
python -m radar_normativo collect
python -m radar_normativo collect --config config/sources.json --output data/latest.json
```

Il risultato è un JSON con gli elementi raccolti e metadati della scansione. La cartella `data/` è esclusa da Git: i runner di GitHub Actions sono effimeri, quindi la persistenza storica in produzione richiederà uno storage durevole dedicato.

## Principi di affidabilità

1. La fonte primaria e il suo URL devono essere conservati.
2. La data di pubblicazione non va confusa con quella di rilevazione.
3. Un feed o un titolo, da soli, non bastano a stabilire se una norma sia in vigore, abrogata o in attesa di attuazione.
4. Se lo stato non è verificato, dichiararlo esplicitamente come `non_verificato`.
5. I riepiloghi automatici non sostituiscono la lettura dell'atto ufficiale.

## Roadmap

- [x] Struttura iniziale, CLI e test automatici
- [x] Raccolta generica RSS/Atom configurabile
- [ ] Verifica e attivazione di feed ufficiali italiani ed europei
- [ ] Normalizzazione avanzata e archivio persistente
- [ ] Classificazione tematica e priorità configurabili
- [ ] Bot Telegram e comandi
- [ ] Monitoraggio delle modifiche e briefing quotidiano
- [ ] Modulo AI opzionale con citazioni verificabili
