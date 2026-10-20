import json
from types import SimpleNamespace

from radar_normativo.collector import collect_sources


def test_empty_sources_returns_valid_empty_scan(tmp_path):
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"version": 1, "sources": []}), encoding="utf-8")

    result = collect_sources(config)

    assert result["schema_version"] == 1
    assert result["item_count"] == 0
    assert result["items"] == []
    assert result["source_results"] == []
    assert result["generated_at"]


def test_missing_url_is_reported_without_crashing(tmp_path):
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"sources": [{"name": "Fonte test"}]}), encoding="utf-8")

    result = collect_sources(config)

    assert result["item_count"] == 0
    assert result["source_results"][0]["ok"] is False
    assert result["source_results"][0]["error"] == "URL mancante"


def test_normalizes_url_and_classifies_english_eu_titles(tmp_path, monkeypatch):
    import radar_normativo.collector as collector

    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"sources": [{
        "name": "EUR-Lex test", "url": "https://example.test/feed", "language": "en"
    }]}), encoding="utf-8")
    entry = {
        "link": "https://eur-lex.europa.eu/./legal-content/AUTO/?uri=CELEX:32026R1234",
        "title": "Commission Implementing Regulation on VAT and tax credit",
        "summary": "",
    }
    monkeypatch.setattr(collector.feedparser, "parse", lambda _: SimpleNamespace(
        bozo=False, entries=[entry]
    ))

    result = collect_sources(config)
    item = result["items"][0]

    assert item["url"] == "https://eur-lex.europa.eu/legal-content/AUTO/?uri=CELEX:32026R1234"
    assert "fisco" in item["topics"]
    assert item["relevance_score"] >= 30
    assert item["legal_status"] == "non_verificato"



def test_removes_redundant_celex_prefix_but_keeps_identifier_only_title(tmp_path, monkeypatch):
    import radar_normativo.collector as collector

    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"sources": [{"name": "EUR-Lex test", "url": "https://example.test/feed", "language": "en"}]}), encoding="utf-8")
    entries = [
        {"link": "https://eur-lex.europa.eu/legal-content/AUTO/?uri=CELEX:32026R1234", "title": "CELEX:32026R1234: Commission Implementing Regulation (EU) 2026/1234 on a test subject", "summary": ""},
        {"link": "https://eur-lex.europa.eu/legal-content/AUTO/?uri=CELEX:32026R1235R(01)", "title": "CELEX:32026R1235R(01)", "summary": "The corrigendum does not concern the English version."},
    ]
    monkeypatch.setattr(collector.feedparser, "parse", lambda _: SimpleNamespace(bozo=False, entries=entries))
    result = collect_sources(config)
    titles = {item["url"]: item["title"] for item in result["items"]}
    assert titles["https://eur-lex.europa.eu/legal-content/AUTO/?uri=CELEX:32026R1234"] == "Commission Implementing Regulation (EU) 2026/1234 on a test subject"
    assert titles["https://eur-lex.europa.eu/legal-content/AUTO/?uri=CELEX:32026R1235R(01)"] == "CELEX:32026R1235R(01)"
