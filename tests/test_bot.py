import json
from datetime import datetime, timezone

from radar_normativo.bot import handle_command


def _fixtures(tmp_path):
    archive = tmp_path / "archive.json"
    sources = tmp_path / "sources.json"
    state = tmp_path / "bot_state.json"
    latest = tmp_path / "latest.json"
    today = datetime.now(timezone.utc).isoformat()
    archive.write_text(json.dumps({
        "updated_at": today,
        "items": [
            {"id": "1", "title": "Nuovo decreto fiscale", "summary": "Misure IVA e imposte", "url": "https://example.test/1", "source_name": "Gazzetta Ufficiale", "published_at": today, "topics": ["fisco"]},
            {"id": "2", "title": "Regolamento agricolo", "summary": "Norme per le aziende", "url": "https://example.test/2", "source_name": "EUR-Lex", "published_at": "2020-01-01T00:00:00+00:00", "topics": ["agricoltura"]},
        ],
    }), encoding="utf-8")
    sources.write_text(json.dumps({"sources": [{"name": "Gazzetta Ufficiale", "url": "https://example.test/feed"}]}), encoding="utf-8")
    latest.write_text(json.dumps({"source_results": [{"name": "Gazzetta Ufficiale", "ok": True}]}), encoding="utf-8")
    return archive, sources, state, latest


def test_start_help_and_sources(tmp_path):
    archive, sources, state, latest = _fixtures(tmp_path)
    args = {"archive_path": archive, "sources_path": sources, "state_path": state, "latest_path": latest}
    assert "pronto" in handle_command("/start", 123, **args)
    assert "/ultime" in handle_command("/aiuto", 123, **args)
    assert "Gazzetta Ufficiale" in handle_command("/fonti", 123, **args)


def test_search_latest_and_status(tmp_path):
    archive, sources, state, latest = _fixtures(tmp_path)
    args = {"archive_path": archive, "sources_path": sources, "state_path": state, "latest_path": latest}
    assert "decreto fiscale" in handle_command("/cerca fiscale", 123, **args)
    assert "Ultime pubblicazioni" in handle_command("/ultime", 123, **args)
    status = handle_command("/stato", 123, **args)
    assert "Elementi in archivio: 2" in status
    assert "OK" in status


def test_filters_are_saved_applied_and_cleared(tmp_path):
    archive, sources, state, latest = _fixtures(tmp_path)
    args = {"archive_path": archive, "sources_path": sources, "state_path": state, "latest_path": latest}
    assert "Filtri salvati" in handle_command("/filtri fiscale", 123, **args)
    assert "fiscale" in handle_command("/filtri", 123, **args)
    latest_text = handle_command("/ultime", 123, **args)
    assert "decreto fiscale" in latest_text
    assert "Regolamento agricolo" not in latest_text
    assert "disattivati" in handle_command("/filtri off", 123, **args)
