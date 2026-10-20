import json

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
