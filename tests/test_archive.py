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
