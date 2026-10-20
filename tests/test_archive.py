import json

import pytest

from radar_normativo.archive import update_archive


def write_scan(path, generated_at, items, source_results=None):
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "generated_at": generated_at,
            "item_count": len(items),
            "source_results": source_results if source_results is not None else [{"name": "Fonte test", "ok": True, "items": len(items)}],
            "items": items,
        }),
        encoding="utf-8",
    )


def test_archive_records_new_items_and_preserves_first_seen(tmp_path):
    latest = tmp_path / "latest.json"
    archive = tmp_path / "archive.json"
    new_items = tmp_path / "new_items.json"
    item = {"id": "abc123", "title": "Atto di prova", "url": "https://example.test/atto"}

    write_scan(latest, "2026-10-20T06:00:00+00:00", [item])
    first = update_archive(latest, archive, new_items)
    assert first["archive_count"] == 1
    assert first["new_item_count"] == 1

    write_scan(latest, "2026-10-21T06:00:00+00:00", [item])
    second = update_archive(latest, archive, new_items)
    saved = json.loads(archive.read_text(encoding="utf-8"))["items"][0]
    new_scan = json.loads(new_items.read_text(encoding="utf-8"))

    assert second["archive_count"] == 1
    assert second["new_item_count"] == 0
    assert saved["first_seen_at"] == "2026-10-20T06:00:00+00:00"
    assert saved["last_seen_at"] == "2026-10-21T06:00:00+00:00"
    assert saved["seen_count"] == 2
    assert new_scan["items"] == []


def test_archive_matches_normalized_url_when_legacy_id_changes(tmp_path):
    latest = tmp_path / "latest.json"
    archive = tmp_path / "archive.json"
    new_items = tmp_path / "new_items.json"
    old_item = {
        "id": "old-id",
        "title": "Atto UE",
        "url": "https://eur-lex.europa.eu/./legal-content/AUTO/?uri=CELEX:32026R1234",
        "first_seen_at": "2026-10-01T00:00:00+00:00",
        "last_seen_at": "2026-10-01T00:00:00+00:00",
        "seen_count": 3,
    }
    archive.write_text(json.dumps({"items": [old_item], "item_count": 1}), encoding="utf-8")
    new_item = {
        "id": "new-id",
        "title": "Atto UE aggiornato",
        "url": "https://eur-lex.europa.eu/legal-content/AUTO/?uri=CELEX:32026R1234",
    }

    write_scan(latest, "2026-10-21T06:00:00+00:00", [new_item])
    result = update_archive(latest, archive, new_items)
    saved = json.loads(archive.read_text(encoding="utf-8"))

    assert result["archive_count"] == 1
    assert result["new_item_count"] == 0
    assert saved["items"][0]["id"] == "old-id"
    assert saved["items"][0]["seen_count"] == 4
    assert saved["items"][0]["first_seen_at"] == "2026-10-01T00:00:00+00:00"


def test_archive_refuses_incomplete_scan(tmp_path):
    latest = tmp_path / "latest.json"
    write_scan(
        latest,
        "2026-10-20T06:00:00+00:00",
        [],
        source_results=[{"name": "Fonte test", "ok": False, "error": "timeout"}],
    )

    with pytest.raises(ValueError, match="scansione incompleta"):
        update_archive(latest, tmp_path / "archive.json", tmp_path / "new_items.json")

    assert not (tmp_path / "archive.json").exists()

def test_archive_does_not_increment_seen_count_twice_on_same_day(tmp_path):
    latest = tmp_path / "latest.json"
    archive = tmp_path / "archive.json"
    new_items = tmp_path / "new_items.json"
    item = {"id": "daily", "title": "Atto giornaliero", "url": "https://example.test/daily"}

    write_scan(latest, "2026-10-20T06:00:00+00:00", [item])
    update_archive(latest, archive, new_items)
    write_scan(latest, "2026-10-20T18:00:00+00:00", [item])
    update_archive(latest, archive, new_items)

    saved = json.loads(archive.read_text(encoding="utf-8"))["items"][0]
    assert saved["seen_count"] == 1
    assert saved["last_seen_at"] == "2026-10-20T18:00:00+00:00"

