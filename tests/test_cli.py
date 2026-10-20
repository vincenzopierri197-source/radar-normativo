import json

from radar_normativo.cli import main


def test_telegram_dry_run_cli(tmp_path, monkeypatch, capsys):
    source = tmp_path / "new_items.json"
    ledger = tmp_path / "ledger.json"
    source.write_text(json.dumps({"items": [{"id": "x", "title": "Atto di prova"}]}), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["radar-normativo", "telegram", "--input", str(source), "--ledger", str(ledger), "--dry-run"],
    )

    main()

    output = capsys.readouterr().out
    assert "Atto di prova" in output
    assert "simulazione" in output
    assert not ledger.exists()
